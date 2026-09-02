#!/usr/bin/env bash
# Red line: refuse to write content that looks like a credential.
. "$(dirname "$0")/_lib.sh"
CONTENT="$(printf '%s' "$INPUT" | jq -r '(.tool_input.content // "") + "\n" + (.tool_input.new_string // "")')"
[ -z "$CONTENT" ] && exit 0
PATTERNS='AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}|sk-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{35}|(password|passwd|secret|api[_-]?key)\s*[:=]\s*["'"'"'][^"'"'"']{8,}'
if printf '%s' "$CONTENT" | grep -Eiq "$PATTERNS"; then
  block "the content matches a credential pattern. Use an environment variable or the secret manager and reference it by name."
fi
exit 0
