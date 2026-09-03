#!/usr/bin/env bash
# Adopt the lifecycle-axis SDLC kit into another repo.
#
# Usage: adopt.sh <target-dir> [--force] [--dry-run] [--with-hooks] [--no-create]
#
#   --force       overwrite files that already exist in the target (default: skip them)
#   --dry-run     print what would be copied/skipped; write nothing
#   --with-hooks  also install .claude/hooks/ and .claude/settings.json (the deterministic
#                 gates), plus .gemini/settings.json and .gemini/agents/ so Gemini CLI runs
#                 the same scripts. The settings file is written from the kit's template
#                 docs/sdlc/templates/claude-settings.json, not from the kit's own
#                 .claude/settings.json, which adds the control-plane unlock the kit needs to
#                 maintain itself (knowledge/decisions/self-hooks-on.md). Without this
#                 flag only CI enforces the eight hard rules locally
#                 -- see knowledge/decisions/plugin-distribution.md.
#   --no-create   fail instead of creating <target-dir> when it does not exist
#
# Never overwrites an existing file unless --force. Prints "copy: <path>" for every file
# written and "skip (exists): <path>" for every file left alone (paths are relative to the
# target). Idempotent: a second run with the same flags prints only skips and changes nothing.
set -u

KIT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"

usage() {
  echo "usage: adopt.sh <target-dir> [--force] [--dry-run] [--with-hooks] [--no-create]" >&2
}

FORCE=false
DRY_RUN=false
WITH_HOOKS=false
NO_CREATE=false
TARGET_ARG=""

while [ $# -gt 0 ]; do
  case "$1" in
    --force) FORCE=true ;;
    --dry-run) DRY_RUN=true ;;
    --with-hooks) WITH_HOOKS=true ;;
    --no-create) NO_CREATE=true ;;
    --) shift; while [ $# -gt 0 ]; do
          if [ -z "$TARGET_ARG" ]; then TARGET_ARG="$1"; fi
          shift
        done
        break ;;
    -*) echo "adopt: unknown flag: $1" >&2; usage; exit 2 ;;
    *)
      if [ -z "$TARGET_ARG" ]; then
        TARGET_ARG="$1"
      else
        echo "adopt: unexpected extra argument: $1" >&2
        usage
        exit 2
      fi
      ;;
  esac
  shift
done

if [ -z "$TARGET_ARG" ]; then
  echo "adopt: missing <target-dir>" >&2
  usage
  exit 2
fi

case "$TARGET_ARG" in
  /*) TARGET="$TARGET_ARG" ;;
  *) TARGET="$PWD/$TARGET_ARG" ;;
esac

if [ ! -d "$TARGET" ]; then
  if [ "$NO_CREATE" = true ]; then
    echo "adopt: target directory does not exist: $TARGET (and --no-create was given)" >&2
    exit 1
  fi
  echo "create: $TARGET"
  if [ "$DRY_RUN" != true ]; then
    mkdir -p -- "$TARGET"
  fi
fi

if [ -d "$TARGET" ]; then
  if ! git -C "$TARGET" rev-parse --show-toplevel >/dev/null 2>&1; then
    echo "adopt: warning: $TARGET is not a git repository; continuing anyway" >&2
  fi
fi

# --- copy machinery -----------------------------------------------------
# copy_file <path relative to both KIT and TARGET> [<destination path relative to TARGET>]
# The optional second argument installs a kit file under a different name in the target
# (used for the settings template, which must not be live in the kit repo itself).
copy_file() {
  src_rel="$1"
  rel="${2:-$1}"
  src="$KIT/$src_rel"
  dst="$TARGET/$rel"
  [ -e "$src" ] || return 0
  if [ -e "$dst" ] && [ "$FORCE" != true ]; then
    echo "skip (exists): $rel"
    return 0
  fi
  echo "copy: $rel"
  if [ "$DRY_RUN" = true ]; then
    return 0
  fi
  mkdir -p -- "$(dirname -- "$dst")"
  cp -p -- "$src" "$dst"
}

# copy_tree <dir relative to both KIT and TARGET> -- every file, in sorted order
copy_tree() {
  rel_dir="$1"
  src_dir="$KIT/$rel_dir"
  [ -d "$src_dir" ] || return 0
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    rel="${f#"$KIT"/}"
    copy_file "$rel"
  done <<EOF_LIST
$(find "$src_dir" -type f | LC_ALL=C sort)
EOF_LIST
}

# copy_eval_cases -- evals/cases/*.yaml whose name starts with hook-, gate- or deploy-
# (the cases that exercise the hooks/scripts adopt.sh actually installs; the rest assume
# this repo's own content -- chain-*, plugin-*, index-*, okf-*, ci-*, review-*, skill-*).
copy_eval_cases() {
  src_dir="$KIT/evals/cases"
  [ -d "$src_dir" ] || return 0
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    base="$(basename -- "$f")"
    case "$base" in
      hook-*|gate-*|deploy-*) copy_file "evals/cases/$base" ;;
    esac
  done <<EOF_LIST
$(find "$src_dir" -maxdepth 1 -type f -name '*.yaml' | LC_ALL=C sort)
EOF_LIST
}

# --- what gets copied ----------------------------------------------------
CONFIG_ENV_PREEXISTED=false
[ -e "$TARGET/.sdlc/config.env" ] && CONFIG_ENV_PREEXISTED=true

copy_file ".sdlc/config.env"
copy_file ".sdlc/README.md"
copy_file ".sdlc/approvers.yaml"
copy_file ".sdlc/environments.yaml"

copy_tree ".claude/skills"
copy_tree ".claude/agents"

if [ "$WITH_HOOKS" = true ]; then
  copy_file "docs/sdlc/templates/claude-settings.json" ".claude/settings.json"
  copy_tree ".claude/hooks"
  # Gemini CLI runs the same scripts through its own wiring (knowledge/decisions/gemini-hooks.md).
  copy_file ".gemini/settings.json"
  copy_tree ".gemini/agents"
else
  echo "note: hooks not installed -- .claude/hooks/ and .claude/settings.json were skipped." \
       " Only CI enforces the hard rules locally without them; rerun with --with-hooks to install."
fi

copy_tree "docs/sdlc/templates"
copy_tree "docs/sdlc/rules"
copy_file "docs/sdlc/README.md"
copy_file "docs/sdlc/okf-pairing.md"

for s in verify.sh check_artifact_chain.py check_okf.py gen_index.py gen_context_files.py \
         log_ledger.py approvers.py run_evals.sh detect_bands.py sdlc_metrics.py \
         check_control_plane.sh check_workflow_permissions.py; do
  copy_file "scripts/$s"
done
copy_tree "scripts/checks"

copy_file "evals/README.md"
copy_eval_cases

copy_tree "work/_example"

for wf in sdlc-gate.yml agent-evals.yml pr-review.yml; do
  copy_file ".github/workflows/$wf"
done
copy_file ".github/CODEOWNERS"

copy_file "REVIEW.md"
copy_file "monitoring/bands.yaml"

copy_file "knowledge/index.md"
for d in decisions lessons runbooks metrics services; do
  copy_file "knowledge/$d/index.md"
done

# --- post-copy steps ------------------------------------------------------
if [ "$DRY_RUN" = true ]; then
  echo
  echo "(dry run: no files were changed)"
  exit 0
fi

if [ ! -e "$TARGET/.sdlc/active" ]; then
  echo "copy: .sdlc/active"
  mkdir -p -- "$TARGET/.sdlc"
  printf '_example\n' > "$TARGET/.sdlc/active"
else
  echo "skip (exists): .sdlc/active"
fi

if [ "$FORCE" = true ] || [ "$CONFIG_ENV_PREEXISTED" = false ]; then
  if [ -e "$TARGET/.sdlc/config.env" ]; then
    NEW_VERIFY_LINE="VERIFY_CMDS=\"echo 'TODO(adopter): set VERIFY_CMDS in .sdlc/config.env (e.g. npm test, pytest, make lint)'\""
    CONFIG_FILE="$TARGET/.sdlc/config.env"
    TMP_CONFIG="$(mktemp "${CONFIG_FILE}.XXXXXX")"
    replaced=false
    while IFS= read -r line || [ -n "$line" ]; do
      case "$line" in
        VERIFY_CMDS=*)
          printf '%s\n' "$NEW_VERIFY_LINE" >> "$TMP_CONFIG"
          replaced=true
          ;;
        *)
          printf '%s\n' "$line" >> "$TMP_CONFIG"
          ;;
      esac
    done < "$CONFIG_FILE"
    if [ "$replaced" != true ]; then
      printf '%s\n' "$NEW_VERIFY_LINE" >> "$TMP_CONFIG"
    fi
    mv -- "$TMP_CONFIG" "$CONFIG_FILE"
    echo "set VERIFY_CMDS to a TODO placeholder in $TARGET/.sdlc/config.env"
  fi
fi

echo
python3 "$KIT/scripts/gen_context_files.py" --root "$TARGET"
# Generate work/index.md and per-item indexes so the index-drift check is clean on day one.
python3 "$KIT/scripts/gen_index.py" --root "$TARGET" >/dev/null

cat <<STEPS

Next steps:
  1. Fill in VERIFY_CMDS in .sdlc/config.env (it currently holds a TODO placeholder).
  2. Edit CLAUDE.md: cut it to one page and start the "Lessons learned" section for this project.
  3. Protect the main branch: require the sdlc-gate check (and agent-evals) before merge.
     (Private repos need GitHub Pro or public visibility for this; otherwise the merge click is
     the gate -- knowledge/decisions/merge-click-is-the-gate.md.)
  4. Add an ANTHROPIC_API_KEY secret (or CLAUDE_CODE_OAUTH_TOKEN from `claude setup-token` on a Pro/Max
     plan) so prompt-based evals and PR review run in CI.
  5. Approve the example work item as yourself (the chain check refuses agent-authored approvals):
       python3 scripts/approve.py _example intent.md spec.md plan.md   # then commit as yourself
  6. Run the loop by hand once: /sdlc-intent -> /sdlc-spec -> /sdlc-plan -> implement -> /sdlc-review.
  7. Gemini CLI users: the hooks need bash and jq on PATH; Antigravity reads GEMINI.md but runs
     no local hooks here yet (docs/sdlc/phase-2-roadmap.md, Phase 1.5).
  8. Read docs/sdlc/README.md for the full picture.
STEPS

exit 0
