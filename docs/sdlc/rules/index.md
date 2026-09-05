---
type: index
title: Rule fragments
description: One rule source rendered by scripts/gen_context_files.py into CLAUDE.md, GEMINI.md and AGENTS.md.
tags: [okf, index, rules, context-files]
timestamp: 2026-09-05T04:48:42Z
---
# Rule fragments

The fragments below are the one rule source. `scripts/gen_context_files.py` renders them, in `(order, filename)` order and
filtered by each fragment's `targets`, into the block between `<!-- BEGIN GENERATED: docs/sdlc/rules — … -->` and `<!-- END GENERATED -->`
in `CLAUDE.md`, `GEMINI.md` and `AGENTS.md`. Edit a fragment, re-run the script; never hand-edit the generated block.
This index is not a fragment and is skipped by the renderer.

- [00-chain.md](00-chain.md) — the artifact chain (all targets)
- [10-hard-rules.md](10-hard-rules.md) — the eight hard rules, byte-identical across targets
- [20-verifying.md](20-verifying.md) — verification commands and healthy output
- [30-conventions.md](30-conventions.md) — workflow and conventions
- [40-claude-only.md](40-claude-only.md) — skills, hooks and subagents (Claude only)
- [50-gemini-only.md](50-gemini-only.md) — Gemini CLI notes (Gemini only)
- [60-lessons.md](60-lessons.md) — the lessons pointer list: one line per file in `knowledge/lessons/` (all targets)
