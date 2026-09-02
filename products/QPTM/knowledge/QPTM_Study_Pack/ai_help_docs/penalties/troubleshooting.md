---
title: Penalties (PEN) - Troubleshooting Guide
category: troubleshooting
feature: Penalties (PEN)
related_repos: Web, Batch
keywords: PEN, penalties, penalty submission, penalty results, hourly penalty schedule, troubleshooting, debug, error, BLCTRL_PENALTY, BLTRAN_INVOICE_PENALTY_HDR, KCTRL_HRLY_PENALTY_SCHD
last_updated: 2026-03-03
---

# Penalties (PEN) - Troubleshooting Guide

## Overview

This document provides guidance for diagnosing and resolving common issues in the Penalties (PEN) feature. It includes diagnostic SQL queries, code locations, and step-by-step resolution procedures.

For business concepts, see [Domain Documentation](./domain.md).
For technical architecture, see [Architecture Documentation](./architecture.md).

---

## Table of Contents

1. [Common Issues - Penalty Submission](#common-issues---penalty-submission)
2. [Common Issues - Penalty Results](#common-issues---penalty-results)
3. [Common Issues - Hourly Penalty Schedule](#common-issues---hourly-penalty-schedule)
4. [Diagnostic SQL Queries](#diagnostic-sql-queries)
5. [Key Code Locations](#key-code-locations)
6. [Error Messages Reference](#error-messages-reference)
7. [Debugging Tips](#debugging-tips)

---

## Common Issues - Penalty Submission

### Issue: "Cannot Query because all of the required params have not been specified"

**Symptoms**: User receives error message when clicking Query on the Penalty Submission screen.

**Root Cause**: One or more required parameters are missing: `EffDateFrom`, `TspNo`, or `PenaltyTypeCode`.

**Code Location**: `QUIControllerPenaltySubmission.DoQuery()` (line ~68)
```
File: Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerPenaltySubmission.cs
```

**Resolution**:
1. Ensure TSP Number is selected (defaults to current TSP if > 0)
2. Ensure Penalty Type is selected from the dropdown
3. Ensure Effective Date From is populated (defaults to current date)
4. Verify the penalty type exists in `QCODE_PENALTY_TYPE` for the selected TSP

**Diagnostic Query**:
```sql
-- Check available penalty types for a TSP
SELECT PenaltyTypeCode, PenaltyBasisCode, TspNo
FROM QCODE_PENALTY_TYPE
WHERE TSP_NO = @TspNo;
```

---

### Issue: "Cannot Save because all of the required params have not been specified"

**Symptoms**: Save fails with error message and/or field-level validation errors on PenaltyDescr or PenaltyTypeCode.

**Root Cause**: Missing required save parameters: `EffDateFrom`, `TspNo`, `PenaltyDescr`, or `PenaltyTypeCode`.

**Code Location**: `QUIControllerPenaltySubmission.DoSave()` (line ~128)
```
File: Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerPenaltySubmission.cs
```

**Additional check for Allocations basis**: If `PenaltyBasisCode = "AL"`, the `LocGrpId` and `LocGrpNm` must also be specified. Missing these throws a `QUserException`.

**Resolution**:
1. Verify Penalty Description is filled in
2. Verify Penalty Type is selected
3. For Allocations-based penalties, verify Location Group is selected
4. Check browser console for field-specific error indicators

---

### Issue: No accounts appear in the Available Accounts grid

**Symptoms**: After querying with valid parameters, the Available Accounts grid is empty.

**Root Cause**: Multiple possible causes in the account filtering pipeline.

**Code Location**: `QUIControllerPenaltySubmission.DoQuery()` and `QPTMServiceCore.FilterAccountsByPenaltyRelation()`
```
Files:
  Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerPenaltySubmission.cs
  Quorum.QPTM.ServiceCore/QPTMServiceCore_PenaltySubmission.cs
```

**Diagnosis Steps**:

1. **Check if penalty basis is Allocations**: If `PenaltyBasisCode = "AL"`, account grids are not shown at all -- this is expected behavior. Verify the penalty type's basis code.

2. **Check inventory accounts exist for TSP**:
```sql
SELECT COUNT(*) FROM InventoryAccountHeader WHERE TSP_NO = @TspNo;
```

3. **Check TOC rules include the penalty type**:
```sql
-- Verify TOC rules exist for the penalty type
SELECT toc.TOC_CD, rule.INCLUDE_TYPE_CD, rule.PENALTY_TYPE_CD
FROM RTTypeOfCharge toc
JOIN RTTypeOfChargeRule rule ON toc.TOC_CD = rule.TOC_CD AND toc.TSP_NO = rule.TSP_NO
WHERE toc.TSP_NO = @TspNo
  AND rule.PENALTY_TYPE_CD = @PenaltyTypeCode
  AND rule.INCLUDE_TYPE_CD = 'I';
```

4. **Check TOS-TOC cross-reference rules exist as of the effective date**:
```sql
-- Verify TOS-TOC mappings exist
SELECT tos.TOS_CD, tos.TOC_CD, tos.EFF_DT_FROM, tos.EFF_DT_TO
FROM RateTosTocRuleXRef tos
WHERE tos.TSP_NO = @TspNo
  AND tos.EFF_DT_FROM <= @EffDateFrom
  AND tos.EFF_DT_TO >= @EffDateFrom;
```

5. **Check for NCTS exclusion**: Accounts with TOS code `NCTS` are automatically excluded (hard-coded for TEC/LDC).
```sql
-- Check if accounts have NCTS TOS
SELECT c.CTR_NO, c.TOS_CD
FROM Contract c
JOIN InventoryAccountHeader iah ON c.CTR_NO = iah.PRIMARY_CTR_NO AND c.TSP_NO = iah.TSP_NO
WHERE iah.TSP_NO = @TspNo AND c.TOS_CD = 'NCTS';
```

---

### Issue: Accounts not moving between Available and Selected grids

**Symptoms**: Clicking the add/remove buttons does not transfer accounts between grids.

**Root Cause**: Row selection state (`IsSelectedObject`) not properly set.

**Code Location**: `PenaltySubmissionController.SelectedAccountAddNewRow()` / `SelectedAccountDeleteRow()`
```
File: Quorum.QPTM.Web.Core/Controllers/PenaltySubmissionController.cs
```

**Resolution**:
1. Ensure rows are properly selected (checkbox checked) in the grid before clicking the transfer button
2. The controller checks `x.IsSelectedObject` to determine which rows to move
3. If the issue persists, check the `AvailableAccountsHeaderSelectedObjectsChanged` and `SelectedAccountsHeaderSelectedObjectsChanged` endpoints for proper selection tracking

---

### Issue: "Cannot access the code table service" error

**Symptoms**: Error appears when querying or saving penalty submission.

**Root Cause**: The `CheckPenaltyBasis` method returned `"Error"`, meaning the penalty type code was not found in `QCODE_PENALTY_TYPE` for the TSP.

**Code Location**: `QPTMServiceCore.CheckPenaltyBasis()`
```
File: Quorum.QPTM.ServiceCore/QPTMServiceCore_PenaltySubmission.cs (line ~131)
```

**Resolution**:
1. Verify the penalty type exists for the TSP:
```sql
SELECT * FROM QCODE_PENALTY_TYPE WHERE TSP_NO = @TspNo AND PENALTY_TYPE_CD = @PenaltyTypeCode;
```
2. If missing, the penalty type needs to be configured in the code table for the TSP
3. Verify the service endpoint for `IQPTMDataAccess_PenaltyType` is properly configured

---

### Issue: HasAccounts flag prevents re-query

**Symptoms**: After initial query, subsequent queries do not refresh the account data.

**Root Cause**: The `HasAccounts` flag is set to `true` after the first query. If it remains `true`, `DoQuery` returns immediately without re-fetching.

**Code Location**: `QUIControllerPenaltySubmission.DoQuery()` (line ~65)
```
File: Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerPenaltySubmission.cs
```

**Resolution**:
- The "Retrieve" action in `PenaltySubmissionController.DoAction` resets `HasAccounts = false` before calling Retrieve
- Changing the PenaltyId field also resets `HasAccounts = false` (in `PenaltySubmissionFieldUpdate`)
- If the issue persists, close and reopen the screen

---

## Common Issues - Penalty Results

### Issue: "Please select a valid TSP Number" error on query

**Symptoms**: Query fails with TSP validation error.

**Root Cause**: TSP Number is zero or negative.

**Code Location**: `QUIControllerPenaltyResults.DoQuery()` (line ~43)
```
File: Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerPenaltyResults.cs
```

**Resolution**: Select a valid TSP Number in the header parameters.

---

### Issue: No penalty results returned despite expected data

**Symptoms**: Query returns empty results when data is expected.

**Root Cause**: Filter criteria too restrictive or data not present for the selected parameters.

**Diagnosis Steps**:

1. **Check with minimal filters** (TSP only):
```sql
SELECT COUNT(*)
FROM BLTRAN_INVOICE_PENALTY_HDR
WHERE TSP_NO = @TspNo;
```

2. **Check accounting month range**:
```sql
SELECT DISTINCT ACCTG_MTH
FROM BLTRAN_INVOICE_PENALTY_HDR
WHERE TSP_NO = @TspNo
ORDER BY ACCTG_MTH DESC;
```
Note: The controller filters AcctgMth by first-day-of-month to last-day-of-month range.

3. **Check approval/processing filters**:
```sql
-- Count by approval and processing status
SELECT APPROVE_IND, PROC_IND, COUNT(*)
FROM BLTRAN_INVOICE_PENALTY_HDR
WHERE TSP_NO = @TspNo
GROUP BY APPROVE_IND, PROC_IND;
```
The "Unapproved Records Only" checkbox filters `IsApprove != true` and "Unprocessed Records Only" filters `IsProc != true`.

---

### Issue: Penalty Details popup shows no tier or pool data

**Symptoms**: Opening the Penalty Details popup shows empty Tier Details or missing Pool Details tab.

**Root Cause**: No child records exist for the selected penalty result.

**Code Location**: `PenaltyResultsController.FormPenaltyDetails()` (line ~276)
```
File: Quorum.QPTM.Web.Core/Controllers/PenaltyResultsController.cs
```

**Key Logic**: The Pool Details tab is only rendered if `prh.PenaltyResultsPoolDtl.FirstOrDefault() != null`. If no pool detail records exist, the tab is hidden.

**Diagnostic Query**:
```sql
-- Check tier details
SELECT * FROM BLTRAN_INVOICE_PENALTY_DTL
WHERE INVOICE_PENALTY_ID = @InvoicePenaltyId AND TSP_NO = @TspNo;

-- Check pool details
SELECT * FROM BLTRAN_INVOICE_PENALTY_POOLDTL
WHERE INVOICE_PENALTY_ID = @InvoicePenaltyId AND TSP_NO = @TspNo;
```

---

### Issue: Cannot approve or process penalty results

**Symptoms**: Changes to IsApprove or IsProc flags are not saving.

**Root Cause**: The save operation calls `Service.UpdateMultiplePenaltyResults` on the entire `BulkContainer.Items` list.

**Code Location**: `QUIControllerPenaltyResults.DoSave()` (line ~96)
```
File: Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerPenaltyResults.cs
```

**Resolution**:
1. Ensure the checkbox/flag is properly toggled in the grid
2. Click Save to persist changes
3. Verify the record is not locked by another process
4. Check for validation errors returned from `UpdateMultiplePenaltyResults`

---

### Issue: Excel export fails or returns incomplete data

**Symptoms**: Export to Excel produces an error or missing columns.

**Code Location**: `PenaltyResultsController.PenaltyResultsExcelExport()`
```
File: Quorum.QPTM.Web.Core/Controllers/PenaltyResultsController.cs (line ~258)
```

**Resolution**:
1. Verify the grid metadata is correctly configured for `Constants.GridIDs.PenaltyResults`
2. Check that the `QImportExportDefinition` is properly set up for `PenaltyResultsHdrDO`
3. The export applies the current request's filters and sorts before generating the file

---

## Common Issues - Hourly Penalty Schedule

### Issue: "Schedule ID is required" / "Effective Date From is required" errors

**Symptoms**: Query fails with validation error.

**Code Location**: `QUIControllerHourlyPenaltySchedule.ReadyForQuery()` (line ~82)
```
File: Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerHourlyPenaltySchedule.cs
```

**Resolution**: Both Schedule ID and Effective Date From are required before querying. Use the Schedule ID pick list to select a valid schedule.

---

### Issue: "Hourly Profile does not have a valid 24 scheduled hours"

**Symptoms**: Creating a new hourly penalty schedule fails with this error.

**Root Cause**: The TSP's hourly profile does not have exactly 24 hours configured.

**Code Location**: `QUIControllerHourlyPenaltySchedule.BuildDefaultSchedule()` (line ~476)
```
File: Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerHourlyPenaltySchedule.cs
```

**Resolution**:
1. Verify the TSP's hourly profile configuration:
```sql
-- Check hour profile for the TSP
SELECT * FROM HourProfile
WHERE TSP_NO = @TspNo
ORDER BY HR_ORDER;
```
2. Ensure exactly 24 hours are configured
3. The profile is retrieved via `ConfirmationService.GetHourlyProfile(tspNo, currentDate)`

---

### Issue: "Modifying existing Schedule ID with new Schedule ID is not permitted"

**Symptoms**: Clone operation fails with this error.

**Root Cause**: User changed the Schedule ID in the header before cloning, but the complete DO has `DataObjectState.Unchanged`.

**Code Location**: `QUIControllerHourlyPenaltySchedule.DoClone()` (line ~191)
```
File: Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerHourlyPenaltySchedule.cs
```

**Resolution**: To clone a schedule, do not change the Schedule ID before clicking Clone. The system will generate a new ID on save.

---

### Issue: Tolerance values not persisting correctly

**Symptoms**: After saving, tolerance values appear cleared or wrong.

**Root Cause**: The `ClearToleranceFields` method clears tolerance fields that don't match the selected hourly penalty type.

**Code Location**: `QUIControllerHourlyPenaltySchedule.ClearToleranceFields()` (line ~535)
```
File: Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerHourlyPenaltySchedule.cs
```

**Key Logic**:
- If `HrlyPenaltyTypeCode = "D"` (Discrete): Clears `HighTolerancePctAsPct` and `LowTolerancePctAsPct`
- If `HrlyPenaltyTypeCode = "P"` (Percent): Clears `HighToleranceQty` and `LowToleranceQty`

**Resolution**:
1. Verify the correct Hourly Penalty Type Code is selected (Discrete vs Percent)
2. Only populate the tolerance fields that match the selected type
3. The non-matching fields will be cleared on save by design

---

### Issue: Schedule ID not generated on new schedule save

**Symptoms**: After saving a new schedule, the Schedule ID remains blank or zero.

**Root Cause**: The `SCHD_ID` sequence may not be properly configured.

**Code Location**: `QPTMAllocationService.UpdateHrlyPenaltySchdHeaders()` (line ~119)
```
File: Quorum.QPTM.ServiceCore.Allocation/QPTMAllocationServiceExt_PenaltySchedule.cs
```

**Diagnostic Steps**:
1. Check the sequence generator:
```sql
-- Check SCHD_ID sequence
EXEC USPG_GETNEXTSEQ @TspNo, 'SCHD_ID', 1;
```
2. Verify the stored procedure `USPG_GETNEXTSEQ` is accessible and returns valid values
3. The service retries in a while loop until `schdID > 0`

---

## Diagnostic SQL Queries

### Penalty Submission Queries

```sql
-- List all penalty definitions for a TSP
SELECT p.PENALTY_ID, p.TSP_NO, p.PENALTY_TYPE_CD, p.PENALTY_DESCR,
       p.EFF_DT_FROM, p.EFF_DT_TO, p.LOC_GRP_ID, p.USER_ID, p.UPDT_DT
FROM BLCTRL_PENALTY p
WHERE p.TSP_NO = @TspNo
ORDER BY p.PENALTY_ID;

-- List penalty detail (account associations) for a penalty
SELECT d.PENALTY_DTL_ID, d.PENALTY_ID, d.INV_ACCT_ID, d.TSP_NO
FROM BLCTRL_PENALTY_DTL d
WHERE d.PENALTY_ID = @PenaltyId AND d.TSP_NO = @TspNo;

-- Check penalty type configuration
SELECT pt.PENALTY_TYPE_CD, pt.TSP_NO, pt.PENALTY_BASIS_CD
FROM QCODE_PENALTY_TYPE pt
WHERE pt.TSP_NO = @TspNo;

-- Join penalty with its details and account info
SELECT p.PENALTY_ID, p.PENALTY_DESCR, p.PENALTY_TYPE_CD,
       d.INV_ACCT_ID, iah.PRIMARY_CTR_NO
FROM BLCTRL_PENALTY p
LEFT JOIN BLCTRL_PENALTY_DTL d ON p.PENALTY_ID = d.PENALTY_ID AND p.TSP_NO = d.TSP_NO
LEFT JOIN InventoryAccountHeader iah ON d.INV_ACCT_ID = iah.ID_INV_ACCT AND d.TSP_NO = iah.TSP_NO
WHERE p.TSP_NO = @TspNo AND p.PENALTY_ID = @PenaltyId;
```

### Penalty Results Queries

```sql
-- List penalty results for a TSP and accounting month
SELECT h.INVOICE_PENALTY_ID, h.PENALTY_ID, h.PENALTY_TYPE_CD,
       h.CTR_NO, h.BP_NO, h.ACCTG_MTH, h.PROD_MTH,
       h.PENALTY_ENG_QTY, h.PENALTY_VOL_QTY, h.PENALTY_AMT, h.RATE,
       h.APPROVE_IND, h.PROC_IND
FROM BLTRAN_INVOICE_PENALTY_HDR h
WHERE h.TSP_NO = @TspNo
  AND h.ACCTG_MTH >= @AcctgMthFrom AND h.ACCTG_MTH <= @AcctgMthTo
ORDER BY h.INVOICE_PENALTY_ID;

-- Get unapproved penalty results
SELECT h.INVOICE_PENALTY_ID, h.CTR_NO, h.PENALTY_AMT, h.PENALTY_TYPE_CD
FROM BLTRAN_INVOICE_PENALTY_HDR h
WHERE h.TSP_NO = @TspNo AND h.APPROVE_IND = 0;

-- Get unprocessed penalty results
SELECT h.INVOICE_PENALTY_ID, h.CTR_NO, h.PENALTY_AMT, h.PENALTY_TYPE_CD
FROM BLTRAN_INVOICE_PENALTY_HDR h
WHERE h.TSP_NO = @TspNo AND h.PROC_IND = 0;

-- Penalty results with tier details
SELECT h.INVOICE_PENALTY_ID, h.PENALTY_AMT,
       d.INVOICE_PENALTY_DTL_ID, d.TIER_DTL_DESCR
FROM BLTRAN_INVOICE_PENALTY_HDR h
JOIN BLTRAN_INVOICE_PENALTY_DTL d ON h.INVOICE_PENALTY_ID = d.INVOICE_PENALTY_ID AND h.TSP_NO = d.TSP_NO
WHERE h.TSP_NO = @TspNo AND h.INVOICE_PENALTY_ID = @InvoicePenaltyId;

-- Penalty results with pool details
SELECT h.INVOICE_PENALTY_ID, h.PENALTY_AMT,
       p.POOL_SEQ_NO
FROM BLTRAN_INVOICE_PENALTY_HDR h
JOIN BLTRAN_INVOICE_PENALTY_POOLDTL p ON h.INVOICE_PENALTY_ID = p.INVOICE_PENALTY_ID AND h.TSP_NO = p.TSP_NO
WHERE h.TSP_NO = @TspNo AND h.INVOICE_PENALTY_ID = @InvoicePenaltyId;

-- Summary of penalty amounts by type and month
SELECT h.PENALTY_TYPE_CD, h.ACCTG_MTH,
       COUNT(*) AS RecordCount,
       SUM(h.PENALTY_AMT) AS TotalPenaltyAmt,
       SUM(h.PENALTY_ENG_QTY) AS TotalPenaltyEngQty
FROM BLTRAN_INVOICE_PENALTY_HDR h
WHERE h.TSP_NO = @TspNo
GROUP BY h.PENALTY_TYPE_CD, h.ACCTG_MTH
ORDER BY h.ACCTG_MTH DESC, h.PENALTY_TYPE_CD;
```

### Hourly Penalty Schedule Queries

```sql
-- List all hourly penalty schedules for a TSP
SELECT h.TSP_NO, h.SCHD_ID, h.SCHD_NM, h.EFF_DT_FROM, h.EFF_DT_TO, h.HRLY_PENALTY_TYPE_CD
FROM KCTRL_HRLY_PENALTY_SCHD_HDR h
WHERE h.TSP_NO = @TspNo
ORDER BY h.SCHD_ID, h.EFF_DT_FROM;

-- Get schedule detail for a specific schedule and effective date
SELECT d.HOUR_ID, d.LOW_TOLERANCE_PCT, d.HIGH_TOLERANCE_PCT,
       d.LOW_TOLERANCE_QTY, d.HIGH_TOLERANCE_QTY
FROM KCTRL_HRLY_PENALTY_SCHD_DTL d
WHERE d.TSP_NO = @TspNo AND d.SCHD_ID = @SchdId AND d.EFF_DT_FROM = @EffDateFrom
ORDER BY d.HOUR_ID;

-- Check hour profile configuration
SELECT HP.ID_HOUR, HP.HOUR, HP.HR_ORDER
FROM HourProfile HP
WHERE HP.TSP_NO = @TspNo
ORDER BY HP.HR_ORDER;
```

### Account Filtering Diagnostic Queries

```sql
-- Check TOC codes for TSP
SELECT TOC_CD FROM RTTypeOfCharge WHERE TSP_NO = @TspNo;

-- Check TOC rules for penalty type inclusion
SELECT TOC_CD, PENALTY_TYPE_CD, INCLUDE_TYPE_CD
FROM RTTypeOfChargeRule
WHERE TSP_NO = @TspNo AND PENALTY_TYPE_CD = @PenaltyTypeCode AND INCLUDE_TYPE_CD = 'I';

-- Check TOS-TOC cross-reference valid as of date
SELECT TOS_CD, TOC_CD, EFF_DT_FROM, EFF_DT_TO
FROM RateTosTocRuleXRef
WHERE TSP_NO = @TspNo
  AND EFF_DT_FROM <= @EffDate AND EFF_DT_TO >= @EffDate;

-- Find accounts excluded by NCTS
SELECT iah.ID_INV_ACCT, iah.PRIMARY_CTR_NO, c.TOS_CD
FROM InventoryAccountHeader iah
JOIN Contract c ON iah.PRIMARY_CTR_NO = c.CTR_NO AND iah.TSP_NO = c.TSP_NO
WHERE iah.TSP_NO = @TspNo AND c.TOS_CD = 'NCTS';
```

---

## Key Code Locations

### Service Layer

| File | Description |
|------|-------------|
| `Quorum.QPTM.ServiceCore/QPTMServiceCore_PenaltySubmission.cs` | Penalty submission service (862 lines). Account filtering, CRUD, enrichment methods. |
| `Quorum.QPTM.ServiceCore.Allocation/QPTMAllocationServiceExt_PenaltySchedule.cs` | Hourly penalty schedule CRUD via allocation service. |

### Controllers

| File | Description |
|------|-------------|
| `Quorum.QPTM.Web.Core/Controllers/PenaltySubmissionController.cs` | MVC controller for Penalty Submission screen. Grid actions, field updates. |
| `Quorum.QPTM.Web.Core/Controllers/PenaltyResultsController.cs` | MVC controller for Penalty Results screen. Grid, popup, export, tier/pool details. |

### UI Controllers

| File | Description |
|------|-------------|
| `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerPenaltySubmission.cs` | Business logic for Penalty Submission: DoQuery, DoSave, DoNew, DoClone, params. |
| `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerPenaltyResults.cs` | Business logic for Penalty Results: DoQuery, DoSave, DoNew, params, BulkContainer. |
| `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerHourlyPenaltySchedule.cs` | Business logic for Hourly Penalty Schedule: effective dating, tolerance clearing, validation. |

### Service Interfaces

| File | Description |
|------|-------------|
| `Quorum.QPTM.ServiceInterface/IQPTMServiceInterface_PenaltySubmission.cs` | WCF interface for penalty submission operations |
| `Quorum.QPTM.ServiceInterface/IQPTMServiceInterface_PenaltyResults.cs` | WCF interface for penalty results operations |
| `Quorum.QPTM.ServiceInterface/IQPTMServiceInterface_HourlyPenaltySchedule.cs` | WCF interface for hourly penalty schedule operations |

### Data Objects

| File | Description |
|------|-------------|
| `Quorum.QPTM.DataObject/CodeGen/PenaltyIdDO.cs` | Penalty header DO (table: BLCTRL_PENALTY) |
| `Quorum.QPTM.DataObject/CodeGen/PenaltyIdDtlDO.cs` | Penalty detail DO (table: BLCTRL_PENALTY_DTL) |
| `Quorum.QPTM.DataObject/CodeGen/PenaltyTypeDO.cs` | Penalty type code DO (table: QCODE_PENALTY_TYPE) |
| `Quorum.QPTM.DataObject/CodeGen/PenaltyResultsHdrDO.cs` | Results header DO (table: BLTRAN_INVOICE_PENALTY_HDR) |
| `Quorum.QPTM.DataObject/CodeGen/PenaltyResultsDtlDO.cs` | Results tier detail DO (table: BLTRAN_INVOICE_PENALTY_DTL) |
| `Quorum.QPTM.DataObject/CodeGen/PenaltyResultsPoolDtlDO.cs` | Results pool detail DO (table: BLTRAN_INVOICE_PENALTY_POOLDTL) |
| `Quorum.QPTM.DataObject/CodeGen/HourlyPenaltyScheduleHeaderDO.cs` | Schedule header DO (table: KCTRL_HRLY_PENALTY_SCHD_HDR) |
| `Quorum.QPTM.DataObject/CodeGen/HourlyPenaltyScheduleDetailDO.cs` | Schedule detail DO (table: KCTRL_HRLY_PENALTY_SCHD_DTL) |
| `Quorum.QPTM.DataObject/PenaltyResultsHdrDOExt.cs` | Extension adding BpNm property |
| `Quorum.QPTM.DataObject/PenaltyResultsDtlDOExt.cs` | Extension adding TierDtlDescr property |

### Views

| File | Description |
|------|-------------|
| `Quorum.QPTM.Web/Views/PenaltySubmission/PenaltySubmission.cshtml` | Penalty Submission main view |
| `Quorum.QPTM.Web/Views/PenaltyResults/PenaltyResults.cshtml` | Penalty Results main view |
| `Quorum.QPTM.Web/Views/PenaltyResults/_PenaltyDetails.cshtml` | Penalty Details popup |
| `Quorum.QPTM.Web/Views/PenaltyResults/_PenaltyDetails_Tier.cshtml` | Tier Details tab |
| `Quorum.QPTM.Web/Views/PenaltyResults/_PenaltyDetails_Pool.cshtml` | Pool Details tab |
| `Quorum.QPTM.Web/Views/HourlyPenaltySchedule/HourlyPenaltySchedule.cshtml` | Hourly Penalty Schedule view |

### Constants

| File | Relevant Constants |
|------|-------------------|
| `Quorum.QPTM.CoreInterface/Constants.cs` | `PenaltyBasisCode`, `PenaltyTypeCode`, `HourlyPenaltyTypeCode`, `HourlyPenaltyConstant`, `SecurityObjectIDs`, `GridIDs`, `PickListIds`, `TypeOfService.NCTS` |

---

## Error Messages Reference

| Error Message | Source | Cause |
|---------------|--------|-------|
| "Cannot Query because all of the required params have not been specified." | `QUIControllerPenaltySubmission.DoQuery` | Missing EffDateFrom, TspNo, or PenaltyTypeCode |
| "Cannot Save because all of the required params have not been specified." | `QUIControllerPenaltySubmission.DoSave` | Missing EffDateFrom, TspNo, PenaltyDescr, or PenaltyTypeCode |
| "Cannot Save because all of the required params have not been specified" | `QUIControllerPenaltySubmission.AddAlertOnSave` | Missing LocGrpId or LocGrpNm for Allocations basis (throws QUserException) |
| "Cannot acces the code table service" | `QUIControllerPenaltySubmission.AddAlertOnSave` | `CheckPenaltyBasis` returned "Error" (throws QUserException, note typo in original) |
| "Cannot access the code table service." | `QUIControllerPenaltySubmission.DoQuery` | `CheckPenaltyBasis` returned "Error" |
| "Please select a valid TSP Number" | `QUIControllerPenaltyResults.DoQuery` | TspNo <= 0 |
| "Invalid TSP Number: {tspNo}" | `QPTMAllocationService.GetHrlyPenaltySchdHeaders` | tspNo <= 0 |
| "Invalid schedule ID: {schdID}" | `QPTMAllocationService.GetHrlyPenaltySchdHeaders` | schdID <= 0 |
| "Schedule ID is required" | `QUIControllerHourlyPenaltySchedule.ReadyForQuery` | SchdId is invalid/empty |
| "Effective Date From is required" | `QUIControllerHourlyPenaltySchedule.ReadyForQuery` | EffDateFrom is null or MinValue |
| "Hourly Profile does not have a valid 24 scheduled hours." | `QUIControllerHourlyPenaltySchedule.BuildDefaultSchedule` | Hour profile count != 24 |
| "Modifying existing Schedule ID with new Schedule ID is not permitted." | `QUIControllerHourlyPenaltySchedule.DoClone` | SchdId changed before clone on unchanged record |

---

## Debugging Tips

### Enabling Verbose Logging

1. **Service layer errors**: Check `QMsgLog.GlobalInstance` for error messages added during query/save operations
2. **Controller exceptions**: `QUIControllerHourlyPenaltySchedule` catches exceptions and logs them via `QMsgLogBase.GlobalInstance.AddErrorMsg(ex.ToString())`
3. **User exceptions**: `QUserException` is used for user-facing validation errors that should be displayed

### Checking Data State

1. **PenaltyId data state**: After save, verify the `PenaltyIdDO.PenaltyId` property was updated from the database (new records get their ID on first save)
2. **HasAccounts flag**: Monitor `MyParams.HasAccounts` to understand whether account data is cached or needs refresh
3. **BulkContainer.Items**: For Penalty Results, all grid data lives in `BulkContainer.Items` on the UI controller

### Common Debugging Patterns

1. **Break on DoQuery/DoSave**: Set breakpoints in the UI controller's `DoQuery()` and `DoSave()` methods to trace business logic flow
2. **Trace account filtering**: The `FilterAccountsByPenaltyRelation` method has multiple loop stages -- set breakpoints in each to identify where accounts are being filtered out
3. **Check penalty basis path**: The `CheckPenaltyBasis` result determines which code path executes in both DoQuery and DoSave -- verify the return value early
4. **Hourly schedule validation**: Set a breakpoint on `Service.ValidateSingleHourlyPenaltyScheduleComplete` to inspect validation results before save

### Known Codebase Notes

1. **Validation is disabled for Penalty Submission**: All `ValidateSingle/MultiPenaltySubmission` methods are commented out. The Validate button is also removed from the UI. Validation is only performed inline in `DoSave`.
2. **NCTS exclusion is hard-coded**: The TOS `NCTS` exclusion in `FilterAccountsByPenaltyRelation` is intentionally hard-coded for TEC (LDC) clients. There is a comment acknowledging this risk.
3. **Typo in error message**: The `AddAlertOnSave` method contains a typo: `"Cannot acces the code table service"` (missing 's' in "access").
4. **Grid ID typo**: `Constants.GridIDs.PenaltyResultsTierDetails` has value `"PentaltyDetailsTierGrid"` (note "Pentalty" instead of "Penalty"). This is the configured value and should not be changed without updating metadata.

---

*Last updated: 2026-03-03*

*Document version: 1.0*
