# Model Policy — which agent runs on which model, and why

> Auto-Bot by **Aditya Bhagat**. Goal: cut cost and wall-clock per case **without weakening the nodes where a wrong answer is expensive or permanent.**

## The tiers

| Tier | Agents | Why this tier |
|---|---|---|
| **opus** | `code-investigator` (G5) · `hallucination-checker` (H) · `data-investigator` (G4) · `knowledge-curator` (N5) · `classifier-agent` (N2) | Wrong answers here are expensive, permanent, or both |
| **sonnet** | `intake-agent` · `repro-agent` · `config-investigator` (G2) · `version-investigator` (G3) · `batch-debugger` · `table-analyst` · `report-writer` (N4) | Structured work, tightly specified by the agent file |
| **haiku** | `metadata-connector` (N0.5) | Mechanical plumbing: read JSON, probe server, string-match client → env |

Set via `model:` frontmatter in `.claude/agents/*.md`, mirrored in `engine/workflows/solve_case.js` (`TIER` map) because that script spawns *generic* agents told to follow an agent file — frontmatter doesn't reach them.

## Why these five stay on the strong model

- **`hallucination-checker`** — 18% of case tokens, and the only thing between a plausible-but-wrong root cause and a customer-facing L4 doc. A cheaper verifier that rubber-stamps claims converts a safety gate into theatre. **Never downgrade this**, even though it looks like an attractive saving.
- **`code-investigator`** — 29% of case tokens. Traces defect mechanisms to `repo/file:line` that go straight into engineering handoffs and ADO bugs.
- **`data-investigator`** — writes correction SQL that touches client data. Cheap mistakes here are expensive mistakes for the customer.
- **`knowledge-curator`** — writes skills that persist. A bad skill poisons every future case that retrieves it; per `HALLUCINATION_GUARDRAILS.md`, "uncited folklore is how knowledge bases rot."
- **`classifier-agent`** — only ~5% of tokens but decides which investigator runs. A wrong gate wastes an entire expensive investigation. Highest leverage per token in the graph.

## Why `report-writer` is sonnet, not haiku

Tempting (9% of tokens, "just template filling"), but it produces the actual deliverable: it must preserve `CONFIRMED`/`INFERRED`/`HYPOTHESIS` labels verbatim, keep customer-facing text free of code symbols, and never launder an inference into a fact. Sonnet holds that discipline; haiku is a real risk of flattened prose and dropped confidence labels for a marginal saving.

## Expected effect (estimates, from one measured run)

Baseline: case 26-01106039 = **876,241 tokens** across 9 agents, all on the session model.

| Case shape | Tokens staying on opus | Rough cost reduction |
|---|---|---|
| G5 code defect (the measured run — worst case) | ~71% | **~20–25%** |
| G1/G2/G3 case (no code investigation — the common path) | ~50% | **~35–40%** |

Plus wall-clock gains on every sonnet/haiku node. These are estimates from a single run, not a benchmark — re-measure after a few cases and retune the map if the split looks wrong.

**The bigger levers are not model choice:**
1. **Auto-Bot Lite** (`autobot.py`) solves known symptom families with **zero LLM calls**. Every case Lite handles is a 100% saving. Route there first.
2. **The gate ladder** already exits cheap: G1/G2/G3 cases never reach the expensive G5 investigator.
3. **KB recall** means solved cases are answered from memory instead of re-investigated.

## Overrides

| Need | How |
|---|---|
| Force every subagent to one model (debugging: "is this a model issue or a prompt issue?") | `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` + `CLAUDE_CODE_SUBAGENT_MODEL=opus` |
| Change the default for untiered subagents | `CLAUDE_CODE_SUBAGENT_MODEL=<alias>` |
| Pin an alias to an exact version | `ANTHROPIC_DEFAULT_OPUS_MODEL=claude-opus-5` (same pattern for sonnet/haiku/fable) |
| One-off escalation of a single agent | Pass `model` on the Agent tool call, or `agent(prompt, {model: 'opus'})` in a workflow — per-invocation wins over frontmatter |

Aliases (`opus`/`sonnet`/`haiku`) are used deliberately instead of pinned IDs so the tiers follow model upgrades without editing 13 files.

## Escalating a hard case

Fixed tiers are the default. When a case is genuinely hard, escalate manually rather than re-tiering:

- Run `/solve-case` and, if the hallucination gate FAILs twice, re-invoke the owning investigator with `model: opus`.
- Weak KB recall (top hit < 0.15) is the signal for a novel case — worth escalating the investigator up front.
- For a whole run: `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1 CLAUDE_CODE_SUBAGENT_MODEL=opus`.

## Not covered here

The mining/onboarding fleets (`docs/ONBOARD_NEW_PRODUCT.md`) spawn 10+ parallel agents and are the biggest consumer of *session* limits — a different workload from case solving. They currently inherit the session model. If session limits become the pain point, tier those next: survey agents → sonnet, skill-writing miners → opus (they write permanent knowledge), consolidators → sonnet.
