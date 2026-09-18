---
type: sdlc/work-item
id: chain-check-without-gh
title: The chain check crashes on a token with no gh binary instead of taking the skipped path
description: check_artifact_chain.py guards the dispatch attestation against a missing token but not against a missing gh binary, so in every remote session container -- token set, no gh -- the check raises FileNotFoundError at :237 on any item with a tapped approval instead of printing the one-line skipped note it prints when the token is absent; every session since 2026-09-08 has run the checks under env -u GH_TOKEN -u GITHUB_TOKEN to get around it.
timestamp: 2026-09-18T17:20:00Z
---
# The chain check crashes on a token with no gh binary instead of taking the skipped path

- [intent.md](intent.md) — status: superseded; approved-by: luissiviero; check_artifact_chain.py guards the dispatch attestation against a missing token but not against a missing gh binary, so in every remote session container -- token set, no gh -- the check raises FileNotFoundError at :237 on any item with a tapped approval instead of printing the one-line skipped note it prints when the token is absent; every session since 2026-09-08 has run the checks under env -u GH_TOKEN -u GITHUB_TOKEN to get around it.
- [spec.md](spec.md) — status: superseded; approved-by: claude; Seven requirements: a missing gh binary takes the no-token path (None, one note, then the author rule), the retire route included; a present binary that fails stays False; every existing attestation answer is unchanged; the check stays offline; all seen red-then-green in one new test module, with the locked file landing by the owner's click.
- [plan.md](plan.md) — status: superseded; approved-by: claude; kind fix: scripts/test_chain_no_gh.py lands red on three of its six cases, then verify_dispatch_run gains a NO_GH_NOTE constant and a try/except around its one gh call, the module goes green with every locked suite green unmodified, and the two real items that crashed on 17004b4 end CHAIN: PASS with the token set; the locked file lands by the owner's click and the item parks from a ledger-only pull request.

Last gate: - 2026-09-18T22:17:26Z | plan.md | delegated -> superseded | luissiviero | 2ba0fa0
