#!/usr/bin/env python3
"""Fail on GitHub Actions workflows that are not read-only-safe.

Minimal YAML-ish reader (no PyYAML dependency) that checks every
`.github/workflows/*.yml` (or the files given on the command line) for:
  (a) a top-level `permissions:` key exists (`permissions: read-all` and
      `permissions: {}` both count as present; `permissions: write-all`
      is rejected separately by rule (d)).
  (b) no `contents: write` at workflow or job level, except an allowlist
      constant below -- empty in this repo, so `contents: write` is
      never allowed.
  (c) no `pull_request_target` anywhere (most commonly an `on:` event).
  (d) no `permissions: write-all` anywhere.

Comments (`#` to end of line, outside quotes) are stripped before any
rule is checked, so a comment that happens to contain "contents: write"
or "pull_request_target" is never a violation.

YAML anchors and aliases (a value beginning with `&` or `*`) are
rejected outright as an unsupported feature: this reader does not
resolve them, and silently misreading an aliased `permissions:` block
would be worse than refusing the file.

Output: one `VIOLATION <file>:<line> <rule> <detail>` line per finding,
then a final `WORKFLOWS: <N> files, <V> violations` line. Exit 1 if any
violation was found, 0 otherwise.
"""
import argparse
import glob
import os
import re
import subprocess
import sys

# Rule (b) allowlist: workflow files permitted to declare `contents: write`.
# Empty -- this repo grants no exceptions. A workflow that legitimately
# needs to write should narrow the permission to itself and add its path
# here in a reviewed PR, not by editing around this checker.
CONTENTS_WRITE_ALLOWLIST = ()

CONTENTS_WRITE_RE = re.compile(r"(?<![\w-])contents\s*:\s*['\"]?write['\"]?(?![\w-])")
PERMISSIONS_WRITE_ALL_RE = re.compile(
    r"(?<![\w-])permissions\s*:\s*['\"]?write-all['\"]?(?![\w-])"
)
PULL_REQUEST_TARGET_RE = re.compile(r"\bpull_request_target\b")
TOP_LEVEL_PERMISSIONS_RE = re.compile(r"^permissions\s*:")
KEY_RE = re.compile(r"^(?P<indent>[ ]*)(?:-\s+)?(?P<key>[A-Za-z0-9_.\-]+):(?P<rest>.*)$")


def repo_root():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except OSError:
        pass
    return os.getcwd()


def strip_comment(line):
    """Remove a trailing `# comment`, respecting single/double-quoted strings."""
    in_single = in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            return line[:i]
    return line


def read_lines(path):
    """Yield (lineno, comment-stripped line) for every non-blank line."""
    with open(path, encoding="utf-8") as f:
        raw = f.readlines()
    for i, orig in enumerate(raw, start=1):
        line = strip_comment(orig.rstrip("\n"))
        if line.strip():
            yield i, line


def value_is_anchor_or_alias(value):
    v = value.strip()
    if not v or v[0] in ("'", '"'):
        return False
    return v[0] in ("&", "*")


def check_anchors_aliases(lines):
    violations = []
    for lineno, line in lines:
        m = KEY_RE.match(line)
        if m:
            if value_is_anchor_or_alias(m.group("rest")):
                violations.append(
                    (lineno, "unsupported-yaml-feature", "anchors/aliases are not supported by this checker")
                )
            continue
        stripped = line.strip()
        if stripped.startswith("- ") and value_is_anchor_or_alias(stripped[2:]):
            violations.append(
                (lineno, "unsupported-yaml-feature", "anchors/aliases are not supported by this checker")
            )
    return violations


def check_pull_request_target(lines):
    return [
        (lineno, "pull-request-target", "pull_request_target must not be used")
        for lineno, line in lines
        if PULL_REQUEST_TARGET_RE.search(line)
    ]


def check_contents_write(lines, path):
    if path in CONTENTS_WRITE_ALLOWLIST:
        return []
    return [
        (lineno, "contents-write", "contents: write is not allowed (no allowlist entry for this file)")
        for lineno, line in lines
        if CONTENTS_WRITE_RE.search(line)
    ]


def check_write_all(lines):
    return [
        (lineno, "permissions-write-all", "permissions: write-all grants full write access")
        for lineno, line in lines
        if PERMISSIONS_WRITE_ALL_RE.search(line)
    ]


def check_top_level_permissions(lines):
    for _, line in lines:
        if TOP_LEVEL_PERMISSIONS_RE.match(line):
            return []
    return [(1, "missing-permissions", "workflow has no top-level `permissions:` key")]


def check_file(path):
    lines = list(read_lines(path))
    violations = []
    violations += check_anchors_aliases(lines)
    violations += check_pull_request_target(lines)
    violations += check_contents_write(lines, path)
    violations += check_write_all(lines)
    violations += check_top_level_permissions(lines)
    return sorted(violations, key=lambda v: v[0])


def default_files(root):
    return sorted(glob.glob(os.path.join(root, ".github", "workflows", "*.yml")))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=None, help="repo root (default: git toplevel, else cwd)")
    ap.add_argument("files", nargs="*", help="workflow files to check (default: .github/workflows/*.yml under --root)")
    a = ap.parse_args(argv)

    root = a.root or repo_root()
    files = a.files if a.files else default_files(root)

    total = 0
    for path in files:
        for lineno, rule, detail in check_file(path):
            print(f"VIOLATION {path}:{lineno} {rule} {detail}")
            total += 1
    print(f"WORKFLOWS: {len(files)} files, {total} violations")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
