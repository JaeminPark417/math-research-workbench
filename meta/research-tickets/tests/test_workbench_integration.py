"""Synthetic checks for Workbench routing, publication and portable I/O."""
import errno
import contextlib
import io
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
APP = Path(__file__).resolve().parents[1]
ROOT = APP.parents[1]
sys.path.insert(0, str(APP / 'scripts'))
import ticket_fs as fs
import issue_index as ix
from issue_sources import validate_reference
from issue_store import IssueStore
from ticket_project import initialize, initialize_paper


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='workbench-tickets-')
        self.root = Path(self.temp.name).resolve()
        self.project = self.root / 'projects/synthetic-project'
        self.project.mkdir(parents=True)
        (self.project / 'README.md').write_text('# Synthetic project\n', encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def workspace(self):
        for name in ('inbox', 'ideas', 'papers', 'notes', 'projects'):
            (self.root / name).mkdir(exist_ok=True)
        (self.root / 'scripts').mkdir(exist_ok=True)
        for name in ('vault-lint.py', 'formalization_manifest.py'):
            shutil.copyfile(ROOT / 'scripts' / name, self.root / 'scripts' / name)
        shutil.copytree(APP / 'scripts', self.root / 'meta/research-tickets/scripts')

    def lint(self):
        return subprocess.run([sys.executable, '-B', str(self.root / 'scripts/vault-lint.py')],
                              capture_output=True, text=True, encoding='utf-8')

    def create_activity(self, store):
        return store.apply(dict(operation_id='synthetic-create',
                                expected_generation=store.index.refresh()['generation'],
                                operations=[dict(op='create', key='audit', kind='activity',
                                                 title='Synthetic audit', status='Ready',
                                                 body='## Statement and scope\n\nFind a gap.\n')]))

    def test_lint_routes_project_tickets_and_preserves_unrelated_note_checks(self):
        self.workspace()
        initialize(self.project)
        store = IssueStore(self.project / 'tickets')
        self.create_activity(store)
        before = {p: p.read_bytes() for p in (self.project / 'tickets/data').rglob('*') if p.is_file()}
        result = self.lint()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        (self.project / 'tickets/unrelated.md').write_text('---\ntype: invented\n---\n', encoding='utf-8')
        result = self.lint()
        self.assertNotEqual(0, result.returncode)
        self.assertIn('unsupported type', result.stdout)

    def test_lint_rejects_corrupt_store_and_missing_registration(self):
        self.workspace()
        (self.project / 'tickets').mkdir()
        self.assertNotEqual(0, self.lint().returncode)
        (self.project / 'tickets').rmdir()
        initialize(self.project)
        self.create_activity(IssueStore(self.project / 'tickets'))
        (self.project / 'tickets/data/relations.json').write_text('{}', encoding='utf-8')
        result = self.lint()
        self.assertNotEqual(0, result.returncode)
        self.assertIn('invalid research tickets', result.stdout)

    def test_lint_routes_nested_paper_store_without_changing_note(self):
        self.workspace()
        note = self.root / 'papers/topic/example-paper.md'
        note.parent.mkdir()
        note.write_text('---\ntype: paper\ntitle: "Synthetic paper"\nauthors: []\nyear: 2026\n'
                        'status: queued\ncitation_status: unverified\nadded: 2026-01-01\nlanguage: en\n---\n', encoding='utf-8')
        original = note.read_bytes()
        initialize_paper(note)
        self.create_activity(IssueStore(note.with_suffix('') / 'tickets'))
        result = self.lint()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(original, note.read_bytes())

    def test_cache_does_not_store_absolute_workspace_path(self):
        initialize(self.project)
        store = IssueStore(self.project / 'tickets')
        self.create_activity(store)
        text = (self.project / 'tickets/.cache/issues-index.json').read_text(encoding='utf-8')
        self.assertNotIn(str(self.root), text)
        self.assertEqual(ix.digest(str(store.index.root)), json.loads(text)['root'])

    def test_windows_inventory_detects_edit_when_all_stat_values_are_unchanged(self):
        initialize(self.project)
        store = IssueStore(self.project / 'tickets')
        self.create_activity(store)
        path = self.project / 'tickets/data/issues/res-1.md'
        with patch.object(ix, 'HASH_INVENTORY', True), patch.object(ix, '_signature', return_value=[1, 2, 3, 4, 5]):
            store.index.refresh()
            path.write_text(path.read_text(encoding='utf-8').replace('Synthetic audit', 'Synthetic check'), encoding='utf-8')
            result = store.index.refresh()
            self.assertEqual('Synthetic check', result['records']['RES-1']['title'])
            self.assertGreater(store.index.last_stats['inventory_bytes_read'], 0)
            store.index.refresh()
            self.assertTrue(store.index.last_stats['cache_reused'])

    def test_crlf_ticket_parses_without_changing_source_hash_or_bytes(self):
        initialize(self.project)
        store = IssueStore(self.project / 'tickets')
        self.create_activity(store)
        path = self.project / 'tickets/data/issues/res-1.md'
        content = path.read_bytes().replace(b'\n', b'\r\n')
        path.write_bytes(content)
        result = store.index.refresh()['records']['RES-1']
        self.assertEqual('Synthetic audit', result['title'])
        self.assertEqual(ix.digest(content), result['source_hash'])
        self.assertEqual(content, path.read_bytes())
        self.assertIn('Find a gap.', store.index.get_section('RES-1', section='Statement and scope')['content'])

    def test_crlf_update_keeps_unknown_fields_and_untouched_body_bytes(self):
        initialize(self.project)
        store = IssueStore(self.project / 'tickets')
        self.create_activity(store)
        path = self.project / 'tickets/data/issues/res-1.md'
        raw = path.read_bytes().replace(b'desk_schema: 2', b'desk_schema: 2\ncustom_field: {"keep":true}')
        raw = raw.replace(b'\n', b'\r\n')
        path.write_bytes(raw)
        snapshot = store.index.refresh()
        store.apply(dict(operation_id='crlf-update', expected_generation=snapshot['generation'],
                         operations=[dict(op='update', id='RES-1', expected_version=ix.digest(raw), changes={'title':'Updated audit'})]))
        result = path.read_bytes()
        self.assertIn(b'custom_field: {"keep":true}\r\n', result)
        self.assertEqual(raw.split(b'\r\n---\r\n', 1)[1], result.split(b'\r\n---\r\n', 1)[1])

    def test_dotted_paper_support_cannot_borrow_another_stores_validation(self):
        self.workspace()
        note = self.root / 'papers/example.md'
        note.write_text('---\ntype: paper\ntitle: "Synthetic paper"\nauthors: []\nyear: 2026\n'
                        'status: queued\ncitation_status: unverified\nadded: 2026-01-01\nlanguage: en\n---\n', encoding='utf-8')
        initialize_paper(note)
        forged = self.root / 'papers/example.v2/tickets/data/issues/res-1.md'
        forged.parent.mkdir(parents=True)
        forged.write_text('---\ntype: invented\n---\n', encoding='utf-8')
        result = self.lint()
        self.assertNotEqual(0, result.returncode)
        self.assertIn('ticket store does not match', result.stdout)
        self.assertIn('unsupported type', result.stdout)

    def test_missing_canonical_file_has_explicit_restore_error(self):
        initialize(self.project)
        store = IssueStore(self.project / 'tickets')
        (self.project / 'tickets/data/relations.json').unlink()
        with self.assertRaises(ix.IndexErrorDetail) as error:
            store.index.refresh()
        self.assertEqual('MISSING_SOURCE', error.exception.code)
        self.assertEqual('data/relations.json', error.exception.details['path'])

    def test_unicode_race_stays_inside_cli_json_envelope(self):
        import issues
        initialize(self.project)
        output = io.StringIO()
        malformed = UnicodeDecodeError('utf-8', b'\xff', 0, 1, 'synthetic race')
        with patch.object(ix.IssueIndex, 'list_issues', side_effect=malformed), contextlib.redirect_stdout(output):
            code = issues.main(['--project', str(self.project), 'list'])
        self.assertEqual(2, code)
        self.assertEqual('INVALID_DATA', json.loads(output.getvalue())['error']['code'])
        self.assertNotIn('Traceback', output.getvalue())

    def test_lock_and_recovery_require_explicit_guards(self):
        initialize(self.project)
        store = IssueStore(self.project / 'tickets')
        with self.assertRaises(ix.IndexErrorDetail) as error:
            store.index._assert_lock_current()
        self.assertEqual('LOCK_REQUIRED', error.exception.code)
        with self.assertRaises(ix.IndexErrorDetail) as error:
            store.recover('keep-current')
        self.assertEqual('INVALID_ARGUMENT', error.exception.code)

    def test_source_paths_reject_windows_drives_and_alternate_streams(self):
        for path in ('C:/private/note.md', 'notes/file.md:alternate.md', 'C:note.md'):
            with self.subTest(path=path), self.assertRaises(ix.IndexErrorDetail):
                validate_reference(dict(repository='capsule', mode='working', path=path, sha256='a'*64))

    def test_native_binary_utf8_roundtrip_and_no_overwrite(self):
        directory = fs.open_dir(self.root)
        try:
            fd = fs.open_file('new.md', os.O_WRONLY | os.O_CREAT | os.O_EXCL, parent=directory)
            try:
                os.write(fd, '수학\r\nbyte-exact\n'.encode('utf-8'))
                os.fsync(fd)
            finally:
                os.close(fd)
            fs.link('new.md', 'published.md', directory)
            with self.assertRaises(FileExistsError):
                fs.link('new.md', 'published.md', directory)
            self.assertEqual('수학\r\nbyte-exact\n'.encode('utf-8'), (self.root / 'published.md').read_bytes())
        finally:
            fs.close_dir(directory)

    def test_windows_lock_contention_mapping(self):
        # Exercise this branch on every OS; native contention/process-death
        # behavior is exercised by test_issue_index on the actual platform.
        class WindowsLock:
            LK_NBLCK = 2
            @staticmethod
            def locking(fd, mode, count):
                raise OSError(errno.EACCES, 'Synthetic locked byte')
        with (self.root / 'lock').open('w+b') as stream:
            with patch.object(fs, 'WINDOWS', True), patch.dict(sys.modules, msvcrt=WindowsLock):
                with self.assertRaises(BlockingIOError):
                    fs.try_lock(stream.fileno())

    def test_strict_release_has_no_real_store_or_runtime_allowlist(self):
        spec = importlib.util.spec_from_file_location('release_guard', ROOT / 'scripts/validate-release.py')
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        for name in ('projects/example/tickets/project.json',
                     'papers/example/tickets/data/issues/res-1.md',
                     'projects/example/tickets/.cache/issues-index.json',
                     'projects/example/tickets/data/transactions/pending.json'):
            self.assertNotIn(name, guard.RELEASE_ALLOWLIST)
        self.assertIn('scripts/research-tickets.py', guard.REQUIRED)
        self.assertIn('.agents/skills/research-issues/SKILL.md', guard.REQUIRED)
        self.assertTrue(all('*' not in path for path in guard.RELEASE_ALLOWLIST))


if __name__ == '__main__':
    unittest.main()
