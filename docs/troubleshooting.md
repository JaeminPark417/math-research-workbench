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
interrupted setup, or an older setup version that needs one new question.

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

Never solve a plugin problem by downloading unknown `main.js` files or copying
someone else's `.obsidian/plugins` folder. See [the plugin guide](obsidian-plugins.md).

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

GitHub connection, an external-storage write, Obsidian or TeX installation, and
each community plugin are separate choices. Approving one does not approve the
others.

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
