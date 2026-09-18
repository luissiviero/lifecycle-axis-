---
type: sdlc/log
id: chain-check-without-gh-log
title: Gate ledger for chain-check-without-gh
description: Chronological record of stage transitions and approvals for this work item.
timestamp: 2026-09-17T23:00:00Z
---
# Log: chain-check-without-gh

Format: `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>`
(append-only; `<note>` is optional; parsed by `scripts/log_ledger.py`).

- 2026-09-17T23:00:00Z | intent.md | (none) -> in-review | claude | 17004b4 | drafted as defect 3, the item the 2026-09-17 ~22:45 Task state named next. One fault, reproduced on 17004b4 (main, full clone, token set, no gh binary): check_artifact_chain.py:233 returns the skipped note only when no token is set and :237 then runs gh api unconditionally, so --slug ci-budget and --slug self-check-false-reds each end in FileNotFoundError 'gh' with exit 1 and no CHAIN line, and CHAIN: PASS with three author-rule notes under env -u GH_TOKEN -u GITHUB_TOKEN. Measured precisely: the call is reached only for an item with a tapped approval, so verify.sh on 17004b4 itself passes with the token set because .sdlc/active is empty, and crashes again the moment the pointer names any tapped item, this one included after its first tap. CI never sees it (sdlc-gate.yml supplies the token on ubuntu-latest, which ships gh). risk-class medium (the fix sits on the path where the gate decides not to check; the policy delegates low only, so medium keeps it supervised), mode supervised. DETOUR: needed (2), check_artifact_chain.py on locked-paths and verify.sh on PROTECTED_PATHS/ALWAYS_LOCKED, so the code lands by the owner's click; no detour record filed, this intent seeks no grant. Five open questions, each with a proposed answer
- 2026-09-18T11:38:16Z | intent.md | in-review -> approved | luissiviero | d33b145
- 2026-09-18T12:00:00Z | intent.md | in-review -> in-review | luissiviero | main | open questions answered: all five proposals accepted as written, the owner delegating each answer to the drafter's proposal for autonomy; Q3 stays medium and supervised
