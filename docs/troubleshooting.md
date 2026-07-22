# Troubleshooting

Start with the symptom you see. You can paste an error message into Codex, but
remove names, private paths, credentials, and confidential research first.

## I opened the folder, but nothing happened

This is expected. Opening a folder does not send a message. In the Codex chat,
send:

```text
Start setup
```

or invoke `$first-run`.

## Codex says this is the wrong folder

Open the folder that directly contains `AGENTS.md`, `README.md`, `meta/`, and
`.agents/`. ZIP extraction sometimes creates two nested folders with similar
names. Select the inner one containing those files.

## Codex can read but not edit

Check that you opened a local folder and that the app has permission to access
it. Codex may begin in read-only mode until you trust the working directory or
approve workspace access. Read the displayed path before approving. Do not
grant access to your entire home folder when the workbench folder is enough.

## Setup says I am in the cloud

A hosted checkout cannot configure software or folders on your computer. Open
the same workbench locally in the [ChatGPT desktop app](https://chatgpt.com/download/),
select Codex, and send `Start setup`. Cloud work may still edit available
Markdown, but it should not mark local setup complete.

## Setup starts again every time

Ask Codex:

```text
Diagnose why first-run setup is not staying complete. Inspect only the setup
status and permissions; do not print private paths or change my answers.
```

Common causes are an unwritable folder, a missing `.harness/local.yaml`, an
interrupted setup, or an older setup version that needs two new questions.

## Setup reports invalid, unreadable, inconsistent, or unsupported state

Stop setup. Codex must not resume, overwrite, follow, or delete the local state
entry. Your research notes are separate from this machine-only preference file
and should remain untouched.

Ask Codex:

```text
Help me recover the first-run state safely. Use only the redacted setup-state
result. Do not read or follow the local state, and do not change anything yet.
Explain whether I need a newer workbench or an approved quarantine rename.
```

For `unsupported`, update the framework before doing anything to the state. For
the other results, Codex may propose renaming only the exact local state entry
to a timestamped quarantine name without following it. It must first identify
whether `.harness` itself or only `local.yaml` is link-like, show the exact
non-destructive rename and recovery source, and ask for approval. Never delete
the entry. If `.harness` itself is a link or junction, use a fresh release copy
to restore the public `.harness` files after the link has been safely
quarantined; do not copy files through the link.

## Python 3.9 or newer was not detected

Python 3.9 or newer runs only the local redacted setup and validation helpers; you do not
need to learn Python. First-run checks for an existing command and a bundled
Codex workspace runtime before asking you to install anything. If neither is
available, it must not create or read saved setup state with ad hoc text
commands.

Choose `later` to continue ordinary Markdown work without saved setup, or ask
Codex to explain the official <https://www.python.org/downloads/> per-user
installer. Opening, downloading, and running an installer each require your
approval. After installation, reopen the workbench and send `Start setup`.

## Claude Code will not install or sign in

Claude Code and Claude are separate Anthropic products. They are optional and
this bundled review accepts only a direct personal Claude Pro or Max
subscription login. Team, Enterprise, Console/API keys, cloud providers,
proxies, and custom gateways need a separately reviewed workflow. It also
stops when managed policy is detected or cannot be checked, because safe mode
does not disable administrator policy hooks. If you do not have a suitable
account, choose `later`; this does not prevent ordinary Codex work. Check
Anthropic's current official
[installation](https://code.claude.com/docs/en/installation) and
[authentication](https://code.claude.com/docs/en/authentication) guidance.

Installing Claude Code and starting its login require separate approvals. If a
password, passkey, MFA, or OAuth prompt appears, Codex should pause while you
complete it yourself. Do not paste a secret or authorization code into chat,
and do not use `claude setup-token` for this setup. If authentication still
fails, remove names, account identifiers, private paths, and codes before
sharing an error message.

When the redacted check is otherwise ready, Codex asks you to run Claude in
safe mode, enter `/status`, and inspect only `Setting sources`. Do not copy the
screen. If `Enterprise managed settings` appears, or you cannot confirm its
absence, choose `later` and do not send the review.

## Claude review asks for approval even though I am signed in

This is expected. Login makes Claude available but does not authorize research
transmission. For every review, Codex must name Anthropic as the provider,
explain the purpose, list the exact files, diff, or text that would leave the
workspace, and ask for approval for that one review. You can decline without
disabling Claude Code or interrupting normal work.

## I cannot find the in-app Browser, or ChatGPT asks me to sign in again

The in-app Browser is available only on supported macOS or Windows desktop
configurations. Product capability, plan, or workspace policy can make it
unavailable, and it is unavailable on Linux. Choose `later` if it is missing or
if no installed compatible skill needs it. See OpenAI's official
[Browser guide](https://help.openai.com/en/articles/20001277-using-the-built-in-browser-in-the-chatgpt-desktop-app).

The Browser uses a profile separate from your ordinary browser and other app
sessions, so a new ChatGPT login can be normal. At a credentials screen, Codex
must pause: enter passwords, passkeys, MFA responses, and OAuth codes yourself.
Codex should not inspect or screenshot that screen. Login does not approve a
file upload or message; each compatible skill must preview the exact outbound
content and ask again before sending it.

## The workbench is inside OneDrive, iCloud, Dropbox, or Google Drive

Stop editing in Codex and Obsidian. Make a backup, close both applications, and
move the entire workbench to a non-sync local folder. Reopen it from the new
location, then ask Codex to check stored paths before changing them. Do not let
Codex move an open workspace automatically.

Keep a separate external-storage folder for PDFs if desired.

## A file in external storage is not visible

Confirm that Google Drive, Dropbox, or OneDrive is running and that the file is
available on this computer. Do not move the whole workbench into the sync
folder. Ask Codex to check only the configured external root without printing
it, and verify the target before creating a folder or moving a file.

Files under `files/` are not backed up by GitHub and need a separate backup.

## GitHub backup is public

Do not add or sync unpublished research. Ask Codex to inspect the current
visibility without printing credentials, then change it to private through
GitHub's account interface. Review GitHub's current
[repository visibility guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility).

If private material was already public, changing visibility does not guarantee
that no one copied it. Remove exposed credentials by revoking them at their
provider and seek appropriate institutional advice for sensitive data.

## Obsidian opens an empty vault

Use **Open folder as vault** and select the existing workbench root—the folder
containing `inbox/`, `ideas/`, and `projects/`. Do not select one of those
subfolders and do not create a second empty vault. See Obsidian's official
[vault guide](https://help.obsidian.md/vault).

## An Obsidian community plugin is installed but not working

An installed plugin must also be enabled. Open **Settings → Community plugins**
and check the installed-plugin toggle. Update one plugin at a time, then restart
Obsidian if its own documentation asks. If the problem began after installation,
disable that plugin first; your Markdown notes remain available.

For **MRW LaTeX Delimiter Compatibility**, do not search **Browse**. Ask Codex to run `python3 scripts/install-bundled-obsidian-plugin.py` with no flags. `installed_current` means the bundled and installed runtime match; `installed_stale` means a separately approved Workbench update is available. After enabling or updating it, test Reading view, Live Preview, cursor movement into and out of a formula-containing table cell, and one Obsidian restart.

| Status or result | Meaning and safe next step |
| --- | --- |
| `not_installed` | Nothing has been copied. Continue without it, or return to the consent-based installation guide. |
| `installed_current` | The installed runtime matches this Workbench release. Check the Enable toggle and run the rendering tests. |
| `installed_stale` | A newer bundled version is available. Read the change explanation, close Obsidian, and approve that update separately if wanted. |
| `empty` | An earlier attempt left an empty plugin directory. Codex may reinstall only after showing the exact action and receiving approval. |
| `installed_modified` | The installed files differ from the same-version bundle. Do not overwrite them; ask Codex to compare and archive the differing copy. |
| `installed_newer` | The installed plugin is newer than this Workbench release. Update the Workbench or preserve the newer copy; do not downgrade it. |
| `unsafe` or `result=unsafe_path` | A link, junction, or non-file object makes the path unsafe. Stop and inspect only this plugin path; never follow it or write through it. |
| `unrecognized`, `install_refused`, or `update_refused` | The directory contains missing or unexpected files. Close Obsidian and ask Codex to inventory this one directory without deleting anything. Installer-owned `.main.js.mrw-*` or `.manifest.json.mrw-*` remnants may be moved to an ignored recovery folder only after their origin is verified and the move is approved. |
| `invalid_bundle` or `bundle_unavailable` | The optional source bundle is incomplete or changed. Re-download or safely update the Workbench; do not fetch a standalone `main.js`. |
| `close_obsidian_and_retry` | Obsidian is probably holding a runtime file open. Close it fully, then retry only the already approved action. |

Finder and Windows metadata files such as `.DS_Store`, `Thumbs.db`, and `Desktop.ini` are ignored by the installer. Other unexpected files are preserved and require inspection rather than automatic cleanup.

Never solve a plugin problem by downloading unknown `main.js` files or copying
someone else's `.obsidian/plugins` folder. The fixed Workbench installer is the only reviewed copy-install exception. See [the plugin guide](obsidian-plugins.md).

## Equations display in Obsidian but a `.tex` file will not compile

These are different systems. Obsidian uses MathJax to display notation in
Markdown; compiling a manuscript requires Overleaf or a local TeX distribution.
Choose Overleaf to continue without a local installation, or rerun setup for
local TeX.

For a compile error, ask Codex to show the first meaningful error and the file
and line that caused it. Do not enable `shell-escape` merely to make an
untrusted document compile.

## Codex asks for approval

Approval prompts are a safety feature. Read the exact command, target folder,
account, and effect. It is always acceptable to decline and ask for a manual or
less invasive alternative.

GitHub connection, an external-storage write, Obsidian or TeX installation,
Claude Code installation, Anthropic login, each Claude review, Browser login,
each Browser upload or message, and each community plugin are separate choices.
Approving one does not approve the others.

## A file seems to be missing

Stop writing new files in the affected folder. Ask Codex for read-only checks
of Git history, Obsidian File Recovery, the operating system's trash, and your
backup. Do not run cleanup, reset, or bulk restore commands until you know which
copy is current.

## I am unsure whether research material is safe to send to Codex

A local folder does not make Codex offline. Content needed for a response may
be sent to OpenAI for processing. Before using referee reports, personal data,
confidential collaborations, regulated data, or restricted material, check
your institution's policy and account data controls. See OpenAI's
[Data Controls guide](https://help.openai.com/en/articles/7730893-data-controls-faq).
If you are unsure, do not add the material until the responsible person or
office has advised you.

For a suspected security defect in the workbench, follow [SECURITY.md](../SECURITY.md).
