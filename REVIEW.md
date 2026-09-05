# Review instructions (REVIEW.md)

Applies to the managed Code Review service, `claude-code-action`, `/sdlc-review`, the reviewer subagents, and humans.

## Passes
Run four passes and tag each finding with its pass:
- **Bugs**: logic errors, broken edge cases, subtle regressions. Evidence: an input and the wrong output.
- **Security**: injection, authentication or authorization gaps, secrets, PII in logs. Apply `.claude/skills/security-standards/SKILL.md`.
- **Compliance**: the change matches `spec.md` (every requirement row has its acceptance test), `plan.md`
  (no unplanned files; deviations logged), and our design principles. A diff that touches `scripts/verify.sh`,
  `scripts/checks/`, `scripts/run_tests.py` or `scripts/run_evals.sh`, or under `kind: fix` an existing test file,
  is **Important** unless `plan.md` names that file.
- **Memory**: a mistake seen for the second time in this repo gets a line in `CLAUDE.md` "Lessons learned" in this PR;
  flag when the change has made `CLAUDE.md` outdated.

## What Important means here
Reserve **Important** for findings that would break behavior, leak data, or breach a policy. Style and naming are **Nits**.

## Cap the nits
Report at most five nits per review; summarize the rest as a count.

## Do not report
Generated files (see `GENERATED_PATHS` in `.sdlc/config.env`) and anything CI already enforces (formatting, lint, the artifact-chain check).

## Format
```
[Important][security] src/auth/session.ts:42 — token compared with `==`; constant-time compare required (security-standards §2). Repro: ...
[Nit][bugs] src/api/users.ts:10 — rename `d` to `deadline`.
Chain: <last line of scripts/check_artifact_chain.py>   Verify: <last line of scripts/verify.sh>
Human approver required: yes/no (RELEASE_GATED_PATHS touched: ...)
Important: <n> | Nits: <m>
```
The delegated-merge workflow reads this last line from the `claude[bot]` review comment and merges a delegated
pull request only when it reads `Important: 0`.

Findings never approve or block on their own. Branch protection requires a code owner; a change under
`RELEASE_GATED_PATHS` requires the owner named in `plan.md`.
