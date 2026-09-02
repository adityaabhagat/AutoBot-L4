# SKILL: QRA Check-Write / ACH / Void / OFR-Escheat — ADO Defect & Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Source:** Azure DevOps Financials bugs (Area Path `QuorumSoftware\Engineering\Financials`, WorkItemType=Bug, State Closed/Resolved)
**Product family:** Quorum Upstream Accounting — **QRA** (Revenue Accounting) check-write / disbursement path, with the actual payment mechanics living in **QCFS** (AP / check run / ACH) and the owner-side release in **QDO/QRA** (OFR from suspense). Repos are `Quorum.Upstream.QCFS.*` and `Quorum.Upstream.Shared.ClassicBatch`.

**Use When:** a case is about issuing or reversing money to owners/vendors — **check runs (AP061), printing/exporting checks, ACH file/email generation (AP150 / ACH_EML), voiding checks (single or bulk), 1099 amounts on voided checks, releasing Owner Funds from suspense (OFR), or QCFS↔QLS check-status sync**. Triage symptom → cluster → confirm the fix is in the client build (FIX-VERSION MATRIX, §11) → escalate with the exact artifacts (§10).

> **Evidence base & honesty note:** WIQL matched **92** Closed/Resolved Financials bugs on the title terms (`check write`, checkwrite, CW0, CWBANK, CWACH, ACH, "owner funds", OFR, escheat, "negative check", void). **Heads-up on the match set:** `ACH` is a substring of *att**ACH**ment*, so **40 of the 92 are attachment/document-upload UI bugs that have nothing to do with check-write** (a different functional area — do not treat them as payment defects). The terms `CW0 / CWBANK / CWACH / OFR / escheat / negative check` matched **zero** titles. So there is **no dedicated "escheat" or "CWBANK/CWACH" bug** in Financials — escheat surfaces only as the **OFR / release-from-suspense** workflow (one item, §8). The genuinely-relevant set is ~22 bugs (≈9 ACH-payment, 9 void, plus 1099/AR/OFR), and that is what this skill mines. ~22 deep-read.

---

## TABLE OF CONTENTS
1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — ACH email / file generation (ACH_EML)](#4-cluster-a--ach-email--file-generation-ach_eml)
5. [Cluster B — ACH posting / routing / stuck batches](#5-cluster-b--ach-posting--routing--stuck-batches)
6. [Cluster C — Void check run: posting, status & QLS sync](#6-cluster-c--void-check-run-posting-status--qls-sync)
7. [Cluster D — Bulk void & void dialog / export (AP061)](#7-cluster-d--bulk-void--void-dialog--export-ap061)
8. [Cluster E — 1099 on voided checks; OFR / release-from-suspense; AR apply](#8-cluster-e--1099-on-voided-checks-ofr--release-from-suspense-ar-apply)
9. [Diagnostic SQL & pointers](#9-diagnostic-sql--pointers)
10. [Escalation Guidance](#10-escalation-guidance)
11. [FIX-VERSION MATRIX](#11-fix-version-matrix)
12. [Key Code, Processes & Repos](#12-key-code-processes--repos)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cluster / cause | First check |
|---|---|---|
| ACH email step (`ACH_EML`) fails: *"Object cannot be cast from DBNull to other types"* | §4 — email SQL `SELECT_CONSTANT_VARIABLES_FOR_EMAIL_ACH` reads `BATCHCHECKRUNDETAIL.POSTED` which is no longer set (perf change moved POSTED to STATUSWORKFLOW) | #1723926 — patch uses `AUDITWORKFLOWLOG.CREATED` as POSTED |
| `ACH_EML` fails: *"service … IQDbConnectionFactoryProvider already exists in the service container"* and `Process will STOP` | §4 — service-container double-registration | #97736/#98969 (core fix); #106883 = same fix back-ported to a client hotfix |
| `ACH_EML` fails: *HTTP 503 Service Unavailable / "Error generating ACH Check Details Report"* | §4 — **SSRS report server down/misconfig**, NOT app code | #1725807 — check `QARCH_CNFG_CTRL` SSRS keys + `QCODE_CHECK_FORM` |
| "Send email to selected **vendor**" emails the whole vendor, not the one batch | §4 — missing custom WHERE clause limiting to the batch | #102451 (rejected — fixed by build upgrade) |
| ACH posting writes the **wrong routing number** after AP061 post | §5 — coalesce picks the Internal-Company-Bank routing # over the vendor's | #103656 |
| ACH vouchers **stuck in Post Pending** / unique-constraint on BA contact `'…ACH'` | §5 — POSTWKFL never actually posted; data/contact-tab dup | #110289 (script + BA005 contacts) |
| Voided check still shows **Cleared / Reported** in QLS (not Voided) after `CHKSTSUPDT` | §6 — check-status sync didn't carry the void; or zero-dollar reissue overwrote status | #1672697 (fixed 2024.10) → **#1773479 still open** for the zero-dollar-reissue subledger case |
| Void post doesn't sync to QLS at all / Land "Reported" not "Voided" | §6 — `CHECKRUNJOURNAL.LASTUPDATE` updated **without time** so sync misses it | #1415226, #1443705 |
| **Bulk void** (AP061, >1 batch) throws *CustomerOpenItemsApplyException / open item lock* exception | §7 — unhandled exception when open items are locked to other batches | #1725804 |
| Void batch check-run **picklist** times out / "No data found" | §7 — pick opened with a **NULL accounting date** generates an unfiltered/slow query | #1789704 |
| Application exception **exporting** a void check run | §7 — file-path security rights (`CHECK_LOCAL_FILE_PATH`), not pure code | #265188 |
| Can't void check runs created **before the Tax-Withholding enhancement**: *"Specified cast is not valid"* | §8 — new `TAXWITHHOLDINGAMT` column is NULL on old rows | #106595 (DB backfill script) |
| 1099 boxes show **duplicate / doubled pay amounts** when a voided check is involved | §8 — cartesian join in the 1099-override payables query | #237859 |
| "Release Owner Funds from suspense" (OFR) — security error / double payment to suspense | §8 — **config / training / security**, not a product defect | #1732502 (recommend-close) |

---

## 2. Pipeline & Concepts

```
[QRA disbursement / owner net] ─► AP voucher (AP055/AP171)
        │  validate → approve → POST (POSTWKFL / scheduled post workflow)
        ▼
   CHECK RUN  (AP061: create → approve → post → PRINT → EXPORT)        ── BATCHCHECKRUNMASTER / BATCHCHECKRUNDETAIL, CHECKRUNJOURNAL
        ├─► CHECK (printed/exported file; CHECK_FILE / CHECK_LOCAL_FILE_PATH config)
        ├─► ACH    (AP150: build ACH file + send vendor emails via ACH_EML / SSRS "ACH Check Details" report)
        │            ACH_ENTRYDETAIL / ACH_ADDENDA, routing # from vendor bank vs Internal-Co bank
        └─► VOID   (AP061 → N → Void; single or bulk) ── writes IDTRANSLOGVOID onto the original CHECKRUNJOURNAL row
                     │
                     ├─► QLS sync (CHKSTSUPDT / CHKSTSUPDTP, QP073) updates QLS Financial Detail status
                     └─► 1099 (QSTG1099OV / INT1099EXP) must net out voided checks

OFR (Owner Funds Release from suspense): QDO/QRA workflow to release suspended owner balances — config/security, separate from check-write code.
```

### Key terms (Quorum/Upstream vocabulary)
- **AP061** — Check Run screen (create/approve/post/print/export, and **Void** via the `N → Void` menu). Bulk void supports multiple payment selections (#1415046).
- **AP150** — ACH screen; *Send email to selected vendor* / *…selected checkrun* triggers the **`ACH_EML`** (a.k.a. `ACH_EMAIL`) batch process.
- **AP171 / AP055** — manual-check voucher / AP voucher creation that feeds the check run.
- **`ACH_EML`** — ACH email batch step; C# step object `Quorum.QCFS.QCFSBatchCore.QPSACHEmailNotification`. Runs the **SSRS "ACH Check Details"** report (looked up from `QCODE_CHECK_FORM.DESCRIPTION = 'ACH Check Details'`; SSRS server from `QARCH_CNFG_CTRL` keys `…SSRS…`). `Continue Process On Failed Execute = FALSE`, so any error **STOPS** the process.
- **`CHECKRUNJOURNAL`** — the canonical check ledger. A void posts `IDTRANSLOGVOID` (and `IDCHECKRUNJOURNAL_ORIG`) onto the **original** row. `LASTUPDATE` on that row drives the **QLS sync** — it must carry **time** or the sync misses it.
- **`CHKSTSUPDT` / `CHKSTSUPDTP`** (QP073) — QCFS→QLS Check Status Update job; C++ (`QSQL_UpdateCheckStatus.cpp` in `Quorum.Upstream.Shared.ClassicBatch/QPDllUpstreamUtil`). Maps QCFS voucher/check status back to QLS Financial Detail via `OFFSYSTEMCHECKNUM`.
- **POSTWKFL** — Scheduled Post Workflow; actually posts the check run from the QPEC. Updates to `CHECKRUNJOURNAL` during POSTWKFL happen in the **QPEC**, not the web BS (so reproduce there — #1415226).
- **`POSTED` flag move** — a perf change stopped setting `POSTED` in the child batch tables (`BATCHCHECKRUNDETAIL.POSTED`) and instead relies on `STATUSWORKFLOW`/`AUDITWORKFLOWLOG` in the master. SQL that still reads child `POSTED` now hits DBNull (#1723926).
- **OFR** = Owner Funds Release (release suspended owner balances). The closest thing to "escheat" in this data set; handled as QDO/QRA config + security, not a check-write code path.
- **1099 override** — `QSTG1099OV` (stage 1099 override) and `INT1099EXP` (`1099MISCINT`) export; must correctly net **voided** checks or amounts double (#237859).

---

## 3. Decision Tree

```
Check-write / payment case
│
├─ ACH email/file step failed (ACH_EML / "Send email")?  → GET process queue ID + the exact error text
│   ├─ "DBNull cannot be cast"                                 → §4  #1723926 (POSTED-date SQL; fixed 2025.04)
│   ├─ "IQDbConnectionFactoryProvider already exists"          → §4  #97736/#98969 (service-container; client back-port #106883)
│   ├─ HTTP 503 / "Error generating ACH Check Details Report"  → §4  #1725807 — SSRS server/report issue, NOT app code
│   └─ vendor email sends all batches                          → §4  #102451 (build upgrade)
│
├─ ACH posting wrong (not the email)?
│   ├─ wrong routing number after post                         → §5  #103656 (coalesce → Internal-Co bank)
│   └─ stuck Post Pending / unique constraint on BA '…ACH'     → §5  #110289 (script; BA005 contact dup)
│
├─ VOID?
│   ├─ void not reflected in QLS (still Cleared/Reported)      → §6  #1672697 (2024.10) ; **#1773479 OPEN** (zero-dollar reissue subledger)
│   ├─ void not syncing / LASTUPDATE missing time              → §6  #1415226, #1443705
│   ├─ BULK void throws open-item-lock exception               → §7  #1725804 (2025.04)
│   ├─ void picklist times out (NULL accounting date)          → §7  #1789704 (2026.04)
│   └─ exception EXPORTING a void run                          → §7  #265188 (file-path security)
│
├─ 1099 amounts wrong with a void?                             → §8  #237859 (cartesian join; 2020.09)
├─ can't void pre-tax-withholding old runs ("cast not valid")? → §8  #106595 (NULL TAXWITHHOLDINGAMT backfill)
├─ Release Owner Funds from suspense (OFR) error/double pay?   → §8  #1732502 — config/security/training (NOT a defect)
└─ AR payment can only approach zero / can't apply credit?     → §8  #66157 (code fix)
```

---

## 4. Cluster A — ACH email / file generation (ACH_EML)

**The largest genuine ACH cluster.** The `ACH_EML` step (AP150 → *Send email…*) is brittle: it stops the whole process on any failure, and it depends on (a) the `POSTED` date, (b) the QFC service container, and (c) an SSRS report server. Four distinct root causes:

| Sub-symptom (verbatim) | Root cause | Fix + fixed-in-build | Bug IDs / SF case |
|---|---|---|---|
| `Object cannot be cast from DBNull to other types` | Registered SQL `SELECT_CONSTANT_VARIABLES_FOR_EMAIL_ACH` selected `D.POSTED` from `BATCHCHECKRUNDETAIL`, but a perf change stopped populating child `POSTED`. | **Code fix:** SQL changed to `AWL.CREATED as POSTED` from `AUDITWORKFLOWLOG`. Merged to develop (`Quorum.Upstream.QCFS.Batch` PR #110004 + QCFS.Web PR #110007), tested RELQA. Iter **25.08 → 2025.04**. | **#1723926** |
| `The service Quorum.QFC.Core.Interface.IQDbConnectionFactoryProvider already exists in the service container. … Continue Process On Failed Execute Is FALSE for ACH_EML … Process will STOP.` | Double-registration of the DB connection-factory provider in the service container. | **Code fix** in `Quorum.Upstream.QCFS.Batch` (PR #7370, commits). NetSuite 310224. Sprint 51/53. **#106883** is the same fix **back-ported as a 2018.08 hotfix for client BLU** (QCFS.Batch→17.6.1, App.QPEC→17.7.9). | **#97736, #98969** (core); **#106883** (BLU hotfix) |
| `HTTP status 503: Service Unavailable. Error generating ACH Check Details Report.` (process queue had a real PQID) | **SSRS report server down or misconfigured** — *not* application code. Report chosen via `QCODE_CHECK_FORM` where `DESCRIPTION='ACH Check Details'`; server from `QARCH_CNFG_CTRL` `KEY_NM like '%SSRS%' and APP_LAYER_CD='ENV'`. | **No code fix** — fixed by restoring SSRS access on the box (#1728503 logged to review the server). Verify other SSRS reports run; confirm the report folder exists on the configured server. Iter 25.10. | **#1725807** |
| *Send email to selected **vendor*** behaves identically to *…selected checkrun* (emails every batch for the vendor) | No custom WHERE clause restricting the email to the single selected batch. | Closed **Rejected** — disposition: the fix ships in the build/version upgrade (no standalone patch). | **#102451** |

**Fix recipe (ACH_EML failure):**
1. Get the **process queue ID** and the **exact error string** (double-click the error in Batch Messages).
2. `DBNull cast` → confirm build ≥ **2025.04** (#1723926); the SQL must read `AUDITWORKFLOWLOG.CREATED`, not child `BATCHCHECKRUNDETAIL.POSTED`.
3. `IQDbConnectionFactoryProvider already exists` → confirm the #97736/#98969 fix is in the client's QCFS.Batch build; for an old/forked client build it may need a back-port (the #106883 pattern).
4. `HTTP 503 / report` → **this is infrastructure**: check the SSRS server in `QARCH_CNFG_CTRL`, confirm the "ACH Check Details" report deploys there and other SSRS reports run. Do not escalate as a code bug.

---

## 5. Cluster B — ACH posting / routing / stuck batches

| Symptom | Root cause | Fix / disposition | Bug ID |
|---|---|---|---|
| After posting an ACH batch (AP061), AP150 shows the **wrong routing number** (an old/defunct internal field) | When populating the vendor bank-account routing #, code does a **coalesce against the Internal Company Bank BA** — if that's populated it wins over the vendor's routing #. Behavior changed between the client's v8 and v17 builds. | **Closed/Verified.** Recommended change: remove/relax the coalesce so the vendor's `Routing No.` is used. (Internal-Co bank is read-only unless the vendor is flagged Internal on the Address tab.) | **#103656** |
| ACH vouchers **stuck in Post Pending**; data already visible in GL095; needed release by EOD | The batches **never actually posted** — POSTWKFL was throwing real errors; symptom was a **BA005 contact-tab uniqueness violation**: `Column 'ID, BA_NO, BASUF, CONTACTTYPECODE' is constrained to be unique. Value '…, …, 1, ACH' is already present.` | **Closed/Rejected** (no product code fix) — resolved operationally via **script** after confirming the duplicate `ACH` contact on BA005. | **#110289** |

**Pattern:** ACH-posting issues are usually **data/config** (a duplicate `ACH` business-associate contact, or an internal-bank routing # overriding the vendor's), not core engine bugs. Verify the **vendor bank account routing #** vs the **Internal Company Bank** flag, and the **BA005 contacts tab** for duplicate `ACH`-type rows, before escalating.

---

## 6. Cluster C — Void check run: posting, status & QLS sync

The recurring void-defect family is **the void not propagating to QLS / Land** because the link row's update is invisible to the sync, or a later zero-dollar reissue overwrites the void status.

| Symptom | Root cause | Fix + fixed-in-build | Bug / SF |
|---|---|---|---|
| Void posts in QCFS but **QLS Financial Detail still shows "Reported"** (Land shows "Voucher Paid"/"Reported", not "Check Voided") | When a void posts, `CHECKRUNJOURNAL.IDTRANSLOGVOID` is stamped on the original row but `LASTUPDATE` was written **without time**; the QLS sync (`m_SEL_QCFS_STATUS`) keys off `LASTUPDATE` and so **misses the change**. | **Code fix** so the void post writes `LASTUPDATE` **with time**. `Quorum.Upstream.QCFS.Web` PR #63812 (`feature/1415226_LastUpdate`) → develop. Iter **22.01**. Note: the POSTWKFL path updates `CHECKRUNJOURNAL` from the **QPEC** (#1415226). | **#1415226** |
| Same family — after a void + `CHKSTSUPDT`, QLS Financial Detail Status/JE-Status not updated | Follow-on of the LASTUPDATE-time issue, plus the sync query (`BATCHVOUCHERDETAIL`/`BATCHVOUCHERMASTER`/`CHECKRUNJOURNAL`) | **Code fix.** QCFS.Web PR #67245/#67248 (`feature/1443705_UpdtIssue`) → develop. Iter **22.06**. | **#1443705** |
| QLS→QCFS imported check is voided, then a **zero-dollar check run** is created for a negative voucher → original void flips to **"Cleared"**; GEC subledger then double-counts ($200 paid vs $100) | The zero-dollar/reissue path updates QLS status via `CHKSTSUPDT`; the sync uses `COALESCE(CJ.IDTRANSLOGVOID, CJV.IDTRANSLOGVOID)` and the new manual voucher is **not linked** to the QLS item by `OFFSYSTEMCHECKNUM`, so the void no longer reports. Manually creating a new QCFS voucher "goes against how the QLS↔QCFS status was built to work." | **OPEN / unresolved as a product fix.** Bug **#1773479 closed *Rejected*** after long dev discussion (Ben Weis): the new-voucher reissue scenario is **not supported** by the QLS status interface. Predecessor fix **#1672697** (GEC CHKSTSUPDT void handling, `QSQL_UpdateCheckStatus.cpp`, iter 24.18 → **2024.10**) addressed the basic void-not-updating case but not the zero-dollar reissue. | **#1773479** (open); **#1672697** (2024.10) — SF context: GEC, client filing 1099 |

**Fix recipe (void not in QLS):**
1. Confirm the client build has the **LASTUPDATE-with-time** fix (#1415226, 2022.01) and the **CHKSTSUPDT void fix** (#1672697, 2024.10).
2. Read the sync query trace: `select * from QARCH_QFCBATCH_SQL_TRACE where PROCESS_QUEUE_ID = <pqid>` — the void is detected via `COALESCE(CJ.IDTRANSLOGVOID, CJV.IDTRANSLOGVOID)` and the link is `OFFSYSTEMCHECKNUM`.
3. If the client created a **new manual voucher / zero-dollar reissue** for the void instead of acting on the QLS-originated voucher, that's the **#1773479 unsupported** path — the status link breaks because the new voucher has no matching `OFFSYSTEMCHECKNUM`. There is no code fix; advise voiding/reissuing against the original QLS-linked voucher.

---

## 7. Cluster D — Bulk void & void dialog / export (AP061)

| Symptom | Root cause | Fix + fixed-in-build | Bug |
|---|---|---|---|
| **Bulk void** (select >1 check-run batch) throws an exception then can't save | `CustomerOpenItemsApplyException: There were errors while trying to update open item lock states` thrown from `BsWorkflowBase.DraftWorkflow` when open items are **locked to other batches** — unhandled, so the whole dialog blows up instead of showing per-line validation. | **Code fix:** catch the exception and surface the lock as per-line-item validation; the batch simply doesn't save. QCFS.Web PR #110925 (`feature/1725804_VoidLockedOpenItemException`) → develop. Iter **25.09 → 2025.04**. | **#1725804** |
| Void batch check-run **picklist** throws *Timeout expired / "No data found"* | Opening the pick with a **NULL accounting date** (after clearing payment type + acct date but keeping bank account) generates an unfiltered `BATCHCHECKRUNMASTER` query that times out. | **Code fix:** prevent the pick from opening unless an accounting date is provided. `Quorum.Upstream.QCFS.ClassicGUI` PR #125301 (`feature/1789704_VoidDialogAP061`) → develop. Iter **26.06 → 2026.04** (found in regression). | **#1789704** |
| Bulk-void UI clarity (multi-payment selection) — labels/edit-box sizing/picklist name | UI enhancement to communicate multi-payment void (picklist ID 36085 renamed "Check Run Batch Void Selected Payment(s)") | **Fixed**, QCFS.ClassicGUI PR #63689 (cosmetic; colons removed). Iter **22.01**. | **#1415046** |
| **Application exception when EXPORTING** a void check run (after print) | **Security rights** on the export path, not check logic: Key Group `CHECK_FILE`, Key Name `CHECK_LOCAL_FILE_PATH` — QDevelopers lacked modify rights on the export share. | **Config / permissions** (DevOps to grant path rights). Verified fixed Core DEV. Iter **21.03**. | **#265188** |

**Fix recipe:** for bulk-void exceptions confirm build ≥ **2025.04** (#1725804); the symptom string is `CustomerOpenItemsApplyException` / "open item lock states." For the picklist timeout, confirm **2026.04** (#1789704) and note it only triggers when the **accounting date is NULL**. For the export exception, check the **`CHECK_LOCAL_FILE_PATH` share permissions** (#265188) before assuming code.

---

## 8. Cluster E — 1099 on voided checks; OFR / release-from-suspense; AR apply

| Symptom | Root cause | Fix / disposition + build | Bug / SF |
|---|---|---|---|
| 1099 override boxes show **duplicate / doubled pay amounts** when a voided check is in the data | **Cartesian join** in the payables query of the 1099-override process (`QSTG1099OV`) when a voided check is involved. | **Code fix** (invalid join corrected). QCFS.Web PR #37736/#37720. Pushed **Develop 2020.03 (17.19.7)** and **2020.09 (17.21.1)**. Verified CNR. (Sibling #237740 = `INT1099EXP`/`1099MISCINT` wrongly set to CSV instead of tab-delimited — same 20.21 wave.) | **#237859** (+#237740) |
| **Cannot void check runs created before the Tax-Withholding enhancement**: *"Specified cast is not valid"* | New column `BATCHCHECKRUNDETAIL.TAXWITHHOLDINGAMT` is **NULL** on rows created before the enhancement; void code casts it and fails. | **DB backfill script** sets the column to 0 on old rows (`…UPS_17.0.00.0013.0000_00_CORE_QCFS_01_106595.sql`). Verified 2019.03. (Core DB 180690.) | **#106595** |
| QRA **Releasing Owner Funds from Suspense (OFR)** — "I don't have security to release owner funds in UAT"; client also wanted to avoid doubling payments so monthly entries hit suspense directly | **Not a product defect.** Mis-routed to Engineering; it's a **QDO security permission + process/training** question (which security object grants OFR; how to perform OFR without double-posting). | **Closed/Rejected ("Recommend Close")** — SF case 25-01005668 closed with the OFR steps provided; no code change. | **#1732502** (SF 25-01022455 / 25-01005668) |
| AR payment application **can only approach zero**, blocking customers who apply a credit from one invoice to another | AR apply logic floored at zero, preventing cross-invoice credit application. | **Code fix.** PRs #1820/#1834/#1941 (QCFS.Web + ClassicGUI). NetSuite 306529. Sprint 37. | **#66157** |

> **Key insight — "escheat" in this product = OFR/suspense, and it is config not code.** No bug in the Financials area is titled "escheat," and the only "owner funds" item (#1732502) was a **security/training** matter, not a defect. When a case mentions escheat / unclaimed property / releasing suspended owner balances, treat it as a **QDO/QRA configuration + security** question first (which security object enables OFR), and verify the disbursement mechanics (check run / ACH / void) only if money actually moved incorrectly.

---

## 9. Diagnostic SQL & pointers

> **Caveat:** these column/SQL names are taken verbatim from the bug repros/dev comments (SQL Server, QCFS schema). **Verify against the client DB** and run a SELECT before any UPDATE/DELETE, in a transaction. The QLS-sync and CHKSTSUPDT logic is **C++** (`QSQL_UpdateCheckStatus.cpp`), so trace via `QARCH_QFCBATCH_SQL_TRACE`.

```sql
-- A. ACH email "DBNull cast" — the fixed SQL reads POSTED from AUDITWORKFLOWLOG, not child POSTED (#1723926)
--    Old (broken): ... D.POSTED ... FROM BATCHCHECKRUNDETAIL D ...
--    New (fixed):  ... AWL.CREATED as POSTED ... (join AUDITWORKFLOWLOG)
SELECT * FROM QARCH_CNFG_CTRL WHERE KEY_NM LIKE '%SSRS%' AND APP_LAYER_CD = 'ENV';   -- B. ACH SSRS 503 (#1725807)
SELECT DISTINCT * FROM QCODE_CHECK_FORM WHERE DESCRIPTION = 'ACH Check Details';     --    which report the ACH_EML runs

-- C. Void not syncing to QLS — does the original CHECKRUNJOURNAL row carry the void + a LASTUPDATE WITH TIME? (#1415226/#1443705)
SELECT IDBEOWNER, CHECKNUM, IDPAYMENTTYPE, CREATED, LASTUPDATE, IDTRANSLOGPOST,
       IDTRANSLOGVOID, IDCHECKRUNJOURNAL_ORIG, ID, BANK_CLR_DT
FROM   CHECKRUNJOURNAL
ORDER  BY IDBEOWNER, CHECKNUM, IDPAYMENTTYPE, IDTRANSLOGPOST;   -- LASTUPDATE must include time

-- D. QLS-sync trace for a CHKSTSUPDT run (the void is detected via COALESCE(CJ.IDTRANSLOGVOID, CJV.IDTRANSLOGVOID), link = OFFSYSTEMCHECKNUM)
SELECT * FROM QARCH_QFCBATCH_SQL_TRACE WHERE PROCESS_QUEUE_ID = <pqid> ORDER BY SEQ_NO;
SELECT * FROM QARCH_QUEU_PROCESS       WHERE PROCESS_QUEUE_ID = <pqid>;

-- E. Zero-dollar reissue breaking the void status (#1773479) — is the new voucher linked to the QLS item?
SELECT BM.IDBEOWNER, BM.CREATED, BM.USERKEY, BM.CONTROLTOTAL, BD.CHECKNUM, BD.PAYAMT, BD.OFFSYSTEMCHECKNUM
FROM   BATCHCHECKRUNMASTER BM JOIN BATCHCHECKRUNDETAIL BD ON BD.IDBATCHECKRUNMASTER = BM.ID
WHERE  BD.OFFSYSTEMCHECKNUM = '<offsystem#>';   -- a manual reissue with no/blank OFFSYSTEMCHECKNUM = the unsupported case

-- F. Pre-Tax-Withholding void cast failure (#106595): NULL column on old check-run rows
SELECT TAXWITHHOLDINGAMT, * FROM BATCHCHECKRUNDETAIL WHERE TAXWITHHOLDINGAMT IS NULL;   -- backfill to 0

-- G. Stuck-Post-Pending ACH unique-constraint (#110289): duplicate ACH contact on BA005
--    error: Column 'ID, BA_NO, BASUF, CONTACTTYPECODE' is constrained to be unique. Value '..,..,1,ACH' already present
SELECT * FROM <BA contact table> WHERE CONTACTTYPECODE = 'ACH';   -- look for the duplicate

-- H. Export-void file path permission (#265188): Key Group CHECK_FILE / Key Name CHECK_LOCAL_FILE_PATH
```

**Always capture for any check-write escalation:** the **process queue ID (PQID)**, the **exact error string**, the **screen (AP061/AP150/AP171)**, the **client + BE owner + check#/batch**, and whether a **void or zero-dollar reissue** is involved.

---

## 10. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- ACH email step throws **`DBNull cast`** (confirm build < 2025.04 → needs #1723926) or **`IQDbConnectionFactoryProvider already exists`** on an old/forked build (needs the #97736 fix or a back-port like #106883).
- A **void doesn't sync to QLS** and the client build predates **2022.01** (#1415226 LASTUPDATE-time) / **2024.10** (#1672697 CHKSTSUPDT void) — provide the `CHKSTSUPDT` PQID and the `QARCH_QFCBATCH_SQL_TRACE`.
- **Bulk void** throws `CustomerOpenItemsApplyException` (build < 2025.04 → #1725804) or the **void picklist times out** with a NULL accounting date (build < 2026.04 → #1789704).
- **1099 doubles** on voided checks (build < 2020.09 → #237859), or **AR apply** can't cross-apply a credit (#66157).
- Provide: **PQID + exact error**, screen, client + BE owner + check/batch numbers, repro, and confirm fix availability in the Upstream release notes / the linked PR's target release.

**Handle as Configuration / Infrastructure / Permissions (NOT a code fix):**
- **ACH_EML HTTP 503** → SSRS server/report (`QARCH_CNFG_CTRL` SSRS keys, `QCODE_CHECK_FORM` 'ACH Check Details') — #1725807.
- **Export-void exception** → `CHECK_LOCAL_FILE_PATH` share permissions — #265188.
- **Wrong routing #** → vendor bank vs Internal-Co bank coalesce / Internal flag on BA Address tab — #103656.
- **Stuck Post Pending** → duplicate `ACH` contact on BA005 (POSTWKFL was erroring) — #110289 (script).
- **Pre-Tax-Withholding void cast** → DB backfill of `TAXWITHHOLDINGAMT` — #106595.

**Handle as Training / Config (NOT a defect):**
- **OFR / Release Owner Funds from suspense** ("escheat"-adjacent) → QDO **security permission** to release funds + the documented OFR steps (avoid double-posting); do not send to Engineering — #1732502.

**Known still-open / unsupported:**
- **#1773479 (GEC)** — voiding then creating a **zero-dollar reissue / new manual voucher** flips the original void to "Cleared" and double-counts in the subledger. Closed **Rejected**: the new-voucher reissue path is **not supported** by the QCFS↔QLS status interface (no `OFFSYSTEMCHECKNUM` link). Advise reissuing against the original QLS-linked voucher; no fix build.

---

## 11. FIX-VERSION MATRIX

| Bug | Symptom (short) | State / Reason | Fixed-in build (from iteration/PR) | Repo / artifact | SF case / origin |
|---|---|---|---|---|---|
| **#1723926** | ACH_EML DBNull cast (POSTED date) | Closed / Ready-for-QA → tested RELQA | **2025.04** (iter 25.08) | QCFS.Batch PR #110004 + QCFS.Web PR #110007 | tag `not 2026.04 Ups` |
| **#1725807** | ACH_EML HTTP 503 (SSRS) | Closed | n/a — **SSRS infra** (iter 25.10) | server config; review WI #1728503 | — |
| **#97736 / #98969** | ACH_EML service-container dup | Closed / Verified | Sprint 51/53 (≈2019) | QCFS.Batch PR #7370 | NetSuite 310224 / 310297 |
| **#106883** | same, back-ported for BLU | Closed / Rejected | **2018.08 hotfix** (QCFS.Batch 17.6.1) | QCFS.Batch | client BLU; NS 310540 ref |
| **#102451** | vendor email = all batches | Closed / Rejected | fixed by build/version upgrade | — | — |
| **#103656** | ACH wrong routing # (coalesce) | Closed / Verified | Sprint 55 (≈2019) | QCFS (vendor bank logic) | NetSuite-era |
| **#110289** | ACH stuck Post Pending (BA dup) | Closed / Rejected | script (no code) | BA005 contacts | Northwoods |
| **#1415226** | void LASTUPDATE missing time | Closed / Ready-for-QA | **2022.01** (iter 22.01) | QCFS.Web PR #63812 (QPEC for POSTWKFL) | internal |
| **#1443705** | void status not synced to QLS/Land | Closed / Fixed | **2022.06** (iter 22.06) | QCFS.Web PR #67245/#67248 | TestRail 2910849 |
| **#1672697** | CHKSTSUPDT void not updating QLS | Closed | **2024.10** (iter 24.18) | Shared.ClassicBatch `QSQL_UpdateCheckStatus.cpp` | GEC (381) |
| **#1773479** | void→Cleared on zero-dollar reissue | **Closed / Rejected (unsupported)** | **none — open gap** | (QLS↔QCFS status interface) | GEC; client 1099 |
| **#1725804** | bulk void open-item-lock exception | Closed / Ready-for-QA → RELQA | **2025.04** (iter 25.09) | QCFS.Web PR #110925 | tag `not 2026.04 Ups` |
| **#1789704** | void picklist timeout (NULL acct date) | Closed / Ready-for-QA → RELQA | **2026.04** (iter 26.06, found in regression) | QCFS.ClassicGUI PR #125301 | — |
| **#1415046** | bulk-void UI clarity | Closed / Fixed | **2022.01** (iter 22.01) | QCFS.ClassicGUI PR #63689 | — |
| **#265188** | exception exporting void run | Closed / Ready-for-QA | **2021.04** (iter 21.03) — config/perms | `CHECK_LOCAL_FILE_PATH` rights | — |
| **#237859** | 1099 doubles on voided check (cartesian) | Closed / Verified | **2020.03 (17.19.7) & 2020.09 (17.21.1)** | QCFS.Web PR #37736/#37720 | (with #237740) |
| **#106595** | can't void pre-tax-withholding (NULL cast) | Closed / Ready-for-QA | **2019.03** | DB script `…_106595.sql` | Core DB 180690 |
| **#66157** | AR apply can only approach zero | Closed / Ready-for-QA | Sprint 37 (≈2018) | QCFS.Web/ClassicGUI PR #1820/#1834/#1941 | NetSuite 306529 |
| **#1732502** | OFR release-from-suspense security | **Closed / Rejected (not a defect)** | n/a — config/training | QDO security object | SF 25-01005668 / 25-01022455 |
| **#1622238** | BA/Owner # search field too small | Closed / Rejected | n/a — UI enhancement, not check-write | QDO BA picklist | SF 23-00918110 |

> Build mapping is derived from **iteration path → release** (e.g. 20.21→2020.09, 21.03→2021.04, 22.01/22.06→2022.x, 24.18→2024.10, 25.08/25.09/25.10→2025.04, 26.06→2026.04) plus PR target branches (all merged to `develop`) and dev comments. No `Microsoft.VSTS.Build.IntegrationBuild` field was populated on these bugs, so **confirm the exact patch build in the Upstream release notes** before quoting it to a client.

---

## 12. Key Code, Processes & Repos

### Processes / screens
| Process / screen | Purpose | Notes |
|---|---|---|
| **AP061** | Check Run (create/approve/post/print/export) + **Void** (`N → Void`, single & bulk) | bulk void open-item lock (#1725804); void picklist NULL-date timeout (#1789704); export path perms (#265188) |
| **AP150** | ACH screen — *Send email to selected vendor/checkrun* | triggers `ACH_EML`; vendor-vs-checkrun WHERE clause (#102451) |
| **`ACH_EML`** (`ACH_EMAIL`) | ACH vendor-email batch step | C# `QPSACHEmailNotification`; STOPS on any error; SQL `SELECT_CONSTANT_VARIABLES_FOR_EMAIL_ACH`; runs SSRS "ACH Check Details" |
| **POSTWKFL** | Scheduled Post Workflow (posts check runs) | updates `CHECKRUNJOURNAL` from the **QPEC** (#1415226) |
| **CHKSTSUPDT / CHKSTSUPDTP** (QP073) | QCFS→QLS check-status sync | C++ `QSQL_UpdateCheckStatus.cpp`; link via `OFFSYSTEMCHECKNUM`; void via `COALESCE(IDTRANSLOGVOID…)` |
| **QSTG1099OV / INT1099EXP** | 1099 override stage / `1099MISCINT` export | must net voided checks (#237859/#237740) |

### Code locations (confirmed via ADO PRs/commits)
| Symbol / file | Repo / path | Cluster |
|---|---|---|
| `CheckRunTransaction.cs` → `PostMe()` (void special logic, IDTRANSLOGVOID, LASTUPDATE) | `Quorum.Upstream.QCFS.Web` `/Quorum.QCFS.BS/Base/` | §6 |
| `BsWorkflowBase.DraftWorkflow` (CustomerOpenItemsApplyException) | `Quorum.Upstream.QCFS.Web` `/Quorum.QCFS.BS/Base/` | §7 bulk void |
| `QPSACHEmailNotification.cs` (`ExecuteReport`, ACH_EML) | `Quorum.Upstream.QCFS.Batch` (`Quorum.QCFS.QCFSBatchCore`) | §4 ACH email |
| `SELECT_CONSTANT_VARIABLES_FOR_EMAIL_ACH` (registered SQL) | QCFS.Batch / QCFS.Web (registered SQL) | §4 |
| AP061 void dialog / picklist | `Quorum.Upstream.QCFS.ClassicGUI` | §7 |
| `QSQL_UpdateCheckStatus.cpp` (CHKSTSUPDT) | `Quorum.Upstream.Shared.ClassicBatch` `/QPDllUpstreamUtil/` | §6 QLS sync |
| `…_106595.sql` (TAXWITHHOLDINGAMT backfill) | `Quorum.Upstream.QCFS.Database` `/…/` | §8 |
| Metadata (picklists, ImpExp 1099MISCINT) | `Quorum.Upstream.Metadata` | §4/§8 |

### Repos (confirmed GUIDs)
- **`Quorum.Upstream.QCFS.Web`** (`6eeec009-…`) — BS layer: check-run/void posting, bulk-void, 1099-override query, AR apply.
- **`Quorum.Upstream.QCFS.ClassicGUI`** (`66ff8d68-…`) — AP061/AP150/AP171 screens, void dialog/picklist.
- **`Quorum.Upstream.QCFS.Batch`** (`bb284f70-…`) — ACH email process (`ACH_EML`).
- **`Quorum.Upstream.QCFS.Database`** (`1c592c7a-…`) — DB fix scripts (e.g. #106595).
- **`Quorum.Upstream.Shared.ClassicBatch`** — C++ `CHKSTSUPDT` (QLS status sync).
- **`Quorum.Upstream.Metadata`** (`3c54aeee-…`) — picklists, import/export defs.

> **Companion (planned):** SKILL_ADO_QCFS_AP_Voucher, SKILL_ADO_QRA_Revenue_Distribution, SKILL_ADO_QDO_DivisionOrder_Suspense (OFR/escheat owner-side detail lives there). Always confirm the client build against the Upstream release notes before quoting a fix version.

---

*Skill created 2026-06-14. Source: 92 Closed/Resolved ADO Financials bugs matched on check-write/ACH/void/OFR title terms (40 were attachment-UI false positives from `ACH`⊂`attachment`; CW*/OFR/escheat/negative-check matched 0 titles). ~22 relevant bugs deep-read with descriptions, repro steps, dev comments, and linked PRs. ADO bugs: #1723926, #1725807, #97736/#98969, #106883, #102451, #103656, #110289, #1415226, #1443705, #1672697, #1773479, #1725804, #1789704, #1415046, #265188, #237859/#237740, #106595, #66157, #1732502, #1622238.*
