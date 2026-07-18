#!/usr/bin/env python3
"""Print only non-sensitive first-run state fields.

This deliberately avoids a general YAML dump because local configuration may
contain identifying repository and storage paths. It uses a small allowlisted
parser so it has no third-party dependencies.
"""

from __future__ import annotations

import os
import re
import stat
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / ".harness"
STATE = HARNESS / "local.yaml"
CURRENT_SETUP_VERSION = 2
SECTIONS = {
    "github",
    "external_storage",
    "obsidian",
    "tex",
    "claude_code",
    "chatgpt_browser",
}
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
    "claude_code.choice",
    "chatgpt_browser.choice",
)
ALLOWED = {
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
    "claude_code.choice": {"", "yes", "no", "later"},
    "chatgpt_browser.choice": {"", "yes", "no", "later"},
}
QUOTED_KEYS = set(ALLOWED) - {"status"}
LEGACY_REQUIRED_CHOICES = (
    "language",
    "github.choice",
    "external_storage.choice",
    "obsidian.choice",
    "tex.choice",
)
VERSION_2_REQUIRED_CHOICES = LEGACY_REQUIRED_CHOICES + (
    "claude_code.choice",
    "chatgpt_browser.choice",
)
COMMUNITY_PLUGIN_IDS = {
    "latex-suite",
    "zotero-integration",
    "dataview",
    "obsidian-git",
}
ISO_TIMESTAMP_WITH_ZONE = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})"
)
FORBIDDEN_DETAIL_KEYS = {
    "account",
    "account_id",
    "account_name",
    "api_key",
    "authenticated",
    "authentication",
    "auth_status",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "email",
    "email_address",
    "is_authenticated",
    "logged_in",
    "login_status",
    "org",
    "organization",
    "organization_id",
    "oauth_code",
    "password",
    "passphrase",
    "plan",
    "private_key",
    "recovery_code",
    "secret",
    "signed_in",
    "subscription",
    "tenant",
    "token",
    "access_token",
    "user",
    "user_id",
    "username",
    "workspace",
    "workspace_id",
}


def decode_scalar(key: str, raw: str) -> str | None:
    value = raw.strip()
    quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}
    decoded = value[1:-1] if quoted else value
    if key in QUOTED_KEYS and not quoted:
        return None
    return decoded if decoded in ALLOWED[key] else None


def is_valid_iso_timestamp(value: str) -> bool:
    if not ISO_TIMESTAMP_WITH_ZONE.fullmatch(value):
        return False
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.utcoffset() is not None


def is_valid_github_repository(value: str) -> bool:
    component = r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}"
    if re.fullmatch(rf"{component}/{component}", value):
        return True
    if value.startswith("git@github.com:"):
        path = value[len("git@github.com:") :]
    else:
        try:
            parsed = urlsplit(value)
            parsed_port = parsed.port
        except ValueError:
            return False
        if (
            parsed.scheme != "https"
            or (parsed.hostname or "").lower() != "github.com"
            or parsed.username is not None
            or parsed.password is not None
            or parsed_port is not None
            or parsed.query
            or parsed.fragment
        ):
            return False
        path = parsed.path.lstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    return bool(re.fullmatch(rf"{component}/{component}", path.strip("/")))


def is_forbidden_detail(key: str) -> bool:
    return (
        key in FORBIDDEN_DETAIL_KEYS
        or key.startswith(
            (
                "account_",
                "auth_",
                "credential_",
                "email_",
                "oauth_",
                "password_",
                "recovery_",
                "secret_",
                "user_",
            )
        )
        or key.endswith(("_credential", "_password", "_secret", "_private_key"))
        or key.endswith("_token")
        or key.endswith("_cookie")
    )


def print_fields(values: dict[str, str], invalid: set[str]) -> None:
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


def is_link_like(path: Path) -> bool:
    """Reject symlinks and Windows junctions without resolving their targets."""
    if path.is_symlink():
        return True
    is_junction = getattr(os.path, "isjunction", None)
    if is_junction and is_junction(path):
        return True
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(reparse_flag and attributes & reparse_flag)


def main() -> int:
    if is_link_like(HARNESS) or is_link_like(STATE):
        print("setup_state=invalid")
        print("setup_reason=unsafe_link")
        return 1
    if not STATE.exists():
        print("setup_state=missing")
        return 0
    if not STATE.is_file():
        print("setup_state=invalid")
        print("setup_reason=not_regular_file")
        return 1

    values: dict[str, str] = {}
    invalid: set[str] = set()
    details: dict[str, str] = {}
    invalid_structure = False
    section = ""
    seen_sections: set[str] = set()
    community_list = False
    community_plugins: set[str] = set()
    try:
        state_text = STATE.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        print("setup_state=unreadable")
        print("setup_reason=read_error")
        return 1

    for line in state_text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        any_key_match = re.match(r"\s*([a-z_][a-z0-9_]*):", line)
        if any_key_match and is_forbidden_detail(any_key_match.group(1)):
            invalid_structure = True
            community_list = False
            continue

        section_match = re.fullmatch(
            r"(github|external_storage|obsidian|tex|claude_code|chatgpt_browser):\s*",
            line,
        )
        if section_match:
            section = section_match.group(1)
            community_list = False
            if section in seen_sections:
                invalid_structure = True
            seen_sections.add(section)
            continue

        top_match = re.fullmatch(
            r"(setup_version|status|language|completed_at):\s*(.*?)\s*", line
        )
        if top_match:
            key, raw = top_match.groups()
            section = ""
            community_list = False
            if key in values:
                invalid.add(key)
                continue
            if key == "setup_version":
                version_text = raw.strip()
                if not re.fullmatch(r"[1-9][0-9]*", version_text):
                    invalid.add(key)
                else:
                    values[key] = version_text
                continue
            if key == "completed_at":
                value = raw.strip()
                quoted = (
                    len(value) >= 2
                    and value[0] == value[-1]
                    and value[0] in {'"', "'"}
                )
                values[key] = value[1:-1] if quoted else value
                continue
        else:
            if community_list:
                plugin_match = re.fullmatch(
                    r"    -\s*(?:(['\"])([a-z0-9-]+)\1|([a-z0-9-]+))\s*",
                    line,
                )
                if plugin_match:
                    plugin_id = plugin_match.group(2) or plugin_match.group(3)
                    if plugin_id not in COMMUNITY_PLUGIN_IDS or plugin_id in community_plugins:
                        invalid_structure = True
                    community_plugins.add(plugin_id)
                    continue
            nested_match = re.fullmatch(r"  ([a-z_][a-z0-9_]*):\s*(.*?)\s*", line)
            if not nested_match or section not in SECTIONS:
                invalid_structure = True
                community_list = False
                continue
            child, raw = nested_match.groups()
            community_list = False

            if section in {"claude_code", "chatgpt_browser"}:
                if child != "choice":
                    invalid_structure = True
                    continue
                key = f"{section}.choice"
            elif child in {"choice", "plugin_setup", "pending_plugin"}:
                if child in {"plugin_setup", "pending_plugin"} and section != "obsidian":
                    invalid_structure = True
                    continue
                key = f"{section}.{child}"
            else:
                allowed_detail = {
                    "github": {"repository", "visibility"},
                    "external_storage": {"provider", "root"},
                    "obsidian": {
                        "installed",
                        "plugin_profile",
                        "community_plugins",
                    },
                    "tex": {"engine"},
                }
                if child not in allowed_detail[section]:
                    invalid_structure = True
                    continue
                if child == "community_plugins":
                    detail_key = "obsidian.community_plugins"
                    if detail_key in details:
                        invalid_structure = True
                        continue
                    details[detail_key] = "present"
                    if raw.strip() == "":
                        community_list = True
                    elif raw.strip() != "[]":
                        invalid_structure = True
                    continue
                detail_key = f"{section}.{child}"
                if detail_key in details:
                    invalid_structure = True
                    continue
                detail_value = raw.strip().strip('"\'')
                if detail_key == "github.repository" and detail_value:
                    if not is_valid_github_repository(detail_value):
                        invalid_structure = True
                        continue
                if detail_key == "github.visibility":
                    detail_value = detail_value.casefold()
                    if detail_value not in {"", "private", "public", "internal"}:
                        invalid_structure = True
                        continue
                details[detail_key] = detail_value
                continue

        if key in values:
            invalid.add(key)
            continue
        decoded = decode_scalar(key, raw)
        if decoded is None:
            invalid.add(key)
        else:
            values[key] = decoded

    if "setup_version" not in values and "setup_version" not in invalid:
        invalid.add("setup_version")
    if "status" not in values and "status" not in invalid:
        invalid.add("status")
    if invalid_structure:
        invalid.add("<structure>")

    version = int(values["setup_version"]) if "setup_version" in values else None
    if version == 1:
        required_choices = LEGACY_REQUIRED_CHOICES
    elif version == CURRENT_SETUP_VERSION:
        required_choices = VERSION_2_REQUIRED_CHOICES
    else:
        # A future schema cannot be judged by version 2 completeness rules.
        required_choices = ()
    inconsistent = False
    if values.get("status") == "complete" and version in {
        1,
        CURRENT_SETUP_VERSION,
    }:
        inconsistent = any(not values.get(key) for key in required_choices)

    if version in {1, CURRENT_SETUP_VERSION}:
        if values.get("github.choice") == "yes":
            inconsistent = inconsistent or not all(
                details.get(key) for key in ("github.repository", "github.visibility")
            )
            if version == CURRENT_SETUP_VERSION:
                inconsistent = inconsistent or details.get("github.visibility") != "private"
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

    completed_at = values.get("completed_at")
    if values.get("status") == "complete" and version in {1, CURRENT_SETUP_VERSION}:
        if version == CURRENT_SETUP_VERSION:
            inconsistent = inconsistent or not completed_at or not is_valid_iso_timestamp(
                completed_at
            )
    elif values.get("status") == "in_progress" and completed_at:
        inconsistent = True

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
        state = "invalid"
        exit_code = 1
    elif inconsistent:
        state = "inconsistent"
        exit_code = 1
    elif version is not None and version > CURRENT_SETUP_VERSION:
        state = "unsupported"
        exit_code = 1
    elif version is not None and version < CURRENT_SETUP_VERSION:
        state = "outdated"
        exit_code = 0
    else:
        state = "ok"
        exit_code = 0

    print(f"setup_state={state}")
    if state == "invalid":
        print("setup_reason=invalid_content")
    elif state == "inconsistent":
        print("setup_reason=inconsistent_content")
    elif state == "unsupported":
        print("setup_reason=newer_version")
    print_fields(values, invalid)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
