# SKILL (ADO): QPTM Allocations / PPA / Imbalance — Defect & Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QPTM (My Quorum Gas Pipeline — Pipeline Transaction Management) | **Source:** Azure DevOps closed/resolved **Bugs**, QuorumSoftware org
**Area paths mined:** `QuorumSoftware\Engineering\Energy Transportation\*` **and** `QuorumSoftware\Engineering\Maintenance\Midstream and Transportation\*` (the Maintenance branch is mixed QPTM+TIPS — see overlap caveat below).
**Scope:** the allocation→imbalance→billing chain in QPTM: **ALALLOCATE / STDPDA** batch (split/deadlock/connection failures, fuel-rate resolution), the **PDA Submission** screen & PDA Import (web vs classic parity, agent/meter-split gap validations, scheduled-qty calc, performance), **Reallocation/PPA trigger** pop-ups, **PPA** generation/rerun/unapproval/cashout, **Imbalance** calc/process/report (INACCTACCM, doubling, sequence overflow, external-report performance), **OBA** allocation & IN53 letter, and the **PTR overlay** TIPS→QPTM interface.

> **Use When:** an ADO/SF case is about a QPTM allocation/PPA/imbalance/OBA/PTR symptom and you need (a) has this been seen/fixed before, (b) the root cause, (c) the fix + which release/build carries it, (d) a workaround. For the **TIPS** side of allocation/PPA/imbalance (Settlement/Paystation/gathering), use the companion `SKILL_TIPS_Allocations_PPA_Imbalance.md`. For QPTM nomination/cycle/EDI, use the QPTM nomination skills.

> **Evidence base:** WIQL returned **918** Bug hits (area ∩ title terms: Allocation, ALALLOCATE, PPA, imbalance, reallocation, OBA, PDA, PTR, overlay; Closed/Resolved). After dropping ~296 false substring hits (PDA/PTR/OBA inside "update/captured/global") and ~16 clearly-TIPS rows, **~596 are genuine QPTM allocation-area bugs**. **61 were deep-read** (full Description + ReproSteps + relations + the *entire* dev comment thread) for root cause and fix. Every root-cause/fix claim below cites the real ADO Bug # and the linked SF case observed during mining.

> **CRITICAL — fixed-in-build is INFERRED.** `Microsoft.VSTS.Build.IntegrationBuild` was **empty on every bug** in this set. Fix versions below are inferred from `Planning:YY.NN` tags, "queued for next TIPS YYYY.NN" tags, "cherry-picked into 20xx.xx / develop" dev comments, and linked PR/hotfix items. Treat every build number as **"(inferred — confirm in release notes / the linked PR target branch)"** before telling a customer their build is fixed.

---

## 1. Quick Triage

| Symptom (case wording) | Likely cluster | First check |
|---|---|---|
| `ALALLOCATE` / `PANIGHTLY` fails on **ALSEL_N / ALMAIN / ALNEWPREPR / ALSPLITNEW** with **deadlock 1205** or **SEQ_NO timeout (-1)** | §4A | LDC with locations spanning multiple splits; QTRAN_SEQ / ALSTAG_NOM_HDR contention; indexes + `QARCH_CTRL_ERR_RETRY` retries |
| ALALLOCATE fails with **"database connection was lost"** / `NOTICE_QUEUE_ID` / DLL-not-found, succeeds on rerun | §4B | QPEC↔DB connectivity (QCloud/Azure); **graceful QPEC restart**; for DLL-not-found it's a repo/provisioning bug |
| ALALLOCATE `Rate error NR — unable to resolve rate` (one-sided path) | §4C | one-sided allocation from a PDA still in place; add one-sided fuel rate OR end-date the PDA |
| ALALLOCATE crashes **no error / "One or more errors"** with `BALANCE_ALL_IN_TO_ALL_OUT` on | §4D | SR-dependency array null-ref (Tallgrass config); engine bug #1383448 |
| ALALLOCATE `Sys Error in registered SQL` after upgrade | §4E | bad `PACTRL_TSP_CNFG_CTRL` data → reconvert; or a registered-SQL preprocess syntax bug |
| Index/rate **time-slice** breaks downstream ALALLOCATE (HDR/DTL mismatch) | §4F | web QFC CloneAsNew over-clones DTL; fixed #1796121 |
| PDA Submission **web ≠ classic**: wrong/summed Sched Qty, duplicate daily-alloc rows, can't save, missing columns, varchar→datetime error | §5 | reproduce in CORE; most are web-layer defects in `QPTMAllocationServiceExt_PDA.cs` / `QUIControllerPDASubmission` |
| PDA throws **meter-split / contract-agent gap** validation for dates unrelated to the PDA | §6 | over-broad validation (`...PDASubmission0021` / `QPDAValidator`); fixed family #1659856/#1676753/#1641972 |
| PDA Submission **retrieve takes minutes / ORA-01013 timeout** | §7 | `ALCTRL_PDA_CONF_SCHD_VW` / `CFCTRL_CONF` volume + `USE_PDA_DUR_FOR_SCHED_QTY`; config cap fix #1742027 |
| Reallocation/PPA **pop-up doesn't appear** after Measurement Entry / Contract / Location change | §8 | event-detector loses `ScreenChangeDetail` across the wire (web), or table missing from handler; also check `BLXREF_REALLOC_PPA` (tbl 27310) setup |
| PPA **generated then auto-reversed**, duplicate/extra PPAs, PPA on rerun/unapproval leaves orphans | §9 | TRNX_ID delete missing prod-dt filter; multi-column Meas-Vol change logs 2 PPAs; rerun must re-run current month too |
| Imbalance **volumes doubling/tripling** on report/invoice | §10 | report subreport view sums a duplicated column (BL01); or upstream alloc; check flow-direction/charge-basis |
| Imbalance **INACCTACCM** step slow/out-of-memory/stops | §11 | large gathering company; SQLID_REVERSAL_VOL; stats; the 1593783 core change was **backed out** |
| Imbalance **sequence too large for column** (precision) | §11 | `ACCT_ACTIVITY_DTL_ID` precision 10→19 (#1723573) |
| Allocation **Imbalance report (ALRX24 / IN22 / INX) hangs** for external users | §12 | external XVW joins `QARCH_SEC_USER` over huge `ALHIST_ALLOC`; view rewrite + purge (#1661117) |
| **OBA** contract not getting correct imbalance / IN53 OBA letter missing a meter | §13 | PDA level-101 per service-requestor setup; nom/measurement flow-direction; NULL `REC_QTY` in `NNCTRL_NOM_DTL` |
| **PTR overlay** (TIPS→QPTM) overrides manual override / doubles / drops meters | §14 | client-specific `QPDllTipsPTMIntegration*` / `STGIMBTIPS`; `QTIP_TRAN_PLANT_PTR` staging; WGT attribute |

---

## 2. The chain (where each cluster sits)

```
[Nominations + Measurement Entry] + [PDA Submission (operator TT5 / svc-req TT101) + Contract/Meter-split + Rate/Fuel rates]
      │  (a change here fires the Reallocation/PPA event detector → pop-up → BLTRAN_PPA_EVENT)   ← §8
      ▼  ALALLOCATE  (steps: ALGETLTST, ALSEL_N, ALNEWPREPR/ALMAIN/ALSPLITNEW, ALALLOC_N, ALNOFTFUEL)  ← §4
         · STDPDA / ALLDEFFNOM / ALESVOLIMP run around it
[ALCTRL_ALLOC / ALSTAG_* / QTRAN_ALLOC_VOL  → Daily Allocated Quantity Maintenance]   ← §5 (PDA screen reads/writes here)
      │
      ├──► PPA path (PPA Approval/Status, rerun, unapproval, cashout)  → BLTRAN_PPA_EVENT / QTRAN_TRNX_ID   ← §9
      ├──► IMBALANCE  (INACCTACCM customer-account accumulation → Authorization to Post Imbalances / Customer Account Maint)  ← §10/§11
      │        → QTRAN_IMBAL_ACCT_ACTIVITY_DTL / QTRAN_INV_ACCT_ACT_DTL_VW_2 ; OBA inventory accounts   ← §13
      ├──► BILLING (BLINVGEN → invoice; OBA/IN53 letter)   ← §13, §10 doubling
      └──► PTR overlay interface  TIPS ⇄ QPTM  (QTIP_TRAN_PLANT_PTR / STRAN_PLANT_PTR)   ← §14
```

**Vocabulary:** **PDA** = Pre-Determined Allocation (operator-level TT5 says which service requestors get gas; **level-101** TT says which contracts the SR's gas goes to — both are required for OBA, §13). **ALALLOCATE** = the pipeline allocation batch; **STDPDA** = the standard-PDA step inside the TIPS-Nightly/facility job. **PPA** = Prior Period Adjustment. **Reallocation** = re-run of a prior gas-day's allocation triggered by a back-dated change. **OBA** = Operational Balancing Agreement contract (takes the swing). **PTR** = Plant Thermal Reduction generated in TIPS and overlaid into QPTM. **Split** = an ALMAIN sub-job partitioning locations/gas-days for parallel processing. **`BLXREF_REALLOC_PPA` / code table 27310** = the map of which screen+table column changes trigger a Reallocation vs a PPA.

---

## 3. Decision Tree

```
QPTM allocation/PPA/imbalance case
│
├─ A BATCH process failed?  → get PQID + failing STEP + exact error
│   ├─ deadlock 1205 / SEQ_NO timeout, LDC, multi-split             → §4A  (indexes/retries; long-term split rework #1320322)
│   ├─ "database connection was lost" / NOTICE_QUEUE_ID, rerun OK    → §4B  (QPEC restart — infra, not code)
│   ├─ Rate error NR (one-sided path)                                → §4C  (one-sided fuel rate / end-date the PDA)
│   ├─ no-error crash w/ BALANCE_ALL_IN_TO_ALL_OUT                    → §4D  (#1383448 SR-dependency null-ref)
│   ├─ "Sys Error in registered SQL" / DLL not found                 → §4E  (PACTRL_TSP_CNFG_CTRL data / provisioning)
│   └─ started after an index/rate time-slice                        → §4F  (#1796121 HDR/DTL mismatch)
│
├─ PDA SUBMISSION screen wrong (not a batch crash)?
│   ├─ web ≠ classic (qty summed/duplicated, can't save, columns)    → §5
│   ├─ meter-split / contract-agent GAP validation misfires          → §6
│   └─ retrieve slow / ORA-01013 timeout                             → §7  (config cap USE_PDA_DUR_FOR_SCHED_QTY)
│
├─ Reallocation/PPA POP-UP not appearing after a change?            → §8  (event detector / table 27310 setup)
│
├─ PPA wrong (auto-reversed, extra, orphan after rerun/unapproval)? → §9
│
├─ IMBALANCE?
│   ├─ volumes doubling/tripling                                     → §10 (report view OR upstream alloc)
│   ├─ INACCTACCM slow/OOM/stops                                     → §11
│   ├─ sequence precision overflow                                   → §11 (#1723573)
│   └─ external imbalance report hangs                               → §12
│
├─ OBA contract / IN53 letter wrong?                                → §13
└─ PTR overlay (TIPS↔QPTM) override/doubling/dropped meters?        → §14
```

---

## 4. Cluster A-F — ALALLOCATE / STDPDA batch failures

The single biggest batch signature. **Always get: TSP, accounting/gas day, the failing process-step name, the exact ORA/COM/SQL error, and the Process Queue ID (PQID).** The step name discriminates the sub-cluster.

### 4A. Deadlock 1205 / sequence-timeout on multi-split LDCs (CNP, XCL, CRW)
- **Symptom:** PANIGHTLY ALALLOCATE fails nightly on `ALSEL_N`/`ALNEWPREPR`/`ALSPLITNEW`; `Transaction (Process ID …) was deadlocked … Update into ALSTAG_NOM_HDR failed`; or `SEQ_NO = -1` timeout reading `QTRAN_SEQ`. Manual rerun (or `Gas Day Offset -1`) often succeeds.
- **Root cause (#1320322 / #228999):** for LDCs, the `THRESHOLD_FOR_LARGE_LOC_ID_GAS_DAY` config spreads one large location's gas-days across **multiple ALMAIN splits**; those splits then concurrently `Open Transaction → GetNextSeq → Update ALSTAG_NOM_HDR` and **deadlock**, and while the txn is open `QTRAN_SEQ` is locked → the sequence-lookup timeout in a *different* split.
- **Fixes / workarounds applied:**
  - **Short-term (#1320322):** add a **Lock on the `ALNEWPREPR` step** (lock setup) so splits don't collide; CNP unblocked. Long-term core ask (process locations spanning multiple splits *first*, then spawn splits) was **moved to Core Engineering roadmap, never delivered as a maintenance fix**.
  - **#228999:** adding **two non-clustered indexes** on `ALTRAN_ALLOC_SEL (SPLIT_NO, PROCESS_QUEUE_ID, LOC_ID)` etc. stopped CNP's nightly failures ("4 nights of success"); plus increase deadlock retries via **`QARCH_CTRL_ERR_RETRY`** (logs show `ATTEMPT 8 OF 10` succeeding), and tune `MAX_LARGE_LOC_ID_GAS_DAY_RECS_IN_ONE_SUBSPLIT` / `MAX_SPLITS_FOR_LARGE_LOC_ID_GAS_DAY` (e.g. 400/20 → 1000/10) to reduce split count. Indexes were treated as client-specific (CNP v4 patch) pending core vetting.
- **Bug IDs:** #1320322 (Rejected, short-term lock + roadmap), #228999 (Verified, indexes/retries), #234047 (CNP ALESVOLIMP connection — see §4B), related #208124, #1321323.
- **SF:** 21-00107073, 20-00090618, 20-00092335.

### 4B. QPEC ↔ DB connection drops / DLL-not-found (CRW, APL, DTE, EQC)
- **Symptom:** intermittent ALALLOCATE failure with `database connection was lost`, `COM Error … Unable to retrieve sequence value for NOTICE_QUEUE_ID`, or `Dll Not Found QPDLLPIPELINEMGRAL_<CLIENT>`. Subsequent reruns succeed.
- **Root cause:** the QPEC temporarily loses its DB connection (QCloud/Azure infra), and on older builds the QPEC stays in a **bad state** afterward (#150654). It is **not an allocation-logic bug**. Newer QFC handles transient outages gracefully; old client builds need a **graceful QPEC restart**. DLL-not-found (#1704047, EQC) is a **provisioning bug** — the client release was pointed at core `Quorum.QPTM.Application.QPEC` instead of the client `EQC.QPTM.*` repo → needs a DevOps re-provision, not engineering.
- **Fix/workaround:** graceful QPEC restart (immediate); confirm QPEC.ini `UseCurrentWorkingDirectory`; route DLL/provisioning issues to DevOps; route persistent connection drops to Cloud Ops (APL/CRW were closed as infra). Long-term graceful-recovery fix lives in newer QFC (#153810) — **not back-patched** to old client builds (deemed too invasive, infrequent).
- **Bug IDs:** #150654 (APL, Rejected — graceful restart, long-term #153810), #210845 (CRW, Rejected — infra), #234047 (CNP, Rejected — DB connectivity, DBAs to check open txns on `ALCTRL_MEAS_VOL`), #1704047 (EQC, Rejected — provisioning), #218029 (ENT STDPDA "one or more errors" — transient, cleared after ENT patch).
- **SF:** 20-00084643, 20-00092335, 24-00994160.

### 4C. One-sided path / "Rate error NR" (HPE)
- **Symptom:** `ALMAIN … Rate error code is NR. Unable to resolve the rate … rec_loc_id=011290, del_loc_id=(blank)` (`QAllocFuelPct.cpp`).
- **Root cause (#1620789):** an end-dated **PDA still in place** created a **one-sided allocation** (rec location, null del location) for which **no fuel rate existed**.
- **Fix/workaround:** either add a **one-sided fuel rate** (edit the Max-Tariff Fuel rate, ALL_LOC rec / no del / 0%) — same pattern as #1434265 / SIRT 113512 — **or** end-date the PDA on the day the meter's last measured volumes/noms existed so the one-sided path disappears (the cleaner fix HPE took).
- **Bug IDs:** #1620789 (Verified), related #1434265. **SF:** 23-00918740.

### 4D. SR-dependency null-ref crash (TEP / Tallgrass)
- **Symptom:** ALALLOCATE fails on `ALALLOC_N` with an ambiguous/no error.
- **Root cause (#1383448):** in `QPipelineAllocationEngine::Allocate()`, when `BALANCE_ALL_IN_TO_ALL_OUT` (Tallgrass-on) and `SR_DEPENDENCY_CHECK_ENABLED` are both on, the code assumes the **SR-Dependency array and To-Point array are the same size**; when they aren't it asserts but then accesses anyway → **null-ref crash with no error**. `SetSRDependencyArray()` (called from `SetSRDependencyOrder()` / `AddPDANodes()`) is the culprit.
- **Fix:** technical core hardening of the SR-dependency check; verified across a full accounting month in TEP_HD_TST17. **Inferred fix: 21.18–21.23 era** (Planning:21.18/19/20 tags; ready-for-QA in 21.23). Confirm in release notes.
- **Bug IDs:** #1383448 (Moved to Ready for QA), related #1545750, #1316915 (ETC prior).

### 4E. Registered-SQL / config-data errors
- **Symptom:** `Sys Error in registered SQL` running allocations for a TSP (#1706632); or step stops because config data is bad.
- **Root cause/fix:** #1706632 — **bad `PACTRL_TSP_CNFG_CTRL` data**; deleting + reconverting that row for the two TSPs resolved it (data fix). A registered-SQL preprocess (`SQLID_PreProcess_InsPathDailyReceipt`) syntax issue was suspected. Registered SQLs are rarely changed → suspect **data found by the query**, not the SQL.
- **Bug IDs:** #1706632 (Rejected — data fix). **SF:** 25-00996952.

### 4F. Index/rate time-slice → HDR/DTL mismatch → ALALLOCATE failure (ENT)
- **Symptom (#1796121):** after time-slicing an Index (changing Effective Date From to mid-month) in **Index Maintenance**, `RTCTRL_INDEX_HDR` gets the new slice but `RTCTRL_INDEX_DTL` stays aligned to month-start → header/detail out of sync → ALALLOCATE fails on inconsistent rate/index data.
- **Root cause:** **Web's QFC `CloneAsNew` deep-clones ALL detail to both headers** during a time-slice, unlike Classic which only works with the filtered grid. Collateral from #1789247.
- **Fix:** `UIController` (DoClone + AddEffectiveDatedItem) now **filters cloned DTL** to those whose `INDEX_START_DT` falls in the header's range (matches Classic); replaced `RemoveOutOfRangeIndexDetails` with `AdjustIndexDetailsForTimeSlice` (clamps DTL dates to header boundaries); fixed per-header scoping in validation Rules 002/004/006. **Cherry-picked into 2025.04, 2025.10, 2026.04, develop** (HOTFIX tag).
- **Bug IDs:** #1796121 (Acceptance), related #1789247, #1804722.

**Fix recipe for §4:** PQID + step + exact error first. Deadlock/SEQ_NO → §4A (indexes/retries/lock, not a quick code fix). "Connection lost"/DLL → §4B (restart / DevOps). NR rate → §4C (one-sided rate or end-date PDA). No-error crash on Tallgrass → §4D. After a time-slice → §4F (confirm the 2025.04+ cherry-pick). Many §4 items are **Rejected = no code change** (infra/data/config) — don't escalate to engineering before ruling those out.

---

## 5. Cluster — PDA Submission web ≠ classic (screen defects)

The largest *screen* cluster. Pattern: **reproducible in core/web, behaves correctly in Classic** → a web-layer (`Quorum.QPTM.Web`) defect in `QPTMAllocationServiceExt_PDA.cs` / `QUIControllerPDASubmission`. Most are **fixed in 2024.04+ and not back-ported** to 2021/2022 builds (workaround: use Classic).

| Symptom | Root cause | Fix / build (inferred) | Bug / SF |
|---|---|---|---|
| Loading effective noms **sums Sched Qty** for records with the same UP name (web only) | `CalcSchedQty()` summed quantities for repeated UP names; gated by config `ALLOC_PDA_CALC_SCHD` | Modified to display individual nominated qtys; **in 2024.04 & 2024.10 (beta.117), NOT 2022.10** | #1664615 / 24-00954644 |
| New **Swing PDA at level 101** → `conversion of varchar to datetime out of range` | `GetPDAHeaders()` passed locId/srBpNo/pdaDurCd where a DateTime was expected (`EffDateFromOriginal/ToOriginal` not set in `QUIControllerPDASubmission`) | Fix to date handling in GetPDAHeaders; reproducible on generic TSP 26001 → core bug | #1639510 / 23-00933210 (also fixes #1648669) |
| Web PDA creates **duplicate daily-allocated rows** (6 instead of 3) → imbalances | extra `ALLOC_METH_CD='PRT'` intermediate-tier rows from `CreateIntermediateTiers()` in `ALNEWPREPR`; web path differs from classic | Merging #1387806 back into 2021.04 fixed it | #1603193 / 23-00899058 |
| Daily allocation **Sched Qty not picked up / wrong (12k vs 10k)** | PDA not consumed correctly | dup of #1387806 | #1386772 |
| **Alloc Method drop-down shows only "Test"** (classic), **0-nom shippers not displayed**, read-only columns editable, grid doesn't fit, missing Svc-Req column, etc. | assorted web/classic parity gaps | several fixed in web; **classic-only ones now WON'T be fixed** ("we are not fixing bugs in classic" — #1700786) | #1700786, #1568117/22-00855662, #1540663-667, #1597079, #1611693 |

**Fix recipe:** reproduce in CORE first (proves it's not client data). If it's web-only and classic is correct, it's a `*ServiceExt_PDA.cs` / `QUIController` defect — check whether the fix already shipped in 2024.04/2024.10 (most did) and whether the client has consumed that master; the standing workaround is **enter the PDA in Classic**. Classic-only defects are no longer fixed.

---

## 6. Cluster — PDA meter-split / contract-agent GAP validation misfires

A distinct **validation** family: PDA Submission/Import throws a *Meter Split* or *Contract Agent* "gaps … during the PDA's effective date range" error for date ranges that **don't overlap** the PDA being edited, blocking the save/import.

- **Root cause:** the gap validator considered **all** meter-split / contract-agent timeslices (and agents whose effective start predates the contract), not just those matching the same SR-BA + contract + meter relationship within the PDA's effective dates.
- **Fixes (a chained family — each tightened the filter for a new scenario the prior fix missed):**
  - **#1611693 (MKW, 23-00911394):** original "unable to save" fix; requires contract eff dates ≥ agent eff-date-from.
  - **#1659856 (ONM, 24-00952959):** agent-change-between-timeslices scenario not covered by MKW fix; validator now lines up agent vs PDA effective dates. **PR 97924 [2024.04], PR 97925 [develop]** → **2024.04 + develop; not R1/2022.10**.
  - **#1676753 (ONM, 24-00967808):** meter-split gap unrelated to the PDA range; added eff-date check to the PDA gap validations (`QTIPSValidationPDASubmission0021_MtrCtrBaRelatedAndEffectiveRange`). **PR 99814 [2022.10]**. Verified MSSQL+Oracle R1 SUP.
  - **#1641972 (ETP, 23-00929063):** PDA **Import** raising the same `QPDAValidator-ValidateMtrCtrEffDateAndSvcReq` warning when meter-split eff dates overlap the agent dates (import used the agent's SR instead of the contract's General-tab SR). Code change brought in the correct SR; reduced ETP warnings 321→29 (the 29 remaining were legit). **PR 97046; May 2024 patch.**
  - **#1768194 (PML, 25-01054999):** same root cause as ONM; **fix NOT patched back to 2021** → workaround = update the PDA in **Classic** (the error is web-only validation).
- **SF:** 23-00911394, 24-00952959, 24-00967808, 23-00929063, 25-01054999.
- **Workaround when unpatched:** edit/import the PDA in **Classic** (the over-broad validation is web-side); or correct the contract-agent / meter-split eff dates so there is genuinely no gap.

---

## 7. Cluster — PDA Submission performance (ETC) — config cap fix

- **Symptom (#1691916 / #1742027, ETC 24-00983745):** PDA Submission retrieve takes **3–5 min in web (ORA-01013 timeout)** and **up to 45 min in Classic (`ALLDEFFNOM`/`UpdateScheduledEngQty`)**. Not reproducible in core.
- **Root cause:** the screen's `ALCTRL_PDA_CONF_SCHD_VW` (4 UNION'd queries) joins **`CFCTRL_CONF`** which for ETC holds **years** of confirmation data (back to 2021; an `IX8_CFCTRL_CONF` index added for TEP in #1551209 made it worse on Oracle, which lacks SQL Server "include" columns). The scheduled-qty calc (`USE_PDA_DUR_FOR_SCHED_QTY=true`, ETC & DTE only) recomputes Sched Qty over the **entire PDA date range**.
- **Fix:** new config to **cap how far back scheduled-qty is calculated** (e.g. 3 months) when `USE_PDA_DUR_FOR_SCHED_QTY` is on; classic `ALLDEFFNOM` sped from minutes→seconds; **web required a larger rewrite** (moved to a feature). With config set, ETC retrieve dropped to ~10–30s. **Tags: HOTFIX, Client Code Change, Core Code Change** (#1742027). Build inferred 2024.04/2024.10 hotfix — confirm.
- **Workaround:** set the new back-cap config; short term, turn `USE_PDA_DUR_FOR_SCHED_QTY` **off** (only ETC/DTE have it on); add a time-slice (shaved 30s–1:15 in tests).
- **Bug IDs:** #1691916 (Acceptance), #1742027 (Acceptance, HOTFIX), related #1551209 (TEP IX8 index), #1647121 (5.82s perf regression in 2024.04).

---

## 8. Cluster — Reallocation/PPA pop-up not triggering

When a back-dated change should fire the **Reallocation/PPA Maintenance** pop-up (and log to `BLTRAN_PPA_EVENT`) but doesn't.

- **Root cause family 1 — event detail lost across the wire (web) (#228510):** in `QEventDetectorContainerBase.Evaluate()` the `QPPAEventDetector` **cleared `screenChangeDetails`** (lines 63–64 of `QPPAEventDetector.cs`) before `SetupEventNotify()`, unlike `QReallocEventDetector`/`QRRCEventDetector`; and `screenChange.ScreenChangeDetail` arrived **empty on the MT side** (lost in web→MT serialization). Collateral from #204170. **Hotfixed back to 2020.09** (Planning:20.20-23).
- **Root cause family 2 — table missing from the change handler (#1773033, ENT Panaya 90):** `HandleGenericScreenChangeEvent` didn't include **`SCTRL_RELATED_CTR`** in its table list, so `HandleContractMaintenanceChange` never fired and `PPAReallocationDialogData.ReallocateSelect` was empty → no pop-up when changing a **Shared MDQ Related Contract**. Adding the table fixed it. **Cherry-picked 2025.04, 2025.10, develop**; HOTFIX (planned 1/16). *Note:* by design the pop-up does **not** re-fire if an unprocessed PPA already exists for that contract+prod-month (avoids dup `BLTRAN_PPA_EVENT`), and only fires for **closed** accounting months.
- **Setup, not a bug (#1761005, ONI):** measurement-entry change didn't trigger realloc → resolved by fixing **code table 27310 / `BLXREF_REALLOC_PPA`** so `ALCTRL_MEAS_VOL` had **reallocate-ind checked, PPA-ind unchecked**; also allocations must have already been run (a row in `ALTRAN_ALLOC_STAT` for the gas-day range) or the trigger is lost.
- **Expected behavior / never worked in classic (#1780199, ENT Defect 110):** Location Maintenance fields (Position of Valve, Purpose, Status, Capacity/Rate Area) are **not valid PPA/realloc triggers**; only loc-group/attribute changes trigger. Closed as not-a-bug; the broader "PPA triggers for all gFlow screens" set (#1779975/#1780431/#1773031) moved to core backlog/feature.
- **Older (#197579/#184982, ONG):** Rate Maintenance pop-up appearing **despite** 27310 setup unchecking `QTY_RETAINED_PCT` → fixed; hotfixed into 2020.04.
- **First check:** for "pop-up missing," verify **table 27310 / `BLXREF_REALLOC_PPA`** has the right reallocate/PPA flags for that screen+table+column, that allocations were already run for the gas day, and that the accounting month is **closed** (open months don't pop). Then suspect the web event-detector bugs above.
- **Bug IDs:** #228510, #1773033, #1761005, #1780199, #197579/#184982; related #1779975, #1780431, #1773031, #1761743.
- **SF:** 24-00946… (ENT Panaya), 22-00827029-adjacent.

---

## 9. Cluster — PPA generation / rerun / unapproval / cashout

| Symptom | Root cause | Fix / build (inferred) | Bug / SF |
|---|---|---|---|
| PPA **unapprove one month** leaves **orphan in `QTRAN_TRNX_ID`** (still on Partially-Approved PPA report; blocks Company Post) | `SQLID m_DEL_MTR_TRNX_PPA` was **missing the Prod-Dt filter** when deleting from `QTRAN_TRNX_ID` | added prod-dt-scoped delete; **hotfix to 2022.10 (+ 2020.03)** | #1639010 / 23-00935744 |
| **PPA on same month as a Rerun** → CO/R records not purged from `QTRAN_TRNX_ID`/`QTRAN_PAYSTATION` | rerun flips PPA→rerun but didn't delete PPA-specific data (different RUN_ID; query looked for `REC_STATUS_CD='CO'` not `'OR'`) | added delete script for that RUN_ID; **must re-run the CURRENT month after the rerun** (current-month run purges by RUN_ID). 2020.03 + R2 SUP | #1647498 / 24-00942120 (collateral of #1619944) |
| **Two PPAs logged** when changing 2 columns on **Measured Volumes** at once (web) | a PK change = delete+add (2 PPAs is correct); a non-PK attribute change should log 1; web logged 2 for both | dedupe to distinct PlantNo+MeterNo+ProdDate+UnitTimeCode in `ResolveAdjustments`; ultimately **Products decided web behavior is acceptable / not a bug** (matches data model) | #1681065 / 24-00972314 |
| **PPA generated then auto-reversed** without restating (BLINVGEN), only after Azure migration, one TSP/pool contract | **never reproduced**; suspected MT **rate cache** in a bad state | workaround = **reset MT cache + reprocess PPAs / rerun BLINVGEN**; closed unreproduced | #1685500 + #1725310 / 24-00973258 |
| **PPA doesn't insert records into Measured Volumes** after approval | PPA→Measured-Volume sync (`QSysFuncAreaUtility`) was **only partially ported to web** (CCT only, not Meas Vol) | smaller targeted port for Meas Vol; **merged to 2022.10 (+2022.04)** | #1547652 / 22-00289018 |
| **Erroneous PPAs** with trigger source "Contract"/"Inventory Balance-CICO Change" appear with no alloc change | not reproduced; PPAs were deleted/unapproved; suspected CICO / manual change | unapprove the bad PPAs; closed unreproduced (data) | #1659737 / 24-00950828; also #1641247/23-00935946 |
| **PPA cashouts intermittently not charged** (random contracts) | not reproduced (client-only) | closed insufficient-info | #1644043 / 23-00936358 |
| ENT gFlow **rerun cashout not sent to TIPS** when no PPA exists in QPTM for that acct/prod-date combo | client-specific `STGIMBTIPS` doesn't send data when `BLTRAN_STAG_IMB_OVRLY` is empty for the combo | update `STGIMBTIPS` to send latest data for rerun months; **hotfix 2024.04** (later reframed as ENT enhancement) | #1760037 / 25-01045831 |

**Fix recipe:** for rerun/unapproval orphans, the family is **delete-statement scoping in `QTRAN_TRNX_ID`** (#1639010 prod-dt filter; #1647498 RUN_ID) — and operationally the client must **re-run the current month after a rerun**. "Auto-reversed PPA after Azure" = MT cache reset + reprocess (no code fix found). Many PPA "wrong" cases are **not reproducible** and close as data/customer — verify there was an actual triggering change before escalating.

---

## 10. Cluster — Imbalance volumes doubling/tripling

- **Most common true defect — a report subreport (#1733867, HEP/STX):** the **Invoice Documents report BL01 / `QRPTS_INVOICE_ACCT_MGR.RPT`** subreport `Invoice Details Acc Mgr.rpt` formula `BILLED_VOL` **sums `WHIV_HV`** which the view `QRPTS_INVOICE_DTL_VW` returns **duplicated** (same volume, different RATE rows) → billed volume doubles/triples while the invoice **amount stays correct**. Fix = add a `TRAN…` condition to the `BILLED_VOL` formula so it doesn't sum the duplicate. Core report (not Crude). **Approved by QA; queued for TIPS 2022.04** (HEP PRD 6/23). #1733867 / 24-… (HEP STX).
- **Imbalance-doubling from upstream allocation/displacement** rather than the report: e.g. #1723503 (ETP daily imbalance vertical view duplicates), #1733867-adjacent. Always check whether the **allocation** itself (flow direction, displacement, OBA combine) is doubling before blaming imbalance.
- **Reallocation-of-OBA-PDA "double volume" on invoice (#1813295, WIT 26-01103426)** — *config, not code*: with **no active OBA PDA**, BLINVGEN wrote the **receipt** allocation as **two invoice-input rows** (CHARGE_BASIS `REC` transport + `RECF` receipt fuel, each 8,600) that merged into one doubled $0 line (8,600+8,600=17,200). **Root cause:** `BLXREF_TOS_CHARGE_BASIS.SHOW_QTY_INVOICE_IND = 1` for TOS=`ITS` charge bases `REC`/`RECF`. **Fix:** set `SHOW_QTY_INVOICE_IND = 0` for `TSP_NO=1, TOS_CD='ITS', CHARGE_BASIS_CD IN ('REC','RECF')`, re-run BLINVGEN. (Allocation output in `ALCTRL_ALLOC` was correct — clean 8,600 rec + 8,600 del.) #1813295 (Acceptance, dup #1813294).
- **New delivery meter not in imbalance (#1625672, MOM 23-00924115)** — *data/config*: meter's volume missing from `QTRAN_INV_ACCT_ACT_DTL_VW_2`; root cause was **gas analysis / imbalance type pulling contractual-adjusted instead of standard quantity**. Config fix.

**Fix recipe:** if the **invoice amount is right but the volume is doubled**, it's a **report/view sum bug** (#1733867) — check the report's `BILLED_VOL`-type formula and whether its view returns duplicate rows per rate. If the *amount* is also wrong, suspect **allocation/charge-basis config** (#1813295) or **gas analysis / imbalance type** (#1625672).

---

## 11. Cluster — Imbalance process (INACCTACCM) performance & failures

- **INACCTACCM slow / out-of-memory / stops (ET/EMP, ONM):** `INACCTACCM` (Customer Account Accumulation) and `SQLID_REVERSAL_VOL` run for hours / hit memory errors for large gathering companies (Enable co 3200; ONM after Patch 15).
  - **Key lesson:** the core performance change in **#1593783 was BACKED OUT** because it caused collateral (ONM Patch-15 regression #1599265 — imbalance went from 5 min to 6.5–17 hours). The ET-specific rework was redone behind a **config** under **#1596532**. So: **do not assume a generic INACCTACCM "fix" is safe**; the 1593783 change is reverted in core. Stats/index health and Oracle version (12c vs 19c optimizer) heavily influence run time.
  - **Bug IDs:** #1593783 (Verified, backed out), #1599265 (Verified, collateral, backed out), #1596532 (config-gated ET rework), related #1593048, #1596532, #1621669/#1619365 (ET/EMP post-go-live perf). **SF:** 23-00901236.
- **Sequence precision overflow (#1723573, ETP 25-01014345):** `INACCTACCM` fails `PL/SQL numeric or value error: number precision too large` because `QTRAN_IMBAL_ACCT_ACTIVITY_D_SQ` exceeded the column precision (seq 10000000032 = 11 digits vs precision 10). **Fix:** increased `ACCT_ACTIVITY_DTL_ID` precision **10 → 19** (DB PRs 110407/110411/110413 for 2024.04 / 2020.03 / develop; code-gen PRs 110562/110568/110569). **SF:** 25-01014345.

**Fix recipe:** for INACCTACCM slowness, gather **stats / rebuild indexes** first, confirm Oracle version, and **do not re-apply the reverted #1593783 change** — the supported perf path is #1596532 (config-gated). For precision errors, it's the seq/column-width fix (#1723573).

---

## 12. Cluster — Allocation Imbalance report hangs for external users (ONK)

- **Symptom (#1661117, ONK 24-00946909):** the **Allocation Imbalance external report (ALRX24 / `RPT_ALR_24` daily-with-reversals)** runs for **hours and returns blank** for external users.
- **Root cause:** the **external** view `ALRPTS_24_DLY_IMB_REV_XVW` wraps the internal `ALRPTS_24_DLY_IMB_REV_VW` and **joins `QARCH_SEC_USER`**, returning ~307k rows over a huge `ALHIST_ALLOC` (ONK keeps 13 years / 10M+ rows). The prod-month filter logic was the odd Month/Year/`<=`/`>=` form (vs AL_03's clean `PROD_MTH=`), and a column alias bug (`REC_LOC_NM` duplicated instead of `REC_ZONE_NM`).
- **Fix:** rewrite the external view to **filter by the logged-in user's `SEC_USER_ID`/`BP_NO` inside the join** (got 3-4s for a single user / ~6 min overall), fix the AL_24 view column aliases (both MSSQL & Oracle, VW + XVW), align prod-month logic with AL_03, and **purge `ALHIST_ALLOC`** beyond the retention need (ONK holds back to 3/2011). **PR 101657 (rpt), 101759/101762 (view) for develop+2022.10; DB Change #1692315.** Hotfix on hold (tracked via SF).
- **Bug IDs:** #1661117 (Verified), related #1742657 (same report, repeat). **SF:** 24-00946909.

---

## 13. Cluster — OBA allocation & IN53 OBA letter

- **OBA contract not getting correct imbalance (#1621428, TEP 23-00918446)** — *setup/expected*: OBA off by 4,970 DTH because **level-101 PDAs must be set up per service-requestor**, not just per operator; one SR (1244) had **no alloc method** so it defaulted to prorata instead of swing. Closed as data/setup — *the swing methodology requires the SR-level (101) PDA*. Not reproducible in CORE.
- **OBA inventory discrepancy off by a few DTH across TSPs (#1703871, TEP 24-00984072)** — intermittent; debugging found the **PPA record was correct but `Alloc Rec` was miscalculated** (15775 vs 15773) — suspected scheduled-volume PPA handling in the customer-account accumulation. Could only reproduce on the UPG env after reopening closed months; closed pending a reproducible open-month data cut.
- **IN53 OBA letter missing a meter (#1768545, NMGC 25-01056321)** — *data*: delivery loc 00004460 absent from the IN53 letter because `NNCTRL_NOM_DTL.REC_QTY` was **NULL** for that loc (a working loc had no NULLs); fix is to add the **delivery loc to the OBA contract** / correct the nom data. Earlier IN53 perf/closed-month issues: #1539233 (perf, 21-00107410), #1548726 (closed accounting months, 22-00289364), #1564969/#1458237 (loc not pulled, 22-00830471/21-00212464).
- **First check (OBA):** verify **level-101 PDA per service-requestor with a swing alloc method**, the **delivery loc is on the OBA contract**, and `NNCTRL_NOM_DTL` has no NULL `REC_QTY` for the missing loc. Most OBA "wrong" cases are setup/data, not engine bugs.

---

## 14. Cluster — PTR overlay interface (TIPS → QPTM)

The client-specific interface that overlays TIPS-generated PTR into QPTM (`QTIP_TRAN_PLANT_PTR` / `STRAN_PLANT_PTR`; ENT/EPCO `QPDllTipsPTMIntegration*`, `QSQL_GenerateSharedPTR.cpp`).

| Symptom | Root cause | Fix | Bug / SF |
|---|---|---|---|
| PTR overlay **overrides a manual PTR override** in QPTM for current & PPA months (ENT, meter 01880) | interface consumed PTR from the staging table even when the **WGT (Well-Head-Gathering) attribute was unchecked** | client-specific fix so manual override is kept for non-WGT locations (current & PPA months); **PR 78677, ENT-specific** | #1567953 / 22-00827029 |
| Wellhead interface **PTR doubling** (EPCO/EPCO WAH) | **two rows in `SCTRL_BA_USAGE`** for the doubled meters; this is a **TIPS** issue, surfaced by a prior change (#1369722/#1369719, "Change Requirements that Drive PTR Generation") that was **supposed to be reverted but wasn't** | revert PR 68144 (`QSQL_GenerateSharedPTR.cpp`); client-specific hotfix | #1600026 / (EPCO); ties to #1567953 |
| PTR interface **drops meters randomly** for YOK plant (EPCO) | `qptm_rpt_22_ptr_by_k_vw` union losing rows on a join (eff-date/`RUN_ID = MAX` subquery); **never reproduced internally** | Deferred — held data cut for re-occurrence | #1409048 / 21-00212509 |

- **Lesson (from EPCO's own feedback on #1600026):** when testing a PTR fix, **run the actual PTR generation process in TIPS** rather than only staging rows into `QTIP_TRAN_PLANT_PTR` — staging-only testing missed the doubling collateral.
- **First check:** PTR issues are **TIPS-side / client-specific interface** problems — check `SCTRL_BA_USAGE` for duplicate rows (doubling), the **WGT attribute** (override consumption), and whether a "PTR generation requirements" change (#1369722) is present that should have been reverted.

---

## 15. Fix-Version Matrix

> IntegrationBuild empty on all; "fixed-in-build" inferred from Planning tags / "cherry-picked" comments / linked PR target branches. **Confirm in release notes.**

| Bug | Symptom (short) | State / Reason | Fixed-in-build (inferred) | SF case | Client |
|---|---|---|---|---|---|
| #1796121 | Index time-slice → HDR/DTL mismatch → ALALLOCATE fail | Closed / Acceptance | **2025.04, 2025.10, 2026.04, develop** (cherry-picked; HOTFIX) | — | ENT |
| #1773033 | Shared-MDQ Related-K change doesn't trigger Realloc/PPA | Closed / Acceptance | **2025.04, 2025.10, develop** (HOTFIX ~Jan) | — | ENT (Panaya 90) |
| #1639010 | PPA unapprove orphan in QTRAN_TRNX_ID (missing prod-dt filter) | Closed / Acceptance | **2022.10 + 2020.03** | 23-00935744 | ONM |
| #1647498 | PPA same-month-as-rerun CO/R not purged | Closed / Acceptance | **2020.03 + R2 SUP** | 24-00942120 | ONM |
| #1659856 | PDA agent-change-between-timeslices validation | Closed / Acceptance | **2024.04 + develop** (PR 97924/97925); not R1/2022.10 | 24-00952959 | ONM |
| #1676753 | PDA meter-split gap validation over-broad | Closed / Ready-QA | **2022.10** (PR 99814) + later | 24-00967808 | ONM |
| #1641972 | PDA Import wrong SR on agent overlap | Closed / Acceptance | **May 2024 patch** (PR 97046); 2024.04 | 23-00929063 | ETP |
| #1664615 | Load-eff-noms sums Sched Qty (web) | Closed / Acceptance | **2024.04 & 2024.10 (beta.117)**; not 2022.10 | 24-00954644 | ETC |
| #1639510 | New Swing PDA varchar→datetime error | Closed / Ready-QA | core (generic TSP 26001); spring release | 23-00933210 | (Great Basin) |
| #1603193 | Web PDA duplicate daily-alloc rows | Closed / Verified | **2021.04** (merge #1387806) | 23-00899058 | HPE |
| #1742027 / #1691916 | PDA Submission perf — back-cap config | Closed / Acceptance | **2024.04/2024.10 hotfix** (Client+Core code change) | 24-00983745 | ETC |
| #228510 | Realloc pop-up missing on Measurement Entry (web) | Closed / Ready-QA | **2020.09** (Planning 20.20-23) | — | core |
| #197579 | Rate-Maint realloc pop-up despite 27310 | Closed / Ready-QA | **2020.04** | — | ONG |
| #1547652 | PPA not inserting Measured Volumes | Closed / Acceptance | **2022.10 + 2022.04** | 22-00289018 | UTG |
| #1733867 | Imbalance volumes doubling (BL01 report) | Closed / Acceptance | **TIPS 2022.04** (core report) | — | HEP/STX |
| #1723573 | Imbalance seq precision 10→19 | Closed / Acceptance | **2024.04, 2020.03, develop** (PRs 110407/11/13) | 25-01014345 | ETP |
| #1661117 | Alloc Imbalance external report hangs | Closed / Verified | **develop + 2022.10** (PR 101657; DB #1692315) | 24-00946909 | ONK |
| #1813295 | Reallocation-of-OBA-PDA double volume on invoice | Closed / Acceptance | **CONFIG** (SHOW_QTY_INVOICE_IND=0) — no build | 26-01103426 | WIT |
| #1761005 | Realloc pop-up missing after Meas Entry | Closed / Acceptance | **CONFIG** (table 27310 / BLXREF_REALLOC_PPA) | — | ONI |
| #1706632 | ALALLOCATE registered-SQL error | Closed / Rejected | **DATA** (reconvert PACTRL_TSP_CNFG_CTRL) | 25-00996952 | (TSP 24/8925) |
| #1620789 | ALALLOCATE rate-error NR one-sided path | Closed / Verified | **CONFIG/DATA** (one-sided rate or end-date PDA) | 23-00918740 | HPE |
| #228999 | ALALLOCATE deadlock/SEQ timeout | Closed / Verified | **client indexes + QARCH_CTRL_ERR_RETRY** (CNP v4 patch) | 20-00090618 | CNP |
| #1320322 | ALALLOCATE multi-split deadlock | Closed / Rejected | **lock on ALNEWPREPR**; long-term → Core roadmap (unshipped) | 21-00107073 | CNP |
| #1383448 | ALALLOCATE SR-dependency null-ref crash | Closed / Ready-QA | **~21.18–21.23** (Planning tags) | — | TEP/Tallgrass |
| #1567953 | PTR overlay overrides manual override | Closed / Acceptance | **ENT client-specific** (PR 78677) | 22-00827029 | ENT |
| #1600026 | Wellhead PTR doubling | Closed / Acceptance | **EPCO client-specific** (revert PR 68144) | — | EPCO |
| #1681065 | Two PPAs on multi-column Meas-Vol change | Closed / Acceptance | **NOT-A-BUG** (web behavior accepted) | 24-00972314 | ONM |
| #1593783 / #1599265 | INACCTACCM perf | Closed / Verified | **change BACKED OUT**; perf via config #1596532 | 23-00901236 | ET/ONM |
| #1768545 | IN53 OBA letter missing meter | Closed / Acceptance | **DATA** (NULL REC_QTY / add del loc to OBA) | 25-01056321 | NMGC |
| #1768194 | PDA agent gap validation (2021) | Closed / Rejected | **NOT patched to 2021** — workaround Classic | 25-01054999 | PML |

---

## 16. Diagnostic pointers

> QPTM lives in SQL Server (`dbo`) for cloud and Oracle (`QRMTIPS` / `ESUITE_Q<CLIENT>`) for on-prem; client schemas drift. Verify column/table names against the client before scripting; always verify-SELECT before any DML, in a transaction.

```sql
-- A. ALALLOCATE deadlock / sequence contention (§4A) — find the failing step + error by PQID
SELECT * FROM QARCH_PROCESS_MSG_LOG  WHERE PROCESS_QUEUE_ID = :pqid ORDER BY SEQ_NO;
SELECT * FROM QARCH_QFCBATCH_SQL_TRACE WHERE PROCESS_QUEUE_ID = :pqid ORDER BY SEQ_NO;
-- deadlock retry config:
SELECT * FROM QARCH_CTRL_ERR_RETRY;                       -- bump retries/wait for transient deadlocks
-- split-sizing configs (reduce concurrent splits): THRESHOLD_FOR_LARGE_LOC_ID_GAS_DAY,
--   MAX_LARGE_LOC_ID_GAS_DAY_RECS_IN_ONE_SUBSPLIT, MAX_SPLITS_FOR_LARGE_LOC_ID_GAS_DAY (Global Config)

-- B. Reallocation/PPA trigger setup (§8) — is the screen+table+column flagged to trigger?
SELECT * FROM BLXREF_REALLOC_PPA WHERE TBL_NM = 'ALCTRL_MEAS_VOL';   -- code table 27310
-- realloc-ind should be checked, PPA-ind unchecked for measurement-driven reallocation

-- C. Index HDR/DTL mismatch from a time-slice (§4F)
SELECT * FROM RTCTRL_INDEX_HDR WHERE TSP_NO=:tsp AND INDEX_ID=:idx ORDER BY EFF_DT_FROM;
SELECT * FROM RTCTRL_INDEX_DTL WHERE TSP_NO=:tsp AND INDEX_ID=:idx ORDER BY INDEX_START_DT;  -- DTL should clamp to HDR range

-- D. Duplicate daily-alloc rows from web PDA (§5) — the spurious PRT rows
SELECT * FROM ALCTRL_ALLOC WHERE ALLOC_GAS_DAY=:gd AND LOC_ID=:loc AND TRANS_TYPE_ID=:tt;  -- ALLOC_METH_CD='PRT' = the dupes

-- E. PPA orphan after unapprove/rerun (§9)
SELECT * FROM QTRAN_TRNX_ID WHERE RUN_ID=:run AND PROCESS_IND=1 AND REC_STATUS_CD IN ('CO','R','OR');
-- compare against QCTRL_PPA_MTR_HDR (RERUN_IND=1); orphans = TRNX rows whose PPA was unapproved but not deleted

-- F. Imbalance doubling — report view returning duplicate volume rows (§10)
-- QRPTS_INVOICE_DTL_VW returns WHIV_HV duplicated across RATE rows; the BL01 subreport sums it.
SELECT MTR_NO, TRAN_CD, WHIV_HV, RATE FROM QRPTS_INVOICE_DTL_VW WHERE ... ;  -- look for same WHIV_HV, different RATE

-- G. Reallocation-of-OBA invoice doubling — charge-basis config (§10, #1813295)
SELECT TSP_NO,TOS_CD,CHARGE_BASIS_CD,SHOW_QTY_INVOICE_IND
FROM   BLXREF_TOS_CHARGE_BASIS WHERE TOS_CD='ITS' AND CHARGE_BASIS_CD IN ('REC','RECF');  -- want SHOW_QTY_INVOICE_IND=0

-- H. Imbalance seq precision overflow (§11, #1723573)
SELECT COLUMN_NAME,DATA_PRECISION FROM ALL_TAB_COLUMNS
WHERE  TABLE_NAME='QTRAN_IMBAL_ACCT_ACTIVITY_DTL' AND COLUMN_NAME='ACCT_ACTIVITY_DTL_ID';  -- should be 19, not 10

-- I. IN53 OBA letter missing meter (§13, #1768545) — NULL receipt qty
SELECT * FROM NNCTRL_NOM_DTL WHERE REC_LOC_ID=:loc AND REC_QTY IS NULL;

-- J. PTR overlay (§14) — staging + the doubling source
SELECT * FROM QTIP_TRAN_PLANT_PTR WHERE PLANT_NO=:plant AND PROD_DT=:pd;     -- ESUITE_Q<CLIENT> on-prem
SELECT BA_NO, COUNT(*) FROM SCTRL_BA_USAGE GROUP BY BA_NO HAVING COUNT(*)>1; -- doubling = 2 rows (#1600026)
```

**Code locations (from comments / PR links):**
- ALALLOCATE engine: `QPipelineAllocationEngine::Allocate()`, `SetSRDependencyArray/Order`, `AddPDANodes` (#1383448); `QPSAlloc.cpp` / `ALNEWPREPR.CreateIntermediateTiers` (#1603193); `QAllocFuelPct.cpp` (rate NR, #1620789).
- PDA web: `QPTMAllocationServiceExt_PDA.cs` (`CalcSchedQty`, `GetPDAHeaders`, `CommonGetPDAHeaderCode`), `QUIControllerPDASubmission.cs`; classic `QVpPreDeterminedAllocationSubmission.cpp`.
- Reallocation/PPA event detector: `QPPAEventDetector.cs`, `QEventDetectorContainerBase.cs`, `HandleGenericScreenChangeEvent`/`HandleContractMaintenanceChange` (#228510, #1773033); classic `QSysFuncAreaUtility` vs web `QSysFuncAreaUtilityEventDetector` (#1547652).
- PTR overlay (client repos): `<CLIENT>.TIPS.ClassicBatch /QPDllTipsPTMIntegration*/QSQL_GenerateSharedPTR.cpp` (#1600026/#1567953); view `qptm_rpt_22_ptr_by_k_vw` (#1409048).
- Repos: `Quorum.QPTM.Web` / `.Web.Controllers`, `Quorum.QPTM.Application.QPEC`, `Quorum.QPTM.ClassicBatch`/`ClassicGUI`, `Quorum.QPTM.Validation.PDA` (RuleAL000…); client overrides `<CLIENT>.QPTM.*` (ENT, ETC, CNP, HPE, EPCO, ONM…). **Check the client repo/schema first** — many fixes are client-specific.

---

## 17. Escalation Guidance

**Is the client's build fixed?** IntegrationBuild is empty in ADO — you **cannot** read fixed-in-build from the work item. Confirm by: (1) the linked PR's **target branch** (e.g. `release/2024.04`, `develop`); (2) `Planning:YY.NN` / "queued for next TIPS YYYY.NN" / "cherry-picked into 20xx.xx" in tags/comments; (3) the client's consumed master version vs the beta where the change landed (e.g. #1664615 went into `Quorum.QPTM.Web 17.31 beta.117` → a client on beta.107 does **not** have it). Then verify in `Quorum.QPTM.ReleaseNotes`.

**Route to Engineering (real code defect) when:**
- A batch step crashes from code, not data/infra: SR-dependency null-ref (#1383448), web event-detail loss (#228510), table-missing-from-handler (#1773033), index time-slice over-clone (#1796121).
- A calc/validation is provably wrong on correct inputs: PDA sched-qty summing (#1664615), agent/meter-split gap over-validation (#1659856/#1676753/#1641972), swing-PDA datetime (#1639510), PPA delete-scoping (#1639010/#1647498), report-view doubling (#1733867), seq precision (#1723573), external-report view (#1661117).
- Provide: **TSP + accounting/prod month + gas day + failing step + exact ORA/COM/SQL error + PQID + a CORE-reproducible walkthrough**. If it only reproduces in the client env, expect it to sit (many here closed Rejected/blocked for lack of a CORE repro or a data cut).

**Handle as Configuration / Cloud Ops (no code) when:**
- Reallocation/PPA pop-up: table **27310 / `BLXREF_REALLOC_PPA`** flags + closed-month + allocations-already-run (#1761005, #1780199 is expected behavior).
- Invoice/imbalance doubling from **`BLXREF_TOS_CHARGE_BASIS.SHOW_QTY_INVOICE_IND`** (#1813295) or gas-analysis/imbalance-type (#1625672).
- OBA: level-101 PDA per service-requestor + del loc on OBA contract + non-NULL `REC_QTY` (#1621428, #1768545).
- ALALLOCATE registered-SQL = bad `PACTRL_TSP_CNFG_CTRL` data (#1706632); one-sided rate (#1620789).
- ALALLOCATE deadlock = client indexes + retry config + split sizing (#228999, #1320322) — Core roadmap for the real fix.

**Infra / QPEC restart first (no code):** ALALLOCATE "database connection lost" / `NOTICE_QUEUE_ID` / transient failures that succeed on rerun → **graceful QPEC restart** + Cloud Ops (#150654, #210845, #234047). DLL-not-found → **DevOps re-provision** to the client repo (#1704047).

**Known dead ends (don't over-invest):** auto-reversing PPA after Azure migration (#1685500/#1725310 — never reproduced; cache reset is the workaround), intermittent OBA inventory off-by-a-few (#1703871), random PTR meter drops (#1409048 deferred), PPA cashouts random (#1644043), erroneous PPAs with no alloc change (#1659737/#1641247) — these closed as not-reproducible/data and need a live open-month data cut to progress.

---

## Overlap / classification caveats
- **The Maintenance area branch (`…\Midstream and Transportation`) is mixed QPTM + TIPS.** The title functional terms here (PDA/ALALLOCATE/PPA/imbalance/OBA/PTR) are overwhelmingly **QPTM**, but a handful of matched rows are clearly **TIPS** (Settlement/gathering invoice/Paystation/Fixed-Fuels imbalance, e.g. #1554226, #1614317, #1660008, #116271, #157492, #1531467) — those were **dropped** (~16) and belong in `SKILL_TIPS_Allocations_PPA_Imbalance.md`. A few are genuinely cross-product (PTR overlay #1567953/#1600026 is a **TIPS-side interface** feeding QPTM; imbalance doubling report #1733867 is a TIPS core report consumed in the imbalance flow) — kept here because the case symptom presents in QPTM.
- **Substring noise:** the `PDA`, `PTR`, `OBA` title terms over-matched (PDA∈"update", PTR∈"captured/scripture", OBA∈"global/probably") — ~296 of the 918 were false positives filtered out by word-boundary matching before analysis.
- **State/reason mix of the 596 QPTM rows:** 595 Closed / 1 Resolved; reasons — Rejected 174 (no code change: data/config/infra/not-reproduced), Verified 151 + Acceptance 141 + Ready-for-QA 108 (fixed), Duplicate 10, Deferred 3. So **roughly 40% closed Rejected** — for this area, "closed bug" frequently means *config/data/infra/expected*, not a shipped code fix. Always read the thread.
- **No IntegrationBuild anywhere** → every build number in this skill is inferred (see header). Confirm in release notes / PR target branch before committing to a customer.

*Skill created 2026-06-14 from 918 WIQL-matched ADO Bugs (≈596 genuine QPTM allocation-area), 61 deep-read. ADO Bugs cited: #1796121 #1773033 #1639010 #1647498 #1659856 #1676753 #1641972 #1664615 #1639510 #1603193 #1742027 #1691916 #228510 #197579 #1547652 #1733867 #1723573 #1661117 #1813295/#1813294 #1761005 #1780199 #1706632 #1620789 #228999 #1320322 #1383448 #1567953 #1600026 #1409048 #1681065 #1593783 #1599265 #1596532 #1768545 #1621428 #1703871 #1685500/#1725310 #1644043 #1659737 #1641247 #1760037 #150654 #210845 #234047 #1704047 #218029 #1734843 #1386772 #1568117 #1410439 #1379613 #1746983 #1698974 #1625672 #1761437 #1768194.*
