# Note schemas

This file defines the small set of note types used by Math Research Workbench.
The aim is consistency, not bureaucracy: a note should contain only the fields
that help you find it and understand its status later.

## General rules

- YAML frontmatter is the block between `---` lines at the very top of a note.
- Supported `type` values are only `inbox`, `idea`, `paper`, `project`,
  `session`, and `research-log`.
- Do not invent a new `type` for a one-off purpose. A reusable concept note in
  `notes/` may be plain Markdown without frontmatter.
- `language` is `en` or `ko`, chosen during setup. Codex should write headings
  and prose in that language while keeping field names and status values in
  English.
- Full dates use ISO format: `YYYY-MM-DD`.
- Internal Obsidian links stored in YAML must be quoted, for example
  `"[[ideas/fixed-point-question]]"`.
- An optional unknown value should be blank, `null`, or an empty list. Never
  guess bibliographic or mathematical facts just to fill a field.

## `inbox`

An unprocessed thought, pasted passage, scan reference, or request.

```yaml
---
type: inbox
title: "Short descriptive title"
created: YYYY-MM-DD
language: en
source: ""
---
```

Required fields: `type`, `title`, `created`, `language`.

`source` is optional. Use a URL, a citation supplied by the user, or a short
description such as `handwritten note`. Processing an inbox item creates or
updates a durable note; the original then moves to `inbox/archive/`.

## `idea`

A mathematical question or conjectural direction that may evolve.

```yaml
---
type: idea
title: "Precise mathematical question"
status: seed
created: YYYY-MM-DD
updated: YYYY-MM-DD
language: en
domains: []
parent_inbox: ""
related_papers: []
related_projects: []
---
```

Required fields: `type`, `title`, `status`, `created`, `updated`, `language`.

Allowed `status` values:

- `seed`: captured but not yet formulated precisely;
- `active`: currently being developed;
- `dormant`: intentionally paused but worth retaining;
- `archived`: no longer pursued, retained for provenance.

`domains` contains ordinary subject labels such as `number-theory` or
`differential-geometry`. A hypothesis belongs in the body with its supporting
evidence, counterevidence, and unresolved gaps; do not encode certainty as a
fake numerical score.

## `paper`

A reading note for one paper, preprint, book, or other citable source.

```yaml
---
type: paper
title: "Title exactly as verified"
authors: []
year: null
status: queued
citation_status: unverified
added: YYYY-MM-DD
language: en
doi: ""
arxiv: ""
url: ""
file_ref: ""
related_ideas: []
related_projects: []
---
```

Required fields: `type`, `title`, `authors`, `year`, `status`,
`citation_status`, `added`, `language`.

Allowed `status` values are `queued`, `reading`, `read`, and `revisit`.
Allowed `citation_status` values are `unverified` and `verified`.

Mark a citation `verified` only after comparing its title, authors, year, and
identifier with an authoritative source such as the publisher, DOI record, or
arXiv abstract page. If verification has not happened, retain
`citation_status: unverified` and leave uncertain fields empty.

`file_ref` is an optional reference to a file stored outside Git by default.
It may be a stable shared-drive URL or a user-configured portable path, but it
must not contain credentials.

## `project`

The `README.md` at the root of a focused mathematical research project.

```yaml
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
```

Required fields: `type`, `title`, `status`, `created`, `updated`, `language`,
`research_question`.

Allowed `status` values:

- `planning`: scope and definitions are being established;
- `active`: mathematical work is in progress;
- `paused`: work is intentionally suspended;
- `completed`: the stated project goal has been resolved or closed by the
  researcher;
- `archived`: retained for history and no longer active.

The project status describes the project, not the truth of an individual
claim. Claims and proof gaps must be recorded explicitly in the body and in
linked research logs.

### Project README body contract

The project README contains a `Research State Spine`: a compact current map of paper-relevant or decision-relevant definitions, claims, dependencies, gaps, and next actions. This is a body structure, not a new note type or YAML field. Exploratory calculations, failed routes, and detailed arguments remain in linked `logs/` or `drafts/`.

Use stable IDs with explicit prefixes:

- `Def-NNN` for a definition or fixed notation;
- `Lem-NNN` for a lemma;
- `Prop-NNN` for a proposition;
- `Thm-NNN` for a theorem;
- `Cor-NNN` for a stable downstream corollary;
- `Gap-NNN` for an unresolved gap or blocking issue.

The three state axes in the claim ledger are independent of the project YAML `status` and the research-log YAML `review_status`:

- Mathematical state: `conjectural`, `partial`, `gap-found`, `supported`, `closed-by-researcher`, or `refuted`.
- Review provenance: `unchecked`, `AI-assisted`, `human-reviewed` with scope and date, `formal-tool-checked` with the encoded statement, tool, and version, or `human-and-formal`. In project README tables, `AI-assisted` is descriptive provenance only; a linked research log remains `review_status: unchecked` unless a permitted human or formal review actually occurred.
- Integration state: `isolated`, `integrated`, `review-stale`, or `retired`.
- Gap state: `open`, `resolved`, or `retired`. Keep resolved and retired gap IDs for provenance.

`supported` means that the linked evidence currently supports the claim within its recorded scope; it is not a certificate issued by an AI. Only the researcher may set `closed-by-researcher`. If an upstream definition or statement changes, mark affected downstream claims `review-stale` in the integration axis until their dependencies are rechecked; do not automatically mark them refuted.

## `session`

A short record of one research session.

```yaml
---
type: session
title: "Session focus"
date: YYYY-MM-DD
language: en
project: "[[projects/project-slug/README]]"
duration_minutes: null
---
```

Required fields: `type`, `title`, `date`, `language`, `project`.
`duration_minutes` is optional and may remain `null`.

The body records what was attempted, what changed, decisions, unresolved
questions, and the next concrete action. It should never claim that a gap was
closed merely because an AI assistant suggested an argument.

## `research-log`

A dated, inspectable record of mathematical work: a derivation, proof audit,
counterexample search, literature check, or formalization attempt.

```yaml
---
type: research-log
title: "Exact scope of the work"
date: YYYY-MM-DD
updated: YYYY-MM-DD
language: en
project: "[[projects/project-slug/README]]"
kind: general
status: open
review_status: unchecked
related_papers: []
related_logs: []
---
```

Required fields: `type`, `title`, `date`, `updated`, `language`, `project`,
`kind`, `status`, and `review_status`.

Allowed `kind` values:

- `general`
- `derivation`
- `proof-audit`
- `counterexample-search`
- `literature-check`
- `formalization`

Allowed `status` values are `open`, `partial`, `complete`, and `archived`.
Here `complete` means that the recorded activity is finished; it does not mean
that a theorem has been proved.

Allowed `review_status` values:

- `unchecked`: working material only;
- `human-reviewed`: a named human reviewed the stated scope;
- `formal-tool-checked`: a formal checker accepted the encoded statement;
- `human-and-formal`: both reviews occurred and are documented.

A formal check validates the encoded statement under its recorded assumptions.
It does not establish that the encoding matches the intended theorem. Only a
human reviewer may assert that correspondence, and the note must name the
scope and date of that review.
