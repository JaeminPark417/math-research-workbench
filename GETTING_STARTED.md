# Getting started, step by step

This guide assumes you have used ChatGPT in a browser but have not used Git,
a terminal, Markdown, or Codex. You do not need to learn those tools before
starting.

## Seven terms used in this guide

- **Folder**: a container on your computer, like a paper filing box.
- **Markdown**: ordinary text with a few simple symbols for headings, links,
  and mathematics. Files end in `.md`.
- **Vault**: Obsidian's name for a folder of notes. In this project, the
  workbench folder and the Obsidian vault are the same folder.
- **Git/GitHub**: optional version history and online backup for text files.
  They are not the same as Google Drive or Dropbox.
- **TeX/LaTeX**: a typesetting system that turns a `.tex` manuscript into a
  PDF. It is not needed for ordinary notes or Obsidian math display.
- **Claude Code/Claude**: an optional Anthropic terminal tool and AI service
  that can provide a second AI review. They are separate from OpenAI, ChatGPT,
  and Codex.
- **In-app Browser**: an optional browser profile inside the desktop app that
  compatible skills can use. It is separate from your ordinary web browser.

## 1. Choose a safe place

The workbench's text files may be managed by Git. Do not let a cloud-sync
client manage the same folder at the same time; two systems trying to rename or
merge the same files can create conflicts.

Create a folder named `MathResearch` directly inside your personal home folder,
then put the workbench inside it. Avoid Desktop or Documents if your computer
automatically syncs those locations. If you are unsure, Codex will check before
setup continues.

Google Drive, Dropbox, OneDrive, and similar services are still useful for
PDFs, scans, slides, and other large files. Setup can connect a separate folder
for those files later.

## 2. Get a copy of the workbench

### Recommended: release ZIP

1. Open the [latest release page](https://github.com/JaeminPark417/math-research-workbench/releases/latest).
2. Under **Assets**, download the ZIP named for Math Research Workbench.
3. Move the ZIP to the safe location chosen above.
4. Extract or unzip it.
5. Open the extracted folder and confirm that you can see `README.md` and
   `AGENTS.md`. That is the folder to open in Codex.

A ZIP is a snapshot. It does not connect your research to GitHub. Setup will
ask whether you want a private GitHub backup and can guide you later.

### Alternative: create from the GitHub template

Use this route only if you already want a GitHub account and private research
repository.

1. On the repository page, choose **Use this template** → **Create a new
   repository**.
2. Give the repository a name that does not reveal confidential research.
3. Select **Private**. Do not accept a public default for unpublished work.
4. Create the repository.
5. Choose **Code** → **Open with GitHub Desktop** and clone it into the safe,
   non-sync location described above. This keeps the local folder connected to
   the private repository.
6. If you do not want GitHub Desktop, use the recommended release-ZIP route
   instead. Downloading a ZIP from your newly created private repository does
   not connect the extracted folder to that repository.

A repository made from a template does not receive template updates
automatically. GitHub documents the current process in
[Creating a repository from a template](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template).

## 3. Install and open Codex

The beginner desktop route below is available on macOS and Windows. On Linux,
there is currently no ChatGPT desktop app; using this workbench requires the
[Codex CLI](https://developers.openai.com/codex/cli/) and basic terminal
familiarity. The rest of this section describes the beginner desktop route; on
Linux, follow the official CLI guide, change into the extracted workbench
folder, start Codex there, and send the same `Start setup` message.

1. Download the [ChatGPT desktop app](https://chatgpt.com/download/) from
   OpenAI's official site.
2. Install it as you would any normal application and sign in.
3. Select **Codex** in the desktop app.
4. Choose the option to open a local folder or project.
5. Select the workbench folder containing `AGENTS.md`.
6. If the app asks whether you trust the folder or want to allow local access,
   confirm only after checking that the displayed folder is the one you chose.

OpenAI's current description of local folders and desktop availability is in
[ChatGPT Work and Codex](https://help.openai.com/en/articles/20001275).

The Codex CLI is not required on macOS or Windows.

## 4. Send the first message

Opening the folder does **not** start a conversation. Codex waits for you to
send a message. Type and send:

```text
Start setup
```

You can also say `초기 설정을 시작해줘` or invoke `$first-run`.

Before saving any answer, Codex checks for Python 3.9 or newer. It uses an existing or
Codex-bundled runtime when available; you do not need to program. If none is
available, Codex explains the official per-user installer and asks separately
before opening, downloading, or running it. If you decline, ordinary Markdown
work still works, but setup does not create a partial state or promise resume.

Once that helper is available, closing the app halfway through is safe: reopen
the same folder and send the same message. Setup records completed answers
locally and resumes at the first unfinished question.

## 5. Answer the setup questions

Codex asks one question at a time. `No` and `later` are always valid answers.

### Language

Choose the language in which Codex should explain unfamiliar terms and report
changes.

### GitHub backup

GitHub can preserve versions of text files. It is optional. If you choose it:

- unpublished research is private by default;
- Codex uses browser or device login and never asks you to paste a password or
  token into chat;
- Codex describes the current connection only as a redacted safety class. After
  you name or approve the intended owner and repository, it shows the proposed
  credential-free canonical address and visibility before changing anything;
  and
- large PDFs remain outside GitHub.

GitHub is not an automatic backup. A change appears there only after it has
been committed and pushed. Codex should explain what those words mean, show
what will be included, verify that the destination is private, and ask before
each synchronization.

The public Math Research Workbench repository is a distribution template, not
the place for your private research.

### External file storage

Choose Google Drive, Dropbox, OneDrive, another existing folder, local-only, or
later. Codex verifies the folder and asks before creating a subfolder. Only
PDFs and other binaries go there; the workbench itself stays in its safe local
location.

If you choose local-only, `files/` is available, but GitHub does not back it up.

### Obsidian

Obsidian is optional. If selected, Codex checks whether it is installed, offers
the official installation route, and asks before installing anything. You then
open the **existing workbench folder** as a vault; do not create a second copy.

Start with core plugins only. Codex separately offers the inert, Workbench-provided LaTeX delimiter compatibility plugin and explains its access, unofficial-directory status, update method, and testing steps before asking whether to install it. Third-party community plugins remain optional and are offered one at a time through Obsidian's official directory. See [Obsidian](docs/obsidian.md) and [Obsidian plugins](docs/obsidian-plugins.md).

### TeX

Choose `later`, Overleaf, local installation, or no. Overleaf is the simplest
starting point because it compiles in the browser. If you choose local TeX,
Codex first detects existing tools, explains the download and disk impact,
shows the exact installation action, and asks for approval. A failed or
postponed installation does not block the rest of setup.

### Claude review

Claude review is optional. It uses Claude Code, a terminal tool from
Anthropic, to ask a separate AI service for a second opinion. It is not
included with ChatGPT or an OpenAI account, and this workflow requires an eligible paid
personal Claude Pro or Max subscription. This bundled beginner workflow does
not use Team, Enterprise, Console/API keys, cloud providers, proxies, or custom
gateways. Managed settings can remain active even in Claude safe mode, so the
workflow stops when a managed policy is found or cannot be checked safely.
Check Anthropic's current official
[installation](https://code.claude.com/docs/en/installation) and
[authentication](https://code.claude.com/docs/en/authentication) guidance.

If you choose `yes`, Codex first checks for Claude Code. If installation is
needed, it explains the official source and exact action, then asks for
approval. Starting the Anthropic login is a second, separate approval. Claude
Code runs in a terminal, but you personally complete any password, passkey,
MFA, or OAuth step in the interactive terminal or browser that opens. Codex
pauses and does not inspect or capture the credentials screen. Never paste an
authentication code into chat, and do not use `claude setup-token` for this
beginner setup.

You do not need to understand terminal commands. On macOS, open **Terminal**
from Spotlight; on Windows, open **Terminal** or **PowerShell** from the Start
menu. Codex shows the exact `claude auth login` command for you to type and
waits while you complete the private sign-in screens yourself.

After login, Codex asks you to open Claude in safe mode and type `/status`
yourself. Look only at `Setting sources`, close Claude, and report whether an
`Enterprise managed settings` source appeared. Do not copy the rest of that
screen into chat. Setup and every later review stop unless you can confirm that
no such source was listed.

A successful login only makes Claude available; it does not permit a review
transmission. Before every review, the `claude-review` skill must identify
Anthropic as the provider, state the purpose, list the exact files, diff, or
text that would be sent, and ask for approval for that one review. You may
decline and continue normally. A Claude review is still an AI review, not a
verified proof.

### ChatGPT in the in-app Browser

This login is optional. The bundled `$pro-context-bundle` uses ChatGPT through
the in-app Browser for an explicitly requested Pro consultation. Choose `later`
if you do not plan to use that skill.

The in-app Browser is available only in supported macOS or Windows desktop
configurations. It can be unavailable because of product capability, plan, or
workspace policy, and it is unavailable on Linux. Its profile is separate from
your ordinary browser and other app sessions, so an existing ChatGPT login may
not carry over. See OpenAI's official
[Browser guide](https://help.openai.com/en/articles/20001277-using-the-built-in-browser-in-the-chatgpt-desktop-app).

If ChatGPT asks you to sign in, Codex pauses. You personally enter passwords,
passkeys, MFA responses, and OAuth codes; Codex does not inspect or screenshot
the credentials screen. Signing in only prepares the Browser profile. It does
not approve a file upload or message. Before each compatible skill sends
anything, Codex must show the provider, purpose, and exact outbound file or
text and ask for approval for that one action. After sending, the skill waits
without an overall time limit and selects `Answer now` only if you explicitly
request it during that consultation.

## 6. Confirm that setup finished

Codex will run a non-destructive check and explain:

- what is ready;
- what was intentionally skipped;
- which choices were postponed; and
- how to change a choice later.

It then gives a folder tour and a few first prompts. You can change one setting
later by saying, for example:

```text
Run setup again, but only help me configure Obsidian.
```

## If you are in a hosted or cloud environment

A cloud checkout is a copy running on another computer. It cannot install
Obsidian, TeX, or Claude Code on your own PC, prepare your desktop app's Browser
profile, inspect your local cloud-drive directories, or store this machine's
ignored preferences. It may still read and edit the Markdown framework
available in that checkout. The setup assistant should explain the limitation
and direct you to local desktop setup; it must not mark your local setup
complete.

## Privacy before research

Opening a local folder does not make Codex an offline program. The material
needed to answer a request may be sent to OpenAI for processing. Before using
unpublished referee reports, student or patient information, confidential
collaborations, export-controlled material, or other restricted content, check
your institution's policy and your account or workspace settings. OpenAI's
[Data Controls guide](https://help.openai.com/en/articles/7730893-data-controls-faq)
explains the controls available for ChatGPT accounts; organizational plans may
have different defaults and administrator rules.

## What setup will never do silently

It will not:

- install software;
- make research public;
- create or delete an online repository;
- change a Git remote;
- move the open workspace;
- write into an external drive;
- install community plugins in bulk;
- install Claude Code or start an Anthropic login;
- send research to Claude or ChatGPT without a new, exact outbound-content
  preview and per-use approval; or
- permanently delete research files.

Two authentication boundaries are absolute, not actions that can be approved:
setup never runs `claude setup-token`, and Codex never inspects or captures a
credentials screen. The user always completes authentication personally.

For a normal working routine, continue with [docs/daily-workflow.md](docs/daily-workflow.md).
Before applying a later release, read [docs/updating.md](docs/updating.md).
