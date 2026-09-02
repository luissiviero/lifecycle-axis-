#!/usr/bin/env bash
# Release gate: an agent may prepare a release but never cross into production without a named human.
. "$(dirname "$0")/_lib.sh"
[ -z "$CMD" ] && exit 0
DEPLOY_RE='(^|[;&| ])(kubectl[[:space:]]+(apply|rollout|delete)|helm[[:space:]]+(install|upgrade|rollback)|terraform[[:space:]]+(apply|destroy)|pulumi[[:space:]]+up|aws[[:space:]]+(cloudformation|lambda|ecs|s3[[:space:]]+sync)|gcloud[[:space:]]+(run|app|functions)[[:space:]]+deploy|az[[:space:]]+webapp|npm[[:space:]]+publish|twine[[:space:]]+upload|docker[[:space:]]+push|flyctl[[:space:]]+deploy|fly[[:space:]]+deploy|vercel[[:space:]]+(--prod|deploy)|serverless[[:space:]]+deploy|cap[[:space:]]+production|git[[:space:]]+push[^;&|]*[[:space:]](main|master|prod|production|release)([[:space:]]|$))'
DANGER_RE='(^|[;&| ])(rm[[:space:]]+-rf[[:space:]]+/|git[[:space:]]+push[[:space:]]+[^;&|]*--force|git[[:space:]]+reset[[:space:]]+--hard[[:space:]]+origin|DROP[[:space:]]+(TABLE|DATABASE))'
if printf '%s' "$CMD" | grep -Eiq "$DANGER_RE"; then
  block "destructive command. Not allowed from an agent session: $CMD"
fi
if printf '%s' "$CMD" | grep -Eiq "$DEPLOY_RE"; then
  SHA="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null)"
  AUTH="$ROOT/.sdlc/release-authorizations/$SHA"
  if [ -f "$AUTH" ] && grep -q '^approved-by:' "$AUTH"; then
    exit 0   # a human authorized exactly this commit (file written by the release manager)
  fi
  if [ -n "${RELEASE_APPROVAL:-}" ] && [ "$RELEASE_APPROVAL" = "$SHA" ]; then
    exit 0   # playbook convention: RELEASE_APPROVAL set by the release pipeline, bound to this commit
  fi
  [ -n "$SDLC_UNATTENDED" ] && block "deploy command in an unattended session with no release authorization for $SHA."
  ask "Release gate: '$CMD' looks like a deploy. No human authorization exists for HEAD ($SHA). Route to approval: the release manager writes .sdlc/release-authorizations/$SHA (approved-by: <name>) or the pipeline sets RELEASE_APPROVAL=$SHA. Approve here only if you are that person."
fi
exit 0
