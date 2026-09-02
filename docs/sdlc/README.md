# The AI-native SDLC loop, built into this repo

> Source: Anthropic, *The AI-Native SDLC playbook* (claude.com/blog, 21 Aug 2026) and the companion Claude Academy course.
> This document reconstructs the playbook's model and explains how this repo turns it into **enforced agent behaviour**.

## 1. What the playbook says (digest)

**Thesis.** Agents made code generation cheap, so the bottleneck moved to everything around the code: planning,
design alignment, security review, testing, approval, incident response. Keep the old *control objectives*
(someone decided what to build, someone checked it, someone approved it, someone can audit it) but change the
*enforcement*: from meetings and ticket queues to committed artifacts, hooks, skills, evals, and gates.

**The loop.** Six non-linear stages. Each stage ends by committing one Markdown artifact; the next stage starts by reading it.

| Stage | Reads | Produces | Gate (human) | Claude mechanism |
|---|---|---|---|---|
| Plan | originator's words | `intent.md` | intent accepted | agent interviews originator |
| Design | `intent.md` + standards | `spec.md` (requirements + design) | spec approved | skills encode brand/security/UX/compliance as hard constraints |
| Build | `spec.md` | `plan.md` → diff + tests | plan approved | plan mode; `CLAUDE.md` memory; hooks as red lines; subagents |
| Test | repo + evals | eval results, regressions | eval config review | 20–50 real-task eval suite; every incident adds an eval |
| Deploy | PR | review findings, release | merge; release authorization | layered agentic review (plan match, security), branch protection, `ask` hooks |
| Maintain | production metrics | incident record → new `intent.md` | triage decision | control bands (1σ log, 2σ diagnose, 3σ act); Claude Tag first-response |

**Enforcement has three layers.**
1. *Advisory*: `CLAUDE.md` and skills make the right behaviour likely.
2. *Deterministic*: hooks and CI make the wrong behaviour impossible (protected paths, secrets, release gate, plan-required).
3. *Human judgment*: approvals at the gates. The commit chain is the audit trail: who asked, what the agent made, who approved.

**Role shifts.** Engineers direct, set intent, and approve. QA becomes verification engineering (design the
machine-checkable loops). Engineering managers allocate *verification attention* and *agent budget* instead of engineer-hours.
Security separates four jobs (create, check, authorize, deploy) across different identities.

**Adoption order.** Leaf plays first: intent template, one-page `CLAUDE.md`, a verify command with a clear exit code,
one deterministic hook, plan mode. Then skills, subagents, evals. Then design pass and PR review. Then CI/CD and gates.
Last, the monitoring-driven loop.

## 2. How this repo builds it

```
CLAUDE.md                      one page of repository memory + the eight hard rules
REVIEW.md                      review policy: order, severity, evidence, five-nit cap
.sdlc/                         control plane (agents cannot edit): path classes, verify cmds, active item, release authorizations
work/<slug>/                   intent.md → spec.md → plan.md → incident.md, each with YAML status + approved-by
docs/sdlc/templates/           the four artifact templates
.claude/skills/sdlc-*          one skill per stage transition: /sdlc-intent /sdlc-spec /sdlc-plan /sdlc-review /sdlc-incident
.claude/skills/security-standards   policy-as-skill; loaded by Design and Review
.claude/agents/                explorer (read-only scout), plan-reviewer, security-reviewer, verifier
.claude/hooks/ + settings.json protect-paths, block-secrets, require-plan, production-gate, stop-verify-reminder
scripts/verify.sh              the single pass/fail signal agents and CI use
scripts/check_artifact_chain.py CI: artifacts approved, diff ⊆ plan, release-gated paths declared
.github/workflows/sdlc-gate.yml runs the chain check + verify on every PR
evals/                         workflow evals; run when CLAUDE.md, skills, hooks, or agents change
monitoring/bands.yaml          control bands with 1σ/2σ/3σ tiers
```

### The enforcement matrix (what stops an agent from doing what)

| Behaviour we want | Advisory | Deterministic | Human |
|---|---|---|---|
| No code before an approved plan | CLAUDE.md rule 1, `/sdlc-plan` | `require-plan.sh` blocks Edit/Write under `PLAN_REQUIRED_PATHS` unless `work/<active>/plan.md` is `approved` | sets `status: approved` |
| Diff matches plan | CLAUDE.md rule 2 | `check_artifact_chain.py` fails PR on unplanned files | reviews deviation log |
| Agent never edits the control plane | rule 3 | `protect-paths.sh`; CI job rejects agent PRs touching hooks/workflows/.sdlc | applies via PR |
| No secrets in repo | security-standards §1 | `block-secrets.sh` pattern match on written content | — |
| Agent never crosses into production | rule 4 | `production-gate.sh`: destructive → deny; deploy → `ask`, or deny when unattended, unless `.sdlc/release-authorizations/<sha>` exists | creates the authorization file |
| Verified before review | rule 5 | Stop hook blocks ending a turn with unverified code changes; CI runs `verify.sh` | reads the pasted verify line |
| Review has evidence, ≤5 nits | REVIEW.md, `/sdlc-review` | reviewer subagents are read-only | final approval |
| Mistakes become memory | rule 7 | — (eval added per incident is checked by `/sdlc-incident`) | reviewer insists |
| Subagents are bounded | rule 8 | `tools:` allow-lists in `.claude/agents/*.md` | — |

### Why each design choice

- **Front matter, not labels.** `status`/`approved-by` live in the artifact itself, so hooks, CI, and humans read the same bit. Git blame shows who flipped it.
- **`## Files` in plan.md is a contract.** It is the cheapest "does the diff match the plan" check that is deterministic. Agentic plan review (the `plan-reviewer` subagent) sits on top for semantics.
- **Skills per transition, not per stage.** A skill is where the agent needs a procedure; `/sdlc-spec` and `/sdlc-plan` are where most drift happens.
- **`ask` vs deny in the release gate.** Interactive sessions get a permission prompt naming the commit; unattended sessions (`SDLC_UNATTENDED=1`, set in CI or headless runs) are denied outright. The authorization file is per-commit, so an approval cannot be reused for a different diff.
- **Reviewer subagents cannot write.** That is the "creator ≠ checker" separation from Anthropic's security write-up, done with tool allow-lists.
- **Evals cover the workflow.** Cases assert hook and skill behaviour, so a `CLAUDE.md` edit that weakens a guardrail fails CI.

## 3. Using it in a project

1. Copy this repo's tree into the project (or add it as a template). Fill `VERIFY_CMDS` and the path classes in `.sdlc/config.env`.
2. Rewrite `CLAUDE.md` for the project: commands, architecture in ten lines, the mistakes the team sees most. Keep it to a page.
3. Add project standards as skills (security is included; add `ux-standards`, `api-conventions`, `data-classification` as needed) and list them in `/sdlc-spec`.
4. Protect `main` in GitHub: require `sdlc-gate` and CODEOWNERS review for `RELEASE_GATED_PATHS`.
5. Run the minimal loop by hand once: `/sdlc-intent` → approve → `/sdlc-spec` → approve → `/sdlc-plan` → approve → implement → `/sdlc-review` → PR.
6. Collect 20–50 real tasks into `evals/cases/` and replace `scripts/run_evals.sh` with a runner that drives the agent.
7. Wire `monitoring/bands.yaml` to real metrics and have the detector call `/sdlc-incident`.

See `phase-2-roadmap.md` for what the playbook does not cover.
