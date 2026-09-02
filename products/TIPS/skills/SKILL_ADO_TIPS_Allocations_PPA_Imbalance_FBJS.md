# SKILL (ADO): TIPS — Allocations / PPA / Imbalance / Facility Batch (FBJS)

**Version:** 1.0 | **Created:** 2026-06-14 | **Source:** ADO TIPS bugs (Closed/Resolved) | **Product:** TIPS (My Quorum TIPS — midstream gas/crude allocation, imbalance & batch processing)
**Use When:** an ADO/SF case is about the TIPS **allocation → imbalance** pipeline: ALLOCATE / CBALLOCATE / PANIGHTLY / Facility-Batch-Job-Submittal (FBJS) failures, an `ORA-00001` / PK / sequence error on a Settle/Imbalance step, a wrong/missing allocated volume, a PPA generated/not-generated/not-purged, an imbalance calc/report number that's off, an Allocation Group / Meter Split / Volume Assembly setup problem, or a gas-statement / plant-performance allocated value. For the *settled value / journal / revenue* side (GEN PTR, CAR/WAH, Journal Entry Control, rate-schedule/UDEF math) use **SKILL_TIPS_Settlement_Revenue_Journal.md**; for batch-queue mechanics use **SKILL_TIPS_Batch_Processing.md**.

> **Evidence base:** ADO WIQL over `Engineering\Midstream` + `Engineering\Maintenance\Midstream and Transportation`, WorkItemType=Bug, State in (Closed,Resolved), title CONTAINS {allocation group, PPA, imbalance, facility batch, FBJS, CBJS, plant, volume assembly, preferential loading, ALLOCATE}. **815 matched**; after dropping the QPTM/Energy-Transportation pipeline-team bugs (see Overlap note) ~**700 are TIPS**, ~194 are real customer-case defects (SF# in title). **~54 deep-read** (description + ReproSteps + full comment thread + linked PRs). Every root-cause claim below cites a real ADO bug # and the SF case in its title.
>
> **Overlap / classification caveat (READ FIRST):** the Maintenance branch is **mixed QPTM + TIPS**, and the search terms `PPA`, `imbalance`, `plant`, `ALLOCATE` are *ambiguous across products*. In **QPTM** (pipeline transaction mgmt), "PPA" = **Prior Period Adjustment** (billing/BLTRAN_PPA_EVENT, rate/contract triggers), "imbalance" = pipeline transportation imbalance / **Imbalance Trading**, and allocation = **ALALLOCATE**. Bugs owned by teams **Pirates of Pipeline / Pipeline Titans / Pipeline Galaxy / Infinite Refresh** are QPTM and were **dropped** (e.g. #1745668, #205930, #206764, #1387337 — rate-deletion/timeslice/location-end-date "PPA" via `QPPAEventHandler.cs` / `BLXREF_REALLOC_PPA` / `PATRAN_LOC_GRP` — these are QPTM billing, NOT TIPS). In **TIPS**, "PPA" = **Prior Period Adjustment of allocation** (`QCTRL_PPA_MTR_*`, `QTRAN_TRNX_ID`, Measured Volumes → Measure/Allocate/Settle), "imbalance" = the gathering **IMBALANCE** batch job (`QTRAN_IMBAL_ACCT_*`, Customer Account Maintenance). Confirm the area-team and the table prefix before treating a bug as TIPS.

---

## 1. Quick Triage Table

| Symptom (user/case report) | Likely cluster | First check |
|---|---|---|
| ALLOCATE / PANIGHTLY / CBALLOCATE "stopped processing on error" or times out at exactly ~1 hour, intermittent, **succeeds on rerun** | **A** (env/connection/perf) | Was it a DB-connection drop / QPEC crash / query-timeout? Restart QPECs, rebuild indexes; usually NOT code (§4) |
| `ORA-00001 unique constraint (..PK_QARCH_TRAN_SEQ)` / `Ins_QARCH_TRAN_SEQ`, or `PK_QTRAN_CTR_TRNX_ID`, on a Settle/Imbalance step; "happens randomly, rerun works" | **B** (sequence collision) | §5 — Oracle retry/timing defect re-inserting an existing seq id; fixed #1746230. Check seq next-val vs MAX |
| `number precision too large` at INACCTACCM; sequence value hit 11 digits | **B** (column precision) | §5 — `ACCT_ACTIVITY_DTL_ID` precision 10→19 (#1723573) |
| Duplicate-key insert into `ALSTAG_ALLOC` / `QTRAN_IMBAL_ACCT_BAL` / paystation on ALLOCATE/IMBALANCE | **B** (dup data / eff-date overlap) | §5 — bad measurement timestamp or eff-date overlap in `QRMTIPS.SEXTN_*`; delete-script + reimport (#1445769, #1697870, #1805171) |
| PPA records **not purged / orphaned** in `QTRAN_TRNX_ID` after unapprove or rerun-same-month; partially-approved-PPA report won't clear | **C** (PPA TRNX_ID defect) | §6 — missing Prod_Dt filter / rerun-month delete (#1639010, #1647498) |
| "Too many / extra PPAs logged" (e.g. editing Measured Volumes in Web) | **C / Expected** | §6 — Web logs 1 PPA per PK-change (add+delete); ruled NOT a defect (#1681065) |
| Imbalance/CICO cashout in **wrong tier**; a UDEF division returns 0 | **D** (imbalance calc) | §7 — `QSettleUdefFormula.cpp` rounded before checking >0 (#1585836) |
| IMBALANCE job fails at **CTRFEE**; escalation index unusually high | **D** (data limit) | §7 — inflation >999% overflows `QTRAN_RATE_RES_DETAIL.ADJ_PCT` (#1534316) |
| Imbalance/Company-Imbalance **performance** (INACCTACCM) regressed after a patch | **D/A** (perf collateral) | §7 — INACCTACCM change reverted; new perf change behind config (#1599265) |
| Allocated volume **missing/0 for one owner** on a meter split; or volume not tying to measured | **E** (alloc-group/split) | §8 — split-decimal rounding (CAN cast fix #1712833); collateral from a reverted patch (#1458246/#1458209) |
| `RESALLOCGP` "Resolve Allocation group mtrs" SQL error (missing `QCTRL_MTR_SPLIT_DTL` join) | **E** | §8 — From-Pt-Join-Formula w/ MTR_SFX but To-Pt formula without it (#1616106) |
| New client on V17: a disposition/fuel (e.g. TFUL) generates **no allocation records** | **E** (client DLL migration) | §8 — CAN alloc/volume-assembly rule not registered in the client V17 Allocate DLL (#1653225) |
| Gas statement / plant-perf **allocated gallons doubled / wrong / 0 for TIK / condensate = theoretical** | **F** (report view/Crystal) | §9 — Crystal/view formula (TIK not summed, hard-coded facility, posted-view not patched) (#1434950, #1454364, #1665714) |
| POSTPLANT fails on **duplicate TRNX_ID** in settle-stmt tables, only for rerun months | **F** (post/TRNX_ID) | §9 — client SUM-meter enhancement set TRNX_ID = numeric PROD_DT (#1640044) |
| Thousands of ALLOCATE **warning** messages (e.g. "no mapping in code table 24825") | **Config** | §8 — point the code-table XRef to the client metadata layer (#1763768) |

---

## 2. Pipeline & where these bugs live

```
[Measurement / Measured Volumes (QCTRL_MEAS_VOL, ALCTRL_MEAS_VOL)]
      │  (PPA logged here → QCTRL_PPA_MTR_PENDING/HDR, QTRAN_TRNX_ID)
      ▼  FACILITY BATCH JOB SUBMITTAL (FBJS) / Company Batch / PANIGHTLY  → runs the steps:
   MEASUREMENT → ALLOCATE (steps: DAYVOLS, RESALLOCGP, ALSEL_N, ALSPLITNEW, CTRMTR, STDPDA, CFTOOUTVOL, CAWDATA, FixedFuels…)
                          → IMBALANCE (steps: TRANSCONTR, INACCTACCM, CUSTACCTBAL, CTRFEE…)
                          → SETTLE → POSTRESULTS / POSTPLANT
      │
      ▼  results land in: QTRAN_ALLOC_VOL / QRPTS_ALLOC_VOL_* (allocation),
                          QTRAN_IMBAL_ACCT_ACTIVITY_DTL / QTRAN_IMBAL_ACCT_BAL (imbalance),
                          QTIP_*_RPTS_SETTLE_STMT (statements), QTRAN_PLANT_STATUS (post)
```

### Vocabulary (TIPS allocation side)
- **FBJS** = Facility Batch Job Submittal (Web + Classic). The screen that runs Measure→Allocate→Imbalance→Settle→Post for a plant/facility. **PANIGHTLY / CBALLOCATE / ALALLOCATE / ALLOCATEQG / ALLOCATEWH** are scheduled batch wrappers; **CBJS/CBALLOCATE** = crude-batch variants. (Note: `ALALLOCATE` is *also* a QPTM process name — see Overlap caveat.)
- **PPA (TIPS)** = Prior Period Adjustment of a closed-month allocation. Logged from Measured Volumes / Meter Split / Rate changes into `QCTRL_PPA_MTR_PENDING`→`QCTRL_PPA_MTR_HDR`; transactional rows tracked by `QTRAN_TRNX_ID` (with `REC_STATUS_CD` CO/R, `RERUN_IND`, `PROCESS_IND`). PPA limit ~**2000 meter-level per plant/month** (contract-level PPAs explode into thousands of meter-level — see Settlement skill §13 / #874381).
- **PDA** = Prior Day/Period Adjustment allocation **setup** on the PDA submission screen (Alloc **Rank** RNK vs Pro-Rata PRT, ATT codes like UPSR/UPSRK, Svc-K). Wrong/missing PDA → defaults to PRT (#1540717/#1554485).
- **Allocation Group** = the meter/contract grouping that drives allocation; tabs: Profile, From/To Point Attribute, Meter Exception, Preferential Loading, Detail. **Volume Assembly / Alloc Rule** = client-registered C++ rules in the Allocate DLL (`QAllocateRuleFactoryCommon.cpp`).
- **Imbalance (TIPS)** = the gathering **IMBALANCE** batch job; balances into `QTRAN_IMBAL_ACCT_ACTIVITY_DTL` / `QTRAN_IMBAL_ACCT_BAL`, surfaced on **Customer Account Maintenance / Balance**. CICO = Cash-In/Cash-Out fee.
- **TRNX_ID / sequences** = `QARCH_TRAN_SEQ` (Oracle `QRMTIPS_QFC.PK_QARCH_TRAN_SEQ`), `QTRAN_CTR_TRNX_ID_SQ`, `QTRAN_IMBAL_ACCT_ACTIVITY_D_SQ`, `QTRAN_SEQ` — recurring collision/overflow source.
- **QRMTIPS / SEXTN / SCTRL** = client extension schema; eff-date overlaps there break ALLOCATE/IMBALANCE inserts.

---

## 3. Decision Tree

```
TIPS allocation/imbalance/FBJS case
│
├─ Is it QPTM? (Imbalance Trading screen, ALALLOCATE on a TSP, BLTRAN_PPA_EVENT, rate/contract/location PPA, Pipeline-* area team)
│      → STOP. Use the QPTM skill. (Overlap caveat.)
│
├─ A batch STEP crashed/timed-out? → get PQID + STEP NAME + exact ORA/COM error
│   ├─ Intermittent, "rerun works", DB-connection-lost / timeout at ~1h / QPEC crash   → §4 (env/perf — restart QPECs, rebuild indexes; NOT code)
│   ├─ ORA-00001 PK_QARCH_TRAN_SEQ / Ins_QARCH_TRAN_SEQ / PK_QTRAN_CTR_TRNX_ID         → §5 (sequence retry/timing defect; #1746230/#1639351/#164770)
│   ├─ "number precision too large" (sequence hit 11 digits)                           → §5 (column precision 10→19; #1723573)
│   ├─ Cannot insert duplicate key (ALSTAG_ALLOC / QTRAN_IMBAL_ACCT_BAL / paystation)  → §5 (dup measurement / eff-date overlap → delete-script; #1445769/#1697870/#1805171)
│   ├─ ACCESS_VIOLATION / E_FAIL on alloc-group SQL (NULL key cols)                     → §5 (missing COALESCE null-check commit; #1404853/#1413006)
│   ├─ RESALLOCGP SQL error (missing QCTRL_MTR_SPLIT_DTL join)                          → §8 (From-Pt-Join-Formula w/ MTR_SFX; #1616106)
│   └─ Fixed-Fuels / FBJS step slow/timeout (not crashing on data)                      → §9/§4 (perf; m_Ins_Fixed_Fuels_Rev; #1693863/#1687619)
│
├─ PPA wrong (process not crashing)?
│   ├─ Orphan/un-purged PPA in QTRAN_TRNX_ID after unapprove or rerun-same-month        → §6 (code defect; #1639010/#1647498)
│   ├─ "Too many PPAs" editing Measured Volumes in Web                                  → §6 (Expected — 1 PPA per PK change; #1681065)
│   └─ Allocation number itself off after PDA edit (RNK shows as PRT, off by 1)         → §8 (PDA/Alloc-Group SETUP, not code; #1540717/#1554485)
│
├─ Imbalance number/report wrong?
│   ├─ CICO/cashout in wrong tier; UDEF division = 0                                    → §7 (QSettleUdefFormula rounding; #1585836)
│   ├─ IMBALANCE fails at CTRFEE; escalation index huge                                 → §7 (ADJ_PCT overflow >999%; #1534316 — data)
│   ├─ Company Imbalance perf regressed after patch (INACCTACCM)                         → §7 (collateral; reverted; #1599265)
│   └─ Meter/volume missing from imbalance; net-0 PPA showing on statement              → §7 (gas-analysis/imbalance-type config #1625672; report suppress #1622136)
│
├─ Allocated volume missing/0 / not tying / random results?
│   ├─ One owner 0 on a meter split (rounding)                                          → §8 (CAN cast fix; #1712833)
│   ├─ Random PVR/Suppl-Fuel/volume between identical reruns                            → §8 (collateral from a bad patch — back out; #1458209/#1458246)
│   ├─ A disposition/fuel (TFUL) generates no records on a new V17 client               → §8 (client Allocate-DLL rule not registered; #1653225)
│   └─ Thousands of "no mapping in code table N" warnings                               → §8 (code-table XRef → client metadata layer; #1763768)
│
├─ Statement / plant-perf allocated value wrong?                                        → §9 (Crystal/view: TIK not summed, posted-view unpatched, condensate=theoretical; #1434950/#1454364/#1665714)
├─ POSTPLANT dup TRNX_ID on rerun months                                                → §9 (client SUM-meter TRNX_ID=PROD_DT enhancement; #1640044)
│
└─ "How do I…", audit, slow-but-works, number follows setup                             → §11 Expected/Config FAQ
```

---

## 4. Cluster A — ALLOCATE / PANIGHTLY / CBALLOCATE process failures: environment, connection & performance (NOT code)

**The single most common ALLOCATE-failure signature, and almost never a code bug.** ALLOCATE/PANIGHTLY/ALESVOLIMP fail intermittently, **succeed on rerun**, with DB-connection-lost / query-timeout / ACCESS_VIOLATION messages.

| Bug / SF | Symptom | Root cause | Fix / Workaround |
|---|---|---|---|
| **#210845** (20-00084643, CRW, *Rejected*) | ALALLOCATE fails intermittently during PANIGHTLY on `ALSEL_N`/`ALSPLITNEW`; reruns succeed | **Dropped DB connection between QPEC and DB server** during the run window (other QCloud clients on the same servers saw it same nights). Not data, not code. | Infra/QCloud investigation; run schedule in **debug mode** to capture more; no code change |
| **#234047** (20-00092335, CNP, *Rejected*) | ALESVOLIMP + PANIGHTLY "A database connection was lost during the transaction"; PANIGHTLY times out at **exactly 1 hour** | PANIGHTLY 1h = QPEC.ini **query-timeout**; ALESVOLIMP = transient DB connectivity / open txn locking `ALCTRL_MEAS_VOL` | Have client DBAs check open transactions; rerun; not a Quorum code issue |
| **#1440051** (22-00251394, XCL, *Rejected*) | ALLOCATE jobs failing with memory/dropped-connection errors, then "Failed to load rate data from existing archive" | **QPEC got into a bad state / bad cached value** | **Bounce (restart) the QPECs** — resolved, no recurrence |
| **#1462196 / #1534888** (22-00262381 / 22-00272887, HVM) | ALLOCATE slow / timing out on **CTRMTR** (paystation insert) and **TPSCHEDPRC**, first week of month | Insert into `qtran_paystation` taking >60min → query timeout; index fragmentation; **two scheduled ALLOCATE runs overlapped** (CTRMTR slow let a 2nd run launch) | **Rebuild indexes** (auto when fragmentation>30%), add **CAW index** (PR 72056/72060), restart services, temporarily raise QPEC.ini timeout 3600→5400. Resolved without code change |
| **#1612548** (23-00911097, QTR, *Rejected*) | CBALLOCATE 15h (was 15min) after env move; slow in `QPC_LOAD_CB_INVENTORY_RPT` | **Customer-written custom procedure** | Client fixed it themselves |
| **#1637022** (23-00934142, PML) / **#1652854** (24-00948103, ACP) | FBJS jobs stall for hours then resume; "stuck on step N" | **QPEC instances crash and fail to restart**, leaving fewer QPECs than queued jobs need → timeout until restart | QCloud QPEC monitoring/auto-restart; **enhance purge logic to keep logs/SQL-trace for error-status processes** (RCA blocked because logs were purged) |

**Fix recipe (A):** get PQID + step + exact error. If the error is **connection-lost / timeout / ACCESS_VIOLATION / "bad cached value"** and **reruns succeed** → treat as **environment/perf**: restart (bounce) QPECs, check index fragmentation on `qtran_paystation`/`CTRMTR`-related tables, confirm no two jobs overlap, and check QCloud for QPEC crashes. Escalate to **QCloud/DBA, not Engineering**, unless it reproduces deterministically on the same data. **Always grab the SQL trace + batch message log in debug mode before logs are purged** (purge wipes them, killing RCA — #1652854).

---

## 5. Cluster B — Sequence collisions & dup-key inserts on Settle/Imbalance steps

`ORA-00001` on a sequence PK (`PK_QARCH_TRAN_SEQ`, `PK_QTRAN_CTR_TRNX_ID`) or a numeric-precision overflow, or a duplicate-key insert. Two distinct sub-families: **code/Oracle timing defects** vs **bad data / eff-date overlaps**.

| Bug / SF | Symptom | Root cause | Fix (+ inferred build) |
|---|---|---|---|
| **#1746230** (24-00945427, ENT) / **#1639351** (23-00930659, ENT) | `Ins_QARCH_TRAN_SEQ` → `ORA-00001 (QRMTIPS_QFC.PK_QARCH_TRAN_SEQ)` on **SETSPLIT** during SJ1 monthly run; "random, rerun works" | **`Ins_QARCH_TRAN_SEQ` re-inserts a sequence id that already exists** — retry logic exists but the error wasn't handled, and the query is **Oracle-DB-compatibility-sensitive** (timing). Prior fix #119535 was never actually in the code. | Query corrected to not re-insert an existing seq id. **PRs into 2024.04, develop, release, 2024.10, 2025.04** (PR 117019/117524/117525). Earliest fixed ≈ **2024.04** *(inferred from PR branches — confirm in release notes)*. Watch: ENT hit a residual SETSPLIT timing scenario after the first fix. |
| **#1723573** (25-01014345, ETP) | **INACCTACCM** fails `PL/SQL numeric or value error: number precision too large`; `QTRAN_IMBAL_ACCT_ACTIVITY_D_SQ` reached 11 digits | Column `ACCT_ACTIVITY_DTL_ID` precision was **10**; sequence outgrew it | **Increase precision 10→19** + regenerate `ImbalAcctActivityDtlDO`. **DB+code PRs into 2020.03, 2024.04, develop, 2024.10** (PR 110407/110411/110413…). *(inferred from PR branches)* |
| **#164770** (DCP, *Rejected*) | IMBALANCE fails on **TRANSCONTR**, `PK_QTRAN_CTR_TRNX_ID` violated; **`QTRAN_CTR_TRNX_ID_SQ` next-val < MAX(CTR_TRNX_ID)** | Sequence fell behind the table's max id | Resync the sequence above MAX (operational); historical DCP issue-resolution batch |
| **#1445769** (22-00253639, CRW) | `Cannot insert duplicate key … ALSTAG_ALLOC … AK_ALSTAG_ALLOC1` running allocations | Client's custom measurement import wrote **bad rows with a 09:00 Gas-Day timestamp instead of 00:00** | **Delete-script** for the bad rows, then reimport with midnight timestamp (data fix; script attached to WI) |
| **#1697870** (24-00989380, DCP, *Rejected*) | "duplicated when inserting into pay station … effective date overlap" in ALLOCATE-ASAP | **Eff-date overlap** in `QRMTIPS.SEXTN_CTR_HEADER_QRMTIPS` (front-end `EFF_DT_TO` 9/30 stored as 10/31) | Correct the eff-date in the extension table (data) |
| **#1805171** (26-01097671, HEC) | IMBALANCE fails on **CUSTACCTBAL**, `PK_QTRAN_IMBAL_ACCT_BAL` duplicate; dup rows on Customer Account Maintenance for a single OBA contract | **Duplicate Customer-Account-Balance rows** (recurs — cf. 26-01065143) | Remove the duplicate `QTRAN_IMBAL_ACCT_BAL` rows (data); pattern recurring across patches |
| **#1404853** (21-00210986, EQT) / **#1413006** (21-00213217, EPCO) | Daily ALLOCATE fails `C0000005 ACCESS_VIOLATION` / "CAN'T GET RECORD COUNT … E_FAIL" on `SEL_QALLOC_GRP_PROFILE` | **LEFT JOIN returning NULL key columns** that an Oracle Oct patch began rejecting; client release **missing the Jan-2020 null-check commit** | EQT: data-script for bad rec-purge/TRNX_ID rows **+** ensure the null-check commit (`QAllocationGrpHdrLoaderComponent.cpp`, commit `bdadd0d…`) is present. EPCO: add **`COALESCE(col, NULL)`** to `SEL_QALLOC_GRP_PROFILE` & `Sel_QAlloc_Grp_Header` — **PRs 67263 (develop), 67264 (release), 67265 (2021.10)** *(inferred)* |

**Fix recipe (B):** read the exact constraint name.
- `PK_QARCH_TRAN_SEQ` / `Ins_QARCH_TRAN_SEQ` / `PK_QTRAN_CTR_TRNX_ID` and **"rerun works"** → sequence retry/timing defect (**#1746230**) or sequence-behind-MAX (**#164770**). Confirm the 2024.04+ fix is deployed; short-term, resync the sequence above MAX.
- `numeric/value error precision too large` → column-precision fix (**#1723573**, 10→19).
- `Cannot insert duplicate key (ALSTAG_ALLOC / QTRAN_IMBAL_ACCT_BAL / paystation)` → **data**: bad measurement timestamp (#1445769), eff-date overlap in `SEXTN_*` (#1697870), or dup Customer-Account-Balance rows (#1805171). Verify-SELECT then delete the offenders in a transaction.
- `ACCESS_VIOLATION` / `E_FAIL` on an alloc-group SELECT → **missing COALESCE null-check** (#1413006) and/or bad rec-purge data on an old build (#1404853).

---

## 6. Cluster C — PPA logging / TRNX_ID purge defects (TIPS, not QPTM)

Real TIPS code defects in how PPA transactional rows are created/deleted in `QTRAN_TRNX_ID` / `QCTRL_PPA_MTR_*`.

| Bug / SF | Symptom | Root cause | Fix (+ inferred build) |
|---|---|---|---|
| **#1639010** (23-00935744, ONM) | After unapproving **one** prod month (others still approved), orphan rows remain in `QTRAN_TRNX_ID`; show on Partially-Approved-PPA report; can block POST | SQL **`m_DEL_MTR_TRNX_PPA` was missing the Prod_Dt filter** when deleting → only partial delete | Add the Prod_Dt filter. **Merged 2020.03, 2022.10, develop (2024.04+)** (PR 92729/92762/92781). *(inferred)* Workaround offered: lift the POST validation from error→warning to get through POST (leaves orphans). |
| **#1647498** (24-00942120, ONM) | Rerun of the **same prod month** as an existing PPA flips PPAs to reruns but **does not delete the PPA-generated CO/R rows** in `QTRAN_TRNX_ID`/`QTRAN_PAYSTATION` | Rerun didn't purge the PPA rows (different RUN_ID; query looked for `REC_STATUS_CD='CO'` but rerun rows are `'OR'`) | Added a delete for the CO/R rows by prod-dt on rerun. **PRs 94931 (2020.03), 97863, develop**. *(inferred)* Op-note: **the *current* month run is what purges PPA rows tied to its RUN_ID — run BOTH the rerun month and the current month.** |
| **#1681065** (24-00972314, ONM) | Editing 2 columns on **Measured Volumes in Web** logs 2 PPAs (Classic logs 1) | When a **PK column** (Meter/ProdDate/UnitTime/VolClsf) changes, it's a delete+add = legitimately **2 PPA rows** in `QCTRL_PPA_MTR_PENDING`. Web and Classic log the same; only the *message* differs. | **Closed as NOT a defect** (Expected). Web matches Classic functionally. |

**Fix recipe (C):** for "PPA won't clear / orphan in `QTRAN_TRNX_ID` / partially-approved report stuck":
1. Confirm whether the trigger was an **unapprove-one-of-many-months** (#1639010 — missing Prod_Dt filter) or a **rerun of the same month as the PPA** (#1647498 — rerun didn't purge CO/R rows). Both are fixed ≈ **2020.03 / 2022.10 / 2024.04** — confirm the client build has it.
2. Diagnostic: rows where `QTRAN_TRNX_ID.PROCESS_IND=1 AND REC_STATUS_CD IN ('CO','OR')` that also have a matching `QCTRL_PPA_MTR_HDR` with `RERUN_IND=1` are the offenders (John Weems' query in §10).
3. For "too many PPAs in Web" → confirm it's a **PK-column change** (= expected, #1681065) before logging a defect.

---

## 7. Cluster D — Imbalance calculation, data-limit & performance

| Bug / SF | Symptom | Root cause | Fix (+ inferred build) |
|---|---|---|---|
| **#1585836** (22-00866782, MER) | Pipeline statement **CICO cashout lands in the wrong tier** (Tier 2 vs 3); a UDEF division `CICO_QTY/NET_DEL_QTY` returned **0** | **`QSettleUdefFormula.cpp` rounded the number without first checking it was > 0** (If/Else UDEF with no rounding) | Code fix in `QSettleUdefFormula.cpp` (same rounding family as #1624085 and the Settlement-skill If/Then/Else rounding defect). **Merged 2022.10 and up** (PR 90417/90439/90440/92229). *(inferred)* Batch behind it: `QPSCtrLevelFees.cpp` / `CTRFEE` step. |
| **#1534316** (22-00272399, HVM) | Nightly **IMBALANCE fails on CTRFEE**; CICO/escalation index very high | An escalation **index/inflation value > 999%** overflows `QTRAN_RATE_RES_DETAIL.ADJ_PCT` (field can't hold >999%). The CTRFEE warnings were a red herring. | **Data** — correct the bad index value. (Field-size limit is the real constraint; not patched.) |
| **#1599265** (23-00901236, ONM) | **Company Imbalance / INACCTACCM** went from 5min to very slow after **Patch 15** (security patch) | The INACCTACCM change shipped for ET's perf was **collateral damage** to ONM (different Oracle optimizer plan) | **Backed the INACCTACCM change out of core**; reworked ET perf change **behind a config** (#1596532/#1599423). Lesson: imbalance perf regressions after a patch are often optimizer-plan collateral. |
| **#1622136** (23-00916681, MOM) | **Net-0 PPAs from reruns still show** on Invoice Detail & Imbalance statement | Report was not suppressing net-0 PPA lines | Suppress net-0 lines on **Invoice Detail – Imbalance charges only** (leave Imbalance Statement section). **2022.10 and up.** *(inferred)* |
| **#1625672** (23-00924115, MOM, *Rejected*) | New delivery meter's allocated volume not in imbalance (`QTRAN_INV_ACCT_ACT_DTL_VW_2` shows 0 gross qty) | **Gas-analysis / imbalance-type config**: imbalance type set to pull **contractual-adjusted** qty instead of **standard** qty | Config fix (imbalance type / gas analysis) — not code |
| **#1693863** (24-00985139, MOM) / **#1687619** (ONM, core) | FBJS times out on the **Fixed-Fuels step on Allocate** ("Query timeout expired"), intermittent | Slow `m_Ins_Fixed_Fuels_Rev` query | **Perf fix to `m_Ins_Fixed_Fuels_Rev`** (PR 102567, cherry-pick of core #1687619). **2024.10.** *(tag "2024.10; Performance" on #1687619)* |

**Fix recipe (D):** reproduce with the client's exact contract/prod-month.
- Wrong CICO **tier** / a UDEF result of 0 → the `QSettleUdefFormula.cpp` round-before->0-check defect (**#1585836**); confirm 2022.10+ build.
- IMBALANCE crash on **CTRFEE** → check the escalation **index value** for an inflation >999% (`ADJ_PCT` overflow, **#1534316**) — data.
- Imbalance **perf** regressed right after a patch → suspect optimizer-plan collateral (**#1599265**); compare execution plans, escalate as collateral.
- Volume **missing** from imbalance → check **imbalance-type / gas-analysis** config first (**#1625672**), not code.

---

## 8. Cluster E — Allocation Group / Meter Split / Volume Assembly / PDA

Mostly **setup / data / client-DLL** issues; a couple of genuine calc defects.

| Bug / SF | Symptom | Root cause | Fix |
|---|---|---|---|
| **#1540717** (22-00274719, GEN) / **#1554485** (22-00290129, GEN) | Monthly Allocation report shows **Oper-Method = PRT even though PDA set to RNK**; allocations off "by 1" | The report rows are **nomination-timing** allocations; with **no PDA matching that ATT**, they default to **Pro-Rata (PRT)**. Stale **Svc-K** value on the PDA broke the PDA-Hash match. A confirmation flip 0→1 caused the off-by-1. | **PDA/Allocation-Group SETUP fix** (not code): delete & re-enter PDAs under the correct **ATT (UPSR vs UPSRK)**, hide Svc-K column, uncheck Realloc, rerun Measure→Allocate. **Config/Training.** |
| **#1712833** (25-01002874, PEM) | One owner's allocated volume = **0** when meter split is `0.9421875 / 0.0578125` | Split-decimal **rounding**: 2nd iteration rounded `0.057812…` up to `0.057813…`, pushing the sum >1 so the residual owner got 0 | **Add casting in the subquery to display the value without rounding** (CAN only, ORA+MSSQL). PR 109849/110017/111073. **≈2025.04 (CAN).** *(inferred)* |
| **#1458209** (22-00253900, MKW) / **#1458246** (22-00260537, MKW) | ALLOCATE gives **random PVR/Suppl-Fuel/volume** between identical reruns; totals under-allocate | **Collateral damage from a bad 2019.05 package** (the same changes that had to be backed out for MER) | **Back out the reverted MER changes** / hotfix the corrected version to MKW. (No new code — re-applying the revert.) |
| **#1616106** (23-00921876, ETP/EMP) | **RESALLOCGP** ("Resolve Allocation group mtrs") errors — generated SQL references **`MTR_SFX`/`QCTRL_MTR_SPLIT_DTL`** but never joins that table | A **To-Point** allocation uses a formula **without** `MTR_SFX`, while the **From-Pt Join Formula** uses one **with** `MTR_SFX` → the split-detail table isn't joined | Code fix in `Quorum.TIPS.ClassicBatch` (Allocate). **PRs 92886/92894 (2022.03/2023.04), develop, release.** *(inferred)* |
| **#1653225** (24-00948315, ALT) | New V17 client: **TFUL disposition generates no allocation records** (Volume Assembly / Alloc Rule "not working") | The **CAN allocation/volume-assembly rule (SPTMTH) was never registered in the client's V17 Allocate DLL** during the V16(TFS)→V17(ADO) migration (cf. tax-rule #1623379) | **Register the CAN rule in the client `QAllocateRuleFactoryCommon.cpp`** (e.g. `QALT…QPDllTipsAllocate`). Client-specific DLL rebuild. PR 95114. |
| **#1763768** (25-01045547, AHS) | Thousands of ALLOCATE warnings: "no mapping … in code table 24825" though data exists | **Profile Module Code-Table XRef** for code table **24825 (`QCODE_PLANT_PERF_ELEM_COL_MAP`)** pointed to core, not the client-managed metadata layer | **Config**: point CT 24825 to the client (Client-Managed) metadata layer, clear cache, restart QPECs. |

**Fix recipe (E):**
- **Wrong alloc method (PRT vs RNK) / off-by-small** → it's **PDA/Alloc-Group setup**, not code (#1540717/#1554485): verify a PDA exists matching the row's **ATT**, clear stale Svc-K, uncheck Realloc, rerun Measure→Allocate.
- **One owner 0 on a split** → split-decimal **rounding** (#1712833 — CAN cast fix).
- **Random results between reruns** → almost always **collateral from a bad patch** (#1458209/#1458246) — identify the package and back out the offending change.
- **RESALLOCGP SQL error** → From-Pt-Join-Formula vs To-Pt-formula `MTR_SFX` mismatch (#1616106).
- **New V17 client missing a disposition/fuel** → **client Allocate-DLL rule not registered** (#1653225).
- **"no mapping in code table N" warnings** → code-table XRef metadata-layer config (#1763768).

---

## 9. Cluster F — Allocated values on statements / plant-performance / POST

Report-view / Crystal-formula bugs and post-time TRNX_ID collisions. The *allocation* is usually right; the **report or the posted view** is wrong.

| Bug / SF | Symptom | Root cause | Fix |
|---|---|---|---|
| **#1434950** (22-00824910/22-00219951, SCX) | Fixed-Recovery Gas Statement: allocated gallons wrong for **posted** months and **0 for TIK** contracts | (a) a prior fix to **`QRPTS_SETTLE_GAS_STMT_PROD_VW`** (non-posted) was **never applied to `QPOST_SETTLE_GAS_STMT_PROD_VW`** (posted); (b) the Crystal formula **doesn't sum TIK volume** like it does shrink | Fix the posted view + Crystal (sum TIK). **Merged 2021.10, 2022.04 and up** (PR 68599/69167-69171). *(inferred)* |
| **#1454364** (22-00255786, WTG) | POP Statement **allocated gallons doubled** for one meter | Crystal formula **hard-coded facility 420** and added `TOT_LIQ_VOL + TOT_LIQ_TIK_VOL`; client moved to facility 410 | Crystal change to use only `TOT_LIQ_VOL`, remove facility hard-code (client-specific report; delivered via services patch) |
| **#1665714** (CHD) | Core Gas Statement: **condensate theoretical = allocated** (same value) | Crystal report formula wrong for allocated condensate (DB view `QRPTS_SETTLE_GAS_STMT_PLNT_VW` returned correct values) | Crystal report fix. **2023.04.** *(iter "Reviewed - May 2024"; PR 97082-97132)* |
| **#1599752** (23-00901545, UTG, *Rejected*) | GPM not calculating on **Plant Performance – Liquids (74B)** | Tied to UTG moving to **Daily** allocation — reports not supported for that without a project | **Won't fix** — needs a holistic project (Expected/scope). |
| **#1640044** (23-00936172/24-00951618, SRB) / **#1643221** (24-00939186, SRB) | **POSTPLANT fails on duplicate TRNX_ID** in `QTIP_POST_RPTS_SETTLE_STMT` for all rerun months ≥ 9/2023; plant-perf report blank | Client enhancement **#1579772** created a **SUM- meter via stored proc that sets `TRNX_ID` = numeric value of `PROD_DT`** → always identical per prod month → collides with posted rows | Generate a **unique per-run TRNX_ID** for the SUM- meter that won't collide with system-generated ids. PR 96813. Short-term: unpost + purge-partial-posted script (attached). **≈2023.04+.** *(inferred)* |
| **#1806658** (26-01099529, HEC) | **POSTPLANT dependency error** "JOURNAL must run first" for a client that doesn't run JOURNAL | The **POSTPLANT→JOURNAL dependency check** shouldn't apply to clients not using JOURNAL | **Remove the dependency check** in client metadata (`HEC.TIPS.Metadata`, PR 128791). Client-specific config/metadata. |
| **#1799931** (26-01094138, IPF) | After 2025.04 Web upgrade, can't end-date/edit a **plant-specific UDEF that links a GLOBAL schedule** | Data-conversion left a plant-specific UDEF pointing at a Global schedule → Web save validation blocks it | **Data-conversion fix**: make the rate schedules + UDEFs Global and start open-ended timeslices at a common date (script attached). Affects multiple clients on upgrade. |

**Fix recipe (F):** if the **allocation query** ties out but the **statement/report** is wrong, it's the **Crystal formula or the report view** — check whether the **posted** view got the same fix as the non-posted one (#1434950), whether a facility is **hard-coded** (#1454364), and whether **TIK** volume is summed. For **POSTPLANT dup-TRNX_ID**, look for a client SUM-meter enhancement setting TRNX_ID from PROD_DT (#1640044).

---

## 10. Diagnostic SQL & pointers

> **Caveat:** TIPS lives in per-client Oracle/MSSQL schemas (`QRMTIPS`, `ESUITE_Q<CLIENT>`, client `_QFC`). Names below come from the cited WIs — **verify against the client schema**, run a verify-SELECT, wrap DELETE/UPDATE in a transaction.

```sql
-- A. Sequence behind the table MAX (TRANSCONTR / QARCH_TRAN_SEQ family, §5)
SELECT MAX(CTR_TRNX_ID) AS max_id FROM QTRAN_CTR_TRNX_ID;          -- compare to:
SELECT LAST_NUMBER FROM ALL_SEQUENCES WHERE SEQUENCE_NAME = 'QTRAN_CTR_TRNX_ID_SQ';
-- If next < max → reset the sequence above MAX (operational unblock; #164770).

-- B. Imbalance activity sequence precision (the 10->19 fix, §5 / #1723573)
SELECT COLUMN_NAME, DATA_PRECISION, DATA_LENGTH FROM ALL_TAB_COLUMNS
WHERE TABLE_NAME = 'QTRAN_IMBAL_ACCT_ACTIVITY_DTL' AND COLUMN_NAME = 'ACCT_ACTIVITY_DTL_ID';

-- C. Orphan / un-purged PPA rows in TRNX_ID (§6, #1639010/#1647498) — John Weems' query
SELECT * FROM QRMTIPS.QTRAN_TRNX_ID t
WHERE t.RUN_ID = '<RUN_ID>' AND t.PROCESS_IND = 1 AND t.REC_STATUS_CD IN ('CO','OR')
AND EXISTS (SELECT 1 FROM QRMTIPS.QCTRL_PPA_MTR_HDR ppa
            WHERE t.PLANT_NO=ppa.PLANT_NO AND t.MTR_NO=ppa.MTR_NO
              AND t.ACCT_DT=ppa.ACCT_DT AND t.PROD_DT=ppa.PROD_DT AND ppa.RERUN_IND = 1);

-- D. Duplicate Customer-Account-Balance rows blocking CUSTACCTBAL (§5, #1805171)
SELECT CTR_NO, CO_CD, ACCT_DT, PROD_DT, COUNT(*) FROM QTRAN_IMBAL_ACCT_BAL
WHERE PROD_DT = '<PROD_DT>' GROUP BY CTR_NO, CO_CD, ACCT_DT, PROD_DT HAVING COUNT(*) > 1;

-- E. Eff-date overlap in the client contract-header extension (§5, #1697870)
SELECT CTR_NO, EFF_DT_FROM, EFF_DT_TO FROM QRMTIPS.SEXTN_CTR_HEADER_QRMTIPS
WHERE CTR_NO = '<CTR_NO>' ORDER BY EFF_DT_FROM;

-- F. Escalation index overflow (>999%) breaking CTRFEE (§7, #1534316)
SELECT * FROM QTRAN_RATE_RES_DETAIL WHERE ADJ_PCT > 999 OR ADJ_PCT IS NULL;

-- G. Allocated vs measured tie-out for a meter/owner (§8 split issues)
SELECT MTR_NO, MTR_SFX, PROD_CD, DISP_CD, UNIT_TM_CD, ALLOC_QTY, NOM_ALLOC_CD, OPER_NOM_ALLOC_CD
FROM QTRAN_ALLOC_VOL WHERE MTR_NO = '<MTR>' AND PROD_DT = '<PROD_DT>' ORDER BY MTR_SFX, PROD_CD;
```

**Where the code lives:** ALLOCATE/IMBALANCE/SETTLE batch = **`Quorum.TIPS.ClassicBatch`** (`QPDllTipsAllocate` incl. `QAllocateRuleFactoryCommon.cpp`, `QAllocationGrpHdrLoaderComponent.cpp`; `QSettleUdefFormula.cpp`; `QPSCtrLevelFees.cpp`). Client overrides = **`<CLIENT>.TIPS.ClassicBatch / .Database / .Metadata`** (ALT/ENT/SCX/MKW/HEC…). Web PPA logging = `QTIPSIntegDataChangeEventTypePPAVOL.cs` (`ResolveAdjustments`/`CreatePPA`). Reports = **`Quorum.TIPS.Reports`** (Crystal) + DB views `QRPTS_*`/`QPOST_*_VW`. **Always check the client repo/schema first** — many fixes are client-specific.

---

## 11. Expected-Behavior / Config / Training FAQ

| Reported as | Reality | Bug |
|---|---|---|
| "ALLOCATE failed but reran fine" / connection-lost / timeout | Env/QCloud (QPEC crash, dropped DB connection, index fragmentation, overlapping runs) — **not code**; restart QPECs, rebuild indexes | #210845, #234047, #1440051, #1462196, #1637022 |
| "Web logs too many PPAs vs Classic" | Expected — a **PK-column change** on Measured Volumes is delete+add = 2 PPA rows in both Classic and Web | #1681065 |
| "Allocation method PRT instead of RNK / off by 1" | PDA / Allocation-Group **setup** — no PDA matches the nomination ATT (defaults to PRT); stale Svc-K | #1540717, #1554485 |
| "GPM/plant-perf not calculating after going Daily" | Reports not supported for Daily without a project | #1599752 |
| "Volume missing from imbalance" | Imbalance-type / **gas-analysis** config (contractual-adjusted vs standard qty) | #1625672 |
| "POSTPLANT says JOURNAL must run first" but we don't use JOURNAL | Remove the **dependency check** (client metadata config) | #1806658 |
| Thousands of "no mapping in code table N" warnings | Code-table XRef pointed at core, not the client metadata layer | #1763768 |
| CBALLOCATE suddenly 15h after env move | Customer's own custom procedure | #1612548 |

**Tell-tale it's env/config/training, not a code defect:** the job **succeeds on rerun**; the error is connection/timeout/ACCESS_VIOLATION; the number **follows the PDA/gas-analysis setup**; a sequence is simply behind its MAX; or it's a Crystal/report-view formula. **Verify the setup and rule out the environment before escalating to Engineering.**

---

## 12. FIX-VERSION MATRIX

> IntegrationBuild was **empty on every analyzed bug**; iteration paths were mostly generic. **Fixed-in-build below is INFERRED from the PR target branches named in the dev comments — confirm in `Quorum.TIPS.ReleaseNotes` / the client patch before quoting to a customer.** "Data/Config" = no product build; resolved operationally.

| ADO Bug | Symptom (short) | State / Reason | Fixed-in (inferred) | SF Case | Client |
|---|---|---|---|---|---|
| #1746230 | QARCH_TRAN_SEQ ORA-00001 on SETSPLIT | Closed / Acceptance | 2024.04, 2024.10, 2025.04, develop, release | 24-00945427 | ENT |
| #1639351 | Same SETSPLIT seq (earlier) | Closed / Acceptance | 2024.04 family | 23-00930659 | ENT |
| #1723573 | Imbalance seq precision 10→19 (INACCTACCM) | Closed / Acceptance | 2020.03, 2024.04, 2024.10, develop | 25-01014345 | ETP |
| #164770 | TRANSCONTR PK_QTRAN_CTR_TRNX_ID seq < MAX | Closed / Rejected | Data (resync seq) | (DCP issue-res) | DCP |
| #1445769 | ALSTAG_ALLOC dup key (bad 09:00 timestamp) | Closed | Data (delete+reimport) | 22-00253639 | CRW |
| #1697870 | Paystation dup / eff-date overlap | Closed / Rejected | Data (SEXTN eff-dt) | 24-00989380 | DCP |
| #1805171 | CUSTACCTBAL dup PK_QTRAN_IMBAL_ACCT_BAL | Closed / Verified | Data (dedupe) | 26-01097671 | HEC |
| #1404853 | Daily ALLOCATE ACCESS_VIOLATION (NULL keys) | Closed / Verified | Data + null-check commit (2019.09 client missing Jan-2020 fix) | 21-00210986 | EQT |
| #1413006 | E_FAIL on SEL_QALLOC_GRP_PROFILE (NULL keys) | Closed / Acceptance | develop, 2021.10, release (COALESCE) | 21-00213217 | EPCO |
| #1639010 | Orphan TRNX_ID after unapprove-one-month | Closed / Acceptance | 2020.03, 2022.10, develop(2024.04) | 23-00935744 | ONM |
| #1647498 | Rerun-same-month doesn't purge CO/R rows | Closed / Acceptance | 2020.03, 2022.10, 2024.04 | 24-00942120 | ONM |
| #1681065 | Web "extra PPA" on Measured Volumes | Closed | **Not a defect (Expected)** | 24-00972314 | ONM |
| #1585836 | CICO cashout wrong tier (UDEF round→0) | Closed / Acceptance | 2022.10 and up | 22-00866782 | MER |
| #1534316 | IMBALANCE CTRFEE; index >999% | Closed / Verified | Data (field-size limit) | 22-00272399 | HVM |
| #1599265 | Company Imbalance INACCTACCM perf collateral | Closed / Verified | Reverted in core; ET change behind config | 23-00901236 | ONM |
| #1622136 | Net-0 PPA on invoice/imbalance stmt | Closed / Acceptance | 2022.10 and up | 23-00916681 | MOM |
| #1625672 | New delivery meter missing from imbalance | Closed / Rejected | Config (gas analysis) | 23-00924115 | MOM |
| #1693863 / #1687619 | Fixed-Fuels FBJS step timeout | Closed / Verified | 2024.10 (`m_Ins_Fixed_Fuels_Rev`) | 24-00985139 | MOM/ONM |
| #1712833 | Meter-split one-owner 0 (rounding) | Closed / Acceptance | ≈2025.04 (CAN cast) | 25-01002874 | PEM |
| #1458209 / #1458246 | Random PVR/Suppl-Fuel / under-alloc | Closed / Verified | Back-out of bad 2019.05 pkg | 22-00253900 / 22-00260537 | MKW |
| #1616106 | RESALLOCGP SQL (MTR_SFX join missing) | Closed / Acceptance | 2022.03/2023.04, develop, release | 23-00921876 | ETP/EMP |
| #1653225 | TFUL disposition no alloc records (V17) | Closed / Acceptance | Client Allocate-DLL rule register | 24-00948315 | ALT |
| #1763768 | "no mapping code table 24825" warnings | Closed | Config (metadata XRef) | 25-01045547 | AHS |
| #1434950 | Fixed-Recovery stmt: posted view + TIK | Closed / Acceptance | 2021.10, 2022.04 and up | 22-00824910 | SCX |
| #1454364 | POP stmt allocated gallons doubled | Closed / Verified | Client Crystal (services patch) | 22-00255786 | WTG |
| #1665714 | Gas stmt condensate theoretical=allocated | Closed / Acceptance | 2023.04 (Crystal) | (CHD) | CHD |
| #1640044 / #1643221 | POSTPLANT dup TRNX_ID (SUM-meter=PROD_DT) | Closed | ≈2023.04+ (uniq TRNX_ID) | 23-00936172 | SRB |
| #1806658 | POSTPLANT JOURNAL dependency check | Closed / Verified | Client metadata (remove check) | 26-01099529 | HEC |
| #1799931 | Plant-specific UDEF w/ Global schedule | Closed / Verified | Data-conversion fix | 26-01094138 | IPF |

---

## 13. Escalation Guidance

**Route to Engineering (Software Defect) — provide PQID + step + exact ORA/COM error + client + plant + acct/prod month + repro:**
- Sequence re-insert / precision overflow: `Ins_QARCH_TRAN_SEQ` (#1746230), `ACCT_ACTIVITY_DTL_ID` precision (#1723573).
- PPA TRNX_ID purge defects: unapprove-one-month (#1639010), rerun-same-month (#1647498).
- Calc/SQL defects: CICO round-before-check (#1585836), RESALLOCGP MTR_SFX join (#1616106), meter-split rounding (#1712833), missing COALESCE null-check (#1413006).
- Report-view/Crystal: posted-view-not-patched + TIK (#1434950), condensate (#1665714), POSTPLANT SUM-meter TRNX_ID (#1640044).

**Route to QCloud / DBA (NOT Engineering):** intermittent ALLOCATE/PANIGHTLY failures that **rerun clean** — QPEC crash/restart, dropped DB connection, index fragmentation, overlapping scheduled runs, query-timeout (#210845, #234047, #1440051, #1462196, #1637022). **Capture SQL trace + batch message log in debug mode before purge.**

**Handle as Configuration / Data (Cloud Ops or Support):** PDA/Alloc-Group setup defaulting to PRT (#1540717/#1554485); code-table XRef metadata layer (#1763768); client Allocate-DLL rule registration on V17 migration (#1653225); POSTPLANT JOURNAL dependency removal (#1806658); eff-date overlaps / dup rows / bad measurement timestamps in `SEXTN_*`/`QTRAN_IMBAL_ACCT_BAL`/`ALSTAG_ALLOC` (#1697870/#1805171/#1445769); escalation index >999% (#1534316); upgrade data-conversion UDEF/schedule linkage (#1799931). Verify-SELECT in a transaction first.

**Handle as Training / Expected (no fix):** Web "extra PPA" (#1681065); allocations correctly following PDA/gas-analysis setup (#1625672); reports unsupported for Daily without a project (#1599752); customer custom procedure (#1612548). See §11.

**Is the client build fixed?** IntegrationBuild is blank in ADO — do **not** quote a build from this skill as gospel. Cross-check the inferred branch in **`Quorum.TIPS.ReleaseNotes`** and the client's patch/hotfix history. Many TIPS fixes are **client-specific** (escalation/precision/DLL-rule), so a core "fixed-in 2024.04" does **not** mean a given client environment has it until their patch lands.

---

*Skill created 2026-06-14 from ADO TIPS bugs (Closed/Resolved) under Engineering\Midstream + Engineering\Maintenance\Midstream and Transportation. 815 WIQL matches → ~700 TIPS after dropping QPTM/Energy-Transportation pipeline-team bugs → ~194 real customer-case defects → ~54 deep-read (description + ReproSteps + full comment threads + linked PRs). Fixed-in-build values are INFERRED from PR target branches/iteration and marked accordingly — confirm in release notes.*
*Companion: SKILL_TIPS_Settlement_Revenue_Journal.md, SKILL_TIPS_Allocations_PPA_Imbalance.md (SF-case version), SKILL_TIPS_Batch_Processing.md, REPO_REFERENCE.md.*
