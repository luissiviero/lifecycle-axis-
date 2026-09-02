---
type: index
title: Lessons
description: Post-mortem lessons, one per incident, linked to the incident record that produced them. Empty until the first incident closes.
tags: [okf, index, lessons]
timestamp: 2026-09-02T20:00:00Z
---

# Lessons

Empty for now. `/sdlc-incident` writes one `type: lesson` file here per closed incident (in addition to the summary
row it appends to `docs/sdlc/lessons.md`, which now points here — see that file), and if the lesson changes how the
agent should behave, the same PR also updates `CLAUDE.md` or a skill, per rule 7.

**File naming.** `knowledge/lessons/<incident-slug>.md`, matching the `work/<slug>/incident.md` that produced it
(link back to it with a relative link). One lesson per file; a single incident that yields more than one distinct
lesson gets `<incident-slug>-<n>.md` for the second and later ones.
