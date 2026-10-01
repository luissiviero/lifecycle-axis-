---
type: doc
title: "Evidence: interview answers from the current state"
description: "Thirty questions about the kit answered from the repository as it stands, with citations; produced read-only for the 2026-09-10 step review."
tags: [sdlc, revision, evidence]
timestamp: 2026-09-10T14:00:00Z
---
# Repository scout answers — lifecycle-axis-, current state

Scope: `origin/main` @ `ca8dd32` (2026-09-10 05:09 -0300, 399 commits) plus every unmerged `origin/*` branch.
Every answer is what the repo says or does today, not what the owner wants. Where two sources disagree, both are quoted.

---

## Q1. What is the deliverable of a "revision"/review, and is there precedent for a meta revision of the kit?

Two different things carry the word.

**A "revision" is a committed consensus record, not a report or an applied change by itself.** `docs/sdlc/templates/revision.md:1-32` defines `type: sdlc/revision` with front matter `artifact:` and `trigger:`, a `## Proposal` section, and one `## Reviewer: <role> (<model>)` section per reviewer, each ending `verdict: revise`. It lives at `work/<slug>/revisions/<n>.md` and its only function is to unlock a re-signature: "`scripts/sign.py --revision` re-signs the artifact only when every `## Reviewer:` section above ends `verdict: revise` and there are at least as many sections as the policy's `min-reviewers`" (`docs/sdlc/templates/revision.md:29-32`; policy at `.sdlc/delegation.yaml:39-43`, `revisions: consensus`, `min-reviewers: 2`). Three exist today: `work/retire-active-pointer/revisions/1.md`, `work/run-queue/revisions/1.md`, `work/run-queue-followups/revisions/1.md`.

**A "review" deliverable is a findings list, not an applied change.** `REVIEW.md:25-34` fixes the format (`[Important][security] file:line — …`, `Chain:`/`Verify:` lines, `Important: <n> | Nits: <m>`); `REVIEW.md:36` — "Findings never approve or block on their own." The reviewer subagents have no write tools (`.claude/agents/security-reviewer.md:4` `tools: Read, Grep, Glob, Bash`; `docs/sdlc/README.md:105` "reviewer subagents have no write tools; the fix is the author's").

**Precedent for a meta revision of the kit itself: yes, twice, and it lives in `docs/sdlc/handoff/`.**
- `docs/sdlc/handoff/lifecycle-axis-vs-playbook.md:9-30` — "lifecycle-axis vs. 'The AI-Native SDLC playbook': what changed, what broke, what is missing", produced by "eight read-only analysts in parallel", "No file in the repo was changed; `git status` is clean" (`:16`). Its verdict paragraph (`:18-30`) is a meta-review of the whole kit.
- `docs/sdlc/handoff/consensus.md:9-16` — reconciles that report with an earlier owner artifact, row by row, and issues a merged fix list; that list became the eleven work items in `docs/sdlc/handoff/PLAN.md` (`docs/sdlc/handoff/index.md:11-19`).

So the precedent shape is: a read-only report + a consensus reconciliation, both committed under `docs/sdlc/handoff/`, converted afterwards into ordinary `work/<slug>/` items.

## Q2. May an agent delete obsolete scripts, branches, roadmap items, or docs? Deletion and `superseded`?

**NOT ANSWERED IN REPO as a general rule.** There is no rule anywhere that says an agent may or may not delete files, branches or roadmap items. What exists:

- Deletion is treated as a *write* by the guards, so it is blocked only where writes are blocked: `.claude/hooks/_lib.sh:276-277` counts `rm|unlink|rmdir|mv|ln|tee|chmod…` operands as Bash write targets, and `protect-paths.sh` refuses them under `PROTECTED_PATHS` (`.sdlc/config.env:9`). Outside those paths deletion is ungated, subject only to rule 1's plan gate for `PLAN_REQUIRED_PATHS="scripts"` (`.sdlc/config.env:4`).
- Rule 2 makes any deletion visible: a deleted path is in the diff, so it must be listed in `plan.md`'s `## Files that change` or CI fails the PR (`docs/sdlc/README.md:98`).
- The one explicit *permission* to delete is narrow: "delete the pointer when a hook makes the mistake impossible" — `CLAUDE.md:94`, `docs/sdlc/rules/60-lessons.md:11`.
- The one explicit *prohibition* on deleting reasoning: `knowledge/decisions/one-writer-until-ledger.md:56` — "Nothing is deleted." Superseded records get a banner instead (`knowledge/decisions/self-enforcement-off.md:11-13`, "**Superseded on 2026-09-02 by `self-hooks-on.md`**"; `knowledge/decisions/merge-click-is-the-gate.md:11-13`).

**`superseded` is a human-only status, and it is the retirement mechanism, not deletion.** `CLAUDE.md:15-17` — "when an item completes, a human retires it (`superseded` on its artifacts, a ledger line each, the pointer cleared or moved to the next item)". `.claude/hooks/protect-approvals.sh` refuses an agent-side `status: approved|superseded` (`docs/sdlc/README.md:109`). `scripts/check_artifact_chain.py:733-755` requires whoever superseded an artifact to hold that artifact's role in `.sdlc/approvers.yaml`.

**Live contradiction:** `work/ci-budget/log.md:17` records that retiring a *delegated* item is currently impossible — "a superseded artifact needs a valid human approver and both artifacts carry approved-by claude, which `.sdlc/approvers.yaml` lists under never-approve; retiring any delegated item is therefore a defect of its own". The evidence is on main: commit `894e11c` set `work/run-queue-followups/intent.md` to superseded and `9811483` put it back — today `work/run-queue-followups/intent.md:7` reads `status: approved`, `spec.md:7` and `plan.md:7` read `delegated`, while `.sdlc/active` has already moved to `ci-budget` (`308f1a2`). The item is finished but never retired.

## Q3. Does kit work go through the kit's own chain? PLAN_REQUIRED_PATHS and PROTECTED_PATHS?

**Yes.** Every change to the kit since 2026-09-02 has a `work/<slug>/` chain: 20 items in `work/index.md:11-30`, from `sdlc-kit-phase-1` to `ci-budget`. `README.md:12` names `work/sdlc-kit-phase-1/` as "The kit's own work item".

- `PLAN_REQUIRED_PATHS="scripts"` (`.sdlc/config.env:4`) — the kit's own product code. `knowledge/decisions/self-hooks-on.md:55` confirms: "plan required for code under `PLAN_REQUIRED_PATHS` (`scripts`, the kit's own product code)".
- `PROTECTED_PATHS=".claude/hooks .github/workflows .sdlc .gemini .claude/settings.json scripts/verify.sh scripts/run_tests.py scripts/run_evals.sh scripts/checks"` (`.sdlc/config.env:9`).
- `RELEASE_GATED_PATHS="migrations infra terraform helm"` (`.sdlc/config.env:12`); `GENERATED_PATHS="src/gen CLAUDE.md GEMINI.md AGENTS.md work/index.md work/*/index.md"` (`:16`).

But rule 3 is **advisory in this repo**: `.claude/settings.json:2-4` sets `SDLC_CONTROL_PLANE_UNLOCK: "1"`, so a control-plane write passes with an audit line (`knowledge/lessons/control-plane-unlock-is-advisory.md`, `knowledge/decisions/self-hooks-on.md:59-67`). The never-unlock set is `.sdlc/release-authorizations/`, `.sdlc/approvers.yaml`, `.sdlc/delegation.yaml` and `.sdlc/hook-decisions.log` (`.sdlc/README.md:1`, `.sdlc/delegation.yaml:1-8`). CI's `check_control_plane.sh` plus the owner's `control-plane-approved` label is the real gate (`docs/sdlc/README.md:114`).

## Q4. Written definition of "done" for the kit as a whole / exit criterion / v1?

**No v1 or exit criterion exists.** The closest three things:

1. **Per-task done** (`CLAUDE.md:59-66`, "Verifying your work"): `scripts/verify.sh` ends `VERIFY: PASS (<sha>)`; `check_artifact_chain.py --base origin/main` ends `CHAIN: PASS`; `run_evals.sh` ends `EVALS: N pass, 0 fail`; `check_okf.py` ends `OKF: N docs, 0 warnings`. "Run all of them before reporting a task complete."
2. **Phase-1 outcome statement** (`work/sdlc-kit-phase-1/intent.md:23-26`): "A new project can adopt the kit in under an hour and the loop runs by hand end to end. The deterministic gates hold regardless of which model produced the change (CI and branch protection, not only hooks). Institutional knowledge lives once, in an OKF bundle, read by both models." That item is `status: superseded` (`:7`).
3. **The roadmap is open-ended**, not a definition of done: `docs/sdlc/phase-2-roadmap.md` lists Phase 1.5, 2 (items 1, 1b, 2-6, 17-19), 3 (7-11) and 4 (12-16), with "Explicitly out of scope for this repo" (`:130-131`) naming only vendor integrations.

The sharpest recorded judgment on this gap: `docs/sdlc/handoff/consensus.md:42` — "right shape, right decisions for the constraints, and a set of implementation gaps that **the kit's own definition of done does not measure**"; and `docs/sdlc/handoff/lifecycle-axis-vs-playbook.md:21-23` — "On its own definition of done it is green… But the definition of done does not measure the properties the playbook cares about."

## Q5. Which model wrote and which reviewed, per work item?

The convention only exists from 2026-09-06 (`work/approve-by-dispatch/log.md:23`, added at the owner's request; rule text at `docs/sdlc/rules/30-conventions.md:21-25` / `CLAUDE.md:78-82`). Before that, ledgers name only the actor `claude`. Everything the repo actually records:

| Item | Writer | Reviewers | Citation |
|---|---|---|---|
| `sdlc-kit-phase-1` | per task: fable (T01, T24), opus (T02-04, T11, T17), sonnet (T05-10, T12-16, T18-23), haiku (T15b) | "fable review" on T11, T12, T13, T19 | `work/sdlc-kit-phase-1/spec.md:97-192`; orchestration note `:13` ("draft breakdown by an Opus planner") |
| `front-matter`, `control-plane-visibility`, `loop-protection`, `bash-guard-hardening`, `deploy-gate`, `approval-gate`, `band-detector`, `adopter-first-hour`, `agent-evals`, `delegation-boundary`, `docs-reconcile`, `batch-b-followups`, `delegated-mode` | **not recorded** | **not recorded** | their `log.md` files name only actor `claude`; the convention post-dates them |
| `approve-by-dispatch` | **not recorded** (the item that *created* the convention) | not recorded; three review rounds noted | `work/approve-by-dispatch/log.md:20,23` |
| `retire-active-pointer` | **Fable 5.1** | security-reviewer + plan-reviewer, **opus** | `work/retire-active-pointer/log.md:18,19,20`; `revisions/1.md:39,43` (`## Reviewer: security-reviewer (opus)`, `plan-reviewer (opus)`), `revisions/1.md:58` "The writer is Fable 5.1" |
| `run-queue` | **Opus 5** | security-reviewer + plan-reviewer, **sonnet** | `work/run-queue/log.md:20`; `revisions/1.md:32,48` |
| `run-queue-followups` | **Opus 5** | plan-reviewer + security-reviewer, **sonnet** | `work/run-queue-followups/log.md:18,21`; `revisions/1.md:44,63` |
| `ci-budget` | exploration **sonnet** (3 scouts), design pass **opus**; second session on **fable**; owner's revision: "opus writes and calls sonnet subagents, fable revises in full at each of five milestones" | "sonnet writes, opus reviews, fable checks divergence" (the delivery answer) | `work/ci-budget/log.md:14,15` |

`ci-budget` is the only item where the two lines contradict each other on who writes: `log.md:14` says "sonnet writes, opus reviews, fable checks divergence"; `log.md:15` (next day, the owner's revision) says "opus writes and calls sonnet subagents, fable revises in full at each of five milestones".

## Q6. Which playbook plays are implemented, declared-only, or inert?

Read from `docs/sdlc/README.md` §1 table (`:24-40`) and the enforcement matrix (`:95-118`), checked against the tree.

**Implemented and deterministic:** intent/spec/plan chain (`work/`, `scripts/check_artifact_chain.py`); CLAUDE.md as a generated one page (`scripts/gen_context_files.py`, `scripts/checks/context-drift.sh`); build-time hooks (7 scripts in `.claude/hooks/`, wired in `.claude/settings.json:17-55`); the feedback loop (`scripts/verify.sh` + `VERIFY_CMDS`, `.sdlc/config.env:25`); test lock during a fix (`protect-tests.sh`); evals in CI (`.github/workflows/agent-evals.yml`, 51 cases in `evals/cases/`); PR review (`pr-review.yml` + `REVIEW.md`); approval gates (`protect-approvals.sh`, `approve.yml`); the control-plane CI guard (`scripts/check_control_plane.sh`); delegated merge (`delegated-merge.yml`, `scripts/delegated_merge.py`).

**Declared but only partly acted on:**
- **Bands / Maintain.** The detector is real and runs nightly (`.github/workflows/bands.yml:11-12` cron `0 3 * * *`; `scripts/detect_bands.py`), but `docs/sdlc/README.md:38` says "in this phase 3σ is diagnosed like 2σ and filed as an issue", and `:108` "the 3σ `routes:` are declared, not yet acted on". `bands.yml:135-158` — "This workflow only ever opens issues, never pull requests". `monitoring/bands.yaml:14,23,32` declare `routes: [pull_request, runbook:rollback-deploy]`, `[runbook:rollback-deploy]`, `[report:engineering-leadership]` — none of these routes has code.
- **Deploy / CI-CD.** `deploy.yml` exists and is `workflow_dispatch` only (`:11-23`), gated by `scripts/deploy.sh`; but `docs/sdlc/README.md:37` — "rollback is a manual `workflow_dispatch` of the previous SHA… **nothing rehearses it**", and `:118` — the GitHub Environment's required reviewers are "not enforceable on the Free plan" (`knowledge/decisions/merge-click-is-the-gate.md:20-23`). No deploy has ever run: `.sdlc/release-authorizations/` holds only `.gitkeep`.

**Inert (declared in the digest, zero mechanism):**
- **`post_deploy_5xx_rate` band** — `monitoring/bands.yaml:16`: `source: "(none — no metrics store yet; tier actions are inert until one exists…)"`.
- **Recurring codebase scans (Claude Security)** — `docs/sdlc/README.md:39` describes the play; no workflow, script or config implements it. `work/sdlc-kit-phase-1/intent.md:56` — "no managed settings, Claude Tag or Claude Security in this phase"; `spec.md:92` lists them as out of scope.
- **Claude on call / Claude Tag** — `docs/sdlc/README.md:40`; same exclusion, `work/sdlc-kit-phase-1/intent.md:56`.
- **The `incident.md` link in the chain** — the template exists (`docs/sdlc/templates/incident.md`) and `/sdlc-incident` exists, but **no `work/*/incident.md` file exists anywhere in the repo**. `docs/sdlc/handoff/consensus.md:26` already flagged this: "Reclassify as Changed, on paper only."
- **Spec-on-intent-merge automation** — `docs/sdlc/README.md:27` "can run headless on intent merge (**not automated in this repo**; see step 6 of Using it)".

## Q7. OKF: what reads the `knowledge/` bundle today? Is Gemini a working target?

**What reads it:** only the kit's own conformance checker and the humans/agents following links. `scripts/check_okf.py` scans `KNOWLEDGE_PATHS="knowledge docs/sdlc"` (`.sdlc/config.env:31`) and is warning-only (`OKF_STRICT="0"`, `:34`; `scripts/checks/okf.sh`). `CLAUDE.md`/`GEMINI.md`/`AGENTS.md` link into it rather than restate it (`CLAUDE.md:86`, `docs/sdlc/okf-pairing.md:49`). Nothing else consumes it: `docs/sdlc/okf-pairing.md:66-67` — "Still open: whether a Knowledge Catalog or any OKF consumer exists today". `docs/sdlc/okf-pairing.md:50-51` freezes it: "no new OKF directories until `lessons/` or `services/` has content that is not an index". `knowledge/services/index.md` is still index-only.

**Gemini:** partly working, not a live target for this owner.
- Wired: `.gemini/settings.json:1-30` runs the same five `.claude/hooks/` scripts on `BeforeTool` (matcher `write_file|replace|run_shell_command`) and the verify reminder on `AfterAgent`; `.gemini/agents/` mirrors the four read-only agents; `knowledge/decisions/gemini-hooks.md` records the payload keys verified against the CLI.
- Blocked: `docs/sdlc/phase-2-roadmap.md:27-32` — "Gemini CLI v0.58 refuses personal Google accounts ('migrate to Antigravity'), and Antigravity reads `GEMINI.md` but not `.gemini/settings.json`: its hooks live in `.agents/hooks.json`… Next step: an adapter under `.agents/`". No `.agents/` directory exists. `docs/sdlc/rules/50-gemini-only.md:27-28` — "Antigravity (IDE and `agy`) reads this file but ignores `.gemini/settings.json`, so there the rules above are advisory only". `docs/sdlc/okf-pairing.md:65-66` — "the Gemini surface in use is Antigravity (IDE and `agy` CLI); Gemini CLI v0.58 refuses personal Google accounts." Also open: "an end-to-end check that PowerShell forwards Gemini CLI's stdin to `bash` on Windows (verified by simulation only)" (`phase-2-roadmap.md:31-32`).

## Q8. "Best practices per model": where are they encoded, source of truth, status?

**Source of truth (designed):** `docs/sdlc/spikes/prompt-surfaces.md`, `status: accepted` (`:7`), dated 2026-09-03, sourced from fourteen Claude platform doc pages listed at `:20-40`. It designs five mechanisms all reading from one source, `docs/sdlc/prompt-blocks/*.md` (the diagram in §2, spike §2.1 at `:96-115`).

**Status: designed, accepted, not scheduled, nothing built.** Verified on disk — none of these exist:
`docs/sdlc/prompt-blocks/`, `.claude/skills/prompting-standards/`, `scripts/check_prompt_surfaces.py`, `scripts/checks/prompt-lint.sh`, `docs/sdlc/templates/agent.md`, `knowledge/runbooks/model-upgrade.md`. `grep -rn "MODEL_\|EFFORT_" .sdlc/config.env scripts/ .claude/` returns nothing.
`docs/sdlc/phase-2-roadmap.md:41-49` — item **1b**, "**Designed, not scheduled**… Becomes work item `prompt-surfaces` when scheduled. Its `implementer` role is provisionally overruled by `knowledge/decisions/one-writer-until-ledger.md` until item 1's ledger exists."

**The two rules fragments are not per-model prompting practice; they are per-runtime mechanics.** `docs/sdlc/rules/40-claude-only.md:5` `targets: [claude]` — skill entry points, hook events, subagent location. `docs/sdlc/rules/50-gemini-only.md:5` `targets: [gemini]` — where hooks are wired, the first-run trust warning, `exit_plan_mode` is not an approved plan, Antigravity's advisory status. Neither carries prompting advice. The one *behavioural* convention that did ship is in the shared fragment: `docs/sdlc/rules/30-conventions.md:21-25` (review on a different model from the writer).

## Q9. Which models and runtimes does the repo assume are available?

- **Claude Code** (interactive): `.claude/settings.json`, `.claude/skills/*`, `.claude/agents/*`, `.claude/hooks/*`; `$CLAUDE_PROJECT_DIR` in every hook command (`.claude/settings.json:22-53`).
- **Claude Code CLI in CI**, pinned: `npm install -g @anthropic-ai/claude-code@2.1.258` in `.github/workflows/agent-evals.yml:63`, `bands.yml:100`, `sdlc-gate.yml:78`.
- **`anthropics/claude-code-action`** pinned by SHA: `.github/workflows/pr-review.yml:73` (`8251c103ac8c1d761882c86aba1412c7f583c844 # v1`).
- **Credentials, either of two, both optional:** `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` — `agent-evals.yml:37-38`, `bands.yml:46-48`, `pr-review.yml:51,75-76`, `sdlc-gate.yml:22,75-76`. `docs/sdlc/github-setup.md:86-89` — "`ANTHROPIC_API_KEY` at repository scope with a spend limit, or `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token` on a Pro/Max plan. Without one, prompt-based evals are skipped (and counted), the `pr-review` workflow does nothing, the `bands` workflow files the raw detector output, and the `sdlc-gate` triage step is skipped. Nothing fails for lack of a key."
- **Claude GitHub App** as `claude[bot]`: `docs/sdlc/github-setup.md:90-91`; `pr-review.yml:3`.
- **`GITHUB_TOKEN`**: `approve.yml:127`, `sdlc-gate.yml:40`. **`RELEASE_APPROVAL`** Environment secret: `deploy.yml:59`.
- **Gemini CLI**: `.gemini/settings.json`; needs `bash` and `jq` on PATH (`docs/sdlc/README.md:147-148`).
- **Antigravity**: reads `GEMINI.md` only, hooks not wired (`docs/sdlc/phase-2-roadmap.md:27-31`, `docs/sdlc/rules/50-gemini-only.md:27-28`).
- **Named models in prose:** Fable 5.1, Fable 5, Opus 5, Opus 4.8, Sonnet 5, Haiku 4.5 (`docs/sdlc/spikes/prompt-surfaces.md:24-26` doc list and §2.6 table); sonnet/opus/fable/haiku per task in `work/sdlc-kit-phase-1/spec.md:97-192`.
- **Runtime environments assumed:** Linux CI runners; a remote container with **no `gh` binary** (`docs/sdlc/handoff/HANDOFF.md:181-183`); Windows 10 + Git Bash (`docs/sdlc/phase-2-roadmap.md:82-102`); a phone (GitHub web editor / Actions tab) as the owner's primary surface (`HANDOFF.md:105-131`).

## Q10. Model routing: is there a role-to-model table, and is it enforced?

**Three tables exist; none is enforced by anything.**

1. `docs/sdlc/spikes/prompt-surfaces.md` §2.6, the role→pin table: lead = Fable 5.1 high; explorer = a fast model at low, or Fable 5.1 at low; verifier = the cheapest model, low; security-reviewer/plan-reviewer = Opus 5 or Fable 5.1 at medium; implementer = Sonnet 5 high/xhigh; screen = Haiku 4.5 low. It is explicitly "a **hypothesis to measure**, not a decision" and "The routing is revised by data, not by opinion: the Phase 2 cost ledger… is the measurement that says whether a row is paying off". The `implementer` row is "**Overruled provisionally** by `knowledge/decisions/one-writer-until-ledger.md`" (§2.6's opening note).
2. `.claude/agents/*.md` **have no `model:` field.** All four carry only `name`, `description`, `tools` (`explorer.md:1-5`, `plan-reviewer.md:1-5`, `security-reviewer.md:1-5`, `verifier.md:1-5`). `.gemini/agents/*.md` likewise. The spike's Point 1 ("Each agent file gains a `model:` and an effort pin… read from `.sdlc/config.env`") is unbuilt; `MODEL_LEAD`/`EFFORT_*` do not appear in `.sdlc/config.env`.
3. `work/sdlc-kit-phase-1/spec.md:97-192` assigns a model per task (T01 fable, T02-04 opus, T05-10 sonnet, T15b haiku, T11 opus + fable review, T24 fable). That artifact is `status: superseded`.

**The one convention written as a rule** is direction-only, not a table: `docs/sdlc/rules/30-conventions.md:21-25` / `CLAUDE.md:78-82` — "A review runs on a **different model from the one that wrote the work**, whenever a second one is available… The item's ledger records which model wrote and which reviewed (**the owner writes the names**)". `.claude/skills/sdlc-run/SKILL.md:31` and `:50-51` repeat it as "where possible". Nothing checks it: no eval case, no CI check, no hook; `grep -rn "model" .github/workflows/*.yml` returns one comment line only (`bands.yml:5`).

**`ci-budget`'s assignment** (`work/ci-budget/log.md:14-15`) is a prose note in a ledger, not config — and the two lines disagree (see Q5). The reviewer's model on `pr-review.yml` was explicitly left unchanged pending measurement: `work/ci-budget/intent.md`, open question on the review's model — "A: unchanged; the review verdict gates delegated merges (`require-review: true`), so cut the count first, measure a week, decide with a number (owner, 2026-09-09)."

## Q11. Compaction / plan-in-conversation failure

**On `main`: nothing.** `.claude/settings.json:17-55` declares `PreToolUse`, `PostToolUse` and `Stop` only — no `SessionStart`, no `UserPromptSubmit`. No file on main uses the word "compaction".

**On `origin/claude/agent-plan-adherence-4b4mqk` (pull request 67), `work/plan-adherence/intent.md`, `status: in-review` (`:8`), 2 commits ahead of main, 0 behind.**

Problem statement, in the owner's words (`:32-38`):
> "I commonly trace a plan and want it executed in a new session. In such session, the plan is read and executed. The problem though, is that it forgets that after a while, which makes it deviating from such plan. How would you enforce the agent to keep the plan at all times, making sure it doesn't deviate?"
> "Is using caveman a good idea? If not, what to do to make it less verbose, and don't forget that mid-way?"

Measured diagnosis (`:42-73`), abbreviated: "The plan lives only in the conversation. Nothing in the repository re-surfaces it… When the harness compacts the conversation, the summary keeps the gist and drops the file list and the step order, which is the moment the deviation starts. A fresh session only delays it." (`:42-45`) "The plan gate checks a word, not a list… the file-list contract of rule 2 is judged once, by `scripts/check_artifact_chain.py:855`, against `git diff <base>...HEAD`… so a deviation is refused when the pull request opens, hours after the edit that made it." (`:46-50`) "Progress has no place on disk… nothing marks a step done" (`:53-59`). "No context file carries an output-style rule" (`:63-68`). "Subagent prompts have no shape" (`:60-62`).

Proposed outcome (`:84-120`): a `SessionStart` hook with matcher `compact` that reprints the active plan's `## Files that change` and `## Order of work`; a `UserPromptSubmit` hook printing `[plan <slug>] <done>/<total> steps done; next: <step>`; a new hook beside `require-plan.sh` that **blocks an edit to a path outside the plan's file list at exit 2**, sharing `section()` with the chain check so the two "can never disagree on a spelling"; a `Stop` hook naming unplanned changed paths; a fixed five-field tickable step shape in the plan template; and an `Input:` line on every agent file. Owner's decisions recorded at `:75-82`: no compaction rule, no second pointer file, no output-style file, no caveman plugin, no subagent writer per step, no per-step plan files, and "nothing manual": every check this item adds is a hook with a payload test and an eval case.

## Q12. Every failure mode the repo has recorded

**`knowledge/lessons/` (14 files, one per mistake made twice; pointers in `CLAUDE.md:95-108`):**
- Rule 3 is advisory here — the unlock lets control-plane writes through; CI and review are the gate — `knowledge/lessons/control-plane-unlock-is-advisory.md`
- A path guard that compares one spelling silently allows Windows path forms — `knowledge/lessons/one-path-spelling-in-guards.md`
- A bad `_lib.sh` edit locks the session out of Edit, Write and Bash at once (hooks refuse without `jq`) — `knowledge/lessons/test-lib-changes-from-a-second-shell.md`
- CRLF from `core.autocrlf` makes byte-comparing `--check` modes report drift on a clean tree — `knowledge/lessons/fold-crlf-before-comparing.md`
- A skill or agent that misspells a template heading ships the wrong spelling into `work/_example` — `knowledge/lessons/skills-spell-template-headings.md`
- A plan file bullet not starting with the bare path fails the chain check — `knowledge/lessons/plan-bullets-start-with-the-path.md`
- The ledger's from/to slot logged as `plan.md | build -> in-review` reads as a regression of an approved plan — `knowledge/lessons/ledger-slot-holds-status-only.md`
- Ledger lines pasted as chat bullets arrive as `- - <ts>` and the parser drops them — `knowledge/lessons/send-ledger-lines-in-a-fenced-block.md`
- An unstaged new file is invisible to `check_front_matter.py` (`git ls-files`), so a bad colon turns CI red — `knowledge/lessons/stage-new-files-before-verify.md`
- A workflow `permissions:` block that names one API surface 403s on another for three days — `knowledge/lessons/workflow-permissions-name-every-api.md`
- A test reading the ambient environment (git identity, wall clock) passes locally and fails on the runner — `knowledge/lessons/tests-carry-their-own-environment.md`
- A rules-fragment line pushes the adopter's rendered `CLAUDE.md` past `MAX_CONTEXT_LINES` — `knowledge/lessons/adopter-context-file-sits-at-the-cap.md`
- `check_artifact_chain.py` reports `CHAIN: PASS` on staged-but-uncommitted work; it audited the wrong work twice in one session — `knowledge/lessons/commit-before-the-chain-check.md`
- A blank line inside an eval `check: |` block truncates it into a stub that always passes — `knowledge/lessons/eval-checks-have-no-blank-lines.md`

**`work/*/intent.md` Problem sections (each a measured failure mode):**
- Approval was a record, not a gate: `env -u CLAUDECODE` defeated the refusal, no hook covered `work/` — `work/approval-gate/intent.md:20-23`
- The Bash write guard missed eleven command shapes (deletes, glued commands, stderr redirects, two-step `cd`); NotebookEdit bypassed every edit hook — `work/bash-guard-hardening/intent.md:3-4`
- The deploy path failed open: `RELEASE_APPROVAL` derived from the commit it approved; the `gh` and `deploy.sh` routes unguarded — `work/deploy-gate/intent.md:3-4`
- The agent could weaken the check on its own work (verify loop, test lock, session settings unprotected) — `work/loop-protection/intent.md:3-4`
- The band detector could not see the breach it exists for (σ=0 baseline, fixed baseline, `--days` ignored, one WE rule missing, nightly duplicate issues) — `work/band-detector/intent.md:3-4`
- A fresh install broke ten times before the adopter could do anything — `work/adopter-first-hour/intent.md:3-4`
- Evals could not go red: one prompt case among 34, a nightly green on an expired credential, 15 hook cases whose negated assertions could not fail — `work/agent-evals/intent.md:3-4`
- Template inline comments broke the chain check, ledger and hooks; the approval script defaulted to a non-approver and enforced no stage order — `work/front-matter/intent.md:3-4`
- Hook decisions were invisible: the unlock's audit line went to stderr on exit 0; `check_control_plane.sh` never matched `kit/*` — `work/control-plane-visibility/intent.md:3-4`
- Docs claimed fifteen controls the code did not ship — `work/docs-reconcile/intent.md:3-4`
- Nothing cleared `.sdlc/active`, so the plan gate opened on finished work — `work/retire-active-pointer/intent.md:3-4`
- A delegated run ended at one ready PR and nothing started the next item — `work/run-queue/intent.md:3-4`
- The chain check reported PASS on work it never saw — `work/run-queue-followups/intent.md:3-4`
- Two spikes on main gave opposite answers on delegating implementation — `work/delegation-boundary/intent.md:3-4`
- 1,124 runs in six days exhausted 2,000 free Actions minutes; the failure path cost 4× the success path; 89 of 96 gate runs were superseded before they mattered — `work/ci-budget/intent.md:3-4,29-67`
- (unmerged) The post-merge advance has never landed: a non-fast-forward push swallowed as a note — `origin/claude/advance-push-intent:work/advance-push/intent.md:36-52`
- (unmerged) Every approval tap leaves the indexes it changes stale — `origin/claude/approve-tap-regenerates-index:work/approve-tap-regenerates-index/intent.md:26-45`
- (unmerged) A plan executed in a new session is forgotten at compaction — `origin/claude/agent-plan-adherence-4b4mqk:work/plan-adherence/intent.md:42-73`

**`revisions/*.md` triggers (design defects caught before code):**
- A signed guard condition was inert in its only motivating case, and a failed `git status` was treated as "not dirty" (fail-open) — `work/run-queue-followups/revisions/1.md:7`
- The ledger actor was the wrong identity, and a failure mode was credited to a mechanism that cannot fire — `work/run-queue/revisions/1.md:10`
- R-2 was judged on the wrong ref; the pointer was used as a path/git argument before validation — `work/retire-active-pointer/revisions/1.md:10`

**Incidents:** none. No `work/*/incident.md` file exists.

**External failure modes recorded but not filed as items:** the 41.8% silent-delegation-failure figure and the 2.2×-4.8× role-pipeline cost from the retired `claude-agents` pilot — `docs/sdlc/spikes/build-stage-from-claude-agents.md:38-45`.

## Q13. Any ranking or prioritisation of pains?

**Yes, once, and only inside `ci-budget`.** `work/ci-budget/intent.md:16-19` quotes the owner: "make a plan on how you'd do it to reduce **(a) GitHub minutes; (b) time; (c) unnecessarily spent tokens**. for that, if we keep the crucial procedures, I don't mind loosen up the other ones to improve this 3 items." The `## Proposed outcome` keeps that (a)/(b)/(c) order with a number on each: (a) ≤6 billed minutes for a PR of #61's shape against ~34 today, mean ≤10 against the 30 measured; (b) draft pushes wait for nothing, ready pushes ≤4 min, a red gate red inside 1 min instead of 3.6; (c) no `claude -p` from CI on a failure without a `triage` label, no review of a draft, at most one review per push after ready.

Elsewhere the ranking is by *adoption order*, not by pain: `docs/sdlc/README.md:42-44` — "Start with the 'clay' plays that nothing points into: intent.md, CLAUDE.md, feedback loop, build-time hooks, plan mode. Then skills, subagents, evals. Then requirements-and-design, PR review. Then approval gates and CI/CD. Last, the monitoring loop, scans, and on-call." The roadmap is "Ordered by how soon a complex project hits them" (`docs/sdlc/phase-2-roadmap.md:14`). `docs/sdlc/spikes/build-stage-from-claude-agents.md:47` ranks its borrows "cheap-first". **Drift is not ranked anywhere against cost or time.**

## Q14. Which surfaces does the repo assume sessions run on?

- **A remote/cloud agent container** — the default assumption. `docs/sdlc/handoff/HANDOFF.md:11` "container state is gone; only git survives"; `:24` "Git identity in a new remote session is again an agent identity"; `:181-183` "No `gh` binary in the remote container… Locally, prefix `GH_TOKEN= GITHUB_TOKEN=`".
- **A phone (GitHub web editor + Actions tab)** — the owner's surface. `HANDOFF.md:105` "the owner works from a phone; keep every ask to taps"; `docs/sdlc/github-setup.md:34-40`; `knowledge/lessons/send-ledger-lines-in-a-fenced-block.md:12`.
- **Windows 10 / Git Bash / Python 3.12-3.13 / `core.autocrlf=true`** — `docs/sdlc/phase-2-roadmap.md:82-102` (roadmap item 19), with (a) bare `python3` and one `os.access` test still open at `:100-102`.
- **GitHub Actions runners (Linux)** — all six workflows; `scripts/deploy.sh` refuses without `CI` set (`docs/sdlc/README.md:118`).
- **Gemini CLI** and **Antigravity** — `.gemini/settings.json`; `docs/sdlc/rules/50-gemini-only.md:27-28`.
- **Desktop app / another PC** are named once, as a reason not to put the unlock in the launching shell: `knowledge/decisions/self-hooks-on.md:83` — "every new environment (desktop app, cloud session, another PC) forgets it".
- **Cowork: NOT ANSWERED IN REPO.** `grep -rni "cowork"` over the tree returns nothing. Closest: the "cloud session" line above.

## Q15. Plan mode, worktrees, parallel sessions: prescribed vs used

**Prescribed:**
- Plan mode: `docs/sdlc/README.md:28` "Plan mode as the default start"; `.claude/skills/sdlc-plan/SKILL.md:3,7` "In plan mode, read an approved spec.md… Work in plan mode; do not edit code." Under Gemini it is explicitly *not* a gate: `docs/sdlc/rules/50-gemini-only.md:18-19` "Leaving plan mode with `exit_plan_mode` is **not** an approved `plan.md`"; `docs/sdlc/spikes/gemini-parity.md:58-61` "auto-approves `enter_plan_mode`/`exit_plan_mode` — so plan mode is **not** an approval gate in CI."
- Worktrees / 2-3 parallel sessions: `docs/sdlc/README.md:32` (the playbook row) and `docs/sdlc/phase-2-roadmap.md:105-106` ("worktree-per-work-item convention" — Phase 3, unbuilt).

**Evidence of actual use — the repo did the opposite:**
- `work/sdlc-kit-phase-1/plan.md:80` — "Options not taken: **worktree-per-task** (merge overhead for a solo owner)".
- `docs/sdlc/handoff/HANDOFF.md:216-217` — "Hooks change serially, never in parallel worktrees"; `docs/sdlc/handoff/PLAN.md:65` — "WI-2..WI-6 all touch `_lib.sh` or the hooks: land serially, never in parallel worktrees."
- `work/ci-budget/intent.md`, Q3's answer — "one agent code pull request open at a time; intent-only ones may run beside it".
- One documented worktree use, for verification only: `work/batch-b-followups/plan.md:80` — "checked in a detached worktree with the fixed script".
- Parallel *read-only subagents* were used and are the sanctioned pattern: eight analysts in `docs/sdlc/handoff/lifecycle-axis-vs-playbook.md:12-14`; three scouts on `ci-budget` (`work/ci-budget/log.md:14`). `knowledge/decisions/one-writer-until-ledger.md:25-26` — "One writer per work item… Subagents are read-only".
- Plan mode used as designed: every `work/*/plan.md` was written before implementation; `work/sdlc-kit-phase-1/spec.md:13` — "Plan-mode session".

## Q16. Budget shape: subscription vs API, Actions minutes, spending limits

- **Actions minutes, measured:** `work/ci-budget/intent.md:22-27` — "the repository is private, created 2026-09-02; 1,124 runs since; GitHub Free includes 2,000 Actions minutes a month for private repositories, billed per job and rounded up to the minute"; the quota exhausted at "2026-09-08 21:43 UTC"; breakdown `sdlc-gate` ~770 min, `pr-review` ~650, `agent-evals` ~300, `delegated-merge` ~100, nightlies ~80, "About 1,900 in six days, against a 2,000 allowance: about 30 billed minutes each, over the 62 pull requests opened in that window."
- **Plan limits:** `knowledge/decisions/merge-click-is-the-gate.md:20-23` — "On 2026-09-02 every one of those endpoints answered `403 Upgrade to GitHub Pro or make this repository public`… private repositories on the Free plan get none of them". `docs/sdlc/github-setup.md:51-55` repeats it for adopters.
- **Resolution taken:** the owner made the repository **public**, nothing else changed — `work/ci-budget/intent.md`, Constraints: "Done 2026-09-09: the owner made the repository public and changed nothing else; the gate ran green on this pull request's head at 12:36 UTC, in 32 seconds." The spending limit and plan are explicitly **out of scope**: "Out of scope: repository visibility, the spending limit and the GitHub plan (the owner's account decision…)".
- **Model spend:** subscription *or* API, both optional. `docs/sdlc/github-setup.md:86-88` — "`ANTHROPIC_API_KEY` at repository scope **with a spend limit**, or `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token` on a **Pro/Max plan**." `work/sdlc-kit-phase-1/intent.md:54` — "an `ANTHROPIC_API_KEY` with a console spend limit is added to CI"; `:56` — "Team/Pro". `docs/sdlc/spikes/prompt-surfaces.md` §2.6 Point 3 names "where the SDK is used, its spend cap" as a deterministic cap — unbuilt.
- **No per-run or per-item budget exists in code.** No cost, budget or token field in any script, config or ledger.

## Q17. Cost ledger / `cost_per_merged_pr`: status, and what depends on it

**Status: does not exist.** `docs/sdlc/phase-2-roadmap.md:35-39`, Phase 2 item 1 — "The playbook names 'agent budget' and reads timings from git and OTel but never attributes spend. **Add** a per-work-item ledger (tokens, tool calls, retries, human review minutes, gate wait) and a `cost_per_merged_pr` control band." Nothing is marked done on that item. `monitoring/bands.yaml` has three metrics, none of them cost. `docs/sdlc/metrics.md:30-31` — "Not defined by the playbook, added in the roadmap: cost per completed task (tokens, tool calls, retries, human minutes) attributed to a work item and owner."

**What depends on it:**
1. `knowledge/decisions/one-writer-until-ledger.md` — the whole record. `:36-43`: "This record expires on the first `cost_per_merged_pr` reading from roadmap item 1's ledger for this repository, **or on 2027-03-05**, whichever comes first. On expiry the question reopens with one measurement, not a debate: over ten of this kit's own work items, a role pipeline with a writing `implementer` costs less than 1.5 times a bare session and shows no silent-delegation failure (a diff the lead did not read before the PR)." Until then the `implementer` role "stays designed, not scheduled".
2. `docs/sdlc/spikes/prompt-surfaces.md` §2.6 — "The routing is revised by data, not by opinion: the Phase 2 cost ledger per work item… is the measurement that says whether a row is paying off… Until the ledger exists, the table stays as small as it is above."
3. `docs/sdlc/spikes/prompt-surfaces.md` §4 Phase C — "The pins land with the cost ledger from the roadmap or, if that is not yet built, with a one-line per-work-item token count in `log.md` as its stand-in, so the routing table has a number to be judged by from its first day."
4. `docs/sdlc/phase-2-roadmap.md:38-39` — item 1b "is judged by this ledger; until it exists, that spike's Phase C uses a per-work-item token count in `log.md` as the stand-in."

## Q18. Any measurement of tokens per item or human time per item?

**No.** The stand-in was designed (`prompt-surfaces.md` §4 Phase C, "a one-line per-work-item token count in `log.md`") and never implemented: `grep -rni "token" work/*/log.md` returns only prose about "wasted tokens" as a goal (`work/ci-budget/log.md:13`) and an unrelated `GH_TOKEN` note. No `log.md` carries a token count, tool-call count, retry count or human-minute figure. `docs/sdlc/templates/log.md`'s line format is `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>` (quoted at `work/run-queue/log.md:10-11`) — there is no cost slot.

**What *is* measured per item, from timestamps:** `scripts/sdlc_metrics.py` "prints four of them (intent→spec and spec→plan hours, two rework counts)" (`docs/sdlc/metrics.md:11-12`). `scripts/github_metrics.py` supplies `ci_test_failure_rate` and `pr_cycle_time_hours` (`monitoring/bands.yaml:7,25`) — PR cycle time is the only proxy for human latency. Gate-wait timestamps exist only in the git-ignored `.sdlc/hook-decisions.log` (`docs/sdlc/metrics.md:25`).

**One-off measurements, in prose:** the 1,124-run / ~1,900-minute audit in `work/ci-budget/intent.md:22-67`; `work/delegated-mode/intent.md:27` — "ledgers record 44 approvals, the plans record 68 deviations, and every merge was a click from a phone."

## Q19. Smallest human act per item as currently designed

**Supervised mode** (`docs/sdlc/github-setup.md:15-47`, `HANDOFF.md:105-131`, `CLAUDE.md:34-45`):
1. Approve `intent.md` — one tap: *Actions → approve → Run workflow* with `slug`, `artifact`, `mode` (`.github/workflows/approve.yml:22-40`; `CLAUDE.md:38-40`). Alternatives: the approval script from the owner's own shell, or the web editor plus a pasted ledger line (`CLAUDE.md:41-45`).
2. Approve `spec.md` — a second tap (the script "enforces intent → spec → plan order", `CLAUDE.md:42`).
3. Approve `plan.md` — a third tap.
4. Apply `control-plane-approved` where the diff touches `PROTECTED_PATHS` — "PR page → '…' (top right) → Edit → Labels" (`HANDOFF.md:119`).
5. Merge click — "the owner clicks merge on the PR page; never merge from the session" (`HANDOFF.md:120-122`; `knowledge/decisions/merge-click-is-the-gate.md:35-37`).
6. Retire the item — set `superseded` on intent/spec/plan, one ledger line each, and clear or move `.sdlc/active` (`CLAUDE.md:15-17`; `HANDOFF.md:169-172`: "Retiring an item is a human act, from the web editor today… **Nothing *retires* an item on merge**"). A one-tap retire is an unopened follow-up (`work/retire-active-pointer/spec.md:130`).
7. Answer the intent interview's open questions (`.claude/skills/sdlc-intent/SKILL.md:11-13`).
8. Triage a band-breach issue (`bands.yml:158` "a human turns the drafted intent.md above into an approved work item"). Under `ci-budget` a `triage` label also becomes a human act (`work/ci-budget/intent.md`, Q2's answer: "A: label").

**Delegated mode** (`.claude/skills/sdlc-run/SKILL.md`, `docs/sdlc/github-setup.md:97-134`):
1. One grant tap per item — `artifact: intent.md`, `mode: delegated`, branch `main` (`SKILL.md:11-14`; `HANDOFF.md:123-128`). The tap also repoints `.sdlc/active`.
2. Nothing else, in theory: spec, plan, implementation, review, ready and merge are all the agent's or CI's (`SKILL.md:24-35`; `docs/sdlc/README.md:113`).
3. A merge click survives for locked-path items — `SKILL.md:60-63` "a pull request that needs the owner's merge click — a locked-path item never merges on its own"; observed on both delegated items: `work/retire-active-pointer/log.md:20` and `work/run-queue-followups/log.md:21` both end "check_artifact_chain.py is a locked path, so the merge is the owner's click".
4. Retirement is still human (as above).
5. Callbacks: deviation cap, `keep` verdict, locked path, unfixable red check, unexplained hook refusal (`SKILL.md:56-63`).

**The floor stated as a rule:** `SKILL.md:66-68` — "a queue of N items is **N human grants, never one grant for N**" (also `knowledge/decisions/run-queue.md`, cited on `origin/claude/standing-grant-intent`, which asks to change exactly this).

## Q20. Delegated mode and the queue: evidence of end-to-end runs

**Evidence of delegated *authoring*, yes; of the queue *advancing without a human*, no.**

- `docs/sdlc/handoff/HANDOFF.md:49-52` — "**Delegated mode has run a full item end to end.** `work/approve-by-dispatch` (#51), `work/retire-active-pointer` (#53), `work/run-queue` (#55, #57) and `work/run-queue-followups` (#56 intent, #58 implementation) are the record. The queue machinery works: `scripts/next_item.py` orders it, `delegated_merge.py` advances `.sdlc/active` after a merge, and `/sdlc-run` loops on its own pull request."
- The ledgers show agent signatures throughout: `work/retire-active-pointer/log.md:15-19` (`in-review -> delegated | claude`), `work/run-queue/log.md:16-19`, `work/run-queue-followups/log.md:16-20`, `work/approve-by-dispatch/log.md` (`plan.md | in-review -> delegated | claude`, `bf15030`). Grants are human: `retire-active-pointer/log.md:14` (`luissiviero | 1c8c209 | mode: delegated`), `run-queue/log.md:15` (`79e9a30`), `run-queue-followups/log.md` (`336470c`).
- **But both completed delegated items ended at a human click**, by their own ledger lines: `work/retire-active-pointer/log.md:20` and `work/run-queue-followups/log.md:21` — "check_artifact_chain.py is a locked path, so the merge is the owner's click **and the queue ends here**".
- **And the advance has never landed.** `origin/claude/advance-push-intent:work/advance-push/intent.md:36-52` (unmerged, `status: in-review`): "`git log --grep=\"Advance .sdlc/active\"` on `main` is empty: **no advance commit has ever landed**… The remote `main` is not an ancestor of the pushed commit, so the push is rejected as non-fast-forward, on every real merge, not only in a race… So `work/run-queue`'s 'zero human input between items' is, today, one merge and then an idle pointer that still names the merged item. A second granted item is never opened." Confirmed here: `git log origin/main --grep="Advance .sdlc/active"` returns nothing; `grep -n "fetch\|ff-only" scripts/delegated_merge.py` returns one unrelated comment (`:587`).
- The one `.sdlc/active` move after a merge was made by a human commit, not the bot: `308f1a2 Replace 'run-queue-followups' with 'ci-budget'`.
- **Contradiction on whether the mode is even on.** `.sdlc/delegation.yaml:13` reads `enabled: True` today. But `docs/sdlc/github-setup.md:106-107` says "In the kit's own repository it is `false` until the owner turns it on", and `HANDOFF.md:76-78` says "it stays `enabled: false` on `main` — the owner's own commit, 9e405fa — until the owner flips it back." The live file is the authority; both docs are stale.
- `merge.require-checks: [sdlc-gate, pr-review]` (`.sdlc/delegation.yaml:52`) — `agent-evals` was already trimmed, matching `HANDOFF.md:79-82`.

## Q21. Which artifacts are required per item, which are generated, which drift checks

**Required by the chain (`scripts/check_artifact_chain.py:9-12`, `docs/sdlc/README.md:80`):** `work/<slug>/intent.md`, `spec.md`, `plan.md` (and `incident.md` when one exists), each with front matter carrying `status` from `("draft","in-review","approved","delegated","superseded")` (`:60`) and `approved-by` only on `approved|delegated|superseded` (`:717`), plus `work/<slug>/log.md` with a matching ledger entry per approval (`:733-777`). Stage order is enforced one stage per PR (`:703-710`). `docs/sdlc/templates/` holds intent, spec, plan, incident, log, revision.

**Conditionally required:** `work/<slug>/revisions/<n>.md` — only when re-signing an already-signed or approved artifact under `revisions: consensus` (`.sdlc/delegation.yaml:35-43`; `docs/sdlc/README.md:112`). Three exist; each item that has one also has a hand-written `revisions/index.md`.

**Generated:** `work/<slug>/index.md` and `work/index.md` by `scripts/gen_index.py` (docstring `:2-31`, "Output is byte-stable: no generation timestamp is ever written"); `CLAUDE.md`, `GEMINI.md`, `AGENTS.md` by `scripts/gen_context_files.py` from `docs/sdlc/rules/` (`.sdlc/config.env:37-40`). All are in `GENERATED_PATHS` (`.sdlc/config.env:16`) and excluded from review findings (`REVIEW.md:23`).

**Drift checks in `scripts/checks/` (all run by `verify.sh`):**
- `index-drift.sh` → `gen_index.py --check` (work indexes)
- `context-drift.sh` → `gen_context_files.py --check` (the three context files)
- `front-matter.sh` → `check_front_matter.py` (strict YAML on every tracked Markdown file)
- `okf.sh` → `check_okf.py` (type field, links, RFC3339 timestamps; warning-only, `OKF_STRICT="0"`)
- `eval-cases.sh` → `check_eval_cases.py` (refuses a case that cannot fail)
- `plugin-manifest.sh` → `check_plugin_manifest.py` (every skill/agent listed and vice versa)
- `workflow-permissions.sh` → `check_workflow_permissions.py`; `workflow-yaml.sh` (every workflow parses)

Not generated and hand-kept, so they drift: `knowledge/*/index.md` and `docs/sdlc/*/index.md` (`docs/sdlc/handoff/consensus.md:41` — "the hand-maintained decisions index that is already stale"; `work/run-queue-followups/log.md:20` — "three lessons from #55 and #57 were never indexed"). `docs/sdlc/handoff/` has no drift check. `gen_index.py --check` currently prints `INDEX: up to date`.

## Q22. Do skills batch questions at the start or ask mid-item?

**Batched at the start, in bounded rounds, then the skill stops.**
- `.claude/skills/sdlc-intent/SKILL.md:10-13` — "Interview the originator in their own words. Ask until you can fill every section without inventing: problem, who is affected, how we would observe success, hard constraints, what is explicitly out of scope, risk class, and which mode they want to run under, supervised or delegated. **Ask at most three questions per turn.** Record unanswered ones under 'Open questions'." Then `:19` — "Stop. A human sets `status: approved`… Ask for the tap."
- The template carries the batch forward: `## Open questions (agent asks; originator answers; carried into spec.md if unresolved)` — seen at `work/ci-budget/intent.md`, six questions each with a proposal and an `A:` line.
- **Mid-item, `/sdlc-run` does not ask — it stops.** `.claude/skills/sdlc-run/SKILL.md:56-63`, "## Stop and call the owner back — Each of these stops the **whole queue**, not just the item: say which item and why, **once**, and do not start the next one." Five triggers listed. `:41` — "When it is empty, the queue is done — say so once and stop."
- Same discipline in the owner routine: `HANDOFF.md:129-131` — "Every request to the owner ends with the phone steps. Send one clear list; do not restate a decision already made".
- `/sdlc-spec` and `/sdlc-plan` do not interview beyond what the previous artifact carries (`.claude/skills/sdlc-plan/SKILL.md:7`, "Precondition: `work/<slug>/spec.md` is approved").

## Q23. What kinds of target projects does the kit assume?

**Language-agnostic by construction, Python-shaped in practice.**
- Explicitly per-repo: `work/sdlc-kit-phase-1/intent.md:41-42` — "Q: Which stacks and commands? A: Per repo, one `scripts/verify.sh` reading `VERIFY_CMDS`/`FORMAT_CMD`/`TEST_FILE_GLOBS` from `.sdlc/config.env`; the adopt script leaves `VERIFY_CMDS` as a TODO for the adopter rather than guessing." `docs/sdlc/github-setup.md:22-24` — placeholder examples "`npm test`, `pytest -q`, `make lint`".
- `TEST_FILE_GLOBS="*_test.* *.test.* *_spec.* *.spec.* test_*.py tests/* test/* __tests__/* evals/cases/*"` (`.sdlc/config.env:19`) — Go/JS/Ruby/Python conventions.
- `RELEASE_GATED_PATHS="migrations infra terraform helm"` (`.sdlc/config.env:12`) — assumes DB migrations and IaC (Terraform, Helm). Roadmap item 3 wants "a migration linter in `verify.sh` (destructive ops, lock analysis, reversibility), migrations in `RELEASE_GATED_PATHS`, and a data-migration standards skill" (`docs/sdlc/phase-2-roadmap.md:53-55`) — unbuilt.
- `GENERATED_PATHS="src/gen …"` (`.sdlc/config.env:16`) — assumes a codegen directory.
- `PLAN_REQUIRED_PATHS="scripts"` here; `work/sdlc-kit-phase-1/intent.md:43-44` — "are `src lib app services packages` the right plan-required paths… A: `work/<slug>/` inside each product repo; the plan-required paths default stays and is edited per repo."
- Deploy surface assumed by the production gate regex: kubectl, helm, terraform, pulumi, aws (cloudformation/lambda/ecs/s3), gcloud run/app/functions, az webapp, npm publish, twine, docker push, flyctl, vercel, serverless, capistrano, `deploy.sh`, `gh release create|workflow run|pr merge` (`.claude/hooks/production-gate.sh:26`). `monitoring/bands.yaml:22` grants `Bash(kubectl logs *)` at 2σ for `post_deploy_5xx_rate` — the metric with no source.
- Repo topology: `work/<slug>/` inside each product repo, one repo at a time. Multi-repo is Phase 3 (`docs/sdlc/phase-2-roadmap.md:105-106`).
- Team shape: `docs/sdlc/handoff/consensus.md:41` — "Most additions exist because the playbook assumes a team and a platform admin that do not exist here."

## Q24. How does a project adopt the kit, and how do updates propagate?

**Two halves of one decision (Q10 of the phase-1 decisions):**

1. **`scripts/adopt.sh <target>`** — the template half. `knowledge/decisions/adopt-script.md:11-21`: the plugin ships skills, agents, commands, templates and scripts "but deliberately *not* hooks, because a red line must not be a per-user plugin toggle. That leaves a gap: something still has to put the control plane (`.sdlc/`), the deterministic hooks, and the CI workflows into a new repository, since none of those travel with the plugin. `scripts/adopt.sh` is that something — the template half of the same Q10 decision, **run once per adopting repo rather than installed and auto-updated like the plugin**." Flags at `scripts/adopt.sh:4-31`: `--force`, `--dry-run`, `--with-hooks`, `--no-create`. It never overwrites without `--force`, is idempotent, rewrites the owner's handle to `<your-github-handle>`, seeds `CLAUDE.md`'s project sections, and installs `.claude/settings.json` from `docs/sdlc/templates/claude-settings.json` — "not from the kit's own `.claude/settings.json`, which adds the control-plane unlock" (`:12-16`).
2. **Plugin / marketplace** — `.claude-plugin/plugin.json` (`name: lifecycle-axis-sdlc`, `version: 0.1.0`, `skills: ./.claude/skills`, four agents) and `.claude-plugin/marketplace.json`. `knowledge/decisions/plugin-distribution.md` is the record; `docs/sdlc/README.md:142-143` — "`claude --plugin-dir .` from this repo, or add it to a marketplace via `.claude-plugin/marketplace.json` — for the skills, agents, and templates **without the repo-local hooks**." `scripts/check_plugin_manifest.py` + `scripts/checks/plugin-manifest.sh` fail verify on manifest drift.

**Update propagation:** only the plugin half updates centrally. `docs/sdlc/phase-2-roadmap.md:61-67`, item 6 — "Package this repo as a plugin (skills, agents, hooks, templates) plus a thin template repo, **so projects update centrally**. **Done in phase 1:** … Hooks stay repo-local, installed via `scripts/adopt.sh --with-hooks` rather than shipped inside the plugin." So hooks, `.sdlc/`, workflows and CI are a one-time copy with no update path other than re-running `adopt.sh --force` (which "carries across" the adopter's `VERIFY_CMDS`, `PLAN_REQUIRED_PATHS` and approver handle, `scripts/adopt.sh:6-8`).

**The remainder is manual:** `docs/sdlc/github-setup.md` "The first hour, in order" (`:15-47`) plus branch protection, the `control-plane-approved` label, secrets, and the Claude GitHub App (`:57-95`).

## Q25. Does the kit enforce its rules on itself?

**Yes, with the control plane deliberately unlocked, and rule 3 therefore advisory.** The decision was reversed once on the same day.

`knowledge/decisions/self-enforcement-off.md` (2026-09-02, **superseded**), `:11-13`: "**Superseded on 2026-09-02 by `self-hooks-on.md`.** The owner reinstated the hooks on this repo with the control-plane unlock set in `.claude/settings.json`; the template and `adopt.sh` behaviour described below still hold for adopters." Its reasoning, `:20-24`: "That is where the kit's own maintenance stalled: the Bash-write guard (rule 3) blocks any edit under `.claude/hooks`, `.github/workflows` and `.sdlc`, so the security hardening of those very files had to go through the owner's GitHub connector, which wrote the hooks without their executable bit (fff489a), which turned CI red, which the agent could not fix locally because the same guard, plus the harness's own safety classifier, refused every route. The owner then decided the kit must not police its own repository."

`knowledge/decisions/self-hooks-on.md` (2026-09-04, current), `:34-37`: "**`.claude/settings.json` returns** with exactly the template's `hooks` block plus `\"env\": {\"SDLC_CONTROL_PLANE_UNLOCK\": \"1\"}`." `:38-41`: "**The unlock applies per protected path on both branches**… The secret-material check (`.env`, `*.pem`, `*.key`, `id_rsa`, …) runs regardless of the unlock, on both branches." `:54-58`: "The guards are live again in this repo: no credential-shaped content in any write, no writes to secret-looking files, plan required for code under `PLAN_REQUIRED_PATHS`… test files locked during a `kind: fix` item, force pushes and hard resets refused, a push to `main` prompts the owner, and a turn that changed plan-required code without a verify run is sent back." `:59-67`: "Rule 3 in `CLAUDE.md` stays advisory in this repo, now with evidence: every control-plane write by an agent is appended to `.sdlc/hook-decisions.log`… The unlock never covers `.sdlc/release-authorizations/`, `.sdlc/approvers.yaml` or the log itself. CI's `check_control_plane.sh`… and CODEOWNERS routing to the owner remain the deterministic gate."

`.claude/settings.json` today: `:2-4` `"env": {"SDLC_CONTROL_PLANE_UNLOCK": "1"}`; `:6-9` a `deny` list (`.env`, `secrets/**`, `~/.ssh/**`, `~/.aws/**`, `WebFetch`, `curl`, `wget`); `:10-15` an `allow` list (verify, run_tests, run_evals, chain check, git status/diff/log, `sign.py`, `gh pr ready|comment|create`, `git push -u origin claude/*`); `:17-55` the seven hooks — five on `Edit|Write|MultiEdit|NotebookEdit`, six on `Bash` (adding `production-gate.sh`), `post-edit-format.sh` on PostToolUse, `stop-verify-reminder.sh` on Stop.

Distilled in the lesson: `knowledge/lessons/control-plane-unlock-is-advisory.md` — "This repo runs its own hooks with `SDLC_CONTROL_PLANE_UNLOCK=1`, so a control-plane write passes with an audit line and a `systemMessage`; CI and the owner's review guard the control plane, not the hook." Pointer at `CLAUDE.md:96`.

**Where self-enforcement is weakest:** `knowledge/decisions/merge-click-is-the-gate.md:45` — "A red check does not stop a merge; the person clicking has to look"; and the unretired `run-queue-followups` chain (Q2) shows the retirement rule not being applied to the kit itself.

## Q26. Each unmerged branch: proposal, commits ahead, and whether the content is on main

| Branch | Ahead / behind main | Proposal (3 lines max) | On main? |
|---|---|---|---|
| `claude/standing-grant-intent` | 4 / 26 | `work/standing-grant/intent.md` (`status: in-review`, `risk-class: medium`): "Delegated mode is the state every session starts in, a subject typed in and a merged pull request out, with no per-item tap." Problem: the grant is per item and per human commit, read by six call sites (`check_artifact_chain.py:299-368`, `sign.py:143-156`, `next_item.py:55-58`, `delegated_merge.py:386-410`, `_lib.sh:211-217`); "a queue of N items is N human grants". Outcome: move the grant for low-risk items into the human-only policy file as one standing grant, let the agent sign the intent under it, and let the merge workflow open a new item when the pointer is empty; supervised becomes what the owner asks for. | **No.** `work/standing-grant/` does not exist on main. |
| `claude/risk-detour-intent` | 4 / 26 | `work/risk-detour/intent.md` (`in-review`, `low`): "A delegated item that meets non-low work looks for a low-only route by reviewer consensus, and parks instead of stopping the queue." Problem: the risk class is refused terminally in five places, `/sdlc-run` stops the whole queue, and the revision record only asks for "the smallest change that clears the trigger", never for a low-only route; no item has ever had a non-`low` risk class, and parking has nowhere to live (the status vocabulary is closed). Outcome: convene reviewers at every gate for a route reaching the outcome on low-risk surface only, adopt on a unanimous verdict, otherwise park the item and continue. | **No.** |
| `claude/advance-push-intent` | 4 / 26 | `work/advance-push/intent.md` (`in-review`, `low`): "The post-merge advance never lands, because it pushes from a checkout older than the merge it follows." Evidence: `delegated-merge.yml:77-79` checks out main before the merge; the API merge moves main; the advance pushes `HEAD:main` from the stale checkout (`delegated_merge.py:960-995`), the rejection is swallowed (`:993-997`), and `git log --grep="Advance .sdlc/active"` on main is empty. Outcome: fetch and fast-forward onto the merged main before the dirty-tree check and any write, with a regression test whose bare remote moves. | **No** — and the bug is still live: `grep -n "fetch\|ff-only" scripts/delegated_merge.py` finds nothing relevant on main. |
| `claude/approve-tap-regenerates-index` | 5 / 20 | `work/approve-tap-regenerates-index/intent.md` (`in-review`, `low`, `mode: supervised`): "The approval tap commits an approval whose indexes are stale; make the tap regenerate what it changes." Evidence: c0aa58c, 3da8bb6 and a903a91 each committed exactly three paths and no `index.md`; `approve_dispatch.py`'s comment "gen_index.py's index.md is regenerated in the same tree" describes a step that does not exist; `work/index.md` is not even in the allowlist. Outcome: the tap regenerates and commits every index, heals pre-existing drift, and the allowlist and comment say what is true. | **No.** The defect persists: nothing in `.github/workflows/approve.yml` runs the index generator, and the false comment is still at `scripts/approve_dispatch.py:57`. (The specific c0aa58c drift was cleaned by later commits — `gen_index.py --check` now prints `INDEX: up to date`.) |
| `claude/handoff-close` | 4 / **138** | Three doc commits: mark HANDOFF's "Current state" as history, rewrite "Task state" to 2026-09-05 07:10 (the 2026-09-04 plan complete; both manual checks each found a defect — `bands.yml` missing `pull-requests: read`, and the flaky `skill-spec-flags-concerns` eval), correct the suggested first prompt, and add `knowledge/lessons/workflow-permissions-name-every-api.md`. | **Effectively yes, and superseded.** The lesson file and its pointer are on main (`knowledge/lessons/workflow-permissions-name-every-api.md`, `docs/sdlc/rules/60-lessons.md:21`). Main's `HANDOFF.md` already carries the "HISTORY, superseded by" markers (`:28`) and a newer Task state dated 2026-09-08 (`:48-61`). The branch is 138 commits behind; merging it would regress the handoff. |
| `claude/agent-plan-adherence-4b4mqk` (PR 67) | **2 / 0** (tip of main) | `work/plan-adherence/intent.md` (`in-review`, `low`, `mode: supervised`): "A plan executed in a new session is forgotten mid-run, and the agent deviates from it." See Q11 for the quoted problem and outcome: a `SessionStart(compact)` hook reprinting the plan, a `UserPromptSubmit` progress line, a new hook refusing an off-plan path at exit 2, a `Stop` unplanned-path report, a five-field tickable step shape, and an `Input:` line on every agent file. | **No.** `work/plan-adherence/` does not exist on main; `.claude/settings.json` on main still declares only `PreToolUse`/`PostToolUse`/`Stop`. |

Other unmerged branches present but not asked about: 9 `kit/*` and 1 `spike/*` branches (all 2026-09-03/04, superseded by main), `claude/session-handoff`, `claude/next-steps-ach27y`, `claude/delegate-mode-next-steps-szrg8d`, `claude/sdlc-queue-pointer-checks-m2yh7y`, `claude/github-scheduled-task-emails-96b6ye`, `claude/pr-63-plan-review-ekiuva`, `claude/project-feasibility-discussion-kx5f0g` (the last three are merged into main via PRs 63 and 64), plus the two Dependabot branches (Q28).

## Q27. Handoff / consensus documents from other sessions

**`docs/sdlc/handoff/` is on `main`** (9 files) and identical in file list on `claude/session-handoff` and `claude/handoff-close`. Contents (`docs/sdlc/handoff/index.md:11-19`):
- `HANDOFF.md` — 19.6 KB. Resume steps (`:11-27`), "Current state (2026-09-05) — HISTORY" (`:28-46`), "Task state (2026-09-08 ~19:40 UTC)" (`:48-61`), "Task state (2026-09-06) — HISTORY" (`:63-103`), "Owner routine (the owner works from a phone; keep every ask to taps)" (`:105-131`), "Suggested first prompt" (`:132-139`), "What the earlier sessions did" (`:141-150`), "Hard facts that govern implementation" (`:152-210`), "Work-item order" (`:212-217`).
- `PLAN.md` (53.9 KB) — the approved 2026-09-04 implementation plan, eleven work items plus Step 0, with verified hook/gate code in an appendix.
- `consensus.md` (14.3 KB) — the reconciliation of the owner's row-by-row artifact with the adversarial report; the source of the "consensus-item-N" tags on the intents.
- `lifecycle-axis-vs-playbook.md` (36.2 KB) — the adversarial comparison, eight read-only analysts, file:line evidence.
- `bypass_table.md` (8.7 KB) — the Bash write-guard bypass evidence.
- `AUTHOR_BRIEF.md` (4.2 KB) — how the Batch A artifacts were drafted.
- `place.sh`, `check_artifacts.py` — helpers; "Copy them to the new session's scratchpad before use (they must not run from inside `docs/`)" (`HANDOFF.md:21-23`).

**What is on a branch and not on main:** only `claude/handoff-close`'s edits to `HANDOFF.md`, and those are *older* than main's version (the branch is 138 behind; main already contains the "HISTORY, superseded by" markers that branch introduced, plus two later Task-state sections). Its one genuinely new artifact, `knowledge/lessons/workflow-permissions-name-every-api.md`, is already on main. `git show origin/claude/session-handoff:docs/sdlc/handoff/consensus.md` returns the same document that is on main.

**No root-level `HANDOFF.md` exists on any branch** — every hit across all 45 remote refs is under `docs/sdlc/handoff/`.

**The proposed per-item handoff file does not exist:** `docs/sdlc/spikes/build-stage-from-claude-agents.md` §3.5 proposes `work/<slug>/handoff.md` with `## State` / `## Next action` / `## Open items` / `## Settled`, capped at 100 lines with `scripts/checks/handoff-cap.sh` — the spike is `status: open` (`:8`) and none of it is built.

## Q28. Issue 40 (band breach) and the two Dependabot pull requests

**Issue 40.** Filed automatically by the Maintain loop's first green run. `knowledge/decisions/delegated-mode.md:47-49` (and the `claude/handoff-close` version of HANDOFF): "Run 7 is the first green one, and the first time the Maintain stage ran end to end: it detected a 3σ breach (**21.31 hours against a trailing mean of 2.67** on `pr_cycle_time_hours`), diagnosed it read-only, and filed **issue 40** with a drafted `pr-review-bottleneck` intent." Its status on main: `docs/sdlc/handoff/HANDOFF.md:101-103` — "Issue 40 (the `pr-review-bottleneck` intent the band detector filed) **is still open for the owner to answer or close**; this work neither read nor answered it." It became the `record:` of `work/delegated-mode` (`intent.md:13`, `spec.md:15`, `plan.md:14`).

**What the kit says should happen to it:** `.github/workflows/bands.yml:158` — "Filed automatically by the bands workflow. This workflow only ever opens issues, never pull requests — **a human turns the drafted intent.md above into an approved work item.** While the breach stays in the series, each nightly run comments here instead of filing again." `docs/sdlc/README.md:38` — "diagnosis written as `intent.md`", gate "service owner triages". `monitoring/bands.yaml:32` gives `pr_cycle_time_hours` a 3σ route of `report:engineering-leadership` — a declared route with no code. `/sdlc-incident` is named as "the manual follow-up" (`docs/sdlc/README.md:157`). Nothing closes it automatically; `work/band-detector/spec.md:166` — "the comment lands on the one open issue and carries `index`; closing the issue ends the thread; the next night files a new issue only if the breach is still in the series."

**The two Dependabot PRs.** Both are one-line SHA bumps of pinned actions, opened 2026-09-09, one commit each:
- `origin/dependabot/github_actions/actions/upload-artifact-7.0.1` — `2527b9e ci: bump actions/upload-artifact from 4.6.2 to 7.0.1`, touching `.github/workflows/bands.yml` only.
- `origin/dependabot/github_actions/anthropics/claude-code-action-1.0.217` — `17552d3 ci: bump anthropics/claude-code-action from 1.0.213 to 1.0.217`, touching `.github/workflows/pr-review.yml` only.

**What the kit says should happen:** `.github/dependabot.yml:1-6` — "Every `uses:` line is pinned to a full commit SHA (a tag is mutable; whoever controls the action can move it to code that runs with this repo's secrets). Dependabot opens a PR when a pinned action publishes a new release and rewrites the SHA plus the version comment; **a human reviews and merges it.** The `npm install -g @anthropic-ai/claude-code@<version>` lines are pinned by hand and are not covered here." `docs/sdlc/phase-2-roadmap.md:74-80` (item 18) records the pins as **Done** with dependabot as the mechanism. Because both diffs touch `.github/workflows/` (a `PROTECTED_PATHS` entry, `.sdlc/config.env:9`) and Dependabot is a Bot author, CI blocks them until a human applies `control-plane-approved`: `knowledge/decisions/merge-click-is-the-gate.md:32-34` — "`scripts/check_control_plane.sh` keeps failing the gate for a bot-authored or `claude/*` diff under `PROTECTED_PATHS` until a human applies `control-plane-approved`. **Dependabot's workflow bumps go through exactly that route (first case: PR #5).**"

Note the `upload-artifact` jump 4.6.2 → 7.0.1 is a major-version bump; nothing in the repo has a policy on major bumps beyond "a human reviews and merges it".

## Q29. Where would a meta-revision document live by convention?

Four precedents, each with a different placement rule:

1. **A meta-review of the kit against an external standard → `docs/sdlc/handoff/`.** This is the exact precedent: `docs/sdlc/handoff/lifecycle-axis-vs-playbook.md` (the report) and `consensus.md` (the reconciliation), both `type: doc`, `tags: [sdlc, handoff, playbook-comparison]`, indexed by `docs/sdlc/handoff/index.md:11-19`, with `PLAN.md` as the resulting work-item plan. They were written by a session that changed nothing else ("No file in the repo was changed; `git status` is clean", `lifecycle-axis-vs-playbook.md:16`), and were converted afterwards into eleven `work/<slug>/` items.
2. **A design investigation that backs a future decision → `docs/sdlc/spikes/<name>.md`**, `type: spike`, with `status:` from a three-word vocabulary defined at `docs/sdlc/spikes/index.md:9-13`: `open` | `accepted` | `decided`. `docs/sdlc/README.md:63` — "design spikes that back a decision". Six exist; `prompt-surfaces.md` (accepted) and `build-stage-from-claude-agents.md` (open) are the meta-est of them, both about how the kit steers agents.
3. **A settled choice with alternatives and consequences → `knowledge/decisions/<name>.md`**, `type: decision`, sections Context / Decision / Consequences / Alternatives considered / Links (the shape of all sixteen; e.g. `self-hooks-on.md`, `one-writer-until-ledger.md`). Used when a spike is arbitrated: `one-writer-until-ledger.md` settles the contradiction between two spikes and carries an expiry (`:36-43`).
4. **Anything that will change files → `work/<slug>/` with the full chain.** `CLAUDE.md:11-17`; every kit change since 2026-09-02 (`work/index.md:11-30`). `docs/sdlc/spikes/build-stage-from-claude-agents.md:23-24` states the rule: "**Nothing here is adopted by being written.** The developer decides in a later session; if adopted, the work goes through the chain as its own work item (see §5)."

So by convention a *meta revision of the kit* is a read-only report under `docs/sdlc/handoff/` (or a spike under `docs/sdlc/spikes/` if it proposes one coherent design), whose accepted conclusions become `knowledge/decisions/` records and `work/<slug>/` items. A `work/<slug>/revisions/<n>.md` is **not** the right home — that name is reserved for re-signing one artifact of one item (Q1).

## Q30. Session continuity: what a new session gets to resume

- **`docs/sdlc/handoff/HANDOFF.md`** is the designated entry point. `:9` "Session handoff (read this first after any context reset)"; `:11-27` "How to resume in a NEW session (container state is gone; only git survives)" — read HANDOFF, then `work/delegated-mode/plan.md` and `knowledge/decisions/delegated-mode.md`; "No task list to re-create: no work item is open"; "Re-arm an hourly `send_later` check-in and subscribe to each PR you open (`subscribe_pr_activity`). Every earlier session deleted its trigger on handoff so two sessions never act on the same PR"; a first check that `protect-approvals.sh` is live. `:132-135` gives a **verbatim suggested first prompt**.
- **`:152-210` "Hard facts that govern implementation"** is the operational memory: the agent git identity, the `GH_TOKEN= GITHUB_TOKEN=` prefix, atomic hook edits, the `work/index.md` merge-conflict recipe, the plan-bullet and ledger-slot formats, the four verification lines.
- **`.sdlc/active`** names the item in progress (`ci-budget` today). `.claude/skills/sdlc-run/SKILL.md:41-43` — "If the session ends mid-queue, nothing is lost: the pointer on `main` is already correct, so the next session resumes at the right item with no repair." (This rests on the advance that has never landed — Q20.)
- **`work/<slug>/log.md`** is the per-item gate ledger, append-only, format at `docs/sdlc/templates/log.md` (quoted at `work/run-queue/log.md:10-11`), parsed by `scripts/log_ledger.py`; the deviation notes on `plan.md` lines are in practice the design record ("its deviations log is the most recent design record", `HANDOFF.md:13`).
- **`work/<slug>/index.md` and `work/index.md`** give progressive disclosure (`docs/sdlc/okf-pairing.md:58`), regenerated by `gen_index.py`.
- **Helper scripts** `docs/sdlc/handoff/place.sh` and `check_artifacts.py` (`HANDOFF.md:21-23`).

**Gaps the repo itself records:** there is no per-item "where was I / what is next" file — `docs/sdlc/spikes/build-stage-from-claude-agents.md` §3.5: "This kit has `log.md` (gate ledger) and `knowledge/decisions/` but **no 'where was I and what is next' file**, and app-sized work items will span sessions" (proposed `work/<slug>/handoff.md`, spike `status: open`, nothing built). And no step is marked done on disk — `origin/claude/agent-plan-adherence-4b4mqk:work/plan-adherence/intent.md:53-59`: "Progress has no place on disk… nothing marks a step done, so a resumed session cannot tell where the previous one stopped except by re-deriving it from the diff."

---

## Coverage

**Files read on `origin/main`:**
`CLAUDE.md`, `GEMINI.md` (line count), `AGENTS.md` (line count), `README.md`, `REVIEW.md`
`.sdlc/README.md`, `.sdlc/config.env`, `.sdlc/active`, `.sdlc/approvers.yaml`, `.sdlc/delegation.yaml`, `.sdlc/environments.yaml`
`.claude/settings.json`; `.claude/agents/{explorer,plan-reviewer,security-reviewer,verifier}.md`; `.claude/hooks/_lib.sh`, `production-gate.sh`, `protect-approvals.sh` (targeted greps)
`.claude/skills/{sdlc-intent,sdlc-run,sdlc-review,sdlc-plan}/SKILL.md`
`.gemini/settings.json`; `.gemini/agents/{explorer,plan-reviewer,security-reviewer,verifier}.md`
`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`
`.github/dependabot.yml`; `.github/workflows/{agent-evals,approve,bands,delegated-merge,deploy,pr-review,sdlc-gate}.yml`
`docs/sdlc/README.md`, `docs/sdlc/phase-2-roadmap.md`, `docs/sdlc/metrics.md`, `docs/sdlc/okf-pairing.md`, `docs/sdlc/github-setup.md`
`docs/sdlc/rules/{30-conventions,40-claude-only,50-gemini-only,60-lessons}.md`
`docs/sdlc/spikes/{index,prompt-surfaces,build-stage-from-claude-agents}.md`
`docs/sdlc/templates/revision.md`
`docs/sdlc/handoff/{index,HANDOFF,consensus,lifecycle-axis-vs-playbook}.md` (+ file listing of `AUTHOR_BRIEF.md`, `PLAN.md`, `bypass_table.md`, `check_artifacts.py`, `place.sh`)
`knowledge/decisions/{self-enforcement-off,self-hooks-on,one-writer-until-ledger,merge-click-is-the-gate,adopt-script}.md`; front matter of all 16 decisions
`knowledge/lessons/*.md` (title + description of all 14, plus `index.md`)
`monitoring/bands.yaml`
`scripts/adopt.sh` (header), `scripts/gen_index.py` (docstring), `scripts/check_artifact_chain.py` (greps), `scripts/delegated_merge.py` (greps), `scripts/approve_dispatch.py` (grep), `scripts/checks/*.sh` (all 8 headers)
`work/index.md`; front matter of all 20 `work/*/intent.md`; `work/ci-budget/{intent,log}.md` in full; `work/{retire-active-pointer,run-queue,run-queue-followups,approve-by-dispatch}/log.md`; `work/*/revisions/{1,index}.md` (headings); `work/sdlc-kit-phase-1/{intent,plan,spec}.md` (partial)
`evals/cases/` (file listing, 51 cases); full repository file listing

**Branches inspected:**
`origin/main` (log, 399 commits), `origin/claude/standing-grant-intent`, `origin/claude/risk-detour-intent`, `origin/claude/advance-push-intent`, `origin/claude/approve-tap-regenerates-index`, `origin/claude/handoff-close`, `origin/claude/agent-plan-adherence-4b4mqk`, `origin/claude/session-handoff`, `origin/dependabot/github_actions/actions/upload-artifact-7.0.1`, `origin/dependabot/github_actions/anthropics/claude-code-action-1.0.217`; full remote branch listing (45 refs) with dates and tip subjects.

**Commands run:** `git log`, `git rev-list --count`, `git diff --stat`, `git show <branch>:<path>`, `git ls-tree`, `git for-each-ref`, `python3 scripts/gen_index.py --check`, `wc -l`, plus targeted `grep`/`ls`/`find`.
