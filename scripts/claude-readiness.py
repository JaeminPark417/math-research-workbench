#!/usr/bin/env python3
"""Classify Claude review readiness without exposing account information."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


ROUTE_OVERRIDE_ENV = {
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_FOUNDRY",
    "CLAUDE_CODE_USE_MANTLE",
    "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_ENABLE_TELEMETRY",
    "ANTHROPIC_CUSTOM_HEADERS",
    "CLAUDE_CODE_CLIENT_CERT",
    "CLAUDE_CODE_CLIENT_KEY",
    "CLAUDE_CODE_CLIENT_KEY_PASSPHRASE",
    "CLAUDE_CODE_EXTRA_CA_CERTS",
    "HTTPS_PROXY",
    "HTTP_PROXY",
    "ALL_PROXY",
    "https_proxy",
    "http_proxy",
    "all_proxy",
    "NODE_EXTRA_CA_CERTS",
    "NODE_TLS_REJECT_UNAUTHORIZED",
    "SSL_CERT_FILE",
}
REQUIRED_REVIEW_FLAGS = {
    "--disable-slash-commands",
    "--disallowedTools",
    "--input-format",
    "--no-chrome",
    "--no-session-persistence",
    "--output-format",
    "--permission-mode",
    "--safe-mode",
    "--settings",
    "--strict-mcp-config",
    "--system-prompt",
    "--tools",
}


def classify_status(
    payload: Any,
    route_override_present: bool,
    managed_policy_state: str,
) -> str:
    """Fail closed unless this is an unmanaged personal subscription route."""
    if route_override_present:
        return "alternate_or_unknown_route"
    if not isinstance(payload, dict) or payload.get("loggedIn") is not True:
        return "not_authenticated"
    if not (
        payload.get("authMethod") == "claude.ai"
        and payload.get("apiProvider") == "firstParty"
    ):
        return "alternate_or_unknown_route"
    subscription_type = payload.get("subscriptionType")
    if not isinstance(subscription_type, str) or subscription_type.casefold() not in {
        "pro",
        "max",
    }:
        return "ineligible_or_managed_subscription"
    if managed_policy_state == "present":
        return "managed_policy_present"
    if managed_policy_state != "absent":
        return "managed_policy_unverifiable"
    return "ready"


def has_review_capabilities(help_text: str) -> bool:
    return all(flag in help_text for flag in REQUIRED_REVIEW_FLAGS)


def has_route_or_telemetry_override(environ: Mapping[str, str]) -> bool:
    """Reject alternate routing, TLS interception, and prompt/body exporters."""
    return any(environ.get(name) for name in ROUTE_OVERRIDE_ENV) or any(
        name.startswith("OTEL_") and bool(value) for name, value in environ.items()
    )


def run_captured(*args: str) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            args,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="strict",
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return None


def path_state(path: Path) -> str:
    """Return present/absent/unknown without reading or resolving the target."""
    try:
        return "present" if os.path.lexists(path) else "absent"
    except OSError:
        return "unknown"


def combine_policy_states(states: list[str]) -> str:
    if "present" in states:
        return "present"
    if "unknown" in states:
        return "unknown"
    return "absent"


def windows_registry_policy_state() -> str:
    try:
        import winreg
    except ImportError:
        return "unknown"

    states: list[str] = []
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            key = winreg.OpenKey(hive, r"SOFTWARE\Policies\ClaudeCode")
        except FileNotFoundError:
            states.append("absent")
        except OSError:
            states.append("unknown")
        else:
            key.Close()
            states.append("present")
    return combine_policy_states(states)


def wsl_windows_policy_state() -> str:
    powershell = shutil.which("powershell.exe")
    if not powershell:
        return "unknown"
    script = (
        "$ErrorActionPreference='Stop'; "
        "$keys=@('Registry::HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\ClaudeCode',"
        "'Registry::HKEY_CURRENT_USER\\SOFTWARE\\Policies\\ClaudeCode'); "
        "$files=@('C:\\Program Files\\ClaudeCode\\managed-settings.json',"
        "'C:\\Program Files\\ClaudeCode\\managed-settings.d',"
        "'C:\\Program Files\\ClaudeCode\\managed-mcp.json'); "
        "if (($keys + $files | Where-Object { Test-Path -LiteralPath $_ }).Count) "
        "{ 'present' } else { 'absent' }"
    )
    result = run_captured(
        powershell,
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        script,
    )
    if result is None or result.returncode != 0:
        return "unknown"
    answer = result.stdout.strip().casefold()
    return answer if answer in {"present", "absent"} else "unknown"


def managed_policy_state() -> str:
    home = Path.home()
    states = [path_state(home / ".claude" / "remote-settings.json")]
    system_name = platform.system()

    if system_name == "Darwin":
        base = Path("/Library/Application Support/ClaudeCode")
        states.extend(
            path_state(base / name)
            for name in (
                "managed-settings.json",
                "managed-settings.d",
                "managed-mcp.json",
            )
        )
        states.extend(
            [
                path_state(
                    Path("/Library/Managed Preferences/com.anthropic.claudecode.plist")
                ),
                path_state(Path("/Library/Preferences/com.anthropic.claudecode.plist")),
            ]
        )
        defaults = shutil.which("defaults")
        if not defaults:
            states.append("unknown")
        else:
            result = run_captured(defaults, "read", "com.anthropic.claudecode")
            if result is None:
                states.append("unknown")
            elif result.returncode == 0:
                states.append("present")
            else:
                # A missing domain is the normal unmanaged result. The user
                # must still perform the documented interactive /status check.
                states.append("absent")
    elif system_name == "Linux":
        base = Path("/etc/claude-code")
        states.extend(
            path_state(base / name)
            for name in (
                "managed-settings.json",
                "managed-settings.d",
                "managed-mcp.json",
            )
        )
        try:
            release = Path("/proc/sys/kernel/osrelease").read_text(
                encoding="utf-8", errors="ignore"
            )
        except OSError:
            release = ""
        if "microsoft" in release.casefold():
            states.append(wsl_windows_policy_state())
    elif system_name == "Windows":
        program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        base = program_files / "ClaudeCode"
        states.extend(
            path_state(base / name)
            for name in (
                "managed-settings.json",
                "managed-settings.d",
                "managed-mcp.json",
            )
        )
        states.append(windows_registry_policy_state())
    else:
        states.append("unknown")

    return combine_policy_states(states)


def main() -> int:
    if not shutil.which("claude"):
        print("claude_readiness=missing")
        return 1

    help_result = run_captured("claude", "--help")
    if (
        help_result is None
        or help_result.returncode != 0
        or not has_review_capabilities(help_result.stdout)
    ):
        print("claude_readiness=incompatible_cli")
        return 1

    route_override_present = has_route_or_telemetry_override(os.environ)
    policy_state = managed_policy_state()
    status_result = run_captured("claude", "--safe-mode", "auth", "status")
    if status_result is None:
        print("claude_readiness=check_failed")
        return 1
    if status_result.returncode != 0:
        print("claude_readiness=not_authenticated")
        return 1

    try:
        payload = json.loads(status_result.stdout)
    except (json.JSONDecodeError, TypeError):
        print("claude_readiness=unrecognized_status")
        return 1

    classification = classify_status(payload, route_override_present, policy_state)
    print(f"claude_readiness={classification}")
    return 0 if classification == "ready" else 1


if __name__ == "__main__":
    sys.exit(main())
