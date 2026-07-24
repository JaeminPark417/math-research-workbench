# Projects

Create a project when a mathematical question needs sustained work across
several sessions. Each project gets one lowercase `kebab-case` folder.

Recommended structure:

```text
projects/project-slug/
├── README.md       current question, state, gaps, and next actions
├── sessions/       dated records of research sessions
├── logs/           derivations, bounded research runs, audits, and checks
└── drafts/         developing mathematical exposition
```

Create the project `README.md` from `meta/templates/project.md`. Create session
notes from `meta/templates/session.md`, and use `research-log.md` or
`proof-audit.md` for inspectable mathematical work. When a problem requires
the second serious attempt, a cross-session resume, multiple obligations or
scoped adapters, or a load-bearing paper claim, Codex uses
`$math-research-run` and `meta/templates/research-run.md`. The researcher may
keep speaking naturally. When the threshold is uncertain, Codex keeps an
ordinary research log; simple questions, explanations, exposition edits, and
routine calculations do not create a run.

Treat the project `README.md` as its **Research State Spine**. The researcher can keep talking to Codex naturally; Codex maintains the spine, and the researcher does not need to edit its tables manually. Promote only stable objects that matter to the paper or a research decision: `Def-NNN` definitions, `Lem-NNN` lemmas, `Prop-NNN` propositions, `Thm-NNN` theorems, `Cor-NNN` corollaries, and `Gap-NNN` unresolved gaps. Give a consequence a `Cor-NNN` identifier only when it is a stable downstream consequence worth tracking. Keep scratch calculations, tentative consequences, failed routes, and evolving exposition in `sessions/`, `logs/`, or `drafts/`.

At the end of a session, update both the session note and the project
`README.md`. The README should always tell a returning researcher:

- the exact research question;
- what is established, conjectural, or blocked by a gap;
- where the supporting notes are;
- the next small action.

Project status is organizational. It never certifies that an individual
mathematical claim is true.

A bounded run preserves a versioned Problem Contract, local obligations,
prove and disprove attempts, scoped adapter evidence, failed routes, synthesis,
and an explicit human-promotion checkpoint. Evidence descriptors are
non-cumulative provenance, not a truth ladder. A same-context review is never
called fresh. `statement-matched` requires dated, scoped human confirmation,
and `closed-by-researcher` requires a dated, scoped researcher decision with
linked evidence. A user-consented reviewer identifier or role is enough; avoid
unnecessary personal information. Automated checks do not prove identity.

Run logs are unpublished research. Before commit, sync, or push, verify that
the destination is exactly private and approve the exact files. Uploads and
external reviews follow the separate per-transmission disclosure and consent
rules. Never send run logs to the public Math Research Workbench distribution
remote.

Existing project READMEs are not rewritten automatically when this framework changes. Migrate one project at a time only when the researcher asks, preview the proposed mapping first, and preserve the original notes and mathematical meaning.
