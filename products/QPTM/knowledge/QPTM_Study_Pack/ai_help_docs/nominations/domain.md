---
title: Nominations (NOM) - Domain Concepts
category: domain
feature: Nominations (NOM)
related_repos: Web, Batch
keywords: nomination, gas day, cycle, timely, evening, intraday, activity, submit, validate, service requester, receipt, delivery, shipper, path, PNT, PT, NAESB, MDQ, fuel, lease
last_updated: 2026-03-03
---

# Nominations (NOM) - Domain Concepts

## Overview

This document explains the **business concepts** behind Nominations in the QPTM system. It focuses on WHAT the system does from a business perspective, explaining domain terminology, business rules, and workflows.

For technical implementation details, see [Architecture Documentation](./architecture.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Business Concepts](#core-business-concepts)
3. [Gas Day and Cycles](#gas-day-and-cycles)
4. [Nomination Types](#nomination-types)
5. [Nomination Models](#nomination-models)
6. [Activity Workflow](#activity-workflow)
7. [Nomination Lifecycle](#nomination-lifecycle)
8. [Validation and Error Handling](#validation-and-error-handling)
9. [Quantities and Calculations](#quantities-and-calculations)
10. [Autogeneration](#autogeneration)
11. [Title Transfers](#title-transfers)
12. [Business Workflows](#business-workflows)
13. [Glossary](#glossary)

---

## System Overview

### What are Nominations?

**Nominations** are the fundamental mechanism by which shippers request transportation of natural gas on a pipeline. A shipper submits a nomination specifying how much gas to move, from where (receipt location), to where (delivery location), under which contract, and for which gas day(s).

**Business Purpose:**
- Allow shippers to request pipeline capacity for gas movement
- Validate nominations against contracts, locations, and business rules
- Track nomination cycles (timely, evening, intraday) for regulatory compliance
- Support NAESB (North American Energy Standards Board) nomination standards
- Calculate fuel requirements and heating factors
- Enable nomination lifecycle tracking from draft to submission

### Key Business Value

- **Capacity Utilization**: Enables efficient allocation of pipeline capacity to shippers
- **Regulatory Compliance**: Implements FERC and NAESB standards for nomination timing and processing
- **Operational Visibility**: Provides clear view of nominated vs. scheduled quantities
- **Multi-Cycle Support**: Handles timely, evening, and intraday nomination cycles
- **Audit Trail**: Complete lifecycle tracking from creation through submission

---

## Core Business Concepts

### Service Requester (SR)

The **Service Requester** (also called shipper) is the entity requesting gas transportation. Identified by:
- **SrBpNo** - Service Requester Business Partner Number (DUNS number)
- **SrCtrNo** - Service Requester Contract Number

A service requester must have a valid contract with the TSP (Transportation Service Provider) to nominate.

### Contracts

Nominations are tied to contracts that define:
- **MDQ (Maximum Daily Quantity)** - Maximum volume the shipper can nominate per day
- **MSQ (Maximum Storage Quantity)** - For storage contracts
- **MDWQ (Maximum Daily Withdrawal Quantity)** - For storage withdrawal
- **MDIQ (Maximum Daily Injection Quantity)** - For storage injection
- **TOS (Type of Service)** - Firm, Interruptible, etc.
- **Contract Period** - Effective date range
- **Path** - Default receipt-to-delivery route

### Locations

Each nomination involves two key locations:
- **Receipt Location (IdRecLoc)** - Where gas enters the pipeline (upstream)
- **Delivery Location (IdDelLoc)** - Where gas exits the pipeline (downstream)

Location types relevant to nominations:
- **Physical Locations** - Actual pipeline interconnects
- **Pool Locations** - Virtual aggregation points (NPPool, Cheyenne)
- **Virtual Locations** - Park, Loan, Payback, Makeup
- **Storage Locations** - Injection/withdrawal points
- **Lease Locations** - Production lease points

### TSP (Transportation Service Provider)

The pipeline operator managing the transportation. Each TSP has:
- TSP Number (TspNo) - Unique identifier
- TSP Preferences - Gas day start time, cycle configuration
- TSP-specific business rules and configurations

---

## Gas Day and Cycles

### Gas Day

A **Gas Day** is a 24-hour period defined by the TSP, typically starting at 9:00 AM Central Time (varies by TSP). Key concepts:

- **BegGasDay** - First day of a nomination's validity period
- **EndGasDay** - Last day of a nomination's validity period
- **Current Gas Day** - Determined by TSP preferences and system time
- Nominations can span multiple gas days within the same calendar month

### Nomination Cycles

Nominations are submitted in **cycles** that follow NAESB-mandated deadlines:

| Cycle | Category | Deadline Type | Description |
|-------|----------|---------------|-------------|
| **Timely** | NOM | ONT (OnTime) | Primary nomination cycle; submitted before gas flow begins |
| **Evening** | NOM | ONT | Secondary cycle for evening adjustments |
| **Intraday 1 (ID1)** | NOM | INT | First intraday adjustment cycle |
| **Intraday 2 (ID2)** | NOM | INT | Second intraday adjustment cycle |
| **Intraday 3 (ID3)** | NOM | INT | Third intraday adjustment cycle |

### Deadline Categories

| Code | Category | Description |
|------|----------|-------------|
| NOM | Nomination | Nomination submission deadlines |
| CNF | Confirmation | Confirmation cycle deadlines |
| SCH | Scheduling | Scheduling process deadlines |
| PDA | PDA | Predetermined allocation deadlines |

### Deadline Types

| Code | Type | Description |
|------|------|-------------|
| ONT | OnTime | Standard on-time deadline |
| INT | Intraday | Intraday nomination deadline |
| LAT | Latest | Latest acceptable nomination time |
| ITI | Internal | Internal nomination timing |
| ETI | External | External nomination timing |

### ENS Cycles

ENS (Electronic Nomination System) cycles are a TSP-specific designation that distinguishes ENS cycles from standard NAESB cycles. Some TSPs operate both ENS and NAESB cycles concurrently.

---

## Nomination Types

### By Transaction Type

| Type | Code | Description |
|------|------|-------------|
| **Path Nomination** | 2 | Standard point-to-point pipeline path nomination |
| **SR Transaction** | 5 | Service requester-initiated nomination |
| **Storage Injection** | 06 | Gas moving into storage |
| **Storage Withdrawal** | 07 | Gas moving out of storage |
| **Park** | PRK | Temporary gas parking |
| **Loan** | LND | Gas lending arrangement |
| **Payback** | PAY | Return of parked/loaned gas |
| **Makeup** | MAK | Makeup volume for imbalances |

### By Nomination Source

- **Manual Nominations** - Created by users through the UI
- **Auto-Generated (AGN)** - Created by system rules (autogeneration)
- **API Nominations** - Submitted via REST API
- **Lease Nominations** - From production lease agreements
- **Bulk Copy Nominations** - Copied from existing nominations

### K-Based vs. Volume-Based

- **Volume (VOL)** - Quantities in volumetric units (Dth)
- **Energy (ENG)** - Quantities in energy units (MMBtu); requires K-contract MDQ calculations

---

## Nomination Models

QPTM supports two NAESB nomination models:

### PNT Model (Path-Node-Transposition)

The **PNT model** is the NAESB 3.0 standard. Nominations are structured as:
- **Path Record** - Defines the receipt-to-delivery path with total quantity
- **Upstream (Receipt/Buy)** - Individual receipt nominations that feed the path
- **Downstream (Delivery/Sell)** - Individual delivery nominations from the path

The path record total must balance: Receipt Total = Delivery Total + Fuel

### PT Model (Path-Transposition)

The **PT model** (legacy) uses simpler point-to-point nominations without the up/down separation:
- Each nomination specifies receipt location, delivery location, and quantity
- No separate upstream/downstream components

### Pathed vs. Non-Pathed

- **Pathed** - Nominations follow a specific contract path (segment route)
- **Non-Pathed (SRK 99999)** - Default contract "99999" used when no specific path is defined

---

## Activity Workflow

### What is an Activity?

An **Activity** is a working set of nomination changes. Before nominations are submitted to the pipeline, they are saved as an activity (draft). Key concepts:

- **Activity Number (ActvNo)** - Unique identifier for the draft
- **Activity Description** - User-provided description
- **Activity Details** - The individual nomination records in the draft

### Activity States

| State | Description |
|-------|-------------|
| **Draft** | Activity created, nominations saved but not submitted |
| **Submitted** | Activity nominations submitted to the pipeline system |
| **Rejected** | Activity marked as inactive (rejected by internal user) |

### Activity Operations

1. **Save Activity** - Persist nomination changes as a draft
2. **Retrieve Activity** - Load a previously saved draft
3. **Submit Activity** - Validate and commit nominations to the system
4. **Reject Activity** - Mark activity as inactive (internal users only)
5. **Copy Activity** - Create a new activity from an existing one

---

## Nomination Lifecycle

### Complete Lifecycle Flow

```
1. CREATE/DRAFT
   User creates nomination records (manual, copy, import, or autogen)
   ↓
2. SAVE ACTIVITY
   Nominations saved as a draft activity (not yet submitted)
   ↓
3. VALIDATE
   System checks all business rules:
   - Security validation (user authorization)
   - Foreign key validation (contracts, locations exist)
   - Line validation (individual record rules)
   - Business validation (cross-record rules, MDQ checks)
   ↓
4. ERROR REVIEW
   If errors found:
   - User reviews validation errors
   - Fix errors and re-validate, OR
   - Override errors if authorized (through a specified end date)
   ↓
5. SUBMIT
   Nominations committed to the system:
   - Set IDs assigned (IdSetAdd for new, IdSetModify for changed)
   - Nominations stored in NNCTRL_NOM_HDR / NNCTRL_NOM_DTL
   - Lifecycle records created
   ↓
6. SCHEDULING
   Submitted nominations flow to CAS for scheduling:
   - Nomination classification (NNCLASSFY)
   - Transaction grouping
   - Capacity reduction if oversubscribed (SCREDUCE)
   ↓
7. CONFIRMATION
   TSP confirms scheduled quantities:
   - Confirmation response processing
   - Variance tracking (nominated vs. confirmed)
```

### Submission Modes

- **Full Submit** - Validate and submit all nominations in the activity
- **Submit by Contract** - Submit valid contracts even if others have errors
- **Partial Submit** - Filter out error nominations and submit the rest

---

## Validation and Error Handling

### Validation Levels

Validation proceeds through 4 hierarchical levels:

| Level | Name | Scope | Example |
|-------|------|-------|---------|
| **1** | Security | User authorization | User doesn't have permission to nominate |
| **2** | Foreign Key | Reference data integrity | Contract doesn't exist, location invalid |
| **3** | Line | Individual record rules | Quantity exceeds limit, date out of range |
| **5** | Business | Cross-record rules | Total nominations exceed MDQ |

### Error Override Mechanism

Authorized users can **override** validation errors:
- Overrides are effective through a specified end date
- If the override end date is before the nomination end date, the system **splits** the nomination:
  - Part 1: Overridden (from start to override end date)
  - Part 2: Not overridden (from override end date to nomination end)
- Override records are tracked in NNTRAN_ERROR_OVERRIDES

### Validation Rule Categories

- **167 total validation rules** organized by level
- **Business Rules (61)** - MDQ limits, imbalance checks, path validation
- **Line Rules (80)** - Contract validity, location dates, transaction types
- **Foreign Key Rules (25)** - Reference data existence checks
- **Security Rules (1)** - User authorization

### Common Validation Errors

| Area | Error | Description |
|------|-------|-------------|
| Contract | FK Contract Invalid | Contract doesn't exist or is expired for gas day |
| MDQ | MDQ Exceeded | Total delivery nominations exceed contract MDQ |
| Location | Location Invalid | Receipt or delivery location not valid for date |
| Cycle | Cycle Closed | Nomination submitted after cycle deadline |
| Quantity | Zero Quantity | Nomination has zero receipt and delivery quantities |
| Path | Path Mismatch | Nomination path doesn't match contract path |
| Fuel | Fuel Calculation Error | Fuel percentage or quantity calculation failed |

---

## Quantities and Calculations

### Key Quantity Fields

| Field | Description |
|-------|-------------|
| **RecQty** | Receipt (upstream) quantity |
| **DelQty** | Delivery (downstream) quantity |
| **FuelQty** | Fuel retention quantity |
| **FuelPct** | Fuel retention percentage |
| **MinRecQty** | Minimum receipt quantity |
| **MinDelQty** | Minimum delivery quantity |

### Calculated Quantities

| Calculation | Method | Description |
|-------------|--------|-------------|
| **KMDQ** | CalculateKMDQ() | Contract daily max for K (energy) contracts |
| **EPSQ** | CalculateEPSQ() | Evening Peak Scheduled Quantity (receipt and delivery) |
| **Location MDQ** | CalculateLocationMDQ() | Point-to-point (PPP) MDQ at location level |
| **Heating Factors** | CalculateRecHeatingFactors() | BTU heating factors for energy conversion |

### Fuel Handling

- **Fuel Percentage** - Configured per contract/location; applied to receipt quantity
- **Fuel Override** - Users can override calculated fuel (IsFuelOvrd flag)
- **Fuel Preference Code** - Determines fuel calculation method
- **Fuel TOC Code** - Type of Charge for fuel assessment

### Balance Rule

For PNT model: **Receipt Total = Delivery Total + Fuel**

---

## Autogeneration

### What is Nomination Autogeneration?

Autogeneration (Autogen) automatically creates nominations based on predefined rules. Used for:
- Load-following nominations (match upstream changes downstream)
- Balancing nominations (reduce imbalances)
- Template-based recurring nominations

### Autogen Configuration

| Setting | Description |
|---------|-------------|
| **Target TSP** | TSP to create nominations for |
| **Target Cycle** | Which cycle to generate for |
| **Receipt/Delivery Location Mapping** | Map source locations to target |
| **Transaction Type** | Type of nomination to create |
| **Imbalance Threshold** | Minimum imbalance to trigger autogen |
| **Contract Filters** | Filter which contracts to include |
| **Execution Sequence** | Order of autogen rule execution |

### Autogen Validation

Autogen nominations go through a subset of validation rules (ValidationNominationSubsetAGN) that filter to only AGN system source nominations.

---

## Title Transfers

### Pending Title Transfers

Title transfers occur when gas ownership changes at an interconnect location:
- **Upstream (Receipt)** - Gas being received by the pipeline
- **Downstream (Delivery)** - Gas being delivered from the pipeline
- The system matches upstream and downstream nominations at transfer points
- Unmatched nominations create **pending title transfers** (imbalances)

### Title Transfer Attributes

- **ATT (Automated Title Transfer)** - Location attribute enabling automatic matching
- **Interconnect Associations** - Links between physical interconnect locations
- Matching logic groups nominations by location and calculates net imbalance

---

## Business Workflows

### Nomination Maintenance Workflow

```
1. Select Parameters (TSP, Gas Day, Service Requester, Location)
2. Query/Retrieve nominations
3. View grid with contract-based nominations and totals
4. Filter by receipt/delivery location, business partner, contract
5. Toggle ENS Cycle visibility (if applicable)
6. View Classification (internal users)
7. Push for Up/Down detail
8. Submit changes
```

### Nomination Submission (NAESB) Workflow

```
1. Enter screen with parameters (TSP, Gas Day Range, SR, Cycle)
2. Retrieve existing nominations
3. Work in multi-tab interface:
   - PATH tab: Add/Edit/Delete PNT path records
   - RECEIPT (UP) tab: Manage upstream nominations
   - DELIVERY (DOWN) tab: Manage downstream nominations
   - LOCATION SUMMARY tab: View aggregated location totals
   - ERRORS tab: Review validation errors
4. Edit operations: inline edit, bulk copy, fuel recalc, import
5. Validate nominations
6. Review/override errors
7. Submit nominations
```

### Location Centric Nomination Workflow

Similar to Nomination Submission but centered on a specific location:
- Location selector drives all data filtering
- All nominations filtered to the selected location
- Uses location-specific picklists for business partners

### Error Override Workflow

```
1. Query nominations with errors
2. Display error grid (one row per error)
3. Select errors to override
4. Set override through-date
5. System splits nominations at override boundary
6. Save overrides
```

---

## Glossary

| Term | Definition |
|------|------------|
| **Activity** | A working set (draft) of nomination changes before submission |
| **AGN** | Autogeneration - automatic creation of nominations |
| **BegGasDay** | First gas day of a nomination's validity |
| **Cycle** | Time window for nomination submission (Timely, Evening, Intraday) |
| **DUNS** | Data Universal Numbering System - unique business identifier |
| **EndGasDay** | Last gas day of a nomination's validity |
| **ENS** | Electronic Nomination System - TSP-specific cycle designation |
| **EPSQ** | Evening Peak Scheduled Quantity |
| **Gas Day** | 24-hour period defined by TSP (typically 9 AM CT to 9 AM CT) |
| **IdNomHash** | Internal hash identifier for nomination uniqueness |
| **Intraday** | Nomination cycle occurring during the gas flow day |
| **KMDQ** | K-contract Maximum Daily Quantity (energy-based) |
| **Lease** | Production lease nomination type |
| **MDIQ** | Maximum Daily Injection Quantity (storage) |
| **MDQ** | Maximum Daily Quantity - contract limit per day |
| **MDWQ** | Maximum Daily Withdrawal Quantity (storage) |
| **MinMSQ** | Minimum Maximum Storage Quantity |
| **MSQ** | Maximum Storage Quantity |
| **NAESB** | North American Energy Standards Board |
| **NPPool** | National Pricing Pool - virtual aggregation location |
| **PNT** | Path-Node-Transposition - NAESB 3.0 nomination model |
| **PT** | Path-Transposition - legacy nomination model |
| **RecQty / DelQty** | Receipt / Delivery quantity |
| **SrBpNo** | Service Requester Business Partner Number |
| **SrCtrNo** | Service Requester Contract Number |
| **Title Transfer** | Change of gas ownership at an interconnect |
| **TOS** | Type of Service (Firm, Interruptible, etc.) |
| **TSP** | Transportation Service Provider (pipeline operator) |

---

## Related Documentation

- [Architecture Documentation](./architecture.md) - Technical implementation details
- [Troubleshooting Guide](./troubleshooting.md) - Known issues and solutions
- [CAS Domain](../capacity-scheduling-allocations/domain.md) - Scheduling that processes nominations
- [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) - Feature/keyword mapping

---

*Last updated: 2026-03-03*
*Document version: 1.0*
