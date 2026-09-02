# Auto-Bot Investigation Graph — Engineering Spec

> Part of Auto-Bot by **Aditya Bhagat**. This is the executable contract for the graph: every node's inputs, outputs, exit conditions, and routing rules. `CLAUDE.md` holds the summary; this file is the authority.

The graph is a directed graph with **decision gates**, **one adversarial verification gate on every terminal path**, and a **mandatory writeback node**. Nodes are implemented as subagents in `.claude/agents/`. State between nodes lives in `cases/<CASE>/` (file-based, token-cheap) — never re-fetch what the brief already holds.

---

## Node N0 — INTAKE (`intake-agent`)

**Input:** Salesforce Case number.
**Steps (in order):**
1. SF: case core fields (`Subject, Description, Status, Priority, Product_list__c, Root_Cause__c, Case_Category__c, Azure_DevOps_Module__c, AccountId, OwnerId, CreatedDate, Resolution__c`).
2. **Product detection** → sets `<P>` for every later node. `Product_list__c` first; fallback to vocabulary match in `products/*/PRODUCT.md`; if TBD product, record the discovered value.
3. KB recall: `python engine/kb.py search "<error codes, batch names, tables, symptom phrases>" --product <P> -k 8`. Run 2–3 query variants (Quorum vocabulary, not plain English — plain terms miss ~55%). Log top hits + scores in the brief.
4. SF depth: CaseComments, EmailMessages, attachments (list all; download/inspect only ones named like errors/logs/screenshots), similar-case sweep (Subject keyword SOQL, LIMIT 25).
5. ADO: work items mentioning the case number or top error codes (WIQL `CONTAINS`), state + fixed-in info of any hit.
6. Triage signal: `Root_Cause__c` prior (`Software Defect`/`Application Configuration` → investigate; `Customer Error`/`Training` → likely Expected Behavior; `User Administration Request` → routine ops runbook).
7. **L2 handoff capture**: from CaseComments/emails, record what L2 already tried and ruled out, plus escalation state — L4 must not repeat L2's steps.

**Output:** `cases/<CASE>/case_brief.md`:
```markdown
# Case Brief — <CASE_NUMBER>
Product: <P> (source: Product_list__c | vocabulary | user)
Client/TSP: … | Priority: … | Status: … | Root_Cause__c: …
## Symptom (2-4 lines, verbatim error codes)
## Environment & version (client build, env, plant/period if TIPS)
## Key entities (contracts K#, noms, locations, PQIDs, tables mentioned)
## KB hits (top 5: score, file, section — resolution recipe if found)
## Similar SF cases (number, status, resolution 1-liner)
## ADO hits (id, type, state, fixed-in [CONFIRMED|INFERRED])
## Attachments (name, type, inspected? key finding)
## Prior gate signal (from Root_Cause__c + KB): G1..G5 hint
```
**Exit:** brief written → N0.5. If case number not found in SF → STOP, report to user.

---

## Node N0.5 — CONNECT (`metadata-connector`) — initial step, before any investigation

**Input:** brief (client + product known).
**Job:** bind the investigation to the right client DB via the **Quorum Metadata MCP** (`QuorumMetadataMCP/QuorumMetadataMCP.exe --env <ENV>`, catalog in `QuorumMetadataMCP/dbconfig.json`):
1. Map client → candidate environment(s) (naming: `<CLIENT3>U_HD_DEV17` etc.).
2. Probe the running `mcp__metadata__*` server: which env is it bound to?
3. Match → record `## Metadata connection` (env, server, DB, DEV-tier caveat) in the brief.
4. Ambiguous / mismatch / not running → return `ASK_USER` options (client + DB); **the orchestrator asks the user**, then the user sets `QUORUM_METADATA_ENV=<env>` and reconnects the `metadata` server. NOT CONNECTED is a valid degraded outcome (investigators emit `NOT YET RUN` SQL).

**Exit:** → N1 always (connected or degraded — never blocks the graph).

---

## Node N1 — REPRODUCE (`repro-agent`)

**Input:** `case_brief.md`.
**Job:** Establish *steps to reproduce* and *reproducibility with current data*:
1. Extract explicit steps from description/comments/attachments; else derive expected steps from `steps_to_reproduce` + `screen_logic` knowledge for the module.
2. Judge: could the symptom be reproduced against current data (are the entities/config still in the reported state)? Use metadata server if connected; else emit the repro-check SQL as `NOT YET RUN`.
3. If NOT reproducible now: state why (data changed, already fixed, timing/cycle-dependent, one-time corruption) — that's routing evidence (already fixed → G3 hint; data changed → G4 hint).

**Output:** `## Reproduction` section appended to the brief: numbered steps, reproducibility verdict (`REPRODUCIBLE | NOT-REPRODUCIBLE(<why>) | UNVERIFIED`), evidence anchors.
**Exit:** → N2 always (non-reproducibility is itself evidence, not a dead end).

---

## Node N2 — CLASSIFY (`classifier-agent`)

**Input:** brief (incl. Reproduction).
**Job:** Assign primary class (+ optional secondary) with 1-line justification each, set the **batch flag** if the failing element is a batch process (any process code / PQID / QPEC / scheduled-job symptom), then route.

**Gate ladder — strict order, positive evidence only:**

| Gate | Class | Take when (evidence tests) | Route |
|------|-------|---------------------------|-------|
| G1 | Expected Behavior | KB/skill "Expected-Behavior FAQ" match; behavior matches documented design; `Root_Cause__c` = Customer Error/Training AND no contradicting evidence | report-writer (explanation + workaround) |
| G2 | Config issue | Symptom maps to a documented config key/code table/metadata layer (`config_logic`, `CONFIG_REFERENCE`); wrong value confirmed or strongly indicated | config-investigator |
| G3 | Version issue | ADO shows the defect already fixed/known in a later version than the client's build | version-investigator |
| G4 | Bad data | Data-signature evidence: orphaned rows, constraint conflicts, time-slice overlap, ghost records, post-refresh drift | data-investigator |
| G5 | Code change | All above ruled out or a code-level defect signature exists | code-investigator |

Rules:
- "Couldn't rule out" ≠ match. Fall through to the next gate.
- Ambiguity between two adjacent gates → run both investigators **in parallel**; classifier reconciles on their evidence.
- Batch flag → `batch-debugger` runs FIRST and feeds its findings back into gate selection (a "batch failure" often resolves to config/data/code once diagnosed).

**Output:** `## Classification` in brief: primary, secondary, batch flag (+ normal|segregated), gate route, justification with anchors.

---

## Node N3 — Investigator gates (G2–G5)

Common contract: read the brief, load ONLY the skill sections KB routed to, investigate, append anchored findings to `cases/<CASE>/evidence.md`, return a **verdict block**: `root_cause, evidence anchors, fix/action, confidence (CONFIRMED|INFERRED|HYPOTHESIS), residual risk`. If confidence < CONFIRMED and another gate became more likely, say so — classifier may re-route (max 2 re-routes per case; after that, present ranked hypotheses honestly in the report as an L4 Investigation doc).

### G2 — `config-investigator` (metadata server)
Pin the exact key (KEY_GRP_NM/KEY_NM/scope) → current value vs expected (metadata server or `NOT YET RUN` SQL) → consumer code path (ADO code search for the typed wrapper) → change instruction incl. cache refresh/restart step + client-metadata-layer note (`<CLIENT>.QPTM.Metadata` overrides standard seed).

### G3 — `version-investigator` (ADO server)
Find fixing work item/PR → the actual merge target + release; label every build number `INFERRED` unless confirmed in ReleaseNotes repo. Compare client version (from brief). Deliver: fixed-in version, upgrade guidance, interim workaround. If fix exists but is NOT in any released version → treat as G5-lite: reference the existing bug, don't re-investigate.

### G4 — `data-investigator` (metadata server)
Diagnostic SQL from skills (each query commented with what its result proves) → bad-data signature → correction script (wrapped in transaction, with row-count sanity checks and rollback note) → root cause of the corruption (one-time vs recurring; recurring → secondary G5/G2 finding).

### G5 — `code-investigator` (ADO server)
Client override repo FIRST (`<CLIENT>.<PRODUCT>.*`), then base repo (`REPO_REFERENCE` in `products/<P>/knowledge/code_logic/`) → trace error code → rule/service → exact `repo/file:line` verified against live file content (`repo_file`) → defect mechanism → ranked fix options (primary with diff, rejected alternative with reason).

### Batch flag — `batch-debugger`
Normal vs segregated diagnosis (QPEC seg-processes, PQID triage, seg logs) — see agent file. Output feeds classifier, not the report directly.

### Table support — `table-analyst` (runs alongside G2/G4/G5 when Metadata connection is CONNECTED)
Builds the module's table map, verifies objects/schemas/registered SQLs live, interrogates row-level state for the case entities (SELECT-only, entity-scoped), and marks where the data chain breaks. Its verdict (`signal: G2|G4|G5|structural`) is evidence for the investigators and classifier — table-level root causes (missing objects, broken chains, constraint conflicts) usually surface here first. DEV-tier caveat: schema/config findings are CONFIRMED anchors; PRD data-state stays INFERRED.

---

## Gate H — HALLUCINATION GATE (`hallucination-checker`) — MANDATORY

Runs on every terminal path BEFORE report writing. Adversarial: tries to REFUTE each claim in `evidence.md` + verdict blocks against `docs/HALLUCINATION_GUARDRAILS.md`:
- every table/column/error-code/file-path claim has an anchor that actually contains it;
- confidence labels are honest (no CONFIRMED without a live-source or query anchor);
- the conclusion answers the CUSTOMER'S reported symptom (drift check: does the root cause explain the original complaint, not a nearby interesting bug?);
- fixed-in builds labeled; line numbers carry the re-baseline caveat.

**Fail →** kick the specific claims back to the owning investigator (max 2 iterations, then downgrade claims to HYPOTHESIS and proceed honestly). **Pass →** N4.

---

## Node N4 — REPORT (`report-writer`)

Pick template by outcome: G1 → `TEMPLATE_Customer_Explanation.md`; G2/G3/G4 → `TEMPLATE_Investigation_Report.md` (14-section) with class-specific sections; G5 CONFIRMED → `TEMPLATE_L4_Triaged.md` (+ `TEMPLATE_Engineering_Handoff.md` when the user asks for the handoff); G5 unconfirmed → L4 Investigation variant (ranked hypotheses H1–H3 + diagnostic plan). Save as `cases/<CASE>/report_<type>.md`. Aditya Bhagat footer always.

---

## Node N5 — WRITEBACK (`knowledge-curator`) — MANDATORY

1. Was the symptom family covered by an existing skill? If NO (weak KB hits at intake, or novel cluster) → create `products/<P>/skills/SKILL_<Category>.md` (or a new section in the closest skill) using the standard skill anatomy (Quick Triage → Decision Tree → clusters → Known ADO items → Diagnostic SQL → Expected-Behavior FAQ → Escalation). Cross-product symptom → `products/_shared/skills/`.
2. Update the product's KB router (`*_Issue_Knowledge_Base.md` symptom→skill table).
3. `python engine/kb.py remember --product <P> cases/<CASE>/report_<type>.md` — pass each report file explicitly (multiple files allowed in one call); archives + reindexes.
4. Move case folder to `cases/_archive/` when the user confirms delivery.

---

## Failure & recovery rules

- MCP server down → degrade gracefully: emit the exact queries/SQL you would have run, labeled `NOT YET RUN`, and continue with KB + cached knowledge. Never fabricate results.
- Two re-route maximum through N2; then ship ranked hypotheses (honesty over false certainty).
- Long case (context pressure) → the brief IS the state; agents must re-read it rather than asking the orchestrator to repeat facts.
- Parallelism: G-investigators and batch-debugger may run concurrently; N0→N1→N2 is sequential; H and N4/N5 are sequential.
