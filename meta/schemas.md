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

`supported` means that the linked evidence currently supports the claim within its recorded scope; it is not a certificate issued by an AI. Set `closed-by-researcher` only after the researcher supplies a dated, scoped decision, a user-consented identifier or role, and linked evidence. This records provenance but does not authenticate the person's identity. If an upstream definition or statement changes, mark affected downstream claims `review-stale` in the integration axis until their dependencies are rechecked; do not automatically mark them refuted.

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

The optional research-run fields keep substantial multi-attempt work
inspectable without creating another note type:

- `run_id` identifies the bounded run log using `Run-YYYYMMDD-NNN`. Its date
  segment equals the note's `date`, which is the run start date, and the full ID
  is unique within the project. Ordinary research logs omit all three
  research-run fields. The ID identifies a research activity; it is not a
  claim ID or truth status.
- A Problem Contract is authoritative only within its run; the project README
  Research State Spine remains the canonical current state. When a run targets
  an existing stable object, record its stable ID in the
  `Spine target reference` field together with the repository-relative project
  README path.
  If the wording copied into `Exact target` matches the current `HEAD` at the
  start of SPEC, record that commit hash; otherwise write `working snapshot
  Run-YYYYMMDD-NNN`, replacing the placeholder with the run's actual ID. Always
  copy the exact current Spine wording into `Exact target`; that text is the
  content anchor for a working snapshot. The Contract version tracks run-local
  revisions; never invent a separate Spine version number.
- Only editorial Spine integration is automatic: add a new stable object copied
  without semantic change from a researcher-provided or already-canonical
  source at baseline state (`conjectural` for claims, `open` for gaps,
  `unchecked` review, and `isolated` integration), update source, dependency,
  or next-action metadata. Mark dependents `review-stale` only after an
  upstream change is already canonical or is applied after Human Promotion;
  keep the stale effects of a merely proposed upstream change in the run's
  proposal. A new AI-authored formulation, a change to an existing statement's
  hypotheses, quantifiers, or scope, a truth-bearing mathematical or gap-state
  change, statement matching, closure, retirement, or a circulation-baseline
  decision remains proposed until Human Promotion.
- A circulation baseline is the exact artifact version the researcher
  designates as ready to share outside the private working context.
- `adapter` records the primary route or scoped aid as `natural-proof`,
  `formalization`, `constructive-search`, `literature-audit`, or `mixed`. Leave
  it empty when no adapter is selected.
- `adapter_scope` states the exact obligation, encoded statement, search
  question, or computational target covered by that adapter. For `mixed`, use
  semicolon-separated per-adapter entries in the form `adapter-name: exact
  scope; adapter-name: exact scope`, and mirror them as separate rows in the
  body Route table. Leave it empty when `adapter` is empty.

Use `meta/templates/research-run.md` when any objective entry condition is met:
a second serious attempt begins, work resumes in another session, the target
needs multiple obligations or adapters, or a claim is load-bearing for a paper
or major research decision. When uncertain, keep an ordinary research log
without research-run fields until the threshold is crossed. Simple questions,
explanations, exposition edits, and routine one-step calculations do not need
a research-run log.

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
- `human-reviewed`: a human, recorded by a user-consented identifier or role,
  reviewed the stated scope on the recorded date;
- `formal-tool-checked`: a formal checker accepted the encoded statement;
- `human-and-formal`: both reviews occurred and are documented.

A formal check validates the encoded statement under its recorded assumptions.
It does not establish that the encoding matches the intended theorem. Only a
human reviewer may assert that correspondence, and the note must name the
scope and date of that review.

Research-run evidence descriptors such as `computationally-checked`,
`formal-encoding-checked`, `statement-matched`,
`literature-audited-within-scope`, and `expert-reviewed` are scoped,
non-cumulative provenance recorded in the note body. They are not additional
`review_status` values and never establish mathematical truth. Use
`statement-matched` only after explicit dated human confirmation of the exact
correspondence and scope. Record human provenance using only an identifier or
role the user has consented to include; do not collect unnecessary personal
information. Set a project claim to `closed-by-researcher` only with dated,
scoped human provenance and linked evidence. Automation may check that these
fields exist, but it cannot prove a human's identity or that the decision is
genuine.

Research-run logs are unpublished research. Before any commit, sync, or push,
verify an exactly private research destination and obtain approval for the
exact files. Uploads and external reviews follow the workspace's separate
per-transmission disclosure and consent rules. The public Math Research
Workbench distribution remote is never an acceptable destination for run logs.
