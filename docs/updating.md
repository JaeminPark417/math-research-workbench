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

## Moving a completed setup from version 1 to version 2

Release v0.2 adds two local setup choices: optional Claude Code for Claude
review, and optional ChatGPT login in the in-app Browser for compatible skills.
An existing completed version 1 setup is **outdated, not damaged**.

During the framework-file update, preserve `.harness/local.yaml` exactly as
described below. After the new framework is in place, run `Start setup` once.
For a completed version 1 setup, the migration must:

- preserve the existing language, GitHub, external-storage, Obsidian, and TeX
  answers and verified details;
- if GitHub was enabled, verify that the current destination reports exactly
  `private`; a legacy `public`, `internal`, or `unknown` destination remains
  preserved as version 1 but must be replaced or made private under a separate
  approval before migration continues;
- after that safety gate, ask only the two new Claude Code and in-app Browser
  questions;
- accept `no` or `later` for either one; and
- avoid installing software or starting a login unless the user chooses it and
  gives the separate approvals required for those actions.

Do not rebuild the local file by hand and do not repeat healthy installations.
The bundled `scripts/migrate-setup-v1.py` helper performs the approved schema
change atomically without printing preserved paths or repository details. It
keeps a restrictive, Git-ignored `.harness/local.v1-backup.yaml` rollback copy.
During migration, the schema number changes to version 2 and setup remains
`in_progress`; it is marked `complete` only after both new questions have an
answer. Choosing `yes` records a preference, not permission to transmit
research: every Claude review, Browser upload, and Browser message still
requires its own exact outbound-content preview and approval.

Keep the v1 backup until setup version 2 has completed and one normal session
has succeeded. If migration fails, do not edit either file by hand; ask Codex
to compare only their redacted classifications and explain a restore plan.

You can use this request after updating the framework files:

```text
Resume the version 1 to version 2 setup migration. Preserve all of my existing
answers and verified details. If GitHub was enabled, verify that it is exactly
private before changing the version; do not commit or push during that check.
Then ask the two new Claude Code and in-app Browser questions, one at a time.
Do not install or start a login without a separate preview and approval.
```

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
`scripts/`, `docs/`, `optional/`, and distributed templates. Research content normally
includes `inbox/`, `ideas/`, `papers/`, `notes/`, `projects/`, and `files/`.
If a release note says a research schema changed, ask Codex for a migration
preview before approving it.

Even if Codex proposes several changes together, one approval is not blanket
permission for all of them. Review the file list and diff, then approve one
operation at a time. Software installation, an external-service action, and a
visibility change each require a separate explanation and approval.

## Adopt the Research State Spine in an existing project

Updating the framework does not automatically rewrite an existing project's `README.md`. The new template tracks stable, paper- or decision-relevant definitions, lemmas, propositions, theorems, corollaries, and unresolved gaps as `Def-NNN`, `Lem-NNN`, `Prop-NNN`, `Thm-NNN`, `Cor-NNN`, and `Gap-NNN`, but each existing project may migrate separately when you choose.

Ask Codex to preview one project's mapping before changing it. Scratch work remains in `sessions/`, `logs/`, or `drafts/`, and a consequence receives `Cor-NNN` only when it is a stable downstream consequence worth tracking. The migration must preserve the original notes and mathematical meaning; it must not treat an identifier as proof verification.

```text
Preview how this one project's README would migrate to the Research State Spine. Do not change any file yet. Keep scratch work in sessions, logs, or drafts; assign Def-NNN, Lem-NNN, Prop-NNN, Thm-NNN, Cor-NNN, and Gap-NNN only to stable objects that matter to the paper or a research decision, and explain every proposed mapping in ordinary language.
```

## Refresh the optional Workbench Obsidian plugin

The project-provided `mrw-latex-delimiter-compat` plugin is not in Obsidian's official directory, so **Check for updates** does not refresh it. Updating the files under `optional/` also does not silently replace the installed local copy.

After a framework update, ask Codex to run `python3 scripts/install-bundled-obsidian-plugin.py` with no flags. This is a read-only, path-free comparison. If it reports `installed_current` or `not_installed`, no update is needed. If it reports `installed_stale`, Codex must explain the version change and ask for separate approval. Close Obsidian before an approved `--update --consent` operation. The helper preserves `data.json`, never edits `community-plugins.json`, refuses modified or unknown installations, and does not enable the plugin. For `empty`, `installed_modified`, `installed_newer`, `unsafe`, `unrecognized`, or `invalid_bundle`, stop and follow the exact-status recovery table in [Troubleshooting](troubleshooting.md); do not delete or overwrite the plugin folder.

After reopening Obsidian, verify inline and display equations in Reading view and Live Preview, move the cursor into and out of a table cell containing a formula, and restart Obsidian once. Existing users who install the plugin after completing first-run setup should ask Codex to run the Obsidian part of setup again. Codex temporarily marks setup `in_progress` and clears the old completion timestamp before installation, then records a new completion timestamp only after the tests pass or the plugin step is explicitly postponed; all other answers remain unchanged.

## If you use GitHub

GitHub backup helps you compare and restore text versions, but it is **not
automatic synchronization**. A file appears on GitHub only after the relevant
changes are committed and pushed. A template-based research repository also
has its own history and no automatic upstream merge.
Before syncing an update:

- verify that the research repository is still private;
- review the complete file list and diff;
- ask Codex to list linked images and attachments ignored by Git; those files
  are not included on GitHub and need a separate backup;
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

Do not permanently delete research files during cleanup. After confirming what
each extra copy contains, move it to an archive location. Any proposed deletion
must first include the exact target and recovery method, followed by a separate
approval.
