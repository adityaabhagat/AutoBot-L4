# SKILL: TIPS — CAW / External Users / Integration / DataSync (ADO Defect Reference)

**Version:** 1.0 | **Created:** 2026-06-14 | **Source:** Azure DevOps TIPS Bugs (Closed/Resolved) | **Product:** My Quorum TIPS (Midstream)
**Functional area:** External-facing surface + system-to-system data movement for TIPS — the **CAW / external-user** web portal & reports, **FLOWCAL ↔ Integration Platform ↔ eSuite/TIPS** measurement integration, **SAP ↔ TIPS** settlement/BA/journal interfaces, **QCM ↔ TIPS** contract/forecasting integration, the **CAWDATA / DataSync** replication processes (`QRMTIPS` → `QRMTIPS_CAW` / `QRMTIPS_CAN`), the **TIPS API Host**, **Exago** Interactive Reports, **QQM** reporting universes, and **QCloud** environment/deployment issues that surface under these.

> **Use When:** an ADO **Bug** (or the SF case behind it) involves: a FLOWCAL/Integration-Platform/eSuite-API meter/sample/quantity transfer failure; a SAP push/pull or journal/BA interface error; the CAWDATA or DataSync replication process erroring or producing stale/missing external data; the TIPS API Host not starting; an Exago / Interactive Reports install/connection problem; a QQM report value mismatch; or an external (producer/shipper/agent) user seeing wrong/no data or report-security gaps. For the **SF-case** view of the same area (config recipes, BA-security, Crystal memory) see `TIPS Assitant\SKILL_TIPS_CAW.md`; this skill is the **ADO/engineering** companion — root cause from dev comments, PRs, and fixed-in-build.

> **Evidence base:** WIQL over Bugs Closed/Resolved in `Engineering\Midstream` + `Engineering\Maintenance\Midstream and Transportation`, title-filtered on CAW/CAWDATA/external user/OKTA/QCloud/replication/integration/DataSync/API host/SAP/QQM/Exago. **424 bugs matched**; **~48 deep-read** (description + ReproSteps + full comment thread + linked PRs). Every root cause below cites real ADO Bug IDs and, where present, the linked SF case (`25-01xxxxxx` / `24-009xxxxx`). **IntegrationBuild is empty on essentially every bug** — fixed-in-build is inferred from the **iteration path (YY.NN → 20YY.MM release)** and PR target branches, and is flagged **(inferred — confirm in release notes)**.

> **Classification / overlap caveat:** the Maintenance branch is **mixed QPTM + TIPS**. The title terms here are mostly TIPS-specific, but two terms are heavily polluted and were **manually de-noised**:
> - **"SAP"** matched 56 bugs but most are the substring in **"di-SAP-pear"** (UI fields/grids disappearing) — those are unrelated QPTM/TIPS-Web UI bugs and were **dropped**. Only genuine *SAP interface/integration/journal/BA* bugs are kept.
> - **"external user"** (91) and **"Imbalance"** pull in many **QPTM pipeline** items (RFS, Nomination Submission, Capacity Release, prearranged bids, Late Nomination Rule, term extension). Those are **QPTM, not TIPS**, and were dropped; only TIPS report-security / TIPS CAW-report items are kept.
> - **"Exago"** (117) is dominated by the one-time **Exago 2020.03 Release Testing** regression wave (~70 near-identical query-screen test defects). Those are summarized as one historical cluster, not enumerated.
> - **QCloud** (22) is mostly **infra/Cloud-Ops** (deployment, outages, app-pool) spanning products — kept only as a triage pointer, not engineering defects.

---

## TABLE OF CONTENTS
1. [Quick Triage](#1-quick-triage)
2. [Decision Tree](#2-decision-tree)
3. [Cluster A — CAWDATA / DataSync replication process errors](#3-cluster-a)
4. [Cluster B — TIPS API Host won't start (MSSQL) + the null-connection-type conflict](#4-cluster-b)
5. [Cluster C — FLOWCAL ↔ Integration Platform ↔ eSuite/TIPS integration](#5-cluster-c)
6. [Cluster D — SAP ↔ TIPS interfaces (settlement / BA / journal / PGAS)](#6-cluster-d)
7. [Cluster E — QCM ↔ TIPS contract & forecasting integration](#7-cluster-e)
8. [Cluster F — External-user TIPS reports: security & performance](#8-cluster-f)
9. [Cluster G — Exago / Interactive Reports install, connection & config](#9-cluster-g)
10. [Cluster H — QQM reporting universe / query value mismatches](#10-cluster-h)
11. [Cluster I — QCloud environment / deployment (infra, triage pointer)](#11-cluster-i)
12. [Fix-Version Matrix](#12-fix-version-matrix)
13. [Diagnostic Pointers](#13-diagnostic-pointers)
14. [Escalation Guidance](#14-escalation-guidance)

---

## 1. Quick Triage

| Symptom (case/bug says) | Likely cluster & root cause | First check |
|---|---|---|
| CAWDATA / SPAWNCAW step errors in facility/company batch; external reports show no/stale data | **A** — `QARCH_DS_SRC_SYSTEM_SCHEMA` code table is env-specific/outdated, or `TIPSDSDataHelper` `.NET connection type` not NULL | Connection Information screen + `QARCH_DS_SRC_SYSTEM_SCHEMA` (§3) |
| "CAWDATAFS" / "CAW Data Replication Full Sync" job errors; external users see data only up to an old gas day | **A** — full-sync failing; same DataSync connection/schema cause | Run CAWFULLSYNC, read batch message log (§3) |
| **TIPS API Host won't start** after upgrade/refresh (MSSQL), `KeyNotFoundException` in `GetDatabaseVendor` | **B** — `DB_CON_STR_TYPE` NULL vs SQL conflict between API Host (needs value) and CAWDATA (needs NULL); APIHost.config not getting data-providers section | `TIPSDSDataHelper` `DB_CON_STR_TYPE`; APIHost.config (§4) |
| FLOWCAL meters/samples/quantities not transferring; "StoreEntity", TimeoutRejectedException, deadlock | **C** — IP↔eSuite API intermittent connection/timeout/deadlock; large bulk pushes | IP activity logs; retry logic; ESuite API trigger join (§5) |
| FLOWCAL integration **widget error** ("Unable to create access token" / generic error) | **C** — API not enabled for client, or no open billing accounting date; needs config toggle | global config / billing date; #1596032 (§5) |
| SAP push/pull fails: "VL push from SAP", BA integration error (ORA-03114), duplicate injection fuel | **D** — missing trigger, dropped Oracle connections, or BA cross-reference/TOC mapping | trigger present? SQLNET.EXPIRE_TIME; BA SAP xref (§6) |
| QCM→TIPS contract/forecasting sync: duplicates, partial sync | **E** — DataSync 5000-char statement limit + meter-suffix duplicates (working-as-designed vs enhancement) | run-summary log on QPEC; SCTRL_MTR_LIST_DTL dupes (§7) |
| External user runs a TIPS report (AL01R / Daily Position / SAVR) → no data / sees others' BAs / hangs | **F** — client-override view stale after core view bump; or report-security view; or report perf (subreports/missing index) | core vs client `*_VW` views; report indexes (§8) |
| Exago / Interactive Reports won't open; "connection ID" error; install needs manual CI edits | **G** — Exago connection ID must be `<MODULE>ExagoDataHelper` on `GLOBAL` metadata layer; installer/config gaps. **Exago deprecated 2025.04** | connection ID + metadata profile; post-refresh (§9) |
| QQM report total doesn't match PGAS/QCT | **H** — QQM universe/derived-table query logic wrong (often legacy formula) | the universe derived table / query (§10) |
| myQuorum slow / app pool / env won't launch / EDI not accepted in QCloud | **I** — infra/Cloud-Ops, not a product bug | QCloud monitoring / Cloud Ops (§11) |

---

## 2. Decision Tree

```
TIPS bug in CAW/External/Integration/DataSync area
│
├─ Is it a BATCH/PROCESS erroring (CAWDATA, SPAWNCAW, CAWDATAFS, DataSync)?           → §3 (A)
│     └─ env-specific config: QARCH_DS_SRC_SYSTEM_SCHEMA outdated OR TIPSDSDataHelper
│        .NET connection type not NULL. Fix per-env (no code); preserve in post-refresh.
│
├─ Is the TIPS API HOST failing to START (esp. MSSQL, after upgrade/refresh)?         → §4 (B)
│     └─ DB_CON_STR_TYPE NULL/SQL conflict. Core fix in APIHost.config/NI→CI
│        (#1617552 then #1762912). Workaround: set DB_CON_STR_TYPE non-NULL to start API.
│
├─ Does FLOWCAL data fail to reach eSuite/TIPS, or the FLOWCAL widget errors?         → §5 (C)
│     ├─ transfer/StoreEntity/timeout/deadlock → IP↔API connection; retry logic; trigger SEEK
│     └─ widget "access token"/error → API not enabled or no open billing date (config)
│
├─ Is it a SAP interface (push VL, BA sync, journal transfer, PGAS→SAP)?             → §6 (D)
│     └─ missing trigger / dropped Oracle conn / BA-SAP cross-ref / sequence overlap.
│        Often NOT reproducible internally (Merit/Entex-specific) → frequently Rejected/Deferred.
│
├─ Is it QCM → TIPS (contract integration / Forecasting DataSync)?                    → §7 (E)
│     └─ 5000-char sync statement limit / meter-suffix "duplicates" (mostly by-design)
│
├─ Is an EXTERNAL USER getting wrong/no/slow data on a TIPS report?                   → §8 (F)
│     ├─ no data after upgrade → client-override view didn't follow a new CORE view (VW2→VW3)
│     ├─ sees BAs not theirs → report param picklist not honoring BA-tab security
│     └─ hangs/too slow → Crystal subreports re-running query; add DB index; rewrite w/o subreports
│
├─ EXAGO / Interactive Reports install/connect/config?                               → §9 (G)
│     └─ connection ID = <MODULE>ExagoDataHelper, metadata profile GLOBAL; installer gaps.
│        Feature DEPRECATED in 2025.04 → many such bugs Rejected "won't HF".
│
├─ QQM report value wrong vs PGAS/QCT?                                                → §10 (H)
│     └─ universe/derived-table query logic; BI Engineering owns universe change.
│
└─ Portal slow / won't launch / EDI / outage in QCloud?                               → §11 (I) Cloud Ops.
```

---

<a name="3-cluster-a"></a>
## 3. Cluster A — CAWDATA / DataSync replication process errors

**Bugs:** #1427530 (UTG, Verified), #1534309 (DTM, 22-00272601), #1725660 (HPE, 25-01015982 CAWDATAFS), #137105 (HPE cache warnings, Ready-for-QA), #111615 (Enable, same cache warnings), #210494 (HVM), #280265 (HPE PROD), #208442 (ETP) | **SF:** 22-00272601, 25-01015982
**Count:** ~9 (one of the best-documented, highest-confidence engineering clusters).

### Symptom
The **CAWDATA / SPAWNCAW** step inside Facility or Company Batch jobs errors out (or just throws cache-suggestion warnings), and transactional data (allocation, invoice, imbalance, settlement) is **not written to the `QRMTIPS_CAW` database** — so external users see **no data or stale data** (e.g. report data stops at an old gas day). The CAW Data Replication Full Sync job (**CAWDATAFS / CAWFULLSYNC**) also errors.

### Root cause (from dev comments)
Two distinct, repeatedly-confirmed causes:
1. **`QARCH_DS_SRC_SYSTEM_SCHEMA` is environment-specific and gets out of date.** On #1427530 the dev (Jon Shuck) reproduced it by debugging: *"Looks like it's referencing an outdated code table … updated the code table and it looks like it's getting further … completed successfully after the changes."* It must match the **Connection Information Screen** values. This is **NOT a code change** — it is corrected **manually per environment**, and (per Jennifer Hart) **must be preserved in the env's post-refresh scripts** or a refresh wipes it. Also seen on #1534309 (DTM) where a missing metadata parameter (52003 on the TPFC layer not in the DTM profile) had to be added to the profile + QPECs restarted.
2. **`TIPSDSDataHelper` (the Data Sync connection) `.NET connection type` must be NULL** for CAWDATA to run on SQL Server (Cristina Keeton, on #1534309: *"this .NET connection type needs to be set to NULL for the TIPSDSDataHelper, and then the CAWDATA process completes successfully."*). See the sharp interaction with the API Host in **§4** — nulling this breaks the API Host.
3. The **cache-suggestion warnings** ("Access to cache … not indexed") on the SPAWNCAW step were a genuine (cosmetic) defect, fixed in code (#137105 / #111615 for Enable, merged to AMID) — not the same as the process erroring.

### Fix / fixed-in-build
- **Config fixes (#1427530, #1534309, #1725660):** no core code — per-env correction of `QARCH_DS_SRC_SYSTEM_SCHEMA` / the metadata profile / the NULL connection type; persist in post-refresh. Resolved by Services/Maintenance.
- **Cache-warning code fix (#137105, #111615):** PRs into QFC (Quorum.QFC). Shipped in the 2018.11-era core and forward — **(inferred — confirm in release notes)**; the same fix was merged from Enable to AMID.

### Workaround
Set `TIPSDSDataHelper` .NET connection type to NULL; align `QARCH_DS_SRC_SYSTEM_SCHEMA` to the Connection Information screen; re-run CAWDATA. For CAWDATAFS, re-run **CAWFULLSYNC** after correcting the connection.

---

<a name="4-cluster-b"></a>
## 4. Cluster B — TIPS API Host won't start (MSSQL) + the null-connection-type conflict

**Bugs:** #1617552 ("2023.04+ TIPS API Host not starting up for MSSQL clients", Acceptance), #1762912 ("2025 TIPS API Host STILL not starting up for MSSQL clients", Verified), #1763112 ("CAWDATA requires null connection type for SQL", Rejected) | **Linked:** #1537332 (Data Sync test), depends on §3.
**Count:** 3 — tightly linked; the canonical example of "fixing one config breaks the other."

### Symptom
After an upgrade/refresh on **MSSQL** clients the **TIPS API Host service fails to start**, throwing:
`System.Collections.Generic.KeyNotFoundException: The given key was not present in the dictionary` at `Quorum.QFC.Data.QDataUtilityBase.GetDatabaseVendor`. In QCloud this fires environment-monitoring noise and leaves components in STEPERR.

### Root cause (from dev comments)
Collateral from the **SQL driver upgrade SQLNCLI11 → MSOLEDBSQL**. The `TIPSDSDataHelper` connection's **`DB_CON_STR_TYPE`** field is the pivot:
- **API Host requires it to be populated** (e.g. `SQL`) or it can't resolve the DB vendor → won't start.
- **CAWDATA / DataSync requires it to be NULL** (see §3) or the process errors.
These two requirements **directly conflict** (#1763112 is the explicit write-up: *"CAWDATA requires null connection type for SQL … leaving the connection type null could lead to … the TIPS API Host does not start since that is a required field"*).

The "real" fix was to make the **APIHost.config** carry the data-providers section so the host can start *regardless* of the connection field. #1617552 added connection types to the .config; #1762912 found the **NI→CI generation for on-prem clients wasn't populating that change** (APIHost.config from repo ≠ what the installer generates) and added the data-providers / NI config section. #1763112 was then **Rejected** with the conclusion: *"The current correct behavior is to have the .NET Connection Type field blank for the Data Sync connection … This was resolved in #1762912 and #1617552 and is no longer an issue."*

### Fix / fixed-in-build
- **#1617552** — iteration **24.21** → first fix shipped ~**2024.04+** era **(inferred — confirm in release notes)**. PRs into APIHost config repos (multiple, e.g. PR 101376/101533-38).
- **#1762912** — iteration **25.23** → on-prem NI/CI config fix in a **2025 release (likely 2025.10)** **(inferred — confirm in release notes)**; "found in Q testing, no release note." PRs 119244–120862.
- **#1763112** — iteration **26.07**, **Rejected** (no fix; documented correct behavior = NULL).

### Workaround
On a non-starting API Host: set `TIPSDSDataHelper` `DB_CON_STR_TYPE` to a **non-NULL** value (`SQL`) to get the API up; but be aware CAWDATA will then fail until it's nulled again — so apply the **#1762912** code fix (correct APIHost.config) to break the conflict permanently. If the client is below the fixed build, this is a known "remediate after every refresh" chore (Matt Davis: 0.5–2 hrs per env).

---

<a name="5-cluster-c"></a>
## 5. Cluster C — FLOWCAL ↔ Integration Platform ↔ eSuite/TIPS integration

**Bugs (transfer/connection):** #1396175 (deadlock, Verified), #1376390 (TimeoutRejectedException, Rejected), #1376389 (StoreEntity connection, Rejected), #1449303 (API registration deadlock), #1594204 (PML meters end-dated/attributes lost), #1686007 (DTM end-dating), #1665697 (reset REVISION_NUMBER, Verified) | **Bugs (widget):** #1561649 (access token), #1564930 (no open billing date), #1596032 (API not enabled), #1702166/#1717675/#1709057/#1596032 (widget errors) | **Bugs (mapping/data):** #1632769 (Liquid specs), #1638670 (lat/long degree-sign), #1396083/#1396092/#1396552/#1404976 (UTG timeslice/PRES_BASE/LIQCONVRSN fields), #1389538, #1448587, #1449244/#1451773, #1462259/#1461177 (PML BTU/flow fields)
**Count:** the single largest genuine TIPS-integration theme (~25+ bugs). SF links: PML/UTG/DTM/MER/AZR/ClearFork client work.

### Symptom
Meters / samples / quantities / liquid specs **fail to transfer** from FLOWCAL through the **Integration Platform (IP)** to the **eSuite API → TIPS**, with errors like `StoreEntity. Polly.Timeout.TimeoutRejectedException`, `Unable to establish a connection with any endpoint`, SQL **deadlock victim**, or `Input string was not in a correct format`. Or the **FLOWCAL Integration Widget** throws "Error in FLOWCAL Integration Widget / Unable to create access token." Or transferred data is **wrong** (meters end-dated, attributes lost, fields set to 0/NULL, missing liquid columns).

### Root cause (from dev comments / PRs)
- **Intermittent connection/timeout/deadlock (#1376389, #1376390, #1396175, #1449303):** large bulk pushes from FLOWCAL overwhelm the eSuite API; failures are sporadic and **mostly not reproducible internally** → several were **Rejected** once **retry logic** in IP was added and the symptom "fell off." #1396175 (deadlock) had a concrete root cause: the **ESuite update trigger joins TIPS `QVALD_MTR` on `MTR_NO` only**, but that table's PK is `(PLANT_NO, MTR_NO)` clustered → forces a **PK SCAN instead of SEEK** → deadlock. Core DB change applied.
- **API self-registration deadlock (#1449303):** on startup eSuite API calls IP, IP calls back for product info, the API is still mid-startup → 100s timeout. Fixed (PR 76717/76736).
- **Widget errors (#1596032, #1561649, #1564930):** for clients **without the FLOWCAL↔eSuite API enabled**, the widget still calls it and errors — needs a **config toggle**; permanent fix tied to **post-refresh global-config** entries (related #1662541). #1564930 = no open billing accounting date set for the company plant.
- **Data-mapping defects (#1632769, #1638670, #1396083/92, etc.):** eSuite staging table missing **liquid-spec columns**; **degree-sign in lat/long** broke parsing (error message improved); various STRAN_VOL fields set to 0 instead of NULL / wrong UOM.
- **Unwanted end-dating (#1594204 PML, #1686007 DTM):** IP time-slicing/end-dating meters that should stay open; **not reproducible internally** with provided payloads → both **Rejected/closed** pending a live 3-way (FLOWCAL+IP+TIPS) repro.

### Fix / fixed-in-build
- **#1632769** (Liquid specs) — iter **24.07** → **2024.10** **(inferred)**; PRs 93385/94790/94849 into eSuite API + Postman tests.
- **#1638670** (lat/long error detail) — iter **24.07** → **2024.10** **(inferred)**; PRs 95498-95629.
- **#1449303** (API registration) — iter **22.22** → **2022.10** **(inferred)**.
- **#1396175** (deadlock, trigger/index) — core DB change; **2021.x** **(inferred)**.
- Connection/timeout bugs (#1376389/90) — resolved by **IP retry logic** (not a TIPS code build) → Rejected.

### Workaround
For widget errors on clients without the API: disable the widget / set the config toggle. For transfer failures: rely on IP **retry** (2nd/3rd attempt usually succeeds); re-publish the failed event through IP. For data-correction (e.g. revision number drift) use the spot-fix script pattern (#1665697 reset `REVISION_NUMBER` on eSuite endpoints IP targets).

---

<a name="6-cluster-d"></a>
## 6. Cluster D — SAP ↔ TIPS interfaces (settlement / BA / journal / PGAS)

**Bugs:** #80828 (Wellhead vol rounds to 0, Ready-for-QA), #181869 (MER VL push from SAP, missing trigger), #177327 (PEM SAP Journal Transfer), #176406 (EMP SAP notice-queue PK / sequence overlap), #169609 (Atmos PGAS→SAP not interfacing), #87466 (DOM QCFSEXPORT broke custom SAP interface), #1630108 (MER BA integration ORA-03114, 23-00903800), #1706429 (MER TIPS-SAP integration, 24-00994038, Deferred), #1746787 (CNP/Entex duplicate injection fuel SAPGL, 25-01023017, Rejected), #158720 (OXY Slaughter plant) | **SF:** 23-00903800, 24-00966815, 24-00994038, 25-01023017
**Count:** ~10. **Heavily client-specific (Merit, Entex/CNP, Pembina, EMP, Atmos)** — Merit is essentially the only SAP-settlement customer, so many are **Rejected/Deferred** (can't reproduce internally).

### Symptom
SAP integration jobs fail or produce wrong data: VL push from SAP→TIPS errors (`CommunicationException … ISAPServiceCoreWA`), SAP Journal Transfer doesn't populate `STRAN_SAP_JE_DOC%`, BA integration (SAP→TIPS, ~21,000 BAs) errors part-way (`ORA-03114`), duplicate injection-fuel rows in `CNP_SAP_GL_DTL`, PGAS export not reaching SAP, or settlement integration fails when a wellhead applied volume rounds to 0.

### Root cause (from dev comments)
- **Missing DB trigger (#181869):** VL push failed for lack of trigger `QCTRL_PPA_STMT_REVISED_BIR` in v17 — added to upgrade packages (no hotfix needed).
- **Rounding (#80828):** code checked volume ≠ 0 **before** rounding, then the division **rounded to 0** → integration fails. Code fix (PR 4372).
- **Sequence overlap (#176406 EMP):** SAP date-interface process runs on a different/earlier `QARCH_TRAN_SEQ` track than other notice processes → notice-queue PK collision. Workaround: delete the overlapped record (buys ~100 IDs). Not reproducible → closed.
- **Dropped Oracle connections (#1630108 / #1706429 MER):** `ORA-03114` on large sequential BA pushes; TIPS+LAND share one Oracle server (single point of failure). Suggested mitigation: append `SQLNET.EXPIRE_TIME=10` to server `sqlnet.ora` (server-side keepalive). Could not RCA internally → **Deferred** (Merit-only).
- **BA-SAP cross-reference (#1746787 CNP):** duplicate injection fuel across unrelated BAs at DB level (`CNP_SAP_GL_DTL`) only — suspected **wrong SAP-number cross-references / TOC category** on the BAs. Not RCA'd → Rejected after >3 weeks blocked.
- **QCFSEXPORT change broke DOM custom SAP interface (#87466):** needed new columns on `STRAN_CORE_INTFC` (`INTFC_PROC_ID`). Code/DB fix (PR 5642).

### Fix / fixed-in-build
- **#80828** (rounding) — PR 4372; merged to V17 era **(inferred)**.
- **#181869** (trigger) — iter **20.07** → **2020.03/2020.07** upgrade packages **(inferred)**.
- **#177327** (PEM journal) — iter **20.06**, tag **PEM: Hotfix 2** → **2020.03 hotfix** **(inferred)**.
- **#87466** (STRAN_CORE_INTFC cols) — Sprint 47, PR 5642 → early V17 **(inferred)**.
- **#1630108 / #1706429 / #1746787** — **no code fix** (Deferred/Rejected, client-specific, not reproducible). Treat as **infra/config** (Oracle keepalive, BA SAP xref).

### Workaround
Per above: add missing triggers via upgrade packages; `SQLNET.EXPIRE_TIME=10` for the ORA-03114 drops; delete overlapped notice-queue record for the sequence collision; verify BA SAP cross-references for duplicate-fuel symptoms.

---

<a name="7-cluster-e"></a>
## 7. Cluster E — QCM ↔ TIPS contract & forecasting integration

**Bugs:** #157801 (PMG QCM/TIPS Forecasting DataSync duplicates, Patch-Immediately, Rejected), #226309 (BLU contract integration QCM→TIPS), #74922 (QCM QIC integration core review)
**Count:** ~3. SF: Pembina (PMG/PCM) forecasting project.

### Symptom
After running the **DataSync between QCM and TIPS Forecasting**, **duplicate** entries appear in the target (PMG), or large syncs are **incomplete** even though the process reports success.

### Root cause (from dev comments)
- **5000-character statement limit (#157801):** the DataSync builds execution statements limited to **5000 chars**; when a sync group is large, records are silently **missed** while the message still says success. Long debate over **bug vs enhancement** — leadership leaned **enhancement** for raising the limit, but agreed an **in-app "X available / X processed" warning** is in-scope.
- **"Duplicates" are mostly by-design:** Data Sync does not regenerate meter suffixes; records on different contracts with the same suffix are **different records** to Data Sync (Ethan Windsor). Cleanup = purge `SCTRL_MTR_LIST_DTL` for the facility and re-sync; run **with deletes** for an exact match.

### Fix / fixed-in-build
- **#157801** — **Rejected** as a bug (not reproducible internally after refresh; reframed as enhancement + better logging). A later patch added DataSync message improvements. **No confirmed fixed-in-build** — do not invent one.

### Workaround
Sync one group at a time (Contracts / Meters / Meter List) to stay under the statement limit; check the **run-summary document in the QPEC Logs folder** (records-to-sync vs synced); purge + re-sync with deletes for an exact copy. Use the duplicate-finder query in §13.

---

<a name="8-cluster-f"></a>
## 8. Cluster F — External-user TIPS reports: security & performance

**Bugs (security/data):** #1715135 (ONM AL01R no data after 2024.04 upgrade, 25-01002928, Acceptance), #1734720 (ONM SAVR shows unassigned BAs, 25-01022205, Approved-by-QA), #1673073 (GNM Daily Position Report ignores security w/ meter param, 24-00964915, Verified→found to be by-design), #1684063 (GNM BA picklist), #1607612/#1407612 (TECO authorization-to-post) | **Bugs (performance):** #1599480 / #1594363 (ETP/EMP Imbalance Detail CAW report too slow), #1661117 (ONK Allocation Imbalance Report hanging, 24-00946909, Verified), #1742657 (ONK same) | **SF:** 25-01002928, 25-01022205, 24-00964915, 24-00946909
**Count:** ~8 TIPS-relevant (after dropping QPTM external-user items).

### Symptom
An **external (producer/shipper/agent) user** runs a TIPS report and gets **no data**, **sees BAs/data not assigned to them**, or the report **hangs/takes hours**.

### Root cause (from dev comments)
- **Stale client-override view after a core view bump (#1715135 ONM):** the 2024.04 AL01R enhancement (Feature **#1639437**) introduced a **new core view `QCTRL_SEC_ALLOC_MTR_VW3_CORE`**. Clients (ONM, HPE) had overridden the **previous** view (`QTIP_CTRL_SEC_ALLOC_MTR_VW2`); after upgrade the report calls **VW3 core**, which lacks the client's OPR/SVC logic → **no data for external users**. Fix = add a new core view #3 (Database Change #1732629) or have the client update setup (alloc group role for PDA Entry type SVC, or associate the User ID with the BA on the meter). Strong stated direction: **stop client-specific view overrides**.
- **Param picklist ignoring BA security (#1734720 SAVR):** the BA picklist showed BAs not on the user's **Integrated Security User → BA tab**; fixed so external users only see their BA-tab BAs (PR 117617). #1673073 turned out **by-design** (report is contract-level; entering a meter still shows the whole contract).
- **Performance (#1599480, #1661117):** the CAW report's **Crystal subreports re-execute the underlying view tens of thousands of times**; the external view JOINs across all users. Fixes: add a **DB index** (e.g. on `QCTRL_ALLOC_PDA`), correct/optimize the `AL*_RPTS_*_VW` / `XVW` views, and ideally **filter by `SEC_USER_ID` / `BP_NO`** so only the logged-in user's rows are read (dropped runtime from hours to seconds). On #1661117 the `ALALL_RPTS_24_DLY_IMB_REV_VW/XVW` were the culprit; report rewrite to pass user param + view optimization.

### Fix / fixed-in-build
- **#1715135** (ONM AL01R view) — iter Maintenance; new core view #3 + Feature **#1639437** in **2024.04 / 2024.10** **(inferred)**; PR 112448, DB change #1732629.
- **#1734720** (SAVR picklist) — PR 117617; Maintenance hotfix, **2024.10/2025.x** **(inferred)**.
- **#1599480** (Imbalance Detail perf) — PRs into **2022.10 and 2023.04** (Cristina Keeton confirmed PR into both); core change = added index only (report/views client-specific).
- **#1661117** (ONK Allocation Imbalance perf) — PRs 101657/101759/101762 into Develop + **2022.10**; DB change #1692315; hotfix on hold (tracked via SF).

### Workaround
For "no data after upgrade": add the alloc-group SVC role / associate User ID with the BA on the meter, or add a client view. For perf: add the missing index and run with full parameters; long-term needs the report/view rewrite.

---

<a name="9-cluster-g"></a>
## 9. Cluster G — Exago / Interactive Reports install, connection & config

**Bugs (config/install):** #1655907 (DB_Configs bad connection ID, Verified), #1619976 (typos in DB_Configs_ORACLE.sql, Rejected), #1706315 (Oracle connection-info wrong Metadata Profile, Rejected), #1717154 (connection-ID error message wrong, Rejected), #1639477 (GNM core-installer gaps, Verified), #1621950 (SQL content column size 512 vs 2000, Acceptance), #1446863 (CAN JIBLINK_ZIP_PATH + IS_INTERNAL_ENVIRONMENT not set by post-refresh, Verified), #1577938 (PML Exago error on QCloud 1.5 after refresh, Rejected), #1730416 (Oracle dump file), #1672582 (crashing in demo) | **Historical wave:** **~70** "Exago 2020.03 Release Testing" query-screen defects (#175428–#178231, #176038–#177703, etc.) from the original Interactive Reports rollout.
**Count:** ~30 config/install + ~70 release-test (summarized). **Exago/Interactive Reports is DEPRECATED in 2025.04** — see fix note.

### Symptom
Exago (TIPS **Interactive Reports**) won't open after an install/refresh; "connection ID" errors; install requires manual Configuration-Item (CI) edits; query-screen columns/data wrong (the 2020.03 wave).

### Root cause (from dev comments)
- **Connection ID + metadata profile (#1655907, #1619976, #1717154, #1706315):** the connection ID **must** be `<MODULE>ExagoDataHelper` (almost always `QTIPExagoDataHelper`), on the **`GLOBAL`** metadata layer. Installer scripts generated `ExagoDataHelper` (no module prefix) and Oracle scripts hardcoded `Metadata`/`Metadeta` (typo) instead of `GLOBAL` → Exago doesn't work until manually fixed.
- **Post-refresh wipes Exago config (#1577938 PML):** refresh overwrote the Exago variables / network logon; permanent fix = add the **Exago variable group to the client's `*.DevOps.EnvironmentSetup`** release and regenerate post-refresh scripts (some clients had the QDEV Exago group, some didn't). Same family as `JIBLINK_ZIP_PATH`/`IS_INTERNAL_ENVIRONMENT` not set on CAN (#1446863).
- **Installer/CI gaps (#1639477):** on-prem Exago needed manual edits to `ConfigureExago.ps1` connection-string template (missing tokens) — fixed in master.
- **Column size mismatch (#1621950):** Exago `content.name`/`content_attribute` 512 (MSSQL) vs 2000 (Oracle) → content truncated/not loaded. DB fix.

### Fix / fixed-in-build
- **#1655907** iter **24.06** → **2024.10** **(inferred)**; **#1621950** iter **24.05**, **#1639477** iter **24.04** → **2024.04/2024.10** **(inferred)**; **#1446863** iter **22.08** → **2022.04** **(inferred)**.
- **Several Rejected with an explicit note (John Weems):** *"Exago (supports TIPS Interactive Reports) is being dropped/deprecated with the 2025.04 release … we will not HF this back since the feature is going away."* So #1619976, #1717154, #1706315 carry **no fix** by design. **Do not promise an Exago fix for any client on/after 2025.04** — the feature is gone.

### Workaround
Manually set the Exago connection ID to `QTIPExagoDataHelper` on the `GLOBAL` metadata layer; add the Exago variable group to the client's EnvironmentSetup release so post-refresh stops wiping it; restart QPECs + web pools.

---

<a name="10-cluster-h"></a>
## 10. Cluster H — QQM reporting universe / query value mismatches

**Bugs:** #1372941 (ACP/Alyeska PGAS+QCT mismatch with QQM, 21-00200020, Verified), #1408470 (ACP Alyeska QQM query error, related), #1360388 (MGP Mustang QQM universe), #1549936 (ERF user not seeing all queries), #1598688 (OH rate class not populated), #1734720-adjacent #1734750 (ACP QQM universe for QCT not retrieving all ticket batches, 25-01024315), #1368608 (ACP automatic reports failing) | **SF:** 21-00200020, 25-01024315
**Count:** ~15 (most are Customer-Service/BI; **BI Engineering owns the universe**, not TIPS core).

### Symptom
A **QQM** (BusinessObjects) report total doesn't match what PGAS/QCT show (e.g. Alyeska Ticket Listing NSV/GSV), or a QQM universe doesn't return all batches/queries.

### Root cause (from dev comments)
Legacy/incorrect **universe derived-table query logic**. On #1372941 the formula subtracted a contractual (meter-suffix) volume from a physical (meter) volume across mismatched suffixes; the derived table `DT_Allocated_Ticket_Trans` / `ACP_BerthAllocation` query was wrong, and the original author had left Quorum with no design docs. Fixed by updating the universe query/derived table and redeploying the `.biar`.

### Fix / fixed-in-build
- **#1372941** — universe `.biar` redeploy (BI), **not** a TIPS application build; verified and deployed to PRD via a QCloud Deployment ticket. **No TIPS release version applies.**

### Workaround
Route QQM value-mismatch issues to **BI Engineering** (universe owner). Confirm whether the user needs **Ticket** vs **Assigned Ticket** objects (the Alyeska confusion) before assuming a defect.

---

<a name="11-cluster-i"></a>
## 11. Cluster I — QCloud environment / deployment (infra, triage pointer)

**Bugs:** #1659669 (CMX 1.5 outage IPWS/notices, RCA), #1665651 (SRB MT down RCA), #1670038 (WS2022 deployment ODBC driver), #1372529 (DTE 1.5 PRD down), #1455392 (HPE 1.5 won't accept EDI), #1411988 (CRW post-refresh domain code QCloud vs QUBE), #1741549/#1742211 (Hilcorp env won't launch), #482133/#630680 (Web deploy/init errors), #123739 (Unitil CPU)
**Count:** ~22 — **mostly Cloud-Ops/infra**, span products.

### Symptom
myQuorum slow, app pool / CPU, environment won't launch, EDI not accepted, outage RCAs, WS2022 ODBC driver gaps, post-refresh domain-code generation wrong.

### Root cause / disposition
Server/web-tier configuration, deployment pipeline, ODBC driver presence, post-refresh tooling (#1411988: Post-Refresh Tool generated domain code `QCloud` for QUBE environments). These are **Cloud Ops / DevOps**, not TIPS product defects.

### Fix / Workaround
Route to **Cloud Ops**; for WS2022, ensure SQL Server ODBC driver installed (#1670038); for post-refresh domain-code, fix the tool config (#1411988).

---

<a name="12-fix-version-matrix"></a>
## 12. Fix-Version Matrix

> IntegrationBuild was **empty on all bugs**; "Fixed-in-build" is **inferred from iteration path / PR branches** unless noted. **Confirm against release notes before quoting to a client.**

| Bug | Cluster | Symptom (short) | State | Fixed-in-build (inferred) | SF case |
|---|---|---|---|---|---|
| #1617552 | B | TIPS API Host won't start (MSSQL) | Acceptance | ~2024.04+ (iter 24.21) | — |
| #1762912 | B | API Host STILL not starting (on-prem NI/CI config) | Verified | ~2025.10 (iter 25.23) | — |
| #1763112 | B/A | CAWDATA requires null .NET conn type | **Rejected** (by-design = NULL) | n/a (iter 26.07) | — |
| #1427530 | A | UTG CAWDATA erroring (QARCH_DS_SRC_SYSTEM_SCHEMA) | Verified | config, per-env (no build) | — |
| #1534309 | A | DTM CAWDATA sync erroring | Rejected→config | config, per-env | 22-00272601 |
| #1725660 | A | HPE CAWDATAFS full-sync job | Rejected→config | config | 25-01015982 |
| #137105 / #111615 | A | SPAWNCAW cache-index warnings | Ready-for-QA | ~2018.11 core fwd | — |
| #1396175 | C | FLOWCAL→eSuite deadlock (trigger PK scan) | Verified | core DB ~2021.x | — |
| #1449303 | C | API self-registration deadlock | Closed | ~2022.10 (iter 22.22) | — |
| #1632769 | C | eSuite staging missing Liquid specs | Ready-for-QA | ~2024.10 (iter 24.07) | — |
| #1638670 | C | lat/long degree-sign error detail | Ready-for-QA | ~2024.10 (iter 24.07) | — |
| #1376389 / #1376390 | C | IP transfer timeout/connection | **Rejected** | n/a (fixed by IP retry) | — |
| #1594204 / #1686007 | C | FLOWCAL end-dating meters | **Rejected** (not repro) | n/a | — |
| #80828 | D | SAP settlement fails on round-to-0 | Ready-for-QA | V17 era (PR 4372) | — |
| #181869 | D | MER VL push (missing trigger) | Ready-for-QA | ~2020.07 (iter 20.07) | — |
| #177327 | D | PEM SAP Journal Transfer | Ready-for-QA | 2020.03 HF2 (iter 20.06) | — |
| #87466 | D | DOM SAP interface (STRAN_CORE_INTFC cols) | Ready-for-QA | early V17 (Sprint 47) | — |
| #1630108 / #1706429 | D | MER BA integration ORA-03114 | Deferred/closed | n/a (Oracle keepalive) | 23-00903800 / 24-00994038 |
| #1746787 | D | CNP/Entex duplicate injection fuel | **Rejected** (not RCA'd) | n/a | 25-01023017 |
| #157801 | E | PMG QCM/TIPS Forecasting DataSync dupes | **Rejected**→enhancement | n/a (5000-char limit) | — |
| #1715135 | F | ONM AL01R no data after upgrade (VW3) | Acceptance | 2024.04/.10 (Feat #1639437) | 25-01002928 |
| #1734720 | F | ONM SAVR shows unassigned BAs | Approved-by-QA | ~2024.10/2025.x | 25-01022205 |
| #1599480 | F | ETP/EMP Imbalance Detail CAW perf | Acceptance | 2022.10 **and** 2023.04 (index) | — |
| #1661117 | F | ONK Allocation Imbalance perf | Verified | Develop + 2022.10 (DB #1692315) | 24-00946909 |
| #1673073 | F | GNM Daily Position ignores security | Verified | by-design (no fix) | 24-00964915 |
| #1655907 | G | Exago DB_Configs bad connection ID | Verified | ~2024.10 (iter 24.06) | — |
| #1639477 | G | GNM Exago installer CI gaps | Verified | ~2024.04 (iter 24.04) | — |
| #1621950 | G | Exago content column size MSSQL vs Oracle | Acceptance | ~2024.10 (iter 24.05) | — |
| #1446863 | G | CAN Exago JIBLINK_ZIP_PATH/post-refresh | Verified | ~2022.04 (iter 22.08) | — |
| #1619976 / #1717154 / #1706315 | G | Exago script typos / conn-ID msg | **Rejected** | n/a (Exago dropped 2025.04) | — |
| #1372941 | H | ACP QQM Ticket Listing value wrong | Verified | BI universe `.biar` (no TIPS build) | 21-00200020 |

---

<a name="13-diagnostic-pointers"></a>
## 13. Diagnostic Pointers

> Verify table/column names against the environment schema before scripting in PRD; wrap UPDATE/DELETE in a transaction with a verify-SELECT.

```sql
-- A. CAWDATA / DataSync source-schema config (the #1427530 root cause)
SELECT * FROM QARCH_DS_SRC_SYSTEM_SCHEMA;   -- must match the Connection Information screen for the env
-- Also confirm TIPSDSDataHelper .NET connection type is NULL (Connection Information screen, not SQL)

-- B. API Host conflict (the #1617552/#1762912 pivot)
--    Connection Information screen → TIPSDSDataHelper → DB_CON_STR_TYPE
--    API Host needs it POPULATED to start; CAWDATA needs it NULL. Fixed build carries it in APIHost.config.

-- C. FLOWCAL/IP transfer: read IP activity/event logs (URLs in the bug), look for StoreEntity /
--    TimeoutRejectedException / deadlock. Deadlock #1396175 = QVALD_MTR PK (PLANT_NO,MTR_NO) scanned on MTR_NO.

-- D. SAP BA integration ORA-03114 drops: server-side keepalive
--    (DBA appends to sqlnet.ora):  SQLNET.EXPIRE_TIME=10
--    SAP notice-queue PK overlap (#176406): inspect QARCH_TRAN_SEQ vs QTIP_ARCH_TRAN_SEQ (same table, two names)
SELECT * FROM CNP_SAP_GL_DTL WHERE PROCESS_QUEUE_ID = <PQID>;  -- duplicate-injection-fuel check (#1746787)

-- E. QCM/TIPS Forecasting DataSync duplicate meter suffixes (#157801 verbatim)
SELECT A.REC_MTR_NO, A.REC_PLANT_NO, A.MTR_SFX
FROM SCTRL_MTR_LIST_DTL A
JOIN SCTRL_MTR_LIST_DTL B
  ON A.REC_PLANT_NO=B.REC_PLANT_NO AND A.REC_MTR_NO=B.REC_MTR_NO
 AND A.MTR_SFX=B.MTR_SFX AND A.CTR_NO<>B.CTR_NO
GROUP BY A.REC_MTR_NO, A.REC_PLANT_NO, A.MTR_SFX HAVING COUNT(*)>1;
-- Plus: read the run-summary doc in the QPEC Logs folder (records-to-sync vs synced).

-- F. External-user report security views (the #1715135 / #1661117 pattern)
--    Compare CORE vs client-override:  QCTRL_SEC_ALLOC_MTR_VW2_CORE / _VW3_CORE  vs  QTIP_CTRL_SEC_ALLOC_MTR_VW2
--    Perf: AL*_RPTS_*_VW / _XVW (e.g. ALALL_RPTS_24_DLY_IMB_REV_VW). Subreports re-run the view; add index, filter by SEC_USER_ID.

-- G. Exago connection: ID must be '<MODULE>ExagoDataHelper' (QTIPExagoDataHelper) on metadata profile 'GLOBAL'
```

---

<a name="14-escalation-guidance"></a>
## 14. Escalation Guidance

**Is the client build already fixed?** Match the bug to §12, then compare the client's TIPS release to the inferred fixed-in-build:
- **API Host won't start (B):** fixed config carried by **2025.10-era** build (#1762912); if below that, expect to remediate after every refresh — set `DB_CON_STR_TYPE` non-NULL to start the API, but that breaks CAWDATA until you re-null it. Get them to the #1762912 build.
- **CAWDATA / DataSync (A):** **not a build problem** — it's per-env config (`QARCH_DS_SRC_SYSTEM_SCHEMA`, NULL connection type). Fix in the env and **persist in post-refresh**; no release will "fix" a mis-set env.
- **FLOWCAL integration (C):** transfer/timeout flakiness is largely resolved by **IP retry logic** (IP side, not a TIPS build). Liquid-spec / lat-long fixes are in **~2024.10**; end-dating bugs are **unresolved/not-reproducible** — escalate only with a live FLOWCAL+IP+TIPS repro.
- **SAP (D):** mostly **client-specific & deferred** (Merit/Entex). Don't promise a build fix; pursue infra (Oracle `SQLNET.EXPIRE_TIME`) or BA SAP cross-reference cleanup. Engineering can't RCA without the client's SAP side.
- **External-user reports (F):** if "no data after upgrade," it's a **stale client-override view** vs a new core view (VW2→VW3) — fix the view/setup, not a build. Perf needs the index + view/report rewrite (in **2022.10/2023.04** for the Imbalance Detail family).
- **Exago (G):** **deprecated in 2025.04** — no fixes ship for clients on/after 2025.04. For older clients, the fixes are config (connection ID / GLOBAL metadata / post-refresh variable group), several already in **2024.x**.
- **QQM (H):** route to **BI Engineering** (universe `.biar`), deploy via QCloud Deployment ticket — no TIPS application version.
- **QCloud (I):** **Cloud Ops / DevOps**, not a product defect.

**Cloud Ops/config vs Engineering quick rule:** reproduces only in a **refreshed/new env** (connection type, source schema, Exago variables, file paths) → **Cloud Ops/config + post-refresh**. Reproduces in a **clean, correctly-configured env** (API Host config bug, FLOWCAL data-mapping, report security-view logic, QQM query) → **Engineering** — link the ADO bug from §12 and confirm the client's build vs the inferred fixed-in-build.

---

*Skill created 2026-06-14 from Azure DevOps TIPS Bugs (Closed/Resolved) under `Engineering\Midstream` + `Engineering\Maintenance\Midstream and Transportation`. 424 bugs matched the WIQL title filter; ~48 deep-read (description + repro + full comment thread + linked PRs).*
*Data-quality caveats: (1) IntegrationBuild empty on all bugs — fixed-in-build inferred from iteration path/PR branches, marked (inferred). (2) "SAP" title term polluted by "disappear"; "external user"/"Imbalance"/"QCloud" polluted by QPTM and infra items — de-noised manually, QPTM Nomination/Offer/RFS/Capacity-Release items dropped. (3) Many client-specific SAP & FLOWCAL bugs are Rejected/Deferred (not reproducible internally) — flagged honestly, no invented builds. (4) QQM = BI universe (BusinessObjects), not a TIPS application build. (5) Exago/Interactive Reports deprecated in 2025.04 — many config bugs intentionally not hotfixed.*
