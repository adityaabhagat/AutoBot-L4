---
title: Allocations (ALLOC) - Troubleshooting Guide
category: troubleshooting
feature: Allocations (ALLOC)
related_repos: Web, Batch
keywords: ALLOC, troubleshooting, PDA, measurement, aggregate location, penalty schedule, allocation errors, diagnostic queries, reallocation, PPA, override
last_updated: 2026-03-03
---

# Allocations (ALLOC) - Troubleshooting Guide

## Overview

This document provides troubleshooting guidance for Allocations (ALLOC) issues in QPTM. It includes common problems, diagnostic SQL queries, error messages, investigation workflows, and historical issue patterns.

For business concepts, see [Domain Documentation](./domain.md).
For technical details, see [Architecture Documentation](./architecture.md).

---

## Table of Contents

1. [Common Issues](#common-issues)
2. [Diagnostic Queries](#diagnostic-queries)
3. [Key Code Locations](#key-code-locations)
4. [Investigation Workflow](#investigation-workflow)
5. [Performance Issues](#performance-issues)
6. [Historical Issues Template](#historical-issues-template)

---

## Common Issues

### Issue 1: Multiple PDA Headers Found

**Symptoms:**
- Error message: "More than one PDA header found" or similar duplicate header error
- Allocation processing fails for a specific location/date/direction
- PDA submission returns an unexpected error

**Root Causes:**
1. Duplicate PDA headers exist in `ALTRAN_PDA_HDR` for the same location, date range, and flow direction
2. Overlapping effective date ranges on PDAs for the same location
3. Data migration or manual insert created duplicates

**Diagnostic Query:**
```sql
-- Find duplicate PDA headers for a location
SELECT
    TSP_NO,
    LOC_ID,
    FLOW_DIR_CD,
    EFF_DATE_FROM,
    EFF_DATE_TO,
    ACCTG_MTH,
    COUNT(*) AS HeaderCount
FROM ALTRAN_PDA_HDR
WHERE TSP_NO = @TspNo
  AND LOC_ID = @LocationId
GROUP BY TSP_NO, LOC_ID, FLOW_DIR_CD, EFF_DATE_FROM, EFF_DATE_TO, ACCTG_MTH
HAVING COUNT(*) > 1;

-- View the duplicate records in detail
SELECT *
FROM ALTRAN_PDA_HDR
WHERE TSP_NO = @TspNo
  AND LOC_ID = @LocationId
  AND FLOW_DIR_CD = @FlowDirection
  AND EFF_DATE_FROM <= @GasDay
  AND EFF_DATE_TO >= @GasDay
ORDER BY UPDT_DT DESC;
```

**Solutions:**
- Identify and remove the duplicate PDA header (keep the most recent or correct one)
- Adjust effective date ranges to eliminate overlaps
- Add validation to prevent future duplicates (check `ValidationEnginePDA`)
- Review `QPTMAllocationServiceExt_PDA.cs` for the PDA lookup logic that expects a single header

---

### Issue 2: No PDA Header Found

**Symptoms:**
- Allocation processing skips a location with no error
- Allocated quantities are zero or missing for a location
- Log indicates "No PDA found" for the location/date combination

**Root Causes:**
1. No PDA submitted for the location/date/flow direction
2. PDA effective dates do not cover the gas day being processed
3. PDA status is not "submitted" or "active"
4. Wrong flow direction on the PDA (Receipt vs Delivery mismatch)
5. Wrong TSP number on the PDA

**Diagnostic Query:**
```sql
-- Check if any PDA exists for the location
SELECT
    h.TSP_NO,
    h.LOC_ID,
    h.FLOW_DIR_CD,
    h.EFF_DATE_FROM,
    h.EFF_DATE_TO,
    h.ACCTG_MTH,
    h.STATUS_CD,
    h.BA_ID,
    h.UPDT_DT,
    COUNT(d.PDA_DTL_ID) AS DetailLineCount
FROM ALTRAN_PDA_HDR h
LEFT JOIN ALTRAN_PDA_DTL d ON h.PDA_HDR_ID = d.PDA_HDR_ID
WHERE h.TSP_NO = @TspNo
  AND h.LOC_ID = @LocationId
GROUP BY h.TSP_NO, h.LOC_ID, h.FLOW_DIR_CD, h.EFF_DATE_FROM,
         h.EFF_DATE_TO, h.ACCTG_MTH, h.STATUS_CD, h.BA_ID, h.UPDT_DT
ORDER BY h.EFF_DATE_FROM DESC;

-- Check if PDA covers the specific gas day
SELECT *
FROM ALTRAN_PDA_HDR
WHERE TSP_NO = @TspNo
  AND LOC_ID = @LocationId
  AND FLOW_DIR_CD = @FlowDirection
  AND EFF_DATE_FROM <= @GasDay
  AND EFF_DATE_TO >= @GasDay
  AND STATUS_CD IN ('S', 'A');  -- Submitted/Active statuses
```

**Solutions:**
- Create and submit a PDA for the missing location/date/direction
- Extend the effective date range of an existing PDA
- Correct the flow direction on the PDA
- Verify the PDA status is submitted/active
- Check that the TSP number matches

---

### Issue 3: No Allocation Plan Transaction Type

**Symptoms:**
- Allocation processing fails with "No allocation plan trans type" or similar message
- Specific transaction types are not being allocated
- Allocation results are incomplete (some contracts missing)

**Root Causes:**
1. No `ALLOC_PLAN_TRANS_TYPE` records exist for the allocation plan
2. Transaction type code in PDA does not match any plan entry
3. Allocation plan header is inactive or expired

**Diagnostic Query:**
```sql
-- Check allocation plan and its transaction types
SELECT
    h.PLAN_ID,
    h.TSP_NO,
    h.PLAN_NM,
    h.EFF_DATE_FROM,
    h.EFF_DATE_TO,
    tt.TRANS_TYPE_CD,
    att.TRANS_TYPE_DESC
FROM ALLOC_PLAN_HDR h
LEFT JOIN ALLOC_PLAN_TRANS_TYPE tt ON h.PLAN_ID = tt.PLAN_ID
LEFT JOIN ALLOC_TRANS_TYPE att ON tt.TRANS_TYPE_CD = att.TRANS_TYPE_CD
WHERE h.TSP_NO = @TspNo
  AND @GasDay BETWEEN h.EFF_DATE_FROM AND h.EFF_DATE_TO
ORDER BY h.PLAN_ID, tt.TRANS_TYPE_CD;

-- Check all available allocation transaction types
SELECT *
FROM ALLOC_TRANS_TYPE
ORDER BY TRANS_TYPE_CD;

-- Check if any plan covers the location
SELECT
    h.PLAN_ID,
    h.PLAN_NM,
    pl.LOC_ID,
    pl.PARENT_LOC_ID
FROM ALLOC_PLAN_HDR h
INNER JOIN ALLOC_PLAN_LOC pl ON h.PLAN_ID = pl.PLAN_ID
WHERE h.TSP_NO = @TspNo
  AND pl.LOC_ID = @LocationId
  AND @GasDay BETWEEN h.EFF_DATE_FROM AND h.EFF_DATE_TO;
```

**Solutions:**
- Add the missing transaction type to `ALLOC_PLAN_TRANS_TYPE`
- Verify the allocation plan header is active and covers the gas day
- Ensure the location is mapped in `ALLOC_PLAN_LOC`
- Check that the transaction type code matches between PDA and plan

---

### Issue 4: No BAs (Business Associates) for User

**Symptoms:**
- User cannot create or view PDAs
- "No Business Associates found for user" error
- PDA screen shows empty BA dropdown

**Root Causes:**
1. User not linked to any Business Associate in the security system
2. BA is inactive or expired
3. User's BA does not have allocation permissions for the TSP/location

**Diagnostic Query:**
```sql
-- Check user-to-BA linkage
SELECT
    u.sUserID,
    u.sUserName,
    uba.nBaNo AS BA_Number,
    ba.sBAName AS BA_Name,
    ba.sBAStatus AS BA_Status
FROM tUser u
LEFT JOIN tUserBA uba ON u.sUserID = uba.sUserID
LEFT JOIN tBA ba ON uba.nBaNo = ba.nBaNo
WHERE u.sUserID = @UserId;

-- Check BA's TSP/location permissions for allocations
SELECT
    ba.nBaNo,
    ba.sBAName,
    bta.nTspNo,
    bta.nLocId
FROM tBA ba
INNER JOIN tBAAllocationAccess bta ON ba.nBaNo = bta.nBaNo
WHERE ba.nBaNo = @BaNumber
  AND bta.nTspNo = @TspNo;
```

**Solutions:**
- Link the user to the appropriate Business Associate
- Verify the BA is active (status check)
- Grant the BA allocation access for the required TSP/location
- Check the `DailyAllocatedQuantityMaintenance` security code is assigned to the user's role

---

### Issue 5: No Contact Types for Role

**Symptoms:**
- PDA validation fails with "No contact types for role" error
- User role does not have the required contact type configuration
- PDA submission blocked at validation step

**Root Causes:**
1. User's role is missing required contact type mappings
2. Contact type configuration is incomplete for the allocation feature
3. Role-to-contact-type association expired or removed

**Diagnostic Query:**
```sql
-- Check role contact type assignments
SELECT
    r.sRoleName,
    rct.sContactTypeCD,
    ct.sContactTypeDesc
FROM tRole r
LEFT JOIN tRoleContactType rct ON r.nRoleID = rct.nRoleID
LEFT JOIN tContactType ct ON rct.sContactTypeCD = ct.sContactTypeCD
WHERE r.nRoleID = @RoleId;

-- Check what contact types are required for PDA
SELECT DISTINCT
    sContactTypeCD,
    sContactTypeDesc
FROM tContactType
WHERE sContactTypeCD IN ('PDA', 'ALLOC', 'MEAS');
```

**Solutions:**
- Add the required contact type to the user's role
- Verify contact type definitions exist in the reference table
- Review `ValidationRuleBasePDABusiness` for the specific contact type requirement
- Ensure role configuration includes allocation-related contact types

---

### Issue 6: Allocation Quantities Zero or Null

**Symptoms:**
- Allocation results show zero or NULL for AllocQty
- Expected volumes not distributed to contracts
- Daily/monthly allocation screens show blank quantities

**Root Causes:**
1. Measurement data (MeasQty) is zero or missing for the location
2. Scheduled quantities (SchdQty) are zero (no nominations or CAS results)
3. PDA detail lines have zero percentage or amount values
4. Allocation method calculation produces zero (e.g., pro-rata with zero total scheduled)
5. Override set to zero

**Diagnostic Query:**
```sql
-- Check measurement data exists for the location/day
SELECT
    TSP_NO,
    GAS_DAY,
    LOC_ID,
    TOTAL_VOL,
    HR_01, HR_02, HR_03, HR_04, HR_05, HR_06,
    HR_07, HR_08, HR_09, HR_10, HR_11, HR_12,
    HR_13, HR_14, HR_15, HR_16, HR_17, HR_18,
    HR_19, HR_20, HR_21, HR_22, HR_23, HR_24
FROM ALCTRL_MEAS_VOL
WHERE TSP_NO = @TspNo
  AND LOC_ID = @LocationId
  AND GAS_DAY = @GasDay;

-- Check allocation results
SELECT
    TSP_NO,
    GAS_DAY,
    LOC_ID,
    CTR_NO,
    FLOW_DIR_CD,
    SCHD_QTY,
    ALLOC_QTY,
    MEAS_QTY
FROM ALCTRL_ALLOC
WHERE TSP_NO = @TspNo
  AND LOC_ID = @LocationId
  AND GAS_DAY = @GasDay;

-- Check PDA detail values
SELECT
    h.LOC_ID,
    d.CTR_NO,
    d.ALLOC_METHOD_CD,
    d.PCT_VAL,
    d.AMT_VAL,
    d.PRIORITY_CD
FROM ALTRAN_PDA_HDR h
INNER JOIN ALTRAN_PDA_DTL d ON h.PDA_HDR_ID = d.PDA_HDR_ID
WHERE h.TSP_NO = @TspNo
  AND h.LOC_ID = @LocationId
  AND h.EFF_DATE_FROM <= @GasDay
  AND h.EFF_DATE_TO >= @GasDay;

-- Check if scheduled quantities exist (from CAS/Nominations)
SELECT
    TSP_NO,
    GAS_DAY,
    LOC_ID,
    CTR_NO,
    SCHD_QTY
FROM ALCTRL_ALLOC
WHERE TSP_NO = @TspNo
  AND LOC_ID = @LocationId
  AND GAS_DAY = @GasDay
  AND (SCHD_QTY IS NULL OR SCHD_QTY = 0);
```

**Solutions:**
- Verify measurement data is loaded (run measurement load process)
- Check CAS/nomination processing produced scheduled quantities
- Verify PDA detail lines have non-zero percentages/amounts
- For pro-rata (PRT) method, ensure total scheduled quantity at location > 0
- Check for overrides that may have set quantities to zero
- Review `QPTMAllocationServiceExt_Measurement.cs` 3-case logic for the accounting month

---

### Issue 7: Measurements Not Rolling Up (Aggregate Location)

**Symptoms:**
- Parent (aggregate) location shows zero or stale measurement volumes
- Child locations have measurements but parent does not reflect them
- Aggregate location rollup process completes but results are incorrect

**Root Causes:**
1. Allocation plan location mapping (`ALLOC_PLAN_LOC`) is missing or incorrect
2. Child location data not loaded before rollup executes
3. Rollup process not triggered or failed silently
4. Parent-child hierarchy definition is wrong (wrong parent assignment)
5. Null handling: all children have NULL measurements, causing parent to remain NULL

**Diagnostic Query:**
```sql
-- Check allocation plan location hierarchy
SELECT
    h.PLAN_ID,
    h.PLAN_NM,
    pl.LOC_ID AS ChildLocId,
    pl.PARENT_LOC_ID AS ParentLocId,
    l1.LOC_NM AS ChildLocName,
    l2.LOC_NM AS ParentLocName
FROM ALLOC_PLAN_HDR h
INNER JOIN ALLOC_PLAN_LOC pl ON h.PLAN_ID = pl.PLAN_ID
LEFT JOIN tLocation l1 ON pl.LOC_ID = l1.nLocId
LEFT JOIN tLocation l2 ON pl.PARENT_LOC_ID = l2.nLocId
WHERE h.TSP_NO = @TspNo
  AND pl.PARENT_LOC_ID = @ParentLocationId;

-- Compare child measurements vs parent
SELECT
    'Parent' AS LocType,
    mv.LOC_ID,
    mv.GAS_DAY,
    mv.TOTAL_VOL
FROM ALCTRL_MEAS_VOL mv
WHERE mv.TSP_NO = @TspNo
  AND mv.LOC_ID = @ParentLocationId
  AND mv.GAS_DAY = @GasDay

UNION ALL

SELECT
    'Child' AS LocType,
    mv.LOC_ID,
    mv.GAS_DAY,
    mv.TOTAL_VOL
FROM ALCTRL_MEAS_VOL mv
WHERE mv.TSP_NO = @TspNo
  AND mv.LOC_ID IN (
      SELECT LOC_ID
      FROM ALLOC_PLAN_LOC
      WHERE PARENT_LOC_ID = @ParentLocationId
  )
  AND mv.GAS_DAY = @GasDay
ORDER BY LocType, LOC_ID;

-- Verify sum of children equals parent
SELECT
    @ParentLocationId AS ParentLocId,
    (SELECT TOTAL_VOL FROM ALCTRL_MEAS_VOL
     WHERE TSP_NO = @TspNo AND LOC_ID = @ParentLocationId AND GAS_DAY = @GasDay) AS ParentTotal,
    SUM(mv.TOTAL_VOL) AS ChildrenSum,
    (SELECT TOTAL_VOL FROM ALCTRL_MEAS_VOL
     WHERE TSP_NO = @TspNo AND LOC_ID = @ParentLocationId AND GAS_DAY = @GasDay) - SUM(mv.TOTAL_VOL) AS Difference
FROM ALCTRL_MEAS_VOL mv
WHERE mv.TSP_NO = @TspNo
  AND mv.LOC_ID IN (
      SELECT LOC_ID FROM ALLOC_PLAN_LOC WHERE PARENT_LOC_ID = @ParentLocationId
  )
  AND mv.GAS_DAY = @GasDay;
```

**Solutions:**
- Verify `ALLOC_PLAN_LOC` has correct parent-child mappings
- Ensure child location measurements are loaded before running rollup
- Re-run the aggregate location rollup (`QPTMAllocationServiceExt_AggregateLocation.cs`)
- Check the 4-stage rollup algorithm for failures in any stage (filter, load, rollup, save)
- Verify the allocation plan header is active and covers the gas day

---

### Issue 8: TSP Gas Flow Not Set Up

**Symptoms:**
- Allocation processing fails with "TSP gas flow not set up" or similar configuration error
- No gas flow direction configured for the TSP at the location
- Allocation cannot determine receipt vs delivery for the location

**Root Causes:**
1. TSP configuration is missing gas flow direction settings
2. Location does not have a flow direction assigned for the TSP
3. TSP cache contains stale data that does not reflect recent configuration changes

**Diagnostic Query:**
```sql
-- Check TSP gas flow configuration
SELECT
    TSP_NO,
    LOC_ID,
    FLOW_DIR_CD,
    EFF_DATE_FROM,
    EFF_DATE_TO
FROM tTSPGasFlow  -- Actual table name may vary
WHERE TSP_NO = @TspNo
  AND LOC_ID = @LocationId
  AND @GasDay BETWEEN EFF_DATE_FROM AND EFF_DATE_TO;

-- Check TSP configuration
SELECT *
FROM tTSP
WHERE nTspNo = @TspNo;

-- Check if location is configured for the TSP
SELECT
    l.nLocId,
    l.sLocName,
    tl.nTspNo,
    tl.sFlowDirCd
FROM tLocation l
INNER JOIN tTSPLocation tl ON l.nLocId = tl.nLocId
WHERE tl.nTspNo = @TspNo
  AND l.nLocId = @LocationId;
```

**Solutions:**
- Configure gas flow direction for the TSP/location combination
- Verify effective dates cover the gas day being processed
- Clear the `TspCache` to ensure fresh configuration is loaded
- Review TSP setup in the admin screens

---

### Issue 9: Numeric Overflow in Rollup

**Symptoms:**
- Aggregate location rollup fails with "Arithmetic overflow" or "Numeric overflow" error
- Large volume values cause data type overflow during summation
- Rollup process crashes for specific parent locations

**Root Causes:**
1. Child location measurements have extremely large values (data entry error or meter malfunction)
2. Sum of child volumes exceeds the database column's numeric precision/scale
3. Null-to-zero conversion creates unexpected large sums
4. Duplicate child records cause double-counting in summation

**Diagnostic Query:**
```sql
-- Check for abnormally large measurement values
SELECT
    mv.LOC_ID,
    mv.GAS_DAY,
    mv.TOTAL_VOL,
    mv.HR_01, mv.HR_02, mv.HR_03, mv.HR_04,
    mv.HR_05, mv.HR_06, mv.HR_07, mv.HR_08,
    mv.HR_09, mv.HR_10, mv.HR_11, mv.HR_12,
    mv.HR_13, mv.HR_14, mv.HR_15, mv.HR_16,
    mv.HR_17, mv.HR_18, mv.HR_19, mv.HR_20,
    mv.HR_21, mv.HR_22, mv.HR_23, mv.HR_24
FROM ALCTRL_MEAS_VOL mv
WHERE mv.TSP_NO = @TspNo
  AND mv.LOC_ID IN (
      SELECT LOC_ID FROM ALLOC_PLAN_LOC WHERE PARENT_LOC_ID = @ParentLocationId
  )
  AND mv.GAS_DAY = @GasDay
  AND (mv.TOTAL_VOL > 99999999 OR mv.TOTAL_VOL < -99999999);

-- Check for duplicate child location entries in plan
SELECT
    pl.LOC_ID,
    pl.PARENT_LOC_ID,
    COUNT(*) AS DuplicateCount
FROM ALLOC_PLAN_LOC pl
WHERE pl.PARENT_LOC_ID = @ParentLocationId
GROUP BY pl.LOC_ID, pl.PARENT_LOC_ID
HAVING COUNT(*) > 1;

-- Calculate expected sum to verify overflow risk
SELECT
    SUM(CAST(mv.TOTAL_VOL AS DECIMAL(20,4))) AS TotalChildSum
FROM ALCTRL_MEAS_VOL mv
WHERE mv.TSP_NO = @TspNo
  AND mv.LOC_ID IN (
      SELECT LOC_ID FROM ALLOC_PLAN_LOC WHERE PARENT_LOC_ID = @ParentLocationId
  )
  AND mv.GAS_DAY = @GasDay;
```

**Solutions:**
- Correct abnormally large measurement values (likely data entry or meter errors)
- Remove duplicate child location entries from `ALLOC_PLAN_LOC`
- Increase numeric precision/scale on the parent location's measurement column if legitimate volumes are large
- Review `QPTMAllocationServiceExt_AggregateLocation.cs` rollup stage 3 for overflow handling
- Add data validation to prevent unreasonable measurement values

---

### Issue 10: PPA Not Triggering

**Symptoms:**
- Reallocation runs but PPA (Previously Posted Allocations) records are not created
- No audit trail of previous allocation values
- Adjustment quantities cannot be calculated because there is no "before" snapshot

**Root Causes:**
1. Allocation was never posted (PPA only created when overwriting posted allocations)
2. PPA creation logic is bypassed due to a status check
3. Reallocation method does not invoke PPA snapshot code
4. Database transaction rolled back, losing PPA records

**Diagnostic Query:**
```sql
-- Check if original allocation was posted
SELECT
    TSP_NO,
    GAS_DAY,
    LOC_ID,
    CTR_NO,
    FLOW_DIR_CD,
    ALLOC_QTY,
    STATUS_CD,
    POST_DT,
    UPDT_DT
FROM ALCTRL_ALLOC
WHERE TSP_NO = @TspNo
  AND LOC_ID = @LocationId
  AND GAS_DAY = @GasDay
ORDER BY CTR_NO;

-- Check if PPA records exist
SELECT *
FROM ALTRAN_ALLOC
WHERE TSP_NO = @TspNo
  AND LOC_ID = @LocationId
  AND GAS_DAY = @GasDay
  AND TRANS_TYPE_CD = 'PPA'
ORDER BY CTR_NO;

-- Check allocation history for the location/day
SELECT
    TSP_NO,
    GAS_DAY,
    LOC_ID,
    CTR_NO,
    ALLOC_QTY,
    UPDT_DT,
    UPDT_USER
FROM ALCTRL_ALLOC
WHERE TSP_NO = @TspNo
  AND LOC_ID = @LocationId
  AND GAS_DAY = @GasDay
ORDER BY UPDT_DT DESC;

-- Check ALCTRL_ANALYSIS for reallocation audit trail
SELECT *
FROM ALCTRL_ANALYSIS
WHERE TSP_NO = @TspNo
  AND LOC_ID = @LocationId
  AND GAS_DAY = @GasDay
ORDER BY UPDT_DT DESC;
```

**Solutions:**
- Verify the original allocation was posted (STATUS_CD indicates posted)
- Check `QPTMAllocationServiceExt_PDA.cs` for the PPA snapshot logic -- ensure it runs before reallocation
- Manually create PPA records from current allocation data before running reallocation
- Review transaction management to ensure PPA insert commits before allocation update
- Check the reallocation workflow to confirm it calls the PPA snapshot method

---

### Issue 11: PDA Validation Failures (PCT Totals)

**Symptoms:**
- PDA submission fails with "Percentage total does not equal 100%" error
- Percentage-method PDA cannot be saved
- Rounding causes percentages to sum to 99.99% or 100.01%

**Root Causes:**
1. PDA detail line percentages do not sum to exactly 100%
2. Floating point rounding creates small discrepancies
3. A detail line was deleted but percentages not redistributed

**Diagnostic Query:**
```sql
-- Check PDA percentage totals
SELECT
    h.PDA_HDR_ID,
    h.LOC_ID,
    h.FLOW_DIR_CD,
    SUM(d.PCT_VAL) AS TotalPercent,
    COUNT(d.PDA_DTL_ID) AS LineCount
FROM ALTRAN_PDA_HDR h
INNER JOIN ALTRAN_PDA_DTL d ON h.PDA_HDR_ID = d.PDA_HDR_ID
WHERE h.TSP_NO = @TspNo
  AND h.LOC_ID = @LocationId
  AND d.ALLOC_METHOD_CD = 'PCT'
GROUP BY h.PDA_HDR_ID, h.LOC_ID, h.FLOW_DIR_CD
HAVING ABS(SUM(d.PCT_VAL) - 100.0) > 0.001;
```

**Solutions:**
- Adjust PDA detail line percentages to sum to exactly 100%
- Check `ValidationRuleBasePDALine` for the tolerance threshold used in validation
- Review rounding logic in the PDA UI to prevent precision issues

---

### Issue 12: Hourly Measurement Data Missing for Specific Hours

**Symptoms:**
- Daily totals are lower than expected
- Specific hourly columns (HR_01 through HR_24) are NULL
- Allocation uses partial daily measurement

**Root Causes:**
1. Meter outage during specific hours
2. Measurement load process ran before all hourly data was available
3. SCADA data feed interrupted for specific hours

**Diagnostic Query:**
```sql
-- Check for NULL hours in measurement data
SELECT
    LOC_ID,
    GAS_DAY,
    TOTAL_VOL,
    CASE WHEN HR_01 IS NULL THEN 'NULL' ELSE CAST(HR_01 AS VARCHAR) END AS HR_01,
    CASE WHEN HR_02 IS NULL THEN 'NULL' ELSE CAST(HR_02 AS VARCHAR) END AS HR_02,
    CASE WHEN HR_03 IS NULL THEN 'NULL' ELSE CAST(HR_03 AS VARCHAR) END AS HR_03,
    -- ... repeat for HR_04 through HR_24
    CASE WHEN HR_24 IS NULL THEN 'NULL' ELSE CAST(HR_24 AS VARCHAR) END AS HR_24
FROM ALCTRL_MEAS_VOL
WHERE TSP_NO = @TspNo
  AND LOC_ID = @LocationId
  AND GAS_DAY = @GasDay;

-- Count NULL hours per location
SELECT
    LOC_ID,
    GAS_DAY,
    (CASE WHEN HR_01 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_02 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_03 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_04 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_05 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_06 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_07 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_08 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_09 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_10 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_11 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_12 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_13 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_14 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_15 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_16 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_17 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_18 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_19 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_20 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_21 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_22 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_23 IS NULL THEN 1 ELSE 0 END +
     CASE WHEN HR_24 IS NULL THEN 1 ELSE 0 END) AS NullHourCount
FROM ALCTRL_MEAS_VOL
WHERE TSP_NO = @TspNo
  AND GAS_DAY = @GasDay
  AND LOC_ID = @LocationId;
```

**Solutions:**
- Re-run measurement load after missing hourly data becomes available
- Review `QPTMAllocationServiceExt_Measurement.cs` for handling of partial hourly data
- Check SCADA/meter data feed for the specific hours
- If data cannot be recovered, use manual override to set estimated hourly values

---

## Diagnostic Queries

### Query 1: Allocation Overview for Gas Day

**Purpose**: Complete view of allocation results for a gas day.

```sql
SELECT
    a.TSP_NO,
    a.GAS_DAY,
    a.LOC_ID,
    l.sLocName AS LocationName,
    a.CTR_NO,
    a.FLOW_DIR_CD,
    a.SCHD_QTY,
    a.ALLOC_QTY,
    a.MEAS_QTY,
    a.ALLOC_QTY - a.SCHD_QTY AS Imbalance,
    CASE
        WHEN a.SCHD_QTY > 0 THEN
            CAST(((a.ALLOC_QTY - a.SCHD_QTY) / a.SCHD_QTY) * 100 AS DECIMAL(10,2))
        ELSE NULL
    END AS ImbalancePct,
    a.STATUS_CD,
    a.UPDT_DT
FROM ALCTRL_ALLOC a
LEFT JOIN tLocation l ON a.LOC_ID = l.nLocId
WHERE a.TSP_NO = @TspNo
  AND a.GAS_DAY = @GasDay
ORDER BY a.LOC_ID, a.CTR_NO;
```

### Query 2: PDA Configuration Summary

**Purpose**: View all active PDAs and their detail lines for a location.

```sql
SELECT
    h.PDA_HDR_ID,
    h.LOC_ID,
    h.FLOW_DIR_CD,
    h.EFF_DATE_FROM,
    h.EFF_DATE_TO,
    h.ACCTG_MTH,
    h.STATUS_CD,
    h.BA_ID,
    d.PDA_DTL_ID,
    d.CTR_NO,
    d.ALLOC_METHOD_CD,
    d.PCT_VAL,
    d.AMT_VAL,
    d.PRIORITY_CD
FROM ALTRAN_PDA_HDR h
INNER JOIN ALTRAN_PDA_DTL d ON h.PDA_HDR_ID = d.PDA_HDR_ID
WHERE h.TSP_NO = @TspNo
  AND h.LOC_ID = @LocationId
  AND h.EFF_DATE_FROM <= @GasDay
  AND h.EFF_DATE_TO >= @GasDay
ORDER BY h.FLOW_DIR_CD, d.PRIORITY_CD, d.CTR_NO;
```

### Query 3: Measurement vs Allocation Comparison

**Purpose**: Compare measured volumes against allocated quantities at each location.

```sql
SELECT
    mv.LOC_ID,
    l.sLocName AS LocationName,
    mv.GAS_DAY,
    mv.TOTAL_VOL AS MeasuredTotal,
    SUM(a.ALLOC_QTY) AS AllocatedTotal,
    mv.TOTAL_VOL - SUM(a.ALLOC_QTY) AS Unallocated,
    COUNT(a.CTR_NO) AS ContractCount
FROM ALCTRL_MEAS_VOL mv
LEFT JOIN ALCTRL_ALLOC a ON
    mv.TSP_NO = a.TSP_NO AND
    mv.LOC_ID = a.LOC_ID AND
    mv.GAS_DAY = a.GAS_DAY
LEFT JOIN tLocation l ON mv.LOC_ID = l.nLocId
WHERE mv.TSP_NO = @TspNo
  AND mv.GAS_DAY = @GasDay
GROUP BY mv.LOC_ID, l.sLocName, mv.GAS_DAY, mv.TOTAL_VOL
HAVING ABS(mv.TOTAL_VOL - SUM(a.ALLOC_QTY)) > 0.01
ORDER BY ABS(mv.TOTAL_VOL - SUM(a.ALLOC_QTY)) DESC;
```

### Query 4: Monthly Allocation Summary

**Purpose**: Monthly aggregation of allocation data for billing reconciliation.

```sql
SELECT
    a.TSP_NO,
    a.LOC_ID,
    l.sLocName AS LocationName,
    a.CTR_NO,
    a.FLOW_DIR_CD,
    COUNT(DISTINCT a.GAS_DAY) AS DayCount,
    SUM(a.SCHD_QTY) AS MonthlySchdQty,
    SUM(a.ALLOC_QTY) AS MonthlyAllocQty,
    SUM(a.MEAS_QTY) AS MonthlyMeasQty,
    SUM(a.ALLOC_QTY) - SUM(a.SCHD_QTY) AS MonthlyImbalance
FROM ALCTRL_ALLOC a
LEFT JOIN tLocation l ON a.LOC_ID = l.nLocId
WHERE a.TSP_NO = @TspNo
  AND a.GAS_DAY >= @MonthStartDate
  AND a.GAS_DAY <= @MonthEndDate
GROUP BY a.TSP_NO, a.LOC_ID, l.sLocName, a.CTR_NO, a.FLOW_DIR_CD
ORDER BY a.LOC_ID, a.CTR_NO;
```

### Query 5: PPA Adjustment Analysis

**Purpose**: Analyze reallocation adjustments by comparing PPA to current allocations.

```sql
SELECT
    a.LOC_ID,
    a.CTR_NO,
    a.GAS_DAY,
    a.FLOW_DIR_CD,
    a.ALLOC_QTY AS CurrentAllocQty,
    ppa.ALLOC_QTY AS PPAAllocQty,
    a.ALLOC_QTY - ppa.ALLOC_QTY AS Adjustment
FROM ALCTRL_ALLOC a
INNER JOIN ALTRAN_ALLOC ppa ON
    a.TSP_NO = ppa.TSP_NO AND
    a.LOC_ID = ppa.LOC_ID AND
    a.CTR_NO = ppa.CTR_NO AND
    a.GAS_DAY = ppa.GAS_DAY AND
    a.FLOW_DIR_CD = ppa.FLOW_DIR_CD AND
    ppa.TRANS_TYPE_CD = 'PPA'
WHERE a.TSP_NO = @TspNo
  AND a.GAS_DAY >= @StartDate
  AND a.GAS_DAY <= @EndDate
ORDER BY a.LOC_ID, a.CTR_NO, a.GAS_DAY;
```

---

## Key Code Locations

| Component | File/Class | What to Look For |
|-----------|-----------|------------------|
| Main Service | `QPTMAllocationService.cs` | Orchestration logic, method routing |
| PDA Processing | `QPTMAllocationServiceExt_PDA.cs` (~252KB) | PDA method assignment, allocation method logic (PRT/PRI/PCT/AMT), PPA snapshot, bulk vs non-bulk |
| Measurement Load | `QPTMAllocationServiceExt_Measurement.cs` | 3-case logic for hourly data, ACCTG_MTH_LAG_TIME handling |
| Aggregate Rollup | `QPTMAllocationServiceExt_AggregateLocation.cs` | 4-stage rollup algorithm, parent-child hierarchy |
| Penalty Schedule | `QPTMAllocationServiceExt_PenaltySchedule.cs` | Imbalance calculation, penalty tier logic |
| PDA Validation | `ValidationEnginePDA` | Validation orchestration |
| Header Validation | `ValidationRuleBasePDABusiness` | TSP, location, date, BA validation |
| Line Validation | `ValidationRuleBasePDALine` | Contract, method, percentage, priority validation |
| Daily UI Controller | `DailyAllocatedQuantityMaintenanceController` | Security: DailyAllocatedQuantityMaintenance |
| Monthly UI Controller | `MonthlyAllocatedQuantityMaintenanceController` | Monthly allocation review/posting |
| API Controller | `AllocationsController` | Route: /api/v1/Allocations |
| Allocation Cache | `AllocationCache` | Allocation reference data caching |
| Location Cache | `LocationCache` | Location hierarchy caching |
| TSP Cache | `TspCache` | TSP configuration caching |
| Cycle Cache | `CycleCache` | Accounting month/cycle caching |

---

## Investigation Workflow

### Step-by-Step Investigation Process

**Step 1: Verify Data Exists**
```sql
-- Check if PDA exists for the location/day
SELECT COUNT(*) AS PDACount
FROM ALTRAN_PDA_HDR
WHERE TSP_NO = @TspNo
  AND LOC_ID = @LocationId
  AND EFF_DATE_FROM <= @GasDay
  AND EFF_DATE_TO >= @GasDay;

-- Check if measurements exist
SELECT COUNT(*) AS MeasCount
FROM ALCTRL_MEAS_VOL
WHERE TSP_NO = @TspNo
  AND LOC_ID = @LocationId
  AND GAS_DAY = @GasDay;

-- Check if allocation results exist
SELECT COUNT(*) AS AllocCount
FROM ALCTRL_ALLOC
WHERE TSP_NO = @TspNo
  AND LOC_ID = @LocationId
  AND GAS_DAY = @GasDay;
```

**Step 2: Check PDA Configuration**
- Verify PDA header exists and is active
- Verify PDA detail lines have valid method codes and values
- Check effective date coverage
- Verify flow direction matches

**Step 3: Check Measurement Data**
- Verify hourly measurements are loaded
- Check for NULL or zero hours
- Verify aggregate location rollup completed (if applicable)

**Step 4: Review Allocation Processing**
- Check allocation method applied correctly (PRT/PRI/PCT/AMT)
- Verify scheduled quantities are populated
- Check for overrides that may have modified results

**Step 5: Check Configuration and Caches**
- Verify `BulkAssignmentPDACount` is set appropriately
- Verify `ACCTG_MTH_LAG_TIME` for measurement loading
- Clear caches (`AllocationCache`, `LocationCache`, `TspCache`) if configuration changed recently

**Step 6: Review Logs and Errors**
- Check batch process logs for allocation processing errors
- Review validation error messages from `ValidationEnginePDA`
- Check for arithmetic/overflow errors in rollup processing

---

## Performance Issues

### Issue: Slow Daily Allocation Processing

**Symptoms**: Daily allocation takes excessively long to complete.

**Investigation:**
```sql
-- Check number of locations being processed
SELECT COUNT(DISTINCT LOC_ID) AS LocationCount
FROM ALTRAN_PDA_HDR
WHERE TSP_NO = @TspNo
  AND EFF_DATE_FROM <= @GasDay
  AND EFF_DATE_TO >= @GasDay;

-- Check number of PDA detail lines
SELECT COUNT(*) AS DetailLineCount
FROM ALTRAN_PDA_HDR h
INNER JOIN ALTRAN_PDA_DTL d ON h.PDA_HDR_ID = d.PDA_HDR_ID
WHERE h.TSP_NO = @TspNo
  AND h.EFF_DATE_FROM <= @GasDay
  AND h.EFF_DATE_TO >= @GasDay;

-- Check measurement table size
SELECT COUNT(*) AS MeasRowCount
FROM ALCTRL_MEAS_VOL
WHERE TSP_NO = @TspNo
  AND GAS_DAY = @GasDay;
```

**Solutions:**
- Verify `BulkAssignmentPDACount` is tuned correctly for your PDA volume
- Check database indexes on `ALTRAN_PDA_HDR`, `ALTRAN_PDA_DTL`, `ALCTRL_MEAS_VOL`, and `ALCTRL_ALLOC`
- Archive old PDA and measurement records
- Review aggregate location rollup performance (Stage 2: Load Data can be expensive)
- Clear and rebuild caches if they have grown stale or large

### Issue: Aggregate Location Rollup Timeout

**Symptoms**: Rollup process times out for locations with many children.

**Solutions:**
- Check number of child locations per parent (consider splitting very large hierarchies)
- Verify indexes on `ALLOC_PLAN_LOC` and `ALCTRL_MEAS_VOL`
- Consider processing the rollup in smaller batches (by parent location)
- Review `QPTMAllocationServiceExt_AggregateLocation.cs` Stage 2 (Load Data) for query optimization opportunities

---

## Historical Issues Template

Use this template to document recurring or resolved historical issues for future reference.

### Template

```
### [Issue Title]

**Date Identified**: YYYY-MM-DD
**Severity**: Critical / High / Medium / Low
**Environment**: Production / UAT / Dev

**Symptoms:**
- [Description of observable symptoms]

**Root Cause:**
- [Technical root cause description]

**Resolution:**
- [Steps taken to resolve]

**Prevention:**
- [Changes made to prevent recurrence]

**Related Code:**
- [File/class/method references]

**Related Work Items:**
- [Bug/task IDs if applicable]
```

### Historical Issue Categories

**PDA Issues**
- Duplicate PDA headers from data migration
- PDA effective date gaps causing allocation gaps
- PCT method rounding errors in PDA detail lines

**Measurement Issues**
- Late-arriving hourly data after allocation posted
- SCADA feed interruptions causing NULL hours
- Aggregate location rollup overflow with large child count

**Allocation Processing Issues**
- Pro-rata division by zero when total scheduled is zero
- Priority method not respecting H/B/L ordering
- Bulk PDA processing threshold causing unexpected behavior

**Configuration Issues**
- BulkAssignmentPDACount set too low causing bulk processing for small batches
- ACCTG_MTH_LAG_TIME too short, rejecting valid prior-month measurements
- Cache staleness after configuration changes

**Security Issues**
- Users unable to access daily allocation screen (missing DailyAllocatedQuantityMaintenance security)
- BA-to-user linkage missing for PDA submission
- Contact type configuration missing for role

---

## Tips and Best Practices

### Troubleshooting Tips

1. **Check PDA first** -- Most allocation issues trace back to missing, duplicate, or misconfigured PDAs
2. **Verify measurements exist** -- Allocation cannot distribute volumes that have not been measured
3. **Clear caches after config changes** -- Stale AllocationCache or LocationCache is a common culprit
4. **Check flow direction** -- Receipt/Delivery mismatch between PDA and allocation is a frequent issue
5. **Use the diagnostic queries** -- Do not assume root cause; verify with data before making changes
6. **Check effective dates** -- Many "missing data" issues are due to PDA or plan dates not covering the gas day

### Prevention Best Practices

1. **Validate PDAs before submission** -- Use the validation engine to catch issues early
2. **Monitor measurement loads** -- Alert when hourly data has NULL values
3. **Audit aggregate location hierarchies** -- Periodically verify parent-child mappings are correct
4. **Review BulkAssignmentPDACount** -- Tune based on actual PDA volumes in production
5. **Archive old data** -- Keep ALCTRL_MEAS_VOL and ALTRAN_PDA_HDR tables manageable
6. **Document custom configurations** -- Record non-default ACCTG_MTH_LAG_TIME and BulkAssignmentPDACount values

---

## Related Documentation

- **Domain**: [domain.md](./domain.md) - Business concepts and terminology
- **Architecture**: [architecture.md](./architecture.md) - Technical implementation details

---

*Last updated: 2026-03-03*
*Document version: 1.0*
