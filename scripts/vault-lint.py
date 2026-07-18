#!/usr/bin/env python3
"""Lightweight, dependency-free checks for Math Research Workbench notes."""

from __future__ import annotations

import os
import re
import stat
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIRS = tuple(ROOT / name for name in ("inbox", "ideas", "papers", "notes", "projects"))
SUPPORTED_TYPES = {"inbox", "idea", "paper", "project", "session", "research-log"}
REQUIRED_FIELDS = {
    "inbox": {"type", "title", "created", "language"},
    "idea": {"type", "title", "status", "created", "updated", "language"},
    "paper": {"type", "title", "authors", "year", "status", "citation_status", "added", "language"},
    "project": {"type", "title", "status", "created", "updated", "language", "research_question"},
    "session": {"type", "title", "date", "language", "project"},
    "research-log": {"type", "title", "date", "updated", "language", "project", "kind", "status", "review_status"},
}
DATE_FIELDS = {"created", "updated", "added", "date"}
ENUM_FIELDS = {
    "idea": {
        "status": {"seed", "active", "dormant", "archived"},
    },
    "paper": {
        "status": {"queued", "reading", "read", "revisit"},
        "citation_status": {"unverified", "verified"},
    },
    "project": {
        "status": {"planning", "active", "paused", "completed", "archived"},
    },
    "research-log": {
        "kind": {
            "general",
            "derivation",
            "proof-audit",
            "counterexample-search",
            "literature-check",
            "formalization",
        },
        "status": {"open", "partial", "complete", "archived"},
        "review_status": {
            "unchecked",
            "human-reviewed",
            "formal-tool-checked",
            "human-and-formal",
        },
    },
}
BINARY_SUFFIXES = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".zip",
    ".7z",
    ".tar",
    ".gz",
    ".tgz",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".heic",
    ".mp3",
    ".wav",
    ".mp4",
    ".mov",
    ".key",
    ".pem",
    ".p12",
    ".pfx",
}
YAML_KEY = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s*(.*))?$")
WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")


def portable_kebab_filename(name: str) -> bool:
    if not name.endswith(".md"):
        return False
    stem = name[:-3]
    if re.match(r"^\d{4}-\d{2}-\d{2}-", stem):
        stem = stem[11:]
    segments = stem.split("-")
    return bool(stem) and all(
        segment and segment == segment.lower() and all(char.isalnum() for char in segment)
        for segment in segments
    )


def frontmatter(text: str) -> dict[str, str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    data: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return data
        match = YAML_KEY.match(line)
        if match:
            key = match.group(1)
            if key in data:
                return None
            data[key] = (match.group(2) or "").strip().strip('"\'')
    return None


def valid_iso_date(value: str) -> bool:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def is_link_like(path: Path) -> bool:
    """Detect symlinks and Windows junction/reparse points without following."""
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


def scan_content() -> tuple[list[Path], list[Path], list[Path], list[Path], list[Path]]:
    markdown: list[Path] = []
    binaries: list[Path] = []
    links: list[Path] = []
    missing: list[Path] = []
    unreadable: list[Path] = []

    for content_root in CONTENT_DIRS:
        if is_link_like(content_root):
            links.append(content_root)
            continue
        if not content_root.is_dir():
            missing.append(content_root)
            continue

        pending = [content_root]
        while pending:
            directory = pending.pop()
            try:
                entries = list(os.scandir(directory))
            except OSError:
                unreadable.append(directory)
                continue
            for entry in entries:
                path = Path(entry.path)
                if is_link_like(path):
                    links.append(path)
                    continue
                try:
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(path)
                    elif entry.is_file(follow_symlinks=False):
                        if path.suffix.lower() == ".md":
                            markdown.append(path)
                        if path.suffix.lower() in BINARY_SUFFIXES:
                            binaries.append(path)
                except OSError:
                    unreadable.append(path)

    return (
        sorted(set(markdown)),
        sorted(set(binaries)),
        sorted(set(links)),
        sorted(set(missing)),
        sorted(set(unreadable)),
    )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    files, binaries, links, missing, unreadable = scan_content()
    stem_index: dict[str, list[Path]] = {}
    for path in files:
        stem_index.setdefault(path.stem.lower(), []).append(path)

    for path in missing:
        errors.append(f"missing content directory: {path.relative_to(ROOT)}")
    for path in links:
        errors.append(f"link or junction is not allowed in content: {path.relative_to(ROOT)}")
    for path in unreadable:
        errors.append(f"content entry could not be read safely: {path.relative_to(ROOT)}")
    for path in binaries:
        errors.append(f"tracked-style binary in text area: {path.relative_to(ROOT)}")

    known_relative_files = {
        path.relative_to(ROOT).as_posix().casefold() for path in files
    }

    for path in files:
        relative = path.relative_to(ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            errors.append(f"Markdown file could not be read safely: {relative}")
            continue
        if path.name != "README.md" and not portable_kebab_filename(path.name):
            warnings.append(f"non-kebab Markdown filename: {relative}")

        data = frontmatter(text)
        if text.startswith("---") and data is None:
            errors.append(f"unterminated or malformed frontmatter: {relative}")
            continue
        if data is not None:
            note_type = data.get("type", "")
            if note_type not in SUPPORTED_TYPES:
                errors.append(f"unsupported type {note_type!r}: {relative}")
            else:
                missing = sorted(REQUIRED_FIELDS[note_type] - data.keys())
                if missing:
                    errors.append(f"missing fields {', '.join(missing)}: {relative}")
                for field, allowed_values in ENUM_FIELDS.get(note_type, {}).items():
                    if field in data and data[field] not in allowed_values:
                        errors.append(
                            f"invalid {field} value {data[field]!r} for {note_type}: {relative}"
                        )
            if data.get("language") not in {None, "en", "ko"}:
                errors.append(f"language must be en or ko: {relative}")
            for field in DATE_FIELDS & data.keys():
                value = data[field]
                if not valid_iso_date(value):
                    errors.append(f"invalid ISO date in {field}: {relative}")

        for raw_link in WIKILINK.findall(text):
            target = raw_link.split("|", 1)[0].split("#", 1)[0].strip()
            if not target or "{" in target:
                continue
            candidate = Path(target if target.endswith(".md") else f"{target}.md")
            if (
                not candidate.is_absolute()
                and ".." not in candidate.parts
                and candidate.as_posix().casefold() in known_relative_files
            ):
                continue
            if Path(target).name.lower() in stem_index:
                continue
            warnings.append(f"unresolved wikilink [[{target}]] in {relative}")

    for item in warnings:
        print(f"WARN: {item}")
    for item in errors:
        print(f"ERROR: {item}")
    print(f"Checked {len(files)} Markdown notes: {len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
