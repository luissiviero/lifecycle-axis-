---
type: doc
title: "Evidence: how the plan changed, and what lives outside main"
description: "Timeline of behaviour changes on main, the share of the repo each founding idea occupies, and every unmerged branch's proposal; produced read-only for the 2026-09-10 step review."
tags: [sdlc, revision, evidence]
timestamp: 2026-09-10T14:00:00Z
---
# lifecycle-axis- — revision history

Scouted read-only against `origin/main` @ `ca8dd32` (2026-09-10, working tree confirmed identical to
`origin/main`) and ten `origin/claude/*` branches. No repository file was edited and no branch was
checked out; all reads used `git show`, `git log`, `git diff`.

---

## Part 1 — Timeline of plan changes

399 commits total on `origin/main`, 2026-09-02 to 2026-09-10. 213 of them are behaviour changes (added
a feature, changed a rule, or reversed a decision); 186 are pure bookkeeping (index/ledger regeneration,
`status: approved` flips, "Update log.md", merge commits). The table below groups consecutive same-PR
commits into one row (99 rows) so the shape of each day is readable; every grouped row's "also:" clause
names the other commits it folds in, so no behaviour-changing commit is dropped. PR numbers come from
`git log --merges --format='%h|%s'` cross-referenced against each merge commit's two parents
(`git log <first-parent>..<second-parent>` gives exactly the commits that PR contributed) — 314 of the
399 commits mapped to a PR this way; the rest (`—` in the PR column) landed straight on `main`, mostly
the owner's own approval clicks and the two GitHub-web-editor administrative edits.

Note: **pull requests 59–62 are missing** from the merged sequence (58 is followed by 63). `ci-budget`'s
own ledger (`work/ci-budget/log.md`, commit `603695b`) explains why: "the approve tap that died in 3
seconds... a 5m54s `claude -p` triage on every red gate (pull requests 59-61 each paid it for a drift
already on main)" — three of the four were CI-triage runs against an already-stale head, closed without
merging once the account's free Actions minutes ran out on 2026-09-08 21:43 UTC; #62 is unaccounted for
in what's on `main` (possibly folded into #63's branch history, which starts from a different point).

| Date | SHA(s) | PR | Slug | What changed in framework behaviour |
|---|---|---|---|---|
| 2026-09-02 | `372801f` | — | — | Scaffold the AI-native SDLC starter kit |
| 2026-09-02 | `76c05c8`..`99b0541` (33 commits) | #1 | — | Align the kit with the full playbook text and add the OKF pairing plan — also: decision options for ten open questions; chain artifacts, config keys, self-registering verify checks; hook test harness + Gemini parity spike; approvers file, log ledger, eval-runner selectors, plugin spike; deploy-only-from-CI + review-identity spike; OKF conformance checker; control-plane label exemption + stop hook + GitHub metrics; one rule source → CLAUDE.md/GEMINI.md/AGENTS.md; OKF front matter + docs/sdlc indexes; generated work indexes; knowledge/ OKF bundle seeded; chain check validates approvers/ledger; plugin manifest (T21) + drift check; `scripts/adopt.sh`; plan file contract covers whole PR diff; closed a Bash-write bypass in the edit hooks; control-plane hardening; human approval helper |
| 2026-09-02 | `4f85d68`..`b483976` (2 commits) | #2 | — | The kit repo stops wiring its own hooks (so an adopter's hooks aren't shadowed) |
| 2026-09-02 | `8e41db4` | #3 | — | Pin CI actions to commit SHAs; add Dependabot |
| 2026-09-02 | `cde4360` | #4 | — | CI accepts a subscription OAuth token as the Claude credential |
| 2026-09-02 | `feb7a2d` | — | `_example` | Example work item's three artifacts approved (template demo, not the kit itself) |
| 2026-09-02 | `4705132` | #5 | — | Dependabot bump: `actions/checkout` 4.4.0 → 7.0.1 |
| 2026-09-02 | `0cd36fe` | #6 | — | Kit's own hooks run again, gated by the control-plane unlock |
| 2026-09-02 | `aa1ab99` | #7 | — | PR reviewer gets a posting route that isn't raw Bash |
| 2026-09-02 | `eea6191` | #8 | — | Records the merge-click decision, Windows findings, LF-only for shell scripts |
| 2026-09-02 | `88ee5dd` | #9 | — | Gemini CLI wired to the same hooks; hooks made to hold on Windows |
| 2026-09-02 | `0991ae3`..`9fe0814` (2 commits) | #10 | — | `adopt.sh` installs `.gemini/` with the hooks; Gemini docs finished |
| 2026-09-03 | `91ffa1e` | #11 | — | Closes the production gate's git-push and boundary bypasses |
| 2026-09-03 | `b41f10f` | #12 | — | Kit's own tooling made to run on Windows (roadmap 19) |
| 2026-09-03 | `921d801`..`be13418` (2 commits) | #13 | — | Spike: adversarial red-team pass for `/sdlc-spec`; fixed `adopt.sh` running `claude setup-token` by accident |
| 2026-09-03 | `1374541` | #14 | — | Spike: encode the Claude platform prompting docs as "prompt-surface" controls |
| 2026-09-03 | `951ea7b` | #12 | — | Fixes a symlink bypass in `_lib.sh` that a skipped test had been hiding |
| 2026-09-03 | `1c415cc` | #14 | — | Accepts the prompt-surfaces spike; adds per-role model routing and a summary table |
| 2026-09-03 | `cd17025` | #12 | — | Records the path-comparison lesson (rule 7); closes roadmap 19 |
| 2026-09-03 | `724c7bb` | #15 | — | Spike: what to borrow from the retired `claude-agents` repo for the Build stage |
| 2026-09-03 | `259dfbe` | #16 | — | Platform docs cited by URL; spike status vocabulary settled; roadmap 1b fixed |
| 2026-09-03 | `74afc41` | #17 | — | Opens `delegation-boundary`: may a subagent ever write code? |
| 2026-09-04 | `35a894f`..`8c21ac3` (2 commits) | #18 | — | Local test suite cut from 10 min to 3 without dropping an assertion |
| 2026-09-04 | `4c895b3`..`11d905b` (3 commits) | #19 | — | A work item can open one stage per PR; the kit's own plan gate excluded from adopters |
| 2026-09-04 | `4c31034`..`3d847f4` (2 commits) | #20 | — | In-progress chain mode covers superseding an item and flipping `.sdlc/active` |
| 2026-09-04 | `8c435a9` | #21 | — | The kit's own product code is plan-gated; eval cases treated as test files |
| 2026-09-04 | `60ab0f5` | #23 | — | Skills and agents quote template spellings exactly (drift prevention) |
| 2026-09-04 | `d5989df` | #22 | — | `delegation-boundary` becomes the active work item |
| 2026-09-04 | `bf2c384` | #21 | — | Hook tests run as an adopter would run them, not as this repo |
| 2026-09-04 | `89bcf9a`, `e111089`, `90af5f1`, `fb1eed7` | #24 | `front-matter` | **New rule**: one front-matter parser for every artifact; comment-line templates; `approve.py` enforces intent→spec→plan stage order |
| 2026-09-04 | `0fec0fb` | #25 | `approval-gate` | **New rule**: only a human can flip an artifact to `status: approved` (hook-enforced) |
| 2026-09-04 | `7bfe5f4`, `0976fc3`, `e73c967`, `274ce9c` | #26 | `control-plane-visibility` | Hook decisions logged; the control-plane unlock made visible; CI reviews the kit's own agent PRs |
| 2026-09-04 | `382db0f`, `3abdca8` | #27 | `deploy-gate` | **New rule**: the deploy path fails closed |
| 2026-09-04 | `a3ee9ef`, `15bf507`, `855fec5` | #28 | `loop-protection` | **New rule**: the agent cannot weaken the check on its own work |
| 2026-09-04 | `c64c6b9`, `7dde0cf`, `9ef5284` | #29 | `bash-guard-hardening` | Bounded closure of the Bash write-guard gaps |
| 2026-09-04 | `60bd6f9` | #30 | — | First session handoff doc written (playbook-comparison work) |
| 2026-09-05 | `37f7145`..`f84d522`, `4bc771c`, `076861d` | #27 | `deploy-gate` | Release authorizations validated against the release-manager role; build gate logged on the PR, not as a plan-status change |
| 2026-09-05 | `69ba125`, `55cf5f5`..`ddb3776` | #25 | `approval-gate` | Approval judged by the *resulting* front matter (every occurrence of the key), not by words matched in the diff; glued `unset` env forms matched |
| 2026-09-05 | `91e3202`..`af0254f` | #31 | `band-detector` | **New feature**: trailing-baseline four-rule anomaly detector; honest GitHub metrics; workflow matrix generated from `bands.yaml` |
| 2026-09-05 | `e421eab`, `9e7fc8c` | #32/#33 | `adopter-first-hour` | **New feature**: a fresh install of the kit works inside the first hour |
| 2026-09-05 | `9d95704`..`2c44d0b` | #34 | `agent-evals` | **New feature**: evals that test the agent itself and can go red; incident-case oracle restores `lessons.md` from a pre-prompt snapshot, never `HEAD` |
| 2026-09-05 | `758a5d4`..`d535925`, `20c1f78` | #35/#36 | `delegation-boundary` | **New rule/decision**: one writer per work item until a cost ledger exists (subagents read, only the session holding the plan edits) |
| 2026-09-05 | `a8b067a`..`970f4d0` | #37 | `docs-reconcile` | Docs made to say what the code actually does; D3 oracle changed to "last content change, not last commit" |
| 2026-09-05 | `be5c5a8`..`473c315` | #39 | `batch-b-followups` | Untrusted `sdlc-gate` triage step closed; placeholder approver handle refused structurally (not just a never-approve entry); chain check accepts a fully superseded predecessor |
| 2026-09-05 | `07c7275` | — | — | `pull-requests: read` added to `bands.yml` permissions directly on `main` (fixes the silent 403 described in Part 3, handoff-close) |
| 2026-09-05 | `38ba396` | (#41, squash) | — | Handoff corrected to the true post-Batch-B state; new lesson `workflow-permissions-name-every-api.md` lands (see Part 3) |
| 2026-09-05 | `71ca50d`..`47e33f7` | #42–#45 | `delegated-mode` | **Major new mode**: `status: delegated`, `scripts/sign.py --delegate`, hooks accept a delegated signature under a grant, `delegated-merge.yml` + `delegated_merge.py` merge a delegated PR without a human tap |
| 2026-09-06 | `9a95421`, `678eada` | #46 | `delegated-mode` | `delegated-mode` item closed out; docs/handoff finalized |
| 2026-09-06 | `4ee5ffc`..`5de0798` | #47–#51 | `approve-by-dispatch` | **New feature**: `approve.yml` workflow_dispatch tap runs `approve.py --from-dispatch` and `approve_dispatch.py`, writing the approval as a commit whose actor is the run's actor — "one tap in the Actions tab" replaces a human shell session |
| 2026-09-06 | `85d56e2`..`15424e0` | — | — | `delegation.yaml` policy edited directly by the owner (require-checks tightened) |
| 2026-09-07 | `c968aeb` | #52 | `retire-active-pointer` | Opens the item: retiring `.sdlc/active` when a work item completes |
| 2026-09-08 | `0697eb6`..`a715243` | #53 | `retire-active-pointer` | **New rule**: `retired` is `superseded`; chain check speaks for a retired item; revision 1 reconciled spec vs. code after 3 Important review findings |
| 2026-09-08 | `4526568`, `5ff9f5d`..`aec7bd4`, `a8b7001` | #54/#55/#57 | `run-queue` | **Major new feature**: grant several items up front (a queue); the merge advances `.sdlc/active` to the next item and `/sdlc-run` loops without a human between items |
| 2026-09-08 | `e227ed6`, `bc36009`..`cd8eda5`, `ffcf177`..`19136bc` | #56/#58 | `run-queue-followups` | Guard added: an empty diff on a dirty tree is refused (closes a silent-no-op hole in the advance) |
| 2026-09-09 | `603695b`..`ed76101` | #63 | `ci-budget` | Opens the item: cut GitHub Actions minutes/latency/tokens after the account exhausted its 2,000 free minutes in 6 days (1,124 runs) |
| 2026-09-09 | `308f1a2` | — | — | `.sdlc/active` repointed from `run-queue-followups` to `ci-budget` directly by the owner |
| 2026-09-09 | `8412525`, `3455ec7` | #64 | `ci-budget` | Drifted indexes regenerated; reviewer's nit on the "over 62" denominator fixed |
| 2026-09-10 | `0e9d160` | — | `ci-budget` | Owner approves `ci-budget/intent.md` — **this is where `main` stands today** |

### Bookkeeping commits per day (excluded from the table above)

| Date | Bookkeeping commits (index/ledger/status-flip/merge/"Update log.md" only) |
|---|---|
| 2026-09-02 | 16 |
| 2026-09-03 | 9 |
| 2026-09-04 | 56 |
| 2026-09-05 | 61 |
| 2026-09-06 | 18 |
| 2026-09-08 | 11 |
| 2026-09-09 | 8 |
| 2026-09-10 | 3 |
| **Total** | **182** (of which ~80 are the 80 merge commits themselves, `git log --merges`) |

(2026-09-07 has zero bookkeeping commits — the whole day is `c968aeb`, one intent draft.)

---

## Part 2 — The three founding ideas

Origin commits found by `git log --diff-filter=A` on each idea's characteristic files, all inside the
very first days:

| Idea | Origin commit(s) | Files that carry it today | Later commits touching it |
|---|---|---|---|
| **1. AI-native SDLC playbook** | `372801f` (2026-09-02, "Scaffold the AI-native SDLC starter kit") and `76c05c8` same day ("Align the kit with the full playbook text") | `docs/sdlc/README.md`, `docs/sdlc/rules/00-30`, `docs/sdlc/templates/`, `.claude/hooks/`, `.claude/skills/sdlc-*`, `.claude/agents/`, `scripts/verify.sh`, `check_artifact_chain.py`, `approve.py`, `sign.py`, `delegated_merge.py`, `gen_index.py`, `.github/workflows/`, `work/` (every work item) | 29 commits touch `docs/sdlc/README.md` alone; effectively every one of the 213 behavioural commits in Part 1 is this idea's implementation — the playbook *is* the repo's spine, so idea 1 is best read as "everything not specifically idea 2 or 3" |
| **2. Open Knowledge Format (OKF)** | `76c05c8` (2026-09-02, "...add the OKF pairing plan"), then same-day `0a44447` ("OKF front matter and index files"), `6f892d3` ("seed the knowledge/ OKF bundle"), `127198f` ("OKF conformance checker, warning by default") | `knowledge/` (decisions + lessons, 40 files), `scripts/check_okf.py` + `scripts/checks/okf.sh` + `scripts/test_check_okf.py`, `scripts/check_front_matter.py` + `scripts/checks/front-matter.sh` + `scripts/test_check_front_matter.py`, `docs/sdlc/okf-pairing.md` | 40 commits touch `knowledge/`; 6 touch `check_okf.py`/`okf-pairing.md`/`check_front_matter.py` directly. The front-matter parser was unified into one implementation on 2026-09-04 (`fb1eed7`, PR #24, "one front-matter parser") — the clearest later structural change to this idea |
| **3. Model/prompting best practices** | `b809369` (2026-09-02, "review-identity spike"), then `1374541` (2026-09-03, "spike on encoding the Claude platform prompting docs as prompt-surface controls"), accepted in `1c415cc` same day ("add per-role model routing and a summary") | `docs/sdlc/spikes/prompt-surfaces.md` (386 lines, the core artifact), `docs/sdlc/rules/40-claude-only.md` (19 lines), `docs/sdlc/rules/50-gemini-only.md` (28 lines), `docs/sdlc/spikes/pr-review-identity.md`, `docs/sdlc/spikes/build-stage-from-claude-agents.md`, `docs/sdlc/spikes/red-team-pass.md`, `docs/sdlc/spikes/gemini-parity.md` | 20 commits touch this file set; last touched `724c7bb`/`259dfbe` (2026-09-03, spike-status vocabulary settled) and `921d801` (2026-09-03, red-team-pass spike). **Notably unimplemented**: the "per-role model routing" the spike designed (each `.claude/agents/*.md` carrying a `model:` field) never shipped — the four files in `.claude/agents/` today (`explorer.md`, `plan-reviewer.md`, `security-reviewer.md`, `verifier.md`) have no `model:` front-matter key; `docs/sdlc/phase-2-roadmap.md` still lists it as "designed, not scheduled" |

### Repo share (mapping used: `git ls-files` + `wc -l`, repo total = 369 tracked files / 37,244 lines)

| Idea | Files | Lines | Share of repo |
|---|---|---|---|
| OKF (`knowledge/**`, `scripts/check_okf.py`, `scripts/check_front_matter.py`, their `checks/*.sh` + tests, `docs/sdlc/okf-pairing.md`) | 40 | 3,045 | ~8.2% |
| Model/prompting practices (`docs/sdlc/spikes/prompt-surfaces.md`, `docs/sdlc/rules/40-claude-only.md`, `docs/sdlc/rules/50-gemini-only.md`, `docs/sdlc/spikes/{pr-review-identity,build-stage-from-claude-agents,red-team-pass,gemini-parity}.md`) | 7 | 1,054 | ~2.8% |
| AI-native SDLC playbook (everything else: hooks, scripts, workflows, skills, agents, templates, `work/`, remaining `docs/sdlc/`) | 322 | ~33,145 | ~89.0% |

The playbook idea dominates by construction — it is the mechanism the other two ideas' content flows
through (OKF is *how artifacts are shaped*, model-practice is *how prompts are shaped*; both are policy
riding on the same hook/script/workflow substrate counted under idea 1). If instead only the files whose
entire *purpose* is idea 1 and nothing else are counted (`.claude/hooks/`, `scripts/check_artifact_chain.py`,
`approve.py`, `sign.py`, `delegated_merge.py`, `.github/workflows/`, `docs/sdlc/templates/`), that core is
still the largest single slice at roughly 60 files / 9,000+ lines — the stated mapping is the one used
above; a narrower "core enforcement only" cut would shrink idea 1's share but not change its rank.

---

## Part 3 — Proposals outside main

| Branch | Commits ahead | Verdict |
|---|---|---|
| `claude/standing-grant-intent` | 4 (2026-09-08) | **Alive** |
| `claude/risk-detour-intent` | 4 (2026-09-08) | **Alive** |
| `claude/advance-push-intent` | 4 (2026-09-08) | **Alive** (describes a real, unfixed bug) |
| `claude/approve-tap-regenerates-index` | 5 (2026-09-08) | **Alive** (describes a real, unfixed bug) |
| `claude/handoff-close` | 4 (2026-09-05) | **Landed elsewhere**, then superseded |
| `claude/agent-plan-adherence-4b4mqk` | 2 (2026-09-10) | **Alive**, freshest proposal |
| `claude/pr-63-plan-review-ekiuva` | 3 (2026-09-10) | **Alive** (a `spec.md` for `ci-budget`, whose `intent.md` is already approved on `main`) |
| `claude/session-handoff` | 0 | Fully merged (PR #30, 2026-09-04) |
| `claude/lifecycle-axis-analysis-cgydca` | 0 | Fully merged (PR #24 `front-matter`, 2026-09-04) |
| `claude/interview-prompt-master-skills-fhzomk` | 0 | Fully merged (its tip is the red-team-pass merge, PR #13, 2026-09-03) |
| `claude/platform-best-practices-0fnr6h` | 0 | Fully merged (its tip is `1c415cc`, the prompt-surfaces acceptance, PR #14, 2026-09-03) |

### The four branches with 0 commits ahead

Each branch's tip commit is itself an ancestor of `main` (`git merge-base --is-ancestor` returns true),
i.e. these are old feature branches whose work landed and whose branch pointer was simply never deleted.
They map onto Part 1/Part 2 entries already described: `session-handoff` → PR #30 (2026-09-04 handoff
doc, later itself superseded by `38ba396`/#41 and again by the 2026-09-06 delegated-mode handoff);
`lifecycle-axis-analysis-cgydca` → PR #24 `front-matter`; `interview-prompt-master-skills-fhzomk` and
`platform-best-practices-0fnr6h` → the red-team-pass and prompt-surfaces spikes (PRs #13/#14, idea 3
in Part 2). No unmerged content to report for these four.

### The seven branches with unmerged commits

**`claude/standing-grant-intent`** (2026-09-08, 4 commits, `work/standing-grant/intent.md`, 160 lines)
- *Problem*: every delegated work item needs a separate human tap that writes `mode: delegated`; a
  queue of N items is N taps, with an idle repo between them. The owner: "I'd want no tap."
- *Proposed outcome*: move the grant for low-risk items into the human-only policy file
  (`.sdlc/delegation.yaml`) as one standing grant; the merge workflow opens a new item itself when the
  pointer is empty; `supervised` becomes the mode the owner explicitly asks for, not the default.
- *Landed elsewhere?* No — grep for "standing grant" / "no tap" on `main` finds nothing outside this
  branch. Depends on `advance-push-intent`'s fix (the advance must actually push) to be usable.
- *Verdict*: **alive**, parked behind `ci-budget` on the queue (`.sdlc/active` currently reads `ci-budget`).

**`claude/risk-detour-intent`** (2026-09-08, 4 commits, `work/risk-detour/intent.md`, 141 lines)
- *Problem*: delegated mode is low-risk-only; today non-low work is refused at admission (5 separate
  refusal points) or, mid-item, stops the *entire* queue. No mechanism looks for a same-outcome route
  that stays low-risk.
- *Proposed outcome*: when a delegated item meets non-low work, convene multiple reviewer agents at the
  gate to find a route that reaches the intent's outcome touching only low-risk surface; adopt it only
  on unanimous consensus, otherwise park the item (a new status/mechanism, not yet designed) and let the
  queue continue with the next item.
- *Landed elsewhere?* No occurrence of "risk-detour", "park", or a low-only reviewer-consensus mechanism
  on `main`.
- *Verdict*: **alive**, parked (risk-class: low, but unimplemented).

**`claude/advance-push-intent`** (2026-09-08, 4 commits, `work/advance-push/intent.md`, 109 lines)
- *Problem*: `delegated_merge.py` advances `.sdlc/active` by committing on the job's pre-merge checkout
  of `main`, then pushing — always a non-fast-forward push since the merge API call already moved
  `main`. The rejection is silently swallowed as a note. **`git log --grep="Advance .sdlc/active"` on
  `main` returns nothing — no advance commit has ever actually landed**, contradicting `run-queue`'s own
  promise of "zero human input between items".
- *Proposed outcome*: fetch and fast-forward onto the merged `main` before writing the advance commit
  (or refuse as a note if that's not a fast-forward), with a regression test whose fixture remote
  actually moves between checkout and push (today's fixture never does, which is why the bug is green).
- *Landed elsewhere?* No — confirmed live bug, unfixed on `main` as of `ca8dd32`.
- *Verdict*: **alive**, and arguably the most load-bearing unmerged fix in the queue (it blocks
  `standing-grant`'s "zero taps" promise from ever being true in production).

**`claude/approve-tap-regenerates-index`** (2026-09-08, 5 commits, `work/approve-tap-regenerates-index/intent.md`, 137 lines)
- *Problem*: `.github/workflows/approve.yml` runs `approve.py` then `approve_dispatch.py --commit` but
  never runs `gen_index.py`; every tap so far (`c0aa58c`, `3da8bb6`, `a903a91`) has left
  `work/<slug>/index.md` and `work/index.md` drifted, so `scripts/verify.sh` is red on a clean `main`
  checkout in the window between a tap and the next agent commit.
- *Proposed outcome*: the tap commits the approval and the regenerated indexes together, nothing else;
  it also heals any pre-existing drift it finds.
- *Landed elsewhere?* No — but the *symptom* is visible directly in Part 1's timeline: `8412525`
  ("[ci-budget] Green main again: regenerate the two drifted indexes", 2026-09-09) is exactly an agent
  manually cleaning up after an un-fixed tap, the same defect class this intent describes.
- *Verdict*: **alive**, describes a recurring, currently-manual-cleanup defect.

**`claude/handoff-close`** (2026-09-05, 4 commits, `docs/sdlc/handoff/HANDOFF.md` +
`knowledge/lessons/workflow-permissions-name-every-api.md`)
- *Problem*: the running session handoff doc still described the pre-Batch-B state; a real production
  incident (bands.yml's `pr_cycle_time_hours` job 403'd for 3 days because `permissions:` granted
  `actions: read` but not `pull-requests: read`, hidden because the other two metrics in the matrix
  stayed green) had no lesson file yet.
- *Proposed outcome*: correct the resume steps/current-state section, record both manual-check defects
  found (the bands permission bug, and eval case `skill-spec-flags-concerns` being non-deterministic
  run-to-run on the same sha), and add the lesson file.
- *Landed elsewhere?* **Yes, confirmed byte-identical.** `git diff` between the branch's
  `knowledge/lessons/workflow-permissions-name-every-api.md` and `main`'s copy is empty; it landed via
  squash-merge `38ba396` ("Handoff: record the true state at session close (#41)", 2026-09-05) — a
  commit that doesn't appear as a "Merge pull request" in `--merges` because it was squashed, not
  merged. This is the CLAUDE.md lesson-pointer line "A workflow's permissions block names every API
  surface its scripts touch... — knowledge/lessons/workflow-permissions-name-every-api.md" verified at
  the source. `main`'s `HANDOFF.md` has since moved further (2026-09-06, delegated-mode content),
  superseding both the branch and `38ba396`'s version.
- *Verdict*: **landed elsewhere** (via #41, a squash merge invisible to `--merges`), now further
  superseded on `main`.

**`claude/agent-plan-adherence-4b4mqk`** (2026-09-10, 2 commits, `work/plan-adherence/intent.md`, 223 lines)
- *Problem*: a plan re-read in a fresh/resumed session is summarized away at compaction (file list and
  step order are the first casualties); the plan-gate hook only checks the `status` word, not the
  `## Files that change` list; the file-list contract (rule 2) is judged once, at PR-open time, hours
  after a deviating edit was made; nothing marks a plan step done on disk, so a resumed session
  re-derives progress from the diff.
- *Proposed outcome*: keep the plan in front of the agent for the whole session (a `SessionStart` /
  `UserPromptSubmit` hook, none exist today) and refuse a deviation at the edit that makes it, not at
  PR-open time; make plan steps track completion; every check tested from a payload, no manual step.
- *Landed elsewhere?* No — greps for "SessionStart", "keep the plan in front of" find nothing else on
  `main`.
- *Verdict*: **alive**, freshest proposal (same day as `main`'s HEAD), not yet spec'd.

**`claude/pr-63-plan-review-ekiuva`** (2026-09-10, 3 commits, `work/ci-budget/spec.md`, 146 lines)
- *Problem*: `ci-budget`'s `intent.md` was approved on `main` (`9811483`, 2026-09-10) but the item's
  design lives only in an informal `work/ci-budget/implementation-plan.md`, not a signed `spec.md` —
  the chain artifact the CLAUDE.md rules require.
- *Proposed outcome*: a proper `spec.md` ("a draft costs nothing, a red gate is red in a minute, and no
  model runs from CI without being asked") written from the intent and read-only explorer passes, then
  reviewed by two sonnet subagents (plan-reviewer, security-reviewer) before any commit — revision 1
  took all nine of their findings. **One finding is a self-inflicted defect caught before it shipped**:
  the security pass found that the spec's first draft would have ordered a `mode` check above the
  `status` check in `check_grant_front_matter`, making a self-sign tripwire unreachable; fixed and
  pinned with a test in the same commit.
- *Landed elsewhere?* No — `work/ci-budget/spec.md` does not exist on `main`; only
  `implementation-plan.md` does.
- *Verdict*: **alive**, actively being worked (freshest branch, same day as `main`'s HEAD) and directly
  continues the in-progress `ci-budget` item.

---

## Part 4 — Pull request review history

80 merge commits total (`git log origin/main --merges`); of those, 64 map to a numbered PR via their
merge-commit subject (`Merge pull request #N` or `Merge PR #N`), plus one squash-merge (`38ba396`, "#41")
invisible to `--merges`. PR numbers run 1–58, then jump to 63–64 (Part 1 explains the 59–62 gap: CI
triage runs against an already-stale head, spent during the Actions-minutes exhaustion `ci-budget`
documents).

Because these are true merge commits (not squashes), the merge commit *body* itself is almost always
just the one-line PR title — round-by-round review detail lives in the item's own `log.md` ledger and,
where a revision was needed, `work/<slug>/revisions/N.md`. Searching those for the "introduced by" /
"defects introduced by the previous fix" pattern the CLAUDE.md conventions call out for PR #51:

**PR #51 (`approve-by-dispatch`, merged `e520f45`, 2026-09-06) — confirmed three review rounds, two
self-inflicted.** `work/approve-by-dispatch/log.md` line at commit `159b303`:

> "docs/sdlc/rules/30-conventions.md gains a convention the spec does not ask for, at the owner's
> request — a review runs on a different model from the writer... Triggered by this item's own three
> review rounds, **two of whose findings were defects introduced by the previous round's fixes**"

The commit sequence inside PR #51 shows the mechanism directly: `ddac58a` ("Review findings: four
security fixes and a flaky oracle") is immediately followed by `159b303` ("Fix the blank-slug binding my
own security fix broke") — a security fix that broke a different code path, caught and fixed in the next
commit. This is the origin of the CLAUDE.md rule that a review should run on a different model from the
one that wrote the work (`docs/sdlc/rules/30-conventions.md`, added in this same PR).

**Other rounds found, none matching "introduced by" as strongly as PR #51:**
- **PR #53 (`retire-active-pointer`, 2026-09-08)**: `revisions/1.md` records three Important findings on
  review round 1 — a base-ref-vs-HEAD ambiguity bug, a path-traversal/NUL-byte/log-injection security
  issue in `.sdlc/active` handling, and a compliance gap where the signed spec's R-2 no longer described
  the code after the first two fixes. All three read as review catching real defects in the *original*
  code, not defects the fixes themselves introduced.
- **PR #55 (`run-queue`, 2026-09-08)**: `revisions/1.md`, review round 1 found a spec/code identity
  mismatch (`claude[bot]` vs. the code's actual `github-actions[bot]`) and a described-but-unreachable
  failure mode in the lost-update re-read — both pre-existing drift between spec and code, not
  fix-introduced regressions.
- **`ci-budget` spec (branch `claude/pr-63-plan-review-ekiuva`, not yet merged, so outside the PR 45–64
  merged range strictly)**: the security pass on spec revision 1 caught the same *class* of bug as PR
  #51 — its own first draft would have made a self-sign tripwire unreachable by mis-ordering two checks
  — but this was caught before any commit shipped, so no round 2 was needed to fix a round-1 fix.
- PRs #45–50, #52, #54, #56–58, #63–64: merge-commit bodies carry no round-by-round text; their `log.md`
  ledgers (not fully read line-by-line here) would be the place to look for further instances if a
  deeper pass is wanted.

---

## Coverage

Commands run (read-only; no checkout, no repo file touched):

```
git fetch origin --quiet
git log origin/main --format='%h %ad %an %s' --date=short --reverse
git log origin/main --format='%h|%ad|%an|%s' --date=short --reverse > /tmp/full_log.txt
git log origin/main --merges --format='%h|%ad|%s' --date=short --reverse > /tmp/merges.txt
git branch -r
git log origin/main..origin/<branch> --oneline   # for each of the 11 named branches
git merge-base --is-ancestor origin/<branch> origin/main   # for the 4 zero-ahead branches
git diff origin/main...origin/<branch> --stat     # for the 7 non-zero branches
git show origin/<branch>:<path>                   # intent.md/spec.md for each proposal
git show origin/main:.sdlc/active
git log origin/main -1 --format='%h %ad %s' --date=short -- .sdlc/active
git cat-file -e origin/main:<path>                # existence checks
git ls-tree [-r] --name-only origin/main -- <dir> # docs/sdlc, .claude/agents, .claude/skills, knowledge/
git ls-files | wc -l ; git ls-files | xargs wc -l # repo totals
git ls-files knowledge/ ... | xargs wc -l         # per-idea line counts (Part 2)
git log origin/main --oneline -- <path(s)>        # commit counts per idea's files
git log origin/main --oneline --diff-filter=A -- <path(s)>  # origin commits per idea
git log -1 --format='%B' <sha>                    # merge commit bodies, PR #51/#43/#44 spot checks
git log <merge>..<merge> --format='%h' (via parents %P)  # PR→commit mapping (python/subprocess)
git show <sha> --stat / --name-only               # verifying specific commits (1c415cc, 38ba396, etc.)
diff <(git show A:file) <(git show B:file)         # confirming handoff-close landed byte-identical
git grep -n "introduced by" origin/main -- 'work/*/log.md' 'work/*/revisions/*.md'
git rev-parse HEAD ; git rev-parse origin/main ; git status --short   # confirmed working tree == origin/main
```
