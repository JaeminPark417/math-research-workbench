# Mathematical research workflow

This workflow turns a rough thought into inspectable mathematical work without
pretending that an AI assistant is a mathematical authority. The researcher
may enter at any step.

## 1. Capture

Put an unstructured thought, question, URL, or reference to a scan in `inbox/`.
Codex should first preserve what the user supplied, then ask only the questions
needed to understand the intended task.

Output: an `inbox` note, unless the user is already working inside an existing
idea or project.

## 2. Triage

Codex proposes one of these destinations and explains it in plain language:

- `ideas/` for a question or conjectural direction;
- `papers/` for a source being read;
- `projects/` for sustained work with a defined research question;
- `notes/` for reusable background material that is not tied to one project.

After the durable note exists and its links have been checked, move the raw
inbox item to `inbox/archive/`. Do not delete it.

## 3. Formulate the question

For an idea, write down:

1. the objects and notation;
2. the exact question or claim;
3. hypotheses and quantifiers;
4. basic examples and edge cases;
5. known obstacles;
6. what would count as progress.

Label conjectures and uncertain steps. Codex must not fill a missing assumption
or reference from memory without marking it as uncertain.

## 4. Check the literature

Search using several formulations of the question. For each potentially
relevant source:

1. verify bibliographic facts against an authoritative record;
2. create or update a `paper` note;
3. distinguish the source's claims from the researcher's interpretation;
4. record the exact theorem, definition, or page relevant to the project;
5. link the paper note to the idea or project.

An unverified lead may be retained, but it must remain visibly unverified.

## 5. Open a project

Create a project when the question needs sustained work. Start from
`meta/templates/project.md` and create this simple structure:

```text
projects/project-slug/
├── README.md
├── sessions/
├── logs/
└── drafts/
```

The project `README.md` is the Research State Spine: the clean current map of the research question, paper-relevant definitions and claims, logical dependencies, open gaps, important links, and next actions. Use the stable IDs and separate state axes defined in `meta/schemas.md`. Codex maintains this map during ordinary conversation; the researcher does not need to edit Markdown tables by hand.

Only promote stable objects that affect a paper or a major research decision into the Spine. Keep exploratory calculations, mixed notes, and failed routes in `logs/` or `drafts`, with links from the Spine when they become relevant.

## 6. Develop an argument

Record substantial derivations and searches as dated `research-log` notes.
Each log should include the exact question, assumptions, work performed,
negative results, unresolved gaps, and a scoped conclusion.

Useful checks include:

- testing boundary and degenerate cases;
- tracing where each hypothesis is used;
- searching for counterexamples;
- checking consistency of notation and dependencies;
- comparing the proposed statement with nearby results in verified sources;
- using symbolic or finite-case calculations as limited evidence.

Do not erase a failed route. Mark why it failed and link it from the project
map if it is likely to recur.

When a log changes a stable definition, lemma, proposition, theorem, corollary, or gap, update the corresponding `Def-NNN`, `Lem-NNN`, `Prop-NNN`, `Thm-NNN`, `Cor-NNN`, or `Gap-NNN` entry in the project README. Record dependencies rather than repeating detailed proofs in the table. If an upstream statement changes, mark downstream integration states `review-stale` until they are rechecked.

## 7. Audit a proof

Use `meta/templates/proof-audit.md` for any important proof or suspected gap.
The audit should decompose the argument into claims and justifications, identify
hidden assumptions, inspect edge cases, and keep a gap register.

AI review can find problems or suggest repairs, but it cannot close a gap by
itself. A gap is closed only when the researcher accepts a complete argument or
when a correctly scoped formal check and human interpretation are both
documented.

## 8. Use formal tools when useful

Formalization is optional and should target a clearly stated lemma or finite
subproblem. Record:

- the exact encoded statement;
- definitions and imported assumptions;
- tool and version;
- the checked source file or durable reference;
- the checker result;
- a human assessment of whether the encoding matches the intended mathematics.

A successful checker result applies only to the encoding. It does not validate
the choice of definitions, the translation of the informal theorem, or the
relevance of the assumptions.

## 9. End a session cleanly

Create a `session` note that records:

- the session goal;
- what was actually done;
- decisions and their reasons;
- unresolved questions;
- the next small, concrete action;
- notes created or updated.

Then reconcile the project `README.md` with the new logs: add or update stable IDs, dependencies, mathematical state, review provenance, integration state, open gaps, and the next action. Do not renumber existing IDs or infer that a claim became true because an AI review found no problem. Archive source material; do not permanently delete it.

## 10. Promote durable knowledge

When a definition, lemma, example, or explanation becomes reusable across
projects, synthesize it in `notes/`. A concept note may be plain Markdown and
should link back to the project logs and verified sources from which it arose.
Do not remove the underlying provenance.

## How Codex should interact with beginners

- Use ordinary language before specialized tool terminology.
- Propose one clear next action at a time.
- Explain what a command or file change will do before requesting approval.
- Never assume that the user knows Git, terminals, YAML, or folder conventions.
- When something fails, state what remains safe, what was not changed, and the
  simplest recovery step.
