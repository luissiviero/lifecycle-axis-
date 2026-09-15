"""The advance skips a parked item (work/risk-detour R-4).

Composes scripts/test_delegated_merge.py's `Advance` fixture -- a real repository with a real bare
remote, three granted items, `merged-item` already worked -- and parks `next-item`, the earlier of the
two unstarted ones, with the one ledger line a park is. `advance()` must then land on `later-item`,
write its two ledger lines there and on the merged item, leave the parked item's ledger byte-identical,
and commit once as the bot with no human commit between (spec R-4, D4).

Red before scripts/next_item.py reads the park: `advance()` returns `next-item`.

Fixtures carry their own identity and time (knowledge/lessons/tests-carry-their-own-environment.md);
the base class supplies the git identity and the fixture dates.
"""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import delegated_merge as dm  # noqa: E402
import log_ledger  # noqa: E402
import test_delegated_merge as base  # noqa: E402

PARK_LINE = ("- 2026-09-04T00:00:00Z | intent.md | approved -> approved | claude | 0abc123 | "
             "parked: revision 2: no low-only route around .claude/hooks; remainder: next-item-supervised\n")


class ParkAdvance(base.Advance):
    def setUp(self):
        super().setUp()
        path = os.path.join(self.root, "work", "next-item", "log.md")
        with open(path, "a", encoding="utf-8") as f:
            f.write(PARK_LINE)
        self._git("add", "-A")
        self._commit("park next-item")
        self._git("push", "-q", "origin", "main")
        with open(path, encoding="utf-8") as f:
            self.parked_ledger_before = f.read()

    def test_the_advance_skips_a_parked_item_and_lands_on_the_next(self):
        result = dm.advance(self.root, self.out, "merged-item", 14, self.policy)
        self.assertEqual(result, "later-item", self.out.stream.getvalue())
        self.assertEqual(self._pointer(), "later-item")
        self.assertIn("ADVANCE: .sdlc/active -> later-item", self.out.stream.getvalue())

        merged = log_ledger.parse(os.path.join(self.root, "work", "merged-item", "log.md"))[0][-1]
        self.assertIn(".sdlc/active advanced to later-item", merged.note)
        self.assertTrue(merged.note.startswith("merged as "), merged.note)
        landed = log_ledger.parse(os.path.join(self.root, "work", "later-item", "log.md"))[0][-1]
        self.assertIn(".sdlc/active advanced here after PR #14 merged", landed.note)
        self.assertEqual(landed.actor, "github-actions[bot]")
        self.assertEqual(self._log("next-item"), self.parked_ledger_before)

        # One commit by the bot after the fixture's own two, none by a human, and it is pushed.
        authors = self._git("log", "--format=%an").splitlines()
        self.assertEqual(authors, ["github-actions[bot]", "Fixture", "Fixture"])
        remote = subprocess.run(["git", "-C", self.remote, "log", "--format=%an", "main"],
                                capture_output=True, text=True).stdout.splitlines()
        self.assertEqual(remote, authors)


def load_tests(loader, tests, pattern):
    """Only this module's case: the base class's own cases are inherited by ParkAdvance and would
    otherwise run a second time under this module's name."""
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromName("test_the_advance_skips_a_parked_item_and_lands_on_the_next",
                                            ParkAdvance))
    return suite


if __name__ == "__main__":
    unittest.main()
