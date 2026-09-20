"""Source boundaries use disposable directories and Git repositories only."""
import hashlib
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
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import issue_index as ix
import issue_sources as source


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ticket-source-tests-')
        self.base = Path(self.temp.name).resolve()
        self.capsule = self.base / 'project'
        self.root = self.capsule / 'tickets'
        self.root.mkdir(parents=True)
        self.repo = self.base / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Disposable Source Test')
        self.git('config', 'user.email', 'source-test@example.org')
        self.git('remote', 'add', 'origin', 'git@github.com:example/fixture.git')
        (self.repo / 'notes').mkdir()
        self.file = self.repo / 'notes/proof.md'
        self.file.write_text('# Proof\n\n## Claim A\n\nA temporary statement.\n', encoding='utf-8')
        self.commit = self.commit_all()
        (self.capsule / 'README.md').write_text('# Project\n\n## Next\n\nTemporary task.\n', encoding='utf-8')
        self.config = {'schema': 1, 'project_id': 'fixture',
                       'coverage': {'state': 'partial', 'scope': 'Tests', 'untracked': []},
                       'repositories': {'research': {'path': str(self.repo),
                                                     'origin': 'https://github.com/example/fixture.git'}}}
        self.write_config()

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        result = subprocess.run(['git', '-C', str(self.repo), *args], capture_output=True,
                                text=True, check=True, env={**os.environ, 'GIT_CONFIG_GLOBAL': os.devnull,
                                                         'GIT_CONFIG_NOSYSTEM': '1'}, encoding='utf-8')
        return result.stdout.strip()

    def commit_all(self):
        self.git('add', '--all')
        self.git('commit', '-qm', 'Disposable fixture')
        return self.git('rev-parse', 'HEAD')

    def write_config(self):
        (self.root / 'project.json').write_text(json.dumps(self.config), encoding='utf-8')

    def ref(self, **kwargs):
        return source.snapshot(self.root, 'research', 'notes/proof.md', commit=self.commit, **kwargs)

    def error(self, code, function, *args, **kwargs):
        with self.assertRaises(ix.IndexErrorDetail) as caught:
            function(*args, **kwargs)
        self.assertEqual(code, caught.exception.code, str(caught.exception))
        return caught.exception

    def test_committed_reference_exact_hash_and_no_content_leak(self):
        ref = self.ref(heading='Claim A')
        self.assertEqual(hashlib.sha256(self.file.read_bytes()).hexdigest(), ref['sha256'])
        self.assertEqual(self.commit, ref['commit'])
        self.assertEqual(ref, source.verify_reference(self.root, ref))
        self.assertEqual({'repository', 'mode', 'commit', 'path', 'sha256', 'heading'}, set(ref))
        ref['object_id'] = 'Obl-001'
        self.assertEqual(ref, source.verify_reference(self.root, ref))

    def test_capsule_working_snapshot(self):
        ref = source.snapshot(self.root, 'capsule', 'README.md', heading='Next')
        self.assertEqual('working', ref['mode'])
        self.assertNotIn('commit', ref)
        self.assertEqual(ref, source.verify_reference(self.root, ref))
        self.assertEqual('current', source.check_drift(self.root, ref)['state'])
        (self.capsule / 'README.md').write_text('# Project\nChanged.\n', encoding='utf-8')
        self.assertEqual('changed', source.check_drift(self.root, ref)['state'])
        self.error('SOURCE_MISMATCH', source.verify_reference, self.root, ref)

    def test_external_working_snapshot_does_not_claim_commit(self):
        ref = source.snapshot(self.root, 'research', 'notes/proof.md')
        self.assertEqual('working', ref['mode'])
        self.assertNotIn('commit', ref)
        self.assertEqual(ref, source.verify_reference(self.root, ref))

    def test_historical_commit_remains_verifiable_after_head_advances(self):
        ref = self.ref()
        self.file.write_text('# Replacement\n', encoding='utf-8')
        advanced = self.commit_all()
        self.assertNotEqual(self.commit, advanced)
        self.assertEqual(ref, source.verify_reference(self.root, ref))
        self.assertEqual('changed', source.check_drift(self.root, ref)['state'])
        self.assertEqual('verified', source.check_drift(self.root, ref)['reference_state'])

    def test_committed_evidence_stays_verified_when_working_file_is_removed(self):
        ref = self.ref()
        self.file.unlink()
        result = source.check_drift(self.root, ref)
        self.assertEqual('unavailable', result['state'])
        self.assertEqual('verified', result['reference_state'])
        self.assertEqual('SOURCE_UNAVAILABLE', result['reason'])

    def test_bad_commit_reference_never_claims_verified_evidence(self):
        ref = {**self.ref(), 'sha256': 'f' * 64}
        result = source.check_drift(self.root, ref)
        self.assertEqual('unavailable', result['reference_state'])
        self.assertEqual('SOURCE_MISMATCH', result['reason'])

    def test_wrong_hash_or_wrong_path_fails(self):
        ref = self.ref()
        self.error('SOURCE_MISMATCH', source.verify_reference, self.root, {**ref, 'sha256': 'f' * 64})
        self.error('SOURCE_UNAVAILABLE', source.verify_reference, self.root, {**ref, 'path': 'notes/missing.md'})

    def test_malformed_reference_fields(self):
        good = self.ref()
        bad = [None, [], {}, {**good, 'extra': True}, {**good, 'mode': 'published'},
               {**good, 'sha256': 'f' * 63}, {**good, 'sha256': 'F' * 64},
               {**good, 'commit': self.commit[:8]}, {**good, 'commit': '-HEAD'},
               {**good, 'repository': '../repo'}, {**good, 'repository': []},
               {**good, 'heading': ''}, {**good, 'object_id': '\x00'},
               {**good, 'mode': 'working'}, {**good, 'path': 'notes/\ud800.md'}]
        for ref in bad:
            with self.subTest(ref=ref):
                self.error('INVALID_ARGUMENT', source.validate_reference, ref)

    def test_validate_is_shape_only(self):
        ref = {'repository': 'not_registered', 'mode': 'working', 'path': 'README.md', 'sha256': '0' * 64}
        with patch.object(source, '_config', side_effect=AssertionError('Must not read config')):
            self.assertEqual(ref, source.validate_reference(ref))

    def test_path_traversal_and_absolute_paths_rejected(self):
        ref = self.ref()
        for path in ('/tmp/note.md', '../note.md', 'notes/../proof.md', './proof.md',
                     'notes//proof.md', 'notes\\proof.md', 'notes/proof.md/', 'notes/\nproof.md'):
            with self.subTest(path=path):
                self.error('INVALID_ARGUMENT', source.validate_reference, {**ref, 'path': path})

    def test_credentials_hidden_git_and_binary_suffixes_rejected(self):
        ref = self.ref()
        for path in ('.env', '.env.md', '.git/config.md', '.ssh/key.md', 'notes/credentials.json',
                     'notes/secrets.yaml', 'notes/token.txt', 'notes/passwords.md',
                     'auth.json', 'notes/id_rsa', 'paper.pdf', 'image.png'):
            with self.subTest(path=path):
                self.error('SOURCE_POLICY', source.validate_reference, {**ref, 'path': path})

    def test_capsule_cannot_reference_tickets_or_claim_commit(self):
        for path in ('tickets/project.json', 'tickets/data/issues/res-1.md'):
            self.error('SOURCE_POLICY', source.snapshot, self.root, 'capsule', path)
        self.error('INVALID_ARGUMENT', source.snapshot, self.root, 'capsule', 'README.md', commit=self.commit)

    def test_unregistered_repository_is_not_opened(self):
        with patch.object(source, '_git', side_effect=AssertionError('No Git lookup')):
            self.error('SOURCE_POLICY', source.snapshot, self.root, 'unregistered', 'README.md')

    def test_mismatched_origin_is_rejected_without_echoing_origin(self):
        self.git('remote', 'set-url', 'origin', 'https://github.com/elsewhere/wrong.git')
        error = self.error('SOURCE_POLICY', self.ref)
        self.assertNotIn('elsewhere', str(error))

    def test_credential_bearing_origin_rejected(self):
        for origin in ('https://secret@example.org/repo/name.git',
                       'https://' + 'fixture-user' + ':' + 'not-a-real-credential' + '@github.com/example/fixture.git',
                       'http://github.com/example/fixture.git', '/local/repo'):
            with self.subTest(origin=origin):
                self.config['repositories']['research']['origin'] = origin
                self.write_config()
                error = self.error('SOURCE_POLICY', self.ref)
                self.assertNotIn(origin, str(error))

    def test_github_https_and_ssh_origin_equivalence(self):
        self.config['repositories']['research']['origin'] = 'ssh://git@github.com/example/fixture.git'
        self.write_config()
        self.assertEqual(self.commit, self.ref()['commit'])

    def test_nested_registered_path_cannot_masquerade_as_repo_root(self):
        self.config['repositories']['research']['path'] = str(self.repo / 'notes')
        self.write_config()
        self.error('SOURCE_POLICY', self.ref)

    def test_registered_symlink_root_rejected(self):
        linked = self.base / 'alias'
        symlink_or_skip(self, linked, self.repo, target_is_directory=True)
        self.config['repositories']['research']['path'] = str(linked)
        self.write_config()
        self.error('SOURCE_POLICY', self.ref)

    def test_registered_symlink_ancestor_rejected(self):
        linked = self.base / 'parent-alias'
        symlink_or_skip(self, linked, self.base, target_is_directory=True)
        self.config['repositories']['research']['path'] = str(linked / 'repo')
        self.write_config()
        self.error('SOURCE_POLICY', self.ref)

    def test_working_symlink_file_and_directory_are_rejected(self):
        symlink_or_skip(self, self.repo / 'linked.md', self.file)
        symlink_or_skip(self, self.repo / 'linked-notes', self.repo / 'notes', target_is_directory=True)
        for path in ('linked.md', 'linked-notes/proof.md'):
            self.error('SOURCE_UNAVAILABLE', source.snapshot, self.root, 'research', path)

    def test_committed_symlink_and_submodule_rejected(self):
        symlink_or_skip(self, self.repo / 'linked.md', 'notes/proof.md')
        self.git('update-index', '--add', '--cacheinfo', '160000,' + self.commit + ',submodule.md')
        self.git('add', 'linked.md')
        self.git('commit', '-qm', 'Unsafe source modes')
        commit = self.git('rev-parse', 'HEAD')
        for path in ('linked.md', 'submodule.md'):
            self.error('SOURCE_POLICY', source.snapshot, self.root, 'research', path, commit=commit)

    def test_missing_and_noncommit_git_object_rejected(self):
        self.error('SOURCE_UNAVAILABLE', source.snapshot, self.root, 'research', 'notes/proof.md', commit='1' * 40)
        blob = self.git('rev-parse', self.commit + ':notes/proof.md')
        self.error('SOURCE_POLICY', source.snapshot, self.root, 'research', 'notes/proof.md', commit=blob)

    def test_working_and_committed_size_limits_before_blob_read(self):
        with patch.object(source, 'MAX_SOURCE_BYTES', 10):
            original = source._git
            seen = []
            def tracked(*args, **kwargs):
                seen.append(args)
                return original(*args, **kwargs)
            with patch.object(source, '_git', side_effect=tracked):
                self.error('SOURCE_TOO_LARGE', self.ref)
            self.assertFalse(any('blob' in args for args in seen))
        with patch.object(source, '_read_file', wraps=source._read_file) as read:
            source.snapshot(self.root, 'research', 'notes/proof.md')
            self.assertTrue(read.called)
        self.file.write_bytes(b'x' * (source.MAX_SOURCE_BYTES + 1))
        self.error('SOURCE_TOO_LARGE', source.snapshot, self.root, 'research', 'notes/proof.md')

    def test_non_utf8_and_nul_sources_rejected(self):
        for raw in (b'bad\xfftext', b'bad\x00text'):
            self.file.write_bytes(raw)
            self.error('SOURCE_POLICY', source.snapshot, self.root, 'research', 'notes/proof.md')
            commit = self.commit_all()
            self.error('SOURCE_POLICY', source.snapshot, self.root, 'research', 'notes/proof.md', commit=commit)

    def test_heading_must_exist_and_not_be_inside_code_fence(self):
        self.error('SOURCE_MISMATCH', self.ref, heading='Missing')
        self.file.write_text('# Proof\n\n```md\n## Fake\n```\n\nReal\n----\n', encoding='utf-8')
        self.error('SOURCE_MISMATCH', source.snapshot, self.root, 'research', 'notes/proof.md', heading='Fake')
        ref = source.snapshot(self.root, 'research', 'notes/proof.md', heading='Real')
        self.assertEqual(ref, source.verify_reference(self.root, ref))

    def test_heading_for_non_markdown_is_explicitly_rejected(self):
        (self.repo / 'proof.tex').write_text('A source', encoding='utf-8')
        self.error('INVALID_ARGUMENT', source.snapshot, self.root, 'research', 'proof.tex', heading='Claim A')

    def test_duplicate_headings_are_ambiguous_including_setext(self):
        for text in ('## Claim A\n\nOne.\n\n## Claim A\n\nTwo.\n',
                     '## Claim A\n\nOne.\n\nClaim A\n-------\n'):
            with self.subTest(text=text):
                self.file.write_text(text, encoding='utf-8')
                self.error('SOURCE_MISMATCH', source.snapshot, self.root, 'research', 'notes/proof.md', heading='Claim A')
                commit = self.commit_all()
                self.error('SOURCE_MISMATCH', source.snapshot, self.root, 'research', 'notes/proof.md', commit=commit, heading='Claim A')

    def test_heading_inside_display_math_is_not_an_anchor_or_duplicate(self):
        for start, end in (('$$', '$$'), ('\\[', '\\]')):
            with self.subTest(delimiter=start):
                self.file.write_text(f'# Proof\n\n{start}\n## Fake\n{end}\n', encoding='utf-8')
                self.error('SOURCE_MISMATCH', source.snapshot, self.root, 'research', 'notes/proof.md', heading='Fake')
                self.file.write_text(f'## Claim A\n\n{start}\n## Claim A\n{end}\n', encoding='utf-8')
                ref = source.snapshot(self.root, 'research', 'notes/proof.md', heading='Claim A')
                self.assertEqual(ref, source.verify_reference(self.root, ref))

    def test_git_ambient_repository_injection_does_not_redirect(self):
        with patch.dict(os.environ, {'GIT_DIR': '/nonexistent/injected.git', 'GIT_WORK_TREE': '/nonexistent'}):
            self.assertEqual(self.commit, self.ref()['commit'])

    def test_git_replace_does_not_change_addressed_commit(self):
        original = self.ref()
        self.file.write_text('# Altered source\n', encoding='utf-8')
        newer = self.commit_all()
        self.git('replace', self.commit, newer)
        self.assertEqual(original, source.verify_reference(self.root, original))

    def test_drift_unavailable_does_not_expose_errors_or_content(self):
        ref = source.snapshot(self.root, 'capsule', 'README.md')
        (self.capsule / 'README.md').unlink()
        result = source.check_drift(self.root, ref)
        self.assertEqual({'state': 'unavailable', 'reason': 'SOURCE_UNAVAILABLE'}, result)

    def test_symlink_config_and_invalid_registration_rejected(self):
        config_file = self.root / 'project.json'
        config_file.unlink()
        target = self.base / 'external-config.json'
        target.write_text(json.dumps(self.config), encoding='utf-8')
        symlink_or_skip(self, config_file, target)
        self.error('SOURCE_UNAVAILABLE', self.ref)
        config_file.unlink()
        for path in ('relative/repo', 'bad\x00root', None):
            self.config['repositories']['research']['path'] = path
            self.write_config()
            self.error('SOURCE_POLICY', self.ref)


if __name__ == '__main__':
    unittest.main()
