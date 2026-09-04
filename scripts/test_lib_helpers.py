"""Unit tests for the helpers in .claude/hooks/_lib.sh (work/control-plane-visibility, spec R-1,
R-2, R-8). Each test sources the real library in a `bash -c` subprocess with a crafted stdin,
the way scripts/test_gemini_wiring.py drives canon(), and CLAUDE_PROJECT_DIR pointing at a
fake repo from scripts/hooktest.py. Nothing here edits a hook or writes into this repo."""
import os
import re
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hooktest import HOOKS_DIR, fake_repo  # noqa: E402


def lib(call, root, stdin="{}", argv0="fakehook.sh"):
    """Source _lib.sh with `stdin` as the hook input, then run `call`; $0 is `argv0`."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("SDLC_") and k != "RELEASE_APPROVAL"}
    env["CLAUDE_PROJECT_DIR"] = root
    return subprocess.run(
        ["bash", "-c", '. "$1/_lib.sh"; ' + call, argv0, HOOKS_DIR],
        input=stdin, capture_output=True, text=True, env=env,
    )


def log_lines(root):
    path = os.path.join(root, ".sdlc", "hook-decisions.log")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return f.read().splitlines()


TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class InputFields(unittest.TestCase):
    def test_cwd_and_session_id_read_from_input(self):
        with fake_repo() as root:
            r = lib('printf "%s|%s" "$CWD" "$SESSION_ID"', root,
                    stdin='{"cwd":"C:\\\\repo\\\\sub","session_id":"abc"}')
            self.assertEqual(r.stdout, "C:/repo/sub|abc", r.stderr)
            r = lib('printf "%s|%s" "$CWD" "$SESSION_ID"', root, stdin="{}")
            self.assertEqual(r.stdout, "|", r.stderr)

    def test_file_falls_back_to_notebook_path(self):
        with fake_repo() as root:
            r = lib('printf "%s" "$FILE"', root,
                    stdin='{"tool_name":"NotebookEdit","tool_input":{"notebook_path":"nb/x.ipynb"}}')
            self.assertEqual(r.stdout, "nb/x.ipynb", r.stderr)
            r = lib('printf "%s" "$FILE"', root,
                    stdin='{"tool_name":"Edit","tool_input":{"file_path":"src/a.ts","notebook_path":"nb/x.ipynb"}}')
            self.assertEqual(r.stdout, "src/a.ts")
            r = lib('printf "%s" "$FILE"', root, stdin='{"tool_name":"Bash","tool_input":{"command":"ls"}}')
            self.assertEqual(r.stdout, "")

    def test_rel_resolves_relative_path_against_cwd(self):
        with fake_repo() as root:
            real = os.path.realpath(root)
            r = lib('rel a.ts', root, stdin='{"cwd":"%s/sub"}' % real)
            self.assertEqual(r.stdout, "sub/a.ts", r.stderr)
            r = lib('rel a.ts', root, stdin="{}")
            self.assertEqual(r.stdout, "a.ts")
            # An absolute path ignores cwd.
            r = lib('rel "%s/x/y"' % real, root, stdin='{"cwd":"%s/sub"}' % real)
            self.assertEqual(r.stdout, "x/y")


FM_FILE = (
    '---\r\nstatus: "Approved"   # note\r\nkind: fix\t# c\r\napproved-by:   # a human\r\n'
    "# status: nope\r\n---\r\nbody-only: x\r\nstatus: draft\r\n"
)


class FrontMatter(unittest.TestCase):
    def test_fm_value_strips_cr_comment_and_quotes(self):
        with fake_repo(**{"work/foo/plan.md": FM_FILE}) as root:
            f = os.path.join(root, "work", "foo", "plan.md")
            self.assertEqual(lib('fm_value "%s" status' % f, root).stdout.strip(), "approved")
            self.assertEqual(lib('fm_value "%s" kind' % f, root).stdout.strip(), "fix")
            self.assertEqual(lib('fm_value "%s" approved-by' % f, root).stdout.strip(), "")
            # Only the front matter is read without `any`; the body's status: draft is never seen.
            self.assertEqual(lib('fm_value "%s" body-only' % f, root).stdout.strip(), "")
            self.assertEqual(lib('fm_value "%s/missing.md" status' % root, root).stdout.strip(), "")

    def test_fm_value_any_reads_past_front_matter(self):
        with fake_repo(**{"work/foo/plan.md": FM_FILE}) as root:
            f = os.path.join(root, "work", "foo", "plan.md")
            self.assertEqual(lib('fm_value "%s" body-only any' % f, root).stdout.strip(), "x")
            # `-` reads stdin, the shape protect-approvals.sh will use on an Edit's new_string.
            r = lib("printf 'a: 1\\nstatus: Approved   # x\\n' | fm_value - status any", root)
            self.assertEqual(r.stdout.strip(), "approved", r.stderr)
            r = lib("printf 'status: approved\\n' | fm_value - status", root)
            self.assertEqual(r.stdout.strip(), "", "without `any` a text with no front matter has no values")


class Approvers(unittest.TestCase):
    def test_artifact_role_reads_approvers_file(self):
        with fake_repo() as root:
            self.assertEqual(lib("artifact_role plan.md", root).stdout.strip(), "tech-lead")
            self.assertEqual(lib("artifact_role intent.md", root).stdout.strip(), "product-owner")
            self.assertEqual(lib("artifact_role incident.md", root).stdout.strip(), "service-owner")
            self.assertEqual(lib("artifact_role readme.md", root).stdout.strip(), "")

    def test_approver_has_role_accepts_listed_handle(self):
        with fake_repo() as root:
            for handle in ("luissiviero", "@LuisSiviero (tech lead)", '"luissiviero"', "'luissiviero'"):
                r = lib('approver_has_role "%s" tech-lead; echo rc=$?' % handle, root)
                self.assertEqual(r.stdout.strip(), "rc=0", handle + r.stderr)
            r = lib('approver_has_role luissiviero release-manager; echo rc=$?', root)
            self.assertEqual(r.stdout.strip(), "rc=0")

    def test_approver_has_role_rejects_never_approve(self):
        with fake_repo() as root:
            for handle in ("claude", "@claude", "claude[bot]", "github-actions[bot]", "someone-else", ""):
                r = lib('approver_has_role "%s" tech-lead; echo rc=$?' % handle, root)
                self.assertEqual(r.stdout.strip(), "rc=1", handle)
            r = lib('approver_has_role luissiviero janitor; echo rc=$?', root)
            self.assertEqual(r.stdout.strip(), "rc=1", "unknown role")

    def test_approver_has_role_missing_file_fails_closed(self):
        with fake_repo() as root:
            os.remove(os.path.join(root, ".sdlc", "approvers.yaml"))
            r = lib('approver_has_role luissiviero tech-lead; echo rc=$?', root)
            self.assertEqual(r.stdout.strip(), "rc=1")


class DecisionLog(unittest.TestCase):
    def test_log_decision_appends_six_tab_fields(self):
        with fake_repo() as root:
            r = lib('log_decision block "why not"; echo rc=$?', root, stdin='{"tool_name":"Edit","session_id":"s1"}')
            self.assertEqual(r.stdout.strip(), "rc=0", r.stderr)
            lines = log_lines(root)
            self.assertEqual(len(lines), 1, lines)
            fields = lines[0].split("\t")
            self.assertEqual(len(fields), 6, fields)
            self.assertRegex(fields[0], TS_RE)
            self.assertEqual(fields[1:], ["block", "fakehook.sh", "Edit", "s1", "why not"])
            # Appends, and the verdict word is whatever the caller passes; block() and ask() use it.
            r = lib('block "boom"', root, stdin='{"tool_name":"Bash","session_id":"s2"}')
            self.assertEqual(r.returncode, 2)
            self.assertIn("boom", r.stderr)
            r = lib('ask "maybe"', root, stdin='{"tool_name":"Bash"}')
            self.assertEqual(r.returncode, 0)
            self.assertIn('"permissionDecision":"ask"', r.stdout.replace(" ", "").replace("\n", ""))
            lines = log_lines(root)
            self.assertEqual([l.split("\t")[1:5] for l in lines[1:]],
                             [["block", "fakehook.sh", "Bash", "s2"], ["ask", "fakehook.sh", "Bash", "?"]])

    def test_log_decision_failure_is_silent(self):
        with fake_repo() as root:
            # A directory at the log path makes every append fail, whatever user runs the tests
            # (a chmod would not stop root); a missing .sdlc/ is the adopter-before-adopt.sh case.
            os.makedirs(os.path.join(root, ".sdlc", "hook-decisions.log"))
            r = lib('log_decision block x; echo rc=$?', root)
            self.assertEqual(r.stdout.strip(), "rc=0", r.stderr)
            self.assertEqual(r.stderr, "")
            r = lib('block "boom"', root)
            self.assertEqual(r.returncode, 2)
            self.assertIn("boom", r.stderr)
            self.assertEqual(r.stderr.count("\n"), 1, "only the block line reaches stderr")
            shutil.rmtree(os.path.join(root, ".sdlc"))
            r = lib('log_decision ask y; echo rc=$?', root)
            self.assertEqual(r.stdout.strip(), "rc=0", r.stderr)
            self.assertEqual(r.stderr, "")


if __name__ == "__main__":
    unittest.main()
