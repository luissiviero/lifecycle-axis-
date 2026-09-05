"""Tests for scripts/check_eval_cases.py: an eval case's `check:` block must be able to fail.

Under `set -e`, a negated command (`! cmd`) never triggers errexit, so a refusal asserted that way
is inert unless it is the block's last command or ends with `|| exit 1` (work/agent-evals R-3).
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(HERE, "check_eval_cases.py")


def _case(root, name, body):
    d = os.path.join(root, "evals", "cases")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name + ".yaml"), "w", encoding="utf-8") as f:
        f.write(body)


def _run(root):
    return subprocess.run([sys.executable, SCRIPT, "--root", root], capture_output=True, text=True)


def _last_line(text):
    lines = [l for l in text.splitlines() if l.strip()]
    return lines[-1] if lines else ""


class EvalCases(unittest.TestCase):
    def test_bare_negation_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            _case(root, "bare", "name: bare\nkind: hook\ncheck: |\n  set -e\n  ! false\n  true\n")
            result = _run(root)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("bare.yaml:5: negated command cannot fail under set -e", result.stdout)
            self.assertEqual(_last_line(result.stdout), "EVAL-CASES: 1 cases, 1 problems")

    def test_negation_with_exit_is_accepted(self):
        with tempfile.TemporaryDirectory() as root:
            _case(root, "ok", "name: ok\nkind: hook\ncheck: |\n  set -e\n  ! false || exit 1\n  ! false || exit 3\n  true\n")
            result = _run(root)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(_last_line(result.stdout), "EVAL-CASES: 1 cases, 0 problems")

    def test_final_negation_is_accepted(self):
        # The last command's status is the script's status, so a bare `!` there can fail the case.
        with tempfile.TemporaryDirectory() as root:
            _case(root, "final", "name: final\nkind: hook\ncheck: |\n  set -e\n  true\n  # trailing comment\n  ! false\n")
            self.assertEqual(_run(root).returncode, 0)

    def test_case_without_set_e_is_accepted(self):
        with tempfile.TemporaryDirectory() as root:
            _case(root, "loose", "name: loose\nkind: hook\ncheck: |\n  ! false\n  true\n")
            _case(root, "oneline", 'name: oneline\nkind: hook\ncheck: "! false"\n')
            self.assertEqual(_run(root).returncode, 0)

    def test_continued_command_is_one_command(self):
        with tempfile.TemporaryDirectory() as root:
            _case(root, "cont-ok", "name: cont-ok\nkind: hook\ncheck: |\n  set -e\n  ! false \\\n    --flag || exit 1\n  true\n")
            self.assertEqual(_run(root).returncode, 0)
            _case(root, "cont-bad", "name: cont-bad\nkind: hook\ncheck: |\n  set -e\n  ! false \\\n    --flag\n  true\n")
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("cont-bad.yaml:5:", result.stdout)
            # A heredoc body is not a command, whatever its lines start with.
            _case(root, "heredoc", "name: heredoc\nkind: hook\ncheck: |\n  set -e\n  cat > f <<'EOF'\n  ! not a command\n  EOF\n  true\n")
            for name in ("cont-bad",):
                os.unlink(os.path.join(root, "evals", "cases", name + ".yaml"))
            self.assertEqual(_run(root).returncode, 0)

    def test_heredoc_operator_inside_quotes_is_not_a_heredoc(self):
        # Two real cases build a heredoc-shaped command inside a printf string for a hook to judge;
        # a parser that took that `<<"EOF"` as a heredoc skipped every later line and missed three
        # inert negations (found while fixing the fifteen cases).
        with tempfile.TemporaryDirectory() as root:
            _case(root, "quoted", "name: quoted\nkind: hook\ncheck: |\n  set -e\n"
                  "  C=\"$(printf 'cat > .sdlc/x <<\"EOF\"\\nbad\\nEOF\\n')\"\n"
                  "  ! echo \"$C\" | grep -q nothing\n  true\n")
            result = _run(root)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("quoted.yaml:6:", result.stdout)

    def test_unknown_kind_or_empty_case_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            _case(root, "kind", "name: kind\nkind: nope\ncheck: \"true\"\n")
            _case(root, "empty", "name: empty\nkind: hook\n")
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("kind.yaml: kind 'nope'", result.stdout)
            self.assertIn("empty.yaml: neither check nor prompt", result.stdout)

    def test_real_cases_pass(self):
        result = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertRegex(_last_line(result.stdout), r"^EVAL-CASES: \d+ cases, 0 problems$")


if __name__ == "__main__":
    unittest.main()
