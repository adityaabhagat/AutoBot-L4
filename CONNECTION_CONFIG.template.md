# CONNECTION_CONFIG — template

> Copy this file to `CONNECTION_CONFIG.md` and fill in. `CONNECTION_CONFIG.md` is NEVER indexed by kb.py (filename-based exclusion) and must never be committed or copied into knowledge folders.

## 1. Salesforce server (MCP connector)

- Connector: claude.ai Salesforce connector, tool prefix `mcp__12c9ae52-5751-4da7-b869-607f03acd2a8__`
- Connected at the account level (no per-project config needed). If the prefix changes after reconnecting, update root `CLAUDE.md` + `.claude/agents/intake-agent.md`.

## 2. ADO server

- Native MCP tools `mcp__ado__*` (org `QuorumSoftware`) when available, else the `azureDevOps` server in `.mcp.json`.
- Set the PAT as an environment variable (used by `.mcp.json` and curl fallback):
  - `AZURE_DEVOPS_PAT` = `<your PAT — Code:Read, Work Items:Read/Write, Wiki:Read>`
- REST fallback quick reference:
  - Base: `https://dev.azure.com/QuorumSoftware`
  - Code search: `POST https://almsearch.dev.azure.com/QuorumSoftware/QuorumSoftware/_apis/search/codesearchresults?api-version=7.0`
  - Auth: `curl -u ":$AZURE_DEVOPS_PAT" …`

## 3. Metadata server — Quorum Metadata MCP (CONFIGURED)

Used by: metadata-connector (N0.5), table-analyst, repro-agent, config-investigator, data-investigator, batch-debugger.

- Package: `QuorumMetadataMCP/QuorumMetadataMCP.exe` (in this folder; stdio MCP, .NET self-contained, Windows auth for SQL Server).
- Wired in `.mcp.json` as server `metadata`; tool prefix `mcp__metadata__*`.
- **Environment selection (client + DB)** — the exe binds ONE environment per launch:
  1. Catalog: `QuorumMetadataMCP/dbconfig.json` (~44 DEV environments, naming `<CLIENT3>U_HD_DEV17`, e.g. `EQCU_HD_DEV17` → `EQC_DEV17UPS_QFC`).
  2. Per case/client: set `QUORUM_METADATA_ENV=<env name>` then reconnect the `metadata` server (`/mcp` → reconnect, or restart the session). Default when unset: `ASTU_HD_DEV17`.
  3. The `metadata-connector` agent verifies the binding at graph node N0.5 and asks you for the client + DB when it can't decide.
  4. New client not in the catalog → add an entry to `dbconfig.json` (`type`/`server`/`database`) — get values from the DBA team; never guess servers.
- Oracle env (`QLS_DEV_OLEDB`) needs Oracle client libraries + a real password in dbconfig.json — keep that file out of git and out of knowledge folders (it is not KB-indexed).
- Access level: READ-ONLY for investigation. Data corrections are delivered as scripts, never auto-executed (see `docs/HALLUCINATION_GUARDRAILS.md`). DEV-tier caveat: schema/config findings anchor CONFIRMED claims; client-PRD data-state claims stay INFERRED.
- If unavailable, agents emit their SQL labeled `NOT YET RUN` for DBA execution — the graph still completes.

## 4. Client environment notes

| Client | Product | Env URLs / DB names | Build/version | Notes |
|---|---|---|---|---|
| | | | | |
