"""Tests for scripts/check_detour.py (work/risk-detour R-2).

Written from the spec's R-2 row and Interfaces section before the script exists, so every case here
is expected to fail today (`ModuleNotFoundError`) and to pass once check_detour.py ships.

Fixtures carry their own identity and time (knowledge/lessons/tests-carry-their-own-environment.md):
every root here writes its own `.sdlc/config.env` and `.sdlc/delegation.yaml`, and the `--diff` cases
build a throwaway git repository with the fixture's own committer.
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_detour as cd  # noqa: E402
import delegated_merge as dm  # noqa: E402

SCRIPT = os.path.join(HERE, "check_detour.py")

CONFIG = """\
PROTECTED_PATHS=".claude/hooks .sdlc scripts/verify.sh"
RELEASE_GATED_PATHS="migrations infra"
GENERATED_PATHS="work/index.md"
"""

POLICY = """\
enabled: true
agents: [claude, claude[bot]]
signable: [spec.md, plan.md, incident.md]
risk-classes: [low]
max-deviations: 5
revisions: consensus
min-reviewers: 2
locked-paths: [scripts/sign.py, REVIEW.md, docs/sdlc/handoff]
"""

PLAN = """\
---
type: sdlc/plan
status: delegated
---
# Plan

## Files that change
- scripts/next_item.py — the queue rule
- docs/sdlc/templates/revision.md — the record
- work/*/index.md — regenerated
- scripts/nothing-here-*.py — a glob that matches nothing

## Release-gated
- migrations/0007.sql — owner: someone
"""


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _root(directory, config=CONFIG, policy=POLICY):
    _write(os.path.join(directory, ".sdlc", "config.env"), config)
    _write(os.path.join(directory, ".sdlc", "delegation.yaml"), policy)
    return directory


class Matching(unittest.TestCase):
    def test_every_locked_list_is_named(self):
        """One path per list; the label names the list(s) the matched prefix sits in, and the prefix
        is the one delegated_merge.check_locked_paths returned (spec D2: matching is the matcher's,
        labelling is a set lookup)."""
        with tempfile.TemporaryDirectory() as root:
            _root(root)
            hits = cd.locked([
                ".claude/hooks/require-plan.sh",      # PROTECTED_PATHS and ALWAYS_LOCKED (.claude)
                "migrations/0007.sql",                # RELEASE_GATED_PATHS
                "scripts/sign.py",                    # locked-paths
                "docs/sdlc/templates/revision.md",    # ALWAYS_LOCKED only
                "work/demo/intent.md",                # this item's intent
            ], root, slug="demo")
            by_path = {path: (labels, prefix) for path, labels, prefix in hits}
            self.assertEqual(set(by_path), {
                ".claude/hooks/require-plan.sh", "migrations/0007.sql", "scripts/sign.py",
                "docs/sdlc/templates/revision.md", "work/demo/intent.md"})
            self.assertEqual(by_path["migrations/0007.sql"], (["RELEASE_GATED_PATHS"], "migrations"))
            self.assertEqual(by_path["scripts/sign.py"], (["locked-paths"], "scripts/sign.py"))
            self.assertEqual(by_path["docs/sdlc/templates/revision.md"],
                             (["ALWAYS_LOCKED"], "docs/sdlc/templates"))
            self.assertEqual(by_path["work/demo/intent.md"],
                             (["this item's intent"], "work/demo/intent.md"))
            # .claude/hooks is a PROTECTED_PATHS entry and .claude is on the floor; the matcher returns
            # whichever prefix it meets first, and the label names every list that prefix is in.
            labels, prefix = by_path[".claude/hooks/require-plan.sh"]
            self.assertIn(prefix, (".claude/hooks", ".claude"))
            if prefix == ".claude":
                self.assertEqual(labels, ["ALWAYS_LOCKED"])
            else:
                self.assertEqual(labels, ["PROTECTED_PATHS"])
            self.assertIn(prefix, list(dm.ALWAYS_LOCKED) + [".claude/hooks"])

    def test_a_file_entry_never_matches_a_longer_name(self):
        """Prefix match on whole path segments, the merge script's own rule: `REVIEW.md.bak` is not
        `REVIEW.md`, and `scripts/verify.sh.orig` is not `scripts/verify.sh`."""
        with tempfile.TemporaryDirectory() as root:
            _root(root)
            self.assertEqual(cd.locked(["REVIEW.md.bak", "scripts/verify.sh.orig", "sdlc/x"], root), [])
            self.assertEqual([p for p, _, _ in cd.locked(["REVIEW.md"], root)], ["REVIEW.md"])

    def test_clean_paths_end_none_and_exit_zero(self):
        with tempfile.TemporaryDirectory() as root:
            _root(root)
            hits = cd.locked(["scripts/next_item.py", "knowledge/decisions/x.md", "work/demo/spec.md"],
                             root, slug="demo")
            self.assertEqual(hits, [])
            self.assertEqual(cd.verdict(hits), ("DETOUR: none", 0))
            self.assertEqual(cd.verdict([("a", ["ALWAYS_LOCKED"], ".claude")] * 3), ("DETOUR: needed (3)", 3))


class Sources(unittest.TestCase):
    def test_plan_bullets_are_read_from_files_that_change(self):
        """Every bullet under `## Files that change` up to the next `## `, the path before the first
        ` — `; a glob expands under the root, a glob matching nothing keeps its literal (spec R-2)."""
        with tempfile.TemporaryDirectory() as root:
            _root(root)
            _write(os.path.join(root, "work", "demo", "plan.md"), PLAN)
            _write(os.path.join(root, "work", "alpha", "index.md"), "x")
            _write(os.path.join(root, "work", "beta", "index.md"), "x")
            paths = cd.plan_paths(os.path.join(root, "work", "demo", "plan.md"), root)
            self.assertEqual(paths, [
                "scripts/next_item.py", "docs/sdlc/templates/revision.md",
                "work/alpha/index.md", "work/beta/index.md", "scripts/nothing-here-*.py"])
            # The release-gated bullet is not under the heading, so it is not a candidate here.
            self.assertNotIn("migrations/0007.sql", paths)

    def test_diff_names_both_sides_of_a_rename(self):
        """`git diff --name-status -M base...HEAD`: a rename is two candidates, since the merge
        script checks `previous_filename` too (a renamed REVIEW.md empties a judging surface)."""
        with tempfile.TemporaryDirectory() as root:
            _root(root)
            git = lambda *a: subprocess.run(["git", "-C", root, *a], check=True,  # noqa: E731
                                            capture_output=True, text=True).stdout.strip()
            git("init", "-q", "-b", "main")
            _write(os.path.join(root, "REVIEW.md"), "review\n")
            _write(os.path.join(root, "notes.md"), "notes\n")
            git("add", "-A")
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.com", "commit", "-q", "-m", "base")
            base = git("rev-parse", "HEAD")
            git("mv", "REVIEW.md", "renamed.md")
            _write(os.path.join(root, "scripts", "new_tool.py"), "print(1)\n")
            git("add", "-A")
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.com", "commit", "-q", "-m", "change")
            paths = cd.diff_paths(root, base)
            self.assertEqual(sorted(paths), ["REVIEW.md", "renamed.md", "scripts/new_tool.py"])
            hits = cd.locked(paths, root)
            self.assertEqual([p for p, _, _ in hits], ["REVIEW.md"])


class Cli(unittest.TestCase):
    def _run(self, root, *args):
        return subprocess.run([sys.executable, SCRIPT, "--root", root, *args],
                              capture_output=True, text=True)

    def test_needed_exits_three_and_counts(self):
        with tempfile.TemporaryDirectory() as root:
            _root(root)
            r = self._run(root, "--paths", "scripts/next_item.py", ".sdlc/active", "REVIEW.md")
            self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
            lines = r.stdout.strip().splitlines()
            self.assertEqual(lines[-1], "DETOUR: needed (2)")
            self.assertEqual(lines[0], ".sdlc/active: locked by PROTECTED_PATHS, ALWAYS_LOCKED '.sdlc'")
            self.assertEqual(lines[1], "REVIEW.md: locked by locked-paths, ALWAYS_LOCKED 'REVIEW.md'")
            clean = self._run(root, "--paths", "scripts/next_item.py")
            self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
            self.assertEqual(clean.stdout.strip(), "DETOUR: none")

    def test_bad_input_exits_two(self):
        """No source, two sources, a plan without the heading, a base git cannot resolve: exit 2 with
        a `check-detour:` line on stderr and no `DETOUR:` line, so silence never reads as clean."""
        with tempfile.TemporaryDirectory() as root:
            _root(root)
            _write(os.path.join(root, "work", "demo", "plan.md"), "---\ntype: sdlc/plan\n---\n# no heading\n")
            cases = [
                (),
                ("--paths", "a", "--plan", "work/demo/plan.md"),
                ("--plan", "work/demo/plan.md"),
                ("--plan", "work/demo/missing.md"),
                ("--diff", "no-such-ref"),
            ]
            for args in cases:
                r = self._run(root, *args)
                self.assertEqual(r.returncode, 2, "%r: %s%s" % (args, r.stdout, r.stderr))
                self.assertNotIn("DETOUR:", r.stdout, args)
                self.assertIn("check-detour:", r.stderr, args)


if __name__ == "__main__":
    unittest.main()
