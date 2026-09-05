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
human sets `status: approved`; a hook refuses it from an agent. The active work item is named in `.sdlc/active`.

## Hard rules (enforced by hooks and CI, not by good intentions)
1. No code edits under the paths in `.sdlc/config.env` (`PLAN_REQUIRED_PATHS`)
   unless the active work item has an **approved** `plan.md`. A plan with `kind: fix`
   also locks test files: reproduce the bug as a failing test first, then fix the code.
2. If implementation deviates from `plan.md`, update `plan.md` in the same commit.
   CI fails a PR whose diff touches files not listed in the plan.
3. Never edit `.claude/hooks/`, `.gemini/`, `.github/workflows/`, `.sdlc/`, `.claude/settings.json`,
   `scripts/verify.sh`, `scripts/run_tests.py`, `scripts/run_evals.sh`, `scripts/checks/`, or secret
   files. Propose the change in the PR description instead. Never set `status: approved`, `approved-by` or
   `approved-on` on a chain artifact and never run `scripts/approve.py`: `protect-approvals.sh` refuses both.
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
- Band detector: `python3 scripts/detect_bands.py --series ...` (exit 3 = breach, 2 = bad input); series: `scripts/github_metrics.py`; workflow matrix: `scripts/bands_config.py`; git metrics: `scripts/sdlc_metrics.py`
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
- Humans approve from their own shell with `python3 scripts/approve.py <slug> <artifact>` (once per clone:
  `git config sdlc.approver <github-handle>`, or pass `--as <handle>`; it enforces intent → spec → plan order), or by
  editing the artifact plus `log.md` in the GitHub web editor; then commit as themselves. The script refuses to run
  inside an agent session; an agent asks for approval and waits. CI checks the approval commit's author.

## Gemini CLI notes
- `.gemini/settings.json` wires the same scripts as Claude: `BeforeTool` on
  `write_file|replace|run_shell_command` runs `.claude/hooks/` protect-paths, block-secrets,
  require-plan, protect-tests, and production-gate; `AfterAgent` runs the verify reminder.
- A project hook that is new or whose command changed warns before it runs, so a local
  block can be skipped on first run. The CI gate (`sdlc-gate`) is the authoritative red line.
- The release gate cannot ask you under Gemini; a deploy or push to a protected branch
  without `.sdlc/release-authorizations/<sha>` is blocked outright.
- Leaving plan mode with `exit_plan_mode` is **not** an approved `plan.md`. Rule 1 is
  satisfied only by `work/<slug>/plan.md` with `status: approved` set by a human.
- Subagents live in `.gemini/agents/` (read-only mirrors of `.claude/agents/`); the
  `/sdlc-*` procedures are the SKILL.md files under `.claude/skills/`: read and follow them.
  Keep one writer per work item: subagents read and return evidence, the session holding the plan
  makes every edit (`knowledge/decisions/one-writer-until-ledger.md`, provisional, with an expiry).
- Antigravity (IDE and `agy`) reads this file but ignores `.gemini/settings.json`, so there
  the rules above are advisory only and `sdlc-gate` plus the merge click are the gates.

## Lessons (one file each in knowledge/lessons/)
A mistake made twice becomes a file there and a pointer line here, in the same PR; delete the pointer when a hook makes the mistake impossible.
- Rule 3 is advisory in this repo: the unlock logs control-plane writes, CI and the owner's review gate them — knowledge/lessons/control-plane-unlock-is-advisory.md
- A path guard compares one spelling; normalise first, never widen its input without a test — knowledge/lessons/one-path-spelling-in-guards.md
- Test a `_lib.sh` change from a second shell; a bad edit locks the session out of every tool — knowledge/lessons/test-lib-changes-from-a-second-shell.md
- Every `--check` folds CRLF before comparing; drift on a file nobody edited means line endings — knowledge/lessons/fold-crlf-before-comparing.md
- A skill or agent spells a template's field or heading exactly as the template does — knowledge/lessons/skills-spell-template-headings.md
- A plan bullet starts with the bare path, then ` — `; the empty deviation bullet is `- ` with a trailing space — knowledge/lessons/plan-bullets-start-with-the-path.md
- The ledger's from/to slot holds `status` values only; log the build gate on the PR — knowledge/lessons/ledger-slot-holds-status-only.md
- Send ledger lines to the owner in a fenced block, never as bullets; run `log_ledger.py` after the approval lands — knowledge/lessons/send-ledger-lines-in-a-fenced-block.md
<!-- END GENERATED -->
