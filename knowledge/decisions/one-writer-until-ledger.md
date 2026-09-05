---
type: decision
title: One writer per work item until the cost ledger exists
description: "Provisional answer to the implementer-versus-one-writer contradiction: subagents read, the lead writes; expires with the first cost_per_merged_pr reading or on 2027-03-05, whichever comes first."
tags: [agents, delegation, build, cost, decision]
timestamp: 2026-09-05T03:39:55Z
---

# One writer per work item until the cost ledger exists

## Context

Two spikes on `main` answered the same question in opposite ways. `docs/sdlc/spikes/prompt-surfaces.md` §2.6
(`status: accepted`, 2026-09-03) adds an `implementer` role: the lead hands over a whole plan step with its
acceptance test and gets back a diff plus the verifier's evidence. `docs/sdlc/spikes/build-stage-from-claude-agents.md`
§2 and §3.1 (`status: open`) say keep one writer per work item and delegate reads only, resting on the retired
`claude-agents` pilot: 37 runs in which role pipelines cost 2.2x to 4.8x a bare session and the reviewer gate
never blocked, and an E2 finding that delegation fails silently in 41.8% of deep-agent failures. Both name the
same arbiter, the Phase 2 cost ledger (`docs/sdlc/phase-2-roadmap.md` item 1), and neither can reach it because
the ledger does not exist. The contradiction was confirmed independently by the CI reviewer on PR #15 and became
`work/delegation-boundary`; the 2026-09-04 consensus (item 9) proposed the provisional answer recorded here.

## Decision

1. **One writer per work item.** The session that holds the approved `plan.md` makes every edit. Subagents are
   read-only: `.claude/agents/*` keep `tools: Read, Grep, Glob, Bash` and return evidence (paths, commands,
   outputs), never diffs (rule 8). `.gemini/agents/*` mirror them.
2. **Provisional, not final.** The answer stands because no measurement taken on this kit's own work supports the
   alternative, not because the alternative is wrong. The pilot's evidence bounds the decision (it is the only
   measurement anyone has) but was taken on small and medium Python bug fixes in another repository, the case
   its own routing wiki marks "ranking unknown, confidence low, zero local runs" for app-sized items.
3. **Scope.** The red-team pass (`docs/sdlc/spikes/red-team-pass.md`, a read-only adversarial reviewer at the spec
   gate) is a different question: build-stage §4 rejects a reviewer *inside the write pipeline*, measured weak
   for write tasks, while `/sdlc-review` already runs read-only reviewers. It is not decided here.

## Expiry and the measurement that flips it

This record expires on the first `cost_per_merged_pr` reading from roadmap item 1's ledger for this repository,
or on **2027-03-05**, whichever comes first. On expiry the question reopens with one measurement, not a debate:
over ten of this kit's own work items, a role pipeline with a writing `implementer` costs less than 1.5 times a
bare session and shows no silent-delegation failure (a diff the lead did not read before the PR). Until that
reading exists, the `implementer` role in `prompt-surfaces.md` §2.6 stays designed, not scheduled, and
`prompt-surfaces.md` Phase C's per-work-item token count in `log.md` is the stand-in measurement.

## Consequences

- **The hooks need no change, and were never the risk.** They read `tool_name`, `tool_input`, `cwd` and
  `session_id` from the tool-call payload and nothing about the caller, so a writing subagent would meet every
  gate the lead meets; `scripts/test_hooks_baseline.py` and `scripts/test_protect_approvals.py` pin that with a
  payload carrying subagent identity fields. What one writer protects is rule 2 checkability (one hand, one
  diff, one plan) and the silent-failure rate the pilot measured; a per-role record of who wrote what inside a
  work item does not exist, so a conditional answer ("a subagent may write when X") has no checkable X today.
- `/sdlc-build` (build-stage §3.1) can be written with "no implementation delegation" as a fact.
- `prompt-surfaces.md` §2.6 keeps its reasoning and gains an "overruled provisionally" line; build-stage §2 and
  §3.1 gain "confirmed provisionally" lines; roadmap item 1b and the rule fragments (`docs/sdlc/rules/40-claude-only.md`,
  `50-gemini-only.md`) point here. Nothing is deleted.
- A live subagent measurement was attempted in the session that wrote this record and refused by the session's
  permission classifier; the payload tests are the deterministic form of the same fact, and a live run stays a
  manual check the owner can make in an interactive session.

## Links

- this record: `knowledge/decisions/one-writer-until-ledger.md`
- `work/delegation-boundary/` (intent, spec, plan, ledger)
- `docs/sdlc/spikes/prompt-surfaces.md` §2.6
- `docs/sdlc/spikes/build-stage-from-claude-agents.md` §2, §3.1, §4
- `docs/sdlc/spikes/red-team-pass.md`
- `docs/sdlc/phase-2-roadmap.md` items 1 and 1b
- `docs/sdlc/handoff/consensus.md` item 9 (branch `claude/session-handoff`)
