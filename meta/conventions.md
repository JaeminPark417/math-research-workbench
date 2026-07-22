# Conventions

These conventions make the workspace predictable for both the researcher and
Codex. They deliberately use a small vocabulary.

## Filenames and folders

- Use lowercase `kebab-case`: `fixed-point-obstruction.md`.
- When order matters, prefix a note with an ISO date:
  `2026-07-18-proof-audit.md`.
- Use a short stable slug for a project folder: `projects/fixed-point-method/`.
- Do not silently rename or move a large set of files. Explain the proposed
  change first and obtain the user's approval.

## Dates

- Use `YYYY-MM-DD` everywhere a full date is needed.
- Do not substitute vague phrases such as `today` in durable notes.
- A publication year may use `YYYY`; leave it `null` when it has not been
  verified.

## Language

- During first-run setup, the user selects `en` or `ko`.
- Codex writes explanations, headings, and note prose in the selected language.
- In a project README, keep the `Research State Spine` structural headings and table headers exactly as written in `meta/templates/project.md`. They are stable machine-readable labels maintained by Codex; surrounding explanation and ordinary headings use the selected language.
- YAML field names, enum values, filenames, LaTeX commands, and standard
  mathematical terminology remain stable in English where translation would
  make searching harder.
- Preserve quotations in their original language and identify the source.
- The user may request a different language for an individual note; set that
  note's `language` field accordingly.

## Links

- Use Obsidian wikilinks for workspace notes: `[[ideas/question-slug]]`.
- Quote wikilinks inside YAML.
- Use ordinary Markdown links for web pages.
- Link to a paper note instead of repeatedly typing a citation by hand.
- For a PDF, scan, image, or other binary, store only a safe reference in the
  text workspace unless the user has deliberately chosen another arrangement.

## Mathematical writing

- Put symbols and formulas in LaTeX: `$f\colon X\to Y$`.
- Define notation before using it and keep it stable within a project.
- State quantifiers, domains, hypotheses, and exceptional cases explicitly.
- Distinguish these labels in working notes: `Definition`, `Claim`,
  `Conjecture`, `Question`, `Gap`, and `Check`.
- A finite example, symbolic calculation, or AI-generated argument is evidence
  to inspect; it is not automatically a proof.
- Preserve failed approaches and counterexamples because they prevent repeated
  work.

## Stable research IDs

- In a project's Research State Spine, use `Def-NNN`, `Lem-NNN`, `Prop-NNN`, `Thm-NNN`, `Cor-NNN`, and `Gap-NNN`. Do not replace these with ambiguous single-letter or collective initialisms.
- Assign an ID only to a definition, claim, corollary, or gap that is stable enough to affect a paper or a major research decision. Ordinary scratch work stays in logs or drafts without an ID.
- A corollary receives `Cor-NNN` when it is a stable downstream consequence that should be rechecked if an upstream claim changes; a passing observation does not need its own ID.
- IDs remain stable when rows move. Never renumber live entries for appearance, never reuse a retired ID, and retain refuted or retired entries with a short reason so old links remain understandable.
- Record dependencies with the same stable IDs. When an upstream item changes, mark affected downstream entries `review-stale` in their integration state until they have been checked again.

## Status and provenance

- Use only the status values defined in `meta/schemas.md`.
- Record why a status changed in the note body or a linked session.
- Separate an author's claim, the researcher's interpretation, and an AI
  suggestion.
- Give external claims a source. If a source cannot be checked, label the claim
  `unverified` rather than completing the citation from memory.
- Keep mathematical state, review provenance, and manuscript integration state in separate columns. A review label never establishes mathematical truth.

## Archive instead of delete

- Do not permanently delete research notes or user-authored source material.
- Move processed inbox items to `inbox/archive/`, preferably under a `YYYY-MM/`
  subfolder.
- Mark inactive ideas and projects `archived`; keep links intact.
- Before replacing substantial text, preserve provenance through version
  history or an archived source copy.
