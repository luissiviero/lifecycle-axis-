#!/usr/bin/env bash
# Eval runner (Test play). Each evals/cases/<name>.yaml has:
#   kind: hook | skill | e2e
#   prompt: "..."            optional; when present and `claude` + ANTHROPIC_API_KEY are available,
#                            the prompt runs non-interactively with bounded tools before `check`.
#   allowed_tools: "..."     optional; default "Read,Grep,Glob,Bash(scripts/verify.sh)"
#   check: <cmd> | block     deterministic oracle; exit 0 = pass
# Without Claude available, prompt cases are skipped (reported), hook cases still run.
#
# Flags:
#   --only <glob>   run only cases whose basename (without .yaml) matches <glob>
#   --kind <kind>   run only cases with kind: hook|skill|e2e (a kind matching no case
#                   is not an error: EVALS: 0 pass, 0 fail, 0 skipped, exit 0)
#   --list          print each selected case's name and kind, one per line; exit 0
#   -h, --help      print this usage
# An unknown flag prints usage to stderr and exits 2.
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT" || exit 1

usage() {
  cat <<'EOF'
Usage: scripts/run_evals.sh [--only <glob>] [--kind hook|skill|e2e] [--list] [-h]
  --only <glob>   run only cases whose basename (without .yaml) matches <glob>
  --kind <kind>   run only cases with kind: <kind> (hook|skill|e2e)
  --list          print each selected case's name and kind, then exit 0
  -h, --help      show this help
EOF
}

field() { awk -v k="$1" '
  $0 ~ "^"k":[ \t]*\\|[ \t]*$" {blk=1; next}
  $0 ~ "^"k":" {sub("^"k":[ \t]*",""); gsub(/^"|"$/,""); print; exit}
  blk && /^[ \t]+/ {sub(/^[ \t]+/,""); print; next}
  blk {exit}' "$2"; }

only=""; kind=""; list_only=0
while [ $# -gt 0 ]; do
  case "$1" in
    --only) only="${2:-}"; shift 2 ;;
    --kind) kind="${2:-}"; shift 2 ;;
    --list) list_only=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done

pass=0; fail=0; skip=0
have_claude=0; command -v claude >/dev/null 2>&1 && [ -n "${ANTHROPIC_API_KEY:-}" ] && have_claude=1
for f in evals/cases/*.yaml; do
  [ -e "$f" ] || continue
  name="$(basename "$f" .yaml)"
  if [ -n "$only" ]; then
    case "$name" in
      $only) ;;
      *) continue ;;
    esac
  fi
  case_kind="$(field kind "$f")"
  if [ -n "$kind" ] && [ "$case_kind" != "$kind" ]; then continue; fi
  if [ "$list_only" = 1 ]; then echo "$name $case_kind"; continue; fi
  prompt="$(field prompt "$f")"; check="$(field check "$f")"
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
if [ "$list_only" = 1 ]; then exit 0; fi
echo "EVALS: $pass pass, $fail fail, $skip skipped"
[ "$fail" = 0 ]
