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
#
# Agent-authored means any of: the PR author is a Bot; the head ref starts with an entry of
# AGENT_BRANCH_PREFIXES (.sdlc/config.env; default "claude/ kit/ spike/"); or a commit in
# <base-ref>..HEAD carries a `Co-Authored-By: ... Claude` or `Claude-Session:` trailer. The kit's
# own sessions commit under the owner's identity on kit/ and spike/ branches with those trailers,
# so before the last two rules 11 of its 13 control-plane PRs were never checked
# (work/control-plane-visibility, consensus item 4).
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
: "${AGENT_BRANCH_PREFIXES:=claude/ kit/ spike/}"   # also a key in .sdlc/config.env (config wins)
AGENT_TRAILER_RE='^(Co-Authored-By:.*Claude|Claude-Session:)'

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

# A trailer anywhere in the PR's own commits (base..HEAD, never the base's history) marks the PR
# agent-authored. A failed git log reads as "no trailer": the diff above already failed the run
# for an unresolvable base, and a shallow clone is the caller's problem (sdlc-gate.yml fetches
# full history).
has_agent_trailer() { git -C "$ROOT" log --format=%B "${BASE}..HEAD" 2>/dev/null | grep -Eiq "$AGENT_TRAILER_RE"; }

agent_authored=0
if [ "$SDLC_PR_AUTHOR_TYPE" = "Bot" ] || is_agent_branch "$SDLC_PR_HEAD_REF" || has_agent_trailer; then
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
# Whole-label comparison: split on commas/newlines, strip JSON brackets, quotes and spaces, then
# compare the complete label. A label that merely contains the token (e.g. "not
# control-plane-approved") must not exempt (security review, nit 5).
while IFS= read -r tok; do
  tok="${tok#"${tok%%[![:space:]]*}"}"; tok="${tok%"${tok##*[![:space:]]}"}"
  tok="${tok#\"}"; tok="${tok%\"}"; tok="${tok#\'}"; tok="${tok%\'}"
  [ -z "$tok" ] && continue
  tok_lc="$(printf '%s' "$tok" | tr '[:upper:]' '[:lower:]')"
  if [ "$tok_lc" = "$label_lc" ]; then
    has_label=1
    break
  fi
done <<EOF
$(printf '%s' "$SDLC_PR_LABELS" | tr -d '[]' | tr ',' '\n')
EOF

if [ "$has_label" -eq 1 ]; then
  printf '%s\n' "$touched"
  echo "CONTROL-PLANE: EXEMPT (label $CONTROL_PLANE_LABEL applied by a human with write access)"
  exit 0
fi

printf '%s\n' "$touched"
echo "CONTROL-PLANE: BLOCKED — agent-authored change to protected paths. A human with write access applies the label '$CONTROL_PLANE_LABEL' after reviewing the diff above; the check re-runs on label."
exit 1
