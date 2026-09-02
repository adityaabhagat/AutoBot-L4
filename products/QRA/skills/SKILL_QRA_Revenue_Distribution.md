# SKILL: QRA Revenue Distribution Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QRA (My Quorum Revenue Accounting — upstream oil-&-gas revenue accounting, myQuorum / On Demand)
**Scope:** The revenue-to-payment pipeline — **Valuation** (VL025/VL031/VL032/VL040/VL100, VLCALC/VLPROC, VLMIUPLOAD), **Contractual Allocation** (CA005/CA010/CA020, flow grids, marketing groups), **Direct Revenue Input / DRI** (VL025 links, VL031/VL032 entry, PPNs, SOD), **Revenue Distribution** (BKRVNU, RDCALCNEW/RDPROCNEW, impairments, RD031), **Check Write / payments** (PCW/CW, QP043, Enverus/EnergyLink, ACH, voids, 1099, escheat), **Owner Funds Release (OFR)**, **JE/journal interface** (JE020/JE100/JE101, QCFSEXPORT to QCFS), and **severance/production tax** (TS/TX screens).
**Companion areas:** Division-order setup (DO005/DO020/DO129/DO130, DOI transfers, maintenance groups) lives mostly in QDO; financial-settlement export/GL is QCFS. This skill *consumes* allocated/valued volumes and DOI decimals and *produces* distributed revenue, journal entries, and owner checks — when the **distributed number itself is wrong, suspect upstream Valuation/CA/DOI setup first** (it is usually the messenger).

> **Evidence base:** 1,170 closed QRA cases in categories Revenue Distribution (835), Direct Revenue Input (241), Contractual Allocation (94). Root-cause split: Customer Error 207, (blank) 196, **Software Defect 132**, Customer Cancelled 109, Training 92, **Application Configuration 63**, Performance 49, Business Change 48, others. This skill mines the **199 actionable** cases (Software Defect 132 + Application Configuration 63 + ChangeConfig 4) for fix recipes, plus ~40 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining. Where a cluster's resolution could not be confirmed from mined text it is marked "resolution pattern unclear."

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — VL100 / BKRVNU revenue-distribution process failures (HIGH FREQUENCY)](#4-cluster-a--vl100--bkrvnu-revenue-distribution-process-failures)
5. [Cluster B — RDCALCNEW locking / ROLLBACK TRANSACTION / orphaned locks](#5-cluster-b--rdcalcnew-locking--rollback-transaction--orphaned-locks)
6. [Cluster C — Contractual Allocation (CA) flow-grid failures](#6-cluster-c--contractual-allocation-ca-flow-grid-failures)
7. [Cluster D — SOD owner pay (double-pay / not distributing)](#7-cluster-d--sod-owner-pay)
8. [Cluster E — Market Group / Maintenance Group / impairment 302](#8-cluster-e--market-group--maintenance-group--impairment-302)
9. [Cluster F — DRI entry & link maintenance (VL025/VL031/VL032/VL040, double-booking, reversals)](#9-cluster-f--dri-entry--link-maintenance)
10. [Cluster G — Check Write / PCW / Enverus & EnergyLink / netting / voids / 1099](#10-cluster-g--check-write--pcw--enverus--energylink--netting--voids--1099)
11. [Cluster H — QRA→QCFS / QRAEXPORT (JIB netting major-product mismatch)](#11-cluster-h--qraqcfs--qraexport)
12. [Cluster I — Severance / production tax](#12-cluster-i--severance--production-tax)
13. [Cluster J — Owner Funds Release (OFR)](#13-cluster-j--owner-funds-release-ofr)
14. [Known ADO Items](#14-known-ado-items)
15. [Diagnostic SQL](#15-diagnostic-sql)
16. [Expected-Behavior / User-Education FAQ](#16-expected-behavior--user-education-faq)
17. [Key Code, Processes & Repos](#17-key-code-processes--repos)
18. [Escalation Guidance](#18-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| VL100 stops with `Impairment Reason Code 302/314`, `RD Record Impaired in JE`, `Progressive Rounding Error during GMI Tract Decimal` | Distribution rounding / market-group / impairment-setup issue; often a deleted/incomplete **Market Group** or DOI decimal | PQID + the exact RD-level impairment code; §4/§8 |
| `ROLLBACK TRANSACTION request has no corresponding BEGIN TRANSACTION` / `Distribution failed for RD Input Group …` at VL100 Full Submit | **RDCALCNEW DB locking** under concurrent/large runs | §5 — short-term: set ENV config `WRITE_TO_DB_ONLY_AT_END = 1` + QPEC restart |
| Process "hung", won't start, "please release lock", builds up on QP110 | **Orphaned RD/VL locks** (`RD_DO_LK`/`VL_DO_LK`) not released after a failed run | §5 — UNDOPROC/clean now releases locks; manually clear `QARCH_LOCK` |
| CA020 fails: `Failed to insert new records into PTRN_CA_VOL`, `CA did not successfully allocate CA Equity Volumes`, `CA Rules have not been entered` | **CA rules / flow-grid / time-slice** setup; DOI Change Warning flags; missing RC010/RC040 effective dates | §6 — CA005/CA010/RC010, DOI-change-warning flags, time-slice end-dates |
| SOD owners **paid on both SOD and Standard contracts**, or SOD value wrong / not distributing | SOD logic defect (zero volume on fuel meter trigger) **or** missing SOD Masterlink (ML005/ML006) | §7 — verify SOD Masterlink setup first; known defect when 0 vol on fuel meter |
| 31 properties' **market groups deleted/missing** after a DO transfer / maintenance group | GRPREFWEB unique-key error left MG tables empty, then COPY_DVD copied empties | §8 — re-create from UAT; root cause is failed GRPREFWEB |
| DRI **double-booking**; reversal "reverses but won't rebook"; PPNs duplicating | DRI/PPN reversal-rebook defect; duplicate meters in flow grid | §9 |
| Check Write errors on some owners not others; `RTRN_CHK_RGSTR.ALT_ST_CD` length | **State/country code too long** for the check-register column (e.g. NZ-WGN); split-insert verification fails | §10 — JE101 query by owner state; exclude offending owner or fix BA address |
| CW "connection error" during PCW/CW; PCW won't lock | App/DB-tier connectivity; stale Citrix/MT session | §10 — restart MT server / verify DB server; re-open session |
| QRAEXPORT / QCFSEXPORT fails for **JIB-netted properties** ("wrong major product code", "5/1 not in effective range") | JIB-netted PAR records use **DO major product code** instead of an ALL DOI | §11 — script to correct major product; long-term WI |
| Severance tax rejected (`Tax Type SV … Adjustment Category Code Not Found`) | Missing **adjustment categories** on TX006 for the state/tax type | §12 — add OA/ON/LV/GT (etc.) to TX006 |
| Tax doubled/tripled on units/tracts; tax-free portion math wrong; negative WV sev | Tax-calc defects (VLA duplication, exempt-adjustment SQL, no zero-floor) | §12 |
| OFR completes with errors / posting routes to **Account Group 80** with no GL account | JIB-owner-suspense routing needs a GL account mapped | §13 — map GL for Acct Group 80 in JE020 |
| "Turn on auto-post for owner funds release" | Config toggle `AUTO_POST_OFR` | §13 |

---

## 2. Pipeline & Concepts

```
[Volumes/Allocation: VA005/VA015/VA030/VA035]  +  [DOI decimals: DO005/DO016, market groups MG004/MG006]  +  [Contracts/Rates: RC010/RC036/RC040]
      │
      ▼  CONTRACTUAL ALLOCATION (CA005/CA010 rules → CA020 run: CACALCSPLT → CACTRALLOC → CAGMIOVRD)   [PTRN_CA_VOL / PTRN_CA_VOL_ACT]
      │
      ▼  VALUATION (VL025 DRI links, VL031/VL032 input, VL040 flow-grid PPNs, VL100 = the master "process revenue")
      │     steps: VLRUNVLCAL → VLCALC (VLPROC) → RDSELECT → RDCALCNEW/RDPROCNEW → JEPRECOMBO → RDIMPAIRJE
      │     [RD results: RD031 (ACT_BAL_DEC vs OWNR_NRI_DEC); impairment reason codes 302/314/…]
      │
      ├──► JOURNAL / GL  (JE020 account mapping, JE100/JE101 entries, MJE; QCFSEXPORT → QCFS → SAP/GL)
      ├──► CHECK WRITE   (PCW pre-check → CW; QP043 Generate Enverus Check File; ENVCHKEXP/EnergyLink; ACH; 1099; escheat)
      └──► OWNER FUNDS RELEASE (DO129/DO130, OFR staging → JE100; AUTO_POST_OFR)
```

### Key terms (Quorum/QRA vocabulary)
- **VL100** = the master "process revenue" job a revenue accountant runs each close. Internally it chains **VLCALC** (valuation), **RDSELECT** (pick RD input), **RDCALCNEW/RDPROCNEW** (distribution calc), **JEPRECOMBO** (journal prep), **RDIMPAIRJE** (impair). If any step fails the whole run stops; get the **Process Queue ID (PQID)** + the failing step.
- **BKRVNU** = "Book Revenue" — the segregated/batch engine behind VL100 distribution (`Quorum.QRA.Process.QPDllBookRev`). Most "VL100 erroring/hung/slow/memory" cases reference BKRVNU.
- **RDCALCNEW / RDPROCNEW** = the new revenue-distribution calculation step inside BKRVNU. Source of the **ROLLBACK TRANSACTION / DB-locking** family (§5).
- **CA (Contractual Allocation)** = allocates pipeline-statement (VA) volumes to contracts on a **flow grid** before valuation. CA020 runs `CACALCSPLT → CACTRALLOC → CAGMIOVRD`; results land in **`PTRN_CA_VOL` / `PTRN_CA_VOL_ACT`**. Driven by **CA rules** (CA005/CA010), measurement points (MP), and **RC010/RC040** contract connections.
- **DRI (Direct Revenue Input)** = manually-entered/imported revenue (not from CA). **VL025** = DRI Link Maintenance; **VL031** = DRI value/volume; **VL032** = manual input (`RSTG_MANL_INPUT`), loaded by **VLMIUPLOAD**; **VL040** = flow-grid PPN processing.
- **PPN** = Prior Period Notification / adjustment (the QRA prior-period-adjustment mechanism). PPAs reprocess closed months; generate RV20/RV36/RV56 records.
- **SOD** = Split Of Detail (a.k.a. SOD owner / SOD contract) — an owner paid under a separate SOD sales contract/price. Tied via **SOD Masterlink** (ML005/ML006). Recurring defect: SOD owner paid on *both* SOD and Standard contract (§7).
- **Market Group (MG) / Marketing Group / MEG** = groups owners for marketing/GMI (Gas Marketing Imbalance) make-up calcs. Screens MG004/MG006; types VLA & CIA. Missing/deleted MGs → impairment 302 (§8).
- **Impairment reason codes** = why an RD record was rejected/held: **302** (commonly market-group/owner-not-tracking), **314** (tax-free add-back / master-data size), 401/416, etc. The number keys the cause.
- **RD031** = the RD detail tab; **ACT_BAL_DEC** (balancing decimal) vs **OWNR_NRI_DEC** (NRI). A mismatch/"balancing decimal reset to NRI" warning is an SOD/decimal symptom.
- **Check Write**: **PCW** (Pre-Check Write, locks & journalizes) then **CW** (cuts checks). **QP043** = Generate Enverus Check File (`ENVCHKEXP`) → EnergyLink. Inclusion/exclusion driven by tables **4021** (include), **4022** ("process all owners"), **4048** (exclude). Check register = `RTRN_CHK_RGSTR`.
- **QCFSEXPORT** = "Export GL and LOS data to QCFS" — pushes GL/LOS to **QCFS** (financial settlement) → SAP. JIB-netting major-product mismatch is the recurring failure (§11).
- **JIB Netting** = netting JIB (joint-interest-billing) expenses against an owner's revenue. RI owners must be enabled in `GCDE_INT_TYPE`; netted suspense routes to Account Group 80.
- **OFR (Owner Funds Release)** = releasing suspended owner funds (DO129/DO130). `AUTO_POST_OFR` auto-posts.
- **QPEC** = the upstream application/process engine (`*.Upstream.Application.QPEC`). A **QPEC restart** realizes config changes and clears stuck sessions.

---

## 3. Decision Tree

```
QRA Revenue Distribution / DRI / Contractual Allocation case
│
├─ A batch process/step FAILED? (VL100/BKRVNU, CA020, QCFSEXPORT, CW)  →  GET PQID + STEP NAME + EXACT ERROR/IMPAIRMENT CODE
│   ├─ "ROLLBACK TRANSACTION has no corresponding BEGIN" / Distribution failed for RD Input Group → §5 (RDCALCNEW lock; WRITE_TO_DB_ONLY_AT_END=1 + QPEC restart)
│   ├─ "please release lock" / hung on QP110 / orphaned RD_DO_LK,VL_DO_LK             → §5 (UNDOPROC/clean releases locks; clear QARCH_LOCK)
│   ├─ Impairment 302 / "RD impaired in JE" / "Progressive Rounding GMI Tract Decimal"→ §8/§4 (market group / DOI decimal; often deleted MG)
│   ├─ Impairment 314                                                                 → §4 (tax-free add-back master-data size; metadata)
│   ├─ CA020: PTRN_CA_VOL insert fail / "no CA results" / "CA Rules not entered"      → §6 (CA rules / time-slice / DOI-change-warning flags)
│   ├─ Tax rejected "Tax Type SV … Adjustment Category Code Not Found"                → §12 (add categories to TX006)
│   └─ QCFSEXPORT/QRAEXPORT for JIB-netted props ("wrong major product"/"eff range")  → §11
│
├─ Output WRONG (process didn't crash)?
│   ├─ SOD owner double-paid or not distributing                                       → §7 (SOD Masterlink ML005/006; 0-vol-on-fuel-meter defect)
│   ├─ DRI double-booking / reversal won't rebook / duplicate PPN/RV56                  → §9
│   ├─ Tax doubled on units-tracts / tax-free portion wrong / negative sev             → §12
│   ├─ Checks netted/voided wrong / negative checks for netted WI+NWI owners           → §10
│   └─ Market groups missing after a DO transfer/maintenance group                      → §8
│
├─ Check Write / payment file?
│   ├─ CW errors some owners, RTRN_CHK_RGSTR column length (state code)                 → §10 (JE101 query; exclude/fix BA address)
│   ├─ "connection error" during PCW/CW; PCW won't lock                                 → §10 (restart MT/DB server; re-open session)
│   └─ EnergyLink/Enverus file incomplete / doesn't tie to check (netting)              → §10/§11
│
├─ Owner Funds Release?  → §13 (Acct Group 80 GL mapping; AUTO_POST_OFR; inactive-property limits)
│
├─ QPEC down / config change not realized / app endpoint errors                         → restart QPEC (§5/§17); often stale session (FAQ §16)
│
└─ Vague "error", "how do I", audit, "wrong number that ties to setup"                   → §16 Expected-Behavior FAQ (Customer Error / Training) — verify DOI/MG/contract setup & upstream allocation first
```

---

## 4. Cluster A — VL100 / BKRVNU revenue-distribution process failures

**The single largest actionable signature.** A revenue accountant runs **VL100 (Full Revenue Submit)** and it stops at an internal step (`VLCALC` → `RDSELECT` → `RDCALCNEW` → `JEPRECOMBO` → `RDIMPAIRJE`). Preliminary Submit often succeeds while **Full** fails. Always capture the **PQID** and read the cascade of `PROCESS_LOG` rows — the *first* ERROR (lowest step) is the real one; everything above it is "Won't execute … prior step failed."

**Representative cascade (23-00929043, Sherrod Unit PPA):**
```
ERROR Progressive Rounding Error occurred during GMI Tract Decimal calculation   <- ROOT
ERROR Continue Process On Failed Execute Is FALSE for VLCALC … Process will STOP
ERROR … RDSELECT … RDIMPAIRJE … (cascade)
```

**Impairment reason codes (the number is the diagnosis):**
- **302** — owner not tracking in a market group / missing or deleted market group / DOI ownership-record (DI) mismatch. *Fix:* update the **Market Rep / Interest Type** so it matches the DOI; re-create the MG (§8). Cases 24-00960682, 25-01048691, 24-00982421.
- **314** — tax-free add-back master-data cross-reference too large. *Fix:* patch built a **temp table for the tax-free add-back setup** to collapse the cross-reference size; the metadata (batch error messages) is optional (22-00659988).
- **610/615 SV "Adjustment Category Code Not Found"** — missing TX006 adjustment categories → §12.
- **209** — VL expecting price terms in RC036 (new "Valid Products" RD=Y flag) → add price term (FAQ, 25-01042767).

**Memory / size failures:**
- **`BKRVNU - Memory Exception`** on very large DOIs (e.g. a waterflood unit, ~2K owners) — see §5; the structural fix is the same `WRITE_TO_DB_ONLY_AT_END` config + processing approach (24-00943638, 25-01043414).
- **`Sequence Contains More Than One Matching Element`** in BKRVNU — data/config returning >1 row where one expected (24-00983823).

**Fix recipe:**
1. Get **PQID + failing step + first ERROR line + impairment code**.
2. Map the impairment code (302→market group, 314→tax-free, SV→TX006). For 302, check **MG004/MG006 Market Rep + Interest Type vs DO005/DO016** for the owner.
3. If Preliminary passes but Full fails, suspect distribution-stage data (decimals, market groups), not valuation.
4. If "ROLLBACK TRANSACTION" or a hang appears → §5 (locking), not a data problem.
5. Many one-off VL100 errors are **customer setup** (missing DOI/volume/contract) — see §16 before escalating.

---

## 5. Cluster B — RDCALCNEW locking / ROLLBACK TRANSACTION / orphaned locks

A distinct, well-understood **DB-contention** family in the distribution step. Two faces:

**(1) ROLLBACK TRANSACTION / RDCALCNEW locking (large or concurrent runs):**
- **Symptom (25-01034392):** VL100 Full Submit fails with `The ROLLBACK TRANSACTION request has no corresponding BEGIN TRANSACTION.` + `Distribution failed for RD Input Group <n>, DOI: …` (two lines per well). Preliminary completed; Full fails.
- **Short-term fix (confirmed):** add an **ENV-layer global setting `WRITE_TO_DB_ONLY_AT_END = 1`** (config `QARCH_CNFG_CTRL`), then **restart QPECs** so it takes effect (25-01034392, 25-01043414). This batches all DB writes to the end of the run, avoiding the mid-run lock/rollback.
- **Long-term:** code fix tracked under **25-01046201** (and the large-DOI memory-exception path 25-01043414 / 25-01036404, Elk City waterflood unit ~2K owners). Confirm the patch in `Quorum.Upstream.QRA.ReleaseNotes`. Implementing code: `Quorum.Upstream.QRA.Batch /Quorum.QRA.Process.QPDllBookRev/QSegProcRDCalculation.cs` (reads `WRITE_TO_DB_ONLY_AT_END`); classic path `Quorum.Upstream.QRA.ClassicBatch /QPDllRevenueAcctgBR/QPSRDPostLaunchRDCalcNew.cpp`.
- Related RDCALCNEW defects: **TOLERANTDEC config not honored** (ENC, ADO #1393995); **401/416 impairments** (ADO #1547201); **process freezes at RDCALCNEW/RDPROCNEW** (DAY 24-00950008, ADO #1656546).

**(2) Orphaned locks after a failed run (22-00868629, EQT):**
- **Symptom:** a process errors, its lock never releases; subsequent jobs queue on **QP110 (Active Locks)** indefinitely until IT manually releases. Common with **BKRVNU, DOINTXFRWK, QCFSIMPCYC**; locks `RD_DO_LK`, `VL_DO_LK`.
- **Fix (hotfixed):** added logic so the **UNDOPROC / clean process releases any locks tied to the revenue run being cleaned**; longer-term work to prevent orphaned locks at the source. Identify outstanding locks with the SQL in §15-E.
- Manual unblock: clear the stuck lock rows in `QARCH_LOCK` for the dead PQID (verify-SELECT first). Stuck-process lock releases: 23-00880754, 22-00544805 (QPEC restart).

**QPEC restart** (the operational lever): needed to realize a config change or clear stuck sessions — 24-00992690, 22-00544805, 25-01043414. Many "QPECs down / app endpoint connection errors" are simply a **stale session left open too long** — start a new session first (25-01044952, 25-01043981, FAQ §16).

---

## 6. Cluster C — Contractual Allocation (CA) flow-grid failures

CA020 allocates pipeline-statement (VA) volumes to contracts on a **flow grid**; results go to **`PTRN_CA_VOL` / `PTRN_CA_VOL_ACT`** via `CACALCSPLT → CACTRALLOC → CAGMIOVRD` (`QPSContractualAllocationSplitter.cpp`, `QFlowGrid.cpp`, `QContractUnit.cpp` in `Quorum.Upstream.QRA.ClassicBatch /QPDllRevenueAcctgCA/`). Most actionable CA cases are **rules / time-slice / DOI-setup**, not engine bugs.

| Issue / signature | Root cause | Fix | Case / ADO |
|---|---|---|---|
| `CA did not successfully allocate CA Equity Volumes` / `Found pipeline statement volumes, but no CA results were calculated` after adding a well to a grid | New well / MP missing CA rules or contract connection for that month | Verify CA rules (CA005/CA010) and contract connection cover the new well's effective period; resolution pattern: re-derive rules for the added MP | 23-00897620 (FG 1160G) |
| `CA Rules have not been entered for a measurement point/contract in the grid` | Missing CA rule rows in CA005 | Enter the CA rules for the MP/contract | 23-00931300 |
| CA020 fails because a **prior time slice did not get end-dated** when a new time slice interfaced from IAN/FI | Time-slice overlap (PD051) from the FI→QRA interface | Set the **Effective From Date in RC010** to match the flow-grid connection's earliest effective date; **delete and re-insert** the CA rows (a DB trigger re-inserts into CA005) — do not just edit the date | 25-01036725 (102-GAS WCAA APEX); long-term RCA 25-01032589 |
| CA020 errors with a **DOI Change Warning** | "DOI Change Warning" flags were checked on the grid | **Uncheck** the DOI-change-warning flags | 24-00949469 |
| `Failed to insert new records into PTRN_CA_VOL` (often on PPA / reverse-rebook months) | Stale parent CA rows for the reprocessed periods | Script to **remove the parent `PTRN_CA_VOL` records** for the months, then re-run (recurred in UAT and PRD) | 22-00661351, 22-00661358, 22-00661349 |
| CA on a Market Group for a unit flips MGs from **Complete → Pending**; "can't find owner in DOI for MG seq" with tier 0 | Blank tier on the MG maps to tier 0 which isn't on the well; DOI/MG tier mismatch | Align MG tier with the DOI tier (MG004/MG006 vs DO005) | 22-00819043 |
| CA failing to allocate VA volumes (general) | VA-volume allocation defect | Code fix | 23-00897620 → ADO #1597474 (CNX), #1612983 (MAC COM errors / MMBTU input) |
| `Marketing Group Changing Status from Completed to Pending` | MG status-flip defect during CA | Code fix | 25-01014835 |

**Fix recipe:** For a CA failure, get the **grid number + production month + the first ERROR** from the CA message log (`QPSContractualAllocation.cpp` lines). Then: (a) confirm **CA rules exist** for every MP/contract on the grid (CA005/CA010); (b) check **time-slice/effective-date alignment** in RC010/PD051 — a non-end-dated prior slice from the FI/IAN interface is the most common 2025 cause (25-01036725); (c) uncheck **DOI Change Warning** flags (24-00949469); (d) for PPA/reverse-rebook `PTRN_CA_VOL` insert failures, clear the stale parent rows then re-run (22-00661351 family).

---

## 7. Cluster D — SOD owner pay

SOD owners (paid under a separate SOD sales contract/price, tied via **SOD Masterlink** ML005/ML006) have two recurring problems.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **SOD owners paid on BOTH the SOD and the Standard (Sales) contract** | Defect triggered when a **zero volume is processed on the fuel meter** in the network — system then pays the owner on both contracts | Code fix; operationally, correct/avoid the zero-volume fuel-meter condition and reverse-rebook the affected month | 25-01034077 (Wadestown 95-GAS), prior 24-00964972 → **ADO #1727410** (CNX, Closed) |
| SOD **marketing adjustments not distributing** to SOD owners when DRI is used with an SOD contract (sales pricing came through, adjustments didn't) | SOD-with-DRI distribution defect | **Fixed in a code change** | 24-00948347 |
| **Taxes not going to contract-price SOD owners** in VL/RD | SOD tax-routing defect | Code fix | 23-00904780 (Issue Log 75) → **ADO #1602580** (GEC, Closed) |
| SOD Masterlink **not paying the SOD owner correctly** | 0-net PPNs generated through VL031 (data/setup) | Verify VL031/ML setup | 24-00944917 |
| **No error thrown** when an **Oil** SOD exists on a DOI but the SOD Masterlink (ML005) isn't set up (Gas throws an error, Oil doesn't) → owners silently paid wrong | Missing oil-side validation (enhancement-style) | Requested oil to match gas validation | 22-00513001 |
| `RD Warning: The balancing decimal of all SOD owners has been reset to their NRI decimal` and RD031 ACT_BAL_DEC == NRI when it shouldn't | SOD balancing-decimal reset defect | Code/decimal handling | 22-00819714 |
| SOD **double paid** when booking from an estimate DOI tier to an actual DOI tier | Reverse/rebook SOD defect | Code | 22-00660676 |

**Fix recipe:** when an SOD owner is mis-paid, **first verify the SOD Masterlink (ML005/ML006)** is set up for that owner/product — a large share are missing-setup, and Oil throws no error (22-00513001). If setup is correct and the owner is paid on **both** SOD and Standard contracts, check for a **zero-volume fuel meter** in the network — that is the known defect trigger (25-01034077 / ADO #1727410); reverse-rebook after correcting. SOD-with-DRI marketing adjustments not distributing is a confirmed code fix (24-00948347).

---

## 8. Cluster E — Market Group / Maintenance Group / impairment 302

Market Groups (MG004/MG006; VLA & CIA types) group owners for GMI make-up. Their loss/corruption is the dominant cause of **impairment 302**.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **Market group data deleted/missing** on N properties after a DO transfer / maintenance group (no PPNs created, so it shouldn't have touched MGs) | The maintenance-group refresh **GRPREFWEB** hit a **UNIQUE KEY violation** and finished in error, leaving the MG tables empty; then **COPY_DVD_W** approval copied the *empty* MGs to the live tables | Re-create MGs (copy from UAT→PRD; mind Effective-From/Open-To columns); WI logged for long-term fix | 24-00982421 (31 OK properties), 24-00995037, 24-00982421; copy-process defect 25-01031089 (COPY_DVD) |
| **Impairment 302** in VL100 | Owner not tracking in MG / Interest-Type-Sequence mismatch vs DOI | Update **Market Rep / Interest Type** to match the DOI ownership (DI); bulk-fix via SQL | 25-01048691, 26-01095104, 25-01056530 |
| **RD031 MEG not working** / MEG owner still getting deductions | Marketing/MEG (market group) deduction defect | Patch (21-00104044 family) | 22-00653848, 22-00705138 |
| MG screen unable to add notes; SC005 Contract-Types/Market-Group-Types tab error | Web/screen defects | Code | ADO #1600450, #1319166 |

**Fix recipe:** for impairment 302, open **MG004/MG006** for the failing property/product and confirm the **Market Rep and Interest Type Sequence match the DOI** (DO005/DO016) — fix the rep/int-type (often bulk SQL) and re-run (25-01048691, 26-01095104). If a **whole set of properties lost their MGs after a maintenance-group/DO transfer**, the cause is a failed **GRPREFWEB** that then propagated empty MGs via **COPY_DVD_W** (24-00982421) — re-create the MGs (UAT→PRD copy) and verify the maintenance-group refresh succeeded before approving.

---

## 9. Cluster F — DRI entry & link maintenance

Direct Revenue Input screens (**VL025** links, **VL031** value/volume, **VL032** manual input → `RSTG_MANL_INPUT`, **VL040** flow-grid PPNs) and the PPN reverse/rebook path.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **VLMIUPLOAD commingling import batches** — a user's run picks up unrelated `RSTG_MANL_INPUT` (VL032) rows | Regression from ADO WI **1387395** (batch-isolation broken) | Fix delivered (MEW Patch 8 on 2024.04) | 25-01012760 |
| **PPN reverses but won't rebook** revenue (gas products only) | Reverse-rebook defect | **Fixed in a later version** | 25-01008485 → **ADO #1659398** |
| **DRI double-booking** when reloading revised DRIs / PPNs duplicate in valuation | Duplicate results on reprocess | Code; verify no duplicate meters in flow grid (see FAQ) | 24-00937356, 22-00577329 (duplicate PPA records) |
| **DRI reversal not working** for a subset of wells | Reversal defect | Packaged in January Hotfix | 23-00921719 |
| **VL025 delete deletes the wrong record** — deleting a link deletes any other record with the **same effective date** (LIKE-match `…%`) | Delete uses a too-broad match (deletes the JIB record too) | Code | 23-00899484 |
| Cannot update / fields grayed-out on **VL025 DRI Link Maintenance** | Screen edit/permission defect | Config/screen | 25-01005683 |
| **VL040 reallocation PPAs create excessive RV56 / RV36** records (correct RV20 count) | Over-generation defect on reallocation PPAs | Defect (repro scenarios provided) | 25-01051141 |
| `VL032` save very slow (15 min); `VL031` import failures, trailing-space DRI IDs | Performance / data-format | Perf + data (trailing space in VL031/VL032 vs VL025 link name) | 22-00512452, 26-01081543 (trailing space), 25-01046860 |
| `VLCALCSPLT` fails when processing **Gas & NGLs together** | Splitter defect on mixed products | Code | 22-00669739 |
| **DRI / VL100 process full revenue** unexpectedly (should be partial) | Config | App config | 25-01035352 |

**Fix recipe:** for DRI errors, reconcile the **VL025 link name exactly** against the VL031/VL032 data (a trailing space breaks VL040 — 26-01081543). Double-booking/duplicate PPNs usually trace to **duplicate meters on the flow grid** (FAQ 26-01094724) or a reversal-rebook defect (25-01008485/#1659398). VLMIUPLOAD commingling is a known regression (25-01012760, fixed Patch 8).

---

## 10. Cluster G — Check Write / PCW / Enverus & EnergyLink / netting / voids / 1099

The payment stage: **PCW** (Pre-Check Write — locks/journalizes) then **CW**; **QP043** Generate Enverus Check File (`ENVCHKEXP`) → EnergyLink; ACH; voids; 1099; escheat.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| CW errors for **some owners but not others**; error on `RTRN_CHK_RGSTR` column **ALT_ST_CD** | The owner's **state/country code is longer than the 5-char check-register column** (e.g. NZ-WGN); the split-insert verification fails and stops remaining inserts | Identify via JE101 query joining `JTRN_SL_DETAIL` ↔ `SCTRL_BA_ADDRESS` (see §15-D); **exclude the offending owner(s)** or fix the BA address, then re-run CW | 25-01044023 |
| **Connection error during PCW/CW**; PCW won't lock; can't run CW | App/DB-tier connectivity; stale session | **Restart/start the MT server and/or check DB server status**; re-open session (recurring: 24-00990915, 25-00996489) | 25-01042542, 22-00678222 |
| Special/minimum CW cuts **too many checks / negative checks** | Inclusion/exclusion-table interaction | Use table **4021** (include) + **uncheck "process all owners" in 4022**, re-run CW from **QP043** → generates only the intended checks (prevented voiding 1,377 checks) | 22-00668080 |
| **Negative revenue checks** cut for **netted owners with WI + NWI on the same BA suffix** | Netting defect | Engineering ticket 213457 | 22-00547102 |
| **Voided check** with an in & out for same well/month/product re-issues **netted** instead of showing in & out | Void/re-issue netting defect | Code | 23-00901530 |
| **EnergyLink file incomplete / doesn't tie to check** (minimum-release month, netting) | EnergyLink generation defect with netting | Code/patch | 22-00628339, 22-00640494 |
| Add **RD031 "Act. Balance Decimal"** to QP043 Enverus file (Distribution Interest column) | EnergyLink export currently uses Owner NRI for both columns | Out-of-scope enhancement | 24-00986412 |
| **1099 export shows no records** | **Import/export definition pointed to the wrong directory** | Repoint the 1099 import/export definition to the correct directory | 24-00977475 (Defect 433) |
| **Escheat** processing issue | Defect | Out-of-cycle hotfix delivered to FTP | 22-00512447 |

**Fix recipe:** a CW failure that hits **only some owners** is almost always a **data-length/format** problem on the check register — run the §15-D JE101 query to find the owner with an over-length state code or other bad BA-address field, exclude/fix, re-run (25-01044023). A CW **connection** error → **restart MT server**, verify DB server, re-open session (25-01042542). For over-cutting on minimum/special runs, use the 4021/4022 include + "process all owners" pattern (22-00668080) rather than voiding en masse.

---

## 11. Cluster H — QRA→QCFS / QRAEXPORT

Exporting GL/LOS and revenue from QRA to **QCFS** (financial settlement → SAP) via **QCFSEXPORT** ("Export GL and LOS data to QCFS"). The dominant defect is **JIB-netted properties**.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| QRAEXPORT/QCFSEXPORT **errors for JIB-netted properties** ("wrong major product code", account verification fails) | JIB-netted records originated in QCFS without a DO major product code; QCFS sends them back with **DO major product code**, so QRA looks for a major-product-specific DOI instead of an **ALL** DOI and fails | Script to correct the major product on the affected properties; long-term code fix tracked | 22-00687061, 22-00687068, 22-00830139 (long-term), 22-00811692 (script) |
| **QCFSEXPORT brought no data** for companies 300/310 (recurring monthly) | Export-scope/company defect | Recurring; long-term tracking case opened | 22-00622152, 22-00652363, 22-00628337 |
| QRAEXPORT step-2 (accruals) fails: **"5/1 not within effective date range"** though the deck shows it in range | Effective-date evaluation defect on export | Code | 22-00687068 |
| Export from QRA to QCFS / "missing voucher" | Export/voucher defect | Code/patch | 22-00678328, 22-00628368, 22-00684021 |
| **NETTING not working for company code 2120** (RI owner) | RI owner not enabled for JIB netting | **Config in `GCDE_INT_TYPE`** to allow RI owners to be JIB-netted | 25-01061334 |

**Fix recipe:** a QCFSEXPORT failure on **JIB-netted** properties is the signature here — the fix is a **script to set the correct major product code** so QRA matches an ALL DOI (22-00687061 family); the permanent fix is tracked under 22-00830139. To enable a new RI owner for netting, configure **`GCDE_INT_TYPE`** (25-01061334). Recurring "no data for companies 300/310" is a separate long-running export defect (22-00622152).

---

## 12. Cluster I — Severance / production tax

Tax calc/setup feeding distribution (TS005/TS006, TX006/TX021 screens; tax engine in `Quorum.Upstream.QRA.Tax` / `.ClassicGui.Tax`).

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| BKRVNU/VL100 rejects: `Tax Type is SV … Adjustment Category Code Not Found` (errors 610/615) | Missing **adjustment categories** on the tax screen for that state/tax type | **Add the adjustment categories to TX006** (e.g. OA, ON, LV, GT for NM & TX); script provided | 26-01081729 |
| **VLA tax records doubled/tripled** for properties on units/tracts when loaded via VL032 and processed through VLA | Unit/tract tax-duplication defect | Code | 23-00927993 |
| **North Dakota tax-free portion** value wrong (couldn't reconcile the math) | Exempt-marketing-adjustment selection assumed a single adjustment of each type | Updated the **CC/LU exempt-adjustment selection SQL** (`m_VLCALC_TAX_INS_TMP_RTRN_CMPRS_COST_ALLOC_BCH`, `m_VLCALC_TAX_INS_TMP_RTRN_MI_LU`) to allow multiples; also fixed `QPropertyDOTransaction.cpp` service-contract comparison when summing DRI adjustments | 22-00827507 |
| **Negative WV severance** value calculated (negative proceeds → negative taxable value) | No zero-floor for the well | Requested stop-at-zero behavior; resolution pattern: tax-team manual override pending code | 23-00930897 |
| Variance in net A/R due to **oil severance / FE (reg) tax** (REPX: producer not paying tax — Tax Pay Code N) | DOI Accounting Rule (VL006) FE Tax = "N – Do Not Pay Calculated Tax" by design | Reviewed; handled per REPX scenario (see case mail chain) | 26-01080702 |
| **NM state withholding excluded not working** | Used "NM" on the code table instead of **30** (the NM state code) | Use the numeric state code (Customer Error) | 25-01050292 |

**Fix recipe:** a `Tax Type SV / Adjustment Category Code Not Found` reject means a **missing TX006 adjustment category** for that state+tax type — add it (26-01081729). Tax doubling on units/tracts is a known VLA defect (23-00927993). Tax-free / exempt-adjustment math errors trace to the exempt-adjustment selection assuming a single adjustment (22-00827507). Always confirm the client used the **numeric state code** (e.g. 30 = NM), not the alpha (25-01050292).

---

## 13. Cluster J — Owner Funds Release (OFR)

Releasing suspended owner funds (DO129/DO130) → OFR staging → JE100.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| OFR completes with errors; posting **routes to Account Group 80** but fails account lookup | A JIB-netting transaction (suspense, pay code 2) triggers **JIB Owner Suspense (Group 80)** routing, but **no GL account is configured for Account Group 80** | **Map a valid GL account for Account Group 80** in the account-mapping table (`JXRF_ACCT_ACCT_GRP`, screen JE020) | 26-01099468 |
| Funds release **completing with errors** / OFR "stuck" under DO129 | OFR processing defect | Code fix | 25-01010841 → **ADO #1541765** (Ovintiv/ECA), **#1584263** (GLE, DO129 stuck) |
| **Funds making into OFR staging 3×, tripling the release** | Triple-insert defect | RCA tracked (critical) | 26-01098402 (RCA for 26-01097438) |
| "Turn on **auto-post** for owner funds release" | Config toggle | Enabled config **`AUTO_POST_OFR`** | 25-01060332 |
| Can't do maintenance / funds release on **inactive properties** (could in old version via DO020/DO130) | Behavior change after upgrade | Resolution pattern unclear from mined cases (logged) | 25-01045849 |
| "Zero" OFRs created on JE100 with no balance | **Expected behavior** — choosing "owners and funds" updates funds status and creates a zero entry; choose **"owners" only** if not changing funds | Education | 26-01067072 |

**Fix recipe:** OFR errors that mention **Account Group 80** = JIB Owner Suspense routing with a missing GL mapping → add the GL account in **JE020 / `JXRF_ACCT_ACCT_GRP`** (26-01099468). "Stuck"/errored OFR under DO129 is a confirmed code-fix family (#1541765, #1584263). `AUTO_POST_OFR` controls auto-posting (25-01060332).

---

## 14. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1727410** | Bug / **Closed** | CNX 2022.04 — SOD Owner paid on both SOD and Standard (Sales) contract | §7 | 25-01034077 / 24-00964972 |
| **#1602580** | Bug / **Closed** | GEC — taxes not going to contract-price SOD owners in VL/RD | §7 | 23-00904780 |
| **#1659398** | Bug / **Closed** | CNX 2022.04 — Simultaneous BKRVNU → VL Reversal source not generated (PPN reverse/rebook) | §9 | 25-01008485 / 24-00948965 |
| **#1597474** | Bug / **Closed** | CNX — Failure to allocate VA volumes during Contractual Allocation | §6 | 23-00897620 |
| **#1612983** | Bug / **Closed** | MAC — Contractual Allocation throwing COM errors / can't input MMBTU into CA rules | §6 | — |
| **#1393995** | Bug / **Closed** | ENC — RDCALCNEW not honoring the TOLERANTDEC config setting | §5 | — |
| **#1547201** | Bug / **Closed** | EQCU — BKRVNU failing with RDCALCNEW on 401/416 impairments | §5 | — |
| **#1656546** | Bug / **Closed** | DAY — process freezes at RDCALCNEW/RDPROCNEW step | §5 | 24-00950008 |
| **#1659398 / #1607081** | Bug / **Closed** | BKRVNU null-insert / reversal-source (MAC 23-00906646) | §4/§9 | 23-00906646 |
| **#1541765** | Bug / **Closed** | Ovintiv/ECA — Owner Funds Release completing with errors | §13 | 25-01010841 |
| **#1584263** | Bug / **Closed** | GLE — Owner Funds Release under DO129 "stuck" | §13 | 23-00888898 |
| **#1387395** | Requirement (regression source) | BKRVNU change that caused VLMIUPLOAD batch commingling | §9 | 25-01012760 |
| **#1600450 / #1319166** | Bug / **Closed** | Market Group / SC005 screen defects | §8 | — |

> Several actionable cases were dispositioned **operationally** (config / script / FTP'd hotfix) with no single product WI: RDCALCNEW lock workaround `WRITE_TO_DB_ONLY_AT_END=1` + QPEC restart (25-01034392, long-term 25-01046201); orphaned-lock release in UNDOPROC/clean (22-00868629); CA `PTRN_CA_VOL` parent-row clear scripts (22-00661351 family); CA time-slice RC010 re-insert (25-01036725); JIB-netting major-product-code scripts (22-00687061/22-00830139); TX006 adjustment-category script (26-01081729); ND tax-free exempt-adjustment SQL fix (22-00827507); 1099 export-definition repoint (24-00977475); Account-Group-80 GL mapping (26-01099468); `GCDE_INT_TYPE` netting config (25-01061334); `AUTO_POST_OFR` toggle (25-01060332). **Confirm exact build/patch in `Quorum.Upstream.QRA.ReleaseNotes` before stating fix availability.**

---

## 15. Diagnostic SQL

> **Caveat:** QRA runs on SQL Server (T-SQL). Table/column names below are taken from case repro text and code search; **verify against the client schema before scripting**, and always run a verify-SELECT before any UPDATE/DELETE, wrapped in a transaction.

```sql
-- A. Find the failing VL100/BKRVNU step + first error by Process Queue ID
--    (the lowest-sequence ERROR is the root; rows above it are cascade "won't execute")
SELECT PROCESS_LOG_ID, LOG_MSG_TYPE_CD, PROCESS_STEP_ID, LOG_MSG
FROM   QARCH_PROCESS_LOG          -- (verify table name in client; per case 23-00929043)
WHERE  PROCESS_QUEUE_ID = @pqid
ORDER  BY PROCESS_LOG_ID;          -- ascending; root cause is the earliest ERROR

-- B. Orphaned locks from RD/VL runs that failed (the 22-00868629 pattern; clear after verify)
SELECT DISTINCT A.*
FROM   QARCH_LOCK A
JOIN   QARCH_QUEU_PROCESS B ON A.MASTER_PROCESS_QUEUE_ID = B.PROCESS_QUEUE_ID
LEFT  JOIN QARCH_CODE_PROCESS_STATUS C
       ON B.STATUS_CD = C.STATUS_CD AND C.STATUS_CTGY_CD <> 'COM'
WHERE  C.STATUS_CTGY_CD IS NULL                      -- not in a completed status
AND    A.LOCK_TYPE_CD IN ('RD_DO_LK','VL_DO_LK');    -- most common stranded locks

-- C. Is the RDCALCNEW lock workaround config set? (§5)
SELECT * FROM QARCH_CNFG_CTRL WHERE CNFG_NM = 'WRITE_TO_DB_ONLY_AT_END';   -- expect value 1 (ENV layer)
SELECT * FROM QARCH_CNFG_CTRL WHERE CNFG_NM = 'AUTO_POST_OFR';             -- OFR auto-post toggle (§13)

-- D. Check-Write failure on over-length state code (the 25-01044023 RTRN_CHK_RGSTR.ALT_ST_CD pattern)
SELECT SUM(D.TRANS_AMT) AS TOT, D.OWNR_BA_NO, A.STATE_CD, A.COUNTRY_CD
FROM   JTRN_SL_DETAIL D
JOIN   SCTRL_BA_ADDRESS A ON D.OWNR_BA_NO = A.BA_NO
WHERE  SL_NO = '01'
GROUP  BY D.OWNR_BA_NO, A.STATE_CD, A.COUNTRY_CD
HAVING SUM(D.TRANS_AMT) <= -100         -- look for STATE_CD longer than the column max (e.g. 'NZ-WGN')
ORDER  BY 3;

-- E. CA results for a flow grid / production month (did CA produce rows?) (§6)
SELECT GRID_NO, PRDN_DT, MP_NO, CTR_NO, MAJ_PROD_CD, DISP_CD, RECORD_COUNT
FROM   PTRN_CA_VOL
WHERE  GRID_NO = '<grid>' AND PRDN_DT = '<prod_dt>';
-- Compare against PTRN_CA_VOL_ACT; a "no CA results were calculated" error = missing/zero rows here.

-- F. RD decimal mismatch (SOD balancing-decimal symptom, §7; RD031)
SELECT RRID, PROP_NO, OWNR_BA_NO, OWNR_NRI_DEC, ACT_BAL_DEC
FROM   <RD031 detail table>
WHERE  RRID = '<rrid>' AND OWNR_NRI_DEC <> ACT_BAL_DEC;

-- G. DOI funds-transfer records stuck "In Interface Transfer" (24-00945242 workaround)
SELECT TRANS_SEQ_NO, XFER_STAT_CD, UPDT_DT
FROM   DONL_INT_FUNDS_XFER_HDR
WHERE  XFER_STAT_CD = '3';   -- 'Approved' but stuck; workaround sets to '6' (Completed) after verify

-- H. JIB suspense GL mapping for Account Group 80 (OFR error, §13)
SELECT * FROM JXRF_ACCT_ACCT_GRP WHERE ACCT_GRP_CD = '80';   -- must have a valid GL account (JE020)
```

---

## 16. Expected-Behavior / User-Education FAQ

~207 Customer-Error + ~92 Training cases. Recognize these to avoid needless scripts/escalations — the overwhelming majority of "VL040/VL100 error" tickets are **setup/data**, not defects.

| Reported as | Reality / answer | Case |
|---|---|---|
| "VL040 / VL100 fails for flow grid / remitter X" | Missing **DOI** (add in DO + cross-ref SP025 + Accounting Rule VL006), missing **volumes** (VA005), or incomplete **Market Group / Bearer Group** — complete the setup and re-run | 26-01101703, 26-01095419, 26-01095418, 26-01094724, 26-01101034 |
| "DRI process exception / VL040 duplicates for a remitter" | **Duplicate meters on the flow grid** (data-conversion artifact) — remove the duplicate meter connections; or wrong **"Pmt. Level Ovrd. MP No." in VL025** — map the correct MP | 26-01094724, 26-01095352, 26-01094584 |
| "VL040 flow grid fails" with a name that "looks right" | **Trailing space** in the VL025 DRI Link name vs VL031/VL032 data — make them match exactly | 26-01081543 |
| "Impairment 302" / "PPN errors with NRI decimals" | Owner not tracking in the **Market Group** — fix Market Rep / Interest Type to match the DOI; or wrong/few properties selected in the PPN | 25-01048691, 25-01031961, 25-01056530 |
| "State withholding / tax not excluding" | Used the **alpha state code** ("NM") instead of the **numeric** code (30) | 25-01050292 |
| "VL100 expecting price terms (209 reject)" | New **Valid Products RD=Y** flag on the product/disposition now requires a price term in **RC036** — add it | 25-01042767 |
| "Zero-balance OFRs created on JE100" | **Expected** — selecting "owners and funds" creates a zero entry; pick **"owners" only** if not changing funds | 26-01067072 |
| "QPECs down / app endpoint connection errors / can't approve in UAT" | Usually a **stale session left open too long** — open a new session; if truly down, restart services/QPEC | 25-01044952, 25-01043981, 25-01042323 |
| "MJE approved twice / duplicate JE100 records" | A double-approval let an MJE post twice — prevent post on the duplicate; investigate how double-approval happened | 25-01056378 |
| "What report shows VL results / distribution codes?" | **RPTVLR017A – VL Results**; distribution code N = "Distribute to All in Market Group" (documentation) | 25-01095018, 26-01102148 |
| "Can't end-date a tax rate (TX021)" / "PPNs won't process" | Data already processed (end-date blocked) — needs OOS project; or simply re-run the PPNs (often clears with no change) | 26-01071028, 25-01026131 |

**Tell-tale it's user/expected:** a VL040/VL100 error that resolves by **adding a missing DOI/volume/contract or completing a Market/Bearer Group**; a trailing space or wrong MP override on a VL025 link; an alpha-vs-numeric code-table value; a "QPEC down" that is a stale session; or an audit/"how does it work"/report-finding question. **Verify DOI setup (DO005/SP025/VL006), Market Groups (MG004/MG006 vs the DOI), contract/price terms (RC036/RC040), and upstream CA/volumes before treating it as a defect.**

---

## 17. Key Code, Processes & Repos

### Processes / screens
| Process / screen | Purpose | Notes |
|---|---|---|
| **VL100** (revenue process) | Master "process revenue"; chains VLCALC → RDSELECT → RDCALCNEW/RDPROCNEW → JEPRECOMBO → RDIMPAIRJE | Get PQID + first ERROR + impairment code (§4) |
| **BKRVNU** | Book-Revenue batch engine behind VL100 distribution | `Quorum.QRA.Process.QPDllBookRev` (§4/§5) |
| **RDCALCNEW / RDPROCNEW** | Revenue-distribution calc step | ROLLBACK/lock family; `WRITE_TO_DB_ONLY_AT_END` (§5) |
| **CA020** (CACALCSPLT → CACTRALLOC → CAGMIOVRD) | Contractual allocation on a flow grid | Writes `PTRN_CA_VOL` / `PTRN_CA_VOL_ACT` (§6) |
| **VL025 / VL031 / VL032 / VL040** | DRI link maint / value-volume / manual input (`RSTG_MANL_INPUT`) / flow-grid PPNs | VLMIUPLOAD loads VL032 (§9) |
| **PCW / CW / QP043 (ENVCHKEXP)** | Pre-Check Write / Check Write / Generate Enverus Check File → EnergyLink | Tables 4021/4022/4048; register `RTRN_CHK_RGSTR` (§10) |
| **QCFSEXPORT** | Export GL & LOS data to QCFS → SAP | JIB-netting major-product mismatch (§11) |
| **JE020 / JE100 / JE101 / MJE** | Account mapping / journal entries / manual JE | Acct Group 80 GL mapping for OFR (§13) |
| **DO129 / DO130 / OFR** | Owner Funds Release | `AUTO_POST_OFR` (§13) |
| **GRPREFWEB / COPY_DVD_W** | Maintenance-group refresh / approve-copy | Failed GRPREFWEB → empty Market Groups (§8) |
| **TX006 / TX021 / TS005 / TS006 / VL006** | Tax setup / accounting rules | Adjustment categories; Tax Pay Code (§12) |

### Code locations (confirmed via ADO code search)
| Symbol / path | Repo | Cluster |
|---|---|---|
| `QSegProcRDCalculation.cs` (reads `WRITE_TO_DB_ONLY_AT_END`) | `Quorum.Upstream.QRA.Batch /Quorum.QRA.Process.QPDllBookRev/` | §5 |
| `QPSRDPostLaunchRDCalcNew.cpp`, `QPSRDBuildSelection.cpp` | `Quorum.Upstream.QRA.ClassicBatch /QPDllRevenueAcctgBR/` | §4/§5 |
| `QPSContractualAllocationSplitter.cpp/.h`, `QFlowGrid.cpp`, `QContractUnit.cpp` | `Quorum.Upstream.QRA.ClassicBatch /QPDllRevenueAcctgCA/` | §6 |
| `QPropertyDOTransaction.cpp`; `m_VLCALC_TAX_INS_TMP_*` SQL IDs | `Quorum.Upstream.QRA.ClassicBatch` (Valuation/Tax) | §12 |
| `RtrnChkRgstrDO.cs / RtrnChkRgstrDAL.cs` (check register) | `Quorum.Upstream.Shared.Web /Quorum.QRA.DataObject|DAL/` | §10 |
| `QARCH_CNFG_CTRL.json` (`WRITE_TO_DB_ONLY_AT_END`, `AUTO_POST_OFR`) | `<CLIENT>.Upstream.Metadata /STANDARD 16.0/` | §5/§13 |

### Repos (see REPO_INVENTORY)
- **`Quorum.Upstream.QRA.*`** — core QRA: `.Database`, `.ClassicBatch` (C++ revenue/CA/tax), `.Batch` (managed BKRVNU), `.Web` / `.Application.MiddleTier` / `.ClassicGUI`, `.Tax` / `.ClassicGui.Tax`, `.ReleaseNotes`.
- **`Quorum.Upstream.QCA.*`** — Contractual Allocation app/batch/db (where CA logic also lives in the newer stack).
- **`Quorum.Upstream.QDO.*`** — Division Order (DOI, maintenance groups, OFR screens).
- **`Quorum.Upstream.QCFS.*`** — financial-settlement / GL export target (QCFSEXPORT lands here → SAP).
- **`Quorum.Upstream.Shared.*`** — shared Web/Batch/ClassicGUI (check register DOs, shared screens).
- **`<CLIENT>.Upstream.QRA.* / .Database / .Metadata / .ClassicBatch`** (CNX, GEC, MAC, MEW, EQC, ENC, DAY, ECA/Ovintiv, GLE, NOG, REP, PNR, …) — **always check the client repo/schema first**; many fixes are client-specific (metadata config, schema, client batch overrides). Note CNX/DCP/ETP/IAC/etc. run **QDOD** (Division-Order-only) repos, not full QRA.

---

## 18. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A **calculation/distribution** is provably wrong on correct setup: SOD paid on both contracts (25-01034077/#1727410), SOD adjustments not distributing (24-00948347), SOD taxes not routing (#1602580), PPN reverses-but-won't-rebook (25-01008485/#1659398), VLA tax doubling on units/tracts (23-00927993), ND tax-free portion (22-00827507), VL025 over-broad delete (23-00899484), excessive RV56 on reallocation PPAs (25-01051141), VLMIUPLOAD commingling (25-01012760/#1387395).
- A **step crashes from a code path**, not data: RDCALCNEW lock/rollback long-term (25-01046201), RDCALCNEW TOLERANTDEC (#1393995), freeze at RDCALCNEW/RDPROCNEW (#1656546), BKRVNU null-insert/"sequence >1" (#1607081, 24-00983823), market-group loss via GRPREFWEB/COPY_DVD (24-00982421), OFR stuck/errored (#1541765, #1584263), OFR triple-insert (26-01098402).
- Provide: **PQID + failing step + first ERROR line + impairment code**, client + property/grid + production & accounting month, the DOI/contract, and a repro. Confirm fix availability in `Quorum.Upstream.QRA.ReleaseNotes` and the linked WI's target build.

**Handle as Configuration / Cloud Ops when:**
- **RDCALCNEW locking** short-term: set `WRITE_TO_DB_ONLY_AT_END = 1` (ENV) + **QPEC restart** (25-01034392, 25-01043414). **Orphaned locks**: confirm UNDOPROC/clean lock-release is deployed; clear `QARCH_LOCK` (22-00868629).
- **CA**: enter/correct CA rules (CA005/CA010), align time-slices/effective dates (RC010/PD051), uncheck DOI-change-warning flags, clear stale `PTRN_CA_VOL` parents for PPA re-runs (25-01036725, 24-00949469, 22-00661351).
- **Tax**: add TX006 adjustment categories (26-01081729). **Netting**: enable RI owners in `GCDE_INT_TYPE` (25-01061334). **OFR**: map GL for Account Group 80 in JE020 (26-01099468); `AUTO_POST_OFR` toggle (25-01060332). **1099**: repoint export definition (24-00977475). **JIB-netted export**: major-product-code correction script (22-00687061 family).
- **QPEC restart** to realize a config change or clear stuck sessions (24-00992690, 22-00544805).

**Service/session first (no code):** Check-Write/UAT "connection error", "QPECs down", "can't approve/view" — **restart MT/QPEC** or simply **open a new session** (stale session is the #1 cause: 25-01042542, 25-01044952, 25-01043981).

**Handle as Training / Expected behavior (no fix):** see §16 — VL040/VL100 errors that resolve by adding a missing DOI/volume/contract or completing a Market/Bearer Group; trailing-space VL025 link names; wrong MP override; alpha-vs-numeric state codes; zero-balance OFRs; report/audit questions. **Verify DOI (DO005/SP025/VL006), Market Groups (MG004/MG006), contract/price terms (RC036/RC040), and upstream CA/volumes before treating it as a defect.**

---

*Skill created: 2026-06-14.*
*Based on: 1,170 closed QRA Revenue Distribution / Direct Revenue Input / Contractual Allocation SF cases — 199 actionable (Software Defect 132 + Application Configuration 63 + ChangeConfig 4) mined for fix recipes, plus ~40 Customer-Error/Training cases for the FAQ. ADO work items #1727410, #1602580, #1659398, #1597474, #1612983, #1393995, #1547201, #1656546, #1607081, #1541765, #1584263, #1387395, #1600450, #1319166.*
*Companion: REPO_INVENTORY, CONFIG_REFERENCE.*
