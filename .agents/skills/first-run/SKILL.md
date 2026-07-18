---
name: first-run
description: Guide a beginner through initial, resumed, or v1-to-v2 setup of Math Research Workbench, including safe folder placement, optional private GitHub backup, external PDF storage, Obsidian and plugins, local TeX, Claude Code for explicit Claude reviews, and ChatGPT sign-in in a supported in-app Browser for compatible skills. Use when `.harness/local.yaml` is missing, incomplete, or outdated; when the user says to start or redo setup; or when setup diagnostics or preferences need updating.
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
- Pause before every account or credential screen. Do not inspect, screenshot,
  transcribe, or store passwords, passkeys, MFA values, OAuth codes, OAuth URLs,
  cookies, account identifiers, or raw authentication-status output. The user
  must complete interactive authentication personally.
- Never run `claude setup-token`; it prints a long-lived credential. A login
  does not approve any later file upload, prompt submission, or cross-provider
  transfer.
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
3. Before creating or resuming saved setup state, locate Python 3.9 or newer. Prefer an
   already available `python3`/`python` command or a bundled workspace Python
   runtime exposed by the current Codex desktop environment. Do not print its
   absolute path. Reject an older Python runtime. If no compatible runtime is available, do **not** create
   `.harness/local.yaml` or start a setup that claims it can resume. Explain
   that Python runs the workbench's local redaction and validation helper; the
   user does not need to write Python. Offer the official
   <https://www.python.org/downloads/> per-user installer and obtain approval
   before opening, downloading, or running it. Recheck after the user completes
   any installer personally. If they decline, continue ordinary Markdown work
   without saved setup and explain that first-run must begin again later.
4. If `.harness/local.yaml` exists, use `python3 scripts/setup-state.py` (or the
   verified Python 3.9-or-newer runtime above) to inspect only its safe status, version, and
   choice fields. Do not dump the file to inspect it.
   - For `ok` or `outdated`, resume under the version rules below.
   - For `invalid`, `unreadable`, or `inconsistent`, stop before any write,
     installer, login, or setup answer change. Do not follow, replace, or
     repair the entry automatically. Explain that the local preference file is
     unsafe or contradictory, leave research files untouched, and use the
     recovery procedure in `docs/troubleshooting.md`.
   - For `unsupported`, stop before any write and tell the user to update the
     workbench; an older setup tool must not change a newer schema.
   - For a helper error, missing classification, or any unrecognized result,
     fail closed: stop before every write and use the recovery guide.
   If Python becomes unavailable while local state already exists, do not fall
   back to reading or editing it with text-search commands. Explain that safe
   automatic resume needs the redacted helper and return to the runtime step.
5. Run the non-mutating doctor for the operating system when possible:
   - macOS/Linux: `bash scripts/doctor.sh`
   - Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/doctor.ps1`
6. Run `python3 scripts/remote-state.py` (or the verified Python 3.9-or-newer runtime) to
   classify the Git remote without printing its raw URL, even when the user may
   decline GitHub setup. If Python is unavailable, use only the safe remote-name
   output from `git remote` and classify visibility as unknown; never fall back
   to printing raw configuration or querying repository owner/URL fields.
   After GitHub setup is selected and the user has named the intended
   repository, a visibility-only `gh repo view` query may verify that exact
   destination. If checks fail, keep visibility unknown. If
   `origin` is the public distribution repository or its visibility is
   anything other than `private` (including `public`, `internal`, or
   `unknown`), warn before
   personal research is written or pushed. A public distribution remote is not
   a safe research destination. If the user chooses `no` or `later`, leave the
   remote unchanged but do not commit or push personal research to it.
   Treat every visibility other than `private` as non-private until a private
   destination is verified. GitHub's `internal` visibility can expose a
   repository to an organization; it is not private.
7. If the workspace is inside a commonly synchronized directory, stop setup and
   guide the user to a local folder such as `~/MathResearch` or
   `%USERPROFILE%\MathResearch`. The Git repository and a cloud-sync client must
   not manage the same files.

For a new setup, create `.harness/local.yaml` with `status: in_progress`,
`setup_version: 2`, and blank unanswered fields matching the example schema.
The value `later` means “asked and postponed”; a blank value means “not asked
yet.” Record a step only after the user answers it.

For an existing `setup_version: 1` setup, inspect the redacted `status` and
choice fields before deciding how to resume:

1. Treat a valid completed version 1 file as outdated, not broken. Preserve
   every existing language, integration answer, and verified detail; do not
   repeat the GitHub, storage, Obsidian, or TeX questions.
2. If version 1 is still `in_progress`, preserve its answered fields and resume
   any unanswered legacy questions in their original order. Do not skip a
   blank legacy answer. If it is inconsistent, use the stop-and-recovery branch
   above and migrate only after the redacted helper reports a valid state.
3. If the preserved GitHub choice is `yes`, require the redacted remote check
   to report exactly `private` before changing the schema version. Older version
   1 setups could legitimately record `public` or `internal`; preserve that
   file as `outdated`, warn that it is not a private backup, and guide the user
   to a private destination under the GitHub consent gates. Do not commit or
   push while resolving this safety gate. This is a required security check,
   not a repeated preference question.
4. Only after all version 1 requirements and the private-remote gate are
   complete, run `python3 scripts/migrate-setup-v1.py` (or the verified runtime)
   exactly once. It validates the redacted state, refuses a saved non-private
   GitHub destination unless the live redacted remote check now verifies it as
   private, creates a restrictive ignored `local.v1-backup.yaml`, atomically
   preserves existing private values, adds blank
   `claude_code.choice` and `chatgpt_browser.choice` fields, changes
   `setup_version` to `2` and `status` to `in_progress`, and clears
   `completed_at` until v2 finishes. Proceed only for
   `migration=ready_for_new_questions`. For any other generic result, stop and
   use the recovery guide; do not dump or hand-edit the file.
5. Ask the two new questions below, one at a time. Never turn a blank field
   into `no` or `later` without the user's answer.

## Step 2: Ask setup questions

Ask these in order. For GitHub, external storage, Obsidian, Claude Code, and
the ChatGPT Browser, accept `yes`, `no`, or `later` in the user's language.
TeX uses the four choices listed below.

Record answers with these exact quoted values so an interrupted run can resume:

| Question | Local field | Allowed answered values |
| --- | --- | --- |
| Language | `language` | `"en"` or `"ko"` |
| GitHub | `github.choice` | `"yes"`, `"no"`, or `"later"` |
| External storage | `external_storage.choice` | `"yes"`, `"no"`, or `"later"` |
| Obsidian | `obsidian.choice` | `"yes"`, `"no"`, or `"later"` |
| TeX | `tex.choice` | `"overleaf"`, `"local"`, `"no"`, or `"later"` |
| Claude Code | `claude_code.choice` | `"yes"`, `"no"`, or `"later"` |
| ChatGPT Browser | `chatgpt_browser.choice` | `"yes"`, `"no"`, or `"later"` |

For a `"yes"` integration, also record its required detail only after it has
been verified: a credential-free canonical `owner/repository` label and the
enum `private`, `public`, or `internal` for GitHub; provider and root for
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
  after the research destination reports exactly `private`; `internal` is not
  private.
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

### F. Claude Code for optional review

Explain that `$claude-review` can send a user-approved excerpt to Anthropic for
an optional second opinion. It is never required for ordinary work, and an AI
review is not a mathematical proof.

- For `yes`, read `references/claude-code.md` completely. Explain the eligible
  personal Claude Pro or Max requirement and managed-policy limitation before
  offering install or login steps.
  Show the exact official source, command, and effect, then obtain
  approval before running an installer.
- After the executable is ready, treat login as a second action. Explain that
  `claude auth login` may open a browser and changes the Claude Code account
  session, then obtain separate approval before presenting the login handoff.
- Let the user perform interactive authentication in their own terminal and
  browser. Do not run or observe the login flow. Verify readiness only through
  the suppressed exit status described in the reference.
- Record `claude_code.choice: "yes"` only after the executable, live login,
  redacted readiness check, and user-only `/status` policy-source confirmation
  are ready at setup time. Do not store an authenticated flag, email,
  organization, plan, credential, policy snapshot, or raw status response.
- For `no` or `later`, record the exact answer and continue. Failed or
  unaffordable setup must not block the workbench.

### G. ChatGPT in the in-app Browser

Explain that this optional step prepares a separate in-app browser profile for
a future compatible skill; it is not required for Codex or Markdown work.

- Read `references/chatgpt-browser.md` completely before offering `yes`.
- Offer `yes` only when the supported desktop Browser capability and a
  compatible consumer skill are both present. This release does not ship a
  ChatGPT Browser consumer skill, so recommend `later` unless the user has
  subsequently installed one.
- Record `chatgpt_browser.choice: "yes"` only after setup-time capability and
  sign-in readiness are confirmed under the reference's credential-screen
  protocol. Do not store login state, email, organization, plan, or cookies.
- On Linux or when the capability is unavailable, explain the limitation and
  offer `no` or `later`; never mark `yes` as a placeholder.
- A setup-time `yes` is only a preference and readiness check. Require a fresh
  live check and new outbound-scope approval whenever a consumer skill is used.

## Step 3: Finish and teach

1. Run the doctor again and summarize pass, warning, and postponed items in
   plain language.
2. Set `status: complete`, preserving `later` choices, and write
   `completed_at` as an ISO 8601 timestamp with a timezone only when language
   and all six integration choice fields contain one of the answered values
   above. Required details for every enabled integration must also be present
   and verified. For enabled Obsidian, plugin setup must be `"complete"` or
   explicitly `"later"`. For enabled Claude Code and the ChatGPT Browser,
   verify setup-time readiness but store only the choice. Otherwise leave
   `status: in_progress` and resume the missing question. Never store
   credentials, account metadata, or live authentication state.
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
