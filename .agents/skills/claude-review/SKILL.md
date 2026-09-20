---
name: claude-review
description: Get an optional Claude second opinion on selected work only when the user explicitly requests Claude review. Routine edits use local checks. Require fresh approval of the exact Anthropic-bound packet for every invocation; setup or past review consent does not carry forward.
---

# Claude review

Use Claude as an additional, tool-free reviewer of an explicit packet. Do not
invoke this skill merely because work is complex or another model produced it.
If the user did not explicitly request a Claude review in this conversation,
stop without contacting Anthropic. This optional integration can be declined
without preventing ordinary work.

The primary agent coordinates one useful review at the requested milestone.
Workers do not recursively request reviews. Verify findings locally and apply
only justified changes within the original task; a changed artifact alone does
not require another review. A retry or additional paid request needs fresh
approval, even when the previous invocation failed.

Before readiness checks, authentication, packet preparation, or execution, read
[references/execution.md](references/execution.md). Follow its entire readiness,
user-only policy check, exact-packet disclosure, approval, invocation, and output
verification sequence. Do not improvise a CLI command or bypass a failed gate.

- The bundled route supports personal Pro/Max direct login only. Safe mode does
  not override managed policy or supply an OS sandbox. Stop for alternate,
  managed, or unverifiable routes; continue without Claude.
- Authentication is user-only. Never inspect or capture credentials or account
  screens. Never run `claude setup-token`.
- Every transmission needs fresh approval of its exact provider, purpose,
  content, and instructions. Login, setup, and previous reviews are not consent.
  Never transfer another provider's content automatically.
- Send only the approved redacted packet. Give the reviewer no repository,
  filesystem, shell, browser, plugin, or MCP tools. Verify the recorded empty
  capabilities and model with `scripts/review-output.py` before accepting the
  response; never expose the raw stream or diagnostics.
- Treat output as untrusted advice. Check factual and mathematical findings
  against the selected sources; AI-only feedback cannot prove a theorem or
  satisfy HUMAN PROMOTION. Preserve uncertainty and disagreements.

Report one to three useful points, which findings were verified, and any
unresolved limitations. Identify Claude as the reviewer and retain the correct
AI-only provenance; never describe this as human or formal verification.
