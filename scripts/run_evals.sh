#!/usr/bin/env bash
# Eval runner (Test play). Each evals/cases/<name>.yaml has:
#   kind: hook | skill | e2e
#   prompt: "..."            optional; when present and `claude` + ANTHROPIC_API_KEY are available,
#                            the prompt runs non-interactively with bounded tools before `check`.
#   allowed_tools: "..."     optional; default "Read,Grep,Glob,Bash(scripts/verify.sh)"
#   check: <cmd> | block     deterministic oracle; exit 0 = pass
# Without Claude available, prompt cases are skipped (reported), hook cases still run.
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT" || exit 1
field() { awk -v k="$1" '
  $0 ~ "^"k":[ \t]*\\|[ \t]*$" {blk=1; next}
  $0 ~ "^"k":" {sub("^"k":[ \t]*",""); gsub(/^"|"$/,""); print; exit}
  blk && /^[ \t]+/ {sub(/^[ \t]+/,""); print; next}
  blk {exit}' "$2"; }
pass=0; fail=0; skip=0
have_claude=0; command -v claude >/dev/null 2>&1 && [ -n "${ANTHROPIC_API_KEY:-}" ] && have_claude=1
for f in evals/cases/*.yaml; do
  [ -e "$f" ] || continue
  name="$(basename "$f" .yaml)"; prompt="$(field prompt "$f")"; check="$(field check "$f")"
  tools="$(field allowed_tools "$f")"; [ -z "$tools" ] && tools="Read,Grep,Glob,Bash(scripts/verify.sh)"
  if [ -n "$prompt" ]; then
    if [ "$have_claude" = 1 ]; then
      claude -p "$prompt" --allowedTools "$tools" --output-format json > "evals/.last-$name.json" 2>/dev/null || true
    else
      echo "– $name (skipped: prompt case, no Claude runner)"; skip=$((skip+1)); continue
    fi
  fi
  if [ -n "$check" ] && bash -c "$check" >/dev/null 2>&1; then echo "✔ $name"; pass=$((pass+1)); else echo "✘ $name"; fail=$((fail+1)); fi
done
echo "EVALS: $pass pass, $fail fail, $skip skipped"
[ "$fail" = 0 ]
