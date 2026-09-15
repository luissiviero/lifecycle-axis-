"""The advance regenerates exactly the indexes it dirties (work/self-check-false-reds R7, R8;
spec D5, D6).

`delegated_merge.advance` appends a ledger line to the merged item and to the next one, so
`work/<merged>/index.md`, `work/<next>/index.md` and `work/index.md` drift the moment it commits
-- `INDEX: 2 file(s) drifted` on `main` at 4eb8383, healed only by the owner's next tap. The fix
renders through `gen_index.render_all`, the one spelling of an index, but writes only those three
paths: `render_all` is repo-wide (29 paths today), and extending the `written` allowlist with all
of them would let an unrelated stale index ride an unattended bot commit.

Composes scripts/test_delegated_merge_advance.py's `MovingRemote` fixture by subclassing, the way
test_park_advance.py composes test_delegated_merge's `Advance`: a real repository, a real bare
remote, and a second clone that moves the remote between the checkout and the advance, as the
merge API does. New module: `kind: fix`. `build_item` reads `.sdlc/approvers.yaml` through
`next_item.resumers`, so the fixture copies the real one in, as test_check_artifact_chain's
`_make_repo` does.

Red before the fix: `test_advance_regenerates_exactly_what_it_dirties` -- the merged item's index
still carries the ledger's previous last line. `test_the_allowlist_is_still_closed` is green today
and pins the refusal at delegated_merge.py's `staged - written` check, reached here through a
stray path staged *after* the clean-tree precondition rather than asserted on the source text.
"""
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import delegated_merge as dm  # noqa: E402
import gen_index  # noqa: E402
import test_check_artifact_chain as chain_tests  # noqa: E402  (REAL_APPROVERS)
import test_delegated_merge as base  # noqa: E402
import test_delegated_merge_advance as adv  # noqa: E402

TOUCHED = ("work/merged-item/index.md", "work/next-item/index.md", "work/index.md")
UNTOUCHED = "work/later-item/index.md"
STALE = "stale line planted by the test; the advance did not dirty this item and must not touch it\n"
STRAY = "scripts/smuggled.py"


class RegeneratesIndex(adv.MovingRemote):
    def setUp(self):
        super().setUp()
        with open(chain_tests.REAL_APPROVERS, encoding="utf-8") as f:
            base._write(os.path.join(self.root, ".sdlc", "approvers.yaml"), f.read())
        # Every index rendered once, so there is zero drift before the advance; then one item the
        # advance never touches is made deliberately stale, to prove the write is scoped.
        for rel, content in gen_index.render_all(self.root):
            base._write(os.path.join(self.root, rel), content)
        base._write(os.path.join(self.root, UNTOUCHED), STALE)
        self._git("add", "-A")
        self._commit(self.root, "indexes")
        self._git("push", "-q", "origin", "main")
        # The second clone pushes the "merge"; it must start from this tip, not the fixture's.
        self._git("pull", "-q", "--ff-only", "origin", "main", cwd=self.other)

    def _read(self, rel):
        with open(os.path.join(self.root, rel), encoding="utf-8") as f:
            return f.read()

    # -- R7 -------------------------------------------------------------------------------------
    def test_advance_regenerates_exactly_what_it_dirties(self):
        merge_sha = self._move_remote()
        result = dm.advance(self.root, self.out, "merged-item", 12, self.policy, merge_sha=merge_sha)
        self.assertEqual(result, "next-item", self.out.stream.getvalue())
        rendered = dict(gen_index.render_all(self.root))
        for rel in TOUCHED:
            self.assertEqual(self._read(rel), rendered[rel], "%s drifted after the advance" % rel)
        self.assertEqual(self._read(UNTOUCHED), STALE, "an index the advance did not dirty was rewritten")
        committed = sorted(self._git("show", "--name-only", "--format=", "HEAD").splitlines())
        self.assertEqual(committed, sorted([".sdlc/active", "work/merged-item/log.md",
                                            "work/next-item/log.md", *TOUCHED]))
        self.assertEqual(self._remote_tip(), self._git("rev-parse", "HEAD"), "the advance was not pushed")

    # -- R8 -------------------------------------------------------------------------------------
    def test_the_allowlist_is_still_closed(self):
        merge_sha = self._move_remote()
        real_append = dm._append_ledger
        root = self.root

        def append_then_smuggle(*args, **kwargs):
            # The real ledger line, then a stray path staged behind the clean-tree check's back:
            # the only way anything outside the allowlist can reach `git diff --cached`.
            rel = real_append(*args, **kwargs)
            base._write(os.path.join(root, STRAY), "print('x')\n")
            self._git("add", "--", STRAY)
            return rel

        with mock.patch.object(dm, "_append_ledger", side_effect=append_then_smuggle):
            with self.assertRaises(dm.MergeError) as raised:
                dm.advance(self.root, self.out, "merged-item", 12, self.policy, merge_sha=merge_sha)
        self.assertIn("outside the advance allowlist", str(raised.exception))
        self.assertIn(STRAY, str(raised.exception))
        self.assertEqual(self._git("diff", "--cached", "--name-only"), "", "the refusal left paths staged")
        # advance() fast-forwards onto the merge commit before it writes anything, so the merge
        # commit is the tip a refusal must leave behind: nothing committed on top, nothing pushed.
        self.assertEqual(self._git("rev-parse", "HEAD"), merge_sha, "the refusal still committed")
        self.assertEqual(self._remote_tip(), merge_sha, "the refusal still pushed")


if __name__ == "__main__":
    unittest.main()
