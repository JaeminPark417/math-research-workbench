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

<!-- Use only for sustained substantive mathematics. Keep the structural
headings and field labels in English; use the selected language for prose.
This is unpublished research, never public distribution content. -->

# Research run

## Problem Contract

- Contract version: `v1`
- Spine target reference: <stable ID; repository-relative project README path; current `HEAD` hash if the copied wording matches it, otherwise `working snapshot Run-YYYYMMDD-NNN` with this run's actual ID; `not applicable` for a new object>
- Exact target: <copy the current Spine wording exactly, or state the proposed new target exactly>
- Objects and definitions:
- Hypotheses and quantifiers:
- Exceptional and boundary cases:
- Allowed sources and tools:
- Success criterion:
- Refutation criterion:
- Explicit exclusions:
- Ambiguities requiring researcher confirmation:

Do not leave SPEC until the exact target, success criterion, and refutation criterion are explicit. The copied wording is the content anchor for a working snapshot; never invent a separate Spine version number. Version run-local revisions and preserve the project Spine's authority. A new AI-authored formulation or changed mathematical scope remains proposed until Human Promotion; record a merely proposed upstream change's downstream effects in the proposal.

## Run manifest

`SPEC → ROUTE → OBLIGATIONS → PROVE / DISPROVE → optional adapters → SYNTHESIZE → HUMAN PROMOTION`

| Field | Value |
|---|---|
| Current stage | SPEC |
| Last checkpoint | YYYY-MM-DD |
| Next bounded action | <one action, or link to its enrolled ticket activity> |

The project-local `run_id` must be unused and its date must equal the note's start `date`. This manifest owns the current next action unless an enrolled activity owns it; do not copy it into another live resume queue.

## Route

| Adapter | Exact bounded scope | Obligations | Why this route |
|---|---|---|---|
|  |  |  |  |

Use one row per selected adapter. For `mixed`, use semicolon-separated `adapter-name: exact scope` entries in frontmatter and matching rows here.

## Obligations

| Obligation | Exact subclaim or test | Depends on | What would establish it | What would refute it | State |
|---|---|---|---|---|---|
| Obligation-001 |  |  |  |  | open |

Use project stable IDs for existing objects; obligation IDs are local to this run.

## Attempt ledger

| Attempt | Date | Obligation | Direction | Branch | Context | Method or adapter | Result | Artifact, limits, or failure reason |
|---|---|---|---|---|---|---|---|---|
|  |  |  |  | none | same-context-audit |  |  |  |

Record consequential attempts, including meaningful failures and conditions for retry. Minor reasoning can stay in a linked derivation. Ordinary work uses `Branch: none` and an honest `same-context-audit`, `human`, or `tool` context. Add `meta/templates/research-run-extensions.md` before recording branch execution, `fresh-isolated`, `independent-proof-audit`, or formalization. Independent search without the candidate proof is not proof verification.

## Adapter and evidence records

| Descriptor | Exact scope | Input, artifact, or source | Result | Assumptions and limitations | Human or tool provenance |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

Use one scoped, non-cumulative descriptor per row. None establishes truth or implies another descriptor. `statement-matched` requires the dated, scoped human confirmation below. `formal-encoding-checked` requires the execution extension, validated manifest, and observed actual checker logs. Record only a user-consented reviewer identifier or role.

## Scoped synthesis

- Supported within the recorded scope:
- Refuted within the recorded scope:
- Conflicting findings:
- Open obligations and gaps:
- Proposed Research State Spine changes:
- Not claimed:

Link exact attempts and evidence. A new truth-bearing step needs its own unverified attempt. Preserve negative evidence; do not present AI agreement as closure.

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

The circulation baseline is the exact artifact version the researcher designates as ready to share. Leave confirmations at `not confirmed` until the researcher supplies a dated, scoped decision with linked evidence. These records do not authenticate identity. AI agreement, successful computation, formal encoding, and run completion never perform promotion. Follow `meta/safety.md` for private backup and each external transmission.
