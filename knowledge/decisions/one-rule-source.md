---
type: decision
title: One rule source renders CLAUDE.md, GEMINI.md and AGENTS.md
description: Why the eight hard rules live in docs/sdlc/rules fragments and are generated into three context files instead of being maintained per model.
resource: scripts/gen_context_files.py
tags: [context-files, gemini, claude-code, drift, t17]
timestamp: 2026-09-05T04:48:42Z
status: in-review
---
# Decision: one rule source, three context files

## Context
The kit targets repos that run both Claude Code and Gemini CLI. Claude Code reads `CLAUDE.md`; Gemini CLI reads
`GEMINI.md` by default and ignores `AGENTS.md` unless it is added to `context.fileName`; other agents read only
`AGENTS.md` (see [the parity spike](../../docs/sdlc/spikes/gemini-parity.md)). Three hand-maintained memory files means
three divergent memories: the failure mode `docs/sdlc/okf-pairing.md` names — a rule tightened in one file and stale in
the other two, with no signal that they disagree.

## Decision
1. The rules live once, as fragments in `docs/sdlc/rules/*.md`, each with front matter `targets:` (a subset of
   `claude`, `gemini`, `agents`) and `order:`. `scripts/gen_context_files.py` concatenates the fragments a target asks
   for and writes them into that target's file between
   `<!-- BEGIN GENERATED: docs/sdlc/rules … -->` and `<!-- END GENERATED -->`.
2. The target name is derived from the filename in `CONTEXT_FILES`: `CLAUDE.md` → `claude`, `GEMINI.md` → `gemini`,
   `AGENTS.md` → `agents`. Adding a fourth reader is one entry in `.sdlc/config.env` plus a `targets:` edit.
3. **The eight hard rules are byte-identical in all three files.** They live in `10-hard-rules.md`, targeted at all
   three; `scripts/test_gen_context_files.py` extracts the section from the three real outputs and compares it.
   A model-specific caveat may never be a variant of a rule — it is an extra fragment that cites the rule number.
4. Model-specific text is segregated: `40-claude-only.md` (skills `/sdlc-*`, `.claude/hooks/` events, `.claude/agents/`)
   renders only into `CLAUDE.md`; `50-gemini-only.md` (Gemini tool names, the first-run hook trust warning,
   `exit_plan_mode` is not an approved `plan.md`, `.gemini/` is protected like `.claude/hooks/`) only into `GEMINI.md`.
   Neither `GEMINI.md` nor `AGENTS.md` names a Claude-only path.
5. **`AGENTS.md` is generated in full, not a pointer** (spike decision 1): a tool that reads only `AGENTS.md` cannot
   follow a pointer, and the cost is zero once the renderer exists. `AGENTS.md` is *not* added to Gemini's
   `context.fileName`, or Gemini would load the rules twice.
6. Text outside the markers is preserved, so `CLAUDE.md`'s "Lessons learned" section stays hand-editable (rule 7 keeps
   working without a regeneration) while every rule above it is generated.
7. Drift is a `verify.sh` failure, not a convention: `scripts/checks/context-drift.sh` runs
   `gen_context_files.py --check`, which exits 1 listing any file that a regeneration would change.
8. `MAX_CONTEXT_LINES` (120) is enforced per rendered file. It is a repo policy — "keep it to one page" — not a limit
   either CLI imposes; no size cap on Gemini's concatenated context is documented.

## Alternatives rejected
- **Three hand-maintained files.** No signal on divergence; the eight rules are the kit's contract and cannot drift.
- **`GEMINI.md`/`AGENTS.md` as one-line pointers to `CLAUDE.md`.** Neither runtime follows a pointer: Gemini
  concatenates only the context files it discovers, and `@file.md` imports would tie a Gemini-only syntax to a
  Claude-named file.
- **A symlink `AGENTS.md` → `CLAUDE.md`.** Cheapest, but it exports Claude-only paths (`/sdlc-*`, `.claude/agents/`) to
  every other agent and cannot carry the Gemini caveats. Symlinks in git are also a portability tax on Windows adopters.
- **Templating (Jinja-style conditionals) inside one file.** More expressive than fragment filtering and much harder to
  diff; it also needs a dependency, and the kit is stdlib-only.

## Consequences
- Editing `CLAUDE.md` inside the markers is now a build break: change the fragment and rerun the generator.
- The H1 is shared, so it reads `# Repository memory (keep to ~1 page)` in all three files rather than naming one file.
- `scripts/adopt.sh` (T22) renders context files into the target repo instead of copying `CLAUDE.md`.
- Follow-ups, both done: `.gemini` is in `PROTECTED_PATHS` (`.sdlc/config.env`); "Lessons learned" moved into
  `knowledge/lessons/` with a pointer fragment (`docs/sdlc/rules/60-lessons.md`, `work/docs-reconcile`), so Gemini and
  third-party agents see lessons too.
