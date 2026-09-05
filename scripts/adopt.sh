#!/usr/bin/env bash
# Adopt the lifecycle-axis SDLC kit into another repo.
#
# Usage: adopt.sh <target-dir> [--force] [--dry-run] [--with-hooks] [--no-create] [--help]
#
#   --force       overwrite files that already exist in the target (default: skip them). The
#                 adopter's own VERIFY_CMDS, PLAN_REQUIRED_PATHS and approver handle are carried
#                 across the overwrite when they differ from the kit's values.
#   --dry-run     print what would be copied/skipped; write nothing
#   --with-hooks  also install .claude/hooks/ and .claude/settings.json (the deterministic
#                 gates), plus .gemini/settings.json and .gemini/agents/ so Gemini CLI runs
#                 the same scripts. The settings file is written from the kit's template
#                 docs/sdlc/templates/claude-settings.json, not from the kit's own
#                 .claude/settings.json, which adds the control-plane unlock the kit needs to
#                 maintain itself (knowledge/decisions/self-hooks-on.md). An existing
#                 .claude/settings.json is merged (the kit's hook entries and missing
#                 permission keys added, everything else kept) and reported. Without this
#                 flag only CI enforces the eight hard rules locally
#                 -- see knowledge/decisions/plugin-distribution.md.
#   --no-create   fail instead of creating <target-dir> when it does not exist
#   -h, --help    print this help and exit
#
# Never overwrites an existing file unless --force. Prints "copy: <path>" for every file
# written, "skip (exists): <path>" for every file left alone and "skip (exists, differs from
# kit): <path>" when the file left alone is not the kit's (paths are relative to the target).
# Idempotent: a second run with the same flags prints only skips and changes nothing.
#
# After the copies: the kit owner's handle becomes <your-github-handle> in .sdlc/approvers.yaml
# and .github/CODEOWNERS; work/_example is set to in-review with a plan listing exactly the
# paths written here; CLAUDE.md is seeded with project sections above the generated block;
# knowledge/*/index.md are written empty. See docs/sdlc/github-setup.md for the first hour.
set -u

KIT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
PLACEHOLDER_HANDLE="<your-github-handle>"
KIT_HANDLE="luissiviero"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

usage() {
  cat <<'USAGE'
usage: adopt.sh <target-dir> [--force] [--dry-run] [--with-hooks] [--no-create] [--help]
  --force       overwrite files that already exist in the target (keeps the adopter's
                VERIFY_CMDS, PLAN_REQUIRED_PATHS and approver handle)
  --dry-run     print what would be copied/skipped; write nothing
  --with-hooks  also install .claude/hooks/, .claude/settings.json (merged if present),
                .gemini/settings.json and .gemini/agents/
  --no-create   fail instead of creating <target-dir> when it does not exist
  -h, --help    print this help and exit
USAGE
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
    -h|--help) usage; exit 0 ;;
    --) shift; while [ $# -gt 0 ]; do
          if [ -z "$TARGET_ARG" ]; then TARGET_ARG="$1"; fi
          shift
        done
        break ;;
    -*) echo "adopt: unknown flag: $1" >&2; usage >&2; exit 2 ;;
    *)
      if [ -z "$TARGET_ARG" ]; then
        TARGET_ARG="$1"
      else
        echo "adopt: unexpected extra argument: $1" >&2
        usage >&2
        exit 2
      fi
      ;;
  esac
  shift
done

if [ -z "$TARGET_ARG" ]; then
  echo "adopt: missing <target-dir>" >&2
  usage >&2
  exit 2
fi

# `C:\Users\...\tmpX` is absolute, but it does not start with `/`. Fold backslashes and treat a
# drive letter as absolute, the same way .claude/hooks/_lib.sh does; without this the target was
# taken as relative and became `$PWD/C:\Users\...`, i.e. a directory named `C:` inside the kit
# (roadmap item 19c).
TARGET_ARG="${TARGET_ARG//\\//}"
case "$TARGET_ARG" in
  /*|[A-Za-z]:/*) TARGET="$TARGET_ARG" ;;
  *) TARGET="$PWD/$TARGET_ARG" ;;
esac

# _abs <path> -- canonical, and one spelling on Windows: `git rev-parse` hands back `C:/kit`
# while `$PWD` is `/c/kit`, so realpath alone leaves the two incomparable (cygpath exists only
# on MSYS/Cygwin; elsewhere this is a plain realpath, as in .claude/hooks/_lib.sh).
_abs() {
  _p="$(realpath -m -- "$1" 2>/dev/null || printf '%s' "$1")"
  case "$_p" in
    [A-Za-z]:/*|/[a-z]/*) cygpath -m -- "$_p" 2>/dev/null || printf '%s' "$_p" ;;
    *) printf '%s' "$_p" ;;
  esac
}
# A target inside the kit is always a mistake, and an expensive one: copy_tree walks the kit with
# `find`, so each copy discovers what earlier copies wrote. That is what turned the drive-letter
# bug above from a junk directory into a test suite that never finished. Refuse it outright.
_kit_abs="$(_abs "$KIT")"
_tgt_abs="$(_abs "$TARGET")"
case "$_tgt_abs" in
  "$_kit_abs"|"$_kit_abs"/*)
    echo "adopt: refusing to adopt into the kit itself: $TARGET" >&2
    exit 2 ;;
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

# --- --force: remember the adopter's own values before anything is overwritten -------------
# The three values the first-hour report found reset by an upgrade. Each is restored after the
# copy when it differs from the kit's line and from the placeholder this script would write.
KEEP_VERIFY=""; KEEP_PLAN=""; KEEP_HANDLE=""
if [ "$FORCE" = true ]; then
  if [ -e "$TARGET/.sdlc/config.env" ]; then
    KEEP_VERIFY="$(grep -m1 '^VERIFY_CMDS=' "$TARGET/.sdlc/config.env" || true)"
    KEEP_PLAN="$(grep -m1 '^PLAN_REQUIRED_PATHS=' "$TARGET/.sdlc/config.env" || true)"
  fi
  if [ -e "$TARGET/.sdlc/approvers.yaml" ]; then
    KEEP_HANDLE="$(sed -n 's/^[[:space:]]*product-owner:[[:space:]]*\[[[:space:]]*\([^],[:space:]]*\).*/\1/p' "$TARGET/.sdlc/approvers.yaml" | head -1)"
  fi
fi

# --- copy machinery -----------------------------------------------------
# COPIED lists every target-relative path this run wrote (one per line, leading newline); the
# post-copy rewrites are keyed on it so a rerun changes nothing, and work/_example's plan is
# generated from it. REWRITTEN names the files this script edits after copying: they always
# differ from the kit on a rerun, so they are not reported as drift.
COPIED=$'\n'
REWRITTEN=" .sdlc/config.env .sdlc/approvers.yaml .github/CODEOWNERS docs/sdlc/rules/00-chain.md work/_example/intent.md work/_example/spec.md work/_example/plan.md work/_example/log.md "
record_copy() { COPIED="${COPIED}${1}"$'\n'; }
was_copied() { case "$COPIED" in *$'\n'"$1"$'\n'*) return 0 ;; *) return 1 ;; esac; }

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
    case "$REWRITTEN" in
      *" $rel "*) echo "skip (exists): $rel" ;;
      *) if cmp -s -- "$src" "$dst"; then echo "skip (exists): $rel"; else echo "skip (exists, differs from kit): $rel"; fi ;;
    esac
    return 0
  fi
  echo "copy: $rel"
  record_copy "$rel"
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

# merge_settings <template> <existing> -- add the kit's hook entries (keyed on their command)
# and missing permission keys to an adopter's .claude/settings.json; keep everything else.
# Never silent: prints "merged: ..." with a count, or a WARNING on both streams when the file
# is not JSON (then nothing is written and the hooks are not wired).
merge_settings() {
  if [ "$DRY_RUN" = true ]; then
    echo "merge: .claude/settings.json"
    return 0
  fi
  python3 - "$1" "$2" <<'PY'
import json, sys
tpl_path, dst_path = sys.argv[1], sys.argv[2]
with open(tpl_path, encoding="utf-8") as f:
    tpl = json.load(f)
try:
    with open(dst_path, encoding="utf-8") as f:
        dst = json.load(f)
    if not isinstance(dst, dict):
        raise ValueError("top level is not a JSON object")
    if "hooks" in dst and not isinstance(dst["hooks"], dict):
        raise ValueError("'hooks' is not a JSON object")
except ValueError as e:
    msg = ("WARNING: .claude/settings.json could not be parsed; hooks NOT installed "
           "(fix the JSON and rerun adopt.sh --with-hooks): %s" % e)
    print(msg)
    print(msg, file=sys.stderr)
    sys.exit(0)
added, changed = 0, False
hooks = dst.get("hooks") or {}
for event, groups in tpl.get("hooks", {}).items():
    mine = hooks.setdefault(event, [])
    for group in groups:
        matcher = group.get("matcher")
        target = next((g for g in mine if isinstance(g, dict) and g.get("matcher") == matcher), None)
        if target is None:
            mine.append(json.loads(json.dumps(group)))
            added += len(group.get("hooks", []))
            changed = True
            continue
        entries = target.setdefault("hooks", [])
        have = {h.get("command") for h in entries if isinstance(h, dict)}
        for h in group.get("hooks", []):
            if h.get("command") not in have:
                entries.append(dict(h))
                have.add(h.get("command"))
                added += 1
                changed = True
if changed:
    dst["hooks"] = hooks
perms = dst.get("permissions")
if not isinstance(perms, dict):
    perms = {}
for key, value in tpl.get("permissions", {}).items():
    if key not in perms:
        perms[key] = list(value)
        dst["permissions"] = perms
        changed = True
if changed:
    with open(dst_path, "w", encoding="utf-8") as f:
        json.dump(dst, f, indent=2)
        f.write("\n")
print("merged: .claude/settings.json (%d hook entries added)" % added)
PY
}

# write_index <rel> <title> <description> <body> -- a minimal knowledge index for the target
# (its own bundle starts empty; the kit's indexes link to files that are not copied).
write_index() {
  dst="$TARGET/$1"
  if [ -e "$dst" ] && [ "$FORCE" != true ]; then
    echo "skip (exists): $1"
    return 0
  fi
  echo "copy: $1"
  record_copy "$1"
  if [ "$DRY_RUN" = true ]; then
    return 0
  fi
  mkdir -p -- "$(dirname -- "$dst")"
  printf -- '---\ntype: index\ntitle: %s\ndescription: %s\ntags: [okf, index]\ntimestamp: %s\n---\n\n# %s\n\n%s\n' \
    "$2" "$3" "$TS" "$2" "$4" > "$dst"
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
  if [ -e "$TARGET/.claude/settings.json" ] && [ "$FORCE" != true ]; then
    merge_settings "$KIT/docs/sdlc/templates/claude-settings.json" "$TARGET/.claude/settings.json"
  else
    copy_file "docs/sdlc/templates/claude-settings.json" ".claude/settings.json"
  fi
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
copy_file "docs/sdlc/github-setup.md"

for s in verify.sh check_artifact_chain.py check_okf.py gen_index.py gen_context_files.py \
         log_ledger.py approvers.py approve.py hooktest.py run_evals.sh detect_bands.py \
         github_metrics.py bands_config.py sdlc_metrics.py deploy.sh \
         check_control_plane.sh check_workflow_permissions.py; do
  copy_file "scripts/$s"
done
copy_tree "scripts/checks"

copy_file "evals/README.md"
copy_eval_cases

copy_tree "work/_example"

for wf in sdlc-gate.yml agent-evals.yml pr-review.yml deploy.yml bands.yml; do
  copy_file ".github/workflows/$wf"
done
copy_file ".github/CODEOWNERS"
copy_file ".gitignore"

copy_file "REVIEW.md"
copy_file "monitoring/bands.yaml"

# The kit's docs/sdlc/index.md links to spikes and roadmap pages that are not copied; the target
# gets a minimal one so its OKF check (every documented directory has an index) is clean.
write_index "docs/sdlc/index.md" "SDLC kit docs" \
  "Entry point to the SDLC kit's documentation installed by scripts/adopt.sh." \
  "- [README](README.md) — the six stages, how the kit implements each play, and the enforcement matrix.
- [GitHub-side setup](github-setup.md) — the first hour after install and the settings the gates rely on.
- [OKF pairing](okf-pairing.md) — how the artifact chain becomes a model-neutral knowledge bundle.
- [templates/](templates/) — intent, spec, plan, incident and log templates.
- [rules/](rules/) — the rule fragments rendered into CLAUDE.md, GEMINI.md and AGENTS.md."

write_index "knowledge/index.md" "Knowledge bundle" \
  "Entry point to this repository's model-neutral OKF knowledge bundle; CLAUDE.md and GEMINI.md link here instead of restating." \
  "This directory is an [Open Knowledge Format](../docs/sdlc/okf-pairing.md) bundle: one concept per file, front matter
with a required \`type\`, path as identity, Markdown links as the graph. Conformance is checked by
\`scripts/check_okf.py\`. Subdirectories: [decisions](decisions/index.md), [lessons](lessons/index.md),
[runbooks](runbooks/index.md), [metrics](metrics/index.md), [services](services/index.md). Each starts empty;
add a file the first time a decision, lesson, runbook, metric or service needs a home more than one work item
will reference, and list it in that directory's index."
write_index "knowledge/decisions/index.md" "Decisions" \
  "Architecture and process decisions, one file per decision with alternatives and consequences. Empty until the first decision lands." \
  "One file per decision (\`type: decision\`): the alternatives considered, what was decided, and the consequences.
Empty for now; list each decision here as it lands."
write_index "knowledge/lessons/index.md" "Lessons" \
  "Post-mortem lessons, one per incident, linked to the incident record that produced them. Empty until the first incident closes." \
  "Empty for now. \`/sdlc-incident\` writes one \`type: lesson\` file here per closed incident, named after the
\`work/<slug>/incident.md\` that produced it; if the lesson changes how the agent should behave, the same PR
also updates \`CLAUDE.md\` or a skill."
write_index "knowledge/runbooks/index.md" "Runbooks" \
  "Pre-approved operational procedures an agent may propose but never run unattended. Empty until the first runbook is written." \
  "One file per procedure (\`type: runbook\`): preconditions, steps, verification, and who is authorized to run it.
An agent may open the link or PR a runbook proposes; it never executes the procedure itself. Empty for now."
write_index "knowledge/metrics/index.md" "Metrics" \
  "One definition per metric named in monitoring/bands.yaml. Empty until the first metric is defined." \
  "One file per metric (\`type: metric-definition\`) named in \`monitoring/bands.yaml\`: definition in prose, the exact
source command, baseline window, what each Western Electric tier does, and known caveats. Empty for now."
write_index "knowledge/services/index.md" "Services" \
  "One concept file per service or table once this project spans more than one service. Empty for now." \
  "Add a file here the first time a second service, external dependency, or shared table needs a description that
more than one work item will reference. Empty for now."

# --- post-copy steps ------------------------------------------------------
if [ "$DRY_RUN" = true ]; then
  echo
  echo "(dry run: no files were changed)"
  exit 0
fi

if [ ! -e "$TARGET/.sdlc/active" ]; then
  echo "copy: .sdlc/active"
  record_copy ".sdlc/active"
  mkdir -p -- "$TARGET/.sdlc"
  printf '_example\n' > "$TARGET/.sdlc/active"
else
  echo "skip (exists): .sdlc/active"
fi

if [ "$FORCE" = true ] || [ "$CONFIG_ENV_PREEXISTED" = false ]; then
  if [ -e "$TARGET/.sdlc/config.env" ]; then
    # Two keys are the kit's own values, not the adopter's: VERIFY_CMDS runs this repo's suite,
    # and PLAN_REQUIRED_PATHS names this repo's product code (scripts/) rather than the usual
    # source directories of an application. Each is rewritten to an adopter default so a change
    # to the kit's own governance never leaks into a target. The placeholder verify command
    # fails on purpose (`&& false`, never `;` -- verify.sh splits VERIFY_CMDS on `;`), so
    # scripts/verify.sh is red until the adopter sets a real command.
    NEW_VERIFY_LINE="VERIFY_CMDS=\"echo 'TODO(adopter): set VERIFY_CMDS in .sdlc/config.env (e.g. npm test, pytest, make lint)' && false\""
    NEW_PLAN_PATHS_LINE="PLAN_REQUIRED_PATHS=\"src lib app services packages\""
    KIT_VERIFY_LINE="$(grep -m1 '^VERIFY_CMDS=' "$KIT/.sdlc/config.env" || true)"
    KIT_PLAN_PATHS_LINE="$(grep -m1 '^PLAN_REQUIRED_PATHS=' "$KIT/.sdlc/config.env" || true)"
    VERIFY_LINE_OUT="$NEW_VERIFY_LINE"
    PLAN_LINE_OUT="$NEW_PLAN_PATHS_LINE"
    if [ -n "$KEEP_VERIFY" ] && [ "$KEEP_VERIFY" != "$KIT_VERIFY_LINE" ] && [ "$KEEP_VERIFY" != "$NEW_VERIFY_LINE" ]; then
      VERIFY_LINE_OUT="$KEEP_VERIFY"
      echo "preserved: VERIFY_CMDS (the adopter's value, not the placeholder)"
    fi
    if [ -n "$KEEP_PLAN" ] && [ "$KEEP_PLAN" != "$KIT_PLAN_PATHS_LINE" ] && [ "$KEEP_PLAN" != "$NEW_PLAN_PATHS_LINE" ]; then
      PLAN_LINE_OUT="$KEEP_PLAN"
      echo "preserved: PLAN_REQUIRED_PATHS (the adopter's value, not the default)"
    fi
    CONFIG_FILE="$TARGET/.sdlc/config.env"
    TMP_CONFIG="$(mktemp "${CONFIG_FILE}.XXXXXX")"
    replaced=false
    replaced_plan=false
    while IFS= read -r line || [ -n "$line" ]; do
      case "$line" in
        VERIFY_CMDS=*)
          printf '%s\n' "$VERIFY_LINE_OUT" >> "$TMP_CONFIG"
          replaced=true
          ;;
        PLAN_REQUIRED_PATHS=*)
          printf '%s\n' "$PLAN_LINE_OUT" >> "$TMP_CONFIG"
          replaced_plan=true
          ;;
        *)
          printf '%s\n' "$line" >> "$TMP_CONFIG"
          ;;
      esac
    done < "$CONFIG_FILE"
    if [ "$replaced" != true ]; then
      printf '%s\n' "$VERIFY_LINE_OUT" >> "$TMP_CONFIG"
    fi
    if [ "$replaced_plan" != true ]; then
      printf '%s\n' "$PLAN_LINE_OUT" >> "$TMP_CONFIG"
    fi
    mv -- "$TMP_CONFIG" "$CONFIG_FILE"
    if [ "$VERIFY_LINE_OUT" = "$NEW_VERIFY_LINE" ]; then
      echo "set VERIFY_CMDS to a TODO placeholder in $TARGET/.sdlc/config.env (scripts/verify.sh is red until you set it)"
    fi
    if [ "$PLAN_LINE_OUT" = "$NEW_PLAN_PATHS_LINE" ]; then
      echo "set PLAN_REQUIRED_PATHS to the adopter default (src lib app services packages) in $TARGET/.sdlc/config.env"
    fi
  fi
fi

# Identity: the kit owner's handle never ships as an adopter's approver or code owner. Only a
# file copied in this run is rewritten, so an adopter's edited file is never touched.
HANDLE_OUT="$PLACEHOLDER_HANDLE"
if [ -n "$KEEP_HANDLE" ] && [ "$KEEP_HANDLE" != "$PLACEHOLDER_HANDLE" ] && [ "$KEEP_HANDLE" != "$KIT_HANDLE" ]; then
  HANDLE_OUT="$KEEP_HANDLE"
  echo "preserved: approver handle ($HANDLE_OUT)"
fi
rewrite_handle() {
  was_copied "$1" || return 0
  f="$TARGET/$1"
  tmp="$(mktemp "$f.XXXXXX")"
  sed "s/$KIT_HANDLE/$HANDLE_OUT/g" "$f" > "$tmp" && mv -- "$tmp" "$f"
  echo "set the approver handle to $HANDLE_OUT in $1"
}
rewrite_handle ".sdlc/approvers.yaml"
rewrite_handle ".github/CODEOWNERS"

# The generated context block opens with the chain rule; its first paragraph must describe the
# adopter's repository, not this starter kit.
if was_copied "docs/sdlc/rules/00-chain.md"; then
  python3 - "$TARGET/docs/sdlc/rules/00-chain.md" <<'PY'
import sys
path = sys.argv[1]
text = open(path, encoding="utf-8").read()
old = ("This repo is a starter kit for the AI-native SDLC: six non-linear stages\n"
       "(Plan → Design → Build → Test → Deploy → Maintain) connected by committed\n"
       "Markdown artifacts. Read `docs/sdlc/README.md` once; then follow the rules below.")
new = ("This repo follows the AI-native SDLC: six non-linear stages\n"
       "(Plan → Design → Build → Test → Deploy → Maintain) connected by committed\n"
       "Markdown artifacts. The sections above the generated block are this project's own;\n"
       "`docs/sdlc/README.md` explains the stages; the rules below are generated from `docs/sdlc/rules/`.")
if old in text:
    open(path, "w", encoding="utf-8").write(text.replace(old, new))
PY
fi

# work/_example in the target is in review, with a plan that lists exactly what this run wrote,
# so the plan gate is closed until the adopter approves it as themselves and the install commit
# is covered once they do (docs/sdlc/github-setup.md, "The first hour").
if was_copied "work/_example/intent.md"; then
  COPIED="$COPIED" TS="$TS" python3 - "$TARGET" <<'PY'
import os, sys
target = sys.argv[1]
ts = os.environ["TS"]
paths = {p for p in os.environ["COPIED"].split("\n") if p}
paths.update([".sdlc/active", "CLAUDE.md", "GEMINI.md", "AGENTS.md", "work/index.md", "work/_example/index.md"])
example = os.path.join(target, "work", "_example")

def in_review(name):
    path = os.path.join(example, name)
    lines = open(path, encoding="utf-8").read().split("\n")
    out, in_fm = [], False
    for i, line in enumerate(lines):
        if i == 0 and line == "---":
            in_fm = True
        elif in_fm and line == "---":
            in_fm = False
        elif in_fm:
            key = line.split(":", 1)[0]
            if key == "status":
                line = "status: in-review"
            elif key in ("approved-by", "approved-on"):
                line = key + ":"
        out.append(line)
    open(path, "w", encoding="utf-8").write("\n".join(out))

for name in ("intent.md", "spec.md", "plan.md"):
    in_review(name)

plan = os.path.join(example, "plan.md")
lines = open(plan, encoding="utf-8").read().split("\n")
out, skipping = [], False
for line in lines:
    if line.startswith("## Files that change"):
        out.append(line)
        out.append("Every path scripts/adopt.sh wrote when this kit was installed (no globs; CI fails the install PR if the diff touches anything else).")
        out.extend("- " + p for p in sorted(paths))
        out.append("")
        skipping = True
        continue
    if skipping:
        if line.startswith("## "):
            skipping = False
        else:
            continue
    out.append(line)
open(plan, "w", encoding="utf-8").write("\n".join(out))

note = "installed by scripts/adopt.sh; approve as yourself from your own shell (docs/sdlc/github-setup.md)"
log = [
    "---", "type: sdlc/log", "id: _example-log", "title: Gate ledger for _example",
    "description: Chronological record of stage transitions and approvals for this work item.",
    "timestamp: " + ts, "---", "# Log: _example", "",
    "Format: `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>` (append-only; parsed by scripts/log_ledger.py).",
    "",
]
log += ["- %s | %s | (none) -> in-review | adopt.sh | 0000000 | %s" % (ts, name, note) for name in ("intent.md", "spec.md", "plan.md")]
open(os.path.join(example, "log.md"), "w", encoding="utf-8").write("\n".join(log) + "\n")
PY
  echo "set work/_example to in-review; its plan lists the paths written by this run"
fi

# A fresh CLAUDE.md opens with the sections the adopter owns; gen_context_files.py appends the
# generated block after them and preserves them on every later render.
if [ ! -e "$TARGET/CLAUDE.md" ]; then
  echo "seed: CLAUDE.md (project sections above the generated block)"
  cat > "$TARGET/CLAUDE.md" <<EOF
# $(basename -- "$TARGET")

## Commands
- TODO(adopter): the verify command and its healthy last line, the test command, the run command

## Architecture
- TODO(adopter): ten lines on how this repo is put together

## Lessons learned (append; one line each; delete when a hook makes it impossible)
-

EOF
fi

echo
python3 "$KIT/scripts/gen_context_files.py" --root "$TARGET"
# Generate work/index.md and per-item indexes so the index-drift check is clean on day one.
python3 "$KIT/scripts/gen_index.py" --root "$TARGET" >/dev/null

# Quoted delimiter: the body is literal help text, and it mentions `claude setup-token` in
# backticks. Unquoted, bash read that as a command substitution and actually ran it -- an
# interactive OAuth flow that never returns, so every adopt.sh run hung on any machine with
# Claude Code installed. CI never saw it because `claude` is not on PATH there.
cat <<'STEPS'

Next steps (docs/sdlc/github-setup.md has the same list with the GitHub settings):
  0. Replace <your-github-handle> with your GitHub login in .sdlc/approvers.yaml and .github/CODEOWNERS.
  1. Fill in VERIFY_CMDS in .sdlc/config.env (it currently holds a TODO placeholder that fails on purpose).
  2. Fill the "## Commands" and "## Architecture" sections at the top of CLAUDE.md (one page; the
     generated block below them is rendered from docs/sdlc/rules/ and is not edited by hand).
  3. Approve the example work item as yourself, from your own shell (the chain check refuses
     agent-authored approvals; the target must be a git repository):
       python3 scripts/approve.py _example intent.md spec.md plan.md --as <your-github-handle>
     then commit as yourself and open the install pull request.
  4. Protect the main branch: require the sdlc-gate check (and agent-evals) before merge; create the
     control-plane-approved label. (Private repos need GitHub Pro or public visibility for protection;
     otherwise the merge click is the gate -- knowledge/decisions/merge-click-is-the-gate.md.)
     sdlc-gate runs only on pull requests: a direct push to main sees no gate.
  5. Add an ANTHROPIC_API_KEY secret (or CLAUDE_CODE_OAUTH_TOKEN from `claude setup-token` on a Pro/Max
     plan) so prompt-based evals and PR review run in CI.
  6. Run the loop by hand once: /sdlc-intent -> /sdlc-spec -> /sdlc-plan -> implement -> /sdlc-review.
  7. Gemini CLI users: the hooks need bash and jq on PATH; Antigravity reads GEMINI.md but runs
     no local hooks here yet (docs/sdlc/phase-2-roadmap.md, Phase 1.5).
  8. Read docs/sdlc/README.md for the full picture.
STEPS

exit 0
