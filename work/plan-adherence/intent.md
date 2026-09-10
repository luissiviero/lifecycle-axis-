---
type: sdlc/intent
id: plan-adherence
title: A plan executed in a new session is forgotten mid-run, and the agent deviates from it
description: "The plan is read once and summarised away at compaction, nothing in the repository re-surfaces it, and the plan's file-list contract is checked only when the pull request opens. This item keeps the plan in front of the agent for the whole session and refuses a deviation at the edit that makes it, with every check tested from a payload and no manual step."
stage: plan
# status: draft | in-review | approved | delegated | superseded
status: in-review
author: Luis Siviero (repo owner), who described the drift in the session of 2026-09-10; drafted by Claude from the owner's statements and an exploration of the hooks, the chain check, the templates and the agent directory
# approved-by: product owner; set only by a human, with scripts/approve.py from their own shell
approved-by:
approved-on:
# risk-class: low | medium | high; the grant below is valid only for classes the policy lists
risk-class: low
# mode: supervised | delegated; delegated-by and delegated-on are set only by a human, like approved-by
mode: supervised
delegated-by:
delegated-on:
# supersedes: previous intent id, if any
supersedes:
# record: legacy system id (Jira/ServiceNow) if that system holds a copy
record:
resource: https://claude.ai/code/session_01HYjaVLbPYzA1eb2hD388PX
tags: [plan-adherence, hooks, compaction, context-files, plan-template, evals, verbosity, one-writer]
timestamp: 2026-09-10T10:48:42Z
---
# Intent: a plan executed in a new session is forgotten mid-run, and the agent deviates

## Problem
In the owner's words, 2026-09-10:

> I commonly trace a plan and want it executed in a new session. In such session, the plan is read and
> executed. The problem though, is that it forgets that after a while, which makes it deviating from such
> plan. How would you enforce the agent to keep the plan at all times, making sure it doesn't deviate?

And on the second half of the same symptom:

> Is using caveman a good idea? If not, what to do to make it less verbose, and don't forget that mid-way?

Measured on 2026-09-10, on `main` at ca8dd32:

- The plan lives only in the conversation. Nothing in the repository re-surfaces it: `.claude/settings.json`
  declares `PreToolUse` (line 18), `PostToolUse` (line 41) and `Stop` (line 49) and no `SessionStart` or
  `UserPromptSubmit` hook. When the harness compacts the conversation, the summary keeps the gist and drops the
  file list and the step order, which is the moment the deviation starts. A fresh session only delays it.
- The plan gate checks a word, not a list. `.claude/hooks/require-plan.sh:21` reads the plan's `status` and
  `:35` blocks unless it is `approved` (or `delegated`, `:26`). Neither that hook nor `_lib.sh` reads
  `## Files that change`. The file-list contract of rule 2 is judged once, by
  `scripts/check_artifact_chain.py:855`, against `git diff <base>...HEAD` (`:544`), so a deviation is refused
  when the pull request opens, hours after the edit that made it.
- The end-of-turn hook does not look at the plan either: `.claude/hooks/stop-verify-reminder.sh:27` blocks
  only when code under `PLAN_REQUIRED_PATHS` changed since `scripts/verify.sh` last passed.
- Progress has no place on disk. `docs/sdlc/templates/plan.md:32-34` gives
  `## Order of work (each step independently verifiable)` two numbered blanks; nothing marks a step done, so a
  resumed session cannot tell where the previous one stopped except by re-deriving it from the diff. No script
  reads that section: `section()` in `check_artifact_chain.py:104-115` is called for `Files` and
  `Release-gated` only (`:850-851`) and collects `-` and `*` bullets, so numbered steps are invisible to it.
  Step quality varies by author: `work/run-queue/plan.md` carries files, the failing test first, the verify
  command and the expected count in every step; other plans carry a sentence.
- Subagent prompts have no shape. Of the four files in `.claude/agents/`, only `plan-reviewer.md:6` names its
  input ("the work item slug and a base ref"); the other three describe a task and leave the input to the
  caller. The owner's observation: "at times it seems like the task the agents receive isn't very structured."
- No context file carries an output-style rule: `grep -i "verbose\|terse\|concise\|preamble\|style"
  docs/sdlc/rules/*.md` returns nothing. Verbosity drifts with the register of a transcript full of long tool
  output, and a rule given in the first message decays with the rest of the conversation. The cap is
  `MAX_CONTEXT_LINES="120"` (`.sdlc/config.env:53`), counted over the whole render
  (`scripts/gen_context_files.py:199`); `CLAUDE.md` is at 108 lines, `GEMINI.md` at 117, and the adopter's
  render sits at the cap (`knowledge/lessons/adopter-context-file-sits-at-the-cap.md:22`).
- The hooks are testable without a session: `scripts/hooktest.py:107-132` runs a hook on a synthetic JSON
  payload, and every fixture under `scripts/fixtures/hook_inputs/` carries `hook_event_name`. No test today
  feeds a `SessionStart` or `UserPromptSubmit` payload, because no such hook exists.
- Gemini mirrors the hook set in `.gemini/settings.json` (`BeforeTool` at line 3, `AfterAgent` at line 22),
  wiring the same scripts under `.claude/hooks/`; there is no `.gemini/hooks/` directory.

The owner's decisions in the same session, each accepted as proposed: no compaction rule (a hook cannot
trigger compaction, so a rule can never be autonomous; make compaction harmless instead); no second pointer
file (`.sdlc/active` and `work/<slug>/plan.md` are the pointer and the plan); no output-style file (a
fragment adds, a style replaces part of the harness prompt); no caveman plugin (a persona bleeds into commits,
ledgers and review findings, and its extra cut measured inside run-to-run noise elsewhere); no subagent
writer per step (`knowledge/decisions/one-writer-until-ledger.md:25` stands until its own expiry); no per-step
plan files (a fourth artifact on every item; the fix is a fixed step shape inside `plan.md`); and "nothing
manual": every check this item adds is a hook with a payload test and an eval case.

## Proposed outcome
- The plan comes back after every compaction. A `SessionStart` hook with matcher `compact` prints the active
  item's `plan.md` (its `## Files that change` and `## Order of work (each step independently verifiable)`
  at least) as context. Observable: a hook test feeding `{"hook_event_name": "SessionStart", "source":
  "compact"}` with a fixture plan prints the plan's file list and steps and exits 0; with an empty
  `.sdlc/active`, or a pointer whose plan is missing, it prints nothing and exits 0. One eval case of
  `kind: hook` per branch.
- Every turn carries one line of progress. A `UserPromptSubmit` hook prints
  `[plan <slug>] <done>/<total> steps done; next: <step>` from the active plan's
  `## Order of work (each step independently verifiable)`, adding the step's files and verify command when the
  step has the shape below. Observable: a hook test asserts the exact line for a plan with three steps and one
  ticked; a plan in today's numbered shape yields `next: <first numbered step>`; an empty pointer yields
  nothing; and the line is one line under 200 characters for every `work/*/plan.md` in the repository.
- A deviation is refused at the edit, not at the pull request. A new hook beside `require-plan.sh`, on
  `Edit|Write|MultiEdit|NotebookEdit` and on Bash writes (through `bash_write_candidates`, `_lib.sh:366`),
  blocks a path outside the active plan's `## Files that change` with exit 2 and a reason naming the path and
  the fix (add it to the list with a deviation line first). `work/<slug>/plan.md` is always allowed, as is
  every prefix the chain check exempts (`check_artifact_chain.py:55`) and every write when no plan is open
  (the gate today). The allowed set is produced by a small helper under `scripts/` that imports `section()`
  from `check_artifact_chain.py`, so the hook and the pull-request check read the list through one function
  and can never disagree on a spelling; the locked script itself is not edited. Observable: four hook tests
  and four eval cases: an unlisted path is blocked; a path matching a listed glob passes; `plan.md` passes;
  the same unlisted path passes once the plan lists it. A fifth test asserts the helper and the chain check
  return the same allowed list for every `work/*/plan.md`.
- The end of a turn reports unplanned paths. `Stop` blocks the turn end, once, naming any changed path outside
  the plan, with the `stop_hook_active` loop guard `stop-verify-reminder.sh:6` uses. Observable: one hook test
  (a fixture plan, one unplanned path in `git status`, the block reason names it; a second call with
  `stop_hook_active: true` exits 0 silently), one eval case.
- A plan step has a fixed, tickable shape. The template's
  `## Order of work (each step independently verifiable)` becomes a checklist whose every step carries five
  fields: goal, files (a subset of the file list), acceptance test, verify command, done-when. Ticking a step
  is part of doing the step. Observable: the pin hook's parser is the test: a test module asserts it returns
  five named fields for every step of the template and at least one step for every existing `work/*/plan.md`
  unchanged; `grep -c "unticked" .claude/agents/plan-reviewer.md` is at least 1; `scripts/test_adopt.py`
  passes unchanged, since `_files_section` (`:355`) reads the file list and not the steps.
- Every subagent has a fixed input shape. Each file in `.claude/agents/` and `.gemini/agents/` opens with an
  `Input:` line naming what the caller must pass (slug, base ref, and for a step-scoped call the step number).
  Observable: `grep -L '^Input:' .claude/agents/*.md .gemini/agents/*.md` prints nothing; today it prints six
  of the eight files.
- The context files carry the style rule. Three to five lines in a rules fragment rendered into all three
  context files: outcome first, no preamble and no restating the request, at most one line of narration per
  tool call, no closing offers, artifact formats verbatim. Observable: `python3 scripts/gen_context_files.py
  --check` clean; every rendered file at or under `MAX_CONTEXT_LINES`; the adopter's render from
  `scripts/adopt.sh` into scratch not "over MAX_CONTEXT_LINES"; the lines present in `CLAUDE.md`, `GEMINI.md`
  and `AGENTS.md`.
- Gemini gets the same gates where it has the event: `.gemini/settings.json` wires the file-list guard under
  `BeforeTool` and the re-injection under its compaction or session-start event where one exists; an event
  Gemini lacks is recorded as a residual, not silently skipped. Observable: a test asserts that every script
  wired under `PreToolUse` in `.claude/settings.json` is wired under `BeforeTool` in `.gemini/settings.json`,
  and that every Claude hook event with no Gemini entry is named under `## Residuals` in the decision record.
- The decision and the runbook exist. `knowledge/decisions/plan-adherence.md` records why the plan is
  re-injected rather than remembered, why the guard duplicates CI's check at the edit, and why one writer
  stands; `knowledge/runbooks/` gains the session runbook line "compact at a step boundary when you can".
  Observable: `python3 scripts/check_okf.py` ends `0 warnings`.
- All green, with nothing manual: `scripts/verify.sh` `VERIFY: PASS`, `python3 scripts/check_artifact_chain.py
  --base origin/main --slug plan-adherence` `CHAIN: PASS`, `scripts/run_evals.sh` `0 fail` with at least ten
  new `kind: hook` cases, `python3 scripts/check_okf.py` `0 warnings`, and the adopter's render at or under
  the cap.

## Affected users and systems
- Users: the owner, whose traced plans are executed in fresh sessions; every session, local or cloud, on this
  repository; adopters of the kit, who receive the hooks, the template and the fragment through `adopt.sh`.
- Services / repos / data: `.claude/hooks/` (three new hooks: re-injection, pin, file-list guard; the `Stop`
  reminder extended; every one in `PROTECTED_PATHS`); `.claude/settings.json` and `.gemini/settings.json`
  (both protected); one new helper under `scripts/` that imports `section()` from `check_artifact_chain.py`
  (the locked script is not edited); `scripts/hooktest.py`, `scripts/test_hooks_baseline.py` and
  `scripts/fixtures/hook_inputs/` (payload tests; `scripts/` is in `PLAN_REQUIRED_PATHS`); `evals/cases/`
  (new `kind: hook` cases); `docs/sdlc/templates/plan.md`
  and `.claude/skills/sdlc-plan/SKILL.md` (the step shape); `.claude/agents/*.md` and `.gemini/agents/*.md`
  (the `Input:` line); one rules fragment under `docs/sdlc/rules/` and the three regenerated context files;
  `knowledge/decisions/`, `knowledge/runbooks/` and their indexes; `docs/sdlc/README.md`'s inventory.

## Constraints
- Must: every hook is silent (no output, exit 0) when `.sdlc/active` is empty, names an item with no `plan.md`,
  or names a plan that is not `approved` or `delegated`; the guard adds no new refusal to a session that has no
  open plan.
- Must: the guard's allowed set comes from `section()` in `check_artifact_chain.py`, imported by a helper,
  never a second spelling (`knowledge/lessons/one-path-spelling-in-guards.md`); `check_artifact_chain.py`
  itself is on the policy's `locked-paths` (`.sdlc/delegation.yaml:64`) and is not edited; every widening of
  the guard's input carries its own test.
- Must: hooks read only the payload fields the existing hooks read (`tool_name`, `tool_input`, `cwd`,
  `session_id`, `stop_hook_active`) plus the two the new events carry (`hook_event_name`, `source`), and the
  repository; nothing about the caller, so a subagent meets the same gate the lead meets
  (`knowledge/decisions/one-writer-until-ledger.md`, consequences).
- Must: new logic lives in new hook files; any `_lib.sh` change is minimal and tested from a second shell before
  it is committed (`knowledge/lessons/test-lib-changes-from-a-second-shell.md`).
- Must: every check this item adds is deterministic and runs from a payload test and a `kind: hook` eval; no
  acceptance step reads "run a session and look". The harness's own compaction is not triggered by a test and
  does not need to be: the `source: compact` payload is the test.
- Must: every rules-fragment line is paid for at the adopter's render, measured with `scripts/adopt.sh` into
  scratch before the pull request (`knowledge/lessons/adopter-context-file-sits-at-the-cap.md`); the cap is not
  raised and no fragment is exempted from the count, because a line excluded from the count is still read.
- Must: existing plans keep their shape and keep passing; the pin hook and the reviewer accept both the numbered
  and the checklist form.
- Must: land in the order re-injection and pin, then step shape and agents, then fragment, then the guard last.
  The guard is a new hook file beside `require-plan.sh`, which it does not edit; the `standing-grant` intent
  (pull request 61, not yet on `main`) names `require-plan.sh`, `_lib.sh` and `protect-approvals.sh` among
  its files, so any `_lib.sh` change here is kept to the minimum and the two items are not merged in the
  same week.
- Must not: add a second pointer file; add an output-style file or the `outputStyle` setting; install the
  caveman plugin or any persona; give any subagent a writing tool or hand a plan step to a subagent as a writer;
  add a per-step artifact under `work/<slug>/`; write a compaction rule; raise `MAX_CONTEXT_LINES`.
- Must not: edit `.sdlc/`, `.github/workflows/`, `scripts/verify.sh`, `scripts/run_tests.py`,
  `scripts/run_evals.sh` or `scripts/checks/`; change what any existing gate refuses beyond the new file-list
  check; write `approved`; skip, weaken or quarantine a test.
- Out of scope: everything a large application needs beyond one item at a time, carried to a follow-up intent:
  a `depends-on` key on the intent and its check in `scripts/next_item.py`; a living architecture record under
  `knowledge/` that `/sdlc-spec` reads; a fresh session per item started by the merge; the sizing rule (a plan
  of at most six steps, a step that fits one window). Also out of scope: the `implementer` role and the
  cost ledger that decides it; a `--append-system-prompt-file` launch habit (local only, no cloud equivalent);
  the PR-time chain check itself, which stays as the second line.

## Risk class
low — every new refusal fails closed and visibly (exit 2 with the path and the fix in the reason), and every
new injection is text the session already had at turn one. Nothing here touches an approval, a grant, a merge
condition or `.sdlc/`. Getting the guard wrong blocks edits until the hook is reverted, which is one file; getting
the re-injection wrong adds noise or adds nothing. The one real hazard is the lock-out a bad `_lib.sh` edit
causes, which the second-shell lesson covers. What makes this the owner's click regardless: `.claude/hooks/`,
`.claude/settings.json` and `.gemini/settings.json` are in `PROTECTED_PATHS`, so the pull request carries the
`control-plane-approved` label and merges by hand. The same value is in the `risk-class` key above.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: does the file-list guard judge every write, or only writes under `PLAN_REQUIRED_PATHS`? Proposed: every
  write the chain check would judge (everything outside its exempt prefixes), because rule 2 and
  `check_artifact_chain.py:855` already judge the whole diff, and a guard narrower than the check it mirrors
  refuses at the pull request what it allowed at the edit.
  A:
- Q: does the style fragment render into all three context files or into `CLAUDE.md` only? Proposed: all
  three (`targets: [claude, gemini, agents]`, as `30-conventions.md` does), since the verbosity the owner
  described is not model-specific. The cost is one fragment's lines in each render; `GEMINI.md` at 117 is
  the tight one and may need prose trimmed in `50-gemini-only.md`.
  A:
- Q: when Gemini has no compaction event, is the re-injection under its `SessionStart` alone acceptable?
  Proposed: yes, with the gap written in the decision record as a residual; `docs/sdlc/spikes/gemini-parity.md:37`
  lists `SessionStart` and `PreCompress`, and the spec confirms which fires after a compression.
  A:
- Q: one item or two? The guard is the only part that adds a refusal and the only part that shares files
  with the `standing-grant` intent on pull request 61. Proposed: one item, with the guard as the last step,
  so the owner's one click covers the whole change and the ordering constraint above keeps the two apart.
  A:
