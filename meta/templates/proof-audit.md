---
type: research-log
title: "Proof audit: exact claim"
date: YYYY-MM-DD
updated: YYYY-MM-DD
language: en
project: "[[projects/project-slug/README]]"
kind: proof-audit
status: open
review_status: unchecked
related_papers: []
related_logs: []
---

<!-- This is a specialized research-log, not a separate note type. Use the
language selected during setup for prose and headings. -->

# Proof audit

## Audit scope

- Stable claim ID: `Thm-001`
- Statement or proof version:
- Included:
- Excluded:

## Claim being audited

Copy the exact statement, including all hypotheses, quantifiers, domains, and
exceptional cases. Link its source.

## Definitions and dependencies

| ID | Definition or dependency | Exact formulation or source | Role in the claim | Current status |
|---|---|---|---|---|
| Def-001 |  |  |  | fixed / proposed |
| Lem-001 |  |  |  | conjectural |

## Argument map

| Step | Claim or inference | Depends on | Justification supplied | Mathematical state |
|---|---|---|---|---|
| S1 |  | Def-001 |  | partial |

Reference the same stable IDs used in the project README. Use the project's mathematical-state vocabulary and reference a `Gap-NNN` whenever a step is blocked. An AI assistant may suggest a state, but a human decides whether a substantive gap is closed.

## Hidden-assumption check

- [ ] Domains and codomains are explicit.
- [ ] Quantifiers are in the correct order.
- [ ] Every denominator or inverse is defined.
- [ ] Boundary, empty, and degenerate cases were considered.
- [ ] Limit, convergence, measurability, or regularity steps state what they use.
- [ ] Every external theorem is cited with matching hypotheses.

Delete checklist items that are irrelevant only after noting why.

## Counterexample search

- Candidate edge cases:
- Findings:
- Limits of the search:

Absence of a found counterexample is not proof.

## Gap register

| Gap ID | Location | Issue | What would resolve it | State |
|---|---|---|---|---|
| Gap-001 | S1 |  |  | open |

## Formal check record, if used

| Date | System and version | Artifact or theorem ID | Scope checked | Result | Limitations |
|---|---|---|---|---|---|
| YYYY-MM-DD |  |  |  | not run |  |

A successful checker result applies to the encoding only. Leave `review_status` unchanged until the corresponding review is documented and a human has assessed whether the encoding matches the intended statement.

## AI-assisted review record

| Date | System or model | Material provided | Review scope | Findings retained | Unresolved cautions |
|---|---|---|---|---|---|
| YYYY-MM-DD |  |  |  |  |  |

AI-assisted review is provenance, not proof certification, and does not by itself change `review_status` from `unchecked`.

## Human review record

| Date | Reviewer | Version reviewed | Scope | Outcome | Remaining qualifications |
|---|---|---|---|---|---|
| YYYY-MM-DD |  |  |  |  |  |

## Scoped conclusion

- Mathematical verdict:
- Scope of verdict:
- Remaining assumptions:
- Open gaps:
- Review provenance:
- Not claimed:

Choose a scoped verdict such as `unresolved`, `gap identified`, `conditionally accepted`, or `accepted by the named human reviewer`. Do not declare the proof complete solely from AI review.

## Next action

- [ ] TODO
