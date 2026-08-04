#!/usr/bin/env python3
"""Validate recorded Lean evidence without executing or attesting commands.

The validator checks manifest structure and, with ``--verify-files``, local file
membership and hashes.  Recorded commands are never executed: it never runs
Lean, Lake, Git, or a checker.  Therefore ``recorded-pass`` means only that a
self-recorded evidence bundle is internally consistent; it is not an execution
attestation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any


RUN_ID = re.compile(r"Run-\d{8}-\d{3}")
OBLIGATION_ID = re.compile(r"(?:Obligation|Obl)-\d{3}")
BRANCH_ID = re.compile(r"Branch-\d{3}")
MANIFEST_ID = re.compile(r"Formalization-\d{3}")
SPINE_ID = re.compile(r"(?:Def|Lem|Prop|Thm|Cor|Gap)-\d{3}")
SHA256 = re.compile(r"sha256:[0-9a-f]{64}")
FULL_COMMIT = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
CHECK_RESULTS = {"not-run", "pass", "fail"}
PLACEHOLDERS = {
    "",
    "todo",
    "tbd",
    "yyyy-mm-dd",
    "run-yyyymmdd-nnn",
    "obligation-nnn",
    "obl-nnn",
    "branch-nnn",
}


class DuplicateKeyError(ValueError):
    """Raised when a JSON object contains a duplicate key."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _read_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        if path.stat().st_size > 262_144:
            return None, ["manifest exceeds the 256 KiB safety limit"]
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
    except FileNotFoundError:
        return None, ["manifest does not exist"]
    except (OSError, UnicodeError) as exc:
        return None, [f"manifest could not be read safely: {exc}"]
    except (json.JSONDecodeError, DuplicateKeyError) as exc:
        return None, [f"invalid manifest JSON: {exc}"]
    if not isinstance(value, dict):
        return None, ["manifest root must be a JSON object"]
    return value, []


def read_manifest(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Read a manifest with duplicate-key rejection for other local validators."""
    return _read_json(path)


def _object(value: Any, label: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return {}
    return value


def _exact_keys(
    value: dict[str, Any], required: set[str], label: str, errors: list[str]
) -> None:
    missing = sorted(required - value.keys())
    unknown = sorted(value.keys() - required)
    if missing:
        errors.append(f"{label} is missing key(s): {', '.join(missing)}")
    if unknown:
        errors.append(f"{label} has unknown key(s): {', '.join(unknown)}")


def _text(value: Any, label: str, errors: list[str], *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or value.strip().casefold() in PLACEHOLDERS:
        errors.append(f"{label} must be a non-placeholder string")
        return None
    stripped = value.strip()
    if any(
        stripped.startswith(opening) and stripped.endswith(closing)
        for opening, closing in (("<", ">"), ("[", "]"), ("{", "}"))
    ):
        errors.append(f"{label} must not be a template placeholder")
        return None
    return stripped


def _enum(value: Any, allowed: set[str], label: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or value not in allowed:
        errors.append(f"{label} must be one of {', '.join(sorted(allowed))}")
        return None
    return value


def _iso_date(value: Any, label: str, errors: list[str], *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        errors.append(f"{label} must be an ISO date")
        return None
    try:
        date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label} must be a real ISO date")
        return None
    return value


def _digest(value: Any, label: str, errors: list[str], *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        errors.append(f"{label} must be sha256 followed by 64 lowercase hexadecimal digits")
        return None
    return value


def _artifact_path(
    value: Any, label: str, errors: list[str], *, nullable: bool = False
) -> str | None:
    if value is None and nullable:
        return None
    text = _text(value, label, errors)
    if text is None:
        return None
    if "\\" in text or re.match(r"^[A-Za-z]:", text):
        errors.append(f"{label} must use a repository-relative POSIX path")
        return None
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts or "." in path.parts or not path.parts:
        errors.append(f"{label} must stay inside the repository and must not contain '.' or '..'")
        return None
    return path.as_posix()


def _path_is_within(path: str, root: str) -> bool:
    path_parts = PurePosixPath(path).parts
    root_parts = PurePosixPath(root).parts
    return len(path_parts) > len(root_parts) and path_parts[: len(root_parts)] == root_parts


def _roots_overlap(first: str, second: str) -> bool:
    first_parts = PurePosixPath(first).parts
    second_parts = PurePosixPath(second).parts
    return (
        first_parts == second_parts
        or first_parts[: len(second_parts)] == second_parts
        or second_parts[: len(first_parts)] == first_parts
    )


def _artifact_ref(
    value: Any,
    label: str,
    errors: list[str],
    refs: list[tuple[str, str, str]],
    *,
    nullable: bool = False,
) -> tuple[str | None, str | None]:
    obj = _object(value, label, errors)
    _exact_keys(obj, {"artifact", "sha256"}, label, errors)
    path = _artifact_path(obj.get("artifact"), f"{label}.artifact", errors, nullable=nullable)
    digest = _digest(obj.get("sha256"), f"{label}.sha256", errors, nullable=nullable)
    if (path is None) != (digest is None):
        errors.append(f"{label} must provide artifact and sha256 together")
    if path is not None and digest is not None:
        refs.append((path, digest, label))
    return path, digest


def _file_refs(
    value: Any,
    label: str,
    errors: list[str],
    refs: list[tuple[str, str, str]],
) -> list[tuple[str, str]]:
    if not isinstance(value, list) or not value:
        errors.append(f"{label} must be a nonempty list")
        return []
    entries: list[tuple[str, str]] = []
    for index, item in enumerate(value):
        item_label = f"{label}[{index}]"
        obj = _object(item, item_label, errors)
        _exact_keys(obj, {"path", "sha256"}, item_label, errors)
        path = _artifact_path(obj.get("path"), f"{item_label}.path", errors)
        digest = _digest(obj.get("sha256"), f"{item_label}.sha256", errors)
        if path is not None and digest is not None:
            entries.append((path, digest))
            refs.append((path, digest, item_label))
    paths = [path for path, _ in entries]
    if len(paths) != len(set(paths)):
        errors.append(f"{label} contains a duplicate path")
    return entries


def _tree_digest(entries: list[tuple[str, str]]) -> str:
    """Return schema-v1 digest of sorted path/NUL/digest/LF records."""
    payload = b"".join(
        path.encode("utf-8") + b"\0" + digest.encode("ascii") + b"\n"
        for path, digest in sorted(entries)
    )
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _check_result(value: dict[str, Any], label: str, errors: list[str]) -> str | None:
    return _enum(value.get("result"), CHECK_RESULTS, f"{label}.result", errors)


def validate_manifest_data(data: dict[str, Any]) -> tuple[list[str], list[tuple[str, str, str]]]:
    """Return structural errors and repository-relative artifact references."""
    errors: list[str] = []
    refs: list[tuple[str, str, str]] = []
    top_keys = {
        "schema_version",
        "manifest_id",
        "run_id",
        "obligation_id",
        "created",
        "updated",
        "source_snapshot",
        "spine_target",
        "problem_contract",
        "natural_statement",
        "formal_target",
        "toolchain",
        "trusted_challenge",
        "untrusted_submission",
        "checks",
        "statement_match",
        "final_record",
    }
    _exact_keys(data, top_keys, "manifest", errors)
    if data.get("schema_version") != 1:
        errors.append("schema_version must equal 1")

    manifest_id = data.get("manifest_id")
    if not isinstance(manifest_id, str) or MANIFEST_ID.fullmatch(manifest_id) is None:
        errors.append("manifest_id must match Formalization-NNN")
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or RUN_ID.fullmatch(run_id) is None:
        errors.append("run_id must match Run-YYYYMMDD-NNN")
    obligation_id = data.get("obligation_id")
    if not isinstance(obligation_id, str) or OBLIGATION_ID.fullmatch(obligation_id) is None:
        errors.append("obligation_id must match Obligation-NNN or Obl-NNN")
    created = _iso_date(data.get("created"), "created", errors)
    updated = _iso_date(data.get("updated"), "updated", errors)
    if created and updated and updated < created:
        errors.append("updated must not precede created")

    snapshot = _object(data.get("source_snapshot"), "source_snapshot", errors)
    _exact_keys(snapshot, {"repository_commit", "working_tree"}, "source_snapshot", errors)
    commit = snapshot.get("repository_commit")
    if commit is not None and (not isinstance(commit, str) or FULL_COMMIT.fullmatch(commit) is None):
        errors.append("source_snapshot.repository_commit must be null or a full 40/64-character lowercase commit hash")
    working_tree = _enum(
        snapshot.get("working_tree"),
        {"clean", "dirty", "not-a-git-repository"},
        "source_snapshot.working_tree",
        errors,
    )

    spine = _object(data.get("spine_target"), "spine_target", errors)
    _exact_keys(spine, {"id", "project_readme"}, "spine_target", errors)
    spine_id = spine.get("id")
    if spine_id != "not-applicable" and (
        not isinstance(spine_id, str) or SPINE_ID.fullmatch(spine_id) is None
    ):
        errors.append("spine_target.id must be a stable research ID or not-applicable")
    _artifact_path(spine.get("project_readme"), "spine_target.project_readme", errors)

    problem = _object(data.get("problem_contract"), "problem_contract", errors)
    _exact_keys(
        problem,
        {"version", "artifact", "artifact_sha256", "exact_target_sha256"},
        "problem_contract",
        errors,
    )
    _text(problem.get("version"), "problem_contract.version", errors)
    problem_path = _artifact_path(problem.get("artifact"), "problem_contract.artifact", errors)
    problem_hash = _digest(problem.get("artifact_sha256"), "problem_contract.artifact_sha256", errors)
    exact_target_hash = _digest(
        problem.get("exact_target_sha256"),
        "problem_contract.exact_target_sha256",
        errors,
    )
    if problem_path and problem_hash:
        refs.append((problem_path, problem_hash, "problem_contract"))

    natural = _object(data.get("natural_statement"), "natural_statement", errors)
    _exact_keys(natural, {"artifact", "sha256"}, "natural_statement", errors)
    natural_path = _artifact_path(natural.get("artifact"), "natural_statement.artifact", errors)
    natural_hash = _digest(natural.get("sha256"), "natural_statement.sha256", errors)
    if natural_path and natural_hash:
        refs.append((natural_path, natural_hash, "natural_statement"))
    if exact_target_hash and natural_hash and exact_target_hash != natural_hash:
        errors.append(
            "problem_contract.exact_target_sha256 must match natural_statement.sha256"
        )

    formal = _object(data.get("formal_target"), "formal_target", errors)
    _exact_keys(
        formal,
        {"language", "declaration", "expected_type_artifact", "expected_type_sha256"},
        "formal_target",
        errors,
    )
    language = _text(formal.get("language"), "formal_target.language", errors)
    if language and language != "Lean 4":
        errors.append("formal_target.language must be Lean 4")
    _text(formal.get("declaration"), "formal_target.declaration", errors)
    expected_path = _artifact_path(
        formal.get("expected_type_artifact"), "formal_target.expected_type_artifact", errors
    )
    expected_hash = _digest(
        formal.get("expected_type_sha256"), "formal_target.expected_type_sha256", errors
    )
    if expected_path and expected_hash:
        refs.append((expected_path, expected_hash, "formal_target.expected_type"))

    toolchain = _object(data.get("toolchain"), "toolchain", errors)
    _exact_keys(
        toolchain,
        {"lean_version", "lake_version", "dependency_lock_artifact", "dependency_lock_sha256"},
        "toolchain",
        errors,
    )
    _text(toolchain.get("lean_version"), "toolchain.lean_version", errors)
    _text(toolchain.get("lake_version"), "toolchain.lake_version", errors)
    lock_path = _artifact_path(
        toolchain.get("dependency_lock_artifact"), "toolchain.dependency_lock_artifact", errors
    )
    lock_hash = _digest(
        toolchain.get("dependency_lock_sha256"), "toolchain.dependency_lock_sha256", errors
    )
    if lock_path and lock_hash:
        refs.append((lock_path, lock_hash, "toolchain.dependency_lock"))

    challenge = _object(data.get("trusted_challenge"), "trusted_challenge", errors)
    _exact_keys(
        challenge,
        {
            "root",
            "tree_digest_algorithm",
            "baseline_tree_sha256",
            "after_tree_sha256",
            "files",
            "allowed_axioms",
        },
        "trusted_challenge",
        errors,
    )
    challenge_root = _artifact_path(challenge.get("root"), "trusted_challenge.root", errors)
    if challenge.get("tree_digest_algorithm") != "sha256-v1":
        errors.append("trusted_challenge.tree_digest_algorithm must equal sha256-v1")
    baseline_hash = _digest(
        challenge.get("baseline_tree_sha256"), "trusted_challenge.baseline_tree_sha256", errors
    )
    after_hash = _digest(
        challenge.get("after_tree_sha256"), "trusted_challenge.after_tree_sha256", errors
    )
    challenge_entries = _file_refs(
        challenge.get("files"), "trusted_challenge.files", errors, refs
    )
    challenge_paths = [path for path, _ in challenge_entries]
    if baseline_hash is not None and challenge_entries:
        computed_tree_hash = _tree_digest(challenge_entries)
        if baseline_hash != computed_tree_hash:
            errors.append(
                "trusted_challenge.baseline_tree_sha256 does not match the sha256-v1 digest of its listed files"
            )
    allowed_axioms = challenge.get("allowed_axioms")
    if not isinstance(allowed_axioms, list) or any(
        not isinstance(item, str) or not item.strip() for item in (allowed_axioms or [])
    ):
        errors.append("trusted_challenge.allowed_axioms must be a list of nonempty strings")
        allowed_axioms = []
    if len(allowed_axioms) != len(set(allowed_axioms)):
        errors.append("trusted_challenge.allowed_axioms contains a duplicate")
    if challenge_root:
        for path in challenge_paths:
            if not _path_is_within(path, challenge_root):
                errors.append(f"trusted challenge file {path!r} is outside trusted_challenge.root")

    submission = _object(data.get("untrusted_submission"), "untrusted_submission", errors)
    _exact_keys(
        submission,
        {"root", "files", "produced_by_branch", "solver_write_scope"},
        "untrusted_submission",
        errors,
    )
    submission_root = _artifact_path(submission.get("root"), "untrusted_submission.root", errors)
    submission_entries = _file_refs(
        submission.get("files"), "untrusted_submission.files", errors, refs
    )
    submission_paths = [path for path, _ in submission_entries]
    produced_by = submission.get("produced_by_branch")
    if not isinstance(produced_by, str) or BRANCH_ID.fullmatch(produced_by) is None:
        errors.append("untrusted_submission.produced_by_branch must match Branch-NNN")
    if submission.get("solver_write_scope") != "solution-only":
        errors.append("untrusted_submission.solver_write_scope must equal solution-only")
    if submission_root:
        for path in submission_paths:
            if not _path_is_within(path, submission_root):
                errors.append(f"untrusted submission file {path!r} is outside untrusted_submission.root")
    if challenge_root and submission_root and _roots_overlap(challenge_root, submission_root):
        errors.append("trusted challenge and untrusted submission roots must not overlap")
    overlap = sorted(set(challenge_paths) & set(submission_paths))
    if overlap:
        errors.append(f"trusted challenge and untrusted submission files overlap: {', '.join(overlap)}")

    checks = _object(data.get("checks"), "checks", errors)
    check_names = {
        "challenge_integrity",
        "source_policy",
        "build",
        "declaration_type",
        "axioms",
        "primary_kernel",
        "secondary_recheck",
    }
    _exact_keys(checks, check_names, "checks", errors)

    integrity = _object(checks.get("challenge_integrity"), "checks.challenge_integrity", errors)
    _exact_keys(integrity, {"result"}, "checks.challenge_integrity", errors)
    integrity_result = _check_result(integrity, "checks.challenge_integrity", errors)

    source_policy = _object(checks.get("source_policy"), "checks.source_policy", errors)
    _exact_keys(source_policy, {"result", "artifact", "sha256"}, "checks.source_policy", errors)
    source_result = _check_result(source_policy, "checks.source_policy", errors)
    source_path, source_hash = _artifact_ref(
        {"artifact": source_policy.get("artifact"), "sha256": source_policy.get("sha256")},
        "checks.source_policy",
        errors,
        refs,
        nullable=source_result == "not-run",
    )

    build = _object(checks.get("build"), "checks.build", errors)
    _exact_keys(build, {"argv", "result", "exit_code", "log_artifact", "log_sha256"}, "checks.build", errors)
    build_result = _check_result(build, "checks.build", errors)
    argv = build.get("argv")
    if not isinstance(argv, list) or any(not isinstance(item, str) or not item for item in argv):
        errors.append("checks.build.argv must be a list of nonempty strings")
    if build_result != "not-run" and not argv:
        errors.append("checks.build.argv must be nonempty after a build attempt")
    exit_code = build.get("exit_code")
    if build_result == "not-run" and exit_code is not None:
        errors.append("checks.build.exit_code must be null when result is not-run")
    if build_result in {"pass", "fail"} and not isinstance(exit_code, int):
        errors.append("checks.build.exit_code must be an integer after a build attempt")
    if build_result == "pass" and exit_code != 0:
        errors.append("a passing build must have exit_code 0")
    build_path = _artifact_path(
        build.get("log_artifact"), "checks.build.log_artifact", errors, nullable=build_result == "not-run"
    )
    build_hash = _digest(
        build.get("log_sha256"), "checks.build.log_sha256", errors, nullable=build_result == "not-run"
    )
    if (build_path is None) != (build_hash is None):
        errors.append("checks.build must provide log_artifact and log_sha256 together")
    if build_path and build_hash:
        refs.append((build_path, build_hash, "checks.build"))

    declaration = _object(checks.get("declaration_type"), "checks.declaration_type", errors)
    _exact_keys(
        declaration,
        {"comparator", "comparator_version", "result", "artifact", "sha256"},
        "checks.declaration_type",
        errors,
    )
    declaration_result = _check_result(declaration, "checks.declaration_type", errors)
    if declaration_result != "not-run":
        _text(declaration.get("comparator"), "checks.declaration_type.comparator", errors)
        _text(declaration.get("comparator_version"), "checks.declaration_type.comparator_version", errors)
    declaration_path, declaration_hash = _artifact_ref(
        {"artifact": declaration.get("artifact"), "sha256": declaration.get("sha256")},
        "checks.declaration_type",
        errors,
        refs,
        nullable=declaration_result == "not-run",
    )

    axioms = _object(checks.get("axioms"), "checks.axioms", errors)
    _exact_keys(axioms, {"observed", "result", "artifact", "sha256"}, "checks.axioms", errors)
    axiom_result = _check_result(axioms, "checks.axioms", errors)
    observed_axioms = axioms.get("observed")
    if not isinstance(observed_axioms, list) or any(
        not isinstance(item, str) or not item.strip() for item in (observed_axioms or [])
    ):
        errors.append("checks.axioms.observed must be a list of nonempty strings")
        observed_axioms = []
    if len(observed_axioms) != len(set(observed_axioms)):
        errors.append("checks.axioms.observed contains a duplicate")
    unexpected_axioms = sorted(set(observed_axioms) - set(allowed_axioms))
    if unexpected_axioms:
        errors.append(f"observed axiom(s) are outside the allowlist: {', '.join(unexpected_axioms)}")
    axiom_path, axiom_hash = _artifact_ref(
        {"artifact": axioms.get("artifact"), "sha256": axioms.get("sha256")},
        "checks.axioms",
        errors,
        refs,
        nullable=axiom_result == "not-run",
    )

    primary = _object(checks.get("primary_kernel"), "checks.primary_kernel", errors)
    _exact_keys(primary, {"version", "result", "log_artifact", "log_sha256"}, "checks.primary_kernel", errors)
    primary_result = _check_result(primary, "checks.primary_kernel", errors)
    if primary_result != "not-run":
        _text(primary.get("version"), "checks.primary_kernel.version", errors)
    primary_path = _artifact_path(
        primary.get("log_artifact"),
        "checks.primary_kernel.log_artifact",
        errors,
        nullable=primary_result == "not-run",
    )
    primary_hash = _digest(
        primary.get("log_sha256"),
        "checks.primary_kernel.log_sha256",
        errors,
        nullable=primary_result == "not-run",
    )
    if (primary_path is None) != (primary_hash is None):
        errors.append("checks.primary_kernel must provide log_artifact and log_sha256 together")
    if primary_path and primary_hash:
        refs.append((primary_path, primary_hash, "checks.primary_kernel"))

    secondary = _object(checks.get("secondary_recheck"), "checks.secondary_recheck", errors)
    _exact_keys(
        secondary,
        {"relation", "checker", "version", "result", "log_artifact", "log_sha256"},
        "checks.secondary_recheck",
        errors,
    )
    relation = _enum(
        secondary.get("relation"),
        {"not-run", "same-kernel-clean-rebuild", "independent-checker"},
        "checks.secondary_recheck.relation",
        errors,
    )
    secondary_result = _check_result(secondary, "checks.secondary_recheck", errors)
    if relation == "not-run":
        if secondary_result != "not-run" or any(
            secondary.get(key) is not None
            for key in ("checker", "version", "log_artifact", "log_sha256")
        ):
            errors.append("a not-run secondary recheck must leave result not-run and detail fields null")
    elif relation is not None:
        _text(secondary.get("checker"), "checks.secondary_recheck.checker", errors)
        _text(secondary.get("version"), "checks.secondary_recheck.version", errors)
        secondary_path = _artifact_path(
            secondary.get("log_artifact"), "checks.secondary_recheck.log_artifact", errors
        )
        secondary_hash = _digest(
            secondary.get("log_sha256"), "checks.secondary_recheck.log_sha256", errors
        )
        if secondary_result == "not-run":
            errors.append("a selected secondary recheck must record pass or fail")
        if secondary_path and secondary_hash:
            refs.append((secondary_path, secondary_hash, "checks.secondary_recheck"))

    statement = _object(data.get("statement_match"), "statement_match", errors)
    _exact_keys(
        statement,
        {"status", "exact_scope", "confirmed_by", "date", "evidence_artifact", "evidence_sha256"},
        "statement_match",
        errors,
    )
    statement_status = _enum(
        statement.get("status"),
        {"not-confirmed", "confirmed", "mismatch-found"},
        "statement_match.status",
        errors,
    )
    if statement_status == "not-confirmed":
        if any(
            statement.get(key) is not None
            for key in ("exact_scope", "confirmed_by", "date", "evidence_artifact", "evidence_sha256")
        ):
            errors.append("an unconfirmed statement match must leave detail fields null")
    else:
        _text(statement.get("exact_scope"), "statement_match.exact_scope", errors)
        if statement_status == "confirmed":
            _text(statement.get("confirmed_by"), "statement_match.confirmed_by", errors)
            _iso_date(statement.get("date"), "statement_match.date", errors)
        elif statement.get("confirmed_by") is not None or statement.get("date") is not None:
            errors.append("mismatch-found must not be recorded as a human confirmation")
        match_path = _artifact_path(
            statement.get("evidence_artifact"), "statement_match.evidence_artifact", errors
        )
        match_hash = _digest(statement.get("evidence_sha256"), "statement_match.evidence_sha256", errors)
        if match_path and match_hash:
            refs.append((match_path, match_hash, "statement_match"))

    final = _object(data.get("final_record"), "final_record", errors)
    _exact_keys(
        final,
        {"trust_boundary", "formal_encoding", "statement_correspondence"},
        "final_record",
        errors,
    )
    trust_status = _enum(
        final.get("trust_boundary"), {"unchecked", "intact", "violated"}, "final_record.trust_boundary", errors
    )
    formal_status = _enum(
        final.get("formal_encoding"),
        {"unchecked", "recorded-pass", "recorded-fail", "conflict"},
        "final_record.formal_encoding",
        errors,
    )
    correspondence = _enum(
        final.get("statement_correspondence"),
        {"not-confirmed", "confirmed", "mismatch-found"},
        "final_record.statement_correspondence",
        errors,
    )
    if correspondence and statement_status and correspondence != statement_status:
        errors.append("final_record.statement_correspondence must match statement_match.status")
    if trust_status == "intact" and (
        integrity_result != "pass" or baseline_hash is None or baseline_hash != after_hash
    ):
        errors.append("an intact trust boundary requires a passing integrity check and equal before/after challenge hashes")
    if trust_status == "violated" and integrity_result != "fail":
        errors.append("a violated trust boundary requires a failed challenge integrity check")
    required_passes = {
        "challenge_integrity": integrity_result,
        "source_policy": source_result,
        "build": build_result,
        "declaration_type": declaration_result,
        "axioms": axiom_result,
        "primary_kernel": primary_result,
    }
    mandatory_failure = "fail" in required_passes.values()
    same_kernel_failure = (
        relation == "same-kernel-clean-rebuild" and secondary_result == "fail"
    )
    independent_conflict = relation == "independent-checker" and {
        primary_result,
        secondary_result,
    } == {"pass", "fail"}
    if formal_status == "recorded-pass":
        failed_requirements = sorted(name for name, result in required_passes.items() if result != "pass")
        if failed_requirements:
            errors.append(
                "formal_encoding recorded-pass requires pass for: " + ", ".join(failed_requirements)
            )
        if trust_status != "intact":
            errors.append("formal_encoding recorded-pass requires an intact trust boundary")
        if commit is None or working_tree != "clean":
            errors.append("formal_encoding recorded-pass requires a clean source snapshot and full repository commit")
        if build_path is None or source_path is None or declaration_path is None or axiom_path is None or primary_path is None:
            errors.append("formal_encoding recorded-pass requires durable artifacts for every mandatory check")
        if secondary_result == "fail":
            errors.append("formal_encoding recorded-pass is forbidden after a failed secondary recheck")
    if formal_status == "recorded-fail" and not (
        mandatory_failure or same_kernel_failure
    ):
        errors.append(
            "formal_encoding recorded-fail requires a failed mandatory check or same-kernel clean rebuild"
        )
    if independent_conflict and formal_status != "conflict":
        errors.append(
            "opposite primary-kernel and independent-checker results require formal_encoding conflict"
        )
    if formal_status == "conflict" and not independent_conflict:
        errors.append(
            "formal_encoding conflict requires opposite primary-kernel and independent-checker results"
        )
    if (
        (mandatory_failure or same_kernel_failure)
        and not independent_conflict
        and formal_status not in {"recorded-fail"}
    ):
        errors.append(
            "a recorded mandatory or same-kernel failure requires formal_encoding recorded-fail"
        )

    return errors, refs


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def verify_artifacts(
    root: Path, refs: list[tuple[str, str, str]]
) -> list[str]:
    """Verify recorded artifact hashes without following links outside root."""
    errors: list[str] = []
    try:
        root = root.resolve(strict=True)
    except OSError as exc:
        return [f"artifact root could not be resolved: {exc}"]
    for relative, expected, label in refs:
        candidate = root.joinpath(*PurePosixPath(relative).parts)
        cursor = root
        linked = False
        for part in PurePosixPath(relative).parts:
            cursor = cursor / part
            if cursor.is_symlink():
                linked = True
                break
        if linked:
            errors.append(f"{label} points through a symbolic link: {relative}")
            continue
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError):
            errors.append(f"{label} artifact is missing or leaves the repository: {relative}")
            continue
        if not resolved.is_file():
            errors.append(f"{label} artifact is not a regular file: {relative}")
            continue
        actual = _sha256_file(resolved)
        if actual != expected:
            errors.append(f"{label} artifact hash mismatch: {relative}")
    return errors


def verify_trusted_challenge_tree(
    root: Path,
    challenge_root: str,
    entries: list[tuple[str, str]],
) -> list[str]:
    """Require ``files`` to exhaustively list regular files below trusted root.

    Traversal uses ``lstat`` and rejects every symbolic link rather than
    following it.  Special filesystem entries are rejected as well because
    they cannot be represented by the manifest's regular-file hash records.
    """
    errors: list[str] = []
    relative_root = PurePosixPath(challenge_root)
    challenge_dir = root.joinpath(*relative_root.parts)

    cursor = root
    for part in relative_root.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return [
                "trusted_challenge.root points through a symbolic link: "
                + challenge_root
            ]

    try:
        root_mode = challenge_dir.lstat().st_mode
    except OSError as exc:
        return [f"trusted_challenge.root is missing or unreadable: {challenge_root}: {exc}"]
    if stat.S_ISLNK(root_mode):
        return [f"trusted_challenge.root is a symbolic link: {challenge_root}"]
    if not stat.S_ISDIR(root_mode):
        return [f"trusted_challenge.root is not a directory: {challenge_root}"]

    actual_files: set[str] = set()
    pending = [challenge_dir]
    while pending:
        directory = pending.pop()
        try:
            children = sorted(directory.iterdir(), key=lambda path: path.name)
        except OSError as exc:
            relative = directory.relative_to(root).as_posix()
            errors.append(f"trusted challenge directory is unreadable: {relative}: {exc}")
            continue
        for child in children:
            relative = child.relative_to(root).as_posix()
            try:
                mode = child.lstat().st_mode
            except OSError as exc:
                errors.append(f"trusted challenge entry is unreadable: {relative}: {exc}")
                continue
            if stat.S_ISLNK(mode):
                errors.append(f"trusted challenge contains a symbolic link: {relative}")
            elif stat.S_ISDIR(mode):
                pending.append(child)
            elif stat.S_ISREG(mode):
                actual_files.add(relative)
            else:
                errors.append(f"trusted challenge contains a non-regular entry: {relative}")

    listed_files = {path for path, _ in entries}
    for missing in sorted(listed_files - actual_files):
        errors.append(f"trusted_challenge.files lists a missing regular file: {missing}")
    for omitted in sorted(actual_files - listed_files):
        errors.append(f"trusted_challenge.files omits a trusted-root file: {omitted}")
    return errors


def validate_manifest_path(
    path: Path, *, root: Path | None = None, verify_files: bool = False
) -> list[str]:
    artifact_root = root or Path.cwd()
    try:
        absolute_root = (
            artifact_root if artifact_root.is_absolute() else Path.cwd() / artifact_root
        )
        resolved_root = absolute_root.resolve(strict=True)
        absolute_path = path if path.is_absolute() else Path.cwd() / path
        relative_manifest = absolute_path.relative_to(absolute_root)
    except (OSError, ValueError) as exc:
        return [f"manifest path must stay inside the artifact root: {exc}"]
    if ".." in relative_manifest.parts or "." in relative_manifest.parts:
        return ["manifest path must not contain '.' or '..'"]
    cursor = resolved_root
    for part in relative_manifest.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return ["manifest path must not contain a symbolic link"]
    try:
        resolved_path = absolute_path.resolve(strict=False)
        resolved_path.relative_to(resolved_root)
    except (OSError, ValueError) as exc:
        return [f"manifest path must stay inside the artifact root: {exc}"]
    data, errors = _read_json(resolved_path)
    if data is None:
        return errors
    structural, refs = validate_manifest_data(data)
    errors.extend(structural)
    if verify_files and not structural:
        errors.extend(verify_artifacts(resolved_root, refs))
        challenge = data["trusted_challenge"]
        challenge_entries = [
            (item["path"], item["sha256"])
            for item in challenge["files"]
        ]
        errors.extend(
            verify_trusted_challenge_tree(
                resolved_root,
                challenge["root"],
                challenge_entries,
            )
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a recorded Lean evidence manifest without executing or attesting "
            "Lean, Lake, Git, or checker commands."
        )
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--verify-files",
        action="store_true",
        help=(
            "verify artifact hashes and require trusted_challenge.files to exhaustively "
            "list its root; this still does not execute or attest recorded commands"
        ),
    )
    args = parser.parse_args(argv)
    errors = validate_manifest_path(
        args.manifest, root=args.root, verify_files=args.verify_files
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Formalization manifest validation failed with {len(errors)} error(s).")
        return 1
    print("Formalization manifest validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
