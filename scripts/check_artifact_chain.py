#!/usr/bin/env python3
"""Fail a PR whose artifact chain is broken.

Two modes, chosen from the diff against --base:
  in-progress  every changed path is under work/ (an artifact-only PR, or no diff at all): the chain
               is checked as far as it exists. intent.md must exist; spec.md may exist only once
               intent.md is approved, plan.md only once spec.md is; every status is one of
               draft | in-review | approved | superseded; log.md exists. This is what lets a work
               item be opened and approved one stage per PR, as docs/sdlc/README.md prescribes.
  strict       anything else changed: the whole chain must be approved (the checks below).

Checks, for the work item named by --slug (or .sdlc/active):
  1. intent.md, spec.md, plan.md exist and each has status: approved with an approved-by value
     (strict mode; in-progress mode requires approved-by only on approved artifacts).
  2. When an artifact is approved, its approved-by handle is a valid approver for that artifact
     type (scripts/approvers.py) and work/<slug>/log.md carries a matching
     "<artifact> | ... -> approved | <actor> | ..." entry (scripts/log_ledger.py). Pass
     --no-approvers to skip this pair of checks (for early adopters without approvers.yaml/log.md).
  3. Every changed file (vs --base) outside work/, docs/, evals/, monitoring/, knowledge/ matches
     a glob in plan.md's "## Files" list.
  4. Files under RELEASE_GATED_PATHS are listed in plan.md's "## Release-gated" section with a human owner.
Exit 0 on success, 1 on any failure. Output is meant to be pasted into a PR comment.

Note: `--base HEAD` (the default when there is no `origin/main` to diff against, e.g. a local
clone with no remote configured) yields an empty diff, so check 3/4 pass trivially and only
checks 1-2 are exercised locally. CI passes `--base origin/<base_ref>` so the changed-file
checks run against the PR's real diff.
"""
import argparse, fnmatch, os, re, subprocess, sys
from datetime import datetime, timezone

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or "."
# evals/ is deliberately NOT exempt: run_evals.sh executes each case's `check:` block as shell in CI,
# so a new case must appear in the approved plan's file list (security review, finding 4).
EXEMPT = ("work/", "docs/", "monitoring/", "knowledge/", "CLAUDE.md", "REVIEW.md", "README.md")
CHAIN = ("intent.md", "spec.md", "plan.md")
STATUSES = ("draft", "in-review", "approved", "superseded")

def front_matter_text(text):
    fm = {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return fm
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
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


def is_agent_identity(author_name, author_email, av):
    """True when a commit author looks like an agent: a never-approve handle or an agent email."""
    handle = av.normalize(author_name) if hasattr(av, "normalize") else author_name.casefold()
    never = {str(x).casefold() for x in getattr(av, "never_approve", [])}
    if handle in never:
        return True
    email = (author_email or "").casefold()
    return any(re.search(p, email) for p in AGENT_EMAIL_PATTERNS)


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
    slug = a.slug or open(os.path.join(ROOT, ".sdlc", "active")).read().strip()
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
    # Artifact-only means *this* item's artifacts (plus the generated top-level index): a PR that
    # touches another item's work/<other>/ while labelled with this slug is mislabelled, and gets the
    # strict check. An empty diff (`--base HEAD`, a local self-check) validates what exists.
    in_progress = all(p == "work/index.md" or p.startswith(f"work/{slug}/") for p in changed_all)
    if in_progress:
        notes.append(
            f"mode: in-progress -- the diff touches only work/{slug}/, so the chain is checked as far "
            "as it exists; any other path in the diff needs the whole chain approved"
        )

    fms = {name: front_matter(os.path.join(wd, name)) for name in CHAIN}
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
                if prev_status != "approved":
                    errors.append(
                        f"work/{slug}/{name} exists but work/{slug}/{prev} is '{prev_status}', not "
                        f"'approved': one stage at a time -- a human approves each artifact before the next is started"
                    )
            if status == "approved" and not fm.get("approved-by"):
                errors.append(f"work/{slug}/{name} is approved but has no approved-by")
            if status != "approved" and fm.get("approved-by"):
                errors.append(
                    f"work/{slug}/{name} has approved-by '{fm.get('approved-by')}' but status '{status}'; "
                    f"scripts/approve.py sets both together"
                )
        else:
            if status != "approved":
                errors.append(f"work/{slug}/{name} status is '{status}', must be 'approved'")
            if not fm.get("approved-by"):
                errors.append(f"work/{slug}/{name} has no approved-by")

        if status == "approved" and not a.no_approvers:
            any_approved = True
            approved_by = fm.get("approved-by", "")
            ok, reason = av.is_valid(name, approved_by)
            if not ok:
                errors.append(
                    f"work/{slug}/{name} approved-by '{approved_by}' is not valid: {reason}"
                )
            elif log_exists:
                target = av.normalize(approved_by)
                match = any(
                    e.artifact == name
                    and e.to_status == "approved"
                    and log_ledger.normalize(e.actor) == target
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
                            from_status="in-review",
                            to_status="approved",
                            actor=approved_by,
                            sha=sha,
                            note="",
                            lineno=0,
                        )
                    )
                    errors.append(
                        f"work/{slug}/log.md has no entry recording {name} approved by "
                        f"'{approved_by}'; append: {line}"
                    )
            # The commit that introduced `status: approved` must not be authored by an agent identity.
            # scripts/approve.py refuses to run inside an agent session, but an environment variable is
            # not a gate; the commit author is what CI can verify.
            # git pathspecs use forward slashes on every platform. os.path.join produced
            # `HEAD:work\<slug>\<file>` on Windows, so `git show` failed, head_text came
            # back empty and this whole approval-author check silently reported "not
            # committed yet" instead of running (roadmap item 19d).
            rel = "/".join(("work", slug, name))
            head_text = subprocess.run(["git", "show", f"HEAD:{rel}"], capture_output=True, text=True, cwd=ROOT).stdout
            who = ""
            if front_matter_text(head_text).get("status") == "approved":
                who = subprocess.run(
                    ["git", "log", "-n1", "--format=%an%x00%ae", "-S", "status: approved", "--", rel],
                    capture_output=True, text=True, cwd=ROOT,
                ).stdout.strip()
            if not who:
                notes.append(f"work/{slug}/{name}: approval not committed yet (author check skipped)")
            else:
                an, _, ae = who.partition("\x00")
                if is_agent_identity(an, ae, av):
                    errors.append(
                        f"work/{slug}/{name}: the commit that set status: approved is authored by an agent "
                        f"identity ({an} <{ae}>); a human must approve and commit"
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
                errors.append(f"{p} changed but is not listed under '## Files' in work/{slug}/plan.md (update the plan in this PR)")
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
