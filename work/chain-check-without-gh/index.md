---
type: sdlc/work-item
id: chain-check-without-gh
title: The chain check crashes on a token with no gh binary instead of taking the skipped path
description: check_artifact_chain.py guards the dispatch attestation against a missing token but not against a missing gh binary, so in every remote session container -- token set, no gh -- the check raises FileNotFoundError at :237 on any item with a tapped approval instead of printing the one-line skipped note it prints when the token is absent; every session since 2026-09-08 has run the checks under env -u GH_TOKEN -u GITHUB_TOKEN to get around it.
timestamp: 2026-09-18T17:00:00Z
---
# The chain check crashes on a token with no gh binary instead of taking the skipped path

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; check_artifact_chain.py guards the dispatch attestation against a missing token but not against a missing gh binary, so in every remote session container -- token set, no gh -- the check raises FileNotFoundError at :237 on any item with a tapped approval instead of printing the one-line skipped note it prints when the token is absent; every session since 2026-09-08 has run the checks under env -u GH_TOKEN -u GITHUB_TOKEN to get around it.
- [spec.md](spec.md) — status: delegated; approved-by: claude; Seven requirements: a missing gh binary takes the no-token path (None, one note, then the author rule), the retire route included; a present binary that fails stays False; every existing attestation answer is unchanged; the check stays offline; all seen red-then-green in one new test module, with the locked file landing by the owner's click.

Last gate: - 2026-09-18T16:59:40Z | spec.md | in-review -> delegated | claude | 2a3d2f8 | revision 1: detour: the fix is one locked file, scripts/check_artifact_chain.py; build it to a ready pull request and park with click needed, per the detour rule's step 5; both reviewers revise (plan-reviewer claude-sonnet-5, security-reviewer claude-opus-5); the writer is claude-fable-5-1
