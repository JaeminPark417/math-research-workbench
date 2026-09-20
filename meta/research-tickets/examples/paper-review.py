#!/usr/bin/env python3
"""Synthetic paper reading and manuscript revision; temporary files only.

All paper statements and review records are teaching fixtures, not publications
or real review evidence. No service, PDF, real project or Git remote is used.
The generated directory is retained for inspection. Python 3.9+ standard library.
"""
import json
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
APP = Path(__file__).resolve().parents[1]
WORKBENCH = APP.parents[1]
sys.path.insert(0, str(APP / 'scripts'))
from issue_sources import snapshot
from issue_store import IssueStore
from ticket_project import initialize, initialize_paper


def create(key, kind, title, body, **fields):
    return dict(op='create', key=key, kind=kind, title=title,
                body='## Statement and scope\n\n' + body + '\n', **fields)


def relation(key, source, target, kind, logic):
    return dict(op='relation-add', key=key, **{'from': source, 'to': target},
                type=kind, route='Synthetic attainment proof', logic=logic,
                evidence='Inspect the exact synthetic statements and endpoint snapshots; no real paper was reviewed.')


class Demo:
    def __init__(self, root):
        self.store, self.sequence = IssueStore(root), 0

    def apply(self, *operations, **guards):
        self.sequence += 1
        return self.store.apply(dict(operation_id='paper-demo-' + str(self.sequence),
                                    expected_generation=self.store.index.refresh()['generation'],
                                    operations=list(operations), **guards))

    def begin(self, identifier, name):
        start = self.store.workflow_start()
        self.apply(dict(op='begin', run_id=name, issue=identifier,
                        reason='Demonstrate a scoped synthetic proof audit.',
                        next_action='Record the missing assumption and its counterexample.'),
                   expected_harness_version=start['harness_version'])

    def end(self, name, evidence):
        active = self.store.workflow_start()['active']
        self.apply(dict(op='end', run_id=name, outcome='completed',
                        summary='Audit performed; the recorded statement has a scoped counterexample.',
                        next_action='Review a corrected formulation separately; no truth promotion.',
                        evidence=[dict(issue=evidence)]), expected_run_version=active['version'])


def reading(base):
    library = base / 'papers'
    (library / 'content').mkdir(parents=True)
    note = library / '2026-synthetic-attainment.md'
    note.write_text('---\ntype: paper\nstatus: reading\nyear: 2026\n---\n'
                    '# Synthetic paper: NOT a real publication\n\n'
                    '## Main theorem\nEvery bounded continuous f:(0,1)→R attains a maximum.\n\n'
                    '## Lemma 1\nEvery nonempty bounded subset of R contains its supremum.\n', encoding='utf-8')
    before = note.read_bytes()
    extract = library / 'content/synthetic-attainment.md'
    extract.write_text('# Synthetic proof extract\n\n## Proof\n'
                       'Apply Lemma 1 to the image of f.\n\n## Proof\n'
                       'The claimed lemma incorrectly treats a supremum as a member.\n', encoding='utf-8')
    initialize_paper(note, 'Synthetic reading fixture', dict(
        schema=1, project_id=note.stem, repositories={},
        coverage=dict(state='complete', scope='Only the two-statement synthetic fixture.', untracked=[]),
        subject=dict(kind='paper', note=note.name, extracts=['content/' + extract.name])))
    root = note.with_suffix('') / 'tickets'
    demo = Demo(root)
    tags = ['paper:synthetic-attainment', 'mode:reading', 'version:fixture-v1']
    main = dict(snapshot(root, 'paper', note.name, heading='Main theorem'), object_id='Thm-1')
    lemma = dict(snapshot(root, 'paper', note.name, heading='Lemma 1'), object_id='Lem-1')
    # Duplicate Proof headings: use file hash plus an exact locator in the body.
    proof = snapshot(root, 'paper', 'content/' + extract.name)
    ids = demo.apply(
        create('main', 'theorem', 'Reported Thm 1: maximum on an open interval',
               'Reported synthetic claim, not verified. Bounded continuous f on (0,1) attains its supremum. Source: fixture v1, Main theorem.',
               claim_ref=main, tags=tags),
        create('lemma', 'lemma', 'Reported Lemma 1: bounded sets contain their supremum',
               'Reported synthetic input. Every nonempty bounded subset of R contains its supremum. Source: fixture v1, Lemma 1.',
               parent='@main', claim_ref=lemma, tags=tags),
        create('audit', 'activity', 'Audit the attainment step',
               'Check membership of the supremum, not only its existence. The first Proof block applies Lemma 1; the second contains the invalid inference.',
               parent='@lemma', tags=tags, source_refs=[proof], status='Ready', priority=1,
               priority_rationale='This input carries the main theorem.', next_action='Test the image (0,1).'),
        relation('lemma-main', '@lemma', '@main', 'requires-input-to',
                 'This reported proof uses Lemma 1 on the image. The input is false without an attainment assumption.'))['created']
    demo.begin(ids['audit'], 'reading-audit')
    ids.update(demo.apply(
        create('counterexample', 'counterexample', 'f(x)=x has supremum 1 but no maximum on (0,1)',
               'For every x in (0,1), (x+1)/2 is in (0,1) and has larger f-value. The bounded image (0,1) does not contain 1. This does not refute compact-domain attainment.',
               parent=ids['main'], tags=tags, source_refs=[main, lemma]),
        create('gap', 'obligation', 'Distinguish existence of a supremum from attainment',
               'The source proof requires membership of the supremum. Boundedness alone gives no such membership. Check a compactness-based replacement.',
               parent=ids['lemma'], tags=tags + ['review:assumption']),
        create('review-v1', 'analysis', 'Scoped audit: missing attainment hypothesis',
               'Reviewer: synthetic fixture. Method: direct counterexample above. Scope: two stated claims and the two Proof blocks; no other assertions or citations reviewed. Finding: missing closedness/compactness conditions. Not independent or human promotion.',
               parent=ids['main'], tags=tags + ['review:gap'], source_refs=[main, lemma, proof]),
        relation('counter-lemma', '@counterexample', ids['lemma'], 'refutes',
                 'The exact reported universal statement fails for the bounded set (0,1).'),
        relation('counter-main', '@counterexample', ids['main'], 'refutes',
                 'The exact open-interval main statement fails for f(x)=x.'),
        relation('review-main', '@review-v1', ids['main'], 'reviews',
                 'Only fixture v1 and the attainment inference were inspected.'))['created'])
    demo.end('reading-audit', ids['review-v1'])
    records = demo.store.index.refresh()['records']
    assert records[ids['audit']]['status'] == 'Done'
    assert records[ids['main']]['status'] != 'Done'
    assert note.read_bytes() == before
    assert all(c['state'] == 'current' for c in demo.store.source_check(list(ids.values()))['checks'])
    return dict(note=str(note), root=str(root), ids=ids, issues=len(records))


def manuscript(base):
    project = base / 'synthetic-manuscript'
    project.mkdir()
    (project / 'README.md').write_text('# Synthetic existing research project\n', encoding='utf-8')
    draft = project / 'draft.md'
    draft.write_text('# Synthetic manuscript v1\n\n## Main theorem\n'
                     'Every bounded continuous f:(0,1)→R attains a maximum.\n', encoding='utf-8')
    initialize(project)
    root = project / 'tickets'
    demo = Demo(root)
    tags = ['paper:synthetic-draft', 'mode:manuscript-review']
    v1 = dict(snapshot(root, 'capsule', 'draft.md', heading='Main theorem'), object_id='Thm-main')
    ids = demo.apply(
        create('existing-claim', 'theorem', 'Existing project claim: open-interval attainment',
               'Synthetic v1 claim already tracked in the project. Reuse this ID for its audit.', claim_ref=v1, tags=tags),
        create('review-v1', 'analysis', 'v1 audit: f(x)=x refutes the claim',
               'Synthetic review by this fixture, direct inspection. Only the open-interval assertion was inspected. The counterexample requires a new formulation.',
               tags=tags + ['version:v1', 'review:gap'], source_refs=[v1]),
        relation('v1-review', '@review-v1', '@existing-claim', 'reviews', 'The reviewed exact version is v1.'))['created']
    old = demo.store.index.refresh()['records'][ids['review-v1']]
    old_bytes = (root / old['path']).read_bytes()
    claim = demo.store.index.refresh()['records'][ids['existing-claim']]
    demo.apply(dict(op='propose', id=claim['id'], expected_version=claim['source_hash'],
                    statement='Replace (0,1) by [0,1]; every continuous real-valued function on this compact domain attains a maximum.',
                    reason='The v1 counterexample exploits the absent endpoint. This proposal does not certify a proof.'))
    # A changed formulation gets a new claim record, retaining the v1 audit.
    draft.write_text('# Synthetic manuscript v2\n\n## Main theorem\n'
                     'Every continuous f:[0,1]→R attains a maximum.\n'
                     'Proof requires compactness of the image and attainment on that compact image.\n', encoding='utf-8')
    assert demo.store.source_check([ids['existing-claim']])['checks'][0]['state'] == 'changed'
    v2 = dict(snapshot(root, 'capsule', 'draft.md', heading='Main theorem'), object_id='Thm-main')
    ids.update(demo.apply(
        create('claim-v2', 'theorem', 'Revised v2 claim: compact-domain attainment',
               'Synthetic v2 replacement statement on [0,1]. Its proof is not reviewed by this workflow example.',
               claim_ref=v2, tags=tags + ['version:v2']),
        create('recheck-v2', 'activity', 'Recheck the compactness argument in v2',
               'Inspect the changed domain and each proof input. The v1 review is not evidence that v2 was checked.',
               parent='@claim-v2', source_refs=[v2], tags=tags + ['version:v2', 'review:needs-recheck'],
               status='Backlog', priority=2, next_action='Verify image compactness and attainment.'),
        relation('revision-link', ids['existing-claim'], '@claim-v2', 'related',
                 'v2 replaces the false v1 statement. This records revision provenance, not implication or verification.'))['created'])
    assert (root / old['path']).read_bytes() == old_bytes
    assert demo.store.index.refresh()['records'][ids['review-v1']]['source_refs'] == [v1]
    assert not demo.store.workflow_start(tag=tags)['items']
    queried = demo.store.index.list_issues(tag=tags)
    assert queried['total'] == 4
    return dict(project=str(project), root=str(root), ids=ids, issues=queried['total'])


if __name__ == '__main__':
    temp_root = Path(tempfile.gettempdir()).resolve()
    if temp_root == WORKBENCH or WORKBENCH in temp_root.parents:
        raise ValueError('The configured temporary root must be outside the Workbench.')
    destination = Path(tempfile.mkdtemp(prefix='paper-workflow-', dir=temp_root)).resolve()
    print(json.dumps(dict(synthetic=True, directory=str(destination),
                          reading=reading(destination), manuscript=manuscript(destination),
                          real_papers_modified=0, real_reviews_performed=0), ensure_ascii=False, indent=2))
