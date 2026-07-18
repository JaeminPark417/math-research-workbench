# GitHub setup reference

Use this reference only after the user chooses GitHub. Explain every outcome in
plain language and keep the research repository private unless the user clearly
chooses otherwise after a publication-risk warning.

## Read-only checks

Run only available checks and summarize without exposing credentials:

```text
git rev-parse --is-inside-work-tree
git status --short
git remote
git config --get user.name
git config --get user.email
gh auth status
gh repo view --json nameWithOwner,visibility,url
```

`gh auth status` may identify the account but must not print a token. Never use
debug or verbose authentication output. Never print raw Git remote configuration
or run `git remote -v`: an HTTPS remote can contain a credential. Prefer the
canonical, credential-free URL returned by `gh repo view`. For a non-GitHub
remote, strip URL user information, query strings, and fragments before showing
the host and path; if safe redaction is uncertain, show only the remote name.

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

Inspect the remote owner and visibility. If it belongs to the user and is
private, keep it. If it is public, warn before any research is added and offer
to change visibility only after explicit approval.

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
included. Do not describe unsynchronized or ignored files as backed up. If
visibility is unknown, do not commit or push until it is confirmed private.
