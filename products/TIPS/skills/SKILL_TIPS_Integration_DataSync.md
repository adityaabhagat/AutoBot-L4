# SKILL: TIPS Integration & DataSync Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-11 | **Product:** My Quorum TIPS (oil/gas transaction & accounting)
**Scope:** All TIPS integration surfaces — FlowCal (FCAL) → TIPS measurement/volume import (incl. Evolution WHMEASIMP / MeasVol Import), the ESuite/TIPS REST APIs (Meter Header timeslicing, Sales Rate API, CSR API), Integration Platform (IP) failed-event republish, Evolution QPTM↔TIPS PTR & imbalance overlay, SAP↔TIPS BA sync, financial interface exports (JE export, TIPS→FI ALLOCEVENT, AR text file, GPEX, JIBLink, paystation/QDOD), orphan meter sync data (SCTRL_MTR_FACILITY), Contract Meter List Web screen, QQM (BusinessObjects reporting), SFTP/Connection Management, and eSuite environment/security plumbing.
**Companion:** For QPTM-side allocation/PTR behavior see **SKILL_Allocations.md** (§7 PTR Overlay & PPA covers the QPTM half of Evolution); EDI nomination flows belong to the QPTM EDI skill. This skill covers the **TIPS side** of data movement.

> Evidence base: 561 closed TIPS cases in categories Integration / DataSync / Integration Platform / EDI / Data Hub / JIBLink / GPEX / eSuite / QQM. Of these, **81 actionable** (37 Software Defect, 37 Application Configuration, 7 ChangeConfig), plus ~62 Training/Customer Error cases sampled for the Expected-Behavior section. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Decision Tree](#2-decision-tree)
3. [FlowCal → TIPS Measurement/Volume Import (HIGH FREQUENCY)](#3-flowcal--tips-measurementvolume-import)
4. [ESuite/TIPS API — Meter Timeslice & API Failures](#4-esuitetips-api--meter-timeslice--api-failures)
5. [Evolution QPTM↔TIPS PTR & Imbalance Overlay](#5-evolution-qptmtips-ptr--imbalance-overlay)
6. [Integration Platform Failed Events / Republish](#6-integration-platform-failed-events--republish)
7. [Orphan Meter Sync Records (SCTRL_MTR_FACILITY)](#7-orphan-meter-sync-records)
8. [SAP ↔ TIPS BA Sync](#8-sap--tips-ba-sync)
9. [Financial Interface Exports (JE / FI / AR / GPEX / JIBLink / QDOD)](#9-financial-interface-exports)
10. [Contract Meter List (Web/QCM Screen)](#10-contract-meter-list-webqcm-screen)
11. [QQM (BusinessObjects) Platform Issues](#11-qqm-businessobjects-platform-issues)
12. [SFTP / Connection Management](#12-sftp--connection-management)
13. [eSuite Environment / Security / Provisioning](#13-esuite-environment--security--provisioning)
14. [Expected Behavior / User Education FAQ](#14-expected-behavior--user-education-faq)
15. [Known ADO Items](#15-known-ado-items)
16. [Diagnostic SQL](#16-diagnostic-sql)
17. [Escalation Guidance](#17-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom | Likely cause | First check |
|---------|--------------|-------------|
| FlowCal daily volumes not arriving in TIPS / Daily Positions empty | **Companies locked** for the acctg month | Company Lock screen — unlock, re-run scheduled import (25-01010617) |
| Volume import "completed successfully" but wrote nothing (Jan 2026+) | **YY→1926 date defect** on 2024.04 and older | Import file year format; YYYY workaround; fixed 2026.04 (26-01065618) |
| FCAL volume load throws 3802 / column-shift errors | A meter using a **UOM TIPS doesn't accept** (e.g. MCM) | Remove/fix the offending meter row in the spreadsheet (24-00989646) |
| Core volume interface step does nothing after a DB refresh | Missing **SCTRL_INT_FULLSYNC** seed row | `SELECT * FROM SCTRL_INT_FULLSYNC WHERE INT_OBJECT_ID='MeterVolume'` (23-00907706) |
| ESuite API error "Effective From Date cannot exceed Effective To Date" | API bisecting-timeslice defect | Version vs fixes #1540498 / #1662511 (24-00955289) |
| Wrong meter timeslice created from an FC meter-updated event | API ignores **contract hour** when widening slice to month edges | #1540498 (22-00868498) |
| Sales Rate API random feedetail insert failure in bulk runs | API race condition / order-of-operations | #1553885; re-run usually succeeds (24-00978724, 22-00823651) |
| Prelim imbalance staging wrong run id / reports empty | Plant run ID used instead of **CO Run ID** in `BLTRAN_STAG_IMB_OVRLY_PRE` | 24-00954762 (code fix) |
| PTR overlay stops with pro-ration error (gas-lift meters) | QPTM WH alloc = 0 for gas-lift; TIPS generated negative PTR | 24-00961955 |
| WHMEASIMP / MeasVol Import partial import or warnings | `AlCtrlMeasVol.LocId` filter defect; paper-meter attr copy defect | #1652309, #1646321 (24-00948249) |
| IP shows StoreEntity "Insert/Updates were cancelled" / deadlock / concurrency | Transient optimistic-concurrency or deadlock | **Re-publish** the failed events from IP (25-01013486 et al.) |
| Can't save Meter Definition / Shared Meter — orphan record error | Orphan open-ended row in **SCTRL_MTR_FACILITY** (often plant 999) | Diagnostic §16-B; data script (25-00997682, 24-00972581) |
| SAP→TIPS BA send fails "Factory XRefDataHelper does not exist" after refresh | XRefDataHelper connection lost in env refresh | Re-add in **Connection Management** screen (24-00984054, #1692076) |
| TIPS ALLOCATE EVENT completes but no data reaches FI | Volume rollup by product/disposition missing | Global config `ALLOCATE \| ROLLUP_MTR_VOL_BY_PROD_DISP` (22-00830775) |
| Contract Meter List Web won't save / silent failure with notifications on | PPA event detector fired before DO populated; archived prod date | 24-00954043 (DO extension fix) |
| All batch jobs missing in Web (fine in Classic) | Processes registered in wrong **metadata layer** (code table #59) | Move global processes to the integrated metadata layer (24-00982327) |
| QQM login screen appears instead of SSO launch | Hardcoded path in global config | Remove path, restart SIA/Tomcat (23-00897783) |
| QQM TIPS Universe ORA-00942 | Missing sysgen (synonym/grant) | Add missing sysgen (22-00549917) |
| SFTP connect fails after refresh | FTP host details blank in UAT | Connection Management host details (25-01004521) |
| Screen crashes (e.g. Contract Maintenance) for everyone | Hung QPEC service | **QPEC restart** (25-01004831) |

---

## 2. Decision Tree

```
TIPS Integration/DataSync case reported
│
├─ Volumes/measurement not arriving from FlowCal or import file?  (§3)
│   ├─ Scheduled job ran but no data → Company Lock screen for the acctg month  (25-01010617)
│   ├─ "Completed successfully", 0 rows, file uses 2-digit years → YY→1926 defect, fix YYYY / upgrade  (26-01065618)
│   ├─ Errors on load (3802 etc.) → bad UOM / bad meter row in file  (24-00989646)
│   ├─ Post-refresh, core interface step inert → SCTRL_INT_FULLSYNC seed row missing  (23-00907706)
│   └─ Evolution WHMEASIMP partial/warnings → known WHMEASIMP bugs §15  (24-00948249)
│
├─ Error surfaced in Integration Platform (StoreEntity/GetEntity)?  (§4, §6)
│   ├─ "Effective From Date cannot exceed Effective To Date" → API timeslice bug, check fix level  (#1662511)
│   ├─ Concurrency violation / deadlock victim / "inserts-updates were cancelled" → RE-PUBLISH (transient)
│   ├─ "Resource not found" on GetEntity → usually republish; if persistent, missing entity/xref
│   └─ "Factory XRefDataHelper does not exist" → Connection Management config lost in refresh  (§8)
│
├─ Evolution QPTM↔TIPS overlay (PTR / prelim imbalance / rerun approval)?  (§5)
│   ├─ Staging table has plant run id, reports empty → CO Run ID defect  (24-00954762)
│   ├─ MCF/MMBTU values flipped in QTIP_TRAN_PLANT_PTR → column-flip defect  (24-00954063)
│   ├─ PTR overlay pro-ration error stops process → gas-lift WH alloc = 0  (24-00961955)
│   └─ Cross-ref SKILL_Allocations.md §7 for the QPTM half
│
├─ Can't edit Meter Definition / Shared Meter (orphan data)?  (§7)
│   └─ Find + delete orphan open-ended SCTRL_MTR_FACILITY (/SCTRL_MTR_HEADER/SEXTN_MTR_HEADER_QRMTIPS)
│      rows via script — recurring at WTG & MER  (25-00997682, #1689827, #1758912)
│
├─ Financial export (JE/FI/AR/GPEX/JIBLink) wrong or empty?  (§9)
│   ├─ TIPS→FI empty → ROLLUP_MTR_VOL_BY_PROD_DISP global config  (22-00830775)
│   ├─ Need to re-push posted data → run ALLOCEVENT (user education)  (26-01070574)
│   └─ Reversal/rerun anomalies (GPEX, paystation) → known rerun defects, escalate w/ run ids
│
├─ Web screen issue (Contract Meter List etc.)?  (§10)
│   ├─ Reproduce in BOTH Web/QCM and ESuite Classic — Web-only ⇒ likely code defect
│   └─ Batch jobs missing in Web entirely → metadata-layer config, code table #59  (24-00982327)
│
├─ QQM (reports/universe/login)?  (§11)
│   └─ Login loop → global config + SIA/Tomcat; ORA-00942 → sysgen; downloads blocked → Chrome settings
│
└─ Connection/credential/provisioning (SFTP, Okta, QPEC)?  (§12, §13)
    └─ Mostly Cloud Ops config — Connection Management, service restarts, security groups
```

---

## 3. FlowCal → TIPS Measurement/Volume Import

The largest actionable cluster (~9 defect/config cases plus a steady stream of Training cases). Three distinct transport paths exist; identify which one first:
1. **Integration Platform (event-based)** — FlowCal meter/volume events → ESuite API → TIPS (Hess, PML, AZR, UTG clients).
2. **Batch file/volume import** — spreadsheet or flat-file volume loads (IACX, Merit), incl. PI imports.
3. **Evolution MeasVol Import / WHMEASIMP** — TIPS MeasVol Import Process by TSP for paper meters (ENT Permian/STX).

### Recurring failures & fixes
| Symptom | Root cause | Resolution recipe | Case |
|---------|-----------|-------------------|------|
| Daily FCAL→TIPS feed "broken", no volumes in Daily Positions report | **Companies locked** for the new acctg month | Unlock on the **Company Lock screen**; scheduled processes then run normally. A one-off query timeout may follow — re-run manually | 25-01010617 |
| Import completes successfully but writes no records; daily pricing (NC4/IC4/Propane) not pulled | **Code defect:** on 2024.04 and older, 2-digit year `/26` parses as **1926** | Short-term: change import file dates to **YYYY**. Long-term: fixed in **2026.04**, hotfixable to 2 prior GAs | 26-01065618 |
| FCAL volume load errors (3802), columns thrown off | One meter used **UOM `MCM`** which TIPS does not accept — shifted VOLUMES/ENERGY MCF/MMBTU columns | Remove/correct the offending meter row, reload | 24-00989646 |
| Core volume/analysis interface step inert after DB refresh | **`SCTRL_INT_FULLSYNC` seed row lost in refresh** | `INSERT INTO SCTRL_INT_FULLSYNC (INT_OBJECT_ID, FULL_SYNC_DT, USER_ID, UPDT_DT) VALUES ('MeterVolume', GETDATE(), 'FLOWCAL', GETDATE());` (verbatim from the case) | 23-00907706 |
| Evolution: MeasVol Import by TSP completed with error, imported only 1 of 3 paper meters | **WHMEASIMP `AlCtrlMeasVol.LocId` filter error** | Code fix — ADO **#1652309** (Closed) | 24-00948249 |
| WHMEASIMP copying pressure base/temperature (not PSIG) onto paper meters with warnings | WHMEASIMP attribute-copy defect | Code fix — ADO **#1646321** (Closed) | (24-00942050) |
| WHMEASIMP overwriting manual measurement entries | MeasVol process overwrite defect | Code fix — ADO **#1644974** (Closed) | — |
| Monthly Nomination Import running long / hung | Hung QPEC services | **Restart TIPS QPEC services** | 22-00540048 |
| Volume file import error (Merit) | File/config mismatch — resolution pattern unclear from mined cases | Verify file layout vs import spec first | 22-00853539 |
| Protrend Analysis upload process error | Date format in stored proc | Changed date format in **`QPP_ANALYSIS_UPLOAD_PRO.sql`** | 22-00691544 |

> **Triage order for "no volumes in TIPS":** (1) company/acctg-month lock, (2) did the scheduled process actually run (process queue), (3) import file format (years, UOM, layout), (4) SCTRL_INT_FULLSYNC seed if env was refreshed, (5) only then suspect the API/code.

---

## 4. ESuite/TIPS API — Meter Timeslice & API Failures

The ESuite REST API is the write path used by Integration Platform for FlowCal-driven meter changes, and by client-built consumers (ONEOK Sales Rate API, CSR API). ~8 actionable cases.

### 4a. Meter Header timeslicing defects (FC → ESuite)
- **Bisecting-slice produces inverted range** — error in IP: `StoreEntity: ESUITE (PUT): Error: Meter Header: Effective From Date cannot exceed Effective To Date. Effective Range: 8/1/2023-7/31/2023`. When a meter's existing time slices are shaped a certain way, the API builds a bisecting slice with an incorrect range. Seen at Hess, UTG, PML. Fixed in ADO **#1662511** (Closed). Case 24-00955289.
- **Wrong timeslice on month-end characteristics change** — the API doesn't account for the **contract hour** when widening the slice to first/end of month, so an FC change at month end (inclusive of contract hour) lands in the wrong slice. Fixed in ADO **#1540498** (Closed). Cases 22-00868498, 23-00902822.
- **What's expected vs defect:** FlowCal edits to meter characteristics legitimately CREATE Meter Header time slices — that alone is by design (23-00930865, Training). Investigate only when the slice **range** is wrong or save errors out.

### 4b. Client API failures
| Issue | Root cause | Resolution | Case |
|-------|-----------|------------|------|
| ONEOK **Sales Rate API**: bulk runs (200–600 trades) randomly fail one feedetail insert; retry corrupts header end-dates | Race condition / order-of-operations in API (FeeDetail timestamps older than Header) | Code fix — ADO **#1553885** (Closed); earlier fixed-fuels exception **#1386943** | 24-00978724, 22-00823651 |
| CSR API authentication error after 2022.10 upgrade | A service was **removed by the upgrade** | Service re-added | 23-00906420 |
| API performance degraded from a patch | Patch-introduced perf regression | Code fix | 23-00929307 |
| Need API request logging to debug ONM integrations | App Insights logging not enabled; qtrace absent | ONM.TIPS Web/MT code + installer/release-pipeline change to add json/route/method-parameter debug logging | 23-00888727 |
| Large-contract Meter List updates via QCM/ESuite sporadic | Defect (resolution pattern unclear from mined cases) | — | 25-00999727 |

---

## 5. Evolution QPTM↔TIPS PTR & Imbalance Overlay

Evolution clients (ENT Permian/STX is the archetype) run TIPS plant accounting integrated with QPTM pipeline allocation. TIPS generates PTR; QPTM overlays it; imbalance flows back into TIPS staging for settlement. ~7 actionable cases, all ENT, all **Software Defect**. The QPTM half is documented in SKILL_Allocations.md §7.

| Symptom | Root cause | Resolution | Case |
|---------|-----------|------------|------|
| Prelim imbalance stages **plant run ID** instead of **CO Run ID** in `BLTRAN_STAG_IMB_OVRLY_PRE` → imbalance reports can't read `QRMTIPS.QTRAN_SETTLE_CTR_FEE` | Run-id selection defect | Code fix: prelim imbalance now stages with the CO_CD run id (matching production import) | 24-00954762 |
| `TIK_SET_RES_MCF/MMBTU` and `PURCH_SET_RES_MCF/MMBTU` **flipped** vs `RES_MCF/RES_MMBTU` in `QTIP_TRAN_PLANT_PTR` | Column-mapping flip defect | Code fix | 24-00954063 |
| PTR overlay errors with pro-ration and stops at first error; TIPS creates negative PTR when WH < Gas Lift | For gas-lift meters QPTM WH allocation is 0, so overlay can't distribute TIPS PTR | Code fix (overlay handling of 0-alloc/gas-lift) | 24-00961955 |
| Prelim Imbalance data issues generally | Defect | (resolution detail not recorded in SF) | 24-00958162 |
| Imbalance overlay **rebooks CO records** on reruns (`QTRAN_SETTLE_CTR_FEE`) | Overlay pull inserted non-CO records on rerun | TIPS Imbalance Overlay Pull updated to insert **only CO records for reruns** and to generate the company status record if no company run executed yet | 22-00603658 |
| Rerun-only approval record not generated after QPTM creates staging records | Rerun approval defect | (resolution detail not recorded in SF) | 22-00608991 |
| Paper meter PTR split decimals wrong | GENPTRPRM derivation | **GENPTRPRM process step** modified to derive processing/transportation contract split decimals for paper meters **from their physical meters** | 22-00603657 |
| QPTM stage imbalance overlay unique constraint on `ESUITE_QENT.BLTRAN_STAG_IMB_OVRLY` | Duplicate insert on overlay staging | Code fix — ADO **#1695118** (Closed) | (24-00984737) |

> **Triage:** always capture **plant run id vs CO run id**, acctg/prod month, and whether it's a **rerun**. Most Evolution overlay defects are rerun-path or run-id-selection bugs.

---

## 6. Integration Platform Failed Events / Republish

A high-volume operational cluster: clients (PML, AZR, Producers Midstream) report batches of failed IP events; resolution is almost always **re-publishing** them. 3 actionable cases + many Training-classified ones (26-01104196, 26-01100423, 26-01090007, 24-00984118).

### Error signatures seen (all resolved by re-publish)
- `StoreEntity: Insert/Updates were cancelled` — optimistic concurrency: "another user changed the record you were viewing…re-query…then save" (25-01013486/473/243; 26-01100423).
- `Concurrency violation: the UpdateCommand affected 0 of the expected 1 records.`
- `Transaction (Process ID n) was deadlocked on lock resources…chosen as the deadlock victim.`
- `System.Net.Http.HttpRequestException: An error occurred while sending the request.`
- `GetEntity: Resource not found` — republish; if it persists, the target entity/xref genuinely doesn't exist (see 25-01056786: meter header referenced a **Contact ID that no longer exists** — client must fix the data, not republish).

### Recipe
1. In Integration Platform, filter failed events for the date range, group by error text.
2. **Re-publish** transient classes (concurrency, deadlock, HTTP send) — they self-heal.
3. For persistent failures, read the payload: missing xref/contact/meter = client data fix; "Factory XRefDataHelper does not exist" = §8 config.
4. Recurring daily deadlocks at scale → escalate as perf/code with event ids and timestamps.

---

## 7. Orphan Meter Sync Records

DataSync cluster: users cannot save **Meter Definition** or **Shared Meter** screens because orphaned, open-ended integration-sync rows exist. Chronic at **WTG** (plant 999 pattern) and **MER**. ~4 SF cases, many more script-deployment WIs in ADO.

- **Symptom:** "Unable to update Meter Definition" / "cannot change Shared meter nor Meter Def — orphan records" (25-00997682, 24-00972581).
- **Root cause:** orphan **open-ended** record in **`SCTRL_MTR_FACILITY`** (sometimes also `SCTRL_MTR_HEADER`, or overlapping timeslices in `SEXTN_MTR_HEADER_QRMTIPS`) pointing at a plant/facility the meter shouldn't be on (WTG: bogus link to plant 999).
- **Resolution recipe:** data script deletes the orphan open-ended row(s) for the named meter, e.g. "erased the orphan open-ended record from SCTRL_MTR_FACILITY linked to plant 999" (25-00997682); or adds the missing facility link (24-00984237: add meter 102701 to facility 999). Script deployments: ADO **#1689827** (WTG PRD, meter 4132890), **#1758912 / #1758697** (MER, meter 226043), **#1722628** (MER, overlapping timeslice meter 226037), **#1734858** (MER, meter 225985).
- **Long-term:** ADO **#1561405** (Closed, Database Change) — "Remove SCTRL_MTR_FACILITY from Integration Synch tables" — reduces the class of orphan creation; if a client still generates these monthly, check their build for it.
- Related: 24-00944499 (TGNR Monthly GPM Condensate) — recurring manual script replaced by a **DB package** delivered via myQuorum Cloud WI **#1647879**.

---

## 8. SAP ↔ TIPS BA Sync

Business Associate master-data sync between SAP and TIPS (Merit Energy pattern; PRA→TIPS at Merit too). ~4-5 cases.

| Symptom | Root cause | Resolution | Case |
|---------|-----------|------------|------|
| SAP→TIPS BA send fails: `TIPS: Exception while updating addresses: Factory XRefDataHelper does not exist` — started after env refresh | **XRefDataHelper connection wiped by the environment refresh** | Re-add **XRefDataHelper** in the **Connection Management** screen. ADO **#1692076 / #1692055** (Closed) | 24-00984054 |
| TIPS→SAP integration error during upgrade testing | Network setup | Network/firewall updates between refreshed envs | 24-00982678 |
| SAP BA integration error during upgrade testing | Config drift | Manual adjustment to configs | 24-00980929 |
| PRA→TIPS bulk BA sync: several BAs fail with **ORA-00001** (unique constraint) | Duplicate-key on bulk insert | Defect; resolution pattern unclear from mined cases — dedupe source BAs / retry singles | 22-00516178 |
| BAs missing post-conversion | Stale conversion | Refreshed a new data conversion CNV→UCT | 22-00874281 |

> **Post-refresh checklist for integrated clients (MER):** Connection Management entries (XRefDataHelper, FTP hosts, CAW connections), SCTRL_INT_FULLSYNC seed rows, network routes. Environment refreshes are the #1 generator of "integration suddenly broken in UAT" cases.

---

## 9. Financial Interface Exports

TIPS → downstream financial systems (FI/JE/AR), and statement/export products (GPEX, JIBLink, Gas Control export). ~7 actionable cases.

| Export | Symptom | Root cause / Resolution | Case |
|--------|---------|-------------------------|------|
| TIPS→FI (ALLOCATE EVENT) | Process completes in TIPS, **no data reaches FI** | Code fix added rollup logic for meter volumes by product & disposition to the TIPS Allocations API service + new global config **`ALLOCATE \| ROLLUP_MTR_VOL_BY_PROD_DISP`** (TIPS metadata layer, defaults to sum) | 22-00830775 |
| JE Export (2023.04) | Journal export to SFTP errors | Application configuration (error spreadsheet attached to case; resolution detail not recorded) | 24-00949784 |
| Paystation / QDOD interface | Bad reversals created on reruns for tolerance-threshold records | Code fix: when inserting reversals for records posted in a prior run but absent from the rerun, check for a **paystation** record instead of a revenue record — leave paystation-only records unchanged in QDOD | 22-00549856 |
| GPEX / Gas Statement CSV | Incorrect data for **reversals on reruns** (Williston) | Software defect (TP114583); fix delivered | 22-00603610 |
| JIBLink Export | Missing backup attachment PDF (v17) | Software defect; resolution detail not recorded in SF | 23-00933239 |
| Gas Control Export | File name **reverted to default** | Config defect; resolution detail not recorded in SF | 24-00971724 |
| AR Text File | QUOR-1823 AR text file issue (Enable) | Software defect; resolution detail not recorded in SF | 22-00562686 |

> User education: to **re-push posted data from TIPS to FI**, run the **ALLOCEVENT** job under TIPS processes (26-01070574, Training).

---

## 10. Contract Meter List (Web/QCM Screen)

eSuite/Web screen with repeated **Web ≠ Classic** defects (mirrors the QPTM pattern: Web screen skips validation or fires events wrong). ~4 actionable cases; an active stream of ADO bugs continues into 2026.

| Symptom | Root cause | Resolution | Case |
|---------|-----------|------------|------|
| Web: cannot SAVE when adding a meter w/ new effective date once **pop-up notifications (mtr_cct)** enabled — silent failure; Classic OK. Log: `The production date: 8/1/2019 is archived. PPA will not be logged.` at `QPPAMeterListPayStationDetector.CheckIfPlantIsArchivedForProdDate` | "Save" event registered in addition to "PreSave" on the Meter List DO Extension → `DoSetNotification` ran the PPA event handler **before DO data was populated** | Code fix: removed the redundant "Save" event registration from the Meter List DO Extension object | 24-00954043 |
| Web error adding CCTs to multiple meters with mtr_cct notification on | Defect | Code fix delivered | 24-00968427 |
| Contract Party name not showing in Contract Meter List | Environment-related (works in core); eng maintenance bug logged | Env restart/refresh; monitor | 25-01005845 |
| Incorrect plant name shown for Oklahoma | Config; resolution detail not recorded | — | 23-00906596 |

Related current ADO: **#1758565** (Closed — list doesn't query when meters are closed, DCP), **#1788087** (Closed — invalid-effective-date error after changing contract effective date, UPC 26-01084783), **#1769433** (Closed — copy/paste not autopopulating required field, ETP), **#1801070** (Proposed — 2026.04 QCM beta: meter-date validation not triggered).

---

## 11. QQM (BusinessObjects) Platform Issues

QQM = the BusinessObjects-based reporting stack for TIPS (universes, public folders, SIA/Tomcat). Almost all **Application Configuration / ChangeConfig**, handled by Cloud Ops.

| Symptom | Resolution | Case |
|---------|------------|------|
| Users get the QQM **login screen** instead of seamless SSO launch | Remove the **hardcoded path in the global config file**, restart **SIA/Tomcat** | 23-00897783 |
| TIPS Universe query → **ORA-00942** (table or view does not exist) | Add the **missing sysgen** (synonym/grant generation for the universe object) | 22-00549917 |
| Kerberos/AD auth after disabling RC4 | **AES-128/AES-256 is supported** — client updates `KRB5.ini` under `C:\Windows` for AES Kerberos encryption | 26-01103241 |
| UAT QQM not launching | **Chrome application not enabled** for the env (myQuorum Cloud WIs #1641983, #1636625) | 23-00933517 |
| Public-folder access / report visibility for a user | Set user type internal for all modules + add to full-access user groups | 23-00919270 |
| Request to use custom code in QQM reports | **Declined by policy** — custom code mods to QQM not allowed | 23-00901114 |
| Single user can't download reports | Chrome browser setting blocking content (Customer Error) | 24-00954347 |

---

## 12. SFTP / Connection Management

| Symptom | Resolution | Case |
|---------|------------|------|
| Fail to connect to SFTP (UAT) | **FTP Host details missing** post-refresh — re-enter on Connection Management | 25-01004521 |
| Need read-only SFTP account (TIPS A1) | Cloud Ops created read-only prod ftp + sent credentials | 24-00984169 |
| CAW (Crude Accounting Workbench) connections missing in UATA1 | **Scripted the CAWDATAHELPER connections** into the TIPS application | 24-00973248 |

> Same lesson as §8: after every environment refresh, audit Connection Management (FTP hosts, XRefDataHelper, CAWDATAHELPER) before debugging anything deeper.

---

## 13. eSuite Environment / Security / Provisioning

Plumbing-level cases — quick wins if you recognize them:

| Symptom | Resolution | Case |
|---------|------------|------|
| Screen crashes on selection (Contract Maintenance) | **QPEC restart** | 25-01004831 |
| Batch jobs missing in **Web** (Classic fine) | Code table **#59** processes were in a client metadata layer; global processes/reports must be under the **integrated metadata layer** (RightAnswers KB 171120132000416) | 24-00982327 |
| New SSO user missing customer prefix (e.g. `EQC_`) | Provisioning automation fired before account activation; **retry interval adjusted** | 25-00996100 |
| Okta apps not provisioning for a user | Added to required group, **rejoined Okta account to app groups** | 23-00929232 |
| Password-reset emails never arrive | Known issue with **@yahoo** domains for QCloud password manager — switch the account email domain | 24-00968277 |
| ESuite launch error after refresh | ESuite installer **repointed to the correct DB** (QRM_ESUITE_DEV) | 23-00916690 |
| Security group can't see scoped data (Group 7) | Enable **scoped security explicit** on the Security Group Privilege screen | 22-00822095 |
| SOA Security User Admin screen broken with OpenID enabled | Software defect (TP152309); resolution detail not recorded | 23-00880661 |
| BA contact missing / data mismatch | DB validation added + Facility Definition screen updated | 23-00920784 |

---

## 14. Expected Behavior / User Education FAQ

From the Training/Customer Error sample (~62 cases in these categories). Recognize these to avoid needless escalation:

1. **"IP events failed again — re-publish them."** Concurrency violations, deadlock victims, and HTTP send errors in Integration Platform are transient; the standing routine (PML/AZR) is simply re-publishing them. Only escalate if the same payload fails repeatedly after republish (26-01104196, 26-01100423, 24-00984118).
2. **"FlowCal edits keep time-slicing our Meter Header."** Expected behavior — meter-characteristic changes in FlowCal create Meter Header time slices via the API by design (23-00930865). Defect only if the slice *range* is wrong (§4).
3. **"How do we re-post data from TIPS to FI?"** Run the **ALLOCEVENT** job under TIPS processes (26-01070574).
4. **PI import fails `UNIQUE CONSTRAINT (ESUITE.PK_STRAN_VOL_DAILY) VIOLATED`.** The TIPS import runs once daily (11:15 MT) — put only **one PI file per day** on the FTP (22-00691533).
5. **EDI: TIPS EDINCOMING fails `NULLABLE OBJECT MUST HAVE A VALUE`.** NULL-quantity noms exist on the TIPS side — client deletes them or zeroes them; process then runs clean (23-00921572, 23-00921194).
6. **EDI: inbound SQOP "RECORD CANNOT BE CONFIRMED IF THERE IS NEITHER A CONFIRMED QUANTITY NOR A CONFIRMED INTEREST PERCENT".** Confirmation rows have `CONF_IND=1` with null qty AND pct — fix on the Confirmation screen (verify SQL in §16-E) (22-00609049).
7. **"PRICETOSCH brought in no records."** Wrong PROD_DT parameter (24-00950069). Likewise plant-post failures are usually client setup: collector ID on Facility Definition needing a Measure re-run (23-00897944), or identifiers >8 chars (22-00513116).
8. **Meter Header IP failure naming a contact** — the meter references a Contact ID that doesn't exist; client corrects the meter header (25-01056786).

---

## 15. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|-------|--------------|-----------------|---------|---------|
| **#1540498** | Bug / **Closed** | ESuite API — incorrect Meter Timeslice updated by FC Integration (contract hour) | §4 | 22-00868498, 23-00902822 |
| **#1662511** | Bug / **Closed** | UTG — ESuite API Time Slice produces error for Meter Header (inverted range) | §4 | 24-00955289 |
| **#1553885** | Bug / **Closed** | ONM — ONEOK Sales Rate API failures | §4 | 22-00823651, 24-00978724 |
| **#1386943** | Bug / **Closed** | ONM — TIPS Contract Sales Rate API Fixed Fuels exception | §4 | 21-00200202, 22-00832172 |
| **#1652309** | Bug / **Closed** | ENT — WHMEASIMP `AlCtrlMeasVol.LocId` filter error | §3 | 24-00948249 |
| **#1644974** | Bug / **Closed** | ENT — WHMEASIMP MeasVol process overwriting manual entries | §3 | — |
| **#1646321** | Bug / **Closed** | Evolution — WHMEASIMP pressure base/temp copied to paper meter | §3 | 24-00942050 |
| **#1695118** | Bug / **Closed** | QPTM stage imbalance overlay unique constraint on `ESUITE_QENT.BLTRAN_STAG_IMB_OVRLY` | §5 | 24-00984737 |
| **#1692076 / #1692055** | Bug+Req / **Closed** | MER — post-refresh update XrefDataHelper connection (TIPS) | §8 | 24-00984054 |
| **#1689827 / #1689553 / #1688305** | Script Deploy / **Closed** | WTG — delete orphan open-ended `SCTRL_MTR_FACILITY` (& `SCTRL_MTR_HEADER`) rows, meter 4132890 | §7 | 24-00979975 |
| **#1758912 / #1758697 / #1734858 / #1722628** | Script Deploy / **Closed** | MER — delete bad/overlapping `SCTRL_MTR_FACILITY` / `SEXTN_MTR_HEADER_QRMTIPS` rows (meters 226043/225985/226037) | §7 | 25-01046485, 25-01023407, 25-01013209 |
| **#1561405** | DB Change / **Closed** | Remove `SCTRL_MTR_FACILITY` from Integration Synch tables | §7 | — |
| **#1647879** | Deployment (myQuorum Cloud) / **Closed** | TGNR — DB package delivering long-term GPM condensate fix | §7 | 24-00944499 |
| **#1730248** | Requirement / **Closed** | TIPS Performance Initiative (Long-Term) — Convert MEASVOLS | §3 | — |
| **#1758565** | Bug / **Closed** | DCP — Contract Meter List does not query when meters are closed | §10 | — |
| **#1788087** | Bug / **Closed** | UPC — QCM invalid-effective-date error in Contract Meter List | §10 | 26-01084783 |
| **#1769433** | Bug / **Closed** | ETP — QCM Contract Meter List copy/paste not autopopulating required field | §10 | — |
| **#1801070** | Bug / **Proposed** | 2026.04 QCM beta — Contract Meter List meter-date validation not triggered | §10 | — |
| **#1641983 / #1636625** | Request+Incident (myQuorum Cloud) / **Closed** | WTG — enable Chrome for UAT QQM | §11 | 23-00933517 |

---

## 16. Diagnostic SQL

(Oracle TIPS schemas: `ESUITE`, `QRMTIPS`, `ESUITE_QENT` for Evolution. Verify schema prefix per client.)

### A. Integration full-sync seed (core volume interface inert after refresh — 23-00907706)
```sql
SELECT * FROM SCTRL_INT_FULLSYNC WHERE INT_OBJECT_ID = 'MeterVolume';
-- Missing? Reseed (verbatim fix from the case):
INSERT INTO SCTRL_INT_FULLSYNC (INT_OBJECT_ID, FULL_SYNC_DT, USER_ID, UPDT_DT)
VALUES ('MeterVolume', GETDATE(), 'FLOWCAL', GETDATE());
```

### B. Orphan / open-ended meter-facility sync rows (Meter Definition blocked — §7)
```sql
-- Open-ended facility links for the affected meter (orphan = facility/plant the meter shouldn't be on)
SELECT * FROM ESUITE.SCTRL_MTR_FACILITY
WHERE  MTR_NO = '<MTR_NO>' AND EFF_DT_TO IS NULL;

-- Cross-check the header side / overlapping timeslices (MER pattern, ADO #1722628)
SELECT * FROM SCTRL_MTR_HEADER          WHERE MTR_NO = '<MTR_NO>' ORDER BY EFF_DT_FROM;
SELECT * FROM SEXTN_MTR_HEADER_QRMTIPS  WHERE MTR_NO = '<MTR_NO>' ORDER BY EFF_DT_FROM;
-- Fix = scripted delete of the orphan open-ended row(s); route via Script Review/Deployment WI.
```

### C. Evolution imbalance overlay run-id check (24-00954762)
```sql
-- Staged prelim imbalance: RUN_ID should correspond to the CO_CD (company) run, not the plant run
SELECT * FROM BLTRAN_STAG_IMB_OVRLY_PRE
WHERE  CO_CD = '<CO_CD>' AND ACCTG_MTH = '<ACCTG_MTH>';

SELECT * FROM QRMTIPS.QTRAN_SETTLE_CTR_FEE
WHERE  CO_CD = '<CO_CD>' AND RUN_ID = '<RUN_ID>';
```

### D. Evolution PTR plant values (column-flip / gas-lift checks — 24-00954063, 24-00961955)
```sql
SELECT MTR_NO, PROD_DT, RES_MCF, RES_MMBTU,
       TIK_SET_RES_MCF, TIK_SET_RES_MMBTU, PURCH_SET_RES_MCF, PURCH_SET_RES_MMBTU
FROM   QTIP_TRAN_PLANT_PTR
WHERE  MTR_NO = '<MTR_NO>' AND PROD_DT = '<PROD_DT>';
-- Red flags: TIK/PURCH MCF values matching the MMBTU column (flip defect); negative PTR on gas-lift meters.
```

### E. EDI confirmation validation (SQOP "cannot be confirmed" — verbatim from 22-00609049)
```sql
SELECT * FROM QRMTIPS.QCTRL_CONF
WHERE  MTR_NO = '<MTR_NO>' AND CONF_IND = 1
  AND  CONF_PCT IS NULL AND CONF_QTY IS NULL;
-- Hits = rows the user must correct on the Confirmation screen.
```

### F. Daily volume landing table (PI / FCAL import dup-key — 22-00691533)
```sql
SELECT MTR_NO, PROD_DT, COUNT(*) FROM STRAN_VOL_DAILY
WHERE  PROD_DT >= '<START>' GROUP BY MTR_NO, PROD_DT HAVING COUNT(*) > 1;
-- PK_STRAN_VOL_DAILY violations = a second import file for the same day.
```

> Column-name caveat: tables `SCTRL_INT_FULLSYNC`, `SCTRL_MTR_FACILITY`, `BLTRAN_STAG_IMB_OVRLY_PRE`, `QTRAN_SETTLE_CTR_FEE`, `QTIP_TRAN_PLANT_PTR`, `QCTRL_CONF`, `STRAN_VOL_DAILY` are all named verbatim in case data; some key/column names in B/C/F are inferred — verify against the client schema before scripting.

---

## 17. Escalation Guidance

**It's a CODE DEFECT → Engineering** when:
- The error reproduces in core/base with correct config (API inverted timeslice ranges, WHMEASIMP filter errors, run-id selection, column flips, rerun reversal logic).
- Web behaves differently from ESuite Classic on the same data (Contract Meter List save/validation class of bugs).
- A bulk/concurrent workload fails non-deterministically while singles succeed (Sales Rate API race).
- Match against §15 first — most of these already have a **Closed** ADO fix; the real question becomes *which version/hotfix carries it* (e.g. the YY-date import fix is in **2026.04**, hotfixable 2 GAs back).

**It's CONFIG/DATA → Cloud Ops** when:
- It started right after an **environment refresh** (XRefDataHelper, FTP hosts, CAW connections, SCTRL_INT_FULLSYNC, installer DB pointers) — §8/§12 checklist.
- It's month-start and volumes stopped → **company locks**.
- A screen is blocked by orphan sync rows → Script Review/Deployment WI with the §16-B verify-SELECT and row counts; destructive steps in a transaction.
- Service-level weirdness (screen crashes for all users, hung imports) → **QPEC / SIA/Tomcat restart** before anything else.
- Security/visibility (batch jobs missing in Web, QQM folders, scoped security) → metadata layer & security-group config.

**It's the CUSTOMER / Training** when:
- The failure class is in §14 (republishable IP errors, expected timeslicing, null noms, dup import files, wrong run parameters). Provide the recipe and close as Training/Customer Error — don't open a bug.

---

*Skill created: 2026-06-11*
*Based on: 561 closed My Quorum TIPS Integration/DataSync-group SF cases — 81 actionable (37 Software Defect / 37 Application Configuration / 7 ChangeConfig) plus ~62 Training & Customer Error cases — and ADO work items #1540498, #1662511, #1553885, #1386943, #1652309, #1644974, #1646321, #1695118, #1692076, #1689827, #1758912, #1722628, #1734858, #1561405, #1647879, #1730248, #1758565, #1788087, #1769433, #1801070, #1641983, #1636625.*
*Companion: SKILL_Allocations.md (QPTM side of Evolution PTR/imbalance overlay).*
