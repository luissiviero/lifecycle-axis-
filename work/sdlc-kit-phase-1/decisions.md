---
type: sdlc/decision-record
id: sdlc-kit-phase-1-decisions
title: Options for the ten open questions in intent.md
description: Alternatives with a recommendation and pros/cons; the owner picks one per question.
status: draft
timestamp: 2026-09-02T00:00:00Z
---
# Decisions for sdlc-kit-phase-1

Pick one row per question (edit this file or answer in chat). "[recommended]" marks my pick.

## Q1 Stacks and commands (verify signal, formatter, test naming)
| Alternative | Pros / cons |
|---|---|
| **One `scripts/verify.sh` per repo reading `.sdlc/config.env` [recommended]** | + one exit code for agents, CI, humans; + CLAUDE.md lists one command; − a small wrapper to maintain per repo |
| Language-native runners listed in CLAUDE.md (`npm test`, `pytest`, …) | + no wrapper; − several commands to remember; − CLAUDE.md and CI drift; − no single pass/fail line to paste |
| Kit auto-detects the stack and generates commands | + zero config; − wrong guesses on mixed repos; − harder to audit what "verified" meant |

## Q2 Repo topology and intent home
| Alternative | Pros / cons |
|---|---|
| **`work/<slug>/` inside each product repo [recommended]** | + chain sits next to the code it produced; + chain check and git metrics are local; − intents that span repos need a link between them |
| One dedicated intent repo for all products | + single place for non-engineers; + cross-repo intents natural; − chain check must follow SHAs across repos; − two histories to audit |
| Monorepo with `work/` at the root | + one chain, one CI; − only sensible if the products already share a repo |

## Q3 Gemini surface and stages
| Alternative | Pros / cons |
|---|---|
| **Gemini CLI for interactive work, reading `GEMINI.md` generated from the same rule source as `CLAUDE.md` [recommended]** | + closest parity with Claude Code (context file, extensions, hook mechanism to verify); + same repo config; − two hook dialects to maintain; − parity of `ask` gates not guaranteed, so CI stays the hard gate |
| Gemini only in CI (Vertex / ADK agents) for the spec and review passes | + sandboxed, no local hooks needed; + model-neutral gates by construction; − no interactive dev loop with Gemini; − two identities to manage in CI |
| Antigravity or another IDE agent reading `AGENTS.md` | + IDE ergonomics; − enforcement is weakest (IDE settings, not repo config); − hardest to audit |

## Q4 Who approves what
| Alternative | Pros / cons |
|---|---|
| **You hold all three roles for now; a separate bot/App identity for agents; branch protection requires one human review [recommended]** | + realistic for one owner; + agent can never self-approve because it is a different identity; − separation of duties is nominal until a second human exists |
| Distinct humans per role (product owner, tech lead, release manager) | + real separation, audit-friendly; − needs a team you may not have yet |
| Agent auto-approves low-risk changes | + speed; − contradicts the playbook until risk tiers are computed (roadmap item 2); − no human in the record |

## Q5 Deploy targets and environments
| Alternative | Pros / cons |
|---|---|
| **Deploy only from CI using GitHub Environments with required reviewers; agents never run deploy commands; the gate hook stays as defence in depth [recommended]** | + model-neutral, uses existing GitHub features, credentials never on a dev machine; + production gate is a GitHub approval, fully logged; − agents cannot rehearse rollback locally; − dev deploys also go through CI |
| Deploy and rollback exposed as MCP tools with per-environment credentials | + the playbook's target state (allowlist, not shell); + agents can deploy to dev freely; − an MCP server per target to build and secure |
| Shell deploy commands matched by regex in the gate hook (today's scaffold) | + works now; − regexes are brittle; − credentials live wherever the shell runs |

## Q6 Legacy source of truth
| Alternative | Pros / cons |
|---|---|
| **Repo is the source of truth; no ticket tool in the loop [recommended]** | + one timestamp authority, simplest chain check; − non-engineers need a git connector (claude.ai / Cowork) to file intents |
| Linkage: `record:` id in artifacts, commit SHA in the tool | + keeps an existing tracker alive; − two truths to reconcile; − extra step per artifact |
| Ticket tool is the truth, artifacts are working copies written back via MCP | + auditors keep their system; − MCP write-back plumbing per tool; − artifacts can lag |

## Q7 Metrics store and CI budget
| Alternative | Pros / cons |
|---|---|
| **GitHub-only metrics (Actions API, PR metadata) plus an Anthropic API key in CI with a spend limit [recommended]** | + no infra; + the playbook's own band examples are CI failure rate and PR cycle time; + prompt evals and triage actually run; − no production bands until a metrics store exists |
| Prometheus / Cloud Monitoring as the band source | + real production bands (5xx, latency); − infra to run and query; − premature for projects without it |
| No key in CI; hook-only evals | + zero cost; − prompt evals never run, so CLAUDE.md and skills are untested; − triage step never fires |

## Q8 Claude platform features
| Alternative | Pros / cons |
|---|---|
| **Team/Pro plan: repo-level `.claude/settings.json` hooks, Claude Code GitHub Action for review, no managed settings [recommended]** | + available now, no admin work; + review runs under its own identity; − a developer can disable local hooks, so CI must be the real gate (already true) |
| Enterprise: managed settings, sandbox, Claude Tag, Claude Security | + non-overridable controls, on-call and scans out of the box; − cost and admin overhead not justified before the loop runs by hand |
| Local-only review via `/sdlc-review`, no CI integration | + free; − review shares the author's session and identity; − no independent record on the PR |

## Q9 OKF today
| Alternative | Pros / cons |
|---|---|
| **Start a `knowledge/` bundle per product repo; conformance check as a warning; Gemini and Claude both read it [recommended]** | + model-neutral memory immediately; + cheap; + two consumers exist on day one (both models); − cross-repo knowledge duplicates until a shared bundle exists |
| One shared knowledge repo pulled in as a git subtree | + single truth across products; − subtree/submodule friction; − chain and knowledge live in different histories |
| Ingest into Google Knowledge Catalog now | + catalog UI and search; − GCP dependency before the format has proven useful; − OKF is v0.1 |

## Q10 Distribution
| Alternative | Pros / cons |
|---|---|
| **Plugin (skills, agents, hooks, templates) plus a thin template repo [recommended]** | + central updates, the playbook's own recommendation; + projects pin a version; − packaging work; − hooks inside a plugin must be enabled per repo |
| Template repo only ("Use this template") | + trivial; − copies drift, fixes never propagate |
| Git subtree of this repo inside each project | + propagates updates; − merge friction; − hook paths and settings differ per project |
