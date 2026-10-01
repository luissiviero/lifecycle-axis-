---
type: doc
title: "Evidence: drift audit"
description: "The kit's own checks run on main, docs compared to code, dead references, declared-but-unbuilt features, divergence from the founding plan, and the bookkeeping share of recent merges; produced read-only for the 2026-09-10 step review."
tags: [sdlc, revision, evidence]
timestamp: 2026-09-10T14:00:00Z
---
# Drift audit — lifecycle-axis- (read-only, 2026-09-10)

Audited at `ca8dd32` (`origin/main`), working tree clean. No repository file was modified.
Scope and method follow the nine steps requested; every finding cites files read or commands run.

---

## 1. The repo's own checks

Run in order. Raw outputs are in the Coverage section.

| Command | Last line | Verdict |
|---|---|---|
| `scripts/verify.sh` (as-is, `GH_TOKEN`/`GITHUB_TOKEN` set) | `VERIFY: FAIL` | **red** |
| `GH_TOKEN= GITHUB_TOKEN= scripts/verify.sh` | `VERIFY: PASS (ca8dd32)` | green |
| `python3 scripts/run_tests.py` (inside verify) | `Ran 835 tests in 32.204s` / `OK` | green |
| `python3 scripts/check_artifact_chain.py --base HEAD` (tokens set) | `FileNotFoundError: ... 'gh'` (traceback) | **crash** |
| `GH_TOKEN= GITHUB_TOKEN= python3 scripts/check_artifact_chain.py --base HEAD` | `CHAIN: PASS` | green |
| `scripts/run_evals.sh` (inside verify) | `EVALS: 44 pass, 0 fail, 6 skipped` | green |
| `python3 scripts/check_okf.py` | `OKF: 182 docs, 0 warnings` | green |
| `python3 scripts/gen_index.py --check` | `INDEX: up to date` | green |
| `python3 scripts/gen_context_files.py --check` | `CONTEXT: 3 files up to date` | green |
| `scripts/checks/*.sh` (8, inside verify) | all `✔ pass` | green |

Both `--check` flags exist (`scripts/gen_index.py:254`, `scripts/gen_context_files.py:207`); `check_okf.py` takes `--strict`/`--root`/`paths` (`scripts/check_okf.py:66-71`) and was run bare, as CLAUDE.md prescribes.

- [severity: high] `scripts/verify.sh` ends `VERIFY: FAIL` on a clean checkout of `main` in any environment that has a GitHub token but no `gh` binary, because `verify_dispatch_run` guards on the token and then shells out to `gh` with no `FileNotFoundError` handling — the kit's single pass/fail signal fails on its own repo — evidence: `scripts/check_artifact_chain.py:196`, `scripts/check_artifact_chain.py:201`, `scripts/verify.sh:11`
- [severity: high] The failure is a bare Python traceback, not a check message, so an adopter sees a crash rather than the "no token / attestation skipped" degradation the same function implements one branch earlier — evidence: `scripts/check_artifact_chain.py:196-197`, `scripts/check_artifact_chain.py:201-203`
- [severity: medium] The repo already knows about this crash and has carried it as an unfixed follow-up since at least 2026-09-08, with a manual `GH_TOKEN= GITHUB_TOKEN=` prefix as the workaround, but neither CLAUDE.md's "Verifying your work" block nor `docs/sdlc/README.md` mentions the prefix — so every doc that tells a reader to run `verify.sh` omits the one thing that makes it pass — evidence: `docs/sdlc/handoff/HANDOFF.md:53-55`, `docs/sdlc/handoff/HANDOFF.md:60-62`, `CLAUDE.md:43`
- [severity: low] `VERIFY: FAIL` prints no sha, so the failing line cannot be pasted into a PR the way CLAUDE.md's contract (`VERIFY: PASS (<sha>)`) implies — evidence: `scripts/verify.sh:30`, `CLAUDE.md:43`

---

## 2. Docs vs code

Read: all 9 `.claude/hooks/*.sh`, all 7 `.github/workflows/*.yml`, all 7 `.claude/skills/*/SKILL.md`, all 4 `.claude/agents/*.md` + 4 `.gemini/agents/*.md`, all 27 non-test `scripts/*.py|*.sh` (headers/argparse; full read for `verify.sh`, `deploy.sh`, `check_control_plane.sh`, `bands_config.py`, `_lib.sh`), against `docs/sdlc/README.md`, `CLAUDE.md`, `docs/sdlc/rules/*.md`, `.sdlc/README.md`, `evals/README.md`, `REVIEW.md`, `docs/sdlc/github-setup.md`, `knowledge/`.

### Claims that are not true of the code

- [severity: high] `docs/sdlc/README.md` states twice that the reviewer subagents are read-only and "have no write tools", and `security-standards` §8 repeats it as policy, but all four `.claude/agents/*.md` grant `Bash` with no command bound, which can write any path the hooks do not cover (`work/`, `docs/`, `evals/`, `knowledge/`, `.claude/skills/`) — evidence: `docs/sdlc/README.md:105`, `docs/sdlc/README.md:73`, `.claude/skills/security-standards/SKILL.md:16`, `.claude/agents/verifier.md:4`, `.claude/agents/security-reviewer.md:4`
- [severity: high] The `.gemini/agents/*.md` mirrors constrain the shell in prose ("Shell is for `git diff` only"), and CLAUDE.md rule 8 promises "bounded tools", but the Claude-side agents carry no such sentence and no tool bound at all — the Gemini mirror is more constrained than the primary — evidence: `.gemini/agents/security-reviewer.md:8-16`, `.claude/agents/security-reviewer.md:4`, `CLAUDE.md:39`
- [severity: high] `docs/sdlc/github-setup.md:72` and `docs/sdlc/README.md:153` both instruct an adopter to make `agent-evals` a required status check, while `docs/sdlc/github-setup.md:132` in the same file explains that `agent-evals.yml` has a `paths:` filter and therefore has no run at all on most PRs; a required check that never reports blocks every pull request permanently — evidence: `docs/sdlc/github-setup.md:72`, `docs/sdlc/github-setup.md:132`, `docs/sdlc/README.md:153`, `.github/workflows/agent-evals.yml:9-11`
- [severity: high] The same `agent-evals` name was removed from `.sdlc/delegation.yaml`'s `merge.require-checks` for exactly that reason, but the adoption docs above were never updated and `.github/workflows/delegated-merge.yml:26` still calls the `workflow_run` list "The three workflows `.sdlc/delegation.yaml` names in `merge.require-checks`" when the policy names two — evidence: `.sdlc/delegation.yaml:52`, `.github/workflows/delegated-merge.yml:26`, `.github/workflows/delegated-merge.yml:31`, `work/ci-budget/intent.md:63-66`
- [severity: high] `REVIEW.md` and `/sdlc-review` both instruct the reviewer to add a line to a `CLAUDE.md` "Lessons learned" section that no longer exists — the section was moved into `docs/sdlc/rules/60-lessons.md` by `work/docs-reconcile`, and CLAUDE.md is now fully generated, so following the instruction would fail `scripts/checks/context-drift.sh` — evidence: `REVIEW.md:13`, `.claude/skills/sdlc-review/SKILL.md:14`, `CLAUDE.md:93`, `docs/sdlc/rules/60-lessons.md:10`
- [severity: medium] `docs/sdlc/README.md`'s enforcement matrix lists `post-edit-format.sh` as the deterministic control for "Formatting never drifts", but `FORMAT_CMD` is empty in this repo, so the hook exits on its first line and enforces nothing — evidence: `docs/sdlc/README.md:102`, `.sdlc/config.env:22`, `.claude/hooks/post-edit-format.sh:4`
- [severity: medium] `docs/sdlc/README.md:74` lists the hooks as "protect-paths, block-secrets, require-plan, protect-tests, production-gate, post-edit-format, stop-verify-reminder" — it omits `protect-approvals.sh`, which is the hook the whole human-only-approvals decision rests on, and `_lib.sh` — evidence: `docs/sdlc/README.md:74`, `.claude/hooks/protect-approvals.sh:1`, `.claude/settings.json:26`
- [severity: medium] `docs/sdlc/README.md:78` lists five `scripts/checks/*.sh`; there are eight on disk — `eval-cases.sh`, `front-matter.sh` and `workflow-yaml.sh` are undocumented in the file map even though all three run in `verify.sh` and one of them (`workflow-yaml.sh`) exists because an invalid workflow silently disabled the gate — evidence: `docs/sdlc/README.md:78`, `scripts/checks/` (8 files), `work/sdlc-kit-phase-1/plan.md:122`
- [severity: medium] `docs/sdlc/README.md:63` names four spikes; six exist (`build-stage-from-claude-agents.md` and `red-team-pass.md` are missing from the map), and `docs/sdlc/index.md` omits `github-setup.md`, `lessons.md` and the whole `handoff/` directory — evidence: `docs/sdlc/README.md:63`, `docs/sdlc/spikes/index.md:16-28`, `docs/sdlc/index.md:9-24`
- [severity: medium] `evals/README.md:9-10` enumerates the gate-test prefixes but omits `sign-*` (5 cases), `approve-*` and `run-*`, so a third of the deterministic suite is outside the documented taxonomy — evidence: `evals/README.md:9-10`, `evals/cases/sign-refuses-without-grant.yaml`, `evals/cases/run-queue-stops-on-empty.yaml`
- [severity: medium] `.sdlc/README.md` documents 11 config keys but not the seven original ones (`PLAN_REQUIRED_PATHS`, `PROTECTED_PATHS`, `RELEASE_GATED_PATHS`, `GENERATED_PATHS`, `TEST_FILE_GLOBS`, `FORMAT_CMD`, `VERIFY_CMDS`), which are the keys an adopter must actually edit first — evidence: `.sdlc/README.md:5-17`, `.sdlc/config.env:4-25`
- [severity: medium] `CLAUDE.md`'s "Hard rules (enforced by hooks and CI, not by good intentions)" heading covers eight rules, but rules 6 (evidence and the five-nit cap), 7 (mistake twice → memory) and 8 (subagent roles and bounded tools) have no hook, no CI check and no eval; the README's own matrix admits this with a `—` in the deterministic column for rule 7 — evidence: `docs/sdlc/rules/10-hard-rules.md:10`, `CLAUDE.md:18`, `docs/sdlc/README.md:118`
- [severity: low] `docs/sdlc/README.md:110` says `approve.yml` has "four inputs"; `CLAUDE.md:72` and all five skills say three (`slug`, `artifact`, `mode`) — the fourth, `note`, is real and used twice in the workflow but appears in no skill — evidence: `docs/sdlc/README.md:110`, `CLAUDE.md:72`, `.github/workflows/approve.yml` (inputs: artifact, mode, slug, note)
- [severity: low] `docs/sdlc/spikes/gemini-parity.md` still carries `status: open` although its consequence is built and recorded (`.gemini/settings.json`, `.gemini/agents/`), which the spikes index defines as `decided` — evidence: `docs/sdlc/spikes/gemini-parity.md:7`, `docs/sdlc/spikes/index.md:9-12`, `knowledge/decisions/gemini-hooks.md:10-11`
- [severity: low] `knowledge/decisions/one-rule-source.md` is the only decision carrying a front-matter `status:`, and it still reads `in-review` although the mechanism it decides has shipped and gates `verify.sh` — evidence: `knowledge/decisions/one-rule-source.md:9`, `scripts/checks/context-drift.sh`
- [severity: low] `.sdlc/delegation.yaml:13` reads `enabled: True` where the shipped template reads `enabled: true`, and the live file has lost the template's paragraph explaining why `agent-evals` must not be in `require-checks` — the template is now more current than the control plane it templates (both readers cope: `policy_value` folds case, `_as_bool` accepts `True`) — evidence: `.sdlc/delegation.yaml:13`, `docs/sdlc/templates/delegation.yaml:13`, `docs/sdlc/templates/delegation.yaml:51-54`, `.claude/hooks/_lib.sh:187`

### Claims that check out

`require-plan.sh`, `protect-paths.sh`, `protect-tests.sh`, `block-secrets.sh`, `production-gate.sh`, `protect-approvals.sh`, `check_control_plane.sh`, `delegated_merge.py`, `detect_bands.py`, `bands_config.py`, `adopt.sh`, `deploy.sh` and all seven workflows behave as `docs/sdlc/README.md`'s matrix and `CLAUDE.md` describe on every other row checked. `adopt.sh` correctly swaps `PLAN_REQUIRED_PATHS` to the adopter default and `VERIFY_CMDS` to a deliberately-failing placeholder (`scripts/adopt.sh:420-421`). `detect_bands.py`'s exit codes match CLAUDE.md (`scripts/detect_bands.py:99-100`). The three generated context files are byte-identical to their fragments.

---

## 3. Dead references

Every backticked repo-shaped path in `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `README.md`, `REVIEW.md`, `docs/sdlc/README.md`, `.sdlc/README.md`, `evals/README.md`, `docs/sdlc/metrics.md`, `lessons.md`, `okf-pairing.md`, `github-setup.md`, `index.md`, all `docs/sdlc/rules/*.md`, all `docs/sdlc/templates/*.md` and all of `knowledge/` was resolved against disk; every `- <path> — …` bullet under every `## Files that change` in all 20 work items was resolved the same way.

- [severity: low] Only three dead references in the whole core doc set, all benign: two are template-relative shorthands and one is a forward reference to an unbuilt Antigravity adapter — evidence: `knowledge/lessons/skills-spell-template-headings.md:12-13`, `knowledge/decisions/gemini-hooks.md:94`
- [severity: low] Every path listed under `## Files that change` in all 20 plans exists; no dead plan entries — evidence: `work/*/plan.md` (19 plans scanned), `work/ci-budget/implementation-plan.md`
- [severity: low] `docs/sdlc/lessons.md` is a live pointer and its target resolves; `docs/sdlc/handoff/` is complete and its `index.md` lists all seven members — evidence: `docs/sdlc/lessons.md:11`, `docs/sdlc/handoff/index.md:11-19`
- [severity: medium] `docs/sdlc/handoff/HANDOFF.md` is the file every reset session is told to read first, and its live "Task state" is dated 2026-09-08 and asserts "No task list to re-create: no work item is open" — but `.sdlc/active` names `ci-budget`, whose intent was approved 2026-09-10 and whose implementation has not started — evidence: `docs/sdlc/handoff/HANDOFF.md:16`, `docs/sdlc/handoff/HANDOFF.md:48`, `.sdlc/active:1`, `work/ci-budget/log.md:18`
- [severity: medium] `HANDOFF.md`'s "Owner routine" tells the owner "the owner clicks merge on the PR page; never merge from the session" with no delegated-mode caveat, while the delegated route merges with no click at all — the same document's history section says delegation is `enabled: false`, which it no longer is — evidence: `docs/sdlc/handoff/HANDOFF.md:125-126`, `docs/sdlc/handoff/HANDOFF.md:78-82`, `.sdlc/delegation.yaml:13`, `.sdlc/delegation.yaml:46`
- [severity: low] `work/sdlc-kit-phase-1/control-plane.patch` (462 lines) is an applied 2026-09-02 patch still committed inside a superseded work item; it is cited only as historical explanation — evidence: `work/sdlc-kit-phase-1/control-plane.patch:1`, `knowledge/decisions/bash-write-guard.md:72`

---

## 4. Obsolete or unreachable code and config

Call sites were greped across `scripts/`, `.github/workflows/`, `.claude/hooks/`, `.claude/skills/`, `evals/cases/`, `scripts/checks/` and `VERIFY_CMDS`.

- [severity: medium] `GENERATED_PATHS` is a config key no code reads — every other key in `.sdlc/config.env` has at least one reader; this one is cited only in prose by `REVIEW.md`, so the "do not report generated files" rule is advisory with nothing behind it — evidence: `.sdlc/config.env:16`, `REVIEW.md:23` (grep for `GENERATED_PATHS` across `.claude/`, `scripts/`, `.github/` returns nothing)
- [severity: medium] `.claude/hooks/post-edit-format.sh` cannot fire in this repo: `FORMAT_CMD=""` makes line 4 exit before anything runs, and no test or eval covers the enabled path — evidence: `.claude/hooks/post-edit-format.sh:4`, `.sdlc/config.env:22`
- [severity: medium] The eval `kind: e2e` is declared in the runner, the validator and the README, but zero `e2e` cases exist — `--kind e2e` is a selector for an empty set — evidence: `scripts/run_evals.sh:28-30`, `scripts/check_eval_cases.py:22`, `evals/README.md:14`, `evals/cases/` (44 hook, 6 skill, 0 e2e)
- [severity: medium] `.github/workflows/delegated-merge.yml`'s `workflow_run.workflows` still lists `agent-evals` alongside a comment claiming the policy names three; the policy names two, so every `agent-evals` completion wakes the merge job to print "waiting" — the repo's own cost analysis measured about 100 billed minutes across 185 such wakes — evidence: `.github/workflows/delegated-merge.yml:26`, `.github/workflows/delegated-merge.yml:31`, `.sdlc/delegation.yaml:52`, `work/ci-budget/intent.md:64-66`
- [severity: medium] `bash_write_targets`' step-3 whole-command rule adds **every** plan-required/protected prefix that appears anywhere in the text of an inline-interpreter command, so a read-only `python3 -c` or `python3 - <<EOF` that merely mentions the string `scripts` is blocked as a write — reproduced three times during this audit on pure-read analysis scripts — evidence: `.claude/hooks/_lib.sh:335-338`, `.claude/hooks/_lib.sh:227`, `.claude/hooks/require-plan.sh:50-55`
- [severity: low] `check_artifact_chain.py --no-approvers` is implemented and unit-tested but documented nowhere an adopter reads (only in the superseded phase-1 spec), so the intended early-adopter escape hatch is effectively invisible — evidence: `scripts/check_artifact_chain.py:497`, `scripts/test_check_artifact_chain.py:166`, `work/sdlc-kit-phase-1/spec.md:142`
- [severity: low] `.sdlc/environments.yaml`'s `github_environment:` key is read by no script — `deploy.yml` passes the raw `environment` input straight through, and the mapping happens to be an identity — evidence: `.sdlc/environments.yaml:9`, `.github/workflows/deploy.yml:16-20` (grep for `github_environment` finds only YAML and prose)
- [severity: low] No workflow input is unused; all 7 inputs across `approve.yml`, `deploy.yml` and `delegated-merge.yml` are referenced — evidence: `.github/workflows/approve.yml`, `.github/workflows/deploy.yml`, `.github/workflows/delegated-merge.yml`
- [severity: low] Every non-test script in `scripts/` has at least one caller or documented invocation; the least-referenced (`check_eval_cases.py`, `check_front_matter.py`) are both wired through `scripts/checks/` — evidence: `scripts/checks/eval-cases.sh`, `scripts/checks/front-matter.sh`
- [severity: low] `knowledge/lessons/eval-checks-have-no-blank-lines.md` has no pointer line in `60-lessons.md`; this is correct by the stated rule (a check now makes the mistake impossible) but leaves 14 lesson files behind 13 pointers with nothing recording why — evidence: `knowledge/lessons/eval-checks-have-no-blank-lines.md:1`, `docs/sdlc/rules/60-lessons.md:11`, `work/run-queue/log.md:21`

---

## 5. Declared but not built

- [severity: high] `.github/CODEOWNERS` — the file that decides who must review a change — is not in `PROTECTED_PATHS`, so `protect-paths.sh` allows an agent to rewrite it (verified: exit 0) and `check_control_plane.sh`, which iterates the same list, will not flag it either; the same is true of `.claude/skills/`, `.claude/agents/`, `REVIEW.md` and `.claude-plugin/`, which `.sdlc/delegation.yaml` locks for *delegated merges only* — evidence: `.sdlc/config.env:11`, `.claude/hooks/protect-paths.sh:44-47`, `scripts/check_control_plane.sh:55-63`, `.sdlc/delegation.yaml:63`
- [severity: high] `work/retire-active-pointer/spec.md:166` asserts "`.claude/skills` is control-plane", and the item shipped, but `PROTECTED_PATHS` never gained it — the agent's own instruction set is writable by the agent, with only `agent-evals.yml`'s regression suite (not a block) behind it — evidence: `work/retire-active-pointer/spec.md:166`, `.sdlc/config.env:11`, `.github/workflows/agent-evals.yml:9-11`
- [severity: medium] `monitoring/bands.yaml`'s 3σ `propose` routes (`pull_request`, `runbook:rollback-deploy`, `report:engineering-leadership`) are declared and never acted on — `bands.yml` treats 3σ exactly like 2σ and only files an issue, and no code reads `routes:` at all; this is disclosed, but it means the Maintain loop's escalation tier is decoration — evidence: `monitoring/bands.yaml:14`, `.github/workflows/bands.yml:52-54`, `.github/workflows/bands.yml:96-98`, `docs/sdlc/README.md:38`
- [severity: medium] `post_deploy_5xx_rate` is a metric with a prose string where its `source:` command should be; `bands_config.py` silently drops it from the matrix, so its 2σ `kubectl logs` tier and its knowledge doc describe behaviour that can never run — evidence: `monitoring/bands.yaml:17-18`, `scripts/bands_config.py:120-122`, `knowledge/metrics/post-deploy-5xx-rate.md:44-46`
- [severity: medium] The `record:` field is present and empty on all 58 chain artifacts and in all four templates, is read by no script and validated by no check, yet `docs/sdlc/README.md:48` presents it as the mechanism for the playbook's "source of truth" linkage — evidence: `docs/sdlc/README.md:48`, `docs/sdlc/templates/intent.md`, `work/*/intent.md` (all `record:` empty; grep for a non-empty value returns nothing)
- [severity: medium] `scripts/deploy.sh` "never executes a deploy command — it prints the command it *would* run"; the entire Deploy stage below the gate is a placeholder, and `.sdlc/release-authorizations/` contains only `.gitkeep`, so the release-authorization path has never been exercised — evidence: `scripts/deploy.sh:3-4`, `.sdlc/release-authorizations/` (only `.gitkeep`), `docs/sdlc/README.md:37`
- [severity: low] Phase-2 roadmap items marked **Done** were verified present: item 0 (OKF bundle, rules fragments, `gen_context_files.py`, `log.md`, `check_okf.py`, `.gemini/settings.json`), item 6 (`plugin.json`, `marketplace.json`, `check_plugin_manifest.py`), item 12 (`agent-evals.yml`, `--kind/--only/--list`), item 13 (`detect_bands.py`, `github_metrics.py`, `bands_config.py`, `bands.yml`), item 17 (`bash_write_targets`/`bash_write_candidates` in `_lib.sh`), item 18 pins (every `uses:` carries a SHA, `.github/dependabot.yml` present), item 19 (`.gitattributes`, drive-letter handling) — no false "Done" found — evidence: `docs/sdlc/phase-2-roadmap.md:18-28`, `docs/sdlc/phase-2-roadmap.md:60-67`, `.github/dependabot.yml:7-9`, `.gitattributes`
- [severity: low] Item 1 (cost and budget attribution) is unbuilt, which is correctly stated, and the `implementer` role of `spikes/prompt-surfaces.md` §2.6 is provisionally overruled by a decision that expires 2027-03-05 — the pointer chain is intact — evidence: `docs/sdlc/phase-2-roadmap.md:37-48`, `knowledge/decisions/one-writer-until-ledger.md:4`
- [severity: low] Item 2 (computed risk tiers) is unbuilt: `risk-class` is a hand-filled front-matter field read by `approve.py`, `sign.py`, `check_artifact_chain.py` and `delegated_merge.py`, derived by nothing — evidence: `docs/sdlc/phase-2-roadmap.md:49-51`, `scripts/check_artifact_chain.py:364`, `scripts/delegated_merge.py:404`
- [severity: low] The `prompt-surfaces` spike is `status: accepted` and entirely unbuilt — `scripts/check_prompt_surfaces.py`, `scripts/checks/prompt-lint.sh` and `.claude/skills/prompting-standards/` do not exist; this is correctly labelled "Designed, not scheduled" — evidence: `docs/sdlc/spikes/prompt-surfaces.md:8`, `docs/sdlc/spikes/prompt-surfaces.md:50`, `docs/sdlc/phase-2-roadmap.md:40-47`
- [severity: low] `/sdlc-build` is designed in a spike and referenced by four documents; no such skill exists, and every mention labels it as unbuilt — evidence: `docs/sdlc/spikes/build-stage-from-claude-agents.md:56`, `work/delegation-boundary/intent.md:77`
- [severity: low] Security scans and Claude Tag / on-call appear only in the playbook digest and the "Not doing" list; nothing claims they are built — evidence: `docs/sdlc/README.md:39-40`, `work/sdlc-kit-phase-1/spec.md` ("## Not doing")

---

## 6. Divergence from the founding plan

`work/sdlc-kit-phase-1/spec.md` defines T01–T24 (25 requirement rows, R-T01…R-T24 plus R-T11). **All 24 tasks were delivered**: every named file exists, including `scripts/fixtures/hook_inputs/{edit,write,multiedit,bash,notebookedit}.json`, `knowledge/runbooks/rollback-deploy.md`, `docs/sdlc/lessons.md` as a pointer, and all five `scripts/checks/*.sh` T05/T14/T16/T17/T20/T21 called for. Nothing in the plan was silently dropped.

The divergence is not in the tasks; it is in the three **outcomes** the intent promised.

- [severity: high] Intent outcome 2 — "the deterministic gates hold regardless of which model produced the change (**CI and branch protection**, not only hooks)" — is half-delivered: `main` carries no branch-protection rule at all (the branches API reports `protected: false`), so every CI check is advisory and the merge click is the only gate for supervised items, with nothing at all for delegated ones beyond the merge script — evidence: `work/sdlc-kit-phase-1/intent.md:26`, `work/ci-budget/log.md:16`, `knowledge/decisions/merge-click-is-the-gate.md:12-14`
- [severity: high] The intent's answer to "Who approves what?" promised that "agents act under a separate bot/App identity that can never approve; branch protection requires one human review" — neither holds: the kit's own sessions commit under the owner's identity, which is precisely why `check_control_plane.sh` had to grow a commit-trailer rule, and there is no branch protection to require the review — evidence: `work/sdlc-kit-phase-1/intent.md:44-45`, `scripts/check_control_plane.sh:17-20`, `work/ci-budget/log.md:16`
- [severity: high] Intent outcome 1 — "a new project can adopt the kit in under an hour and the loop runs by hand end to end" — needed a whole remedial work item (`adopter-first-hour`, "A fresh install of the kit breaks in the first hour"), and the adoption instructions it produced still contain the `agent-evals` required-check trap of §2 — evidence: `work/sdlc-kit-phase-1/intent.md:25`, `work/adopter-first-hour/intent.md` (title), `docs/sdlc/github-setup.md:72`
- [severity: medium] Delivered differently: T24 promised `EVALS: ≥17 pass`; the suite is now 50 cases, 44 deterministic and 6 prompt-driven — a genuine over-delivery, but `evals/README.md`'s "20–50 cases drawn from real recent tasks" target is met almost entirely by gate tests of the kit's own machinery, not by the playbook's "real tasks" — evidence: `work/sdlc-kit-phase-1/spec.md:191`, `evals/README.md:5`, `evals/cases/` (44 `hook`, 6 `skill`)
- [severity: medium] Delivered differently: the phase-1 spec's "## Not doing" list explicitly excluded Gemini hooks; they were built three weeks later, so `.gemini/settings.json` now runs the same scripts and `.gemini` had to be added to `PROTECTED_PATHS` after the fact — evidence: `work/sdlc-kit-phase-1/spec.md` ("## Not doing"), `knowledge/decisions/gemini-hooks.md:1-11`, `.sdlc/config.env:11`
- [severity: medium] Reversal chain 1 — `self-enforcement-off.md` (the kit repo does not wire its own hooks) was superseded the same day by `self-hooks-on.md`, which wires them plus a standing `SDLC_CONTROL_PLANE_UNLOCK=1` in `.claude/settings.json`; the net effect is that rule 3, presented in CLAUDE.md as a hard red line, is advisory in this repo — evidence: `knowledge/decisions/self-enforcement-off.md:10-12`, `.claude/settings.json:2-4`, `knowledge/lessons/control-plane-unlock-is-advisory.md:1`, `CLAUDE.md:94`
- [severity: medium] Reversal chain 2 — `merge-click-is-the-gate.md` (CI is informational, a human clicks) was superseded for delegated items by `delegated-mode.md` (a workflow merges, no click), which was itself amended twice: by `approve-by-dispatch.md` (the grant becomes a tap) and by `run-queue.md` (the merge, not the session, advances `.sdlc/active`); four records now describe one mechanism — evidence: `knowledge/decisions/merge-click-is-the-gate.md:11-13`, `knowledge/decisions/delegated-mode.md:11-32`, `knowledge/decisions/run-queue.md:9-10`
- [severity: medium] Reversal chain 3 — `human-only-approvals.md` ("only a human can flip an artifact to approved") was amended by `delegated-mode.md` so an agent signs `delegated`; the words `approved` and `delegated` now mean different things to `approvers.yaml` (which lists `claude` under `never-approve`) and to `delegation.yaml` (which lists `claude` under `agents`), and the two files must be read together to know who may write what — evidence: `knowledge/decisions/human-only-approvals.md:10-12`, `.sdlc/approvers.yaml:31`, `.sdlc/delegation.yaml:22`

---

## 7. Internal contradictions still marked current

Supersession hygiene is generally good: `self-enforcement-off.md`, `merge-click-is-the-gate.md` and `human-only-approvals.md` all carry banners, and `run-queue.md` carries `amends:` in front matter with a back-pointer in `delegated-mode.md`. The contradictions below are the ones nothing marks.

- [severity: high] `knowledge/decisions/merge-click-is-the-gate.md` rests entirely on "the owner chose to keep the repo private on the Free plan", where branch protection returns 403; the repository was made public on 2026-09-09 and the decision carries no amendment — so the reason the kit gives for having no branch protection is no longer true, while `docs/sdlc/README.md` cites this record in three enforcement rows — evidence: `knowledge/decisions/merge-click-is-the-gate.md:27-29`, `work/ci-budget/intent.md:147`, `docs/sdlc/README.md:105`, `docs/sdlc/README.md:119`
- [severity: high] `.claude/skills/security-standards/SKILL.md:16` ("Reviewer subagents are read-only") and `.claude/agents/*.md:4` (`tools: Read, Grep, Glob, Bash`) are flatly opposite and both current; the skill is loaded as a *hard constraint* during Design, Build and Review — evidence: `.claude/skills/security-standards/SKILL.md:16`, `.claude/agents/plan-reviewer.md:4`
- [severity: high] `REVIEW.md:13` / `.claude/skills/sdlc-review/SKILL.md:14` instruct an edit to `CLAUDE.md` that `knowledge/decisions/one-rule-source.md:36` and `docs/sdlc/rules/60-lessons.md` forbid (edit the fragment, never the generated file) — two current documents give opposite instructions for the same act — evidence: `REVIEW.md:13`, `knowledge/decisions/one-rule-source.md:36`, `docs/sdlc/rules/60-lessons.md:10`
- [severity: high] `docs/sdlc/rules/00-chain.md:23` (rendered into all three context files) states that a human retires a completed item with `superseded` on its artifacts — but `work/ci-budget/log.md:17` records that this is **impossible** for any delegated item, because a `superseded` artifact needs a valid human approver and delegated artifacts carry `approved-by: claude`, which `.sdlc/approvers.yaml` lists under `never-approve`; the rule and the recorded defect are both current — evidence: `docs/sdlc/rules/00-chain.md:23`, `work/ci-budget/log.md:17`, `.sdlc/approvers.yaml:31`
- [severity: high] The consequence is visible in the tree: 19 of 20 work items are still `approved`/`delegated` and only `sdlc-kit-phase-1` was ever retired, so `work/index.md` presents 19 open items, the plan gate has no closed plan behind it, and `work/retire-active-pointer` — the item that wrote the retirement rule — is itself unretired — evidence: `work/index.md:10-30`, `work/retire-active-pointer/intent.md` (`status: approved`), `docs/sdlc/rules/00-chain.md:23`
- [severity: medium] `.sdlc/active` names `ci-budget`, whose plan is a non-standard `implementation-plan.md`; `require-plan.sh` looks for `work/<slug>/plan.md`, so the plan gate is closed for `scripts/` today, and `gen_index.py`'s `ARTIFACTS` tuple cannot see the file, so `work/ci-budget/index.md` lists an item with no plan while a 1,000-line plan sits beside it — evidence: `.sdlc/active:1`, `work/ci-budget/implementation-plan.md`, `.claude/hooks/require-plan.sh:19`, `scripts/gen_index.py:42`, `work/ci-budget/index.md:9-11`
- [severity: medium] `work/ci-budget/intent.md`'s approved outcome sets "require branches to be up to date: **off**" as the owner's decision, while `docs/sdlc/github-setup.md:72` still tells adopters to set it **on**; the item is approved and unimplemented, so the two are simultaneously current — evidence: `work/ci-budget/intent.md` (Q3 answer), `docs/sdlc/github-setup.md:72`
- [severity: low] `knowledge/lessons/control-plane-unlock-is-advisory.md` says rule 3 is advisory here; `CLAUDE.md:20` presents rule 3 as one of the rules "enforced by hooks and CI, not by good intentions" — the contradiction is disclosed by the lesson pointer three sections later in the same file, which is the honest but confusing arrangement — evidence: `knowledge/lessons/control-plane-unlock-is-advisory.md:1`, `CLAUDE.md:20`, `CLAUDE.md:94`

---

## 8. Bookkeeping burden — last 8 merged pull requests

`git log origin/main --merges` filtered to true `Merge pull request` commits; per-merge file lists from `git diff --name-only <merge>^1 <merge>^2`. **Generated** = `*/index.md`, `*/log.md`, `work/index.md`, `CLAUDE.md`/`GEMINI.md`/`AGENTS.md`, `revisions/index.md`.

| merge | PR | files | generated | work artifacts (intent/spec/plan/revisions) | code + config | other docs |
|---|---|---|---|---|---|---|
| ca8dd32 | #64 | 4 | 3 | 1 | 0 | 0 |
| bce2a43 | #63 | 6 | 3 | 3 | 0 | 0 |
| 4fa4f7a | #58 | 14 | 5 | 4 | 4 | 1 |
| 336470c | #56 | 4 | 3 | 1 | 0 | 0 |
| a83c8e4 | #57 | 16 | 6 | 4 | 3 | 3 |
| 44cac9d | #55 | 25 | 9 | 5 | 8 | 3 |
| 79e9a30 | #54 | 4 | 3 | 1 | 0 | 0 |
| d1efd89 | #53 | 15 | 6 | 5 | 3 | 1 |
| **total** | | **88** | **38 (43%)** | **24 (27%)** | **18 (20%)** | **8 (9%)** |

- [severity: high] 43% of every file touched by the last eight merges is machine-regenerated bookkeeping, and a further 27% is chain paperwork — 70% of the merge traffic is the process describing itself, against 20% code and config — evidence: `git diff --name-only ca8dd32^1 ca8dd32^2` (3 of 4 files generated), `git diff --name-only 336470c^1 336470c^2` (3 of 4 generated)
- [severity: medium] Four of the eight merges (#64, #63, #56, #54) touch **no** code or config at all — they are pure ledger-and-index commits, each of which still paid a full `sdlc-gate` + `pr-review` + `agent-evals` + `delegated-merge` cycle — evidence: `git show --stat ca8dd32`, `git show --stat 79e9a30`, `work/ci-budget/intent.md:57-66`
- [severity: medium] The index regeneration is itself a recurring failure source: `894e11c` set an artifact to `superseded` in the web editor without regenerating the two files that render it, turning `index-drift.sh` red on `main` and on every branch cut from it — evidence: `work/ci-budget/log.md:17`, `scripts/checks/index-drift.sh`

---

## 9. Size

| Category | Count | Lines |
|---|---|---|
| Markdown, all tracked | 204 files | 15,465 |
| — `work/` (chain artifacts, logs, indexes) | 20 items | 8,978 |
| — `docs/` (README, rules, templates, spikes, handoff) | 41 files | 4,201 |
| — `knowledge/` (decisions, lessons, runbooks, metrics) | 39 files | 2,267 |
| — root (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `README.md`, `REVIEW.md`) | 5 files | 375 |
| Scripts, non-test (`scripts/*.py`, `*.sh`, `scripts/checks/`) | 35 files | 6,973 |
| Tests (`scripts/test_*.py`) | 35 files | 11,295 |
| Hooks (`.claude/hooks/*.sh`) | 9 | 909 |
| Workflows (`.github/workflows/*.yml`) | 7 | 728 |
| Eval cases (`evals/cases/*.yaml`) | 50 | 804 |
| Skills (`.claude/skills/*/SKILL.md`) | 7 | 172 |
| Agents (`.claude/agents/` + `.gemini/agents/`) | 4 + 4 | 24 + 48 |
| YAML/JSON config, all tracked | — | 2,023 |
| **Unit tests** | **835** | across 35 modules |
| **Eval cases by kind** | hook 44, skill 6, e2e 0 | |
| `scripts/checks/*.sh` | 8 | |
| Decisions / lessons / spikes | 15 / 14 / 6 | |

- [severity: medium] Markdown outweighs all executable code (scripts + hooks + workflows = 8,610 lines) by 1.8:1, and `work/` alone (8,978 lines of chain paperwork for 20 items, ~450 lines per item) is larger than the entire non-test codebase — evidence: `git ls-files '*.md' | xargs wc -l` (15,465), `git ls-files 'scripts/*' | grep -v '/test_' | xargs wc -l` (6,973)
- [severity: low] The test-to-code ratio is 1.6:1 (11,295 test lines against 6,973 script lines, 835 tests) — healthy, and 44 of 50 eval cases are deterministic and run without a model — evidence: `scripts/run_tests.py` output (`Ran 835 tests`), `scripts/run_evals.sh` output (`EVALS: 44 pass, 0 fail, 6 skipped`)
- [severity: low] `CLAUDE.md` renders at 108 lines against a 120 cap; `GEMINI.md` at 117 and `AGENTS.md` at 97 — the cap is real and close, which is why the lessons list is a pointer file — evidence: `wc -l CLAUDE.md GEMINI.md AGENTS.md`, `.sdlc/config.env:38`, `knowledge/lessons/adopter-context-file-sits-at-the-cap.md:1`

---

## Coverage

### Commands run, with last output line

| Command | Last line |
|---|---|
| `timeout 900 bash scripts/verify.sh` | `VERIFY: FAIL` |
| `GH_TOKEN= GITHUB_TOKEN= timeout 900 bash scripts/verify.sh` | `VERIFY: PASS (ca8dd32)` |
| `python3 scripts/check_okf.py` | `OKF: 182 docs, 0 warnings` |
| `python3 scripts/gen_index.py --check` | `INDEX: up to date` |
| `python3 scripts/gen_context_files.py --check` | `CONTEXT: 3 files up to date` |
| `GH_TOKEN= GITHUB_TOKEN= python3 scripts/check_artifact_chain.py --base HEAD` | `CHAIN: PASS` |
| `python3 scripts/check_artifact_chain.py --base HEAD` (tokens set) | `FileNotFoundError: [Errno 2] No such file or directory: 'gh'` |
| `python3 scripts/run_tests.py` (via verify) | `OK` (`Ran 835 tests in 32.204s`) |
| `scripts/run_evals.sh` (via verify) | `EVALS: 44 pass, 0 fail, 6 skipped` |
| `scripts/checks/context-drift.sh` | `CONTEXT: 3 files up to date` |
| `scripts/checks/eval-cases.sh` | `EVAL-CASES: 50 cases, 0 problems` |
| `scripts/checks/front-matter.sh` | `FRONT-MATTER: 197 docs, 0 problems (PyYAML)` |
| `scripts/checks/index-drift.sh` | `INDEX: up to date` |
| `scripts/checks/okf.sh` | `OKF: 182 docs, 0 warnings` |
| `scripts/checks/plugin-manifest.sh` | `√ Validation passed` |
| `scripts/checks/workflow-permissions.sh` | `WORKFLOWS: 7 files, 0 violations` |
| `scripts/checks/workflow-yaml.sh` | `WORKFLOW-YAML: all files parse (PyYAML)` |
| `git log origin/main --merges -40 --format=%h\|%s` | `Merge pull request #51 …` |
| `git diff --name-only <merge>^1 <merge>^2` × 8 | 88 files total (table §8) |
| Markdown dead-path scan (204 files, backticked repo paths) | 3 misses, all benign (§3) |
| Plan `## Files that change` scan (20 items) | no output = no missing paths |
| Config-key reader scan (16 keys × repo grep) | `GENERATED_PATHS` alone has no reader |
| Script call-site scan (27 non-test scripts) | all referenced |
| Workflow-input usage scan (PyYAML + regex, 7 workflows) | 7 inputs, 0 unused |
| `printf … \| .claude/hooks/protect-paths.sh` on `.github/CODEOWNERS` | `rc=0` (allowed) |
| `printf … \| .claude/hooks/protect-paths.sh` on `.claude/skills/sdlc-run/SKILL.md` | `rc=0` (allowed) |
| `printf … \| .claude/hooks/protect-paths.sh` on `REVIEW.md` | `rc=0` (allowed) |
| `printf … \| .claude/hooks/require-plan.sh` on an inline-python read command | `rc=2` (blocked — false positive, §4) |
| `bash …/probe_delegation.sh` (`delegation_on` vs `delegation.load`) | `bash delegation_on: ON` / `python enabled = True` (agree) |
| `wc -l` across `*.md`, `scripts/`, hooks, workflows, evals, skills, agents | table §9 |

### Files read

**Root**: `CLAUDE.md`, `GEMINI.md` (line 49), `AGENTS.md` (line 49), `README.md`, `REVIEW.md`, `.gitattributes`.

**Control plane**: `.sdlc/config.env`, `.sdlc/active`, `.sdlc/approvers.yaml`, `.sdlc/delegation.yaml`, `.sdlc/environments.yaml`, `.sdlc/README.md`, `.sdlc/release-authorizations/` (listing).

**Hooks**: `.claude/hooks/_lib.sh` (incl. `bash_write_targets`, `delegation_on`, `agent_handle_ok`, `artifact_signable`), `block-secrets.sh`, `post-edit-format.sh`, `production-gate.sh` (1–60), `protect-approvals.sh` (header), `protect-paths.sh`, `protect-tests.sh`, `require-plan.sh`, `stop-verify-reminder.sh`; `.claude/settings.json`, `.gemini/settings.json`, `docs/sdlc/templates/claude-settings.json`.

**Skills and agents**: all 7 `.claude/skills/*/SKILL.md`; all 4 `.claude/agents/*.md`; all 4 `.gemini/agents/*.md`.

**Workflows**: `agent-evals.yml`, `approve.yml`, `bands.yml` (full), `delegated-merge.yml` (triggers + permissions), `deploy.yml`, `pr-review.yml`, `sdlc-gate.yml` (full); `.github/CODEOWNERS`, `.github/dependabot.yml`.

**Scripts**: `verify.sh` (full), `check_artifact_chain.py` (docstring, `verify_dispatch_run`, argparse, `--no-approvers` sites), `check_control_plane.sh` (full), `deploy.sh` (1–60), `bands_config.py` (`matrix`), `detect_bands.py` (argparse, exit codes), `gen_index.py` (docstring, `ARTIFACTS`, argparse), `gen_context_files.py` (argparse), `check_okf.py` (argparse), `check_eval_cases.py` (`KINDS`), `run_evals.sh` (usage block), `adopt.sh` (config-rewrite section, copy list), `delegation.py` (`Policy`, `_as_bool`), `delegated_merge.py` (`check_required_runs`, `check_cool_off`, policy read), `sdlc_metrics.py` (call-site scan), `test_sdlc_metrics.py`; listings of all 35 `test_*.py`, all 8 `scripts/checks/*.sh`, `scripts/fixtures/`.

**Docs**: `docs/sdlc/README.md` (full), `phase-2-roadmap.md` (full), `metrics.md` (full), `lessons.md` (full), `index.md` (full), `github-setup.md` (branch-protection and delegated sections), `spikes/index.md`, `spikes/prompt-surfaces.md` (head + §2.3/§3), `spikes/gemini-parity.md` (status + UNVERIFIED list), `spikes/red-team-pass.md` (status + adopt table), `handoff/index.md`, `handoff/HANDOFF.md` (full), `templates/delegation.yaml`, `templates/claude-settings.json`, `docs/sdlc/rules/60-lessons.md`, `docs/sdlc/rules/10-hard-rules.md` (heading), `docs/sdlc/rules/00-chain.md` (retirement clause), `docs/sdlc/rules/50-gemini-only.md` (line 20).

**Knowledge**: front matter of all 15 `knowledge/decisions/*.md`; bodies of `merge-click-is-the-gate.md`, `delegated-mode.md` (banners), `self-enforcement-off.md`, `self-hooks-on.md`, `human-only-approvals.md`, `one-rule-source.md`, `one-writer-until-ledger.md`, `run-queue.md`, `gemini-hooks.md`, `bash-write-guard.md`, `adopt-script.md` (line 124); `knowledge/lessons/index.md` + all 14 lesson filenames; `knowledge/metrics/post-deploy-5xx-rate.md` (full); `knowledge/decisions/index.md`.

**Evals and monitoring**: `evals/README.md` (full), all 50 `evals/cases/*.yaml` (names, `kind:` lines; bodies of `skill-plan-names-files-and-proof.yaml`); `monitoring/bands.yaml` (full).

**Work items**: `work/index.md` (full); `work/sdlc-kit-phase-1/intent.md` and `spec.md` (full), `plan.md` (deviation log lines 94–134), `log.md` (line 17), `control-plane.patch` (head); `work/ci-budget/intent.md`, `log.md`, `index.md` (full); front matter (`status`, `approved-by`, `mode`) of all 58 chain artifacts across all 20 items; `## Files that change` of all 20 plans; `work/retire-active-pointer/spec.md` (R-5, G-9), `work/run-queue/plan.md` + `log.md` (line 21), `work/docs-reconcile/spec.md` (R-7), `work/delegation-boundary/intent.md` + `spec.md`, `work/adopter-first-hour/spec.md` (R-7), `work/loop-protection/spec.md` (R-8), `work/batch-b-followups/*` (HANDOFF references).

**Plugin**: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`.

### Severity tally

| Severity | Count |
|---|---|
| high | 18 |
| medium | 29 |
| low | 23 |
| **total** | **69** |
