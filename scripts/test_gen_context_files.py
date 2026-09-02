import io
import os
import sys
import contextlib
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)

import gen_context_files as gen  # noqa: E402

BEGIN = "<!-- BEGIN GENERATED: rules — edit the fragments, run scripts/gen_context_files.py -->"
END = "<!-- END GENERATED -->"

FRAGMENT_A = """---
type: sdlc/rule-fragment
targets: [alpha, beta]
order: 0
---
# Shared header

Shared body line.
"""

FRAGMENT_B = """---
type: sdlc/rule-fragment
targets: [alpha]
order: 10
---
## Alpha only
- one alpha-only bullet
"""

GOLDEN_ALPHA = (
    BEGIN + "\n"
    "# Shared header\n"
    "\n"
    "Shared body line.\n"
    "\n"
    "## Alpha only\n"
    "- one alpha-only bullet\n"
    + END + "\n"
)

GOLDEN_BETA = (
    BEGIN + "\n"
    "# Shared header\n"
    "\n"
    "Shared body line.\n"
    + END + "\n"
)


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _make_root(root, max_lines=120, fragments=None):
    """A minimal repo: two context files (ALPHA.md, BETA.md) from rules/."""
    _write(
        os.path.join(root, ".sdlc", "config.env"),
        'CONTEXT_FILES="ALPHA.md BETA.md"\n'
        'RULES_SRC="rules"\n'
        'MAX_CONTEXT_LINES="%d"\n' % max_lines,
    )
    for name, body in (fragments or {"00-a.md": FRAGMENT_A, "10-b.md": FRAGMENT_B}).items():
        _write(os.path.join(root, "rules", name), body)
    return root


def _run(*argv):
    """Run the generator; return (rc, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = gen.main(list(argv))
    return rc, out.getvalue(), err.getvalue()


class RenderTests(unittest.TestCase):
    def test_golden_render_for_two_fragments(self):
        with tempfile.TemporaryDirectory() as root:
            _make_root(root)
            rc, _, err = _run("--root", root)
            self.assertEqual(rc, 0, err)
            self.assertEqual(_read(os.path.join(root, "ALPHA.md")), GOLDEN_ALPHA)
            self.assertEqual(_read(os.path.join(root, "BETA.md")), GOLDEN_BETA)

    def test_target_filtering_keeps_alpha_only_fragment_out_of_beta(self):
        with tempfile.TemporaryDirectory() as root:
            _make_root(root)
            self.assertEqual(_run("--root", root)[0], 0)
            self.assertIn("## Alpha only", _read(os.path.join(root, "ALPHA.md")))
            self.assertNotIn("## Alpha only", _read(os.path.join(root, "BETA.md")))

    def test_text_outside_the_markers_is_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            _make_root(root)
            _write(
                os.path.join(root, "ALPHA.md"),
                "Hand-written preamble.\n\n" + BEGIN + "\nstale\n" + END + "\n"
                "\n## Lessons learned\n- keep me\n",
            )
            self.assertEqual(_run("--root", root)[0], 0)
            text = _read(os.path.join(root, "ALPHA.md"))
            self.assertTrue(text.startswith("Hand-written preamble.\n\n" + BEGIN))
            self.assertTrue(text.endswith("## Lessons learned\n- keep me\n"))
            self.assertNotIn("stale", text)
            self.assertIn("## Alpha only", text)

    def test_second_run_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as root:
            _make_root(root)
            self.assertEqual(_run("--root", root)[0], 0)
            first = _read(os.path.join(root, "ALPHA.md"))
            rc, out, _ = _run("--root", root)
            self.assertEqual(rc, 0)
            self.assertIn("0 changed", out)
            self.assertEqual(_read(os.path.join(root, "ALPHA.md")), first)

    def test_check_fails_after_a_hand_edit_and_passes_after_regeneration(self):
        with tempfile.TemporaryDirectory() as root:
            _make_root(root)
            self.assertEqual(_run("--root", root)[0], 0)
            self.assertEqual(_run("--root", root, "--check")[0], 0)
            path = os.path.join(root, "ALPHA.md")
            _write(path, _read(path).replace("Shared body line.", "Edited by hand."))
            rc, _, err = _run("--root", root, "--check")
            self.assertEqual(rc, 1)
            self.assertIn("ALPHA.md is out of date", err)
            self.assertEqual(_run("--root", root)[0], 0)
            self.assertEqual(_run("--root", root, "--check")[0], 0)

    def test_over_length_exits_1_with_the_count_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as root:
            long_fragment = FRAGMENT_A + "\n".join("filler %d" % i for i in range(30)) + "\n"
            _make_root(root, max_lines=10, fragments={"00-a.md": long_fragment})
            rc, _, err = _run("--root", root)
            self.assertEqual(rc, 1)
            self.assertIn("ALPHA.md: 35 lines, over MAX_CONTEXT_LINES=10", err)
            self.assertFalse(os.path.exists(os.path.join(root, "ALPHA.md")))
            self.assertFalse(os.path.exists(os.path.join(root, "BETA.md")))


class ErrorTests(unittest.TestCase):
    def _expect_failure(self, root, needle):
        rc, _, err = _run("--root", root)
        self.assertEqual(rc, 1, err)
        self.assertIn(needle, err)
        self.assertFalse(os.path.exists(os.path.join(root, "BETA.md")))

    def test_begin_marker_without_end_errors_without_writing(self):
        with tempfile.TemporaryDirectory() as root:
            _make_root(root)
            _write(os.path.join(root, "ALPHA.md"), "intro\n" + BEGIN + "\nbody\n")
            self._expect_failure(root, "BEGIN GENERATED marker without an END")
            self.assertEqual(_read(os.path.join(root, "ALPHA.md")), "intro\n" + BEGIN + "\nbody\n")

    def test_end_marker_without_begin_errors_without_writing(self):
        with tempfile.TemporaryDirectory() as root:
            _make_root(root)
            _write(os.path.join(root, "ALPHA.md"), "intro\nbody\n" + END + "\n")
            self._expect_failure(root, "END GENERATED marker without a BEGIN")

    def test_fragment_containing_a_marker_line_errors(self):
        with tempfile.TemporaryDirectory() as root:
            _make_root(root, fragments={"00-a.md": FRAGMENT_A + END + "\n"})
            self._expect_failure(root, "contains a generated-block marker")

    def test_unknown_target_errors(self):
        with tempfile.TemporaryDirectory() as root:
            _make_root(root, fragments={"00-a.md": FRAGMENT_A.replace("beta", "gamma")})
            self._expect_failure(root, "unknown target 'gamma'")

    def test_missing_order_errors(self):
        with tempfile.TemporaryDirectory() as root:
            _make_root(root, fragments={"00-a.md": FRAGMENT_A.replace("order: 0\n", "")})
            self._expect_failure(root, "no 'order:'")


class RealOutputTests(unittest.TestCase):
    """The eight hard rules must be byte-identical in all three context files."""

    @staticmethod
    def _hard_rules(path):
        block, on = [], False
        for line in _read(path).split("\n"):
            if line.startswith("## "):
                if on:
                    break
                on = line.startswith("## Hard rules")
                if on:
                    block.append(line)
                continue
            if on:
                block.append(line)
        return "\n".join(block).strip("\n")

    def test_hard_rules_are_identical_across_the_three_context_files(self):
        rules = {}
        for name in ("CLAUDE.md", "GEMINI.md", "AGENTS.md"):
            path = os.path.join(ROOT, name)
            self.assertTrue(os.path.exists(path), "%s is missing" % name)
            rules[name] = self._hard_rules(path)
            self.assertIn("8. Subagents have a named role", rules[name], name)
        self.assertEqual(rules["CLAUDE.md"], rules["GEMINI.md"])
        self.assertEqual(rules["CLAUDE.md"], rules["AGENTS.md"])

    def test_claude_only_content_stays_out_of_the_neutral_files(self):
        for name in ("GEMINI.md", "AGENTS.md"):
            text = _read(os.path.join(ROOT, name))
            self.assertNotIn("/sdlc-intent", text, name)
            self.assertNotIn(".claude/agents/` with", text, name)
        self.assertNotIn("Gemini CLI notes", _read(os.path.join(ROOT, "AGENTS.md")))
        self.assertIn("Gemini CLI notes", _read(os.path.join(ROOT, "GEMINI.md")))

    def test_lessons_learned_stays_outside_the_generated_block(self):
        text = _read(os.path.join(ROOT, "CLAUDE.md"))
        self.assertLess(text.index(gen.END_MARKER), text.index("## Lessons learned"))


if __name__ == "__main__":
    unittest.main()
