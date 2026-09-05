import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_index  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
GEN_INDEX = os.path.join(HERE, "gen_index.py")

ALPHA_INTENT = """\
---
type: sdlc/intent
id: alpha
title: Alpha item
description: Do the alpha thing
status: approved
approved-by: alice
timestamp: 2026-01-01T00:00:00Z
---
# Intent: alpha

Body text.
"""

ALPHA_SPEC = """\
---
type: sdlc/spec
id: alpha
status: approved
approved-by: alice
timestamp: 2026-01-02T00:00:00Z
---
# Spec: alpha
"""

ALPHA_LOG = """\
---
type: sdlc/log
id: alpha-log
title: Gate ledger for alpha
description: test fixture
timestamp: 2026-01-01T00:00:00Z
---
# Log: alpha

- 2026-01-01T00:00:00Z | intent.md | (none) -> draft | alice | abc1234 | drafted
- 2026-01-01T01:00:00Z | intent.md | draft -> approved | alice | abc1234 | approved
- 2026-01-02T00:00:00Z | spec.md | draft -> approved | alice | def5678 | approved
"""

ZETA_INTENT = """\
---
type: sdlc/intent
id: zeta
status: draft
---
# Intent: zeta stands alone
"""

GOLDEN_ALPHA_INDEX = (
    "---\n"
    "type: sdlc/work-item\n"
    "id: alpha\n"
    "title: Alpha item\n"
    "description: Do the alpha thing\n"
    "timestamp: 2026-01-02T00:00:00Z\n"
    "---\n"
    "# Alpha item\n"
    "\n"
    "- [intent.md](intent.md) — status: approved; approved-by: alice; Do the alpha thing\n"
    "- [spec.md](spec.md) — status: approved; approved-by: alice; \n"
    "\n"
    "Last gate: - 2026-01-02T00:00:00Z | spec.md | draft -> approved | alice | def5678 | approved\n"
)

GOLDEN_ZETA_INDEX = (
    "---\n"
    "type: sdlc/work-item\n"
    "id: zeta\n"
    "title: \"Intent: zeta stands alone\"\n"
    "description: \n"
    "timestamp: 1970-01-01T00:00:00Z\n"
    "---\n"
    "# Intent: zeta stands alone\n"
    "\n"
    "- [intent.md](intent.md) — status: draft; approved-by: ; \n"
    "\n"
    "Last gate: —\n"
)

GOLDEN_TOP_INDEX = (
    "---\n"
    "type: sdlc/index\n"
    "title: Work items\n"
    "description: Generated index of every work/<slug> item; run scripts/gen_index.py to refresh.\n"
    "timestamp: 2026-01-02T00:00:00Z\n"
    "---\n"
    "# Work items\n"
    "\n"
    "| slug | title | stage | intent | spec | plan | last gate |\n"
    "|---|---|---|---|---|---|---|\n"
    "| [alpha](alpha/index.md) | Alpha item | spec | approved | approved | — | spec.md -> approved by alice |\n"
    "| [zeta](zeta/index.md) | Intent: zeta stands alone | intent | draft | — | — | — |\n"
)


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def _build_two_item_tree(root):
    """One full item with a log (alpha: intent + spec, no plan) and one
    intent-only item (zeta, whose title falls back to its first heading)."""
    _write(os.path.join(root, "work", "alpha", "intent.md"), ALPHA_INTENT)
    _write(os.path.join(root, "work", "alpha", "spec.md"), ALPHA_SPEC)
    _write(os.path.join(root, "work", "alpha", "log.md"), ALPHA_LOG)
    _write(os.path.join(root, "work", "zeta", "intent.md"), ZETA_INTENT)


def _outputs_by_path(outputs):
    return {relpath: content for relpath, content in outputs}


def _run_cli(args, cwd=None):
    return subprocess.run(
        [sys.executable, GEN_INDEX] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


class GoldenRender(unittest.TestCase):
    def test_two_items_match_golden_strings(self):
        with tempfile.TemporaryDirectory() as root:
            _build_two_item_tree(root)
            outputs = _outputs_by_path(gen_index.render_all(root))
            self.assertEqual(
                outputs[os.path.join("work", "alpha", "index.md")], GOLDEN_ALPHA_INDEX
            )
            self.assertEqual(
                outputs[os.path.join("work", "zeta", "index.md")], GOLDEN_ZETA_INDEX
            )
            self.assertEqual(outputs["work/index.md"], GOLDEN_TOP_INDEX)


class Idempotence(unittest.TestCase):
    def test_running_twice_yields_identical_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            _build_two_item_tree(root)
            first = gen_index.render_all(root)
            second = gen_index.render_all(root)
            self.assertEqual(first, second)

    def test_writing_twice_yields_identical_files_on_disk(self):
        with tempfile.TemporaryDirectory() as root:
            _build_two_item_tree(root)
            r1 = _run_cli(["--root", root])
            self.assertEqual(r1.returncode, 0, r1.stderr)
            with open(os.path.join(root, "work", "index.md"), "rb") as f:
                first_bytes = f.read()
            r2 = _run_cli(["--root", root])
            self.assertEqual(r2.returncode, 0, r2.stderr)
            with open(os.path.join(root, "work", "index.md"), "rb") as f:
                second_bytes = f.read()
            self.assertEqual(first_bytes, second_bytes)


class CheckMode(unittest.TestCase):
    def test_check_passes_on_freshly_generated_tree(self):
        with tempfile.TemporaryDirectory() as root:
            _build_two_item_tree(root)
            gen = _run_cli(["--root", root])
            self.assertEqual(gen.returncode, 0, gen.stderr)
            chk = _run_cli(["--check", "--root", root])
            self.assertEqual(chk.returncode, 0, chk.stdout + chk.stderr)

    def test_check_ignores_crlf_line_endings(self):
        """A core.autocrlf=true checkout on Windows hands back CRLF index files. The generator
        writes LF, so a byte-for-byte compare called every such checkout drifted until
        someone regenerated; a line-ending difference alone is not drift."""
        with tempfile.TemporaryDirectory() as root:
            _build_two_item_tree(root)
            gen = _run_cli(["--root", root])
            self.assertEqual(gen.returncode, 0, gen.stderr)

            top_index = os.path.join(root, "work", "index.md")
            with open(top_index, "rb") as f:
                lf = f.read()
            self.assertNotIn(b"\r\n", lf)
            with open(top_index, "wb") as f:
                f.write(lf.replace(b"\n", b"\r\n"))

            chk = _run_cli(["--check", "--root", root])
            self.assertEqual(chk.returncode, 0, chk.stdout + chk.stderr)

    def test_check_fails_after_hand_edit_and_names_the_file(self):
        with tempfile.TemporaryDirectory() as root:
            _build_two_item_tree(root)
            gen = _run_cli(["--root", root])
            self.assertEqual(gen.returncode, 0, gen.stderr)

            top_index = os.path.join(root, "work", "index.md")
            with open(top_index, "a", encoding="utf-8") as f:
                f.write("hand-edited\n")

            chk = _run_cli(["--check", "--root", root])
            self.assertEqual(chk.returncode, 1)
            self.assertIn("work/index.md", chk.stdout)

    def test_check_reports_missing_file(self):
        with tempfile.TemporaryDirectory() as root:
            _build_two_item_tree(root)
            gen = _run_cli(["--root", root])
            self.assertEqual(gen.returncode, 0, gen.stderr)

            os.remove(os.path.join(root, "work", "alpha", "index.md"))

            chk = _run_cli(["--check", "--root", root])
            self.assertEqual(chk.returncode, 1)
            self.assertIn(os.path.join("work", "alpha", "index.md"), chk.stdout)
            self.assertIn("missing", chk.stdout)


class MissingArtifacts(unittest.TestCase):
    def test_description_with_colon_is_quoted_and_round_trips(self):
        # work/delegated-mode: an intent description holding `: ` was rendered as a plain scalar,
        # which PyYAML reads as a nested mapping, so scripts/checks/front-matter.sh went red on the
        # generated index. Quoted on the way out, read back unchanged by both readers.
        desc = "Add a mode: the owner grants once, the agent signs the rest; see #40"
        with tempfile.TemporaryDirectory() as root:
            _write(
                os.path.join(root, "work", "colon", "intent.md"),
                textwrap.dedent(
                    f"""\
                    ---
                    type: sdlc/intent
                    id: colon
                    title: Colon item
                    description: "{desc}"
                    status: draft
                    ---
                    # Intent: colon
                    """
                ),
            )
            rendered = gen_index.render_item_index(gen_index.build_item(root, "colon"))
            self.assertIn(f'description: "{desc}"\n', rendered)
            self.assertEqual(gen_index.cac.front_matter_text(rendered)["description"], desc)
            try:
                import yaml  # noqa: F401
            except ImportError:
                return
            block = rendered.split("---\n")[1]
            self.assertEqual(yaml.safe_load(block)["description"], desc)
        for plain in ("Do the alpha thing", "a #1 priority", "x: y"):
            self.assertEqual(gen_index._yaml_scalar(plain).startswith('"'), ": " in plain or " #" in plain)

    def test_missing_intent_falls_back_to_slug_title(self):
        with tempfile.TemporaryDirectory() as root:
            _write(
                os.path.join(root, "work", "no-intent", "spec.md"),
                textwrap.dedent(
                    """\
                    ---
                    type: sdlc/spec
                    id: no-intent
                    status: draft
                    ---
                    # Spec only
                    """
                ),
            )
            item = gen_index.build_item(root, "no-intent")
            self.assertIsNone(item["fms"]["intent.md"])
            self.assertEqual(item["title"], "no-intent")
            self.assertEqual(item["description"], "")
            self.assertEqual(item["timestamp"], gen_index.DEFAULT_TIMESTAMP)
            self.assertIsNone(item["last_entry"])

            rendered = gen_index.render_item_index(item)
            self.assertNotIn("intent.md](intent.md)", rendered)
            self.assertIn("spec.md](spec.md)", rendered)
            self.assertIn("Last gate: —", rendered)

    def test_empty_item_directory_does_not_crash(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "work", "empty"))
            item = gen_index.build_item(root, "empty")
            self.assertEqual(item["title"], "empty")
            self.assertEqual(item["timestamp"], gen_index.DEFAULT_TIMESTAMP)
            rendered = gen_index.render_item_index(item)
            self.assertIn("Last gate: —", rendered)


class UnicodeAndEscaping(unittest.TestCase):
    def test_unicode_title_survives(self):
        with tempfile.TemporaryDirectory() as root:
            _write(
                os.path.join(root, "work", "uni", "intent.md"),
                textwrap.dedent(
                    """\
                    ---
                    type: sdlc/intent
                    id: uni
                    title: Ãœbersicht — café résumé 日本語
                    status: draft
                    ---
                    # placeholder
                    """
                ),
            )
            item = gen_index.build_item(root, "uni")
            self.assertEqual(item["title"], "Ãœbersicht — café résumé 日本語")

            outputs = _outputs_by_path(gen_index.render_all(root))
            item_content = outputs[os.path.join("work", "uni", "index.md")]
            self.assertIn("Ãœbersicht — café résumé 日本語", item_content)
            top_content = outputs["work/index.md"]
            self.assertIn("Ãœbersicht — café résumé 日本語", top_content)

            # round-trips through disk as UTF-8
            gen = _run_cli(["--root", root])
            self.assertEqual(gen.returncode, 0, gen.stderr)
            with open(os.path.join(root, "work", "uni", "index.md"), encoding="utf-8") as f:
                on_disk = f.read()
            self.assertIn("Ãœbersicht — café résumé 日本語", on_disk)

    def test_title_containing_pipe_is_escaped_in_table(self):
        with tempfile.TemporaryDirectory() as root:
            _write(
                os.path.join(root, "work", "piped", "intent.md"),
                textwrap.dedent(
                    """\
                    ---
                    type: sdlc/intent
                    id: piped
                    title: Before | After
                    status: draft
                    ---
                    # placeholder
                    """
                ),
            )
            outputs = _outputs_by_path(gen_index.render_all(root))
            top_content = outputs["work/index.md"]
            self.assertIn("Before \\| After", top_content)
            # the row still has exactly 8 unescaped '|' column separators
            row = next(
                line for line in top_content.splitlines() if line.startswith("| [piped]")
            )
            unescaped_pipes = row.replace("\\|", "").count("|")
            self.assertEqual(unescaped_pipes, 8)


if __name__ == "__main__":
    unittest.main()
