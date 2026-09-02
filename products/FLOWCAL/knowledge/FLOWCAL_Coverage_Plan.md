# FLOWCAL Family — Coverage Plan (FLOWCAL · TESTit · PROVEit)

> Survey date: 2026-09-02 · Source: Salesforce aggregate SOQL (ALL history, no date filter) + ADO org `QuorumSoftware`.
> Product_list__c literals surveyed separately: `FLOWCAL`, `TESTit`, `PROVEit`. Skill groups below are UNIFIED across the family, tagged with which literal(s) each covers.

---

## 1. Volume totals (COUNT by Status)

| Literal | Total cases | Closed | Closed - No Response | Closed - Deferred | Open (all other) |
|---------|------------:|-------:|---------------------:|------------------:|-----------------:|
| FLOWCAL | 44,912 | 41,000 | 3,026 | 243 | 643 |
| TESTit  | 16,126 | 15,128 | 908 | 21 | 69 |
| PROVEit | 6,519 | 6,045 | 432 | 13 | 29 |
| **Family** | **67,557** | 62,173 | 4,366 | 277 | 741 |

~98.9% of family history is closed — a deep mining corpus. Open backlog is small (741), concentrated in FLOWCAL (`New` 241, `In Progress` 92, `In Development Queue` 75, `In Review` 71, `Pending Customer/Quorum` 127).

## 2. Root cause distribution (COUNT by Root_Cause__c, top rows)

| Root_Cause__c | FLOWCAL | TESTit | PROVEit | Family |
|---------------|--------:|-------:|--------:|-------:|
| (null) | 24,603 (55%) | 9,335 (58%) | 3,668 (56%) | 37,606 |
| Training | 5,136 | 1,364 | 752 | 7,252 |
| Licenses | 2,342 | 2,299 | 823 | 5,464 |
| **Software Defect** | **1,734** | **264** | **117** | **2,115** |
| Customer Cancelled | 1,576 | 349 | 123 | 2,048 |
| **Application Configuration** | **1,534** | **425** | **131** | **2,090** |
| Platform | 1,019 | 105 | 47 | 1,171 |
| No Action Taken | 900 | 213 | 94 | 1,207 |
| Hardware/Software Change | 847 | 526 | 214 | 1,587 |
| Customer Error | 758 | 260 | 102 | 1,120 |
| Not in Product Plan | 745 | 78 | 47 | 870 |
| User Administration Request | 658 | 166 | 43 | 867 |

**Actionable (Software Defect + Application Configuration): FLOWCAL 3,268 · TESTit 689 · PROVEit 248 = 4,205 family-wide.**
Caveat: Root_Cause__c is null on ~56% of history, so 4,205 is a floor; the actionable rate among *coded* cases is ~14-16%. Mining queries should not filter on Root_Cause__c alone — use category + keyword.

## 3. Case_Category__c distribution (top categories, all root causes)

Field is well-populated (null: FLOWCAL 4,333 = 9.6%, TESTit 3,151 = 19.5%, PROVEit 1,447 = 22.2%) — no subject-clustering fallback needed. 210 distinct (literal, category) pairs; top rows:

| Category | FLOWCAL | TESTit | PROVEit |
|----------|--------:|-------:|--------:|
| Imports / Exports | 4,326 | 1,048 | 298 |
| Reports | 4,014 | 642 | 349 |
| Licensing | 1,934 | 3,227 | 1,176 |
| Database | 3,018 | 719 | 235 |
| Services | 2,766 | 267 | 30 |
| Installation / Upgrade | 2,492 | 2,093 | 1,136 |
| Meter | 2,370 | 79 | 45 |
| Calculations | 1,687 | 112 | 111 |
| Liquids | 1,602 | — | — |
| CrypKey | 1,254 | 1,281 | 233 |
| Flow Data | 1,278 | — | — |
| Help | 1,280 | 316 | 240 |
| Exceptions / Messages | 1,104 | 18 | — |
| Source Quality | 1,080 | 5 | — |
| Closing / PPA's | 1,066 | — | — |
| FLOWCloud | 972 | — | — |
| Security | 915 | 279 | 66 |
| Environment | 830 | 150 | 60 |
| Tools | 708 | — | — |
| Configuration | 644 | 31 | 1 |
| Interface | 535 | 273 | 90 |
| Tasks | 3 | 529 | 339 |
| Schedules / Schedule Definitions | — | 291 | — |
| Locations | 494 | — | 5 |
| Rollup Viewer | 462 | — | — |
| Utilities | 456 | 155 | — |
| Application Configuration | — | 111 | 45 |
| Hardware / Wiring | — | 4 | 109 |
| Provers | 2 | 6 | 79 |

## 4. Actionable-by-category (Root_Cause__c IN ('Software Defect','Application Configuration'))

Top actionable rows (family = 4,205):

| Category | FLOWCAL | TESTit | PROVEit |
|----------|--------:|-------:|--------:|
| Reports | 357 | 46 | 26 |
| Imports / Exports | 304 | 61 | 20 |
| Services | 299 | 21 | — |
| Database | 183 | 50 | 6 |
| Calculations | 158 | 9 | 1 |
| Installation / Upgrade | 92 | 108 | 57 |
| FLOWCloud | 122 | — | — |
| Meter | 113 | 1 | — |
| Flow Data | 111 | — | — |
| Configuration / App Config | 111 | 45+20 | 14+7 |
| Exceptions / Messages | 101 | — | — |
| Environment | 90 | 32 | 4 |
| Closing / PPA's | 84 | — | — |
| Liquids | 78 | — | — |
| Source Quality | 64 | — | — |
| Tools | 61 | — | — |
| Meter Imports | 56 | — | — |
| Security/Auth/Access (combined) | ~143 | ~19 | ~10 |
| Licensing + CrypKey | 87 | 68 | 24 |
| Integration (all flavors) | ~82 | ~65 | ~1 |
| Tasks / Performing Tasks / Schedules / Devices / Provers | — | ~53 | ~38 |
| Interface / User Interface | 47 | 37 | 15 |

---

## 5. Proposed skill groups (14 unified groups ≈ 90% of actionable volume)

Sizing basis: actionable counts from §4 (floor values); est_cases = family-wide total in the symptom family regardless of root cause. Keywords are distinctive strings for SOQL `Subject/Description LIKE '%kw%'` mining — process/exe names, error codes, screen names, not plain English.

| # | Group | Covers | Est. cases (family) | Actionable | Mining keywords |
|---|-------|--------|--------------------:|-----------:|-----------------|
| 1 | Imports & file formats (CFX/GQ/ticket/SCADA import failures, import drivers) | FLOWCAL, TESTit, PROVEit | ~6,150 | ~475 | `CFX`, `FcSrvFileImport`, `GQ Text`, `TIDX`, `PIDX`, `import driver`, `file import`, `Scout file` |
| 2 | Reports & report scheduling (missing data on reports, report service, Rollup Viewer) | FLOWCAL, TESTit, PROVEit | ~5,470 | ~465 | `FcSrvReports`, `BLM Analysis`, `report preview`, `Rollup Viewer`, `Crystal`, `report schedul` |
| 3 | Windows services, rollups & transaction queue (service down/stuck/restart) | FLOWCAL (+TESTit services) | ~3,125 | ~345 | `FcSrv`, `Meter Rollup`, `Location Rollup`, `FcSrvTrans`, `Transaction Queue`, `service restart`, `Auto Estimate`, `FcSrvGQTrans` |
| 4 | Installation / upgrade / environment / deployment | FLOWCAL, TESTit, PROVEit | ~7,005 | ~420 | `upgrade`, `installer`, `installation`, `10.9`, `3.18`, `9.19`, `ShowCFX`, `new environment`, `migration` |
| 5 | Licensing & CrypKey (site keys, license transfer, authorization errors) | FLOWCAL, TESTit, PROVEit | ~9,105 | ~180 | `CrypKey`, `site key`, `license transfer`, `authorizing`, `license count`, `authorization code` |
| 6 | Database & performance (Oracle/SQL Server, partitioning, purge, db errors) | FLOWCAL, TESTit, PROVEit | ~4,130 | ~260 | `_fc_db_error`, `Oracle`, `SQL Server`, `partitioning`, `tablespace`, `purge`, `database refresh` |
| 7 | Calculations, gas quality & measurement standards (gas/liquids, GQ apply) | FLOWCAL (+TESTit/PROVEit calc) | ~4,900 | ~365 | `AGA`, `GPA 2172`, `API 11`, `heating value`, `HEATING_VALUE`, `CTL`, `BTU`, `specific gravity`, `CALCit`, `recalc` |
| 8 | Meter data editing, flow data, closing & PPA (Volume/Meter Editor, estimates, month close) | FLOWCAL | ~4,800 | ~345 | `Volume Editor`, `Meter Editor`, `EEFFACE`, `periodic record`, `edit reason`, `PPA`, `prior period`, `unclose`, `estimate` |
| 9 | Security, authentication & access (OKTA, Citrix, access lists, logins) | FLOWCAL, TESTit, PROVEit | ~1,620 | ~170 | `OKTA`, `Citrix`, `access list`, `login failed`, `log in`, `password reset`, `Secure Gateway`, `RO user` |
| 10 | FLOWCloud & hosted operations (QCloud env down, FTP, portal) | FLOWCAL | ~1,245 | ~130 | `FLOWCloud`, `QCloud`, `FTP`, `hosted`, `PROD`, `UAT`, `customer portal` |
| 11 | Integrations & WebSync (eSuite, QPTM/Xchange, FLOWCAL↔TESTit↔PROVEit sync, API) | FLOWCAL, TESTit, PROVEit | ~730 | ~150 | `WebSync`, `eSuite`, `not sync`, `Integration Platform`, `integration service`, `MuleSoft`, `Xchange`, `API` |
| 12 | Exceptions, validations & messages (Exception Resolver, validation limits, Message NNN) | FLOWCAL | ~1,425 | ~130 | `Message 321`, `Exception Resolver`, `validation`, `exception`, `limits`, `flagged` |
| 13 | Field operations: tasks, schedules, devices & proving runs | TESTit, PROVEit | ~1,720 | ~95 | `proving task`, `prover`, `OMNI`, `CAppDATUtils`, `flow averag`, `schedule recurrence`, `Auto Run`, `run data`, `SVP` |
| 14 | Desktop UI, screens, tools & utilities (grids, editors, FcLoader, Settings Manager, lists, locations) | FLOWCAL, TESTit, PROVEit | ~3,225 | ~240 | `FcLoader`, `Settings Manager`, `Bulk Change`, `List Edit`, `Query Edit`, `grid`, `freeze`, `locations` |

**Coverage check:** groups sum to ~3,770 of 4,205 actionable ≈ **90%**. Residual: `Help` (76 actionable — mostly doc/how-to, route as Expected Behavior), null-category (124), and long-tail micro-categories.

Notes:
- Licensing/CrypKey (#5) is the single biggest raw-volume family (9.1k cases) but mostly `Licenses` root cause (site-key issuance ops, not defects) — the skill should be a fast recipe: CrypKey diagnostics + site key procedure + license transfer steps.
- TESTit actionable volume concentrates in Install/Upgrade (108), Imports (61), App Config (45+20), Integration Services (45), Database (50), Reports (46), UI (37) — groups 4, 1, 11, 6, 2, 14 cover it.
- PROVEit actionable concentrates in Install/Upgrade (57), Reports (26), Tasks/Proving (24+), Imports (20) — groups 4, 2, 13, 1 cover it.

## 6. Vocabulary seeds (from subject sampling + ADO bugs)

- **Error/exception codes:** `EEFFACE` (Meter/Volume Editor open error), `Exception Error occurred in CAppDATUtils` (TESTit/PROVEit launch), `FLOWCAL Message 321` (ticket import failure), `_fc_db_error` log files, exception code `0xc0000092` (FcSrvFileImport2.exe crash, module `CC32C250MT.DLL`), "Value was either too large or too small for a Decimal" (PROVEit OMNI retrieve, `FlowCal.FieldApplications.Classes.Communication.Omni.CCommOmni.RetrieveMassRuns`).
- **File formats:** `.cfx` (Common File eXchange — gas/liquids per-meter data), `.tfx`, GQ text files, `TIDX` (TESTit import), `PIDX` (PROVEit import), Scout files, chart meter files.
- **Service executables (from FC.BoolTox `ServicesRepository.cs`):** `FcSrvFileImport.exe`/`FcSrvFileImport2.exe` (File Import), `FcSrvTrans.exe` (TQ), `FcSrvMtrRollup.exe`, `FcSrvLcnRollup.exe`, `FcSrvCalcMtrRollup.exe`, `FcSrvReports.exe`, `FcSrvCloseData.exe` (Meter Close), `FcSrvLcnCloseData.exe` (Location Close), `FcSrvGQTrans.exe` (Source Apply), `FcSrvAutoEstimate.exe`.
- **Screens/modules:** Volume Editor, Meter Editor, Settings Manager > Services > Service Configuration, Exception Resolver, Rollup Viewer, ShowCFX, CALCit Calculator, FcLoader, FcDataBoss (internal data-load tool used in repro steps), Master Meter Allocation.
- **DB columns spotted:** `HEATING_VALUE_SATB` (dry vs wet HV on source calc).
- **Environment vocab:** Citrix published apps, OKTA groups (`<Client>-PROVEit-RW-UAT` naming), QCloud servers (`QCP*`/`QCU*` hosts), env naming `<CLIENT>_PRD319FLD_TESTIT` / `<CLIENT>_UAT319FLD_PROVEIT`, gMSA service accounts (`svc<CLIENT>Meas<ENV>`), NetScaler LBVS entries for TESTit WebSync WebAPI/WebIDP.
- **Versioning:** FLOWCAL 10.x (10.5.0.14, 10.9.0.1), TESTit 3.x (3.11, 3.16.1, 3.17, 3.18.1), PROVEit 9.x (9.5.1, 9.11, 9.17.1, 9.19.1). ADO port-bug convention: title suffix `(DEV)` / `(R1090 PORT)` for the 10.90 release branch.
- **Field devices:** OMNI 6000 flow computer, SVP controller, provers (expansion coefficients Ga/Gl/Gc, API 12.2 proving calc method).

## 7. ADO notes (org `QuorumSoftware`)

**Area paths (verified from real bugs):**
| Project | Area Path | What lands there |
|---------|-----------|------------------|
| `Quorum` | `Quorum\North America\Measurement` | Triage-level FLOWCAL/TESTit/PROVEit bugs from support |
| `Quorum` | `Quorum\North America\Measurement\Maintenance` | FLOWCAL maintenance bugs (e.g. 1627121, 1710336) |
| `Quorum` | `Quorum\North America\Measurement\Field Apps and API` | TESTit/PROVEit ("Field Apps") + API bugs (e.g. 1807377 Prover coefficient) |
| `QuorumSoftware` | `QuorumSoftware\Engineering\Measurement\Maintenance` | Engineering-side bug copies/ports (e.g. 1808567 DEV, 1808568 R1090 PORT) |
| `myQuorum Cloud` | (various) | Hosting/provisioning/upgrade tickets — useful for FLOWCloud group (#10) |

Bugs frequently reference the source SF case number in the description (`Case Owner - {name}` + `2x-00xxxxxx` pattern) — good join key for mining.

**Repo name patterns (QuorumSoftware project):**
- `FC.*` — FlowCal tooling: `FC.BoolTox` (services admin tool; confirmed FlowCal.* C# namespaces), `FC.DevOps.*`.
- `measurement-client` (~26 MB) — likely the FLOWCAL desktop client monorepo; field apps namespace `FlowCal.FieldApplications.*` (TESTit/PROVEit comms, OMNI) appears in bug stack traces — confirm exact repo during mining (no repo literally named TESTit/PROVEit exists).
- `evs-measurement-*` — next-gen measurement microservices (`-volume-calculation`, `-balancing`, `-summarization`, `-closing`, `-uom`, `-api`).
- `domain-measurement-api`, `domain-measurement-xchange-api` — integration/API layer (group #11).
- `Quorum.Measurement.Wiki` — dev wiki (Desktop-Application/Technical-Architecture.md, Testing guides) — high-value KB seed material.
- `Measurement-PS-Scripts`, `FieldOps.Scada.Import2.0`, `Flowcal.Automation.Azure.Deployment` — ops/import tooling.
- `MFC.*` (`MFC.QGM.*`, `MFC.QCM.*`, `MFC.QEMS.*`, `MFC.ESuite.*`) — myQuorum measurement metadata/reports/database repos (eSuite integration relevant to group #11).

**Code search caveat:** ADO code search over `FlowCal.FieldApplications` mostly surfaces `Quorum.Measurement.Wiki` + `FC.BoolTox`; the core desktop source (C++: `CC32C250MT.DLL` runtime hints at C++ Builder) may not be code-search indexed. Plan on wiki + work-item mining as the primary ADO evidence channel, `repo_file` on `measurement-client`/`evs-measurement-*` as secondary.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Aggregates are point-in-time (2026-09-02); re-run the SOQL in §1-§4 before rebalancing groups.*
