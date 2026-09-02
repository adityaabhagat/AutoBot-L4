# TIPS Issue Knowledge Base (Master Index)

**Product:** TIPS = Salesforce `Product_list__c = 'My Quorum TIPS'` (~9,300 closed cases as of 2026-06-11; ~1,540 actionable: Software Defect 853 + Application Configuration 603 + ChangeConfig 85)
**Purpose:** Route a new TIPS case to the right skill fast. Built by mining resolved Salesforce cases + cross-referencing Azure DevOps.

> **How to use:** Match the case's symptom/keyword below → open the linked skill → follow its Quick Triage + Decision Tree. Or search everything at once: `python "..\Mid L4 Assistant\kb.py" search "<symptom>"`.

---

## 1. Symptom → Skill Lookup

| If the case mentions… | Go to |
|---|---|
| Facility Batch Job failing (MEASUREMENT → ALLOCATE → SETTLE → POSTRESULT), allocation group / Volume Assembly Rule, PDA submission/meter split, PPA approve/un-approve, imbalance not calculating | [SKILL_TIPS_Allocations_PPA_Imbalance.md](SKILL_TIPS_Allocations_PPA_Imbalance.md) |
| Job stuck/hung, QPEC restart, rerun won't run, duplicate TRNX_ID / PK violation, purge/archive, import file paths | [SKILL_TIPS_Batch_Processing.md](SKILL_TIPS_Batch_Processing.md) |
| CAW (Customer Activity Website): external user setup, OKTA/QCloud login, CAWDATA replication, shipper visibility, impersonation | [SKILL_TIPS_CAW.md](SKILL_TIPS_CAW.md) |
| FlowCal/GMAS import, ESuite/TIPS API, Evolution QPTM↔TIPS PTR/imbalance overlay, Integration Platform failed events, SAP BA sync, QQM/BusinessObjects, SFTP | [SKILL_TIPS_Integration_DataSync.md](SKILL_TIPS_Integration_DataSync.md) |
| Invoice doubled/missing data, PPA reversal wrong, statement/invoice group config, rates rounding/decimals, escalation schedules, fees not populating (CCT/UOM) | [SKILL_TIPS_Invoice_Billing_Rates.md](SKILL_TIPS_Invoice_Billing_Rates.md) |
| Contract time-slice/effective-date overlap, CCT, Contract Meter List, meter definition/split, company/org maintenance, QTRAN_PAYSTATION build failures, gas-lift duplication (ASSCGLM) | [SKILL_TIPS_Master_Data_Contracts.md](SKILL_TIPS_Master_Data_Contracts.md) |
| Volume/analysis imports (FLOWCAL/QIMPVOLD/spreadsheet), WHMEASIMP, Measured Volumes screen, truck tickets, TRNX_ID exhaustion, INACCUM/INGASACCTG inventory | [SKILL_TIPS_Measurement_Ticketing.md](SKILL_TIPS_Measurement_Ticketing.md) |
| Report/statement blank, doubled, mis-totaled, won't print/distribute; regulatory/severance tax (TX/OK/ND/NM/KS/CO); Exago/Interactive Reports; Post Results | [SKILL_TIPS_Reporting_Statements.md](SKILL_TIPS_Reporting_Statements.md) |
| Citrix/QCloud login, environment refresh fallout, QPEC services/scheduler, grid/picklist/code-table metadata, global config keys, QEMAIL, Flowcal widget, patch tracking | [SKILL_TIPS_System_Configuration.md](SKILL_TIPS_System_Configuration.md) |
| Settlement run/statement values, revenue distribution, GL/journal entries, JIB, annual gas equalization, SETTLEMGR, QTRAN_SETTLE_* | [SKILL_TIPS_Settlement_Revenue_Journal.md](SKILL_TIPS_Settlement_Revenue_Journal.md) |
| User access/login, roles & security groups, object privileges, Business Associate (BA) setup/name change, external/TPA provisioning | [SKILL_TIPS_Security_UserAdmin.md](SKILL_TIPS_Security_UserAdmin.md) |
| Nomination entry/import, confirmations, scheduling, availability/wellhead scheduling, forecasting | [SKILL_TIPS_Nominations_Scheduling.md](SKILL_TIPS_Nominations_Scheduling.md) |
| Widget missing/not editable, dashboard blank, context selector, works-in-Classic-not-Web, "no company set" | [SKILL_TIPS_UI_Widgets.md](SKILL_TIPS_UI_Widgets.md) |
| Case has category All/Other/none — check the cross-category sweep | [SKILL_TIPS_Uncategorized_Sweep.md](SKILL_TIPS_Uncategorized_Sweep.md) |
| Which module owns this? repo/table orientation | [SKILL_TIPS_Modules.md](SKILL_TIPS_Modules.md) |
| Daily queue triage / SLO | [SKILL_Queue_Prioritization.md](SKILL_Queue_Prioritization.md) |
| Config key behavior (QPTM & TIPS) | `..\Mid L4 Assistant\CONFIG_REFERENCE.md` |

---

## 2. Coverage Map (skill-build status by category group)

| Category group (raw `Case_Category__c` values) | Closed | Actionable mined | Status |
|---|---|---|---|
| Reporting + Ad Hoc + Regulatory + Gas Statements + Statement Gen + Post Results | 1,945 | 354 | ✅ SKILL_TIPS_Reporting_Statements.md |
| System Configuration + Installation + Environment Issue | 1,051 | 255 | ✅ SKILL_TIPS_System_Configuration.md |
| Uncategorized (All / Other / null) | 1,336 | mined by keyword | ✅ SKILL_TIPS_Uncategorized_Sweep.md |
| Allocations + Allocation Maintenance + PPA Framework + Imbalance(s) | 962 | ~200 | ✅ SKILL_TIPS_Allocations_PPA_Imbalance.md |
| Batch Job Submittal + Processing + Maintenance + Purge/Archive | 590 | ~150 | ✅ SKILL_TIPS_Batch_Processing.md |
| Integration + DataSync + Integration Platform + EDI + eSuite + QQM + GPEX | 563 | ~140 | ✅ SKILL_TIPS_Integration_DataSync.md |
| Master Data + Company + Meter Admin + Contract Maintenance | 397 | ~100 | ✅ SKILL_TIPS_Master_Data_Contracts.md |
| CAW | 311 | ~80 | ✅ SKILL_TIPS_CAW.md |
| Measurement + Volumetric + Ticketing + Inventory + CO&O | 299 | 66 | ✅ SKILL_TIPS_Measurement_Ticketing.md |
| Invoice(s) + Billing + Rates | 280 | ~80 | ✅ SKILL_TIPS_Invoice_Billing_Rates.md |
| User Interface + Dashboard/Widgets + Design Studio | 142 | ~40 | ✅ SKILL_TIPS_UI_Widgets.md |
| Settlement + Revenue + Journal + Annual Equalizations | 577 | mined | ✅ SKILL_TIPS_Settlement_Revenue_Journal.md |
| Security + Business Associates | 519 | mined | ✅ SKILL_TIPS_Security_UserAdmin.md |
| Nominations + Confirmations + Scheduling + Wellhead + Forecasting | 344 | mined | ✅ SKILL_TIPS_Nominations_Scheduling.md |

---

## 3. Cross-cutting TIPS patterns (check on every case)

1. **TRNX_ID exhaustion/duplication is a product-wide defect family** — duplicate TRNX_IDs in `QTRAN_PAYSTATION` break CTRMTR/settlement; orphan-delete scripts recur (ADO #1718964, #1698080, #1709987, #1773003). If a batch job fails on a PK violation, check TRNX_ID first.
2. **Contract/meter time-slice overlaps surface downstream** — master-data effective-date overlaps show up as allocation zeroes, paystation build failures, settlement errors. Trace back to QCM/CCT/CML setup before blaming the failing step.
3. **Web vs Classic parity** — same as QPTM: myQuorum Web screens diverge from Classic; "works in Classic, fails in Web" = parity bug.
4. **Post-refresh drift** — after UAT/DEV refreshes: `ESUITE.QARCH_CTRL_CONNECT_INFO` re-pointing, EMAIL_* keys, impexp paths still on PRD, scheduler jobs. A wave of weird env-specific failures right after a refresh is almost always this.
5. **Evolution (QPTM↔TIPS) sync** — Midstream clients (ETP/ENT etc.): PTR overlay, WHMEASIMP, imbalance overlay defects cross product boundaries. Coordinate with the QPTM skills (`..\Mid L4 Assistant\SKILL_Allocations.md` §7, `SKILL_Integration_Processing.md` §9).
6. **Patch-delivery noise** — ~55 "Software Defect" System Configuration cases are just "Patch N on YYYY.MM" delivery vehicles with no symptom content. Don't mine/treat them as defects; follow their linked cases.
7. **Root-Cause triage first** — same as QPTM: `Software Defect`/`Application Configuration`/`ChangeConfig` → real investigation; `Training`/`Customer Error` → expected-behavior answer; `User Administration Request`/`Database Refresh Request` → ops runbook.
8. **Cluster on TIPS vocabulary** — QTRAN_*, QRPTS_*/QPOST_*, QARCH_*, CAW/CAWDATA, QPEC, FBJS, CTRMTR, SETTLEMGR, WHMEASIMP, INACCUM, ASSCGLM, QIMPVOLD, Exago — not generic English.

---

## 4. Standard data sources

- **Salesforce:** the Salesforce connector (`soqlQuery`). TIPS filter: `Product_list__c = 'My Quorum TIPS'`. Fix detail lives in `Description` + `Resolution__c` (often thin — ~20% empty; say so rather than guess).
- **Azure DevOps:** org `QuorumSoftware`; connection details in [CONNECTION_CONFIG.md](CONNECTION_CONFIG.md). TIPS repos: `IPF.TIPS.*`, `Quorum.TIPS.Crude.*`, client-prefixed `ACL/ACP/IAC.TIPS.*` — full catalog in `..\Mid L4 Assistant\REPO_INVENTORY.md`.
- **Vector KB:** `python "..\Mid L4 Assistant\kb.py" search "<symptom>"` — indexes both projects + cached code.
- **SF knowledge articles:** `..\Mid L4 Assistant\SF_KNOWLEDGE_ARTICLES.md`.

---

*Index created 2026-06-11, completed 2026-06-13 — all 14 TIPS category groups mined (~5.5M tokens of case analysis across two runs). 15 SKILL_TIPS_*.md files (incl. SKILL_TIPS_Modules). Coverage map fully ✅.*
