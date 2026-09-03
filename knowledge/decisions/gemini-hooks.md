---
type: decision
title: Gemini CLI runs the same hook scripts through .gemini/settings.json
description: The deterministic gates are wired for Gemini CLI as BeforeTool/AfterAgent hooks that call the scripts in .claude/hooks/ unchanged; the release gate fails closed under Gemini; the hooks now handle Windows drive-letter paths and refuse to run blind without jq.
tags: [gemini, hooks, windows, control-plane, sdlc]
timestamp: 2026-09-02T23:30:00Z
---

# Gemini CLI runs the same hook scripts through `.gemini/settings.json`

Closes the Phase 1.5 roadmap item and the UNVERIFIED notes in
[`docs/sdlc/spikes/gemini-parity.md`](../../docs/sdlc/spikes/gemini-parity.md).

## Context

The spike established that Gemini CLI's `BeforeTool` hook has the same stdin/stdout/exit-2
contract as Claude Code's `PreToolUse`, and that Gemini exports `CLAUDE_PROJECT_DIR` "for
compatibility". What it could not verify offline was checked against the installed CLI
(v0.58.0, `@google/gemini-cli` bundle):

- `write_file` and `replace` take `file_path`; `run_shell_command` takes `command`. The hooks
  already read exactly those keys, so no adapter is needed.
- Hook commands run through `bash -c` on Linux and macOS and through
  `powershell.exe -NoProfile -Command` on Windows. `$GEMINI_PROJECT_DIR` and
  `$CLAUDE_PROJECT_DIR` are substituted textually with a shell-escaped value before the
  command runs, and are also set in the hook's environment.
- The output model accepts `decision: "block" | "deny"` and treats Claude's
  `hookSpecificOutput.permissionDecision: "ask"` as no decision at all.
- Project subagents load from `.gemini/agents/*.md` with a strict front-matter schema
  (`name`, `description`, `tools`, `model`, `temperature`, `max_turns`, `timeout_mins`).
- Sign-in with a personal Google account is refused by this CLI version ("migrate to the
  Antigravity suite"); an individual authenticates with `GEMINI_API_KEY` from AI Studio,
  set in the user's environment, never in the repo.

Smoke-testing the wiring on the owner's Windows PC found two defects in the hooks that
Gemini did not cause but would have inherited:

1. **Drive-letter paths were treated as relative.** `canon()` in `_lib.sh` recognised only
   `/`-rooted paths as absolute. Claude Code on Windows hands the hook
   `C:\repo\src\x.ts`; that became `<root>/C:/repo/src/x.ts`, fell outside `ROOT`, and
   every guard allowed it. The hooks had been silently off for Edit/Write on Windows.
2. **Without `jq` the hooks allowed blindly.** Every field parses to empty when `jq` is
   missing, and an empty `FILE` and `CMD` is an allow. On this PC winget's `jq.exe` lives
   in a directory the hook process does not have on PATH, so this was the live state.

## Decision

- `.gemini/settings.json` (committed) wires `BeforeTool` on
  `write_file|replace|run_shell_command` to protect-paths, block-secrets, require-plan and
  protect-tests, `BeforeTool` on `run_shell_command` to production-gate, and `AfterAgent` to
  the verify reminder. Commands are `bash .claude/hooks/<hook>.sh`: Gemini spawns every hook
  with the project directory as `cwd`, and the `bash` prefix makes the same line work under
  PowerShell. The textual `$GEMINI_PROJECT_DIR` substitution is not used, because on Windows
  it yields a single-quoted PowerShell string that does not concatenate with a following
  `/path` (`bash 'C:\repo'/.claude/...` runs bash on the directory).
- `production-gate.sh` treats a set `GEMINI_SESSION_ID` like `SDLC_UNATTENDED`: a deploy
  without a release authorization is blocked, because an ask Gemini cannot render would
  otherwise pass.
- `_lib.sh` folds backslashes, recognises `X:/...` as absolute, and normalises `ROOT` and
  every candidate through `cygpath -m` where that exists, so `C:\repo`, `C:/repo` and
  `/c/repo` all compare equal.
- `_lib.sh` fails closed when `jq` is missing (after looking in winget's package directory
  and adding it to PATH in POSIX form): gating hooks block with an install hint; the two
  advisory hooks exit quietly so a missing tool can never wedge the end of a turn.
- `.gemini/agents/` mirrors the four read-only agents with Gemini's tool names.
- `.gemini` joins `PROTECTED_PATHS`, and hard rule 3 names it, in all three context files.

## Alternatives not taken

- A separate `.gemini/hooks/` directory with Gemini-specific scripts: two copies of every
  guard to keep in sync, for no gain, since the contract is the same.
- Replacing `jq` with a Python parser: `python3` is itself the Microsoft Store stub on this
  PC (roadmap item 19a); failing closed with a one-line fix is safer than a second fallback.
- Making the release gate ask under Gemini via the policy engine's `ask_user`: not reachable
  from a hook, and repo-committable policy TOML is still unverified.

## Consequences

- On Windows, Claude Code sessions in this repo now see the guards for the first time: a
  write under `src/` without an approved plan is blocked, and a control-plane write prints
  the unlock audit line. The first version of the jq fallback put a `C:/` path into the
  MSYS PATH, which the colon splits; it locked the session that wrote it until the owner
  patched the line by hand (`cygpath -u`). A hook change is tested from a second shell
  before the session that made it relies on it.
- The first Gemini run on a clone prompts to trust the folder and to acknowledge the six
  project hooks; until the owner accepts, nothing runs locally and CI is the only gate.
- Whether PowerShell forwards Gemini's stdin to `bash` end to end is verified only by the
  owner running a blocked write in a real Gemini session; the unit tests cover the scripts,
  not the spawn.
- `scripts/adopt.sh --with-hooks` does not yet copy `.gemini/`; adopters running Gemini copy
  it by hand until that follow-up lands (roadmap Phase 1.5).
