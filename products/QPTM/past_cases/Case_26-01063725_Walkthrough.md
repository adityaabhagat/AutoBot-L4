# Walkthrough Document — PPA Fuel triggered when no PPA is intended to be created

| Field | Value |
|---|---|
| **Title** | PPA Fuel triggered when no PPA is intended to be created |
| **Salesforce Case #** | 26-01063725 |
| **ADO #** | *(blank in source doc)* |
| **Originating Client** | Enterprise Product Operating LLC |
| **TSP** | 30051 — Enterprise Texas Pipeline LLC |
| **Product** | QPTM & TIPS |
| **System tested in** | ENT HD DEVA1 |
| **Author** | Sara Riano / Santiago Berrones |

*(Extracted from `Case 26-01063725 Before Walkthrough ENTPPA (1).docx`. Screenshots in `Case_26-01063725_Walkthrough_images/`.)*

---

## Objectives

The walkthrough document is created by Quorum resources during issue resolution to provide an overview of the issue and document, from a functional perspective, the steps to test it. It lets Client and Quorum:

- Review and confirm requested changes before they are made.
- Confirm the changes were implemented as requested and function as expected.
- Understand the scope of the issue in order to thoroughly test.

## Issue Description

PPA fuel records are appearing in the **Allocation Imbalance Report** without any manual PPA creation or triggering activity. During testing the report initially did **not** contain PPA entries; however, after executing a series of TIPS processes and QPTM batch jobs, PPA fuel records began appearing under the **TMV plant**.

It is unclear which specific process, synchronization, or code path is causing the PPA records to populate. The behavior appears related to the interaction between TIPS processing and QPTM allocation/synchronization jobs, but additional investigation is needed to determine the exact source and root cause.

## Testing Preparation

**Configuration**
- TSP **30051**
- Work on an open month that is open in both QPTM and TIPS.

---

## Testing Steps

| # | Action |
|---|--------|
| 1 | Open QPTM. Navigate to the Code/Decode table screen, filter using ID **27217**. Verify the first open month — for this test the open month is **2/1/2026**. |
| 2 | Navigate to the Reallocation Status screen. Verify whether reallocations are pending for 2/1/2026. For this test there are two (Accounting and Prod month 2/1/2026) and none for 1/1/2026. |
| 3 | Navigate to the PPA Status screen, verify any PPA for PRD month **1/1/2026** (testing uses this month). Note there are **11 records** under this PRD month. |
| 4 | Batch Process Execution → run **Allocation Process** for open accounting month 2/1/2026, TSP 30051. Check **Reallocate IND** and **Unallocate IND**; do **not** allocate the entire month. Completing with errors/warnings is OK. |
| 5 | Batch Process Execution → run **Allocation WGT to TIPS** for open accounting month 2/1/2026, TSP 30051. Check **Reallocate IND** and **Unallocate IND**; do not allocate the entire month. Warnings OK. |
| 6 | Report Execution → run the **Allocation Imbalance Report** (Monthly) for accounting month 2/1/2026, TSP 30051. |
| 7 | Check the report — it does **not** have PPA under the TMV plant. (ref: `BEFORE-FEBACCTG-25069884_ALR_24M_1.pdf`) |
| 8 | Open TIPS → Batch Process Execution → **PTR – TIPS MeasVolImportProcess** under 'TIPS Process' type, accounting month 2/1/2026, TSP 30051. |
| 9 | Accounting Date Maintenance → verify open month for company **GTT**, facility **TMV**; ensure the Jan month is closed (close it if open). |
| 10 | Accounting Date Maintenance → open **2/1/2026** for Billing, add a production date for Jan, check **rerun**, click Update. |
| 11 | Facility Batch Job Submittal → Facility **Thompsonville plant TMV**, Accounting Date 2/1/2026, Time interval Monthly. PRD Date **1/1/2026**, Start Job **Measurement Standardization**, End Job **ARAP Batch Job**, Run Type **Revision due to liquid value adjustments**. Submit Job. **Repeat** with PRD Date 2/1/2026. |
| 12 | Open QPTM → Batch Process Execution → run the **PTR Overlay Synchronization** process, accounting month 2/1/2026, TSP 30051. |
| 13 | Report Execution → re-run the **Allocation Imbalance Report** (Monthly), accounting month 2/1/2026, TSP 30051. |
| 14 | Check the report — it **has** PPA under the TMV plant. (ref: `AFTER-FEBACCTG-25069910_ALR_24M_1.pdf`) The PPA Rec Qty and PPA PtR Qty are the same (net zero), **however the PPA Fuel Qty still generates a value**. |
| 15 | PPA Status screen → verify PPA for PRD month 1/1/2026. Still **11 records** (none newly processed). |

---

## BEFORE — step-by-step with screenshots

**Step 1 — Code/Decode (ID 27217): first open month = 2/1/2026**

![Step 1 — Code/Decode table](Case_26-01063725_Walkthrough_images/image1.png)

**Step 2 — Reallocation Status: two pending for 2/1/2026, none for 1/1/2026**

![Step 2 — Reallocation Status](Case_26-01063725_Walkthrough_images/image2.png)

**Step 3 — PPA Status: 11 records under PRD month 1/1/2026**

![Step 3 — PPA Status before](Case_26-01063725_Walkthrough_images/image3.png)

**Step 4 — Allocation Process (Reallocate IND ✓, Unallocate IND ✓, not entire month)**

![Step 4 — Allocation Process params](Case_26-01063725_Walkthrough_images/image4.png)

**Step 5 — Allocation WGT to TIPS (Reallocate IND ✓, Unallocate IND ✓)**

![Step 5 — Allocation WGT to TIPS params](Case_26-01063725_Walkthrough_images/image5.png)

**Step 6 — Allocation Imbalance Report execution (Monthly)**

![Step 6 — Report execution params](Case_26-01063725_Walkthrough_images/image6.png)

**Step 7 — BEFORE report: no PPA under TMV (all PPA columns = 0)**

![Step 7 — BEFORE report, no PPA](Case_26-01063725_Walkthrough_images/image7.png)

---

## TRIGGER — TIPS restate + QPTM PTR sync

**Step 8 — TIPS PTR – MeasVolImportProcess**

![Step 8 — TIPS MeasVolImport](Case_26-01063725_Walkthrough_images/image8.png)

**Step 9 — Accounting Date Maintenance: GTT / TMV, Jan closed**

![Step 9 — Accounting Date Maintenance](Case_26-01063725_Walkthrough_images/image9.png)

**Step 10 — Accounting Date Maintenance: open 2/1/2026 for Billing, add Jan prod date, rerun**

![Step 10 — Accounting Date Maintenance, open billing](Case_26-01063725_Walkthrough_images/image10.png)

**Step 11 — Facility Batch Job Submittal: TMV, Revision due to liquid value adjustments, Measurement Standardization → ARAP Batch Job**

![Step 11 — Facility Batch Job Submittal](Case_26-01063725_Walkthrough_images/image11.png)

**Step 12 — PTR Overlay Synchronization process (TSP 30051, acct 02/2026)**

![Step 12 — PTR Overlay Synchronization](Case_26-01063725_Walkthrough_images/image12.png)

---

## AFTER — bug appears

**Step 13 — re-run Allocation Imbalance Report (same params as step 6)**

![Step 13 — Report execution params](Case_26-01063725_Walkthrough_images/image6.png)

**Step 14 — AFTER report: PPA now appears under TMV. PPA Rec Qty and PPA PtR Qty net to zero, but PPA Fuel Qty still generates a value.**

![Step 14 — AFTER report, spurious PPA fuel](Case_26-01063725_Walkthrough_images/image13.png)

**Step 15 — PPA Status: still 11 records under PRD 1/1/2026 (none newly processed)**

![Step 15 — PPA Status after](Case_26-01063725_Walkthrough_images/image14.png)

**Expected result:** the user should successfully get the report with **no fuel PPA added**.

---

## After / Resolution / Technical Solution

*Left blank in the source document — Engineering completes these after development.*

---

## L4 Notes (analysis — not part of the source doc)

The AFTER report (image13) is the decisive evidence. Under **Plant TMV, Proc K 12514**, each receipt location posts a paired **RES / REV** entry:

| Rec Loc | PPA Rec | PPA Fuel | PPA PtR |
|---|---|---|---|
| MCKENDRICK | 50 / (50) | 1 / (2) | 12 / (12) |
| BLUE STONE | 650 / (650) | 7 / (8) | 154 / (154) |
| CLARK HEREFORD | 50 / (50) | 1 / (2) | 11 / (11) |

**Prod Mth 01/01/2026 Total: PPA Rec = 0, PPA PtR = 0, PPA Del = 0 — but PPA Fuel = (4).**

Receipt and PtR net **exactly to zero** (no real allocation change), yet fuel leaves a non-zero **(4)** residual. A no-op restate is producing phantom PPA fuel.

This walkthrough is the **fresh reproduction data cut** supporting reopening bug **#1753672** (previously Closed/Rejected because Dev could not reproduce). It aligns with the documented RCA: the **PTR Overlay Synchronization (ALPTRSYNC)** force-reallocates with no value-change gate, and **ALALLOCATE re-rounds fuel** on the restate — so fuel rounding survives even when receipt and PtR cancel to zero.

---

## L4 Triaged — Root Cause & Suggested Code Fix

**Classification:** Software Defect — confirmed at code level (not config, not user error, not as-designed). Full triage: `Case_26-01063725_L4_Triaged.md`.

**Process / file:** `ALPTRSYNC` = `ENT.QPTM.ClassicBatch` / `QPDllPipelineMgrAL_ENT/QPSTIPSPtrAllocSync.cpp` (repo `3be6f2b9-…`). TMV = South Texas → the standard file, not the Permian `_PRM` twin.

**Two compounding defects:**

- **Defect A — PTR Overlay Sync reallocates with no value-change gate.** `AllocateSubTotalsToDailyNom()` calls `SetSchdEngQtyOverride()` (**L1547**) which flips `m_bIsPPA` unconditionally; `IsOverride()` returns that flag. `DoReAllocation()` then gates the reallocation **only** on `if (pNomAlloc->IsOverride())` (**L1158**) — *not* on whether the recomputed PTR override actually differs from the booked alloc. It writes an `ALTRAN_REALLOC_SEL` row (`TRIGGER_SRC_CD=PTR` L1196, `PPA_SRC_CD=…PTR` L1199) and launches synchronous **ALALLOCATE** (L1251) with **`REALLOC_IND=true`** (L1274) for every override nom. So an idempotent PTR re-sync (TIPS re-sends the same PTR after the liquid-value rerun) still forces a full reallocation.
- **Defect B — fuel doesn't net to zero on the restate (downstream in ALALLOCATE).** This file writes only `SCHD_ENG_QTY_OVRD` (never fuel). When the forced ALALLOCATE re-runs, REC and PtR re-derive identically (net 0), but **Fuel (= alloc × fuel rate, progressively rounded) is re-rounded asymmetrically** across the RES/REV legs → the non-zero `(4)` residual booked as PPA fuel. ALALLOCATE was modified by the PTR-overlay feature under ADO **#1617125** (where the recompute lives).

### Suggested code fix (ranked)

**Primary (lowest risk) — propagate the value-change decision `UpdateOverrides` already computes, and gate the reallocation on it.**

> **File to modify:** `ENT.QPTM.ClassicBatch` → `/QPDllPipelineMgrAL_ENT/QPSTIPSPtrAllocSync.cpp` (+ header `QPSTIPSPtrAllocSync.h`), repo GUID `3be6f2b9-48fc-4999-b873-a37a0cce97ac`, branch `develop`
> **Where:** `UpdateOverrides()` (~L942/L977/L989) sets a new change flag; `DoReAllocation()` gates on it at **line 1158**.

An override is by definition different from the plain scheduled qty, so comparing it against the booked `GetSchedEngQty()` is the **wrong baseline** (almost always "different" → would not suppress the no-op). The correct baseline is the **previously-stored override** in `ALCTRL_ALLOC_OVRD`, which `UpdateOverrides` already compares (L999) but discards. Surface that change decision on the data object and gate the reallocation on it — four small, convention-following edits:

```cpp
// 1) QPSTIPSPtrAllocSync.h — QNomAllocData: change flag distinct from m_bIsPPA
	bool  IsOvrdChanged() const					{ return m_bOvrdChanged; }
	void  SetOvrdChanged(bool bChanged)			{ m_bOvrdChanged = bChanged; }
	bool    m_bOvrdChanged;   // private member, beside m_bIsPPA

// 2) QPSTIPSPtrAllocSync.cpp — init in BOTH ctors
	, m_bOvrdChanged(false)              // default ctor init list (~L1304)
	m_bOvrdChanged = rhs.m_bOvrdChanged; // copy ctor body (~L1327)

// 3) UpdateOverrides — record the change, reusing the existing CompareValue (~L993, non-null branch)
	const bool bOvrdChanged = bOrigSchdEngQtyIsNull
		|| QUtilityPipelineMgr::CompareValue(pNomAlloc->GetSchdEngQtyOverride(),
											 dOrigSchdEngQtyOvrd,
											 QUtilityPipelineMgr::msc_dCOLUMN_PRECISION_10) != 0;
	pNomAlloc->SetOvrdChanged(bOvrdChanged);
	if (bIsPPAMonth && bOvrdChanged) { bIsPPA = true; }
	// (also: SetOvrdChanged(true) in the insert branch ~L964; SetOvrdChanged(!bOrigSchdEngQtyIsNull) in the clear-to-NULL branch ~L981)

// 4) DoReAllocation (~L1158) — gate on the real change, not just "override applied"
	if (pNomAlloc->IsOverride() && pNomAlloc->IsOvrdChanged())
	{
		// ... existing ALTRAN_REALLOC_SEL write + ALALLOCATE launch (unchanged) ...
	}
```

An idempotent PTR re-sync now leaves `m_bOvrdChanged == false` → no realloc row, no ALALLOCATE → the spurious PPA is eliminated at the source (fuel and rec/ptr), while a genuine PTR change still reallocates. Localized to the ENT PTR-sync; reuses the file's own `CompareValue(..., msc_dCOLUMN_PRECISION_10)` idiom.

> ⚠️ Getter names are easy to transpose: booked = `GetSchedEngQty()` ("Sch**e**d"); override = `GetSch**d**EngQtyOverride()`. There is no `GetSchdEngQty()`.

**Full engineering handoff (precise diffs + ready-to-paste ADO bug write-up): `Case_26-01063725_L4_Triaged.md` §4 and §8.**

**Secondary (only if Primary is insufficient) — make ALALLOCATE carry-forward fuel** when REC and PtR net to zero on a restate, instead of recompute-and-re-round. Higher blast radius (core allocation engine, ADO #1617125 area).

> Apply the same Primary gate to the Permian twin `QPSTIPSPtrAllocSync_PRM.cpp` (same folder), which has the analogous defect (it writes the override into the legacy fuel column `crALLOC_FUEL_ENG_QTY_OVRD` ~L1370 rather than relying on ALALLOCATE to re-round).

### Expected result after fix
Re-running steps 8–14 with an **unchanged** measurement/PTR yields an AFTER report identical to BEFORE — **no PPA fuel under TMV** (no `ALTRAN_REALLOC_SEL` rows with `TRIGGER_SRC_CD=PTR` from the sync; no ALALLOCATE relaunch). A genuine PTR change still reallocates and books a legitimate PPA.

*Line numbers per `QPSTIPSPtrAllocSync.cpp` @ develop — confirm against the client's build branch before coding.*
