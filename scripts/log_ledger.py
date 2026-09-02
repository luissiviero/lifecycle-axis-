#!/usr/bin/env python3
"""Parse and render work/<slug>/log.md gate ledgers.

Ledger line format (append-only, one entry per line):
  - <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>
`<note>` is optional, so a well-formed line has 5 or 6 '|'-separated fields.
Everything else in the file (front matter, the heading, the "Format:" line,
blank lines, comments) is ignored.

Public API:
  parse(path) -> (entries: list[Entry], malformed: list[tuple[int, str]])
  approvals(entries, artifact) -> list[Entry]
  render(entry) -> str
  normalize(handle) -> str
"""
import sys
from collections import namedtuple
from datetime import datetime

Entry = namedtuple("Entry", "ts artifact from_status to_status actor sha note lineno")


def normalize(handle):
    """Normalize an actor handle: strip quotes, keep the first token, strip
    a leading '@', casefold. Duplicated from scripts/approvers.py's rule
    (not imported: that module may not exist yet in this repo)."""
    h = handle.strip().strip("\"'")
    h = h.split()[0] if h.split() else ""
    h = h.lstrip("@")
    return h.casefold()


def _parse_ts(raw):
    s = raw.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _strip_front_matter(lines):
    """Return (start_index) of the first line after a leading '---' ... '---'
    front-matter block, or 0 if the file has none."""
    if not lines or lines[0].strip() != "---":
        return 0
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return idx + 1
    return len(lines)  # unterminated front matter: nothing left to parse


def parse(path):
    """Parse a log.md ledger. Returns (entries, malformed); missing file ->
    ([], []). Entries are returned in file order."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        return [], []

    entries, malformed = [], []
    start = _strip_front_matter(lines)

    for i in range(start, len(lines)):
        raw_line = lines[i]
        lineno = i + 1
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if not stripped.startswith("- "):
            continue

        body = stripped[2:]
        fields = [f.strip() for f in body.split("|")]
        if len(fields) not in (5, 6):
            malformed.append((lineno, raw_line))
            continue

        ts_raw, artifact, arrow, actor_raw, sha = fields[:5]
        note = fields[5] if len(fields) == 6 else ""

        if "->" not in arrow:
            malformed.append((lineno, raw_line))
            continue
        from_status, to_status = (p.strip() for p in arrow.split("->", 1))

        try:
            _parse_ts(ts_raw)
        except ValueError:
            malformed.append((lineno, raw_line))
            continue

        entries.append(
            Entry(
                ts=ts_raw,
                artifact=artifact,
                from_status=from_status,
                to_status=to_status,
                actor=normalize(actor_raw),
                sha=sha,
                note=note,
                lineno=lineno,
            )
        )

    return entries, malformed


def approvals(entries, artifact):
    """Entries that transitioned `artifact` to status 'approved'."""
    return [e for e in entries if e.to_status == "approved" and e.artifact == artifact]


def render(entry):
    """Render the exact ledger line an agent should append for `entry`."""
    parts = [
        entry.ts,
        entry.artifact,
        f"{entry.from_status} -> {entry.to_status}",
        entry.actor,
        entry.sha,
    ]
    line = "- " + " | ".join(parts)
    if entry.note:
        line += " | " + entry.note
    return line


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: log_ledger.py <path/to/log.md>", file=sys.stderr)
        sys.exit(2)
    target = sys.argv[1]
    parsed_entries, bad_lines = parse(target)
    for entry in parsed_entries:
        print(render(entry))
    for lineno, line in bad_lines:
        print(f"MALFORMED line {lineno}: {line}", file=sys.stderr)
    sys.exit(1 if bad_lines else 0)
