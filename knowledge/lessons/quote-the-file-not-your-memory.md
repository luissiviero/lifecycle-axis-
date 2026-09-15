---
type: lesson
title: A citation names the file and quotes it; a section name written from memory is a guess
description: "One handoff bullet was miscited twice in two review rounds: first a sentence attributed to a code comment that never held it, then the right sentence filed under the wrong heading of the right file. Both times the substance was correct and the pointer was not, and both times a reviewer had to spend a round proving it. Quote the text and name the file; leave out the heading, or read it first."
tags: [lesson, citation, review, handoff, evidence]
resource: ../../docs/sdlc/handoff/HANDOFF.md
timestamp: 2026-09-14T14:30:00Z
---
# A citation names the file and quotes it

## What happened
One bullet in `docs/sdlc/handoff/HANDOFF.md` explained why the delegated-merge workflow goes red on a
pull request whose `Work-Item` is not the active slug. Its claim was right and its citations were not,
twice in a row.

Round two of the automated review on pull request 90 read the bullet as filing a rule 7 repeat. The
rebuttal was correct — `work/ci-budget` R-7 chose that red run deliberately — but it said the quoted
sentence was "the same sentence" in `scripts/delegated_merge.py`'s `NOT_DELEGATED` comment. It was not.
That comment reads "a refusal about the pull request itself stays red beside it"; the closely worded
sentence the bullet was remembering belongs to a *different* comment, beside the `locked-paths` call,
about an agent branch touching the control plane. The reviewer found it by reading both comments.

Round four, on the corrected bullet, found the next one: the reasoning sentence was attributed to
`work/ci-budget/spec.md`'s `## Decisions`, and it is in `### Failure modes and how they surface` fifty
lines earlier. The quote itself was verbatim and correctly attributed; only the heading was invented.

Both slips cost a reviewer a round each, on a handoff-only pull request whose whole value is that a
later reader can trust it without re-deriving anything.

## Rule
Cite what you read, in this shape: the quoted text, verbatim, and the file it is in. A requirement id
(`R7`) is stable and safe to name. A heading is not, and neither is a position — "a few lines above",
"just below", "in the same section" — because those are the parts most easily supplied from memory
while the quote itself is being copied correctly. This lesson's own pull request proves it: round four
put the sentence under the wrong heading, and round five, on the text written to fix that, said "a few
lines above" about a sentence fifty-seven lines below. If a heading or a distance genuinely helps the
reader, read it first — `grep -n "^#" <file>` beside the two line numbers answers both in one command.
When the same fact appears in several files, quote each one's own words rather than declaring them the
same sentence: near-identical wording in two places is usually two different claims.

## Where it is enforced
Nothing enforces it. The automated reviewer catches it when it reads the cited file, which is what
happened twice here; a check could grep a document's quoted strings against the files it names, but none
exists.
