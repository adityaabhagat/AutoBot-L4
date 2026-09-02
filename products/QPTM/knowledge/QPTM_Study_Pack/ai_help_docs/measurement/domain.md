---
title: Measurement (MEAS) - Domain Concepts
category: domain
feature: Measurement (MEAS)
related_repos: Web, Batch
keywords: MEAS, measurement, measured volume, hourly measurement, daily measurement, gas day, production month, accounting month, BTU factor, heating factor, accuracy code, SCADA, meter data, gas analysis, close schedule, aggregate location, bidirectional, POV, volume source, PPA, FlowCal
last_updated: 2026-03-03
---

# Measurement (MEAS) - Domain Concepts

## Overview

This document explains the **business concepts** behind the Measurement (MEAS) feature in the QPTM system. It focuses on WHAT the system does from a business perspective, explaining domain terminology, business rules, and workflows for gas pipeline measurement processing.

For technical implementation details, see [Architecture Documentation](./architecture.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Measurement Types](#measurement-types)
3. [Key Date Concepts](#key-date-concepts)
4. [Volume and Energy Quantities](#volume-and-energy-quantities)
5. [Auto-Populate Options (MeasOption)](#auto-populate-options-measoption)
6. [Gas Analysis Concepts](#gas-analysis-concepts)
7. [Accuracy Codes](#accuracy-codes)
8. [Volume Source Codes](#volume-source-codes)
9. [Location Concepts](#location-concepts)
10. [Bidirectional Locations and POV](#bidirectional-locations-and-pov)
11. [Aggregate Locations](#aggregate-locations)
12. [Close Schedules](#close-schedules)
13. [By Month Distribution](#by-month-distribution)
14. [SCADA and Meter Data Integration](#scada-and-meter-data-integration)
15. [Measurement and Allocation Integration](#measurement-and-allocation-integration)
16. [PPA Reallocation Events](#ppa-reallocation-events)
17. [Operator Workflows](#operator-workflows)
18. [Key Business Rules](#key-business-rules)
19. [Glossary](#glossary)

---

## System Overview

### What is Measurement (MEAS)?

**Measurement (MEAS)** is the process of recording and managing gas volume and energy measurements at pipeline locations. Measurements are the foundational data that drives allocation, billing, and balancing within the QPTM natural gas pipeline transportation management system.

**Business Purpose:**
- Record daily and hourly gas volumes (MCF) and energy quantities (DTH) at pipeline meter locations
- Track heating factors (BTU) that relate volume to energy
- Support both manual entry and automated data imports from SCADA/FlowCal systems
- Maintain historical measurement records across accounting periods
- Provide measurement data to downstream allocation and billing processes

### Key Business Value

- **Operational Accuracy**: Ensures gas volumes flowing through the pipeline are correctly recorded
- **Billing Foundation**: Measurement data is the basis for all shipper billing and invoicing
- **Allocation Input**: Measured volumes feed directly into the allocation process for distributing gas among shippers
- **Regulatory Compliance**: Supports FERC and NAESB requirements for gas measurement reporting
- **Audit Trail**: Maintains complete history of measurement changes across accounting periods

---

## Measurement Types

### Daily Measurement (Measurement Entry)

Daily measurement is the primary method for recording gas volumes at a location for each gas day within a production month. Each row in the Measurement Entry screen represents one gas day with:

- **Volume Quantity (MCF)**: The measured gas volume in thousand cubic feet
- **Energy Quantity (DTH)**: The measured energy in decatherms
- **BTU Factor**: The heating value that converts between volume and energy
- **Accuracy Code**: Whether the reading is Actual (A) or Estimated (E)
- **POV Code**: Point of View (Receipt or Delivery) for bidirectional locations

The Measurement Entry screen (`QVPMEASUREMENTENTRY`) displays all gas days in the selected production month and allows operators to enter or modify daily measurements.

### Hourly Measurement (Hourly Measurement Maintenance)

Hourly measurement provides sub-daily granularity for gas volume recording. Each gas day is broken into hours based on the TSP's hour profile configuration. Hourly measurement:

- Breaks a single gas day into up to 24 hourly time slots
- Uses the TSP-configured hour profile to determine valid hours
- Supports the same volume, energy, and BTU factor fields as daily measurement
- Rolls up hourly values to daily totals through aggregate location processing
- Is accessed from the Hourly Measurement Maintenance screen (`QVPSOAHOURLYMEASUREMENTENTRY`)

The hourly measurement screen links directly from the Measurement Entry screen for a selected gas day.

### Measurement Results (Read-Only View)

The Measurement Results screen (`QVPMEASUREMENTRESULTS`) provides a read-only view of historical measurement data. It allows querying by:

- Location or Location Group
- Gas Day range (from/to)
- Accounting Month

This screen references the history table (`ALHIST_MEAS_VOL`) and is used for audit and review purposes.

---

## Key Date Concepts

### Gas Day

The **Gas Day** is the specific calendar date on which gas flows were measured. Each measurement record is associated with a single gas day. Gas days must fall within the selected production month.

### Production Month (ProdMth)

The **Production Month** represents the calendar month during which gas physically flowed. It is always the first day of the month (e.g., 2026-03-01 for March 2026). The production month determines which set of gas days are available for measurement entry.

### Accounting Month (AcctgMth)

The **Accounting Month** is the billing period to which a measurement record is assigned. It may differ from the production month in PPA (Previously Posted Allocation) scenarios. Key rules:
- The accounting month must be greater than or equal to the production month
- The accounting month is always normalized to the first day of the month
- If production month changes and exceeds accounting month, the accounting month auto-adjusts
- Measurements in closed accounting months cannot be modified

### Current Billing Accounting Month (CurrentBillAcctMonth)

The **Current Billing Accounting Month** is the earliest open accounting month for the TSP. It determines which measurement records are "live" (in the control table) versus "historical" (in the history table). This is retrieved via `GetOpenAccountingMonth()`.

### Current Measurement Accounting Month (CurrentMeasAcctMonth)

The **Current Measurement Accounting Month** is the earliest open measurement month for the TSP. It is retrieved via `GetOpenMeasurementMonth()` and may differ from the billing accounting month based on TSP configuration.

### Accounting Month Lag Time

The **ACCTG_MTH_LAG_TIME** TSP configuration setting defines the number of months between the production month and the accounting month. For hourly measurement, the system validates that `AcctgMth - LagTime == ProdMth` for current or future production months.

---

## Volume and Energy Quantities

### Volume Quantity (VolQty / MCF)

The gas volume measured in the TSP's configured volume unit of measure (typically MCF - thousand cubic feet). This is the raw volumetric measurement from the meter.

### Energy Quantity (EngQty / DTH)

The energy equivalent of the measured gas volume, typically in decatherms (DTH). Energy = Volume x BTU Factor.

### BTU Factor (Heating Value)

The **BTU Factor** is the conversion factor between volume and energy quantities. It represents the heating value of the gas:
- `EngQty = VolQty * BtuFactor`
- `VolQty = EngQty / BtuFactor`
- `BtuFactor = EngQty / VolQty`

### Other Volume (OthVolQty) and Conversion Factor (ConvFactor)

Some locations support an **Other UOM** (unit of measure) for volume, controlled by the `OtherUOM` location attribute. When enabled:
- `OthVolQtyDisplay` replaces `VolQtyDisplay` in the UI
- `ConvFactor` replaces `BtuFactor` for conversions
- The same energy-to-volume relationship applies: `EngQty = OthVolQty * ConvFactor`

---

## Auto-Populate Options (MeasOption)

The **MeasOption** (Auto-Populate Type) determines which column is automatically calculated when the other two are provided. There are three modes:

| MeasOption Code | Name | Auto-Calculated Column | User Enters |
|---|---|---|---|
| `BTU` | Heating Factor | BTU Factor (or ConvFactor) | Volume + Energy |
| `DTH` | Energy | Energy (EngQty) | Volume + BTU Factor |
| `MCF` | Volume | Volume (VolQty) | Energy + BTU Factor |

**Default:** The system defaults to `BTU` (Heating Factor mode), where the user enters both volume and energy, and the BTU factor is auto-calculated.

---

## Gas Analysis Concepts

Gas analysis data is managed through the **Gas Analysis Search** screen and provides gas quality information for pipeline locations. Gas analysis data includes:

- **Component analysis**: Methane, ethane, propane percentages, etc.
- **Heating value**: BTU content per unit volume, which feeds into the BTU Factor used in measurement
- **Specific gravity**: Gas density relative to air

Gas analysis data is associated with specific locations and effective date ranges, and it informs the BTU factors used during measurement entry. The Gas Analysis Search screen (`GasAnalysisSearchController`) provides querying and viewing capabilities.

---

## Accuracy Codes

Each measurement record has an **Accuracy Code** indicating the data quality:

| Code | Name | Description |
|---|---|---|
| `A` | Actual | Data from an actual meter reading (SCADA, FlowCal, or verified manual) |
| `E` | Estimate | Estimated value, not from an actual reading |

**Business Rules:**
- **AllowChangeActualVolumes** (global config): If false, users cannot modify records with Accuracy Code = Actual
- **AllowChangeVolumesToEstimate** (global config): If false, users cannot change the Accuracy Code to Estimate
- When both configs are false, actual measurement records are fully locked from editing
- The default accuracy code for new records is configured via `QPTMGlobalConfigs.DefaultAccuracyCode`

---

## Volume Source Codes

The **Volume Source Code** (`VolSrcCode`) identifies how the measurement data was originated:

| Code | Name | Description |
|---|---|---|
| `MAN` | Manual | Data entered manually through the Measurement Entry screen |
| `FC` | FlowCal | Data imported from FlowCal SCADA integration |
| `MPS` | Measurement Information Process System | Data from the MPS source system |

When saving through the Measurement Entry screen, the system automatically sets `VolSrcCode = "MAN"` (Manual).

---

## Location Concepts

### Location (IdLoc)

A **Location** represents a physical meter point or measurement station on the pipeline. Each measurement is recorded for a specific location identified by `IdLoc`. Locations have:
- Effective date ranges (`EffDateFrom` / `EffDateTo`)
- A POV Code (Receipt, Delivery, or Bidirectional)
- Volume and Energy UOM preferences
- Optional Other UOM configuration

### Location Groups (IdLocGrp)

**Location Groups** allow querying measurement results across multiple related locations simultaneously. The Measurement Results screen supports both individual location and location group queries.

---

## Bidirectional Locations and POV

### Point of View (POV)

The **POV Code** indicates the flow direction at a location:

| Code | Name | Description |
|---|---|---|
| `R` | Receipt | Gas is received into the pipeline |
| `D` | Delivery | Gas is delivered out of the pipeline |
| `B` | Bidirectional | Gas can flow in either direction |

### Bidirectional Rules

For **bidirectional locations** (POV Code = `B`):
- Each measurement record MUST have a POV code set to either Receipt (`R`) or Delivery (`D`)
- The POV column becomes editable in the grid
- Delivery volumes are subtracted when calculating location totals
- Validation rule 004 enforces that bidirectional locations have a valid POV code

For **non-bidirectional locations**:
- The POV code field is read-only
- The POV code is automatically cleared on save (`PrepareForUpdate` sets `PovCode = ""`)

### Total Calculations with POV

When calculating monthly totals (TotalMcf and TotalDth):
- Receipt volumes are **added** to the total
- Delivery volumes at bidirectional locations are **subtracted** from the total
- The check uses `LocPovCd` (location's effective POV) to determine if a bidirectional location's record is a delivery

---

## Aggregate Locations

### Parent and Child Locations

An **Aggregate Location** is a parent location that represents the sum of volumes from its child locations. The system supports hierarchical location structures through the `PALocationAggregate` table.

### Aggregate Volume Entry Rules

- **AllowAggregateVolumeEntry** (global config): Controls whether entries can be made directly at aggregate (parent) locations
- **AllowAggregateEntry** (global config): Controls UI editability at aggregate locations
- If `AllowAggregateVolumeEntry` is false and the location is a parent, validation rule 001 blocks saving
- If `AllowAggregateEntry` is false and the location is a parent, the grid becomes read-only
- Child locations store their parent location ID in `IdPrntAggrLoc`

### Rollup Process

When measurement data is saved for a **child location**:
1. The system identifies the parent location via `GetPALocationAggregateParentLoc()`
2. A batch process (`BATCHID_ESUITE_VOL_IMPORT`) is launched to roll up child volumes to the parent
3. The rollup aggregates all child location volumes into the parent location's measurement

For hourly measurements, the rollup is performed via `RollAggregateLocations()` after saving changes.

---

## Close Schedules

### Measurement Close Schedule

The **Measurement Close Schedule** defines the dates when measurement periods close for a TSP. It is displayed as a dashboard widget (`MeasurementCloseWidgetVM`) showing upcoming close dates.

The close schedule uses the `CalendarDate` table with the `MeasurementClose` calendar date type. The widget displays:
- Close dates within the current month that are on or after today
- Close dates whose relative month matches the current month

### Billing Close vs Measurement Close

- **Billing Close**: Determined by `GetOpenAccountingMonth()` - the earliest open billing month
- **Measurement Close**: Determined by `GetOpenMeasurementMonth()` - the earliest open measurement month
- These may differ based on TSP configuration (the measurement close may lag behind or lead the billing close)

When a measurement period closes:
- Active measurement records move from the control table (`ALCTRL_MEAS_VOL`) to the history table (`ALHIST_MEAS_VOL`)
- The `IsLatest` flag in history marks the most recent version of each record
- Users can no longer modify measurements for the closed period

---

## By Month Distribution

The **By Month** feature allows operators to distribute a total monthly volume evenly across all gas days in the production month.

### Distribution Method

The supported method is **Divide By Days In Month** (`DIV`):
1. User enters a total monthly volume (MCF), energy (DTH), and/or BTU factor
2. The system divides the total evenly across all gas days
3. Remainder is distributed to the last days of the month (one unit added/subtracted per day)
4. If the total is less than the number of days, each day gets 1 (or -1 for negatives), with zero-fill for remaining days

### By Month Auto-Calculation

When entering By Month values, the system auto-calculates the missing field:
- If ByMonthVolQty is missing: `VolQty = EngQty / BtuFactor`
- If ByMonthEngQty is missing: `EngQty = VolQty * BtuFactor`
- If ByMonthBtuFactor is missing: `BtuFactor = EngQty / VolQty`

---

## SCADA and Meter Data Integration

### FlowCal Integration

The system supports automated measurement data import from **FlowCal**, a SCADA (Supervisory Control and Data Acquisition) system. FlowCal-imported records:
- Have `VolSrcCode = "FC"` (FlowCal volume source)
- Typically have `AccuracyCode = "A"` (Actual)
- Are imported via the batch process `BATCHID_ESUITE_VOL_IMPORT`
- May trigger aggregate rollup processing for child locations

### Volume Import Batch Process

The `BATCHID_ESUITE_VOL_IMPORT` batch process handles:
- Importing measurement data from external SCADA systems
- Rolling up child location volumes to parent aggregate locations
- Processing triggered both manually and after measurement entry save
- Parameters include: TSP number, Location ID, Accounting Months, and Gas Days

### Hourly Measurement Sync

The `MeasuredVolumeHourlyLastSync` table tracks the last synchronization timestamp for hourly measurement data, ensuring that import processes only process new or changed data.

---

## Measurement and Allocation Integration

### How Measurement Feeds Allocation

Measured volumes are the primary input to the allocation process:
1. Measured volumes at each location represent the total gas that flowed
2. The allocation process distributes these measured volumes among shippers based on PDAs (Predetermined Allocations)
3. Allocated quantities are compared against scheduled/nominated quantities to determine imbalances

### Measurement Results in Allocation Context

The `MeasurementResultsController` inherits from `AllocationControllerBase`, reflecting the tight integration between measurement and allocation. Measurement Results provides links to:
- **Location Maintenance**: Navigate to location details with context (TspNo, LocId, date range)

---

## PPA Reallocation Events

### What is PPA?

A **Previously Posted Allocation (PPA)** event is triggered when measurement data changes after allocations have already been posted. This signals that existing allocations need to be recalculated.

### When PPA Events Are Created

PPA events are created when hourly measurement data changes affect contracts associated with the measurement location. The system:
1. Identifies all contracts linked to the location (directly or via location groups)
2. Creates `ReallocatePPAEventDO` records for each affected contract/production month
3. Checks for duplicate PPA events before inserting
4. The PPA source code is set to `"LOC"` (Location) with trigger source `"AL03"`

### PPA Approval

TSP configuration (`PPA_APPROVE_IND`) controls whether PPA events require approval before processing.

### PPA Dialog in Measurement Entry

After saving measurements in the Measurement Entry screen, the system notifies the QIC (Quorum Integration Controller) service of changes. The response may include:
- `ReallocateSelectDO`: Prompts the user to select which contracts to reallocate
- `ReallocatePPAEventDO`: PPA events to be processed

The `IsShowPPAReallocationDialog` JavaScript callback on the Save button handles displaying the PPA dialog.

---

## Operator Workflows

### Daily Measurement Entry Workflow

1. **Open Measurement Entry screen** and select TSP, Location, Production Month, and Accounting Month
2. **Select MeasOption** (BTU, DTH, or MCF) to choose auto-populate behavior
3. **Query** to load existing measurements for all gas days in the production month
4. **Enter or modify** volume, energy, or BTU values for each gas day
5. **Save** to persist changes, which triggers:
   - Validation (accounting month, accuracy code, bidirectional, gas day, aggregate, location)
   - Data persistence to `ALCTRL_MEAS_VOL`
   - Aggregate rollup batch process (if child location)
   - PPA event generation (if post-allocation changes)

### Hourly Measurement Workflow

1. From Measurement Entry, **select a gas day row** and navigate to Hourly Measurement Maintenance
2. The hourly screen displays all configured hours for the selected gas day
3. **Enter volume and energy** values per hour
4. **Save** to persist hourly data, which triggers aggregate rollup if applicable
5. Returns to Measurement Entry where daily totals reflect hourly changes

### By Month Entry Workflow

1. From Measurement Entry, click **"By Month"** button
2. Enter total monthly volume (MCF), energy (DTH), and/or BTU factor
3. System auto-calculates any missing field
4. Click apply to distribute values across all gas days
5. Review and adjust individual days as needed
6. Save the measurement entry

### Measurement Review Workflow

1. Open **Measurement Results** screen
2. Query by Location/Location Group, Gas Day range, and Accounting Month
3. Review historical measurement data (read-only)
4. Export to Excel for further analysis
5. Navigate to Location Maintenance for location details

---

## Key Business Rules

### Validation Rules Summary

| Rule # | Name | Description |
|---|---|---|
| 001 | ValidateAggregateVolumeEntry | Blocks saving at aggregate (parent) locations if AllowAggregateVolumeEntry is false |
| 002 | ValidateAccuracyCode | Prevents modifying Actual records when AllowChangeActualVolumes is false; prevents changing to Estimate when AllowChangeVolumesToEstimate is false |
| 003 | ValidateAccountingMonth | Validates accounting month is not in a closed billing/measurement period; prevents duplicate records for same AcctgMth+GasDay |
| 004 | ValidateBidirectionalLocations | Requires POV code (R or D) for bidirectional locations when position state is active |
| 005 | ValidateGasDay | Validates gas day cannot be later than the last day of the accounting month |
| 006 | ValidateLocation | Validates the location exists in PALocation with valid effective dates |

### Hourly Measurement Validation Rules

| Rule # | Name | Description |
|---|---|---|
| 001 | ValidateMandatory | Validates accounting month rules for PPA scenarios and requires POV for bidirectional meters |
| 002 | DeleteAccountingMonth | Validates deletion scenarios for accounting month records |
| 003 | ValidateQtyDisplay | Ensures measurement values are positive (non-negative) |
| 004 | ValidateAccountingMonth | Validates accounting month constraints for hourly records |

### Critical Business Rules

1. **Production Month <= Accounting Month**: The production month can never exceed the accounting month
2. **Closed Period Protection**: Measurements in closed accounting months cannot be modified
3. **Negative Volume Rejection**: Hourly measurements reject negative volume and energy values
4. **Mandatory Fields**: AcctgMth, BtuFactor, and AccuracyCode are required when VolQty or EngQty is entered
5. **Manual Source on Save**: All measurements saved through the UI automatically receive `VolSrcCode = "MAN"`
6. **History vs Control Table Routing**: The system automatically queries the correct table based on production month and accounting month relationship to the current billing month

---

## Glossary

| Term | Definition |
|---|---|
| **AcctgMth** | Accounting Month - the billing period to which a measurement is assigned |
| **Accuracy Code** | Indicates whether a measurement is Actual (A) or Estimated (E) |
| **Aggregate Location** | A parent location whose volumes are the sum of its child locations |
| **BTU Factor** | Heating value conversion factor between volume and energy |
| **Bidirectional** | A location where gas can flow in either direction (Receipt or Delivery) |
| **By Month** | Feature to distribute a monthly total evenly across gas days |
| **ConvFactor** | Conversion factor used with Other UOM locations (equivalent to BTU Factor) |
| **DTH** | Decatherm - standard energy unit for natural gas |
| **EngQty** | Energy Quantity - measured energy in DTH |
| **FlowCal** | SCADA system for automated meter data collection |
| **Gas Day** | The calendar date on which gas flow was measured |
| **IdLoc** | Location Identifier - unique code for a pipeline meter point |
| **IsLatest** | Flag on history records indicating the most recent version |
| **MCF** | Thousand Cubic Feet - standard volume unit for natural gas |
| **MeasOption** | Auto-Populate Type: BTU (default), DTH, or MCF |
| **OthVolQty** | Other Volume Quantity - volume in an alternative UOM |
| **POV** | Point of View - Receipt (R), Delivery (D), or Bidirectional (B) |
| **PPA** | Previously Posted Allocation - reallocation event triggered by measurement changes |
| **ProdMth** | Production Month - the month when gas physically flowed |
| **SCADA** | Supervisory Control and Data Acquisition - automated meter data systems |
| **TspNo** | Transportation Service Provider Number |
| **VolQty** | Volume Quantity - measured gas volume in MCF |
| **VolSrcCode** | Volume Source Code - indicates data origin (MAN, FC, MPS) |

---

*Last updated: 2026-03-03*

*Document version: 1.0*
