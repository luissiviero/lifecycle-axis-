#!/usr/bin/env python3
"""Git-derived SDLC metrics per work item: first commit of intent, spec, plan; rework counts.
Usage: scripts/sdlc_metrics.py [--json]"""
import json, os, subprocess, sys
ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
def first_ts(path):
    out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%ct", "--", path], capture_output=True, text=True, cwd=ROOT).stdout.split()
    return int(out[-1]) if out else None
def commits_after(path, ts):
    if ts is None: return 0
    out = subprocess.run(["git", "log", f"--since=@{ts}", "--format=%H", "--", path], capture_output=True, text=True, cwd=ROOT).stdout.split()
    return max(0, len(out) - 1)
rows = []
for slug in sorted(os.listdir(os.path.join(ROOT, "work"))):
    d = os.path.join("work", slug)
    if not os.path.isdir(os.path.join(ROOT, d)): continue
    i, s, p = (first_ts(os.path.join(d, f)) for f in ("intent.md", "spec.md", "plan.md"))
    rows.append({"work_item": slug,
                 "intent_to_spec_hours": round((s - i) / 3600, 1) if i and s else None,
                 "spec_to_plan_hours": round((p - s) / 3600, 1) if s and p else None,
                 "spec_rework_after_plan": commits_after(os.path.join(d, "spec.md"), p),
                 "intent_rework_after_spec": commits_after(os.path.join(d, "intent.md"), s)})
if "--json" in sys.argv: print(json.dumps(rows, indent=2))
else:
    for r in rows: print(r)
