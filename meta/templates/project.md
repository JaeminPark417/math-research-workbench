---
type: project
title: "Project title"
status: planning
created: YYYY-MM-DD
updated: YYYY-MM-DD
language: en
research_question: ""
related_ideas: []
related_papers: []
---

<!-- Save this file as projects/project-slug/README.md. Use the language selected during setup for prose and ordinary headings. Keep the Research State Spine structural headings and table headers exactly as written in English so cross-project search and lint remain reliable. Codex maintains these tables for the user. -->

# Research question

State one primary question precisely enough that progress can be assessed.

## Scope

### Included

- TODO

### Not included

- TODO

## Definitions and notation

- TODO

## Current state

Write a short, dated summary. Separate established facts from conjectures and open gaps.

## Research State Spine

This is the clean current map for claims and gaps that may affect a paper or a major research decision. Keep exploratory calculations, mixed notes, and failed routes in `logs/` or `drafts`; link them here only when they become relevant to the current route. You may continue speaking to Codex naturally: Codex should maintain this map while preserving the detailed source notes.

Use stable, explicit IDs: `Def-001`, `Lem-001`, `Prop-001`, `Thm-001`, `Cor-001`, and `Gap-001`. Do not shorten them to single letters, do not renumber them when rows move, and do not reuse an ID after an item is retired. Give a corollary its own `Cor-NNN` ID only when it is a stable downstream consequence that should be rechecked after an upstream statement changes.

### Current research state

| Item | Current value |
|---|---|
| Active route or focus | TODO |
| Blocking gaps | None recorded yet |
| Immediate next action | TODO |

### Definition registry

| ID | Definition or notation | Exact formulation or source | Notes |
|---|---|---|---|
| Def-001 | TODO |  |  |

### Claim ledger

| ID | Claim | Mathematical state | Depends on | Evidence or source | Review provenance | Integration state | Next action |
|---|---|---|---|---|---|---|---|
| Lem-001 | TODO | conjectural | Def-001 |  | unchecked | isolated |  |
| Prop-001 | TODO | conjectural | Lem-001 |  | unchecked | isolated |  |
| Thm-001 | TODO | conjectural | Prop-001 |  | unchecked | isolated |  |
| Cor-001 | TODO | conjectural | Thm-001 |  | unchecked | isolated |  |

Keep the three state axes separate:

- Mathematical state: `conjectural`, `partial`, `gap-found`, `supported`, `closed-by-researcher`, or `refuted`.
- Review provenance: `unchecked`, `AI-assisted`, or a scoped and dated human or formal-tool review. AI review alone does not establish the claim.
- Integration state: `isolated`, `integrated`, `review-stale`, or `retired`. When an upstream definition or claim changes, mark affected downstream rows `review-stale`; do not automatically mark them refuted.
- Gap state: `open`, `resolved`, or `retired`. Retain resolved and retired IDs so earlier logs remain understandable.

### Open gaps

| ID | Affects | Precise missing justification or issue | Severity | State | Next action |
|---|---|---|---|---|---|
| Gap-001 | Thm-001 | TODO | blocking | open |  |

## Important links

- Ideas:
- Papers:
- Research logs:
- Drafts:

## Next actions

- [ ] One small, concrete next action

## Session index

- TODO
