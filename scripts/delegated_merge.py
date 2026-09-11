#!/usr/bin/env python3
"""Merge a delegated pull request from CI, only when every printed condition holds.

Called by `.github/workflows/delegated-merge.yml` on a `workflow_run` completion, so it runs from
the default branch: this script and the three `.sdlc/` files it reads are always `main`'s copies,
never the head's (work/delegated-mode R-15, D6; knowledge/decisions/delegated-mode.md decision 6).
The same rule holds for the grant itself: `work/<slug>/intent.md` and the commit that wrote its
`mode: delegated` line are read from the pull request's BASE branch, never from the head under
judgement. It is the click, for delegated items only; `merge-click-is-the-gate.md` still describes
every supervised pull request.

Nothing here is discretionary. Eight conditions run in a fixed order, each printing one
`CONDITION <name>: <ok|refused|waiting> — <detail>` line; the run stops at the first non-`ok`
verdict and ends with `DELEGATED-MERGE: merged #<n> <sha>`, `... refused (<name>)`,
`... waiting (<name>)` or `... dry-run (<verdict>)`. Exit 0 on a merge or a wait, 1 on a refusal
-- except two refusals that are not errors and exit 0: `policy` (delegated merging is simply off)
and `stale` (the head moved under the merge call; the next check completion retries).

`--dry-run` calls no mutating endpoint and does not stop at the first refusal: it prints every
condition it can still evaluate, which is what makes it useful against a supervised item's pull
request. A condition whose input an earlier refusal made unavailable is skipped, never guessed.

Usage:
  delegated_merge.py [--dry-run] [--event FILE] [--policy FILE] [--root DIR] [--fixtures DIR]
    --event     the `workflow_run` event JSON; default $GITHUB_EVENT_PATH.
    --policy    the delegation policy; default <root>/.sdlc/delegation.yaml.
    --root      the checkout to read .sdlc/ from; default the git root (in CI: main).
    --fixtures  test only: serve every GET from <DIR>/<method>_<path>.json and record every
                mutating call into <DIR>/calls.jsonl instead of sending it. No network.

Every GitHub call goes through `gh_api(method, path, fields=None)`, which shells out to `gh api`
as `scripts/github_metrics.py` does; tests replace the module-level `API` hook (`--fixtures`
installs one). stdlib only, Python 3.8 syntax.
"""
import argparse
import base64
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import approvers  # noqa: E402  (path set up above)
import check_artifact_chain as chain  # noqa: E402  (front_matter_text and config())
import delegation  # noqa: E402  (the one policy parser)
import log_ledger  # noqa: E402  (the one ledger renderer, for the advance's two lines)
import next_item  # noqa: E402  (the queue rule, shared with the sdlc-run skill)

# This workflow's own check run, excluded from "every other check run must be green": it is in
# progress while it runs, so including it would make the condition unsatisfiable. GitHub names a
# check run after the JOB, not the workflow, and delegated-merge.yml's job is `merge` -- naming the
# workflow here excluded nothing and let this job's own in-progress run wait for itself
# (pull request 45 security pass, nit b).
SELF_CHECK_NAME = "merge"
# The reviewer identity pr-review.yml posts as (docs/sdlc/spikes/pr-review-identity.md).
REVIEW_BOT_LOGIN = "claude[bot]"
REVIEW_BOT_TYPE = "Bot"
# The workflow whose run *is* the review verdict, and the link its comment carries. Any account
# with a token can post a comment ending `Important: 0`; only the pr-review workflow can produce a
# run of this head sha, so the comment is believed only when it links that run
# (pull request 45 security pass, finding 3).
REVIEW_WORKFLOW_NAME = "pr-review"
REVIEW_RUN_LINK = "/actions/runs/%s"
# REVIEW.md's summary line, added for exactly this condition (work/delegated-mode R-13).
REVIEW_SUMMARY_RE = re.compile(r"^Important: (\d+) \| Nits: (\d+)$")
# `Work-Item: <slug>` in the pull request body, and the shape a slug must have. The slug is
# interpolated into `work/<slug>/intent.md` and into API paths, so a `.`-only segment or a leading
# dot -- `..`, `.git` -- would name a file outside the work item (pull request 45 security pass,
# finding 7).
WORK_ITEM_RE = re.compile(r"^Work-Item:\s*(\S+)$")
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*(\.[A-Za-z0-9_-]+)*$")
# The literal the `-G` pickaxe checks look for, here read out of a commit's patch.
GRANT_LINE_RE = re.compile(r"^\+mode:\s*delegated\s*$")
OK_CHECK_CONCLUSIONS = ("success", "skipped", "neutral")
# GitHub's own committer for web-editor and API commits: it signs with GitHub's key, and the
# author of a commit it makes is the authenticated account that asked for it.
WEB_FLOW_LOGIN = "web-flow"
# The identity approve_dispatch.py commits as. A dispatch-made grant is authored by the
# run's actor and committed by the bot, so route B checks the committer against this
# rather than against a product-owner role (work/approve-by-dispatch D2, R-7).
BOT_LOGIN = "github-actions[bot]"
# The paths this script locks whatever any file says: the control plane, the judging surfaces and
# the rules an agent's pull request must not be able to rewrite on its way in. See
# `check_locked_paths` -- the policy's `locked-paths` only ever adds to this floor.
ALWAYS_LOCKED = (
    ".github", ".claude", ".gemini", "docs/sdlc/rules", "docs/sdlc/templates",
    "CLAUDE.md", "GEMINI.md", "AGENTS.md", "REVIEW.md", ".sdlc",
    "scripts/checks", "scripts/verify.sh", "scripts/run_tests.py", "scripts/run_evals.sh",
)
# `gh api` reports the HTTP status in its stderr; 405/409 on the merge endpoint mean the sha moved.
HTTP_STATUS_RE = re.compile(r"HTTP (\d{3})")
STALE_STATUSES = (405, 409)
# `--head-sha` is interpolated into API paths; a sha is hex and nothing else.
HEAD_SHA_ARG_RE = re.compile(r"^[0-9a-f]{7,40}$")

OK = "ok"
REFUSED = "refused"
WAITING = "waiting"
# A fourth verdict, and the only non-`ok` one that is not a problem: the pull request belongs to a
# supervised item, so this workflow was never the thing that merges it. Every gate and review
# completion on such a pull request used to end this run red and billed; it now ends green, while a
# refusal about the pull request itself stays red beside it (work/ci-budget R-7).
NOT_DELEGATED = "not-delegated"

# Conclusions that say nothing about the head sha, handled in `_pr_runs` (work/ci-budget R-6).
SKIPPED = "skipped"
CANCELLED = "cancelled"

# Test hook: a callable (method, path, fields) -> parsed JSON, installed by --fixtures or by a
# test. `None` means "really call `gh`". Kept module-level so a test never patches subprocess.
API = None


class MergeError(RuntimeError):
    """A GitHub call failed. `.status` is the HTTP status when `gh` reported one."""

    def __init__(self, message, status=None):
        RuntimeError.__init__(self, message)
        self.status = status


# --- GitHub plumbing -------------------------------------------------------
def _parse_json_stream(text):
    """`gh api --paginate` prints one JSON document per page (github_metrics.py note): flatten
    array pages into one list, and concatenate object pages' list values key by key."""
    text = (text or "").strip()
    if not text:
        return None
    decoder = json.JSONDecoder()
    docs = []
    idx, end = 0, len(text)
    while idx < end:
        while idx < end and text[idx] in " \t\r\n":
            idx += 1
        if idx >= end:
            break
        obj, idx = decoder.raw_decode(text, idx)
        docs.append(obj)
    if not docs:
        return None
    if len(docs) == 1:
        return docs[0]
    if all(isinstance(d, list) for d in docs):
        flat = []
        for d in docs:
            flat.extend(d)
        return flat
    merged = {}
    for d in docs:
        if not isinstance(d, dict):
            continue
        for key, value in d.items():
            if isinstance(value, list):
                merged.setdefault(key, []).extend(value)
            else:
                merged.setdefault(key, value)
    return merged


def gh_api(method, path, fields=None):
    """The one entry point for every GitHub call: `gh api -X <method> <path> [-f k=v ...]`, with
    `--paginate` on GET (so no caller loops). Raises MergeError carrying `gh`'s stderr."""
    if API is not None:  # test hook (see module docstring)
        return API(method, path, fields)
    cmd = ["gh", "api", "-X", method.upper()]
    if method.upper() == "GET":
        cmd.append("--paginate")
    cmd.append(path)
    for key, value in sorted((fields or {}).items()):
        cmd.extend(["-f", "%s=%s" % (key, value)])
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except OSError as exc:
        raise MergeError("cannot run gh: %s" % exc)
    if proc.returncode != 0:
        found = HTTP_STATUS_RE.search(proc.stderr or "")
        raise MergeError(
            "%s %s failed: %s" % (method.upper(), path, (proc.stderr or "").strip()),
            status=int(found.group(1)) if found else None,
        )
    return _parse_json_stream(proc.stdout)


def fixture_name(method, path):
    """The file a `--fixtures` run reads for one request. Tests build their fixtures with it."""
    return "%s_%s.json" % (method.upper(), re.sub(r"[/?&=]", "_", path))


class FixtureAPI(object):
    """The test double for `gh_api`: a GET reads `<dir>/<method>_<path>.json` (a missing file is
    a MergeError naming it, so a forgotten fixture fails loudly rather than merging silently), and
    a mutating call appends `{"method","path","fields"}` to `<dir>/calls.jsonl` instead of being
    sent. Nothing here opens a socket."""

    def __init__(self, directory):
        self.dir = directory
        self.calls_path = os.path.join(directory, "calls.jsonl")

    def __call__(self, method, path, fields=None):
        path_file = os.path.join(self.dir, fixture_name(method, path))
        if method.upper() != "GET":
            with open(self.calls_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"method": method.upper(), "path": path,
                                    "fields": fields or {}}, sort_keys=True) + "\n")
        elif not os.path.exists(path_file):
            raise MergeError("no fixture %s for GET %s" % (path_file, path))
        if not os.path.exists(path_file):
            return {}
        with open(path_file, encoding="utf-8") as f:
            return json.load(f)


def items(payload, key=None):
    """The list inside an API response: the array itself, or `payload[key]` for object endpoints."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and key and isinstance(payload.get(key), list):
        return payload[key]
    return []


def _ts(value):
    """Parse a GitHub ISO-8601 timestamp into an aware datetime, or None."""
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _get(mapping, *path):
    """`mapping["a"]["b"]` with every missing or non-dict level answering None."""
    cur = mapping
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _superseded_by_a_later_success(run, matching):
    """True when `run` was cancelled and a later run of the same workflow on this head succeeded.

    GitHub holds one running and one pending run per concurrency group and evicts the pending one
    when a third event joins, whatever `cancel-in-progress` says. So a `cancelled` row can land on a
    ready head with no push at all -- go ready, apply a label, edit the body -- and
    `check_required_runs` refuses on any completed non-success run, which no later green run clears.
    Only a new commit would. The later success is what makes the cancelled row not evidence; a
    cancelled run with no later success still refuses, as it always did (work/ci-budget R-6).

    The join key is `workflow_id`, never `name`. A workflow's `name:` is a string the head branch
    writes: a diff may add `.github/workflows/x.yml` with `name: sdlc-gate` and a body that always
    succeeds, and on a same-repository pull request that file runs from the head. Keyed on the name,
    such a run would supersede the real gate's cancelled row and `check_required_runs` would read
    green for a commit the real gate never judged. Before this rule that forgery bought nothing,
    because every matching run had to be green; it must not start buying something now. A run with
    no `workflow_id` supersedes nothing, which is the closed answer (PR-A security pass)."""
    if run.get("status") != "completed" or run.get("conclusion") != CANCELLED:
        return False
    workflow = run.get("workflow_id")
    if workflow is None:
        return False
    return any(other.get("workflow_id") == workflow
               and other.get("status") == "completed"
               and other.get("conclusion") == "success"
               and (other.get("id") or 0) > (run.get("id") or 0)
               for other in matching)


def _pr_runs(runs, head_ref):
    """The workflow runs that judged THIS pull request: `event == "pull_request"` on `head_ref`.

    A `workflow_dispatch` or `schedule` run of the same workflow is one anybody with write access
    can start green on any code, and a run of another branch never saw this diff, so neither may
    stand in for a required check (pull request 45 security pass, finding 5).

    Two more are dropped here, and nowhere else, so `check_required_runs`, `check_review` and
    `check_cool_off` need no rule of their own (work/ci-budget R-6, spec D2):
      - a completed `skipped` run. A `pull_request` run concludes skipped only when every job's
        `if:` was false, which after the gate's draft guard means the head was a draft or the event
        was a Bot's body edit. Neither says anything about the head that later went ready on the
        same sha, and without this every pull request that was ever a draft is unmergeable.
      - a cancelled run a later success superseded, per the helper above.
    Nothing else is ever dropped: `failure`, `timed_out`, a run still in progress and a cancelled
    run with nothing after it all reach the conditions exactly as before. The empty-`matching`
    refusal in `check_required_runs` is what keeps "nothing passed" from reading as "nothing
    failed": dropping every row of a workflow leaves no run at all, which is a refusal."""
    matching = [r for r in (runs or [])
                if r.get("event") == "pull_request" and r.get("head_branch") == head_ref]
    return [r for r in matching
            if not (r.get("status") == "completed" and r.get("conclusion") == SKIPPED)
            and not _superseded_by_a_later_success(r, matching)]


# --- Conditions. Each is pure: it takes the JSON (and policy/config) it needs and returns
# (verdict, detail), with no I/O, so every refusal in R-15 has a unit test of its own. ---------
def check_policy(policy):
    """1. `merge.enabled`. A missing file or a false flag is the closed state, not an error."""
    if not policy.exists:
        return REFUSED, "policy off (no %s)" % policy.path
    if not policy.enabled:
        return REFUSED, "policy off (delegated mode is off in %s)" % policy.path
    if not policy.merge.get("enabled"):
        return REFUSED, "policy off (merge.enabled is false in %s)" % policy.path
    return OK, "merge enabled, method %s" % policy.merge.get("method")


def check_event(event):
    """2. The event is a completed, successful `pull_request` run of this repository (never a
    fork). A conclusion that is not `success` is refused here rather than left to the checks
    condition: a red required workflow is the answer, whatever a later re-read of the run list
    might say (pull request 45 security pass, nit d)."""
    run = event.get("workflow_run") or {}
    if run.get("event") != "pull_request":
        return REFUSED, "workflow_run.event is '%s', not 'pull_request'" % run.get("event")
    head_repo = _get(run, "head_repository", "full_name")
    repo = _get(event, "repository", "full_name")
    if not head_repo or head_repo != repo:
        return REFUSED, "head repository '%s' is not '%s' (fork pull requests are never merged)" % (
            head_repo, repo)
    if not run.get("conclusion"):
        return REFUSED, "workflow_run has no conclusion yet"
    if run.get("conclusion") != "success":
        return REFUSED, "workflow_run concluded %s, not success" % run.get("conclusion")
    return OK, "%s run %s concluded %s" % (run.get("name"), run.get("id"), run.get("conclusion"))


def pick_pr(pulls, head_sha):
    """The single open pull request whose head sha is `head_sha`, or None when it is not unique."""
    matches = [p for p in (pulls or [])
               if p.get("state") == "open" and _get(p, "head", "sha") == head_sha]
    return matches[0] if len(matches) == 1 else None


def check_delegation(pull, root):
    """3. Is this item delegated at all? A supervised one is not this workflow's to merge.

    Read from the checkout this job runs in, which is always the default branch, never the head
    under judgement (delegated-merge.yml). No API call: the file is on disk.

    Three answers are `ok` rather than `not-delegated`, because each belongs to a condition that
    refuses it properly and red:
      - no `Work-Item:` line, which `check_pull_request` refuses;
      - no `work/<slug>/intent.md` in this checkout, which `check_grant_front_matter` refuses;
      - an intent whose own status is `delegated`, i.e. an agent that signed its own grant. That is
        the single most serious refusal this script makes, and folding it into a green run would
        hide it (work/ci-budget, plan step 4, third invariant).
    """
    slug = work_item_slug((pull or {}).get("body"))
    if not slug:
        return OK, "no Work-Item line; the pull-request condition decides"
    path = os.path.join(root or ".", "work", slug, "intent.md")
    try:
        with open(path, encoding="utf-8") as handle:
            front = chain.front_matter_text(handle.read())
    except (OSError, IOError):
        return OK, "no work/%s/intent.md in this checkout; the grant condition decides" % slug
    if (front.get("status") or "").strip() == "delegated":
        return OK, "work/%s/intent.md is signed 'delegated'; the grant condition decides" % slug
    mode = (front.get("mode") or "supervised").strip()
    if mode.lower() == "delegated" and mode != "delegated":
        # `Delegated` is not the grant word, and the grant condition says so in as many words. This
        # condition must not answer a green `not-delegated` over that: a misspelling on an intent
        # meant to be delegated is a red run with a reason, not a quiet pass (PR-A M2 revision).
        return OK, "work/%s/intent.md mode is '%s'; the grant condition decides" % (slug, mode)
    if mode != "delegated":
        return NOT_DELEGATED, "#%s, Work-Item: %s, mode %s" % (
            (pull or {}).get("number"), slug, mode)
    return OK, "work/%s is delegated" % slug


def _locked_paths(config, policy, slug):
    """Every path a delegated pull request may not touch: the repository's own protected and
    release-gated classes, the policy's `locked-paths`, and this item's intent."""
    locked = list(config.get("PROTECTED_PATHS") or []) + \
        list(config.get("RELEASE_GATED_PATHS") or []) + list(policy.locked_paths)
    if slug:
        # The grant is read from the base, so a diff that rewrites this item's intent cannot widen
        # its own permission -- but it must not land under a delegated merge either.
        locked.append("work/%s/intent.md" % slug)
    return locked


def work_item_slug(body):
    """The slug on the pull request body's `Work-Item: <slug>` line, or None.

    A slug that is not a plain path segment is no slug: it is interpolated into
    `work/<slug>/intent.md`, so `..` or `.git` would read a file that is not this item's
    (pull request 45 security pass, finding 7)."""
    for line in (body or "").splitlines():
        found = WORK_ITEM_RE.match(line.strip())
        if found and SLUG_RE.match(found.group(1)):
            return found.group(1)
    return None


def check_pull_request(pulls, head_sha, agent_prefixes, default_branch, active_slug=""):
    """3. Exactly one open, non-draft agent pull request into the default branch, whose slug is the
    work item `.sdlc/active` names.

    The slug decides which intent.md is read for the grant, and the body that carries it is written
    by whoever opened the pull request. Binding it to `.sdlc/active` -- read from the base checkout
    this script runs from, never from the head -- means a branch cannot point the grant check at
    another item's approved intent (pull request 45 security pass, finding 7)."""
    open_matches = [p for p in (pulls or [])
                    if p.get("state") == "open" and _get(p, "head", "sha") == head_sha]
    if len(open_matches) != 1:
        return REFUSED, "%d open pull requests have head sha %s; need exactly one" % (
            len(open_matches), head_sha)
    pr = open_matches[0]
    if pr.get("draft"):
        return REFUSED, "pull request #%s is a draft" % pr.get("number")
    ref = _get(pr, "head", "ref") or ""
    if not any(ref.startswith(prefix) for prefix in agent_prefixes):
        return REFUSED, "head branch '%s' has no AGENT_BRANCH_PREFIXES prefix (%s)" % (
            ref, " ".join(agent_prefixes) or "none")
    slug = work_item_slug(pr.get("body"))
    if not slug:
        return REFUSED, "no 'Work-Item: <slug>' line in the body of #%s" % pr.get("number")
    active = (active_slug or "").strip()
    if slug != active:
        return REFUSED, ("Work-Item is '%s' but .sdlc/active names '%s'; only the active work item "
                         "is merged" % (slug, active))
    base = _get(pr, "base", "ref")
    if base != default_branch:
        return REFUSED, "base branch is '%s', not the default branch '%s'" % (base, default_branch)
    return OK, "#%s %s -> %s, Work-Item: %s" % (pr.get("number"), ref, base, slug)


def check_required_runs(runs, require_checks, head_ref):
    """4a. Every `require_checks` workflow ran on this head sha for this pull request, and every
    such run succeeded.

    Only `event == "pull_request"` runs of `head_ref` count (`_pr_runs`), and *all* of them must be
    green rather than merely one: a manually dispatched green run beside a failed pull_request run
    used to satisfy this condition, which is a check anybody with write access could start
    (pull request 45 security pass, finding 5). A name with no run at all refuses rather than
    waits: `agent-evals.yml` has a `paths:` filter, so a pull request outside those paths produces
    no run and would otherwise wait forever (spec gotchas)."""
    for name in require_checks:
        matching = [r for r in _pr_runs(runs, head_ref) if r.get("name") == name]
        if not matching:
            return REFUSED, ("required workflow '%s' has no pull_request run of '%s' on this head "
                             "sha (a workflow with a paths: filter never runs for a diff outside "
                             "them; list only always-run workflows in merge.require-checks)"
                             % (name, head_ref))
        failed = [r for r in matching
                  if r.get("status") == "completed" and r.get("conclusion") != "success"]
        if failed:
            return REFUSED, "required workflow '%s' concluded %s" % (
                name, failed[0].get("conclusion"))
        pending = [r for r in matching if r.get("status") != "completed"]
        if pending:
            return WAITING, "required workflow '%s' is %s" % (name, pending[0].get("status"))
    return OK, "%d required workflow(s) green" % len(require_checks)


def check_check_runs(check_runs, self_name=SELF_CHECK_NAME):
    """4b. Every other check run on the head sha is completed and not a failure."""
    failed, pending = [], []
    for run in check_runs or []:
        if run.get("name") == self_name:
            continue
        if run.get("status") != "completed":
            pending.append(run)
        elif run.get("conclusion") not in OK_CHECK_CONCLUSIONS:
            failed.append(run)
    if failed:
        return REFUSED, "check run '%s' concluded %s" % (
            failed[0].get("name"), failed[0].get("conclusion"))
    if pending:
        return WAITING, "check run '%s' is %s" % (pending[0].get("name"), pending[0].get("status"))
    return OK, "%d other check run(s) green" % len([
        r for r in (check_runs or []) if r.get("name") != self_name])


def check_grant_front_matter(front_matter, policy, base_ref=None):
    """5a. The BASE branch's `intent.md` carries a live grant a human wrote. `delegated` is named
    apart from every other non-approved status because it is the one an agent could have written,
    on the very file that carries its grant -- widening its own permission (decision record,
    decision 2). The file is read from the base, not the head: a grant that exists only on the
    branch under judgement was written by whoever wrote that branch (pull request 45 security
    pass, finding 2)."""
    on = (" on %s" % base_ref) if base_ref else ""
    if front_matter is None:
        return REFUSED, "no intent.md%s for this pull request" % on
    status = (front_matter.get("status") or "").strip()
    if status == "delegated":
        return REFUSED, "intent.md is signed 'delegated'; an agent never signs its own grant"
    if status != "approved":
        return REFUSED, "intent.md%s status is '%s', not 'approved'" % (on, status)
    mode = (front_matter.get("mode") or "").strip()
    if mode != "delegated":
        return REFUSED, "intent.md%s mode is '%s', not 'delegated'" % (on, mode or "supervised")
    ok, reason = policy.risk_ok(front_matter.get("risk-class"))
    if not ok:
        return REFUSED, reason
    if not (front_matter.get("delegated-by") or "").strip():
        return REFUSED, "intent.md%s has no delegated-by handle" % on
    return OK, "approved%s, delegated by %s, risk-class %s" % (
        on, front_matter.get("delegated-by"), front_matter.get("risk-class"))


def commit_adds_grant(commit_detail, path):
    """True when this commit's patch for `path` adds a `mode: delegated` line."""
    for changed in (commit_detail or {}).get("files") or []:
        if changed.get("filename") != path:
            continue
        for line in (changed.get("patch") or "").splitlines():
            if GRANT_LINE_RE.match(line):
                return True
    return False


def _grant_route_a(commit_detail, approvers_file, expected_handle, sha, on):
    """The signed-commit route, unchanged in behaviour: a human's own commit, GitHub-verified.

    The signature gate lives here rather than ahead of the route choice. It used to run first, and
    a first-running gate would refuse every route-B commit before its route was ever considered:
    an Actions runner pushes over git, and a git-pushed commit carries no signature at all
    (work/approve-by-dispatch, the plan's step 1 measurement).

    `author.login` is the account GitHub attributed the commit to, and `expected_handle` is the
    intent's own `delegated-by`: the file's claim of who granted must be the login that wrote it,
    or the ledger names one human and the commit another. Author and committer are two different
    people and the signature covers only the committer -- `author.login` is resolved from an author
    email the committer sets freely -- so the committer must be a product owner too, or GitHub's own
    `web-flow` signer (pull request 45 security pass, finding 1). `reason == "valid"` is required
    alongside `verified` for the same fail-closed reason: no other reason string is a signature this
    script understands.
    """
    verified = _get(commit_detail, "commit", "verification", "verified")
    reason = _get(commit_detail, "commit", "verification", "reason") or "unverified"
    if not verified or reason != "valid":
        return REFUSED, "grant commit %s is not GitHub-verified (%s)" % (sha[:12], reason)
    login = _get(commit_detail, "author", "login") or ""
    ok, why = approvers_file.has_role("product-owner", login)
    if not ok:
        return REFUSED, "grant commit %s author '%s': %s" % (sha[:12], login, why)
    norm = approvers.Approvers.normalize
    if expected_handle is not None and norm(expected_handle) != norm(login):
        return REFUSED, "intent.md says delegated-by '%s' but the grant commit %s is by '%s'" % (
            expected_handle, sha[:12], login)
    committer = _get(commit_detail, "committer", "login") or ""
    committer_ok, committer_why = approvers_file.has_role("product-owner", committer)
    if not committer_ok and norm(committer) != WEB_FLOW_LOGIN:
        return REFUSED, ("grant commit %s is signed by committer '%s', not by the author '%s': %s "
                         "(only a product owner or GitHub's own '%s' may commit a grant)"
                         % (sha[:12], committer, login, committer_why, WEB_FLOW_LOGIN))
    return OK, "granted%s in verified commit %s by %s (committed by %s)" % (
        on, sha[:12], login, committer)


def _grant_route_b(commit_detail, approvers_file, expected_handle, sha, on, dispatch,
                   trailer_actor, slug=None):
    """The dispatch route: the grant was a tap in the Actions tab, and the run says who made it.

    Not a fallback. It is taken only when the commit carries an `Approved-Run` trailer, and a
    trailer that does not resolve to a matching run is refused outright rather than retried on
    route A -- otherwise a forged trailer would be a way to *choose* the weaker check.

    It substitutes conditions rather than adding one. Route A's signature is replaced by the run
    record, which is the stronger proxy for "a human caused this": `actor.login` is set by GitHub
    when the run starts and nothing inside the run can change it, whereas a signature only proves
    the committer held a key. The signature condition is dropped because it cannot be met -- a
    commit pushed over git from a runner is unsigned -- and the committer condition survives as the
    bot identity approve_dispatch.py sets (spec R-7, C4; the plan's step 1).
    """
    norm = approvers.Approvers.normalize
    if not dispatch:
        return REFUSED, ("grant commit %s carries an Approved-Run trailer but the run could not be "
                         "read; a trailer that does not resolve is refused" % sha[:12])
    for field, got, want in (("event", dispatch.get("event"), "workflow_dispatch"),
                             ("path", dispatch.get("path"), chain.DISPATCH_WORKFLOW_PATH),
                             ("conclusion", dispatch.get("conclusion"), "success")):
        if (got or "") != want:
            return REFUSED, "grant commit %s: dispatch run %s is %r, expected %r" % (
                sha[:12], field, got, want)
    actor = _get(dispatch, "actor", "login") or ""
    ok, why = approvers_file.has_role("product-owner", actor)
    if not ok:
        return REFUSED, "grant commit %s: dispatch actor '%s': %s" % (sha[:12], actor, why)
    if norm(trailer_actor or "") != norm(actor):
        return REFUSED, ("grant commit %s says Approved-Actor '%s' but the run was started by '%s'"
                         % (sha[:12], trailer_actor, actor))
    if expected_handle is not None and norm(expected_handle) != norm(actor):
        return REFUSED, "intent.md says delegated-by '%s' but the dispatch was run by '%s'" % (
            expected_handle, actor)
    title = dispatch.get("display_title") or dispatch.get("name") or ""
    if slug and slug not in title:
        return REFUSED, "grant commit %s: dispatch run-name %r does not name '%s'" % (
            sha[:12], title, slug)
    if "intent.md" not in title:
        return REFUSED, "grant commit %s: dispatch run-name %r does not name intent.md" % (
            sha[:12], title)
    committer = _get(commit_detail, "committer", "login") or ""
    # The bot and nothing else. `web-flow` is GitHub's signer for web-editor and API commits, which
    # is route A's territory: mechanism 1 never produces it, because approve_dispatch.py sets the
    # committer explicitly. Accepting it here would widen route B past what the plan's step 1
    # concluded, for no case that can actually arise (pull request 51 plan-conformance pass).
    if norm(committer) != norm(BOT_LOGIN):
        return REFUSED, ("grant commit %s was dispatched but committed by '%s', not '%s'"
                         % (sha[:12], committer, BOT_LOGIN))
    return OK, "granted%s by dispatch run %s, started by %s (committed by %s)" % (
        on, dispatch.get("id") or "?", actor, committer)


def _dispatch_run(repo, commit_detail):
    """The Actions run a grant commit's `Approved-Run` trailer names, or None.

    None is not "no trailer": route B refuses a commit whose trailer it cannot resolve, so a run
    that 404s or an API that is unreachable fails the merge closed, as every other condition here
    does. A commit with no trailer never reaches this call's result, because route A is chosen
    before `dispatch` is read.
    """
    message = _get(commit_detail or {}, "commit", "message") or ""
    m = chain.APPROVED_RUN_RE.search(message)
    if not m:
        return None
    try:
        return gh_api("GET", "repos/%s/actions/runs/%s" % (repo, m.group(1)))
    except MergeError:
        return None


def check_grant_commit(commit_detail, approvers_file, expected_handle=None, base_ref=None,
                       dispatch=None, slug=None):
    """5b. The grant commit really was caused by the product owner the intent names.

    Two routes, chosen by the commit itself, never tried in turn. Route A (`_grant_route_a`) is a
    human's own signed commit. Route B (`_grant_route_b`) is a tap in the Actions tab, taken when
    and only when the commit carries an `Approved-Run` trailer. Each names its own conditions, and
    a commit that fails the route it selected is refused -- there is no second attempt, because
    falling back would let a forged trailer pick which check to face (spec R-7, C4).
    """
    on = (" on %s" % base_ref) if base_ref else ""
    if not commit_detail:
        return REFUSED, ("no commit adding the grant line in the last %d commits touching the "
                         "intent%s" % (GRANT_WINDOW, on))
    sha = commit_detail.get("sha") or "?"
    message = _get(commit_detail, "commit", "message") or ""
    actor_match = chain.APPROVED_ACTOR_RE.search(message)
    if chain.APPROVED_RUN_RE.search(message):
        return _grant_route_b(commit_detail, approvers_file, expected_handle, sha, on, dispatch,
                              actor_match.group(1) if actor_match else "", slug=slug)
    return _grant_route_a(commit_detail, approvers_file, expected_handle, sha, on)


def check_locked_paths(files, prefixes):
    """6. The diff touches nothing locked, under either its current or its former name.

    ALWAYS_LOCKED is this script's own floor -- the control plane, the rule and template files, and
    the surfaces that judge a pull request -- and `prefixes` (PROTECTED_PATHS, RELEASE_GATED_PATHS,
    the policy's `locked-paths` and this item's own intent.md) only ever adds to it: a policy file
    can widen what is locked, never narrow it. A rename is checked on `previous_filename` as well,
    since `git mv REVIEW.md x.md` empties a judging surface without any entry naming it
    (pull request 45 security pass, finding 6).

    Prefix match on whole path segments, the comparison `check_control_plane.sh` makes (`f == p`
    or `f` under `p/`), so a file entry never matches a longer name and a directory covers its
    tree. This is what makes the head's own sdlc-gate trustworthy (spec D6)."""
    locked = [p.rstrip("/") for p in (list(ALWAYS_LOCKED) + list(prefixes or []))]
    for changed in files or []:
        for key in ("filename", "previous_filename"):
            name = changed.get(key) or ""
            for prefix in locked:
                if name == prefix or name.startswith(prefix + "/"):
                    return REFUSED, "%s is under the locked path '%s'" % (name, prefix)
    return OK, "%d changed file(s), none locked" % len(files or [])


def check_review(comments, runs, head_ref):
    """7. The review verdict comes from the `pr-review` workflow's own run of this head, and that
    run's tracking comment reports `Important: 0`.

    A `claude[bot]` comment is not evidence by itself: the comment API takes any token, so a body
    ending `Important: 0` is something an agent's own credential could write. The runs already
    fetched for this head sha are: every `pr-review` run of `head_ref` on this sha must have
    concluded `success` (a failed one refuses, none yet waits), and only a comment linking the
    newest such run's id counts. Of those, the EARLIEST is read -- the tracking comment the action
    opens when the run starts -- so a later comment forged with the same link cannot overwrite the
    verdict. The run's own `head_sha` is what binds the review to this head, which is why no
    timestamp is compared any more (pull request 45 security pass, findings 3 and 4).

    Fails closed (spec Q3): no credential means no run and no comment, which waits for the owner
    rather than merging."""
    matching = [r for r in _pr_runs(runs, head_ref) if r.get("name") == REVIEW_WORKFLOW_NAME]
    completed = [r for r in matching if r.get("status") == "completed"]
    failed = [r for r in completed if r.get("conclusion") != "success"]
    if failed:
        return REFUSED, "%s run %s concluded %s" % (
            REVIEW_WORKFLOW_NAME, failed[0].get("id"), failed[0].get("conclusion"))
    if not completed:
        return WAITING, "no completed %s run of '%s' on this head sha yet" % (
            REVIEW_WORKFLOW_NAME, head_ref)
    newest = max(completed, key=lambda r: int(r.get("id") or 0))
    link = REVIEW_RUN_LINK % newest.get("id")
    bot = [c for c in (comments or [])
           if _get(c, "user", "login") == REVIEW_BOT_LOGIN
           and _get(c, "user", "type") == REVIEW_BOT_TYPE
           and link in (c.get("body") or "")]
    if not bot:
        return WAITING, "no %s comment links %s run %s yet" % (
            REVIEW_BOT_LOGIN, REVIEW_WORKFLOW_NAME, newest.get("id"))
    bot.sort(key=lambda c: str(c.get("created_at") or ""))
    tracking = bot[0]  # the comment the action opened for that run
    summary = None
    for line in (tracking.get("body") or "").splitlines():
        found = REVIEW_SUMMARY_RE.match(line.strip())
        if found:
            summary = found
    if summary is None:
        return WAITING, ("the %s comment for %s run %s has no 'Important: <n> | Nits: <m>' line"
                         % (REVIEW_BOT_LOGIN, REVIEW_WORKFLOW_NAME, newest.get("id")))
    important = int(summary.group(1))
    if important:
        return REFUSED, "the review reports Important: %d" % important
    return OK, "%s run %s reports Important: 0 | Nits: %s" % (
        REVIEW_WORKFLOW_NAME, newest.get("id"), summary.group(2))


def check_cool_off(runs, require_checks, cool_off_hours, now, head_ref):
    """8. `cool_off_hours` have passed since the newest required run of this pull request finished.
    Same filter as the checks condition: a dispatched or foreign-branch run is not a stamp this
    pull request earned (pull request 45 security pass, finding 5)."""
    if not cool_off_hours:
        return OK, "no cool-off configured"
    stamps = [_ts(r.get("updated_at")) for r in _pr_runs(runs, head_ref)
              if r.get("name") in require_checks]
    stamps = [s for s in stamps if s is not None]
    if not stamps:
        return WAITING, "no required run has an updated_at to measure the cool-off from"
    newest = max(stamps)
    ready = newest + timedelta(hours=cool_off_hours)
    if now < ready:
        return WAITING, "cool-off of %sh ends at %s" % (cool_off_hours, ready.isoformat())
    return OK, "cool-off of %sh elapsed since %s" % (cool_off_hours, newest.isoformat())


def merge_comment_body(handle, grant_sha):
    """The comment left on the merged pull request: who granted the delegation, and where. The
    handle is normalised (`approvers.Approvers.normalize`), never the raw front-matter text: the
    comment is a record, and front matter is a field a branch can fill with anything
    (pull request 45 security pass, nit c)."""
    return ("merged under delegation granted by %s in %s\n\n---\n"
            "_Generated by the delegated-merge workflow_"
            % (approvers.Approvers.normalize(handle), grant_sha))


# --- Runner ----------------------------------------------------------------
def load_config(root):
    """`.sdlc/config.env` under `root`, through check_artifact_chain.config() -- the one parser
    for that file. It takes no root (it reads the git root), so the module global is swapped for
    the single call and restored; in CI the root *is* the git root, which is main's checkout."""
    previous = chain.ROOT
    chain.ROOT = root
    try:
        return chain.config()
    finally:
        chain.ROOT = previous


def read_active_slug(root):
    """`<root>/.sdlc/active`, stripped -- the work item main says is being worked on. An empty
    string when the file is missing, which refuses every pull request rather than merging one."""
    try:
        with open(os.path.join(root, ".sdlc", "active"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


class Run(object):
    """Prints one line per condition and remembers the first non-`ok` verdict."""

    def __init__(self, dry_run, stream=None):
        self.dry_run = dry_run
        self.stream = stream or sys.stdout
        self.first_bad = None
        self.bad = []

    def record(self, name, result):
        verdict, detail = result
        self.stream.write(u"CONDITION %s: %s — %s\n" % (name, verdict, detail))
        if verdict != OK:
            self.bad.append((name, verdict, detail))
            if self.first_bad is None:
                self.first_bad = (name, verdict, detail)
        return verdict == OK

    def keep_going(self, ok):
        """Stop at the first refusal; under --dry-run evaluate everything still evaluable."""
        return ok or self.dry_run

    def _worst(self):
        """The verdict that decides the run. `not-delegated` is outranked by anything else: it
        says only that this workflow does not merge supervised items, so a locked path or a refused
        pull request recorded beside it is what the run must report and go red on
        (work/ci-budget R-7)."""
        if not self.bad:
            return None
        for entry in self.bad:
            if entry[1] != NOT_DELEGATED:
                return entry
        return self.bad[0]

    def _code(self):
        """0 on a merge or a wait, 1 on a refusal -- with two documented exceptions: delegated
        merging being off is the closed state, and a supervised item is not this workflow's to
        merge. Neither is a failed run; every other refusal still is."""
        worst = self._worst()
        if worst is None:
            return 0
        name, verdict, _ = worst
        if verdict in (WAITING, NOT_DELEGATED) or name == "policy":
            return 0
        return 1

    def finish(self, merged=None):
        worst = self._worst()
        if self.dry_run:
            if worst is None:
                verdict = "would merge #%s" % merged if merged else "all conditions ok"
            else:
                verdict = "%s: %s" % (worst[1], worst[0])
            self.stream.write("DELEGATED-MERGE: dry-run (%s)\n" % verdict)
            return self._code()
        if worst is None:
            self.stream.write("DELEGATED-MERGE: merged %s\n" % merged)
            return 0
        self.stream.write("DELEGATED-MERGE: %s (%s)\n" % (worst[1], worst[0]))
        return self._code()


def _decode_contents(payload):
    """The text of a `contents/` response (base64), or None."""
    if not isinstance(payload, dict) or payload.get("encoding") != "base64":
        return None
    try:
        return base64.b64decode(payload.get("content") or "").decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None


GRANT_WINDOW = 100


def _grant_commit(repo, slug, base_ref):
    """The commit that wrote the grant, on the BASE branch: the newest of the last GRANT_WINDOW
    commits touching the intent whose patch adds `mode: delegated`, or None. `sha=<base_ref>` --
    never the head sha -- because a grant commit that exists only on the branch under judgement is
    a commit that branch wrote (pull request 45 security pass, finding 2). There is no fallback to
    "the newest commit touching the file": a commit that never wrote the grant is not the grant,
    however trusted its author (pull request 45 plan-conformance pass, finding 3)."""
    path = "work/%s/intent.md" % slug
    # `gh_api` GETs with --paginate, so `per_page` bounds a page, not the answer: slice the window
    # back on, or "the last 100 commits" in the refusal would be a lie.
    listed = items(gh_api("GET", "repos/%s/commits?path=%s&sha=%s&per_page=%d"
                          % (repo, path, base_ref, GRANT_WINDOW)))[:GRANT_WINDOW]
    for entry in listed:  # the commits endpoint is newest first
        detail = gh_api("GET", "repos/%s/commits/%s" % (repo, entry.get("sha")))
        # GitHub omits `files[].patch` for very large commits; that reads here as "this commit did
        # not add the grant", which is the fail-closed answer and must stay one.
        if commit_adds_grant(detail, path):
            return detail
    return None


def run(event, policy, config, approvers_file, dry_run=False, now=None, stream=None,
        active_slug="", root=""):
    """Evaluate every condition in order and, unless --dry-run, merge. Returns the exit code."""
    out = Run(dry_run, stream)
    now = now or datetime.now(timezone.utc)

    if not out.record("policy", check_policy(policy)):
        return out.finish()

    wf = event.get("workflow_run") or {}
    repo = _get(event, "repository", "full_name") or ""
    head_sha = wf.get("head_sha") or ""
    default_branch = _get(event, "repository", "default_branch") or "main"
    ok = out.record("event", check_event(event))
    if not out.keep_going(ok) or not (repo and head_sha):
        return out.finish()

    pulls = items(gh_api("GET", "repos/%s/commits/%s/pulls" % (repo, head_sha)))
    prefixes = config.get("AGENT_BRANCH_PREFIXES") or []
    # The pull request whose body supplies the slug is the one pick_pr selects, so it is resolved
    # before the delegation condition reads it; `check_pull_request` below still refuses an
    # ambiguous or missing one (work/ci-budget R-7).
    pr = pick_pr(pulls, head_sha)
    delegated = out.record("delegation", check_delegation(pr, root))
    ok = out.record("pull-request",
                    check_pull_request(pulls, head_sha, prefixes, default_branch, active_slug))
    if not out.keep_going(ok) or pr is None:
        return out.finish()
    number = pr.get("number")
    slug = work_item_slug(pr.get("body"))
    if not delegated and not out.dry_run:
        # A supervised item: the grant, the checks, the review and the cool-off all judge whether an
        # item this workflow could merge is ready, and this one it could never merge. `locked-paths`
        # still runs, so an agent branch touching the control plane stays a red run with its own
        # condition line whatever its item's mode (work/ci-budget R-7).
        #
        # Under --dry-run none of this applies: that route exists to print every condition and its
        # verdict for a sha, which is exactly what the owner wants against a supervised pull
        # request, so it falls through and evaluates the rest as the module docstring promises.
        files = items(gh_api("GET", "repos/%s/pulls/%s/files?per_page=100" % (repo, number)))
        out.record("locked-paths", check_locked_paths(files, _locked_paths(config, policy, slug)))
        return out.finish()
    head_ref = _get(pr, "head", "ref") or ""
    # The base of this pull request: the branch this job checked out, and the only history that
    # existed before the head branch did. Every grant read below uses it.
    base_ref = _get(pr, "base", "ref") or default_branch

    required = policy.merge.get("require_checks") or []
    runs = items(gh_api("GET", "repos/%s/actions/runs?head_sha=%s&per_page=100" % (repo, head_sha)),
                 "workflow_runs")
    checks_result = check_required_runs(runs, required, head_ref)
    if checks_result[0] == OK:
        check_runs = items(
            gh_api("GET", "repos/%s/commits/%s/check-runs?per_page=100" % (repo, head_sha)),
            "check_runs")
        checks_result = check_check_runs(check_runs)
    ok = out.record("checks", checks_result)
    if not out.keep_going(ok):
        return out.finish()

    grant_sha, grant_handle = "", ""
    if slug:
        contents = gh_api("GET", "repos/%s/contents/work/%s/intent.md?ref=%s"
                          % (repo, slug, base_ref))
        text = _decode_contents(contents)
        front = chain.front_matter_text(text) if text is not None else None
        grant_result = check_grant_front_matter(front, policy, base_ref=base_ref)
        if grant_result[0] == OK:
            grant_handle = (front.get("delegated-by") or "").strip()
            detail = _grant_commit(repo, slug, base_ref)
            grant_sha = (detail or {}).get("sha") or ""
            grant_result = check_grant_commit(detail, approvers_file,
                                              expected_handle=grant_handle, base_ref=base_ref,
                                              dispatch=_dispatch_run(repo, detail), slug=slug)
        ok = out.record("grant", grant_result)
        if not out.keep_going(ok):
            return out.finish()

    files = items(gh_api("GET", "repos/%s/pulls/%s/files?per_page=100" % (repo, number)))
    ok = out.record("locked-paths", check_locked_paths(files, _locked_paths(config, policy, slug)))
    if not out.keep_going(ok):
        return out.finish()

    if policy.merge.get("require_review"):
        comments = items(gh_api("GET", "repos/%s/issues/%s/comments?per_page=100" % (repo, number)))
        ok = out.record("review", check_review(comments, runs, head_ref))
        if not out.keep_going(ok):
            return out.finish()

    ok = out.record("cool-off",
                    check_cool_off(runs, required, policy.merge.get("cool_off_hours") or 0, now,
                                   head_ref))
    if not out.keep_going(ok):
        return out.finish()

    if dry_run:
        return out.finish(merged=number)

    try:
        gh_api("PUT", "repos/%s/pulls/%s/merge" % (repo, number), {
            "sha": head_sha,
            "merge_method": policy.merge.get("method"),
            # The head label is the branch's own text; the merge commit names the pull request,
            # which is the record (pull request 45 security pass, nit f).
            "commit_title": "Merge pull request #%s (delegated)" % number,
        })
    except MergeError as exc:
        if exc.status in STALE_STATUSES:
            # The head moved between the check completing and this call. Not an error: the push
            # that moved it will complete its own checks and fire this workflow again.
            out.stream.write(u"CONDITION merge: %s — head sha %s no longer mergeable (HTTP %s)\n"
                             % (REFUSED, head_sha[:12], exc.status))
            out.stream.write("DELEGATED-MERGE: refused (stale)\n")
            return 0
        raise

    try:
        gh_api("DELETE", "repos/%s/git/refs/heads/%s" % (repo, head_ref))
    except MergeError as exc:  # a protected or already-deleted branch is not a merge failure
        out.stream.write("note: could not delete %s: %s\n" % (head_ref, exc))
    gh_api("POST", "repos/%s/issues/%s/comments" % (repo, number),
           {"body": merge_comment_body(grant_handle, grant_sha)})
    # work/run-queue R-2: the merge is the moment the item finishes, and this checkout is main's
    # (the workflow takes the default branch, never the head), so this is the only place that may
    # move the pointer -- an item's own pull request never can, because `.sdlc` is ALWAYS_LOCKED.
    # A failure here never un-merges anything: it is logged and the run still reports the merge.
    if root:
        try:
            advance(root, out, slug, number, policy, now=now)
        except (OSError, ValueError, MergeError) as exc:
            # ValueError covers UnicodeDecodeError from a non-UTF-8 intent.md in the queue: the
            # merge already succeeded, so a crash here would report a failed job for work that
            # landed (security pass on pull request 55, nit 3). A git failure is a note too.
            out.stream.write("note: could not advance .sdlc/active: %s\n" % exc)
    return out.finish(merged="#%s %s" % (number, head_sha))


# The only paths the advance may write. Anything else staged means something other than this
# function touched the tree, and the commit is abandoned rather than made -- the same shape of
# guard as scripts/approve_dispatch.py's allowlist (work/run-queue R-5).
ADVANCE_IDENTITY = ("github-actions[bot]", "41898282+github-actions[bot]@users.noreply.github.com")


def _git(root, *args, **kw):
    r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)
    if kw.get("check", True) and r.returncode != 0:
        raise MergeError("git %s failed: %s" % (" ".join(args), r.stderr.strip()))
    return r.stdout.strip()


def _ledger_safe(value):
    """A front-matter value fit for a pipe-separated ledger field.

    `delegated-by` and `delegated-on` are hand-typed by a human at grant time and are interpolated
    into a `|`-delimited line that `log_ledger.parse` reads back; a `|` or a line break in either
    would push the line past six fields and make it MALFORMED, which silently drops it from
    `approvals()` and `signatures()` (security pass on pull request 55, nit 4). `scripts/sign.py`
    refuses such a note outright; here the line is written by CI with no one to ask, so the
    character is replaced and the value still reads.
    """
    text = (value or "?").strip()
    for bad, good in (("|", "/"), ("\r", " "), ("\n", " ")):
        text = text.replace(bad, good)
    return text or "?"


def _append_ledger(root, slug, entry):
    """Append one rendered ledger line to work/<slug>/log.md. Returns the relative path."""
    rel = "work/%s/log.md" % slug
    path = os.path.join(root, rel)
    with open(path, "a", encoding="utf-8") as f:
        f.write(log_ledger.render(entry) + "\n")
    return rel


def advance(root, out, merged_slug, number, policy, now=None):
    """Move `.sdlc/active` to the next queued item and record it on both ledgers.

    Refuses, writing nothing, on a dirty tree, when the pointer does not name the item just merged,
    and when the computed next item is the merged one. An empty queue clears the pointer, which is a
    valid state every reader already handles.

    What actually protects a concurrent run is the push at the end: it is not forced, so any commit
    that landed on the remote in between rejects it and this run stands down (security pass on pull
    request 55, nit 1). The pointer check below is a cheap precondition, not that protection --
    `check_pull_request` has already refused any pull request whose `Work-Item` is not the active
    slug, so in production it compares the file to itself. It is kept because `advance()` is also
    reachable directly, where it is the only thing standing between a wrong argument and a wrong
    write.
    """
    now = now or datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    # The allowlist below bounds which *files* are committed, not what is inside them: `git add` on
    # an already-dirty file would stage that file's other changes too (security pass, nit 2). The
    # workflow's checkout is always fresh, so a dirty tree here means something unexpected touched
    # it, and the honest answer is to write nothing at all.
    dirty = _git(root, "status", "--porcelain")
    if dirty:
        out.stream.write("note: the checkout is not clean, so nothing was advanced:\n%s\n" % dirty)
        return None
    pointer = read_active_slug(root)
    if pointer != merged_slug:
        out.stream.write("note: .sdlc/active names '%s', not the merged '%s'; not advancing\n"
                         % (pointer, merged_slug))
        return None
    nxt = next_item.next_item(root, policy, exclude=merged_slug)
    if nxt == merged_slug:  # defensive: exclude should already have removed it
        out.stream.write("note: the queue named the merged item; not advancing\n")
        return None

    sha = _git(root, "rev-parse", "--short", "HEAD") or "0000000"
    written = []
    with open(os.path.join(root, ".sdlc", "active"), "w", encoding="utf-8") as f:
        f.write((nxt + "\n") if nxt else "")
    written.append(".sdlc/active")

    note = ("merged as %s; .sdlc/active advanced to %s" % (sha, nxt) if nxt
            else "merged as %s; the queue is empty, .sdlc/active cleared" % sha)
    written.append(_append_ledger(root, merged_slug, log_ledger.Entry(
        ts=ts, artifact="PR #%s" % number, from_status="in-review", to_status="in-review",
        actor=ADVANCE_IDENTITY[0], sha=sha, note=note, lineno=0)))

    if nxt:
        fm = chain.front_matter(os.path.join(root, "work", nxt, "intent.md")) or {}
        written.append(_append_ledger(root, nxt, log_ledger.Entry(
            ts=ts, artifact="intent.md", from_status="approved", to_status="approved",
            actor=ADVANCE_IDENTITY[0], sha=sha,
            note=(".sdlc/active advanced here after PR #%s merged, under the grant by %s on %s"
                  % (number, _ledger_safe(fm.get("delegated-by")),
                     _ledger_safe(fm.get("delegated-on")))),
            lineno=0)))

    _git(root, "add", "--", *written)
    staged = [p for p in _git(root, "diff", "--cached", "--name-only").split("\n") if p]
    unexpected = sorted(set(staged) - set(written))
    if unexpected:
        _git(root, "reset", "-q", "HEAD", check=False)
        raise MergeError("refusing to commit paths outside the advance allowlist: %s"
                         % ", ".join(unexpected))
    _git(root, "-c", "user.name=%s" % ADVANCE_IDENTITY[0],
         "-c", "user.email=%s" % ADVANCE_IDENTITY[1],
         "commit", "-q", "-m",
         "[%s] Advance .sdlc/active after #%s merged" % (nxt or "queue-empty", number))
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    push = subprocess.run(["git", "-C", root, "push", "origin", "HEAD:%s" % branch],
                          capture_output=True, text=True)
    if push.returncode != 0:
        # Someone else pushed between the checkout and now. The pointer is unchanged on the remote,
        # and the next merge advances it; retrying here would race the same way.
        out.stream.write("note: advance commit not pushed (%s); the next merge will advance\n"
                         % (push.stderr.strip().splitlines() or ["push rejected"])[-1])
        return None
    out.stream.write("ADVANCE: .sdlc/active -> %s\n" % (nxt or "(empty queue)"))
    return nxt


def main(argv=None):
    global API
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true",
                        help="evaluate and print every condition; never call a mutating endpoint")
    parser.add_argument("--event", default=os.environ.get("GITHUB_EVENT_PATH"),
                        help="the workflow_run event JSON (default: $GITHUB_EVENT_PATH)")
    parser.add_argument("--policy", help="delegation policy (default: <root>/.sdlc/delegation.yaml)")
    parser.add_argument("--root", help="checkout to read .sdlc/ from (default: the git root)")
    parser.add_argument("--fixtures", help="test only: serve GETs from DIR, record writes there")
    parser.add_argument("--head-sha", metavar="SHA",
                        help="dry-run only: judge this head sha as if a pull_request run of it had "
                             "just completed (the workflow's workflow_dispatch route); implies --dry-run")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"),
                        help="with --head-sha: owner/repo (default: $GITHUB_REPOSITORY)")
    args = parser.parse_args(argv)

    root = args.root or chain.ROOT
    if args.fixtures:
        API = FixtureAPI(args.fixtures)

    if args.head_sha:
        # A synthesised event for an owner-triggered dry run: the same shape workflow_run delivers,
        # for this repository, so every condition below reads it the same way. Never a live merge.
        args.dry_run = True
        # The value comes from a workflow_dispatch input and is interpolated into API paths.
        if not HEAD_SHA_ARG_RE.match(args.head_sha):
            print("--head-sha must be 7-40 hex characters", file=sys.stderr)
            return 2
        if not args.repo:
            print("--head-sha needs --repo or $GITHUB_REPOSITORY", file=sys.stderr)
            return 2
        try:
            info = gh_api("GET", "repos/%s" % args.repo) or {}
        except MergeError as exc:
            print("GitHub call failed: %s" % exc, file=sys.stderr)
            return 1
        event = {
            "workflow_run": {"event": "pull_request", "head_sha": args.head_sha, "conclusion": "success",
                             "name": "dry-run", "id": 0,
                             "head_repository": {"full_name": args.repo}},
            "repository": {"full_name": args.repo,
                           "default_branch": info.get("default_branch") or "main"},
        }
    else:
        if not args.event:
            print("no event file: pass --event or set GITHUB_EVENT_PATH", file=sys.stderr)
            return 2
        try:
            with open(args.event, encoding="utf-8") as f:
                event = json.load(f)
        except (OSError, ValueError) as exc:
            print("cannot read the event file: %s" % exc, file=sys.stderr)
            return 2

    try:
        policy = delegation.load(path=args.policy or os.path.join(root, ".sdlc", "delegation.yaml"))
        config = load_config(root)
        rel = (config.get("APPROVERS_FILE") or [".sdlc/approvers.yaml"])[0]
        approvers_file = approvers.load(
            path=rel if os.path.isabs(rel) else os.path.join(root, rel))
    except (OSError, ValueError) as exc:
        print("cannot read the policy or approvers file: %s" % exc, file=sys.stderr)
        return 2
    try:
        return run(event, policy, config, approvers_file, dry_run=args.dry_run,
                   active_slug=read_active_slug(root), root=root)
    except MergeError as exc:
        print("GitHub call failed: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
