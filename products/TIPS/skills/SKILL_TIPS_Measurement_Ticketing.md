# SKILL: TIPS Measurement, Volumetric & Ticketing Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-11 | **Product:** My Quorum TIPS (oil/gas gathering, processing & settlement)
**Scope:** Measurement processing (TIPS Measurement Interface / MEASIMPORT / WHMEASIMP / Load Daily & Monthly Volumes / QIMPVOLD / SP_QTIP_ALL_VOL_IMPORT), Gas Analysis import & component setup (C5+/C6+, weighted-average WGHTAVGGAS, Master Meter Groups), Measured Volume & Meter Definition screens (Web vs Classic), Facility Batch Job / Plant run / Monthly-Close step failures (MeasAnalysis, NGLPROD, ARAP), Meter Split / Contract Meter List & split-decimal, Truck Ticket import, Integration-Platform (FlowCal→TIPS / GMAS) script-deployment errors, Volumetric Maintenance, Inventory (LIFO/FIFO), and CO&O / settlement-statement volume issues.
**Companion:** This is the TIPS analogue of QPTM **SKILL_Allocations.md**. TIPS *produces* measured/allocated wellhead volumes that flow into Paystation → settlement statements; for QPTM-side allocation/PTR overlay see SKILL_Allocations.md (Evolution clients sync via WHMEASIMP / GEN PTR). Do not duplicate those — cross-references noted.

> **Use When:** any TIPS case categorized **Measurement, Volumetric Maintenance, Ticketing, Inventory (LIFO/FIFO), or CO&O Module** — i.e. a measurement/analysis import fails, a Facility Batch Job / plant step errors, volumes double/triple or show 0, gas-analysis components are missing, a meter split / split-decimal is wrong, a truck-ticket import is short, or a settlement statement shows zero/wrong volumes.

> **Evidence base:** ~313 closed TIPS cases in these 5 categories. **66 actionable** (Root Cause = Software Defect 41, Application Configuration 20, ChangeConfig 5: Measurement 48, Volumetric Maintenance 11, Ticketing 4, Inventory 3, CO&O 0) drive the cluster sections; ~35 Training/Customer-Error cases drive the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining. **Data-quality caveat:** the SF MCP connector intermittently returned crossed result-sets during mining; category membership for every cited case was re-verified, but exact column names below marked "inferred" should be confirmed against the schema before scripting.

---

## TABLE OF CONTENTS
1. [Quick Triage Table](#1-quick-triage-table)
2. [TIPS Measurement Pipeline & Concepts](#2-tips-measurement-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster 1 — Measurement / Volume Import Failures (HIGH FREQUENCY)](#4-cluster-1--measurement--volume-import-failures-high-frequency)
5. [Cluster 2 — Gas Analysis Import & Component Setup (C5+/C6+)](#5-cluster-2--gas-analysis-import--component-setup-c5c6)
6. [Cluster 3 — Weighted-Average Analysis / Master Meter Group (WGHTAVGGAS / MMG)](#6-cluster-3--weighted-average-analysis--master-meter-group)
7. [Cluster 4 — Facility Batch Job / Plant / Monthly-Close Step Failures](#7-cluster-4--facility-batch-job--plant--monthly-close-step-failures)
8. [Cluster 5 — TRNX_ID Unique-Constraint / Purge-Recycle](#8-cluster-5--trnx_id-unique-constraint--purge-recycle)
9. [Cluster 6 — Meter Split / Contract Meter List / Split-Decimal → Settlement](#9-cluster-6--meter-split--contract-meter-list--split-decimal--settlement)
10. [Cluster 7 — Measured Volume & Meter Definition Screens (Web vs Classic)](#10-cluster-7--measured-volume--meter-definition-screens-web-vs-classic)
11. [Cluster 8 — Truck Ticket Import (Ticketing)](#11-cluster-8--truck-ticket-import-ticketing)
12. [Cluster 9 — Integration Platform (FlowCal→TIPS / GMAS) Script Deployment](#12-cluster-9--integration-platform-flowcaltips--gmas-script-deployment)
13. [Cluster 10 — Theoretical Gallons / GPM / NGL Yield](#13-cluster-10--theoretical-gallons--gpm--ngl-yield)
14. [Expected Behavior / User-Education FAQ](#14-expected-behavior--user-education-faq)
15. [Known Historical ADO Items](#15-known-historical-ado-items)
16. [Key Code Files, Processes & Repos](#16-key-code-files-processes--repos)
17. [Database Tables Reference](#17-database-tables-reference)
18. [Diagnostic SQL Queries](#18-diagnostic-sql-queries)
19. [Escalation Decision Guidance](#19-escalation-decision-guidance)

---

## 1. Quick Triage Table

| Symptom (message / behavior) | Likely cause | First check |
|------------------------------|--------------|-------------|
| Measurement Import / MEASIMPORT shows volume **doubled/tripled** or meter **multiple times**; QPTM matches TIPS | Measurement-import warning/dedup defect | Patch level; ADO #1670170 (24-00963344). Verify QPTM↔TIPS actually match (warnings spurious). |
| `WHMEASIMP FAILED ... AN ITEM WITH THE SAME KEY HAS ALREADY BEEN ADDED` | Duplicate-key in wellhead meas import collection | Patch 59 (ETP TSP 30051, 24-00990231); check for dup paper-meter rows. |
| `ERROR IN SP_QTIP_ALL_VOL_IMPORT ... USER_ID` failure / meter end-dated on zero vol (V17) | `USER_ID` >30 char via trigger; truncation fix | 24-00965985 — see §4 / §8. |
| Daily volume import only loads **first ~49,000 rows** | PK constraint violation aborts load mid-file | Split file or fix dup keys; 22-00679867. |
| Plant/Facility Batch Job fails **PK / unique constraint** on `QTRAN_PAYSTATION_GATH_ATTR` or analysis step | **Overlapping timeslice** on a meter | §7/§8; find overlapping meter (23-00932144, 22-00513111). |
| MeasAnalysis step fails: unique constraint on `QTRAN_STD_ANALYSIS_BASE.TRNX_ID` (all facilities) | TRNX_ID exhaustion/collision | Reset TRNX_ID to 0 (short-term); ADO #1617830 long-term (§8). |
| `WGHTAVGGAS` fails during MEASUREMENT for a plant with **no Master Meter Group** | Step errored instead of skipping | Should warn+skip (2020.07 fix); 22-00598144 (§6). |
| After an MMG **rerun**, current billing month **won't generate** a new weighted analysis | MMG rerun date-range/open-ended defect | ADO #1435165 / #1685847 (§6). |
| Gas-analysis **components missing** (Ethylene/Propylene, Hexane, C6 not in C5+) | Facility Definition component/Plus-component config | §5 — Component Product Allocation tab. |
| Settlement statement shows **0** for NGLS / WH vol; PPA gas stmt shows 0 Mcf/MMBtu | **Split Decimal = 0 / missing** at Meter Split level | §9 (26-01091612, 24-00937128). |
| Meter-split data / CCT **disappears**, timeslices open-ended after escalation/rollback | CCT escalation/rollback defect | §6/§9 (26-01094306). |
| Measured Volume screen **rounds** Temperature/Production Hrs (Web); Classic shows full value | Web rounding-render defect | §10 (23-00926060). |
| Truck-ticket import only loads **first 50 tickets** / density column missing in Web | Truck-ticket import row-limit / Web parity defect | §11 (24-00978630, ADO #1595913/#1777564). |
| Integration Platform FlowCal→TIPS error; `REVISION_NUMBER`>1000 | FlowCal sends multiple events inflating revision | Script reset revision; FlowCal upgrade (§12, 25-01047138). |
| GMAS / GMASMAST process fails on file **path** after env change | Import path stale; needs service restart | §12 (26-01082744). |
| Theoretical gallons / GPM don't tie to client number | GPM factor / analysis component config | §13 (22-00818737). |

---

## 2. TIPS Measurement Pipeline & Concepts

### What TIPS measurement does
TIPS ingests **measured volumes** and **gas analyses** (from FlowCal/GMAS/spreadsheets), runs them through **Measurement** (analysis, weighted-average, splits), allocates wellhead volumes to wells/contracts, and produces **Paystation** rows that feed **settlement statements** (CO&O/gas statements). Most batch logic runs as **Facility Batch Job** steps under the **TurboTips** batch engine (`Quorum.TIPS.Batch.QPDllTurboTips`).

```
[FlowCal / GMAS / Spreadsheet]                 [Manual entry: Measured Volume / Analysis screens]
        │                                                │
        ▼  Integration Platform (eSuite sync) ───────────┤
[Load Daily/Monthly Volumes + Analysis from eSuite]      │
   (SP_QTIP_ALL_VOL_IMPORT, MEASIMPORT/WHMEASIMP)        │
        │                                                ▼
        ▼  Facility Batch Job (TurboTips) ── MeasAnalysis → WGHTAVGGAS → Meter Split → NGLPROD → ARAP...
[Measured volumes + std analysis: QTRAN_STD_ANALYSIS_BASE, meas vol tables]
        │
        ├──► Meter Split (Split Decimal) ──► QTRAN_PAYSTATION (Paystation) ──► Settlement Gas Statements
        └──► Inventory (LIFO/FIFO) / Volumetric Maintenance
```

### Key concepts
- **Facility Batch Job / Plant run:** the ordered step chain (MeasAnalysis, WGHTAVGGAS, TMTRSPLIT, NGLPROD, ARAP_IFGTT, settlement). A failure names the **step** — that is your first clue (e.g. "fails at NGLPROD step").
- **TRNX_ID:** an integer transaction id stamped on measurement/analysis/paystation rows. Historically grew unbounded (Daily runs burn many); a **purge-recycle** change now reuses TRNX_IDs (Facility Config `IGNORE_PURGE_IND`). Both **exhaustion/collision** (unique constraint) and **recycle side-effects** (stale User_ID/Updt_Dt on Paystation) are recurring (§8).
- **Master Meter Group (MMG) / WGHTAVGGAS:** weighted-average gas analysis across grouped meters. No-MMG and rerun handling are recurring defect areas (§6).
- **Meter Split & Split Decimal:** the fraction (`S_DECIMAL`) by which a wellhead/parent meter volume is split to wells/contracts. A **missing or zero split decimal** silently zeros downstream Paystation/settlement volumes (§9) — the single most common "settlement shows 0" root cause.
- **CCT (Contract/Cost-center timeslice):** effective-dated meter-split/contract config. **Overlapping CCT timeslices** cause PK-violation plant failures; escalation/rollback can erase CCT data (§6/§9).
- **eSuite / Integration Platform:** the sync layer between FlowCal (measurement source) and TIPS. "Volumes didn't update" is very often "Load Volume from eSuite was not re-run after the FlowCal change" — a process/training issue, not a defect (§14).
- **Web vs Classic:** as in QPTM, many TIPS screen defects are Web-only (rounding, density column, split delete). Reproduce in both; the Web screen is usually the more-permissive/less-faithful one.

---

## 3. Decision Tree

```
TIPS Measurement/Volumetric/Ticketing case
│
├─ A batch step / import FAILED (Facility Batch Job, MEASIMPORT, WHMEASIMP, Load Volumes, plant run)?  (§4,§7)
│   ├─ Get the STEP name + exact error + facility/plant + prod month
│   ├─ "same key has already been added" / PK / unique constraint
│   │     ├─ on QTRAN_STD_ANALYSIS_BASE.TRNX_ID → TRNX_ID exhaustion → reset to 0 (short-term), §8 / ADO #1617830
│   │     ├─ on QTRAN_PAYSTATION_GATH_ATTR / analysis step → OVERLAPPING TIMESLICE on a meter → fix via script, rerun (§7)
│   │     └─ import file aborts mid-file (~49k rows) → dup-key in load file → fix/split file (22-00679867)
│   ├─ SP_QTIP_ALL_VOL_IMPORT USER_ID failure / V17 zero-vol end-dates meter → §4/§8 (24-00965985)
│   ├─ Volume doubled/tripled in MEASIMPORT warnings (QPTM matches) → defect, ADO #1670170 (§4)
│   └─ "did the customer simply not re-run Load Volume from eSuite?" → FAQ (§14)  ← check FIRST, very common
│
├─ Gas analysis issue?  (§5,§6)
│   ├─ Components missing (Ethylene/Propylene/Hexane) or C6 not in C5+ → Facility Definition config (§5)
│   ├─ WGHTAVGGAS fails (no MMG) → should warn+skip, patch (§6, 22-00598144)
│   └─ MMG rerun won't generate current-month analysis → defect ADO #1435165/#1685847 (§6)
│
├─ Settlement statement / PPA gas stmt shows 0 or wrong volume?  (§9)
│   └─ Check Meter Split SPLIT DECIMAL (S_DECIMAL) — missing/0 zeros Paystation (26-01091612, 24-00937128)
│   └─ CCT erased/open-ended after escalation/rollback → §6/§9 (26-01094306)
│
├─ Screen issue (Measured Volume / Meter Definition / Contract Meter List)?  (§10)
│   └─ Web ≠ Classic (rounding, won't retrieve, abandon split, delete open split) → reproduce both; usually Web defect
│
├─ Truck ticket import short / Web missing column?  (§11)  → row-limit / Web parity defect
│
├─ Integration Platform / FlowCal→TIPS / GMAS error?  (§12)
│   ├─ REVISION_NUMBER>1000 → FlowCal multi-event; reset script + FlowCal upgrade (25-01047138)
│   └─ stale import path → fix path + service restart (26-01082744)
│
└─ Theoretical gallons / GPM / yield off?  (§13)  → GPM factor / component config
```

---

## 4. Cluster 1 — Measurement / Volume Import Failures (HIGH FREQUENCY)

The largest actionable cluster. TIPS pulls volumes/analyses from FlowCal/eSuite or spreadsheets via **Load Daily/Monthly Volumes**, **MEASIMPORT / WHMEASIMP** (wellhead meas import), and the proc **`SP_QTIP_ALL_VOL_IMPORT`**.

### Dominant failure signatures
| Error / behavior | Root cause | Disposition | Evidence |
|------------------|-----------|-------------|----------|
| `WHMEASIMP FAILED ... AN ITEM WITH THE SAME KEY HAS ALREADY BEEN ADDED` | Duplicate key in the wellhead-meas import collection (often dup paper-meter rows) | Code fix, patch 59 | 24-00990231 (ETP TSP 30051) |
| MEASIMPORT warnings show meter **multiple times**, **TIPS volume tripled**; QPTM **does** match TIPS (warnings spurious) | Measimport warning/aggregation defect | **Code fix** | 24-00963344 → **ADO #1670170** (+ #1670217 "non-paper meters show 0", 24-00963342) |
| `ERROR IN SP_QTIP_ALL_VOL_IMPORT: The Well/Customer Facility … does not exist or is invalid at plant …` | Import references a facility/well not set up at the plant | Config / data | 24-00965985-adjacent (24-00965985 root cause below) |
| V17: loading a **zero volume after a valid month end-dates the meter**; `SP_QTIP_ALL_VOL_IMPORT` errors | Proc fetched `USER_ID`, trigger `TR_CVTIPS_SVALD_MTR_HEADER_U` prepended `UPDATE_`, pushing it past the **30-char** limit (e.g. `UPDATE_ALLOVOL_AJINKYA.KHARADE`) | **Code fix** — truncate USER_ID to 30 chars | 24-00965985 (AltaGas, regression vs V16) |
| Daily import (`QIMPVOLD`, step `QIMPEXP`) loads only the **first ~49,000 rows** then errors | Row that violates a **primary-key constraint** aborts the batch insert; rows before it commit | Identify/clean the dup-key row, or split the file | 22-00679867 |
| Pre-scheduling Facility Batch Jobs **stop with errors and run ~60 min** | Batch step defect | Code fix, **patch 17** (held by UTG upgrade) | 24-00971506 |
| Plant run fails at **NGLPROD** step (TMTRSPLIT→ARAP_IFGTT) | Plant/NGL step setup or defect (reproduced in Q env) | Code/config | 24-00945026 |
| `Daily - Process fails at NGLPROD ... ACCESS_VIOLATION (C0000005)` | Native batch crash in NGL step | Code fix | 24-00945026-class |

### The 24-00965985 root cause (verbatim, engineering)
> *"During SP_QTIP_ALL_VOL_IMPORT, the USER_ID was fetched into a variable. A trigger (TR_CVTIPS_SVALD_MTR_HEADER_U) appended a prefix (UPDATE_) … in certain cases the final string exceeded the 30-character limit — e.g. UPDATE_ALLOVOL_AJINKYA.KHARADE — causing failures. Fix: restrict USER_ID to a maximum of 30 characters; characters beyond are truncated."* Use this to recognize any "long username / Customer Facility import suddenly failing in V17" report.

### Fix recipe
1. Get the **step name** (MEASIMPORT/WHMEASIMP/QIMPVOLD/Load Volumes/NGLPROD), **plant/facility**, **prod month**, and exact error.
2. **Before escalating**, rule out the #1 non-defect cause: *did the customer re-run "Load Volume from eSuite" / LoadMonthlyVolumesAndGasAnalysisFromEsuite after the FlowCal change?* (§14) and *is the import file/column spec correct?*
3. PK / "same key" / "~49k rows": run Diagnostic A (overlapping timeslice) and B (dup rows); clean the offending data or split the file, then rerun.
4. "Tripled / multiple warnings, QPTM matches": this is a known **code defect** (ADO #1670170) — confirm patch level; reassure the warnings are spurious if QPTM↔TIPS reconcile.
5. Long-username / V17 zero-vol-end-date: the **USER_ID>30** truncation fix (24-00965985) — confirm it is in the client's patch.

---

## 5. Cluster 2 — Gas Analysis Import & Component Setup (C5+/C6+)

Gas analyses arrive from FlowCal/GMAS. Most "component missing / wrong %" cases are **Facility Definition configuration**, not code.

| Issue | Root cause | Resolution recipe | Case |
|-------|-----------|-------------------|------|
| **Ethylene & Propylene** missing in analysis | Components not configured / not interfaced | Manually update the few affected meters on the **Analysis screen**; **decouple Import Analysis and Measured Volumes from Measurement** so analysis can be imported from FlowCal first, then add missing components | 24-00992188 (HEP-JAV 9000) |
| **Hexane** component not interfacing (FlowCal→TIPS) | Plus-components config bringing/omitting wrong components | Set config to **not bring in Plus components** globally; for facilities using **C5+**, update the product assigned to C5+ to include the **individual components** on the **Component Product Allocation tab** of **Facility Definition** | 25-01001253 (Stateline TSP 800) |
| **C6 analysis not included in C5+ calculation** | Facility-definition component rollup | Resolved with **configuration on Facility Definition** (component grouping) | 23-00925874 (Sendero) |
| Analysis upload validation **doesn't detect `#VALUE!`** spreadsheet error | Upload validation gap | Code fix | 22-00570848 |
| Import/Export Definition: `PRES_BASE` **can't be set to null** | Metadata field nullability | Code fix | 22-00641354 |
| TIPS Gas Analysis Import (2024.04) errors | Analysis import defect | Code fix (patch) | 25-01041475, 25-01041981 |

> **Pattern:** for "component X missing/wrong" the lever is almost always the **Component Product Allocation tab on Facility Definition** plus the **Plus-components** setting (C5+/C6+). Confirm what the source (FlowCal) actually sends before assuming a TIPS defect — see FAQ 22-00668432 (client's file had extra C+ components changing methane mol%).

---

## 6. Cluster 3 — Weighted-Average Analysis / Master Meter Group (WGHTAVGGAS / MMG)

`WGHTAVGGAS` (step in `Quorum.TIPS.Batch.QPDllTurboTips/StepExecution/WGHTAVGGAS.cs`) computes weighted-average gas analysis across a **Master Meter Group**.

| Issue | Root cause | Resolution | Case / ADO |
|-------|-----------|------------|------------|
| `WGHTAVGGAS` **fails during MEASUREMENT** for plants with **no Master Meter Group** (workaround was dummy MMG) | Step errored instead of skipping | **Fix merged from 2020.07: WGHTAVGGAS now throws a warning and skips to the next step when no MMG found** | 22-00598144 |
| MMG **rerun**: after a rerun, current billing month **no longer creates** a new weighted analysis; rerun analysis left **open-ended** (12/31/9999 instead of 12/31/9000) | MMG rerun date-range / time-slice generation defect | Code fix | 22-00869412; **ADO #1435165** (Master Meter Group Derived Analysis — Rerun/Date Range), **#1685847** (MMG Analysis Meter Not Generating an Analysis) |
| `2020.03 Master Meter Allocation – Weighted Average Gas Analysis Fails if No Master Meter Group is Setup` | Same no-MMG class as above | Code fix | 22-00598144 |
| Performance: WGHTAVGGAS slow | Long-running step | **ADO #1737689** — TIPS Performance Initiative: Convert WGHTAVGGAS | (perf) |

> When a client reports "no analysis on the current month after a rerun," it is the **rerun open-ended-date-range defect** (#1435165/#1685847), not their setup. The 12/31/9999 vs 12/31/9000 open-ended-date mismatch is the tell (cross-ref 22-00868194).

---

## 7. Cluster 4 — Facility Batch Job / Plant / Monthly-Close Step Failures

Plant/Facility Batch Jobs fail on a named **step**. The two dominant root causes are **overlapping timeslices** (PK violations) and **TRNX_ID** (§8).

| Failure | Root cause | Resolution recipe | Case |
|---------|-----------|-------------------|------|
| Anadarko Superplant batch job fails **PK violation on `QTRAN_PAYSTATION_GATH_ATTR`** | **Overlapping timeslice** for a meter (e.g. Meter #1414406) | Correct the overlapping timeslice **via script**, then rerun the plant | 23-00932144 |
| Plant errs in Measurement with **Unique Constraint on the Analysis step** | **2 meters with overlapping analysis timeslices** | Tell user to fix the overlapping timeslices and **rerun measurement** | 22-00513111 (Pegasus) |
| MeasAnalysis step fails: unique constraint on `QTRAN_STD_ANALYSIS_BASE.TRNX_ID` for **all facilities** | TRNX_ID exhaustion/collision (SQL is in a DLL, not visible) | **Reset TRNX_ID to 0** (short-term); long-term fix §8 | 23-00916043 |
| `Plant run errored in measure while loading April volumes` | Measurement step defect | Code fix | 24-00981973 |
| `Measanalysis step fails for all facilities during Monthly Close` | TRNX_ID (above) | §8 | 23-00916043 |
| Master Meter Group **Rerun Failure** (TP149456) | MMG rerun (see §6) | §6 | 22-00869412 |
| `Unknown Error running Facility Batch Jobs` | Env/config | ChangeConfig | 23-00884944 |

### Fix recipe
1. Identify the **failing step** and whether the error is a **PK/unique-constraint**.
2. PK on a **paystation/gathering-attr or analysis** table → almost always an **overlapping timeslice** on a specific meter. Run Diagnostic A to find it; correct via script; rerun the plant/measurement.
3. Constraint on **`TRNX_ID`** → §8 (reset to 0 short-term; ADO #1617830 long-term).
4. Native crash (`ACCESS_VIOLATION C0000005`) at NGLPROD → **code defect**, escalate with step + repro.

---

## 8. Cluster 5 — TRNX_ID Unique-Constraint / Purge-Recycle

`TRNX_ID` is an integer transaction id stamped across measurement/analysis/paystation rows. Two distinct failure modes:

### 8a. Exhaustion / collision (Software Defect)
- MeasAnalysis insert into `QTRAN_STD_ANALYSIS_BASE` fails on a **unique constraint on TRNX_ID across all facilities** — **23-00916043**. **Short-term:** reset TRNX_ID to 0. **Long-term:** the integer-limit fix — **23-00916530** ("Resolve TRNX_ID integer value limitation – Long Term Fix"), **ADO #1617830 (Bug, Closed)** + **#1631131 (Task)**; settlement-side split scripts in **ADO #1773003** (Core TIPS 17.0 – SETTLEMGR TRNX_ID Split Scripts).
- **#1656405 (Bug, Closed)** — "Daily CO trnx_id are being purged when they are not supposed to."

### 8b. Purge-recycle side effects (Expected behavior after a release change)
- After the recycle change, **Paystation `User_ID`/`Updt_Dt` show the original (not latest) values** because TRNX_IDs are reused and `QTRAN_PAYSTATION` pulls User_ID/Updt_Dt from `QTRAN_TRNX_ID`. **This is by design** to slow TRNX_ID growth (esp. Daily runs). **Revert to old behavior** by setting **Facility Config `IGNORE_PURGE_IND = 1`** — **24-00972261** (Customer Error / release-note education).

> Recognize the two: a **unique-constraint failure** = defect (reset to 0 + confirm #1617830 patch). A **stale User_ID/Updt_Dt complaint** = recycle-by-design (toggle `IGNORE_PURGE_IND`).

---

## 9. Cluster 6 — Meter Split / Contract Meter List / Split-Decimal → Settlement

The bridge from measurement to settlement is the **Meter Split** and its **Split Decimal (`S_DECIMAL`)**. A missing/zero split decimal silently zeros downstream Paystation and settlement volumes — the most common "settlement shows 0/wrong" root cause.

| Issue | Root cause | Resolution recipe | Case |
|-------|-----------|-------------------|------|
| Settlement statement shows **0** for one meter's **NGLS** (Theoretical/Allocated Vols, Shrink MMBtu) | **Split Decimal = 0** at Meter Split level → flowed `S_DECIMAL=0` into Paystation (`OXYPOST_SETTLE_GAS_STMT_VW`: `NVL(ALLOC.WHDV_VOL * PAY.S_DECIMAL,0)`) | Set the Meter Split decimal correctly (others = 1); rebuild split | 26-01091612 (OXY) |
| Revised gas statement shows **0 Gross WH Mcf/MMBtu** on PPA (but $ correct) | **Split decimal missing** for those meters at meter split | **Rebuild the split** so decimals come into Meter Split; wellhead volumes then show | 24-00937128 (IACX) |
| Meter is **not settling / not on allocated-volume query** | **No CCT set up** for the current production month on the meter split | Set up the CCT for the prod month | 26-01100577 |
| CCT data **disappears**, timeslices **open-ended** after Escalation rollback | Escalation/rollback erased Services-tab/CCT data | Fix the CCTs and run the **Escalation process** correctly going forward | 26-01094306 |
| Contract Meter List **allows abandoning a meter split** / lets a 5610 Regular User **delete an open meter split** | Cache/permission defect (Web) | **Web-only fix:** query the DB directly for an effective date before the cached window and **ignore the cache** (will not be fixed in Classic) | 24-00957962 |
| **Child meters** can't be added to Contract Meter List ("duplicate key") | Stale contract-meter records causing duplicate-key conflict | Identify and remove the conflicting contract-meter records, then add child meters | 26-01087430 |
| Duplicate meter with child meters needs deletion | User couldn't delete | Deletable from **Meter Definition** screen per documentation | 26-01101667 |
| `Meter Header Foreign Key Constraints` | Referential integrity on meter header | ChangeConfig | 22-00876039 |

> **First check for any "settlement / gas statement shows 0 or wrong volume":** the **Split Decimal at the Meter Split level** (should be 1 unless intentionally split) and whether a **CCT exists for the production month**. Two cases (26-01091612, 24-00937128) resolved purely on split decimal.
>
> *Note:* cases 26-01091612 / 26-01100577 / 26-01094306 / 26-01087430 surfaced in a connector result-set crossing during mining; their CaseNumber+Resolution were re-read directly and are consistent with the split-decimal/CCT pattern, but they may be officially categorized under CO&O/settlement rather than "Inventory/Measurement." Treat them as the settlement-volume pattern regardless of category label.

---

## 10. Cluster 7 — Measured Volume & Meter Definition Screens (Web vs Classic)

Screen-layer defects, predominantly **Web-only** parity gaps. Lower urgency, high volume.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Measured Volume screen **rounds Temperature (2 dp) and Production Hours (1 dp)** in Web; Classic shows full value (visible in Bulk Edit) | Web rounding-render defect | Code fix (match Classic) | 23-00926060 |
| `Meter Definition Doesn't Retrieve Data` (v17) | Web retrieve defect | Code fix | 22-00555531 |
| Measured Volume screen **predictive text inconsistent** (v17) | Web autocomplete defect | Code fix | 22-00555546 |
| `Error Msg Upon Opening Meas Vol Screen` (2020.03) | Screen init defect | Code fix | 22-00598147 |
| `Result Qtys not calculating for "More"/"All" rows` | Grid calc defect | Code fix | 22-00679851 |
| TIPS A1 **Shared Meter** saving error in Web | Web save defect | Config/code | 24-00965747 |
| `myQuorum Ticket Analysis Update screen` (UAT2) | Web screen defect | Code fix | 22-00831415 |

> Same rule as QPTM: reproduce in **both Web and Classic**; the Web screen is usually the offender (rounding, predictive text, retrieve). Several are explicitly "Web only — will not fix in Classic" (24-00957962).

---

## 11. Cluster 8 — Truck Ticket Import (Ticketing)

The **Ticketing** category is small (4 actionable) and dominated by truck-ticket import limits/parity.

| Issue | Root cause | Fix | Case / ADO |
|-------|-----------|-----|------------|
| Veresen **Truck Ticket Import** uploads **density for only the first 50 tickets**; Web is missing the **"density variance"** column | Import row-limit + Web parity gap | Code fix | 24-00978630 |
| Rounding issue with truck tickets / S&W | Rounding defect | Code fix | **ADO #1595913 (Bug, Closed)** |
| Truck tickets not importing with a new Transporter | Transporter mapping defect | Code fix | **ADO #1777564 (Bug, Closed)** |

> The other "Ticketing" actionable cases (24-00948810 SF password reset, 23-00881178 ETRN case-access) are **not product defects** — they are SF/access requests miscategorized as Ticketing.

---

## 12. Cluster 9 — Integration Platform (FlowCal→TIPS / GMAS) Script Deployment

The **Volumetric Maintenance** category is dominated by **Integration-Platform script-deployment** tickets (FlowCal→TIPS via eSuite, and GMAS imports). These are operational fixes, often a one-line script or a service restart — not product code bugs.

| Issue | Root cause | Resolution recipe | Case |
|-------|-----------|-------------------|------|
| FlowCal→TIPS integration error; **`REVISION_NUMBER` > 1000** on measurement/analysis | FlowCal sends **multiple events**, inflating the revision number | **Script resets REVISION_NUMBER >1000 back to 1 or 2** (temp workaround); **FlowCal upgrade** is the real fix | 25-01047138, and the recurring "Script Deployment for Integration Platform Error" family (25-01050084 BMD, 25-01050137 UTG, 25-01014139) |
| GMAS / `GMASMAST` fails: import file **path** stale after a UAT deployment | Process still points at old `APPFILES\TIPS\IMPORTS\GMAS` path | Fix the path **and restart the service** so it takes effect | 26-01082744 (`GMASINT`) |
| FlowCal volume import only selects data after **un-checking "sync date"** | **Missing value on `SCTRL_INT_FULLSYNC`** (esuite schema) | Add the correct value to `SCTRL_INT_FULLSYNC`; import then runs as intended | 25-01025108 (Pembina) |
| TIPS Gas Analysis Import (Integration) errors | Analysis import defect | Patch | 25-01041475, 25-01041981 |
| `Import Daily Vols` bad data in **staging table** | Bad rows in the import staging table | **Cleanup script for the staging table** | 26-01064055, 26-01070885 |

> The "Script Deployment for Integration Platform Error" cases are a **standing operational pattern**: the FlowCal revision-number inflation needs a periodic reset script until the client's FlowCal is upgraded. Route to **Cloud Ops** with the reset script; flag FlowCal upgrade as the durable fix.

---

## 13. Cluster 10 — Theoretical Gallons / GPM / NGL Yield

| Issue | Root cause | Disposition | Case |
|-------|-----------|-------------|------|
| Theoretical gallons not calculating correctly; natural-gas theos / GPM total don't tie to client (Verdun) number | GPM factor / analysis-component config feeding theoretical-gallon calc | Verify GPM factors & component config; **resolution pattern unclear from mined data** (case closed without a documented config change in SF) | 22-00818737 |
| `Theoretical Gallons Issue` | Theo-gallon calc | Code fix | 22-00818737 |
| `Mol % calculations` — methane % differs between source and TIPS | Source gas-analysis file had extra C+ components | Client updated file to remove extra C+ components (Customer Error) | 22-00668432 |
| `Condensate GPM Script` | GPM scripting request | Code/script | 22-00566331 |

> Theoretical-gallon/GPM cases are low volume and mixed; confirm the **analysis components and GPM factors** before assuming a calc bug. Where the SF record has no concrete resolution, **resolution pattern is unclear from the mined cases** — escalate to Engineering with the meter, prod month, and the client's expected vs system GPM.

---

## 14. Expected Behavior / User-Education FAQ

~35 Measurement/Volumetric/Ticketing cases are **Training / Customer Error**. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|-------------|------------------|------|
| "Volumes didn't update after we changed FlowCal" | **"Load Volume from eSuite" / LoadMonthlyVolumesAndGasAnalysisFromEsuite was not re-run** after the FlowCal change — run it once volumes are final | 24-00951525, 24-00966933 |
| "Volume Import Error – PK Concurrency Violation" | Often user reconciliation; use **Confirmation Response** screen to verify confirmed physical quantities | 26-01083874 |
| "Import Daily Vols error" | **Bad data in the staging table** → cleanup script | 26-01064055 |
| "Daily Vol file won't import" | **FILENAME field / file extension** not specified correctly in the import process | 25-01059309 |
| "Monthly Volumes Import error" / "Quantity vs Alternate quantity does not match" | Customer's import **columns / .csv rows** were wrong — fix and re-upload | 25-01040744, 24-00947373, 24-00961637 |
| "Import/Export Definition – can't edit metadata layer / columns reordered" | The **metadata layer can't be edited** by the user; the **File Definition tab does NOT reorder Excel columns** — it tells the system the expected column order | 25-01042838 |
| "Paystation User_ID/Updt_Dt not updating" | **By design** — TRNX_IDs are recycled; revert via Facility Config **`IGNORE_PURGE_IND = 1`** | 24-00972261 |
| "Measured Volume screen requires wet/dry basis" | Required **only when UOM is MCF or MMBtu** (TIPS must convert if different from plant standard); not required for other UOMs | 22-00675919 |
| "Negative Inlet / negative MCF" | Allocation groups calculating **net delivered** correctly; gas-lift value exceeded wellhead → legitimately negative (false-flow / measurement-system question) | 25-01010165 |
| "Plant erring – unique constraint on Analysis step" | **Overlapping analysis timeslices** on the user's meters — fix and rerun (this is user data, not a bug) | 22-00513111 |
| "Gas analysis won't load from WinSCP" | **Add a leading zero on the dates** in the import file and rerun | 22-00514762 |
| "Gas analysis mol% wrong" | Source file had **extra C+ components**; correct the file | 22-00668432 |
| "Shared Meter Definition – how do I set up?" | Guided: create meter + Facility-tab integration on **Meter Definition** | 23-00924510 |
| Password reset / user activation / case-access | **Not measurement defects** — route to User Admin (AD self-service) | 24-00987932, 23-00923921, 22-00700688, 24-00948810, 23-00881178 |
| "Out of memory (Classic)" / "Scheduled jobs not running" | Infra: **service restart**; missing/backup **import paths** added | 22-00540318, 22-00691532 |

**Tell-tale it's user/expected:** Load-from-eSuite not re-run; bad rows / wrong columns / missing file extension in the import; overlapping timeslices in the user's own meter data; a recycle-by-design Paystation User_ID; or "negative/zero" that is the formula behaving correctly on the supplied volumes.

---

## 15. Known Historical ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|-------|--------------|-----------------|---------|---------|
| **#1670170** | Bug / **Closed** | 24-00963344 — DEVF TIPS Measimport warnings show multiple times & TIPS volume tripled | §4 | 24-00963344 |
| **#1670217** | Task / **Closed** | 24-00963342 — DEVF TIPS Measimport warning, non-paper meters show 0 | §4 | 24-00963342 |
| **#1617830** | Bug / **Closed** | ONM — 23-00916530 Long-Term TRNX_ID Fix (integer-limit) | §8 | 23-00916530 |
| **#1631131** | Task / **Closed** | ONM — 23-00916530 Long-Term TRNX_ID Fix | §8 | 23-00916530 |
| **#1656405** | Bug / **Closed** | Daily CO trnx_id being purged when they should not be | §8 | — |
| **#1773003** | Database Change / **Closed** | Core TIPS 17.0 — SETTLEMGR TRNX_ID Split Scripts | §8 | — |
| **#1435165** | Bug / **Closed** | Master Meter Group Derived Analysis — Rerun/Date Range (22-00220682, TP138553) | §6 | 22-00869412 (related) |
| **#1685847** | Bug / **Closed** | 24-00963716 — [2022.10] MMG Analysis Meter Not Generating an Analysis | §6 | 24-00963716 |
| **#1737689** | Requirement / **Closed** | TIPS Performance Initiative (Long-Term) — Convert WGHTAVGGAS | §6 | — |
| **#1595913** | Bug / **Closed** | Rounding Issue with Truck Tickets / S&W | §11 | — |
| **#1777564** | Bug / **Closed** | Truck tickets not importing with new Transporter | §11 | — |

> **Takeaway:** TIPS measurement defects split into (a) **data/timeslice** issues (overlapping CCT/analysis timeslices, dup keys, bad import rows) dispositioned operationally with a script + rerun; (b) genuine **code bugs** (measimport doubling #1670170, TRNX_ID limit #1617830, MMG rerun #1435165/#1685847, WGHTAVGGAS no-MMG, USER_ID>30, truck-ticket limits); and (c) **config/integration** (FlowCal revision-number resets, GMAS paths, Facility-Definition components, split decimals). The most common silent data trap is a **zero/missing Meter Split decimal** zeroing settlement.

---

## 16. Key Code Files, Processes & Repos

### Batch processes — TurboTips engine (`Quorum.TIPS.Batch.QPDllTurboTips`)
| Process / Step | Purpose |
|----------------|---------|
| **MEASIMPORT / WHMEASIMP** | Measurement / Wellhead measurement import (doubling defect #1670170; "same key" 24-00990231). |
| **Load Daily/Monthly Volumes & Gas Analysis from eSuite** | Pull volumes/analyses from eSuite/FlowCal onto Measured Volume screen (re-run after FlowCal change — §14). |
| **`SP_QTIP_ALL_VOL_IMPORT`** | Volume-import stored proc (per-client `*.TIPS.Database`/`*.ESuite.Database` `…/Procs/SP_QTIP_ALL_VOL_IMPORT.sql`). USER_ID>30 truncation fix (24-00965985). Trigger `TR_CVTIPS_SVALD_MTR_HEADER_U`. |
| **QIMPVOLD (step QIMPEXP)** | Daily volume import (PK-violation mid-file, 22-00679867). |
| **MeasAnalysis** | Standard-analysis step; inserts to `QTRAN_STD_ANALYSIS_BASE` (TRNX_ID unique constraint, 23-00916043). |
| **WGHTAVGGAS** | Weighted-average gas analysis over MMG — `Quorum.TIPS.Batch.QPDllTurboTips/StepExecution/WGHTAVGGAS.cs` (no-MMG warn+skip; rerun defect). |
| **TMTRSPLIT / NGLPROD / ARAP_IFGTT** | Meter-split → NGL production → AR/AP plant steps (NGLPROD ACCESS_VIOLATION 24-00945026). |
| **SETTLEMGR** | Settlement manager (TRNX_ID split scripts #1773003). |
| **GMASINT / GMASMAST** | GMAS measurement import (path/restart 26-01082744). |
| **ADJNOSVOL** | Adjust Non-Op Split Volume (not working in v16, 22-00561530). |

### Web screens (myQuorum TIPS Web)
| Screen | Purpose / known defects |
|--------|-------------------------|
| **Measured Volumes** | Manual vol entry; Web rounding (23-00926060), predictive text (22-00555546). |
| **Analysis** | Gas-analysis entry; manual component fill (24-00992188). |
| **Meter Definition** | Meter setup; retrieve (22-00555531), delete dup meters (26-01101667). |
| **Contract Meter List / Meter Split** | Split-decimal & CCT; abandon/delete split (24-00957962), child meters (26-01087430). |
| **Import/Export Definition + File Definition tab** | Import column spec (metadata read-only; File Definition = expected column order, 25-01042838). |
| **Ticket Analysis Update** | Truck-ticket analysis (22-00831415). |

### Repos
`Quorum.TIPS.Batch` (incl. `Quorum.TIPS.Batch.QPDllTurboTips`), `Quorum.Tips.TurboTips` (tests), and per-client overrides `<CLIENT>.TIPS.Database` / `.ESuite.Database` / `.TIPS.Metadata` (e.g. **CMP, ALT, PEP** seen for `SP_QTIP_ALL_VOL_IMPORT`). **Always check the client override `*.TIPS.Database`/`*.ESuite.Database` proc/view** before assuming base behavior — settlement views are client-prefixed (e.g. `OXYPOST_SETTLE_GAS_STMT_VW`).

---

## 17. Database Tables Reference

| Table / View | Purpose |
|--------------|---------|
| **`QTRAN_STD_ANALYSIS_BASE`** | Standard gas-analysis rows. **Unique constraint on `TRNX_ID`** — the MeasAnalysis collision target (23-00916043). |
| **`QTRAN_PAYSTATION`** | Paystation rows feeding settlement; carries **`S_DECIMAL`** (split decimal) and pulls `User_ID`/`Updt_Dt` from `QTRAN_TRNX_ID` (recycle side-effect, 24-00972261). |
| **`QTRAN_PAYSTATION_GATH_ATTR`** | Paystation gathering attributes — **PK violation on overlapping timeslice** (23-00932144). |
| **`QTRAN_TRNX_ID`** | TRNX_ID master (purge/recycle; User_ID/Updt_Dt source). |
| **`QUORUM_VOL_DAILY`** | Daily volume import staging table (~49k-row PK abort, 22-00679867). |
| **`SCTRL_INT_FULLSYNC`** (esuite) | Integration full-sync control — missing value breaks FlowCal sync-date import (25-01025108). |
| Settlement views e.g. **`OXYPOST_SETTLE_GAS_STMT_VW`** | Client-prefixed settlement gas-statement view: `NVL(ALLOC.WHDV_VOL * PAY.S_DECIMAL,0)` — shows why a **zero split decimal** zeros NGLS (26-01091612). |
| **Meter Split / CCT tables** | Split decimal `S_DECIMAL` + contract/cost-center timeslices (CCT). Overlapping/erased CCT = §6/§9 (column names *inferred* — verify before scripting). |
| **`REVISION_NUMBER`** (measurement/analysis) | FlowCal multi-event inflation >1000 → reset script (25-01047138). |
| Trigger **`TR_CVTIPS_SVALD_MTR_HEADER_U`** | Prepends `UPDATE_` to USER_ID; >30-char overflow in `SP_QTIP_ALL_VOL_IMPORT` (24-00965985). |
| Facility Config **`IGNORE_PURGE_IND`** | Set =1 to revert TRNX_ID recycle (restore latest User_ID/Updt_Dt on Paystation). |

---

## 18. Diagnostic SQL Queries

> Verify table/column names against the client's schema (TIPS schemas are heavily client-prefixed; several names below are inferred from case repros). Always run a SELECT and eyeball counts before any corrective script; wrap destructive steps in a transaction.

### A. Overlapping timeslices on a meter (PK-violation plant failures — 23-00932144, 22-00513111)
```sql
-- Analysis timeslices (adapt table per client; QTRAN_STD_ANALYSIS_* / meter-split CCT)
SELECT MTR_NO, EFF_DT_FROM, EFF_DT_TO, COUNT(*)
FROM   <analysis/CCT timeslice table>
WHERE  PLANT_NO = <PLANT> AND PROD_DT = '<PROD_MTH>'
GROUP BY MTR_NO, EFF_DT_FROM, EFF_DT_TO
HAVING COUNT(*) > 1;
-- Or detect overlaps: rows for the same MTR_NO whose [EFF_DT_FROM,EFF_DT_TO] ranges intersect.
```

### B. Split decimal feeding settlement (zero/missing → 0 on gas statement — 26-01091612, 24-00937128)
```sql
SELECT MTR_NO, PROD_DT, S_DECIMAL
FROM   QTRAN_PAYSTATION
WHERE  PLANT_NO = <PLANT> AND MTR_NO = '<MTR>' AND PROD_DT = '<PROD_MTH>';
-- S_DECIMAL = 0 or NULL on the affected meter (others = 1) is the 26-01091612 signature.
```

### C. TRNX_ID collision / exhaustion (MeasAnalysis unique constraint — 23-00916043)
```sql
SELECT TRNX_ID, COUNT(*) dup_ct
FROM   QTRAN_STD_ANALYSIS_BASE
WHERE  PLANT_NO = <PLANT> AND PROD_DT = '<PROD_MTH>'
GROUP BY TRNX_ID HAVING COUNT(*) > 1;
-- Short-term remediation: reset the TRNX_ID sequence/counter to 0 (per 23-00916043).
```

### D. Daily-volume staging load gaps (~49k-row abort — 22-00679867)
```sql
SELECT MIN(VOL_DATE), MAX(VOL_DATE), COUNT(*), COUNT(DISTINCT MTR_NO)
FROM   QUORUM_VOL_DAILY WHERE BATCH_ID = <BATCH>;
-- Compare row count to the source file; find the first dup/constraint-violating key after the loaded rows.
```

### E. FlowCal revision-number inflation (Integration Platform — 25-01047138)
```sql
SELECT MTR_NO, PROD_DT, REVISION_NUMBER
FROM   <measurement/analysis table>
WHERE  REVISION_NUMBER > 1000;
-- Remediation script resets these back to 1 or 2 (temp until FlowCal upgrade).
```

### F. Facility Config flag (TRNX_ID recycle — 24-00972261)
```sql
SELECT FACILITY_NO, CONFIG_KEY, CONFIG_VALUE
FROM   <facility config table>
WHERE  FACILITY_NO = <FACILITY> AND CONFIG_KEY = 'IGNORE_PURGE_IND';
-- =1 restores original User_ID/Updt_Dt behavior on Paystation.
```

---

## 19. Escalation Decision Guidance

**Route to Engineering (Software Defect)** when:
- A batch step crashes natively (`ACCESS_VIOLATION`) or fails on logic you can't fix with data (NGLPROD, measimport doubling #1670170, WGHTAVGGAS no-MMG/rerun #1435165/#1685847, USER_ID>30 truncation, truck-ticket import limits, TRNX_ID integer limit #1617830).
- A Web screen behaves differently from Classic in a way that loses/rounds data (reproduce in both first), e.g. 23-00926060, 24-00957962.
- Provide: failing **step name**, **plant/facility + prod month**, exact error text, patch/version, and whether it reproduces in a non-hotfix env.

**Route to Cloud Ops (Application Configuration / ChangeConfig / scripts)** when:
- **Overlapping timeslice / dup-key** needs a corrective data script + plant rerun (23-00932144) — scope to the specific meter, wrap in a transaction.
- **TRNX_ID reset to 0** (short-term) pending the #1617830 patch.
- **Integration-Platform** fixes: FlowCal `REVISION_NUMBER` reset script, GMAS path + service restart, `SCTRL_INT_FULLSYNC` value, staging-table cleanup (§12).
- **Split decimal / CCT** corrections at Meter Split level (§9).

**Handle as Training / answer (no escalation)** when the FAQ (§14) matches — most "volumes didn't update," "import errored," and "Paystation User_ID" cases. Check the FAQ **before** opening any script or bug.

**Config/Facility-Definition (no code)** for gas-analysis component issues (§5): Component Product Allocation tab + Plus-components setting.

---

*Skill created: 2026-06-11*
*Based on: 66 actionable TIPS Measurement/Volumetric/Ticketing/Inventory SF cases (Software Defect 41 + Application Configuration 20 + ChangeConfig 5) + ~35 Training/Customer-Error cases + ADO #1670170, #1670217, #1617830, #1631131, #1656405, #1773003, #1435165, #1685847, #1737689, #1595913, #1777564.*
*Companion: SKILL_Allocations.md (QPTM), SKILL_Customer_Accounts_Inventory.md, SKILL_Billing.md. Implementing code: Quorum.TIPS.Batch.QPDllTurboTips (TurboTips), SP_QTIP_ALL_VOL_IMPORT, WGHTAVGGAS.cs.*
