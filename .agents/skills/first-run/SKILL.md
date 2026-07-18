---
name: first-run
description: Guide a beginner through initial or resumed setup of Math Research Workbench, including safe folder placement, optional private GitHub backup, external PDF storage, optional Obsidian and plugins, and optional local TeX. Use when `.harness/local.yaml` is missing or incomplete, when the user says to start or redo setup, or when setup diagnostics or preferences need updating.
---

# First-run setup

Set up the workspace without assuming software-development experience. Ask one
question at a time, make every optional integration skippable, and save progress
so an interrupted setup can resume safely.

## Non-negotiable rules

- Do not install software, change accounts, create repositories, alter Git
  remotes, or write outside this repository without explicit approval for the
  exact action.
- Do not ask the user to paste a token or password. Prefer browser/device login.
- Never display `.harness/local.yaml` with `cat`, `sed`, or an equivalent whole-
  file read. Inspect only the named scalar fields needed for the current step
  (such as `status`, `setup_version`, or a `choice`), and prevent repository or
  storage paths from appearing in tool output. Paths may identify the user.
- Never print raw `pwd`, `git remote -v`, `git remote get-url`, or remote
  configuration during setup. Use the workbench's redacted diagnostic helpers;
  a raw path can identify the user and an HTTPS remote can contain a token.
- Do not move an open workspace automatically. If its location is unsafe, give
  a destination and ask the user to move it and reopen Codex.
- Prefer `no` or `later` over a broken integration. A skipped option must not
  block Markdown research work.
- Re-running setup must be idempotent: detect completed steps before acting.
- Keep the public distribution repository distinct from the user's research
  repository. A research remote is private by default.

## Step 1: Establish the environment

1. Determine whether Codex is running locally with access to this folder. This
   workflow targets the local Codex desktop app or CLI.
2. If the environment is a hosted/cloud checkout, explain that local software,
   local cloud-drive folders, and persistent ignored state cannot be configured
   there. Point the user to `GETTING_STARTED.md`; do not create a fake completed
   marker.
3. If `.harness/local.yaml` exists, use `python3 scripts/setup-state.py` (or the
   platform's `python` command) to inspect only its safe status, version, and
   choice fields, then resume the first incomplete step. Do not dump the file
   to inspect it. If Python is unavailable, use an anchored field-specific
   query that cannot match `repository`, `root`, or other path fields.
   Otherwise use `.harness/config.example.yaml` as the schema.
4. Run the non-mutating doctor for the operating system when possible:
   - macOS/Linux: `bash scripts/doctor.sh`
   - Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/doctor.ps1`
5. Run `python3 scripts/remote-state.py` (or the platform's `python` command) to
   classify the Git remote without printing its raw URL, even when the user may
   decline GitHub setup. If Python is unavailable, use only the safe remote-name
   output from `git remote` and the canonical `visibility,url` fields from
   `gh repo view --json visibility,url`. If those checks fail, classify
   visibility as unknown; never fall back to printing raw configuration. If
   `origin` is the public distribution repository or
   any public repository, warn before
   personal research is written or pushed. A public distribution remote is not
   a safe research destination. If the user chooses `no` or `later`, leave the
   remote unchanged but do not commit or push personal research to it.
   Treat `visibility=unknown` as public until a private destination is verified.
6. If the workspace is inside a commonly synchronized directory, stop setup and
   guide the user to a local folder such as `~/MathResearch` or
   `%USERPROFILE%\MathResearch`. The Git repository and a cloud-sync client must
   not manage the same files.

Create or update `.harness/local.yaml` with `status: in_progress`,
`setup_version: 1`, and blank unanswered fields matching the example schema.
The value `later` means “asked and postponed”; a blank value means “not asked
yet.” Record a step only after the user answers it.

## Step 2: Ask setup questions

Ask these in order. For GitHub, external storage, and Obsidian, accept `yes`,
`no`, or `later` in the user's language. TeX uses the four choices listed
below.

Record answers with these exact quoted values so an interrupted run can resume:

| Question | Local field | Allowed answered values |
| --- | --- | --- |
| Language | `language` | `"en"` or `"ko"` |
| GitHub | `github.choice` | `"yes"`, `"no"`, or `"later"` |
| External storage | `external_storage.choice` | `"yes"`, `"no"`, or `"later"` |
| Obsidian | `obsidian.choice` | `"yes"`, `"no"`, or `"later"` |
| TeX | `tex.choice` | `"overleaf"`, `"local"`, `"no"`, or `"later"` |

For a `"yes"` integration, also record its required detail only after it has
been verified: repository and visibility for GitHub; provider and root for
external storage; installed state and plugin profile for Obsidian. For local
TeX, record the verified engine. Community plugin names go in
`obsidian.community_plugins` only after each one is enabled and tested.
`obsidian.plugin_setup` is `"in_progress"`, `"complete"`, or `"later"`; a
completed empty plugin list means core plugins only. While a plugin is being
guided, `obsidian.pending_plugin` is one of `"latex-suite"`,
`"zotero-integration"`, `"dataview"`, or `"obsidian-git"`. Never put
credentials in any field.

### A. Language

Infer the conversation language, then confirm it. Record a short language code.
Use that language for the remainder of setup and daily work.

### B. GitHub backup

Explain in one sentence: GitHub stores version history for text files; it is not
required. Recommend a private repository for unpublished research.

- For `yes`, read `references/github.md` completely, inspect the current Git
  state, verify visibility, and follow its consent gates. Record `"yes"` only
  after the private research destination has been verified.
- For `no`, record `github.choice: "no"`; do not initialize Git merely to
  satisfy the harness.
- For `later`, record `github.choice: "later"` and continue.

### C. External file storage

Explain that GitHub is for text while external storage is for PDFs, scans,
slides, and other binaries.

- For `yes`, read `references/storage.md` completely and offer Google Drive,
  Dropbox, OneDrive, another existing folder, or local-only storage.
- Verify the selected directory exists before recording it. Create a new
  subdirectory only after showing the exact path and receiving approval.
- For `no`, record `external_storage.choice: "no"`; for `later`, record
  `external_storage.choice: "later"`. Keep `files/` as the local, Git-ignored
  fallback and state clearly that GitHub does not back it up.

### D. Obsidian

Explain that Obsidian is optional; the workbench remains ordinary Markdown
without it.

- For `yes`, read `references/obsidian.md` completely. Detect an existing
  installation. If absent, present an OS-appropriate official installation
  route and obtain approval before running any package-manager command.
- Guide the user to open this existing folder as an Obsidian vault. Do not copy
  or relocate it into an Obsidian-specific directory.
- Then read `references/obsidian-plugins.md`. Recommend the core-only profile.
  Offer community plugins by purpose and guide UI installation one at a time;
  never download or copy plugin code directly.
- Set `obsidian.plugin_setup: "in_progress"` while guiding a community plugin.
  Record its whitelisted ID in `obsidian.pending_plugin` so an interrupted run
  resumes that exact plugin. Only after the user confirms it was installed,
  enabled, and tested should setup append the ID to `community_plugins`, clear
  `pending_plugin`, and set the profile to custom. If the user stops, explicitly
  choose whether to resume later or keep the currently working core-only
  profile.
- Choosing core-only sets `obsidian.plugin_setup: "complete"` immediately. A
  postponed plugin decision sets it to `"later"` and preserves the currently
  working core-only profile; preserve `pending_plugin` only when the user wants
  to resume that specific plugin later.
- Record `obsidian.choice: "yes"` only after an Obsidian installation is
  detected and plugin setup is `"complete"` or `"later"`. For `no` or `later`,
  record the exact answer and continue.

### E. TeX

Explain that Obsidian renders math without a local TeX installation. Local TeX
is needed only to compile `.tex` manuscripts on this computer. Offer
`Overleaf`, `install locally`, `no`, or `later`, with `later` first.

- For local installation, read `references/tex.md` completely. Detect existing
  tools, present the package, source, approximate impact reported by the package
  manager, and exact command, then obtain approval. If the package manager does
  not report size, say that it could not be determined; never guess.
- After installation, verify with the platform's `scripts/compile-tex` wrapper
  and `meta/templates/article.tex`.
- A failed or postponed TeX install is advisory and must not block setup.
- Record `tex.choice: "local"` only after verification. Record `"overleaf"`,
  `"no"`, or `"later"` immediately when the user chooses that complete option.

## Step 3: Finish and teach

1. Run the doctor again and summarize pass, warning, and postponed items in
   plain language.
2. Set `status: complete`, preserving `later` choices and a `completed_at` ISO
   date, only when language and all four choice fields contain one of the
   answered values above. Required details for every enabled integration must
   also be present and verified. For enabled Obsidian, plugin setup must be
   `"complete"` or explicitly `"later"`. Otherwise leave `status: in_progress`
   and resume the missing question. Never store credentials in the file.
3. Give a short folder tour:
   - `inbox/`: put unclassified material here.
   - `ideas/`: evolving questions and conjectures.
   - `papers/`: bibliographic and reading notes, not copyrighted PDFs.
   - `notes/`: reusable definitions, lemmas, and explanations.
   - `projects/`: active research with sessions and proof work.
   - `files/`: local ignored binaries or links to external storage.
4. Offer four first prompts in the user's language, such as processing an
   arXiv link, auditing a proof, starting a project, and ending a session.
5. Point to `docs/daily-workflow.md` and state that setup can be changed later
   by saying "Run setup again" or invoking `$first-run`.

## Updating an existing setup

When explicitly asked to reconfigure, change only the requested preference.
Run diagnostics first, preview side effects, preserve unrelated answers, and
update the timestamp. Never repeat an installation that is already healthy.
