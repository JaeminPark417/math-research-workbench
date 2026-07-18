#!/usr/bin/env python3
"""Atomically add version 2 choices without printing private setup details."""

from __future__ import annotations

import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / ".harness"
STATE = HARNESS / "local.yaml"
BACKUP = HARNESS / "local.v1-backup.yaml"
SETUP_STATE = ROOT / "scripts" / "setup-state.py"
REMOTE_STATE = ROOT / "scripts" / "remote-state.py"


def is_link_like(path: Path) -> bool:
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


def safe_state_classification() -> tuple[str, dict[str, str]] | None:
    try:
        result = subprocess.run(
            [sys.executable, str(SETUP_STATE)],
            cwd=ROOT,
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
    if result.returncode != 0:
        return None
    fields: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in {
            "setup_state",
            "setup_version",
            "status",
            "language",
            "github.choice",
            "external_storage.choice",
            "obsidian.choice",
            "tex.choice",
        }:
            fields[key] = value
    return fields.get("setup_state", ""), fields


def safe_remote_visibility() -> str:
    try:
        result = subprocess.run(
            [sys.executable, str(REMOTE_STATE)],
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="strict",
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return "unknown"
    if result.returncode != 0:
        return "unknown"
    answers = [
        line.split("=", 1)[1]
        for line in result.stdout.splitlines()
        if line.startswith("visibility=")
    ]
    return answers[0] if len(answers) == 1 else "unknown"


def build_migrated_text(source: str, verified_private_remote: bool) -> str | None:
    lines = source.splitlines()
    version_indexes = [
        index
        for index, line in enumerate(lines)
        if re.fullmatch(r"setup_version:\s*1\s*", line)
    ]
    status_indexes = [
        index
        for index, line in enumerate(lines)
        if re.fullmatch(
            r"status:\s*(['\"]?)(?:complete|in_progress)\1\s*", line
        )
    ]
    if len(version_indexes) != 1 or len(status_indexes) != 1:
        return None
    if any(
        line.startswith(("claude_code:", "chatgpt_browser:")) for line in lines
    ):
        return None

    lines[version_indexes[0]] = "setup_version: 2"
    lines[status_indexes[0]] = "status: in_progress"
    if verified_private_remote:
        visibility_indexes = [
            index
            for index, line in enumerate(lines)
            if re.fullmatch(r"  visibility:\s*.*", line)
        ]
        if len(visibility_indexes) != 1:
            return None
        lines[visibility_indexes[0]] = '  visibility: "private"'
    completed_indexes = [
        index for index, line in enumerate(lines) if line.startswith("completed_at:")
    ]
    if len(completed_indexes) > 1:
        return None
    if completed_indexes:
        insert_at = completed_indexes[0]
        lines[completed_indexes[0]] = 'completed_at: ""'
    else:
        insert_at = len(lines)
        lines.append('completed_at: ""')

    new_sections = [
        "claude_code:",
        '  choice: ""',
        "chatgpt_browser:",
        '  choice: ""',
    ]
    lines[insert_at:insert_at] = new_sections
    return "\n".join(lines) + "\n"


def main() -> int:
    if is_link_like(HARNESS) or is_link_like(STATE) or is_link_like(BACKUP):
        print("migration=unsafe_state")
        return 1
    if not STATE.is_file():
        print("migration=state_missing")
        return 1

    classification = safe_state_classification()
    if classification is None:
        print("migration=state_not_ready")
        return 1
    state_class, fields = classification
    required = (
        "language",
        "github.choice",
        "external_storage.choice",
        "obsidian.choice",
        "tex.choice",
    )
    if (
        state_class != "outdated"
        or fields.get("setup_version") != "1"
        or any(fields.get(key) in {None, "<missing>", "<unanswered>"} for key in required)
    ):
        print("migration=state_not_ready")
        return 1

    github_enabled = fields.get("github.choice") == "yes"
    if github_enabled and safe_remote_visibility() != "private":
        print("migration=private_remote_required")
        return 1

    try:
        source = STATE.read_text(encoding="utf-8")
        migrated = build_migrated_text(source, github_enabled)
        if migrated is None:
            print("migration=state_not_ready")
            return 1
        original_mode = stat.S_IMODE(STATE.stat().st_mode)
        if os.path.lexists(BACKUP):
            if not BACKUP.is_file() or BACKUP.read_text(encoding="utf-8") != source:
                print("migration=backup_conflict")
                return 1
        else:
            backup_descriptor = os.open(
                BACKUP,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
            with os.fdopen(
                backup_descriptor, "w", encoding="utf-8", newline="\n"
            ) as backup:
                backup.write(source)
                backup.flush()
                os.fsync(backup.fileno())
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix="local-migrate-",
            suffix=".yaml",
            dir=HARNESS,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(migrated)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.chmod(temporary_path, original_mode & 0o600 or 0o600)
        os.replace(temporary_path, STATE)
    except (OSError, UnicodeError):
        try:
            if "temporary_path" in locals() and temporary_path.exists():
                temporary_path.unlink()
        except OSError:
            pass
        print("migration=write_failed")
        return 1

    print("migration=ready_for_new_questions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
