---
type: sdlc/intent
id: delegation-boundary
title: Decide whether a subagent may ever write code in this kit
description: Two accepted-or-proposed spikes give opposite answers on delegating implementation; settle it before either is built.
stage: plan
status: approved
author: Luis Siviero (repo owner), drafted with Claude
approved-by: luissiviero
approved-on: 2026-09-05
supersedes:
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/15
tags: [agents, delegation, build, cost, spikes]
timestamp: 2026-09-03T20:00:00Z
---
# Intent: decide whether a subagent may ever write code in this kit

## Problem
Two spikes on `main` give opposite answers to the same question, and both are load-bearing for
work that is queued next.

- [`spikes/prompt-surfaces.md`](../../docs/sdlc/spikes/prompt-surfaces.md) §2.6 (`status: accepted`,
  accepted by the owner 2026-09-03) adds an **`implementer` role**: "the lead hands over a whole plan
  step with its acceptance test and gets back a diff plus the verifier's evidence", pinned to
  Sonnet 5 at high/xhigh effort. It is item 1b on the Phase 2 roadmap.
- [`spikes/build-stage-from-claude-agents.md`](../../docs/sdlc/spikes/build-stage-from-claude-agents.md)
  §2 and §3.1 (`status: open`) say the opposite: "Keep one writer per work item; delegate reads only",
  and the proposed `/sdlc-build` skill spells out "No implementation delegation: one writer per work
  item keeps rule 2 checkable."

The disagreement is about evidence, not taste. The build-stage position rests on measurements taken
in the retired `claude-agents` repo: a 37-run pilot in which role pipelines cost 2.2x to 4.8x a bare
session and the reviewer gate never blocked once, and an E2 finding that delegation fails silently in
41.8% of deep-agent failures. The prompt-surfaces position rests on the Claude platform model pages,
which say to delegate independent, verifiable units and never a handful of tool calls — and which
say nothing about a plan step specifically. Both documents name the same arbiter (the Phase 2 cost
ledger, roadmap item 1), and neither can reach it, because the ledger does not exist yet.

A second, smaller disagreement rides along: build-stage §4 lists "a separate reviewer agent" under
what not to bring, while [`spikes/red-team-pass.md`](../../docs/sdlc/spikes/red-team-pass.md)
proposes a forked adversarial reviewer at the spec gate. The stages differ and the pilot evidence is
scoped to small/medium Python bug fixes, so this one may resolve as "not the same claim".

Who is affected: every session that runs the kit, and every repo that adopts it. How we know: the
CI reviewer on PR #15 independently confirmed the contradiction and cited
`prompt-surfaces.md:210-219`.

## Proposed outcome
One written answer, in `knowledge/decisions/`, that both spikes then point at, so the question is not
re-litigated per session. Observable:

- `grep -rn "one writer per work item\|implementer" docs/sdlc/spikes/ knowledge/` returns text that
  agrees with itself.
- Whichever way it goes, the losing spike keeps its reasoning and gains a line saying it was
  overruled, by what, and on what date — nothing is deleted.
- If the answer is conditional ("a subagent may write when X"), X is checkable by a hook or by CI,
  not by a session's judgment. Rule 2 (the diff matches `plan.md`) must stay verifiable either way.
- The rule fragment that renders into `CLAUDE.md` / `GEMINI.md` states the answer in one sentence.

## Affected users and systems
- Users: the owner; every Claude Code and Gemini CLI session running this kit; future adopters.
- Services / repos / data: `docs/sdlc/spikes/prompt-surfaces.md`,
  `docs/sdlc/spikes/build-stage-from-claude-agents.md`, `docs/sdlc/spikes/red-team-pass.md`,
  `docs/sdlc/phase-2-roadmap.md` items 1 and 1b, `docs/sdlc/rules/`, `.claude/agents/`,
  `.sdlc/config.env` (the proposed `MODEL_*` / `EFFORT_*` pins), and the unbuilt `/sdlc-build` skill.

## Constraints
- Must: keep both spikes' evidence intact; state which measurement would change the answer.
- Must: leave rule 2 checkable — a diff that deviates from `plan.md` has to be catchable regardless
  of who typed it. The hooks match on tool calls, not on identity, which is an argument the
  prompt-surfaces spike already makes; test it rather than assume it.
- Must not: settle it by picking the more recent document, or by averaging the two into a hedge that
  neither spike's author would recognise.
- Must not: touch `.claude/agents/`, `.sdlc/` or `.claude/settings.json` in this work item — those are
  control plane (rule 3), and the pins are prompt-surfaces' Phase C, not this decision.
- Out of scope: building the cost ledger (roadmap item 1); building `/sdlc-build`; the model and
  effort pins themselves; the red-team pass.

## Risk class
low — the deliverable is a decision record plus doc edits. Blast radius is documentation and one
rule fragment. No data, no secrets, no deploy path. It gates two larger items, so being wrong is
cheap to reverse here and expensive to reverse after either is built.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: Can this be decided now, or does it wait on the Phase 2 cost ledger that both spikes name as
  the arbiter? A third option is a provisional answer with an explicit expiry ("one writer until the
  ledger exists").
  A: (proposed by the session on 2026-09-05; edit before approving) The third option. One writer per work
  item, subagents read-only, recorded in `knowledge/decisions/one-writer-until-ledger.md`. It expires when
  roadmap item 1's ledger produces its first `cost_per_merged_pr` reading for this repository, or on
  2027-03-05, whichever comes first; on expiry the question reopens with the measurement named in the
  record, not with a debate.
- Q: Does the 37-run pilot's evidence transfer? It measured small/medium Python bug fixes in another
  repo, and the `implementer` proposal is about app-sized work items — the exact case the pilot's own
  routing wiki marks "ranking unknown, confidence low, zero local runs".
  A: (proposed) No. It bounds the decision, because it is the only measurement anyone has, but it does not
  transfer to app-sized items; that is why the answer is provisional and names the measurement that would
  replace it (this kit's own work items, not another repo's bug fixes).
- Q: If a subagent may write, what makes the silent-delegation failure mode (41.8%) visible here —
  the verifier's evidence, the chain check, or something that does not exist yet?
  A: (proposed) Two of the three exist and one does not. The chain check keeps rule 2 checkable whoever
  typed the diff, and the hooks are identity-blind by construction: they read `tool_name`, `tool_input`,
  `cwd` and `session_id` from the tool-call payload and nothing else, so a subagent's Edit or Bash meets the
  same gates as the lead's (pinned by a test in this item). What does not exist is any record of who
  wrote what inside a work item, so the verifier's evidence contract (rule 8) is the only thing that would
  make a silent delegation failure visible, and it is advisory. A conditional answer ("a subagent may
  write when X") therefore has no checkable X today; hence one writer until the ledger, which is where
  that record would live.
- Q: Is the red-team-pass conflict the same question, or a separate one about read-only reviewers at
  the Design gate? If separate, it drops out of this work item.
  A: (proposed) Separate. Build-stage §4 rejects a reviewer *in the write pipeline* (measured weak for write
  tasks); the red-team pass is a read-only reviewer at the spec gate, which build-stage's own `/sdlc-review`
  already uses. It drops out of this item; the decision record says so in one line so it is not re-derived.
