# Safety and trust boundaries

Math Research Workbench is an organizational aid. It does not replace the
researcher's mathematical judgment, source checking, backups, or informed
approval of changes to the computer.

## Mathematical claims

- Treat AI-generated mathematics as a draft until a human has checked it.
- Never label a theorem proved merely because an assistant produced a plausible
  argument.
- Keep assumptions, quantifiers, exceptional cases, and dependencies visible.
- Record gaps rather than smoothing them over.
- Preserve counterexamples and failed approaches.

## Human and formal review

- `human-reviewed` means a named human reviewed the scope documented in the
  note. It is not a universal guarantee beyond that scope.
- `formal-tool-checked` means a checker accepted the encoded statement under
  the recorded environment and assumptions.
- A checker cannot decide whether the encoded statement faithfully expresses
  the researcher's intended theorem.
- Use `human-and-formal` only when both events are documented. Do not infer it
  automatically from a successful tool result.
- An AI-only review must remain `unchecked`, even if several AI systems agree.

## Citations and sources

- Never invent a title, author, venue, year, theorem number, DOI, arXiv ID, URL,
  or quotation.
- Verify bibliographic data with an authoritative source before setting
  `citation_status: verified`.
- If access is unavailable, keep the lead with an explicit `unverified` label.
- Quote sparingly, preserve the original wording, and include the source.
- Clearly separate what a source says from the researcher's inference and the
  assistant's suggestion.

## Files and deletion

- Do not permanently delete user-authored notes, scans, drafts, or source
  material. Archive them instead.
- Before a broad rename, move, or rewrite, show the affected files and explain
  the expected change.
- Avoid overwriting substantial text when a reversible move or versioned edit
  is available.
- Keep PDFs, images, scans, and other binaries outside the Git-backed workspace
  by default. Store a safe link or portable reference in the related note.

## Privacy and sharing

- A public template repository does not imply that a researcher's own work
  should be public. When GitHub is enabled, private is the safe default for a
  personal research repository.
- Do not store passwords, access tokens, private keys, recovery codes, or
  confidential collaborator information in notes.
- Before publishing or sharing, review the full file list for unpublished work,
  personal paths, tracked binaries, and hidden configuration files.
- External-drive links should not expose credentials or private sharing tokens.

## External AI review and Browser sessions

- Claude Code and Claude are provided by Anthropic, separately from Codex,
  ChatGPT, and OpenAI. A Claude review creates a separate data flow to
  Anthropic under the user's Anthropic account and its current terms and data
  controls.
- Installing Claude Code, signing in to Anthropic, and sending a particular
  review are three separate choices. Approval for one does not approve the
  others. Never use `claude setup-token` during beginner setup.
- The bundled Claude review supports only a personal Pro or Max direct login.
  Safe mode does not override managed policy. Stop for Team, Enterprise,
  alternate routing or telemetry export, any detected policy source, an unverifiable policy check,
  or a user who cannot confirm that `/status` lists no enterprise-managed
  settings source for the current run.
- Before each external review, identify Anthropic as the provider, explain the
  purpose, and show the exact files, diff, or text proposed for transmission.
  Send only after the user approves that one review. Declining must leave the
  ordinary Codex workflow usable.
- A ChatGPT login inside the in-app Browser is separate from ordinary browser
  and app sessions. Availability can depend on the operating system, product
  capability, plan, and workspace policy; an unavailable Browser is not a
  setup failure.
- Pause at every password, passkey, MFA, or OAuth screen so the user can take
  control. Do not inspect, screenshot, record, or echo credentials or
  authentication codes.
- Signing in does not authorize an upload or message. Before every compatible
  Browser skill sends text or a file, show the exact outbound content,
  provider, destination, and purpose, then request per-use approval.
- A review by Claude or ChatGPT is still an AI-only review and must remain
  `unchecked` unless the required human or formal review is documented.

## Changes to the computer

- Explain installations and system changes in beginner-friendly language.
- Show the proposed action, expected effect, disk use when known, and recovery
  path before asking for approval.
- Do not install software, enable third-party extensions, connect accounts, or
  change repository visibility without explicit user approval.
- If a command fails, do not repeatedly retry potentially destructive actions.
  Inspect the state and explain the next safe option.
