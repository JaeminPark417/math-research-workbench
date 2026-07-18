# Obsidian setup reference

Obsidian is optional. It is a local Markdown editor; Codex can use the workbench
without it.

## Detect before installing

Use a read-only platform check for the application or command. If Obsidian is
already installed, do not reinstall it.

If it is absent, show the user the official download route and, when available,
an OS package-manager alternative. Recheck current package identifiers before
running them. State the exact command and ask for approval.

- Official download: <https://obsidian.md/download>
- Official help: <https://obsidian.md/help>

Do not silently install Homebrew, a Linux package manager, or another system
prerequisite merely to install Obsidian. Offer the official graphical installer
instead.

## Open the workbench

1. Launch Obsidian.
2. Choose **Open folder as vault**.
3. Select the existing Math Research Workbench folder.
4. Do not copy the workbench into an Obsidian folder or a cloud-sync directory.
5. Confirm that `inbox`, `ideas`, `papers`, `notes`, and `projects` appear.

The repository provides minimal core settings: new notes go to `inbox/`, local
attachments go to `files/`, and a small set of official core plugins is enabled.
Workspace layouts, caches, community plugin code, and plugin data are local and
ignored by Git.

Explain that `files/` is also ignored by Git. If the user configured external
storage, prefer links to that storage for large PDFs.
