"""Tests for scripts/approve_dispatch.py: the role gate and the committer of the dispatch route."""
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import approve_dispatch  # noqa: E402
import gen_index  # noqa: E402

GEN_INDEX = os.path.join(HERE, "gen_index.py")

IDENTITY = "luissiviero <69210737+luissiviero@users.noreply.github.com>"


def make_repo(slug="demo"):
    root = tempfile.mkdtemp()
    subprocess.run(["git", "init", "-q", "-b", "main", root], check=True)
    subprocess.run(["git", "-C", root, "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", root, "config", "user.name", "tester"], check=True)
    os.makedirs(os.path.join(root, ".sdlc"))
    os.makedirs(os.path.join(root, "work", slug))
    shutil.copy(os.path.join(REPO, ".sdlc", "approvers.yaml"),
                os.path.join(root, ".sdlc", "approvers.yaml"))
    # Another item is active, so a test that exercises --activate produces a real change.
    with open(os.path.join(root, ".sdlc", "active"), "w") as f:
        f.write("_example\n")
    with open(os.path.join(root, "work", slug, "intent.md"), "w") as f:
        f.write("---\nstatus: in-review\n---\n# Demo\n")
    subprocess.run(["git", "-C", root, "add", "-A"], check=True)
    subprocess.run(["git", "-C", root, "commit", "-q", "-m", "init"], check=True)
    return root


def write(root, rel, text):
    path = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def add_other_item(root, stale_index=True):
    """A second, committed work item whose index the approval of `demo` may not write by hand.

    Every index is rendered up to date first, then `work/other/index.md` alone is overwritten with
    stale text, so the tree has exactly one drifted index: the shape of main after a tap
    (work/approve-tap-regenerates-index, spec R-2). Committed with the fixture's own identity,
    which make_repo set (knowledge/lessons/tests-carry-their-own-environment.md).
    """
    write(root, "work/other/intent.md", "---\nstatus: in-review\ntitle: Other\n---\n# Other\n")
    for rel, content in gen_index.render_all(root):
        write(root, rel, content)
    if stale_index:
        write(root, "work/other/index.md", "# stale\n")
    subprocess.run(["git", "-C", root, "add", "-A"], check=True)
    subprocess.run(["git", "-C", root, "commit", "-q", "-m", "other item"], check=True)


class ActorCheck(unittest.TestCase):
    """R-2: the run refuses before it writes, and says why."""

    def setUp(self):
        self.root = make_repo()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def check(self, login, artifact="intent.md", **kw):
        return approve_dispatch.check_actor(login, artifact, root=self.root, **kw)

    def test_role_holder_passes(self):
        ok, reason = self.check("luissiviero")
        self.assertTrue(ok, reason)

    def test_handle_outside_the_role_is_refused(self):
        ok, reason = self.check("someone-else")
        self.assertFalse(ok)
        self.assertIn("someone-else", reason)

    def test_never_approve_handle_is_refused(self):
        ok, reason = self.check("claude[bot]")
        self.assertFalse(ok)
        self.assertIn("agent identities cannot approve", reason)

    def test_empty_actor_is_refused(self):
        ok, reason = self.check("")
        self.assertFalse(ok)
        self.assertIn("empty approver", reason)

    def test_placeholder_is_refused(self):
        ok, reason = self.check("<your-handle>")
        self.assertFalse(ok)
        self.assertIn("placeholder", reason)

    def test_cli_exits_1_and_prints_the_reason(self):
        r = subprocess.run(
            [sys.executable, os.path.join(HERE, "approve_dispatch.py"),
             "--check-actor", "someone-else", "--artifact", "intent.md", "--root", self.root],
            capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("may not approve", r.stderr)
        self.assertNotIn("ok", r.stdout)

    def test_cli_prints_ok_for_a_role_holder(self):
        r = subprocess.run(
            [sys.executable, os.path.join(HERE, "approve_dispatch.py"),
             "--check-actor", "luissiviero", "--artifact", "intent.md", "--root", self.root],
            capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "ok")


class Mode(unittest.TestCase):
    """R-8: a delegation grant lands on the default branch or nowhere."""

    def setUp(self):
        self.root = make_repo()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def check(self, **kw):
        kw.setdefault("artifact", "intent.md")
        artifact = kw.pop("artifact")
        return approve_dispatch.check_actor("luissiviero", artifact, root=self.root, **kw)

    def test_delegated_on_a_side_branch_is_refused_naming_the_ref(self):
        ok, reason = self.check(mode="delegated", ref="work/demo", default_branch="main")
        self.assertFalse(ok)
        self.assertIn("work/demo", reason)
        self.assertIn("default branch", reason)

    def test_delegated_on_the_default_branch_passes(self):
        for ref in ("main", "refs/heads/main"):
            ok, reason = self.check(mode="delegated", ref=ref, default_branch="main")
            self.assertTrue(ok, f"{ref}: {reason}")

    def test_supervised_proceeds_on_any_ref(self):
        ok, reason = self.check(mode="supervised", ref="work/demo", default_branch="main")
        self.assertTrue(ok, reason)

    def test_delegated_on_a_non_intent_artifact_is_refused(self):
        ok, reason = self.check(artifact="spec.md", mode="delegated", ref="main",
                                default_branch="main")
        self.assertFalse(ok)
        self.assertIn("intent.md", reason)

    def test_delegated_with_no_default_branch_is_refused(self):
        ok, reason = self.check(mode="delegated", ref="main")
        self.assertFalse(ok)
        self.assertIn("default branch", reason)

    def test_the_workflow_requires_an_explicit_slug_for_a_grant(self):
        """Security pass on pull request 51: `run-name` can only interpolate the raw input, and
        route B binds the grant to the run-name. A grant dispatched with a blank slug would produce
        an empty slug segment there and be refused at merge time."""
        wf = os.path.join(REPO, ".github", "workflows", "approve.yml")
        with open(wf, encoding="utf-8") as f:
            text = f.read()
        self.assertIn('[ -z "$slug" ] && [ "$MODE" = delegated ]', text)
        self.assertIn("must name its slug explicitly", text)


class SlugContainment(unittest.TestCase):
    """Security pass on pull request 51: the workflow's `tr -cd 'A-Za-z0-9._-'` keeps dots, so `..`
    reaches the script intact and would make work/<slug>/ resolve to the repository root."""

    def setUp(self):
        self.root = make_repo()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_allowed_paths_refuses_a_traversing_slug(self):
        for bad in ("..", ".", "../..", ".git", "..hidden"):
            with self.assertRaises(SystemExit, msg=bad):
                approve_dispatch.allowed_paths(bad)

    def test_allowed_paths_accepts_a_normal_slug(self):
        for good in ("demo", "approve-by-dispatch", "item_1", "v1.2"):
            paths = approve_dispatch.allowed_paths(good)
            self.assertIn("work/%s/intent.md" % good, paths)

    def test_allowed_paths_never_escapes_the_work_directory(self):
        for path in approve_dispatch.allowed_paths("demo"):
            self.assertTrue(path.startswith("work/demo/") or path == ".sdlc/active", path)

    def test_check_actor_refuses_a_traversing_slug(self):
        ok, reason = approve_dispatch.check_actor("luissiviero", "intent.md", root=self.root,
                                                  slug="..")
        self.assertFalse(ok)
        self.assertIn("work/<slug>/", reason)

    def test_check_actor_accepts_a_normal_slug(self):
        ok, reason = approve_dispatch.check_actor("luissiviero", "intent.md", root=self.root,
                                                  slug="demo")
        self.assertTrue(ok, reason)


class Commit(unittest.TestCase):
    """R-4: the trailers, the split identity, and the staged-path allowlist."""

    def setUp(self):
        self.root = make_repo()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def git(self, *args):
        return subprocess.run(["git", "-C", self.root, *args],
                              capture_output=True, text=True).stdout.strip()

    def approve_something(self):
        write(self.root, "work/demo/intent.md", "---\nstatus: approved\n---\n# Demo\n")
        write(self.root, "work/demo/log.md", "- ts | intent.md | in-review -> approved\n")

    def run_commit(self, **kw):
        kw.setdefault("artifact", "intent.md")
        return approve_dispatch.commit("demo", "luissiviero", "12345", root=self.root,
                                       identity=IDENTITY, **kw)

    def test_message_ends_with_both_trailers(self):
        self.approve_something()
        self.assertEqual(self.run_commit(), 0)
        body = self.git("log", "-1", "--format=%B").strip()
        self.assertTrue(body.endswith("Approved-Run: 12345\nApproved-Actor: luissiviero"), body)
        self.assertTrue(body.startswith("[demo] Approve intent.md as luissiviero"), body)

    def test_note_sits_above_the_trailers(self):
        self.approve_something()
        self.assertEqual(self.run_commit(note="looks right"), 0)
        body = self.git("log", "-1", "--format=%B").strip()
        self.assertIn("looks right", body)
        self.assertTrue(body.endswith("Approved-Actor: luissiviero"), body)

    def test_author_is_the_actor_and_committer_is_the_bot(self):
        self.approve_something()
        self.assertEqual(self.run_commit(), 0)
        self.assertEqual(self.git("log", "-1", "--format=%an"), "luissiviero")
        self.assertEqual(self.git("log", "-1", "--format=%ae"),
                         "69210737+luissiviero@users.noreply.github.com")
        self.assertEqual(self.git("log", "-1", "--format=%cn"), approve_dispatch.BOT_NAME)
        self.assertEqual(self.git("log", "-1", "--format=%ce"), approve_dispatch.BOT_EMAIL)

    def test_a_stray_path_aborts_the_commit(self):
        self.approve_something()
        write(self.root, "scripts/sneaky.py", "print('hi')\n")
        before = self.git("rev-parse", "HEAD")
        self.assertEqual(self.run_commit(), 1)
        self.assertEqual(self.git("rev-parse", "HEAD"), before)

    def test_a_stray_path_is_named_in_the_refusal(self):
        self.approve_something()
        write(self.root, "scripts/sneaky.py", "print('hi')\n")
        self.assertEqual(approve_dispatch.unexpected_paths("demo", root=self.root),
                         ["scripts/sneaky.py"])

    def test_active_and_index_are_allowed(self):
        self.approve_something()
        write(self.root, ".sdlc/active", "demo\n")
        write(self.root, "work/demo/index.md", "# index\n")
        self.assertEqual(self.run_commit(), 0)
        names = self.git("show", "--name-only", "--format=", "HEAD").split()
        self.assertIn(".sdlc/active", names)
        self.assertIn("work/demo/index.md", names)

    def test_another_items_files_are_a_stray_path(self):
        self.approve_something()
        write(self.root, "work/other/intent.md", "---\nstatus: approved\n---\n")
        self.assertEqual(approve_dispatch.unexpected_paths("demo", root=self.root),
                         ["work/other/intent.md"])

    def test_nothing_to_stage_is_refused(self):
        self.assertEqual(self.run_commit(), 1)

    # --- work/approve-tap-regenerates-index: --commit regenerates the indexes before it judges the tree

    def run_commit_capturing(self, **kw):
        """run_commit with stdout and stderr captured; returns (rc, stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = self.run_commit(**kw)
        return rc, out.getvalue(), err.getvalue()

    def read(self, rel):
        with open(os.path.join(self.root, *rel.split("/")), "rb") as f:
            return f.read()

    def committed_names(self):
        return sorted(self.git("show", "--name-only", "--format=", "HEAD").split())

    def test_commit_regenerates_both_indexes(self):
        """R-1, R-8: the tap's commit carries both indexes, byte-identical to the generator's render,
        and the run log says which files were rewritten."""
        self.approve_something()
        rc, out, _ = self.run_commit_capturing()
        self.assertEqual(rc, 0)
        self.assertEqual(self.committed_names(),
                         ["work/demo/index.md", "work/demo/intent.md", "work/demo/log.md", "work/index.md"])
        self.assertEqual(self.git("status", "--porcelain"), "", "the commit left the tree dirty")
        want = dict(gen_index.render_all(self.root))
        for rel in ("work/demo/index.md", "work/index.md"):
            self.assertEqual(self.read(rel), want[rel].encode("utf-8"), rel)
        r = subprocess.run([sys.executable, GEN_INDEX, "--check", "--root", self.root],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("INDEX: up to date", r.stdout)
        self.assertIn("approve-dispatch: regenerated 2 index file(s): work/demo/index.md, work/index.md",
                      out)
        again = io.StringIO()
        with contextlib.redirect_stdout(again):
            self.assertEqual(approve_dispatch.regenerate(self.root), ([], []))
        self.assertIn("approve-dispatch: indexes already up to date", again.getvalue())

    def test_a_stale_index_of_another_item_is_committed_too(self):
        """R-2: a tap heals drift it finds; the other item's index is regenerated and committed."""
        add_other_item(self.root, stale_index=True)
        self.approve_something()
        rc, out, _ = self.run_commit_capturing(ref="main", default_branch="main")
        self.assertEqual(rc, 0)
        # The generator renders work/index.md last; sorted order puts it before work/other/index.md.
        self.assertIn("approve-dispatch: regenerated 3 index file(s): work/demo/index.md, "
                      "work/index.md, work/other/index.md", out)
        names = self.committed_names()
        self.assertIn("work/other/index.md", names)
        for rel in ("work/demo/index.md", "work/demo/intent.md", "work/demo/log.md", "work/index.md"):
            self.assertIn(rel, names)
        want = dict(gen_index.render_all(self.root))
        self.assertEqual(self.read("work/other/index.md"), want["work/other/index.md"].encode("utf-8"))
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_generated_indexes_of_any_item_are_allowed(self):
        """R-3, the positive half: every generated index passes the guard, whichever item it belongs to,
        including one whose directory name SLUG_RE would refuse as a slug (work/_example on main)."""
        add_other_item(self.root, stale_index=True)
        write(self.root, "work/other/index.md", "# regenerated\n")
        write(self.root, "work/_example/index.md", "# example\n")
        write(self.root, "work/index.md", "# top\n")
        self.assertEqual(approve_dispatch.unexpected_paths("demo", root=self.root, wide=True), [])

    def test_index_lookalikes_are_stray(self):
        """R-3, the negative half: the widening reaches exactly work/<dir>/index.md and work/index.md."""
        strays = ["index.md", "work/other/sub/index.md", "work/.hidden/index.md",
                  "work/other/index.md.orig", "work/other/intent.md"]
        for rel in strays:
            write(self.root, rel, "x\n")
        self.assertEqual(approve_dispatch.unexpected_paths("demo", root=self.root), sorted(strays))

    def test_a_stray_beside_regenerated_indexes_still_aborts(self):
        """R-4: regeneration does not mask a stray; the refusal names the stray and no index."""
        self.approve_something()
        write(self.root, "scripts/sneaky.py", "print('hi')\n")
        before = self.git("rev-parse", "HEAD")
        rc, _, err = self.run_commit_capturing()
        self.assertEqual(rc, 1)
        self.assertEqual(self.git("rev-parse", "HEAD"), before)
        self.assertIn("scripts/sneaky.py", err)
        self.assertNotIn("index.md", err)

    def test_index_only_changes_do_not_make_a_commit(self):
        """R-5, R-8: when the approval wrote nothing, a regenerated index alone is not a commit under
        approval trailers; the run log still says what was regenerated."""
        add_other_item(self.root, stale_index=True)
        before = self.git("rev-parse", "HEAD")
        rc, out, err = self.run_commit_capturing(ref="main", default_branch="main")
        self.assertEqual(rc, 1)
        self.assertEqual(self.git("rev-parse", "HEAD"), before)
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")
        self.assertIn("nothing staged", err)
        self.assertIn("only generated indexes changed: work/other/index.md", err)
        self.assertIn("approve-dispatch: regenerated 1 index file(s): work/other/index.md", out)

    # --- revision 1: the heal is scoped to the default branch, a rename is judged at both ends

    ROUTE_VARS = ("GITHUB_REF_NAME", "GITHUB_REF_TYPE", "GITHUB_EVENT_PATH")

    def test_on_another_ref_only_the_items_indexes_are_written(self):
        """R-2 narrow route, R-8: on a work branch the tap writes its own two indexes, leaves a
        foreign stale one untouched and unstaged, and says so."""
        add_other_item(self.root, stale_index=True)
        self.approve_something()
        rc, out, _ = self.run_commit_capturing(ref="work/demo", default_branch="main")
        self.assertEqual(rc, 0)
        self.assertEqual(self.committed_names(),
                         ["work/demo/index.md", "work/demo/intent.md", "work/demo/log.md", "work/index.md"])
        self.assertEqual(self.read("work/other/index.md"), b"# stale\n")
        self.assertEqual(self.git("status", "--porcelain"), "", "the foreign index was staged or changed")
        self.assertIn("approve-dispatch: left 1 stale index file(s) unwritten on this ref: "
                      "work/other/index.md", out)

    def test_a_foreign_index_is_a_stray_on_the_narrow_route(self):
        """R-3, spec D7: off the default branch a foreign index is a stray however it got dirty."""
        add_other_item(self.root, stale_index=True)
        write(self.root, "work/other/index.md", "# regenerated\n")
        write(self.root, "work/_example/index.md", "# example\n")
        write(self.root, "work/index.md", "# top\n")
        self.assertEqual(approve_dispatch.unexpected_paths("demo", root=self.root),
                         ["work/_example/index.md", "work/other/index.md"])

    def test_a_traversing_slug_is_refused_on_a_clean_tree(self):
        """R-3: the slug is validated before any path is judged, so a clean tree changes nothing.
        Green since f8b0e1d; mutation-tested red by removing the up-front allowed_paths call."""
        self.assertEqual(self.git("status", "--porcelain"), "")
        for bad in ("..", ".", ".git", "../x"):
            with self.assertRaises(SystemExit, msg=bad):
                approve_dispatch.unexpected_paths(bad, root=self.root)

    def test_unknown_ref_takes_the_narrow_route(self):
        """R-11: with no ref given and none of the runner's variables set, the tap is narrow."""
        add_other_item(self.root, stale_index=True)
        self.approve_something()
        with mock.patch.dict(os.environ):
            for var in self.ROUTE_VARS:
                os.environ.pop(var, None)
            rc, out, _ = self.run_commit_capturing()
        self.assertEqual(rc, 0)
        self.assertNotIn("work/other/index.md", self.committed_names())
        self.assertIn("left 1 stale index file(s) unwritten on this ref: work/other/index.md", out)

    def test_a_malformed_event_payload_takes_the_narrow_route(self):
        """R-11: a missing, unparsable, wrong-shaped or null payload never raises; each is narrow."""
        payloads = {"missing": None, "not-json": "not json", "list": "[]",
                    "repo-not-object": '{"repository": 7}',
                    "null": '{"repository": {"default_branch": null}}',
                    "empty": '{"repository": {"default_branch": ""}}'}
        for label, payload in payloads.items():
            with self.subTest(payload=label):
                root = make_repo()
                outside = tempfile.mkdtemp()  # the payload lives outside the repo, as the runner's does
                try:
                    add_other_item(root, stale_index=True)
                    write(root, "work/demo/intent.md", "---\nstatus: approved\n---\n# Demo\n")
                    write(root, "work/demo/log.md", "- ts | intent.md | in-review -> approved\n")
                    event = os.path.join(outside, "event.json")
                    if payload is not None:
                        with open(event, "w", encoding="utf-8") as f:
                            f.write(payload)
                    with mock.patch.dict(os.environ, {"GITHUB_REF_NAME": "main",
                                                      "GITHUB_REF_TYPE": "branch",
                                                      "GITHUB_EVENT_PATH": event}):
                        out, err = io.StringIO(), io.StringIO()
                        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                            rc = approve_dispatch.commit("demo", "luissiviero", "12345", root=root,
                                                         identity=IDENTITY, artifact="intent.md")
                    self.assertEqual(rc, 0, err.getvalue())
                    names = subprocess.run(["git", "-C", root, "show", "--name-only", "--format=", "HEAD"],
                                           capture_output=True, text=True).stdout.split()
                    self.assertNotIn("work/other/index.md", names)
                    self.assertIn("left 1 stale index file(s) unwritten", out.getvalue())
                finally:
                    shutil.rmtree(root, ignore_errors=True)
                    shutil.rmtree(outside, ignore_errors=True)

    def test_a_rename_source_is_judged_too(self):
        """R-10: a staged rename whose source is outside the allowlist is a stray, even when its
        destination is a generated index the route allows."""
        subprocess.run(["git", "-C", self.root, "mv", ".sdlc/approvers.yaml", "work/demo/index.md"],
                       check=True)
        self.approve_something()
        before = self.git("rev-parse", "HEAD")
        rc, _, err = self.run_commit_capturing()
        self.assertEqual(rc, 1)
        self.assertEqual(self.git("rev-parse", "HEAD"), before)
        self.assertIn(".sdlc/approvers.yaml", err)

    def test_cli_threads_ref_and_default_branch_into_commit(self):
        """R-7: --commit has one spelling of "which ref": the parsed flags reach commit()."""
        with mock.patch.object(approve_dispatch, "commit", return_value=0) as m:
            rc = approve_dispatch.main(["--commit", "--actor", "luissiviero", "--run-id", "1",
                                        "--slug", "demo", "--artifact", "intent.md",
                                        "--ref", "work/x", "--default-branch", "main",
                                        "--root", self.root])
        self.assertEqual(rc, 0)
        kw = m.call_args.kwargs
        self.assertEqual(kw.get("ref"), "work/x")
        self.assertEqual(kw.get("default_branch"), "main")


if __name__ == "__main__":
    unittest.main()
