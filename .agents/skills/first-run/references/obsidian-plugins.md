# Obsidian plugin guide

Start with core plugins. Obsidian builds and supports them, and they are already
included with the application. Community plugins execute third-party code with
access to the vault and may make network calls or modify files.

- Core plugin list: <https://obsidian.md/help/Plugins/Core%2Bplugins>
- Community plugin safety and installation:
  <https://obsidian.md/help/Extending%2BObsidian/Community%2Bplugins>

## Recommended profiles

### Core only (default)

Use File explorer, Search, Quick switcher, Backlinks, Outgoing links, Page
preview, Properties view, Templates, Command palette, Outline, Word count, and
File recovery. No community plugin is required for this workbench.

### Compatibility for imported LaTeX delimiters

Offer **MRW LaTeX Delimiter Compatibility** when the user has existing or
imported Markdown containing `\(...\)` or `\[...\]`, including formulas in
table cells. Standard Obsidian math does not require this plugin, and new notes
should follow `meta/conventions.md`.

This project-authored plugin is bundled inertly under
`optional/obsidian-plugins/mrw-latex-delimiter-compat/`. It is not listed in
Obsidian's official Community Plugins directory, so never search for or install
its ID from **Browse**. The current code makes no network requests, collects no
telemetry, and does not write research notes, but once enabled it still runs
with Obsidian plugin-level access to the vault. Turning on community plugins
also changes Obsidian's global trust setting for this vault. Updates come only
with Math Research Workbench releases.

Ask for explicit approval after that explanation. If approved, use only:

```text
python3 scripts/install-bundled-obsidian-plugin.py --install --consent
```

The tool prints the same disclosure, accepts no source or destination path,
copies only `main.js` and `manifest.json`, verifies the copied bytes, and never
edits `.obsidian/community-plugins.json`. It does not enable the plugin. The
user must then:

1. Open **Settings → Community plugins** and read Obsidian's warning.
2. Select **Turn on community plugins** if they accept that global trust change.
3. Enable **MRW LaTeX Delimiter Compatibility** in the installed list. Do not
   use **Browse** for this plugin.
4. Open an ordinary test note and confirm `\(x+y\)` in Reading view and Live
   Preview.
5. Confirm a `\(x+y\)` formula in a Markdown table remains rendered after the
   cursor enters and leaves the cell.
6. Restart Obsidian and confirm both tests again.

Keep `obsidian.plugin_setup` as `"in_progress"` with pending ID
`mrw-latex-delimiter-compat` until the user confirms all six steps. If they
decline, do not run the installer. If they choose later, leave the bundle inert
and preserve the pending ID only when they want to resume this exact choice.
When adding the plugin after first-run was already complete, first set the
overall setup `status` back to `in_progress` and clear `completed_at`; restore
completed status with a new timezone-bearing timestamp only after the checks
pass or the plugin step is explicitly postponed.

For an update, first run the installer with no flags. If it reports
`plugin_status=installed_stale`, explain the bundled and installed versions,
ask for a separate approval, ask the user to close Obsidian, and run:

```text
python3 scripts/install-bundled-obsidian-plugin.py --update --consent
```

The updater preserves an existing `data.json` and refuses unknown files,
modified equal-version code, downgrades, links, junctions, and path arguments.
After reopening Obsidian, repeat the rendering checks. Obsidian's **Check for
updates** action cannot update this unregistered plugin.

### Faster mathematical typing

Offer **Latex Suite**. Obsidian already renders standard LaTeX-style math;
Latex Suite adds snippets and typing expansions. It is optional and may change
typed text automatically.

Directory page: <https://community.obsidian.md/plugins/obsidian-latex-suite>

### Zotero literature workflow

Offer **Zotero Integration** only to an existing Zotero user. Explain its
additional Zotero and Better BibTeX requirements before installation. Do not
request or store a Zotero API credential in the vault.

Directory page:
<https://community.obsidian.md/plugins/obsidian-zotero-desktop-connector>

### Metadata dashboards

Offer **Dataview** only after the user understands properties. Prefer its query
language; do not enable or paste DataviewJS from an untrusted source because it
can run code with plugin-level access.

Directory page: <https://community.obsidian.md/plugins/dataview>

### Git from Obsidian (advanced)

Offer **Git** only when GitHub backup is enabled and the user explicitly wants
Obsidian to manage synchronization. Explain that simultaneous scheduled commits
from Obsidian and Codex can conflict. Choose one automatic sync owner; default
to Codex-guided Git and leave automatic Obsidian Git sync off.

Directory page: <https://community.obsidian.md/plugins/obsidian-git>

## Installation sequence

For each selected community plugin:

1. Make sure the text repository has a current backup.
2. Open **Settings → Community plugins**.
3. Select **Turn on community plugins**, then **Browse**.
4. Search for the exact plugin name and verify its author and directory page.
5. Select **Install**, then **Enable**.
6. Test one ordinary note before installing another plugin.

While these steps are unfinished, keep `obsidian.plugin_setup` marked
`"in_progress"` and save its whitelisted ID in `obsidian.pending_plugin`. Add a
plugin to `obsidian.community_plugins` and clear `pending_plugin` only after the
user confirms that it is installed, enabled, and tested. If the user postpones,
record `"later"`; do not mistake selection or opening the settings screen for a
completed installation. The IDs are `latex-suite`, `zotero-integration`,
`dataview`, and `obsidian-git`. The separate fixed bundle ID is
`mrw-latex-delimiter-compat`.

Do not download plugin archives or write `.obsidian/plugins/` directly. The
only exception is the reviewed fixed-ID bundle installed by the exact helper
above after approval. For third-party directory plugins, periodically use
**Check for updates** in the same settings page.
