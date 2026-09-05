---
type: lesson
title: Send ledger lines to the owner in a fenced block, never as bullets
description: "A ledger line pasted into the GitHub web editor from a chat bullet arrives as '- - <ts> | …' and the ledger parser drops it; it happened on bash-guard-hardening and deploy-gate."
tags: [lesson, ledger, approvals, web-editor]
resource: ../../scripts/log_ledger.py
timestamp: 2026-09-05T04:45:00Z
---
# Send ledger lines to the owner in a fenced block, never as bullets

## What happened
The owner approves from a phone in the GitHub web editor and pastes the ledger lines the session sends. A line sent
as a chat bullet arrives as `- - <ts> | …`; `scripts/log_ledger.py` drops it and the approval leaves no ledger
trace. It happened on `work/bash-guard-hardening` and `work/deploy-gate`.

## Rule
Send approval lines in a fenced code block, never as bullets, and run
`python3 scripts/log_ledger.py work/<slug>/log.md` right after the approval commit lands.

## Where it is enforced
`scripts/log_ledger.py` reports the parsed lines; the session's checklist. Prose beyond that.
