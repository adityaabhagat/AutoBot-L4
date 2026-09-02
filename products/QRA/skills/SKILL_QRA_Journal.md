# SKILL: QRA Journal Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QRA (My Quorum Revenue Accounting — myQuorum / On Demand Upstream oil-and-gas revenue accounting)
**Scope:** The QRA **Journal** subsystem — the back end that turns settled/distributed revenue, owner-funds, tax, and manual entries into subledger (SL) and GL journal entries, then exports them to **QCFS** (the Quorum financial/GL system). Covers the JE-screen family (JE100/JE101/JE110/JE205/JE206/JE210), the journal batch processes (JEPOST, TAXJEPOST, JESUMMARY, JEPRESUM/JEPREPOST, JEROLLDATE, JEPURGE, DATAPUBLISH, QCFSEXPORT), MJE create/approve/post workflow, OFR (owner funds release) auto-posting, tax journalization (tax combo / ONRR / MMS), and journalization-level account configuration (GL013 / JE010).

> **Evidence base:** ~561 closed QRA Journal cases (`Case_Category__c IN ('Journal','Journal Entries')`). Root-cause split: (blank) 135, **Software Defect 131**, Customer Error 70, Training 29, Customer Cancelled 28, **Application Configuration 25**, Performance 21, others. This skill mines the **~76 actionable** cases (Software Defect 46 pulled + App Configuration 25 + ChangeConfig 2 = the actionable set, sampled to the most recent/representative) for fix recipes, plus a sample of Training/Customer-Error cases for the Expected-Behavior FAQ. Every claim cites a real SF case and/or ADO work item observed during mining. Where a cluster has no clear resolution it is marked *resolution pattern unclear from mined cases.*

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — QCFSEXPORT failures (HIGH FREQUENCY)](#4-cluster-a--qcfsexport-failures)
5. [Cluster B — JE Post / JESUMMARY batch failures & numeric overflow](#5-cluster-b--je-post--jesummary-batch-failures--numeric-overflow)
6. [Cluster C — Tax journalization (tax combo, ONRR/MMS, TAXJEPOST)](#6-cluster-c--tax-journalization)
7. [Cluster D — MJE create / approve / post status stuck](#7-cluster-d--mje-create--approve--post-status-stuck)
8. [Cluster E — OFR auto-posting & journalization-level config](#8-cluster-e--ofr-auto-posting--journalization-level-config)
9. [Cluster F — JE query/filter screen defects (JE101/JE110, Web vs Classic)](#9-cluster-f--je-queryfilter-screen-defects)
10. [Cluster G — Account journalization / GL013 / JE010 config](#10-cluster-g--account-journalization--gl013--je010-config)
11. [Cluster H — Missing DB connections / QPEC restart / service errors](#11-cluster-h--missing-db-connections--qpec-restart--service-errors)
12. [Known ADO Items](#12-known-ado-items)
13. [Diagnostic SQL](#13-diagnostic-sql)
14. [Expected-Behavior / User-Education FAQ](#14-expected-behavior--user-education-faq)
15. [Key Code, Processes & Repos](#15-key-code-processes--repos)
16. [Escalation Guidance](#16-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| `QCFSEXPORT` fails Final: **"Invalid account number NNNN-NNNN ... did not pass QCFS Validation"** | The GL account a journal line points at is **not set up / not visible to QRA in GL013** | §4 / §10 — add the account in **GL013** (visible to QRA); often a suspense offset account like `9999-9999` (26-01084517) |
| `QCFSEXPORT` **timeout** (`Execution Timeout Expired`, `JEVALCDBLK Validation not completed`) | Process exceeds the 1-hour command timeout | §4 — raise **`COMMAND_TIMEOUT_SEC`** config, **restart QPECs** to pick up the change (25-01007761) |
| `QCFSEXPORT` / `QRA Export` **stuck for hours**, missing JEs | Process hung; **do not just re-run** (dup risk) | §4 — engineering unblocks with a script; capture QPEC + MiddleTier logs (25-01001856, 24-00977460) |
| `QCFSEXPORT` **partial post** (only first 20K headers), JE100 trans-amt ≠ posted-trans-amt | Header-batch limit defect in the post | §4 — script to insert missing lines; validate JE101/JE110 by account (22-00560521) |
| Batch process **"Cannot insert duplicate key ... `UIX_TONL_TAX_INPUT`"** / `TAX_COMBO_INS_TAX_INPUT_2ND_ROLLUP` fails | Erroneous/duplicate rows in **`TONL_TAX_INPUT`** (tax-combo rollup); historical defect | §6 — delete the erroneous duplicate-key rows, re-run TAXJEPOST (22-00823344, 24-00960891, 25-01040037) |
| `JESUMMARY` / `JEPURGE` **completes with errors / arithmetic overflow** | A summary/report column is **`numeric(13,2)`** and the value needs 14+ digits | §5 — widen the column to `numeric(17,2)` to match `JTRN_SL_DETAIL.TRANS_AMT` (24-00938880 / ADO #1641942, 25-01054416) |
| `JEPOST` errors / runs long / memory | Memory or `JTRN_JEPOST_PROC` constraint/state issue | §5 — script to clear, plus memory fix (25-01037334, ADO #1641385) |
| MJE shows **POSTED but "Processing"**, or **VAL but should be POSTED** | Status not committed to `JONL_MANL_JE_HDR` | §7 — script to correct the MJE status; not a posting failure (22-00515826, 22-00577371) |
| MJE **won't post / approval "stopped processing on error"** | Account/account-group cross-ref missing, or RVNU_RUN_ID/config issue | §7 — check account/account-group setup; patch or revert UAT config (22-00577314, 24-00964011) |
| Revenue run ID **stuck in JE100**, can't roll period ("unprocessed batches") | Two RRIDs cross-referencing each other for cleaning | §7 — script to break the cross-reference so the period can close (22-00518226) |
| **OFR / owner funds release not auto-posting** on JE100 | `AUTO_POST_OFR` config not enabled in the right (client) DB layer | §8 — set **`AUTO_POST_OFR='1'`**, verify POSTWKFL completes; script into the client/QFC layer (25-01051314, 25-01034648) |
| Accrual/NGL volume missing or wrong on JE100; zero-dollar lines dropped | Zero-trans-amount entries not journalized | §8 — **`INCLUDE_ZERO_TRANS_AMT`** / `INCLUDE_ZERO_TRANS_AMT_BY_SYS_SRC`, `OFR_GRP_BY_GRS_AMT` (25-01041182, 26-01096204) |
| **JE101 / JE110 filter** returns wrong rows (Suspense Reason, Subledger No., Trans Amt) | Grid/Registered-SQL filter defect | §9 — fix Registered SQL + Grid Definition (24-00986688/ADO #1695727, 25-01048055) |
| Subledger query **inconsistent Web vs Classic** | Web codegen object out of sync with JE101 | §9 — regenerate `JtrnSlDetailWeb` to match JE101 (24-00965638) |
| Lump-sum posts with no detail / clearing account way off / production-tax not at well level | Account journalization **level** misconfigured | §10 — GL013 + JE010 journalization config (26-01101592, 25-01047071) |
| `Invalid object name '#ZERO_SOD'` / COA sync fails / DATAPUBLISH errors | A **DB connection (QLS / QLandDataHelper) is missing** or QPECs need restart | §11 — add the missing connection in `QARCH_CTRL_CONNECTION_INFO`; restart QPECs (24-00973140, 25-01059279, 25-01022599) |
| OFR / VL / PPN **"Progressive rounding error"** | Decimal-tracking / tolerance | §14 — `TOLERANT_DEC` layer; DO130 funds-only workaround (24-00961978, 22-00644851) |

---

## 2. Pipeline & Concepts

```
[Revenue Distribution / Valuation (VL) + Division Order (QDO) + Tax]
      │
      ▼  JE PREPARE  (JEPRECOMBO / JEPREPOST / JEPRESUM — build SL detail & summary)
[JTRN_SL_DETAIL (subledger journal detail), JTRN_GL_* (GL MTD/HIST), JONL_MANL_JE_HDR (manual JEs)]
      │
      ├──► JE POST / TAXJEPOST   (post SL + tax journal to GL; JTRN_JEPOST_PROC drives state)
      ├──► JESUMMARY / JEPRESUM  (summarize SL → JRPT_* reporting tables)
      ├──► JEROLLDATE            (roll accounting period: JTRN_GL_MTD_* → JTRN_GL_HIST_*)
      └──► QCFSEXPORT            (validate + export GL data → QCFS financial system / external GL)
            (screens: JE100 batch status, JE101/JE110 SL detail query, JE205/JE206/JE210 MJE)
```

### Key terms (QRA / upstream-accounting vocabulary)
- **SL (subledger)** — QRA's revenue subledger; detail rows live in **`JTRN_SL_DETAIL`** (the canonical journal-detail table; `TRANS_AMT` is `numeric(17,2)`). Summarized into `JRPT_*` reporting tables.
- **JE screens** — **JE100** = batch/run posting status; **JE101** = Subledger Detail Query (Classic) / *Subledger Detail Query* (Web); **JE110** = SL summary query; **JE205/JE206** = Manual JE detail entry; **JE210** = MJE approval; **JE010/JE005/JE020** = JE setup (group types, account cross-ref, decision-field validations); **GL013** = chart-of-accounts / GL account maintenance; **GL025/GL095** = GL batch / journal results.
- **MJE** = Manual Journal Entry. Lifecycle: **VAL** (validated) → approved (`SUB_APRV_NO`) → **POSTED**. Stored in **`JONL_MANL_JE_HDR`**. Status getting stuck out of sync with reality is a recurring data-fix cluster (§7).
- **RRID / RVNU_RUN_ID** = Revenue Run ID — the batch key that flows through JE100 → JEPOST → QCFSEXPORT.
- **OFR** = Owner Funds Release; **POSTWKFL** = the post-workflow process; **`AUTO_POST_OFR`** config controls whether the OFR batch auto-posts on JE100 (§8).
- **QCFS** = Quorum's financial/GL system (separate product). **QCFSEXPORT** validates QRA GL data (`JEVALCDBLK`, `SSTAG_CORE_INTFC`) and pushes it to QCFS; account validation is against **GL013**.
- **Tax combo / TAXJEPOST** = tax-combination rollup that writes **`TONL_TAX_INPUT`** then posts tax journals. The class is **`QPSTaxCombo`**; the SL post class is **`QPSJSLPosting`**.
- **ONRR / MMS batch type 16** = federal royalty (ONRR/MMS) journalization path; `JRNL_MMS_PROC_DEDUCT` config controls how deducts are journalized (§6).
- **PQID** (Process Queue ID) = key the batch message/log — always get it from the user.
- **QPEC** = the QRA batch/process engine service; many "restart services" cases are QPEC restarts to pick up a config or clear a hung process (§11).
- **Progressive rounding error** = decimal-tracking tolerance error in OFR/VL/PPN (DO funds transfers); managed via `TOLERANT_DEC` and the DO130 workaround (§14).

---

## 3. Decision Tree

```
QRA Journal case
│
├─ A batch process failed/hung? → GET PQID + EXACT PROCESS STEP + ERROR TEXT
│   ├─ QCFSEXPORT "Invalid account ... did not pass QCFS Validation"   → §4/§10 (add account to GL013, visible to QRA)
│   ├─ QCFSEXPORT timeout / JEVALCDBLK not completed                    → §4  (raise COMMAND_TIMEOUT_SEC, restart QPECs)
│   ├─ QCFSEXPORT / QRA Export stuck for hours, missing JEs             → §4  (script to unblock — DO NOT blind re-run; dup risk)
│   ├─ "duplicate key ... UIX_TONL_TAX_INPUT" / QPSTAXCOMBO / TAXJEPOST → §6  (delete erroneous TONL_TAX_INPUT rows, re-run)
│   ├─ JESUMMARY/JEPURGE "arithmetic overflow" / numeric error          → §5  (widen numeric(13,2) → numeric(17,2))
│   ├─ JEPOST errors/long/memory; JTRN_JEPOST_PROC constraint           → §5  (clear state script + memory fix)
│   ├─ JEROLLDATE transfer aborted (JTRN_GL_MTD_* → _HIST_*)            → §5  (escalate w/ PQID; period-roll data move)
│   └─ "Invalid object name '#ZERO_SOD'" / COA sync / DATAPUBLISH       → §11 (missing QLS/QLandDataHelper connection; QPEC restart)
│
├─ Journal output wrong (process didn't crash)?
│   ├─ Lump-sum / no detail / wrong clearing balance / wrong post level → §10 (GL013 + JE010 journalization level)
│   ├─ NGL/accrual volume wrong, zero-$ lines dropped                   → §8  (INCLUDE_ZERO_TRANS_AMT / OFR_GRP_BY_GRS_AMT)
│   └─ OFR batch didn't auto-post on JE100                              → §8  (AUTO_POST_OFR='1', POSTWKFL, client-layer script)
│
├─ MJE problem?
│   ├─ MJE status stuck (POSTED-shows-Processing / VAL-should-be-POSTED)→ §7  (script JONL_MANL_JE_HDR status)
│   ├─ MJE won't post / approval "stopped on error"                     → §7  (account/account-group cross-ref; revert UAT config)
│   ├─ RRID stuck in JE100, can't roll period                          → §7  (RRID cross-reference script)
│   └─ Huge MJE (90k+ rows) won't show in JE100 / can't unapprove        → §7/§14 (split into smaller batches)
│
├─ Query/filter screen wrong?
│   ├─ JE101/JE110 filter returns wrong rows (Suspense Reason, etc.)    → §9  (Registered SQL + Grid Definition fix)
│   └─ SL query Web vs Classic mismatch                                 → §9  (regenerate JtrnSlDetailWeb)
│
└─ "Progressive rounding error", escheat oddity, audit/"how do I…"     → §14 Expected-Behavior FAQ
```

---

## 4. Cluster A — QCFSEXPORT failures

**The single largest actionable journal signature.** `QCFSEXPORT` (screen **QP043**) validates QRA GL data and pushes it to the **QCFS** financial system. It is the last gate before close/check-write, so these come in **critical**. Four distinct sub-signatures:

| Sub-signature | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **"Invalid account number NNNN-NNNN ... Account did not pass QCFS Validation. Validation for `SSTAG_CORE_INTFC` not successful"** | A journal line (often a **revenue-suspense MJE** booked to an offset account like `9999-9999`) points at a GL account **not set up / not visible to QRA in GL013** | Add the account in **GL013** and make it **visible to QRA** (config). Decide with client whether suspense should offset to that account or a real one | 26-01084517 |
| **Timeout** — `Select failed <...>: Execution Timeout Expired`, `JEVALCDBLK Validation not completed successfully` | Export exceeds the default ~1-hour command timeout on a large dataset | Increase **`COMMAND_TIMEOUT_SEC`** config and **restart QPECs** so the new value is picked up | 25-01007761 |
| **Stuck for hours / never finishes**, JEs missing | Process hung mid-run | Engineering unblocks with a **script** (do **not** blind re-run — duplicate-entry risk). Capture **QPEC + MiddleTier logs** for RCA | 25-01001856 (script ADO #1711420 / RCA #1711544), 24-00977460 ("blank errors") |
| **Partial post** — only first ~20K header records posted; JE100 `trans_amt` ≠ posted `trans_amt`; JE101/JE110 detail short | Header-batch limit defect in the post step | **Script** to insert the missing lines (modified post SQL); then **validate JE101 + JE110 by account** (taxes/adjustments per line) | 22-00560521 (worked under 21-00104663) |
| "QCFSEXPORT Error" with no actionable text ("mystery error") | Usually one of the above (account validation / timeout) | Several closed via a **KB article** handed to the user; reproduce against GL013 + the PQID log | 24-00984839, 24-00977775, 23-00936225 |

**Fix recipe:**
1. Get **PQID** and read the QP043 message log — the real error (invalid account / timeout / validation) is in the log, not the toast.
2. **Invalid account** → look up the account on the failing line in **GL013**; if missing/not-visible-to-QRA, add it (26-01084517). This is the most common QCFSEXPORT cause.
3. **Timeout** → raise `COMMAND_TIMEOUT_SEC`, restart QPECs (25-01007761).
4. **Stuck** → do not re-run; escalate for a clean-up/unblock script; pull QPEC + MiddleTier logs (25-01001856).
5. **Partial/short post** → script the missing lines and reconcile JE101/JE110 by account (22-00560521).

---

## 5. Cluster B — JE Post / JESUMMARY batch failures & numeric overflow

Journal batch processes (**JEPOST**, **JESUMMARY**, **JEPRESUM/JEPREPOST**, **JEROLLDATE**, **JEPURGE**) crashing at a step.

| Step / signature | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **JESUMMARY fails / "arithmetic overflow"** inserting summary rows | Target summary column is **`numeric(13,2)`**; a real value needs 14+ digits | Widen the column. Confirmed defect | 24-00938880 / **ADO #1641942** (Bug, Closed); script-approval #1434672 (PRM) |
| **JEPURGE completes with `CSE`** — `Error setting value for column BFR_PRG_CREDIT_SUM / AFTER_PRG_CREDIT_SUM / *_DEBIT_SUM for ... JRPT_PRG` | Same root cause: those **`JRPT_PRG`** columns are `numeric(13,2)` but the purge sum is 14 digits | **SQL script to widen `BFR_PRG_*`/`AFTER_PRG_*` to `numeric(17,2)`** (match `JTRN_SL_DETAIL.TRANS_AMT`) | 25-01054416 |
| **JEPOST errored** (needed for close) | Initial data issue + **memory** | **Script** for the data (ADO #1752013) + **memory** addressed (ADO #1749635) | 25-01037334 |
| **JEPOST allowed for an RRID flagged "prevent posting"** | State in **`JTRN_JEPOST_PROC`** for that RRID | Script to reset the status in `JTRN_JEPOST_PROC`; TAXJEPOST then completes "No data posted to GL" (no impact). Long-term RCA 25-01035223 | 25-01034938 |
| **Invalid check constraints on `JTRN_JEPOST_PROC`** | Schema/constraint defect | Fixed for CCI/ENC/CORE/MAC | **ADO #1641385** (Bug, Closed) |
| **JE Post combined w/ Tax runs 35 min then "error deleting records from `DONL_DO_HDR`"** (`QPSJSLPosting.cpp:1240`) | Defect in the SL-posting delete | **Included in Upstream Patch 27** | 22-00651672 |
| **JEROLLDATE "transfer aborted"** moving `JTRN_GL_MTD_TAX→JTRN_GL_HIST_TAX` / `..._ADJ_CTGY` for a slice | Period-roll data-transfer failure mid-slice | Escalate with PQID; verify the slice ranges before/after; do not roll forward until clean | 22-00650815 |
| **JEPRESUM hanging / deadlocking** (account group 5; multiple JEPRESUMs same PQID) | Concurrency/perf defect | Engineering (FSTR-3449/3261 era) | 22-00512578, 22-00512536, 22-00512476 |

**Fix recipe:** get **PQID + step + exact error**. The **`numeric(13,2)` overflow** is the dominant defect family here — when JESUMMARY/JEPURGE/JEPRESUM throws an arithmetic/insert error on a sum column, check the target column's datatype against `JTRN_SL_DETAIL.TRANS_AMT` (`numeric(17,2)`) and widen it (24-00938880, 25-01054416). For JEPOST state stuck on an RRID, the unblock is a scoped `JTRN_JEPOST_PROC` status script (25-01034938) — but always open/confirm the long-term RCA case.

---

## 6. Cluster C — Tax journalization (tax combo, ONRR/MMS, TAXJEPOST)

Tax-side journalization run by **TAXJEPOST** / the **tax-combination rollup** (class **`QPSTaxCombo`** in `QPDllRevenueAcctgBR`), writing **`TONL_TAX_INPUT`**.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **"Cannot insert duplicate key row ... `UIX_TONL_TAX_INPUT`"** / `TAX_COMBO_INS_TAX_INPUT_2ND_ROLLUP` failed / `QPSTAXCOMBO` failed Execute | **Erroneous/duplicate rows already in `TONL_TAX_INPUT`** (often historical bad TX-type PPN data, e.g. TX70) collide on the unique index during the 2nd rollup | **Delete the erroneous duplicate-key rows** from `TONL_TAX_INPUT` (the dup key is printed in the error), then re-run TAXJEPOST. Recurring — typically needs a script each time | 22-00823344, 24-00960891, 25-01040037 |
| **Tax combo failed to insert zero'd-out rebook records** | Duplicate-key rebook rows | Script to clean the offending keys (dup-key value given in the case) | 24-00960891 |
| **ONRR batch type 16 not journalizing NGL deducts to the clearing account** (goes to "other deductions" instead) | `JRNL_MMS_PROC_DEDUCT` config | **Set `JRNL_MMS_PROC_DEDUCT = FALSE`** (script to insert the config on the client layer, e.g. SEP) | 25-01047071 |
| **`TRRYLMMSRF` (ONRR royalty final) SPE "no records found"**, holding the period roll | No data on TR015 even after PRELIM (`TRRYLMMSRP`); stale proc/staging rows | **Clean-up scripts**: null `TSTG_MMS_RYL_SL.LAST_VL_PROC_DT` for the prod date; delete the stuck PQIDs from `GTRN_PROC_BCH_NO`, `JTRN_JSTG_PROC`, `JTRN_JEPOST_PROC`, `TTRN_MMS_RYL_2014_PEND_SUM`; re-run PRELIM then FINAL. Long-term 25-01034907 | 25-01033813 |
| **PPN failing in TAXJEPOST** (oil PPN) | Erroneous historical tax data in `TONL_TAX_INPUT` (defect-origin) | Delete the erroneous data, re-run | 22-00823344 |

**Fix recipe:** the **`UIX_TONL_TAX_INPUT` duplicate-key** is the dominant tax-journal signature and almost always resolves by **deleting the specific erroneous duplicate row(s)** named in the error and re-running TAXJEPOST (verify-SELECT first). For ONRR/MMS deduct mis-journalization, the lever is the **`JRNL_MMS_PROC_DEDUCT`** config. For ONRR royalty-final "no records," clear the staging/proc tables for the PQIDs and re-run PRELIM→FINAL.

---

## 7. Cluster D — MJE create / approve / post status stuck

Manual JE lifecycle (`JONL_MANL_JE_HDR`): **VAL → approved (`SUB_APRV_NO`) → POSTED**, across JE205/JE206/JE210. Most are **data fixes** to realign status, or config reverts.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **MJEs in JE205 "Posted" but show "Processing"** | Status not committed | **Script** to update posted MJEs stuck in Processing | 22-00515826 |
| **MJEs status VAL — should be POSTED** (batch proof attached) | Status update didn't fire on approval | **Script** to update stuck-Validated MJEs to Posted in **`JONL_MANL_JE_HDR`** | 22-00577371 |
| **Revenue Run ID stuck in JE100**, can't roll period ("unprocessed batches… referencing the other for cleaning") | **Two RRIDs cross-referencing each other** | **Script** to break the cross-reference so the client can close | 22-00518226 |
| **MJE approval "stopped processing on error"** — "major product code not on account/account group cross-reference" | Account / **account-group cross-reference** missing for the target account | Patch deployed to client PRD; verify account-group / cross-ref setup | 22-00577314 |
| **Suspense MJEs error on submit** — "unable to get next `RVNU_RUN_ID`"; SPE on JE100 | A **UAT config change** (Land Payments testing) broke it; header didn't roll back on failure | **Revert the config** to prior values + script to fix orphaned headers; restart services. Won't occur in PRD if configs are correct | 24-00964011 |
| **JEMANLBCOM no longer works** — "UNABLE TO UPDATE ALL MJE HEADER RECORDS TO APPROVED STATUS (`SUB_APRV_NO = -1`)" | Bulk-approve update defect | *resolution pattern unclear from mined cases* (Resolution blank) | 24-00971395 |
| **JE206 requires "Contract" fields** for an account that shouldn't need them (e.g. 120-00-5000) | Account defaulted to **JE Group Type 9** in JE010/JE005, which excludes Contract Number | Known bug — fixed in a later release; **upgrade** to get the fix | 24-00947974 |
| **Unable to unapprove a MJE / 90k+-row MJE doesn't show in JE100** | Oversized MJE batch | **Split the MJE into smaller batches** and re-process | 26-01063658 |
| **Revenue MJE won't post — CE status (Rejects/Impaired)** | Entry stuck in CE | *resolution pattern unclear from mined cases* (Resolution blank) | 22-00669882 |

**Fix recipe:** for "status stuck," confirm what actually happened (was it posted in GL?) before scripting — then a scoped **`JONL_MANL_JE_HDR`** status update realigns it (22-00515826, 22-00577371). For "won't post / approval errors," check (a) **account / account-group cross-reference** setup for the target account (22-00577314), (b) whether a **recent UAT config change** broke it (24-00964011), (c) **batch size** for very large uploads (26-01063658). For RRIDs blocking a period roll, it's the **cross-reference script** (22-00518226).

---

## 8. Cluster E — OFR auto-posting & journalization-level config

How owner-funds-release and zero-dollar entries get journalized — almost all **config**, mostly client-layer.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **OFR not auto-posting** on JE100 after POSTWKFL completes | **`AUTO_POST_OFR`** not effective in the right DB layer | Set **`AUTO_POST_OFR='1'`**; **script** the config into the client/QFC database to enable OFR auto-posting | 25-01051314, 25-01034648, 26-01065786 |
| **Missing accrual/NGL volume** — entries where revenue = deducts (`trans_amt=0` but `trans_qty<>0`) are dropped | Journal didn't include zero-dollar lines | New **global-config option to journalize zero transaction amounts**: **`INCLUDE_ZERO_TRANS_AMT`** (and `..._BY_SYS_SRC`). Related: `OFR_GRP_BY_GRS_AMT` groups OFR JEs by gross amt/qty | 25-01041182 |
| **NGL volume in JE100 doesn't tie to RD031** (e.g. −53,480 vs 116,787) | Zero-trans-amount VL lines excluded | **`INCLUDE_ZERO_TRANS_AMT='1'`** and **`INCLUDE_ZERO_TRANS_AMT_BY_SYS_SRC='VL'`** | 26-01096204 |
| **DO PPN moved balances between contracts** on the A/P clearing account (224028) | Missing client files | "Added the missing files" (config/deploy) | 22-00698363 |
| **Pre-Checkwrite returned no journal records to post** | Config/setup | App Configuration (Resolution detail thin) | 24-00978093 |

**Fix recipe:** OFR-not-auto-posting is the headline here — confirm **`AUTO_POST_OFR='1'`** is set **in the layer the process actually reads** (UAT vs PRD vs QFC client DB), confirm **POSTWKFL** completes, then script the config in if missing (25-01051314). When a *volume* (NGL/accrual) doesn't tie between JE100 and the revenue screen (RD031), suspect **zero-trans-amount exclusion** → `INCLUDE_ZERO_TRANS_AMT` family (26-01096204, 25-01041182).

---

## 9. Cluster F — JE query/filter screen defects

JE101 (Subledger Detail Query) and JE110 query/grid filters returning wrong rows — **Software Defect**, fixed by correcting the **Registered SQL + Grid Definition** (and, for Web, the codegen object).

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **JE101 Suspense Reason filter does not work** (breaks escheat reconciliation) | Filter not wired to the grid query | Fixed | 24-00986688, 25-01002577 / **ADO #1695727** (Bug, Closed); related EQT #1537863 (Suspense Reason not updating in JE101 with OFR) |
| **JE110 filter on Suspense Reason = SL returned 7S records** | Wrong grid/registered SQL mapping | **Updated Registered SQL + Grid Definition on JE110** | 25-01048055 |
| **JE101 additional defects**: State decode wrong, Transaction-Amount filter broken, Subledger-No filter (esp. "Or") broken, no thousands separators | Multiple grid/filter issues | Tracked as follow-on to 24-00986688 (Resolution detail thin on the follow-on) | 25-01018434 |
| **SL query inconsistent Web vs Classic** | Web object diverged from JE101 | **Created new `JtrnSlDetailWeb` codegen object** to match JE101 (Classic) and the Web Subledger Detail Query | 24-00965638 |
| **JE100 not showing account details for older entries** | Query/grid scope | App Configuration (detail thin) | 25-01046385 |
| **JE205 missing batch type and status (PRD)** | Grid/metadata | App Configuration | 23-00923968 |

**Fix recipe:** filter-returns-wrong-rows on JE101/JE110 is a **Registered SQL + Grid Definition** fix (25-01048055; ADO #1695727 for the JE101 Suspense Reason). For **Web-vs-Classic** discrepancies, the SL Web grid is a **codegen object (`JtrnSlDetailWeb`)** that must be regenerated to match the Classic JE101 query (24-00965638). These ship in a release/patch — confirm the client's build.

---

## 10. Cluster G — Account journalization / GL013 / JE010 config

"The journal posts to the wrong account / at the wrong level / with no detail" — **Application Configuration** in **GL013** (account maintenance) and **JE010** (journalization setup), validated in GL095.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **Lump-sum amounts posted with no detail; clearing account shows a $10MM balance**; production-tax not at well/cost-center level; A/R & cash-clearing not at purchaser level | Journalization **level/detail** misconfigured for those accounts | Configuration change in **GL013 + JE010** so tax posts at cost-center (well) level and A/R/clearing at purchaser level; validate in **GL095** | 26-01101592 |
| **QCFSEXPORT "Invalid account 9999-9999"** (revenue-suspense offset) | Account not in GL013 / not visible to QRA | Add account to **GL013** visible to QRA (see §4) | 26-01084517 |
| **JEMASSWO severance-tax + state-payable write-off not working together** | Account-group / keyword setup | **Additional config around account groups and keywords** | 25-01013760 |
| **OFRs to Internal Owners — incorrect account journalization** | Journalization logic for internal-owner OFRs | Code fix | 22-00547108 / **ADO #210222** (Bug, Closed) |
| **Permian Upgrade — COA Maint: account won't push to QRA** | Missing DB connections (see §11) | Add QLS / QLandDataHelper connections | 24-00973140 |
| **Entries associated with MEGs** | Journal-group/account config | App Configuration (detail thin) | 24-00976166 |

**Fix recipe:** for "posts to wrong account / wrong level / no detail," the levers are **GL013** (does the account exist, is it visible to QRA, at what level) and **JE010** (group type & journalization level — recall **JE Group Type 9 excludes Contract Number**, §7/24-00947974). Validate the result in **GL095** before close. Account-group/keyword setup drives write-offs (JEMASSWO, 25-01013760) and MJE approval cross-ref errors (§7/22-00577314).

---

## 11. Cluster H — Missing DB connections / QPEC restart / service errors

A recurring operational signature, especially during **upgrades / new-environment cutover**: a process fails because a **named DB connection is missing** from `QARCH_CTRL_CONNECTION_INFO`, or the **QPEC** service needs a restart to pick up config or clear a hang.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **DATAPUBLISH completes with errors** → accounts created in GL013 don't appear in JE010 | A required DB connection (`QLandDataHelper`) missing | **Added a dummy `QLandDataHelper` to `QARCH_CTRL_CONNECTION_INFO`** identical to the QRA connection | 25-01059279 |
| **COA Maint sync error — account won't push to QRA** (Permian upgrade) | `QLS` and `QLandDataHelper` DB connections missing | **Added the missing connections** | 24-00973140 |
| **"Invalid object name '#ZERO_SOD'"** in `VLCALC_SOD_GET_SOD_ZEROGRSAMT` during Valuation Finalize | Service/session state; temp table not present | **Restart QPECs** | 25-01022599 |
| **QCFSEXPORT timeout** | Config not picked up | Raise `COMMAND_TIMEOUT_SEC`, **restart QPECs** (§4) | 25-01007761 |
| **Blank errors when running batches** | Transient / clears on re-process | Re-process the batch; capture logs if it persists | 24-00977460 |
| **Throttling — QRA DB queries time out** (e.g. `GCDE_SUSP_RSN_CD` 20 min, `JTRN_SL_DETAIL` 2 hr; Databricks external connection) | External-tool connection / DB resource | Engagement/perf review (not a journal code defect) | 24-00977368 |
| **Import / destination folder access denied** (Marlin import, UAT folder) | File-share permissions | Grant folder access | 23-00910056, 25-01020749 |

**Fix recipe:** during upgrades/cutover, "process X errors / account won't sync / DATAPUBLISH fails" is frequently a **missing connection in `QARCH_CTRL_CONNECTION_INFO`** (`QLS`, `QLandDataHelper`) — add it mirroring the QRA connection (25-01059279, 24-00973140). For transient `Invalid object name '#temp'` / "restart services," a **QPEC restart** clears it (25-01022599). Always restart QPECs after a config change so it's picked up (§4).

---

## 12. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1641942** | Bug / **Closed** | JESUMMARY process failing because of large values (arithmetic overflow) | §5 | 24-00938880 |
| **#1434672** | Bug / **Closed** | PRM Script Approval — JESUMMARY | §5 | — |
| **#1641385** | Bug / **Closed** | Invalid check constraints on `JTRN_JEPOST_PROC` (CCI/ENC/CORE/MAC) | §5 | — |
| **#1752013 / #1749635** | Script / Bug / **Closed** | JEPOST data-fix script + memory fix | §5 | 25-01037334 |
| **#1695727** | Bug / **Closed** | MEW 2024.04 — JE101 Suspense Reason Filter does not work | §9 | 24-00986688 |
| **#1537863** | Bug / **Closed** | EQT — Suspense Reason not updating in JE101 with OFR process | §9 | 22-00273667 |
| **#1711420 / #1711544** | Bug / **Closed** | RLY — QCFSEXPORT stuck, script review + RCA (QPEC/MT logs) | §4 | 25-01001856 |
| **#210222** | Bug / **Closed** | GLE — OFRs to Internal Owners have incorrect Account Journalization | §10 | 22-00547108 |
| **#1318171** | Bug / **Closed** | EQT — `CWOWFNDRLS` Progressive rounding error (OFR) | §14 | 22-00644851 |
| **#1321337** | Bug / **Closed** | Escheat amounts doubling upon Final process run | §14 | 22-00644853 |
| **#1726731** | Bug / **Closed** | SGY/GEC — CW005 checks stay (OS) but cleared (CL) in QCFS BR005 | §14 | 25-01020731 |
| Upstream **Patch 27** | Patch / Released | JE Post combined w/ Tax — `DONL_DO_HDR` delete error (`QPSJSLPosting`) | §5 | 22-00651672 |

> Many actionable cases were dispositioned **operationally** (config + client-layer script) with no single product WI: QCFSEXPORT account-in-GL013 (26-01084517), COMMAND_TIMEOUT_SEC raise (25-01007761), `TONL_TAX_INPUT` dup-key deletes (22-00823344, 24-00960891, 25-01040037), `JRNL_MMS_PROC_DEDUCT=FALSE` (25-01047071), `AUTO_POST_OFR='1'` (25-01051314), `INCLUDE_ZERO_TRANS_AMT` (26-01096204, 25-01041182), `numeric(13,2)→(17,2)` widen (25-01054416), missing `QARCH_CTRL_CONNECTION_INFO` connection (25-01059279, 24-00973140). Confirm exact build/patch in `Quorum.Upstream.QRA.ReleaseNotes`.

---

## 13. Diagnostic SQL

> **Caveat:** QRA runs on **SQL Server** (note `numeric(p,s)`, `#temp` tables, `dbo.` schema, native-client COM errors). Tables/columns below are from case repro text and code search — **verify against the client DB before scripting**, and always run a verify-SELECT before any DELETE/UPDATE, wrapped in a transaction.

```sql
-- A. Duplicate-key rows blocking the tax-combo rollup (UIX_TONL_TAX_INPUT, §6)
--    The error prints the exact dup key; confirm it before deleting.
SELECT * FROM dbo.TONL_TAX_INPUT
WHERE  /* match the printed dup-key tuple, e.g. */ PRDN_DT = '2023-03-01' AND PROD_CD = 166;

-- B. Numeric overflow on summary/purge columns (§5) — are they too narrow?
--    JTRN_SL_DETAIL.TRANS_AMT is numeric(17,2); these should match.
SELECT COLUMN_NAME, DATA_TYPE, NUMERIC_PRECISION, NUMERIC_SCALE
FROM   INFORMATION_SCHEMA.COLUMNS
WHERE  TABLE_NAME = 'JRPT_PRG'
AND    COLUMN_NAME IN ('BFR_PRG_CREDIT_SUM','AFTER_PRG_CREDIT_SUM','BFR_PRG_DEBIT_SUM','AFTER_PRG_DEBIT_SUM');

-- C. MJE status out of sync (§7) — POSTED vs what the screen shows
SELECT RVNU_RUN_ID, MANL_JE_NO, JE_STAT_CD, SUB_APRV_NO, POST_DT
FROM   dbo.JONL_MANL_JE_HDR
WHERE  RVNU_RUN_ID = <RRID>;          -- look for VAL/Processing rows that GL shows as posted

-- D. JEPOST state for an RRID flagged prevent-posting (§5/25-01034938)
SELECT * FROM dbo.JTRN_JEPOST_PROC WHERE PROCESS_QUEUE_ID = <PQID>;
-- (TRRYLMMSRF clean-up, §6/25-01033813, deletes the stuck PQIDs from
--  GTRN_PROC_BCH_NO, JTRN_JSTG_PROC, JTRN_JEPOST_PROC, TTRN_MMS_RYL_2014_PEND_SUM.)

-- E. JE100 vs revenue volume tie-out (zero-trans-amount exclusion, §8)
SELECT SYS_SRC_CD, SUM(TRANS_AMT) amt, SUM(TRANS_QTY) qty, COUNT(*) ct
FROM   dbo.JTRN_SL_DETAIL
WHERE  RVNU_RUN_ID = <RRID> AND COMP_NO = <CO>
GROUP BY SYS_SRC_CD;
-- Rows with TRANS_AMT = 0 and TRANS_QTY <> 0 are the ones INCLUDE_ZERO_TRANS_AMT controls.

-- F. Is the relevant journal config set (and in the layer the process reads)?
SELECT CONFIG_NM, CONFIG_VAL, OPER_BUS_SEG_CD   -- layer matters (CORE vs client)
FROM   <config table; via Global Config screen in Classic>
WHERE  CONFIG_NM IN ('AUTO_POST_OFR','INCLUDE_ZERO_TRANS_AMT','INCLUDE_ZERO_TRANS_AMT_BY_SYS_SRC',
                     'OFR_GRP_BY_GRS_AMT','JRNL_MMS_PROC_DEDUCT','COMMAND_TIMEOUT_SEC','TOLERANT_DEC');

-- G. Missing DB connection blocking DATAPUBLISH / COA sync (§11)
SELECT * FROM dbo.QARCH_CTRL_CONNECTION_INFO;   -- look for QLS / QLandDataHelper

-- H. The failing process step + error by Process Queue ID
--    Get PQID from the user, then read the batch message log for that PQID + step.
```

---

## 14. Expected-Behavior / User-Education FAQ

~70 Customer-Error + ~29 Training cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| **"Progressive rounding error"** during OFR / VL / PPN (e.g. transaction sequence N) | Decimal-tracking tolerance. Clean-up script for the immediate run; **workaround: use DO130 for funds-only transfers with "transfer all suspense" checked**; longer term tune a **`TOLERANT_DEC`** layer (e.g. `0.00000001`) | 22-00644851 (ADO #1318171), 24-00940369, 24-00961978, 23-00929043 |
| **"Revenue failing to run"** with rounding/decimal errors | Create a new **`TOLERANT_DEC`** layer set to a small value (e.g. `0.00000001`) | 24-00961978 |
| **PPN reversals/rebooks have decimals that don't match** | Often **bad tracking** — new owner tiers set up post-go-live as **CUR** accounting rule instead of **HIS**; fix the tier rule | 25-01033694 |
| **Escheat process doubling / unexpected final results** (PA unknown/foreign addresses) | Known defect (estimated vs actual doubled) — fixed; verify build | 22-00644853 (ADO #1321337) |
| **Escheat NAUPA export "no property records to write"** when Reporting Method = N&H | Registered-SQL `SQLID_Select_NAUPAHolderData` filters only `NPA`; **workaround: set EC010 Reporting Area to NPA** | 22-00669743 |
| **CW005 checks stay Outstanding (OS)** though cleared (CL) in QCFS BR005 after a reversal | Reversal in BR005 didn't flip the check back to OS; **workaround: script the CW005 status**; long-term = add CHKREGUPDT into the BR005 posting process | 25-01020731 (ADO #1726731) |
| **Huge MJE (90k+ rows) won't show in JE100 / can't unapprove** | Batch too large — **split the MJE into smaller batches** and re-process | 26-01063658 |
| **"Blank/mystery error" when running a batch** | Often transient — re-process the cleaned batch; if it recurs, capture the PQID log | 24-00977460, 22-00559071 |
| **QCFSEXPORT "Invalid account" / "mystery error"** | Almost always an account not in **GL013** or a timeout — see §4; several closed via a **KB** | 24-00984839, 24-00977775 |
| **"How do I…" account/journalization setup, audit questions** | Training — walk through **GL013 / JE010** and account groups (§10) | 25-01013760, 24-00976166 |

**Tell-tale it's user/expected:** a "progressive rounding error" on OFR/VL/PPN (tolerance + DO130 workaround); a QCFSEXPORT "invalid account" that's simply not in GL013; an escheat NAUPA/method edge case with a known EC010 workaround; a check stuck OS after a BR005 reversal; or an oversized MJE that just needs splitting. Verify the **GL013/JE010 config and the config layer the process reads** before treating it as a defect.

---

## 15. Key Code, Processes & Repos

### Processes / batch steps (run from QP043 / QP063)
| Process / step | Purpose | Notes |
|---|---|---|
| **JEPRECOMBO / JEPREPOST / JEPRESUM** | Prepare-for-post: build SL detail & summary | Deadlock/perf history (§5); writes `JTRN_SL_DETAIL`, `JRPT_*` |
| **JEPOST / TAXJEPOST** | Post SL + tax journal to GL | State in **`JTRN_JEPOST_PROC`**; SL post class `QPSJSLPosting`; tax-combo class `QPSTaxCombo` → `TONL_TAX_INPUT` (§5/§6) |
| **JESUMMARY** | Summarize SL → reporting tables | `numeric(13,2)` overflow defect (§5, ADO #1641942) |
| **JEPURGE** | Purge SL/journal history (per subledger) | Writes `JRPT_PRG`; same `numeric(13,2)` overflow (§5, 25-01054416) |
| **JEROLLDATE** | Roll accounting period | Moves `JTRN_GL_MTD_*` → `JTRN_GL_HIST_*` (§5, 22-00650815) |
| **QCFSEXPORT** (QP043) | Validate + export GL data → QCFS | `JEVALCDBLK` validation, `SSTAG_CORE_INTFC`, account check vs GL013 (§4) |
| **DATAPUBLISH** | Publish COA/accounts so GL013 ↔ JE010 align | Needs `QLandDataHelper` connection (§11) |
| **POSTWKFL** | OFR post workflow | `AUTO_POST_OFR` controls auto-post on JE100 (§8) |
| **TRRYLMMSRP / TRRYLMMSRF** | ONRR/MMS royalty journalization (PRELIM/FINAL) | Clean-up scripts for stuck staging (§6, 25-01033813) |

### Code locations (confirmed via ADO code search)
| Symbol | Repo / path | Cluster |
|---|---|---|
| `QPSTaxCombo` (.cpp/.h) | `Quorum.Upstream.QRA.ClassicBatch /QPDllRevenueAcctgBR/` | §6 tax combo |
| `QPSJSLPosting` (.cpp/.h) | `Quorum.Upstream.QRA.ClassicBatch /QPDllRevenueAcctgJE/` | §5 SL posting (`DONL_DO_HDR` delete, Patch 27) |
| Process-step metadata (`QARCH_CTRL_PROCESS_STEP.json`) | `<CLIENT>.Upstream.Metadata /STANDARD <ver>/` | step config / "Continue on error" flags |
| `QARCH_CTRL_CONNECTION_INFO` | client DB / `<CLIENT>.Upstream.*.Database` | §11 missing connections |

### Repos (see REPO_INVENTORY)
- **`Quorum.Upstream.QRA.ClassicBatch`** — C++ journal/tax/post batch (`QPDllRevenueAcctgJE`, `QPDllRevenueAcctgBR`). Core of §4–§6.
- **`Quorum.Upstream.QRA.Batch`** — managed batch.
- **`Quorum.Upstream.QRA.Web` / `.Application.Web` / `.Application.MiddleTier`** — JE screens (JE101/JE110/JE205 etc.); the `JtrnSlDetailWeb` codegen object lives here (§9).
- **`Quorum.Upstream.QRA.Database`** — QRA schema (`JTRN_*`, `JONL_*`, `JRPT_*`, `TONL_TAX_INPUT`).
- **`Quorum.Upstream.QRA.ClassicGui.Tax` / `Quorum.Upstream.QRA.Tax`** — tax journalization GUI/logic.
- **`Quorum.Upstream.QCFS.*`** — the financial system QCFSEXPORT targets (validation, BR005 bank recon, GL).
- **`Quorum.Upstream.QRA.ReleaseNotes`** — confirm fix/patch availability and target build.
- **`<CLIENT>.Upstream.QRA.*` / `<CLIENT>.Upstream.Metadata` / `<CLIENT>.Upstream.QCFS.Database`** — client overrides (MEW, SPR, RLY, EQT, PNR, GLE, CNX, SEP, PER, ENC, TG/SND…). **Check the client layer first** — most config (AUTO_POST_OFR, JRNL_MMS_PROC_DEDUCT, COMMAND_TIMEOUT_SEC, INCLUDE_ZERO_TRANS_AMT), schema-width fixes, and connection rows are client-specific.

---

## 16. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A **calculation/journalization is provably wrong** on correct inputs: OFRs-to-internal-owners account journalization (22-00547108/#210222), JESUMMARY arithmetic overflow (24-00938880/#1641942), JE101/JE110 filter returns wrong rows (24-00986688/#1695727, 25-01048055), Web-vs-Classic SL mismatch (24-00965638), JE Group Type 9 forcing Contract on JE206 (24-00947974), `JTRN_JEPOST_PROC` check-constraints (#1641385), JE Post `DONL_DO_HDR` delete error (22-00651672/Patch 27).
- A **batch step crashes from a code/proc bug**: JEPRESUM deadlock (22-00512536), JEROLLDATE transfer abort (22-00650815), QCFSEXPORT partial-post 20K-header limit (22-00560521).
- Provide: **PQID + failing step + exact error text**, client + company/business segment + accounting month + RRID, and a repro. Confirm fix availability in `Quorum.Upstream.QRA.ReleaseNotes` and the WI's target build/patch.

**Handle as Configuration (Cloud Ops / Services) when:**
- **GL013 / JE010** account or journalization-level setup (26-01101592, 26-01084517, 25-01013760), account-group/keyword setup for MJE approval & write-offs.
- **Journal config** in the right layer: `AUTO_POST_OFR='1'` (25-01051314), `INCLUDE_ZERO_TRANS_AMT(_BY_SYS_SRC)` (26-01096204, 25-01041182), `JRNL_MMS_PROC_DEDUCT=FALSE` (25-01047071), `COMMAND_TIMEOUT_SEC` raise (25-01007761), `TOLERANT_DEC` layer (24-00961978).
- **Client-clone schema drift**: widen summary/purge columns `numeric(13,2)→(17,2)` to match `JTRN_SL_DETAIL.TRANS_AMT` (25-01054416).
- **Missing DB connection** in `QARCH_CTRL_CONNECTION_INFO` (QLS/QLandDataHelper) during upgrade/cutover (25-01059279, 24-00973140); **QPEC restart** to pick up config / clear a hang (25-01022599).

**Data-fix scripts (verify-SELECT in a transaction first):**
- Delete erroneous duplicate-key rows in `TONL_TAX_INPUT` and re-run TAXJEPOST (22-00823344, 24-00960891, 25-01040037).
- Realign MJE status in `JONL_MANL_JE_HDR` (22-00515826, 22-00577371); break RRID cross-references blocking a period roll (22-00518226); reset `JTRN_JEPOST_PROC` status for a prevent-posting RRID (25-01034938); clear stuck ONRR royalty staging/proc tables then re-run PRELIM→FINAL (25-01033813).

**Do NOT blind re-run a stuck QCFSEXPORT** (duplicate-entry risk) — escalate for a clean-up/unblock script and capture QPEC + MiddleTier logs (25-01001856).

**Handle as Training / Expected behavior (no fix):** see §14 — progressive rounding (DO130 workaround), escheat NAUPA/EC010 method edge cases, CW005-after-BR005-reversal, oversized MJEs needing a split, and QCFSEXPORT "invalid account" that's simply missing from GL013.

---

*Skill created: 2026-06-14.*
*Based on ~561 closed QRA Journal SF cases — ~76 actionable (Software Defect + Application Configuration + ChangeConfig) mined for fix recipes, plus a sample of Customer-Error/Training cases for the FAQ. ADO work items #1641942, #1434672, #1641385, #1752013/#1749635, #1695727, #1537863, #1711420/#1711544, #210222, #1318171, #1321337, #1726731; Upstream Patch 27. Code: `QPSTaxCombo` & `QPSJSLPosting` in Quorum.Upstream.QRA.ClassicBatch.*
*Companion: REPO_INVENTORY, CONFIG_REFERENCE, SF knowledge articles, kb.py vector KB.*
