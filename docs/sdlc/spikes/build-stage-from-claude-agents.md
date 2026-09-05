---
type: spike
title: Build-stage discipline borrowed from claude-agents
description: What to bring into this kit from the retired claude-agents repo (the /task shape as a Build-stage skill, plan-template lines, review round caps, a multi-session hand-off file, outcome telemetry) and what to leave behind, with the evidence and the implementation order.
tags: [sdlc, build, skills, review, telemetry, claude-agents]
timestamp: 2026-09-03T12:00:00Z
status: open
---

# Spike: Build-stage discipline borrowed from `claude-agents`

Written 2026-09-03 after a full read of `C:\dev\claude-agents` (105 commits, 2026-08-29 to 2026-09-02) and a
comparison against this kit. **Nothing here is adopted by being written.** The developer decides in a later
session; if adopted, the work goes through the chain as its own work item (see §5).

Sources: `claude-agents/docs/ai-native-sdlc-2026-09-02.md` (its own mapping of the playbook onto its tree),
`docs/wiki/ROUTING.md` (evidence per task class), `docs/setups-vs-premade-2026-09-01.md`,
`arch/A-single/skills/task/SKILL.md` (the `/task` skill), `arch/A-single/agents/reviewer.md`,
`base/rules/agents-contracts.md` (hand-off contracts and the review rubric), `bench/metrics.csv` (the 37-run pilot).

## 1. Context and the decision already taken

`claude-agents` set out to find the best multi-agent architecture by benchmark. It built five architectures
(A single-session, B role pipeline, C parallel workers, D teams, E workflows), a global hook layer installed into
`~/.claude`, and a benchmark harness. It measured itself, then pivoted on 2026-09-01 to a routing wiki (task class
to best-evidenced setup). On 2026-09-02 it reviewed the AI-native SDLC playbook and concluded the playbook "is the
lifecycle axis; the wiki is the dial on each stage". This repo was started the same day.

On 2026-09-03 the developer retired `claude-agents` as a project and its global layer was uninstalled from
`~/.claude` (backup: `~/.claude/backups/claude-agents-2026-09-03/`). Two reasons were concrete: its global bash
guard applied role policies by agent name, and `explorer` and `verifier` are also this kit's agent names, so it
constrained agents it was never designed for; and its global CLAUDE.md demanded `/repo-init` and an
`agent-team.env` this kit does not use.

## 2. Evidence that bounds what is worth bringing

| Finding | Source | Consequence for this kit |
|---|---|---|
| 37-run pilot: every architecture resolved every task; role pipelines cost 2.2x to 4.8x a bare session; the reviewer gate never blocked once | `bench/metrics.csv`, DECISIONS 2026-09-01 evening; scope: small/medium Python bug fixes | Do not add a second reviewer agent or a role pipeline. Structure is not what makes the Build stage better on ordinary tasks. |
| `greenfield-auto` routing row: ranking unknown, confidence low, zero local runs; `greenfield-supervised`: no ranking published | `docs/wiki/ROUTING.md` | Nothing measured supports any Build-stage machinery for app-sized work. Treat the first work items as the test and record what the loop catches. |
| `long-horizon` row ranks memory and context discipline first (a capped live-state file, journal, decisions), not role pipelines | `docs/wiki/ROUTING.md`, Confucius E3 | The multi-session hand-off file (§3.5) is the borrow with the best evidence behind it. |
| The playbook's one deterministic gap in `claude-agents` was the test-file lock; this kit already has it | `ai-native-sdlc-2026-09-02.md` item 1; `.claude/hooks/protect-tests.sh` | Nothing to bring for hooks. |
| Delegation fails silently in 41.8% of deep-agent failures (E2) | `docs/wiki/ROUTING.md` research-recon row | Keep one writer per work item; delegate reads only. |

> **Confirmed provisionally** by [`knowledge/decisions/one-writer-until-ledger.md`](../../../knowledge/decisions/one-writer-until-ledger.md) on 2026-09-05, with an expiry and a named measurement.

## 3. What to implement, ranked cheap-first

### 3.1 `/sdlc-build`: the `/task` shape as the missing Build-stage skill

**Gap.** The entry points are `/sdlc-intent` -> `/sdlc-spec` -> `/sdlc-plan` -> implement -> `/sdlc-review`.
"Implement" has no skill; the session improvises. `/task` steps 4 to 8 are exactly that missing part. Steps 0 to 3
(precheck, plan, approval, record) are already the chain, and the chain's versions are stronger (human approval via
`scripts/approve.py`, committed `plan.md`, `require-plan.sh`).

**File.** `.claude/skills/sdlc-build/SKILL.md`. Frontmatter: `disable-model-invocation: true` (side-effecting);
`allowed-tools` limited to Read, Edit, Write, Glob, Grep, `Agent(explorer)`, `Agent(verifier)`, and Bash for
`git status/diff/log/add/commit`, `scripts/verify.sh`, `scripts/run_evals.sh`, `python3 scripts/check_artifact_chain.py`.
No `git push`. No implementation delegation: one writer per work item keeps rule 2 checkable.

> **Confirmed provisionally** by [`knowledge/decisions/one-writer-until-ledger.md`](../../../knowledge/decisions/one-writer-until-ledger.md) on 2026-09-05, with an expiry and a named measurement.

**Steps, mapped from `/task`:**

| Step | Content | From `/task` | Changed for this kit |
|---|---|---|---|
| 0 PRECHECK | Active slug from `.sdlc/active`; `plan.md` must be `status: approved` (else stop and ask for approval); working tree clean except the work item; `scripts/verify.sh` green before any edit | step 0 | Baseline command is `verify.sh`, not an env file. No hand-off cleanup. |
| 1 IMPLEMENT | Follow `## Order of work`. Read before editing. Grep for an existing helper before adding one, and check the module where it would naturally live before concluding it does not exist. Minimal diffs. Every new test carries a one-line comment saying why it matters. A discovery that changes an interface, a data model, or destructive behaviour: stop and ask. Any other deviation: edit `## Files that change` and `## Deviations log` in the same commit as the code (rule 2). | step 4 | Deviations go to `plan.md`, not to a report. |
| 2 VERIFY | Run `scripts/verify.sh`; fix and re-run, at most four rounds; never delete or weaken a test. Still red after four: do not commit; report `BLOCKED:` with the last 40 lines and stop. | step 5 | Drop `changes.md`; the plan's file list plus `check_artifact_chain.py` is the contract. `verifier` subagent may be used to isolate a failure. |
| 3 REVIEW | Invoke `/sdlc-review` on the diff. Apply `[Important]` findings only; nits only when trivial. Then repeat VERIFY. At most two review rounds; after that stop and show what is outstanding without committing. | step 6 | Reuses the existing review skill and its subagents instead of a new reviewer agent. |
| 4 COMMIT | Only when verify is green and the last review has no open `[Important]`. Compare `git status --porcelain` with `## Files that change`; any path not listed: stop and ask. `git add <explicit paths>`; never `-A` or `.`. Message explains why and names the slug (conventions). Do not push. | step 7 | The comparison is the local form of the CI chain check. |
| 5 REPORT | Append one `log.md` line: `<ts> | plan.md | approved -> built | <actor> | <sha> | rounds=<n> important=<n> verify=<last line>`. Then at most five bullets: commit, verify line, review rounds, deviations, decisions needed. Suggest `/clear` when context is large. | step 8 | `log.md` replaces the JSON run record; the token ledger is deferred (§3.6). |

**Also touch:** `.claude-plugin/plugin.json` (the manifest check fails when a skill is missing from it);
`docs/sdlc/rules/` fragment that carries the entry-points line (then `python3 scripts/gen_context_files.py`);
`docs/sdlc/README.md` §2 tree; one eval case (`skill-build-refuses-unapproved-plan.yaml`, kind `skill`, prompt
asks it to implement under a draft plan, check asserts no diff under `PLAN_REQUIRED_PATHS`).

**Cost.** About two hours including the eval and one dry run on a real work item.

### 3.2 Two lines in the plan template

- A `Done means: <one sentence>` line at the top of `plan.md`, the acceptance check the review scores the change
  against. `claude-agents` made its reviewer score "plan" against that line, which is what stopped a diff that
  followed the plan faithfully while the plan missed the task.
- The blocking-question rule: questions to the human before leaving plan mode are only for decisions that change a
  public interface, a data model, or destructive behaviour; everything else is an assumption written into the plan
  with the conventional choice stated. This is the rule that kept plans from coming back as drafts too often.

Files: `docs/sdlc/templates/plan.md`, `.claude/skills/sdlc-plan/SKILL.md` step 2. Optional later:
`check_artifact_chain.py` warns when an approved plan has no `Done means:` line.

### 3.3 Review round cap and "Important only"

`/sdlc-review` today produces findings; nothing says how many times the loop runs or which findings the author must
act on. Add to the skill: at most two rounds per work item; `[Important]` findings must be fixed or answered with
evidence; nits are optional. Consider the `SCORES:` line from `claude-agents`' rubric
(`plan | correctness | security | maintainability | tests`, 0 to 5, every blocking finding pulls its dimension to
1 or 2) as an optional second line in the REVIEW.md format. It makes the verdict derivable from the findings rather
than from taste, but it is a nicety: their reviewer never blocked once in 37 runs, so measure first (§4).

Files: `.claude/skills/sdlc-review/SKILL.md`, `REVIEW.md` (format block).

### 3.4 Green-baseline rule as a hook, not prose

`/task` refused to start on a red baseline. Here the Stop hook nags after code changes, but nothing stops work from
starting on a broken tree. The cheapest deterministic form: `require-plan.sh` (already on every code edit) also
refuses the first edit of a session when `.sdlc/.last-verify` is older than the newest commit, with the reason
"run scripts/verify.sh first". Keep it advisory in `/sdlc-build` first; promote to the hook only if the first
work items show it mattered. Hooks live under `.claude/hooks/`, control plane, so this is an owner change with the
unlock set.

### 3.5 A hand-off file for multi-session work items

`claude-agents` nearly lost its state once because it lived only in a chat; its remedy was a capped live-state file
read in full at every session start, a per-day journal for history, and a decisions log for reasoning. This kit has
`log.md` (gate ledger) and `knowledge/decisions/` but no "where was I and what is next" file, and app-sized work
items will span sessions.

Proposal: `work/<slug>/handoff.md`, template in `docs/sdlc/templates/handoff.md`, sections `## State`,
`## Next action`, `## Open items` (each with a date and a one-line re-test), `## Settled` (drops after two
sessions). Capped at 100 lines; over the cap is a failed hand-off. `/sdlc-build` reads it at PRECHECK and
refreshes it at REPORT. History goes to `log.md` notes, reasoning to `knowledge/decisions/`. Add
`scripts/checks/handoff-cap.sh` so `verify.sh` fails on an oversized hand-off (a report-tier check that became a
gate because the cap is a number, not a judgment).

This is the borrow with the strongest external evidence (the `long-horizon` row) and the one most specific to
the developer's goal of long autonomous tasks.

### 3.6 Post-merge outcome telemetry (defer)

`/outcome <sha> ok|fixed` recorded whether a pipeline commit held or needed a fix afterwards, "the field no benchmark
can produce". Phase 2 item 1 (cost and budget attribution) is the home for it. Until then, a `log.md` line with
artifact `commit` and note `outcome=ok|fixed` costs nothing and `scripts/sdlc_metrics.py` can count it later.
Do not build a separate ledger now.

### 3.7 The routing wiki as a reference (consider)

`claude-agents/docs/wiki/` is an OKF bundle, the same format as `knowledge/`. Its `ROUTING.md` answers "how much
machinery does this task class deserve", which is a Design-stage input here. Options: link it from
`knowledge/index.md` as an external bundle, or copy `ROUTING.md` alone into `knowledge/routing.md` with a
`last_verified` date. Do not import the 38 setup entries; they age.

## 4. What not to bring, recorded so it is not re-derived

- **`.claude/pipeline/` hand-offs, `changes.md`, `diff.patch`, the JSON run record with per-agent tokens.** The
  committed `work/<slug>/` chain and `log.md` are the audit trail; a second store would drift.
- **A separate reviewer agent, and the B/C/D/E architectures.** Measured or graded weak-to-negative for write
  tasks; `/sdlc-review` with its read-only subagents is the equivalent.
- **The role guards (`bash_guard.py`, `write_guard.py`).** They constrain by agent name; this kit constrains by
  path and by tool list in each agent's frontmatter, which does not collide across repos.
- **The benchmark harness and the FROZEN baseline.** Instrument for a parked comparison; the evals directory is
  this kit's regression harness.
- **The global `~/.claude` layer.** Everything here is repo-local by design so it travels with the repo and is
  model-neutral (`.gemini/` mirrors it).

## 5. Suggested work item and order

Slug `sdlc-build-skill`, `kind: feature`, `risk-class: low`. Run it through the chain itself: `intent.md` (this
spike is the interview), `spec.md` (the table in §3.1 is the requirements list), `plan.md`, then implement with
the new skill's own text as the first dry run.

1. §3.2 plan-template lines (minutes; unblock everything else).
2. §3.1 `/sdlc-build` with its eval, manifest entry, rules fragment, README line.
3. §3.3 review cap, without the `SCORES:` line.
4. §3.5 hand-off template and cap check.
5. §3.4, §3.6, §3.7 only after two real work items have run through 1 to 4.

**Acceptance.** `scripts/verify.sh` ends `VERIFY: PASS`; `scripts/run_evals.sh` counts the new case;
`python3 scripts/check_plugin_manifest.py` passes with the new skill; one real work item goes
approved -> built -> reviewed -> merged using only the skills, and its `log.md` carries the build line.

**Measure before extending.** For the first three work items, record in the build line whether the review round
or the verify loop caught anything. If neither ever does, the cap and the loop stay but the `SCORES:` line and the
hook form of §3.4 are not worth building.

## 6. Open questions for the developer

- Should `/sdlc-build` be allowed to run `/sdlc-review` itself, or should review always start from a fresh session
  so the reviewer has no shared context with the author? `/task` used a fresh-context subagent for that reason;
  `/sdlc-review`'s subagents already give partial isolation.
- Cap for `handoff.md`: 100 lines is a guess; `claude-agents` measured its live set at about 136 and set 150.
- Does `.gemini/` need a mirror of the new skill? Agents are mirrored today; skills are not.
