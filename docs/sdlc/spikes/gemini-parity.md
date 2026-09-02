---
type: spike
title: Gemini CLI enforcement parity
description: What Gemini CLI can enforce locally versus what must stay CI-only, so T17 can target rule fragments per model.
tags: [gemini, hooks, context-files, enforcement, t03]
timestamp: 2026-09-02T15:30:00Z
status: in-review
---
# Spike: Gemini CLI parity (T03)

Question: for a repo running Claude Code and Gemini CLI, which of the eight hard rules can be a *local* red line
for Gemini, and which stay CI-only? Answer drives T17 (one rule source → `CLAUDE.md` / `GEMINI.md` / `AGENTS.md`).

## Sources
- Context7 `/websites/geminicli` (mirror of geminicli.com docs) — context files, hooks reference, policy engine.
- `raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/…`: `hooks/reference.md`, `hooks/index.md`,
  `cli/gemini-md.md`, `cli/plan-mode.md`, `reference/configuration.md`, `reference/policy-engine.md`, `core/subagents.md`.
- WebSearch (AGENTS.md default behaviour, subagents).
- **Unreachable / not usable:** `geminicli.com` is blocked by the egress proxy (`EGRESS_BLOCKED`); `github.com` HTML blob
  pages and the GitHub MCP tools are scoped to `luissiviero/lifecycle-axis-` only (`Access denied`). `docs/subagents.md`
  and `docs/cli/subagents.md` are 404 — the real path is `docs/core/subagents.md`. Everything below is from
  `raw.githubusercontent.com` or the Context7 mirror.

## Findings

**1. Context files.** Default filename is `GEMINI.md`. Loading is hierarchical: `~/.gemini/GEMINI.md` (global) →
workspace/project files found by walking up to a boundary marker (`.git`, per `context.memoryBoundaryMarkers`) →
just-in-time subdirectory files discovered when tools touch a path; all found files are concatenated into one memory
blob (`/memory show` prints it). Sub-directory discovery is capped at 200 dirs by `context.discoveryMaxDirs`.
`@file.md` imports are supported (`context.importFormat`). The filename is configurable and accepts an **array in
priority order**: `{"context": {"fileName": ["AGENTS.md", "CONTEXT.md", "GEMINI.md"]}}`. **`AGENTS.md` is not read by
default** — only if it is added to `context.fileName`. Extensions carry their own `contextFileName` in
`gemini-extension.json`. No documented byte/line cap on the concatenated context (UNVERIFIED).

**2. Pre-tool interception — yes, and it is close to a drop-in.** Gemini CLI has hooks with eleven events:
`BeforeTool`, `AfterTool`, `BeforeAgent`, `AfterAgent`, `BeforeModel`, `AfterModel`, `BeforeToolSelection`,
`SessionStart`, `SessionEnd`, `Notification`, `PreCompress`. `BeforeTool` is the analogue of Claude's `PreToolUse`.
Contract: JSON on **stdin**, JSON on **stdout**, logs on **stderr**; input carries `session_id`, `cwd`,
`hook_event_name`, `tool_name`, `tool_input`; exit `0` = stdout parsed as JSON, exit `2` = **system block with stderr
as the rejection reason (turn continues)**, other = non-fatal warning. JSON denial is `{"decision":"deny"|"block",
"reason":"…"}`; `continue:false` kills the loop; `hookSpecificOutput.tool_input` rewrites arguments.
Config lives under `hooks` in `settings.json` with `matcher` (regex over tool names, e.g. `"write_file|replace"`),
`name`, `type:"command"`, `command`, `timeout` (ms), `sequential`.
**This repo's hooks are already portable at the block path**: `_lib.sh` blocks with `exit 2` + stderr, reads
`.tool_name` / `.tool_input.file_path` / `.tool_input.command`, and roots itself on `CLAUDE_PROJECT_DIR` — which
Gemini sets "for compatibility" alongside `GEMINI_PROJECT_DIR`, `GEMINI_PLANS_DIR`, `GEMINI_SESSION_ID`, `GEMINI_CWD`.
Only `ask()` (Claude's `permissionDecision:"ask"` JSON) has no `BeforeTool` equivalent — asking is the policy engine's
`ask_user`, not a hook decision.

**3. Per-repo committable settings — yes.** Precedence: defaults → system-defaults → `~/.gemini/settings.json` →
**`.gemini/settings.json` (project)** → system settings → env → CLI args. Project settings carry `hooks`, `mcpServers`,
`context`, `tools` (`allowed`, `exclude`, `confirmationRequired`, `sandbox*`, `shell.*`), `security`, and
`policyPaths` / `adminPolicyPaths`. Trust caveat: a project hook whose name or command changes (e.g. after a `git pull`)
is treated as "a new, untrusted hook" and warns before running — the docs also warn that hooks "execute arbitrary code
with your user privileges". So a committed Gemini hook is a real gate, but a first-run/after-change human ack is in the
loop. Extensions (`gemini-extension.json`) can ship MCP servers, context files and hooks.

**4. Plan mode, permissions, subagents — all three exist.** Plan mode: `gemini --approval-mode=plan`, `/plan`,
Shift+Tab; read-only toolset, writes confined to `~/.gemini/tmp/<project>/<session-id>/plans/*.md`; leaves via the
`exit_plan_mode` tool (hookable: `AfterTool` matcher `exit_plan_mode`). In non-interactive runs the policy engine
auto-approves `enter_plan_mode`/`exit_plan_mode` — so plan mode is **not** an approval gate in CI.
Permissions: a policy engine with TOML rules (`toolName`, `argsPattern`, `commandPrefix`, `commandRegex`, `decision` ∈
`allow|deny|ask_user`, `priority` 0–999, `modes`, `denyMessage`); `deny` removes the tool from the model's memory and
supersedes the deprecated `tools.exclude`. Documented rule locations are `~/.gemini/policies/*.toml` and OS admin
paths; whether `policyPaths` resolves repo-relative paths (i.e. committable policy) is UNVERIFIED.
Subagents: `.gemini/agents/*.md` (project, "shared with your team") or `~/.gemini/agents/*.md`, YAML front matter
`name`, `description`, `tools` (names or `*` / `mcp_*` wildcards), `model`, `temperature`, `max_turns`; body is the
system prompt; subagents cannot call subagents. Direct parity with `.claude/agents/`.

## The eight hard rules

| Hard rule | Enforcement for Gemini |
|---|---|
| 1. No edits under `PLAN_REQUIRED_PATHS` without an approved `plan.md`; `kind: fix` locks tests | **Local** — `BeforeTool` hook in committed `.gemini/settings.json`, matcher `write_file\|replace\|run_shell_command`, running `require-plan.sh` / `protect-tests.sh` unchanged (block via `exit 2` + stderr); backed by `sdlc-gate` |
| 2. Diff must match `plan.md`; update the plan in the same commit | **CI-only** (`sdlc-gate` / `check_artifact_chain.py`) — needs the whole diff, not one tool call |
| 3. Never edit `.claude/hooks/`, `.github/workflows/`, `.sdlc/`, secrets | **Local** — same `BeforeTool` hook running `protect-paths.sh` + `block-secrets.sh`; optional policy-engine `deny` with `argsPattern`; backed by the control-plane job |
| 4. Never deploy, publish, or push to a protected branch | **Local nudge** — `BeforeTool` on `run_shell_command` running `production-gate.sh`; **authoritative gate is CI-only** (branch protection + GitHub Environments, T19) |
| 5. Run `scripts/verify.sh` before asking for review | **Local (advisory)** — `AfterAgent` hook (the `Stop` analogue) reusing `stop-verify-reminder.sh`; authoritative in `sdlc-gate` |
| 6. Review findings cite `file:line`; max five minor comments | **CI-only** — prose rule in the context file + `pr-review.yml` (T20); no local mechanism in either CLI |
| 7. A mistake made twice becomes a line in this file or a skill | **Neither** — prose rule; identical in `CLAUDE.md` / `GEMINI.md` / `AGENTS.md` |
| 8. Subagents have a named role, bounded tools, return evidence | **Local** — `.gemini/agents/*.md` front matter `name` / `description` / `tools` mirrors `.claude/agents/`; no CI check either side |

Net: rules 1, 3, 8 reach real local parity; 4 and 5 reach advisory parity; 2, 6, 7 stay CI-only or prose.
**No Gemini hook is written in this phase** (per the plan) — this spike only fixes what T17 must emit.

## Decision

1. **Generate `AGENTS.md` in full from the same fragments — not a pointer.** Gemini reads `GEMINI.md` by default and
   ignores `AGENTS.md` unless configured, so `AGENTS.md` exists for third-party agents that read only that name; a
   pointer file would be useless to a tool that reads nothing else. Cost is zero once the renderer exists.
2. **Do not add `AGENTS.md` to `context.fileName`.** With `["AGENTS.md","GEMINI.md"]` both files load and the eight
   rules are concatenated twice. `GEMINI.md` stays the only file Gemini loads.
3. **`GEMINI.md` needs a Gemini-specific section** (`50-gemini-only.md`): hooks live in `.gemini/settings.json` and
   fire on `write_file` / `replace` / `run_shell_command`, not `Edit|Write|MultiEdit`; a hook may warn on first run
   after it changes, so the CI gate is the real red line; `exit_plan_mode` is **not** an approved `plan.md`; treat
   `.gemini/` as protected the same way `.claude/hooks/` is.

## Consequences for T17
- Fragment front matter needs a third target: `targets: [claude, gemini, agents]`; `AGENTS.md` gets the neutral set
  (`00`, `10`, `20`, `30`) and neither `40-claude-only.md` nor `50-gemini-only.md`.
- `40-claude-only.md`: `.claude/hooks/`, `PreToolUse`/`Stop`, `/sdlc-*` skills. `50-gemini-only.md`: decision 3 above.
- The rule-identity test must compare the eight rules byte-for-byte across **three** outputs, not two.
- `MAX_CONTEXT_LINES=120` is a repo policy, not a Gemini limit; apply it per output file.
- Follow-up (not this phase): add `.gemini` to `PROTECTED_PATHS` in `.sdlc/config.env` — a `.sdlc` edit, so it needs a
  human PR, and `CONTEXT_FILES` already lists all three files.

## Unverified
- UNVERIFIED: the argument key Gemini's `write_file` / `replace` use inside `tool_input` (assumed `file_path`) and
  `run_shell_command`'s (assumed `command`). A one-line adapter in the hook (`.tool_input.file_path // .tool_input.absolute_path // …`) removes the risk when a Gemini hook is actually written.
- UNVERIFIED: whether `policyPaths` accepts repo-relative paths, i.e. whether policy TOML can be committed per repo.
- UNVERIFIED: whether project `.gemini/settings.json` hooks run without an interactive trust prompt in a
  non-interactive/CI invocation.
- UNVERIFIED: any size cap on concatenated context files (none documented; only `context.discoveryMaxDirs` = 200).
- UNVERIFIED: version skew — docs read from `main`, not a pinned release (Context7 lists v0.36.0–v0.39.1).
