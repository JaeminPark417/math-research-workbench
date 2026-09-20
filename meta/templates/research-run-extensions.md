<!-- Append these five sections together only for actual bounded dispatch,
isolation claims, or formalization. They preserve the existing execution
schema. Unused branch tables remain empty; unused formalization is not used.
Read the applicable section of meta/math-details.md before execution. -->

## Bounded branch plan

- Execution mode: not used
- Artifact root: repository-relative path / not used
- Exact contract version and obligation:
- Allowed input artifacts and SHA-256:
- Forbidden inputs and allowed write scope:
- Planned branch / depth / repair budgets: exact integer caps / not used
- Planned token / tool / wall-time budgets: exact caps / not used
- No-new-information threshold and stop policy:

Valid execution modes are `single-attempt`, `bounded-branch-loop`, and `not used`. Keep `not used` for an unused branch extension, including formalization without dispatch. Use `meta/templates/research-branch-prompt.md` for an actual dispatch. Preserve the frozen prompt-artifact hash and the final rendered-prompt hash. Repair creates a child branch and preserves its parent output. Do not expand agreed budgets silently. Formalization without branch dispatch leaves the branch-specific fields `not used` and the tables below empty.

## Branch ledger

| Branch | Parent | Obligation | Role | Attempt | State |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Execution records

| Attempt | Branch | Provider, model, and version | Prompt artifact and SHA-256 | Rendered prompt SHA-256 | Context and input bundle with SHA-256 | Originating reasoning supplied | Parent or sibling reasoning supplied | Seed and sampling | Budget and usage | Stop reason | Output artifact and SHA-256 |
|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |  |  |

Every executed branch connects to its Attempt ledger row. Record unavailable provider versions, seeds, sampling controls, or usage as `not exposed`, never invented values.

`fresh-isolated` is blind search: both reasoning-supplied fields must be `no`, with no candidate proof or originating, parent, or sibling reasoning supplied.

`independent-proof-audit` requires Originating reasoning supplied `yes` and Parent or sibling reasoning supplied `no`. Its approved proof package is the exact frozen target, complete candidate proof, and explicitly named dependency artifacts. Record every actual supplied path and SHA-256 in the input bundle; this package counts as originating reasoning even when an earlier branch produced it. Receiving that proof is necessary for an audit and must not be hidden to claim freshness.

Parent or sibling reasoning means other attempts, critiques, or prior reviewer verdicts beyond that package. Supply any of those, or the originating conversation, and use `same-context-audit` with honest exposure fields. Do not relabel prior evaluations as dependency artifacts. If isolation or the actual input scope is unverified, do not claim an independent audit.

## Automation signals

| Signal | Exact branch or artifact version | Basis | Closure effect |
|---|---|---|---|
|  |  |  |  |

Only `candidate-green`, `branch-convergence`, `model-convergence`, `two-of-three-agreement`, `adversary-conceded`, and `no-error-found` are allowed signals; every closure effect is `none`. Signals can stop or redirect search. They never set an evidence descriptor, mathematical state, statement match, gap closure, or Human Promotion.

## Formalization boundary

- Formalization manifest: not used
- Trusted challenge root: not used
- Untrusted submission root: not used
- Trust-boundary result: unchecked
- Formal-encoding record: unchecked

For actual formalization, copy `meta/templates/formalization-manifest.json` to the run's repository-relative artifact path and record it here. Follow **Formalization trust boundary** in `meta/math-details.md`: immutable trusted challenge, disjoint untrusted submission, `solution-only` write scope, exhaustive trusted file inventory, actual observed checker commands, durable logs and hashes, and separately confirmed intended-statement correspondence. The manifest validator executes no commands; its pass alone establishes neither `formal-tool-checked` nor `formal-encoding-checked`.
