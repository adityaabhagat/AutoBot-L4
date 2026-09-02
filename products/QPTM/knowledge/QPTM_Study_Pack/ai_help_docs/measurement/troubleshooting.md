---
title: Measurement (MEAS) - Troubleshooting Guide
category: troubleshooting
feature: Measurement (MEAS)
related_repos: Web, Batch
keywords: MEAS, measurement, troubleshooting, errors, validation, accounting month, accuracy code, aggregate, bidirectional, POV, hourly, By Month, PPA, volume, energy, BTU, close schedule, FlowCal, SCADA
last_updated: 2026-03-03
---

# Measurement (MEAS) - Troubleshooting Guide

## Overview

This document provides troubleshooting guidance for common issues in the Measurement (MEAS) feature of the QPTM system. It covers error messages, root causes, resolution steps, SQL diagnostic queries, and code locations.

For business concepts, see [Domain Documentation](./domain.md).
For technical architecture, see [Architecture Documentation](./architecture.md).

---

## Table of Contents

1. [Validation Errors](#validation-errors)
2. [Query and Data Issues](#query-and-data-issues)
3. [Hourly Measurement Issues](#hourly-measurement-issues)
4. [By Month Distribution Issues](#by-month-distribution-issues)
5. [Aggregate Location Issues](#aggregate-location-issues)
6. [Bidirectional Location Issues](#bidirectional-location-issues)
7. [Accounting Month Issues](#accounting-month-issues)
8. [PPA Reallocation Issues](#ppa-reallocation-issues)
9. [Performance Issues](#performance-issues)
10. [Integration Issues](#integration-issues)
11. [Diagnostic SQL Queries](#diagnostic-sql-queries)
12. [Key File Locations](#key-file-locations)

---

## Validation Errors

### Error: "Aggregate Volume Entry is not allowed"

**Validation Rule:** `QPTMValidationMeasurementEntry001_ValidateAggregateVolumeEntry`
**Error String:** `Strings.MEASUREMENTENTRY_VALIDATE_AGGREGATE_VOLUME_ENTRY`

**Root Cause:** User is attempting to save measurement data at a parent (aggregate) location, but the global configuration `ALLOW_AGGREGATE_VOLUME_ENTRY` is disabled.

**Resolution:**
1. Check if the location is a parent/aggregate location:
   ```sql
   SELECT * FROM PA_LOC_AGGR
   WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc
   AND EFF_DT_FROM <= @ProdMth AND EFF_DT_TO >= @ProdMth
   ```
2. If aggregate entry is required, enable the global config:
   ```sql
   SELECT * FROM GLOBAL_CONFIG_CTRL
   WHERE CONFIG_CATEGORY = 'MEASUREMENT ENTRY'
   AND KEY_NM = 'ALLOW_AGGREGATE_VOLUME_ENTRY'
   ```
3. Alternatively, enter data at the child location level and let the rollup process aggregate

**Code Location:**
- Validation: `Quorum.QPTM.Validations/Screens/MeasurementEntry/Validation Rules/QPTMValidationMeasurementEntry001_ValidateAggregateVolumeEntry.cs`
- Config: `QPTMGlobalConfigs.AllowAggregateVolumeEntry`

---

### Error: "Cannot modify Actual volumes" / Accuracy Code Validation

**Validation Rule:** `QPTMValidationMeasurementEntry002_ValidateAccuracyCode`
**Error Strings:**
- `Strings.MEASUREMENTENTRY_VALIDATE_ACCURACY_CODE_FOR_ACTUAL`
- `Strings.MEASUREMENTENTRY_VALIDATE_ACCURACY_CODE_FOR_ESTIMATE`
- `Strings.MEASUREMENTENTRY_VALIDATE_ACCURACY_CODE_FOR_OVERRIDE`

**Root Cause:** User is modifying a record with Accuracy Code = "A" (Actual) when `AllowChangeActualVolumes` is false, or attempting to change Accuracy Code to "E" (Estimate) when `AllowChangeVolumesToEstimate` is false.

**Resolution:**
1. Check the current accuracy code of the record
2. Verify global configuration settings:
   ```sql
   -- Check AllowChangeActualVolumes
   SELECT * FROM GLOBAL_CONFIG_CTRL
   WHERE KEY_NM = 'ALLOW_CHANGE_ACTUAL_VOL'

   -- Check AllowChangeVolumesToEstimate
   SELECT * FROM GLOBAL_CONFIG_CTRL
   WHERE KEY_NM = 'ALLOW_CHANGE_VOL_TO_EST'
   ```
3. If the record came from FlowCal (VolSrcCode = 'FC'), it typically has Accuracy = 'A' and may be locked

**Code Location:**
- Validation: `Quorum.QPTM.Validations/Screens/MeasurementEntry/Validation Rules/QPTMValidationMeasurementEntry002_ValidateAccuracyCode.cs`
- Config: `QPTMGlobalConfigs.AllowChangeActualVolume`, `QPTMGlobalConfigs.AllowChangeVolumesToEstimate`

---

### Error: "Accounting Month is in a closed period"

**Validation Rule:** `QPTMValidationMeasurementEntry003_ValidateAccountingMonth`
**Error String:** `Strings.MEASUREMENTENTRY_VALIDATE_ACCOUNTING_MONTH`

**Root Cause:** User is attempting to save a measurement record with an accounting month that is before the current open billing accounting month (the period is closed).

**Resolution:**
1. Check the current open accounting month:
   ```sql
   -- Find open accounting month for the TSP
   -- This varies by TSP configuration; check via the application
   ```
2. Ensure the AcctgMth on the record is >= the current open billing month
3. If the accounting month must be changed, it must be set to the current open month or a future month

**Code Location:**
- Validation: `Quorum.QPTM.Validations/Screens/MeasurementEntry/Validation Rules/QPTMValidationMeasurementEntry003_ValidateAccountingMonth.cs`

---

### Error: "Duplicate accounting month record"

**Validation Rule:** `QPTMValidationMeasurementEntry003_ValidateAccountingMonth` (second check)
**Error String:** `Strings.VALIDATE_ACC_MONTH`

**Root Cause:** User changed the accounting month on a record, and a record already exists in `ALCTRL_MEAS_VOL` for the same TspNo + IdLoc + GasDay + AcctgMth combination.

**Resolution:**
1. Query existing records for the gas day:
   ```sql
   SELECT * FROM ALCTRL_MEAS_VOL
   WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc
   AND GAS_DAY = @GasDay
   ORDER BY ACCTG_MTH DESC
   ```
2. Determine if the target accounting month already has a record
3. Either use the existing record or choose a different accounting month

---

### Error: "POV must be set for bidirectional locations"

**Validation Rule:** `QPTMValidationMeasurementEntry004_ValidateBidirectionalLocations`
**Error String:** `Strings.MEASUREMENTENTRY_VALIDATE_BIDIRECTIONAL_LOCATIONS`

**Root Cause:** The location is bidirectional (POV = 'B'), but the measurement record does not have a valid POV code set to either Receipt ('R') or Delivery ('D').

**Resolution:**
1. Verify the location is bidirectional:
   ```sql
   SELECT LOC_ID, POV_CD FROM PA_LOC
   WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc
   AND EFF_DT_FROM <= @AsOfDate AND EFF_DT_TO >= @AsOfDate
   ```
2. Set the POV code on each measurement record to 'R' or 'D'
3. Note: This validation only fires when `PositionState` is true and the record has volume/energy/BTU data

**Code Location:**
- Validation: `Quorum.QPTM.Validations/Screens/MeasurementEntry/Validation Rules/QPTMValidationMeasurementEntry004_ValidateBidirectionalLocations.cs`

---

### Error: "Gas Day cannot be greater than Accounting Month"

**Validation Rule:** `QPTMValidationMeasurementEntry005_ValidateGasDay`
**Error String:** `Strings.MEASUREMENTENTRY_VALIDATE_GAS_DAY`

**Root Cause:** The gas day on a measurement record is later than the last day of the accounting month. For example, GasDay = 2026-04-15 with AcctgMth = 2026-03-01.

**Resolution:**
1. Ensure the accounting month encompasses the gas day
2. The accounting month is always the first day of a month; the gas day must be <= last day of that month
3. Usually indicates a data entry error or incorrect accounting month selection

**Code Location:**
- Validation: `Quorum.QPTM.Validations/Screens/MeasurementEntry/Validation Rules/QPTMValidationMeasurementEntry005_ValidateGasDay.cs`

---

### Error: "Invalid Location"

**Validation Rule:** `QPTMValidationMeasurementEntry006_ValidateLocation`
**Error String:** `Strings.MEASUREMENTENTRY_VALIDATE_LOCATION`

**Root Cause:** The location ID does not exist in the `PA_LOC` table for the given TSP number.

**Resolution:**
1. Verify the location exists:
   ```sql
   SELECT * FROM PA_LOC
   WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc
   ```
2. Check if the location has valid effective dates covering the measurement period
3. Ensure the location is associated with the correct TSP

**Code Location:**
- Validation: `Quorum.QPTM.Validations/Screens/MeasurementEntry/Validation Rules/QPTMValidationMeasurementEntry006_ValidateLocation.cs`

---

### Error: "Value must be specified for AcctgMth / BtuFactor / AccuracyCode"

**Source:** `QUIControllerMeasurementEntry.PreSave()`

**Root Cause:** A mandatory field is missing on a record that has volume or energy data. The PreSave check requires:
- AcctgMth when VolQty is entered (MCF mode) or EngQty is entered (DTH mode) or both (BTU mode)
- BtuFactor for all modes with data
- AccuracyCode for all modes with data

**Resolution:**
1. Ensure all mandatory fields are populated for records with volume/energy data
2. Check if the MeasOption matches the data being entered (BTU expects both VolQty and EngQty)

**Code Location:**
- `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerMeasurementEntry.cs`, `PreSave()` method

---

### Error: "Required fields: Location, Production Month, Accounting Month"

**Source:** `QUIControllerMeasurementEntry.ReadyForQuery()`
**Error String:** `Strings.MEASUREMENTENTRY_VALIDATE_REQUIREDFIELD`

**Root Cause:** One or more required query parameters are missing (IdLoc, ProdMth, or AcctgMth).

**Resolution:** Ensure all header fields are populated before clicking Query.

---

### Error: "Production Month cannot be greater than Accounting Month"

**Source:** `QUIControllerMeasurementEntry.ReadyForQuery()`
**Error String:** `Strings.MEASUREMENTENTRY_PRODMONTH_GREATERTHAN_ACCTGMTH`

**Root Cause:** The selected Production Month is after the Accounting Month, which is not allowed.

**Resolution:** Ensure ProdMth <= AcctgMth. The system auto-adjusts AcctgMth when ProdMth changes.

---

## Query and Data Issues

### Issue: Grid shows no data after query

**Possible Causes:**
1. No measurement records exist for the selected ProdMth/AcctgMth/Location combination
2. The data is in the history table but the query is routing to the control table (or vice versa)
3. AcctgMth filter is excluding records

**Diagnostic Steps:**
1. Check control table:
   ```sql
   SELECT * FROM ALCTRL_MEAS_VOL
   WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc
   AND GAS_DAY >= @ProdMthStart AND GAS_DAY <= @ProdMthEnd
   ORDER BY GAS_DAY, ACCTG_MTH DESC
   ```
2. Check history table:
   ```sql
   SELECT * FROM ALHIST_MEAS_VOL
   WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc
   AND GAS_DAY >= @ProdMthStart AND GAS_DAY <= @ProdMthEnd
   ORDER BY GAS_DAY, ACCTG_MTH DESC
   ```
3. Verify the open accounting month to understand routing:
   - ProdMth >= OpenBillAcctMonth -> control table
   - ProdMth < OpenBillAcctMonth AND AcctgMth >= OpenBillAcctMonth -> union
   - Both < OpenBillAcctMonth -> history only

**Code Location:**
- Query routing: `QPTMServiceCore_MeasurementEntry.cs`, `GetSingleMeasurementEntry()` method

---

### Issue: Grid shows empty rows with no volume/energy data

**Root Cause:** This is expected behavior. The `AddAdditionalPropertiesMeasurementEntry` method fills in missing gas days with blank records so the grid shows all days of the production month. These placeholder rows have:
- `AccuracyCode` = default (`QPTMGlobalConfigs.DefaultAccuracyCode`)
- `VolUomCode` and `EngUomCode` from TSP preferences
- Null volume and energy quantities

**Resolution:** This is by design. Enter data in the blank rows as needed.

**Code Location:**
- `QPTMServiceCore_MeasurementEntry.cs`, `AddAdditionalPropertiesMeasurementEntry()` method, "Add missing days" section

---

### Issue: Data appears stale / old values showing after save

**Possible Causes:**
1. The `DoQuery()` re-query after save may be returning cached data
2. Accounting month changes trigger a delete+add pattern (PreProcessData) which may cause confusion
3. Union query (IsUnion = true) may merge stale history data with current data

**Diagnostic Steps:**
1. Check if PreProcessData correctly processed accounting month changes
2. Verify the saved data in the control table
3. Check if the IsLatest flag is correct in history:
   ```sql
   SELECT * FROM ALHIST_MEAS_VOL
   WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc AND GAS_DAY = @GasDay
   ORDER BY ACCTG_MTH DESC
   ```

**Code Location:**
- PreProcessData: `QUIControllerMeasurementEntry.cs`, `PreProcessData()` method
- Union logic: `QPTMServiceCore_MeasurementEntry.cs`, `AddAdditionalPropertiesMeasurementEntry()`, IsUnion section

---

## Hourly Measurement Issues

### Issue: "The TSP preference for gas flow is not set up for TSP"

**Root Cause:** The hour profile is not configured for the TSP, or it has more than 24 entries. The `GetHourlyMeasurement` method requires a valid hour profile with 1-24 entries.

**Resolution:**
1. Check the hour profile:
   ```sql
   SELECT * FROM HOUR_PROFILE
   WHERE TSP_NO = @TspNo
   ORDER BY HR_ORDER
   ```
2. Ensure the profile has 1-24 entries with valid hour definitions
3. Contact pipeline admin to configure the hour profile

**Code Location:**
- `QPTMAllocationServiceExt_Measurement.cs`, `GetHourlyMeasurement()` method

---

### Error: "Measurement value must be a positive number"

**Validation Rule:** `QPTMValidationHourlyMeasurementMaintenance003_ValidateQtyDisplay`

**Root Cause:** Negative values were entered for hourly volume or energy quantities.

**Resolution:** Hourly measurements must be non-negative. If gas flows in the opposite direction, use the POV code to indicate delivery direction rather than negative values.

**Code Location:**
- `Quorum.QPTM.Validations/Screens/HourlyMeasurementMaintenance/Validation Rules/QPTMValidationHourlyMeasurementMaintenance003_ValidateQtyDisplay.cs`

---

### Error: "Accounting month for a PPA must be the current open accounting month"

**Validation Rule:** `QPTMValidationHourlyMeasurementMaintenance001_ValidateMandatory`

**Root Cause:** For hourly records where ProdMth < OpenMeasMth (a PPA scenario), the AcctgMth must equal the current open measurement month.

**Resolution:** Set the accounting month to the current open measurement month when entering PPA hourly measurements.

---

### Error: "Accounting Month must be equal to Production Month"

**Validation Rule:** `QPTMValidationHourlyMeasurementMaintenance001_ValidateMandatory`

**Root Cause:** For current or future production months, the accounting month (adjusted by lag time) must equal the production month. The rule checks: `AcctgMth - AcctMthLagTime == ProdMth`.

**Resolution:** Verify the ACCTG_MTH_LAG_TIME setting and ensure the accounting month is correctly aligned:
```sql
SELECT * FROM TSP_CONFIG_CTRL
WHERE TSP_NO = @TspNo AND CONFIG_CATEGORY = 'TSP' AND KEY_NM = 'ACCTG_MTH_LAG_TIME'
```

---

### Issue: Hourly grid shows null/empty values for some hours

**Root Cause:** This is expected. The `IsOverride` flag distinguishes real records from placeholders:
- `IsOverride = true`: Record exists in database (shows actual values)
- `IsOverride = false`: Placeholder based on hour profile (shows null for EngQtyDisplay and VolQtyDisplay)

When a user enters data in a placeholder row, `IsOverride` is set to true.

**Code Location:**
- `MeasuredVolumeHourlyDOExt.cs`, `EngQtyDisplay` and `VolQtyDisplay` getters check `m_bIsOverride`

---

## By Month Distribution Issues

### Issue: "By Month" button is disabled / shows warning

**Error String:** `Constants.MeasurementEntry.ValidationMessage.WarningByMonthBtn`

**Root Cause:** The BulkContainer has no items (the grid is empty). You must query data first to populate gas days before using By Month distribution.

**Resolution:** Query measurement data for the production month first, then use the By Month feature.

**Code Location:**
- `MeasurementEntryController.cs`, `CheckByMonthBtn()` method

---

### Issue: By Month distribution produces uneven values

**Root Cause:** When the total volume does not divide evenly by the number of days, the system distributes the remainder by adding/subtracting 1 unit to the last N days where N is the remainder.

**Example:** Total MCF = 100, Days = 31
- First 28 days: 3 MCF each (3 x 28 = 84)
- Last 3 days: 4 MCF each + 1 (adding remainder of 16 across trailing days)

**Resolution:** This is by design. Review and adjust individual day values after distribution if more precise distribution is needed.

**Code Location:**
- `QUIControllerMeasurementEntry.cs`, `CalculateByMonth()` method

---

## Aggregate Location Issues

### Issue: Save button is disabled for a location

**Root Cause:** The location is a parent (aggregate) location and `AllowAggregateEntry` global config is false. The Save button's `Enabled` property is set to `!(!allowAggregateEntry && isParentLocation)`.

**Resolution:**
1. Enter data at child location level instead
2. Or enable the global config if aggregate entry is required

**Code Location:**
- `MeasurementEntryController.cs`, `GetActions()` method
- Config: `QPTMGlobalConfigs.AllowAggregateEntry`

---

### Issue: Batch process not rolling up child volumes to parent

**Root Cause:** The rollup batch process (`BATCHID_ESUITE_VOL_IMPORT`) may not have been triggered or may have failed.

**Diagnostic Steps:**
1. Check if AllowAggregateEntry is true (rollup is skipped when true)
2. Check if the location is a parent (rollup is also skipped for parent locations)
3. Verify the batch process was launched and check its status in the process queue
4. Verify parent-child relationship:
   ```sql
   SELECT * FROM PA_LOC_AGGR
   WHERE TSP_NO = @TspNo AND CHILD_LOC_ID = @ChildLocId
   AND EFF_DT_FROM <= @ProdMth AND EFF_DT_TO >= @ProdMth
   ```

**Code Location:**
- Rollup trigger: `QUIControllerMeasurementEntry.cs`, `UpdateParentLocation()` method
- Batch launch: `QUIControllerMeasurementEntry.cs`, `LaunchBatchProcess()` method

---

### Issue: "Entries for this aggregate location could be overwritten during the next import"

**Error String:** `Constants.MeasurementEntry.ValidationMessage.WarningAgreegateLocation`

**Root Cause:** This is a warning (not an error) shown when `IsParentLocation = true` and `AllowAggregateEntry = true`. It warns that importing volume data may overwrite manual entries at the aggregate location.

**Resolution:** This is informational. The user can choose to continue or cancel.

---

## Bidirectional Location Issues

### Issue: POV column is read-only even though location should be bidirectional

**Root Cause:** The `IsBidirectional` flag is determined by checking the location's POV code at the effective date of the production month, not the global as-of date.

**Diagnostic Steps:**
1. Check location POV at the production month date:
   ```sql
   SELECT LOC_ID, POV_CD, EFF_DT_FROM, EFF_DT_TO FROM PA_LOC
   WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc
   AND EFF_DT_FROM <= @ProdMth AND EFF_DT_TO >= @ProdMth
   ```
2. Verify `POV_CD = 'B'` for the effective period covering the production month

**Code Location:**
- `QPTMServiceCore_MeasurementEntry.cs`, `AddAdditionalPropertiesMeasurementEntry()` - sets `IsBidirectional`
- `MeasurementEntryController.cs`, `UpdateControlStates()` - controls POV column editability

---

### Issue: Volume totals are incorrect for bidirectional locations

**Root Cause:** The total calculation subtracts delivery volumes from receipt volumes. If `LocPovCd` (location-level POV) is "D" (Delivery) for a bidirectional location, volumes are subtracted from the total.

**Diagnostic Steps:**
1. Check the `LocPovCd` being set on each record
2. Verify the location POV mapping:
   ```sql
   SELECT LOC_ID, POV_CD, EFF_DT_FROM, EFF_DT_TO FROM PA_LOC
   WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc
   ORDER BY EFF_DT_FROM
   ```

**Code Location:**
- Total calculation: `QUIControllerMeasurementEntry.cs`, `GetTotal()` method
- LocPovCd assignment: `QPTMServiceCore_MeasurementEntry.cs`, `AddAdditionalPropertiesMeasurementEntry()` (line with `measuredVolume.LocPovCd = location?.PovCode`)

**Known Issue:** The LocPovCd assignment uses `location.EffDateFrom >= measuredVolume.GasDay` which may not correctly match the effective date range. The condition should likely use `<=` for EffDateFrom. Check if this logic is producing unexpected results for locations with multiple effective periods.

---

## Accounting Month Issues

### Issue: Cannot change accounting month on existing records

**Root Cause:** The `PreProcessData` method handles accounting month changes with a complex delete+add pattern:
- If original AcctgMth < CurrentBillAcctMonth: creates a new record (clone)
- If new AcctgMth >= CurrentBillAcctMonth or < original: deletes old + creates new

This process can fail silently or create unexpected behavior if the control table already has a record for the new AcctgMth.

**Diagnostic Steps:**
1. Check what AcctgMth values exist:
   ```sql
   SELECT GAS_DAY, ACCTG_MTH, VOL_QTY, ENG_QTY FROM ALCTRL_MEAS_VOL
   WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc
   AND GAS_DAY BETWEEN @ProdMthStart AND @ProdMthEnd
   ORDER BY GAS_DAY, ACCTG_MTH
   ```

**Code Location:**
- `QUIControllerMeasurementEntry.cs`, `PreProcessData()` method

---

## PPA Reallocation Issues

### Issue: PPA dialog not appearing after save

**Root Cause:** PPA events are only created when:
1. There are actual changes (modified or added records)
2. The QIC service returns `ReallocateSelectDO` or `ReallocatePPAEventDO` objects
3. The JavaScript callback `IsShowPPAReallocationDialog` fires correctly

**Diagnostic Steps:**
1. Check if the save actually modified records (no changes = no PPA)
2. Verify QIC service connectivity
3. Check for PPA events in the database:
   ```sql
   SELECT * FROM REALLOCATE_PPA_EVENT
   WHERE TSP_NO = @TspNo AND PROD_MTH = @ProdMth
   ORDER BY CTR_NO
   ```

**Code Location:**
- PPA creation: `QUIControllerMeasurementEntry.cs`, `DoSave()` method
- QIC notification: `QICService.NotifyOfChange(screenChange)`

---

### Issue: Duplicate PPA events being created

**Root Cause:** The `CreatePPAEvents` method checks for duplicates using `FindPPAEventDO`, but the duplicate check depends on the `LOG_DUPLICATE_PPAS` billing configuration.

**Diagnostic Steps:**
```sql
-- Check for duplicate PPA events
SELECT TSP_NO, CTR_NO, PROD_MTH, PPA_SRC_CD, PROCESSED_IND, APPROVE_IND, COUNT(*)
FROM REALLOCATE_PPA_EVENT
WHERE TSP_NO = @TspNo AND PROD_MTH = @ProdMth
GROUP BY TSP_NO, CTR_NO, PROD_MTH, PPA_SRC_CD, PROCESSED_IND, APPROVE_IND
HAVING COUNT(*) > 1
```

**Code Location:**
- `QPTMAllocationServiceExt_Measurement.cs`, `CreatePPAEvents()` and `InsertPPAEvent()` methods

---

## Performance Issues

### Issue: Measurement Entry query is slow

**Possible Causes:**
1. Large number of records in `ALCTRL_MEAS_VOL` for the location
2. Union query (Case 2) combining control + history tables
3. AddAdditionalProperties making multiple database calls

**Resolution:**
1. Check record counts:
   ```sql
   SELECT COUNT(*) FROM ALCTRL_MEAS_VOL
   WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc

   SELECT COUNT(*) FROM ALHIST_MEAS_VOL
   WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc
   ```
2. Ensure proper indexes exist on PK columns (TSP_NO, LOC_ID, GAS_DAY, ACCTG_MTH)
3. Review if the IsUnion case is triggered unnecessarily

---

### Issue: Hourly measurement query returns null

**Root Cause:** The `GetHourlyMeasurement` method catches all exceptions and returns null:
```csharp
catch (Exception)
{
    return null;
}
```

**Resolution:** This swallowed exception pattern makes debugging difficult. Check:
1. Hour profile exists for the TSP (most common cause)
2. Database connectivity
3. Data access service registration in the DI container

**Code Location:**
- `QPTMAllocationServiceExt_Measurement.cs`, `GetHourlyMeasurement()` method

---

## Integration Issues

### Issue: FlowCal imported data cannot be edited

**Root Cause:** FlowCal imports set `AccuracyCode = "A"` (Actual). If `AllowChangeActualVolumes` is false, these records are locked from editing.

**Resolution:**
1. Check the volume source code:
   ```sql
   SELECT VOL_SRC_CD, ACCURACY_CD FROM ALCTRL_MEAS_VOL
   WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc AND GAS_DAY = @GasDay
   ```
2. If editing is required, enable `AllowChangeActualVolumes` temporarily or through proper configuration change

---

### Issue: Measurement close dates not showing in widget

**Root Cause:** The `GetMeasurementCloseDates` method filters calendar dates to the current month.

**Diagnostic Steps:**
```sql
SELECT * FROM CALENDAR_DT
WHERE TSP_NO = @TspNo AND CALENDAR_DT_TYPE = 'MeasurementClose'
ORDER BY CALENDAR_DT
```

**Code Location:**
- `QPTMMeasurementCloseScheduleWidgetService.cs`, `GetMeasurementCloseDates()` method
- Calendar date type: `Constants.CalendarDateType.MeasurementClose`

---

## Diagnostic SQL Queries

### Check Measurement Data for a Location

```sql
-- Daily measurements (control table)
SELECT TSP_NO, LOC_ID, GAS_DAY, ACCTG_MTH, PROD_MTH,
       VOL_QTY, ENG_QTY, BTU_FACTOR, ACCURACY_CD, POV_CD,
       VOL_SRC_CD, PRNT_AGGR_LOC_ID, USER_ID, UPDT_DT
FROM ALCTRL_MEAS_VOL
WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc
AND GAS_DAY BETWEEN @StartDate AND @EndDate
ORDER BY GAS_DAY, ACCTG_MTH DESC

-- Daily measurements (history table)
SELECT TSP_NO, LOC_ID, GAS_DAY, ACCTG_MTH, PROD_MTH,
       VOL_QTY, ENG_QTY, BTU_FACTOR, ACCURACY_CD, POV_CD,
       LATEST_IND, CHANGE_TYPE_CD, CHANGE_DT, CHANGE_USER_ID
FROM ALHIST_MEAS_VOL
WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc
AND GAS_DAY BETWEEN @StartDate AND @EndDate
ORDER BY GAS_DAY, ACCTG_MTH DESC, HIST_IDX DESC
```

### Check Hourly Measurement Data

```sql
-- Hourly measurements (control table)
SELECT TSP_NO, LOC_ID, GAS_DAY, HOUR_ID, ACCTG_MTH,
       VOL_QTY, ENG_QTY, BTU_FACTOR, ACCURACY_CD, POV_CD
FROM ALCTRL_MEAS_VOL_HRLY
WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc AND GAS_DAY = @GasDay
ORDER BY HOUR_ID, ACCTG_MTH DESC

-- Hourly measurements (history table)
SELECT TSP_NO, LOC_ID, GAS_DAY, HOUR_ID, ACCTG_MTH,
       VOL_QTY, ENG_QTY, BTU_FACTOR, LATEST_IND
FROM ALHIST_MEAS_VOL_HRLY
WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc AND GAS_DAY = @GasDay
ORDER BY HOUR_ID, ACCTG_MTH DESC
```

### Check Location Configuration

```sql
-- Location details
SELECT LOC_ID, LOC_NM, POV_CD, VOL_UOM_CD, ENG_UOM_CD,
       EFF_DT_FROM, EFF_DT_TO, OTH_VOL_UOM_CD
FROM PA_LOC
WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc
ORDER BY EFF_DT_FROM

-- Location attributes (OtherUOM)
SELECT * FROM PA_LOC_ATTR
WHERE TSP_NO = @TspNo AND LOC_ID = @IdLoc
AND LOC_ATTR_CD = 'OtherUOM'
ORDER BY EFF_DT_FROM

-- Aggregate location relationships
SELECT LOC_ID AS ParentLoc, CHILD_LOC_ID, EFF_DT_FROM, EFF_DT_TO
FROM PA_LOC_AGGR
WHERE TSP_NO = @TspNo
AND (LOC_ID = @IdLoc OR CHILD_LOC_ID = @IdLoc)
ORDER BY EFF_DT_FROM
```

### Check Hour Profile

```sql
SELECT TSP_NO, ID_HOUR, HOUR, HR_ORDER
FROM HOUR_PROFILE
WHERE TSP_NO = @TspNo
ORDER BY HR_ORDER
```

### Check TSP Configuration

```sql
-- Accounting month lag time
SELECT * FROM TSP_CONFIG_CTRL
WHERE TSP_NO = @TspNo AND CONFIG_CATEGORY = 'TSP'
AND KEY_NM = 'ACCTG_MTH_LAG_TIME'

-- PPA approval indicator
SELECT * FROM TSP_CONFIG_CTRL
WHERE TSP_NO = @TspNo AND CONFIG_CATEGORY = 'TSP'
AND KEY_NM = 'PPA_APPROVE_IND'
```

### Check Global Configuration

```sql
SELECT CONFIG_CATEGORY, KEY_NM, KEY_VALUE
FROM GLOBAL_CONFIG_CTRL
WHERE CONFIG_CATEGORY IN ('MEASUREMENT ENTRY', 'BILLING')
AND KEY_NM IN ('ALLOW_AGGREGATE_VOLUME_ENTRY', 'ALLOW_CHANGE_ACTUAL_VOL',
               'ALLOW_CHANGE_VOL_TO_EST', 'LOG_DUPLICATE_PPAS')
```

### Check PPA Events

```sql
SELECT TSP_NO, CTR_NO, PROD_MTH, LOC_ID, PPA_SRC_CD,
       TRIGGER_SRC_CD, PROCESSED_IND, APPROVE_IND
FROM REALLOCATE_PPA_EVENT
WHERE TSP_NO = @TspNo AND PROD_MTH = @ProdMth
ORDER BY CTR_NO
```

---

## Key File Locations

### Service Layer

| File | Path |
|---|---|
| Measurement Entry Service | `Quorum.QPTM.ServiceCore/QPTMServiceCore_MeasurementEntry.cs` |
| Hourly/Allocation Measurement Service | `Quorum.QPTM.ServiceCore.Allocation/QPTMAllocationServiceExt_Measurement.cs` |
| Measurement Close Widget Service | `Quorum.QPTM.ServiceCore.Allocation/QPTMMeasurementCloseScheduleWidgetService.cs` |
| Service Interface | `Quorum.QPTM.ServiceInterface/IQPTMServiceInterface_MeasurementEntry.cs` |

### Controllers

| File | Path |
|---|---|
| Measurement Entry Controller | `Quorum.QPTM.Web.Core/Controllers/MeasurementEntryController.cs` |
| Measurement Results Controller | `Quorum.QPTM.Web.Core/Controllers/MeasurementResultsController.cs` |
| Hourly Measurement Controller | `Quorum.QPTM.Web.Core/Controllers/HourlyMeasurementMaintenanceController.cs` |

### UI Controllers

| File | Path |
|---|---|
| Measurement Entry UI Controller | `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerMeasurementEntry.cs` |
| Hourly Measurement UI Controller | `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerHourlyMeasurementMaintenance.cs` |

### Data Objects

| File | Path |
|---|---|
| MeasuredVolumeDO Extension | `Quorum.QPTM.DataObject/MeasuredVolumeDOExt.cs` |
| MeasuredVolumeHourlyDO Extension | `Quorum.QPTM.DataObject/MeasuredVolumeHourlyDOExt.cs` |
| MeasuredVolumeDO CodeGen | `Quorum.QPTM.DataObject/CodeGen/MeasuredVolumeDO.cs` |
| MeasuredVolumeHourlyDO CodeGen | `Quorum.QPTM.DataObject/CodeGen/MeasuredVolumeHourlyDO.cs` |
| MeasuredVolumeHistoryDO CodeGen | `Quorum.QPTM.DataObject/CodeGen/MeasuredVolumeHistoryDO.cs` |

### View Models

| File | Path |
|---|---|
| MeasurementEntryRootVM | `Quorum.QPTM.Web.Core/ViewModels/MeasurementEntryRootVM.cs` |
| MeasurementResultsRootVM | `Quorum.QPTM.Web.Core/ViewModels/MeasurementResultsRootVM.cs` |
| HourlyMeasurementMaintenanceRootVM | `Quorum.QPTM.Web.Core/ViewModels/HourlyMeasurementMaintenanceRootVM.cs` |
| MeasurementCloseWidgetVM | `Quorum.QPTM.Web.Core/ViewModels/MeasurementCloseWidgetVM.cs` |
| MeasuredVolumeVM (CodeGen) | `Quorum.QPTM.Web.Core/ViewModels/CodeGen/MeasuredVolumeVM.cs` |

### Validation Rules

| File | Path |
|---|---|
| Validation Context | `Quorum.QPTM.Validations/Screens/MeasurementEntry/Context/QPTMValidationContext_MeasurementEntry.cs` |
| Rule 001 - Aggregate | `Quorum.QPTM.Validations/Screens/MeasurementEntry/Validation Rules/QPTMValidationMeasurementEntry001_ValidateAggregateVolumeEntry.cs` |
| Rule 002 - Accuracy | `Quorum.QPTM.Validations/Screens/MeasurementEntry/Validation Rules/QPTMValidationMeasurementEntry002_ValidateAccuracyCode.cs` |
| Rule 003 - AcctgMth | `Quorum.QPTM.Validations/Screens/MeasurementEntry/Validation Rules/QPTMValidationMeasurementEntry003_ValidateAccountingMonth.cs` |
| Rule 004 - Bidirectional | `Quorum.QPTM.Validations/Screens/MeasurementEntry/Validation Rules/QPTMValidationMeasurementEntry004_ValidateBidirectionalLocations.cs` |
| Rule 005 - GasDay | `Quorum.QPTM.Validations/Screens/MeasurementEntry/Validation Rules/QPTMValidationMeasurementEntry005_ValidateGasDay.cs` |
| Rule 006 - Location | `Quorum.QPTM.Validations/Screens/MeasurementEntry/Validation Rules/QPTMValidationMeasurementEntry006_ValidateLocation.cs` |
| Hourly Rule 001 | `Quorum.QPTM.Validations/Screens/HourlyMeasurementMaintenance/Validation Rules/QPTMValidationHourlyMeasurementMaintenance001_ValidateMandatory.cs` |
| Hourly Rule 003 | `Quorum.QPTM.Validations/Screens/HourlyMeasurementMaintenance/Validation Rules/QPTMValidationHourlyMeasurementMaintenance003_ValidateQtyDisplay.cs` |

### Constants

| File | Path |
|---|---|
| Constants (Security IDs, Screen IDs, etc.) | `Quorum.QPTM.CoreInterface/Constants.cs` |

### Unit Tests

| File | Path |
|---|---|
| Measurement Entry Tests | `Quorum.QPTM.UnitTests/MeasurementEntry/MeasurementEntryTests.cs` |
| Measurement Entry Tests (No Context) | `Quorum.QPTM.UnitTests/MeasurementEntry/MeasurementEntryTests_NoContext.cs` |
| Measurement Close Unit Tests | `Quorum.QPTM.QPTMUnitTests/AllocationsWidgets/Measurement Close/MeasurementCloseUnitTests.cs` |

---

*Last updated: 2026-03-03*

*Document version: 1.0*
