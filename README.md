# Math Research Workbench

**A beginner-friendly Codex workspace for mathematical research.**

[한국어 안내](README.ko.md) · [Detailed setup](GETTING_STARTED.md)

Math Research Workbench helps mathematicians organize ideas, paper notes,
proof work, and projects in ordinary Markdown files. It is designed for people
who have used ChatGPT but have never used Git, a terminal, or a coding agent.
No programming experience is required.

This public repository contains only the reusable framework. It does **not**
contain anyone's research notes, personal paths, credentials, or experimental
machine-learning setup.

## Start here

The recommended route is a release ZIP. GitHub is optional.

1. On macOS or Windows, install the
   [ChatGPT desktop app](https://chatgpt.com/download/) and sign in. Linux users
   currently need the [Codex CLI](https://developers.openai.com/codex/cli/) and
   basic terminal familiarity.
2. Download the ZIP from the
   [latest release](https://github.com/JaeminPark417/math-research-workbench/releases/latest).
3. Extract it into a local folder that is **not** managed by iCloud Drive,
   OneDrive, Dropbox, or Google Drive. A folder named `MathResearch` directly
   inside your home folder is usually a good choice.
4. In the desktop app, select **Codex** and open the extracted folder.
5. Send this message:

   ```text
   Start setup
   ```

Opening a folder gives Codex access to the workspace, but it does not send a
message or begin setup by itself. You must send **Start setup** (or invoke
`$first-run`).

Codex then asks one question at a time about:

- a Python 3.9-or-newer helper runtime for safe saved setup and resume (Codex first uses an
  existing or bundled runtime; no programming is required);
- your preferred language;
- optional private GitHub backup for text files;
- optional storage for PDFs and other large files;
- optional Obsidian installation and plugins;
- Overleaf or optional local TeX compilation;
- optional Claude Code installation and Anthropic sign-in for Claude reviews;
- optional ChatGPT sign-in inside the in-app Browser for the bundled
  `$pro-context-bundle` consultation skill, when that Browser is available.

Python 3.9 or newer is used only for safe local setup-state checks; it is not a programming
requirement. Every service and editor integration is optional. Codex shows the
exact effect and asks for approval before installing software, changing an
account, creating a remote repository, or writing outside this folder.

For screen-by-screen instructions and a glossary, read
[GETTING_STARTED.md](GETTING_STARTED.md).

## What is inside?

| Folder | Purpose |
| --- | --- |
| `inbox/` | Unsorted material you want Codex to help classify |
| `ideas/` | Questions, conjectures, and evolving research directions |
| `papers/` | Bibliographic and reading notes; not copyrighted PDFs |
| `notes/` | Reusable definitions, lemmas, examples, and explanations |
| `projects/` | Active research, proof work, session notes, and drafts |
| `files/` | Local large-file fallback; excluded from GitHub by default |
| `meta/` | Conventions, schemas, safety rules, and templates |

## How project research stays organized

You can keep working exactly as you would in an ordinary conversation: ask questions, add information, test approaches, and solve the problem with Codex. For each active project, Codex maintains the project `README.md` as a compact **Research State Spine** so that the important mathematical state remains easy to recover.

The spine gives stable, paper- or decision-relevant objects explicit identifiers: `Def-NNN` for definitions, `Lem-NNN` for lemmas, `Prop-NNN` for propositions, `Thm-NNN` for theorems, `Cor-NNN` for corollaries, and `Gap-NNN` for unresolved gaps. These identifiers organize the work; they do not certify that a claim is true. A consequence receives a `Cor-NNN` identifier only when it has become a stable downstream consequence worth carrying into the paper or later decisions.

Exploratory calculations, temporary observations, failed approaches, and tentative consequences stay in `sessions/`, `logs/`, or `drafts/`. Codex promotes only the stable objects that matter to the paper or a research decision, and you do not need to edit the spine's tables by hand.

For example, you can simply ask:

```text
Keep researching this problem with me as usual. Update the project Research State Spine with any stable definition, lemma, proposition, theorem, corollary, or unresolved gap that matters to the paper, and leave scratch work in the logs or drafts.
```

The files remain readable without Codex or Obsidian. Obsidian is an optional
visual editor for the same Markdown files.

## Useful first requests

You can write naturally. For example:

```text
Put this research question into the inbox and help me formulate it precisely.
```

```text
Read this arXiv link, verify the bibliographic details, and create a paper note.
```

```text
Audit this proof. Separate established steps, gaps, and possible repairs.
Do not call it verified based only on your own review.
```

```text
Create a new project for this problem and explain every folder you create.
```

See [the daily workflow](docs/daily-workflow.md) for more examples.

## Important safety defaults

- Unpublished research repositories are **private by default**.
- GitHub is not an automatic backup. Only changes that have been committed and
  pushed appear there; ask Codex to explain and confirm each synchronization.
- The workbench repository should not live inside a cloud-sync folder. Use an
  external drive service for PDFs and other binaries instead.
- Codex never needs your password, access token, private key, or browser cookie
  pasted into chat.
- Claude Code and Claude are separate Anthropic services. Installation and
  sign-in each require approval and this bundled review uses only a direct
  personal Claude Pro or Max subscription login. Team, Enterprise, Console/API
  keys, cloud providers, proxies, and custom gateways need a different reviewed
  workflow. Because Claude safe mode does not disable managed policy, the
  workflow stops when policy is detected or cannot be ruled out and asks the
  user to confirm the CLI's policy-source screen before each review.
  Follow the official
  [installation](https://code.claude.com/docs/en/installation) and
  [authentication](https://code.claude.com/docs/en/authentication) guidance.
- Signing in is not permission to send research. Before every Claude review or
  Browser-based upload or message, Codex must name the provider, show the exact
  outbound files, diff, or text, and ask again for that one use. The bundled
  `$pro-context-bundle` waits for Pro to finish without an overall time limit
  and never selects `Answer now` unless the user explicitly asks during that
  consultation.
- Enter passwords, passkeys, MFA responses, and OAuth codes yourself. Codex
  pauses at credential screens and does not inspect or capture them.
- The project-provided LaTeX delimiter compatibility plugin is bundled inertly
  and requires separate consent, manual enabling, and a rendering test.
  Third-party community plugins remain optional; install them one at a time
  only after reading [the plugin guide](docs/obsidian-plugins.md).
- Obsidian can render mathematical notation without a local TeX installation.
  Overleaf is the simplest default for compiling manuscripts.
- A language-model review is not a proof. References and final mathematical
  claims require independent verification.
- A local folder does not make Codex an offline tool. Material needed for a
  request may be sent to OpenAI for processing. Check your institution's rules
  before using confidential collaboration, referee, student, patient, or
  restricted material, and review your account's
  [Data Controls](https://help.openai.com/en/articles/7730893-data-controls-faq).

## Local desktop versus cloud

On macOS or Windows, use the ChatGPT desktop app for the beginner first-run
flow. It can work with a local folder when you grant access. There is currently
no Linux desktop app; Linux users need the Codex CLI, which assumes some
terminal familiarity; follow the current
[official CLI guide](https://developers.openai.com/codex/cli/). A hosted
Codex/cloud checkout cannot install Obsidian or
TeX on your computer, inspect a local cloud-drive folder, or preserve this
machine's ignored setup file. In that situation the workbench remains usable as
Markdown, but Codex will point you back to the desktop setup guide instead of
pretending local setup is complete. See OpenAI's
[current desktop and Codex overview](https://help.openai.com/en/articles/20001275).

The optional in-app Browser is available only on supported macOS or Windows
desktop configurations, and its availability can depend on product capability,
plan, or workspace policy. It is unavailable on Linux. Its profile is separate
from your ordinary browser and other app sessions, so ChatGPT may ask you to
sign in again. The bundled `$pro-context-bundle` uses it; choose `later` if you
do not plan to use that skill. See the official
[Browser guide](https://help.openai.com/en/articles/20001277-using-the-built-in-browser-in-the-chatgpt-desktop-app).

On macOS or Windows, the Codex CLI is supported for experienced users but is
not required for the beginner desktop route.

## Help and project information

- [Detailed setup](GETTING_STARTED.md)
- [Obsidian guide](docs/obsidian.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Updating safely](docs/updating.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [License and content notice](CONTENT-NOTICE.md)

Math Research Workbench is an independent project and is not affiliated with
OpenAI, Anthropic, ChatGPT, Codex, Claude, Obsidian, GitHub, Overleaf, or any
cloud-storage provider.
