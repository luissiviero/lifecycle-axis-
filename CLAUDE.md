# CLAUDE.md — repository memory (keep to ~1 page)

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
   unless the active work item has an **approved** `plan.md`.
2. If implementation deviates from `plan.md`, update `plan.md` in the same commit.
   CI fails a PR whose diff touches files not listed in the plan.
3. Never edit `.claude/hooks/`, `.github/workflows/`, `.sdlc/`, or secret files.
   Propose the change in the PR description instead.
4. Never deploy, publish, or push to a protected branch. The production gate hook
   stops you; a human authorizes releases.
5. Run `scripts/verify.sh` before asking for review. Paste its last line in the PR.
6. Review findings cite `file:line` and evidence. Max five minor comments per review.
7. A mistake made twice becomes a line in this file or a skill, in the same PR.
8. Subagents have a named role in `.claude/agents/`, bounded tools, and must
   return evidence (paths, commands, outputs), not opinions.

## Commands
- Verify everything: `scripts/verify.sh` (exit code is the answer)
- Check the artifact chain for a PR: `scripts/check_artifact_chain.py --base origin/main`
- Run evals: `scripts/run_evals.sh` (see `evals/README.md`)

## Workflow entry points (skills)
`/sdlc-intent` → `/sdlc-spec` → `/sdlc-plan` → implement → `/sdlc-review` → `/sdlc-incident`

## Conventions
- Branch: `work/<slug>`. PR title starts with `[<slug>]`. PR body has `Work-Item: <slug>`.
- Commit messages explain *why*; reference the work item slug.
- Tests live next to the code they test; every bug fix adds a regression test.

## Lessons learned (append; one line each; delete when a hook makes it impossible)
- (none yet)
