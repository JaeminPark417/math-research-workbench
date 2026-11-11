#!/usr/bin/env python3
"""Check a mathematical research run against its project sources and evidence."""
from __future__ import annotations

import argparse
import hashlib
import re
from datetime import date
from pathlib import Path

from formalization_manifest import read_manifest, validate_manifest_path
from math_target import COMMIT, SNAPSHOT_FIELD, check as check_math_target, local_path, split_markdown_table_row

YAML_KEY = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s*(.*))?$")

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


def repository_relative_artifact(root: Path, value: str) -> Path | None:
    """Resolve a safe repository-relative POSIX artifact path."""
    if not value or "\\" in value or re.match(r"^[A-Za-z]:", value):
        return None
    candidate = Path(value)
    if candidate.is_absolute() or "." in candidate.parts or ".." in candidate.parts:
        return None
    unresolved = root / candidate
    cursor = root
    for part in candidate.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return None
    resolved = unresolved.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None
    return unresolved


def check_decision_evidence(root: Path, decision: str, marker: str, source_ref: str) -> str | None:
    """Check the declared target version and bytes linked from one human decision."""
    parts = [part.strip() for part in decision.split("|")]
    if len(parts) != 3:
        return "expected target version | repository-relative evidence path | sha256:digest"
    version, relative, expected = parts
    source_version = source_ref.rsplit(";", 1)[-1].strip()
    if version != marker and not (COMMIT.fullmatch(source_version) and source_version == version):
        return "decision target version differs from the frozen target"
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", expected):
        return "expected a full SHA-256 for the decision evidence"
    artifact = repository_relative_artifact(root, relative)
    if artifact is None or not artifact.is_file():
        return "decision evidence must be a regular file inside the research repository"
    digest = hashlib.sha256()
    try:
        with artifact.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return "unable to read decision evidence"
    if expected != "sha256:" + digest.hexdigest():
        return "decision evidence bytes differ from the recorded digest"
    return None


def validate_research_run_harness(
    root: Path,
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
    relative = path.relative_to(root)
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
            errors.append(f"independent-proof-audit execution {attempt} must exclude other attempts and prior reviewer verdicts beyond the frozen candidate and its named dependencies: {relative}")
        if context == "independent-proof-audit" and originating_reasoning != "yes":
            errors.append(f"independent-proof-audit execution {attempt} must receive the exact candidate proof as originating reasoning; exclude the originating conversation: {relative}")
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
    manifest_path = repository_relative_artifact(root, manifest_value)
    if manifest_path is None or manifest_path.suffix.lower() != ".json":
        errors.append(f"Formalization manifest must be a safe repository-relative JSON path: {relative}")
        return
    if manifest_path.is_symlink() or not manifest_path.is_file():
        errors.append(f"Formalization manifest does not exist as a regular file: {manifest_value}: {relative}")
        return
    manifest_errors = validate_manifest_path(
        manifest_path, root=root, verify_files=formal_claimed
    )
    for item in manifest_errors:
        errors.append(f"invalid formalization manifest {manifest_value}: {item}: {relative}")
    if manifest_errors:
        return
    manifest_data, read_errors = read_manifest(manifest_path)
    if read_errors or manifest_data is None:
        return
    if manifest_data.get("run_id") != data.get("run_id"):
        errors.append(f"formalization manifest run_id does not match research run: {relative}")
    obligation_id = manifest_data.get("obligation_id")
    if not isinstance(obligation_id, str) or obligation_id not in obligations:
        errors.append(f"formalization manifest obligation_id is not declared in the Obligations table: {relative}")
    final_record = manifest_data.get("final_record")
    if not isinstance(final_record, dict):
        errors.append(f"formalization manifest final_record must be an object: {relative}")
        return
    if formal_record is not None and formal_record != final_record.get("formal_encoding"):
        errors.append(f"Formal-encoding record contradicts the formalization manifest: {relative}")
    if formal_claimed and final_record.get("formal_encoding") != "recorded-pass":
        errors.append(f"formal review or evidence requires final_record.formal_encoding recorded-pass: {relative}")


def validate_research_run(
    root: Path,
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
        errors.append(f"research run requires research-log frontmatter: {path.relative_to(root)}")
        return
    relative = path.relative_to(root)
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

    if contract_section or "## Problem Contract" in text:
        try:
            notice = check_math_target(root, path, text)
            if notice:
                warnings.append(f"{notice}: {relative}")
        except (OSError, ValueError) as exc:
            errors.append(f"invalid target binding: {exc}: {relative}")

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
            if status == "confirmed" and details_valid:
                marker = markdown_bullet_value(contract_section, SNAPSHOT_FIELD)
                if not marker:
                    warnings.append(f"legacy {gate} decision: verify the target version and decision evidence manually: {relative}")
                else:
                    evidence_label = status_label.replace(" confirmation", " decision evidence")
                    decision = markdown_bullet_value(promotion_section, evidence_label) or ""
                    source_ref = markdown_bullet_value(contract_section, "Spine target reference") or ""
                    issue = check_decision_evidence(root, decision, marker, source_ref)
                    if issue:
                        errors.append(f"{gate} decision evidence: {issue}: {relative}")

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

    validate_research_run_harness(root, path, text, data, errors)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="project repository or extracted workspace")
    parser.add_argument("--run", required=True, help="repository-relative research-run Markdown")
    args = parser.parse_args()
    root = args.root.resolve()
    errors, warnings = [], []
    try:
        path = local_path(root, args.run)
        text = path.read_text(encoding="utf-8")
        data = frontmatter(text)
        if not data or "run_id" not in data:
            raise ValueError("expected the shared research-run format (run_id in frontmatter)")
        validate_research_run(root, path, text, data, errors, warnings)
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
    for message in errors:
        print("ERROR:", message)
    for message in warnings:
        print("REVIEW:", message)
    if errors:
        return 1
    if warnings:
        return 2
    print("Validated the recorded run structure and its applicable source and evidence references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
