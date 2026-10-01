---
type: doc
title: "Evidence: fresh-reader cross-check of the draft"
description: "A third model read only the committed files and checked coverage, citations, unsupported claims, internal contradictions and counts; the source of the corrections listed in Appendix E."
tags: [sdlc, revision, evidence, review]
timestamp: 2026-09-10T17:00:00Z
---
# Cross-check: `docs/sdlc/revision/2026-09-10-step-review.md`

Fresh-reader review. No repository file was edited. All verdicts below are backed by a citation to a
repository file, an evidence file, or a command run during this check (see Coverage at the end).

---

## 1. COVERAGE

**Row identity.** A structural diff (parsed both markdown tables by row number, respecting `\|`
escapes) confirms Table 1 carries exactly rows 1–164, no gaps, no duplicates, in the same order as
`evidence/steps.md`'s three tables (Lens A 1–110, Lens B 111–139, Maintain 140–164 — identical ranges
in both documents).

- **Missing/renumbered rows: none.** Every number 1–164 appears exactly once in both files.
- **Step text: no row was found where the draft's one-line step description names a different action
  than `steps.md`'s "Step" column for the same number.** The draft's column is a compressed
  paraphrase (it drops the leading path segments, e.g. `sdlc-intent/SKILL.md` for
  `.claude/skills/sdlc-intent/SKILL.md`) but the action described matches in every row I checked,
  including a full read of rows 1–110 and spot checks across 111–164.
- **Citation accuracy is a different matter — see §2.** A structural diff of same-file line numbers
  between the draft and `steps.md`'s "Defined in" column turned up a **systematic off-by-one citation
  error** confined to four skill files: `.claude/skills/sdlc-spec/SKILL.md` (rows 28, 29, 31, 33),
  `.claude/skills/sdlc-review/SKILL.md` (rows 75, 76, 78, 79, 83), and
  `.claude/skills/sdlc-incident/SKILL.md` (rows 153, 154, 155) — twelve rows in all, each citing a
  line one lower than the line that actually carries the described step (verified against the files
  directly; detail and one worked example in §2). `sdlc-plan/SKILL.md` and `sdlc-intent/SKILL.md`
  citations in the draft were not affected. This is a citation-precision defect, not a step-identity
  defect: every one of these twelve rows still names the right file and the right action.
- **Change cell: non-empty in all 164 rows**, confirmed programmatically (no row parsed to an empty
  or missing 4th cell). Distribution: `keep` 97, `keep (note)` 18, `change` 28, `fix` 11, `drop` 8,
  `build` 1, `merge → 10` 1. Sum = 164.
- **Appendix A: all 30 questions (Q1–Q30) have a full answer in `evidence/answers.md`.** I read
  `answers.md` in full — every Q1–Q30 has a dedicated section with citations, and the draft's
  Appendix A row for each is a faithful short-form compression of that section (spot-checked Q1, Q2,
  Q5, Q10, Q19, Q20, Q25 word-for-word against the full answer).

## 2. CITATION CHECK

### The 11 `fix` rows

| Row | Verdict | Note |
|---|---|---|
| 18 | **partly** | `approve.yml:79-84` (the mechanism) is accurate. But the Why column's "misrouted twice" and the Current-state citation `ci-budget/log.md:15-16` are off: the actual misrouting narrative is at `work/ci-budget/log.md:17`, not 15–16 (line 15 is a routing note about *why* the tap can't run pre-merge, not the misroute event; line 17 is the event: "The approve run at 15:52 resolved its blank slug against the pull request's own branch… approve.py wrote nothing"). A second, independent instance is real but different in kind: `steps.md:44` cites `work/retire-active-pointer/intent.md:48-50`, which describes the risk in prose ("a supervised approval tap left with a blank `slug`… resolves to that finished item"), not a second confirmed misroute event. "Twice" is defensible only if a documented risk counts as an occurrence; the row's own citation does not support "twice" on its own. |
| 21 | **confirmed** | `scripts/approve_dispatch.py:16-27` — verified the trailers, author/committer split and staged-path allowlist exactly as described. |
| 48 | **confirmed** | `.sdlc/config.env:9` `PROTECTED_PATHS` verified to omit `.github/CODEOWNERS`, `.claude/skills/`, `.claude/agents/`, `REVIEW.md`, `.claude-plugin/` — matches `drift.md` §5 exactly. |
| 60 | **confirmed** | Read all four `.claude/agents/*.md`: every one carries `tools: Read, Grep, Glob, Bash` with no bound and no `model:` field — matches the row and `drift.md` §2. |
| 65 | **confirmed, and independently reproduced.** | Read `scripts/check_artifact_chain.py:196-203`: with `GH_TOKEN`/`GITHUB_TOKEN` set, it shells out to `gh` with no `FileNotFoundError` handling. This session itself has `GH_TOKEN`/`GITHUB_TOKEN` set and no `gh` binary (`command -v gh` → not found) — the exact failure condition the row describes, confirmed live, not just quoted from `drift.md` §1. |
| 78 | **partly** | Citation is `.claude/skills/sdlc-review/SKILL.md:10`; the actual delegation sentence ("Delegate the security pass to the `security-reviewer` subagent and the plan-conformance pass to the `plan-reviewer` subagent…") is on **line 9**. Line 10 is the *next* step ("Output findings exactly in REVIEW.md's format…"). `steps.md` cites the correct line 9. Content of the row is otherwise accurate. |
| 84 | **confirmed** | `docs/sdlc/rules/60-lessons.md:11` matches verbatim ("A mistake made twice becomes a file there and a pointer line here…"). Cross-checked `REVIEW.md:13` and `sdlc-review/SKILL.md:14`: both do say "add a line to CLAUDE.md 'Lessons learned'" — confirms the three-way contradiction the row fixes. |
| 97 | **confirmed** | `.github/workflows/delegated-merge.yml:31` lists `workflows: [sdlc-gate, agent-evals, pr-review]`; `.sdlc/delegation.yaml:52` `require-checks: [sdlc-gate, pr-review]` — the mismatch is exactly as described. |
| 100 | **confirmed (mechanism); the finding-1 statistic is not — see below.** | `scripts/delegated_merge.py:994-1000`: pushes without a prior fetch/fast-forward; a rejected push is only logged as a note. `git log origin/main --grep="Advance .sdlc/active"` returns nothing — independently confirmed no advance commit has ever landed on `main`. |
| 104 | **confirmed** | `docs/sdlc/rules/00-chain.md:23-24` and `.sdlc/approvers.yaml:26` (`never-approve: [..., "claude"]`) both verified directly; matches the row and `work/ci-budget/log.md:17`. |
| 125 | **confirmed** | `docs/sdlc/github-setup.md:65-78` verified to list `agent-evals` and "up to date: **on**" as required — matches the row and Appendix B contradiction 2. |

**Tally: 9 confirmed, 2 partly (18, 78), 0 not supported** among the 11 `fix` rows.

### The "Five findings"

1. **Partly.** The core mechanism ("the push after every delegated merge is rejected as non-fast-forward and swallowed as a note") is confirmed exactly as above. **The specific statistic — "of the last hundred delegated-merge runs, 8 succeeded, 38 failed and 54 were skipped" — does not appear anywhere in `evidence/steps.md`, `answers.md`, `drift.md`, or `history.md`.** Appendix D says only that "the Actions API was queried directly" for this — no file:line, no raw output, no coverage-section command. I could not reach the GitHub Actions API from this session (no `gh`, no outbound network permission) and cannot independently confirm or refute the 8/38/54 breakdown. **This is the one finding in the draft with a load-bearing number that is not traceable to anything in the repository.**
2. **Confirmed.** Verified directly: `.sdlc/approvers.yaml:26` lists `claude` under `never-approve`; `work/ci-budget/log.md:17` records the resulting impossibility; `work/index.md` and the 20 items' front matter (checked via `work/*/intent.md` listings already surfaced in `answers.md` Q2) show 19 of 20 still open.
3. **Confirmed.** All four agent files carry unbounded `Bash` (verified above, row 60); `.sdlc/config.env:9` confirmed to omit the five named paths (row 48).
4. **Confirmed, reproduced live** (see row 65 above) — "this session's included" is literally true of the session performing this cross-check too.
5. **Confirmed as far as verifiable.** `work/ci-budget/log.md:16` self-reports "`main` carries no branch protection rule at all (branches API, protected: false)" and `work/ci-budget/intent.md`'s Q16 answer records the repo went public 2026-09-09 with no other change. I cannot independently query the live GitHub branch-protection API from this session, so "now available" rests on the same public-repo fact already verified for row 96/125, extended by inference (a documented general GitHub Free-plan rule) rather than a fresh API check of this specific endpoint.

### Five `change` rows (chosen: 4, 15, 38, 45, 96)

| Row | Verdict | Note |
|---|---|---|
| 4 | **confirmed** | `work/ci-budget/intent.md:166-201` has exactly six `Q:`/`A:` pairs in its first round (before "(added after exploration)"/"(second session)" markers begin), each with a proposed answer edited by the owner — matches "one round of six questions, each with a proposal, answered as `A:` lines" precisely. |
| 15 | **confirmed** | `docs/sdlc/README.md:110` says "four inputs"; `.github/workflows/approve.yml` has four inputs (`artifact`, `mode`, `slug`, `note`); `CLAUDE.md:72` and the skills say three. Verified directly. |
| 38 | **confirmed** | `.claude/skills/sdlc-plan/SKILL.md:10` matches; `require-plan.sh` (verified for row 45 below) confirms nothing reads the file list at edit time — it is judged only by `check_artifact_chain.py` against the whole PR diff, matching the Current-state citation. |
| 45 | **confirmed** | Read `require-plan.sh` in full: `check_plan_required()` only ever reads the plan's front-matter `status` field — it never parses `## Files that change`. Confirms "the gate checks the status word, not the file list" exactly. |
| 96 | **confirmed** | Same facts as finding 5 above, cross-checked against `knowledge/decisions/merge-click-is-the-gate.md` framing already read in `answers.md` Q25. |

### Five Table 2 rows (chosen: 4.1, 42.1, 58.1, 96.1, 135.1)

| Row | Verdict | Note |
|---|---|---|
| 4.1 | **confirmed** | Same evidence as change-row 4. |
| 42.1 | **confirmed** | `git show origin/claude/agent-plan-adherence-4b4mqk:work/plan-adherence/intent.md` (lines ~106-113): "A plan step has a fixed, tickable shape… five fields: goal, files (a subset of the file list), acceptance test, verify command, done-when" — verbatim match to the row. |
| 58.1 | **confirmed** | Matches `answers.md` Q10 in full: three unenforced tables, no `model:` field in any `.claude/agents/*.md` (verified directly, row 60), `MODEL_LEAD` etc. absent from `.sdlc/config.env` (checked: not present). |
| 96.1 | **confirmed** | Consistent with finding 5 and row 96 evidence above; `drift.md` §7 (read in full) is the correct section for "internal contradictions still marked current," which is where the merge-click premise is flagged. |
| 135.1 | **not a citation claim** | "From: new" — no external citation to check; it is the review's own proposal. |

**Overall citation tally across all 26 required checks: 21 confirmed, 4 partly (rows 18, 78, and the two "change"/"Table 2" rows are all confirmed so the partlys are only 18 and 78 plus Finding 1's statistic), 1 not supported (Finding 1's specific Actions-run breakdown).**

## 3. UNSUPPORTED CLAIMS

Sentences that state a fact about the repository with no citation in the draft or in the evidence
files (quoted verbatim):

- **"of the last hundred `delegated-merge` runs, 8 succeeded, 38 failed and 54 were skipped"** (Finding 1, and repeated in row 100's Current-state column). No file:line, no evidence-file citation, no raw command output anywhere in `steps.md`/`answers.md`/`drift.md`/`history.md`. Not verifiable from this session (no `gh`, no outbound network permission granted). This is the most consequential unsupported number in the draft, since Finding 1 is one of the "five findings that change the picture."
- **"Three of the fourteen lessons and one red `main` came from index regeneration alone"** (§0, Stance D). The "one red `main`" half is confirmed (`work/ci-budget/log.md:17`, `894e11c`). The "three of the fourteen lessons" half has no citation anywhere; I searched all 14 lesson files for "index" and found only `fold-crlf-before-comparing.md` (about CRLF drift on **both** context files and index files, not index-regeneration specifically) and `stage-new-files-before-verify.md` (about the front-matter checker, unrelated to index regeneration). I could not identify which three lessons the claim means, or verify there are three.
- **"a second model reading the same log from CI has not once fixed anything"** (row 92, Why column). No citation; not findable in any evidence file. Not independently verifiable from repository state (would require reading historical CI triage step-summary output, which isn't retained in the repo).
- **"That inventory was produced mechanically from every skill, hook, workflow, template, script docstring, rule fragment, decision and work item"** (§0, "What a step is"). This overstates `steps.md`'s own Coverage section, which explicitly lists what it did **not** read in full: `.claude/hooks/_lib.sh`'s 382 lines (only via callers), most of `check_artifact_chain.py`/`delegated_merge.py`/`adopt.sh`/`detect_bands.py`/`github_metrics.py`/`gen_*.py` beyond cited sections, all `test_*.py`, all `docs/sdlc/spikes/*`, seven named `knowledge/decisions/*.md` files, twelve of the fourteen `knowledge/lessons/` files, and the specs/plans of twelve work items. "Every… decision" and "every… work item" are not literally true of the inventory's own stated method — verifiable directly against `steps.md`'s Coverage section (lines 296-305).
- **"A blank slug on a feature branch has misrouted twice"** (row 18, Why column) — see §2 above; the row's own citation supports one confirmed event, not two.

## 4. INTERNAL CONTRADICTIONS

- **Rows 130 and 157 disagree with each other about the same fact, even though row 157 explicitly says "Same as row 130."** Row 157's Current-state column reads "Q16: inert on the Free plan; **now available since the repo is public**." Row 130's Current-state column, covering the identical GitHub Environment/required-reviewer mechanism, says only "Q6: no deploy has ever run; `deploy.sh` prints the command it would run; `release-authorizations/` holds only `.gitkeep`" — it never mentions that the repo going public may have changed availability, the way row 157 (and rows 96/125/Finding 5) do for branch protection. The draft applies its own "the repo went public, so re-check what was 'inert on the Free plan'" logic to branch protection (rows 96, 125) but not consistently to the twin Environment-reviewer mechanism (row 130), even in the row that is supposed to be its primary statement (157 defers to 130 for the substance and then contradicts 130's own text).
- **Appendix B contradiction 8 is marked "still open," but its owning row is `keep` with no action.** Contradiction 8: "The two chain checkers disagree about whether `.sdlc/active` is an item's own file. Row 109; still open." Row 109 itself reads: `keep | — | — |` — under the draft's own vocabulary table (§0), `keep` means "the step stands; nothing to do." A contradiction the draft itself calls "still open" is assigned to a row that proposes no fix, unlike every other numbered contradiction in Appendix B (1→row 104 `fix`, 2→rows 97/125 `fix`, 3→row 84 `fix`, 4→rows 96/125 `change`/`fix`, 9→row 60 `fix`, 10→row 131 `keep (note)` at least flags a doc fix). Contradiction 8 is the one item in Appendix B left with no corrective row at all.
- **Row 63's Why cites "three lessons" from index regeneration; row 63.1's Why cites the same "three lessons"; §0 Stance D also claims "three... lessons."** All three restate the same unverified number (see §3) without ever naming which three lessons — a claim repeated three times in the document is still one uncited claim, not three independent confirmations.
- **Section 0's methodology claim ("produced mechanically from every… decision and work item") is contradicted by `steps.md`'s own Coverage section**, which lists specific decisions and work-item specs/plans it did not read (see §3). The draft's own evidence base admits the gap that its framing sentence denies.

## 5. WHAT A FRESH READER WOULD ASK

- **Finding 1's numbers**: where is the raw `gh api` output or Actions run list for the "8/38/54" breakdown? Without it, a reader who wants to check the headline claim of the review has nowhere to look.
- **The twelve off-by-one citations** (§1/§2): were these citations generated by a different tool pass than `steps.md`'s, against a slightly different checkout? The pattern is too consistent (always exactly one line low, confined to three specific skill files) to be random — a reader would want to know what produced it, since the same tool may have mis-cited other, unchecked rows too.
- **What happens to the four "alive" unmerged branches** (`standing-grant-intent`, `risk-detour-intent`, `advance-push-intent`, `approve-tap-regenerates-index`) once the draft's proposals are accepted — are they rebased and reused as the actual PRs for rows 100.1/8.1/62.1/etc., or are the new steps implemented fresh and the branches abandoned? Appendix C never says, even though three of them describe defects the draft's own Appendix C step 1 promises to fix.
- **Who reviews this document itself**, given rule/Stance E ("reviewers run on a different model from the writer") and step 135.2's own admission that "the second-model cross-check of this document… has not run yet, since the charter that would define it is itself a proposal in this draft"? A reader would ask whether this cross-check (mine) is meant to be that charter's first instance, or whether it is separate and 135.2 still needs to be written and run.
- **Sizing**: no row or appendix estimates how large the "one control-plane pull request" (row A.2, bundling rows 8, 21, 35, 45.1, 48, 65, 97, 98, 100.1, 104.1) would actually be as a diff, or how long the owner's single review of it would take — a reviewer weighing "one big label tap" against "ten separate items" has no numbers to weigh it with.
- **The `parked` status** (row 62.1) is introduced as "a new status word for the chain check and `next_item.py`," but nothing says whether `parked` also needs a new `check_artifact_chain.py` STATUSES entry, a new eval case, or a new front-matter validation the way every other status transition in the repo has one — is it a `status:` value or something else?
- **Row 96.1** proposes branch protection with "one approving review… satisfied by the review comment" — the repo's actual mechanism today is a `claude[bot]` PR *comment*, not a GitHub PR *review* object; a fresh reader who knows GitHub's required-reviews feature would ask exactly how a comment "satisfies" a review requirement, since GitHub's branch protection API does not accept an arbitrary comment as a review approval.
- **Cost of implementing 45 non-`keep` rows plus 25 new steps**: no row or appendix gives a rough total (files touched, PRs needed, hours) for the whole revision — only Appendix C's nine-step order, with no sizing per step.

## 6. COUNTS

Recounted directly from the draft's own tables (not restated from the draft's prose, since the draft
makes few explicit self-claims about these numbers):

| Item | Recount | Draft's own explicit claim (front matter / §0 / body) | Match? |
|---|---|---|---|
| Table 1 rows | 164 (1–110, 111–139, 140–164; no gaps/dupes) | "164 existing steps" (description); "the 164 steps in `evidence/steps.md`" (§0) | ✅ |
| Rows per Change value | keep 97, keep (note) 18, change 28, fix 11, drop 8, build 1, merge→n 1 (sum 164) | none stated explicitly in prose (task prompt's "11 fix rows" is externally correct, confirmed) | ✅ (no draft self-claim to check against, but externally correct) |
| Rows per lens | Lens A 1–110 (110 rows), Lens B 111–139 (29 rows), Maintain 140–164 (25 rows) | "lens A, rows 1–110… lens B, rows 111–139… Maintain loop (rows 140–164)" (§0) | ✅ |
| Table 2 (new steps) rows | 25 (4.1, 8.1, 13.1, 35.1, 42.1, 42.2, 45.1, 58.1, 58.2, 60.1, 62.1, 63.1, 71.1, 72.1, 94.1, 96.1, 100.1, 104.1, 135.1, 135.2, 146.1, 161.1, 163.1, A.1, A.2) | "25 proposed new steps" (description) | ✅ |
| Appendix A questions | 30 (Q1–Q30, no gaps) | "the thirty interview questions answered from evidence" (description); "Appendix A. The thirty questions" (heading) | ✅ |
| Appendix B contradictions | 12 (numbered 1–12) | no explicit count stated in the draft (description says only "the contradictions the review found") | — (no self-claim to verify; recount is 12) |
| Five findings | 5 (numbered 1–5 in §0) | "Five findings that change the picture" | ✅ |

**No numeric self-claim the draft makes about its own structure was found to be wrong.** The counts
that *are* wrong or unsupported (Finding 1's 8/38/54, Stance D's "three… lessons") are claims about
the **repository's** history, not about the **document's** own shape — those are covered in §2/§3, not
here.

---

## Coverage

**Files read in full:**
- `docs/sdlc/revision/2026-09-10-step-review.md` (the draft, both pages)
- `docs/sdlc/revision/evidence/steps.md`
- `docs/sdlc/revision/evidence/answers.md` (both pages)
- `docs/sdlc/revision/evidence/drift.md`
- `docs/sdlc/revision/evidence/history.md`
- `docs/sdlc/revision/evidence/index.md`

**Repository files opened to verify specific citations:**
- `.github/workflows/approve.yml` (lines 75-90)
- `scripts/approve_dispatch.py` (lines 10-30)
- `.sdlc/config.env` (`PROTECTED_PATHS`, `PLAN_REQUIRED_PATHS`)
- `docs/sdlc/rules/10-hard-rules.md` (rule 8)
- `docs/sdlc/rules/20-verifying.md` (full)
- `docs/sdlc/rules/00-chain.md` (lines 18-28)
- `docs/sdlc/rules/60-lessons.md` (full)
- `docs/sdlc/github-setup.md` (lines 65-80)
- `.claude/agents/explorer.md`, `plan-reviewer.md`, `security-reviewer.md`, `verifier.md` (headers)
- `.claude/skills/sdlc-review/SKILL.md` (full, line-numbered)
- `.claude/skills/sdlc-spec/SKILL.md` (full, line-numbered)
- `.claude/skills/sdlc-plan/SKILL.md` (full, line-numbered)
- `.claude/skills/sdlc-run/SKILL.md` (lines 1-50, line-numbered)
- `.claude/skills/sdlc-incident/SKILL.md` (full, line-numbered)
- `REVIEW.md` (full, line-numbered)
- `.sdlc/approvers.yaml` (`never-approve` block)
- `scripts/check_artifact_chain.py` (lines 185-210, the `gh` call site)
- `.claude/hooks/require-plan.sh` (full)
- `.github/workflows/delegated-merge.yml` (`workflow_run` block, lines 25-36)
- `.sdlc/delegation.yaml` (`require-checks`, `method`)
- `scripts/delegated_merge.py` (grep for `fetch|ff-only|push|non-fast`, and lines around 990-1000)
- `work/ci-budget/log.md` (full)
- `work/ci-budget/intent.md` (lines 40-270, Open questions section)
- `work/retire-active-pointer/intent.md` (lines 40-55)
- `knowledge/lessons/*.md` (grepped for "index"; three matching files read in full: `fold-crlf-before-comparing.md`, `stage-new-files-before-verify.md`, `index.md`)

**Commands run (all read-only):**
- `wc -l` on the draft and all four evidence files
- `git log origin/main --grep="Advance .sdlc/active" --oneline` (and `| wc -l`) — confirms no advance commit on `main`
- `git show origin/claude/agent-plan-adherence-4b4mqk:work/plan-adherence/intent.md` — confirmed the five-field plan-step shape and the compaction problem statement, without checking out the branch
- `command -v gh` — confirmed no `gh` binary in this session
- `env | grep -i "^GH_TOKEN=\|^GITHUB_TOKEN="` — confirmed both tokens are set in this session (reproducing the exact `VERIFY: FAIL` condition of row 65 / finding 4)
- `grep -rn` / `grep -c` across `docs/sdlc/revision/evidence/*.md`, `work/*/log.md`, `.claude/skills/*/SKILL.md`, `knowledge/lessons/*.md` for specific phrases and citation targets (each cited inline above)
- Python scripts (ad hoc, in `/tmp`) to: (1) parse both markdown tables (respecting `\|` escapes) and diff row numbers 1–164 between the draft and `steps.md` for gaps/duplicates; (2) tabulate the draft's `Change` column distribution; (3) extract and diff same-file `file:line` citations between the draft and `steps.md` to surface the off-by-one pattern; (4) count Table 2 rows, Appendix A rows, and Appendix B numbered items directly from the draft's text
