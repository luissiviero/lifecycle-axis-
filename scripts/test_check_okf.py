import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
CHECK_OKF = os.path.join(HERE, "check_okf.py")

sys.path.insert(0, HERE)
import check_okf  # noqa: E402


def _write(root, rel, content):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


CONFORMING = (
    "---\n"
    "type: doc\n"
    "title: T\n"
    "description: D\n"
    "timestamp: 2026-01-01T00:00:00Z\n"
    "---\n"
    "body\n"
)


def _run(root, *args):
    return subprocess.run(
        [sys.executable, CHECK_OKF, "--root", root, *args],
        capture_output=True,
        text=True,
    )


def _last_line(text):
    lines = [l for l in text.splitlines() if l.strip()]
    return lines[-1] if lines else ""


class ConformingDoc(unittest.TestCase):
    def test_conforming_doc_with_index_is_clean(self):
        with tempfile.TemporaryDirectory() as root:
            _write(root, "a.md", CONFORMING)
            _write(root, "index.md", CONFORMING)
            result = _run(root, root)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(_last_line(result.stdout), "OKF: 2 docs, 0 warnings")


class MissingType(unittest.TestCase):
    def test_no_front_matter_is_one_warning(self):
        with tempfile.TemporaryDirectory() as root:
            _write(root, "index.md", CONFORMING)
            _write(root, "a.md", "no front matter here\n")
            result = _run(root, root)
            self.assertEqual(result.returncode, 0)
            lines = [l for l in result.stdout.splitlines() if l.startswith("WARN")]
            self.assertEqual(len(lines), 1)
            self.assertIn("a.md type", lines[0])
            self.assertEqual(_last_line(result.stdout), "OKF: 2 docs, 1 warnings")

    def test_missing_type_is_strict_failure(self):
        with tempfile.TemporaryDirectory() as root:
            _write(root, "index.md", CONFORMING)
            _write(root, "a.md", "no front matter here\n")
            result = _run(root, "--strict", root)
            self.assertEqual(result.returncode, 1)

    def test_missing_type_is_non_strict_pass(self):
        with tempfile.TemporaryDirectory() as root:
            _write(root, "index.md", CONFORMING)
            _write(root, "a.md", "no front matter here\n")
            result = _run(root, root)
            self.assertEqual(result.returncode, 0)

    def test_front_matter_present_but_type_empty_is_still_one_type_warning(self):
        # title/description/timestamp are present, so only the type rule fires.
        doc = "---\ntitle: T\ndescription: D\ntimestamp: 2026-01-01T00:00:00Z\n---\nbody\n"
        with tempfile.TemporaryDirectory() as root:
            _write(root, "index.md", CONFORMING)
            _write(root, "a.md", doc)
            result = _run(root, root)
            lines = [l for l in result.stdout.splitlines() if l.startswith("WARN")]
            self.assertEqual(len(lines), 1)
            self.assertIn("a.md type", lines[0])


class BadTimestamp(unittest.TestCase):
    def test_unparseable_timestamp_warns(self):
        doc = "---\ntype: doc\ntitle: T\ndescription: D\ntimestamp: not-a-date\n---\nbody\n"
        with tempfile.TemporaryDirectory() as root:
            _write(root, "index.md", CONFORMING)
            _write(root, "a.md", doc)
            result = _run(root, root)
            lines = [l for l in result.stdout.splitlines() if l.startswith("WARN")]
            self.assertEqual(len(lines), 1)
            self.assertIn("a.md timestamp", lines[0])

    def test_z_suffix_timestamp_is_accepted(self):
        with tempfile.TemporaryDirectory() as root:
            _write(root, "index.md", CONFORMING)
            _write(root, "a.md", CONFORMING)
            result = _run(root, root)
            self.assertEqual(_last_line(result.stdout), "OKF: 2 docs, 0 warnings")


class BrokenLink(unittest.TestCase):
    def test_broken_relative_link_names_target(self):
        doc = (
            "---\ntype: doc\ntitle: T\ndescription: D\ntimestamp: 2026-01-01T00:00:00Z\n---\n"
            "See [broken](missing.md) for details.\n"
        )
        with tempfile.TemporaryDirectory() as root:
            _write(root, "index.md", CONFORMING)
            _write(root, "a.md", doc)
            result = _run(root, root)
            lines = [l for l in result.stdout.splitlines() if l.startswith("WARN")]
            self.assertEqual(len(lines), 1)
            self.assertIn("link", lines[0])
            self.assertIn("missing.md", lines[0])

    def test_external_link_is_ignored(self):
        doc = (
            "---\ntype: doc\ntitle: T\ndescription: D\ntimestamp: 2026-01-01T00:00:00Z\n---\n"
            "See [ext](https://example.com/x) and [mail](mailto:a@example.com) and [frag](#section).\n"
        )
        with tempfile.TemporaryDirectory() as root:
            _write(root, "index.md", CONFORMING)
            _write(root, "a.md", doc)
            result = _run(root, root)
            self.assertEqual(_last_line(result.stdout), "OKF: 2 docs, 0 warnings")

    def test_valid_relative_link_resolves(self):
        doc = (
            "---\ntype: doc\ntitle: T\ndescription: D\ntimestamp: 2026-01-01T00:00:00Z\n---\n"
            "See [other](other.md) and [dir](sub/).\n"
        )
        with tempfile.TemporaryDirectory() as root:
            _write(root, "index.md", CONFORMING)
            _write(root, "a.md", doc)
            _write(root, "other.md", CONFORMING)
            os.makedirs(os.path.join(root, "sub"), exist_ok=True)
            result = _run(root, root)
            self.assertEqual(_last_line(result.stdout), "OKF: 3 docs, 0 warnings")


class MissingIndex(unittest.TestCase):
    def test_dir_with_md_and_no_index_warns(self):
        with tempfile.TemporaryDirectory() as root:
            _write(root, "sub/a.md", CONFORMING)
            result = _run(root, root)
            lines = [l for l in result.stdout.splitlines() if l.startswith("WARN")]
            self.assertEqual(len(lines), 1)
            self.assertIn("index", lines[0])
            self.assertTrue(lines[0].startswith("WARN sub "))


class FencedCodeBlockFirst(unittest.TestCase):
    def test_doc_starting_with_fence_is_not_front_matter(self):
        doc = "```\ntype: doc\n---\n```\nbody\n"
        with tempfile.TemporaryDirectory() as root:
            _write(root, "index.md", CONFORMING)
            _write(root, "a.md", doc)
            result = _run(root, root)
            lines = [l for l in result.stdout.splitlines() if l.startswith("WARN")]
            self.assertEqual(len(lines), 1)
            self.assertIn("a.md type", lines[0])

    def test_front_matter_second_dashes_is_the_boundary(self):
        # front_matter() (imported from check_artifact_chain) stops at the
        # SECOND '---' line: confirm the parser itself, not just the CLI.
        with tempfile.TemporaryDirectory() as root:
            path = _write(
                root,
                "a.md",
                "---\ntype: doc\n---\nnot-a-key: not-parsed-as-front-matter\n",
            )
            fm = check_okf.cac.front_matter(path)
            self.assertEqual(fm, {"type": "doc"})
            self.assertNotIn("not-a-key", fm)


class DeterministicSort(unittest.TestCase):
    def test_findings_sorted_by_path_then_rule(self):
        with tempfile.TemporaryDirectory() as root:
            _write(root, "index.md", CONFORMING)
            _write(root, "z.md", "no front matter\n")
            _write(root, "a.md", "no front matter\n")
            result = _run(root, root)
            warn_lines = [l for l in result.stdout.splitlines() if l.startswith("WARN")]
            self.assertEqual(warn_lines, sorted(warn_lines))
            self.assertTrue(warn_lines[0].startswith("WARN a.md"))
            self.assertTrue(warn_lines[1].startswith("WARN z.md"))


class RealRepo(unittest.TestCase):
    def test_real_repo_exits_zero_non_strict(self):
        # docs/sdlc has no front matter yet, so warnings are expected today;
        # the repo's own OKF_STRICT=0 in .sdlc/config.env means that must
        # not fail the build.
        result = subprocess.run(
            [sys.executable, CHECK_OKF, "--root", REPO_ROOT],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertRegex(_last_line(result.stdout), r"^OKF: \d+ docs, \d+ warnings$")


if __name__ == "__main__":
    unittest.main()
