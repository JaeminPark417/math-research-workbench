# Update the workbench safely

Your research matters more than a framework update. Never drag a new release
over your working folder and choose “replace all.” A release ZIP is a snapshot,
and a repository created from a GitHub template does not update automatically.

## Before any update

1. Read the release notes. If no change you need is listed, you may postpone.
2. Confirm that your text files have a recent backup.
3. Confirm separately that PDFs and other files in external storage or
   `files/` have a backup.
4. Close Obsidian or pause editing so files do not change during comparison.
5. Download the new release into a **separate temporary folder** outside your
   working vault.

Do not copy `.harness/local.yaml` into a public issue or release. It may contain
private paths.

## Recommended update request

Open your existing workbench in local Codex and say:

```text
Help me update Math Research Workbench safely from the new release in this
separate folder. First compare versions. Do not change ideas, papers, notes,
projects, files, .harness/local.yaml, or personal Obsidian settings. List every
framework file you propose to replace and show the expected effect. Wait for my
approval before applying anything.
```

Provide the new release folder only when Codex asks. Grant access to that one
folder, not to an entire home directory or cloud drive.

Framework files normally include `AGENTS.md`, `.agents/skills/`, `meta/`,
`scripts/`, `docs/`, and distributed templates. Research content normally
includes `inbox/`, `ideas/`, `papers/`, `notes/`, `projects/`, and `files/`.
If a release note says a research schema changed, ask Codex for a migration
preview before approving it.

## If you use GitHub

GitHub backup helps you compare and restore text versions, but a template-based
research repository has its own history and no automatic upstream merge.
Before syncing an update:

- verify that the research repository is still private;
- review the complete file list and diff;
- do not use force push, history rewrite, `git reset --hard`, or `git clean`;
  and
- keep binaries outside the Git repository.

If the update produces a conflict, stop and ask Codex to explain both versions
in plain language. Do not choose “accept all” without reviewing the affected
research file.

## Verify and keep a rollback copy

After an approved update, ask Codex to run the workbench's non-destructive
checks and summarize warnings. Open several research notes and confirm that
links, equations, and Obsidian still work before removing the temporary copy.

Keep the pre-update backup until you have completed at least one normal session.
If something is wrong, restore the affected files from that backup or Git
history; do not delete the whole vault.
