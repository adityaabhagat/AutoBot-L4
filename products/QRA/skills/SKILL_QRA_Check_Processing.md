# SKILL: QRA Check Processing Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QRA (My Quorum Revenue Accounting — upstream oil & gas owner/royalty accounting in the myQuorum / On Demand suite)
**Scope:** The owner-payment pipeline — **Pre-Checkwrite (PCW)**, **Checkwrite (CW_MAIN)**, **Owner Funds Release (OFR / CWOWFNDRLS)**, **check & bank-file export** (paper PDS, Wells Fargo / JP Morgan / MUFG / Comerica / NACHA bank ACH files, EnergyLink/Enverus revenue files), **ACH statement email** (CWACHEMAIL), **Escheat / NAUPA**, **1099 export**, **Check Input (CI)**, void/bank-rec status, and the QRA→QCFS handoff. This is the back end that turns distributed revenue into owner checks/ACH and the files that go to banks and to the GL.
**Companion skills (Upstream Assistant):** revenue distribution / DOI / suspense → upstream revenue-distribution skill; JIB-to-revenue netting and QCFS/AR posting → upstream JIB skill; master data (BA, owner, bank account, property) → upstream master-data skill. This skill *consumes* posted owner-payable balances (subledger 01, escheat SL 24, etc.) and *produces* checks/ACH files, statements, escheat/NAUPA files, and 1099s — when the **amount** is wrong, suspect upstream distribution/suspense/DOI first (CW is usually the messenger); when the **file/process/format** is wrong, it is almost always QRA.

> **Evidence base:** 1,743 closed QRA Check-Processing cases (Case_Category: Check Write 1,510 + Check Input 226 + Check Interfaces 7). Root-cause split: (blank) 395, Customer Error 260, Customer Cancelled 160, **Software Defect 157**, Training 111, **Application Configuration 101**, Business Change 60, Performance 57, others. This skill mines the **268 actionable** cases (Software Defect 157 + Application Configuration 101 + ChangeConfig 10) for fix recipes, plus ~60 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining; where a cluster had no clear resolution in the mined cases it is marked *resolution pattern unclear*.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — Negative / under-minimum / zero checks (HIGH FREQUENCY)](#4-cluster-a--negative--under-minimum--zero-checks)
5. [Cluster B — Checkwrite / PCW / OFR process failures, footing & primary-key errors](#5-cluster-b--checkwrite--pcw--ofr-process-failures)
6. [Cluster C — Dynamic-export check files (CHKFLWF / REDDOG / Enverus / EnergyLink / PDS)](#6-cluster-c--dynamic-export-check-files)
7. [Cluster D — Bank ACH / NACHA / MUFG / JP Morgan / Comerica file errors](#7-cluster-d--bank-ach--nacha--mufg--jp-morgan--comerica-file-errors)
8. [Cluster E — CWACHEMAIL / ACH statement email](#8-cluster-e--cwachemail--ach-statement-email)
9. [Cluster F — Escheat / NAUPA](#9-cluster-f--escheat--naupa)
10. [Cluster G — OFR & check-detail progressive-rounding / footing errors](#10-cluster-g--ofr--check-detail-progressive-rounding--footing-errors)
11. [Cluster H — Void / sent-to-bank flag / bank-rec (CW005 ↔ BR005) status scripts](#11-cluster-h--void--sent-to-bank-flag--bank-rec-status-scripts)
12. [Cluster I — Check Input (CI) errors](#12-cluster-i--check-input-ci-errors)
13. [Cluster J — Performance / timeout / out-of-memory (large export & batch splitting)](#13-cluster-j--performance--timeout--out-of-memory)
14. [Cluster K — 1099 export](#14-cluster-k--1099-export)
15. [Known ADO Items](#15-known-ado-items)
16. [Diagnostic SQL](#16-diagnostic-sql)
17. [Expected-Behavior / User-Education FAQ](#17-expected-behavior--user-education-faq)
18. [Key Code, Processes & Repos](#18-key-code-processes--repos)
19. [Escalation Guidance](#19-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| **Negative-dollar checks generated** / bank rejected file for a negative payment | Netting/min-release config not applied across pay types; reversal (DRI reversal / PPA / sequence-2 acquired interest) drives a tier negative | §4 — `USE_NETTING_FOR_CHK_MIN_RELEASE`; check whether a reversal/deficit owner is involved; known core defect family |
| Owner with payable balance > minimum **not getting a check** | Min-release / JIB over-netting logic, or owner in Minimum Release / Stop-Pay / suspense | §4 — `RSTG_PCW_MIN_AMT_OWNR`, `CheckMinimumPay()` / `dCheckJIBOverNetAmt`; Stop-Pay & suspense |
| **CW_MAIN / PCW "Completed with errors"** / fails / stuck | Bad data in staging, a duplicate/index issue, or a left-over lock | §5 — get **PQID + step + exact error**; check index/footing/primary-key; CW_JELK lock |
| Checkwrite **footing error** (`does not foot across … TRANS_VAL_AMT`) / "did not foot, rejected" | Backup-withholding double-count or tax/deduct mismatch on the record | §5/§10 — footing detail; BUWH on PPNs |
| **OFR "Progressive rounding error in transaction sequence"** | Decimal-interest rounding / OFR-creation script split that doesn't sum to 100% | §10 — clean-up script; DO130 transfer-all-suspense workaround; known hotfix |
| Check-file export **SPE'd / "Unable to locate or create DAL"** after an upgrade/hotfix | Dynamic-export def points to a client `ESUITE_Q*` view / wrong core view; metadata in wrong layer | §6 — fix the export def to point to the **core** view; correct the client (`Q<CLIENT>`) metadata layer |
| Enverus/EnergyLink file **fails to load** (datatype/blank element, extra rows, runs forever) | `QARCH_EXP_DEF_DATA_FILTER` flag (e.g. `EXP_TO_PDS_FL`) mismatch; null/blank XML element; security `SEC_USER_ID` | §6 — align FILTER_VALUES to the export flag; blank element default |
| **Bank ACH / NACHA file** missing routing/origin IDs, footing off, MUFG tract/null fields | Metadata in non-client layer overwritten on upgrade; null columns in the export view | §7 — re-apply config in client layer; null-handle the view |
| **CWBANKACH** "unhandled exception … QPSCWBANKACHEXPORT failed Execute" after upgrade | Process-step / export defect surfaced by upgrade | §7 — ADO #1680444 (MEW 2024.04) |
| **CWACHEMAIL** fails / runs 23+ hrs / mixes owner details / no statements sent | Too many child processes; very large statements (>7k lines); overlapping jobs; bad BA email casing | §8 — split/reduce children (software update); move big checks; fix BA email |
| **Escheat / NAUPA** completes with errors / no records to file / amounts doubled | Reporting-method WHERE-clause gap (`N&H` vs `NPA`), missing print-name config, foreign/unknown-address doubling | §9 — EC010 reporting method; supplemental script; known hotfixes |
| Voided checks keep erroring / void process re-voids them | Void posted but `PROC_FL` never set to Y in `RONL_VOID_CHK` | §11 — script `PROC_FL = 'Y'` (recurring, low-risk) |
| Checks **stuck (OS) in CW005** though cleared in QCFS BR005 (or reversal didn't flip to OS) | `CHKREGUPDT` not run inside the BR005 post/reversal | §11 — run `CHKREGUPDT`; script status; ADO #1726731 |
| Need to re-send paper checks but files gone / `PMT_SENT_TO_BANK_FL='Y'` with no file | Flag set but export file deleted/never archived | §11 — script reset `PMT_SENT_TO_BANK_FL='N'` (recurring at EQT) |
| **CI** errors: distribution failed, attachment, "no detail", reject, pressure base, well completion required | CI config/template (interest types, pressure base, required fields) or stuck/cancelled process | §12 — code-table / config; clear stuck process |
| 1099 export SPE / wrong (large negative) owner net value | Staging table missing BOX columns (hotfix) or distribution feeding bad net | §14 — 1099 hotfix; data |

---

## 2. Pipeline & Concepts

```
[Revenue distribution → owner-payable balances by DOI/owner/SL]   (upstream — see revenue-distribution skill)
      │
      ▼  PRE-CHECKWRITE  (PCW / CWPREPOST)  — stage who gets paid, apply minimum release & JIB netting → JE055/JE102, RSTG_PCW_*
      │      (must be POSTED in JE100 before CW)
      ▼  CHECKWRITE  (CW_MAIN, multi-step)  — cut checks/ACH → RTRN_CHK_RGSTR (the check register), JE100/JE101 entries
      │      ├─ OFR (CWOWFNDRLS) — Owner Funds Release / suspense release into the run
      │      └─ Escheat (CWMNLESCHT / CWECHNAUP) — unclaimed-property checks + NAUPA/HRS files
      │
      ▼  EXPORT
      ├─ Paper checks / detail (RPT_CWR046, PDS export, CKFLQRAPPD)
      ├─ Bank ACH files (CWBANKACH → NACHA; bank dynamic exports: Wells Fargo, JP Morgan, MUFG, Comerica)
      ├─ Revenue detail files (EnergyLink / Enverus via REDDOG / CHKFL* / ENVCHKEXP dynamic exports)
      ├─ ACH statement emails (CWACHEMAIL)
      └─ 1099 export (CW1099EXPT)
      │
      ▼  QRA → QCFS  (QCFSEXPORT / Check Register Update CHKREGUPDT) → GL & bank reconciliation (BR005)
```

### Key terms (Quorum / QRA vocabulary)
- **PCW (Pre-Checkwrite)** = `CWPREPOST` — determines payees, applies **owner/company minimum check amount** and **JIB netting**, writes `RSTG_PCW_*` staging + the JE055/JER055 pre-check-write report. **Must be posted in JE100 before CW**; running CW without posting PCW is the single most common user error (§17).
- **CW_MAIN** = the Checkwrite process (runs many steps; PQID-driven). Cuts checks into **`RTRN_CHK_RGSTR`** (the revenue check register; `CHK_RGSTR_SEQ_NO`, `CW_CHK_STAT_CD` = OS/CL/VD, `PMT_SENT_TO_BANK_FL`, `RYL_PMT_TYPE_CD` PP/DW, `CHK_DT`, `BUS_UNIT_CD`, `OPER_BUS_SEG_CD`).
- **OFR** = **Owner Funds Release** = `CWOWFNDRLS` (screen DO130, staging `RSTG_OWNR_FUND_RLS`, `TRANS_SEQ_NO`). Releases suspended funds into the run. Prone to **progressive-rounding** and out-of-memory on large batches (§10/§13).
- **CW_JELK** = the Checkwrite system **lock** record. It is cleared automatically when CW completes. Users must **never** delete/release it manually — doing so breaks the run and requires a script to re-insert it (§17).
- **Minimum Release** = owner/company minimum check amount; owners under it are held (`RSTG_PCW_MIN_AMT_OWNR`). **QRA does not cut negative checks** by design (§17).
- **JIB netting** = nets an owner's working-interest JIB AR against their revenue before paying; controlled by configs like `USE_NETTING_FOR_CHK_MIN_RELEASE`, `JIB_NETTING_PROPERTY_LOOKUP` / `GCDE_DFLT_PROP_JIB`. Over-netting can zero or negate a check (`dCheckJIBOverNetAmt`).
- **Dynamic Export** = QRA's metadata-driven file generator. Definitions live in `QARCH_EXP_DEF_*` tables (`QARCH_EXP_DEF_DETAIL`, `QARCH_EXP_DEF_DATA_FILTER`, `QARCH_EXP_DEF_DATA_UPDATE`, `QARCH_EXP_DEF_DATA_HRCHY`). Each export has an **ExpId** (e.g. `WELLSFARGO`, `CEN_REDDOG`, `PDS_ENC`, `ENVERUS`) and runs in an **AppLayer** (`Q<CLIENT>`). Most "export broke after upgrade/hotfix" cases are a **def/metadata-layer** problem, not a code bug.
- **REDDOG / CHKFL\*** = the revenue-detail dynamic exports to **EnergyLink (Enverus)**. `ENVCHKEXP`, `CHKFLREDOG/CHKFLREDOD`, `CHKRDGSPLT`, `EXPCHKPDS`, `CHKFLWF` (Wells Fargo) are the launcher process IDs.
- **Escheat** = unclaimed-property processing: `CWMNLESCHT` (cut escheat checks, often to a state), `CWECHNAUP` / `CWCUESCHT` (NAUPA / HRS export). Config in code tables **EC010 (Escheat Processing Rules)**, 4021/4022 (state/escheatable), 9173 (file paths). Reporting method **NPA** (NAUPA only) vs **N&H** (NAUPA & HRS) matters.
- **QCFSEXPORT / CHKREGUPDT** = the handoff that pushes QRA financial activity to **QCFS** (the GL / financials engine) and updates the QRA check register from bank-rec activity. **CW must complete before any JE post / QCFS export.**
- **CW005 / CW020 / CW035 / CW010 / BR005** = key screens. **CW005** = check register inquiry (status OS/CL/VD). **CW020** = void check. **CW035** = update check status. **CW010** = state withholding config. **BR005** = (QCFS) bank reconciliation. **JE100/JE101/JE102/JE055/JER055** = journal/pre-CW screens & reports.
- **QPEC** = the QRA batch/process engine server(s). "QPEC restart / graceful restart" clears many stuck-process and timeout symptoms (config/ops, not code).

---

## 3. Decision Tree

```
QRA Check-Processing case
│
├─ A check AMOUNT looks wrong (negative / zero / under-minimum / owner not paid)?
│   ├─ Negative or zero check cut / in bank file        → §4  (netting+min-release config; reversal/deficit owner; core defect family #1353354/#1537586/#1636588/#1658185)
│   └─ Owner over minimum not getting a check            → §4  (RSTG_PCW_MIN_AMT_OWNR; JIB over-netting; Stop-Pay/suspense; min-release defect 22-00560559 / 25-01045271)
│
├─ A PROCESS failed / "Completed with errors" / stuck?  → GET PQID + STEP + EXACT ERROR
│   ├─ CW_MAIN footing / primary-key / index error       → §5  (footing detail; rebuild index 25-01031507; exclude owner 25-01049143)
│   ├─ OFR "Progressive rounding error in trans seq"      → §10 (clean-up script / DO130 workaround / hotfix #1318171)
│   ├─ Out of memory / runs many hours                    → §13 (memory/purge; OFR child-process split; batch the run)
│   └─ Stuck in Processing after a cancel / missing lock   → §5/§17 (re-insert CW_JELK / PCW lock; clear status — usually user error)
│
├─ A FILE failed to generate or load?
│   ├─ Check-file dynamic export SPE'd / "locate or create DAL" → §6 (export def → core view; fix client metadata layer)
│   ├─ Enverus/EnergyLink file fails to load / datatype / extra rows → §6 (QARCH_EXP_DEF_DATA_FILTER flag; blank-element default)
│   ├─ Bank ACH / NACHA / MUFG / JP Morgan / Comerica wrong → §7 (client-layer metadata re-apply; null-handle view; ADO #1680444)
│   └─ ACH statement EMAILs fail / mix owners / not sent     → §8 (CWACHEMAIL child-process / big-statement / BA-email)
│
├─ Escheat / NAUPA?                                       → §9  (EC010 reporting method NPA vs N&H; print-name config; doubling hotfix #1321337)
│
├─ Void / bank-rec / sent-to-bank status wrong?           → §11 (PROC_FL='Y'; CHKREGUPDT / ADO #1726731; reset PMT_SENT_TO_BANK_FL)
│
├─ Check Input (CI)?                                       → §12 (interest types / pressure base / required field config; clear stuck CI)
│
├─ 1099?                                                   → §14 (1099 hotfix; staging BOX columns; bad net value)
│
└─ "How do I…", ran CW without posting PCW, accidental void/cancel, why-no-negative-checks → §17 Expected-Behavior FAQ
```

---

## 4. Cluster A — Negative / under-minimum / zero checks

**The single largest and most recurring defect-and-config signature in QRA Checkwrite.** The system is *designed* not to cut negative checks, so a negative/zero check in `CW005` or (worse) in a file already sent to the bank is either a **netting/min-release config gap** or a **core distribution defect**, and several core defects have been fixed across releases.

**Symptoms (verbatim):**
- "negative check amount was generated in file sent to bank … rejected because of the negative payment" (22-00830939).
- "PCW and CW were ran and **negative payments/checks** were generated" after a DRI upload then DRI **reversal** on the same entry (23-00934272).
- "The 1098 CW generated 19 owners with **negative checks**, totaling ($188K). These owners are in **deficit due to some PPAs**" (24-00965101).
- "Owner … since go-live has not received a check … set up to be **JIB netted** … balance far greater than $10 … showed up in `RSTG_PCW_MIN_AMT_OWNR`" (22-00560559).
- "2 owners with payable balances over $100 … did not get checks generated. Even with NM Withholding applied, balances still would be over $100 min pay" (25-01045271).

**Root causes & fixes seen:**
- **Netting not applied across pay types / min-release (config).** Enabling **`USE_NETTING_FOR_CHK_MIN_RELEASE`** fixed a negative check that reached the bank file (22-00830939). 25-01050336 ("Checkwrite generated negative checks") resolved as **config**. This is the first thing to check.
- **A reversal / deficit drives the net negative.** A DRI reversal (23-00934272), prior-period adjustments / PPAs putting owners in deficit (24-00965101), or a **sequence-2 acquired interest still taking deductions** (22-00704966) push the owner net below zero. Verify the *upstream* transaction first; the CW number is correct given the inputs in many of these (often closed as Training, §17 — e.g. 25-01032653: WI JIB nets to $0, then OR interest debit drops it negative, "QRA does not cut negative checks").
- **Core Checkwrite defect family (code).** Multiple closed bugs fixed CW generating negative checks: **#1353354** (Ovintiv/ECA, 22-00512952 / 22-00512525 Build-34 negative & zero checks), **#1537586** (EQC, 22-00823270 negative checks & ACH payments), **#1636588** (CNX/SGY 2022.04 negative check amounts, 23-00931490/23-00934272), **#1658185** (CORE_TST_QRA negative checks). Long-term fixes also under 22-00680765 ("long term fix for CheckWrite cutting negative checks", Encino) and 24-00965101 ("resolved in an update the customer implemented").
- **Owner over minimum not paid (code).** 22-00560559 required a **code fix** (patch also covered 20-00086023, 20-00081693); 25-01045271 is a confirmed **defect fixed in the Sept hotfix for 2025.04**. 26-01069501 traced to a negative **`dCheckJIBOverNetAmt`** in `CheckMinimumPay()` (JIB over-netting) — investigated via the OFR/min-pay logic.

**Fix recipe:**
1. Pull `CW005` for the BA/owner; confirm the sign and the `RYL_PMT_TYPE_CD`. If a **negative reached a bank file**, void the check, adjust control totals with the bank, and treat the root cause separately.
2. Check **min-release / netting config**: `USE_NETTING_FOR_CHK_MIN_RELEASE`, owner/company minimum amounts, `JIB_NETTING_PROPERTY_LOOKUP`. Enabling correct netting resolved 22-00830939.
3. Check for a **reversal / PPA / deficit / sequence-2 acquired interest** behind the negative — if the inputs are correct, this is **Expected Behavior** (§17), not a defect.
4. For "owner over minimum not getting paid," inspect `RSTG_PCW_MIN_AMT_OWNR` and the PCW debug (`CheckMinimumPay()` / `dCheckJIBOverNetAmt`), and confirm Stop-Pay/suspense isn't set. If config is clean, it is the known min-release defect — confirm the build (25-01045271 → 2025.04 Sept hotfix).
5. If a negative/zero check is cut with clean config and no reversal, escalate as the **core CW negative-check defect** (cite #1353354 / #1537586 / #1636588 / #1658185) with PQID + BA + amounts.

---

## 5. Cluster B — Checkwrite / PCW / OFR process failures

`CW_MAIN` (or PCW / CWPREPOST) **"Completed N of N steps with errors"** or fails outright. Distinct from §4 (output wrong) — here the process crashes. Always get **PQID + the failing step + the exact error**.

| Signature | Root cause | Fix | Case / ADO |
|---|---|---|---|
| CW_MAIN "Completed 32 of 32 with errors"; `Execution Error 666 … maximum system-generated unique value for a duplicate group was exceeded for index` | Corrupted/over-full index on a JTRN adjustment table | **Rebuild the index** on `JTRN_JE_INPUT_ACCT_ADJ_CTGY` (script); same pattern seen at Pioneer | 25-01031507 / RCA 25-01032084 |
| **Primary Key Violation** in Checkwrite | A single owner's data (here a script-changed BA tax ID) collided | **Workaround:** exclude the owner via **code table 4048**; RCA separate | 25-01049143 / RCA 25-01049219 |
| CW_MAIN **`TRANS_VAL_AMT` footing error** — "Record does not foot across … does not equal TRANS_AMT … will be rejected" | Tax/deduct/withholding child amounts don't sum to the transaction value | Footing detail fix (see §10); BUWH double-count was one cause (22-00544826) | 23-00881976, 22-00544826 |
| CW_MAIN failing while testing an update; adding `CW_JELK` lock record didn't help | Process/data from the in-flight update | Engineering assist | 24-00993168 (rel. 24-00977208) |
| PCW errors: **duplicate in `RSTG_CORE_FNCL_JIB_UPLOAD`** | Stale archive/staging rows after a refresh | **Clean the archive/staging tables** | 24-00945978 |
| PCW SPE'd / failed after a v16→v17 refresh | Bad pre-CW data from refresh timing | Remove bad data from pre-CW tables | 25-01003747 |
| `QRANET` JIB import batch **won't post** ("APPLIED AMOUNT + CURRENT AMOUNT MUST APPROACH ZERO") | Zero-amount applied to a QRANET JIB batch in AR076 | Toggle **AR044 "Allow Non-Zero Payment Application"** on, post, toggle off; **fixed in May hotfix** | 22-00566209 / **#1411454** |
| OFR launched from QP043 errors (MEW 2023.04) | OFR launcher defect | Bug fix | 23-00925668 / **#1628612** |
| Various process "stuck in Processing" / `JE100` shows PRC after a cancel | User cancelled mid-run; status not reset | Script the status flags; re-insert lock (§17) | 22-00582895, 25-01035714, 25-01037294 |

**Fix recipe:**
1. Get **PQID + step name + exact error** (export the error grid). The error text routes you: `index … duplicate group` → rebuild that index (25-01031507); `Primary Key Violation` → isolate/exclude the offending owner (code table 4048, 25-01049143); `does not foot across` → §10; `duplicate in RSTG_*` → clean staging (24-00945978).
2. Confirm **PCW was posted** in JE100 before CW (the #1 false alarm, §17). Never let the user manually delete `CW_JELK` (§17).
3. If the run is **stuck after a cancel**, do not re-run blindly — script the status/lock back to a clean state first (§11/§17).
4. Footing errors are data/calc at the record level (§10); rebuild-index and stale-staging errors are operational; persistent code crashes (OFR launcher, etc.) escalate with PQID.

---

## 6. Cluster C — Dynamic-export check files (CHKFLWF / REDDOG / Enverus / EnergyLink / PDS)

QRA's metadata-driven **Dynamic Export** produces the revenue-detail and check files (EnergyLink/Enverus, Wells Fargo, PDS/paper). The dominant failure is **"SPE'd: Unable to locate or create DAL"** after an upgrade/hotfix, or an Enverus file that **won't load into EnergyLink** because of a filter-flag or datatype problem. These are **metadata/def** issues, not engine bugs.

| Signature | Root cause | Fix | Case |
|---|---|---|---|
| REDDOG / CHKFLWF **"Unable to locate and create DAL … Could not load file or assembly 'Quorum.Upstream.Shared.DAL'"** after a hotfix | The export def points to a **client `ESUITE_Q*` view** (e.g. `VW_RTRN_CHK_RGSTR_DETAIL`) that isn't a core view, so the core .dll reference is invalid | **Repoint the export def to the CORE view/object** (e.g. `RTRN_CHK_RGSTR_DETAIL` / `REDDOG_RTRN_CHK_RGSTR_DTL`); check the change into the BOM/client metadata layer | 25-01005424 (REDDOG), 25-01010938 (CHKFLWF→`WELLSFARGO` export, QCEN layer) |
| Enverus file **fails to load**: "The pricelessdeduct element is invalid … according to its datatype currency" | XML element was **blank** (`<PriceLessDeduct></PriceLessDeduct>`) and currency can't be blank | Default the blank element to `.00`; log RCA case to stop it recurring | 25-01009521 |
| EnergyLink/Enverus file has **extra rows** that error on load | **Security** (`SEC_USER_ID`) config | Update `SEC_USER_ID` / security config | 24-00990686 |
| Improper **`_DATA_FILTER`** for Enverus DynExp — `QARCH_EXP_DEF_DATA_FILTER.FILTER_VALUES` ≠ `QARCH_EXP_DEF_DATA_UPDATE.UPDATE_VALUES` | Filter/update flag mismatch (e.g. `ExpToPdsFl` / `EXP_TO_PDS_FL`) | Align `FILTER_VALUES` to the export flag; **recurs after every patch/refresh until Hotfix with metadata repo 17.27.2** | 24-00953232, 25-01036296 (REDDOG ran 19+ hrs) |
| Exported check files **cutting off 10-digit zip / MICR line / data** | Export template / column mapping | Template/metadata fix | 24-00986632, 25-01067210 (MICR), 24-00986352 (file not populating) |
| EnergyLink revenue detail **incorrect / duplicate header / picked up wrong company's JIBNET lines** | Export def view scope (BU/company filter) | Correct the export-def view/filter scope | 22-00711092, 22-00520567, 22-00520571 |
| Energylink revenue check detail process **not set up** (`EXPCHKPDS`) | Net-new export config | Stand up the export def/process | 23-00905280, 23-00905050 (Comerica) |
| MUFG dynamic export **Tract Description wrong** | **NULL records** in the TRACT DESCRIPTION column | Modify the export view to give null a value of `""` | 22-00649086 |

**Fix recipe:**
1. Get the **ExpId + AppLayer + DetailSeqNo** from the error (e.g. `ExpId: WELLSFARGO AppLayer: QCEN DetailSeqNo: 2`).
2. "**Unable to locate/create DAL**" → the export def references an object the core .dll can't resolve. Compare the def's view (`VW_*`) against the **core** table/view (`RTRN_CHK_RGSTR_DETAIL`, `REDDOG_RTRN_CHK_RGSTR_DTL`); repoint to core and re-check into the client metadata layer (25-01005424, 25-01010938).
3. **Won't load into EnergyLink** → inspect the failing XML element. Blank where currency required → default `.00` (25-01009521); extra rows → security (`SEC_USER_ID`, 24-00990686); runs forever / wrong rows → `QARCH_EXP_DEF_DATA_FILTER` flag mismatch (24-00953232, 25-01036296) — and warn the client it recurs after each refresh until the metadata-repo hotfix.
4. Wrong fields/nulls/truncation → fix the **export view / template / column mapping** (MUFG nulls 22-00649086; zip/MICR truncation 24-00986632, 25-01067210).
> Many same-symptom cases close as **Customer Error** (wrong file extension `.xls` vs `.txt`, wrong file path, deleted file, ran while all checks Void) — see §17 before assuming a defect.

---

## 7. Cluster D — Bank ACH / NACHA / MUFG / JP Morgan / Comerica file errors

Bank payment files are generated by `CWBANKACH` (→ NACHA) or by bank-specific dynamic exports. The recurring root cause is **metadata applied in a non-client layer that gets overwritten on upgrade**, or **null/format handling in the export view**.

| Signature | Root cause | Fix | Case |
|---|---|---|---|
| Revenue **NACHA** file not printing immediate-destination / immediate-origin / Company ID / routing numbers | A 2022 metadata change was made in a **non-client layer** and was **overwritten by the upgrade** | Re-add the configuration in the **correct client layer**, restart services | 24-00995014 |
| **CWBANKACH** "An Unhandled exception … `QPSCWBANKACHEXPORT failed Execute` … Process will STOP" after a 2024.04 upgrade | Bank-ACH export process-step defect surfaced by upgrade | Bug fix | 24-00972834 / **#1680444** |
| **JP Morgan** detail file errors after CW completes | A **custom DB view** definition (client-specific) | Data script to change the custom view definition | 22-00661285 (BP; also 22-00661286/287/288) |
| **MUFG** export: Tract Description wrong / TRACT # added to Property Name / Check Detail issues | Null columns / property-name composition in the export view | View fix / dynamic-export config | 22-00649086, 22-00655322, 22-00649086 |
| **Footing issue on Bank ACH** / ACH batch incomplete vs check register | Footing/selection in the ACH build | *resolution pattern unclear from mined cases* (Description/Resolution not retained) | 22-00705242, 23-00892363 |
| **Comerica** revenue check file export not set up / wrong scope | Net-new export config / company filter | Stand up / scope the export | 23-00916222, 23-00905050, 22-00660640 (BU filter) |
| New **revenue bank account** not working / routing defaulting to 7777777 | Bank-account master / config not picked up | Config fix | 25-01010801, 25-01023123 |

**Fix recipe:**
1. Identify the bank/export (`CWBANKACH`/NACHA vs WELLSFARGO/MUFG/JPMC/Comerica dynamic export). For **CWBANKACH unhandled exception** post-upgrade → known bug #1680444 (24-00972834).
2. For **missing header/routing/origin fields after an upgrade** → the config was in the wrong (non-client) metadata layer and got overwritten — re-apply in the **client layer** and restart services (24-00995014). This is the canonical bank-file regression.
3. For **wrong/null field values** (MUFG tract, property name) → fix the **export view** (null → `""`, property-name composition) (22-00649086, 22-00655322).
4. Bank-specific custom views (BP/JP Morgan) are fixed with a targeted data script (22-00661285).
> Check §17 first: BA detail edited in BA005 after CW (25-01010549), wrong royalty-payment-type code, etc., produce ACH failures that are **Customer Error**.

---

## 8. Cluster E — CWACHEMAIL / ACH statement email

`CWACHEMAIL` emails ACH/direct-deposit royalty statements. It is fragile under **volume** (spawns many child processes) and **very large individual statements**, and is sensitive to **BA email data**.

| Signature | Root cause | Fix | Case / ADO |
|---|---|---|---|
| CWACHEMAIL **stops processing repeatedly** / runs 23+ hrs | Process generates **too many child processes** | **Software update reduced the number of child processes** | 22-00816019 / **#1532972**; backup-email gap 22-00831120 / **#1559828** |
| CWACHEMAIL **fails** when an owner statement is **very large (>7k lines)** | Big statements choke the email process | **Monthly workaround:** change those owners' **check dates** so they fall out of the ACHEMAIL run, then change back and **send the big checks manually**; ACHEMAIL enhancement not in 2021.10 | 24-00976670, 25-01026799 (same 5–6 owners recurring) |
| Statements **not received** though process "completed successfully" | **BA email addresses with mixed upper/lower case** (or wrong/missing) | Correct the BA emails (BA005); for non-primary contacts, enhancement to allow **multiple ACH primary owner emails** | 25-01053262, 24-00978111 |
| Statement shows **cumulative page numbers / cumulative net** | Custom report (`CWR046`) template defect | Update the custom CWR046 report | 25-01053262 |
| **Overlapping** CWBANKACH + CWACHEMAIL jobs **mix owners' details** into one PDF | Concurrency between the file-creation jobs | Process fix to prevent detail cross-contamination | 22-00566235 |
| ACH email PDF **blank for combined payment types** | Combined-pay-type rendering | Bug fix | (EQC) **#1368267** |
| CWACHEMAIL **collateral after hotfix** — `BA_NM1` invalid, incorrectly exported "PP" checks | Hotfix regression on the email variable/filter | Bug fix | **#1572704** |

**Fix recipe:**
1. **Fails / hangs / runs for hours** → it's the child-process volume issue; confirm the software update (#1532972) is in the build. For a single very large owner statement, use the **check-date workaround** (move the big owners out, run ACHEMAIL, send them manually) — this is the standing monthly recipe at GLE (24-00971007 lineage → 24-00976670, 25-01026799).
2. **"Completed" but owners didn't get statements** → check **BA email addresses** (casing/blank) in BA005 first (25-01053262); for non-primary contacts, the multi-email enhancement (24-00978111).
3. **Wrong content** (cumulative totals/pages, mixed owners) → custom **CWR046** report (25-01053262) or the overlapping-job concurrency fix (22-00566235).

---

## 9. Cluster F — Escheat / NAUPA

Escheat (`CWMNLESCHT`) cuts unclaimed-property checks (often to a state); `CWECHNAUP` / `CWCUESCHT` produce the **NAUPA / HRS** files. Most actionable cases are **config on EC010 / code tables** or a **reporting-method WHERE-clause gap**; a few are core defects.

| Signature | Root cause | Fix | Case / ADO |
|---|---|---|---|
| `CWECHNAUP` (NAUPA Export) "**There are no property records to write to the file**" when **EC010 Reporting Method = N&H (NAUPA & HRS)** | Registered SQL `SQLID_Select_NAUPAHolderData` WHERE clause only matched `ESCHT_RPT_MTHD_CD='NPA'` | **Workaround:** set EC010 Reporting Area to **NPA**; fix = include both `NPA` and `N&H` in the SQL | 22-00669743 |
| **NAUPA report** populates **"Escheet"** as the property number/name; missing holder info | **Missing configs** that print the name/contact of the person running the process | Add the missing configs; supplemental script to **separate companies per NAUPA run** | 23-00931510 |
| Could not cut escheat check to **State of Colorado** during custom CW (nothing picked up in PCW/CW) | Missing escheat config | Add configuration settings (4021/4022 code tables involved) | 22-00854362 |
| **Escheat amounts doubled** on Final vs Edit for BAs with **Unknown/Foreign** addresses | Core escheat doubling defect | Hotfix | 22-00644853 / **#1321337** |
| Escheat fails in TEST though setup looks correct (global config, file paths CT 9173, EC010) | Environment/data | *resolution pattern unclear from mined cases* | 22-00669734 |
| Spring/Yearly Escheat edit **errors for specific states** (CT/NY) | Bad data | Data-correction script | 22-00702583 |
| "Escheat - Pay to current" steps / months-left-behind / "leaves months behind" | Escheat processing-step defects | Bug fixes | 22-00566327 / **#1395676**, **#1456632** (ECA), **#1452347** (DCP) |
| Escheat CW **Out of Memory** (DE/NY) | Volume; subledger 24 never purged | **Run Special JEPURGE on subledger 24** | 25-01006404 |

**Fix recipe:**
1. Confirm the **EC010 Reporting Method**: if it's **N&H** and `CWECHNAUP` says "no property records," that's the known WHERE-clause gap — switch to **NPA** as workaround (22-00669743).
2. Verify escheat config completeness: **EC010**, code tables **4021/4022** (state/escheatable), **9173** (file paths), and the **holder/print-name** configs (missing configs caused "Escheet" placeholders, 23-00931510).
3. **Doubled amounts** for unknown/foreign addresses = core defect (#1321337) — confirm hotfix.
4. **Out of memory** on escheat CW → run **Special JEPURGE on SL 24** (25-01006404) and apply purge recommendations (§13).

---

## 10. Cluster G — OFR & check-detail progressive-rounding / footing errors

A persistent **calculation** cluster: **"Progressive rounding error in transaction sequence …"** on OFR (`CWOWFNDRLS`) and **footing errors** on check detail. Rooted in decimal-interest rounding and in OFR-creation that doesn't sum to 100%.

| Signature | Root cause | Fix | Case / ADO |
|---|---|---|---|
| OFR (`CWOWFNDRLS`) "**PROGRESSIVE ROUNDING ERROR IN TRANSACTION SEQUENCE**" | An automated script created the OFR with **multiple entries that didn't add up to 100%** for specific cases | Correct the OFR entries to sum to 100% | 23-00884851 |
| OFR progressive rounding (EQT DFCT-1063), holds up Checkwrite | Decimal-interest rounding on funds-only transfers | **Workaround:** use **DO130 for funds-only transfers with "transfer all suspense" checked**; clean-up script in PRD; **hotfix** | 22-00644851 / Eng #1318171 |
| OFR "Completed with Errors" progressive rounding on specific trans sequences | Same family — bad/uneven transfer entries | Data clean-up / hotfix | 24-00940369, 23-00884851 |
| Check **footing error** — backup withholding (BUWH) showing multiple times / calculated erroneously on **PPNs** | Tax/withholding double-count in check detail | Footing/withholding fix | 22-00544826 |
| CW_MAIN `TRANS_VAL_AMT` footing — record doesn't equal `TRANS_AMT`, rejected | Child tax/deduct/reimb amounts don't reconcile to the value | Footing detail correction | 23-00881976 |
| OFR errors: "No keyword can be determined for `TRANS_SEQ_NO`" / releasing funds from a **non-paying owner** | User releasing funds for an excluded/non-paying owner | Exclude that owner from the transactions | 25-01037608 (Customer Error) |

**Fix recipe:**
1. **Progressive rounding on OFR**: identify the offending `TRANS_SEQ_NO`(s). If an automated OFR-creation script made entries that don't total 100%, correct/clean them (23-00884851). To **avoid** it going forward, use **DO130 funds-only transfer with "transfer all suspense"** (the documented workaround, 22-00644851) and confirm hotfix #1318171.
2. **Footing errors**: read the "does not foot across" detail — it lists every component (`TRANS_VAL_AMT`, tax NET, deduct/reimb, BUWH, Ad Val, etc.). A common culprit is **backup withholding double-counting on PPNs** (22-00544826). The record is rejected until the components reconcile.
3. These hold up Checkwrite, so they come in **critical/time-sensitive** — a clean-up script unblocks the run; the underlying rounding/footing logic is the long-term fix.

---

## 11. Cluster H — Void / sent-to-bank flag / bank-rec status scripts

A steady, **recurring, low-risk data-script** cluster around the check register (`RTRN_CHK_RGSTR`) and void table (`RONL_VOID_CHK`). These are operational scripts, not code fixes (though a couple have ADO long-term tickets).

| Signature | Root cause | Fix (script) | Case / ADO |
|---|---|---|---|
| **Voided checks not marked Processed** → `CWVDCHK` keeps trying to re-void them and errors ("already Void and cannot be voided again") | Void posted (JEs generated, funds returned) but the job died before setting `PROC_FL` | `UPDATE RONL_VOID_CHK SET PROC_FL='Y' WHERE CHK_RGSTR_SEQ_NO IN (…)` — **recurring, considered low-risk** | 26-01095065, 26-01096507, 23-00932659, 26-01079982/26-01079994 |
| Checks **stuck (OS) in CW005** though **cleared (CL) in QCFS BR005** (or a BR005 **reversal** didn't flip them back to OS) | `CHKREGUPDT` not executed inside the BR005 post/reversal | **Run `CHKREGUPDT`** (QP063 Check Register Update); workaround = script the CW005 status; long-term = add CHKREGUPDT into the BR005 posting process | 25-01020731, 25-01024847 / **#1726731** |
| Need to **re-send paper checks** but the export files are gone while `PMT_SENT_TO_BANK_FL='Y'` | Files deleted/never archived after export, flag still set | Script **`UPDATE RTRN_CHK_RGSTR SET PMT_SENT_TO_BANK_FL='N'`** for the affected `CHK_RGSTR_SEQ_NO` so files regenerate — **recurring at EQT, low-risk** | 25-01010240, 24-00945324, 24-00944730 |
| Large bank file **split** to stay under 999,999 records — flip flags in thirds/halves to export in multiple files | Bank rejects files > 999,999 records (the "8" control record overflows) | Script `PMT_SENT_TO_BANK_FL` in batches to export each chunk; permanent = **Bank Check File Splitter** enhancement | 24-00945324, 24-00170179, 23-00907951 / Eng #1540914 |
| **Update sent-to-bank flag** for a small set of checks | Routine correction | Targeted script | 22-00523688, 22-00523688 |
| Cleared/check-status / cleared-date wrong in CW005 | Status/date data | Script CW005 status / fix maintenance-app data | 23-00883609, 26-01095965 |

**Fix recipe:**
1. **Void re-erroring** → check `RONL_VOID_CHK.PROC_FL` for the `CW_CHK_STAT_CD='VD'` checks (join `RTRN_CHK_RGSTR`); set `PROC_FL='Y'` for the affected `CHK_RGSTR_SEQ_NO` (script in §16). Confirm the JEs already posted before scripting.
2. **CW005 stuck OS vs BR005 CL** → run **`CHKREGUPDT`** first; if it doesn't flip them (e.g. after a BR005 reversal), script the status — this is the documented #1726731 workaround.
3. **Re-send paper checks / split large file** → reset `PMT_SENT_TO_BANK_FL` for the specific `CHK_RGSTR_SEQ_NO` (verify-SELECT first); these EQT scripts are deployed direct to PRD and are well-trodden. The permanent answer to the >999,999 limit is the **Bank Check File Splitter** (#1540914).
4. Always **verify-SELECT in a transaction** before any `UPDATE` to `RTRN_CHK_RGSTR` / `RONL_VOID_CHK`.

---

## 12. Cluster I — Check Input (CI) errors

Check Input (CI screens — CI005/CI012/CI021/CI022/CI031/CI035/CI040, process `CI031`, CDEX) records externally-received checks/details and journalizes them. Cases are mostly **config/template** or **stuck-process**.

| Signature | Root cause | Fix | Case |
|---|---|---|---|
| CI "**Distribution failed for RD Input Group … DOI: …/REV/ALL/1**" on `CI031` / second error after CI022 | Distribution/config for the input group | *resolution pattern unclear from mined cases* (upgrade-UAT, Resolution not retained) | 25-01019144 |
| CI **"Not a valid pressure base, record has been rejected"** (JEPREPARE, `RAJEPFPE29`) for a NM property | Std pressure base missing in code table `GCDE_STD_PRES` | **Add the Std Pres value (e.g. 15.000) to `GCDE_STD_PRES`** | 25-01060580 |
| CI005 suddenly **requires Well Completion** after upgrade | Config **`BOOK_REV_WELL_COMPL`** inadvertently turned on by the upgrade | **Disable `BOOK_REV_WELL_COMPL`** | 24-00970339 |
| **CI021 document attachment** error | Check-number field allows 20 chars but the attachment table only allows 12 | Column-length fix (defect) | 25-01018845 |
| CI031 **process stuck** ("Processing"/PRC in JE100) after a cancel | User cancelled mid-run; status not reset | Clear the stuck process / script the status | 22-00582895, 25-01000681 |
| **CI035** items with no detail / no check number; "Lease Gross Value Unavailable" suspense | Required field not on the CI template (Lease Gross Value), or items to be cleared | Add a **CI012 formula** to back-calculate Lease Gross Value; advise how to clear | 26-01083515, 22-00547014 |
| **Missing required Interest types** in Check Input config | CI config gap | Add the interest types to CI config | 23-00912085 |
| **CDEX** (check-data exchange) not calculating against deck / no data at CI040 | CDEX config / deck mapping | CDEX configuration | 24-00986347, 24-00986349, 24-00973425, 25-01023155 |

**Fix recipe:**
1. **"Not a valid pressure base"** → add the standard pressure base to `GCDE_STD_PRES` for the state (25-01060580). **"Requires Well Completion"** after upgrade → disable `BOOK_REV_WELL_COMPL` (24-00970339) — both are upgrade-flipped configs.
2. **Distribution / interest-type / CDEX** errors → verify the CI **config & template** (required interest types 23-00912085; CDEX deck mapping 24-00986347/349). Lease Gross Value isn't a template field — add a **CI012 formula** to derive it (26-01083515).
3. **Stuck CI031** after a cancel → clear/script the status; advise the user **not to cancel** mid-run (recurring user error, §17).

---

## 13. Cluster J — Performance / timeout / out-of-memory

QRA Checkwrite/OFR/export over large datasets times out or runs out of memory. Mostly **memory/purge config + batch splitting**, with one confirmed OFR child-process defect.

| Signature | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **OFR out of memory** on large batches | OFR is supposed to chunk transactions into child processes but the split logic wasn't firing — it pushes everything at once | **Workaround:** split via QP043 `CWOWFNDRLS` filtered by **"DO Maint Seq No"** (= `TRANS_SEQ_NO` in `RSTG_OWNR_FUND_RLS`); **hotfix** to fix the chunking | 23-00897432 (Upstream Hotfix 10) |
| **Checkwrite out of memory** after 5+ hrs (even with 2 months PPA) | QPEC server under-resourced; purges not run | **Increase QPEC memory to match the other QPEC server**; implement **Special Purge** recommendations | 23-00926418 |
| EnergyLink/REDDOG file **times out / runs 19+ hrs** | Export-def filter not narrowing the data (see §6); also volume | Fix `QARCH_EXP_DEF_DATA_FILTER` flag (§6); purge/batch | 23-00891819, 25-01036296 |
| `QCFSEXPORT` / `CHKFILE` / `EXPCHKPDS` **timeout / not completing / stuck** | Server timeout / volume | QPEC restart; purge; resource | 22-00516801, 22-00704960, 22-00704974, 22-00628665 |
| `PN025` / query screens **lock up** querying data | Query/volume | Perf | 22-00875630 |
| Escheat CW **out of memory** | Subledger 24 never purged | **Special JEPURGE on SL 24** | 25-01006404 |
| General "QPEC restart needed" | Stuck engine | Restart QPEC (often graceful, during business hours) | 25-01053175, 22-00523732, 25-01020296 |

**Fix recipe:**
1. **Out of memory** → (a) confirm **QPEC server memory** parity and (b) implement **purge** recommendations (**Special Purge**, and **Special JEPURGE on the relevant subledger** — e.g. SL 24 for escheat). 23-00926418 and 25-01006404 both resolved this way.
2. **Large OFR** → split via the **DO Maint Seq No** parameter in QP043 (23-00897432) and confirm the chunking hotfix.
3. **Export runs forever** → first fix the **export-def filter** (§6) so it isn't processing all rows, then purge/batch.
4. **Stuck process** → QPEC graceful restart clears most transient hangs (no code).

---

## 14. Cluster K — 1099 export

`CW1099EXPT` builds the annual 1099 file from check-register/distribution data into `RRPT_1099_MISC` / `RSTG_1099_MISC`.

| Signature | Root cause | Fix | Case |
|---|---|---|---|
| `CW1099EXPT` SPE on `SQLID_Insert_Rrpt1099MiscRecs` — "Failed to insert 1099 Misc Records"; **Invalid column name 'BOX5'/'BOX15'/'BOX17'** | `RRPT_1099_MISC` missing the BOX columns | **Take the latest 1099 hotfix** (on 2020.03) | 22-00669836 |
| `RSTG_1099_MISC.OWNR_NET_VAL` has **large negative numbers** (e.g. −$40k where net check was +$13k) | 1099 net-value calculation bug | **Not resolved in product** — client built their own 1099 extract as a workaround | 23-00925324 |
| 1099 updates / new boxes / property-grouping hotfixes | Annual regulatory/format changes | Hotfix | 22-00690481, 22-00704972 |

**Fix recipe:** 1099 issues cluster around **annual schema/format hotfixes** — confirm the client has the latest 1099 hotfix for their release (22-00669836). The negative-net-value defect (23-00925324) had **no product fix** in the mined cases; the client self-extracted — flag for Engineering if it recurs.

---

## 15. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1353354** | Bug / Closed | Ovintiv/ECA — Negative Revenue Check Created During Check Write | §4 | 22-00512952 |
| **#1537586** | Bug / Closed | EQC — Checkwrite issued negative checks and ACH payments | §4 | 22-00823270 |
| **#1636588** | Bug / Closed | CNX,SGY — 2022.04 Checkwrite produced negative check amounts | §4 | 23-00931490 / 23-00934272 |
| **#1658185** | Bug / Closed | CORE_TST_QRA — Checkwrite generated negative checks | §4 | — |
| **#1411454** | Bug / Closed | QRAREV could not post & QRANET posting pending (AR076 non-zero apply) | §5 | 22-00566209 / 21-00214457 |
| **#1628612** | Bug / Closed | MEW 2023.04 — error on OFR process launched from QP043 | §5 | 23-00925668 |
| **#1318171** | Bug / Closed | EQT — CWOWFNDRLS Progressive rounding error in transaction sequence | §10 | 22-00644851 |
| **#1680444** | Bug / Closed | MEW 2024.04 — CWBANKACH Bank ACH File failing with unhandled exception | §7 | 24-00972834 |
| **#1532972** | Bug / Closed | ERF — CWACHEMAIL still running after 23+ hours (child-process reduction) | §8 | 22-00816019 |
| **#1559828** | Bug / Closed | ERF — CWACHEMAIL Backup Email is Missing | §8 | 22-00831120 |
| **#1572704** | Bug / Closed | CWACHEMAIL collateral after hotfix — `BA_NM1` invalid, exported "PP" wrong | §8 | — |
| **#1368267** | Bug / Closed | EQC — ACH Email notification PDF blank for combined payment types | §8 | — |
| **#1321337** | Bug / Closed | Escheat amounts doubling upon run of Final Process (foreign/unknown addr) | §9 | 22-00644853 |
| **#1395676** | Bug / Closed | TGNR-CCI — Escheat pay to current Steps | §9 | 22-00566327 |
| **#1456632** | Bug / Closed | ECA — Current Escheat leaves months behind during processing | §9 | 21-00208127 |
| **#1452347** | Bug / Closed | DCP — Error running Escheat Process 1 in SB | §9 | 22-00256230 |
| **#1726731** | Bug / Closed | SGY/GEC — Checks remain (OS) in CW005 but cleared (CL) in QCFS BR005 | §11 | 25-01020731 / 25-01012665 |
| **#1540914** | Requirement / Closed | EQCU — Add splitter for CKFLQRAPPD (>999,999-record bank file) | §11 | 23-00907951 / 22-00276496 |

> Several actionable cases were dispositioned **operationally** (data script / config / metadata-layer correction) with no single product WI: NACHA client-layer metadata (24-00995014), REDDOG/CHKFLWF export-def → core view (25-01005424, 25-01010938), Enverus `QARCH_EXP_DEF_DATA_FILTER` flag — *recurs each refresh until metadata repo 17.27.2* (24-00953232, 25-01036296), `USE_NETTING_FOR_CHK_MIN_RELEASE` (22-00830939), `BOOK_REV_WELL_COMPL` disable (24-00970339), `GCDE_STD_PRES` add (25-01060580), index rebuild on `JTRN_JE_INPUT_ACCT_ADJ_CTGY` (25-01031507), min-release defect → 2025.04 Sept hotfix (25-01045271). Confirm exact build/patch in the Upstream release notes when stating fix availability.

---

## 16. Diagnostic SQL

> **Caveat:** QRA runs on SQL Server (core `dbo` + client `ESUITE_Q<CLIENT>` / `Q<CLIENT>` layers). Table/column names below are from case repro text and code search; **verify against the client schema first**, and always run a verify-SELECT before any UPDATE, wrapped in a transaction.

```sql
-- A. The check register for a BU / check date (status, sent-to-bank, void) — §4/§11
SELECT CHK_RGSTR_SEQ_NO, CHK_NO, BA_NO, CHK_AMT, CW_CHK_STAT_CD,        -- OS / CL / VD
       PMT_SENT_TO_BANK_FL, RYL_PMT_TYPE_CD, CHK_DT, UPDT_DT
FROM   RTRN_CHK_RGSTR
WHERE  OPER_BUS_SEG_CD = '<SEG>' AND BUS_UNIT_CD = <BU> AND CHK_DT = '<MM/DD/YYYY>'
ORDER BY CHK_AMT;                                                       -- negatives sort first (§4)

-- B. Voided checks not marked processed (the §11 PROC_FL pattern)
SELECT CW.CHK_RGSTR_SEQ_NO, CW.CHK_NO, CW.CW_CHK_STAT_CD, VID.PROC_FL
FROM   RTRN_CHK_RGSTR CW
JOIN   RONL_VOID_CHK  VID ON CW.CHK_RGSTR_SEQ_NO = VID.CHK_RGSTR_SEQ_NO
WHERE  CW.CW_CHK_STAT_CD = 'VD' AND VID.PROC_FL = 'N';
-- Fix (after confirming JEs posted): UPDATE RONL_VOID_CHK SET PROC_FL='Y', UPDT_USER='Q_SCRIPT', UPDT_DT=dbo.FN_QGETDATE(GETDATE()) WHERE CHK_RGSTR_SEQ_NO IN (…);

-- C. Re-send paper checks / split a large bank file (reset sent-to-bank flag) — §11
-- Verify-SELECT, then: UPDATE RTRN_CHK_RGSTR SET PMT_SENT_TO_BANK_FL='N' WHERE CHK_RGSTR_SEQ_NO IN (…);
-- File totals for a bank control (EQT pattern, 23-00907951):
SELECT UPDT_DT, SUM(CHK_AMT) Total_Checks_Amount, COUNT(CHK_NO) Number_of_Checks
FROM   RTRN_CHK_RGSTR
WHERE  OPER_BUS_SEG_CD='<SEG>' AND BUS_UNIT_CD=<BU> AND CHK_DT='<DT>'
  AND  RYL_PMT_TYPE_CD='PP' AND PMT_SENT_TO_BANK_FL='Y' AND CHK_AMT<>0 AND CW_CHK_STAT_CD<>'VD'
GROUP BY UPDT_DT;

-- D. Owner under minimum / not getting a check (PCW staging) — §4
SELECT * FROM RSTG_PCW_MIN_AMT_OWNR WHERE ACCT_NO LIKE '<OWNER>%';

-- E. Dynamic-export def filter mismatch (the §6 REDDOG/Enverus recurring fix)
SELECT EXP_ID, FILTER_NAME, FILTER_VALUES FROM QARCH_EXP_DEF_DATA_FILTER WHERE EXP_ID = '<ENVERUS|CEN_REDDOG|…>';
SELECT EXP_ID, UPDATE_NAME, UPDATE_VALUES FROM QARCH_EXP_DEF_DATA_UPDATE WHERE EXP_ID = '<…>';
-- FILTER_VALUES (e.g. ExpToPdsFl) must match the export flag; align after each refresh until the metadata-repo hotfix.
SELECT * FROM QARCH_EXP_DEF_DATA_HRCHY WHERE EXP_ID = '<PDS_ENC|WELLSFARGO|…>';

-- F. Escheat reporting method on EC010 (the §9 N&H vs NPA gap)
--    If CWECHNAUP says "no property records" with N&H, set the reporting area to NPA (or take the SQL fix).
--    EC010 / code tables 4021,4022 (state/escheatable), 9173 (file paths).

-- G. CI pressure base / well-completion config (§12)
SELECT * FROM GCDE_STD_PRES;                            -- add STD_PRES for the state (25-01060580)
-- BOOK_REV_WELL_COMPL config flipped on by upgrade (24-00970339) — disable in global config.

-- H. 1099 staging net value sanity (§14)
SELECT ACCT_NO, FORM_TYPE, OWNR_NET_VAL FROM RSTG_1099_MISC WHERE ACCT_NO LIKE '<OWNER>%';

-- I. Find the failing process step + error by Process Queue ID
--    Get PQID from the user (e.g. 9012260), then read the batch message/log for that PQID + step
--    (export the CW_MAIN error grid; look for: footing, index duplicate-group, primary-key, DAL-not-found).
```

---

## 17. Expected-Behavior / User-Education FAQ

~111 Training + ~260 Customer-Error cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| "**Checkwrite failed / completed with errors**" / "URGENT check write error" | **Ran CW without posting PCW.** Post the PCW entry in **JE100** (select PCW from the drop-down), then **rerun CW from QP043** (rerunning from JE100 alone often doesn't work). The most common QRA case, full stop. | 25-01013247, 26-01088160, 26-01095312, 25-01000670 |
| "**Checkwrite won't let me clean/rerun**" / "CW_MAIN error" after I released a lock | The user **manually released `CW_JELK`** (or deleted the PCW lock). **Never release CW_JELK manually** — the system clears it when CW completes. Re-insert the lock via script. | 25-01037294, 25-01044714, 25-01035714 |
| "**Negative / odd check**" — owner has a balance but check is negative or $0 | **QRA does not cut negative checks by design.** After JIB netting zeroes the WI check, the owner's OR-interest **debit** can drop the net negative; deficits/PPAs/reversals do too. Verify the inputs — if correct, it's expected (verify upstream distribution/suspense). | 25-01032653, 24-00965101 (config side §4) |
| "**Owner not getting a check**" | Check **Stop-Pay date**, **owner suspense**, and **minimum release** (owner/company minimum, JIB netting). Often a setup choice, not a bug — but confirm vs the known min-release defect (§4). | 26-01066388, 24-00957488 |
| "Generate Check File **failed**" / "file incomplete" / "Enverus file error" | **User-driven export mistakes:** wrong file **extension** (`.xls` vs `.txt`), wrong/old **file path**, **deleted** the file, ran while **all checks are Void**, or didn't add the `.XLS` parameter. Reset the export flag (`EXP_TO_PDS_FL`/`PMT_SENT_TO_BANK_FL`) and rerun. | 25-01026734, 25-01006422/308, 25-00999630, 25-01048905, 25-01056517 |
| "**Process stuck in Processing**" after I cancelled it | **Cancelling mid-run** leaves JE100 in PRC. Don't cancel — call Quorum. Resolution is a script to reset the status/locks (CI031, EXPOI, TAXPOST/JEPOST). | 22-00582895, 25-01025460, 25-01004537, 25-01000681 |
| "Accidentally **voided a check** that already cleared the bank" | Voiding returns funds to payable/suspense. If it already cleared, process a **manual JE** to offset the void; don't reissue blindly. | 25-01002910, 25-01029293 |
| "**QRA data not flowing to GL**" / "Error posting MJE" / "JE100 not showing my transaction" | Run **`QCFSIMPCYC`** (QCFS Import Cycle) for the GL flow; **Checkwrite must complete before any JE/MJE posts.** | 26-01099179, 26-01096415, 25-01047697 |
| "Where does TIPS/QRA look for **withholding / federal entity / NM-TX withholding**?" | Config questions — **CW010** (state withholding), code tables **4018** (excluded owners, per-state), BA entity type. Usually the client configured the wrong state/owner set. | 25-01028464, 25-01029516 |
| "How do I **release minimum suspense / reverse a CI suspense line / net JIB AR vs WI revenue**?" | Training — walk through suspense release, CI reversal, and JIB netting (`JIB_NETTING_PROPERTY_LOOKUP` / `GCDE_DFLT_PROP_JIB` to book at a default property). | 26-01100673, 25-01047180, 26-01079994, 25-01004108 |
| "**JER055 / Pre-Check Write report doesn't total**" / "JE Build — no JE100 generated" | Report/process education — explain how the pre-CW report pulls owner payables from the subledger and how JE Reconciliation generates JE100. | 25-01046038, 25-01054786 |
| "Need **QPEC restart**" / "Quorum System Manager not working" | Operational — restart QPEC services (often graceful, during business hours). Not a code fix. | 25-01020296, 25-01025336 |

**Tell-tale it's user/expected:** a Checkwrite that failed because **PCW wasn't posted**; a **manually-released CW_JELK**; a **negative/zero** check that correctly follows netting + reversals + deficits; an export that failed on a **wrong file extension/path or deleted file**; a process **stuck after a user cancel**; or a **"how does it work" / withholding-config** question. Confirm PCW-posted, the lock, the upstream amount, and the export parameters **before** treating it as a defect.

---

## 18. Key Code, Processes & Repos

### Processes / batch IDs
| Process ID | Purpose | Notes |
|---|---|---|
| **CWPREPOST / PCW** | Pre-Checkwrite — payees, minimum release, JIB netting | Must be **posted in JE100** before CW; staging `RSTG_PCW_*` |
| **CW_MAIN** | Checkwrite — cut checks/ACH | Multi-step; writes `RTRN_CHK_RGSTR`; lock `CW_JELK` |
| **CWOWFNDRLS** | Owner Funds Release (OFR) | Screen DO130; `RSTG_OWNR_FUND_RLS`; progressive-rounding & OOM hot spots (§10/§13) |
| **CWMNLESCHT / CWECHNAUP / CWCUESCHT** | Escheat checks + NAUPA/HRS export | Config EC010, code tables 4021/4022/9173 (§9) |
| **CWBANKACH** | Bank ACH (NACHA) file | Class `QPSCWBANKACHEXPORT`; ADO #1680444 (§7) |
| **CHKFLWF / REDDOG / CHKFLREDOG / CHKRDGSPLT / ENVCHKEXP / EXPCHKPDS** | Dynamic exports — Wells Fargo, EnergyLink/Enverus, PDS | Defs in `QARCH_EXP_DEF_*`; "DAL not found" / filter-flag issues (§6) |
| **CKFLQRAPPD / EQCHUNKATE / CHKFILE** | Paper check / PDS export & chunking | Bank-file splitter #1540914 (§11/§13) |
| **CWACHEMAIL** | ACH statement emails | Child-process volume & big-statement limits (§8) |
| **CW1099EXPT** | 1099 export | `RRPT_1099_MISC` / `RSTG_1099_MISC` (§14) |
| **CWVDCHK** | Void check process | `RONL_VOID_CHK.PROC_FL` (§11) |
| **CHKREGUPDT** | Check Register Update (QP063 Upstream Shared) | Flips CW005 status from QCFS bank-rec; #1726731 (§11) |
| **QCFSEXPORT / QCFSIMPCYC** | QRA ↔ QCFS handoff to GL | CW must complete first (§17) |

### Code locations (confirmed via ADO code search)
| Symbol / area | Repo / path | Cluster |
|---|---|---|
| `QPSCWBankACHExport` (.cpp/.h) — `QPSCWBANKACHEXPORT` step | `Quorum.Upstream.QRA.ClassicBatch /QPDllRevenueAcctgCW/` | §7 Bank ACH |
| Checkwrite / OFR / escheat batch steps | `Quorum.Upstream.QRA.ClassicBatch /QPDllRevenueAcctgCW/` | §4/§5/§9/§10 |
| `QFrmOwnerFundsRelease.cs`, `QFrmDOIMaintApprovalOwnerFunds.cs` (OFR / DO130) | `Quorum.Upstream.QRA.ClassicGUI /Quorum.Upstream.QRA.DO/` | §10 OFR |
| `QDOConstants.cs` and DO/QDO shared logic | `Quorum.Upstream.Shared.Web /…CoreInterface/QDO/` | §4/§10 |
| Dynamic-export process-step metadata | `QARCH_CTRL_PROCESS_STEP.json` etc. in `<CLIENT>.Upstream.Metadata` (+ `SUM.Upstream.Metadata` standard) | §6/§7 |

### Repos
- **`Quorum.Upstream.QRA.ClassicBatch`** — C++ batch: Checkwrite, PCW, OFR, escheat, bank-ACH/dynamic export (`QPDllRevenueAcctgCW`).
- **`Quorum.Upstream.QRA.ClassicGUI`** — desktop screens (DO/OFR, CI, CW005/020/035).
- **`Quorum.Upstream.Shared.Web` / `.Shared.*`** — shared QDO/core-interface, web screens.
- **`<CLIENT>.Upstream.Metadata`** (EQC/QCEN, CNX, MEW, GLE, SPR, ENC, etc.) and **standard `SUM.Upstream.Metadata`** — dynamic-export defs, code tables, process steps. **Most "broke after upgrade/hotfix" cases are a metadata-layer problem here** (config landed in a non-client layer and was overwritten) — always check the **client layer** first.

---

## 19. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- **CW cuts a negative/zero check** with clean netting/min-release config and no reversal behind it (#1353354 / #1537586 / #1636588 / #1658185), or an **owner over minimum isn't paid** with clean config (22-00560559; 25-01045271 → 2025.04 Sept hotfix).
- A **calculation** is provably wrong: **OFR progressive rounding** (#1318171), check **footing** (BUWH double-count, 22-00544826 / 23-00881976), **escheat doubling** for foreign/unknown addresses (#1321337), **1099 net value** (23-00925324, no product fix yet).
- A **process step crashes from code**, not data/config: `CWBANKACH` unhandled exception (#1680444), OFR launcher (#1628612), CWACHEMAIL child-process blow-up (#1532972), CI attachment column length (25-01018845), CW005-vs-BR005 status not updating on reversal (#1726731).
- Provide: **PQID + failing step + exact error**, client + BU + check date + accounting month, the BA/owner, and a repro. Confirm fix availability in the Upstream release notes and the linked WI's target build.

**Handle as Configuration / Cloud Ops when:**
- **Netting / min-release**: `USE_NETTING_FOR_CHK_MIN_RELEASE`, owner/company minimums, `JIB_NETTING_PROPERTY_LOOKUP` / `GCDE_DFLT_PROP_JIB` (22-00830939, 25-01004108).
- **Dynamic-export defs**: repoint to the **core view** (REDDOG/CHKFLWF, 25-01005424 / 25-01010938), align **`QARCH_EXP_DEF_DATA_FILTER`** flags (24-00953232, 25-01036296 — recurs each refresh until metadata-repo hotfix), null-handle the export view (MUFG 22-00649086), re-apply **bank-file metadata in the client layer** (NACHA 24-00995014).
- **Code-table / global config flipped by an upgrade**: `BOOK_REV_WELL_COMPL` (24-00970339), `GCDE_STD_PRES` (25-01060580), escheat **EC010 / 4021 / 4022 / 9173** (22-00854362, 22-00669743), withholding **CW010 / 4018** (25-01028464).
- **Client-clone / schema drift & index health**: rebuild `JTRN_JE_INPUT_ACCT_ADJ_CTGY` index (25-01031507); clean stale `RSTG_*` staging/archive (24-00945978).

**Handle as recurring low-risk data script (Cloud Ops):**
- Void `PROC_FL='Y'` in `RONL_VOID_CHK` (26-01095065 family); reset `PMT_SENT_TO_BANK_FL` to re-send/split paper checks (25-01010240, 24-00945324 — EQT runs these straight to PRD); CW005 status after BR005 (#1726731). **Always verify-SELECT in a transaction first.**

**Performance first (no code):** increase **QPEC memory** and apply **Special Purge / Special JEPURGE** (23-00926418, 25-01006404); split large **OFR** via the DO-Maint-Seq-No parameter (23-00897432); QPEC graceful restart for stuck processes.

**Handle as Training / Expected behavior (no fix):** see §17 — **PCW not posted before CW** (the #1 case), **manually-released CW_JELK**, negative/zero checks that correctly follow netting+reversals, export failures from wrong extension/path/deleted file, processes stuck after a user cancel, and "how does it work / withholding-config" questions. Confirm PCW-posted, the lock, the upstream amount, and the export parameters before escalating.

---

*Skill created: 2026-06-14.*
*Based on: 1,743 closed QRA Check-Processing SF cases (Check Write 1,510 + Check Input 226 + Check Interfaces 7) — 268 actionable (Software Defect 157 + Application Configuration 101 + ChangeConfig 10) mined for fix recipes, plus ~60 Training/Customer-Error cases for the FAQ. ADO work items #1353354, #1537586, #1636588, #1658185, #1411454, #1628612, #1318171, #1680444, #1532972, #1559828, #1572704, #1368267, #1321337, #1395676, #1456632, #1452347, #1726731, #1540914.*
*Companion: upstream revenue-distribution, JIB-to-revenue/QCFS, and master-data skills; REPO_REFERENCE.*
