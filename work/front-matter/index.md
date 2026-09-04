---
type: sdlc/work-item
id: front-matter
title: Templates and artifact parsers must agree; approve.py must not misfire
description: Inline comments in the artifact templates break the chain check, the ledger and the hooks; approve.py defaults to a handle that is not an approver and enforces no stage order.
timestamp: 2026-09-04T21:50:19Z
---
# Templates and artifact parsers must agree; approve.py must not misfire

- [intent.md](intent.md) — status: approved; approved-by: luissiviero; Inline comments in the artifact templates break the chain check, the ledger and the hooks; approve.py defaults to a handle that is not an approver and enforces no stage order.
- [spec.md](spec.md) — status: approved; approved-by: luissiviero; One front-matter parser for every Python reader, comment lines instead of inline comments in the templates, an example that matches them, and an approve.py that only records gates a human can actually hold.
- [plan.md](plan.md) — status: approved; approved-by: luissiviero; Implementation steps for one tolerant front-matter parser, comment-line templates, a matching example, approve.py stage order and handle rules, has_role, and forward-compatible hook fixtures.

Last gate: - 2026-09-04T22:37:37Z | plan.md | build -> in-review | claude | dccde00 | implementation of steps 1-8 complete; tests 300 -> 318, evals 25 pass, OKF 66 docs 0 warnings; five deviations recorded in plan.md
