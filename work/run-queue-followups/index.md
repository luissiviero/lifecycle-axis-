---
type: sdlc/work-item
id: run-queue-followups
title: The chain check reports PASS on work it never saw; make it say so instead
description: "check_artifact_chain.py diffs <base>...HEAD, so staged and uncommitted work is invisible to it; an empty diff is in-progress mode, and the check prints CHAIN: PASS under a note describing a diff that does not exist. It audited the wrong work twice in one session. The lesson written for it says the guard is nowhere yet; this item writes the guard."
timestamp: 2026-09-08T19:20:00Z
---
# The chain check reports PASS on work it never saw; make it say so instead

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; check_artifact_chain.py diffs <base>...HEAD, so staged and uncommitted work is invisible to it; an empty diff is in-progress mode, and the check prints CHAIN: PASS under a note describing a diff that does not exist. It audited the wrong work twice in one session. The lesson written for it says the guard is nowhere yet; this item writes the guard.
- [spec.md](spec.md) — status: delegated; approved-by: claude; check_artifact_chain.py takes in-progress mode whenever the diff is empty, so staged and uncommitted work reads as CHAIN: PASS under a note describing a diff that does not exist. Refuse that case early, the way the unknown-base-ref case is already refused, and leave verify.sh's --base HEAD self-check untouched.
- [plan.md](plan.md) — status: delegated; approved-by: claude; A guard after changed_all refuses when the diff is empty, the caller did not ask for the self-check, and the working tree is dirty or unreadable; seven regression cases, one mutation-tested eval, and the lesson stops saying the guard is nowhere.

Last gate: - 2026-09-08T19:45:00Z | plan.md | delegated -> delegated | claude | dd1a7a9 | deviation: the owner asked for a documentation pass before the session ends; file list gains knowledge/lessons/index.md (three lessons from #55 and #57 were never indexed, this item's own among them), docs/sdlc/README.md (the chain-check inventory line gains the new refusal) and docs/sdlc/handoff/HANDOFF.md (task state two items stale, missing the GH_TOKEN= prefix a new session needs and commit-then-check). Additive prose, no behaviour. 2 of 5
