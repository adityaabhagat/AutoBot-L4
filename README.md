# 🤖 Auto-Bot — The Centralized L4 Issue Solver

> **Built by Aditya Bhagat** · Quorum Business Solutions
> *One tool, every product. Give it a case number — get a verified root cause.*

Auto-Bot takes a Salesforce case ID and runs the complete L4 investigation process for any onboarded Quorum product — **QPTM · TIPS · QDO · QLS · QRD** (extensible to QRA/QCA/QCFS and beyond). It reproduces, classifies, investigates through a cheapest-first gate ladder, adversarially fact-checks itself, writes the L4 triaged documentation, and **remembers every solved case** in a per-product vector knowledge base.

## Quick start

```
claude                          # open Claude Code in this folder
/solve-case 26-01063725         # full investigation graph
/intake 26-01063725             # gather-only (brief, no investigation)
/batch-debug ALALLOCATE QPTM    # direct batch diagnosis
/new-skill QPTM <topic>         # mint a skill for an uncovered symptom family
/onboard-product QLS            # bring a new product in
```

First-time setup:
1. Copy `CONNECTION_CONFIG.template.md` → `CONNECTION_CONFIG.md` and fill in (never committed/indexed).
2. Ensure the Salesforce connector and ADO MCP server are connected (see `.mcp.json` / template).
3. Metadata server (client DB access): bundled at `QuorumMetadataMCP/` and wired in `.mcp.json`. Pick the client/DB per case: `$env:QUORUM_METADATA_ENV = "<env from QuorumMetadataMCP/dbconfig.json>"` (e.g. `EQCU_HD_DEV17` for EQT), then reconnect the `metadata` server — the `metadata-connector` agent will ask you when it can't decide.
4. Build the knowledge indexes: `python engine/kb.py build --all`

## Two ways to solve a case

- **Agent graph** (`/solve-case`) — LLM investigators reason through the full graph; handles novel defects. Deep, slower, token-heavy.
- **Auto-Bot Lite** (`/lite-solve` or `python autobot.py solve <case#>`) — deterministic, zero-LLM pipeline: TF-IDF recall → 280 compiled rules (gate ladder as literal code) → SQL packs with declared interpretations → field-proven recipes. Solves known symptom families in seconds; novel symptoms get a pre-gathered human packet. Spec: `docs/AUTOBOT_LITE_WORKFLOW.md` · schema: `rules/SCHEMA.md` · validate: `python autobot.py check` · grow: `python autobot.py learn <case#>`.

## How it works (30 seconds)

**Intake** pulls everything from Salesforce + ADO and recalls similar past work from the vector KB → **Repro** establishes steps-to-reproduce and whether it still reproduces → **Classify** routes to the cheapest matching gate: *Expected Behavior → Config → Version (already fixed) → Bad Data → Code Change*, with a batch-process sub-flow (normal vs segregated/QPEC) → the routed **investigator** digs with the right server (Salesforce / ADO / metadata) → the **hallucination gate** adversarially verifies every claim against its evidence anchor → **report-writer** produces the deliverable (L4 Triaged doc, Engineering Handoff, or customer explanation + workaround) → **knowledge-curator** writes what was learned back into skills and the vector index.

Full spec: `engine/GRAPH.md` · Architecture: `docs/ARCHITECTURE.md` · Evidence rules: `docs/HALLUCINATION_GUARDRAILS.md`

## Knowledge today

| Product | Skills | Notes |
|---|---|---|
| QPTM | 23 (+3 shared) | Full: study pack, screen info, code cache, config & repo references |
| TIPS | 24 | Full: gas + crude lines, module map, KB router |
| QDO | 4 | Partial — growable via onboarding prompts |
| QLS | scaffold | Integration touchpoints documented; ready to mine |
| QRD | scaffold | Ready to mine |

---
*Auto-Bot — engineered with an obsession for evidence by **Aditya Bhagat**. If it can't prove it, it won't say it.*
