# Local issue-based research management

Research issues preserve questions, claims, proof dependencies, failed approaches, counterexamples, evidence and the next action. They are local Markdown and JSON files, with no external tracker, account or background research service. You can keep speaking naturally; Codex maintains the records during requested work through the [research-issues skill](../.agents/skills/research-issues/SKILL.md).

## Load the part needed now

A status question needs bounded queries and the relevant source, not enrollment or a full workflow. On entering or resuming an enrolled project, read its registration/coverage and the sections below that match the action. Reuse that context during the same task; reload when scope, source versions or state change.

| Current action | Read or do |
| --- | --- |
| Orient, search, or answer a status question | Enrollment/authority, current-action ownership, and bounded query guidance; no write contract or session start |
| Perform a requested research activity | Restore the active/last operational session and relevant sources; begin or reuse one activity session |
| Enroll or change ticket records | Relevant sections of [WRITE-API.md](research-tickets/WRITE-API.md) before the first mutation |
| Map a paper argument or maintain manuscript issues | Relevant sections of [PAPER-WORKFLOW.md](research-tickets/PAPER-WORKFLOW.md) |
| Manage a computational or experimental study | Relevant sections of [EXPERIMENTAL-WORKFLOW.md](research-tickets/EXPERIMENTAL-WORKFLOW.md) |
| Recover an interrupted write | Recovery guidance and the inspected journal; never run recovery as routine setup |

Ordinary explanations, small calculations, note edits and reading summaries do not need new activities or operational sessions merely because a store exists. If such work changes a relevant source or record, update the affected references through the guarded writer. Load math-run or adapter instructions only when their own task conditions apply.

## Enrollment and authority

Enroll a project or selected paper only when the user requests issue-based management for that scope. New and existing projects remain unenrolled until that request; status questions never initialize a store. Inventory the project README, existing stable IDs, active research run, remaining actions and meaningful failed routes. Start with partial coverage and state what is not yet indexed. Do not copy another project's tickets or migrate all projects automatically.

The project Research State Spine remains the canonical mathematical map under [math-workflow.md](math-workflow.md). Long research runs retain their Problem Contract, obligations, attempts and evidence. Ticket `RES-N` IDs identify records inside one store; they do not replace `Def-NNN`, `Lem-NNN`, `Prop-NNN`, `Thm-NNN`, `Cor-NNN` or `Gap-NNN`. Bind existing objects using `claim_ref.object_id` and exact source bytes. A new AI-authored mathematical formulation remains proposed. Bound statements cannot be overwritten; use append-only `propose` or a separately identified revision. Neither activity Done, paper read status, a source hash, nor AI agreement performs HUMAN PROMOTION.

## One home for each current action

- Within enrolled coverage, tickets are authoritative for current operational actions, priority and activity status. Use their existing IDs and link to them from the project README.
- The Research State Spine remains authoritative for canonical mathematics, strategic direction and work outside ticket coverage. Keep unindexed actions visible there; an empty ticket queue is not project completion.
- Session notes and research logs preserve dated outcomes, evidence, decisions and the resume point at that time. Link to the current ticket or Spine action instead of maintaining another live checklist. Persistent mathematical runs retain their own exact target and attempt/evidence history. Without a covered ticket, an active run owns its bounded immediate next step; the Spine links to that run. Without an active run, keep the small unindexed action list in the Spine.

A request to continue the enrolled work authorizes its ordinary local record maintenance. Do not ask again for each ticket update, descriptive slug or record link. New enrollment scope, mathematical promotion, public/private destination changes and external transmission retain their own boundaries. Local maintenance never authorizes background research or an outbound request.

## Store layout

```text
scripts/research-tickets.py              CLI, run from the workspace root
meta/research-tickets/scripts/           Python 3.9+ standard-library engine
projects/<slug>/tickets/
  project.json                          explicit registration and coverage
  data/project.json                     display metadata
  data/issues/res-<n>.md                 canonical tickets
  data/relations.json                   scoped versioned relationships
  data/harness.json                     active/last operational session pointers
  data/runs/<session-id>.json            durable events and evidence
  data/operations/<operation-id>.json    idempotency receipts
  .cache/issues-index.json              disposable lookup index
```

Runs, receipts and harness files appear when needed. Canonical files belong in the user's private research backup. Cache, pending journals, local full-text history, locks and enrollment staging are local recovery state, excluded from Git; never delete a live lock or pending journal to bypass an error. Preserve the data before repairing it. Missing canonical records require restoration, not invented replacements.

For standalone reading, use the existing `papers/<slug>.md` and its sibling `papers/<slug>/tickets/`. Nested paper directories are supported. Workbench books use its existing `type: paper` schema; the engine also accepts legacy `type: book`, but this does not add that type to the Workbench note schema. Own manuscripts use the existing project store. Read the relevant [PAPER-WORKFLOW.md](research-tickets/PAPER-WORKFLOW.md) sections when mapping proof dependencies or maintaining manuscript issues; a short paper summary alone does not require the full contract.

## Start, work, checkpoint, end

1. On project entry or a real resume, read the README and only enough recent evidence to recover the requested work. If no registration exists, keep the existing note workflow. For enrolled work, use `workflow start --limit 5` to inspect active/last sessions, coverage and unindexed Spine actions. This query does not begin research. Do not repeat onboarding or re-read every guide at each reply.
2. When carrying out a requested activity, choose a relevant Ready/Todo activity, record why, and begin or reuse its short operational session. Do not silently bypass an already active session. Priority 1 is urgent, 2 high, 3 normal, 4 low, and 0 unassigned (sorted last). Reconsider priorities when evidence or direction changes. Operational `blocked_by` links reference only activities and must be Done before beginning.
3. Record meaningful mathematical objects, reviews, scoped relations and failed routes when they affect the argument or next decision. Keep minor calculations in the relevant log; do not create an issue for every thought. Preserve a counterexample's exact refutation scope and keep shared lemmas as one object with several dependents.
4. Checkpoint when there is a useful result, a change of direction, a pause or an interruption risk. Record the evidence and update the current action in its authoritative ticket/Spine record. If a sustained math run exists, use `math_run` with exact source and stable run-local IDs. Several short ticket sessions can reference one persistent run; ending a ticket session does not end or prove it.
5. Finish an open operational session as completed/paused/blocked with the relevant evidence. These set the activity to Done/Ready/Backlog; a gap or negative result can be a completed activity. Write a separate session note only when substantive work or a decision needs a readable historical summary. Link existing ticket/run evidence rather than copying it. Preserve the human-promotion boundary. Infrastructure maintenance, status checks and tests never begin real research sessions.

The same engine can record `question → hypothesis → experiment → result → analysis → decision`. An experiment is a design, not an executable activity; negative/null/invalid results are retained. Conditional follow-ups stay Backlog until an explicit recorded decision activates them. This is an agent rule, not an enforced approval gate. See [EXPERIMENTAL-WORKFLOW.md](research-tickets/EXPERIMENTAL-WORKFLOW.md); no training stack, server or job runner is bundled.

## Bounded queries

```text
python3 scripts/research-tickets.py --project projects/SLUG workflow start --limit 5
python3 scripts/research-tickets.py --project projects/SLUG list --kind activity --status Ready --limit 5
python3 scripts/research-tickets.py --project projects/SLUG search "terms" --fields id,title,status --limit 5
python3 scripts/research-tickets.py --project projects/SLUG neighbors RES-1 --type requires-input-to --direction incoming
python3 scripts/research-tickets.py --project projects/SLUG show RES-1 --section "Statement and scope"
python3 scripts/research-tickets.py --project projects/SLUG source check RES-1
```

On Windows use `python` or the Python launcher selected at setup in place of `python3`. The agent chooses the query needed for the question and prepares any write request; this example list is not a checklist to run in full. Users need not write JSON or learn commands. Reads may rebuild the disposable index, but never initialize tickets, begin work or change canonical records. Search covers metadata and bounded excerpts, not full text. Respect `excerpt_scope_complete`, warnings, `truncated` and cursors; a missing match does not prove that an assertion is absent.

`parent`/`contains` express organization, not proof. `requires-input-to` records one proof route; `sufficient-route-to`, `refutes`, `useful-for`, `reviews` and `related` retain route, logic, evidence and endpoint versions. No relation propagates truth, priorities or readiness automatically. Preserve superseded relations. `neighbors --include-noncurrent` inspects history.

## Source checks and guarded writes

Use [WRITE-API.md](research-tickets/WRITE-API.md) for enrollment, request envelopes, source bindings and recovery. Create stable keys, use exact generation/file/session versions, and keep the same operation ID and packet when retrying an uncertain write. On conflict, inspect the difference; never silently refresh guards and resubmit. Only the writer modifies canonical ticket data. Never edit the index by hand.

`source snapshot` verifies local source bytes in the selected capsule/paper or an explicitly registered Git clone. Commit evidence records the full SHA, path and SHA-256; working snapshots remain unpublished. Source verification does not contact a remote or establish proof validity. Before using committed work as a published milestone, follow existing approval/private-destination rules and verify the pushed SHA separately. External registration contains a machine-specific absolute clone path; inspect and adapt it explicitly on a new machine without weakening origin checks. Prefer capsule/paper sources for a portable single-workspace setup.

Workflow start/doctor checks at most 20 references for returned candidates, active work and ancestors. Continue `source check <source_check_ids...> --cursor <source_checks_next_cursor>` when truncated. Explicitly check each other claim/input before relying on it. With no candidates, doctor may check zero sources. Inspect each `state` and, for commit sources, `reference_state`: changed/missing working files do not invalidate a verified historical blob. A successful command is not a claim that all evidence is current.

On `PENDING_TRANSACTION`, inspect `recover status`. Finish only against its inspected journal hash. Unknown edits must be preserved and reconciled; `keep-current` requires inspection of every target hash and a coherent resulting state. Do not prune receipts, runs or harness history.

## Portability and privacy

Use a local workspace outside cloud-sync folders. Windows hashes the canonical inventory on each query because creation time cannot detect content edits; parsed records are still cached and `inventory_bytes_read` reports that I/O separately. POSIX uses descriptor-based no-follow access and file locks; Windows uses byte-range locks, checks for symlinks/reparse points, and atomic file replacement. File bytes are flushed, but Python's Windows standard library cannot flush directory metadata: the journal supports recovery after process interruption, not a universal power-loss durability guarantee. Filesystems without required locking or hard-link support fail rather than silently dropping those checks. These are cooperating-client safeguards, not a hostile-filesystem sandbox.

Tickets, exact-source references, operational sessions and receipts are unpublished research. Follow [safety.md](safety.md) and AGENTS.md for private backup and external transmission consent. Never publish a populated store to the public distribution. The strict release validator accepts only the bundled engine, documentation and wholly synthetic fixtures by exact filename; it continues to reject real stores, caches and local recovery artifacts. [TESTING.md](research-tickets/TESTING.md) describes verification and limits.
