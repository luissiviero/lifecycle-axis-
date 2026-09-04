---
type: sdlc/spec
id: deploy-gate
title: The deploy path fails open; every route to production must fail closed on a named human
description: Requirements and design for validating release authorizations against the release-manager role, gating the gh and deploy.sh routes, and unbinding RELEASE_APPROVAL from github.sha.
stage: design
status: in-review
reads: intent.md
approved-by:
approved-on:
skills-applied: [security-standards]
skills-version: 60ab0f5
prompt: "Transcribed from the approved implementation plan (session above), section WI-5 and appendix A5, by a drafting subagent; reviewed by the orchestrator."
record:
resource: https://claude.ai/code/session_01DSYmeD7eng2GKQ3EbHQDzo
tags: [deploy, production-gate, release-authorization, hooks, ci, consensus-item-4]
timestamp: 2026-09-04T21:50:29Z
---
# Spec: the deploy path fails open; every route to production must fail closed on a named human

## Requirements (each maps to an intent outcome)
Intent outcomes: (1) authorization file validated against `release-manager`; (2) the `gh`, `deploy.sh`
and `deploy`+`prod` routes ask or block; (3) `deploy.yml` reads a human-stored secret; (4) `deploy.sh`
validates the committed file; (5) decisions logged and docs truthful; (6) tests and evals grow, verify green.

| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | `production-gate.sh` allows a deploy-shaped command on `.sdlc/release-authorizations/<HEAD>` only when `approved-by` holds `release-manager` and is not in `never-approve`; otherwise the file is ignored | 1, 5 | `scripts/test_hooks_baseline.py::ProductionGateHook::test_allows_release_authorization_by_release_manager` (rc 0, empty stdout, `allow` line in `.sdlc/hook-decisions.log`), `::test_asks_when_release_authorization_names_claude`, `::test_blocks_unattended_when_release_authorization_names_someone` (rc 2, `reject` logged); eval `evals/cases/gate-ignores-unauthorized-release-file.yaml` |
| R-2 | The seven deploy-shaped strings from A5 ask; the five look-alikes allow; `gh pr merge --admin 12` asks | 2 | `::test_asks_on_deploy_shaped_commands` (seven subtests), `::test_allows_deploy_lookalikes` (five subtests), `::test_asks_on_gh_pr_merge_admin`; eval `gate-blocks-unattended-deploy.yaml` (adds `gh release create v1.0` under `SDLC_UNATTENDED=1`, exit 2) |
| R-3 | `deploy.yml` never derives `RELEASE_APPROVAL` from `github.sha` or `inputs.sha` | 3 | `scripts/test_deploy_guard.py::DeployGuard::test_workflow_does_not_bind_release_approval_to_github_sha` (greps the workflow for a `RELEASE_APPROVAL:` line containing `github.sha` or `inputs.sha`; none) |
| R-4 | `deploy.sh` with `RELEASE_APPROVAL` empty accepts a committed authorization only by a `release-manager`; refuses naming the handle otherwise; a file without `approved-by` refuses; env wins over file | 4 | `::test_committed_authorization_by_release_manager_succeeds`, `::test_committed_authorization_by_non_release_manager_refuses` (stderr names the handle), `::test_authorization_file_without_approved_by_refuses`, `::test_env_release_approval_wins_over_file`; renamed `::test_release_approval_env_and_github_actions_succeeds`; eval `deploy-refuses-without-approval.yaml` gains the file route (temp repo, `approved-by: claude`, exit 1) |
| R-5 | Decision records, runbook, `environments.yaml` and README rows describe the code as it now is | 5 | `grep -c 'cannot be satisfied by exporting' knowledge/decisions/deploy-from-ci.md` prints `0`; `grep -c 'rehearsed in staging on a schedule' .sdlc/environments.yaml` prints `0`; `python3 scripts/check_okf.py` ends `OKF: N docs, 0 warnings` |
| R-6 | Whole suite green | 6 | `scripts/verify.sh` ends `VERIFY: PASS (<sha>)`; `scripts/run_evals.sh` ends `EVALS: N pass, 0 fail, N skipped`; `python3 scripts/check_artifact_chain.py --base origin/main --slug deploy-gate` ends `CHAIN: PASS` |

## Design
### Architecture / data flow
Three independent checkpoints on one path, each fails closed on its own: the hook (agent session), the
workflow (CI input), and `deploy.sh` (the guard inside the job). A human's authorization enters by one
of two routes only: an Environment secret `RELEASE_APPROVAL` equal to the 40-hex SHA, or a committed
`.sdlc/release-authorizations/<sha>` whose `approved-by` is a `release-manager` in `.sdlc/approvers.yaml`.
The hook validates the file with the awk helpers from `_lib.sh` (`fm_value`, `approver_has_role`,
`log_decision`, all from `control-plane-visibility`); `deploy.sh` validates it with
`python3 scripts/approvers.py --has-role` (from `front-matter`). Nothing in the workflow computes
the approval any more.

### Interfaces (APIs, events, schemas) — exact shapes
`production-gate.sh:92-95` becomes (A5):
```bash
  AUTH="$ROOT/.sdlc/release-authorizations/$SHA"
  if [ -f "$AUTH" ]; then
    BY="$(fm_value "$AUTH" approved-by any)"
    if approver_has_role "$BY" release-manager; then log_decision allow "release authorization $SHA by $BY"; exit 0; fi
    log_decision reject "release authorization $SHA names '$BY', not a release-manager"
  fi
```
The `RELEASE_APPROVAL` branch (`:96-98`), the unattended block (`:99`) and the ask (`:100`) are unchanged.
`DEPLOY_RE` (`:26`) gains two clauses and three regex pairs join it; `is_deploy()` replaces the grep at `:90`:
```bash
DEPLOY_RE="$BOUND"'(kubectl…|cap[[:space:]]+production|([^[:space:]]*/)?deploy\.sh|gh[[:space:]]+(release[[:space:]]+create|workflow[[:space:]]+run|pr[[:space:]]+merge))'
DEPLOY_WORD_RE="$BOUND"'([^[:space:]]*/)?deploy([[:space:]]|$)'
PROD_RE='(^|[^[:alnum:]_])(prod|production)([^[:alnum:]_-]|$)'
GH_API_RE="$BOUND"'gh[[:space:]]+api[[:space:]]+[^;&|]*(releases|merges|dispatches)'
GH_MUT_RE='(-X|--method)[[:space:]=]*(POST|PUT|PATCH|DELETE)|(^|[[:space:]])(-f|-F|--field|--raw-field|--input)([[:space:]]|=)'
is_deploy() {
  printf '%s' "$1" | grep -Eiq "$DEPLOY_RE" && return 0
  printf '%s' "$1" | grep -Eiq "$DEPLOY_WORD_RE" && printf '%s' "$1" | grep -Eiq "$PROD_RE" && return 0
  printf '%s' "$1" | grep -Eiq "$GH_API_RE" && printf '%s' "$1" | grep -Eiq "$GH_MUT_RE" && return 0
  return 1
}
```
(`kubectl…` stands for the existing clause list at `:26`, kept verbatim.) Ask: `make deploy ENV=production`,
`./scripts/deploy.sh production`, `gh workflow run deploy.yml -f environment=production`, `./deploy production`,
`gh release create v1.0`, `gh pr merge 5 --squash`, `gh api -X POST repos/o/r/merges -f base=main`. Allow:
`deploy --help`, `echo deployment notes`, `gh pr view 12`, `gh api repos/o/r/releases/latest`, `git log --grep=deploy`.

`scripts/deploy.sh`, inserted between `:75` (SHA) and `:79` (the empty-`RELEASE_APPROVAL` refusal) (A5):
```bash
AUTH="$ROOT/.sdlc/release-authorizations/$SHA"
if [ -z "${RELEASE_APPROVAL:-}" ] && [ -f "$AUTH" ]; then
  BY="$(sed -n 's/^approved-by:[[:space:]]*//p' "$AUTH" | head -1 | sed 's/[[:space:]]*#.*$//')"
  if python3 "$ROOT/scripts/approvers.py" --has-role release-manager "$BY" >/dev/null 2>&1; then
    RELEASE_APPROVAL="$SHA"
  else
    echo "deploy refused: $AUTH names '$BY', who is not a release-manager in .sdlc/approvers.yaml." >&2; exit 1
  fi
fi
```
`.github/workflows/deploy.yml:55`: `RELEASE_APPROVAL: ${{ secrets.RELEASE_APPROVAL }}` with a comment that it is
empty unless a human stored the SHA as an Environment secret; `CI: "true"` (`:56`) stays. The authorization file
schema stays one YAML-ish line, `approved-by: <handle>`; `fm_value ... any` reads it with or without `---` fences.

### Data and migrations
None. No new fields; the authorization file and the secret carry a handle and a SHA (internal, not personal
data). `.sdlc/release-authorizations/` holds only `.gitkeep` today, so no existing file changes meaning.

### Failure modes and how they surface
- Secret unset or stale in CI: `deploy.sh:80` or `:84` refuses naming both SHAs; the job fails before `DEPLOY:`.
- Authorization file names a non-release-manager: hook logs `reject` and asks (blocks unattended);
  `deploy.sh` refuses naming the handle and the file path.
- `approvers.yaml` missing in the checkout: `approver_has_role` returns 1 (fails closed); `approvers.py`
  loads fail-closed (`approvers.py:146-147`) so `--has-role` exits 1.
- `python3` missing in CI: the `--has-role` call fails, the file route refuses; the secret route still works.
- False positive on the word pair (`ls deploy production`): one prompt; never a block in an attended session.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: `gh pr merge` now prompts, while `merge-click-is-the-gate.md:32-33` has the agent merging on the owner's chat instruction — policy: rule 4 and that decision record — contradiction? no — owner: luissiviero — resolution: the prompt is the click; record updated at `:32-33,43-45`.
- C2: until `control-plane-visibility` lands its never-unlock `case`, an agent under the unlock can still write `.sdlc/release-authorizations/<sha>` in this repo, and the file route would trust a file the writer forged with a listed handle — policy: security-standards §8 (writer is not approver) — contradiction? yes, transiently — owner: luissiviero — resolution: WI-2 merges before this item (plan order); CI `check_control_plane.sh` blocks an agent PR touching `.sdlc` until the owner labels it; the chain check's commit-author test does not cover this file, so the label is the control.
- C3: `GITHUB_ACTIONS` and `CI` stay as checks that any shell can set — policy: docs say what the code does (consensus) — contradiction? no — owner: luissiviero — resolution: keep them as hints; `deploy-from-ci.md:40-43` reworded.
- C4: two implementations of one rule (awk `approver_has_role` in the hook, `approvers.py --has-role` in `deploy.sh`) can drift — policy: security-standards §3 (validate at the boundary) — contradiction? no — owner: luissiviero — resolution: both are tested against the real `.sdlc/approvers.yaml` copied into the fixture; `test_approvers.py` (WI-1) and `test_lib_helpers.py` (WI-2) pin the same three cases.
- C5: an Environment secret holding a SHA is a credential-shaped value in GitHub, not in the diff — policy: security-standards §1 — contradiction? no — owner: luissiviero — resolution: referenced by name only; the runbook says where it is stored and that it is replaced per release.

## Open questions carried from intent.md
- `gh pr merge` prompt accepted as the merge click? (proposed yes)
- Keep the secret route beside the file route? (proposed yes)
- Runbook passes the 40-hex SHA, not a tag? (proposed yes)

## Decisions (ADR-style: context → decision → consequences)
- D1: Env before file in `deploy.sh`: a set `RELEASE_APPROVAL` is compared first, the file is read only when it is empty → a stale secret is reported as a SHA mismatch rather than silently overridden by a file → the tests pin "env wins".
- D2: The hook validates with awk, `deploy.sh` with Python: hooks may not call `python3` (on the owner's Windows PC it may be the Store stub; a hook must answer in milliseconds), `deploy.sh` runs only in Linux CI and reuses the canonical parser → two implementations, one fixture (C4).
- D3: `is_deploy()` composes three pairs instead of one regex: the word pair and the `gh api` pair need two independent matches over the same command, which one ERE cannot express without ordering assumptions → a few more `grep` processes per Bash call, only when the command is deploy-shaped.
- D4: `gh pr merge` counts as deploy-shaped: on this repo merging to `main` is the release act and `deploy.yml` fires from `main` via `gh release create` → one prompt per merge, accepted (C1).

## Gotchas found while reading the codebase
- No revision of `production-gate.sh` ever had the playbook's generic `deploy`+`production` clause (first version at `0d00f91` names tools only); "dropped" means never adopted, not removed later.
- `hooktest.run_hook` strips `RELEASE_APPROVAL` and every `SDLC_*` variable (`hooktest.py:103-107`), and `run_evals.sh:51` unsets the unlock: tests must set what they assert on.
- `hooktest.fake_repo` (`hooktest.py:59-92`) copies only `config.env`; the `approvers.yaml` copy arrives with `front-matter` step 6 and the R-1 tests need it (or must pass the file explicitly).
- `test_deploy_guard._make_repo` (`:14-36`) copies only `environments.yaml` and `deploy.sh`; the new `python3` call needs `scripts/approvers.py`, `scripts/check_artifact_chain.py` (imported at `approvers.py:28`, runs `git rev-parse` at import) and `.sdlc/config.env` (`approvers.load` reads `APPROVERS_FILE`) in the temp repo.
- `deploy.yml` has inputs `environment` and `sha` only (`:13-22`); `rollback-deploy.md:25` says "`sha`/`ref`", and `:26` says to pass a release tag, which `deploy.sh:83` would refuse (it compares 40-hex SHAs).
- `eval deploy-refuses-without-approval.yaml` runs in the real repo with `CI=` empty; the file-route case must build a temp repo (pattern: `chain-rejects-unknown-approver.yaml`) because writing under `.sdlc/release-authorizations/` in the kit is a control-plane write.
- `docs/sdlc/README.md:102` describes the file route with no approver condition; `:112` says `deploy.sh` "refuses without `RELEASE_APPROVAL` matching HEAD", true, but the workflow supplied both sides.
- `.sdlc/environments.yaml:18` says the rollback is "rehearsed in staging on a schedule"; no workflow does that.
- `.sdlc/README.md:5` says the authorization file is "created by a human"; nothing enforced it.

## Not doing
- Deploy or rollback as MCP tools, a real deploy command, a GitHub plan or visibility change.
- The never-unlock `case` in `protect-paths.sh` (in `control-plane-visibility`, A5 quotes it there); the approval hook (`approval-gate`).
- Making the hook `allow` anything: an authorized deploy exits 0 silently, as today, and the tool's own permission prompt still applies.
- Gating `git push` differently: `push_reaches_protected()` is unchanged.
