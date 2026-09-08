#!/usr/bin/env python3
"""Which delegated work item is next in the queue (work/run-queue R-1).

The owner grants N intents up front; this answers, deterministically and from committed files
alone, which one a run should open next. It is read by `scripts/delegated_merge.py` when it advances
`.sdlc/active` after a merge, and by the `sdlc-run` skill to print the queue before a run starts.

An item is in the queue when all of these hold on `work/<slug>/intent.md`:
  - `status: approved`   -- a human approved it (an agent never signs an intent)
  - `mode: delegated`    -- a human granted it; a non-granted item omits the key entirely rather
                            than leaving it blank, so an absent key means "not granted"
  - `risk-class` is one the policy delegates (`.sdlc/delegation.yaml`)
  - it is *unstarted*: no `spec.md`, or its status is `draft`/`in-review`. A signed or approved spec
    means some session is already working it, and handing it out twice would put two writers on one
    item (knowledge/decisions/one-writer-until-ledger.md).
Delegated mode being off empties the queue, like every other `may_*` query in delegation.py.

Order: earliest `delegated-on` first, ties broken by slug ascending. `delegated-on` is date-only, so
ties are the normal case rather than an edge one; the slug tiebreak makes the order total, which is
what lets the skill print it before the run and the merge reproduce it afterwards.

API:
  queue(root, policy, exclude=None) -> [slug, ...]   the whole queue, in order
  next_item(root, policy, exclude=None) -> slug|None the first of it

CLI:
  python3 scripts/next_item.py [--root DIR] [--exclude SLUG]
      print the next slug and exit 0; print nothing and exit 3 when the queue is empty
  python3 scripts/next_item.py --list
      print the whole queue, one slug per line (exit 0 even when empty)
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import delegation  # noqa: E402
from check_artifact_chain import ROOT, SLUG_RE, front_matter  # noqa: E402

# A spec in one of these states has not been signed off, so the item is still unstarted. Anything
# else (`delegated`, `approved`, `superseded`) means the item has moved past Design.
UNSTARTED_SPEC_STATUSES = ("draft", "in-review")


def _eligible(root, slug, policy):
    """(True, None) when `slug` belongs in the queue, else (False, reason). Reason is for the CLI's
    --list --why and for tests; nothing else reads it."""
    if not SLUG_RE.match(slug or ""):
        return False, "not a work-item name"
    fm = front_matter(os.path.join(root, "work", slug, "intent.md"))
    if fm is None:
        return False, "no intent.md"
    if fm.get("status") != "approved":
        return False, "intent is '%s', not 'approved'" % (fm.get("status") or "missing")
    if (fm.get("mode") or "supervised").strip() != "delegated":
        return False, "not granted (mode is '%s')" % (fm.get("mode") or "supervised")
    ok, reason = policy.risk_ok(fm.get("risk-class", ""))
    if not ok:
        return False, reason
    spec = front_matter(os.path.join(root, "work", slug, "spec.md"))
    if spec is not None and (spec.get("status") or "draft") not in UNSTARTED_SPEC_STATUSES:
        return False, "already started (spec.md is '%s')" % spec.get("status")
    return True, None


def queue(root=None, policy=None, exclude=None):
    """Every eligible item, earliest grant first, ties by slug."""
    root = root or ROOT
    policy = policy if policy is not None else delegation.load()
    work = os.path.join(root, "work")
    if not os.path.isdir(work):
        return []
    found = []
    for slug in sorted(os.listdir(work)):
        if slug == exclude or not os.path.isdir(os.path.join(work, slug)):
            continue
        ok, _ = _eligible(root, slug, policy)
        if ok:
            fm = front_matter(os.path.join(root, "work", slug, "intent.md"))
            # An absent or malformed date sorts last rather than crashing the queue: the grant is
            # still valid, it just has no place to claim in the order.
            found.append(((fm.get("delegated-on") or "9999-99-99").strip(), slug))
    return [slug for _, slug in sorted(found)]


def next_item(root=None, policy=None, exclude=None):
    q = queue(root, policy, exclude)
    return q[0] if q else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=None, help="repository root (default: this checkout)")
    ap.add_argument("--exclude", default=None, help="omit this slug (the item just merged)")
    ap.add_argument("--list", action="store_true", help="print the whole queue, one slug per line")
    a = ap.parse_args(argv)
    root = a.root or ROOT
    try:
        policy = delegation.load(path=os.path.join(root, ".sdlc", "delegation.yaml"))
    except ValueError as exc:
        print("next-item: malformed delegation policy: %s" % exc, file=sys.stderr)
        return 2
    if a.list:
        for slug in queue(root, policy, a.exclude):
            print(slug)
        return 0
    slug = next_item(root, policy, a.exclude)
    if slug is None:
        return 3
    print(slug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
