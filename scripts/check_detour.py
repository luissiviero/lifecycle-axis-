#!/usr/bin/env python3
"""Does this work touch a path the delegated merge will lock? (work/risk-detour R-2)

The detour trigger of the `sdlc-run` skill: at every gate the run asks this script whether the paths
it is about to plan, or has already changed, fall under a list the merge refuses -- `PROTECTED_PATHS`
and `RELEASE_GATED_PATHS` from `.sdlc/config.env`, the policy's `locked-paths` from
`.sdlc/delegation.yaml`, the merge script's own `ALWAYS_LOCKED` floor, and (with `--slug`) this item's
`intent.md`. The matching is `scripts/delegated_merge.py`'s `check_locked_paths`, called once per path,
so the answer here is the answer the merge will give (knowledge/lessons/one-path-spelling-in-guards.md:
one matcher, never a second spelling of the rule). Only the label -- which list the matched prefix sits
in -- is computed here, as a set lookup on the prefix the matcher returned.

Deterministic, advisory, local: it changes nothing and judges nothing at the merge; the merge script
runs the same matcher again on the pull request's files.

Sources (exactly one):
  --paths P...        the paths themselves
  --plan FILE         every bullet under `## Files that change` in a plan.md, the path before the first
                      ` — ` (knowledge/lessons/plan-bullets-start-with-the-path.md); a glob expands under
                      the root, a glob matching nothing keeps its literal
  --diff BASE         `git diff --name-status -M BASE...HEAD`: both names of a rename are candidates,
                      since the merge checks `previous_filename` too

Output: one line per locked path, in input order,
  <path>: locked by <list>[, <list>...] '<prefix>'
then the verdict line, which is also the exit code:
  DETOUR: none          exit 0
  DETOUR: needed (<n>)  exit 3
Bad input (no source, two sources, an unreadable plan, a plan without the heading, a base git cannot
resolve) is exit 2 with a `check-detour: <reason>` line on stderr and no `DETOUR:` line, so a caller
that reads the last line never mistakes silence for clean.
"""
import argparse
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import delegated_merge as dm  # noqa: E402  (check_locked_paths, _locked_paths, ALWAYS_LOCKED, load_config)
import delegation  # noqa: E402

DEFAULT_ROOT = os.path.dirname(HERE)
FILES_HEADING = "## Files that change"
# The matcher's reason: "<name> is under the locked path '<prefix>'". A reworded reason fails the
# test that pins this rather than mislabelling silently (plan risk 2).
REASON_RE = re.compile(r" is under the locked path '(.*)'$")
BULLET_SPLIT = " — "
GLOB_CHARS = ("*", "?", "[")


class DetourInputError(Exception):
    """Bad input: reported as exit 2, never as a verdict."""


def _labels(prefix, config, policy, slug):
    """Every list `prefix` sits in, in a fixed order. Entries are compared the way the matcher
    normalised them (a trailing slash stripped)."""
    p = prefix.rstrip("/")
    lists = (
        ("PROTECTED_PATHS", config.get("PROTECTED_PATHS") or []),
        ("RELEASE_GATED_PATHS", config.get("RELEASE_GATED_PATHS") or []),
        ("locked-paths", policy.locked_paths),
        ("ALWAYS_LOCKED", dm.ALWAYS_LOCKED),
        ("this item's intent", ["work/%s/intent.md" % slug] if slug else []),
    )
    return [name for name, entries in lists if p in [e.rstrip("/") for e in entries]]


def locked(paths, root=None, slug=None):
    """[(path, [label, ...], prefix), ...] for every path the merge would refuse, in input order."""
    root = root or DEFAULT_ROOT
    config = dm.load_config(root)
    policy = delegation.load(path=os.path.join(root, ".sdlc", "delegation.yaml"))
    prefixes = dm._locked_paths(config, policy, slug)
    hits = []
    for path in paths:
        verdict, reason = dm.check_locked_paths([{"filename": path}], prefixes)
        if verdict != dm.REFUSED:
            continue
        m = REASON_RE.search(reason)
        prefix = m.group(1) if m else "?"
        hits.append((path, _labels(prefix, config, policy, slug), prefix))
    return hits


def verdict(hits):
    """The last line and the exit code."""
    if hits:
        return "DETOUR: needed (%d)" % len(hits), 3
    return "DETOUR: none", 0


def plan_paths(plan_file, root=None):
    """The paths a plan's `## Files that change` bullets name, globs expanded under `root`."""
    root = root or DEFAULT_ROOT
    try:
        with open(plan_file, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError as exc:
        raise DetourInputError("cannot read %s: %s" % (plan_file, exc.strerror or exc))
    inside, bullets = False, []
    for line in lines:
        if line.startswith(FILES_HEADING):
            inside = True
            continue
        if inside and line.startswith("## "):
            break
        if inside and line.startswith("- "):
            head = line[2:].split(BULLET_SPLIT, 1)[0].strip().strip("`")
            if head:
                bullets.append(head)
    if not inside:
        raise DetourInputError("%s has no '%s' heading" % (plan_file, FILES_HEADING))
    paths = []
    for raw in bullets:
        # One spelling per path, the matcher's (knowledge/lessons/one-path-spelling-in-guards.md):
        # `./x` and `a/../x` are `x`. A bullet that leaves the root is bad input, not a clean path
        # (security pass on pull request 96, nits 1 and 2).
        b = os.path.normpath(raw).replace(os.sep, "/")
        if os.path.isabs(raw) or b == ".." or b.startswith("../"):
            raise DetourInputError("plan bullet '%s' is not a path under the repository root" % raw)
        if any(c in b for c in GLOB_CHARS):
            matches = sorted(glob.glob(b, root_dir=root, recursive=True))
            paths.extend(m.replace(os.sep, "/") for m in matches) if matches else paths.append(b)
        else:
            paths.append(b)
    return paths


def diff_paths(root, base):
    """Every name a diff against `base` touches, both names of a rename."""
    root = root or DEFAULT_ROOT
    ok = subprocess.run(["git", "-C", root, "rev-parse", "--verify", "--quiet", base + "^{commit}"],
                        capture_output=True, text=True)
    if ok.returncode != 0:
        raise DetourInputError("git cannot resolve '%s' as a commit" % base)
    # `-z`: NUL-terminated, so a name with a tab, a newline or a non-ASCII byte arrives as itself
    # rather than C-quoted (`core.quotePath`), and the matcher sees the real name
    # (knowledge/lessons/nul-terminated-git-output.md; security pass on pull request 96, finding 1).
    # The record is `<status>NUL<path>NUL`, and `<status>NUL<old>NUL<new>NUL` for a rename or copy.
    r = subprocess.run(["git", "-C", root, "diff", "--name-status", "-M", "-z", "%s...HEAD" % base, "--"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise DetourInputError("git diff failed: %s" % (r.stderr.strip().splitlines() or ["?"])[-1])
    fields = r.stdout.split("\0")
    paths, i = [], 0
    while i < len(fields) and fields[i]:
        status = fields[i]
        take = 2 if status[:1] in ("R", "C") else 1
        for name in fields[i + 1:i + 1 + take]:
            if name and name not in paths:
                paths.append(name)
        i += 1 + take
    return paths


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=None, help="repository root (default: this checkout)")
    ap.add_argument("--slug", default=None, help="the work item, so its intent.md counts as locked")
    ap.add_argument("--paths", nargs="+", metavar="P", help="paths to judge")
    ap.add_argument("--plan", metavar="FILE", help="read the paths from a plan.md's Files that change")
    ap.add_argument("--diff", metavar="BASE", help="read the paths from git diff BASE...HEAD")
    a = ap.parse_args(argv)
    root = a.root or DEFAULT_ROOT
    sources = [s for s in (a.paths, a.plan, a.diff) if s]
    try:
        if len(sources) != 1:
            raise DetourInputError("give exactly one of --paths, --plan, --diff")
        if a.paths:
            paths = a.paths
        elif a.plan:
            plan_file = a.plan if os.path.isabs(a.plan) else os.path.join(root, a.plan)
            paths = plan_paths(plan_file, root)
        else:
            paths = diff_paths(root, a.diff)
        policy_path = os.path.join(root, ".sdlc", "delegation.yaml")
        try:
            hits = locked(paths, root, a.slug)
        except (OSError, ValueError) as exc:
            raise DetourInputError("cannot read %s or %s: %s" % (
                os.path.join(root, ".sdlc", "config.env"), policy_path, exc))
    except DetourInputError as exc:
        print("check-detour: %s" % exc, file=sys.stderr)
        return 2
    for path, labels, prefix in hits:
        print("%s: locked by %s '%s'" % (path, ", ".join(labels) or "?", prefix))
    line, code = verdict(hits)
    print(line)
    return code


if __name__ == "__main__":
    sys.exit(main())
