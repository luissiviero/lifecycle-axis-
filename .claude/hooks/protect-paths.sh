#!/usr/bin/env bash
# Red line: agents never edit the control plane or secret material.
. "$(dirname "$0")/_lib.sh"
[ -z "$FILE" ] && exit 0
R="$(rel "$FILE")"
under_any "$R" "$PROTECTED_PATHS" && block "'$R' is a protected path ($PROTECTED_PATHS). Describe the change you want in the PR body; a human applies it."
case "$R" in
  .env|.env.*|*.pem|*.key|*.p12|*id_rsa*|*.keystore) block "'$R' looks like secret material. Never write secrets to the repo.";;
esac
exit 0
