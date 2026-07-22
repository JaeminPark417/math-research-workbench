#!/usr/bin/env python3
"""Install the one reviewed Workbench-provided Obsidian plugin safely."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ID = "mrw-latex-delimiter-compat"
SOURCE_DIR = ROOT / "optional" / "obsidian-plugins" / PLUGIN_ID
PLUGINS_DIR = ROOT / ".obsidian" / "plugins"
DESTINATION = PLUGINS_DIR / PLUGIN_ID
RUNTIME_FILES = ("main.js", "manifest.json")
SOURCE_FILES = {*RUNTIME_FILES, "README.md", "LICENSE"}
PRESERVED_LOCAL_FILES = {"data.json"}
IGNORED_METADATA_FILES = {".DS_Store", "Thumbs.db", "Desktop.ini", "desktop.ini"}
SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")

DISCLOSURE = """\
This installs the optional MRW LaTeX Delimiter Compatibility plugin.
- It is provided with Math Research Workbench, not listed in Obsidian's official directory.
- It renders \\(...\\) and \\[...\\] math; the current code makes no network requests and does not write notes.
- Enabling it requires turning on Obsidian community plugins, which changes the vault's trust setting.
- This tool copies fixed runtime files only. It never enables the plugin or edits community-plugins.json.
- Updates come from Math Research Workbench releases, not Obsidian's Check for updates action.
"""


class InstallError(RuntimeError):
    """A path-free, user-facing install failure."""


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


def ensure_safe_chain(path: Path) -> None:
    """Refuse links or junctions from the workbench root through path."""
    try:
        relative = path.relative_to(ROOT)
    except ValueError as error:
        raise InstallError("result=unsafe_path") from error
    current = ROOT
    for part in relative.parts:
        current = current / part
        if current.exists() or current.is_symlink():
            if is_link_like(current):
                raise InstallError("result=unsafe_path")


def read_manifest(directory: Path) -> dict[str, object]:
    manifest_path = directory / "manifest.json"
    ensure_safe_chain(manifest_path)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise InstallError("result=invalid_manifest") from error
    if not isinstance(payload, dict):
        raise InstallError("result=invalid_manifest")
    required_strings = ("id", "name", "version", "minAppVersion", "description", "author")
    if any(not isinstance(payload.get(key), str) or not payload[key] for key in required_strings):
        raise InstallError("result=invalid_manifest")
    if payload["id"] != PLUGIN_ID or not SEMVER.fullmatch(str(payload["version"])):
        raise InstallError("result=invalid_manifest")
    if not isinstance(payload.get("isDesktopOnly"), bool):
        raise InstallError("result=invalid_manifest")
    return payload


def validate_source() -> tuple[dict[str, object], dict[str, bytes]]:
    ensure_safe_chain(SOURCE_DIR)
    try:
        entries = {entry.name for entry in os.scandir(SOURCE_DIR)}
    except OSError as error:
        raise InstallError("result=bundle_unavailable") from error
    if entries - IGNORED_METADATA_FILES != SOURCE_FILES:
        raise InstallError("result=invalid_bundle")
    payload = read_manifest(SOURCE_DIR)
    runtime: dict[str, bytes] = {}
    for name in RUNTIME_FILES:
        path = SOURCE_DIR / name
        ensure_safe_chain(path)
        if not path.is_file() or is_link_like(path):
            raise InstallError("result=invalid_bundle")
        try:
            runtime[name] = path.read_bytes()
        except OSError as error:
            raise InstallError("result=invalid_bundle") from error
        if not runtime[name]:
            raise InstallError("result=invalid_bundle")
    return payload, runtime


def semver_tuple(version: object) -> tuple[int, int, int]:
    match = SEMVER.fullmatch(str(version))
    if not match:
        raise InstallError("result=invalid_manifest")
    return tuple(int(part) for part in match.groups())


def inspect_destination(
    source_manifest: dict[str, object], source_runtime: dict[str, bytes]
) -> tuple[str, str]:
    ensure_safe_chain(ROOT / ".obsidian")
    ensure_safe_chain(PLUGINS_DIR)
    ensure_safe_chain(DESTINATION)
    if not DESTINATION.exists():
        return "not_installed", ""
    if not DESTINATION.is_dir() or is_link_like(DESTINATION):
        return "unsafe", ""
    try:
        entries = {entry.name for entry in os.scandir(DESTINATION)}
    except OSError:
        return "unsafe", ""
    if not entries:
        return "empty", ""
    allowed = set(RUNTIME_FILES) | PRESERVED_LOCAL_FILES | IGNORED_METADATA_FILES
    if not set(RUNTIME_FILES).issubset(entries) or not entries.issubset(allowed):
        return "unrecognized", ""
    for name in entries:
        candidate = DESTINATION / name
        if is_link_like(candidate) or not candidate.is_file():
            return "unsafe", ""
    try:
        installed_manifest = read_manifest(DESTINATION)
        installed_runtime = {
            name: (DESTINATION / name).read_bytes() for name in RUNTIME_FILES
        }
    except (InstallError, OSError):
        return "unrecognized", ""
    installed_version = str(installed_manifest["version"])
    if installed_runtime == source_runtime:
        return "installed_current", installed_version
    installed_semver = semver_tuple(installed_version)
    source_semver = semver_tuple(source_manifest["version"])
    if installed_semver < source_semver:
        return "installed_stale", installed_version
    if installed_semver > source_semver:
        return "installed_newer", installed_version
    return "installed_modified", installed_version


def write_temp_file(destination: Path, name: str, content: bytes) -> Path:
    handle = tempfile.NamedTemporaryFile(
        mode="wb", prefix=f".{name}.mrw-", dir=destination, delete=False
    )
    temp_path = Path(handle.name)
    try:
        with handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.chmod(0o600)
        if temp_path.read_bytes() != content:
            raise InstallError("result=copy_verification_failed")
        return temp_path
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def replace_runtime(runtime: dict[str, bytes]) -> None:
    ensure_safe_chain(ROOT / ".obsidian")
    if not (ROOT / ".obsidian").is_dir():
        raise InstallError("result=obsidian_vault_unavailable")
    try:
        PLUGINS_DIR.mkdir(mode=0o700, exist_ok=True)
        ensure_safe_chain(PLUGINS_DIR)
        DESTINATION.mkdir(mode=0o700, exist_ok=True)
        ensure_safe_chain(DESTINATION)
    except OSError as error:
        raise InstallError("result=install_directory_unavailable") from error

    old_runtime: dict[str, bytes | None] = {}
    staged: dict[str, Path] = {}
    replaced: list[str] = []
    try:
        for name in RUNTIME_FILES:
            target = DESTINATION / name
            old_runtime[name] = target.read_bytes() if target.is_file() else None
            staged[name] = write_temp_file(DESTINATION, name, runtime[name])
        for name in RUNTIME_FILES:
            os.replace(staged[name], DESTINATION / name)
            replaced.append(name)
        if any((DESTINATION / name).read_bytes() != runtime[name] for name in RUNTIME_FILES):
            raise InstallError("result=copy_verification_failed")
    except (OSError, InstallError) as error:
        for name in reversed(replaced):
            target = DESTINATION / name
            previous = old_runtime[name]
            try:
                if previous is None:
                    target.unlink(missing_ok=True)
                else:
                    rollback = write_temp_file(DESTINATION, name, previous)
                    os.replace(rollback, target)
            except (OSError, InstallError):
                pass
        for temp_path in staged.values():
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
        if isinstance(error, PermissionError):
            raise InstallError("result=close_obsidian_and_retry") from error
        if isinstance(error, InstallError):
            raise error
        raise InstallError("result=install_failed") from error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check or install the reviewed Workbench Obsidian plugin."
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--install", action="store_true")
    action.add_argument("--update", action="store_true")
    parser.add_argument(
        "--consent",
        action="store_true",
        help="Confirm that the user approved the disclosure shown by the setup guide.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        source_manifest, source_runtime = validate_source()
        status, installed_version = inspect_destination(source_manifest, source_runtime)
        bundled_version = str(source_manifest["version"])

        if not args.install and not args.update:
            suffix = f" installed_version={installed_version}" if installed_version else ""
            print(f"plugin_status={status} bundled_version={bundled_version}{suffix}")
            attention_states = {
                "empty",
                "installed_modified",
                "installed_newer",
                "unsafe",
                "unrecognized",
            }
            return 1 if status in attention_states else 0

        print(DISCLOSURE, end="")
        if not args.consent:
            print("result=consent_required")
            return 2

        if args.install:
            if status == "installed_current":
                print(f"result=already_current version={bundled_version}")
                return 0
            if status not in {"not_installed", "empty"}:
                print(f"result=install_refused plugin_status={status}")
                return 1
        else:
            if status == "installed_current":
                print(f"result=already_current version={bundled_version}")
                return 0
            if status != "installed_stale":
                print(f"result=update_refused plugin_status={status}")
                return 1

        replace_runtime(source_runtime)
        final_status, _ = inspect_destination(source_manifest, source_runtime)
        if final_status != "installed_current":
            print("result=copy_verification_failed")
            return 1
        action = "installed" if args.install else "updated"
        print(f"result={action} version={bundled_version}")
        return 0
    except InstallError as error:
        print(str(error))
        return 1


if __name__ == "__main__":
    sys.exit(main())
