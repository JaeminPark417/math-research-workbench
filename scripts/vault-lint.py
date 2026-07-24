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
    if data is None or not (RESEARCH_RUN_FIELDS & data.keys()):
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
                f"research run missing {heading!r}: {relative}; restore the research-run template or remove all run metadata"
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
                f"research run Human promotion missing exact field {RESEARCH_RUN_DECISION_FIELD!r}: {relative}; restore the research-run template or remove all run metadata"
            )
        for gate, labels in RESEARCH_RUN_CONFIRMATION_FIELDS.items():
            status_label, scope_label, actor_label, date_label = labels
            values = {
                label: markdown_bullet_value(promotion_section, label) for label in labels
            }
            missing_labels = [label for label, value in values.items() if value is None]
            if missing_labels:
                errors.append(
                    f"research run Human promotion missing exact field(s) {', '.join(repr(item) for item in missing_labels)}: {relative}; restore the research-run template or remove all run metadata"
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
