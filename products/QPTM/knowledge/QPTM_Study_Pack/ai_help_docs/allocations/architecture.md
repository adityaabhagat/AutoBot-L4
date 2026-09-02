---
title: Allocations (ALLOC) - Architecture
category: architecture
feature: Allocations (ALLOC)
related_repos: Web, Batch
keywords: ALLOC, architecture, QPTMAllocationService, PDA, measurement, aggregate location, penalty schedule, controllers, API, validation, data objects, database tables, cache, configuration
last_updated: 2026-03-03
---

# Allocations (ALLOC) - Architecture

## Overview

This document explains the **technical architecture** of the Allocations (ALLOC) system in QPTM. It covers service layer design, controller structure, API endpoints, validation framework, data objects, database schema, key algorithms, caching, and configuration.

For business concepts and terminology, see [Domain Documentation](./domain.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Service Layer](#service-layer)
3. [Controllers](#controllers)
4. [API Layer](#api-layer)
5. [Validation Framework](#validation-framework)
6. [Data Objects](#data-objects)
7. [Database Tables](#database-tables)
8. [Key Algorithms](#key-algorithms)
9. [Caching](#caching)
10. [Configuration](#configuration)
11. [Integration Points](#integration-points)

---

## System Architecture

### Architectural Layers

```
+-------------------------------------------------------------+
|                    WEB APPLICATION LAYER                      |
|  +------------------------+  +----------------------------+  |
|  | DailyAllocatedQuantity |  | MonthlyAllocatedQuantity   |  |
|  | MaintenanceController  |  | MaintenanceController      |  |
|  +----------+-------------+  +-------------+--------------+  |
+-------------|-----------------------------|------------------+
              |                             |
              v                             v
+-------------------------------------------------------------+
|                       API LAYER                              |
|  +--------------------------------------------------------+ |
|  | AllocationsController (route: /api/v1/Allocations)     | |
|  |   GET collection | GET by ID | GET summary | GET enums | |
|  +--------------------------------------------------------+ |
+-------------------------------------------------------------+
              |
              v
+-------------------------------------------------------------+
|                      SERVICE LAYER                           |
|  +--------------------------------------------------------+ |
|  | QPTMAllocationService.cs (Main Orchestrator)           | |
|  +--------------------------------------------------------+ |
|  | QPTMAllocationServiceExt_PDA.cs (PDA Processing)       | |
|  | QPTMAllocationServiceExt_Measurement.cs (Hourly Meas.) | |
|  | QPTMAllocationServiceExt_AggregateLocation.cs (Rollup) | |
|  | QPTMAllocationServiceExt_PenaltySchedule.cs (Penalties)| |
|  +--------------------------------------------------------+ |
+-------------------------------------------------------------+
              |
              v
+-------------------------------------------------------------+
|                   VALIDATION LAYER                           |
|  +--------------------------------------------------------+ |
|  | ValidationEnginePDA                                    | |
|  | ValidationRuleBasePDABusiness (header-level rules)     | |
|  | ValidationRuleBasePDALine (line-level rules)           | |
|  +--------------------------------------------------------+ |
+-------------------------------------------------------------+
              |
              v
+-------------------------------------------------------------+
|                   DATA ACCESS LAYER                          |
|  +--------------------------------------------------------+ |
|  | AllocationPDAHeaderDO/Ext   | AllocationPDADetailDO/Ext| |
|  | AllocationDO/Ext            | AllocationOverrideDO     | |
|  | MeasuredVolumeHourlyDO      | MeasuredVolumeHistoryDO  | |
|  | HourlyPenaltyScheduleHeaderDO                          | |
|  +--------------------------------------------------------+ |
+-------------------------------------------------------------+
              |
              v
+-------------------------------------------------------------+
|                        DATABASE                              |
|  ALTRAN_PDA_HDR, ALTRAN_PDA_DTL, ALCTRL_ALLOC,             |
|  ALTRAN_ALLOC, ALCTRL_MEAS_VOL, ALCTRL_MEAS_VOL_HIST,     |
|  ALLOC_PLAN_HDR, ALLOC_PLAN_LOC, ALLOC_PLAN_TRANS_TYPE,    |
|  ALLOC_TRANS_TYPE, ALCTRL_ANALYSIS                          |
+-------------------------------------------------------------+
              |
              v
+-------------------------------------------------------------+
|                        CACHE LAYER                           |
|  AllocationCache | LocationCache | TspCache | CycleCache    |
+-------------------------------------------------------------+
```

---

## Service Layer

### QPTMAllocationService.cs (Main Service)

**Role**: Primary orchestrator for all allocation operations. Coordinates PDA processing, measurement loading, aggregate location rollup, and penalty schedule execution.

**Key Responsibilities:**
- Orchestrate daily and monthly allocation processing
- Coordinate between extension services
- Manage allocation lifecycle (create, update, post, reallocate)
- Interface with controllers and API layer

**Key Methods (typical):**
- `ProcessDailyAllocation()` -- Run daily allocation for a gas day
- `ProcessMonthlyAllocation()` -- Run monthly allocation for an accounting month
- `GetAllocations()` -- Retrieve allocation data for display
- `SaveAllocations()` -- Persist allocation changes
- `SubmitAllocations()` -- Submit allocations for posting

### QPTMAllocationServiceExt_PDA.cs (PDA Processing)

**Role**: Handles all Predetermined Allocation (PDA) processing logic. This is the largest service extension file (~252KB), reflecting the complexity of PDA business rules.

**Key Responsibilities:**
- PDA creation, validation, and submission
- PDA method assignment (bulk vs non-bulk based on `BulkAssignmentPDACount` config)
- PDA-to-allocation translation (applying PRT/PRI/PCT/AMT methods)
- PDA revision and reallocation handling
- PPA (Previously Posted Allocations) snapshot creation

**Key Processing Logic:**
```
PDA Processing Flow:

1. Load active PDAs for gas day/location
   |-- Query ALTRAN_PDA_HDR + ALTRAN_PDA_DTL
   |-- Filter by effective dates, flow direction, TSP

2. Determine assignment method
   |-- Count PDAs exceeding BulkAssignmentPDACount?
   |   |-- YES: Use bulk assignment path
   |   |-- NO:  Use non-bulk (individual) assignment path

3. Apply allocation method per PDA
   |-- PRT: Calculate pro-rata shares from SchdQty ratios
   |-- PRI: Sort by priority code (H/B/L), fill sequentially
   |-- PCT: Apply percentage from PDA detail lines
   |-- AMT: Assign fixed amounts from PDA detail lines

4. Generate allocation records
   |-- Write to ALCTRL_ALLOC and ALTRAN_ALLOC
   |-- Track AllocQty per contract per location
```

### QPTMAllocationServiceExt_Measurement.cs (Hourly Measurement)

**Role**: Handles loading and processing of hourly measurement data from meters/SCADA systems.

**Key Responsibilities:**
- Load hourly measurement volumes into `ALCTRL_MEAS_VOL`
- Apply 3-case logic based on accounting month context
- Manage measurement history in `ALCTRL_MEAS_VOL_HIST`
- Aggregate hourly data to daily/monthly totals

**3-Case Logic:**
```
Case 1: Gas day is in the CURRENT accounting month
    --> Load measurements directly from real-time data source
    --> Write to ALCTRL_MEAS_VOL

Case 2: Gas day is in the PRIOR accounting month AND within lag period
    --> Load measurements from prior-month data source
    --> Lag period controlled by ACCTG_MTH_LAG_TIME config
    --> Write to ALCTRL_MEAS_VOL (updating existing records)

Case 3: Gas day is in a HISTORICAL accounting month (beyond lag)
    --> Load from ALCTRL_MEAS_VOL_HIST
    --> Used for reallocation and audit
    --> Original values preserved; corrections tracked separately
```

### QPTMAllocationServiceExt_AggregateLocation.cs (Rollup)

**Role**: Manages parent-child location rollup for aggregate locations.

**Key Responsibilities:**
- Identify aggregate (parent) locations and their children
- Roll up child measurement/allocation data to parent locations
- Handle missing child data scenarios
- Persist rolled-up results

**4-Stage Rollup Algorithm:**
```
Stage 1: Build Filters
    |-- Identify all aggregate location hierarchies
    |-- Build TSP/date range filter criteria
    |-- Determine which locations need rollup processing

Stage 2: Load Data
    |-- Load child location measurements (ALCTRL_MEAS_VOL)
    |-- Load existing parent location records
    |-- Load allocation plan location mappings (ALLOC_PLAN_LOC)

Stage 3: Rollup Calculation
    |-- For each parent location:
    |   |-- Sum all child location MeasQty values
    |   |-- Apply rollup rules (additive summation)
    |   |-- Handle nulls/zeros per configuration
    |-- Validate rollup totals

Stage 4: Save Results
    |-- Persist rolled-up MeasQty to parent records
    |-- Update ALCTRL_ALLOC for parent locations
    |-- Log processing results and any data gaps
```

### QPTMAllocationServiceExt_PenaltySchedule.cs (Penalties)

**Role**: Processes penalty schedule calculations for allocation imbalances.

**Key Responsibilities:**
- Calculate imbalances (AllocQty - SchdQty)
- Apply penalty schedule tiers
- Compute hourly penalty amounts (using `HourlyPenaltyScheduleHeaderDO`)
- Generate penalty records for billing

---

## Controllers

### DailyAllocatedQuantityMaintenanceController

**Security Code**: `DailyAllocatedQuantityMaintenance`

**Purpose**: Manages the web UI for daily allocation review and maintenance.

**Key Responsibilities:**
- Display daily allocated quantities for review
- Allow operators to apply overrides
- Support daily allocation approval workflow
- Filter by TSP, location, gas day, flow direction

**Typical Actions:**
- `Index()` -- Load daily allocation maintenance screen
- `GetDailyAllocations()` -- Retrieve daily allocation data grid
- `SaveOverrides()` -- Save manual allocation overrides
- `ApproveAllocations()` -- Approve daily allocations for posting

### MonthlyAllocatedQuantityMaintenanceController

**Purpose**: Manages the web UI for monthly allocation review and maintenance.

**Key Responsibilities:**
- Display monthly allocated quantity summaries
- Support monthly reconciliation workflow
- Allow monthly allocation adjustments
- Handle month-end posting and PPA creation

**Typical Actions:**
- `Index()` -- Load monthly allocation maintenance screen
- `GetMonthlyAllocations()` -- Retrieve monthly allocation data grid
- `SaveAdjustments()` -- Save monthly allocation adjustments
- `PostMonthlyAllocations()` -- Post monthly allocations for billing

---

## API Layer

### AllocationsController

**Route**: `/api/v1/Allocations`

**Purpose**: RESTful API for programmatic access to allocation data.

**Endpoints:**

| Method | Route | Description |
|--------|-------|-------------|
| **GET** | `/api/v1/Allocations` | Get allocation collection (with filters) |
| **GET** | `/api/v1/Allocations/{id}` | Get a specific allocation by ID |
| **GET** | `/api/v1/Allocations/summary` | Get allocation summary data |
| **GET** | `/api/v1/Allocations/enumeratedvalues` | Get enumerated values (allocation methods, priority codes, etc.) |

**Common Query Parameters:**
- `tspNo` -- Filter by TSP number
- `gasDay` -- Filter by gas day
- `accountingMonth` -- Filter by accounting month
- `locationId` -- Filter by location
- `flowDirection` -- Filter by receipt (R) or delivery (D)
- `contractNo` -- Filter by contract number

**Response Format:**
```json
{
    "data": [
        {
            "allocationId": 12345,
            "tspNo": 1,
            "gasDay": "2026-03-01",
            "locationId": "LOC001",
            "contractNo": "K-100",
            "flowDirection": "R",
            "schdQty": 5000.00,
            "allocQty": 4800.00,
            "measQty": 4800.00,
            "allocMethodCd": "PRT",
            "priorityCd": "B"
        }
    ],
    "totalCount": 1
}
```

---

## Validation Framework

### ValidationEnginePDA

**Purpose**: Orchestrates all PDA validation rules before a PDA can be saved or submitted.

**Validation Flow:**
```
PDA Validation Pipeline:

Input: PDA Header + PDA Detail Lines
    |
    v
ValidationRuleBasePDABusiness (Header-Level Rules)
    |-- Validate TSP number exists and is active
    |-- Validate location exists and is eligible
    |-- Validate effective date range is valid
    |-- Validate flow direction is set
    |-- Validate accounting month is correct
    |-- Validate BA (Business Associate) authorization
    |
    v
ValidationRuleBasePDALine (Line-Level Rules)
    |-- Validate contract number exists and is active
    |-- Validate contract is eligible for location
    |-- Validate allocation method code (PRT/PRI/PCT/AMT)
    |-- Validate percentage values (0-100 for PCT method)
    |-- Validate percentage total sums to 100% (PCT method)
    |-- Validate amount values are non-negative (AMT method)
    |-- Validate priority code (H/L/B for PRI method)
    |-- Validate no duplicate contract entries
    |
    v
Output: Validation Result (pass/fail with error messages)
```

**Key Validation Rules:**

| Rule | Level | Description |
|------|-------|-------------|
| TSP Validation | Header | TSP must exist and be active |
| Location Validation | Header | Location must be valid for allocation |
| Date Range | Header | Effective dates must be valid and not overlap existing PDAs |
| BA Authorization | Header | Submitting BA must be authorized for the location |
| Contract Eligibility | Line | Contract must be active and eligible at the location |
| Method Code | Line | Must be one of PRT, PRI, PCT, AMT |
| PCT Sum to 100 | Line | All percentage lines at a location must total 100% |
| Priority Code | Line | Must be H, L, or B when PRI method used |
| No Duplicates | Line | Same contract cannot appear twice in same PDA |
| Amount Non-Negative | Line | AMT values must be >= 0 |

---

## Data Objects

### PDA Data Objects

| Data Object | Database Table | Description |
|-------------|----------------|-------------|
| **AllocationPDAHeaderDO** | `ALTRAN_PDA_HDR` | PDA header: location, dates, flow direction, TSP, BA, status |
| **AllocationPDAHeaderExtDO** | `ALTRAN_PDA_HDR` (extended) | Extended PDA header with additional computed/joined properties |
| **AllocationPDADetailDO** | `ALTRAN_PDA_DTL` | PDA detail line: contract, allocation method, quantity/percentage, priority |
| **AllocationPDADetailExtDO** | `ALTRAN_PDA_DTL` (extended) | Extended PDA detail with additional computed/joined properties |

### Allocation Data Objects

| Data Object | Database Table | Description |
|-------------|----------------|-------------|
| **AllocationDO** | `ALCTRL_ALLOC` | Core allocation record: contract, location, gas day, AllocQty |
| **AllocationExtDO** | `ALCTRL_ALLOC` (extended) | Extended allocation with joins to contract, location, BA names |
| **AllocationOverrideDO** | Override tracking | Manual override records with reason codes and override quantities |

### Measurement Data Objects

| Data Object | Database Table | Description |
|-------------|----------------|-------------|
| **MeasuredVolumeHourlyDO** | `ALCTRL_MEAS_VOL` | Hourly measured volume per location per gas day |
| **MeasuredVolumeHistoryHourlyDO** | `ALCTRL_MEAS_VOL_HIST` | Historical hourly measured volumes for audit/reallocation |

### Penalty Data Objects

| Data Object | Description |
|-------------|-------------|
| **HourlyPenaltyScheduleHeaderDO** | Penalty schedule header with tier definitions, tolerance bands, and penalty rates |

---

## Database Tables

### Core Allocation Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| **ALTRAN_PDA_HDR** | PDA header records | TSP_NO, LOC_ID, EFF_DATE_FROM, EFF_DATE_TO, FLOW_DIR_CD, ACCTG_MTH, BA_ID, STATUS_CD |
| **ALTRAN_PDA_DTL** | PDA detail/line records | PDA_HDR_ID, CTR_NO, ALLOC_METHOD_CD, PCT_VAL, AMT_VAL, PRIORITY_CD |
| **ALCTRL_ALLOC** | Allocation control (daily/monthly results) | TSP_NO, GAS_DAY, LOC_ID, CTR_NO, FLOW_DIR_CD, SCHD_QTY, ALLOC_QTY, MEAS_QTY |
| **ALTRAN_ALLOC** | Allocation transaction records | Detailed allocation transactions with audit trail |

### Measurement Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| **ALCTRL_MEAS_VOL** | Hourly measured volumes (current) | TSP_NO, GAS_DAY, LOC_ID, HR_01 through HR_24, TOTAL_VOL |
| **ALCTRL_MEAS_VOL_HIST** | Hourly measured volumes (historical) | Same as ALCTRL_MEAS_VOL plus HIST_DT, HIST_TYPE |

### Allocation Plan Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| **ALLOC_PLAN_HDR** | Allocation plan header | PLAN_ID, TSP_NO, PLAN_NM, EFF_DATE_FROM, EFF_DATE_TO |
| **ALLOC_PLAN_LOC** | Allocation plan location mappings | PLAN_ID, LOC_ID, PARENT_LOC_ID (for aggregate locations) |
| **ALLOC_PLAN_TRANS_TYPE** | Allocation plan transaction type mappings | PLAN_ID, TRANS_TYPE_CD |

### Reference and Analysis Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| **ALLOC_TRANS_TYPE** | Allocation transaction type definitions | TRANS_TYPE_CD, TRANS_TYPE_DESC |
| **ALCTRL_ANALYSIS** | Allocation analysis/audit records | TSP_NO, GAS_DAY, LOC_ID, ANALYSIS_TYPE, ANALYSIS_VALUE |

### Table Relationships

```
ALTRAN_PDA_HDR (1) ---< (N) ALTRAN_PDA_DTL
    |                            |
    | (PDA drives allocation)    | (detail specifies method per contract)
    v                            v
ALCTRL_ALLOC (allocation results per contract/location/day)
    |
    |--- references ---> ALCTRL_MEAS_VOL (measured volumes)
    |--- references ---> ALCTRL_MEAS_VOL_HIST (historical measurements)
    |
ALLOC_PLAN_HDR (1) ---< (N) ALLOC_PLAN_LOC
                   ---< (N) ALLOC_PLAN_TRANS_TYPE
    |
    | (plan defines aggregate location hierarchies)
    v
ALCTRL_ANALYSIS (analysis/audit trail)
```

---

## Key Algorithms

### 1. PDA Method Assignment (Bulk vs Non-Bulk)

**Purpose**: Determine whether to use bulk or individual PDA processing based on volume.

```
Algorithm: PDA Method Assignment

Input: List of PDAs for processing, BulkAssignmentPDACount config value

1. Count = number of PDAs to process
2. Threshold = read BulkAssignmentPDACount from configuration
3. If Count >= Threshold:
       Use BULK assignment path
       |-- Load all PDAs into memory at once
       |-- Process as batch for efficiency
       |-- Reduced database round-trips
   Else:
       Use NON-BULK assignment path
       |-- Process each PDA individually
       |-- More granular error handling
       |-- Better for debugging individual PDA issues
```

**Configuration**: `BulkAssignmentPDACount` is stored in the system configuration table. Typical default values range from 50 to 200.

### 2. Aggregate Location Rollup (4-Stage)

**Purpose**: Roll up child location volumes to parent aggregate locations.

```
Algorithm: Aggregate Location Rollup

Stage 1: Build Filters
    Input: TSP number, gas day range, allocation plan
    Process:
        1. Query ALLOC_PLAN_LOC for parent-child mappings
        2. Build list of parent locations with their children
        3. Construct date range filters
        4. Build TSP-specific filter criteria
    Output: Filter set for data loading

Stage 2: Load Data
    Input: Filter set from Stage 1
    Process:
        1. Query ALCTRL_MEAS_VOL for child location hourly data
        2. Query existing parent location records
        3. Load ALLOC_PLAN_LOC for hierarchy definitions
        4. Cache loaded data for rollup processing
    Output: Child data set, parent data set, hierarchy map

Stage 3: Rollup Calculation
    Input: Child data, parent data, hierarchy map
    Process:
        For each parent location:
            1. Identify all child locations
            2. For each hour (HR_01 through HR_24):
                ParentHrValue = SUM(ChildHrValues)
            3. ParentTotalVol = SUM(HR_01..HR_24)
            4. Handle nulls:
                - If child value is NULL, treat as 0 (configurable)
                - If ALL children are NULL, parent = NULL
            5. Validate: ParentTotal should equal sum of children
    Output: Rolled-up parent location records

Stage 4: Save Results
    Input: Rolled-up parent records
    Process:
        1. Upsert parent records into ALCTRL_MEAS_VOL
        2. Update ALCTRL_ALLOC for parent locations
        3. Log rollup summary (parent, child count, totals)
        4. Flag any data gaps or anomalies
    Output: Persisted rollup results
```

### 3. Hourly Measurement Load (3-Case Logic)

**Purpose**: Load hourly measurement data with logic that varies based on the accounting month context.

```
Algorithm: Hourly Measurement Load

Input: Gas day, accounting month, ACCTG_MTH_LAG_TIME config

1. Determine current accounting month (CurrentAcctgMth)
2. Determine gas day's accounting month (GasDayAcctgMth)

Case 1: GasDayAcctgMth == CurrentAcctgMth
    |-- This is a current-month gas day
    |-- Load from real-time measurement data source
    |-- Write directly to ALCTRL_MEAS_VOL
    |-- Overwrite any existing records for same day/location

Case 2: GasDayAcctgMth == (CurrentAcctgMth - 1)
         AND DaysSinceMonthEnd <= ACCTG_MTH_LAG_TIME
    |-- This is a prior-month gas day within the lag window
    |-- Load from prior-month data source
    |-- Update existing ALCTRL_MEAS_VOL records
    |-- Allows late-arriving measurement corrections

Case 3: GasDayAcctgMth < (CurrentAcctgMth - 1)
         OR DaysSinceMonthEnd > ACCTG_MTH_LAG_TIME
    |-- This is a historical gas day
    |-- Read from ALCTRL_MEAS_VOL_HIST
    |-- Do NOT modify current measurement table
    |-- Used for reallocation and audit only
```

### 4. PDA Submission Processing

**Purpose**: Process a submitted PDA and generate allocation instructions.

```
Algorithm: PDA Submission

Input: PDA Header ID

1. Load PDA Header from ALTRAN_PDA_HDR
2. Load PDA Detail lines from ALTRAN_PDA_DTL
3. Run ValidationEnginePDA:
   |-- Execute ValidationRuleBasePDABusiness rules
   |-- Execute ValidationRuleBasePDALine rules
   |-- If validation fails: return errors, stop processing

4. Determine PDA Method Assignment:
   |-- Count PDAs at same location/period
   |-- Compare to BulkAssignmentPDACount threshold
   |-- Select bulk or non-bulk path

5. Process PDA by allocation method:
   |-- PRT: Calculate pro-rata ratios from SchdQty
   |-- PRI: Build priority queue (H -> B -> L)
   |-- PCT: Validate percentages sum to 100%
   |-- AMT: Validate fixed amounts

6. Mark PDA as submitted (update STATUS_CD)
7. PDA ready for allocation engine to consume
```

---

## Caching

### Cache Classes

| Cache | Description | Key Data Cached |
|-------|-------------|-----------------|
| **AllocationCache** | Caches allocation-specific reference data | Allocation plans, transaction types, PDA templates, allocation method lookups |
| **LocationCache** | Caches location data across features | Location details, aggregate location hierarchies, location-to-TSP mappings |
| **TspCache** | Caches TSP configuration data | TSP settings, TSP-specific allocation rules, gas flow configurations |
| **CycleCache** | Caches cycle/period data | Accounting month definitions, gas day calendars, cycle timing |

### Cache Usage Patterns

```
Cache Lifecycle:

1. Cache Population (Application Startup / First Request)
   |-- AllocationCache loads allocation plans, trans types
   |-- LocationCache loads location hierarchies
   |-- TspCache loads TSP configurations
   |-- CycleCache loads accounting month definitions

2. Cache Read (During Processing)
   |-- Service methods read from cache instead of database
   |-- Reduces database round-trips during allocation processing
   |-- Example: LocationCache.GetAggregateChildren(parentLocId)

3. Cache Invalidation (On Data Change)
   |-- Configuration changes trigger cache refresh
   |-- New accounting month triggers CycleCache refresh
   |-- Location hierarchy changes trigger LocationCache refresh

4. Cache Refresh (Periodic)
   |-- Caches may be refreshed on a timer or on-demand
   |-- Critical for ensuring allocation uses current configuration
```

**Important**: Cache staleness can cause allocation issues. If allocation results are unexpected, clearing the relevant caches (particularly `AllocationCache` and `LocationCache`) should be an early troubleshooting step.

---

## Configuration

### Key Configuration Parameters

| Parameter | Description | Typical Value | Impact |
|-----------|-------------|---------------|--------|
| **BulkAssignmentPDACount** | Threshold for bulk vs non-bulk PDA processing | 50-200 | Determines PDA processing efficiency path |
| **ACCTG_MTH_LAG_TIME** | Days after month-end to allow prior-month measurement updates | 5-15 days | Controls how long late measurements are accepted |

### BulkAssignmentPDACount

**Purpose**: Controls the cutoff point between individual and bulk PDA processing.

**How it works:**
- If the number of PDAs to process at a location/period >= this threshold, the system uses bulk processing
- Bulk processing loads all PDAs into memory and processes them as a batch, reducing database round-trips
- Non-bulk processing handles each PDA individually, providing better error isolation

**Tuning Guidance:**
- Lower values (e.g., 50): More aggressive bulk processing, better performance for high-volume locations
- Higher values (e.g., 200): More individual processing, better error isolation but slower for high volumes
- Monitor processing times to find the optimal threshold for your environment

### ACCTG_MTH_LAG_TIME

**Purpose**: Defines the grace period (in days) after a month ends during which measurement data from the prior month can still be loaded and processed.

**How it works:**
- During the first N days of a new month (where N = ACCTG_MTH_LAG_TIME), the system accepts measurement updates for the prior month
- After the lag period expires, prior-month measurements can only be accessed from historical tables
- This allows for late-arriving meter reads and measurement corrections

**Tuning Guidance:**
- Shorter lag (e.g., 5 days): Faster month-end close, fewer late corrections
- Longer lag (e.g., 15 days): More flexibility for late data, but delays final month-end numbers

---

## Integration Points

### Upstream Dependencies

| System | Data Provided | Tables/Objects |
|--------|---------------|----------------|
| **CAS (Capacity Scheduling)** | Scheduled quantities (SchdQty) | Fed into allocation as the baseline for pro-rata and priority calculations |
| **Nominations (NN)** | Nomination details | Provides contract/location/quantity context |
| **Contracts (K)** | Contract terms and eligibility | Validates PDA contract references |
| **Measurement (SCADA)** | Meter readings (MeasQty) | Loaded into ALCTRL_MEAS_VOL for allocation processing |

### Downstream Consumers

| System | Data Consumed | Purpose |
|--------|---------------|---------|
| **Billing (BL)** | Monthly allocated quantities | Invoicing shippers for transported volumes |
| **Balancing** | AllocQty vs SchdQty imbalances | Operational balancing and cash-out processing |
| **Reporting** | Allocation summaries | Regulatory reporting and operational dashboards |
| **EDI** | Allocation transaction data | Electronic data interchange with counterparties |

### Cross-Feature Relationships

```
Nominations (NN) --> CAS --> Allocations (ALLOC) --> Billing (BL)
                              |
                              |-- Measurement (SCADA) feeds MeasQty
                              |-- Contracts (K) validates eligibility
                              |-- Penalty Schedules enforce compliance
                              |-- PPA tracks reallocation history
```

---

## Key Code Locations Summary

| Component | File/Class | Purpose |
|-----------|-----------|---------|
| Main Service | `QPTMAllocationService.cs` | Orchestrates all allocation operations |
| PDA Processing | `QPTMAllocationServiceExt_PDA.cs` | PDA lifecycle and allocation method logic (~252KB) |
| Measurement | `QPTMAllocationServiceExt_Measurement.cs` | Hourly measurement loading (3-case logic) |
| Aggregate Location | `QPTMAllocationServiceExt_AggregateLocation.cs` | Parent-child location rollup (4-stage) |
| Penalty Schedule | `QPTMAllocationServiceExt_PenaltySchedule.cs` | Penalty calculation and processing |
| Daily Controller | `DailyAllocatedQuantityMaintenanceController` | Daily allocation UI (security: DailyAllocatedQuantityMaintenance) |
| Monthly Controller | `MonthlyAllocatedQuantityMaintenanceController` | Monthly allocation UI |
| API Controller | `AllocationsController` | REST API at /api/v1/Allocations |
| PDA Validation | `ValidationEnginePDA` | PDA validation orchestrator |
| Business Rules | `ValidationRuleBasePDABusiness` | PDA header-level validation rules |
| Line Rules | `ValidationRuleBasePDALine` | PDA line-level validation rules |
| PDA Header DO | `AllocationPDAHeaderDO` / `AllocationPDAHeaderExtDO` | Maps to ALTRAN_PDA_HDR |
| PDA Detail DO | `AllocationPDADetailDO` / `AllocationPDADetailExtDO` | Maps to ALTRAN_PDA_DTL |
| Allocation DO | `AllocationDO` / `AllocationExtDO` | Maps to ALCTRL_ALLOC |
| Override DO | `AllocationOverrideDO` | Manual override tracking |
| Meas Volume DO | `MeasuredVolumeHourlyDO` | Maps to ALCTRL_MEAS_VOL |
| Meas History DO | `MeasuredVolumeHistoryHourlyDO` | Maps to ALCTRL_MEAS_VOL_HIST |
| Penalty DO | `HourlyPenaltyScheduleHeaderDO` | Penalty schedule definitions |

---

## Related Documentation

- **Domain**: [domain.md](./domain.md) - Business concepts and terminology
- **Troubleshooting**: [troubleshooting.md](./troubleshooting.md) - Common issues and solutions

---

*Last updated: 2026-03-03*
*Document version: 1.0*
