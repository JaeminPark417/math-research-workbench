#!/usr/bin/env python3
"""Record a fictional experimental research cycle in a NEW temporary capsule.

This example launches no jobs, reads no real project, and contacts no service.
Every measurement and completed job below is a synthetic fixture, not research
evidence. Generated files are retained for inspection. Python 3.9+ suffices.

Run without arguments, or pass --output /tmp/new-synthetic-capsule. An explicit
output must be a new directory below an OS temporary root; its parent must exist.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import re
import sys
import tempfile

sys.dont_write_bytecode = True
APP = Path(__file__).resolve().parents[1]
WORKBENCH = APP.parents[1]
sys.path.insert(0, str(APP / 'scripts'))

from issue_index import IndexErrorDetail
from issue_sources import snapshot
from issue_store import IssueStore
from ticket_project import initialize


def below(path, root):
    return path != root and root in path.parents


def new_project(output):
    """Validate the destination before making any file or directory."""
    temp_root = Path(tempfile.gettempdir()).resolve()
    roots = {temp_root}
    if Path('/tmp').is_dir():
        roots.add(Path('/tmp').resolve())
    if temp_root == WORKBENCH or below(temp_root, WORKBENCH):
        raise ValueError('The configured temporary root is inside the Workbench.')
    if output is None:
        parent = Path(tempfile.mkdtemp(prefix='research-cycle-', dir=temp_root)).resolve()
        project = parent / 'synthetic-experiment'
    else:
        requested = Path(output).expanduser()
        if not requested.is_absolute():
            raise ValueError('--output must be absolute.')
        project = requested.resolve()
        if any(p == WORKBENCH or below(p, WORKBENCH) for p in (requested, project)):
            raise ValueError('The example refuses all Vault destinations.')
        if not any(below(project, root) for root in roots):
            raise ValueError('--output must be strictly below an OS temporary root.')
        if requested.exists() or requested.is_symlink() or project.exists():
            raise ValueError('--output must name a new directory; existing paths are never reused.')
        if not project.parent.is_dir():
            raise ValueError('The output parent directory must already exist.')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,119}', project.name):
        raise ValueError('The output name must use lowercase letters, digits and hyphens.')
    project.mkdir()
    return project


def create(key, kind, title, body, **fields):
    return dict(op='create', key=key, kind=kind, title=title,
                body='## Statement and scope\n\n' + body + '\n', **fields)


def relation(key, source, target, kind, logic):
    return {'op': 'relation-add', 'key': key, 'from': source, 'to': target,
            'type': kind, 'route': 'Fictional two-seed screening example',
            'logic': logic,
            'evidence': 'Synthetic protocol and endpoint source snapshots only; no real experiment was run.'}


def demonstrate(project):
    today = dt.date.today().isoformat()
    (project / 'README.md').write_text(
        '# Synthetic experimental cycle\n\n'
        'This disposable teaching fixture contains no real research measurements or jobs.\n\n'
        '## Predeclared protocol\n\n'
        'Question: does the toy intervention justify a larger evaluation? The scoped hypothesis is that its mean paired score gain on two fictional seeds reaches at least 1.0 percentage point. Compare the intervention with the same baseline and split for each seed. Freeze that screening threshold before writing the fictional observations. Two seeds cannot establish generalization or statistical significance.\n\n'
        'Proceed to a larger evaluation only after the gate passes and an explicit decision activates the conditional activity. Job completion alone is insufficient.\n',
        encoding='utf-8')
    initialize(project, 'Synthetic experimental research cycle', {
        'schema': 1, 'project_id': project.name,
        'coverage': {'state': 'complete', 'scope': 'This fictional teaching cycle only; no real project coverage is claimed.', 'untracked': []},
        'repositories': {}})
    root = project / 'tickets'
    store = IssueStore(root)
    sequence = 0

    def apply(*operations, **guards):
        nonlocal sequence
        sequence += 1
        return store.apply({'operation_id': 'synthetic-cycle-' + str(sequence),
                            'expected_generation': store.index.refresh()['generation'],
                            'operations': list(operations), **guards})

    protocol = snapshot(root, 'capsule', 'README.md', heading='Predeclared protocol')
    ids = apply(
        create('question', 'question', 'Should the toy intervention receive a larger evaluation?',
               'A fictional research question; an unanswered question is not a pending execution task.'),
        create('hypothesis', 'hypothesis', 'Mean paired gain reaches the 1.0 pp screening gate',
               'Scoped to two fictional seeds, fixed baseline and fixed split. This is a screening hypothesis, not a universal performance claim.',
               parent='@question', source_refs=[protocol]),
        create('design', 'experiment', 'Predeclared two-seed paired comparison',
               'Compare matched fictional seed pairs and apply the frozen >=1.0 pp mean-gain gate. This object records the design; the child activity records execution.',
               parent='@hypothesis', source_refs=[protocol]),
        create('execution', 'activity', 'Record the fictional execution and inspect its evidence',
               'Simulate a completed evaluation manifest. No training, inference, external job or network request is launched.',
               parent='@design', status='Ready', priority=1,
               next_action='Write the synthetic manifest and check the predeclared gate.',
               priority_rationale='The selected design needs its observation and interpretation recorded.'),
        create('conditional-expansion', 'activity', 'Larger evaluation only after a positive gate decision',
               'Conditional follow-up. Keep Backlog until the gate passes and a recorded decision explicitly activates it; a Done blocker alone must not activate it.',
               parent='@design', status='Backlog', blocked_by=['@execution'], priority=2,
               next_action='Await an explicit go/no-go decision.'),
        relation('design-tests-question', '@design', '@question', 'tests', 'The design operationalizes this narrow question.'),
        relation('design-tests-hypothesis', '@design', '@hypothesis', 'tests', 'The predeclared threshold is the scoped hypothesis test.'))['created']
    initial = store.workflow_start()
    assert [item['id'] for item in initial['items']] == [ids['execution']]
    run_id = 'synthetic-evaluation-session'
    apply({'op': 'begin', 'run_id': run_id, 'issue': ids['execution'],
           'reason': 'Demonstrate evidence recording for the selected fictional design.',
           'next_action': 'Record fictional observations without launching any real job.'},
          expected_harness_version=initial['harness_version'])

    # These literals are fixtures. No model, dataset, remote worker or RNG is used.
    observations = [
        {'fixture_seed': 1, 'status': 'completed', 'baseline_score_pct': 70.0, 'intervention_score_pct': 70.4, 'gain_pp': 0.4},
        {'fixture_seed': 2, 'status': 'completed', 'baseline_score_pct': 71.0, 'intervention_score_pct': 71.3, 'gain_pp': 0.3},
    ]
    mean_gain = round(sum(row['gain_pp'] for row in observations) / len(observations), 2)
    threshold = 1.0
    manifest = {'synthetic': True, 'real_jobs_launched': 0, 'fixture_jobs_completed': 2,
                'predeclared_gate': {'metric': 'mean_paired_gain_pp', 'minimum': threshold},
                'observations': observations, 'mean_paired_gain_pp': mean_gain,
                'gate_passed': mean_gain >= threshold}
    (project / 'logs').mkdir()
    manifest_path = 'logs/synthetic-manifest.json'
    log_path = 'logs/' + today + '-synthetic-gate.md'
    (project / manifest_path).write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    (project / log_path).write_text(
        '---\ntype: project-log\nproject: ' + project.name + '\ndate: ' + today + '\n'
        'slug: synthetic-gate\nstatus: complete\nreview_status: unchecked\n---\n\n'
        '# Fictional gate observation\n\n'
        '## Context\n\nEvery job and measurement below is invented for this example. No real experiment ran.\n\n'
        '## Setup\n\nTwo fixed fictional seed pairs, the same baseline and split, and a predeclared >=1.0 pp mean-gain gate. No external artifacts or services are involved.\n\n'
        '## Results\n\n| Fictional seed | Baseline (%) | Intervention (%) | Gain (pp) | Fixture job |\n'
        '|---|---:|---:|---:|---|\n| 1 | 70.0 | 70.4 | 0.4 | completed |\n| 2 | 71.0 | 71.3 | 0.3 | completed |\n\n'
        'Both fictional jobs completed, but mean gain is 0.35 pp, below 1.0 pp. The screening gate failed.\n\n'
        '## Interpretation\n\nNegative means failure of this predeclared screening gate. The positive raw differences do not meet its threshold. Two invented observations provide no real-world evidence, statistical significance, or universal refutation of the intervention.\n\n'
        '## Implications\n\nNo-go for expanding this branch. Cancel the conditional expansion activity. Retain the original design and failed gate. Record a revised design that would isolate the mechanism and add uncertainty estimates; leave it Backlog for a later explicit decision.\n\n'
        '## Artifacts\n\n[Complete synthetic manifest](synthetic-manifest.json).\n', encoding='utf-8')
    manifest_ref = snapshot(root, 'capsule', manifest_path)
    log_ref = snapshot(root, 'capsule', log_path, heading='Results')
    interpretation_ref = snapshot(root, 'capsule', log_path, heading='Interpretation')
    decision_ref = snapshot(root, 'capsule', log_path, heading='Implications')
    assert all('object_id' not in ref for ref in (protocol, manifest_ref, log_ref, interpretation_ref, decision_ref))
    active = store.workflow_start()['active']
    ids.update(apply(
        create('result', 'result', 'Two fictional jobs completed; the screening gate failed',
               'Synthetic mean gain is 0.35 pp versus the predeclared >=1.0 pp gate. Negative denotes failure of this specific gate, not a failed process or universal refutation.',
               parent=ids['design'], outcome='negative', source_refs=[manifest_ref, log_ref]),
        relation('design-produces-result', ids['design'], '@result', 'produces', 'The observation belongs to this frozen comparison design.'),
        relation('execution-produces-result', ids['execution'], '@result', 'produces', 'This activity recorded the fixture observations; it did not establish the hypothesis.'),
        relation('result-challenges-hypothesis', '@result', ids['hypothesis'], 'challenges', 'The specific screening threshold was not met; no broader claim is refuted.'),
        {'op': 'checkpoint', 'run_id': run_id,
         'summary': 'The fictional execution completed, while the predeclared scientific screening gate failed.',
         'next_action': 'Interpret the narrow result and record a go/no-go decision.',
         'evidence': [{'issue': '@result'}, {'source': manifest_ref}]},
        expected_run_version=active['version'])['created'])

    active = store.workflow_start()['active']
    followup = store.index.refresh()['records'][ids['conditional-expansion']]
    ids.update(apply(
        create('analysis', 'analysis', 'The failed gate limits this branch, not all possible interventions',
               'The 0.35 pp mean misses the predeclared 1.0 pp threshold. The two fictional seeds cannot establish a general effect or its absence. Preserve the negative finding and the validity limits.',
               parent=ids['result'], outcome='negative', source_refs=[manifest_ref, interpretation_ref]),
        create('decision', 'decision', 'No-go: cancel expansion and retain a revised design',
               'Do not expand the current branch. Explicitly cancel its conditional activity. Keep the earlier hypothesis, design and failed result as research history.',
               parent=ids['question'], source_refs=[decision_ref]),
        create('revised-design', 'experiment', 'Deferred mechanism ablation with uncertainty estimates',
               'Proposed follow-up design: isolate the mechanism, choose replication and uncertainty reporting before any future execution, and retain the original gate as history. It is not ready or executed.',
               parent=ids['question'], status='Backlog'),
        relation('analysis-interprets-result', '@analysis', ids['result'], 'interprets', 'Interpret the scoped negative gate and its limitations.'),
        relation('analysis-challenges-hypothesis', '@analysis', ids['hypothesis'], 'challenges', 'The scoped gate is not satisfied; universality and significance are outside scope.'),
        relation('result-informs-decision', ids['result'], '@decision', 'informs', 'The failed screening gate informs the no-go decision.'),
        relation('analysis-informs-decision', '@analysis', '@decision', 'informs', 'Validity limits favor a redesigned comparison instead of expansion.'),
        relation('decision-motivates-revision', '@decision', '@revised-design', 'motivates', 'Retain a possible future design without activating work automatically.'),
        {'op': 'update', 'id': ids['conditional-expansion'], 'expected_version': followup['source_hash'],
         'changes': {'status': 'Canceled', 'next_action': 'Do not execute: the scoped gate failed and the recorded decision is no-go.'}},
        {'op': 'end', 'run_id': run_id, 'outcome': 'completed',
         'summary': 'Evidence recording and interpretation finished; the synthetic gate failed and expansion was explicitly canceled.',
         'next_action': 'Inspect the retained failed branch and deferred revised design; choose future work explicitly.',
         'evidence': [{'issue': ids['result']}, {'issue': '@analysis'}, {'issue': '@decision'}, {'source': decision_ref}]},
        expected_run_version=active['version'])['created'])

    validation = store.index.validate()
    records = store.index.refresh()['records']
    final = store.workflow_start()
    events = store.workflow_run(run_id)['items']
    checks = store.source_check(list(ids.values()), limit=50)
    assert manifest['gate_passed'] is False and mean_gain == 0.35
    assert records[ids['execution']]['status'] == 'Done'
    assert records[ids['conditional-expansion']]['status'] == 'Canceled'
    assert all(record['status'] != 'Done' for record in records.values() if record['kind'] != 'activity')
    assert final['active'] is None and final['items'] == []
    assert [event['phase'] for event in events] == ['begin', 'checkpoint', 'end']
    assert checks['next_cursor'] is None and all(check['state'] == 'current' for check in checks['checks'])
    return {'ok': True, 'synthetic': True, 'project': str(project), 'real_jobs_launched': 0,
            'issues': store.index.list_issues(limit=50, fields=['id', 'kind', 'title', 'status', 'outcome', 'parent'])['items'],
            'validation': validation, 'source_checks': {'total': checks['total'],
                'all_current': checks['next_cursor'] is None and all(check['state'] == 'current' for check in checks['checks'])},
            'workflow': {'initial_ready': [item['id'] for item in initial['items']],
                         'final_ready': final['items'], 'active': final['active'],
                         'last_session_status': final['last_run']['status'],
                         'events': [event['phase'] for event in events]},
            'interpretation': {'fixture_jobs_completed': 2, 'mean_gain_pp': mean_gain,
                               'predeclared_minimum_pp': threshold, 'gate_passed': False,
                               'result_outcome': 'negative', 'decision': 'no-go',
                               'conditional_followup': 'Canceled', 'revised_design': 'Backlog',
                               'scope': 'Fictional teaching data only; no real evidence or universal refutation.'}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', help='New capsule path below an OS temporary root; parent must exist.')
    args = parser.parse_args()
    try:
        result = demonstrate(new_project(args.output))
    except (ValueError, OSError, IndexErrorDetail) as error:
        print(json.dumps({'ok': False, 'error': getattr(error, 'code', 'EXAMPLE_ERROR'),
                          'message': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
