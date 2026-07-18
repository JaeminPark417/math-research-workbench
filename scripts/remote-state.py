#!/usr/bin/env python3
"""Report Git remote safety without printing a raw credential-bearing URL."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
DISTRIBUTION = ("jaeminpark417", "math-research-workbench")


def capture(*args: str) -> tuple[int, str]:
    try:
        result = subprocess.run(
            args,
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="strict",
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return 1, ""
    return result.returncode, result.stdout.strip()


def github_repository(raw: str) -> tuple[str, str] | None:
    value = raw.strip()
    if value.startswith("git@github.com:"):
        path = value[len("git@github.com:") :]
    else:
        try:
            parsed = urlsplit(value)
        except ValueError:
            return None
        try:
            port = parsed.port
        except ValueError:
            return None
        scheme = parsed.scheme.casefold()
        safe_https = (
            scheme == "https"
            and parsed.username is None
            and parsed.password is None
            and port is None
        )
        safe_ssh = (
            scheme == "ssh"
            and parsed.username == "git"
            and parsed.password is None
            and port in {None, 22}
        )
        safe_git = (
            scheme == "git"
            and parsed.username is None
            and parsed.password is None
            and port is None
        )
        if (
            (parsed.hostname or "").lower() != "github.com"
            or not (safe_https or safe_ssh or safe_git)
            or parsed.query
            or parsed.fragment
        ):
            return None
        path = parsed.path.lstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    path = path.strip("/")
    parts = path.split("/")
    safe_component = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
    if len(parts) != 2 or not all(safe_component.fullmatch(part) for part in parts):
        return None
    return parts[0], parts[1]


def main() -> int:
    if not shutil.which("git"):
        print("git_tree=unknown")
        print("origin=unknown")
        print("visibility=unknown")
        return 0

    code, inside = capture("git", "rev-parse", "--is-inside-work-tree")
    if code != 0 or inside != "true":
        print("git_tree=no")
        print("origin=none")
        print("visibility=not-applicable")
        return 0

    print("git_tree=yes")
    code, raw_origin = capture("git", "config", "--get", "remote.origin.url")
    if code != 0 or not raw_origin:
        print("origin=none")
        print("visibility=not-applicable")
        return 0

    repository = github_repository(raw_origin)
    if repository is None:
        print("origin=other-present-redacted")
        print("visibility=unknown")
        return 0

    normalized = tuple(part.lower() for part in repository)
    if normalized == DISTRIBUTION:
        print("origin=public-distribution")
        print("visibility=public")
        return 0

    print("origin=github-present-redacted")
    visibility = "unknown"
    if shutil.which("gh"):
        code, answer = capture(
            "gh",
            "repo",
            "view",
            f"{repository[0]}/{repository[1]}",
            "--json",
            "visibility",
            "--jq",
            ".visibility",
        )
        if code == 0 and answer.lower() in {"private", "public", "internal"}:
            visibility = answer.lower()
    print(f"visibility={visibility}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
