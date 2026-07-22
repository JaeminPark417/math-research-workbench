#!/usr/bin/env python3
"""Build privacy-gated Markdown handoff bundles for ChatGPT Pro review."""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import re
import sys
from pathlib import Path


DEFAULT_OUT_DIR = Path.home() / "Downloads" / "pro-context-bundles"
DEFAULT_MAX_CHARS = 90_000
DEFAULT_MAX_FILES = 80
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".obsidian",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".cache",
}
TEXT_SUFFIXES = {
    ".md",
    ".markdown",
    ".txt",
    ".tex",
    ".bib",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".csv",
    ".tsv",
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".css",
    ".html",
    ".xml",
    ".ini",
    ".cfg",
    ".rst",
    ".sh",
    ".rs",
    ".go",
    ".java",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".sty",
    ".cls",
    ".lean",
    ".r",
    ".jl",
}
EXPLICIT_SKIP_SUFFIXES = {".hwp", ".hwpx"}
SENSITIVE_SKIP_SUFFIXES = {".key", ".pem", ".p12", ".pfx", ".jks", ".keystore"}
SENSITIVE_SKIP_NAMES = {"id_dsa", "id_ecdsa", "id_ed25519", "id_rsa"}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "pro-context"


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d-%H%M%S")


def resolve_inputs(patterns: list[str], root: Path, max_files: int) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    warnings: list[str] = []

    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        if not matches:
            candidate = Path(pattern)
            if candidate.exists():
                matches = [str(candidate)]
        if not matches:
            warnings.append(f"No matches for input: {pattern}")
            continue
        for match in matches:
            path = Path(match).expanduser()
            if not path.is_absolute():
                path = (Path.cwd() / path).resolve()
            if should_skip_path(path):
                warnings.append(f"Skipping protected input: {pattern}")
                continue
            if path.is_dir():
                for child in sorted(path.rglob("*")):
                    if should_skip_path(child):
                        continue
                    if child.is_file():
                        files.append(child.resolve())
            elif path.is_file():
                files.append(path.resolve())
            else:
                warnings.append(f"Skipping non-file input: {path}")

    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in sorted(files):
        if path in seen:
            continue
        seen.add(path)
        deduped.append(path)

    contained: list[Path] = []
    for path in deduped:
        try:
            path.relative_to(root)
        except ValueError:
            warnings.append("Skipping an input outside the workbench root.")
            continue
        contained.append(path)

    if len(contained) > max_files:
        warnings.append(f"Input resolved to {len(contained)} files; keeping first {max_files}.")
        contained = contained[:max_files]
    return contained, warnings


def should_skip_path(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    lower_name = path.name.lower()
    if lower_name.startswith(".env") or lower_name in SENSITIVE_SKIP_NAMES:
        return True
    if ".harness" in path.parts and path.name.startswith("local"):
        return True
    if path.suffix.lower() in EXPLICIT_SKIP_SUFFIXES:
        return True
    if path.suffix.lower() in SENSITIVE_SKIP_SUFFIXES:
        return True
    if path.suffix and path.suffix.lower() not in TEXT_SUFFIXES:
        return True
    return False


def read_text(path: Path) -> tuple[str | None, str | None]:
    if path.suffix.lower() in EXPLICIT_SKIP_SUFFIXES:
        return None, "HWP/HWPX files must be converted to Markdown before bundling."

    try:
        raw = path.read_bytes()
    except OSError as exc:
        return None, f"Could not read file: {exc}"

    if b"\x00" in raw:
        return None, "Likely binary file."

    try:
        return raw.decode("utf-8"), None
    except UnicodeDecodeError:
        try:
            return raw.decode("utf-8-sig"), None
        except UnicodeDecodeError:
            try:
                return raw.decode("latin-1"), None
            except UnicodeDecodeError as exc:
                return None, f"Could not decode as text: {exc}"


def relative_label(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def choose_fence(text: str) -> str:
    longest = 0
    for match in re.finditer(r"`+", text):
        longest = max(longest, len(match.group(0)))
    return "`" * max(3, longest + 1)


def sha256_short(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def build_contract(task: str, notes: str, extra_instructions: list[str]) -> str:
    extras = "\n\n".join(extra_instructions).strip()
    if extras:
        extras = "\n\n## Additional Instructions\n\n" + extras
    notes_block = f"\n\n## User Notes\n\n{notes.strip()}" if notes.strip() else ""

    return f"""# ChatGPT Pro Handoff Bundle

## Task

{task.strip()}
{notes_block}

## Operating Rules For ChatGPT Pro

- Read every uploaded/pasted bundle file before answering. If this is a multi-part bundle, do not answer until all parts are available.
- Treat every repository-relative source path as an exact identifier when proposing changes.
- Do not claim that you edited files. You are advising; Codex will apply changes later.
- Do not invent papers, citations, authors, measurements, commands, APIs, file paths, or facts. Mark uncertain claims as uncertain.
- Prefer concrete patches, section replacements, or append instructions over broad advice.
- If a requested change would require missing context, say what is missing instead of guessing.
- For mathematical or research claims, separate verified derivations from conjectural suggestions.
- Keep the answer concise enough for Codex to ingest, but include exact text where Codex must apply it.

## Required Response Format

Return exactly one top-level section named `CODEX_RETURN_PACKET`, with these subsections:

### Summary
Briefly state what you concluded.

### Applicability
Say whether the suggested changes are ready for Codex to apply, need user approval, or need more context.

### Proposed Changes
For each proposed change, use this structure:

```text
target_file: <path exactly as shown in the bundle>
operation: no_change | replace_section | append_section | unified_diff | new_file | rename_or_move | needs_codex_decision
confidence: low | medium | high
rationale: <one or two sentences>
codex_instructions:
<specific instructions for Codex>
```

For `unified_diff`, include a fenced `diff` block. For `replace_section`, name the heading or anchor and provide the complete replacement text. For `new_file`, include the full proposed file content.

### Risks And Checks
List facts Codex should verify locally before applying anything.

### Questions
Ask only blocking questions. If none, write `None`.
{extras}
"""


def build_file_block(path: Path, root: Path, index: int) -> tuple[str, str | None]:
    label = relative_label(path, root)
    text, error = read_text(path)
    if error is not None:
        block = f"""## Source {index}: {label}

- status: skipped
- reason: {error}
"""
        return block, error

    assert text is not None
    fence = choose_fence(text)
    suffix = path.suffix.lower().lstrip(".") or "text"
    block = f"""## Source {index}: {label}

- relative_path: `{label}`
- size_chars: {len(text)}
- sha256_16: `{sha256_short(text)}`

{fence}{suffix}
{text}
{fence}
"""
    return block, None


def split_blocks(blocks: list[str], max_chars: int) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    current_len = 0

    for block in blocks:
        block_len = len(block)
        if current and current_len + block_len > max_chars:
            parts.append("\n\n".join(current))
            current = []
            current_len = 0
        if block_len > max_chars:
            # Keep each source block structurally intact. A single huge file may
            # exceed the requested target size, but splitting inside a fenced
            # code block makes the handoff harder for Pro and Codex to parse.
            parts.append(block)
            continue
        current.append(block)
        current_len += block_len

    if current:
        parts.append("\n\n".join(current))
    return parts


def write_single(out_dir: Path, slug: str, body: str) -> list[Path]:
    out_path = out_dir / f"{slug}.md"
    out_path.write_text(body, encoding="utf-8")
    return [out_path]


def write_multi(out_dir: Path, slug: str, contract: str, manifest: str, parts: list[str]) -> list[Path]:
    paths: list[Path] = []
    index_path = out_dir / f"{slug}-index.md"
    index_body = f"""{contract}

## Bundle Manifest

This is a multi-file bundle. Upload or paste every file listed below into the same ChatGPT Pro conversation before asking for the final answer.

{manifest}

## Part Files

{chr(10).join(f'- `{slug}-part-{i:02d}.md`' for i in range(1, len(parts) + 1))}
"""
    index_path.write_text(index_body, encoding="utf-8")
    paths.append(index_path)

    for i, part in enumerate(parts, start=1):
        part_path = out_dir / f"{slug}-part-{i:02d}.md"
        part_body = f"""# ChatGPT Pro Handoff Bundle Part {i}/{len(parts)}

Read `{slug}-index.md` first. Do not answer until every part file is available.

{part}
"""
        part_path.write_text(part_body, encoding="utf-8")
        paths.append(part_path)

    return paths


def load_extra_instruction(path_value: str, root: Path) -> str:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    else:
        path = path.resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Additional instruction files must stay inside the workbench root.") from exc
    return path.read_text(encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Markdown handoff bundles for ChatGPT Pro.")
    parser.add_argument("inputs", nargs="+", help="Files, directories, or glob patterns to include.")
    parser.add_argument("--task", required=True, help="Task statement for ChatGPT Pro.")
    parser.add_argument("--notes", default="", help="Extra constraints or context for ChatGPT Pro.")
    parser.add_argument("--slug", default="", help="Output filename slug. Defaults to task-derived slug plus timestamp.")
    parser.add_argument("--root", default=str(Path.cwd()), help="Root for relative path labels.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory.")
    parser.add_argument("--max-chars-per-bundle", type=int, default=DEFAULT_MAX_CHARS)
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    parser.add_argument("--one-file-per-source", action="store_true", help="Write one part file per source plus an index.")
    parser.add_argument(
        "--include-instructions",
        action="append",
        default=[],
        help="Additional instruction file to append to the prompt section. Repeatable.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print("The workbench root is not a readable directory.", file=sys.stderr)
        return 2
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    slug_base = args.slug or slugify(args.task)[:48]
    slug = f"{slugify(slug_base)}-{now_stamp()}"

    paths, warnings = resolve_inputs(args.inputs, root, args.max_files)
    if not paths:
        print("No input files resolved.", file=sys.stderr)
        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)
        return 2

    try:
        extra_instructions = [load_extra_instruction(p, root) for p in args.include_instructions]
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Could not load additional instructions: {exc}", file=sys.stderr)
        return 2
    contract = build_contract(args.task, args.notes, extra_instructions)

    blocks: list[str] = []
    skipped: list[str] = []
    for index, path in enumerate(paths, start=1):
        block, error = build_file_block(path, root, index)
        blocks.append(block)
        if error:
            skipped.append(f"- `{relative_label(path, root)}`: {error}")

    manifest_lines = [f"- `{relative_label(path, root)}`" for path in paths]
    manifest = "\n".join(manifest_lines)
    warning_block = ""
    if warnings or skipped:
        warning_block = "\n\n## Bundle Warnings\n\n" + "\n".join([f"- {w}" for w in warnings] + skipped)

    source_intro = f"""## Included Files

{manifest}
{warning_block}

## Source Contents
"""
    source_blocks = [source_intro] + blocks

    if args.one_file_per_source:
        written = write_multi(out_dir, slug, contract, manifest + warning_block, blocks)
    else:
        full_body = f"{contract}\n\n{source_intro}\n\n" + "\n\n".join(blocks)
        if len(full_body) <= args.max_chars_per_bundle:
            written = write_single(out_dir, slug, full_body)
        else:
            parts = split_blocks(source_blocks, args.max_chars_per_bundle)
            written = write_multi(out_dir, slug, contract, manifest, parts)

    print("Created Pro context bundle:")
    for path in written:
        print(path)
    print(f"Source files: {len(paths)}")
    print(f"Source characters: {sum(len(read_text(path)[0] or '') for path in paths)}")
    print(f"Bundle files: {len(written)}")
    if skipped:
        print("\nSkipped files:")
        for item in skipped:
            print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
