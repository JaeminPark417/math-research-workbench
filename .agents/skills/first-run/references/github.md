# GitHub setup reference

Use this reference only after the user chooses GitHub. Explain every outcome in
plain language. This beginner backup flow requires a repository whose verified
visibility is exactly `private`; publishing research is a separate workflow.

## Read-only checks

Use the workbench's redacted helpers and summarize outcomes without exposing
credentials or account identifiers:

```text
bash scripts/doctor.sh                         # macOS/Linux
powershell -NoProfile -File scripts/doctor.ps1 # Windows
python3 scripts/remote-state.py
```

The doctor suppresses Git author and GitHub authentication values and reports
only whether they are configured. Never run an unsuppressed `git config --get
user.name`, `git config --get user.email`, or `gh auth status`. Never print raw
Git remote configuration or run `git remote -v`: an HTTPS remote can contain a
credential. `remote-state.py` reports only a redacted origin class and verified
visibility. If a new repository needs an owner name, ask the user to type the
GitHub owner they intend to use; do not discover it from raw authentication
output.

After GitHub setup is explicitly selected, `git status --short` and `git
remote` may be used to show the relative tracked-file state and remote names;
neither command prints a remote URL. Use `gh repo view` only with output limited
to the user-approved repository's `visibility` after its owner/name is already
known. Do not request `nameWithOwner`, a raw URL, or account fields.

## Acquisition cases

### Release ZIP: no Git repository

1. Explain that a private GitHub repository will back up Markdown and history.
2. Verify `git` and `gh`. If missing, use the official installation guide for
   the detected OS and get approval before installing.
3. Ask for the repository name and confirm the GitHub owner.
4. Show the exact private target and proposed commands.
5. Before the first commit, show the complete proposed tracked-file list. Stop
   if it contains research PDFs, office documents, archives, media, credentials,
   personal paths, or private hidden configuration. Do not bypass `.gitignore`
   with a force-add.
6. After approval, initialize `main`, configure identity if needed, create the
   first commit, and create the remote with an explicit private flag.
7. Report the final URL and verify its visibility through GitHub.

### GitHub template: personal remote already present

Inspect the remote owner and visibility. If it belongs to the user and reports
exactly `private`, keep it. For `public`, `internal`, or `unknown`, warn before
any research is added and offer to create or select a private destination.
GitHub's `internal` visibility may expose a repository across an organization;
it is not a private research backup. Change visibility only after explicit
approval.

### GitHub template: private repository downloaded as a ZIP

A ZIP has no Git connection, even if it came from the user's private template
repository. Do not create a second repository or silently attach the extracted
files. Before research begins, recommend cloning the existing private
repository with GitHub Desktop into a new safe local folder. Preserve any work
already added to the ZIP copy and preview a separate, approved copy operation
only if it must be transferred into the clone.

### Clone of the public distribution repository

The public remote is a source for harness updates, not a research destination.
Before changing it, show:

- current `origin` classification and a credential-free canonical URL only when
  `gh repo view` can provide one;
- proposed `upstream` URL;
- proposed new private `origin` URL;
- rollback: rename `upstream` back to `origin` if the new origin was not made.

Obtain approval, then rename the distribution remote to `upstream` and create a
separate private research repository as `origin`. Recheck both URLs.

## Installation and authentication

Use current official documentation rather than remembered package identifiers:

- Git: <https://git-scm.com/downloads>
- GitHub CLI: <https://cli.github.com/>
- GitHub authentication: <https://cli.github.com/manual/gh_auth_login>

Prefer browser/device authentication. Do not ask the user to paste a personal
access token into chat, a note, a command argument, or a configuration file.

## Prohibited operations

Never force-push, amend published commits, rewrite history, run destructive
reset or clean commands, delete a remote or repository, or change visibility
without a separate explanation and approval. A setup failure must leave the
local research files intact.

## Synchronization is explicit

GitHub does not automatically receive local edits. Only committed and pushed
changes appear online. Before each first-run synchronization, explain the file
list, verify that the destination is the user's private research repository,
and obtain approval. Also inspect Markdown links and embeds plus `files/` for
ignored attachments, and list the relative attachments that will **not** be
included. Do not describe unsynchronized or ignored files as backed up. Unless
visibility reports exactly `private`, do not commit or push research.
