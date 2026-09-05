#!/usr/bin/env bash
# Self-registering check (picked up by scripts/verify.sh): the front matter of every tracked Markdown
# file parses as strict YAML (work/docs-reconcile R-6). The kit's own parser tolerates an unquoted
# `title: A: b`; GitHub's renderer shows an error banner instead of the document. PyYAML when present,
# a structural fallback otherwise; check_front_matter.py names the file and line.
set -u
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
python3 "$ROOT/scripts/check_front_matter.py" --root "$ROOT"
exit $?
