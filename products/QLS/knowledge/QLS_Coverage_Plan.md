# QLS Coverage Plan — Skill-Mining Survey

> Survey date: 2026-09-02 · `Product_list__c = 'My Quorum Land'` · ALL history, no date filter.
> Source: aggregate SOQL (4 queries) + 4 subject-sample pages (LIMIT 25) + ADO area-path discovery.
> Purpose: size the skill groups so 8–14 groups cover ~90% of ACTIONABLE volume before the mining run.

## Headline numbers

| Metric | Value |
|---|---|
| Total QLS cases | **14,538** |
| Actionable (`Root_Cause__c` in Software Defect + Application Configuration) | **2,570** (17.7%) |
| — Software Defect | 1,063 |
| — Application Configuration | 1,507 |
| Root cause null | 3,499 (24%) — mostly older/cancelled cases |
| Closed volume (Closed + No Response + Deferred) | 13,738 (94.5%) — history is minable |
| `Case_Category__c` null | only 623 (4.3%) — **category field is reliable**; no subject-cluster fallback needed |

## Aggregate: Root_Cause__c (top)

| Root cause | Count |
|---|---|
| (null) | 3,499 |
| Application Configuration | 1,507 |
| Business Change | 1,252 |
| Training | 1,205 |
| Software Defect | 1,063 |
| Customer Error | 1,037 |
| Customer Cancelled | 1,032 |
| Project Debt | 492 |
| No Action Taken | 425 |
| Other | 377 |
| User Administration Request | 304 |
| Hardware/Software Change | 299 |
| Cloud Outage | 252 |
| Platform / HW-SW Env Change | 197 + 197 |
| Performance | 166 |
| (long tail: packaging issues, licenses, deployment, upgrades…) | <165 each |

## Aggregate: Status

Closed 11,448 · Closed - No Response 1,966 · Closed - Deferred 324 · New 170 · Pending Quorum 130 · Complete-Pending Customer Review 126 · Pending Customer 80 · In Review 77 · Complete-Pending Delivery 72 · In Development Queue 69 · In Progress 56 · Development In Progress 20.

## Category landscape (155 raw values → 14 groups)

`Case_Category__c` has three naming eras that must be merged when mining: bare names ("Payments"), `QLS - Agreement – <tab>` era, and `QLA - <module>` / `QGIS - <module>` prefixed values. Group by symptom family, not by raw picklist value.

## Proposed skill groups (ranked by actionable volume)

Actionable = Software Defect + Application Configuration. Sum over groups = **2,375 / 2,570 = 92.4%** of actionable volume.

| # | Group | Est. cases (all) | Actionable | Raw categories folded in |
|---|---|---|---|---|
| 1 | Payments & Financial Processing | 1,773 | 308 | Payments, Payment, QLS - Agreement – Payment, Payment Processing, Manual Payments, QLS - Manual Payment Setup, Manual Payment Setup, QLS - Create Manual Payment Detail, Financial Detail, QLS - Financial Detail, Lease Cost, QLS - Lease Cost, Journal Entries, Financial History, Cost Center |
| 2 | Agreement Header, Search & Lifecycle | 2,172 | 295 | Agreement Detail, QLS - Agreement – Agreement/Subdivision Header, Agreement / Subdivision Header, Agreement Search, QLS - Agreement Search, Agreement Summary, Agreements, Copy Agreement, QLS - Copy Agreement, Delete Agreement, QLS - Delete Agreement, All |
| 3 | eCalendar & Obligations | 1,125 | 275 | eCalendar, eCalendar (Legacy), Calendar, QLS - Calendar, Obligations, QLS - Agreement – Obligation, Obligation Information, Electronic Notification |
| 4 | Legal Description, Acreage & Depth | 1,471 | 222 | Legal Description, QLS - Agreement – Legal Description, Legal Block Description, Acreage, QLS - Agreement – Acreage, Depth, QLS - Agreement – Depth, Aliquot, Chain of Title, QLS - Agreement – Chain of Title, Undivided Interest, Tract Relations |
| 5 | Reports, QQM & Widgets | 1,288 | 196 | Reports, QQM, Widgets, Dashboard / Widget, Agreement Data Sheet, QLS - Agreement Data Sheet (ADS) |
| 6 | Integration & Financial Export (SAP/AFIS/PUBBA) | 1,005 | 172 | Integration, Data Loading / Export, Agreement Data Importer |
| 7 | QGIS / Mapping & Polygen | 503 | 163 | all `QGIS - *` values, Polygen, Maps, Web Map, Map Status, Layers, Feature Class / SDE, Transaction Models, Esri Framework, Spatial Search, Grid Source Management, Agreement Linker |
| 8 | Participation, Organization & BA | 646 | 149 | Participation, QLS - Agreement – Participation, Organization, QLS - Agreement – Organization, Additional Part(y/ies), QLS - Agreement – Additional Party, Business Associate / BA Contact, QLS - Business Associate (BA), Names and Addresses, DOI Creation |
| 9 | QLA (Land Administration web suite) | 384 | 134 | QLA - Agreements, QLA - Payments, QLA - Integration, QLA - Tasks, QLA - Projects, QLA - Contacts, QLA - Parcels, QLA - Validation |
| 10 | Dates/Documents, Provisions & Notes | 611 | 112 | Dates and Documents, QLS - Agreement – Date and Document, Date and Document, Provisions, Provision, QLS - Agreement – Provision, QLS - Notes/Remarks, Documents, Images |
| 11 | Related Records & Cross References | 369 | 98 | Cross Reference(s), QLS - Agreement – Cross Reference, Related Agreements/Wells/Pipelines, QLS - Agreement – Related Well/Agreement/Prospect/Pipeline/Non Interest Related Well, Prospect, Non-Interest Related Wells, Related Asset/Facilities/Project/Prospect |
| 12 | Security & Access | 913 | 94 | Security, System Manager, SalesForce Admin Tasks |
| 13 | Batch Processes & Mass Changes | 352 | 87 | QLS - Batch Process, Batch Process, Mass Changes, QLS - Mass Changes |
| 14 | Configuration & Code/Decode Maintenance | 254 | 70 | QLS - Configuration Settings, Code Table Navigator, QLS - Code/Decode Value Maintenance, Code/Decode Value Maintenance |

**Not skill targets** (remaining ~7.6% of actionable): null category (57), Performance (43), Hosting (34), Hotfix Request (29 — meta), Platform/UX (14), Land Web Screens (5), Activity Progress (6) — environment/meta families, route to Cloud Ops or handle case-by-case.

## Per-group mining keywords (SOQL `LIKE` seeds, spotted in real subjects)

| Group | Distinctive keywords |
|---|---|
| Payments & Financial | `Create Payment Detail`, `Payment Balancing`, `check run`, `Pay/Drop`, `Payee`, `manual payment`, `Financial Detail`, `Lease Cost`, `Intercompany Billing`, `payment type` |
| Agreement Header/Search | `Agreement Search`, `Subdivision Header`, `Copy Agreement`, `Delete Agreement`, `Property Status`, `Agreement Navigator`, `AGM ` |
| eCalendar & Obligations | `eCal`, `eCalendar`, `Pull Events`, `Route Maintenance`, `Desk`, `ECALWF`, `Task List`, `Unapproved Events`, `Working Months`, `UBT` |
| Legal Desc/Acreage/Depth | `Legal Description`, `Acreage`, `Depth`, `Aliquot`, `Chain of Title`, `Tract`, `LTS Subject` |
| Reports/QQM/Widgets | `QQM`, `Web Intelligence`, `BIAR`, `widget`, `Agreement Data Sheet`, `payment forecast report` |
| Integration/Fin Export | `AFISCRTAE`, `AFIS`, `SAPINTJE`, `PUBBA`, `QLSURLIMP`, `UPSFINEXP`, `Positive Pay`, `Bank Submission`, `DATAPUBLISH`, `AP157`, `QCFS Import`, `CC INTERFACE` |
| QGIS/Mapping | `Polygen`, `QGIS`, `ArcMap`, `Agreement Linker`, `Web Map`, `SDE`, `Feature Class`, `Plat` |
| Participation/Org/BA | `Participation`, `Additional Party`, `Business Associate`, `Payee Selection`, `Names and Addresses`, `Organization` |
| QLA | `QLA`, `QLARIS`, `Parcel`, `QLA Payments` |
| Dates/Docs/Provisions | `Provision`, `Date and Document`, `document type`, `Remarks`, `provision model` |
| Related/XRef | `Cross Reference`, `Related Well`, `Related Agreement`, `Prospect`, `Non-Interest` |
| Security & Access | `security`, `role`, `permission`, `System Manager`, `Batch Security`, `user access` |
| Batch/Mass Changes | `batch process`, `Mass Change`, `scheduled process`, `ECALWFSCRUB`, `Reposcrub`, `Run_Other_SQL`, `Roll Date` |
| Config/Code-Decode | `Code Table Navigator`, `code/decode`, `decode value`, `Configuration Settings`, `QARCH_CNFG_CTRL` |

## Vocabulary seeds (from subject sampling + ADO bug bodies)

- **Batch/process codes:** QLSURLIMP, UPSFINEXP, AFISCRTAE (QLS→Upstream AP financial export), ECALWFSCRUB (workflow scrubber), SAPINTJE, DATAPUBLISH, Positive Pay, Bank Submission, Reposcrub, Run_Other_SQL_1, Roll Date scheduled process, Pull Events (eCalendar).
- **Tables/columns (Oracle, LIS schema):** `lis.participants` (`PRTP_KEY_EXT`, `BA_1099_IND`), `LAND_RESEARCH`, `AFIS_TEMPLATE`, `QARCH_CNFG_CTRL` (config control, JSON in metadata repos), `GOPL_JEFF_SECTIONS` (client code/decode), `READY_FOR_ECAL_REC_FL`, config key `EnableReadyForRecommendation`, `PayeeEFTCriteria`.
- **Screens:** eCalendar Inbox, eCalendar Task List, Route Maintenance, Desk Maintenance, Create Payment Detail, Payment Balancing, Pay/Drop Authorization, Payee Selection, Agreement Navigator (AN- prefixed screens), Code Table Navigator, Agreement Data Sheet, Function Navigator → Land Financial.
- **Integrations:** PUBBA full sync (BA publish), SAP (CC INTERFACE, check detail job, SAPINTJE JE export), Upstream AP055/AP157 voucher screens via AFISCRTAE, QCFS land-payment import, WMN email notification, QLA→QLS payment integration, Well integration.
- **Error signature seen in defects:** `System.MethodAccessException ... get_NoteControllers` (platform upgrade collateral in QLS Web controllers).
- **QQM = BusinessObjects/Web Intelligence** query tool (BIAR files, Java applet era issues).

## ADO notes

- **Org:** QuorumSoftware. Bugs split across two projects: **`QuorumSoftware`** (bulk of history) and **`Quorum`** (current, PI-based iterations e.g. `Quorum\PI 26.2\26.2.4`).
- **Area paths verified from real bugs:**
  - `QuorumSoftware\Engineering\Land\Committed Backlog` — product-dev bugs (e.g. #1708512, #1693760)
  - `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Land` — L4/maintenance escalations (e.g. #1702244)
  - `Quorum\North America\Upstream\Land RnD` — current escalated maintenance bugs, 2026+ (e.g. #1814672, #1808498)
- **Core repos (project QuorumSoftware):** `Quorum.QLS.Web`, `Quorum.QLS.ServiceCore` (e.g. `QQLSServiceCore_Financial.cs`, `QQLSServiceCore_EcalBatch.cs`), `Quorum.QLS.Metadata`, `Quorum.QLS.Database`, `Quorum.QLS.DataObject`, `Quorum.QLS.ClassicGUI`, `Quorum.QLS.QLandShared`, `Quorum.QLS.Royalties`, `QLS.Batch`; QGIS side: `Quorum.QGIS.ArcGISPro.AddIn`, `Quorum.QGIS.ArcGISPro.ServiceInterface`.
- **Client override repos:** `<CLIENT3>.QLS.Metadata` — confirmed set: AST, BPG, CHV, COP, DOM, ENR, LOD, MUR, NWD, SAV, SRC, XTO (config lives in e.g. `QARCH_CNFG_CTRL.json` under `STANDARD 16.0/`). Matches the `<CLIENT>.QLS.ESuite.Database` lead in PRODUCT.md.
- **Hotfix conventions:** tags `2022.04/2023.04/2024.04/2024.10/2025.04/2026.04 Hotfix (+ Completed)`; branches `hotfix/17.2x.y`. Release train = `YYYY.MM`, so version-issue (G3) checks are viable via tags.
- **Environment naming:** `<CLIENT>_LND_DEV17[HD]_ORACLE` DB naming and `DMBL_HD_DEV17_QLS` HD URLs — QLS runs on **Oracle** with the `lis` schema.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
