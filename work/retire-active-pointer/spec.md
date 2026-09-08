---
type: sdlc/spec
id: retire-active-pointer
title: A retired item is `superseded`, the pointer never names one, and the chain check says so in one line
description: "Reuse `status: superseded` as the retirement mark the gate already closes on, make the chain check fail a pointer that names a retired item and note one that names another item, check the base ref it diffs against, and document the retirement act; the one-tap retire is a follow-up item."
stage: design
status: delegated
reads: intent.md
approved-by: claude
approved-on: 2026-09-08
skills-applied: [security-standards]
skills-version: a398fad
prompt: "/sdlc-run retire-active-pointer -> /sdlc-spec, in session_014hU9gCLdAQNspXN6Hnh6Nj, from the approved and delegated intent and an explorer pass over check_artifact_chain.py, require-plan.sh, _lib.sh, approve.py, approve_dispatch.py, delegated_merge.py, gen_index.py and adopt.sh"
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/52
tags: [control-plane, active-pointer, plan-gate, chain-check, followup]
timestamp: 2026-09-08T15:00:00Z
---
# Spec: a retired item is `superseded`, the pointer never names one, and the chain check says so

## Requirements (each maps to an intent outcome)
| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | A retired item closes the plan gate: with `.sdlc/active` (or `SDLC_WORK_ITEM`) naming an item whose `plan.md` is `status: superseded`, an Edit under `PLAN_REQUIRED_PATHS` is refused. This is `require-plan.sh:35` as it stands; the requirement pins it so no later change reopens it. No hook is edited. | 1 (edit refused on a completed item) | `scripts/test_hooks_baseline.py::RequirePlanHook::test_blocks_when_plan_superseded` — exit 2, stderr names `superseded` |
| R-2 | The chain check fails, in one line, when `.sdlc/active` names a retired item: `work/<active>/intent.md` is `status: superseded`. The line names the item and the fix. It fires whatever `--slug` says, because the pointer is wrong for every pull request until it moves. | 2 (stale pointer reported in one clear line) | `scripts/test_check_artifact_chain.py::StalePointer::test_retired_active_item_is_one_clear_failure` — exit 1, exactly one `  FAIL:` line, containing `.sdlc/active names '<slug>', which is retired` |
| R-3 | The chain check notes, without failing, when `--slug` names one item and `.sdlc/active` names another: the merge script merges only the active item (`delegated_merge.py:329-330`), so the author should learn it here, not at merge. | 2 | `StalePointer::test_slug_differs_from_active_is_a_note` — exit 0, one `  note:` line containing `.sdlc/active names '<other>', not '<slug>'` |
| R-4 | The chain check verifies the base ref it diffs against. `git diff <base>...HEAD` failing is one `  FAIL:` line naming the ref and `--base HEAD`, never a silent in-progress mode. Today a missing ref yields an empty diff, `all([])` is true, and the check prints a note claiming the diff touches only this item (`check_artifact_chain.py:506-525`; reproduced in this session, see G-3). | 2 (one clear line, not a silent wrong answer) | `StalePointer::test_unknown_base_ref_is_one_clear_failure` — `--base no-such-ref` exits 1 with exactly one `  FAIL:` line naming `no-such-ref`; every existing case in the file still passes |
| R-5 | The act of retiring is written down where the tap routine is: `docs/sdlc/rules/00-chain.md` states that a human retires a completed item by setting `superseded` on its chain artifacts, logging the ledger lines, and clearing or moving `.sdlc/active`; `docs/sdlc/handoff/HANDOFF.md` carries the routine (web editor today, one tap as a follow-up). `CLAUDE.md`/`GEMINI.md`/`AGENTS.md` are regenerated. No skill is edited (`.claude/skills` is control-plane; G-9). | 3 (clearing available without a shell; the prose in the same pull request) | `scripts/checks/context-drift.sh` passes; `wc -l CLAUDE.md` ≤ 120; `grep -c superseded docs/sdlc/rules/00-chain.md` ≥ 1; `grep -c 'sdlc/active' docs/sdlc/handoff/HANDOFF.md` ≥ 2 |
| R-6 | The whole loop is green and nothing else moves: `scripts/verify.sh` ends `VERIFY: PASS`, the chain check ends `CHAIN: PASS`, `scripts/run_evals.sh` ends `0 fail`, `check_okf.py` ends `0 warnings`; every pre-existing case in `test_check_artifact_chain.py` and `test_hooks_baseline.py` passes unchanged. | 4 | the four last lines, pasted in the pull request; test counts before/after in the pull request |

## Design
### Architecture / data flow
Nothing new flows. Three readers of existing state change what they say:

1. **`require-plan.sh`** — unchanged. It already refuses any plan whose status is not `approved` (or a
   signed `delegated` plan under a live grant). `superseded` is therefore already a closed gate; R-1
   only pins that with a test so the property is named and cannot regress silently.
2. **`check_artifact_chain.py`** — three additions in `main()`, all before the chain loop:
   - after the slug is resolved, read `.sdlc/active` (already done at `:512`) and the front matter of
     `work/<active>/intent.md`; if its status is `superseded`, append the R-2 error;
   - if `a.slug` is given and differs from the pointer, append the R-3 note;
   - check `git diff`'s return code at `:506`; on failure print the R-4 line and exit 1 the way the
     empty-pointer case does at `:479-481`.
3. **The documents** — the retirement act, spelled once in the rules fragment and once in the handoff.

### Interfaces (APIs, events, schemas) — exact shapes
- R-2 line: `  FAIL: .sdlc/active names '<active>', which is retired (work/<active>/intent.md is superseded); clear .sdlc/active or point it at the item in progress`
- R-3 line: `  note: .sdlc/active names '<active>', not '<slug>': the merge script merges only the active item; point .sdlc/active at <slug> in this pull request, or expect the merge to be refused`
- R-4 line: `  FAIL: base ref '<base>' is not known here (git diff failed); pass --base HEAD for a local self-check, or fetch the ref` followed by `CHAIN: FAIL`, exit 1.
- The retirement act, as prose (R-5): set `status: superseded` on `intent.md`, `spec.md` and `plan.md`
  (and `incident.md` if present); append one ledger line per artifact, `approved -> superseded` (or
  `delegated -> superseded`), with the actor's handle; set `.sdlc/active` to the next item or to empty.
  `superseded` is human-only (`protect-approvals.sh:48`), so the act is the owner's in every mode.
- No new file, key, flag, status word or workflow input.

### Data and migrations
None. `.sdlc/active` keeps its shape (one slug, one line, blank allowed). No field is added to any
artifact. No personal or regulated data (security-standards §4: n/a).

### Failure modes and how they surface
- Pointer names a retired item → every pull request's chain check fails with the R-2 line until the
  pointer moves; the fix is a one-line edit of `.sdlc/active`, which an agent may make under the
  unlock with an audit line (G-5).
- Pointer names another item than the pull request's → R-3 note; nothing fails; the merge script's
  refusal is now foretold rather than discovered.
- Base ref absent → R-4 failure instead of a false "in-progress" pass. Locally, `VERIFY_CMDS` already
  passes `--base HEAD`, so `scripts/verify.sh` is unaffected; CI fetches with depth 0, so it is too.
- Item finished but never retired → unchanged from today and out of this item's reach (G-1): no local
  signal says "shipped". What this item does is make retirement a defined, documented act with a
  gate that provably closes on it, and a follow-up makes it one tap (D-4).

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: R-2 turns a retired-but-active pointer into a CI failure on unrelated pull requests — policy:
  none contradicts; it is the intent's own third open question answered "block" — contradiction? no —
  owner: luissiviero — resolution: accepted under the grant (D-3); the fix is one line.
- C2: `scripts/check_artifact_chain.py` is on the policy's `locked-paths`, so `delegated_merge.py`
  refuses this pull request and the owner merges by hand — policy: `.sdlc/delegation.yaml`
  `locked-paths` — contradiction? no, it is the policy working — owner: luissiviero — resolution: one
  merge click, stated in the pull request.
- C3: R-4 is not literally in the intent's outcomes; it is the same function, the same failure class
  (the check trusting an input it never verified), and the mechanism by which this session's own
  chain check audited the wrong item — policy: CLAUDE.md "do not widen the PR on your own" —
  contradiction? borderline — owner: luissiviero — resolution: included with its own test and named
  in the ledger; the reviewer may strike it, and the plan lists it as a separable step.

## Open questions carried from intent.md
- Q1 "what makes an item complete?" — answered by D-1: retired means `status: superseded` on the
  intent, a human act. The proposed "pull request merged" half is dropped: no artifact records it and
  no hook can ask (G-1, G-2).
- Q2 "who clears the pointer?" — the human who retires the item, as part of the same act (D-1, R-5);
  the merge cannot (G-4). One tap for it is the follow-up (D-4).
- Q3 "block or warn?" — the plan gate blocks (R-1, existing); the chain check fails on a retired
  pointer (R-2) and warns on a mismatched one (R-3) (D-3).

## Decisions (ADR-style: context → decision → consequences)
- D-1: **Retired is `status: superseded` on the intent.** Context: the repo already defines the word
  that way — `check_artifact_chain.py:573-577`: "it is what an approved artifact becomes when the
  item is retired, so a retired chain must stay checkable" — it is in `STATUSES` (`:51`), it is
  human-only (`protect-approvals.sh:48`), and one item has used it (`work/sdlc-kit-phase-1`).
  Decision: reuse it; add no word. Consequences: no hook changes, no new human-only enforcement, and
  the retirement act is one the owner has already performed once from the web editor.
- D-2: **The hook is not touched.** Context: `require-plan.sh:35` refuses every plan that is not
  `approved`, so a `superseded` plan is already refused; `.claude/hooks` is a protected path and
  `/sdlc-run` stops for those. Decision: pin the property with a test (R-1) instead of editing the
  hook. Consequences: the intent's first outcome is met by existing code, the run does not stop, and
  the pull request needs no `control-plane-approved` label.
- D-3: **A retired pointer is an error; a mismatched pointer is a note.** Context: the first is an
  inconsistency with no legitimate reading and a one-line fix; the second has a legitimate transient —
  a pull request that opens a new item before the pointer moves, which is exactly what pull request 52
  was. Decision: `errors` for R-2, `notes` for R-3. Consequences: pressure where it is unambiguous,
  information where it is not.
- D-4: **The one-tap retire is a follow-up item, not this one.** Context: it extends
  `.github/workflows/approve.yml`, a protected path, for which `/sdlc-run` must stop and ask; the
  owner's stated objective is a run that does not stop. Decision: document the web-editor act now
  (R-5), open the tap as its own intent. Consequences: retiring stays a phone-capable act today and
  becomes one tap later; this pull request touches no protected path.
- D-5: **R-4 is included.** Context: G-3 — the chain check's silent in-progress mode on a bad base ref
  was reproduced in this session and is the reason a bare local run audited `approve-by-dispatch`.
  Decision: four lines and a test in the function already being edited. Consequences: C3; a
  separable plan step the reviewer can strike.
- D-6: **`adopt.sh`'s `_example` seed is left alone.** Context: it opens the plan gate on an
  adopter's day one (G-6), but `work/adopter-first-hour` designed that first hour and this item's
  intent puts retroactive audits out of scope. Decision: not doing; named for a follow-up.

## Gotchas found while reading the codebase
- G-1: **No field records that an item's pull request merged.** `index.md`'s "Last gate" is a
  re-render of the last ledger line (`gen_index.py:181`); a merged item's reads `in-review`
  (`work/approval-gate/index.md`). `stage:` is a constant per file type. Merges appear only as prose
  in ledger notes (`work/delegated-mode/log.md:23`). The intent's proposed completion signal does not
  exist and cannot be read offline.
- G-2: **Hooks are offline and awk-only by design.** No hook uses `gh`, `curl`, a token or `git
  fetch`; none references `origin/main`; `_lib.sh:105-106` forbids python in hooks. Anything a hook
  decides must be decidable from the working tree.
- G-3: **`check_artifact_chain.py:506` never checks `git diff`'s return code.** A missing base ref
  gives an empty `changed_all`, `all([])` is `True`, and the check prints a note claiming the diff
  touches only this item. Reproduced here on 2026-09-07 with uncommitted work: the check audited the
  pointer's item and passed. The nearest pattern in the same file does check it (`:243-247`).
- G-4: **`delegated_merge.py` has no write-back.** After the merge API call it deletes the head branch
  and comments (`:847-869`); it never commits. The moment an item finishes leaves the pointer as found.
- G-5: **`.sdlc/active` is protected but not never-unlock.** `protect-paths.sh:38-41` lists
  `approvers.yaml`, `delegation.yaml`, `release-authorizations`, `hook-decisions.log`; the pointer is
  absent, so with `SDLC_CONTROL_PLANE_UNLOCK=1` (`.claude/settings.json:3`) an agent's write passes
  with an audit line. `HANDOFF.md:150-151` already relies on it.
- G-6: **`adopt.sh:403-409` seeds `_example`, whose plan is approved.** The day-one open gate, already
  written down at `docs/sdlc/handoff/lifecycle-axis-vs-playbook.md:272-273`.
- G-7: **Every grant tap repoints the pointer** (`approve.yml:117`, `--activate`). One item is active
  at a time; pre-granting several intents leaves the last tap's item active. A run queue is a feature
  this repo does not have, and the one that turns one tap into hours of unattended work.
- G-8: **`approve_dispatch.py:73` already allowlists `.sdlc/active`** in a dispatch commit, so a future
  retire route needs no allowlist change.
- G-9: **`.claude/skills` is control-plane** — pull request 51 needed the label for it. The skills'
  end-of-run prose is left as is; R-5 lives in `docs/` only.
- G-10: **The Bash guard reads prose.** `protect-approvals.sh` refused a heredoc that merely
  *described* another item's signed plan; a file whose text mentions the protected words is written
  with the Write tool, not a shell redirect.

## Security standards, applied
§1 secrets: n/a, none touched. §2 auth: n/a, no endpoint. §3 input: the slug read from `.sdlc/active`
is used only for a path under `work/` and a message; `SLUG_RE` (`approve_dispatch.py`) is the existing
boundary and is not widened. §4 data: none. §5 dependencies: none. §6 infra: no release-gated path.
§7 logging: the chain check's lines carry no personal data. §8 hygiene: the writer of this spec does
not approve it; it is signed under the grant, and the review runs on a different model.

## Not doing
- The one-tap retire route in `approve.yml` — follow-up item (D-4).
- Editing `require-plan.sh` or any hook — unnecessary (D-2) and a protected path.
- Changing `adopt.sh`'s `_example` seed — follow-up (D-6).
- Retiring `approve-by-dispatch` retroactively — out of scope by the intent; the owner may apply R-5's
  act to it in the web editor at any time. The pointer already moved off it.
- A run queue — the next intent, not this one (G-7).
- Detecting "finished but not retired" — no local signal exists (G-1); the design makes retirement a
  defined act instead.
