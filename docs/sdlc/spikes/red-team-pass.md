---
type: spike
title: Adversarial red-team pass before spec approval
description: Evaluation of interview-me's 8-dimension red-team taxonomy as an opt-in phase in /sdlc-spec, with a recommended 4-dimension subset, evidence rules and risk-class gating.
tags: [spec, review, red-team, security, sdlc, design]
timestamp: 2026-09-03T00:00:00Z
status: open
---

# Spike - adversarial red-team pass in `/sdlc-spec`

**Status: open.** Nothing here is decided or implemented. This records what was found,
what is worth taking, and how it would be built if accepted. A `knowledge/decisions/`
record is written only if and when the owner accepts it.

## Where this came from

[`Sorbh/interview-me`](https://github.com/Sorbh/interview-me) - a Claude Code skill that
interviews the user like a senior architect and emits a spec. MIT licensed, single author
(Saurabh Kumar), v1.6.0, 45 stars / 4 forks at the time of reading, 13 commits between
2026-02-21 and 2026-07-26, all five issues opened by the author himself. Read at commit
`ad9e1a8` (`skills/interview-me/SKILL.md`, `VERIFY.md`, `STYLE_PRESETS.md`; ~1,180 lines
of pure Markdown, no executables).

Adoption is thin - this is not a battle-tested dependency and is not proposed as one. It
is a **source of ideas**, evaluated on its merits and re-derived to fit this chain. No
text is copied; if any were, MIT requires the notice to travel with it.

Separately: the practice of "have Claude interview you with `AskUserQuestion` and write a
spec before implementing" is publicised by Anthropic independently of this repo. The repo
is one person's elaboration of a generic idea, not the canonical implementation of it.

## What is worth taking

Two things, of which only the first is in scope for this spike:

1. **The red-team pass** (`SKILL.md` Phase 3) - after the interview and before the spec is
   written, a *separate* forked agent adversarially attacks the design across a fixed
   taxonomy, receives the full decision log so it can self-filter findings the user already
   answered, and emits structured findings with a `severity` and an `evidence` field.
2. **`--verify` drift detection** (`VERIFY.md`) - out of scope here; tracked separately.
   Worth noting because this chain has no equivalent and `docs/sdlc/phase-2-roadmap.md`
   is the natural home for it.

Three design properties of the pass are the actually valuable part, independent of the
taxonomy itself:

- **A different agent than the author.** This matches `security-standards` rule 8
  ("the agent that writes a change is not the one that approves it; reviewer subagents are
  read-only") and this repo's existing `explorer` / `security-reviewer` / `plan-reviewer`
  pattern. An author agent grading its own design is the failure mode the whole idea exists
  to fix.
- **Self-filtering against the decision log.** Findings that already have a recorded answer
  are dropped before the human sees them. Without this, every run re-raises settled points.
- **Structured findings, not prose.** `{dimension, severity, title, description, evidence,
  suggestedQuestion, suggestedOptions}`. Prose findings cannot be counted, capped, deduped
  across runs, or promoted under CLAUDE.md rule 7.

## The key structural fit

`docs/sdlc/templates/spec.md` already carries the destination:

```
## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: <concern> - policy: <skill/section> - contradiction? yes/no - owner: <name> - resolution:
```

**The output slot exists; the generator does not.** Today that section is filled by
whatever the spec author happened to notice. That is the gap this spike is about - it is
not a new concept being bolted on, it is a missing input to an existing structure.

## Gap analysis - the 8 dimensions vs this chain

| # | Dimension | Covered today by | Verdict |
|---|---|---|---|
| 1 | Failure modes | `spec.md` `### Failure modes and how they surface` - a fill-in prompt answered by the same agent that wrote the design | **Adopt.** The heading creates an illusion of coverage; self-report is not attack |
| 2 | Scaling cliffs | nothing | **Gate on risk class.** Near-zero value on a docs-and-scripts repo; high value for anything built with the kit |
| 3 | Security gaps | `security-standards` (8 rules) as Design constraints; `security-reviewer` subagent at `/sdlc-review`; `## Areas of concern` | **Adopt narrowly** - questions and concerns only at Design, verdicts stay at Review |
| 4 | Contradictory decisions | `## Decisions (ADR-style)` records them; `check_artifact_chain.py` validates chain and approval authorship, not semantic consistency - nothing checks D3 against D7 | **Adopt.** The failure a solo builder cannot self-detect, which is the kit's own premise |
| 5 | Operational concerns | partial and late: `security-standards` rule 6 (reversible migrations); `detect_bands.py` / `sdlc_metrics.py` / `/sdlc-incident` at Maintain | **Adopt.** A genuine chain break - see below |
| 6 | Data integrity | partial: rule 4 (classify new fields), `### Data and migrations`. Races and consistency: not covered | **Split and gate** - see below |
| 7 | Dependency risks | rule 5 covers *adding* a dep (state why, pin, no unknown post-install scripts). Vendor outage, deprecation, lock-in: not covered | **Do not adopt as a dimension** - extend rule 5 instead |
| 8 | Wildcard | nothing | **Adopt, capped at 1 and promotable** - see below |

### Why 5 (operational concerns) is a chain break, not just a gap

This repo has a full Maintain stage - `monitoring/bands.yaml`, `scripts/detect_bands.py`
(exit 3 = breach), `knowledge/metrics/*` with one definition per band - and `spec.md` never
declares **what band or signal a new feature should be watched on**. A feature is designed,
built, deployed and then discovered to be unmonitored. Closing this means one question at
Design: "which existing band covers this, or which new one does it need?" That is cheaper
than any of the other seven.

### Why 3 (security) is worth shifting left despite the duplication risk

CLAUDE.md rule 2: *"CI fails a PR whose diff touches files not listed in the plan."* A
security finding raised at `/sdlc-review`, after code exists, can invalidate the file list
in an **already-approved** `plan.md` - so the fix costs a code change *plus* a plan
amendment *plus* re-clearing a human gate. The same finding at Design costs a paragraph in
an unapproved document.

Also: `security-standards` rule 2 says *"every new endpoint states its authz rule in the
spec"* - a spec-time obligation with no spec-time checker. This would be that checker.

The cost is duplicate findings at Design and Review, which is noise and, worse, breeds
"we already looked at that" at the gate that has real code in front of it. Mitigated by
the scope rule: Design emits concerns, Review emits verdicts.

### Why 6 (data integrity) is split rather than adopted or dropped

The dimension bundles two unlike things:

- **Migrations and consistency** - cheap, checkable, and already anchored by
  `security-standards` rule 6. Adopt outright.
- **Race conditions** - the hallucination magnet. LLMs invent races in single-writer code.

Gate the races half on a design-surface trigger (concurrency, shared mutable state,
multi-writer paths, migrations) and impose one hard rule: **a race finding must name the
interleaving** - two concrete operations, an explicit order, and the resulting bad state.
No interleaving, no finding, dropped before the human sees it. A fabricated race cannot
produce a coherent interleaving, so the requirement filters mechanically rather than by
judgement. Same discipline as `VERIFY.md`'s "every finding carries a `file:line` or the
searches that came up empty".

### Why the wildcard stays

A taxonomy is a blind-spot generator: seven named dimensions find seven kinds of problem
forever, and the eighth becomes invisible *because* the list looks complete. The wildcard
is the only slot that can surface an unnamed failure mode.

Its real job is **intake, not per-run value**. CLAUDE.md rule 7 - *"a mistake made twice
becomes a line in this file or a skill"* - is already the promotion mechanism. Cap the
wildcard at one evidence-backed finding per run; when the same theme appears twice across
work items, rule 7 promotes it into a named dimension. The taxonomy then grows from this
repo's own failures instead of from someone else's list. Cost: one line in a prompt.

## Recommendation

**Adopt four dimensions as an opt-in step inside `/sdlc-spec`. Do not create a new skill.**

- Always: **contradictory decisions**, **operational concerns**, **failure modes**,
  **wildcard (cap 1)**.
- Risk class `medium` / `high` only: **scaling cliffs**, **data integrity** (migrations
  half always; races half only on the concurrency trigger).
- Never as a dimension: **security** stays a hard constraint plus `security-reviewer`;
  the pass may only raise security *questions*. **Dependency risks** become an extension
  of `security-standards` rule 5.

Risk class is already the right gate: `docs/sdlc/templates/intent.md` defines it as
`low | medium | high` justified by blast radius, data sensitivity and regulation, and it
already routes approval depth (`spec.md`: "tech lead consulted for medium/high risk").
Reusing it costs nothing and adds no new vocabulary.

## How it would be built

Roughly a 25-line addition to a 13-line skill, one agent file, one template line, one eval.
No change to the artifact chain, the hooks, CI, or `check_artifact_chain.py`.

1. **`.claude/skills/sdlc-spec/SKILL.md`** - new step between current 4 and 5:
   after the draft spec is assembled and before `status: in-review` is written, offer the
   pass via `AskUserQuestion`. Declining is recorded, not silent.
2. **`.claude/agents/red-teamer.md`** - a new read-only subagent, `tools: Read, Grep, Glob,
   Bash`, mirroring `security-reviewer`'s bounded shape. It receives the draft spec, the
   Decisions section, the `## Open questions carried from intent.md`, the risk class and the
   `explorer` brief from step 1. It never edits.
3. **Self-filter** - the agent drops any finding already answered in `## Decisions` or
   `## Not doing` before returning.
4. **Evidence rule** - every finding carries `file:line`, the searches that came up empty,
   or the literal token `design-only - no code yet`. The third value is a **debt marker**:
   `/sdlc-review` must re-check those specific claims against real code rather than treating
   them as closed. Findings with no evidence field are dropped by the skill, not shown.
5. **Output** - surviving findings become `C<n>` rows in the existing `## Areas of concern`
   table, each with its dimension and severity. Nothing else in the template changes.
6. **Cap** - critical and major are always shown; minor findings are batch-dismissable in
   one prompt. This keeps the spirit of CLAUDE.md rule 6's five-comment cap without
   silently discarding a critical finding.
7. **`docs/sdlc/templates/spec.md`** - one line in front matter, `red-team: run | skipped |
   n/a`, so a spec that never had the pass is distinguishable from one that passed it clean.
8. **Eval** - `evals/cases/red-team-flags-contradiction.yaml`: a fixture spec containing two
   decisions that contradict each other must produce at least one `C` row naming both. This
   is the one dimension whose success is deterministic enough to assert on.

## Costs and open questions

- **Token cost.** A second forked agent with codebase access on every spec, on top of the
  `explorer` pass `/sdlc-spec` already runs. Opt-in and risk-class gating are the controls.
- **Approver load.** Every surviving finding is a `C` row that `luissiviero` - sole holder
  of every role in `.sdlc/approvers.yaml` - must resolve before Build. This is the main
  reason to start with four dimensions rather than eight.
- **Two mechanisms, one job.** `interview-me`'s own `SKILL.md` warns against this in its
  resume logic: *"do not improvise a second drift mechanism; two divergent implementations
  of the same check will disagree."* Security findings must land in exactly one place.
- OPEN: does the pass run before or after the human sees the draft spec? Before means the
  owner reads one document; after means the owner can decline paying for a pass on a spec
  they already know is wrong. Leaning **before**, with the opt-in prompt as the escape.
- OPEN: should a `critical` finding block `status: in-review`? Against, on principle - the
  agent flags, the human decides, and nothing in this chain lets an agent hold a gate.
- OPEN: whether `red-team: skipped` should be visible in `scripts/sdlc_metrics.py` as a
  process metric. Probably yes, eventually; not in a first cut.

## Links

- [`Sorbh/interview-me`](https://github.com/Sorbh/interview-me) - MIT, the source of the idea
- `.claude/skills/sdlc-spec/SKILL.md` - where the step would go
- `.claude/skills/security-standards/SKILL.md` - rules 2, 4, 5, 6, 8 referenced above
- `.claude/agents/security-reviewer.md` - the shape `red-teamer.md` would copy
- `docs/sdlc/templates/spec.md` - `## Areas of concern`, the existing output slot
- `docs/sdlc/templates/intent.md` - risk class, the proposed gate
- `docs/sdlc/phase-2-roadmap.md` - where `--verify`-style spec drift detection belongs
- `knowledge/decisions/index.md` - where a decision record lands if this is accepted
