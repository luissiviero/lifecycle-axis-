---
type: index
title: Decisions
description: Architecture and process decisions for the SDLC kit, one file per decision with accepted alternatives and consequences.
tags: [okf, index, decisions]
timestamp: 2026-09-02T20:00:00Z
---

# Decisions

One file per decision (`type: decision`): the alternatives considered, what was decided, and the consequences. New
decisions land here as their task ships; this index is regenerated to add each one as it appears on disk.

<!-- regenerate links when new decisions land -->

- [Control-plane exemption is a human-applied PR label](control-plane-label.md)
- [Deploy only from CI via GitHub Environments](deploy-from-ci.md)
- [One rule source renders CLAUDE.md, GEMINI.md and AGENTS.md](one-rule-source.md)
- [Plugin distribution for the SDLC kit](plugin-distribution.md)
- [bash-write-guard.md](bash-write-guard.md) — hook heuristic and CI job together close the Bash heredoc bypass; human unlock env var
