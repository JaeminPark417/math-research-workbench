#!/usr/bin/env python3
"""Validate the public distribution without third-party dependencies."""

from __future__ import annotations

import hashlib
import json
import os
import re
import runpy
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    ".agents/skills/first-run/SKILL.md",
    ".agents/skills/first-run/references/setup.md",
    ".agents/skills/first-run/agents/openai.yaml",
    ".agents/skills/first-run/references/github.md",
    ".agents/skills/first-run/references/claude-code.md",
    ".agents/skills/first-run/references/chatgpt-browser.md",
    ".agents/skills/first-run/references/storage.md",
    ".agents/skills/first-run/references/obsidian.md",
    ".agents/skills/first-run/references/obsidian-plugins.md",
    ".agents/skills/first-run/references/tex.md",
    ".agents/skills/claude-review/SKILL.md",
    ".agents/skills/claude-review/references/execution.md",
    ".agents/skills/claude-review/agents/openai.yaml",
    ".agents/skills/math-research-run/SKILL.md",
    ".agents/skills/math-research-run/agents/openai.yaml",
    ".agents/skills/pro-context-bundle/SKILL.md",
    ".agents/skills/pro-context-bundle/agents/openai.yaml",
    ".agents/skills/pro-context-bundle/scripts/build_pro_bundle.py",
    ".github/workflows/validate.yml",
    ".gitattributes",
    ".gitignore",
    ".harness/config.example.yaml",
    ".harness/README.md",
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
    "files/README.md",
    "ideas/README.md",
    "inbox/README.md",
    "inbox/archive/.gitkeep",
    "meta/conventions.md",
    "meta/math-workflow.md",
    "meta/math-details.md",
    "meta/templates/research-run-extensions.md",
    "meta/safety.md",
    "meta/schemas.md",
    "meta/templates/article.tex",
    "meta/templates/idea.md",
    "meta/templates/inbox.md",
    "meta/templates/paper.md",
    "meta/templates/project.md",
    "meta/templates/proof-audit.md",
    "meta/templates/formalization-manifest.json",
    "meta/templates/research-run.md",
    "meta/templates/research-branch-prompt.md",
    "meta/templates/research-log.md",
    "meta/templates/session.md",
    "notes/README.md",
    "optional/obsidian-plugins/mrw-latex-delimiter-compat/LICENSE",
    "optional/obsidian-plugins/mrw-latex-delimiter-compat/README.md",
    "optional/obsidian-plugins/mrw-latex-delimiter-compat/main.js",
    "optional/obsidian-plugins/mrw-latex-delimiter-compat/manifest.json",
    "papers/README.md",
    "projects/README.md",
    "scripts/compile-tex.ps1",
    "scripts/compile-tex.sh",
    "scripts/claude-readiness.py",
    "scripts/review-output.py",
    "scripts/tests/test_review_output.py",
    "scripts/doctor.ps1",
    "scripts/doctor.sh",
    "scripts/formalization_manifest.py",
    "scripts/math_run_checks.py",
    "scripts/math_target.py",
    "scripts/tests/test_math_target.py",
    "meta/math-research-contract.md",
    "meta/research-tickets/tests/test_research_journey.py",
    "scripts/install-bundled-obsidian-plugin.py",
    "scripts/migrate-setup-v1.py",
    "scripts/remote-state.py",
    "scripts/setup-state.py",
    "scripts/tests/mrw-latex-delimiter-compat.test.js",
    "scripts/validate-release.py",
    "scripts/vault-lint.py",
}
REQUIRED |= {
    'meta/research-tickets/tests/ticket_test_support.py',
    'meta/research-tickets/tests/test_workbench_integration.py',
    '.agents/skills/research-issues/SKILL.md',
    '.agents/skills/research-issues/agents/openai.yaml',
    'docs/research-issues.ko.md',
    'docs/research-issues.md',
    'meta/research-ticket-workflow.md',
    'meta/research-tickets/EXPERIMENTAL-WORKFLOW.md',
    'meta/research-tickets/PAPER-WORKFLOW.md',
    'meta/research-tickets/TESTING.md',
    'meta/research-tickets/WRITE-API.md',
    'meta/research-tickets/examples/experimental-cycle.py',
    'meta/research-tickets/examples/paper-review.py',
    'meta/research-tickets/scripts/issue_index.py',
    'meta/research-tickets/scripts/issue_sources.py',
    'meta/research-tickets/scripts/issue_store.py',
    'meta/research-tickets/scripts/issue_transaction.py',
    'meta/research-tickets/scripts/issues.py',
    'meta/research-tickets/scripts/ticket_fs.py',
    'meta/research-tickets/scripts/ticket_project.py',
    'meta/research-tickets/tests/fixtures/issues/res-10.md',
    'meta/research-tickets/tests/fixtures/issues/res-11.md',
    'meta/research-tickets/tests/fixtures/issues/res-12.md',
    'meta/research-tickets/tests/fixtures/issues/res-13.md',
    'meta/research-tickets/tests/fixtures/issues/res-14.md',
    'meta/research-tickets/tests/fixtures/issues/res-15.md',
    'meta/research-tickets/tests/fixtures/issues/res-16.md',
    'meta/research-tickets/tests/fixtures/issues/res-17.md',
    'meta/research-tickets/tests/fixtures/issues/res-5.md',
    'meta/research-tickets/tests/fixtures/issues/res-6.md',
    'meta/research-tickets/tests/fixtures/issues/res-7.md',
    'meta/research-tickets/tests/fixtures/issues/res-8.md',
    'meta/research-tickets/tests/fixtures/issues/res-9.md',
    'meta/research-tickets/tests/fixtures/project.json',
    'meta/research-tickets/tests/fixtures/relations.json',
    'meta/research-tickets/tests/test_experimental_workflow.py',
    'meta/research-tickets/tests/test_issue_index.py',
    'meta/research-tickets/tests/test_issue_sources.py',
    'meta/research-tickets/tests/test_issue_store.py',
    'meta/research-tickets/tests/test_paper_workflow.py',
    'meta/research-tickets/tests/test_ticket_harness.py',
    'scripts/research-tickets.py',
}
RELEASE_ALLOWLIST = REQUIRED | {
    ".github/ISSUE_TEMPLATE/bug.yml",
    ".github/ISSUE_TEMPLATE/feature.yml",
}
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
SECRET_PATTERNS = {
    "private key block": re.compile(
        r"-----BEGIN [A-Z0-9 -]*PRIVATE KEY(?: BLOCK)?-----"
    ),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "GitHub fine-grained token": re.compile(
        r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"
    ),
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "Google API key": re.compile(r"\bAIza[A-Za-z0-9_-]{30,}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "assigned secret": re.compile(
        r"(?i)(?<![A-Za-z0-9_-])(?P<key_quote>['\"`]?)"
        r"(?:[a-z0-9]+[_-])*"
        r"(?:api[_-]?key|access[_-]?(?:key|token)|authorization[_-]?code|cookie|"
        r"client[_-]?secret|mfa[_-]?code|oauth[_-]?token|passphrase|password|"
        r"private[_-]?key|recovery[_-]?code|secret[_-]?access[_-]?key|secret|token)"
        r"(?P=key_quote)\s*[:=]\s*"
        r"(?!\s*['\"`]?(?:example|placeholder|changeme|none|null)['\"`]?"
        r"(?=\s|$|[,}\]#]))"
        r"(?:['\"`][^'\"`\r\n]{8,}['\"`]|[^\s#'\"`]{8,})"
    ),
    "credential-bearing URL": re.compile(
        r"(?i)https?://(?:[^/\s:@]+:[^/\s@]+@|[^\s]*[?&#]"
        r"(?:access[_-]?token|api[_-]?key|auth|key|token)=[^&#\s]+)"
    ),
}
PERSONAL_PATHS = {
    "macOS personal path": re.compile(
        r"(?i)/users/(?!username(?:/|\b)|example(?:/|\b))[A-Za-z0-9._-]+"
        r"(?=/|\s|$|[)'\"`.,:;])"
    ),
    "Windows personal path": re.compile(
        r"(?i)\b[A-Z]:\\Users\\(?!username(?:\\|\b)|example(?:\\|\b))"
        r"[^\\\s'\"`]+(?=\\|\s|$|[)'\"`.,:;])"
    ),
    "Linux personal path": re.compile(
        r"(?i)/home/(?!username(?:/|\b)|example(?:/|\b))[A-Za-z0-9._-]+"
        r"(?=/|\s|$|[)'\"`.,:;])"
    ),
    "personal email address": re.compile(
        r"(?i)\b(?!git@github\.com\b)[A-Z0-9._%+-]+@"
        r"(?!example\.(?:com|org|net)\b)[A-Z0-9.-]+\.[A-Z]{2,}\b"
    ),
}
FORBIDDEN_SETUP_DETAIL_KEYS = {
    "account",
    "account_id",
    "account_name",
    "access_token",
    "api_key",
    "authenticated",
    "authentication",
    "auth_status",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "email",
    "email_address",
    "is_authenticated",
    "logged_in",
    "login_status",
    "org",
    "organization",
    "organization_id",
    "oauth_code",
    "password",
    "passphrase",
    "plan",
    "private_key",
    "recovery_code",
    "secret",
    "signed_in",
    "subscription",
    "tenant",
    "token",
    "user",
    "user_id",
    "username",
    "workspace",
    "workspace_id",
}


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


def public_files() -> list[Path]:
    files: list[Path] = []
    pending = [ROOT]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                relative = path.relative_to(ROOT)
                # Skip the canonical repository's root metadata while still
                # traversing and rejecting a nested .git tree in an artifact.
                if relative.parts and relative.parts[0] == ".git":
                    continue
                relative_text = relative.as_posix()
                if (
                    relative_text in {".claude", ".codex", ".obsidian/plugins"}
                    or relative.parent.as_posix() == ".harness"
                    and relative.name.startswith("local")
                ):
                    # Private or machine-local content is checked for presence
                    # below but never traversed or read.
                    continue
                if is_link_like(path):
                    files.append(path)
                elif entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                elif entry.is_file(follow_symlinks=False):
                    files.append(path)
    return sorted(files)


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def has_safe_auth_redirection(line: str) -> bool:
    """Return true only when both Claude status streams are discarded."""
    if re.search(r"\*>\s*\$null\b", line, re.IGNORECASE):
        return True
    if re.search(r"&>\s*/dev/null\b", line):
        return True
    stdout_null = re.search(r"(?:^|\s)(?:1?>)\s*/dev/null\b", line)
    stderr_null = re.search(r"(?:^|\s)2>\s*/dev/null\b", line)
    stderr_to_stdout = re.search(r"(?:^|\s)2>&1(?:\s|$|[`);|])", line)
    if stdout_null and stderr_null:
        return True
    return bool(
        stdout_null
        and stderr_to_stdout
        and stdout_null.start() < stderr_to_stdout.start()
    )


def command_clause(line: str, command_start: int) -> tuple[str, int]:
    """Return only the sentence/shell clause containing the command."""
    start = 0
    end = len(line)
    for boundary in re.finditer(r";|&&|\|\||[.!?](?=\s|$)", line):
        if boundary.end() <= command_start:
            start = boundary.end()
        elif boundary.start() > command_start:
            end = boundary.start()
            break
    return line[start:end], command_start - start


def is_negative_command_mention(line: str, command_match: re.Match[str]) -> bool:
    clause, local_start = command_clause(line, command_match.start())
    before = clause[:local_start].casefold()
    after = clause[local_start + len(command_match.group(0)) :].casefold()
    negative_before = re.search(
        r"\b(?:never|do\s+not|don['’]t|must\s+not)\b",
        before,
    )
    positive_transition = re.search(
        r"\b(?:and|but|then|instead)\s+(?:first\s+)?"
        r"(?:run|use|execute|display|print)\b[^.!?;]*$",
        before,
    )
    negative_after = re.search(
        r"^\s*[`'\" ]*(?:is\s+prohibited|must\s+not\s+be\s+(?:run|used|executed|printed))",
        after,
    )
    korean_negative = re.search(
        r"^\s*[`'\" ]*(?:을|를)?\s*"
        r"(?:(?:실행|사용|출력|표시)(?:하지|하면\s+안|하지\s+마)|"
        r"(?:실행|사용|출력|표시)?\s*금지|마세요)",
        after,
    )
    return bool(
        (negative_before and not positive_transition)
        or negative_after
        or korean_negative
    )


def is_forbidden_setup_detail_key(key: str) -> bool:
    return (
        key in FORBIDDEN_SETUP_DETAIL_KEYS
        or key.startswith(
            (
                "account_",
                "auth_",
                "credential_",
                "email_",
                "oauth_",
                "password_",
                "recovery_",
                "secret_",
                "user_",
            )
        )
        or key.endswith(("_credential", "_password", "_secret", "_private_key"))
        or key.endswith("_token")
        or key.endswith("_cookie")
    )


def validate_auth_commands(relative: str, text: str, errors: list[str]) -> None:
    """Reject persistent-token setup and status commands that expose output."""
    if relative == "scripts/validate-release.py":
        return
    executable = (
        r"(?<![A-Za-z0-9_.-])(?:&\s*)?"
        r"(?P<quote>['\"]?)claude(?:\.exe)?(?P=quote)"
    )
    setup_token_pattern = re.compile(
        executable + r"\s+setup-token(?![A-Za-z0-9_-])", re.IGNORECASE
    )
    auth_status_pattern = re.compile(
        executable + r"\s+auth\s+status(?![A-Za-z0-9_-])", re.IGNORECASE
    )
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in setup_token_pattern.finditer(line):
            if not is_negative_command_mention(line, match):
                errors.append(
                    f"persistent Claude setup-token command in {relative}:{line_number}"
                )
        for match in auth_status_pattern.finditer(line):
            clause, _ = command_clause(line, match.start())
            if not has_safe_auth_redirection(clause) and not is_negative_command_mention(
                line, match
            ):
                errors.append(
                    f"Claude auth status may expose account details in {relative}:{line_number}"
                )


def complete_setup_state(version: int, include_version_2_choices: bool) -> str:
    version_2_sections = ""
    if include_version_2_choices:
        version_2_sections = textwrap.dedent(
            """\
            claude_code:
              choice: "no"
            chatgpt_browser:
              choice: "later"
            """
        )
    completed_at = (
        'completed_at: "2026-07-19T12:00:00+00:00"\n'
        if version == 2
        else 'completed_at: "2026-07-19"\n'
    )
    return textwrap.dedent(
        f"""\
        setup_version: {version}
        status: complete
        language: "en"
        github:
          choice: "no"
          repository: ""
          visibility: ""
        external_storage:
          choice: "no"
          provider: ""
          root: ""
        obsidian:
          choice: "no"
          installed: null
          plugin_setup: ""
          pending_plugin: ""
          plugin_profile: ""
          community_plugins: []
        tex:
          choice: "no"
          engine: ""
        """
    ) + version_2_sections + completed_at


def blank_version_2_setup_state() -> str:
    return textwrap.dedent(
        """\
        setup_version: 2
        status: in_progress
        language: ""
        github:
          choice: ""
        external_storage:
          choice: ""
        obsidian:
          choice: ""
          plugin_setup: ""
          pending_plugin: ""
        tex:
          choice: ""
        claude_code:
          choice: ""
        chatgpt_browser:
          choice: ""
        """
    )


def execute_setup_state(
    state_text: str | None,
    *,
    state_symlink: bool = False,
) -> tuple[subprocess.CompletedProcess[str] | None, str | None]:
    """Run setup-state.py from an isolated stdlib-only temporary copy."""
    with tempfile.TemporaryDirectory(prefix="workbench-state-") as temp_name:
        fixture_root = Path(temp_name) / "workbench"
        scripts_dir = fixture_root / "scripts"
        harness_dir = fixture_root / ".harness"
        scripts_dir.mkdir(parents=True)
        harness_dir.mkdir()
        shutil.copy2(ROOT / "scripts/setup-state.py", scripts_dir / "setup-state.py")
        state_path = harness_dir / "local.yaml"

        if state_symlink:
            assert state_text is not None
            target_path = fixture_root / "linked-local.yaml"
            target_path.write_text(state_text, encoding="utf-8")
            try:
                os.symlink(target_path, state_path)
            except OSError as symlink_error:
                if os.name != "nt":
                    return None, f"could not create setup-state symlink fixture: {symlink_error}"

                # Windows junctions do not require symlink privileges. The
                # helper treats either reparse-point form as unsafe.
                harness_dir.rmdir()
                target_dir = fixture_root / "linked-harness"
                target_dir.mkdir()
                (target_dir / "local.yaml").write_text(state_text, encoding="utf-8")
                junction = subprocess.run(
                    ["cmd", "/d", "/c", "mklink", "/J", str(harness_dir), str(target_dir)],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if junction.returncode != 0:
                    return None, "could not create setup-state link fixture on Windows"
        elif state_text is not None:
            state_path.write_text(state_text, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(scripts_dir / "setup-state.py")],
            cwd=fixture_root,
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            check=False,
        )
        fixture_path = str(fixture_root)
        if fixture_path in result.stdout or fixture_path in result.stderr:
            return result, "setup-state output exposed its workspace path"
        return result, None


def validate_setup_state_fixtures(errors: list[str]) -> None:
    private_github_v2 = complete_setup_state(2, True).replace(
        'github:\n  choice: "no"\n  repository: ""\n  visibility: ""',
        'github:\n  choice: "yes"\n'
        '  repository: "https://github.com/example/research.git"\n'
        '  visibility: "private"',
    )
    public_github_v1 = complete_setup_state(1, False).replace(
        'github:\n  choice: "no"\n  repository: ""\n  visibility: ""',
        'github:\n  choice: "yes"\n'
        '  repository: "example/legacy-research"\n'
        '  visibility: "PUBLIC"',
    )
    unquoted_plugin_v1 = complete_setup_state(1, False).replace(
        'obsidian:\n  choice: "no"\n  installed: null\n'
        '  plugin_setup: ""\n  pending_plugin: ""\n'
        '  plugin_profile: ""\n  community_plugins: []',
        'obsidian:\n  choice: "yes"\n  installed: true\n'
        '  plugin_setup: "complete"\n  pending_plugin: ""\n'
        '  plugin_profile: "custom"\n  community_plugins:\n'
        '    - latex-suite',
    )
    bundled_plugin_v2 = complete_setup_state(2, True).replace(
        'obsidian:\n  choice: "no"\n  installed: null\n'
        '  plugin_setup: ""\n  pending_plugin: ""\n'
        '  plugin_profile: ""\n  community_plugins: []',
        'obsidian:\n  choice: "yes"\n  installed: true\n'
        '  plugin_setup: "complete"\n  pending_plugin: ""\n'
        '  plugin_profile: "custom"\n  community_plugins:\n'
        '    - "mrw-latex-delimiter-compat"',
    )
    unknown_bundled_plugin_v2 = bundled_plugin_v2.replace(
        '    - "mrw-latex-delimiter-compat"',
        '    - "latex-delimiter-compat"',
    )
    reconfiguring_bundled_plugin_v2 = (
        complete_setup_state(2, True)
        .replace("status: complete", "status: in_progress")
        .replace(
            'obsidian:\n  choice: "no"\n  installed: null\n'
            '  plugin_setup: ""\n  pending_plugin: ""\n'
            '  plugin_profile: ""\n  community_plugins: []',
            'obsidian:\n  choice: "yes"\n  installed: true\n'
            '  plugin_setup: "in_progress"\n'
            '  pending_plugin: "mrw-latex-delimiter-compat"\n'
            '  plugin_profile: "core-only"\n  community_plugins: []',
        )
        .replace('completed_at: "2026-07-19T12:00:00+00:00"', 'completed_at: ""')
    )
    fractional_timestamp_v2 = complete_setup_state(2, True).replace(
        'completed_at: "2026-07-19T12:00:00+00:00"',
        'completed_at: "2026-07-19T12:00:00.5+00:00"',
    )
    completed_with_pending_plugin_v2 = reconfiguring_bundled_plugin_v2.replace(
        "status: in_progress", "status: complete"
    ).replace('completed_at: ""', 'completed_at: "2026-07-19T12:00:00+00:00"')
    fixtures = [
        ("missing local state", None, "missing", 0),
        ("blank in-progress version 2", blank_version_2_setup_state(), "ok", 0),
        (
            "in-progress verified GitHub choice",
            blank_version_2_setup_state().replace(
                'github:\n  choice: ""',
                'github:\n  choice: "yes"\n'
                '  repository: "example/research"\n'
                '  visibility: "private"',
            ),
            "ok",
            0,
        ),
        (
            "in-progress GitHub yes without details",
            blank_version_2_setup_state().replace(
                'github:\n  choice: ""', 'github:\n  choice: "yes"'
            ),
            "inconsistent",
            1,
        ),
        (
            "in-progress storage yes without details",
            blank_version_2_setup_state().replace(
                'external_storage:\n  choice: ""',
                'external_storage:\n  choice: "yes"',
            ),
            "inconsistent",
            1,
        ),
        (
            "in-progress Obsidian yes without details",
            blank_version_2_setup_state().replace(
                'obsidian:\n  choice: ""', 'obsidian:\n  choice: "yes"'
            ),
            "inconsistent",
            1,
        ),
        (
            "in-progress local TeX without engine",
            blank_version_2_setup_state().replace(
                'tex:\n  choice: ""', 'tex:\n  choice: "local"'
            ),
            "inconsistent",
            1,
        ),
        ("valid version 1", complete_setup_state(1, False), "outdated", 0),
        ("valid version 2", complete_setup_state(2, True), "ok", 0),
        ("valid private GitHub URL", private_github_v2, "ok", 0),
        ("valid bundled Obsidian plugin", bundled_plugin_v2, "ok", 0),
        ("unlisted bundled Obsidian plugin ID", unknown_bundled_plugin_v2, "invalid", 1),
        ("resumable bundled plugin reconfiguration", reconfiguring_bundled_plugin_v2, "ok", 0),
        ("completed setup with pending bundled plugin", completed_with_pending_plugin_v2, "inconsistent", 1),
        ("short fractional completed timestamp", fractional_timestamp_v2, "ok", 0),
        (
            "version 2 public GitHub destination",
            private_github_v2.replace('visibility: "private"', 'visibility: "public"'),
            "inconsistent",
            1,
        ),
        (
            "version 2 internal GitHub destination",
            private_github_v2.replace('visibility: "private"', 'visibility: "internal"'),
            "inconsistent",
            1,
        ),
        ("legacy uppercase public visibility", public_github_v1, "outdated", 0),
        ("legacy unquoted plugin ID", unquoted_plugin_v1, "outdated", 0),
        (
            "malformed version 2",
            complete_setup_state(2, True).replace('language: "en"', "language: yes"),
            "invalid",
            1,
        ),
        (
            "unquoted new choice",
            complete_setup_state(2, True).replace(
                'claude_code:\n  choice: "no"', "claude_code:\n  choice: yes"
            ),
            "invalid",
            1,
        ),
        (
            "unknown new choice",
            complete_setup_state(2, True).replace(
                'chatgpt_browser:\n  choice: "later"',
                'chatgpt_browser:\n  choice: "maybe"',
            ),
            "invalid",
            1,
        ),
        ("future version", "setup_version: 3\nstatus: complete\n", "unsupported", 1),
        (
            "incomplete version 2",
            complete_setup_state(2, False),
            "inconsistent",
            1,
        ),
        (
            "invalid version 1",
            complete_setup_state(1, False).replace('language: "en"', 'language: ""'),
            "inconsistent",
            1,
        ),
        (
            "impossible version 2 timestamp",
            complete_setup_state(2, True).replace(
                "2026-07-19T12:00:00+00:00", "2026-99-99T99:99:99+99:99"
            ),
            "inconsistent",
            1,
        ),
        (
            "legacy unvalidated version 1 date",
            complete_setup_state(1, False).replace("2026-07-19", "2026-02-30"),
            "outdated",
            0,
        ),
        (
            "legacy blank version 1 completion time",
            complete_setup_state(1, False).replace(
                'completed_at: "2026-07-19"', 'completed_at: ""'
            ),
            "outdated",
            0,
        ),
        (
            "legacy missing version 1 completion time",
            complete_setup_state(1, False).replace(
                'completed_at: "2026-07-19"\n', ""
            ),
            "outdated",
            0,
        ),
        (
            "invalid GitHub visibility",
            private_github_v2.replace('visibility: "private"', 'visibility: "secret"'),
            "invalid",
            1,
        ),
    ]
    for label, state_text, expected_state, expected_exit in fixtures:
        result, fixture_error = execute_setup_state(state_text)
        if fixture_error:
            errors.append(f"{label} fixture failed: {fixture_error}")
            continue
        assert result is not None
        expected_line = f"setup_state={expected_state}"
        if result.returncode != expected_exit or expected_line not in result.stdout.splitlines():
            errors.append(
                f"{label} fixture expected {expected_line}/exit {expected_exit}"
            )

    redaction_marker = "PRIVATE-ACCOUNT-AND-PATH-MARKER"
    redaction_state = complete_setup_state(2, True).replace(
        '  root: ""', f'  root: "/Users/example/{redaction_marker}"'
    )
    redaction_result, redaction_error = execute_setup_state(redaction_state)
    if redaction_error:
        errors.append(f"redaction fixture failed: {redaction_error}")
    elif redaction_result is not None and (
        redaction_result.returncode != 0
        or "setup_state=ok" not in redaction_result.stdout.splitlines()
        or redaction_marker in redaction_result.stdout
        or redaction_marker in redaction_result.stderr
    ):
        errors.append("setup-state redaction fixture exposed or rejected an allowlisted detail")

    forbidden_marker = "PRIVATE-AUTH-DETAIL-MARKER"
    forbidden_password_key = "pass" + "word"
    forbidden_state = complete_setup_state(2, True).replace(
        'github:\n  choice: "no"',
        'github:\n  choice: "no"\n'
        f'  {forbidden_password_key}: "{forbidden_marker}"',
    )
    forbidden_result, forbidden_error = execute_setup_state(forbidden_state)
    if forbidden_error:
        errors.append(f"forbidden auth detail fixture failed: {forbidden_error}")
    elif forbidden_result is not None and (
        forbidden_result.returncode != 1
        or "setup_state=invalid" not in forbidden_result.stdout.splitlines()
        or forbidden_marker in forbidden_result.stdout
        or forbidden_marker in forbidden_result.stderr
    ):
        errors.append("setup-state forbidden auth detail was accepted or exposed")

    authorization_marker = "PRIVATE-AUTHORIZATION-CODE-MARKER"
    authorization_key = "authorization" + "_code"
    authorization_state = complete_setup_state(2, True).replace(
        'claude_code:\n  choice: "no"',
        'claude_code:\n  choice: "no"\n'
        f'  {authorization_key}: "{authorization_marker}"',
    )
    authorization_result, authorization_error = execute_setup_state(authorization_state)
    if authorization_error:
        errors.append(f"authorization detail fixture failed: {authorization_error}")
    elif authorization_result is not None and (
        authorization_result.returncode != 1
        or "setup_state=invalid" not in authorization_result.stdout.splitlines()
        or authorization_marker in authorization_result.stdout
        or authorization_marker in authorization_result.stderr
    ):
        errors.append("setup-state authorization detail was accepted or exposed")

    credential_url_marker = "PRIVATE-URL-CREDENTIAL-MARKER"
    credential_url = "https://example:" + credential_url_marker + "@github.com/a/b.git"
    credential_url_state = private_github_v2.replace(
        "https://github.com/example/research.git", credential_url
    )
    credential_url_result, credential_url_error = execute_setup_state(
        credential_url_state
    )
    if credential_url_error:
        errors.append(f"credential URL fixture failed: {credential_url_error}")
    elif credential_url_result is not None and (
        credential_url_result.returncode != 1
        or "setup_state=invalid" not in credential_url_result.stdout.splitlines()
        or credential_url_marker in credential_url_result.stdout
        or credential_url_marker in credential_url_result.stderr
    ):
        errors.append("setup-state credential URL was accepted or exposed")

    symlink_result, symlink_error = execute_setup_state(
        complete_setup_state(2, True), state_symlink=True
    )
    if symlink_error:
        errors.append(f"symlink fixture failed: {symlink_error}")
    elif symlink_result is not None and (
        symlink_result.returncode != 1
        or symlink_result.stdout.splitlines()
        != ["setup_state=invalid", "setup_reason=unsafe_link"]
    ):
        errors.append("setup-state symlink fixture was not rejected safely")


def execute_setup_migration(
    state_text: str,
    remote_visibility: str | None = None,
) -> tuple[subprocess.CompletedProcess[str], str, str | None]:
    with tempfile.TemporaryDirectory(prefix="workbench-migration-") as temp_name:
        fixture_root = Path(temp_name) / "workbench"
        scripts_dir = fixture_root / "scripts"
        harness_dir = fixture_root / ".harness"
        scripts_dir.mkdir(parents=True)
        harness_dir.mkdir()
        for script_name in (
            "setup-state.py",
            "migrate-setup-v1.py",
            "remote-state.py",
        ):
            shutil.copy2(ROOT / "scripts" / script_name, scripts_dir / script_name)
        if remote_visibility is not None:
            (scripts_dir / "remote-state.py").write_text(
                "#!/usr/bin/env python3\n"
                'print("git_tree=yes")\n'
                'print("origin=github-present-redacted")\n'
                f'print("visibility={remote_visibility}")\n',
                encoding="utf-8",
            )
        state_path = harness_dir / "local.yaml"
        state_path.write_text(state_text, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(scripts_dir / "migrate-setup-v1.py")],
            cwd=fixture_root,
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            check=False,
        )
        final_text = state_path.read_text(encoding="utf-8")
        backup_path = harness_dir / "local.v1-backup.yaml"
        backup_text = (
            backup_path.read_text(encoding="utf-8") if backup_path.is_file() else None
        )
        return result, final_text, backup_text


def validate_setup_migration_fixtures(errors: list[str]) -> None:
    private_marker = "PRIVATE-PRESERVED-ROOT-MARKER"
    valid_v1 = complete_setup_state(1, False).replace(
        '  root: ""', f'  root: "/Users/example/{private_marker}"'
    ).replace("setup_version: 1", "setup_version:  1").replace(
        "status: complete", 'status: "complete"'
    ).replace('completed_at: "2026-07-19"\n', "")
    result, migrated, backup = execute_setup_migration(valid_v1)
    if (
        result.returncode != 0
        or result.stdout.splitlines() != ["migration=ready_for_new_questions"]
        or private_marker in result.stdout
        or private_marker in result.stderr
        or private_marker not in migrated
        or backup != valid_v1
        or "setup_version: 2" not in migrated
        or 'claude_code:\n  choice: ""' not in migrated
        or 'chatgpt_browser:\n  choice: ""' not in migrated
        or 'completed_at: ""' not in migrated
    ):
        errors.append("version 1 setup migration was not atomic and redacted")
    else:
        migrated_result, migrated_error = execute_setup_state(migrated)
        if (
            migrated_error
            or migrated_result is None
            or migrated_result.returncode != 0
            or "setup_state=ok" not in migrated_result.stdout.splitlines()
            or "status=in_progress" not in migrated_result.stdout.splitlines()
        ):
            errors.append("migrated version 2 setup did not validate")

    public_v1 = complete_setup_state(1, False).replace(
        'github:\n  choice: "no"\n  repository: ""\n  visibility: ""',
        'github:\n  choice: "yes"\n  repository: "example/research"\n'
        '  visibility: "public"',
    )
    public_result, public_after, public_backup = execute_setup_migration(public_v1)
    if (
        public_result.returncode != 1
        or public_result.stdout.splitlines() != ["migration=private_remote_required"]
        or public_after != public_v1
        or public_backup is not None
    ):
        errors.append("version 1 migration did not stop for a public remote")

    incomplete_v1 = complete_setup_state(1, False).replace(
        'language: "en"', 'language: ""'
    ).replace("status: complete", "status: in_progress")
    incomplete_result, incomplete_after, incomplete_backup = execute_setup_migration(
        incomplete_v1
    )
    if (
        incomplete_result.returncode != 1
        or incomplete_result.stdout.splitlines() != ["migration=state_not_ready"]
        or incomplete_after != incomplete_v1
        or incomplete_backup is not None
    ):
        errors.append("version 1 migration changed an incomplete state")

    live_private_result, live_private_after, live_private_backup = (
        execute_setup_migration(public_v1, remote_visibility="private")
    )
    if (
        live_private_result.returncode != 0
        or live_private_result.stdout.splitlines()
        != ["migration=ready_for_new_questions"]
        or 'visibility: "private"' not in live_private_after
        or live_private_backup != public_v1
    ):
        errors.append("migration did not reconcile a live private legacy remote")


def validate_auth_command_fixtures(errors: list[str]) -> None:
    fixtures = (
        ("unsuppressed", "claude auth status", True),
        ("unsuppressed Windows quoted", '& "claude" auth status', True),
        ("unsuppressed Windows exe", "claude.exe auth status", True),
        ("safe POSIX", "claude auth status >/dev/null 2>&1", False),
        ("unsafe POSIX order", "claude auth status 2>&1 >/dev/null", True),
        ("safe separate POSIX", "claude auth status 2>/dev/null >/dev/null", False),
        ("safe PowerShell", "claude auth status *> $null", False),
        ("negative status mention", "Never run claude auth status.", False),
        (
            "negative replacement mention",
            "Do not replace the helper with unsuppressed claude auth status output.",
            False,
        ),
        (
            "negative qualified status mention",
            "Do not run unsuppressed claude auth status.",
            False,
        ),
        (
            "unrelated negative status",
            "Do not print the banner; run claude auth status",
            True,
        ),
        (
            "same-clause positive status",
            "Do not print the banner and run claude auth status",
            True,
        ),
        (
            "Korean negative status",
            "claude auth status를 실행하지 마세요.",
            False,
        ),
        (
            "Korean mixed positive status",
            "배너는 출력하지 말고 claude auth status를 실행하세요.",
            True,
        ),
        ("negative token mention", "Never run claude setup-token.", False),
        ("unsuppressed Windows token", "& 'claude' setup-token", True),
        ("unsuppressed Windows exe token", "claude.exe setup-token", True),
        (
            "unrelated negative token",
            "Do not wait; first run claude setup-token",
            True,
        ),
        (
            "Korean negative token",
            "claude setup-token 사용 금지",
            False,
        ),
        (
            "Korean mixed positive token",
            "다른 명령은 실행하지 말고 claude setup-token을 사용하세요.",
            True,
        ),
        (
            "Korean capture mixed positive token",
            "화면은 캡처하면 안 되고 claude setup-token을 실행하세요.",
            True,
        ),
    )
    for label, command, should_error in fixtures:
        fixture_errors: list[str] = []
        validate_auth_commands("auth-fixture.txt", command, fixture_errors)
        if bool(fixture_errors) != should_error:
            errors.append(f"{label} auth-redirection fixture was misclassified")


def validate_secret_fixtures(errors: list[str]) -> None:
    assigned = SECRET_PATTERNS["assigned secret"]
    sample = "abcdefgh" + "ijklmnopqrstuvwxyz"
    token_key = "to" + "ken"
    api_key_name = "api" + "_key"
    anthropic_key_name = "anthropic" + "_api_key"
    should_match = (
        token_key + ": " + sample,
        '"' + token_key + '": "' + sample + '"',
        "'" + api_key_name + "': '" + sample + "'",
        anthropic_key_name.upper() + "=" + sample,
        token_key + ": `" + sample + "`",
    )
    should_not_match = (
        token_key + ": placeholder",
        '"' + token_key + '": "placeholder"',
        api_key_name + ": null",
    )
    if any(not assigned.search(value) for value in should_match):
        errors.append("assigned-secret scanner missed a quoted or unquoted fixture")
    if any(assigned.search(value) for value in should_not_match):
        errors.append("assigned-secret scanner rejected a documented placeholder")

    key_pattern = SECRET_PATTERNS["private key block"]
    key_headers = tuple(
        "-----BEGIN " + kind + "-----"
        for kind in (
            "PRIVATE KEY",
            "ENCRYPTED PRIVATE KEY",
            "DSA PRIVATE KEY",
            "PGP PRIVATE KEY BLOCK",
        )
    )
    if any(not key_pattern.search(header) for header in key_headers):
        errors.append("private-key scanner missed a supported key header fixture")

    direct_secret_fixtures = {
        "GitHub fine-grained token": "github" + "_pat_" + "A" * 24,
        "AWS access key": "AKIA" + "ABCDEFGHIJKLMNOP",
        "Google API key": "AIza" + "A" * 35,
        "Slack token": "xoxb-" + "1234567890-abcdefghij",
    }
    for label, value in direct_secret_fixtures.items():
        if not SECRET_PATTERNS[label].search(value):
            errors.append(f"{label} scanner missed its fixture")

    personal_should_match = (
        "/Users/" + "realperson",
        "/users/" + "realperson/research",
        "/home/" + "realperson",
        "C:\\Users\\" + "realperson",
        "person" + "@private-university.edu",
    )
    personal_should_not_match = (
        "/Users/username/project",
        "/Users/example/project",
        "person" + "@example.com",
        "git" + "@github.com",
    )
    if any(
        not any(pattern.search(value) for pattern in PERSONAL_PATHS.values())
        for value in personal_should_match
    ):
        errors.append("personal-data scanner missed a path or email fixture")
    if any(
        any(pattern.search(value) for pattern in PERSONAL_PATHS.values())
        for value in personal_should_not_match
    ):
        errors.append("personal-data scanner rejected a documented example fixture")


def validate_claude_readiness_fixtures(errors: list[str]) -> None:
    try:
        helper = runpy.run_path(str(ROOT / "scripts/claude-readiness.py"))
    except (OSError, SyntaxError, RuntimeError):
        errors.append("Claude readiness helper could not be loaded safely")
        return
    classify = helper.get("classify_status")
    capabilities = helper.get("has_review_capabilities")
    combine = helper.get("combine_policy_states")
    run_captured = helper.get("run_captured")
    route_override = helper.get("has_route_or_telemetry_override")
    if (
        not callable(classify)
        or not callable(capabilities)
        or not callable(combine)
        or not callable(run_captured)
        or not callable(route_override)
    ):
        errors.append("Claude readiness helper is missing testable classifiers")
        return

    direct = {
        "loggedIn": True,
        "authMethod": "claude.ai",
        "apiProvider": "firstParty",
        "subscriptionType": "pro",
    }
    classifications = (
        (direct, False, "absent", "ready"),
        (direct, True, "absent", "alternate_or_unknown_route"),
        (direct, False, "present", "managed_policy_present"),
        (direct, False, "unknown", "managed_policy_unverifiable"),
        ({**direct, "subscriptionType": "team"}, False, "absent", "ineligible_or_managed_subscription"),
        ({**direct, "apiProvider": "gateway"}, False, "absent", "alternate_or_unknown_route"),
        ({"loggedIn": False}, False, "absent", "not_authenticated"),
    )
    for payload, override, policy, expected in classifications:
        if classify(payload, override, policy) != expected:
            errors.append(f"Claude readiness classification failed for {expected}")

    required_flags = helper.get("REQUIRED_REVIEW_FLAGS")
    if not isinstance(required_flags, set):
        errors.append("Claude readiness helper has no required flag set")
    else:
        complete_help = "\n".join(sorted(required_flags))
        incomplete_help = complete_help.replace("--safe-mode", "")
        if not capabilities(complete_help) or capabilities(incomplete_help):
            errors.append("Claude readiness capability check failed closed incorrectly")
    if combine(["absent", "present"]) != "present" or combine(
        ["absent", "unknown"]
    ) != "unknown":
        errors.append("Claude managed-policy state precedence is unsafe")
    if not route_override({"OTEL_LOGS_EXPORTER": "otlp"}) or not route_override(
        {"CLAUDE_CODE_USE_MANTLE": "1"}
    ) or route_override({"OTEL_LOGS_EXPORTER": ""}):
        errors.append("Claude readiness route or telemetry override check is unsafe")

    utf8_result = run_captured(
        sys.executable, "-X", "utf8", "-c", "print('readiness \\u2713')"
    )
    invalid_utf8_result = run_captured(
        sys.executable, "-c", "import os; os.write(1, bytes([255]))"
    )
    if (
        utf8_result is None
        or utf8_result.returncode != 0
        or "readiness" not in utf8_result.stdout
    ):
        errors.append("Claude readiness helper rejected valid UTF-8 output")
    if invalid_utf8_result is not None:
        errors.append("Claude readiness helper did not fail closed on invalid UTF-8")


def validate_remote_state_fixtures(errors: list[str]) -> None:
    try:
        helper = runpy.run_path(str(ROOT / "scripts/remote-state.py"))
    except (OSError, SyntaxError, RuntimeError):
        errors.append("remote-state helper could not be loaded safely")
        return
    parse_repository = helper.get("github_repository")
    capture = helper.get("capture")
    if not callable(parse_repository) or not callable(capture):
        errors.append("remote-state helper is missing testable classifiers")
        return
    valid_urls = (
        "example/research",
        "https://github.com/example/research.git",
        "git" + "@github.com:example/research.git",
        "ssh://git" + "@github.com/example/research.git",
    )
    # owner/repository is a setup-state label rather than a configured Git URL.
    if parse_repository(valid_urls[0]) is not None:
        errors.append("remote-state treated a non-URL label as a configured remote")
    if any(parse_repository(value) is None for value in valid_urls[1:]):
        errors.append("remote-state rejected a credential-free GitHub fixture")
    unsafe_urls = (
        "https://" + "user:credential" + "@example.com/a/b.git",
        "https://" + "user:credential" + "@github.com/a/b.git",
        "https://github.com/a/b.git?" + "to" + "ken=credential",
        "ssh://someone" + "@github.com/a/b.git",
    )
    if any(parse_repository(value) is not None for value in unsafe_urls):
        errors.append("remote-state accepted a credential-bearing or ambiguous URL")

    utf8_code, utf8_text = capture(
        sys.executable, "-X", "utf8", "-c", "print('remote \\u2713')"
    )
    invalid_code, invalid_text = capture(
        sys.executable, "-c", "import os; os.write(1, bytes([255]))"
    )
    if utf8_code != 0 or "remote" not in utf8_text:
        errors.append("remote-state rejected valid UTF-8 output")
    if invalid_code == 0 or invalid_text:
        errors.append("remote-state did not fail closed on invalid UTF-8")


def run_bundled_plugin_installer(
    fixture_root: Path, *arguments: str
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [
            sys.executable,
            str(fixture_root / "scripts/install-bundled-obsidian-plugin.py"),
            *arguments,
        ],
        cwd=fixture_root,
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        check=False,
    )
    fixture_text = str(fixture_root)
    if fixture_text in result.stdout or fixture_text in result.stderr:
        return subprocess.CompletedProcess(
            result.args,
            99,
            result.stdout,
            "installer output exposed its workspace path",
        )
    return result


def make_bundled_plugin_fixture(parent: Path) -> Path:
    fixture_root = parent / "workbench"
    scripts_dir = fixture_root / "scripts"
    bundle_parent = fixture_root / "optional" / "obsidian-plugins"
    scripts_dir.mkdir(parents=True)
    (fixture_root / ".obsidian").mkdir()
    shutil.copy2(
        ROOT / "scripts/install-bundled-obsidian-plugin.py",
        scripts_dir / "install-bundled-obsidian-plugin.py",
    )
    shutil.copytree(
        ROOT / "optional/obsidian-plugins/mrw-latex-delimiter-compat",
        bundle_parent / "mrw-latex-delimiter-compat",
    )
    return fixture_root


def validate_bundled_obsidian_plugin(errors: list[str]) -> None:
    plugin_id = "mrw-latex-delimiter-compat"
    bundle = ROOT / "optional" / "obsidian-plugins" / plugin_id
    expected_files = {"LICENSE", "README.md", "main.js", "manifest.json"}
    try:
        bundle_files = {entry.name for entry in os.scandir(bundle)}
    except OSError:
        errors.append("bundled Obsidian plugin directory could not be read")
        return
    if bundle_files != expected_files:
        errors.append("bundled Obsidian plugin must contain exactly four reviewed files")

    try:
        manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors.append("bundled Obsidian plugin manifest is invalid JSON")
        return
    required_strings = (
        "id",
        "name",
        "version",
        "minAppVersion",
        "description",
        "author",
    )
    semver = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
    if (
        not isinstance(manifest, dict)
        or manifest.get("id") != plugin_id
        or bundle.name != plugin_id
        or any(
            not isinstance(manifest.get(key), str) or not manifest[key]
            for key in required_strings
        )
        or not semver.fullmatch(str(manifest.get("version", "")))
        or not semver.fullmatch(str(manifest.get("minAppVersion", "")))
        or not isinstance(manifest.get("isDesktopOnly"), bool)
    ):
        errors.append("bundled Obsidian plugin manifest fields are invalid")

    main_js = read_text(bundle / "main.js")
    if not main_js:
        errors.append("bundled Obsidian plugin main.js is missing or unreadable")
    else:
        forbidden_capabilities = (
            "fetch(",
            "requestUrl",
            "XMLHttpRequest",
            "WebSocket",
            "child_process",
            "vault.create",
            "vault.modify",
            "adapter.write",
        )
        if any(capability in main_js for capability in forbidden_capabilities):
            errors.append("bundled Obsidian plugin gained an undisclosed external or write capability")

    installer = read_text(ROOT / "scripts/install-bundled-obsidian-plugin.py")
    required_installer_boundaries = (
        'PLUGIN_ID = "mrw-latex-delimiter-compat"',
        'PRESERVED_LOCAL_FILES = {"data.json"}',
        'IGNORED_METADATA_FILES = {".DS_Store"',
        'action.add_argument("--install"',
        'action.add_argument("--update"',
        '"--consent"',
        "ensure_safe_chain",
        "is_link_like",
        "community-plugins.json",
    )
    if not installer or any(
        boundary not in installer for boundary in required_installer_boundaries
    ):
        errors.append("bundled Obsidian plugin installer is missing safety boundaries")

    workflow = read_text(ROOT / ".github/workflows/validate.yml")
    required_workflow_checks = (
        'python-version: ["3.9", "3.12"]',
        "actions/setup-node@v6",
        "python -B -m unittest discover -s meta/research-tickets/tests -q",
        "node --check optional/obsidian-plugins/mrw-latex-delimiter-compat/main.js",
        "node scripts/tests/mrw-latex-delimiter-compat.test.js",
    )
    if not workflow or any(check not in workflow for check in required_workflow_checks):
        errors.append("CI is missing Python compatibility or bundled plugin tests")

    with tempfile.TemporaryDirectory(prefix="workbench-plugin-") as temp_name:
        fixture_root = make_bundled_plugin_fixture(Path(temp_name))
        obsidian_dir = fixture_root / ".obsidian"
        installed_dir = obsidian_dir / "plugins" / plugin_id
        community_state = obsidian_dir / "community-plugins.json"
        community_sentinel = '["existing-plugin"]\n'
        community_state.write_text(community_sentinel, encoding="utf-8")
        (
            fixture_root
            / "optional/obsidian-plugins/mrw-latex-delimiter-compat/.DS_Store"
        ).write_text("fixture\n", encoding="utf-8")

        initial_status = run_bundled_plugin_installer(fixture_root)
        if (
            initial_status.returncode != 0
            or "plugin_status=not_installed" not in initial_status.stdout
            or installed_dir.exists()
        ):
            errors.append("bundled plugin status check was not read-only")

        missing_consent = run_bundled_plugin_installer(fixture_root, "--install")
        if (
            missing_consent.returncode != 2
            or "result=consent_required" not in missing_consent.stdout
            or installed_dir.exists()
        ):
            errors.append("bundled plugin install did not fail closed without consent")

        installed = run_bundled_plugin_installer(
            fixture_root, "--install", "--consent"
        )
        copied_files = (
            {entry.name for entry in os.scandir(installed_dir)}
            if installed_dir.is_dir()
            else set()
        )
        copied_bytes_match = installed_dir.is_dir() and all(
            (installed_dir / name).read_bytes()
            == (bundle / name).read_bytes()
            for name in ("main.js", "manifest.json")
        )
        if (
            installed.returncode != 0
            or "result=installed" not in installed.stdout
            or copied_files != {"main.js", "manifest.json"}
            or not copied_bytes_match
            or community_state.read_text(encoding="utf-8") != community_sentinel
        ):
            errors.append("bundled plugin consented install fixture failed")

        current = run_bundled_plugin_installer(fixture_root)
        if current.returncode != 0 or "plugin_status=installed_current" not in current.stdout:
            errors.append("bundled plugin current-version detection failed")

        (installed_dir / "Thumbs.db").write_text("fixture\n", encoding="utf-8")
        current_with_metadata = run_bundled_plugin_installer(fixture_root)
        if (
            current_with_metadata.returncode != 0
            or "plugin_status=installed_current" not in current_with_metadata.stdout
        ):
            errors.append("bundled plugin rejected harmless operating-system metadata")

        local_data = '{"fixture":true}\n'
        (installed_dir / "data.json").write_text(local_data, encoding="utf-8")
        old_manifest = json.loads((installed_dir / "manifest.json").read_text(encoding="utf-8"))
        old_manifest["version"] = "0.3.3"
        (installed_dir / "manifest.json").write_text(
            json.dumps(old_manifest, indent=2) + "\n", encoding="utf-8"
        )
        (installed_dir / "main.js").write_text("// older fixture\n", encoding="utf-8")

        stale = run_bundled_plugin_installer(fixture_root)
        update_without_consent = run_bundled_plugin_installer(fixture_root, "--update")
        if (
            stale.returncode != 0
            or "plugin_status=installed_stale" not in stale.stdout
            or update_without_consent.returncode != 2
            or "result=consent_required" not in update_without_consent.stdout
            or (installed_dir / "main.js").read_text(encoding="utf-8")
            != "// older fixture\n"
        ):
            errors.append("bundled plugin update did not preserve consent or stale state")

        updated = run_bundled_plugin_installer(
            fixture_root, "--update", "--consent"
        )
        if (
            updated.returncode != 0
            or "result=updated" not in updated.stdout
            or (installed_dir / "data.json").read_text(encoding="utf-8") != local_data
            or community_state.read_text(encoding="utf-8") != community_sentinel
            or any(
                (installed_dir / name).read_bytes() != (bundle / name).read_bytes()
                for name in ("main.js", "manifest.json")
            )
        ):
            errors.append("bundled plugin consented update fixture failed")

        (installed_dir / "unexpected.js").write_text("fixture\n", encoding="utf-8")
        refused = run_bundled_plugin_installer(
            fixture_root, "--update", "--consent"
        )
        if refused.returncode == 0 or "result=update_refused" not in refused.stdout:
            errors.append("bundled plugin installer accepted unexpected destination files")

    with tempfile.TemporaryDirectory(prefix="workbench-plugin-link-") as temp_name:
        fixture_parent = Path(temp_name)
        fixture_root = make_bundled_plugin_fixture(fixture_parent)
        plugins_path = fixture_root / ".obsidian" / "plugins"
        redirect_target = fixture_parent / "redirect-target"
        redirect_target.mkdir()
        link_ready = False
        try:
            os.symlink(redirect_target, plugins_path, target_is_directory=True)
            link_ready = True
        except OSError:
            if os.name == "nt":
                junction = subprocess.run(
                    [
                        "cmd",
                        "/d",
                        "/c",
                        "mklink",
                        "/J",
                        str(plugins_path),
                        str(redirect_target),
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                link_ready = junction.returncode == 0
        if not link_ready:
            errors.append("could not create bundled plugin link-safety fixture")
        else:
            linked = run_bundled_plugin_installer(
                fixture_root, "--install", "--consent"
            )
            if linked.returncode == 0 or any(redirect_target.iterdir()):
                errors.append("bundled plugin installer wrote through a link or junction")


def execute_vault_lint(
    note_text: str | None = None,
    binary_name: str | None = None,
    note_relative: str = "notes/fixture.md",
    note_texts: dict[str, str] | None = None,
    extra_files: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="workbench-lint-") as temp_name:
        fixture_root = Path(temp_name) / "workbench"
        scripts_dir = fixture_root / "scripts"
        scripts_dir.mkdir(parents=True)
        shutil.copy2(ROOT / "scripts/vault-lint.py", scripts_dir / "vault-lint.py")
        for module in ("math_target.py", "math_run_checks.py"):
            shutil.copy2(ROOT / "scripts" / module, scripts_dir / module)
        shutil.copy2(
            ROOT / "scripts/formalization_manifest.py",
            scripts_dir / "formalization_manifest.py",
        )
        for name in ("inbox", "ideas", "papers", "notes", "projects"):
            (fixture_root / name).mkdir()
        if note_text is not None:
            note_path = fixture_root / note_relative
            note_path.parent.mkdir(parents=True, exist_ok=True)
            note_path.write_text(note_text, encoding="utf-8")
        for relative, text in (note_texts or {}).items():
            note_path = fixture_root / relative
            note_path.parent.mkdir(parents=True, exist_ok=True)
            note_path.write_text(text, encoding="utf-8")
        for relative, text in (extra_files or {}).items():
            extra_path = fixture_root / relative
            extra_path.parent.mkdir(parents=True, exist_ok=True)
            extra_path.write_text(text, encoding="utf-8")
        if binary_name is not None:
            (fixture_root / "notes" / binary_name).write_bytes(b"fixture")
        return subprocess.run(
            [sys.executable, str(scripts_dir / "vault-lint.py")],
            cwd=fixture_root,
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            check=False,
        )


def fixture_sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def valid_formalization_fixture() -> tuple[dict[str, object], dict[str, str]]:
    """Return a recorded-pass manifest and the repository artifacts it pins."""
    files = {
        "projects/fixture/README.md": "# Fixture project\n",
        "projects/fixture/logs/research-run.md": "Exact target: fixture theorem\n",
        "projects/fixture/formalization/natural-statement.md": "Fixture theorem.\n",
        "projects/fixture/formalization/trusted/expected-type.txt": "Fixture.theorem : True\n",
        "projects/fixture/formalization/trusted/lake-manifest.json": "{}\n",
        "projects/fixture/formalization/trusted/Challenge.lean": "import Fixture.Solution\nexample : True := Fixture.theorem\n",
        "projects/fixture/formalization/submission/Solution.lean": "namespace Fixture\ntheorem theorem : True := by trivial\nend Fixture\n",
        "projects/fixture/formalization/checks/source-policy.txt": "no sorry or admit found\n",
        "projects/fixture/formalization/checks/build.log": "build passed\n",
        "projects/fixture/formalization/checks/declaration-type.txt": "type matched\n",
        "projects/fixture/formalization/checks/axioms.txt": "[]\n",
        "projects/fixture/formalization/checks/kernel.log": "kernel accepted\n",
    }
    hashes = {path: fixture_sha256(text) for path, text in files.items()}
    challenge_paths = sorted(
        path
        for path in files
        if path.startswith("projects/fixture/formalization/trusted/")
    )
    challenge_records = b"".join(
        path.encode("utf-8")
        + b"\0"
        + hashes[path].encode("ascii")
        + b"\n"
        for path in challenge_paths
    )
    challenge_tree = "sha256:" + hashlib.sha256(challenge_records).hexdigest()
    manifest: dict[str, object] = {
        "schema_version": 1,
        "manifest_id": "Formalization-001",
        "run_id": "Run-20260724-001",
        "obligation_id": "Obligation-001",
        "created": "2026-07-24",
        "updated": "2026-07-24",
        "source_snapshot": {
            "repository_commit": "1" * 40,
            "working_tree": "clean",
        },
        "spine_target": {
            "id": "Lem-001",
            "project_readme": "projects/fixture/README.md",
        },
        "problem_contract": {
            "version": "v1",
            "artifact": "projects/fixture/logs/research-run.md",
            "artifact_sha256": hashes["projects/fixture/logs/research-run.md"],
            "exact_target_sha256": hashes[
                "projects/fixture/formalization/natural-statement.md"
            ],
        },
        "natural_statement": {
            "artifact": "projects/fixture/formalization/natural-statement.md",
            "sha256": hashes[
                "projects/fixture/formalization/natural-statement.md"
            ],
        },
        "formal_target": {
            "language": "Lean 4",
            "declaration": "Fixture.theorem",
            "expected_type_artifact": "projects/fixture/formalization/trusted/expected-type.txt",
            "expected_type_sha256": hashes[
                "projects/fixture/formalization/trusted/expected-type.txt"
            ],
        },
        "toolchain": {
            "lean_version": "4.19.0",
            "lake_version": "5.0.0",
            "dependency_lock_artifact": "projects/fixture/formalization/trusted/lake-manifest.json",
            "dependency_lock_sha256": hashes[
                "projects/fixture/formalization/trusted/lake-manifest.json"
            ],
        },
        "trusted_challenge": {
            "root": "projects/fixture/formalization/trusted",
            "tree_digest_algorithm": "sha256-v1",
            "baseline_tree_sha256": challenge_tree,
            "after_tree_sha256": challenge_tree,
            "files": [
                {"path": path, "sha256": hashes[path]} for path in challenge_paths
            ],
            "allowed_axioms": [],
        },
        "untrusted_submission": {
            "root": "projects/fixture/formalization/submission",
            "files": [
                {
                    "path": "projects/fixture/formalization/submission/Solution.lean",
                    "sha256": hashes[
                        "projects/fixture/formalization/submission/Solution.lean"
                    ],
                }
            ],
            "produced_by_branch": "Branch-001",
            "solver_write_scope": "solution-only",
        },
        "checks": {
            "challenge_integrity": {"result": "pass"},
            "source_policy": {
                "result": "pass",
                "artifact": "projects/fixture/formalization/checks/source-policy.txt",
                "sha256": hashes[
                    "projects/fixture/formalization/checks/source-policy.txt"
                ],
            },
            "build": {
                "argv": ["lake", "env", "lean", "Challenge.lean"],
                "result": "pass",
                "exit_code": 0,
                "log_artifact": "projects/fixture/formalization/checks/build.log",
                "log_sha256": hashes[
                    "projects/fixture/formalization/checks/build.log"
                ],
            },
            "declaration_type": {
                "comparator": "Lean elaborated typecheck",
                "comparator_version": "1",
                "result": "pass",
                "artifact": "projects/fixture/formalization/checks/declaration-type.txt",
                "sha256": hashes[
                    "projects/fixture/formalization/checks/declaration-type.txt"
                ],
            },
            "axioms": {
                "observed": [],
                "result": "pass",
                "artifact": "projects/fixture/formalization/checks/axioms.txt",
                "sha256": hashes[
                    "projects/fixture/formalization/checks/axioms.txt"
                ],
            },
            "primary_kernel": {
                "version": "Lean 4.19.0",
                "result": "pass",
                "log_artifact": "projects/fixture/formalization/checks/kernel.log",
                "log_sha256": hashes[
                    "projects/fixture/formalization/checks/kernel.log"
                ],
            },
            "secondary_recheck": {
                "relation": "not-run",
                "checker": None,
                "version": None,
                "result": "not-run",
                "log_artifact": None,
                "log_sha256": None,
            },
        },
        "statement_match": {
            "status": "not-confirmed",
            "exact_scope": None,
            "confirmed_by": None,
            "date": None,
            "evidence_artifact": None,
            "evidence_sha256": None,
        },
        "final_record": {
            "trust_boundary": "intact",
            "formal_encoding": "recorded-pass",
            "statement_correspondence": "not-confirmed",
        },
    }
    return manifest, files


def execute_formalization_manifest(
    manifest: dict[str, object] | None = None,
    files: dict[str, str] | None = None,
    *,
    raw_manifest: str | None = None,
    verify_files: bool = True,
) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="workbench-formalization-") as temp_name:
        fixture_root = Path(temp_name) / "workbench"
        scripts_dir = fixture_root / "scripts"
        scripts_dir.mkdir(parents=True)
        shutil.copy2(
            ROOT / "scripts/formalization_manifest.py",
            scripts_dir / "formalization_manifest.py",
        )
        for relative, text in (files or {}).items():
            artifact = fixture_root / relative
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text(text, encoding="utf-8")
        manifest_path = fixture_root / "formalization-manifest.json"
        manifest_path.write_text(
            raw_manifest
            if raw_manifest is not None
            else json.dumps(manifest or {}, indent=2),
            encoding="utf-8",
        )
        command = [
            sys.executable,
            str(scripts_dir / "formalization_manifest.py"),
            str(manifest_path),
            "--root",
            str(fixture_root),
        ]
        if verify_files:
            command.append("--verify-files")
        return subprocess.run(
            command,
            cwd=fixture_root,
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            check=False,
        )


def validate_formalization_manifest_fixtures(errors: list[str]) -> None:
    manifest, files = valid_formalization_fixture()

    def clone() -> dict[str, object]:
        return json.loads(json.dumps(manifest))

    valid_result = execute_formalization_manifest(manifest, files)
    overlap = clone()
    overlap["untrusted_submission"]["root"] = overlap["trusted_challenge"]["root"]  # type: ignore[index]
    overlap_result = execute_formalization_manifest(overlap, files)
    changed_challenge = clone()
    changed_challenge["trusted_challenge"]["after_tree_sha256"] = "sha256:" + "f" * 64  # type: ignore[index]
    changed_challenge_result = execute_formalization_manifest(changed_challenge, files)
    unexpected_axiom = clone()
    unexpected_axiom["checks"]["axioms"]["observed"] = ["Classical.choice"]  # type: ignore[index]
    unexpected_axiom_result = execute_formalization_manifest(unexpected_axiom, files)
    target_hash_mismatch = clone()
    target_hash_mismatch["problem_contract"]["exact_target_sha256"] = "sha256:" + "e" * 64  # type: ignore[index]
    target_hash_mismatch_result = execute_formalization_manifest(
        target_hash_mismatch, files
    )
    unsafe_path = clone()
    unsafe_path["natural_statement"]["artifact"] = "/tmp/statement.md"  # type: ignore[index]
    unsafe_path_result = execute_formalization_manifest(unsafe_path, files)
    invalid_scope = clone()
    invalid_scope["untrusted_submission"]["solver_write_scope"] = "whole-repository"  # type: ignore[index]
    invalid_scope_result = execute_formalization_manifest(invalid_scope, files)
    placeholder_toolchain = clone()
    placeholder_toolchain["toolchain"][  # type: ignore[index]
        "lean_version"
    ] = "<record the exact Lean version; replace this placeholder>"
    placeholder_toolchain_result = execute_formalization_manifest(
        placeholder_toolchain, files
    )
    incomplete_match = clone()
    incomplete_match["statement_match"].update(  # type: ignore[union-attr]
        {
            "status": "confirmed",
            "exact_scope": "fixture theorem",
            "confirmed_by": None,
            "date": "2026-07-24",
            "evidence_artifact": "projects/fixture/formalization/natural-statement.md",
            "evidence_sha256": files
            and fixture_sha256(files["projects/fixture/formalization/natural-statement.md"]),
        }
    )
    incomplete_match["final_record"]["statement_correspondence"] = "confirmed"  # type: ignore[index]
    incomplete_match_result = execute_formalization_manifest(incomplete_match, files)
    missing_build_log = clone()
    missing_build_log["checks"]["build"]["log_artifact"] = None  # type: ignore[index]
    missing_build_log["checks"]["build"]["log_sha256"] = None  # type: ignore[index]
    missing_build_log_result = execute_formalization_manifest(missing_build_log, files)
    duplicate_json = json.dumps(manifest).replace(
        '"run_id": "Run-20260724-001",',
        '"run_id": "Run-20260724-001", "run_id": "Run-20260724-002",',
        1,
    )
    duplicate_key_result = execute_formalization_manifest(
        files=files, raw_manifest=duplicate_json
    )
    tampered_files = dict(files)
    tampered_files[
        "projects/fixture/formalization/submission/Solution.lean"
    ] += "-- tampered\n"
    tampered_artifact_result = execute_formalization_manifest(manifest, tampered_files)
    unlisted_trusted_files = dict(files)
    unlisted_trusted_files[
        "projects/fixture/formalization/trusted/Unlisted.lean"
    ] = "axiom hidden : False\n"
    unlisted_trusted_file_result = execute_formalization_manifest(
        manifest, unlisted_trusted_files
    )
    secondary_files = dict(files)
    secondary_log = "projects/fixture/formalization/checks/secondary.log"
    secondary_files[secondary_log] = "independent checker rejected the submission\n"
    failed_secondary = clone()
    failed_secondary["checks"]["secondary_recheck"].update(  # type: ignore[index,union-attr]
        {
            "relation": "independent-checker",
            "checker": "fixture-independent-checker",
            "version": "1",
            "result": "fail",
            "log_artifact": secondary_log,
            "log_sha256": fixture_sha256(secondary_files[secondary_log]),
        }
    )
    failed_secondary_result = execute_formalization_manifest(
        failed_secondary, secondary_files
    )
    recorded_conflict = json.loads(json.dumps(failed_secondary))
    recorded_conflict["final_record"]["formal_encoding"] = "conflict"  # type: ignore[index]
    recorded_conflict_result = execute_formalization_manifest(
        recorded_conflict, secondary_files
    )
    same_kernel_failure = json.loads(json.dumps(failed_secondary))
    same_kernel_failure["checks"]["secondary_recheck"][  # type: ignore[index]
        "relation"
    ] = "same-kernel-clean-rebuild"
    same_kernel_failure["final_record"]["formal_encoding"] = "conflict"  # type: ignore[index]
    same_kernel_conflict_result = execute_formalization_manifest(
        same_kernel_failure, secondary_files
    )
    same_kernel_recorded_fail = json.loads(json.dumps(same_kernel_failure))
    same_kernel_recorded_fail["final_record"][  # type: ignore[index]
        "formal_encoding"
    ] = "recorded-fail"
    same_kernel_recorded_fail_result = execute_formalization_manifest(
        same_kernel_recorded_fail, secondary_files
    )
    mandatory_failure_conflict = clone()
    mandatory_failure_conflict["checks"]["build"]["result"] = "fail"  # type: ignore[index]
    mandatory_failure_conflict["checks"]["build"]["exit_code"] = 1  # type: ignore[index]
    mandatory_failure_conflict["final_record"]["formal_encoding"] = "conflict"  # type: ignore[index]
    mandatory_failure_conflict_result = execute_formalization_manifest(
        mandatory_failure_conflict, files
    )
    secondary_pass_files = dict(files)
    secondary_pass_files[secondary_log] = "independent checker accepted the submission\n"
    primary_fail_secondary_pass = clone()
    primary_fail_secondary_pass["checks"]["primary_kernel"]["result"] = "fail"  # type: ignore[index]
    primary_fail_secondary_pass["checks"]["secondary_recheck"].update(  # type: ignore[index,union-attr]
        {
            "relation": "independent-checker",
            "checker": "fixture-independent-checker",
            "version": "1",
            "result": "pass",
            "log_artifact": secondary_log,
            "log_sha256": fixture_sha256(secondary_pass_files[secondary_log]),
        }
    )
    primary_fail_secondary_pass["final_record"][  # type: ignore[index]
        "formal_encoding"
    ] = "recorded-fail"
    primary_fail_recorded_fail_result = execute_formalization_manifest(
        primary_fail_secondary_pass, secondary_pass_files
    )
    primary_fail_conflict = json.loads(json.dumps(primary_fail_secondary_pass))
    primary_fail_conflict["final_record"]["formal_encoding"] = "conflict"  # type: ignore[index]
    primary_fail_conflict_result = execute_formalization_manifest(
        primary_fail_conflict, secondary_pass_files
    )

    cases = (
        ("valid recorded-pass manifest", valid_result, 0),
        ("overlapping trust roots", overlap_result, 1),
        ("changed trusted challenge", changed_challenge_result, 1),
        ("unexpected axiom", unexpected_axiom_result, 1),
        ("target hash mismatch", target_hash_mismatch_result, 1),
        ("unsafe artifact path", unsafe_path_result, 1),
        ("invalid solver write scope", invalid_scope_result, 1),
        ("placeholder toolchain version", placeholder_toolchain_result, 1),
        ("incomplete statement match", incomplete_match_result, 1),
        ("missing mandatory build log", missing_build_log_result, 1),
        ("duplicate JSON key", duplicate_key_result, 1),
        ("tampered artifact", tampered_artifact_result, 1),
        ("unlisted trusted challenge file", unlisted_trusted_file_result, 1),
        ("failed independent secondary recheck", failed_secondary_result, 1),
        ("recorded independent-checker conflict", recorded_conflict_result, 0),
        ("same-kernel failure mislabeled conflict", same_kernel_conflict_result, 1),
        ("same-kernel failure recorded fail", same_kernel_recorded_fail_result, 0),
        ("mandatory failure mislabeled conflict", mandatory_failure_conflict_result, 1),
        (
            "primary failure and independent pass mislabeled recorded fail",
            primary_fail_recorded_fail_result,
            1,
        ),
        (
            "primary failure and independent pass recorded conflict",
            primary_fail_conflict_result,
            0,
        ),
    )
    for label, result, expected in cases:
        if result.returncode != expected:
            errors.append(
                f"formalization manifest {label} fixture expected exit {expected}"
            )
        output = result.stdout + result.stderr
        if "Traceback" in output or "Formalization manifest validation" not in result.stdout:
            errors.append(f"formalization manifest {label} fixture crashed or omitted its summary")
    diagnostics = (
        (overlap_result, "roots must not overlap"),
        (changed_challenge_result, "equal before/after challenge hashes"),
        (unexpected_axiom_result, "outside the allowlist"),
        (
            target_hash_mismatch_result,
            "must match natural_statement.sha256",
        ),
        (unsafe_path_result, "must stay inside the repository"),
        (invalid_scope_result, "solver_write_scope must equal solution-only"),
        (placeholder_toolchain_result, "toolchain.lean_version must not be a template placeholder"),
        (incomplete_match_result, "statement_match.confirmed_by"),
        (missing_build_log_result, "durable artifacts for every mandatory check"),
        (duplicate_key_result, "duplicate JSON key"),
        (tampered_artifact_result, "artifact hash mismatch"),
        (unlisted_trusted_file_result, "trusted_challenge.files"),
        (failed_secondary_result, "failed secondary recheck"),
        (
            same_kernel_conflict_result,
            "conflict requires opposite primary-kernel and independent-checker results",
        ),
        (
            mandatory_failure_conflict_result,
            "a recorded mandatory or same-kernel failure requires formal_encoding recorded-fail",
        ),
        (
            primary_fail_recorded_fail_result,
            "opposite primary-kernel and independent-checker results require formal_encoding conflict",
        ),
    )
    for result, marker in diagnostics:
        if marker not in result.stdout:
            errors.append(
                f"formalization manifest fixture did not emit diagnostic {marker!r}"
            )


def validate_vault_lint_fixtures(errors: list[str]) -> None:
    valid = textwrap.dedent(
        """\
        ---
        type: research-log
        title: "Fixture"
        date: 2026-07-19
        updated: 2026-07-19
        language: en
        project: ""
        kind: proof-audit
        status: complete
        review_status: unchecked
        ---
        Safe fixture.
        """
    )
    invalid_enums = (
        valid.replace("kind: proof-audit", "kind: experiment")
        .replace("status: complete", "status: proved")
        .replace("review_status: unchecked", "review_status: ai-verified")
    )
    invalid_date = valid.replace("date: 2026-07-19", "date: 2026-99-99", 1)
    duplicate_review = valid.replace(
        "review_status: unchecked",
        "review_status: unchecked\nreview_status: human-reviewed",
    )
    valid_run = valid.replace("2026-07-19", "2026-07-24").replace(
        "review_status: unchecked\n---\nSafe fixture.",
        textwrap.dedent(
            """\
            review_status: unchecked
            run_id: Run-20260724-001
            adapter: natural-proof
            adapter_scope: "Direct proof and obstruction search"
            ---
            # Research run
            ## Problem Contract
            - Exact target: Prove the fixture theorem under its stated hypotheses.
            - Success criterion: Supply a complete proof with every dependency identified.
            - Refutation criterion: Supply a counterexample satisfying the hypotheses.
            ## Run manifest
            Fixture.
            ## Bounded branch plan
            Fixture.
            ## Branch ledger
            | Branch | Parent | Obligation | Role | Attempt | State |
            |---|---|---|---|---|---|
            | Branch-001 | root | Obligation-001 | solver | Attempt-001 | candidate-produced |
            ## Execution records
            | Attempt | Branch | Provider, model, and version | Prompt artifact and SHA-256 | Rendered prompt SHA-256 | Context and input bundle with SHA-256 | Originating reasoning supplied | Parent or sibling reasoning supplied | Seed and sampling | Budget and usage | Stop reason | Output artifact and SHA-256 |
            |---|---|---|---|---|---|---|---|---|---|---|---|
            | Attempt-001 | Branch-001 | fixture-provider / fixture-model / 1 | prompts/solver.md SHA256_FIXTURE | SHA256_FIXTURE | fresh-isolated; inputs/fixture.md SHA256_FIXTURE | no | no | not exposed | max 100 tokens / used 50 | candidate-produced | outputs/candidate.md SHA256_FIXTURE |
            ## Automation signals
            | Signal | Exact branch or artifact version | Basis | Closure effect |
            |---|---|---|---|
            | candidate-green | Branch-001 / SHA256_FIXTURE | fixture candidate | none |
            ## Obligations
            | Obligation | Exact subclaim or test | Depends on | What would establish it | What would refute it | State |
            |---|---|---|---|---|---|
            | Obligation-001 | Establish the fixture estimate | | A complete derivation | A valid counterexample | open |
            ## Attempt ledger
            | Attempt | Date | Obligation | Direction | Branch | Context | Method or adapter | Result | Artifact, limits, or failure reason |
            |---|---|---|---|---|---|---|---|---|
            | Attempt-001 | 2026-07-24 | Obligation-001 | prove | Branch-001 | fresh-isolated | direct proof | candidate | outputs/candidate.md; encoding unchecked |
            ## Adapter and evidence records
            | Descriptor | Exact scope | Input, artifact, or source | Result | Assumptions and limitations | Human or tool provenance |
            |---|---|---|---|---|---|
            | | | | | | |
            ## Formalization boundary
            - Formalization manifest: not used
            - Trusted challenge root: not used
            - Untrusted submission root: not used
            - Trust-boundary result: unchecked
            ## Scoped synthesis
            Fixture.
            ## Human promotion
            - Statement-match confirmation: not confirmed
            - Statement-match scope:
            - Statement-match confirmed by (consented identifier or role):
            - Statement-match confirmation date:
            - Closed-by-researcher confirmation: not confirmed
            - Closed-by-researcher scope:
            - Closed-by-researcher confirmed by (consented identifier or role):
            - Closed-by-researcher confirmation date:
            - Researcher decision and qualifications:
            """
        ).rstrip().replace("SHA256_FIXTURE", "sha256:" + "a" * 64),
    )
    # Compact runs keep the same core schema without paying for unused
    # branching/formalization records. These fixtures exercise behavior, not
    # whether a prose guide repeats a particular phrase.
    compact_run = valid_run
    for heading in ("Bounded branch plan", "Branch ledger", "Execution records",
                    "Automation signals", "Formalization boundary"):
        compact_run = re.sub(r"^## " + re.escape(heading) + r"\n.*?(?=^## |\Z)",
                             "", compact_run, flags=re.MULTILINE | re.DOTALL)
    compact_run = compact_run.replace("| Branch-001 | fresh-isolated |", "| none | same-context-audit |")
    audit_run = valid_run.replace("fresh-isolated", "independent-proof-audit").replace(
        "| Obligation-001 | prove |", "| Obligation-001 | check |"
    ).replace("| no | no | not exposed |", "| yes | no | not exposed |")
    legacy_compact_run = compact_run.replace(
        "| Direction | Branch | Context |", "| Direction | Context |"
    ).replace("|---|---|---|---|---|---|---|---|---|", "|---|---|---|---|---|---|---|---|").replace(
        "| prove | none | same-context-audit |", "| prove | same-context-audit |"
    )
    # Use the distributed appendix unchanged: empty extension tables must not
    # turn an unsupported isolation claim into a recorded execution.
    compact_with_empty_extensions = compact_run + "\n\n" + (
        ROOT / "meta/templates/research-run-extensions.md"
    ).read_text(encoding="utf-8")
    compact_statement_match = compact_run.replace(
        "| | | | | | |",
        "| statement-matched | Fixture theorem | proof.txt | matched | exact fixture statement | human |",
    )
    compact_cases = (
        ("legacy compact run without branch column", legacy_compact_run, 0),
        ("legacy compact invalid obligation", legacy_compact_run.replace("| 2026-07-24 | Obligation-001 |", "| 2026-07-24 | Obligation-999 |"), 1),
        ("compact run", compact_run, 0),
        ("compact unknown obligation", compact_run.replace("| 2026-07-24 | Obligation-001 |", "| 2026-07-24 | Obligation-999 |"), 1),
        ("compact invalid context", compact_run.replace("| same-context-audit |", "| ai-verified |"), 1),
        ("compact unrecorded branch", compact_run.replace("| none |", "| Branch-001 |"), 1),
        ("compact unrecorded fresh search", compact_run.replace("| same-context-audit |", "| fresh-isolated |"), 1),
        ("compact unrecorded proof audit", compact_run.replace("| same-context-audit |", "| independent-proof-audit |").replace("| prove |", "| check |"), 1),
        ("compact unrecorded formal review", compact_run.replace("review_status: unchecked", "review_status: formal-tool-checked"), 1),
        ("compact unrecorded formal evidence", compact_run.replace("| | | | | | |", "| formal-encoding-checked | fixture | missing.json | pass | encoding only | tool |"), 1),
        ("compact unrecorded formal adapter", compact_run.replace("adapter: natural-proof", "adapter: formalization"), 1),
        ("independent exact-proof audit", audit_run, 0),
        ("proof audit without candidate", audit_run.replace("| yes | no | not exposed |", "| no | no | not exposed |"), 1),
        ("proof audit wrong direction", audit_run.replace("| Obligation-001 | check |", "| Obligation-001 | prove |"), 1),
        ("compact run with empty extensions", compact_with_empty_extensions, 0),
        ("empty extensions without fresh-search execution", compact_with_empty_extensions.replace("| same-context-audit |", "| fresh-isolated |"), 1),
        ("empty extensions without proof-audit execution", compact_with_empty_extensions.replace("| same-context-audit |", "| independent-proof-audit |").replace("| prove |", "| check |"), 1),
        ("run heading without run metadata", re.sub(r"^(?:run_id|adapter|adapter_scope):.*\n", "", compact_run, flags=re.MULTILINE), 1),
        ("run heading without frontmatter", re.sub(r"\A---\n.*?\n---\n", "", compact_run, count=1, flags=re.DOTALL), 1),
        ("statement match with renamed evidence heading", compact_statement_match.replace("## Adapter and evidence records", "## Evidence"), 1),
        ("statement match with deleted evidence heading", compact_statement_match.replace("## Adapter and evidence records\n", ""), 1),
        ("formal pass without manifest", compact_with_empty_extensions.replace("- Formal-encoding record: unchecked", "- Formal-encoding record: recorded-pass"), 1),
        ("invalid formal-encoding record", compact_with_empty_extensions.replace("- Formal-encoding record: unchecked", "- Formal-encoding record: ai-verified"), 1),
        ("invalid execution mode", compact_with_empty_extensions.replace("- Execution mode: not used", "- Execution mode: autonomous-proof"), 1),
        ("proof audit with parent or sibling reasoning", audit_run.replace("| yes | no | not exposed |", "| yes | yes | not exposed |"), 1),
    )
    for label, content, expected in compact_cases:
        result = execute_vault_lint(note_text=content)
        if result.returncode != expected:
            errors.append(f"vault lint fixture failed: {label}: expected {expected}, got {result.returncode}: {result.stdout}")

    # Bound targets must preserve the canonical wording, even in older compact runs.
    target_ref = "- Spine target reference: Thm-001; notes/source.md; working snapshot Run-20260724-001"
    canonical_target = "Every real symmetric matrix is orthogonally diagonalizable."
    source_fixture = "| ID | Claim | Mathematical state |\n|---|---|---|\n| Thm-001 | " + canonical_target + " | open |\n"
    for target, expected in ((canonical_target, 0), (canonical_target.replace("real symmetric", "positive definite real symmetric"), 1)):
        bound = compact_run.replace("- Exact target: Prove the fixture theorem under its stated hypotheses.",
                                    target_ref + "\n- Exact target: " + target)
        result = execute_vault_lint(note_text=bound, extra_files={"notes/source.md": source_fixture})
        if result.returncode != expected or (expected and "legacy working target" not in result.stdout):
            errors.append("canonical target comparison fixture failed: " + result.stdout)

    invalid_calendar_run = valid_run.replace(
        "run_id: Run-20260724-001", "run_id: Run-20260230-001"
    )
    invalid_adapter_run = valid_run.replace(
        "adapter: natural-proof", "adapter: generic-agent"
    )
    missing_run_id = valid_run.replace("run_id: Run-20260724-001", 'run_id: ""')
    missing_adapter_scope = valid_run.replace(
        'adapter_scope: "Direct proof and obstruction search"',
        'adapter_scope: ""',
    )
    missing_adapter = valid_run.replace("adapter: natural-proof", 'adapter: ""')
    valid_mixed_adapter = valid_run.replace("adapter: natural-proof", "adapter: mixed").replace(
        'adapter_scope: "Direct proof and obstruction search"',
        'adapter_scope: "Natural proof of Obligation-001; literature audit for the named theorem"',
    )
    invalid_mixed_adapter = valid_run.replace("adapter: natural-proof", "adapter: mixed")
    run_frontmatter_date_mismatch = valid_run.replace(
        "date: 2026-07-24", "date: 2026-07-23", 1
    )
    placeholder_contract = valid_run.replace(
        "- Exact target: Prove the fixture theorem under its stated hypotheses.",
        "- Exact target: TODO",
    )
    empty_obligation = valid_run.replace(
        "| Obligation-001 | Establish the fixture estimate | | A complete derivation | A valid counterexample | open |",
        "| Obligation-001 | | | | | open |",
    )
    statement_matched_row = valid_run.replace(
        "| | | | | | |",
        "| statement-matched | Fixture theorem | proof.txt | matched | exact fixture statement | human |",
    )
    confirmed_statement_match = (
        statement_matched_row.replace(
            "- Statement-match confirmation: not confirmed",
            "- Statement-match confirmation: confirmed",
        )
        .replace(
            "- Statement-match scope:",
            "- Statement-match scope: Fixture theorem with the recorded hypotheses",
        )
        .replace(
            "- Statement-match confirmed by (consented identifier or role):",
            "- Statement-match confirmed by (consented identifier or role): project researcher",
        )
        .replace(
            "- Statement-match confirmation date:",
            "- Statement-match confirmation date: 2026-07-24",
        )
    )
    invalid_statement_match_date = confirmed_statement_match.replace(
        "- Statement-match confirmation date: 2026-07-24",
        "- Statement-match confirmation date: 2026-02-30",
    )
    valid_closed_confirmation = (
        valid_run.replace(
            "- Closed-by-researcher confirmation: not confirmed",
            "- Closed-by-researcher confirmation: confirmed",
        )
        .replace(
            "- Closed-by-researcher scope:",
            "- Closed-by-researcher scope: Fixture theorem only",
        )
        .replace(
            "- Closed-by-researcher confirmed by (consented identifier or role):",
            "- Closed-by-researcher confirmed by (consented identifier or role): project researcher",
        )
        .replace(
            "- Closed-by-researcher confirmation date:",
            "- Closed-by-researcher confirmation date: 2026-07-24",
        )
    )
    invalid_closed_confirmation = valid_closed_confirmation.replace(
        "- Closed-by-researcher scope: Fixture theorem only",
        "- Closed-by-researcher scope:",
    )
    missing_confirmation_field = valid_run.replace(
        "- Statement-match confirmation date:\n", ""
    )
    missing_run_heading = valid_run.replace(
        "## Attempt ledger\n"
        "| Attempt | Date | Obligation | Direction | Branch | Context | Method or adapter | Result | Artifact, limits, or failure reason |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
        "| Attempt-001 | 2026-07-24 | Obligation-001 | prove | Branch-001 | fresh-isolated | direct proof | candidate | outputs/candidate.md; encoding unchecked |\n",
        "",
    )
    invalid_branch_role = valid_run.replace(
        "| Branch-001 | root | Obligation-001 | solver | Attempt-001 | candidate-produced |",
        "| Branch-001 | root | Obligation-001 | closer | Attempt-001 | candidate-produced |",
    )
    invalid_fresh_originating_reasoning = valid_run.replace(
        "| no | no | not exposed | max 100 tokens / used 50 |",
        "| yes | no | not exposed | max 100 tokens / used 50 |",
    )
    invalid_fresh_related_reasoning = valid_run.replace(
        "| no | no | not exposed | max 100 tokens / used 50 |",
        "| no | yes | not exposed | max 100 tokens / used 50 |",
    )
    invalid_automation_closure = valid_run.replace(
        "| candidate-green | Branch-001 / " + "sha256:" + "a" * 64 + " | fixture candidate | none |",
        "| candidate-green | Branch-001 / " + "sha256:" + "a" * 64 + " | fixture candidate | proof |",
    )
    valid_model_convergence = valid_run.replace(
        "| candidate-green | Branch-001 / " + "sha256:" + "a" * 64 + " | fixture candidate | none |",
        "| model-convergence | Branch-001 / " + "sha256:" + "a" * 64 + " | scoped fixture agreement | none |",
    )
    valid_two_of_three_agreement = valid_run.replace(
        "| candidate-green | Branch-001 / " + "sha256:" + "a" * 64 + " | fixture candidate | none |",
        "| two-of-three-agreement | Branch-001 / " + "sha256:" + "a" * 64 + " | scoped fixture agreement | none |",
    )
    formal_evidence_without_manifest = valid_run.replace(
        "| | | | | | |",
        "| formal-encoding-checked | Fixture Lean target | missing.json | pass | encoding only | tool |",
    )
    cyclic_branch_genealogy = valid_run.replace(
        "| Branch-001 | root | Obligation-001 | solver | Attempt-001 | candidate-produced |",
        "| Branch-001 | Branch-002 | Obligation-001 | solver | Attempt-001 | candidate-produced |\n"
        "| Branch-002 | Branch-001 | Obligation-001 | adversary | Attempt-002 | failed |",
    )
    cross_ledger_unknown_attempt = valid_run.replace(
        "| Branch-001 | root | Obligation-001 | solver | Attempt-001 | candidate-produced |",
        "| Branch-001 | root | Obligation-001 | solver | Attempt-002 | candidate-produced |",
    )
    cross_ledger_unknown_obligation = valid_run.replace(
        "| Branch-001 | root | Obligation-001 | solver | Attempt-001 | candidate-produced |",
        "| Branch-001 | root | Obligation-002 | solver | Attempt-001 | candidate-produced |",
    )
    cross_ledger_context_mismatch = valid_run.replace(
        "| Attempt-001 | 2026-07-24 | Obligation-001 | prove | Branch-001 | fresh-isolated | direct proof | candidate | outputs/candidate.md; encoding unchecked |",
        "| Attempt-001 | 2026-07-24 | Obligation-001 | prove | Branch-001 | same-context-audit | direct proof | candidate | outputs/candidate.md; encoding unchecked |",
    )
    invalid_rendered_prompt_hash = valid_run.replace(
        " | " + "sha256:" + "a" * 64 + " | fresh-isolated;",
        " | sha256:ABC | fresh-isolated;",
        1,
    )
    formal_manifest, formal_files = valid_formalization_fixture()
    formal_manifest_relative = (
        "projects/fixture/formalization/formalization-manifest.json"
    )
    formal_files[formal_manifest_relative] = json.dumps(formal_manifest, indent=2)
    valid_formal_evidence = formal_evidence_without_manifest.replace(
        "- Formalization manifest: not used",
        f"- Formalization manifest: {formal_manifest_relative}",
    )
    project_spine = textwrap.dedent(
        """\
        ---
        type: project
        title: "Fixture project"
        status: active
        created: 2026-07-22
        updated: 2026-07-22
        language: en
        research_question: "Fixture question"
        ---
        ## Research State Spine
        ### Definition registry
        | ID | Definition or notation | Exact formulation or source | Notes |
        |---|---|---|---|
        | Def-001 | Fixture | | |
        ### Claim ledger
        | ID | Claim | Mathematical state | Depends on | Evidence or source | Review provenance | Integration state | Next action |
        |---|---|---|---|---|---|---|---|
        | Lem-001 | Fixture \\( |x| \\) | conjectural | Def-001 | | unchecked | isolated | |
        ### Open gaps
        | ID | Affects | Precise missing justification or issue | Severity | State | Next action |
        |---|---|---|---|---|---|
        | Gap-001 | Lem-001 | Fixture | local | open | |
        """
    )
    duplicate_project_id = project_spine.replace(
        "### Open gaps",
        "| Lem-001 | Duplicate | conjectural | Def-001 | | unchecked | isolated | |\n### Open gaps",
    )
    malformed_project_id = project_spine.replace("| Lem-001 |", "| L1 |")
    long_form_project_id = project_spine.replace("| Lem-001 |", "| Lemma-001 |")
    invalid_state_axes = project_spine.replace(
        "| conjectural | Def-001 | | unchecked | isolated |",
        "| human-reviewed | Def-001 | | supported | conjectural |",
    )
    missing_spine_heading = project_spine.replace("## Research State Spine\n", "")
    invalid_claim_header = project_spine.replace(
        "| ID | Claim | Mathematical state | Depends on | Evidence or source | Review provenance | Integration state | Next action |",
        "| ID | Claim | State | Evidence or gap | Source log |",
    )
    base_claim_row = (
        "| Lem-001 | Fixture \\( |x| \\) | conjectural | Def-001 | | unchecked | isolated | |"
    )
    acyclic_project = project_spine.replace(
        base_claim_row,
        base_claim_row
        + "\n| Prop-001 | Downstream fixture | supported | Lem-001 | | human-reviewed (fixture) | integrated | |",
    )
    dangling_dependency = project_spine.replace(
        "| conjectural | Def-001 | | unchecked | isolated |",
        "| conjectural | Lem-999 | | unchecked | isolated |",
    )
    self_dependency = project_spine.replace(
        "| conjectural | Def-001 | | unchecked | isolated |",
        "| conjectural | Lem-001 | | unchecked | isolated |",
    )
    cyclic_dependencies = project_spine.replace(
        base_claim_row,
        "| Lem-001 | First fixture | conjectural | Prop-001 | | unchecked | isolated | |\n"
        "| Prop-001 | Second fixture | conjectural | Lem-001 | | unchecked | isolated | |",
    )
    stale_dependency = project_spine.replace(
        base_claim_row,
        "| Lem-001 | Upstream fixture | supported | Def-001 | | human-reviewed (fixture) | review-stale | |\n"
        "| Prop-001 | Downstream fixture | supported | Lem-001 | | human-reviewed (fixture) | integrated | |",
    )
    transitive_stale_dependency = project_spine.replace(
        base_claim_row,
        "| Lem-001 | Upstream fixture | supported | Def-001 | source | human-reviewed (fixture, 2026-07-24) | review-stale | |\n"
        "| Prop-001 | Middle fixture | supported | Lem-001 | source | human-reviewed (fixture, 2026-07-24) | integrated | |\n"
        "| Thm-001 | Downstream fixture | supported | Prop-001 | source | human-reviewed (fixture, 2026-07-24) | integrated | |",
    )
    valid_closed_claim = project_spine.replace(
        base_claim_row,
        "| Lem-001 | Fixture claim | closed-by-researcher | Def-001 | proof-log.md | human-reviewed (project researcher, 2026-07-24) | integrated | |",
    )
    closed_claim_missing_evidence = valid_closed_claim.replace(
        "| proof-log.md | human-reviewed", "| | human-reviewed"
    )
    closed_claim_undated_review = valid_closed_claim.replace(
        "human-reviewed (project researcher, 2026-07-24)",
        "human-reviewed (project researcher)",
    )
    freeform_dependency = project_spine.replace(
        "| conjectural | Def-001 | | unchecked | isolated |",
        "| conjectural | a classical lemma | | unchecked | isolated |",
    )
    legacy_project = project_spine.replace(
        "## Research State Spine\n### Definition registry\n| ID | Definition or notation | Exact formulation or source | Notes |\n|---|---|---|---|\n| Def-001 | Fixture | | |\n### Claim ledger\n| ID | Claim | Mathematical state | Depends on | Evidence or source | Review provenance | Integration state | Next action |\n|---|---|---|---|---|---|---|---|\n| Lem-001 | Fixture \\( |x| \\) | conjectural | Def-001 | | unchecked | isolated | |\n### Open gaps\n| ID | Affects | Precise missing justification or issue | Severity | State | Next action |\n|---|---|---|---|---|---|\n| Gap-001 | Lem-001 | Fixture | local | open | |",
        "## Claim ledger\n| ID | Claim | State | Evidence or gap | Source log |\n|---|---|---|---|---|\n| C1 | Fixture | conjectural | | |",
    )
    legacy_project_result = execute_vault_lint(
        note_text=legacy_project,
        note_relative="projects/fixture/README.md",
    )
    valid_run_result = execute_vault_lint(note_text=valid_run)
    invalid_calendar_run_result = execute_vault_lint(note_text=invalid_calendar_run)
    invalid_adapter_run_result = execute_vault_lint(note_text=invalid_adapter_run)
    missing_run_id_result = execute_vault_lint(note_text=missing_run_id)
    missing_adapter_scope_result = execute_vault_lint(note_text=missing_adapter_scope)
    missing_adapter_result = execute_vault_lint(note_text=missing_adapter)
    invalid_mixed_adapter_result = execute_vault_lint(note_text=invalid_mixed_adapter)
    run_frontmatter_date_mismatch_result = execute_vault_lint(
        note_text=run_frontmatter_date_mismatch
    )
    run_filename_date_mismatch_result = execute_vault_lint(
        note_text=valid_run,
        note_relative="notes/2026-07-23-fixture.md",
    )
    placeholder_contract_result = execute_vault_lint(note_text=placeholder_contract)
    empty_obligation_result = execute_vault_lint(note_text=empty_obligation)
    unconfirmed_statement_match_result = execute_vault_lint(
        note_text=statement_matched_row
    )
    invalid_statement_match_date_result = execute_vault_lint(
        note_text=invalid_statement_match_date
    )
    invalid_closed_confirmation_result = execute_vault_lint(
        note_text=invalid_closed_confirmation
    )
    missing_confirmation_field_result = execute_vault_lint(
        note_text=missing_confirmation_field
    )
    missing_run_heading_result = execute_vault_lint(note_text=missing_run_heading)
    invalid_branch_role_result = execute_vault_lint(note_text=invalid_branch_role)
    invalid_fresh_originating_reasoning_result = execute_vault_lint(
        note_text=invalid_fresh_originating_reasoning
    )
    invalid_fresh_related_reasoning_result = execute_vault_lint(
        note_text=invalid_fresh_related_reasoning
    )
    invalid_automation_closure_result = execute_vault_lint(
        note_text=invalid_automation_closure
    )
    valid_model_convergence_result = execute_vault_lint(
        note_text=valid_model_convergence
    )
    valid_two_of_three_agreement_result = execute_vault_lint(
        note_text=valid_two_of_three_agreement
    )
    formal_evidence_without_manifest_result = execute_vault_lint(
        note_text=formal_evidence_without_manifest
    )
    cyclic_branch_genealogy_result = execute_vault_lint(
        note_text=cyclic_branch_genealogy
    )
    cross_ledger_unknown_attempt_result = execute_vault_lint(
        note_text=cross_ledger_unknown_attempt
    )
    cross_ledger_unknown_obligation_result = execute_vault_lint(
        note_text=cross_ledger_unknown_obligation
    )
    cross_ledger_context_mismatch_result = execute_vault_lint(
        note_text=cross_ledger_context_mismatch
    )
    invalid_rendered_prompt_hash_result = execute_vault_lint(
        note_text=invalid_rendered_prompt_hash
    )
    valid_formal_evidence_result = execute_vault_lint(
        note_text=valid_formal_evidence,
        extra_files=formal_files,
    )
    duplicate_project_run_id_result = execute_vault_lint(
        note_texts={
            "projects/fixture/logs/run-a.md": valid_run.replace(
                'project: ""', 'project: "[[projects/fixture/README]]"'
            ),
            "projects/fixture/logs/run-b.md": valid_run.replace(
                'project: ""', 'project: "[[projects/fixture/README]]"'
            ),
        }
    )
    cross_project_run_id_result = execute_vault_lint(
        note_texts={
            "projects/first/logs/run-a.md": valid_run.replace(
                'project: ""', 'project: "[[projects/first/README]]"'
            ),
            "projects/second/logs/run-b.md": valid_run.replace(
                'project: ""', 'project: "[[projects/second/README]]"'
            ),
        }
    )
    dangling_dependency_result = execute_vault_lint(
        note_text=dangling_dependency,
        note_relative="projects/fixture/README.md",
    )
    self_dependency_result = execute_vault_lint(
        note_text=self_dependency,
        note_relative="projects/fixture/README.md",
    )
    cyclic_dependencies_result = execute_vault_lint(
        note_text=cyclic_dependencies,
        note_relative="projects/fixture/README.md",
    )
    stale_dependency_result = execute_vault_lint(
        note_text=stale_dependency,
        note_relative="projects/fixture/README.md",
    )
    transitive_stale_dependency_result = execute_vault_lint(
        note_text=transitive_stale_dependency,
        note_relative="projects/fixture/README.md",
    )
    closed_claim_missing_evidence_result = execute_vault_lint(
        note_text=closed_claim_missing_evidence,
        note_relative="projects/fixture/README.md",
    )
    closed_claim_undated_review_result = execute_vault_lint(
        note_text=closed_claim_undated_review,
        note_relative="projects/fixture/README.md",
    )
    freeform_dependency_result = execute_vault_lint(
        note_text=freeform_dependency,
        note_relative="projects/fixture/README.md",
    )
    cases = (
        ("valid research log", execute_vault_lint(note_text=valid), 0),
        ("valid research run", valid_run_result, 0),
        ("invalid research-run calendar date", invalid_calendar_run_result, 1),
        ("invalid research-run adapter", invalid_adapter_run_result, 1),
        ("research run missing run ID", missing_run_id_result, 1),
        ("research run missing adapter scope", missing_adapter_scope_result, 1),
        ("research run missing adapter", missing_adapter_result, 1),
        ("valid mixed research-run adapter", execute_vault_lint(note_text=valid_mixed_adapter), 0),
        ("invalid mixed research-run adapter", invalid_mixed_adapter_result, 1),
        ("research-run frontmatter date mismatch", run_frontmatter_date_mismatch_result, 1),
        ("research-run filename date mismatch", run_filename_date_mismatch_result, 1),
        ("research-run placeholder contract", placeholder_contract_result, 1),
        ("research-run early SPEC empty obligation", empty_obligation_result, 0),
        ("valid statement-match confirmation", execute_vault_lint(note_text=confirmed_statement_match), 0),
        ("unconfirmed statement-matched evidence", unconfirmed_statement_match_result, 1),
        ("invalid statement-match date", invalid_statement_match_date_result, 1),
        ("valid closed confirmation", execute_vault_lint(note_text=valid_closed_confirmation), 0),
        ("invalid closed confirmation", invalid_closed_confirmation_result, 1),
        ("missing exact confirmation field", missing_confirmation_field_result, 1),
        ("duplicate project-local research-run ID", duplicate_project_run_id_result, 1),
        ("same research-run ID across projects", cross_project_run_id_result, 0),
        (
            "research run missing required heading",
            missing_run_heading_result,
            1,
        ),
        ("research-run invalid branch role", invalid_branch_role_result, 1),
        (
            "research-run originating reasoning in fresh context",
            invalid_fresh_originating_reasoning_result,
            1,
        ),
        (
            "research-run related reasoning in fresh context",
            invalid_fresh_related_reasoning_result,
            1,
        ),
        (
            "research-run automation closure",
            invalid_automation_closure_result,
            1,
        ),
        ("research-run model convergence signal", valid_model_convergence_result, 0),
        (
            "research-run two-of-three signal",
            valid_two_of_three_agreement_result,
            0,
        ),
        (
            "formal evidence without manifest",
            formal_evidence_without_manifest_result,
            1,
        ),
        ("cyclic branch genealogy", cyclic_branch_genealogy_result, 1),
        ("branch references unknown attempt", cross_ledger_unknown_attempt_result, 1),
        (
            "branch references unknown obligation",
            cross_ledger_unknown_obligation_result,
            1,
        ),
        ("attempt/execution context mismatch", cross_ledger_context_mismatch_result, 1),
        (
            "invalid rendered prompt hash",
            invalid_rendered_prompt_hash_result,
            1,
        ),
        ("valid formal evidence manifest", valid_formal_evidence_result, 0),
        ("invalid research-log enums", execute_vault_lint(note_text=invalid_enums), 1),
        ("impossible research date", execute_vault_lint(note_text=invalid_date), 1),
        ("duplicate frontmatter key", execute_vault_lint(note_text=duplicate_review), 1),
        (
            "valid project Research State Spine",
            execute_vault_lint(
                note_text=project_spine,
                note_relative="projects/fixture/README.md",
            ),
            0,
        ),
        (
            "acyclic claim dependencies",
            execute_vault_lint(
                note_text=acyclic_project,
                note_relative="projects/fixture/README.md",
            ),
            0,
        ),
        (
            "dangling claim dependency",
            dangling_dependency_result,
            1,
        ),
        (
            "self claim dependency",
            self_dependency_result,
            1,
        ),
        (
            "two-node claim dependency cycle",
            cyclic_dependencies_result,
            1,
        ),
        ("stale dependency propagation", stale_dependency_result, 0),
        ("transitive stale dependency propagation", transitive_stale_dependency_result, 0),
        (
            "valid closed-by-researcher claim",
            execute_vault_lint(
                note_text=valid_closed_claim,
                note_relative="projects/fixture/README.md",
            ),
            0,
        ),
        ("closed claim missing evidence", closed_claim_missing_evidence_result, 1),
        ("closed claim undated review", closed_claim_undated_review_result, 1),
        ("free-form dependency warning", freeform_dependency_result, 0),
        (
            "duplicate stable project ID",
            execute_vault_lint(
                note_text=duplicate_project_id,
                note_relative="projects/fixture/README.md",
            ),
            1,
        ),
        (
            "abbreviated project ID",
            execute_vault_lint(
                note_text=malformed_project_id,
                note_relative="projects/fixture/README.md",
            ),
            1,
        ),
        (
            "long-form project ID",
            execute_vault_lint(
                note_text=long_form_project_id,
                note_relative="projects/fixture/README.md",
            ),
            1,
        ),
        (
            "swapped Research State Spine axes",
            execute_vault_lint(
                note_text=invalid_state_axes,
                note_relative="projects/fixture/README.md",
            ),
            1,
        ),
        (
            "missing Research State Spine heading",
            execute_vault_lint(
                note_text=missing_spine_heading,
                note_relative="projects/fixture/README.md",
            ),
            1,
        ),
        (
            "invalid Research State Spine claim header",
            execute_vault_lint(
                note_text=invalid_claim_header,
                note_relative="projects/fixture/README.md",
            ),
            1,
        ),
        (
            "legacy project ledger",
            legacy_project_result,
            0,
        ),
        ("ignored binary suffix", execute_vault_lint(binary_name="private-data.xlsx"), 1),
        ("ignored archive suffix", execute_vault_lint(binary_name="private-data.tgz"), 1),
    )
    for label, result, expected_exit in cases:
        if result.returncode != expected_exit:
            errors.append(f"vault-lint {label} fixture expected exit {expected_exit}")
        combined_output = result.stdout + result.stderr
        if "Traceback" in combined_output or "Checked " not in result.stdout:
            errors.append(f"vault-lint {label} fixture crashed or omitted its summary")
        if expected_exit == 1 and "ERROR:" not in result.stdout:
            errors.append(f"vault-lint {label} fixture failed without the expected diagnostic")
    if "WARN: legacy project claim ledger" not in legacy_project_result.stdout:
        errors.append("vault-lint legacy project fixture did not offer optional migration")
    if "ERROR: invalid calendar date in research run_id 'Run-20260230-001'" not in invalid_calendar_run_result.stdout:
        errors.append("vault-lint did not exercise the invalid calendar date branch")
    if "ERROR: invalid research-run adapter" not in invalid_adapter_run_result.stdout:
        errors.append("vault-lint did not reject an invalid research-run adapter")
    if "ERROR: research run_id is required" not in missing_run_id_result.stdout:
        errors.append("vault-lint did not require a research-run ID")
    if (
        "ERROR: research-run adapter_scope is required"
        not in missing_adapter_scope_result.stdout
    ):
        errors.append("vault-lint did not require a scope for a selected adapter")
    if "ERROR: research-run adapter is required" not in missing_adapter_result.stdout:
        errors.append("vault-lint did not require an adapter for a supplied scope")
    if "ERROR: mixed research-run adapter_scope requires at least two semicolon-separated bounded scopes" not in invalid_mixed_adapter_result.stdout:
        errors.append("vault-lint did not enforce bounded mixed-adapter scopes")
    if "does not match frontmatter date" not in run_frontmatter_date_mismatch_result.stdout:
        errors.append("vault-lint did not match the run ID date to frontmatter")
    if "does not match dated filename prefix" not in run_filename_date_mismatch_result.stdout:
        errors.append("vault-lint did not match the run ID date to a dated filename")
    if "Problem Contract 'Exact target' requires a non-placeholder value" not in placeholder_contract_result.stdout:
        errors.append("vault-lint did not require a meaningful Problem Contract")
    if "WARN: research run has no substantive Obligation-NNN row yet" not in empty_obligation_result.stdout:
        errors.append("vault-lint did not flag an empty early-SPEC obligation ledger")
    if "ERROR: statement-matched evidence requires a non-default human statement-match confirmation" not in unconfirmed_statement_match_result.stdout:
        errors.append("vault-lint allowed statement-matched evidence without human confirmation")
    if "requires a real ISO date" not in invalid_statement_match_date_result.stdout:
        errors.append("vault-lint did not reject an impossible statement-match date")
    if "ERROR: research run closed-by-researcher confirmation requires non-placeholder scope" not in invalid_closed_confirmation_result.stdout:
        errors.append("vault-lint did not require complete closed-by-researcher confirmation")
    if "Human promotion missing exact field(s) 'Statement-match confirmation date'" not in missing_confirmation_field_result.stdout:
        errors.append("vault-lint did not require the exact Human promotion fields")
    if "ERROR: duplicate research run_id 'Run-20260724-001' within project" not in duplicate_project_run_id_result.stdout:
        errors.append("vault-lint did not reject a project-local duplicate run ID")
    if "ERROR: research run missing '## Attempt ledger'" not in missing_run_heading_result.stdout:
        errors.append("vault-lint did not reject a missing research-run heading")
    if "has invalid role 'closer'" not in invalid_branch_role_result.stdout:
        errors.append("vault-lint did not reject an unknown branch role")
    if "must not receive originating reasoning" not in invalid_fresh_originating_reasoning_result.stdout:
        errors.append("vault-lint did not enforce fresh-context originating-reasoning isolation")
    if "must not receive parent or sibling reasoning" not in invalid_fresh_related_reasoning_result.stdout:
        errors.append("vault-lint did not enforce fresh-context related-reasoning isolation")
    if "must have Closure effect 'none'" not in invalid_automation_closure_result.stdout:
        errors.append("vault-lint allowed an automation signal to close mathematics")
    if "formal review or evidence requires a validated formalization manifest" not in formal_evidence_without_manifest_result.stdout:
        errors.append("vault-lint allowed formal evidence without a manifest")
    if "cyclic research-run branch genealogy" not in cyclic_branch_genealogy_result.stdout:
        errors.append("vault-lint did not reject a cyclic branch genealogy")
    if "references unknown attempt 'Attempt-002'" not in cross_ledger_unknown_attempt_result.stdout:
        errors.append("vault-lint did not enforce branch-to-attempt ledger integrity")
    if "references unknown obligation 'Obligation-002'" not in cross_ledger_unknown_obligation_result.stdout:
        errors.append("vault-lint did not enforce branch-to-obligation ledger integrity")
    if "does not match Attempt ledger context" not in cross_ledger_context_mismatch_result.stdout:
        errors.append("vault-lint did not enforce attempt-to-execution context integrity")
    if "requires an exact rendered prompt SHA-256" not in invalid_rendered_prompt_hash_result.stdout:
        errors.append("vault-lint did not reject an invalid rendered prompt hash")
    if "ERROR: unknown dependency 'Lem-999' for Lem-001" not in dangling_dependency_result.stdout:
        errors.append("vault-lint did not reject a dangling claim dependency")
    if "ERROR: self dependency for Lem-001" not in self_dependency_result.stdout:
        errors.append("vault-lint did not reject a self claim dependency")
    if "ERROR: cyclic claim dependencies Lem-001 -> Prop-001 -> Lem-001" not in cyclic_dependencies_result.stdout:
        errors.append("vault-lint did not reject a two-node claim dependency cycle")
    if (
        "WARN: integrated Prop-001 depends on stale, retired, gap-found, or refuted Lem-001"
        not in stale_dependency_result.stdout
    ):
        errors.append("vault-lint did not warn about a stale integrated dependency")
    if (
        "WARN: integrated Thm-001 transitively depends on stale, retired, gap-found, or refuted Lem-001 via Prop-001 -> Lem-001"
        not in transitive_stale_dependency_result.stdout
    ):
        errors.append("vault-lint did not propagate a stale dependency transitively")
    for result in (closed_claim_missing_evidence_result, closed_claim_undated_review_result):
        if (
            "ERROR: closed-by-researcher Lem-001 requires nonempty evidence or source and dated human-reviewed or human-and-formal provenance"
            not in result.stdout
            or "not reviewer identity" not in result.stdout
        ):
            errors.append("vault-lint did not enforce the structural closed-by-researcher gate")
            break
    if "WARN: legacy or free-form dependency for Lem-001" not in freeform_dependency_result.stdout:
        errors.append("vault-lint did not warn about a free-form dependency")


def validate_math_project_harness(errors: list[str]) -> None:
    project_template = read_text(ROOT / "meta/templates/project.md") or ""
    exact_claim_header = (
        "| ID | Claim | Mathematical state | Depends on | Evidence or source | "
        "Review provenance | Integration state | Next action |"
    )
    required_project_markers = (
        "## Research State Spine",
        "### Current research state",
        "### Definition registry",
        "### Claim ledger",
        "### Open gaps",
        exact_claim_header,
        "Def-001",
        "Lem-001",
        "Prop-001",
        "Thm-001",
        "Cor-001",
        "Gap-001",
        "Mathematical state",
        "Review provenance",
        "Integration state",
        "review-stale",
        "closed-by-researcher",
    )
    missing_project_markers = [
        marker for marker in required_project_markers if marker not in project_template
    ]
    if missing_project_markers:
        errors.append("project template is missing the Research State Spine contract")
    if (
        "| ID | Claim | State | Evidence or gap | Source log |" in project_template
        or re.search(r"^\|\s*C1\s*\|", project_template, re.MULTILINE)
    ):
        errors.append("project template still contains the legacy mixed-state claim ledger")

    proof_audit = read_text(ROOT / "meta/templates/proof-audit.md") or ""
    required_audit_markers = (
        "## Audit scope",
        "Stable claim ID",
        "Def-001",
        "Lem-001",
        "Gap-001",
        "## Formal check record",
        "## AI-assisted review record",
        "## Human review record",
        "## Scoped conclusion",
    )
    if any(marker not in proof_audit for marker in required_audit_markers):
        errors.append("proof-audit template is not aligned with stable research IDs")
    if re.search(r"^\|\s*G1\s*\|", proof_audit, re.MULTILINE):
        errors.append("proof-audit template still contains the legacy G1 identifier")

    research_run = read_text(ROOT / "meta/templates/research-run.md") or ""
    research_extensions = read_text(ROOT / "meta/templates/research-run-extensions.md") or ""
    math_core = read_text(ROOT / "meta/math-workflow.md") or ""
    math_details = read_text(ROOT / "meta/math-details.md") or ""
    if "meta/templates/research-run-extensions.md" not in research_run:
        errors.append("compact run does not route to its optional execution contract")
    research_run += "\n" + research_extensions
    required_run_markers = (
        "type: research-log",
        'run_id: ""',
        'adapter: ""',
        'adapter_scope: ""',
        "# Research run",
        "## Problem Contract",
        "Spine target reference:",
        "working snapshot Run-YYYYMMDD-NNN",
        "content anchor",
        "never invent a separate Spine version number",
        "AI-authored formulation",
        "merely proposed upstream change",
        "exact artifact version",
        "## Run manifest",
        "## Bounded branch plan",
        "## Branch ledger",
        "## Execution records",
        "## Automation signals",
        "## Obligations",
        "## Attempt ledger",
        "## Formalization boundary",
        "## Scoped synthesis",
        "## Human promotion",
        "meta/templates/research-branch-prompt.md",
        "SPEC → ROUTE → OBLIGATIONS → PROVE / DISPROVE → optional adapters → SYNTHESIZE → HUMAN PROMOTION",
    )
    if any(marker not in research_run for marker in required_run_markers):
        errors.append("research-run template is missing its bounded control-plane contract")

    research_run_skill = read_text(
        ROOT / ".agents/skills/math-research-run/SKILL.md"
    ) or ""
    if "meta/math-workflow.md" not in research_run_skill or "meta/math-details.md" not in research_run_skill:
        errors.append("math research skill does not route to its core and optional guides")
    research_run_skill += "\n" + math_core + "\n" + math_details
    required_run_skill_markers = (
        "Problem Contract",
        "Spine target reference",
        "current `HEAD`",
        "working snapshot Run-YYYYMMDD-NNN",
        "content anchor",
        "Never invent a separate Spine",
        "new AI-authored formulation",
        "proposed upstream change",
        "exact artifact version",
        "Attempt ledger",
        "Branch-NNN",
        "idea-generator",
        "statement-matcher",
        "synthesizer",
        "solution-only",
        "formalization_manifest.py",
        "research-branch-prompt.md",
        "Human promotion",
    )
    if any(
        re.search(re.escape(marker), research_run_skill, re.IGNORECASE) is None
        for marker in required_run_skill_markers
    ):
        errors.append("math-research-run skill is missing its core run boundaries")

    branch_prompt = read_text(
        ROOT / "meta/templates/research-branch-prompt.md"
    ) or ""
    required_prompt_markers = (
        "## Execution identity",
        "## Allowed input bundle",
        "## Context declaration",
        "## Budget and stop policy",
        "## Role contract",
        "## Required return",
        "idea-generator",
        "solver",
        "adversary",
        "repairer",
        "formalizer",
        "statement-matcher",
        "synthesizer",
        "Rendered",
        "Human Promotion",
    )
    if any(
        re.search(re.escape(marker), branch_prompt, re.IGNORECASE) is None
        for marker in required_prompt_markers
    ):
        errors.append("research branch prompt template is missing its bounded role contract")

    schemas = read_text(ROOT / "meta/schemas.md") or ""
    required_run_schema_markers = (
        "run_id",
        "Run-YYYYMMDD-NNN",
        "natural-proof",
        "formalization",
        "constructive-search",
        "literature-audit",
        "mixed",
        "Spine target",
        "current `HEAD`",
        "working snapshot",
        "content anchor",
        "never invent a separate Spine",
        "AI-authored formulation",
        "merely proposed upstream change",
        "exact artifact version",
        "bounded-branch-loop",
        "candidate-produced",
        "closure effect",
        "formalization-manifest.json",
    )
    if any(marker not in schemas for marker in required_run_schema_markers):
        errors.append("research-run schema is missing an optional metadata contract")

    math_workflow = math_core + "\n" + math_details
    required_run_workflow_markers = (
        "Spine target reference",
        "current `HEAD`",
        "working snapshot",
        "content anchor",
        "never invent a separate Spine version number",
        "new AI-authored formulation",
        "merely proposed upstream change",
        "exact artifact version",
        "bounded proof-search harness",
        "Branch-NNN",
        "candidate-green",
        "trusted challenge",
        "untrusted submission",
        "formalization_manifest.py",
    )
    if any(marker not in math_workflow for marker in required_run_workflow_markers):
        errors.append("math workflow is missing the research-run authority contract")

    formalization_template_path = ROOT / "meta/templates/formalization-manifest.json"
    try:
        formalization_template = json.loads(
            formalization_template_path.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError):
        formalization_template = {}
        errors.append("formalization manifest template is not valid JSON")
    required_manifest_keys = {
        "schema_version",
        "manifest_id",
        "run_id",
        "obligation_id",
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
    if (
        not isinstance(formalization_template, dict)
        or formalization_template.get("schema_version") != 1
        or not required_manifest_keys <= formalization_template.keys()
        or formalization_template.get("untrusted_submission", {}).get(
            "solver_write_scope"
        )
        != "solution-only"
    ):
        errors.append("formalization manifest template is missing its trust-boundary contract")

    formalization_validator = read_text(
        ROOT / "scripts/formalization_manifest.py"
    ) or ""
    required_validator_markers = (
        "duplicate JSON key",
        "trusted challenge and untrusted submission roots must not overlap",
        "observed axiom(s) are outside the allowlist",
        "formal_encoding recorded-pass requires",
        "artifact hash mismatch",
        "does not execute or attest recorded commands",
    )
    if any(marker not in formalization_validator for marker in required_validator_markers):
        errors.append("formalization manifest validator is missing a required trust-boundary check")

    legacy_statement_version = re.compile(
        r"\b(?:record|include|cite|provide|require)\b[^.\n]{0,160}"
        r"\bstatement version\b",
        re.IGNORECASE,
    )
    for label, content in (
        ("research-run template", research_run),
        ("math-research-run skill", research_run_skill),
        ("research-run schema", schemas),
        ("math workflow", math_workflow),
    ):
        if legacy_statement_version.search(content):
            errors.append(f"{label} still requires an undefined statement version")

    documentation_contracts = {
        "AGENTS.md": ("Research State Spine", "Def-NNN", "Cor-NNN", "Gap-NNN", "review-stale"),
        ".agents/skills/first-run/SKILL.md": (
            "Research State Spine",
            "Def-NNN",
            "Cor-NNN",
            "Gap-NNN",
            "does not need to edit tables manually",
        ),
        "README.md": ("Research State Spine", "Def-NNN", "Cor-NNN", "Gap-NNN"),
        "README.ko.md": ("Research State Spine", "Def-NNN", "Cor-NNN", "Gap-NNN"),
        "docs/daily-workflow.md": ("Research State Spine", "Def-NNN", "Cor-NNN", "Gap-NNN"),
        "docs/daily-workflow.ko.md": ("Research State Spine", "Def-NNN", "Cor-NNN", "Gap-NNN"),
        "docs/updating.md": ("Research State Spine", "does not automatically rewrite", "Cor-NNN"),
        "docs/updating.ko.md": ("Research State Spine", "자동으로 다시 작성되지 않습니다", "Cor-NNN"),
    }
    for relative, markers in documentation_contracts.items():
        text = read_text(ROOT / relative) or ""
        if any(marker not in text for marker in markers):
            errors.append(f"math project harness guidance is incomplete in {relative}")


def main() -> int:
    if sys.argv[1:] not in ([], ["--release"], ["--release-artifact"]):
        print("Usage: validate-release.py [--release|--release-artifact]")
        return 2
    strict_release = sys.argv[1:] in (["--release"], ["--release-artifact"])
    artifact_release = sys.argv[1:] == ["--release-artifact"]
    errors: list[str] = []
    try:
        files = public_files()
    except OSError:
        print("ERROR: public file tree could not be traversed safely")
        return 1
    relative_files = {path.relative_to(ROOT).as_posix() for path in files}

    if artifact_release and os.path.lexists(ROOT / ".git"):
        errors.append("release artifact must not contain .git metadata")
    if artifact_release and any(
        ".git" in Path(relative).parts for relative in relative_files
    ):
        errors.append("release artifact must not contain nested .git metadata")

    for missing in sorted(REQUIRED - relative_files):
        errors.append(f"missing required file: {missing}")
    if strict_release:
        for unexpected in sorted(relative_files - RELEASE_ALLOWLIST):
            errors.append(f"unexpected file in public release: {unexpected}")

    for forbidden in (".claude", ".codex"):
        if os.path.lexists(ROOT / forbidden):
            errors.append(f"forbidden public path exists: {forbidden}")
    if strict_release and os.path.lexists(ROOT / ".obsidian/plugins"):
        errors.append("forbidden public path exists: .obsidian/plugins")
    harness_dir = ROOT / ".harness"
    if strict_release and not is_link_like(harness_dir) and harness_dir.is_dir():
        try:
            has_local_state = any(
                entry.name.startswith("local") for entry in os.scandir(harness_dir)
            )
        except OSError:
            has_local_state = True
        if has_local_state:
            errors.append("forbidden public path exists: .harness/local*")

    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if is_link_like(path):
            errors.append(f"link or junction is not allowed in release: {relative}")
            continue
        try:
            size = path.stat().st_size
        except OSError:
            errors.append(f"file metadata could not be read safely: {relative}")
            continue
        if size > 1_000_000:
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
        validate_auth_commands(relative, text, errors)
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

    for skill_name in (
        "first-run",
        "claude-review",
        "math-research-run",
        "pro-context-bundle",
        "research-issues",
    ):
        skill = ROOT / f".agents/skills/{skill_name}/SKILL.md"
        if skill.exists():
            skill_text = skill.read_text(encoding="utf-8")
            if (
                not skill_text.startswith("---\n")
                or f"\nname: {skill_name}\n" not in skill_text
                or "\ndescription:" not in skill_text
            ):
                errors.append(f"{skill_name} SKILL.md has invalid required frontmatter")

    claude_review_skill = ROOT / ".agents/skills/claude-review/SKILL.md"
    if claude_review_skill.exists():
        review_text = claude_review_skill.read_text(encoding="utf-8")
        review_text += "\n" + (read_text(ROOT / ".agents/skills/claude-review/references/execution.md") or "")
        required_review_boundaries = (
            "--model opus",
            "--effort xhigh",
            "--safe-mode",
            '--settings \'{"disableAllHooks":true}\'',
            '--tools ""',
            '--disallowedTools "*"',
            "--disable-slash-commands",
            "--permission-mode dontAsk",
            "--no-chrome",
            "--strict-mcp-config",
            "--mcp-config",
            "--setting-sources",
            "--output-format stream-json",
            "scripts/review-output.py",
            "--no-session-persistence",
            "Do not pass `--max-turns`",
            "without a fixed time limit",
            "BEGIN APPROVED REVIEW PACKET",
            "END APPROVED REVIEW PACKET",
        )
        missing_boundaries = [
            boundary for boundary in required_review_boundaries if boundary not in review_text
        ]
        if missing_boundaries:
            errors.append("Claude review skill is missing required one-shot isolation boundaries")

    claude_review_ui = ROOT / ".agents/skills/claude-review/agents/openai.yaml"
    if claude_review_ui.exists():
        ui_text = claude_review_ui.read_text(encoding="utf-8")
        if "allow_implicit_invocation: false" not in ui_text:
            errors.append("Claude review skill must disable implicit invocation")

    math_run_ui = ROOT / ".agents/skills/math-research-run/agents/openai.yaml"
    if math_run_ui.exists():
        ui_text = math_run_ui.read_text(encoding="utf-8")
        if "policy:\n  allow_implicit_invocation: true" not in ui_text:
            errors.append("math research-run skill must allow implicit invocation")

    pro_skill = ROOT / ".agents/skills/pro-context-bundle/SKILL.md"
    if pro_skill.exists():
        pro_text = pro_skill.read_text(encoding="utf-8")
        required_pro_boundaries = (
            "fresh approval",
            "Do not put absolute local paths in an outbound bundle.",
            "without an overall time limit",
            "Never click `Answer now` automatically",
            "Click `Answer now` only when the user explicitly requests",
        )
        missing_boundaries = [
            boundary for boundary in required_pro_boundaries if boundary not in pro_text
        ]
        if missing_boundaries:
            errors.append("Pro context skill is missing required approval or wait boundaries")

    pro_builder = ROOT / ".agents/skills/pro-context-bundle/scripts/build_pro_bundle.py"
    if pro_builder.exists():
        builder_text = pro_builder.read_text(encoding="utf-8")
        required_builder_boundaries = (
            "TEXT_SUFFIXES",
            "SENSITIVE_SKIP_SUFFIXES",
            "Skipping an input outside the workbench root.",
            "Additional instruction files must stay inside the workbench root.",
            "# ChatGPT Pro Handoff Bundle",
        )
        if any(boundary not in builder_text for boundary in required_builder_boundaries):
            errors.append("Pro context builder is missing required privacy boundaries")
        if "- absolute_path:" in builder_text:
            errors.append("Pro context builder must not put absolute paths in outbound bundles")

    pro_ui = ROOT / ".agents/skills/pro-context-bundle/agents/openai.yaml"
    if pro_ui.exists():
        ui_text = pro_ui.read_text(encoding="utf-8")
        if "allow_implicit_invocation: false" not in ui_text:
            errors.append("Pro context skill must disable implicit invocation")

    example_config = ROOT / ".harness/config.example.yaml"
    if example_config.exists():
        config_text = example_config.read_text(encoding="utf-8")
        blank_choices = re.findall(r'^  choice:\s*""\s*$', config_text, re.MULTILINE)
        all_choices = re.findall(r"^  choice:\s*.*$", config_text, re.MULTILINE)
        section_children: dict[str, list[str]] = {}
        current_section = ""
        for line in config_text.splitlines():
            section_match = re.fullmatch(r"([a-z_][a-z0-9_]*):\s*", line)
            if section_match:
                current_section = section_match.group(1)
                section_children.setdefault(current_section, [])
                continue
            child_match = re.match(r"  ([a-z_][a-z0-9_]*):", line)
            if child_match and current_section:
                section_children[current_section].append(child_match.group(1))
        config_keys = {
            match.group(1)
            for match in re.finditer(
                r"^\s*([a-z_][a-z0-9_]*):", config_text, re.MULTILINE
            )
        }
        if (
            re.findall(r"^setup_version:\s*(.*?)\s*$", config_text, re.MULTILINE)
            != ["2"]
            or 'language: ""' not in config_text
            or len(blank_choices) != 6
            or len(all_choices) != 6
            or 'plugin_setup: ""' not in config_text
            or 'pending_plugin: ""' not in config_text
            or section_children.get("claude_code") != ["choice"]
            or section_children.get("chatgpt_browser") != ["choice"]
        ):
            errors.append(
                "example setup must use version 2 with six blank choices and choice-only AI sections"
            )
        forbidden_config_keys = sorted(
            key for key in config_keys if is_forbidden_setup_detail_key(key)
        )
        if forbidden_config_keys:
            errors.append("example setup must not store authentication or account details")

    validate_setup_state_fixtures(errors)
    validate_setup_migration_fixtures(errors)
    validate_auth_command_fixtures(errors)
    validate_secret_fixtures(errors)
    validate_claude_readiness_fixtures(errors)
    validate_remote_state_fixtures(errors)
    validate_bundled_obsidian_plugin(errors)
    validate_formalization_manifest_fixtures(errors)
    validate_vault_lint_fixtures(errors)
    validate_math_project_harness(errors)

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
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:-dev)?\n?", version_text):
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
