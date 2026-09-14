#!/usr/bin/env python3
"""The two halves of .github/workflows/approve.yml that must not be shell: the role gate that runs
before anything is written, and the commit that records who pressed Run.

Usage:
  scripts/approve_dispatch.py --check-actor LOGIN --artifact NAME [--mode MODE] [--ref REF]
                              [--default-branch NAME] [--root DIR]
  scripts/approve_dispatch.py --commit --actor LOGIN --run-id N --slug S [--artifact NAME]
                              [--note TEXT] [--activated] [--root DIR]

--check-actor prints `ok` and exits 0 when LOGIN holds the artifact's role in .sdlc/approvers.yaml;
otherwise it prints the reason from approvers.Approvers.is_valid on stderr and exits 1, before the
approval step runs, so a refusal leaves the tree untouched (R-2, D5). With `--mode delegated` it
also requires --ref to be the default branch: a grant lands on main or nowhere (R-8).

--commit first regenerates every index with gen_index.render_all -- work/<slug>/index.md for every
item and work/index.md, so a tap heals drift it finds on the ref -- then stages exactly the item's
chain files, .sdlc/active and the generated indexes, refuses (exit 1) when `git status --porcelain`
lists anything else or when nothing but an index changed, and commits with

    author    = the run's actor, as <id>+<login>@users.noreply.github.com from the users API
    committer = github-actions[bot]
    trailers  = Approved-Run: <run id> / Approved-Actor: <login>

The split identity is D2: the author is the actor so check_artifact_chain.py's existing git-author
rule keeps passing with no API call, and the committer is the bot so the commit never claims a human
typed it. The trailers are what make the decision verifiable afterwards -- check_artifact_chain.py
and delegated_merge.py both resolve them against the Actions API, which reports `actor.login` from
the run record, a field nothing inside the run can set (R-5, R-6, R-7).

The staged-path allowlist lives here rather than in the workflow because a shell `git add work/...`
would glob: a stray file from some future change to approve.py could ride along unnoticed (D6).

stdlib only. Exit codes: 0 ok, 1 refused/usage error.
"""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import approvers  # noqa: E402
import gen_index  # noqa: E402

BOT_NAME = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"

# The same shape delegated_merge.py's SLUG_RE enforces, and for the same reason. The workflow's
# `tr -cd 'A-Za-z0-9._-'` strips slashes but keeps dots, so `..` survives it intact -- and a slug of
# `..` makes work/<slug>/ resolve to the repository root, so `allowed_paths` would name root files
# rather than the item's. Nothing at the root is called intent.md today, which is the only reason
# that failed softly rather than letting a `contents: write` run commit outside the work item. A
# containment rule that holds only because of what happens not to exist is not a containment rule
# (security pass on pull request 51).
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*(\.[A-Za-z0-9_-]+)*$")

# Exactly what an approval may touch. approve.py writes the artifact, log.md and (with --activate)
# .sdlc/active; --commit itself regenerates work/*/index.md and work/index.md with
# gen_index.render_all before it judges the tree, and commits every index it changed, other items'
# included (work/approve-tap-regenerates-index). Anything else is a bug in the caller, not something
# to commit quietly.
CHAIN_FILES = ("intent.md", "spec.md", "plan.md", "incident.md", "log.md", "index.md")

# A generated index of any item. The segment class is the generator's, not SLUG_RE's: gen_index
# renders every directory under work/ (gen_index._work_items), and main tracks work/_example/index.md,
# whose name SLUG_RE refuses as a slug -- a predicate built on SLUG_RE would fail every tap the moment
# that one index drifted, naming a file no tap wrote. A leading dot is excluded so `.`, `..` and
# `.git` never match, the same containment SLUG_RE gives the slug (spec D4, G-2).
INDEX_RE = re.compile(r"work/([A-Za-z0-9_][A-Za-z0-9._-]*)/index\.md")
TOP_INDEX = "work/index.md"


def git(*args, root=None, check=True):
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit(f"approve-dispatch: git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def allowed_paths(slug):
    if not SLUG_RE.match(slug or ""):
        raise SystemExit("approve-dispatch: refusing a slug that is not a plain work-item name: "
                         "%r (it would name paths outside work/<slug>/)" % (slug,))
    return {f"work/{slug}/{name}" for name in CHAIN_FILES} | {".sdlc/active"}


def check_actor(login, artifact, mode=None, ref=None, default_branch=None, root=None,
                slug=None):
    """(True, "ok") when `login` may decide `artifact`; otherwise (False, reason)."""
    if slug is not None and not SLUG_RE.match(slug or ""):
        return False, ("slug %r is not a plain work-item name; it would name paths outside "
                       "work/<slug>/" % (slug,))
    path = os.path.join(root, ".sdlc", "approvers.yaml") if root else None
    av = approvers.load(path)
    ok, reason = av.is_valid(artifact, login)
    if not ok:
        return False, reason
    # A grant is the one write that must land on the default branch: .sdlc/active and the mode keys
    # are read from main by every later check, so a grant on a side branch would be invisible (R-8).
    if mode == "delegated":
        if artifact != "intent.md":
            return False, "mode: delegated applies to intent.md; it is the file that carries the grant"
        if not default_branch:
            return False, "cannot verify the ref: no default branch given"
        if ref != default_branch and ref != f"refs/heads/{default_branch}":
            return False, (f"a delegation grant must be dispatched from the default branch "
                           f"({default_branch}), not '{ref}'")
    return True, "ok"


def actor_identity(login):
    """`<id>+<login>@users.noreply.github.com`, the identity GitHub itself uses for this account.

    Resolved from the users API so the numeric id is the account's real one; without it the address
    would be a guess, and a guessed address is not an identity.
    """
    r = subprocess.run(["gh", "api", f"users/{login}", "--jq", ".id"],
                       capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip().isdigit():
        raise SystemExit(f"approve-dispatch: cannot resolve the GitHub id for '{login}': "
                         f"{r.stderr.strip() or r.stdout.strip()}")
    return f"{login} <{r.stdout.strip()}+{login}@users.noreply.github.com>"


def is_generated_index(path):
    return path == TOP_INDEX or INDEX_RE.fullmatch(path) is not None


def is_allowed(path, slug):
    """May an approval of `slug` commit `path`: one of its own chain files, .sdlc/active, or any
    generated index (spec R-3)."""
    return path in allowed_paths(slug) or is_generated_index(path)


def changed_paths(root=None):
    """Every path `git status` reports as changed, one per entry, sorted.

    Two details of `git status --porcelain` decide whether the guard built on this works at all,
    and both were found by its own tests. The status field is two columns wide and unstaged changes
    leave the first blank, so the output must not be stripped before the lines are split --
    stripping eats that leading space and shifts every path by one character. And untracked content
    is reported one directory at a time unless --untracked-files=all is asked for, which would let a
    whole new directory of stray files past as a single entry that never matches an allowed path.
    """
    r = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"approve-dispatch: git status failed: {r.stderr.strip()}")
    out = []
    for line in r.stdout.split("\n"):
        if not line.strip():
            continue
        path = line[3:].strip().strip('"')
        if " -> " in path:  # a rename: judge the destination
            path = path.split(" -> ", 1)[1]
        out.append(path)
    return sorted(out)


def unexpected_paths(slug, root=None):
    """Paths git reports as changed that an approval is not allowed to touch."""
    return [p for p in changed_paths(root) if not is_allowed(p, slug)]


def regenerate(root=None):
    """Render every index with gen_index's own renderer and write the ones whose bytes differ.

    Returns the repository-relative paths written, sorted, and prints them so the workflow's run
    log says what the tap rewrote (spec R-8). The write is the generator's own call (utf-8, LF) and
    CRLF on disk is folded before comparing, as gen_index.py --check does; the committer's test runs
    that --check on the committed tree, which is what proves the two write routes agree (spec D1).
    Content never makes the generator fail (spec G-1); an unwritable tree raises, and commit() lets
    that propagate before anything is staged, so the run fails before its push and nothing lands.
    """
    top = gen_index.resolve_root(root)
    written = []
    for rel, content in gen_index.render_all(top):
        full = os.path.join(top, *rel.split("/"))
        want = content.encode("utf-8")
        try:
            with open(full, "rb") as f:
                have = f.read().replace(b"\r\n", b"\n")
        except FileNotFoundError:
            have = None
        if have == want:
            continue
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        written.append(rel)
    written.sort()
    if written:
        print(f"approve-dispatch: regenerated {len(written)} index file(s): {', '.join(written)}")
    else:
        print("approve-dispatch: indexes already up to date")
    return written


def commit(slug, actor, run_id, artifact=None, note="", root=None, identity=None):
    # Regenerate first, then judge the whole tree: a regenerated index of any item is allowed, a
    # stray path is still refused, and the regenerated files go with the discarded tree (spec D2).
    regenerate(root)
    stray = unexpected_paths(slug, root=root)
    if stray:
        print("approve-dispatch: refusing to commit; an approval may not touch: "
              + ", ".join(stray), file=sys.stderr)
        return 1
    # Everything git reported passed the guard, so stage exactly that: one list drives both the
    # guard and the staging, and a regenerated index of another item is reachable (spec D5).
    changed = changed_paths(root)
    # A diff of generated indexes alone is not an approval: the trailers below vouch for a decision,
    # and there was none. Refuse before staging, so the index is empty and the regenerated files
    # stay unstaged in a tree the run discards (spec D3, R-5).
    if not [p for p in changed if not is_generated_index(p)]:
        print("approve-dispatch: nothing staged; approve.py wrote no change", file=sys.stderr)
        return 1
    git("add", "--", *changed, root=root)
    if not git("diff", "--cached", "--name-only", root=root):
        print("approve-dispatch: nothing staged; approve.py wrote no change", file=sys.stderr)
        return 1
    subject = f"[{slug}] Approve {artifact or 'artifact'} as {actor}"
    body = f"{note}\n\n" if note else ""
    message = f"{subject}\n\n{body}Approved-Run: {run_id}\nApproved-Actor: {actor}\n"
    author = identity or actor_identity(actor)
    env = dict(os.environ, GIT_COMMITTER_NAME=BOT_NAME, GIT_COMMITTER_EMAIL=BOT_EMAIL)
    r = subprocess.run(["git", "commit", "--author", author, "-F", "-"],
                       cwd=root, input=message, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        print(f"approve-dispatch: commit failed: {r.stderr.strip()}", file=sys.stderr)
        return 1
    print(git("log", "-1", "--format=%H %an <%ae> / %cn <%ce>", root=root))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check-actor", dest="check_actor", metavar="LOGIN")
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--actor")
    ap.add_argument("--artifact")
    ap.add_argument("--mode")
    ap.add_argument("--ref")
    ap.add_argument("--default-branch", dest="default_branch")
    ap.add_argument("--run-id", dest="run_id")
    ap.add_argument("--slug")
    ap.add_argument("--note", default="")
    ap.add_argument("--root")
    a = ap.parse_args(argv)

    if a.check_actor is not None:
        if not a.artifact:
            print("approve-dispatch: --check-actor needs --artifact", file=sys.stderr)
            return 1
        ok, reason = check_actor(a.check_actor, a.artifact, mode=a.mode, ref=a.ref,
                                 default_branch=a.default_branch, root=a.root, slug=a.slug)
        if not ok:
            print(f"approve-dispatch: {a.check_actor} may not approve {a.artifact}: {reason}",
                  file=sys.stderr)
            return 1
        print("ok")
        return 0

    if a.commit:
        missing = [f for f in ("actor", "run_id", "slug") if not getattr(a, f)]
        if missing:
            print(f"approve-dispatch: --commit needs {', '.join('--' + m.replace('_', '-') for m in missing)}",
                  file=sys.stderr)
            return 1
        return commit(a.slug, a.actor, a.run_id, artifact=a.artifact, note=a.note, root=a.root)

    ap.print_usage(sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
