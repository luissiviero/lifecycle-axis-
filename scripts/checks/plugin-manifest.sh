#!/usr/bin/env bash
# Self-registering check (picked up by scripts/verify.sh): .claude-plugin/plugin.json
# and marketplace.json match the components actually on disk. Runs
# check_plugin_manifest.py and passes its exit code through, then calls
# `claude plugin validate .` only when the CLI is on PATH -- skipping with a
# note otherwise, per docs/sdlc/spikes/plugin-packaging.md.
set -u
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
[ -f "$ROOT/.claude-plugin/plugin.json" ] || { echo "PLUGIN: no manifest (not a plugin repo); skipped"; exit 0; }
python3 "$ROOT/scripts/check_plugin_manifest.py" --root "$ROOT"
rc=$?

if command -v claude >/dev/null 2>&1; then
  ( cd "$ROOT" && claude plugin validate . )
  validate_rc=$?
  if [ "$validate_rc" -ne 0 ]; then
    rc=$validate_rc
  fi
else
  echo "plugin-manifest: 'claude' CLI not on PATH, skipping 'claude plugin validate .'"
fi

exit "$rc"
