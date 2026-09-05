import os, subprocess, sys, tempfile, textwrap, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import approvers
from approvers import load


class ApproversRepoFile(unittest.TestCase):
    """Exercises the real .sdlc/approvers.yaml via the default resolution
    path (config() -> APPROVERS_FILE -> git root)."""

    def setUp(self):
        self.a = load()

    def test_valid_handle_per_artifact(self):
        for artifact, role in [
            ("intent.md", "product-owner"),
            ("spec.md", "product-owner"),
            ("plan.md", "tech-lead"),
            ("incident.md", "service-owner"),
        ]:
            self.assertEqual(self.a.role_for(artifact), role)
            ok, reason = self.a.is_valid(artifact, "luissiviero")
            self.assertTrue(ok, reason)
            self.assertEqual(reason, "ok")

    def test_at_prefix_normalizes(self):
        ok, reason = self.a.is_valid("plan.md", "@luissiviero")
        self.assertTrue(ok, reason)

    def test_trailing_annotation_normalizes(self):
        ok, reason = self.a.is_valid("intent.md", "luissiviero (product owner)")
        self.assertTrue(ok, reason)

    def test_placeholder_handle_holds_no_role(self):
        """adopt.sh ships `<your-github-handle>` in every role; it must approve nothing until the
        adopter replaces it (work/batch-b-followups R-2)."""
        ok, reason = self.a.has_role("tech-lead", "<your-github-handle>")
        self.assertFalse(ok)
        self.assertIn("placeholder", reason)
        ok, reason = self.a.is_valid("plan.md", "<your-github-handle>")
        self.assertFalse(ok)
        self.assertIn("placeholder", reason)

    def test_normalize_matches_expectations(self):
        self.assertEqual(approvers.Approvers.normalize("@luissiviero"), "luissiviero")
        self.assertEqual(
            approvers.Approvers.normalize("luissiviero (product owner)"), "luissiviero"
        )
        self.assertEqual(approvers.Approvers.normalize('"LuisSiviero"'), "luissiviero")
        self.assertEqual(approvers.Approvers.normalize(""), "")

    def test_bot_handle_rejected(self):
        for bot in ("claude[bot]", "github-actions[bot]", "claude", "@claude"):
            ok, reason = self.a.is_valid("plan.md", bot)
            self.assertFalse(ok)
            self.assertEqual(reason, "agent identities cannot approve")

    def test_unknown_handle_names_role(self):
        ok, reason = self.a.is_valid("plan.md", "someone-else")
        self.assertFalse(ok)
        self.assertIn("tech-lead", reason)

    def test_unknown_artifact_rejected(self):
        self.assertIsNone(self.a.role_for("readme.md"))
        ok, reason = self.a.is_valid("readme.md", "luissiviero")
        self.assertFalse(ok)
        self.assertIn("readme.md", reason)

    def test_empty_handle_rejected(self):
        ok, reason = self.a.is_valid("plan.md", "")
        self.assertFalse(ok)
        self.assertEqual(reason, "empty approver")


class ApproversMissingFile(unittest.TestCase):
    def test_missing_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            missing = os.path.join(d, "nope.yaml")
            a = load(missing)
            self.assertFalse(a.exists)
            ok, reason = a.is_valid("plan.md", "luissiviero")
            self.assertFalse(ok)
            self.assertIn(missing, reason)
            self.assertIn("no approvers file", reason)


class ApproversMalformed(unittest.TestCase):
    def _write(self, d, content):
        path = os.path.join(d, "approvers.yaml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_tab_indentation_raises_with_line_number(self):
        with tempfile.TemporaryDirectory() as d:
            path = self._write(d, "roles:\n\tproduct-owner: [x]\n")
            with self.assertRaises(ValueError) as cm:
                load(path)
            self.assertIn(f"{path}:2:", str(cm.exception))

    def test_missing_colon_raises_with_line_number(self):
        with tempfile.TemporaryDirectory() as d:
            path = self._write(d, "roles\n  product-owner: [x]\n")
            with self.assertRaises(ValueError) as cm:
                load(path)
            self.assertIn(f"{path}:1:", str(cm.exception))

    def test_unknown_top_level_key_raises_with_line_number(self):
        with tempfile.TemporaryDirectory() as d:
            path = self._write(d, "teams:\n  x: [y]\n")
            with self.assertRaises(ValueError) as cm:
                load(path)
            self.assertIn(f"{path}:1:", str(cm.exception))
            self.assertIn("teams", str(cm.exception))


class ApproversTempFileDifferentOwner(unittest.TestCase):
    def test_temp_file_with_different_owner_works(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "approvers.yaml")
            with open(path, "w", encoding="utf-8") as f:
                f.write(
                    textwrap.dedent(
                        """\
                        roles:
                          product-owner: [alice]
                        artifacts:
                          intent.md: product-owner
                        never-approve: ["claude"]
                        """
                    )
                )
            a = load(path)
            ok, reason = a.is_valid("intent.md", "alice")
            self.assertTrue(ok, reason)
            ok, reason = a.is_valid("intent.md", "luissiviero")
            self.assertFalse(ok)


class HasRole(unittest.TestCase):
    """work/front-matter spec R-9: the role question the deploy gate asks, as a method and a CLI."""

    def setUp(self):
        self.a = load()

    def test_listed_handle_ok(self):
        for role in ("product-owner", "tech-lead", "release-manager", "service-owner"):
            ok, reason = self.a.has_role(role, "luissiviero")
            self.assertTrue(ok, f"{role}: {reason}")
            self.assertEqual(reason, "ok")
        ok, _ = self.a.has_role("tech-lead", "@LuisSiviero (tech lead)")
        self.assertTrue(ok)

    def test_never_approve_handle_rejected(self):
        for bot in ("claude[bot]", "github-actions[bot]", "claude", "@claude"):
            ok, reason = self.a.has_role("tech-lead", bot)
            self.assertFalse(ok)
            self.assertEqual(reason, "agent identities cannot approve")
        ok, reason = self.a.has_role("tech-lead", "")
        self.assertFalse(ok)
        self.assertEqual(reason, "empty approver")
        ok, reason = self.a.has_role("tech-lead", "someone-else")
        self.assertFalse(ok)
        self.assertEqual(reason, "someone-else is not a tech-lead")

    def test_unknown_role_rejected(self):
        ok, reason = self.a.has_role("janitor", "luissiviero")
        self.assertFalse(ok)
        self.assertEqual(reason, "no such role janitor")
        with tempfile.TemporaryDirectory() as d:
            missing = os.path.join(d, "nope.yaml")
            ok, reason = load(missing).has_role("tech-lead", "luissiviero")
            self.assertFalse(ok)
            self.assertIn("no approvers file", reason)

    def test_cli_exit_codes(self):
        script = os.path.join(HERE, "approvers.py")
        cases = (("tech-lead", "luissiviero", 0), ("tech-lead", "claude", 1),
                 ("tech-lead", "someone-else", 1), ("janitor", "luissiviero", 1))
        for role, handle, code in cases:
            r = subprocess.run([sys.executable, script, "--has-role", role, handle],
                               capture_output=True, text=True, cwd=os.path.dirname(HERE))
            self.assertEqual(r.returncode, code, f"{role} {handle}: {r.stderr}")
            self.assertTrue(r.stderr.strip(), "reason goes to stderr")
        # No flag: the JSON dump is unchanged.
        r = subprocess.run([sys.executable, script], capture_output=True, text=True, cwd=os.path.dirname(HERE))
        self.assertEqual(r.returncode, 0)
        self.assertIn('"roles"', r.stdout)


if __name__ == "__main__":
    unittest.main()
