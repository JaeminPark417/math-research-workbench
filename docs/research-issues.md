# Keep research organized with local issues

[한국어 안내](research-issues.ko.md)

An issue is a small research record: a claim, needed lemma, missing proof step, counterexample, review or action. Together they retain why a route was chosen, what failed, which evidence applies, and what to do next. They live beside your research in ordinary files. No external tracker, account or new interface is required.

## Start with one project

Tell Codex:

```text
Apply issue-based management to this project. Read its current state first,
reuse existing claim IDs, preserve failed approaches and counterexamples,
and tell me what remains outside the initial issue map.
```

Codex enrolls just this scope and maintains it during your requested work, without asking permission for each routine local update. It does not import every project or start research while you are absent. Later you can say:

```text
Continue this project. Check the current activity, its evidence and the
unindexed next steps, then work on the next step toward our goal.
```

Or request only the current state; that does not start an activity. A blank issue queue does not mean the whole project is finished: earlier notes or other routes may be outside the selected scope.

## Keep one current action list

Within the enrolled scope, tickets hold the current actions, priorities and activity status. The project Spine keeps canonical mathematics, strategic direction and work not yet indexed, with links to relevant tickets. Session notes and research logs preserve what happened and point back to the current action; they do not repeat a live checklist. When no ticket covers an active mathematical run, that run holds its bounded immediate step and the Spine links to it.

A quick explanation, small note edit, priority correction or status question does not need a new activity or operational session. Codex uses only the relevant queries and guides. When you actually ask it to carry out an activity, it starts or reuses the corresponding session and preserves the result.

## Use it while reading or writing

```text
As we read this paper, map the main theorem and the lemmas it uses.
Record exact assumptions, unchecked proof steps and scoped counterexamples.
```

```text
While we build and revise this manuscript, keep its main claims, shared
lemmas, missing arguments and next writing actions connected in the project.
Preserve the earlier review when the statement changes.
```

Paper reading uses a store beside the existing paper note; your manuscript stays in its existing project. A shared lemma is recorded once. Citations and source statements still require inspection; the issue map itself does not verify them.

## What completion means

Only an activity can be Done. That means the work was performed, including an audit that found a gap or an experiment with a negative result. It does not prove the theorem. The project Research State Spine, detailed research-run log and your explicit mathematical judgment remain the authority for claims and gaps.

For research activities, Codex keeps a short operational session for the current activity. A separate readable session summary is useful after substantive work or a decision, not every ticket edit. Several such sessions can reference one longer mathematical run. Counterexamples and failed routes remain available; priorities include a reason and can change with the evidence.

## Files, safety and recovery

Project records live under `projects/<slug>/tickets/`. Paper records live beside the paper note in `<slug>/tickets/`. The Markdown files remain readable without Codex. Use Codex and the guarded writer for edits so relationships and evidence stay consistent; do not edit the derived index manually.

These files contain unpublished research. Follow the usual consent and exactly-private destination check before backup or sharing. Never push your populated stores to the public Workbench distribution. Local caches, locks and recovery journals are not included in Git backup; canonical tickets, session events and operation receipts are.

On another machine, capsule/paper references work inside the copied workspace. Registered external clones need their paths and expected origins checked explicitly. Keep the workspace outside cloud-sync folders. On interrupted writes, ask Codex to inspect recovery status and preserve unknown edits. Never delete locks or pending journals to force a write through. Recovery is not a guarantee against disk failure or power loss.

You do not need terminal commands or JSON. The [agent workflow](../meta/research-ticket-workflow.md), [write contract](../meta/research-tickets/WRITE-API.md) and [tests](../meta/research-tickets/TESTING.md) document the details for maintainers. Python 3.9 or newer is the only runtime dependency.
