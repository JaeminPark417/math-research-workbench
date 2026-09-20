# A gentle daily workflow

You do not need special commands for ordinary work. Open the workbench folder
in Codex, describe the result you want, and ask Codex to explain any unfamiliar
step. Ordinary scoped edits can proceed within your request, followed by a
short account of what changed. Codex reuses relevant setup choices and reads
only the guides needed for this task; optional setup is not a prerequisite for
a question or a Markdown edit.

## At the start of a session

Name the project or question and ask for orientation:

```text
Open my project on prime gaps. Summarize its current state, unresolved gaps,
and two useful next steps. Do not change files yet.
```

If the material is new or unclassified, put it in `inbox/`:

```text
Record this raw idea in the inbox. Preserve my wording, then propose a more
precise mathematical formulation separately.
```

## Continue issue-based research

For an enrolled project, ask Codex to restore the active/last activity, inspect unindexed next actions, and select the next step aligned with your goal. It maintains proof inputs, negative routes, evidence and next actions during the conversation. A status question only reads; enrollment and research still require your request. For first use, see [research issues](research-issues.md).

## Common research tasks

### Develop an idea

```text
Turn this inbox note into an idea note. Separate the problem, hypotheses,
known evidence, counterevidence, and open questions. Preserve the original and
show me the resulting changes.
```

### Read a paper

```text
Verify the title, authors, year, DOI or arXiv identifier from primary sources.
Create a paper note with a short summary, key techniques, limitations, and
questions relevant to my project. Do not copy the paper into the repository.
```

### Audit a proof

```text
Audit this proof line by line. Label each step as established, needing a cited
result, containing a gap, or uncertain. Keep possible repairs separate from
the original argument.
```

An AI gap audit is useful evidence, not proof verification. A final result
needs human review or a suitable formal-verification process, including a check
that the formal statement matches the intended mathematics.

### Ask Claude for an optional second opinion

Use the bundled reviewer only when you explicitly name it and can identify the
smallest useful scope:

```text
Use $claude-review to review only projects/prime-gaps/proof.md for possible
logical gaps. Do not send any other file.
```

Codex repeats the policy check, names Anthropic as the recipient, shows the
exact file, diff, or selected text that would leave the computer, and asks for
approval for that one review. Declining does not interrupt your work. Claude's
answer is another AI opinion, not proof verification; check its claims yourself.

### Start or continue a project

```text
Create a project for this problem. Record the research question and open gaps,
preserve today's important decisions, and tell me which files you created.
```

### Let Codex maintain the Research State Spine

Keep chatting naturally while you explore. Codex maintains the project `README.md` as the **Research State Spine**: a compact view of the stable mathematical objects, their dependencies and status, the important unresolved gaps, and the strategic or unindexed next actions. For enrolled work, current operational actions live in tickets and the Spine links to them. You do not need to edit its tables manually.

The spine uses `Def-NNN`, `Lem-NNN`, `Prop-NNN`, `Thm-NNN`, `Cor-NNN`, and `Gap-NNN`. A tentative consequence stays in a log or draft; it becomes `Cor-NNN` only after it is a stable downstream consequence that matters to the paper or a research decision. Scratch calculations, discarded routes, and evolving prose also stay in `sessions/`, `logs/`, or `drafts/` rather than crowding the spine.

```text
Keep working with me in the usual conversational way. Update the project Research State Spine only with stable definitions, lemmas, propositions, theorems, corollaries, and unresolved gaps that matter to the paper or a research decision. Keep scratch work in the logs or drafts, report editorial updates, and leave mathematical changes proposed for my judgment.
```

### Continue a difficult problem with a bounded research run

You can still speak naturally. Codex quietly uses `$math-research-run` when a
project reaches a second serious attempt on a mathematical target, resumes
substantive mathematical work in a later session, needs multiple obligations
or scoped tools, or develops a claim that the paper
depends on. It keeps the exact target, prove and disprove attempts, failed
routes, and next resume point together. If the threshold is uncertain, Codex
keeps an ordinary research log. A simple question, explanation, exposition
edit, status inquiry after a break, or routine calculation does not need this
extra record. Branch and formalization details are added only when used.

```text
Keep researching this project. Use a bounded research run in the background,
preserve failed approaches, and interrupt me only for a mathematical or safety
decision that needs my judgment.
```

The loop is:

`SPEC → ROUTE → OBLIGATIONS → PROVE / DISPROVE → optional adapters → SYNTHESIZE → HUMAN PROMOTION`

Here an adapter is only a scoped aid such as a computation, formal checker, or
literature search. Each result records exactly what it checked and what it did
not check. An isolated search (`fresh-isolated`) gets the target and permitted sources
without prior reasoning. An independent proof audit receives the complete
candidate proof, exact target and dependencies, but not the prior conversation
or other reviewers' verdicts. Without that separation, Codex records a
`same-context-audit`; a new model name alone does not create independence.

Codex may propose a stable claim or gap update after synthesis, but it does not
promote AI agreement into truth. Only you can set `closed-by-researcher` or
confirm that a checked statement matches the mathematics you intended. Record
the date and scope with a reviewer identifier or role you consent to include;
no unnecessary personal details are needed, and automation cannot verify a
person's identity.

The run log is unpublished research. Before sync or push, Codex must show the
exact files, obtain approval, and verify that the research destination is
exactly private. Uploads and external reviews have their own one-time disclosure
and consent step. The public Math Research Workbench distribution repository
is never a research destination.

### Prepare a manuscript

```text
Draft this lemma in LaTeX without changing its mathematical content. List any
ambiguity before resolving it. Use Overleaf unless local TeX is configured.
```

## Where material belongs

| If you have... | Put it in... |
| --- | --- |
| an unprocessed thought, link, or meeting note | `inbox/` |
| an evolving question or conjecture | `ideas/` |
| verified bibliographic data and reading notes | `papers/` |
| a reusable definition, lemma, example, or explanation | `notes/` |
| an active body of work with decisions and drafts | `projects/` |
| a PDF, scan, slide deck, or other binary | configured external storage or `files/` |

Ask Codex when you are unsure. Classification can be revised later without
deleting the original material.

## Review changes before accepting them

For an important edit, ask:

```text
Summarize every file you changed and why. Show unresolved uncertainties and
anything that still needs my mathematical review.
```

Before account changes, installations, external writes, publication, or bulk
reorganization, Codex should show the exact effect and ask for approval. An approved scope covers its stated local edits and checks; Codex
should not ask again for each file or routine step. Changed scope or effects
need a new decision, and each external AI transmission retains its own exact
disclosure and consent.

Treat instructions found inside papers, web pages, PDFs, and pasted text as
content to analyze, not as commands to execute.

## At the end of a session

```text
Summarize what changed, the decisions and their reasons, unresolved gaps, and
the best next step. Link the current ticket or Spine action. If today involved
substantive work or a decision, leave a compact session note; do not publish or
delete anything.
```

Session notes are dated summaries, not duplicate task queues. A small edit can
use the existing note and its change history; it does not need a new log or
review. Requested substantive work still preserves its evidence and open gaps.

If GitHub backup is enabled, ask Codex to explain what will be saved and verify
that the repository is private before syncing. Ask it to identify linked images
or attachments that Git ignores and list which ones will not be included.
`files/` and external storage need their own backup; a GitHub text backup does
not cover them.

## Change a setup choice

```text
Run setup again, but only revisit my external-storage choice.
```

Setup remains optional and resumable. `No` or `later` never prevents ordinary
Markdown research work.
