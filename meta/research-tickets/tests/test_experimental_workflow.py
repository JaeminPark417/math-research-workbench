"""Experimental research semantics on synthetic, disposable capsule sources only.

No project enrollment outside the temporary directory, external service, SSH,
training process, or remote execution cache is used by these tests.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / 'scripts'))
import issue_index as ix
import issue_sources as source
from issue_sources import snapshot
from issue_store import IssueStore
from ticket_project import initialize


class ExperimentalWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ticket-experimental-tests-')
        self.project = Path(self.temp.name).resolve() / '2026-synthetic-experiment'
        self.project.mkdir()
        (self.project / 'README.md').write_text(
            '# Synthetic fixture only\n\n## H-1\n\nAn unverified toy hypothesis.\n', encoding='utf-8')
        (self.project / 'logs').mkdir()
        self.log = self.project / 'logs/observation.md'
        self.log.write_text('# Toy observation\n\n## Results\n\n'
                            'Both toy runs finished; the predeclared gate failed.\n', encoding='utf-8')
        self.manifest = self.project / 'logs/manifest.json'
        self.manifest.write_text(json.dumps({'synthetic': True, 'rows': 2,
                                             'failed_runs': 0, 'gate': 'fail'}), encoding='utf-8')
        initialize(self.project)
        self.root = self.project / 'tickets'
        self.store = IssueStore(self.root)
        self.index = self.store.index
        self.log_ref = snapshot(self.root, 'capsule', 'logs/observation.md', heading='Results')
        self.manifest_ref = snapshot(self.root, 'capsule', 'logs/manifest.json')
        self.n = 0

    def tearDown(self):
        self.temp.cleanup()

    def packet(self, *operations, **extra):
        self.n += 1
        return dict(operation_id='experimental-' + str(self.n),
                    expected_generation=self.index.refresh()['generation'],
                    operations=list(operations), **extra)

    def apply(self, *operations, **extra):
        return self.store.apply(self.packet(*operations, **extra))

    def create(self, key, kind, **fields):
        return dict(op='create', key=key, kind=kind, title='Synthetic ' + key,
                    body='## Statement and scope\n\nDisposable toy research only.\n',
                    **fields)

    def record(self, identifier):
        return self.index.refresh()['records'][identifier]

    def update(self, identifier, **changes):
        return dict(op='update', id=identifier,
                    expected_version=self.record(identifier)['source_hash'], changes=changes)

    def relation(self, key, source, target, kind):
        return {'op': 'relation-add', 'key': key, 'from': source, 'to': target,
                'type': kind, 'route': 'Synthetic scoped route',
                'logic': 'Only the recorded toy protocol and contrast are in scope.',
                'evidence': 'Disposable toy observation and exact source snapshots.'}

    def canonical(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in (self.root / 'data').rglob('*') if p.is_file()}

    def rejects_unchanged(self, *operations, **extra):
        request = self.packet(*operations, **extra)
        before = self.canonical()
        with self.assertRaises(ix.IndexErrorDetail) as caught:
            self.store.apply(request)
        self.assertEqual(before, self.canonical())
        return caught.exception

    def call(self, *args):
        result = subprocess.run(
            [sys.executable, '-B', str(APP.parents[1] / 'scripts/research-tickets.py'),
             '--project', str(self.project), *args], capture_output=True, text=True, encoding='utf-8')
        value = json.loads(result.stdout)
        self.assertEqual(0 if value['ok'] else 2, result.returncode, result.stderr)
        return value

    def begin(self, identifier, run='toy-session'):
        start = self.store.workflow_start()
        return self.apply(dict(op='begin', run_id=run, issue=identifier,
                               reason='Review a synthetic experiment outcome',
                               next_action='Inspect the retained result'),
                          expected_harness_version=start['harness_version'])

    def source_chain(self):
        """Two ready activities share 25 references across their ancestors."""
        refs = []
        for n in range(24):
            path = 'logs/paged-' + str(n) + '.json'
            (self.project / path).write_text(json.dumps({'synthetic_reference': n}), encoding='utf-8')
            refs.append(snapshot(self.root, 'capsule', path))
        claim = dict(snapshot(self.root, 'capsule', 'README.md', heading='H-1'), object_id='H-1')
        ids = self.apply(
            self.create('hypothesis', 'hypothesis', claim_ref=claim, source_refs=refs[:12]),
            self.create('design', 'experiment', parent='@hypothesis', source_refs=refs[12:]),
            self.create('first', 'activity', parent='@design', status='Ready'),
            self.create('second', 'activity', parent='@design', status='Ready'))['created']
        return ids, refs + [claim]

    def test_research_chain_keeps_all_objects_and_typed_relations(self):
        created = self.apply(
            self.create('question', 'question'), self.create('hypothesis', 'hypothesis'),
            self.create('design', 'experiment', source_refs=[self.manifest_ref]),
            self.create('observation', 'result', outcome='mixed', source_refs=[self.log_ref]),
            self.create('interpretation', 'analysis', outcome='inconclusive'),
            self.create('decision', 'decision'),
            self.create('execution', 'activity', status='Ready'),
            self.create('followup', 'activity', status='Backlog'))['created']
        edges = [('test-question', 'design', 'question', 'tests'),
                 ('test-hypothesis', 'design', 'hypothesis', 'tests'),
                 ('design-result', 'design', 'observation', 'produces'),
                 ('execution-result', 'execution', 'observation', 'produces'),
                 ('support', 'observation', 'hypothesis', 'supports'),
                 ('challenge', 'interpretation', 'hypothesis', 'challenges'),
                 ('interpret', 'interpretation', 'observation', 'interprets'),
                 ('result-decision', 'observation', 'decision', 'informs'),
                 ('analysis-decision', 'interpretation', 'decision', 'informs'),
                 ('next-question', 'decision', 'question', 'motivates'),
                 ('next-hypothesis', 'decision', 'hypothesis', 'motivates'),
                 ('next-design', 'decision', 'design', 'motivates'),
                 ('next-activity', 'decision', 'followup', 'motivates')]
        self.apply(*(self.relation(k, created[a], created[b], t) for k, a, b, t in edges))
        self.assertEqual(8, self.index.validate()['issues'])
        self.assertEqual(13, self.index.validate()['relations'])
        self.assertNotIn('object_id', self.log_ref)
        self.assertEqual([self.log_ref], self.record(created['observation'])['source_refs'])
        self.assertEqual([created['execution']], [r['id'] for r in self.store.workflow_start()['items']])
        self.assertTrue(all(self.record(created[k])['status'] == 'Backlog'
                            for k in ('question', 'hypothesis', 'design', 'observation', 'interpretation', 'decision')))

    def test_completed_activity_with_negative_finding_does_not_start_followup(self):
        ids = self.apply(self.create('hypothesis', 'hypothesis'),
                         self.create('execution', 'activity', status='Ready'),
                         self.create('followup', 'activity', status='Backlog', blocked_by=['@execution']))['created']
        self.begin(ids['execution'])
        active = IssueStore(self.root).workflow_start()['active']
        result = self.apply(
            self.create('failed-gate', 'result', outcome='negative', source_refs=[self.log_ref]),
            self.create('stop-expansion', 'decision'),
            self.relation('gate-challenges', '@failed-gate', ids['hypothesis'], 'challenges'),
            self.relation('gate-informs', '@failed-gate', '@stop-expansion', 'informs'),
            dict(op='end', run_id=active['id'], outcome='completed',
                 summary='The toy execution completed; its scientific gate failed.',
                 next_action='Keep expansion deferred until an explicit decision.',
                 evidence=[{'issue': '@failed-gate'}, {'source': self.manifest_ref}]),
            expected_run_version=active['version'])
        fresh = IssueStore(self.root).workflow_start()
        self.assertIsNone(fresh['active'])
        self.assertEqual('completed', fresh['last_run']['status'])
        self.assertEqual([], fresh['items'])
        self.assertEqual('Done', self.record(ids['execution'])['status'])
        self.assertEqual('Backlog', self.record(ids['followup'])['status'])
        self.assertEqual('Backlog', self.record(ids['hypothesis'])['status'])
        self.assertEqual('negative', self.record(result['created']['failed-gate'])['outcome'])

    def test_nonactivity_objects_cannot_be_done_or_own_an_operational_session(self):
        kinds = ('question', 'hypothesis', 'experiment', 'result', 'analysis', 'decision')
        ids = self.apply(*(self.create(k, k, status='Ready') for k in kinds))['created']
        for kind in kinds:
            with self.subTest(kind=kind):
                self.rejects_unchanged(self.update(ids[kind], status='Done'))
                start = self.store.workflow_start()
                self.rejects_unchanged(
                    dict(op='begin', run_id='invalid-' + kind, issue=ids[kind],
                         reason='Must reject nonactivity', next_action='No action'),
                    expected_harness_version=start['harness_version'])
        self.assertEqual([], self.store.workflow_start()['items'])

    def test_invalid_outcomes_and_wrong_object_kinds_are_atomic(self):
        for value in ('success', '', True, 7, {}, []):
            with self.subTest(outcome=value):
                self.rejects_unchanged(self.create('valid-before-error', 'question'),
                                       self.create('bad-result', 'result', outcome=value))
        for kind in ('hypothesis', 'activity', 'decision', 'experiment', 'theorem'):
            with self.subTest(kind=kind):
                self.rejects_unchanged(self.create('wrong-kind', kind, outcome='positive'))
        identifier = self.apply(self.create('result', 'result', outcome='negative'))['created']['result']
        self.rejects_unchanged(self.update(identifier, outcome='confirmed'))
        self.rejects_unchanged(self.update(identifier, unsupported_empirical_field=True))

    def test_source_reference_shape_uniqueness_count_and_path_rejections(self):
        too_many = []
        for n in range(21):
            path = 'logs/fixture-' + str(n) + '.json'
            (self.project / path).write_text(json.dumps({'synthetic': n}), encoding='utf-8')
            too_many.append(snapshot(self.root, 'capsule', path))
        invalid = [None, {}, 'logs/observation.md', [self.log_ref, self.log_ref],
                   too_many, [{**self.log_ref, 'path': '../README.md'}],
                   [{**self.log_ref, 'path': '.env.md'}],
                   [{**self.log_ref, 'repository': 'unregistered'}]]
        for refs in invalid:
            with self.subTest(refs=refs):
                self.rejects_unchanged(self.create('bad-source', 'result', source_refs=refs))
        identifier = self.apply(self.create('source-error-codes', 'result'))['created']['source-error-codes']
        for refs in (None, {}, [self.log_ref, self.log_ref], too_many):
            self.assertEqual('INVALID_ARGUMENT', self.rejects_unchanged(
                self.create('bad-input', 'result', source_refs=refs)).code)
            self.assertEqual('INVALID_ARGUMENT', self.rejects_unchanged(
                self.update(identifier, source_refs=refs)).code)

    def test_source_hash_is_verified_on_create_and_update(self):
        bad = {**self.log_ref, 'sha256': '0' * 64}
        self.assertEqual('SOURCE_MISMATCH', self.rejects_unchanged(
            self.create('bad-source', 'result', source_refs=[bad])).code)
        identifier = self.apply(self.create('result', 'result', source_refs=[self.log_ref]))['created']['result']
        self.assertEqual('SOURCE_MISMATCH', self.rejects_unchanged(
            self.update(identifier, source_refs=[bad])).code)
        self.log.write_text(self.log.read_text(encoding='utf-8') + '\nA later toy revision.\n', encoding='utf-8')
        self.assertEqual('SOURCE_MISMATCH', self.rejects_unchanged(
            self.create('stale-source', 'analysis', source_refs=[self.log_ref])).code)

    def test_rebinding_source_refs_marks_edge_stale_and_preserves_endpoint_snapshot(self):
        ids = self.apply(self.create('hypothesis', 'hypothesis'),
                         self.create('result', 'result', source_refs=[self.log_ref], outcome='negative'))['created']
        self.apply(self.relation('challenge', ids['result'], ids['hypothesis'], 'challenges'))
        original = self.index.neighbors(ids['result'])['items'][0]
        self.assertEqual([self.log_ref], original['from_version']['source_refs'])
        self.assertEqual('negative', original['from_version']['outcome'])
        self.log.write_text(self.log.read_text(encoding='utf-8') + '\nReplacement observation is inconclusive.\n', encoding='utf-8')
        new_ref = snapshot(self.root, 'capsule', 'logs/observation.md', heading='Results')
        self.apply(self.update(ids['result'], source_refs=[new_ref]))
        self.assertEqual([], self.index.neighbors(ids['result'])['items'])
        stale = self.index.neighbors(ids['result'], include_noncurrent=True)['items'][0]
        self.assertEqual('needs-review', stale['status'])
        self.assertEqual(original['from_version'], stale['from_version'])
        self.apply(self.relation('replacement', ids['result'], ids['hypothesis'], 'challenges'),
                   dict(op='relation-supersede', key='challenge', replacement='replacement',
                        reason='The observed source revision changed.'))
        edges = self.index.neighbors(ids['result'], include_noncurrent=True)['items']
        self.assertEqual({'superseded', 'current'}, {e['status'] for e in edges})

    def test_outcome_changes_invalidate_edges_but_notes_do_not(self):
        ids = self.apply(self.create('hypothesis', 'hypothesis'),
                         self.create('result', 'result', outcome='positive'))['created']
        self.apply(self.relation('support', ids['result'], ids['hypothesis'], 'supports'))
        original = copy.deepcopy(self.index.neighbors(ids['result'])['items'][0])
        self.apply(self.update(ids['result'], notes='A provenance annotation only.'))
        self.assertEqual('current', self.index.neighbors(ids['result'])['items'][0]['status'])
        self.apply(self.update(ids['result'], outcome='invalid'))
        stale = self.index.neighbors(ids['result'], include_noncurrent=True)['items'][0]
        self.assertEqual('needs-review', stale['status'])
        self.assertEqual(original['from_version'], stale['from_version'])
        self.assertEqual('Backlog', self.record(ids['hypothesis'])['status'])

    def test_typed_relation_endpoint_errors_never_publish_partial_findings(self):
        kinds = ('question', 'hypothesis', 'experiment', 'result', 'analysis', 'decision', 'activity', 'lemma')
        ids = self.apply(*(self.create(k, k) for k in kinds))['created']
        invalid = [('tests', 'activity', 'hypothesis'), ('tests', 'experiment', 'result'),
                   ('produces', 'hypothesis', 'result'), ('produces', 'experiment', 'analysis'),
                   ('supports', 'experiment', 'hypothesis'), ('supports', 'result', 'lemma'),
                   ('challenges', 'result', 'question'), ('interprets', 'result', 'analysis'),
                   ('informs', 'experiment', 'decision'), ('informs', 'analysis', 'activity'),
                   ('motivates', 'result', 'experiment'), ('motivates', 'decision', 'result')]
        for relation_type, source, target in invalid:
            with self.subTest(relation=relation_type, source=source, target=target):
                self.rejects_unchanged(self.create('would-have-been-created', 'result'),
                    self.relation('invalid-edge', ids[source], ids[target], relation_type))

    def test_source_checks_include_ancestor_claims_and_all_supporting_refs(self):
        claim = dict(snapshot(self.root, 'capsule', 'README.md', heading='H-1'), object_id='H-1')
        ids = self.apply(self.create('hypothesis', 'hypothesis', claim_ref=claim,
                                    source_refs=[self.log_ref, self.manifest_ref]),
                         self.create('audit', 'activity', status='Ready', parent='@hypothesis'))['created']
        before = self.canonical()
        checks = self.store.workflow_start()['source_checks']
        self.assertEqual(3, len(checks))
        self.assertTrue(all(item['issue'] == ids['hypothesis'] and item['state'] == 'current' for item in checks))
        self.assertTrue(all(item['repository'] == 'capsule' and item['mode'] == 'working'
                            and item['path'] and item['reference_sha256'] for item in checks))
        self.log.write_text(self.log.read_text(encoding='utf-8') + '\nDrift without canonical ticket mutation.\n', encoding='utf-8')
        result = self.call('source', 'check', ids['audit'])
        self.assertTrue(result['ok'])
        self.assertEqual(['changed', 'current', 'current'], sorted(r['state'] for r in result['checks']))
        self.assertEqual(before, self.canonical())

    def test_priority_zero_means_unassigned_after_priorities_one_through_four(self):
        ids = self.apply(*(self.create('priority-' + str(n), 'activity', status='Ready', priority=n)
                           for n in range(5)))['created']
        expected = [ids['priority-' + str(n)] for n in (1, 2, 3, 4, 0)]
        self.assertEqual(expected, [item['id'] for item in self.store.workflow_start()['items']])
        self.assertEqual(expected, [item['id'] for item in self.index.list_issues()['items']])

    def test_cli_filters_and_pagination_distinguish_null_from_unassessed(self):
        outcomes = ('positive', 'negative', 'null', 'mixed', 'inconclusive', 'invalid')
        ids = self.apply(*(self.create('result-' + v, 'result', outcome=v, source_refs=[self.log_ref]) for v in outcomes),
                         self.create('unassessed', 'result'),
                         self.create('explicit-unassessed', 'analysis', outcome=None))['created']
        page = self.call('list', '--kind', 'result', '--fields', 'id,outcome,source_refs', '--limit', '2')
        found = list(page['items'])
        while page['next_cursor']:
            page = self.call('list', '--kind', 'result', '--fields', 'id,outcome,source_refs',
                             '--limit', '2', '--cursor', page['next_cursor'])
            found.extend(page['items'])
        self.assertEqual(7, len(found))
        self.assertEqual(7, len({v['id'] for v in found}))
        filtered = self.call('search', 'synthetic', '--outcome', 'null', '--fields', 'id,outcome')
        self.assertEqual([{'id': ids['result-null'], 'outcome': 'null'}], filtered['items'])
        self.assertIsNone(self.record(ids['unassessed'])['outcome'])
        self.assertIsNone(self.record(ids['explicit-unassessed'])['outcome'])
        self.assertFalse(self.call('list', '--outcome', 'passed')['ok'])

    def test_outcome_is_part_of_cursor_query_identity(self):
        self.apply(*(self.create('result-' + str(n), 'result', outcome='negative') for n in range(3)))
        page = self.index.list_issues(outcome='negative', fields=['id', 'outcome'], limit=1)
        self.assertTrue(page['next_cursor'])
        with self.assertRaises(ix.IndexErrorDetail):
            self.index.list_issues(outcome='positive', fields=['id', 'outcome'], limit=1,
                                  cursor=page['next_cursor'])

    def test_archiving_negative_branch_preserves_sources_results_and_relations(self):
        ids = self.apply(self.create('hypothesis', 'hypothesis'),
                         self.create('result', 'result', outcome='negative', source_refs=[self.log_ref]))['created']
        self.apply(self.relation('negative-evidence', ids['result'], ids['hypothesis'], 'challenges'))
        old_edge = copy.deepcopy(self.index.neighbors(ids['result'])['items'][0])
        source_bytes = self.log.read_bytes()
        self.apply(dict(op='archive', id=ids['result'], expected_version=self.record(ids['result'])['source_hash'], archived=True))
        self.assertEqual([], self.index.list_issues(outcome='negative')['items'])
        restored = self.index.list_issues(outcome='negative', include_archived=True,
                                         fields=['id', 'outcome', 'source_refs'])['items'][0]
        self.assertEqual('negative', restored['outcome'])
        self.assertEqual([self.log_ref], restored['source_refs'])
        self.assertEqual(old_edge, self.index.neighbors(ids['result'])['items'][0])
        self.assertEqual(source_bytes, self.log.read_bytes())

    def test_cache_rebuild_preserves_empirical_fields_and_warm_queries_read_no_bodies(self):
        self.apply(self.create('observation', 'result', outcome='inconclusive', source_refs=[self.log_ref]))
        before = self.index.list_issues(fields=['id', 'outcome', 'source_refs'])['items']
        cache = self.root / '.cache/issues-index.json'
        self.assertTrue(cache.exists())
        cache.unlink()  # Disposable cache in this temporary fixture only.
        self.assertEqual(before, IssueStore(self.root).index.list_issues(fields=['id', 'outcome', 'source_refs'])['items'])
        self.index.list_issues(outcome='inconclusive')
        self.assertEqual(0, self.index.last_stats['source_bytes_read'])

    def test_idempotent_retry_and_stale_generation_preserve_negative_evidence(self):
        packet = self.packet(self.create('negative', 'result', outcome='negative', source_refs=[self.log_ref]))
        first = self.store.apply(packet)
        before = self.canonical()
        retry = IssueStore(self.root).apply(packet)
        self.assertTrue(retry['replayed'])
        self.assertEqual(first['created'], retry['created'])
        self.assertEqual(before, self.canonical())
        stale = dict(packet, operation_id='new-but-stale-intent')
        with self.assertRaises(ix.IndexErrorDetail) as caught:
            self.store.apply(stale)
        self.assertEqual('CONFLICT', caught.exception.code)
        self.assertEqual(before, self.canonical())

    def test_session_evidence_retains_historical_result_after_reassessment(self):
        ids = self.apply(self.create('work', 'activity', status='Ready'),
                         self.create('result', 'result', outcome='positive', source_refs=[self.log_ref]))['created']
        self.begin(ids['work'])
        active = self.store.workflow_start()['active']
        self.apply(dict(op='checkpoint', run_id=active['id'], summary='Record toy evidence before reassessment.',
                        next_action='Review contamination.', evidence=[{'issue': ids['result']}]),
                   expected_run_version=active['version'])
        run_path = self.root / 'data/runs/toy-session.json'
        historical = run_path.read_bytes()
        self.apply(self.update(ids['result'], outcome='invalid'))
        self.assertEqual(historical, run_path.read_bytes())
        active = IssueStore(self.root).workflow_start()['active']
        self.apply(dict(op='end', run_id=active['id'], outcome='paused',
                        summary='Result is invalid; source retained.', next_action='Design a clean replacement.',
                        evidence=[{'issue': ids['result']}]), expected_run_version=active['version'])
        self.assertEqual('paused', IssueStore(self.root).workflow_start()['last_run']['status'])

    def test_math_claim_bindings_proposals_and_existing_relations_remain_unchanged(self):
        claim = dict(snapshot(self.root, 'capsule', 'README.md', heading='H-1'), object_id='H-1')
        ids = self.apply(self.create('theorem', 'theorem', claim_ref=claim),
                         self.create('lemma', 'lemma'))['created']
        self.apply(self.relation('old-math-relation', ids['lemma'], ids['theorem'], 'requires-input-to'))
        record = self.record(ids['theorem'])
        self.assertEqual('canonical-reference', record['statement_role'])
        self.assertEqual([], record['source_refs'])
        self.assertIsNone(record['outcome'])
        self.rejects_unchanged(self.update(ids['theorem'], body='An impermissible replacement.'))
        self.apply(dict(op='propose', id=ids['theorem'], expected_version=self.record(ids['theorem'])['source_hash'],
                        statement='A narrower proposed toy claim.', reason='A proposal is not a promotion.'))
        self.assertEqual('proposed', self.record(ids['theorem'])['proposals'][0]['status'])
        self.assertEqual('current', self.index.neighbors(ids['theorem'])['items'][0]['status'])
        self.assertEqual(2, self.index.validate()['issues'])

    def test_experimental_records_are_not_mathematical_formulation_proposals(self):
        kinds = ('question', 'hypothesis', 'experiment', 'result', 'analysis', 'decision')
        ids = self.apply(*(self.create(k, k, source_refs=[self.log_ref]) for k in kinds),
                         self.create('activity', 'activity'))['created']
        for kind in kinds:
            with self.subTest(kind=kind):
                self.assertEqual('research-record', self.record(ids[kind])['statement_role'])
        self.assertEqual('operational', self.record(ids['activity'])['statement_role'])
        for kind in kinds + ('activity',):
            with self.subTest(proposal_kind=kind):
                self.rejects_unchanged(
                    self.create('would-have-been-written', 'result'),
                    dict(op='propose', id=ids[kind], expected_version=self.record(ids[kind])['source_hash'],
                         statement='This is not a mathematical formulation proposal.',
                         reason='Experimental revisions need a distinct research record.'))
        claim = dict(snapshot(self.root, 'capsule', 'README.md', heading='H-1'), object_id='H-1')
        self.apply(self.update(ids['hypothesis'], claim_ref=claim))
        self.assertEqual('canonical-reference', self.record(ids['hypothesis'])['statement_role'])
        self.rejects_unchanged(dict(op='propose', id=ids['hypothesis'],
            expected_version=self.record(ids['hypothesis'])['source_hash'],
            statement='A bound experimental record is still not a theorem.', reason='Kind governs this operation.'))

    def test_source_pagination_bounds_byte_checks_before_verification(self):
        ids, refs = self.source_chain()
        before = self.canonical()
        with patch.object(source, 'check_drift', wraps=source.check_drift) as checked:
            start = self.store.workflow_start()
            self.assertEqual(20, checked.call_count)
            self.assertEqual(20, len(start['source_checks']))
            self.assertEqual(25, start['source_checks_total'])
            self.assertTrue(start['source_checks_truncated'])
            self.assertEqual([ids['first'], ids['second']], start['source_check_ids'])
            checked.reset_mock()
            second = self.store.source_check(start['source_check_ids'],
                                             cursor=start['source_checks_next_cursor'])
            self.assertEqual(5, checked.call_count)
        self.assertIsNone(second['next_cursor'])
        self.assertFalse(second['truncated'])
        checks = start['source_checks'] + second['checks']
        self.assertEqual({r['sha256'] for r in refs}, {c['sha256'] for c in checks})
        self.assertEqual(25, len(checks))
        self.assertTrue(all(c['state'] == 'current' for c in checks))
        self.assertEqual(before, self.canonical())

    def test_cli_source_check_continues_workflow_and_doctor_cursors(self):
        ids, refs = self.source_chain()
        for command in (('workflow', 'start'), ('doctor',)):
            with self.subTest(command=command):
                first = self.call(*command)
                self.assertTrue(first['ok'])
                self.assertEqual(20, len(first['source_checks']))
                self.assertTrue(first['source_checks_truncated'])
                page = self.call('source', 'check', *first['source_check_ids'],
                                 '--limit', '3', '--cursor', first['source_checks_next_cursor'])
                checks = list(first['source_checks'])
                while True:
                    self.assertTrue(page['ok'])
                    self.assertLessEqual(len(page['checks']), 3)
                    checks.extend(page['checks'])
                    if not page['next_cursor']:
                        break
                    page = self.call('source', 'check', *first['source_check_ids'],
                                     '--limit', '3', '--cursor', page['next_cursor'])
                self.assertEqual(25, len(checks))
                self.assertEqual({r['sha256'] for r in refs}, {c['sha256'] for c in checks})
        deduplicated = self.store.source_check([ids['second'], ids['first'], ids['second']])
        self.assertEqual([ids['first'], ids['second']], deduplicated['ids'])
        self.assertEqual(25, deduplicated['total'])

    def test_source_cursor_rejects_changed_target_and_generation_without_byte_reads(self):
        ids, _ = self.source_chain()
        first = self.store.source_check([ids['first']], limit=1)
        with patch.object(source, 'check_drift', wraps=source.check_drift) as checked:
            with self.assertRaises(ix.IndexErrorDetail) as raised:
                self.store.source_check([ids['second']], limit=1, cursor=first['next_cursor'])
            self.assertEqual('INVALID_CURSOR', raised.exception.code)
            checked.assert_not_called()
        self.apply(self.update(ids['first'], notes='A real ticket revision changes query generation.'))
        with patch.object(source, 'check_drift', wraps=source.check_drift) as checked:
            with self.assertRaises(ix.IndexErrorDetail) as raised:
                self.store.source_check([ids['first']], limit=1, cursor=first['next_cursor'])
            self.assertEqual('STALE_CURSOR', raised.exception.code)
            checked.assert_not_called()
        cli = self.call('source', 'check', ids['first'], '--cursor', first['next_cursor'])
        self.assertEqual('STALE_CURSOR', cli['error']['code'])

    def test_experiment_design_is_not_an_operational_completion_blocker(self):
        ids = self.apply(self.create('design', 'experiment'),
                         self.create('execute', 'activity', status='Backlog'))['created']
        self.rejects_unchanged(self.create('invalid-followup', 'activity',
                                          blocked_by=[ids['design']]))
        self.rejects_unchanged(self.update(ids['execute'], blocked_by=[ids['design']]))
        self.apply(self.relation('design-context', ids['design'], ids['execute'], 'useful-for'))
        self.assertEqual('current', self.index.neighbors(ids['execute'])['items'][0]['status'])
        self.assertEqual([], self.store.workflow_start()['items'])


if __name__ == '__main__':
    unittest.main()
