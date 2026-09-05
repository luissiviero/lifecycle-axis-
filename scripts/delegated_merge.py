#!/usr/bin/env python3
"""Merge a delegated pull request from CI, only when every printed condition holds.

Called by `.github/workflows/delegated-merge.yml` on a `workflow_run` completion, so it runs from
the default branch: this script and the three `.sdlc/` files it reads are always `main`'s copies,
never the head's (work/delegated-mode R-15, D6; knowledge/decisions/delegated-mode.md decision 6).
It is the click, for delegated items only; `merge-click-is-the-gate.md` still describes every
supervised pull request.

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

# This workflow's own check run, excluded from "every other check run must be green":
# it is in progress while it runs, so including it would make the condition unsatisfiable.
SELF_CHECK_NAME = "delegated-merge"
# The reviewer identity pr-review.yml posts as (docs/sdlc/spikes/pr-review-identity.md).
REVIEW_BOT_LOGIN = "claude[bot]"
REVIEW_BOT_TYPE = "Bot"
# REVIEW.md's summary line, added for exactly this condition (work/delegated-mode R-13).
REVIEW_SUMMARY_RE = re.compile(r"^Important: (\d+) \| Nits: (\d+)$")
# `Work-Item: <slug>` in the pull request body; the slug charset the repo's work/ dirs use.
WORK_ITEM_RE = re.compile(r"^Work-Item:\s*([A-Za-z0-9._-]+)$")
# The literal the `-G` pickaxe checks look for, here read out of a commit's patch.
GRANT_LINE_RE = re.compile(r"^\+mode:\s*delegated\s*$")
OK_CHECK_CONCLUSIONS = ("success", "skipped", "neutral")
# `gh api` reports the HTTP status in its stderr; 405/409 on the merge endpoint mean the sha moved.
HTTP_STATUS_RE = re.compile(r"HTTP (\d{3})")
STALE_STATUSES = (405, 409)

OK = "ok"
REFUSED = "refused"
WAITING = "waiting"

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
    """2. The event is a completed `pull_request` run of this repository (never a fork)."""
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
    return OK, "%s run %s concluded %s" % (run.get("name"), run.get("id"), run.get("conclusion"))


def pick_pr(pulls, head_sha):
    """The single open pull request whose head sha is `head_sha`, or None when it is not unique."""
    matches = [p for p in (pulls or [])
               if p.get("state") == "open" and _get(p, "head", "sha") == head_sha]
    return matches[0] if len(matches) == 1 else None


def work_item_slug(body):
    """The slug on the pull request body's `Work-Item: <slug>` line, or None."""
    for line in (body or "").splitlines():
        found = WORK_ITEM_RE.match(line.strip())
        if found:
            return found.group(1)
    return None


def check_pull_request(pulls, head_sha, agent_prefixes, default_branch):
    """3. Exactly one open, non-draft agent pull request into the default branch, with a slug."""
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
    base = _get(pr, "base", "ref")
    if base != default_branch:
        return REFUSED, "base branch is '%s', not the default branch '%s'" % (base, default_branch)
    return OK, "#%s %s -> %s, Work-Item: %s" % (pr.get("number"), ref, base, slug)


def check_required_runs(runs, require_checks):
    """4a. Every `require_checks` workflow ran on this head sha and succeeded. A name with no run
    at all refuses rather than waits: `agent-evals.yml` has a `paths:` filter, so a pull request
    outside those paths produces no run and would otherwise wait forever (spec gotchas)."""
    for name in require_checks:
        matching = [r for r in (runs or []) if r.get("name") == name]
        if not matching:
            return REFUSED, ("required workflow '%s' has no run on this head sha (a workflow with a "
                             "paths: filter never runs for a diff outside them; list only always-run "
                             "workflows in merge.require-checks)" % name)
        if any(r.get("status") == "completed" and r.get("conclusion") == "success"
               for r in matching):
            continue
        pending = [r for r in matching if r.get("status") != "completed"]
        if pending:
            return WAITING, "required workflow '%s' is %s" % (name, pending[0].get("status"))
        worst = matching[-1]
        return REFUSED, "required workflow '%s' concluded %s" % (name, worst.get("conclusion"))
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


def check_grant_front_matter(front_matter, policy):
    """5a. The head's `intent.md` carries a live grant a human wrote. `delegated` is named apart
    from every other non-approved status because it is the one an agent could have written, on the
    very file that carries its grant -- widening its own permission (decision record, decision 2)."""
    if front_matter is None:
        return REFUSED, "no intent.md at the head of this pull request"
    status = (front_matter.get("status") or "").strip()
    if status == "delegated":
        return REFUSED, "intent.md is signed 'delegated'; an agent never signs its own grant"
    if status != "approved":
        return REFUSED, "intent.md status is '%s', not 'approved'" % status
    mode = (front_matter.get("mode") or "").strip()
    if mode != "delegated":
        return REFUSED, "intent.md mode is '%s', not 'delegated'" % (mode or "supervised")
    ok, reason = policy.risk_ok(front_matter.get("risk-class"))
    if not ok:
        return REFUSED, reason
    if not (front_matter.get("delegated-by") or "").strip():
        return REFUSED, "intent.md has no delegated-by handle"
    return OK, "approved, delegated by %s, risk-class %s" % (
        front_matter.get("delegated-by"), front_matter.get("risk-class"))


def commit_adds_grant(commit_detail, path):
    """True when this commit's patch for `path` adds a `mode: delegated` line."""
    for changed in (commit_detail or {}).get("files") or []:
        if changed.get("filename") != path:
            continue
        for line in (changed.get("patch") or "").splitlines():
            if GRANT_LINE_RE.match(line):
                return True
    return False


def check_grant_commit(commit_detail, approvers_file, exact=True, expected_handle=None):
    """5b. The grant commit is GitHub-verified and authored by a product owner -- server-side, not
    git-authored: a local `git commit --author` cannot satisfy `commit.verification.verified`, and
    `author.login` is the account GitHub attributed the commit to (spec D2, decision 6).
    `expected_handle` is the intent's `delegated-by`: the file's own claim of who granted must be
    the login that wrote it, or the ledger would name one human and the commit another.
    `exact=False` means no commit in the window added the line and the newest one touching the
    file was judged instead, which the detail then says."""
    if not commit_detail:
        return REFUSED, "no commit found that touches the intent"
    sha = commit_detail.get("sha") or "?"
    how = "" if exact else " (no commit in the window adds 'mode: delegated'; using the newest one touching the file)"
    if not _get(commit_detail, "commit", "verification", "verified"):
        reason = _get(commit_detail, "commit", "verification", "reason") or "unverified"
        return REFUSED, "grant commit %s is not GitHub-verified (%s)%s" % (sha[:12], reason, how)
    login = _get(commit_detail, "author", "login") or ""
    ok, reason = approvers_file.has_role("product-owner", login)
    if not ok:
        return REFUSED, "grant commit %s author '%s': %s%s" % (sha[:12], login, reason, how)
    norm = approvers.Approvers.normalize
    if expected_handle is not None and norm(expected_handle) != norm(login):
        return REFUSED, "intent.md says delegated-by '%s' but the grant commit %s is by '%s'%s" % (
            expected_handle, sha[:12], login, how)
    return OK, "granted in verified commit %s by %s%s" % (sha[:12], login, how)


def check_locked_paths(files, prefixes):
    """6. The diff touches nothing under PROTECTED_PATHS, RELEASE_GATED_PATHS or locked-paths.
    Prefix match on whole path segments, the comparison `check_control_plane.sh` makes (`f == p`
    or `f` under `p/`), so a file entry never matches a longer name and a directory covers its
    tree. This is what makes the head's own sdlc-gate trustworthy (spec D6)."""
    for changed in files or []:
        name = changed.get("filename") or ""
        for prefix in prefixes:
            prefix = prefix.rstrip("/")
            if name == prefix or name.startswith(prefix + "/"):
                return REFUSED, "%s is under the locked path '%s'" % (name, prefix)
    return OK, "%d changed file(s), none locked" % len(files or [])


def check_review(comments, head_time):
    """7. The newest `claude[bot]` comment reviews *this* head and ends `Important: 0`. Fails
    closed (spec Q3): no credential means no comment, which waits for the owner rather than
    merging, and a review older than the head commit reviewed older code, so a push after a clean
    review re-opens this condition."""
    bot = [c for c in (comments or [])
           if _get(c, "user", "login") == REVIEW_BOT_LOGIN
           and _get(c, "user", "type") == REVIEW_BOT_TYPE]
    if not bot:
        return WAITING, "no %s review comment yet" % REVIEW_BOT_LOGIN
    bot.sort(key=lambda c: str(c.get("updated_at") or c.get("created_at") or ""))
    newest = bot[-1]
    posted = _ts(newest.get("updated_at") or newest.get("created_at"))
    if head_time is not None and posted is not None and posted < head_time:
        return WAITING, "the newest review (%s) is older than the head commit (%s)" % (
            posted.isoformat(), head_time.isoformat())
    summary = None
    for line in (newest.get("body") or "").splitlines():
        found = REVIEW_SUMMARY_RE.match(line.strip())
        if found:
            summary = found
    if summary is None:
        return WAITING, "the newest %s comment has no 'Important: <n> | Nits: <m>' line" % REVIEW_BOT_LOGIN
    important = int(summary.group(1))
    if important:
        return REFUSED, "the review reports Important: %d" % important
    return OK, "review reports Important: 0 | Nits: %s" % summary.group(2)


def check_cool_off(runs, require_checks, cool_off_hours, now):
    """8. `cool_off_hours` have passed since the newest required run finished."""
    if not cool_off_hours:
        return OK, "no cool-off configured"
    stamps = [_ts(r.get("updated_at")) for r in (runs or []) if r.get("name") in require_checks]
    stamps = [s for s in stamps if s is not None]
    if not stamps:
        return WAITING, "no required run has an updated_at to measure the cool-off from"
    newest = max(stamps)
    ready = newest + timedelta(hours=cool_off_hours)
    if now < ready:
        return WAITING, "cool-off of %sh ends at %s" % (cool_off_hours, ready.isoformat())
    return OK, "cool-off of %sh elapsed since %s" % (cool_off_hours, newest.isoformat())


def merge_comment_body(handle, grant_sha):
    """The comment left on the merged pull request: who granted the delegation, and where."""
    return ("merged under delegation granted by %s in %s\n\n---\n"
            "_Generated by the delegated-merge workflow_" % (handle, grant_sha))


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


class Run(object):
    """Prints one line per condition and remembers the first non-`ok` verdict."""

    def __init__(self, dry_run, stream=None):
        self.dry_run = dry_run
        self.stream = stream or sys.stdout
        self.first_bad = None

    def record(self, name, result):
        verdict, detail = result
        self.stream.write(u"CONDITION %s: %s — %s\n" % (name, verdict, detail))
        if verdict != OK and self.first_bad is None:
            self.first_bad = (name, verdict, detail)
        return verdict == OK

    def keep_going(self, ok):
        """Stop at the first refusal; under --dry-run evaluate everything still evaluable."""
        return ok or self.dry_run

    def _code(self):
        """0 on a merge or a wait, 1 on a refusal -- with `policy` the documented exception:
        delegated merging being off is the closed state, not a failed run."""
        if self.first_bad is None:
            return 0
        name, verdict, _ = self.first_bad
        if verdict == WAITING or name == "policy":
            return 0
        return 1

    def finish(self, merged=None):
        if self.dry_run:
            if self.first_bad is None:
                verdict = "would merge #%s" % merged if merged else "all conditions ok"
            else:
                verdict = "%s: %s" % (self.first_bad[1], self.first_bad[0])
            self.stream.write("DELEGATED-MERGE: dry-run (%s)\n" % verdict)
            return self._code()
        if self.first_bad is None:
            self.stream.write("DELEGATED-MERGE: merged %s\n" % merged)
            return 0
        self.stream.write("DELEGATED-MERGE: %s (%s)\n" % (self.first_bad[1], self.first_bad[0]))
        return self._code()


def _decode_contents(payload):
    """The text of a `contents/` response (base64), or None."""
    if not isinstance(payload, dict) or payload.get("encoding") != "base64":
        return None
    try:
        return base64.b64decode(payload.get("content") or "").decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None


def _grant_commit(repo, slug, head_sha):
    """The commit that wrote the grant -- the newest whose patch adds `mode: delegated` -- as
    (commit_detail, exact). The fallback to the newest commit touching the file keeps a squashed
    history from reading as "no grant"; the detail then says which commit was judged."""
    path = "work/%s/intent.md" % slug
    listed = items(gh_api("GET", "repos/%s/commits?path=%s&sha=%s&per_page=20" % (repo, path, head_sha)))
    newest = None
    for entry in listed:  # the commits endpoint is newest first
        detail = gh_api("GET", "repos/%s/commits/%s" % (repo, entry.get("sha")))
        if newest is None:
            newest = detail
        if commit_adds_grant(detail, path):
            return detail, True
    return newest, False


def run(event, policy, config, approvers_file, dry_run=False, now=None, stream=None):
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
    ok = out.record("pull-request", check_pull_request(pulls, head_sha, prefixes, default_branch))
    pr = pick_pr(pulls, head_sha)
    if not out.keep_going(ok) or pr is None:
        return out.finish()
    number = pr.get("number")
    slug = work_item_slug(pr.get("body"))

    required = policy.merge.get("require_checks") or []
    runs = items(gh_api("GET", "repos/%s/actions/runs?head_sha=%s&per_page=100" % (repo, head_sha)),
                 "workflow_runs")
    checks_result = check_required_runs(runs, required)
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
        contents = gh_api("GET", "repos/%s/contents/work/%s/intent.md?ref=%s" % (repo, slug, head_sha))
        text = _decode_contents(contents)
        front = chain.front_matter_text(text) if text is not None else None
        grant_result = check_grant_front_matter(front, policy)
        if grant_result[0] == OK:
            grant_handle = (front.get("delegated-by") or "").strip()
            detail, exact = _grant_commit(repo, slug, head_sha)
            grant_sha = (detail or {}).get("sha") or ""
            grant_result = check_grant_commit(detail, approvers_file, exact=exact,
                                              expected_handle=grant_handle)
        ok = out.record("grant", grant_result)
        if not out.keep_going(ok):
            return out.finish()

    locked = list(config.get("PROTECTED_PATHS") or []) + \
        list(config.get("RELEASE_GATED_PATHS") or []) + list(policy.locked_paths)
    files = items(gh_api("GET", "repos/%s/pulls/%s/files?per_page=100" % (repo, number)))
    ok = out.record("locked-paths", check_locked_paths(files, locked))
    if not out.keep_going(ok):
        return out.finish()

    if policy.merge.get("require_review"):
        head_time = _ts(_get(wf, "head_commit", "timestamp"))
        if head_time is None:
            head_time = _ts(_get(gh_api("GET", "repos/%s/commits/%s" % (repo, head_sha)),
                                 "commit", "committer", "date"))
        comments = items(gh_api("GET", "repos/%s/issues/%s/comments?per_page=100" % (repo, number)))
        ok = out.record("review", check_review(comments, head_time))
        if not out.keep_going(ok):
            return out.finish()

    ok = out.record("cool-off",
                    check_cool_off(runs, required, policy.merge.get("cool_off_hours") or 0, now))
    if not out.keep_going(ok):
        return out.finish()

    if dry_run:
        return out.finish(merged=number)

    label = _get(pr, "head", "label") or _get(pr, "head", "ref") or ""
    try:
        gh_api("PUT", "repos/%s/pulls/%s/merge" % (repo, number), {
            "sha": head_sha,
            "merge_method": policy.merge.get("method"),
            "commit_title": "Merge pull request #%s from %s (delegated)" % (number, label),
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

    ref = _get(pr, "head", "ref") or ""
    try:
        gh_api("DELETE", "repos/%s/git/refs/heads/%s" % (repo, ref))
    except MergeError as exc:  # a protected or already-deleted branch is not a merge failure
        out.stream.write("note: could not delete %s: %s\n" % (ref, exc))
    gh_api("POST", "repos/%s/issues/%s/comments" % (repo, number),
           {"body": merge_comment_body(grant_handle, grant_sha)})
    return out.finish(merged="#%s %s" % (number, head_sha))


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
        return run(event, policy, config, approvers_file, dry_run=args.dry_run)
    except MergeError as exc:
        print("GitHub call failed: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
