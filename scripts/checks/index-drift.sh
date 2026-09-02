#!/usr/bin/env bash
# Self-registering check (picked up by scripts/verify.sh): work/index.md and
# work/<slug>/index.md must match what scripts/gen_index.py would generate.
set -u
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
python3 "$ROOT/scripts/gen_index.py" --check --root "$ROOT"
exit $?
