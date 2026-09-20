"""Paper reading/review compatibility on synthetic, disposable local sources.

No real paper, project, network endpoint, or remote Git operation is used.
One disposable Git fixture has only a synthetic origin configuration so the
existing repository alias named ``paper`` can be checked without contacting it.
"""
import concurrent.futures
import copy
import json
import os
from pathlib import Path
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
import issue_sources as source
from issue_store import IssueStore
import ticket_project as project


class PaperWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ticket-paper-tests-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.library = self.base / 'papers'
        self.library.mkdir()
        self.note = self.make_note('2026-synthetic-paper')
        self.support = self.note.with_suffix('')
        self.root = self.support / 'tickets'
        self.n = 0

    def make_note(self, stem, kind='paper', body=None):
        note = self.library / (stem + '.md')
        note.write_text(
            '---\ntype: ' + kind + '\ntitle: Synthetic fixture\n'
            'year: 2026\nstatus: reading\n---\n\n' +
            (body or '# Synthetic paper\n\n## Theorem A\n\n'
             'A toy statement for source-boundary tests only.\n'),
            encoding='utf-8')
        return note

    def config(self, note=None, extracts=None):
        note = note or self.note
        return {'schema': 1, 'project_id': note.stem,
                'coverage': {'state': 'partial', 'scope': 'Synthetic reading scope',
                             'untracked': ['Other claims have not been read.']},
                'repositories': {},
                'subject': {'kind': 'paper', 'note': note.name,
                            'extracts': list(extracts or [])}}

    def enroll(self, config=None):
        project.initialize_paper(self.note, config=config)
        self.root, self.registration = project.load_paper(self.note)
        self.store = IssueStore(self.root)
        self.index = self.store.index
        return self.store

    def reject(self, function, *args, code=None, **kwargs):
        with self.assertRaises(ix.IndexErrorDetail) as caught:
            function(*args, **kwargs)
        if code:
            self.assertEqual(code, caught.exception.code, str(caught.exception))
        return caught.exception

    def call(self, *args, selector='--paper', target=None):
        completed = subprocess.run(
            [sys.executable, '-B', str(APP.parents[1] / 'scripts/research-tickets.py'),
             selector, str(target or self.note), *args],
            capture_output=True, text=True, encoding='utf-8')
        try:
            result = json.loads(completed.stdout)
        except ValueError:
            self.fail('CLI did not return JSON: ' + completed.stderr)
        self.assertEqual(0 if result['ok'] else 2, completed.returncode,
                         completed.stderr)
        return result

    def packet(self, *operations, **extra):
        self.n += 1
        return {'operation_id': 'paper-test-' + str(self.n),
                'expected_generation': self.index.refresh()['generation'],
                'operations': list(operations), **extra}

    def apply(self, *operations, **extra):
        return self.store.apply(self.packet(*operations, **extra))

    def create(self, key, kind='activity', **fields):
        return {'op': 'create', 'key': key, 'title': 'Synthetic ' + key,
                'kind': kind, 'status': 'Ready',
                'body': '## Statement and scope\n\nSynthetic bounded test.\n',
                **fields}

    def record(self, identifier):
        return self.index.refresh()['records'][identifier]

    def update(self, identifier, **changes):
        return {'op': 'update', 'id': identifier,
                'expected_version': self.record(identifier)['source_hash'],
                'changes': changes}

    def relation(self, key, origin, target, kind='reviews'):
        return {'op': 'relation-add', 'key': key, 'from': origin, 'to': target,
                'type': kind, 'route': 'Synthetic audit',
                'logic': 'Only the recorded toy version is in scope.',
                'evidence': 'Synthetic source snapshot, not a proof verdict.'}

    def note_ref(self, **kwargs):
        return source.snapshot(self.root, 'paper', self.note.name, **kwargs)

    def config_write(self, config):
        (self.root / 'project.json').write_text(json.dumps(config), encoding='utf-8')

    def begin(self, identifier):
        state = self.store.workflow_start()
        return self.apply(
            {'op': 'begin', 'run_id': 'synthetic-reading', 'issue': identifier,
             'reason': 'Read a synthetic statement', 'next_action': 'Inspect source'},
            expected_harness_version=state['harness_version'])

    def test_unenrolled_queries_and_selector_errors_do_not_create_sidecar(self):
        before = self.note.read_bytes()
        self.assertFalse(self.call('workflow', 'start')['ok'])
        self.assertFalse(self.call('--project', str(self.library), 'list')['ok'])
        self.assertFalse(self.support.exists())
        self.assertEqual(before, self.note.read_bytes())

    def test_paper_and_book_enroll_without_rewriting_notes_or_fake_readme(self):
        quoted = self.make_note('2026-quoted-key', kind='"paper"')
        quoted.write_text(quoted.read_text(encoding='utf-8').replace('type:', '"type":'), encoding='utf-8')
        for note in (self.note, self.make_note('2026-synthetic-book', kind="'book'"), quoted):
            with self.subTest(note=note.name):
                before = note.read_bytes()
                result = project.initialize_paper(note)
                root, config = project.load_paper(note)
                self.assertTrue(result['ok'])
                self.assertEqual(note.with_suffix('') / 'tickets', root)
                self.assertEqual({'kind': 'paper', 'note': note.name, 'extracts': []},
                                 config['subject'])
                self.assertEqual(note.stem, config['project_id'])
                self.assertEqual(before, note.read_bytes())
                self.assertFalse((root.parent / 'README.md').exists())
                self.assertFalse((root / 'data/harness.json').exists())
                self.assertEqual(0, IssueStore(root).index.list_issues()['total'])

    def test_only_first_frontmatter_type_and_safe_slug_are_accepted(self):
        invalid = {
            '2026-body-type': '# Synthetic\n\n---\ntype: paper\n---\n',
            '2026-wrong-type': '---\ntype: project\n---\n\ntype: paper\n',
            '2026-duplicate-type': '---\ntype: paper\ntype: book\n---\n',
            '2026-quoted-duplicate': '---\ntype: paper\n"type": project\n---\n',
            '2026-single-quoted-duplicate': "---\n'type': paper\ntype: project\n---\n",
            '2026-open-frontmatter': '---\ntype: paper\n# No closing delimiter\n',
            '2026-unquoted-unsafe type': '---\ntype: paper\n---\n',
        }
        for stem, body in invalid.items():
            with self.subTest(stem=stem):
                note = self.library / (stem + '.md')
                note.write_text(body, encoding='utf-8')
                self.reject(project.initialize_paper, note)
                self.assertFalse(note.with_suffix('').exists())

    def test_invalid_config_and_extract_paths_leave_no_sidecar(self):
        bad_configs = []
        for key, value in [('project_id', 'another-paper'), ('schema', 2)]:
            config = self.config()
            config[key] = value
            bad_configs.append(config)
        for key, value in [('kind', 'project'), ('note', 'other.md'),
                           ('note', '../' + self.note.name), ('extra', True)]:
            config = self.config()
            config['subject'][key] = value
            bad_configs.append(config)
        for extracts in [['../other.md'], ['/tmp/other.md'], ['other.md'],
                         ['content/../other.md'], ['content/a.md', 'content/a.md'],
                         ['content/a.pdf'], ['content/.env.md'], 'content/a.md']:
            config = self.config()
            config['subject']['extracts'] = extracts
            bad_configs.append(config)
        for config in bad_configs:
            with self.subTest(config=config):
                self.reject(project.initialize_paper, self.note, config=config)
                self.assertFalse(self.support.exists())

    def test_existing_sidecar_and_symlink_inputs_are_never_overwritten(self):
        self.support.mkdir()
        retained = self.support / 'user-note.md'
        retained.write_text('User content stays in place.\n', encoding='utf-8')
        self.reject(project.initialize_paper, self.note)
        self.assertEqual('User content stays in place.\n', retained.read_text(encoding='utf-8'))
        self.assertFalse(self.root.exists())
        linked_note = self.library / '2026-linked-note.md'
        symlink_or_skip(self, linked_note, self.note)
        self.reject(project.initialize_paper, linked_note)
        other = self.make_note('2026-linked-support')
        symlink_or_skip(self, other.with_suffix(''), self.support, target_is_directory=True)
        self.reject(project.initialize_paper, other)
        self.assertFalse(self.root.exists())

    def test_publish_failure_leaves_original_note_and_no_live_sidecar(self):
        before = self.note.read_bytes()
        with patch.object(Path, 'rename', side_effect=OSError('Synthetic publish failure')):
            with self.assertRaises((OSError, ix.IndexErrorDetail)):
                project.initialize_paper(self.note)
        self.assertEqual(before, self.note.read_bytes())
        self.assertFalse(self.support.exists())

    def test_parallel_initializers_publish_exactly_one_complete_store(self):
        def attempt(_):
            try:
                return project.initialize_paper(self.note)['ok']
            except ix.IndexErrorDetail as error:
                return error.code
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, range(2)))
        self.assertEqual(1, results.count(True))
        self.assertEqual(1, len([v for v in results if isinstance(v, str)]))
        root, config = project.load_paper(self.note)
        self.assertEqual(self.note.name, config['subject']['note'])
        self.assertEqual([], json.loads((root / 'data/relations.json').read_text(encoding='utf-8')))
        self.assertEqual(0, IssueStore(root).index.list_issues()['total'])

    def test_note_change_during_staging_prevents_publication(self):
        initial_writer = project._write_initial
        later_note = self.note.read_text(encoding='utf-8') + '\nUser edit during enrollment.\n'
        def stage_then_change(*args, **kwargs):
            initial_writer(*args, **kwargs)
            self.note.write_text(later_note, encoding='utf-8')
        with patch.object(project, '_write_initial', side_effect=stage_then_change):
            self.reject(project.initialize_paper, self.note, code='SOURCE_CHANGED')
        self.assertEqual(later_note, self.note.read_text(encoding='utf-8'))
        self.assertFalse(self.support.exists())

    def test_registration_identity_is_enforced_by_selector_root_and_sources(self):
        self.enroll()
        self.make_note('2026-other-paper')
        for field, value in [('project_id', '2026-other-paper'),
                             ('note', '2026-other-paper.md')]:
            with self.subTest(field=field):
                config = copy.deepcopy(self.registration)
                if field == 'note':
                    config['subject'][field] = value
                else:
                    config[field] = value
                self.config_write(config)
                self.reject(project.load_paper, self.note)
                self.reject(lambda: IssueStore(self.root).index.refresh())
                self.reject(self.note_ref)
                self.assertFalse(self.call('list', selector='--root', target=self.root)['ok'])
                self.config_write(self.registration)

    def test_display_identity_is_not_a_way_around_scope_validation(self):
        self.enroll()
        metadata = self.root / 'data/project.json'
        changed = json.loads(metadata.read_text(encoding='utf-8'))
        changed['id'] = '2026-another-paper'
        metadata.write_text(json.dumps(changed), encoding='utf-8')
        self.reject(project.load_paper, self.note)
        self.reject(self.index.refresh)
        self.reject(self.note_ref)
        self.assertFalse(self.call('doctor', selector='--root', target=self.root)['ok'])

    def test_cli_paper_init_config_and_healthy_doctor_metadata(self):
        config = self.config(extracts=['content/not-created-yet.md'])
        packet = self.base / 'registration.json'
        packet.write_text(json.dumps(config), encoding='utf-8')
        result = self.call('init', '--config-file', str(packet), '--name', 'Selected synthetic paper')
        self.assertTrue(result['ok'], result)
        report = self.call('doctor')
        self.assertTrue(report['ok'], report)
        self.assertIsNone(report['project'])
        self.assertEqual(config['subject'], report['subject'])
        self.assertEqual('../../' + self.note.name, report['capsule'])
        self.assertEqual(config['coverage'], report['coverage'])
        self.assertEqual(0, report['issues'])
        self.assertEqual([], report['source_checks'])
        self.assertFalse(report['source_checks_truncated'])
        self.assertIsNone(report['source_checks_next_cursor'])
        display = json.loads((self.root / 'data/project.json').read_text(encoding='utf-8'))
        self.assertEqual('Selected synthetic paper', display['name'])

    def test_frontmatter_does_not_create_or_duplicate_source_headings(self):
        self.enroll()
        self.reject(self.note_ref, heading='status: reading', code='SOURCE_MISMATCH')
        self.assertEqual('Theorem A', self.note_ref(heading='Theorem A')['heading'])
        self.note.write_text(self.note.read_text(encoding='utf-8') + '\n## status: reading\n\nActual body section.\n', encoding='utf-8')
        self.assertEqual('status: reading', self.note_ref(heading='status: reading')['heading'])
        self.assertEqual('current', source.check_drift(self.root, self.note_ref(heading='status: reading'))['state'])

    def test_nested_paper_library_and_extracts_stay_relative_to_note(self):
        self.library = self.library / 'gnn'
        self.library.mkdir()
        note = self.make_note('2026-nested-paper')
        extract = self.library / 'content/thesis/chapter-01.md'
        extract.parent.mkdir(parents=True)
        extract.write_text('# Chapter 1\n\nSynthetic nested extract.\n', encoding='utf-8')
        config = self.config(note, extracts=['content/thesis/chapter-01.md'])
        project.initialize_paper(note, config=config)
        root, _ = project.load_paper(note)
        ref = source.snapshot(root, 'paper', 'content/thesis/chapter-01.md', heading='Chapter 1')
        self.assertEqual(ref, source.verify_reference(root, ref))
        self.reject(source.snapshot, root, 'paper', '../content/thesis/chapter-01.md')
        self.assertEqual('../../' + note.name, IssueStore(root).workflow_start()['capsule'])

    def test_source_operation_reads_paper_registration_once(self):
        self.enroll()
        with patch.object(source, '_read_file', wraps=source._read_file) as reads:
            ref = self.note_ref(heading='Theorem A')
            paths = [call.args[1] for call in reads.call_args_list]
            self.assertEqual(1, paths.count('project.json'))
            self.assertEqual(1, paths.count('data/project.json'))
        with patch.object(source, '_read_file', wraps=source._read_file) as reads:
            source.verify_reference(self.root, ref)
            paths = [call.args[1] for call in reads.call_args_list]
            self.assertEqual(1, paths.count('project.json'))
            self.assertEqual(1, paths.count('data/project.json'))

    def test_warm_cache_rechecks_note_identity_outside_the_ticket_inventory(self):
        self.enroll()
        self.apply(self.create('cached-reading'))
        self.assertEqual(1, self.index.list_issues()['total'])
        self.assertEqual(1, self.index.list_issues()['total'])
        original = self.note.read_text(encoding='utf-8')
        self.note.write_text(original.replace('type: paper', 'type: project', 1), encoding='utf-8')
        self.reject(self.index.list_issues)
        self.reject(project.load_paper, self.note)
        self.reject(self.note_ref)
        self.assertFalse(self.call('list', selector='--root', target=self.root)['ok'])
        self.note.write_text(original, encoding='utf-8')
        self.assertEqual(1, self.index.list_issues()['total'])
        self.note.rename(self.library / '2026-moved-paper.md')
        self.reject(self.index.list_issues)

    def test_paper_sources_allow_only_own_note_and_explicit_extracts(self):
        content = self.library / 'content'
        content.mkdir()
        extract = content / 'synthetic.md'
        extract.write_text('# Extract\n\n## Lemma B\n\nSynthetic text.\n', encoding='utf-8')
        unlisted = content / 'unlisted.md'
        unlisted.write_text('# Unlisted\n', encoding='utf-8')
        other = self.make_note('2026-other-paper')
        self.enroll(self.config(extracts=['content/synthetic.md']))
        self.assertEqual('working', self.note_ref()['mode'])
        ref = source.snapshot(self.root, 'paper', 'content/synthetic.md', heading='Lemma B')
        self.assertEqual(ref, source.verify_reference(self.root, ref))
        for path in (other.name, 'content/unlisted.md', 'content/synthetic.md.bak',
                     '../' + self.note.name, str(self.note)):
            with self.subTest(path=path):
                self.reject(source.snapshot, self.root, 'paper', path)
        audit = self.support / 'audit.md'
        audit.write_text('# Scoped audit\n', encoding='utf-8')
        self.assertEqual('working', source.snapshot(self.root, 'capsule', 'audit.md')['mode'])
        self.reject(source.snapshot, self.root, 'capsule', '../../' + self.note.name)
        self.reject(source.snapshot, self.root, 'paper', 'tickets/project.json')
        extract.unlink()
        self.assertEqual('unavailable', source.check_drift(self.root, ref)['state'])

    def test_allowlisted_source_symlinks_cannot_escape_after_enrollment(self):
        content = self.library / 'content'
        content.mkdir()
        extract = content / 'synthetic.md'
        extract.write_text('# Original extract\n', encoding='utf-8')
        outside = self.base / 'outside.md'
        outside.write_text('# Outside scope\n', encoding='utf-8')
        self.enroll(self.config(extracts=['content/synthetic.md']))
        extract.unlink()
        symlink_or_skip(self, extract, outside)
        self.reject(source.snapshot, self.root, 'paper', 'content/synthetic.md')
        extract.unlink()
        content.rename(self.base / 'original-content')
        symlink_or_skip(self, content, self.base / 'original-content', target_is_directory=True)
        (self.base / 'original-content/synthetic.md').write_text('# Relocated\n', encoding='utf-8')
        self.reject(source.snapshot, self.root, 'paper', 'content/synthetic.md')

    def test_logical_paper_alias_is_working_only_and_cannot_be_shadowed(self):
        config = self.config()
        config['repositories']['paper'] = {'path': str(self.base),
                                           'origin': 'https://example.invalid/test/repo.git'}
        self.reject(project.initialize_paper, self.note, config=config)
        self.assertFalse(self.support.exists())
        self.enroll()
        self.reject(source.snapshot, self.root, 'paper', self.note.name, commit='1' * 40)

    def test_existing_project_git_repository_alias_paper_still_supports_commits(self):
        repo = self.base / 'synthetic-repo'
        repo.mkdir()
        environment = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        environment.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1',
                           GIT_TERMINAL_PROMPT='0')
        def git(*args):
            return subprocess.run(['git', '-C', str(repo), *args], env=environment,
                                  capture_output=True, text=True, check=True, encoding='utf-8').stdout.strip()
        git('init', '-q')
        git('config', 'user.name', 'Synthetic Paper Test')
        git('config', 'user.email', 'paper-test@example.org')
        git('config', 'commit.gpgsign', 'false')
        git('config', 'core.hooksPath', str(self.base / 'no-hooks'))
        origin = 'https://example.invalid/synthetic/paper.git'
        git('config', 'remote.origin.url', origin)
        (repo / 'proof.md').write_text('# Exact synthetic revision\n', encoding='utf-8')
        git('add', 'proof.md')
        git('commit', '-qm', 'Synthetic local fixture')
        revision = git('rev-parse', 'HEAD')
        capsule = self.base / '2026-synthetic-project'
        capsule.mkdir()
        (capsule / 'README.md').write_text('# Existing project fixture\n', encoding='utf-8')
        config = {'schema': 1, 'project_id': capsule.name,
                  'coverage': {'state': 'partial', 'scope': 'Compatibility test', 'untracked': []},
                  'repositories': {'paper': {'path': str(repo), 'origin': origin}}}
        project.initialize(capsule, config=config)
        root, _ = project.load_project(capsule)
        ref = source.snapshot(root, 'paper', 'proof.md', commit=revision)
        self.assertEqual('commit', ref['mode'])
        self.assertEqual(ref, source.verify_reference(root, ref))
        (repo / 'proof.md').write_text('# Later working revision\n', encoding='utf-8')
        check = source.check_drift(root, ref)
        self.assertEqual('changed', check['state'])
        self.assertEqual('verified', check['reference_state'])

    def test_source_drift_preserves_old_review_and_new_review_gets_new_reference(self):
        self.enroll()
        old_ref = self.note_ref()
        result = self.apply(self.create('review-v1', 'analysis', source_refs=[old_ref],
                                        tags=['mode:reading', 'finding:gap']))
        old_id = result['created']['review-v1']
        before = (self.root / self.record(old_id)['path']).read_bytes()
        self.note.write_text(self.note.read_text(encoding='utf-8') + '\nA later source revision.\n', encoding='utf-8')
        checks = self.store.source_check([old_id])['checks']
        self.assertEqual('changed', checks[0]['state'])
        self.reject(source.verify_reference, self.root, old_ref, code='SOURCE_MISMATCH')
        new_ref = self.note_ref()
        result = self.apply(self.create('review-v2', 'analysis', source_refs=[new_ref],
                                        tags=['mode:reading', 'finding:gap']))
        new_id = result['created']['review-v2']
        self.assertNotEqual(old_id, new_id)
        self.assertNotEqual(old_ref['sha256'], new_ref['sha256'])
        self.assertEqual(before, (self.root / self.record(old_id)['path']).read_bytes())
        self.assertEqual([old_ref], self.record(old_id)['source_refs'])
        self.assertEqual([new_ref], self.record(new_id)['source_refs'])

    def test_ambiguous_heading_requires_whole_file_fallback(self):
        self.note.write_text(self.note.read_text(encoding='utf-8') + '\n## Theorem A\n\nA second occurrence.\n', encoding='utf-8')
        self.enroll()
        self.reject(self.note_ref, heading='Theorem A')
        ref = self.note_ref()
        ref['object_id'] = 'Synthetic-Theorem-A-at-page-2'
        self.assertNotIn('heading', ref)
        self.assertEqual(ref, source.verify_reference(self.root, ref))

    def test_two_paper_stores_keep_same_local_ids_and_sources_isolated(self):
        self.enroll()
        first = self.apply(self.create('first-paper-activity'))['created']['first-paper-activity']
        other = self.make_note('2026-other-paper')
        project.initialize_paper(other)
        other_root, _ = project.load_paper(other)
        other_store = IssueStore(other_root)
        result = other_store.apply({'operation_id': 'other-paper-operation',
                                    'expected_generation': other_store.index.refresh()['generation'],
                                    'operations': [self.create('other-paper-activity')]})
        second = result['created']['other-paper-activity']
        self.assertEqual('RES-1', first)
        self.assertEqual(first, second)
        self.assertNotEqual(self.record(first)['title'],
                            other_store.index.refresh()['records'][second]['title'])
        self.reject(source.snapshot, self.root, 'paper', other.name)
        self.reject(source.snapshot, other_root, 'paper', self.note.name)

    def test_bound_statement_is_immutable_and_done_only_completes_activity(self):
        self.enroll()
        ref = dict(self.note_ref(heading='Theorem A'), object_id='Thm-A')
        created = self.apply(self.create('claim', 'theorem', claim_ref=ref),
                             self.create('audit-activity'))['created']
        claim, activity = created['claim'], created['audit-activity']
        original = self.index.get_section(claim)['content']
        self.reject(self.apply, self.update(claim, body='A changed theorem.'), code='PROMOTION_REQUIRED')
        self.reject(self.apply, self.update(claim, status='Done'))
        self.apply({'op': 'propose', 'id': claim,
                    'expected_version': self.record(claim)['source_hash'],
                    'statement': 'A candidate weaker statement.', 'reason': 'Synthetic gap finding.'})
        self.apply(self.update(activity, status='Done'))
        self.assertEqual(original, self.index.get_section(claim)['content'])
        self.assertEqual('proposed', self.record(claim)['proposals'][0]['status'])
        self.assertEqual('canonical-reference', self.record(claim)['statement_role'])
        self.assertEqual('Done', self.record(activity)['status'])
        self.assertNotEqual('Done', self.record(claim)['status'])

    def test_claim_version_update_stales_review_relation_without_erasing_history(self):
        self.enroll()
        ref = dict(self.note_ref(), object_id='Thm-A')
        created = self.apply(self.create('claim', 'theorem', claim_ref=ref),
                             self.create('review', 'analysis', source_refs=[ref]),
                             self.relation('review-v1', '@review', '@claim'))['created']
        self.note.write_text(self.note.read_text(encoding='utf-8') + '\nSource revision two.\n', encoding='utf-8')
        new_ref = dict(self.note_ref(), object_id='Thm-A')
        self.apply(self.update(created['claim'], claim_ref=new_ref))
        historical = self.index.neighbors(created['claim'], include_noncurrent=True)['items']
        self.assertEqual(1, len(historical))
        self.assertEqual('needs-review', historical[0]['status'])
        self.assertEqual(ref, historical[0]['to_version']['claim_ref'])
        self.assertEqual([ref], self.record(created['review'])['source_refs'])
        self.assertEqual(0, self.index.neighbors(created['claim'])['total'])

    def seed_tagged(self):
        return self.apply(
            self.create('both', tags=['paper:one', 'mode:reading']),
            self.create('paper-only', tags=['paper:one']),
            self.create('split-label', tags=['paper:one'], labels=['mode:reading']),
            self.create('other', tags=['paper:two', 'mode:reading']))['created']

    def test_multi_tag_queries_use_and_across_tags_and_labels_and_bound_input(self):
        self.enroll()
        ids = self.seed_tagged()
        self.assertEqual(3, self.index.list_issues(tag='paper:one')['total'])
        result = self.index.list_issues(tag=['paper:one', 'mode:reading'])
        self.assertEqual({ids['both'], ids['split-label']}, {v['id'] for v in result['items']})
        self.assertEqual(0, self.index.list_issues(tag=['paper:one', 'missing'])['total'])
        for bad in ([''], [1], ' ', ['tag-' + str(n) for n in range(21)]):
            with self.subTest(tag=bad):
                self.reject(self.index.list_issues, tag=bad)

    def test_multi_tag_cursors_normalize_order_and_duplicates_but_not_new_filters(self):
        self.enroll()
        self.seed_tagged()
        first = self.index.list_issues(tag=['paper:one', 'mode:reading'], limit=1)
        second = self.index.list_issues(tag=['mode:reading', 'paper:one', 'paper:one'],
                                       limit=1, cursor=first['next_cursor'])
        self.assertNotEqual(first['items'][0]['id'], second['items'][0]['id'])
        self.assertFalse(second['truncated'])
        self.reject(self.index.list_issues, tag=['paper:one'], limit=1,
                    cursor=first['next_cursor'], code='INVALID_CURSOR')

    def test_cli_repeated_tag_applies_to_list_search_and_workflow(self):
        self.enroll()
        ids = self.seed_tagged()
        expected = {ids['both'], ids['split-label']}
        for command in (['list'], ['search', 'Synthetic'], ['workflow', 'start']):
            with self.subTest(command=command):
                result = self.call(*command, '--tag', 'paper:one', '--tag', 'mode:reading')
                self.assertTrue(result['ok'], result)
                self.assertEqual(expected, {v['id'] for v in result['items']})

    def test_filtered_workflow_preserves_active_last_run_and_returns_scope_context(self):
        self.enroll()
        ids = self.seed_tagged()
        active_id = ids['other']
        self.begin(active_id)
        active = self.store.workflow_start(tag=['paper:one', 'mode:reading'])
        self.assertEqual(active_id, active['active']['issue'])
        self.assertEqual('../../' + self.note.name, active['capsule'])
        self.assertEqual({ids['both'], ids['split-label']}, {v['id'] for v in active['items']})
        self.assertTrue(all('tags' in item for item in active['items']))
        self.apply({'op': 'end', 'run_id': 'synthetic-reading', 'outcome': 'paused',
                    'summary': 'Synthetic session checkpoint.', 'next_action': 'Resume later'},
                   expected_run_version=active['active']['version'])
        ended = self.store.workflow_start(tag=['paper:one', 'mode:reading'])
        self.assertIsNone(ended['active'])
        self.assertEqual(active_id, ended['last_run']['issue'])
        self.assertEqual('paused', ended['last_run']['status'])


if __name__ == '__main__':
    unittest.main()
