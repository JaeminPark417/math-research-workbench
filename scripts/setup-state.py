#!/usr/bin/env python3
"""Print only non-sensitive first-run state fields.

This deliberately avoids a general YAML dump because local configuration may
contain identifying repository and storage paths.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / ".harness"
STATE = HARNESS / "local.yaml"
SECTIONS = {"github", "external_storage", "obsidian", "tex"}
ORDER = (
    "setup_version",
    "status",
    "language",
    "github.choice",
    "external_storage.choice",
    "obsidian.choice",
    "obsidian.plugin_setup",
    "obsidian.pending_plugin",
    "tex.choice",
)
ALLOWED = {
    "setup_version": {"1"},
    "status": {"in_progress", "complete"},
    "language": {"", "en", "ko"},
    "github.choice": {"", "yes", "no", "later"},
    "external_storage.choice": {"", "yes", "no", "later"},
    "obsidian.choice": {"", "yes", "no", "later"},
    "obsidian.plugin_setup": {"", "in_progress", "complete", "later"},
    "obsidian.pending_plugin": {
        "",
        "latex-suite",
        "zotero-integration",
        "dataview",
        "obsidian-git",
    },
    "tex.choice": {"", "overleaf", "local", "no", "later"},
}
QUOTED_KEYS = set(ORDER) - {"setup_version", "status"}


def decode_scalar(key: str, raw: str) -> str | None:
    value = raw.strip()
    quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}
    decoded = value[1:-1] if quoted else value
    if key in QUOTED_KEYS and not quoted:
        return None
    return decoded if decoded in ALLOWED[key] else None


def main() -> int:
    if HARNESS.is_symlink() or STATE.is_symlink():
        print("setup_state=invalid")
        return 1
    if not STATE.exists():
        print("setup_state=missing")
        return 0
    if not STATE.is_file():
        print("setup_state=invalid")
        return 1

    values: dict[str, str] = {}
    invalid: set[str] = set()
    details: dict[str, str] = {}
    section = ""
    try:
        state_text = STATE.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        print("setup_state=unreadable")
        return 1
    for line in state_text.splitlines():
        section_match = re.fullmatch(r"(github|external_storage|obsidian|tex):\s*", line)
        if section_match:
            section = section_match.group(1)
            continue
        top_match = re.fullmatch(r"(setup_version|status|language):\s*(.*?)\s*", line)
        if top_match:
            key, raw = top_match.groups()
        else:
            nested_match = re.fullmatch(r"  ([a-z_]+):\s*(.*?)\s*", line)
            if not nested_match or section not in SECTIONS:
                continue
            child, raw = nested_match.groups()
            if child in {"choice", "plugin_setup", "pending_plugin"}:
                if child in {"plugin_setup", "pending_plugin"} and section != "obsidian":
                    continue
                key = f"{section}.{child}"
            else:
                allowed_detail = {
                    "github": {"repository", "visibility"},
                    "external_storage": {"provider", "root"},
                    "obsidian": {"installed", "plugin_profile"},
                    "tex": {"engine"},
                }
                if child not in allowed_detail[section]:
                    continue
                detail_key = f"{section}.{child}"
                detail_value = raw.strip().strip('"\'')
                details[detail_key] = detail_value
                continue
        decoded = decode_scalar(key, raw)
        if decoded is None:
            invalid.add(key)
        else:
            values[key] = decoded

    required_choices = (
        "language",
        "github.choice",
        "external_storage.choice",
        "obsidian.choice",
        "tex.choice",
    )
    inconsistent = False
    if values.get("status") == "complete":
        inconsistent = any(not values.get(key) for key in required_choices)
        if values.get("github.choice") == "yes":
            inconsistent = inconsistent or not all(
                details.get(key) for key in ("github.repository", "github.visibility")
            )
        if values.get("external_storage.choice") == "yes":
            inconsistent = inconsistent or not all(
                details.get(key)
                for key in ("external_storage.provider", "external_storage.root")
            )
        if values.get("obsidian.choice") == "yes":
            inconsistent = inconsistent or values.get("obsidian.plugin_setup") not in {
                "complete",
                "later",
            }
            inconsistent = inconsistent or details.get("obsidian.installed") != "true"
            inconsistent = inconsistent or not details.get("obsidian.plugin_profile")
        if values.get("tex.choice") == "local":
            inconsistent = inconsistent or not details.get("tex.engine")

    plugin_setup = values.get("obsidian.plugin_setup", "")
    pending_plugin = values.get("obsidian.pending_plugin", "")
    if plugin_setup == "in_progress" and not pending_plugin:
        inconsistent = True
    if pending_plugin and plugin_setup not in {"in_progress", "later"}:
        inconsistent = True
    if values.get("obsidian.choice") not in {"", "yes"} and (
        plugin_setup or pending_plugin
    ):
        inconsistent = True

    if invalid:
        print("setup_state=invalid")
    elif inconsistent:
        print("setup_state=inconsistent")
    else:
        print("setup_state=ok")

    for key in ORDER:
        if key in invalid:
            display = "<invalid-or-unquoted>"
        elif key not in values:
            display = "<missing>"
        elif values[key] == "":
            display = "<unanswered>"
        else:
            display = values[key]
        print(f"{key}={display}")
    return 1 if invalid or inconsistent else 0


if __name__ == "__main__":
    sys.exit(main())
