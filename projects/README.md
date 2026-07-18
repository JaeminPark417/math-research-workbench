# Projects

Create a project when a mathematical question needs sustained work across
several sessions. Each project gets one lowercase `kebab-case` folder.

Recommended structure:

```text
projects/project-slug/
├── README.md       current question, state, gaps, and next actions
├── sessions/       dated records of research sessions
├── logs/           derivations, proof audits, and literature checks
└── drafts/         developing mathematical exposition
```

Create the project `README.md` from `meta/templates/project.md`. Create session
notes from `meta/templates/session.md`, and use `research-log.md` or
`proof-audit.md` for inspectable mathematical work.

At the end of a session, update both the session note and the project
`README.md`. The README should always tell a returning researcher:

- the exact research question;
- what is established, conjectural, or blocked by a gap;
- where the supporting notes are;
- the next small action.

Project status is organizational. It never certifies that an individual
mathematical claim is true.
