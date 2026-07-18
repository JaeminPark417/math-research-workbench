#!/usr/bin/env python3
"""Lightweight, dependency-free checks for Math Research Workbench notes."""

from __future__ import annotations

import re
import sys
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
BINARY_SUFFIXES = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".zip", ".png", ".jpg", ".jpeg"}
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
            data[match.group(1)] = (match.group(2) or "").strip().strip('"\'')
    return None


def markdown_files() -> list[Path]:
    result: list[Path] = []
    for directory in CONTENT_DIRS:
        if directory.exists():
            result.extend(path for path in directory.rglob("*.md") if path.is_file())
    return sorted(set(result))


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    files = markdown_files()
    stem_index: dict[str, list[Path]] = {}
    for path in files:
        stem_index.setdefault(path.stem.lower(), []).append(path)

    for directory in CONTENT_DIRS:
        if not directory.exists():
            errors.append(f"missing content directory: {directory.relative_to(ROOT)}")
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix.lower() in BINARY_SUFFIXES:
                errors.append(f"tracked-style binary in text area: {path.relative_to(ROOT)}")

    for path in files:
        relative = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
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
            if data.get("language") not in {None, "en", "ko"}:
                errors.append(f"language must be en or ko: {relative}")
            for field in DATE_FIELDS & data.keys():
                value = data[field]
                if value and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                    errors.append(f"invalid ISO date in {field}: {relative}")

        for raw_link in WIKILINK.findall(text):
            target = raw_link.split("|", 1)[0].split("#", 1)[0].strip()
            if not target or "{" in target:
                continue
            candidate = ROOT / (target if target.endswith(".md") else f"{target}.md")
            if candidate.exists():
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
