---
type: sdlc/work-item
id: standing-grant
title: Delegated mode is the state every session starts in, a subject typed in and a merged pull request out, with no per-item tap
description: "Today every delegated item needs a human tap that writes mode: delegated on its intent; a queue of N items is N taps and an idle repository between them. Move the grant for low-risk items to the human-only policy file as one standing grant, let the intent be signed by the agent under it, and let the merge workflow open a new item when the pointer is empty. Supervised becomes what the owner asks for."
timestamp: 2026-09-08T22:00:00Z
---
# Delegated mode is the state every session starts in, a subject typed in and a merged pull request out, with no per-item tap

- [intent.md](intent.md) — status: in-review; approved-by: ; Today every delegated item needs a human tap that writes mode: delegated on its intent; a queue of N items is N taps and an idle repository between them. Move the grant for low-risk items to the human-only policy file as one standing grant, let the intent be signed by the agent under it, and let the merge workflow open a new item when the pointer is empty. Supervised becomes what the owner asks for.

Last gate: - 2026-09-08T20:31:19Z | intent.md | (none) -> in-review | claude | 5d6ae96 | drafted from the owner's statements (delegated as the default mode, supervised on request; no tap, just start writing) and an exploration of every reader of the grant; measured: the per-item grant and its five readers, intent.md never signable, the pointer's two writers, the parser that raises on an unknown policy key, verify failing on an empty pointer, risk-class unguarded by the hook despite decision 2; risk class proposed medium as the owner's call; six questions answered as proposals for the owner
