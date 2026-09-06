#!/usr/bin/env python3
"""Approve a work-item artifact as a human: flip its front matter and record the gate in log.md.

Usage:
  scripts/approve.py <slug> <artifact>... [--as HANDLE] [--note TEXT] [--delegate] [--activate] [--dry-run]
                     [--from-dispatch RUN_ID]

  <artifact> is one of intent.md, spec.md, plan.md, incident.md (or several).
  --as HANDLE   GitHub handle recorded as approved-by (default: `git config sdlc.approver`; there is
                no fallback to user.name, a display name is not a handle); it must hold the
                artifact's role in .sdlc/approvers.yaml.
  --note TEXT   free text for the ledger line.
  --delegate    grant delegated mode on this item, with intent.md only: the agent may then sign the
                rest of the chain under its own handle (scripts/sign.py). Refused when the intent's
                `risk-class` is not one .sdlc/delegation.yaml delegates -- a missing policy file is
                the closed state, so the grant is refused there too.
  --activate    also point .sdlc/active at <slug>.
  --dry-run     print what would change, write nothing.
  --from-dispatch RUN_ID
                run inside `.github/workflows/approve.yml`'s workflow_dispatch run RUN_ID, where the
                human act was pressing Run and GitHub recorded the actor. Requires --as (the run's
                actor), and is refused with exit 3 unless GITHUB_ACTIONS is "true" and GITHUB_RUN_ID
                equals RUN_ID, so a session cannot reach this path by passing the flag. It suppresses
                only the CLAUDECODE refusal and writes the run id, actor and approved artifacts to
                $GITHUB_OUTPUT for the committer step; every file it writes is byte-identical to a
                plain run (work/approve-by-dispatch R-3).

What it does, per artifact: sets `status: approved`, `approved-by: HANDLE`, `approved-on: <today UTC>` in
the YAML front matter, and appends `- <ts> | <artifact> | <old> -> approved | HANDLE | <sha> | <note>` to
work/<slug>/log.md (creating it from the template shape if absent). With --delegate it also sets
`mode: delegated`, `delegated-by: HANDLE` and `delegated-on: <today UTC>` on intent.md -- the grant
delegated mode stands on, which is why it is a human act on the one file no agent may sign -- and the
intent's ledger note carries `mode: delegated` (after any --note, separated by `; `). It then prints
the commit command; the human commits. Nothing is committed by this script.

Stage order: spec.md is approved only once intent.md is, plan.md only once spec.md is (on disk, or
earlier in the same call, which processes several artifacts in chain order whatever order they are
given in). A violation exits 1 naming the predecessor and its status, and writes nothing.

Only a human may approve (hard rule in CLAUDE.md). The script therefore refuses to run inside a Claude
Code session, which exports CLAUDECODE=1 to every command it runs; an agent asking a human to approve
is the intended path. That refusal is a courtesy, not a gate (an environment variable can be
stripped): the deterministic check is in scripts/check_artifact_chain.py, which fails when the commit
that set `status: approved` -- or `mode: delegated` -- is authored by an agent identity. Commit the
approval as yourself.
Exit codes: 0 ok, 1 usage/validation error, 3 refused (agent session).
"""
import argparse, os, re, subprocess, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import approvers  # noqa: E402
import log_ledger  # noqa: E402
from check_artifact_chain import ROOT, front_matter  # noqa: E402

ARTIFACTS = ("intent.md", "spec.md", "plan.md", "incident.md")
PREDECESSOR = {"spec.md": "intent.md", "plan.md": "spec.md"}


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT).stdout.strip()


def set_front_matter(text, updates):
    """Return text with the given front-matter keys set (added after `status:` when missing)."""
    if not text.startswith("---\n"):
        raise ValueError("no front matter")
    head, rest = text[4:].split("\n---\n", 1)
    lines = head.split("\n")
    for key, value in updates.items():
        pat = re.compile(rf"^{re.escape(key)}:.*$")
        for i, line in enumerate(lines):
            if pat.match(line):
                lines[i] = f"{key}: {value}"
                break
        else:
            idx = next((i for i, l in enumerate(lines) if l.startswith("status:")), len(lines) - 1)
            lines.insert(idx + 1, f"{key}: {value}")
    return "---\n" + "\n".join(lines) + "\n---\n" + rest


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("slug")
    ap.add_argument("artifacts", nargs="+", choices=ARTIFACTS, metavar="artifact")
    ap.add_argument("--as", dest="handle")
    ap.add_argument("--note", default="")
    ap.add_argument("--delegate", action="store_true",
                    help="with intent.md: also grant delegated mode (mode/delegated-by/delegated-on)")
    ap.add_argument("--activate", action="store_true")
    ap.add_argument("--from-dispatch", dest="from_dispatch", metavar="RUN_ID",
                    help="run inside the approve.yml workflow_dispatch run RUN_ID; requires --as")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    # A dispatch run is the one caller that is neither a human shell nor an agent session: the
    # human act happened in the Actions tab, and GitHub -- not this process -- recorded who made
    # it. The three conditions below are all checkable from the environment the runner sets and
    # none of them is settable by the workflow's inputs, so a session cannot fake its way in by
    # passing the flag (work/approve-by-dispatch R-3).
    if a.from_dispatch is not None:
        if not a.handle:
            print("approve: --from-dispatch requires --as <github-handle> (the run's actor)", file=sys.stderr)
            return 1
        if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("GITHUB_RUN_ID") != a.from_dispatch:
            print("approve: --from-dispatch is only valid inside the GitHub Actions run it names "
                  "(GITHUB_ACTIONS=true and GITHUB_RUN_ID matching).", file=sys.stderr)
            return 3
    elif os.environ.get("CLAUDECODE"):
        print("approve: refused — this is a Claude Code session (CLAUDECODE is set). Only a human approves; "
              "run this from your own shell.", file=sys.stderr)
        return 3

    handle = a.handle or git("config", "sdlc.approver")
    if not handle:
        print("approve: no handle; pass --as <github-handle> or `git config sdlc.approver <handle>`", file=sys.stderr)
        return 1
    av = approvers.load()
    wd = os.path.join(ROOT, "work", a.slug)
    if not os.path.isdir(wd):
        print(f"approve: work/{a.slug} does not exist", file=sys.stderr)
        return 1

    # The grant lives on intent.md and nowhere else: a later artifact may not widen the item's
    # permission, and the agent never signs the file that grants it (work/delegated-mode R-8, D-b).
    policy = None
    if a.delegate:
        if "intent.md" not in a.artifacts:
            print("approve: --delegate applies to intent.md; it is the file that carries the grant",
                  file=sys.stderr)
            return 1
        # Lazy import: only a --delegate call needs the policy, so a repository without
        # scripts/delegation.py still approves normally.
        import delegation

        try:
            policy = delegation.load()
        except ValueError as e:
            print(f"approve: malformed delegation policy: {e}", file=sys.stderr)
            return 1

    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    today = now.strftime("%Y-%m-%d")
    sha = git("rev-parse", "--short", "HEAD") or "0000000"
    changed, lines = [], []

    # Validate everything first, in chain order, so a refusal writes nothing; then write.
    ordered = [n for n in ARTIFACTS if n in a.artifacts]
    approved_now = set()
    todo = []  # (name, path, old_status, new_text, note)
    for name in ordered:
        path = os.path.join(wd, name)
        fm = front_matter(path)
        if fm is None:
            print(f"approve: work/{a.slug}/{name} is missing", file=sys.stderr)
            return 1
        ok, reason = av.is_valid(name, handle)
        if not ok:
            print(f"approve: '{handle}' may not approve {name}: {reason}", file=sys.stderr)
            return 1
        prev = PREDECESSOR.get(name)
        if prev and prev not in approved_now:
            prev_fm = front_matter(os.path.join(wd, prev))
            prev_status = "missing" if prev_fm is None else (prev_fm.get("status") or "draft")
            if prev_status != "approved":
                print(f"approve: work/{a.slug}/{name} needs work/{a.slug}/{prev} approved first "
                      f"(it is '{prev_status}')", file=sys.stderr)
                return 1
        approved_now.add(name)
        old = fm.get("status", "draft") or "draft"
        updates = {"status": "approved", "approved-by": handle, "approved-on": today}
        note = a.note
        grant = a.delegate and name == "intent.md"
        if grant:
            ok, reason = policy.risk_ok(fm.get("risk-class", ""))
            if not ok:
                hint = ("; create .sdlc/delegation.yaml from docs/sdlc/templates/delegation.yaml first"
                        if not policy.exists else "")
                print(f"approve: work/{a.slug}/intent.md may not be delegated: {reason}{hint}",
                      file=sys.stderr)
                return 1
            updates.update({"mode": "delegated", "delegated-by": handle, "delegated-on": today})
            note = f"{a.note}; mode: delegated" if a.note else "mode: delegated"
        # An intent approved earlier can still be granted later, so "already approved" is a no-op
        # only when there is nothing new to write -- the grant included.
        settled = not grant or (fm.get("mode") == "delegated" and fm.get("delegated-by"))
        if old == "approved" and av.normalize(fm.get("approved-by", "")) == av.normalize(handle) and settled:
            print(f"approve: work/{a.slug}/{name} already approved by {handle}; nothing to do")
            continue
        with open(path, encoding="utf-8") as f:
            text = f.read()
        todo.append((name, path, old, set_front_matter(text, updates), note))

    for name, path, old, new_text, note in todo:
        entry = log_ledger.Entry(ts=ts, artifact=name, from_status=old, to_status="approved",
                                 actor=handle, sha=sha, note=note, lineno=0)
        line = log_ledger.render(entry)
        print(f"{'would approve' if a.dry_run else 'approved'}: work/{a.slug}/{name} ({old} -> approved) by {handle}")
        print(f"  ledger: {line}")
        if not a.dry_run:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_text)
            lines.append(line)
        changed.append(name)

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

    if a.activate and not a.dry_run:
        with open(os.path.join(ROOT, ".sdlc", "active"), "w", encoding="utf-8") as f:
            f.write(a.slug + "\n")
        print(f"activated: .sdlc/active -> {a.slug}")

    if changed and not a.dry_run and a.from_dispatch is not None:
        # The committer step reads these instead of re-deriving them: it must stage exactly what
        # this call wrote, and name the same run in the commit trailer (R-4).
        out = os.environ.get("GITHUB_OUTPUT")
        if out:
            with open(out, "a", encoding="utf-8") as f:
                f.write(f"approved={' '.join(changed)}\n")
                f.write(f"run-id={a.from_dispatch}\n")
                f.write(f"actor={handle}\n")
    elif changed and not a.dry_run:
        paths = f"work/{a.slug}" + (" .sdlc/active" if a.activate else "")
        print("\nNext: review the diff, then commit as yourself:")
        print(f"  git add {paths} && git commit -m \"[{a.slug}] approve {' '.join(changed)}\"")
        print("  python3 scripts/check_artifact_chain.py --slug", a.slug, "--base origin/main")
    return 0


if __name__ == "__main__":
    sys.exit(main())
