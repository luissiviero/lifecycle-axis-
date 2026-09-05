#!/usr/bin/env python3
"""Every tracked Markdown front matter must parse as strict YAML (work/docs-reconcile R-6).

The kit's own front-matter reader (scripts/check_artifact_chain.py) splits `key: value` on the first
colon and tolerates `title: Metrics: one thing`. GitHub's renderer and every strict YAML reader do not:
they show an error banner instead of the document. This check runs where `verify.sh` runs, so the
defect is caught before the push, not on a phone.

Two modes, named in the last line:
  - PyYAML present: `yaml.safe_load` on the block; a parse error or a block that is not a mapping is a
    problem, reported as `<path>:<line>: <first line of the error>` with the file line number.
  - PyYAML absent (or --no-yaml): a structural pass over each `key: value` line; an unquoted plain
    scalar that contains `: ` or ` #`, or starts with a YAML indicator, is a problem. This is the rule
    that catches every failure the kit's documents have had; it is not a YAML parser.

Files come from `git ls-files -- '*.md'` under --root; a file whose first line is not `---` has no
front matter and is skipped (not counted). CRLF is folded to LF before comparing (CLAUDE.md lesson).
`--stdin` checks one document from standard input instead (path `<stdin>`).

Usage: scripts/check_front_matter.py [--root DIR] [--stdin] [--no-yaml]
Last line: `FRONT-MATTER: N docs, M problems (PyYAML|structural)`; exit 1 when M > 0, 2 on a bad argument.
"""
import argparse, os, re, subprocess, sys

KEY_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.-]*):(?:[ \t]+(.*))?$")
INDICATORS = "&*!|>%@`"


def split_front_matter(text):
    """Return (block_lines, first_block_line_number) or (None, 0) when the file has no front matter.

    `block_lines` excludes the two `---` fences; the number is the 1-based file line of the first
    block line (always 2). A missing closing fence returns the rest of the file as the block."""
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return None, 0
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], 2
    return lines[1:], 2


def check_with_yaml(block, first_line, yaml):
    try:
        data = yaml.safe_load("\n".join(block))
    except yaml.YAMLError as exc:  # pragma: no cover - message shape depends on PyYAML
        mark = getattr(exc, "problem_mark", None)
        line = first_line + (mark.line if mark is not None else 0)
        problem = getattr(exc, "problem", None) or str(exc).splitlines()[0]
        return [(line, problem)]
    if not isinstance(data, dict):
        return [(first_line - 1, "front matter is not a mapping")]
    return []


def check_structurally(block, first_line):
    problems = []
    if block and not any(KEY_LINE.match(l) for l in block):
        return [(first_line - 1, "front matter is not a mapping")]
    for offset, raw in enumerate(block):
        line = first_line + offset
        if not raw.strip() or raw.lstrip().startswith("#") or raw.startswith((" ", "\t")):
            continue
        m = KEY_LINE.match(raw)
        if not m:
            problems.append((line, "not a `key: value` line"))
            continue
        value = (m.group(2) or "").strip()
        if not value:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            continue
        if value[0] in "[{":
            continue
        if value[0] in INDICATORS:
            problems.append((line, "value starts with a YAML indicator %r; quote the whole value" % value[0]))
        elif ": " in value or " #" in value:
            problems.append((line, "unquoted value contains ': ' or ' #'; quote the whole value"))
    return problems


def check_text(text, path, yaml):
    block, first = split_front_matter(text)
    if block is None:
        return None
    found = check_with_yaml(block, first, yaml) if yaml else check_structurally(block, first)
    return ["%s:%d: %s" % (path, line, msg) for line, msg in found]


def tracked_markdown(root):
    try:
        out = subprocess.run(
            ["git", "-C", root, "ls-files", "-z", "--", "*.md", "**/*.md"],
            capture_output=True, text=True, check=True,
        ).stdout
        names = [n for n in out.split("\0") if n]
    except (subprocess.CalledProcessError, OSError):
        names = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d != ".git"]
            for f in filenames:
                if f.endswith(".md"):
                    names.append(os.path.relpath(os.path.join(dirpath, f), root))
    return sorted(set(names))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=None, help="repository root (default: git toplevel of the cwd)")
    ap.add_argument("--stdin", action="store_true", help="check one document read from standard input")
    ap.add_argument("--no-yaml", action="store_true", help="force the structural fallback")
    try:
        args = ap.parse_args(argv)
    except SystemExit:
        return 2
    yaml = None
    if not args.no_yaml:
        try:
            import yaml as _yaml
            yaml = _yaml
        except ImportError:
            yaml = None
    mode = "PyYAML" if yaml else "structural"

    docs = problems = 0
    if args.stdin:
        found = check_text(sys.stdin.read(), "<stdin>", yaml)
        if found is not None:
            docs = 1
            for line in found:
                print(line)
            problems = len(found)
    else:
        root = args.root or subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
        ).stdout.strip() or os.getcwd()
        for rel in tracked_markdown(root):
            full = os.path.join(root, rel)
            try:
                with open(full, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            found = check_text(text, rel, yaml)
            if found is None:
                continue
            docs += 1
            for line in found:
                print(line)
            problems += len(found)
    print("FRONT-MATTER: %d docs, %d problems (%s)" % (docs, problems, mode))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
