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

## Status and provenance

- Use only the status values defined in `meta/schemas.md`.
- Record why a status changed in the note body or a linked session.
- Separate an author's claim, the researcher's interpretation, and an AI
  suggestion.
- Give external claims a source. If a source cannot be checked, label the claim
  `unverified` rather than completing the citation from memory.

## Archive instead of delete

- Do not permanently delete research notes or user-authored source material.
- Move processed inbox items to `inbox/archive/`, preferably under a `YYYY-MM/`
  subfolder.
- Mark inactive ideas and projects `archived`; keep links intact.
- Before replacing substantial text, preserve provenance through version
  history or an archived source copy.
