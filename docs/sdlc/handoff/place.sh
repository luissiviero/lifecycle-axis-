#!/usr/bin/env bash
# place.sh <slug> [<title>] : branch claude/<slug> from origin/main, add work/<slug>/{intent,spec,plan,log}.md, regen, commit, push.
set -eu
slug="$1"; title="${2:-open the work item (intent, spec, plan in review)}"
S=/tmp/claude-0/-home-user-lifecycle-axis-/2f1b2a2d-073a-5a84-a273-d7f99f7cbee7/scratchpad
R=/home/user/lifecycle-axis-
cd "$R"
[ -z "$(git status --porcelain)" ] || { echo "tree not clean"; exit 1; }
git fetch -q origin main
git checkout -q -b "claude/$slug" origin/main
mkdir -p "work/$slug"
cp "$S/batchA/$slug/intent.md" "$S/batchA/$slug/spec.md" "$S/batchA/$slug/plan.md" "work/$slug/"
ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; sha="$(git rev-parse --short HEAD)"
cat > "work/$slug/log.md" <<LOG
---
type: sdlc/log
id: $slug-log
title: Gate ledger for $slug
description: Chronological record of stage transitions and approvals for this work item.
timestamp: $ts
---
# Log: $slug

Format: \`- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>\` (append-only; parsed by scripts/log_ledger.py).

- $ts | intent.md | (none) -> in-review | claude | $sha | drafted from the approved 2026-09-04 implementation plan; batched with spec and plan for the owner to approve from their own shell
- $ts | spec.md | (none) -> in-review | claude | $sha | same
- $ts | plan.md | (none) -> in-review | claude | $sha | same
LOG
python3 scripts/gen_index.py >/dev/null
echo "== chain (expected red until the owner approves) =="
python3 scripts/check_artifact_chain.py --base origin/main --slug "$slug" || true
python3 scripts/check_okf.py | tail -1
git add "work/$slug" work/index.md
git commit -q -F - <<MSG
$slug: $title

Batch A of the 2026-09-04 implementation plan. Intent, spec and plan are
in-review together (owner chose batched approvals); the chain check on this
PR stays red until the owner approves all three from their own shell.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01DSYmeD7eng2GKQ3EbHQDzo
MSG
git log -1 --format='%h %s'
for i in 1 2 3; do git push -u origin "claude/$slug" 2>&1 | tail -1 && break || sleep $((2**i)); done
git checkout -q claude/lifecycle-axis-analysis-cgydca
echo "placed $slug"
