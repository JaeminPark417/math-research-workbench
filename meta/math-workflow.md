# Mathematical research workflow

Use the records that make the current question inspectable and resumable. The researcher can start with a question, a proof, an existing project, or a paper; do not force an inbox-to-project ceremony or a fixed sequence of tools.

## Capture, formulate, and find sources

Preserve what the researcher supplied. Use `inbox/` for unclassified material, `ideas/` for a direction, `papers/` for a source worth retaining, `projects/` for sustained work, and `notes/` for reusable background. Work in the existing destination when it is already clear. Archive processed source material after checking its durable note and links.

State the objects, definitions, hypotheses, quantifiers, exceptional cases, and exact target. Ask only when an ambiguity changes the mathematics or the authorized work; label uncertain assumptions and unverified references. Do not silently strengthen or weaken the question.

When literature matters, verify bibliographic facts against authoritative records and identify the exact theorem, definition, page, or version used. Distinguish the source's claim from interpretation. Retain an unverified lead as unverified; a search with no result does not establish absence.

## Keep one canonical project map

For sustained work, create a project from `meta/templates/project.md`: `README.md`, `logs/`, `sessions/`, and `drafts/` as needed. The README Research State Spine is the canonical map of stable, paper- or decision-relevant definitions, claims, dependencies, gaps, and source links. Use `Def-NNN`, `Lem-NNN`, `Prop-NNN`, `Thm-NNN`, `Cor-NNN`, and `Gap-NNN`; never renumber or reuse an ID. Scratch calculations and failed routes stay in the working log or draft.

Keep mathematical state, review provenance, and integration state separate. Automatic editorial integration may copy a researcher-provided or already-canonical new object without semantic change at baseline states (`conjectural` for claims, `open` for gaps, `unchecked` review, `isolated` integration), or update source/dependency/next-action metadata. A new AI-authored formulation, changed hypotheses, quantifiers or scope, truth-bearing state change, statement matching, closure, retirement, or circulation-baseline decision remains proposed until Human Promotion. Mark dependents `review-stale` after an authorized upstream change becomes canonical; keep the stale effects of a merely proposed upstream change in its proposal.

Read only the relevant note-type contract in `meta/schemas.md` and the applicable conventions when writing. Preserve English structural headings and field labels while using the researcher's chosen language for mathematical prose.

## Use a run when substantive work needs continuity

Use `$math-research-run` for a second serious attempt, substantive mathematical work resumed across sessions, several obligations or scoped adapters, or a load-bearing paper/major-decision claim. A status inquiry, ordinary explanation, simple exposition edit, or one-step calculation does not create or resume a run. If uncertain, keep an ordinary research log until sustained work actually begins.

Continue an existing matching run; use `meta/templates/research-run.md` only when a new record is needed. The compact record contains the exact Problem Contract, route, obligations, consequential attempts, evidence, scoped synthesis, and human decisions. It does not require a branch tree, external reviewer, formal checker, or separate logs for ordinary reasoning steps. Its control stages are a way to record progress, not mandatory separate messages or tool calls:

`SPEC → ROUTE → OBLIGATIONS → PROVE / DISPROVE → optional adapters → SYNTHESIZE → HUMAN PROMOTION`

For an existing target, record its stable ID and repository-relative README path in `Spine target reference`. Copy its exact current wording into `Exact target`. Record the current `HEAD` commit only if that wording matches it at SPEC start; otherwise use `working snapshot Run-YYYYMMDD-NNN` with the actual run ID. The copied text is the content anchor; never invent a separate Spine version number. Version run-local changes and keep the project Spine canonical. Do not leave SPEC until `Exact target`, `Success criterion`, and `Refutation criterion` are explicit.

Record one Route row per selected adapter. Use the existing `adapter` and `adapter_scope` schema; `mixed` scopes are semicolon-separated `adapter-name: exact scope` entries. A method selects how to investigate an obligation, not its truth. Reuse a single bounded next action instead of maintaining independent copies in the manifest, a resume block, and a session summary.

## Develop and test the argument

Use useful checks: degenerate cases, missing hypotheses, counterexamples, logical dependencies, nearby verified results, and appropriately scoped computation. Record attempts that produce a candidate, counterexample, meaningful failure, changed direction, or reproducible result. Minor reasoning can remain in the linked derivation. Preserve why a route failed and the conditions under which retrying could help.

An attempt's result must name its scope and limitations. Computation covers tested cases; literature review covers recorded sources; a formal checker covers an encoding. None automatically establishes the intended theorem. Keep conflicting findings visible. Synthesis reconciles cited work; any new truth-bearing step needs its own unverified attempt.

## Audit an important proof

For a load-bearing proof or suspected gap, use `meta/templates/proof-audit.md` or an equivalent linked audit with exact target, complete candidate version, dependencies, checked steps, counterexamples, gaps, and limitations. Inspect the joins between lemmas as well as the lemmas themselves. Choose independent review at consequential milestones rather than requiring external reviews before and after each small edit.

Distinguish the actual work performed:

- `same-context-audit`: the reviewer has the originating conversation or prior reasoning. Useful, but not independent.
- `fresh-isolated`: an isolated search given the target, obligation, and permitted sources without originating, parent, or sibling reasoning. This is independent exploration, not an audit of a proof it never received.
- `independent-proof-audit`: a reviewer isolated from the prior conversation and reviewer verdicts receives the exact target, complete candidate proof, and dependencies at recorded versions. It must receive the proof to inspect its inferences. Record its actual inputs and exposure; a new persona, model, or session alone proves no independence.

Use the optional execution records for the two isolation claims; if isolation or sufficient input cannot be established, say so and retain `same-context-audit`. AI agreement, a failed attack, and `no-error-found` do not close a gap. Human review or suitable formal checking still requires a faithfully matched statement and the human decisions below. External transmission follows `meta/safety.md`, including provider, purpose, exact outgoing scope, and consent.

## Load specialist detail only when used

For a bounded proof-search harness, isolated dispatch, or independent proof audit, read **Bounded dispatch** in `meta/math-details.md` and append `meta/templates/research-run-extensions.md` to the run. For Lean/formalization, read **Formalization trust boundary** in that guide and use the same appendix plus the existing formalization manifest. The shared appendix keeps old table contracts compatible; unused branch tables may remain empty and unused formalization is `not used`.

Ordinary single-agent natural proof work keeps the compact template without those extension headings. Add the appendix before recording a branch assignment, isolation claim, formal adapter, formal review, or formal evidence. Existing detailed runs remain valid; do not strip their histories or bulk-migrate them.

## Human decisions and evidence

Use one scoped, non-cumulative evidence descriptor per row: `computationally-checked`, `formal-encoding-checked`, `statement-matched`, `literature-audited-within-scope`, or `expert-reviewed`. Record source/artifact version, result, assumptions, limitations, and applicable provenance. One descriptor never implies another or a truth status.

Keep the exact Human promotion fields at `not confirmed` until the researcher supplies a dated, scoped decision. `statement-matched` requires explicit human confirmation of correspondence to the intended mathematics. `closed-by-researcher` requires that decision and linked evidence. Record only a user-consented identifier or role; automation checks record structure, not human identity. The circulation baseline is the exact artifact version the researcher designates as ready to share. A completed run means that the activity ended, not that the theorem was proved.

## Checkpoint without duplicating the research

At a meaningful transition, record what changed, its evidence, unresolved issues, and the next bounded action in the current run. For an enrolled ticket store, the selected activity owns the operational next action; link to it from the run and capsule while the capsule retains strategic priorities and unindexed work. Without tickets, the run manifest owns its current next action. Session summaries are dated history and links, not another mutable queue or a copy of the proof.

Use `meta/research-ticket-workflow.md` and `$research-issues` only for a requested enrollment or an existing store. Restore partial coverage and active/last operational state. A short ticket activity can refer to the same persistent run across sessions; activity completion and source checks never promote mathematical truth. Status inquiries do not enroll stores or start research.

Preserve source notes and failed attempts. Extract genuinely reusable material into `notes/` with links to its provenance. Follow the normal private-backup and external-transmission rules in `meta/safety.md`; research runs never belong in the public Workbench distribution remote.
