# SKILL: QCA — JIB / Fixed Assets / LOS Defect & Fix Reference (ADO-mined)

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** Quorum Upstream Accounting — **QCA** (Cost Accounting), focused on **JIB** (Joint Interest Billing), **Fixed Assets**, and **LOS** (Lease Operating Statement)
**Source:** Azure DevOps **Bug** work items under Area Path `QuorumSoftware\Engineering\Financials` (org QuorumSoftware), State Closed/Resolved, title-matched on JIB / joint interest / fixed asset / DD&A / inventory / LOS / lease operating / billing / billing deck / JEA. 169 bugs matched; ~52 deep-read (description + repro + dev comments + linked PRs).
**Companion skills:** the sibling Upstream-ADO skills for QRA / QDO / QCFS; for SF-case-driven investigation use the QPTM/TIPS L4 skills. This skill is a *root-cause + fix* lookup, not a config how-to.

> **Use When:** an L4 engineer has a QCA case touching **JB005 process control / Initiate Billing Cycle**, **JIB owner/rebill allocation child jobs**, **LOSDD / LOSLOAD import & LOS reports**, **JEA (Journal Entry Allocation) reports/process**, **JIBLink export**, **JIB→QCFS posting/tie-out**, **JBR0xx billing reports**, or **Fixed Assets reports** — and needs to know "is this a known defect, what was the root cause, is it fixed, and in which build?"

> **Evidence base & honesty notes:**
> - These are **internal engineering bugs** (most found during QA/regression of core releases, area "Committed Backlog"/"Financials"), not customer SF cases. Only a handful carry an SF case number in the title/description; where seen it is cited (e.g. `25-01013387`, `24-00953070`). Most are keyed by ADO **#id** + **iteration path** (e.g. `24.18`) + **title release prefix** (`2024.10:` / `2025.04:` / `2026.04:`) + **Tags** (`Not 2024.10 Ups`, `Robot RN 2026.04`, `2022.10 GA QA`).
> - **No `IntegrationBuild` field was populated** on any of these bugs. "Fixed-in-build" below is inferred from the **title release prefix**, the **iteration/sprint path**, and **Tags**. Treat it as the release train, and always confirm the exact build/script in `Quorum.Upstream.ReleaseNotes` and the linked PR's `targetRefName` before telling a client it's fixed. PRs in this area merge to **`develop`** then cherry-pick to release/hotfix branches.
> - Where a bug had **no clear root cause/fix** in its description/comments/PR (closed as Rejected/Duplicate/Deferred, or "closed due to inactivity"), it is labelled as such — not invented.
> - **Repo/code is shared.** Almost every code/SQL fix lives in **`Quorum.Upstream.QCA.ClassicBatch`** (C++ batch), **`Quorum.Upstream.QCA.Database`** (T-SQL stored procs/reg-SQL), **`Quorum.Upstream.Database`** (core DB), **`Quorum.Upstream.Reports`** (Crystal/RDL), **`Quorum.Upstream.Metadata`** (picklists/grids), **`Quorum.Upstream.QCA.ClassicGUI`** (WinForms business rules). Repo names were resolved from the live PR links.

---

## TABLE OF CONTENTS
1. [Quick Triage Table](#1-quick-triage-table)
2. [The JIB pipeline (JB005) & key tables](#2-the-jib-pipeline-jb005--key-tables)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — JB005 / Initiate Billing Cycle & JIB-step process failures](#4-cluster-a)
5. [Cluster B — JIB Owner/Rebill Allocation child-job splitting (counts & memory)](#5-cluster-b)
6. [Cluster C — LOSDD / LOSLOAD import & LOS report processing](#6-cluster-c)
7. [Cluster D — JEA (Journal Entry Allocation) reports & interest process](#7-cluster-d)
8. [Cluster E — JIBLink export](#8-cluster-e)
9. [Cluster F — JIB ⇄ QCFS posting / tie-out / bad BA-number data](#9-cluster-f)
10. [Cluster G — JBR0xx Billing Reports (cosmetic + AR-summary math)](#10-cluster-g)
11. [Cluster H — Fixed Assets reports & imports](#11-cluster-h)
12. [Cluster I — Close Reconciliation Report not reconciling](#12-cluster-i)
13. [Cluster J — Deployment / migration script-missing gaps](#13-cluster-j)
14. [Fix-Version Matrix](#14-fix-version-matrix)
15. [Diagnostic pointers (tables, queries, logs)](#15-diagnostic-pointers)
16. [Escalation Guidance](#16-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (engineer/client reports) | Likely cluster | First check |
|---|---|---|
| JB005 **Initiate Billing Cycle** fails: `Invalid column name '<COL>'` / `Not all required columns provided` / "registered SQL ... `m_INS_SEXT_CORE_INTFC`" | **A** | The QSTAG/SEXTN core-interface table is **missing a column** the reg-SQL inserts, or an IDENTITY hit BIGINT limit; collateral from a core DB change. §4 |
| JB005 step **"Create billing journal entries" / "Finalize and Post Results"** stops on error | **A** | Often **missing reference data** (`JBCDE_FAILURE` code) or a **chunk/Group-By config** producing invalid SQL. §4 |
| JIB process **launches hundreds of child jobs that do nothing** / warnings / takes forever | **B** | Split stored-proc computing child count from total rows, not the actual `PROC_GRP_SEQ_NO` stamping. §5 |
| JIB child job (`JBOACHILD` / `LOSEXTCHLD`) **memory / "not enough Contiguous Memory" / UCALC error** | **B / C** | 32-bit 2GB memory ceiling; slice size too large, or UCALC engine loaded when fast-calc configured. §5/§6 |
| **LOSDD_IMP** fails `Can't update batch ... 'Sel_Intfc_Transactions'` / "Row cannot be located for updating" | **C** | **Invalid data in `GONL_PROP`** — two properties on the same `ID_COST_CNTR`. Data fix. §6 |
| **Duplicate rows** in `QTRAN_LOS_CUSTOM_SL` / `QFACT_LOS` after LOSLOAD | **C** | Parallel child jobs querying by `ACCTG_MTH/ACTIVITY_DT` without an **ID-range** filter. §6 |
| **JEA003 report** fails to run / invalid SQL | **D** | Optional "Exclude Properties" param not handled; or >1 `SCODE_ATTR_TYPE` DISTRICT row needs `ATTR_GRP_CD='CC'` filter. §7 |
| **JIBLink export** excludes/duplicates invoices (esp. prepayment-only rebills) | **E** | Stored-proc join excludes fully-netted invoices; prepay billable in hold. §8 |
| JIB JE **won't post in QCFS** "Missing Vendor Suffix" / bad VENDOR_BA_NO | **F** | `USP_JIB_COMPRESSOR` inserting `' '` (space) instead of NULL into nullable vendor cols. §9 |
| **JBR030/031/036/037** billing report cosmetics / wrong OUTSTANDING BALANCE | **G** | Report formatting, or summary-field-in-formula math. §10 |
| Fixed Assets **FAR012 / MT Proof report picklist filter doesn't work** | **H** | Reg-SQL missing the WHERE-clause parameter. §11 |
| **Close Reconciliation Report** line not reconciling with JB350/JB520 | **I** | Mostly closed inactive/by-design; report grouping vs screen total. §12 |
| Process/proc/script "works in CORE_SUP but not here" / "missing during deployment" | **J** | Fluent-migration / maintenance-window script not applied. §13 |

---

## 2. The JIB pipeline (JB005) & key tables

```
[QCFS GL/AP vouchers, billable accounts]    [Fixed Assets, Compressor (JB040), Overhead config]
            │ QCFSIMPCYC / JBGLIMPORT (Initiate Billing Cycle)
            ▼
   JB005: Process Control — runs the JIB steps IN ORDER, each can fail independently:
     Well Completion Volume Load → Property Allocation (JB350) → Owner Allocation (JBOWNALLOC)
     → Rebill Owner/Property Allocation (JBREBILL) → Prepare JE (JBPREPJE) → Compute Overheads
     → Invoice Preparation (JBINVMNPRC) → Create Billing JEs → Initiate Billing Cycle (JBGLIMPORT)
     → Finalize and Post Results → Roll Date Forward (JBROLLDATE)
            │
            ├──► JIBLink export (JBINVJIBLK / "215 - Export to JIBLink", QP053)  → CSV to JIBLink
            ├──► JIB JEs flow back to QCFS (POSTWKFL / BUSSVCRUN) to post to GL
            └──► Reports: JBR030/031/036/037 billing, JBR055 Close Recon, JEA001/002/003, LOS00x
```

**Key tables (QCA database unless noted):**
- **`JBTRN_*`** — JIB transaction working tables: `JBTRN_CTF` (cost-transfer/charge), `JBTRN_OWNER_ALLOC`, `JBTRN_PREPARE_JE`, `JBTRN_PROCESS_ACTIVITY` (per-step state — drives JB005 green/red), `JBTRN_PROP_ALLOC_CSL_UPDATE`.
- **`JBSTG_*`** — JIB staging tables that child jobs read: `JBSTG_OWNER_ALLOC`, `JBSTG_INVOICE`, `JBSTG_JIBLINK_EXPORT_FINAL`. Each row stamped with `PROC_GRP_SEQ_NO` = which child slice processes it.
- **`JBCDE_*` / `JBCTRL_*`** — JIB code/control: `JBCDE_FAILURE` (CTF failure codes), `JBCDE_BUSINESS_SEGMENT` (`BILLING_EXPORT_IND`), `JBCTRL_PROCESS_DEPENDENCY` (JB005 step sequence).
- **`QSTAG_CORE_INTFC_IMP` / `STRAN_CORE_INTFC` / `SEXTN_CORE_INTFC_JIB` / `SEXTN_CORE_INTFC_LOSDD`** — the cross-module import staging chain (QCFS→JIB/LOS). Column drift here is the #1 Initiate-Billing-Cycle failure cause.
- **`QTRAN_LOS_RAW_DATA` / `QTRAN_LOS_FINANCIAL_SL` / `QTRAN_LOS_CUSTOM_SL` / `QFACT_LOS`** — LOS data + reporting fact table; `QSTAG_LOS_REPORT_DATA` for the report pre-process.
- **`GONL_PROP` / `SCTRL_COST_CNTR` / `DONL_DO_DETAIL`** — property, cost-center, DOI. Bad `ID_COST_CNTR` here breaks LOSDD_IMP.
- **`QARCH_QFCBATCH_SQL_TRACE` / `QARCH_PROCESS_MSG_LOG` / `QARCH_QUEU_PROCESS`** — batch diagnostics keyed by `PROCESS_QUEUE_ID` (PQID) and `MASTER_PROCESS_QUEUE_ID`. Always start here.

---

## 3. Decision Tree

```
QCA / JIB / FixedAssets / LOS issue
│
├─ A JB005 / batch STEP failed (STOPPED PROCESSING ON ERROR)?  → GET PQID + step name + exact COM/ADO error
│   ├─ "Invalid column name" / "Not all required columns" / m_INS_SEXT_CORE_INTFC / IDENTITY/BIGINT  → §4 (interface-column drift; core DB script)
│   ├─ "Create billing JEs" / "Finalize and Post" invalid SQL or missing JBCDE_FAILURE code           → §4 (ref-data / chunk Group-By)
│   ├─ LOSDD_IMP "Can't update batch ... Sel_Intfc_Transactions" / "Row cannot be located"             → §6 (GONL_PROP dup ID_COST_CNTR — DATA fix)
│   └─ Child job "not enough Contiguous Memory" / UCALC error / WCP status                              → §5/§6 (memory; split/slice; fast-calc config)
│
├─ Too many / too few child jobs, warnings, slow (not a hard crash)?  → §5 (split stored-proc count vs PROC_GRP_SEQ_NO stamping)
│
├─ Output/data wrong (process "succeeded")?
│   ├─ JIB JE won't post in QCFS ("Missing Vendor Suffix" / bad BA)     → §9 (USP_JIB_COMPRESSOR space-vs-NULL; control account)
│   ├─ JIBLink CSV missing/dup invoices                                 → §8 (export stored-proc join; prepay hold)
│   ├─ Multi-level allocation stops after first level                    → §5 (bad warning halting allocation — 106976)
│   └─ Report numbers wrong (JBR03x / JBR055 / JEA002)                   → §10 / §12 (report math / grouping)
│
├─ Report fails to RUN or picklist/filter broken?
│   ├─ JEA001/002/003                                                    → §7
│   ├─ FAR012 / MT Proof / Fixed Assets picklist filter                  → §11 (reg-SQL missing WHERE param)
│   └─ JBR03x cosmetic                                                   → §10
│
└─ "Works in CORE_SUP / other env but not here" / "missing during deployment"  → §13 (migration-script gap)
```

---

## 4. Cluster A — JB005 / Initiate Billing Cycle & JIB-step process failures
*(8 bugs deep-read; the single most common QCA support signature)*

**Symptom:** A JB005 step (most often **Initiate Billing Cycle** = `JBGLIMPORT`, also "Create billing journal entries", "Finalize and Post Results") shows **STOPPED PROCESSING ON ERROR** in the process monitor. The COM/ADO error names a column or registered SQL.

**Root causes seen (each is a real bug):**
- **Cross-module interface table is missing a column the reg-SQL inserts** — collateral from a core DB change that added a column to one of QCA/QRA/QCFS but not all three of the shared `QSTAG_CORE_INTFC_IMP`/`SEXTN_CORE_INTFC_*` tables.
  - **#1391488** (`21.10`): `Invalid column name 'BUS_UNIT_CD_POST_TO'`. Reg-SQL `m_INS_QSTAG_CORE_INTFC` was updated to insert `BUS_UNIT_CD_POST_TO` but the column was missing from the QCA/QRA QSTAG tables. Fix = add the column to QCA & QRA interface tables (core DB #1391511/#1391512); collateral of #1319801. **Fixed for 2021.10.**
  - **#1793723** (`26.07`, 2026.04): "Error in registered SQL: **`m_INS_SEXT_CORE_INTFC`**". Root cause per dev (Ben Weis): an **IDENTITY column needed to be widened (the change was a 2023 script `UPS_17.0.00.0026.0000_00_CORE_QCA_01_1599962.sql` that drops/re-adds index `IX_SEXTN_CORE_INTFC_JIB_4`); the test env had not had it applied** and an ID neared the int limit. Operational fix = apply the missing core script (drop index → widen → re-add). **Confirmed for 2026.04 train.**
  - **#185035** (`20.07`, 2020.03): `QJIBDeckMgr::Initialize() failed, Not all required columns provided` — Initiate Billing Cycle (`JBGLIMPORT`) couldn't import a record using a **varchar business-unit code** exported from QRA (collateral of #174585). Code fix in `Quorum.Upstream.QCA.ClassicBatch`. **Fixed 2020.03.**
- **Missing reference / code data** — **#1410266** (`21.23`): Initiate Billing Cycle DB-conflict errors because reference row **`JBCDE_FAILURE` code 'B'** was missing in the test env; inserting it cleared it. Data/env, not code.
- **Chunk-config produces invalid SQL** — **#1684125** (`24.18`, 2024.10): "Finalize and Post Results" failed; dev found a **non-empty chunk value set while the actual "GROUP BY" was left empty → invalid SQL syntax** in `INS_ARJournalStage`; introduced by chunk-configuration changes. Code fix PR #100347 (`Quorum.Upstream.QCA.ClassicBatch`). **Fixed 2024.10.**
- **Pre-existing bad data / stale JBTRN_PROCESS_ACTIVITY** — **#1555035** (`22.21`, 2022.10): Initiate Billing Cycle failed "Batch 06.24 on Company 100 is not posted" because an `FA120` Inventory-Subledger material-transfer batch was only partially posted; the validation `m_Sel_UnpostedEntriesQCA` queries `QCTRL_MTRL_TRANS`. Dev notes "we hit this every cycle" — bad/partly-posted MT data; cleaned via maintenance-window script. **Closed 2022.10 (data, recurring).**
- **"Create billing journal entries"** — **#1589042** (`23.07`, 2023.04 regression): step failed; fixed (PRs 82877/82888 in `Quorum.Upstream.QCA.ClassicBatch`). Note: dev flagged it "complete in 2023.04 but not in release notes" → **may be missing from RN; verify build**.
- **Post-but-not-rolled edits corrupt the run** — **#1725253** (`25.12`; SF **25-01013387**, client FMO): client edited JB030/JB035 after posting JIB but before `JBROLLDATE`, so re-roll errored. Long-term fix = add the **`PROHIBIT_CHANGING_HISTORY`** business rule (`QBusinessRuleProhibitChangingHistory`) to **JB035** (`QFrmPercentageOH`) — JB030 already had it; check `JBCDE_BUSINESS_SEGMENT.BILLING_EXPORT_IND=1` to block edits between post and roll. PR #112769 (`Quorum.Upstream.QCA.ClassicGUI`). Tag `not 2026.04 Ups` / `Recommend Open` — **long-term fix tracked, confirm it shipped before promising it.**
- **#1685018** (`24.21`) — "JIB process sequence not same as CORE_SUP / new process added": **Rejected**, root cause = pre-existing data in `JBTRN_PROCESS_ACTIVITY` / `JBCTRL_PROCESS_DEPENDENCY` (a stray `JBCTFDOI` entry), not a code change. Cleanup script, no product fix.

**Fix recipe:** Get **PQID + failing step + exact COM/ADO error** from the monitor (double-click the red row). Then:
1. `Invalid column name` / `Not all required columns` → the reg-SQL inserts a column missing from a QCA/QRA/QCFS shared interface table. Compare the three `QSTAG_CORE_INTFC_IMP` / `SEXTN_CORE_INTFC_*` tables; apply the core DB script. (#1391488, #1793723, #185035)
2. Missing-code-row error (`JBCDE_FAILURE`, etc.) → insert the reference row; promote to maintenance window. (#1410266)
3. "Batch not posted" at Initiate Billing Cycle → find the unposted `QCTRL_MTRL_TRANS`/FA120 batch via `m_Sel_UnpostedEntriesQCA`; finish-post or clean it. (#1555035)
4. Invalid-SQL on Create/Finalize → check chunk config (Group BY left empty with a non-empty chunk value). (#1684125)
5. Always scope re-runs by company + process period; verify in `QARCH_QFCBATCH_SQL_TRACE WHERE SQL_SUCCESS_IND=0`.

---

## 5. Cluster B — JIB Owner/Rebill Allocation child-job splitting
*(7 bugs deep-read; the dominant **engineering/performance** defect family, surfaced via "JIB stress testing")*

**Symptom:** The JIB allocation/invoice processes (`JBOWNALLOC`, `JBREBILL`, `JBINVMNPRC`, `JBPREPJE`) either **launch far more child jobs than there is data for** (many do nothing, emit warnings), or **child jobs hit memory exceptions** ("not enough Contiguous Memory") on large data.

**Root cause (the recurring one):** the split stored procedures called **`USP_CALC_SPLIT_VALUES_BY_KEY`** to decide the child-job count purely from **total record count ÷ recommended slice size**, but the records are then **grouped by a key (e.g. `BA_NO`)** and stamped into `PROC_GRP_SEQ_NO`. When one key holds a huge share of rows, the stamped group count and the launched child count diverge → empty child jobs + warning `CAJBINME04`. The reliable fix is to stamp with the **modulus** and **return the real group count**:
```sql
UPDATE JBSTG_OWNER_ALLOC SET PROC_GRP_SEQ_NO = 1 + SEQ_NO % @I_GRP_CNT
 WHERE PROCESS_QUEUE_ID = @IN_I_MASTER_PROC_QUEUE_ID;
-- then RETURN (@I_GRP_CNT)  -- the true number of child jobs to launch
```

| Bug | Process / proc | Root cause & fix | Build |
|---|---|---|---|
| **#1367134** | `USP_JIB_PREPARE_JE_SPLIT`, `USP_JIB_STAGE_INVOICE_SPLIT` (JBJEMINHLD) | Split count from totals, not stamping → 25 real groups but 163 child jobs. Proc fixed to return true count; also changed the "0 child jobs" **error** `CAJBINME04` to a **warning** (valid for rebills). PR #54934 (`Quorum.Upstream.QCA.Database`) + C++ msg change | ~21.18 (2021.x) |
| **#1367142** | `QPSJIBRebillReversal.cpp` (`#REBILL_REVERSAL_PERIOD` temp table) | The step ran the **create+insert of the temp table twice** (drop logic actually re-created it), leaving it on the connection. Split SQL into create / insert / drop. (`Quorum.Upstream.QCA.ClassicBatch`) | ~21.14 |
| **#1368892** | `JBOACHILD` child process | **Memory exception** loading too much at once via QPEC at slice size 10k. Lower slice + limit per-child load. | ~21.18 |
| **#1389411** | `QSQL_JIBOwnerAllocation.cpp` `m_SEL_OwnerAllocStageSvcDt` | Sub-select built temp table filtering only by `PROC_GRP_SEQ_NO`, not `PROCESS_QUEUE_ID` → exploded. Add PQID to the subselect. **Closed/Rejected** (folded into the family) | — |
| **#1416291** | `USP_JIB_OWNER_ALLOC_STAGE_SPLIT` | Same modulus/return-count fix as #1367134, applied to the owner-alloc split proc. Tag `Not 2024.10 Ups; Not 2025.04 Ups` → **core engineering, port status varies by client** | 22.03-era, maintenance |
| **#1354771** | `USP_JIB_STAGE_INVOICE_SPLIT` (Invoice Prep JBINVMNPRC) | Invoice-prep launched empty child jobs; an older NetSuite ticket 308442 had changed `USP_JIB_PRE_JOURNAL_SPLIT` correctly but this proc incorrectly. Return correct split count. | ~21.12 |
| **#79741** | "JIB Stored Procedure not proportionately creating Child Processes" (308442) | The original split-proportion fix (`USP_JIB_PRE_JOURNAL_SPLIT`). Closed/Validation Passed | Maintenance Sprint 43 |
| **#95060** | `JBPREPJE` of `JBOWNALLOC` | "Prepare JE Split can go out of bounds with large chunk size" — Owner Allocation fails "Owner Allocation Splitting Procedure Failed." Verified fixed | Maintenance Sprint 50 |
| **#106976** | Property Allocation (multi-level) | Multi-level alloc stopped after the first level with a bogus warning "Property … not a valid from property". Re-worked the bad warning so allocation continues. **Fixed in 2019.03.** | 2019.03 |

**Fix recipe:** confirm the mismatch — `SELECT PROC_GRP_SEQ_NO, COUNT(*) FROM JBSTG_OWNER_ALLOC WHERE PROCESS_QUEUE_ID=<master PQID> GROUP BY PROC_GRP_SEQ_NO` vs the launched child count in `QARCH_QUEU_PROCESS WHERE MASTER_PROCESS_QUEUE_ID=<master PQID>`. If counts diverge → the split proc on that client is an **old version**; bring it to the modulus/return-count version. If child jobs throw **memory** errors, reduce the slice size config (`JB_OWNERALLOCSUGG_SLICE_MAX_SIZE`, `..._MIN_SIZE`) and the concurrent child limit; the underlying 32-bit 2GB ceiling means very large per-child queries (100k+ rows) will fail.

---

## 6. Cluster C — LOSDD / LOSLOAD import & LOS report processing
*(6 bugs deep-read)*

**6a. LOSDD_IMP "Can't update batch ... 'Sel_Intfc_Transactions'" / "Row cannot be located for updating" — DATA bug, recurring**
- **#1721401** (`25.07`, 2025.04) and **#139189** (2019.09, **Rejected**) and **#1685518** (`24.19`, 2024.10) are the **same root cause**: **invalid data in `GONL_PROP` — two or more properties pointing at the same `ID_COST_CNTR`** (validations were off when set up). The cursor-based update can't locate its row.
  - Diagnostic: `SELECT A.ID_COST_CNTR,* FROM GONL_PROP A JOIN (SELECT ID_COST_CNTR FROM GONL_PROP GROUP BY ID_COST_CNTR HAVING COUNT(*)>1) B ON A.ID_COST_CNTR=B.ID_COST_CNTR ORDER BY A.ID_COST_CNTR;`
  - Fix: create the missing `SCTRL_COST_CNTR` and re-point `GONL_PROP.ID_COST_CNTR` (Jimmy Bidwell's scripts), then re-run after **Restage Cross Module Import Data**. Code in `Quorum.Upstream.QCA.ClassicBatch/QPDllCostAcctgLOS`. **Largely a data fix; "modify the query to prevent it" was considered but the practical fix is data cleanup each occurrence.**

**6b. LOSLOAD / Custom-LOS duplicate rows — child-job timing without ID-range filter**
- **#102203** (Custom LOS, Verified): LOSDD_IMP spins up multiple `LOSEXTCHLD` children; step `LOSCUSTEXT` lacked the **ID-range SQL variable** that `LOSEXTCHLD` already had → concurrent inserts produced **duplicates in `QTRAN_LOS_CUSTOM_SL`**. Fix = add ID-range param to the custom-LOS reg-SQL. (`Quorum.Upstream.QCA.Database` PR #10128)
- **#108888** (LOSLOAD, Verified): duplicates moving `QTRAN_LOS_CUSTOM_SL` → `QFACT_LOS` because `m_QcalLOSLoad_SEL_CUSTOM` (`QSQL_QcalLOSLoad.cpp`) child jobs query by `ACCTG_MTH`/`ACTIVITY_DT` and overlap before records are marked processed. Same family as #102203; needs per-child ID-range / proper PROCESS_IND gating.

**6c. LOS report pre-process / performance**
- **#105515** (Verified): `RPT_LOS` pre-process converted the org-hierarchy identity to **`CHAR(6)`**; with >6-digit identities the hierarchy fails to build. Fix = `CHAR(6)`→`CHAR(10)` in `QSQL_QcaLOSReportPreProcess.cpp > m_CREATE_ORGOREDER_VIEW` (`ORG_ORDERSEQ` in `QSTAG_LOS_REPORT_DATA` already holds 100).
- **#107643 / #107680** (CNR, Verified, "Performance; SQL Tuning"): the LOS DOI-join query (`QTRAN_LOS_RAW_DATA` JOIN `DONL_DO_DETAIL` with an `OR` on `ACTIVITY_DT`/`ACCTG_MTH`) and `MAX(ID) FROM QTRAN_LOS_FINANCIAL_SL` ran 40+×/hour consuming huge CPU. Fix = index recommendations + query tuning (core DB SIR 181049; `Quorum.Upstream.QCA.Database` PR #9902).
- **#257980** (APH, **Rejected**): `RPT_LOS002` ~20 min when the **top of a very large org hierarchy** is selected. The `OR`-in-join was later eliminated via a CTE (#1640745); APH ultimately **scheduled the pre-report process nightly** rather than a code fix. Slow only at the highest org level with huge hierarchy — largely **expected for that data shape**.
- **#1712620** (CEN, `25.05`): `LOSDD_IMP` stuck in **WCP** with **UCALC "not enough Contiguous Memory"** on a 20M-row import (1000+ child jobs). Engineering could **not reliably reproduce**; mitigation = new config **`AFE_COMMIT_COST_FORCE_FASTCALC`** + ensure global **`USELEGACYFORMULAENGINE=0`** so the UCALC DLL isn't loaded under fast-calc; re-stage + re-run via script. Pulled into stability work — **may still recur in latest on very large imports.**

**6d. Deprecation:** **#1770974** (2026.04) deprecated/disabled the unused **`LOS_IMPORT`/`LOSSUM`/`LOS_IMPDBG`** processes (use `LOSDD_IMP`). Cosmetic — don't expect these on QP053 after 2026.04.

---

## 7. Cluster D — JEA (Journal Entry Allocation) reports & interest process
*(4 bugs deep-read; mostly report SQL/view fixes via `Quorum.Upstream.Reports`)*

| Bug | Symptom | Root cause / fix | Build |
|---|---|---|---|
| **#75821** | JEA003 fails when the optional **"Exclude Properties"** param is not provided | Handle the null optional param. (`Quorum.Upstream.QCA.Batch`) | Maint Sprint 41 |
| **#1098169** | JEA003 staging **invalid SQL** when >1 `SCODE_ATTR_TYPE` row has `DESCR='DISTRICT'` | Add filter **`ATTR_GRP_CD = 'CC'`** to the staging query. Setup needs QCODEACCOUNTGROUP/QCODEACCOUNTATTRIBUTE/SCODE_ATTR_TYPE attributes to bucket accounts. | 21.09 |
| **#78671** | RPT_JEA001 Batch Audit returns no data when transfer destination is an **allocation group** | View/report fix. Verified deployed **2018.09**. | 2018.09 |
| **#78815** | JEA Interest Report incorrectly includes **already-processed** records | View fix (core DB SIR 175735). Verified **2018.09**. | 2018.09 |
| **#282975** | RPT_JEA002 Interest Calc. Balance **mismatches** the Journal Entry Subledger Transaction-Amount sum | **No defect** — the report and the subledger screen **group at different levels**; dev produced a walkthrough showing how to line them up. No code change. (closed) | n/a |

> **Insight:** the JEA report bugs are real but small (null-param handling, a missing `ATTR_GRP_CD='CC'` filter, a view that didn't exclude processed rows). The "numbers don't match RPT_JEA002" complaint (#282975) is usually a **grouping-level misunderstanding, not a bug** — verify the grouping before escalating.

---

## 8. Cluster E — JIBLink export
*(3 bugs deep-read)*

| Bug | Symptom | Root cause / fix | Build |
|---|---|---|---|
| **#74991** | JIBLink export **duplicating prepayments** across AFEs/properties | Stored-proc dedup fix (`Quorum.Upstream.QCA.ClassicBatch`/`.Database`). | Maint Sprint 41 |
| **#79213** | "Exclude from JIBLink" checkbox **not functioning** unless Default Profile Code set | Validation/flag fix (`Quorum.Upstream.Shared.ClassicGUI`). | Maint Sprint 44 |
| **#111034** | JIBLink export **excludes invoices entirely comprised of prepayment deductions** (esp. rebills) | The export proc join filtered out fully-netted invoices; the prepay billable records are placed in **hold** for the rebill period and picked up next month. Affects CNR/Camino, similar at PRC/MAC (client-specific JIBLink exports). | Maint Sprint 60 |
| **#205667** | JIBLink CSV **AGE section** shows descriptions other than "JIB Invoice" for current month | **Not a bug** — requirement wording unclear; "current month" = JIB invoices from that month, but Misc Invoice/Deposit (non-JIB AR) legitimately appear. Closed. | n/a |
| **#230601** | `JBINVJIBLK` (215-Export to JIBLink) **STOPPED PROCESSING ON ERROR** | An **AGE subquery join was wrong**: compared `CUSTOMEROPENITEM.IDBEOWNER` (INT) to `BUSINESSENTITY.USERKEY` (varchar); correct join is `COI.IDBEOWNER = BE.ID`. Core DB #230715. (introduced by a prior 09/2020 core change) | 2020.x |

**Note:** several clients run **client-specific JIBLink export** stored procs (PRC, MAC, CNR) — a core fix may need porting to the client repo.

---

## 9. Cluster F — JIB ⇄ QCFS posting / tie-out / bad BA-number data
*(3 bugs deep-read)*

- **#185437** (`21.10`, 2020.03) — **the canonical one.** JIB JEs from the **Compressor Rental Costs** step won't post in QCFS: `USP_JIB_COMPRESSOR` inserts **`' '` (a space) into `VENDOR_BA_NO`** (and other nullable vendor cols) in `JBTRN_CTF` instead of **NULL**; the space carries through to QCFS and fails **POSTWKFL** validation with **"Missing Vendor Suffix"**. Fix = insert **NULL** for all nullable vendor columns in the proc (`Quorum.Upstream.QCA.Database/USP_JIB_COMPRESSOR.sql`; core DB #1328441). **Fixed 2020.03.**
- **#242815** (`21.09`, **Rejected**) — the QA-side manifestation of the above (imported GL025 batch "Could Not Post", "Missing Vendor Suffix"); also includes a separate finding that a **GL025 batch not on a JIB-billable account (no JIB group code on GL013) simply won't flow to JB080** (expected). Folded into #185437.
- **#106653** (PRC, **Rejected/inactivity**) — JIB invoices not tying to QCFS AR076/AR085/AR173. Root cause traced to the **MINRLSE offset account being a QCFS Control Account** (control accounts reject imports); recommendation = use a proper **JIB AR Suspense** account. Config, not code.
- **#93899** (Verified, 2019.x) — QCFS batches with billable accounts at status **Approved Final** weren't picked up by JIB as unposted transactions. Fixed (`Quorum.Upstream.QCA.ClassicBatch` PR #7063).

**Fix recipe:** for "JIB JE won't post in QCFS / Missing Vendor Suffix," check `BATCHJOURNALENTRYLINE`/`BATCHJECUSTOMCODEBLOCKUPSTREAM` for `VENDOR_NO=' '` with NULL `VENDOR_SUF`, and trace back to `JBTRN_CTF` — the source is usually the compressor proc inserting a space (#185437). For "invoices not tying," verify the offset/suspense account isn't a QCFS **control account** and the GL account has a **JIB group code** on GL013.

---

## 10. Cluster G — JBR0xx Billing Reports
*(4 bugs deep-read; report-only, `Quorum.Upstream.Reports`)*

- **Cosmetic / formatting (RPT_JBR030/031/036/037):** **#165679, #165698, #166488** — dollar-sign inconsistency, text/box margins, vertical spacing. Pure report-layout fixes. Tag `2020.03; BLD`.
- **"Two unreadable superimposed lines when report has no data":** **#159637 (JBR036), #163370 (JBR030), #163424 (JBR031), #165184/#165567** — empty-dataset rendering. Report fixes, 2019.10–2020.03.
- **Wrong OUTSTANDING BALANCE (AR-summary variants):** **#168448 (JBR037), #168453 (JBR036)** — the **Invoice Total uses a summary field**, and combining a summary field into the `Balance Forward + Total Current Month + Invoice Total` formula is non-trivial in the report engine. Fixed for 2020.03; if a client reports a wrong AR-summary outstanding balance, this is the known area.

> These are low-severity report defects; none are data-corruption. If a client sees a wrong **balance** (not just cosmetics) on JBR036/JBR037, it's the summary-field math (#168448/#168453).

---

## 11. Cluster H — Fixed Assets reports & imports
*(3 bugs deep-read)*

- **#1655838** (`24.07`) — **FAR012 Location Stock Item Report**: Account-Number picklist **filter doesn't work**. Root cause = picklist **32075** reg-SQL `SELECT_DISTINCT_ACCT_NO` (distinct `ACCT_NO` from `QTRAN_AFE_SL`) **was missing the WHERE-clause parameter**. Add the filter param. (`Quorum.Upstream.Metadata` PR #95487). Tag `Not 2024.10 Ups` → fixed in 2024.04 line, **confirm port**.
- **#1690680** (`25.11`, 2024.10 regression) — **Fixed Assets MT Proof Report**: **Batch No picklist filter doesn't work** — same class of defect (picklist reg-SQL missing filter param). Fixed; `Quorum.Upstream.Metadata` PR #112060. Regression-bug RN not published.
- **#67623** — `FACOIMPORT` (Fixed Assets Core Import) errors inserting into the FA subledger. **Closed: process no longer used** (per Mark). Don't chase a fix.
- **#57226** (Maintenance, area "Maintenance and Overhead", Duplicate) — `MT_IMPORT` cartesian creating multiple Inventory-Catalog records. Inventory/MT overlap area — noted, not QCA-core.

**Pattern:** the live Fixed-Assets defects are **QP086 picklist filters not applying the WHERE parameter** (reg-SQL in `Quorum.Upstream.Metadata`). Quick to confirm: open the picklist, try to filter — if nothing narrows, it's this class.

---

## 12. Cluster I — Close Reconciliation Report not reconciling
*(read; mostly Rejected/inactive — important to know these were NOT fixed as code)*

- **#1320287, #1320340, #1320345, #1320374** — JBR055 Close Reconciliation Report lines ("Drilling Overhead", "Allocation Hold – Net Change / Beginning of Period", "Property Allocation") not reconciling with JB350/JB520 Resource-Amount totals. **All closed Rejected / "due to inactivity."** The reported case (#1320287) was a **grouping/expected-rounding** situation (report shows Resource Amount ÷ 2 as debit/credit; with no records it should show 0). **No code fix shipped** — treat as report-grouping/expected unless a fresh repro proves otherwise.
- **#179253** (Uncommitted Backlog, Rejected) — JB080 "Cost Interface Import" line not reconciling with Close Reconciliation Report. Same family, not fixed.

> **Caveat:** this cluster is the weakest on resolution — most were closed without a product fix. If a client raises a Close-Recon mismatch, **do not assume a known fix exists**; reproduce and check report grouping vs the screen total first.

---

## 13. Cluster J — Deployment / migration script-missing gaps
*(operational, recurs across releases)*

- **#1746136** (`25.16`) — `USP_TRUNCATE_JBTRN_JIB_JOURNAL` **missing during the 2025.04 deployment**. The script (`UPS_17.0.00.0027.0000_00_CORE_QCA_24_1683779.sql`, #1683779) was checked into 2024.10 **develop only**; a **Fluent-migration ordering issue** (script 25 checked in for 2024.10, then script 24 added for 2025.04) meant it wasn't re-applied. Fix = re-create the script and merge to the 2025.04 hotfix.
- **#1714885** (`25.05`) — `ARCLOSSL` (Archive/Purge LOS Financials) fails **"DLL not found"** in CORE_TST though OK in CORE_SUP. Root cause = the new **Archive-and-Purge DLL must be manually added to the app QPEC** (nightly deploy doesn't pick it up).
- **#1793723** (see §4) and **#1685018** (see §4) also reduce to **environment/script state**, not code.

> **Tell-tale:** "works in CORE_SUP / one env but not another," "missing during deployment," or a registered SQL/DLL/proc that exists in one env's DB but not another → this cluster. Check whether the **migration script / DLL was applied**, not the source code.

---

## 14. Fix-Version Matrix

> Fixed-in-build inferred from **title release-prefix / iteration / Tags** (no `IntegrationBuild` set on these bugs). PRs merge to `develop`; confirm exact build & cherry-picks in `Quorum.Upstream.ReleaseNotes`. SF case shown only where present in the bug.

| ADO # | State / Reason | Symptom (cluster) | Inferred fixed-in / release | Repo of fix | SF case |
|---|---|---|---|---|---|
| #1391488 | Closed/RfQA | Init Billing Cycle `Invalid column BUS_UNIT_CD_POST_TO` (A) | 2021.10 | core DB + QCA.Database | — |
| #185035 | Closed/RfQA | Init Billing Cycle varchar BU code (A) | 2020.03 | QCA.ClassicBatch | — |
| #1410266 | Closed/RfQA | Init Billing Cycle missing `JBCDE_FAILURE` (A) | 2021.x (env/data) | data | — |
| #1555035 | Closed/RfQA | Init Billing Cycle "batch not posted" (A) | 2022.10 (data/recurring) | data | — |
| #1589042 | Closed/RfQA | "Create billing JEs" step error (A) | 2023.04 (⚠ maybe absent from RN) | QCA.ClassicBatch | — |
| #1684125 | Closed/RfQA | "Finalize and Post" invalid Group-By SQL (A) | 2024.10 | QCA.ClassicBatch | — |
| #1793723 | Closed/RfQA | Init Billing Cycle `m_INS_SEXT_CORE_INTFC` / IDENTITY (A) | 2026.04 (script-driven) | core DB script | — |
| #1725253 | Closed/RfQA | Post-not-rolled edits; JB035 change-history rule (A) | 25.12; `not 2026.04 Ups` ⚠ confirm shipped | QCA.ClassicGUI | 25-01013387 |
| #1685018 | Closed/Rejected | JB005 sequence differs (A) | not a code fix (data) | — | — |
| #1367134 | Closed/RfQA | JIB split proc child-count (B) | ~2021.x maintenance | QCA.Database | — |
| #1367142 | Closed/RfQA | Rebill temp-table re-created twice (B) | ~2021.x | QCA.ClassicBatch | — |
| #1368892 | Closed/RfQA | JBOACHILD memory exception (B) | ~2021.x | QCA.ClassicBatch | — |
| #1416291 | Closed/RfQA | Owner-alloc split modulus fix (B) | maintenance; `Not 2024.10/2025.04 Ups` ⚠ port varies | QCA.Database | — |
| #1354771 | Closed/RfQA | Invoice-prep split launching empty children (B) | ~2021.12 | QCA.Database | — |
| #79741 | Closed/Validation | Split-proportion proc (B) | Maint Sprint 43 | QCA.Database | — |
| #95060 | Closed/Verified | Prepare-JE split out of bounds (B) | Maint Sprint 50 | QCA.Database | — |
| #106976 | Closed/Verified | Multi-level alloc stops after L1 (B) | 2019.03 | QCA.ClassicBatch | — |
| #1721401 | Closed/RfQA | LOSDD_IMP `Sel_Intfc_Transactions` (C) | 2025.04 (data fix) | data / QCA.ClassicBatch | — |
| #1685518 | Closed/RfQA | LOSDD_IMP DB errors / GONL_PROP dup (C) | 2024.10 (data fix) | data | — |
| #139189 | Closed/Rejected | LOSDD_IMP same dup-ID_COST_CNTR (C) | 2019.09 (data) | data | — |
| #102203 | Closed/Verified | Custom LOS dup rows — add ID-range (C) | Maint Sprint 58 | QCA.Database | — |
| #108888 | Closed/Verified | LOSLOAD dup into QFACT_LOS (C) | Maint Sprint 60 | QCA.ClassicBatch | — |
| #105515 | Closed/Verified | LOS report CHAR(6)→CHAR(10) org hierarchy (C) | Maint (2019.x) | QCA.ClassicBatch | — |
| #107643/#107680 | Closed/Verified | CNR LOS query perf/index (C) | Maint Sprint 58 | QCA.Database + core | — |
| #257980 | Closed/Rejected | APH LOS report slow at top org (C) | no code fix; schedule pre-process | — | — |
| #1712620 | Closed/Acceptance | CEN LOSDD_IMP UCALC memory/WCP (C) | 25.05 mitigation; ⚠ may recur on huge imports | QCA.ClassicBatch + QPEC | (CEN) |
| #1770974 | Closed/RfQA | Deprecate LOS_IMPORT (C) | 2026.04 | Metadata + QCA.Database | — |
| #75821 | Closed/RfQA | JEA003 optional Exclude param (D) | Maint Sprint 41 | QCA.Batch | — |
| #1098169 | Closed/RfQA | JEA003 needs `ATTR_GRP_CD='CC'` (D) | 2021.09 | QCA.Batch | — |
| #78671 | Closed/RfQA | JEA001 alloc-group destination (D) | 2018.09 | Reports | — |
| #78815 | Closed/RfQA | JEA Interest includes processed (D) | 2018.09 | Reports + core DB | — |
| #282975 | Closed/RfQA | JEA002 vs subledger mismatch (D) | no fix (grouping) | — | — |
| #74991 | Closed/RfQA | JIBLink dup prepayments (E) | Maint Sprint 41 | QCA.ClassicBatch | — |
| #79213 | Closed/RfQA | "Exclude from JIBLink" checkbox (E) | Maint Sprint 44 | Shared.ClassicGUI | — |
| #111034 | Closed/Verified | JIBLink excludes prepay-only invoices (E) | Maint Sprint 60 | QCA.Database (+client) | — |
| #205667 | Closed/RfQA | JIBLink AGE description (E) | no fix (requirement) | — | — |
| #230601 | Closed/RfQA | JBINVJIBLK crash — bad AGE join (E) | 2020.x | QCA.Database + core | — |
| #185437 | Closed/RfQA | Compressor JE bad VENDOR_BA_NO space (F) | 2020.03 | QCA.Database (USP_JIB_COMPRESSOR) | — |
| #242815 | Closed/Rejected | QCFS import "Missing Vendor Suffix" (F) | folded into #185437 | — | — |
| #93899 | Closed/Verified | Approved-Final QCFS batch not picked (F) | 2019.x | QCA.ClassicBatch | — |
| #106653 | Closed/Rejected | JIB↔QCFS AR tie-out (F) | config (suspense vs control acct) | — | — |
| #168448/#168453 | Closed/RfQA | JBR037/JBR036 wrong outstanding balance (G) | 2020.03 | Reports | — |
| #165679/#165698/#166488 | Closed/RfQA-Rejected | JBR030/031 cosmetic (G) | 2020.03 | Reports | — |
| #159637/#163370/#163424 | Closed/RfQA | JBR no-data superimposed text (G) | 2019.10–2020.03 | Reports | — |
| #1655838 | Closed/RfQA | FAR012 acct picklist filter (H) | 2024.04 (`Not 2024.10 Ups`) | Metadata | — |
| #1690680 | Closed/RfQA | FA MT Proof batch-no filter (H) | 2024.10 regression | Metadata | — |
| #67623 | Closed/Rejected | FACOIMPORT (H) | process retired | — | — |
| #1320287/#1320340/#1320345/#1320374/#179253 | Closed/Rejected | Close Recon not reconciling (I) | no code fix (grouping/inactive) | — | — |
| #1746136 | Closed/Verified | USP_TRUNCATE_JBTRN_JIB_JOURNAL missing deploy (J) | 2025.04 hotfix | Upstream.Database script | — |
| #1714885 | Closed/RfQA | ARCLOSSL DLL-not-found (J) | 25.05 (QPEC DLL deploy) | QPEC config | — |
| #1659695 | Closed/Duplicate | CNR prepay subledger rogue txns (F-adj) | dup of #1657661 (cancelled archive job scripts) | — | 24-00953070 |

*("RfQA" = Reason "Moved out of state Ready for QA", i.e. dev-complete and QA-verified, the normal terminal state for these internal bugs.)*

---

## 15. Diagnostic pointers (tables, queries, logs)

> SQL Server (Upstream is MSSQL, schema `dbo`). Always verify-SELECT before any UPDATE/DELETE and wrap in a transaction.

```sql
-- A. Find the failing step + error for a batch run (start here for ANY "stopped on error")
SELECT * FROM QARCH_QFCBATCH_SQL_TRACE WHERE PROCESS_QUEUE_ID = <PQID> AND SQL_SUCCESS_IND = 0 ORDER BY SEQ_NO;
SELECT * FROM QARCH_PROCESS_MSG_LOG    WHERE PROCESS_QUEUE_ID = <PQID> AND LOG_MSG_TYPE_CD NOT IN ('DEBUG','INFO');

-- B. Child-job count vs staged-group count (the split-proc divergence, §5)
SELECT PROC_GRP_SEQ_NO, COUNT(*) FROM JBSTG_OWNER_ALLOC WHERE PROCESS_QUEUE_ID = <masterPQID> GROUP BY PROC_GRP_SEQ_NO;  -- (or JBSTG_INVOICE / JBTRN_PREPARE_JE)
SELECT PROCESS_QUEUE_ID, PROCESS_ID, STATUS_CD, PARAM_DESCR_LIST FROM QARCH_QUEU_PROCESS WHERE MASTER_PROCESS_QUEUE_ID = <masterPQID> ORDER BY PROCESS_QUEUE_ID DESC;

-- C. LOSDD_IMP dup ID_COST_CNTR root cause (§6a)
SELECT A.ID_COST_CNTR, A.* FROM GONL_PROP A
JOIN (SELECT ID_COST_CNTR FROM GONL_PROP GROUP BY ID_COST_CNTR HAVING COUNT(*) > 1) B ON A.ID_COST_CNTR = B.ID_COST_CNTR
ORDER BY A.ID_COST_CNTR;

-- D. Interface-column drift (§4): confirm a column the reg-SQL inserts exists in ALL three product copies
SELECT TABLE_CATALOG, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'QSTAG_CORE_INTFC_IMP' AND COLUMN_NAME = '<COL>';
-- run against the QCA, QRA, and QCFS databases; a missing copy is the bug.

-- E. Bad vendor data blocking QCFS post (§9): space instead of NULL
SELECT VENDOR_NO, VENDOR_SUF, * FROM BATCHJOURNALENTRYMASTER A
JOIN BATCHJOURNALENTRYLINE B ON A.ID = B.IDBATJE
JOIN BATCHJECUSTOMCODEBLOCKUPSTREAM C ON B.ID = C.IDBATJELINE
WHERE A.USERKEY = '<batch>';  -- look for VENDOR_NO = ' ' with NULL VENDOR_SUF; trace back to JBTRN_CTF

-- F. JB005 step state (why a step is red / sequence wrong, §4)
SELECT * FROM JBTRN_PROCESS_ACTIVITY WHERE PROCESS_PERIOD = '<yyyy-mm-01>';
SELECT * FROM JBCTRL_PROCESS_DEPENDENCY ORDER BY 1;  -- stray rows change the JB005 sequence (#1685018)
```

**Where the code lives (resolved from live PRs):**
| Area | Repo | Notable symbols |
|---|---|---|
| JIB/LOS C++ batch | `Quorum.Upstream.QCA.ClassicBatch` | `QPDllCostAcctgJIB`, `QPDllCostAcctgLOS`, `QPSJIBRebillReversal.cpp`, `QSQL_JIBOwnerAllocation.cpp`, `QSQL_QcalLOSLoad.cpp`, `QSQL_QcaLOSReportPreProcess.cpp` |
| JIB/LOS stored procs & reg-SQL | `Quorum.Upstream.QCA.Database` | `USP_JIB_*` (`_COMPRESSOR`, `_PREPARE_JE_SPLIT`, `_STAGE_INVOICE_SPLIT`, `_OWNER_ALLOC_STAGE_SPLIT`, `_PRE_JOURNAL_SPLIT`), `USP_CALC_SPLIT_VALUES_BY_KEY`, `USP_TRUNCATE_JBTRN_JIB_JOURNAL` |
| Core/shared interface tables & scripts | `Quorum.Upstream.Database` | `QSTAG_CORE_INTFC_IMP`, `SEXTN_CORE_INTFC_*`, migration scripts `UPS_17.0.00.xxxx_...sql` |
| Reports (JBR0xx, JEA, LOS, Close Recon) | `Quorum.Upstream.Reports` | RPT_JBR030/031/036/037, RPT_JEA001/002/003, RPT_LOS002, JBR055 |
| Picklists / grids | `Quorum.Upstream.Metadata` | picklist 32075 `SELECT_DISTINCT_ACCT_NO` (FAR012), batch-no picklist |
| WinForms business rules | `Quorum.Upstream.QCA.ClassicGUI` | `QBusinessRuleProhibitChangingHistory`, `QBusinessRulePropEffDOI`, `QFrmCatasConstOH`(JB030)/`QFrmPercentageOH`(JB035) |
| QPEC / process host | `Quorum.Upstream.Application.QPEC` | child-process execution, DLL loading (ARCLOSSL) |

---

## 16. Escalation Guidance

**Is it fixed in the client's build?** Map the client release to the matrix:
- **2018.09** — JEA001/JEA002 report/view fixes (#78671, #78815).
- **2019.03** — multi-level allocation warning fix (#106976).
- **2020.03** — Compressor VENDOR_BA_NO NULL fix (#185437); varchar BU Initiate Billing Cycle (#185035); JBR03x cosmetics & AR-summary balance (#168448/#168453); JBINJIBLK AGE join (#230601).
- **2021.09/.10** — JEA003 `ATTR_GRP_CD='CC'` (#1098169); `BUS_UNIT_CD_POST_TO` interface column (#1391488).
- **2022.10** — partly-posted MT batch handling (#1555035).
- **2023.04** — "Create billing JEs" step (#1589042) **— verify it's actually in the RN, dev flagged it missing**.
- **2024.04 / 2024.10** — FAR012 picklist (#1655838, port-dependent); FA MT-Proof picklist (#1690680); "Finalize and Post" Group-By SQL (#1684125); LOSDD_IMP GONL_PROP data (#1685518).
- **2025.04** — `USP_TRUNCATE_JBTRN_JIB_JOURNAL` deploy script (#1746136); LOSDD_IMP `Sel_Intfc_Transactions` data (#1721401).
- **2026.04** — `m_INS_SEXT_CORE_INTFC`/IDENTITY (#1793723); LOS_IMPORT deprecation (#1770974). **JB035 post-not-rolled rule (#1725253) tagged `not 2026.04 Ups` — confirm before promising.**

**Route to Engineering (real code/proc defect) when:**
- A **split stored proc** launches the wrong child count → bring the proc to the modulus/return-count version (§5: #1367134/#1416291/#1354771).
- A **reg-SQL inserts a column missing** from one of the QCA/QRA/QCFS shared interface tables (§4: #1391488/#1793723) — needs a coordinated core DB change to all three.
- **Compressor / vendor data** writes a space instead of NULL (§9: #185437).
- A **picklist filter** doesn't apply its WHERE param (§11: #1655838/#1690680).
- Provide: **PQID + failing step + exact COM/ADO error**, client + company + process period, the `QARCH_QFCBATCH_SQL_TRACE`/`QARCH_PROCESS_MSG_LOG` rows, and which **build** the client is on.

**Handle as DATA fix (no product change) when:**
- LOSDD_IMP "Row cannot be located" → **dup `ID_COST_CNTR` in `GONL_PROP`** (§6a) — create `SCTRL_COST_CNTR`, re-point, re-stage, re-run.
- Init Billing Cycle "batch not posted" → finish-post / clean the partly-posted `QCTRL_MTRL_TRANS`/FA120 batch (§4).
- JB005 sequence "wrong" / step stuck red → stale `JBTRN_PROCESS_ACTIVITY` / stray `JBCTRL_PROCESS_DEPENDENCY` row (§4: #1685018).

**Handle as CONFIG (no code) when:**
- JIB↔QCFS tie-out off → offset/suspense account is a QCFS **control account**, or GL account missing a **JIB group code** (§9: #106653).
- JEA002 vs subledger "mismatch" → **report grouping level** (§7: #282975).

**Handle as DEPLOYMENT/ENV (§13) when:** "works in CORE_SUP but not here," "missing during deployment," DLL-not-found, or a proc/script present in one env's DB but not another → check the **migration script / DLL was applied**, not the source.

**Weak-resolution areas (don't assume a known fix):** **Close Reconciliation Report** mismatches (§12 — almost all Rejected/inactive) and **very large LOS imports / top-of-hierarchy LOS reports** (§6: #257980 by-design, #1712620 not reliably reproducible). Reproduce first.

---

*Skill created 2026-06-14. Source: 169 ADO Bug work items under `QuorumSoftware\Engineering\Financials` matching JIB/FixedAssets/LOS terms (State Closed/Resolved); ~52 deep-read with descriptions, repro steps, dev comments, and linked PRs. No `IntegrationBuild` was set on any bug — fixed-in-build is inferred from title release-prefix / iteration path / Tags and MUST be confirmed in `Quorum.Upstream.ReleaseNotes` and the linked PR before stating fix availability to a client. ADO is read-only; nothing was modified.*
