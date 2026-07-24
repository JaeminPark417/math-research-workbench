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

## Obligations

| Obligation | Exact subclaim or test | Depends on | What would establish it | What would refute it | State |
|---|---|---|---|---|---|
| Obligation-001 |  |  |  |  | open |

Obligation IDs are local to this run. Use the project's stable IDs when an
obligation refers to an existing definition, claim, corollary, or gap.

## Attempt ledger

| Attempt | Date | Obligation | Direction | Context | Method or adapter | Result | Artifact, limits, or failure reason |
|---|---|---|---|---|---|---|---|
| Attempt-001 | YYYY-MM-DD | Obligation-001 | prove / disprove / check | fresh-isolated / same-context-audit / human / tool |  |  |  |

Call a pass `fresh-isolated` only when its worker did not receive the
originating reasoning. Otherwise use `same-context-audit` or record that a
fresh pass was not run. Preserve failed attempts.

## Adapter and evidence records

| Descriptor | Exact scope | Input, artifact, or source | Result | Assumptions and limitations | Human or tool provenance |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

Enter exactly one descriptor per row. Descriptors are scoped, non-cumulative
provenance. None establishes truth or implies another descriptor. Record
`statement-matched` only after explicit dated human confirmation of the
correspondence and scope. Use only a reviewer identifier or role the user has
consented to record; omit unnecessary personal information.

## Scoped synthesis

- Supported within the recorded scope:
- Refuted within the recorded scope:
- Conflicting findings:
- Open obligations and gaps:
- Proposed Research State Spine changes:
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
