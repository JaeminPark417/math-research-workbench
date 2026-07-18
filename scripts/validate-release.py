#!/usr/bin/env python3
"""Validate the public distribution without third-party dependencies."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    ".agents/skills/first-run/SKILL.md",
    ".agents/skills/first-run/agents/openai.yaml",
    ".agents/skills/first-run/references/github.md",
    ".agents/skills/first-run/references/storage.md",
    ".agents/skills/first-run/references/obsidian.md",
    ".agents/skills/first-run/references/obsidian-plugins.md",
    ".agents/skills/first-run/references/tex.md",
    ".github/workflows/validate.yml",
    ".gitattributes",
    ".gitignore",
    ".harness/config.example.yaml",
    ".obsidian/app.json",
    ".obsidian/core-plugins.json",
    ".obsidian/templates.json",
    "AGENTS.md",
    "CONTENT-NOTICE.md",
    "GETTING_STARTED.md",
    "GETTING_STARTED.ko.md",
    "LICENSE",
    "README.md",
    "README.ko.md",
    "SECURITY.md",
    "VERSION",
    "CONTRIBUTING.md",
    "docs/daily-workflow.md",
    "docs/daily-workflow.ko.md",
    "docs/obsidian.md",
    "docs/obsidian-plugins.md",
    "docs/obsidian-plugins.ko.md",
    "docs/obsidian.ko.md",
    "docs/troubleshooting.ko.md",
    "docs/troubleshooting.md",
    "docs/updating.md",
    "docs/updating.ko.md",
    "meta/conventions.md",
    "meta/math-workflow.md",
    "meta/safety.md",
    "meta/schemas.md",
    "meta/templates/article.tex",
    "meta/templates/idea.md",
    "meta/templates/inbox.md",
    "meta/templates/paper.md",
    "meta/templates/project.md",
    "meta/templates/proof-audit.md",
    "meta/templates/research-log.md",
    "meta/templates/session.md",
    "scripts/compile-tex.ps1",
    "scripts/compile-tex.sh",
    "scripts/doctor.ps1",
    "scripts/doctor.sh",
    "scripts/remote-state.py",
    "scripts/setup-state.py",
    "scripts/vault-lint.py",
}
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
SECRET_PATTERNS = {
    "private key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "assigned secret": re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
}
PERSONAL_PATHS = {
    "macOS personal path": re.compile(r"/Users/(?!username(?:/|\b)|example(?:/|\b))[A-Za-z0-9._-]+/"),
    "Windows personal path": re.compile(r"(?i)\b[A-Z]:\\Users\\(?!username(?:\\|\b)|example(?:\\|\b))[^\\\s]+\\"),
    "Linux personal path": re.compile(r"/home/(?!username(?:/|\b)|example(?:/|\b))[A-Za-z0-9._-]+/"),
}


def public_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_symlink() or path.is_file():
            files.append(path)
    return sorted(files)


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def main() -> int:
    errors: list[str] = []
    relative_files = {path.relative_to(ROOT).as_posix() for path in public_files()}

    for missing in sorted(REQUIRED - relative_files):
        errors.append(f"missing required file: {missing}")

    for forbidden in (".harness/local.yaml", ".claude", ".codex", ".obsidian/plugins"):
        if (ROOT / forbidden).exists():
            errors.append(f"forbidden public path exists: {forbidden}")

    for path in public_files():
        relative = path.relative_to(ROOT).as_posix()
        if path.is_symlink():
            errors.append(f"symlink is not allowed in release: {relative}")
            continue
        if path.stat().st_size > 1_000_000:
            errors.append(f"file exceeds 1 MB: {relative}")
        text = read_text(path)
        if text is None:
            errors.append(f"non-text file in public allowlist: {relative}")
            continue

        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{label} pattern in {relative}")
        for label, pattern in PERSONAL_PATHS.items():
            if pattern.search(text):
                errors.append(f"{label} in {relative}")
        if path.suffix.lower() == ".md":
            for raw_target in MARKDOWN_LINK.findall(text):
                target = raw_target.strip().strip("<>")
                if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                clean = unquote(target.split("#", 1)[0].split("?", 1)[0])
                if not clean:
                    continue
                resolved = (path.parent / clean).resolve()
                try:
                    resolved.relative_to(ROOT)
                except ValueError:
                    errors.append(f"local link leaves repository in {relative}: {target}")
                    continue
                if not resolved.exists():
                    errors.append(f"broken local link in {relative}: {target}")

    skill = ROOT / ".agents/skills/first-run/SKILL.md"
    if skill.exists():
        skill_text = skill.read_text(encoding="utf-8")
        if not skill_text.startswith("---\n") or "\nname: first-run\n" not in skill_text or "\ndescription:" not in skill_text:
            errors.append("first-run SKILL.md has invalid required frontmatter")

    example_config = ROOT / ".harness/config.example.yaml"
    if example_config.exists():
        config_text = example_config.read_text(encoding="utf-8")
        blank_choices = re.findall(r'^  choice:\s*""\s*$', config_text, re.MULTILINE)
        if (
            'language: ""' not in config_text
            or len(blank_choices) != 4
            or 'plugin_setup: ""' not in config_text
            or 'pending_plugin: ""' not in config_text
        ):
            errors.append("example setup choices must be blank until the user answers")

    for wrapper_name in ("scripts/compile-tex.sh", "scripts/compile-tex.ps1"):
        wrapper = ROOT / wrapper_name
        if wrapper.exists():
            wrapper_text = wrapper.read_text(encoding="utf-8")
            if "-norc" not in wrapper_text or "-no-shell-escape" not in wrapper_text:
                errors.append(f"unsafe latexmk defaults in {wrapper_name}")

    github_reference = ROOT / ".agents/skills/first-run/references/github.md"
    if github_reference.exists():
        github_text = github_reference.read_text(encoding="utf-8")
        if re.search(r"^\s*git remote -v\s*$", github_text, re.MULTILINE):
            errors.append("GitHub setup must not print raw credential-bearing remote URLs")

    version_file = ROOT / "VERSION"
    if version_file.exists():
        version_text = version_file.read_text(encoding="utf-8")
        if not re.fullmatch(r"\d+\.\d+\.\d+\n?", version_text):
            errors.append("VERSION must contain one semantic version")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Release validation failed with {len(errors)} error(s).")
        return 1

    print(f"Release validation passed for {len(relative_files)} public files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
