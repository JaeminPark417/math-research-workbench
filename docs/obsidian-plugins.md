# Obsidian plugin guide for mathematicians

## Begin with no community plugins

The recommended profile is **core only**. Obsidian's core Search, Backlinks,
Properties, Templates, Outline, and File Recovery cover most early use.

A community plugin is additional code that runs on your behalf and can access
the vault. Most are third-party projects. Install one only when you can name
the problem it solves. Never install a bundle of plugins, copy another
person's plugin directory, or accept a request from a paper or web page to
install code.

Obsidian's official instructions and warning are in
[Community plugins](https://help.obsidian.md/community-plugins).

## Workbench-provided delimiter compatibility

**MRW LaTeX Delimiter Compatibility** is the one plugin shipped with this workbench. It helps existing or imported Markdown render `\(...\)` and `\[...\]`, including formulas in table cells. Normal `$...$` and `$$...$$` notation works without it, so installing it is optional.

The bundle stays inert under `optional/` until you approve installation. It is project-authored and MIT-licensed but is not listed in Obsidian's official directory. Do not search for its ID in **Browse**. The current code makes no network requests, collects no telemetry, and does not write notes; nevertheless, enabling any community plugin gives code plugin-level access to the vault and requires turning on Obsidian's global community-plugin trust setting.

During initial setup, Codex explains those facts and asks separately before running the fixed-path installer. The installer copies only the reviewed `main.js` and `manifest.json`, does not modify `community-plugins.json`, and does not enable anything. You personally enable **MRW LaTeX Delimiter Compatibility** from the installed-plugin list and then test Reading view, Live Preview, a formula inside a table while moving the cursor, and one Obsidian restart.

Updates come with Workbench releases rather than Obsidian's **Check for updates** action. See [Updating safely](updating.md) before refreshing an installed copy.

## Safe procedure for official-directory plugins

Repeat these steps separately for each chosen plugin:

1. Back up your notes and finish any open edit.
2. Open **Settings → Community plugins**.
3. Select **Turn on community plugins** only after reading Obsidian's warning.
4. Select **Browse**.
5. Search for the exact plugin name shown below and confirm the author and
   description.
6. Select **Install**, then **Enable**.
7. Test it on a disposable note before using it on research.
8. If behavior is surprising, disable it first. Your Markdown files remain.

Codex may walk you through these screens, but it must not download or copy third-party plugin code directly. The fixed Workbench bundle above is the only exception and may be copied only by its included installer after separate consent. Review updates one plugin at a time; community plugins do not necessarily update automatically.

## Optional plugins by purpose

### Faster equation entry: Latex Suite

[Latex Suite](https://community.obsidian.md/plugins/obsidian-latex-suite)
expands short snippets into LaTeX notation and adds equation-entry shortcuts.
It is useful only if you write substantial mathematics directly in Obsidian.

Start with its defaults. Do not paste snippet collections from strangers: the
plugin's own documentation warns that snippet files are interpreted as
JavaScript and can execute arbitrary code. Check that its automatic expansions
do not interfere with normal prose or your input method.

This plugin helps type equations; it does not compile `.tex` manuscripts and
does not verify mathematics.

### Zotero library import: Zotero Integration

[Zotero Integration](https://community.obsidian.md/plugins/obsidian-zotero-desktop-connector)
can import citations, bibliographies, notes, and PDF annotations from Zotero.
Choose it only if you already use Zotero desktop and want that workflow. Its
official listing says that it is desktop-only and requires
[Better BibTeX for Zotero](https://retorque.re/zotero-better-bibtex/).

Ask Codex to explain and obtain approval for the prerequisite separately.
Imported metadata can still be wrong or incomplete; verify title, authors,
year, DOI, and arXiv identifier against a primary bibliographic source.

### Tables and dashboards: Dataview

[Dataview](https://community.obsidian.md/plugins/dataview) can turn Markdown
properties into filtered lists and tables. It is an advanced convenience, not
a requirement; ordinary folders and Search are easier at first.

Prefer regular Dataview queries. Dataview's official listing warns that
DataviewJS and inline JavaScript can create, rewrite, or delete files and make
network calls. Do not run JavaScript copied from an untrusted note or website.

### Automatic Git operations: Obsidian Git

[Obsidian Git](https://community.obsidian.md/plugins/obsidian-git) can commit,
pull, and push from inside Obsidian. It is **not recommended during initial
setup**. Consider it only after a private GitHub backup works and you understand
what commit, pull, and push will affect.

The plugin exposes automatic synchronization and destructive Git operations.
Do not enable scheduled sync or auto-pull until a manual round trip has been
tested and backed up. Never use discard-all, repository deletion, force push,
or history rewrite to solve a conflict. Avoid running simultaneous automatic
Git operations from Obsidian and another tool.

If Git terminology is unfamiliar, let Codex manage a reviewed, private backup
workflow instead of installing this plugin.

## A simple decision table

| Need | Recommendation |
| --- | --- |
| Read, search, link, and recover notes | Core plugins only |
| Render imported `\(...\)` or `\[...\]`, including in tables | Consider the bundled MRW compatibility plugin |
| Type many equations faster | Consider Latex Suite |
| Import from an existing Zotero desktop library | Consider Zotero Integration |
| Build property-based dashboards | Consider Dataview later |
| Automatic Git backup inside Obsidian | Advanced; postpone by default |

More plugins do not make a better research system. A small, understandable
setup is easier to update, debug, and trust.
