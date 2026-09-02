#!/usr/bin/env bash
# verify.sh check: CLAUDE.md / GEMINI.md / AGENTS.md match the fragments in RULES_SRC.
set -u
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
python3 "$ROOT/scripts/gen_context_files.py" --check
