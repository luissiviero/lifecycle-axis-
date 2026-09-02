#!/usr/bin/env bash
# Guard the control plane (PROTECTED_PATHS) against agent-authored changes that no human has
# reviewed. Run from CI (sdlc-gate.yml) or by hand: scripts/check_control_plane.sh <base-ref>
#
# Env (set by the caller; all optional, safe defaults below):
#   SDLC_PR_AUTHOR_TYPE   GitHub PR author's account type, e.g. "Bot" or "User".
#   SDLC_PR_HEAD_REF      PR head branch name.
#   SDLC_PR_LABELS        PR labels: newline-, comma- or JSON-array-formatted.
#   CONTROL_PLANE_LABEL   overrides the value sourced from .sdlc/config.env.
#
# Exit 0 on: no protected-path changes; human-authored change (informational only); or an
# agent-authored change carrying the exemption label. Exit 1 on: an agent-authored change to
# protected paths without the label, or a git-diff failure.
set -u

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$ROOT" ]; then
  echo "CONTROL-PLANE: not a git repository" >&2
  exit 1
fi
# shellcheck disable=SC1091
[ -f "$ROOT/.sdlc/config.env" ] && . "$ROOT/.sdlc/config.env"

BASE="${1:-}"
if [ -z "$BASE" ]; then
  echo "Usage: scripts/check_control_plane.sh <base-ref>" >&2
  exit 1
fi

: "${PROTECTED_PATHS:=}"
: "${CONTROL_PLANE_LABEL:=control-plane-approved}"
: "${SDLC_PR_AUTHOR_TYPE:=}"
: "${SDLC_PR_HEAD_REF:=}"
: "${SDLC_PR_LABELS:=}"
AGENT_BRANCH_PREFIXES="${AGENT_BRANCH_PREFIXES:-claude/}"

diff_out="$(cd "$ROOT" && git diff --name-only "${BASE}...HEAD" 2>&1)"
rc=$?
if [ $rc -ne 0 ]; then
  echo "CONTROL-PLANE: could not diff against base '$BASE': $diff_out" >&2
  exit 1
fi

touched=""
while IFS= read -r f; do
  [ -z "$f" ] && continue
  for prefix in $PROTECTED_PATHS; do
    case "$f" in
      "$prefix"|"$prefix"/*)
        touched="$touched
$f"
        break
        ;;
    esac
  done
done <<EOF
$diff_out
EOF
touched="$(printf '%s' "$touched" | sed '/^$/d')"

if [ -z "$touched" ]; then
  echo "CONTROL-PLANE: clean"
  exit 0
fi

is_agent_branch() {
  local ref="$1" prefix
  for prefix in $AGENT_BRANCH_PREFIXES; do
    case "$ref" in
      "$prefix"*) return 0 ;;
    esac
  done
  return 1
}

agent_authored=0
if [ "$SDLC_PR_AUTHOR_TYPE" = "Bot" ] || is_agent_branch "$SDLC_PR_HEAD_REF"; then
  agent_authored=1
fi

if [ "$agent_authored" -eq 0 ]; then
  printf '%s\n' "$touched"
  echo "CONTROL-PLANE: human-authored, review by CODEOWNERS"
  exit 0
fi

# Parse SDLC_PR_LABELS leniently: newline-, comma- or JSON-array-formatted. Extract tokens made
# of [A-Za-z0-9._-]+ so any of those separators (and surrounding JSON punctuation/quotes) works.
has_label=0
label_lc="$(printf '%s' "$CONTROL_PLANE_LABEL" | tr '[:upper:]' '[:lower:]')"
while IFS= read -r tok; do
  [ -z "$tok" ] && continue
  tok_lc="$(printf '%s' "$tok" | tr '[:upper:]' '[:lower:]')"
  if [ "$tok_lc" = "$label_lc" ]; then
    has_label=1
    break
  fi
done <<EOF
$(printf '%s' "$SDLC_PR_LABELS" | grep -oE '[A-Za-z0-9._-]+')
EOF

if [ "$has_label" -eq 1 ]; then
  printf '%s\n' "$touched"
  echo "CONTROL-PLANE: EXEMPT (label $CONTROL_PLANE_LABEL applied by a human with write access)"
  exit 0
fi

printf '%s\n' "$touched"
echo "CONTROL-PLANE: BLOCKED — agent-authored change to protected paths. A human with write access applies the label '$CONTROL_PLANE_LABEL' after reviewing the diff above; the check re-runs on label."
exit 1
