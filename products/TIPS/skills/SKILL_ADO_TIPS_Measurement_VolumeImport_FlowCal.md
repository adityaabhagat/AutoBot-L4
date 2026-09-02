# SKILL (ADO): TIPS Measurement / Volume-Import / FlowCal — Defect & Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Source:** Azure DevOps closed/resolved TIPS Bugs (NOT Salesforce)
**Product:** My Quorum TIPS (midstream measurement, gas analysis, volume import, settlement statements)
**Area:** `Measurement_VolumeImport_FlowCal` — Measured Volumes, Gas Analysis, FlowCal→eSuite→TIPS integration, GMAS, Master Meter Group / weighted-average analysis, meter split → gas statement, Ticket Volume/Analysis import, measurement batch steps.

> **Use When:** triaging a TIPS measurement/volume case and you want to know *whether a code fix already exists, in which build, and what the dev-confirmed root cause was* — straight from the ADO bug + dev comment thread + linked PRs. This is the ADO-mined companion to the SF-case-mined `SKILL_TIPS_Measurement_Ticketing.md` (TIPS Assistant). Where they overlap (same SF case), the ADO thread is the more authoritative root-cause/fix source.

> **Evidence base:** WIQL over BOTH `QuorumSoftware\Engineering\Midstream*` and `QuorumSoftware\Engineering\Maintenance\Midstream and Transportation*`, WorkItemType=Bug, State in (Closed,Resolved), title containing measurement/volume/FLOWCAL/WHMEASIMP/MeasVol/analysis/ticket/QIMPVOLD/"gas analysis"/GMAS. **588 bugs matched** (capped to most-recent 250 for field triage); **54 deep-read** (description + ReproSteps + relations/PRs + full comment thread). Every root-cause/fix claim below is from a real dev comment or linked PR observed during mining.

> **CLASSIFICATION / OVERLAP CAVEATS (read first):**
> - The **Maintenance\Midstream and Transportation** branch is **MIXED QPTM + TIPS**. Team-name leaf nodes are a strong product signal: **`Guardians of TIPS` / `TIPS'n Tricks`** = TIPS; **`Pirates of Pipeline` / `Pipeline Galaxy` / `Pipeline Titans`** = QPTM (pipeline/transportation). Customer Service / Professional Service leaves are mixed.
> - **QPTM bugs that matched on the keywords and were DROPPED** (not in scope): Capacity Release / Contract Maintenance MSQ-MDQ / Imbalance Volumes / OBA-PDA double-volume / TPC segment-location doubling / QGM invoice duplication / CFAUTOCONF / BROLLDATE / "transportation volume" / Nomination-Offer-RFS. Examples dropped: #1702160, #1656800, #1697139, #1721304, #1720978, #1767998, #1768368, #1813294/#1813295, #1716918, #1733867, #1731417/#1731420 (QGM/HEP invoice), #1765102, #1623346/#1631925/#1607262 (QPTM format).
> - **Genuinely ambiguous / shared (core view used by both):** several **gas-statement** bugs live in QPTM-labeled leaves but operate on **TIPS core settlement views** (`QPOST_/QRPTS_SETTLE_GAS_STMT_*_VW`) — kept as TIPS (#1354249, #1434950, #1570322, #1591365, #1681391/DOH_MEASPR).
> - **IntegrationBuild is EMPTY on every one of these bugs.** Fixed-in-build below is **inferred** from PR target branches in dev comments (e.g. `[2021.10]`, `[2022.04]`, `develop`), iteration path (YY.NN), and version tags, and is marked **(inferred — confirm in release notes)**. TIPS end-of-time is **12/31/9000** (NOT 9999) — a 9999 value is itself a bug tell (see Cluster D).

---

## 1. QUICK TRIAGE

| Symptom (error / behavior) | Cluster | Lead bug → fix (inferred build) |
|---|---|---|
| Excel/`LOAD SPREADSHEET ALL VOLUMES` import end-dates a meter that had 0 vol this month / stops mid-file | A | #1712775 ALT 24-00965985 — proc only re-statused NULL/PROD disposition; now creates new open-ended slice (2024.10-era) |
| `PK_ALCTRL_MEAS_VOL` duplicate-key on FTP/MEASIMP import; only `.csv` works | A | #1700609 SUI 24-00990895 — file must be true `.csv`; `USE_STRAN_LATEST_TABLES` config + ALESVOLIMP sync date (config, not code) |
| `ALESVOLIMP` skips volumes written to eSuite during the run | A | #219868 XCL — sync-date `>` vs `>=` rounding race; PRs 33735/33314/35399 |
| `ALESVOLIMP` 100k+ records 12h/timeout | A | #1649462 XCL — perf (closed by client, not fixed) |
| FlowCal→TIPS: heat value = 0 in `QTRAN_ALLOC_VOL`; `ALT_QTY_UOM_CD=DTH` | C | #1396228 — map DTH→MMBTU in eSuite API + TIPS UOM check (2021.10/2022.04/develop) |
| FlowCal→TIPS: MCF vol not inserted; `PRES_BASE_CD=0` in `STRAN_VOL_*` | C | #1403818 — default to plant pressure base from `QCTRL_PLANT_HDR` (2021.10/develop) |
| IP error `inserts/updates were cancelled … another user changed the record` | C | #1433354 UTG — FlowCal sends duplicate/near-simultaneous events; concurrency on overlapping OE timeslice (ESuite.API 17.0.9, 2021.04 patch) |
| FlowCal import ignores liquid meters with 0 vol / ghost records on re-import | C | #1741530 PEM 25-01025108 — remove WHERE clause in `QTIP_VOLUME_MONTHLY_VW` so import overrides prior value (PR 116109) |
| FlowCal std import wrong decimals (gas/GJ rounding) | C | #1678596 PEM 24-00969233 — rounding in `QTIP_VOLUME_DAILY_VW`/`_MONTHLY_VW` (PR 101039) |
| GMAS / analysis import "completes successfully" but **no data** when file date < FULL_SYNC_DT | C | #1655328 CMX — `SCTRL_INT_FULLSYNC` needs timestamp; `SRC_SYSTEM_UPDT_DT` datetime (PR 96108) |
| Gas analysis import doesn't overwrite on 2nd run / re-import | E | #1757914 CHD 25-01041981 — `QPP_IMPORT_ANALYSIS` LEFT JOIN to dead `STRAN_MTR_FACILITY_RANGE`; → `SCTRL_MTR_FACILITY` JOIN (PR 118428) |
| Single CSV for 2 TSPs only imports once / sync-date blocks 2nd TSP | E | #1773646 VGP 25-01057601 — ALANLIMPFC sync-date param 30040 not passed to child ALESGASIMP (26.03; add param 26570) |
| Load Analysis sets plus-component **GPM=0** | E | #1426499 UTG — `OVERRIDE_PLUS_COMPONENT` rollup zeroing GPM (2021.10/develop) |
| Gas-analysis import removes **FW Factor** on prior month | E | #1377251 IAC 21-00202866 — retain FW_FCTR on old timeslice in Load Gas Analysis (2019.10/2021.04/2021.10/2022.04) |
| Mol% won't recalc on Bulk Edit / import-from-Excel; 100.000001 shows 100.000000 | E | #1443304 PEM — enable totals refresh after bulk/import (2021.10/2022.04/develop); caused collateral #1457974 |
| C7+ Molar-Mass / Density limit is an **error** in Web but warning in Classic | E | #219721 PEM — change validation error→warning (2021.10/develop) |
| C6+/Hexane+ rolled into "Other" on gas statement after upgrade | E | #1783561 IACX 26-01069756 — config-related; re-post fixes go-forward (PR 124597) |
| MMG **rerun** leaves derived analysis open-ended `12/31/9999` → current month fails | D | #1435165 ONM 22-00220682 — rerun creates 9999 overlap; fix in `MasterMeterGrpWghtAvgGasAnalyzer` (2020.03→develop) |
| MMG Analysis Meter **not generating** an analysis at all | D | #1685847 ONM 24-00963716 — batch + new Web validation on Meter Group/Analysis Meter/Eff date (2022.10/2024.04) |
| MMG Web "Error Occurred during field update" on derived meter | D | #1328845 ONM — `DateTime.MaxValue.Date` (9999) bad timeslice; should be 9000 (2021.04) |
| Allocated volume = 0 for one owner when split decimals are e.g. `0.9421875 / 0.0578125` | F | #1712833 PEM 25-01002874 — rounding to `0.05781300…003`; cast subquery (CAN ORA+MSSQL) |
| Gas statement 0/wrong shrink, theo gallons, gas-lift added to wellhead | F | #1354249 SCX — 3 report fixes; gas-lift not added to Gross WH (2020.11→develop) |
| Posted gas statement allocated gallons wrong / 0 for TIK | F | #1434950 SCX — `QPOST_SETTLE_GAS_STMT_PROD_VW` missed prior `QRPTS_` fix; TIK formula (2021.10/2022.04) |
| Theo gallons 0 after switching liquids monthly→daily | F | #1570322 UTG 22-00874962 — `MONVOLS` step didn't roll up theoretical to monthly (2023.04/develop; go-forward only) |
| Measured Volume Web rounds Temperature/Production Hrs vs Classic | G | #1681445 ONM 23-00926060 — Web mask + **display control type → double numeric** (2022.10/2024.04) |
| Measurement Entry Bulk Edit allows decimals → allocation/PANIGHTLY fails | G | #1647889 ONK — apply format/mask to Vol/Eng grid columns (QPTM-leaf but core meas entry) |
| Measurement Entry no longer shows **negative** volumes (sign/comma) | G | #1605706 ONK 23-00906127 — grid number-format metadata for negatives (2022.10) |
| Ticket Volume Update: Density Variance hidden after row 50 / not in Web grid | H | #1687126 PEM 24-00978630 — unhide column (Core + Core CAN; also Ticket Analysis Update) |
| Ticket Analysis "Plus component required" error in Web | H | #1389877 PEM 21-00207544 — metadata lost in 2021.04 merge; restore non-required (2021.04) |
| GMAS/PI "completes" but no data into system after upgrade | C | #1442338 NRM 22-00251937 — `*.TIPS.Application.QPEC` missing core Crude packages in csproj → seg process can't spawn GMASLDVOLS (2022.04 / QPEC 17.20.4) |

---

## 2. DECISION TREE

```
TIPS Measurement / Volume-Import / FlowCal bug
│
├─ Is it actually QPTM? (Capacity Release, MSQ/MDQ, Imbalance, OBA PDA, TPC segments, QGM invoice, Nomination/Offer/RFS, BROLLDATE, CFAUTOCONF)
│     → OUT OF SCOPE. See QPTM ADO skills. (Team leaf Pirates/Galaxy/Titans ≈ QPTM.)
│
├─ IMPORT into TIPS fails / loads wrong (§A)
│   ├─ Excel "LOAD SPREADSHEET ALL VOLUMES" end-dates a 0-vol meter / stops mid-file → #1712775 (disposition NULL/PROD only)
│   ├─ PK_ALCTRL_MEAS_VOL dup key / only .csv works → #1700609 (file format + USE_STRAN_LATEST_TABLES) — CONFIG, not a code bug
│   ├─ ALESVOLIMP skips concurrent eSuite writes → #219868 (sync >= )   |  slow on 100k → #1649462 (perf, unfixed)
│   └─ "Vol Subscriber Error: meter X is a parent location" → #1681391 DOH (delete bad parent-meter vol rows; script)
│
├─ FlowCal → eSuite → TIPS INTEGRATION (§C)
│   ├─ heat 0 / DTH→MMBTU → #1396228   |  MCF not inserting / PRES_BASE_CD=0 → #1403818
│   ├─ "inserts/updates were cancelled" concurrency → #1433354 (FlowCal duplicate events; ESuite.API)
│   ├─ liquid 0-vol ignored / ghost records → #1741530   |  rounding wrong → #1678596
│   ├─ GMAS "success but no data" when file date < FULL_SYNC_DT → #1655328 (SCTRL_INT_FULLSYNC timestamp)
│   ├─ GMAS/PI success but no data (post-upgrade) → #1442338 (QPEC missing Crude packages)
│   └─ meter end-dated by IP / not transferring → #1686007 (not repro), #1811840 (IP object validation override)
│
├─ GAS ANALYSIS import / component (§E)
│   ├─ won't overwrite on re-run → #1757914 (QPP_IMPORT_ANALYSIS dead-table join)
│   ├─ single CSV / 2 TSPs sync-date → #1773646 (ALANLIMPFC param passthrough)
│   ├─ plus-component GPM=0 → #1426499   |  FW Factor removed → #1377251
│   ├─ Mol% not recalc (bulk/import) → #1443304   |  C7+ limit error vs warning → #219721
│   └─ C6+/Hexane+ in "Other" → #1783561   |  NC5 not converting heat/gas → #1791807 (analysis ≠ 100%; CONFIG)
│
├─ MASTER METER GROUP / WGHTAVGGAS (§D)
│   ├─ rerun → 12/31/9999 overlap, current month fails → #1435165
│   ├─ analysis meter not generating → #1685847   |  Web field-update error on derived meter → #1328845
│   └─ no warning when a master meter has no vol → #1352003
│
├─ METER SPLIT → SETTLEMENT / GAS STATEMENT (§F)
│   ├─ one owner 0 on tiny split decimal → #1712833 (rounding/cast)
│   └─ shrink/theo/gas-lift/TIK/posted-view wrong → #1354249, #1434950, #1570322, #1591365
│
├─ MEASURED VOLUME / MEASUREMENT ENTRY SCREEN (§G, Web vs Classic)
│   └─ rounding #1681445 · bulk-edit decimals #1647889 · negatives #1605706 · non-manual edit #1638339 · 0-fill partial month #1774450 (CONFIG/workaround)
│
└─ TICKETING (§H)
    └─ Density column hidden #1687126 · Plus-component required #1389877 · QQM neg tickets #1734750 (universe/data, unfixed)
```

---

## 3. Cluster A — Volume Import into TIPS (Excel / ALESVOLIMP / MEASIMP / WHMEASIMP)

**Symptom:** the Excel/FlowCal/FTP volume import into TIPS (or QPTM via eSuite) fails on a PK error, end-dates meters incorrectly, skips rows, or skips records written concurrently.

**Root causes (dev-confirmed):**
- **#1712775 (ALT, SF 24-00965985, Closed):** "LOAD SPREADSHEET ALL VOLUMES" import prematurely end-dated meters that had volume in the prior month but **0 in the current month**, and stopped loading mid-file at the offending meter. Dev (Cristina Keeton): the stored proc *"based on the business requirements at the time… should only update the status for meters with a disposition of either NULL or PROD"* — SALE-disposition meters were excluded; the real defect was the **incorrect end-dating**, now fixed to *"create a new open ended range with the new Production status code when needed."* The "missing record count" vs spreadsheet was duplicate product-code rows (H2O+CON), expected. PRs 113720/113721/113867/113913/114163/114164/114168/114173. **NOTE:** the SF-mined skill attributes 24-00965985 to a "USER_ID>30-char trigger truncation" — that is a *different/adjacent* fix thread for the same case; the ADO bug's primary root cause is the disposition/end-dating logic. Treat both as candidate fixes; confirm which is in the client patch.
- **#1700609 (SUI, SF 24-00990895, Rejected/CONFIG):** `Violation of PRIMARY KEY PK_ALCTRL_MEAS_VOL … duplicate key`. Resolved NOT by code: the import file was **not a true `.csv`** (import/export def is comma-delimited) and the `USE_STRAN_LATEST_TABLES` global config plus the `ALESVOLIMP` **sync date** had to be set correctly. Convert file to `.csv`, run ALESVOLIMP with the right sync date.
- **#219868 (XCL, SF 20-00087720, Verified):** `ALESVOLIMP` skipped volumes written to `STRAN_VOL_DAILY` at almost the same instant the import read it (sync-date rounded to the second). Fix discussion: change the `> SYNC_DATE` filter to `>= SYNC_DATE`. PRs 33313/33314/33735/35399. Long-term fix of critical #218931.
- **#1649462 (XCL, Rejected — NOT fixed):** ALESVOLIMP non-linear perf; 8k rows ~5-15 min, 100k → 12h/timeout. Dev (Durvesh) found `TransferStage2.ProcessParentMeterVolumesAll` looping 1526× with nested per-meter delete+insert (`QPTMMeterVolumeSubscriber.cs`, `m_MaxNumberOfMeters=100`). **Closed by client** before a fix landed — perf root cause documented, no PR.
- **#1681391 (DOH, SF 24-00973101, Verified):** `DOH_MEASPR`/`ALESVOLIMP` fails `Vol Subscriber Error: A measured volume was found for meter 85371 which is setup as a parent location`. Meter became a parent on 12/1/2023; bad rows in `QUORUM_VOL_DAILY` + `STRAN_VOL_DAILY`. **Fix = script to delete the parent-meter volume rows**, then rerun. Root cause is source data, not code.

**Workaround:** ensure `.csv` + correct import/export def column order; set ALESVOLIMP sync date / `USE_STRAN_LATEST_TABLES`; for parent-location errors, delete the offending vol rows (script) and rerun.

**Bug IDs:** 1712775, 1700609, 219868, 1649462, 1681391 · **SF:** 24-00965985, 24-00990895, 20-00087720, 24-00973101 · **Clients:** ALT, SUI, XCL, DOH.

---

## 4. Cluster C — FlowCal → eSuite → TIPS Integration (UOM, pressure base, concurrency, GMAS, ghost records)

**Symptom:** the FlowCal/Integration-Platform/eSuite path "runs successfully" but data is wrong/zero/missing in TIPS, or throws an IP concurrency error.

**Root causes (dev-confirmed):**
- **#1396228 (FC-TIPS, Closed):** `ALT_QTY_UOM_CD=DTH` written to `STRAN_VOL_DAILY/_MONTHLY`; TIPS can't recognize DTH so **heat value = 0** in `QTRAN_ALLOC_VOL`. Fix (Lee Allison): map **DTH→MMBTU** (equivalent, no conversion factor) when moving FlowCal data into eSuite, and add a TIPS-UOM check (code table 24011 / QCODE_QTY_UOM) in `LDMVOLES`. PRs 62303/62317/62321/67610/67635/67645/67646/67648. Caused collateral #1443818. **Inferred build:** 2021.10 (hotfix/17.1.1), release 17.3.0, develop.
- **#1403818 (FC-TIPS, Closed):** `PRES_BASE_CD=0` in `STRAN_VOL_*` → MCF volumes not inserted into `QTRAN_ALLOC_VOL`. Fix: default to the plant pressure base from `QCTRL_PLANT_HDR` when FlowCal doesn't supply it. PRs 61338/61339/61340/67635. Split out from IP WI #1396556. **Inferred:** 2021.10 / develop.
- **#1433354 (UTG, Closed):** IP error `the inserts/updates were cancelled due to the fact that another user changed the record`. Long thread: **FlowCal sends multiple/near-simultaneous events** (per Kevin Delgado, expected FlowCal behavior) for the same meter on different contract months; both events try to end-date/overwrite the **same open-ended (OE) timeslice** in `MeterMonthlySampleCommand.cs` → EF concurrency violation. Resolution path = API retry / DB lock + targeted query by productionDateStart/End. Related #1426529/#1433353/#1433355/#1433359 (IP duplicate events). **Inferred:** ESuite.API artifact **17.0.9**, 2021.04 patch (#1444154); merged to develop pre-2022.04.
- **#1741530 (PEM, SF 25-01025108, Ready for Review):** FlowCal monthly import (LDMVOLS) **ignores liquid meters with 0 volume**, and re-uploading leaves **ghost records** (prior `STRAN_VOL_MONTHLY` value persists via `QTIP_VOLUME_MONTHLY_VW`). Fix (Ajinkya): **remove the WHERE clause from `QTIP_VOLUME_MONTHLY_VW`** so the import overrides the previous value and 0-liquid imports. PR 116109.
- **#1678596 (PEM, SF 24-00969233, Verified):** FlowCal standard import wrong decimals. Fix: rounding logic in `QTIP_VOLUME_DAILY_VW` / `QTIP_VOLUME_MONTHLY_VW` (Daily gas/liq/tons 2dp, GJ 0dp; Monthly 1dp, GJ 0dp). PR 101039. Patch passed QA. (Process-transition miss; reclassified Bug.)
- **#1655328 (CMX, Closed):** `GMASIMPORT` "completes successfully but data not uploaded" when a second file shares the generation date / file date < `FULL_SYNC_DT`. Root cause: `SRC_SYSTEM_UPDT_DT` in `QUORUM_VOL_DAILY` had no timestamp (QTZDate) and UPG defaulted `FULL_SYNC_DT` to 00:00. Fix: give it a real **DateTime** timestamp (Codegen object editor). PR 96108. **Workaround:** set `SCTRL_INT_FULLSYNC` MeterVolume entry to a date prior to the file generation date.
- **#1442338 (NRM, SF 22-00251937, Verified):** post-upgrade GMAS/PI "complete" but no data; `GMASLDVOLS` segregated process never spawned. Root cause (Jennifer Hart): **`NRM.TIPS.Application.QPEC` csproj was missing all Core TIPS Crude packages** (removed in a prior upgrade), so the seg process couldn't load crude DLLs / the custom SQL that spawns the volume-load. Fix = re-add packages. Hotfix `NRM.TIPS.Application.QPEC` 17.20.4 (2022.04-era).
- **#1686007 (DTM, Rejected):** IP end-dates a meter on FlowCal meter-header change. **Not reproducible** in 2024.10 with the supplied payloads (likely extra IP calls). No fix — re-log with full IP call trace if it recurs.
- **#1811840 (XCL, SF 26-01102718, Acceptance):** meter not transferring FlowCal→eSuite→QPTM; workaround = override **TIPS object validation** in the QXCL layer (as done for DSU) + restart services; tracked under IP #1812284.

**Workaround:** confirm UOM/pressure-base in `STRAN_VOL_*`; for concurrency, expect FlowCal duplicate events (retry); for GMAS "no data", set `SCTRL_INT_FULLSYNC`/`FULL_SYNC_DT` to a timestamp before the file date; for post-upgrade "no spawn", verify the client `*.TIPS.Application.QPEC` packages.

**Bug IDs:** 1396228, 1403818, 1433354, 1741530, 1678596, 1655328, 1442338, 1686007, 1811840, 1559898 (SUI — missing `QUORUM_VOL_DAILY` table, client-specific) · **SF:** 25-01025108, 24-00969233, 22-00251937, 26-01102718 · **Clients:** FC-TIPS core, UTG, PEM, CMX, NRM, DTM, XCL, SUI.

---

## 5. Cluster D — Master Meter Group / Weighted-Average Gas Analysis (WGHTAVGGAS, feature 183197)

**Symptom:** the WGHTAVGGAS step (added for ONEOK feature 183197, runs after MMALLOC in MEASUREMENT) doesn't generate the derived group analysis, creates overlapping open-ended slices on rerun, or errors in Web.

**Root causes (dev-confirmed):**
- **#1435165 (ONM, SF 22-00220682 / TP138553, Acceptance):** on **rerun of a prior production month**, the derived weighted-average analysis is created with end date **`12/31/9999`** instead of `12/31/9000`, **overlapping** later analysis records and **failing the current billing month**. Dev (Dan Stefan): "Oneok's assumption was the new Derived Weighted Average process would follow the same logic Allocate does in deriving analysis records for prior periods" — a testing/design miss. Fix in `MasterMeterGrpWghtAvgGasAnalyzer` to consider other analysis records. Many PRs across 2020.03 / 2021.04 / 2021.10 / 2022.04 / 2022.10 / develop (69795/74146-74180/79647-79767). **Inferred:** all from 2020.03 forward.
- **#1685847 (ONM, SF 24-00963716, Ready for QA):** the MMG Analysis Meter **doesn't generate an analysis at all** (no record, only an INFO msg) even with master-meter volumes+analysis present. Two-part fix: batch change in `WGHTAVGGAS` + a **new Web validation** on the Master Meter Group screen (Meter Group#/Analysis Meter#/Effective Start Date) to prevent the bad data setup. PRs 100884-100942/113868. **Inferred:** 2022.10 / 2024.04.
- **#1328845 (ONM, Ready for QA, 21.11):** "Error Occurred during field update" in **Web only** on the meter that derives data from the master meter. Root cause (Zachary Babka): use of **`DateTime.MaxValue.Date` (12/31/9999)** created a bad timeslice; TIPS end-of-time must be **12/31/9000**; the fix prevents the bad slice (existing bad slices must be deleted/cleaned). PRs 52137/52278. 2021.04; hotfix back to 2020.03 (ONEOK).
- **#1352003 (ONM, Verified, 21.14):** when one master meter has **no volumes** for the month, the **expected warning** isn't shown (the analysis still purges/handles correctly). PRs 53550/53563. (This is the no-volume warning gap; the no-MMG warn+skip behavior is the related 2020.07 fix in the SF skill.)

**Workaround:** delete the bad `12/31/9999` timeslice and rerun MEASUREMENT; ensure valid non-overlapping MMG setup (now enforced by #1685847 validation).

**Bug IDs:** 1435165, 1685847, 1328845, 1352003 · **SF:** 22-00220682, 24-00963716 · **Client:** ONM (ONEOK). Feature 183197.

---

## 6. Cluster E — Gas Analysis Import & Component Setup (overwrite, sync date, GPM, FW Factor, Mol%, plus-components, validations)

**Symptom:** gas-analysis import doesn't overwrite / doesn't pull / zeroes a component / loses a factor / wrong validation severity.

**Root causes (dev-confirmed):**
- **#1757914 (CHD, SF 25-01041981, Acceptance):** custom `LDANLYS_RG` won't overwrite analysis after the first import. Root cause (Akshay Jadhav): `QPP_IMPORT_ANALYSIS` (step IMP_ANALYS) **LEFT JOINs the dead `STRAN_MTR_FACILITY_RANGE` table**; data never moves WTRAN→STRAN. Fix: join `SCTRL_MTR_FACILITY` with an inner JOIN. DB change #1760317, PR 118428. Hotfix 10/17. (Client-specific, not testable in core.)
- **#1773646 (VGP, SF 25-01057601, Verified, 26.03):** `ALANLIMPFC` doesn't update analysis / a single FlowCal CSV used for 2 TSPs fails the 2nd. Root cause (Zachary Koontz / Daniel Mendivelso): top-level `ALANLIMPFC` sync-date param **30040 isn't passed through to child `ALESGASIMP`** (which uses QPTM sync param **26570**). Short-term fix: add param 26570 to ALANLIMPFC defaulted 1/1/2000. Long-term: ALESGASIMP falls back to eSuite sync date. Also: `STRAN_ANALYSIS_DAILY` is never refreshed (add to archive def FCANL/FCIMP). PRs 123421/123516/123519. (Sibling rejected WI #1769377 was the critical-part triage of the same SF case — drop as dup.)
- **#1426499 (UTG, Acceptance):** "Load Analysis from eSuite" sets the **plus-component GPM to 0** for the component named by global config `OVERRIDE_PLUS_COMPONENT` (all eSuite component GPMs are 0; code shouldn't zero the rollup). PRs 64765/65960/65962. **Inferred:** 2021.10 / develop. Related FlowCal-side GPM mapping issue noted by Will Wagner.
- **#1377251 (IAC, SF 21-00202866, Acceptance):** `LDMANLS` removes the **FW Factor** on the prior-month analysis screen when loading the current month. Core fix: **retain FW_FCTR on the existing timeslice** during Load Gas Analysis time-slicing (don't clear). (IAC has an extra client SP `SP_QTIP_SET_FW_FCTR` that sets it on the new slice.) PRs 64893/68050/68881/68882/81000. Merged 2019.10 (IAC build) / 2021.04 / 2021.10 / 2022.04. Watch: a sibling field `TEST_GPM_PAN` had the same class of issue.
- **#1443304 (PEM, SF 22-00252293, Acceptance):** Total Mol% doesn't recalc after **Bulk View/Edit or Import-from-Excel**; 100.000001 displays as 100.000000. Fix: enable totals to refresh after bulk/import. PRs 68782/69086/69087/69089. 2021.10 / 2022.04 / develop. **Caused collateral #1457974** (spurious "lose pending changes" message).
- **#219721 (PEM, Ready for QA, 21.23):** Web logs **C7+ Molar Mass should be between 100 and 142** (and C7+ Density 670–900) as an **error**; Classic logs a **warning** and saves. Fix: change validation severity error→warning (validation was wrongly authored as error since 2015). PRs 57992/61690/61956/61958/62172/62178. 2021.10 / develop.
- **#1783561 (IACX, SF 26-01069756, Acceptance):** C6+/Hexane+ Mol/GPM rolling into "Other" on the GAS_STMT after a 2024.10 upgrade. Dev (Cristina): **config change, not the upgrade**; measurement data is correct; re-running+posting fixes it go-forward. PR 124597. (Posted tables won't retro-fix.)
- **#1791807 (IPF, SF 26-01089915, Verified — CONFIG):** NC5 component not converting heat/gas vol in `QTRAN_ALLOC_VOL`. Root cause: the **analysis didn't equal 100%**; adjusting to 100 (or enabling the "put difference into largest component" config) fixes it. Not a code bug.
- **#1697124 (PEM, SF 24-00987145, Rejected):** "Upload Protrend Analysis" allows Mol% sums like 99.999999 that aren't 100. Root cause: SP cursor `NOT BETWEEN 99.99 and 100.001` floating-point edge. Documented; not fixed (rejected).
- **#1316787 (KEY, SF 20-00098179, Verified):** C5+ Component Analysis Report **div/0** — crystal formula uses denominator `{@C4_COMP_SUM07}` (0) instead of `{@C4_COMP_SUM06}`. PR 49498. Client-specific, KEY patch.
- **#1574907 (OXY, Rejected):** duplicate records in the Analysis Meter pick list in Web/CAW (Classic clean). Pick list ID 24031 / Reg SQL `SELECT_METER_WITH_GAS_ANALYSIS`. Closed by client (low priority) — root cause not fixed.
- **#1773688 (AZR, SF 25-01058203, Verified):** `SP_QTIP_IMPORT_ANALYSIS_INTO_QAZR` not truncating staging first. **Not reproducible**; client outside version policy (no patch).

**Workaround:** for "won't overwrite," fix the staging→STRAN join / sync-date param; for component zeroing, check `OVERRIDE_PLUS_COMPONENT` and analysis=100%; for FW Factor, confirm the retain-on-old-slice fix is in the client build.

**Bug IDs:** 1757914, 1773646, 1426499, 1377251, 1443304, 219721, 1783561, 1791807, 1697124, 1316787, 1574907, 1773688 · **SF:** 25-01041981, 25-01057601, 21-00202866, 22-00252293, 26-01069756, 26-01089915, 24-00987145, 20-00098179, 25-01058203 · **Clients:** CHD, VGP, UTG, IAC/IACX, PEM, IPF, KEY, OXY, AZR.

---

## 7. Cluster F — Meter Split → Settlement / Gas Statement Volumes

**Symptom:** a meter split decimal or a settlement view zeroes/miscomputes wellhead, shrink, theoretical, gas-lift, or allocated gallons on the gas statement.

**Root causes (dev-confirmed):**
- **#1712833 (PEM, SF 25-01002874, Acceptance):** with split decimals `0.9421875000 / 0.0578125000` the **0.0578125 owner shows 0** allocated. Root cause (Ajinkya): the split decimal **rounds to `0.0578130000000000003`** in the 2nd iteration, summing >1 (1.0001). Fix: **cast the subquery** so the value isn't rounded. PRs 109849/110017/111073. **CAN only**, ORA + MSSQL.
- **#1354249 (SCX, Acceptance, 2020.11):** core gas statement: (1) shrink returns **0** when contract pay code = TIK ALL; (2) **theoretical gallons missing** on the POP statement; (3) **gas-lift volume incorrectly added** to Gross Wellhead (should be `QTRAN_FIXED_FUELS.wellhead delivered`). Fixes split SCX-specific + core. PRs 53115/53229/53238/55005/55293/56220/63142/63143/63358/63359. 2020.11→2021.10/develop.
- **#1434950 (SCX, SF 22-00219951/22-00824910, Acceptance):** posted gas statement allocated gallons wrong — the prior core fix on `QRPTS_SETTLE_GAS_STMT_PROD_VW` (#277677) was **not applied to `QPOST_SETTLE_GAS_STMT_PROD_VW`**; and the crystal TIK formula returns **0** (doesn't read TIK vol like shrink does). PRs 66571/66814/68599/68602/68805/68807/69167-69171. 2021.10 / 2022.04.
- **#1570322 (UTG, SF 22-00874962, Acceptance):** after switching liquids monthly→daily, theo gallons show **0**. Root cause: the **`MONVOLS` step rolls daily→monthly but explicitly excludes theoretical quantities**. Fix: add theoretical volumes to MONVOLS. PRs 84524/84672/86744/86745. 2023.04 / develop — **go-forward only** (must re-run Allocate).
- **#1591365 (MOM, Acceptance):** Wellhead Information section of the gas statement must reflect **contractually adjusted** Gross/Net-delivered (from Fixed Fuels). Fix in `QRPTS_SETTLE_GAS_STMT_PROD_VW`. PRs 85051/85075/85090/90420/90422/90423/96986. hotfix/17.24.x/17.25.x/develop.

**First check for any "gas statement 0/wrong volume":** the **split decimal at the Meter Split level** (rounding for tiny decimals → #1712833) and whether the fix is in **both** `QRPTS_` (non-posted) and `QPOST_` (posted) settlement views (#1434950).

**Bug IDs:** 1712833, 1354249, 1434950, 1570322, 1591365 · **SF:** 25-01002874, 22-00219951, 22-00824910, 22-00874962 · **Clients:** PEM (CAN), SCX, UTG, MOM. Cross-ref SF skill §9 (split-decimal=0 zeros settlement, 26-01091612/24-00937128).

---

## 8. Cluster G — Measured Volume / Measurement Entry Screens (Web vs Classic)

**Symptom:** Web screen rounds/loses/blocks data that Classic handles; bulk-edit decimals break downstream allocation.

**Root causes (dev-confirmed):**
- **#1681445 (ONM, SF 23-00926060, Acceptance):** Measured Volume Web **rounds Temperature (2dp) and Production Hours (1dp)**; Classic shows full value. Fix (Cristina): add the input **mask AND change the display control type to a double numeric** (mask alone wasn't enough — grid re-render rounded). PRs 101009/101147/101148/102462/102468/102469. 2022.10 / 2024.04. Stacey: could silently affect settlement.
- **#1647889 (ONK, SF 24-00939019, Acceptance):** Measurement Entry **Bulk View/Edit allows decimals** in Vol/Eng → stored un-rounded → `PANIGHTLY` allocation fails. Fix: apply format/mask to grid columns (`CalculateAutoPopulateColumns`). PRs 94591/94594/95118-95121/95176/95177. (QPTM-leaf but core Measurement Entry; "Bulk Edit required on Measurement Entry per Products for Excel copy/paste.")
- **#1605706 (ONK, SF 23-00906127, Acceptance):** Measurement Entry **no longer displays negative volumes** (sign/comma) on de-select (totals still calc). Fix: grid number-format **metadata** for negatives. PRs 86997/87424/87425. ONK 2022.10.
- **#1638339 (Acceptance):** Production Volumes screen wouldn't let users add/edit **non-Manual** rows. Fix PRs 92241/92242. develop pre-2024.04.
- **#1774450 (NCG, Rejected — workaround):** Measurement Entry **auto-fills 0 volumes** for remaining days when auto-gen var = "Volume" → allocation fails. Feasible workaround provided; closed, not fixed in code.

**Rule:** reproduce in **both Web and Classic**; the Web screen is usually the offender (rounding/mask/negatives). Several are explicitly Core/Core-CAN metadata changes.

**Bug IDs:** 1681445, 1647889, 1605706, 1638339, 1774450 · **SF:** 23-00926060, 24-00939019, 23-00906127, 25-01060437 · **Clients:** ONM, ONK, NCG.

---

## 9. Cluster H — Ticketing (Ticket Volume / Analysis Update, QQM)

**Symptom:** ticket grid hides a column, requires a non-required field, or a QQM report drops negative tickets.

**Root causes (dev-confirmed):**
- **#1687126 (PEM, SF 24-00978630, Acceptance):** **Density Variance** column not shown in Ticket Volume Update grid (hidden after row 50 in Classic — Products won't fix Classic — and missing from the Web grid unless bulk/export). Fix: **unhide the column** in Core + Core CAN (also applied to Ticket Analysis Update). PRs 101977/102137/102138/102139.
- **#1389877 (PEM, SF 21-00207544, Ready for QA, 21.23):** "Plus component required" **error** on Ticket Analysis save in Web (shouldn't be required, matching Classic). Root cause (Jennifer Hart): the metadata was correctly set but **lost in the 2021.04 build merges** (`QARCH_CTRL_OBJECT_USE_RELATION.json` in `PEM.TIPS.Metadata`). Fix: restore non-required. 2021.04.
- **#1734750 (ACP, SF 25-01024315, Acceptance — NOT fixed in product):** QQM "Ticket Listing" universe drops **negative ticket** quantities (`DT_Allocated_Ticket_Trans` derived table `OTHER_QTY > 0`). Changing to `<> 0` returns the -2 ticket but creates duplicate rows and shifts S&W%. **Client declined the change** (risk) — derived-table edits are owned by Product Engineering; no fix shipped.

**Bug IDs:** 1687126, 1389877, 1734750 · **SF:** 24-00978630, 21-00207544, 25-01024315 · **Clients:** PEM, ACP. Cross-ref SF skill §11 (truck-ticket import row-limit; ADO #1595913/#1777564).

---

## 10. FIX-VERSION MATRIX

> All `IntegrationBuild` empty → "Fixed-in-build" is **inferred** from PR target branches / iteration / tags. **Confirm in release notes / the client's patch before quoting to a customer.** State key: Closed/Resolved.

| Bug | Cluster | Symptom (short) | State | Fixed-in-build (inferred) | SF case | Client |
|---|---|---|---|---|---|---|
| 1712775 | A | Excel import end-dates 0-vol meter, stops mid-file | Closed | 2024.10-era hotfix (PRs 1137xx/1141xx) | 24-00965985 | ALT |
| 1700609 | A | PK_ALCTRL_MEAS_VOL dup; .csv/config | Closed(Rej) | CONFIG (no code) | 24-00990895 | SUI |
| 219868 | A | ALESVOLIMP skips concurrent writes (sync `>=`) | Closed | ~2020 (PRs 33xxx-35xxx) | 20-00087720 | XCL |
| 1649462 | A | ALESVOLIMP 100k perf | Closed(Rej) | NOT FIXED (perf RCA only) | — | XCL |
| 1681391 | A | "meter is a parent location" import error | Closed | script (data fix) | 24-00973101 | DOH |
| 1396228 | C | DTH→MMBTU, heat=0 | Closed | 2021.10 / 17.3.0 / develop | — | FC-TIPS/UTG |
| 1403818 | C | PRES_BASE_CD=0, MCF not inserting | Closed | 2021.10 / develop | — | FC-TIPS |
| 1433354 | C | IP concurrency "inserts/updates cancelled" | Closed | ESuite.API 17.0.9 / 2021.04 patch | — | UTG |
| 1741530 | C | liquid 0-vol ignored / ghost records | Closed | PR 116109 (PEM DB) | 25-01025108 | PEM |
| 1678596 | C | FlowCal import rounding | Closed | PR 101039 (PEM DB) | 24-00969233 | PEM |
| 1655328 | C | GMAS success but no data < FULL_SYNC_DT | Closed | PR 96108 (CMX) | — | CMX |
| 1442338 | C | GMAS/PI no spawn post-upgrade | Closed | QPEC 17.20.4 / 2022.04 | 22-00251937 | NRM |
| 1686007 | C | IP end-dates meter | Closed(Rej) | NOT REPRO (2024.10) | — | DTM |
| 1811840 | C | meter not transferring to QPTM | Closed | QXCL object-validation override + restart | 26-01102718 | XCL |
| 1435165 | D | MMG rerun 9999 overlap, month fails | Closed | 2020.03→2022.10 / develop | 22-00220682 | ONM |
| 1685847 | D | MMG analysis not generating | Closed | 2022.10 / 2024.04 | 24-00963716 | ONM |
| 1328845 | D | MMG Web field-update error (9999 slice) | Closed | 2021.04 (back to 2020.03) | — | ONM |
| 1352003 | D | MMG no-volume warning missing | Closed | 2021.04 (PRs 53550/53563) | — | ONM |
| 1757914 | E | analysis import won't overwrite (dead-table join) | Closed | PR 118428 / 2023.04 (CHD) | 25-01041981 | CHD |
| 1773646 | E | ALANLIMPFC sync-date param passthrough | Closed | 26.03 (PRs 1234xx; VGP metadata) | 25-01057601 | VGP |
| 1426499 | E | plus-component GPM=0 | Closed | 2021.10 / develop | — | UTG |
| 1377251 | E | FW Factor removed on import | Closed | 2019.10/2021.04/2021.10/2022.04 | 21-00202866 | IAC |
| 1443304 | E | Mol% not recalc on bulk/import | Closed | 2021.10 / 2022.04 / develop | 22-00252293 | PEM |
| 219721 | E | C7+ limit error→warning (Web) | Closed | 2021.10 / develop | — | PEM |
| 1783561 | E | C6+/Hexane+ in "Other" | Closed | PR 124597 (config; go-forward) | 26-01069756 | IACX |
| 1791807 | E | NC5 not converting | Closed | CONFIG (analysis=100%) | 26-01089915 | IPF |
| 1697124 | E | Protrend Mol% < 100 allowed | Closed(Rej) | NOT FIXED | 24-00987145 | PEM |
| 1316787 | E | C5+ report div/0 (crystal) | Closed | PR 49498 (KEY patch) | 20-00098179 | KEY |
| 1574907 | E | analysis pick-list dups (Web) | Closed(Rej) | NOT FIXED (client closed) | — | OXY |
| 1773688 | E | QAZR import SP not truncating | Closed | NOT REPRO (out of policy) | 25-01058203 | AZR |
| 1712833 | F | tiny split decimal → owner 0 (rounding) | Closed | CAN ORA+MSSQL (PRs 1098xx-1110xx) | 25-01002874 | PEM |
| 1354249 | F | shrink/theo/gas-lift wrong on gas stmt | Closed | 2020.11→2021.10 / develop | — | SCX |
| 1434950 | F | posted gas stmt alloc gallons / TIK | Closed | 2021.10 / 2022.04 | 22-00219951 | SCX |
| 1570322 | F | theo 0 after monthly→daily (MONVOLS) | Closed | 2023.04 / develop (go-forward) | 22-00874962 | UTG |
| 1591365 | F | WH info not contractually adjusted | Closed | hotfix/17.24.x-17.25.x / develop | — | MOM |
| 1681445 | G | Meas Vol Web rounds Temp/Prod Hrs | Closed | 2022.10 / 2024.04 | 23-00926060 | ONM |
| 1647889 | G | Meas Entry bulk-edit decimals break alloc | Closed | PRs 945xx/951xx | 24-00939019 | ONK |
| 1605706 | G | Meas Entry negatives not shown | Closed | ONK 2022.10 | 23-00906127 | ONK |
| 1638339 | G | can't edit non-Manual production vols | Closed | develop pre-2024.04 | — | (QGM) |
| 1774450 | G | Meas Entry 0-fills partial month | Closed(Rej) | workaround (not fixed) | 25-01060437 | NCG |
| 1687126 | H | Density Variance column hidden | Closed | Core + Core CAN (PRs 1019xx-1021xx) | 24-00978630 | PEM |
| 1389877 | H | Ticket Analysis plus-comp required (Web) | Closed | 2021.04 (PEM metadata) | 21-00207544 | PEM |
| 1734750 | H | QQM drops negative tickets | Closed | NOT FIXED (client declined) | 25-01024315 | ACP |
| 142562 | A | MEASMETER "Unable to insert Paystation" PK | Resolved | core (PR 16500); add plant_no to QCTRL_METER_PARENT join | — | TCP/core |
| 1408304 | A | ALESVOLIMP "cast not valid" (Oracle) | Closed | 2021.04/2021.10 (PRs 63169/63173/63591) | — | DRS |

---

## 11. DIAGNOSTIC POINTERS

- **Get the failing STEP/PROCESS + plant/facility + prod month + exact error first.** Process names seen: `MEASUREMENT`/`MEASUREMNT`, `MEASMETER`, `WGHTAVGGAS`, `MMALLOC`, `ALESVOLIMP`, `ALANLIMPFC`/`ALESGASIMP`/`ESMEASINT`, `LDMVOLS`/`LDMANLS`/`LDANLYS_RG`, `QIMPVOLD/QIMPEXP`, `MONVOLS`, `GMASIMPORT`/`GMASLDVOLS`, `DOH_MEASPR`/`AMID_MEASF`, `PANIGHTLY` (QPTM alloc), `QPP_IMPORT_ANALYSIS`, `SP_QTIP_ALL_VOL_IMPORT`, `SP_QTIP_IMPORT_ANALYSIS_INTO_QAZR`.
- **Key tables/views:** `STRAN_VOL_DAILY/_MONTHLY`, `STRAN_ANALYSIS_DAILY/_MONTHLY`, `WTRAN_ANALYSIS_MONTHLY`, `QUORUM_VOL_DAILY`, `QUORUM_ANALYSIS_DAILY`, `QTIP_VOLUME_MONTHLY_VW/_DAILY_VW`, `ALCTRL_MEAS_VOL` (PK `PK_ALCTRL_MEAS_VOL`), `ALCTRL_MEAS_VOL_INT_SYNC` (SYNC_DT), `SCTRL_INT_FULLSYNC`/`FULL_SYNC_DT`, `QCTRL_MEAS_VOL`, `QTRAN_ALLOC_VOL` (GAS/HEAT 0 = UOM/pressure/100% issue), `QCTRL_ANALYSIS`/`_COMP`, `QCTRL_MASTER_MTR_GRP_HDR/_DTL`, `SCTRL_MTR_FACILITY` (vs dead `STRAN_MTR_FACILITY_RANGE`), `QCTRL_METER_PARENT`, settlement views `QRPTS_/QPOST_SETTLE_GAS_STMT_*_VW`, `QTRAN_FIXED_FUELS`, `QXREF_CARGO_TICKET`/`DT_Allocated_Ticket_Trans`.
- **Config/code-tables:** `OVERRIDE_PLUS_COMPONENT`, `USE_STRAN_LATEST_TABLES`, code table `24011`/`QCODE_QTY_UOM`, sync-date params `30040` (eSuite) / `26570` (QPTM).
- **End-of-time tell:** any analysis/timeslice ending **12/31/9999** is a bug (should be **12/31/9000**) — Cluster D.
- **Web-vs-Classic:** reproduce in both; Web mask/display-control-type/metadata is usually the offender (Clusters G, E).
- **Repos / where the fix lives:** core `Quorum.TIPS.Database`, `Quorum.TIPS.Reports`, `Quorum.TIPS.Batch(.QPDllTurboTips)`, `Quorum.TIPS.ClassicBatch`, `Quorum.ESuite.API` (`MeterMonthlySampleCommand.cs`), Integration Platform; **client overrides** `<CLIENT>.TIPS.Database` / `.ESuite.Database` / `.TIPS.Metadata` / `.TIPS.Application.QPEC` (PEM, IAC, CHD, VGP, CMX, NRM, ALT, SCX, ONM seen). **Always check the client override first** — many of these are client-specific procs/views/reports.

---

## 12. ESCALATION — is the client's build fixed?

1. **Identify the cluster + lead bug** (tables above). Pull the bug's PR branch list (dev comments) to see which release branches the fix merged to: `develop`, `release/17.x`, `hotfix/17.x.y`, `[2020.03]…[2026.03]`.
2. **Map to the client's build.** Because IntegrationBuild is empty, compare the client's TIPS version against the **inferred build** in §10 and the PR target branches. If the client is **below** the earliest branch the fix merged to (e.g., FW Factor merged 2019.10+; MMG rerun 2020.03+; DTH→MMBTU 2021.10+), the fix is **NOT in their build** → route to Maintenance for a hotfix to their line. Confirm against release notes before promising.
3. **Client-specific fixes** (CHD #1757914, VGP #1773646, PEM views, IAC FW Factor SP, NRM QPEC, SCX/MOM reports) ship via a **client patch with the client repo's latest metadata/DB** — not a core build number; coordinate with the Upgrades/Patch team for that client.
4. **Route to Engineering** when: a measurement/analysis/settlement **batch step** or **view** computes wrong (UOM/pressure/rounding/9999-slice/MONVOLS theo), a **Web screen** loses/rounds/blocks vs Classic, or a stored proc joins a dead table. Provide: failing **step/process**, **plant + prod month**, exact error, client version, repro env.
5. **Route to Cloud Ops / config (no code)** when: `.csv`/import-def/column-order, `USE_STRAN_LATEST_TABLES`/`SCTRL_INT_FULLSYNC`/`FULL_SYNC_DT`, `OVERRIDE_PLUS_COMPONENT`, analysis-not-100% (NC5), parent-location bad rows, FlowCal revision/duplicate events — i.e. the Rejected/CONFIG rows (#1700609, #1791807, #1697124, #1774450, #1655328 workaround, #1811840).
6. **NOT-fixed / dead ends — set expectations:** #1649462 (ALESVOLIMP perf, client closed), #1734750 (QQM neg tickets, client declined), #1697124 (Protrend <100, rejected), #1574907 (analysis pick-list dups, client closed), #1773688/#1686007 (not reproducible). Don't quote a build for these.

---

## NOTES & DATA-QUALITY CAVEATS

- **588 WIQL matches / 54 deep-read.** The keyword set (volume/analysis/ticket/measurement…) is broad; ~half the most-recent 250 were QPTM (pipeline) and dropped per the overlap rules in the header. Team-name leaves (`Guardians of TIPS`/`TIPS'n Tricks` vs `Pirates of Pipeline`/`Pipeline Galaxy`/`Pipeline Titans`) were the main TIPS-vs-QPTM discriminator.
- **All fixed-in-build values are INFERRED** (IntegrationBuild empty on 100% of these bugs) from PR target branches, iteration paths, and version tags — **confirm in release notes / client patch** before customer-facing use.
- **SF↔ADO root-cause divergence:** for ALT 24-00965985 the SF-mined skill cites a USER_ID>30-char trigger truncation; the ADO bug (#1712775) documents the disposition/end-dating logic. Same case, two fix threads — verify which is in the client's patch.
- **#1769377 vs #1773646** are the same VGP SF case (25-01057601): the first (Rejected) was critical-part triage, the second (Verified) carries the real fix. Counted once for the fix.
- Cross-references: SF-mined `SKILL_TIPS_Measurement_Ticketing.md` (TIPS Assistant) §4 (import), §5/§6 (analysis/MMG — ADO #1435165/#1685847 confirmed here), §9 (split decimal), §11 (truck tickets — ADO #1595913/#1777564, not re-mined here).
```
