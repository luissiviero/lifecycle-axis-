---
name: sdlc-intent
description: Plan stage. Interview the originator and write work/<slug>/intent.md from the template. Use when someone describes a problem, feature, or incident that has no intent.md yet.
---
# /sdlc-intent — capture intent

You are producing the first link in the artifact chain. Do not design or plan yet.

1. Ask for a slug (kebab-case) if not given. Create `work/<slug>/` and copy `docs/sdlc/templates/intent.md`; create
   `work/<slug>/log.md` from `docs/sdlc/templates/log.md` at the same time — it is the item's gate ledger, and
   every later gate appends to it.
2. Interview the originator in their own words. Ask until you can fill every section without inventing:
   problem, who is affected, how we would observe success, hard constraints, what is explicitly out of scope, risk class,
   and which mode they want to run under, supervised or delegated.
   Ask at most three questions per turn. Record unanswered ones under "Open questions".
3. Quote the originator where possible; do not paraphrase intent into solution language.
4. Write the file with `status: in-review` and `risk-class` from the answer. Always write `mode: supervised`:
   `delegated` on the intent is a grant only a human writes, with `scripts/approve.py --delegate` from their own
   shell or by editing the four grant keys in the GitHub web editor. Append the first ledger line to
   `work/<slug>/log.md` (`intent.md | (none) -> in-review`, format in the template), then run
   `python3 scripts/gen_index.py`: it writes `work/<slug>/index.md` and `work/index.md`, and
   `scripts/checks/index-drift.sh` fails the pull request without them. Print the path and the open questions.
5. Open the intent's pull request with `gh pr create --draft` (an intent-only one may run beside the active
   item's code pull request). A draft's gate and review runs conclude `skipped` in seconds, so writing costs
   nothing; mark it ready when you ask the owner to merge, and the gate runs once on that click. The tap comes
   after the merge, not before it: the approval resolves the slug on `main`, where `work/<slug>/` does not
   exist until this pull request lands.
6. Stop. A human sets `status: approved` and `approved-by`. Never set them yourself. Ask for the tap: give the owner the three inputs to pick in the Actions tab (**Actions -> approve -> Run workflow**, `.github/workflows/approve.yml`): `slug`, `artifact`, `mode`. Naming the inputs is not approving -- the owner reads the artifact and chooses, and the run records who chose. For an intent that is also to carry a grant, the owner picks `mode: delegated` there; the
   workflow refuses a delegated grant on any ref but the default branch.

Done means: every success criterion is observable and has a number or a test attached.
