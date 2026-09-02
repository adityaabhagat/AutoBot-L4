# Auto-Bot Architecture

> The centralized L4 issue solver — **built by Aditya Bhagat**, Quorum Business Solutions.

## What it is

One Claude Code project that takes a Salesforce case number for ANY onboarded Quorum product (QPTM, TIPS, QLS, QDO, QRD, …) and runs the L4 process end-to-end: intake → reproduce → classify → investigate through the cheapest-first gate ladder → adversarial hallucination check → templated report → knowledge writeback. Product knowledge is file-based and vector-indexed per product, so every solved case makes the next one faster and cheaper.

## Folder map

```
Auto-Bot/
├── CLAUDE.md                    # Master orchestrator instructions (start here)
├── README.md
├── .mcp.json                    # ADO MCP server (SF connector is account-level; metadata server per template)
├── CONNECTION_CONFIG.template.md# Fill in and save as CONNECTION_CONFIG.md (git/kb-ignored, never indexed)
├── .claude/
│   ├── agents/                  # 11 graph nodes as subagents
│   │   ├── intake-agent.md          # N0  gather SF+ADO+KB, detect product, write brief
│   │   ├── repro-agent.md           # N1  steps to reproduce + reproducibility verdict
│   │   ├── classifier-agent.md      # N2  5 classes + batch flag + gate routing
│   │   ├── config-investigator.md   # G2  config keys/metadata layers
│   │   ├── version-investigator.md  # G3  already-fixed check (ADO)
│   │   ├── data-investigator.md     # G4  bad-data signature + correction script
│   │   ├── code-investigator.md     # G5  code root cause to file:line
│   │   ├── batch-debugger.md        # flag normal vs segregated (QPEC) batch
│   │   ├── hallucination-checker.md # H   adversarial verify (mandatory)
│   │   ├── report-writer.md         # N4  templated deliverables
│   │   └── knowledge-curator.md     # N5  skill writeback + kb remember
│   └── skills/                  # entry points: solve-case, intake, batch-debug, new-skill, onboard-product
├── engine/
│   ├── GRAPH.md                 # graph engineering spec (nodes/edges/gates/failure rules)
│   ├── kb.py                    # per-product TF-IDF vector KB (build/search/stats/remember/products)
│   └── workflows/solve_case.js  # optional deterministic Workflow-tool orchestration of the graph
├── products/
│   ├── _shared/skills/          # cross-product skills — indexed into every product's KB
│   ├── _template/               # scaffold for new products
│   └── <P>/                     # QPTM · TIPS · QLS · QDO · QRD
│       ├── PRODUCT.md           # identity, Product_list__c, vocabulary table, routing rules
│       ├── skills/              # SKILL_*.md (SF-mined symptom skills + SKILL_ADO_* defect skills)
│       ├── knowledge/           # 11 logic categories + routers/references
│       │   ├── business_logic/ functional_logic/ code_logic/ screen_logic/
│       │   ├── config_logic/ metadata_logic/ table_logic/ module_logic/
│       │   ├── domain_logic/ architecture_logic/ steps_to_reproduce/
│       │   └── <P>_Issue_Knowledge_Base.md   # symptom→skill router
│       ├── past_cases/          # case memory (solved reports live here)
│       ├── code_cache/          # cached source (indexed; note capture dates)
│       └── kb_index/            # TF-IDF index (generated; never edit)
├── cases/                       # active case workspaces + _archive/
├── templates/                   # Investigation (14-sect), L4 Triaged (8-sect), Eng Handoff (13-sect), Customer Explanation
└── docs/                        # this file, HALLUCINATION_GUARDRAILS, ONBOARD_NEW_PRODUCT, legacy workflow
```

## Design decisions

- **File-based state, per-case workspace** — agents communicate through `cases/<CASE>/case_brief.md` + `evidence.md`, not conversation context. Cheap in tokens, survives session breaks, auditable.
- **TF-IDF vector KB, offline** — no embedding API cost/latency/keys; discriminates on Quorum vocabulary (error codes, process codes, table prefixes), which is exactly what TF-IDF is good at. Per-product indexes keep searches sharp; `_shared` skills are indexed into every product.
- **Cheapest-first gate ladder** — mirrors the human L4 flow (expected behavior → config → version → bad data → code) and doubles as a token/cost optimizer: most cases exit early.
- **Adversarial gate on every path** — the hallucination-checker refutes rather than confirms; drift check keeps the answer on the customer's actual complaint.
- **Writeback is a node, not a habit** — N5 is part of the graph, so memory grows on every case by construction.
- **Graceful degradation** — missing metadata server turns live checks into labeled `NOT YET RUN` DBA scripts; the graph still completes honestly.

## The three MCP servers

| Server | Provides | Used by |
|---|---|---|
| Salesforce (claude.ai connector `12c9ae52…`) | case, comments, emails, attachments, knowledge articles, SOSL | intake, version (case side), curator (mining) |
| ADO (`mcp__ado__*`) | WIQL/work items, code search, repo files, PRs, release notes, wiki | intake, version, code, config (consumer check), curator |
| Metadata — Quorum Metadata MCP (`QuorumMetadataMCP/QuorumMetadataMCP.exe --env <ENV>`, ~44 client DEV DBs in dbconfig.json, per-case selection via `QUORUM_METADATA_ENV`) | live schemas, registered SQLs, config tables, batch metadata, read-only data queries | metadata-connector (N0.5), table-analyst, repro, config, data, batch |
