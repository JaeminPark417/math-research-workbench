#!/usr/bin/env python3
"""Lightweight, dependency-free checks for Math Research Workbench notes."""

from __future__ import annotations

import os
import re
import stat
import sys
from datetime import date
from pathlib import Path

sys.dont_write_bytecode = True
from formalization_manifest import read_manifest, validate_manifest_path


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
STATE_SPINE_HEADER = (
    "| ID | Claim | Mathematical state | Depends on | Evidence or source | "
    "Review provenance | Integration state | Next action |"
)
LEGACY_CLAIM_HEADER = "| ID | Claim | State | Evidence or gap | Source log |"
MATHEMATICAL_STATES = {
    "conjectural",
    "partial",
    "gap-found",
    "supported",
    "closed-by-researcher",
    "refuted",
}
INTEGRATION_STATES = {"isolated", "integrated", "review-stale", "retired"}
REVIEW_PROVENANCE_PREFIXES = (
    "unchecked",
    "AI-assisted",
    "human-reviewed",
    "formal-tool-checked",
    "human-and-formal",
)
STABLE_RESEARCH_ID_IN_TEXT = re.compile(
    r"(?<![A-Za-z0-9-])(?:Def|Lem|Prop|Thm|Cor|Gap)-\d{3}(?![A-Za-z0-9-])"
)
RESEARCH_RUN_FIELDS = {"run_id", "adapter", "adapter_scope"}
RESEARCH_RUN_ID = re.compile(r"Run-(\d{4})(\d{2})(\d{2})-\d{3}")
RESEARCH_RUN_ADAPTERS = {
    "natural-proof",
    "formalization",
    "constructive-search",
    "literature-audit",
    "mixed",
}
RESEARCH_RUN_HEADINGS = (
    "# Research run",
    "## Problem Contract",
    "## Run manifest",
    "## Obligations",
    "## Attempt ledger",
    "## Adapter and evidence records",
    "## Scoped synthesis",
    "## Human promotion",
)
RESEARCH_RUN_CONTRACT_FIELDS = (
    "Exact target",
    "Success criterion",
    "Refutation criterion",
)
RESEARCH_RUN_CONFIRMATION_FIELDS = {
    "statement-match": (
        "Statement-match confirmation",
        "Statement-match scope",
        "Statement-match confirmed by (consented identifier or role)",
        "Statement-match confirmation date",
    ),
    "closed-by-researcher": (
        "Closed-by-researcher confirmation",
        "Closed-by-researcher scope",
        "Closed-by-researcher confirmed by (consented identifier or role)",
        "Closed-by-researcher confirmation date",
    ),
}
RESEARCH_RUN_DECISION_FIELD = "Researcher decision and qualifications"
RESEARCH_RUN_HARNESS_HEADINGS = (
    "## Bounded branch plan",
    "## Branch ledger",
    "## Execution records",
    "## Automation signals",
    "## Formalization boundary",
)
RESEARCH_RUN_ROLES = {
    "idea-generator",
    "solver",
    "adversary",
    "repairer",
    "formalizer",
    "statement-matcher",
    "synthesizer",
}
RESEARCH_RUN_CONTEXTS = {"fresh-isolated", "independent-proof-audit", "same-context-audit", "human", "tool"}
RESEARCH_RUN_BRANCH_STATES = {
    "planned",
    "running",
    "candidate-produced",
    "failed",
    "stopped",
}
RESEARCH_RUN_STOP_REASONS = {
    "candidate-produced",
    "counterexample-produced",
    "budget-exhausted",
    "contract-ambiguity",
    "repeated-failure",
    "tool-error",
    "safety-or-consent-boundary",
    "human-stop",
}
RESEARCH_RUN_AUTOMATION_SIGNALS = {
    "candidate-green",
    "branch-convergence",
    "model-convergence",
    "two-of-three-agreement",
    "adversary-conceded",
    "no-error-found",
}
BRANCH_ID = re.compile(r"Branch-\d{3}")
ATTEMPT_ID = re.compile(r"Attempt-\d{3}")
OBLIGATION_ID = re.compile(r"Obligation-\d{3}")
SHA256 = re.compile(r"sha256:[0-9a-f]{64}")
PLACEHOLDER_VALUES = {
    "",
    "-",
    "—",
    "...",
    "all",
    "everything",
    "general",
    "n/a",
    "na",
    "none",
    "not specified",
    "placeholder",
    "tbd",
    "todo",
    "unbounded",
    "yyyy-mm-dd",
}


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


def markdown_subsection(text: str, heading: str) -> str:
    if heading not in text:
        return ""
    after_heading = text.split(heading, 1)[1]
    next_heading = re.search(r"^#{2,3}\s+", after_heading, re.MULTILINE)
    return after_heading[: next_heading.start()] if next_heading else after_heading


def normalized_table_id(value: str) -> str:
    return value.strip().strip("`*_ ")


def substantive_value(value: str) -> bool:
    """Return whether a compact Markdown field is more than a placeholder."""
    normalized = normalized_table_id(value).strip().strip('"\'').casefold()
    return normalized not in PLACEHOLDER_VALUES and not re.fullmatch(
        r"[<{\[].*?[>}\]]", normalized
    )


def markdown_bullet_value(section: str, label: str) -> str | None:
    """Return one exact list-field value, accepting an indented continuation."""
    match = re.search(
        rf"^[ \t]*-[ \t]+{re.escape(label)}:[ \t]*(.*?)[ \t]*$",
        section,
        re.MULTILINE,
    )
    if match is None:
        return None
    inline = match.group(1).strip()
    if inline:
        return inline
    continuation: list[str] = []
    for line in section[match.end() :].splitlines():
        if re.match(r"^\s*-\s+[^:]+:", line) or re.match(r"^#{2,3}\s+", line):
            break
        if line.strip():
            continuation.append(line.strip())
    return " ".join(continuation)


def markdown_table_rows(
    section: str, expected_header: tuple[str, ...]
) -> tuple[bool, list[list[str]]]:
    """Return rows from the first table with an exact normalized header."""
    found = False
    rows: list[list[str]] = []
    for line in section.splitlines():
        cells = split_markdown_table_row(line)
        if not cells:
            if found and rows:
                break
            continue
        normalized = tuple(normalized_table_id(cell).casefold() for cell in cells)
        if not found:
            if normalized == tuple(item.casefold() for item in expected_header):
                found = True
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
            continue
        rows.append(cells)
    return found, rows


def repository_relative_artifact(value: str) -> Path | None:
    """Resolve a safe repository-relative POSIX artifact path."""
    if not value or "\\" in value or re.match(r"^[A-Za-z]:", value):
        return None
    candidate = Path(value)
    if candidate.is_absolute() or "." in candidate.parts or ".." in candidate.parts:
        return None
    unresolved = ROOT / candidate
    cursor = ROOT
    for part in candidate.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return None
    resolved = unresolved.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return unresolved


def validate_research_run_harness(
    path: Path,
    text: str,
    data: dict[str, str],
    errors: list[str],
) -> None:
    """Validate migrate-on-touch bounded-branch and formalization records."""
    present = {
        heading
        for heading in RESEARCH_RUN_HARNESS_HEADINGS
        if re.search(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE)
    }
    relative = path.relative_to(ROOT)
    missing = [heading for heading in RESEARCH_RUN_HARNESS_HEADINGS if heading not in present]
    if present and missing:
        errors.append(
            f"research-run harness is missing heading(s) {', '.join(repr(item) for item in missing)}: {relative}; restore the optional research-run extensions; omit them only when no branch, independent-context, or formal record needs them"
        )
        return

    obligation_section = markdown_subsection(text, "## Obligations")
    obligation_header = (
        "Obligation",
        "Exact subclaim or test",
        "Depends on",
        "What would establish it",
        "What would refute it",
        "State",
    )
    found_obligation_table, obligation_rows = markdown_table_rows(
        obligation_section, obligation_header
    )
    if not found_obligation_table:
        errors.append(f"research-run harness has an invalid Obligations header: {relative}")
    obligations: set[str] = set()
    for row in obligation_rows:
        if len(row) != len(obligation_header):
            errors.append(
                f"research-run Obligations row has {len(row)} cells; expected 6: {relative}"
            )
            continue
        obligation = normalized_table_id(row[0])
        if not substantive_value(obligation):
            continue
        if OBLIGATION_ID.fullmatch(obligation) is None:
            errors.append(f"invalid research-run obligation ID {obligation!r}: {relative}")
            continue
        if obligation in obligations:
            errors.append(f"duplicate research-run obligation ID {obligation!r}: {relative}")
            continue
        obligations.add(obligation)

    attempt_section = markdown_subsection(text, "## Attempt ledger")
    attempt_header = (
        "Attempt",
        "Date",
        "Obligation",
        "Direction",
        "Branch",
        "Context",
        "Method or adapter",
        "Result",
        "Artifact, limits, or failure reason",
    )
    found_attempt_table, attempt_rows = markdown_table_rows(
        attempt_section, attempt_header
    )
    if not found_attempt_table and not present:
        # The pre-branch template had Context but no Branch column. Read it
        # without rewriting history; still check references and provenance.
        legacy_header = attempt_header[:4] + attempt_header[5:]
        found_attempt_table, legacy_rows = markdown_table_rows(attempt_section, legacy_header)
        if found_attempt_table:
            attempt_rows = []
            for row in legacy_rows:
                if len(row) != len(legacy_header):
                    errors.append(f"legacy research-run Attempt ledger row has {len(row)} cells; expected 8: {relative}")
                else:
                    attempt_rows.append(row[:4] + ["none"] + row[4:])
    if not found_attempt_table:
        errors.append(f"research-run harness has an invalid Attempt ledger header: {relative}")
    attempts: dict[str, tuple[str, str, str]] = {}
    for row in attempt_rows:
        if len(row) != len(attempt_header):
            errors.append(
                f"research-run Attempt ledger row has {len(row)} cells; expected 9: {relative}"
            )
            continue
        attempt = normalized_table_id(row[0])
        if not substantive_value(attempt):
            continue
        if ATTEMPT_ID.fullmatch(attempt) is None:
            errors.append(f"invalid research-run attempt ID {attempt!r}: {relative}")
            continue
        if attempt in attempts:
            errors.append(f"duplicate research-run attempt ID {attempt!r}: {relative}")
            continue
        if not valid_iso_date(normalized_table_id(row[1])):
            errors.append(f"research-run attempt {attempt} requires a real ISO date: {relative}")
        obligation = normalized_table_id(row[2])
        if obligation not in obligations:
            errors.append(
                f"research-run attempt {attempt} references unknown obligation {obligation!r}: {relative}"
            )
        direction = normalized_table_id(row[3]).casefold()
        if direction not in {"prove", "disprove", "check"}:
            errors.append(
                f"research-run attempt {attempt} has invalid direction {direction!r}: {relative}"
            )
        branch = normalized_table_id(row[4])
        if branch != "none" and BRANCH_ID.fullmatch(branch) is None:
            errors.append(
                f"research-run attempt {attempt} has invalid branch {branch!r}: {relative}"
            )
        context = normalized_table_id(row[5]).casefold()
        if context not in RESEARCH_RUN_CONTEXTS:
            errors.append(
                f"research-run attempt {attempt} has invalid context {context!r}: {relative}"
            )
        if context == "independent-proof-audit" and direction != "check":
            errors.append(f"independent-proof-audit attempt {attempt} requires direction check: {relative}")
        attempts[attempt] = (obligation, branch, context)

    evidence_section = markdown_subsection(text, "## Adapter and evidence records")
    formal_claimed = data.get("review_status") in {"formal-tool-checked", "human-and-formal"}
    formal_claimed = formal_claimed or any(
        normalized_table_id(cells[0]).casefold() == "formal-encoding-checked"
        for line in evidence_section.splitlines()
        if (cells := split_markdown_table_row(line))
    )
    if not present:
        for attempt, (_, branch, context) in attempts.items():
            if branch != "none" or context in {"fresh-isolated", "independent-proof-audit"}:
                errors.append(f"research-run attempt {attempt} requires the optional execution records for its branch or independent context: {relative}")
        if formal_claimed or data.get("adapter") == "formalization":
            errors.append(f"formal review, evidence, or adapter requires the optional Formalization boundary and manifest: {relative}")
        if data.get("adapter") == "mixed" and "formalization" in data.get("adapter_scope", "").casefold():
            errors.append(f"mixed formalization adapter requires the optional Formalization boundary: {relative}")
        return

    branch_section = markdown_subsection(text, "## Branch ledger")
    branch_header = ("Branch", "Parent", "Obligation", "Role", "Attempt", "State")
    found_branch_table, branch_rows = markdown_table_rows(branch_section, branch_header)
    if not found_branch_table:
        errors.append(f"research-run harness has an invalid Branch ledger header: {relative}")
    branches: dict[str, str] = {}
    branch_roles: dict[str, str] = {}
    branch_obligations: dict[str, str] = {}
    branch_attempts: dict[str, str] = {}
    branch_states: dict[str, str] = {}
    for row in branch_rows:
        if len(row) != len(branch_header):
            errors.append(f"research-run Branch ledger row has {len(row)} cells; expected 6: {relative}")
            continue
        branch = normalized_table_id(row[0])
        if not substantive_value(branch):
            continue
        if BRANCH_ID.fullmatch(branch) is None:
            errors.append(f"invalid research-run branch ID {branch!r}: {relative}")
            continue
        if branch in branches:
            errors.append(f"duplicate research-run branch ID {branch!r}: {relative}")
            continue
        parent = normalized_table_id(row[1])
        obligation = normalized_table_id(row[2])
        role = normalized_table_id(row[3]).casefold()
        attempt = normalized_table_id(row[4])
        state = normalized_table_id(row[5]).casefold()
        if parent != "root" and BRANCH_ID.fullmatch(parent) is None:
            errors.append(f"research-run branch {branch} has invalid parent {parent!r}: {relative}")
        if OBLIGATION_ID.fullmatch(obligation) is None:
            errors.append(f"research-run branch {branch} has invalid obligation {obligation!r}: {relative}")
        if role not in RESEARCH_RUN_ROLES:
            errors.append(f"research-run branch {branch} has invalid role {role!r}: {relative}")
        if attempt != "none" and ATTEMPT_ID.fullmatch(attempt) is None:
            errors.append(f"research-run branch {branch} has invalid attempt {attempt!r}: {relative}")
        if state not in RESEARCH_RUN_BRANCH_STATES:
            errors.append(f"research-run branch {branch} has invalid state {state!r}: {relative}")
        branches[branch] = parent
        branch_roles[branch] = role
        branch_obligations[branch] = obligation
        branch_attempts[branch] = attempt
        branch_states[branch] = state
    for branch, parent in branches.items():
        if parent == branch:
            errors.append(f"research-run branch {branch} cannot be its own parent: {relative}")
        elif parent != "root" and parent not in branches:
            errors.append(f"research-run branch {branch} has unknown parent {parent!r}: {relative}")
    for branch in sorted(branches):
        seen: set[str] = set()
        cursor = branch
        while cursor in branches and branches[cursor] != "root":
            if cursor in seen:
                errors.append(f"cyclic research-run branch genealogy at {branch}: {relative}")
                break
            seen.add(cursor)
            cursor = branches[cursor]

    for branch in sorted(branches):
        obligation = branch_obligations[branch]
        attempt = branch_attempts[branch]
        state = branch_states[branch]
        if obligation not in obligations:
            errors.append(
                f"research-run branch {branch} references unknown obligation {obligation!r}: {relative}"
            )
        if attempt != "none":
            record = attempts.get(attempt)
            if record is None:
                errors.append(
                    f"research-run branch {branch} references unknown attempt {attempt!r}: {relative}"
                )
            else:
                attempt_obligation, attempt_branch, _ = record
                if attempt_branch != branch:
                    errors.append(
                        f"research-run branch {branch} attempt {attempt} is assigned to {attempt_branch!r} in the Attempt ledger: {relative}"
                    )
                if attempt_obligation != obligation:
                    errors.append(
                        f"research-run branch {branch} attempt {attempt} has obligation {attempt_obligation!r}, expected {obligation!r}: {relative}"
                    )
        if state in {"candidate-produced", "failed", "stopped"} and attempt == "none":
            errors.append(
                f"terminal research-run branch {branch} requires an Attempt ledger reference: {relative}"
            )

    execution_section = markdown_subsection(text, "## Execution records")
    execution_header = (
        "Attempt",
        "Branch",
        "Provider, model, and version",
        "Prompt artifact and SHA-256",
        "Rendered prompt SHA-256",
        "Context and input bundle with SHA-256",
        "Originating reasoning supplied",
        "Parent or sibling reasoning supplied",
        "Seed and sampling",
        "Budget and usage",
        "Stop reason",
        "Output artifact and SHA-256",
    )
    found_execution_table, execution_rows = markdown_table_rows(
        execution_section, execution_header
    )
    if not found_execution_table:
        errors.append(f"research-run harness has an invalid Execution records header: {relative}")
    executions: dict[str, tuple[str, str]] = {}
    for row in execution_rows:
        if len(row) != len(execution_header):
            errors.append(f"research-run Execution records row has {len(row)} cells; expected 12: {relative}")
            continue
        attempt = normalized_table_id(row[0])
        if not substantive_value(attempt):
            continue
        if ATTEMPT_ID.fullmatch(attempt) is None:
            errors.append(f"invalid research-run execution attempt {attempt!r}: {relative}")
            continue
        if attempt in executions:
            errors.append(f"duplicate research-run execution attempt {attempt!r}: {relative}")
        branch = normalized_table_id(row[1])
        if branch not in branches:
            errors.append(f"research-run execution {attempt} references unknown branch {branch!r}: {relative}")
        if not substantive_value(row[2]):
            errors.append(f"research-run execution {attempt} requires provider/model/version or 'not exposed': {relative}")
        if SHA256.search(row[3]) is None:
            errors.append(f"research-run execution {attempt} requires a prompt artifact SHA-256: {relative}")
        if SHA256.fullmatch(normalized_table_id(row[4])) is None:
            errors.append(f"research-run execution {attempt} requires an exact rendered prompt SHA-256: {relative}")
        context = normalized_table_id(row[5].split(";", 1)[0]).casefold()
        if context not in RESEARCH_RUN_CONTEXTS or SHA256.search(row[5]) is None:
            errors.append(f"research-run execution {attempt} requires one context value and input-bundle SHA-256: {relative}")
            context = ""
        originating_reasoning = normalized_table_id(row[6]).casefold()
        related_reasoning = normalized_table_id(row[7]).casefold()
        if originating_reasoning not in {"yes", "no"}:
            errors.append(f"research-run execution {attempt} Originating reasoning supplied must be yes or no: {relative}")
        if related_reasoning not in {"yes", "no"}:
            errors.append(f"research-run execution {attempt} Parent or sibling reasoning supplied must be yes or no: {relative}")
        if context == "fresh-isolated" and originating_reasoning != "no":
            errors.append(f"fresh-isolated research-run execution {attempt} must not receive originating reasoning: {relative}")
        if context == "fresh-isolated" and related_reasoning != "no":
            errors.append(f"fresh-isolated research-run execution {attempt} must not receive parent or sibling reasoning: {relative}")
        if context == "fresh-isolated" and branch_roles.get(branch) == "repairer":
            errors.append(f"repairer research-run execution {attempt} cannot be fresh-isolated: {relative}")
        if context == "independent-proof-audit" and related_reasoning != "no":
            errors.append(f"independent-proof-audit execution {attempt} must exclude other attempts and prior reviewer verdicts: {relative}")
        if context == "independent-proof-audit" and originating_reasoning != "yes":
            errors.append(f"independent-proof-audit execution {attempt} must receive the exact candidate proof as originating reasoning: {relative}")
        for index, label in ((8, "seed and sampling"), (9, "budget and usage")):
            if not substantive_value(row[index]):
                errors.append(f"research-run execution {attempt} requires {label}: {relative}")
        stop_reason = normalized_table_id(row[10]).casefold()
        if stop_reason not in RESEARCH_RUN_STOP_REASONS:
            errors.append(f"research-run execution {attempt} has invalid stop reason {stop_reason!r}: {relative}")
        output = normalized_table_id(row[11])
        if output != "not-produced" and SHA256.search(row[11]) is None:
            errors.append(f"research-run execution {attempt} requires an output SHA-256 or not-produced: {relative}")
        if stop_reason in {"candidate-produced", "counterexample-produced"} and SHA256.search(row[11]) is None:
            errors.append(f"research-run execution {attempt} produced a candidate without a hashed output artifact: {relative}")
        executions[attempt] = (branch, context)

    for attempt, (branch, context) in sorted(executions.items()):
        record = attempts.get(attempt)
        if record is None:
            errors.append(
                f"research-run execution {attempt} has no matching Attempt ledger row: {relative}"
            )
            continue
        _, attempt_branch, attempt_context = record
        if attempt_branch != branch:
            errors.append(
                f"research-run execution {attempt} branch {branch!r} does not match Attempt ledger branch {attempt_branch!r}: {relative}"
            )
        if attempt_context != context:
            errors.append(
                f"research-run execution {attempt} context {context!r} does not match Attempt ledger context {attempt_context!r}: {relative}"
            )
        if branch_attempts.get(branch) != attempt:
            errors.append(
                f"research-run execution {attempt} is not the attempt recorded for branch {branch!r}: {relative}"
            )
    for branch, attempt in sorted(branch_attempts.items()):
        if attempt != "none" and attempt not in executions:
            errors.append(
                f"research-run branch {branch} attempt {attempt} has no Execution records row: {relative}"
            )
    for attempt, (_, branch, context) in sorted(attempts.items()):
        if branch != "none" and branch not in branches:
            errors.append(
                f"research-run attempt {attempt} references unknown branch {branch!r}: {relative}"
            )
        if (branch != "none" or context in {"fresh-isolated", "independent-proof-audit"}) and attempt not in executions:
            errors.append(
                f"research-run attempt {attempt} branch or independent context has no Execution records row: {relative}"
            )

    signal_section = markdown_subsection(text, "## Automation signals")
    signal_header = ("Signal", "Exact branch or artifact version", "Basis", "Closure effect")
    found_signal_table, signal_rows = markdown_table_rows(signal_section, signal_header)
    if not found_signal_table:
        errors.append(f"research-run harness has an invalid Automation signals header: {relative}")
    for row in signal_rows:
        if len(row) != len(signal_header):
            errors.append(f"research-run Automation signals row has {len(row)} cells; expected 4: {relative}")
            continue
        signal = normalized_table_id(row[0]).casefold()
        if not substantive_value(signal):
            continue
        if signal not in RESEARCH_RUN_AUTOMATION_SIGNALS:
            errors.append(f"invalid research-run automation signal {signal!r}: {relative}")
        if normalized_table_id(row[3]).casefold() != "none":
            errors.append(f"research-run automation signal {signal!r} must have Closure effect 'none': {relative}")

    plan_section = markdown_subsection(text, "## Bounded branch plan")
    execution_mode = markdown_bullet_value(plan_section, "Execution mode")
    if execution_mode is not None and normalized_table_id(execution_mode) not in {"single-attempt", "bounded-branch-loop", "not used"}:
        errors.append(f"invalid research-run Execution mode: {relative}")

    formal_section = markdown_subsection(text, "## Formalization boundary")
    formal_record = markdown_bullet_value(formal_section, "Formal-encoding record")
    if formal_record is not None:
        formal_record = normalized_table_id(formal_record)
        if formal_record not in {"unchecked", "recorded-pass", "recorded-fail", "conflict"}:
            errors.append(f"invalid research-run Formal-encoding record: {relative}")
    formal_claimed = formal_claimed or formal_record == "recorded-pass"
    manifest_value = markdown_bullet_value(formal_section, "Formalization manifest")
    if manifest_value is None:
        errors.append(f"research-run Formalization boundary is missing 'Formalization manifest': {relative}")
        return
    manifest_value = normalized_table_id(manifest_value)
    if manifest_value.casefold() == "not used":
        if formal_claimed or formal_record not in {None, "unchecked"}:
            errors.append(f"formal review or evidence requires a validated formalization manifest: {relative}")
        return
    manifest_path = repository_relative_artifact(manifest_value)
    if manifest_path is None or manifest_path.suffix.lower() != ".json":
        errors.append(f"Formalization manifest must be a safe repository-relative JSON path: {relative}")
        return
    if manifest_path.is_symlink() or not manifest_path.is_file():
        errors.append(f"Formalization manifest does not exist as a regular file: {manifest_value}: {relative}")
        return
    manifest_errors = validate_manifest_path(
        manifest_path, root=ROOT, verify_files=formal_claimed
    )
    for item in manifest_errors:
        errors.append(f"invalid formalization manifest {manifest_value}: {item}: {relative}")
    manifest_data, read_errors = read_manifest(manifest_path)
    if read_errors or manifest_data is None:
        return
    if manifest_data.get("run_id") != data.get("run_id"):
        errors.append(f"formalization manifest run_id does not match research run: {relative}")
    obligation_id = manifest_data.get("obligation_id")
    if isinstance(obligation_id, str) and obligation_id not in text:
        errors.append(f"formalization manifest obligation_id is not present in the research run: {relative}")
    if formal_record is not None and formal_record != manifest_data.get("final_record", {}).get("formal_encoding"):
        errors.append(f"Formal-encoding record contradicts the formalization manifest: {relative}")
    if formal_claimed and manifest_data.get("final_record", {}).get("formal_encoding") != "recorded-pass":
        errors.append(f"formal review or evidence requires final_record.formal_encoding recorded-pass: {relative}")


def valid_date_in_text(value: str) -> bool:
    return any(valid_iso_date(item) for item in re.findall(r"\d{4}-\d{2}-\d{2}", value))


def review_provenance_valid(value: str) -> bool:
    return any(
        value == prefix
        or (
            value.startswith(prefix)
            and value[len(prefix) : len(prefix) + 1] in {" ", "(", "[", ":", ";", "-", "—"}
        )
        for prefix in REVIEW_PROVENANCE_PREFIXES
    )


def validate_research_run(
    path: Path,
    text: str,
    data: dict[str, str] | None,
    errors: list[str],
    warnings: list[str],
) -> None:
    """Validate the optional research-run extension of a research log."""
    run_heading = re.search(r"^# Research run\s*$", text, re.MULTILINE)
    if not run_heading and (data is None or not (RESEARCH_RUN_FIELDS & data.keys())):
        return
    if data is None:
        errors.append(f"research run requires research-log frontmatter: {path.relative_to(ROOT)}")
        return
    relative = path.relative_to(ROOT)
    if data.get("type") != "research-log":
        errors.append(f"research-run metadata requires type research-log: {relative}")

    run_id = data.get("run_id", "")
    if not run_id:
        errors.append(
            f"research run_id is required when run metadata is present: {relative}"
        )
    else:
        match = RESEARCH_RUN_ID.fullmatch(run_id)
        if match is None:
            errors.append(f"invalid research run_id {run_id!r}: {relative}")
        else:
            run_date = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
            try:
                date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                errors.append(f"invalid calendar date in research run_id {run_id!r}: {relative}")
            else:
                frontmatter_date = data.get("date", "")
                if frontmatter_date and frontmatter_date != run_date:
                    errors.append(
                        f"research run_id date {run_date} does not match frontmatter date {frontmatter_date}: {relative}"
                    )
                filename_date = re.match(r"^(\d{4}-\d{2}-\d{2})-", path.name)
                if filename_date is not None and filename_date.group(1) != run_date:
                    errors.append(
                        f"research run_id date {run_date} does not match dated filename prefix {filename_date.group(1)}: {relative}"
                    )

    adapter = data.get("adapter", "")
    if adapter and adapter not in RESEARCH_RUN_ADAPTERS:
        errors.append(f"invalid research-run adapter {adapter!r}: {relative}")
    adapter_scope = data.get("adapter_scope", "")
    if adapter and not adapter_scope:
        errors.append(
            f"research-run adapter_scope is required when adapter is set: {relative}"
        )
    if adapter_scope and not adapter:
        errors.append(
            f"research-run adapter is required when adapter_scope is set: {relative}"
        )
    if adapter == "mixed" and adapter_scope:
        scopes = [scope.strip() for scope in adapter_scope.split(";")]
        if len(scopes) < 2 or any(not substantive_value(scope) for scope in scopes):
            errors.append(
                f"mixed research-run adapter_scope requires at least two semicolon-separated bounded scopes: {relative}"
            )

    for heading in RESEARCH_RUN_HEADINGS:
        if re.search(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE) is None:
            errors.append(
                f"research run missing {heading!r}: {relative}; restore the research-run contract; ordinary logs must omit both run metadata and run structure"
            )

    contract_section = markdown_subsection(text, "## Problem Contract")
    if contract_section:
        for field in RESEARCH_RUN_CONTRACT_FIELDS:
            value = markdown_bullet_value(contract_section, field)
            if value is None or not substantive_value(value):
                errors.append(
                    f"research run Problem Contract {field!r} requires a non-placeholder value: {relative}"
                )

    obligation_section = markdown_subsection(text, "## Obligations")
    substantive_obligation = False
    for line in obligation_section.splitlines():
        cells = split_markdown_table_row(line)
        if len(cells) >= 2 and re.fullmatch(
            r"Obligation-\d{3}", normalized_table_id(cells[0])
        ):
            substantive_obligation = substantive_obligation or substantive_value(cells[1])
    if obligation_section and not substantive_obligation:
        warnings.append(
            f"research run has no substantive Obligation-NNN row yet; acceptable only while the run remains at early SPEC: {relative}"
        )

    promotion_section = markdown_subsection(text, "## Human promotion")
    confirmation_records: dict[str, tuple[bool, bool]] = {}
    if promotion_section:
        if markdown_bullet_value(promotion_section, RESEARCH_RUN_DECISION_FIELD) is None:
            errors.append(
                f"research run Human promotion missing exact field {RESEARCH_RUN_DECISION_FIELD!r}: {relative}; restore the research-run contract; ordinary logs must omit both run metadata and run structure"
            )
        for gate, labels in RESEARCH_RUN_CONFIRMATION_FIELDS.items():
            status_label, scope_label, actor_label, date_label = labels
            values = {
                label: markdown_bullet_value(promotion_section, label) for label in labels
            }
            missing_labels = [label for label, value in values.items() if value is None]
            if missing_labels:
                errors.append(
                    f"research run Human promotion missing exact field(s) {', '.join(repr(item) for item in missing_labels)}: {relative}; restore the research-run contract; ordinary logs must omit both run metadata and run structure"
                )
                confirmation_records[gate] = (False, False)
                continue
            status = (values[status_label] or "").strip().casefold()
            if status not in {"not confirmed", "confirmed"}:
                errors.append(
                    f"research run {status_label!r} must be 'not confirmed' or 'confirmed': {relative}"
                )
            details_valid = all(
                substantive_value(values[label] or "") for label in (scope_label, actor_label)
            ) and valid_iso_date((values[date_label] or "").strip())
            if status == "confirmed" and not details_valid:
                errors.append(
                    f"research run {gate} confirmation requires non-placeholder scope and consented identifier or role plus a real ISO date; lint checks structure and date only, not human identity: {relative}"
                )
            if status != "not confirmed" and not valid_iso_date(
                (values[date_label] or "").strip()
            ):
                errors.append(
                    f"research run {gate} confirmation requires a real ISO date when not 'not confirmed'; lint checks date syntax only and does not verify human identity: {relative}"
                )
            confirmation_records[gate] = (status == "confirmed", details_valid)

    evidence_section = markdown_subsection(text, "## Adapter and evidence records")
    for line in evidence_section.splitlines():
        cells = split_markdown_table_row(line)
        if not cells:
            continue
        descriptor = normalized_table_id(cells[0]).casefold()
        if descriptor == "statement-matched" and confirmation_records.get(
            "statement-match"
        ) != (True, True):
            errors.append(
                f"statement-matched evidence requires a non-default human statement-match confirmation with scope, consented identifier or role, and real ISO date; lint does not verify human identity: {relative}"
            )

    validate_research_run_harness(path, text, data, errors)


def parsed_dependencies(value: str) -> tuple[list[str], bool]:
    """Return stable IDs and whether a dependency cell contains free-form text."""
    normalized = normalized_table_id(value)
    if normalized.casefold() in {"", "-", "—", "none", "n/a", "na"}:
        return [], False
    dependencies = STABLE_RESEARCH_ID_IN_TEXT.findall(normalized)
    remainder = STABLE_RESEARCH_ID_IN_TEXT.sub("", normalized)
    remainder = re.sub(r"(?i)<br\s*/?>|\band\b", "", remainder)
    remainder = re.sub(r"[\s,;+/&]+", "", remainder)
    return dependencies, bool(remainder)


def dependency_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    """Return deterministic claim-dependency cycles, with each cycle reported once."""
    state: dict[str, int] = {}
    stack: list[str] = []
    stack_index: dict[str, int] = {}
    cycles: dict[tuple[str, ...], list[str]] = {}

    def canonical(nodes: list[str]) -> tuple[str, ...]:
        rotations = [tuple(nodes[index:] + nodes[:index]) for index in range(len(nodes))]
        return min(rotations)

    def visit(node: str) -> None:
        state[node] = 1
        stack_index[node] = len(stack)
        stack.append(node)
        for dependency in sorted(graph.get(node, [])):
            if dependency not in graph:
                continue
            if state.get(dependency, 0) == 0:
                visit(dependency)
            elif state.get(dependency) == 1:
                cycle = stack[stack_index[dependency] :]
                key = canonical(cycle)
                cycles.setdefault(key, list(key))
        stack.pop()
        stack_index.pop(node, None)
        state[node] = 2

    for node in sorted(graph):
        if state.get(node, 0) == 0:
            visit(node)
    return [cycles[key] for key in sorted(cycles)]


def validate_research_state_spine(
    path: Path,
    text: str,
    data: dict[str, str] | None,
    errors: list[str],
    warnings: list[str],
) -> None:
    if data is None or data.get("type") != "project" or path.name != "README.md":
        return
    relative = path.relative_to(ROOT)
    if "## Research State Spine" not in text:
        if STATE_SPINE_HEADER in text:
            errors.append(f"Research State Spine missing its section heading: {relative}")
            return
        if LEGACY_CLAIM_HEADER in text or re.search(r"^\|\s*C1\s*\|", text, re.MULTILINE):
            warnings.append(
                f"legacy project claim ledger; optional per-project migration available: {relative}"
            )
        return

    for heading in (
        "## Research State Spine",
        "### Definition registry",
        "### Claim ledger",
        "### Open gaps",
    ):
        if heading not in text:
            errors.append(f"Research State Spine missing {heading!r}: {relative}")
    if STATE_SPINE_HEADER not in text:
        errors.append(f"Research State Spine has an invalid claim-ledger header: {relative}")

    spine_start = text.index("## Research State Spine")
    after_spine_heading = text[spine_start + len("## Research State Spine") :]
    next_section = re.search(r"^##(?!#)\s+", after_spine_heading, re.MULTILINE)
    spine_text = (
        after_spine_heading[: next_section.start()]
        if next_section is not None
        else after_spine_heading
    )

    stable_ids: list[str] = []
    claim_rows: dict[str, tuple[str, str, str]] = {}
    table_specs = (
        ("### Definition registry", re.compile(r"Def-\d{3}"), 4),
        ("### Claim ledger", re.compile(r"(?:Lem|Prop|Thm|Cor)-\d{3}"), 8),
        ("### Open gaps", re.compile(r"Gap-\d{3}"), 6),
    )
    for heading, id_pattern, expected_cells in table_specs:
        section = markdown_subsection(spine_text, heading)
        for line in section.splitlines():
            cells = split_markdown_table_row(line)
            if not cells:
                continue
            first_cell = normalized_table_id(cells[0])
            if first_cell == "ID" or re.fullmatch(r":?-+:?", first_cell):
                continue
            if not first_cell:
                warnings.append(f"blank stable research ID in {heading}: {relative}")
                continue
            if id_pattern.fullmatch(first_cell) is None:
                errors.append(
                    f"invalid stable research ID {first_cell!r} in {heading}: {relative}"
                )
                continue
            stable_ids.append(first_cell)
            if len(cells) != expected_cells:
                errors.append(
                    f"Research State Spine row for {first_cell} has {len(cells)} cells; expected {expected_cells}: {relative}"
                )
                continue
            if heading == "### Claim ledger":
                mathematical_state = cells[2]
                depends_on = cells[3]
                evidence_or_source = cells[4]
                review_provenance = cells[5]
                integration_state = cells[6]
                if mathematical_state not in MATHEMATICAL_STATES:
                    errors.append(
                        f"invalid mathematical state {mathematical_state!r} for {first_cell}: {relative}"
                    )
                if not review_provenance_valid(review_provenance):
                    errors.append(
                        f"invalid review provenance {review_provenance!r} for {first_cell}: {relative}"
                    )
                if integration_state not in INTEGRATION_STATES:
                    errors.append(
                        f"invalid integration state {integration_state!r} for {first_cell}: {relative}"
                    )
                if mathematical_state == "closed-by-researcher":
                    dated_human_review = (
                        review_provenance.startswith("human-reviewed")
                        or review_provenance.startswith("human-and-formal")
                    ) and valid_date_in_text(review_provenance)
                    if not substantive_value(evidence_or_source) or not dated_human_review:
                        errors.append(
                            f"closed-by-researcher {first_cell} requires nonempty evidence or source and dated human-reviewed or human-and-formal provenance; lint checks structure and date only, not reviewer identity: {relative}"
                        )
                claim_rows[first_cell] = (
                    mathematical_state,
                    integration_state,
                    depends_on,
                )

    duplicates = sorted({item for item in stable_ids if stable_ids.count(item) > 1})
    if duplicates:
        errors.append(
            f"duplicate stable research IDs {', '.join(duplicates)}: {relative}"
        )

    known_ids = set(stable_ids)
    dependency_graph: dict[str, list[str]] = {}
    for claim_id, (_, _, dependency_text) in claim_rows.items():
        dependencies, has_freeform = parsed_dependencies(dependency_text)
        dependency_graph[claim_id] = dependencies
        if has_freeform:
            warnings.append(
                f"legacy or free-form dependency for {claim_id}; use stable research IDs: {relative}"
            )
        for dependency in sorted(set(dependencies)):
            if dependency not in known_ids:
                errors.append(
                    f"unknown dependency {dependency!r} for {claim_id}: {relative}"
                )
            if dependency == claim_id:
                errors.append(f"self dependency for {claim_id}: {relative}")

    for claim_id in sorted(claim_rows):
        _, downstream_integration_state, _ = claim_rows[claim_id]
        if downstream_integration_state != "integrated":
            continue
        pending = [([dependency], dependency) for dependency in dependency_graph[claim_id]]
        visited: set[str] = set()
        while pending:
            path_to_upstream, upstream_id = pending.pop(0)
            if upstream_id in visited or upstream_id not in claim_rows:
                continue
            visited.add(upstream_id)
            upstream_math_state, upstream_integration_state, _ = claim_rows[upstream_id]
            if (
                upstream_integration_state in {"review-stale", "retired"}
                or upstream_math_state in {"gap-found", "refuted"}
            ):
                if len(path_to_upstream) == 1:
                    warnings.append(
                        f"integrated {claim_id} depends on stale, retired, gap-found, or refuted {upstream_id}: {relative}"
                    )
                else:
                    warnings.append(
                        f"integrated {claim_id} transitively depends on stale, retired, gap-found, or refuted {upstream_id} via {' -> '.join(path_to_upstream)}: {relative}"
                    )
            pending.extend(
                (path_to_upstream + [dependency], dependency)
                for dependency in dependency_graph.get(upstream_id, [])
                if dependency not in visited
            )

    for cycle in dependency_cycles(dependency_graph):
        if len(cycle) == 1:
            # The more precise self-dependency diagnostic was already emitted.
            continue
        errors.append(
            f"cyclic claim dependencies {' -> '.join(cycle + [cycle[0]])}: {relative}"
        )


def ticket_location(path: Path) -> bool:
    parts = path.relative_to(ROOT).parts
    return path.name == 'tickets' and (
        len(parts) == 3 and parts[0] == 'projects'
        or len(parts) >= 3 and parts[0] == 'papers'
    )


def validate_ticket_stores(stores: list[Path], errors: list[str]) -> set[Path]:
    """Route only canonical issue files; do not exempt arbitrary sidecar notes."""
    if not stores:
        return set()
    sys.path.insert(0, str(ROOT / 'meta/research-tickets/scripts'))
    try:
        from issue_index import IndexErrorDetail, FILE_RE
        from issue_store import IssueStore
        from ticket_project import load_project, load_paper
    except (ImportError, OSError, SyntaxError):
        errors.append('ticket engine is missing; restore the Workbench helpers')
        return set()
    owned = set()
    for store in stores:
        relative = store.relative_to(ROOT).as_posix()
        try:
            if relative.startswith('projects/'):
                root, config = load_project(store.parent)
            else:
                root, config = load_paper(store.parent.with_suffix('.md'))
            if root != store:
                errors.append(f'ticket store does not match the selected note: {relative}')
                continue
            engine = IssueStore(root)
            # Validate local data only; lint does not open registered external sources.
            with engine.index._lock() as directory:
                engine.index._assert_readable()
                snapshot = engine.index._refresh_locked(directory, force=True)
                engine._validate_harness(snapshot['records'])
            owned.update(p for p in (root / 'data/issues').iterdir() if FILE_RE.fullmatch(p.name))
        except IndexErrorDetail as error:
            errors.append(f'invalid research tickets ({error.code}): {relative}')
        except (OSError, ValueError):
            errors.append(f'research tickets could not be read safely: {relative}')
    return owned


def scan_content() -> tuple[list[Path], list[Path], list[Path], list[Path], list[Path], list[Path]]:
    markdown: list[Path] = []
    binaries: list[Path] = []
    links: list[Path] = []
    missing: list[Path] = []
    unreadable: list[Path] = []
    stores: list[Path] = []

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
                        if ticket_location(path):
                            stores.append(path)
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
        sorted(set(stores)),
    )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    files, binaries, links, missing, unreadable, stores = scan_content()
    ticket_files = validate_ticket_stores(stores, errors)
    stem_index: dict[str, list[Path]] = {}
    project_run_ids: dict[tuple[str, str], list[Path]] = {}
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
        if path in ticket_files:
            continue
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
            run_id = data.get("run_id", "").strip()
            if run_id:
                project_key = data.get("project", "").strip().casefold()
                project_run_ids.setdefault((project_key, run_id), []).append(path)

        validate_research_run(path, text, data, errors, warnings)
        validate_research_state_spine(path, text, data, errors, warnings)

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

    for (project_key, run_id), run_paths in sorted(project_run_ids.items()):
        if len(run_paths) < 2:
            continue
        locations = ", ".join(
            path.relative_to(ROOT).as_posix() for path in sorted(run_paths)
        )
        errors.append(
            f"duplicate research run_id {run_id!r} within project {project_key or '<unspecified>'!r}: {locations}"
        )

    for item in warnings:
        print(f"WARN: {item}")
    for item in errors:
        print(f"ERROR: {item}")
    print(f"Checked {len(files)} Markdown notes: {len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
