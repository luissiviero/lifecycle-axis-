---
type: sdlc/spec
id: session-chaining
title: "A session owns one work item, leaves its state in git, and schedules its successor"
description: "Names the one-session-per-work-item protocol in the handoff and in sdlc-run, makes the finishing session schedule the next one where its runtime can and say so where it cannot, and fixes three places where kit documentation instructs an act the repository's own checks refuse."
stage: design
# status: draft | in-review | approved | delegated | superseded
status: approved
reads: intent.md
# approved-by: product owner; tech lead consulted for medium/high risk; set only by a human
approved-by: luissiviero
approved-on: 2026-09-13
# skills-applied: skills loaded as hard constraints while writing this spec
skills-applied: [security-standards]
skills-version: 29535f3
prompt: work/session-chaining/intent.md plus the owner's three answers of 2026-09-13 (a real mechanism; fold in pointer-contradiction; one rendered rules line), and a read-only scout over the repository's existing agent-from-CI precedents, adopt.sh surface and autonomy decisions
record:
resource: knowledge/decisions/run-queue.md
tags: [sdlc, skills, handoff, context, session, protocol]
timestamp: 2026-09-13T20:45:00Z
---
# Spec: A session owns one work item, leaves its state in git, and schedules its successor

## Requirements (each maps to an intent outcome)
| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|---|---|---|
| R1 | `docs/sdlc/handoff/HANDOFF.md` gains a `## Session protocol` section stating the three invariants: a session owns exactly **one** work item; everything durable is in git (`.sdlc/active`, `work/<slug>/log.md`, this handoff), so the session is disposable; the session that finishes an item is the one that starts the next. | "A named session protocol exists in HANDOFF.md and in sdlc-run" | new `evals/cases/session-protocol-is-written-down.yaml` greps `^## Session protocol` in HANDOFF.md and the three invariant keywords; fails against `main` today |
| R2 | `sdlc-run` step 7 gains the chaining act as its **last** step, in this order: (a) confirm `.sdlc/active` on `main` names the next item, (b) refresh the handoff's `## Task state` and its seed prompt for that item, (c) commit and push those, (d) **only then** schedule a successor session with the seed prompt, (e) end. The order is the requirement: the durable state is correct before anything is scheduled, so a failure at (d) costs nothing. **At most one successor per finish, and never as a successor's own first act** — this account has already exhausted its Actions minutes once (`work/ci-budget/intent.md`), and an unbounded chain is the way to do it again. | "stated as a mechanism with a trigger, not as advice" | the same eval case greps `sdlc-run/SKILL.md` for the ordered act, for `schedule`, and for the at-most-once cap; `scripts/run_evals.sh --only session-protocol-is-written-down` |
| R3 | The seed prompt stops being a "Suggested first prompt" and becomes the contract the chaining act sends: `HANDOFF.md`'s prompt section is renamed and states that it is refreshed by the finishing session and read by the next one. It must be standalone — a fresh session has no conversation. | "what starts the next one" | eval case greps the renamed heading and the words `standalone` and `refreshed`; `grep -c "Suggested first prompt" docs/sdlc/handoff/HANDOFF.md` = 0 |
| R4 | The runtime dependency is stated, not hidden: `sdlc-run` says the scheduling step uses whatever the session's runtime provides (a scheduled routine, a session API), and that **a runtime with no such capability skips (d) and says so in its final message**, leaving (a)–(c) done. No kit code calls any vendor API. | intent "Must not: widen what an agent may do"; the kit's model-neutral position (`docs/sdlc/README.md:126-131`) | eval case asserts the fallback sentence is present in `sdlc-run/SKILL.md` (absent today) |
| R5 | `.claude/skills/sdlc-review/SKILL.md:20` stops telling the agent to edit `CLAUDE.md`. The lesson convention is a file in `knowledge/lessons/` plus a pointer line in `docs/sdlc/rules/60-lessons.md`, which is what rule 7 actually means. | intent defect 3a | eval case: `grep -c 'CLAUDE.md "Lessons learned"' .claude/skills/sdlc-review/SKILL.md` = 0 and `knowledge/lessons/` is named instead |
| R6 | `.claude/skills/sdlc-intent/SKILL.md` names `work/<slug>/log.md` and `python3 scripts/gen_index.py` in its steps, so an item created by following it literally has a ledger and a clean index. | intent defect 3b, and "Following /sdlc-intent literally … produces an item with a log.md" | eval case greps both strings (0 occurrences today); `python3 scripts/gen_index.py --check` clean after a dry item |
| R7 | **(folded from `pointer-contradiction`)** **Both** instances in `HANDOFF.md` are corrected, not just the one the mock walk found: `:37` "then the session sets `.sdlc/active`" and `:194` "the session sets it after merging `main` into the…", which says the same wrong thing in different words. `.sdlc` is in `PROTECTED_PATHS` (`.sdlc/config.env`), so `protect-paths.sh` blocks that write; `sdlc-run`'s Never list already says "write `.sdlc/active` yourself — the merge workflow moves it" (`SKILL.md:71`); `scripts/delegated_merge.py`'s `advance()` is what moves it. | not in the intent's outcomes — folded in on the owner's 2026-09-13 answer, same defect class as R5 in a file R1 rewrites | eval case: `grep -cE "session sets" docs/sdlc/handoff/HANDOFF.md` = 0 (it is 2 today, at `:37` and `:194`), which catches any re-wording rather than one exact phrase |
| R8 | One rendered line in `docs/sdlc/rules/` points at the handoff: `CLAUDE.md` names `.sdlc/active` once (`:15`) and never mentions `HANDOFF.md`, so a session started without a seed prompt cannot discover the protocol. The line **points**, it does not restate. Paid for by re-flowing prose in the same or another fragment; no rule dropped. | intent "possibly docs/sdlc/rules/ if the protocol earns a rendered line" (`## Affected users and systems`) | **the discriminating check is the adopter's *rendered* file, not the repo's**: after `bash scripts/adopt.sh "$SCRATCH/a" && python3 scripts/gen_context_files.py --root "$SCRATCH/a"`, `grep -c HANDOFF "$SCRATCH/a/CLAUDE.md"` = 1 — it is **0** today. `grep -c HANDOFF CLAUDE.md GEMINI.md AGENTS.md` = 1 each. `wc -l "$SCRATCH/a/CLAUDE.md"` ≤ 120 is a **ceiling, not proof**: it already prints 120 on an unchanged tree, so it can never show the line landed. `scripts/checks/context-drift.sh` passes |
| R9 | Crucial, byte-for-byte: no change to `scripts/`, `.github/workflows/`, `.sdlc/`, `.claude/hooks/`, `.gemini/`, or any `PROTECTED_PATHS` entry. This item is instructions and documentation only. | intent `## Constraints`, "Must not: widen what an agent may do" | `git diff origin/main --name-only` matches none of those prefixes |
| R10 | **The seed prompt is context, never authority.** `sdlc-run`'s chaining act states that the prompt carries *where to look* — the handoff, `.sdlc/active`, the item — and that the successor re-reads the item's own approved artifacts before acting. Nothing a prompt says can widen what the successor may do; the hooks and the chain check are unchanged by it. Defence in depth for C5, and true whatever the lock state. | intent "Must not: widen what an agent may do" | eval case greps `sdlc-run/SKILL.md` for the "context, not authority" clause and for the re-read instruction (both absent today) |

## Design
### Architecture / data flow
The kit cannot start a session; only a runtime can. So the mechanism is split:

- **The kit owns the contract.** The seed prompt (R3) is committed to git and refreshed by the
  finishing session as part of its ordered last act (R2). That makes the successor's instructions
  auditable *before* it runs — the owner can read in the repository exactly what the next session
  will be told.
- **The runtime owns the trigger.** Step (d) calls whatever the session's own runtime provides. This
  session's runtime, for example, can schedule a routine that opens a fresh session with a standalone
  prompt; that route has been exercised twice while executing `ci-budget`. Another runtime may have
  nothing, and then (d) is skipped and said out loud (R4).

The ordering in R2 is the whole safety argument. `.sdlc/active` is moved by
`scripts/delegated_merge.py`'s `advance()`, not by the session; the handoff and ledger are committed
before anything is scheduled. So the chain is **best-effort on top of authoritative state**: if (d)
never happens, or the successor never starts, the repository is in exactly the state it is in today
and the owner resumes from `.sdlc/active` as they do now. Nothing downstream depends on the chain
having worked.

That is also why this does not contradict `knowledge/decisions/run-queue.md:25-27`, which closed the
route "a session cannot be **relied on** to" move the pointer, on the reasoning that "a design that
*requires* one alive is a design that stops when it dies." Nothing here requires a live session for
correctness; the chain only removes a paste when it happens to work.

### Interfaces (APIs, events, schemas) — exact shapes
One interface, and it is a file: the seed prompt section of `docs/sdlc/handoff/HANDOFF.md`. Its shape
is *standalone prose that names where to look* — the handoff, `.sdlc/active` on `main`, the item's
`work/<slug>/` artifacts — and never an instruction that widens authority (R10). The scheduling call
itself is deliberately **not** an interface this kit defines: it belongs to the runtime, takes the
prompt as its payload, and no repository code shapes or observes it (R4). That is the whole of the
model-neutral claim, and also the whole of C2's residual.

### Data and migrations
n/a — no data field, no schema, no store, no migration. Nothing here is classified public, internal,
personal or regulated, because nothing here is data.

### Failure modes and how they surface
- **Step (d) never fires** (no runtime capability, a scheduling error, the session dies at (c)). The
  repository is exactly as it is today; the owner resumes from `.sdlc/active`. Surfaces as silence —
  which is the failure mode this item is *accepting*, not fixing.
- **The successor starts and the pointer has moved underneath it.** It re-reads `.sdlc/active` from
  `main` as its first act (R2a, R10) and works whatever it names; a stale prompt loses a little time,
  never correctness.
- **The seed prompt is wrong or widened.** Bounded by R10 and, if the owner takes C5, by the merge
  script's locked-path floor. Surfaces in the pull request that changed the handoff — which is why C5
  matters.
- **The chain runs more often than intended.** R2's at-most-once cap is prose, enforced by the eval
  case's grep, not by a runtime guard. Surfaces on the billing page, which is how `ci-budget` started.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- **C1 — Risk class.** `intent.md` is approved at `risk-class: low` with the caveat that a mechanism
  needing "a script or a scheduled trigger" re-opens the question. The shape chosen adds **no script,
  no workflow, no secret and no new authority** — it is instructions plus a committed prompt — so
  `low` still holds on its own terms. Recorded here rather than assumed, because the intent asked for
  it explicitly. If Build finds it needs any file under `scripts/` or `.github/workflows/`, R9 fails
  and the item stops for a revised intent.
- **C2 — A session that schedules successors could chain without end.** Security rule 8 (agent
  hygiene) applies: the writer is not the approver. Three bounds, and the security review on this
  spec tested all three. Two hold: the successor is told to work the item `.sdlc/active` names, and
  only a human moves that pointer (`delegated_merge.py:431-434` binds the merge to it, `.sdlc` is on
  `ALWAYS_LOCKED`, and `next_item.py` makes the next slug a function of pre-existing human grants);
  and the successor can no more approve, merge or retire than this session can.
  **The third does not hold, and the earlier draft of this concern overstated it.** "Its prompt is
  committed, so an unexpected chain is visible in git" is a *convention, not a guarantee*: R4 puts the
  scheduling call in the runtime by design, so no hook, script or CI job is positioned to see the
  payload. What is committed is what *should* be sent; nothing binds it to what *is* sent. R2's
  at-most-once cap is prose in a skill for the same reason. The owner is therefore signing off on a
  protocol the repository states and cannot enforce — that is the real trade, and it should be read
  as such rather than as an audited one.
- **C3 — Adopters do not all get the trigger.** `scripts/adopt.sh:347-349` copies five workflows and
  not `delegated-merge.yml`, so an adopter without delegated mode has no automatic pointer advance
  either; and an adopter on a runtime without scheduling gets only (a)–(c). The protocol must
  therefore read as complete and useful with (d) absent. R4 is what makes that true, and it is the
  requirement most worth reviewing.
- **C5 — R3 makes the handoff executable, and the handoff is not locked. Owner act required before
  Build.** Found by the security review on this spec, and verified: `docs/sdlc/handoff/HANDOFF.md` is
  on **neither** `scripts/delegated_merge.py:89-93`'s `ALWAYS_LOCKED` (which covers
  `docs/sdlc/rules` and `docs/sdlc/templates`, not `handoff`) **nor** `.sdlc/delegation.yaml:64`'s
  `locked-paths`. Delegated auto-merge is live on this repository today (`.sdlc/delegation.yaml:13`
  `enabled: True`, `:48` `merge.enabled: true`). So once R3 turns that file's prose into the next
  session's instructions, a delegated pull request touching only the handoff could widen the seed
  prompt and **merge with no human click** — the gate checks chain, verify, evals and OKF, none of
  which read prose for scope creep, and every cycle rewrites that prompt by design (R2b), so a
  slightly wider one looks like business as usual. This is an escalation **this spec introduces**:
  before R3, the handoff was documentation nobody executed.
  The fix is one line the owner adds — `docs/sdlc/handoff` on `.sdlc/delegation.yaml`'s
  `locked-paths` — and it cannot be done inside this item: R9 forbids touching `.sdlc/`, and the
  policy file is human-only by design (`protect-paths.sh` never unlocks it). **Recommendation: take
  it before Build.** R10 is defence in depth, not a substitute: it bounds what a widened prompt can
  authorise, not whether one can land unreviewed.
- **C4 — The rendered line is permanent and the cap has none spare.** The adopter render sits at
  exactly `MAX_CONTEXT_LINES`. R8 buys discovery for every future session in every adopting
  repository, and costs a line of some other rule's prose forever. Reviewable by reading the re-flow
  diff; droppable without affecting R1–R7.

## Open questions carried from intent.md
All three were answered by the owner on 2026-09-13 and are recorded here as decisions D1, D2 and D3.
None remain open.

## Decisions (ADR-style: context → decision → consequences)
- **D1 — The mechanism is session-side and best-effort.** *Context:* the owner asked for a real
  mechanism rather than documentation; CI could spawn a session but every agent CI in this repository
  is read-only and advisory (`pr-review.yml:158-160` disallows `Bash,Edit,Write`; the gate's triage
  allows `Read,Grep,Glob`; `bands.yml` only files an issue), `adopt.sh` does not ship the merge
  workflow, and `production-gate.sh:26` blocks an agent dispatching a workflow. *Decision:* the
  finishing session schedules its successor through its own runtime, after committing the durable
  state, and says so when it cannot. *Consequences:* no new CI authority, no new secret, no
  contradiction with `run-queue.md`; the chain is a convenience, never a dependency; and the
  capability is uneven across runtimes, which R4 makes explicit rather than papering over.
- **D2 — `pointer-contradiction` is folded in.** *Context:* `HANDOFF.md:37` tells the session to set
  `.sdlc/active`, which `protect-paths.sh` blocks and `sdlc-run:71` forbids. *Decision:* fix it here.
  *Consequences:* one fewer work item; and R1 does not write a new protocol next to a line known to
  be wrong, in the same file. The queue item is closed by this spec rather than by its own chain.
- **D3 — The protocol earns exactly one rendered line, pointing not restating.** *Context:*
  `CLAUDE.md` never mentions the handoff, so an unchained start cannot discover the protocol; the
  chained start carries its own prompt and does not need it. *Decision:* one pointer line, paid for by
  re-flowing prose. *Consequences:* discovery for every adopter; one line of some other rule's prose
  re-flowed; and the protocol has two homes to keep in step, which the eval case pins.

## Gotchas found while reading the codebase
- `.sdlc` is in `PROTECTED_PATHS`, so `HANDOFF.md:37` instructs an act the hooks refuse. The same
  shape as the `sdlc-review` defect, in a different file — worth stating in the protocol itself, so
  the next writer does not reintroduce it.
- `CLAUDE.md`, `GEMINI.md` and `AGENTS.md` are **generated** from `docs/sdlc/rules/*`. Any requirement
  phrased as "add a line to CLAUDE.md" is unimplementable; the line goes in a fragment and is
  rendered. R5 exists because the kit forgot this about itself.
- `pr-review.yml` restores `.claude/` and `CLAUDE.md` from the **base** branch on `pull_request`
  events, so the automated reviewer cannot see this item's skill changes and will report them absent
  (`docs/sdlc/spikes/pr-review-identity.md`). Expect that finding on the Build pull request and
  answer it with the head's content, as `ci-budget` PR-B did.
- `scripts/next_item.py` already supplies the next slug deterministically, and `delegated_merge.py`'s
  `advance()` already writes the pointer and two ledger lines. The chaining act must not duplicate
  either; it reads the result.

## Not doing
- **No CI-side session spawner.** Rejected for this item: it contradicts `run-queue.md`, does not
  reach adopters (`adopt.sh:347-349`), and would be the first CI path starting a write-capable agent
  rather than a read-only one. If the owner wants it, it is its own intent, its own risk class, and a
  decision record superseding `run-queue.md`.
- **No change to who moves `.sdlc/active`.** It stays `advance()`'s, behind the merge.
- **No new secret, no new workflow, no `scripts/` change** (R9).
- **The other three fix-queue items** — `chain-check-robustness`, `adopt-ships-what-it-references`,
  `index-after-approval` — remain separate, as the intent's scope says.
- **Security rules 1–7**: n/a for this diff — no secret, no endpoint, no input boundary, no data
  field, no dependency, no `RELEASE_GATED_PATHS` path, no logging. Rule 8 is addressed in C2.
