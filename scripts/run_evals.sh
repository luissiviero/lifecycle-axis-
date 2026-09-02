#!/usr/bin/env bash
# Runs every eval case in evals/cases/*.yaml and records pass/fail.
# Placeholder harness: each case names a prompt and a `check` command (inline or `check: |` block).
# Replace with a runner that drives your agent (e.g. `claude -p`) and then runs `check`.
set -u
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT" || exit 1
pass=0; fail=0
for f in evals/cases/*.yaml; do
  [ -e "$f" ] || continue
  name="$(basename "$f" .yaml)"
  check="$(awk '
    /^check:[ \t]*\|[ \t]*$/ {blk=1; next}
    /^check:/ {sub(/^check:[ \t]*/,""); print; exit}
    blk && /^[ \t]+/ {sub(/^[ \t]+/,""); print; next}
    blk {exit}' "$f")"
  if [ -n "$check" ] && bash -c "$check" >/dev/null 2>&1; then echo "✔ $name"; pass=$((pass+1)); else echo "✘ $name"; fail=$((fail+1)); fi
done
echo "EVALS: $pass pass, $fail fail"
[ "$fail" = 0 ]
