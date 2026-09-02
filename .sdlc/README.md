`.sdlc/` is the control plane for this repo's SDLC loop. Agents cannot edit it (see `protect-paths.sh`).

- `config.env` — path classes and verify commands used by hooks, CI, and scripts.
- `active` — slug of the work item the current session is implementing (`work/<slug>/`).
- `release-authorizations/<sha>` — one file per human-authorized release; created by a human, checked by `production-gate.sh`.
