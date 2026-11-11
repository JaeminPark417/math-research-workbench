#!/usr/bin/env python3
"""Copy and compare the exact Markdown target of a mathematical research run."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from typing import NamedTuple


class TargetError(ValueError):
    pass


COMMIT = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?")
ID = re.compile(r"[\w][\w.:-]*")
SNAPSHOT_FIELD = "Target snapshot"
HEADING_FIELD = "Target heading"
REF_PLACEHOLDERS = {
    "<stable ID; repository-relative path to the canonical statement (project README or claim ledger); current `HEAD` hash if the copied wording matches it, otherwise `working snapshot Run-YYYYMMDD-NNN` with this run's actual ID; `not applicable` for a new object>",
    "<stable ID; repository-relative project README path; current `HEAD` hash if the copied wording matches it, otherwise `working snapshot Run-YYYYMMDD-NNN` with this run's actual ID; `not applicable` for a new object>",
    "<stable ID; repository-relative canonical statement/claim-ledger path in the private repo; current `HEAD` commit hash at SPEC start if `Exact statement` matches it, otherwise `working snapshot Run-YYYYMMDD-NNN` using this run's actual ID; use `not applicable` for a new object>",
}
TARGET_PLACEHOLDERS = {
    "<copy the current Spine wording exactly, or state the proposed new target exactly>",
    "<all quantifiers, hypotheses, parameter ranges, and conclusion>",
}


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def local_path(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative or any(c in relative for c in "\n\r;:"):
        raise TargetError("expected a repository-relative POSIX path")
    path = PurePosixPath(relative)
    if path.is_absolute() or any(part.startswith(".") for part in relative.split("/")) or "//" in relative:
        raise TargetError("expected a repository-relative non-hidden path")
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise TargetError("symbolic links are not supported in target paths")
    return current


def git_text(root, args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                            env={**os.environ, "GIT_NO_LAZY_FETCH": "1", "GIT_TERMINAL_PROMPT": "0"})
    if result.returncode:
        raise TargetError("Git source version unavailable")
    return result.stdout.decode("utf-8").replace("\r\n", "\n")


def at_commit(root, source, commit):
    if not COMMIT.fullmatch(commit):
        raise TargetError("expected a full Git commit ID")
    if git_text(root, ["cat-file", "-t", commit]).strip() != "commit":
        raise TargetError("source version must identify a Git commit")
    if Path(git_text(root, ["rev-parse", "--show-toplevel"]).strip()).resolve() != root:
        raise TargetError("--root must be the repository root for commit references")
    return git_text(root, ["cat-file", "blob", commit + ":" + source])


def split_markdown_table_row(line: str) -> list[str]:
    """Split one Markdown table row while preserving escaped/code/math pipes."""
    stripped = line.strip()
    if not stripped.startswith("|"):
        return []
    body = stripped[1:-1] if stripped.endswith("|") else stripped[1:]
    cells: list[str] = []
    current: list[str] = []
    code = False
    math_mode = ""
    index = 0
    while index < len(body):
        char = body[index]
        next_char = body[index + 1] if index + 1 < len(body) else ""
        pair = char + next_char
        if char == "\\" and next_char:
            if pair in {"\\(", "\\["} and not code and not math_mode:
                math_mode = pair
            elif (
                (pair == "\\)" and math_mode == "\\(")
                or (pair == "\\]" and math_mode == "\\[")
            ):
                math_mode = ""
            current.extend((char, next_char))
            index += 2
            continue
        if char == "`" and not math_mode:
            code = not code
            current.append(char)
            index += 1
            continue
        if char == "$" and not code and math_mode not in {"\\(", "\\["}:
            math_mode = "" if math_mode == "$" else "$"
            current.append(char)
            index += 1
            continue
        if char == "|" and not code and not math_mode:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        index += 1
    cells.append("".join(current).strip())
    return cells


def structural_lines(lines, in_run=False):
    """Keep line numbers and hide fence delimiters and literal code from Markdown lookups."""
    fence = ""
    inside_value = False
    for line in lines:
        if in_run and not fence:
            if inside_value and (not line.strip() or re.match(r"^[ \t]{2}", line)):
                yield None
                continue
            inside_value = bool(re.match(r"^- (?:\*\*)?(?:Exact target|Exact statement)(?:\*\*)?:", line))
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = ""
            yield None
        elif marker and (marker[1][0] != "`" or "`" not in marker[2]):
            fence = marker[1]
            yield None
        else:
            yield line


def statement_columns(cells):
    for labels in ({"exact statement", "exact formulation or source", "exact formulation",
                    "precise missing justification or issue"}, {"statement"}, {"claim", "claim or gap"}):
        found = [i for i, value in enumerate(cells) if value.casefold() in labels]
        if found:
            return found
    return []


def claim_text(source_text, claim_id, heading=None):
    if not ID.fullmatch(claim_id):
        raise TargetError("invalid claim ID")
    lines = source_text.splitlines()
    if heading is not None:
        if not heading.strip() or "\n" in heading or "\r" in heading:
            raise TargetError("expected a single nonempty source heading")
        headings = [(i, len(m[1]), m[2]) for i, line in enumerate(structural_lines(lines))
                    if line is not None and (m := re.fullmatch(r" {0,3}(#{1,6})[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*", line))]
        where = [(i, level) for i, level, name in headings if name == heading]
        if len(where) != 1:
            raise TargetError("source heading is missing or ambiguous")
        start, level = where[0]
        end = next((i for i, depth, _ in headings if i > start and depth <= level), len(lines))
        body = lines[start + 1:end]
        while body and not body[-1].strip():
            body.pop()
        first = next((i for i, line in enumerate(body) if line.strip()), len(body))
        values = ["\n".join(body[first:])]
    else:
        values = []
        columns = []
        for line in structural_lines(lines):
            if line is None or not line.lstrip().startswith("|"):
                columns = []
                continue
            cells = split_markdown_table_row(line)
            if cells and cells[0].casefold() == "id":
                columns = statement_columns(cells)
            elif columns:
                identifier = re.sub(r" \([^()]+ legacy alias\)$", "", cells[0]).strip("` ")
                if identifier == claim_id:
                    if len(columns) != 1 or columns[0] >= len(cells):
                        raise TargetError("statement column is missing or ambiguous for this claim")
                    values.append(cells[columns[0]])
        if len(values) != 1:
            raise TargetError("source claim ID is missing or ambiguous; use an exact heading for a standalone statement")
    if not values[0].strip():
        raise TargetError("empty source statement")
    return values[0]


def contract_span(text):
    lines = text.splitlines(keepends=True)
    offset, starts, ends = 0, [], []
    for raw, line in zip(lines, structural_lines(lines, in_run=True)):
        if line is not None and re.match(r"^#{1,2}[ \t]", line):
            ends.append(offset)
            if line.rstrip() == "## Problem Contract":
                starts.append(offset + len(raw))
        offset += len(raw)
    if len(starts) != 1:
        raise TargetError("missing Problem Contract")
    start = starts[0]
    return start, next((end for end in ends if end >= start), len(text))


class ContractField(NamedTuple):
    start: int
    end: int
    prefix: str


def field(contract, names):
    label = "|".join(re.escape(name) for name in names)
    pattern = re.compile(r"^(- (?:\*\*)?(?:" + label + r")(?:\*\*)?:)[ \t]*(.*)$")
    offset = 0
    lines = contract.splitlines(keepends=True)
    result = None, None
    for i, (raw, line) in enumerate(zip(lines, structural_lines(lines, in_run=True))):
        match = pattern.match(line.rstrip("\n")) if line is not None else None
        if match:
            if result[0] is not None:
                raise TargetError("duplicate contract field " + "/".join(names))
            parts = [match[2]]
            end = offset + len(raw.rstrip("\n"))
            next_offset = offset + len(raw)
            blanks = 0
            for following in lines[i + 1:]:
                body = following.rstrip("\n")
                if not body.strip():
                    blanks += 1
                elif re.match(r"^[ \t]{2}", body):
                    parts += [""] * blanks + [body[2:]]
                    blanks = 0
                    end = next_offset + len(body)
                else:
                    break
                next_offset += len(following)
            if len(parts) > 1 and not parts[0]:
                parts = parts[1:]
            result = ContractField(offset, end, match[1]), "\n".join(parts)
        offset += len(raw)
    return result


def render(value):
    prefix = "\n  " if value.startswith((" ", "\t")) else ""
    first, *rest = value.split("\n")
    return prefix + first + "".join("\n" + ("  " + line if line.strip() else "") for line in rest)


def run_id_of(text):
    match = re.search(r'^run_id:[ \t]*["\x27]?([\w.-]+)', text, re.M)
    if match:
        return match[1]
    _, value = field(text, ["Run ID"])
    if value and re.fullmatch(r"Run-\d[\w.-]+", value.strip("`")):
        return value.strip("`")
    raise TargetError("fill in the run ID before capture")


def ref_for(snap):
    return f"{snap['id']}; {snap['source']}; {snap['version']}"


def definition(root, source, claim_id, heading, commit, run_id):
    path = local_path(root, source)
    if path.suffix.lower() != ".md":
        raise TargetError("target source must be Markdown")
    if commit:
        target = claim_text(at_commit(root, source, commit), claim_id, heading)
    else:
        target = claim_text(path.read_text(encoding="utf-8"), claim_id, heading)
        try:
            head = git_text(root, ["rev-parse", "--verify", "HEAD"]).strip()
            if claim_text(at_commit(root, source, head), claim_id, heading) == target:
                commit = head
        except (TargetError, OSError, UnicodeError):
            pass
    return dict(schema=1, id=claim_id, source=source, heading=heading, run_id=run_id,
                version=commit or "working snapshot " + run_id, statement=target)


def snapshot_path(run):
    return run.with_suffix(".target.json")


def replace_fields(raw, edits):
    """Parse in LF coordinates, preserve all bytes outside the fields (even for mixed EOL)."""
    normalized = raw.replace("\r\n", "\n")
    lines = raw.split("\n")

    def original_index(position):
        count = normalized.count("\n", 0, position)
        return position + sum(line.endswith("\r") for line in lines[:count])

    result = raw
    for start, end, value in sorted(edits, reverse=True):
        eol = "\r\n" if lines[normalized.count("\n", 0, start)].endswith("\r") else "\n"
        result = result[:original_index(start)] + value.replace("\n", eol) + result[original_index(end):]
    return result


def capture(root, run_relative, source, claim_id, heading=None, commit=None):
    run = local_path(root, run_relative)
    if run.suffix.lower() != ".md" or run == local_path(root, source):
        raise TargetError("select a separate Markdown run")
    original = run.read_bytes()
    raw = original.decode("utf-8")
    text = raw.replace("\r\n", "\n")
    start, end = contract_span(text)
    contract = text[start:end]
    ref, ref_value = field(contract, ["Spine target reference"])
    target, target_value = field(contract, ["Exact target", "Exact statement"])
    marker, _ = field(contract, [SNAPSHOT_FIELD])
    heading_field, old_heading = field(contract, [HEADING_FIELD])
    if not ref or not target:
        raise TargetError("missing Spine target reference or exact statement field")
    path = snapshot_path(run)
    if marker:
        raise TargetError("run already has a frozen target; use check or create a new run")
    snap = definition(root, source, claim_id, heading, commit, run_id_of(text))
    expected_ref = ref_for(snap)
    if ref_value and ref_value not in REF_PLACEHOLDERS and ref_value != expected_ref:
        raise TargetError("existing source reference differs; preserve this run and create a new one")
    if ref_value == expected_ref and snap["version"].startswith("working snapshot "):
        raise TargetError("cannot retroactively verify a legacy working reference; preserve this run and capture a new one")
    if target_value and target_value not in TARGET_PLACEHOLDERS and target_value != snap["statement"]:
        raise TargetError("existing target differs; preserve this run and create a new one")
    if heading_field and old_heading != heading:
        raise TargetError("existing target heading differs; preserve this run and create a new one")
    payload = json.dumps(snap, ensure_ascii=False, indent=2) + "\n"
    replacement = ref.prefix + " " + expected_ref + "\n- Target snapshot: sha256:" + digest(payload)
    if heading and not heading_field:
        replacement += "\n- Target heading: " + heading
    updated = replace_fields(raw, [
        (start + ref.start, start + ref.end, replacement),
        (start + target.start, start + target.end, target.prefix + " " + render(snap["statement"])),
    ])
    if path.is_symlink():
        raise TargetError("invalid target snapshot path")
    try:
        with path.open("x", encoding="utf-8", newline="\n") as output:
            output.write(payload)
    except FileExistsError:
        if path.read_text(encoding="utf-8") != payload:
            raise TargetError("snapshot exists without a run marker (interrupted capture?); inspect the saved snapshot before creating a new run")
    with tempfile.NamedTemporaryFile(dir=run.parent, delete=False) as output:
        temp = Path(output.name)
        output.write(updated.encode("utf-8"))
    try:
        os.chmod(temp, run.stat().st_mode & 0o777)
        if run.read_bytes() != original:
            raise TargetError("run changed during capture; inspect the saved snapshot")
        os.replace(temp, run)
    finally:
        temp.unlink(missing_ok=True)
    return path


def check(root, run, text):
    """Return a current-source/legacy warning, or raise for an invalid binding."""
    start, end = contract_span(text)
    contract = text[start:end]
    _, marker = field(contract, [SNAPSHOT_FIELD])
    _, visible_heading = field(contract, [HEADING_FIELD])
    _, ref = field(contract, ["Spine target reference"])
    _, target = field(contract, ["Exact target", "Exact statement"])
    path = snapshot_path(run)
    if marker is not None or path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_file():
            raise TargetError("missing or invalid target snapshot")
        if marker is None:
            raise TargetError("snapshot exists without a run marker (interrupted capture?); inspect it and retry the original capture")
        payload = path.read_text(encoding="utf-8")
        if marker != "sha256:" + digest(payload):
            raise TargetError("target snapshot digest differs from run")
        snap = json.loads(payload)
        keys = {"schema", "run_id", "source", "id", "version", "heading", "statement"}
        if (not isinstance(snap, dict) or set(snap) != keys or snap["schema"] != 1
                or not all(isinstance(snap[k], str) for k in keys - {"schema", "heading"})
                or (snap["heading"] is not None and not isinstance(snap["heading"], str))):
            raise TargetError("invalid target snapshot fields")
        if ref != ref_for(snap) or snap["run_id"] != run_id_of(text):
            raise TargetError("run ID/source reference differs from frozen target")
        visible_statement = "\n".join(line if line.strip() else "" for line in snap["statement"].split("\n"))
        if target != visible_statement:
            raise TargetError("run target differs from frozen source wording")
        if visible_heading is not None and visible_heading != snap["heading"]:
            raise TargetError("run target heading differs from frozen source heading")
        target = snap["statement"]
        source, claim_id, heading, version = (snap[k] for k in ("source","id","heading","version"))
        if not COMMIT.fullmatch(version) and version != "working snapshot " + snap["run_id"]:
            raise TargetError("invalid frozen source version")
    else:
        if ref and ref.strip("` ").lower() == "not applicable":
            return None
        if not ref or ref.startswith("<"):
            return "source binding is missing; capture the existing target or record not applicable for a new claim"
        pieces = [x.strip().strip("`") for x in ref.split(";")]
        if len(pieces) != 3 or not ID.fullmatch(pieces[0]) or not pieces[1].endswith(".md"):
            return "legacy source reference has no machine-readable locator; compare manually"
        claim_id, source, version = pieces
        commit = re.search(r"(?<![0-9a-f])([0-9a-f]{40}(?:[0-9a-f]{24})?)(?![0-9a-f])", version)
        if commit:
            version = commit[1]
        elif not version.startswith("working snapshot "):
            return "legacy source version is unavailable; compare manually"
        heading = visible_heading
    source_path = local_path(root, source)
    if source_path.suffix.lower() != ".md":
        raise TargetError("target source must be Markdown")
    notices = []
    if marker is None and not COMMIT.fullmatch(version):
        notices.append("legacy working reference; original wording unverifiable")
    if COMMIT.fullmatch(version):
        try:
            pinned = claim_text(at_commit(root, source, version), claim_id, heading)
        except (TargetError, OSError, UnicodeError) as exc:
            notices.append(("frozen target intact; " if marker is not None else "legacy reference; ")
                           + "pinned source unavailable: " + str(exc))
        else:
            if pinned != target:
                raise TargetError("run target differs from the pinned source wording")
    try:
        current = claim_text(source_path.read_text(encoding="utf-8"), claim_id, heading)
    except (OSError, UnicodeError, TargetError) as exc:
        notices.append("current source unavailable: " + str(exc))
    else:
        if current != target:
            if marker is None and not COMMIT.fullmatch(version):
                raise TargetError("legacy working target and current source differ; verify original snapshot before reuse")
            notices.append("current source wording changed; original target preserved"
                           if marker is not None or not notices else "legacy target and current source differ")
    return "; ".join(notices) or None


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="action", required=True)
    for action in ("capture", "check"):
        sub = subs.add_parser(action)
        sub.add_argument("--root", type=Path, required=True, help="verified project repository root")
        sub.add_argument("--run", required=True, help="repository-relative run Markdown")
        if action == "capture":
            sub.add_argument("--source", required=True, help="repository-relative canonical Markdown")
            sub.add_argument("--id", required=True, help="stable claim ID")
            sub.add_argument("--heading", help="unique exact heading for a standalone statement")
            sub.add_argument("--commit", help="full historical Git commit; default: current wording")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.action == "capture":
            print("Saved", capture(root, args.run, args.source, args.id, args.heading, args.commit).relative_to(root))
        else:
            run = local_path(root, args.run)
            text = run.read_text(encoding="utf-8")
            result = check(root, run, text)
            if result:
                print("REVIEW:", result)
                return 2
            _, ref = field(text[slice(*contract_span(text))], ["Spine target reference"])
            if ref.strip("` ").lower() == "not applicable":
                print("Unbound run: no existing canonical target identified.")
            else:
                print("Recorded target matches the source wording.")
    except (OSError, UnicodeError, ValueError) as exc:
        print("ERROR:", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
