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

    # --- work/approve-by-dispatch R-5: the trailer route -----------------------------------
    TRAILERS = "\n\nApproved-Run: {run}\nApproved-Actor: {actor}\n"

    def _reapprove_with_trailers(self, root, wd, handle, actor, run="12345"):
        """Set status: approved in a commit carrying the dispatch trailers."""
        _write(os.path.join(wd, "intent.md"), "---\nstatus: in-review\napproved-by:\n---\n# artifact\n")
        _commit(root, "back to review")
        _write(os.path.join(wd, "intent.md"), _artifact(handle))
        _git(root, "add", "-A")
        _git(root, "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
             "-c", "user.name=github-actions[bot]", "commit", "-q",
             "-m", "[demo] Approve intent.md" + self.TRAILERS.format(run=run, actor=actor))

    def test_trailer_whose_actor_matches_approved_by_passes(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)
            # The committer is the bot, so without the trailer this would fail the author rule.
            self._reapprove_with_trailers(root, wd, "luissiviero", "luissiviero")
            result = _run(root, "--base", "HEAD")
            self.assertEqual(_last_line(result.stdout), "CHAIN: PASS", result.stdout)
            self.assertNotIn("authored by an agent identity", result.stdout)

    def test_trailer_naming_a_different_handle_than_approved_by_fails(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)
            self._reapprove_with_trailers(root, wd, "luissiviero", "someone-else")
            result = _run(root, "--base", "HEAD")
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL", result.stdout)
            self.assertIn("Approved-Actor: someone-else", result.stdout)

    def test_no_token_accepts_the_trailer_and_says_so(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)
            self._reapprove_with_trailers(root, wd, "luissiviero", "luissiviero")
            env = {k: v for k, v in os.environ.items()
                   if k not in ("GH_TOKEN", "GITHUB_TOKEN")}
            result = subprocess.run(
                [sys.executable, os.path.join(HERE, "check_artifact_chain.py"), "--base", "HEAD"],
                cwd=root, capture_output=True, text=True, env=env)
            self.assertEqual(_last_line(result.stdout), "CHAIN: PASS", result.stdout)
            self.assertIn("accepted on the author rule alone", result.stdout)

    def test_an_agent_authored_commit_with_no_trailer_still_fails(self):
        """The trailer route is additive: it must not soften the rule for everything else."""
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)
            _write(os.path.join(wd, "intent.md"), "---\nstatus: in-review\napproved-by:\n---\n# artifact\n")
            _commit(root, "back to review")
            _write(os.path.join(wd, "intent.md"), _artifact("luissiviero"))
            self._commit_as(root, self.AGENT_NAME, self.AGENT_EMAIL, "no trailers here")
            result = _run(root, "--base", "HEAD")
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL", result.stdout)
            self.assertIn("authored by an agent identity", result.stdout)


class DispatchAttestation(unittest.TestCase):
    """R-6: the trailer is checked against the run record, not believed."""

    def setUp(self):
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import check_artifact_chain as cac

        self.cac = cac

    def _run_json(self, **overrides):
        run = {"event": "workflow_dispatch", "path": ".github/workflows/approve.yml",
               "conclusion": "success", "actor": {"login": "luissiviero"}}
        run.update(overrides)
        return run

    def _verify(self, run, actor="luissiviero", token="t"):
        """verify_dispatch_run with the API call stubbed out at the subprocess boundary."""
        import json as _json
        import subprocess as _sp

        real = self.cac.subprocess.run
        payload = _json.dumps(run)

        def fake(args, **kw):
            if args[:2] == ["gh", "api"]:
                return _sp.CompletedProcess(args, 0, payload, "")
            return real(args, **kw)

        self.cac.subprocess.run = fake
        env_keys = {"GH_TOKEN": token, "GITHUB_REPOSITORY": "luissiviero/lifecycle-axis-"}
        saved = {k: os.environ.get(k) for k in env_keys}
        try:
            os.environ.update({k: v for k, v in env_keys.items() if v is not None})
            if token is None:
                os.environ.pop("GH_TOKEN", None)
                os.environ.pop("GITHUB_TOKEN", None)
            return self.cac.verify_dispatch_run("12345", actor)
        finally:
            self.cac.subprocess.run = real
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_matching_run_verifies(self):
        ok, detail = self._verify(self._run_json())
        self.assertIs(ok, True, detail)

    def test_a_run_of_another_workflow_fails(self):
        ok, detail = self._verify(self._run_json(path=".github/workflows/deploy.yml"))
        self.assertIs(ok, False)
        self.assertIn("path", detail)

    def test_a_run_of_another_event_fails(self):
        ok, detail = self._verify(self._run_json(event="push"))
        self.assertIs(ok, False)
        self.assertIn("event", detail)

    def test_a_failed_run_fails(self):
        ok, detail = self._verify(self._run_json(conclusion="failure"))
        self.assertIs(ok, False)
        self.assertIn("conclusion", detail)

    def test_another_actor_fails(self):
        ok, detail = self._verify(self._run_json(actor={"login": "someone-else"}))
        self.assertIs(ok, False)
        self.assertIn("actor", detail)

    def test_no_token_returns_none_with_a_note(self):
        saved = {k: os.environ.pop(k, None) for k in ("GH_TOKEN", "GITHUB_TOKEN")}
        try:
            ok, detail = self.cac.verify_dispatch_run("12345", "luissiviero")
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v
        self.assertIsNone(ok)
        self.assertIn("accepted on the author rule alone", detail)

    def test_trailers_are_read_from_the_commit_body(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _write(os.path.join(root, "note.txt"), "x\n")
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m",
                 "subject\n\nApproved-Run: 777\nApproved-Actor: luissiviero\n")
            sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                                 capture_output=True, text=True).stdout.strip()
            saved = self.cac.ROOT
            self.cac.ROOT = root
            try:
                self.assertEqual(self.cac.dispatch_attestation(sha), ("777", "luissiviero"))
            finally:
                self.cac.ROOT = saved

    def test_a_commit_without_trailers_has_no_attestation(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                                 capture_output=True, text=True).stdout.strip()
            saved = self.cac.ROOT
            self.cac.ROOT = root
            try:
                self.assertIsNone(self.cac.dispatch_attestation(sha))
            finally:
                self.cac.ROOT = saved


# --- work/delegated-mode R-4, R-5, R-6 ------------------------------------------------------
# Written from spec.md's acceptance column before scripts/delegation.py and the chain-check
# changes exist; every test below is expected to fail today and pass once they ship. See
# NOTES.md for the assumptions this file bakes in (from_status on a "-> delegated" line is what
# decides fresh-signature vs. re-sign; exact FAIL wording beyond what the spec pins down is
# asserted loosely, by substring, not verbatim).

HUMAN_NAME = "luissiviero"
HUMAN_EMAIL = "69210737+luissiviero@users.noreply.github.com"
AGENT_NAME = "Claude"
AGENT_EMAIL = "noreply@anthropic.com"

# Exactly spec.md design D1.
DELEGATION_POLICY = """\
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

REVISION_TWO_REVIEWERS_REVISE = """\
---
type: sdlc/revision
id: demo-revision-1
title: Revise the spec
artifact: spec.md
trigger: blocking error found in review; evidence: scripts/run_tests.py:1 fake failure
timestamp: 2026-09-05T02:00:00Z
---
## Proposal
Change X because Y.

## Reviewer: security (gpt-5)
Findings noted.
verdict: revise

## Reviewer: architecture (gemini)
Findings noted.
verdict: revise
"""

REVISION_ONE_REVIEWER = """\
---
type: sdlc/revision
id: demo-revision-1
title: Revise the spec
artifact: spec.md
trigger: blocking error found in review
timestamp: 2026-09-05T02:00:00Z
---
## Proposal
Change X because Y.

## Reviewer: security (gpt-5)
Findings noted.
verdict: revise
"""

REVISION_ONE_KEEP = """\
---
type: sdlc/revision
id: demo-revision-1
title: Revise the spec
artifact: spec.md
trigger: blocking error found in review
timestamp: 2026-09-05T02:00:00Z
---
## Proposal
Change X because Y.

## Reviewer: security (gpt-5)
Findings noted.
verdict: revise

## Reviewer: architecture (gemini)
Disagrees; the plan is fine as is.
verdict: keep
"""


def _write_delegation_policy(root, content=DELEGATION_POLICY):
    _write(os.path.join(root, ".sdlc", "delegation.yaml"), content)


def _commit_as(root, name, email, message):
    _git(root, "add", "-A")
    _git(root, "-c", f"user.email={email}", "-c", f"user.name={name}", "commit", "-q", "-m", message)


def _grant_intent(approved_by=HUMAN_NAME, risk_class="low", mode="delegated",
                   delegated_by=HUMAN_NAME, delegated_on="2026-09-05"):
    """intent.md front matter carrying a delegated-mode grant (D2), still status: approved
    with the same approved-by luissiviero already recorded and logged by _make_repo -- only
    the grant fields are new, so the pre-existing 'status: approved' commit-authorship check
    keeps pointing at _make_repo's original (non-agent) commit."""
    return (
        "---\n"
        "status: approved\n"
        f"approved-by: {approved_by}\n"
        f"risk-class: {risk_class}\n"
        f"mode: {mode}\n"
        f"delegated-by: {delegated_by}\n"
        f"delegated-on: {delegated_on}\n"
        "---\n# artifact\n"
    )


def _apply_grant(root, wd, risk_class="low", mode="delegated", author=(HUMAN_NAME, HUMAN_EMAIL)):
    """Write the grant onto work/<slug>/intent.md and commit it as `author` (name, email),
    with a ledger line recording it, as spec.md D2 describes."""
    _write(os.path.join(wd, "intent.md"), _grant_intent(risk_class=risk_class, mode=mode))
    with open(os.path.join(wd, "log.md"), "a", encoding="utf-8") as f:
        f.write(f"- 2026-09-05T00:00:00Z | intent.md | approved -> approved | {HUMAN_NAME} | abc1234 | mode: delegated\n")
    _commit_as(root, author[0], author[1], "grant delegated mode")


def _sign_delegated(root, wd, artifact="spec.md", handle="claude", from_status="in-review", note="",
                    keep_approval=False):
    """Flip `artifact` to status: delegated, approved-by `handle`, committed by the agent
    identity, with a matching '-> delegated' ledger line. A fresh signature is one on an artifact no
    human ever approved, so the base fixture's `-> approved` ledger line for it is dropped unless
    `keep_approval` (the demote-then-sign case: PR #43 security pass, finding 1)."""
    content = _plan(handle, status="delegated") if artifact == "plan.md" else _artifact(handle, status="delegated")
    _write(os.path.join(wd, artifact), content)
    if not keep_approval and from_status not in ("approved", "delegated"):
        log_path = os.path.join(wd, "log.md")
        with open(log_path, encoding="utf-8") as f:
            kept = [l for l in f if f"| {artifact} | in-review -> approved |" not in l]
        with open(log_path, "w", encoding="utf-8") as f:
            f.writelines(kept)
    line = f"- 2026-09-05T01:00:00Z | {artifact} | {from_status} -> delegated | {handle} | abc1234"
    if note:
        line += f" | {note}"
    with open(os.path.join(wd, "log.md"), "a", encoding="utf-8") as f:
        f.write(line + "\n")
    _commit_as(root, AGENT_NAME, AGENT_EMAIL, f"sign {artifact} as {handle}")


def _base_delegated_repo(root):
    """demo, fully approved by _make_repo, then granted (human) and spec.md freshly signed
    delegated by claude (in-review -> delegated, no revision record needed): the R-4 pass case."""
    wd = _make_repo(root)
    _write_delegation_policy(root)
    _apply_grant(root, wd)
    _sign_delegated(root, wd, artifact="spec.md", handle="claude", from_status="in-review")
    return wd


class DelegatedChain(unittest.TestCase):
    """work/delegated-mode R-4 and R-5: the chain check accepts a delegated artifact only
    when the policy, the grant and the ledger all agree, and requires a revision record for a
    re-signature of an already-approved-or-delegated artifact."""

    # --- R-4: the grant ---------------------------------------------------------------------

    def test_valid_grant_and_fresh_signature_passes(self):
        with tempfile.TemporaryDirectory() as root:
            _base_delegated_repo(root)
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(_last_line(result.stdout), "CHAIN: PASS")

    def test_demoted_then_signed_artifact_needs_a_revision_record(self):
        # PR #43 security pass, finding 1: an approved spec demoted to in-review (the accepted
        # demotion residual) and then signed fresh is a re-decision of a human approval; the ledger
        # still holds the approval, so the signature needs a revision record.
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)
            _write_delegation_policy(root)
            _apply_grant(root, wd)
            _sign_delegated(root, wd, artifact="spec.md", from_status="in-review", keep_approval=True)
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("revision", result.stdout)

    def test_deviation_line_after_first_signature_needs_no_record(self):
        # Advisory review on PR #43: a `delegated -> delegated | deviation:` line after the first
        # signature is a deviation, not a re-decision; check_revisions must not count it, and the
        # signature before it stays a fresh one.
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)
            _write_delegation_policy(root)
            _apply_grant(root, wd)
            _sign_delegated(root, wd, artifact="spec.md", from_status="in-review")
            with open(os.path.join(wd, "log.md"), "a", encoding="utf-8") as f:
                f.write("- 2026-09-05T02:00:00Z | spec.md | delegated -> delegated | claude | abc1234 | deviation: add src/x.py\n")
            _commit_as(root, AGENT_NAME, AGENT_EMAIL, "log a deviation")
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(_last_line(result.stdout), "CHAIN: PASS")

    def test_signer_not_in_agents_fails_naming_the_signer(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)
            _write_delegation_policy(root)
            _apply_grant(root, wd)
            _sign_delegated(root, wd, artifact="spec.md", handle="mallory", from_status="in-review")
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            self.assertIn("mallory", result.stdout)

    def test_intent_itself_delegated_fails(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)
            _write_delegation_policy(root)
            _apply_grant(root, wd)
            _write(os.path.join(wd, "intent.md"), _artifact("claude", status="delegated"))
            with open(os.path.join(wd, "log.md"), "a", encoding="utf-8") as f:
                f.write("- 2026-09-05T01:00:00Z | intent.md | approved -> delegated | claude | abc1234\n")
            _commit_as(root, AGENT_NAME, AGENT_EMAIL, "bad: intent itself delegated")
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            self.assertIn("intent.md", result.stdout)

    def test_no_delegated_ledger_line_fails(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)
            _write_delegation_policy(root)
            _apply_grant(root, wd)
            # spec.md's front matter says delegated, but no matching ledger line is appended.
            _write(os.path.join(wd, "spec.md"), _artifact("claude", status="delegated"))
            _commit_as(root, AGENT_NAME, AGENT_EMAIL, "sign spec.md with no ledger line")
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")

    def test_agent_authored_grant_commit_fails(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)
            _write_delegation_policy(root)
            _apply_grant(root, wd, author=(AGENT_NAME, AGENT_EMAIL))
            _sign_delegated(root, wd, artifact="spec.md", handle="claude", from_status="in-review")
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            self.assertIn("agent identity", result.stdout)

    def test_risk_class_outside_policy_fails(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)
            _write_delegation_policy(root)
            _apply_grant(root, wd, risk_class="medium")
            _sign_delegated(root, wd, artifact="spec.md", handle="claude", from_status="in-review")
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            self.assertIn("medium", result.stdout)

    def test_missing_policy_file_fails(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _make_repo(root)
            # No _write_delegation_policy(root) call: .sdlc/delegation.yaml is absent.
            _apply_grant(root, wd)
            _sign_delegated(root, wd, artifact="spec.md", handle="claude", from_status="in-review")
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            self.assertIn("delegation", result.stdout)

    def test_artifact_only_diff_with_delegated_spec_and_no_grant_fails(self):
        """R-4: the grant is checked in in-progress mode too, not only strict mode."""
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)  # unrelated 'demo' item, fully approved, on main
            _write_delegation_policy(root)
            # Committed on main *before* the branch, so the policy file itself is not part of the
            # work/new branch's diff -- otherwise it would fail own_artifact() and force strict mode.
            _commit(root, "add delegation policy")
            _git(root, "checkout", "-q", "-b", "work/new")
            wd = os.path.join(root, "work", "new")
            _write(os.path.join(wd, "intent.md"), _artifact("", status="draft"))  # no grant at all
            _write(os.path.join(wd, "spec.md"), _artifact("claude", status="delegated"))
            log = (
                "- 2026-09-05T00:00:00Z | intent.md | (none) -> draft | claude[bot] | abc1234 | drafted\n"
                "- 2026-09-05T01:00:00Z | spec.md | draft -> delegated | claude | abc1234\n"
            )
            _write(os.path.join(wd, "log.md"), log)
            _commit(root, "spec delegated with no grant on a fresh item")
            result = _run(root, "--slug", "new", "--base", "main")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")
            self.assertIn("mode: in-progress", result.stdout)

    # --- R-5: the revision gate --------------------------------------------------------------

    def test_resign_with_unanimous_revision_record_passes(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _base_delegated_repo(root)
            _write(os.path.join(wd, "revisions", "1.md"), REVISION_TWO_REVIEWERS_REVISE)
            _write(os.path.join(wd, "spec.md"), _artifact("claude", status="delegated"))
            with open(os.path.join(wd, "log.md"), "a", encoding="utf-8") as f:
                f.write("- 2026-09-05T03:00:00Z | spec.md | delegated -> delegated | claude | abc1234 | revision 1: fixed X\n")
            _commit_as(root, AGENT_NAME, AGENT_EMAIL, "revise spec per unanimous review")
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(_last_line(result.stdout), "CHAIN: PASS")

    def test_resign_with_one_reviewer_section_fails(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _base_delegated_repo(root)
            _write(os.path.join(wd, "revisions", "1.md"), REVISION_ONE_REVIEWER)
            _write(os.path.join(wd, "spec.md"), _artifact("claude", status="delegated"))
            with open(os.path.join(wd, "log.md"), "a", encoding="utf-8") as f:
                f.write("- 2026-09-05T03:00:00Z | spec.md | delegated -> delegated | claude | abc1234 | revision 1: fixed X\n")
            _commit_as(root, AGENT_NAME, AGENT_EMAIL, "revise spec with only one reviewer")
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")

    def test_resign_with_a_keep_verdict_fails(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _base_delegated_repo(root)
            _write(os.path.join(wd, "revisions", "1.md"), REVISION_ONE_KEEP)
            _write(os.path.join(wd, "spec.md"), _artifact("claude", status="delegated"))
            with open(os.path.join(wd, "log.md"), "a", encoding="utf-8") as f:
                f.write("- 2026-09-05T03:00:00Z | spec.md | delegated -> delegated | claude | abc1234 | revision 1: fixed X\n")
            _commit_as(root, AGENT_NAME, AGENT_EMAIL, "revise spec with a keep verdict")
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")

    def test_resign_with_no_revision_record_fails(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _base_delegated_repo(root)
            # No work/demo/revisions/1.md written at all.
            _write(os.path.join(wd, "spec.md"), _artifact("claude", status="delegated"))
            with open(os.path.join(wd, "log.md"), "a", encoding="utf-8") as f:
                f.write("- 2026-09-05T03:00:00Z | spec.md | delegated -> delegated | claude | abc1234 | revision 1: fixed X\n")
            _commit_as(root, AGENT_NAME, AGENT_EMAIL, "revise spec with no record file")
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")

    # --- R-5: the deviation cap ---------------------------------------------------------------

    def test_deviation_count_over_the_cap_fails(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _base_delegated_repo(root)
            with open(os.path.join(wd, "log.md"), "a", encoding="utf-8") as f:
                for n in range(6):
                    f.write(f"- 2026-09-05T{10 + n:02d}:00:00Z | plan.md | approved -> approved | claude | abc1234 | deviation: change {n}\n")
            _commit(root, "six deviations, one over the cap of 5")
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(_last_line(result.stdout), "CHAIN: FAIL")

    def test_deviation_count_at_the_cap_passes(self):
        with tempfile.TemporaryDirectory() as root:
            wd = _base_delegated_repo(root)
            with open(os.path.join(wd, "log.md"), "a", encoding="utf-8") as f:
                for n in range(5):
                    f.write(f"- 2026-09-05T{10 + n:02d}:00:00Z | plan.md | approved -> approved | claude | abc1234 | deviation: change {n}\n")
            _commit(root, "five deviations, exactly the cap")
            result = _run(root, "--slug", "demo", "--base", "HEAD")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(_last_line(result.stdout), "CHAIN: PASS")


class ActiveSlugRequired(unittest.TestCase):
    """work/delegated-mode R-6: an empty or missing .sdlc/active with no --slug is one clear
    failure line, not a cascade of "work//<artifact> is missing" errors."""

    def test_empty_active_slug_is_one_clear_failure(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            _write(os.path.join(root, ".sdlc", "active"), "")
            _commit(root, "blank .sdlc/active")
            result = _run(root, "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            fail_lines = [l for l in result.stdout.splitlines() if l.startswith("  FAIL:")]
            self.assertEqual(len(fail_lines), 1, result.stdout)
            self.assertEqual(
                fail_lines[0],
                "  FAIL: no active work item (.sdlc/active is empty; pass --slug or set it)",
            )

    def test_missing_active_file_is_one_clear_failure(self):
        with tempfile.TemporaryDirectory() as root:
            _make_repo(root)
            os.remove(os.path.join(root, ".sdlc", "active"))
            _commit(root, "remove .sdlc/active")
            result = _run(root, "--base", "HEAD")
            self.assertEqual(result.returncode, 1)
            fail_lines = [l for l in result.stdout.splitlines() if l.startswith("  FAIL:")]
            self.assertEqual(len(fail_lines), 1, result.stdout)
            self.assertEqual(
                fail_lines[0],
                "  FAIL: no active work item (.sdlc/active is empty; pass --slug or set it)",
            )


if __name__ == "__main__":
    unittest.main()
