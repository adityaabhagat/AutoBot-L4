# SKILL: QPTM Integration & Processing Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-01 | **Product:** QPTM (My Quorum Gas Pipeline)
**Scope:** NON-EDI inbound/outbound integrations & APIs, file imports/exports (FlowCal, MV90, OSI PI, IPWS/EBB, AP/GL), data sync between systems (PTR/TIPS, PGAS, ROME, CRS), batch/scheduled job failures (PANIGHTLY, ALALLOCATE, balancing, billing exports), queue/processing issues, and **QQM** reporting.
**Companion:** For EDI transport (NMST/NMQR, ENMQR/EEDM codes, EDI server connectivity, PGP keys, cycle deadlines) see **SKILL_EDI_Troubleshooting.md** — EDI nomination traffic is out of scope here; cross-references noted below. For nom-overlap/duplicate/ghost-nom delete scripts see **SKILL_Nominations.md §4**.

> **What is QQM?** Mined from the cases, **QQM = Quorum Query Manager** — QPTM's **SAP BusinessObjects–based reporting / universe layer** (a separate report-server tier, not an in-app screen). Evidence: 22-00827445 "Business Objects Universe", 22-00876134 "Users not able to run reports", 22-00592373 "column needs redefined from Dimension to Measure" (BO universe terms), 22-00940368 "Apache Log4j…vulnerabilities" (Java report server), 22-00712617 "shutting down QQM servers". QQM issues are almost all **report-data correctness, universe definition, scheduling, or report-server admin** — classify them as Reporting/Config, NOT as core QPTM processing defects. Cross-link **SKILL_Reporting_Regulatory_Postings.md** for in-app report screens.

> **Evidence base:** ~750 closed QPTM Integration/Processing/QQM cases. This guide is built on the **217 actionable** ones (Software Defect 52, Application Configuration 86, Customer Error 43, Training 36). Every claim below cites a real SF case# and/or ADO work item.

---

## TABLE OF CONTENTS
1. [Quick Triage Checklist](#1-quick-triage-checklist)
2. [Integration & Processing Concepts](#2-integration--processing-concepts)
3. [Symptom → Root-Cause Matrix](#3-symptom--root-cause-matrix)
4. [Cluster Counts](#4-cluster-counts-actionable-cases)
5. [Batch / Scheduled Job Failures (HIGHEST VOLUME)](#5-batch--scheduled-job-failures-highest-volume)
6. [File Import — FlowCal / MV90 / Measurement / Gas Quality](#6-file-import--flowcal--mv90--measurement--gas-quality)
7. [File Export — IPWS/EBB, AP/GL, Billing, CW* Interfaces, OSI PI](#7-file-export--ipwsebb-apgl-billing-cw-interfaces-osi-pi)
8. [SFTP / FTP Transport](#8-sftp--ftp-transport)
9. [PTR / TIPS Cross-Product Sync (Evolution / Midstream)](#9-ptr--tips-cross-product-sync-evolution--midstream)
10. [Allocation / Balancing / Imbalance Processing](#10-allocation--balancing--imbalance-processing)
11. [QQM (Quorum Query Manager) Reporting](#11-qqm-quorum-query-manager-reporting)
12. [QEMAIL / Notifications](#12-qemail--notifications)
13. [Key Code Files & Repos](#13-key-code-files--repos)
14. [Database Tables Reference](#14-database-tables-reference)
15. [Diagnostic SQL Queries](#15-diagnostic-sql-queries)
16. [Verbatim Fix Scripts (redacted)](#16-verbatim-fix-scripts-redacted)
17. [Known Historical ADO Bugs](#17-known-historical-ado-bugs)
18. [Expected Behavior / User Education](#18-expected-behavior--user-education)
19. [Escalation Decision Tree](#19-escalation-decision-tree)

---

## 1. Quick Triage Checklist
```
[ ] 1. Is it an IMPORT (into QPTM), an EXPORT (out of QPTM), or an internal BATCH process?
[ ] 2. Exact process/job name? (PANIGHTLY, ALALLOCATE, CWINTRTRAN, GBGALLOAD, OSIPICSV, MV90, BLSOAIMP…)
[ ] 3. Process Queue ID (PQID) and the exact error/warning text? ("completed with errors" ≠ "failed")
[ ] 4. Which TSP_NO and environment (PRD / UAT / DEV / which pod e.g. A1/B1)?
[ ] 5. Is the EXTERNAL system the source of truth (FlowCal, MV90, PGAS, OSI PI, ROME, CRS)?
[ ] 6. Did it work before? What changed — UPGRADE, new build, env refresh, file-path/SFTP change?
[ ] 7. Scheduled (Schedule Definition) or manually launched? Is the schedule even active?
[ ] 8. Is the job HUNG (QUE status) vs ERRORED vs producing WRONG DATA?
[ ] 9. For QQM: is it report DATA wrong, report won't RUN, scheduling, or report-SERVER admin?
[ ] 10. EDI-related (NMST/NMQR/EEDM/EDI server)? → STOP, use SKILL_EDI_Troubleshooting.md.
```

### Where does it live?
| Symptom | Cluster | First place to look |
|---|---|---|
| `PANIGHTLY`/`ALALLOCATE`/balancing job errors or hangs | §5 Batch | Process Queue (PQID), process step, prerequisite data |
| FlowCal/MV90/gas-quality measurement not importing | §6 Import | SFTP landing, import def file path, source-DB extract |
| IPWS/EBB postings missing or wrong TSP | §7 Export | Export def, TSP config, IPWS SFTP |
| AP/GL/billing/CCS/CRS export wrong or failing | §7 Export | `QARCH_CTRL_IMPEXP`, export overwrite flag |
| `CWINTRTRAN`/`CWCAPRTRAN`/`CWINDXCUST` error | §7 CW* | File path config, env-specific path pointing at wrong pod |
| SFTP "cannot connect" / file stuck on SFTP | §8 SFTP | FTP connection config, credentials, firewall |
| PTR overriding manual values / TIPS dependency | §9 PTR | PTR overlay process, WGT attribute, cash-out flag |
| Report data wrong / report won't run | §11 QQM | BO universe definition, effective-dating, report server |
| QEMAIL / notice email not sending | §12 Email | SMTP server config, QEMAIL setup |

---

## 2. Integration & Processing Concepts

### Batch process model
QPTM work runs through **batch processes** launched from the **Batch Process Execution** window (Web) or scheduled via **Schedule Definitions**. Each run gets a **Process Queue ID (PQID)** and a status:
- **COMPLETED** — clean.
- **COMPLETED WITH ERRORS / WARNINGS** — ran, but some rows/steps failed (very common; usually **data**, not a code defect — 24-00993609, 25-01051859, 25-01006449).
- **ERROR / FAILED** — the step itself died (config, missing data, truncation, FK).
- **QUE / hung** — never picked up by the queue handler; often an infrastructure/queue-handler issue, not the job (25-01004842, 25-01012625).

A process is defined by a **Batch Process Definition** + **Parameters/Picklist** metadata; if the definition or its parameter/picklist metadata isn't checked-in to an environment, the job **won't appear in the picklist** or runs with **missing parameters** (24-00993020, 25-01008695, 25-01037771, 26-01098795, 24-00949543).

### Import vs Export interfaces
- **Imports** pull external data into QPTM staging then apply it: measurement (FlowCal/MV90/gas-quality), prices (QCM), noms (OSI PI nom import), statements (BLSOAIMP).
- **Exports** push QPTM data out: IPWS/EBB postings, AP/GL/journal, billing (CCS/CRS), index-of-customers (CWINDXCUST), operational capacity (CWOPERCAP), RDD/PCC.
- Both are driven by **Import/Export definitions** with a **file path** and (for exports) flags like **`EXP_OVERWRITE_FILE_IND`** in `QARCH_CTRL_IMPEXP`. A huge share of cases are simply a **wrong/stale file path or SFTP endpoint** after an upgrade or env refresh.

### Cross-product data flow
QPTM exchanges data with **TIPS** (PTR/measurement, "Evolution"/Midstream projects), **FlowCal** (measurement, often via E-Suite/ESUITE), **MV90** (meter translation), **OSI PI** (real-time), **PGAS**, **ROME** (imbalance), **CRS/CCS** (billing). These interfaces are the bulk of the Integration category.

---

## 3. Symptom → Root-Cause Matrix

| Symptom (message / behavior) | Most common root cause | Fix type | Evidence |
|---|---|---|---|
| Batch "COMPLETED WITH ERRORS" on a few rows | Bad/missing source data (orphaned detail w/o header, missing day) | Data review / data script | 25-01006213, 24-00993609, 25-01051859 |
| Job HUNG in QUE status, nothing running | Queue handler / infra, not the job | Infrastructure | 25-01004842, 25-01012625, 25-01017346 |
| Job "not showing in picklist" / params missing in Web | Batch-process definition or parameter/picklist metadata not checked-in to that env | Config (check-in metadata) | 26-01098795, 25-01037771, 24-00949543, 25-01008695 |
| PANIGHTLY failing after upgrade/metadata change | Process-step metadata wrong for that client | Config / code | 24-00995528 (ADO #1705412), 25-01038437 (#1751637) |
| Truncation error on insert (e.g. ALALLOCATE) | Target column too short for incoming value | Data script (ALTER column length) | 25-01046183 |
| "duplicate key" / "primary key" on allocation/CICO | Missing days / bidirectional needs zero-noms, or re-run over existing rows | Config / data | 25-01055410, 25-01036204, 26-01063368 |
| FlowCal/MV90 measurement not importing | Wrong import def file path / SFTP filename / source extract empty | Config / customer-side | 23-00926020, 25-01021236, 24-00954023, 25-01013727 |
| MV90 mishandling dates after 2025 | Date-parse defect in MV90 translation | Code fix | 26-01063597, ADO #1691307 |
| IPWS posting missing / wrong TSP posted | Export def / TSP config; invalid TSP in posting export | Config / code | 26-01082546, 24-00993283, 22-00565430 |
| Export producing TRIPLE/DUPLICATE values (RDD/PCC) | Export overwrite flag off → appends instead of overwriting | Config script (`EXP_OVERWRITE_FILE_IND=1`) | 24-00992623, ADO #1705697 |
| CWINTRTRAN/CWCAPRTRAN/CWINDXCUST error | File path points at wrong env/pod | Config (fix path) | 25-01002835, 25-01002841, 25-01025889, 24-00954614 |
| SFTP "cannot connect" / file won't process | FTP connection config, credentials, firewall; re-add path | Config / infra | 24-00982650, 25-01034768, 25-01042793, 24-00960816 |
| PTR overlay overriding manual PTR / zeroing PPA | PTR overlay sync defect (skips/overrides protected rows) | Code fix | 22-00827029, 22-00609003, 22-00603656 |
| QPTM step depends on a TIPS step that's done | Cross-product dependency defect | Code fix | 24-00972705 (ADO #1681831) |
| Orphaned location stops ALL jobs in a TSP | Orphaned `KATYPOOL`/loc rows referenced across tables | Data script (delete loc rows) | 24-00951885 (ADO #1660692) |
| QQM report data ≠ QPTM app | BO universe mapping / effective-dating defect | Code/universe fix | 22-00592312, 22-00597391, 22-00592372 |
| QQM report won't run / crashes / slow | Report-server memory / Log4j / config | Infra / config | 22-00521666, 22-00876134, 24-00940368 |
| QEMAIL / notice email not sending | SMTP server config invalid for env | Config | 24-00940028, 25-01057894, 24-00950093, 26-01084197 |

---

## 4. Cluster Counts (actionable cases)

**Software Defect + Application Configuration (138):**
| Count | Cluster |
|---|---|
| 29 | Batch / scheduled job failure (incl. picklist/def-missing-in-Web) |
| 15 | FlowCal / MV90 / measurement / gas-quality import |
| 13 | QQM reporting / universe |
| 10 | PTR / TIPS sync (Evolution/Midstream) |
| 9 | IPWS / EBB posting |
| 8 | SFTP / FTP transport |
| 5 | Billing / GL / AP export |
| 4 | CW* interface exports (CWINTRTRAN/CWCAPRTRAN/CWINDXCUST/CWOPERCAP) |
| 4 | Allocation / balancing / imbalance |
| 4 | QEMAIL / notifications |
| ~37 | Other (CAS cuts, code-table check-ins, hotfix rollups, perf RCAs, env refresh) |

**Customer Error + Training (79):** dominated by **QQM (20)** and **Batch job questions (9)** — i.e. mostly "how does this job/report work" and "my file/data is wrong", not product defects. See §18.

---

## 5. Batch / Scheduled Job Failures (HIGHEST VOLUME)

The single largest cluster. Triage by the **status** first (§2): *completed-with-errors* (data), *hung/QUE* (infra), *failed* (config/data), *missing-from-picklist* (metadata check-in).

### 5a. "Completed with errors / warnings"
Usually a small set of **bad/missing data rows**, not a code bug. Pull the PQID log and find the erroring row.
- **RTVALDDSRT** (25-01006213, **Data Script Provided**): several **detail records had a missing header**; client ran multiple processes simultaneously creating orphaned detail. Fix = data script to clean the orphans. RCA in resolution: *"detail records in the database but not in the system."*
- **PANIGHTLY / inventory / balancing "warnings"** (25-01002193, 24-00993609, 25-01000765, 25-01002477): inventory/account warnings are frequently **expected** or data-config, resolved by *Configuration Changed* / education.
- Customer-error variants (educate, don't script): ALESVOLIMP (25-01051859), CANOMCLTG (25-01006449), ALALLOCATE completed-with-errors (24-00962876).

### 5b. Hung / QUE status (infrastructure)
25-01004842 ("hung in UAT since 2/10 / QUE status"), 25-01012625 ("automated processes are not running"), 25-01017346 ("Allocation process failing" — DB **didn't capture a new time-slice EFF_DT_TO**; fix was to toggle the Effective-Date-To and revert it to force the DB trigger). These resolve via **Infrastructure Resolved** or a small data nudge — check the **queue handler / middle-tier** before assuming a job defect.

### 5c. Missing from picklist / params missing in Web (metadata check-in)
When migrating Classic→Web or across envs, the **Batch Process Definition** and its **Parameter/Picklist** metadata must be checked-in:
- 26-01098795 "EDI Batch Process Not Showing in Picklist", 25-01037771 "Interfaces category missing from Batch Process Execution window", 25-01030566 "Missing Jobs under Import A Data File", 24-00949543 "BLSOAIMP not present in Web", 25-01008695 "Batch job parameters missing in web" (**Software Updated**, ADO confirms code path), 24-00993020 / 24-00988518 (parameter/picklist check-in).
- **Fix:** check-in the process definition + parameter/picklist metadata to the target environment.

### 5d. Real defects (Software Updated)
- **REX PANIGHTLY Failing** — 24-00995528, **ADO #1705412 (Bug/Closed)**; sibling metadata defect 25-01038437 = **#1751637 (Bug/Closed)**, plus XCL intermittent #1616200 / #1620218.
- **PAPOSTENRL job stopped running** — 24-00950223 (Software Updated).
- **CWOPERCAP results in error** — 24-00948503 (Software Updated).
- **UTIL_RESEED_IDENTITIES procedure changed by new build** — 25-01017806 (Software Updated; a build regression to the reseed proc — relevant to the §4 ghost-nom reseed note in SKILL_Nominations).

### Diagnostic
```sql
-- Recent runs of a named process (status + error)
SELECT PROC_QUEUE_ID, PROC_NM, TSP_NO, STATUS_CD, SUBMIT_DT, START_DT, END_DT, ERROR_MSG
FROM QARCH_PROC_QUEUE
WHERE PROC_NM = '<PROCESS_NAME>' AND SUBMIT_DT >= TRUNC(SYSDATE)-7
ORDER BY SUBMIT_DT DESC;

-- Step-level detail for one PQID (which step failed)
SELECT STEP_NO, STEP_NM, STATUS_CD, ERROR_MSG, START_DT, END_DT
FROM QARCH_PROC_QUEUE_STEP
WHERE PROC_QUEUE_ID = <PQID> ORDER BY STEP_NO;
```
> Table/column names above are the canonical QPTM process-queue pattern; confirm exact names against the client schema (varies Oracle vs SQL Server). The actionable signal is **status + the failing step's error text**.

---

## 6. File Import — FlowCal / MV90 / Measurement / Gas Quality

Measurement is QPTM's biggest inbound feed. Two recurring failure modes: (a) **the file/extract never arrives or is wrong** (customer/source side); (b) **the import definition path/filename is wrong** (config).

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| FlowCal→QPTM measurement not importing (via E-Suite/ESUITE) | Interface/process category or path misconfig | Config | 23-00926020, 23-00915392, 24-00945344, 25-01026412 |
| Measurement "missing for July" / "not in FlowCal" | **Source extract empty** — data not in FlowCal yet | Educate (customer-side) | 25-01031931, 26-01096082, 22-00513489 |
| Scheduled-vs-Measured report missing measured qty | FlowCal extract didn't land; **workaround = run query on FlowCal DB, drop file on FTP** | Workaround / code | 25-01013727 |
| MV90 mishandling dates after 2025 | Date-parse defect in MV90 translation program | Code fix | **26-01063597** |
| MV90 import into PGAS not working | MV90 import defect | Code fix | 24-00976811, **ADO #1684017 (Bug/Closed)** |
| MV90 batch process wiped after upgrade | Upgrade dropped the process/script | Re-create / code | **ADO #1691307 (Active)**, #1693312 |
| GBGALLOAD / GBGALOAD / GBDAILLOAD not importing gas-quality / not updating Gas Analysis Search | SFTP file not landing / import def path / filename config | Config | 24-00953851, 24-00960485, 24-00972786, 25-01009965 |
| GASQUALITY2 XML import def file path wrong | Path config after env change | Config | 24-00954023 |
| Gas Quality Report not loading data | Report-data defect | Code fix | 24-00993275 |
| WHMEASIMP / wellhead measurement refinement (WGT attr) | Process needs to respect WGT-attribute flag | Code fix | 24-00944126; education variant 24-00961609 |

### Diagnostic
- Confirm the file actually **landed on SFTP** (§8) and matches the **import def filename pattern** (filenames are the #1 culprit after env refresh — 24-00969291, 25-01000170).
- For FlowCal: confirm the data exists **in the FlowCal DB / E-Suite** for that month/meter before blaming QPTM (25-01031931).
- Compare the import **definition file path** PRD vs UAT — paths frequently point at the wrong pod after a refresh.

---

## 7. File Export — IPWS/EBB, AP/GL, Billing, CW* Interfaces, OSI PI

### 7a. IPWS / EBB postings
IPWS = the public **Internet Posting / EBB**. Postings flow QPTM→IPWS via SFTP.
| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Notice posting not reaching IPWS | Export def / IPWS SFTP / TSP config | Config | 26-01082546, 24-00980101 |
| TSP posting to IPWS that shouldn't be | TSP/posting config | Config | 24-00993283 |
| Posting export using **invalid TSP** | Export-side defect | Code fix | 22-00565430 |
| IPWS locations download for specific TSPs | Loc-download config | Config | 25-01037716 |
| Can't connect to IPWS SFTP | SFTP/credentials | Config/infra | 24-00982650 |
| Older IPWS records purge question | Educate (retention) | Education | 25-01059639 |

### 7b. Billing / AP / GL / Journal / CCS / CRS exports
| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **RDD/PCC export TRIPLING/DUPLICATING values** | `EXP_OVERWRITE_FILE_IND` off → file appended each run | **Config script set flag = 1** (§16) | **24-00992623, ADO #1705697 (Bug/Closed)** |
| Billing CCS export failing | Export defect | Workaround/code | 24-00968265 |
| CRS Billing export error | Path/config | Config | 25-01032633 |
| AP & GL exports | Export config | Config | 26-01064051 |
| Journal Entry export "incorrect formatting" | Customer expectation / format | Educate | 24-00950432 |
| Invoice payment errors | Config | Config | 25-01012869 |

### 7c. CW* interface exports
`CWINTRTRAN`, `CWCAPRTRAN`, `CWINDXCUST`, `CWOPERCAP`, `CWFIRMTRAN` — capacity/index/operational-capacity export jobs. The dominant root cause is a **file path pointing at the wrong environment/pod** after a refresh.
- 25-01002835 / 24-00954614 (CWINTRTRAN), 25-01021126 (CWINTRTRAN scheduled), 25-01002841 (CWCAPRTRAN), 25-01023194 / 25-01025889 (CWINDXCUST — UBTA1 path pointing at PRDA1), 24-00948503 (CWOPERCAP error → Software Updated), 24-00966155 (CWFIRMTRAN logic — education).

### 7d. OSI PI
- OSIPICSV batch errors (25-01034768) — **FTP server issue; re-add the path** in the app. OSI PI export via SFTP (24-00950726, 25-01051027). OSI PI nom-import schedule (25-00998139).

---

## 8. SFTP / FTP Transport

A cross-cutting cause behind many §6/§7 cases. The interface itself is fine — the **FTP connection config, credentials, or firewall** is wrong, or a file is **stuck** on the server.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| FTP connection "not properly configured" | FTP connection record wrong | Config | 25-01042793 (TESTXCLRSBL) |
| Can't connect to IPWS SFTP | Endpoint/credentials | Config/infra | 24-00982650 |
| OSIPICSV / file won't process — re-add path fixes it | Stale FTP path object | Config (remove+re-add path) | 25-01034768 |
| Emails/files blocked by firewall | Network/firewall | Infra | 24-00960816 |
| File stuck on SFTP, needs clearing | Orphaned file | Ops (clear file) | 24-00956198 |
| SFTP credentials for new env | New-env setup | Config | 25-01020644, 25-00999691 |
| "Problem with SFTP site" | Endpoint/config | Config | 25-01021771 |

> **Pattern:** the single most reliable fix for "FTP path not working" is to **delete and re-add the FTP/path object** in the app (25-01034768) — the stored path object goes stale after an env refresh.

---

## 9. PTR / TIPS Cross-Product Sync (Evolution / Midstream)

QPTM and **TIPS** exchange measurement & **PTR** (point/plant theoretical recovery) data on Midstream ("Evolution") clients (ETP/ENT, XCL, Permian/Midland/STX plants). The recurring defect family: **PTR overlay overriding values it should protect**, or **QPTM steps wrongly depending on a TIPS step**.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| PTR overlay overriding **manually-overridden** PTR (PPA months) | Overlay sync ignores manual-override protection | Code fix | 22-00827029 |
| Interface 2 — PTR incorrectly overriding to **zero** for PPA months w/ no changes | Overlay zeroing unchanged rows | Code fix | 22-00609003 |
| Interface 3 — writing records to TIPS when **no data exists** in latest `BLTRAN_STAG_IMB_OVRLY` run | Stage-table guard missing | Code fix | 22-00609005 |
| PTR overlay sync **skipping repeat meters** (Permian) | Iteration defect | Code fix | 22-00603656 |
| Meas file overriding manual measurement adjustment on PPA | Overlay protection | Workaround/code | 22-00683173 |
| Wellhead approve/un-approve not working (STX) | Process defect | Code fix | 24-00953268 |
| PTR overlay gives no errors / no child steps when PTR attr not set | Missing error handling | Code fix | 24-00960932 |
| QPTM steps shouldn't depend on TIPS step after PTR approval done | Cross-product dependency | Code fix | **24-00972705, ADO #1681831 (Bug/Closed)** |
| Prelim-imbalance cashing out contracts NOT set for cash-out | Cash-out flag not honored | Code fix | 24-00941492 |
| Purge prior prelim-imbalance cash-out runs | Re-run/purge defect | Code fix | 24-00939615 |
| GENPTRPRM2 success but no PTR records for plant | Config (plant/accounting-month setup) | Config | 24-00941956 |
| Inactive plants run to pick up plant fuel but no wellhead activity | Setup/config | Config | 24-00939388 |

> **Tell-tale:** if the complaint is "my **manual override** got wiped" or "PTR went to **zero**", it's the overlay-protection defect family (22-00827029 / 22-00609003) — escalate as a code bug, don't just re-enter the data.

---

## 10. Allocation / Balancing / Imbalance Processing

(Core allocation logic lives in **SKILL_Allocations.md** — this section covers the *processing/job* angle only.)

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **ALALLOCATE truncation error** | Target column too short for incoming value | **Data script: ALTER column length** (§16) | 25-01046183 |
| Allocation "duplicate key" (bidirectional/MEP, closed meas month) | Missing days need **zero noms** entered for deliveries | Config / customer data | 25-01055410 |
| CICO primary-key errors (INDAYIMBCI/INACCTBAL) | Re-run over existing rows / data | Educate / RCA | 25-01036204 |
| Allocation process failing — DB didn't capture new time-slice | Toggle EFF_DT_TO then revert to fire DB trigger | Infra/data nudge | 25-01017346 |
| Add a PreStep validation to IM_IMBALCI | Add validation step | Data/config script | 24-00965152 |
| Balancing job / Blackfin test | Job config | Config | 25-01000758, 25-01021036 |

---

## 11. QQM (Quorum Query Manager) Reporting

**QQM = SAP BusinessObjects–based reporting layer** (separate report-server tier). Issues split into **(a) report data correctness / universe definition**, **(b) report won't run / performance**, **(c) scheduling**, **(d) report-server admin**. Most QQM cases are **Customer Error / Training** (the report or the data, not a product bug) — classify carefully.

### 11a. Universe / data-correctness defects (Software Updated)
- **Report data ≠ QPTM app** — 22-00592312.
- **Effective-dating not applied** to measurement (Location Contact OPR/AG1/AG2) — 22-00597391; **Heat Content Factor not effective-dated** — 22-00592372; **parent/child measurement hierarchy** tie-out — 22-00597575, 22-00597388 (BAs see child loc after re-parent), 22-00597535.
- **Column needs redefined Dimension→Measure** (a BO universe edit) — 22-00592373.
- **Point-specific records missing from QQM class** — 22-00806193.

### 11b. Won't run / performance / server
- Reports slow / crash during updates → **memory allocation adjustment** (22-00521666, resolution: *"Memory allocation adjustments"*); PPA Complex Price/Volume report hangs (22-00521667).
- Users can't run reports (22-00876134, **Software Update Available**).
- Apache **Log4j 1.x** vulnerabilities on the QQM (Java) report server (24-00940368) — patch/upgrade.
- Business Objects Universe – Upstream Capacity Release (22-00827445).

### 11c / 11d. Scheduling & admin (mostly Customer Error / Training)
- Two report instances for one schedule (22-00666877); report not sent by email (22-00515573); report scheduling functionality request (22-00597420 — enhancement); shutting down QQM servers (22-00712617); QQM user issue (22-00675883); DTH-vs-MCF report differences (22-00516846 — expected, unit difference).

> Many QQM cases are an **OH (Ohio)** go-live cluster (22-005923xx / 22-005973xx). For in-app (non-BO) report screens, see **SKILL_Reporting_Regulatory_Postings.md**.

---

## 12. QEMAIL / Notifications

QPTM sends notice/alert emails via **QEMAIL** through an SMTP server. Nearly all failures are **SMTP config invalid for the environment** (especially UAT).
- 24-00940028 (UAT SMTP not valid), 25-01057894 (QEMAIL SMTP error), 24-00950093 (QEmail error sending), 26-01084197 (v2025.10 QEMAIL errors), 25-01054894 (notice email), 26-01082092 (informational alerts), 24-00960816 (firewall blocking email), 25-01017559 (service-disruption subscription — education).
- **Fix:** verify the SMTP host/port/relay config in the email/system settings for that env; UAT often lacks a valid relay by design.

---

## 13. Key Code Files & Repos

> Integration/processing logic spans batch, interface-framework, and DB repos. Use ADO code search to confirm exact paths per release/client; the table is the orientation map (consistent with SKILL_EDI/Nominations repo IDs).

| Repo | GUID | Relevant area |
|---|---|---|
| Quorum.QPTM.Batch | e024d80b-5c45-411c-93e1-78e2798ed885 | PANIGHTLY, ALALLOCATE, import/export interfaces, PTR overlay, balancing |
| Quorum.QPTM.Web | 41e317c0-844c-4728-98da-529092957738 | Batch Process Execution window, schedule defs, picklist/param metadata |
| APL.QPTM.Database | 2e1fb9e5-a46a-4257-b99a-fd47721dd399 | QARCH_CTRL_IMPEXP, process-queue, interface staging tables |
| Quorum.EDIServ | 30cdad90-e4ae-405c-8d67-747955bcf870 | EDI transport only — see SKILL_EDI_Troubleshooting.md |
| `<CLIENT>.QPTM.*` | — | Client overrides of interface defs / process steps (XCL, ENT/ETP, CSU, HEP, TEP, MGD) |

**Process/interface names seen in cases** (search these in code/metadata): `PANIGHTLY`, `ALALLOCATE`, `RTVALDDSRT`, `BLSOAIMP`, `BLROLLDATE`, `BLEXPROME`, `PAPOSTENRL`, `CWINTRTRAN`, `CWCAPRTRAN`, `CWINDXCUST`, `CWOPERCAP`, `CWFIRMTRAN`, `GBGALLOAD`/`GBGALOAD`/`GBDAILLOAD`, `WHMEASIMP`, `PERPTRSYNC`, `GENPTRPRM2`, `OSIPICSV`, `GASQUALITY2`, `IM_IMBALCI`, `ALLOC_CUV`, `MV90`.

---

## 14. Database Tables Reference

| Table | Purpose |
|---|---|
| `QARCH_PROC_QUEUE` / `QARCH_PROC_QUEUE_STEP` | Batch process queue runs + step status/errors (PQID) |
| `QARCH_CTRL_IMPEXP` | **Import/Export definitions** — file path, `EXP_OVERWRITE_FILE_IND`, `IMPEXP_ID`, `APP_LAYER_CD` (RDD/PCC overwrite fix, 24-00992623) |
| `QARCH_XREF_CDTBL_VALU_META_MOD` | Code-table cross-ref metadata (missing-code-table case 24-00947584) |
| `BLTRAN_STAG_IMB_OVRLY` | Imbalance-overlay **staging** table (TIPS Interface 3 guard, 22-00609005) |
| `PACTRL_LOC_ATTR` / `_FLAT` / `PACTRL_SYS_LOC_GRP_LOC` / `_FLAT` / `PACTRL_LOC_USER_DEF` / `PACTRL_LOC_CAP` / `PAVALD_LOC` | Location attribute/group tables — orphaned-loc cleanup (KATYPOOL, 24-00951885) |
| `KCTRL_CTR_LOC` | Contract↔location link (orphaned-loc cleanup) |
| `SEXTN_MTR_HEADER_QPTM` | Meter header extension (orphaned-meter cleanup) |
| `KCTRL_CTR_AGENT` / `KCTRL_BP_AGENT` | Agent tables hammered by Offer Viewer (perf RCA 24-00966750) |
| `KATYPOOL` (location) | The orphaned location in 24-00951885 |

---

## 15. Diagnostic SQL Queries

### A. Find recent runs / errors for a process
```sql
SELECT PROC_QUEUE_ID, PROC_NM, TSP_NO, STATUS_CD, SUBMIT_DT, START_DT, END_DT, ERROR_MSG
FROM QARCH_PROC_QUEUE
WHERE PROC_NM = '<PROCESS_NAME>'        -- e.g. 'PANIGHTLY','ALALLOCATE','CWINTRTRAN'
  AND SUBMIT_DT >= TRUNC(SYSDATE)-7
ORDER BY SUBMIT_DT DESC;
```

### B. Which step failed for a PQID
```sql
SELECT STEP_NO, STEP_NM, STATUS_CD, ERROR_MSG, START_DT, END_DT
FROM QARCH_PROC_QUEUE_STEP
WHERE PROC_QUEUE_ID = <PQID>
ORDER BY STEP_NO;
```

### C. Inspect an import/export definition (path + overwrite flag)
```sql
SELECT IMPEXP_ID, APP_LAYER_CD, DIRECTION_CD, FILE_PATH, FILE_NM_PATTERN,
       EXP_OVERWRITE_FILE_IND, FTP_CONN_ID, IS_ACTIVE
FROM QARCH_CTRL_IMPEXP
WHERE IMPEXP_ID = '<INTERFACE_ID>';     -- e.g. 'CSURDD','CSUPCC','CWINTRTRAN'
-- Red flags: file path pointing at the WRONG env/pod; EXP_OVERWRITE_FILE_IND = 0 on a job
-- that should overwrite (RDD/PCC tripling — 24-00992623).
```

### D. Orphaned-location check (jobs failing TSP-wide — 24-00951885)
```sql
-- Find a LOC_ID present in attribute/group tables but no longer a valid location
SELECT 'PACTRL_LOC_ATTR' tbl, COUNT(*) n FROM PACTRL_LOC_ATTR WHERE LOC_ID='<LOC_ID>'
UNION ALL SELECT 'KCTRL_CTR_LOC', COUNT(*) FROM KCTRL_CTR_LOC WHERE LOC_ID_2='<LOC_ID>'
UNION ALL SELECT 'SEXTN_MTR_HEADER_QPTM', COUNT(*) FROM SEXTN_MTR_HEADER_QPTM WHERE MTR_NO='<LOC_ID>';
```

### E. Staging-table guard (TIPS imbalance overlay — 22-00609005)
```sql
-- Confirm the latest overlay run actually has data before it writes to TIPS
SELECT RUN_ID, COUNT(*) row_cnt, MIN(GAS_DAY), MAX(GAS_DAY)
FROM BLTRAN_STAG_IMB_OVRLY
WHERE TSP_NO = <TSP_NO>
GROUP BY RUN_ID ORDER BY RUN_ID DESC;
```

---

## 16. Verbatim Fix Scripts (redacted)

> Captured **verbatim from ADO attachments** via PAT. Concrete IDs/users/dates redacted to `<PLACEHOLDER>`; **real table/column names and logic kept intact.** Always run a verify-SELECT and confirm the row count before applying.

### Script A — Export overwrite flag (RDD/PCC tripling fix)
> Source: ADO **#1705697** attachment `1705697 - CSURDD and CSUPCC Overwrite - Oracle.sql` (CSU, case 24-00992623). The export jobs were **appending** each run because `EXP_OVERWRITE_FILE_IND` was off; setting it to 1 makes each run overwrite the file (fixes the triple/duplicate values). Deployed as a QDBMGR MDC script.
```sql
-- Set export definitions to OVERWRITE the output file (not append) per run.
-- Params: <IMPEXP_ID> (e.g. 'CSUPCC','CSURDD'), <APP_LAYER_CD> (e.g. 'QCSU'), <USER_ID>
BEGIN
  UPDATE QARCH_CTRL_IMPEXP
     SET EXP_OVERWRITE_FILE_IND = 1,
         UPDT_DT = TO_DATE('<YYYY-MM-DD HH24:MI:SS>','YYYY-MM-DD HH24:MI:SS'),
         USER_ID = '<USER_ID>'
   WHERE IMPEXP_ID = '<IMPEXP_ID_1>' AND APP_LAYER_CD = '<APP_LAYER_CD>';

  UPDATE QARCH_CTRL_IMPEXP
     SET EXP_OVERWRITE_FILE_IND = 1,
         UPDT_DT = TO_DATE('<YYYY-MM-DD HH24:MI:SS>','YYYY-MM-DD HH24:MI:SS'),
         USER_ID = '<USER_ID>'
   WHERE IMPEXP_ID = '<IMPEXP_ID_2>' AND APP_LAYER_CD = '<APP_LAYER_CD>';
END;
/
-- Verify first:  SELECT IMPEXP_ID, EXP_OVERWRITE_FILE_IND FROM QARCH_CTRL_IMPEXP
--                WHERE IMPEXP_ID IN ('<IMPEXP_ID_1>','<IMPEXP_ID_2>');
```

### Script B — Orphaned-location cleanup (jobs failing TSP-wide)
> Source: ADO **#1660692** attachment `WWM Script.sql` (WWM, case 24-00951885). An orphaned location set up only in one TSP (`KATYPOOL` / `ATPKTYMXP`) left dangling rows that made **every** batch job in any TSP stop with a warning. The fix deletes the location's rows across all attribute/group/contract/meter tables. **Run the verify-SELECTs (Diagnostic §15D) first; delete in this order.**
```sql
-- Params: <LOC_ID> (e.g. the orphaned location/meter code)
DELETE FROM PACTRL_LOC_ATTR            WHERE LOC_ID = '<LOC_ID>';
DELETE FROM PACTRL_LOC_ATTR_FLAT       WHERE LOC_ID = '<LOC_ID>';
DELETE FROM PACTRL_SYS_LOC_GRP_LOC     WHERE LOC_ID = '<LOC_ID>';
DELETE FROM PACTRL_LOC_USER_DEF        WHERE LOC_ID = '<LOC_ID>';
DELETE FROM PACTRL_LOC_CAP             WHERE LOC_ID = '<LOC_ID>';
DELETE FROM PACTRL_SYS_LOC_GRP_LOC_FLAT WHERE LOC_ID = '<LOC_ID>';
DELETE FROM KCTRL_CTR_LOC              WHERE LOC_ID_2 = '<LOC_ID>';
DELETE FROM PAVALD_LOC                 WHERE LOC_ID = '<LOC_ID>';
DELETE FROM SEXTN_MTR_HEADER_QPTM      WHERE MTR_NO = '<LOC_ID>';
```

### Script C — Column-length truncation fix (ALALLOCATE)
> Source/pattern: case 25-01046183 (**Data Script Provided**, resolution: *"Script for altering column length was run"*). The verbatim ALTER was not in an ADO attachment; reconstructed pattern below — confirm the exact table/column from the truncation error text before running.
```sql
-- ALALLOCATE failed inserting a value longer than the target column.
-- Identify the column from the error, then widen it:
ALTER TABLE <TARGET_TABLE> MODIFY ( <COLUMN_NAME> VARCHAR2(<NEW_LEN>) );   -- Oracle
-- (SQL Server:  ALTER TABLE <TARGET_TABLE> ALTER COLUMN <COLUMN_NAME> VARCHAR(<NEW_LEN>); )
```

> **Other script-attachment cases (titles confirmed, binary in SF):** RTVALDDSRT orphan-detail cleanup (25-01006213), IM_IMBALCI pre-step add (24-00965152), MGD copy scheduled definitions PRD→UAT (24-00966480). For nom-overlap delete scripts use **SKILL_Nominations.md §4 Templates A/B**.

---

## 17. Known Historical ADO Bugs

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1705412** | Bug / Closed | TEP — REX PANIGHTLY Failing | §5 Batch | 24-00995528 |
| **#1751637** | Bug / Closed | GBG — Metadata Changes for PANIGHTLY Midstream Process Step | §5 Batch | 25-01038437 |
| #1616200 | Bug / Closed | XCL_PRD17 — Intermittent PANIGHTLY processing issues | §5 Batch | — |
| #1620218 | Incident / Closed | XCL — PANIGHTLY processes stopping with errors | §5 Batch | — |
| #1711651 | Requirement / Ready for QA | HEP — PANIGHTLY process check-in | §5 Batch | — |
| **#1705697** | Bug / Closed | CSU — CSU_PCC_EX/CSU_RDD_EX producing triple/duplicate values | §7 Export | 24-00992623 |
| **#1681831** | Bug / Closed | ENT — ETP/Permian/Midland should not depend on TIPS step after PTR approval (+ #1683882/#1683883 QA/DEV) | §9 PTR | 24-00972705 |
| **#1660692** | Bug / Closed | F/V (WWM) — Jobs stopping with orphaned-record warning in KATYPOOL | §5 / §16B | 24-00951885 |
| **#1684017** | Bug / Closed | MV90 import into PGAS not working | §6 Import | 24-00976811 |
| **#1691307** | Bug / Active | XCL — MV90 Batch Process wiped after upgrade (ESUITE PRDA1) | §6 Import | — |
| #1693312 | Database Change / Rejected | XCL — Update MV90 batch process script | §6 Import | — |

> **Takeaway:** the highest-volume processing complaints (PANIGHTLY, completed-with-errors, picklist-missing, FTP path) are usually **config/metadata/data**, dispositioned without a product bug. The genuine code-defect families are **PTR-overlay protection** (#1681831 and 22-00827029/22-00609003 era), **MV90 date/upgrade** (#1684017/#1691307), **PANIGHTLY metadata** (#1705412/#1751637), and **export-overwrite** (#1705697).

---

## 18. Expected Behavior / User Education

Root Cause = **Customer Error / Training** dominates the volume here (79 cases). Recognize these to avoid scripts/escalations.

| Reported as | Reality | Case |
|---|---|---|
| "Measurement missing / not importing" | Data **not in FlowCal/source yet** — nothing for QPTM to pull | 25-01031931, 26-01096082, 22-00513489 |
| "Job completed with errors" | A few bad/missing-data rows; review the row, not a defect | 25-01051859, 25-01006449, 24-00962876 |
| "Quorum is locked" / "system locked during accounting roll" | Accounting roll / month-close in progress — expected lock | 24-00990964, 26-01099854 |
| "Month closed in error, reopen it" | Customer prematurely closed the month; provide reopen data script | 24-00983668, 24-00974020 |
| "Duplicate / primary-key error on allocation" | Re-run over existing data, or bidirectional needs zero-noms | 25-01055410, 25-01036204, 26-01063368 |
| "How does QLONGJOB / BLROLLDATE / IOC work?" | Process explanation request | 25-01006816, 26-01098578, 25-01063117 |
| "QEMAIL SMTP error in UAT" | UAT has no valid relay by design | 25-01057894, 24-00940028 |
| "Volumes not on INX40 / up-down report" | Data/config on customer side | 25-01044691, 25-01050921 |
| "Report data differs UAT vs PRD" / "DTH vs MCF differ" | Different env data / unit difference — expected | 22-00597413, 22-00516846 |
| "QQM report scheduling functionality" | Enhancement request, not a defect | 22-00597420 |
| "Clear out PRD IPW" / destructive request | Declined by Quorum | 24-00968784 |

**Tell-tale it's user/expected:** the data is wrong **at the source** (FlowCal/MV90/PGAS), the "error" is a small data row in an otherwise-good run, the lock is an in-progress accounting roll, or the env genuinely lacks a relay/data (UAT).

---

## 19. Escalation Decision Tree
```
Integration/Processing case reported
│
├─ EDI (NMST/NMQR/EEDM/EDI server/PGP)?  →  SKILL_EDI_Troubleshooting.md
│
├─ Batch job problem?  (§5)
│   ├─ "completed with errors/warnings" → find the failing ROW/STEP (PQID); usually DATA → review/data script
│   ├─ HUNG / QUE status → infrastructure / queue handler (25-01004842, 25-01012625)
│   ├─ "not in picklist" / params missing → check-in Batch Def + Parameter/Picklist metadata to env
│   └─ Real failure after upgrade/metadata → check for client ADO (e.g. #1705412 PANIGHTLY)
│
├─ IMPORT not working (FlowCal/MV90/gas-quality)?  (§6)
│   ├─ File on SFTP? matches import-def filename pattern? → fix path/filename config (§8)
│   ├─ Data actually in the source (FlowCal/E-Suite)? → if not, customer-side (educate)
│   └─ MV90 date/upgrade behavior → code (#1684017/#1691307)
│
├─ EXPORT wrong/failing (IPWS/AP-GL/billing/CW*/OSI PI)?  (§7)
│   ├─ TRIPLE/DUPLICATE values → EXP_OVERWRITE_FILE_IND off → §16 Script A
│   ├─ CW*/path error → file path pointing at wrong env/pod → fix QARCH_CTRL_IMPEXP path
│   └─ Invalid TSP / posting defect → code (22-00565430)
│
├─ SFTP/FTP "can't connect" / file stuck?  (§8)
│   └─ Verify FTP conn/credentials/firewall; often remove + re-add the path object fixes it
│
├─ PTR / TIPS sync?  (§9)
│   ├─ Manual override wiped / PTR zeroed → overlay-protection DEFECT → escalate (code)
│   └─ QPTM step depends on TIPS step → dependency defect (#1681831)
│
├─ Allocation/balancing job?  (§10)
│   ├─ Truncation → ALTER column length (§16 Script C)
│   ├─ Duplicate key (bidirectional/MEP) → zero-noms / data
│   └─ Time-slice not captured → toggle EFF_DT_TO + revert
│
├─ QQM?  (§11)
│   ├─ Data ≠ app / effective-dating / hierarchy → universe DEFECT (code)
│   ├─ Won't run / slow / crash → report-server memory/config/Log4j
│   └─ Scheduling / "differs by env" / DTH-vs-MCF → usually Customer/Training (expected)
│
├─ QEMAIL / notice email?  (§12)
│   └─ SMTP config for the env (UAT often has none by design)
│
├─ Orphaned location stopping ALL jobs in a TSP?  (§5/§16B)
│   └─ Diagnostic §15D → orphaned-loc cleanup script (§16 Script B)
│
└─ Job/process "how does it work"? → Training (answer, don't script)  (§18)
```

---

*Skill created: 2026-06-01*
*Based on: 217 actionable QPTM Integration/Processing/QQM SF cases + ADO #1705412, #1751637, #1705697, #1681831, #1660692, #1684017, #1691307, #1616200, #1620218. Verbatim fix SQL from ADO attachments on #1705697 (export-overwrite) and #1660692 (orphaned-loc cleanup).*
*Companion skills: SKILL_EDI_Troubleshooting.md (EDI transport), SKILL_Nominations.md (nom overlap/delete scripts §4), SKILL_Allocations.md (allocation logic), SKILL_Reporting_Regulatory_Postings.md (in-app reports). Applicable to all QPTM TSPs/clients.*
