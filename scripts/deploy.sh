#!/usr/bin/env bash
# Deploy guard (Q5: deploy only from CI via GitHub Environments; agents never run this
# for real). This script never executes a deploy command -- it prints the command it
# *would* run and exits 0, once every guard below is satisfied. It runs only from the
# `deploy` job in .github/workflows/deploy.yml; a human never runs it locally, and an
# agent must never be asked to run it "for real" -- the production-gate hook stays as
# defence in depth if that ever happens anyway.
#
# Usage: scripts/deploy.sh <environment>
set -u
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
ENV_FILE="$ROOT/.sdlc/environments.yaml"

usage() { echo "Usage: scripts/deploy.sh <environment>" >&2; }

if [ $# -lt 1 ] || [ -z "${1:-}" ]; then
  usage
  exit 2
fi
ENVIRONMENT="$1"

# Tiny indentation-based reader for .sdlc/environments.yaml (stdlib shell only, no
# YAML parser). Lists the environment names (two-space-indented keys directly under
# `environments:`) and reads the `approval:` value for one environment.
list_environments() {
  awk '
    /^environments:/ { in_env=1; next }
    in_env && /^[A-Za-z]/ { in_env=0 }
    in_env && /^  [A-Za-z0-9_-]+:[[:space:]]*$/ {
      name=$0; sub(/^  /, "", name); sub(/:.*/, "", name); print name
    }
  ' "$ENV_FILE"
}

approval_for() {
  # $1 = environment name
  awk -v env="$1" '
    /^environments:/ { in_env=1; next }
    in_env && /^[A-Za-z]/ { in_env=0 }
    in_env && /^  [A-Za-z0-9_-]+:[[:space:]]*$/ {
      name=$0; sub(/^  /, "", name); sub(/:.*/, "", name)
      cur=(name==env); next
    }
    cur && /^    approval:/ {
      val=$0; sub(/^    approval:[[:space:]]*/, "", val)
      sub(/[[:space:]]*#.*/, "", val)
      gsub(/[[:space:]]+$/, "", val)
      print val; exit
    }
  ' "$ENV_FILE"
}

if [ ! -f "$ENV_FILE" ]; then
  echo "deploy refused: environments file not found at $ENV_FILE" >&2
  exit 1
fi

VALID_ENVS="$(list_environments)"
env_known=0
for e in $VALID_ENVS; do
  [ "$e" = "$ENVIRONMENT" ] && env_known=1 && break
done
if [ "$env_known" != 1 ]; then
  echo "deploy refused: unknown environment '$ENVIRONMENT'. Valid environments:" >&2
  for e in $VALID_ENVS; do echo "  - $e" >&2; done
  exit 1
fi

# (b) deploy runs from CI only -- never on a developer or agent machine.
if [ -z "${CI:-}" ]; then
  echo "deploy refused: deploy runs from CI only (CI is not set). Do not run this locally." >&2
  exit 1
fi

SHA="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null)"

# (a) a human (or the pipeline acting on a human's approval) bound RELEASE_APPROVAL
# to exactly this commit.
if [ -z "${RELEASE_APPROVAL:-}" ]; then
  echo "deploy refused: RELEASE_APPROVAL is not set. It must equal the current commit ($SHA)." >&2
  exit 1
fi
if [ "$RELEASE_APPROVAL" != "$SHA" ]; then
  echo "deploy refused: RELEASE_APPROVAL ($RELEASE_APPROVAL) does not match HEAD ($SHA)." >&2
  exit 1
fi

# (d) production's approval is release-manager: assert the GitHub Environment's
# required-reviewer gate actually ran (it only runs inside GitHub Actions).
APPROVAL="$(approval_for "$ENVIRONMENT")"
if [ "$APPROVAL" = "release-manager" ] && [ "${GITHUB_ACTIONS:-}" != "true" ]; then
  echo "deploy refused: environment '$ENVIRONMENT' requires release-manager approval, which is enforced by the GitHub Environment's required reviewers. GITHUB_ACTIONS is not 'true', so that gate cannot be confirmed here." >&2
  exit 1
fi

# ADOPTERS: replace with your deploy command
COMMAND="echo replace-me-with-your-deploy-command --environment $ENVIRONMENT --sha $SHA"

echo "DEPLOY: would run $COMMAND for $ENVIRONMENT at $SHA"
exit 0
