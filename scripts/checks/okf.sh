#!/usr/bin/env bash
# Self-registering check (picked up by scripts/verify.sh): OKF conformance,
# warning by default. check_okf.py reads OKF_STRICT from .sdlc/config.env
# itself, so this just runs it and passes its exit code through.
set -u
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
python3 "$ROOT/scripts/check_okf.py" --root "$ROOT"
exit $?
