#!/usr/bin/env python3
"""OKF conformance checker (warning by default).

Walks the configured knowledge paths (or explicit paths given on the command
line) and reports, for every *.md file found:
  - `type` missing/empty in front matter (required)                  -> WARN <path> type <detail>
  - `title` / `description` / `timestamp` missing (conventional)     -> WARN <path> field:<name> <detail>
  - `timestamp` present but not RFC3339                              -> WARN <path> timestamp <detail>
  - a relative Markdown link target that does not resolve on disk    -> WARN <path> link <target>
and, for every directory (under the scanned paths) holding at least one .md
file, that it has an index.md                                        -> WARN <dir> index <detail>

Last line: `OKF: <N> docs, <W> warnings`. Exit 0 normally; exit 1 only when
--strict (or OKF_STRICT=1 in .sdlc/config.env and no --strict flag) and
warnings were found.

See docs/sdlc/okf-pairing.md for what OKF requires and why this is a warning,
not a merge gate, before the format is stable.
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_artifact_chain as cac  # noqa: E402  (path set up above; reuses front_matter()/config())

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
EXTERNAL_SCHEMES = ("http:", "https:", "mailto:")


def resolve_root(root_arg):
    if root_arg:
        return os.path.abspath(root_arg)
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
        )
        top = out.stdout.strip()
        if out.returncode == 0 and top:
            return top
    except OSError:
        pass
    return os.getcwd()


def load_config(root):
    """Read .sdlc/config.env under `root` via check_artifact_chain.config().

    That function is keyed off the module-global ROOT, so point it at our
    resolved root before calling it. Missing config.env is not fatal here:
    scanning still works (defaults to no knowledge paths, non-strict).
    """
    prev_root = cac.ROOT
    cac.ROOT = root
    try:
        return cac.config()
    except FileNotFoundError:
        return {}
    finally:
        cac.ROOT = prev_root


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", help="repo root to resolve config/defaults against (default: git toplevel or cwd)")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any warnings were found")
    ap.add_argument("paths", nargs="*", help="paths to scan (default: KNOWLEDGE_PATHS from config, plus 'work')")
    return ap.parse_args(argv)


def _walk_dirs(base):
    """Yield (dir_path, [md_file_paths_directly_in_dir]) for base and every
    subdirectory under it, skipping .git and following a symlinked directory
    at most once per branch (and never revisiting a real path already seen,
    which also guards against symlink cycles)."""
    visited_real = set()

    def helper(d, followed_symlink):
        real = os.path.realpath(d)
        if real in visited_real:
            return
        visited_real.add(real)
        try:
            entries = sorted(os.scandir(d), key=lambda e: e.name)
        except OSError:
            return
        mdfiles, subdirs = [], []
        for entry in entries:
            if entry.name == ".git":
                continue
            if entry.is_dir(follow_symlinks=True):
                is_link = entry.is_symlink()
                if is_link and followed_symlink:
                    continue  # already followed one symlink level on this branch
                subdirs.append((entry.path, followed_symlink or is_link))
            elif entry.is_file(follow_symlinks=True) and entry.name.endswith(".md"):
                mdfiles.append(entry.path)
        yield d, mdfiles
        for sd, nested_followed in subdirs:
            yield from helper(sd, nested_followed)

    yield from helper(base, False)


def _link_targets(text):
    for m in LINK_RE.finditer(text):
        raw = m.group(1).strip()
        if not raw:
            continue
        # Drop an optional trailing "title" (e.g. `y.md "Title"`).
        target = raw.split(None, 1)[0]
        yield raw, target


def check_file(path, root):
    """Return a list of (rel_path, rule, detail) findings for one .md file."""
    findings = []
    rel = os.path.relpath(path, root)
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return findings
    lines = text.splitlines()
    has_fm_marker = bool(lines) and lines[0].strip() == "---"
    fm = cac.front_matter(path) or {}

    if not has_fm_marker:
        findings.append((rel, "type", "no front matter"))
    else:
        if not fm.get("type"):
            findings.append((rel, "type", "missing or empty 'type'"))
        for name in ("title", "description", "timestamp"):
            if not fm.get(name):
                findings.append((rel, f"field:{name}", f"missing '{name}'"))
        ts = fm.get("timestamp")
        if ts:
            try:
                datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                findings.append((rel, "timestamp", f"'{ts}' is not RFC3339"))

    for raw_target, target in _link_targets(text):
        if target.startswith(EXTERNAL_SCHEMES):
            continue
        if target.startswith("#"):
            continue
        path_part, _, _frag = target.partition("#")
        if not path_part:
            continue
        resolved = os.path.normpath(os.path.join(os.path.dirname(path), path_part))
        ok = os.path.isdir(resolved) if path_part.endswith("/") else os.path.exists(resolved)
        if not ok:
            findings.append((rel, "link", raw_target))

    return findings


def scan(paths, root):
    findings = []
    doc_count = 0
    seen_files = set()
    seen_dirs = set()
    for base in paths:
        if os.path.isfile(base):
            real = os.path.realpath(base)
            if base.endswith(".md") and real not in seen_files:
                seen_files.add(real)
                findings.extend(check_file(base, root))
                doc_count += 1
            continue
        for dirpath, mdfiles in _walk_dirs(base):
            real_dir = os.path.realpath(dirpath)
            if real_dir not in seen_dirs:
                seen_dirs.add(real_dir)
                if mdfiles and "index.md" not in {os.path.basename(f) for f in mdfiles}:
                    rel_dir = os.path.relpath(dirpath, root)
                    findings.append((rel_dir, "index", "missing index.md"))
            for f in mdfiles:
                real_f = os.path.realpath(f)
                if real_f in seen_files:
                    continue
                seen_files.add(real_f)
                findings.extend(check_file(f, root))
                doc_count += 1
    return findings, doc_count


def default_paths(root, cfg):
    names = list(cfg.get("KNOWLEDGE_PATHS", [])) + ["work"]
    out = []
    for name in names:
        full = name if os.path.isabs(name) else os.path.join(root, name)
        if os.path.exists(full):
            out.append(full)
    return out


def main(argv=None):
    a = parse_args(argv)
    root = resolve_root(a.root)
    cfg = load_config(root)

    if a.paths:
        candidates = a.paths
        paths = []
        for p in candidates:
            full = p if os.path.isabs(p) else os.path.join(root, p)
            if os.path.exists(full):
                paths.append(full)
    else:
        paths = default_paths(root, cfg)

    findings, doc_count = scan(paths, root)
    findings.sort(key=lambda t: (t[0], t[1], t[2]))

    for rel, rule, detail in findings:
        print(f"WARN {rel} {rule} {detail}")
    warnings = len(findings)
    print(f"OKF: {doc_count} docs, {warnings} warnings")

    strict = a.strict or (cfg.get("OKF_STRICT", ["0"])[:1] == ["1"])
    sys.exit(1 if (strict and warnings > 0) else 0)


if __name__ == "__main__":
    main()
