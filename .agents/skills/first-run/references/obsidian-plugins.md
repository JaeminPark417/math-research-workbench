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
`dataview`, and `obsidian-git`.

Do not download plugin archives or write `.obsidian/plugins/` directly. Explain
that community plugins do not update automatically; the user should periodically
use **Check for updates** in the same settings page.
