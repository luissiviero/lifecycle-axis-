---
type: sdlc/spec
id: retire-delegated-items
title: A retired item is judged by who retired it, and a retirement is one tap that regenerates what it changes
description: "check_artifact_chain.py stops validating approved-by against the approver list on a superseded artifact and reads who retired it from the -> superseded ledger line and the commit that set the status (the author rule, or the Approved-Actor trailer when a tap did it); approve.py gains --retire and --next, approve_dispatch.py and approve.yml gain mode: retire with a next input, so a retirement is one tap whose commit goes through the committer that already regenerates the indexes. Nothing an agent can do becomes wider: superseded stays a word the hook, sign.py and the chain check refuse from an agent."
stage: design
# status: draft | in-review | approved | delegated | superseded
status: approved
reads: intent.md
# approved-by: product owner; tech lead consulted for medium/high risk; set only by a human
approved-by: luissiviero
approved-on: 2026-09-14
# skills-applied: skills loaded as hard constraints while writing this spec
skills-applied: [security-standards]
skills-version: e879ca8
prompt: "/sdlc-spec retire-delegated-items in session_01WSLuyVWcurCx6yPwNqxPPo, after the owner's tap approved the intent on main (017c832); from the approved supervised intent and its three owner-answered questions, a direct read of scripts/check_artifact_chain.py (the status rules, the approver and ledger checks, the author and trailer routes, RUN_NAME_RE, verify_dispatch_run, the pointer checks), scripts/approve.py, scripts/approve_dispatch.py, .github/workflows/approve.yml, scripts/sign.py and .claude/hooks/protect-approvals.sh (both refuse superseded), scripts/delegated_merge.py's route B, the four test modules the plan will extend and their fixtures, evals/cases/hook-blocks-agent-approval.yaml, and the three documents that describe the retirement routine"
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/86
tags: [delegated-mode, retirement, chain-check, approvals, gen-index, control-plane]
timestamp: 2026-09-14T16:40:00Z
---
# Spec: a retired item is judged by who retired it, and a retirement is one tap

## Requirements (each maps to an intent outcome)
| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | **A human-retired, agent-signed item passes.** On a `superseded` artifact the ledger shows signed under a grant (a `-> delegated` line for it, or a retiring line from `delegated`) the chain check does not validate `approved-by` against `.sdlc/approvers.yaml`: it is the agent's signature and is not read for the decision. On one a human approved (`approved -> superseded`, no signature line) the approver check stays as it is (plan deviation 3: the pre-existing `test_superseded_with_an_invalid_approver_fails` pins a human-approved artifact keeping a valid approver, and the intent keeps every existing case green). The existing rules that remain are what judge the retirement: a `-> superseded` ledger line for the artifact whose actor holds the artifact's role, and a commit that set `status: superseded` authored by a non-agent identity (or carrying a verified trailer, R-3). | 1 (first observable: `CHAIN: PASS` on the retired agent-signed tree) | New `scripts/test_check_artifact_chain.py::RetiredDelegatedItem::test_human_retirement_of_an_agent_signed_item_passes` — `_base_delegated_repo` (spec.md `delegated`, `approved-by: claude`), then on a branch the three artifacts set `superseded` with their `approved-by` kept, one `<old> -> superseded \| luissiviero` line each, committed by the human identity; `--slug demo --base main` ends `CHAIN: PASS` and prints `mode: in-progress`. **Red today**: `work/demo/spec.md approved-by 'claude' is not valid: agent identities cannot approve`. |
| R-2 | **An agent-retired item fails, naming the ledger.** The same tree with the retiring ledger lines' actor set to `claude` fails with exactly one `FAIL` line per artifact, the existing `work/<slug>/<artifact> log.md has no entry recording <artifact> superseded by a valid approver; append: ...` message; the count matters, so a superseded agent-signed artifact is not reported twice for one cause. | 1 (second observable) and 3 | `RetiredDelegatedItem::test_agent_actor_on_the_retiring_line_fails_naming_the_line` — as R-1 with every retiring line's actor `claude`: exit 1, last line `CHAIN: FAIL`, `no entry recording spec.md superseded by a valid approver` present, and the `FAIL:` lines that name spec.md number exactly one. **Red today**: the one failure is the approver message, and the ledger message is absent. |
| R-3 | **A tap-retired item passes on the trailer route, bound to the retiring line.** When the commit that set `superseded` carries `Approved-Run`/`Approved-Actor`, the deciding handle compared against `Approved-Actor` is the actor of that artifact's `-> superseded` ledger line, not `approved-by`; and `verify_dispatch_run` for a `superseded` artifact requires the run-name's mode segment to read `retire` and waives the artifact-in-title binding (one retire run supersedes every present artifact, whatever the `artifact` input showed), keeping the slug binding, the four-field run check and the no-token fallback exactly as they are. | 1 (the intent's third answer: "both routes") and 2 | `RetiredDelegatedItem::test_tap_retirement_with_trailers_passes` — the R-1 tree retired in one commit shaped as `ApprovalAuthor._reapprove_with_trailers` shapes one (author `luissiviero <...@users.noreply.github.com>`, committer the bot, both trailers), run without a token: `CHAIN: PASS`, and the output does not contain `the run's actor is the deciding handle`. **Red today**: `spec.md: the commit that set status: superseded carries Approved-Actor: luissiviero, but the artifact says approved-by: claude`. `RetiredDelegatedItem::test_tap_retirement_by_a_handle_outside_the_role_fails` — the same with `Approved-Actor: someone-else` and the ledger actor `someone-else`: `CHAIN: FAIL` (green today by a different message; it pins that loosening R-1 does not open this door). `DispatchAttestation` gains one case with the stubbed API: a run whose title is `approve intent.md (retire) on demo by @luissiviero` verifies a superseded `spec.md`; the same title with mode `supervised` is refused with `does not name 'spec.md'`. |
| R-4 | **Strict mode still refuses a superseded artifact, and every existing case stays green unmodified.** The intent's "both modes" is narrowed to in-progress mode (C1): a pull request whose diff carries anything but the item's own files must name a live item, because a retired plan closes the plan gate and a superseded chain must never cover code. | 3 | `RetiredDelegatedItem::test_strict_mode_still_refuses_a_superseded_artifact` — the R-1 tree plus one file outside the item in the diff: `CHAIN: FAIL` with `status is 'superseded', must be 'approved'` (green today; a pin). `python3 scripts/run_tests.py` green with no existing case in `scripts/test_check_artifact_chain.py` edited: `git diff origin/main -- scripts/test_check_artifact_chain.py` shows additions only (`--numstat` deletions column is 0). |
| R-5 | **`approve.py --retire` retires an item as a human.** `scripts/approve.py <slug> [artifact...] --retire [--next SLUG] [--as HANDLE] [--note TEXT] [--from-dispatch RUN_ID] [--dry-run]`: with `--retire` the artifacts are optional and default to every one of `intent.md`, `spec.md`, `plan.md`, `incident.md` present on disk; each must be `approved`, `delegated` or already `superseded` (the last is skipped as a no-op, so an interrupted retirement can be finished); a present `draft` or `in-review` artifact is refused naming it, and nothing is written. The handle must hold each artifact's role in `.sdlc/approvers.yaml`, checked before any write. Per artifact it sets `status: superseded` only — `approved-by` and `approved-on` are untouched — and appends `- <ts> \| <artifact> \| <old> -> superseded \| HANDLE \| <sha> \| <note>`. No stage-order rule applies. `--retire` refuses `--delegate` and `--activate` (use `--next`). The agent-session refusal (exit 3) and the `--from-dispatch` conditions are the ones approving has today; a dispatch run writes `retired=<artifacts>`, `run-id=` and `actor=` to `$GITHUB_OUTPUT`. | 2 (the first answer: "approve.py --retire under the same attestation") and 3 | New `scripts/test_approve.py::Retire` — `test_retires_every_present_artifact_and_keeps_approved_by` (three artifacts `superseded`, `approved-by` unchanged byte for byte, three ledger lines `approved -> superseded`, then the copied chain check on a retiring branch ends `CHAIN: PASS`); `test_a_delegated_artifact_is_retired_from_delegated` (spec.md `delegated`/`claude`: the line reads `delegated -> superseded`, the approver is the human handle); `test_refuses_an_in_review_artifact_and_writes_nothing`; `test_a_handle_without_a_role_is_refused_before_writing`; `test_already_superseded_is_a_noop`; `test_refuses_delegate_and_activate`; `test_agent_session_is_refused` (exit 3); `test_from_dispatch_writes_retired_to_github_output`; `test_dry_run_writes_nothing`. All red today (`--retire` is an unknown argument). |
| R-6 | **`--next` moves the pointer, never leaves a retired slug in it.** `--next SLUG` must match `check_artifact_chain.SLUG_RE`, differ from the retired slug, and name a `work/<SLUG>/intent.md` on disk whose status is not `superseded`; it writes `.sdlc/active`. `--next ""` (blank; the tap's blank input) clears the pointer when it names the retired slug. `--retire` with no `--next` behaves as blank. A pointer naming some other live item is left as it is either way, with a printed note. Validation happens before any write. | 2 (the second answer: "a slug repoints .sdlc/active at it, blank clears it") | `Retire::test_next_repoints_the_pointer`; `test_blank_next_clears_a_pointer_naming_the_item`; `test_a_pointer_at_another_item_is_left_alone`; `test_next_naming_no_item_is_refused` (exit 1, nothing written, the artifacts still `approved`); `test_next_naming_a_retired_item_is_refused`; `test_next_with_a_traversing_slug_is_refused` (`../x`). Red today. |
| R-7 | **The role gate covers every artifact the retirement will write.** `approve_dispatch.check_actor(login, artifact, mode="retire", root=, slug=)` requires `slug`, ignores the `artifact` input's value, and requires `login` to hold the role of every chain artifact present under `work/<slug>/`; a slug with no artifacts is refused. Supervised and delegated behaviour is unchanged. | 2 and 3 | `scripts/test_approve_dispatch.py::Retire::test_retire_requires_every_present_artifacts_role` (an approvers file where the actor holds `product-owner` but not `tech-lead`: refused naming `plan.md`); `test_retire_with_every_role_passes`; `test_retire_without_a_slug_is_refused`; `Mode` cases green unmodified. Red today (`mode="retire"` passes as if supervised). |
| R-8 | **The tap's commit says what it did and carries the same trailers.** `approve_dispatch.commit(..., mode="retire")` writes the subject `[<slug>] Retire as <actor>`; the note, the trailers, the author/committer split, the staged-path allowlist (`.sdlc/active` is already in it) and the index regeneration are unchanged; `--mode` reaches `commit` from the CLI. | 2 (the intent's third observable: "commits through scripts/approve_dispatch.py --commit, which already regenerates the indexes") | `test_approve_dispatch.py::Retire::test_retire_subject_and_trailers` (subject as above, message ends with both trailers); `test_retire_commits_the_pointer_and_the_regenerated_indexes` (a tree where approve.py-shaped writes cleared `.sdlc/active` and left `work/index.md` stale: the commit holds both and `gen_index.py --check` on it prints `INDEX: up to date`); the existing `Commit` cases green unmodified. Red today (`commit()` has no `mode`). |
| R-9 | **The workflow offers the retirement.** `.github/workflows/approve.yml`: `mode` options `[supervised, delegated, retire]`; a new optional string input `next` ("retire only: the slug to point .sdlc/active at; blank clears it"), sanitised like `slug`; the Resolve step requires an explicit slug for `retire` as it does for a grant; the role gate passes `--mode`; the Approve step runs `approve.py "$SLUG" --retire --as "$ACTOR" --from-dispatch "$GITHUB_RUN_ID" [--note] --next "$NEXT"` for `retire`; the Commit step passes `--mode "$MODE"`; `run-name` is byte-identical, so `RUN_NAME_RE` and route B of `delegated_merge.py` keep parsing it. The `artifact` input's description says it is ignored for `retire`. | 2 | `scripts/test_check_workflow_permissions.py::ApproveWorkflow`: `test_offers_the_four_inputs` becomes `test_offers_the_five_inputs` (`["artifact", "mode", "next", "note", "slug"]`, mode options three) — red today; `test_run_name_still_matches_the_checker_that_parses_it` unmodified and green; `test_approve_dispatch.py::Retire::test_the_workflow_requires_an_explicit_slug_for_a_retirement` asserts the Resolve step's condition names `retire` — red today. |
| R-10 | **The tap regenerates what it changes.** A retirement run's commit contains every index the route allows, by the existing `regenerate()` call in `commit()`; no second regeneration path is added. | 2 ("gen_index.py --check on the resulting commit prints INDEX: up to date") | R-8's second case; `grep -c "render_all" scripts/approve_dispatch.py` is unchanged from `main`. The production observation is the owner's first retire tap on `main`, recorded in the ledger of the item it retires. |
| R-11 | **Nothing an agent can do becomes wider.** `protect-approvals.sh`, `sign.py` and `delegated_merge.py` are not edited; the hook still refuses an Edit that sets `superseded`; `sign.py` still refuses it; the chain check still fails a superseded artifact whose retiring commit is agent-authored or whose retiring line is missing or agent-actored (R-2). | 3 | `git diff origin/main --stat -- .claude/hooks scripts/sign.py scripts/delegated_merge.py .sdlc scripts/checks` prints nothing; `scripts/run_evals.sh --only hook-blocks-agent-approval` passes; existing `test_superseded_without_a_ledger_line_by_a_valid_approver_fails` and the `ApprovalAuthor` agent-identity cases green unmodified; `test_sign.py` green. |
| R-12 | **The routine is written where a human reads it.** `docs/sdlc/github-setup.md`'s Actions-tab paragraph gains the retirement (mode `retire`, `slug` required, `next`); `docs/sdlc/handoff/HANDOFF.md`'s bullet beginning "Retiring an item is a human act, from the web editor today" names the tap first and the web editor second, and its clean-up advice about a retired `Work-Item:` is corrected to what R-1 makes true (an in-progress pull request may name a retired item); `knowledge/lessons/human-commits-leave-indexes-stale.md`'s "Where it is enforced" records that the tap route is closed for approvals and retirements and only the web-editor route stays open. | intent Affected systems | `grep -n "retire" docs/sdlc/github-setup.md` is non-empty; `grep -c "from the web editor today" docs/sdlc/handoff/HANDOFF.md` is 0; `grep -n "retire" knowledge/lessons/human-commits-leave-indexes-stale.md` names the tap; `python3 scripts/check_okf.py` ends `0 warnings`. |
| R-13 | **The loop is green.** `scripts/verify.sh` ends `VERIFY: PASS`, `python3 scripts/check_artifact_chain.py --base origin/main --slug retire-delegated-items` ends `CHAIN: PASS`, `scripts/run_evals.sh` ends `0 fail`, `python3 scripts/check_okf.py` ends `0 warnings`, both generators report up to date, and the adopter's rendered context file stays at or under `MAX_CONTEXT_LINES`. | all | The last lines, pasted in the pull request; the new cases counted, every one named red above seen red before its code (`knowledge/lessons/a-verifiable-command-fails-before-the-change.md`). |

## Design
### Architecture / data flow
Two halves, both on the human side of the line the hook draws.

**The check.** In `scripts/check_artifact_chain.py` the per-artifact block that today begins with the comment
"Approving and superseding are both human acts: the same approver, ledger and commit-author checks apply to
either status" splits by status:

- `approved`: unchanged. `av.is_valid(name, approved_by)`, then the `-> approved` ledger line whose actor is
  `approved_by`, then the author/trailer check with `Approved-Actor` compared to `approved_by`.
- `superseded`: no `is_valid` on `approved_by`. The ledger rule stays as written today (a `-> superseded`
  line for the artifact whose actor `av.is_valid(name, actor)` accepts) and becomes the whole of the
  "who" decision; the artifact's *retirer* is that line's actor. The author/trailer check runs as today
  on the commit `-G '^status: superseded$'` finds, with two changes: `Approved-Actor` is compared to the
  retirer, and `verify_dispatch_run(..., artifact=name, ..., retired=True)` (or an equivalent argument the
  plan names) checks that `RUN_NAME_RE` parses the title with `mode == "retire"` and skips the
  `artifact in title` line; a superseded artifact attested by a run whose mode is not `retire` is refused
  with the existing `does not name` wording, because an approval run cannot have set `superseded`.

Agent-signed history stays exactly as it is on disk: `approved-by: claude` on a retired `spec.md` is the
record that the agent signed it under a grant, which is what the intent means by "the signature's record".

**The tap.** `approve.py` gains one mode and one pointer flag; `approve_dispatch.py` learns the mode in its
two entry points; the workflow exposes it. The data flow of a retire run is the approval's with one step
changed:

1. Resolve the slug (explicit, or refused: `run-name` must record it, and R-6 needs it).
2. `approve_dispatch.py --check-actor "$ACTOR" --artifact "$ARTIFACT" --mode retire --slug "$SLUG"`: refused
   unless the actor holds every present artifact's role (R-7). Nothing written on refusal.
3. `approve.py "$SLUG" --retire --as "$ACTOR" --from-dispatch "$GITHUB_RUN_ID" --next "$NEXT" [--note]`:
   validates everything, then writes the statuses, the ledger lines and the pointer (R-5, R-6).
4. `approve_dispatch.py --commit ... --mode retire`: regenerates the indexes the route allows, refuses any
   stray path, commits `[slug] Retire as actor` with the trailers, author the actor, committer the bot
   (R-8, R-10). `git push origin HEAD:$REF` as today.

A retirement on `main` takes the wide route and heals every stale index it finds, which is what the intent's
second half asks for; on any other ref only the item's two.

### Interfaces (APIs, events, schemas) — exact shapes
- `scripts/approve.py <slug> [artifact ...] --retire [--next SLUG] [--as HANDLE] [--note TEXT] [--from-dispatch RUN_ID] [--dry-run]`.
  `artifacts` becomes `nargs="*"`; without `--retire` an empty list is a usage error (exit 1, so today's
  `nargs="+"` behaviour is preserved by hand). Output per artifact: `retired: work/<slug>/<name> (<old> ->
  superseded) by <handle>` and the ledger line; for the pointer `pointer: .sdlc/active -> <next>` or
  `pointer: .sdlc/active cleared` or `pointer: .sdlc/active names '<other>', left as it is`. The human-commit
  hint names `work/<slug> .sdlc/active` when the pointer changed. Refusals (exit 1, nothing written):
  `approve: work/<slug>/<name> is '<status>'; a retirement supersedes approved or delegated artifacts only`,
  `approve: '<handle>' may not retire <name>: <reason>`, `approve: --retire takes --next, not --activate`,
  `approve: --retire and --delegate are exclusive`, `approve: --next '<x>' is not a work-item slug`,
  `approve: --next '<x>' names no work/<x>/intent.md`, `approve: --next '<x>' is retired`, `approve: --next
  may not name the item being retired`. A slug is judged by `check_artifact_chain.SLUG_RE`, already the
  module `approve.py` imports `ROOT` and `front_matter` from (G-5).
- `scripts/approve_dispatch.py --check-actor LOGIN --artifact NAME --mode retire --slug S [--root DIR]`:
  `ok` / exit 0, or exit 1 with `approve-dispatch: LOGIN may not retire <name>: <reason>` for the first
  artifact refused, or `... slug S has no chain artifact to retire`.
- `scripts/approve_dispatch.py --commit ... --mode retire`: subject `[S] Retire as LOGIN`; any other or absent
  `--mode` keeps `[S] Approve <artifact> as LOGIN`.
- `.github/workflows/approve.yml` inputs: `artifact` (unchanged options; description gains "ignored for
  retire"), `mode` options `[supervised, delegated, retire]`, `slug`, `note`, `next` (string, optional). The
  step summary reads `Retired` / `` `<slug>` by @<actor>, .sdlc/active -> <next|empty> ``.
- `check_artifact_chain.verify_dispatch_run(run_id, actor, slug=None, artifact=None, commit_sha=None, retired=False)`:
  with `retired=True` the title must parse with mode `retire`, and `artifact` is not required in the title.
- Ledger line shape, unchanged: `- <RFC3339> | <artifact> | approved -> superseded | <handle> | <sha> | <note>`
  (or `delegated -> superseded`). The ledger parser is not touched.

### Data and migrations
No data classes, no schema, no migration. The four retired items on `main` (`sdlc-kit-phase-1`,
`session-chaining`, `approve-tap-regenerates-index`, `advance-push`) are judged by the new rule the moment it
lands: every one of their twelve `-> superseded` ledger lines carries the actor `luissiviero` (read from
their `log.md` files while writing this), and their retirement commits are human-authored, so an in-progress
pull request naming any of them passes; `approve-tap-regenerates-index`, whose `spec.md` and `plan.md` read
`delegated -> superseded` with `approved-by: claude`, goes from red to green, which is R-1 in production. No
file under `work/` other than this item's is rewritten by this item.

### Failure modes and how they surface
- Tap with `retire` and a blank slug: the Resolve step exits 1 with `::error::a retirement must name its slug
  explicitly`; nothing written.
- Actor lacks one artifact's role: the role gate exits 1 naming the artifact; nothing written.
- `next` names no item, a retired item, the item itself, or a non-slug: `approve.py` exits 1 before any write;
  the run fails; nothing pushed.
- An artifact is `draft` or `in-review`: refused naming it; abandoning an unfinished item is not a
  retirement (Not doing).
- Everything already superseded and the pointer already right: `approve.py` writes nothing, `commit()` refuses
  with `nothing staged` (today's D3), the run fails red, nothing pushed. That is the honest outcome; a
  retirement that changes nothing has no decision to attest.
- A retirement committed by an agent identity, from any route: `CHAIN: FAIL` on the author rule, as today.
- A retiring ledger line by an agent handle: `CHAIN: FAIL` naming the line (R-2).
- A forged trailer on a retirement, no token: the no-token fallback applies unchanged (an agent-authored
  commit with an unverified trailer fails); with a token, the run's actor, event, path, conclusion, slug and
  `retire` mode must all agree.
- A web-editor retirement: passes the check by the author rule (this is the fix's purpose) and leaves the
  indexes stale, as the lesson keeps recording.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: the intent's first observable says `CHAIN: PASS` "in both modes"; this spec keeps strict mode refusing
  `superseded` (R-4) and makes only in-progress mode pass — policy: `docs/sdlc/rules/00-chain.md` ("a retired
  plan closes the gate") — contradiction? yes, with the intent's wording; no, with its Must ("keep every
  existing chain-check case green unmodified": strict-mode refusal is pinned by existing cases) — owner:
  luissiviero — resolution:
- C2: `.github/workflows/approve.yml` is on rule 3's never-edit list; the agent edits it under the unlock so
  the workflow test (R-9) and the file land in one pull request, and the owner's label and click gate it —
  policy: CLAUDE.md rule 3, `knowledge/lessons/control-plane-unlock-is-advisory.md` — contradiction? no —
  owner: luissiviero — resolution:
- C3: R-1 removes one check from the chain (the approver list on `superseded`); the weight moves to the ledger
  actor's role and the commit's author or trailer, both already enforced. A defect in the split (a code path
  where `status == "superseded"` skips the ledger rule) would let an agent-authored retirement pass, which is
  why R-2 counts `FAIL` lines and R-3 has a wrong-handle case — policy: security-standards 8 — contradiction?
  no — owner: luissiviero — resolution:
- C4: the plan will be `kind: feature`, not `fix`: four existing test modules gain cases and one existing
  workflow test changes its expected input list (R-9), which `protect-tests.sh` refuses under `kind: fix` —
  policy: CLAUDE.md rule 1 — contradiction? no — owner: luissiviero — resolution:

## Open questions carried from intent.md
- All three were answered on the intent (`approve.py --retire` under the same attestation; `next` moves the
  pointer, blank clears; both routes). One reading of the second answer is decided here and can be reversed
  on the plan: blank `next` clears the pointer **when it names the retired item**; a pointer already at a
  different live item is left alone (D3).

## Decisions (ADR-style: context → decision → consequences)
- D1: **`superseded` is judged by the retirer, never by `approved-by`.** Context: `approved-by` on a retired
  artifact is history (a human's or, under a grant, the agent's signature), and the check misread it as the
  retirer. Decision: on `superseded`, the ledger line's actor and the retiring commit's author or trailer are
  the whole decision; the approver list is still asked about `approved-by` when the ledger shows no signature
  for the artifact (no `-> delegated` line and no retiring line from `delegated`), because a human-approved
  artifact's approver was a valid handle and a bot handle there is a malformed record (the pre-existing case
  pins it; amended under plan deviation 3). Consequences:
  R-1 to R-3; `approved` keeps every check it has; the two agent-signed artifacts on `main` become checkable.
- D2: **The retirement lives in `approve.py` as `--retire`.** Context: the owner's first answer. Decision:
  one script, the same `--from-dispatch` attestation, the same agent refusal. Consequences: `artifacts`
  becomes optional under the flag; `test_approve.py`'s fixture copies `check_artifact_chain.py` already, so
  `SLUG_RE` costs no new copy (G-5).
- D3: **Blank `next` clears a pointer naming the retired item and leaves any other alone.** Context: the
  owner asked that a retired slug never stay in the pointer, and that blank clears; a pointer that already
  names another live item (the owner retiring an item that is not the active one) would be lost by a literal
  clear. Decision: clear when it names the retired item, otherwise print a note and leave it. Consequences:
  the invariant "the pointer never names a retired item after a retirement" holds either way; the owner can
  reverse this on the plan by asking for a literal clear.
- D4: **The `artifact` input is ignored in retire mode rather than replaced.** Context: `run-name`
  interpolates raw inputs and `RUN_NAME_RE` and route B parse it, and a retirement supersedes every present
  artifact. Decision: keep the input and the run-name shape; the check waives the artifact binding when the
  mode segment reads `retire`. Consequences: no change to `RUN_NAME_RE`, `delegated_merge.py` or the
  workflow-permissions run-name test; the ignored input is documented in its description (R-9).
- D5: **Strict mode stays closed to `superseded`.** Context: C1. Decision: R-4. Consequences: a pull request
  that carries code may never name a retired item; the clean-up pull request after a retirement carries the
  retired `Work-Item:` line and only the item's own files and indexes (`#91` did exactly this), and the
  handoff's advice is corrected to say so (R-12).
- D6: **The role gate reads the checkout, not the input.** Context: R-7. Decision: `check_actor` with mode
  `retire` lists the chain files present under `work/<slug>/` and requires every role. Consequences: a
  retirement by the tech lead alone is refused if the item has an `intent.md` (product-owner); in this
  repository every role is the same handle, so the owner's tap passes.

## Gotchas found while reading the codebase
- G-1: `approved-by` is misread twice, not once. The obvious site is `av.is_valid(name, approved_by)` under
  the comment "Approving and superseding are both human acts"; the second is the trailer route's `if
  av.normalize(actor) != av.normalize(approved_by)`, which would refuse every tap retirement of an
  agent-signed artifact after the first fix. R-3 pins it.
- G-2: `verify_dispatch_run` has `if artifact and artifact not in title: return False`; with three artifacts
  superseded by one run whose title names one `artifact` input, two of three would fail. R-3 waives it on
  `mode == "retire"` only.
- G-3: `RUN_NAME_RE` is pinned to the workflow's `run-name` by `test_run_name_still_matches_the_checker_that_parses_it`,
  and `delegated_merge.py`'s route B checks `"intent.md" not in title` on grant commits. Neither changes: a
  retire run is never a grant commit (a grant adds `mode: delegated`), so route B never sees one.
- G-4: `approve.py` declares `artifacts` with `nargs="+"`, so `approve.py <slug> --retire` is a usage error
  today; and `commit()` refuses a diff of indexes alone, so a no-op retirement fails the run rather than
  pushing an empty attestation (a feature, kept).
- G-5: `test_approve.py::make_repo` copies a fixed list of scripts into the fixture (`approve.py`,
  `approvers.py`, `log_ledger.py`, `check_artifact_chain.py`); a new import in `approve.py` must be on that
  list or every case fails with `ModuleNotFoundError`. `SLUG_RE` lives in `check_artifact_chain.py`, already
  copied.
- G-6: an empty `.sdlc/active` is a handled state in the check (`no active work item (.sdlc/active is empty;
  pass --slug or set it)`), but it fails every pull request without a `Work-Item:` line. The owner's second
  answer accepts this; the handoff says a handoff-only pull request carries the line or the owner points
  first.
- G-7: `protect-tests.sh` under `kind: fix` locks every test file that exists on disk; this item edits four,
  so the plan is `kind: feature` (C4).
- G-8: `test_the_workflow_requires_an_explicit_slug_for_a_grant` asserts the literal shell condition
  `[ -z "$slug" ] && [ "$MODE" = delegated ]`; the retire condition is a second line, not an edit of that
  one, so the case stays green unmodified.

## Not doing
- Making strict mode accept `superseded` (C1, D5): a pull request that carries code names a live item.
- Retiring an item automatically on merge, or the advance itself (intent Out of scope; `work/advance-push`).
- Enforcing the web-editor route's index drift (intent Out of scope; the lesson stays).
- Abandoning an unfinished item (a `draft` or `in-review` artifact) by tap: `--retire` refuses it; deleting or
  hand-editing such an item stays a web-editor act.
- A `docs/sdlc/rules/` line for the routine: the adopter's rendered context file sits at the cap
  (`knowledge/lessons/adopter-context-file-sits-at-the-cap.md`); the handoff and `github-setup.md` carry it.
- The `EXEMPT` asymmetry in the chain check (`GEMINI.md`/`AGENTS.md` not exempt): filed for its own intent.
- Touching `.sdlc/`, `.claude/hooks/`, `scripts/checks/`, `sign.py` or `delegated_merge.py` (R-11).
