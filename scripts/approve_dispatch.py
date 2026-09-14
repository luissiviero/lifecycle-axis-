#!/usr/bin/env python3
"""The two halves of .github/workflows/approve.yml that must not be shell: the role gate that runs
before anything is written, and the commit that records who pressed Run.

Usage:
  scripts/approve_dispatch.py --check-actor LOGIN --artifact NAME [--mode MODE] [--ref REF]
                              [--default-branch NAME] [--slug S] [--root DIR]
  scripts/approve_dispatch.py --commit --actor LOGIN --run-id N --slug S [--artifact NAME]
                              [--mode MODE] [--note TEXT] [--root DIR]

--check-actor prints `ok` and exits 0 when LOGIN holds the artifact's role in .sdlc/approvers.yaml;
otherwise it prints the reason from approvers.Approvers.is_valid on stderr and exits 1, before the
approval step runs, so a refusal leaves the tree untouched (R-2, D5). With `--mode delegated` it
also requires --ref to be the default branch: a grant lands on main or nowhere (R-8). With `--mode
retire` the artifact input is ignored and --slug is required: a retirement supersedes every chain
artifact present under work/<slug>/, so LOGIN must hold every one of their roles
(work/retire-delegated-items R-7).

--commit first regenerates the indexes with gen_index.render_all: on the default branch every
work/<slug>/index.md and work/index.md whose bytes changed, so a tap on main heals drift it finds
there; on any other ref only the item's own work/<slug>/index.md and work/index.md, because
check_artifact_chain.py counts only those as the item's files and a foreign index in a work branch's
diff would turn its pull request red. It then stages exactly the item's chain files, .sdlc/active
and the indexes the route allows, refuses (exit 1) when `git status --porcelain` lists anything else
(a rename is judged at both ends) or when nothing but an index changed, and commits with

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
import json
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
# gen_index.render_all before it judges the tree, and commits every index it changed -- other items'
# included on the default branch, the item's own two only on any other ref
# (work/approve-tap-regenerates-index). Anything else is a bug in the caller, not something to commit
# quietly.
CHAIN_FILES = ("intent.md", "spec.md", "plan.md", "incident.md", "log.md", "index.md")
# The artifacts a retirement supersedes, in chain order: the ones approve.py --retire writes.
ARTIFACTS = ("intent.md", "spec.md", "plan.md", "incident.md")

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
    if mode == "retire":
        # Every present artifact is written, so every role is required; the `artifact` input is
        # what the form showed and means nothing here (spec D4). Read from the checkout, like the
        # retirement itself. And on the default branch only, like a grant: a retirement moves
        # .sdlc/active, and a work branch whose diff moves the pointer is strict for the chain
        # check, so its pull request could never merge (security pass on pull request 92).
        if not slug:
            return False, "a retirement must name its slug; the artifact input is ignored"
        if not default_branch:
            return False, "cannot verify the ref: no default branch given"
        if not is_default_branch(ref, default_branch):
            return False, (f"a retirement must be dispatched from the default branch "
                           f"({default_branch}), not '{ref}'")
        wd = os.path.join(root or ".", "work", slug)
        present = [n for n in ARTIFACTS if os.path.exists(os.path.join(wd, n))]
        if not present:
            return False, f"work/{slug} has no chain artifact to retire"
        for name in present:
            ok, reason = av.is_valid(name, login)
            if not ok:
                return False, f"{name}: {reason}"
        return True, "ok"
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
        if not is_default_branch(ref, default_branch):
            return False, (f"a delegation grant must be dispatched from the default branch "
                           f"({default_branch}), not '{ref}'")
    return True, "ok"


def is_default_branch(ref, default_branch):
    """One spelling of "is this ref the default branch", shared by the role gate above and the route
    below: `<name>` and `refs/heads/<name>` both count (knowledge/lessons/one-path-spelling-in-guards.md)."""
    return bool(default_branch) and ref in (default_branch, f"refs/heads/{default_branch}")


def event_default_branch(path=None):
    """`repository.default_branch` from the Actions event payload, or None.

    The same field the workflow's role gate reads as github.event.repository.default_branch, and the
    one delegated_merge.py reads from the same file. Never raises: a missing or empty path, an
    unreadable file, JSON that does not parse or nests past the interpreter's recursion limit, a top
    level or `repository` that is not an object, or a value that is not a non-empty string all return
    None, and None takes the narrow route (spec R-11).
    """
    path = path or os.environ.get("GITHUB_EVENT_PATH")
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            event = json.load(f)
    except (OSError, ValueError, RecursionError):
        return None
    repo = event.get("repository") if isinstance(event, dict) else None
    value = repo.get("default_branch") if isinstance(repo, dict) else None
    return value if isinstance(value, str) and value else None


def route(ref=None, default_branch=None):
    """True for the wide route -- the run is on the default branch, so the tap may heal every index --
    and False for the narrow route, the item's own two indexes only (spec R-11, D6).

    `ref` and `default_branch` are the caller's when given (main() threads the parsed --ref and
    --default-branch through), else the runner's: GITHUB_REF, the full `refs/heads/<name>`, whose
    prefix disambiguates a branch literally named `refs/heads/main` (its full ref is
    `refs/heads/refs/heads/main`), then GITHUB_REF_NAME, and the event payload. GITHUB_REF_TYPE, when
    set, must say `branch`, so a tag named like the branch is narrow. Every unknown value is narrow: a
    spoofed or missing input can only stop a heal, never cause one.
    """
    ref = ref or os.environ.get("GITHUB_REF") or os.environ.get("GITHUB_REF_NAME")
    default_branch = default_branch or event_default_branch()
    ref_type = os.environ.get("GITHUB_REF_TYPE")
    if ref_type and ref_type != "branch":
        return False
    return is_default_branch(ref, default_branch)


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


def own_index(path, slug):
    """The two indexes check_artifact_chain.py counts as the item's own files, whatever the route."""
    return path in (f"work/{slug}/index.md", TOP_INDEX)


def is_allowed(path, slug, allowed=None, wide=False):
    """May an approval of `slug` commit `path`: one of its own chain files, .sdlc/active, its own two
    indexes, or, on the wide route only, any generated index (spec R-3, D7). `allowed` is
    allowed_paths(slug), precomputed by a caller judging many paths."""
    allowed = allowed_paths(slug) if allowed is None else allowed
    if path in allowed or own_index(path, slug):
        return True
    return wide and is_generated_index(path)


def changed_paths(root=None):
    """Two sorted lists from one `git status --porcelain -z`: the paths to judge, and the paths to stage.

    A rename or copy entry contributes both ends to the judged list, so a source outside the
    allowlist is a stray like any other, and its destination alone to the staged list, because git
    already holds the source's deletion in the index and `git add` on the vanished path exits 128
    (spec D5, R-10). Every other entry contributes its path to both.

    The output is NUL-delimited (-z): no path is quoted or escaped, and a rename is two fields, the
    destination then the source, so a filename that itself contains ` -> ` cannot be mistaken for a
    rename or split in the wrong place (the second review round and the automated review on #83 each
    found one such case in the line-oriented format). Two details still decide whether the guard
    built on this works at all, and both were found by its own tests: the status field is two columns
    wide and unstaged changes leave the first blank, so an entry must not be stripped before the path
    is cut from it; and untracked content is reported one directory at a time unless
    --untracked-files=all is asked for, which would let a whole new directory of stray files past as
    a single entry that never matches an allowed path.
    """
    r = subprocess.run(["git", "status", "--porcelain", "-z", "--untracked-files=all"],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"approve-dispatch: git status failed: {r.stderr.strip()}")
    fields = r.stdout.split("\0")
    judged, staged = [], []
    i = 0
    while i < len(fields):
        entry = fields[i]
        i += 1
        if not entry:
            continue
        code, path = entry[:2], entry[3:]
        if "R" in code or "C" in code:
            old = fields[i] if i < len(fields) else ""
            i += 1
            judged.extend((old, path))
            staged.append(path)
        else:
            judged.append(path)
            staged.append(path)
    return sorted(judged), sorted(staged)


def unexpected_paths(slug, root=None, changed=None, wide=False):
    """Judged paths an approval of `slug` may not touch on this route, sorted. `changed` is the judged
    list from changed_paths, so the guard and the staging read the same status run."""
    allowed = allowed_paths(slug)  # a traversing slug is refused up front, whatever the tree holds
    judged = changed_paths(root)[0] if changed is None else changed
    return sorted(p for p in judged if not is_allowed(p, slug, allowed, wide))


def regenerate(root=None, writable=None):
    """Render every index with gen_index's own renderer and write those the route may commit.

    Returns (written, skipped): the repository-relative paths whose bytes differ, sorted, split by
    whether `writable(rel)` accepted them (None accepts everything). Prints them so the workflow's
    run log says what the tap rewrote and what it left (spec R-8). The write is the generator's own
    call (utf-8, LF) and CRLF on disk is folded before comparing, as gen_index.py --check does; the
    committer's test runs that --check on the committed tree, which is what proves the two write
    routes agree (spec D1). Content never makes the generator fail (spec G-1); an unwritable tree
    raises, and commit() lets that propagate before anything is staged, so the run fails before its
    push and nothing lands.
    """
    top = gen_index.resolve_root(root)
    written, skipped = [], []
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
        if writable is not None and not writable(rel):
            skipped.append(rel)
            continue
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        written.append(rel)
    written.sort()
    skipped.sort()
    if written:
        print(f"approve-dispatch: regenerated {len(written)} index file(s): {', '.join(written)}")
    else:
        print("approve-dispatch: indexes already up to date")
    if skipped:
        print(f"approve-dispatch: left {len(skipped)} stale index file(s) unwritten on this ref: "
              + ", ".join(skipped))
    return written, skipped


def commit(slug, actor, run_id, artifact=None, note="", root=None, identity=None, ref=None,
           default_branch=None, mode=None):
    # The route first: on the default branch the tap may write and stage any generated index; on any
    # other ref only the item's own two, so a work branch's diff never carries a foreign index that
    # would flip check_artifact_chain.py out of in-progress mode (spec R-2, R-11, D6, D7).
    wide = route(ref, default_branch)
    writable = is_generated_index if wide else (lambda p: own_index(p, slug))
    # Regenerate before judging the whole tree: a regenerated index the route allows passes, a stray
    # path is still refused, and the regenerated files go with the discarded tree (spec D2).
    regenerate(root, writable)
    judged, staged = changed_paths(root)
    stray = unexpected_paths(slug, root=root, changed=judged, wide=wide)
    if stray:
        print("approve-dispatch: refusing to commit; an approval may not touch: "
              + ", ".join(stray), file=sys.stderr)
        return 1
    # A diff of generated indexes alone is not an approval: the trailers below vouch for a decision,
    # and there was none. Refuse before staging, so the index is empty and the regenerated files
    # stay unstaged in a tree the run discards (spec D3, R-5).
    if not [p for p in staged if not is_generated_index(p)]:
        cause = f" (only generated indexes changed: {', '.join(staged)})" if staged else ""
        print(f"approve-dispatch: nothing staged; approve.py wrote no change{cause}", file=sys.stderr)
        return 1
    # Everything reported passed the guard, so stage exactly the staged list from the same status run.
    git("add", "--", *staged, root=root)
    if not git("diff", "--cached", "--name-only", root=root):
        print("approve-dispatch: nothing staged; approve.py wrote no change", file=sys.stderr)
        return 1
    # A retirement writes every present artifact, so the subject names the act, not one file
    # (work/retire-delegated-items R-8); the trailers below are the same either way.
    if mode == "retire":
        subject = f"[{slug}] Retire as {actor}"
    else:
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
        return commit(a.slug, a.actor, a.run_id, artifact=a.artifact, note=a.note, root=a.root,
                      ref=a.ref, default_branch=a.default_branch, mode=a.mode)

    ap.print_usage(sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
