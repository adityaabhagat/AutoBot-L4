# SKILL: QDO Transfers / Suspend-Release / Query-Screens Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** My Quorum Division Order (QDO) — upstream oil-and-gas owner-relations / division-order accounting (part of the myQuorum / On Demand upstream suite)
**Scope:** The ownership-transfer & suspense pipeline — **Transfers** (DOI / owner / workspace / maintenance-group transfers, carve-outs, recoupment, bearer-group changes, MEG/exemption movement), **Suspend/Release** (Owner Funds Release / OFR, External Funds Release / EFR, pay-code changes, escheat/NAUPA), and **Query Screens** (owner / DOI search, saved searches, DOR/CI suspense reports, associated-lease lookup). This skill *consumes* a built DOI (decimal interest, bearer groups, MEGs) and *moves/suspends/releases* ownership and funds across it; when a downstream revenue number is wrong, the transfer is usually the cause — fix the transfer/funds-release first.
**Companion skills (assumed, mirror the TIPS layout):** DOI build / decimal-interest / revenue-deck setup → master-data skill; revenue distribution / PPN / RRV mechanics → revenue skill; batch-job / process-queue mechanics (PQID, steps, restart) → batch skill; SAP/GL integration → integration skill. REPO_REFERENCE.md for repo paths.

> **Evidence base:** 463 closed QDO Transfers / Suspend-Release / Query-Screens cases (Transfers 318, Suspend/Release 104, Query Screens 41). Root-cause split: (blank) 120, **Software Defect 83**, Customer Error 60, Hardware/Software Change 31, Customer Cancelled 30, Training 27, Hardware/Software Env Change 16, **Application Configuration 14**, Performance 8, **ChangeConfig 2**, others. This skill mines the **99 actionable** cases (Software Defect 83 + Application Configuration 14 + ChangeConfig 2) for fix recipes, plus ~35 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case and/or ADO work item observed during mining.
> **Tables/screens caveat:** QDO runs on **SQL Server** (`*_QRA` databases, e.g. `EQC_DEV17UPS_QRA`); tables are `DONL_*` (live) and `DONL_DVD_*` (workspace/"DVD" staging), with `RSTG_*` release-staging and `DSTG_*` SAP-staging tables. Names below are from case repro text and ADO; **verify against the client DB before scripting**, always run a verify-SELECT in a transaction first.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — DO129 funds-release stuck in status 3-Approved (double approval)](#4-cluster-a)
5. [Cluster B — OFR / EFR process fails on bad / unprocessed staging records](#5-cluster-b)
6. [Cluster C — Workspace / COPY_DVD approval failures (FK / interest-seq)](#6-cluster-c)
7. [Cluster D — MEG / market-exemption missing after transfer](#7-cluster-d)
8. [Cluster E — Funds not moving / wrong amount on transfer & pay-code change](#8-cluster-e)
9. [Cluster F — Bearer-group / carve-out / PPN-not-created on transfer](#9-cluster-f)
10. [Cluster G — Marketing-Group / DOI-change "stuck Pending" mass scripts](#10-cluster-g)
11. [Cluster H — Bad-data blocks transfer (flags, leading zeros, decimals, trailing space)](#11-cluster-h)
12. [Cluster I — Query Screens (owner/DOI search, saved searches, reports, leases)](#12-cluster-i)
13. [Cluster J — Performance (Preview DOI / DOINTXWRK / maintenance)](#13-cluster-j)
14. [Known ADO Items](#14-known-ado-items)
15. [Diagnostic SQL](#15-diagnostic-sql)
16. [Expected-Behavior / User-Education FAQ](#16-expected-behavior--user-education-faq)
17. [Key Screens, Processes & Repos](#17-key-screens-processes--repos)
18. [Escalation Guidance](#18-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| Wells / transfers **stuck in DO129 at "3-Approved"** (should be "6-Completed"); can't act on the owners | **Funds Release approved twice within seconds** (double-click); 1st completes, 2nd cancels, status sticks at 3 | §4 — script `UPDATE DONL_INT_FUNDS_XFER_HDR SET XFER_STAT_CD='6' WHERE XFER_STAT_CD='3' AND TRANS_SEQ_NO=...`; fixed in Web/future versions (ADO #1668846) |
| OFR / EFR errors: *"Division Order/Owner has pending Suspense Release Transactions that have not been processed"* | Leftover unprocessed/rejected rows in `RSTG_OWNR_FUND_RLS` (+ `_ERR`); or a transfer with bad data (trailing space in Owner/BA) | §5 — rerun OFR with **"Process Rejected Records"** flag, or script `PROC_FL='Y'` for the bad TRANS_SEQ_NO; check `FOOTING_TOLERANCE` global config |
| Workspace/MG approval (`COPY_DVD` / `COPY_DVD_W`) fails on FK or interest-seq | Workspace bearer group not yet in live `DONL_BEARER_GRP_HDR`; or from-owner interest seq mismatch | §6 — (ADO #1387066) data fix `DONL_DVD_INT_FUNDS_XFER_DTL`; for FK_DONL_DVD_MKT_EXMPT truncate unused tables (23-00933603) |
| Owner has a MEG assigned but **DO007 shows no exemptions** → being charged deducts they shouldn't | MEG/exemption not created in `DONL_MKT_EXMPT` on the transfer/setup (MEG-remediation lineage) | §7 — script to backfill `DONL_MKT_EXMPT`; long-term fixed by MEG remediation (ADO #1409730 family) |
| Funds don't move / move the wrong amount after a transfer or pay-code change | MG transfer not carrying all selected funds (defect); or `SL_DETAIL_NO` int32 overflow → 0 | §8 — (ADO #1713151 SL_DETAIL_NO=0; 25-01004614 int32→int64); confirm fix build |
| Bearer-group change / carve-out doesn't generate PPN; "bearer percent sum ≠ 1" on approve | PPN-on-BG-change logic / GMI calc defect | §9 — (ADO #1647374, #1601966, #1554580) |
| "Run our script to set MG status Pending→Complete and DOI change flag Y→N" | Routine **mass DOI/marketing-group cleanup**, recurring per client | §10 — recurring operational data script (22-00523776/788/527011) |
| Transfer red-bars with a data error (Lawsuit Flag, invalid NRI, can't add owner) | **Bad source data** or a config limit (decimal places) blocking the transfer | §11 — fix the offending row / config; often a script |
| Owner/DOI search returns "NO DATA FOUND" / wrong sub / foreign owner missing | Search/picklist defect, or BA country-state not in `GCDE_CD`; saved searches from terminated user | §12 — config/data; saved-search `QARCH_FILTER_SAVE_NET` |
| Preview DOI / DOINTXWRK / maintenance taking hours | Process not scoped to affected DOIs / heavy funds-detail query | §13 — perf; scope to touched DOIs (ADO #170514) |

---

## 2. Pipeline & Concepts

```
[DOI built: decimal interest, bearer groups, MEGs, pay codes]
      │
      ▼  DOI / OWNER / WORKSPACE TRANSFER  (DO020 workspace, or DOI/owner maintenance group → Preview DOI → Approve)
[COPY_DVD / COPY_DVD_W  copies DONL_DVD_* workspace data → live DONL_* ; generates PPNs/reversals]
      │
      ├──► SUSPEND / RELEASE  (DO130 build funds release → DO129 approve → OFR batch CWOWFNDRLS/QP043 → RSTG_OWNR_FUND_RLS → subledger)
      ├──► SAP / GL integration (DSTG_SAP_* staging, VW_QSYNC_* views)
      └──► QUERY / REPORTS  (owner/DOI search, DO005/DO006/DO007, DOR/CI suspense reports, NAUPA/escheat QP043)
```

### Key terms (Quorum / QDO vocabulary)
- **DOI** = Division Order Interest — an owner's decimal-interest record on a property/tier (`DONL_DO_DETAIL`). A **transfer** moves interest from one owner (BA) to another.
- **Maintenance Group (MG) / Workspace Group (WS)** = the container in which DOI changes (transfers, modifies, pay-code changes, bearer-group maintenance) are staged, previewed, and approved. Web uses **Workspace**; classic uses **Maintenance**. Screens: DO020 (create WS), DO025 (verify/submit/approve WS), Maintenance Group screen (Web).
- **Preview DOI / Approve** → triggers **`COPY_DVD`** (maintenance) or **`COPY_DVD_W`** (workspace) — the batch step that copies staged `DONL_DVD_*` rows into live `DONL_*` tables and generates PPNs/reversals. Most "approval failed" defects live here.
- **BA** = Business Associate (owner number). **NRI** = Net Revenue Interest (decimal, up to 10 places). **WI/NWI/RI/ORI** = working / non-working / royalty / overriding-royalty interest types.
- **Bearer Group (BG)** = the group of working-interest owners that "bear" a non-working owner's costs; `DONL_BEARER_GRP_HDR`. A **carve-out** (WI→NWI) auto-creates a new BG. Bearer percents on a market group must sum to 1.
- **MEG** = Market Exemption Group — a group of marketing/deduct exemptions assigned to an owner so they aren't charged certain deducts. Individual exemptions historically lived in **`DONL_MKT_EXMPT`** (live) / `DONL_DVD_MKT_EXMPT` (workspace); a **MEG-remediation** enhancement (2021.10, ADO #1409730/#1365149) moved lookups to `DONL_MKT_EXMP_GRP_DETAIL` and stopped writing individual MEs. Screens DO006/DO007 display them.
- **OFR** = Owner Funds Release; **EFR** = External Funds Release. Built on **DO130** (select funds), approved on **DO129**, processed by the **`CWOWFNDRLS`** batch (a.k.a. **QP043 → DOFUNDRLS**). Staged in **`RSTG_OWNR_FUND_RLS`** (+ `_ERR`). Deleting a release on DO129 runs **DOFUNDRVS / `USPD_FUNDS_RVS`** which removes the `RSTG_OWNR_FUND_RLS` rows (where `PROC_FL <> 'N'`).
- **`XFER_STAT_CD`** = funds-transfer status on `DONL_INT_FUNDS_XFER_HDR`: **3 = Approved**, **6 = Completed** (the DO129 stuck-status fix flips 3→6); SXI = cancelled duplicate; SPE/SXE = error.
- **PPN / RRV** = Prior-Period Notification / Reversal generated when a transfer/BG-change affects already-processed (revenue-booked) months. Created inside `COPY_DVD`.
- **Recoup / Recoupment flag** = on a DOI transfer, recoup of suspended funds; cannot be applied to a plain funds release (see §16).
- **DOINTXWRK / QDOInterestTransfer** = the interest-transfer batch process (PQID-tracked). **DVDVERIFY** = workspace verification step.
- **QLS** = Quorum Land System; associated leases tie to a DOI via the **QLS → DO Lease Interface** job.

---

## 3. Decision Tree

```
QDO Transfer / Suspend-Release / Query-Screens case
│
├─ Funds-release / OFR / EFR problem?
│   ├─ Stuck in DO129 "3-Approved" (won't go to 6/Completed)        → §4  (double-approval; script XFER_STAT_CD 3→6; Web fixes it)
│   ├─ "pending Suspense Release Transactions not processed" / OFR errors → §5  (RSTG_OWNR_FUND_RLS leftover/bad rows; rerun w/ Process Rejected, or PROC_FL='Y'; FOOTING_TOLERANCE)
│   ├─ Funds don't move / wrong $ after pay-code change            → §8  (SL_DETAIL_NO=0 / int32 overflow; MG not carrying all funds)
│   └─ Escheat/NAUPA QP043 errors                                  → §5/§11 (INCORPORATION_STATE_CODE config; report regen)
│
├─ Transfer / workspace / MG approval failed (COPY_DVD / COPY_DVD_W)?  → GET PQID + EXACT SQL/COM ERROR + table name
│   ├─ FK violation on DONL_BEARER_GRP_HDR / interest-seq           → §6  (workspace BG not in live; from-owner seq; ADO #1387066)
│   ├─ FK_DONL_DVD_MKT_EXMPT__DONL_DVD_DO_DETAIL on Preview         → §6/§7 (truncate unused DVD_MKT_EXMPT tables, 23-00933603)
│   ├─ "bearer percent sum is not equal to 1"                       → §9  (GMI calc on partial NWI redistribution; ADO #1554580)
│   ├─ "HF.XFER_EFF_DT_FROM could not be bound" / reversal query    → §8  (Get-DOs-for-reversals query defect; 23-00930981 / 25-01007452)
│   └─ Workspace Reason validation error                            → §6  (new reason codes; ADO #1559879, 22-00831119)
│
├─ Output wrong after a (successful) transfer?
│   ├─ Owner has MEG but DO007 shows no exemptions / charged deducts → §7  (DONL_MKT_EXMPT not populated; MEG-remediation family)
│   ├─ Bearer-group change / carve-out didn't create PPN            → §9  (ADO #1647374 / #1601966)
│   └─ Interest didn't combine on WI↔NWI                            → §9  (combine-flag / carve-out)
│
├─ "Run our cleanup script" (MG Pending→Complete, DOI change flag Y→N) → §10 (recurring mass script — verify scope, transaction)
│
├─ Transfer red-bars on bad data (Lawsuit Flag, invalid NRI, decimals, can't add owner) → §11
│
├─ Query/search/report screen wrong?                                → §12 (owner/DOI search, saved searches, DOR/CI, QLS leases)
│
└─ "Taking hours" / timeouts on Preview / DOINTXWRK / maintenance   → §13 (perf — scope to affected DOIs)
```

---

## 4. Cluster A — DO129 funds-release stuck in status 3-Approved (double approval)

**The single most recurring actionable Suspend/Release signature.** Wells/transfers sit in DO129 at **"3 - Approved"** instead of advancing to **"6 - Completed"**, which blocks any further action on the tied owners.

**Root cause (confirmed, ADO #1668846 "EQT — Users can double approve funds release", 24-00950107):** a user (or a slow UI) **approves the same Funds Release transaction twice within seconds**. The first process runs and moves the funds correctly; the second is detected as a duplicate and cancelled — but the header status is left at **3** instead of **6**. The funds move only once (no double payment), the record is just stuck.

**Immediate workaround / fix recipe:**
1. Get the **TRANS_SEQ_NO** (and PQID) of the stuck transfer from DO129.
2. Run the status-flip script (always inside a transaction, verify-SELECT first):
   ```sql
   UPDATE DONL_INT_FUNDS_XFER_HDR
   SET    XFER_STAT_CD = '6'
   WHERE  XFER_STAT_CD = '3' AND TRANS_SEQ_NO IN ('<seq>');
   ```
   Examples run in PRD: 25-01041288 (seq 115303), 25-01006556 (seq 76470 / 100960), 25-01049272 (EQC). Script-review WIs: **ADO #1655987 / #1661187 (24-00950107), #1715947 (EQC QRA)**.
3. **Long-term:** "Does not happen in web/future versions" (25-01006556). The classic UI hardening (gray-out the Approve button immediately) was deployed but did not fully hold in Prod for EQT classic — the durable fix is the **upgrade to Web DO** (EQT's next upgrade per 25-01041288). Confirm the client's target build.

> **Related older lineage (GLE, 23-00888898):** funds releases that **can't be approved or deleted** because an existing release has all lines rejected-but-marked-not-processed while the header shows complete (**ADO #1584263 / #1585450 / #1587434 / #1589104**). Deleting from DO129 runs `USPD_FUNDS_RVS` to clear `RSTG_OWNR_FUND_RLS`; if the delete itself fails, that is the script-approval path. A separate perf fix in #1584263 was for releases with **>10,000 detail lines** failing to delete on DO129.

---

## 5. Cluster B — OFR / EFR process fails on bad / unprocessed staging records

OFR/EFR (DO130 build → DO129 approve → `CWOWFNDRLS`/QP043) fails with *"THIS DIVISION ORDER/OWNER HAS PENDING SUSPENSE RELEASE TRANSACTIONS THAT HAVE NOT BEEN PROCESSED"* (message title `FUNDS_RLS`), or stops on error when **"Process Rejected Records"** is checked. The blocker is leftover rows in **`RSTG_OWNR_FUND_RLS`** with `PROC_FL='N'` (+ rows in `RSTG_OWNR_FUND_RLS_ERR`).

| Sub-pattern | Root cause | Fix | Case |
|---|---|---|---|
| Unprocessed rows + `RSTG_OWNR_FUND_RLS_ERR` says *"Plugged TRANS_AMT exceeds tolerance"* | Footing tolerance too tight | **Create an env-specific `FOOTING_TOLERANCE` record in Global Config** (set to 1); **reprocess `CWOWFNDRLS` with "Process Rejected Records Flag" = Y** | 22-00560533 |
| OFR stops on error when "Process Rejected Records" checked; bad data = **trailing space in Owner No** (`"305726 "`) in the staging table | Extra space written to `RSTG_OWNR_FUND_RLS` | Script `UPDATE RSTG_OWNR_FUND_RLS SET PROC_FL='Y' WHERE TRANS_SEQ_NO IN ('<seq>')` to mark bad records processed; same approach as 23-00914643 | 25-01005386, 23-00918864, 25-01036728 (FROM_OWNER_BA vs TO_OWNER_BA mismatch) |
| Funds not picked up in transfer despite "All Suspense" flag | Previously-not-processed rows in `RSTG_OWNR_FUND_RLS` | **Rerun OFR with "process rejected records" checked** for those seq numbers | 25-01027352 |
| OFR completed with **Warnings**, can't post — *"No Suspense Release data… for OPER_BUS_SEG_CD"* | DO130 transactions **not approved before** running OFR from QP043 | Approve DO130 transactions, rerun OFR (Customer Error) | 25-01026528 |
| **QP Escheat / NAUPA** process fails: *"global configuration specifying state of incorporation is --"* | Missing `INCORPORATION_STATE_CODE` global config for the client | Set `INCORPORATION_STATE_CODE` (e.g. "42" = Texas) | 24-00973284 |
| NAUPA report failed to generate (worked in prior UAT cycle) | Report/config | resolution pattern unclear from mined cases (re-gen / env config) | 25-01052395 |

**Fix recipe:** (1) query `RSTG_OWNR_FUND_RLS` and `_ERR` for the owner/transfer; (2) if it's a tolerance footing error, raise `FOOTING_TOLERANCE` in Global Config and reprocess with **Process Rejected Records = Y**; (3) if it's genuinely bad data (trailing space, BA mismatch) that can't be cleaned in the app, script `PROC_FL='Y'` on the offending `TRANS_SEQ_NO` to skip it, then reprocess. The recurring root cause is a **trailing space in the Owner/BA number**; the newer build no longer creates it but you still clean up legacy rows with the script.

---

## 6. Cluster C — Workspace / COPY_DVD approval failures (FK / interest-seq)

`COPY_DVD` / `COPY_DVD_W` (the Preview-DOI / Approve step that copies workspace `DONL_DVD_*` into live `DONL_*`) crashes on a SQL Server FK or constraint error. **Get the exact table name in the error.**

| Signature | Root cause | Fix | Case / ADO |
|---|---|---|---|
| `COPY_DVD_W` fails; FK `FK_DONL_INT_FUNDS_XFER_DTL__DONL_BEARER_GRP_HDR` (or insert into `DONL_BEARER_GRP_HDR`) | A **new bearer group created inside the workspace** doesn't exist in live tables yet, but copy inserts the funds-xfer detail first → FK violation. Classic carve-out "complex 3" path. | Code fix to the copy order (ADO #1387066). Data unblock: align/insert the BG or correct the from-owner interest seq in `DONL_DVD_INT_FUNDS_XFER_DTL` | 23-00930178, **ADO #1387066** |
| Preview DOI fails: `DELETE … conflicted with FK_DONL_DVD_MKT_EXMPT__DONL_DVD_DO_DETAIL` (NativeError 547) on a 100% backdated transfer w/ funds | Rows in **`DONL_DVD_MKT_EXMPT`** that this QDO version no longer uses (MEG remediation) | **Script to truncate the 2 unused DVD market-exemption tables** | 23-00933603 |
| `WRKSPCSTEP` step error executing `USPD_DO_DVD_WORKSPACE_CREATTION` (`QPCEProcessStepDBProcedureLauncher.cpp`) | Bad workspace data | **Data script** delivered & run | 22-00669883 |
| Workspace transfer **validation error using a new Workspace Reason** code | New reason codes not handled | **Code fix, ADO #1559879** | 22-00831119 |
| Workspace stuck "In workspace ###" on DO020 after group transfer; can't re-query on DO025 | Status not cleared on completed group | resolution pattern unclear from mined cases — escalate as defect | 22-00664641 |
| RI→RI / RI→WI workspace transfer red-bar error | A DO-Web workspace-transfer enhancement (**ADO 1409730/1409730-era change**) caused it | Code change (22-00638065 cites change 1409730) | 22-00638065, 22-00647316 |
| `DSTG_DO_GWI` unique-key violation on DOIINTXWRK (`AK_DSTG_DO_GWI`) | Missing **Patch 7** | Apply Patch 7 | 23-00933147 |
| MEG primary-key error after env refresh (post-refresh script didn't reset sequence) | `QARCH_TRAN_SEQ.LAST_NO` for `TRANS_GRP_SEQ_NO` not reset to max across all xfer/maint/hist tables | Run the seq-reset script (see §15) | 25-00997687 |

**Fix recipe:** read the **exact SQL/COM error + table**. Bearer-group FK on copy = workspace BG not yet in live (ADO #1387066) — align the BG or correct interest seq. `DONL_DVD_MKT_EXMPT` FK on a backdated 100% transfer = truncate the unused DVD-ME tables (23-00933603). Stored-proc/`WRKSPCSTEP` errors are usually a scoped data script. After any env refresh, suspect the **`QARCH_TRAN_SEQ` sequence not reset** (25-00997687).

---

## 7. Cluster D — MEG / market-exemption missing after transfer

A high-recurrence, multi-client defect family: an owner is **assigned a MEG but DO006/DO007 shows no exemptions** in the bottom grid, so the owner is wrongly charged deducts. Almost always triggered by a **transfer or new setup** that failed to write the individual exemptions to **`DONL_MKT_EXMPT`**.

**History / root cause:** historically every individual market exemption was written to `DONL_MKT_EXMPT` (live) / `DONL_DVD_MKT_EXMPT` (workspace). A **MEG-remediation enhancement (2021.10, ADO #1409730 "Reconsider Marketing Exemptions" + #1365149)** changed the design to **look exemptions up from `DONL_MKT_EXMP_GRP_DETAIL`** and stop creating individual MEs on transfer. During and after that migration, transfers either (a) failed to create the expected `DONL_MKT_EXMPT` rows (pre-remediation clients) or (b) kept wrongly inserting into the deprecated `DONL_DVD_MKT_EXMPT` (mid-migration clients).

| Symptom | Fix | Case / ADO |
|---|---|---|
| MEG assigned, no exemptions in `DONL_MKT_EXMPT` → DO007 empty → owner charged deducts | **Script to backfill the missing `DONL_MKT_EXMPT` rows**; long-term resolved by MEG remediation | 22-00527089, 22-00682725, 22-00830748, **ADO #630572 (MAC), #1406357 (AST)** |
| Transfers still **inserting into deprecated `DONL_DVD_MKT_EXMPT`** post-remediation → Preview/approval FK fails | MEG clean-up script + remediation code | **ADO #1592105 (EQC), #1594122, #1462054, #1446715, #1553027** |
| `DOEXPMAINT` fails on a MEG change | Exemption-maintenance defect | 22-00688787 (resolution unclear from mined cases — escalate) |
| Exemption maintenance fails on **converted wells** with `DONL_DVD_OWNR_LSE` SQL error | Owner-lease data on converted wells | research/defect | 23-00904958 |
| MEG details not interfacing to SAP after MG approval (`DONL_MKT_EXMPT` / `DSTG_SAP_DONL_MKT_EXMPT` / `VW_QSYNC_REV_MKTG_EXMPT` missing data) | Remediation moved MEs to `DONL_MKT_EXMP_GRP_DETAIL`; integration view not updated | Core DB change | **ADO #1540964 (RSC)** |
| MEG missing only for production months **before** the transfer effective date (PPN tracking) | PPN/MEG-date handling | defect | 23-00926323, **ADO #1610057 (GEC)** |

**Fix recipe:** confirm the owner has a MEG on DO006 but blank exemptions on **DO007**. Query `DONL_MKT_EXMPT` for the BA/property/eff-date slice (see §15-D). If rows are missing, **script the backfill**; if rows are wrongly in `DONL_DVD_MKT_EXMPT`, run the MEG clean-up. Check the client's build against the **MEG-remediation lineage (#1409730 / #1592105 / #1594122)** — under-deployed remediation is the most common reason this recurs.

---

## 8. Cluster E — Funds not moving / wrong amount on transfer & pay-code change

Funds appear correct mid-transaction but come out wrong (or zero) after preview/approve. Two confirmed defects:

| Symptom | Root cause | Fix | Case / ADO |
|---|---|---|---|
| Pay-code change releases only part of the funds; balances don't move; MG funds tab shows **blank funds records** | On preview, staged release row written to **`RSTG_DVD_OWNR_FUND_RLS` with `SL_DETAIL_NO = 0`** (the subledger detail row's unique id) → discrepancies on approval. Happens when real `SL_DETAIL_NO` exceeds the int32 limit (~2.1B / seen >2.5M) | **`SL_DETAIL_NO` widened from int32 to int64** to match the DB column | 25-01004614, **ADO #1713151 (ECA)** |
| DO130s pull different totals each time; preview throws the amounts off; can't edit, must recreate | MG transfer not including **all funds selected on the DOI transfer** | "Maintenance group transfers will now correctly transfer all Funds selected on the DOI transfer" (code fix) | 24-00973202 |
| Owner funds transfer "looks ok" but **doesn't show on subledger detail query**; preview PPN reversal date wrong | Preview-PPN-reversal date pulled wrong from query `m_GetDOsForReversalDVDNew`; web form not showing the transfer | Corrected the reversal date query; follow-on logged as 25-01012214 | 25-01007452, 25-01012214 |
| DO transfer error *"HF.XFER_EFF_DT_FROM could not be bound"* on the **"Get DO for Reversals"** SQL step | Bad alias / missing `HF` table in the reversals query | defect (same reversals-query family) | 23-00930981 |
| DO130 shows incorrect totals on first input when **multiple tiers** | Tier roll-up defect | defect | 22-00655448 |
| Funds-release requires Recoup flag going No-Pay↔Pay/Suspense, but recoup only allowed on DOI transfers (contradictory) | Validation defect | Resolved with **2022.04** upgrade | 22-00822175 |

**Fix recipe:** for partial/zero funds on a **pay-code change**, suspect **`SL_DETAIL_NO=0`** in `RSTG_DVD_OWNR_FUND_RLS` (ADO #1713151) — confirm the build has the int64 fix. For wrong totals on a **DOI transfer**, it's the "MG not carrying all funds" fix (24-00973202). For "transfer ok but not on subledger / reversal-date wrong," it's the **reversals query** family (25-01007452, 23-00930981).

---

## 9. Cluster F — Bearer-group / carve-out / PPN-not-created on transfer

Transfers that change interest type (WI↔NWI, carve-outs) manipulate **bearer groups** and must regenerate **PPNs** for revenue-booked months. Recurring defects:

| Symptom | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **PPN not created** for a bearer-group change | New check-in (COPY_DVD) logic compared **live-against-live** instead of workspace-vs-live for BG changes; `msc_sDO_PPN_RSN_CD_BG_CHG` PPNs not logged | Code fix; broader **PPN/RRV creation rewrite** | 23-00912601, **ADO #1647374 (ERF), #1596364, #1601966 (Feature, Proposed)** |
| Workspace transfer (partial NWI redistribution) errors *"bearer group bearer percent sum is not equal to 1 for the specified production date"* (`RADOGMIE16 QGMICalc.cpp`) | GMI/bearer-percent calc on partial NWI redistribution | Code fix | 22-00291136, **ADO #1554580 (MEW)** |
| WI→NWI carve-out (ORI on AP / 700-series tiers) **does not auto-create BG** | Carve-out BG auto-creation gap | defect | 22-00819387 |
| Bearer-group change generates transactions for only 2 of 3 selected lines | BG-change transaction-generation defect | defect | 22-00672535 |
| Interest **not combining** on WI→NWI / NWI→WI transfers | Combine-flag handling | defect | 22-00672530, 24-00962774, 22-00564752 (Hot Fix WI 128225) |
| "Combined Interest Flag not functioning correctly" | Combine-flag defect | defect | 22-00634683 |
| Cross-category transfer issues (RI↔WI etc.) | Cross-category transfer | **ADO #128225 (Bug, Closed — CNX/MRO/P2)** | 22-00638065 |
| `#DOI_SKIP_CHECKIN_` temp-table use in check-in logic | Check-in skip logic | **ADO #1748386 (OVV, 25-01019193)** | — |

**Fix recipe:** these are mostly **engine/code defects** in the carve-out / bearer-group / PPN path, not config. Verify bearer percents sum to 1 and the BG exists in live before blaming the engine; if the data is clean and PPNs still don't generate on a BG change, it's the PPN-logic family (**ADO #1647374 / #1601966**). Provide PQID + property/tier + transfer seq + the exact `QGMICalc`/`RADO*` error.

---

## 10. Cluster G — Marketing-Group / DOI-change "stuck Pending" mass scripts

A recurring **operational** pattern (mostly Mach/legacy clients): after mass DOI changes, marketing/maintenance groups sit in **Pending** and the **DOI change flag stays 'Y'**. The standard disposition is a **client-specific cleanup script**, re-run on request.

| Symptom | Fix | Case |
|---|---|---|
| "Run our script to update MG status **Pending → Complete** and **DOI change flag Y → N**" | Recurring mass-update data script (run by the same engineer each time) | 22-00523776, 22-00523788, 22-00527011, 22-00523691 (Mach) |
| Pending Maintenance Groups stuck for hours/days; tiers stuck "Submit for DOI Approval"; revert fails with *"DVD_DO historical rows copy failed in CopyDataFromDVD method"* | Approval/sync defect; revert path | defect/data (23-00932953 is the same `CopyDataFromDVD` signature) | 22-00672532, 22-00676476, 23-00932953 |
| JOA Maintenance processes but doesn't sync to SAP, MG stays Pending | Sync defect | defect | 22-00634708 |

**Fix recipe:** treat the Pending→Complete / change-flag-Y→N request as a **recurring scoped data script** — confirm the exact MG list and DOI scope, verify-SELECT, wrap in a transaction. The `CopyDataFromDVD`/"DVD_DO historical rows copy failed" message on revert is a known stuck-MG failure mode (22-00672532, 23-00932953) — capture PQID and escalate if the script can't clear it.

---

## 11. Cluster H — Bad-data blocks transfer (flags, leading zeros, decimals, trailing space)

Transfers red-bar because a **source data value is invalid** or hits a **configured limit**. Quick wins — fix the row or the config, don't escalate as an engine bug.

| Symptom | Root cause | Fix | Case |
|---|---|---|---|
| Transfer error traced to **Lawsuit Settlement Flag = '0'** (should be Y/N) | Bad flag value | **Script to correct the flag rows** | 22-00547177 |
| *"Invalid NRI to be transferred for Old Owner"* on a 12-decimal allocation | Decimal-places config allowed only **10**, customer entered 12 | Working as designed — config limit (Application Configuration) | 25-01043082 |
| **Leading-zeros NRI won't paste** into MG screen; only displays to 7 places (need 10) | Copy-paste / display formatting of NRI with ≥6 leading zeros | recurring; resolution pattern unclear from mined cases — escalate (orig 22-00828790, re-raised 26-01089745) | 26-01089745 |
| Can't create MG for an owner **not in the revenue deck** | Owner not on deck | **Script** (already fixed in future versions) | 24-00964767, 24-00964675 (no fix needed — works in CORE SUP) |
| Trailing space in Owner/BA blocks OFR | see §5 | §5 | 25-01005386 |
| Duplicate primary key on DOI / payout transfer | Seq/key collision | see §6 seq-reset; research | 22-00819876, 22-00572181 |
| Inquiry Date 1/1/1900 → *"Please specify a valid Inquiry Date"* when calculating a Market Group | Bad inquiry date | provide steps to undo / set valid date | 25-01051248 |

**Fix recipe:** read the red-bar error for the offending field. Flag/format issues (Lawsuit Flag '0', trailing space) = **scoped data script**. "Invalid NRI" / too-many-decimals = a **config limit** (decimal places), explain to the user (not a defect). Owner-not-on-deck = script or expected.

---

## 12. Cluster I — Query Screens (owner/DOI search, saved searches, reports, leases)

| Symptom | Root cause | Fix | Case |
|---|---|---|---|
| Owner/DOI Search widget returns **"NO DATA FOUND"**; Owner Search name doesn't populate | Search defect | resolution pattern unclear from mined cases — escalate as defect | 25-01020086 |
| Searching an owner with **multiple subs** returns the wrong sub's address | Sub-address query defect | defect | 22-00822032 |
| **Foreign owners** not retrievable via Owner Search | Picklist reads **`GCDE_CD`** for country/state; BA's country/state not in `GCDE_CD` | **Update the BA to match `GCDE_CD` config** (data/config) | 23-00910303 |
| Associated leases on DOI **not returning all leases** (not all QLS leases available) | QLS→DO lease interface not run / connections missing | **Add QLS connections, run the QLS→DO Lease Interface job** | 25-01044633 |
| Saved searches from a **terminated user** can't be removed for everyone (only hideable) | `GLOBL_IND` flag | `UPDATE QARCH_FILTER_SAVE_NET SET GLOBL_IND = 0 WHERE …` | 25-01042869 |
| **DOR018 / DOR016 / CI035** suspense report returns no data / wrong state | Suspense data not loaded; report pulls from loaded data | Load the revenue-suspense data; report then populates | 23-00909232, 22-00684302 |
| Field defaults not working in Web; Combine-Ownership checkbox; saved-search mgmt | Web form-default config | config | 25-01026980, 24-00972872 |
| `XFER_OWNR_LSE_IND` form-default in `QFRMDVDDOIQUICKTRANSFER` (DO034) not carrying to new transfer | Form-default-value defect | Resolved in client upgrade | 24-00974583 |
| Interactive Reports menu / frowny-face error | Report-menu config | config (disable/fix) | 23-00923636 |
| View Details of Associated Cost Centers bounces back to Dashboard | Navigation defect | defect | 23-00902872 |

**Fix recipe:** "no data" on search/report is usually **data not loaded or a config/picklist gap** (`GCDE_CD` for foreign owners, suspense data for DOR/CI, QLS interface for leases) — not always a code bug. Saved-search cleanup = `QARCH_FILTER_SAVE_NET.GLOBL_IND`. Genuine search/navigation defects (multiple-subs, NO DATA FOUND widget) escalate with the exact owner/screen.

---

## 13. Cluster J — Performance (Preview DOI / DOINTXWRK / maintenance)

| Symptom | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **DOINTXWRK** process taking multiple hours | The **"Funds Details" query** run throughout the process | perf improvement investigated | 25-01028170 |
| **Preview DOI** runs long on large MGs; `DVDVERIFY` runs on **all** checked-out DOIs, not just touched ones | Whole unit (~2,100 DOIs) checked out for a 1-DOI change; DVDVERIFY not scoped | Scope DVDVERIFY/preview to **affected DOIs only** (like COPY_DVD does) | 22-00809019, **ADO #170514 (MRO)** |
| MG005→MG006 screen navigation slow | Screen/query perf | improvement | 22-00512860 |
| System time delays / bulk-edit / import-to-owners / timeouts selecting funds | Volume / query perf | perf | 22-00823946, 23-00884583, 22-00676534 (`QDOInterestTransfer_000044` timing out) |
| QCLOUD slow at roll-out (response time, dashboards) | Environment/config | Application Configuration / env tuning | 25-01001965 |

**Fix recipe:** transfer/maintenance slowness is almost always **process not scoped to the affected DOIs** (the whole unit is checked out). The durable fix is engine scoping (ADO #170514). For DOINTXWRK, the Funds-Details query is the hot spot (25-01028170). QCLOUD roll-out slowness is env/config tuning, not a code defect.

---

## 14. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1668846** | Bug / **Closed** | EQT — Users can double approve funds release | §4 | 24-00950107 |
| **#1655987 / #1661187** | Bug / **Closed** | EQCU — Wells stuck DO129 status 3-Approved (script approval) | §4 | 24-00950107 |
| **#1715947** | Bug / **Closed** | EQC QRA — Wells stuck in DO129 (script review) | §4 | 25-01006556/25-01041288 |
| **#1584263** | Bug / **Closed** | GLE — OFR under DO129 "stuck" (also >10k-line delete perf) | §4 | 23-00888898 |
| **#1585450 / #1587434 / #1589104** | Bug / **Closed** | GLE — Unable to approve/delete Owner Funds Release | §4/§5 | 23-00888898 |
| **#1387066** | Bug / **Closed** | COPY_DVD_W fail — bearer-group FK violation (DO Tracking complex 3) | §6 | 23-00930178 |
| **#1559879** | Bug / **Closed** | NOGU — Workspace Transfer validation error (new Workspace Reason) | §6 | 22-00831119 |
| **#1554580** | Bug / **Closed** | MEW — bearer percent sum ≠ 1 on workspace transfer (QGMICalc) | §9 | 22-00291136 |
| **#1647374** | Bug / **Closed** | ERF — PPN not created for BG change | §9 | 23-00912601 |
| **#1596364** | Bug / **Closed** | CA PPN email / BG-change PPN logic (live-vs-live) | §9 | — |
| **#1601966** | Feature / **Proposed** | Upstream Stability — DO PPN / RRV Creation Rewrite | §9 | — |
| **#128225** | Bug / **Closed** | myQuorum DOI Maintenance — Cross Category Transfers Issues (CNX/MRO) | §9 | — |
| **#1748386** | Bug / **Closed** | ECA (OVV) — Evaluate/Remove use of #DOI_SKIP_CHECKIN_ | §6/§9 | 25-01019193 |
| **#1409730** | Feature / **Closed** | Reconsider Marketing Exemptions (MEG remediation, 2021.10) | §7 | — |
| **#1592105** | Bug / **Closed** | EQCU — Transfers involving MEGs still inserting into DONL_DVD_MKT_EXMPT | §7 | 22-00825548 |
| **#1594122 / #1462054 / #1446715 / #1553027 / #1365149** | Bug/Feature / **Closed** | MEG clean-up & remediation lineage | §7 | — |
| **#630572** | Bug / **Closed** | MAC — DOI Exemption Missing after Transfer or Set Up | §7 | (21-00104298 lineage) |
| **#1406357** | Bug / **Closed** | AST — Market exemptions not showing in DO007 after adding MEG | §7 | — |
| **#1540964** | Bug / **Closed** | RSC — MEG details not interfacing to SAP after MG approval | §7 | — |
| **#1610057** | Bug / **Closed** | GEC — MEG/PPN tracking for months before transfer eff date | §7 | 23-00926323 |
| **#1713151** | Bug / **Closed** | ECA — MG funds tab blank records / `SL_DETAIL_NO=0` on pay-code change | §8 | 25-01004614 |
| **#170514** | Bug / **Closed** | MRO — Preview DOI perf / DVDVERIFY runs on all DOIs | §13 | — |
| **#1369323 / #1387066** | Bug / **Closed** | DO Tracking complex test cases — reversal/FK on workspace approve | §6 | — |

> Many actionable cases were dispositioned **operationally** (scoped data script / config) with no single product WI: DO129 status flip 3→6 (§4), `RSTG_OWNR_FUND_RLS` `PROC_FL='Y'` clean-up (§5), `FOOTING_TOLERANCE` & `INCORPORATION_STATE_CODE` global config (§5), `DONL_MKT_EXMPT` backfill (§7), DVD-MKT-EXMPT truncate (23-00933603), MG Pending→Complete / DOI-flag Y→N mass script (§10), `QARCH_TRAN_SEQ` post-refresh reset (25-00997687), `QARCH_FILTER_SAVE_NET.GLOBL_IND` saved-search cleanup (§12). Confirm exact build/patch in the release notes when stating fix availability.

---

## 15. Diagnostic SQL

> **Caveat:** SQL Server, per-client `*_QRA` databases. **Verify table/column names against the client DB** and always run a verify-SELECT inside a transaction before any UPDATE/DELETE.

```sql
-- A. DO129 funds-release stuck at "3-Approved" (the §4 double-approval signature)
SELECT TRANS_SEQ_NO, XFER_STAT_CD, OPER_BUS_SEG_CD, UPDT_DT
FROM   DONL_INT_FUNDS_XFER_HDR
WHERE  XFER_STAT_CD = '3';                       -- 6 = completed; flip 3->6 for the stuck seq
-- Confirm a duplicate kickoff in the process queue (two PQIDs seconds apart):
SELECT PQID, STATUS_CD, START_DT FROM QARCH_QUEU_PROCESS WHERE PQID IN (<pqid1>,<pqid2>);

-- B. OFR/EFR leftover or bad staging rows (the §5 "pending unprocessed" blocker)
SELECT TRANS_SEQ_NO, PROC_FL, FROM_OWNER_BA, TO_OWNER_BA, SL_NO, SL_DETAIL_NO
FROM   RSTG_OWNR_FUND_RLS
WHERE  PROC_FL = 'N';                             -- red flag: trailing space in *_OWNER_BA
SELECT * FROM RSTG_OWNR_FUND_RLS_ERR WHERE TRANS_SEQ_NO IN ('<seq>');
-- Unblock (skip the bad transfer's records):
-- UPDATE RSTG_OWNR_FUND_RLS SET PROC_FL='Y' WHERE TRANS_SEQ_NO IN ('<seq>');  then reprocess CWOWFNDRLS w/ Process Rejected = Y

-- C. Pay-code-change funds discrepancy — SL_DETAIL_NO = 0 (the §8 int32-overflow signature, ADO #1713151)
SELECT TRANS_SEQ_NO, SL_NO, SL_DETAIL_NO, COUNT(*) ct
FROM   RSTG_DVD_OWNR_FUND_RLS
WHERE  SL_DETAIL_NO = 0
GROUP BY TRANS_SEQ_NO, SL_NO, SL_DETAIL_NO;       -- any rows = the blank-funds defect; confirm int64 build

-- D. MEG / market exemption missing after transfer (the §7 DO007-empty signature)
SELECT * FROM DONL_MKT_EXMPT
WHERE  PROP_NO = '<prop>' AND BA_NO IN (<ba>) AND EFF_DT_FROM = '<eff>';  -- empty => backfill needed
-- Should NOT have rows in the deprecated workspace table (post-remediation):
SELECT * FROM DONL_DVD_MKT_EXMPT WHERE PROP_NO = '<prop>' AND BA_NO IN (<ba>);  -- rows => run MEG cleanup (#1592105/#1594122)

-- E. Workspace bearer-group FK before approve (the §6 COPY_DVD_W FK signature, ADO #1387066)
SELECT * FROM DONL_DVD_BEARER_GRP_HDR WHERE BEARER_GRP_NO = '<bg>';   -- exists in DVD…
SELECT * FROM DONL_BEARER_GRP_HDR     WHERE BEARER_GRP_NO = '<bg>';   -- …but not yet in live => FK violation on copy

-- F. Post-env-refresh sequence reset (the 25-00997687 MEG primary-key error)
-- Resets QARCH_TRAN_SEQ.LAST_NO for TRANS_GRP_SEQ_NO to the max across all xfer/maint/hist (live + DVD) tables:
UPDATE QARCH_TRAN_SEQ
SET LAST_NO = (SELECT MAX(TRANS_GRP_SEQ_NO) FROM (
        SELECT MAX(TRANS_GRP_SEQ_NO) TRANS_GRP_SEQ_NO FROM DONL_INT_FUNDS_XFER_HDR
  UNION ALL SELECT MAX(TRANS_GRP_SEQ_NO) FROM DONL_DVD_INT_FUNDS_XFER_HDR
  UNION ALL SELECT MAX(TRANS_GRP_SEQ_NO) FROM DONL_OWNR_EXCPT_MAINT_HDR
  UNION ALL SELECT MAX(TRANS_GRP_SEQ_NO) FROM DONL_DVD_OWNR_EXCPT_MAINT_HDR
  UNION ALL SELECT MAX(TRANS_GRP_SEQ_NO) FROM DONL_PAY_CD_MAINT_HDR
  UNION ALL SELECT MAX(TRANS_GRP_SEQ_NO) FROM DONL_DVD_PAY_CD_MAINT_HDR
  UNION ALL SELECT MAX(TRANS_GRP_SEQ_NO) FROM DONL_DVD_DO_HIST
  UNION ALL SELECT MAX(TRANS_GRP_SEQ_NO) FROM DONL_DO_HIST) A)
WHERE SEQ_NM = 'TRANS_GRP_SEQ_NO';   -- wrap in BEGIN TRAN / verify / COMMIT

-- G. Saved-search cleanup for a terminated user (§12, 25-01042869)
-- UPDATE QARCH_FILTER_SAVE_NET SET GLOBL_IND = 0 WHERE <saved-search filter>;

-- H. Find the failing transfer/approval step by PQID (use the batch skill for the exact log table)
--    Get PQID from the user (e.g. 15066245), then read the batch message/log for that PQID + step (COPY_DVD / COPY_DVD_W / WRKSPCSTEP / DOINTXWRK).
```

---

## 16. Expected-Behavior / User-Education FAQ

~27 Training + ~60 Customer-Error cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| "Can I **undo** a transfer?" / "How do I reverse?" | Training — there is no one-click undo; reverse via the correct maintenance path (and the recoup-error "undo" steps) | 24-00937742, 25-01051248 |
| "Target owner **not in DOI Search** after the owner transfer completed" | Training — refresh/requery; the owner is there once the transfer completed (not a defect) | 25-01003845 |
| "Error in DOI maintenance when transferring to a **non-DOI owner**" | Training — the to-owner must be set up correctly first (not a defect) | 25-01003851 |
| "Wells stuck in DO129 3-Approved again" | Known double-approval issue (§4) — run the `XFER_STAT_CD 3→6` script; durable fix = Web/upgrade | 25-01049272, 25-01006556 |
| "OFR completed with Warnings, can't post — no suspense release data" | Customer Error — **DO130 transactions weren't approved before running OFR** in QP043; approve, then rerun | 25-01026528 |
| "Funds not picked up despite 'All Suspense' flag" | Leftover unprocessed `RSTG_OWNR_FUND_RLS` rows — **rerun OFR with 'Process Rejected Records'** (§5) | 25-01027352, 25-01013039 |
| "Recoup flag required going No-Pay↔Pay" but "recoup only on DOI transfers" | Confusing but expected pre-2022.04; recoup applies to DOI transfers, not plain funds releases (fixed 2022.04) | 22-00822175 |
| "Maintenance Groups keep being created as 'Maintenance Group #6'" on pay-status changes | Working-session resolved (user workflow), not a defect | 26-01096881 |
| "Foreign owner not in Owner Search" | Config — BA's country/state must exist in **`GCDE_CD`**; update the BA (§12) | 23-00910303 |
| "Invalid NRI to be transferred" on a 12-decimal interest | Config limit — decimals configured to **10 places**; not a defect (§11) | 25-01043082 |
| "How do I attach a document to a maintenance group?" / "remove saved searches?" | Training — DO Web attach steps; saved-search `GLOBL_IND` (§12) | 25-01043400, 25-01042869 |

**Tell-tale it's user/expected:** OFR run before DO130 approval; "missing" owner that's actually there after requery; recoup confusion pre-2022.04; foreign owner missing because the BA's country/state isn't in `GCDE_CD`; "invalid NRI" caused by the configured decimal-places limit; and any "how do I…" workflow question. Verify the **funds-release approval state, staging-table contents, and config limits** before treating it as a defect.

---

## 17. Key Screens, Processes & Repos

### Screens
| Screen | Purpose |
|---|---|
| **DO020 / DO025** | Workspace Group creation / verify-submit-approve |
| **Maintenance Group screen (Web)** | Create MG, add transactions, Preview DOI, Approve |
| **DO034** | DOI Quick Transfer (form `QFRMDVDDOIQUICKTRANSFER`, `XFER_OWNR_LSE_IND` default) |
| **DO005 / DO006 / DO007** | Owner/DOI query; MEG assignment; **market-exemption display** (the "DO007 empty" §7 symptom) |
| **DO100 / DO105** | DOI history / workspace approval columns |
| **DO129** | Funds-release approval (the **stuck 3-Approved** screen, §4) |
| **DO130** | Build Owner/External Funds Release (select funds, pay-code change) |
| **DOR016 / DOR018 / CI035** | Suspense reports (§12) |
| **QP043** | Process/Report Launcher — runs OFR (`CWOWFNDRLS`/DOFUNDRLS), Escheat, NAUPA |

### Processes / batch steps
| Process / step | Purpose | Notes |
|---|---|---|
| **COPY_DVD / COPY_DVD_W / COPY_DVD_S** | Copy workspace `DONL_DVD_*` → live `DONL_*`; generate PPNs/reversals on Approve | Most approval-failure defects (§6/§9); FK on `DONL_BEARER_GRP_HDR` (#1387066) |
| **DVDVERIFY** | Workspace verification on Preview | Runs on all checked-out DOIs — perf (§13, #170514) |
| **DOINTXWRK / QDOInterestTransfer** | Interest-transfer batch | Funds-Details query is the perf hot spot (25-01028170) |
| **CWOWFNDRLS / DOFUNDRLS** | OFR batch (release suspended funds) | Staging `RSTG_OWNR_FUND_RLS`; "Process Rejected Records" flag (§5) |
| **DOFUNDRVS / USPD_FUNDS_RVS** | Reverse/delete a funds release from DO129 | Clears `RSTG_OWNR_FUND_RLS` where `PROC_FL <> 'N'` |
| **USPD_DO_DVD_WORKSPACE_CREATTION** | Workspace creation stored proc (`WRKSPCSTEP`) | 22-00669883 |

### Key tables
- **Transfers:** `DONL_INT_FUNDS_XFER_HDR` / `_DTL` (live), `DONL_DVD_INT_FUNDS_XFER_HDR` / `_DTL` (workspace), `DONL_DO_DETAIL` / `DONL_DVD_DO_DETAIL`, `DONL_DO_HIST` / `DONL_DVD_DO_HIST`, `DONL_BEARER_GRP_HDR` / `DONL_DVD_BEARER_GRP_HDR`.
- **MEG/exemptions:** `DONL_MKT_EXMPT` (live), `DONL_DVD_MKT_EXMPT` (deprecated workspace), `DONL_MKT_EXMP_GRP_DETAIL` (post-remediation source).
- **Release staging:** `RSTG_OWNR_FUND_RLS` (+ `_ERR`), `RSTG_DVD_OWNR_FUND_RLS`.
- **SAP staging / views:** `DSTG_SAP_DONL_MKT_EXMPT`, `DSTG_DO_GWI`, `VW_QSYNC_REV_MKTG_EXMPT`.
- **Sequence/util:** `QARCH_TRAN_SEQ`, `QARCH_QUEU_PROCESS`, `QARCH_FILTER_SAVE_NET`, `GCDE_CD`.
- **Config:** Global Config keys `FOOTING_TOLERANCE`, `INCORPORATION_STATE_CODE`; decimal-places config.

### Code locations / symbols seen
- `QGMICalc.cpp` (`RADOGMIE16`) — GMI / bearer-percent calc (§9, #1554580).
- `QPCEProcessStepDBProcedureLauncher.cpp` — process-step launcher (WRKSPCSTEP, §6).
- `CopyDataFromDVD` method — DVD historical-rows copy on revert (§10, 22-00672532 / 23-00932953).
- `m_GetDOsForReversalDVDNew` query — Preview-PPN reversal date (§8, 25-01007452).
- PPN reason code `msc_sDO_PPN_RSN_CD_BG_CHG` — bearer-group-change PPN (§9).

### Repos (verify in REPO_REFERENCE.md)
QDO is the upstream Division Order module of the On Demand / myQuorum upstream suite. Source lives in the **QuorumSoftware** ADO project; per-client schemas are the `*_QRA` SQL Server DBs (e.g. `EQC_*`, `RSC_*`, `MRO_*`, `CORE_*UPS_QRA`). Classic batch is C++ (`QGMICalc`, `QADORecordset`, `QPCE*`); Web DO uses the workspace check-in path. **Always check the client schema/build first** — most fixes are version-gated (MEG remediation 2021.10, recoup 2022.04, DSTG_DO_GWI Patch 7, SL_DETAIL_NO int64) or client-specific scripts.

---

## 18. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- An **approval/transfer step crashes from code/proc**, not data: bearer-group FK on copy order (#1387066), GMI "bearer percent ≠ 1" (#1554580), PPN-not-created-on-BG-change (#1647374/#1601966), reversal-date query (`m_GetDOsForReversalDVDNew`, 25-01007452 / 23-00930981), workspace-reason validation (#1559879).
- A **funds amount is provably wrong** on correct inputs: pay-code-change `SL_DETAIL_NO=0` (int32 overflow, #1713151), MG not carrying all selected funds (24-00973202).
- Provide: **PQID + failing step (COPY_DVD/COPY_DVD_W/WRKSPCSTEP/DOINTXWRK/OFR) + exact SQL/COM error + table name**, client + property/tier + transfer/owner seq, and a repro. Confirm fix availability and the client's target build (most fixes are version-gated).

**Handle as Configuration / Cloud Ops:**
- **Global Config**: `FOOTING_TOLERANCE` (OFR footing, §5), `INCORPORATION_STATE_CODE` (escheat/NAUPA, §5), decimal-places limit (§11). Form defaults / Combine-Ownership / Web grid config (§12).
- **`GCDE_CD`** country/state for foreign-owner search; **QLS→DO Lease Interface** for associated leases (§12).
- **Build/version**: confirm MEG remediation (#1409730 family), recoup (2022.04), Patch 7 (DSTG_DO_GWI), SL_DETAIL_NO int64 are deployed for the client.

**Handle as scoped data script (verify-SELECT in a transaction first):**
- DO129 stuck status flip `XFER_STAT_CD 3→6` (§4); `RSTG_OWNR_FUND_RLS` `PROC_FL='Y'` clean-up (§5); `DONL_MKT_EXMPT` backfill / `DONL_DVD_MKT_EXMPT` cleanup (§7); DVD-MKT-EXMPT truncate (23-00933603); MG Pending→Complete / DOI-flag Y→N (§10); `QARCH_TRAN_SEQ` post-refresh reset (25-00997687); Lawsuit-Flag / bad-flag correction (§11); `QARCH_FILTER_SAVE_NET.GLOBL_IND` saved-search cleanup (§12).

**Handle as Training / Expected behavior (no fix):** see §16 — OFR run before DO130 approval, "missing" owner that's there on requery, recoup confusion pre-2022.04, foreign owner missing from `GCDE_CD`, "invalid NRI" from the decimal-places limit, "how do I attach / undo / remove saved searches." Verify funds-release state, staging tables, and config limits before treating as a defect.

---

*Skill created: 2026-06-14.*
*Based on: 463 closed QDO Transfers/Suspend-Release/Query-Screens SF cases — 99 actionable (Software Defect 83 + Application Configuration 14 + ChangeConfig 2) mined for fix recipes, plus ~35 Training/Customer-Error cases for the FAQ. ADO work items #1668846, #1655987/#1661187/#1715947, #1584263/#1585450/#1587434/#1589104, #1387066, #1559879, #1554580, #1647374/#1596364/#1601966, #128225, #1748386, #1409730/#1592105/#1594122/#630572/#1406357/#1540964/#1610057, #1713151, #170514, #1369323.*
