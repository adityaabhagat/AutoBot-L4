---
title: Confirmations (CONF) - Domain Concepts
category: domain
feature: Confirmations (CONF)
related_repos: Web, Batch
keywords: CONF, confirmation, confirmation response, TSP, reconciliation, nomination-to-confirmation, scheduled quantity, confirmed quantity, variance, EPSQ, reduction reason, confirmation method, hourly profile, confirmation level, cycle, path balancing, unbalanced, filter, ConfMethCode, ReductRsnCode, IsHrProf, CFCTRL_CONF_LVL
last_updated: 2026-03-03
---

# Confirmations (CONF) - Domain Concepts

## Overview

This document explains the **business concepts** behind Confirmations in the QPTM system. It focuses on WHAT the system does from a business perspective, explaining domain terminology, business rules, and workflows.

For technical implementation details, see [Architecture Documentation](./architecture.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Business Concepts](#core-business-concepts)
3. [Confirmation Response Workflow](#confirmation-response-workflow)
4. [Cycles](#cycles)
5. [Variance Analysis](#variance-analysis)
6. [EPSQ (Estimated Pipeline Safety Quantity)](#epsq-estimated-pipeline-safety-quantity)
7. [Confirmation Methods and Reduction Reasons](#confirmation-methods-and-reduction-reasons)
8. [Hourly Profiles](#hourly-profiles)
9. [Confirmation Levels](#confirmation-levels)
10. [Path Balancing](#path-balancing)
11. [Confirmation Summary](#confirmation-summary)
12. [Filter Types](#filter-types)
13. [Business Workflows](#business-workflows)
14. [Glossary](#glossary)

---

## System Overview

### What are Confirmations?

**Confirmations** represent the Transporting Service Provider's (TSP) response to nominations submitted by shippers. After a shipper nominates gas for transportation, the TSP confirms the quantities that will actually flow on the pipeline. The confirmation process reconciles what was nominated with what the TSP can physically and contractually support.

**Business Purpose:**
- Provide the TSP's official response to shipper nominations
- Reconcile nominated quantities against pipeline capacity and operational constraints
- Track confirmed quantities versus scheduled/nominated quantities
- Support variance analysis for operational planning and imbalance management
- Enable hourly profile confirmation for intraday flow management
- Enforce EPSQ limits and path balancing requirements

### Key Business Value

- **Operational Accuracy**: Ensures confirmed quantities reflect actual pipeline capability
- **Imbalance Prevention**: Detects and flags unbalanced paths before gas flows
- **Regulatory Compliance**: Maintains NAESB confirmation cycle deadlines
- **Variance Tracking**: Provides visibility into nomination-to-confirmation discrepancies
- **Hourly Granularity**: Supports hourly flow profiles for precise scheduling
- **TSP Accountability**: Creates auditable confirmation records for each cycle

---

## Core Business Concepts

### 1. Confirmation in the Gas Pipeline Context

A **Confirmation** is the TSP's formal response to a nomination. When a shipper nominates gas for a specific gas day, the TSP evaluates the nomination against:
- Available pipeline capacity at each location
- Contractual obligations and capacity rights
- Operational constraints (maintenance, pressure, EPSQ)
- Balancing requirements across paths

The TSP then **confirms** the quantities, which may be equal to, less than, or (in rare cases with ratchet provisions) different from the nominated quantities.

### 2. TSP Reconciliation (Nomination-to-Confirmation Matching)

**TSP Reconciliation** is the process of matching nominations to confirmations. Each confirmation record links back to the original nomination, enabling:
- Side-by-side comparison of nominated vs. confirmed quantities
- Identification of reductions and their reasons
- Tracking of which cycle the confirmation applies to
- Aggregation of confirmation data by location, shipper, or path

**Key Matching Attributes:**
- TSP Number (TSP_NO)
- Gas Day
- Cycle ID
- Nomination ID
- Location (receipt/delivery)
- Contract Number
- Service Requester

### 3. Scheduled vs Confirmed Quantities

| Quantity Type | Source | Description |
|---------------|--------|-------------|
| **Nominated Quantity (NomQty)** | Shipper | What the shipper requested |
| **Scheduled Quantity (SchdQty)** | CAS Process | What CAS allocated after capacity reduction |
| **Confirmed Quantity (ConfQty)** | TSP Confirmation | What the TSP confirmed will actually flow |

**Business Rule**: The confirmed quantity represents the TSP's final determination of what will flow. It may differ from both the nominated and scheduled quantities based on operational conditions, EPSQ limits, or path balancing needs.

### 4. Service Requester and Counterparty

**Service Requester (SR)**: The shipper who submitted the nomination and receives the confirmation response.

**Counterparty (CP)**: The business party on the other end of the transaction at the confirmation location.

**Business Rule**: Confirmations must be associated with the correct service requester and contract to ensure accurate tracking and billing.

---

## Confirmation Response Workflow

### Overview

The confirmation response workflow describes the end-to-end process from nomination receipt through confirmation submission.

```
Confirmation Response Workflow:

1. Nomination Received
   |-- Shipper submits nomination for gas day/cycle
   |-- Nomination validated and scheduled by CAS
   v

2. Confirmation Preparation
   |-- TSP reviews scheduled quantities
   |-- System loads nomination data into confirmation grid
   |-- Operator reviews quantities by location/shipper/path
   v

3. Confirmation Entry
   |-- TSP enters confirmed quantities (ConfQty)
   |-- Sets confirmation method (ConfMethCode)
   |-- Provides reduction reason if ConfQty < NomQty (ReductRsnCode)
   |-- Optionally enters hourly profile (IsHrProf)
   v

4. Confirmation Validation
   |-- Validate ConfQty >= 0
   |-- Validate ConfQty does not fall below EPSQ
   |-- Validate path balancing (if ConfRunPathBalForPnt enabled)
   |-- Validate hourly profile totals match daily total
   |-- Run 4-level validation (Security, FK, Line, Business)
   v

5. Confirmation Submission
   |-- Submit confirmation for the cycle
   |-- Trigger CFPROCESS batch process
   |-- Update confirmation status
   |-- Notify downstream systems (EDI, balancing)
   v

6. Post-Submission
   |-- Confirmation available for viewing in summary
   |-- Variance analysis available (NomQty - ConfQty)
   |-- Data flows to allocation and billing processes
```

### Edit Closed Cycle

**Business Rule**: Under specific conditions, a TSP operator may need to edit a confirmation for an already-closed cycle. This requires special security permissions and is controlled by the `GetActions` logic with the "Edit Closed Cycle" action. This capability allows corrections after a cycle deadline has passed.

---

## Cycles

### Confirmation Cycles

Confirmations follow the same cycle structure as nominations. Each cycle represents a specific submission window during which the TSP must respond.

| Cycle ID | Cycle Name | Description |
|----------|------------|-------------|
| **1** | TIMELY | Primary day-ahead confirmation cycle; TSP responds to timely nominations |
| **2** | EVENING | Evening confirmation cycle; TSP responds to evening nomination adjustments |
| **3** | ID1 | Intraday 1; first same-day confirmation cycle |
| **4** | ID2 | Intraday 2; second same-day confirmation cycle |
| **6** | ID3 | Intraday 3; third same-day confirmation cycle |

**Business Rules:**
- The TSP must respond within each cycle's deadline
- Later cycle confirmations can revise earlier cycle confirmations
- The system tracks the latest cycle confirmation for each nomination
- The `DefaultToOpenConfirmationCycle` configuration controls which cycle is selected by default in the UI
- The `ShowPrevCycleDataEnabled` configuration controls whether previous cycle data is displayed

### Cycle Filtering

The system supports filtering confirmations by cycle status:
- **Next Open Cycle**: Shows data for the next cycle that has not yet been confirmed
- **Previous Day Cycle**: Shows data from the prior gas day's cycles for reference

---

## Variance Analysis

### Nomination-to-Confirmation Variance

**Variance** is the difference between the nominated quantity and the confirmed quantity:

```
Variance = NomQty - ConfQty
```

| Variance | Meaning | Implication |
|----------|---------|-------------|
| **Variance = 0** | Full confirmation | TSP confirmed the entire nominated quantity |
| **Variance > 0** | Partial confirmation (cut) | TSP reduced the nomination; a reduction reason is required |
| **Variance < 0** | Over-confirmation | Rare; may indicate ratchet or correction scenario |

**Business Purpose of Variance Analysis:**
- Identify locations or shippers with frequent cuts
- Detect operational constraints affecting specific pipeline segments
- Support imbalance management and penalty assessment
- Provide data for dispute resolution between shippers and TSP

### Variance Reporting

Variance data is available in the Confirmation Summary view, aggregated by:
- **By Location**: Shows variance totals for each receipt/delivery point
- **By Shipper**: Shows variance totals for each service requester
- **By Path**: Shows variance totals for each nomination path

---

## EPSQ (Estimated Pipeline Safety Quantity)

### What is EPSQ?

**EPSQ (Estimated Pipeline Safety Quantity)** is the minimum quantity of gas that must flow at a location to maintain safe pipeline operations. EPSQ represents operational minimums below which the pipeline cannot safely function.

**Business Rule**: A confirmation quantity cannot be reduced below the EPSQ value for a location. If a TSP attempts to confirm a quantity below EPSQ, the system will reject the confirmation.

### EPSQ in the Confirmation Process

- EPSQ values are defined per location and gas day
- During confirmation entry, the system validates that ConfQty >= EPSQ
- If nominations are already below EPSQ, the TSP may need to confirm at the EPSQ minimum
- EPSQ violations are flagged during validation and must be resolved before submission

### EPSQ Example

```
Location: Receipt Point 12345
EPSQ: 500 Dth
Nominated Quantity: 800 Dth

Valid Confirmation: 600 Dth (above EPSQ)
Invalid Confirmation: 400 Dth (below EPSQ - rejected)
Minimum Confirmation: 500 Dth (at EPSQ floor)
```

---

## Confirmation Methods and Reduction Reasons

### Confirmation Method (ConfMethCode)

The **Confirmation Method** indicates how the confirmation quantity was determined.

**Common Confirmation Methods:**
- **Auto**: System-generated confirmation based on rules
- **Manual**: TSP operator entered the confirmed quantity manually
- **EDI**: Confirmation received via Electronic Data Interchange
- **Default**: Confirmation set to a default value (e.g., full confirmation)

### Reduction Reason (ReductRsnCode)

When a confirmation quantity is less than the nominated quantity, the TSP must provide a **Reduction Reason** explaining why the nomination was cut.

**Common Reduction Reasons:**
- **Capacity**: Insufficient pipeline capacity at the location
- **EPSQ**: Confirmation would fall below EPSQ minimum
- **Operational**: Operational constraint (maintenance, pressure issues)
- **Contractual**: Contract limitation or capacity release issue
- **Balancing**: Path balancing requirement necessitated the reduction
- **Other**: Other reason (requires explanation)

**Business Rule**: A reduction reason is required whenever ConfQty < NomQty. The system enforces this during validation.

---

## Hourly Profiles

### What are Hourly Profiles?

**Hourly Profiles (IsHrProf)** allow the TSP to specify confirmed quantities on an hour-by-hour basis for a gas day, rather than a single daily total. This provides granular control over intraday flow patterns.

### Hourly Profile Usage

- Stored in the `CFCTRL_CONF_HOURLY` table
- Each record contains 24 hourly quantity values (one per hour of the gas day)
- The sum of hourly quantities must equal the daily confirmed quantity
- Enabled on a per-confirmation basis via the `IsHrProf` flag

### Hourly Profile Business Rules

1. **Total Consistency**: The sum of all 24 hourly values must equal the daily ConfQty
2. **Non-Negative Hours**: Individual hourly values cannot be negative
3. **Profile Update**: When the daily total changes, hourly values must be redistributed
4. **Mismatch Detection**: The system flags hourly profile mismatches during validation

### Hourly Profile Example

```
Daily Confirmed Quantity: 2,400 Dth
Even Distribution: 100 Dth per hour (2,400 / 24)

Custom Profile Example:
Hours 1-6:   50 Dth/hr  =  300 Dth
Hours 7-18: 150 Dth/hr  = 1,800 Dth
Hours 19-24: 50 Dth/hr  =  300 Dth
Total:                    2,400 Dth (matches daily total)
```

---

## Confirmation Levels

### What are Confirmation Levels?

**Confirmation Levels (CFCTRL_CONF_LVL)** represent the hierarchical structure of confirmation data. Levels allow confirmations to be organized at different granularity levels for aggregation and reporting.

### Level Structure

Confirmation levels enable viewing and managing confirmations at multiple hierarchy levels:
- **Summary Level**: Aggregated view across all nominations for a location
- **Detail Level**: Individual nomination-level confirmation records
- **Plan Level**: Planned confirmation quantities (pre-submission)
- **Role Level**: Confirmation data by business party role

**Business Rule**: Confirmation level data must be consistent across all hierarchy levels. Changes at the detail level must roll up correctly to the summary level.

---

## Path Balancing

### What is Path Balancing?

**Path Balancing** ensures that the total confirmed receipt quantities equal the total confirmed delivery quantities across a nomination path. An **unbalanced path** occurs when receipts and deliveries do not match.

### Path Balancing Rules

- Controlled by the `ConfRunPathBalForPnt` configuration setting
- When enabled, the system validates that receipt and delivery confirmations balance
- Unbalanced paths are flagged and may prevent confirmation submission
- The `ConfUpdCallBalancingAfter` configuration controls when balancing is recalculated

### Unbalanced Path Detection

An unbalanced path is detected when:
```
Total Confirmed Receipts != Total Confirmed Deliveries (for a path)
```

**Business Impact:**
- Unbalanced paths indicate potential operational issues
- The TSP must resolve imbalances before confirming
- Persistent imbalances may result in penalties or operational flow orders

---

## Confirmation Summary

### What is the Confirmation Summary?

The **Confirmation Summary** provides an aggregated view of confirmation data across multiple dimensions. It is the primary screen used by TSP operators to review and manage confirmations.

### Summary Views

The confirmation summary supports multiple aggregation views:

| View | Description | Use Case |
|------|-------------|----------|
| **By Location** | Confirmation totals grouped by receipt/delivery location | Identify location-specific capacity issues |
| **By Shipper** | Confirmation totals grouped by service requester | Review shipper-specific confirmation status |
| **By Path** | Confirmation totals grouped by nomination path | Detect path imbalances and balancing issues |

### Summary Concepts

- **Confirmed Total**: Sum of all confirmed quantities for the filter criteria
- **Nominated Total**: Sum of all nominated quantities for comparison
- **Variance Total**: Aggregate variance (NomQty - ConfQty) for the selection
- **Unconfirmed Count**: Number of nominations without a confirmation response
- **Unbalanced Count**: Number of paths where receipts do not equal deliveries

---

## Filter Types

### Confirmation Filters

The confirmation system supports several filter types to help operators focus on relevant data:

| Filter | Description | Business Purpose |
|--------|-------------|------------------|
| **NextOpenCycle** | Shows data for the next cycle that is open for confirmation | Focus on pending work for the current cycle |
| **PreviousDayCycle** | Shows data from the prior gas day's cycles | Reference previous day's confirmations for continuity |
| **Unconfirmed** | Shows only nominations that have not yet been confirmed | Identify outstanding work items |
| **Unbalanced** | Shows only paths where receipts do not equal deliveries | Prioritize path balancing corrections |
| **ExcludeZero** | Excludes nominations/confirmations with zero quantities | Reduce noise in the confirmation grid |

**Business Rule**: Filters can be combined to narrow the view. For example, "NextOpenCycle + Unconfirmed" shows only pending confirmations for the current open cycle.

---

## Business Workflows

### Daily Confirmation Workflow

```
Daily Confirmation Process:

1. Pre-Confirmation (Morning)
   |-- CAS process completes scheduling
   |-- Scheduled quantities available for confirmation
   |-- TSP operator opens Confirmation Summary screen
   v

2. Timely Cycle Confirmation (Cycle 1)
   |-- Filter: NextOpenCycle (Timely)
   |-- Review nominated vs scheduled quantities
   |-- Enter confirmed quantities
   |-- Provide reduction reasons for cuts
   |-- Enter hourly profiles if required
   |-- Validate and submit
   v

3. Evening Cycle Confirmation (Cycle 2)
   |-- Review nomination changes from evening cycle
   |-- Confirm or adjust quantities
   |-- Submit evening confirmations
   v

4. Intraday Confirmations (Cycles 3, 4, 6)
   |-- Process intraday nomination changes
   |-- Confirm adjusted quantities
   |-- Validate path balancing
   |-- Submit intraday confirmations
   v

5. End-of-Day Review
   |-- Review confirmation summary
   |-- Check for unconfirmed nominations
   |-- Verify path balancing
   |-- Generate variance reports
```

### Month-End Confirmation Reconciliation

**Month-End Considerations:**
- Final confirmation for all gas days in the month
- Reconciliation of confirmed vs actual flow quantities
- Variance analysis for billing and imbalance settlement
- Confirmation data feeds into allocation and invoicing

### Special Handling Scenarios

**Scenario 1: EPSQ Constraint**
- TSP cannot confirm below EPSQ
- Must maintain minimum flow for safety
- May require coordination with shipper to adjust nomination

**Scenario 2: Closed Cycle Edit**
- Cycle deadline has passed
- Correction needed for submitted confirmation
- Requires "Edit Closed Cycle" permission
- Controlled by security configuration

**Scenario 3: Path Imbalance Resolution**
- Path receipts do not equal deliveries
- TSP must adjust confirmations to balance
- May require coordination across multiple shippers
- System flags unbalanced paths for attention

---

## Glossary

### Terms and Abbreviations

| Term | Definition |
|------|------------|
| **CONF** | Confirmations - the TSP's response to shipper nominations |
| **TSP** | Transporting Service Provider - the pipeline operator who confirms nominations |
| **NomQty** | Nominated Quantity - the quantity the shipper requested |
| **SchdQty** | Scheduled Quantity - the quantity allocated by the CAS process |
| **ConfQty** | Confirmed Quantity - the quantity the TSP confirmed will flow |
| **Variance** | The difference between nominated and confirmed quantities (NomQty - ConfQty) |
| **EPSQ** | Estimated Pipeline Safety Quantity - minimum flow required for safe operation |
| **ConfMethCode** | Confirmation Method Code - how the confirmation was determined |
| **ReductRsnCode** | Reduction Reason Code - why a nomination was cut during confirmation |
| **IsHrProf** | Hourly Profile flag - indicates confirmation has hour-by-hour quantities |
| **Path Balancing** | Ensuring total receipts equal total deliveries on a nomination path |
| **Unbalanced Path** | A path where confirmed receipts do not equal confirmed deliveries |
| **Cycle** | A nomination/confirmation submission window (Timely, Evening, ID1, ID2, ID3) |
| **Gas Day** | The operational period for pipeline operations (typically 9 AM to 9 AM) |
| **Service Requester (SR)** | The shipper who submitted the nomination |
| **Counterparty (CP)** | The business party on the other end of the transaction |
| **CFPROCESS** | Batch process triggered after confirmation submission |
| **CFCTRL_CONF** | Primary confirmation database table |
| **CFCTRL_CONF_LVL** | Confirmation levels table for hierarchical data |
| **MDQ** | Maximum Daily Quantity - contracted capacity limit |
| **Edit Closed Cycle** | Permission to modify confirmations after cycle deadline |

### Related Processes

- **Nominations (NOM)**: Input to the confirmation process - see [Nominations Domain](../nominations/domain.md)
- **Capacity Scheduling Allocations (CAS)**: Produces scheduled quantities that feed into confirmation - see [CAS Domain](../capacity-scheduling-allocations/domain.md)
- **Allocations (AL)**: Uses confirmed quantities for actual flow allocation
- **Billing (BL)**: Uses confirmed quantities for invoicing
- **EDI**: Exchanges confirmation data with TSPs electronically

---

## Business Rules Summary

### Critical Business Rules

1. **EPSQ Floor**: Confirmed quantities cannot be reduced below EPSQ for a location
2. **Reduction Reason Required**: A reduction reason must be provided when ConfQty < NomQty
3. **Cycle Deadlines**: Confirmations must be submitted within cycle deadlines
4. **Latest Cycle Wins**: Latest cycle confirmation overrides earlier cycles for the same nomination
5. **Path Balancing**: Total confirmed receipts must equal total confirmed deliveries on a path (when enabled)
6. **Hourly Profile Consistency**: Sum of hourly values must equal the daily confirmed quantity
7. **Non-Negative Quantities**: Confirmed quantities and hourly values cannot be negative
8. **Security Enforcement**: Confirmation entry requires QVpSOAConfirmationResponse security object
9. **Closed Cycle Protection**: Editing closed cycles requires special permissions
10. **Batch Trigger**: CFPROCESS batch is triggered after each confirmation submission

---

## Related Documentation

- **Architecture**: [architecture.md](./architecture.md) - Technical implementation details
- **Troubleshooting**: [troubleshooting.md](./troubleshooting.md) - Common issues and solutions
- **Nominations Domain**: [../nominations/domain.md](../nominations/domain.md) - Upstream nomination concepts
- **CAS Domain**: [../capacity-scheduling-allocations/domain.md](../capacity-scheduling-allocations/domain.md) - Scheduling and allocation concepts
- **QUICK_REFERENCE.md**: Feature mapping and keywords for CONF

---

*Last updated: 2026-03-03*
*Document version: 1.0*
