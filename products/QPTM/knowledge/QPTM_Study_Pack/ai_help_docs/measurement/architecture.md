---
title: Measurement (MEAS) - Technical Architecture
category: architecture
feature: Measurement (MEAS)
related_repos: Web, Batch
keywords: MEAS, measurement, QPTMServiceCore_MeasurementEntry, MeasurementEntryController, MeasurementResultsController, HourlyMeasurementMaintenanceController, QPTMAllocationServiceExt_Measurement, MeasuredVolumeDO, MeasuredVolumeHourlyDO, ALCTRL_MEAS_VOL, ALHIST_MEAS_VOL, validation, UIController
last_updated: 2026-03-03
---

# Measurement (MEAS) - Technical Architecture

## Overview

This document describes the **technical architecture** of the Measurement (MEAS) feature in the QPTM system. It covers the service layer, controllers, data objects, database tables, validation rules, and configuration.

For business concepts, see [Domain Documentation](./domain.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Service Layer](#service-layer)
3. [Web Controllers (MVC)](#web-controllers-mvc)
4. [UI Controllers](#ui-controllers)
5. [Data Objects](#data-objects)
6. [View Models](#view-models)
7. [Database Tables](#database-tables)
8. [Data Access Layer](#data-access-layer)
9. [Validation Rules](#validation-rules)
10. [Configuration Settings](#configuration-settings)
11. [Batch Processes](#batch-processes)
12. [Integration Points](#integration-points)
13. [Security](#security)
14. [Key Code Paths](#key-code-paths)

---

## Architecture Overview

```
Layer               Component                                     Namespace
-----------         -----------------------------------------     ----------------------------------
Web (MVC)           MeasurementEntryController                    Quorum.QPTM.Web.Controllers
                    MeasurementResultsController                  Quorum.QPTM.Controllers
                    HourlyMeasurementMaintenanceController        Quorum.QPTM.Controllers

UI Controller       QUIControllerMeasurementEntry                 Quorum.QPTM.Controllers
                    QUIControllerMeasurementResults               Quorum.QPTM.Controllers
                    QUIControllerHourlyMeasurementMaintenance     Quorum.QPTM.Controllers

Service             QPTMServiceCore (partial)                     Quorum.QPTM.ServiceCore
                    QPTMAllocationService (partial)               Quorum.QPTM

Data Object         MeasuredVolumeDO / MeasuredVolumeDOExt        Quorum.QPTM.DataObject
                    MeasuredVolumeHourlyDO / DOExt                Quorum.QPTM.DataObject
                    MeasuredVolumeHistoryDO                       Quorum.QPTM.DataObject
                    MeasuredVolumeHistoryHourlyDO                 Quorum.QPTM.DataObject
                    MeasurementEntryData                          Quorum.QPTM.DataObject

View Model          MeasurementEntryRootVM                        Quorum.QPTM.Web.ViewModels
                    MeasurementResultsRootVM                      Quorum.QPTM.Web.ViewModels
                    HourlyMeasurementMaintenanceRootVM            Quorum.QPTM.Web.ViewModels
                    MeasuredVolumeVM                              Quorum.QPTM.Web.ViewModels
                    MeasuredVolumeHourlyVM                        Quorum.QPTM.Web.ViewModels

Validation          QPTMValidationMeasurementEntry001-006         Quorum.QPTM.Validation
                    QPTMValidationHourlyMeasurementMaint001-004   Quorum.QPTM.Validation

DAL                 MeasuredVolumeDAL                             Quorum.QPTM.DAL
                    MeasuredVolumeHourlyDAL                       Quorum.QPTM.DAL
                    MeasuredVolumeHistoryDAL                      Quorum.QPTM.DAL
                    MeasuredVolumeHistoryHourlyDAL                Quorum.QPTM.DAL
```

---

## Service Layer

### QPTMServiceCore_MeasurementEntry

**File:** `Quorum.QPTM.ServiceCore/QPTMServiceCore_MeasurementEntry.cs`
**Interface:** `IQPTMService_MeasurementEntry`
**Class:** `QPTMServiceCore` (partial class)

This is the core service for daily measurement CRUD operations. Key methods:

#### Query Methods

| Method | Description |
|---|---|
| `GetSingleMeasurementEntry(MeasurementEntryData)` | Main query method. Routes to control table or history table based on ProdMth vs CurrentBillAcctMonth |
| `GetSingleMeasurementEntryStreaming(QStreamedMessage)` | Streaming wrapper for `GetSingleMeasurementEntry` |

**Query Routing Logic (3 cases):**

```
Case 1: ProdMth >= CurrentBillAcctMonth
  -> Query ALCTRL_MEAS_VOL (control table)
  -> Filter by AcctgMth <= selected AcctgMth, group by GasDay taking latest AcctgMth

Case 2: ProdMth < CurrentBillAcctMonth AND AcctgMth >= CurrentBillAcctMonth
  -> Query ALCTRL_MEAS_VOL (control table) + ALHIST_MEAS_VOL (history, IsLatest only)
  -> IsUnion = true (combines current and historical data)

Case 3: ProdMth < CurrentBillAcctMonth AND AcctgMth < CurrentBillAcctMonth
  -> Query ALHIST_MEAS_VOL (history table only)
  -> Filter by AcctgMth <= selected AcctgMth, group by GasDay taking latest AcctgMth
```

#### Update Methods

| Method | Description |
|---|---|
| `UpdateSingleMeasurementEntry(MeasurementEntryData)` | Validates then saves via `IQPTMDataAccess_MeasuredVolume.UpdateMultipleMeasuredVolume()` |
| `UpdateSingleMeasurementEntryStreaming(QStreamedMessage)` | Streaming wrapper |

#### Validate Methods

| Method | Description |
|---|---|
| `ValidateSingleMeasurementEntry(MeasurementEntryData, enActionContext)` | Entry point for validation |
| `ValidateSingleMeasurementEntryInternal(MeasurementEntryData, enActionContext)` | Clears errors, creates `QMeasurementEntryValidationContext`, runs validation rules |

#### Additional Property Methods

| Method | Description |
|---|---|
| `AddAdditionalPropertiesMeasurementEntry(MeasurementEntryData)` | Enriches data with: location POV code, OtherUOM flag, bidirectional flag, parent/child location info, fills missing gas days |
| `GetLocationByTspNoLocId(tspNo, idLoc)` | Retrieves PALocation records for the given TSP/location |
| `GetLocationAttribute(tspNo, idLoc, locAttrCode, effDateFrom)` | Gets location attributes (e.g., OtherUOM) |
| `GetPALocationAggregateChildLocs(tspNo, idLoc, prodMth)` | Checks if location is a parent (has child locations) |
| `GetPALocationAggregateParentLoc(tspNo, idLoc, prodMth)` | Gets the parent location ID for a child location |
| `GetPALocationVolUOM(tspNo, idLoc, effDateFrom)` | Gets location volume UOM configuration |
| `GetPALocationMinMaxKeyDates(tspNo, idLoc)` | Gets all location records for min/max date validation |

### QPTMAllocationServiceExt_Measurement

**File:** `Quorum.QPTM.ServiceCore.Allocation/QPTMAllocationServiceExt_Measurement.cs`
**Class:** `QPTMAllocationService` (partial class)

Handles hourly measurement operations and PPA event creation. Key methods:

#### Hourly Measurement Methods

| Method | Signature | Description |
|---|---|---|
| `GetHourlyMeasurement` | `(short tspNo, string locId, DateTime gasDay, DateTime acctgMonth)` | Retrieves hourly measurement data using 3-case routing (same pattern as daily) |
| `UpdateHourlyMeasurement` | `(List<MeasuredVolumeHourlyDO>)` | Saves hourly data with aggregate rollup support |
| `GetOpenAccountingMonth` | `(short tspNo)` | Returns the current open accounting month from ALDataAccess |
| `GetOpenMeasurementMonth` | `(short tspNo)` | Returns the current open measurement month from ALDataAccess |
| `GetTSPPreferences` | `(short tspNo)` | Returns TSP preferences (UOM codes, formats) from TspCache |

#### Hourly Query Routing Logic (3 cases)

```
Case 1: gasDay >= openProdMonth AND acctgMonth >= openAcctgMonth
  -> Query ALCTRL_MEAS_VOL_HRLY (control table)
  -> GetLatestMeasurement removes duplicates keeping latest AcctgMth per HourId

Case 2: gasDay < openProdMonth AND acctgMonth >= openAcctgMonth
  -> Query ALCTRL_MEAS_VOL_HRLY + ALHIST_MEAS_VOL_HRLY (IsLatest = true)
  -> Combines current and historical hourly data

Case 3: gasDay < openProdMonth AND acctgMonth < openAcctgMonth
  -> Query ALHIST_MEAS_VOL_HRLY (history only)
  -> GetLatestMeasurement removes duplicates
```

#### Update Logic (UpdateHourlyMeasurement)

1. Checks `ALLOW_AGGREGATE_VOLUME_ENTRY` global config
2. If aggregate entry is not allowed, checks for parent location
3. Filters out unchanged records, newly added nulls, and negative values
4. Saves via `MeasuredVolumeHourly.SaveList()`
5. If child location has a parent, performs `RollAggregateLocations()` rollup

#### PPA Event Methods

| Method | Description |
|---|---|
| `CreatePPAEvents(Dictionary<string, MeasuredVolumeHourlyDO>, string)` | Creates PPA events for contracts associated with changed measurement locations |
| `CreatePPAEventDO(...)` | Builds individual PPA event records |
| `InsertPPAEvent(Dictionary, ref string, bool)` | Inserts PPA events after checking for duplicates |
| `FindPPAEventDO(BindingListView, ReallocatePPAEventDO, bool)` | Finds existing PPA events to prevent duplicates |

### QPTMMeasurementCloseScheduleWidgetService

**File:** `Quorum.QPTM.ServiceCore.Allocation/QPTMMeasurementCloseScheduleWidgetService.cs`
**Interface:** `IQPTMMeasurementCloseScheduleWidget`

| Method | Description |
|---|---|
| `GetMeasurementCloseDates(short tspNo)` | Retrieves upcoming measurement close dates from CalendarDate table, filtered to current month |

---

## Web Controllers (MVC)

### MeasurementEntryController

**File:** `Quorum.QPTM.Web.Core/Controllers/MeasurementEntryController.cs`
**Security:** `QScreenSecurityObject(Constants.SecurityObjectIDs.MeasurementEntry)` = `"QVPMEASUREMENTENTRY"`
**Base Class:** `AllocationControllerBase<QUIControllerMeasurementEntry, MeasurementEntryRootVM>`

#### Actions and Links

| Element | Description |
|---|---|
| **By Month Button** | `BtnByMonth` action, opens monthly distribution popup |
| **Query Button** | Standard query, text from `QPTMGlobalConfigs.QueryBtnText` |
| **Save Button** | Custom JS `ValidateBeforeSave`, disabled if parent location and aggregate entry not allowed |
| **Hourly Measurement Link** | Hidden link, navigates to HourlyMeasurementMaintenance with selected gas day context |

#### Key Endpoints

| Endpoint | HTTP | Description |
|---|---|---|
| `MeasurementEntryFieldUpdate` | POST | Updates UI controller fields |
| `ByMonthPopupFieldUpdate` | POST | Updates By Month popup fields |
| `MeasurementEntryGetData` | POST | Grid data retrieval with Kendo DataSourceRequest |
| `MeasurementEntryGridUpdate` | POST | Grid row update |
| `MeasurementEntryGridDeleteRow` | POST | Grid row deletion |
| `MeasurementEntryGridExcelExport` | GET | Excel export |
| `MeasurementEntryGridBulkEdit` (GET) | GET | Bulk edit export |
| `MeasurementEntryGridBulkEdit` (PUT) | PUT | Bulk edit import |
| `ShowBtnByMonthPopup` | GET | Returns By Month popup partial view |
| `ClearMeasuredList` | POST | Clears grid when key fields change |
| `UpdateByMonthData` | POST | Auto-calculates By Month fields |
| `CalculateByMonth` | POST | Distributes By Month values across gas days |
| `CheckAggregate` | POST | Checks if location is aggregate with entry allowed |
| `CheckByMonthBtn` | POST | Validates By Month button availability |
| `SetSelectedMeasuredVolume` | GET | Sets selected row for hourly link navigation |
| `PositionColumnHiddenState` | JSON | Controls position column visibility |

#### Control States Logic

The `UpdateControlStates` method determines which columns are read-only based on:
- **Auto-populate column**: The MeasOption-calculated column is always read-only
- **Aggregate parent**: If parent location and AllowAggregateEntry is false, all editable columns become read-only
- **Bidirectional POV**: POV column is read-only unless the location is bidirectional AND aggregate entry is allowed

### MeasurementResultsController

**File:** `Quorum.QPTM.Web.Core/Controllers/MeasurementResultsController.cs`
**Security:** `QScreenSecurityObject(Constants.SecurityObjectIDs.MeasurementResults)` = `"QVPMEASUREMENTRESULTS"`
**Base Class:** `AllocationControllerBase<QUIControllerMeasurementResults, MeasurementResultsRootVM>`

#### Key Endpoints

| Endpoint | HTTP | Description |
|---|---|---|
| `MeasurementResultsFieldUpdate` | POST | Field update handler |
| `MeasurementResultsGetData` | POST | Grid data, applies POV-based sign reversal for non-receipt locations |
| `MeasurementResultsExcelExport` | GET/POST | Excel export |
| `MeasurementResultsBulkEdit` (GET) | GET | Bulk edit export (VolQty and EngQty are read-only) |
| `MeasurementResultsBulkEdit` (PUT) | PUT | Bulk edit import |

#### Special Behavior

- Grid data applies sign reversal: if `PovCode != Receipt` and `MeasResultsByPOV` TSP config is true, `EngQty` and `VolQty` are negated
- Links to **Location Maintenance** screen with context parameters (TspNo, LocId, date range)
- Context data provides Energy and Volume UOM from TSP preferences

### HourlyMeasurementMaintenanceController

**File:** `Quorum.QPTM.Web.Core/Controllers/HourlyMeasurementMaintenanceController.cs`
**Security:** `QScreenSecurityObject(Constants.SecurityObjectIDs.HourlyMeasurementEntry)` = `"QVPSOAHOURLYMEASUREMENTENTRY"`
**Base Class:** `AllocationControllerBase<QUIControllerHourlyMeasurementMaintenance, HourlyMeasurementMaintenanceRootVM>`

#### Key Endpoints

| Endpoint | HTTP | Description |
|---|---|---|
| `HourlyMeasurementMaintenanceFieldUpdate` | POST | Field update |
| `HourlyMeasurementMaintenanceGetData` | POST | Grid data with control states |
| `HourlyMeasurementMaintenanceUpdate` | POST | Grid row update, returns totals in OtherChanges |
| `HourlyMeasurementMaintenanceDeleteRow` | POST | Grid row deletion |
| `HourlyMeasurementMaintenanceExcelExport` | GET | Excel export |
| `HourlyMeasurementMaintenanceBulkEdit` (GET) | GET | Bulk edit export |
| `HourlyMeasurementMaintenanceBulkEdit` (PUT) | PUT | Bulk edit import |
| `ClearMeasuredList` | POST | Clears grid on key field change |

#### Control States

| Property | Condition for Read-Only |
|---|---|
| `PovCode` | Not bidirectional location |
| `BtuFactor` | MeasOption is HeatingFactor (BTU) |
| `EngQtyDisplay` | MeasOption is Energy (DTH) |
| `VolQtyDisplay` | MeasOption is Volume (MCF) |

#### Links

- **Measurement Entry**: Links back to daily measurement entry with context (TspNo, ProdMth, IdLoc, AcctgMth)
- **Save Action**: Custom post-callback `IsShowPPAReallocationDialog` for PPA handling

---

## UI Controllers

### QUIControllerMeasurementEntry

**File:** `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerMeasurementEntry.cs`
**Security:** `QSecurityObject(Constants.SecurityObjectIDs.MeasurementEntry)`
**Base Class:** `QPTMBulkInterfaceControllerBase<MeasuredVolumeDO>`

#### Key Properties

| Property | Type | Description |
|---|---|---|
| `MeasurementEntryData` | `MeasurementEntryData` | Main data container |
| `SelectedMeasuredVolume` | `MeasuredVolumeDO` | Currently selected grid row |
| `AllowAggregateEntry` | `bool` | From `QPTMGlobalConfigs.AllowAggregateEntry` |
| `PositionColumnState` | `bool` | Controls position column visibility |

#### Controller Lifecycle

| Method | Description |
|---|---|
| `DoNew()` | Initializes MeasurementEntryData, sets TspNo, calls SetDefaults |
| `ReadyForQuery()` | Validates required fields (IdLoc, ProdMth, AcctgMth), checks ProdMth <= AcctgMth |
| `DoQuery()` | Calls `Service.GetSingleMeasurementEntry()`, populates BulkContainer |
| `DoSave()` | Calls `PrepareForUpdate()`, `Service.UpdateSingleMeasurementEntry()`, triggers PPA via QIC |
| `PreSave()` | Validates mandatory fields (AcctgMth, BtuFactor, AccuracyCode) based on MeasOption |

#### Auto-Populate (CalculateAutoPopulateColumns)

For each changed item in BulkContainer:
- **BTU mode**: `BtuFactor = CalcBTUFactor()` from VolQty and EngQty
- **DTH mode**: `EngQty = CalcEngQty()` from VolQty and BtuFactor
- **MCF mode**: `VolQty = CalcVolQty()` from EngQty and BtuFactor

Handles both standard UOM (VolQty/BtuFactor) and OtherUOM (OthVolQty/ConvFactor).

#### PreProcessData Logic

Handles accounting month changes:
- If AcctgMth changed and original was before CurrentBillAcctMonth: clone as new record
- If AcctgMth changed to current/future billing month: delete old + clone as new
- Added records with no VolQty/EngQty are skipped
- All other records pass through unchanged

#### Batch Process (UpdateParentLocation)

After save, if no errors and not aggregate parent:
1. Collects AcctgMth and GasDay lists from added/modified records
2. Launches `BATCHID_ESUITE_VOL_IMPORT` asynchronously with TSP, Location, dates
3. Uses `ParameterUseType.MultipleValues` for date lists
4. Monitors process via `QUICUtilities.AddProcessToMonitor`

#### Params Class (QControllerParamsMeasurementEntry)

Registered parameters (all AutoPush + RequiredForQuery):
- `IdLoc` (string) - Location ID
- `LocNm` (string) - Location Name
- `ProdMth` (DateTime?) - Production Month
- `AcctgMth` (DateTime?) - Accounting Month
- `MeasOption` (string) - Auto-Populate Type, defaults to `"BTU"`

Property change behavior:
- AcctgMth normalized to first day of month
- If ProdMth > AcctgMth, AcctgMth auto-adjusts to match ProdMth

---

## Data Objects

### MeasuredVolumeDO

**CodeGen file:** `Quorum.QPTM.DataObject/CodeGen/MeasuredVolumeDO.cs`
**Extension file:** `Quorum.QPTM.DataObject/MeasuredVolumeDOExt.cs`
**Table:** `ALCTRL_MEAS_VOL`

#### Key Properties

| Property | Column | Type | Description |
|---|---|---|---|
| `TspNo` | `TSP_NO` | `short` | TSP identifier (PK) |
| `IdLoc` | `LOC_ID` | `string` | Location identifier (PK) |
| `GasDay` | `GAS_DAY` | `DateTime` | Gas day (PK) |
| `AcctgMth` | `ACCTG_MTH` | `DateTime` | Accounting month (PK) |
| `ProdMth` | `PROD_MTH` | `DateTime` | Production month |
| `VolQty` | `VOL_QTY` | `decimal?` | Volume quantity |
| `EngQty` | `ENG_QTY` | `decimal?` | Energy quantity |
| `BtuFactor` | `BTU_FACTOR` | `decimal?` | BTU conversion factor |
| `OthVolQty` | `OTH_VOL_QTY` | `decimal?` | Other UOM volume |
| `ConvFactor` | `CONV_FACTOR` | `decimal?` | Other UOM conversion factor |
| `AccuracyCode` | `ACCURACY_CD` | `string` | A=Actual, E=Estimate |
| `PovCode` | `POV_CD` | `string` | Point of View (R/D) |
| `VolSrcCode` | `VOL_SRC_CD` | `string` | Volume source (MAN/FC/MPS) |
| `IdPrntAggrLoc` | `PRNT_AGGR_LOC_ID` | `string` | Parent aggregate location |
| `VolUomCode` | `VOL_UOM_CD` | `string` | Volume UOM code |
| `EngUomCode` | `ENG_UOM_CD` | `string` | Energy UOM code |
| `UserId` | `USER_ID` | `string` | Last update user |
| `UpdateDate` | `UPDT_DT` | `DateTime` | Last update timestamp |

#### Extension Properties (DOExt)

| Property | Type | Description |
|---|---|---|
| `LocPovCd` | `string` | Location-level POV code (from PALocation) |
| `OriginalUpdatedDate` | `DateTime` | Original update date before changes |
| `ShowOtherUOM` | `bool` | Whether Other UOM columns are shown |
| `PositionState` | `bool` | Position column visibility state |
| `EngQtyDisplay` | `decimal?` | Display wrapper for EngQty |
| `VolQtyDisplay` | `decimal?` | Display wrapper for VolQty |
| `OthVolQtyDisplay` | `decimal?` | Display wrapper for OthVolQty |

#### Calculation Methods (DOExt)

| Method | Formula | Notes |
|---|---|---|
| `CalcVolQty()` | `EngQty / BtuFactor` (or `EngQty / ConvFactor` for OtherUOM) | Returns 0 if factor is null/zero |
| `CalcEngQty()` | `VolQty * BtuFactor` (or `OthVolQty * ConvFactor`) | Returns 0 if factor is null/zero |
| `CalcBTUFactor()` | `EngQty / VolQty` (or `EngQty / OthVolQty`) | Returns 0 if either qty is zero |
| `LoadFromHistory(MeasuredVolumeHistoryDO)` | Maps history DO fields to current DO | Used when loading from history table |

### MeasuredVolumeHourlyDO

**CodeGen file:** `Quorum.QPTM.DataObject/CodeGen/MeasuredVolumeHourlyDO.cs`
**Extension file:** `Quorum.QPTM.DataObject/MeasuredVolumeHourlyDOExt.cs`
**Table:** `ALCTRL_MEAS_VOL_HRLY`

#### Additional Properties (DOExt)

| Property | Type | Description |
|---|---|---|
| `LocNm` | `string` | Location name |
| `Hour` | `string` | Formatted hour display ("h:mm tt") |
| `MeasHour` | `DateTime` | Hour timestamp (set-only) |
| `IsOverride` | `bool` | True = real record from DB; False = placeholder |
| `IsPPA` | `bool` | Whether this is a PPA record |
| `IsValid` | `bool` | True if both VolQtyDisplay and EngQtyDisplay have values |
| `EngQtyDisplay` | `decimal?` | Returns null if IsOverride is false; sets IsOverride on assign |
| `VolQtyDisplay` | `decimal?` | Returns null if IsOverride is false; sets IsOverride on assign |

#### Default Values

- `VolSrcCode` defaults to `Constants.VolumeSource_Manual` ("MAN")
- `AccuracyCode` defaults to `Constants.Accuracy_Actual` ("A")

### MeasuredVolumeHistoryDO / MeasuredVolumeHistoryHourlyDO

**Tables:** `ALHIST_MEAS_VOL` / `ALHIST_MEAS_VOL_HRLY`

History data objects mirror the control table structure with additional fields:
- `IsLatest` (bool): Indicates the most recent version of a record
- `ChangeTypeCode` (string): Type of change that created the history record
- `ChangeDate` (DateTime?): When the change occurred
- `IdChangeUser` (string): User who made the change

### MeasurementEntryData

A composite data transfer object that bundles query parameters and results:

| Property | Type | Description |
|---|---|---|
| `TspNo` | `short` | TSP number |
| `IdLoc` | `string` | Location ID |
| `LocNm` | `string` | Location name |
| `ProdMth` | `DateTime` | Production month |
| `AcctgMth` | `DateTime` | Accounting month |
| `MeasOption` | `string` | Auto-populate type (BTU/DTH/MCF) |
| `MeasuredVolume` | `List<MeasuredVolumeDO>` | The measurement records |
| `CurrentBillAcctMonth` | `DateTime` | Current open billing accounting month |
| `CurrentMeasAcctMonth` | `DateTime` | Current open measurement month |
| `GlobalAsOfDate` | `DateTime` | As-of date for location lookups |
| `TspPreferences` | `TspPreferencesDO` | TSP UOM and format preferences |
| `IsUnion` | `bool` | Whether data combines control + history tables |
| `ShowOtherUOM` | `bool` | Whether Other UOM is enabled for the location |
| `OtherUOM` | `string` | The Other UOM code |
| `IsBidirectional` | `bool` | Whether location is bidirectional |
| `IsParentLocation` | `bool` | Whether location is an aggregate parent |
| `IsChildLocation` | `bool` | Whether location is an aggregate child |
| `ParentLocation` | `string` | Parent location ID (if child) |
| `PovCode` | `string` | Location POV code |
| `ByMonthMethod` | `string` | By Month distribution method |
| `ByMonthVolQty` | `decimal?` | By Month volume total |
| `ByMonthEngQty` | `decimal?` | By Month energy total |
| `ByMonthBtuFactor` | `decimal?` | By Month BTU factor |

---

## View Models

### MeasurementEntryRootVM

**File:** `Quorum.QPTM.Web.Core/ViewModels/MeasurementEntryRootVM.cs`

Maps to `ALCTRL_MEAS_VOL` table columns. Additional UI properties:
- `TotalMcf`, `TotalDth`: Formatted total strings
- `ShowOtherUOM`: Controls OtherUOM column visibility
- `ByMonthMethod`, `ByMonthVolQty`, `ByMonthEngQty`, `ByMonthBtuFactor`: By Month popup data
- `McfFormat`, `BtuFormat`, `DthFormat`: TSP-specific number formatting

### MeasurementResultsRootVM

**File:** `Quorum.QPTM.Web.Core/ViewModels/MeasurementResultsRootVM.cs`

Maps to `ALHIST_MEAS_VOL` table columns. Additional properties:
- `IdLocGrp`, `IdLocGrpName`: Location group filter values
- `GasDayFrom`, `GasDayTo`: Gas day range filter
- `IsLatest`: History latest flag

### HourlyMeasurementMaintenanceRootVM

**File:** `Quorum.QPTM.Web.Core/ViewModels/HourlyMeasurementMaintenanceRootVM.cs`

Properties include:
- `TotalDth`, `TotalMcf`: Formatted hourly totals
- `AllowAggregateVolumeEntryKey`: Aggregate entry config key
- `IsAggregate`: Whether location is aggregate
- `VolUomCode`, `EngUomCode`: UOM display labels

### MeasurementCloseWidgetVM

**File:** `Quorum.QPTM.Web.Core/ViewModels/MeasurementCloseWidgetVM.cs`

Dashboard widget showing upcoming measurement close dates:
- `Measurements`: Collection of `CalendarDateDO` records

---

## Database Tables

### Control Tables (Active Data)

| Table | Description | Primary Key |
|---|---|---|
| `ALCTRL_MEAS_VOL` | Daily measured volumes | TSP_NO, LOC_ID, GAS_DAY, ACCTG_MTH |
| `ALCTRL_MEAS_VOL_HRLY` | Hourly measured volumes | TSP_NO, LOC_ID, GAS_DAY, HOUR_ID, ACCTG_MTH |
| `ALCTRL_MEAS_VOL_HRLY_LAST_SYNC` | Hourly measurement last sync timestamps | TSP_NO, LOC_ID |

### History Tables (Closed Period Data)

| Table | Description | Key Addition |
|---|---|---|
| `ALHIST_MEAS_VOL` | Daily measured volume history | + HIST_IDX, LATEST_IND |
| `ALHIST_MEAS_VOL_HRLY` | Hourly measured volume history | + HIST_IDX, LATEST_IND |

### Related Tables

| Table | Description | Usage |
|---|---|---|
| `PA_LOC` | Pipeline Administration Location | Location POV, UOM, effective dates |
| `PA_LOC_ATTR` | Location Attributes | OtherUOM flag |
| `PA_LOC_AGGR` | Location Aggregation | Parent-child location relationships |
| `PA_LOC_GRP` | Location Groups | Group-based queries |
| `CALENDAR_DT` | Calendar Dates | Measurement close schedule dates |
| `HOUR_PROFILE` | Hour Profile | TSP hour configuration for hourly measurement |
| `TSP_PREF` | TSP Preferences | UOM codes, number formats |
| `TSP_CONFIG_CTRL` | TSP Configuration Control | ACCTG_MTH_LAG_TIME, PPA_APPROVE_IND |
| `GLOBAL_CONFIG_CTRL` | Global Configuration Control | ALLOW_AGGREGATE_VOLUME_ENTRY |
| `REALLOCATE_PPA_EVENT` | PPA Reallocation Events | Triggered by measurement changes |

### View Tables

| Table | Description |
|---|---|
| `ALCTRL_MEAS_VOL_LATEST_VW` | View of latest daily measurements |
| `ALCTRL_MEAS_VOL_LATEST_PRD_VW` | View of latest daily measurements by production month |

---

## Data Access Layer

### Key Data Access Interfaces

| Interface | Description |
|---|---|
| `IQPTMDataAccess_MeasuredVolume` | CRUD for ALCTRL_MEAS_VOL |
| `IQPTMDataAccess_MeasuredVolumeHistory` | Read for ALHIST_MEAS_VOL |
| `IQPTMDataAccess_MeasuredVolumeHourly` | CRUD for ALCTRL_MEAS_VOL_HRLY |
| `IQPTMDataAccess_MeasuredVolumeHistoryHourly` | Read for ALHIST_MEAS_VOL_HRLY |
| `IQPTMDataAccess_HourProfile` | Read hour profile configuration |
| `IQPTMDataAccess_PALocation` | Read location data |
| `IQPTMDataAccess_PALocationAttribute` | Read location attributes |
| `IQPTMDataAccess_PALocationAggregate` | Read parent-child relationships |
| `IQPipelineAdminDataAccess` | Calendar dates for close schedules |

### DAL Files (CodeGen)

| File | Table |
|---|---|
| `MeasuredVolumeDAL.cs` | ALCTRL_MEAS_VOL |
| `MeasuredVolumeHistoryDAL.cs` | ALHIST_MEAS_VOL |
| `MeasuredVolumeHourlyDAL.cs` | ALCTRL_MEAS_VOL_HRLY |
| `MeasuredVolumeHistoryHourlyDAL.cs` | ALHIST_MEAS_VOL_HRLY |
| `MeasuredVolumeHourlyLastSyncDAL.cs` | ALCTRL_MEAS_VOL_HRLY_LAST_SYNC |
| `MeasuredVolumeLatestVwDAL.cs` | ALCTRL_MEAS_VOL_LATEST_VW |
| `MeasuredVolumeLatestPrdVwDAL.cs` | ALCTRL_MEAS_VOL_LATEST_PRD_VW |
| `OperatorMeasuredVolumeDAL.cs` | Operator measurement view |

---

## Validation Rules

### Measurement Entry Validation Rules

**Validation Group:** `QPTMMeasurementEntry`
**Context Class:** `QMeasurementEntryValidationContext`
**File:** `Quorum.QPTM.Validations/Screens/MeasurementEntry/Context/QPTMValidationContext_MeasurementEntry.cs`

| Rule | File | Description |
|---|---|---|
| 001 | `QPTMValidationMeasurementEntry001_ValidateAggregateVolumeEntry.cs` | Blocks save at parent locations if `AllowAggregateVolumeEntry` is false |
| 002 | `QPTMValidationMeasurementEntry002_ValidateAccuracyCode.cs` | Validates accuracy code change permissions based on `AllowChangeActualVolumes` and `AllowChangeVolumesToEstimate` |
| 003 | `QPTMValidationMeasurementEntry003_ValidateAccountingMonth.cs` | Validates AcctgMth is not in closed period; prevents duplicate AcctgMth+GasDay records |
| 004 | `QPTMValidationMeasurementEntry004_ValidateBidirectionalLocations.cs` | Requires POV code (R or D) for bidirectional locations |
| 005 | `QPTMValidationMeasurementEntry005_ValidateGasDay.cs` | Validates GasDay <= last day of AcctgMth |
| 006 | `QPTMValidationMeasurementEntry006_ValidateLocation.cs` | Validates location exists in PALocation |

### Hourly Measurement Validation Rules

**Validation Group:** `QPTMHourlyMeasurementMaintenance`
**Context Class:** `QPTMHourlyMeasurementMaintenanceValidationContext`
**File:** `Quorum.QPTM.Validations/Screens/HourlyMeasurementMaintenance/Context/QPTMHourlyMeasurementMaintenanceValidationContext.cs`

| Rule | File | Description |
|---|---|---|
| 001 | `QPTMValidationHourlyMeasurementMaintenance001_ValidateMandatory.cs` | Validates AcctgMth rules for PPA; requires POV for bidirectional meters |
| 002 | `QPTMValidationHourlyMeasurementMaintenance002_DeleteAccountingMonth.cs` | Validates deletion scenarios |
| 003 | `QPTMValidationHourlyMeasurementMaintenance003_ValidateQtyDisplay.cs` | Ensures positive (non-negative) measurement values |
| 004 | `QPTMValidationHourlyMeasurementMaintenance004_ValidateAccountingMonth.cs` | Validates hourly accounting month constraints |

---

## Configuration Settings

### Global Configuration (`GLOBAL_CONFIG_CTRL`)

| Category | Key | Description | Used In |
|---|---|---|---|
| MEASUREMENT ENTRY | `ALLOW_AGGREGATE_VOLUME_ENTRY` | Allows volume entry at aggregate locations | Hourly update, Validation 001 |

### TSP Configuration (`TSP_CONFIG_CTRL`)

| Category | Key | Description | Used In |
|---|---|---|---|
| TSP | `ACCTG_MTH_LAG_TIME` | Months between ProdMth and AcctgMth | Hourly query routing |
| TSP | `PPA_APPROVE_IND` | Whether PPA events require approval | PPA event creation |

### QPTMGlobalConfigs Properties

| Property | Description | Used In |
|---|---|---|
| `AllowAggregateEntry` | Controls UI editability at aggregate locations | MeasurementEntryController |
| `AllowAggregateVolumeEntry` | Controls save permission at aggregate locations | Validation 001 |
| `AllowChangeActualVolume` | Controls editing of Actual accuracy records | Validation 002 |
| `AllowChangeVolumesToEstimate` | Controls changing accuracy to Estimate | Validation 002 |
| `DefaultAccuracyCode` | Default accuracy code for new records | AddAdditionalProperties |
| `QueryBtnText` | Text for Query button | All controllers |

### QPTMTspOrGlobalConfigs

| Property | Description | Used In |
|---|---|---|
| `MeasResultsByPOV(tspNo)` | Whether Measurement Results negates non-receipt volumes | MeasurementResultsController |

---

## Batch Processes

### BATCHID_ESUITE_VOL_IMPORT

**Process ID:** `Constants.ProcessIDs.BATCHID_ESUITE_VOL_IMPORT`

Triggered after saving measurement entries for child locations. Parameters:

| Parameter | Constant | Description |
|---|---|---|
| TSP_NO | `PARAM_TSP_NO` | TSP number |
| LOC_ID | `PARAM_LOC_ID` | Location identifier |
| ACCTG_MONTH | `PARAM_ACCTG_MONTH` | List of accounting months (MultipleValues) |
| GAS_DAY | `PARAM_GAS_DAY` | List of gas days (MultipleValues) |

Launched asynchronously (`runSynchronous: false`) and monitored via `QUICUtilities.AddProcessToMonitor`.

### RollAggregateLocations

Called from `QPTMAllocationServiceExt_Measurement.UpdateHourlyMeasurement()` for hourly data. Performs:
- Rolling up child location hourly volumes to parent aggregate location
- Uses screen ID `"QVPSOAHOURLYMEASUREMENTENTRY"` as the rollup source identifier

---

## Integration Points

### QIC (Quorum Integration Controller)

After saving in MeasurementEntry, the `QICService.NotifyOfChange()` is called with a `GenericScreenChange` containing all changed `MeasuredVolumeDO` records. Returns:
- `ReallocateSelectDO`: PPA reallocation selection options
- `ReallocatePPAEventDO`: PPA events to process

### Allocation Service

The `QPTMAllocationServiceExt_Measurement` is part of the Allocation Service assembly, reflecting measurement's role as allocation input.

### Location Maintenance

Measurement Results provides navigation links to Location Maintenance with context parameters.

### Gas Analysis Search

Gas analysis data provides BTU factor information that feeds into measurement entry. Managed via separate `GasAnalysisSearchController`.

---

## Security

### Screen Security Object IDs

| Screen | Security ID | Constant |
|---|---|---|
| Measurement Entry | `QVPMEASUREMENTENTRY` | `Constants.SecurityObjectIDs.MeasurementEntry` |
| Measurement Results | `QVPMEASUREMENTRESULTS` | `Constants.SecurityObjectIDs.MeasurementResults` |
| Hourly Measurement Entry | `QVPSOAHOURLYMEASUREMENTENTRY` | `Constants.SecurityObjectIDs.HourlyMeasurementEntry` |

---

## Key Code Paths

### Save Measurement Entry (End-to-End)

```
MeasurementEntryController (MVC)
  -> QUIControllerMeasurementEntry.DoSave()
    -> PreSave() - validates mandatory fields
    -> PrepareForUpdate() - sets VolSrcCode, POV, parent loc
      -> PreProcessData() - handles AcctgMth changes (delete+add)
    -> Service.UpdateSingleMeasurementEntry()
      -> ValidateSingleMeasurementEntry() - runs all 6 validation rules
      -> DataAccess.UpdateMultipleMeasuredVolume() - persists to ALCTRL_MEAS_VOL
      -> GetSingleMeasurementEntry() - re-queries to refresh
    -> UpdateParentLocation() - launches batch rollup if child location
    -> QICService.NotifyOfChange() - triggers PPA events
```

### Query Measurement Entry (End-to-End)

```
MeasurementEntryController (MVC)
  -> QUIControllerMeasurementEntry.ReadyForQuery()
    -> Validates IdLoc, ProdMth, AcctgMth
    -> SetQueryParams() - populates MeasurementEntryData
  -> QUIControllerMeasurementEntry.DoQuery()
    -> Service.GetSingleMeasurementEntry()
      -> Routes to Case 1, 2, or 3 based on dates
      -> GetMeasuredVolume() or GetMeasuredVolumeHistory()
      -> AddAdditionalPropertiesMeasurementEntry()
        -> Location POV, OtherUOM, Bidirectional, Parent/Child, Fill missing days
    -> BulkContainer.Items = MeasuredVolume list
```

---

*Last updated: 2026-03-03*

*Document version: 1.0*
