#!/usr/bin/env python3
"""Sign a work-item artifact as the agent: flip its front matter to `delegated` and record the gate in log.md.

Usage:
  scripts/sign.py <slug> <artifact>... [--note TEXT] [--revision revisions/<n>.md] [--dry-run]

  <artifact> is one of spec.md, plan.md, incident.md (or several). intent.md is never signable: it
                carries the grant, so an agent that could sign it could widen its own permission.
  --note TEXT   free text for the ledger line.
  --revision revisions/<n>.md
                re-sign an artifact that already carries a signature or a human approval, naming the
                consensus record under work/<slug>/revisions/ that justifies it. The ledger note
                becomes `revision <n>: <TEXT>`, which is what check_artifact_chain.py looks for.
  --dry-run     print what would change, write nothing.

What it does, per artifact: sets `status: delegated`, `approved-by: HANDLE`, `approved-on: <today
UTC>` in the YAML front matter, and appends `- <ts> | <artifact> | <old> -> delegated | HANDLE |
<sha> | <note>` to work/<slug>/log.md (creating it from the template shape if absent). It then
prints the commit command; the session commits. Nothing is committed by this script.

HANDLE comes from SDLC_AGENT_HANDLE (default `claude`) and must be an agent the policy lists; there
is no --as flag, because a signature is the identity the session actually runs under, never one it
picks. The grant is on the item's intent.md: `status: approved` by a human, `mode: delegated`, a risk
class the policy delegates. Everything else this script refuses -- a missing or disabled policy, an
unlisted handle, an unlisted artifact, a predecessor that no gate has passed, a re-signature with no
consensus record -- is the closed answer, so delegated mode stays off until the owner turns it on.

Stage order: spec.md is signed only once intent.md has passed its gate, plan.md only once spec.md
has (`approved`, `delegated` or `superseded`, on disk or earlier in the same call, which processes
several artifacts in chain order whatever order they are given in); incident.md has no predecessor.
A violation exits 1 naming the predecessor and its status, and writes nothing.

This is the mirror image of scripts/approve.py. That script is a human act and refuses to run inside
a Claude Code session; this one is an agent act and refuses to run outside one (exit 3 when
CLAUDECODE is unset) -- a human approves with scripts/approve.py from their own shell. Like that
refusal, this one is a courtesy, not a gate: the deterministic checks are
.claude/hooks/protect-approvals.sh (which judges the resulting front matter) and
scripts/check_artifact_chain.py (which re-checks the grant, the signature, the ledger line and every
revision record from the committed files). See work/delegated-mode (R-7, D3).
Exit codes: 0 ok, 1 usage/validation error, 3 refused (not an agent session).
"""
import argparse, os, re, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import delegation  # noqa: E402
import log_ledger  # noqa: E402
# set_front_matter, PREDECESSOR and git() are approve.py's, used verbatim so an approval and a
# signature write the same shape of front matter (importing it runs no CLAUDECODE check: that lives
# in its main(), not at module level).
from approve import PREDECESSOR, git, set_front_matter  # noqa: E402
# _reviewer_verdicts and REVISION_NOTE_RE are the chain check's, imported rather than re-implemented
# so sign.py judges a revision record exactly as CI will (work/delegated-mode R-5, D4).
from check_artifact_chain import REVISION_NOTE_RE, ROOT, _reviewer_verdicts, front_matter  # noqa: E402

ARTIFACTS = ("intent.md", "spec.md", "plan.md", "incident.md")
# What a predecessor's gate may look like: a human approval, an agent signature under this same
# grant, or the retired form of either (work/delegated-mode R-7, and the chain check's own rule).
GATED = ("approved", "delegated", "superseded")
REVISION_FILE_RE = re.compile(r"^(\d+)\.md$")
DEFAULT_HANDLE = "claude"


def fail(message):
    """Print one line on stderr and hand main() its exit code. Nothing has been written yet."""
    print(f"sign: {message}", file=sys.stderr)
    return 1


def resolve_revision(arg, slug, wd, policy):
    """Return (path, n) for --revision, or (None, reason) when the record cannot justify a re-sign.

    The record is read here exactly as check_artifact_chain.check_revisions will read it from the
    commit: every `## Reviewer:` section's verdict, a `keep` anywhere is a stop, and at least
    min_reviewers sections saying `revise`. `revisions: free` skips the verdicts (the policy says
    the record is not required at all; requiring the file to exist is the closed reading).
    """
    candidates = [arg] if os.path.isabs(arg) else [os.path.join(wd, arg), os.path.join(ROOT, arg)]
    path = next((p for p in candidates if os.path.exists(p)), candidates[0])
    m = REVISION_FILE_RE.match(os.path.basename(path))
    if not m:
        return None, (f"--revision must name work/{slug}/revisions/<n>.md with <n> a number, "
                      f"not '{arg}'")
    n = m.group(1)
    rel = f"work/{slug}/revisions/{n}.md"
    if not os.path.exists(path):
        return None, (f"--revision names revision {n} but {rel} does not exist; write it from "
                      f"docs/sdlc/templates/revision.md first")
    if policy.revisions != "consensus":
        return (path, n), None
    verdicts = _reviewer_verdicts(path)
    if "keep" in verdicts:
        return None, (f"{rel}: a reviewer's verdict is 'keep'; a revision needs every reviewer to "
                      f"say 'revise' -- stop here and call the owner back")
    revise = verdicts.count("revise")
    if revise < policy.min_reviewers:
        return None, (f"{rel} has {revise} '## Reviewer:' section(s) with 'verdict: revise'; "
                      f"{policy.path} requires {policy.min_reviewers}")
    return (path, n), None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("slug")
    ap.add_argument("artifacts", nargs="+", choices=ARTIFACTS, metavar="artifact")
    ap.add_argument("--note", default="")
    ap.add_argument("--revision", metavar="revisions/<n>.md",
                    help="the consensus record justifying a re-signature")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    if not os.environ.get("CLAUDECODE"):
        print("sign: refused — sign.py runs only inside an agent session (CLAUDECODE is not set); "
              "a human approves with scripts/approve.py from their own shell.", file=sys.stderr)
        return 3

    handle = (os.environ.get("SDLC_AGENT_HANDLE") or DEFAULT_HANDLE).strip()
    wd = os.path.join(ROOT, "work", a.slug)
    if not os.path.isdir(wd):
        return fail(f"work/{a.slug} does not exist")

    try:
        policy = delegation.load()
    except ValueError as e:
        return fail(f"malformed delegation policy: {e}")
    ok, reason = policy.may_sign(handle)
    if not ok:
        hint = ("; copy docs/sdlc/templates/delegation.yaml to .sdlc/delegation.yaml -- the owner's "
                "commit, not the session's") if not policy.exists else ""
        return fail(f"'{handle}' may not sign: {reason}{hint}")

    # The grant. It lives on intent.md and nowhere else, so an agent can never widen its own
    # permission by signing something (work/delegated-mode D-b).
    intent = front_matter(os.path.join(wd, "intent.md"))
    if intent is None:
        return fail(f"work/{a.slug}/intent.md is missing; it is the file that carries the grant")
    intent_status = intent.get("status") or "draft"
    if intent_status != "approved":
        return fail(f"work/{a.slug}/intent.md is '{intent_status}', not 'approved': a delegated "
                    f"signature needs a human-approved intent behind it")
    mode = intent.get("mode") or "supervised"
    if mode != "delegated":
        return fail(f"work/{a.slug}/intent.md has mode '{mode}', so this item is supervised; a human "
                    f"grants delegated mode on the intent (scripts/approve.py --delegate) before an "
                    f"agent signs anything")
    ok, reason = policy.risk_ok(intent.get("risk-class", ""))
    if not ok:
        # check_artifact_chain.py checks the grant's risk class in both modes, so a signature
        # written now would fail CI; refusing here is the same answer given earlier.
        return fail(f"work/{a.slug}/intent.md: {reason}; the grant is invalid, so nothing is signed")

    revision = None
    if a.revision:
        revision, reason = resolve_revision(a.revision, a.slug, wd, policy)
        if revision is None:
            return fail(reason)

    note = a.note.strip()
    if "|" in note or "\n" in note:
        # A ledger line is pipe-separated and one line long; log_ledger.parse would call the result
        # malformed, and a malformed line is a signature nobody can read.
        return fail("--note may not contain '|' or a line break: it is the last field of a "
                    "pipe-separated ledger line")
    if revision:
        # The note is the only link from the ledger line to its record, so it is written in the
        # exact shape check_artifact_chain.check_revisions parses back, and checked against that
        # same expression before anything is written.
        note = f"revision {revision[1]}:" + (f" {note}" if note else "")
        if not REVISION_NOTE_RE.match(note):
            return fail(f"the ledger note '{note}' is not the 'revision <n>: <why>' shape "
                        f"check_artifact_chain.py reads back")

    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    today = now.strftime("%Y-%m-%d")
    sha = git("rev-parse", "--short", "HEAD") or "0000000"

    # Validate everything first, in chain order, so a refusal writes nothing; then write.
    ordered = [n for n in ARTIFACTS if n in a.artifacts]
    signed_now = set()
    todo = []  # (name, path, old_status, new_text)
    for name in ordered:
        if name == "intent.md":
            return fail(f"work/{a.slug}/intent.md is never signable: it carries the grant, so a "
                        f"human approves it with scripts/approve.py -- an agent never signs the file "
                        f"that grants its own permission")
        ok, reason = policy.may_sign_artifact(name)
        if not ok:
            return fail(f"work/{a.slug}/{name}: {reason}")
        path = os.path.join(wd, name)
        fm = front_matter(path)
        if fm is None:
            return fail(f"work/{a.slug}/{name} is missing")
        prev = PREDECESSOR.get(name)
        if prev and prev not in signed_now:
            prev_fm = front_matter(os.path.join(wd, prev))
            prev_status = "missing" if prev_fm is None else (prev_fm.get("status") or "draft")
            if prev_status not in GATED:
                return fail(f"work/{a.slug}/{name} needs work/{a.slug}/{prev} approved, delegated or "
                            f"superseded first (it is '{prev_status}')")
        signed_now.add(name)
        old = fm.get("status", "draft") or "draft"
        if old in ("approved", "delegated"):
            if policy.revisions == "never":
                return fail(f"work/{a.slug}/{name} is already '{old}' and {policy.path} says "
                            f"revisions: never; re-deciding a signed artifact is the owner's call")
            if not revision:
                return fail(f"work/{a.slug}/{name} is already '{old}'; re-signing it needs "
                            f"--revision revisions/<n>.md naming the consensus record that says why")
        elif revision:
            print(f"sign: warning: work/{a.slug}/{name} is '{old}', not a re-signature; --revision "
                  f"is for an artifact that already carries a signature or an approval",
                  file=sys.stderr)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        todo.append((name, path, old, set_front_matter(
            text, {"status": "delegated", "approved-by": handle, "approved-on": today})))

    changed, lines = [], []
    for name, path, old, new_text in todo:
        entry = log_ledger.Entry(ts=ts, artifact=name, from_status=old, to_status="delegated",
                                 actor=handle, sha=sha, note=note, lineno=0)
        line = log_ledger.render(entry)
        print(f"{'would sign' if a.dry_run else 'signed'}: work/{a.slug}/{name} "
              f"({old} -> delegated) by {handle}")
        print(f"  ledger: {line}")
        if not a.dry_run:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_text)
            lines.append(line)
        changed.append(name)

    if revision:
        print(f"  revision: work/{a.slug}/revisions/{revision[1]}.md")

    log_path = os.path.join(wd, "log.md")
    if lines:
        if not os.path.exists(log_path):
            header = (f"---\ntype: sdlc/log\nid: {a.slug}-log\ntitle: Gate ledger for {a.slug}\n"
                      f"description: Chronological record of stage transitions and approvals for this work item.\n"
                      f"timestamp: {ts}\n---\n# Log: {a.slug}\n\n"
                      "Format: `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>` "
                      "(append-only; parsed by scripts/log_ledger.py).\n\n")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(header)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    if changed and not a.dry_run:
        print("\nNext: review the diff, then commit:")
        print(f"  git add work/{a.slug} && git commit -m \"[{a.slug}] sign {' '.join(changed)}\"")
        print("  python3 scripts/check_artifact_chain.py --slug", a.slug, "--base origin/main")
    return 0


if __name__ == "__main__":
    sys.exit(main())
