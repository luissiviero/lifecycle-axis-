---
type: index
title: Runbooks
description: Pre-approved operational procedures an agent may propose but never run unattended.
tags: [okf, index, runbooks]
timestamp: 2026-09-02T20:00:00Z
---

# Runbooks

One file per procedure (`type: runbook`): preconditions, steps, verification, and who is authorized to run it. An
agent may open the link or PR a runbook proposes; it never executes the procedure itself — see each runbook's own
"propose, never run" section and `.claude/hooks/production-gate.sh`.

- [Roll back a deploy](rollback-deploy.md)
