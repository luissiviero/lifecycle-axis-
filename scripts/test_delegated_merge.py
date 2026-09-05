"""Tests for scripts/delegated_merge.py (work/delegated-mode R-15).

Two layers, matching the script's shape:
  * unit tests on the pure condition functions -- one per refusal reason listed in R-15, each
    built from a small JSON dict, so a condition's meaning is pinned independently of the runner;
  * two end-to-end runs through `main()` with `--fixtures`, which serves every GET from a file and
    records every mutating call into calls.jsonl. The allow case asserts the merge request body,
    the branch delete and the grant comment; the `--dry-run` case asserts nothing was recorded.

No network, no `gh`, no PyYAML: `--fixtures` installs the module's `API` hook, and the fixture
policy is the same text as FIXTURE_POLICY in scripts/test_delegation.py (spec.md design D1).
"""
import base64
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import approvers  # noqa: E402
import delegated_merge as dm  # noqa: E402
import delegation  # noqa: E402

SCRIPT = os.path.join(HERE, "delegated_merge.py")

# Exactly the YAML in spec.md design D1 (the same text scripts/test_delegation.py fixes).
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

FIXTURE_APPROVERS = """\
roles:
  product-owner: [owner]
  tech-lead: [owner]
artifacts:
  intent.md: product-owner
  spec.md: product-owner
  plan.md: tech-lead
never-approve: ["claude[bot]", "github-actions[bot]", "claude"]
"""

FIXTURE_CONFIG = """\
PROTECTED_PATHS=".claude/hooks .github/workflows .sdlc .gemini .claude/settings.json scripts/verify.sh"
RELEASE_GATED_PATHS="migrations infra terraform helm"
AGENT_BRANCH_PREFIXES="claude/ kit/ spike/"
APPROVERS_FILE=".sdlc/approvers.yaml"
"""

REPO = "owner/lifecycle-axis-"
HEAD_SHA = "a" * 40
GRANT_SHA = "b" * 40
SLUG = "delegated-mode"
INTENT_PATH = "work/%s/intent.md" % SLUG
HEAD_TIME = "2026-09-05T10:00:00Z"
REVIEW_TIME = "2026-09-05T11:00:00Z"
NOW = datetime(2026, 9, 5, 12, 0, 0, tzinfo=timezone.utc)

INTENT_TEXT = """\
---
type: sdlc/intent
id: delegated-mode
status: approved
approved-by: owner
approved-on: 2026-09-05
risk-class: low
mode: delegated
delegated-by: owner
delegated-on: 2026-09-05
---
# Intent
"""


def _write(path, text):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _policy(directory, text=FIXTURE_POLICY):
    path = os.path.join(directory, "delegation.yaml")
    _write(path, text)
    return delegation.load(path=path)


def _approvers(directory, text=FIXTURE_APPROVERS):
    path = os.path.join(directory, "approvers.yaml")
    _write(path, text)
    return approvers.load(path=path)


# ---------------------------------------------------------------------------
# Small JSON builders. Every unit test starts from a passing shape and breaks
# exactly one field, so a test names its own refusal reason.
# ---------------------------------------------------------------------------
def make_event(**over):
    event = {
        "repository": {"full_name": REPO, "default_branch": "main"},
        "workflow_run": {
            "id": 99, "name": "sdlc-gate", "event": "pull_request",
            "status": "completed", "conclusion": "success", "head_sha": HEAD_SHA,
            "head_repository": {"full_name": REPO},
            "head_commit": {"id": HEAD_SHA, "timestamp": HEAD_TIME},
        },
    }
    event["workflow_run"].update(over.pop("workflow_run", {}))
    event.update(over)
    return event


def make_pr(**over):
    pr = {
        "number": 12, "state": "open", "draft": False,
        "body": "Work-Item: %s\n\nSome description.\n" % SLUG,
        "head": {"sha": HEAD_SHA, "ref": "claude/delegated-mode",
                 "label": "owner:claude/delegated-mode"},
        "base": {"ref": "main"},
    }
    pr.update(over)
    return pr


def make_runs(**over):
    names = ["sdlc-gate", "agent-evals", "pr-review"]
    runs = [{"name": n, "status": "completed", "conclusion": "success",
             "updated_at": HEAD_TIME} for n in names]
    for run in runs:
        if run["name"] in over:
            run.update(over[run["name"]])
    return runs


def make_check_runs():
    return [
        {"name": "sdlc-gate", "status": "completed", "conclusion": "success"},
        {"name": "agent-evals", "status": "completed", "conclusion": "success"},
        {"name": "pr-review", "status": "completed", "conclusion": "success"},
        {"name": "delegated-merge", "status": "in_progress", "conclusion": None},
    ]


def make_intent_fm(**over):
    front = {"status": "approved", "mode": "delegated", "risk-class": "low",
             "delegated-by": "owner"}
    front.update(over)
    return front


def make_grant_commit(**over):
    commit = {
        "sha": GRANT_SHA,
        "author": {"login": "owner"},
        "commit": {"verification": {"verified": True, "reason": "valid"},
                   "committer": {"date": HEAD_TIME}},
        "files": [{"filename": INTENT_PATH,
                   "patch": "@@\n-mode: supervised\n+mode: delegated\n"}],
    }
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(commit.get(key), dict):
            commit[key].update(value)
        else:
            commit[key] = value
    return commit


def make_review_comment(**over):
    comment = {
        "user": {"login": "claude[bot]", "type": "Bot"},
        "created_at": REVIEW_TIME, "updated_at": REVIEW_TIME,
        "body": "## Review\n\nNothing blocking.\n\nImportant: 0 | Nits: 2\n",
    }
    comment.update(over)
    return comment


# ---------------------------------------------------------------------------
# 1. policy
# ---------------------------------------------------------------------------
class PolicyCondition(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_enabled_policy_is_ok(self):
        verdict, detail = dm.check_policy(_policy(self.tmp.name))
        self.assertEqual(verdict, dm.OK, detail)

    def test_missing_policy_file_is_policy_off(self):
        policy = delegation.load(path=os.path.join(self.tmp.name, "nope.yaml"))
        verdict, detail = dm.check_policy(policy)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("policy off", detail)

    def test_merge_enabled_false_is_policy_off(self):
        policy = _policy(self.tmp.name, FIXTURE_POLICY.replace(
            "merge:\n  enabled: true", "merge:\n  enabled: false"))
        verdict, detail = dm.check_policy(policy)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("policy off", detail)

    def test_policy_off_exits_zero_because_it_is_the_closed_state(self):
        run = dm.Run(dry_run=False, stream=io.StringIO())
        run.record("policy", (dm.REFUSED, "policy off"))
        self.assertEqual(run.finish(), 0)


# ---------------------------------------------------------------------------
# 2. event
# ---------------------------------------------------------------------------
class EventCondition(unittest.TestCase):
    def test_pull_request_run_of_this_repo_is_ok(self):
        verdict, detail = dm.check_event(make_event())
        self.assertEqual(verdict, dm.OK, detail)

    def test_event_not_pull_request_is_refused(self):
        verdict, detail = dm.check_event(make_event(workflow_run={"event": "push"}))
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("push", detail)

    def test_fork_head_repository_is_refused(self):
        event = make_event(workflow_run={"head_repository": {"full_name": "mallory/fork"}})
        verdict, detail = dm.check_event(event)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("fork", detail)

    def test_missing_conclusion_is_refused(self):
        verdict, detail = dm.check_event(make_event(workflow_run={"conclusion": None}))
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("conclusion", detail)


# ---------------------------------------------------------------------------
# 3. pull-request
# ---------------------------------------------------------------------------
class PullRequestCondition(unittest.TestCase):
    prefixes = ["claude/", "kit/", "spike/"]

    def check(self, pr):
        return dm.check_pull_request([pr], HEAD_SHA, self.prefixes, "main")

    def test_agent_pull_request_is_ok(self):
        verdict, detail = self.check(make_pr())
        self.assertEqual(verdict, dm.OK, detail)
        self.assertIn(SLUG, detail)

    def test_no_open_pull_request_for_the_head_sha_is_refused(self):
        verdict, detail = dm.check_pull_request([], HEAD_SHA, self.prefixes, "main")
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("exactly one", detail)

    def test_draft_is_refused(self):
        verdict, detail = self.check(make_pr(draft=True))
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("draft", detail)

    def test_head_prefix_not_an_agent_prefix_is_refused(self):
        pr = make_pr(head={"sha": HEAD_SHA, "ref": "work/delegated-mode", "label": "x"})
        verdict, detail = self.check(pr)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("work/delegated-mode", detail)

    def test_no_work_item_line_is_refused(self):
        verdict, detail = self.check(make_pr(body="just a description\n"))
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("Work-Item", detail)

    def test_base_not_the_default_branch_is_refused(self):
        verdict, detail = self.check(make_pr(base={"ref": "release/1.x"}))
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("release/1.x", detail)

    def test_work_item_slug_is_read_from_the_body(self):
        self.assertEqual(dm.work_item_slug("Work-Item: %s" % SLUG), SLUG)
        self.assertIsNone(dm.work_item_slug("Work-Item: not a slug"))


# ---------------------------------------------------------------------------
# 4. checks
# ---------------------------------------------------------------------------
class ChecksCondition(unittest.TestCase):
    required = ["sdlc-gate", "agent-evals", "pr-review"]

    def test_all_required_runs_green_is_ok(self):
        verdict, detail = dm.check_required_runs(make_runs(), self.required)
        self.assertEqual(verdict, dm.OK, detail)

    def test_required_workflow_missing_is_refused(self):
        runs = [r for r in make_runs() if r["name"] != "agent-evals"]
        verdict, detail = dm.check_required_runs(runs, self.required)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("agent-evals", detail)

    def test_required_workflow_failed_is_refused(self):
        runs = make_runs(**{"pr-review": {"conclusion": "failure"}})
        verdict, detail = dm.check_required_runs(runs, self.required)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("failure", detail)

    def test_required_workflow_pending_waits(self):
        runs = make_runs(**{"pr-review": {"status": "in_progress", "conclusion": None}})
        verdict, detail = dm.check_required_runs(runs, self.required)
        self.assertEqual(verdict, dm.WAITING)
        self.assertIn("in_progress", detail)

    def test_foreign_check_run_failed_is_refused(self):
        runs = make_check_runs() + [
            {"name": "lint", "status": "completed", "conclusion": "failure"}]
        verdict, detail = dm.check_check_runs(runs)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("lint", detail)

    def test_foreign_check_run_pending_waits(self):
        runs = make_check_runs() + [
            {"name": "lint", "status": "queued", "conclusion": None}]
        verdict, detail = dm.check_check_runs(runs)
        self.assertEqual(verdict, dm.WAITING)
        self.assertIn("lint", detail)

    def test_this_workflows_own_check_run_is_ignored(self):
        # delegated-merge itself is in_progress while it evaluates; counting it could never pass.
        verdict, detail = dm.check_check_runs(make_check_runs())
        self.assertEqual(verdict, dm.OK, detail)

    def test_skipped_and_neutral_conclusions_are_accepted(self):
        runs = [{"name": "a", "status": "completed", "conclusion": "skipped"},
                {"name": "b", "status": "completed", "conclusion": "neutral"}]
        self.assertEqual(dm.check_check_runs(runs)[0], dm.OK)


# ---------------------------------------------------------------------------
# 5. grant
# ---------------------------------------------------------------------------
class GrantFrontMatter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.policy = _policy(self.tmp.name)

    def check(self, **over):
        return dm.check_grant_front_matter(make_intent_fm(**over), self.policy)

    def test_granted_intent_is_ok(self):
        verdict, detail = self.check()
        self.assertEqual(verdict, dm.OK, detail)
        self.assertIn("owner", detail)

    def test_intent_not_approved_is_refused(self):
        verdict, detail = self.check(status="in-review")
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("in-review", detail)

    def test_intent_signed_delegated_is_refused(self):
        # The intent carries the grant; an agent signing it would widen its own permission.
        verdict, detail = self.check(status="delegated")
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("never signs its own grant", detail)

    def test_supervised_intent_is_refused(self):
        verdict, detail = self.check(mode="supervised")
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("supervised", detail)

    def test_risk_class_outside_the_policy_is_refused(self):
        verdict, detail = self.check(**{"risk-class": "high"})
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("high", detail)

    def test_empty_delegated_by_is_refused(self):
        verdict, detail = self.check(**{"delegated-by": ""})
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("delegated-by", detail)

    def test_missing_intent_is_refused(self):
        verdict, detail = dm.check_grant_front_matter(None, self.policy)
        self.assertEqual(verdict, dm.REFUSED)


class GrantCommit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.approvers = _approvers(self.tmp.name)

    def test_verified_product_owner_commit_is_ok(self):
        verdict, detail = dm.check_grant_commit(make_grant_commit(), self.approvers)
        self.assertEqual(verdict, dm.OK, detail)
        self.assertIn("owner", detail)

    def test_unverified_grant_commit_is_refused(self):
        commit = make_grant_commit(commit={"verification": {"verified": False,
                                                            "reason": "unsigned"}})
        verdict, detail = dm.check_grant_commit(commit, self.approvers)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("not GitHub-verified", detail)

    def test_author_without_the_product_owner_role_is_refused(self):
        commit = make_grant_commit(author={"login": "mallory"})
        verdict, detail = dm.check_grant_commit(commit, self.approvers)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("mallory", detail)

    def test_agent_author_is_refused_even_if_listed(self):
        commit = make_grant_commit(author={"login": "claude[bot]"})
        verdict, detail = dm.check_grant_commit(commit, self.approvers)
        self.assertEqual(verdict, dm.REFUSED)

    def test_no_commit_at_all_is_refused(self):
        verdict, _ = dm.check_grant_commit(None, self.approvers)
        self.assertEqual(verdict, dm.REFUSED)

    def test_delegated_by_must_match_the_grant_commit_author(self):
        # The file's own claim of who granted must be the login GitHub attributed the commit to:
        # a grant written by the owner but naming another human would put one name in the ledger
        # and another on the commit.
        verdict, detail = dm.check_grant_commit(make_grant_commit(), self.approvers,
                                                expected_handle="@Owner")
        self.assertEqual(verdict, dm.OK, detail)
        verdict, detail = dm.check_grant_commit(make_grant_commit(), self.approvers,
                                                expected_handle="someone-else")
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("someone-else", detail)

    def test_no_commit_adding_the_grant_line_is_refused_not_approximated(self):
        # Pull request 45 plan-conformance pass, finding 3: a commit that merely touches intent.md
        # is never judged as the grant; when none in the window adds the line, the condition refuses.
        verdict, detail = dm.check_grant_commit(None, self.approvers)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("no commit adding the grant line", detail)

    def test_commit_adds_grant_reads_the_patch_of_that_file_only(self):
        self.assertTrue(dm.commit_adds_grant(make_grant_commit(), INTENT_PATH))
        self.assertFalse(dm.commit_adds_grant(make_grant_commit(), "work/other/intent.md"))
        touched = make_grant_commit(files=[{"filename": INTENT_PATH,
                                           "patch": "@@\n+title: something\n"}])
        self.assertFalse(dm.commit_adds_grant(touched, INTENT_PATH))


# ---------------------------------------------------------------------------
# 6. locked-paths
# ---------------------------------------------------------------------------
class LockedPathsCondition(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        policy = _policy(self.tmp.name)
        config = {
            "PROTECTED_PATHS": [".claude/hooks", ".github/workflows", ".sdlc"],
            "RELEASE_GATED_PATHS": ["migrations", "infra", "terraform", "helm"],
        }
        self.prefixes = (config["PROTECTED_PATHS"] + config["RELEASE_GATED_PATHS"]
                         + policy.locked_paths)

    def check(self, *names):
        return dm.check_locked_paths([{"filename": n} for n in names], self.prefixes)

    def test_ordinary_diff_is_ok(self):
        verdict, detail = self.check("scripts/sdlc_metrics.py", "docs/sdlc/README.md")
        self.assertEqual(verdict, dm.OK, detail)

    def test_protected_path_is_refused(self):
        verdict, detail = self.check("docs/x.md", ".github/workflows/bands.yml")
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn(".github/workflows", detail)

    def test_release_gated_path_is_refused(self):
        verdict, detail = self.check("migrations/0001_init.sql")
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("migrations", detail)

    def test_policy_locked_path_is_refused(self):
        verdict, detail = self.check("scripts/check_artifact_chain.py")
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("check_artifact_chain.py", detail)

    def test_prefix_match_is_on_whole_segments(self):
        # `.sdlc` must not match `.sdlcx/`, and a file entry must not match a longer name.
        verdict, _ = self.check(".sdlcx/notes.md", "scripts/approve.py.bak")
        self.assertEqual(verdict, dm.OK)


# ---------------------------------------------------------------------------
# 7. review
# ---------------------------------------------------------------------------
class ReviewCondition(unittest.TestCase):
    head_time = dm._ts(HEAD_TIME)

    def test_clean_review_is_ok(self):
        verdict, detail = dm.check_review([make_review_comment()], self.head_time)
        self.assertEqual(verdict, dm.OK, detail)

    def test_no_review_comment_waits(self):
        # Fail closed (spec Q3): no pr-review credential means no comment, so the owner decides.
        verdict, detail = dm.check_review([], self.head_time)
        self.assertEqual(verdict, dm.WAITING)
        self.assertIn("claude[bot]", detail)

    def test_a_human_comment_is_not_a_review(self):
        human = {"user": {"login": "owner", "type": "User"},
                 "created_at": REVIEW_TIME, "body": "Important: 0 | Nits: 0"}
        verdict, _ = dm.check_review([human], self.head_time)
        self.assertEqual(verdict, dm.WAITING)

    def test_comment_without_the_summary_line_waits(self):
        verdict, detail = dm.check_review(
            [make_review_comment(body="Claude is working...")], self.head_time)
        self.assertEqual(verdict, dm.WAITING)
        self.assertIn("Important", detail)

    def test_important_one_is_refused(self):
        verdict, detail = dm.check_review(
            [make_review_comment(body="Important: 1 | Nits: 0\n")], self.head_time)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("Important: 1", detail)

    def test_review_older_than_the_head_commit_waits(self):
        stale = make_review_comment(created_at="2026-09-05T09:00:00Z",
                                    updated_at="2026-09-05T09:00:00Z")
        verdict, detail = dm.check_review([stale], self.head_time)
        self.assertEqual(verdict, dm.WAITING)
        self.assertIn("older than the head commit", detail)

    def test_the_newest_bot_comment_decides(self):
        old_clean = make_review_comment(created_at="2026-09-05T10:30:00Z",
                                        updated_at="2026-09-05T10:30:00Z")
        new_blocking = make_review_comment(body="Important: 2 | Nits: 0\n")
        verdict, _ = dm.check_review([old_clean, new_blocking], self.head_time)
        self.assertEqual(verdict, dm.REFUSED)


# ---------------------------------------------------------------------------
# 8. cool-off
# ---------------------------------------------------------------------------
class CoolOffCondition(unittest.TestCase):
    required = ["sdlc-gate", "agent-evals", "pr-review"]

    def test_zero_hours_is_ok(self):
        verdict, detail = dm.check_cool_off(make_runs(), self.required, 0, NOW)
        self.assertEqual(verdict, dm.OK, detail)

    def test_cool_off_not_elapsed_waits(self):
        runs = make_runs(**{"pr-review": {"updated_at": "2026-09-05T11:45:00Z"}})
        verdict, detail = dm.check_cool_off(runs, self.required, 4, NOW)
        self.assertEqual(verdict, dm.WAITING)
        self.assertIn("cool-off", detail)

    def test_cool_off_elapsed_is_ok(self):
        verdict, detail = dm.check_cool_off(make_runs(), self.required, 1, NOW)
        self.assertEqual(verdict, dm.OK, detail)

    def test_no_required_run_timestamp_waits(self):
        verdict, _ = dm.check_cool_off([], self.required, 4, NOW)
        self.assertEqual(verdict, dm.WAITING)


# ---------------------------------------------------------------------------
# End to end, through main() with --fixtures. No network: every GET is a file,
# every mutating call is a line in calls.jsonl.
# ---------------------------------------------------------------------------
class Checkout(object):
    """A fixture root: .sdlc/{delegation.yaml,approvers.yaml,config.env} plus an API fixture dir.

    `set_fixture` writes one response by the same name the script asks for (dm.fixture_name), so a
    renamed endpoint breaks the test loudly instead of silently serving the wrong file.
    """

    def __init__(self, directory, policy_text=FIXTURE_POLICY):
        self.root = os.path.join(directory, "checkout")
        self.fixtures = os.path.join(directory, "fixtures")
        os.makedirs(self.fixtures, exist_ok=True)
        _write(os.path.join(self.root, ".sdlc", "delegation.yaml"), policy_text)
        _write(os.path.join(self.root, ".sdlc", "approvers.yaml"), FIXTURE_APPROVERS)
        _write(os.path.join(self.root, ".sdlc", "config.env"), FIXTURE_CONFIG)
        self.event_path = os.path.join(directory, "event.json")
        _write(self.event_path, json.dumps(make_event()))

    def set_fixture(self, method, path, payload):
        _write(os.path.join(self.fixtures, dm.fixture_name(method, path)),
               json.dumps(payload))

    def happy_path(self):
        self.set_fixture("GET", "repos/%s/commits/%s/pulls" % (REPO, HEAD_SHA), [make_pr()])
        self.set_fixture("GET", "repos/%s/actions/runs?head_sha=%s&per_page=100" % (REPO, HEAD_SHA),
                         {"workflow_runs": make_runs()})
        self.set_fixture("GET", "repos/%s/commits/%s/check-runs?per_page=100" % (REPO, HEAD_SHA),
                         {"check_runs": make_check_runs()})
        self.set_fixture("GET", "repos/%s/contents/%s?ref=%s" % (REPO, INTENT_PATH, HEAD_SHA),
                         {"encoding": "base64",
                          "content": base64.b64encode(INTENT_TEXT.encode("utf-8")).decode("ascii")})
        self.set_fixture("GET", "repos/%s/commits?path=%s&sha=%s&per_page=%d"
                         % (REPO, INTENT_PATH, HEAD_SHA, dm.GRANT_WINDOW), [{"sha": GRANT_SHA}])
        self.set_fixture("GET", "repos/%s/commits/%s" % (REPO, GRANT_SHA), make_grant_commit())
        self.set_fixture("GET", "repos/%s/pulls/12/files?per_page=100" % REPO,
                         [{"filename": "scripts/sdlc_metrics.py"}, {"filename": "work/%s/plan.md" % SLUG}])
        self.set_fixture("GET", "repos/%s/issues/12/comments?per_page=100" % REPO,
                         [make_review_comment()])
        self.set_fixture("PUT", "repos/%s/pulls/12/merge" % REPO,
                         {"merged": True, "sha": "c" * 40})
        return self

    def calls(self):
        path = os.path.join(self.fixtures, "calls.jsonl")
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def argv(self, *extra):
        return ["--event", self.event_path, "--root", self.root,
                "--fixtures", self.fixtures] + list(extra)

    def argv_without_fixtures(self, *extra):
        """For a test that installs its own `API` hook -- `--fixtures` would replace it."""
        return ["--event", self.event_path, "--root", self.root] + list(extra)


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(setattr, dm, "API", None)

    def run_main(self, checkout, *extra):
        out = io.StringIO()
        saved = sys.stdout
        sys.stdout = out
        try:
            code = dm.main(checkout.argv(*extra))
        finally:
            sys.stdout = saved
        return code, out.getvalue()

    def test_every_condition_ok_merges_deletes_the_branch_and_comments(self):
        checkout = Checkout(self.tmp.name).happy_path()
        code, output = self.run_main(checkout)
        self.assertEqual(code, 0, output)
        names = [line.split(":")[0].replace("CONDITION ", "")
                 for line in output.splitlines() if line.startswith("CONDITION ")]
        self.assertEqual(names, ["policy", "event", "pull-request", "checks", "grant",
                                 "locked-paths", "review", "cool-off"])
        self.assertIn("DELEGATED-MERGE: merged #12 %s" % HEAD_SHA, output)

        calls = checkout.calls()
        by_method = dict((c["method"], c) for c in calls)
        merge = by_method["PUT"]
        self.assertEqual(merge["path"], "repos/%s/pulls/12/merge" % REPO)
        self.assertEqual(merge["fields"]["sha"], HEAD_SHA)
        self.assertEqual(merge["fields"]["merge_method"], "merge")
        self.assertIn("#12", merge["fields"]["commit_title"])

        self.assertEqual(by_method["DELETE"]["path"],
                         "repos/%s/git/refs/heads/claude/delegated-mode" % REPO)

        body = by_method["POST"]["fields"]["body"]
        self.assertEqual(
            body,
            "merged under delegation granted by owner in %s\n\n---\n"
            "_Generated by the delegated-merge workflow_" % GRANT_SHA)
        self.assertEqual([c["method"] for c in calls], ["PUT", "DELETE", "POST"])

    def test_dry_run_records_no_call_and_prints_a_dry_run_verdict(self):
        checkout = Checkout(self.tmp.name).happy_path()
        code, output = self.run_main(checkout, "--dry-run")
        self.assertEqual(code, 0, output)
        last = [line for line in output.splitlines() if line.strip()][-1]
        self.assertTrue(last.startswith("DELEGATED-MERGE: dry-run ("), last)
        self.assertEqual(checkout.calls(), [])

    def test_dry_run_against_a_supervised_item_prints_the_grant_refusal(self):
        checkout = Checkout(self.tmp.name).happy_path()
        checkout.set_fixture(
            "GET", "repos/%s/contents/%s?ref=%s" % (REPO, INTENT_PATH, HEAD_SHA),
            {"encoding": "base64",
             "content": base64.b64encode(
                 INTENT_TEXT.replace("mode: delegated", "mode: supervised").encode("utf-8")
             ).decode("ascii")})
        code, output = self.run_main(checkout, "--dry-run")
        self.assertEqual(code, 1, output)
        self.assertIn("CONDITION grant: refused", output)
        self.assertIn("DELEGATED-MERGE: dry-run (refused: grant)", output)
        self.assertEqual(checkout.calls(), [])

    def test_policy_off_is_a_no_op_that_exits_zero(self):
        checkout = Checkout(self.tmp.name, policy_text=FIXTURE_POLICY.replace(
            "enabled: true\nagents", "enabled: false\nagents")).happy_path()
        code, output = self.run_main(checkout)
        self.assertEqual(code, 0, output)
        self.assertIn("policy off", output)
        self.assertIn("DELEGATED-MERGE: refused (policy)", output)
        self.assertEqual(checkout.calls(), [])

    def test_a_refusal_exits_one_and_stops_at_that_condition(self):
        checkout = Checkout(self.tmp.name).happy_path()
        checkout.set_fixture("GET", "repos/%s/pulls/12/files?per_page=100" % REPO,
                             [{"filename": ".github/workflows/sdlc-gate.yml"}])
        code, output = self.run_main(checkout)
        self.assertEqual(code, 1, output)
        self.assertIn("DELEGATED-MERGE: refused (locked-paths)", output)
        self.assertNotIn("CONDITION review", output)
        self.assertEqual(checkout.calls(), [])

    def test_a_wait_exits_zero_and_merges_nothing(self):
        checkout = Checkout(self.tmp.name).happy_path()
        checkout.set_fixture("GET", "repos/%s/issues/12/comments?per_page=100" % REPO, [])
        code, output = self.run_main(checkout)
        self.assertEqual(code, 0, output)
        self.assertIn("DELEGATED-MERGE: waiting (review)", output)
        self.assertEqual(checkout.calls(), [])

    def test_head_sha_route_synthesises_the_event_and_forces_a_dry_run(self):
        # The workflow_dispatch route: no event file, the head sha and repo from the arguments,
        # the default branch from the repository endpoint, and never a mutating call even without
        # --dry-run on the command line.
        checkout = Checkout(self.tmp.name).happy_path()
        checkout.set_fixture("GET", "repos/%s" % REPO, {"default_branch": "main"})
        # No head_commit in a synthesised event: the review condition reads the commit instead.
        checkout.set_fixture("GET", "repos/%s/commits/%s" % (REPO, HEAD_SHA),
                             {"sha": HEAD_SHA,
                              "commit": {"committer": {"date": "2026-09-05T10:00:00Z"}}})
        out = io.StringIO()
        saved = sys.stdout
        sys.stdout = out
        try:
            code = dm.main(["--root", checkout.root, "--fixtures", checkout.fixtures,
                            "--head-sha", HEAD_SHA, "--repo", REPO])
        finally:
            sys.stdout = saved
        output = out.getvalue()
        self.assertEqual(code, 0, output)
        self.assertIn("CONDITION event: ok", output)
        self.assertIn("DELEGATED-MERGE: dry-run (would merge #12)", output)
        self.assertEqual(checkout.calls(), [])

    def test_cli_runs_as_a_subprocess_with_the_same_verdict(self):
        checkout = Checkout(self.tmp.name).happy_path()
        proc = subprocess.run([sys.executable, SCRIPT] + checkout.argv("--dry-run"),
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        last = [line for line in proc.stdout.splitlines() if line.strip()][-1]
        self.assertTrue(last.startswith("DELEGATED-MERGE: dry-run ("), proc.stdout)
        self.assertEqual(checkout.calls(), [])


class StaleMerge(unittest.TestCase):
    """A push between the check completing and the merge call: HTTP 409, refused (stale), exit 0."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(setattr, dm, "API", None)

    def test_http_409_on_merge_is_refused_stale_and_exits_zero(self):
        checkout = Checkout(self.tmp.name).happy_path()
        served = dm.FixtureAPI(checkout.fixtures)

        def api(method, path, fields=None):
            if method == "PUT":
                raise dm.MergeError("PUT %s failed (HTTP 409)" % path, status=409)
            return served(method, path, fields)

        dm.API = api
        out = io.StringIO()
        saved = sys.stdout
        sys.stdout = out
        try:
            code = dm.main(checkout.argv_without_fixtures())
        finally:
            sys.stdout = saved
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("DELEGATED-MERGE: refused (stale)", out.getvalue())
        self.assertEqual(checkout.calls(), [])


class Plumbing(unittest.TestCase):
    def test_fixture_name_flattens_the_query_string(self):
        self.assertEqual(dm.fixture_name("GET", "repos/o/r/pulls/1/files?per_page=100"),
                         "GET_repos_o_r_pulls_1_files_per_page_100.json")

    def test_paginated_array_pages_are_flattened(self):
        self.assertEqual(dm._parse_json_stream('[{"a": 1}]\n[{"a": 2}]'), [{"a": 1}, {"a": 2}])

    def test_paginated_object_pages_merge_their_lists(self):
        merged = dm._parse_json_stream('{"workflow_runs": [1]}\n{"workflow_runs": [2]}')
        self.assertEqual(dm.items(merged, "workflow_runs"), [1, 2])

    def test_a_missing_get_fixture_is_a_loud_error(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(dm.MergeError):
                dm.FixtureAPI(d)("GET", "repos/o/r/pulls/1")

    def test_merge_comment_body_names_the_handle_and_the_grant_commit(self):
        body = dm.merge_comment_body("owner", GRANT_SHA)
        self.assertTrue(body.startswith("merged under delegation granted by owner in %s" % GRANT_SHA))
        self.assertTrue(body.endswith("_Generated by the delegated-merge workflow_"))

    def test_ts_reads_github_timestamps(self):
        self.assertEqual(dm._ts("2026-09-05T10:00:00Z"),
                         datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc))
        self.assertIsNone(dm._ts(None))
        self.assertIsNone(dm._ts("not a date"))

    def test_load_config_reads_the_given_root_and_restores_the_module_global(self):
        with tempfile.TemporaryDirectory() as d:
            _write(os.path.join(d, ".sdlc", "config.env"), FIXTURE_CONFIG)
            import check_artifact_chain as chain
            before = chain.ROOT
            config = dm.load_config(d)
            self.assertEqual(config["AGENT_BRANCH_PREFIXES"], ["claude/", "kit/", "spike/"])
            self.assertEqual(chain.ROOT, before)


if __name__ == "__main__":
    unittest.main()
