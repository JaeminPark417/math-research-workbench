# Canonical write API

This is the Workbench local ticket contract. Run `python3 scripts/research-tickets.py --project /absolute/project/path write --request-file packet.json`. Python 3.9+ and its standard library suffice. `--root` is reserved for explicit test/legacy stores. JSON can be supplied by `--request-file -` on stdin. The Python equivalent is `IssueStore(root).apply(request)`.

## Request envelope

```json
{
  "operation_id": "unique-intent-001",
  "expected_generation": "generation from the latest query",
  "operations": []
}
```

Operation IDs, creation keys, run IDs and new relation keys use 1–64 ASCII letters, digits, underscores or hyphens, beginning with a letter/digit. Keep the entire request unchanged for retries. A reused ID with different content is rejected. A conflict requires inspection and a new request/operation ID. At most 20 operations, 32 changed files including receipt, and a 32 MiB journal are accepted per transaction. CLI input is limited to 4 MiB. Bounds are checked before canonical publication. A prepared transaction survives interruption.

## Create, update, archive and relations

Creation assigns the next free RES number under the common lock. Stable `key` prevents accidental duplicate integration. Optional parent references and relation endpoints may use `@key` for an issue created in the same request, even if its create operation appears later. New issue statuses are Backlog (default), Ready, or Todo. Mathematical kinds are theorem, lemma, obligation, counterexample, obstruction; experimental research kinds are question, hypothesis, experiment, result, analysis, decision; activity is the shared operational kind. Kind is immutable after creation. Only activity can become Done, begin a work session or be an operational blocker. Experiment means a design, not a runnable activity.

```json
{
  "operation_id": "record-scoped-observation-001",
  "expected_generation": "replace with current generation",
  "operations": [
    {
      "op": "create", "key": "scoped-lemma", "kind": "lemma",
      "title": "A precisely scoped claim", "parent": "RES-5",
      "body": "## Statement and scope\n\nRecord the exact assumptions and claim.\n",
      "priority": 3, "priority_rationale": "Needed by the chosen route"
    },
    {
      "op": "create", "key": "failed-stronger-claim", "kind": "counterexample",
      "title": "Counterexample to the stronger version", "parent": "@scoped-lemma",
      "body": "## Statement and scope\n\nRecord the example and exactly which claim fails.\n"
    },
    {
      "op": "relation-add", "key": "counterexample-scope",
      "from": "@failed-stronger-claim", "to": "@scoped-lemma", "type": "refutes",
      "to_inline_target": "The stronger version, not the retained scoped claim",
      "route": "named research route", "logic": "Only this stronger assertion fails",
      "evidence": "See the explicit example in the counterexample body"
    }
  ]
}
```

Updates require `expected_version` equal to the current whole-file `source_hash` (select it with `list --fields id,source_hash`). All updates to one issue in a single packet use its original version. Allowed `changes`: title, status, priority, priority_rationale, parent, labels, tags, archived, summary, blocked_by, next_action, body and notes, plus verified claim_ref and source_refs bindings and outcome. Unmentioned metadata/body/notes remain unchanged. Body and notes limits are 100,000 and 50,000 characters, respectively. Do not include the reserved local-notes marker. Priority changes require a nonempty rationale. Clearing parent uses null; clearing lists uses []; next_action/rationale must remain nonempty if set.

Priority values are 0 unassigned, 1 urgent, 2 high, 3 normal and 4 low; sorting places 0 last. Nonactivity statuses such as In Progress/In Review are administrative annotations; workflow start and untracked_in_progress enumerate activities only. Query other kinds directly when investigating research records.

```json
{"op":"update","id":"RES-13","expected_version":"current file hash","changes":{"priority":1,"priority_rationale":"Unblocks the selected route","next_action":"Check the remaining hypothesis"}}
```

`{"op":"archive","id":"RES-13","expected_version":"current hash","archived":true}` preserves the issue and every relation. Set false to restore. Current active-run activities cannot be archived or moved out of In Progress/In Review until ended. Hierarchy, duplicate and operational blocker cycles are rejected. Existing duplicate history is preserved; assigning new duplicate targets is not supported.

Relations support requires-input-to, sufficient-route-to, refutes, useful-for, reviews, related, plus the experimental relations below. `contains` is derived only from parent metadata. New edges require route, logic and evidence. Self-refutations additionally require `to_inline_target`. The writer captures final local body/file hashes and any claim_ref/source_refs/outcome for both endpoints. Existing imported commit/heading/inline provenance is retained. Body, claim_ref, source_refs or outcome edits mark touching current edges needs-review; note/priority edits do not. Missing legacy source_refs/outcome normalize to []/null, preserving old math edge freshness.

| Experimental relation | Allowed source → target kinds |
|---|---|
| tests | experiment → hypothesis/question |
| produces | experiment/activity → result |
| supports, challenges | result/analysis → hypothesis |
| interprets | analysis → result |
| informs | result/analysis → decision |
| motivates | decision → question/hypothesis/experiment/activity |

These edges retain scoped reasoning without computing truth or operational readiness. No supports/challenges aggregation, automatic hypothesis verdict or conditional activity activation is performed. See [EXPERIMENTAL-WORKFLOW](EXPERIMENTAL-WORKFLOW.md) for semantic guidance.

```json
{"op":"relation-supersede","key":"old-edge","reason":"The scope changed","replacement":"new-edge"}
```

Replacement is optional but must name an existing or same-packet edge. Superseded edges remain stored; `neighbors --include-noncurrent` exposes them.

## Operational session lifecycle

`workflow start --limit 5` returns generation, harness_version, active and last-ended session summaries/versions, bounded ready candidates and untracked in-progress activities. The last_run summary includes its next action and persistent math_run reference so a fresh context can resume paused work. It writes no source files. Use start again to resume after interruption; `workflow run ID` pages events.

Begin requires `expected_harness_version` in the envelope and one final operation:

```json
{"op":"begin","run_id":"scope-review-001","issue":"RES-13","reason":"Highest priority ready activity that advances this route","next_action":"Inspect the exact assumptions"}
```

Checkpoint/end require envelope `expected_run_version` from start's active.version. Only one workflow transition is accepted, and it must be the final operation. Create findings/relations before it so references can use `@key`.

```json
{"op":"checkpoint","run_id":"scope-review-001","summary":"A stronger claim failed under the recorded example","next_action":"Check the restricted statement","evidence":[{"issue":"RES-18","description":"Recorded counterexample"}]}
```

```json
{"op":"end","run_id":"scope-review-001","outcome":"completed","summary":"The scope audit is recorded","next_action":"Review the remaining lemma independently","evidence":[{"issue":"RES-18"}]}
```

Session outcomes completed/paused/blocked set the activity to Done/Ready/Backlog. Begin sets In Progress. These are operational states, not proof verification or empirical support, and are distinct from result/analysis outcome metadata. Conditional follow-ups must stay Backlog until an explicit recorded decision activates them; blocked_by checks only whether preceding activities are Done. completed needs evidence; paused/blocked may have an empty evidence array. Each event retains timestamp, summary, next action, operation ID, created IDs and hashed evidence. At most 999 begin/checkpoint events leave room for the final end. Runs are capped at 2 MiB UTF-8; non-end transitions reserve 256 KiB for closing. A RUN_LIMIT_REACHED error means end the current run before beginning another.

The conditional-follow-up decision rule is an agent instruction; the writer does not enforce a decision approval gate. Ordinary status updates remain available, and agents must record the reason and supporting decision before activating conditional work.

Evidence is either `{ "issue": "RES-18" }` (also `@key`) or `{ "path": "artifacts/check.md", "sha256": "inspected file hash" }`, optionally with description. Use the issue form for all issue files; path-form references accept only ticket-store artifacts/notes with extensions md, txt, json, tex, lean, py or csv. Paths are relative, no symlinks or traversal; at most 20 references. Issue evidence captures the final version in the transaction. Historical hashes preserve which revision was used; a later file edit does not rewrite old evidence.

## Recovery

Inspect `recover status`. If pending, it returns journal_hash plus each target's before/after/conflict state and current_hash. Normal reads fail closed; they never finish a pending transaction. Write retries automatically attempt safe recovery.

`recover finish --request-file` accepts:

```json
{"expected_journal":"journal_hash from inspected status"}
```

Unknown edits block finish without overwriting them. Preserve and reconcile the edit before retrying. If the reviewed current files form a coherent state, an explicit `recover keep-current --request-file` can abandon the pending plan:

```json
{
  "expected_journal":"inspected journal_hash",
  "expected_files": {
    "data/issues/res-13.md":"inspected current_hash",
    "data/operations/unique-intent-001.json":null
  }
}
```

Include **all** paths from status, not just this example. Current graph and active run must validate. Abandonment preserves files/history and records a permanent abandoned receipt; that operation ID cannot be retried. A published applied receipt is the commit point, so finish only archives the remaining journal and does not revert external edits made after that receipt.

Receipts in data/operations, all data/runs records and data/harness.json are canonical and must not be pruned. The last_run pointer is strictly validated as well as active; missing or corrupt records require restoration from Git/backup, rather than dropping references. Full before/after history is Git-ignored and can be separately archived. Cache is disposable; the root lock is not. Cooperating clients are serialized, but external editors do not participate in this lock: an external write between the final hash check and replacement can still be lost. This is not an adversarial filesystem sandbox or an ACID database.

After successful source recovery, a cache refresh failure returns the recovery status with `index_updated=false` and `index_error`; retrying ordinary index refresh/rebuild does not replay the source write. Full transaction history uses `files[]` entries for all before/after contents; the top-level `before` is only a compatibility convenience for a single-issue web patch.

## Source bindings and proposed formulations

Generate a reference from registered source bytes, then inspect the relevant source before using it:

```bash
python3 scripts/research-tickets.py --project projects/SLUG source snapshot capsule README.md --heading 'Research State Spine' --object-id Thm-001
python3 scripts/research-tickets.py --project projects/SLUG source snapshot research research-notes/claim.md --commit FULL_40_CHARACTER_SHA --heading 'Statement'
python3 scripts/research-tickets.py --project projects/SLUG source check RES-1
```

`source snapshot` is read-only. References contain repository, mode (`working` or `commit`), path, sha256 and optional heading/object_id; commit mode requires the full SHA. `capsule` is the current project directory, excluding tickets/. Other repositories require a registered absolute clone path and expected credential-free origin in tickets/project.json. The helper checks actual clone root/origin, safe relative path, text size, exact bytes and optional unambiguous heading. It does not contact a remote or certify a pushed commit. Follow the existing private-repo/pushed-SHA gate before updating milestone or canonical mathematical evidence.

`claim_ref` on create/update requires `object_id`. It connects an issue to the canonical source; the ticket body remains an operational summary, not an independent truth ledger. Unbound mathematical objects have derived `statement_role: proposed`. A bound body cannot be overwritten, and its binding cannot be removed or redirected to another object. A source revision can be rebound only after checking the actual canonical source, with the same object ID; the tool verifies bytes but cannot authenticate HUMAN PROMOTION.

Use a separate append-only proposal for mathematical kinds instead of overwriting a bound statement. `propose` is rejected for activity and the six experimental kinds; create a revised experimental research record and retain its predecessor:

```json
{"op":"propose","id":"RES-1","expected_version":"inspected whole-file hash","statement":"Proposed replacement with exact assumptions","reason":"The recorded counterexample invalidates the broader scope"}
```

The writer appends the proposal, its base source reference, timestamp and operation ID. Every entry remains `proposed`; there is no machine promotion operation. Read it with `list --fields id,claim_ref,statement_role,proposals`. Pending proposal changes do not invalidate canonical proof edges. Local body edits mark ticket edges needs-review, while actual canonical upstream changes are handled through the Spine workflow. `source check` reports drift without rewriting either source or edge. Before using another issue or cross-route dependency, explicitly check that issue too.

`source check RES-1 [RES-2 ...] --limit 20 [--cursor CURSOR]` checks claim_ref and source_refs on selected issues and ancestors, paging references before reading their source bytes. It returns checks, ids, total, returned, truncated, generation and next_cursor. The limit is 1–50; up to 51 input IDs are supported and normalized to a unique numeric order. Cursors are bound to the IDs and ticket generation; working source drift is observed at each call, not frozen across pages. Workflow start and doctor check at most 20 references for returned candidates and the active activity, exposing source_check_ids, source_checks_truncated, source_checks_total and source_checks_next_cursor. Continue with `source check <source_check_ids...> --cursor <source_checks_next_cursor>`. These checks are not an exhaustive audit of every project source. A source-check response with ok=true means the check ran; inspect each state (current, changed or unavailable, with reason when unavailable) rather than treating ok as evidence validity.

## Supporting source references and empirical outcomes

Source-check entries include repository, path, mode, optional commit/heading/object_id and reference_sha256 so every result identifies the checked reference. The existing state field reports working-tree drift (current/changed/unavailable); sha256, when present, is the working file's current hash. For commit mode, reference_state separately reports verified/unavailable for the historical commit evidence. A verified commit can coexist with changed or unavailable working files. A failed historical verification returns unavailable and its reason without claiming verified evidence. This preserves the earlier drift API while making historical evidence validity explicit. Source checks do not establish publication or scientific truth.

Create/update accepts optional source_refs: an array of at most 20 distinct references produced by source snapshot. Their shape matches repository evidence above; object_id is optional, and all supplied references are byte-verified before publication. Stored frontmatter is desk_source_refs; index field is source_refs, default []. Exact duplicates are rejected; ordering is retained. A change to the array marks touching current edges needs-review. Source references may supplement claim_ref without changing its identity or immutable-body rules. Source files must be allowed text in the capsule or a registered local clone, not remote URLs/paths or raw .log files. Use a dated MD log or JSON/CSV manifest to describe remote artifacts and execution metadata.

Optional outcome (desk_outcome in frontmatter) is allowed only on result and analysis; values are positive, negative, null, mixed, inconclusive, invalid. Omitted or JSON null means unassessed; the string "null" means an assessed null finding. List/search accept `--outcome negative` (or another enum), and fields can include source_refs/outcome. The cache schema is 5 and rebuilds automatically; canonical note/registration schemas remain unchanged. This field is a descriptive interpretation under the recorded protocol, not a hypothesis verdict or run exit code.

Unbound experimental kinds have statement_role research-record; activity is operational; unbound mathematical kinds remain proposed; any claim-bound object retains canonical-reference. These derived roles do not grant scientific validity. A successful activity with unfavorable results can therefore be Done while its result has outcome negative and its hypothesis remains unverified. A runnable synthetic example is `python3 -B meta/research-tickets/examples/experimental-cycle.py`.

Repository evidence in checkpoint/end uses `{"source": <reference>, "description": "scope and limitations"}`. Historical commit references remain valid even after HEAD moves. Working snapshots explicitly remain unpublished evidence. Old event hashes are never rewritten.

A begin operation may include `math_run: {"run_id":"Run-20260918-001","source":<reference>,"object_ids":["Obligation-001","Attempt-002","Evidence-003"]}`. This references the persistent external research ledger. The ticket `run_id` is a unique operational session ID; several sessions may reference the same persistent math run. End seals only the operational session. The math_run binding is immutable within a session. Small tasks below the existing sustained-research threshold omit it.

## Project enrollment and coverage

`--project PATH init [--name TITLE] [--config-file registration.json]` explicitly creates an empty store. It does not import old projects or rewrite README. Existing tickets/ is never overwritten. Default registration is partial and warns that capsule Next steps and research-run ledgers remain unindexed. Enrollment is a separate user-requested project migration step.

Registration schema:

```json
{
  "schema": 1,
  "project_id": "2026-example",
  "coverage": {"state": "partial", "scope": "Selected main route", "untracked": ["Other routes remain in the capsule"]},
  "repositories": {"research": {"path": "/absolute/canonical/clone", "origin": "https://github.com/OWNER/REPO"}}
}
```

The project ID must equal the capsule directory name and use 1–120 lowercase letters, digits or hyphens, starting with a letter/digit. Use an absolute canonical directory path without symlink components (on macOS, resolve temporary /tmp or /var aliases before testing). `RES-1` is local to one project; use `project_id:RES-1` across project boundaries. Relationships are intra-project. Registration changes invalidate the index generation and stale write requests. `doctor` checks the complete local index plus active/last session consistency and reports partial coverage. It does not enumerate or migrate existing projects or assert full external-source coverage.

Source rebinding retains the identity tuple `(repository, path, heading, object_id)` and only updates its version/hash. Relocating a canonical object requires a separately reviewed migration; ordinary update cannot redirect a same-named obligation to another run. Rebinding marks prior touching current ticket edges needs-review and preserves their old endpoint snapshots. New edges capture the source reference as well as the local body/file hashes. This prevents a refreshed source pointer from silently making old proof relationships look current.

## Paper enrollment and source scope

`--paper /absolute/papers/<slug>.md` selects an existing paper/book note; it is mutually exclusive with `--project` and `--root`. `init [--name TITLE] [--config-file registration.json]` creates its sibling `<slug>/tickets/` without changing the note. `ticket_project.initialize_paper(note, name=None, config=None)` and `load_paper(note)` are the Python counterparts; load returns `(root, config)`. Missing registration returns NOT_CONFIGURED without creating files. Initialization stages the whole support directory and publishes it by one rename under a library lock. Any existing support path is refused, including non-ticket content. Failures before publication leave the note and live support path unchanged; an interrupted process can leave ignored staging directories for later inspection. This is not a guarantee against noncooperating external editors.

Optional paper registration extension (schema remains 1; ordinary project registrations are unchanged):

```json
{
  "schema": 1,
  "project_id": "2026-author-topic",
  "coverage": {"state": "partial", "scope": "Main theorem and its stated inputs", "untracked": ["Appendix and cited proofs"]},
  "repositories": {},
  "subject": {
    "kind": "paper",
    "note": "2026-author-topic.md",
    "extracts": ["content/2026-author-topic.md"]
  }
}
```

The note must be a regular UTF-8 `.md` file with one first-frontmatter `type: paper` or `type: book`; the filename uses the same lowercase slug rule as projects. Use the canonical path with no symbolic-link components (resolve macOS /tmp or /var aliases for fixtures). Plain/simply quoted type keys and values and trailing YAML comments are accepted; this selector is not a general YAML validator. `subject.kind` is the fixed workflow literal `paper` for both papers and books; the bibliographic type remains in the original note. Note stem, registration project_id, support directory and data/project.json ID must agree. Selectors, direct index/store APIs and source verification all enforce this identity. project_id is retained as a storage identifier, not a claim that the note is a research project. Paper doctor/workflow responses include subject and the `../../<slug>.md` capsule pointer.

In a paper store, `paper` is a logical working-text alias rooted at the note's own directory, allowing only its exact note and up to 50 distinct registered extract paths under that directory's `content/`. For `papers/gnn/<slug>.md`, this means `papers/gnn/content/`, not the top-level `papers/content/`. Nested paths such as `content/thesis/chapter-01.md` are supported. Traversal, unsafe paths, symlinks, ticket-store paths and binary PDFs are rejected. A missing extract does not invalidate the registration; checks for that source report unavailable. Snapshots, verification on writes and drift checks enforce the same allowlist. Merely listing stored source_refs is metadata retrieval, not source verification.

Logical paper commit mode is rejected before Git access. A paper subject cannot also register repositories.paper. Existing ordinary project stores with a real Git repository alias named paper retain their former working/commit behavior. `capsule` in a paper store points to `<slug>/`, allowing supporting text outside its tickets/ directory. Other explicitly registered Git aliases remain available. No paper source mode traverses arbitrary sibling notes. PDFs stay in files/ or configured external storage; text provenance must record PDF/version/hash/page and extraction/visual checks in the body. Hash verification authenticates the bytes read, not equivalence to a PDF or proof validity.

```bash
python3 scripts/research-tickets.py --paper papers/2026-author-topic.md source snapshot paper 2026-author-topic.md --heading 'Main theorem' --object-id Thm-1
python3 scripts/research-tickets.py --paper papers/2026-author-topic.md source snapshot paper content/2026-author-topic.md
```

Omit heading for repeated/ambiguous headings and record precise locators in the body. Keep object_id stable; version/page/hash metadata belongs in provenance. Bound claim identity/body restrictions apply unchanged. A different statement, path or heading uses a proposal/new revision record, not silent rebinding. New reviews preserve old analysis source_refs by agent policy; the writer does not make general analysis bodies immutable. See [PAPER-WORKFLOW](PAPER-WORKFLOW.md).

## Multiple-tag queries

List/search and workflow start accept repeated `--tag VALUE` flags (up to 20); Python `tag` accepts a single legacy string or a nonempty list. Matching is AND across each record's combined tags and labels. Order and duplicates are normalized before binding pagination cursors. Changing the filter invalidates its cursor. Other list filters still combine with AND.

Filtered workflow start returns matching ready candidates with tags/labels, but always retains the whole store's active session, last_run and untracked_in_progress IDs. Active/last summaries include tags/labels and matches_filter; requested_tags reports the normalized filter. There remains only one active operational session per store. Source-check bounds and cursor continuation rules above apply unchanged, including checks of the active activity even when outside the requested filter.
