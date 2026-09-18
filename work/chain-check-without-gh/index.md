---
type: sdlc/work-item
id: chain-check-without-gh
title: The chain check crashes on a token with no gh binary instead of taking the skipped path
description: check_artifact_chain.py guards the dispatch attestation against a missing token but not against a missing gh binary, so in every remote session container -- token set, no gh -- the check raises FileNotFoundError at :237 on any item with a tapped approval instead of printing the one-line skipped note it prints when the token is absent; every session since 2026-09-08 has run the checks under env -u GH_TOKEN -u GITHUB_TOKEN to get around it.
timestamp: 2026-09-17T23:00:00Z
---
# The chain check crashes on a token with no gh binary instead of taking the skipped path

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; check_artifact_chain.py guards the dispatch attestation against a missing token but not against a missing gh binary, so in every remote session container -- token set, no gh -- the check raises FileNotFoundError at :237 on any item with a tapped approval instead of printing the one-line skipped note it prints when the token is absent; every session since 2026-09-08 has run the checks under env -u GH_TOKEN -u GITHUB_TOKEN to get around it.

Parked: parked: ready PR #111; click needed (scripts/check_artifact_chain.py). The fix is one locked file, so the delegated merge refuses the code by design and the owner's click merges it; spec and plan signed under the grant with detour records revisions/1.md and revisions/2.md, the module seen red then green, verify.sh green with the token set and unset, automated review Important 0 and Nits 3 on 9afe0f6. Writer claude-fable-5-1

Last gate: - 2026-09-18T17:24:32Z | PR #112 | in-review -> in-review | github-actions[bot] | 622deaf | merged as 622deaf; the queue is empty, .sdlc/active cleared
