# Local setup state

`config.example.yaml` documents the setup fields. During first-run, Codex writes
machine-specific choices to `local.yaml`.

Blank values mean “not answered yet.” The explicit value `later` means the user
was asked and chose to postpone that item, so setup can still be completed.
Keep language, choice, plugin-state, and pending-plugin values in quotation
marks exactly as shown; unquoted YAML words such as `yes` and `no` can be
misread as booleans by some tools.

`local.yaml` is intentionally ignored by Git because it may contain local paths
or account names. It must never contain passwords, access tokens, API keys, or
private keys.
