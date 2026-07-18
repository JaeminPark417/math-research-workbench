# Contributing

Thank you for helping make Math Research Workbench safer and clearer for
mathematicians who may have no software-development experience.

## Before contributing

- For a small documentation correction, a GitHub issue or web-based edit is
  welcome.
- For a new workflow, schema change, installer, or folder reorganization, open
  an issue first and explain the beginner's problem it solves.
- Report security problems privately as described in [SECURITY.md](SECURITY.md),
  not in a public issue.

## Scope

Good contributions include:

- clearer beginner instructions;
- cross-platform diagnostic improvements;
- safe mathematics-oriented templates;
- accessibility and localization improvements; and
- tests that prevent personal data or unsafe defaults from entering a release.

This distribution intentionally excludes machine-learning experiment stacks,
training pipelines, GPUs, checkpoints, SSH/server configuration, private vault
content, and institution-specific material.

## Content rules

- Do not contribute private research, credentials, personal paths, or account
  identifiers.
- Do not invent papers, authors, theorems, DOIs, arXiv identifiers, quotations,
  or mathematical results.
- Do not contribute copyrighted PDFs or figures without redistribution rights.
- Use generic examples rather than real unpublished conjectures or drafts.
- Explain technical terms in plain language before using abbreviations.
- Make optional integrations genuinely skippable.
- Do not make a research repository public by default.
- Do not add bulk or silent software/plugin installation.

By submitting material, you represent that you have the right to contribute it
under this project's MIT License.

## Documentation style

- Write for a reader who has used ChatGPT but not Git or a terminal.
- Put the expected outcome before commands.
- Give one decision at a time and explain how to undo it.
- Use official, primary documentation for installation and account guidance.
- Avoid screenshots whose labels are likely to become stale; name the purpose
  of a control as well as its current label.

## Validation

Before submitting a pull request, run the available checks from the repository
root:

```text
python3 scripts/vault-lint.py
python3 scripts/validate-release.py
```

If a check cannot run on your computer, say so in the pull request. A maintainer
can help; lack of terminal experience should not prevent a documentation
contribution.

Keep each pull request focused. Describe what a beginner could not do before,
what changed, and how you verified the new behavior.
