import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(HERE, "check_artifact_chain.py")
REAL_CONFIG = os.path.join(ROOT, ".sdlc", "config.env")
REAL_APPROVERS = os.path.join(ROOT, ".sdlc", "approvers.yaml")
TEMPLATES = os.path.join(ROOT, "docs", "sdlc", "templates")
EXAMPLE = os.path.join(ROOT, "work", "_example")

sys.path.insert(0, HERE)
from check_artifact_chain import front_matter_text  # noqa: E402


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _commit(root, message="init"):
    _git(root, "add", "-A")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", message)


def _artifact(approved_by, status="approved"):
    return f"---\nstatus: {status}\napproved-by: {approved_by}\n---\n# artifact\n"


def _plan(approved_by, files="- src/**\n", status="approved"):
    return (
        f"---\nstatus: {status}\napproved-by: {approved_by}\n---\n"
        f"# plan\n\n## Files that change\n{files}\n## Release-gated\n(none)\n"
    )


def _default_log(approved_by="luissiviero"):
    return (
        f"- 2026-01-01T00:00:00Z | intent.md | in-review -> approved | {approved_by} | abc1234 |\n"
        f"- 2026-01-01T00:00:00Z | spec.md | in-review -> approved | {approved_by} | abc1234 |\n"
        f"- 2026-01-01T00:00:00Z | plan.md | in-review -> approved | {approved_by} | abc1234 |\n"
    )


def _make_repo(root, slug="demo", approved_by="luissiviero", plan_files="- src/**\n",
               log_content=None, include_log=True, branch="main"):
    """Build a minimal git repo: real .sdlc/config.env + approvers.yaml, .sdlc/active,
    work/<slug>/{intent,spec,plan}.md approved by `approved_by` (plan lists `plan_files`
    under '## Files that change'), and (unless include_log is False) a matching log.md.
    Commits everything on `branch`. Returns work/<slug>'s absolute path."""
    _git(root, "init", "-q")
    _git(root, "checkout", "-q", "-b", branch)
    os.makedirs(os.path.join(root, ".sdlc"), exist_ok=True)
    shutil.copy(REAL_CONFIG, os.path.join(root, ".sdlc", "config.env"))
    shutil.copy(REAL_APPROVERS, os.path.join(root, ".sdlc", "approvers.yaml"))
    _write(os.path.join(root, ".sdlc", "active"), slug + "\n")

    wd = os.path.join(root, "work", slug)
    _write(os.path.join(wd, "intent.md"), _artifact(approved_by))
    _write(os.path.join(wd, "spec.md"), _artifact(approved_by))
    _write(os.path.join(wd, "plan.md"), _plan(approved_by, files=plan_files))

    if include_log:
        if log_content is None:
            log_content = _default_log(approved_by)
        _write(os.path.join(wd, "log.md"), log_content)

    _commit(root)
    return wd


def _run(root, *args):
    return subprocess.run(
        ["python3", SCRIPT, *args],
        cwd=root, capture_output=True, text=True,
    )


def _last_line(text):
    lines = [l for l in text.splitlines() if l.strip()]
    return lines[-1] if lines else ""


class HappyPath(unittest.TestCase):
    def test_approved_by_luissiviero_with_matching_log_passes(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(_last_line(result.stdout), "CHAIN: PASS")


class UnknownApprover(unittest.TestCase):
    def test_bot_handle_fails_naming_agent_identities(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root, approved_by="claude[bot]")
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            self.assertIn("agent identities", result.stdout)

    def test_non_role_handle_fails_naming_the_role(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root, approved_by="someone-else")
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            # intent.md/spec.md require product-owner, plan.md requires tech-lead
            self.assertIn("is not a product-owner", result.stdout)
            self.assertIn("is not a tech-lead", result.stdout)


class LogEntryRequired(unittest.TestCase):
    def test_missing_entry_for_one_artifact_fails_with_renderable_line(self):
        with tempfile.TemporaryDirectory() as root:
            log_content = (
                "- 2026-01-01T00:00:00Z | intent.md | in-review -> approved | luissiviero | abc1234 |\n"
                "- 2026-01-01T00:00:00Z | plan.md | in-review -> approved | luissiviero | abc1234 |\n"
            )
            _make_repo(root, log_content=log_content)
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            self.assertIn("| spec.md | in-review -> approved | luissiviero |", result.stdout)

    def test_actor_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as root:
            # approved-by is a valid approver, but the log records a different actor
            _make_repo(root, log_content=_default_log(approved_by="bob"))
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            self.assertIn("no entry recording", result.stdout)

    def test_missing_log_file_fails(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root, include_log=False)
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            self.assertIn("work/demo/log.md is missing", result.stdout)


class MalformedLogLine(unittest.TestCase):
    def test_malformed_line_becomes_a_note_not_a_failure(self):
        with tempfile.TemporaryDirectory() as root:
            log_content = _default_log() + "- this line is not well formed\n"
            _make_repo(root, log_content=log_content)
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(_last_line(result.stdout), "CHAIN: PASS")
            self.assertIn("note:", result.stdout)
            self.assertIn("malformed log line", result.stdout)


class NoApproversFlag(unittest.TestCase):
    def test_no_approvers_skips_approver_and_ledger_checks(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root, approved_by="claude[bot]", include_log=False)
            result = _run(root, "--slug", "demo", "--base", "HEAD", "--no-approvers")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(_last_line(result.stdout), "CHAIN: PASS")


class FilesSectionRegression(unittest.TestCase):
    """Existing behaviour: a changed file outside plan.md's '## Files that change'
    still fails the chain check."""

    def test_file_outside_plan_files_fails_against_base_branch(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)  # first commit on 'main', fully approved and logged
            _git(root, "checkout", "-q", "-b", "work/demo")
            _write(os.path.join(root, "other", "x.txt"), "hello\n")
            _commit(root, "add file outside plan")
            result = _run(root, "--slug", "demo", "--base", "main")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            self.assertIn(
                "other/x.txt changed but is not listed under '## Files that change'", result.stdout
            )


class InProgressChain(unittest.TestCase):
    """A PR whose diff touches only work/ is checked as far as the chain exists, so a work item
    can be opened and approved one stage per PR. Anything else in the diff needs the whole chain."""

    DRAFT_LOG = "- 2026-01-01T00:00:00Z | intent.md | (none) -> draft | claude[bot] | abc1234 | drafted\n"

    def _start_item(self, root, slug="new", intent=None, log=DRAFT_LOG):
        _make_repo(root)  # 'main' holds the fully approved 'demo' item; the new item lands on a branch
        _git(root, "checkout", "-q", "-b", f"work/{slug}")
        wd = os.path.join(root, "work", slug)
        _write(os.path.join(wd, "intent.md"), intent if intent is not None else _artifact("", status="draft"))
        if log is not None:
            _write(os.path.join(wd, "log.md"), log)
        return wd

    def test_intent_only_draft_passes(self):
        with tempfile.TemporaryDirectory() as root:
            self._start_item(root)
            _commit(root, "open the work item")
            result = _run(root, "--slug", "new", "--base", "main")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(_last_line(result.stdout), "CHAIN: PASS")
            self.assertIn("mode: in-progress", result.stdout)

    def test_spec_started_before_intent_is_approved_fails(self):
        with tempfile.TemporaryDirectory() as root:
            wd = self._start_item(root)
            _write(os.path.join(wd, "spec.md"), _artifact("", status="draft"))
            _commit(root, "spec too early")
            result = _run(root, "--slug", "new", "--base", "main")
            self.assertEqual(result.returncode, 1)
            self.assertIn("one stage at a time", result.stdout)
            self.assertIn("work/new/intent.md is 'draft'", result.stdout)

    def test_status_outside_the_enum_fails(self):
        with tempfile.TemporaryDirectory() as root:
            self._start_item(root, intent=_artifact("", status="open"))
            _commit(root, "bad status word")
            result = _run(root, "--slug", "new", "--base", "main")
            self.assertEqual(result.returncode, 1)
            self.assertIn("must be one of draft, in-review, approved, delegated, superseded", result.stdout)

    def test_approved_by_on_a_draft_fails(self):
        with tempfile.TemporaryDirectory() as root:
            self._start_item(root, intent=_artifact("luissiviero", status="draft"))
            _commit(root, "half-approved")
            result = _run(root, "--slug", "new", "--base", "main")
            self.assertEqual(result.returncode, 1)
            self.assertIn("approve.py sets both together", result.stdout)

    def test_approved_intent_still_needs_a_valid_approver(self):
        with tempfile.TemporaryDirectory() as root:
            log = "- 2026-01-01T00:00:00Z | intent.md | in-review -> approved | claude[bot] | abc1234 |\n"
            self._start_item(root, intent=_artifact("claude[bot]"), log=log)
            _commit(root, "bot approval")
            result = _run(root, "--slug", "new", "--base", "main")
            self.assertEqual(result.returncode, 1)
            self.assertIn("approved-by 'claude[bot]' is not valid", result.stdout)

    def test_missing_log_fails(self):
        with tempfile.TemporaryDirectory() as root:
            self._start_item(root, log=None)
            _commit(root, "no ledger")
            result = _run(root, "--slug", "new", "--base", "main")
            self.assertEqual(result.returncode, 1)
            self.assertIn("work/new/log.md is missing", result.stdout)

    def test_another_items_artifacts_in_the_diff_is_not_in_progress_for_this_slug(self):
        with tempfile.TemporaryDirectory() as root:
            self._start_item(root)
            _write(os.path.join(root, "work", "other", "intent.md"), _artifact("", status="draft"))
            _commit(root, "two items in one PR, labelled with one")
            result = _run(root, "--slug", "new", "--base", "main")
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("mode: in-progress", result.stdout)
            self.assertIn("work/new/spec.md is missing", result.stdout)

    def test_superseding_an_approved_plan_keeps_its_approved_by_and_passes(self):
        """Retiring an item: plan.md goes approved -> superseded, its approved-by stays as history."""
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)  # 'demo' fully approved on main
            _git(root, "checkout", "-q", "-b", "work/demo")
            _write(os.path.join(wd, "plan.md"), _plan("luissiviero", status="superseded"))
            with open(os.path.join(wd, "log.md"), "a", encoding="utf-8") as f:
                f.write("- 2026-01-02T00:00:00Z | plan.md | approved -> superseded | luissiviero | abc1234 | retired\n")
            _commit(root, "retire the item")
            result = _run(root, "--slug", "demo", "--base", "main")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("mode: in-progress", result.stdout)

    def test_fully_superseded_chain_passes(self):
        """Retiring a whole item: all three artifacts go approved -> superseded with their approved-by
        kept and a ledger line each. The stage-order rule accepts a superseded predecessor, or an item
        could be opened and approved but never retired (work/batch-b-followups R-3; PR #38)."""
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)  # 'demo' fully approved on main
            _git(root, "checkout", "-q", "-b", "work/demo")
            for name in ("intent.md", "spec.md", "plan.md"):
                body = _plan("luissiviero", status="superseded") if name == "plan.md" \
                    else _artifact("luissiviero", status="superseded")
                _write(os.path.join(wd, name), body)
            with open(os.path.join(wd, "log.md"), "a", encoding="utf-8") as f:
                for name in ("intent.md", "spec.md", "plan.md"):
                    f.write("- 2026-01-02T00:00:00Z | %s | approved -> superseded | luissiviero | abc1234 | retired\n" % name)
            _commit(root, "retire the whole item")
            result = _run(root, "--slug", "demo", "--base", "main")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("mode: in-progress", result.stdout)
            self.assertEqual(_last_line(result.stdout), "CHAIN: PASS")

    def test_superseded_with_an_invalid_approver_fails(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)
            _git(root, "checkout", "-q", "-b", "work/demo")
            _write(os.path.join(wd, "plan.md"), _plan("claude[bot]", status="superseded"))
            with open(os.path.join(wd, "log.md"), "a", encoding="utf-8") as f:
                f.write("- 2026-01-02T00:00:00Z | plan.md | approved -> superseded | luissiviero | abc1234 |\n")
            _commit(root, "retire with a bot approver")
            result = _run(root, "--slug", "demo", "--base", "main")
            self.assertEqual(result.returncode, 1)
            self.assertIn("approved-by 'claude[bot]' is not valid", result.stdout)

    def test_superseded_without_a_ledger_line_by_a_valid_approver_fails(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)
            _git(root, "checkout", "-q", "-b", "work/demo")
            _write(os.path.join(wd, "plan.md"), _plan("luissiviero", status="superseded"))
            with open(os.path.join(wd, "log.md"), "a", encoding="utf-8") as f:
                f.write("- 2026-01-02T00:00:00Z | plan.md | approved -> superseded | claude[bot] | abc1234 |\n")
            _commit(root, "retired by a bot")
            result = _run(root, "--slug", "demo", "--base", "main")
            self.assertEqual(result.returncode, 1)
            self.assertIn("no entry recording plan.md superseded by a valid approver", result.stdout)
            self.assertIn("approved -> superseded | luissiviero", result.stdout)

    def test_activating_the_item_in_the_same_diff_stays_in_progress(self):
        with tempfile.TemporaryDirectory() as root:
            self._start_item(root)
            _write(os.path.join(root, ".sdlc", "active"), "new\n")
            _commit(root, "open and activate")
            result = _run(root, "--slug", "new", "--base", "main")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("mode: in-progress", result.stdout)

    def test_pointing_active_at_another_item_is_strict(self):
        with tempfile.TemporaryDirectory() as root:
            self._start_item(root)
            _write(os.path.join(root, ".sdlc", "active"), "somebody-else\n")
            _commit(root, "active flipped elsewhere")
            result = _run(root, "--slug", "new", "--base", "main")
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("mode: in-progress", result.stdout)

    def test_code_in_the_diff_needs_the_whole_chain(self):
        with tempfile.TemporaryDirectory() as root:
            self._start_item(root)
            _write(os.path.join(root, "scripts", "x.py"), "print('hi')\n")
            _commit(root, "code with a draft chain")
            result = _run(root, "--slug", "new", "--base", "main")
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("mode: in-progress", result.stdout)
            self.assertIn("work/new/spec.md is missing", result.stdout)
            self.assertIn("work/new/intent.md status is 'draft', must be 'approved'", result.stdout)


class TemplateFrontMatter(unittest.TestCase):
    """work/front-matter spec R-1 and R-2: the one Python parser reads a value the way YAML does,
    so a template copied verbatim into work/<slug>/ passes the chain check."""

    def test_inline_comment_is_stripped(self):
        fm = front_matter_text("---\nstatus: draft            # draft | in-review | approved\n---\n")
        self.assertEqual(fm["status"], "draft")
        fm = front_matter_text("---\nkind: feature\t# feature | fix\napproved-by:   # a human\n---\n")
        self.assertEqual(fm["kind"], "feature")
        self.assertEqual(fm["approved-by"], "")

    def test_quoted_status_parses(self):
        self.assertEqual(front_matter_text('---\nstatus: "in-review"\n---\n')["status"], "in-review")
        self.assertEqual(front_matter_text("---\nstatus: 'approved'\n---\n")["status"], "approved")
        # Only a matching pair is a quote; a lone apostrophe is part of the value.
        self.assertEqual(front_matter_text("---\ntitle: the owner's plan\n---\n")["title"], "the owner's plan")

    def test_comment_line_is_not_a_key(self):
        fm = front_matter_text(
            "---\n# status: draft | in-review | approved | superseded\nstatus: in-review\n"
            "  # approved-by: set only by a human\napproved-by:\n---\n"
        )
        self.assertEqual(fm["status"], "in-review")
        self.assertEqual(fm["approved-by"], "")
        self.assertNotIn("# status", fm)
        self.assertNotIn("# approved-by", fm)
        self.assertEqual(len(fm), 2)

    def test_crlf_input_parses(self):
        fm = front_matter_text("---\r\nstatus: approved   # note\r\napproved-by: luissiviero\r\n---\r\n# body\r\n")
        self.assertEqual(fm["status"], "approved")
        self.assertEqual(fm["approved-by"], "luissiviero")

    def test_url_anchor_is_kept(self):
        fm = front_matter_text("---\nresource: https://example.com/issues/12#comment-3\ntitle: Fix #12 crash\n---\n")
        self.assertEqual(fm["resource"], "https://example.com/issues/12#comment-3")
        # YAML semantics, accepted in spec C2: whitespace then '#' starts a comment; quote such a value.
        self.assertEqual(fm["title"], "Fix")
        self.assertEqual(front_matter_text('---\ntitle: "Fix #12 crash"\n---\n')["title"], "Fix #12 crash")

    def test_verbatim_template_copy_passes_in_progress(self):
        """The real docs/sdlc/templates/intent.md, copied unchanged into a new work item."""
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _git(root, "checkout", "-q", "-b", "work/new")
            wd = os.path.join(root, "work", "new")
            os.makedirs(wd)
            shutil.copy(os.path.join(TEMPLATES, "intent.md"), os.path.join(wd, "intent.md"))
            _write(os.path.join(wd, "log.md"), InProgressChain.DRAFT_LOG)
            _commit(root, "open the work item from the template")
            result = _run(root, "--slug", "new", "--base", "main")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(_last_line(result.stdout), "CHAIN: PASS")
            self.assertIn("mode: in-progress", result.stdout)


def _front_matter_keys(path):
    """Front-matter keys in file order; comment lines are guidance, not keys."""
    keys = []
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.lstrip().startswith("#") or ":" not in line:
            continue
        keys.append(line.split(":", 1)[0].strip())
    return keys


def _headings(path):
    with open(path, encoding="utf-8") as f:
        return [l.rstrip() for l in f.read().splitlines() if l.startswith("## ") or l.startswith("### ")]


class ExampleMatchesTemplates(unittest.TestCase):
    """work/front-matter spec R-6: the always-green example has the templates' keys and headings,
    in the templates' order, so it teaches the shape the parsers and skills expect."""

    ARTIFACTS = ("intent.md", "spec.md", "plan.md")

    def test_front_matter_keys_match(self):
        for name in self.ARTIFACTS:
            with self.subTest(artifact=name):
                self.assertEqual(
                    _front_matter_keys(os.path.join(EXAMPLE, name)),
                    _front_matter_keys(os.path.join(TEMPLATES, name)),
                )

    def test_headings_match(self):
        for name in self.ARTIFACTS:
            with self.subTest(artifact=name):
                self.assertEqual(
                    _headings(os.path.join(EXAMPLE, name)),
                    _headings(os.path.join(TEMPLATES, name)),
                )


class ApprovalAuthor(unittest.TestCase):
    """The approval is attributed to the diff that set `status: approved`, never to a later commit that
    merely mentions the phrase (work/agent-evals R-5; the PR #25 misattribution)."""

    AGENT_NAME, AGENT_EMAIL = "claude", "noreply@anthropic.com"

    def _commit_as(self, root, name, email, message):
        _git(root, "add", "-A")
        _git(root, "-c", f"user.email={email}", "-c", f"user.name={name}", "commit", "-q", "-m", message)

    def test_prose_mention_after_approval_does_not_reattribute(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)  # approved, committed by a human-shaped author
            with open(os.path.join(wd, "intent.md"), "a", encoding="utf-8") as f:
                f.write("\nDeviation: the owner set status: approved from the web editor.\n")
            self._commit_as(root, self.AGENT_NAME, self.AGENT_EMAIL, "agent deviation note")
            result = _run(root, "--base", "HEAD")
            self.assertEqual(_last_line(result.stdout), "CHAIN: PASS", result.stdout)
            self.assertNotIn("authored by an agent identity", result.stdout)

    def test_agent_commit_that_sets_approved_fails(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)
            _write(os.path.join(wd, "intent.md"), "---\nstatus: in-review\napproved-by:\n---\n# artifact\n")
            _commit(root, "back to review")
            _write(os.path.join(wd, "intent.md"), _artifact("luissiviero"))
            self._commit_as(root, self.AGENT_NAME, self.AGENT_EMAIL, "agent flips it to approved")
            result = _run(root, "--base", "HEAD")
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL", result.stdout)
            self.assertIn("authored by an agent identity (claude <noreply@anthropic.com>)", result.stdout)


if __name__ == "__main__":
    unittest.main()
