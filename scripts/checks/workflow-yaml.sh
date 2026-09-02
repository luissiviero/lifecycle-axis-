#!/usr/bin/env bash
# Every workflow file must parse as YAML. GitHub rejects an unparseable workflow silently from the
# PR's point of view (a failed run with no jobs, listed by file path), which is how sdlc-gate.yml sat
# broken for a day: an unquoted step name containing ": ". Uses PyYAML when available; otherwise a
# minimal structural check (balanced quotes per line, no tabs) so the check never blocks on a missing
# dependency.
set -u
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
status=0
if python3 -c "import yaml" 2>/dev/null; then
  for f in "$ROOT"/.github/workflows/*.yml "$ROOT"/.github/workflows/*.yaml; do
    [ -e "$f" ] || continue
    if ! python3 -c "import sys, yaml; yaml.safe_load(open(sys.argv[1]))" "$f" 2>/tmp/wf-yaml-err.$$; then
      echo "YAML ERROR: ${f#"$ROOT"/}: $(tr '\n' ' ' < /tmp/wf-yaml-err.$$)"; status=1
    fi
  done
  rm -f /tmp/wf-yaml-err.$$
  [ "$status" = 0 ] && echo "WORKFLOW-YAML: all files parse (PyYAML)"
else
  for f in "$ROOT"/.github/workflows/*.yml "$ROOT"/.github/workflows/*.yaml; do
    [ -e "$f" ] || continue
    if grep -nP '\t' "$f" >/dev/null; then echo "YAML ERROR: ${f#"$ROOT"/}: tab character"; status=1; fi
    # an unquoted plain scalar after `name:` that contains ": " is the defect that bit sdlc-gate.yml
    if grep -nE '^\s*-?\s*name:\s+[^"'"'"'|>].*: ' "$f" >/dev/null; then
      echo "YAML ERROR: ${f#"$ROOT"/}: unquoted 'name:' value contains ': ' (quote the whole value)"; status=1
    fi
  done
  [ "$status" = 0 ] && echo "WORKFLOW-YAML: structural check passed (PyYAML not installed)"
fi
exit $status
