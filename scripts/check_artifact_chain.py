#!/usr/bin/env python3
"""Fail a PR whose artifact chain is broken.

Two modes, chosen from the diff against --base:
  in-progress  every changed path is this item's own (work/<slug>/, the generated work/index.md, or
               .sdlc/active when it now names <slug>), or there is no diff at all: the chain is
               checked as far as it exists. intent.md must exist; spec.md may exist only once
               intent.md is approved, plan.md only once spec.md is; every status is one of
               draft | in-review | approved | delegated | superseded; approved-by only on
               approved, delegated or superseded artifacts; log.md exists. This is what lets a
               work item be opened, approved one stage per PR, activated, and finally
               superseded, as docs/sdlc/README.md prescribes.
  strict       anything else changed: the whole chain must be approved, or signed `delegated`
               under a valid grant (the checks below).

Checks, for the work item named by --slug (or .sdlc/active):
  1. intent.md, spec.md, plan.md exist and each has status: approved with an approved-by value
     (strict mode; in-progress mode requires approved-by only on approved artifacts).
  2. When an artifact is approved, its approved-by handle is a valid approver for that artifact
     type (scripts/approvers.py) and work/<slug>/log.md carries a matching
     "<artifact> | ... -> approved | <actor> | ..." entry (scripts/log_ledger.py). Pass
     --no-approvers to skip this pair of checks (for early adopters without approvers.yaml/log.md).
  3. Every changed file (vs --base) outside work/, docs/, evals/, monitoring/, knowledge/ matches
     a glob in plan.md's "## Files that change" list.
  4. Files under RELEASE_GATED_PATHS are listed in plan.md's "## Release-gated" section with a human owner.
  5. Whenever any artifact is `delegated` -- an agent's signature rather than a human's approval --
     the grant behind it holds (intent.md approved by a human, `mode: delegated`, a risk class the
     policy delegates, a grant commit no agent authored), each signature is by an agent the policy
     lists on an artifact the policy lists and is recorded in log.md, every re-signature has a
     consensus record under work/<slug>/revisions/, and the item is under the deviation cap. The
     policy is scripts/delegation.py's `.sdlc/delegation.yaml`; a missing one closes delegated mode
     (work/delegated-mode R-4, R-5).
Exit 0 on success, 1 on any failure. Output is meant to be pasted into a PR comment.

Note: `--base HEAD` (the default when there is no `origin/main` to diff against, e.g. a local
clone with no remote configured) yields an empty diff, so check 3/4 pass trivially and only
checks 1-2 are exercised locally. CI passes `--base origin/<base_ref>` so the changed-file
checks run against the PR's real diff.
"""
import argparse, fnmatch, json, os, re, subprocess, sys
from datetime import datetime, timezone

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or "."
# evals/ is deliberately NOT exempt: run_evals.sh executes each case's `check:` block as shell in CI,
# so a new case must appear in the approved plan's file list (security review, finding 4).
EXEMPT = ("work/", "docs/", "monitoring/", "knowledge/", "CLAUDE.md", "REVIEW.md", "README.md")
CHAIN = ("intent.md", "spec.md", "plan.md")
# `delegated` sits where an approval would: an agent signed it under a grant a human gave on
# intent.md, which is why it is a word of its own rather than `approved` with an agent handle
# (work/delegated-mode R-2, D-a).
STATUSES = ("draft", "in-review", "approved", "delegated", "superseded")

def _fm_value(raw):
    """Clean one front-matter value the way YAML reads it: a value that is only a comment is
    empty; a trailing ` #...` (whitespace, then `#`) is a comment and is dropped, so a `#` with no
    whitespace before it -- a URL anchor -- survives; matching surrounding quotes are stripped;
    `strip()` also drops a stray `\r` from a CRLF checkout."""
    v = raw.strip()
    if v.startswith("#"):
        return ""
    # A quoted value is taken whole, comment or not: `title: "Fix #12 crash"   # note` is the
    # spec's answer (C2) for a value that needs ` #`. The quote check therefore runs first.
    if v[:1] in ("\"", "'"):
        end = v.find(v[0], 1)
        if end != -1:
            return v[1:end].strip()
    return re.split(r"\s+#", v, 1)[0].rstrip()

def front_matter_text(text):
    """Parse the leading `---` block into a dict. Every Python reader in scripts/ (approve.py,
    gen_index.py, gen_context_files.py, check_okf.py, check_plugin_manifest.py) goes through this
    one function, so a `# comment` line is never a key and a `value   # note` is never a value
    for any of them (work/front-matter, spec R-1)."""
    fm = {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return fm
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.lstrip().startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = _fm_value(v)
    return fm

def front_matter(path):
    try:
        with open(path, encoding="utf-8") as f:
            return front_matter_text(f.read())
    except FileNotFoundError:
        return None

def section(path, title):
    out, on = [], False
    for line in open(path, encoding="utf-8"):
        if line.startswith("## "):
            on = line[3:].strip().lower().startswith(title.lower())
            continue
        if on and line.lstrip().startswith(("-", "*")):
            item = line.lstrip()[1:].strip()
            item = item.split("—")[0].split(" - ")[0].strip().strip("`")
            if item:
                out.append(item)
    return out

def config():
    cfg = {}
    with open(os.path.join(ROOT, ".sdlc", "config.env"), encoding="utf-8") as f:
        for line in f:
            m = re.match(r'^([A-Z_]+)="(.*)"\s*$', line)
            if m:
                cfg[m.group(1)] = m.group(2).split()
    return cfg

AGENT_EMAIL_PATTERNS = (r"@anthropic\.com$", r"\[bot\]@", r"^noreply@")

# The one workflow whose runs may stand as an approval. A trailer naming a run of any
# other workflow is refused, not merely unverified (work/approve-by-dispatch R-6).
DISPATCH_WORKFLOW_PATH = ".github/workflows/approve.yml"

# approve.yml's `run-name`. Parsed rather than substring-matched so a blank slug segment is
# distinguishable from a slug that simply differs: the first falls back to .sdlc/active at the
# approval's parent, the second is a refusal. test_check_workflow_permissions.py asserts the
# workflow's own run-name still matches this, so a format change breaks loudly rather than
# silently turning the slug binding off.
RUN_NAME_RE = re.compile(
    r"^approve (?P<artifact>\S+) \((?P<mode>\w+)\) on (?P<slug>\S*) by @(?P<actor>\S+)\s*$")

# A revision record's reviewer sections and their verdicts (work/delegated-mode R-5, D4).
# docs/sdlc/templates/revision.md writes `## Reviewer: <role> (<model>)`; a `###` heading is read
# the same way, so a record that nests its reviewers under one `## Reviewers` heading still counts.
REVIEWER_RE = re.compile(r"^#{2,3} +Reviewer\b")
VERDICT_RE = re.compile(r"^\s*verdict:\s*(\S+)", re.IGNORECASE)
REVISION_NOTE_RE = re.compile(r"^revision (\d+):")


def is_agent_identity(author_name, author_email, av):
    """True when a commit author looks like an agent: a never-approve handle or an agent email."""
    handle = av.normalize(author_name) if hasattr(av, "normalize") else author_name.casefold()
    never = {str(x).casefold() for x in getattr(av, "never_approve", [])}
    if handle in never:
        return True
    email = (author_email or "").casefold()
    return any(re.search(p, email) for p in AGENT_EMAIL_PATTERNS)


APPROVED_RUN_RE = re.compile(r"^Approved-Run:\s*(\d+)\s*$", re.MULTILINE)
APPROVED_ACTOR_RE = re.compile(r"^Approved-Actor:\s*(\S+)\s*$", re.MULTILINE)


def dispatch_attestation(commit_sha):
    """(run_id, actor) from a commit's Approved-Run / Approved-Actor trailers, or None.

    .github/workflows/approve.yml writes both when an approval was made by pressing Run in the
    Actions tab. Their presence is what selects the trailer route below; their *truth* is checked
    against the Actions API by verify_dispatch_run, never taken from the message alone
    (work/approve-by-dispatch R-5).
    """
    body = subprocess.run(["git", "log", "-n1", "--format=%B", commit_sha],
                          capture_output=True, text=True, cwd=ROOT).stdout
    run = APPROVED_RUN_RE.search(body or "")
    actor = APPROVED_ACTOR_RE.search(body or "")
    if not run or not actor:
        return None
    return run.group(1), actor.group(1)


def verify_dispatch_run(run_id, actor, slug=None, artifact=None, commit_sha=None):
    """(True, detail) when the Actions API confirms the run; (False, reason) when it contradicts it;
    (None, reason) when there is no token to ask with.

    The run record is the anchor of the whole dispatch route: `actor.login` is set by GitHub when
    the run starts and nothing inside the run can change it, so a commit trailer that matches a
    successful workflow_dispatch run of approve.yml really was caused by that person pressing Run.
    Four fields must all agree -- the event, the workflow path, the conclusion and the actor --
    because any one of them alone could be satisfied by a different run (R-6).

    The run must also be *this* decision's run. Run ids and actors are public in the Actions tab, so
    without binding the run to the slug and the artifact, any past successful approval by the right
    person could be cited as the attestation for a different one: forge a commit approving anything,
    quote a real run id, and the four fields above all agree. `run-name` carries both (R-1), so both
    are checked here, exactly as delegated_merge.py's route B checks them for a grant. Found by the
    security pass on pull request 51.
    """
    if not (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")):
        return None, "no GH_TOKEN/GITHUB_TOKEN; the dispatch trailer was accepted on the author rule alone"
    repo = os.environ.get("GITHUB_REPOSITORY") or _repo_slug()
    if not repo:
        return None, "cannot determine the repository; dispatch attestation skipped"
    r = subprocess.run(["gh", "api", f"repos/{repo}/actions/runs/{run_id}"],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        return False, f"run {run_id} could not be read from {repo}: {r.stderr.strip()[:200]}"
    try:
        run = json.loads(r.stdout)
    except ValueError:
        return False, f"run {run_id} returned unparseable JSON"
    checks = (
        ("event", run.get("event"), "workflow_dispatch"),
        ("path", run.get("path"), DISPATCH_WORKFLOW_PATH),
        ("conclusion", run.get("conclusion"), "success"),
        ("actor", (run.get("actor") or {}).get("login"), actor),
    )
    for field, got, want in checks:
        if (got or "").casefold() != (want or "").casefold():
            return False, f"run {run_id} {field} is {got!r}, expected {want!r}"
    title = run.get("display_title") or run.get("name") or ""
    if artifact and artifact not in title:
        return False, f"run {run_id} run-name {title!r} does not name {artifact!r}"
    if slug:
        named = RUN_NAME_RE.match(title)
        if named and named.group("slug"):
            if named.group("slug") != slug:
                return False, (f"run {run_id} run-name {title!r} names slug "
                               f"{named.group('slug')!r}, not {slug!r}")
        else:
            # A blank `slug` input means "whatever .sdlc/active names on this ref" (R-1), and
            # run-name is evaluated from the raw input before any step runs -- so a blank-slug
            # dispatch has no slug segment for the check above to match, and requiring one would
            # refuse every supervised approval made the documented way (pr-review on pull request
            # 51). The run's own resolution is still reproducible from git: `.sdlc/active` at the
            # approval commit's parent is the file the run read. That is a fact, not a guess, so
            # the binding holds without making the owner type a slug.
            resolved = _active_at_parent(commit_sha) if commit_sha else None
            if resolved is None:
                return False, (f"run {run_id} run-name {title!r} names no slug and .sdlc/active "
                               f"could not be read at the approval's parent")
            if resolved != slug:
                return False, (f"run {run_id} run-name {title!r} names no slug, and .sdlc/active "
                               f"at the approval's parent was {resolved!r}, not {slug!r}")
    return True, (f"run {run_id} verified: workflow_dispatch of {DISPATCH_WORKFLOW_PATH} by {actor}"
                  f" for {slug or '?'}/{artifact or '?'}")


def _active_at_parent(commit_sha):
    """`.sdlc/active` as it stood in the commit's first parent, or None if unreadable.

    The parent is the dispatch ref's tip at the moment the run checked it out, so this is exactly
    the value the run's own "Resolve the slug" step read.
    """
    r = subprocess.run(["git", "show", f"{commit_sha}^:.sdlc/active"],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        return None
    return r.stdout.strip() or None


def _repo_slug():
    """`owner/name` from the origin remote, for the Actions API call."""
    url = subprocess.run(["git", "remote", "get-url", "origin"],
                         capture_output=True, text=True, cwd=ROOT).stdout.strip()
    m = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?$", url)
    return m.group(1) if m else ""


def _active_slug():
    """The slug in .sdlc/active, or "" when the file is missing or empty."""
    try:
        with open(os.path.join(ROOT, ".sdlc", "active"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _reviewer_verdicts(path):
    """The verdict of each `## Reviewer:` section of a revision record, in file order.

    A section with no `verdict:` line yields None, which counts as neither `revise` nor `keep`: an
    unfinished record is too few reviewers, never a silent pass (work/delegated-mode R-5).
    """
    verdicts = []
    inside = False
    with open(path, encoding="utf-8") as f:
        for line in f:
            if REVIEWER_RE.match(line):
                verdicts.append(None)
                inside = True
                continue
            if line.startswith("#"):
                inside = False
                continue
            m = VERDICT_RE.match(line)
            if inside and m and verdicts[-1] is None:
                verdicts[-1] = m.group(1).strip().casefold()
    return verdicts


def check_grant(slug, wd, policy, av, notes, errors):
    """Validate the grant that every `delegated` signature in this item stands on.

    A signature is worth exactly what the grant behind it is worth, so this runs in both modes as
    soon as any artifact is `delegated` (work/delegated-mode R-4): intent.md is approved by a human
    -- never `delegated` itself, or the agent would be signing the file that carries its own
    permission (spec D-b) -- it says `mode: delegated`, its risk class is one the policy delegates,
    and the commit that added `mode: delegated` is not an agent identity.
    """
    if not policy.exists:
        errors.append(
            f"work/{slug}: an artifact is 'delegated' but there is no delegation policy at "
            f"{policy.path}; a signature with no policy behind it is nobody's decision"
        )
        return
    if not policy.enabled:
        errors.append(
            f"work/{slug}: an artifact is 'delegated' but delegated mode is off in {policy.path}"
        )
        return
    fm = front_matter(os.path.join(wd, "intent.md"))
    if fm is None:
        errors.append(f"work/{slug}/intent.md is missing; it is the file that carries the grant")
        return
    status = fm.get("status")
    if status == "delegated":
        errors.append(
            f"work/{slug}/intent.md is 'delegated'; the intent carries the grant, so a human always "
            f"signs it -- an agent never widens its own permission"
        )
    elif status != "approved":
        errors.append(
            f"work/{slug}/intent.md is '{status}', not 'approved': a delegated signature needs a "
            f"human-approved intent behind it"
        )
    granted_by = fm.get("approved-by", "")
    ok, reason = av.is_valid("intent.md", granted_by)
    if not ok:
        errors.append(
            f"work/{slug}/intent.md approved-by '{granted_by}' cannot grant delegated mode: {reason}"
        )
    mode = fm.get("mode") or "supervised"
    if mode != "delegated":
        errors.append(
            f"work/{slug}/intent.md has mode '{mode}', so this item is supervised; a human grants "
            f"delegated mode on the intent before an agent signs anything"
        )
    ok, reason = policy.risk_ok(fm.get("risk-class", ""))
    if not ok:
        errors.append(f"work/{slug}/intent.md: {reason}")
    # The grant is a human act, checked the way an approval is: `-G '^mode: delegated$'` finds the
    # commit that added that exact line, and the HEAD guard keeps a commit that later removed it
    # from being read as the grant. Not committed yet is a note, not a failure, as above.
    rel = "/".join(("work", slug, "intent.md"))
    head_text = subprocess.run(["git", "show", f"HEAD:{rel}"], capture_output=True, text=True, cwd=ROOT).stdout
    who = ""
    if front_matter_text(head_text).get("mode") == "delegated":
        who = subprocess.run(
            ["git", "log", "-n1", "--format=%an%x00%ae", "-G", "^mode: delegated$", "--", rel],
            capture_output=True, text=True, cwd=ROOT,
        ).stdout.strip()
    if not who:
        notes.append(f"work/{slug}/intent.md: grant not committed yet (author check skipped)")
    else:
        an, _, ae = who.partition("\x00")
        if is_agent_identity(an, ae, av):
            errors.append(
                f"work/{slug}/intent.md: the commit that set mode: delegated is authored by an agent "
                f"identity ({an} <{ae}>); a human grants delegated mode and commits"
            )


def check_signature(slug, name, fm, policy, entries, log_exists, errors):
    """One `delegated` artifact: the policy lists it, the policy lists its signer, log.md records it.

    No commit-author check and no approvers.yaml role here: this signature is the agent's own act,
    and `.sdlc/approvers.yaml` lists `claude` under never-approve on purpose -- approving and
    signing are different acts, judged by different files (spec gotchas, D-a).
    """
    import log_ledger  # main() put scripts/ on sys.path before calling this

    signer = fm.get("approved-by", "")
    ok, reason = policy.may_sign_artifact(name)
    if not ok:
        errors.append(f"work/{slug}/{name} is 'delegated' but {reason}")
    ok, reason = policy.may_sign(signer)
    if not ok:
        errors.append(f"work/{slug}/{name} is signed by '{signer}', which may not sign: {reason}")
        return
    if not log_exists:
        return
    target = log_ledger.normalize(signer)
    if any(log_ledger.normalize(e.actor) == target for e in log_ledger.signatures(entries, name)):
        return
    sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT,
    ).stdout.strip()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = log_ledger.render(
        log_ledger.Entry(ts=ts, artifact=name, from_status="in-review", to_status="delegated",
                         actor=signer, sha=sha, note="", lineno=0)
    )
    errors.append(f"work/{slug}/log.md has no entry recording {name} signed by '{signer}'; append: {line}")


def check_revisions(slug, wd, name, policy, entries, errors):
    """Every signature after the first is a recorded last resort (work/delegated-mode R-5, D4).

    Re-signing means the agent changed a decision a signature or an approval already stood on, so
    the ledger line names `revision <n>:` and work/<slug>/revisions/<n>.md carries the reviewers who
    said `revise`. A `deviation:` line is not a re-decision -- it is an edit inside the approved
    plan, bounded by the policy's cap -- so check_deviations counts it and this does not.
    """
    import log_ledger

    sigs = log_ledger.signatures(entries, name)
    # A human approval anywhere in the artifact's ledger makes every signature a re-decision, whatever
    # the file's status says now: demoting an approved artifact to in-review passes the hook (the
    # accepted residual in human-only-approvals.md), so the ledger, not the front matter, is what
    # says a decision already stood (PR #43 security pass, finding 1).
    was_approved = bool(log_ledger.approvals(entries, name))
    resigns = [
        e for i, e in enumerate(sigs)
        if not e.note.strip().startswith("deviation:")
        and (i > 0 or was_approved or e.from_status in ("approved", "delegated"))
    ]
    if not resigns or policy.revisions == "free":
        return
    if policy.revisions == "never":
        errors.append(
            f"work/{slug}/{name} was signed again ({len(resigns)} time(s)) but {policy.path} says "
            f"revisions: never; that decision is the owner's"
        )
        return
    for e in resigns:
        m = REVISION_NOTE_RE.match(e.note.strip())
        if not m:
            errors.append(
                f"work/{slug}/log.md:{e.lineno}: re-signing {name} needs the note "
                f"'revision <n>: <why>' naming a record in work/{slug}/revisions/"
            )
            continue
        rel = f"work/{slug}/revisions/{m.group(1)}.md"
        path = os.path.join(wd, "revisions", f"{m.group(1)}.md")
        if not os.path.exists(path):
            errors.append(
                f"work/{slug}/log.md:{e.lineno} names revision {m.group(1)} but {rel} does not exist"
            )
            continue
        verdicts = _reviewer_verdicts(path)
        if "keep" in verdicts:
            errors.append(
                f"{rel}: a reviewer's verdict is 'keep'; a revision needs every reviewer to say "
                f"'revise' -- otherwise stop and call the owner back"
            )
            continue
        revise = verdicts.count("revise")
        if revise < policy.min_reviewers:
            errors.append(
                f"{rel} has {revise} '## Reviewer:' section(s) with 'verdict: revise'; "
                f"{policy.path} requires {policy.min_reviewers}"
            )


def check_deviations(slug, policy, entries, errors):
    """Deviations are ledger lines noted `deviation:`; the policy caps how many an item may
    accumulate before the plan itself has to be re-decided (work/delegated-mode R-5, D4)."""
    devs = [e for e in entries if e.note.strip().startswith("deviation:")]
    if len(devs) > policy.max_deviations:
        errors.append(
            f"work/{slug}/log.md records {len(devs)} deviation lines; {policy.path} allows "
            f"{policy.max_deviations} -- re-plan instead of deviating again"
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--slug")
    ap.add_argument(
        "--no-approvers",
        action="store_true",
        help="skip the approvers.yaml + log.md ledger checks (for early adopters without them)",
    )
    a = ap.parse_args()
    slug = a.slug or _active_slug()
    if not slug:
        # Before anything else, and in one line: with no slug there is no item to check, which is a
        # setup mistake rather than a broken chain (work/delegated-mode R-6).
        print("  FAIL: no active work item (.sdlc/active is empty; pass --slug or set it)")
        print("CHAIN: FAIL")
        sys.exit(1)
    wd = os.path.join(ROOT, "work", slug)
    errors, notes = [], []

    approvers = log_ledger = None
    av = None
    entries, malformed = [], []
    log_exists = False
    if not a.no_approvers:
        # Lazy import: approvers.py does `from check_artifact_chain import ROOT, config`, so
        # importing it at module load time here would be circular. By main() time this module
        # has already finished executing, so the lazy import resolves cleanly either way.
        here = os.path.dirname(os.path.abspath(__file__))
        if here not in sys.path:
            sys.path.insert(0, here)
        import approvers
        import log_ledger

        av = approvers.load()
        log_path = os.path.join(wd, "log.md")
        log_exists = os.path.exists(log_path)
        entries, malformed = log_ledger.parse(log_path)

    any_approved = False

    diff = subprocess.run(["git", "diff", "--name-only", f"{a.base}...HEAD"], capture_output=True, text=True, cwd=ROOT)
    changed_all = [p for p in diff.stdout.split() if p]
    # Artifact-only means *this* item's artifacts (plus the generated top-level index), and
    # .sdlc/active when the diff points it at this item -- activating an item is part of opening it.
    # A PR that touches another item's work/<other>/ while labelled with this slug is mislabelled,
    # and gets the strict check. An empty diff (`--base HEAD`, a local self-check) validates what exists.
    active_path = os.path.join(ROOT, ".sdlc", "active")
    active_now = open(active_path, encoding="utf-8").read().strip() if os.path.exists(active_path) else ""

    def own_artifact(p):
        if p == "work/index.md" or p.startswith(f"work/{slug}/"):
            return True
        return p == ".sdlc/active" and active_now == slug

    in_progress = all(own_artifact(p) for p in changed_all)
    if in_progress:
        notes.append(
            f"mode: in-progress -- the diff touches only work/{slug}/ (and .sdlc/active naming it), so the "
            "chain is checked as far as it exists; any other path in the diff needs the whole chain approved"
        )

    fms = {name: front_matter(os.path.join(wd, name)) for name in CHAIN}

    # One `delegated` artifact anywhere in the item -- incident.md included, which the chain loop
    # below does not walk -- puts the whole item under the delegation policy, in both modes
    # (work/delegated-mode R-4). Nothing reads the policy until then, so a repository that never
    # delegates needs no policy file at all.
    delegated = {
        name: fm
        for name, fm in list(fms.items()) + [("incident.md", front_matter(os.path.join(wd, "incident.md")))]
        if fm is not None and fm.get("status") == "delegated"
    }
    if delegated and not a.no_approvers:
        import delegation  # lazy for the same reason as approvers above: it imports this module

        try:
            policy = delegation.load()
        except ValueError as e:
            policy = None
            errors.append(f"malformed delegation policy: {e}")
        if policy is not None:
            check_grant(slug, wd, policy, av, notes, errors)
            if not log_exists:
                errors.append(f"work/{slug}/log.md is missing; every signature is recorded there")
            for name, fm in delegated.items():
                check_signature(slug, name, fm, policy, entries, log_exists, errors)
                check_revisions(slug, wd, name, policy, entries, errors)
            check_deviations(slug, policy, entries, errors)

    if in_progress and fms["intent.md"] is None:
        errors.append(f"work/{slug}/intent.md is missing; a work item starts with an intent")
    if in_progress and not a.no_approvers and not log_exists and any(fm is not None for fm in fms.values()):
        errors.append(f"work/{slug}/log.md is missing; every gate, including '(none) -> draft', is recorded there")

    for i, name in enumerate(CHAIN):
        fm = fms[name]
        if fm is None:
            if not in_progress:
                errors.append(f"work/{slug}/{name} is missing")
            continue
        status = fm.get("status")
        if status not in STATUSES:
            errors.append(f"work/{slug}/{name} status is '{status}', must be one of {', '.join(STATUSES)}")
        if in_progress:
            if i > 0:
                prev = CHAIN[i - 1]
                prev_status = (fms[prev] or {}).get("status", "missing")
                # 'superseded' counts like 'approved' here: it is what an approved artifact becomes when
                # the item is retired, so a retired chain must stay checkable (work/batch-b-followups R-3).
                # 'delegated' counts too: under a grant it is what the previous stage's gate looks like
                # (work/delegated-mode R-4); the grant itself is checked above.
                if prev_status not in ("approved", "superseded", "delegated"):
                    errors.append(
                        f"work/{slug}/{name} exists but work/{slug}/{prev} is '{prev_status}', not "
                        f"'approved', 'delegated' or 'superseded': one stage at a time -- each artifact "
                        f"is signed off before the next is started"
                    )
            if status in ("approved", "delegated") and not fm.get("approved-by"):
                errors.append(f"work/{slug}/{name} is {status} but has no approved-by")
            # A superseded artifact keeps the approved-by it earned; a delegated one names the agent
            # that signed it; a draft or in-review one has none.
            if status not in ("approved", "delegated", "superseded") and fm.get("approved-by"):
                errors.append(
                    f"work/{slug}/{name} has approved-by '{fm.get('approved-by')}' but status '{status}'; "
                    f"scripts/approve.py sets both together"
                )
        else:
            if status not in ("approved", "delegated"):
                errors.append(
                    f"work/{slug}/{name} status is '{status}', must be 'approved'"
                    f" (or 'delegated' under a valid grant)"
                )
            if not fm.get("approved-by"):
                errors.append(f"work/{slug}/{name} has no approved-by")

        # Approving and superseding are both human acts: the same approver, ledger and
        # commit-author checks apply to either status.
        if status in ("approved", "superseded") and not a.no_approvers:
            any_approved = True
            approved_by = fm.get("approved-by", "")
            ok, reason = av.is_valid(name, approved_by)
            if not ok:
                errors.append(
                    f"work/{slug}/{name} approved-by '{approved_by}' is not valid: {reason}"
                )
            elif log_exists:
                target = av.normalize(approved_by)
                if status == "approved":
                    match = any(
                        e.artifact == name
                        and e.to_status == "approved"
                        and log_ledger.normalize(e.actor) == target
                        for e in entries
                    )
                else:
                    # Whoever superseded it must hold the artifact's role; it need not be the
                    # original approver, whose handle stays in approved-by as history.
                    match = any(
                        e.artifact == name
                        and e.to_status == "superseded"
                        and av.is_valid(name, e.actor)[0]
                        for e in entries
                    )
                if not match:
                    sha = subprocess.run(
                        ["git", "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True, cwd=ROOT,
                    ).stdout.strip()
                    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    line = log_ledger.render(
                        log_ledger.Entry(
                            ts=ts,
                            artifact=name,
                            from_status="in-review" if status == "approved" else "approved",
                            to_status=status,
                            actor=approved_by,
                            sha=sha,
                            note="",
                            lineno=0,
                        )
                    )
                    who_did = f"approved by '{approved_by}'" if status == "approved" else "superseded by a valid approver"
                    errors.append(
                        f"work/{slug}/log.md has no entry recording {name} {who_did}; append: {line}"
                    )
            # The commit that introduced `status: approved` must not be authored by an agent identity.
            # `-G '^status: approved$'` finds the commit whose diff added or removed that exact line;
            # `-S` counted the phrase anywhere in the file, so a later agent commit that mentioned it
            # in prose was read as the approver (work/agent-evals R-5).
            # scripts/approve.py refuses to run inside an agent session, but an environment variable is
            # not a gate; the commit author is what CI can verify.
            # git pathspecs use forward slashes on every platform. os.path.join produced
            # `HEAD:work\<slug>\<file>` on Windows, so `git show` failed, head_text came
            # back empty and this whole approval-author check silently reported "not
            # committed yet" instead of running (roadmap item 19d).
            rel = "/".join(("work", slug, name))
            head_text = subprocess.run(["git", "show", f"HEAD:{rel}"], capture_output=True, text=True, cwd=ROOT).stdout
            who = ""
            if front_matter_text(head_text).get("status") == status:
                who = subprocess.run(
                    ["git", "log", "-n1", "--format=%H%x00%an%x00%ae", "-G", f"^status: {status}$", "--", rel],
                    capture_output=True, text=True, cwd=ROOT,
                ).stdout.strip()
            if not who:
                act = "approval" if status == "approved" else "supersession"
                notes.append(f"work/{slug}/{name}: {act} not committed yet (author check skipped)")
            else:
                sha, an, ae = (who.split("\x00") + ["", ""])[:3]
                attested = dispatch_attestation(sha)
                if attested:
                    # The trailer route: the decision was a tap in the Actions tab, and the run --
                    # not the commit -- says who made it. The deciding handle is the trailer's
                    # actor, which must be the handle the artifact names; then the run itself is
                    # checked, when there is a token to check it with (R-5, R-6).
                    run_id, actor = attested
                    if av.normalize(actor) != av.normalize(approved_by):
                        errors.append(
                            f"work/{slug}/{name}: the commit that set status: {status} carries "
                            f"Approved-Actor: {actor}, but the artifact says approved-by: "
                            f"{approved_by}; the run's actor is the deciding handle"
                        )
                    else:
                        ok, detail = verify_dispatch_run(run_id, actor, slug=slug, artifact=name,
                                                         commit_sha=sha)
                        notes.append(f"work/{slug}/{name}: {detail}")
                        if ok is False:
                            errors.append(f"work/{slug}/{name}: dispatch attestation failed: {detail}")
                        elif ok is None and is_agent_identity(an, ae, av):
                            # No token, so the trailer cannot be checked against the run. Fall back
                            # to the author rule -- what the spec means by "accepted on the author
                            # rule alone". Without this, an unverifiable trailer would be *better*
                            # than no trailer at all: any agent could write two lines into a commit
                            # message and skip the one check that applies with no token
                            # (security pass on pull request 51).
                            errors.append(
                                f"work/{slug}/{name}: the commit that set status: {status} carries an "
                                f"unverified dispatch trailer and is authored by an agent identity "
                                f"({an} <{ae}>); a human must set it and commit"
                            )
                elif is_agent_identity(an, ae, av):
                    errors.append(
                        f"work/{slug}/{name}: the commit that set status: {status} is authored by an agent "
                        f"identity ({an} <{ae}>); a human must set it and commit"
                    )

    if not a.no_approvers:
        if any_approved and not log_exists:
            errors.append(f"work/{slug}/log.md is missing; approvals must be recorded there")
        for lineno, raw in malformed:
            notes.append(f"work/{slug}/log.md:{lineno}: malformed log line: {raw.strip()}")

    changed = [p for p in changed_all if not p.startswith(EXEMPT)]
    plan = os.path.join(wd, "plan.md")
    if os.path.exists(plan):
        allowed = section(plan, "Files")
        gated_listed = section(plan, "Release-gated")
        cfg = config()
        for p in changed:
            if not any(fnmatch.fnmatch(p, g) or p == g or p.startswith(g.rstrip("/") + "/") for g in allowed):
                errors.append(f"{p} changed but is not listed under '## Files that change' in work/{slug}/plan.md (update the plan in this PR)")
            if any(p == g or p.startswith(g + "/") for g in cfg.get("RELEASE_GATED_PATHS", [])):
                if not any(p.startswith(x.split()[0].rstrip("/")) for x in gated_listed):
                    errors.append(f"{p} is release-gated but not declared under '## Release-gated' in plan.md with a human owner")
                else:
                    notes.append(f"{p} is release-gated: requires the named owner's approval before merge")

    print(f"Artifact chain check for work item '{slug}' vs {a.base}")
    for n in notes: print(f"  note: {n}")
    for e in errors: print(f"  FAIL: {e}")
    print("CHAIN: " + ("FAIL" if errors else "PASS"))
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
