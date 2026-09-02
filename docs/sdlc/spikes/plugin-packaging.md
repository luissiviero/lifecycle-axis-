---
type: spike
title: Plugin packaging for the SDLC kit
description: How lifecycle-axis ships as a Claude Code plugin - manifest and marketplace schema, component contribution, hook path resolution, and local dogfooding.
tags: [plugin, packaging, hooks, distribution, sdlc]
timestamp: 2026-09-02T00:00:00Z
status: decided
---

# Spike T02 - plugin packaging
Sources reached (egress was **not** blocked): Context7 `/websites/code_claude` plus live docs [plugins](https://code.claude.com/docs/en/plugins),
[plugins-reference](https://code.claude.com/docs/en/plugins-reference), [plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces),
[discover-plugins](https://code.claude.com/docs/en/discover-plugins), [hooks](https://code.claude.com/docs/en/hooks).
Every claim is from those pages unless tagged UNVERIFIED.

## Findings
### 1. `.claude-plugin/plugin.json`
- The manifest is **optional** (components auto-discover, name comes from the directory); required only for
  metadata or custom component paths. **`name` is its only required field**: kebab-case, no spaces, and the
  namespace for components (`/plugin-name:skill-name`). ([plugins-reference])
- Optional: `displayName`, `version`, `description`, `author{name,email,url}`, `homepage`, `repository`,
  `license`, `keywords`, `metadata`, `skills`, `commands`, `agents`, `hooks`, `mcpServers`, `outputStyles`,
  `lspServers`, `experimental`, `dependencies`, `defaultEnabled`, `userConfig`, `channels`. **`version`** is an
  optional semver **string** (`"1.2.0"`): users get updates only when it is bumped, and it beats the marketplace
  entry's version. ([plugins])
- Custom component paths must be relative, start with `./`, and stay inside the plugin root - a path that
  escapes it is rejected (`path escapes plugin directory`). `skills` takes a directory (string or array; `"."`
  is also accepted), `commands` takes files or directories, `agents` takes **individual `.md` files**,
  `hooks` takes a JSON file path or an inline object. ([plugins-reference])

### 2. `.claude-plugin/marketplace.json`
- Required top level: **`name`** (kebab-case), **`owner`** (object, `name` required; `email`/`url` optional),
  **`plugins`** (array). Optional: `$schema`, `description`, `version`, `metadata.pluginRoot`,
  `allowCrossMarketplaceDependenciesOn`, `renames`. ([plugin-marketplaces])
- Plugin entry: required **`name`** + **`source`**; optional `displayName`, `description`, `version`, `author`,
  `homepage`, `repository`, `license`, `keywords`, `category`, `tags`, `defaultEnabled`, `strict`, component path
  overrides, archive `headers`/`headersHelper`. `source` is a relative path string (`"./plugins/x"`, resolved
  against the marketplace root) or an object (`github`, `url`, `git-subdir`, `npm`, `archive`, `command`).
- Teams auto-install by committing `.claude/settings.json` with `extraKnownMarketplaces` +
  `enabledPlugins: {"plugin@marketplace": true}`; these apply once the user trusts the folder.

### 3. How a plugin contributes components
- All functional dirs live at the **plugin root**, never inside `.claude-plugin/`: `skills/<name>/SKILL.md`,
  `commands/<name>.md` (flat, legacy - prefer `skills/`), `agents/<name>.md`, `hooks/hooks.json`, `.mcp.json`,
  `.lsp.json`, `monitors/monitors.json`, `bin/`, `settings.json`. ([plugins], [plugins-reference])
- Hooks do **not** require `hooks/hooks.json`: the same object may be inlined in the manifest's `hooks` field or
  pointed at another file; the JSON shape is identical to the `hooks` object in `.claude/settings.json`.
- Hook commands reference their own files through **`${CLAUDE_PLUGIN_ROOT}`**, quoted in shell form:
  `"\"${CLAUDE_PLUGIN_ROOT}\"/scripts/format-code.sh"`. Also exported: `${CLAUDE_PLUGIN_DATA}` (persistent) and
  `${CLAUDE_PROJECT_DIR}`. The plugin root path **changes on update** - never store state there.
- Project/user `.claude/agents/` **override** same-named plugin agents; plugin skills are namespaced, so local
  and plugin copies coexist. Plugin hooks fire in **every project where the plugin is enabled**. ([plugins])

### 4. `$CLAUDE_PROJECT_DIR` from plugin-shipped hooks - yes
"These variables are exported to hook processes, MCP servers, and LSP subprocesses", and `${CLAUDE_PROJECT_DIR}`
is the project root ([plugins-reference], [hooks]). So `_lib.sh`'s `ROOT="${CLAUDE_PROJECT_DIR:-...}"` keeps
resolving the **consumer's** `.sdlc/config.env`, `.sdlc/active`, `work/<slug>/plan.md` and
`.sdlc/release-authorizations/` even when the script sits under the plugin root: every consumer-side path in
`.claude/hooks/{require-plan,protect-tests,production-gate,stop-verify-reminder}.sh` is built from `$ROOT`, and
`_lib.sh` is sourced via `$(dirname "$0")`, which stays plugin-relative. Without `.sdlc/config.env`,
`PROTECTED_PATHS`/`PLAN_REQUIRED_PATHS` are empty and `under_any` false, so hooks **fail open** in non-adopting
repos - except the unconditional secret-filename `case` in `protect-paths.sh`.

### 5. Local loading for dogfooding
- `claude --plugin-dir ./my-plugin` (accepts a `.zip`; repeatable; shadows an installed plugin of the same name
  for the session); `/reload-plugins` picks up edits without a restart. ([plugins])
- `/plugin marketplace add ./path` (or `claude plugin marketplace add ./path`, or a `.../marketplace.json`), then
  `/plugin install <plugin>@<marketplace>`. `claude plugin validate ./plugin` checks the manifest (`--strict`
  makes warnings errors). ([discover-plugins], [plugins])
- **A repo can host and consume its own marketplace** - list it in `extraKnownMarketplaces` with a relative
  `source`. For *this* repo that is redundant: `.claude/{skills,agents}` already load as project config, so
  enabling the plugin here duplicates skills under a namespace and lets project agents shadow plugin ones.
  Dogfood against a **temp target produced by `adopt.sh`**, not against this repo.

## Decision
**Default: ship skills, agents, commands, templates and scripts in the plugin; install hooks repo-local via
`scripts/adopt.sh --with-hooks`.** Plugin root = **repo root** (`.claude-plugin/plugin.json` beside `.claude/`),
custom paths `"skills": "./.claude/skills/"`, `"agents": ["./.claude/agents/<name>.md", ...]` - nothing is
duplicated. Chosen on evidence, not for lack of it:

1. A red line must not be per-user optional. Plugin enablement lives in user/local settings and is switchable
   with `/plugin`; hooks in the consumer's `.claude/settings.json` bind everyone who trusts the folder.
2. Plugin hooks run in every enabled project. These hooks are repo governance, not global behaviour, and
   `protect-paths.sh`'s secret-filename check is unconditional.
3. Hooks and the `.sdlc/config.env` they read must version together in the consumer repo, alongside
   `scripts/verify.sh` and the CI chain check enforcing the same contract.

**Fallback (verified, not a guess):** a team wanting zero copied files enables hooks from the plugin via
`"hooks": "./.claude/hooks/hooks.json"`, each command written `"\"${CLAUDE_PLUGIN_ROOT}\"/.claude/hooks/<n>.sh"`;
consumer state still resolves via `$CLAUDE_PROJECT_DIR` (finding 4). Only if the repo still commits `.sdlc/`.

## Consequences
**T21 (manifest + drift check)**
- `.claude-plugin/plugin.json`: `name: "lifecycle-axis"`, semver `version`, `description`, `author`,
  `repository`, `license`, `skills: "./.claude/skills/"`, `agents: [...]` (one entry per file), **no `hooks`
  field** under the default decision. `.claude-plugin/marketplace.json`: `name`, `owner{name}`,
  `plugins: [{name, source, description, version}]`.
- `check_plugin_manifest.py` must also assert: paths start with `./` and stay inside the repo root; `agents`
  lists every `.claude/agents/*.md` and nothing else (that array is the drift-prone field, since `skills` is one
  directory); `version` is semver; no functional dir sits inside `.claude-plugin/`. Call `claude plugin validate .`
  from `scripts/checks/plugin-manifest.sh` only when the CLI is on PATH, skipping with a note otherwise.

**T22 (`adopt.sh`)**
- `--with-hooks` copies `.claude/hooks/*` **and** the `hooks` block of `.claude/settings.json` into the target;
  without it, warn loudly that the deterministic gates are not installed and only CI enforces them. Make it the
  documented default invocation in `README.md`.
- Target hook commands keep `"$CLAUDE_PROJECT_DIR"/...`; no `${CLAUDE_PLUGIN_ROOT}` in a repo-local install.
- Optionally emit `extraKnownMarketplaces` + `enabledPlugins` into the target's `.claude/settings.json` so
  adopters get skills/agents from the plugin while their hooks stay repo-local. Smoke test the result with
  `claude --plugin-dir <kit>` from the temp target, or `/plugin marketplace add <kit>`.

## Unverified items
- UNVERIFIED: whether a marketplace entry may use `"source": "./"` (the marketplace root) for a repo-is-the-plugin
  layout; docs show only `./sub/dir`. Check with `claude plugin validate .`; if rejected, move the plugin to
  `plugins/lifecycle-axis/` or use a `github` source object.
- UNVERIFIED: whether `agents` accepts a **directory** (docs show files only); if it does, T21's drift check on
  that array is unnecessary.
- UNVERIFIED: precedence when a repo has project hooks **and** enables a plugin shipping the same hooks - assume
  both run (duplicate blocks): safe but noisy, so never ship both.
