#!/usr/bin/env python3
"""Generate work/<slug>/index.md and work/index.md from the artifact chain.

For every work/<slug>/ directory (sorted; '_'-prefixed items included) this
reads the front matter of intent.md, spec.md, plan.md, incident.md (a
missing file -> None) and the last entry of work/<slug>/log.md (via
scripts/log_ledger.py), then writes:

  work/<slug>/index.md   front matter `type: sdlc/work-item`, `id: <slug>`,
                          `title` (intent.md's front-matter title, else its
                          first `# ` heading, else the slug), `description`
                          (intent.md's front-matter description, else ""),
                          `timestamp` (the latest `timestamp` among the four
                          artifacts' front matter, else the last log entry's
                          timestamp, else "1970-01-01T00:00:00Z" -- never the
                          generation time); a bullet linking each artifact
                          that exists, and a "Last gate:" line.

  work/index.md           front matter `type: sdlc/index`, `title: Work
                          items`, `description`, `timestamp` (max of every
                          item's timestamp); a table of every item.

Output is byte-stable: no generation timestamp is ever written, entries are
sorted, and lines end with LF. Running this twice on an unchanged tree
produces identical bytes.

Usage: gen_index.py [--check] [--root DIR]
  --check   render to memory and compare against what's on disk; print each
            file that differs or is missing and exit 1; exit 0 if all match.
  --root    repo root to scan/write under (default: git toplevel, else cwd).
"""
import argparse
import os
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_artifact_chain as cac  # noqa: E402  (front_matter(), reused)
import log_ledger  # noqa: E402

ARTIFACTS = ("intent.md", "spec.md", "plan.md", "incident.md")
DEFAULT_TIMESTAMP = "1970-01-01T00:00:00Z"
INDEX_DESCRIPTION = "Generated index of every work/<slug> item; run scripts/gen_index.py to refresh."


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


def _parse_ts(raw):
    """Return a comparable datetime for an RFC3339-ish string, or None."""
    if not raw:
        return None
    s = raw.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _max_ts(raws):
    """The raw string among `raws` with the latest parseable timestamp, or
    None if none parse."""
    best_raw, best_dt = None, None
    for raw in raws:
        dt = _parse_ts(raw)
        if dt is None:
            continue
        if best_dt is None or dt > best_dt:
            best_dt, best_raw = dt, raw
    return best_raw


def _escape_pipe(s):
    return (s or "").replace("|", "\\|")


def _first_heading(path):
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if line.startswith("# "):
                    return line[2:].strip()
    except OSError:
        pass
    return None


def _work_items(work_dir):
    if not os.path.isdir(work_dir):
        return []
    return sorted(
        name
        for name in os.listdir(work_dir)
        if os.path.isdir(os.path.join(work_dir, name))
    )


def build_item(root, slug):
    """Gather everything needed to render work/<slug>/index.md."""
    item_dir = os.path.join(root, "work", slug)
    fms = {name: cac.front_matter(os.path.join(item_dir, name)) for name in ARTIFACTS}

    intent_fm = fms.get("intent.md") or {}
    title = intent_fm.get("title") or ""
    if not title:
        title = _first_heading(os.path.join(item_dir, "intent.md")) or slug
    description = intent_fm.get("description") or ""

    entries, _malformed = log_ledger.parse(os.path.join(item_dir, "log.md"))
    last_entry = entries[-1] if entries else None

    ts_candidates = [fm.get("timestamp") for fm in fms.values() if fm and fm.get("timestamp")]
    timestamp = _max_ts(ts_candidates)
    if timestamp is None and last_entry is not None:
        timestamp = last_entry.ts
    if timestamp is None:
        timestamp = DEFAULT_TIMESTAMP

    return {
        "slug": slug,
        "fms": fms,
        "title": title,
        "description": description,
        "timestamp": timestamp,
        "last_entry": last_entry,
    }


def render_item_index(item):
    lines = [
        "---",
        "type: sdlc/work-item",
        f"id: {item['slug']}",
        f"title: {item['title']}",
        f"description: {item['description']}",
        f"timestamp: {item['timestamp']}",
        "---",
        f"# {item['title']}",
        "",
    ]
    for name in ARTIFACTS:
        fm = item["fms"].get(name)
        if fm is None:
            continue
        status = fm.get("status", "")
        approved_by = fm.get("approved-by", "")
        desc = fm.get("description", "")
        lines.append(f"- [{name}]({name}) — status: {status}; approved-by: {approved_by}; {desc}")
    lines.append("")
    entry = item["last_entry"]
    lines.append(f"Last gate: {log_ledger.render(entry) if entry else '—'}")
    lines.append("")
    return "\n".join(lines)


def _stage(fms):
    if fms.get("plan.md") is not None:
        return "plan"
    if fms.get("spec.md") is not None:
        return "spec"
    if fms.get("intent.md") is not None:
        return "intent"
    return "—"


def _status_cell(fms, name):
    fm = fms.get(name)
    if not fm:
        return "—"
    return fm.get("status") or "—"


def _last_gate_cell(entry):
    if entry is None:
        return "—"
    return f"{entry.artifact} -> {entry.to_status} by {entry.actor}"


def render_top_index(items):
    timestamp = _max_ts([item["timestamp"] for item in items]) or DEFAULT_TIMESTAMP
    lines = [
        "---",
        "type: sdlc/index",
        "title: Work items",
        f"description: {INDEX_DESCRIPTION}",
        f"timestamp: {timestamp}",
        "---",
        "# Work items",
        "",
        "| slug | title | stage | intent | spec | plan | last gate |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in items:
        slug = item["slug"]
        title = _escape_pipe(item["title"])
        stage = _stage(item["fms"])
        intent_cell = _status_cell(item["fms"], "intent.md")
        spec_cell = _status_cell(item["fms"], "spec.md")
        plan_cell = _status_cell(item["fms"], "plan.md")
        last_gate = _escape_pipe(_last_gate_cell(item["last_entry"]))
        lines.append(
            f"| [{slug}]({slug}/index.md) | {title} | {stage} | {intent_cell} | {spec_cell} | {plan_cell} | {last_gate} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_all(root):
    """Return [(relpath, content), ...] for every generated file, in a
    stable order: each item's index.md (slug order), then work/index.md."""
    work_dir = os.path.join(root, "work")
    slugs = _work_items(work_dir)
    items = [build_item(root, slug) for slug in slugs]
    outputs = [
        (os.path.join("work", item["slug"], "index.md"), render_item_index(item))
        for item in items
    ]
    outputs.append(("work/index.md", render_top_index(items)))
    return outputs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="check for drift instead of writing")
    ap.add_argument("--root", help="repo root to scan/write under (default: git toplevel or cwd)")
    a = ap.parse_args(argv)

    root = resolve_root(a.root)
    outputs = render_all(root)

    if a.check:
        problems = []
        for relpath, content in outputs:
            full = os.path.join(root, relpath)
            want = content.encode("utf-8")
            try:
                with open(full, "rb") as f:
                    have = f.read()
            except FileNotFoundError:
                problems.append(f"{relpath}: missing")
                continue
            if have != want:
                problems.append(f"{relpath}: drifted")
        if problems:
            for p in problems:
                print(p)
            print(f"INDEX: {len(problems)} file(s) drifted")
            sys.exit(1)
        print("INDEX: up to date")
        sys.exit(0)

    for relpath, content in outputs:
        full = os.path.join(root, relpath)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"wrote {relpath}")
    sys.exit(0)


if __name__ == "__main__":
    main()
