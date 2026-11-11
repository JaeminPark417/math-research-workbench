"""Exercise the public entry point with synthetic research notes and local Git history."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1]
if not (SCRIPTS / "math_target.py").exists():
    SCRIPTS = Path(__file__).resolve().parent
HELPER = SCRIPTS / "math_target.py"
REF = "<stable ID; repository-relative path to the canonical statement (project README or claim ledger); current `HEAD` hash if the copied wording matches it, otherwise `working snapshot Run-YYYYMMDD-NNN` with this run's actual ID; `not applicable` for a new object>"
TARGET = '<copy the current Spine wording exactly, or state the proposed new target exactly>'
RUN = """---
type: research-log
run_id: Run-20261111-001
---
# Research run

## Problem Contract

- Spine target reference: <source>
- Exact target: <statement>
- Success criterion: Prove it.

## Synthesis

Original notes.
""".replace("<source>", REF).replace("<statement>", TARGET)
STATEMENT = r"Every real symmetric matrix $A$ is orthogonally diagonalizable."
NARROWED = STATEMENT.replace("real symmetric", "positive definite real symmetric")


def ledger(statement):
    return "| ID | Claim | Mathematical state |\n|---|---|---|\n| Thm-001 | " + statement + " | open |\n"


class TargetTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run = self.root / "정리.md"
        self.run.write_text(RUN, encoding="utf-8")
        self.source = self.root / "source.md"
        self.source.write_text(ledger(STATEMENT), encoding="utf-8")
        self.snap = self.run.with_suffix(".target.json")

    def cli(self, action, *extra, expect=0):
        args = [sys.executable, str(HELPER), action, "--root", str(self.root), "--run", self.run.name]
        if action == "capture":
            args += ["--source", "source.md", "--id", "Thm-001"]
        result = subprocess.run(args + list(extra), encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result.stdout

    def test_frozen_working_target_and_later_changes(self):
        self.assertIn("정리.target.json", self.cli("capture"))
        snap = json.loads(self.snap.read_text(encoding="utf-8"))
        self.assertEqual(snap["version"], "working snapshot Run-20261111-001")
        self.assertEqual(snap["statement"], STATEMENT)
        self.cli("check")
        self.source.write_text(ledger(NARROWED), encoding="utf-8")
        self.assertIn("current source wording changed", self.cli("check", expect=2))
        captured = self.run.read_text(encoding="utf-8")
        self.run.write_text(captured.replace(STATEMENT, NARROWED), encoding="utf-8")
        self.assertIn("differs from frozen", self.cli("check", expect=1))
        self.assertEqual(self.snap.read_text(encoding="utf-8").count(STATEMENT), 1)

    def test_multiline_private_source_survives_reopening(self):
        source = "Every bounded monotone sequence converges.\n\n1. 상수 수열도 포함한다.\n2. Keep all inequalities.\n\n$$\n  a_n \\le b\n$$"
        self.source.write_text("# Result\n\n## 정확한 명제\n\n" + source + "\n\n## Proof\nA separate proof.\n", encoding="utf-8")
        self.run.write_text(RUN.replace("run_id: Run-20261111-001", "").replace(
            "- Spine target reference:", "- **Run ID**: `Run-20261111-001`\n- **Spine target reference**:"
        ).replace("- Exact target:", "- **Exact statement**:"), encoding="utf-8")
        self.cli("capture", "--heading", "정확한 명제")
        self.assertEqual(json.loads(self.snap.read_text(encoding="utf-8"))["statement"], source)
        self.cli("check")
        written = self.run.read_text(encoding="utf-8")
        self.assertIn("- Target heading: 정확한 명제", written)
        self.assertIn("Original notes.", written)
        self.run.write_text(written.replace("Target heading: 정확한 명제", "Target heading: Proof"), encoding="utf-8")
        self.assertIn("heading differs", self.cli("check", expect=1))

    def test_legacy_local_scope_drift_requires_review(self):
        self.run.write_text(RUN.replace(REF, "Thm-001; source.md; working snapshot Run-20261111-001").replace(TARGET, NARROWED), encoding="utf-8")
        self.assertIn("legacy working target", self.cli("check", expect=1))
        self.run.write_text(self.run.read_text(encoding="utf-8").replace(NARROWED, STATEMENT), encoding="utf-8")
        self.assertIn("original wording unverifiable", self.cli("check", expect=2))
        self.assertFalse(self.snap.exists())

    def test_existing_statement_or_binding_is_never_replaced(self):
        original = RUN.replace(TARGET, NARROWED)
        self.run.write_text(original, encoding="utf-8")
        self.assertIn("existing target differs", self.cli("capture", expect=1))
        self.assertEqual(self.run.read_text(encoding="utf-8"), original)
        self.assertFalse(self.snap.exists())
        self.run.write_text(RUN, encoding="utf-8")
        self.cli("capture")
        self.assertIn("already has a frozen", self.cli("capture", expect=1))
        self.snap.write_text(self.snap.read_text(encoding="utf-8").replace(STATEMENT, NARROWED), encoding="utf-8")
        self.assertIn("digest differs", self.cli("check", expect=1))

    def test_missing_and_duplicate_locators(self):
        self.source.write_text(ledger(STATEMENT) + ledger(NARROWED), encoding="utf-8")
        self.assertIn("missing or ambiguous", self.cli("capture", expect=1))
        self.assertFalse(self.snap.exists())
        self.source.write_text(ledger(STATEMENT), encoding="utf-8")
        self.cli("capture")
        self.snap.unlink()
        self.assertIn("missing or invalid", self.cli("check", expect=1))

    def test_table_prefers_exact_wording_and_rejects_tied_columns(self):
        header = "| ID | Claim | Exact statement | Other |"
        rows = "|---|---|---|---|\n| Thm-001 | Short title | " + STATEMENT + " | alternate |\n"
        proposed = "| Thm-001 (proposed v2) | Proposed | Pending revision | open |\n"
        self.source.write_text(header.replace("Other", "Exact formulation") + "\n" + rows, encoding="utf-8")
        self.assertIn("column is missing or ambiguous", self.cli("capture", expect=1))
        fake = "~~~~md\n" + ledger(NARROWED) + "~~~\n" + ledger(NARROWED) + "~~~~~\n"
        self.source.write_text(fake + header + "\n" + rows + proposed, encoding="utf-8")
        self.cli("capture")
        self.assertEqual(json.loads(self.snap.read_text(encoding="utf-8"))["statement"], STATEMENT)
        self.cli("check")

    def test_fenced_headings_and_other_quoted_examples(self):
        fake = "````markdown\n## Theorem\n```\n## Theorem\n`````\n"
        body = "Assume all of the following.\n\n~~~~example\n## Not a heading\n~~~\n## Still literal\n~~~~~\n\nThen the conclusion holds."
        self.source.write_text(fake + "## Theorem\n" + body + "\n\n## Proof\nSeparate proof.\n", encoding="utf-8")
        notes = "````markdown\n## Problem Contract\n```\n- Exact target: A literal illustration\n````\n"
        self.run.write_text(notes + RUN.replace("- Spine target reference:", notes.replace("## Problem Contract", "## Literal heading") + "- Spine target reference:"), encoding="utf-8")
        self.cli("capture", "--heading", "Theorem")
        self.assertEqual(json.loads(self.snap.read_text(encoding="utf-8"))["statement"], body)
        self.cli("check")

    def test_checkout_newlines_and_editor_whitespace(self):
        body = "Two paragraphs.\n\nOne more condition."
        self.source.write_text("## Exact statement\n" + body + "\n", encoding="utf-8")
        mixed = RUN.replace("\n", "\r\n").replace("## Synthesis\r\n", "## Synthesis\n")
        self.run.write_bytes(mixed.encode("utf-8"))
        self.cli("capture", "--heading", "Exact statement")
        raw = self.run.read_bytes()
        self.assertTrue(raw.endswith(b"## Synthesis\n\r\nOriginal notes.\r\n"))
        self.assertIn(b"Two paragraphs.\r\n\r\n  One more condition.", raw)
        self.snap.write_bytes(self.snap.read_bytes().replace(b"\n", b"\r\n"))
        self.run.write_bytes(raw.replace(b"paragraphs.\r\n\r\n", b"paragraphs.\r\n  \r\n"))
        self.cli("check")
        self.run.write_bytes(raw)
        self.cli("check")

    def test_review_missing_bindings_and_preserve_angle_bracket_text(self):
        for ref in ("", REF):
            self.run.write_text(RUN.replace(REF, ref), encoding="utf-8")
            self.assertIn("binding is missing", self.cli("check", expect=2))
        self.run.write_text(RUN.replace(REF, "not applicable"), encoding="utf-8")
        self.assertIn("Unbound", self.cli("check"))
        original = RUN.replace(TARGET, "<x, y>")
        self.run.write_text(original, encoding="utf-8")
        self.assertIn("existing target differs", self.cli("capture", expect=1))
        self.assertEqual(self.run.read_text(encoding="utf-8"), original)
        self.assertFalse(self.snap.exists())
        self.run.write_text(RUN, encoding="utf-8")
        self.cli("capture")
        self.run.write_text(RUN, encoding="utf-8")
        self.assertIn("interrupted capture", self.cli("check", expect=1))
        self.cli("capture")
        self.cli("check")

    @unittest.skipUnless(shutil.which("git"), "Git unavailable")
    def test_pinned_source_from_historical_commit(self):
        def git(*args):
            return subprocess.check_output(
                ["git", "-c", "user.name=Fixture", "-c", "user.email=source-test@example.org",
                 "-c", "core.hooksPath=" + os.devnull, "-c", "commit.gpgSign=false", *args],
                cwd=self.root, stderr=subprocess.PIPE, encoding="utf-8").strip()
        git("init", "-q")
        git("add", "source.md")
        git("commit", "-qm", "Synthetic source")
        old = git("rev-parse", "HEAD")
        self.cli("capture")
        self.assertEqual(json.loads(self.snap.read_text(encoding="utf-8"))["version"], old)
        self.snap.unlink()
        self.run.write_text(RUN.replace(REF, "Thm-001; source.md; HEAD " + old).replace(TARGET, STATEMENT), encoding="utf-8")
        self.cli("check")
        self.run.write_text(RUN, encoding="utf-8")
        self.source.write_text(ledger(NARROWED), encoding="utf-8")
        git("add", "source.md")
        git("commit", "-qm", "Synthetic revision")
        self.cli("capture", "--commit", old)
        self.assertEqual(json.loads(self.snap.read_text(encoding="utf-8"))["statement"], STATEMENT)
        self.assertIn("current source wording changed", self.cli("check", expect=2))
        self.snap.unlink()
        self.run.write_text(RUN.replace(REF, "Thm-001; source.md; HEAD " + old).replace(TARGET, NARROWED), encoding="utf-8")
        self.assertIn("pinned source wording", self.cli("check", expect=1))


if __name__ == "__main__":
    unittest.main()
