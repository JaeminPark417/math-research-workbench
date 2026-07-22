# MRW LaTeX Delimiter Compatibility

This is an optional, project-provided Obsidian plugin for Math Research
Workbench. It renders imported Markdown that uses `\(...\)` for inline math or
`\[...\]` for display math, including formulas inside Markdown tables. New
workbench notes should continue to use the notation documented in
`meta/conventions.md`.

The files in this directory are inert. Obsidian does not load them from here.
The first-run guide explains the plugin and asks for separate consent before
the fixed-path installer copies `main.js` and `manifest.json` into the local
`.obsidian/plugins/mrw-latex-delimiter-compat/` directory. The installer never
edits `.obsidian/community-plugins.json`, and the user must enable the plugin
personally in Obsidian.

The current source makes no network requests, collects no telemetry, and does
not write research notes. Like every Obsidian community plugin, however, it
runs with plugin-level access to the vault after the user enables it. It is not
listed in Obsidian's official Community Plugins directory and must never be
installed by searching the **Browse** screen. Updates arrive with Math Research
Workbench releases rather than Obsidian's **Check for updates** action.

Use `python3 scripts/install-bundled-obsidian-plugin.py` for a read-only,
path-free status check. Installation or update must go through the workbench's
consent procedure; see `docs/obsidian-plugins.md`.

This plugin is distributed under the MIT License in `LICENSE`.
