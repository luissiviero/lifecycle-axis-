"""Tests for scripts/delegation.py (work/delegated-mode R-1).

Written from work/delegated-mode/spec.md's Interfaces section and design D1 before the
implementation exists, so every test here is expected to fail today (ImportError / AttributeError)
and to pass once scripts/delegation.py ships. See NOTES.md in this drop for the assumptions this
file bakes in about types (enabled/merge booleans, max_deviations/min_reviewers ints) and about the
default CLI resolution path, since the spec's Interfaces section does not spell either out fully.
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import delegation  # noqa: E402

DELEGATION_SCRIPT = os.path.join(HERE, "delegation.py")

# Exactly the YAML in spec.md design D1.
FIXTURE_POLICY = """\
enabled: true
agents: [claude, claude[bot]]
signable: [spec.md, plan.md, incident.md]
risk-classes: [low]
max-deviations: 5
revisions: consensus
min-reviewers: 2
merge:
  enabled: true
  require-review: true
  require-checks: [sdlc-gate, agent-evals, pr-review]
  method: merge
  cool-off-hours: 0
locked-paths: [scripts/check_artifact_chain.py, scripts/approvers.py, scripts/log_ledger.py, scripts/approve.py, scripts/sign.py, scripts/delegation.py, scripts/delegated_merge.py, scripts/check_control_plane.sh, scripts/check_workflow_permissions.py, REVIEW.md, .claude-plugin]
"""

DISABLED_POLICY = """\
enabled: false
agents: [claude]
signable: [spec.md]
risk-classes: [low]
max-deviations: 5
revisions: consensus
min-reviewers: 2
merge:
  enabled: true
  require-review: true
  require-checks: [sdlc-gate]
  method: merge
  cool-off-hours: 0
locked-paths: []
"""

EXPECTED_LOCKED_PATHS = [
    "scripts/check_artifact_chain.py", "scripts/approvers.py", "scripts/log_ledger.py",
    "scripts/approve.py", "scripts/sign.py", "scripts/delegation.py",
    "scripts/delegated_merge.py", "scripts/check_control_plane.sh",
    "scripts/check_workflow_permissions.py", "REVIEW.md", ".claude-plugin",
]


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _fixture_path(d, content=FIXTURE_POLICY):
    path = os.path.join(d, "delegation.yaml")
    _write(path, content)
    return path


def _cli(root, *args):
    return subprocess.run(
        [sys.executable, DELEGATION_SCRIPT, *args],
        cwd=root, capture_output=True, text=True,
    )


def _init_repo(root, policy_content=None):
    """A bare git repo (so `git rev-parse --show-toplevel` resolves, the way
    check_artifact_chain.ROOT / approvers.load() rely on) with an optional
    .sdlc/delegation.yaml -- no commit required for toplevel resolution."""
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)
    if policy_content is not None:
        _write(os.path.join(root, ".sdlc", "delegation.yaml"), policy_content)


class FixtureLoadsEveryKey(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = _fixture_path(self.tmp.name)
        self.policy = delegation.load(path=self.path)

    def test_enabled(self):
        self.assertIs(self.policy.enabled, True)

    def test_agents(self):
        self.assertEqual(self.policy.agents, ["claude", "claude[bot]"])

    def test_signable(self):
        self.assertEqual(self.policy.signable, ["spec.md", "plan.md", "incident.md"])

    def test_risk_classes(self):
        self.assertEqual(self.policy.risk_classes, ["low"])

    def test_max_deviations_is_int(self):
        self.assertEqual(self.policy.max_deviations, 5)
        self.assertIsInstance(self.policy.max_deviations, int)

    def test_revisions(self):
        self.assertEqual(self.policy.revisions, "consensus")

    def test_min_reviewers_is_int(self):
        self.assertEqual(self.policy.min_reviewers, 2)
        self.assertIsInstance(self.policy.min_reviewers, int)

    def test_merge_dict(self):
        self.assertEqual(
            self.policy.merge,
            {
                "enabled": True,
                "require_review": True,
                "require_checks": ["sdlc-gate", "agent-evals", "pr-review"],
                "method": "merge",
                "cool_off_hours": 0,
            },
        )

    def test_locked_paths(self):
        self.assertEqual(self.policy.locked_paths, EXPECTED_LOCKED_PATHS)


class MissingFileFailsClosed(unittest.TestCase):
    def test_enabled_is_false_and_may_sign_fails_naming_the_path(self):
        with tempfile.TemporaryDirectory() as d:
            missing = os.path.join(d, "nope.yaml")
            policy = delegation.load(path=missing)
            self.assertIs(policy.enabled, False)
            ok, reason = policy.may_sign("claude")
            self.assertFalse(ok)
            self.assertIn(missing, reason)


class DisabledPolicy(unittest.TestCase):
    def test_enabled_false_disables_signing(self):
        with tempfile.TemporaryDirectory() as d:
            path = _fixture_path(d, DISABLED_POLICY)
            policy = delegation.load(path=path)
            self.assertIs(policy.enabled, False)
            ok, reason = policy.may_sign("claude")
            self.assertFalse(ok)
            self.assertTrue(reason)


class MaySign(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.policy = delegation.load(path=_fixture_path(self.tmp.name))

    def test_agent_handle_is_allowed(self):
        ok, reason = self.policy.may_sign("claude")
        self.assertTrue(ok, reason)

    def test_handle_not_in_agents_fails(self):
        ok, reason = self.policy.may_sign("mallory")
        self.assertFalse(ok)
        self.assertIn("mallory", reason)

    def test_human_handle_is_never_an_agent(self):
        ok, reason = self.policy.may_sign("luissiviero")
        self.assertFalse(ok)


class MaySignArtifact(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.policy = delegation.load(path=_fixture_path(self.tmp.name))

    def test_intent_is_never_signable(self):
        ok, reason = self.policy.may_sign_artifact("intent.md")
        self.assertFalse(ok, reason)

    def test_spec_is_signable(self):
        ok, reason = self.policy.may_sign_artifact("spec.md")
        self.assertTrue(ok, reason)

    def test_plan_and_incident_are_signable(self):
        ok, _ = self.policy.may_sign_artifact("plan.md")
        self.assertTrue(ok)
        ok, _ = self.policy.may_sign_artifact("incident.md")
        self.assertTrue(ok)


class RiskOk(unittest.TestCase):
    """risk_ok returns (bool, reason), the same shape as may_sign and may_sign_artifact --
    confirmed against scripts/check_artifact_chain.py's check_grant, which unpacks it as
    `ok, reason = policy.risk_ok(...)`; the spec's Interfaces section does not spell this out."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.policy = delegation.load(path=_fixture_path(self.tmp.name))

    def test_low_is_in_policy(self):
        ok, reason = self.policy.risk_ok("low")
        self.assertTrue(ok, reason)

    def test_medium_is_not_in_policy(self):
        ok, reason = self.policy.risk_ok("medium")
        self.assertFalse(ok)
        self.assertTrue(reason)

    def test_high_is_not_in_policy(self):
        ok, _ = self.policy.risk_ok("high")
        self.assertFalse(ok)


class MalformedPolicy(unittest.TestCase):
    def test_tab_indentation_raises_with_path_and_line(self):
        with tempfile.TemporaryDirectory() as d:
            path = _fixture_path(d, "merge:\n\tenabled: true\n")
            with self.assertRaises(ValueError) as cm:
                delegation.load(path=path)
            self.assertIn(f"{path}:2:", str(cm.exception))

    def test_unknown_top_level_key_raises_with_path_and_line(self):
        with tempfile.TemporaryDirectory() as d:
            path = _fixture_path(d, "teams: [x]\n")
            with self.assertRaises(ValueError) as cm:
                delegation.load(path=path)
            self.assertIn(f"{path}:1:", str(cm.exception))
            self.assertIn("teams", str(cm.exception))


class CLI(unittest.TestCase):
    def test_may_sign_exits_0_with_the_fixture(self):
        with tempfile.TemporaryDirectory() as root:
            _init_repo(root, FIXTURE_POLICY)
            r = _cli(root, "--may-sign", "claude")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_may_sign_exits_1_without_a_policy_file(self):
        with tempfile.TemporaryDirectory() as root:
            _init_repo(root, None)
            r = _cli(root, "--may-sign", "claude")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_may_sign_exits_1_for_a_handle_outside_agents(self):
        with tempfile.TemporaryDirectory() as root:
            _init_repo(root, FIXTURE_POLICY)
            r = _cli(root, "--may-sign", "mallory")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_no_flags_dumps_json(self):
        with tempfile.TemporaryDirectory() as root:
            _init_repo(root, FIXTURE_POLICY)
            r = _cli(root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('"agents"', r.stdout)


if __name__ == "__main__":
    unittest.main()
