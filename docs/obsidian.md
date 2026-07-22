# Obsidian: optional visual note-taking

Obsidian is optional. Math Research Workbench consists of ordinary Markdown
files and works without it. Obsidian provides a convenient editor, search,
links, and rendered mathematics for those same files.

In Obsidian, a **vault** is simply a folder of notes. The workbench folder is
already the vault; do not create or copy it into a second Obsidian-specific
folder. Obsidian's official documentation explains both
[local Markdown storage](https://help.obsidian.md/data-storage) and how to
[open an existing folder as a vault](https://help.obsidian.md/vault).

## Install only if you want it

During first-run setup, answer yes, no, or later. If you answer yes, Codex:

1. checks whether Obsidian is already installed;
2. presents the official installation route for your operating system;
3. explains any command or package-manager action; and
4. asks for explicit approval before installing anything.

You may instead install it yourself from the official
[Obsidian download page](https://obsidian.md/download) and
[installation guide](https://help.obsidian.md/install).

## Open the workbench

1. Start Obsidian.
2. Choose **Open folder as vault**.
3. Select the workbench root containing `AGENTS.md`, `inbox/`, and `projects/`.
4. Choose **Open**.
5. If the operating system asks for folder access, verify the path before
   allowing it.

Do not choose **Create new vault** for this existing workbench.

The distributed `.obsidian` folder contains a small starting configuration.
It sends new notes to `inbox/`, attachments to `files/`, and enables useful
core plugins. Device-specific window layout and plugin data should not be
published with research.

## Recommended core-only profile

Core plugins are included with Obsidian and maintained by its team. The
workbench enables a modest set:

- File explorer, Search, and Quick switcher;
- Backlinks and Outgoing links;
- Properties view, Page preview, and Outline;
- Templates and Command palette;
- Word count; and
- File recovery.

You can manage them under **Settings → Core plugins**. See Obsidian's official
[core plugin list](https://help.obsidian.md/plugins).

The shared Templates setting points to `meta/templates/`. Open the Templates
core-plugin settings and confirm that **Template folder location** is
`meta/templates` before inserting a workbench template.

File Recovery is helpful, but it is not a complete backup. Keep an independent
backup of valuable research.

## Mathematics and TeX

Obsidian renders LaTeX-style notation in Markdown using MathJax. For example:

```md
Inline: $e^{2\pi i}=1$.

Display:
$$
\int_0^1 x^n\,dx=\frac{1}{n+1}.
$$
```

This does not require a local TeX distribution. A local TeX installation is
only for compiling `.tex` manuscripts into PDFs. See Obsidian's
[mathematics syntax](https://help.obsidian.md/advanced-syntax#Math).

## Community plugins

No community plugin is required. Start with the core-only profile for a few
sessions, then install only a plugin that solves a specific problem. Community
plugins execute additional project or third-party code with access to your vault; Obsidian explicitly
warns users about this in its [community plugin guide](https://help.obsidian.md/community-plugins).

The Workbench also includes one inert, project-authored compatibility plugin under `optional/` for imported `\(...\)` and `\[...\]` notation. It is not installed or enabled by default. Its separate consent and testing procedure is documented in the plugin guide.

Continue with [obsidian-plugins.md](obsidian-plugins.md) before installing one.

## Codex and Obsidian together

Both applications edit the same files. To avoid conflicting edits:

- finish typing a note before asking Codex to reorganize it;
- let Codex describe files it changed;
- allow Obsidian a moment to refresh after a large edit; and
- close Obsidian before a framework update or bulk file move.

If a note appears stale, reopen it or use Obsidian's documented metadata-cache
rebuild option. Do not create a second copy of the vault as a quick fix.
