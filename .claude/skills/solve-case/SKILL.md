---
name: solve-case
description: Run the full Auto-Bot L4 investigation graph on a Salesforce case number — intake, reproduction, classification, gated investigation, hallucination check, report, and knowledge writeback. Use when given a case number to solve (e.g. /solve-case 26-01063725).
---

# /solve-case <CASE_NUMBER> — the main Auto-Bot flow

You are orchestrating the Auto-Bot investigation graph (authority: `engine/GRAPH.md`). Execute the nodes as subagents in this order, passing state ONLY through `cases/<CASE_NUMBER>/` files:

1. **N0** — launch `intake-agent` with the case number. Wait; read back only its summary. If SF has no such case → stop, tell the user.
2. **N0.5** — launch `metadata-connector`. If it returns an `ASK_USER` block → ask the user (AskUserQuestion) which client environment/DB to use, relay the chosen env (`QUORUM_METADATA_ENV=<env>` + reconnect the `metadata` server), and re-run the connector once. NOT CONNECTED after that → proceed degraded (investigators emit `NOT YET RUN` SQL); never stall the graph on this.
3. **N1** — launch `repro-agent`.
4. **N2** — launch `classifier-agent`. If it sets a batch flag → launch `batch-debugger` first and re-run classification with its findings.
5. **Gate** — launch the routed investigator(s) (`config-investigator` | `version-investigator` | `data-investigator` | `code-investigator`). If the Metadata connection is CONNECTED and the route touches G2/G4/G5, launch `table-analyst` in the same parallel batch — its table map + data-chain break point is root-cause evidence for the investigators. Ambiguous two-gate routes run in parallel (single message, multiple Agent calls).
6. **Gate H** — launch `hallucination-checker`. FAIL → send listed claims back to their owning investigators (max 2 iterations), then re-check. Never skip this, even for "obvious" cases.
7. **N4** — launch `report-writer`.
8. **N5** — launch `knowledge-curator`.

## Orchestrator rules

- You do not investigate; agents do. You route, watch verdict blocks, and enforce the two-re-route maximum through N2.
- Progress updates to the user at each node transition: one line each ("N2: classified G4 bad data — duplicate settlement revisions, batch flag none").
- Token discipline: read agents' returned summaries and verdict blocks, not the raw brief/evidence, unless resolving a conflict.
- Final message to the user: outcome class, root cause (with confidence), deliverable path(s), the 5-line SF-paste summary from report-writer, and what the knowledge-curator learned.
- If the user gave multiple case numbers, run the graphs sequentially unless they explicitly ask for parallel.
