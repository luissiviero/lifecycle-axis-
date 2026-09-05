---
type: decision
title: Only a human can flip an artifact to approved
description: A PreToolUse hook, protect-approvals.sh, refuses any agent-side edit that sets status approved or superseded, approved-by or approved-on on a chain artifact, and any Bash call of scripts/approve.py or unset of CLAUDECODE; the control-plane unlock never applies; require-plan.sh also checks that the approver holds the plan's role. Decided in work/approval-gate (consensus item 1).
tags: [hooks, approvals, chain-check, control-plane, sdlc]
timestamp: 2026-09-05T01:40:00Z
---

# Only a human can flip an artifact to approved

## Context

The artifact chain rests on `status: approved` and `approved-by` in `work/<slug>/{intent,spec,plan,incident}.md`.
Before this decision the only guards were `scripts/approve.py` refusing to run with `CLAUDECODE` set and
`scripts/check_artifact_chain.py` rejecting an approval commit with an agent author in CI. Nothing stopped an
agent session from editing the front matter directly: an Edit of `status: approved` passed every hook, and in the
kit repo the control-plane unlock (`SDLC_CONTROL_PLANE_UNLOCK=1`, `self-hooks-on.md`) would have let the same
session write `.sdlc/approvers.yaml` too. The consensus review with the playbook listed this as item 1.

## Decision

1. **A hook, not a convention.** `.claude/hooks/protect-approvals.sh` runs on `Edit|Write|MultiEdit|NotebookEdit`
   and on `Bash`, after `protect-tests.sh`. On the edit branch it applies the edit to a copy of the file's current
   text (Write and NotebookEdit carry the whole new text; Edit and MultiEdit carry literal replacements) and
   compares the *resulting* front matter with the current one: `approved` or `superseded` where the file says
   otherwise, or a non-empty `approved-by`/`approved-on` that differs from the current value, is refused (exit 2).
   Judging the result rather than the words of the edit is what catches a bare-value edit such as
   `luissiviero` → `mallory` on an approved plan (PR #25 review). Drafting, revising and `status: in-review` pass,
   and so does a body edit on an approved artifact, so a deviations log stays editable.
2. **The Bash branch refuses the act, not just the file.** Any command naming `approve.py`, or unsetting or
   reassigning `CLAUDECODE`, is refused before the write guard is consulted, so it holds with
   `BASH_WRITE_GUARD=0`. With the guard on, a write candidate that is a chain artifact already carrying an
   approval (`status: approved|superseded` or a non-empty `approved-by`) is refused outright: an approved
   artifact changes only through Write/Edit, where the result can be checked. A write to a draft is checked
   against the command text, and a write whose text mentions `approved` or `supersed` is refused.
3. **No unlock.** `SDLC_CONTROL_PLANE_UNLOCK` is never read by this hook. The kit repo's own sessions cannot
   approve either; the owner approves from their shell (`scripts/approve.py`) or from the GitHub web editor.
4. **`require-plan.sh` checks the approver.** An approved plan gates implementation only when `approved-by` holds
   the plan's role (`artifacts.plan.md` in `.sdlc/approvers.yaml`, `tech-lead` by default) and is not listed under
   `never-approve`; a missing approvers file fails closed.

## Alternatives considered

- Blocking every write that touches an approval field: would stop drafting and the deviations log. Rejected.
- A `python3` call from the hook to `scripts/approvers.py`: an import-time `git rev-parse` and the Windows Store
  `python3` stub add latency and a failure mode; the awk helpers in `_lib.sh` cost about 2 ms. Rejected.
- Honouring the unlock in the kit repo: would leave the owner's own agent sessions able to self-approve. Rejected.
- Changing `check_artifact_chain.py`'s author check: it stays as the CI backstop for web-editor approvals.

## Consequences and residuals

- **Demotion passes.** The hook compares against the file's current values, so an agent can still move an
  approved artifact back to `in-review`; only the re-approval is refused. The demotion loses an approval that the
  chain check then reports. Accepted (spec C1).
- **The word rule is broad.** A Bash heredoc that writes a chain artifact and merely quotes the word `approved`
  in prose is refused; drafts go through Write/Edit (spec C2).
- **The Bash branch reads command text, so it can be obfuscated.** `F=appro; G=ve.py; python3 "scripts/$F$G" …`
  never contains the substring the `approve.py` rule looks for, and a draft can be written through a command the
  write-candidate parser does not recognise (a Python heredoc, say). The rule is a tripwire for the honest path,
  not a sandbox: `scripts/approve.py` itself refuses to run with `CLAUDECODE` set, an approved artifact refuses
  every Bash write regardless of wording, and CI's `check_artifact_chain.py` rejects an approval whose commit
  author is an agent identity or whose ledger entry is missing. Those are the backstops (PR #25 review).
- **Evals that run `approve.py` on purpose** (`approve-refuses-in-agent-session.yaml`) are executed by
  `scripts/run_evals.sh`, not by an agent's Bash call, so the normal path is unaffected; an agent typing the
  same line by hand is refused, which is the point (spec C3).
- **Web-editor approvals.** The owner's phone route (edit the three front-matter lines and append the ledger
  lines in the GitHub web editor, commit as themselves) is unaffected: the hook runs only inside agent sessions,
  and CI's chain check validates the approving commit's author and the ledger.
- Wiring is read at session start: a session that changed `.claude/settings.json` keeps the old hook set until
  restarted.
