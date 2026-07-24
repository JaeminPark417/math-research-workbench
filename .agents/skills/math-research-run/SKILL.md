---
name: math-research-run
description: Maintain an inspectable, bounded control loop for sustained mathematical research inside a Math Research Workbench project. Use implicitly when a project reaches a second serious attempt, resumes across sessions, needs multiple obligations or adapters, or develops a load-bearing paper claim; use explicitly when the researcher invokes `$math-research-run`. Do not invoke for simple questions, routine explanations, lightweight exposition, a one-step calculation, or work that has not crossed this entry threshold.
---

# Math research run

Let the researcher keep speaking naturally. Maintain the control loop and its
records in the background, and interrupt only at an epistemic or safety
boundary that needs a human decision.

## Apply the entry gate

Use this workflow only for sustained project mathematics. The objective entry
threshold is crossed when any one of these conditions holds:

- a second serious attempt at the same target is beginning;
- the work is being resumed in a later session;
- the target requires multiple obligations or multiple scoped adapters; or
- a claim is load-bearing for a paper or major research decision and therefore
  needs an inspectable audit trail.

If the threshold is uncertain, keep an ordinary `research-log` and start a run
only when one of these conditions is met. If the work does not already belong
to a project, follow the normal project-opening workflow before creating a run
record. Do not create a run merely to summarize a project, answer a question,
explain a theorem, edit exposition, or perform a single routine calculation.

For a qualifying task, create or continue a dated `research-log` from
`meta/templates/research-run.md`. Reuse an active run when its Problem Contract
still matches. Create a new `run_id` when the target, hypotheses, or success
criterion changes materially. Do not migrate older logs unless the researcher
asks.

Assign a new run the next unused project-local ID in the form
`Run-YYYYMMDD-NNN`. The date segment must equal the run note's `date`, which is
the run's start date. The full ID must be unique within that project. Never
renumber or reuse an existing run ID. Ordinary research logs omit `run_id`,
`adapter`, and `adapter_scope` entirely.

Do not require a swarm, daemon, model API, or special solver. Use available
agents and tools only when they help a precisely scoped obligation. Keep each
attempt bounded and preserve failed routes.

## Run the loop

Follow this order:

`SPEC → ROUTE → OBLIGATIONS → PROVE / DISPROVE → optional adapters → SYNTHESIZE → HUMAN PROMOTION`

### 1. SPEC

Write a Problem Contract using the exact English headings and field labels in
`meta/templates/research-run.md`; do not translate, rename, or remove them.
Complete the exact target, objects, definitions, hypotheses, quantifiers,
exceptional cases, allowed sources or tools, success criterion, refutation
criterion, and explicit exclusions. Version the contract inside the log. Do
not leave SPEC until `Exact target`, `Success criterion`, and `Refutation
criterion` are explicit. Ask the researcher when an ambiguity would change the
theorem; do not silently choose a stronger or weaker statement.

Treat the Problem Contract as a run-local execution snapshot, not the canonical
project state. When it targets an existing Research State Spine object, record
the stable ID in the `Spine target reference` field together with the
repository-relative project README path. If `Exact target` matches the wording
in the current `HEAD` at the start of SPEC, record that commit hash. Otherwise
write `working snapshot Run-YYYYMMDD-NNN`, replacing the placeholder with the
run's actual ID. In every case, copy the exact current Spine wording into
`Exact target`; that text is the content anchor for a working snapshot. The
Contract version tracks run-local revisions. Never invent a separate Spine
version number.

Only editorial Spine integration is automatic: add a new stable object copied
without semantic change from a researcher-provided or already-canonical source
at the baseline states (`conjectural` for a claim, `open` for a gap,
`unchecked` review, and `isolated` integration); update source, dependency, or
next-action metadata. Mark dependents `review-stale` only after an upstream
change is already canonical or is applied after HUMAN PROMOTION. For a merely
proposed upstream change, keep its downstream stale effects in the run's
proposal. Keep a new AI-authored formulation, a change to an existing
statement's hypotheses, quantifiers, or scope, a truth-bearing mathematical or
gap-state change, statement matching, closure, retirement, or a
circulation-baseline decision as a proposed change until HUMAN PROMOTION.

### 2. ROUTE

Select one or more routes and record why:

- natural-language proof development;
- formal encoding of a stated lemma or finite subproblem;
- constructive or computational search with a defined evaluator;
- literature-sensitive comparison against verified primary sources.

The route chooses methods; it does not determine mathematical truth.

When recording the optional `adapter` frontmatter field, use only
`natural-proof`, `formalization`, `constructive-search`, `literature-audit`, or
`mixed`; leave it empty when no adapter is selected. Put the exact bounded
purpose in `adapter_scope`, and record every selected route in the body Route
table. For `mixed`, encode one scope per adapter in `adapter_scope`, separated
by semicolons, in the form `adapter-name: exact scope; adapter-name: exact
scope`.

### 3. OBLIGATIONS

Decompose the target into exact, testable obligations. Record dependencies,
what would establish each obligation, what would refute it, and known edge
cases. Keep run-local obligation IDs in the log. Keep candidate objects
run-local during this stage. Reconcile an object into the Research State Spine
only after it has become stable and paper- or decision-relevant, and only under
the editorial boundary defined in SPEC; otherwise list it under Proposed
Research State Spine changes.

### 4. PROVE / DISPROVE

For important obligations, pursue both a constructive argument and an
adversarial failure search. Use a fresh-context pass only when the worker is
actually isolated from the originating reasoning and receives only the Problem
Contract, the exact obligation, and explicitly permitted artifacts. Record the
context supplied.

If genuine isolation is unavailable, label the work `same-context audit` or
`fresh pass not run`; never call it fresh or independent. Agreement between AI
passes is evidence to inspect, not proof.

Record every prove, disprove, and check attempt in the Attempt ledger,
including the context, method, result, artifact, limitations, or failure
reason.

### 5. Use optional scoped adapters

Use a computation, formal checker, or literature search only for a named
obligation and record it in `adapter`, `adapter_scope`, and the body Route table
when useful. For each adapter, preserve the exact input or statement, relevant
version, result, artifact or source, assumptions, and limitations. Follow
workspace approval, privacy, citation, and untrusted-content rules before any
external action.

A passing computation covers only tested cases. A formal checker covers only
the encoding. A literature search covers only the recorded sources and search
scope.

### 6. SYNTHESIZE

Reconcile supporting attempts, failure searches, adapter results, and
contradictions obligation by obligation. State what is supported within scope,
what is refuted, what remains open, and what is not claimed. Update the run log
and then apply only permitted editorial changes to the project Research State
Spine. Leave every other stable change proposed for HUMAN PROMOTION. After an
authorized upstream statement change becomes canonical, mark dependent
integration `review-stale` until it is rechecked; for a proposed upstream
change, record that downstream effect only in the proposal.

### 7. HUMAN PROMOTION

Propose promotions; do not perform truth promotion on AI authority. Preserve
the exact Human promotion field labels from the template. Leave both
confirmation fields at `not confirmed` until the researcher acts. Treat
`statement-matched` as present only after a human explicitly confirms that the
checked or reviewed statement matches the intended mathematics, with scope,
date, and a user-consented reviewer identifier or role recorded. A project
claim may become `closed-by-researcher` only with dated, scoped human
provenance and linked evidence. Without those confirmations, retain the
existing mathematical state and unresolved gap. The workflow records the
researcher's assertion; it does not authenticate or prove a person's identity.
Here, the circulation baseline is the exact artifact version the researcher
designates as ready to share outside the private working context.

## Record evidence without a ladder

Use scoped provenance descriptors such as `computationally-checked`,
`formal-encoding-checked`, `statement-matched`,
`literature-audited-within-scope`, and `expert-reviewed` only when the log names
their exact scope, artifact or source, result, limitations, and reviewer where
applicable. Put exactly one descriptor in each evidence-table row; never use a
slash-separated list. These descriptors are non-cumulative: one never implies
another, and none is a truth status. Identify a human only by an identifier or
role the user has consented to record; do not collect an email address,
institution, or other unnecessary personal information.

Keep `review_status` within the values in `meta/schemas.md`. AI work remains
`unchecked` unless a permitted human or formal review is actually documented.
Setting the run log's `status` to `complete` means only that the recorded
activity ended, not that the theorem was proved.

## Stay quiet at ordinary transitions

Do not narrate internal stage changes by default. Surface the control loop when
the researcher asks, when files will be materially reorganized, or when one of
these boundaries is reached:

- the Problem Contract is mathematically ambiguous;
- a proposed tool or external source needs approval or a privacy decision;
- prove and disprove attempts conflict;
- an encoding may not match the intended statement;
- a claim or gap is ready for explicit human promotion or closure.

At the end of a session, leave the run resumable: record the current stage,
open obligations, failed attempts, evidence limitations, and next bounded
action, then perform the ordinary session and Research State Spine updates.

Treat every run log as unpublished research. Before any commit, sync, or push,
show the exact files, obtain the required approval, and verify that the
research destination is exactly private. Before an upload or external review,
follow the workspace's separate per-transmission disclosure and consent rules.
Never commit or push a run log to the public Math Research Workbench
distribution remote; its public nature makes it unsuitable for research data.
