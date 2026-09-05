---
type: doc
title: lifecycle-axis vs. the AI-native SDLC playbook
description: The adversarial comparison report with file:line evidence, 2026-09-04.
tags: [sdlc, handoff, playbook-comparison]
timestamp: 2026-09-04T22:13:39Z
---

# lifecycle-axis vs. "The AI-Native SDLC playbook": what changed, what broke, what is missing

Repo at `64bcb17` (main). Playbook: Louis Claxton, Anthropic, 21 Aug 2026 (53 pages as exported).
Method: I read the full playbook and the repo's design docs myself, then ran eight read-only analysts in
parallel (one per playbook stage, one for everything added beyond the playbook, one that ran the repo's
own definition of done, one that installed the kit into a throwaway repo and walked a first work item).
Every claim below was produced by reading code or by running a command; I re-ran the highest-severity
ones myself. No file in the repo was changed; `git status` is clean.

## Verdict in five sentences

The repo is faithful to the playbook's *shape*: every play has a mechanism, the artifact chain is real,
and several mechanisms are stricter and safer than the article's own examples. On its own definition of
done it is green: `VERIFY: PASS`, 300 tests, 26 evals, 14 s on Linux. But the definition of done does
not measure the properties the playbook cares about, and on those the kit is weaker than it says: the
control plane is unlocked in the kit's own repo and nothing logs it; the deploy path fails open; approval
is honor-system; the feedback loop can be gutted by the agent that uses it; the band detector cannot see
the most obvious breach; and a fresh adopter hits five breaking problems in the first hour. About half
of the repo's mass (Gemini parity, OKF, generated indexes, plugin packaging, prompt-surfaces) serves
consumers that do not exist yet, while the one thing the playbook makes central, a per-change plan with
named files, is absent for the kit itself. The good news is that the fixes are mostly small and the
repo's own docs already know about several of them.

---

## (a) Good changes: better than the article, or a faithful extension of it

Ranked by how much real risk they remove.

1. **Human-only switches are captured before the repo config is sourced.** `_lib.sh:9-11,28-31`
   reads `RELEASE_APPROVAL` and the unlock from the process environment first, and the gate compares
   `RELEASE_APPROVAL` to the exact HEAD SHA (`production-gate.sh:96`). The playbook's example gate
   (p.36-37) passes on *any* non-empty `RELEASE_APPROVAL`, which the agent can `export` in the same
   shell. Tested (`test_control_plane_hardening.py:99-128`).

2. **The PR reviewer cannot run code, cannot write, and reads REVIEW.md from the base ref**
   (`pr-review.yml:29-33,64-69,95-97`). The article's step 1 (p.33) leaves both holes open: a PR can
   rewrite the policy the reviewer follows, and the reviewer runs PR-head code while holding the key.
   The repo also scopes the CI credential to the read-only triage step and the nightly default-branch
   job, unlike the article's own `agent-evals.yml` (p.31), which hands the key to a job executing
   `evals/*.json` from the PR head.

3. **One verify command, self-extending, with healthy last lines documented, and a Stop hook that
   actually blocks.** `verify.sh` runs `VERIFY_CMDS` plus every `scripts/checks/*.sh`; CLAUDE.md lists
   each command with its expected final line, exactly p.27-28; the Stop hook returns
   `{"decision":"block"}` when plan-required code changed after the last green run. Deterministic across
   runs, 0 skipped tests on Linux.

4. **Refspec-aware push detection and a Bash write guard the playbook does not have.**
   `push_reaches_protected()` catches `HEAD:main`, `+feature:main`, `refs/heads/main`, `--all`,
   `--delete`, and a bare `git push` whose upstream is main; the write guard canonicalises `..`,
   symlinks and `cd`/`pushd` targets before matching. The article registers a Bash hook only for
   deploys (p.36) and says nothing about heredocs into protected paths.

5. **A hook test harness** (`hooktest.py`, fixtures, 98 hook tests). The playbook says agent
   configuration "deserves the regression testing that code gets" (p.30) but provides no harness.

6. **`work/<slug>/` co-locates the whole chain, and in-progress chain mode lets an item be opened one
   stage per PR.** The playbook's bare `intent/` folder (p.10) never says how spec and plan find their
   intent. The in-progress mode (`check_artifact_chain.py:141-157`) is what makes "each stage ends by
   committing an artifact" (p.6) mergeable under CI; 22 tests.

7. **The spec template captures the provenance the playbook asks to log** (`skills-applied`,
   `skills-version`, `prompt`, p.14) and encodes "areas of concern" as a structured row with policy,
   contradiction flag, owner and resolution. The article states the requirement and gives no field.

8. **Deterministic band detection on GitHub-only metrics, with the inert metric marked inert.**
   `detect_bands.py` has no model dependency; the model is invoked only on breach with the tier's tool
   list; `post_deploy_5xx_rate` is honestly labelled "no source" rather than faked. Rollback is
   "propose, never run" behind three layers, stricter than the article's 3σ auto-rollback (p.45), which
   is the right call for a one-person shop.

9. **Least-privilege, SHA-pinned workflows with a checker in verify** (`check_workflow_permissions.py`,
   Dependabot for the SHAs). Beyond the article.

10. **Windows hardening found three real fail-open bugs** (drive-letter paths, missing `jq`, MSYS
    mount forms), each now a regression test and a CLAUDE.md lesson. The playbook never considers
    non-POSIX paths.

11. **Honest decision records.** `merge-click-is-the-gate.md`, `adopt-script.md`,
    `control-plane-label.md` state what the platform cannot do. The playbook silently assumes branch
    protection (p.33, p.40).

12. **REVIEW.md adds a Memory pass** so "mistake seen twice goes to CLAUDE.md" (p.34 step 5) is a
    first-class review output, not a sentence in prose.

---

## (b) Things that should not have changed, or whose implementation is faulty

Ranked by severity. Where a doc claims the opposite of what the code does, the doc reference is given
because that is the more dangerous half.

### B1. Rule 3 is unenforced and unlogged in the kit's own repo (high)

- `.claude/settings.json:2-4` commits `SDLC_CONTROL_PLANE_UNLOCK=1`, exported to every session. With
  it, `protect-paths.sh:24-25` prints one line to stderr and exits 0.
- Claude Code does not show stderr from a hook that exits 0; it goes to the debug log only. So the
  "audit line in the transcript" claimed in `self-hooks-on.md:59-60`, `bash-write-guard.md:77-78` and
  CLAUDE.md line 67 does not exist anywhere a human or the model sees.
- The CI backstop never fires: `check_control_plane.sh:35,77` calls a PR agent-authored only when the
  author is a Bot or the branch starts with `claude/`. The kit's PRs used `kit/*` and `spike/*`
  branches under the owner's identity. Of 13 merged PRs that touched `PROTECTED_PATHS`, 2 carried the
  label. `docs/sdlc/README.md:108` still says CI blocks such PRs.
- Why this is a should-not-have-changed: the playbook's model is that "the controls have to come from
  configuration in the repo" (p.26). Shipping the off-switch inside that configuration, in the
  flagship repo, converts every red line the kit sells into an invisible stderr line. The alternative
  the decision rejected, setting the unlock in the shell that launches Claude Code, is exactly the
  playbook's pattern for `RELEASE_APPROVAL` (p.36). The earlier same-day decision
  (`self-enforcement-off.md`) was at least honest that hooks were off.

### B2. The deploy path fails open (high)

- `deploy.yml:55-56` sets `RELEASE_APPROVAL: ${{ inputs.sha || github.sha }}` and `CI: "true"`
  itself. Inside Actions the approval always equals HEAD; it is never a human act. The only real gate
  is the GitHub Environment reviewer, which `merge-click-is-the-gate.md:14-19` says returns 403 on this
  plan. That record's line 43 claims the deploy path "fails closed rather than open". It does not.
- `gh release create v1`, `gh workflow run deploy.yml -f environment=production` and the equivalent
  `gh api` call all pass `production-gate.sh` unattended, and each starts a production run of
  `deploy.yml`.
- `deploy-from-ci.md:36-43` says the `GITHUB_ACTIONS` check "cannot be satisfied by exporting the two
  env vars locally". Running `CI=1 GITHUB_ACTIONS=true RELEASE_APPROVAL=$(git rev-parse HEAD)
  scripts/deploy.sh production` from a shell prints `DEPLOY: would run …` with exit 0, and
  `test_deploy_guard.py:113-121` asserts that as success.
- The generic `deploy` and `production` substring match from the playbook (p.36) was dropped for a
  vendor-CLI regex (`production-gate.sh:24-26`). Result: `make deploy ENV=production`,
  `./scripts/deploy.sh production`, `./deploy production` and `printf 'deploy production' | sh` all
  allow. The vendor list was a good addition; removing the generic clause was not.
- `production-gate.sh:93` accepts any `approved-by:` line in `.sdlc/release-authorizations/<sha>`
  without checking `approvers.yaml`, and under the unlock (B1) the agent can write that file. In a
  clone with such a file, `kubectl apply` and `git push origin HEAD:main` allow unattended. No test
  covers the authorization-file route.
- Impact is latent only because `deploy.sh:97` is an `echo`.

### B3. Approval is honor-system, and the replacement is heavier than what it replaced (high)

- The playbook records acceptance as "the merge or the closing review" (p.11), in git history. The
  repo replaced that with front-matter `status`, `approved-by`, `approve.py`, `approvers.yaml`, a
  `log.md` ledger and a commit-author check: roughly 950 lines including tests.
- From inside an agent session: `env -u CLAUDECODE python3 scripts/approve.py <slug> intent.md --as
  luissiviero`, commit, and `check_artifact_chain.py` prints `CHAIN: PASS`. Or skip the script: one
  `sed` on the front matter plus one hand-written ledger line also passes. No hook covers `work/`
  (`config.env:7`); the commit-author check (`check_artifact_chain.py:84,261`) only catches bot emails,
  and a local agent commits with the human's git config. `approve.py:21-23` admits the refusal "is a
  courtesy, not a gate".
- The merge gate is also shared-identity: `merge-click-is-the-gate.md:31-33` has the agent merge with
  the owner's `gh` login, so `git log --merges` cannot separate agent merges from human ones. That
  contradicts p.41 ("acts under the agent's own identity") and the repo's own spike decision.
- With one handle in every role, `approvers.py` can only ever answer "luissiviero". The mechanism
  scales if a second human joins; today it enforces less than the article while costing more.

### B4. The feedback loop is not protected from the agent that uses it (high)

- In a clone, replacing `scripts/verify.sh` with `echo "VERIFY: PASS (gutted)"` and emptying
  `run_tests.py`, committed on an agent branch, passes every automated gate as CI runs them:
  `CHAIN: PASS` (the umbrella plan lists `scripts/**`), `CONTROL-PLANE: clean` (`scripts` is not
  protected), and the gate's Verify step runs the PR-head script. No hook blocks the edit under a
  `kind: feature` plan. REVIEW.md has no "reject any change that touches the check" rule, which is the
  playbook's stated fallback (p.28 step 7).
- `protect-tests.sh` blocks edits but not `rm`, `git rm`, `unlink`, `mv`, `perl -pi -e`, or
  `git revert`. An agent told "make the failing test pass" can delete it.
- `kind: fix` blocks *new* test files too (`protect-tests.sh:22` has no exists check). The playbook's
  own workflow, "reproduce the bug as a failing test first" (p.28), which CLAUDE.md line 18 repeats,
  is therefore impossible under the hook: before approval `require-plan.sh` blocks the write, after
  approval `protect-tests.sh` blocks it.
- The `kind:` parse (`protect-tests.sh:15-16`) fails *open* on the template's own inline comment
  (`kind: feature   # feature | fix`), on `kind: Fix`, on `kind: "fix"`, and on a CRLF plan. Its sibling
  `require-plan.sh` fails closed on the same parse, so a Windows checkout gets both behaviours at once.
- `touch .sdlc/.last-verify` is not a write the guard sees, so the Stop hook can be silenced; and after
  `git commit` the tree is clean, so the hook is silent on the normal path anyway.
- `chmod -x scripts/checks/okf.sh` passes every hook, and `verify.sh:15` then skips the check with no
  output; `test_verify.py:76` pins that silence as intended.

### B5. The Bash write guard has a long silent-allow list and a loud false-positive list (high for adopters)

- Verified passes against `.sdlc/config.env` (full 100-row table in the Build analyst's output):
  newline-separated commands, `true; cp …` with the semicolon glued, `( … )` and `{ …; }`, `bash -c`,
  `sh -c`, `eval`, `xargs`, `find -exec`, `nice`, `cp -t DIR`, `install -t`, `cp -r stage/.sdlc .`,
  `rsync -a stage/ .`, `tar xf`, `unzip`, `sort -o`, `sed --in-place`, `perl -pi`, `node -e`,
  `ruby -e`, `git apply <file>`, `patch < file`, `git restore <path>` without `--`, a quoted path with
  a space, `$PWD/` and `~/` prefixes, `>|`, and, worst, `2> .sdlc/config.env` and `&> …`, which
  truncate the config and thereby unset every guard. `rm -rf .sdlc`, `git rm`, `mv … /tmp` and
  `chmod -x .claude/hooks/*.sh` are not writes at all in the guard's model. `bash-write-guard.md:104-115`
  acknowledges about a third of these.
- Two-step `cd`: Claude Code's Bash tool keeps the working directory between calls and sends it as
  `cwd`; `_lib.sh` never reads that field and resolves relative candidates against `$ROOT`. `cd .sdlc`
  in one call and `echo … >> config.env` in the next passes.
- `NotebookEdit` was added to the matcher by the control-plane patch, but every hook reads
  `.tool_input.file_path`; NotebookEdit sends `notebook_path` and `new_source`. All four edit hooks exit
  0 for a notebook under `.sdlc/` or one containing an AWS key.
- False positives are not "nearly free" as `bash-write-guard.md:62` says: with
  `PLAN_REQUIRED_PATHS="scripts"` and a draft active item, every `python3 -c` or heredoc that merely
  *mentions* a path under `scripts/` is blocked; `git apply` is blocked because `app` is a substring of
  `apply`; a heredoc containing the dotenv filename is blocked as secret material. Three analysts hit
  this during read-only work, and the secrets hook blocked the first save of this very report because a
  bullet quoted a fake credential-shaped example.

### B6. The band detector cannot see the breach it exists for (high)

- `detect_bands.py:20`: `if s == 0: return 0`. A baseline with zero variance never breaches. Thirty
  days of green CI is exactly that baseline; the first 100%-failure day returns `tier: null`, exit 0.
  Verified by hand. No test uses a constant baseline.
- The baseline is `series[:window]`, the *first* N points, not a rolling window (`:27`). For
  `pr_cycle_time_hours`, `github_metrics.py:158` fetches every closed PR with no date filter and
  ignores `--days`, so the baseline is the repo's first 14 merges forever. `bands.yaml:21` and the
  metric docs say `rolling_30d`.
- `bands.yml:61` uses `--window 14`; the metric docs (`ci-test-failure-rate.md:29,49`) say 30 and
  "needs at least 30 points". With window 30 and 30 days of data the detector would test nothing.
- Three of the four Western Electric rules; the 8-in-a-row drift rule is absent, and the 3σ rule tests
  only the last point. The playbook's reason for WE rules is "slow drift as well as spikes" (p.43).
- The 3σ `propose` tier and the `routes:` in `bands.yaml` are read by nothing; the workflow hard-copies
  the 2σ tool list and only ever files an issue (`bands.yml:33-34`). README line 38 and the metric docs
  still describe 3σ as opening a PR or proposing the runbook.
- `gh issue create` runs unconditionally, so a multi-day drift files one duplicate issue per night; the
  diagnosis prompt asks Claude to "look at recent commits" while `git log` is not in the allowed tools.
- `ci_test_failure_rate` counts every workflow in the repo, including the nightly bands job itself, and
  treats `cancelled` and `timed_out` as non-failures.

### B7. The templates break the tooling that reads them (high for adopters)

- `templates/intent.md:7,9` and `templates/plan.md:7-8,10` carry inline comments on `status:`,
  `kind:` and `approved-by:`. `check_artifact_chain.py:42-53` does not strip them: a verbatim template
  copy, which `/sdlc-intent` step 1 instructs, fails with `status is 'draft   # draft | in-review …'`
  and `has approved-by '# product owner…'`. `approve.py` then writes the comment text into the ledger
  line, whose `|` characters make it malformed. `require-plan.sh` quotes the same garbage in its block
  message; `protect-tests.sh` fails open on it (B4). No test in the suite builds an artifact from a
  template.

### B8. The kit does not run its own process (high for credibility)

- One umbrella work item, `sdlc-kit-phase-1`, whose "Files that change" is nine `**` globs covering
  194 of 195 tracked files. With `EXEMPT` (`check_artifact_chain.py:38`) the diff-in-plan check can
  never fail. 21 of 23 PRs cite this slug. The playbook's plan names three files (p.16-17); the
  repo's own skill says "prefer explicit paths" (`sdlc-plan/SKILL.md:10`); roadmap item 18 admits the
  wildcards "stay open".
- The plan was approved once and then amended 33 times by the agent, including adding whole globs
  after approval. The deviations log is a changelog, not the "same commit" sync of p.16 step 7.
- `log.md` stopped at 2026-09-02 23:00 after nine entries; 22 PRs merged since with zero ledger lines,
  while `30-conventions.md:19` says every gate gets an entry.
- The ledger shows the chain was retrofitted: spec "from the approved plan-mode plan" (chain
  inverted), "implementation waves 0-6 complete" while plan was `in-review`, all three artifacts
  approved together at the end.
- Branch convention `work/<slug>` (`30-conventions.md:17`) followed by 1 PR of 23.
- `work/_example`, the one worked example newcomers copy, uses different headings and field names
  from the templates (`## Success criteria` vs `## Proposed outcome`, `originator:` vs `author:`,
  `source:` vs `resource:`); the skill-spelling fix in PR #23 corrected the skills and agents but not
  the example.

### B9. A fresh adopter breaks in the first hour (high for the kit's stated purpose)

Verified by installing into a throwaway repo with `adopt.sh --with-hooks`. Ranked by abandon-likelihood:

1. `adopt.sh:294` and the generated CLAUDE.md tell the adopter to run `scripts/approve.py`; the copy
   list (`adopt.sh:196`) omits it. The first human act fails with "no such file".
2. The install commit itself fails the chain check with 70 "not listed in plan" errors, so the
   adopter's first PR is red and nothing explains why.
3. `.sdlc/approvers.yaml` and `CODEOWNERS` land with `luissiviero` in every role. Fixing that means
   editing `.sdlc/`, which the hooks block from an agent, and then `_example` becomes an invalid chain.
4. A pre-existing `.claude/settings.json` (anyone who has used Claude Code in the repo) is skipped
   with one line among 95, and every hook is silently inert. `test_adopt.py` covers only the empty
   target.
5. `VERIFY: PASS` on a repo whose only verify command is `echo 'TODO(adopter)…'`.
   `adopt-script.md:56-60` claims "a loud placeholder cannot" produce a false green. It does.
6. The plan gate is open on day one: `.sdlc/active` is `_example`, whose plan is already `approved`,
   and `require-plan.sh` checks status only.
7. The rendered CLAUDE.md opens "This repo is a starter kit for the AI-native SDLC" inside the
   adopter's product repo, spends 57 generated lines before any project content, and the adopter is
   told to "cut it to one page" while the drift check forbids editing inside the markers.
8. `knowledge/*/index.md` link to 14 files that were not copied; `OKF: 27 docs, 14 warnings` on every
   verify from day one.
9. No GitHub-side checklist ships (required checks, the `control-plane-approved` label, secrets, App
   install); it exists only in a spike file that is not copied. `sdlc-gate` triggers on
   `pull_request` only, so a direct push to main sees no gate.
10. `--force`, the documented upgrade path, resets `VERIFY_CMDS` and `PLAN_REQUIRED_PATHS` to
    placeholders and overwrites customised hooks; without `--force` there is no drift signal at all.
11. Eval cases pass vacuously when the thing under test is missing: `deploy-refuses-without-approval`
    asserts `! scripts/deploy.sh`, and `deploy.sh` is not copied, so exit 127 negates to pass. A
    hookless adoption gets `agent-evals` red forever.
12. Smaller: no `.gitignore` shipped (untracked `.last-verify` and `__pycache__` after the first run);
    `--help` is an unknown flag; `make deploy` is not gated and there is no config knob to add it.

### B10. Weight added for consumers that do not exist (medium, but it is half the repo)

- **Gemini layer.** `gemini-hooks.md:91-97`: Gemini CLI refuses the owner's personal account, and
  Antigravity, the surface actually in use, reads `GEMINI.md` but not `.gemini/settings.json`. So the
  wiring, four mirrored agents, `50-gemini-only.md`, `test_gemini_wiring.py`, two evals and the
  `.gemini` protected path guard a tool the owner cannot run. The wiring itself is technically sound
  against Gemini CLI's documented payload; it is just unused.
- **OKF.** Real standard (Google, June 2026), absent from the playbook. What it costs here: front
  matter on 61 docs, of which 40 share one of two fabricated timestamps; 14 `index.md` files; an
  index-per-directory rule; a checker, 15 tests and two evals. `okf-pairing.md:63-65` still lists
  "whether any OKF consumer exists" as open, so the only consumer is `check_okf.py`.
  `knowledge/lessons/` and `knowledge/services/` are empty shells; `docs/sdlc/lessons.md` points at
  the empty one. `knowledge/decisions/index.md` is hand-maintained and already stale
  (`adopt-script.md` missing).
- **Generated `work/index.md` and per-item indexes** restate `ls work/` plus front matter, with a
  generator and a drift check to keep them honest.
- **Plugin packaging** is correct and validates, but has no second adopter; hooks cannot ship in it
  anyway, which the decision record reasons out well.
- **Prompt-surfaces spike, `status: accepted`**: canonical prompt blocks, an eight-rule lint, a skill,
  three templates, a fifth review pass, per-role model pins, nightly behaviour evals. Nothing in the
  playbook asks for it; p.21 explicitly says not to write a skill for what belongs in a prompt. It has
  already produced a contradiction with another spike that needed its own work item
  (`delegation-boundary`).
- Totals: 19 non-test scripts (3,783 LOC) and 25 test modules (4,622 LOC), 26 evals, 61 Markdown
  docs, 5 workflows, 3 context files. Onboarding reading for an adopter is 430 lines minimum, about
  700 realistic; the playbook's "Getting started" boxes for the five clay plays total about 40.
  The kit has no "install one play" mode; it front-loads Deploy, Maintain, OKF, Gemini and bands into
  day one, where the playbook says start with one clay play (p.8).

### B11. Evals are unit tests renamed (medium)

- 25 of 26 cases are `kind: hook` shell oracles against scripts, most duplicating a `test_*.py` case.
  The one `kind: skill` case checks that a file exists and lacks `status: approved`. Nothing exercises
  `/sdlc-spec`, `/sdlc-plan`, `/sdlc-review`, `/sdlc-incident`, the subagents, or whether
  `security-standards` triggers (p.22 step 4). `evals/README.md:1-5` claims "evaluation of the agent
  workflow, not just the code".
- The one prompt case has no red path: PR-time runs `--kind hook` only; the nightly is schedule-only
  and stays green when the credential is missing because `run_evals.sh:79` never fails on skips. If
  the OAuth token expires, the pass rate silently measures nothing.
- `run_evals.sh:75` discards the oracle's stdout and stderr; a failing case prints `✘ name` and
  nothing else.
- `agent-evals.yml:8` path filter omits `docs/sdlc/rules/**` (the source of CLAUDE.md), `GEMINI.md`,
  `AGENTS.md`, `.gemini/**`, `.claude-plugin/**`.
- The playbook's step 4, "gate configuration changes on the results" (p.30), is not met: the only
  model-driven case runs after merge.

### B12. Docs claim controls the code does not deliver (medium; listed because each will mislead an adopter)

| Claim | Where | Reality |
|---|---|---|
| "Agents cannot edit" `.sdlc/` | `.sdlc/README.md:1`, `docs/sdlc/README.md:59` | unlocked in this repo (B1) |
| CI blocks `claude/*` control-plane PRs | `docs/sdlc/README.md:108` | 11 of 13 such PRs unlabeled, branch names never matched |
| audit line "in the transcript" | `self-hooks-on.md:59`, CLAUDE.md:67 | stderr on exit 0, never shown |
| deploy path "fails closed" | `merge-click-is-the-gate.md:43` | B2 |
| deploy.sh "cannot be satisfied by exporting locally" | `deploy-from-ci.md:36-43` | it can |
| `@claude` fix loop | `docs/sdlc/README.md:35` | re-review only; reviewer has no write |
| 3σ opens a PR or proposes the runbook | README:38,106; metrics docs | diagnose only |
| rollback "rehearsed in staging on a schedule" | `environments.yaml:18` | no cron, no staging target |
| window 30, `rolling_30d` | metric docs, `bands.yaml` | window 14, fixed first-N baseline |
| "a loud placeholder cannot" give a false PASS | `adopt-script.md:56-60` | it does |
| index.md "stubs" | `adopt-script.md:82` | they link to 14 missing files |
| `log.md` entry at every gate | `30-conventions.md:19` | none since day one |
| `sdlc_metrics.py` "prints the git-derived ones" | `metrics.md:11` | 3 of ~26 indicators, one off-by-one |
| `'## Files'` heading | `check_artifact_chain.py:23,281` | template says `## Files that change` |
| CODEOWNERS "mirrors config.env" | `CODEOWNERS` header | `.gemini` missing |

### B13. Smaller faults worth a line each

- `VERIFY_CMDS` runs the chain check with `--base HEAD`, an empty diff, so the local single signal never
  runs the diff-in-plan check CI runs; CLAUDE.md compensates by asking for four commands.
- Local and CI chain checks disagree whenever `.sdlc/active` is not the item being shipped, which is the
  repo's state right now (`delegation-boundary` active, PR #23 shipped under `sdlc-kit-phase-1`).
  Following CLAUDE.md verbatim gives a red local check for a green PR, and the hooks evaluate the wrong
  plan: `require-plan.sh` currently blocks every write under `scripts/`.
- `production-gate.sh` silent allows: `git pu''sh`, aliases, `python3 -c … subprocess`, `$(echo origin)`,
  `git checkout main && git push` (branch read before the switch), `HEAD:release/1.0` (`release` is an
  exact match). `gh pr merge --admin`, `gh api`, and `curl` to the merge endpoint are all allowed,
  which is the actual direct path to main on a repo with no branch protection.
- `DANGER_RE` blocks every `rm -rf /absolute/path` and `--force-with-lease`; users will turn the hook
  off.
- `block-secrets.sh` false-positives on a quoted env-var reference in a password field and on writes
  outside the repo; misses AWS secret access keys, JWTs, Stripe live keys, Slack webhooks, dotenv lines.
- Windows `canon()`: no case-fold (NTFS is case-insensitive, so `.SDLC/` is the control plane there),
  `\\?\`, UNC, 8.3 names, trailing dot or space all resolve outside ROOT and allow.
- `approve.py` default handle is `git config user.name` first token, `luis`, which is not an approver;
  every approval needs `--as`. It also enforces no stage order.
- `sdlc_metrics.py:9-12` `commits_after()` is off by one; the test asserts only `>= 0`.
- Rollback runbook step 1 says pass the previous release *tag*; `deploy.sh:75,83` compares to a 40-hex
  SHA and refuses. Rollback also re-runs the chain check on the old commit, which fails if its work
  item was superseded.
- Malformed hook JSON makes every hook allow (`jq` parse failure leaves fields empty), unlike the
  fail-closed missing-`jq` path.
- Subscription OAuth token as the CI credential (commit `cde4360`): a personal, long-lived token in a
  repo secret, no spend cap, and no decision record. Confirm against current terms; not asserted as a
  violation.
- Nothing runs `shellcheck` or `pyflakes` (4 warnings, 3 unused imports today, all benign).

---

## (c) Things the playbook asks for that the repo should have done and did not

Ranked by value per hour of work.

1. **`permissions.deny` and `permissions.allow` in `.claude/settings.json`.** The playbook's worked
   example (p.37-38) denies reading dotenv and secrets files, `WebFetch`, `curl`, `wget`, and
   pre-approves the safe inner loop. None of that is enterprise-only; the repo has the exact lines in
   `managed-settings.example.json` and applies them nowhere. Today nothing stops reading a dotenv file
   or `curl` egress, and `verify.sh` is not pre-approved so a default-mode session prompts for it.

2. **Protect the loop.** Put `.claude/settings.json`, `scripts/verify.sh`, `scripts/run_tests.py`,
   `scripts/run_evals.sh` and `scripts/checks/` in `PROTECTED_PATHS` (or run verify from the base
   branch in CI), treat `rm`, `git rm`, `mv`-source and `chmod` as writes, block only *existing* test
   files under `kind: fix`, and add a REVIEW.md rule that any diff touching a check or a test in a fix
   PR is Important. This is p.28 step 7, the one thing the Test play says must hold.

3. **Per-change plans with named files, and retire the umbrella.** The repo already knows this
   (roadmap 18, `sdlc-plan/SKILL.md:10`). Until then rule 2 is unfalsifiable and B4 is free.

4. **Log hook decisions.** One append-only line per allow/ask/block with timestamp, tool, path, and
   decision, to a git-ignored file or `.sdlc/`. That gives the p.37 audit trail and the p.39 gate-wait
   metric without OpenTelemetry, and would have made B1 visible.

5. **Five to ten real agent evals** in the existing runner: `/sdlc-spec` on `work/_example` produces
   `## Areas of concern` and `skills-applied`; `/sdlc-plan` produces the two required headings and does
   not self-approve; a `kind: fix` task leaves test globs untouched; a write containing a planted key
   is refused; the incident skill names a new eval file. Run them on PRs touching `.claude/skills/**`
   and `docs/sdlc/rules/**`, and make the nightly red when the credential is missing.

6. **Fix the templates and add a template-derived test.** Move the inline comments to a line above the
   field, strip comments in every parser, and add one test per script that starts from a verbatim
   template copy.

7. **A formatter and linter hook.** `FORMAT_CMD` is empty and `post-edit-format.sh` is a no-op. For
   this repo `ruff` and `shellcheck` are one config line each; the playbook lists this as one of three
   build-hook jobs (p.23).

8. **Back `security-standards` with something deterministic** (p.22). Only §1 has a hook and it is
   porous; §5 (new dependency needs a plan entry) is a `git diff --name-only` check away. Name a policy
   owner and end the skill with a runnable check, as the playbook's example does.

9. **Fix the detector**: treat σ=0 with any deviation as a 3σ breach, use a trailing window, filter PRs
   by date, add the 8-in-a-row rule, test more than the last point, dedupe issues, and make the
   workflow read `bands.yaml` instead of hand-copying it.

10. **Make the adopter path work**: copy `approve.py`, `.gitignore` and `deploy.sh`; make
    `check_artifact_chain` treat the install commit as exempt or ship a plan for it; merge instead of
    skip an existing `settings.json` and warn loudly; fail verify while `VERIFY_CMDS` is the placeholder;
    ship an `_example` that is `in-review`, not `approved`; put a placeholder handle in `approvers.yaml`
    and `CODEOWNERS`; render a project-shaped CLAUDE.md with a Commands and Architecture section the
    adopter owns outside the markers; copy the GitHub-side checklist; add `--help`.

11. **Reconcile every row in the B12 table** with the code, in whichever direction is true. The
    playbook's warning that "anything stale is taking up context for no benefit" (p.20) applies to
    CLAUDE.md, and the README enforcement matrix is what an adopter will trust.

12. **Put `incident.md` in the chain.** `CHAIN` is intent, spec, plan only; the incident template has
    no `approved-by` although a role is assigned; nothing checks that an incident names an eval
    (roadmap 13 says Phase 4). Also `TEST_FILE_GLOBS` includes `evals/cases/*`, so under a `kind: fix`
    item the mandatory incident eval is blocked.

13. **Compute the indicators the repo says it computes.** Three of about 26 exist. Time to first
    review, comments resolved without a human touching the branch, first-pass CI success and gate wait
    are each one `gh api` call on data the metrics script already pulls.

14. **Decide whether to keep the Gemini and OKF layers.** If the Gemini surface is Antigravity, either
    write the `.agents/hooks.json` adapter the roadmap describes or delete the `.gemini/` wiring and
    say GEMINI.md is advisory. If no OKF consumer is planned, drop the checker and the fabricated
    timestamps and keep `knowledge/decisions/` as plain ADRs. Either answer is fine; carrying both
    unresolved is the cost.

15. **Non-engineer intent path** (p.10): an intent-only PR from a connector fails CI unless the body
    carries `Work-Item:`, a `log.md` exists, and the template comments are stripped. Derive the slug
    from the diff path and create the ledger on first sight.

16. **Windows path folding**: case-fold, strip `\\?\`, UNC and trailing dot or space in `winpath()`;
    CRLF-tolerant front-matter parsing; a CRLF `.gitattributes` rule for Markdown.

17. **Sync the drift the repo elsewhere guards against**: CODEOWNERS vs `PROTECTED_PATHS`, the
    hand-maintained `knowledge/decisions/index.md`, lessons restated in CLAUDE.md instead of linked
    from `knowledge/lessons/`, and rendered into GEMINI.md too.

---

## Suggested order if you fix things

1. Remove the committed unlock; set it in the launching shell (playbook pattern). Half a day.
2. `permissions.deny`/`allow`; `.claude/settings.json`, `verify.sh`, `checks/`, `run_tests.py` into
   `PROTECTED_PATHS`; treat `rm`/`mv`/`chmod` as writes; existing-only test lock. One day.
3. Restore the generic `deploy` and `production` match; validate `approved-by` in the gate against
   `approvers.yaml`; make `RELEASE_APPROVAL` in `deploy.yml` come from a human-readable source, not
   `github.sha`; gate `gh release`, `gh workflow run`, `gh pr merge`. One day.
4. Templates: comments off the field lines; strip comments in all parsers; one template-derived test
   per tool. Half a day.
5. Detector: σ=0, trailing window, date filter, 4th rule, dedupe. Half a day.
6. Adopter path: the ten items in (c)10. One to two days.
7. Retire the umbrella plan; every PR from here on has a real plan with named files. Ongoing.
8. Reconcile the B12 table. Half a day.
9. Real agent evals. One day.
10. Decide Gemini and OKF. A conversation, then either a day of deletion or a day of adapter.

## What I could not verify from here

- Whether GitHub Environment reviewers and branch protection are still unavailable on this repo today
  (the 403s are dated 2026-09-02).
- Whether the nightly eval, `pr-review` and `bands` workflows have run non-vacuously on the live repo,
  and which secret is set.
- Windows behaviour of `cygpath` and MSYS `realpath` on the path forms listed in B13 (logic verified on
  Linux with a Windows-shaped ROOT).
- Whether Antigravity is still the only Gemini surface in use.
- Whether Claude Code's `PreToolUse` hooks apply to subagent tool calls exactly as to the lead; the
  repo assumes yes and has no test.

Full analyst outputs, the 100-row Bash write-guard table and the 71-row production-gate table are in
the scratchpad alongside this file.
