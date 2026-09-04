---
type: sdlc/work-item
id: control-plane-visibility
title: Hook decisions must be logged; the control-plane unlock must be visible; CI must recognise the kit's own agent PRs
description: The unlock's audit line goes to stderr on exit 0 where Claude Code never shows it, check_control_plane.sh never matched the kit's kit/* branches, and no hook decision is recorded anywhere durable.
timestamp: 2026-09-04T21:46:58Z
---
# Hook decisions must be logged; the control-plane unlock must be visible; CI must recognise the kit's own agent PRs

- [intent.md](intent.md) — status: in-review; approved-by: ; The unlock's audit line goes to stderr on exit 0 where Claude Code never shows it, check_control_plane.sh never matched the kit's kit/* branches, and no hook decision is recorded anywhere durable.
- [spec.md](spec.md) — status: in-review; approved-by: ; A tab-separated decision log written by every hook, a systemMessage on every unlocked write, three never-unlock paths, and agent detection by branch prefix list or commit trailer in check_control_plane.sh.
- [plan.md](plan.md) — status: in-review; approved-by: ; Add log_decision and the A1 helpers to _lib.sh, a systemMessage and never-unlock list to protect-paths.sh, a prefix list and trailer scan to check_control_plane.sh, with tests, two evals and the doc corrections.

Last gate: - 2026-09-04T21:55:16Z | plan.md | (none) -> in-review | claude | 64bcb17 | same
