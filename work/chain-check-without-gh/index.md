---
type: sdlc/work-item
id: chain-check-without-gh
title: The chain check crashes on a token with no gh binary instead of taking the skipped path
description: check_artifact_chain.py guards the dispatch attestation against a missing token but not against a missing gh binary, so in every remote session container -- token set, no gh -- the check raises FileNotFoundError at :237 on any item with a tapped approval instead of printing the one-line skipped note it prints when the token is absent; every session since 2026-09-08 has run the checks under env -u GH_TOKEN -u GITHUB_TOKEN to get around it.
timestamp: 2026-09-18T17:20:00Z
---
# The chain check crashes on a token with no gh binary instead of taking the skipped path

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; check_artifact_chain.py guards the dispatch attestation against a missing token but not against a missing gh binary, so in every remote session container -- token set, no gh -- the check raises FileNotFoundError at :237 on any item with a tapped approval instead of printing the one-line skipped note it prints when the token is absent; every session since 2026-09-08 has run the checks under env -u GH_TOKEN -u GITHUB_TOKEN to get around it.
- [spec.md](spec.md) — status: delegated; approved-by: claude; Seven requirements: a missing gh binary takes the no-token path (None, one note, then the author rule), the retire route included; a present binary that fails stays False; every existing attestation answer is unchanged; the check stays offline; all seen red-then-green in one new test module, with the locked file landing by the owner's click.
- [plan.md](plan.md) — status: delegated; approved-by: claude; kind fix: scripts/test_chain_no_gh.py lands red on three of its six cases, then verify_dispatch_run gains a NO_GH_NOTE constant and a try/except around its one gh call, the module goes green with every locked suite green unmodified, and the two real items that crashed on 17004b4 end CHAIN: PASS with the token set; the locked file lands by the owner's click and the item parks from a ledger-only pull request.

Parked: parked: ready PR #111; click needed (scripts/check_artifact_chain.py). The fix is one locked file, so the delegated merge refuses the code by design and the owner's click merges it; spec and plan signed under the grant with detour records revisions/1.md and revisions/2.md, the module seen red then green, verify.sh green with the token set and unset, automated review Important 0 and Nits 3 on 9afe0f6. Writer claude-fable-5-1

Last gate: - 2026-09-18T17:35:00Z | plan.md | delegated -> delegated | claude | 3982151 | deviation: the docstring sentence for verify_dispatch_run shipped naming both causes of the caught exception (no gh on PATH, or cwd=ROOT gone), not the wording the plan bullet quoted; the bullet now quotes the shipped sentence and the plan's deviations log records it. Raised by the automated re-review of #111 on 2143b32 as a compliance nit
