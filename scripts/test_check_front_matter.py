"""Tests for scripts/check_front_matter.py: every tracked Markdown front matter must parse as strict YAML
(work/docs-reconcile R-6).

The kit's own parser tolerates an unquoted `title: Metrics: one thing`, GitHub's renderer does not: the
owner met the YAML error banner from a phone on 2026-09-05. The checker runs PyYAML when present and a
structural fallback otherwise, and names its mode in the last line.
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "check_front_matter.py")

GOOD = '---\ntype: doc\ntitle: "Metrics: one leading indicator"\ntimestamp: 2026-09-05T00:00:00Z\n---\n# Doc\n'
BAD = "---\ntype: doc\ntitle: Metrics: one leading indicator\ntimestamp: 2026-09-05T00:00:00Z\n---\n# Doc\n"
LIST = "---\n- one\n- two\n---\n# Doc\n"
PLAIN = "# No front matter\n\nJust text.\n"


def _repo(root, files):
    subprocess.run(["git", "init", "-q", root], check=True)
    for name, body in files.items():
        with open(os.path.join(root, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
    subprocess.run(["git", "-C", root, "add", "-A"], check=True)


def _run(root, *extra, stdin=None):
    return subprocess.run(
        [sys.executable, SCRIPT, "--root", root, *extra], capture_output=True, text=True, input=stdin
    )


def _last(text):
    lines = [l for l in text.splitlines() if l.strip()]
    return lines[-1] if lines else ""


class FrontMatter(unittest.TestCase):
    def test_unquoted_colon_space_is_reported_with_file_and_line(self):
        with tempfile.TemporaryDirectory() as root:
            _repo(root, {"bad.md": BAD})
            r = _run(root)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("bad.md:3:", r.stdout)
            self.assertTrue(_last(r.stdout).startswith("FRONT-MATTER: 1 docs, 1 problems"), r.stdout)

    def test_quoted_value_passes(self):
        with tempfile.TemporaryDirectory() as root:
            _repo(root, {"good.md": GOOD})
            r = _run(root)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue(_last(r.stdout).startswith("FRONT-MATTER: 1 docs, 0 problems"), r.stdout)

    def test_file_without_front_matter_is_skipped_not_counted(self):
        with tempfile.TemporaryDirectory() as root:
            _repo(root, {"good.md": GOOD, "plain.md": PLAIN})
            r = _run(root)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue(_last(r.stdout).startswith("FRONT-MATTER: 1 docs, 0 problems"), r.stdout)

    def test_block_that_is_not_a_mapping_is_a_problem(self):
        with tempfile.TemporaryDirectory() as root:
            _repo(root, {"list.md": LIST})
            r = _run(root)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("list.md:1: front matter is not a mapping", r.stdout)

    def test_stdin_checks_one_document(self):
        with tempfile.TemporaryDirectory() as root:
            _repo(root, {"good.md": GOOD})
            r = _run(root, "--stdin", stdin=BAD)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("<stdin>:3:", r.stdout)
            self.assertTrue(_last(r.stdout).startswith("FRONT-MATTER: 1 docs, 1 problems"), r.stdout)

    def test_structural_fallback_catches_the_same_defect_and_names_its_mode(self):
        with tempfile.TemporaryDirectory() as root:
            _repo(root, {"bad.md": BAD, "good.md": GOOD})
            r = _run(root, "--no-yaml")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("bad.md:3:", r.stdout)
            self.assertNotIn("good.md", r.stdout)
            self.assertEqual(_last(r.stdout), "FRONT-MATTER: 2 docs, 1 problems (structural)")


if __name__ == "__main__":
    unittest.main()
