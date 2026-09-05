---
type: sdlc/rule-fragment
title: Verifying your work
description: The commands every agent runs before reporting a task complete.
targets: [claude, gemini, agents]
order: 20
tags: [rules, verify, evals]
timestamp: 2026-09-05T02:28:00Z
---
## Verifying your work
- Verify everything: `scripts/verify.sh` — must end with `VERIFY: PASS (<sha>)`; it also runs every `scripts/checks/*.sh`
- Artifact chain for a PR: `python3 scripts/check_artifact_chain.py --base origin/main` — must end with `CHAIN: PASS`
- Evals: `scripts/run_evals.sh` — must end with `EVALS: N pass, 0 fail, ...` (`--kind`/`--only`/`--list` select cases; see `evals/README.md`)
- OKF conformance: `python3 scripts/check_okf.py` — must end with `OKF: N docs, 0 warnings` (warning-only unless `OKF_STRICT=1`)
Run all of them before reporting a task complete and paste the last lines. If a test fails, fix the code, not the test.
- Regenerate before committing — verify fails on drift: `python3 scripts/gen_index.py` and `python3 scripts/gen_context_files.py`
- Band detector: `python3 scripts/detect_bands.py --series ...` (exit 3 = breach, 2 = bad input); series: `scripts/github_metrics.py`; workflow matrix: `scripts/bands_config.py`; git metrics: `scripts/sdlc_metrics.py`
- Keep this file under `MAX_CONTEXT_LINES` (120): `wc -l CLAUDE.md` after regenerating; trim prose, never rules, if over
