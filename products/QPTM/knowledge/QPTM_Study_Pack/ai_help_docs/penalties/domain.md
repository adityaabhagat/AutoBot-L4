---
title: Penalties (PEN) - Domain Concepts
category: domain
feature: Penalties (PEN)
related_repos: Web, Batch
keywords: PEN, penalties, penalty submission, penalty results, penalty type, penalty basis, hourly penalty schedule, imbalance pooling, critical period, tolerance, inventory, allocations, cashout, OBA, CPD, CPR, IMP
last_updated: 2026-03-03
---

# Penalties (PEN) - Domain Concepts

## Overview

This document explains the **business concepts** behind the Penalties (PEN) feature in the QPTM system. It focuses on WHAT the system does from a business perspective, explaining domain terminology, business rules, and workflows for gas pipeline penalty management.

For technical implementation details, see [Architecture Documentation](./architecture.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Penalty Types](#penalty-types)
3. [Penalty Basis Codes](#penalty-basis-codes)
4. [Penalty Submission Workflow](#penalty-submission-workflow)
5. [Penalty Results Workflow](#penalty-results-workflow)
6. [Hourly Penalty Schedules](#hourly-penalty-schedules)
7. [Tolerance Bands](#tolerance-bands)
8. [Penalty Calculations and Quantities](#penalty-calculations-and-quantities)
9. [Account-Penalty Association](#account-penalty-association)
10. [Type of Charge (TOC) Rules and TOS Integration](#type-of-charge-toc-rules-and-tos-integration)
11. [Approval and Processing Workflow](#approval-and-processing-workflow)
12. [Tier and Pooling Details](#tier-and-pooling-details)
13. [Key Business Rules](#key-business-rules)
14. [Glossary](#glossary)

---

## System Overview

### What is Penalties (PEN)?

**Penalties (PEN)** is the feature responsible for managing financial penalties assessed against shippers on a natural gas pipeline. These penalties arise when shippers deviate from their scheduled quantities -- either by taking too much or too little gas compared to what was nominated and confirmed. The penalty system ensures pipeline operational balance and incentivizes shippers to maintain accurate nominations.

**Business Purpose:**
- Define and manage penalty configurations (Penalty Submission)
- Associate inventory accounts with penalty definitions for tracking
- Calculate penalty amounts based on scheduled vs allocated vs measured quantities
- Review, approve, and process penalty calculation results (Penalty Results)
- Support hourly penalty schedules with configurable tolerance bands
- Enable tiered penalty rate structures and pooling-based penalty calculations

### Key Business Value

- **Pipeline Operational Balance**: Incentivizes shippers to maintain accurate nominations and reduce imbalances
- **Revenue Recovery**: Captures penalty charges for contractual violations
- **Regulatory Compliance**: Supports FERC tariff requirements for penalty assessment
- **Flexible Configuration**: Supports multiple penalty types, basis codes, and tolerance mechanisms
- **Transparency**: Provides detailed results with tier breakdowns and pool detail visibility

---

## Penalty Types

Penalty types classify the nature of the penalty being assessed. Each type is stored in the `QCODE_PENALTY_TYPE` code table and is identified by a `PenaltyTypeCode`.

### Defined Penalty Type Codes

| Code | Name | Description |
|------|------|-------------|
| `IMP` | Imbalance Pooling | Penalty for imbalances that exceed allowable pooling thresholds. Applied when a shipper's actual gas flow deviates from the scheduled quantity beyond the permitted tolerance. |
| `CPD` | Critical Period Delivery | Penalty applied during critical operational periods when delivery deviations are more costly to the pipeline. Assessed on the delivery (outflow) side. |
| `CPR` | Critical Period Receipt | Penalty applied during critical operational periods for receipt-side deviations. Assessed on the receipt (inflow) side. |

### Penalty Type Properties

Each penalty type record in `QCODE_PENALTY_TYPE` includes:
- **PenaltyTypeCode** (PK): Short string code (up to 3 characters)
- **TspNo** (PK): TSP number identifying which pipeline the type belongs to
- **PenaltyBasisCode**: Determines whether the penalty is calculated based on Allocations (`AL`) or Inventory (`IN`)

---

## Penalty Basis Codes

The **Penalty Basis Code** determines how penalty-eligible accounts and quantities are evaluated. It is retrieved from the `QCODE_PENALTY_TYPE` code table via the `CheckPenaltyBasis` service method.

| Code | Name | Behavior |
|------|------|----------|
| `AL` | Allocations | Penalty is based on allocation quantities. The submission screen requires a Location Group (LocGrpId/LocGrpNm). Account selection grids are NOT shown -- only the Location Group picker. |
| `IN` | Inventory | Penalty is based on inventory account quantities. The submission screen shows Available/Selected account grids for associating inventory accounts with the penalty definition. Location Group fields may be hidden. |

The penalty basis code controls the entire workflow behavior for both Penalty Submission and Penalty Results:
- For **Allocations** basis: The save operation only persists the penalty header with a Location Group reference.
- For **Inventory** basis: The save operation manages the penalty header AND its child `PenaltyIdDtl` records, each linking to an Inventory Account.

---

## Penalty Submission Workflow

Penalty Submission is the screen where pipeline operators define penalty configurations and associate them with accounts or location groups.

### Workflow Steps

1. **Set Parameters**: User selects TSP Number, Penalty Type, Effective Date From, and optionally Effective Date To.
2. **Check Penalty Basis**: System retrieves the `PenaltyBasisCode` for the selected penalty type.
3. **Query/Retrieve Accounts** (Inventory basis only):
   - Retrieves all Inventory Account Headers for the TSP
   - Attaches Service Requester (Business Associate) names to accounts
   - Attaches Division information from Contract User Defined fields
   - Filters accounts by Penalty Relation (TOS-TOC rule cross-reference)
   - Splits accounts into "Available" and "Selected" lists based on existing PenaltyIdDtl records
4. **User Selects Accounts**: User moves accounts between Available and Selected grids.
5. **Save**:
   - For Allocations basis: Saves header with Location Group ID
   - For Inventory basis: Adds/removes `PenaltyIdDtl` child records based on the Available/Selected account state
6. **Penalty ID Assignment**: On first save, the system generates a new Penalty ID; subsequent saves use the existing ID.

### Required Fields for Save

- TSP Number
- Penalty Type Code
- Effective Date From
- Penalty Description
- Location Group ID and Name (Allocations basis only)

---

## Penalty Results Workflow

Penalty Results is the screen where pipeline operators review, approve, and manage calculated penalty records. Results are generated by the batch penalty calculation process.

### Query Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| TSP Number | Yes | Pipeline identifier |
| Accounting Month | No | Month for billing purposes (filters by first/last day of month) |
| Production Month | No | Month of gas production (filters by first/last day of month) |
| Contract Number | No | Specific contract to filter by |
| Unapproved Records Only | No | Filters to show only records where `IsApprove = false` |
| Unprocessed Records Only | No | Filters to show only records where `IsProc = false` |

### Result Record Fields

Each penalty result (from `BLTRAN_INVOICE_PENALTY_HDR`) contains:
- **InvoicePenaltyId**: Unique identifier for the calculated penalty record
- **PenaltyId**: Reference back to the penalty definition (from submission)
- **PenaltyTypeCode**: The type of penalty
- **CtrNo / BpNo / AmendNo**: Contract, Business Partner, and Amendment references
- **ActivityDate**: Date of the activity generating the penalty
- **AcctgMth / ProdMth**: Accounting and Production months
- **TocCode / ChargeBasisCode**: Type of Charge and charge basis
- **AllocEngQty / AllocVolQty**: Allocated energy and volume quantities
- **SchdEngQty / SchdVolQty**: Scheduled energy and volume quantities
- **PenaltyEngQty / PenaltyVolQty**: The calculated penalty quantities
- **Rate**: The penalty rate applied
- **PenaltyAmt**: The calculated penalty dollar amount
- **IsApprove / IsProc**: Approval and processing status flags
- **LocId1 / LocId2**: Location identifiers
- **FlowDirection**: Direction of gas flow
- **RateHdrId / RateDtlId**: Rate table references
- **DailyImbalQty / DailyTradeQty**: Daily imbalance and trade quantities
- **InvAllocRecQty / InvAllocDelQty**: Inventory allocation receipt and delivery quantities
- **Comments**: Free-text comments field

---

## Hourly Penalty Schedules

Hourly Penalty Schedules define hour-by-hour penalty parameters for a gas day. They allow pipelines to configure different tolerance thresholds for each hour of the day.

### Structure

- **Schedule Header** (`KCTRL_HRLY_PENALTY_SCHD_HDR`): Defines the schedule with a Schedule ID, TSP, effective date range, schedule name, and hourly penalty type code.
- **Schedule Detail** (`KCTRL_HRLY_PENALTY_SCHD_DTL`): Contains one record per hour (24 total) with tolerance values for each hour.

### Key Properties

| Property | Description |
|----------|-------------|
| SchdId | Unique schedule identifier |
| SchdNm | Human-readable schedule name |
| HrlyPenaltyTypeCode | Determines tolerance mode: `D` (Discrete) or `P` (Percent) |
| EffDateFrom / EffDateTo | Effective date range for the schedule version |

### Effective Dating

Hourly Penalty Schedules support effective dating, allowing multiple versions of a schedule over time. The system uses `IQEffectiveDated` interface for managing time-sliced schedule data.

---

## Tolerance Bands

Tolerance bands define the range within which quantity deviations are permitted before penalties apply. They are configured per hour in the Hourly Penalty Schedule Detail.

### Tolerance Types

| Type | Fields | When Used |
|------|--------|-----------|
| **Discrete (D)** | `HighToleranceQty`, `LowToleranceQty` | When `HrlyPenaltyTypeCode = "D"`. Tolerance is expressed as absolute quantity values. |
| **Percent (P)** | `HighTolerancePct`, `LowTolerancePct` | When `HrlyPenaltyTypeCode = "P"`. Tolerance is expressed as percentage values. |

### Clearing Behavior on Save

When saving an hourly penalty schedule:
- If the type is **Discrete**: The system clears `HighTolerancePctAsPct` and `LowTolerancePctAsPct` fields.
- If the type is **Percent**: The system clears `HighToleranceQty` and `LowToleranceQty` fields.

This ensures only the relevant tolerance mode fields contain values.

---

## Penalty Calculations and Quantities

Penalty calculations involve comparing scheduled quantities against allocated or measured quantities to determine deviation amounts.

### Quantity Types in Results

| Quantity | Column | Description |
|----------|--------|-------------|
| Scheduled Energy | `SCHD_ENG_QTY` | Energy quantity the shipper was scheduled to flow |
| Scheduled Volume | `SCHD_VOL_QTY` | Volume quantity the shipper was scheduled to flow |
| Allocated Energy | `ALLOC_ENG_QTY` | Actual allocated energy quantity |
| Allocated Volume | `ALLOC_VOL_QTY` | Actual allocated volume quantity |
| Penalty Energy | `PENALTY_ENG_QTY` | Calculated penalty energy quantity |
| Penalty Volume | `PENALTY_VOL_QTY` | Calculated penalty volume quantity |
| Penalty Amount | `PENALTY_AMT` | Calculated monetary penalty amount |
| Daily Imbalance | `DAILY_IMBAL_QTY` | Daily imbalance quantity |
| Daily Trade | `DAILY_TRADE_QTY` | Daily trade quantity |
| Inv Alloc Receipt | `INV_ALLOC_REC_QTY` | Inventory allocation receipt quantity |
| Inv Alloc Delivery | `INV_ALLOC_DEL_QTY` | Inventory allocation delivery quantity |

### Unit of Measure Fields

- **EngUomCode**: Energy unit of measure (e.g., DTH, MMBTU)
- **VolUomCode**: Volume unit of measure (e.g., MCF)
- **AmtUomCode**: Currency unit of measure
- **BillUomCode**: Billing unit of measure
- **BtuFactor**: BTU conversion factor
- **ConvFactor**: General conversion factor

---

## Account-Penalty Association

The system links inventory accounts to penalty definitions through `BLCTRL_PENALTY_DTL` records.

### Filtering Logic

When querying available accounts for penalty association, the system applies a multi-step filter:

1. **TSP Filter**: Accounts must belong to the selected TSP
2. **Contract Lookup**: Each account's primary contract is retrieved to determine its Type of Service (TOS)
3. **NCTS Exclusion**: Accounts with TOS code `NCTS` are excluded (TEC/LDC-specific rule)
4. **TOC Rule Matching**: Type of Charge rules are checked for the penalty type with `IncludeTypeCode = "I"`
5. **TOS-TOC Cross-Reference**: The TOS-TOC rule cross-reference table is checked for active rules as of the effective date

Only accounts that pass all filter steps appear in the Available Accounts grid.

### Division Assignment

Accounts are enriched with Division information from the `ContractUserDefined` table, using the `UserDef1` field. This provides grouping context on the submission screen.

---

## Type of Charge (TOC) Rules and TOS Integration

Penalty eligibility depends on the intersection of:
- **Type of Charge (TOC)** rules configured for the TSP
- **Penalty Type Code** associated with specific TOC rules
- **Type of Service (TOS)** codes from the shipper's contract
- **TOS-TOC Rule Cross-Reference** records valid as of the effective date

The `FilterAccountsByPenaltyRelation` method implements this complex relationship filtering:
1. Retrieves all TOC codes for the TSP
2. Filters TOC codes to those with rules including the selected Penalty Type (with `IncludeTypeCode = "I"`)
3. For each account, gets the contract's TOS code
4. Checks TOS-TOC cross-reference table for valid records as of the effective date

---

## Approval and Processing Workflow

Penalty results go through two status stages:

### Approval (`IsApprove`)
- **Unapproved**: Newly calculated penalty records default to unapproved
- **Approved**: Operator reviews and approves the penalty record
- The Penalty Results screen supports filtering for unapproved records only

### Processing (`IsProc`)
- **Unprocessed**: Approved records awaiting downstream processing (e.g., invoicing)
- **Processed**: Records that have been sent to invoicing or other downstream systems
- The Penalty Results screen supports filtering for unprocessed records only

---

## Tier and Pooling Details

Penalty Results support two levels of detail beyond the header:

### Tier Details (`BLTRAN_INVOICE_PENALTY_DTL`)
- Provides breakdown of penalty calculations by rate tier
- Each tier detail record includes a `TierDtlDescr` for the tier description
- Accessible via the "Tier Details" tab in the Penalty Details popup
- Child records of `PenaltyResultsHdrDO`

### Pool Details (`BLTRAN_INVOICE_PENALTY_POOLDTL`)
- Provides penalty pooling breakdown details
- Pool details tab is only rendered when pool detail records exist
- Accessible via the "Pooling Details" tab in the Penalty Details popup
- Child records of `PenaltyResultsHdrDO`

---

## Key Business Rules

1. **Required Parameters for Query**: TSP Number, Penalty Type, and Effective Date From must be specified before querying penalty submission data.
2. **Required Parameters for Save**: TSP Number, Penalty Type, Effective Date From, and Penalty Description are required. For Allocations basis, Location Group ID and Name are additionally required.
3. **NCTS Exclusion**: Accounts with the `NCTS` Type of Service code are automatically excluded from penalty submission. This is a hard-coded rule specific to TEC (LDC) clients.
4. **Penalty Basis Determines UI Behavior**: The Penalty Basis Code (`AL` or `IN`) fundamentally changes the Penalty Submission screen behavior -- controlling whether the account selection grids or the Location Group picker are displayed.
5. **Account Filtering by TOS-TOC Rules**: Only accounts with valid TOS-TOC cross-reference entries for the selected penalty type as of the effective date are eligible for penalty association.
6. **Effective Date Defaults**: Effective Date From defaults to the current date; Effective Date To defaults to `9000-12-31` (end of time).
7. **Hourly Penalty Schedule Defaults to 24 Hours**: When creating a new hourly penalty schedule, the system generates 24 detail rows (one per gas hour) based on the TSP's hourly profile configuration.
8. **Tolerance Mode Exclusivity**: When saving an hourly penalty schedule, the system clears tolerance fields that do not match the selected penalty type (Discrete vs Percent) to prevent data inconsistency.
9. **Penalty Results Are Batch-Generated**: Penalty result records in `BLTRAN_INVOICE_PENALTY_HDR` are generated by the batch process; the Penalty Results screen is for review, approval, and management only.
10. **Previously Posted Allocations (PPA)**: Penalty results include a `PpaSrcCode` field supporting PPA-related penalty tracking.

---

## Glossary

| Term | Definition |
|------|------------|
| **Penalty ID** | Unique identifier for a penalty definition (from Penalty Submission) |
| **Invoice Penalty ID** | Unique identifier for a calculated penalty result record |
| **Penalty Type Code** | Classification code for the penalty (IMP, CPD, CPR) |
| **Penalty Basis Code** | Determines whether penalty is based on Allocations (AL) or Inventory (IN) |
| **TOS** | Type of Service -- classification of the transportation service agreement |
| **TOC** | Type of Charge -- classification of charges that can be applied |
| **TOS-TOC Rule Cross-Reference** | Mapping table linking types of service to types of charge rules |
| **Inventory Account** | An account tracking gas inventory positions for a shipper |
| **Location Group** | A logical grouping of pipeline locations used for allocation-based penalties |
| **Hourly Penalty Schedule** | Configuration defining tolerance bands and penalty parameters for each hour of a gas day |
| **Tolerance Band** | The acceptable range of deviation before penalties apply |
| **Discrete Tolerance** | Tolerance expressed as absolute quantity values |
| **Percent Tolerance** | Tolerance expressed as percentage of scheduled quantity |
| **TSP** | Transportation Service Provider (the pipeline company) |
| **Schedule ID (SchdId)** | Unique identifier for an hourly penalty schedule |
| **Effective Dating** | Mechanism for managing time-versioned records with EffDateFrom/EffDateTo |
| **PPA** | Previously Posted Allocations -- adjustments to prior period allocations |
| **IsApprove** | Flag indicating whether a penalty result has been approved by an operator |
| **IsProc** | Flag indicating whether a penalty result has been processed for downstream systems |
| **Division** | Organizational grouping derived from Contract User Defined field (`UserDef1`) |
| **Business Associate (BP)** | The service requester/shipper entity associated with a contract |
| **NCTS** | A Type of Service code specific to TEC (LDC) clients, excluded from penalty submission |
| **Gas Hour** | One of the 24 hours in a gas day, defined by the TSP's hourly profile |

---

*Last updated: 2026-03-03*

*Document version: 1.0*
