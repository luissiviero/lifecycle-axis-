---
type: sdlc/work-item
id: run-queue-followups
title: The chain check reports PASS on work it never saw; make it say so instead
description: "check_artifact_chain.py diffs <base>...HEAD, so staged and uncommitted work is invisible to it; an empty diff is in-progress mode, and the check prints CHAIN: PASS under a note describing a diff that does not exist. It audited the wrong work twice in one session. The lesson written for it says the guard is nowhere yet; this item writes the guard."
timestamp: 2026-09-08T19:10:00Z
---
# The chain check reports PASS on work it never saw; make it say so instead

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; check_artifact_chain.py diffs <base>...HEAD, so staged and uncommitted work is invisible to it; an empty diff is in-progress mode, and the check prints CHAIN: PASS under a note describing a diff that does not exist. It audited the wrong work twice in one session. The lesson written for it says the guard is nowhere yet; this item writes the guard.
- [spec.md](spec.md) — status: delegated; approved-by: claude; check_artifact_chain.py takes in-progress mode whenever the diff is empty, so staged and uncommitted work reads as CHAIN: PASS under a note describing a diff that does not exist. Refuse that case early, the way the unknown-base-ref case is already refused, and leave verify.sh's --base HEAD self-check untouched.
- [plan.md](plan.md) — status: delegated; approved-by: claude; A guard after changed_all refuses when the diff is empty, the base is not HEAD and the working tree is dirty; _rev is hoisted so the base-versus-HEAD comparison has one spelling; four regression cases, one mutation-tested eval, and the lesson stops saying the guard is nowhere.

Last gate: - 2026-09-08T19:01:45Z | plan.md | in-review -> delegated | claude | c0aa58c
