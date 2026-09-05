#!/usr/bin/env bash
# Self-registering check (picked up by scripts/verify.sh): every eval case can fail. A `! cmd`
# assertion under `set -e` that is not the block's last command and lacks `|| exit 1` is inert
# (work/agent-evals R-3); check_eval_cases.py names the file and line.
set -u
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
python3 "$ROOT/scripts/check_eval_cases.py" --root "$ROOT"
exit $?
