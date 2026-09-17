---
type: sdlc/plan
id: self-check-false-reds
title: Three red modules first, then the three fixes in the order the spec numbers them
description: "Three new test modules, each committed red on its own (kind fix locks every existing one), then check_artifact_chain.py gains a slugless EXEMPT decision after the diff guards and a graft predicate on both -G lookups, then advance() in delegated_merge.py regenerates exactly the three indexes it dirties; every judging suite stays green unmodified as the net, and the owner merges by click."
stage: build
# status: draft | in-review | approved | delegated | superseded  (require-plan.sh refuses code edits until approved)
status: approved
# kind: feature | fix  (fix: protect-tests.sh refuses edits to existing test files)
kind: fix
reads: spec.md
# approved-by: engineer for routine; tech lead/architect for medium/high risk; set only by a human
approved-by: luissiviero
approved-on: 2026-09-15
risk-class: medium
record:
resource: https://github.com/luissiviero/lifecycle-axis-/pull/104
tags: [chain-check, delegated-merge, advance, shallow-clone, gen-index, fix, defect-1]
timestamp: 2026-09-15T15:05:00Z
---
# Plan: three red modules first, then the three fixes in the order the spec numbers them (from intent.md 2026-09-15)

`kind: fix`, as the intent requires: `protect-tests.sh` locks every existing test file and eval case for the
life of this plan, so all eight regression cases live in three new modules the hook leaves writable. Each
module composes the fixtures of the suite it sits beside by import, the way `scripts/test_park_advance.py`
composes `test_delegated_merge`'s and `scripts/test_gen_index_retired.py` composes `test_gen_index`'s, so a
renamed helper fails loudly at import rather than passing silently.

No engineer interview: the owner is the only human and works from a phone, so the repository's own record
stood in for it — `CLAUDE.md`, the two suites this touches (`scripts/test_check_artifact_chain.py`,
`scripts/test_delegated_merge_advance.py`), and the spec's five gotchas. Two facts from that reading shape
the order below: `require-plan.sh` keeps every code edit closed until this plan is approved, so nothing in
steps 1–6 happens before the tap; and the three fixes are independent of one another, so each lands with
its own module going green while the other two modules' red cases stay red, which is the proof that a fix
fixes only its own fault.

## Files that change
- scripts/test_chain_no_slug.py — new; `class NoSlug` on `test_check_artifact_chain._make_repo` / `_run` / `_last_line`: `test_empty_pointer_and_exempt_diff_is_a_note` (pointer emptied and committed, one commit touching only `docs/note.md`, `--base <the commit before>`; expects `CHAIN: PASS`, exit 0, a `note:` naming the empty pointer) — **red today**, exit 1 at `:528`; `test_empty_pointer_and_code_diff_still_fails` (same, the commit also touches `scripts/foo.py`; expects today's `FAIL: no active work item` line, exit 1) — green today, a pin; `test_explicit_slug_naming_nothing_still_fails` (`--slug no-such-item`; exit 1) — green today, a pin (spec R1, R2, R3, D1, D2)
- scripts/test_chain_shallow.py — new; `class Graft`: `test_shallow_boundary_is_a_note_not_an_approver` (`_make_repo`, one more commit authored `github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>` touching `README.md` so the boundary is an agent's, then `git clone --depth 1 file://<root>` and the check run *inside the clone* with `--slug demo --base HEAD`; expects `CHAIN: PASS` and a `note:` containing `history is shallow at <sha12>`) — **red today**, three agent-identity FAILs; `test_full_clone_still_catches_an_agent_approval` (the same repo, un-cloned, with `status: approved` genuinely committed by the agent identity, as `ApprovalAuthor` does; expects the FAIL it gets today, and no shallow note) — green today, **the pin that R4 cannot become a bypass**; `test_the_check_never_fetches` (a `git` shim first on `PATH` that appends its argv to a log and execs the real `git`; runs the shallow case through it; asserts no argv line contains `fetch`, `clone`, `pull` or `remote`, and `git status --porcelain` is byte-identical before and after) — green today, a pin (spec R4, R5, R6, D3, D4)
- scripts/test_advance_regenerates_index.py — new; `class RegeneratesIndex(test_delegated_merge_advance.MovingRemote)` reusing its bare remote, checkout, second clone, policy and `_move_remote`; `setUp` additionally copies the real `.sdlc/approvers.yaml` in (G-1 below) and writes every index from `gen_index.render_all` so drift is zero before the advance, then overwrites `work/later-item/index.md` with one stale line; `test_advance_regenerates_exactly_what_it_dirties` (after `advance()`: `render_all` content equals the on-disk file for `work/merged-item/index.md`, `work/next-item/index.md` and `work/index.md`; `work/later-item/index.md` still holds the stale line; `git show --name-only --format= HEAD` in the checkout is exactly `{.sdlc/active, work/merged-item/log.md, work/next-item/log.md, work/merged-item/index.md, work/next-item/index.md, work/index.md}`) — **red today**, the two ledgers' indexes drift; `test_the_allowlist_is_still_closed` (a path outside the allowlist staged before `advance()`; expects `MergeError` naming it and an empty `git diff --cached`) — green today, a pin (spec R7, R8, D5, D6)
- scripts/test_check_artifact_chain.py — the owner's own edit: `ActiveSlugRequired`'s two cases expect the
  note instead of the `FAIL` (both renamed `..._is_one_clear_note`). Locked to agents under `kind: fix`, so a
  human changed it, as the hook's message directs; listed here because it is in the diff (deviation 3)
- scripts/check_artifact_chain.py — (a) the diff and its two fail-closed guards at `:556-598` move into `_changed_paths(base) -> list[str]`, called once right after the boundary validation at `:527` and before anything reads `slug`; the no-slug decision at `:528-531` then reads the result: every path starting with an `EXEMPT` prefix → the note and `CHAIN: PASS`, exit 0; otherwise today's `FAIL` line unchanged. `changed_all` below is the returned list, not recomputed. (b) `_is_graft(sha) -> bool`: reads the file `git rev-parse --git-path shallow` names, returns `sha in lines`, and `False` when the file is absent or unreadable; at `:386` and `:833`, when `who` is non-empty and `_is_graft(sha)`, take the existing "author check skipped" note branch with the message `history is shallow at <sha12>; the author check needs the real approval commit -- run git fetch --unshallow origin`. No new exit path. The module docstring's `evals/` sentence at `:23` is **not** touched (spec, Not doing) (spec R1–R6, D1–D4)
- scripts/delegated_merge.py — `import gen_index` beside the `chain` import (lazy is unnecessary: `gen_index` imports `next_item`, not this module); in `advance()` after the ledger appends at `:1150-1163` and before `_git(root, "add", ...)` at `:1164`: build `touched = {work/<merged>/index.md, work/index.md}` plus `work/<next>/index.md` when `nxt`, iterate `gen_index.render_all(root)`, write and `written.append` only the paths in `touched`. The allowlist check at `:1164-1170` is untouched. One sentence in `advance()`'s docstring says the indexes it dirties are regenerated in the same commit (spec R7, R8, D5, D6)
- work/self-check-false-reds/plan.md — this plan; its deviations log
- work/self-check-false-reds/log.md — one ledger line per gate
- work/self-check-false-reds/index.md — regenerated
- work/index.md — regenerated

Not in the list, on purpose: `scripts/gen_index.py` (spec D6: `render_all` is reused as it is, no new seam);
`scripts/next_item.py` (read by `advance()`, changed by no requirement); `scripts/verify.sh`, the hooks, the
workflows and `.sdlc/` (intent, Must not); `scripts/test_check_artifact_chain.py`,
`scripts/test_delegated_merge.py`, `scripts/test_delegated_merge_advance.py`, `scripts/test_park_advance.py`
and every other existing test module (locked under `kind: fix`, and their staying green *unmodified* is the
net under steps 4–6).

## Release-gated
(none) — no path under `RELEASE_GATED_PATHS` (`migrations infra terraform helm`) is touched.

`python3 scripts/check_detour.py --slug self-check-false-reds --plan work/self-check-false-reds/plan.md`
returns **`DETOUR: needed (2)`**: `scripts/check_artifact_chain.py` and `scripts/delegated_merge.py` are on
the policy's `locked-paths`. Per the skill's step 5 for a supervised item: **the merge is the owner's click.**
The delegated-merge workflow refuses any pull request whose diff touches a locked path, and this item is
`mode: supervised` in any case. No `control-plane-approved` label is needed: `scripts/check_control_plane.sh:55`
guards `PROTECTED_PATHS` only, and neither file is in that list — `locked-paths` and `PROTECTED_PATHS` are
different lists with different enforcers (measured; an earlier session message claimed the label would be
needed and was wrong).

## Order of work (each step independently verifiable)
1. **The no-slug module, red.** Draft `scripts/test_chain_no_slug.py` in the scratchpad against the
   repository's `check_artifact_chain`, then place it (G-2: the hook locks the file the moment it exists
   under this plan). Verify: `python3 -m unittest discover -s scripts -p test_chain_no_slug.py` shows
   exactly **one** failure — R1's case, on exit code 1 and the `FAIL: no active work item` line — and R2,
   R3 green (`knowledge/lessons/a-verifiable-command-fails-before-the-change.md`). Commit the red module on
   its own so the record holds it.
2. **The graft module, red.** Same for `scripts/test_chain_shallow.py`. Verify: exactly **one** failure —
   R4's case, on three `authored by an agent identity` lines — and R5, R6 green. Commit red on its own.
3. **The advance module, red.** Same for `scripts/test_advance_regenerates_index.py`. Verify: exactly **one**
   failure — R7's case, on the two drifted indexes and the six-path commit list — and R8 green. Commit red
   on its own. After this step every existing suite is still green and untouched; the three commits are the
   baseline the next three steps are measured against.
4. **Fix (a).** `_changed_paths` extracted, the no-slug decision moved and made `EXEMPT`-aware. Verify:
   `test_chain_no_slug.py` fully green; `test_chain_shallow.py` and `test_advance_regenerates_index.py` each
   **still one red** (the fix touched nothing of theirs); `python3 -m unittest discover -s scripts -p
   test_check_artifact_chain.py` green unmodified, in particular the base-ref and dirty-tree cases, which
   now run *before* the pointer is judged (D2) and must still produce their own `FAIL` line first.
5. **Fix (b).** `_is_graft` and the two call sites. Verify: `test_chain_shallow.py` fully green;
   `test_advance_regenerates_index.py` still one red; `test_check_artifact_chain.py` green unmodified, in
   particular `ApprovalAuthor` and `DispatchAttestation`, the two classes that would notice a widened skip.
6. **Fix (c).** The import, the scoped regeneration, the docstring sentence. Verify:
   `test_advance_regenerates_index.py` fully green; `test_delegated_merge.py`,
   `test_delegated_merge_advance.py`, `test_delegated_merge_advance_review.py` and `test_park_advance.py`
   green unmodified.
7. **The whole loop, and the two production shapes.** `python3 scripts/gen_index.py`, `git add` every
   changed file (`knowledge/lessons/stage-new-files-before-verify.md`), `scripts/verify.sh`, commit, then
   `python3 scripts/check_artifact_chain.py --base origin/main --slug self-check-false-reds`
   (`knowledge/lessons/commit-before-the-chain-check.md`), `scripts/run_evals.sh`, `python3 scripts/check_okf.py`,
   `python3 scripts/check_detour.py --slug self-check-false-reds --diff origin/main` (expect `needed (2)`).
   Then the two shapes the intent measured, on this branch's own code: a depth-1 clone of the branch, the
   check run inside it with `--slug self-check-false-reds --base HEAD` → `CHAIN: PASS` with the graft note;
   and a scratch commit that empties `.sdlc/active` and touches only `docs/`, checked with `--base HEAD^` →
   `CHAIN: PASS` with the empty-pointer note. Both outputs pasted into the pull request.
8. **Draft pull request, review, ready, click.** Open the draft on `claude/self-check-false-reds-code`,
   `[self-check-false-reds]` in the title, `Work-Item: self-check-false-reds` in the body, the last lines of
   step 7 and the three red runs of steps 1–3 pasted. `/sdlc-review` with `plan-reviewer` and
   `security-reviewer` on a model other than the writer's; fix what they find with evidence; post
   `Important: 0 | Nits: <m>`; mark ready. **The owner merges by click** — no delegated merge, no label
   (Release-gated above). `sdlc-run` step 7 follows: this session refreshes the handoff's Task state and
   seed prompt, and the pointer moves at the owner's next tap, not by this session.

## Risks
- Risk: the graft skip in (b) becomes a way to hide a genuine agent approval → mitigation: R5's case commits
  `status: approved` *as the agent* on a full clone and requires today's FAIL, and it is in the same module as
  R4, so the two cannot go green independently; `_is_graft` is `False` whenever the shallow file is absent,
  so a full clone cannot enter the branch; CI is `fetch-depth: 0` (`sdlc-gate.yml:46`), so no pull request
  can make the gate's clone shallow (spec C1).
- Risk: (a)'s reorder changes which `FAIL` a broken checkout reports first (D2) → mitigation: the existing
  base-ref and dirty-tree cases in `test_check_artifact_chain.py` are locked and must stay green unmodified
  (step 4); both paths stay exit 1, so no caller's verdict flips, only the line.
- Risk: (c)'s regeneration sweeps an unrelated stale index into an unattended bot commit → mitigation: the
  write is filtered to the three paths and R7 plants a deliberately stale fourth index and asserts it is
  left alone; the allowlist is extended only by paths actually written, and R8 pins that anything else
  still raises `MergeError` (spec C2, D6).
- Risk: `render_all` raises on the advance fixture because `build_item` reads `.sdlc/approvers.yaml` through
  `next_item.resumers` and the fixture has none (G-1) → mitigation: the module's `setUp` copies the real file
  in, exactly as `test_check_artifact_chain._make_repo` does with `REAL_APPROVERS`.
- Risk: the shallow fixture clones through `file://` and a git version refuses `--depth` over a local path
  → mitigation: `file://` (not a bare path) is what forces the smart transport that honours `--depth`; this
  session measured it on this container's git. If a runner's git differs, the case skips with a reason
  rather than passing vacuously (`unittest.SkipTest` naming the git version).
- Risk: the step-7 shapes pass locally and the gate still goes red → mitigation: the gate runs the same
  script against `origin/<base>`; step 7 runs exactly that command before the push.
- What this could break: the two scripts that judge every merge and every signature. That is why each fix
  lands only after its own module is red, why the other two modules must *stay* red across it, and why every
  existing suite for both scripts is locked and required green unmodified.
- Options considered and not taken: a hard-coded index triple in `advance()` (D5: computed, or it drifts);
  `git fetch --unshallow` from inside the check (R6 forbids it; a verification step must not mutate its
  subject); relaxing R7's test to a subset (D6: it would have hidden a 29-path allowlist); adding cases to
  the existing modules (locked under `kind: fix`); a single new module for all eight cases (three faults,
  three fixes, three independent red-to-green transitions is the proof the plan is built on).

## Proof
- `scripts/verify.sh` green, ending `VERIFY: PASS (<sha>)`; `CHAIN: PASS`; `EVALS: <n> pass, 0 fail`; `OKF: 0 warnings`; `INDEX: up to date`
- Spec rows → tests: R1 → `NoSlug::test_empty_pointer_and_exempt_diff_is_a_note`; R2 →
  `NoSlug::test_empty_pointer_and_code_diff_still_fails`; R3 → `NoSlug::test_explicit_slug_naming_nothing_still_fails`;
  R4 → `Graft::test_shallow_boundary_is_a_note_not_an_approver`; R5 →
  `Graft::test_full_clone_still_catches_an_agent_approval`; R6 → `Graft::test_the_check_never_fetches`;
  R7 → `RegeneratesIndex::test_advance_regenerates_exactly_what_it_dirties`; R8 →
  `RegeneratesIndex::test_the_allowlist_is_still_closed`
- The three red runs of steps 1–3 pasted beside the green run, one failure each, on the lines named above
- `git diff origin/main --numstat -- scripts/test_check_artifact_chain.py scripts/test_delegated_merge.py scripts/test_delegated_merge_advance.py scripts/test_park_advance.py scripts/gen_index.py scripts/next_item.py` empty
- `python3 scripts/check_detour.py --slug self-check-false-reds --diff origin/main` → `DETOUR: needed (2)`, the two locked scripts and nothing else
- Manual / browser / screenshot / eval: the two step-7 production shapes, pasted; after the merge, the next
  delegated merge with an empty queue leaves `main` green — the production observation the intent was
  written for, recorded in the handoff's next Task state rather than here.

## Rollback
Revert the commits. `check_artifact_chain.py` returns to failing on an empty pointer and reading the graft
as an approver; `advance()` returns to committing the pointer and ledgers only; the three new modules go with
the revert. No data, format, policy or workflow change persists; `gen_index.py` and `next_item.py` were never
touched; `.sdlc/active` was never moved by this item. Both scripts are locked paths, so the revert is itself
an owner's click.

## Deviations log (append during implementation; same commit as the deviation)
- 2026-09-15 — step 3: the `scripts/test_advance_regenerates_index.py` bullet named the base class
  `AdvanceAfterRemoteMoved`; the fixture class in `scripts/test_delegated_merge_advance.py` is `MovingRemote`.
  The bullet is corrected in this commit. No path, step, requirement or acceptance test changed; the module
  composes the fixture the plan describes, by subclassing as `test_park_advance.py` does. Also found while
  drafting R8: `advance()` fast-forwards onto the merge commit before it writes, so a refusal leaves HEAD
  at the merge commit, not at the pre-advance tip; the case pins `merge_sha`, which is what the spec's
  "nothing committed on top" means. 1 of 5 (supervised: a human re-approves only a plan *revision*, and
  this is not one).
- 2026-09-15 — step order: fix (b) lands before fix (a), and fix (a) is held. Fix (a) was applied and
  verified per step 4 -- `test_chain_no_slug.py` green, `test_chain_shallow.py` and
  `test_advance_regenerates_index.py` still one red each -- but it turns two cases of the locked
  `scripts/test_check_artifact_chain.py` red: `ActiveSlugRequired`'s empty-pointer and missing-pointer cases
  (`work/delegated-mode` R-6) run `--base HEAD` and assert exit 1 on exactly the `FAIL: no active work item`
  line that spec R1 replaces with a note. They are not wrong tests; they pin the rule this spec supersedes,
  and R-6's intent (one clear line, not a cascade) still holds as one clear note. Under `kind: fix` the hook
  forbids editing them and says a human changes them, so step 4's proof ("green unmodified") cannot hold
  as written. Fix (a) is kept as a patch pending the owner's edit of those two cases; fixes (b) and (c)
  proceed in the meantime. No requirement, design line or acceptance test of this item changed; the
  locked suite's expectation is what changed, by the approved spec. 2 of 5.
- 2026-09-17 — `scripts/test_check_artifact_chain.py` joins the file list, and fix (a) lands. The owner
  edited `ActiveSlugRequired`'s two cases by hand (`5dc6c0c`, `6b24c62`), which deviation 2 said was the
  only way past the `kind: fix` lock: both now expect exit 0, `CHAIN: PASS`, exactly one
  `note: no active work item` line and zero `FAIL:` lines, and both are renamed `..._is_one_clear_note`.
  The file is therefore in this pull request's diff and belongs in this list, though no agent wrote it.
  With the held patch applied the suite is 94 OK and every other locked suite is green unmodified. No
  requirement, design line or acceptance test of this item changed; `work/delegated-mode` R-6's intent
  (one clear line, not a cascade) still holds as one clear note, which is spec R1. 3 of 5.
