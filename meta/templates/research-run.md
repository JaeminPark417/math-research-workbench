---
type: research-log
title: "Research run: exact target"
date: YYYY-MM-DD
updated: YYYY-MM-DD
language: en
project: "[[projects/project-slug/README]]"
kind: general
status: open
review_status: unchecked
run_id: ""
adapter: ""
adapter_scope: ""
related_papers: []
related_logs: []
---

<!-- This is a specialized research-log, not a separate note type. Use it only
after the entry threshold for sustained project mathematics is crossed. Keep
these structural headings and field labels in English; write ordinary prose in
the language selected during setup. Treat this log as unpublished research. -->

# Research run

## Problem Contract

- Contract version: `v1`
- Spine target reference: <stable ID; repository-relative project README path; current `HEAD` commit hash at SPEC start if `Exact target` matches it, otherwise `working snapshot Run-YYYYMMDD-NNN` using this run's actual ID; use `not applicable` for a new object>
- Exact target: <copy the exact current Spine wording when targeting an existing object; otherwise state the proposed target exactly>
- Objects and definitions:
- Hypotheses and quantifiers:
- Exceptional and boundary cases:
- Allowed sources and tools:
- Success criterion:
- Refutation criterion:
- Explicit exclusions:
- Ambiguities requiring researcher confirmation:

Do not continue past an ambiguity that would change the mathematical
statement. Do not leave SPEC until `Exact target`, `Success criterion`, and
`Refutation criterion` are explicit. Record every later contract change and
why it was made. This contract is authoritative only inside this run; the
project Research State Spine remains canonical. The Contract version tracks
run-local revisions. The exact wording in `Exact target` is the content anchor
for a working snapshot; never invent a separate Spine version number.

Only editorial Spine integration is automatic: copy a researcher-provided or
already-canonical new object without semantic change at the baseline states
`conjectural` or `open`, `unchecked`, and `isolated`, or update source,
dependency, or next-action metadata. Mark dependents `review-stale` only after
an upstream change is already canonical or is applied after Human Promotion;
keep the stale effects of a merely proposed upstream change in this run's
proposal. A new AI-authored formulation, a change to an existing statement's
hypotheses, quantifiers, or scope, a truth-bearing mathematical or gap-state change,
statement matching, closure, retirement, or a circulation-baseline decision
remains proposed until Human Promotion.

## Run manifest

`SPEC → ROUTE → OBLIGATIONS → PROVE / DISPROVE → optional adapters → SYNTHESIZE → HUMAN PROMOTION`

| Field | Value |
|---|---|
| Current stage | SPEC |
| Route | natural-proof / formalization / constructive-search / literature-audit / mixed |
| Started | YYYY-MM-DD |
| Last checkpoint | YYYY-MM-DD |
| Context policy | fresh isolation available / same-context only / not applicable |
| Execution mode | single-attempt / bounded-branch-loop / not used |
| Artifact root | repository-relative path / not used |
| Prompt contract version / artifact / SHA-256 | exact version, path, and `sha256:<64 lowercase hex>` / not used |
| Planned branch / depth / repair budgets | exact integer caps / not used |
| Planned token / tool / wall-time budgets | exact caps / not used |
| Stop policy | exact precommitted stop conditions / not used |
| Next bounded action |  |

The `run_id` date segment must equal the `date` above, the run's start date,
and the full ID must be unused elsewhere in this project.

## Route

| Adapter | Exact bounded scope | Obligations | Why this route |
|---|---|---|---|
|  |  |  |  |

Use one row per selected adapter. When frontmatter uses `adapter: mixed`, write
`adapter_scope` as semicolon-separated per-adapter entries, for example
`natural-proof: Obligation-001 direct proof; constructive-search:
Obligation-002 finite counterexample search`.

## Bounded branch plan

Use this optional harness only for named obligations that benefit from multiple
independent attempts, adversarial pressure, repair, or formalization. It is not
a generic swarm or a truth-producing stage. Freeze the allowed input bundle,
write scope, budgets, no-new-information threshold, and stop policy before
dispatch. Do not expand them silently.

Allowed roles are `idea-generator`, `solver`, `adversary`, `repairer`,
`formalizer`, `statement-matcher`, and `synthesizer`. A repair creates a child
branch and never overwrites its parent. Start each dispatch artifact from
`meta/templates/research-branch-prompt.md` and preserve both its frozen hash and
the final rendered-prompt hash.

## Branch ledger

| Branch | Parent | Obligation | Role | Attempt | State |
|---|---|---|---|---|---|
|  | root / Branch-NNN | Obligation-NNN | allowed role | Attempt-NNN / none | planned / running / candidate-produced / failed / stopped |

## Execution records

| Attempt | Branch | Provider, model, and version | Prompt artifact and SHA-256 | Rendered prompt SHA-256 | Context and input bundle with SHA-256 | Originating reasoning supplied | Parent or sibling reasoning supplied | Seed and sampling | Budget and usage | Stop reason | Output artifact and SHA-256 |
|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  | yes / no | yes / no | not exposed / exact values |  |  |  |

These records explain how a candidate was produced. They do not mean that the
candidate is correct. Use `fresh-isolated` only when both reasoning-supplied
fields are `no` and the input bundle excludes the originating, parent, and
sibling reasoning. A repair that receives a critique is not fresh. Record
unavailable model versions, seeds, sampling controls, or usage as `not
exposed`; do not guess.

## Automation signals

| Signal | Exact branch or artifact version | Basis | Closure effect |
|---|---|---|---|
|  |  |  | none |

Every automated signal has `Closure effect` equal to `none`. It may stop or
redirect search, but it cannot set an evidence descriptor, mathematical state,
statement match, gap closure, or Human Promotion.
Use only `candidate-green`, `branch-convergence`, `model-convergence`,
`two-of-three-agreement`, `adversary-conceded`, or `no-error-found` in the
`Signal` column.

## Obligations

| Obligation | Exact subclaim or test | Depends on | What would establish it | What would refute it | State |
|---|---|---|---|---|---|
| Obligation-001 |  |  |  |  | open |

Obligation IDs are local to this run. Use the project's stable IDs when an
obligation refers to an existing definition, claim, corollary, or gap.

## Attempt ledger

| Attempt | Date | Obligation | Direction | Branch | Context | Method or adapter | Result | Artifact, limits, or failure reason |
|---|---|---|---|---|---|---|---|---|
| Attempt-001 | YYYY-MM-DD | Obligation-001 | prove / disprove / check | Branch-NNN / none | fresh-isolated / same-context-audit / human / tool |  |  |  |

Call a pass `fresh-isolated` only when its associated Execution record has both
reasoning-supplied fields set to `no` and its worker received no originating,
parent, or sibling reasoning. Otherwise use `same-context-audit` or record that
a fresh pass was not run. Preserve failed attempts.

## Adapter and evidence records

| Descriptor | Exact scope | Input, artifact, or source | Result | Assumptions and limitations | Human or tool provenance |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

Enter exactly one descriptor per row. Descriptors are scoped, non-cumulative
provenance. None establishes truth or implies another descriptor. Record
`statement-matched` only after explicit dated human confirmation of the
correspondence and scope. Use only a reviewer identifier or role the user has
consented to record; omit unnecessary personal information.

## Formalization boundary

- Formalization manifest: not used
- Trusted challenge root: not used
- Untrusted submission root: not used
- Trust-boundary result: unchecked
- Formal-encoding record: unchecked

When formalization is attempted, copy
`meta/templates/formalization-manifest.json` into a repository-relative
artifact path and replace `not used` with the path and frozen roots. The
trusted challenge is verifier-side immutable input, not a claim of
mathematical truth. Solver-produced Lean is an untrusted submission and may
not modify the challenge, comparator, dependency lock, or allowed-axiom
policy. The manifest's `trusted_challenge.files` array must exhaustively list
every regular file under the trusted challenge root. Use only `unchecked`,
`recorded-pass`, `recorded-fail`, or `conflict` for the Formal-encoding record.
`recorded-pass` is self-recorded provenance, not proof that any command ran.
Use `recorded-fail` for a failed mandatory check or same-kernel clean rebuild;
reserve `conflict` for opposite pass/fail results from the primary kernel and
a genuinely independent checker.
The manifest validator checks structure and hashes but does not execute Lean,
the recorded build, Git checks, or any other command. Execute and observe the
actual mandatory commands separately before setting `recorded-pass` or
recording `formal-tool-checked` or `formal-encoding-checked`; link the durable
logs and validated manifest. A validator pass alone establishes neither formal
evidence descriptor. Statement correspondence remains a dated, scoped human
decision.

## Scoped synthesis

- Supported within the recorded scope:
- Refuted within the recorded scope:
- Conflicting findings:
- Open obligations and gaps:
- Proposed Research State Spine changes:
- Harness stop reason and branch / attempt IDs:
- Unavailable reproducibility metadata:
- Candidate automation signals (never closure):
- Not claimed:

## Human promotion

- Statement-match confirmation: not confirmed
- Statement-match scope:
- Statement-match confirmed by (consented identifier or role):
- Statement-match confirmation date:
- Proposed mathematical-state change:
- Closed-by-researcher confirmation: not confirmed
- Closed-by-researcher scope:
- Closed-by-researcher confirmed by (consented identifier or role):
- Closed-by-researcher confirmation date:
- Researcher decision and qualifications:

The circulation baseline is the exact artifact version the researcher
designates as ready to share outside the private working context. AI agreement,
a successful computation, a formal checker result, or a completed run never
performs this promotion automatically. Keep each
confirmation at `not confirmed` until a human explicitly supplies the dated,
scoped decision. These fields record that decision; they do not authenticate
the person's identity.

`candidate-green`, `branch-convergence`, `model-convergence`,
`two-of-three-agreement`, `adversary-conceded`, `no-error-found`, and a passing
Lean build are scoped candidate signals only. No combination of them performs
Human Promotion automatically.

## Resume point

- Current stage:
- Open obligations:
- Failed routes not to repeat:
- Evidence limitations:
- Next bounded action:

Before commit, sync, or push, verify an exactly private research destination
and obtain approval for the exact files. Before upload or external review,
follow the workspace's per-transmission disclosure and consent rules. Never
publish this log through the public Math Research Workbench distribution
remote.
