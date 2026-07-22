#!/usr/bin/env python3
"""Validate the public distribution without third-party dependencies."""

from __future__ import annotations

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
    ".agents/skills/first-run/agents/openai.yaml",
    ".agents/skills/first-run/references/github.md",
    ".agents/skills/first-run/references/claude-code.md",
    ".agents/skills/first-run/references/chatgpt-browser.md",
    ".agents/skills/first-run/references/storage.md",
    ".agents/skills/first-run/references/obsidian.md",
    ".agents/skills/first-run/references/obsidian-plugins.md",
    ".agents/skills/first-run/references/tex.md",
    ".agents/skills/claude-review/SKILL.md",
    ".agents/skills/claude-review/agents/openai.yaml",
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
    "scripts/doctor.ps1",
    "scripts/doctor.sh",
    "scripts/install-bundled-obsidian-plugin.py",
    "scripts/migrate-setup-v1.py",
    "scripts/remote-state.py",
    "scripts/setup-state.py",
    "scripts/tests/mrw-latex-delimiter-compat.test.js",
    "scripts/validate-release.py",
    "scripts/vault-lint.py",
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
) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="workbench-lint-") as temp_name:
        fixture_root = Path(temp_name) / "workbench"
        scripts_dir = fixture_root / "scripts"
        scripts_dir.mkdir(parents=True)
        shutil.copy2(ROOT / "scripts/vault-lint.py", scripts_dir / "vault-lint.py")
        for name in ("inbox", "ideas", "papers", "notes", "projects"):
            (fixture_root / name).mkdir()
        if note_text is not None:
            note_path = fixture_root / note_relative
            note_path.parent.mkdir(parents=True, exist_ok=True)
            note_path.write_text(note_text, encoding="utf-8")
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
        | Lem-001 | Fixture \( |x| \) | conjectural | Def-001 | | unchecked | isolated | |
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
    legacy_project = project_spine.replace(
        "## Research State Spine\n### Definition registry\n| ID | Definition or notation | Exact formulation or source | Notes |\n|---|---|---|---|\n| Def-001 | Fixture | | |\n### Claim ledger\n| ID | Claim | Mathematical state | Depends on | Evidence or source | Review provenance | Integration state | Next action |\n|---|---|---|---|---|---|---|---|\n| Lem-001 | Fixture \\( |x| \\) | conjectural | Def-001 | | unchecked | isolated | |\n### Open gaps\n| ID | Affects | Precise missing justification or issue | Severity | State | Next action |\n|---|---|---|---|---|---|\n| Gap-001 | Lem-001 | Fixture | local | open | |",
        "## Claim ledger\n| ID | Claim | State | Evidence or gap | Source log |\n|---|---|---|---|---|\n| C1 | Fixture | conjectural | | |",
    )
    legacy_project_result = execute_vault_lint(
        note_text=legacy_project,
        note_relative="projects/fixture/README.md",
    )
    cases = (
        ("valid research log", execute_vault_lint(note_text=valid), 0),
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

    for skill_name in ("first-run", "claude-review", "pro-context-bundle"):
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
        required_review_boundaries = (
            "--safe-mode",
            '--settings \'{"disableAllHooks":true}\'',
            '--tools ""',
            '--disallowedTools "*"',
            "--disable-slash-commands",
            "--permission-mode dontAsk",
            "--no-chrome",
            "--strict-mcp-config",
            "--no-session-persistence",
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
