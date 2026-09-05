---
type: sdlc/intent
id: loop-protection
title: The agent must not be able to weaken the check on its own work
description: The verify loop, the test lock and the session settings are unprotected; a branch that guts verify.sh passes every gate, a fix item cannot write its failing test first, and a skipped check or a failing eval says nothing.
stage: plan
status: approved
author: Luis Siviero (repo owner), drafted with Claude from the 2026-09-04 playbook comparison
approved-by: luissiviero
approved-on: 2026-09-04
supersedes:
record:
resource: https://claude.ai/code/session_01DSYmeD7eng2GKQ3EbHQDzo
tags: [hooks, verify, protect-tests, settings, consensus-item-3, consensus-item-12]
timestamp: 2026-09-04T21:49:03Z
---
# Intent: the agent must not be able to weaken the check on its own work

## Problem
The Test play's one rule with teeth, "the agent cannot weaken the check on its own fix", does not hold
here. In a clone, an agent branch that replaced `scripts/verify.sh` with a script printing
`VERIFY: PASS` and emptied `scripts/run_tests.py` passed the chain check, the control-plane check and
the gate's own verify step: the umbrella plan listed `scripts/**`, `PROTECTED_PATHS`
(`.sdlc/config.env:7`) names only `.claude/hooks .github/workflows .sdlc .gemini`, and
`.github/workflows/sdlc-gate.yml:36` runs the PR head's `scripts/verify.sh`. No hook stops the edit
under a `kind: feature` plan, and `REVIEW.md` has no rule that a diff touching the check is a finding.

The test lock has three defects. `protect-tests.sh:22` blocks every path matching `TEST_FILE_GLOBS`,
new files included, so under `kind: fix` the failing test that rule 1 demands ("reproduce the bug as a
failing test first", `docs/sdlc/rules/10-hard-rules.md:13`) cannot be written, and because the globs
(`.sdlc/config.env:17`) include `evals/cases/*`, the incident eval is blocked too. The hook does not
see `rm`, `git rm` or `mv` of a test (`_lib.sh:98-199` has no arm for them; bypass table rows 21-24
pass). And `protect-tests.sh:15-16` compares the raw `kind:` value with `fix`, so the template's own
`kind: feature   # feature | fix` comment, `kind: "fix"`, `kind: Fix` and a CRLF plan all fail open,
while `require-plan.sh:19` fails closed on the same parse.

Around the loop: `.claude/settings.json`, which wires every hook, is not in `PROTECTED_PATHS`, so an
agent can rewire or drop the hooks; neither it nor `docs/sdlc/templates/claude-settings.json` has
`permissions.deny` or `permissions.allow`, although the playbook's worked example does and
`docs/sdlc/managed-settings.example.json:4-5` already holds the lines; `scripts/verify.sh:15` skips a
non-executable check with no output, so `chmod -x scripts/checks/okf.sh` silently removes a gate
(`scripts/test_verify.py:76` pins that silence as intended); and `scripts/run_evals.sh:75` sends the
oracle's output to `/dev/null`, so a failing eval prints only `✘ name`. Consensus items 3 (protect the
loop) and 12 (add `permissions.deny`/`allow`).

Affected: every session here and in every adopter's repo (`adopt.sh:249-256` copies `PROTECTED_PATHS`
verbatim); the owner, who reads `VERIFY: PASS` as evidence. How we know: reproduced in a scratch
clone and with crafted hook JSON (comparison report B4, bypass table).

## Proposed outcome
1. `PROTECTED_PATHS` also lists `.claude/settings.json`, `scripts/verify.sh`, `scripts/run_tests.py`,
   `scripts/run_evals.sh` and `scripts/checks`; `.github/CODEOWNERS` mirrors them; rule 3 names them.
   An Edit or a Bash write to any of them exits 2 without the human unlock.
2. Under `kind: fix`, a new test file or eval case is writable, an existing one is blocked ("existing
   test file"); `kind: fix   # comment`, `kind: "Fix"` and a CRLF plan lock; `require-plan.sh` reads
   `status:` through the same parser.
3. Both settings files carry the `permissions.deny` and `permissions.allow` lists from the worked
   example and differ from each other only by `env`.
4. `scripts/verify.sh` prints `skipped (not executable): <check>` and fails unless
   `VERIFY_ALLOW_SKIPPED_CHECKS=1`; `scripts/run_evals.sh` prints the oracle's output under a `✘`.
5. `REVIEW.md`: a diff touching the loop files, or an existing test under `kind: fix`, is Important.
6. Every change has a test or an eval; `scripts/verify.sh` stays green; context files and the README
   enforcement matrix say what the code now does.

## Affected users and systems
- Users: the owner; every Claude Code session here; adopters (`adopt.sh --with-hooks`).
- Services / repos / data: this repo only: `.sdlc/config.env`, CODEOWNERS, the two plan hooks, both
  settings files, `verify.sh`, `run_evals.sh`, `REVIEW.md`, hook tests and evals, rule 3, the README.

## Constraints
- Must: keep every hook verdict unchanged for inputs that pass today, except the fail-open `kind:`
  cases (now lock) and new test files under `kind: fix` (now allowed); keep the `VERIFY:` and
  `EVALS:` contract lines byte-identical on the passing path; keep `.claude/settings.json` and the
  template identical apart from `env` (`scripts/test_adopt.py:307` compares the installed copy).
- Must not: add `rm`/`mv` arms to `_lib.sh` here (the Bash-guard item owns them); call `python3`
  inside a hook; change what `PLAN_REQUIRED_PATHS` covers.
- Out of scope: the approval-field hook, the deploy gate, adopter installation, `incident.md` in the chain.

## Risk class
low: config lists, two hook lines behind a shared parser, two runner messages and tests. A wrong
`PROTECTED_PATHS` entry blocks loudly rather than allowing silently. No data, no secrets, no deploy
path. The `permissions.deny` list is the one user-visible change: `WebFetch` and `curl` are refused.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: Should CI also run `scripts/verify.sh` from the base branch, so a PR cannot carry its own
  verifier even under the unlock? Proposed: not now; a workflow change belongs with the CI item.
  A:
- Q: `Bash(git *)` in `permissions.allow` as in the example, or only `git status|diff|log`?
  Proposed: the three read-only forms; `git push` stays behind `production-gate.sh`.
  A:
