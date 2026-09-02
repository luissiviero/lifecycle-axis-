#!/usr/bin/env bash
# Self-registering check (picked up by scripts/verify.sh): every workflow in
# .github/workflows/ declares a top-level `permissions:` block, never grants
# `contents: write` or `permissions: write-all`, and never triggers on
# `pull_request_target`. Just runs check_workflow_permissions.py and passes
# its exit code through.
set -u
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
python3 "$ROOT/scripts/check_workflow_permissions.py" --root "$ROOT"
exit $?
