---
title: Confirmations (CONF) - Troubleshooting Guide
category: troubleshooting
feature: Confirmations (CONF)
related_repos: Web, Batch
keywords: CONF, troubleshooting, issues, errors, diagnostic queries, solutions, debugging, EPSQ, cycle closed, FK validation, path imbalance, unconfirmed, hourly profile, variance
last_updated: 2026-03-03
---

# Confirmations (CONF) - Troubleshooting Guide

## Overview

This document provides troubleshooting guidance for Confirmations (CONF) issues in QPTM. It includes common problems, diagnostic queries, error messages, root cause analysis patterns, and solutions.

For business concepts, see [Domain Documentation](./domain.md).
For technical details, see [Architecture Documentation](./architecture.md).

---

## Table of Contents

1. [Common Issues](#common-issues)
2. [Root Cause Analysis Patterns](#root-cause-analysis-patterns)
3. [Diagnostic SQL Queries](#diagnostic-sql-queries)
4. [Error Messages](#error-messages)
5. [Investigation Workflow](#investigation-workflow)
6. [Performance Issues](#performance-issues)
7. [Historical Work Items](#historical-work-items)

---

## Common Issues

### Issue 1: Cannot Confirm Below EPSQ

**Symptoms:**
- Validation error when entering a confirmation quantity
- Error message indicating quantity is below EPSQ minimum
- Unable to submit confirmation for a specific location

**Root Causes:**
1. EPSQ value configured for the location exceeds the nominated quantity
2. Operator attempting to reduce confirmation below the safety minimum
3. EPSQ values not updated for the current gas day
4. Incorrect EPSQ configuration at the location level

**Investigation Steps:**
```sql
-- Check EPSQ value for the location
SELECT
    LOC.ID_LOC,
    LOC.LOC_NM,
    LOC.EPSQ_QTY
FROM PACTRL_LOC LOC
WHERE LOC.ID_LOC = @LocationId
  AND LOC.TSP_NO = @TspNo;

-- Compare EPSQ to nomination and confirmation quantities
SELECT
    c.CONF_ID,
    c.ID_REC_LOC,
    c.ID_DEL_LOC,
    c.NOM_QTY,
    c.CONF_QTY,
    loc.EPSQ_QTY,
    CASE
        WHEN c.CONF_QTY < loc.EPSQ_QTY THEN 'BELOW EPSQ'
        ELSE 'OK'
    END AS EPSQStatus
FROM CFCTRL_CONF c
LEFT JOIN PACTRL_LOC loc ON c.ID_REC_LOC = loc.ID_LOC AND c.TSP_NO = loc.TSP_NO
WHERE c.TSP_NO = @TspNo
  AND c.GAS_DAY = @GasDay
  AND c.ID_CYCLE = @CycleId;
```

**Solutions:**
- Verify EPSQ value is correctly configured for the location
- If nomination is below EPSQ, confirm at the EPSQ minimum
- Coordinate with operations to adjust EPSQ if it is incorrectly set
- Check if EPSQ should apply for this gas day (seasonal or temporary changes)

---

### Issue 2: Cycle is Closed

**Symptoms:**
- Unable to enter or edit confirmation quantities
- "Cycle is closed" error message displayed
- Confirmation fields are read-only in the UI

**Root Causes:**
1. The confirmation cycle deadline has passed
2. The cycle was manually closed by an administrator
3. The `DefaultToOpenConfirmationCycle` setting is directing the user to a closed cycle
4. User does not have "Edit Closed Cycle" permission

**Investigation Steps:**
```sql
-- Check cycle status
SELECT
    cy.ID_CYCLE,
    cy.CYCLE_NM,
    cy.CYCLE_STAT_CD,
    cy.CYCLE_OPEN_DT,
    cy.CYCLE_CLOSE_DT,
    CASE
        WHEN GETDATE() BETWEEN cy.CYCLE_OPEN_DT AND cy.CYCLE_CLOSE_DT THEN 'OPEN'
        ELSE 'CLOSED'
    END AS CurrentStatus
FROM PACTRL_CYCLE cy
WHERE cy.TSP_NO = @TspNo
  AND cy.GAS_DAY = @GasDay
ORDER BY cy.ID_CYCLE;

-- Check user permissions for Edit Closed Cycle
SELECT *
FROM SYSTBL_USER_SEC_OBJ uso
WHERE uso.sUserID = @UserId
  AND uso.sSecObjCode = 'QVpSOAConfirmationResponse';
```

**Solutions:**
- If the cycle should still be open, check the cycle close date configuration
- If editing a closed cycle is necessary, grant "Edit Closed Cycle" permission to the user
- Use the `GetActions` method to verify if "Edit Closed Cycle" is available
- Check `UseSecObjAllowUserMakeCutOnATTLocation` configuration

---

### Issue 3: FK Validation Failed

**Symptoms:**
- Level 2 (Foreign Key) validation error during confirmation save
- Error message referencing missing or invalid reference data
- Confirmation cannot be saved despite valid quantities

**Root Causes:**
1. Referenced nomination no longer exists or was deleted
2. Location ID is invalid or inactive for the gas day
3. Contract number is invalid or expired
4. Cycle ID does not exist in the cycle configuration table
5. TSP number mismatch between confirmation and reference data

**Investigation Steps:**
```sql
-- Verify nomination exists
SELECT *
FROM NNCTRL_NOM_HDR nh
WHERE nh.TSP_NO = @TspNo
  AND nh.ID_NOM = @NomId
  AND nh.GAS_DAY = @GasDay;

-- Verify location is active
SELECT *
FROM PACTRL_LOC loc
WHERE loc.ID_LOC = @LocationId
  AND loc.TSP_NO = @TspNo
  AND @GasDay BETWEEN loc.EFF_DATE_FROM AND ISNULL(loc.EFF_DATE_TO, '9999-12-31');

-- Verify contract is active
SELECT *
FROM KCTRL_CTR ctr
WHERE ctr.CTR_NO = @ContractNo
  AND ctr.TSP_NO = @TspNo
  AND @GasDay BETWEEN ctr.EFF_DATE_FROM AND ISNULL(ctr.EFF_DATE_TO, '9999-12-31');

-- Verify cycle exists
SELECT *
FROM PACTRL_CYCLE cy
WHERE cy.ID_CYCLE = @CycleId
  AND cy.TSP_NO = @TspNo;
```

**Solutions:**
- Verify all referenced entities exist and are active for the gas day
- Check nomination status (may have been withdrawn or superseded)
- Verify location effective dates encompass the gas day
- Check contract effective dates and status
- Ensure cycle ID is valid for the TSP

---

### Issue 4: Path Imbalance Detected

**Symptoms:**
- Validation warning or error about unbalanced path
- Confirmation submission blocked due to path imbalance
- Receipt and delivery totals do not match for a nomination path

**Root Causes:**
1. Confirmed receipt quantity does not equal confirmed delivery quantity for a path
2. Partial confirmation on one side of the path (receipt confirmed, delivery not)
3. Different reduction amounts applied to receipt and delivery locations
4. Fuel quantity not properly accounted for in path balancing
5. `ConfRunPathBalForPnt` configuration not aligned with business requirements

**Investigation Steps:**
```sql
-- Check path balance for a gas day/cycle
SELECT
    c.ID_NOM,
    c.GAS_DAY,
    c.ID_CYCLE,
    SUM(CASE WHEN c.ID_REC_LOC IS NOT NULL THEN c.CONF_QTY ELSE 0 END) AS TotalRecConf,
    SUM(CASE WHEN c.ID_DEL_LOC IS NOT NULL THEN c.CONF_QTY ELSE 0 END) AS TotalDelConf,
    SUM(CASE WHEN c.ID_REC_LOC IS NOT NULL THEN c.CONF_QTY ELSE 0 END) -
    SUM(CASE WHEN c.ID_DEL_LOC IS NOT NULL THEN c.CONF_QTY ELSE 0 END) AS Imbalance
FROM CFCTRL_CONF c
WHERE c.TSP_NO = @TspNo
  AND c.GAS_DAY = @GasDay
  AND c.ID_CYCLE = @CycleId
GROUP BY c.ID_NOM, c.GAS_DAY, c.ID_CYCLE
HAVING ABS(
    SUM(CASE WHEN c.ID_REC_LOC IS NOT NULL THEN c.CONF_QTY ELSE 0 END) -
    SUM(CASE WHEN c.ID_DEL_LOC IS NOT NULL THEN c.CONF_QTY ELSE 0 END)
) > 0.01
ORDER BY ABS(
    SUM(CASE WHEN c.ID_REC_LOC IS NOT NULL THEN c.CONF_QTY ELSE 0 END) -
    SUM(CASE WHEN c.ID_DEL_LOC IS NOT NULL THEN c.CONF_QTY ELSE 0 END)
) DESC;
```

**Solutions:**
- Adjust receipt and/or delivery confirmations to balance the path
- Verify fuel quantities are correctly factored into balancing calculation
- Check `ConfRunPathBalForPnt` configuration for the TSP
- If path balancing is incorrectly blocking, review `ConfUpdCallBalancingAfter` timing
- Coordinate with multiple shippers if the path spans multiple nominations

---

### Issue 5: User Not Associated with TSP

**Symptoms:**
- User cannot access confirmation screens
- "Access denied" or "User not associated with TSP" error
- Confirmation data loads but user cannot make changes

**Root Causes:**
1. User account not linked to the TSP in security configuration
2. User missing `QVpSOAConfirmationResponse` security object
3. User missing `ConfirmationSummary` security object for summary view
4. Business party access not configured for the user

**Investigation Steps:**
```sql
-- Check user-TSP association
SELECT *
FROM SYSTBL_USER_BP_ACCESS uba
WHERE uba.sUserID = @UserId
  AND uba.nTspNo = @TspNo;

-- Check security object permissions
SELECT *
FROM SYSTBL_USER_SEC_OBJ uso
WHERE uso.sUserID = @UserId
  AND uso.sSecObjCode IN ('QVpSOAConfirmationResponse', 'ConfirmationSummary');

-- Check user role assignments
SELECT
    ur.sUserID,
    ur.sRoleCode,
    rso.sSecObjCode
FROM SYSTBL_USER_ROLE ur
INNER JOIN SYSTBL_ROLE_SEC_OBJ rso ON ur.sRoleCode = rso.sRoleCode
WHERE ur.sUserID = @UserId
  AND rso.sSecObjCode IN ('QVpSOAConfirmationResponse', 'ConfirmationSummary');
```

**Solutions:**
- Add user-TSP association in SYSTBL_USER_BP_ACCESS
- Grant `QVpSOAConfirmationResponse` security object for confirmation entry
- Grant `ConfirmationSummary` security object for summary view access
- Assign appropriate role that includes confirmation security objects
- Verify QOperationContext.Current.SecurityUser is populated correctly

---

### Issue 6: No Open Cycle Found

**Symptoms:**
- Confirmation screen loads with no data
- "No open cycle found" message or empty cycle dropdown
- `DefaultToOpenConfirmationCycle` not finding any cycle

**Root Causes:**
1. All cycles for the gas day are closed
2. Cycle open/close dates not configured for the gas day
3. Cycle configuration missing for the TSP
4. Gas day is too far in the past or future

**Investigation Steps:**
```sql
-- Find all cycles and their status for the gas day
SELECT
    cy.ID_CYCLE,
    cy.CYCLE_NM,
    cy.CYCLE_STAT_CD,
    cy.CYCLE_OPEN_DT,
    cy.CYCLE_CLOSE_DT,
    CASE
        WHEN cy.CYCLE_STAT_CD = 'O' THEN 'OPEN'
        WHEN cy.CYCLE_STAT_CD = 'C' THEN 'CLOSED'
        ELSE cy.CYCLE_STAT_CD
    END AS StatusDesc,
    CASE
        WHEN GETDATE() BETWEEN cy.CYCLE_OPEN_DT AND cy.CYCLE_CLOSE_DT THEN 'WITHIN WINDOW'
        WHEN GETDATE() < cy.CYCLE_OPEN_DT THEN 'NOT YET OPEN'
        ELSE 'PAST DEADLINE'
    END AS TimeStatus
FROM PACTRL_CYCLE cy
WHERE cy.TSP_NO = @TspNo
  AND cy.GAS_DAY = @GasDay
ORDER BY cy.ID_CYCLE;

-- Check DefaultToOpenConfirmationCycle config
SELECT *
FROM SYSTBL_CONFIG
WHERE sConfigKey = 'DefaultToOpenConfirmationCycle'
  AND nTspNo = @TspNo;
```

**Solutions:**
- Verify cycle configuration exists for the TSP and gas day
- Check cycle open/close date windows
- If all cycles are legitimately closed, use "Edit Closed Cycle" functionality
- Verify `DefaultToOpenConfirmationCycle` configuration value
- Ensure gas day is within the valid operational range

---

### Issue 7: Hourly Profile Mismatch

**Symptoms:**
- Validation error when saving hourly profile
- "Hourly profile total does not match daily quantity" error
- Hourly values saved but confirmation shows incorrect daily total

**Root Causes:**
1. Sum of 24 hourly values does not equal the daily confirmed quantity
2. Rounding errors in hourly distribution calculation
3. Daily total was changed after hourly values were entered
4. `UpdateHourlyProfileTotal` not called after quantity change
5. Negative hourly values entered

**Investigation Steps:**
```sql
-- Check hourly profile totals vs daily quantity
SELECT
    c.CONF_ID,
    c.CONF_QTY AS DailyTotal,
    h.HR_01 + h.HR_02 + h.HR_03 + h.HR_04 + h.HR_05 + h.HR_06 +
    h.HR_07 + h.HR_08 + h.HR_09 + h.HR_10 + h.HR_11 + h.HR_12 +
    h.HR_13 + h.HR_14 + h.HR_15 + h.HR_16 + h.HR_17 + h.HR_18 +
    h.HR_19 + h.HR_20 + h.HR_21 + h.HR_22 + h.HR_23 + h.HR_24 AS HourlySum,
    c.CONF_QTY - (
        h.HR_01 + h.HR_02 + h.HR_03 + h.HR_04 + h.HR_05 + h.HR_06 +
        h.HR_07 + h.HR_08 + h.HR_09 + h.HR_10 + h.HR_11 + h.HR_12 +
        h.HR_13 + h.HR_14 + h.HR_15 + h.HR_16 + h.HR_17 + h.HR_18 +
        h.HR_19 + h.HR_20 + h.HR_21 + h.HR_22 + h.HR_23 + h.HR_24
    ) AS Discrepancy
FROM CFCTRL_CONF c
INNER JOIN CFCTRL_CONF_HOURLY h ON c.TSP_NO = h.TSP_NO AND c.CONF_ID = h.CONF_ID
WHERE c.TSP_NO = @TspNo
  AND c.GAS_DAY = @GasDay
  AND c.ID_CYCLE = @CycleId
  AND c.IS_HR_PROF = 1
  AND ABS(c.CONF_QTY - (
        h.HR_01 + h.HR_02 + h.HR_03 + h.HR_04 + h.HR_05 + h.HR_06 +
        h.HR_07 + h.HR_08 + h.HR_09 + h.HR_10 + h.HR_11 + h.HR_12 +
        h.HR_13 + h.HR_14 + h.HR_15 + h.HR_16 + h.HR_17 + h.HR_18 +
        h.HR_19 + h.HR_20 + h.HR_21 + h.HR_22 + h.HR_23 + h.HR_24
  )) > 0.01;

-- Check for negative hourly values
SELECT
    c.CONF_ID,
    h.*
FROM CFCTRL_CONF c
INNER JOIN CFCTRL_CONF_HOURLY h ON c.TSP_NO = h.TSP_NO AND c.CONF_ID = h.CONF_ID
WHERE c.TSP_NO = @TspNo
  AND c.GAS_DAY = @GasDay
  AND c.ID_CYCLE = @CycleId
  AND (h.HR_01 < 0 OR h.HR_02 < 0 OR h.HR_03 < 0 OR h.HR_04 < 0
    OR h.HR_05 < 0 OR h.HR_06 < 0 OR h.HR_07 < 0 OR h.HR_08 < 0
    OR h.HR_09 < 0 OR h.HR_10 < 0 OR h.HR_11 < 0 OR h.HR_12 < 0
    OR h.HR_13 < 0 OR h.HR_14 < 0 OR h.HR_15 < 0 OR h.HR_16 < 0
    OR h.HR_17 < 0 OR h.HR_18 < 0 OR h.HR_19 < 0 OR h.HR_20 < 0
    OR h.HR_21 < 0 OR h.HR_22 < 0 OR h.HR_23 < 0 OR h.HR_24 < 0);
```

**Solutions:**
- Recalculate hourly values to match the daily total
- Call `UpdateHourlyProfileTotal` after changing the daily confirmed quantity
- Check for rounding errors (use consistent decimal precision)
- Ensure no negative hourly values exist
- If discrepancy is due to rounding, distribute the remainder to the last hour

---

### Issue 8: Data Disappears After Submit

**Symptoms:**
- Confirmation data visible before submission but disappears after
- Confirmation summary shows zero or missing records after submit
- CFPROCESS batch completes but data is not visible

**Root Causes:**
1. CFPROCESS batch process encountered errors and rolled back
2. Confirmation status changed to a value excluded by default filters
3. Cycle filter changed after submission (e.g., NextOpenCycle moved to next cycle)
4. Data moved from staging to a different table during processing
5. Summary query filters exclude submitted data

**Investigation Steps:**
```sql
-- Check if confirmation records still exist in CFCTRL_CONF
SELECT
    c.CONF_ID,
    c.GAS_DAY,
    c.ID_CYCLE,
    c.CONF_QTY,
    c.CONF_STAT_CD,
    c.UPDT_DT,
    c.UPDT_USER_ID
FROM CFCTRL_CONF c
WHERE c.TSP_NO = @TspNo
  AND c.GAS_DAY = @GasDay
  AND c.ID_CYCLE = @CycleId
ORDER BY c.UPDT_DT DESC;

-- Check CFPROCESS batch status
SELECT *
FROM tProcessQueue
WHERE sProcessCode = 'CFPROCESS'
  AND dProcessDate >= DATEADD(day, -1, GETDATE())
ORDER BY dProcessDate DESC;

-- Check CFPROCESS error messages
SELECT
    m.nMessageID,
    m.sProcessCode,
    m.dMessageDate,
    m.sMessage,
    m.sStackTrace
FROM tMessage m
WHERE m.sProcessCode = 'CFPROCESS'
  AND m.dMessageDate >= DATEADD(day, -1, GETDATE())
  AND m.nMessageType = 1  -- Errors
ORDER BY m.dMessageDate DESC;

-- Check confirmation status codes
SELECT DISTINCT
    c.CONF_STAT_CD,
    COUNT(*) AS RecordCount
FROM CFCTRL_CONF c
WHERE c.TSP_NO = @TspNo
  AND c.GAS_DAY = @GasDay
GROUP BY c.CONF_STAT_CD;
```

**Solutions:**
- Check CFPROCESS batch process for errors and re-run if needed
- Verify the confirmation status code filter in the summary query
- Adjust the cycle filter (try "PreviousDayCycle" or select cycle manually)
- Check if data was moved to a different cycle during processing
- Verify summary query parameters match the submitted data

---

### Issue 9: Wrong Quantities Shown

**Symptoms:**
- Confirmation grid shows incorrect NomQty, SchdQty, or ConfQty values
- Quantities do not match what was entered or expected
- Different values shown in summary vs detail views

**Root Causes:**
1. Stale data in the UI (cache not refreshed)
2. Latest cycle filter not applied correctly (showing old cycle data)
3. Multiple confirmations for the same nomination (duplicate records)
4. Summary aggregation including unintended records
5. NomQty or SchdQty not updated from latest nomination/CAS cycle
6. Unit of measure mismatch

**Investigation Steps:**
```sql
-- Check for duplicate confirmation records
SELECT
    c.ID_NOM,
    c.GAS_DAY,
    c.ID_CYCLE,
    COUNT(*) AS ConfCount
FROM CFCTRL_CONF c
WHERE c.TSP_NO = @TspNo
  AND c.GAS_DAY = @GasDay
  AND c.ID_CYCLE = @CycleId
GROUP BY c.ID_NOM, c.GAS_DAY, c.ID_CYCLE
HAVING COUNT(*) > 1;

-- Compare confirmation to source nomination and CAS data
SELECT
    c.CONF_ID,
    c.ID_NOM,
    c.NOM_QTY AS ConfNomQty,
    nh.NOM_QTY AS ActualNomQty,
    c.SCHD_QTY AS ConfSchdQty,
    cs.REC_SCHED_QTY AS CASSchdQty,
    c.CONF_QTY,
    c.ID_CYCLE
FROM CFCTRL_CONF c
LEFT JOIN NNCTRL_NOM_HDR nh ON c.TSP_NO = nh.TSP_NO AND c.ID_NOM = nh.ID_NOM AND c.GAS_DAY = nh.GAS_DAY
LEFT JOIN CACTRL_SUMMARY cs ON c.TSP_NO = cs.TSP_NO AND c.GAS_DAY = cs.GAS_DAY AND c.ID_CYCLE = cs.ID_CYCLE
WHERE c.TSP_NO = @TspNo
  AND c.GAS_DAY = @GasDay
  AND c.ID_CYCLE = @CycleId
  AND c.ID_NOM = @NomId;

-- Check if ApplyNomLatestCycleFilter is working correctly
SELECT
    c.ID_NOM,
    c.ID_CYCLE,
    c.CONF_QTY,
    c.UPDT_DT,
    ROW_NUMBER() OVER (PARTITION BY c.ID_NOM ORDER BY c.ID_CYCLE DESC) AS CycleRank
FROM CFCTRL_CONF c
WHERE c.TSP_NO = @TspNo
  AND c.GAS_DAY = @GasDay
  AND c.ID_NOM = @NomId
ORDER BY c.ID_CYCLE DESC;
```

**Solutions:**
- Refresh the UI to clear any cached data
- Verify `ApplyNomLatestCycleFilter` is selecting the correct cycle
- Remove duplicate confirmation records if found
- Verify NomQty and SchdQty reference values are current
- Check summary aggregation logic for the selected view (ByLocation/ByShipper/ByPath)
- Ensure unit of measure is consistent across all data sources

---

### Issue 10: Validation Always Fails

**Symptoms:**
- Every confirmation attempt fails validation
- Validation errors are generic or unclear
- The issue affects all users for the TSP/gas day

**Root Causes:**
1. System configuration is missing or invalid for the TSP
2. Validation engine has a systemic error (not data-specific)
3. Required reference data is missing (cycle config, location config)
4. Security configuration is globally misconfigured
5. Database connection or timeout issues causing validation to fail

**Investigation Steps:**
```sql
-- Check TSP configuration
SELECT *
FROM SYSTBL_CONFIG
WHERE nTspNo = @TspNo
  AND sConfigKey LIKE '%Conf%';

-- Check for missing required reference data
SELECT
    'Cycles' AS DataType,
    COUNT(*) AS RecordCount
FROM PACTRL_CYCLE
WHERE TSP_NO = @TspNo AND GAS_DAY = @GasDay
UNION ALL
SELECT
    'Locations' AS DataType,
    COUNT(*) AS RecordCount
FROM PACTRL_LOC
WHERE TSP_NO = @TspNo AND @GasDay BETWEEN EFF_DATE_FROM AND ISNULL(EFF_DATE_TO, '9999-12-31')
UNION ALL
SELECT
    'Contracts' AS DataType,
    COUNT(*) AS RecordCount
FROM KCTRL_CTR
WHERE TSP_NO = @TspNo AND @GasDay BETWEEN EFF_DATE_FROM AND ISNULL(EFF_DATE_TO, '9999-12-31');

-- Check validation error log
SELECT TOP 20 *
FROM tMessage m
WHERE m.sProcessCode LIKE '%CONF%'
  AND m.dMessageDate >= DATEADD(day, -1, GETDATE())
ORDER BY m.dMessageDate DESC;
```

**Solutions:**
- Verify all TSP configuration settings are present and valid
- Check that cycle, location, and contract reference data exists for the gas day
- Review validation error messages for specific failure details
- Test with a different user to rule out user-specific security issues
- Check database connectivity and query timeouts
- Review ValidationEngineConfirmation implementation for recent code changes

---

## Root Cause Analysis Patterns

### Pattern 1: Confirmation Not Appearing in Grid

**Description**: A confirmation that was entered or expected does not appear in the confirmation grid.

**Analysis Checklist:**
1. **Cycle Filter**: Is the cycle filter set to the correct cycle? Check if `NextOpenCycle` has moved past the target cycle.
2. **Confirmation Status**: Has the confirmation status changed to a value that is filtered out?
3. **Latest Cycle Filter**: Is `ApplyNomLatestCycleFilter` excluding the record because a newer cycle exists?
4. **Nomination Status**: Was the underlying nomination withdrawn, rejected, or superseded?
5. **TSP/Gas Day**: Are the TSP number and gas day parameters correct?

**Diagnostic Query:**
```sql
-- Find confirmation regardless of filters
SELECT
    c.CONF_ID,
    c.ID_NOM,
    c.GAS_DAY,
    c.ID_CYCLE,
    c.CONF_QTY,
    c.CONF_STAT_CD,
    c.UPDT_DT,
    nh.NOM_STAT_CD AS NomStatus
FROM CFCTRL_CONF c
LEFT JOIN NNCTRL_NOM_HDR nh ON c.TSP_NO = nh.TSP_NO AND c.ID_NOM = nh.ID_NOM AND c.GAS_DAY = nh.GAS_DAY
WHERE c.TSP_NO = @TspNo
  AND c.GAS_DAY = @GasDay
  AND c.ID_NOM = @NomId
ORDER BY c.ID_CYCLE DESC;
```

### Pattern 2: Data Disappears After Submit

**Description**: Confirmation data is visible before submission but disappears or appears to be lost after the submit action.

**Analysis Checklist:**
1. **CFPROCESS Batch**: Did the CFPROCESS batch complete successfully? Check tProcessQueue and tMessage.
2. **Status Transition**: Did the confirmation status change to a value excluded by default filters?
3. **Cycle Advancement**: Did the UI advance to the next open cycle after submission, hiding the just-submitted data?
4. **Rollback**: Did a database error cause the transaction to roll back?
5. **Summary vs Detail**: Is the data visible in direct SQL query but not in the UI summary?

**Diagnostic Query:**
```sql
-- Check if data exists and what happened during processing
SELECT
    c.CONF_ID,
    c.CONF_STAT_CD,
    c.UPDT_DT,
    c.UPDT_USER_ID,
    pq.nProcessStatus AS BatchStatus,
    pq.dProcessDate AS BatchRunDate
FROM CFCTRL_CONF c
LEFT JOIN tProcessQueue pq ON pq.sProcessCode = 'CFPROCESS'
    AND pq.dProcessDate >= DATEADD(hour, -1, c.UPDT_DT)
WHERE c.TSP_NO = @TspNo
  AND c.GAS_DAY = @GasDay
  AND c.ID_CYCLE = @CycleId
ORDER BY c.UPDT_DT DESC;
```

### Pattern 3: Wrong Quantities Shown

**Description**: The quantities displayed in the confirmation grid do not match expected values.

**Analysis Checklist:**
1. **Source Data**: Are NomQty and SchdQty reference values current from nominations and CAS?
2. **Cycle Mismatch**: Is the confirmation showing data from a different cycle than expected?
3. **Duplicates**: Are there duplicate confirmation records inflating totals?
4. **Aggregation**: Is the summary view double-counting or missing records?
5. **Cache**: Is the UI displaying stale cached data?
6. **UOM**: Is there a unit of measure mismatch?

**Diagnostic Query:**
```sql
-- Full data comparison across all sources
SELECT
    'Nomination' AS Source,
    nh.ID_NOM,
    nh.NOM_QTY,
    nh.ID_CYCLE AS SourceCycle
FROM NNCTRL_NOM_HDR nh
WHERE nh.TSP_NO = @TspNo AND nh.GAS_DAY = @GasDay AND nh.ID_NOM = @NomId

UNION ALL

SELECT
    'CAS Schedule' AS Source,
    @NomId AS ID_NOM,
    cs.REC_SCHED_QTY AS Qty,
    cs.ID_CYCLE
FROM CACTRL_SUMMARY cs
WHERE cs.TSP_NO = @TspNo AND cs.GAS_DAY = @GasDay AND cs.ID_CYCLE = @CycleId

UNION ALL

SELECT
    'Confirmation' AS Source,
    c.ID_NOM,
    c.CONF_QTY,
    c.ID_CYCLE
FROM CFCTRL_CONF c
WHERE c.TSP_NO = @TspNo AND c.GAS_DAY = @GasDay AND c.ID_NOM = @NomId
ORDER BY Source, SourceCycle;
```

---

## Diagnostic SQL Queries

### Query 1: Unconfirmed Nominations

**Purpose**: Find all nominations that do not have a corresponding confirmation record for a gas day/cycle.

```sql
SELECT
    nh.TSP_NO,
    nh.GAS_DAY,
    nh.ID_NOM,
    nh.ID_CYCLE,
    nh.NOM_QTY,
    nh.SR_BP_NO,
    nh.SR_CTR_NO,
    nh.ID_REC_LOC,
    nh.ID_DEL_LOC,
    nh.TOS_CD,
    nh.NOM_STAT_CD
FROM NNCTRL_NOM_HDR nh
LEFT JOIN CFCTRL_CONF c ON
    nh.TSP_NO = c.TSP_NO
    AND nh.ID_NOM = c.ID_NOM
    AND nh.GAS_DAY = c.GAS_DAY
    AND nh.ID_CYCLE = c.ID_CYCLE
WHERE nh.TSP_NO = @TspNo
  AND nh.GAS_DAY = @GasDay
  AND nh.ID_CYCLE = @CycleId
  AND c.CONF_ID IS NULL
ORDER BY nh.ID_NOM;
```

### Query 2: Path Imbalances

**Purpose**: Identify all paths with receipt/delivery imbalances in confirmations.

```sql
SELECT
    c.ID_NOM,
    c.GAS_DAY,
    c.ID_CYCLE,
    SUM(CASE WHEN c.ID_REC_LOC IS NOT NULL THEN c.CONF_QTY ELSE 0 END) AS TotalRecConf,
    SUM(CASE WHEN c.ID_DEL_LOC IS NOT NULL THEN c.CONF_QTY ELSE 0 END) AS TotalDelConf,
    SUM(CASE WHEN c.ID_REC_LOC IS NOT NULL THEN c.CONF_QTY ELSE 0 END) -
    SUM(CASE WHEN c.ID_DEL_LOC IS NOT NULL THEN c.CONF_QTY ELSE 0 END) AS Imbalance,
    CASE
        WHEN ABS(SUM(CASE WHEN c.ID_REC_LOC IS NOT NULL THEN c.CONF_QTY ELSE 0 END) -
             SUM(CASE WHEN c.ID_DEL_LOC IS NOT NULL THEN c.CONF_QTY ELSE 0 END)) > 0.01
        THEN 'UNBALANCED'
        ELSE 'BALANCED'
    END AS BalanceStatus
FROM CFCTRL_CONF c
WHERE c.TSP_NO = @TspNo
  AND c.GAS_DAY = @GasDay
  AND c.ID_CYCLE = @CycleId
GROUP BY c.ID_NOM, c.GAS_DAY, c.ID_CYCLE
ORDER BY ABS(
    SUM(CASE WHEN c.ID_REC_LOC IS NOT NULL THEN c.CONF_QTY ELSE 0 END) -
    SUM(CASE WHEN c.ID_DEL_LOC IS NOT NULL THEN c.CONF_QTY ELSE 0 END)
) DESC;
```

### Query 3: Confirmation Levels Overview

**Purpose**: View confirmation level hierarchy and aggregated quantities.

```sql
SELECT
    lvl.TSP_NO,
    lvl.GAS_DAY,
    lvl.ID_CYCLE,
    lvl.CONF_LVL_ID,
    lvl.CONF_LVL_TYPE,
    lvl.PARENT_LVL_ID,
    lvl.AGG_CONF_QTY,
    lvl.AGG_NOM_QTY,
    lvl.AGG_CONF_QTY - lvl.AGG_NOM_QTY AS LevelVariance,
    COUNT(dtl.CONF_ID) AS DetailCount
FROM CFCTRL_CONF_LVL lvl
LEFT JOIN CFCTRL_CONF_LVL_DTL dtl ON
    lvl.TSP_NO = dtl.TSP_NO
    AND lvl.CONF_LVL_ID = dtl.CONF_LVL_ID
WHERE lvl.TSP_NO = @TspNo
  AND lvl.GAS_DAY = @GasDay
  AND lvl.ID_CYCLE = @CycleId
GROUP BY lvl.TSP_NO, lvl.GAS_DAY, lvl.ID_CYCLE,
    lvl.CONF_LVL_ID, lvl.CONF_LVL_TYPE, lvl.PARENT_LVL_ID,
    lvl.AGG_CONF_QTY, lvl.AGG_NOM_QTY
ORDER BY lvl.CONF_LVL_ID;
```

### Query 4: Cycle Status and Deadlines

**Purpose**: View all cycle statuses and deadlines for a gas day.

```sql
SELECT
    cy.TSP_NO,
    cy.GAS_DAY,
    cy.ID_CYCLE,
    cy.CYCLE_NM,
    cy.CYCLE_STAT_CD,
    cy.CYCLE_OPEN_DT,
    cy.CYCLE_CLOSE_DT,
    CASE
        WHEN cy.CYCLE_STAT_CD = 'O' THEN 'OPEN'
        WHEN cy.CYCLE_STAT_CD = 'C' THEN 'CLOSED'
        ELSE cy.CYCLE_STAT_CD
    END AS StatusDesc,
    CASE
        WHEN GETDATE() < cy.CYCLE_OPEN_DT THEN 'NOT YET OPEN'
        WHEN GETDATE() BETWEEN cy.CYCLE_OPEN_DT AND cy.CYCLE_CLOSE_DT THEN 'WITHIN WINDOW'
        ELSE 'PAST DEADLINE'
    END AS TimeStatus,
    (SELECT COUNT(*) FROM CFCTRL_CONF c
     WHERE c.TSP_NO = cy.TSP_NO AND c.GAS_DAY = cy.GAS_DAY AND c.ID_CYCLE = cy.ID_CYCLE
    ) AS ConfirmationCount
FROM PACTRL_CYCLE cy
WHERE cy.TSP_NO = @TspNo
  AND cy.GAS_DAY = @GasDay
ORDER BY cy.ID_CYCLE;
```

### Query 5: EPSQ Values for Locations

**Purpose**: List EPSQ values for all active locations for a gas day.

```sql
SELECT
    loc.TSP_NO,
    loc.ID_LOC,
    loc.LOC_NM,
    loc.EPSQ_QTY,
    loc.EFF_DATE_FROM,
    loc.EFF_DATE_TO,
    (SELECT COUNT(*) FROM CFCTRL_CONF c
     WHERE c.TSP_NO = loc.TSP_NO
       AND (c.ID_REC_LOC = loc.ID_LOC OR c.ID_DEL_LOC = loc.ID_LOC)
       AND c.GAS_DAY = @GasDay
       AND c.CONF_QTY < loc.EPSQ_QTY
    ) AS BelowEPSQCount
FROM PACTRL_LOC loc
WHERE loc.TSP_NO = @TspNo
  AND loc.EPSQ_QTY > 0
  AND @GasDay BETWEEN loc.EFF_DATE_FROM AND ISNULL(loc.EFF_DATE_TO, '9999-12-31')
ORDER BY loc.LOC_NM;
```

### Query 6: Hourly Profile Issues

**Purpose**: Find confirmations with hourly profile mismatches or issues.

```sql
SELECT
    c.CONF_ID,
    c.ID_NOM,
    c.GAS_DAY,
    c.ID_CYCLE,
    c.CONF_QTY AS DailyTotal,
    c.IS_HR_PROF,
    h.HR_01 + h.HR_02 + h.HR_03 + h.HR_04 + h.HR_05 + h.HR_06 +
    h.HR_07 + h.HR_08 + h.HR_09 + h.HR_10 + h.HR_11 + h.HR_12 +
    h.HR_13 + h.HR_14 + h.HR_15 + h.HR_16 + h.HR_17 + h.HR_18 +
    h.HR_19 + h.HR_20 + h.HR_21 + h.HR_22 + h.HR_23 + h.HR_24 AS HourlySum,
    ABS(c.CONF_QTY - (
        h.HR_01 + h.HR_02 + h.HR_03 + h.HR_04 + h.HR_05 + h.HR_06 +
        h.HR_07 + h.HR_08 + h.HR_09 + h.HR_10 + h.HR_11 + h.HR_12 +
        h.HR_13 + h.HR_14 + h.HR_15 + h.HR_16 + h.HR_17 + h.HR_18 +
        h.HR_19 + h.HR_20 + h.HR_21 + h.HR_22 + h.HR_23 + h.HR_24
    )) AS Discrepancy,
    CASE
        WHEN h.CONF_ID IS NULL AND c.IS_HR_PROF = 1 THEN 'MISSING HOURLY RECORD'
        WHEN ABS(c.CONF_QTY - (
            h.HR_01 + h.HR_02 + h.HR_03 + h.HR_04 + h.HR_05 + h.HR_06 +
            h.HR_07 + h.HR_08 + h.HR_09 + h.HR_10 + h.HR_11 + h.HR_12 +
            h.HR_13 + h.HR_14 + h.HR_15 + h.HR_16 + h.HR_17 + h.HR_18 +
            h.HR_19 + h.HR_20 + h.HR_21 + h.HR_22 + h.HR_23 + h.HR_24
        )) > 0.01 THEN 'TOTAL MISMATCH'
        ELSE 'OK'
    END AS ProfileStatus
FROM CFCTRL_CONF c
LEFT JOIN CFCTRL_CONF_HOURLY h ON c.TSP_NO = h.TSP_NO AND c.CONF_ID = h.CONF_ID
WHERE c.TSP_NO = @TspNo
  AND c.GAS_DAY = @GasDay
  AND c.ID_CYCLE = @CycleId
  AND c.IS_HR_PROF = 1
ORDER BY c.CONF_ID;
```

---

## Error Messages

### Error: "Confirmation quantity cannot be below EPSQ"

**Cause**: ValidationEngineConfirmation Level 4 (Business) detected ConfQty < EPSQ for the location.

**Solution**: Increase ConfQty to at least the EPSQ value, or verify EPSQ configuration is correct for the location.

### Error: "Cycle is closed for confirmation entry"

**Cause**: ValidationEngineConfirmation Level 1 (Security) detected the cycle is closed.

**Solution**: Use "Edit Closed Cycle" action if permitted, or switch to an open cycle.

### Error: "Foreign key validation failed"

**Cause**: ValidationEngineConfirmation Level 2 (FK) detected an invalid reference.

**Solution**: Run the FK diagnostic queries above to identify the missing reference entity.

### Error: "Reduction reason is required"

**Cause**: ValidationEngineConfirmation Level 3 (Line) detected ConfQty < NomQty without a ReductRsnCode.

**Solution**: Set the ReductRsnCode field to indicate why the nomination was reduced.

### Error: "Hourly profile total does not match daily quantity"

**Cause**: ValidationEngineConfirmation Level 3 (Line) detected hourly sum != ConfQty.

**Solution**: Recalculate hourly values or call UpdateHourlyProfileTotal to redistribute.

### Error: "Path imbalance detected"

**Cause**: ValidationEngineConfirmation Level 4 (Business) detected receipts != deliveries on a path.

**Solution**: Adjust receipt and/or delivery confirmations to balance. Check ConfRunPathBalForPnt setting.

---

## Investigation Workflow

### Step-by-Step Investigation Process

**Step 1: Identify the Scope**
- Which TSP, gas day, and cycle is affected?
- Is the issue user-specific or system-wide?
- Is the issue data-specific or configuration-related?

**Step 2: Check Configuration**
```sql
-- Check all confirmation-related configuration
SELECT *
FROM SYSTBL_CONFIG
WHERE nTspNo = @TspNo
  AND (sConfigKey LIKE '%Conf%' OR sConfigKey LIKE '%EPSQ%' OR sConfigKey LIKE '%PathBal%');
```

**Step 3: Verify Data Exists**
```sql
-- Check nomination, CAS, and confirmation data
SELECT 'Nominations' AS DataType, COUNT(*) AS Cnt
FROM NNCTRL_NOM_HDR WHERE TSP_NO = @TspNo AND GAS_DAY = @GasDay AND ID_CYCLE <= @CycleId
UNION ALL
SELECT 'CAS Summary', COUNT(*)
FROM CACTRL_SUMMARY WHERE TSP_NO = @TspNo AND GAS_DAY = @GasDay AND ID_CYCLE = @CycleId
UNION ALL
SELECT 'Confirmations', COUNT(*)
FROM CFCTRL_CONF WHERE TSP_NO = @TspNo AND GAS_DAY = @GasDay AND ID_CYCLE = @CycleId;
```

**Step 4: Review Batch Process Logs**
- Check `tProcessQueue` for CFPROCESS execution
- Check `tMessage` for errors with process code CFPROCESS
- Review batch parameters for the failed run

**Step 5: Review Validation Errors**
- Check the browser network tab for API error responses
- Review server-side validation error messages
- Identify which validation level (1-4) is failing

**Step 6: Run Diagnostic Queries**
- Use the appropriate diagnostic query from the section above
- Compare data across nominations, CAS, and confirmations
- Check for data integrity issues (duplicates, orphans, mismatches)

---

## Performance Issues

### Issue: Slow Confirmation Summary Loading

**Symptoms**: Confirmation Summary screen takes a long time to load data.

**Investigation:**
```sql
-- Check confirmation table size
SELECT
    OBJECT_NAME(i.object_id) AS TableName,
    SUM(p.rows) AS RowCount
FROM sys.indexes i
INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
WHERE OBJECT_NAME(i.object_id) IN ('CFCTRL_CONF', 'CFCTRL_CONF_HOURLY', 'CFCTRL_CONF_LVL')
GROUP BY OBJECT_NAME(i.object_id);

-- Check for missing indexes on CFCTRL_CONF
EXEC sp_helpindex 'CFCTRL_CONF';
```

**Solutions:**
- Ensure indexes exist on TSP_NO, GAS_DAY, ID_CYCLE columns
- Archive old confirmation data
- Optimize GetSummaryConfirmations query
- Review Kendo DataSource paging configuration (server-side paging recommended)

### Issue: Batch Process Timeout

**Symptoms**: CFPROCESS takes too long and times out.

**Solutions:**
- Increase CFPROCESS timeout setting
- Process fewer records per batch run
- Check for database blocking during batch execution
- Optimize CFPROCESS stored procedures

---

## Historical Work Items

### Work Item Categories

This section documents known historical issue categories related to Confirmations. Use this as a reference when investigating similar issues.

**EPSQ Issues**
- EPSQ values not loaded for new locations
- Seasonal EPSQ changes not applied on correct date
- EPSQ validation bypass for emergency situations

**Cycle Management Issues**
- Cycle open/close times not synchronized with NAESB deadlines
- Edit Closed Cycle permission not properly inherited from roles
- Default cycle selection pointing to incorrect cycle

**Path Balancing Issues**
- Path balance calculation not accounting for fuel
- Balancing triggered at incorrect time (before all confirmations entered)
- Cross-path balancing affecting unrelated nominations

**Hourly Profile Issues**
- Rounding errors accumulating across 24 hours
- Hourly profile not cleared when daily total set to zero
- UpdateHourlyProfileTotal not called during batch processing

**Data Integrity Issues**
- Orphaned hourly records without parent confirmation
- Duplicate confirmation records for same nomination/cycle
- Stale NomQty/SchdQty references after nomination updates

---

## Tips and Best Practices

### Troubleshooting Tips

1. **Always check the cycle status first** - Most confirmation issues stem from cycle timing
2. **Verify CFPROCESS batch completed** - Data issues after submit usually trace to batch errors
3. **Use diagnostic queries to verify data** - Do not assume the UI is showing correct data; query directly
4. **Compare across all three sources** - Nominations, CAS, and Confirmations may have different values
5. **Check configuration before debugging code** - Many issues are configuration-related (EPSQ, path balancing, cycle defaults)

### Prevention Best Practices

1. **Monitor CFPROCESS execution** - Set up alerts for batch failures
2. **Validate EPSQ configuration** - Review EPSQ values when adding new locations
3. **Test cycle transitions** - Verify cycle open/close times before gas day
4. **Regular data cleanup** - Archive old confirmation and hourly profile data
5. **Index maintenance** - Keep CFCTRL_CONF and related table indexes optimized

---

## Related Documentation

- **Domain**: [domain.md](./domain.md) - Business concepts
- **Architecture**: [architecture.md](./architecture.md) - Technical implementation
- **Nominations Troubleshooting**: [../nominations/troubleshooting.md](../nominations/troubleshooting.md) - Upstream nomination issues
- **CAS Troubleshooting**: [../capacity-scheduling-allocations/troubleshooting.md](../capacity-scheduling-allocations/troubleshooting.md) - Scheduling issues affecting confirmations
- **QUICK_REFERENCE.md**: Feature mapping and keywords

---

*Last updated: 2026-03-03*
*Document version: 1.0*
