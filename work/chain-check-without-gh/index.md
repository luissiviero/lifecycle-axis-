---
type: sdlc/work-item
id: chain-check-without-gh
title: The chain check crashes on a token with no gh binary instead of taking the skipped path
description: check_artifact_chain.py guards the dispatch attestation against a missing token but not against a missing gh binary, so in every remote session container -- token set, no gh -- the check raises FileNotFoundError at :237 on any item with a tapped approval instead of printing the one-line skipped note it prints when the token is absent; every session since 2026-09-08 has run the checks under env -u GH_TOKEN -u GITHUB_TOKEN to get around it.
timestamp: 2026-09-17T23:00:00Z
---
# The chain check crashes on a token with no gh binary instead of taking the skipped path

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; check_artifact_chain.py guards the dispatch attestation against a missing token but not against a missing gh binary, so in every remote session container -- token set, no gh -- the check raises FileNotFoundError at :237 on any item with a tapped approval instead of printing the one-line skipped note it prints when the token is absent; every session since 2026-09-08 has run the checks under env -u GH_TOKEN -u GITHUB_TOKEN to get around it.

Last gate: - 2026-09-18T16:49:41Z | intent.md | superseded -> approved | luissiviero | 9adde1a | mode: delegated
