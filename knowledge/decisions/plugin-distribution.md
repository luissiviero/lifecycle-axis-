---
type: decision
title: Plugin distribution for the SDLC kit
description: The kit ships as a Claude Code plugin carrying skills, agents, commands, templates and scripts; hooks stay repo-local, installed by scripts/adopt.sh --with-hooks, and a drift check keeps the manifest honest.
tags: [plugin, packaging, distribution, hooks, sdlc]
timestamp: 2026-09-02T00:00:00Z
---

# Plugin distribution for the SDLC kit

## Context

`work/sdlc-kit-phase-1/decisions.md` Q10 asked how `lifecycle-axis` should reach a new
repository: a thin template a user clones and edits in place, or a Claude Code plugin a user
installs and updates. The owner accepted **plugin + thin template repo**. `docs/sdlc/spikes/plugin-packaging.md`
(T02) answered the open questions from live docs (Context7 `/websites/code_claude` plus
`plugins`, `plugins-reference`, `plugin-marketplaces`, `discover-plugins`, `hooks` — egress was
not blocked) and is authoritative on the manifest schema and on the packaging decision below;
this record carries that decision into the shipped manifest (T21) and states its consequences.

The hard question was whether the deterministic gates — `.claude/hooks/*.sh`, wired through
`.claude/settings.json` — can travel inside the plugin too, or must stay repo-local.

## Decision

**The plugin ships skills, agents, commands, templates and scripts. Hooks stay repo-local,
installed by `scripts/adopt.sh --with-hooks` (T22).** Plugin root is the repo root:
`.claude-plugin/plugin.json` sits beside `.claude/`, `docs/`, `scripts/`. Per the spike's
finding 3, components normally auto-discover from `skills/`, `agents/`, `commands/` at the
plugin root, but this repo keeps them under `.claude/skills/` and `.claude/agents/` for
dogfooding (so the same files serve both the project's own Claude Code session and the shipped
plugin) — so `plugin.json` points at them explicitly with relative `./`-prefixed custom paths
instead of relying on auto-discovery:

- `"skills": "./.claude/skills"` — one directory path; a plugin skill directory covers every
  subdirectory holding a `SKILL.md`, so new skills need no manifest edit.
- `"agents": ["./.claude/agents/explorer.md", "./.claude/agents/plan-reviewer.md", "./.claude/agents/security-reviewer.md", "./.claude/agents/verifier.md"]`
  — the spike marks "does `agents` accept a directory" **UNVERIFIED** (docs show individual
  `.md` files only), so each agent file is listed explicitly rather than assumed to auto-cover.
  This is the drift-prone field: `scripts/check_plugin_manifest.py` fails a build that adds an
  agent file without adding it here (or vice versa).
- No `hooks` key in `plugin.json`.

Why hooks stay out, from the spike's evidence (not for lack of a working mechanism — findings 3
and 4 confirm a plugin *can* ship hooks via `${CLAUDE_PLUGIN_ROOT}`-relative commands that still
resolve the consumer's `.sdlc/config.env` through `$CLAUDE_PROJECT_DIR`):

1. A red line must not be per-user optional. Plugin enablement lives in user/local settings and
   is toggled with `/plugin`; hooks belong in the consumer's own `.claude/settings.json`, which
   binds everyone who trusts the folder, not just whoever has the plugin enabled this session.
2. Plugin hooks fire in **every** project where the plugin is enabled. These hooks are this
   repo's governance (protected paths, secret filenames, the plan-required gate), not global
   behaviour a user would want turned on everywhere they happen to enable the kit's skills.
3. Hooks and the `.sdlc/config.env` they read (`PROTECTED_PATHS`, `PLAN_REQUIRED_PATHS`,
   `RELEASE_GATED_PATHS`, …) must version together in the consumer repo, alongside
   `scripts/verify.sh` and the CI chain check that enforce the same contract. Splitting the hook
   scripts into the plugin while the config they read stays in the consumer invites the two to
   drift out of sync silently.

`.claude-plugin/marketplace.json` names the marketplace (`lifecycle-axis`, owner `luissiviero`)
and lists one plugin entry (`lifecycle-axis-sdlc`) with `"source": "./"` — this repo hosts and
is the plugin in one. That value is carried forward from the spike as **UNVERIFIED** (see below);
`scripts/checks/plugin-manifest.sh` runs `claude plugin validate .` when the CLI is on PATH and
it accepted `"source": "./"` without complaint in this session (`claude` 2.1.258) — evidence, not
proof against a future schema change, so the uncertainty stays recorded rather than assumed
resolved.

### Alternatives considered

| Alternative | Pros / cons |
|---|---|
| **Ship skills/agents/commands/templates/scripts in the plugin; hooks repo-local via `adopt.sh --with-hooks` [chosen]** | + red lines stay bound to the repo everyone trusts, not to a per-user plugin toggle; + hooks and the config they read version together; − adopters run one extra `--with-hooks` step and a second copy of the same skills/agents exists in every consumer (plugin-namespaced, no functional duplication) |
| Ship everything, hooks included, via `plugin.json`'s inline `hooks` field | + one install step, zero repo-local files; − a red line becomes exactly as optional as any other plugin, toggled off with `/plugin disable`; − hooks fire in *every* enabled project, not just repos that opted into this governance; − `.sdlc/config.env` still has to live in the consumer, so the hook and its config can drift apart across plugin versions |
| No plugin; thin template repo only, cloned and edited in place | + simplest mental model; − no update path — an adopter's copy of skills/agents/scripts silently rots against upstream fixes; rejected by the accepted decision (Q10) itself |

## Consequences

- `scripts/adopt.sh` (T22) must document `--with-hooks` as the recommended default invocation in
  `README.md` and warn loudly when it is omitted: without it, the deterministic gates are not
  installed locally and only CI enforces the eight hard rules.
- `scripts/check_plugin_manifest.py` + `scripts/checks/plugin-manifest.sh` (this task) are the
  drift check: every `.claude/skills/*/SKILL.md` and `.claude/agents/*.md` must be covered by
  `plugin.json`, every `SKILL.md`/agent front-matter `name` must equal its directory/filename
  stem, `plugin.json`/`marketplace.json` must agree on the plugin name, and any `hooks` paths a
  future manifest references must exist and be executable. It runs as a self-registering
  `scripts/checks/*.sh` picked up by `scripts/verify.sh` (T05), and `evals/cases/plugin-manifest-lists-every-skill.yaml`
  locks in that a skill directory added without a manifest update is caught.
- **Per-user enablement caveat**: enabling `lifecycle-axis-sdlc` gives a user the skills, agents
  and slash commands, but *not* the hooks — a developer who enables the plugin without also
  running `adopt.sh --with-hooks` can invoke `/sdlc-plan` and friends with none of the red lines
  (`protect-paths.sh`, `block-secrets.sh`, `require-plan.sh`, `production-gate.sh`) active
  locally. CI (`sdlc-gate.yml`, the chain check) is the backstop for that gap; this is the same
  shape of caveat the spike's fallback exists to close for a team that wants hooks distributed
  via the plugin instead.
- Dogfooding this repo's own plugin against itself is redundant and confusing (`.claude/{skills,agents}`
  already load as project config; enabling the plugin here would duplicate skills under a
  namespace and let project agents shadow plugin ones) — per the spike, verify packaging against
  a **temp target produced by `adopt.sh`**, not this repo.

## Unverified items (carried from the spike)

- UNVERIFIED: whether a marketplace entry may use `"source": "./"` for a repo-is-the-plugin
  layout; the docs the spike reached show only `./sub/dir` examples. `claude plugin validate .`
  accepted it in this session; if a future CLI version rejects it, move the plugin to
  `plugins/lifecycle-axis/` or switch to a `github` source object.
- UNVERIFIED: whether `plugin.json`'s `agents` field accepts a directory path the way `skills`
  does. Docs show individual `.md` files only, so `check_plugin_manifest.py` treats the array as
  authoritative and drift-checks it; if a directory form is confirmed later, the per-file listing
  and its drift check become unnecessary (not wrong — just more verbose than needed).
- UNVERIFIED: precedence when a repo has project-local hooks **and** enables a plugin shipping
  the same hooks. Assume both run (duplicate blocks: safe, just noisy) — reason enough never to
  ship the same hook both ways, which this decision already avoids by keeping hooks out of the
  plugin entirely.

## How to try it locally

```sh
# Load the plugin from this checkout without installing it, shadowing any
# installed plugin of the same name for the session:
claude --plugin-dir /home/user/lifecycle-axis-
# /reload-plugins picks up further edits without restarting.

# Validate the manifest and marketplace files directly (what
# scripts/checks/plugin-manifest.sh also runs when `claude` is on PATH):
claude plugin validate .
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .claude-plugin/marketplace.json

# Run the repo's own drift check:
python3 scripts/check_plugin_manifest.py
```

Do not enable the plugin inside *this* repo for real use (see Consequences); use a temp target
produced by `scripts/adopt.sh` to exercise the plugin-plus-hooks combination an adopter would
actually run.

## Links

- `docs/sdlc/spikes/plugin-packaging.md`
- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `scripts/check_plugin_manifest.py`
- `scripts/checks/plugin-manifest.sh`
- `scripts/test_check_plugin_manifest.py`
- `evals/cases/plugin-manifest-lists-every-skill.yaml`
- `scripts/adopt.sh` (T22)
- `work/sdlc-kit-phase-1/decisions.md`
