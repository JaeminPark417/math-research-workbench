# Claude Code setup

Use this reference only after the user chooses to consider Claude Code for the
optional `$claude-review` skill. Keep the workbench usable when this step is
declined, postponed, unavailable, or unsuccessful.

## Explain the boundary first

- State that a review sends the separately approved prompt and selected
  excerpts to Anthropic. Anthropic's account data controls and terms apply.
- State that this bundled review workflow targets a direct personal Anthropic
  `claude.ai` subscription login using Claude Pro or Max. The free Claude.ai
  plan does not include Claude Code. Team, Enterprise, Console/API-key access,
  Bedrock, Vertex AI, Foundry, proxies, and custom gateways are outside this
  beginner workflow because managed policy, the actual credential route,
  billing, and data controls require different disclosure.
- Ask the user to verify institutional policy before sending confidential,
  regulated, referee, student, patient, or unpublished restricted material.
- Clarify that setup does not send research content and that login does not
  authorize a later review. `$claude-review` requests exact-scope approval on
  every run.

Use the official documentation as the source of truth:

- Installation: <https://code.claude.com/docs/en/installation>
- Authentication: <https://code.claude.com/docs/en/authentication>
- Safe mode and CLI flags: <https://code.claude.com/docs/en/cli-reference>
- Telemetry controls: <https://code.claude.com/docs/en/monitoring-usage>

## Detect without revealing local data

Use `scripts/claude-readiness.py` for every readiness check. It suppresses the
executable path and help text, verifies all CLI flags required by the bundled
review, parses status JSON inside the helper without printing account fields,
and emits only a generic classification. Do not run `claude doctor` during
beginner setup because its diagnostics may expose machine-specific
configuration. Do not replace the helper with raw `--version` or `--help`.
Never run unsuppressed `claude auth status` or print environment output.

Only `claude_readiness=ready` may continue to the manual policy-source check.
That result means no known local managed-policy indicator was detected; it is
not proof that no remotely delivered policy exists. If the helper reports an
alternate or unknown route, do not inspect or change credentials. Explain that
an API key, bearer token, long-lived OAuth token, cloud provider, gateway,
custom base URL, `apiKeyHelper`, proxy, custom TLS route, OpenTelemetry
exporter, managed credential, or unknown provider cannot
use this direct-Anthropic beginner workflow, then offer `later` or `no`.
Likewise stop for an ineligible or managed subscription, a present managed
policy, or an unverifiable policy check. Never advise the user to delete or
bypass an organizational policy.

## Install only with exact consent

If Claude Code is absent, select one official route appropriate to the current
operating system. Before execution, show the command verbatim, identify its
source as Anthropic or the named package manager, explain its effect, and ask
for approval for that exact command.

- macOS, Linux, or WSL native installer:
  `curl -fsSL https://claude.ai/install.sh | bash`
  This downloads and executes Anthropic's installer in the user's account and
  installs a native Claude Code launcher. Native installs update in the
  background.
- macOS Homebrew alternative:
  `brew install --cask claude-code`
  This adds the stable Claude Code cask through Homebrew. Homebrew installs do
  not update automatically unless the user configures that separately.
- Windows PowerShell native installer:
  `irm https://claude.ai/install.ps1 | iex`
  This downloads and executes Anthropic's PowerShell installer for the current
  user; administrator access is not normally required. Native installs update
  in the background.
- Windows WinGet alternative:
  `winget install Anthropic.ClaudeCode`
  This installs the Anthropic Claude Code package through WinGet. WinGet does
  not update it automatically.

Do not substitute an unofficial package, run as administrator, or add another
dependency unless the user requests it and approves the newly displayed
effect. If the command or effect differs from this reference, reopen the
official installation page and obtain fresh approval. After installation,
rerun only the redacted readiness helper. An `incompatible_cli` result means
the installed CLI lacks one or more isolation flags required by
`$claude-review`; use the official update route only after showing it and
obtaining approval.

## Hand authentication to the user

1. Explain that the next action starts an Anthropic account login, can open a
   browser, and changes Claude Code's local account session. Show the exact
   command `claude auth login` and ask for separate approval to begin this
   login handoff. Installation approval or the earlier `yes` answer is not
   approval for this account action.
2. Only after that approval, tell the user to open a separate terminal window and run
   `claude auth login` themselves. They may instead run `claude` and follow its
   first-launch login prompt. Assume no terminal experience: on macOS, say to
   open **Terminal** from Spotlight; on Windows, say to open **Terminal** or
   **PowerShell** from the Start menu. Explain that they can type or paste the
   exact displayed command and press Enter without understanding shell syntax.
3. Pause all terminal and browser inspection while the user authenticates. Do
   not capture a screenshot or read terminal output during this interval.
4. Tell the user to enter passwords, passkeys, MFA values, OAuth codes, and any
   fallback login URL only in their own terminal or browser, never in chat.
5. Ask the user to return only after sensitive values and URLs are no longer
   visible and to say that the flow is finished. Do not ask which account they
   used.

Never run `claude setup-token`. It prints a long-lived OAuth credential and is
intended for non-interactive automation, not this workbench.

## Verify readiness without reading status

After the user says the flow is finished, run the redacted readiness helper
exactly once. Do not run unsuppressed `claude auth status`, inspect the helper's
captured JSON, or report raw output. For `claude_readiness=ready`, ask the user
to open a separate terminal, run `claude --safe-mode`, enter `/status`, and
inspect only `Setting sources`. They must exit and confirm only that no
`Enterprise managed settings` source appeared. Do not view, capture, or ask
them to transcribe the rest of the screen. Record `claude_code.choice: "yes"`
only after that confirmation. Otherwise explain the generic classification and
offer `later` or `no`.

Do not store `authenticated`, `signed_in`, an account name, email,
organization, plan, API-key presence, or a status snapshot. `$claude-review`
must repeat a live readiness check at actual use time.

The review skill must launch Claude with `--safe-mode`, which disables ordinary
local customizations while preserving normal authentication. Managed settings
and policy hooks can remain active, so the helper and user-only `/status` check
are mandatory before each review. The review also passes inline
`disableAllHooks` settings as defense in depth. Never substitute `--bare`:
current Claude Code help states that bare mode does not read OAuth or keychain
credentials and therefore conflicts with the subscription login flow above.
