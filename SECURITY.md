# Security policy

## Supported version

Security fixes target the latest published release. Users should update to the
latest release after reviewing its notes and following
[the safe update guide](docs/updating.md).

## Report a vulnerability privately

Please do not disclose a vulnerability in a public issue. Use the repository's
[private security advisory form](https://github.com/JaeminPark417/math-research-workbench/security/advisories/new).

Include:

- the affected release or commit;
- the operating system and Codex surface;
- the smallest reproduction you can provide without private research;
- the impact you believe is possible; and
- a safe proposed fix, if you have one.

Do not send passwords, tokens, private keys, cookies, or confidential research.
If a credential has been exposed, revoke or rotate it with the relevant
provider first.

## Security-sensitive areas

Reports are especially useful for:

- a setup step that can run without explicit consent;
- command or path injection in a script;
- writing outside the selected workspace or external-storage folder;
- accidental publication of a private repository;
- an external AI review, Browser upload, or message that can occur without a
  per-use preview and explicit approval;
- capture, display, storage, or logging of a password, passkey, MFA response,
  OAuth code, token, cookie, or authentication screen;
- unsafe handling of untrusted TeX, PDFs, web pages, or pasted instructions;
- a release that includes credentials, personal paths, or private content; and
- destructive Git or file operations.

## Boundaries

OpenAI, Anthropic, ChatGPT, Codex, Claude, Claude Code, GitHub, Obsidian, TeX
distributions, cloud-storage services, and community plugins are separate
projects and vendors. Math Research Workbench is not affiliated with or
endorsed by them. A Claude review sends only the material separately approved
for that review as model input after route and managed-policy gates; a
compatible in-app Browser skill sends only the
separately approved upload or message to its stated provider. Signing in is
not consent to either data flow.

Report defects in those third-party products to their maintainers. Please also
notify this project privately when our guidance or integration makes such a
defect more dangerous. Do not include account credentials, authentication
screens, or private research in either report.

Until a fix is available, stop the affected setup step, keep the repository
private, disconnect the relevant integration if safe, and preserve files for
recovery. Do not run destructive cleanup commands.
