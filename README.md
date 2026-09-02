# lifecycle-axis

A starter kit that turns Anthropic's *AI-native SDLC playbook* into enforced agent behaviour for Claude Code projects:
artifact chain (`intent.md → spec.md → plan.md → diff → review → incident`), hooks as red lines, skills as standards,
read-only reviewer subagents, a single verify signal, and CI that checks the chain.

- Start here: [`docs/sdlc/README.md`](docs/sdlc/README.md)
- Pairing with the Open Knowledge Format for Claude + Gemini: [`docs/sdlc/okf-pairing.md`](docs/sdlc/okf-pairing.md)
- What comes next: [`docs/sdlc/phase-2-roadmap.md`](docs/sdlc/phase-2-roadmap.md)
- Metrics per play: [`docs/sdlc/metrics.md`](docs/sdlc/metrics.md)
- Institutional knowledge (decisions, lessons, runbooks, metrics — model-neutral OKF bundle): [`knowledge/`](knowledge/index.md)
- Next work item (draft, awaiting your answers): [`work/sdlc-kit-phase-1/intent.md`](work/sdlc-kit-phase-1/intent.md)
- Agent memory and rules: [`CLAUDE.md`](CLAUDE.md), [`REVIEW.md`](REVIEW.md)
- Adopt this kit in another repo: `scripts/adopt.sh <target>` (`--with-hooks` to install the Claude hooks too)
- Or install it as a Claude Code plugin: [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json)
