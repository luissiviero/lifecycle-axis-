---
type: sdlc/rule-fragment
title: Verifying your work
description: The commands every agent runs before reporting a task complete.
targets: [claude, gemini, agents]
order: 20
tags: [rules, verify, evals]
timestamp: 2026-09-02T00:00:00Z
---
## Verifying your work
- Verify everything: `scripts/verify.sh` — must end with `VERIFY: PASS (<sha>)`
- Artifact chain for a PR: `python3 scripts/check_artifact_chain.py --base origin/main` — must end with `CHAIN: PASS`
- Evals: `scripts/run_evals.sh` — must end with `EVALS: N pass, 0 fail, ...` (see `evals/README.md`)
Run all of them before reporting a task complete and paste the last lines. If a test fails, fix the code, not the test.
- Band detector: `python3 scripts/detect_bands.py --series ...` (exit 3 = breach); metrics: `scripts/sdlc_metrics.py`
