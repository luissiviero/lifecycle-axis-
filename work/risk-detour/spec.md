---
type: sdlc/spec
id: risk-detour
title: A deterministic detour check at every gate, a route record reviewers judge, a park that is two ledger words, and a queue that skips what is parked
description: "The run meets non-low work as a DETOUR: needed line from a new path check that reuses the merge script's own locked-path matcher; a revision record of kind detour carries the route and reviewers judge the route, not the trigger; a unanimous revise amends and re-signs the artifact, two split records at one gate park the item as a parked: ledger line on intent.md that next_item.py and the index both read; the park lands as the item's own delegated pull request so the merge's advance moves the pointer, and the non-low remainder is a supervised intent with a detour-of key in its own pull request."
stage: design
# status: draft | in-review | approved | delegated | superseded
status: delegated
reads: intent.md
# approved-by: product owner; tech lead consulted for medium/high risk; set only by a human
approved-by: claude
approved-on: 2026-09-15
# skills-applied: skills loaded as hard constraints while writing this spec
skills-applied: [security-standards]
skills-version: e879ca8
prompt: "/sdlc-run risk-detour in session_01Fux6LyAKQhzsaSdrRaddij, the scheduled successor named by the handoff's seed prompt of 2026-09-15 ~00:35 UTC; from the approved, delegated intent (3ce6eae) and its six owner-answered questions, a direct read of .claude/skills/sdlc-run/SKILL.md (the stop rule, the revision rule, step 7), docs/sdlc/templates/revision.md, scripts/next_item.py and scripts/test_next_item.py, scripts/delegated_merge.py (ALWAYS_LOCKED, _locked_paths, check_locked_paths, check_pull_request, advance, load_config), scripts/check_artifact_chain.py (STATUSES, check_revisions, _reviewer_verdicts, REVISION_NOTE_RE, own_artifact), scripts/sign.py (resolve_revision, the revision note shape), scripts/log_ledger.py, scripts/gen_index.py and its golden test, scripts/gen_context_files.py, the two rule fragments, evals/README.md and three eval cases, knowledge/decisions/delegated-mode.md, work/run-queue/revisions/1.md, and scripts/adopt.sh into scratch for the adopter's line count"
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/60
tags: [delegated-mode, run-queue, sdlc-run, risk-class, revision-record, consensus, parking, detour]
timestamp: 2026-09-15T00:50:24Z
---
# Spec: a deterministic detour check at every gate, a route record, a park of two ledger words, and a queue that skips it

The intent's six questions are answered and are decisions here, not proposals: a click-locked route is
finished to a ready pull request and parked (Q1); two records per gate, then the park (Q2); a second
Claude model is a valid second reviewer, named in its heading (Q3); the generated index marks a parked
item, with a golden test (Q4); `scripts/next_item.py` joins `locked-paths` after this item merges, as the
owner's own edit (Q5, not this item's); at the intent-drafting gate a unanimous `revise` files and ledgers
the record and re-signs nothing (Q6).

## Requirements (each maps to an intent outcome)
| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | **A detour record is a revision record, accepted as-is.** `docs/sdlc/templates/revision.md` gains a front-matter key `kind: revision \| detour` (default `revision`; a detour record sets `detour`), a `## Route` section for a detour (the outcome the route reaches, every path it touches with the list each falls under, why the class is honestly low, the remainder left for a human, what in spec and plan goes stale), and a reviewer question set for a detour that asks about the route, not the trigger. The verdict words stay `revise` and `keep`; `STATUSES` is untouched; `scripts/sign.py` and `scripts/check_artifact_chain.py` do not change. | 1 | `scripts/test_sign.py::SignPasses::test_resigns_with_a_detour_record`: a record with `kind: detour`, a `## Route` section and two `## Reviewer:` sections ending `verdict: revise` re-signs `spec.md` with `--revision revisions/2.md --note "detour: <route>"`, and the ledger note reads `revision 2: detour: <route>`; `python3 scripts/check_artifact_chain.py --base HEAD` on that fixture's shape is the same code path as today (`_reviewer_verdicts` reads two `revise`). New test, a guard predicted green today: the template is prose, so the test is the proof that the new marker and section are inert to the judging scripts; it is mutation-checked by flipping one verdict to `keep`, which `sign.py` must refuse. |
| R-2 | **The trigger is one command with two answers.** New `scripts/check_detour.py` takes paths from `--paths P...`, `--plan work/<slug>/plan.md` (every `## Files that change` bullet's leading path; a glob bullet is expanded under the root, the literal kept when nothing matches) or `--diff <base>` (`git diff --name-only <base>...HEAD`, renames as both names), matches each through `delegated_merge.check_locked_paths([{"filename": p}], prefixes)` with `prefixes = delegated_merge._locked_paths(config, policy, slug)` -- so `PROTECTED_PATHS`, `RELEASE_GATED_PATHS`, the policy's `locked-paths`, `ALWAYS_LOCKED` and, with `--slug`, this item's `intent.md` are the lists, exactly as the merge will judge them -- prints one line per locked path `<path>: locked by <list> '<prefix>'` and ends `DETOUR: none` (exit 0) or `DETOUR: needed (<n>)` (exit 3). Exit 2 with a `check-detour:` line on stderr for no source, two sources, an unreadable plan, a plan without the heading, or a base that `git rev-parse --verify` rejects. | 3 | `scripts/test_check_detour.py` (new module): `Matching::test_every_locked_list_is_named` (one path per list, all five labels), `Matching::test_a_file_entry_never_matches_a_longer_name` (`REVIEW.md.bak` is none), `Matching::test_clean_paths_end_none_and_exit_zero`, `Sources::test_plan_bullets_are_read_from_files_that_change` (a fixture plan with two bullets and a glob), `Sources::test_diff_names_both_sides_of_a_rename`, `Cli::test_needed_exits_three_and_counts`, `Cli::test_bad_input_exits_two` (no source, two sources, missing heading, bad base). Eval `evals/cases/detour-check-names-locked-paths.yaml`: a fixture root with a policy and a config, `--paths` over one clean and two locked paths ends `DETOUR: needed (2)` exit 3, and the clean set ends `DETOUR: none` exit 0. |
| R-3 | **A parked item is never offered again.** `next_item.py` gains `parked_note(entries) -> str \| None`: of the ledger entries whose `artifact` is `intent.md` and whose stripped note starts `parked:` or `resumed:`, the last in file order decides; it returns the `parked:` note or `None`. `_eligible` returns `(False, "parked: ...")` when it is set, before the spec test, so a park before the spec and a park mid-item read the same. The record the note names is not opened: a park is conservative. | 4 | `scripts/test_next_item.py::Parked::test_parked_before_the_spec_is_skipped`, `Parked::test_parked_then_resumed_by_the_owner_is_offered_again`, `Parked::test_a_parked_note_naming_a_missing_record_still_parks`, plus `Parked::test_parked_note_reads_the_latest_of_parked_and_resumed` on the helper. Eval `evals/cases/run-queue-skips-parked-item.yaml`: two granted items, the earlier one parked by a ledger line; `next_item.py --root` prints the later one, `--list` prints only it; a `resumed:` line appended puts the first back at the head. |
| R-4 | **The park moves the pointer on.** A park is the item's own delegated pull request: `work/<slug>/log.md` (the `parked:` line), `work/<slug>/revisions/<n>.md`, the regenerated `work/<slug>/index.md` and `work/index.md`, nothing else, so `check_locked_paths` finds nothing, the chain runs in in-progress mode and `delegated_merge.py` merges it; its `advance()` then computes the next item through `next_item.next_item(root, policy, exclude=<slug>)`, which R-3 makes skip the parked item, and writes the two ledger lines it writes today. No script that judges the merge changes. | 5 | `scripts/test_park_advance.py::ParkAdvance::test_the_advance_skips_a_parked_item_and_lands_on_the_next` (new module, composing `test_delegated_merge.Advance`'s fixture: three granted items, the merged one, a parked one with the earlier `delegated-on`, a queued one): `advance()` returns the queued slug, `.sdlc/active` names it, the merged item's ledger ends `merged as <sha>; .sdlc/active advanced to <queued>`, the queued item's ledger ends `.sdlc/active advanced here after PR #<n> merged`, the parked item's ledger is byte-identical to before, and `git log` on the fixture shows one commit by `github-actions[bot]` after the fixture commit and none by a human. Red today: `advance()` lands on the parked item. |
| R-5 | **The remainder reaches the owner as a supervised intent.** `docs/sdlc/templates/intent.md` gains `detour-of:` (blank; the slug of the parked item when this intent is its remainder) after `supersedes:`. `.claude/skills/sdlc-run/SKILL.md` and `.claude/skills/sdlc-intent/SKILL.md` say the remainder is `work/<slug>-supervised/intent.md` with `mode: supervised`, the record's risk class, `detour-of: <slug>`, on its own branch and pull request, never in the park pull request (a diff touching another item's `work/<other>/` drops the chain to strict mode). | 6 | Eval `evals/cases/detour-is-written-down.yaml` (structural greps, the shape of `session-protocol-is-written-down`): the intent template has `^detour-of:`; the revision template has `^kind:`, `^## Route` and the five route questions; the log template carries a `parked:` example line; the run skill has `## The detour rule`, names `scripts/check_detour.py`, `DETOUR: needed`, `two records`, `parked: ready PR #<n>; click needed`, `-supervised`, `detour-of` and no longer says a locked path "stops the whole queue"; the spec, plan and intent skills each name `scripts/check_detour.py`. |
| R-6 | **The index marks a parked item.** `gen_index.py` reads `next_item.parked_note` on the item's ledger: `work/index.md`'s `stage` cell reads `parked` for such an item, and `work/<slug>/index.md` gains the line `Parked: <note>` before `Last gate:`. Unparked items render byte-identically to today. | Q4 | `scripts/test_gen_index.py::ParkedMarker::test_a_parked_item_is_marked_in_both_indexes` (its own fixture tree, so `GOLDEN_TOP_INDEX` is untouched): golden strings for the item index and the table row; `test_two_items_match_golden_strings` still passes unchanged. |
| R-7 | **The run detours at every gate, and parks instead of stopping.** `sdlc-run/SKILL.md`: the locked-path case leaves "Stop and call the owner back" and becomes `## The detour rule`: at intent drafting, spec, plan and mid-build the trigger is `check_detour.py` (`--paths` on the paths the intent's Affected systems or the spec's design names, `--plan` on the plan, `--diff origin/main` on the branch); `needed` convenes at least `min-reviewers` reviewers on a different model from the writer where one is available, a second Claude model when not, each named in its heading, with the route question set; unanimous `revise` amends the artifact and re-signs it under the record (`sign.py --revision revisions/<n>.md --note "detour: <route>"`, ledger `revision <n>: detour: <route>`); at the intent gate nothing is re-signed, the route goes into the in-review intent's Proposed outcome and the tap is the sign-off; a split record is closed and a changed route is a new record; the third trigger at one gate parks. A park: the `parked: revision <n>: <why>; remainder: <slug>-supervised` line on `intent.md`, `approved -> approved`, the item's own pull request per R-4; the remainder per R-5; then step 7 as today. A route the agent may build but the merge locks is finished to a ready pull request and parked `parked: ready PR #<n>; click needed (<path>)` from a second, ledger-only pull request (`check_pull_request` counts open pull requests by head sha, so the two coexist). `sdlc-spec`, `sdlc-plan` and `sdlc-intent` each gain the one line that runs the check at their gate. | 2, 5, Q1, Q2, Q3, Q6 | Eval `detour-is-written-down.yaml` (R-5's, the same case) asserts every quoted phrase above; `skill-names-match-templates` and `session-protocol-is-written-down` still pass. |
| R-8 | **Nothing the owner reads by hand gets longer.** `docs/sdlc/rules/30-conventions.md` and `docs/sdlc/rules/40-claude-only.md` change by rewriting existing lines (the delegated-mode bullet, the `/sdlc-run` bullet), adding none; `python3 scripts/gen_context_files.py` regenerates the three context files. | 7 | `scripts/adopt.sh <scratch>/adopt-after --with-hooks; wc -l <scratch>/adopt-after/{CLAUDE,GEMINI,AGENTS}.md` reads at most `120 119 99`, the numbers measured before the change (the adopter's `CLAUDE.md` sits at the cap); `scripts/checks/context-drift.sh` ends `CONTEXT: 3 files up to date`. |
| R-9 | **The decision is on record.** `knowledge/decisions/risk-detour.md` (`amends: delegated-mode.md`) records why the detour is a record and the park two ledger words; `delegated-mode.md` gains an "Amended on 2026-09-15" note under its header quote naming decision 4; `knowledge/decisions/index.md` gains one line. | 1, 2 | `python3 scripts/check_okf.py` ends `OKF: <n> docs, 0 warnings`; `grep -c 'Amended on 2026-09-15' knowledge/decisions/delegated-mode.md` is 1. |
| R-10 | **All green.** | 8 | `scripts/verify.sh` ends `VERIFY: PASS (<sha>)`; `python3 scripts/check_artifact_chain.py --base origin/main --slug risk-detour` ends `CHAIN: PASS`; `scripts/run_evals.sh` ends `EVALS: N pass, 0 fail, ...`; `python3 scripts/check_okf.py` ends `0 warnings`. |

## Design
### Architecture / data flow
1. **Trigger.** At each gate the skill runs `python3 scripts/check_detour.py <source>`. The script loads
   `<root>/.sdlc/delegation.yaml` through `delegation.load(path=...)` and `<root>/.sdlc/config.env` through
   `delegated_merge.load_config(root)`, builds `prefixes = delegated_merge._locked_paths(config, policy, slug)`
   and, per candidate path, calls `delegated_merge.check_locked_paths([{"filename": p}], prefixes)`. `REFUSED`
   names the prefix in its reason (`"%s is under the locked path '%s'"`); the label is a set lookup of that
   prefix in `PROTECTED_PATHS`, `RELEASE_GATED_PATHS`, the policy's `locked-paths`, `ALWAYS_LOCKED` and the
   item's intent, every list it appears in, comma-joined. Nothing about the matching rule is re-implemented.
2. **Record.** `needed` convenes the reviewers. The writer drafts `work/<slug>/revisions/<n>.md` from the
   template with `kind: detour`, `trigger:` quoting the `DETOUR:` output, `## Route` answering the five route
   questions, and one `## Reviewer: <role> (<model>)` section per reviewer, each ending `verdict: revise` or
   `verdict: keep`. Reviewers are `plan-reviewer` and `security-reviewer` subagents on a different model from
   the writer; a second Claude model when no other is on the machine (Q3).
3. **Adopt.** Unanimous `revise`: the artifact is amended to the route and re-signed with
   `python3 scripts/sign.py <slug> <artifact> --revision revisions/<n>.md --note "detour: <route>"`, whose
   ledger note `sign.py` writes as `revision <n>: detour: <route>` (its `f"revision {n}:" + f" {note}"`
   shape, unchanged). At the intent-drafting gate the record is filed and ledgered as
   `intent.md | in-review -> in-review | claude | <sha> | revision <n>: detour: <route>` and nothing is
   re-signed (Q6). Any `keep`: the record is closed; a changed route is a new record; the second closed record
   at the same gate parks (Q2).
4. **Park.** Two ledger words carry the state: `parked:` and `resumed:` notes on `intent.md` lines, latest
   wins. The agent appends `- <ts> | intent.md | approved -> approved | claude | <sha> | parked: revision <n>:
   <why>; remainder: <slug>-supervised`, regenerates the indexes, commits the record with it, and opens the
   item's own pull request (`Work-Item: <slug>`, `claude/` branch, ready once local checks are green). The
   diff is own artifacts only, so the merge workflow merges it and `advance()` moves the pointer past the
   parked item (R-3 skips it, `exclude` removes it) to the next queued item, writing its two ledger lines,
   with no human commit between the park and the advance. The owner resumes by appending
   `- <ts> | intent.md | approved -> approved | luissiviero | <sha> | resumed: <why>` from the web editor.
5. **Remainder.** `/sdlc-intent <slug>-supervised` drafts the non-low remainder from the record's route
   section: `mode: supervised`, `risk-class:` the record's class, `detour-of: <slug>`, in its own branch and
   draft pull request, which may run beside the park pull request (an intent-only one always may).
6. **Index.** `gen_index.build_item` calls `next_item.parked_note(entries)`; `render_top_index` writes
   `parked` in the `stage` cell and `render_item_index` a `Parked: <note>` line when it is set.

### Interfaces (APIs, events, schemas) — exact shapes
- `scripts/check_detour.py [--root DIR] [--slug SLUG] (--paths P... | --plan FILE | --diff BASE)`
  - stdout, one line per locked path, in input order, then the verdict line:
    ```
    .claude/skills/sdlc-run/SKILL.md: locked by ALWAYS_LOCKED '.claude'
    .sdlc/active: locked by PROTECTED_PATHS, ALWAYS_LOCKED '.sdlc'
    scripts/sign.py: locked by locked-paths 'scripts/sign.py'
    migrations/0007.sql: locked by RELEASE_GATED_PATHS 'migrations'
    work/risk-detour/intent.md: locked by this item's intent 'work/risk-detour/intent.md'
    DETOUR: needed (5)
    ```
    or `DETOUR: none`. Exit 0 none, 3 needed, 2 bad input (`check-detour: <reason>` on stderr, no
    `DETOUR:` line).
  - `--plan`: bullets under `## Files that change` up to the next `## `, each `- <path> — ...`; the path is
    the text before the first ` — ` (or the whole bullet when there is none), a `*`/`?`/`[` glob expanded
    with `glob.glob(pattern, root_dir=root, recursive=True)`, the literal kept when nothing matches.
  - `--diff BASE`: `git -C <root> diff --name-only --diff-filter=ACMRD -M <BASE>...HEAD --`, plus
    `--name-status` for renames so both names are candidates; `BASE` must pass `git rev-parse --verify
    --quiet <BASE>^{commit}` or exit 2.
  - API: `locked(paths, root, slug=None) -> list[(path, labels, prefix)]`, `verdict(hits) -> (line, code)`,
    `plan_paths(plan_file, root) -> list[str]`, `diff_paths(root, base) -> list[str]`.
- `next_item.parked_note(entries) -> str | None`: `entries` are `log_ledger.Entry`s; only `artifact ==
  "intent.md"`; `note.strip().startswith(("parked:", "resumed:"))`; the last such entry decides;
  `parked:` returns the stripped note, `resumed:` or none returns `None`. `_eligible` reason:
  `"parked: <note without the parked: prefix>"`.
- Ledger lines (from/to hold status values only):
  - park: `- <ts> | intent.md | approved -> approved | claude | <sha> | parked: revision <n>: <why>; remainder: <slug>-supervised`
  - click-locked park: `- <ts> | intent.md | approved -> approved | claude | <sha> | parked: ready PR #<n>; click needed (<path>)`
  - resume: `- <ts> | intent.md | approved -> approved | luissiviero | <sha> | resumed: <why>`
  - detour adopted on a signed artifact: written by `sign.py --revision`, note `revision <n>: detour: <route>`
  - detour adopted at the intent gate: `- <ts> | intent.md | in-review -> in-review | claude | <sha> | revision <n>: detour: <route>`
- `docs/sdlc/templates/revision.md` front matter: `kind: revision` with the comment
  `# kind: revision | detour  (detour: the trigger is a DETOUR: needed line, the proposal is a route that stays low)`;
  body: `## Proposal` (kept), `## Route (detour only)` with five sub-bullets (outcome reached, paths and their
  lists, why low, remainder, what goes stale), and each `## Reviewer:` section's text gains the detour
  question set in one sentence beside the existing three.
- `docs/sdlc/templates/intent.md` front matter: `# detour-of: the slug of the parked item this intent is the
  remainder of, if any` and `detour-of:` after `supersedes:`.
- `docs/sdlc/templates/log.md`: one more example line, the park shape above.
- `work/index.md` row for a parked item: `| [slug](slug/index.md) | <title> | parked | approved | — | — | intent.md -> approved by claude |`;
  `work/<slug>/index.md`: the line `Parked: parked: revision 1: ...` inserted before `Last gate:`, with a
  blank line between.

### Data and migrations
None. No schema, no personal or regulated data; every new field is a Markdown front-matter key or a ledger
note in a committed file. `security-standards` §4 n/a.

### Failure modes and how they surface
- **The check cannot read its inputs**: exit 2 with a `check-detour:` line; no `DETOUR:` line, so a skill
  that greps the last line sees neither answer and stops. A plan without `## Files that change` is exit 2,
  not `none`: silence must never read as clean.
- **A path is locked and the route stays locked**: the second closed record parks; the run continues at
  step 7 with the pointer moved by the park pull request's merge. If that merge waits (no `pr-review`
  credential, a red check), the park pull request is the callback exactly as an item's pull request is
  today; the pointer does not move until it merges, and the session says so.
- **The park pull request cannot merge under the workflow** because the item's spec or plan is not yet
  signed (a park before the spec): the chain is in in-progress mode and passes on an intent alone (as
  #60 and this item's own opening did), so the merge is not blocked by the chain; `require-review` still
  needs `Important: 0`, which a diff of `work/` files draws (the false `Important` is on `.claude/` and
  `CLAUDE.md` diffs only).
- **A `parked:` line whose record is missing**: the queue still skips the item (R-3, third case); the chain
  check is silent because `check_revisions` runs only on `delegated` artifacts and `intent.md` never is. The
  owner reads the park in the index and the ledger.
- **The owner resumes**: a `resumed:` line after the `parked:` one re-queues the item at its `delegated-on`
  order; a second `parked:` after that parks again. Ordering is file order; the ledger is append-only.
- **The advance lands on the parked item anyway**: only if `next_item.py` on `main` predates R-3; the
  workflow runs `main`'s copy, so this holds until this item merges and not after. Until then the run skill
  says a park's advance is unproven in production.
- **The adopter's context file exceeds the cap**: `gen_context_files.py` exits 1 for the kit's own files
  only; the adopter's is measured by hand (R-8) because its seeded sections add twelve lines above the block.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: this item's own pull request touches `.claude/skills`, `docs/sdlc/templates` and `docs/sdlc/rules`,
  all on `ALWAYS_LOCKED`, so the delegated merge refuses it and the owner merges by click — policy:
  `knowledge/decisions/delegated-mode.md` decision 6 — contradiction? no — owner: luissiviero —
  resolution: the intent's first answer: finish to a ready pull request and park with `parked: ready PR
  #<n>; click needed (<path>)`. The park line for *this* item is written only once `check_detour.py` and
  R-3 exist on the branch, in the pull request itself, since a ledger-only second pull request would be
  judged by `main`'s `next_item.py` and its advance would be a no-op on an empty queue anyway.
- C2: a park's advance depends on `pr-review` posting `Important: 0` for a `work/`-only diff — policy:
  `delegated-mode.md` consequences, "the advisory reviewer cannot see a pull request's own changes to
  `.claude/` or `CLAUDE.md`" — contradiction? no, a park diff touches neither — owner: luissiviero —
  resolution: accepted; a waiting park is the same callback shape as any waiting delegated merge.
- C3: `scripts/check_detour.py` runs `git diff` with a user-supplied base — policy: security-standards §3
  — contradiction? no — owner: luissiviero — resolution: the base is verified with `git rev-parse --verify
  --quiet <base>^{commit}` first, passed after `--` is impossible for a revision so it is passed as a
  single argv element, never through a shell; paths are printed, never executed or interpolated into a
  command.
- C4: `next_item.py` is read by the advance and is not on `locked-paths` — policy: `.sdlc/delegation.yaml`
  is the owner's file — contradiction? no — owner: luissiviero — resolution: Q5, the owner adds it after
  this item merges; this item does not touch `.sdlc/`.

## Open questions carried from intent.md
- none: all six are answered on the intent and applied above (Q1 → R-7 and C1, Q2 → R-7, Q3 → R-7, Q4 → R-6,
  Q5 → C4, Q6 → R-7 and design step 3).

## Decisions (ADR-style: context → decision → consequences)
- D1: one record type, not two. Context: `sign.py` and the chain check read `## Reviewer:` and `verdict:` and
  nothing else, and both are locked. Decision: a detour is a revision record with `kind: detour` and a `## Route`
  section. Consequences: the judging scripts see the same file they see today; `kind:` is advisory, read by
  people and by the run skill; a future strict reader can key on it.
- D2: the trigger reuses the merge's matcher by call, not by copy. Context: the intent names "the one matcher
  the merge script already uses" and the lesson `one-path-spelling-in-guards.md`. Decision: `check_detour.py`
  imports `delegated_merge` and calls `check_locked_paths` per path, `_locked_paths` for the prefixes,
  `load_config` for the config; only the label (which list the prefix sits in) is computed locally, as a set
  lookup on the prefix the matcher returned. Consequences: importing `delegated_merge` is cheap (argparse and
  stdlib at module level, no network until `main`); a matcher change on `main` changes the check the same
  day; the label parses the matcher's reason string, which a test pins so a reworded reason fails loudly.
- D3: a park is two ledger words, latest wins. Context: `STATUSES` is closed, the intent may carry no new
  front-matter key from an agent, `protect-approvals.sh` guards the grant keys. Decision: `parked:` and
  `resumed:` notes on `intent.md` ledger lines, `approved -> approved`, the shape the advance already writes
  on intents. Consequences: no hook or judging script changes; `log_ledger.approvals()` counts the line, which
  nothing reads for `intent.md` except `test_approve.py`'s own fixture; the owner's resume is one web-editor
  line.
- D4: the park lands through the merge's own advance. Context: a session never writes `.sdlc/active`, and the
  only mover on a merge is `advance()`. Decision: the park is the item's own delegated pull request, own
  artifacts only. Consequences: no human commit between park and advance (R-4); the remainder intent must ride
  separately (strict mode otherwise); the pointer moves only when that pull request merges.
- D5: click-locked routes finish and park from a second pull request. Context: Q1, and `check_pull_request`
  counts open pull requests by head sha, not by slug. Decision: the code pull request stays ready for the click;
  a ledger-only pull request carries `parked: ready PR #<n>; click needed (<path>)` and merges under the
  workflow. Consequences: the pointer moves before the click; the click later merges a pull request whose slug
  the pointer no longer names, which is the human path and needs no gate.
- D6: the index says `parked` where the owner looks first. Context: Q4. Decision: the `stage` cell, and a
  `Parked:` line on the item index. Consequences: the stage the item reached is one click away on its own
  index; the top table stays seven columns.
- D7: rounds are two records per gate. Context: Q2; "as many agents as necessary" is rounds, not a wider
  panel. Decision: a split record closes, a changed route is a new record, the third trigger at one gate parks.
  Consequences: at most two records per gate per item until `max-detours` arrives with `standing-grant`.
- D8: no net line in a claude-targeted fragment. Context: the adopter's `CLAUDE.md` renders at 120, the cap
  (measured 2026-09-15). Decision: rewrite the two existing bullets that describe the run and the delegated
  ledger words. Consequences: R-8's numbers are the acceptance test; a third line is a deviation.

## Gotchas found while reading the codebase
- G-1: `check_artifact_chain.config()` reads `ROOT`, not an argument; `delegated_merge.load_config(root)` swaps
  the module global for one call. Use it, or every fixture reads the kit's own `config.env`.
- G-2: `check_locked_paths` returns on the *first* locked file; call it once per path to name every hit.
- G-3: `check_pull_request` requires exactly one open pull request *with this head sha*; two open pull requests
  for one slug on two branches pass it, which is what D5 stands on.
- G-4: `log_ledger.signatures()` is `to_status == "delegated"` and `approvals()` is `to_status == "approved"`;
  a park line is neither a signature nor a re-sign, so `check_revisions` never sees it; keep the park on
  `intent.md`, never on `spec.md` or `plan.md`, or the re-sign rule would demand a record.
- G-5: `sign.py` builds the re-sign note as `revision <n>:` plus a space and `--note`; `--note "detour: <route>"`
  is the intent's `revision <n>: detour: <route>`; a note starting `deviation:` would be counted as a deviation
  by `check_deviations`, so a detour note never starts with that word.
- G-6: an eval `check:` block ends at the first unindented line, and a blank line is unindented
  (`knowledge/lessons/eval-checks-have-no-blank-lines.md`); a negated assertion needs `|| exit 1`.
- G-7: `test_gen_index.py`'s three golden strings pin bytes of a two-item tree; a new fixture item there would
  change `GOLDEN_TOP_INDEX`. The parked case gets its own tree.
- G-8: the adopter's `CLAUDE.md` is exactly `MAX_CONTEXT_LINES` today (120; `GEMINI.md` 119, `AGENTS.md` 99).
- G-9: `next_item.py`'s docstring mentions `--list --why`, which the CLI does not have; the `_eligible` reason
  strings reach tests only.
- G-10: the container's chain check crashes on a set `GH_TOKEN` with no `gh` binary (a filed defect); run
  `verify.sh` and the chain check with `env -u GH_TOKEN -u GITHUB_TOKEN` here. A shallow clone misattributes
  approvals; this session unshallowed first.
- G-11: `PLAN_REQUIRED_PATHS` is `scripts`, so every script in this item waits for the signed plan; the skills,
  templates, rules and knowledge files do not, but are written in the same pull request after it anyway.

## Not doing
- `max-detours` as a policy key, an agent-written or revisited `risk-class`, a dedicated detour-reviewer role,
  hook protection of `risk-class`: `work/standing-grant`.
- Any change to `check_artifact_chain.py`, `sign.py`, `delegated_merge.py`, `delegation.py`, `log_ledger.py`,
  the hooks, the workflows, `.sdlc/`, `.gemini/` (protected; the Gemini agent copies stay as they are).
- Adding `scripts/next_item.py` to `locked-paths` (Q5, the owner's edit after the merge).
- A `--why` flag on `next_item.py`, or printing parked items in `--list`.
- Making the advance recognise a park pull request specially: it is an ordinary delegated merge.
- Updating `docs/sdlc/README.md`'s stage table; the run skill and the decision record are the reference.
