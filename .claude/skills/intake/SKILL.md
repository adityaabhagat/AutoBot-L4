---
name: intake
description: Gather-only mode — pull everything about a Salesforce case (SF + ADO + vector-KB recall), detect the product, and produce the case brief WITHOUT starting the investigation. Use for "get me the details on case X" or to pre-stage a case for later.
---

# /intake <CASE_NUMBER>

Launch the `intake-agent` subagent with the case number. When it returns:

1. Show the user the executive summary + the path to `cases/<CASE_NUMBER>/case_brief.md`.
2. Highlight: detected product (and detection source), the prior gate signal, the strongest KB hit (if it looks like a past-case resolution recipe, say so — the case may be solvable from memory alone).
3. Ask nothing; end by noting they can continue with `/solve-case <CASE_NUMBER>` (the graph will reuse the brief and skip re-gathering).
