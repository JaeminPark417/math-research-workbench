---
name: first-run
description: Set up, resume setup, or change requested preferences in Math Research Workbench. Use for a setup request or a missing preference that blocks the requested integration. Missing or outdated local state alone does not interrupt ordinary Markdown work, questions, or distribution maintenance.
---

# First-run setup

Setup is optional for ordinary research. Start it when requested, or offer the
specific missing choice needed for an integration. Never interrupt an ordinary
question, note edit, or public-template maintenance just because
`.harness/local.yaml` is absent or outdated. Do not create a completion marker
or fill unanswered choices with `later` without the user's answer.

Read the relevant section of [references/setup.md](references/setup.md):

- **Establish the environment:** initial/resumed setup and v1 migration. Use
  the redacted `scripts/setup-state.py` and `scripts/remote-state.py` helpers;
  never print local config, raw remotes, or authentication output. An invalid,
  unknown, or unsupported state blocks setup writes, not unrelated research.
- **Ask setup questions:** only unanswered or explicitly changed preferences.
  Ask one at a time and preserve previous answers. Read the matching integration
  reference below only when that option is chosen.
- **Finish and teach:** validate the answered choices, record completion only
  after verification, and give the folder tour.
- **Updating an existing setup:** change only the requested preference; preserve
  all other answers. Follow the resumable state rules for plugin installation.

| Selected option | Reference |
|---|---|
| Private GitHub backup | [github.md](references/github.md) |
| PDFs and other large files | [storage.md](references/storage.md) |
| Obsidian | [obsidian.md](references/obsidian.md) |
| Optional Obsidian plugins | [obsidian-plugins.md](references/obsidian-plugins.md) |
| Local TeX | [tex.md](references/tex.md) |
| Optional Claude review | [claude-code.md](references/claude-code.md) |
| ChatGPT in a supported in-app Browser | [chatgpt-browser.md](references/chatgpt-browser.md) |

Read `meta/safety.md` from the workspace root before
installation, account, sharing, or storage changes. Explain the exact action
and get its approval; an already approved action need not be approved twice.
Installing software, signing in, and transmitting research are separate actions.
Authentication is user-only: pause without reading or capturing credentials.
Never run `claude setup-token`. A skipped integration leaves Markdown work usable.

Require an available Python 3.9+ runtime before creating resumable setup state.
Use the OS-specific doctor for actual setup diagnostics, not on every task.
Keep personal research out of the public distribution and cloud-synced Git
folders. For research backup, verify an exactly private destination.

After setup, point to `docs/daily-workflow.md`. Codex maintains the project's
Research State Spine; the user does not need to edit tables manually. Explain
stable IDs such as `Def-NNN`, `Cor-NNN`, and `Gap-NNN` only as needed.
