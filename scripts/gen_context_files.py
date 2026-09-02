#!/usr/bin/env python3
"""Render the context files in CONTEXT_FILES from the rule fragments in RULES_SRC.

One rule source, three readers: `docs/sdlc/rules/*.md` fragments carry front matter
with `targets:` and `order:`; this script concatenates the fragments a target asks
for and writes them into that target's context file, between

    <!-- BEGIN GENERATED: docs/sdlc/rules — edit the fragments, run scripts/gen_context_files.py -->
    <!-- END GENERATED -->

Target names come from CONTEXT_FILES: CLAUDE.md -> claude, GEMINI.md -> gemini,
AGENTS.md -> agents. Text outside the markers (a hand-kept "Lessons learned"
section, for example) is preserved verbatim; a file that does not exist yet is
created whole; an existing file with no markers keeps its text and gains the block
at the end.

Exit 1 without writing anything on: a BEGIN marker without an END (or the reverse,
or either one twice), a fragment whose body contains a marker line, a fragment with
an unknown target, a missing/blank `targets:` or `order:`, or a rendered file longer
than MAX_CONTEXT_LINES.

Usage:
  scripts/gen_context_files.py [--check] [--root DIR]
    --check   render to memory and exit 1 listing the files that would change
              (or are over-length); exit 0 when everything is up to date.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import check_artifact_chain as chain  # noqa: E402  reuse front_matter()/config()

DEFAULT_ROOT = os.path.dirname(HERE)
BEGIN_PREFIX = "<!-- BEGIN GENERATED:"
END_MARKER = "<!-- END GENERATED -->"


class RenderError(Exception):
    """A fragment, a marker or a length budget is wrong; nothing gets written."""


class Fragment(object):
    def __init__(self, name, targets, order, body):
        self.name = name
        self.targets = targets
        self.order = order
        self.body = body


def begin_marker(rules_src):
    return "%s %s — edit the fragments, run scripts/gen_context_files.py -->" % (
        BEGIN_PREFIX,
        rules_src,
    )


def is_begin(line):
    s = line.strip()
    return s.startswith(BEGIN_PREFIX) and s.endswith("-->")


def is_end(line):
    return line.strip() == END_MARKER


def config(root):
    """Read .sdlc/config.env under `root` with check_artifact_chain's reader."""
    previous = chain.ROOT
    chain.ROOT = root
    try:
        return chain.config()
    finally:
        chain.ROOT = previous


def read_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read().replace("\r\n", "\n")


def strip_front_matter(text):
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return text
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[idx + 1:])
    return text


def parse_targets(raw, name):
    if raw is None:
        raise RenderError("%s: front matter has no 'targets:'" % name)
    value = raw.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    targets = [t.strip().strip("\"'") for t in value.split(",")]
    targets = [t for t in targets if t]
    if not targets:
        raise RenderError("%s: 'targets:' is empty" % name)
    return targets


def parse_order(raw, name):
    if raw is None:
        raise RenderError("%s: front matter has no 'order:'" % name)
    try:
        return int(raw.strip())
    except ValueError:
        raise RenderError("%s: 'order: %s' is not an integer" % (name, raw.strip()))


def load_fragments(rules_dir, known_targets):
    """Every *.md in `rules_dir`, in (order, filename) order, as Fragments."""
    if not os.path.isdir(rules_dir):
        raise RenderError("rule source directory %s does not exist" % rules_dir)
    fragments = []
    # index.md is the OKF index of the fragment directory, never a fragment itself.
    for name in sorted(n for n in os.listdir(rules_dir) if n.endswith(".md") and n != "index.md"):
        path = os.path.join(rules_dir, name)
        front = chain.front_matter(path) or {}
        targets = parse_targets(front.get("targets"), name)
        order = parse_order(front.get("order"), name)
        for target in targets:
            if target not in known_targets:
                raise RenderError(
                    "%s: unknown target '%s' (known: %s)"
                    % (name, target, ", ".join(sorted(known_targets)))
                )
        body = strip_front_matter(read_text(path)).strip("\n")
        for lineno, line in enumerate(body.split("\n"), 1):
            if is_begin(line) or is_end(line):
                raise RenderError(
                    "%s:%d: fragment body contains a generated-block marker" % (name, lineno)
                )
        fragments.append(Fragment(name, targets, order, body))
    fragments.sort(key=lambda f: (f.order, f.name))
    return fragments


def render_block(fragments, target, rules_src):
    bodies = [f.body for f in fragments if target in f.targets]
    lines = [begin_marker(rules_src)] + ("\n\n".join(bodies).split("\n") if bodies else [])
    lines.append(END_MARKER)
    return "\n".join(lines) + "\n"


def apply_block(existing, block, name):
    """Splice `block` into `existing` (None when the file does not exist)."""
    if existing is None or not existing.strip():
        return block
    lines = existing.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    begins = [i for i, line in enumerate(lines) if is_begin(line)]
    ends = [i for i, line in enumerate(lines) if is_end(line)]
    if len(begins) > 1 or len(ends) > 1:
        raise RenderError("%s: more than one generated block" % name)
    if begins and not ends:
        raise RenderError("%s: BEGIN GENERATED marker without an END GENERATED marker" % name)
    if ends and not begins:
        raise RenderError("%s: END GENERATED marker without a BEGIN GENERATED marker" % name)
    if not begins:
        return "\n".join(lines).rstrip("\n") + "\n\n" + block
    if ends[0] < begins[0]:
        raise RenderError("%s: END GENERATED marker before BEGIN GENERATED" % name)
    merged = lines[: begins[0]] + block.rstrip("\n").split("\n") + lines[ends[0] + 1:]
    return "\n".join(merged).rstrip("\n") + "\n"


def render_all(root):
    """{filename: rendered text} for every file in CONTEXT_FILES."""
    cfg = config(root)
    names = cfg.get("CONTEXT_FILES", [])
    if not names:
        raise RenderError("CONTEXT_FILES is empty in .sdlc/config.env")
    rules_src = (cfg.get("RULES_SRC") or ["docs/sdlc/rules"])[0]
    targets = dict((n, os.path.splitext(n)[0].lower()) for n in names)
    fragments = load_fragments(os.path.join(root, rules_src), set(targets.values()))
    rendered = {}
    for name in names:
        path = os.path.join(root, name)
        existing = read_text(path) if os.path.exists(path) else None
        rendered[name] = apply_block(existing, render_block(fragments, targets[name], rules_src), name)
    return rendered


def over_length(rendered, root):
    """Files whose render exceeds MAX_CONTEXT_LINES, as ready-to-print messages."""
    raw = config(root).get("MAX_CONTEXT_LINES")
    if not raw:
        return []
    limit = int(raw[0])
    problems = []
    for name in sorted(rendered):
        count = len(rendered[name].splitlines())
        if count > limit:
            problems.append("%s: %d lines, over MAX_CONTEXT_LINES=%d" % (name, count, limit))
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="report drift instead of writing; exit 1 if any file would change")
    parser.add_argument("--root", default=DEFAULT_ROOT, help="repository root (default: this repo)")
    args = parser.parse_args(argv)
    root = os.path.abspath(args.root)

    try:
        rendered = render_all(root)
        problems = over_length(rendered, root)
    except RenderError as exc:
        print("gen_context_files: %s" % exc, file=sys.stderr)
        return 1
    if problems:
        for problem in problems:
            print("gen_context_files: %s" % problem, file=sys.stderr)
        return 1

    stale = []
    for name in sorted(rendered):
        path = os.path.join(root, name)
        current = read_text(path) if os.path.exists(path) else None
        if current != rendered[name]:
            stale.append(name)
    if args.check:
        if stale:
            for name in stale:
                print("gen_context_files: %s is out of date (run scripts/gen_context_files.py)" % name,
                      file=sys.stderr)
            return 1
        print("CONTEXT: %d files up to date" % len(rendered))
        return 0
    for name in sorted(rendered):
        path = os.path.join(root, name)
        if name in stale:
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(rendered[name])
        print("%s %s (%d lines)" % ("wrote  " if name in stale else "same   ",
                                    name, len(rendered[name].splitlines())))
    print("CONTEXT: %d files rendered, %d changed" % (len(rendered), len(stale)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
