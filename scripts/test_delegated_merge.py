"""Tests for scripts/delegated_merge.py (work/delegated-mode R-15).

Two layers, matching the script's shape:
  * unit tests on the pure condition functions -- one per refusal reason listed in R-15, each
    built from a small JSON dict, so a condition's meaning is pinned independently of the runner;
  * two end-to-end runs through `main()` with `--fixtures`, which serves every GET from a file and
    records every mutating call into calls.jsonl. The allow case asserts the merge request body,
    the branch delete and the grant comment; the `--dry-run` case asserts nothing was recorded.

The security pass on pull request 45 added a refusal test for each of its findings: a spoofed
grant author, a grant read from the head, a review comment that no pr-review run backs, a run
somebody dispatched by hand, a rename out of a judging surface, and a slug that is not the active
work item.

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
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import approvers  # noqa: E402
import delegated_merge as dm  # noqa: E402
import delegation  # noqa: E402
import log_ledger  # noqa: E402  (the Advance class parses the two ledger lines back)

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
HEAD_REF = "claude/delegated-mode"
BASE_REF = "main"
HEAD_TIME = "2026-09-05T10:00:00Z"
REVIEW_TIME = "2026-09-05T11:00:00Z"
NOW = datetime(2026, 9, 5, 12, 0, 0, tzinfo=timezone.utc)
# The pr-review run whose id the review comment must link (findings 3/4).
REVIEW_RUN_ID = 7003
RUN_IDS = {"sdlc-gate": 7001, "agent-evals": 7002, "pr-review": REVIEW_RUN_ID}
REVIEW_RUN_URL = "https://github.com/%s/actions/runs/%d" % (REPO, REVIEW_RUN_ID)

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
        "head": {"sha": HEAD_SHA, "ref": HEAD_REF, "label": "owner:%s" % HEAD_REF},
        "base": {"ref": BASE_REF},
    }
    pr.update(over)
    return pr


def make_runs(**over):
    """The three required workflow runs, as `actions/runs?head_sha=` returns them: each carries the
    `event` and `head_branch` the checks and review conditions filter on, and an `id` the review
    comment links."""
    names = ["sdlc-gate", "agent-evals", "pr-review"]
    runs = [{"name": n, "id": RUN_IDS[n], "event": "pull_request", "head_branch": HEAD_REF,
             "status": "completed", "conclusion": "success", "updated_at": HEAD_TIME}
            for n in names]
    for run in runs:
        if run["name"] in over:
            run.update(over[run["name"]])
    return runs


def make_check_runs():
    return [
        {"name": "sdlc-gate", "status": "completed", "conclusion": "success"},
        {"name": "agent-evals", "status": "completed", "conclusion": "success"},
        {"name": "pr-review", "status": "completed", "conclusion": "success"},
        # delegated-merge.yml's own job, named `merge`: GitHub names a check run after the job.
        {"name": "merge", "status": "in_progress", "conclusion": None},
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
        "committer": {"login": "owner"},
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
    """The tracking comment pr-review.yml opens for its run: it links the run, which is what binds
    the verdict to a workflow nobody else can start."""
    comment = {
        "user": {"login": "claude[bot]", "type": "Bot"},
        "created_at": REVIEW_TIME, "updated_at": REVIEW_TIME,
        "body": "## Review\n\n[View job run](%s)\n\nNothing blocking.\n\nImportant: 0 | Nits: 2\n"
                % REVIEW_RUN_URL,
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

    def test_failed_run_is_refused(self):
        # Nit d: a completed run is not enough; the run that woke this workflow must be green.
        verdict, detail = dm.check_event(make_event(workflow_run={"conclusion": "failure"}))
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("failure", detail)


# ---------------------------------------------------------------------------
# 3. pull-request
# ---------------------------------------------------------------------------
class PullRequestCondition(unittest.TestCase):
    prefixes = ["claude/", "kit/", "spike/"]

    def check(self, pr, active=SLUG):
        return dm.check_pull_request([pr], HEAD_SHA, self.prefixes, "main", active)

    def test_agent_pull_request_is_ok(self):
        verdict, detail = self.check(make_pr())
        self.assertEqual(verdict, dm.OK, detail)
        self.assertIn(SLUG, detail)

    def test_no_open_pull_request_for_the_head_sha_is_refused(self):
        verdict, detail = dm.check_pull_request([], HEAD_SHA, self.prefixes, "main", SLUG)
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

    def test_a_traversing_slug_is_not_a_slug(self):
        # Finding 7: the slug is interpolated into work/<slug>/intent.md.
        self.assertIsNone(dm.work_item_slug("Work-Item: .."))
        self.assertIsNone(dm.work_item_slug("Work-Item: ../other"))
        self.assertIsNone(dm.work_item_slug("Work-Item: .git"))
        self.assertEqual(dm.work_item_slug("Work-Item: batch-b.2"), "batch-b.2")
        verdict, detail = self.check(make_pr(body="Work-Item: ..\n"))
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("Work-Item", detail)

    def test_slug_that_is_not_the_active_work_item_is_refused(self):
        # Finding 7: the body is written by the branch; .sdlc/active is read from the base checkout.
        verdict, detail = self.check(make_pr(), active="another-item")
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn(SLUG, detail)
        self.assertIn("another-item", detail)
        self.assertIn(".sdlc/active", detail)

    def test_missing_active_file_refuses(self):
        verdict, detail = self.check(make_pr(), active="")
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn(".sdlc/active", detail)


# ---------------------------------------------------------------------------
# 4. checks
# ---------------------------------------------------------------------------
class ChecksCondition(unittest.TestCase):
    required = ["sdlc-gate", "agent-evals", "pr-review"]

    def check(self, runs, head_ref=HEAD_REF):
        return dm.check_required_runs(runs, self.required, head_ref)

    def test_all_required_runs_green_is_ok(self):
        verdict, detail = self.check(make_runs())
        self.assertEqual(verdict, dm.OK, detail)

    def test_required_workflow_missing_is_refused(self):
        runs = [r for r in make_runs() if r["name"] != "agent-evals"]
        verdict, detail = self.check(runs)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("agent-evals", detail)

    def test_required_workflow_failed_is_refused(self):
        runs = make_runs(**{"pr-review": {"conclusion": "failure"}})
        verdict, detail = self.check(runs)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("failure", detail)

    def test_required_workflow_pending_waits(self):
        runs = make_runs(**{"pr-review": {"status": "in_progress", "conclusion": None}})
        verdict, detail = self.check(runs)
        self.assertEqual(verdict, dm.WAITING)
        self.assertIn("in_progress", detail)

    def test_a_dispatched_green_run_does_not_excuse_a_failed_pull_request_run(self):
        # Finding 5: anybody with write access can start a workflow_dispatch run and let it pass.
        runs = make_runs(**{"sdlc-gate": {"conclusion": "failure"}})
        runs.append({"name": "sdlc-gate", "id": 7099, "event": "workflow_dispatch",
                     "head_branch": HEAD_REF, "status": "completed", "conclusion": "success",
                     "updated_at": HEAD_TIME})
        verdict, detail = self.check(runs)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("sdlc-gate", detail)
        self.assertIn("failure", detail)

    def test_a_run_on_another_branch_is_ignored(self):
        # Finding 5: a green run of the same workflow on someone else's branch judged other code.
        runs = make_runs(**{"pr-review": {"head_branch": "claude/other-item"}})
        verdict, detail = self.check(runs)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("pr-review", detail)
        self.assertIn("no pull_request run", detail)

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
        # Nit b: the check run carries the JOB's name (`merge`), which is what is excluded; this
        # job is in_progress while it evaluates, so counting it could never pass.
        self.assertEqual(dm.SELF_CHECK_NAME, "merge")
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
        return dm.check_grant_front_matter(make_intent_fm(**over), self.policy, base_ref=BASE_REF)

    def test_granted_intent_is_ok(self):
        verdict, detail = self.check()
        self.assertEqual(verdict, dm.OK, detail)
        self.assertIn("owner", detail)
        self.assertIn("on %s" % BASE_REF, detail)

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
        verdict, detail = dm.check_grant_front_matter(None, self.policy, base_ref=BASE_REF)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("on %s" % BASE_REF, detail)


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
        self.assertIn("unsigned", detail)

    def test_verified_with_a_reason_other_than_valid_is_refused(self):
        # Finding 1: `verified` true with any other reason is not a state to trust.
        commit = make_grant_commit(commit={"verification": {"verified": True,
                                                            "reason": "unverified_email"}})
        verdict, detail = dm.check_grant_commit(commit, self.approvers)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("unverified_email", detail)

    def test_author_without_the_product_owner_role_is_refused(self):
        commit = make_grant_commit(author={"login": "mallory"})
        verdict, detail = dm.check_grant_commit(commit, self.approvers)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("mallory", detail)

    def test_agent_author_is_refused_even_if_listed(self):
        commit = make_grant_commit(author={"login": "claude[bot]"})
        verdict, detail = dm.check_grant_commit(commit, self.approvers)
        self.assertEqual(verdict, dm.REFUSED)

    def test_a_valid_signature_over_a_spoofed_author_is_refused(self):
        # Finding 1: verification.verified covers the COMMITTER's signature, and author.login comes
        # from an author email the committer picks. mallory signing a commit whose author line says
        # `owner` produces exactly this shape.
        commit = make_grant_commit(committer={"login": "mallory"})
        verdict, detail = dm.check_grant_commit(commit, self.approvers, expected_handle="owner")
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("mallory", detail)
        self.assertIn("committer", detail)

    def test_web_flow_committer_with_an_owner_author_is_ok(self):
        # GitHub's own signer for web-editor and API commits: the author is the account that asked.
        commit = make_grant_commit(committer={"login": "web-flow"})
        verdict, detail = dm.check_grant_commit(commit, self.approvers, expected_handle="owner")
        self.assertEqual(verdict, dm.OK, detail)

    def test_the_owner_signing_their_own_commit_is_ok(self):
        commit = make_grant_commit(author={"login": "owner"}, committer={"login": "owner"})
        verdict, detail = dm.check_grant_commit(commit, self.approvers, expected_handle="owner")
        self.assertEqual(verdict, dm.OK, detail)

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
        verdict, detail = dm.check_grant_commit(None, self.approvers, base_ref=BASE_REF)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("no commit adding the grant line", detail)
        self.assertIn("on %s" % BASE_REF, detail)

    # --- work/approve-by-dispatch R-7: route B, the dispatch route ---------------------------
    TRAILERS = "[demo] Approve intent.md as owner\n\nApproved-Run: 12345\nApproved-Actor: owner\n"

    def dispatched_commit(self, message=None, **over):
        """A grant commit as approve_dispatch.py makes one: unsigned, authored by the run's actor,
        committed by the bot, carrying the two trailers."""
        base = make_grant_commit(
            author={"login": "owner"},
            committer={"login": "github-actions[bot]"},
            commit={"verification": {"verified": False, "reason": "unsigned"},
                    "message": message if message is not None else self.TRAILERS})
        for key, value in over.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                base[key].update(value)
            else:
                base[key] = value
        return base

    def dispatch_run(self, **over):
        run = {"id": 12345, "event": "workflow_dispatch",
               "path": ".github/workflows/approve.yml", "conclusion": "success",
               "actor": {"login": "owner"},
               "display_title": "approve intent.md (delegated) on demo by @owner"}
        run.update(over)
        return run

    def grant(self, commit=None, run=None, **kw):
        kw.setdefault("expected_handle", "owner")
        kw.setdefault("slug", "demo")
        return dm.check_grant_commit(commit if commit is not None else self.dispatched_commit(),
                                     self.approvers,
                                     dispatch=run if run is not None else self.dispatch_run(), **kw)

    def test_route_b_with_a_matching_run_is_ok(self):
        verdict, detail = self.grant()
        self.assertEqual(verdict, dm.OK, detail)
        self.assertIn("dispatch run 12345", detail)

    def test_route_b_is_taken_although_the_commit_is_unsigned(self):
        """The whole point of moving the signature gate inside route A: a runner's commit is
        unsigned, so a gate ahead of the route choice refused every dispatch before it began."""
        verdict, detail = self.grant()
        self.assertEqual(verdict, dm.OK, detail)
        self.assertNotIn("not GitHub-verified", detail)

    def test_a_run_of_another_workflow_is_refused(self):
        verdict, detail = self.grant(run=self.dispatch_run(path=".github/workflows/deploy.yml"))
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("path", detail)

    def test_a_run_of_another_event_is_refused(self):
        verdict, detail = self.grant(run=self.dispatch_run(event="push"))
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("event", detail)

    def test_a_failed_run_is_refused(self):
        verdict, detail = self.grant(run=self.dispatch_run(conclusion="failure"))
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("conclusion", detail)

    def test_a_run_started_by_another_actor_is_refused(self):
        verdict, detail = self.grant(run=self.dispatch_run(actor={"login": "mallory"}))
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("mallory", detail)

    def test_a_trailer_actor_that_contradicts_the_run_is_refused(self):
        """The trailer is a claim; the run is the record. When they disagree, the run wins."""
        commit = self.dispatched_commit(
            message="[demo] Approve intent.md\n\nApproved-Run: 12345\nApproved-Actor: mallory\n")
        verdict, detail = self.grant(commit=commit)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("mallory", detail)

    def test_a_run_name_naming_another_slug_is_refused(self):
        run = self.dispatch_run(display_title="approve intent.md (delegated) on other by @owner")
        verdict, detail = self.grant(run=run)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("run-name", detail)

    def test_a_run_name_naming_another_artifact_is_refused(self):
        run = self.dispatch_run(display_title="approve spec.md (supervised) on demo by @owner")
        verdict, detail = self.grant(run=run)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("intent.md", detail)

    def test_no_run_at_all_is_refused_and_never_falls_back(self):
        """A trailer that does not resolve must not be a way to *choose* route A's checks."""
        verdict, detail = self.grant(run=False)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("does not resolve", detail)

    def test_delegated_by_must_match_the_run_actor(self):
        verdict, detail = self.grant(expected_handle="someone-else")
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("someone-else", detail)

    def test_a_dispatched_commit_committed_by_someone_else_is_refused(self):
        commit = self.dispatched_commit(committer={"login": "mallory"})
        verdict, detail = self.grant(commit=commit)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("mallory", detail)

    def test_route_b_does_not_accept_web_flow_as_committer(self):
        """web-flow is route A's signer for web-editor and API commits. Mechanism 1 never produces
        it, so accepting it on route B would widen the route for no case that can arise."""
        commit = self.dispatched_commit(committer={"login": "web-flow"})
        verdict, detail = self.grant(commit=commit)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("web-flow", detail)

    def test_an_actor_without_the_product_owner_role_is_refused(self):
        commit = self.dispatched_commit(
            message="[demo] Approve intent.md\n\nApproved-Run: 12345\nApproved-Actor: mallory\n")
        verdict, detail = self.grant(commit=commit, run=self.dispatch_run(actor={"login": "mallory"}),
                                     expected_handle="mallory")
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("mallory", detail)

    def test_a_commit_with_no_trailer_still_takes_route_a(self):
        commit = make_grant_commit(commit={"message": "[demo] approve intent.md"})
        verdict, detail = dm.check_grant_commit(commit, self.approvers, expected_handle="owner",
                                                dispatch=self.dispatch_run(), slug="demo")
        self.assertEqual(verdict, dm.OK, detail)
        self.assertIn("verified commit", detail)

    def test_commit_adds_grant_reads_the_patch_of_that_file_only(self):
        self.assertTrue(dm.commit_adds_grant(make_grant_commit(), INTENT_PATH))
        self.assertFalse(dm.commit_adds_grant(make_grant_commit(), "work/other/intent.md"))
        touched = make_grant_commit(files=[{"filename": INTENT_PATH,
                                           "patch": "@@\n+title: something\n"}])
        self.assertFalse(dm.commit_adds_grant(touched, INTENT_PATH))

    def test_a_commit_with_no_patch_at_all_is_not_the_grant(self):
        # GitHub omits files[].patch on very large commits; that must read as "no grant".
        huge = make_grant_commit(files=[{"filename": INTENT_PATH}])
        self.assertFalse(dm.commit_adds_grant(huge, INTENT_PATH))


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
        self.assertIn(".github", detail)

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

    def test_the_floor_holds_with_no_policy_at_all(self):
        # Finding 6: ALWAYS_LOCKED is the script's own; `prefixes` only adds. A skill, a workflow
        # that is not under .github/workflows, and CODEOWNERS are all judging surfaces.
        for name in (".claude/skills/x/SKILL.md", ".github/CODEOWNERS", "CLAUDE.md",
                     "docs/sdlc/templates/plan.md", "scripts/checks/front-matter.sh"):
            verdict, detail = dm.check_locked_paths([{"filename": name}], [])
            self.assertEqual(verdict, dm.REFUSED, name)
            self.assertIn(name, detail)

    def test_a_rename_out_of_a_locked_path_is_refused(self):
        # Finding 6: `git mv REVIEW.md notes.md` empties a judging surface, and the entry's
        # `filename` is the harmless new name.
        files = [{"filename": "notes.md", "previous_filename": "REVIEW.md"}]
        verdict, detail = dm.check_locked_paths(files, self.prefixes)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("REVIEW.md", detail)

    def test_the_items_own_intent_is_refused_when_the_runner_adds_it(self):
        # Finding 2: the grant is read from the base, and the diff may not rewrite it either.
        verdict, detail = dm.check_locked_paths([{"filename": INTENT_PATH}],
                                                self.prefixes + [INTENT_PATH])
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn(INTENT_PATH, detail)


# ---------------------------------------------------------------------------
# 7. review
# ---------------------------------------------------------------------------
class ReviewCondition(unittest.TestCase):
    def check(self, comments, runs=None, head_ref=HEAD_REF):
        return dm.check_review(comments, make_runs() if runs is None else runs, head_ref)

    def test_clean_review_is_ok(self):
        verdict, detail = self.check([make_review_comment()])
        self.assertEqual(verdict, dm.OK, detail)
        self.assertIn(str(REVIEW_RUN_ID), detail)

    def test_no_review_comment_waits(self):
        # Fail closed (spec Q3): no pr-review credential means no comment, so the owner decides.
        verdict, detail = self.check([])
        self.assertEqual(verdict, dm.WAITING)
        self.assertIn("claude[bot]", detail)

    def test_a_human_comment_is_not_a_review(self):
        human = {"user": {"login": "owner", "type": "User"},
                 "created_at": REVIEW_TIME,
                 "body": "[View job run](%s)\n\nImportant: 0 | Nits: 0" % REVIEW_RUN_URL}
        verdict, _ = self.check([human])
        self.assertEqual(verdict, dm.WAITING)

    def test_comment_without_the_summary_line_waits(self):
        verdict, detail = self.check([make_review_comment(
            body="Claude is working... [View job run](%s)" % REVIEW_RUN_URL)])
        self.assertEqual(verdict, dm.WAITING)
        self.assertIn("Important", detail)

    def test_important_one_is_refused(self):
        verdict, detail = self.check([make_review_comment(
            body="[View job run](%s)\n\nImportant: 1 | Nits: 0\n" % REVIEW_RUN_URL)])
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("Important: 1", detail)

    def test_a_comment_that_links_no_run_is_ignored(self):
        # Finding 3: the comment API takes any token; only the run binds a verdict to this head.
        forged = make_review_comment(body="LGTM\n\nImportant: 0 | Nits: 0\n")
        verdict, detail = self.check([forged])
        self.assertEqual(verdict, dm.WAITING)
        self.assertIn(str(REVIEW_RUN_ID), detail)

    def test_a_later_comment_carrying_the_link_cannot_overwrite_the_verdict(self):
        # Finding 3: the EARLIEST comment linking the run is the one the action opened; a copy
        # posted afterwards with the same link is somebody else's text.
        tracking = make_review_comment(
            created_at="2026-09-05T11:00:00Z",
            body="[View job run](%s)\n\nImportant: 2 | Nits: 0\n" % REVIEW_RUN_URL)
        forged = make_review_comment(created_at="2026-09-05T11:30:00Z")
        verdict, detail = self.check([forged, tracking])
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("Important: 2", detail)

    def test_a_review_run_of_an_older_head_does_not_count(self):
        # Finding 4: the run list is fetched for this head sha, so a review of an older head is
        # simply not in it -- which is what replaces the timestamp comparison. Here the only
        # pr-review run belongs to another branch's head.
        runs = make_runs(**{"pr-review": {"head_branch": "claude/other-item"}})
        verdict, detail = self.check([make_review_comment()], runs=runs)
        self.assertEqual(verdict, dm.WAITING)
        self.assertIn("no completed pr-review run", detail)

    def test_a_failed_review_run_is_refused(self):
        runs = make_runs(**{"pr-review": {"conclusion": "failure"}})
        verdict, detail = self.check([make_review_comment()], runs=runs)
        self.assertEqual(verdict, dm.REFUSED)
        self.assertIn("failure", detail)

    def test_a_review_run_still_in_progress_waits(self):
        runs = make_runs(**{"pr-review": {"status": "in_progress", "conclusion": None}})
        verdict, detail = self.check([make_review_comment()], runs=runs)
        self.assertEqual(verdict, dm.WAITING)
        self.assertIn("no completed", detail)


# ---------------------------------------------------------------------------
# 8. cool-off
# ---------------------------------------------------------------------------
class CoolOffCondition(unittest.TestCase):
    required = ["sdlc-gate", "agent-evals", "pr-review"]

    def test_zero_hours_is_ok(self):
        verdict, detail = dm.check_cool_off(make_runs(), self.required, 0, NOW, HEAD_REF)
        self.assertEqual(verdict, dm.OK, detail)

    def test_cool_off_not_elapsed_waits(self):
        runs = make_runs(**{"pr-review": {"updated_at": "2026-09-05T11:45:00Z"}})
        verdict, detail = dm.check_cool_off(runs, self.required, 4, NOW, HEAD_REF)
        self.assertEqual(verdict, dm.WAITING)
        self.assertIn("cool-off", detail)

    def test_cool_off_elapsed_is_ok(self):
        verdict, detail = dm.check_cool_off(make_runs(), self.required, 1, NOW, HEAD_REF)
        self.assertEqual(verdict, dm.OK, detail)

    def test_no_required_run_timestamp_waits(self):
        verdict, _ = dm.check_cool_off([], self.required, 4, NOW, HEAD_REF)
        self.assertEqual(verdict, dm.WAITING)

    def test_a_dispatched_run_is_not_a_cool_off_stamp(self):
        # Finding 5: the same filter as the checks condition, or a hand-started run would restart
        # (or satisfy) the clock this pull request has to sit out.
        dispatched = [{"name": "sdlc-gate", "id": 7099, "event": "workflow_dispatch",
                       "head_branch": HEAD_REF, "status": "completed", "conclusion": "success",
                       "updated_at": HEAD_TIME}]
        verdict, _ = dm.check_cool_off(dispatched, self.required, 4, NOW, HEAD_REF)
        self.assertEqual(verdict, dm.WAITING)


# ---------------------------------------------------------------------------
# End to end, through main() with --fixtures. No network: every GET is a file,
# every mutating call is a line in calls.jsonl.
# ---------------------------------------------------------------------------
class Checkout(object):
    """A fixture root: .sdlc/{delegation.yaml,approvers.yaml,config.env,active} plus an API
    fixture dir.

    `set_fixture` writes one response by the same name the script asks for (dm.fixture_name), so a
    renamed endpoint breaks the test loudly instead of silently serving the wrong file. The intent
    and its grant commit are fixtured on the BASE ref, which is where the script reads them.
    """

    def __init__(self, directory, policy_text=FIXTURE_POLICY, active=SLUG):
        self.root = os.path.join(directory, "checkout")
        self.fixtures = os.path.join(directory, "fixtures")
        os.makedirs(self.fixtures, exist_ok=True)
        _write(os.path.join(self.root, ".sdlc", "delegation.yaml"), policy_text)
        _write(os.path.join(self.root, ".sdlc", "approvers.yaml"), FIXTURE_APPROVERS)
        _write(os.path.join(self.root, ".sdlc", "config.env"), FIXTURE_CONFIG)
        _write(os.path.join(self.root, ".sdlc", "active"), active + "\n")
        self.event_path = os.path.join(directory, "event.json")
        _write(self.event_path, json.dumps(make_event()))

    def set_fixture(self, method, path, payload):
        _write(os.path.join(self.fixtures, dm.fixture_name(method, path)),
               json.dumps(payload))

    def set_intent(self, ref, text):
        self.set_fixture("GET", "repos/%s/contents/%s?ref=%s" % (REPO, INTENT_PATH, ref),
                         {"encoding": "base64",
                          "content": base64.b64encode(text.encode("utf-8")).decode("ascii")})

    def happy_path(self):
        self.set_fixture("GET", "repos/%s/commits/%s/pulls" % (REPO, HEAD_SHA), [make_pr()])
        self.set_fixture("GET", "repos/%s/actions/runs?head_sha=%s&per_page=100" % (REPO, HEAD_SHA),
                         {"workflow_runs": make_runs()})
        self.set_fixture("GET", "repos/%s/commits/%s/check-runs?per_page=100" % (REPO, HEAD_SHA),
                         {"check_runs": make_check_runs()})
        self.set_intent(BASE_REF, INTENT_TEXT)
        self.set_fixture("GET", "repos/%s/commits?path=%s&sha=%s&per_page=%d"
                         % (REPO, INTENT_PATH, BASE_REF, dm.GRANT_WINDOW), [{"sha": GRANT_SHA}])
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
        self.assertIn("on %s" % BASE_REF, output)  # the grant was read from the base branch

        calls = checkout.calls()
        by_method = dict((c["method"], c) for c in calls)
        merge = by_method["PUT"]
        self.assertEqual(merge["path"], "repos/%s/pulls/12/merge" % REPO)
        self.assertEqual(merge["fields"]["sha"], HEAD_SHA)
        self.assertEqual(merge["fields"]["merge_method"], "merge")
        # Nit f: the title names the pull request, not the head label the branch chose.
        self.assertEqual(merge["fields"]["commit_title"],
                         "Merge pull request #12 (delegated)")
        self.assertNotIn(HEAD_REF, merge["fields"]["commit_title"])

        self.assertEqual(by_method["DELETE"]["path"],
                         "repos/%s/git/refs/heads/%s" % (REPO, HEAD_REF))

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
        checkout.set_intent(BASE_REF, INTENT_TEXT.replace("mode: delegated", "mode: supervised"))
        code, output = self.run_main(checkout, "--dry-run")
        self.assertEqual(code, 1, output)
        self.assertIn("CONDITION grant: refused", output)
        self.assertIn("DELEGATED-MERGE: dry-run (refused: grant)", output)
        self.assertEqual(checkout.calls(), [])

    def test_a_grant_that_exists_only_on_the_head_is_refused(self):
        # Finding 2: the head's intent.md is written by the branch under judgement. The base ref
        # is the only copy read, so a delegated intent pushed to the head changes nothing.
        checkout = Checkout(self.tmp.name).happy_path()
        checkout.set_intent(BASE_REF, INTENT_TEXT.replace("mode: delegated", "mode: supervised"))
        checkout.set_intent(HEAD_SHA, INTENT_TEXT)
        code, output = self.run_main(checkout)
        self.assertEqual(code, 1, output)
        self.assertIn("CONDITION grant: refused", output)
        self.assertIn("supervised", output)
        self.assertEqual(checkout.calls(), [])

    def test_a_diff_touching_the_items_own_intent_is_refused(self):
        # Finding 2: the grant is read from the base; the pull request may not rewrite it.
        checkout = Checkout(self.tmp.name).happy_path()
        checkout.set_fixture("GET", "repos/%s/pulls/12/files?per_page=100" % REPO,
                             [{"filename": INTENT_PATH}])
        code, output = self.run_main(checkout)
        self.assertEqual(code, 1, output)
        self.assertIn("DELEGATED-MERGE: refused (locked-paths)", output)
        self.assertIn(INTENT_PATH, output)
        self.assertEqual(checkout.calls(), [])

    def test_a_slug_that_is_not_the_active_work_item_is_refused(self):
        # Finding 7: .sdlc/active comes from this job's own checkout of the base branch.
        checkout = Checkout(self.tmp.name, active="another-item").happy_path()
        code, output = self.run_main(checkout)
        self.assertEqual(code, 1, output)
        self.assertIn("DELEGATED-MERGE: refused (pull-request)", output)
        self.assertIn("another-item", output)
        self.assertEqual(checkout.calls(), [])

    def test_a_review_comment_without_the_run_link_waits(self):
        # Finding 3: any token can post `Important: 0`; only the run backs it.
        checkout = Checkout(self.tmp.name).happy_path()
        checkout.set_fixture("GET", "repos/%s/issues/12/comments?per_page=100" % REPO,
                             [make_review_comment(body="Important: 0 | Nits: 0\n")])
        code, output = self.run_main(checkout)
        self.assertEqual(code, 0, output)
        self.assertIn("DELEGATED-MERGE: waiting (review)", output)
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

    def test_head_sha_that_is_not_a_sha_is_a_usage_error(self):
        # Nit e: the value comes from a workflow_dispatch input and is interpolated into API paths.
        checkout = Checkout(self.tmp.name).happy_path()
        err = io.StringIO()
        saved = sys.stderr
        sys.stderr = err
        try:
            code = dm.main(["--root", checkout.root, "--fixtures", checkout.fixtures,
                            "--head-sha", "main; rm -rf /", "--repo", REPO])
        finally:
            sys.stderr = saved
        self.assertEqual(code, 2, err.getvalue())
        self.assertIn("hex", err.getvalue())
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

    def test_merge_comment_body_normalises_the_handle(self):
        # Nit c: front matter is a field the branch fills in; the record carries the login.
        body = dm.merge_comment_body("@Owner  <owner@example.com>", GRANT_SHA)
        self.assertIn("granted by owner in", body)
        self.assertNotIn("@Owner", body)

    def test_the_grant_window_is_sliced_off_a_paginated_answer(self):
        # Nit a: `gh api` GET paginates, so per_page bounds a page, not the answer -- the refusal
        # says "the last 100 commits" and must mean it.
        calls = []
        many = [{"sha": "%040d" % i} for i in range(dm.GRANT_WINDOW + 25)]

        def api(method, path, fields=None):
            calls.append(path)
            if "/commits?" in path:
                return many
            return {"sha": path.rsplit("/", 1)[-1], "files": []}

        saved = dm.API
        dm.API = api
        try:
            self.assertIsNone(dm._grant_commit(REPO, SLUG, BASE_REF))
        finally:
            dm.API = saved
        self.assertIn("sha=%s" % BASE_REF, calls[0])
        self.assertEqual(len(calls) - 1, dm.GRANT_WINDOW)

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

    def test_read_active_slug_strips_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(dm.read_active_slug(d), "")
            _write(os.path.join(d, ".sdlc", "active"), "%s\n" % SLUG)
            self.assertEqual(dm.read_active_slug(d), SLUG)


ADVANCE_INTENT = """\
---
type: sdlc/intent
status: approved
mode: delegated
delegated-by: luissiviero
delegated-on: %s
risk-class: low
---
# intent
"""

ADVANCE_LOG = """\
---
type: sdlc/log
id: %s-log
---
# Log

- 2026-01-01T00:00:00Z | intent.md | in-review -> approved | luissiviero | abc1234 | granted
"""


class Advance(unittest.TestCase):
    """work/run-queue R-2, R-3, R-5: after a merge the pointer moves to the next queued item, both
    ledgers record it, and nothing outside the allowlist is ever committed.

    The fixture is a real git repository with a real bare remote, so the commit, the staged-path
    guard and the push are exercised rather than mocked. Identity and time are the fixture's own
    (knowledge/lessons/tests-carry-their-own-environment.md): the runner has no git identity, and
    the advance must supply its own.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = os.path.join(self.tmp.name, "checkout")
        self.remote = os.path.join(self.tmp.name, "remote.git")
        subprocess.run(["git", "init", "-q", "--bare", self.remote], check=True)
        _write(os.path.join(self.root, ".sdlc", "delegation.yaml"), FIXTURE_POLICY)
        _write(os.path.join(self.root, ".sdlc", "active"), "merged-item\n")
        for slug, on in (("merged-item", "2026-09-01"), ("next-item", "2026-09-02"),
                         ("later-item", "2026-09-03")):
            _write(os.path.join(self.root, "work", slug, "intent.md"), ADVANCE_INTENT % on)
            _write(os.path.join(self.root, "work", slug, "log.md"), ADVANCE_LOG % slug)
        # merged-item is already worked; the other two are unstarted and so form the queue.
        _write(os.path.join(self.root, "work", "merged-item", "spec.md"),
               "---\ntype: sdlc/spec\nstatus: delegated\n---\n# spec\n")
        self._git("init", "-q", "-b", "main")
        self._git("remote", "add", "origin", self.remote)
        self._git("add", "-A")
        self._commit("fixture")
        self._git("push", "-q", "origin", "main")
        self.policy = delegation.load(path=os.path.join(self.root, ".sdlc", "delegation.yaml"))
        self.out = dm.Run(dry_run=False, stream=io.StringIO())

    def _git(self, *args):
        return subprocess.run(["git", "-C", self.root, *args], capture_output=True, text=True,
                              check=True).stdout.strip()

    def _commit(self, message):
        # The runner has no git identity; the fixture carries its own.
        self._git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.com",
                  "commit", "-q", "-m", message)

    def _pointer(self):
        return dm.read_active_slug(self.root)

    def _log(self, slug):
        with open(os.path.join(self.root, "work", slug, "log.md"), encoding="utf-8") as f:
            return f.read()

    def test_advances_to_the_next_queued_item(self):
        result = dm.advance(self.root, self.out, "merged-item", 12, self.policy)
        self.assertEqual(result, "next-item")
        self.assertEqual(self._pointer(), "next-item")
        self.assertIn("ADVANCE: .sdlc/active -> next-item", self.out.stream.getvalue())

    def test_the_commit_is_pushed_and_carries_the_bot_identity(self):
        dm.advance(self.root, self.out, "merged-item", 12, self.policy)
        self.assertEqual(self._git("status", "--porcelain"), "")
        self.assertEqual(self._git("log", "-1", "--format=%an"), dm.ADVANCE_IDENTITY[0])
        self.assertIn("Advance .sdlc/active after #12 merged", self._git("log", "-1", "--format=%s"))
        remote_head = subprocess.run(["git", "-C", self.remote, "log", "-1", "--format=%s", "main"],
                                     capture_output=True, text=True).stdout
        self.assertIn("Advance .sdlc/active after #12 merged", remote_head)

    def test_ledger_lines_parse_and_name_both_items(self):
        dm.advance(self.root, self.out, "merged-item", 12, self.policy)
        for slug, expected in (("merged-item", "advanced to next-item"),
                               ("next-item", "advanced here after PR #12 merged")):
            path = os.path.join(self.root, "work", slug, "log.md")
            entries, malformed = log_ledger.parse(path)
            self.assertEqual(malformed, [], "%s: %s" % (slug, malformed))
            self.assertIn(expected, entries[-1].note)
            # The literal string from spec.md R-3, not dm.ADVANCE_IDENTITY: asserting the code's own
            # constant pins nothing, and let the spec and the code disagree unnoticed until the
            # plan-conformance pass on pull request 55 read both (revision 1).
            self.assertEqual(entries[-1].actor, "github-actions[bot]")
        # The from/to slot holds status values only (knowledge/lessons/ledger-slot-holds-status-only.md).
        merged_last = log_ledger.parse(os.path.join(self.root, "work", "merged-item", "log.md"))[0][-1]
        self.assertEqual((merged_last.from_status, merged_last.to_status), ("in-review", "in-review"))
        self.assertIn("under the grant by luissiviero on 2026-09-02", self._log("next-item"))

    def test_a_stale_pointer_is_a_lost_update_and_writes_nothing(self):
        """Another run advanced first: the pointer no longer names the merged item, so this one
        stands down rather than overwriting a newer decision."""
        _write(os.path.join(self.root, ".sdlc", "active"), "someone-else\n")
        self._git("add", "-A")
        self._commit("another run advanced first")
        before = self._git("rev-parse", "HEAD")
        self.assertIsNone(dm.advance(self.root, self.out, "merged-item", 12, self.policy))
        self.assertEqual(self._pointer(), "someone-else")
        self.assertEqual(self._git("rev-parse", "HEAD"), before)
        self.assertIn("not advancing", self.out.stream.getvalue())

    def test_an_empty_queue_clears_the_pointer_and_says_so(self):
        for slug in ("next-item", "later-item"):
            _write(os.path.join(self.root, "work", slug, "spec.md"),
                   "---\ntype: sdlc/spec\nstatus: delegated\n---\n# spec\n")
        self._git("add", "-A")
        self._commit("both remaining items already started")
        self.assertIsNone(dm.advance(self.root, self.out, "merged-item", 12, self.policy))
        self.assertEqual(self._pointer(), "")
        self.assertIn("the queue is empty", self._log("merged-item"))
        self.assertIn("(empty queue)", self.out.stream.getvalue())

    def test_a_staged_stray_path_never_reaches_the_commit(self):
        """A stray modification in the tree must not ride along in the advance commit. The clean-tree
        precondition catches it first (that is the point of adding it after the security pass); the
        staged-path allowlist behind it stays as a second line of defence, asserted below on the
        function itself rather than through a path that can no longer reach it."""
        _write(os.path.join(self.root, "scripts", "smuggled.py"), "print('x')\n")
        self._git("add", "-A")
        before = self._git("rev-parse", "HEAD")
        self.assertIsNone(dm.advance(self.root, self.out, "merged-item", 12, self.policy))
        self.assertEqual(self._git("rev-parse", "HEAD"), before)
        self.assertIn("the checkout is not clean", self.out.stream.getvalue())
        self.assertIn("scripts/smuggled.py", self.out.stream.getvalue())
        with open(dm.__file__, encoding="utf-8") as f:
            self.assertIn("outside the advance allowlist", f.read())

    def test_a_failed_push_leaves_the_run_reporting_the_merge(self):
        """A rejected push is a note, never an exception: the merge already happened."""
        self._git("remote", "set-url", "origin", os.path.join(self.tmp.name, "no-such-remote.git"))
        self.assertIsNone(dm.advance(self.root, self.out, "merged-item", 12, self.policy))
        self.assertIn("not pushed", self.out.stream.getvalue())

    def test_run_without_a_root_never_advances(self):
        """Every existing caller passes no root (the 111 cases below), and must keep working."""
        self.assertEqual(dm.run.__defaults__[-1], "")

    def test_a_dirty_tree_writes_nothing(self):
        """Security pass on pull request 55, nit 2: the allowlist bounds which files are committed,
        not what is inside them, so an already-dirty file would have ridden along in `git add`. A
        checkout that is not clean is refused before anything is written."""
        with open(os.path.join(self.root, "work", "next-item", "log.md"), "a", encoding="utf-8") as f:
            f.write("- smuggled text nobody staged\n")
        before = self._git("rev-parse", "HEAD")
        self.assertIsNone(dm.advance(self.root, self.out, "merged-item", 12, self.policy))
        self.assertEqual(self._pointer(), "merged-item")
        self.assertEqual(self._git("rev-parse", "HEAD"), before)
        self.assertIn("the checkout is not clean", self.out.stream.getvalue())

    def test_a_pipe_in_a_grant_field_cannot_break_the_ledger_line(self):
        """Security pass, nit 4: `delegated-by` is hand-typed and lands in a pipe-separated field.
        A `|` there would push the line past six fields, and log_ledger would call the whole line
        malformed -- silently dropping the record this feature exists to write."""
        _write(os.path.join(self.root, "work", "next-item", "intent.md"),
               ADVANCE_INTENT.replace("delegated-by: luissiviero",
                                      "delegated-by: luis | siviero") % "2026-09-02")
        self._git("add", "-A")
        self._commit("a grant handle with a pipe in it")
        dm.advance(self.root, self.out, "merged-item", 12, self.policy)
        entries, malformed = log_ledger.parse(os.path.join(self.root, "work", "next-item", "log.md"))
        self.assertEqual(malformed, [], malformed)
        self.assertIn("luis / siviero", entries[-1].note)

    def test_a_non_utf8_intent_in_the_queue_is_a_note_not_a_crash(self):
        """Security pass, nit 3: the merge already happened, so a decode error while reading the
        next item's grant must not fail the job for work that landed."""
        with open(os.path.join(self.root, "work", "next-item", "intent.md"), "wb") as f:
            f.write(b"---\nstatus: approved\nmode: delegated\ndelegated-by: \xff\xfe\n---\n")
        self._git("add", "-A")
        self._commit("a next item that is not utf-8")
        with self.assertRaises(UnicodeDecodeError):
            dm.advance(self.root, self.out, "merged-item", 12, self.policy)
        # run() turns exactly that into a note instead of a failed job, because the except tuple it
        # wraps advance() in covers ValueError, and UnicodeDecodeError is one.
        self.assertTrue(issubclass(UnicodeDecodeError, ValueError))
        with open(dm.__file__, encoding="utf-8") as f:
            self.assertIn("except (OSError, ValueError, MergeError)", f.read())

    def test_dry_run_never_advances(self):
        """R-2: `--dry-run` prints its verdict and writes nothing -- pinned here rather than left to
        EndToEnd, which only asserts that no GitHub call was made (plan-conformance nit)."""
        before = self._git("rev-parse", "HEAD")
        out = dm.Run(dry_run=True, stream=io.StringIO())
        out.finish(merged=12)
        self.assertEqual(self._pointer(), "merged-item")
        self.assertEqual(self._git("rev-parse", "HEAD"), before)
        self.assertIn("dry-run", out.stream.getvalue())


if __name__ == "__main__":
    unittest.main()
