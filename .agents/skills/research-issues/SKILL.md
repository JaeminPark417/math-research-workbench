---
name: research-issues
description: Maintain local issue-based research records for explicitly enrolled projects or selected paper notes; preserve proof dependencies, counterexamples, source versions, priorities and resumable activities during requested research and manuscript work. Use when the user requests issue management or when continuing an enrolled project. Status inquiries only read; never enroll a project or start research automatically.
---

# Research issues

Read `meta/research-ticket-workflow.md` and `meta/research-tickets/WRITE-API.md`. Use the workspace's Python runtime and `scripts/research-tickets.py`; do not install an external tracker or require the researcher to manage JSON. Resolve the actual project directory or paper note before any query. A bare RES ID is never a store selector.

For an explicitly requested enrollment, inventory the README, current stable objects, active math run, failed routes and next steps; call `--project projects/SLUG init` or `--paper papers/SLUG.md init`, then integrate only the requested scope with stable creation keys. Start with partial coverage and retain unindexed work. Do not initialize because of a status question, routine summary or missing registration. Do not create real tickets in the public distribution checkout.

For registered projects use `workflow start --limit 5`. Read active/last session, partial coverage and untracked work before selecting a candidate. Use `list`, `search`, `show` and `neighbors` to retrieve bounded relevant sections; never load the full index into context. Inspect warnings, scope completeness and pagination. Source-check every relevant claim/input before trusting its evidence, including remaining pages and claims outside the candidate list. Source hashes certify bytes, not proof, PDF fidelity, human identity or remote publication.

During requested research choose one Ready/Todo activity, record the reason and begin an operational session. Checkpoint meaningful findings, failed approaches, exact refutation scope and next action. End completed/paused/blocked with evidence as required. Maintain `math_run` when the existing `$math-research-run` threshold is crossed: a short ticket session and a persistent mathematical run are different records. Infrastructure tests never create real research sessions.

Use the transactional writer with exact generation, issue and session versions. Preserve the identical packet/operation ID on uncertain retries; conflicts require inspection and a new intent. Only activities can be Done or be operational blockers. Priority changes require a rationale. Keep conditional follow-ups Backlog until an explicit decision activates them. `parent` organizes; scoped research relations neither prove claims nor unlock work automatically.

Bind existing Spine objects with their stable IDs and exact sources. New AI formulations remain proposed. Use append-only `propose` for bound mathematical changes, never overwrite their statement or redirect their identity. Work completion, review completion and HUMAN PROMOTION remain distinct. Follow `meta/math-workflow.md` and `$math-research-run` for all truth-bearing changes.

For selected paper reading or manuscript writing/review, also read `meta/research-tickets/PAPER-WORKFLOW.md`. Apply it from the first argument outline through proof development and revisions. Reuse shared lemmas and project claim IDs. Preserve earlier review records and source versions; new rounds get new analysis/activity records. Repeated `--tag` filters combine with AND, while global active/last sessions remain visible: do not bypass an active session for another paper.

For computational or experimental questions read `meta/research-tickets/EXPERIMENTAL-WORKFLOW.md`. Record the design, observed result (including negative/null/invalid), scoped interpretation and resulting decision. An experiment record is not a runnable activity. No server, training stack or remote execution is supplied by this skill.

On interrupted transactions, use inspected `recover status` hashes; preserve external edits and never remove live locks, pending journals, receipts or runs to bypass an error. Follow the workspace's existing per-transmission approval and private-backup rules for any external review, sync or push. Enrollment and local ticket upkeep do not authorize outside transmission or background research.
