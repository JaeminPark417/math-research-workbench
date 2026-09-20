---
name: research-issues
description: Maintain local issue-based research records for explicitly enrolled projects or selected paper notes; preserve proof dependencies, counterexamples, source versions, priorities and resumable activities during requested research and manuscript work. Use when the user requests issue management or when continuing an enrolled project. Status inquiries only read; never enroll a project or start research automatically.
---

# Research issues

Use this skill for the requested project/paper scope, with the workspace's Python runtime and `scripts/research-tickets.py`. Resolve the actual store; a bare RES ID never selects a project. Do not install another tracker or ask the researcher to manage JSON.

## Load only the applicable contract

Read `meta/research-ticket-workflow.md` sections for the current action and the selected registration/coverage. A status query does not require `WRITE-API.md`; load its relevant sections before the first enrollment, mutation or recovery action. Read `PAPER-WORKFLOW.md` for argument/dependency mapping and manuscript issue maintenance, and `EXPERIMENTAL-WORKFLOW.md` for structured studies. Simple summaries, note edits and calculations need neither the full set of guides nor an operational session. Reuse current task context until scope or sources change.

## Restore and select

Enroll only when requested. Inventory the README, existing stable objects, active run, meaningful failed routes and remaining actions; use `--project projects/SLUG init` or `--paper papers/SLUG.md init` for that scope only. Start with partial coverage and preserve unindexed work. A status question or missing registration never authorizes enrollment. Do not create real tickets in the public distribution checkout.

On entry or resume, use `workflow start --limit 5` for an enrolled store. Inspect active/last work and partial coverage; use bounded `list`, `search`, `show` or `neighbors` queries as needed rather than reading the entire index. Respect warnings and pagination. Check the exact source of each claim/input relied on; hashes certify bytes, not proof, PDF fidelity, human identity or publication. A source check need not rescan unrelated evidence.

## Maintain requested work

Current operational actions within enrolled coverage live in tickets. The Spine holds canonical mathematics, strategy and unindexed work, and links to covered tickets. Without a covered ticket, an active run owns its bounded immediate next step and the Spine links to it; with no active run, the Spine holds the unindexed action list. Ordinary logs and session notes record dated results and refer to those current actions; do not maintain duplicate live checklists.

For an actual research activity, choose a relevant Ready/Todo item, record the reason, and begin or reuse an operational session. Do not bypass an active session, including one for another paper. Querying status, correcting a note or maintaining priorities does not itself start research. During authorized work, make routine local updates without repeated permission questions. Checkpoint meaningful findings, failed approaches, evidence and the next action; end completed/paused/blocked with the required evidence. A separate human-readable session note is for substantive work or decisions, not every record edit.

Use the transactional writer with exact generation, issue and session versions. Preserve the identical packet/operation ID on uncertain retries; inspect conflicts before a new intent. Only activities can be Done or be operational blockers. Priority changes retain a rationale. Conditional follow-ups remain Backlog until a recorded decision activates them. `parent` organizes; research relations neither prove claims nor unlock work automatically.

Bind existing Spine objects with stable IDs and exact sources. New AI formulations remain proposed; use append-only `propose` for bound mathematical changes, never overwrite their statements or redirect their identities. Work completion, review completion and HUMAN PROMOTION are distinct. Load `meta/math-workflow.md` or `$math-research-run` only for the corresponding mathematical action; a ticket session does not require a new persistent run.

For paper/manuscript mapping, reuse shared lemmas and preserve earlier review/source versions. Repeated `--tag` filters combine with AND. For structured studies, preserve the design, negative/null/invalid observations, scoped interpretation and decision; an experiment record is not an executable activity. No server or training stack is supplied.

## Recovery and external boundaries

On interruption, inspect `recover status` and its hashes. Preserve external edits; never remove live locks, journals, receipts or runs to force a write. Enrollment and local upkeep do not authorize background research, sync, publication or outside transmission. Keep the public template's exactly-private research-backup checks and fresh per-transmission consent for external reviewers or browser actions. Infrastructure tests never create real research sessions.
