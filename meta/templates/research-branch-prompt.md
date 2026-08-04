# Bounded research branch prompt

<!-- Copy this file into the run's private artifact root, fill every required
field, hash that frozen artifact, then render the final provider-specific
prompt and hash the rendered bytes separately. Do not put secrets or
unapproved research in an outbound prompt. -->

## Execution identity

- Run ID: `Run-YYYYMMDD-NNN`
- Problem Contract version / artifact / SHA-256:
- Obligation: `Obligation-NNN`
- Branch / parent: `Branch-NNN` / root or `Branch-NNN`
- Attempt: `Attempt-NNN`
- Role: idea-generator / solver / adversary / repairer / formalizer / statement-matcher / synthesizer
- Allowed write root:

## Exact task

Paste the exact obligation and its establishment and refutation criteria. Do
not strengthen, weaken, or silently reinterpret it.

## Allowed input bundle

| Artifact | SHA-256 | Why it is permitted |
|---|---|---|
| repository-relative path | `sha256:<64 lowercase hex>` |  |

Anything not listed here is unavailable to this branch.

## Context declaration

- Originating reasoning supplied: yes / no
- Parent or sibling reasoning supplied: yes / no
- Claimed context: fresh-isolated / same-context-audit / human / tool

Use `fresh-isolated` only when both reasoning fields are `no` and the bundle
contains only the Problem Contract, exact obligation, and explicitly permitted
artifacts. A repairer that receives a critique is not fresh.

## Budget and stop policy

- Token budget:
- Tool-call budget:
- Wall-time budget:
- Stop immediately on: candidate produced / counterexample produced / budget exhausted / repeated failure / contract ambiguity / tool error / safety or consent boundary / human stop
- No-new-information threshold:

Do not request or consume a larger budget without returning to the
orchestrator.

## Role contract

Apply exactly one contract:

- `idea-generator`: return distinct routes, assumptions, a first obligation,
  and a kill-test for each route. Do not claim proof or closure.
- `solver`: attempt this exact obligation, expose every used assumption and
  dependency, and identify any remaining gap. Do not change the target.
- `adversary`: seek a concrete counterexample, missing assumption, or invalid
  inference and give a scoped verdict. Failure to find one is not correctness.
- `repairer`: make the smallest delta for the named defect, identify new
  dependencies and remaining risks, and preserve the parent artifact. Do not
  claim independence.
- `formalizer`: produce only an untrusted Lean submission and a statement
  mapping report under the allowed solution write root. Do not alter the
  trusted challenge, comparator, test, lockfile, or axiom policy. Do not set a
  final formal-encoding record or claim a formal evidence descriptor.
- `statement-matcher`: report exact correspondences, differences, and
  uncertainty between informal and formal statements. Do not set
  `statement-matched` or authenticate a human.
- `synthesizer`: reconcile cited attempts obligation by obligation and preserve
  contradictions and gaps. Put any new truth-bearing step in a separate
  `UNVERIFIED` attempt; do not perform closure or state promotion.

## Required return

Return these exact fields before any supporting detail:

- Attempt:
- Branch:
- Role:
- Exact obligation restated:
- Result: candidate-produced / counterexample-produced / failed / inconclusive
- Assumptions and dependencies used:
- Strongest disconfirming pressure:
- Remaining gaps:
- Stop reason:
- Output artifacts and SHA-256:
- Not claimed:

If a signal is returned, use only `candidate-green`, `branch-convergence`,
`model-convergence`, `two-of-three-agreement`, `adversary-conceded`, or
`no-error-found`. AI agreement and tool passes are scoped execution signals
only. They never prove the theorem, set an evidence descriptor, confirm
statement correspondence, close a gap, or perform Human Promotion.
