# SKILL: TIPS Batch Processing Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-11 | **Product:** My Quorum TIPS
**Scope:** TIPS batch processing — Facility Batch Job Submittal / Company Batch Job Submittal (Measure → Allocate → Settle → Journal → Post), QPEC job execution (stuck jobs, status 'UX'), ALLOCATE step failures (CTRMTR / GETOPENINV / paystation PK violations), reruns & PPA months, posting (POSTRESLT / imbalance account balance), batch performance (CALC_STATS), file imports & connections (FlowCal / SFTP / Import-Export Definitions / Connection Management), Purge & Archive (QARCHIVE / TIPARCHIVE / HISTPURGE / RECPURGE), and batch-related global config.
**Use When:** Any TIPS case in categories *Batch Job Submittal, Processing, Maintenance, Purge/Archive, Archiving* — "job stuck", "facility batch job failing", "can't post", "rerun won't run", "process erroring", "import failing", "archive error".
**Companion:** For QPTM allocation engine issues see **SKILL_Allocations.md** (Evolution/TIPS-integrated clients overlap on WHMEASIMP/PTR). This skill covers the TIPS batch *framework and steps*, not statement/invoice content.

> Evidence base: 590 closed TIPS cases in this category group; 111 actionable (Software Defect 43 + Application Configuration ~58 + ChangeConfig 10 per detail pull) mined in full, plus 30 Training/Customer Error cases for the Expected-Behavior section, cross-referenced against ADO. Every root-cause claim cites a real SF case and/or ADO item observed during mining.

---

## TABLE OF CONTENTS

1. [Quick Triage](#1-quick-triage)
2. [TIPS Batch Concepts & Pipeline](#2-tips-batch-concepts--pipeline)
3. [Decision Tree](#3-decision-tree)
4. [Stuck / Hung Jobs & QPEC Restarts (HIGH FREQUENCY)](#4-stuck--hung-jobs--qpec-restarts)
5. [Facility/Company Batch Job Screen — Web vs Classic Defects](#5-facilitycompany-batch-job-screen--web-vs-classic-defects)
6. [Batch Job Code-Table Config (QCODE_BATCH_JOB)](#6-batch-job-code-table-config)
7. [Duplicate TRNX_IDs / PK Violations in Batch Steps (CTRMTR / GETOPENINV / IMBAL_ACCT_BAL)](#7-duplicate-trnx_ids--pk-violations)
8. [Reruns & PPA-Month Processing](#8-reruns--ppa-month-processing)
9. [Batch Performance (CALC_STATS / Indexes / SQL Tuning)](#9-batch-performance)
10. [Imports, SFTP, File Paths & Connection Management](#10-imports-sftp-file-paths--connection-management)
11. [Purge & Archive (QARCHIVE / TIPARCHIVE / HISTPURGE)](#11-purge--archive)
12. [WHMEASIMP / Measurement Import Data Loss (Evolution)](#12-whmeasimp--measurement-import-data-loss)
13. [Post-Refresh Environment & Warning-Flood Issues (CAW*, ALLOCATE warnings)](#13-post-refresh-environment--warning-flood-issues)
14. [Orphaned / Overlapping Reference Data Breaking Jobs](#14-orphaned--overlapping-reference-data-breaking-jobs)
15. [Global Config Changes Affecting Batch](#15-global-config-changes-affecting-batch)
16. [Expected Behavior / User Education FAQ](#16-expected-behavior--user-education-faq)
17. [Known ADO Items](#17-known-ado-items)
18. [Diagnostic SQL](#18-diagnostic-sql)
19. [Escalation Guidance](#19-escalation-guidance)

---

## 1. Quick Triage

```
[ ] 1. WHICH job — Facility Batch Job (per-plant: Measure/Allocate/Settle/Journal) or Company Batch Job
       (cross-plant: Imbalance/Invoice/Post Results)? Which STEP (e.g. CTRMTR, GETOPENINV, ROLLACCTDT, INACCTACCM)?
[ ] 2. Master PQID of the failed/stuck run? (keys the QPEC log; clients can read it off the batch screen)
[ ] 3. EXACT error text? Common: "duplicate process error", "Violation of PRIMARY KEY constraint PK_QTRAN_PAYSTATION",
       "ORA-00001 unique constraint", "last completed process ID doesn't match", "Query Timeout Expired",
       "Internal System Error running job", "Cannot get default Quantity UOMs ... QXREF_QTY_UOM_CD".
[ ] 4. Stuck (status never finishes) vs errored (red)? Stuck → §4 (restart + UX script). Errored → match the error below.
[ ] 5. Web or Classic? Web/Classic job-status sync and rerun screens have a known defect family (§5, §8).
[ ] 6. Normal month, RERUN month, or PPA month? Rerun/PPA interplay is its own defect family (§8).
[ ] 7. Did this start right after a DB refresh, deployment, or services restart? → §13 (env config) before code.
[ ] 8. Are reversals / end-dated meters / overlapping timeslices involved? → §7/§14 (data-driven PK violations).
[ ] 9. First run after posting all plants (empty QTRAN tables overnight)? → stale stats, §9 CALC_STATS.
[ ] 10. Import job: check file path, file-already-exists, host definition, QPEC user active, .NET-vs-SQL connection (§10).
```

### Symptom → likely cause → first check
| Symptom | Likely cause | First check |
|---------|--------------|-------------|
| Job stuck "in progress", new runs blocked by "duplicate process error" | Orphaned QPEC process | §4 — restart QPEC services + UX script (24-00974530) |
| "Internal program error occurred", plant stuck in Facility Lock | Hung QPEC + jobs left processing | §4 (23-00890868) |
| Web shows facility jobs runnable after a company-job failure; Classic locks them | Web/Classic sync defect | §5 (25-01033408) |
| Post Results: "last completed process ID doesn't match" | QCODE_BATCH_JOB row order (SETTLEAGH vs SETTLEDAY) | §6 (25-00996637) |
| Error on Company Batch Job screen on open/retrieve | Duplicate rows in batch code table | §6 (24-00942212, 24-00941908) |
| `PK_QTRAN_PAYSTATION` / duplicate TRNX_ID on CTRMTR | Overlapping meter eff-dates / reversals on end-dated meters | §7 (23-00927502, 26-01083551) |
| Posting fails on accounting-period roll — PK constraint | Duplicates in QTRAN_IMBAL_ACCT_BAL | §7 (26-01087709, ADO #1772117) |
| Rerun month grayed out / can't post a rerun in Web | Rerun approval handling defect | §8 (23-00906527) |
| Rerun of a month that has same-month PPAs corrupts data | PPA-same-month rerun defect | §8 (24-00942120) |
| Job suddenly takes hours (Journal/Imbalance/Allocate) | Stale optimizer stats / missing index / split logic | §9 (23-00892948, 23-00934500) |
| Import fails: SFTP / file path / "file already exists" | Import-Export Definition, host def, QPEC user | §10 (24-00964377, 24-00973935) |
| CAWDATAFS / batch step "connection error" | .NET connection set to SQL CONNECTION in Connection Management | §10 (25-01016313, 26-01065785) |
| QARCHIVE / TIPARCHIVE errors | Archive group connection details / setup | §11 (25-01058403, 23-00895638) |
| Measured volumes vanished for paper meters after close | WHMEASIMP PPA-config deletion bug | §12 (25-01032433) |
| Thousands of new ALLOCATE warnings / UAT jobs fail after refresh | Post-refresh config still pointing at PRD; missing facility configs | §13 (26-01086760, 25-01045540) |
| "Found Orphaned Location attribute..." (CANOMCLTG) | Orphan rows in PACTRL_LOC_ATTR(_FLAT) | §14 (24-00994166) |
| New unexplained errors after TIPSMASTER | Contract header timeslice overlap | §14 (23-00878192) |
| Large negative fuel allocations, no setup change | Global rounding config | §15 (26-01104466) |

---

## 2. TIPS Batch Concepts & Pipeline

TIPS processes a **plant (facility) for an accounting month + production month** through a fixed job sequence, then company-level jobs consolidate and post.

```
FACILITY BATCH JOB SUBMITTAL (per plant)            COMPANY BATCH JOB SUBMITTAL (per company)
  Measure (MEASVOL, MEASUREMND, gas analysis)         Imbalance (JOURNALIMB / INACCTACCM)
    → Allocate (ALLOCATE: steps incl. CTRMTR,           → Invoice / Invoice Approval
      GETOPENINV, GATHFUEL, STDPDA, RESALLOCGP)         → Post Results (POSTRESLT/POSTRESLT2,
    → Settle (SETTLEPREP, SETTLEDAY/SETTLEAGH)             ROLLACCTDT rolls the accounting date)
    → Journal (JE_*, CALC_STATS step)
    → Approve / Lock Plant → Post
```

- Jobs execute on **QPEC** servers; each run gets a **Master PQID**. A job left mid-flight holds a lock — the framework refuses to start a duplicate, so a hung job blocks everything (§4). Status code **'UX'** marks a process as failed/cancelled so it can be re-run.
- **Web vs Classic:** both UIs front the same job tables; a family of defects (mostly the 2022.10 wave) makes the Web screen show stale/incorrect job status or allow actions Classic correctly blocks (§5).
- The job sequence and dependencies are **configuration**: `QCODE_BATCH_JOB` (hidden `ROW_ID` orders jobs), process definitions in `QARCH_CTRL_PROCESS*` / `QARCH_CTRL_PROC_PROCSTEP` metadata, and process dependencies. Wrong config = "last completed process ID doesn't match" class errors (§6).
- **Rerun** months reprocess a posted production month; **PPA** months carry prior-period adjustments. Reruns must respect "Rerun Exclude" approval jobs and must not collide with PPAs of the same production month (§8).
- **ALLOCATE step implementation:** TurboTips engine — `Quorum.TIPS.Batch/Quorum.TIPS.Batch.QPDllTurboTips/StepExecution/CTRMTR.cs`, `Quorum.Tips.TurboTips/Quorum.Tips.TurboTips.Allocate/CTRMTR/psCTRMTR.cs`; classic C++ batch e.g. `<CLIENT>.TIPS.ClassicBatch/QPDllTipsAllocate/QSQL_RetrieveClosingInventory.cpp` (GETOPENINV). Client process metadata lives in `<CLIENT>.TIPS.Metadata` repos.

---

## 3. Decision Tree

```
TIPS batch case reported
│
├─ Job STUCK / "duplicate process error" / plant locked?            → §4
│   └─ Restart QPEC services + script stuck statuses to 'UX'; if recurring → DBA stats (§9) or escalate
│
├─ Job ERRORED with a PK / unique-constraint message?               → §7
│   ├─ PK_QTRAN_PAYSTATION / duplicate TRNX_ID → overlapping meter eff-dates or reversals on end-dated
│   │     meters → data-fix script + code fix (2025.04.1.13 for CTRMTR/GETOPENINV dup creation)
│   └─ QTRAN_IMBAL_ACCT_BAL / posting roll → delete-duplicates script (ADO #1776936) + software update
│
├─ Error mentions a SPECIFIC missing thing (rate factor, index value, fee tab, inactive meter,
│   orphaned location attribute, timeslice overlap)?                → §14 / §16 — data/config, often customer-side
│
├─ Web behaves differently from Classic (status, rerun, next-job)?  → §5 — known Web sync defect family; patch level
│
├─ "Last completed process ID doesn't match" / job missing in Web / wrong next job?  → §6 — QCODE_BATCH_JOB config
│
├─ Rerun or PPA month involved?                                     → §8
│
├─ Import / SFTP / connection error?                                → §10
│   └─ Started after refresh/deployment? check Connection Management .NET-vs-SQL first (25-01016313)
│
├─ QARCHIVE / TIPARCHIVE / HISTPURGE?                               → §11
│
├─ Sudden slowness, first run after posting all plants?             → §9 — CALC_STATS / stats / index
│
├─ Right after a DB refresh (UAT pointing at PRD, warning floods)?  → §13
│
└─ Vague "process is red", how-to, unapproval, purge questions?     → §16 — likely Training/Customer Error
```

---

## 4. Stuck / Hung Jobs & QPEC Restarts

**The single most common actionable pattern (~11 cases).** A QPEC process dies or hangs mid-run; the job row stays "in progress"; new submissions fail with a **duplicate process error**; the plant may sit in **Facility Lock**.

**Symptom:** "Job not finished since <date>, unable to start new job due to duplicate process error. Master PQID <n>. Need status set to UX" (24-00974530, M6 Midstream — verbatim). "Internal program error occurred... plant was stuck in Facility Lock status" (23-00890868, NorthRiver).

**Root cause:** orphaned QPEC process / dead service; occasionally stale DB optimizer stats make the job run "forever" (24-00975612 — DBA ran statistics and the hung TIPS jobs cleared).

**Resolution recipe:**
1. Get the **Master PQID** and confirm in the process queue that the run is genuinely dead (no progress in the QPEC log).
2. **Restart the QPEC / QTIPS services** (Cloud Ops request for hosted clients). This alone resolved 22-00516202, 22-00512698, 26-01097581, 26-01066599 (even "emails not being received from TIPS" was a hung QTIPS service), and the Facility-Batch-Job progress icons in 24-00955005.
3. **Script all processes left in a processing status to 'UX'** before re-running (the standard pairing — 23-00890868, 24-00974530: "a script was applied to set the stuck processes to 'UX'").
4. Re-run the batch job. If the same job hangs again → have the DBA **gather statistics** (24-00975612) and check §9.
5. If the job calls a **customer-owned stored procedure**, the hang is theirs to fix (24-00985269, Hess).
- Representative cases: 24-00974530, 23-00890868, 24-00986899, 24-00975612, 22-00516202, 22-00512698, 26-01091247 (timeout config + QPEC restart), 22-00598172 (QPEC failed to create/open its log file).

> Stuck-in-QUEUE where even Cancel won't cancel is a long-standing product gap (training case 25-01033454 references 22-00263967). The UX-script + restart is the operational answer.

---

## 5. Facility/Company Batch Job Screen — Web vs Classic Defects

**~11 cases, heavily the ONEOK 2022.10 upgrade wave.** The Web batch screens get out of sync with Classic or skip Classic's guards.

**Symptoms & dispositions (all real):**
| Issue | Fix | Case |
|-------|-----|------|
| Company job fails (e.g. Invoice Approval "Invalid plant status for approval") — **Web still lets you run facility jobs; Classic removes them** | Code fix made | 25-01033408 (ONEOK) |
| Company Batch Job not in sync between Classic and Web | Code fix (2022.10 patch wave) | 23-00908450 |
| Facility Batch Jobs "Next Available" not in sync with Classic | Code fix | 23-00893815 (MarkWest) |
| Status indicator not updating once Settle completes | Code fix | 23-00905993 |
| "Run Next Job" populates the wrong NEXT AVAILABLE JOB | Code fix | 24-00942089 |
| Web allows Sched Qty Inv Generation after job APPROVED/LOCKED | Code fix | 23-00908451 |
| Can't post Gathering Facilities in the Web | Code fix | 23-00907238 |
| Error when running multiple batch jobs in Web Batch Process screen | Code fix | 24-00960610 |
| Job status icon stays gray instead of green/red/yellow | Code fix (status colors) | 22-00561477 (Pembina) |
| Batch Job Submittal requires multiple Retrieves (v17) | Code fix | 22-00555581 (DTE) |

**Resolution recipe:** reproduce in **both** UIs; if Classic is correct and Web is wrong (or vice-versa) it is a **code defect** — match to the client's version/patch level and the ADO family in §17 (recent recurrences: #1777919 IPF "Honor Facility Batch Jobs Setup & Display Status Correctly", #1777056 Daily's query blank after rerun setup). Workaround while waiting on a patch: perform the action in the UI that behaves correctly, and never trust the Web status icon without a Retrieve.

---

## 6. Batch Job Code-Table Config

**Symptom:** Post Results errors "the last completed process ID doesn't match what is required to post" (25-00996637, Merit); the Company Batch Job screen errors on open (24-00942212, 24-00941908, Genesis); a batch job (e.g. **JE_EX_SAB**) exists in Classic but is **missing in Web** (25-01014535, Third Coast).

**Root cause:** the batch-job sequence is data in **`QCODE_BATCH_JOB`** — a hidden **`ROW_ID`** column orders the jobs. Duplicated rows or wrong ordering break job-sequence validation; a missing **Process Type** on a process keeps it off the Web screen.

**Resolution recipe (verbatim from 25-00996637):** *"Reordered the ROW_ID in the db for QCODE_BATCH_JOB, for Settle process. It has to be first SETTLEAGH (Monthly) and then SETTLEDAY (Daily) — it's a hidden column that identifies and orders that row."*
1. Query `QCODE_BATCH_JOB` for the company/plant; look for **duplicate rows** (delete the dupes — 24-00942212, 24-00941908) and **ROW_ID order** that contradicts the required sequence (monthly settle before daily).
2. Job missing in Web → configure its **Process Type** on the process definition (25-01014535).
3. Process-dependency additions (e.g. tie Imbalance → Invoice) are config work, not defects (24-00952753).
- Also here: RECORD PURGE addition to **code table 24180** shipped as a patch (25-01038844, Steel Reef).

---

## 7. Duplicate TRNX_IDs / PK Violations

**~6 actionable cases + an active ADO family.** Batch steps insert transaction rows; pre-existing duplicates or duplicate-generating bugs kill the step with a PK violation.

### 7a. CTRMTR / GETOPENINV (ALLOCATE steps)
- **26-01083551 (Pivotal):** *"batch job steps CTRMTR and GETOPENINV create duplicates for meters that have reversals and are end dated"* — **code fix in TIPS 2025.04.1.13**; client must upgrade to consume it.
- **23-00927502 (Producers Midstream):** `Violation of PRIMARY KEY constraint 'PK_QTRAN_PAYSTATION'` — duplicate TRNX_IDs tied to one meter (1449959B) with **overlapping effective dates**; fixed by SQL identifying mismatched effective dates across related tables and correcting them.
- **24-00946936 (Producers Midstream):** ANASU facility job errors — **overlapping date in `SCTRL_MTR_FACILITY`** for a meter; script corrected the overlap and re-synced a record with `SCTRL_MTR_HEADER` / `SEXTN_MTR_HEADER_QRMTIPS`.
- ADO confirms the family: #1718964 (root cause of duplicated TRNX_IDs in `QTRAN_PAYSTATION` failing CTRMTR), #1752343 (EQC, Proposed — same PK error), #1745358/#1746523 (SCT — CTRMTR stuck/timeout, part 2 on `INS_GATH_REC_PAYSTATION`), #1691458 (UGI — CTRMTR memory exhaustion).

### 7b. QTRAN_IMBAL_ACCT_BAL (posting / accounting-period roll)
- **26-01087709 (Hess):** *"issue rolling our accounting period due to the primary key record constraint during the posting process"* — duplicates in `QTRAN_IMBAL_ACCT_BAL`; resolved by sharing the available **software update** + engineering's resolution. ADO #1772117 (root cause, dup records in `QPOST_IMBAL_ACCT_BAL` and `QTRAN_IMBAL_ACCT_BAL`) and delete-duplicates **script deployments #1776936 / #1778789** (HEC PRD).
- **24-00962703 (Genesis):** PPA rerun error `ORA-00001 unique constraint` — same shape on Oracle.

**Resolution recipe:**
1. Capture the exact constraint name → it names the table. Run the matching dup-check in §18.
2. **Duplicates already in the table** → delete-duplicates data script (pattern of ADO #1776936/#1778789), then re-run the step.
3. **Duplicates being *created* by the step** (reversals + end-dated meters) → known defect; fix is in **2025.04.1.13** (26-01083551) — check client version, otherwise script-and-rerun each occurrence.
4. **Overlapping meter/contract effective dates** as the feeder → fix the timeslices (§14) or the dupes return.

---

## 8. Reruns & PPA-Month Processing

**Symptom families (~5 cases):**
| Issue | Root cause / fix | Case |
|-------|------------------|------|
| Rerun month selectable in Web but process jobs **grayed out/locked**; Classic works | Fixed: Facility Batch Job Submittal now only requires approvals set up for rerun months and properly excludes approval jobs marked **"Rerun Exclude"** | 23-00906527 (ONEOK, 2022.10) |
| Rerun of a production month that has **PPAs of the same month**: flips PPAs to Reruns but does **not delete the PPA TRNX_IDs**, creating Measurement/Allocate/Settle rows with REC_STATUS_CD 'CO' and 'R' | Code defect — fixed with the duplicate-TRNX_ID long-term fix | 24-00942120 (ONEOK) |
| Can't post a re-run (duplicate TRNX_IDs) — long-term fix tracking | Fix delivered May 2024 | 24-00951618 / 23-00936172 (Steel Reef) |
| Re-running a Permian plant for a prod month **prior to Evolution** causes Wellhead to approve | Defect (Evolution/QPTM boundary — see SKILL_Allocations §6) | 24-00985623 (ETP) |
| Plant reruns failing (Dover Hennessey) | Code fix | 22-00549944 (Mustang) |

**Triage:** for any rerun case, establish (a) is there a **PPA for the same production month** in flight, (b) are approval jobs configured with **Rerun Exclude**, (c) the client's version vs the 2022.10/2024 fixes. A rerun colliding with same-month PPAs on an unpatched version will corrupt status codes — stop the client from re-running until cleaned up.

---

## 9. Batch Performance

**~10 cases.** Long-running or timing-out batch jobs. Two proven mechanisms:

### 9a. Stale optimizer statistics → CALC_STATS
- **23-00892948 (IACX):** JOURNALIMB ran 1.5h instead of 10min. Root cause (verbatim): *"problem was only occurring the first time they ran journal a day after having posted all their plants (which meant the QTRAN tables were empty when stats ran during the night)"*. Fix: **added process step `CALC_STATS` to Journal** which recalcs stats for certain tables.
- **23-00932008 (WTG):** ALLOCATE performance — resolved by **adding CALC_STATS for the ALLOCATE job**.
- The tables CALC_STATS covers are config: **`QCODE_TABLE_CALC_STATS`** (ADO DB changes #1633473, #1644834, #1706988 — e.g. SCT adding `QTRAN_PAYSTATION`).
- **24-00975612 (Hess):** DBA-run statistics cleared hung jobs — same mechanism, manual form.

### 9b. Genuine code/SQL defects
| Case | Fix |
|------|-----|
| 23-00934500 (Opportune) — Company **Imbalance (INACCTACCM)** query timeout | ADO **#1636859**: *bypass the splitting logic when no splits are set up*; delivered via Patch 11 |
| 23-00878024 (NorthRiver) — **MEASUREMND** slow | Removed `FN_FIRST_DAY_OF_MONTH` from the WHERE clause of Canadian `SQLID_STD_ANAL_COMP` (query already restricted to monthly records) |
| 22-00822030 (ONEOK) — Resolve Allocation Group Mtrs slows QPECs | In-memory processing changed from map to `unordered_set` |
| 22-00679965 (Harvest) — Imbalance too long | Index created |
| 22-00556376/77/78, 22-00562670 (Enable) — GATHFUEL / STDPDA / MEASVOL / Journal perf | Client-specific perf patches deployed |

**Resolution recipe:** if slowness appears on the **first run after a posting cycle/refresh** → stats problem: run stats manually, then permanently add the affected tables to `QCODE_TABLE_CALC_STATS` / add the CALC_STATS step to that job. If slowness is constant and data-volume-proportional → capture the long-running SQL and escalate as a perf defect (note ADO #1744413 "TIPS Performance Initiative — Convert CTRMTR" exists for step modernization).

---

## 10. Imports, SFTP, File Paths & Connection Management

**~11 cases, almost all Application Configuration.**

| Issue | Fix | Case |
|-------|-----|------|
| SFTP "not working" | The client's **QPEC user was marked inactive** — reactivate | 24-00973935 (WTG) |
| UAT can't load volume file — SFTP error | **Host definition** updated | 24-00964377 (Harvest) |
| FlowCal import path wrong | Change import file path in **Batch Process Execution / Import definition** | 24-00963134 (Steel Reef) |
| Gas Analysis Loader fails | **Import/Export Definition was missing the file path location** — set it, place file there | 22-00875127 (Merit) |
| Inventory-override spreadsheet won't upload | File path corrected to `\\<server>\QFC17$\<CLIENT>\<ENV>\AppFiles\TIPS\Imports` | 25-01025681 (Pivotal) |
| UAT FTP folder structure ≠ PRD | Corrected UAT FTP folder structure | 26-01091018 (Scout) |
| **CAWDATAFS / batch step connection error** — ".NET connection was equal to SQL CONNECTION" | Fix the connection entry (workaround); root cause suspected deployment-side; KB drafted | 25-01016313 (Lighthouse) |
| Facility job fails "a meter on a PDA doesn't exist" + connection fallout | Hotfix for the known bug; **removed an invalid setting on the Connection Management screen for the .NET Connection Type (TIPSDSService)** | 26-01065785 (Opportune) |
| Missing Connection IDs after env work | Re-add connection IDs (env config) | 26-01063395 (Hess) |
| Process-step connection failures with cryptic errors | QFC change: verify connection before use in process step + better error logging | 22-00583574 (Campus Energy) |

**Resolution recipe:** for any import/batch connection failure — in order: (1) **Import/Export Definition** path + Backup Options ("Append Date To Filename" prevents file-already-exists, 25-01043424), (2) **host definition / FTP folder structure** vs PRD, (3) **QPEC user active**, (4) **Connection Management**: the .NET Connection Type must not carry SQL-connection settings (TIPSDSService); after refreshes/deployments connections can revert — fix and restart services.

---

## 11. Purge & Archive

**~6 cases.** Processes: **QARCHIVE** (archive groups), **TIPARCHIVE** (TIPS archive), **HISTPURGE** (posted-run purge), **RECPURGE** / Facility Run History & Purge (operational purge).

| Issue | Fix | Case |
|-------|-----|------|
| New archive group errors in PRD | **Script executed to correct the connection details in the archive; long-term fix in 2024.10+** | 25-01058403 (M6) |
| TIPARCHIVE batch process failed | Error came from client-side setup; setup instructions provided | 23-00895638 (ETP) |
| QARCHIVE 'failed execute' | (resolution not recorded in SF; ADO shows the recurring family: #1689869 QArchive PK error, #1460618 daily failure, #1650552 invalid column `ARCHIVE_PROCESS_QUEUE_ID`) | 22-00824980 (Pembina) |
| **HISTPURGE was purging Posted Run_IDs** | Fixed: HISTPURGE now checks whether a Run_ID is posted and skips it | 22-00561531 (Pembina) |
| Meter Splits in Web error from an extra archiving validation Classic didn't have | Code fix | 22-00598115 (ONEOK) |
| Want to purge all days at once (E2E purge) | Config/enhancement discussion | 24-00969374 (ETP) |

**Resolution recipe:** archive failures are usually **archive-group connection/setup** (post-refresh especially) — verify the archive connection details first (script-fixable, 25-01058403), then match the error to the ADO QArchive family. Educate clients that **DB-query-based archiving is not supported** (26-01089541) and HISTPURGE on modern versions will skip posted runs by design.

---

## 12. WHMEASIMP / Measurement Import Data Loss

**Evolution (TIPS↔QPTM) clients — small but severe (~3 cases, P1 material).**

- **25-01032433 / 25-01031716 (Enterprise):** *"June 2025 Measured Volume missing for all paper meters for STX plants"* after close. Root cause (verbatim): *"a bug with how the WHMEASIMP process handles certain configurations of PPAs that can delete measured volumes."* Development **patched** it; confirm the patch before any rerun. If a client reports wholesale missing measured volumes on paper/wellhead-fed meters right after a close with PPAs in play — this is the first suspect.
- ADO sibling defect: **#1713703/#1713704/#1713707/#1716969/#1719499 (ENT)** — *WHMEASIMP: QPTM child-meter measured volumes overridden by the aggregate meter in TIPS*.
- **22-00642221 (Keyera):** RIMPT volume visible by query but not in Volume Editor — CAN-layer default for `VOL_CLSF_CD` on screen `QVPMEASUREDVOLUME` widened to search all volume/meter types.
- WHMEASIMP is **client metadata-defined** (`ENT.TIPS.Metadata /STANDARD 16.0/QARCH_CTRL_PROCESS*.json`) — confirm which client layer owns the process definition before assuming base behavior.

---

## 13. Post-Refresh Environment & Warning-Flood Issues

**~7 cases (Hess/EQT heavy).** Jobs fail or spew warnings in UAT/DEV right after a database refresh.

- **26-01086760 (EQT):** CAWDATAFS failing in UAT after refresh — *"some of the tables are still pointing to PRD"*; standard post-refresh repoint per KB article.
- **25-01041546 (Hess):** CAWDATA process step failing in DEV — same family.
- **25-01045540 / 25-01045547 / 25-01045551 (Hess, AHS DEV):** ALLOCATE generating **56,000+ warnings** on TIOGA / unnecessary warnings on both plants — **missing Facility Configs** in the refreshed env; config not code.
- **25-01041547 (Hess):** popup *"Cannot get default Quantity UOMs. Please check table QXREF_QTY_UOM_CD"* — missing default-UOM config rows (cosmetic; screen still works).
- **24-00956235 (Steel Reef):** posting error resolved by **UAT/DEV refresh** (myQuorum Cloud refresh WIs).

**Resolution recipe:** anything that broke *immediately after a refresh* → run the post-refresh checklist before debugging: connection strings/linked tables not pointing at PRD (incl. Connection Management .NET entries §10), facility configs present, env-specific paths (FTP/import) corrected, then restart QPEC services. These belong to **Cloud Ops**, not Engineering.

---

## 14. Orphaned / Overlapping Reference Data Breaking Jobs

**~5 cases.** Batch steps assume clean timeslices; orphans/overlaps surface as opaque job errors.

| Error | Root cause | Fix | Case |
|-------|-----------|-----|------|
| CANOMCLTG: *"Found Orphaned Location attribute CML for location 11253N..."* | Rows in `PACTRL_LOC_ATTR_FLAT` / `PACTRL_LOC_ATTR` whose `LOC_ID` is not in `PACTRL_LOC` | Verbatim fix: `SELECT * FROM PACTRL_LOC_ATTR_FLAT WHERE LOC_ID NOT IN (SELECT LOC_ID FROM PACTRL_LOC)` (and same for `PACTRL_LOC_ATTR`) → **delete this data** | 24-00994166 (EQT) |
| New unexplained errors after TIPSMASTER post-restart | **Contract Header Timeslice Overlapping** | Client corrected the overlapping timeslice | 23-00878192 (NorthRiver) |
| Measure-to-Settle error for one contract | `SEXTN_CTR_HEADER_QRMTIPS` row not updated when user edited the contract header timeslice in QCM | Script re-synced the extension row | 22-00627496 (IACX) |
| Facility job PK errors (meter) | Overlapping eff-dates in `SCTRL_MTR_FACILITY` (+ out-of-sync `SCTRL_MTR_HEADER`/`SEXTN_MTR_HEADER_QRMTIPS`) | Correction script | 24-00946936 (Producers) |
| Contract Meter List — meter suffix generation breaking jobs on UPDATE | Code defect (development required) | 22-00561456 (Pembina) |
| Duplicate contract record when rejection status changed from default "none" | Delete the prior record from the contract on reject-option change | 24-00986307 (Opportune) |

**Heuristic:** when a batch error names a specific **location/meter/contract**, diff its timeslices and extension tables (`SEXTN_*_QRMTIPS`) before suspecting the process code. These are data-fix scripts, not patches.

---

## 15. Global Config Changes Affecting Batch

| Change | Effect | Case |
|--------|--------|------|
| **Progressive rounding** global | Fixed *"large negative Fuel allocations"* on a contract with unchanged setup (allocation-group formula + UDF rounding interplay) | 26-01104466 (EQT) |
| **`ACCOUNTING_PERIOD_MODE`** added to global config table, set to Plant (**PLT**) in client layer (QHEC) | Accounting period managed per plant; must be re-checked after patches/upgrades | 26-01096195 (Hilcorp) |
| Global config warning to external users on daily/monthly **split imports** | Warning enabled via global configuration settings | 23-00918173 (NorthRiver) |
| RESALLOCGP batch errors | Provided process + error documentation (config-level guidance) | 26-01099359 (Conifer) |

**Note:** global config rows live in the layered config (base vs client layer e.g. QHEC); always make the change in the **client layer** and record it so refreshes/upgrades don't lose it (the explicit purpose of 26-01096195).

---

## 16. Expected Behavior / User Education FAQ

~93 Training + ~69 Customer Error cases in this group. The recurring answers:

1. **"Post Results / company job errors after we reran something at facility level."** Rerunning measurement through Journal at the facility level resets the sequence — company jobs must then be run **in the correct order** (26-01091091). Same family as the QCODE sequence error but user-induced.
2. **"POST fails at step ROLLACCTDT."** Production dates must be linked to **future open accounting dates** before posting. In normal operation POST adds them automatically; manually opening accounting dates during testing breaks this (26-01084537). See also 25-01043024 — manual close-and-roll on the **Accounting Date Maintenance** screen is the workaround when the roll misbehaves.
3. **"Scheduled daily allocation job failing" / "Bantry will not run" / "plant won't run."** Almost always missing month-keyed reference data: a **missing monthly rate factor** (26-01081703), a **missing index value** for the month (26-01068552), a **missing Accounting Date Maintenance record** for the month (26-01080672), a **missing fee tab on the CCT** (25-01049468), or **inactive meters still on the contract list** — compare contract meters vs `QVALD_METER` (25-01022162).
4. **"FlowCal import failed."** Check the data: flow hours > 24 on some meters was the actual cause (26-01080908). Also file-already-exists → enable **Append Date To Filename** on the Import/Export Definition Backup Options (25-01043424).
5. **"We posted by accident / ran the wrong month — undo it."** Posting is recoverable only via DB **flashback/restore** if caught immediately (25-01055902); wrong-month data is removed via **Facility Run History and Purge → PURGE IND** (25-01024558, 25-01054575). Provide the Batch Job Unapproval doc for unapproving (26-01088862). Cancelling a facility run **mid-run** corrupts state — re-run the plant (25-01027939).
6. **"Settle/Contract Settlement keeps erroring."** Often residue from incomplete purges: RECPURGE not clearing everything → full rerun Measure→Allocate fixed it (25-01026123); unposted `QTRAN_PLANT_STATUS` record skipped by PLNTPAPREV purge → duplicate `QTRAN_PURC_REVENUE` rows (25-01032049, ADO myQuorum Cloud #1744847); PPA-Processing flag left on a posted month logs unwanted PPAs on FlowCal changes (25-01048496).
7. **"Facility Lock screen doesn't show my facility."** Working as designed — explained screen behavior (26-01092967).
8. **Archive guidance:** archiving via direct database queries is **not recommended/supported**; use the Archive process per documentation (26-01089541).

---

## 17. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|-------|--------------|-----------------|---------|---------|
| **#1636859** | Bug / Closed | MOM — Company Batch INACCTACCM failing with Query Timeout Expired (fix: bypass split logic when no splits; Patch 11) | §9 | 23-00934500 / 23-00934008 |
| **#1718964** | Requirement / Closed | UGI — Root cause for duplicated TRNX_IDs in QTRAN_PAYSTATION failing CTRMTR | §7 | 25-00999295 |
| **#1752343** | Bug / **Proposed** | EQC — CTRMTR `PK_QTRAN_PAYSTATION` cannot insert duplicate key | §7 | — |
| **#1745358 / #1746523** | Bug / Closed | SCT — CTRMTR step stuck/timeout (part 2: `INS_GATH_REC_PAYSTATION`) | §7/§9 | — |
| **#1691458** | Incident / Closed | UGI — CTRMTR failing with memory errors (contiguous VM block) | §7 | 24-00965985 |
| **#1744413** | Requirement / Closed | TIPS Performance Initiative (Long-Term) — Convert CTRMTR | §9 | — |
| **#1772117** | Bug / Closed | HEC — Root cause for duplicated records in `QPOST_IMBAL_ACCT_BAL` / `QTRAN_IMBAL_ACCT_BAL` | §7 | 25-01060242 / 25-01061774 |
| **#1776936 / #1778789** | Script Deployment / Closed | HEC — Delete duplicates from `QTRAN_IMBAL_ACCT_BAL` (PRD) | §7 | 26-01065143 / 26-01068169 |
| **#1713703 / #1713704 / #1713707** | Task / Closed | ENT — WHMEASIMP: QPTM child-meter measured volumes overridden by aggregate meter in TIPS | §12 | — |
| **#1689869** | Bug / Closed | HPE/BBT — Scheduled Jobs QArchive PK error | §11 | 24-00974423 |
| **#1650552** | Bug / Ready for QA | ALT — QARCHIVE step error: invalid column `ARCHIVE_PROCESS_QUEUE_ID` | §11 | — |
| **#1460618** | Bug / Closed | RLY — QArchive job failing daily | §11 | 22-00261704 |
| **#1633473 / #1644834 / #1706988** | Database Change / Closed | Scripts adding tables to `QCODE_TABLE_CALC_STATS` (incl. SCT `QTRAN_PAYSTATION`) | §9 | — |
| **#1777919** | Bug / Closed | IPF — CAN Facility Batch Job screen: honor setup & display status correctly | §5 | 26-01067772 |
| **#1777056** | Bug / Closed | IPF 2025.04 — Daily's query blank on Facility Batch Job Submittal after rerun setup | §5/§8 | 26-01066641 |
| **#1757579** | Bug / Closed | 2025.10 Beta — QAC plant Facility Batch Jobs failing | §5 | — |
| **#1744847** | (myQuorum Cloud) / Closed | PLNTPAPREV purge skips unposted `QTRAN_PLANT_STATUS` → duplicate `QTRAN_PURC_REVENUE` | §16-6 | 25-01032049 |

---

## 18. Diagnostic SQL

> Table/column names below marked ✅ are confirmed verbatim from case resolutions/ADO; others are patterns — verify against the client schema before scripting.

### A. Duplicate TRNX_IDs in paystation (CTRMTR PK failure) ✅
```sql
SELECT TRNX_ID, COUNT(*) AS dup_ct
FROM   QTRAN_PAYSTATION
GROUP BY TRNX_ID
HAVING COUNT(*) > 1;
-- 23-00927502: trace dups back to the meter and check overlapping effective dates
-- across SCTRL_MTR_FACILITY / SCTRL_MTR_HEADER / SEXTN_MTR_HEADER_QRMTIPS.
```

### B. Duplicates blocking the posting roll (QTRAN_IMBAL_ACCT_BAL) ✅ table, key inferred
```sql
-- Use the exact PK columns from the constraint message in the job log:
SELECT <PK columns>, COUNT(*) FROM QTRAN_IMBAL_ACCT_BAL
GROUP BY <PK columns> HAVING COUNT(*) > 1;
-- Same check on QPOST_IMBAL_ACCT_BAL (ADO #1772117). Fix = delete-dups script (ADO #1776936 pattern).
```

### C. Orphaned location attributes (CANOMCLTG) ✅ verbatim from 24-00994166
```sql
SELECT * FROM PACTRL_LOC_ATTR_FLAT WHERE LOC_ID NOT IN (SELECT LOC_ID FROM PACTRL_LOC);
SELECT * FROM PACTRL_LOC_ATTR      WHERE LOC_ID NOT IN (SELECT LOC_ID FROM PACTRL_LOC);
-- Orphans confirmed → delete this data (per the case resolution).
```

### D. Overlapping meter-facility timeslices ✅ table
```sql
SELECT a.MTR_NO, a.EFF_DT_FROM, a.EFF_DT_TO, b.EFF_DT_FROM, b.EFF_DT_TO
FROM   SCTRL_MTR_FACILITY a JOIN SCTRL_MTR_FACILITY b
       ON a.MTR_NO = b.MTR_NO AND a.ROWID <> b.ROWID
WHERE  a.EFF_DT_FROM < b.EFF_DT_TO AND b.EFF_DT_FROM < a.EFF_DT_TO;  -- column names: verify in env
```

### E. Batch-job sequence config (Post Results "last process ID doesn't match") ✅ table & ROW_ID
```sql
SELECT * FROM QCODE_BATCH_JOB ORDER BY ROW_ID;
-- ROW_ID is the hidden ordering column. For Settle: SETTLEAGH (Monthly) must come BEFORE SETTLEDAY (Daily)
-- (25-00996637). Also check for fully duplicated rows (24-00942212 / 24-00941908) and delete dupes.
```

### F. CALC_STATS coverage (recurring slowness) ✅ table
```sql
SELECT * FROM QCODE_TABLE_CALC_STATS;
-- Slow job's hot tables (e.g. QTRAN_PAYSTATION) missing? Add via DB-change script (ADO #1706988 pattern)
-- and/or add the CALC_STATS process step to the job (23-00892948, 23-00932008).
```

### G. Stuck processes (before the UX reset script)
```sql
-- Identify runs still 'in progress' for the Master PQID the client supplies, in the process queue table
-- (name varies by version — locate via the Master PQID shown on the batch screen).
-- Standard remediation: Cloud Ops restarts QPEC services, then script those statuses to 'UX' (24-00974530).
```

### H. Inactive meters still on a contract (TIPSMASTER/Measure errors) ✅ table
```sql
-- Compare contract meter list vs valid meters (25-01022162):
SELECT * FROM QVALD_METER WHERE MTR_NO IN (<meters on the contract>);
-- Meters absent/inactive here must be removed from the contract before Measurement will run.
```

### I. Erroneous imported gas analysis rows ✅ tables
```sql
SELECT * FROM QCTRL_ANALYSIS     WHERE <eff-date predicate from the bad import>;
SELECT * FROM QCTRL_ANALYSIS_CMP WHERE <same predicate>;
-- 26-01085198: bad effective dates from a client gas-analysis import; cleanup script deletes these rows.
```

---

## 19. Escalation Guidance

**Engineering (defect) when:**
- Web vs Classic divergence on the batch screens reproduces on a supported patch level (§5) — cite the §17 family.
- A batch step *creates* duplicates (CTRMTR/GETOPENINV with reversals + end-dated meters — fixed 2025.04.1.13; WHMEASIMP deleting/overriding measured volumes; rerun-vs-same-month-PPA corruption) — these are version-gated code fixes; check the client's version first and answer with the fix version if it already exists.
- Constant (not stats-related) performance degradation with a captured long-running SQL (§9b).
- HISTPURGE/QARCHIVE failures matching #1650552/#1689869 signatures on current versions.

**Cloud Ops (config/operational) when:**
- Stuck jobs → QPEC/QTIPS service restart + UX script (§4). This is the default first move for "nothing runs".
- Post-refresh breakage (connections pointing at PRD, missing facility configs, FTP/file paths, Connection Management .NET entries) (§10, §13).
- Archive-group connection details, data-fix scripts (delete dups, orphan cleanup, timeslice corrections) — script review + deployment workflow (#1776936 pattern). All such scripts: verify-SELECT first, scope tightly, wrap in a transaction.

**Neither (close as Training/Customer Error) when:**
- The error names missing month-keyed setup (rate factor, index value, accounting date record, CCT fee tab, inactive meters) (§16-3).
- The user broke sequence themselves (facility-level rerun then company jobs out of order; manual accounting-date opens during testing; cancelled a run mid-flight) (§16-1/2/5).
- The ask is procedural: unapproval, purge of a wrongly-run month, archive guidelines (§16-5/8).

**Honesty notes (mining caveats):**
- 24/111 actionable cases had an **empty Resolution__c** (notably the Genesis 2024 go-live wave and several ONEOK 2022.10 items closed against patch bundles); clusters built on those rely on Subject text — resolution pattern partially unclear from mined cases for: 22-00824980 (QARCHIVE failed-execute), 24-00960610 (multi-job Web error), 23-00898608 (Lock Plant error).
- Root_Cause__c labeling is noisy: several "Application Configuration" cases were actually patched defects (25-01038844, 25-01034452 — "bug fix with patch") and several "Software Defect" cases were pure ops (22-00516202 — services restart). Treat the cluster, not the label, as the signal.

---

*Skill created: 2026-06-11. Based on 590 closed TIPS Batch_Processing-group cases (categories: Batch Job Submittal, Processing, Maintenance, Purge/Archive, Archiving); 111 actionable cases mined in full; 30 Training/Customer Error cases sampled; ADO items #1636859, #1718964, #1752343, #1745358, #1746523, #1691458, #1744413, #1772117, #1776936, #1778789, #1713703-07, #1689869, #1650552, #1460618, #1633473, #1644834, #1706988, #1777919, #1777056, #1757579, #1744847. Code anchors: Quorum.TIPS.Batch/QPDllTurboTips/StepExecution/CTRMTR.cs, Quorum.Tips.TurboTips.Allocate/CTRMTR/psCTRMTR.cs, <CLIENT>.TIPS.ClassicBatch/QPDllTipsAllocate/QSQL_RetrieveClosingInventory.cpp, <CLIENT>.TIPS.Metadata/QARCH_CTRL_PROCESS*.json.*
