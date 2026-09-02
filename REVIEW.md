# REVIEW.md — code review policy

Applies to humans, `/sdlc-review`, and the `security-reviewer` subagent.

## What a review checks, in order
1. **Plan conformance.** Does the diff do what `plan.md` says, and only that?
   Unplanned files or behaviour → `blocking` unless the plan was updated in the same PR.
2. **Spec conformance.** Do the tests prove each acceptance criterion in `spec.md`?
3. **Security.** Run the `security-standards` skill checklist. Any hit → `blocking`.
4. **Correctness.** Bugs you can demonstrate with an input and an expected output.
5. **Maintainability.** Only if it changes what the next engineer must do.

## Severity
| Level | Meaning | Required evidence |
|---|---|---|
| blocking | Must change before merge | `file:line`, the failing input or the policy line violated |
| major | Should change; author may push back with reasons | `file:line` and a concrete scenario |
| minor | Nit. Maximum **five** per review. Skip the rest. | `file:line` |

## Output format
```
[blocking] src/auth/session.ts:42 — token compared with `==`; timing-safe compare required (security-standards §2). Repro: ...
[minor] src/api/users.ts:10 — rename `d` to `deadline`.
Verdict: request-changes | approve | approve-with-nits
Verify: <last line of scripts/verify.sh output>
```

## Do not
- Restate the diff. Comment only where something should change.
- Ask for work outside `plan.md`. Open a new intent instead.
- Approve anything under `RELEASE_GATED_PATHS` without a named human approver.
