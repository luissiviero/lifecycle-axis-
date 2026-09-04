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
3. Never edit `.claude/hooks/`, `.gemini/`, `.github/workflows/`, `.sdlc/`, or secret
   files. Propose the change in the PR description instead.
4. Never deploy, publish, or push to a protected branch. The production gate hook
   stops you; a human authorizes releases.
5. Run `scripts/verify.sh` before asking for review. Paste its last line in the PR.
6. Review findings cite `file:line` and evidence. Max five minor comments per review.
7. A mistake made twice becomes a line in this file or a skill, in the same PR.
8. Subagents have a named role in the agent directory (`.claude/agents/`,
   `.gemini/agents/`), bounded tools, and must return evidence (paths, commands,
   outputs), not opinions.

## Verifying your work
- Verify everything: `scripts/verify.sh` — must end with `VERIFY: PASS (<sha>)`; it also runs every `scripts/checks/*.sh`
- Artifact chain for a PR: `python3 scripts/check_artifact_chain.py --base origin/main` — must end with `CHAIN: PASS`
- Evals: `scripts/run_evals.sh` — must end with `EVALS: N pass, 0 fail, ...` (`--kind`/`--only`/`--list` select cases; see `evals/README.md`)
- OKF conformance: `python3 scripts/check_okf.py` — must end with `OKF: N docs, 0 warnings` (warning-only unless `OKF_STRICT=1`)
Run all of them before reporting a task complete and paste the last lines. If a test fails, fix the code, not the test.
- Regenerate before committing — verify fails on drift: `python3 scripts/gen_index.py` and `python3 scripts/gen_context_files.py`
- Band detector: `python3 scripts/detect_bands.py --series ...` (exit 3 = breach); metrics: `scripts/sdlc_metrics.py`
- Keep this file under `MAX_CONTEXT_LINES` (120): `wc -l CLAUDE.md` after regenerating; trim prose, never rules, if over

## Workflow
One stage at a time: write `intent.md`, then `spec.md`, then `plan.md`, then implement,
then review, and file `incident.md` when something breaks. Templates for each artifact
are in `docs/sdlc/templates/`. Do not start an artifact until a human has approved the
previous one.

## Conventions
- Branch: `work/<slug>`. PR title starts with `[<slug>]`. PR body has `Work-Item: <slug>`.
- Commit messages explain *why*; reference the work item slug.
- Tests live next to the code they test; every bug fix adds a regression test.
- `work/<slug>/log.md` gets an entry at every gate (format in `docs/sdlc/templates/log.md`); `approved-by` must be a
  handle from `.sdlc/approvers.yaml`; decisions go to `knowledge/decisions/`; institutional knowledge goes to
  `knowledge/`, and CLAUDE.md/GEMINI.md link to it rather than restating it.
- Humans approve with `python3 scripts/approve.py <slug> <artifact>` from their own shell, then commit. It refuses
  to run inside an agent session; an agent asks for approval and waits.

## Workflow entry points (skills)
`/sdlc-intent` → `/sdlc-spec` → `/sdlc-plan` → implement → `/sdlc-review` → `/sdlc-incident`
- Hooks in `.claude/hooks/` enforce rules 1, 3 and 4 as `PreToolUse` matchers on
  `Edit|Write|MultiEdit|Bash`, plus a `Stop` reminder for rule 5. They read
  `.sdlc/config.env` under `$CLAUDE_PROJECT_DIR`; a block is `exit 2` with the reason on stderr.
- Subagents live in `.claude/agents/` with a named role and a bounded `tools:` list.
<!-- END GENERATED -->

## Lessons learned (append; one line each; delete when a hook makes it impossible)
- This repo runs its own hooks with `SDLC_CONTROL_PLANE_UNLOCK=1` set in `.claude/settings.json` (`knowledge/decisions/self-hooks-on.md`): control-plane writes pass with one audit line each, so rule 3 is advisory here and CI plus the owner's review guard the control plane. Restart the session after changing hook wiring.
- A guard that compares paths must compare one spelling: three separate bypasses came from a Windows path form the comparison did not recognise (`C:\...` read as relative; a POSIX path under an MSYS mount like `/tmp` left unconverted by `winpath()`), and each one made the hook *allow* silently. Normalise through `canon()`/`winpath()` and never widen a guard's input without a test. A skipped guard test is not a passing one: the third hid behind a test that could not run on Windows until Developer Mode was enabled.
- The hooks need `jq` and refuse every edit without it (`knowledge/decisions/gemini-hooks.md`). Test a `_lib.sh` change from a second shell before the session that made it relies on it: a bad edit there locks the session out of Edit, Write and Bash at once.
- A drift check that compares bytes is wrong on a Windows checkout: `core.autocrlf` hands back CRLF while the generators write LF, so `gen_context_files.py --check` and then `gen_index.py --check` each reported drift on a clean tree until CRLF was normalised before comparing. Any new `--check` compares with `\r\n` folded to `\n`, and a drift report on a file nobody edited is the first thing to suspect.
- A skill or agent that names a template's field or heading must spell it as the template does: `/sdlc-spec` said `standards-applied` where `templates/spec.md` says `skills-applied`, and `/sdlc-plan` plus both `plan-reviewer` agents said `## Files` and `## Verification` where `templates/plan.md` says `## Files that change` and `## Proof`; the wrong spelling shipped into `work/_example/spec.md` before anyone noticed. Eval `skill-names-match-templates` pins the spellings; when a template field or heading changes, grep `.claude/skills`, `.claude/agents` and `.gemini/agents` for the old one in the same PR.
