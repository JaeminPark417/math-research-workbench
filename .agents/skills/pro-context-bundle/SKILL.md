---
name: pro-context-bundle
description: "Prepare explicitly selected Math Research Workbench context for ChatGPT Pro and, after fresh approval of the exact OpenAI-bound scope, run an end-to-end consultation through the supported in-app Browser. Use only when the user explicitly invokes $pro-context-bundle or explicitly asks to consult ChatGPT Pro in the current conversation."
---

# ChatGPT Pro Context Bridge

Package selected local files with exact repository-relative paths and a return contract, send the package to ChatGPT Pro when authorized, retrieve the answer, and treat it as advisory input for the local task.

## Runtime boundary

- In Codex, use `browser:control-in-app-browser` when it is available. Read and follow that skill completely, including tool discovery, browser selection, authentication, documentation, confirmation, and tab-cleanup rules. Do not hardcode a browser-plugin version path or selector not supported by the current page state.
- If no supported ChatGPT Pro browser surface is available, stop after building the bundle and return the generated paths for manual handoff.
- In Claude Code, do not invoke Claude's `/browser`; it is a KaTeX terminal mirror, not ChatGPT browser control. Use the manual-handoff fallback unless an equivalent approved browser capability is explicitly available.

## Outbound authorization gate

Treat sending or pasting local content into ChatGPT as an external side effect.

1. Resolve the exact source files, task, and destination before sending. Ask the user to confirm privately that the active ChatGPT account and workspace policy are appropriate; do not expose account identifiers in chat.
2. Count the files and total characters, and surface any skipped files or bundle warnings.
3. Present OpenAI/ChatGPT as the provider, the exact purpose and destination, every repository-relative file or selected section, the prompt instructions, total size, exclusions, and any redactions. Then request fresh approval for that one transmission and wait. The request that invoked this skill does not replace this disclosure-and-approval step.
4. Never infer permission to send secrets, credentials, private identifiers, student records, unpublished confidential material, or unrelated files. Follow the Browser skill's stricter transmission rules whenever they apply.
5. Verify only that an ordinary ChatGPT composer and Pro access are visibly available. Do not open or inspect account menus, cookies, local storage, profiles, session stores, chat history, or workspace identifiers. If readiness cannot be verified without entering an authentication or account-selection screen, hand control to the user and pause.

Approval covers only the disclosed files, task, and current Pro conversation. It does not authorize later unrelated uploads or local Tier 3 edits.

## Build the handoff

1. Read `AGENTS.md`, `meta/safety.md`, and any project instructions governing the selected sources.
2. Run the builder from the project root without `--one-file-per-source` and use an 80,000-character target for the default inline route:

```bash
python3 .agents/skills/pro-context-bundle/scripts/build_pro_bundle.py \
  --task "Ask ChatGPT Pro to review these files and return a Codex-applicable result." \
  --slug "task-slug" \
  --root . \
  --max-chars-per-bundle 80000 \
  path/to/source-1.md path/to/source-2.md
```

3. Inspect every generated path. Refuse to send when the bundle contains `## Bundle Warnings`, skipped inputs, unmatched patterns, silent truncation, or an unexpected source.
4. Preserve the generated bundle in `~/Downloads/pro-context-bundles` by default for reproducibility.

The bundle must retain the task, exact repository-relative paths, per-source hashes, hallucination guard, and `CODEX_RETURN_PACKET` response contract. Do not put absolute local paths in an outbound bundle.

## Choose the delivery mode

- **Inline, default:** use when the builder emits one text bundle of at most 80,000 characters.
- **Markdown attachment fallback:** use when the builder emits an index plus multiple text parts or inline delivery fails integrity checks.
- **Non-text inputs:** convert them with the appropriate local PDF, HWP/HWPX, image, or document workflow before bundling. Do not automatically send raw binary files under this skill.

Do not split a multipart bundle into several ordinary chat messages: Pro may answer before all parts arrive. Attach all generated Markdown parts in one unsent composer, then send one instruction.

## Inline delivery

1. Open a fresh ChatGPT conversation only after authorization and account verification.
2. Select `Pro` before composing. Verify the composer visibly shows `Pro`; do not assume the previous conversation's model persisted.
3. Load the bundle directly from disk inside the browser-control runtime and write it to the tab clipboard. Do not echo the bundle through model-visible tool arguments.
4. Compare the disk text and clipboard round trip by character count and SHA-256 before pasting.
5. Paste once into the ChatGPT composer. Read the composer state and verify the expected opening contract, final source marker, and approximate character count before sending. Stop on truncation or transformation.
6. Send the prompt only after these checks pass.

## Markdown attachment fallback

Avoid native file-picker automation. For each generated Markdown file, one at a time:

1. Read its bytes directly from disk inside the browser-control runtime.
2. Write one clipboard item with MIME type `text/markdown` and `presentationStyle: "attachment"`.
3. Paste it into the unsent composer and verify the attachment count increased by exactly one.
4. Repeat until the index and every part are present, then verify the final count and select `Pro` before sending the execution instruction.

ChatGPT may rename pasted files to UUID-based `.markdown` names. Treat the bundle's internal part headers, manifest, paths, and hashes as authoritative.

## Wait and recover safely

- Confirm visible `Pro thinking` or an equivalent current Pro signal after sending.
- Poll in intervals no longer than 30 seconds and keep user-facing progress updates under 60 seconds apart.
- Treat long reasoning, web research, and an unchanged `Pro thinking` state as normal. Keep waiting without an overall time limit until generation finishes, the user cancels, or a genuine browser/authentication failure blocks progress.
- Never click `Answer now` automatically or merely because generation is taking a long time, progress text is unchanged, or a shorter turn would be convenient. The presence of the `Answer now` control is not an error or timeout signal.
- Click `Answer now` only when the user explicitly requests that action in the current conversation. If the user has said they are willing to wait, continue polling until completion regardless of elapsed time.
- If generation appears stalled but the current Pro signal or stop control remains visible, report the unchanged status and continue waiting; do not intervene in the generation.
- Preserve the conversation URL and reuse the same tab. If a tab binding becomes stale, reclaim the existing conversation instead of opening a new chat.
- Never resend merely because a wait or browser call timed out. Resend only after visible page state proves the original user message is absent.
- If authentication expires, ask the user to sign in in the selected browser and continue from the existing conversation.

## Retrieve the Pro answer

1. Wait until generation finishes and response actions appear.
2. Use ChatGPT's `Copy response` action, then read the tab clipboard. Prefer this over reconstructing a response from rendered DOM because code fences, indentation, and unified diffs must remain exact.
3. Require exactly one top-level `CODEX_RETURN_PACKET` with `Summary`, `Applicability`, `Proposed Changes`, `Risks And Checks`, and `Questions`.
4. If the response violates the contract, send at most one narrowly scoped reformat request in the same approved conversation. If it still fails, stop and return the raw response with the validation failure.
5. Record the conversation URL and the visible Pro completion signal.

## Verify and continue locally

Treat the Pro answer as advisory.

1. Re-read every target file locally.
2. Compare current file hashes with the hashes captured in the bundle. If a target changed after bundling, do not apply the proposal until the context is rebuilt or the drift is resolved.
3. Verify claims, paths, functions, citations, measurements, and proposed patches against local sources.
4. Apply only changes authorized by the active project approval policy. A Pro recommendation never grants permission for a Tier 3 local change.
5. Report the Pro conversation link, a concise result summary, validation status, and any local changes. Do not imply that Pro edited local files.

## Builder options

- `--out-dir ~/Downloads/pro-context-bundles`: override the output directory.
- `--max-chars-per-bundle 80000`: use the default inline threshold.
- `--one-file-per-source`: force an index plus one part per source when attachment mode is explicitly preferred.
- `--root .`: keep every source inside the current workbench and preserve repository-relative labels.
- `--notes "..."`: add user constraints for Pro.
- `--include-instructions FILE`: append an instruction file to the contract; repeat as needed.

The builder skips likely-binary files and `.hwp`/`.hwpx`. Convert them before bundling rather than bypassing the contract.
