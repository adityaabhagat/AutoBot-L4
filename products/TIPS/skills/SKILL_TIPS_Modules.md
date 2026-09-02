# SKILL: TIPS Module & Issue Map

**Use When:** Classifying any TIPS case — to decide which module owns the issue, which repo/tables to look at, and what the usual root causes are.

TIPS = gas & crude **measurement → allocation → contracts/rates → inventory/imbalance → statements/settlements → EDI/reporting**. Below are the modules that generate most L4 cases (themes confirmed from live Salesforce traffic).

---

## Module Map

### 1. Measurement / Meter Definitions
**Symptoms:** "Meter Definition changes in PROD", FLOWCAL → TIPS meter def sync, wrong volumes/energy, missing measurement.
**Source of truth:** Measurement usually flows **from FLOWCAL** into TIPS. A meter-def change in FLOWCAL propagates to IP/eSuite/TIPS.
**Look at:** `Quorum.TIPS.ServiceCore` (measurement import), inbound interface jobs in `Quorum.TIPS.Batch`, meter def tables.
**Common root causes:** unintended meter-def change pushed from FLOWCAL by a QPEC user; effective-date mismatch; UOM mismatch.

### 2. Allocation
**Symptoms:** volumes not splitting correctly across wells/leases/meters/plants, allocation imbalance, re-allocation needed.
**Look at:** allocation services in `Quorum.TIPS.ServiceCore` + `Quorum.TIPS.Batch`; client overrides in `<CLIENT>.TIPS.*`.
**Common root causes:** missing/incorrect allocation rule or theoretical factor; effective-dated config gap; data not posted before allocation ran.

### 3. Inventory & Imbalance
**Symptoms:** "Inventory Issue", "Ending Oil Inventory", "Dry Imbalance Inventory update issues", inventory override files.
**Look at:** inventory roll-forward / balancing logic in `ServiceCore`/`Batch`; inventory tables; imbalance config.
**Common root causes:** out-of-order postings, prior-period adjustment not rolled forward, override file not applied, sign/UOM error.

### 4. Contracts & Rates
**Symptoms:** "Contract Rates Web", "Contractual UOM", wrong fee/rate applied, effective date issues.
**Look at:** contract/rate services in `ServiceCore`; `Quorum.TIPS.Web.Controllers` (Contract Rates screen); rate tables.
**Common root causes:** rate effective date / tier setup, UOM on the contract vs. measurement, missing rate row.

### 5. Statements & Settlements
**Symptoms:** "gas statement generation" memory error / performance degraded, missing values on statement, wrong settlement amount.
**Look at:** statement generation in `Quorum.TIPS.Batch` / `ServiceCore`; `Quorum.TIPS.Reports`; `Quorum.TIPS.DQS.*`.
**Common root causes:** large dataset → memory/timeout (perf), missing config → blank section, allocation/inventory upstream wrong → statement wrong (fix upstream, not the statement).

### 6. Crude — Truck / Marine / Batch Tickets & Terminals
**Symptoms:** truck ticket / batch ticket / meter batch ticket reports, terminal views, crude & water locations, marine/pipeline tickets.
**Look at:** `Quorum.TIPS.Crude.*` and `Quorum.TIPS.CrudeCommon.*` (NOT the gas repos).
**Common root causes:** missing external location setup, ticket-to-contract mapping, scheduling config.

### 7. EDI
**Symptoms:** inbound/outbound EDI messages, partner transmissions failing/rejecting.
**Look at:** `Quorum.TIPS.ServiceCore.EDI`; `Quorum.TIPS.Events` / `Messaging.Publisher`.
**Common root causes:** trading-partner config, message mapping, transport.

### 8. SAP Integration
**Symptoms:** financials/postings to SAP, SAP web service errors.
**Look at:** `Quorum.TIPS.SAP.*` (ServiceCore, Proxies, WebServices) and client `*.TIPS.SAP.*`.

### 9. Web UI / Screens / Org Hierarchy
**Symptoms:** "Organization Hierarchy Error When adding New Row", grid errors, screen won't save.
**Look at:** `Quorum.TIPS.Web.Controllers` + `Quorum.TIPS.Metadata` (grid/screen defs) + `Quorum.TIPS.Validation`.
**Common root causes:** metadata/grid config, validation rule, client metadata override.

### 10. Reports / DQS
**Symptoms:** missing reports, report column requests, data-query views.
**Look at:** `Quorum.TIPS.Reports`, `Quorum.TIPS.DQS.DataSource`, `Quorum.TIPS.DQS.QueryView`, client `*.TIPS.Reports`.

### 11. Environment / Access (usually NOT code)
**Symptoms:** Okta/SSO resets, add user to group/SCADA, UAT/DEV refresh requests, deploy a release package.
**Classification:** almost always **Configuration / operational**, not a defect. Route to access/ops; no code analysis needed.

### 12. Canada-specific
If the client operates in Canada (e.g. AltaGas, NorthRiver, Pembina, Suncor), check `Quorum.TIPS.Canada.*` for region-specific allocation/validation/service overrides.

---

## Classification Quick Rules

- **Access / Okta / refresh / deploy** → Configuration/Operational. No code trace.
- **"changes appeared in PROD" / unexpected data change** → likely Data (often a QPEC user or upstream FLOWCAL push), produce RCA. Check audit/who-changed-what.
- **Statement/report wrong** → check whether the *upstream* allocation/inventory is wrong first; the statement is usually just the messenger.
- **Memory / "performance degraded" / timeout on generation** → perf Defect or data-volume; check batch sizing/queries, not formatting.
- **"cannot save" / validation error on a screen** → `Validation` rule (+ client override) and `Metadata`.
- **Crude keywords** (truck/marine/batch ticket, terminal, water) → Crude line repos.

## Always-do
1. Identify **client code** from the Account (see REPO_REFERENCE.md) and **gas vs crude**.
2. Check the **client repo** for an override before reading base code.
3. For "fix availability", check `Quorum.TIPS.ReleaseNotes` and the linked ADO work item's target release.

> Verify table/class/file names against current code via ADO Code Search before asserting them in a report — this map is a routing guide, not a schema reference.
