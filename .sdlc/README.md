`.sdlc/` is the control plane for this repo's SDLC loop. Agents cannot edit it (see `protect-paths.sh`).

- `config.env` — path classes and verify commands used by hooks, CI, and scripts.
- `active` — slug of the work item the current session is implementing (`work/<slug>/`).
- `release-authorizations/<sha>` — one file per human-authorized release; created by a human, checked by `production-gate.sh`.
- `APPROVERS_FILE` — path to the roles/approvers file used to validate `approved-by` in chain artifacts.
- `KNOWLEDGE_PATHS` — directories scanned by the OKF conformance checker.
- `OKF_STRICT` — when `1`, the OKF conformance check fails the build on warnings instead of only warning.
- `CONTEXT_FILES` — the generated agent context files (e.g. `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`).
- `RULES_SRC` — directory of rule fragments rendered into each file in `CONTEXT_FILES`.
- `CONTROL_PLANE_LABEL` — PR label that exempts a control-plane diff from the automated block; applied by a human only.
- `BASH_WRITE_GUARD` — when `1`, `protect-paths.sh` also inspects Bash commands for writes to protected paths.
- `MAX_CONTEXT_LINES` — maximum line count allowed in each generated context file.

