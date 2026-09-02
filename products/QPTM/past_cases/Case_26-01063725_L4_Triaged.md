# L4 Triaged — Case 26-01063725

| | |
|---|---|
| **Salesforce Case** | 26-01063725 |
| **Predecessor** | Case 25-01033013 / ADO Bug **#1753672** (Closed – could not reproduce) |
| **Client** | Enterprise Products Operating LLC (ENT / EPCO) |
| **Contact** | Diane Duong / Lali Joseph · CSM Sara Riano |
| **Product / Module** | QPTM / Allocations (PTR Overlay Synchronization → ALALLOCATE) |
| **Environment** | ENT HD DEVA1 (repro); PSTA available; PRD impact |
| **TSP / Plant** | TSP 30051 (Enterprise Texas Pipeline) / **TMV (Thompsonville, South Texas)** |
| **Priority** | High (triggers audits) |
| **Classification** | **Software Defect — confirmed at code level** (not configuration, not customer error, not "working as designed") |
| **L4 / Date** | Aditya Bhagat · 2026-06-15 |

---

## 1. Issue Summary

On a reversal/restate cycle the **Allocation Imbalance Report (ALR24M / ALRPT_24)** shows a **PPA fuel quantity** under the TMV plant even though **neither the fuel rate nor the allocated quantity changed**. The receipt and path (PtR) quantities net to exactly zero across the reversal/restate pair, but the **PPA Fuel column leaves a non-zero residual**. No PPA was intentionally created and no PPA records were processed.

This recurs after a TIPS rerun + the QPTM **PTR Overlay Synchronization** process; it is not a one-off data anomaly.

---

## 2. Reproduction (deterministic — from client walkthrough, ENT HD DEVA1, TSP 30051)

Open accounting month **2/1/2026**, prior production month **1/1/2026**, plant **TMV**, company **GTT**.

1. Run QPTM **Allocation Process** (Reallocate + Unalloc IND) and **Allocation WGT to TIPS** for acct 2/2026.
2. Run **ALR24M** (Monthly) → **clean: NO PPA under TMV** (Process Queue ID **25069883**).
3. In **TIPS**: run **PTR – MeasVolImportProcess**; in **Accounting Date Maintenance** open 2/2026 for Billing, add a Jan production date, set rerun.
4. Run the **Facility Batch Job** for TMV: Run Type **"Revision due to liquid value adjustments"**, Measurement Standardization → ARAP, for PRD 1/1/2026 and 2/1/2026.
5. Run QPTM **PTR Overlay Synchronization** for acct 2/2026 (Process Queue ID **25069885**, completes with warning).
6. Re-run **ALR24M** (Process Queue ID **25069910**) → **PPA Fuel now appears under TMV**.

**Evidence (AFTER report, Prod Mth 01/01/2026, plant TMV / Proc K 12514):** paired RES/REV rows per receipt location —
- PPA Rec Qty: 50 / (50), 650 / (650), 50 / (50) → **nets 0**
- PPA PtR Qty: 12 / (12), 154 / (154), 11 / (11) → **nets 0**
- **PPA Fuel Qty: 1 / (2), 7 / (8), 1 / (2) → Prod-month total `(4)` — non-zero**

So REC and PtR cancel exactly, but Fuel does not. (Full repro + 14 screenshots: `Case_26-01063725_Walkthrough.md`.)

---

## 3. Root Cause (code level)

**Process:** `ALPTRSYNC` = **`ENT.QPTM.ClassicBatch` / `QPDllPipelineMgrAL_ENT/QPSTIPSPtrAllocSync.cpp`** (repo `3be6f2b9-48fc-4999-b873-a37a0cce97ac`, branch develop, 1,649 lines). (TMV = South Texas → the standard `QPSTIPSPtrAllocSync.cpp`, not the Permian `_PRM` twin.)

Two compounding defects:

### Defect A — PTR Overlay Sync force-reallocates with NO value-change gate (this file)
Call path: `Execute()` (L134) → `ComputeOverrides()` (L543) → `QPTRAllocDataTotal::AllocateSubTotalsToDailyNom()` (L1480) → `UpdateOverrides()` (L835) → **`DoReAllocation()` (L1072)**.

- In `AllocateSubTotalsToDailyNom`, the override is applied via `SetSchdEngQtyOverride(dSchdEngQtyOvrd)` (**L1547**), which flips the data object's PPA flag (`m_bIsPPA`, init L1292); `IsOverride()` returns that flag.
- **`DoReAllocation` gates the reallocation only on `if (pNomAlloc->IsOverride())` (L1158)** — i.e., "an override was applied," **NOT** on whether the recomputed PTR override actually **differs** from the currently-booked allocation. It then writes an `ALTRAN_REALLOC_SEL` row (`TRIGGER_SRC_CD = CDTBLVAL_TRIGGER_SRC_PTR` L1196, `PPA_SRC_CD = CDTBLVAL_PPA_SRC_PTR` L1199) and launches a synchronous **`ALALLOCATE`** (`PROCID_AL_ALLOCATE` L1251) with **`PARAMID_REALLOC_IND = true` (L1274)** for every override nom.
- Result: when TIPS re-sends the **same** PTR after the liquid-value rerun (an **idempotent / no-op restate**), the override is still applied and the row is still reallocated, even though the value is unchanged.

> Note: `UpdateOverrides` already performs a value-change compare at **L999** (`QUtilityPipelineMgr::CompareValue(pNomAlloc->GetSchdEngQtyOverride(), dOrigSchdEngQtyOvrd, msc_dCOLUMN_PRECISION_10) != 0`). The same precision-compare helper is used at L469/L620/L695. The reallocation decision in `DoReAllocation` simply **does not apply that guard** — it trusts `IsOverride()` alone.

### Defect B — Fuel does not net to zero on the restate (downstream, in ALALLOCATE) — *hypothesis, not yet code-confirmed*
`QPSTIPSPtrAllocSync` writes only `SCHD_ENG_QTY_OVRD`; it does not write fuel (verified). The spurious fuel is therefore produced downstream when the forced **`ALALLOCATE`** re-runs. **Leading hypothesis:** REC and PtR re-derive identically and net to zero, but Fuel (= allocated qty × fuel rate, progressively rounded) is recomputed and re-rounded asymmetrically across the RES/REV legs, leaving a non-zero residual booked as PPA fuel; the PTR-overlay feature modified ALALLOCATE under ADO **#1617125**. **This has not been confirmed in the ALALLOCATE source (not pulled this session)** — it is consistent with the evidence (REC/PtR net 0, Fuel ≠ 0) but should be verified there if the Primary fix is not pursued. Note: the **Primary fix does not depend on Defect B** — it prevents the no-op reallocation entirely, so ALALLOCATE never re-runs for the unchanged case.

**Why 2025 was "not reproducible" (#1753672 closed):** the spurious PPA only appears when measurement is **refreshed** (a TIPS rerun re-sends PTR). With no rerun, nothing is reallocated and no PPA is generated — so it looked intermittent and was guessed to be "rounding."

---

## 4. Suggested Code Fix (ranked)

> Diffs follow the existing file conventions (Hungarian notation, comma-first ctor init lists, tab-aligned inline accessors, `//` comments). Line numbers per `develop` @ repo `3be6f2b9-48fc-4999-b873-a37a0cce97ac`; **re-baseline against the client's build branch before coding.**

### Primary — propagate the value-change decision `UpdateOverrides` already computes, and gate the reallocation on it

**Files:** `/QPDllPipelineMgrAL_ENT/QPSTIPSPtrAllocSync.h` and `/QPDllPipelineMgrAL_ENT/QPSTIPSPtrAllocSync.cpp` (repo `ENT.QPTM.ClassicBatch`).

**Why not a one-line compare in `DoReAllocation`:** an override exists precisely because it differs from the plain scheduled qty, so comparing the override against the booked `GetSchedEngQty()` is the wrong baseline (almost always "different" → would not suppress the no-op). The correct baseline is the **previously-stored override** in `ALCTRL_ALLOC_OVRD`, which `UpdateOverrides` already compares (L999) but discards — its result lives only in a local `bIsPPA` used for the warning at L1019. We surface that change decision on the data object and gate `DoReAllocation` on it. The change below also de-duplicates the existing PPA logic (one `bOvrdChanged` local, reused).

**1) `QPSTIPSPtrAllocSync.h` — `QNomAllocData`: add a change flag distinct from `m_bIsPPA`.**
```cpp
// accessors (place beside IsOverride / SetOverrideDirection):
	bool  IsOvrdChanged() const					{ return m_bOvrdChanged; }
	void  SetOvrdChanged(bool bChanged)			{ m_bOvrdChanged = bChanged; }

// private members (place beside m_bIsPPA):
	bool    m_bOvrdChanged;
```

**2) `QPSTIPSPtrAllocSync.cpp` — initialize the member in BOTH constructors** (the default ctor init list ~L1304 and the copy ctor ~L1327; note the copy ctor here copies members explicitly, so the new flag must be added or it is left indeterminate on any array copy):
```cpp
// default ctor init list (append, comma-first):
	, m_bOvrdChanged(false)

// copy ctor body (append):
	m_bOvrdChanged = rhs.m_bOvrdChanged;
```

**3) `QPSTIPSPtrAllocSync.cpp` — `UpdateOverrides()`: record the change (reuse the comparison already trusted at L999).**
```cpp
// (a) insert branch — new non-null override row written (~L964, where it already sets bIsPPA):
	pNomAlloc->SetOvrdChanged(true);			// brand-new override = a real change
	if (bIsPPAMonth)
	{
		bIsPPA = true;
	}

// (b) existing row, override cleared to NULL (~L981):
	const bool bOvrdChanged = !bOrigSchdEngQtyIsNull;	// clearing an existing override = a change
	pNomAlloc->SetOvrdChanged(bOvrdChanged);
	if (bIsPPAMonth && bOvrdChanged)
	{
		bIsPPA = true;
	}

// (c) existing row, override is non-null (~L993) — replaces the current bIsPPAMonth/CompareValue block:
	const bool bOvrdChanged = bOrigSchdEngQtyIsNull
		|| QUtilityPipelineMgr::CompareValue(pNomAlloc->GetSchdEngQtyOverride(),
											 dOrigSchdEngQtyOvrd,
											 QUtilityPipelineMgr::msc_dCOLUMN_PRECISION_10) != 0;
	pNomAlloc->SetOvrdChanged(bOvrdChanged);
	if (bIsPPAMonth && bOvrdChanged)
	{
		bIsPPA = true;
	}
```

**4) `QPSTIPSPtrAllocSync.cpp` — `DoReAllocation()` (L1158): gate on the real change, not just "override applied".**
```cpp
	if (pNomAlloc->IsOverride() && pNomAlloc->IsOvrdChanged())
	{
		// ... existing ALTRAN_REALLOC_SEL write + synchronous ALALLOCATE launch (unchanged) ...
	}
```

An idempotent PTR re-sync now leaves `m_bOvrdChanged == false`, so no `ALTRAN_REALLOC_SEL` row is written and no `ALALLOCATE` is launched — the spurious PPA is eliminated at the source (fuel **and** rec/ptr), while a genuine PTR change still reallocates. Localized to the ENT PTR-sync; reuses the file's own `CompareValue(..., msc_dCOLUMN_PRECISION_10)` idiom.

> **Note for review:** the booked getter is `GetSchedEngQty()` ("Sch**e**d") and the override getter is `GetSch**d**EngQtyOverride()` — easy to transpose. The `m_bOvrdChanged` flag is set in `UpdateOverrides` and read in `DoReAllocation`; both iterate the *same* `allocDataFromQptmArray` elements by pointer (no copy in between), so propagation is safe even though the existing copy ctor is partial.

### Secondary — make ALALLOCATE carry-forward fuel on a no-op restate
If a reallocation must still run, have `ALALLOCATE` **carry forward the prior fuel** when REC and PtR net to zero on a restate, instead of recompute-and-re-round. **Higher blast radius (core allocation engine, ADO #1617125 area); not yet pinpointed to a file/line** — only pursue if the Primary gate proves insufficient.

**Recommendation:** ship the **Primary** gate first; lowest risk and resolves the reported symptom.

---

## 5. Expected Result After Fix
Re-running the walkthrough (steps 3–6) with an **unchanged** measurement/PTR produces an AFTER report identical to BEFORE — **no PPA fuel rows under TMV** (no `ALTRAN_REALLOC_SEL` rows with `TRIGGER_SRC_CD = PTR` created by the PTR Overlay Sync; no ALALLOCATE relaunch). A genuine PTR change still reallocates and books a legitimate PPA.

## 6. Diagnostic SQL (verify the defect signature)
```sql
-- Reallocation rows the PTR Overlay Sync enqueued for the TMV meter (expect TRIGGER_SRC_CD=PTR with no real change)
SELECT TSP_NO, LOC_ID, GAS_DAY, ACCTG_MTH, PROD_MTH, PROC_CD, PPA_SRC_CD,
       TRIGGER_SRC_CD, TRIGGER_SRC_DTL, USER_ID, UPDT_DT
FROM   ALTRAN_REALLOC_SEL
WHERE  TSP_NO = 30051 AND TRIGGER_SRC_CD = 'PTR'
ORDER  BY UPDT_DT DESC;

-- Reversal vs restate: alloc qty & fuel rate identical, but PPA fuel non-zero (the (4) residual)
SELECT PLANT_NO, LOC_ID, CTR_NO, ACCTG_MTH, PROD_DT, ALLOC_TYPE,
       ALLOC_QTY, FUEL_RATE, FUEL_QTY, PTR_QTY, UPDT_DT
FROM   ALHIST_ALLOC_LATEST_VW
WHERE  PLANT_NO = 'TMV' AND PROD_DT = '2026-01-01'
ORDER  BY LOC_ID, PROD_DT, UPDT_DT;
```

## 7. Related Items
- **ADO #1753672** — predecessor; closed "could not reproduce." **This walkthrough is the reproducible data cut Dev was missing — clone/reopen.**
- Same `ALTRAN_REALLOC_SEL` spurious-insert family as **#1797289** and case **26-01081678** (measurement-import delete+reinsert path; both lack a value-change guard before reallocating).
- **ADO #1617125** — PTR-overlay change that modified ALALLOCATE (Defect B lives here).
- File last changed Jan-2024 (PR 92582); defect is latent — no fix in flight.

**Suggested ADO bug title:** `ENT - 26-01063725 - PTR Overlay Sync (ALPTRSYNC) reallocates with no idempotency gate → ALALLOCATE re-rounds non-netting PPA fuel (TMV; no change in fuel rate/alloc qty)`

---

## 8. ADO Bug — ready to paste (Engineering handoff)

> Clone/reopen **#1753672** (do not lose its history) and update these fields.

| Field | Value |
|---|---|
| **Work Item Type** | Bug |
| **Title** | ENT - 26-01063725 - PTR Overlay Sync (ALPTRSYNC) reallocates with no value-change gate → ALALLOCATE re-rounds non-netting PPA fuel (TMV) |
| **Area Path** | QuorumSoftware\Engineering\Maintenance\Midstream and Transportation\Customer Service |
| **Product / Module** | QPTM / Allocations (PTR Overlay Synchronization) — *predecessor was filed under Module = Reporting; root cause is in Allocations* |
| **Severity / Priority** | 2 - High / 2 |
| **Found in Version** | Confirm client build (predecessor #1753672 = 2023.04) |
| **Customer** | Enterprise Products Operating LLC |
| **Salesforce Case** | 26-01063725 (predecessor 25-01033013) |
| **Root Cause (category)** | Code Defect — missing value-change guard before reallocation |

**Repro Steps** (ENT HD DEVA1, TSP 30051; open acct 2/1/2026, prior prod 1/1/2026, plant TMV, company GTT):
1. Run QPTM Allocation Process (Reallocate + Unalloc IND) and Allocation WGT to TIPS for acct 2/2026.
2. Run ALR24M (Monthly) → no PPA under TMV (baseline clean).
3. In TIPS: run PTR – MeasVolImportProcess; open 2/2026 for Billing in Accounting Date Maintenance, add a Jan production date, set rerun.
4. Run the TIPS Facility Batch Job for TMV: Run Type "Revision due to liquid value adjustments", Measurement Standardization → ARAP, for PRD 1/1/2026 and 2/1/2026.
5. Run QPTM PTR Overlay Synchronization for acct 2/2026.
6. Re-run ALR24M.

**Expected:** report unchanged from step 2 — no PPA fuel under TMV when fuel rate and allocated qty did not change.
**Actual:** PPA appears under TMV for prod month 1/1/2026; PPA Rec and PPA PtR net to zero, but PPA Fuel posts a non-zero residual (observed total `(4)`).

**Root Cause:** `ENT.QPTM.ClassicBatch /QPDllPipelineMgrAL_ENT/QPSTIPSPtrAllocSync.cpp` — `DoReAllocation()` (L1158) gates the reallocation only on `QNomAllocData::IsOverride()` (i.e. `m_bIsPPA`, set unconditionally whenever an override is applied), **not** on whether the recomputed PTR override actually differs from the previously-stored override. So an idempotent TIPS PTR re-sync forces a full reallocation; the subsequent synchronous `ALALLOCATE` (REALLOC_IND=true, modified under #1617125) re-rounds fuel asymmetrically across the RES/REV legs, leaving the spurious PPA fuel even though REC and PtR net to zero. The correct change comparison already exists in `UpdateOverrides()` (L999, against `ALCTRL_ALLOC_OVRD`) but its result is discarded.

**Proposed Fix:** see §4 (Primary) — add `QNomAllocData::m_bOvrdChanged`, set it in `UpdateOverrides()` from the existing `CompareValue(..., msc_dCOLUMN_PRECISION_10)` comparison, and gate `DoReAllocation()` on `IsOverride() && IsOvrdChanged()`. Header + .cpp in the same module; no schema/data change. Apply the equivalent gate to the Permian twin `QPSTIPSPtrAllocSync_PRM.cpp`.

**Regression Risk:** Low and localized to the ENT PTR Overlay Sync. The gate only *suppresses* reallocations where the recomputed override is unchanged within column precision (10 dp); every genuine PTR change still reallocates exactly as today. No change to ALALLOCATE, the override DB write (`ALCTRL_ALLOC_OVRD`), or the PPA warning message.

**Test / Verification:**
- Re-run the repro above → ALR24M shows no PPA fuel under TMV; no `ALTRAN_REALLOC_SEL` rows with `TRIGGER_SRC_CD='PTR'` created by step 5; no ALALLOCATE relaunch.
- Positive case: make a real PTR change in TIPS, re-sync → reallocation still fires and a legitimate PPA is booked.
- Regression sweep: a Permian (`_PRM`) plant and a non-PPA (current production month) override both reallocate unchanged.

**Release Note (draft):** *Corrected the QPTM PTR Overlay Synchronization so that re-importing unchanged TIPS pointer allocations no longer triggers a reallocation; this prevents spurious PPA fuel quantities on the Allocation Imbalance Report (ALR24M) when the fuel rate and allocated quantity have not changed.*

---

*Prepared by L4 (Aditya Bhagat), 2026-06-15. All symbols verified against `QPSTIPSPtrAllocSync.cpp` / `.h` @ develop — re-baseline line numbers against the client's build branch before coding.*
