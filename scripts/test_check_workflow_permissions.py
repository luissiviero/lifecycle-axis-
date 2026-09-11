import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(HERE, "check_workflow_permissions.py")

spec = importlib.util.spec_from_file_location("check_workflow_permissions", SCRIPT)
cwp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cwp)


def _write(root, name, body):
    path = os.path.join(root, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    return path


def _run(args, cwd=None):
    return subprocess.run(
        [sys.executable, SCRIPT] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def _last_line(text):
    lines = [l for l in text.splitlines() if l.strip()]
    return lines[-1] if lines else ""


CONFORMING = """\
name: example
on:
  pull_request:
    types: [opened]
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
"""


class CheckFile(unittest.TestCase):
    """Direct check_file() tests -- one violating / one conforming fixture per rule."""

    def test_missing_top_level_permissions_is_a_violation(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write(d, "bad.yml", "name: x\non:\n  push: {}\njobs:\n  b:\n    runs-on: ubuntu-latest\n")
            violations = cwp.check_file(path)
            rules = [r for _, r, _ in violations]
            self.assertIn("missing-permissions", rules)

    def test_conforming_workflow_has_no_violations(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write(d, "good.yml", CONFORMING)
            self.assertEqual(cwp.check_file(path), [])

    def test_permissions_read_all_is_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write(d, "good.yml", "name: x\non:\n  push: {}\npermissions: read-all\njobs:\n  b:\n    runs-on: ubuntu-latest\n")
            self.assertEqual(cwp.check_file(path), [])

    def test_permissions_empty_map_is_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write(d, "good.yml", "name: x\non:\n  push: {}\npermissions: {}\njobs:\n  b:\n    runs-on: ubuntu-latest\n")
            self.assertEqual(cwp.check_file(path), [])

    def test_permissions_write_all_is_a_violation(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write(d, "bad.yml", "name: x\non:\n  push: {}\npermissions: write-all\njobs:\n  b:\n    runs-on: ubuntu-latest\n")
            violations = cwp.check_file(path)
            rules = [r for _, r, _ in violations]
            self.assertIn("permissions-write-all", rules)

    def test_contents_write_at_workflow_level_is_a_violation(self):
        body = "name: x\non:\n  push: {}\npermissions:\n  contents: write\njobs:\n  b:\n    runs-on: ubuntu-latest\n"
        with tempfile.TemporaryDirectory() as d:
            path = _write(d, "bad.yml", body)
            violations = cwp.check_file(path)
            rules = [r for _, r, _ in violations]
            self.assertIn("contents-write", rules)

    def test_contents_write_at_job_level_is_a_violation(self):
        body = (
            "name: x\non:\n  push: {}\npermissions:\n  contents: read\n"
            "jobs:\n  b:\n    runs-on: ubuntu-latest\n    permissions:\n      contents: write\n"
        )
        with tempfile.TemporaryDirectory() as d:
            path = _write(d, "bad.yml", body)
            violations = cwp.check_file(path)
            rules = [r for _, r, _ in violations]
            self.assertIn("contents-write", rules)

    def test_allowlist_matches_relative_path(self):
        # work/delegated-mode R-14: default_files() yields absolute paths, and the allowlist
        # holds repo-relative ones, so the comparison must normalise or no entry ever matches.
        body = CONFORMING.replace("contents: read", "contents: write")
        with tempfile.TemporaryDirectory() as d:
            wf = os.path.join(d, ".github", "workflows")
            os.makedirs(wf)
            allowed = _write(wf, "delegated-merge.yml", body)
            other = _write(wf, "other.yml", body)
            rules = [r for _, r, _ in cwp.check_file(allowed, root=d)]
            self.assertNotIn("contents-write", rules, "the allowlisted file, passed as an absolute path")
            self.assertIn("contents-write", [r for _, r, _ in cwp.check_file(other, root=d)])
            # A relative argument is resolved against the working directory, as any CLI path is.
            rel = _run([os.path.join(".github", "workflows", "delegated-merge.yml"), "--root", d], cwd=d)
            self.assertEqual(rel.returncode, 0, rel.stdout)
            # The CLI resolves against --root the same way.
            result = _run(["--root", d])
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("other.yml", result.stdout)
            self.assertNotIn("delegated-merge.yml:", result.stdout)

    def test_contents_read_is_not_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write(d, "good.yml", CONFORMING)
            rules = [r for _, r, _ in cwp.check_file(path)]
            self.assertNotIn("contents-write", rules)

    def test_pull_request_target_is_a_violation(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write(
                d, "bad.yml",
                "name: x\non:\n  pull_request_target:\n    types: [opened]\npermissions:\n  contents: read\njobs:\n  b:\n    runs-on: ubuntu-latest\n",
            )
            violations = cwp.check_file(path)
            rules = [r for _, r, _ in violations]
            self.assertIn("pull-request-target", rules)

    def test_pull_request_is_not_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write(d, "good.yml", CONFORMING)
            rules = [r for _, r, _ in cwp.check_file(path)]
            self.assertNotIn("pull-request-target", rules)

    def test_anchor_definition_is_a_violation(self):
        body = "name: x\non:\n  push: {}\npermissions:\n  contents: read\ndefaults: &defaults\n  run:\n    shell: bash\njobs:\n  b:\n    runs-on: ubuntu-latest\n"
        with tempfile.TemporaryDirectory() as d:
            path = _write(d, "bad.yml", body)
            violations = cwp.check_file(path)
            rules = [r for _, r, _ in violations]
            self.assertIn("unsupported-yaml-feature", rules)

    def test_alias_reference_is_a_violation(self):
        body = "name: x\non:\n  push: {}\npermissions: *shared_perms\njobs:\n  b:\n    runs-on: ubuntu-latest\n"
        with tempfile.TemporaryDirectory() as d:
            path = _write(d, "bad.yml", body)
            violations = cwp.check_file(path)
            rules = [r for _, r, _ in violations]
            self.assertIn("unsupported-yaml-feature", rules)

    def test_quoted_glob_starting_with_star_is_not_an_alias(self):
        # `paths: ['*.md']` and `- cron: '0 2 * * *'` must not be mistaken for aliases.
        body = (
            "name: x\non:\n  pull_request:\n    paths: ['*.md']\n  schedule:\n"
            "    - cron: '0 2 * * *'\npermissions:\n  contents: read\njobs:\n  b:\n    runs-on: ubuntu-latest\n"
        )
        with tempfile.TemporaryDirectory() as d:
            path = _write(d, "good.yml", body)
            self.assertEqual(cwp.check_file(path), [])

    def test_comment_with_contents_write_is_ignored(self):
        body = (
            "name: x\n# example: contents: write is not allowed here\non:\n  push: {}\n"
            "permissions:\n  contents: read # not contents: write\njobs:\n  b:\n    runs-on: ubuntu-latest\n"
        )
        with tempfile.TemporaryDirectory() as d:
            path = _write(d, "good.yml", body)
            self.assertEqual(cwp.check_file(path), [])

    def test_comment_with_pull_request_target_is_ignored(self):
        body = "name: x\n# do not use pull_request_target\non:\n  push: {}\npermissions:\n  contents: read\njobs:\n  b:\n    runs-on: ubuntu-latest\n"
        with tempfile.TemporaryDirectory() as d:
            path = _write(d, "good.yml", body)
            self.assertEqual(cwp.check_file(path), [])

    def test_violation_message_names_file_and_line(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write(d, "bad.yml", "name: x\non:\n  push: {}\npermissions: write-all\njobs:\n  b:\n    runs-on: ubuntu-latest\n")
            violations = cwp.check_file(path)
            lineno, rule, detail = violations[0]
            self.assertEqual(lineno, 4)
            self.assertEqual(rule, "permissions-write-all")
            self.assertTrue(detail)


class CLI(unittest.TestCase):
    def test_conforming_dir_exits_zero(self):
        with tempfile.TemporaryDirectory() as d:
            wf = os.path.join(d, ".github", "workflows")
            os.makedirs(wf)
            _write(d, os.path.join(".github", "workflows", "good.yml"), CONFORMING)
            result = _run(["--root", d])
            self.assertEqual(result.returncode, 0)
            self.assertRegex(_last_line(result.stdout), r"^WORKFLOWS: 1 files, 0 violations$")

    def test_violating_dir_exits_nonzero_and_prints_violation_line(self):
        with tempfile.TemporaryDirectory() as d:
            wf = os.path.join(d, ".github", "workflows")
            os.makedirs(wf)
            _write(
                d, os.path.join(".github", "workflows", "bad.yml"),
                "name: x\non:\n  push: {}\npermissions:\n  contents: write\njobs:\n  b:\n    runs-on: ubuntu-latest\n",
            )
            result = _run(["--root", d])
            self.assertEqual(result.returncode, 1)
            self.assertIn("VIOLATION", result.stdout)
            self.assertIn("bad.yml:5 contents-write", result.stdout)
            self.assertRegex(_last_line(result.stdout), r"^WORKFLOWS: 1 files, 1 violations$")

    def test_empty_workflows_dir_exits_zero(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, ".github", "workflows"))
            result = _run(["--root", d])
            self.assertEqual(result.returncode, 0)
            self.assertRegex(_last_line(result.stdout), r"^WORKFLOWS: 0 files, 0 violations$")

    def test_explicit_file_arguments_override_default_glob(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, ".github", "workflows"))
            good = _write(d, os.path.join(".github", "workflows", "good.yml"), CONFORMING)
            _write(
                d, os.path.join(".github", "workflows", "bad.yml"),
                "name: x\non:\n  push: {}\npermissions: write-all\njobs:\n  b:\n    runs-on: ubuntu-latest\n",
            )
            result = _run([good])
            self.assertEqual(result.returncode, 0)
            self.assertRegex(_last_line(result.stdout), r"^WORKFLOWS: 1 files, 0 violations$")


class RealRepo(unittest.TestCase):
    """This task's own file (pr-review.yml) must be clean. Violations found
    elsewhere in .github/workflows/ are reported (stderr), not asserted here --
    those files may belong to another task's in-progress work (see T20 spec)."""

    def test_pr_review_workflow_is_clean(self):
        path = os.path.join(ROOT, ".github", "workflows", "pr-review.yml")
        self.assertTrue(os.path.exists(path), "pr-review.yml must exist")
        violations = cwp.check_file(path)
        self.assertEqual(violations, [], f"pr-review.yml violations: {violations}")

    def test_real_workflows_directory(self):
        owned = os.path.join(ROOT, ".github", "workflows", "pr-review.yml")
        reported = []
        for path in cwp.default_files(ROOT):
            for lineno, rule, detail in cwp.check_file(path):
                if path == owned:
                    self.fail(f"{path}:{lineno} {rule} {detail}")
                reported.append(f"{path}:{lineno} {rule} {detail}")
        if reported:
            print(
                "NOTE: .github/workflows/ has violations outside this task's file "
                "(likely another task's in-progress workflow -- not edited here):",
                file=sys.stderr,
            )
            for line in reported:
                print(f"  {line}", file=sys.stderr)


class SdlcGate(unittest.TestCase):
    """R-13: the chain check's one new API surface is granted explicitly, not left to the code.

    A scope the code needs and the workflow does not declare fails open here rather than loudly:
    verify_dispatch_run finds no token, prints its note, and the attestation is never checked in the
    one place it matters. So the oracle reads the parsed permissions block and the step's env,
    rather than trusting that a token happens to be present at run time
    (knowledge/lessons/workflow-permissions-name-every-api.md).
    """

    PATH = os.path.join(ROOT, ".github", "workflows", "sdlc-gate.yml")

    def setUp(self):
        import yaml

        with open(self.PATH, encoding="utf-8") as f:
            self.doc = yaml.safe_load(f)
        # YAML 1.1 reads a bare `on:` key as the boolean True (as ApproveWorkflow notes below).
        self.triggers = self.doc[True] if True in self.doc else self.doc["on"]
        self.job = self.doc["jobs"]["artifact-chain"]

    def test_permissions_are_exactly_contents_read_and_actions_read(self):
        self.assertEqual(self.doc["permissions"], {"contents": "read", "actions": "read"})

    # work/ci-budget R-1 and R-2. The gate ran on every push to every pull request, draft or not,
    # with no concurrency group, and installed the CLI to triage any red run. These four oracles
    # are what "a draft costs nothing, a superseded run is cancelled, and a model reads a failure
    # only when the owner asks" means in the file.

    def test_ready_for_review_triggers(self):
        types = self.triggers["pull_request"]["types"]
        # Without this, a pull request that lived as a draft gets no gate run until its next push.
        self.assertIn("ready_for_review", types)
        # The six that were there stay: a human's body edit still runs, and the labels still do.
        for kept in ("opened", "synchronize", "reopened", "edited", "labeled", "unlabeled"):
            self.assertIn(kept, types)

    def test_skips_drafts_and_bot_edits(self):
        guard = " ".join((self.job.get("if") or "").split())
        self.assertIn("github.event.pull_request.draft == false", guard)
        # A Bot editing the body (an app's summary or tracking comment) changes nothing the gate
        # reads, and used to buy a second full run on the same sha.
        self.assertIn("github.event.action == 'edited'", guard)
        self.assertIn("github.event.sender.type == 'Bot'", guard)

    def test_cancels_only_on_synchronize(self):
        self.assertIn("concurrency", self.doc, "the gate declares no concurrency group")
        group = str(self.doc["concurrency"]["group"])
        self.assertIn("github.event.pull_request.number", group)
        # Only a new push supersedes a run. A same-sha re-trigger (a label, a human edit, going
        # ready) queues behind it instead, so the head sha never carries a cancelled run.
        cancel = str(self.doc["concurrency"]["cancel-in-progress"])
        self.assertIn("github.event.action == 'synchronize'", cancel)

    def test_triage_is_label_gated(self):
        label_clause = "contains(github.event.pull_request.labels.*.name, 'triage')"
        on_failure, gated = [], []
        for step in self.job["steps"]:
            guard = " ".join(str(step.get("if") or "").split())
            if "failure()" in guard:
                on_failure.append(step.get("name"))
            if label_clause in guard:
                gated.append(step.get("name"))
        self.assertEqual(len(on_failure), 2, "the trust and triage steps are the failure() pair")
        # Both, and nothing else: a step that installs the CLI without the label is the cost this
        # requirement removes, and a label clause anywhere else would gate a check that must run.
        self.assertEqual(sorted(gated), sorted(on_failure))

    def test_the_artifact_chain_step_receives_gh_token(self):
        steps = self.doc["jobs"]["artifact-chain"]["steps"]
        chain = [s for s in steps if "check_artifact_chain.py" in (s.get("run") or "")]
        self.assertEqual(len(chain), 1, "exactly one step runs the chain check")
        self.assertIn("GH_TOKEN", chain[0].get("env", {}))

    def test_no_other_workflow_gains_a_scope(self):
        # The two that already declared `actions` keep it and gain nothing: delegated-merge.yml
        # reads runs for R-7's route B, bands.yml reads its own run history for the metrics
        # series. sdlc-gate.yml is the only file this work item adds the scope to.
        import yaml

        wf = os.path.join(ROOT, ".github", "workflows")
        with_actions = []
        for name in sorted(os.listdir(wf)):
            if not name.endswith((".yml", ".yaml")):
                continue
            with open(os.path.join(wf, name), encoding="utf-8") as f:
                perms = (yaml.safe_load(f) or {}).get("permissions")
            if isinstance(perms, dict) and "actions" in perms:
                with_actions.append(name)
        self.assertEqual(with_actions, ["bands.yml", "delegated-merge.yml", "sdlc-gate.yml"])


class ApproveWorkflow(unittest.TestCase):
    """R-1: the dispatch workflow is clean, allowlisted, and as small as it claims to be."""

    PATH = os.path.join(ROOT, ".github", "workflows", "approve.yml")

    def setUp(self):
        import yaml

        self.assertTrue(os.path.exists(self.PATH), "approve.yml must exist")
        with open(self.PATH, encoding="utf-8") as f:
            self.text = f.read()
        self.doc = yaml.safe_load(self.text)
        # YAML 1.1 reads a bare `on:` key as the boolean True, which is why this is not doc["on"].
        self.triggers = self.doc[True] if True in self.doc else self.doc["on"]

    def test_is_clean_under_the_checker(self):
        self.assertEqual(cwp.check_file(self.PATH), [])

    def test_is_allowlisted_for_contents_write(self):
        self.assertIn(".github/workflows/approve.yml", cwp.CONTENTS_WRITE_ALLOWLIST)

    def test_declares_contents_write_and_no_other_scope(self):
        self.assertEqual(self.doc["permissions"], {"contents": "write"})

    def test_checks_out_exactly_once(self):
        # A second checkout would be a second ref in play, and the whole design rests on the
        # dispatch ref being the only thing this workflow reads and writes (D3).
        self.assertEqual(self.text.count("actions/checkout"), 1)

    def test_installs_no_dependency(self):
        for forbidden in ("pip install", "npm install", "setup-python", "setup-node"):
            self.assertNotIn(forbidden, self.text)

    def test_is_dispatch_only(self):
        self.assertEqual(list(self.triggers), ["workflow_dispatch"])

    def test_offers_the_four_inputs(self):
        inputs = self.triggers["workflow_dispatch"]["inputs"]
        self.assertEqual(sorted(inputs), ["artifact", "mode", "note", "slug"])
        self.assertEqual(inputs["artifact"]["options"],
                         ["intent.md", "spec.md", "plan.md", "incident.md"])
        self.assertEqual(inputs["mode"]["options"], ["supervised", "delegated"])

    def test_run_name_carries_actor_slug_artifact_and_mode(self):
        run_name = self.doc["run-name"]
        for fragment in ("github.actor", "inputs.slug", "inputs.artifact", "inputs.mode"):
            self.assertIn(fragment, run_name)

    def test_run_name_still_matches_the_checker_that_parses_it(self):
        """check_artifact_chain.RUN_NAME_RE parses this title to tell a blank slug segment from a
        different one. If the format drifts, the parse fails and the slug binding quietly stops
        applying — so pin the two together rather than leaving it to a comment."""
        import re as _re
        import sys as _sys

        if HERE not in _sys.path:
            _sys.path.insert(0, HERE)
        import check_artifact_chain as cac

        # Render the template the way GitHub would, for a filled and a blank slug.
        for slug in ("demo", ""):
            rendered = self.doc["run-name"]
            for expr, value in (("inputs.artifact", "spec.md"), ("inputs.mode", "supervised"),
                                ("inputs.slug", slug), ("github.actor", "owner")):
                rendered = _re.sub(r"\$\{\{\s*%s\s*\}\}" % _re.escape(expr), value, rendered)
            match = cac.RUN_NAME_RE.match(rendered)
            self.assertIsNotNone(match, "RUN_NAME_RE no longer parses %r" % rendered)
            self.assertEqual(match.group("slug"), slug)
            self.assertEqual(match.group("artifact"), "spec.md")


if __name__ == "__main__":
    unittest.main()



class PrReviewWorkflow(unittest.TestCase):
    """work/ci-budget R-3: one review per ready push, and on the `@claude` comment route the
    reviewer takes both its policy and its configuration from the base branch.

    The action restores `.claude/` and `CLAUDE.md` from base on `pull_request` events only, and the
    comment route checks out `refs/pull/N/head` with the credential in hand. So a branch could hand
    the reviewer its own instructions, which is the same class of problem REVIEW.md was already
    pinned against (spec C4), and a fork's head could be checked out at all (A2b).
    """

    PATH = os.path.join(ROOT, ".github", "workflows", "pr-review.yml")

    def setUp(self):
        import yaml

        with open(self.PATH, encoding="utf-8") as f:
            self.text = f.read()
        self.doc = yaml.safe_load(self.text)
        self.steps = self.doc["jobs"]["review"]["steps"]

    def _step(self, needle):
        for step in self.steps:
            if needle in str(step.get("name") or "") or needle in str(step.get("uses") or ""):
                return step
        self.fail("no step matching %r" % needle)

    def test_concurrency(self):
        self.assertIn("concurrency", self.doc, "pr-review declares no concurrency group")
        group = str(self.doc["concurrency"]["group"])
        # Both triggers: a pull_request event carries the number, an issue_comment the issue's.
        self.assertIn("github.event.pull_request.number", group)
        self.assertIn("github.event.issue.number", group)
        cancel = str(self.doc["concurrency"]["cancel-in-progress"])
        self.assertIn("github.event.action == 'synchronize'", cancel)

    def test_fork_guard_precedes_checkout(self):
        names = [str(s.get("name") or s.get("uses") or "") for s in self.steps]
        guard = self._step("head repository")
        checkout = self._step("actions/checkout")
        self.assertLess(names.index(str(guard.get("name"))), names.index(str(checkout.get("name"))),
                        "the guard must run before the head is checked out, not beside it")
        self.assertIn("issue_comment", str(guard.get("if")))
        # It gates the checkout rather than only reporting: the checkout's own condition reads it.
        self.assertIn("steps.local.outputs.ok", str(checkout.get("if")))

    def test_pins_agent_config_from_base_on_comments(self):
        pin = self._step("Pin review policy")
        run = str(pin.get("run") or "")
        for path in ("REVIEW.md", "CLAUDE.md", "GEMINI.md", "AGENTS.md", ".claude"):
            self.assertIn(path, run, path)

    def test_draft_skip_and_no_bash_unchanged(self):
        guard = " ".join(str(self.doc["jobs"]["review"].get("if") or "").split())
        self.assertIn("github.event.pull_request.draft == false", guard)
        self.assertIn('contains(fromJSON(\'["OWNER","MEMBER","COLLABORATOR"]\')', guard)
        self.assertIn('--disallowedTools "Bash,Edit,Write,MultiEdit,NotebookEdit,WebFetch,WebSearch"',
                      self.text)


class DelegatedMergeWorkflow(unittest.TestCase):
    """work/ci-budget R-5: the merge script wakes on the two workflows the policy requires.

    `agent-evals` left `merge.require-checks` on 2026-09-06 (15424e0) but stayed in this list, so
    every one of its runs woke the merge script for a minute to print `waiting`.
    """

    PATH = os.path.join(ROOT, ".github", "workflows", "delegated-merge.yml")

    def test_wakes_on_gate_and_review_only(self):
        import yaml

        with open(self.PATH, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        triggers = doc[True] if True in doc else doc["on"]
        self.assertEqual(triggers["workflow_run"]["workflows"], ["sdlc-gate", "pr-review"])

    def test_the_wake_list_matches_the_policy(self):
        # The two lists are the same decision written twice; a later edit to one alone is the
        # failure this catches (an extra name delays a merge, a missing one never wakes it).
        import delegation

        policy = delegation.load()
        import yaml

        with open(self.PATH, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        triggers = doc[True] if True in doc else doc["on"]
        self.assertEqual(sorted(triggers["workflow_run"]["workflows"]),
                         sorted(policy.merge.get("require_checks") or []))
