#!/usr/bin/env python3
"""Verify a Claude stream locally; never contact a provider or print raw metadata."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

OPUS_MODEL = re.compile(r"claude-opus-[0-9][A-Za-z0-9.-]*")
HAIKU_MODEL = re.compile(r"claude-haiku-[0-9][A-Za-z0-9.-]*")


class ReviewError(ValueError):
    pass


def _reject_tool_events(value: object) -> None:
    """Inspect structured events, never strings that may merely discuss tools."""
    pending = [value]
    while pending:
        current = pending.pop()
        if isinstance(current, list):
            pending.extend(current)
        elif isinstance(current, dict):
            kind = current.get("type")
            subtype = current.get("subtype")
            # Covers tool_use, server_tool_use, tool_result, tool_progress,
            # tool_use_summary, stream-event blocks, and provider extensions.
            if any(isinstance(label, str) and any(marker in label.lower() for marker in ("tool", "hook", "function_call"))
                   for label in (kind, subtype)):
                raise ReviewError("review contained a tool or hook event")
            if any(key in current and current[key] is not None for key in (
                    "tool_use_id", "parent_tool_use_id", "tool_call_id", "tool_calls", "tool_call", "tool_name", "function_call")):
                raise ReviewError("review contained a tool-call reference")
            pending.extend(current.values())


def verify_output(path: Path) -> dict:
    """Validate observable capabilities/model labels, not endpoint attestation."""
    initialized = False
    session_id = None
    primary_model = None
    assistant_text = []
    final = None
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict) or not isinstance(item.get("type"), str):
            raise ReviewError("review stream contains a malformed event")
        if item["type"] not in {"system", "assistant", "result", "rate_limit_event"}:
            raise ReviewError("review stream contains an unknown event type")
        if item["type"] == "system" and item.get("subtype") not in {"init", "thinking_tokens", "status", "api_retry"}:
            raise ReviewError("review stream contains an unknown system event")
        _reject_tool_events(item)
        if final is not None:
            raise ReviewError("review stream contains events after its final result")
        if item.get("type") == "system" and item.get("subtype") == "init":
            if initialized:
                raise ReviewError("review stream contains multiple initialization events")
            initialized = True
            for field in ("tools", "mcp_servers", "skills", "plugins"):
                if field not in item or not isinstance(item[field], list) or item[field] != []:
                    raise ReviewError(f"review did not explicitly report empty {field}")
            primary_model = item.get("model")
            if not isinstance(primary_model, str) or not OPUS_MODEL.fullmatch(primary_model):
                raise ReviewError("review did not initialize an identifiable Claude Opus primary model")
            session_id = item.get("session_id")
            if session_id is not None and (not isinstance(session_id, str) or not session_id):
                raise ReviewError("review stream contains an invalid session identifier")
        elif not initialized:
            raise ReviewError("review stream did not initialize before emitting output")
        if session_id is not None and "session_id" in item and item["session_id"] != session_id:
            raise ReviewError("review stream contains mismatched session identifiers")
        if item.get("type") == "assistant":
            message = item.get("message")
            if not isinstance(message, dict) or not isinstance(message.get("content"), list):
                raise ReviewError("review contains a malformed assistant message")
            if "model" in message and message["model"] != primary_model:
                raise ReviewError("assistant model contradicts the initialized primary model")
            for block in message["content"]:
                if (not isinstance(block, dict) or not isinstance(block.get("type"), str)
                        or block["type"] not in {"text", "thinking", "redacted_thinking"}):
                    raise ReviewError("review contains an unknown or malformed assistant content block")
                if block["type"] == "text":
                    if not isinstance(block.get("text"), str):
                        raise ReviewError("review contains a malformed assistant text block")
                    if block["text"].strip():
                        assistant_text.append(block["text"])
        if item.get("type") == "result":
            if session_id is not None and item.get("session_id") != session_id:
                raise ReviewError("final result does not identify the initialized session")
            if (item.get("subtype") != "success" or item.get("is_error") is not False
                    or not isinstance(item.get("result"), str) or not item["result"].strip()
                    or not isinstance(item.get("modelUsage"), dict) or not item["modelUsage"]):
                raise ReviewError("review did not produce a well-formed successful result")
            if primary_model not in item["modelUsage"]:
                raise ReviewError("final usage does not include the initialized Opus primary model")
            for model, usage in item["modelUsage"].items():
                if (not isinstance(model, str) or not isinstance(usage, dict)
                        or (model != primary_model and not HAIKU_MODEL.fullmatch(model))):
                    raise ReviewError("final usage contains an unexpected model label or malformed usage")
            final = item
    if not initialized or final is None:
        raise ReviewError("review did not produce a verified successful tool-free result")
    # Claude's result may repeat only the final text segment. Prefer the ordered
    # complete assistant text; never append result and duplicate its last part.
    result = "\n\n".join(assistant_text) if assistant_text else final["result"]
    return {"tool_free": True, "primary_model": primary_model, "result": result,
            "model_usage": list(final["modelUsage"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        result = verify_output(args.path)
    except (OSError, UnicodeError, ValueError):
        # Raw events and exception details may contain account fields or paths.
        print("review_output=unverified", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
