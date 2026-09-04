---
type: doc
title: Consensus of the two playbook comparisons
description: Reconciliation of the earlier row-by-row page with the adversarial code analysis; merged fix list.
tags: [sdlc, handoff, playbook-comparison]
timestamp: 2026-09-04T22:13:39Z
---

# Consensus: the earlier row-by-row comparison and this session's adversarial analysis

Inputs: the artifact "lifecycle-axis against the Playbook" (48 rows, scorecard 14 added / 15 changed /
17 removed / 2 kept, nine hindsight verdicts) and `lifecycle-axis-vs-playbook.md` from this session.
Both are against `main` at `64bcb17`. The earlier page reads the decision records and judges the
*design*; this session ran the code and judges the *implementation*. Where they conflict, the rule
applied below is: a design verdict stands unless the code shows the mechanism does not do what the
design says, in which case the verdict becomes "right design, faulty implementation" with the fix named.

## 1. Where the earlier page needs revising (evidence from this session)

| Row | Earlier verdict | What the code shows | Consensus |
|---|---|---|---|
| 3, and "Keep as is" in Table 3 | Approval script, approvers file and ledger: "very high, the single most important addition; without it every other gate is theatre; nothing to change" | The refusal inside an agent session is `env -u CLAUDECODE` away; a `sed` on the front matter plus one ledger line passes `CHAIN: PASS`; the commit-author check only catches bot emails and a local agent commits under the owner's git config; no hook covers `work/` | **Keep the design; it is not yet a gate.** The reasoning is right: with one owner and an agent that can merge, "the merge is the approval" proves nothing. But today it is a record, not a lock. Two additions make it one locally: a hook that blocks any agent write changing `status:` or `approved-by:` in `work/*/*.md`, and a Bash-matcher rule for `approve.py` and `env -u CLAUDECODE`. Approvals made from the GitHub web editor (as the owner did for the phase-1 item) are the one path the author check can already distinguish; document that as the approval route. |
| 13, and "Keep" in Table 3 | Control-plane unlock: "honest about rule 3 being advisory here; the right trade; adopters do not inherit it" | The audit line goes to stderr on exit 0, which Claude Code never shows. The CI backstop matches only Bot authors or `claude/*` branches; the kit's PRs used `kit/*` and `spike/*`, so 11 of 13 control-plane PRs were never checked | **Keep the decision, fix the implementation.** The unlock is defensible for a self-hosting kit only if the audit trail it promises exists. Either emit the line as hook JSON output so it is displayed, or append it to a log file; and make `check_control_plane.sh` treat every PR from a session as agent-authored (branch prefix list from config, or presence of a `Co-Authored-By: Claude` trailer), or move the unlock to the launching shell as the playbook does with `RELEASE_APPROVAL`. Adopters do not inherit the unlock, but they do inherit an unprotected `.claude/settings.json`, which should join `PROTECTED_PATHS`. |
| 8 | `require-plan.sh` "blocks every plan-required path until plan.md is approved by a human" | It string-matches `status: approved` and never reads `approved-by`; `work/<slug>/plan.md` is editable by the agent; `SDLC_WORK_ITEM` can point at the approved umbrella plan | **Right design, one missing check.** Add the approver check to the hook (it already has the parser), and protect `work/*/plan.md` front matter as in row 3. |
| 17 (Kept) | Test lock during a fix: "kept as written; the cheapest honest guard" | Blocks *new* test files, so the playbook's failing-test-first flow is impossible; misses `rm`, `git rm`, `mv`, `perl -pi`; fails open on the template's own `kind: feature  # …` comment and on a CRLF plan | **Reclassify as Changed and faulty.** Lock only files that exist at hook time, treat delete and rename as writes, strip comments in the parser. |
| 34 (Kept) | Incident becomes an eval: "the one Maintain rule with teeth" | Nothing checks it: `incident.md` is not in the chain, the template has no `approved-by` though a role is assigned, and `TEST_FILE_GLOBS` includes `evals/cases/*`, so under a `kind: fix` item the mandatory eval is blocked by the very hook of row 17 | **Reclassify as Changed, on paper only.** Add `incident.md` to the chain with a required eval path; exempt new files under `evals/cases/` from the fix lock. |
| 24 | CI gate "blocks any bot-authored or `claude/*` PR touching protected paths" | Never fired on the kit's own PRs (see row 13); the exemption label is addable by the agent under the owner's `gh` login | **Downgrade to "a record more than a lock" for this repo too**, which the page already says for adopters. |
| 25 | Approval gate: "the authorization file is a human-written, agent-unwritable record"; "tested only by evals, never by use" | Any `approved-by:` line satisfies it, not checked against `approvers.yaml`; under the unlock the agent can write it, after which `kubectl apply` and `git push origin HEAD:main` pass unattended; no test covers the file route | **Right design, two missing checks.** Validate the handle against `approvers.yaml`; never lift the unlock for `release-authorizations/`; add the test. |
| 27 | CI/CD: "a scaffold around an echo; accept, mark as template" | `deploy.yml` sets `RELEASE_APPROVAL` from `github.sha` itself; `gh release create` and `gh workflow run deploy.yml` pass the hook and start a production run; `deploy.sh`'s "CI only" check is satisfied by exporting three variables; the generic `deploy`+`production` match was dropped so `make deploy ENV=production` is not gated | **Accept as scaffold, but fix the fail-open pieces before an adopter fills in the echo.** `RELEASE_APPROVAL` must come from a human act; restore the generic match; gate `gh release`, `gh workflow run` and `gh pr merge`. |
| 31 | Control bands: "14-day window contradicts documented 30; issues only; never fired in anger" | Also: σ=0 baseline returns no breach, which is what a healthy CI series looks like; baseline is the first N points, not rolling; PR series has no date filter; 3 of 4 Western Electric rules; duplicate issue per night | **Same verdict, larger fix list.** The detector cannot see the breach it exists for until σ=0 is handled. |
| 37 | Gate ledger: "works only because the chain check reads it" | True, and the kit stopped keeping it after day one: nine entries, none since 2026-09-02 23:00 across 22 merged PRs | **Agree, and note the kit is not keeping it.** The deviations log became the ledger; the chain check does not read that. |
| 42 | `adopt.sh`: "copies without overwriting, rewrites the adopter's config; high for the kit's purpose" | Verified install: `approve.py` referenced but not copied; the install commit fails the chain check with 70 errors; owner's handle in every role; an existing `settings.json` leaves all hooks silently inert; `VERIFY: PASS` on a TODO placeholder; plan gate open because `_example` ships approved | **Design fine, first-day path broken.** Ten fixes listed in the report's (c)10. |
| 1, 4, 10, 12 | All rated "high, and right" | Agree, with one addition each: the templates' inline comments break the chain check on a verbatim copy (row 1); `/sdlc-spec` never asks for flagged concerns or fills the provenance fields the template has (row 4); the umbrella plan makes rule 2 unfalsifiable, which the page already flags (row 10); skills are advisory and untested by any prompt eval (row 12). | No verdict change; implementation notes added. |

## 2. Where this session's report needs revising (the earlier page is right)

| This session said | Earlier page's point | Consensus |
|---|---|---|
| S1 / B3: the approval stack is "over-engineering that should not have changed"; "strictly weaker than the article's" | With one owner and an agent that merges, the article's own gate proves nothing; the article also assumes branch protection that does not exist on this plan | **Withdrawn as a should-not-have-changed.** It is the right replacement for the article's merge-as-approval. Keep it and make it a gate (Table 1, row 3). |
| B1: committing the unlock "should not have changed" | Running the kit's own hooks is better than the previous state (hooks off); the decision record is honest | **Downgraded to "faulty implementation".** The decision stands; the invisible audit line and the non-matching CI check are the defects. |
| B10: "half the repo serves consumers that do not exist"; suggested deleting Gemini and OKF | "Most additions exist because the playbook assumes a team and a platform admin that do not exist here"; Gemini is insurance; OKF should be kept but frozen | **Adopt the earlier framing.** Keep both, stop investing, and fix the two things that make the OKF check hollow today: 40 identical fabricated timestamps and the hand-maintained decisions index that is already stale. State in GEMINI.md that Antigravity ignores the hooks, which the Gemini-only fragment already does. |
| Verdict paragraph: "the kit is weaker than it says" | The kit rebuilt the control objectives for one owner on a free plan; most of it is correct in shape | **Both true.** The consensus wording: right shape, right decisions for the constraints, and a set of implementation gaps that the kit's own definition of done does not measure. |
| (c)14: "decide Gemini and OKF" as an open item | Already decided in the page: keep, downgrade, freeze | **Closed.** |

## 3. Items the earlier page raised that this session did not, now adopted

- **Risk class in the intent** (row 1): the one field the playbook lacks and "who approves" needs. Add to (a).
- **`.sdlc/` as the single control plane** (row 15): every gate reads the same path lists; scattering them would guarantee drift. Add to (a). Caveat from this session: `.claude/settings.json`, which wires the hooks, is outside it.
- **`superseded` hardened to the same checks as approval** (row 43), found by the CI reviewer on PR #20. Add to (a).
- **Security hardening from the bot reviewer paid for itself** (row 44): human-only switches, the two-job eval split, SHA pins, the workflow-permissions checker. Add to (a); this session credited the mechanisms without crediting where they came from.
- **Auto mode never cashed** (row 9): the payoff the playbook promises is auto-accept for routine work once guardrails hold. The kit has no guidance and, given Sections 1 and 2, the guardrails are not yet at the point where it is safe. Add to (c) as a goal that the fix list serves.
- **Headless spec pass is blocked by the kit's own policy** (row 6): `check_workflow_permissions.py` forbids `contents: write` everywhere, so a bot that opens a spec PR needs a scoped exception. This is the precise blocker; this session only said "not built".
- **Babysit-to-green and agent write steps in CI** (rows 22, 29) are deliberate trades of convenience for a smaller attack surface. Agree; medium, later, with a scoped token.
- **Two distribution routes** (row 42): the plugin cannot carry hooks, so `adopt.sh` is the real route and should be the documented one. Agree.
- **The implementer-versus-one-writer contradiction** (row 14, Table 3): adopt the provisional answer "one writer per work item until the cost ledger exists", with an expiry, so the `delegation-boundary` item can close. This session adds one input: the hooks match on tool calls, not identity, and Claude Code applies `PreToolUse` hooks to subagent calls, so a writing subagent is hook-equivalent to the lead; the real risk is rule 2 checkability and the silent-failure rate the retired pilot measured, not the gates. That supports the provisional one-writer answer.
- **OpenTelemetry export** (row 48): half the playbook's "where it is logged" cells assume it. This session's "log every hook decision to a file" is the free-plan stand-in and closes most of that gap.

## 4. Scorecard after reconciliation

The earlier scorecard (14 added, 15 changed, 17 removed, 2 kept) stands as a description of *what*
changed. One correction: the two "Kept" rows, the fix-time test lock and incident-becomes-an-eval, are
the two playbook rules this session found do not hold as written, so after reconciliation nothing in
the kit is "kept as written and working"; every play was changed, and the two that were meant to be
verbatim are the two with the least enforcement.

Merged hindsight list, in the order both analyses now agree on:

1. **Make the approval stack a gate** (hook on `work/*` status fields; Bash rule for `approve.py`;
   validate `approved-by` in the release gate). Best decision in the kit; currently a record.
2. **Fix the unlock's visibility and the CI match**, or move the unlock to the shell. Keep the decision.
3. **Protect the loop** (`settings.json`, `verify.sh`, `checks/`, `run_tests.py`; delete and rename as
   writes; existing-only test lock; incident evals exempt).
4. **Close the deploy fail-open** (`RELEASE_APPROVAL` from a human act; generic deploy match back;
   gate `gh release`, `gh workflow run`, `gh pr merge`). Keep the scaffold framing.
5. **Retire the umbrella plan**; per-change plans with named files. Both analyses; PR #22 started it.
6. **Fix the detector** (σ=0, rolling window, date filter, fourth rule, dedupe) before pointing it at
   a real metric.
7. **Fix the templates and the adopter's first hour** (comments off field lines; copy `approve.py`;
   install commit exempt; placeholder handle; merge or warn on existing `settings.json`; fail on the
   placeholder verify command; `_example` in review, not approved).
8. **Rename the evals' expectation** and add the first real-task cases, with a red path when the
   credential is missing. Both analyses.
9. **Decide delegation provisionally**: one writer until the ledger exists, with an expiry.
10. **Keep OKF and Gemini frozen**; fix the fabricated timestamps and the stale hand index; say in
    GEMINI.md that the hooks do not run under Antigravity.
11. **Reconcile the fifteen doc claims** in the report's B12 table with the code.
12. **Add `permissions.deny`/`allow`** as page 37 shows; not enterprise-only; the lines already exist in
    the example file.

Everything above is a recommendation; nothing was changed in the repo.
