---
type: sdlc/intent
id: front-matter
title: Templates and artifact parsers must agree; approve.py must not misfire
description: Inline comments in the artifact templates break the chain check, the ledger and the hooks; approve.py defaults to a handle that is not an approver and enforces no stage order.
stage: plan
status: in-review
author: Luis Siviero (repo owner), drafted with Claude from the 2026-09-04 playbook comparison
approved-by:
approved-on:
supersedes:
record:
resource: https://claude.ai/code/session_01DSYmeD7eng2GKQ3EbHQDzo
tags: [templates, chain-check, approve, hooks, consensus-item-6]
timestamp: 2026-09-04T21:32:24Z
---
# Intent: templates and artifact parsers must agree; approve.py must not misfire

## Problem
A verbatim copy of `docs/sdlc/templates/intent.md`, which `/sdlc-intent` step 1 instructs, fails the
chain check: `front_matter_text()` in `scripts/check_artifact_chain.py:42-53` does not strip the inline
`# …` comments the template carries on `status:`, `approved-by:` and `kind:`, so the status reads as
`draft            # draft | in-review | …` and is "not one of" the enum. `scripts/approve.py` then writes
that comment text into the ledger line, whose `|` characters make the line malformed. The hooks have the
same blind spot in the other direction: `require-plan.sh:19` quotes the garbage in its block message,
and `protect-tests.sh:15-16` fails *open* on `kind: feature   # feature | fix`, on `kind: "fix"`, on
`kind: Fix` and on a CRLF plan, so the test lock silently switches itself off on the template's own
spelling. No test in the suite starts from a template-derived artifact, which is why none of this was
caught (found by the 2026-09-04 comparison against the playbook, consensus item 6).

Two smaller misfires in `scripts/approve.py`: the default handle falls back to the first token of
`git config user.name` (`:75`), which for the owner yields `luis`, not an approver, so every approval
needs `--as`; and it enforces no stage order, so `spec.md` can be approved while `intent.md` is still
a draft (the chain check catches it later, but the tool that records the gate should not record an
impossible gate).

Who is affected: every adopter on their first work item; the owner on every approval; every session
that relies on the fix-time test lock. How we know: the analyst reproduced each case with crafted hook
JSON and a scratch clone (`EXP5`, `EXP7`, `EXP8` in the comparison report).

## Proposed outcome
- A verbatim copy of any template into `work/<slug>/` passes `check_artifact_chain.py` in in-progress
  mode, and `approve.py` on it produces a five-field ledger line with no `#` left on the `status:` line.
- The templates keep their guidance as a comment line above each field, so the hooks' current
  `status:` and `kind:` parsers read a template-derived plan cleanly (pinned by a characterisation
  test). The shared hook parser itself (`fm_value` in `_lib.sh`) lands in `control-plane-visibility`,
  and its use in `require-plan.sh` and `protect-tests.sh` in `loop-protection`, so this item makes
  no hook runtime change.
- `work/_example/` matches the templates field for field and heading for heading.
- `approve.py` without `sdlc.approver` exits 1 with the exact `--as` hint, never guesses from
  `user.name`; approving `spec.md` with an unapproved `intent.md` (or `plan.md` with an unapproved
  `spec.md`) is refused.
- `scripts/approvers.py` exposes `has_role(role, handle)` and a `--has-role` CLI (needed by the
  deploy-gate item that follows).
- `scripts/hooktest.py` fake repos carry `.sdlc/approvers.yaml`, and the hook fixtures that say
  `status: approved` also say `approved-by: luissiviero`, so the approval-gate item that follows can
  validate the approver without flipping today's tests.
- Test count grows by the template-derived, comment, quote, CRLF, handle-default, stage-order and
  `has_role` cases; `scripts/verify.sh` stays green.

## Affected users and systems
- Users: the owner (approvals); adopters (first work item); every Claude Code and Gemini session that
  reads `status:`/`kind:` through the hooks.
- Services / repos / data: this repo only. `scripts/check_artifact_chain.py` (imported by
  `approve.py`, `gen_index.py`, `gen_context_files.py`, `check_okf.py`, `check_plugin_manifest.py`),
  `scripts/approve.py`, `scripts/approvers.py`, `scripts/hooktest.py`, the four templates,
  `work/_example/`, the affected tests, `docs/sdlc/rules/30-conventions.md`. No hook script changes.

## Constraints
- Must: change no hook script in this item (the fail-open `kind:` cases lock in `loop-protection`);
  keep the `VERIFY:`/`CHAIN:`/`EVALS:` contract lines byte-identical.
- Must: stay stdlib-only Python (no PyYAML).
- Must not: change what `status: approved` means, how the ledger is formatted, or the template
  headings (`evals/cases/skill-names-match-templates.yaml` pins them).
- Must not: set `status: approved` or `approved-by` on any artifact from an agent session; this item's
  own artifacts are approved by the owner with `scripts/approve.py` from their shell.
- Out of scope: the approval-field hook and `require-plan.sh`'s approver validation (next items),
  the Bash write-guard, the deploy gate, adopter installation.

## Risk class
low — parsers, templates and tests; the only hook change is a shared parser that widens what is
recognised. Blast radius is this repo's tooling and any adopter that copies it. No data, no secrets,
no deploy path.

## Open questions (agent asks; originator answers; carried into spec.md if unresolved)
- Q: Should a `title:` such as `Fix #12 crash` be read as `Fix` (YAML semantics, comment starts at
  whitespace-then-`#`) or preserved whole? The proposed parser follows YAML; titles with ` #` are rare
  and can be quoted.
  A:
- Q: Should `approve.py` refuse stage-order violations outright, or warn and continue with `--force`?
  Proposed: refuse; the chain check would reject the result anyway.
  A:
