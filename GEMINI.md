<!-- BEGIN GENERATED: docs/sdlc/rules — edit the fragments, run scripts/gen_context_files.py -->
# Repository memory (keep to ~1 page)

This repo is a starter kit for the AI-native SDLC: six non-linear stages
(Plan → Design → Build → Test → Deploy → Maintain) connected by committed
Markdown artifacts. Read `docs/sdlc/README.md` once; then follow the rules below.

## The artifact chain (never skip a link)
intent.md → spec.md → plan.md → diff + tests → PR + review findings → incident record → new intent.md

Each work item lives in `work/<slug>/` and holds `intent.md`, `spec.md`, `plan.md`
(and later `incident.md`). Every artifact has YAML front matter with `status`
(`draft` | `in-review` | `approved` | `superseded`) and `approved-by`. Only a
human sets `status: approved`. The active work item is named in `.sdlc/active`.

## Hard rules (enforced by hooks and CI, not by good intentions)
1. No code edits under the paths in `.sdlc/config.env` (`PLAN_REQUIRED_PATHS`)
   unless the active work item has an **approved** `plan.md`. A plan with `kind: fix`
   also locks test files: reproduce the bug as a failing test first, then fix the code.
2. If implementation deviates from `plan.md`, update `plan.md` in the same commit.
   CI fails a PR whose diff touches files not listed in the plan.
3. Never edit `.claude/hooks/`, `.github/workflows/`, `.sdlc/`, or secret files.
   Propose the change in the PR description instead.
4. Never deploy, publish, or push to a protected branch. The production gate hook
   stops you; a human authorizes releases.
5. Run `scripts/verify.sh` before asking for review. Paste its last line in the PR.
6. Review findings cite `file:line` and evidence. Max five minor comments per review.
7. A mistake made twice becomes a line in this file or a skill, in the same PR.
8. Subagents have a named role in the agent directory (`.claude/agents/`,
   `.gemini/agents/`), bounded tools, and must return evidence (paths, commands,
   outputs), not opinions.

## Verifying your work
- Verify everything: `scripts/verify.sh` — must end with `VERIFY: PASS (<sha>)`
- Artifact chain for a PR: `python3 scripts/check_artifact_chain.py --base origin/main` — must end with `CHAIN: PASS`
- Evals: `scripts/run_evals.sh` — must end with `EVALS: N pass, 0 fail, ...` (see `evals/README.md`)
Run all of them before reporting a task complete and paste the last lines. If a test fails, fix the code, not the test.
- Band detector: `python3 scripts/detect_bands.py --series ...` (exit 3 = breach); metrics: `scripts/sdlc_metrics.py`

## Workflow
One stage at a time: write `intent.md`, then `spec.md`, then `plan.md`, then implement,
then review, and file `incident.md` when something breaks. Templates for each artifact
are in `docs/sdlc/templates/`. Do not start an artifact until a human has approved the
previous one.

## Conventions
- Branch: `work/<slug>`. PR title starts with `[<slug>]`. PR body has `Work-Item: <slug>`.
- Commit messages explain *why*; reference the work item slug.
- Tests live next to the code they test; every bug fix adds a regression test.

## Gemini CLI notes
- Hooks are `BeforeTool` entries in `.gemini/settings.json` and match Gemini tool names
  (`write_file`, `replace`, `run_shell_command`), not `Edit|Write|MultiEdit`.
- A project hook that is new or whose command changed warns before it runs, so a local
  block can be skipped on first run. The CI gate (`sdlc-gate`) is the authoritative red line.
- Leaving plan mode with `exit_plan_mode` is **not** an approved `plan.md`. Rule 1 is
  satisfied only by `work/<slug>/plan.md` with `status: approved` set by a human.
- Treat `.gemini/` (settings, agents, policies) as protected exactly like `.claude/hooks/`
  in rule 3: propose the change in the PR description instead of editing it.
<!-- END GENERATED -->
