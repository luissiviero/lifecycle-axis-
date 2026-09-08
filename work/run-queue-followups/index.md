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

Last gate: - 2026-09-08T19:50:00Z | PR #58 | draft -> in-review | claude | 19136bc | the guard, seven cases (four seen red before it existed), an eval mutation-tested red three ways, the lesson's enforcement section, and a documentation pass. Design reviewed by plan-reviewer and security-reviewer on sonnet against an Opus 5 writer; their two revise verdicts are revisions/1.md, which corrected an inert predicate and a fail-open path before any code was written. VERIFY: PASS (dd1a7a9), CHAIN: PASS, EVALS: 44 pass 0 fail, OKF: 178 docs 0 warnings. check_artifact_chain.py is a locked path, so the merge is the owner's click and the queue ends here
