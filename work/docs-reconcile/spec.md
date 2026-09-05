---
type: sdlc/spec
id: docs-reconcile
title: The docs say what the code does
description: "Requirements and design for the twelve stale sentences, the strict front-matter check, honest OKF timestamps, the lessons move into knowledge/lessons/, the roadmap done marks and the .gitattributes text rule."
stage: design
status: approved
reads: intent.md
approved-by: luissiviero
approved-on: 2026-09-05
skills-applied: [security-standards]
skills-version: 60ab0f5
prompt: "Drafted from the intent, the approved 2026-09-04 implementation plan section WI-11 (docs/sdlc/handoff/PLAN.md), consensus items 10 and 11, and a read-only survey by the explorer subagent of every B12 row and every WI-11 line citation against the code on main (2223bc5), with file:line evidence for each verdict; reviewed by the orchestrator."
record:
resource: https://claude.ai/code/session_01Te8oN2GdvRupSixH4kjR8Y
tags: [docs, okf, knowledge, lessons, reconcile, consensus-item-10, consensus-item-11]
timestamp: 2026-09-05T04:25:00Z
---
# Spec: the docs say what the code does

## Requirements (each maps to an intent outcome)
Intent outcomes: (1) every B12 row true or rewritten, verdict recorded; (2) the WI-11 line items read true and the
roadmap marks WI-7 and WI-9; (3) honest timestamps and the OKF freeze; (4) complete `knowledge/` indexes; (5) a
strict front-matter check in `verify.sh`; (6) lessons in `knowledge/lessons/` with a pointer list every context file
renders; (7) `.gitattributes` LF rule.

| # | Requirement | Intent outcome | Acceptance test (machine-checkable) |
|---|-------------|----------------|--------------------------------------|
| R-1 | The twelve stale sentences (D1 table) are rewritten to describe the code; the sentence names the mechanism that holds instead | 1, 2 | for each row of D1, the row's `grep -c` oracle prints the count given; `grep -c 'branch protection' docs/sdlc/README.md` prints `2` (the two design-choice paragraphs at `:120,:124`, which already say CI holds for any model) |
| R-2 | The fifteen B12 rows have a verdict recorded here (D1), each with the evidence location; the fifteen already-true rows change nothing | 1 | D1 has 15 B12 rows + the WI-11 rows; `git diff origin/main --stat -- .sdlc/README.md scripts/check_control_plane.sh scripts/deploy.sh scripts/adopt.sh monitoring/bands.yaml .github/CODEOWNERS` is empty |
| R-3 | `docs/sdlc/lessons.md` links `knowledge/lessons/index.md` with a Markdown link; `knowledge/lessons/index.md` states the one destination (one lesson per file, linked to the incident, work item or PR that produced it) and drops the "appends a row" claim; `/sdlc-incident` gains the step that writes `knowledge/lessons/<incident-slug>.md` and its tier wording matches `bands.yaml` (1σ `log`; 2σ `diagnose` read-only with the tier's `tools:`; 3σ `propose` along the metric's `routes:`) | 2 | `grep -c '](../../knowledge/lessons/index.md)' docs/sdlc/lessons.md` prints `1`; `grep -c 'appends' knowledge/lessons/index.md` prints `0`; `grep -c 'knowledge/lessons/' .claude/skills/sdlc-incident/SKILL.md` prints `1`; `grep -c 'routes' .claude/skills/sdlc-incident/SKILL.md` prints `1` |
| R-4 | Every `docs/` and `knowledge/` document's `timestamp` is within 24 h of `git log -1 --format=%cI -- <file>` on the PR head; untouched files get the commit instant exactly (UTC, `Z`); files this item edits carry the edit time. `okf-pairing.md` records the freeze | 3 | the D3 oracle prints `TIMESTAMPS: N docs, 0 stale`; `grep -c 'no new OKF directories' docs/sdlc/okf-pairing.md` prints `1` |
| R-5 | Every `index.md` under `knowledge/` lists exactly the non-index `.md` files beside it (today true; the eight lessons keep it true) | 4 | the D3 index oracle prints nothing |
| R-6 | `scripts/check_front_matter.py` parses the front matter of every tracked `*.md` with PyYAML when present (a structural fallback otherwise), fails on a block that does not parse to a mapping, and is run by `scripts/checks/front-matter.sh`; the five failing documents are quoted | 5 | `python3 scripts/check_front_matter.py` ends `FRONT-MATTER: N docs, 0 problems`, exit 0; with a fixture whose `title:` holds an unquoted `: ` it prints the file and line and exits 1; `scripts/verify.sh` lists `front-matter.sh` as `✔ pass`; a `git stash`-free proof: `git show origin/main:docs/sdlc/metrics.md | python3 scripts/check_front_matter.py --stdin` exits 1 |
| R-7 | Eight `type: lesson` documents in `knowledge/lessons/`, one per `CLAUDE.md` lesson, each naming the work item or PR that produced it; a new fragment `docs/sdlc/rules/60-lessons.md` (`targets: [claude, gemini, agents]`) renders one pointer line per lesson; the hand-kept "Lessons learned" section leaves `CLAUDE.md`; `one-rule-source.md` marks the follow-up done | 6 | `ls knowledge/lessons/*.md | grep -vc index.md` prints `8`; `grep -c 'knowledge/lessons/' CLAUDE.md GEMINI.md AGENTS.md` prints `8` each (pointer lines only); `wc -l < CLAUDE.md` ≤ 120; `scripts/checks/context-drift.sh` passes; `grep -c '^## Lessons learned' CLAUDE.md` prints `0` |
| R-8 | `.gitattributes` forces LF on `*.md`, `*.py`, `*.yml`, `*.yaml` | 7 | `git check-attr eol CLAUDE.md scripts/verify.sh monitoring/bands.yaml .github/workflows/bands.yml scripts/gen_index.py` prints `eol: lf` five times |
| R-9 | The suite stays green and grows | all | `scripts/verify.sh` → `VERIFY: PASS`; `CHAIN: PASS` with `--slug docs-reconcile`; `EVALS: N pass, 0 fail`; `OKF: N docs, 0 warnings`; `python3 scripts/run_tests.py` count grows by the front-matter tests (D4: 6) |

## Design
### Architecture / data flow
Nothing executable changes except one new checker. Every other change is a sentence, a front-matter value, or a
new Markdown file. The renderer (`gen_context_files.py`) picks the new fragment up by filename.

**D1. The verdict table (R-1, R-2).** Verdicts from the survey of `main` at 2223bc5. "Fixed" means WI-1..10 already made the sentence true; nothing changes.

| Claim (B12 row or WI-11 line) | Where now | Verdict | Rewrite / oracle |
|---|---|---|---|
| B12-1 "agents cannot edit" `.sdlc/` | `.sdlc/README.md:1` | fixed | — |
| B12-1 same | `docs/sdlc/README.md:59` | stale | append "(this repo unlocks it for its own sessions, logged: `knowledge/decisions/self-hooks-on.md`)"; `grep -c 'self-hooks-on' docs/sdlc/README.md` prints `1` |
| B12-2 CI blocks `claude/*` control-plane PRs | `README.md:108`, `check_control_plane.sh:43,88-93` | fixed | — |
| B12-3 audit line "in the transcript" | `self-hooks-on.md:59-63`, `CLAUDE.md:74` | fixed | — |
| B12-4 deploy path "fails closed" | `merge-click-is-the-gate.md:45-48`, `deploy.yml:59`, `deploy.sh:94-101` | fixed | — |
| B12-5 deploy.sh "cannot be satisfied locally" | `deploy-from-ci.md:39-40` | stale (residual) | "refuses unless `CI` is set; any shell can set it, so guard 1 is the gate"; `grep -c 'any shell can set it' knowledge/decisions/deploy-from-ci.md` prints `2` (one exists at `:44`) |
| B12-6 `@claude` fix loop | `README.md:35`, `pr-review.yml:28,97` | stale | "`@claude` comment re-runs the review (the reviewer has no write tools; the fix is the author's)"; `grep -c 'fix loop' docs/sdlc/README.md` prints `0` |
| B12-6 same row "code owner via branch protection" | `README.md:35` | stale | "code owner at the merge click (branch protection where the plan allows it)"; see R-1 count |
| B12-7 3σ opens a PR | `README.md:38,106`, two metric docs | fixed | — |
| B12-7 same | `knowledge/metrics/post-deploy-5xx-rate.md:42` | stale (residual) | "declared route; the metric has no source yet, so nothing runs"; `grep -c 'declared' knowledge/metrics/post-deploy-5xx-rate.md` ≥ `1` |
| B12-8 rollback "rehearsed" | `.sdlc/environments.yaml:18` | fixed | — |
| B12-8 same | `README.md:37`, `deploy-from-ci.md:61-62` | stale | "rollback is a manual `workflow_dispatch` of the previous SHA (`knowledge/runbooks/rollback-deploy.md`); nothing rehearses it"; `grep -c 'rehearsed' docs/sdlc/README.md knowledge/decisions/deploy-from-ci.md` prints `0` each |
| B12-9 window 30 / `rolling_30d` | `bands.yaml:8,10`, metric docs | fixed | — |
| B12-10 loud placeholder false PASS | `adopt-script.md:96-102`, `adopt.sh:420` | fixed | — |
| B12-11 index stubs | `adopt-script.md:103-105`, `adopt.sh:366-393` | fixed | — |
| B12-12 `log.md` at every gate | `30-conventions.md:20`; 13 ledgers with 7–12 lines | fixed (practice) | — |
| B12-13 `sdlc_metrics.py` "prints the git-derived ones" | `docs/sdlc/metrics.md:11-12`, `sdlc_metrics.py:18-22` | stale | "prints four of them (intent→spec and spec→plan hours, two rework counts) for the Capture-intent and Requirements rows"; `grep -c 'four' docs/sdlc/metrics.md` ≥ `1` |
| B12-14 `## Files` heading | `check_artifact_chain.py:23` docstring; `:301,:306` | fixed (docstring nit) | docstring says `## Files that change`; `grep -c '"## Files"' scripts/check_artifact_chain.py` prints `0` |
| B12-15 CODEOWNERS mirrors config.env | `CODEOWNERS:14-29`, `config.env:9,12` | fixed | — |
| WI-11 README:27 "can run headless on intent merge" | `README.md:27` | stale | "(not automated in this repo; see step 6 of Using it)"; `grep -c 'not automated' docs/sdlc/README.md` prints `1` |
| WI-11 README:103 "branch protection" | `README.md:103` | stale | "the merge click on this plan (`knowledge/decisions/merge-click-is-the-gate.md`); branch protection where the plan allows it"; `grep -c 'merge-click-is-the-gate' docs/sdlc/README.md` prints `2` (this row and `:112`) |
| WI-11 README:112 "Environment's required reviewers" | `README.md:112` | partially stale | add "(not enforceable on the Free plan: `merge-click-is-the-gate.md`)" |
| WI-11 README:140 fill seeded sections | `README.md:140-142` | fixed | — |
| WI-11 README:147 "point `bands.yaml` at real metrics; invoke `/sdlc-incident` at 2σ" | `README.md:147` | stale | "add your own metrics beside the two GitHub ones `bands.yaml` already reads; `bands.yml` diagnoses at 2σ and 3σ and files an issue with a drafted intent"; `grep -c 'files an issue' docs/sdlc/README.md` ≥ `2` |
| WI-11 verification row | `README.md` "Verified before done" row | stale (B13 first bullet) | add "`VERIFY_CMDS` runs the chain check against `HEAD` (structure only); the diff-in-plan check is `--base origin/main`, which CI runs"; `grep -c 'structure only' docs/sdlc/README.md` prints `1` |
| WI-11 `rules/index.md:10-11` | `gen_context_files.py:37,140` | stale | "in `(order, filename)` order" and the real marker `<!-- BEGIN GENERATED: docs/sdlc/rules — … -->`; `grep -c 'filename order' docs/sdlc/rules/index.md` prints `0`; `grep -c 'BEGIN GENERATED:' docs/sdlc/rules/index.md` prints `1` |
| WI-11 `lessons.md:11-12` | backtick spans | stale | Markdown link (R-3) |
| WI-11 `knowledge/lessons/index.md:11-12` + `/sdlc-incident` | no lesson step in the skill | stale both ways | R-3 |
| WI-11 skill step 2 tiers | `SKILL.md:8` vs `bands.yaml:12-14` | stale | R-3 |
| WI-11 roadmap 116-119 | items 12 and 13 carry no done mark | stale | "**Done (WI-7):** `detect_bands.py`, `github_metrics.py`, `bands_config.py`, `bands.yml`" on item 13's detector clause; "**Done (WI-9):** `agent-evals.yml` on every config change and nightly with `--require-claude`; `run_evals.sh --kind/--only/--list`" on item 12; `grep -c 'Done (WI-7)\|Done (WI-9)' docs/sdlc/phase-2-roadmap.md` prints `2` |
| WI-11 `gemini-parity.md:84` "No Gemini hook is written" | `gemini-hooks.md:48-51` | stale | append "(superseded 2026-09-02: wired in `.gemini/settings.json`, `knowledge/decisions/gemini-hooks.md`)"; `grep -c 'superseded 2026-09-02' docs/sdlc/spikes/gemini-parity.md` prints `1`; additions only: `git diff origin/main -- docs/sdlc/spikes/ | grep -c '^-[^-]'` prints `1` (the one replaced line) |

**D2. The front-matter checker (R-6).** `scripts/check_front_matter.py`, stdlib plus optional PyYAML, modelled on `check_eval_cases.py`:
- Input: every path from `git ls-files -- '*.md'` under `--root` (default: the repository root), or one document on
  `--stdin`. A file without a leading `---` line is skipped and not counted. The block ends at the next line that is
  exactly `---` (CRLF folded to LF first, per the CLAUDE.md lesson).
- With PyYAML: `yaml.safe_load(block)` must return a `dict`; a `yaml.YAMLError` is reported as
  `<path>:<line>: <first line of the error>` where the line is the block-relative line from the error's `problem_mark`
  plus the offset of the block in the file.
- Without PyYAML: for each `key: value` line whose value is an unquoted plain scalar, report it when the value
  contains `: ` or ` #`, or starts with one of `[]{}&*!|>'"%@`` ` when the rest is not a flow sequence or mapping.
  The fallback is the rule that catches every failure the five documents have today; the last line says which
  mode ran (`(PyYAML)` / `(structural)`), as `workflow-yaml.sh` does.
- Output: one line per problem, then `FRONT-MATTER: N docs, M problems`; exit 1 when M > 0. `--root` for tests.
- `scripts/checks/front-matter.sh`: the eight-line self-registering wrapper (`set -u`, `ROOT` from `git rev-parse`,
  exec the script, pass the exit code). Control plane: the PR asks for `control-plane-approved`.
- Fixes: quote the `title`/`description` in `docs/sdlc/metrics.md`, `docs/sdlc/phase-2-roadmap.md`,
  `knowledge/decisions/merge-click-is-the-gate.md`, `docs/sdlc/handoff/HANDOFF.md`, `docs/sdlc/handoff/PLAN.md`
  (five documents; the intent said six because `PLAN.md` has two such lines). Quoting changes no value the kit's
  parser reads: `_fm_value` strips matching quotes.

**D3. Timestamps, indexes, freeze (R-4, R-5).**
- One-off, not committed: for each `docs/**/*.md` and `knowledge/**/*.md` on the branch, if the file is not edited
  by this item, set `timestamp:` to `git log -1 --format=%cI -- <file>` converted to UTC `Z`; if it is edited, set
  it to the edit instant. `work/**` is untouched (the ledger is its record).
- Oracle (kept in the spec, not the repo). "Last change" means the last commit that changed a line other than
  `timestamp:` itself; otherwise the pass that sets a timestamp to the commit date would move that date, and every
  untouched file would read stale by construction (found in implementation; the plan's Deviations log has it):
  ```
  n=0; for f in $(git ls-files 'docs/**/*.md' 'knowledge/**/*.md' 'docs/*.md' 'knowledge/*.md' | sort -u); do
    ts=$(sed -n 's/^timestamp:[[:space:]]*//p' "$f" | head -1); [ -z "$ts" ] && continue
    c=""; for sha in $(git log --format=%H -- "$f"); do
      if git show --format= "$sha" -- "$f" | grep -E '^[-+]' | grep -vE '^(\+\+\+|---) |^[-+]timestamp:' | grep -q .; then c=$(git show -s --format=%cI "$sha"); break; fi
    done
    [ -z "$c" ] && c=$(git log -1 --format=%cI -- "$f")
    python3 -c 'import sys,datetime as d; a,b=[d.datetime.fromisoformat(x.replace("Z","+00:00")) for x in sys.argv[1:]]; sys.exit(abs((a-b).total_seconds())>86400)' "$ts" "$c" || { echo "STALE $f $ts $c"; n=$((n+1)); }
  done; echo "TIMESTAMPS: stale=$n"
  ```
  The expected last line is `TIMESTAMPS: stale=0`.
- Index oracle: for each `knowledge/*/`, the set of non-index `.md` files in the directory (`ls`) equals the set of
  Markdown link targets ending in `.md` inside its `index.md` (extracted with `grep -o`); prints nothing on agreement.
- `docs/sdlc/okf-pairing.md` gains, under "Where not to pair", the sentence: "No new OKF directories until
  `lessons/` or `services/` has content that is not an index (frozen 2026-09-05, consensus item 10); `lessons/`
  gains its first content in `work/docs-reconcile`."

**D4. Lessons (R-7).**
- Eight files, `type: lesson`, front matter `title`, `description`, `tags: [lesson, …]`, `timestamp`, `resource`
  (the work item or PR), body: "What happened", "Rule", "Where it is enforced" (the hook, check or "prose only").
  Names, by the mistake: `control-plane-unlock-is-advisory.md`, `one-path-spelling-in-guards.md`,
  `test-lib-changes-from-a-second-shell.md`, `fold-crlf-before-comparing.md`, `skills-spell-template-headings.md`,
  `plan-bullets-start-with-the-path.md`, `ledger-slot-holds-status-only.md`, `send-ledger-lines-in-a-fenced-block.md`.
- `docs/sdlc/rules/60-lessons.md` (`order: 60`, all targets): heading `## Lessons (one file each in knowledge/lessons/)`,
  a one-line rule ("a mistake made twice becomes a file there and a pointer line here, in the same PR; delete the
  pointer when a hook makes the mistake impossible"), then eight lines of the form
  `- <one clause> — knowledge/lessons/<name>.md`. The heading differs from the `## Lessons learned` section
  `adopt.sh` seeds in an adopter's `CLAUDE.md`, so an adopted repo has both without a clash: the kit's lessons about
  the kit's tooling, and the adopter's own.
- `CLAUDE.md` loses lines 72–81 (the hand-kept section); the three context files are regenerated. Budget: 81 − 10 + 11 ≈ 82.
- `knowledge/lessons/index.md` lists the eight and restates the naming rule as "one lesson per file, named by the
  mistake, linked to the incident, work item or PR that produced it; incidents use the incident slug".
- Tests for D2 (`scripts/test_check_front_matter.py`, 6): unquoted `: ` in a title is reported with file and line;
  a quoted value passes; a file without front matter is skipped and not counted; a block that parses to a list is
  a problem; `--stdin` reports on one document; the last line format and exit codes.

### Interfaces (APIs, events, schemas) — exact shapes
- `python3 scripts/check_front_matter.py [--root DIR] [--stdin]` → stdout `<path>:<line>: <problem>` lines then
  `FRONT-MATTER: N docs, M problems (PyYAML|structural)`; exit 0/1; exit 2 on a bad argument.
- `docs/sdlc/rules/60-lessons.md` front matter: `type: sdlc/rule-fragment`, `targets: [claude, gemini, agents]`, `order: 60`.

### Data and migrations
None. Front-matter values are re-quoted, never changed.

### Failure modes and how they surface
- A future document with an unquoted `: ` fails `verify.sh` with file and line (was: a GitHub render banner).
- A machine without PyYAML runs the structural fallback and says so in the last line.
- A timestamp that drifts again is not checked by CI (consensus item 10 froze OKF); the D3 oracle stays in this spec
  for the next sweep.

## Areas of concern (flagged; product owner resolves each with its policy owner before Build)
- C1: `scripts/checks/front-matter.sh` is a control-plane file — policy: rule 3 — contradiction? no (WI-9 set the
  precedent with `eval-cases.sh`) — owner: luissiviero — resolution: `control-plane-approved` on the PR.
- C2: the kit's eight lessons render into every adopter's `CLAUDE.md`/`GEMINI.md` through the shared fragment —
  policy: one rule source (`one-rule-source.md`) — contradiction? no; they are lessons about the kit's own tooling
  (`jq`, path guards, CRLF, ledger and plan formats), which adopters run — owner: luissiviero — resolution: keep; an
  adopter deletes a pointer line the way they would any fragment line.
- C3: the `sdlc-gate` triage step runs `claude -p` in an untrusted workspace ("Ignoring 7 permissions.allow entries")
  — policy: rule 3 (workflows) — out of this item; proposed in the PR description with the `agent-evals.yml:45-57`
  trust step as the model — owner: luissiviero.
- C4: `.sdlc/approvers.yaml` could list `<your-github-handle>` under `never-approve` so a forgotten replacement can
  never approve (`adopt-script.md:158`) — policy: never-unlock file — out of this item; proposed in the PR description.

## Open questions carried from intent.md
- Fail immediately vs warn first for the front-matter check: proposed fail (intent Q1); this spec assumes it.
- One lesson file each vs grouped: proposed one each (intent Q2); D4 assumes it.
- Loosen "one per incident" to "one per file, whatever produced it": proposed yes (intent Q3); D4 assumes it.

## Decisions (ADR-style: context → decision → consequences)
- D-a: PyYAML is optional → the checker has a structural fallback and names its mode, like `workflow-yaml.sh` → no new
  dependency; the strict check runs wherever PyYAML is (the runner, this session).
- D-b: the survey's "fixed" rows change nothing → fifteen locations stay byte-identical (R-2 oracle) → the diff is
  the twelve rewrites, and a reviewer can check each against D1.
- D-c: `sdlc_metrics.py`'s off-by-one (B12-13, B13) is a code change → not made here (intent: B13 out of scope); noted
  in Not doing with the fix.
- D-d: timestamps are set once by a one-off script and not checked by CI → honest today, and the freeze means
  nothing new lands; the oracle lives in D3 for the next sweep.

## Gotchas found while reading the codebase
- `PLAN.md` counted five lessons at `CLAUDE.md:68-72`; there are eight at `:73-81` (Batch A and B added three).
- `docs/sdlc/handoff/HANDOFF.md` carries a `timestamp` one day after its last commit (future-dated); the one-off
  script corrects it like any other.
- `check_okf.py` validates only Markdown-syntax links (`LINK_RE`: bracketed text followed by a parenthesised target), so
  a backtick path is invisible to it (R-3).
- `section()` in `check_artifact_chain.py` matches by prefix, which is why `## Files that change` already works;
  only the docstring says `## Files`.
- `git ls-files 'docs/**/*.md'` needs the quotes: the shell would expand `**` as `*` and miss nested files.

## Not doing
- `scripts/sdlc_metrics.py:12` `commits_after` off-by-one (B13): `max(0, len(out) - 1)` subtracts one whether or
  not the anchoring commit touched the path; the fix is to count commits strictly after the anchor by SHA. Own item.
- The `sdlc-gate` triage trust step (C3) and the `never-approve` placeholder entry (C4): PR description proposals.
- The other B13 items; the Antigravity adapter; the Gemini CLI account; consensus item 12.
- A CI check on timestamps (D-d); OKF strict mode (consensus item 10 keeps it a warning).
