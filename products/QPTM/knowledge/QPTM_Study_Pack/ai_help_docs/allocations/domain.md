---
title: Allocations (ALLOC) - Domain Concepts
category: domain
feature: Allocations (ALLOC)
related_repos: Web, Batch
keywords: ALLOC, allocations, PDA, predetermined allocation, pro-rata, priority, percentage, amount, measurement, aggregate location, penalty schedule, PPA, reallocation, SchdQty, AllocQty, MeasQty
last_updated: 2026-03-03
---

# Allocations (ALLOC) - Domain Concepts

## Overview

This document explains the **business concepts** behind the Allocations (ALLOC) feature in the QPTM system. It focuses on WHAT the system does from a business perspective, explaining domain terminology, business rules, and workflows for gas pipeline allocation processing.

For technical implementation details, see [Architecture Documentation](./architecture.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Predetermined Allocation (PDA)](#predetermined-allocation-pda)
3. [Allocation Types and Methods](#allocation-types-and-methods)
4. [Allocation Quantities](#allocation-quantities)
5. [Measurement Integration](#measurement-integration)
6. [Aggregate Locations](#aggregate-locations)
7. [Penalty Schedules](#penalty-schedules)
8. [Priority Handling](#priority-handling)
9. [Flow Direction](#flow-direction)
10. [Duration Codes](#duration-codes)
11. [Previously Posted Allocations (PPA)](#previously-posted-allocations-ppa)
12. [Business Workflows](#business-workflows)
13. [Overrides](#overrides)
14. [Glossary](#glossary)

---

## System Overview

### What is Allocations (ALLOC)?

**Allocations (ALLOC)** is the process of distributing actual measured gas volumes among shippers and contracts at pipeline locations. After gas flows through the pipeline, measured volumes at each location must be allocated to individual transactions based on predetermined methods, priorities, and contractual agreements.

**Business Purpose:**
- Distribute measured gas volumes to individual shippers and contracts
- Apply allocation methods (pro-rata, priority, percentage, amount) to determine each party's share
- Reconcile scheduled quantities against actual measurements
- Support daily and monthly allocation cycles
- Enable penalty schedule processing for imbalance management
- Handle parent-child location rollups through aggregate locations

### Key Business Value

- **Accurate Distribution**: Ensures measured gas volumes are fairly distributed among shippers
- **Contractual Compliance**: Applies agreed-upon allocation methods per contract
- **Operational Transparency**: Provides clear audit trail from measurement to allocation
- **Imbalance Management**: Tracks scheduled vs allocated vs measured quantities for balancing
- **Regulatory Compliance**: Supports FERC and NAESB requirements for gas allocation reporting

---

## Predetermined Allocation (PDA)

### What is a PDA?

A **Predetermined Allocation (PDA)** is a shipper-submitted document that specifies how gas volumes should be allocated at a given location for a given time period. The PDA defines the allocation method, the participating contracts, and the quantities or percentages to be used during allocation processing.

### PDA Structure

A PDA consists of two parts:

**PDA Header (`ALTRAN_PDA_HDR`)**:
- Identifies the location, effective dates, flow direction, and overall PDA parameters
- Contains the accounting month, TSP number, and submission status
- Tracks the Business Associate (BA) submitting the PDA

**PDA Detail (`ALTRAN_PDA_DTL`)**:
- Contains individual line items specifying contracts, allocation methods, quantities, and percentages
- Each detail line represents a single contract's allocation instruction
- Includes priority codes, percentage values, and fixed amount quantities

### PDA Lifecycle

```
PDA Lifecycle:

1. PDA Creation
   |-- Shipper or operator creates PDA for a location
   |-- Specifies allocation method, contracts, quantities/percentages
   |-- Sets effective date range and flow direction

2. PDA Validation
   |-- System validates business rules (ValidationEnginePDA)
   |-- Checks contract eligibility, location validity, date ranges
   |-- Validates percentage totals (must sum to 100% for PCT method)

3. PDA Submission
   |-- PDA submitted for processing
   |-- System assigns PDA method (bulk vs non-bulk)
   |-- PDA becomes active for allocation processing

4. Allocation Processing
   |-- Daily/monthly allocation reads active PDAs
   |-- Applies specified allocation method to measured volumes
   |-- Generates allocation records (ALCTRL_ALLOC)

5. PDA Revision/Reallocation
   |-- PDAs can be revised for future periods
   |-- Reallocation triggers reprocessing with updated PDAs
   |-- PPA records preserve previously posted values
```

### PDA Method Assignment

The system determines how to process PDAs based on volume:

- **Bulk Assignment**: When the number of PDAs exceeds the `BulkAssignmentPDACount` configuration threshold, the system uses a bulk processing approach for efficiency
- **Non-Bulk Assignment**: For smaller PDA counts, the system processes each PDA individually with more granular control

**Business Rule**: The `BulkAssignmentPDACount` configuration parameter (stored in system configuration) controls this threshold. Typical values range from 50-200 depending on system capacity.

---

## Allocation Types and Methods

### Allocation Method Codes

The system supports four primary allocation methods, each identified by a three-character code:

| Code | Name | Description | When Used |
|------|------|-------------|-----------|
| **PRT** | Pro-Rata | Allocates volumes proportionally based on scheduled quantities | Default method; fair distribution based on each contract's share |
| **PRI** | Priority | Allocates volumes based on priority ranking (H/L/B codes) | When certain contracts must be filled before others |
| **PCT** | Percentage | Allocates volumes based on fixed percentages specified in PDA | When shippers agree to fixed percentage splits |
| **AMT** | Amount | Allocates a fixed volume amount to specific contracts | When specific volume amounts are contractually required |

### Pro-Rata (PRT) Method

**How it works:**
- Each contract receives a share of measured volume proportional to its scheduled quantity relative to the total scheduled quantity at the location
- Formula: `AllocQty = MeasQty * (ContractSchdQty / TotalSchdQty)`

**Example:**
```
Location Total Measured: 10,000 Dth
Contract A Scheduled: 6,000 Dth (60%)
Contract B Scheduled: 4,000 Dth (40%)

Allocation:
Contract A: 10,000 * (6,000 / 10,000) = 6,000 Dth
Contract B: 10,000 * (4,000 / 10,000) = 4,000 Dth
```

### Priority (PRI) Method

**How it works:**
- Contracts are ranked by priority code (H = High, L = Low, B = Base)
- Higher priority contracts are filled first up to their scheduled quantity
- Remaining volume flows to lower priority contracts

**Example:**
```
Location Total Measured: 7,000 Dth
Contract A (Priority H): Scheduled 5,000 Dth
Contract B (Priority L): Scheduled 5,000 Dth

Allocation:
Contract A (High): min(5,000, 7,000) = 5,000 Dth (filled first)
Contract B (Low):  7,000 - 5,000 = 2,000 Dth (gets remainder)
```

### Percentage (PCT) Method

**How it works:**
- Each contract receives a fixed percentage of the measured volume as specified in the PDA
- Percentages must sum to 100% across all contracts at the location

**Example:**
```
Location Total Measured: 10,000 Dth
Contract A: 70% per PDA
Contract B: 30% per PDA

Allocation:
Contract A: 10,000 * 0.70 = 7,000 Dth
Contract B: 10,000 * 0.30 = 3,000 Dth
```

### Amount (AMT) Method

**How it works:**
- Specific volume amounts are assigned to contracts as defined in the PDA
- Remaining volume (if any) may be allocated via a secondary method

**Example:**
```
Location Total Measured: 10,000 Dth
Contract A: 4,000 Dth (fixed amount per PDA)
Contract B: 3,000 Dth (fixed amount per PDA)
Remainder: 3,000 Dth (allocated per secondary method or pro-rata)
```

---

## Allocation Quantities

### Key Quantity Types

The allocation process tracks three fundamental quantity types that flow through the system:

| Quantity | Field | Description | Source |
|----------|-------|-------------|--------|
| **SchdQty** | Scheduled Quantity | The quantity scheduled for transportation based on nominations and CAS processing | CAS/Nomination system |
| **AllocQty** | Allocated Quantity | The quantity allocated to each contract after applying the allocation method to measured volumes | Allocation processing |
| **MeasQty** | Measured Quantity | The actual measured volume at the location from meters/measurement devices | Measurement system |

### Quantity Relationships

```
Quantity Flow:

SchdQty (from CAS/Nominations)
    |
    v
Allocation Method Applied (PRT/PRI/PCT/AMT)
    |
    v
AllocQty (distributed to contracts)
    |
    |--- Compared against MeasQty (actual measurement)
    |
    v
Imbalance = AllocQty - SchdQty
```

**Business Rules:**
- The sum of all AllocQty values at a location should equal the MeasQty for that location
- Imbalances (differences between AllocQty and SchdQty) are tracked for balancing and penalty purposes
- When MeasQty is zero or unavailable, allocation may use SchdQty as a proxy (depending on configuration)

### Quantity Precedence

During allocation processing, quantities are resolved in this order:
1. **Measured Quantity (MeasQty)**: Preferred source -- actual meter readings
2. **Scheduled Quantity (SchdQty)**: Used when measurements are unavailable
3. **Override Quantity**: Manual overrides take precedence over calculated values

---

## Measurement Integration

### Overview

Measurements represent actual gas volumes recorded at pipeline locations. The allocation system integrates measurement data to distribute real volumes rather than relying solely on scheduled quantities.

### Measurement Granularity

| Granularity | Table | Description |
|-------------|-------|-------------|
| **Hourly** | `ALCTRL_MEAS_VOL` | Hour-by-hour measured volumes for each location |
| **Daily** | Aggregated from hourly | Sum of 24 hourly values for a gas day |
| **Monthly** | Aggregated from daily | Sum of all daily values for an accounting month |

### Hourly Measurement Processing

Hourly measurement data is loaded into the system using a **3-case logic** based on the current accounting month:

**Case 1: Current Accounting Month**
- Load measurements for the current gas day from real-time meter data
- Apply any measurement corrections or adjustments
- Used for daily allocation processing

**Case 2: Prior Accounting Month (Lag Period)**
- Load measurements for gas days in the prior month that fall within the accounting lag period
- Controlled by the `ACCTG_MTH_LAG_TIME` configuration parameter
- Allows for late-arriving measurement data to be captured

**Case 3: Historical Accounting Month**
- Load measurements from historical records (`ALCTRL_MEAS_VOL_HIST`)
- Used for reallocation and audit purposes
- Preserves original measurement values alongside corrected values

**Business Rule**: The `ACCTG_MTH_LAG_TIME` configuration determines how many days into the next month measurement data from the prior month can still be loaded and processed.

### Measurement Data Flow

```
Meter/SCADA System
    |
    v
Hourly Measurement Load (QPTMAllocationServiceExt_Measurement)
    |
    |-- Case 1: Current month --> ALCTRL_MEAS_VOL
    |-- Case 2: Lag period    --> ALCTRL_MEAS_VOL
    |-- Case 3: Historical    --> ALCTRL_MEAS_VOL_HIST
    |
    v
Aggregate to Daily/Monthly
    |
    v
Allocation Processing (uses MeasQty)
```

---

## Aggregate Locations

### What are Aggregate Locations?

**Aggregate Locations** represent parent locations that aggregate (roll up) volumes from one or more child locations. This parent-child hierarchy allows the system to compute total volumes at a higher level from detailed measurements at individual meter points.

### Parent-Child Rollup

**Purpose:**
- A physical pipeline location may have multiple meters or sub-locations
- The aggregate (parent) location represents the total volume across all child locations
- Allocation may occur at the parent level using rolled-up measurements

### Rollup Process (4-Stage)

The aggregate location rollup follows a 4-stage process:

```
Stage 1: Build Filters
    |-- Identify aggregate locations and their children
    |-- Determine date ranges and TSP filters
    |-- Build query parameters for data retrieval
    |
    v
Stage 2: Load Data
    |-- Load child location measurements
    |-- Load existing parent location data
    |-- Retrieve allocation plan configurations
    |
    v
Stage 3: Rollup Calculation
    |-- Sum child location quantities to parent
    |-- Apply rollup rules (additive, weighted, etc.)
    |-- Handle missing child data (zero vs null)
    |
    v
Stage 4: Save Results
    |-- Persist rolled-up quantities to parent location records
    |-- Update allocation control records
    |-- Log rollup processing results
```

**Business Rule**: If any child location has missing measurement data, the rollup behavior depends on configuration -- it may treat missing data as zero or skip the rollup for that period.

---

## Penalty Schedules

### What are Penalty Schedules?

**Penalty Schedules** define the financial consequences when shippers deviate from their scheduled quantities. Imbalances between scheduled and actual (measured/allocated) quantities can trigger penalties that incentivize accurate nominations and balanced operations.

### Penalty Components

| Component | Description |
|-----------|-------------|
| **Imbalance Tolerance** | Percentage or volume threshold before penalties apply |
| **Penalty Rate** | Dollar amount per unit of imbalance volume |
| **Penalty Tiers** | Multiple penalty levels that increase with greater imbalance |
| **Cashout Price** | Price used to value imbalance volumes for financial settlement |

### Penalty Calculation

```
Imbalance = AllocQty - SchdQty

If |Imbalance| <= Tolerance:
    Penalty = $0 (within tolerance band)

If |Imbalance| > Tolerance:
    Penalty = (|Imbalance| - Tolerance) * PenaltyRate

Tiered Example:
    0-5% imbalance:   No penalty
    5-10% imbalance:  $0.10/Dth
    10-20% imbalance: $0.25/Dth
    >20% imbalance:   $0.50/Dth
```

### Hourly Penalty Schedules

For TSPs that operate on an hourly basis, penalty schedules can be applied at the hourly level using `HourlyPenaltyScheduleHeaderDO`. This allows for more granular imbalance management where hour-by-hour deviations are tracked and penalized.

---

## Priority Handling

### Priority Codes

The allocation system uses priority codes to determine the order in which contracts receive allocated volumes when the Priority (PRI) allocation method is used:

| Code | Name | Description | Allocation Order |
|------|------|-------------|-----------------|
| **H** | High | Highest priority -- filled first | 1st (receives volume before all others) |
| **B** | Base | Base/normal priority -- filled after high | 2nd (receives volume after high priority) |
| **L** | Low | Lowest priority -- filled last | 3rd (receives remaining volume) |

### Priority Allocation Logic

```
Priority Allocation Flow:

Total Measured Volume at Location: V

Step 1: Allocate to High Priority (H) contracts
    |-- Each H contract gets min(SchdQty, remaining V)
    |-- Deduct allocated amounts from V
    |
    v
Step 2: Allocate to Base Priority (B) contracts
    |-- Each B contract gets min(SchdQty, remaining V)
    |-- If multiple B contracts, apply pro-rata within tier
    |-- Deduct allocated amounts from V
    |
    v
Step 3: Allocate to Low Priority (L) contracts
    |-- Each L contract gets min(SchdQty, remaining V)
    |-- If multiple L contracts, apply pro-rata within tier
    |-- Any remaining V is unallocated
```

**Business Rules:**
1. Within the same priority tier, if multiple contracts exist, volumes are distributed pro-rata based on scheduled quantities
2. A contract at a higher priority tier always receives its full scheduled quantity (if available) before any lower-tier contract receives volume
3. Priority codes are specified per PDA detail line, allowing different contracts at the same location to have different priorities

---

## Flow Direction

### Receipt vs Delivery

Allocations track gas flow direction at each location:

| Direction | Code | Description |
|-----------|------|-------------|
| **Receipt** | R | Gas entering the pipeline at this location (injection) |
| **Delivery** | D | Gas leaving the pipeline at this location (withdrawal) |

### Flow Direction in Allocation

- **PDA Header**: Specifies the flow direction for the entire PDA at that location
- **Allocation Records**: Track quantities separately for receipt and delivery
- **Measurement Volumes**: Recorded with flow direction to match against scheduled direction
- **Imbalance Calculation**: Receipt and delivery imbalances are tracked independently

**Business Rule**: A single location may have both receipt and delivery activity. The allocation system processes each direction independently, ensuring receipt allocations use receipt measurements and delivery allocations use delivery measurements.

---

## Duration Codes

### What are Duration Codes?

**Duration Codes** specify the time period for which an allocation or PDA is effective. They control whether allocation processing runs on a daily, monthly, or other periodic basis.

| Code | Description | Usage |
|------|-------------|-------|
| **Daily** | Allocation applies to a single gas day | Used for daily allocation processing cycles |
| **Monthly** | Allocation applies to the entire accounting month | Used for monthly allocation and settlement |

### Duration in Processing

- **Daily Allocation**: Processes each gas day individually, using daily measurements and scheduled quantities
- **Monthly Allocation**: Aggregates an entire month of data, producing final monthly allocated quantities for billing and settlement
- **PDA Duration**: PDAs may be submitted for a single day or an entire month depending on the allocation plan configuration

---

## Previously Posted Allocations (PPA)

### What is PPA?

**Previously Posted Allocations (PPA)** capture the allocation quantities that were previously computed and posted before a reallocation occurs. PPA records serve as an audit trail, preserving the original allocation values so that changes from reallocation can be tracked and reconciled.

### PPA Triggering

PPA records are created when:
1. **Reallocation is initiated** -- the system saves current allocation values as PPA before reprocessing
2. **Measurement corrections** arrive after initial allocation -- the system preserves original allocations
3. **PDA revisions** change the allocation method or parameters for a previously allocated period

### PPA Business Rules

- PPA values represent the "before" snapshot; new allocation values represent the "after"
- The difference between PPA and current allocation identifies the reallocation adjustment
- PPA records are read-only once created -- they cannot be modified
- Multiple reallocation cycles produce multiple PPA snapshots, each preserving the prior state

```
PPA Flow:

Original Allocation (Day 1):
    Contract A: 5,000 Dth (posted)
    Contract B: 3,000 Dth (posted)

Measurement Correction Arrives (Day 5):
    System saves PPA:
        PPA Contract A: 5,000 Dth
        PPA Contract B: 3,000 Dth

Reallocation with Corrected Measurement:
    Contract A: 5,500 Dth (new allocation)
    Contract B: 3,200 Dth (new allocation)

Adjustment:
    Contract A: 5,500 - 5,000 = +500 Dth
    Contract B: 3,200 - 3,000 = +200 Dth
```

---

## Business Workflows

### Workflow 1: PDA Submission

```
PDA Submission Workflow:

1. Shipper/Operator Initiates PDA
   |-- Selects location, effective dates, flow direction
   |-- Chooses allocation method (PRT/PRI/PCT/AMT)
   |-- Enters contract details, quantities/percentages

2. System Validates PDA
   |-- ValidationEnginePDA runs business rules
   |-- Checks: contract eligibility, date ranges, percentage totals
   |-- ValidationRuleBasePDABusiness: header-level rules
   |-- ValidationRuleBasePDALine: line-level rules

3. PDA Saved to Database
   |-- Header saved to ALTRAN_PDA_HDR
   |-- Detail lines saved to ALTRAN_PDA_DTL

4. PDA Submitted for Processing
   |-- PDA method assigned (bulk vs non-bulk)
   |-- PDA becomes active for allocation engine
```

### Workflow 2: Daily Allocation

```
Daily Allocation Workflow:

1. Measurement Data Loaded
   |-- Hourly measurements loaded (QPTMAllocationServiceExt_Measurement)
   |-- 3-case logic applied based on accounting month
   |-- Measurements stored in ALCTRL_MEAS_VOL

2. Aggregate Location Rollup
   |-- Child location measurements rolled up to parents
   |-- 4-stage process: filter, load, rollup, save
   |-- QPTMAllocationServiceExt_AggregateLocation

3. Allocation Processing
   |-- Active PDAs retrieved for gas day
   |-- Allocation method applied per location
   |-- AllocQty computed for each contract
   |-- Results stored in ALCTRL_ALLOC and ALTRAN_ALLOC

4. Allocation Review
   |-- DailyAllocatedQuantityMaintenanceController
   |-- Operators review allocated quantities
   |-- Manual overrides applied if needed
   |-- Allocation approved or sent for reprocessing
```

### Workflow 3: Monthly Allocation

```
Monthly Allocation Workflow:

1. Month-End Data Aggregation
   |-- All daily measurements aggregated for the month
   |-- All daily allocations reviewed and finalized
   |-- Late-arriving measurements included per lag time

2. Monthly Allocation Processing
   |-- Monthly PDAs applied
   |-- Monthly allocation method executed
   |-- Final monthly AllocQty computed per contract

3. Monthly Review and Posting
   |-- MonthlyAllocatedQuantityMaintenanceController
   |-- Operators review monthly totals
   |-- Adjustments made for measurement corrections
   |-- Monthly allocation posted for billing

4. PPA Creation (if reallocation needed)
   |-- Previous monthly allocations saved as PPA
   |-- Reallocation executed with updated data
   |-- Adjustment quantities calculated
```

### Workflow 4: Measurement Entry

```
Measurement Entry Workflow:

1. Meter Data Collection
   |-- SCADA/meter data received
   |-- Hourly volumes captured per location

2. Measurement Load
   |-- QPTMAllocationServiceExt_Measurement processes data
   |-- Hourly records written to ALCTRL_MEAS_VOL
   |-- Historical records maintained in ALCTRL_MEAS_VOL_HIST

3. Validation
   |-- Measurement values checked for reasonableness
   |-- Missing hours flagged
   |-- Duplicate measurements handled

4. Aggregation
   |-- Hourly values summed to daily totals
   |-- Daily values summed to monthly totals
   |-- Aggregate location rollup triggered
```

### Workflow 5: Reallocation

```
Reallocation Workflow:

1. Trigger Identified
   |-- Measurement correction received
   |-- PDA revision submitted
   |-- Manual reallocation requested

2. PPA Snapshot
   |-- Current allocation values saved as PPA
   |-- PPA records locked (read-only)

3. Reallocation Processing
   |-- Updated measurements and/or PDAs loaded
   |-- Allocation methods re-applied
   |-- New AllocQty values computed

4. Adjustment Calculation
   |-- New AllocQty - PPA AllocQty = Adjustment
   |-- Adjustments posted to billing/settlement
   |-- Audit trail maintained
```

---

## Overrides

### Allocation Overrides

**Allocation Overrides** allow operators to manually adjust allocated quantities, bypassing the standard allocation method calculation. Overrides are tracked through `AllocationOverrideDO`.

### Override Scenarios

| Scenario | Description |
|----------|-------------|
| **Meter Error** | Measurement device malfunction requires manual volume adjustment |
| **Contractual Agreement** | Off-system agreement between parties requires specific volume assignment |
| **Operational Emergency** | Pipeline operational issues require manual allocation adjustments |
| **Reconciliation** | Month-end reconciliation reveals discrepancies requiring correction |

### Override Business Rules

1. **Override quantities take precedence** over calculated allocation quantities
2. **Override reason must be documented** for audit purposes
3. **Overrides do not change the PDA** -- they only affect the final allocation output
4. **Overrides are versioned** -- each override creates a new record, preserving the history
5. **Sum of overrides plus calculated allocations must still equal the measured volume** at the location (balance constraint)

---

## Glossary

### Terms and Abbreviations

| Term | Definition |
|------|------------|
| **ALLOC** | Allocations -- the system for distributing measured gas volumes to contracts |
| **PDA** | Predetermined Allocation -- shipper-submitted document specifying allocation instructions |
| **PRT** | Pro-Rata allocation method -- distributes proportionally based on scheduled quantities |
| **PRI** | Priority allocation method -- distributes based on H/L/B priority ranking |
| **PCT** | Percentage allocation method -- distributes based on fixed percentages |
| **AMT** | Amount allocation method -- assigns fixed volume amounts |
| **SchdQty** | Scheduled Quantity -- quantity scheduled for transportation from CAS/nominations |
| **AllocQty** | Allocated Quantity -- quantity allocated to a contract after applying allocation method |
| **MeasQty** | Measured Quantity -- actual measured volume at a location from meters |
| **PPA** | Previously Posted Allocations -- snapshot of prior allocation values before reallocation |
| **BA** | Business Associate -- entity (shipper, operator) interacting with the system |
| **TSP** | Transportation Service Provider -- pipeline company providing transportation services |
| **MDQ** | Maximum Daily Quantity -- maximum contractual daily volume |
| **H/L/B** | High/Low/Base priority codes used in PRI allocation method |
| **Aggregate Location** | Parent location that rolls up volumes from child locations |
| **Penalty Schedule** | Rules defining financial consequences for allocation imbalances |
| **Reallocation** | Re-running allocation with updated data (measurements, PDAs) |
| **Override** | Manual adjustment to calculated allocation quantities |
| **Gas Day** | Operational 24-hour period for pipeline operations (typically 9 AM to 9 AM) |
| **Accounting Month** | Calendar month used for billing and settlement purposes |
| **Flow Direction** | Receipt (R) or Delivery (D) indicating gas entering or leaving the pipeline |
| **Duration Code** | Specifies whether allocation is daily or monthly |
| **Imbalance** | Difference between allocated and scheduled quantities |
| **Cashout** | Financial settlement of imbalance volumes at a specified price |

### Related Processes

- **Capacity Scheduling Allocations (CAS)**: Produces scheduled quantities that feed into allocation processing
- **Nominations (NN)**: Shippers submit nominations that determine scheduled quantities
- **Confirmations (CF)**: Validates scheduled quantities against counterparty agreements
- **Billing (BL)**: Uses monthly allocated quantities for invoicing
- **Measurement (MS)**: Provides actual measured volumes used in allocation
- **Contracts (K)**: Define the contractual terms and allocation methods per shipper

---

## Business Rules Summary

### Critical Business Rules

1. **PDA Required**: Allocation processing requires an active PDA for each location/direction/period
2. **Balance Constraint**: Sum of allocated quantities at a location must equal the measured volume
3. **Percentage Totals**: PCT method PDA detail lines must sum to 100%
4. **Priority Order**: PRI method fills H before B before L
5. **PPA Preservation**: PPA records are immutable once created
6. **Override Precedence**: Manual overrides supersede calculated allocations
7. **Measurement Source**: Actual measurements take precedence over scheduled quantities
8. **Aggregate Rollup**: Parent location volumes must equal sum of child location volumes
9. **Effective Dates**: PDAs and allocation plans must be effective for the processing period
10. **Accounting Month Lag**: Late-arriving measurements honored within ACCTG_MTH_LAG_TIME window

---

## Related Documentation

- **Architecture**: [architecture.md](./architecture.md) - Technical implementation details
- **Troubleshooting**: [troubleshooting.md](./troubleshooting.md) - Common issues and solutions

---

*Last updated: 2026-03-03*
*Document version: 1.0*
