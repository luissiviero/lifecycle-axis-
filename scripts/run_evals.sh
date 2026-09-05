#!/usr/bin/env bash
# Eval runner (Test play). Each evals/cases/<name>.yaml has:
#   kind: hook | skill | e2e
#   prompt: "..."            optional; when present and `claude` plus ANTHROPIC_API_KEY or
#                            CLAUDE_CODE_OAUTH_TOKEN (from `claude setup-token`) are available,
#                            the prompt runs non-interactively with bounded tools before `check`.
#   allowed_tools: "..."     optional; default "Read,Grep,Glob,Bash(scripts/verify.sh)"
#   setup: <cmd> | block     optional; runs before the prompt (and before check); a failing
#                            setup fails the case with its output
#   check: <cmd> | block     deterministic oracle; exit 0 = pass
# Without Claude available, prompt cases are skipped (reported), hook cases still run; with
# --require-claude a skipped prompt case counts as a failure (nightly CI, so an expired
# credential is a red run, work/agent-evals).
#
# Flags:
#   --only <glob>       run only cases whose basename (without .yaml) matches <glob>
#   --kind <kind>       run only cases with kind: hook|skill|e2e (a kind matching no case
#                       is not an error: EVALS: 0 pass, 0 fail, 0 skipped, exit 0)
#   --list              print each selected case's name and kind, one per line; exit 0
#   --require-claude    a prompt case that cannot run (no claude or no credential) is a failure
#   -h, --help          print this usage
# An unknown flag prints usage to stderr and exits 2.
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT" || exit 1

usage() {
  cat <<'EOF'
Usage: scripts/run_evals.sh [--only <glob>] [--kind hook|skill|e2e] [--list] [--require-claude] [-h]
  --only <glob>       run only cases whose basename (without .yaml) matches <glob>
  --kind <kind>       run only cases with kind: <kind> (hook|skill|e2e)
  --list              print each selected case's name and kind, then exit 0
  --require-claude    a prompt case that cannot run (no claude or no credential) counts as a failure
  -h, --help          show this help
EOF
}

field() { awk -v k="$1" '
  $0 ~ "^"k":[ \t]*\\|[ \t]*$" {blk=1; next}
  $0 ~ "^"k":" {sub("^"k":[ \t]*",""); gsub(/^"|"$/,""); print; exit}
  blk && /^[ \t]+/ {sub(/^[ \t]+/,""); print; next}
  blk {exit}' "$2"; }

only=""; kind=""; list_only=0; require_claude=0
while [ $# -gt 0 ]; do
  case "$1" in
    --only) only="${2:-}"; shift 2 ;;
    --kind) kind="${2:-}"; shift 2 ;;
    --list) list_only=1; shift ;;
    --require-claude) require_claude=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done

# The kit repo sets SDLC_CONTROL_PLANE_UNLOCK in its own .claude/settings.json so agents can
# maintain the control plane here (knowledge/decisions/self-hooks-on.md). Hook oracles must see
# the guards locked, as an adopter's session would; scripts/hooktest.py strips it the same way.
unset SDLC_CONTROL_PLANE_UNLOCK
pass=0; fail=0; skip=0
have_claude=0; command -v claude >/dev/null 2>&1 && { [ -n "${ANTHROPIC_API_KEY:-}" ] || [ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; } && have_claude=1
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
  prompt="$(field prompt "$f")"; check="$(field check "$f")"; setup="$(field setup "$f")"
  tools="$(field allowed_tools "$f")"; [ -z "$tools" ] && tools="Read,Grep,Glob,Bash(scripts/verify.sh)"
  if [ -n "$prompt" ] && [ "$have_claude" != 1 ]; then
    # Decide before any setup runs, so a case that cannot run leaves no fixture behind.
    if [ "$require_claude" = 1 ]; then
      echo "✘ $name (prompt case, no Claude runner; --require-claude)"; fail=$((fail+1))
    else
      echo "– $name (skipped: prompt case, no Claude runner)"; skip=$((skip+1))
    fi
    continue
  fi
  # A fixture the case needs (an approved predecessor, a buggy module) is staged by `setup:`;
  # its failure is the case's failure, with the output, never a silent pass of the check.
  if [ -n "$setup" ]; then
    setup_out="$(mktemp)"
    if ! bash -c "$setup" >"$setup_out" 2>&1; then
      echo "✘ $name (setup failed)"; sed 's/^/    /' "$setup_out"; rm -f "$setup_out"; fail=$((fail+1)); continue
    fi
    rm -f "$setup_out"
  fi
  if [ -n "$prompt" ]; then
    claude -p "$prompt" --allowedTools "$tools" --output-format json > "evals/.last-$name.json" 2>/dev/null || true
  fi
  # The oracle's output is kept and printed under a failing case, so a red eval says why in the
  # CI log; a passing case prints nothing extra (work/loop-protection).
  out="$(mktemp)"
  if [ -n "$check" ] && bash -c "$check" >"$out" 2>&1; then
    echo "✔ $name"; pass=$((pass+1))
  else
    echo "✘ $name"; sed 's/^/    /' "$out"; fail=$((fail+1))
  fi
  rm -f "$out"
done
if [ "$list_only" = 1 ]; then exit 0; fi
echo "EVALS: $pass pass, $fail fail, $skip skipped"
[ "$fail" = 0 ]
