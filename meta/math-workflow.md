# Mathematical research workflow

This workflow turns a rough thought into inspectable mathematical work without
pretending that an AI assistant is a mathematical authority. The researcher
may enter at any step.

## 1. Capture

Put an unstructured thought, question, URL, or reference to a scan in `inbox/`.
Codex should first preserve what the user supplied, then ask only the questions
needed to understand the intended task.

Output: an `inbox` note, unless the user is already working inside an existing
idea or project.

## 2. Triage

Codex proposes one of these destinations and explains it in plain language:

- `ideas/` for a question or conjectural direction;
- `papers/` for a source being read;
- `projects/` for sustained work with a defined research question;
- `notes/` for reusable background material that is not tied to one project.

After the durable note exists and its links have been checked, move the raw
inbox item to `inbox/archive/`. Do not delete it.

## 3. Formulate the question

For an idea, write down:

1. the objects and notation;
2. the exact question or claim;
3. hypotheses and quantifiers;
4. basic examples and edge cases;
5. known obstacles;
6. what would count as progress.

Label conjectures and uncertain steps. Codex must not fill a missing assumption
or reference from memory without marking it as uncertain.

## 4. Check the literature

Search using several formulations of the question. For each potentially
relevant source:

1. verify bibliographic facts against an authoritative record;
2. create or update a `paper` note;
3. distinguish the source's claims from the researcher's interpretation;
4. record the exact theorem, definition, or page relevant to the project;
5. link the paper note to the idea or project.

An unverified lead may be retained, but it must remain visibly unverified.

## 5. Open a project

Create a project when the question needs sustained work. Start from
`meta/templates/project.md` and create this simple structure:

```text
projects/project-slug/
├── README.md
├── sessions/
├── logs/
└── drafts/
```

The project `README.md` contains the Research State Spine: the clean current map of the research question, paper-relevant definitions and claims, logical dependencies, open gaps, important links, and next actions. Use the stable IDs and separate state axes defined in `meta/schemas.md`. Codex maintains this map during ordinary conversation; the researcher does not need to edit Markdown tables by hand.

Record only stable objects that affect a paper or a major research decision in the Spine. Editorial integration may add a new object copied without semantic change from a researcher-provided or already-canonical source at baseline state (`conjectural` for claims, `open` for gaps, `unchecked` review, and `isolated` integration), or update source/dependency/next-action metadata. Mark dependents `review-stale` only after an upstream change is already canonical or is applied after Human Promotion; keep the stale effects of a merely proposed upstream change in the run's proposal. A new AI-authored formulation, a change to an existing statement's hypotheses, quantifiers, or scope, a truth-bearing mathematical or gap-state change, statement matching, closure, retirement, or a circulation-baseline decision remains proposed until Human Promotion. Keep exploratory calculations, mixed notes, and failed routes in `logs/` or `drafts`, with links from the Spine when they become relevant.

## 6. Use a bounded research run for sustained work

Invoke `$math-research-run` implicitly when the work reaches a second serious
attempt, resumes in a later session, needs multiple obligations or scoped
adapters, or concerns a load-bearing paper claim. Let the researcher continue
in ordinary conversation while Codex maintains a dated `research-log` from
`meta/templates/research-run.md`. If the threshold is uncertain, use an
ordinary research log until one of these conditions is met. Do not create a run
for a simple question, routine explanation, lightweight exposition, or
one-step calculation.

Use this control loop:

`SPEC → ROUTE → OBLIGATIONS → PROVE / DISPROVE → optional adapters → SYNTHESIZE → HUMAN PROMOTION`

1. **SPEC:** fix a versioned Problem Contract with the exact target, objects,
   hypotheses, quantifiers, boundary cases, success and refutation criteria,
   allowed sources or tools, and exclusions. Ask the researcher about any
   ambiguity that would change the statement. Preserve the template's English
   headings and field labels, and do not leave SPEC until `Exact target`,
   `Success criterion`, and `Refutation criterion` are explicit.
   The Problem Contract is authoritative only within that run. The project
   README Research State Spine remains canonical. Put an existing target's
   stable ID and repository-relative project README path in the
   `Spine target reference` field. If its exact wording matches the current `HEAD` at the start of
   SPEC, record that commit hash; otherwise use `working snapshot
   Run-YYYYMMDD-NNN`, replacing the placeholder with the run's actual ID. In
   every case, copy the current Spine wording into `Exact target`; that text is
   the working snapshot's content anchor. The Contract version tracks run-local
   revisions; never invent a separate Spine version number. Apply only the
   editorial changes defined above and keep all other changes proposed until
   Human Promotion.
2. **ROUTE:** choose natural proof development, formal encoding, constructive
   or computational evaluation, literature-sensitive comparison, or a scoped
   combination. The route selects methods, not truth. Record one row per
   adapter in the body Route table. For `mixed`, use semicolon-separated
   per-adapter scopes in `adapter_scope`.
3. **OBLIGATIONS:** split the target into exact subclaims or tests, recording
   dependencies and both establishment and refutation criteria.
4. **PROVE / DISPROVE:** preserve constructive attempts and adversarial failure
   searches. Call a pass fresh only when the worker is genuinely isolated from
   the originating reasoning and receives only the Problem Contract, exact
   obligation, and permitted artifacts. Otherwise record `same-context audit`
   or `fresh pass not run`.
5. **Optional adapters:** use computation, a formal checker, or literature
   search only for a named obligation. Record exact input or encoded statement,
   version, source or artifact, result, assumptions, and limitations. Follow
   the workspace's approval and privacy rules for every external action.
6. **SYNTHESIZE:** reconcile attempts and contradictions obligation by
   obligation. State what is supported or refuted within scope, what remains
   open, and what is not claimed.
7. **HUMAN PROMOTION:** propose stable Research State Spine changes, but never
   promote AI agreement or a tool result into truth. Leave the template's
   stable confirmation fields at `not confirmed` until a human makes a dated,
   scoped decision. Record `statement-matched` only after explicit dated human
   confirmation that the checked statement matches the intended mathematics.
   A circulation baseline is the exact artifact version the researcher
   designates as ready to share outside the private working context.
   Set `closed-by-researcher` only with dated, scoped researcher provenance and
   linked evidence. Use only a user-consented reviewer identifier or role and
   avoid unnecessary personal information. Automation records these fields; it
   cannot authenticate a person's identity.

Evidence descriptors such as `computationally-checked`,
`formal-encoding-checked`, `statement-matched`,
`literature-audited-within-scope`, and `expert-reviewed` are scoped,
non-cumulative provenance. One does not imply another, and none is a
mathematical state. A completed research run means only that the logged
activity ended. Put only one evidence descriptor in each table row.

Do not require a generic swarm, daemon, model API, or specialized solver. Use
available agents and tools only when they help a bounded obligation. Keep
ordinary stage transitions quiet; interrupt when the Problem Contract is
ambiguous, an external action requires approval, attempts conflict, statement
matching is uncertain, or human promotion is ready.

### Optional bounded proof-search harness

A bounded proof-search harness is an optional execution method inside PROVE /
DISPROVE, not a new truth-producing stage. Use it only for a named obligation
that benefits from multiple independent attempts, adversarial pressure,
repair, or formalization. Before dispatch, freeze the exact obligation,
permitted input bundle and hashes, write scope, maximum branches and repair
depth, token/tool/time budgets, no-new-information threshold, and stop policy.
Never expand the search budget silently.

Give every branch a `Branch-NNN` ID and connect every execution to an existing
`Attempt-NNN`. A retry or repair creates a child branch and preserves its
parent output. Record branch parentage, provider/model/version, prompt artifact
and rendered-prompt hashes, input artifacts and hashes, context policy, seed
and sampling controls or `not exposed`, planned budget and observed use, stop
reason, and output artifact and hash. Record `Originating reasoning supplied`
and `Parent or sibling reasoning supplied` as separate `yes` or `no` fields.

Parentage records genealogy, not context exposure. Use `fresh-isolated` only
when both reasoning-supplied fields are `no`, the actual input bundle excludes
the originating, parent, and sibling reasoning, and the bundle contains only
the Problem Contract, exact obligation, and explicitly permitted artifacts. A
repair that receives a critique is a same-context audit. A root branch is not
automatically fresh, and a child is not automatically non-fresh.

Every execution prompt uses a common envelope: the exact contract and
obligation, allowed and forbidden inputs, write scope, one role objective,
required return shape, budget and stop conditions, and the boundary that AI
agreement or a tool pass is not proof or promotion. Copy
`meta/templates/research-branch-prompt.md` for the durable prompt artifact and
use these role contracts:

| Role | Required work | Must not do |
|---|---|---|
| `idea-generator` | propose distinct routes, assumptions, first obligations, and kill-tests | claim proof or closure |
| `solver` | attempt one exact obligation and expose dependencies and gaps | change the target or hide assumptions |
| `adversary` | seek counterexamples, missing assumptions, and invalid inferences | infer correctness merely because the attack failed |
| `repairer` | make the smallest tracked repair to a named defect | overwrite the parent or claim independence |
| `formalizer` | produce an untrusted Lean candidate for the frozen target | modify the trusted challenge, evaluator, or lockfile |
| `statement-matcher` | report differences and uncertainties between informal and formal statements | set `statement-matched` or authenticate a reviewer |
| `synthesizer` | reconcile attempts and preserve conflicts and gaps | add hidden proof steps or promote mathematical state |

Signals such as `candidate-green`, `branch-convergence`, `model-convergence`,
`two-of-three-agreement`, `adversary-conceded`, and `no-error-found` may stop
or redirect the search. They are branch-scoped routing signals, not evidence
descriptors, proof, statement matching, gap closure, or Human Promotion.

Treat the run log as unpublished research. Before any commit, sync, or push,
obtain approval for the exact files and verify that the research destination is
exactly private. Uploads and external reviews follow the separate
per-transmission disclosure and consent rules. Never send a run log to the
public Math Research Workbench distribution remote.

## 7. Develop an argument

Record substantial derivations and searches as dated `research-log` notes.
Each log should include the exact question, assumptions, work performed,
negative results, unresolved gaps, and a scoped conclusion.

Useful checks include:

- testing boundary and degenerate cases;
- tracing where each hypothesis is used;
- searching for counterexamples;
- checking consistency of notation and dependencies;
- comparing the proposed statement with nearby results in verified sources;
- using symbolic or finite-case calculations as limited evidence.

Do not erase a failed route. Mark why it failed and link it from the project
map if it is likely to recur.

When a log changes a stable definition, lemma, proposition, theorem, corollary, or gap, update the corresponding `Def-NNN`, `Lem-NNN`, `Prop-NNN`, `Thm-NNN`, `Cor-NNN`, or `Gap-NNN` entry in the project README. Record dependencies rather than repeating detailed proofs in the table. If an upstream statement changes, mark downstream integration states `review-stale` until they are rechecked.

## 8. Audit a proof

Use `meta/templates/proof-audit.md` for any important proof or suspected gap.
The audit should decompose the argument into claims and justifications, identify
hidden assumptions, inspect edge cases, and keep a gap register.

AI review can find problems or suggest repairs, but it cannot close a gap by
itself. A gap is closed only when the researcher accepts a complete argument or
when a correctly scoped formal check and human interpretation are both
documented.

## 9. Use formal tools when useful

Formalization is optional and should target a clearly stated lemma or finite
subproblem. Record:

- the exact encoded statement;
- definitions and imported assumptions;
- tool and version;
- the checked source file or durable reference;
- the checker result;
- a human assessment of whether the encoding matches the intended mathematics.

A successful checker result applies only to the encoding. It does not validate
the choice of definitions, the translation of the informal theorem, or the
relevance of the assumptions.

### Formalization trust boundary

Freeze a trusted challenge before solver execution. Here, trusted means
verifier-side immutable input; it does not mean that the statement is
mathematically true. The challenge pins the natural statement and hash,
definitions and assumptions, expected Lean declaration or elaborated type,
allowed imports and axioms, toolchain and dependency lock, build/test argv,
and challenge file/tree hashes.

The schema-v1 challenge tree uses `sha256-v1`: sort each listed trusted file by
repository-relative path, encode `path`, NUL, `sha256:<digest>`, and LF as
UTF-8 records, concatenate them, and hash the resulting bytes with SHA-256.
The `trusted_challenge.files` array is the exhaustive inventory of every
regular file under `trusted_challenge.root`, including the expected-type and
dependency-lock artifacts when they are stored there. An unlisted regular file
under that root invalidates the recorded trust boundary.

Treat every solver-produced Lean file as an untrusted submission in a separate
write root. It must not modify the challenge, comparator, dependency lock, or
allowed-axiom policy. Preserve a machine-readable manifest copied from
`meta/templates/formalization-manifest.json`. Use only `unchecked`,
`recorded-pass`, `recorded-fail`, or `conflict` for
`final_record.formal_encoding`. A `recorded-pass` entry requires recorded
unchanged challenge hashes, disjoint trusted and untrusted paths, a clean
pinned repository snapshot, passing source-policy, build, declaration-type,
allowed-axiom, and primary-kernel checks, plus durable logs and hashes. It is
self-recorded provenance, not an execution attestation. Record `#print axioms`
output. A same-kernel clean rebuild is useful but is not an independent
checker. Use `recorded-fail` for a failed mandatory check or same-kernel clean
rebuild. Reserve `conflict` for opposite pass/fail results from the primary
kernel and a genuinely independent checker.

Run `python3 scripts/formalization_manifest.py MANIFEST --root . --verify-files`
from the repository root to check the recorded boundary and artifact hashes.
The validator never executes Lean, `build.argv`, Git checks, or any other
recorded command. Execute and observe the mandatory commands separately before
setting `recorded-pass` or recording formal evidence. A passing validator alone
does not establish `formal-tool-checked` or `formal-encoding-checked`; those may
be recorded only after the actual tool commands have run, their results have
been observed, and durable logs and the validated manifest are linked. The
intended-statement correspondence still needs the existing dated, scoped human
confirmation.

## 10. End a session cleanly

Create a `session` note that records:

- the session goal;
- what was actually done;
- decisions and their reasons;
- unresolved questions;
- the next small, concrete action;
- notes created or updated.

Then reconcile the project `README.md` with the new logs: add or update stable IDs, dependencies, mathematical state, review provenance, integration state, open gaps, and the next action. Do not renumber existing IDs or infer that a claim became true because an AI review found no problem. Archive source material; do not permanently delete it.

## 11. Promote durable knowledge

When a definition, lemma, example, or explanation becomes reusable across
projects, synthesize it in `notes/`. A concept note may be plain Markdown and
should link back to the project logs and verified sources from which it arose.
Do not remove the underlying provenance.

## How Codex should interact with beginners

- Use ordinary language before specialized tool terminology.
- Propose one clear next action at a time.
- Explain what a command or file change will do before requesting approval.
- Never assume that the user knows Git, terminals, YAML, or folder conventions.
- When something fails, state what remains safe, what was not changed, and the
  simplest recovery step.
