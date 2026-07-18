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

# Claim being audited

Copy the exact statement, including all hypotheses, quantifiers, domains, and
exceptional cases. Link its source.

## Definitions and dependencies

- Definition or earlier result:
  - Exact source:
  - Assumptions imported:

## Argument map

| Step | Claim | Justification supplied | Audit state |
|---|---|---|---|
| 1 |  |  | unchecked |

Use audit states such as `unchecked`, `clear`, `needs-detail`, `gap`, and
`depends-on-source`. An AI assistant may suggest a state, but a human decides
whether a substantive gap is closed.

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
| G1 |  |  |  | open |

## Formal check, if used

- Encoded statement:
- Definitions and assumptions:
- Tool and version:
- Source file or durable reference:
- Checker result:
- Human comparison with intended claim:

A successful checker result applies to the encoding only. Leave
`review_status` unchanged until the corresponding review is documented.

## Human review

- Reviewer:
- Date:
- Scope reviewed:
- Outcome:
- Remaining qualifications:

## Conclusion

Choose a scoped conclusion such as `unresolved`, `gap identified`,
`conditionally accepted`, or `accepted by the named human reviewer`. Do not
declare the proof complete solely from AI review.

## Next action

- [ ] TODO
