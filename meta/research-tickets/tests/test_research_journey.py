"""Reopen the documented synthetic projects from a fresh process, in either distribution."""
import hashlib
import json
import re
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TICKETS = Path(__file__).resolve().parents[1]
ROOT = TICKETS.parents[1]
SCRIPTS = ROOT / 'scripts' if (ROOT / 'scripts/research-tickets.py').is_file() else ROOT / 'meta/scripts'


class ResearchJourneyTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='research-journey-')
        self.addCleanup(directory.cleanup)
        self.env = dict(os.environ, TMPDIR=directory.name, TEMP=directory.name, TMP=directory.name,
                        PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')

    def invoke(self, script, *args):
        cmd = [sys.executable, '-B', str(script), *map(str, args)]
        result = subprocess.run(cmd, env=self.env, capture_output=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_paper_then_revision_and_resume(self):
        demo = self.invoke(TICKETS / 'examples/paper-review.py')
        cli = SCRIPTS / 'research-tickets.py'
        paper, draft = demo['reading'], demo['manuscript']
        ids = paper['ids']
        trace = self.invoke(cli, '--paper', paper['note'], 'neighbors', ids['main'],
                            '--type', 'refutes', '--direction', 'incoming')['items']
        self.assertEqual([(edge['from'], edge['to']) for edge in trace], [(ids['counterexample'], ids['main'])])
        resume = self.invoke(cli, '--paper', paper['note'], 'workflow', 'resume',
                             '--failed', ids['counterexample'], '--gap', ids['gap'], '--json')
        self.assertEqual(resume['failed_route']['id'], ids['counterexample'])
        self.assertEqual([gap['id'] for gap in resume['open_gaps']], [ids['gap']])
        self.assertIsNone(resume['ticket'])
        revised = draft['ids']
        checks = self.invoke(cli, '--project', draft['project'], 'source', 'check',
                             revised['review-v1'], revised['claim-v2'])['checks']
        self.assertEqual({(row['issue'], row['state']) for row in checks},
                         {(revised['review-v1'], 'changed'), (revised['claim-v2'], 'current')})
        resume = self.invoke(cli, '--project', draft['project'], 'workflow', 'resume', '--json')
        self.assertEqual(resume['ticket']['id'], revised['recheck-v2'])
        self.assertEqual(resume['next_action'], 'Verify image compactness and attainment.')
        self.assertTrue(Path(resume['ticket']['path']).is_file())

    def test_documented_experiment_entry_point(self):
        demo = self.invoke(TICKETS / 'examples/experimental-cycle.py')
        self.assertEqual(demo['real_jobs_launched'], 0)
        self.assertEqual(demo['interpretation']['result_outcome'], 'negative')
        self.assertEqual(demo['interpretation']['conditional_followup'], 'Canceled')
        self.assertEqual(demo['workflow']['events'], ['begin', 'checkpoint', 'end'])
        self.assertTrue(demo['source_checks']['all_current'])

    def make_run(self, directory):
        repo = Path(directory)
        source = repo / 'claims.md'
        statement = 'Every bounded continuous real function on (0,1) attains a maximum.'
        source.write_text('## Claim\n' + statement + '\n', encoding='utf-8')
        run = repo / 'run.md'
        template = (ROOT / 'meta/templates/research-run.md').read_text(encoding='utf-8')
        template = template.replace('YYYY-MM-DD', '2026-01-02').replace('run_id: ""', 'run_id: Run-20260102-001')
        template = template.replace('- Success criterion:', '- Success criterion: Derive attainment in the full stated domain.')
        template = template.replace('- Refutation criterion:', '- Refutation criterion: Give one admissible counterexample.')
        template = template.replace('| Obligation-001 |  |', '| Obligation-001 | Check whether the supremum is attained. |')
        run.write_text(template, encoding='utf-8')
        return repo, source, statement, run

    def check_run(self, repo, script, *args, expected=0):
        cmd = [sys.executable, '-B', str(SCRIPTS / script), *args, '--root', str(repo), '--run', 'run.md']
        proc = subprocess.run(cmd, env=self.env, capture_output=True, encoding='utf-8')
        self.assertEqual(proc.returncode, expected, proc.stdout + proc.stderr)
        return proc.stdout

    def test_captured_run_refutes_wrong_scope_and_demands_new_review(self):
        with tempfile.TemporaryDirectory(prefix='research-run-') as directory:
            repo, source, statement, run = self.make_run(directory)

            def check(script, *args, expected=0):
                return self.check_run(repo, script, *args, expected=expected)

            self.assertIn('source binding is missing', check('math_target.py', 'check', expected=2))
            check('math_target.py', 'capture', '--source', 'claims.md', '--heading', 'Claim', '--id', 'Thm-001')
            recorded = run.read_text(encoding='utf-8')
            self.assertIn(statement, recorded)
            check('math_run_checks.py')
            run.write_text(recorded.replace(statement, statement.replace('(0,1)', '[0,1]')), encoding='utf-8')
            self.assertIn('target', check('math_run_checks.py', expected=1))
            run.write_text(recorded.replace('## Scoped synthesis',
                           '| statement-matched | v1 | claims.md | agrees | all cases | AI-only |\n\n## Scoped synthesis'), encoding='utf-8')
            self.assertIn('human statement-match', check('math_run_checks.py', expected=1))
            run.write_text(recorded, encoding='utf-8')
            source.write_text('## Claim\n' + statement.replace('(0,1)', '[0,1]') + '\n', encoding='utf-8')
            self.assertIn('current source wording changed', check('math_run_checks.py', expected=2))
            self.assertEqual(run.read_text(encoding='utf-8'), recorded)

    def test_decision_tracks_its_reviewed_target_and_evidence(self):
        with tempfile.TemporaryDirectory(prefix='research-decision-') as directory:
            repo, source, statement, run = self.make_run(directory)
            self.check_run(repo, 'math_target.py', 'capture', '--source', source.name,
                           '--heading', 'Claim', '--id', 'Thm-001')
            recorded = run.read_text(encoding='utf-8')
            marker = re.search(r'^- Target snapshot: (\S+)$', recorded, re.M)[1]
            proof = repo / 'review.md'
            proof.write_bytes(b'Scoped review of attainment on the open interval.\n')
            digest = 'sha256:' + hashlib.sha256(proof.read_bytes()).hexdigest()
            for gate in ('Statement-match', 'Closed-by-researcher'):
                with self.subTest(gate=gate):
                    confirmed = recorded.replace(f'{gate} confirmation: not confirmed', f'{gate} confirmation: confirmed')
                    for key, value in (('scope', 'The proposed attainment claim'),
                                       ('confirmed by (consented identifier or role)', 'researcher'),
                                       ('confirmation date', '2026-01-02')):
                        confirmed = confirmed.replace(f'- {gate} {key}:', f'- {gate} {key}: {value}')
                    def write_decision(version, evidence):
                        decision = f'{version} | review.md | {evidence}'
                        run.write_text(confirmed.replace(f'- {gate} decision evidence:', f'- {gate} decision evidence: {decision}'), encoding='utf-8')
                    run.write_text(confirmed, encoding='utf-8')
                    self.assertIn('decision evidence', self.check_run(repo, 'math_run_checks.py', expected=1))
                    write_decision('sha256:' + '0' * 64, digest)
                    self.assertIn('target version differs', self.check_run(repo, 'math_run_checks.py', expected=1))
                    write_decision(marker, 'sha256:' + '0' * 64)
                    self.assertIn('evidence bytes differ', self.check_run(repo, 'math_run_checks.py', expected=1))
                    write_decision(marker, digest)
                    self.assertIn('Validated the recorded run structure', self.check_run(repo, 'math_run_checks.py'))

    def test_formal_manifest_uses_declared_obligation_and_reports_malformed_record(self):
        with tempfile.TemporaryDirectory(prefix='research-manifest-') as directory:
            repo, source, statement, run = self.make_run(directory)
            self.check_run(repo, 'math_target.py', 'capture', '--source', source.name,
                           '--heading', 'Claim', '--id', 'Thm-001')
            templates = ROOT / 'meta/templates'
            note = run.read_text(encoding='utf-8') + '\n' + (templates / 'research-run-extensions.md').read_text(encoding='utf-8')
            note = note.replace('- Formalization manifest: not used', '- Formalization manifest: manifest.json')
            run.write_text(note + '\nObligation-002 is mentioned here only as an unrelated example.\n', encoding='utf-8')
            raw = (templates / 'formalization-manifest.json').read_text(encoding='utf-8')
            raw = raw.replace('YYYY-MM-DD', '2026-01-02').replace('YYYYMMDD-NNN', '20260102-001')
            raw = raw.replace('-NNN', '-001').replace('project-slug', 'fixture').replace('<64 lowercase hex>', '0' * 64)
            manifest = json.loads(raw)
            manifest['problem_contract']['version'] = 'v1'
            manifest['toolchain']['lean_version'] = '4.19.0'
            manifest['toolchain']['lake_version'] = '5.0.0'
            manifest['formal_target']['declaration'] = 'Fixture.example'
            manifest['final_record']['formal_encoding'] = 'unchecked'
            trusted = manifest['trusted_challenge']
            inventory = sorted((f['path'], f['sha256']) for f in trusted['files'])
            tree = ''.join(path + '\0' + digest + '\n' for path, digest in inventory)
            trusted['baseline_tree_sha256'] = trusted['after_tree_sha256'] = 'sha256:' + hashlib.sha256(tree.encode()).hexdigest()
            def save():
                (repo / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            save()
            self.check_run(repo, 'math_run_checks.py')
            manifest['obligation_id'] = 'Obligation-002'
            save()
            self.assertIn('not declared in the Obligations table', self.check_run(repo, 'math_run_checks.py', expected=1))
            manifest['obligation_id'] = 'Obligation-001'
            manifest['final_record'] = []
            save()
            self.assertIn('final_record must be an object', self.check_run(repo, 'math_run_checks.py', expected=1))
