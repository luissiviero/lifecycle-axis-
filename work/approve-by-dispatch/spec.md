---
type: sdlc/spec
id: approve-by-dispatch
title: One tap in the Actions tab writes what approve.py writes, with the run's actor as the human act
description: "A workflow_dispatch workflow runs scripts/approve.py with the run's actor as the handle and commits the result, so every approval and every delegation grant is one tap; the commit carries the run id, and the chain check and the merge script verify a dispatch-made decision against the run's server-side record."
stage: design
status: in-review
reads: intent.md
approved-by:
approved-on:
skills-applied: [security-standards]
skills-version: c98cb19
prompt: "/sdlc-spec approve-by-dispatch, in the session that built delegated mode (session_01EF2oWHtpLmPRkivdcz75p1), from the approved intent and an explorer pass over approve.py, check_artifact_chain.py, delegated_merge.py, the existing workflows and production-gate.sh"
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/47
tags: [approvals, delegation, workflow-dispatch, control-plane, chain-check, auto-merge]
timestamp: 2026-09-06T15:45:00Z
---
# Spec: one tap in the Actions tab writes what approve.py writes, with the run's actor as the human act

## Requirements (each maps to an intent outcome)

| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | `.github/workflows/approve.yml` runs on `workflow_dispatch` with inputs `artifact` (choice: `intent.md`, `spec.md`, `plan.md`, `incident.md`), `mode` (choice: `supervised`, `delegated`; read only when the artifact is `intent.md`), `slug` (string, optional; empty means the slug in `.sdlc/active` on the checked-out ref) and `note` (string, optional). It declares `permissions: contents: write` and nothing else, holds a `run-name` carrying actor, slug, artifact and mode, checks out only the dispatch ref, and installs no dependency | one tap | `scripts/checks/workflow-permissions.sh` and `workflow-yaml.sh` pass with the file allowlisted; `grep -c 'actions/checkout' .github/workflows/approve.yml` prints 1; `scripts/test_check_workflow_permissions.py::CheckFile::test_real_workflows_directory` passes with the new allowlist entry |
| R-2 | The workflow refuses, before writing anything, when the run's `github.actor` does not hold the artifact's role in `.sdlc/approvers.yaml`, is a `never-approve` handle, or is a placeholder. The refusal is the job failing with the reason in the step summary and no commit | the tap is the human act | `scripts/test_approve_dispatch.py`: `resolve_actor` refuses a handle outside the role, a `never-approve` handle and an empty actor, each with the reason; the workflow calls it before `approve.py` |
| R-3 | `scripts/approve.py` gains `--from-dispatch RUN_ID` (with `--as` required alongside it): it skips the `CLAUDECODE` refusal only when `GITHUB_ACTIONS=true` and `GITHUB_RUN_ID` equals the value, records the run id for the commit trailer, and changes nothing else about what it writes | one tap | `scripts/test_approve.py::ApproveFromDispatch`: `--from-dispatch` outside Actions exits 3; inside a faked Actions env writes exactly the same files as a plain run (byte-compared); the ledger line and front matter are unchanged |
| R-4 | The workflow commits what `approve.py` wrote with `author` set to the actor's GitHub identity (`<id>+<login>@users.noreply.github.com`, resolved from the users API) and `committer` set to `github-actions[bot]`, and the message ends with the trailers `Approved-Run: <run id>` and `Approved-Actor: <login>`. It pushes to the dispatch ref. Nothing else is staged: `git status --porcelain` after the run lists only the item's files and `.sdlc/active` | one tap; the tap is the human act | `scripts/test_approve_dispatch.py::Commit`: the message ends with both trailers; the author matches the actor and the committer is the bot; a diff containing any other path aborts the push |
| R-5 | `scripts/check_artifact_chain.py` accepts a dispatch-made approval: when the commit that introduced `status: approved` carries an `Approved-Run:` trailer, the author check reads the trailer's `Approved-Actor` as the deciding handle and requires it to equal the artifact's `approved-by`; the existing git-author rule still applies to every commit without the trailer | one tap; the tap is the human act | `scripts/test_check_artifact_chain.py::ApprovalAuthor`: a trailer commit whose `Approved-Actor` matches passes; one whose trailer names a different handle than `approved-by` fails; an agent-authored commit with no trailer still fails |
| R-6 | When a token is available (`GH_TOKEN` or `GITHUB_TOKEN`), the chain check verifies the trailer against the run: the run exists in this repository, its `event` is `workflow_dispatch`, its `path` is `.github/workflows/approve.yml`, its `conclusion` is `success`, and its `actor.login` equals `Approved-Actor`. A mismatch fails; no token means the trailer is accepted on the author rule alone and the run says so in one note line | the tap is the human act | `scripts/test_check_artifact_chain.py::DispatchAttestation`: a fixture run with a different actor, a different workflow path or a different event fails; with no token the check passes and prints the note |
| R-7 | `scripts/delegated_merge.py` accepts a dispatch-made grant: `check_grant_commit` takes a third path beside "product-owner committer" and "web-flow", namely a commit whose `Approved-Run:` trailer resolves to a successful `workflow_dispatch` run of `.github/workflows/approve.yml` in this repository whose actor holds `product-owner` and equals the intent's `delegated-by`. Every other condition is unchanged, and a trailer that does not resolve is refused | one tap | `scripts/test_delegated_merge.py::GrantCommit`: a trailer commit with a matching run is ok; with a run of another workflow, another event, a failed conclusion, another actor, or no run at all, refused; the existing unverified-signature and spoofed-author cases still refuse |
| R-8 | With `mode: delegated` the workflow refuses unless the dispatch ref is the repository's default branch, and passes `--delegate --activate` so the grant and `.sdlc/active` land on `main` | both directions, per item | `scripts/test_approve_dispatch.py::Mode`: a delegated dispatch on a non-default ref fails naming the ref; a supervised dispatch on any ref proceeds; the delegated call carries both flags |
| R-9 | An agent session still cannot press it: `production-gate.sh` continues to catch `gh workflow run` (ask when attended, block when unattended), and `protect-approvals.sh` continues to refuse a Bash command naming `approve.py` | the AI still cannot press it | `evals/cases/gate-blocks-workflow-dispatch.yaml`: an unattended session running `gh workflow run approve.yml` is blocked; `evals/cases/approve-refuses-in-agent-session.yaml` still passes unchanged |
| R-10 | The skills ask for the tap instead of "wait for a human": `sdlc-intent`, `sdlc-spec`, `sdlc-plan`, `sdlc-incident` and `sdlc-run` name the three inputs to give the owner (`slug`, `artifact`, `mode`); the rule fragments and `docs/sdlc/README.md`'s matrix say the tap is the human act; `docs/sdlc/github-setup.md` and `docs/sdlc/handoff/HANDOFF.md` carry the routine | one tap | `scripts/checks/context-drift.sh` passes; `wc -l CLAUDE.md` ≤ 120; `grep -c 'approve.yml' .claude/skills/*/SKILL.md` ≥ 4; `python3 scripts/check_okf.py` ends `0 warnings` |
| R-11 | `knowledge/decisions/approve-by-dispatch.md` amends `delegated-mode.md` and `human-only-approvals.md`: the human act is the tap, recorded by GitHub, and `approved` is still a word only a human causes to be written | the tap is the human act | `python3 scripts/check_okf.py` ends `0 warnings`; `grep -c approve-by-dispatch knowledge/decisions/human-only-approvals.md knowledge/decisions/delegated-mode.md` prints 1 each; `knowledge/decisions/index.md` lists it |
| R-12 | The whole loop is green: `scripts/verify.sh` ends `VERIFY: PASS`, the chain check ends `CHAIN: PASS`, `scripts/run_evals.sh` ends `0 fail`, `check_okf.py` ends `0 warnings` | every outcome | those four last lines, pasted in the pull request |

## Design

### Architecture / data flow

```
owner: Actions tab -> Run workflow (branch selector = the target ref)
   inputs: artifact, mode, slug?, note?
        |
approve.yml, on the dispatch ref, permissions: contents: write
  1. checkout the dispatch ref (the only checkout)
  2. resolve the actor:  scripts/approve_dispatch.py --check-actor "$GITHUB_ACTOR" --artifact ...
       refuses (job fails, no commit) unless the actor holds the artifact's role
  3. python3 scripts/approve.py <slug> <artifact> --as "$GITHUB_ACTOR" \
        --from-dispatch "$GITHUB_RUN_ID" [--note ...] [--delegate --activate]
  4. scripts/approve_dispatch.py --commit  (author = actor identity, committer = the bot,
        trailers Approved-Run / Approved-Actor, refuses any path outside work/<slug>/ + .sdlc/active)
  5. git push origin HEAD:<dispatch ref>
        |
later, on the pull request or the merge:
  check_artifact_chain.py  -> trailer path (R-5, R-6)
  delegated_merge.py       -> trailer path for the grant (R-7)
```

The decision is the tap. GitHub records who made it (`github.actor` on the run, readable afterwards through
`GET /repos/{owner}/{repo}/actions/runs/{id}`), and nothing inside the run can change that field: it is not
an input, not a commit field, and not writable by the token. Everything the run writes is therefore
attributable to that actor, and the two checkers verify the attribution from the run rather than from the
commit alone.

### Interfaces (APIs, events, schemas) — exact shapes

- `scripts/approve.py <slug> <artifact>... [--as HANDLE] [--note TEXT] [--delegate] [--activate]
  [--dry-run] [--from-dispatch RUN_ID]`. `--from-dispatch` requires `--as`, requires
  `GITHUB_ACTIONS=true` and `GITHUB_RUN_ID == RUN_ID`, and exits 3 otherwise; it suppresses only the
  `CLAUDECODE` refusal (a runner has no `CLAUDECODE`, so this is belt and braces) and makes the run id
  available to the committer step through `$GITHUB_OUTPUT`. Everything else the script writes is byte
  identical to a shell run.
- `scripts/approve_dispatch.py --check-actor LOGIN --artifact NAME [--root DIR]` → exit 0 with `ok` on
  stdout, exit 1 with the reason from `approvers.Approvers.is_valid`. `--commit --actor LOGIN --run-id N
  --slug S [--artifact NAME]` → stages exactly `work/<slug>/{intent,spec,plan,incident,log,index}.md` and
  `.sdlc/active`, refuses (exit 1) if `git status --porcelain` lists anything else, and commits with the
  author, committer and trailers of R-4. stdlib only, `gh api` for the users lookup.
- Commit message shape:
  ```
  [<slug>] Approve <artifact> as <actor>

  <note, when given>

  Approved-Run: <run id>
  Approved-Actor: <login>
  ```
- `check_artifact_chain.py`: a new helper `dispatch_attestation(commit_sha) -> (run_id, actor) | None`
  reading the trailers with `git log -n1 --format=%B`, and `verify_dispatch_run(run_id, actor)` calling
  `gh api repos/{repo}/actions/runs/{id}` when a token is present. The existing
  `git log -n1 --format=%an%x00%ae -G '^status: approved$'` call stays as the path for every commit with
  no trailer.
- `delegated_merge.py`: `check_grant_commit(..., dispatch=None)` where `dispatch` is the resolved run for
  the grant commit; the third acceptance path is `dispatch.event == "workflow_dispatch"`,
  `dispatch.path == ".github/workflows/approve.yml"`, `dispatch.conclusion == "success"`,
  `dispatch.actor.login` holds `product-owner` and equals the intent's `delegated-by`.

### Data and migrations

No stored data changes and no new fields on any artifact. The commit trailers are message text, not front
matter, so every existing artifact stays valid and every existing approval keeps passing under the
unchanged author rule. Classification: the actor login is public GitHub data (rule 4, nothing personal or
regulated).

### Failure modes and how they surface

- Actor outside the role → the job fails at step 2, no commit, the reason in the step summary. The owner
  sees a red run and nothing changed.
- `approve.py` refuses (chain order, risk class outside the policy, already approved) → the job fails with
  the script's own message; nothing is committed because the commit step never runs.
- The dispatch ref is not the default branch with `mode: delegated` → refused at step 2 (R-8).
- The push races another push to the same ref → the push fails, the run is red, nothing is half-applied
  (the commit is local to the runner). The owner taps again.
- No token where the chain check runs (a local `verify.sh`) → the trailer is accepted on the author rule
  and the run prints one note line saying the attestation was not verified. CI always has a token.
- The Actions API is unreachable from the merge script → `MergeError`, the merge is refused, the pull
  request waits. Fail closed, as every other condition there does.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)

- C1: a commit whose author is the owner was not typed by the owner — policy:
  `knowledge/decisions/human-only-approvals.md` — contradiction? partial — owner: luissiviero —
  resolution: the author field is already forgeable today (`git commit --author`), which that record
  accepts as a residual backstopped by CI; this item narrows rather than widens it, because the trailer
  plus the Actions API makes a dispatch-made approval *verifiable* where a hand-typed one is only
  plausible. The committer stays `github-actions[bot]` so the commit never claims a human typed it.
- C2: the workflow holds `contents: write` and pushes to `main` — policy: rule 3, security-standards §6 —
  contradiction? no — owner: luissiviero — resolution: second entry in `CONTENTS_WRITE_ALLOWLIST`, one
  checkout of the dispatch ref only, no PR-head code executed, the staged-path allowlist of R-4, and the
  workflow file itself is control-plane so it needs the label and the owner's review to change.
- C3: anyone with write access can press Run, not only the owner — policy: `.sdlc/approvers.yaml` —
  contradiction? no — owner: luissiviero — resolution: pressing is not deciding; the workflow refuses an
  actor outside the artifact's role before writing, and on this repository that role is the owner alone.
- C4: `delegated_merge.py` gains a third acceptance path, so the grant no longer always carries a GitHub
  signature — policy: `knowledge/decisions/delegated-mode.md` decision 6 — contradiction? partial —
  owner: luissiviero — resolution: the signature was a proxy for "a human caused this"; the run record is
  a stronger proxy, since it names the actor server-side and cannot be set by the commit. Both paths stay;
  the new one is not a fallback but an alternative with its own conditions, and a trailer that fails to
  resolve is refused rather than falling back.
- C5: the session that drafts an item also tells the owner which inputs to tap — policy:
  security-standards §8 — contradiction? no — owner: luissiviero — resolution: naming the inputs is not
  approving; the owner reads the artifact and chooses, and the run records who chose.

## Open questions carried from intent.md

- Q: every approval as a tap, or only the delegation grant? A: (intent, accepted) every approval.
- Q: where does a delegated grant land? A: (intent, accepted) on `main`; R-8 enforces it.
- Q: who may press Run? A: (intent, accepted) anyone with write access; only a role holder passes.
- Q: how does the AI ask? A: (intent, accepted) it posts the three inputs; R-10 puts that in the skills.
- Q: may a run demote an artifact? A: (intent, accepted) no; a demotion stays a web-editor edit.

## Decisions (ADR-style: context → decision → consequences)

- D1: **The run's actor is the identity, and the commit carries it as a trailer.** Context: the chain check
  is git-only and reads the commit author; the merge script reads the API and wants a signature; neither
  can see a dispatch by itself. Decision: the run writes `Approved-Run` and `Approved-Actor` trailers, and
  both checkers gain a path that resolves them against the Actions API. Consequences: one new API surface
  for the chain check (`actions: read` on `sdlc-gate.yml`), and the trailer becomes the audit anchor.
- D2: **Author is the actor, committer is the bot.** Alternative considered: commit entirely as
  `github-actions[bot]`. Rejected because `is_agent_identity` matches `[bot]@` in the email, so every
  dispatch-made approval would need the API path to pass the chain check, which fails closed on a local
  `verify.sh` with no token. With the author as the actor, the existing rule keeps working unchanged and
  the trailer adds verification on top. Consequence: the split identity has to be explained once, in the
  decision record, so a reader of `git log` is not misled.
- D3: **The dispatch ref is the target.** Alternative: a `branch` input. Rejected because GitHub's own
  "Use workflow from branch" selector is already that input, and a second one could disagree with it.
  Consequence: a branch cut before `approve.yml` exists cannot be selected; the item's first branch after
  the merge is the first that can.
- D4: **`approve.py` is reused, not reimplemented.** The workflow calls the same script the owner would
  call in a shell, so the two routes cannot drift. Consequence: `--from-dispatch` is the only new flag,
  and the byte-comparison test of R-3 pins the equivalence.
- D5: **The workflow refuses before it writes.** The role check runs as its own step, so a refusal leaves
  the tree untouched and the failure is one line in the summary, rather than a half-written item.
- D6: **The staged-path allowlist is in the committer, not in the workflow.** A shell `git add work/...`
  would glob; the script compares `git status --porcelain` against the exact list and aborts on anything
  else, so a stray file from a future change to `approve.py` cannot ride along.

## Gotchas found while reading the codebase

- `scripts/approve.py` commits nothing: it writes and prints the commit command
  (`scripts/approve.py:202-206`, docstring at `:25`). The workflow must do the commit itself, which is
  why `approve_dispatch.py --commit` exists at all.
- The ledger sha comes from `git rev-parse --short HEAD` *before* the approval commit exists
  (`scripts/approve.py:122`), so a dispatch-made line cites the parent, exactly as a hand-written one
  cites the head at the time. The chain check never compares that column
  (`scripts/check_artifact_chain.py:492-497`), so this is cosmetic, and it is the nit the reviewer raised
  on pull request 47. Recording it here rather than changing it: rewriting the column would need a second
  commit amending the ledger the first one wrote.
- `is_agent_identity` (`scripts/check_artifact_chain.py:127-134`) matches `@anthropic.com$`, `\[bot\]@`
  and `^noreply@` in the *email*. The owner's web-editor identity
  (`69210737+luissiviero@users.noreply.github.com`) matches none of them, which is why D2's author choice
  keeps the existing rule working.
- The author check only runs when `HEAD`'s front matter still says the status it is checking
  (`scripts/check_artifact_chain.py:540-547`); it is git-only, with no API call anywhere in that file.
- `handle` comes from `--as` or `git config sdlc.approver` and never from `user.name`
  (`scripts/approve.py:91`), so the workflow passes `--as "$GITHUB_ACTOR"` and needs no git identity to
  run the script itself.
- No workflow in this repository commits or pushes today, and none configures a git identity: `approve.yml`
  is the first. `delegated-merge.yml` mutates only through the API.
- No workflow uses `github.actor`, `run-name` or `github.run_id` today either; all three are new ground
  here, so the plan verifies them on a real run rather than assuming.
- `workflow_dispatch` runs the workflow file *from the selected ref*, which is what makes D3 work and also
  what limits it (a ref without `approve.yml` cannot be chosen).
- `production-gate.sh:26` already catches `gh workflow run` in its deploy regex, asking when attended and
  blocking under `SDLC_UNATTENDED` (`:117-118`). R-9 pins that rather than adding a rule.
- `scripts/test_check_workflow_permissions.py::CheckFile::test_real_workflows_directory` reads the live
  workflow directory, so `approve.yml` fails the suite until its allowlist entry lands in the same commit.

## Not doing

- Retiring `.sdlc/active` when an item completes: the standing follow-up, still open. This item sets the
  slug on a delegated grant (`--activate`) but never clears it.
- Pre-filling the dispatch inputs from a link: GitHub offers no URL that populates a `workflow_dispatch`
  form, so the AI hands the owner three values to pick, not a one-click link.
- A demotion or a revocation route: out of scope by the intent's own answer; both stay web-editor edits.
- Signing the dispatch-made commit: the runner has no key, and the run record replaces the signature for
  the one check that wanted it (C4). Stated here as security-standards §2's "state the authz rule": the
  authz rule for every write this workflow makes is "the run's actor holds the artifact's role".
- Changing `.sdlc/approvers.yaml`, `.sdlc/delegation.yaml` or `.sdlc/config.env`.
