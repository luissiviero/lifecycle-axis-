#!/usr/bin/env bash
# Release gate: an agent may prepare a release but never cross into production without a named human.
# RELEASE_APPROVAL and SDLC_UNATTENDED are taken from the hook process's environment only
# (captured in _lib.sh before .sdlc/config.env is sourced), so a value planted in the repo
# config cannot satisfy the gate (security review, finding 2).
. "$(dirname "$0")/_lib.sh"
[ -z "$CMD" ] && exit 0
# Gemini CLI has no "ask" decision for BeforeTool: the JSON ask() emits is ignored and the call
# would go through. Under Gemini (it exports GEMINI_SESSION_ID to every hook) the gate therefore
# fails closed, exactly as it does when SDLC_UNATTENDED is set (knowledge/decisions/gemini-hooks.md).
if [ -z "$SDLC_UNATTENDED" ] && [ -n "${GEMINI_SESSION_ID:-}" ]; then SDLC_UNATTENDED="gemini-cli"; fi

# A command starts at the beginning of the input, after a separator, or after any whitespace.
# The old boundary spelled that `(^|[;&| ])` with a literal space, so a tab-indented
# `<TAB>terraform apply` and a parenthesised `(git push origin main)` walked past every clause
# below (review of PR #11).
BOUND='(^|[;&|(){}!]|[[:space:]])'
# Protected destinations, shared by the branch names below and by push_reaches_protected().
PROTECTED_BRANCHES='main master prod production release'
# Tool-shaped deploys: the tool name plus a mutating subcommand is enough to recognise them.
# Each vendor clause names those subcommands explicitly. `aws cloudformation|lambda|ecs` and
# `az webapp` used to match the whole tool, so read-only calls -- `az webapp list`,
# `aws lambda list-functions` -- asked a human for a release authorization (review of PR #11).
# `git push` is deliberately absent: what it reaches depends on refspecs, flags and the current
# upstream, which no regex over the command text can see. push_reaches_protected() decides it.
DEPLOY_RE="$BOUND"'(kubectl[[:space:]]+(apply|rollout|delete)|helm[[:space:]]+(install|upgrade|rollback)|terraform[[:space:]]+(apply|destroy)|pulumi[[:space:]]+up|aws[[:space:]]+(cloudformation[[:space:]]+(deploy|create-stack|update-stack|delete-stack|create-change-set|execute-change-set)|lambda[[:space:]]+(create-function|delete-function|invoke|publish-version|update-alias|update-function-code|update-function-configuration)|ecs[[:space:]]+(create-service|update-service|delete-service|deploy|register-task-definition|run-task)|s3[[:space:]]+sync)|gcloud[[:space:]]+(run|app|functions)[[:space:]]+deploy|az[[:space:]]+webapp[[:space:]]+(up|deploy|deployment|create|delete|restart|start|stop|swap)|npm[[:space:]]+publish|twine[[:space:]]+upload|docker[[:space:]]+push|flyctl[[:space:]]+deploy|fly[[:space:]]+deploy|vercel[[:space:]]+(--prod|deploy)|serverless[[:space:]]+deploy|cap[[:space:]]+production)'
DANGER_RE="$BOUND"'(rm[[:space:]]+-rf[[:space:]]+/|git[[:space:]]+push[[:space:]]+[^;&|]*--force|git[[:space:]]+reset[[:space:]]+--hard[[:space:]]+origin|DROP[[:space:]]+(TABLE|DATABASE))'

# is_protected <ref> -- true when <ref> names one of PROTECTED_BRANCHES, case-insensitively.
is_protected() {
  local ref="${1,,}" b
  [ -n "$ref" ] || return 1
  for b in $PROTECTED_BRANCHES; do [ "$ref" = "$b" ] && return 0; done
  return 1
}

# push_reaches_protected <command> -- true when a `git push` in <command> can write a protected
# branch. The old regex clause matched only a bare `main`-shaped word after `git push`, so a
# refspec (`git push origin HEAD:main`, `refs/heads/main`, the remote delete `:main`), a
# whole-repo push (`--all`, `--mirror`) and a bare `git push` whose upstream is main all went
# through untouched (review of PR #11). Splitting the command and reading the arguments is the
# only way to see those; over-inclusive on purpose, because this hook asks rather than decides.
push_reaches_protected() {
  local cmd="${1:0:16384}" seg tok ref branch upstream saw_push refs noglob
  local -a toks
  case "${cmd,,}" in *push*) ;; *) return 1;; esac
  while IFS= read -r seg; do
    case "${seg,,}" in *git*push*) ;; *) continue;; esac
    noglob=0
    case "$-" in *f*) noglob=1;; *) set -f;; esac
    # shellcheck disable=SC2206
    toks=( $seg )
    [ "$noglob" = 1 ] || set +f
    saw_push=0; refs=0
    for tok in "${toks[@]}"; do
      tok="${tok//\"/}"; tok="${tok//\'/}"
      if [ "$saw_push" = 0 ]; then
        [ "${tok,,}" = push ] && saw_push=1
        continue
      fi
      case "${tok,,}" in
        --all|--mirror) return 0;;   # pushes every local branch, main included
        -*) continue;;
      esac
      refs=$((refs+1))
      [ "$refs" = 1 ] && continue    # the remote
      ref="${tok##*:}"               # HEAD:main, :main (a remote delete), main:main
      ref="${ref#+}"                 # +main, a forced refspec
      ref="${ref#refs/heads/}"
      is_protected "$ref" && return 0
    done
    [ "$saw_push" = 1 ] || continue
    [ "$refs" -gt 1 ] && continue    # refspecs were given and none of them is protected
    # No refspec: git pushes the current branch, or whatever its upstream names. A HEAD that
    # cannot be resolved is exactly the push worth asking about, so it counts as protected.
    branch="$(git -C "$ROOT" symbolic-ref --quiet --short HEAD 2>/dev/null)"
    [ -z "$branch" ] && return 0
    is_protected "$branch" && return 0
    upstream="$(git -C "$ROOT" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null)"
    is_protected "${upstream#*/}" && return 0
  done <<EOF
$(printf '%s' "$cmd" | tr ';&|()' '\n\n\n\n\n')
EOF
  return 1
}

if printf '%s' "$CMD" | grep -Eiq "$DANGER_RE"; then
  block "destructive command. Not allowed from an agent session: $CMD"
fi
if printf '%s' "$CMD" | grep -Eiq "$DEPLOY_RE" || push_reaches_protected "$CMD"; then
  SHA="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null)"
  AUTH="$ROOT/.sdlc/release-authorizations/$SHA"
  if [ -f "$AUTH" ] && grep -q '^approved-by:' "$AUTH"; then
    exit 0   # a human authorized exactly this commit (file written by the release manager; the path is protected from agents)
  fi
  if [ -n "${RELEASE_APPROVAL:-}" ] && [ "$RELEASE_APPROVAL" = "$SHA" ]; then
    exit 0   # playbook convention: RELEASE_APPROVAL set by the release pipeline's environment, bound to this commit
  fi
  [ -n "$SDLC_UNATTENDED" ] && block "deploy command in an unattended session with no release authorization for $SHA."
  ask "Release gate: '$CMD' looks like a deploy. No human authorization exists for HEAD ($SHA). Route to approval: the release manager writes .sdlc/release-authorizations/$SHA (approved-by: <name>) or the pipeline sets RELEASE_APPROVAL=$SHA. Approve here only if you are that person."
fi
exit 0
