---
type: sdlc/spec
id: delegation-boundary
title: Decide whether a subagent may ever write code in this kit
description: "Requirements and design for the provisional answer: one writer per work item, subagents read-only, with an expiry and a named measurement, written once in knowledge/decisions and pointed at by both spikes, the roadmap and the rule fragments."
stage: design
status: in-review
reads: intent.md
approved-by:
approved-on:
skills-applied: [security-standards]
skills-version: 60ab0f5
prompt: "Drafted from the owner's intent (four open questions answered provisionally by the session, marked for the owner to edit), the approved 2026-09-04 implementation plan section WI-10, consensus item 9, and a survey of what the hooks read from the tool-call payload; reviewed by the orchestrator."
record:
resource: https://claude.ai/code/session_01Te8oN2GdvRupSixH4kjR8Y
tags: [agents, delegation, build, cost, spikes, decision, consensus-item-9]
timestamp: 2026-09-05T03:39:55Z
---
# Spec: decide whether a subagent may ever write code in this kit

## Requirements (each maps to an intent outcome)
Intent outcomes: (1) one written answer in `knowledge/decisions/` that both spikes point at; (2) the losing spike
keeps its reasoning and gains an overruled line; (3) any condition is checkable by a hook or CI, and rule 2 stays
verifiable; (4) the rule fragments state the answer in one sentence.

| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | `knowledge/decisions/one-writer-until-ledger.md` exists (`type: decision`) with sections Context, Decision, Expiry and the measurement that flips it, Consequences, Links; the Decision states: one writer per work item; subagents read-only (`.claude/agents/*` keep `tools:` without Edit/Write); the answer is provisional | 1 | `python3 scripts/check_okf.py` ends `0 warnings`; `grep -c '^## ' knowledge/decisions/one-writer-until-ledger.md` prints `5`; `grep -q 'one writer per work item' knowledge/decisions/one-writer-until-ledger.md` |
| R-2 | `docs/sdlc/spikes/prompt-surfaces.md` §2.6 gains one line: overruled provisionally by the decision, on 2026-09-05, until its expiry; `docs/sdlc/spikes/build-stage-from-claude-agents.md` §2 (the E2 row) and §3.1 gain one line each: confirmed provisionally by the decision, on 2026-09-05; nothing else in either spike changes | 2 | `git diff origin/main -- docs/sdlc/spikes/ | grep -c '^-[^-]'` prints `0` (additions only); `grep -c 'one-writer-until-ledger' docs/sdlc/spikes/prompt-surfaces.md docs/sdlc/spikes/build-stage-from-claude-agents.md` prints `1` and `2` |
| R-3 | `docs/sdlc/phase-2-roadmap.md` item 1b gains one sentence: the `implementer` role of §2.6 is provisionally overruled by the decision until item 1's ledger exists | 1 | `grep -c 'one-writer-until-ledger' docs/sdlc/phase-2-roadmap.md` prints `1` |
| R-4 | `docs/sdlc/rules/40-claude-only.md` and `docs/sdlc/rules/50-gemini-only.md` each gain one sentence stating the answer and naming the record; `CLAUDE.md` and `GEMINI.md` are regenerated and stay under `MAX_CONTEXT_LINES` (120); `AGENTS.md` is byte-identical | 4 | `grep -c 'one writer per work item' CLAUDE.md GEMINI.md` prints `1` each; `scripts/checks/context-drift.sh` passes; `wc -l < CLAUDE.md` ≤ 120 |
| R-5 | `knowledge/decisions/index.md` lists the new record and the missing `adopt-script.md` entry | 1 | `grep -c 'one-writer-until-ledger.md\|adopt-script.md' knowledge/decisions/index.md` prints `2` |
| R-6 | The intent's own oracle agrees with itself: every file under `docs/sdlc/spikes/` and `knowledge/` that matches `one writer per work item` or `implementer` also names `one-writer-until-ledger` | 1 | `for f in $(grep -rlE 'one writer per work item\|implementer' docs/sdlc/spikes/ knowledge/); do grep -q one-writer-until-ledger "$f" \|\| echo "$f"; done` prints nothing |
| R-7 | Hook identity-blindness is tested, not assumed: a `PreToolUse` payload that also carries `agent_name`, `subagent_type` and `parent_tool_use_id` fields gets the same verdict from `protect-paths.sh` (Edit on `.sdlc/x`: block) and `protect-approvals.sh` (Edit setting `status: approved`: block) as the payload without them | 3 | `scripts/test_hooks_baseline.py::ProtectPathsHook::test_verdict_ignores_caller_identity_fields`, `::ProtectApprovalsHook::test_verdict_ignores_caller_identity_fields` |
| R-8 | Whole suite green | 1-4 | `scripts/verify.sh` ends `VERIFY: PASS (<sha>)`; `scripts/run_evals.sh` ends `EVALS: N pass, 0 fail, N skipped`; `python3 scripts/check_artifact_chain.py --base origin/main --slug delegation-boundary` ends `CHAIN: PASS` |

## Design
### Architecture / data flow
A decision record, four annotation lines, two rule sentences, one index edit, one test. No code path changes.
The record is the single place the answer lives; every other edit is a pointer to it.

### Interfaces (APIs, events, schemas) — exact shapes
`knowledge/decisions/one-writer-until-ledger.md`:
```
---
type: decision
title: One writer per work item until the cost ledger exists
description: "Provisional answer to the implementer-versus-one-writer contradiction: subagents read, the lead writes; expires with the first cost_per_merged_pr reading or on 2027-03-05."
tags: [agents, delegation, build, cost, decision]
timestamp: 2026-09-05T03:39:55Z
---
# One writer per work item until the cost ledger exists

## Context
(the two spikes, their evidence, the arbiter neither can reach; consensus item 9)
## Decision
1. One writer per work item: the session that holds the plan makes every edit; subagents are read-only
   (`.claude/agents/*` keep `tools: Read, Grep, Glob, Bash` and return evidence, rule 8).
2. Provisional: it stands because no measurement on this kit's own work supports the alternative, not
   because the alternative is wrong.
3. Scope: the red-team pass (a read-only reviewer at the spec gate) is a different question and is not
   decided here.
## Expiry and the measurement that flips it
Expires on the first `cost_per_merged_pr` reading from roadmap item 1's ledger for this repository, or on
2027-03-05, whichever comes first. The question reopens with one measurement: over ten of this kit's own
work items, a role pipeline with a writing `implementer` costs less than 1.5 times a bare session and shows
no silent-delegation failure (a diff the lead did not read before the PR). Until that reading exists, the
`implementer` role in `prompt-surfaces.md` §2.6 stays designed, not scheduled.
## Consequences
- The hooks need no change: they read `tool_name`, `tool_input`, `cwd` and `session_id` and nothing about
  the caller, so a writing subagent would meet every gate the lead meets (test: R-7). The gates were never
  the risk; rule 2 checkability and the pilot's silent-failure rate are.
- `/sdlc-build` (build-stage §3.1) can be written with "no implementation delegation" as a fact, not a debate.
- `prompt-surfaces.md` Phase C's per-work-item token count in `log.md` is the stand-in measurement until
  the ledger exists.
## Links
(both spikes, the roadmap item, the intent, consensus item 9)
```
The annotation lines (verbatim):
- `prompt-surfaces.md`, end of the §2.6 opening paragraph: `> **Overruled provisionally** by
  [`knowledge/decisions/one-writer-until-ledger.md`](../../knowledge/decisions/one-writer-until-ledger.md)
  on 2026-09-05: the `implementer` role stays designed, not scheduled, until that record expires.`
- `build-stage-from-claude-agents.md`, after the §2 table and at the end of the §3.1 "No implementation
  delegation" paragraph: `> **Confirmed provisionally** by [`knowledge/decisions/one-writer-until-ledger.md`]
  (../../knowledge/decisions/one-writer-until-ledger.md) on 2026-09-05, with an expiry and a named
  measurement.`
- `phase-2-roadmap.md` item 1b, after "Becomes work item `prompt-surfaces` when scheduled.": `Its
  `implementer` role is provisionally overruled by
  [`knowledge/decisions/one-writer-until-ledger.md`](../knowledge/decisions/one-writer-until-ledger.md)
  until item 1's ledger exists.`
- `40-claude-only.md`, appended to the subagents bullet: `One writer per work item: subagents read and
  return evidence, the session holding the plan makes every edit (`knowledge/decisions/one-writer-until-
  ledger.md`, provisional, with an expiry).` `50-gemini-only.md`: the same sentence appended to its
  subagents bullet.

`scripts/test_hooks_baseline.py` gains, in the two named classes, a test that runs the hook twice with the
same `tool_input` and asserts equal exit codes and equal stdout, the second payload carrying
`"agent_name": "implementer", "subagent_type": "implementer", "parent_tool_use_id": "toolu_01"` at the top
level (the shape Claude Code's subagent tool calls carry).

### Data and migrations
None.

### Failure modes and how they surface
- A future edit to a spike that contradicts the record: R-6's oracle (also the intent's) prints the file.
- The record expires unnoticed: the expiry date is in the record and in the roadmap item; `docs-reconcile`
  and each `/sdlc-review` Memory pass read `knowledge/decisions/`.
- A hook that starts reading identity: R-7 fails.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: the four answers in `intent.md` are the session's proposals, marked as such — policy: the intent is the originator's — contradiction? no — owner: luissiviero — resolution: the owner edits any answer before approving; the spec and record follow the intent as approved (the plan's step 1 re-reads them).
- C2: the live measurement the intent asked for ("test it rather than assume it") was attempted as a subagent run in this session and refused by the session's permission classifier; the spec rests hook-equivalence on what the hooks read (surveyed: four payload fields, no caller identity) and pins it with R-7 — policy: evidence over assumption — contradiction? no — owner: luissiviero — resolution: R-7 is a deterministic test of the same fact; a live subagent run stays a manual check the owner can do in an interactive session.
- C3: the expiry date and the 1.5x threshold are the session's numbers — policy: the record must name the measurement — contradiction? no — owner: luissiviero — resolution: proposed in the intent's answer 1; the owner edits them there.

## Open questions carried from intent.md
- The four answers as proposed (each marked "(proposed)" in `intent.md`).

## Decisions (ADR-style: context → decision → consequences)
- D1: One record, many pointers: the intent's outcome is a single answer nobody re-litigates → every other edit is a one-line link, so the spikes keep their reasoning intact (R-2 admits additions only).
- D2: Provisional with an expiry and a named measurement, not a verdict: the only evidence is another repo's pilot, and both spikes name the same absent arbiter → the record says exactly what reading reopens it.
- D3: Identity-blindness pinned by a payload test rather than a live subagent: the hooks are scripts fed JSON; adding the subagent fields to a payload is the same input the hook would see → a stable test in the existing hook module.
- D4: Both rule fragments (40 and 50), not only 40 as the 2026-09-04 plan listed: the intent's outcome names `CLAUDE.md` / `GEMINI.md` and `40-claude-only` renders into `CLAUDE.md` alone → one sentence in each, `AGENTS.md` unchanged.

## Gotchas found while reading the codebase
- `work/delegation-boundary/log.md:13` records the draft with sha `(pending)`; `log_ledger.py` reads the sha column as text, so the line parses; it is left as history.
- `.claude/agents/*.md` all carry `tools: Read, Grep, Glob, Bash`; `.gemini/agents/*.md` have an empty `tools:` line (read-only mirrors). No agent has Edit or Write today, so the decision changes no file under `.claude/agents/` (rule 3 kept).
- `prompt-surfaces.md` is `status: accepted`; `build-stage-from-claude-agents.md` is `status: open`. Neither status changes: the record overrules one section, not the spike.
- `docs/sdlc/rules/40-claude-only.md` renders into `CLAUDE.md` only (`targets: [claude]`); the Gemini sentence needs `50-gemini-only.md`.
- `knowledge/decisions/index.md` is hand-kept ("regenerate links when new decisions land") and lacks `adopt-script.md`; the 2026-09-04 plan already noted it.
- `CLAUDE.md` is at 79 lines; one more rendered line stays far under 120.

## Not doing
- The cost ledger, `/sdlc-build`, the model and effort pins, `.claude/agents/` edits, the red-team pass.
- Any change to the hooks.
