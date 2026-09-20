"""Writes, recovery and research runs are exercised only on disposable copies."""
import concurrent.futures
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from ticket_test_support import symlink_or_skip
from unittest.mock import patch

sys.dont_write_bytecode = True
APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / 'scripts'))
import issue_index as ix
import issue_transaction as tx
from issue_store import IssueStore, render
import issue_store as st


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='desk-write-')
        self.root = Path(self.temp.name).resolve()
        (self.root / 'data').mkdir()
        for name in ('issues', 'project.json', 'relations.json'):
            src, dst = APP / 'tests/fixtures' / name, self.root / 'data' / name
            shutil.copytree(src, dst) if src.is_dir() else shutil.copyfile(src, dst)
        self.store = IssueStore(self.root)
        self.index = self.store.index
        self.counter = 0

    def tearDown(self):
        self.temp.cleanup()

    def sources(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in (self.root / 'data').rglob('*') if p.is_file()}

    def note(self, identifier='RES-13'):
        return self.root / 'data/issues' / (identifier.lower() + '.md')

    def error(self, code, function, *args, **kwargs):
        with self.assertRaises(ix.IndexErrorDetail) as caught:
            function(*args, **kwargs)
        self.assertEqual(code, caught.exception.code, str(caught.exception))
        return caught.exception

    def packet(self, *ops, **extra):
        self.counter += 1
        return dict(operation_id='test-' + str(self.counter), expected_generation=self.index.refresh()['generation'], operations=list(ops), **extra)

    def create(self, key='new', kind='lemma', **extra):
        return dict(op='create', key=key, kind=kind, title='Temporary ' + kind, body='## Statement\n\nTemporary test statement.\n', **extra)

    def update(self, identifier='RES-13', **changes):
        return dict(op='update', id=identifier, expected_version=ix.digest(self.note(identifier).read_bytes()), changes=changes)

    def relation(self, key='test-edge', **extra):
        return dict(op='relation-add', key=key, **{'from': 'RES-13', 'to': 'RES-5', 'type': 'requires-input-to',
                    'route': 'test route', 'logic': 'conditional on recorded scope', 'evidence': 'Temporary fixture only', **extra})

    def begin(self, run='run-1', issue='RES-13'):
        start = self.store.workflow_start()
        return self.store.apply(self.packet(dict(op='begin', run_id=run, issue=issue, reason='First ready priority', next_action='Inspect scope'), expected_harness_version=start['harness_version']))

    def flow_packet(self, phase='checkpoint', *ops, **extra):
        active = self.store.workflow_start()['active']
        return self.packet(*ops, dict(op=phase, run_id=active['id'], summary='Recorded finding', next_action='Check next case', **extra), expected_run_version=active['version'])

    def interrupt(self, packet, target):
        original = tx.atomic
        def fail_at(index, path, *args):
            if path == target:
                raise OSError('Injected interruption')
            return original(index, path, *args)
        with patch.object(tx, 'atomic', side_effect=fail_at):
            self.error('TRANSACTION_PENDING', self.store.apply, packet)
        return self.store.recover()

    def test_create_all_kinds_roundtrip_and_warm_cache(self):
        packet = self.packet(*(self.create(k, k, parent='RES-5', tags=['검증']) for k in sorted(ix.KINDS)))
        result = self.store.apply(packet)
        self.assertEqual(len(ix.KINDS), len(result['created']))
        snapshot = IssueStore(self.root).index.refresh()
        self.index.refresh()
        self.assertEqual(0, self.index.last_stats['source_bytes_read'])
        for identifier in result['created'].values():
            record = snapshot['records'][identifier]
            self.assertEqual('local', record['origin'])
            self.assertIsNone(record['source_url'])
            meta, _, _ = ix.parse_note(self.note(identifier).read_text(encoding='utf-8'), identifier)
            self.assertEqual(2, meta['desk_schema'])
            self.assertIsNone(meta['desk_imported_at'])
        self.assertEqual(len(snapshot['records']), len(self.store.read_web()['issues']))

    def test_updates_preserve_unknown_fields_and_archive_relations(self):
        path = self.note()
        path.write_text(path.read_text(encoding='utf-8').replace('desk_schema: 1', 'desk_schema: 1\ncustom_field: {"keep": true}'), encoding='utf-8')
        original_body = ix.parse_note(path.read_text(encoding='utf-8'), 'RES-13')[1]
        self.store.apply(self.packet(self.update(title='새 제목', priority=1, priority_rationale='Unblocks the main route', notes='메모')))
        meta, body, notes = ix.parse_note(path.read_text(encoding='utf-8'), 'RES-13')
        self.assertEqual({'keep': True}, meta['custom_field'])
        self.assertEqual(original_body, body)
        self.assertEqual('메모', notes)
        rels = (self.root / 'data/relations.json').read_bytes()
        for archived in (True, False):
            self.store.apply(self.packet(dict(op='archive', id='RES-13', expected_version=ix.digest(path.read_bytes()), archived=archived)))
            self.assertEqual(archived, self.index.refresh()['records']['RES-13']['archived'])
            self.assertEqual(rels, (self.root / 'data/relations.json').read_bytes())

    def test_invalid_write_has_no_partial_changes(self):
        for op, code in [(self.update(priority=1), 'INVALID_ARGUMENT'),
                         (self.update(parent='RES-999'), 'DANGLING_REFERENCE'),
                         (self.update('RES-5', parent='RES-13'), 'INVALID_DATA'),
                         (self.update('RES-5', status='Done'), 'INVALID_ARGUMENT'),
                         (self.update(blocked_by=['RES-5']), 'INVALID_DATA'),
                         (self.create('../escape'), 'INVALID_ARGUMENT'),
                         (self.create(kind='typo'), 'INVALID_ARGUMENT')]:
            with self.subTest(op=op):
                packet = self.packet(self.create('would-be-valid'), op)
                before = self.sources()
                self.error(code, self.store.apply, packet)
                self.assertEqual(before, self.sources())

    def test_versions_generation_and_idempotence_survive_history_pruning(self):
        packet = self.packet(self.create())
        result = self.store.apply(packet)
        shutil.rmtree(self.root / 'data/history')
        retry = IssueStore(self.root).apply(packet)
        self.assertTrue(retry['replayed'])
        self.assertEqual(result['created'], retry['created'])
        self.error('OPERATION_REUSED', self.store.apply, dict(packet, operations=[self.create('different')]))
        stale = dict(packet, operation_id='stale-generation')
        self.error('CONFLICT', self.store.apply, stale)
        self.error('DUPLICATE_KEY', self.store.apply, self.packet(self.create()))
        op = self.update(notes='wrong')
        op['expected_version'] = 'stale'
        self.error('CONFLICT', self.store.apply, self.packet(op))

    def test_relations_capture_versions_and_body_edits_require_review(self):
        self.store.apply(self.packet(self.relation()))
        edge = next(e for e in self.index.refresh()['relations'] if e['key'] == 'test-edge')
        self.assertEqual(ix.digest(self.note().read_bytes()), edge['from_version']['file_sha256'])
        self.store.apply(self.packet(self.update(notes='Notes alone do not change a claim')))
        self.assertEqual('current', next(e for e in self.index.refresh()['relations'] if e['key'] == 'test-edge')['status'])
        self.store.apply(self.packet(self.update(body='## Statement\n\nRevised scope.\n')))
        after = next(e for e in self.index.refresh()['relations'] if e['key'] == 'test-edge')
        self.assertEqual('needs-review', after['status'])
        self.assertEqual(edge['from_version'], after['from_version'])
        self.store.apply(self.packet(self.relation('replacement'), dict(op='relation-supersede', key='test-edge', reason='Updated scope', replacement='replacement')))
        raw = json.loads((self.root / 'data/relations.json').read_text(encoding='utf-8'))
        self.assertEqual('superseded', next(e for e in raw if e['key'] == 'test-edge')['status'])

    def test_refutation_inline_target_and_reserved_relation_keys(self):
        for op in (self.relation('contains-test'), self.relation(type='invented'), self.relation(type='refutes', **{'to': 'RES-13'})):
            self.error('INVALID_ARGUMENT', self.store.apply, self.packet(op))
        self.store.apply(self.packet(self.relation(type='refutes', to_inline_target='Only the old stronger claim', **{'to': 'RES-13'})))
        self.assertTrue(any(e.get('to_inline_target') == 'Only the old stronger claim' for e in self.index.refresh()['relations']))

    def test_workflow_full_lifecycle_restart_evidence_and_no_proof_promotion(self):
        original_math = {i: r['status'] for i, r in self.index.refresh()['records'].items() if r['kind'] != 'activity'}
        before = self.sources()
        start = self.store.workflow_start(limit=1)
        self.assertEqual(['RES-13'], [i['id'] for i in start['items']])
        self.assertEqual(before, self.sources())
        self.begin()
        self.store = IssueStore(self.root)  # New process/store can continue a durable run.
        self.assertEqual('run-1', self.store.workflow_start()['active']['id'])
        packet = self.flow_packet('checkpoint', self.create('lemma'), self.create('counter', 'counterexample'),
                                  self.relation(**{'from': '@counter', 'to': '@lemma', 'type': 'refutes'}),
                                  self.relation('activity-edge'), evidence=[{'issue': '@counter'}])
        result = self.store.apply(packet)
        self.assertEqual(2, len(result['created']))
        snapshot = self.index.refresh()
        edge = next(e for e in snapshot['relations'] if e['key'] == 'activity-edge')
        self.assertEqual(snapshot['records']['RES-13']['source_hash'], edge['from_version']['file_sha256'])
        stale = self.flow_packet()
        stale['expected_run_version'] = packet['expected_run_version']
        self.error('CONFLICT', self.store.apply, stale)
        self.store.apply(self.flow_packet('end', outcome='completed', evidence=[{'issue': result['created']['counter']}]))
        self.assertIsNone(self.store.workflow_start()['active'])
        snapshot = self.index.refresh()
        self.assertEqual('Done', snapshot['records']['RES-13']['status'])
        self.assertEqual(original_math, {i: snapshot['records'][i]['status'] for i in original_math})
        run = self.store.workflow_run('run-1', limit=2)
        self.assertEqual('completed', run['run']['status'])
        self.assertEqual(3, run['total'])
        self.assertTrue(run['next_cursor'])
        final = self.store.workflow_run('run-1', cursor=run['next_cursor'], limit=2)['items'][0]
        self.assertEqual('end', final['phase'])
        evidence = final['evidence'][0]
        self.assertEqual(ix.digest((self.root / evidence['path']).read_bytes()), evidence['sha256'])

    def test_workflow_wip_and_completion_guards(self):
        self.begin()
        self.error('WIP_LIMIT', self.begin, 'run-2', 'RES-14')
        self.error('WORKFLOW_CONFLICT', self.store.apply, self.packet(self.update(archived=True)))
        self.error('WORKFLOW_CONFLICT', self.store.patch_web, 'RES-13', {'version': ix.digest(self.note().read_bytes()), 'status': 'Done'})
        self.error('INVALID_ARGUMENT', self.store.apply, self.flow_packet('end', outcome='completed'))
        self.store.apply(self.flow_packet('end', outcome='paused'))
        self.assertEqual('Ready', self.index.refresh()['records']['RES-13']['status'])
        self.begin('run-2')
        self.store.apply(self.flow_packet('end', outcome='blocked'))
        self.assertEqual('Backlog', self.index.refresh()['records']['RES-13']['status'])

    def test_operational_blockers_and_cycle_are_distinct_from_proof_edges(self):
        self.store.apply(self.packet(self.update(blocked_by=['RES-14'])))
        self.assertEqual(['RES-14'], [i['id'] for i in self.store.workflow_start()['items']])
        self.error('BLOCKED', self.begin)
        self.error('INVALID_DATA', self.store.apply, self.packet(self.update('RES-14', blocked_by=['RES-13'])))
        self.store.apply(self.packet(self.update('RES-14', status='Done')))
        self.begin()

    def test_bad_begin_and_harness_version(self):
        start = self.store.workflow_start()
        for identifier in ('RES-5', 'RES-7', 'RES-999', [], None):
            self.error('INVALID_ARGUMENT', self.begin, 'run-1', identifier)
        op = dict(op='begin', run_id='run-1', issue='RES-13', reason='A reason', next_action='Inspect')
        self.error('CONFLICT', self.store.apply, self.packet(op, expected_harness_version='stale'))
        self.store.apply(self.packet(op, expected_harness_version=start['harness_version']))

    def test_artifact_evidence_hash_and_path_guards(self):
        self.begin()
        artifact = self.root / 'artifacts/check.md'
        artifact.parent.mkdir()
        artifact.write_text('A recorded observation', encoding='utf-8')
        for entry, code in [({'path': 'artifacts/check.md', 'sha256': 'stale'}, 'CONFLICT'),
                            ({'path': '../outside.md', 'sha256': 'x'}, 'INVALID_ARGUMENT'),
                            ({'issue': []}, 'INVALID_ARGUMENT'),
                            ({'issue': 'RES-5', 'path': 'artifacts/check.md'}, 'INVALID_ARGUMENT')]:
            self.error(code, self.store.apply, self.flow_packet(evidence=[entry]))
        self.store.apply(self.flow_packet('end', outcome='completed', evidence=[{'path': 'artifacts/check.md', 'sha256': ix.digest(artifact.read_bytes())}]))

    def test_interruption_at_each_publication_boundary_recovers_once(self):
        # Each subcase starts from a fresh disposable copy, including the receipt boundary.
        for target in ('data/harness.json', 'data/issues/res-13.md', 'data/runs/run-1.json', 'data/operations/test-1.json', 'data/history/test-1.json'):
            with self.subTest(target=target):
                if self.counter:
                    self.tearDown()
                    self.setUp()
                state = self.store.workflow_start()
                packet = self.packet(dict(op='begin', run_id='run-1', issue='RES-13', reason='Test recovery', next_action='Inspect'), expected_harness_version=state['harness_version'])
                status = self.interrupt(packet, target)
                before = self.sources()
                self.error('PENDING_TRANSACTION', self.index.refresh)
                self.error('PENDING_TRANSACTION', self.store.workflow_start)
                self.assertEqual(before, self.sources())
                self.error('CONFLICT', self.store.recover, 'finish', expected_journal='stale')
                self.store.recover('finish', expected_journal=status['journal_hash'])
                self.assertTrue(self.store.apply(packet)['replayed'])
                self.assertEqual('run-1', self.store.workflow_start()['active']['id'])
                self.assertEqual(1, len(list((self.root / 'data/operations').glob('*.json'))))

    def test_write_entry_recovers_pending_but_queries_never_do(self):
        packet = self.packet(self.create())
        self.interrupt(packet, 'data/issues/res-18.md')
        self.error('PENDING_TRANSACTION', self.store.read_web)
        result = IssueStore(self.root).apply(packet)
        self.assertTrue(result['replayed'])
        self.assertEqual('RES-18', result['created']['new'])
        self.assertFalse(self.store.recover()['pending'])

    def test_abrupt_process_exit_releases_lock_and_preserves_recoverable_journal(self):
        state = self.store.workflow_start()
        packet = self.packet(dict(op='begin', run_id='run-1', issue='RES-13', reason='Process crash test', next_action='Inspect'), expected_harness_version=state['harness_version'])
        script = '''import sys, json, os
sys.path.insert(0, sys.argv[1])
import issue_transaction as tx
from issue_store import IssueStore
original = tx.atomic
def abrupt(index, path, *args):
    if path == 'data/runs/run-1.json':
        os._exit(17)
    return original(index, path, *args)
tx.atomic = abrupt
IssueStore(sys.argv[2]).apply(json.load(sys.stdin))
'''
        child = subprocess.run([sys.executable, '-B', '-c', script, str(APP / 'scripts'), str(self.root)], input=json.dumps(packet), text=True, capture_output=True, cwd=tempfile.gettempdir(), timeout=15, encoding='utf-8')
        self.assertEqual(17, child.returncode, child.stderr)
        fresh = IssueStore(self.root)
        self.error('PENDING_TRANSACTION', fresh.workflow_start)
        self.assertTrue(fresh.apply(packet)['replayed'])
        self.assertEqual('run-1', fresh.workflow_start()['active']['id'])
        self.assertFalse(fresh.recover()['pending'])

    def test_unknown_edit_blocks_recovery_and_can_be_preserved_explicitly(self):
        packet = self.packet(self.update(notes='planned'))
        self.interrupt(packet, 'data/issues/res-13.md')
        self.note().write_text(render(self.note().read_text(encoding='utf-8'), {}, notes='external author'), encoding='utf-8')
        status = self.store.recover()
        self.error('RECOVERY_CONFLICT', self.store.recover, 'finish', expected_journal=status['journal_hash'])
        hashes = {item['path']: item['current_hash'] for item in status['files']}
        self.error('CONFLICT', self.store.recover, 'keep-current', expected_journal=status['journal_hash'], expected_files={})
        self.store.recover('keep-current', expected_journal=status['journal_hash'], expected_files=hashes)
        self.assertEqual('external author', self.store.read_web('RES-13')['notes'])
        self.error('OPERATION_ABANDONED', self.store.apply, packet)

    def test_keep_current_rejects_incoherent_partial_run(self):
        state = self.store.workflow_start()
        packet = self.packet(dict(op='begin', run_id='run-1', issue='RES-13', reason='Test', next_action='Inspect'), expected_harness_version=state['harness_version'])
        status = self.interrupt(packet, 'data/issues/res-13.md')
        before = self.sources()
        self.error('NOT_FOUND', self.store.recover, 'keep-current', expected_journal=status['journal_hash'], expected_files={f['path']: f['current_hash'] for f in status['files']})
        self.assertEqual(before, self.sources())

    def test_keep_current_rejects_partial_end_before_run_is_closed(self):
        self.begin()
        packet = self.flow_packet('end', outcome='paused')
        status = self.interrupt(packet, 'data/issues/res-13.md')
        self.error('WORKFLOW_CONFLICT', self.store.recover, 'keep-current', expected_journal=status['journal_hash'], expected_files={f['path']: f['current_hash'] for f in status['files']})
        self.store.recover('finish', expected_journal=status['journal_hash'])
        self.assertIsNone(self.store.workflow_start()['active'])

    def test_run_limit_reserves_room_for_end(self):
        self.begin()
        path = self.root / 'data/runs/run-1.json'
        run = json.loads(path.read_text(encoding='utf-8'))
        run['events'] *= 999
        path.write_text(tx.encoded(run), encoding='utf-8')
        self.error('INVALID_ARGUMENT', self.store.apply, self.flow_packet())
        self.store.apply(self.flow_packet('end', outcome='paused'))
        self.assertEqual(1000, self.store.workflow_run('run-1')['total'])

    def test_byte_budget_rejects_checkpoint_while_end_remains_possible(self):
        self.begin()
        path = self.root / 'data/runs/run-1.json'
        run = json.loads(path.read_text(encoding='utf-8'))
        event = dict(run['events'][0], summary='측' * 2000, next_action='정' * 2000)
        # Build a valid, large run just below the checkpoint budget.
        while len(tx.encoded(dict(run, events=run['events'] + [event])).encode()) < st.MAX_RUN_BYTES - st.END_RESERVE_BYTES - 1000:
            run['events'].append(event)
        path.write_text(tx.encoded(run), encoding='utf-8')
        packet = self.flow_packet()
        packet['operations'][-1]['summary'] = '측' * 2000
        packet['operations'][-1]['next_action'] = '정' * 2000
        before = self.sources()
        self.error('RUN_LIMIT_REACHED', self.store.apply, packet)
        self.assertEqual(before, self.sources())
        self.store.apply(self.flow_packet('end', outcome='paused'))
        self.assertIsNone(self.store.workflow_start()['active'])
        self.assertLess(path.stat().st_size, st.MAX_RUN_BYTES)

    def test_successful_recovery_reports_post_commit_cache_failure(self):
        packet = self.packet(self.update(notes='recovered'))
        status = self.interrupt(packet, 'data/issues/res-13.md')
        with patch.object(self.index, '_refresh_locked', side_effect=OSError('Cache failure')):
            result = self.store.recover('finish', expected_journal=status['journal_hash'])
        self.assertEqual('applied', result['status'])
        self.assertFalse(result['index_updated'])
        self.assertFalse(result['pending'])
        self.assertEqual('recovered', self.store.read_web('RES-13')['notes'])

    def test_same_priority_web_save_preserves_existing_rationale(self):
        self.store.apply(self.packet(self.update(priority_rationale='Unlocks the reviewed research route')))
        item = self.store.read_web('RES-13')
        self.store.patch_web(item['id'], {'version': item['version'], 'priority': item['priority']})
        self.assertEqual('Unlocks the reviewed research route', self.index.refresh()['records']['RES-13']['priority_rationale'])

    def test_bad_create_metadata_is_an_argument_error(self):
        for fields in ({'blocked_by': 'RES-5'}, {'summary': 'x' * 2001}, {'priority': 'high'}):
            self.error('INVALID_ARGUMENT', self.store.apply, self.packet(self.create(**fields)))

    def test_issue_evidence_requires_issue_form_to_capture_transaction_version(self):
        self.begin()
        self.error('INVALID_ARGUMENT', self.store.apply, self.flow_packet(evidence=[{'path': 'data/issues/res-13.md', 'sha256': ix.digest(self.note().read_bytes())}]))

    def test_write_reparses_canonical_relations_instead_of_copying_tampered_cache(self):
        original = (self.root / 'data/relations.json').read_bytes()
        snapshot = self.index.refresh()
        path = self.root / '.cache/issues-index.json'
        cache = json.loads(path.read_text(encoding='utf-8'))
        cache.pop('checksum')
        cache['raw_relations'] = []
        cache['records']['RES-13']['title'] = 'Wrong derived title'
        cache['checksum'] = ix.digest(ix.canonical(cache))
        path.write_text(tx.encoded(cache), encoding='utf-8')
        packet = {'operation_id': 'canonical-reparse', 'expected_generation': snapshot['generation'], 'operations': [self.update(notes='safe update')]}
        self.store.apply(packet)
        self.assertEqual(original, (self.root / 'data/relations.json').read_bytes())
        result = self.index.refresh()
        self.assertEqual(31, len(result['relations']))
        self.assertEqual(snapshot['records']['RES-13']['title'], result['records']['RES-13']['title'])

    def test_external_body_change_derives_stale_edge_without_mutating_sources(self):
        self.store.apply(self.packet(self.relation()))
        path = self.note()
        path.write_text(render(path.read_text(encoding='utf-8'), {}, body='External statement revision'), encoding='utf-8')
        before = self.sources()
        edge = next(e for e in self.index.refresh()['relations'] if e['key'] == 'test-edge')
        self.assertEqual('needs-review', edge['status'])
        self.assertEqual(before, self.sources())

    def test_evidence_issue_expected_hash_is_checked(self):
        self.begin()
        self.error('CONFLICT', self.store.apply, self.flow_packet(evidence=[{'issue': 'RES-5', 'sha256': 'stale'}]))

    def test_receipt_commit_point_does_not_revert_later_external_edits(self):
        packet = self.packet(self.update(notes='committed'))
        status = self.interrupt(packet, 'data/history/test-1.json')
        self.note().write_text(render(self.note().read_text(encoding='utf-8'), {}, notes='later external edit'), encoding='utf-8')
        self.store.recover('finish', expected_journal=status['journal_hash'])
        self.assertEqual('later external edit', self.store.read_web('RES-13')['notes'])
        self.assertTrue(self.store.apply(packet)['replayed'])

    def test_index_failure_after_commit_reports_committed_and_can_rebuild(self):
        packet = self.packet(self.create())
        original = self.index._refresh_locked
        calls = []
        def fail_second(*args, **kwargs):
            calls.append(1)
            if len(calls) == 2:
                raise OSError('Cache failure after source commit')
            return original(*args, **kwargs)
        with patch.object(self.index, '_refresh_locked', side_effect=fail_second):
            result = self.store.apply(packet)
        self.assertFalse(result['index_updated'])
        self.assertTrue(self.store.apply(packet)['replayed'])
        self.assertIn('RES-18', self.index.refresh(force=True)['records'])

    def test_parallel_writers_retry_after_generation_conflict_without_duplicate_ids(self):
        def create_one(number):
            store = IssueStore(self.root)
            for _ in range(20):
                request = {'operation_id': 'parallel-' + str(number), 'expected_generation': store.index.refresh()['generation'], 'operations': [self.create('parallel-' + str(number))]}
                try:
                    return store.apply(request)['created']
                except ix.IndexErrorDetail as error:
                    if error.code != 'CONFLICT':
                        raise
            self.fail('Concurrent writer never made progress')
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(create_one, range(4)))
        self.assertEqual(4, len({identifier for item in results for identifier in item.values()}))
        self.assertEqual(17, len(self.index.refresh()['records']))

    def test_project_lock_survives_cache_removal_and_rejects_replacement(self):
        with self.index._lock():
            shutil.rmtree(self.root / '.cache')
            self.error('INDEX_BUSY', IssueStore(self.root, lock_timeout=0.01).workflow_start)
            lock = self.root / '.research-desk.lock'
            if os.name == 'nt':
                # Windows refuses renaming an open lock; contention was checked above.
                return
            lock.rename(self.root / '.previous-lock')
            lock.touch()
            self.error('LOCK_REPLACED', self.index._assert_lock_current)

    def test_symlinked_storage_cannot_escape(self):
        outside = self.root / 'outside'
        outside.mkdir()
        for directory in ('history', 'transactions', 'operations', 'runs'):
            with self.subTest(directory=directory):
                link = self.root / 'data' / directory
                packet = self.packet(self.create())
                symlink_or_skip(self, link, outside, target_is_directory=True)
                if directory == 'runs':
                    self.error('UNSAFE_PATH', self.begin)
                else:
                    self.error('UNSAFE_PATH', self.store.apply, packet)
                self.assertEqual([], list(outside.iterdir()))
                link.unlink()

    def test_malformed_journal_and_injected_path_are_rejected(self):
        packet = self.packet(self.create())
        self.interrupt(packet, 'data/issues/res-18.md')
        path = self.root / tx.PENDING
        value = json.loads(path.read_text(encoding='utf-8'))
        value['files'][0]['path'] = '../outside.md'
        value.pop('checksum')
        value['checksum'] = ix.digest(ix.canonical(value))
        path.write_text(tx.encoded(value), encoding='utf-8')
        self.error('INVALID_JOURNAL', self.store.recover)
        self.assertFalse((self.root.parent / 'outside.md').exists())

    def test_cli_stdin_other_cwd_and_malformed_workflow(self):
        def cli(command, packet):
            result = subprocess.run([sys.executable, '-B', str(APP / 'scripts/issues.py'), '--root', str(self.root), *command, '--request-file', '-'], input=json.dumps(packet), text=True, capture_output=True, cwd=tempfile.gettempdir(), timeout=15, encoding='utf-8')
            self.assertNotIn('Traceback', result.stderr)
            return result.returncode, json.loads(result.stdout)
        packet = self.packet(self.create())
        code, result = cli(['write'], packet)
        self.assertEqual(0, code)
        self.assertEqual('RES-18', result['created']['new'])
        code, result = cli(['workflow', 'begin'], {'operations': [None]})
        self.assertEqual(2, code)
        self.assertEqual('INVALID_ARGUMENT', result['error']['code'])

    def test_web_per_issue_version_allows_unrelated_updates(self):
        original = self.store.read_web('RES-13')
        self.store.apply(self.packet(self.update('RES-14', notes='unrelated')))
        self.assertEqual('saved', self.store.patch_web('RES-13', {'version': original['version'], 'notes': 'saved'})['notes'])
        self.error('CONFLICT', self.store.patch_web, 'RES-13', {'version': original['version'], 'notes': 'stale'})


if __name__ == '__main__':
    unittest.main()
