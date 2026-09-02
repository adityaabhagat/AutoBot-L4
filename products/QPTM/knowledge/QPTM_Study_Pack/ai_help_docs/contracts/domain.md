---
title: Contracts (CTR) - Domain Concepts
category: domain
feature: Contracts (CTR)
related_repos: Web, Batch
keywords: contract, amendment, TOS, type of service, MDQ, MDIQ, MDWQ, MSQ, service requester, agent, contact, location, effective date, attribute flat table, imbalance, PAL/ISS, capacity release, firm, interruptible, evergreen, seasonal profile, ratchet, nomination, billing, status, executed, pending, active, EPSQ, NAESB, OFO, FTS, ITS, UAF, under award, GOV, greater of overrun
last_updated: 2026-03-05
---

# Contracts (CTR) - Domain Concepts

## Overview

This document explains the **business concepts** behind Contract Maintenance in the QPTM system. It focuses on WHAT the system does from a business perspective, explaining domain terminology, business rules, and workflows.

For technical implementation details, see [Architecture Documentation](./architecture.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Business Concepts](#core-business-concepts)
3. [Contract Types and Classification](#contract-types-and-classification)
4. [Type of Service (TOS)](#type-of-service-tos)
5. [Contract Quantities](#contract-quantities)
6. [Contract Lifecycle](#contract-lifecycle)
7. [Amendments](#amendments)
8. [Effective Dates and Time Slices](#effective-dates-and-time-slices)
9. [Contract Locations](#contract-locations)
10. [Contract Agents](#contract-agents)
11. [Contact Overrides (Notice Parties)](#contact-overrides-notice-parties)
12. [Contract Attributes and Flat Table](#contract-attributes-and-flat-table)
13. [Imbalance Configuration](#imbalance-configuration)
14. [PAL/ISS Trade (Park and Loan)](#paliss-trade-park-and-loan)
15. [Related Contracts](#related-contracts)
16. [Key Business Rules and Workflows](#key-business-rules-and-workflows)
17. [Integration Points](#integration-points)
18. [Glossary](#glossary)

---

## System Overview

### What is Contract Maintenance?

**Contract Maintenance** is the central screen in QPTM for managing transportation contracts between shippers (service requesters) and the pipeline (Transportation Service Provider, or TSP). Contracts define the terms under which a shipper can transport, store, park, or loan natural gas on the pipeline.

**Business Purpose:**
- Define shipper rights and obligations for pipeline capacity
- Manage contract lifecycle from draft through execution, activation, and termination
- Track amendments and effective date ranges for contract changes
- Configure contract locations (receipt and delivery points)
- Set up billing, rate, and imbalance parameters
- Support capacity release and nomination readiness
- Manage contract agents and contact information
- Record TOS (Type of Service) attributes that drive downstream behavior

### Key Business Value

- **Capacity Management**: Contracts are the basis for pipeline capacity allocation and nomination validation
- **Revenue Tracking**: Contract MDQ and rate assignments drive billing calculations
- **Regulatory Compliance**: Supports FERC-regulated firm and interruptible service agreements
- **Operational Control**: TOS attributes control nomination, scheduling, and balancing behavior
- **Audit Trail**: Full amendment history with effective date tracking
- **Integration Hub**: Contracts feed nominations, allocations, confirmations, scheduling, billing, and capacity release

---

## Core Business Concepts

### Transportation Service Provider (TSP)

The **TSP** is the pipeline company that provides natural gas transportation. Each contract is associated with a single TSP identified by **TspNo** (a numeric identifier, typically a short integer). All contract operations are scoped by TSP.

### Business Associate (BA / Business Party)

The **Business Associate** (also called Business Party or BP) is the shipper entity entering into a contract. Identified by:
- **BaNo** (Business Associate Number) - Unique identifier for the entity
- **BpNm** (Business Party Name) - Display name
- **BaSuf** (Business Associate Suffix) - Optional suffix to differentiate subdivisions

A business associate must be active to be associated with new contracts. Inactive business associates trigger validation warnings.

### Contract Number (CtrNo)

The **CtrNo** is the unique identifier for a contract within a TSP. It can be:
- **Auto-generated** using a global sequence number
- **Prefixed** with TSP and TOS codes if the `UseTSPTOSContractPrefix` global config is enabled (format: `{TspNo}{TosCode}-{SeqNo}`)
- Maximum length of 12 characters when using TSP/TOS prefix

### Amendment Number (AssignNo / AmendNo)

Each contract can have multiple **amendments** (also referred to as AssignNo). Amendment 0 is the original contract. Each subsequent amendment increments the number. The amendment number, combined with CtrNo and TspNo, uniquely identifies a specific contract version.

---

## Contract Types and Classification

### Type Code (TypeCode)

The high-level contract classification. Typical values include:
- Transportation agreements
- Storage agreements
- Park and Loan agreements

### Sub Type Code (SubTypeCode / TOS Code)

The specific **Type of Service** under which the contract operates. This is one of the most important fields as it drives:
- Attribute defaults
- Rate schedule resolution
- Nomination validation rules
- Amendment handling behavior (Additive vs. Replacement)

### Service Class

Contracts are classified by service class:
- **Firm (FRM)** - Guaranteed capacity; shipper has priority
- **Interruptible (INT)** - Capacity available on a best-effort basis; can be curtailed

### Amendment Handling Codes

Each TOS defines how amendments are processed:
- **Additive** - New amendments add time slices alongside existing ones; effective dates do not overlap
- **Replacement** - New amendments replace the previous version entirely

---

## Type of Service (TOS)

The **Type of Service** defines the nature of the pipeline service and drives attribute defaults. Key TOS-related concepts:

### TOS Attributes

Each TOS has a set of boolean attributes that control contract behavior. These are stored per-contract as `CtrAttributeDO` records and summarized in the **Attribute Flat Table** for performance. Key attributes include:

| Attribute Code | Name | Purpose |
|---|---|---|
| NOM | Nominatable | Whether the contract can be used for nominations |
| BIL | Billable | Whether the contract generates invoices |
| CAP | Capacity Release Allowed | Whether capacity can be released to other shippers |
| CIO | Cash In Cash Out | Whether CICO imbalance settlement is enabled |
| IMB | Imbalance | Whether imbalance tracking is enabled |
| PPP | Primary Point Pairs | Whether point-pair routing is enforced |
| ADO | Allow Discount Offers | Whether discounted rate offers are permitted |
| AST | Allow Storage Transfers | Whether storage transfers between contracts are permitted |
| HNA | Hourly Nominations Allowed | Whether hourly nomination granularity is supported |
| EVG | Evergreen | Whether the contract auto-renews |
| NSD | Noms on Supplemental Delivery Locations | Whether supplemental delivery locations are permitted |
| NSR | Noms on Supplemental Receipt Locations | Whether supplemental receipt locations are permitted |
| BKL | Bill MDQ on Contract Level | Whether MDQ billing is at contract level vs. location level |
| IOC | Index of Customers | Whether the contract participates in the customer index |
| OPR | Operational Balance | Whether operational balancing is enabled |
| EXN | Exclude Nominations | Whether nominations are excluded from processing |
| LDN | Lease Displacement Noms | Whether lease displacement nominations are allowed |
| LOC | Life of Contract | Whether the contract is life-of-contract |
| ENS | Enhanced Nomination Service | Whether enhanced nomination service is enabled |
| NCA | Non-Confirming Agreement | Whether this is a non-confirming agreement |
| NGT | Negotiated Rates | Whether negotiated (non-tariff) rates apply |
| PMF | Prorate Meter Fees | Whether meter fees are prorated |
| PIT | PITS Percentage | Whether percentage-in-transportation-service applies |
| BHA | Bill Higher of SRC | Whether billing uses the higher of SRC or actual |
| BSC | Bill SRC | Whether billing uses SRC quantity |
| SEM | SE Market Expansion Legacy | Legacy SE market expansion attribute |
| RCR | Rate Case Error Report | Whether rate case error reporting is enabled |
| LLF | Block Manual LF Locations | Whether manual lateral facility locations are blocked |
| ESL | Exclude Sec Loc from IOC | Whether secondary locations are excluded from the index |
| GOV | Greater Of Overrun | Whether greater-of-overrun billing logic applies |
| BMA | Bill Maximum Attribute | Legacy/TSP-specific attribute (usage varies by TSP) |
| LFK | Lateral Facility Key | Legacy/TSP-specific attribute (usage varies by TSP) |

### TOS Contract Tab

The `TypeOfServiceContractTabDO` defines which UI tabs are visible for a given TOS, controlling the contract maintenance screen layout.

---

## Contract Quantities

### MDQ (Maximum Daily Quantity)

The **MDQ** is the maximum daily quantity a shipper is entitled to transport. It is the primary capacity metric for a contract. MDQ can be defined at:
- **Contract level** - Overall maximum for the contract (`CtrMdqDisplayOnly`)
- **Location level** - Per-location MDQ on each receipt/delivery point (`FixedMDQQty`)

MDQ can also have seasonal variations via seasonal profiles:
- **Summer MDQ** (`SummerMDQQty`)
- **Winter MDQ** (`WinterMDQQty`)
- **Shoulder MDQ** (`ShoulderMDQQty`)
- **Fixed MDQ** (`FixedMDQQty`)

### MDIQ (Maximum Daily Injection Quantity)

For storage contracts, the **MDIQ** defines the maximum daily quantity that can be injected into storage. Controlled by:
- `FixedMdiqQty` - Fixed injection quantity
- `IdMdiqRatchet` - Ratchet schedule for dynamic MDIQ

### MDWQ (Maximum Daily Withdrawal Quantity)

For storage contracts, the **MDWQ** defines the maximum daily quantity that can be withdrawn from storage. Controlled by:
- `FixedMdwqQty` - Fixed withdrawal quantity
- `IdMdwqRatchet` - Ratchet schedule for dynamic MDWQ

### MSQ (Maximum Storage Quantity)

The **MSQ** defines the maximum total quantity that can be stored under a storage contract:
- `CtrMsq` - Maximum storage quantity
- `CtrMsqMin` - Minimum storage quantity (floor)
- `MsqMinSeasonalProfId` - Seasonal profile for minimum MSQ

### Override MDQ

The **Override MDQ** (`OvrdCtrMdq`) allows pipeline operators to temporarily override the contract MDQ for operational purposes.

### SRC Quantity

The **SRC (Supplemental Receipt Capacity)** quantity represents additional capacity beyond the base MDQ:
- `SrcSeasonalProfId` - Seasonal profile for SRC
- `SrcQty` - SRC quantity

---

## Contract Lifecycle

### Status Codes

Contracts progress through a lifecycle defined by status codes (stored in `QCODE_CTR_STATUS`):

| Code | Status | Description |
|---|---|---|
| DFT | Draft | Contract is being prepared, not yet finalized |
| PEN | Pending | Contract is submitted but not yet executed |
| PRO | Proposed | Contract has been proposed to the shipper |
| EXE | Executed | Contract has been signed/executed by all parties |
| UAF | Under Award | Contract is under capacity release award processing |
| ACT | Active | Contract is currently in effect for nominations and billing |
| EXP | Expired | Contract has passed its expiration date |
| TRM | Terminated | Contract has been terminated before natural expiration |
| INA | Inactive | Contract has been deactivated |

### Status Transitions

Key status transition rules:
1. **Executed** requires an `ExecutedDate` to be set (auto-set to current date on status change)
2. Amendments cannot be set to **Executed** or **Active** unless previous amendments (amendment 0) are also Executed or Active (for Additive TOS)
3. For **Replacement** amendment handling, amendment 0 must be Executed or Active before subsequent amendments can be Executed
4. Status changes trigger **event notifications** via the `QPTMContractMaintenanceStatusCdChangeEventDetector`

### Key Dates

| Date Field | Purpose |
|---|---|
| EffDateFrom | Contract effective start date |
| EffDateTo | Contract effective end date |
| ExecutedDate | Date the contract was executed |
| PrimaryTermExpDate | Primary term expiration date |
| ExpireDate | Contract expiration date |
| EvergreenNoticeDate | Notice date for evergreen renewal |
| EvergreenTerminationDate | Termination date if evergreen not renewed |

---

## Amendments

### What are Amendments?

An **amendment** represents a modification to an existing contract. Rather than editing the original contract, QPTM creates a new amendment (time slice) that captures the changes. This preserves the full audit history of all contract modifications.

### Amendment Workflow

1. User selects an existing contract
2. User clicks "New Amendment" (Ctrl+Alt+N shortcut)
3. System calculates the next amendment number (`GetNextAmendNo` = max existing AmendNo + 1)
4. A new amendment record is created with the original contract's TOS and effective dates as defaults
5. User modifies the amendment fields (dates, quantities, locations, etc.)
6. On save, the system validates the amendment against business rules
7. The amendment description defaults to "Original Contract" for amendment 0

### Amendment Handling Modes

- **Additive**: Each amendment creates a new effective date range. Multiple amendments can coexist with non-overlapping date ranges. The system enforces that all previous amendments must be Executed or Active before a new one can be Executed.
- **Replacement**: Each amendment replaces the previous one. Only amendment 0 needs to be in Executed/Active status.

---

## Effective Dates and Time Slices

### Time Slice Concept

Contracts use **effective dating** (also called "time slicing") to track changes over time. Each time slice represents the contract values for a specific date range:
- `EffDateFrom` - Start of the time slice (inclusive)
- `EffDateTo` - End of the time slice (inclusive)

### Effective Date Views

The system provides two views for querying contract effective date ranges:
- `KCTRL_CTR_EFF_DATE_RANGE_VW` - Standard effective date ranges
- `KCTRL_CTR_EFF_DATE_RANGE_GS_VW` - Gas storage effective date ranges

### As-Of-Date Queries

When querying contracts, an **as-of date** determines which time slice is returned. The special value `9000-12-31` returns all effective dates (all time slices).

---

## Contract Locations

### Location Structure

Each contract amendment defines **receipt** and **delivery** locations that specify where gas enters and exits the pipeline:

- **IdLoc1** - Receipt (upstream) location identifier
- **IdLoc2** - Delivery (downstream) location identifier
- **IdLocGrp1** - Receipt location group
- **IdLocGrp2** - Delivery location group
- **IdParentLoc1** - Parent receipt location
- **IdParentLoc2** - Parent delivery location

### Location MDQ

Each location can have its own MDQ quantities:
- `FixedMDQQty` - Fixed daily quantity
- `SummerMDQQty` - Summer quantity
- `WinterMDQQty` - Winter quantity
- `ShoulderMDQQty` - Shoulder season quantity
- `IdSeasonalProf` - Seasonal profile for MDQ variation

Total contract MDQ is summarized as:
- `TotalContractReceiptMDQ` - Sum of all receipt location MDQs
- `TotalContractDeliveryMDQ` - Sum of all delivery location MDQs

### Location Validation

Location validations include:
- Required TOS/location attribute cross-reference validation
- Threshold quantity validation
- Hourly measurement penalty checks
- Segment validation
- Facility validation
- Duplicate location detection
- Ineffective date validation
- Primary point pair validation

---

## Contract Agents

### Agent Structure

**Contract agents** represent entities authorized to act on behalf of the shipper. Agents are stored separately from the contract header and are tied only by CtrNo (not by AmendNo -- agents apply across all amendments).

Key agent fields:
- **AgentBaNo** - Agent business associate number
- **ConsentingBpNo** - Consenting business party number
- **Effective dates** - When the agent authority is valid

### Agent Save Behavior

Due to foreign key constraints, the system saves contract agents in a special order:
1. Clear contract agents from the main save
2. Save the contract header first
3. Save agents separately via `UpdateAgent()`

This two-phase approach prevents FK errors (referenced in WI #206053).

---

## Contact Overrides (Notice Parties)

**Contract Notice Parties** are contact overrides that specify who should receive notifications for a given contract. Each notice party links to a contact record (`ContactSeqNo`) and includes:
- First name, Last name, Title
- Department source code
- Override indicators for various notification types

Contact overrides allow contracts to use different contacts than the default business associate contacts.

---

## Contract Attributes and Flat Table

### Attribute Storage

Contract attributes are stored in two forms:

1. **Normalized attributes** (`KCTRL_CTR_ATTR` table / `CtrAttributeDO`): Each TOS attribute is a separate row with:
   - `TosAttrCode` - The attribute code (e.g., "NOM", "BIL", "CAP")
   - `IsAttrTrue` - Boolean indicating if the attribute is enabled

2. **Flat table** (`KCTRL_CTR_ATTR_FLAT` table / `ContractAttributeFlatDO`): A single row per contract time slice with a column for each attribute as a boolean flag (e.g., `AttrIndNom`, `AttrIndBil`, `AttrIndCap`).

### Flat Table Purpose

The flat table is a **performance optimization**. Downstream processes (nominations, scheduling, billing) can query a single row to check multiple attributes rather than joining against the normalized attribute table. The flat table is regenerated from the normalized attributes on every contract save.

### Flat Table Update Algorithm

On each contract save (`UpdateSingleContractMaintenanceComplete`):

1. The `ContractMaintenance_UpdateAttributeFlatTable` class is invoked
2. For each contract header time slice:
   a. Look up or create the `ContractAttributeFlatDO` record
   b. Iterate through all `CtrAttributeDO` records
   c. Map each `TosAttrCode` to its corresponding flat table column via a switch statement
   d. Set the column value to the attribute's `IsAttrTrue` value
3. The flat table record is saved as part of the complete object save

### Key Flat Table Columns

| Column | Attribute | Meaning |
|---|---|---|
| AttrIndNom | Nominatable | Contract can be nominated |
| AttrIndBil | Billable | Contract is billable |
| AttrIndCap | Capacity Release Allowed | CR is allowed |
| AttrIndCio | Cash In Cash Out | CICO is enabled |
| AttrIndImb | Imbalance | Imbalance tracking enabled |
| AttrIndPpp | Primary Point Pairs | PPP routing enforced |
| AttrIndHna | Hourly Nominations Allowed | Hourly noms allowed |
| AttrIndEvg | Evergreen | Contract auto-renews |
| AttrIndAdo | Allow Discount Offers | Discount offers permitted |
| AttrIndAst | Allow Storage Transfers | Storage transfers permitted |

---

## Imbalance Configuration

Contracts can be configured for imbalance tracking and settlement. Key fields include:

- **Imbalance attribute** (IMB) - Must be enabled for imbalance tracking
- **Settlement method** - How imbalances are settled
- **CICO (Cash In Cash Out)** - Whether cash settlement is used
- **Trade lag time** - Time allowed for imbalance trading
- **CICO PPA lag time** - Lag time for PPA prior period adjustments
- **Tied contracts** - Contracts that share imbalance settlement
- **Seasonal profile** - For seasonal imbalance settlement variations
- **Imbalance settle portion code** - Controls settlement portion calculation

---

## PAL/ISS Trade (Park and Loan)

For **Park and Loan / Interruptible Storage Service** contracts, a dedicated trade tab captures deal-specific information:

- **Deal Type Code** - Buy/Sell/Transfer
- **Trade Timestamp** - When the trade was executed
- **Total Volume** - Total contract volume
- **Flow dates and volumes** - First and second activity period dates and daily volumes
- **Daily Rate** - Contract daily rate (validated against rate resolution)
- **Market spreads** - Gross and net market spread
- **Futures pricing** - Futures 1 and Futures 2 prices
- **TVM** - Time Value of Money
- **Revenue calculations** - Total revenue, PalIss fee, third party fee
- **Amendment type** - How the PAL/ISS deal was amended
- **Injection/Withdrawal method** - How injection and withdrawal are handled
- **Aggregated quantities** - Min and max aggregated quantities for master contracts

---

## Related Contracts

Contracts can be linked to other contracts through the **Related Contracts** tab. Relationship types include:

- **Overrun relationships** - Link an overrun contract to its base contract
- **Imbalance relationships** - Link contracts that share imbalance settlement
- **General relationships** - Other contract-to-contract associations

Related contract validation ensures:
- Valid contract numbers or external contract numbers
- Valid overrun/related relationship reasons
- Valid imbalance-related contract linkages
- Effective date consistency between related contracts

---

## Key Business Rules and Workflows

### Contract Save Workflow

1. **Validate before save**: All validation rules execute across all tabs
2. **Generate CtrNo**: For new contracts, auto-generate the contract number
3. **Update attribute flat table**: Synchronize normalized attributes to flat table
4. **Save header**: Save the contract header (clearing agents first to avoid FK errors)
5. **Save agents**: Save contract agents separately
6. **Save auth overrun and FSS**: Save authorized overrun and FSS schedule records
7. **Event detection**: Check for MDQ changes and status code changes
8. **Notification**: Send email notifications for detected events

### Validation Categories

Contract validation is organized by tab/area:

| Category | Rule Count | Key Validations |
|---|---|---|
| Header | 12 | Company validation, back-dating, integrated mode, BA suffix, business party, inactive BA, inactive TOS, TOS code/amendment handling, nomination readiness, pre-delete, date gap |
| General | 16 | Ratchet, primary point pairs, NNS contract, override MDQ, prepaid offset, MDIQ/MDWQ mode, SRC, seasonal profile type, TOS, facility, MSQ |
| Dates | 6 | Status code, evergreen terms, primary term expire date, evergreen dates, date code, internal user |
| Locations | 12 | Required attributes, threshold quantity, hourly measurement, segments, facility, delivery location multi-contract, ineffective date, primary point pairs, location row, duplicate attributes |
| Agents | 5 | Historical viewing date, update rights, primary agent, effective date, effective date overlap |
| Contacts | 8 | Contact update, invalid contact, valid contact, multiple contacts, inactive contact, nomination validation, customer account, billing invoice |
| Imbalance | 10 | Trade lag time, CICO PPA lag time, contract imbalance, tied contract, CICO, settlement method, imbalance info, settle portion code, seasonal profile ID |
| PAL/ISS Trade | 15 | Flow dates, date quantities, amendment type action, action type, deal qty vs total qty, action date, billing month, total vol change, journal entry, amend deal type, amend no and type, MSQ, master contract aggregated qty |
| Auth Overrun | 5 | Daily overrun quantity, effective date, required fields, effective date overlap, duplicate record |
| FSS Schedule | 1 | Required fields |
| Contract Quantity | 4 | Fill quantity or seasonal profile, PITS contract quantity, PITS percentage, PITS attribute |
| Related Contracts | 5 | Related contract number, overrun reason, imbalance, related contract validation, relationship effective dates |
| Text | 2 | TSP, tied BP on contract |

### MDQ Change Event

When the contract MDQ changes, the system:
1. Detects the change by comparing `CtrMdqDisplayOnlyOriginal` with `CtrMdqDisplayOnly`
2. Identifies affected delivery locations
3. Fires a `ContractLocationMDQChange` event
4. Sends email notification with details of the change

### Status Change Event

When the contract status changes, the system:
1. Detects the change by comparing `StatusCodeOriginal` with the current `StatusCode`
2. Fires a `ContractStatusChange` event
3. Sends notification with contract number, business party, status, and effective dates

---

## Integration Points

Contracts integrate with nearly every other QPTM module:

| Module | Integration |
|---|---|
| Nominations | Contract MDQ limits nomination quantities; TOS attributes control nomination behavior |
| Allocations | Contract locations define allocation points |
| Confirmations | Contract data feeds confirmation processing |
| Scheduling | Contract capacity feeds scheduling algorithms |
| Capacity Release | CAP attribute enables capacity release; contracts define releasable capacity |
| Billing/Invoicing | Contract rates and quantities drive invoice generation |
| Inventory | Storage contracts link to inventory account headers |
| Rates | Contracts reference rate schedules and rate resolution |
| EDI | Contract data is transmitted via electronic data interchange |
| RFS (Request for Service) | RFS can create new contracts through the approval workflow |
| Locations | Contracts reference pipeline locations and location groups |
| Business Associates | Contracts are tied to shipper business associates |

---

## Glossary

| Term | Definition |
|---|---|
| **Amendment** | A version of a contract representing a modification; identified by AssignNo/AmendNo |
| **BA / Business Associate** | The shipper entity on a contract; identified by BaNo |
| **Capacity Release** | The process of releasing unused firm contract capacity to other shippers |
| **CICO** | Cash In Cash Out - imbalance settlement method using cash |
| **CtrNo** | Contract Number - unique identifier for a contract within a TSP |
| **Effective Dating** | The use of date ranges (EffDateFrom/EffDateTo) to version contract data |
| **EFO** | Emergency Flow Order - pipeline directive for emergency balancing situations |
| **EPSQ** | Elapsed Pro-rata Scheduled Quantity - the quantity of gas that has already flowed during a gas day; cannot cut below EPSQ since that gas has already been transported |
| **Evergreen** | A contract that automatically renews unless terminated |
| **Firm Service** | Guaranteed pipeline capacity that cannot be curtailed |
| **FSS** | Firm Storage Service - a type of storage contract |
| **FTS** | Firm Transportation Service - a type of firm service contract |
| **Imbalance** | The difference between gas receipts and deliveries on a contract |
| **Interruptible Service** | Pipeline capacity available on best-effort basis; can be curtailed |
| **ITS** | Interruptible Transportation Service - a type of interruptible service contract |
| **K** | Short code prefix for Contract-related database tables and codes (e.g., KCTRL_CTR_HDR) |
| **MDQ** | Maximum Daily Quantity - the maximum gas volume per day under a contract |
| **MDIQ** | Maximum Daily Injection Quantity - max daily injection for storage contracts |
| **MDWQ** | Maximum Daily Withdrawal Quantity - max daily withdrawal for storage contracts |
| **MSQ** | Maximum Storage Quantity - max total gas in storage under a contract |
| **NAESB** | North American Energy Standards Board - regulatory body that defines gas industry standards for nominations, scheduling, and electronic transactions |
| **Notice Party** | A contact override for contract notifications |
| **OFO** | Operational Flow Order - pipeline directive for operational balancing to maintain system integrity |
| **PAL/ISS** | Park and Loan / Interruptible Storage Service |
| **PNT** | Path Non-Threaded - nomination type without specified routing path |
| **PPP** | Primary Point Pairs - routing enforcement between receipt and delivery points |
| **PT** | Path Threaded - nomination type with specified routing path |
| **Ratchet** | A schedule that adjusts MDIQ/MDWQ based on storage balance or other factors |
| **Seasonal Profile** | A schedule defining how quantities vary by season (summer/winter/shoulder) |
| **Service Class** | Classification as Firm or Interruptible |
| **SRC** | Supplemental Receipt Capacity - additional capacity beyond base MDQ |
| **Time Slice** | A single effective-dated record representing contract values for a date range |
| **TOS** | Type of Service - the service classification (e.g., firm transport, storage, PAL) |
| **TSP** | Transportation Service Provider - the pipeline company |
| **TOS Attribute** | A boolean flag on a TOS that controls contract behavior (e.g., Nominatable, Billable) |

---

*Last updated: 2026-03-05*

*Document version: 1.2*
