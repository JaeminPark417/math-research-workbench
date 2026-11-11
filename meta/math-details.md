# Optional mathematical execution detail

Read only the section needed for actual dispatch or formalization. Ordinary mathematical work uses the compact run template. Follow the active workflow for the project's canonical source, permitted execution, storage and external transmission. The researcher retains Human Promotion authority.

## Bounded dispatch

Use the optional bounded proof-search harness for a named obligation that benefits from several attempts, adversarial pressure, repair, or an independent proof audit. It is an execution method, not another truth-producing stage. Append `meta/templates/research-run-extensions.md` to the existing run; do not create another live research record.

Before dispatch, freeze the Problem Contract version and exact obligation, permitted input artifacts with SHA-256, forbidden inputs, and allowed write scope. Set branch/depth/repair caps and token/tool/time budgets appropriate to the task, plus a no-new-information threshold and stop policy. Do not silently expand the agreed scope or budget. Follow the workspace's consent rules for any new provider or external transmission.

Each dispatched `Branch-NNN` links to an `Attempt-NNN` and exact obligation. A retry or repair creates a child and preserves the parent output. Use `meta/templates/research-branch-prompt.md` for the role contract and required return. Its roles are `idea-generator`, `solver`, `adversary`, `repairer`, `formalizer`, `statement-matcher`, and `synthesizer`; choose one role instead of requiring all of them. A synthesizer reconciles cited attempts and cannot hide a new proof step or promote state. A statement-matcher reports discrepancies but cannot assert human correspondence. A formalizer writes only an untrusted candidate in its solution root.

Record provider/model/version, the frozen prompt artifact and SHA-256, the separately hashed final rendered prompt, input hashes, context, observed budget/usage, stop reason, and preserved output/hash. Use `not exposed` when a provider does not reveal version, seed, sampling controls, or usage. Do not guess. A produced candidate needs its actual artifact hash; an output not produced is `not-produced` with its failure or stop reason.

### Context and audit independence

Branch parentage records genealogy, not independence. Use these labels according to actual inputs:

- `fresh-isolated`: a blind search receiving only the exact target/obligation and permitted sources, with no originating, parent, or sibling reasoning. Both reasoning-supplied fields must be `no`. A solver independently rediscovering an argument did not audit the original proof.
- `independent-proof-audit`: a reviewer isolated from the prior conversation receives an approved proof package: the exact frozen target, complete candidate proof, and explicitly named dependency artifacts. This package counts as originating reasoning: require `Originating reasoning supplied: yes` and `Parent or sibling reasoning supplied: no`. Record the actual supplied artifacts and each SHA-256, not merely the intended inputs. Check the candidate's inference chain, including joins between components, rather than producing another proof and calling agreement verification.
- `same-context-audit`: the reviewer has the originating conversation, other attempts, critiques, or prior reviewer verdicts beyond the approved proof package, or isolation cannot be established. A repairer receiving a critique uses this label. State any missing independent audit rather than substituting a persona or new model name.

For these fields, parent or sibling reasoning means other attempt reasoning, critiques, and prior reviewer verdicts beyond that exact frozen proof package. The candidate and its named mathematical dependencies are the package being audited, even if produced by an earlier branch; they are recorded as originating reasoning, not hidden as absent inputs. Do not relabel conversation or prior evaluations as dependencies to preserve an independence claim. Exposure to that additional material requires `Parent or sibling reasoning supplied: yes` and `same-context-audit`. Blind `fresh-isolated` search still requires both reasoning-supplied fields to be `no`; it cannot receive the candidate proof package.
- `human` and `tool`: identify actual human or tool work with its scoped provenance.

An independent context is a provenance claim to justify, not a proof status. Record unresolved gaps, counterexamples, conflicts, and limitations. Model agreement, `candidate-green`, `branch-convergence`, `model-convergence`, `two-of-three-agreement`, `adversary-conceded`, and `no-error-found` are routing/stop signals only. Their closure effect is always `none`; no combination performs Human Promotion.

## Formalization trust boundary

Formalization is optional. Choose a named obligation and preserve the exact encoded statement, definitions, imported assumptions, tool versions, artifacts, actual checks, and limitations. A checker accepts an encoding; it does not establish that the encoding expresses the intended theorem.

Before solver execution, copy `meta/templates/formalization-manifest.json` to a repository-relative artifact path and append the execution extension to the run. Replace all example paths with paths relative to the repository containing the evidence. In `spine_target.project_readme`, use the actual project overview or canonical claim-ledger path. Export the exact target verbatim as the `natural_statement` artifact; its SHA-256 must equal `exact_target_sha256`. Freeze a trusted challenge containing that statement, the expected Lean declaration/elaborated type, definitions, assumptions, allowed imports/axioms, toolchain, dependency lock, build/test argv, and file/tree hashes. Here trusted means verifier-side immutable input, not mathematical truth.

The schema-v1 `trusted_challenge.files` array exhaustively lists every regular file under `trusted_challenge.root` exactly once, including expected-type and lock artifacts stored there. An unlisted regular file invalidates the recorded boundary. The `sha256-v1` tree hash is SHA-256 of sorted UTF-8 records consisting of repository-relative path, NUL, `sha256:<digest>`, and LF.

Keep solver-produced Lean in a disjoint untrusted submission root. The solver write scope is `solution-only`; changes to the challenge, comparator, dependency lock, test, or axiom policy invalidate the attempt. A repair preserves its failed parent and gets a new candidate version.

Execute and observe the mandatory source-policy, pinned clean repository-state, build, declaration-type comparator, allowed-axiom, and primary-kernel checks separately. Preserve exact argv, exit status, logs and hashes, including `#print axioms` output, challenge before/after hashes, and any secondary check. A same-kernel clean rebuild is not an independent checker.

Use only `unchecked`, `recorded-pass`, `recorded-fail`, or `conflict` for `final_record.formal_encoding`. `recorded-pass` is self-recorded provenance, not an execution attestation. A failed mandatory check or same-kernel clean rebuild requires `recorded-fail`; reserve `conflict` for opposite pass/fail results from the primary kernel and a genuinely independent checker.

After actual commands run, use the active workflow's `math_run_checks.py --root REPO --run RELPATH` command to check the run and its linked manifest. To inspect a manifest separately, invoke the sibling `formalization_manifest.py MANIFEST --root REPO --verify-files` with the same research repository root.

The validator does not execute Lean, `build.argv`, Git checks, or another recorded command; it does not enforce an OS sandbox, authenticate a human, establish statement correspondence, or certify mathematical truth. A passing manifest alone establishes neither `formal-tool-checked` nor `formal-encoding-checked`. Record formal evidence only after actual command execution was observed and its durable logs and validated manifest are linked.

Intended-statement correspondence still requires explicit dated, scoped human confirmation. Only then can `statement-matched` be recorded. Closure and a circulation baseline remain separate researcher decisions. Never infer them from a formal tool result.
