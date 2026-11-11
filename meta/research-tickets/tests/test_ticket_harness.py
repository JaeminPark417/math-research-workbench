"""Observable integration scenarios for project enrollment and research continuity."""
import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from ticket_test_support import symlink_or_skip

sys.dont_write_bytecode = True
APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / 'scripts'))
import issue_index as ix
from issue_store import IssueStore
from issue_sources import snapshot
from ticket_project import initialize, load_project


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ticket-harness-')
        self.project = Path(self.temp.name).resolve() / '2026-demo'
        self.project.mkdir()
        self.capsule = self.project / 'README.md'
        self.capsule.write_text('# Project\n\n## Claim-A\n\nCanonical assertion A.\n\n## Next steps\n\nAn unindexed route.\n', encoding='utf-8')
        self.n = 0

    def tearDown(self):
        self.temp.cleanup()

    def enroll(self):
        initialize(self.project)
        self.root, self.config = load_project(self.project)
        self.store = IssueStore(self.root)
        self.ref = dict(snapshot(self.root, 'capsule', 'README.md', heading='Claim-A'), object_id='Claim-A')

    def call(self, *args):
        p = subprocess.run([sys.executable, '-B', str(APP.parents[1] / 'scripts/research-tickets.py'), '--project', str(self.project), *args], capture_output=True, text=True, encoding='utf-8')
        value = json.loads(p.stdout)
        self.assertEqual(0 if value['ok'] else 2, p.returncode, p.stderr)
        return value

    def packet(self, *ops, **extra):
        self.n += 1
        return dict(operation_id='intent-' + str(self.n), expected_generation=self.store.index.refresh()['generation'], operations=list(ops), **extra)

    def create(self, key, kind='activity', **kwargs):
        return dict(op='create', key=key, kind=kind, title=key, body='Working record.', status='Ready', **kwargs)

    def apply(self, *ops, **extra):
        return self.store.apply(self.packet(*ops, **extra))

    def version(self, identifier):
        return self.store.index.refresh()['records'][identifier]['source_hash']

    def reject(self, code, fn, *args):
        with self.assertRaises(ix.IndexErrorDetail) as raised:
            fn(*args)
        self.assertEqual(code, raised.exception.code)

    def test_resume_defaults_are_scoped_to_the_live_project_activity(self):
        self.enroll()
        ids = self.apply(self.create('route'), self.create('other'), self.create('failure', 'obstruction'),
                         self.create('gap', 'obligation'), self.create('other-gap', 'obligation'))['created']
        links = {'activity': ids['route'], 'failed': ids['failure'], 'gaps': [ids['gap']]}
        field = 'resume_links: ' + json.dumps(links)
        def overview(fields):
            self.capsule.write_text('---\n' + fields + '\n---\n# Project\n', encoding='utf-8')
        def resume(*options):
            return self.call('workflow', 'resume', '--json', *options)

        overview(field)
        view = resume()
        self.assertEqual(('candidate', ids['route'], ids['failure'], ids['gap']),
                         (view['ticket_role'], view['ticket']['id'], view['failed_route']['id'], view['open_gaps'][0]['id']))
        self.assertEqual(ids['other-gap'], resume('--gap', ids['other-gap'])['open_gaps'][0]['id'])
        self.assertIsNone(resume('--activity', ids['other'])['failed_route'])
        for fields in ('', field + '\n' + field, 'resume_links: {"activity":"RES-99999"}'):
            overview(fields)
            view = resume()
            self.assertIsNone(view['ticket'])
            self.assertIsNone(view['failed_route'])
        overview(field)
        self.apply(dict(op='begin', run_id='other', issue=ids['other'], reason='Selected a different route',
                        next_action='Check its own evidence'), expected_harness_version=self.store.workflow_start()['harness_version'])
        view = resume()
        self.assertEqual(('active', ids['other'], None, []),
                         (view['ticket_role'], view['ticket']['id'], view['failed_route'], view['open_gaps']))

    def test_unenrolled_queries_do_not_create_files(self):
        before = {str(p): p.read_bytes() for p in self.project.rglob('*') if p.is_file()}
        self.assertEqual('NOT_CONFIGURED', self.call('workflow', 'start')['error']['code'])
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.project.rglob('*') if p.is_file()})

    def test_init_empty_idempotence_and_partial_coverage(self):
        self.assertTrue(self.call('init')['ok'])
        before = self.capsule.read_bytes()
        result = self.call('doctor')
        self.assertTrue(result['ok'])
        self.assertEqual(0, result['issues'])
        self.assertEqual('partial', result['coverage']['state'])
        self.assertEqual('ALREADY_CONFIGURED', self.call('init')['error']['code'])
        self.assertEqual(before, self.capsule.read_bytes())

    def test_parallel_enrollment_never_overwrites(self):
        def attempt(_):
            try:
                return initialize(self.project)['ok']
            except ix.IndexErrorDetail as error:
                return error.code
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            values = list(pool.map(attempt, range(2)))
        self.assertEqual(1, values.count(True))
        self.assertIn(next(v for v in values if v is not True), ('ALREADY_CONFIGURED', 'INDEX_BUSY'))
        self.assertEqual('2026-demo', load_project(self.project)[1]['project_id'])

    def test_invalid_enrollment_never_publishes_a_registration(self):
        self.reject('INVALID_CONFIG', initialize, self.project, None, {})
        self.assertFalse((self.project / 'tickets').exists())
        config = {'schema': 1, 'project_id': self.project.name, 'coverage': {'state': 'partial', 'scope': 'Initial', 'untracked': ['x' * 2000] * 50}, 'repositories': {}}
        self.reject('INVALID_CONFIG', initialize, self.project, None, config)
        self.assertFalse((self.project / 'tickets').exists())

    def test_bound_claim_proposal_preserves_source_and_body(self):
        self.enroll()
        result = self.apply(self.create('claim', 'theorem', claim_ref=self.ref))
        identifier = result['created']['claim']
        body = self.store.index.get_section(identifier)
        before = self.capsule.read_bytes()
        update = dict(op='update', id=identifier, expected_version=self.version(identifier), changes={'body': 'Changed assertion'})
        self.reject('PROMOTION_REQUIRED', self.apply, update)
        for n in range(2):
            self.apply(dict(op='propose', id=identifier, expected_version=self.version(identifier), statement='Weaker formulation ' + str(n), reason='Counterexample bounds the scope'))
        record = self.store.index.refresh()['records'][identifier]
        self.assertEqual(2, len(record['proposals']))
        self.assertTrue(all(p['status'] == 'proposed' and p['base_ref'] == self.ref for p in record['proposals']))
        self.assertEqual('canonical-reference', record['statement_role'])
        self.assertEqual(before, self.capsule.read_bytes())
        self.assertEqual(body['content'], self.store.index.get_section(identifier)['content'])
        for ref in (None, [], {'object_id': 'Other'}, dict(self.ref, path='other.md'), dict(self.ref, heading='Next steps'), dict(self.ref, repository='other')):
            self.reject('INVALID_ARGUMENT', self.apply, dict(op='update', id=identifier, expected_version=self.version(identifier), changes={'claim_ref': ref}))

    def test_new_claims_are_explicit_proposals_and_cannot_be_done(self):
        self.enroll()
        self.apply(self.create('new-claim', 'lemma'))
        record = self.store.index.refresh()['records']['RES-1']
        self.assertEqual('proposed', record['statement_role'])
        self.reject('INVALID_ARGUMENT', self.apply, dict(op='update', id='RES-1', expected_version=self.version('RES-1'), changes={'status': 'Done'}))

    def test_claim_reference_requires_real_hash_and_object_id(self):
        self.enroll()
        self.reject('SOURCE_MISMATCH', self.apply, self.create('bad', 'lemma', claim_ref=dict(self.ref, sha256='0' * 64)))
        ref = dict(self.ref); ref.pop('object_id')
        self.reject('INVALID_ARGUMENT', self.apply, self.create('bad', 'lemma', claim_ref=ref))
        self.assertEqual({}, self.store.index.refresh()['records'])

    def test_source_drift_is_visible_without_canonical_mutation(self):
        self.enroll()
        self.apply(self.create('claim', 'theorem', claim_ref=self.ref), self.create('audit', parent='@claim'))
        before = {str(p): p.read_bytes() for p in (self.root / 'data').rglob('*') if p.is_file()}
        self.capsule.write_text(self.capsule.read_text(encoding='utf-8').replace('assertion A', 'assertion B'), encoding='utf-8')
        start = self.store.workflow_start()
        self.assertEqual('changed', start['source_checks'][0]['state'])
        self.assertEqual('partial', start['coverage']['state'])
        self.assertEqual(before, {str(p): p.read_bytes() for p in (self.root / 'data').rglob('*') if p.is_file()})

    def test_registration_change_invalidates_write_generation(self):
        self.enroll()
        packet = self.packet(self.create('stale'))
        config = dict(self.config, coverage=dict(self.config['coverage'], scope='Changed scope'))
        (self.root / 'project.json').write_text(json.dumps(config), encoding='utf-8')
        self.reject('CONFLICT', self.store.apply, packet)
        self.assertEqual({}, self.store.index.refresh()['records'])

    def test_rebinding_source_marks_edges_stale_and_retains_original_version(self):
        self.enroll()
        edge = dict(op='relation-add', key='input', type='requires-input-to', route='route-A', logic='conditional input', evidence='source snapshot')
        edge.update({'from': '@claim', 'to': '@lemma'})
        self.apply(self.create('claim', 'theorem', claim_ref=self.ref), self.create('lemma', 'lemma'), edge)
        before = self.store.index.neighbors('RES-1')['items'][0]['from_version']
        self.assertEqual(self.ref, before['claim_ref'])
        self.capsule.write_text(self.capsule.read_text(encoding='utf-8') + '\nUpdated canonical source.\n', encoding='utf-8')
        ref = dict(snapshot(self.root, 'capsule', 'README.md', heading='Claim-A'), object_id='Claim-A')
        self.apply(dict(op='update', id='RES-1', expected_version=self.version('RES-1'), changes={'claim_ref': ref}))
        self.assertEqual([], self.store.index.neighbors('RES-1')['items'])
        historical = self.store.index.neighbors('RES-1', include_noncurrent=True)['items'][0]
        self.assertEqual('needs-review', historical['status'])
        self.assertEqual(before, historical['from_version'])

    def test_two_sessions_reference_one_persistent_math_run(self):
        self.enroll()
        ledger = self.project / 'research-run.md'
        ledger.write_text('# Run-1\n\n## Obl-1\n\nUnresolved.\n', encoding='utf-8')
        ref = snapshot(self.root, 'capsule', 'research-run.md')
        math_run = {'run_id': 'Run-1', 'source': ref, 'object_ids': ['Obl-1']}
        self.apply(self.create('work'))
        for session in ('session-1', 'session-2'):
            start = self.store.workflow_start()
            self.apply(dict(op='begin', run_id=session, issue='RES-1', reason='Resume obligation', next_action='Inspect evidence', math_run=math_run), expected_harness_version=start['harness_version'])
            active = self.store.workflow_start()['active']
            self.assertEqual(math_run, active['math_run'])
            self.apply(dict(op='end', run_id=session, outcome='paused', summary='Scope checked', next_action='Continue later', evidence=[{'source': ref}]), expected_run_version=active['version'])
            resumed = IssueStore(self.root).workflow_start()
            self.assertIsNone(resumed['active'])
            self.assertEqual(session, resumed['last_run']['id'])
            self.assertEqual('Run-1', resumed['last_run']['math_run']['run_id'])
            self.assertEqual('Continue later', resumed['last_run']['next_action'])
        self.assertEqual('Unresolved.', ledger.read_text(encoding='utf-8').strip().splitlines()[-1])
        self.assertEqual(2, len(list((self.root / 'data/runs').glob('*.json'))))
        for p in (self.root / 'data/runs').glob('*.json'):
            self.assertEqual('Run-1', json.loads(p.read_text(encoding='utf-8'))['math_run']['run_id'])

    def test_project_namespaces_are_isolated(self):
        self.enroll(); self.apply(self.create('first'))
        second = self.project.parent / '2026-second'; second.mkdir()
        (second / 'README.md').write_text('# Second\n', encoding='utf-8')
        initialize(second)
        other = IssueStore(second / 'tickets')
        packet = dict(operation_id='intent-1', expected_generation=other.index.refresh()['generation'], operations=[self.create('second')])
        self.assertEqual('RES-1', other.apply(packet)['created']['second'])
        self.assertEqual('first', self.store.index.refresh()['records']['RES-1']['title'])

    def test_config_symlink_and_path_mismatch_are_rejected(self):
        self.enroll()
        config = self.root / 'project.json'; saved = self.root / 'saved.json'
        config.rename(saved); symlink_or_skip(self, config, saved)
        self.reject('UNSAFE_PATH', load_project, self.project)
        config.unlink(); saved.rename(config)
        data = json.loads(config.read_text(encoding='utf-8')); data['project_id'] = 'another'
        config.write_text(json.dumps(data), encoding='utf-8')
        self.reject('INVALID_CONFIG', load_project, self.project)

    def test_cli_source_roundtrip(self):
        self.enroll()
        result = self.call('source', 'snapshot', 'capsule', 'README.md', '--heading', 'Claim-A', '--object-id', 'Claim-A')
        self.assertEqual(self.ref, result['source'])


if __name__ == '__main__':
    unittest.main()
