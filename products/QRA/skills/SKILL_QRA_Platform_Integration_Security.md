# SKILL: QRA Platform / Integration / Security Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** My Quorum Revenue Accounting (QRA) — upstream oil & gas revenue accounting (myQuorum / On Demand suite)
**Scope:** The cross-cutting **platform, integration, batch-process, and security** layer of QRA — the back-end revenue pipeline batch jobs (**BKRVNU** book-revenue, **VL100 / VL040** value-allocation/distribution, **VLCALC / VLCALCSPLT**, **Contractual Allocation (CA)**), the **export/integration** boundary (**QCFSEXPORT** GL→QCFS, EnergyLink/Enverus, 1099, NAUPA/escheat, FI→QRA / QLS network sync), **payments** (Check Write / OFR / ACH / netting), **process/infrastructure health** (QPEC restart, orphaned locks, timeouts, performance), and **security / Web-vs-Classic config / code-table** issues. This is the catch-all sibling to the functional-calculation skills.
**Companion skills:** Revenue valuation math, owner/DOI suspense detail, and check-write business rules belong in the QRA functional skills; this skill owns the *process crashed / didn't export / can't log in / Web≠Classic* surface. When the **settled/valued number itself** is wrong (decimals, NRI, severance math), fix that in the functional/valuation skill first — this skill is usually the messenger (the batch step that reported it).

> **Evidence base:** The QRA "Platform_Integration_Security" category bucket holds **221 actionable** closed cases (Root Cause = **Software Defect 73 + Application Configuration 140 + ChangeConfig 8**) out of ~1,800 closed cases in the bucket (Case_Category__c IN eSuite/Platform-UX/Integration/Security/Business Associates/System Configuration/QQM/Other/All/Installation/Archive/Estimate/Contracts). Functional category mix of the actionable set (the SF `Case_Category__c` *primary* label): Revenue Distribution and Direct Revenue Input dominate, with Contractual Allocation. This skill mines those 221 for fix recipes plus ~30 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining; where a mined case had no populated resolution it is marked "resolution pattern unclear from mined cases."

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — BKRVNU (Book Revenue) batch failures (HIGH FREQUENCY)](#4-cluster-a--bkrvnu-book-revenue-batch-failures)
5. [Cluster B — VL100 / VL040 value-allocation & distribution failures](#5-cluster-b--vl100--vl040-value-allocation--distribution-failures)
6. [Cluster C — QCFSEXPORT & GL/LOS export to QCFS](#6-cluster-c--qcfsexport--glos-export-to-qcfs)
7. [Cluster D — External integration / files (EnergyLink, Enverus, 1099, NAUPA/Escheat, FI→QRA / QLS)](#7-cluster-d--external-integration--files)
8. [Cluster E — Check Write / OFR / ACH / netting (payments)](#8-cluster-e--check-write--ofr--ach--netting)
9. [Cluster F — SOD (Standard Owner Deck) distribution & MasterLink](#9-cluster-f--sod-standard-owner-deck-distribution--masterlink)
10. [Cluster G — Contractual Allocation (CA) failures](#10-cluster-g--contractual-allocation-ca-failures)
11. [Cluster H — Process health: QPEC restart, orphaned locks, stuck batches](#11-cluster-h--process-health-qpec-restart-orphaned-locks-stuck-batches)
12. [Cluster I — Performance & timeouts (revenue runs, QQM, DRI, VL032 save)](#12-cluster-i--performance--timeouts)
13. [Cluster J — Market Group / maintenance-group copy (GRPREFWEB / COPY_DVD)](#13-cluster-j--market-group--maintenance-group-copy)
14. [Cluster K — Security, Web-vs-Classic cache, code-table & column-length config](#14-cluster-k--security-web-vs-classic-cache-code-table--column-length-config)
15. [Known ADO Items](#15-known-ado-items)
16. [Diagnostic SQL](#16-diagnostic-sql)
17. [Expected-Behavior / User-Education FAQ](#17-expected-behavior--user-education-faq)
18. [Key Code, Processes & Repos](#18-key-code-processes--repos)
19. [Escalation Guidance](#19-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| **BKRVNU** "Book Revenue" process fails / stuck at PRC / "Distribution failed for RD Input Group …" / child `RDCALC` fails | Batch-step defect or orphaned lock; simultaneous BKRVNU runs collide; Dual-Fuel/DRI edge | PQID + failing **child process + step name**; §4 (+ §11 if a lock); confirm BKRVNU patch for the client |
| BKRVNU **"Memory Exception"** / runs indefinitely | Volume / batch sizing / orphaned lock | §4/§11/§12 — restart QPEC, clean the run (releases locks), batch the work |
| **VL100 / VL040** erroring: "302 / 314 / 540 impairment", "failed on RD distribution", "failed to create 2nd DIST level PSUM" | Impairment reason-code data condition; tax-exempt / tolerance / split-rounding | §5 — get the **impairment reason code**; tax-exempt flag scripts, TOLERANT_DEC, VL split logic |
| **QCFSEXPORT** "did not bring data over" / over-applied / null INV_NO / can't reprocess | Already-flagged GL interface rows; null/over-applied data | §6 — flip `GL_INTFC_COMPLETE_FL` to N in `JTRN_GL_MTD`; script-review the bad rows |
| EnergyLink / Enverus / 1099 export **shows no records / wrong format / incomplete** | Wrong import/export **definition directory**; format/spec gap | §7 — verify the export definition path; NAUPA format & escheat source-type are known defect areas |
| **Check Write** "Connection Error" / fails on a column (state code) / negative checks for netted owners | DB/MT server down; column-length data; netting/owner-inclusion setup | §8 — restart MT/DB server; find the over-length value (e.g. `ALT_ST_CD`); use owner-inclusion table |
| **SOD owner** double-paid / not paid / "balancing decimal reset to NRI" / missing MasterLink | SOD MasterLink setup or SOD-in-DRI defect | §9 — check SOD MasterLink; config `ONLY_CREATE_WARNINGS_FOR_MISSING_SOD_MASTERLINKS` |
| **Contractual Allocation (CA)** failing / won't close / flowgrid errors | DOI Change Warning Flags checked; flowgrid state/data | §10 — uncheck DOI Change Warning Flags; verify flowgrid |
| Everything **stuck in QUE**, nothing running, app "down/slow critical" | Orphaned process holding a DB/process lock | §11 — **restart QPECs**, cancel the stuck OFR/run; clean the run to release locks |
| Revenue run / QQM report / DRI entry **times out / very slow** | Timeout config too low; volume; missing optimization | §12 — raise timeout config (LCMBIAR for QQM), re-optimize tables, batch the entry |
| **Market groups deleted / empty / changing Completed→Pending** | GRPREFWEB unique-key failure left tables empty, then COPY_DVD copied empties to live | §13 — re-refresh group; copy from UAT; code fix removed extraneous table from query |
| User **can't log in / can't update a screen / Web ≠ Classic / dropdown won't change** | Security setup (wrong email, missing group/metadata layer); **cache not refreshed** after Code/Decode change | §14 — fix security; **refresh the Web cache** after any Code/Decode value-maintenance change |

---

## 2. Pipeline & Concepts

```
[FI / measurement / network]  →(INT_QLSWL, JDECCINTFC, FI→QRA sync)→  [QRA volumes & DOIs]
      │
      ▼  VALUE ALLOCATION / DISTRIBUTION
   VL032/VL031 (import) → VL040 (VLCALC / VLCALCSPLT split) → VL100 (RD distribution, PSUM, PPN/RV creation)
      │
      ▼  BOOK REVENUE
   BKRVNU  (child procs incl. RDCALC / RDCALCNEW, GMI calc, market-group GMI) → JE100 (journalize) → JE200 / LOS
      │
      ├──► PAYMENTS:  OFR (Owner Funds Release) → Check Write (QP043 / CW / PCW) → ACH / Enverus check file
      └──► EXPORTS/INTEGRATION:  QCFSEXPORT (GL+LOS → QCFS), EnergyLink/Enverus, 1099 (NEC/MISC), NAUPA/Escheat (HRS)
```

### Key terms (QRA / upstream-accounting vocabulary)
- **BKRVNU** = the **Book Revenue** batch process (run from the VL100 / Revenue Submission screen). Has child processes (`RDCALC`/`RDCALCNEW`, GMI calc, market-group GMI). The single largest defect/lock surface in this bucket.
- **VL100 / VL040 / VL032 / VL031 / VL025 / VL040** = the **Value Allocation** screen family. VL032/VL031 import revenue; VL040 runs `VLCALC`/`VLCALCSPLT` (splitting/allocation); VL100 runs RD distribution and creates **PSUM**, **PPN**, **RV** records. VL025 = DRI Link Maintenance.
- **RD** = **Revenue Distribution**; **RRID** = Revenue Run ID; **RD Input Group** = the unit of work VL100 distributes.
- **PPN** = revenue payment/processing notice record (created by VL031/VL100); **RV20/RV40/RV56** = revenue voucher/reversal record types.
- **DRI** = **Direct Revenue Input** (manual revenue entry, VL025/VL032 screens, DR020/DO055). **SOD** = **Standard Owner Deck** — a standardized owner/DOI deck; **SOD MasterLink** ties a property to its SOD deck.
- **NRI / decimal interest / balancing decimal** = owner net-revenue-interest decimals; "balancing decimal reset to NRI" is a recurring SOD warning.
- **GMI** = Gross Margin/Income calc step inside revenue (e.g. `USPD_MKT_GRP_GMI_CALC`); progressive-rounding bugs live here.
- **CA / Contractual Allocation** = the contractual (flowgrid / marketing-group) allocation that feeds revenue; runs as "Valuation Main Process" / VLPROC.
- **OFR** = **Owner Funds Release**; **Check Write (CW / PCW / QP043)** = generates owner checks; **netting** = JIB-to-revenue netting (config in code table `GCDE_INT_TYPE` / `GCD_INT_TYPE`).
- **QCFSEXPORT** = the batch that exports **GL + LOS data to QCFS** (Quorum's financial/GL system); driven by `JTRN_GL_MTD` (GL month-to-date staging) with the `GL_INTFC_COMPLETE_FL` flag.
- **QPEC** = the QRA batch/process engine service (per-environment, e.g. `QCPRDQPEC909-V`). Restarting QPECs is the standard unblock for stuck/locked processes.
- **GRPREFWEB / COPY_DVD(_W)** = maintenance-group **refresh** (GRPREFWEB) then **copy/approve to live** (COPY_DVD). A failed GRPREFWEB can leave market-group tables empty and COPY_DVD then copies the emptiness to PRD.
- **Web vs Classic + Code/Decode value maintenance** = QRA runs a ClassicGUI and a Web UI off shared metadata/code tables (e.g. `5002 GCD_INT_TYPE`, `5030`, `16142`, `29046`). Changes in Classic require a **Web cache refresh** to appear in Web — the #1 "Web≠Classic" cause.

---

## 3. Decision Tree

```
QRA platform / integration / security case
│
├─ A batch PROCESS/STEP failed? → GET PQID + the failing CHILD PROCESS + STEP NAME + exact error
│   ├─ BKRVNU (book revenue) fails / stuck / memory / RDCALC child / Distribution failed   → §4  (+ §11 if lock, §12 if perf)
│   ├─ VL100 / VL040 (impairment 302/314/540, RD distribution, PSUM, VLCALCSPLT)            → §5
│   ├─ QCFSEXPORT "no data / over-applied / null INV_NO / can't reprocess"                  → §6  (GL_INTFC_COMPLETE_FL=N + script review)
│   ├─ Contractual Allocation / Valuation Main Process / flowgrid won't close               → §10 (DOI Change Warning Flags)
│   └─ Market group refresh/approve (GRPREFWEB / COPY_DVD) left groups empty                → §13
│
├─ An EXPORT/INTEGRATION produced nothing / wrong format / incomplete?
│   ├─ QCFSEXPORT                                                                            → §6
│   └─ EnergyLink / Enverus / 1099 / NAUPA-Escheat / FI→QRA / QLS wells                      → §7 (verify export definition path; format gaps)
│
├─ PAYMENTS wrong / failing?
│   ├─ Check Write connection error / column error / negative checks / variances             → §8
│   ├─ OFR stuck / not auto-processing / files rejected                                       → §8 / §11 (AUTO_POST_OFR; cancel stuck OFR)
│   └─ SOD owner double-paid / not paid / balancing-decimal reset / MasterLink missing        → §9
│
├─ Whole environment STUCK / "critical / down / slow", everything in QUE?                    → §11 (restart QPECs, cancel stuck OFR/run, clean run releases locks)
├─ Single thing SLOW / TIMES OUT (revenue run, QQM report, DRI entry, VL032 save)            → §12 (raise timeout config; re-optimize; batch)
│
└─ Can't log in / can't update screen / Web ≠ Classic / dropdown won't change / privilege error → §14 (security setup + Web cache refresh after Code/Decode change)
```

---

## 4. Cluster A — BKRVNU (Book Revenue) batch failures

**The single largest actionable signature in this bucket.** BKRVNU is run from the VL100 / Revenue Submission screen and orchestrates child processes (`RDCALC`/`RDCALCNEW`, GMI). It fails three ways: **(1) a child-process/step error**, **(2) stuck/indefinite (lock/perf)**, **(3) a wrong-result defect**.

**Representative cases & fixes:**

| Issue / signature | Root cause | Fix | Case / ADO |
|---|---|---|---|
| FMO 2024.10 upgrade — DRI BKRVNU **"Distribution failed for RD Input Group …"** | Upgrade-introduced BKRVNU/DRI defect | Code fix in the upgrade build | 25-01025049 / **#1735710** (Bug, Closed) |
| BKRVNU child **`RDCALC` fails** (FMO) | Child-process defect | Code fix | **#1711649** (Bug, Closed) |
| BKRVNU **stuck at PRC** (CEN) | Orphaned lock / stuck child | Restart QPEC + clean the run (see §11) | **#1725921** (Incident, Closed) |
| **Simultaneous BKRVNU** runs → unintended **VL reversal** collateral (CNX 2022.04); also "PPN reversing but not rebooking revenue" | Concurrency: two BKRVNU runs collided; a separate PPN fix caused collateral damage to RD | Corrected; OOC hotfix | 25-01008485, 25-01055209 / **#1659398** (Bug, Closed, CNX 2022.04) |
| BKRVNU **"Dual Fuel" DRIs** (RLY) | DRI Dual-Fuel edge in BKRVNU | Code fix | 25-01061195 / **#1774912** (Bug, Closed) |
| **BKRVNU Memory Exception** | Volume / sizing | Batch the work; see §12 perf (`USPD_MKT_GRP_GMI_CALC` perf improvement) | 24-00943638, 22-00552667, 22-00674535 |
| **`RDCALCNEW` database locking** (long-term fix) | Locking under concurrency | Long-term locking fix (§11) | 25-01046201 |
| BKRVNU "Sequence Contains More Than One Matching Element" | >1 row where one expected (LINQ/SQL) | Code fix | 24-00983823 |
| "302 Impairment Error" on BKRVNU/VL100 | Impairment data condition (see §5) | §5 | 24-00960682, 24-00684039 |

**Fix recipe:**
1. Get **PQID + the failing child process (RDCALC/RDCALCNEW/GMI) + exact message**. Many BKRVNU "failures" are actually a **lock** (process stuck at PRC) → go to §11 first: restart QPEC, then **clean/undo the revenue run** (the clean process releases locks tied to that run — #1659398/22-00868629).
2. If it is a **true child-process defect** (RDCALC fails, Distribution-failed, Dual-Fuel, simultaneous-run reversal) → escalate to Engineering with PQID; these are confirmed bugs with closed WIs (#1711649, #1735710, #1774912, #1659398) — confirm the fix build for the client.
3. **Never run two BKRVNU jobs simultaneously** for overlapping data — #1659398 shows concurrency can produce spurious VL reversals.
4. Memory/indefinite → §12 (batch; the `USPD_MKT_GRP_GMI_CALC` GMI step was a known perf hotspot — 22-00552667).

---

## 5. Cluster B — VL100 / VL040 value-allocation & distribution failures

VL040 runs the split (`VLCALC`/`VLCALCSPLT`); VL100 runs RD distribution and creates PSUM/PPN/RV. Failures cluster around **impairment reason codes**, **tax-exempt/tolerance data**, and **split rounding**.

| Issue / signature | Root cause | Fix | Case |
|---|---|---|---|
| VL100 erroring on **PA (Pennsylvania) revenue** | Working-interest rows flagged tax-exempt incorrectly | **Script to remove the tax-exempt flag from WI** (set tax-exempt = N on the RRV deck) | 22-00638062, 22-00830841, 22-00637969 |
| **Revenue Failing to Run** / tolerance mismatch | Decimal tolerance too tight | **Create a new layer of `TOLERANT_DEC` and set it to `0.00000001`** | 24-00961978 |
| **Duplicate PPA / progressive-rounding** on VL100 (Frontier gas) | VL split put unit properties in different split jobs → progressive rounding on GMI tract calc | Fixed VL split logic so unit properties stay in the **same split job** | 22-00577329 |
| `VLCALCSPLT` fails processing **Gas & NGLs together** | Split-engine defect on combined products | Code fix | 22-00669739 |
| V17 upgrade — **System Logic Error processing Gas/NGL for same prop** | A validation (`SELECT_COUNT_RTRN_MDR_FINAL`) firing wrongly | Updated rSQL `SELECT_COUNT_RTRN_MDR_FINAL` to **always false**, disabling the over-eager validation | 25-01024334 |
| "Failed to create for **2nd DIST level PSUM** records" / RD distribution failed | Distribution data/defect | Engineering (PQID) | 22-00660634, 22-00660645, 22-00660648 |
| **Impairment reason code 302 / 314 / 540** on VL100/BKRVNU | Data condition rejecting the record (302 = master-data/cross-ref; 314 = sales record rejected; 540 = post WI-transfer impairment) | Resolve the underlying data; some are defects (e.g. 540 after WI transfer, 24-00985211) | 22-00659988, 24-00960682, 24-00985211, 26-01083253 |
| Tax-free add-back **313 "sales record is rejected"** | Master-data cross-ref size | Patch building a **temp table for tax-free add-back setup** (collapses the cross-ref) | 22-00659988, 22-00552666 |
| `RV20`/`RV40`/`RV56` missing or excessive (PPA) | Reversal-record creation defects | Code fixes | 22-00512818, 23-00898000, 25-01051141 |
| VLMIUPLOAD comingling user import batches / pushes VL032→VL031 without "Transform Data" | Import-process defect | Patch (MEW Patch 8, 2024.04) | 25-01012760, 22-00655369 |

**Fix recipe:** capture the **exact impairment reason code** (302/313/314/540) — it tells you whether it is data (fix master data / tax-exempt flag) or a defect. Two repeatable config fixes: **tax-exempt flag = N** on the RRV/WI deck (PA revenue — 22-00638062/22-00830841) and **`TOLERANT_DEC` = 0.00000001** (revenue won't run on tiny decimal mismatch — 24-00961978). Split/rounding and Gas+NGL-together are confirmed engine defects (22-00577329, 22-00669739).

---

## 6. Cluster C — QCFSEXPORT & GL/LOS export to QCFS

QCFSEXPORT exports **GL + LOS data → QCFS**, driven by the `JTRN_GL_MTD` staging table and its `GL_INTFC_COMPLETE_FL` flag. The repeatable failure is "**export brought no data / can't re-run**" because the rows are already flagged complete, plus data-quality rows (null INV_NO, over-applied).

| Issue / signature | Root cause | Fix | Case / ADO |
|---|---|---|---|
| QCFSEXPORT **"did not bring data over"** / "Revenue data did not export" for companies (e.g. 300, 310) / needs to re-run | GL interface rows already flagged complete (`GL_INTFC_COMPLETE_FL = Y`) | **Flip `GL_INTFC_COMPLETE_FL` to `N` in `JTRN_GL_MTD`** to allow reprocessing | 22-00652363, 22-00622152, 22-00684021 ("same steps as previous instances") |
| QCFSEXPORT **null `INV_NO`** error | Null invoice number in the GL staging rows | Script-review to fix/remove the offending rows | **#1737292** (Script Review, Closed — GLE) |
| QCFSEXPORT **over-applied** error | Over-applied amounts in staging | Script-review cleanup | **#1740164** (Script Review, Closed — SND) |
| QCFSEXPORT **cleanup** (CCI) | Stale/partial staging rows | Script-review cleanup | 25-01053391 / **#1766902** (Script Review, Closed) |
| "Unable to run the QCFSExport Process" | Often a lock/stuck process | §11 restart QPEC; or re-run after flag reset | 26-01065698 (resolution pattern unclear from mined cases) |
| Client running **internal scripts** on the GL staging without telling Q | Client self-modified staging → out of scope | Set expectation: future troubleshooting OOS if client scripts staging | 22-00678328 (GEC) |

**Fix recipe:** for "QCFSEXPORT didn't bring data over / need to re-run," the standard unblock is **`UPDATE JTRN_GL_MTD SET GL_INTFC_COMPLETE_FL='N'`** scoped to the company/period, then re-run QCFSEXPORT (verify-SELECT first, wrap in a transaction). For null-INV_NO / over-applied, raise a **Script Review** (these are the established WI type for QCFS staging fixes — #1737292/#1740164/#1766902). Implementing code: `QPDllRevenueAcctgJE/QPSJEExportGLtoQCFS.cpp` in `Quorum.Upstream.QRA.ClassicBatch`.

---

## 7. Cluster D — External integration / files

Outbound files and inbound network sync. Most are **export-definition / format config**, a few are defects (NAUPA format, escheat source type).

| Issue / signature | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **1099 export shows no records** (all BUs, NEC & MISC) | Import/export **definition pointed at the wrong directory** | Update the import/export definition to the correct export directory | 24-00977475 (config) |
| 1099 errors/questions / 1099 Override Address not working | Setup + an address defect | Config + fix | 22-00672711, 24-00977475, 22-00681574 / **#1388316** (EQT), **#1388257** |
| **EnergyLink file incomplete / can't generate**; EnergyLink export not excluding `RYL_PMT_TYPE='IP'` after upgrade | File-spec / filter config; upgrade regression | Config / patch | 22-00628339, 22-00640494, 25-01066966 (resolution pattern unclear for 22-00628339/22-00640494) |
| Add **Act. Balance Decimal (RD031)** to **Enverus** check file (QP043) | Enhancement to the Enverus/Enverus-check export | Config/enhancement | 24-00986412 |
| **NAUPA export not in required format**; **Current Escheat (source type 'CU')** doesn't export via NAUPA/HRS | Escheat/NAUPA format & source-type defects | Defect/hotfix (escheat hotfix delivered via FTP) | 22-00655390, 22-00655366, 22-00512447, 22-00512452 / escheat WIs **#1772217/#1787206** |
| **FI → QRA** "Unable to Sync Network Data with QRA" / "March allocations error to accounting" | Often a **locked QRA user account** blocks the FI→QRA send | Unlock the user (e.g. `WAG_QPA_USER_PRD`) and resend | 24-00941816, 26-01091972 |
| **Wells missing in QLS** | Client ran only `JDECCINTFC`, not `INT_QLSWL` | Run the **`INT_QLSWL`** process | 26-01066411 |
| `INTL_QLSWL` / `INT_QLSWL` process failure on PQID | Network-sync process error | Engineering (PQID) | 22-00682543, 22-00682545, 22-00512465 |
| AFE integration Quorum → OpenInvoice | Integration setup question | Config/answer | 26-01093512 (resolution pattern unclear from mined cases) |

**Fix recipe:** for "export produced no records," **check the export/import definition's target directory first** (24-00977475) — wrong path is the most common config cause, especially after an environment refresh. For "FI→QRA / send to accounting" errors, **check for a locked QRA service/user account** (24-00941816, 26-01091972). For "wells missing in QLS," confirm the client ran **`INT_QLSWL`** (not just `JDECCINTFC`). NAUPA/escheat format issues are genuine defects — confirm the escheat hotfix/WI build.

---

## 8. Cluster E — Check Write / OFR / ACH / netting (payments)

| Issue / signature | Root cause | Fix | Case |
|---|---|---|---|
| **Check Write "Connection Error"** / connection error during CW | MT (mid-tier) or DB server down | **Restart/start the MT server and/or check the DB server status** | 25-01042542 |
| Check Write **fails on a column** (e.g. `RTRN_CHK_RGSTR.ALT_ST_CD`) | An owner's **state/region code exceeds the column length** (e.g. `NZ-WGN` > 5 chars) | Identify the over-length owner (JE101 query on `JTRN_SL_DETAIL` ⋈ `SCTRL_BA_ADDRESS`), **exclude those owners and re-run CW** (then fix the address) | 25-01044023 |
| **Negative checks** cut for netted owners (WI + non-WI) / minimum-CW run generating negatives | Owner-inclusion / netting setup | Add the affected owners to the **owner inclusion table** and **uncheck "process all owners"** in the 4022 table, re-run CW from QP043 (avoided voiding 1,377 checks) | 22-00668080, 22-00547102 |
| **JIB netting not working** for a company / RI owners not netted | Netting config | Config **`GCDE_INT_TYPE`** (code table) to allow RI owners to be JIB-netted | 25-01061334, 22-00811692, 22-00830139 |
| **OFR not auto-processing** / "turn on automatic owner funds release" | Auto-post config off | Turn on **`AUTO_POST_OFR`** configuration | 25-01060332, 25-01045849 (25-01045849 resolution pattern unclear) |
| **OFR completed with errors / files rejected** | Data/process | Engineering (PQID); some are stuck OFR → §11 | 25-01010841 |
| **Voided check / check-write variances** | Reconciliation/report | Variance report / data review | 23-00901530, 22-00678207, 22-00678222 (resolution pattern unclear) |
| Duplicate payment to owners for **recoups** | Recoup script | **Ran provided script** in QCloud to prevent duplicate recoup payments | 23-00934662, 22-00544807 |
| Connection/Quorum-IP **`CHKFLWF`** error | Workflow/connection | Engineering | 24-00962103 (resolution pattern unclear) |

**Fix recipe:** "Connection Error during Check Write" = **infrastructure** → restart MT server / check DB (25-01042542), not a code fix. CW failing on an insert is usually a **column-length data problem** — the error names the table/column (e.g. `ALT_ST_CD`); find the over-length owner, exclude+re-run, then fix the data (25-01044023). Negative/unwanted checks for netted owners → use the **owner inclusion table + uncheck process-all-owners (4022)** then re-run QP043 (22-00668080). Netting config = code table **`GCDE_INT_TYPE`**; OFR auto-post = **`AUTO_POST_OFR`**.

---

## 9. Cluster F — SOD (Standard Owner Deck) distribution & MasterLink

SOD = a standardized owner deck; **SOD MasterLink** ties a property to its deck. Defects cluster around SOD **not paying / double-paying** and **missing MasterLinks**.

| Issue / signature | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **SOD MasterLink not paying SOD owner correctly** | MasterLink/SOD distribution defect | Code fix | 24-00944917 (0-net PPNs via VL031) / **#1655209** (Bug, Closed) |
| **SOD not distributing in DRI** when using SOD contracts | DRI+SOD distribution defect | Code change | 24-00948347, 24-00948965 |
| SOD owners **paid on both SOD and Standard contracts** (Wadestown 95-GAS) | DOI/contract setup double-counting SOD owners | Fix the contract/DOI setup | 25-01034077 (resolution pattern unclear; setup issue) |
| **SOD double paid** / SOD pricing lease-use | Distribution/pricing defect | Code/config | 22-00660676, 23-00913491 |
| RD Warning **"balancing decimal of all SOD owners has been reset to their NRI decimal"** | SOD balancing-decimal reset behavior | Often expected (decimals didn't balance → reset to NRI); confirm deck decimals | 22-00819714 (resolution pattern unclear; see FAQ) |
| **Missing SOD MasterLinks** rejecting VLPROC records | No config to choose warn-vs-reject | Config **`ONLY_CREATE_WARNINGS_FOR_MISSING_SOD_MASTERLINKS`** — `true` = warn & keep record; `false` = reject & error | 23-00904780 / **#1372503, #1388257** (Bugs, Closed) |
| DRI SOD **marketing adjustments not distributing** | DRI SOD adjustment defect | Code | 24-00948347 |

**Fix recipe:** for "SOD owner not paid / double-paid," verify the **SOD MasterLink** for the property and whether the owner is also on a Standard contract (double-count). For **missing MasterLinks blocking a run**, set **`ONLY_CREATE_WARNINGS_FOR_MISSING_SOD_MASTERLINKS = true`** (config in `QARCH_CNFG_CTRL` metadata) so VLPROC warns instead of rejecting. SOD-in-DRI distribution failures are confirmed code fixes (24-00948347, #1655209).

---

## 10. Cluster G — Contractual Allocation (CA) failures

CA / "Valuation Main Process" / VLPROC allocates via flowgrids and marketing groups. Most actionable CA cases are **DOI-warning-flag config** or flowgrid data.

| Issue / signature | Root cause | Fix | Case |
|---|---|---|---|
| **Contractual Allocation failing** / "Valuation will not close without errors" | **DOI Change Warning Flags** were checked, blocking the close | **Uncheck the DOI Change Warning Flags** | 24-00949469, 22-00824213 |
| Flowgrid **"Unknown State Code"** | Flowgrid/meter missing or invalid state code | Correct the flowgrid state code | 23-00913803 |
| CA error on a marketing group / "CA Issue on MG for a Unit" / FG failing CA | Flowgrid / marketing-group setup | Config (flowgrid/MG) | 22-00819043, 22-00661351, 22-00661358, 23-00897620, 22-00661349/350 |
| **Unable to close CA** for current month (Mars B) | Open dependency / data | Resolve dependency; close | 23-00925470 (resolution pattern unclear) |
| **PPN duplicating one well** of a flowgrid in results | Flowgrid dup defect | Code fix | 23-00924250 |
| Contractual allocation **records stuck in processing (VL040)** | Stuck/locked CA run | §11 (QPEC restart / clean) | 22-00684259 |

**Fix recipe:** the highest-yield CA fix is **uncheck the DOI Change Warning Flags** when CA/Valuation won't close (24-00949469). Otherwise verify the **flowgrid** (state code, meter membership, marketing-group setup). Stuck CA at VL040 → treat as a lock (§11).

---

## 11. Cluster H — Process health: QPEC restart, orphaned locks, stuck batches

The most operationally common unblock in the whole bucket. QRA processes acquire DB/process locks; an interrupted session leaves an **orphaned lock** and everything queues behind it.

| Issue / signature | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **Everything in QUE, nothing running, "CRITICAL / down / slow"** | A user triggered a process (often **OFR**) then closed the session → process + DB stuck | **Cancel the stuck OFR/process, restart QPECs** → all processes complete | 26-01100772 (Sandridge), 24-00992690, 22-00544805/807, 22-00897911 |
| **Orphaned locks** prevent processing until manual release | No auto-release of locks on undo/clean | **Added logic in undo/clean to release any locks tied to the revenue run being cleaned** (hotfixable); long-term: prevent orphaned locks | 22-00868629 / related #1659398 |
| **`RDCALCNEW` database locking** (recurring) | Concurrency locking | Long-term locking fix | 25-01046201 |
| "Please release lock(s) in UAT" / "QPEC restart" / "LUX UAT restart" / "stuck process" | Stuck process / lock | Release lock / restart QPEC | 23-00880754, 22-00544805, 22-00660639, 22-00512837 |
| **Records stuck in "In Interface Transfer" table** | DOI records periodically stuck | Clear/retransfer | 24-00945242 (resolution pattern unclear) |
| "Please clear out files" / clear locks | Operational cleanup | Clear files/locks | 24-00939129 |

**Fix recipe:** the standard sequence for "QRA stuck / queued / critical-down": **(1)** identify the stuck process (often an OFR or BKRVNU left by a closed session); **(2)** cancel it; **(3)** restart the **QPEC** service(s); processes then drain. If the stuck thing was a **revenue run**, run the **clean/undo** — it now releases locks tied to that run (#1659398/22-00868629). Repeat lock contention on `RDCALCNEW` is a known concurrency issue (25-01046201).

---

## 12. Cluster I — Performance & timeouts

| Issue / signature | Root cause | Fix | Case |
|---|---|---|---|
| **Revenue runs time out on GMI Calc step** | Run exceeds timeout config | **Increase the timeout configuration** to allow a longer run | 25-01023282 |
| **QQM reports time out** before DB tables are re-optimized | Stale optimization + low timeout | **Re-optimize tables**; provide latest **LCMBIAR** file with timeout-config changes | 25-01057012 |
| **BKRVNU runs indefinitely / Memory Exception / execution time** | Volume / GMI step (`USPD_MKT_GRP_GMI_CALC`) | Perf improvement to the GMI calc; batch the work | 22-00552667, 22-00674535, 24-00943638 |
| **DRI entry very slow / errors unless broken into small batches**; **VL032 save takes 15 min** | Large-batch entry / save perf | Break entry into smaller batches; perf fixes | 22-00552622, 22-00512452, 22-00688650 |
| **Batch processing time analysis** / RCA for performance | Volume / config | Perf RCA | 24-00937024, 23-00886149, 22-00868629 |
| **JEPURGE out of memory** | Purge volume | Batch / memory | 22-00512837 |

**Fix recipe:** "X times out" → first **raise the timeout config** (revenue run 25-01023282; QQM via LCMBIAR 25-01057012) and **re-optimize the relevant tables**. For BKRVNU/GMI and large DRI/VL032 entry, **batch the work** and confirm the GMI perf improvement build (22-00552667). Out-of-memory on purge/large jobs → batch and check memory limits.

---

## 13. Cluster J — Market Group / maintenance-group copy (GRPREFWEB / COPY_DVD)

Maintenance groups are refreshed (**GRPREFWEB**) then copied/approved to live (**COPY_DVD(_W)**). A failed refresh can silently empty the market-group tables.

| Issue / signature | Root cause | Fix | Case |
|---|---|---|---|
| **31 market groups deleted** after processing a DOI on a maintenance group | **GRPREFWEB** failed on a **UNIQUE KEY violation** re-inserting market-group data → left tables **empty**; then **COPY_DVD_W** copied the empty groups to live | Workaround: copy/paste market-group info from UAT to PRD; WI logged for long-term fix | 24-00982421 |
| **Market Group Issue** (code query) | Code-based SQL query referenced an **extraneous DB table** | **Remove the extraneous database table from the code-based SQL query** | 24-00995037, 24-00982421, 22-00982421 |
| **Marketing Group changing status Completed → Pending** | Status/refresh defect | Defect | 25-01014835 |
| `COPY_DVD` process issue | Copy/approve process | Engineering | 25-01031089 (DO055 comments — see §17), 23-00913273 (MEG no details) |
| "MEG 23 owner still getting deductions" / "MEG 1 no details" / RD031 MEG not working | Market/MEG group setup | Config/patch | 22-00705138, 23-00913273, 22-00653848 |

**Fix recipe:** if market groups go **empty/deleted** after a maintenance-group operation, look for a **failed GRPREFWEB (unique-key violation)** that emptied the tables before **COPY_DVD_W** promoted the emptiness to live (24-00982421). Recover by re-refreshing the group or copying from UAT; escalate for the long-term fix. The "Market Group Issue" code defect was fixed by removing an extraneous table from a code SQL query (24-00995037).

---

## 14. Cluster K — Security, Web-vs-Classic cache, code-table & column-length config

A steady stream of access and **Web≠Classic** cases. The dominant theme: **changes made in Classic / Code-Decode value maintenance don't show in Web until the Web cache is refreshed.**

| Issue / signature | Root cause | Fix | Case |
|---|---|---|---|
| Change in Classic / Code table **not reflected in Web**; dropdown won't change to textbox; country code not updating Web | **Web cache not refreshed** after the Code/Decode value-maintenance change | **Refresh the Web cache** after any Code/Decode change (26-01064758, 25-01047937); provide the cache-refresh steps | 26-01070905, 26-01064758, 25-01047937, 26-01085915 |
| **Can't update a code table** (e.g. `5002 GCD_INT_TYPE`) despite privileges | Missing **metadata layers** for the user in the code table (e.g. table 296) | Add the required metadata layers | 26-01066561 |
| **Can't log in** to Upstream | **Wrong email address** in security setup | Correct the user's security/email setup | 25-01059672, 25-01040566 |
| Maintenance-group error for a user | User repo out of sync | Run **`REPOSCRUB`** for the user | 25-01057940 |
| Confirm security objects to update Pay Codes & OFRs / privilege errors | Missing security groups | Provide/assign the correct security group list | 25-01049596 |
| Column **truncated** (cost-related, archive table length ≠ source) / `ORA-12899` saving | Column-length metadata mismatch | Align column lengths | 22-00678373, 24-00957743 (Override Address deleting) |
| SSL cert / QCloud cert questions for PRD/UAT | Cert rotation | Provide QCloud cert + SAP import steps | 25-01042517, 25-01042341 |
| Grid screen columns not aligned with filter columns; "IN" function missing on DO screens | Web/grid UI defects | Web fix | 22-00512531, 25-01061605, 25-01005683 |

**Fix recipe:** for **any "Web shows something different from Classic / my change didn't take"** → **refresh the Web cache** after the Code/Decode value-maintenance change (this resolves the majority — 26-01070905, 26-01064758, 25-01047937). For "can't update a code table despite privileges," check the user's **metadata layers** on that code table (26-01066561). For login failures, verify the **email/security setup** (25-01059672). Useful code-table references surfaced in cases: `5002 GCD_INT_TYPE` (interest type/netting), `5030` (valid JIB combinations), `16142` (QP085 contact name), `29046` (PR005 attribute type), `296` (metadata layer security).

---

## 15. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1735710** | Bug / Closed | FMO 2024.10 — DRI BKRVNU "Distribution failed" | §4 | 25-01025049 |
| **#1711649** | Bug / Closed | FMO — BKRVNU child process `RDCALC` fails | §4 | — |
| **#1725921** | Incident (Global Cloud Ops) / Closed | CEN — BKRVNU stuck at PRC | §4/§11 | — |
| **#1659398** | Bug / Closed | CNX 2022.04 — Simultaneous BKRVNU → VL reversal | §4/§11 | 24-00948965, 25-01008485 |
| **#1774912** | Bug / Closed | RLY — BKRVNU "Dual Fuel" DRIs | §4 | 25-01061195 |
| **#1709416** | Bug / Closed | ETP — Double volume found from revenue data | §5 (cross-product) | 25-00998597 |
| **#1716679** | Feature / Discarded | Upstream Performance — BKRVNU future work (dup) | §12 | — |
| **#1655209** | Bug / Closed | SOD MasterLink not paying SOD owner correctly | §9 | 24-00944917 |
| **#1372503** | Bug / Closed | Improving Missing SOD MasterLink warning messages for VL | §9 | — |
| **#1388257** | Bug / Closed | Hotfix 9 — SOD MasterLink setup required for all major products | §9 | 21-00206605 |
| **#1737292** | Script Review / Closed | GLE QRA — Null `INV_NO` QCFSEXPORT error | §6 | — |
| **#1740164** | Script Review / Closed | SND — QCFSEXPORT over-applied error | §6 | — |
| **#1766902** | Script Review / Closed | CCI — QCFSEXPORT clean up | §6 | 25-01053391 |
| **#1388316** | Requirement / Closed | EQT — 1099 QRA errors & questions | §7 | 21-00205330 |
| **#1772217 / #1787206** | Requirement / Closed & Active | QLS Agreement Mgmt, Payment — Escheat + Check Payees (UsePayCodeDefaultBy) | §7 | — |

> Many actionable cases were dispositioned **operationally** with no single product WI: QCFSEXPORT re-run via `GL_INTFC_COMPLETE_FL=N` (22-00652363), tax-exempt-flag scripts (22-00638062, 22-00830841), `TOLERANT_DEC=0.00000001` (24-00961978), `AUTO_POST_OFR` / `GCDE_INT_TYPE` config (25-01060332, 25-01061334), DOI-Change-Warning-Flag uncheck (24-00949469), QPEC restarts (26-01100772, 24-00992690), and Web cache refreshes (26-01064758, 25-01047937). Confirm exact build/patch in `Quorum.Upstream.QRA.ReleaseNotes` when stating fix availability (the SOD-MasterLink config first appears in 2020.03/2020.09/2021.04/2022.04 release notes).

---

## 16. Diagnostic SQL

> **Caveat:** QRA runs on Oracle (Classic batch) and SQL Server (some Web/upgrade clients — note the `ROLLBACK TRANSACTION` / `Sequence Contains…` errors). Table/column names below are taken from case repro text and code search; **verify against the client schema before scripting**, and always run a verify-SELECT before any DELETE/UPDATE, wrapped in a transaction.

```sql
-- A. QCFSEXPORT brought no data / need to reprocess (§6): rows already flagged complete
SELECT COMPANY, ACCTG_PERIOD, GL_INTFC_COMPLETE_FL, COUNT(*)
FROM   JTRN_GL_MTD
WHERE  COMPANY IN ('300','310') AND ACCTG_PERIOD = '<PERIOD>'
GROUP BY COMPANY, ACCTG_PERIOD, GL_INTFC_COMPLETE_FL;
-- Unblock (verify-SELECT first, wrap in a transaction):
-- UPDATE JTRN_GL_MTD SET GL_INTFC_COMPLETE_FL='N' WHERE COMPANY='<co>' AND ACCTG_PERIOD='<period>';

-- B. Check Write column-length failure (§8): find owners whose state code exceeds the column (e.g. ALT_ST_CD = 5)
SELECT SUM(D.TRANS_AMT) AS TOT, D.OWNR_BA_NO, A.STATE_CD, A.COUNTRY_CD
FROM   JTRN_SL_DETAIL D
JOIN   SCTRL_BA_ADDRESS A ON D.OWNR_BA_NO = A.BA_NO
WHERE  SL_NO = '01'
GROUP BY D.OWNR_BA_NO, A.STATE_CD, A.COUNTRY_CD
HAVING SUM(D.TRANS_AMT) <= -100
ORDER BY A.STATE_CD;   -- look for an over-length / unexpected STATE_CD (e.g. NZ-WGN). Exclude those owners, re-run CW.

-- C. Stuck / orphaned-lock triage (§11): which processes are queued / locked
--    Get the PQID(s) from the user; identify the oldest non-completed process holding the lock,
--    cancel it, then restart the QPEC service for that environment.

-- D. Impairment reason codes on a revenue run (§5): why VL100/BKRVNU rejected records
SELECT IMPAIR_RSN_CD, COUNT(*) FROM <revenue detail/impairment table>
WHERE  RRID = '<run id>'
GROUP BY IMPAIR_RSN_CD;   -- 302 master-data/cross-ref, 313/314 sales record rejected, 540 post WI-transfer

-- E. SOD MasterLink presence for a property (§9)
SELECT * FROM <SOD masterlink table> WHERE PROP_NO = '<prop>';
-- Missing MasterLink + you want warn-not-reject → config ONLY_CREATE_WARNINGS_FOR_MISSING_SOD_MASTERLINKS = true

-- F. Market-group emptied after maintenance-group refresh (§13): check GRPREFWEB / COPY_DVD outcome
--    Confirm GRPREFWEB PQID errored on a UNIQUE KEY before COPY_DVD_W ran; verify the live market-group tables are non-empty.

-- G. Code-table / metadata layer for a security or Web-vs-Classic issue (§14)
--    Check the user's metadata layers for the code table (e.g. table 296) before assuming a privilege bug;
--    after any Code/Decode value-maintenance change, REFRESH THE WEB CACHE.
```

---

## 17. Expected-Behavior / User-Education FAQ

~81 Training + ~121 Customer-Error cases sit alongside the actionable set. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| "I changed it in Classic / Code table but **Web still shows the old value**" / "dropdown won't become a textbox" / "country code not updating Web" | Customer Error — **refresh the Web cache** after the Code/Decode value-maintenance change | 26-01070905, 26-01064758, 25-01047937, 26-01085915 |
| "**Can't log in** to Upstream" | Usually wrong email / security setup, not an outage | 25-01059672, 25-01040566 |
| "I have privileges but **can't update code table 5002 / pay codes / OFRs**" | Missing **metadata layers** / wrong security group — assign the right group/layer | 26-01066561, 25-01049596 |
| "Everything is **stuck / slow / critical-down**, nothing running" | A user left a process (often **OFR**) running and closed the session → orphaned lock; **cancel + restart QPEC** (§11) | 26-01100772, 26-01091972 |
| "**Wells missing in QLS**" | Client ran `JDECCINTFC` but not **`INT_QLSWL`** — run INT_QLSWL | 26-01066411 |
| "Where do I store a **secondary TIN**?" / "template to upload new BAs?" / "BA attachment table?" | Training — Tax ID tab with a different tax-ID type; BA setup guidance | 26-01096402, 25-01061458, 26-01106366 |
| "Comments **duplicated 200 million times** in DO055" | RCA: **comments should not be made in DO055**; data-script cleanup needed | 25-01031089 |
| "RD warning: **balancing decimal of all SOD owners reset to NRI**" | Working as designed when deck decimals don't balance — verify the deck decimals (not a bug) | 22-00819714 |
| "**DOI Transfer / JIB transaction errors**" | Check **code table 5030** for valid JIB combinations | 25-01041432, 23-00879879 |
| "Negative checks / variances on Check Write" | Often netting/owner-inclusion setup, not a defect — use owner-inclusion table (§8) | 22-00668080, 22-00678207 |
| "Audit / DLL audit / how does X calculate" | Documentation/education, not defects | 26-01069230, audit requests |
| "Do we need **new SSL/QCloud certs**?" | Provide the QCloud cert + SAP import steps; cert rotation is expected | 25-01042517, 25-01042341 |

**Tell-tale it's user/expected:** a Web-vs-Classic mismatch that clears with a **cache refresh**; a login/privilege failure that is a **security-setup** error; an environment "down/stuck" that is one **orphaned lock** (restart QPEC); a "missing wells" that is a **not-run integration process**; or an audit/"how does it work" question. Verify **cache, security setup, and process locks** before treating any of these as a defect.

---

## 18. Key Code, Processes & Repos

### Processes / batch steps
| Process / step | Purpose | Notes |
|---|---|---|
| **BKRVNU** | Book Revenue (run from VL100 / Revenue Submission) | Child procs `RDCALC`/`RDCALCNEW`, GMI (`USPD_MKT_GRP_GMI_CALC`); locking & concurrency hotspot (§4/§11) |
| **VL040 (`VLCALC` / `VLCALCSPLT`)** | Value allocation / split | Split-rounding, Gas+NGL-together defects (§5) |
| **VL100** | RD distribution; creates PSUM/PPN/RV | Impairment reason codes; "2nd DIST level PSUM" (§5) |
| **VLPROC / Valuation Main Process / CA** | Contractual allocation (flowgrid / marketing group) | DOI Change Warning Flags; SOD MasterLink warn-vs-reject config (§9/§10) |
| **QCFSEXPORT** (`QPSJEExportGLtoQCFS`) | Export GL + LOS → QCFS | `JTRN_GL_MTD.GL_INTFC_COMPLETE_FL` (§6) |
| **QP043 / CW / PCW** | Check Write / Enverus check file | Owner-inclusion (4022), netting `GCDE_INT_TYPE` (§8) |
| **OFR** | Owner Funds Release | `AUTO_POST_OFR` auto-post config; common stuck-process source (§8/§11) |
| **GRPREFWEB / COPY_DVD(_W)** | Maintenance-group refresh / copy-to-live | Unique-key failure can empty market groups (§13) |
| **INT_QLSWL / INTL_QLSWL / JDECCINTFC** | Network → QLS wells / FI→QRA sync | "Wells missing in QLS" = INT_QLSWL not run (§7) |
| **JE100 / JE200 / TAXJEPOST / JEPURGE** | Journalize / post / purge | Timeouts; `JTRN_SL_DETAIL`, `JTRN_GL_MTD`, `DONL_DO_HDR` (§12) |
| **QPEC** | QRA batch/process engine service | Restart to clear stuck/locked processes (§11) |

### Code locations (confirmed via ADO code search)
| Symbol / file | Repo / path | Cluster |
|---|---|---|
| `QPSJEExportGLtoQCFS.cpp`, `QPSJSLPosting.cpp` | `Quorum.Upstream.QRA.ClassicBatch /QPDllRevenueAcctgJE/` | §6 QCFSEXPORT |
| `QPSCWPreCheckwriteFinalize.cpp` | `Quorum.Upstream.QRA.ClassicBatch /QPDllRevenueAcctgCW/` | §8 Check Write |
| `QSegProcSeveranceReporting.cs` | `Quorum.Upstream.QRA.Batch /QPDllSeveranceReporting/` | §5 severance/tax |
| `QFrmRevenueSubmission.cs` (VL100 / BKRVNU launch) | `Quorum.Upstream.QRA.ClassicGUI /Quorum.Upstream.QRA.VL/` | §4/§5 |
| `ONLY_CREATE_WARNINGS_FOR_MISSING_SOD_MASTERLINKS`, `AUTO_POST_OFR`, etc. | `<CLIENT>.Upstream.Metadata` & `Quorum.Upstream.Metadata /STANDARD 16.0/QARCH_CNFG_CTRL.json` | §9/§8 config keys |
| `QARCH_CTRL_PROCESS_PARAM.json` (QCFSEXPORT params) | `*.Upstream.Metadata /STANDARD 16.0/` | §6 |
| `BatchProcessBKRVNUTests.cs` | `Quorum.QRA.AT /Quorum.QRA.AT.Tests.UI/` (+ `Quorum.QDO.AT`) | §4 test coverage |

### Repos (see REPO_REFERENCE / REPO_INVENTORY)
- **`Quorum.Upstream.QRA.ClassicBatch`** — C++ revenue batch (`QPDllRevenueAcctgJE` = QCFSEXPORT/journal, `QPDllRevenueAcctgCW` = Check Write).
- **`Quorum.Upstream.QRA.Batch`** — managed batch (severance reporting, exports).
- **`Quorum.Upstream.QRA.ClassicGUI`** — VL screens (Revenue Submission/VL100, VL032/VL040, DR/DO screens).
- **`Quorum.Upstream.QRA.ReleaseNotes`** — confirm fix/patch versions and config-key introduction.
- **`Quorum.Upstream.Metadata` / `<CLIENT>.Upstream.Metadata`** — `QARCH_CNFG_CTRL.json` (config keys), code tables, column lengths. **Always check the client metadata/schema first** — many fixes are client-specific (config keys, column lengths, export-definition directories, custom stored procs).
- **`Quorum.QRA.AT` / `Quorum.QDO.AT`** — automated test repos (BKRVNU, reports/batch).

---

## 19. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A **BKRVNU/VL** child process crashes from code, not data/lock: `RDCALC` fails (#1711649), "Distribution failed for RD Input Group" (#1735710), Dual-Fuel DRIs (#1774912), simultaneous-BKRVNU VL-reversal (#1659398), `VLCALCSPLT` Gas+NGL-together (22-00669739), split progressive-rounding (22-00577329), "Sequence Contains More Than One…" (24-00983823).
- A **calculation/result** is provably wrong on correct inputs: SOD MasterLink not paying (#1655209), SOD-in-DRI not distributing (24-00948347), market-group empties via GRPREFWEB unique-key (24-00982421), 540-impairment after WI transfer (24-00985211), double volume (#1709416).
- An **integration format** is wrong: NAUPA format / escheat source-type 'CU' (22-00655390, 22-00655366), EnergyLink filter regression after upgrade (25-01066966).
- Provide: **PQID + failing child process + step + exact error**, client + company/BU + accounting period, the RRID / property / contract, and a repro. Confirm fix availability in `Quorum.Upstream.QRA.ReleaseNotes` and the linked WI's target build. Note SQL-Server clients surface `ROLLBACK TRANSACTION` / "Sequence Contains…" errors (upgrade clients).

**Route to Cloud Ops / handle as Configuration when:**
- **QCFSEXPORT** re-run: flip `GL_INTFC_COMPLETE_FL` to N in `JTRN_GL_MTD` (22-00652363); null-INV_NO / over-applied → **Script Review** (#1737292/#1740164/#1766902).
- **Config keys**: `ONLY_CREATE_WARNINGS_FOR_MISSING_SOD_MASTERLINKS`, `AUTO_POST_OFR`, netting `GCDE_INT_TYPE`, `TOLERANT_DEC=0.00000001`, tax-exempt-flag scripts (23-00904780, 25-01060332, 25-01061334, 24-00961978, 22-00638062).
- **CA won't close** → uncheck DOI Change Warning Flags (24-00949469).
- **Export definition** pointing at the wrong directory (1099 no records — 24-00977475); column-length / archive-table length mismatch (22-00678373).
- **Client-clone drift / client custom procs** (e.g. custom bank-reconciliation stored proc mishandling dates — 26-01063911) live in `<CLIENT>.Upstream.*`.

**Handle as process-health / operational first (no code):**
- **Stuck / queued / "critical-down"** → cancel the stuck OFR/run, **restart QPECs** (26-01100772, 24-00992690); clean/undo the revenue run to release locks (22-00868629/#1659398).
- **Check Write "Connection Error"** → restart MT server / check DB server (25-01042542).
- **Timeouts** → raise the timeout config; re-optimize tables; QQM via latest LCMBIAR (25-01023282, 25-01057012).

**Handle as Training / Expected behavior (no fix):** see §17 — **Web≠Classic → refresh Web cache** (the #1 expected-behavior cause); login/privilege = security setup; "missing wells" = INT_QLSWL not run; SOD balancing-decimal reset; JIB combinations in code table 5030; audit/"how does it work" questions.

---

*Skill created: 2026-06-14.*
*Based on: 221 actionable closed QRA "Platform_Integration_Security" SF cases (Software Defect 73 + Application Configuration 140 + ChangeConfig 8) mined for fix recipes, plus ~30 Training/Customer-Error cases for the FAQ. ADO work items #1735710, #1711649, #1725921, #1659398, #1774912, #1709416, #1655209, #1372503, #1388257, #1737292, #1740164, #1766902, #1388316, #1772217/#1787206.*
*Companion: QRA functional/valuation skills, REPO_REFERENCE.md, CONFIG_REFERENCE.md.*
