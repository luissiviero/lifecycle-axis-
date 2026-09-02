#!/usr/bin/env bash
# Build-time guardrail: run the formatter on the file just edited so drift never accumulates. Fast, scoped to one file.
. "$(dirname "$0")/_lib.sh"
[ -z "$FILE" ] || [ -z "${FORMAT_CMD:-}" ] && exit 0
[ -f "$FILE" ] || exit 0
bash -c "$FORMAT_CMD \"\$1\"" _ "$FILE" >/dev/null 2>&1 || printf 'formatter failed on %s (non-blocking)\n' "$(rel "$FILE")" >&2
exit 0
