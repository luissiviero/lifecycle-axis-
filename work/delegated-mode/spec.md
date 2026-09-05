---
type: sdlc/spec
id: delegated-mode
title: A second way to run a work item, where I approve the start and the AI signs the rest under its own name
description: "Requirements and design for delegated mode: the policy file, the grant on the intent, the delegated status and the agent signing script, the hook and chain-check rules that accept it, the revision gate, and the CI merge workflow."
stage: design
status: approved
reads: intent.md
approved-by: luissiviero
approved-on: 2026-09-05
skills-applied: [security-standards]
skills-version: c420e3c
prompt: "Drafted from the approved plan of the 2026-09-05 session (Claude plan file), the architect review of that plan against .claude/hooks/_lib.sh, protect-approvals.sh, require-plan.sh, production-gate.sh, scripts/approve.py, approvers.py, check_artifact_chain.py, log_ledger.py, check_control_plane.sh, check_workflow_permissions.py, sdlc-gate.yml and the decision records; owner answers recorded in intent.md."
record:
resource: https://github.com/luissiviero/lifecycle-axis-/issues/40
tags: [delegation, approvals, hooks, chain-check, auto-merge, policy, control-plane]
timestamp: 2026-09-05T11:28:24Z
---
# Spec: a second way to run a work item, where I approve the start and the AI signs the rest under its own name

## Requirements (each maps to an intent outcome)
Intent outcomes: (1) two modes, delegated runs grant to merge with no owner act; (2) the agent signs under
its own handle with a distinct status; (3) revisions are a recorded last resort; (4) one policy file;
(5) the human-only gates are unchanged; (6) two handoff follow-ups absorbed.

| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | `scripts/delegation.py` loads `.sdlc/delegation.yaml` with the two-level parser from `scripts/approvers.py` and exposes `enabled`, `agents`, `signable`, `risk_classes`, `max_deviations`, `revisions`, `min_reviewers`, `merge` (`enabled`, `require_review`, `require_checks`, `method`, `cool_off_hours`), `locked_paths`; a missing file or `enabled: false` loads a policy on which every `may_*` query answers False | 4 | `scripts/test_delegation.py`: fixture file loads every key; missing file gives `enabled False` and `may_sign("claude") == (False, reason)`; a tab or unknown key raises with `path:line` |
| R-2 | The status vocabulary is `draft`, `in-review`, `approved`, `delegated`, `superseded` everywhere it is enumerated: `check_artifact_chain.py` `STATUSES`, the four templates' status comments, `docs/sdlc/rules/00-chain.md`, `docs/sdlc/templates/log.md`, `knowledge/lessons/ledger-slot-holds-status-only.md`; `gen_index.py` renders `status: delegated; approved-by: <agent>` like the other statuses | 2 | `grep -c delegated` prints ≥ 1 in each listed file; `python3 scripts/gen_index.py --check` exits 0 after regeneration; `scripts/test_gen_index.py` has a delegated case |
| R-3 | `docs/sdlc/templates/intent.md` gains `risk-class`, `mode`, `delegated-by`, `delegated-on` after `approved-on`, with comments saying the last three are human-only; `work/_example/intent.md` carries them; `scripts/adopt.sh` blanks `delegated-by` and `delegated-on` on the copied example as it blanks `approved-by` | 1, 4 | `scripts/test_adopt.py`: the copied `_example/intent.md` has `mode: supervised` and empty `delegated-by`; `check_artifacts.py`-style key comparison of `_example/intent.md` against the template passes |
| R-4 | `check_artifact_chain.py` accepts a `delegated` artifact when all hold: the artifact is in policy `signable`; `approved-by` is in policy `agents`; `log.md` has a `-> delegated` line by that signer; the item's `intent.md` is `approved` by a valid product owner, has `mode: delegated`, a `risk-class` in policy `risk_classes`, and the last commit touching `^mode: delegated$` in it is not an agent identity; `intent.md` itself is never `delegated`. The grant is checked in both in-progress and strict modes whenever any artifact is `delegated`; the predecessor rule accepts `approved`, `superseded`, `delegated` | 2, 5 | `scripts/test_check_artifact_chain.py` class `DelegatedChain`: pass case; fail cases for signer not in agents, artifact not signable, no ledger line, intent delegated, agent-authored grant commit, risk class outside policy, missing policy file, artifact-only diff with `delegated` and no grant |
| R-5 | `check_artifact_chain.py` requires, for every `-> delegated` ledger line on an artifact that already carried a signature or approval, a record `work/<slug>/revisions/<n>.md` named in the line's note, with at least policy `min_reviewers` sections `### Reviewer:` each ending `verdict: revise`; a `keep` verdict, a missing record or too few sections fails; deviation lines (`delegated -> delegated` or `approved -> approved` with note `deviation:`) are counted and more than policy `max_deviations` fails | 3 | `DelegatedChain`: re-sign with a two-reviewer unanimous record passes; with one reviewer, with a `keep`, with no record fails; six deviation lines under `max-deviations: 5` fails, five pass |
| R-6 | `check_artifact_chain.py` with an empty or missing `.sdlc/active` and no `--slug` prints one line `FAIL: no active work item (.sdlc/active is empty; pass --slug or set it)` and exits 1 | 6 | `scripts/test_check_artifact_chain.py::test_empty_active_slug_is_one_clear_failure` |
| R-7 | `scripts/sign.py <slug> <artifact>... [--note TEXT] [--revision revisions/<n>.md]` refuses (exit 3) unless `CLAUDECODE` is set, and (exit 1) unless policy `enabled`, the intent has `mode: delegated`, each artifact is in `signable`, the handle (`SDLC_AGENT_HANDLE`, default `claude`) is in `agents`, the predecessor is `approved`, `delegated` or `superseded`, and, for an artifact already `approved` or `delegated`, `--revision` names an existing record; it writes `status: delegated`, `approved-by`, `approved-on` and appends the ledger line, note prefixed `revision <n>:` when re-signing | 2, 3 | `scripts/test_sign.py`: one test per refusal; the pass case's ledger line parses with `log_ledger.py` and `approved-by` equals the handle; `evals/cases/sign-refuses-without-grant.yaml`, `sign-refuses-human-handle.yaml`, `sign-refuses-intent.yaml`, `sign-refuses-when-policy-off.yaml`, `sign-refuses-resign-without-revision.yaml` |
| R-8 | `scripts/approve.py` gains `--delegate`: only with `intent.md`, sets `mode: delegated`, `delegated-by: HANDLE`, `delegated-on: <today>` beside the approval, refuses when the intent's `risk-class` is outside policy `risk_classes`, and the ledger note carries `mode: delegated`; `--activate` unchanged | 1 | `scripts/test_approve.py`: `--delegate` on a low-risk intent writes the three keys and the note; on `risk-class: medium` refuses with exit 1; `--delegate` with `spec.md` refuses |
| R-9 | `.claude/hooks/protect-approvals.sh` judges the resulting front matter as a whole: it allows `status: delegated` with an `approved-by` in policy `agents` only when the target is in `signable` and the target item's `intent.md` has `mode: delegated` and the policy is enabled; it refuses `approved` and `superseded` as today, any `approved-by` outside `agents` on a `delegated` result, and any change to `mode`, `delegated-by`, `delegated-on` (a new file with `mode: delegated` is a change; `mode: supervised` on a new file is allowed). Bash branch: `check_text` also reads `mode`; the word rule adds `delegat`; a command naming `sign.py` passes the `approve.py` rule; a `gh api` call with a mutating method on a `contents/` or `git/` path is refused | 2, 5 | `scripts/test_protect_approvals.py` class `Delegated`: allow case; refusals for intent target, handle outside agents, `approved`, `mode` edit, new intent with `mode: delegated`, policy off, `gh api -X PUT .../contents/work/x/intent.md`; every existing test unchanged and green; `evals/cases/hook-allows-delegated-sign.yaml`, `hook-refuses-mode-edit.yaml`, `hook-refuses-new-intent-with-grant.yaml` |
| R-10 | `.claude/hooks/require-plan.sh` opens the plan gate when `plan.md` is `approved` by a tech lead (as today) or `delegated` with an approver in policy `agents`, `plan.md` in `signable`, the intent's `mode` `delegated` and the policy enabled; `_lib.sh` gains `policy_value`, `policy_list`, `agent_handle_ok`, `intent_mode`, `delegation_on`; `protect-paths.sh` adds `.sdlc/delegation.yaml` to the never-unlock list | 2, 4, 5 | `scripts/test_hooks_baseline.py`: delegated plan opens with grant, closed without, closed for a handle outside agents; `scripts/test_lib_helpers.py`: the five helpers against a fixture policy; `scripts/test_protect_paths_bash.py`: a write to `.sdlc/delegation.yaml` is refused with the unlock set |
| R-11 | `.claude/settings.json` and `docs/sdlc/templates/claude-settings.json` allow `Bash(gh pr ready*)`, `Bash(gh pr comment*)`, `Bash(gh pr create*)`, `Bash(git push -u origin claude/*)`, `Bash(python3 scripts/sign.py*)`; no deny entry changes | 1 | `python3 -c 'import json; ...'` asserts the five entries in both files; the deny list equals `main`'s |
| R-12 | Skills: `sdlc-intent` asks for the mode and writes `mode: supervised` and `risk-class`; `sdlc-spec`, `sdlc-plan`, `sdlc-incident` end with "when the intent has `mode: delegated`, run `scripts/sign.py` and continue; otherwise stop"; `sdlc-review` posts the summary line; new `sdlc-run` drives spec to ready pull request and states the revision rule verbatim (last resort; blocking error; reviewers per policy on a different model; unanimous `revise` or stop and call back); rules fragments `10`, `30`, `40`, `50` say the same in one line each; `00-chain.md` lists the status; `60-lessons.md` gets the missing pointer; the three context files regenerate under 120 lines | 1, 3, 6 | `scripts/checks/context-drift.sh` and `plugin-manifest.sh` pass; `wc -l CLAUDE.md` ≤ 120; `grep -c 'sign.py' .claude/skills/*/SKILL.md` ≥ 4; `grep -c workflow-permissions-name-every-api docs/sdlc/rules/60-lessons.md` prints 1 |
| R-13 | `REVIEW.md`'s format block ends with `Important: <n> | Nits: <m>`; `docs/sdlc/README.md` gains three enforcement-matrix rows (signature, revision gate, delegated merge) and names `delegation.yaml`; `knowledge/decisions/delegated-mode.md` amends `human-only-approvals.md` and supersedes `merge-click-is-the-gate.md` for delegated items, both of which gain a pointer line; `docs/sdlc/github-setup.md` and `.sdlc/README.md` describe the grant routine and the policy file | 4 | `python3 scripts/check_okf.py` ends `0 warnings`; `grep -c 'Important: <n>' REVIEW.md` prints 1; `grep -c delegated-mode knowledge/decisions/human-only-approvals.md knowledge/decisions/merge-click-is-the-gate.md` prints 1 each |
| R-14 | `.github/workflows/delegated-merge.yml` runs on `workflow_run` completion of the policy's `require_checks` workflows from the default branch with `contents: write`, `pull-requests: write`, `checks: read`, `concurrency` keyed on the head SHA, and calls `scripts/delegated_merge.py`; `scripts/check_workflow_permissions.py` allowlists the file and compares repo-relative paths | 1, 5 | `scripts/checks/workflow-permissions.sh` and `workflow-yaml.sh` pass; `scripts/test_check_workflow_permissions.py::test_allowlist_matches_relative_path`; `grep -c 'actions/checkout' .github/workflows/delegated-merge.yml` prints 1 (main only; no head checkout) |
| R-15 | `scripts/delegated_merge.py` merges only when every condition holds, and prints one line per condition with its verdict under `--dry-run`: policy `merge.enabled`; event is a pull request from this repository; PR resolved via `commits/<sha>/pulls`, not draft, head prefix in `AGENT_BRANCH_PREFIXES`, body has `Work-Item:`; every check run on the head SHA except itself is completed and successful and every `require_checks` name is present (a pending one exits 0 silently); the head's `intent.md` has `mode: delegated`, `status: approved`, a risk class in policy, and the grant commit is `verification.verified` with `author.login` holding `product-owner`; the diff touches nothing under `PROTECTED_PATHS`, `RELEASE_GATED_PATHS` or policy `locked_paths`; when `require_review`, the `claude[bot]` tracking comment ends with `Important: 0`; `cool_off_hours` elapsed. It merges with `sha` and `merge_method` from policy, deletes the branch, and comments `merged under delegation granted by <handle> in <sha>` | 1, 5 | `scripts/test_delegated_merge.py`: one fixture per refusal (each condition), the allow case asserts the merge request body; `--dry-run` against a supervised item's pull request prints the grant refusal |
| R-16 | Suite green on every pull request of this item | all | `VERIFY: PASS`; `CHAIN: PASS` with `--slug delegated-mode` once approved; `EVALS: N pass, 0 fail`; `OKF: N docs, 0 warnings`; test count grows over `main` |

## Design
### Architecture / data flow
```
owner (web editor or approve.py --delegate --activate, a human commit on main)
   └─ intent.md: status approved, mode delegated, risk-class low; log.md line; .sdlc/active
agent session (/sdlc-run)
   ├─ spec.md  ── sign.py ──> status delegated, approved-by claude, ledger line
   ├─ plan.md  ── sign.py ──> same; require-plan.sh opens on it (policy + grant)
   ├─ build, verify, /sdlc-review, PR ready, ledger `PR #n | draft -> in-review`
   └─ a blocking error → revisions/<n>.md (reviewers per policy) → unanimous revise → sign.py --revision
CI
   ├─ sdlc-gate: check_artifact_chain.py validates signatures, grant, revisions, deviation cap
   ├─ pr-review: claude[bot] comment ending `Important: 0`
   └─ delegated-merge (workflow_run): delegated_merge.py → merge as github-actions[bot], comment
```
Every reader of the policy goes through one of two entry points: `scripts/delegation.py` (Python) and the
`policy_*` helpers in `_lib.sh` (awk). Nothing else parses the file.

**D1. Policy file** (R-1, R-10). `.sdlc/delegation.yaml`, created by the owner on `main` from
`docs/sdlc/templates/delegation.yaml`:
```yaml
enabled: true
agents: [claude, claude[bot]]
signable: [spec.md, plan.md, incident.md]
risk-classes: [low]
max-deviations: 5
revisions: consensus
min-reviewers: 2
merge:
  enabled: true
  require-review: true
  require-checks: [sdlc-gate, agent-evals, pr-review]
  method: merge
  cool-off-hours: 0
locked-paths: [scripts/check_artifact_chain.py, scripts/approvers.py, scripts/log_ledger.py, scripts/approve.py, scripts/sign.py, scripts/delegation.py, scripts/delegated_merge.py, scripts/check_control_plane.sh, scripts/check_workflow_permissions.py, REVIEW.md, .claude-plugin]
```
`approvers._parse` is reused as-is (it already handles nested two-level maps and flow lists); the
`TOP_KEYS` check moves into a parameter so each file names its own keys. `protect-paths.sh` adds the
path to the hard-coded never-unlock case, so the session cannot write it even in the kit repo.

**D2. Grant** (R-3, R-8). Front matter on `intent.md` after `approved-on`:
```
# risk-class: low | medium | high; the grant below is valid only for classes the policy lists
risk-class: low
# mode: supervised | delegated; delegated-by and delegated-on are set only by a human, like approved-by
mode: supervised
delegated-by:
delegated-on:
```
`approve.py --delegate` sets the three values with the approval; the ledger line's note is
`mode: delegated`. From the web editor the owner edits the same six lines and appends the same ledger line.
CI's author check for the grant reuses the existing `-G` pattern with `^mode: delegated$` and the same
"HEAD still says so" guard, in `check_artifact_chain.py`. The merge script's server-side check reads
`GET repos/{r}/commits/{sha}` and requires `commit.verification.verified` true and `author.login` in the
`product-owner` role; web-editor commits satisfy it, local commits need `git commit -S`.

**D3. Signature** (R-2, R-4, R-7). `sign.py` mirrors `approve.py`'s structure (validate everything, then
write) and reuses `set_front_matter`, `log_ledger.render` and `front_matter`. It is the only writer of
`status: delegated` on the honest path; the hook is the tripwire and CI the backstop, as for approvals.
Chain order: `PREDECESSOR` as in `approve.py`, accepted statuses `approved`, `delegated`, `superseded`.

**D4. Revision gate** (R-5, R-7). Template `docs/sdlc/templates/revision.md`, front matter `type:
sdlc/revision`, `id: <slug>-revision-<n>`, `title`, `artifact` (the file to re-sign), `trigger` (the error
or finding that blocks the plan, with evidence: command, output, `file:line`), `timestamp`; body: a
`Proposal` section, then one `Reviewer: <role> (<model>)` section per reviewer, each ending with a line
`verdict: revise` or `verdict: keep`. `sign.py --revision` checks the section count and verdicts before writing; `check_artifact_chain.py`
checks them again from the committed file. A deviation is a plan edit limited to `## Files that change`,
`## Order of work` numbering and `## Deviations log`; the ledger line note starts with `deviation:`. The
chain check counts those lines per item against `max_deviations`. Which edits count as a deviation is a
rule the skills state and the reviewer enforces; the chain check enforces the count and the record.

**D5. Hook rules** (R-9, R-10). `protect-approvals.sh`'s `check_result` collects the resulting `status`,
`approved-by`, `approved-on`, `mode`, `delegated-by`, `delegated-on` (every occurrence, as `fm_all` does
today) and decides once: refuse on `approved`/`superseded` where the file says otherwise; refuse any
`mode`/`delegated-*` change; if the result is `delegated`, require `delegation_on`, the target in
`signable`, the target not `intent.md`, `agent_handle_ok` on every `approved-by` occurrence, and
`intent_mode` of the target's slug equal to `delegated`; otherwise refuse `approved-by`/`approved-on`
changes as today. `require-plan.sh` adds the `delegated` branch after the `approved` branch, reading the
same helpers. Both helpers read the policy from `$ROOT/.sdlc/delegation.yaml` at call time, so a policy
edit applies to the next tool call with no session restart.

**D6. Merge workflow** (R-14, R-15). `workflow_run` runs from the default branch, so the script and the
policy it reads are `main`'s. Fork pull requests are refused by the head-repository check. A race with a
new push is closed by passing `sha` to the merge endpoint. The `locked_paths` refusal is what makes "the
head's `sdlc-gate` is green" trustworthy: every file that judges the chain is identical on head and main.
`merge_method: merge` keeps the owner's web-editor commits and the agent's signing commits as distinct
authors in `main`'s history, which the `-G` checks read.

### Interfaces (APIs, events, schemas) — exact shapes
- `scripts/delegation.py`: `load(path=None) -> Policy`; `Policy.may_sign(handle) -> (bool, reason)`,
  `may_sign_artifact(name)`, `risk_ok(cls)`, `merge` (a dict with the keys in D1), `locked_paths` (list),
  `max_deviations` (int), `revisions` (`never|consensus|free`), `min_reviewers` (int); CLI
  `python3 scripts/delegation.py` dumps JSON, `--may-sign HANDLE` exits 0/1.
- `scripts/sign.py`: exit 0 ok, 1 validation, 3 refused (not an agent session). Ledger line:
  `- <ts> | <artifact> | <old> -> delegated | <handle> | <sha> | <note>`.
- `scripts/approve.py --delegate`: as today plus the three keys; refuses with exit 1 on a risk class the
  policy does not list.
- `scripts/delegated_merge.py [--dry-run] [--event FILE]`: reads the `workflow_run` event JSON; exit 0 on
  merge or on a silent wait; exit 1 on a refusal (printed, one line per condition).
- `_lib.sh`: `policy_value <key>`, `policy_list <key>` (one item per line), `agent_handle_ok <handle>`,
  `intent_mode <slug>`, `delegation_on`.
- Ledger vocabulary: `-> delegated` (signature), `delegated -> delegated` with note `deviation: <path>` or
  `revision <n>: <line>`, `approved -> delegated` with note `revision <n>: <line>` (a revision of a
  human-approved artifact), `approved -> approved` with note `deviation:` (a deviation on a human plan).

### Data and migrations
No stored data changes. Existing artifacts are untouched: the new intent keys are read with a default
(`mode` empty means `supervised`), so every existing work item stays valid without edits.

### Failure modes and how they surface
- Policy file missing or `enabled: false` → `sign.py` exit 1 naming the file; hooks refuse `delegated`
  with the same reason; the chain check fails any `delegated` artifact; the merge workflow exits 0 with
  "policy off" in its log. Everything is closed; supervised mode unaffected.
- `pr-review` has no credential → no `claude[bot]` comment → `require_review` refuses → the pull request
  waits for the owner. Visible in the merge workflow's log and in `--dry-run`.
- A check flakes red → the merge script refuses; a re-run that turns green fires `workflow_run` again.
- A new push after the check completed → the merge endpoint refuses on `sha`; the next completion retries.
- A revision record with a `keep` → `sign.py` refuses; the skill says stop and call the owner back.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: an agent identity satisfies a gate that today only a human satisfies — policy:
  `knowledge/decisions/human-only-approvals.md` — contradiction? partial: the record says an agent never
  sets `approved`; this spec keeps that literally and adds a second word — owner: luissiviero —
  resolution: the new decision record amends the old one and lists the human-only gates that stay.
- C2: the merge click stops being the gate for delegated items — policy:
  `knowledge/decisions/merge-click-is-the-gate.md` — contradiction? yes, for delegated items only — owner:
  luissiviero — resolution: the grant is the click; the record gains a superseded-for-delegated pointer;
  the server-side grant check (D2) replaces the git-author backstop the click made sufficient.
- C3: a session running with the owner's own GitHub login could create a GitHub-signed grant commit
  through the API — policy: security-standards (identity) — contradiction? no, a residual — owner:
  luissiviero — resolution: the hook refuses mutating `gh api` calls on `contents/` and `git/` paths
  (R-9); the decision record states that delegated mode requires the session to hold an agent identity
  (the remote sessions' Claude app identity, or a bot token locally), never the owner's login.
- C4: hook, workflow and `.sdlc/active` edits by the session — policy: rule 3 — contradiction? no —
  owner: luissiviero — resolution: `control-plane-approved` on pull requests 1b and 2; `.sdlc/active` and
  `.sdlc/delegation.yaml` are the owner's own commits on `main`.
- C5: `REVIEW.md` is pinned from the base branch by `pr-review.yml` — policy: that workflow's design —
  contradiction? no — owner: luissiviero — resolution: the summary line takes effect after pull request 1c
  merges, before pull request 2 needs it.

## Open questions carried from intent.md
- Q3 (no credential or a flake): proposed fail closed; D6 and the failure modes assume it.
- Q4 (second reviewer's model): proposed a different model, named in the record; the template's
  `## Reviewer: <role> (<model>)` heading assumes it.

## Decisions (ADR-style: context → decision → consequences)
- D-a: a distinct status word rather than `approved` with an agent handle → every existing rule and
  reader that says "approved means a human read it" stays true; one more value in five enumerations.
- D-b: the grant on the intent, never on a later artifact → the agent never signs the file that carries
  the grant, so it cannot widen its own permission; a change of intent needs a new intent.
- D-c: one policy file rather than keys in `config.env` and `approvers.yaml` → one place to tune, one
  parser, one never-unlock entry; `approvers.yaml` and `config.env` are untouched.
- D-d: revision needs a committed consensus record, checked by CI, rather than a rule in a skill alone →
  the owner can find every plan change and who argued for it; the cost is one file per revision, which
  is the point.
- D-e: the merge is a CI workflow with the repository token rather than the session's `gh` → the merger
  is `github-actions[bot]`, deterministic conditions, no new credential; supersedes the click for
  delegated items only.
- D-f: `merge_method: merge`, never squash → history keeps distinct authors for the `-G` checks.
- D-g: four small pull requests on one chain → each readable from a phone; the plan lists every file so
  the chain check passes on each.

## Gotchas found while reading the codebase
- `compare_fields` in `protect-approvals.sh` judges one field at a time; the delegated rule needs the
  resulting status and handle together, hence the `check_result` restructure (D5).
- `approver_has_role` in `_lib.sh` fails closed on `never-approve`, which lists `claude`; the agent helper
  is separate on purpose and never consults that list.
- `approvers._parse` raises on a top-level key outside `TOP_KEYS`; that is why the policy is its own file.
- `check_workflow_permissions.py` compares absolute paths against a relative allowlist, so today's
  allowlist can never match; R-14 fixes the comparison.
- `REVIEW.md` has no summary line; the merge condition needs one, and `pr-review.yml` reads `REVIEW.md`
  from the base branch, so it must merge before the merge workflow relies on it.
- Under `SDLC_UNATTENDED` every `ask` from `production-gate.sh` is a block; the run skill must never issue
  a deploy-shaped command, and `gh pr ready`, `gh pr comment`, `gh pr create` and a push to a `claude/`
  branch are not deploy-shaped (verified against `DEPLOY_RE`, `GH_API_RE`, `push_reaches_protected`).
- `agent-evals.yml` has a `paths:` filter; a pull request outside those paths produces no `agent-evals`
  check run, so "every `require_checks` name present" must treat a workflow that did not trigger as
  absent, not pending. The script reads the workflow's `paths:` to decide (or the owner drops the name).

## Not doing
- Tiering `PROTECTED_PATHS` (follow-up item, run in delegated mode).
- Retiring `.sdlc/active` when an item completes; the grant overwrites it.
- A merge cool-off greater than zero by default (the key exists for the owner to raise).
- Letting the agent sign `intent.md` or `incident.md` of a supervised item.
- Fixing `skill-spec-flags-concerns` or adding the NUL-byte check.
