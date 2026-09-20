---
name: math-research-run
description: "Maintain a bounded research record for sustained mathematics: a second serious attempt, substantive research resumed across sessions, multiple obligations or adapters, or a load-bearing paper claim. Use on $math-research-run. Status inquiries, explanations, simple exposition edits, and one-step calculations do not create or resume a run."
---

# Math research run

Let the researcher work in ordinary conversation. Maintain only the records needed to recover the target, consequential attempts, evidence, and next action. Read `meta/math-workflow.md` for authority and proof-review boundaries; consult only relevant schema sections when writing.

## Start or resume

For a qualifying task, reuse an active run whose Problem Contract still matches. Otherwise create a dated `research-log` from `meta/templates/research-run.md` in an existing project. Open a project first only when sustained work has no project yet. If the entry threshold is uncertain, use an ordinary research log. Do not migrate older logs automatically.

Assign the next unused project-local `Run-YYYYMMDD-NNN`; its date equals the note's start `date`. Never renumber or reuse it. Ordinary research logs omit `run_id`, `adapter`, and `adapter_scope`. A material change to target, hypotheses, or success criterion starts a new run linked to the previous one.

Preserve the template's English headings and field labels. Fill `Exact target`, `Success criterion`, and `Refutation criterion` before leaving SPEC. For an existing Spine target, copy its exact wording and record its stable ID and README path in `Spine target reference`. Use the current `HEAD` hash only if that wording matches it; otherwise record `working snapshot Run-YYYYMMDD-NNN` with this run's actual ID. The copied wording is the content anchor. Never invent a separate Spine version number.

## Work and record meaningful changes

- Select a bounded route and exact obligations. Use `natural-proof`, `formalization`, `constructive-search`, `literature-audit`, or `mixed`; leave adapter fields empty if none applies. For `mixed`, give semicolon-separated per-adapter scopes and matching Route rows.
- Record consequential work in the Attempt ledger: candidate, counterexample, substantive failure, change of route, review, or reproducible tool result. Keep minor reasoning in its linked derivation. Preserve failed routes and retry conditions.
- Retain exact artifact/source versions, assumptions, and limits. Reconcile conflicting results obligation by obligation. New proof steps introduced during synthesis need a separate unverified attempt.
- Update the run manifest's next bounded action. If an enrolled ticket activity owns it, link to that activity rather than keeping a second live instruction. Session logs retain dated outcomes and links.

The usual single-agent run uses `Branch: none` and `same-context-audit`, `human`, or `tool` as appropriate. It needs no branch plan, prompt-hash table, repeated resume block, or external reviewer. A run ending means activity completion, not proof completion.

## Optional execution detail

Load **Bounded dispatch** in `meta/math-details.md` only for actual branch dispatch or an isolation claim. Append `meta/templates/research-run-extensions.md`; it preserves the existing five extension headings and tables. Use `meta/templates/research-branch-prompt.md` for a dispatched `Branch-NNN`, with exact inputs, write scope, budgets, stop conditions, and observed provenance.

`fresh-isolated` describes search without originating, parent, or sibling reasoning; it is not proof verification. `independent-proof-audit` requires an isolated reviewer to receive the complete candidate proof, exact target, and dependencies. Record the supplied proof as reasoning rather than falsely claiming no exposure. A new model or persona alone is not independence. If isolation is unavailable, use `same-context-audit` and state that limit.

For formalization, read **Formalization trust boundary** in `meta/math-details.md`, append the same execution extension, and use the existing manifest. Preserve `solution-only` solver scope and the disjoint trusted challenge/untrusted submission roots. `scripts/formalization_manifest.py` checks recorded structure and hashes; it executes no Lean or build commands. Record formal evidence only after actual checks run and their logs are observed. Unused branch tables can remain empty; unused formalization stays `not used`.

## Preserve mathematical authority

The project Research State Spine remains canonical. Automatic editorial integration may copy a researcher-provided or already-canonical new object without semantic change at `conjectural`/`open`, `unchecked`, `isolated`, or update source/dependency/next-action metadata. A new AI-authored formulation, changed statement or scope, truth-bearing state change, matching, closure, retirement, or circulation decision remains a proposal until Human promotion. Mark dependents `review-stale` only after an upstream change becomes canonical; keep a proposed upstream change's downstream effects in its proposal.

Use one scoped evidence descriptor per row, never a ladder of truth. Keep statement-match and closure confirmations `not confirmed` until a dated, scoped human decision is recorded, with a user-consented identifier or role and linked evidence. Record `statement-matched` and `closed-by-researcher` only under those respective decisions. The circulation baseline is the exact artifact version the researcher designates as ready to share. AI votes, no-error reports, computation, and formal encoding never perform this promotion. Validators do not authenticate a human or the truth of a record.

For existing `tickets/project.json`, use `$research-issues` and `meta/research-ticket-workflow.md` to restore coverage and operational state and link the persistent run through `math_run`. Do not enroll merely because this skill ran. Follow `meta/safety.md` for private research backup and each external transmission; no research run is published to the public Workbench distribution remote.
