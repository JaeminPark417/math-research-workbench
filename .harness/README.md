# Local setup state

`config.example.yaml` documents the setup fields. During first-run, Codex writes
machine-specific choices to `local.yaml`.

The redacted state helper requires Python 3. First-run checks an existing or
Codex-bundled runtime before creating `local.yaml`; if none is available, it
offers the official per-user installer and does not create a partial state that
cannot be resumed. No Python programming is required.

Blank values mean “not answered yet.” The explicit value `later` means the user
was asked and chose to postpone that item, so setup can still be completed.
Keep language, choice, plugin-state, and pending-plugin values in quotation
marks exactly as shown; unquoted YAML words such as `yes` and `no` can be
misread as booleans by some tools.

Setup version 2 adds two optional choices: whether to configure Claude Code for
the `claude-review` skill and whether to sign in to ChatGPT inside Codex's
in-app Browser for compatible browser-based skills. A valid version 1 file is
reported as `outdated`, not broken. A completed version 1 setup preserves its
existing answers and, after verifying any enabled GitHub destination is still
exactly private, asks only the two new questions. A non-private legacy remote is
preserved but must be made private or replaced before migration. An in-progress
version 1 setup first resumes any unanswered original question.
The `scripts/migrate-setup-v1.py` helper performs that schema-only change
atomically, keeps the original as ignored `local.v1-backup.yaml`, and prints no
preserved path or repository detail.

The `claude_code` and `chatgpt_browser` sections store only `choice`. They do not
record authentication or sign-in state, email addresses, organizations, plans,
cookies, or tokens. Authentication can expire and must be checked at the time a
feature is used. Browser sign-in is checked only inside the in-app Browser, not
in a shell.

`local.yaml` is intentionally ignored by Git because the older setup sections
may contain local paths or repository metadata. It must never contain
passwords, access tokens, API keys, private keys, authentication booleans,
email addresses, organization names, plan names, cookies, or tokens.
