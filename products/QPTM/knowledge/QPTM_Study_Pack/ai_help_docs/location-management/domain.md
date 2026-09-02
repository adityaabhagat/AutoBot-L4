---
title: Location Management (LOC) - Domain Concepts
category: domain
feature: Location Management (LOC)
related_repos: Web, Batch
keywords: LOC, location, meter, MeterHeader, PACTRL_LOC, receipt, delivery, interconnect, pool, aggregate, operator, confirm party, contact, location group, location path, mass change, POV, PovCode, LocTypeCode, LocPurpCode, location attribute, capacity, ownership, producer, broker, affidavit, supplier pins, bidirectional, shadow location, transfer location, LDC, geographic, SEXTN_MTR_HEADER_QPTM, PACTRL_LOC_AGGREGATE
last_updated: 2026-03-03
---

# Location Management (LOC) - Domain Concepts

## Overview

This document explains the **business concepts** behind Location Management in the QPTM system. It focuses on WHAT the system does from a business perspective, explaining domain terminology, business rules, and workflows.

For technical implementation details, see [Architecture Documentation](./architecture.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Business Concepts](#core-business-concepts)
3. [Location Types and Classifications](#location-types-and-classifications)
4. [Point of View (POV)](#point-of-view-pov)
5. [Location Attributes](#location-attributes)
6. [Operator IDs, Confirm Parties, and Contacts](#operator-ids-confirm-parties-and-contacts)
7. [Location Groups and Capacity/Rate Areas](#location-groups-and-capacityrate-areas)
8. [Location Paths](#location-paths)
9. [Child Locations and Aggregates](#child-locations-and-aggregates)
10. [Interconnects](#interconnects)
11. [Ownership and Producers](#ownership-and-producers)
12. [Brokers and End-User Transportation](#brokers-and-end-user-transportation)
13. [Affidavits](#affidavits)
14. [Supplier Pins](#supplier-pins)
15. [Bidirectional Locations](#bidirectional-locations)
16. [Mass Change Operations](#mass-change-operations)
17. [Effective Dating](#effective-dating)
18. [Key Business Rules](#key-business-rules)
19. [Glossary](#glossary)

---

## System Overview

### What is Location Management?

**Location Management** (feature code: LOC) is the master data maintenance system for pipeline locations (also known as meters or meter points) within the QPTM natural gas pipeline transportation management application. Every physical or logical point where gas enters, exits, or is measured on the pipeline system is represented as a location record.

**Business Purpose:**
- Define and maintain all receipt and delivery points on the pipeline
- Associate operator IDs, confirming parties, and contact information with each location
- Configure location attributes that control how the location participates in nominations, allocations, scheduling, and billing
- Manage parent-child aggregate location hierarchies
- Track interconnect relationships between pipeline systems
- Define capacity, ownership, and rate area assignments
- Support effective-dated location records for historical tracking

### Key Business Value

- **Pipeline Operations**: Locations are the fundamental building blocks of all pipeline operations -- nominations, confirmations, allocations, scheduling, and invoicing all reference location records
- **Regulatory Compliance**: FERC and NAESB requirements mandate accurate location data including operator identification, capacity information, and interconnect details
- **Master Data Integrity**: Changes to location data cascade across the entire system, affecting nominations, contracts, rate schedules, and billing
- **Operational Flexibility**: Effective dating allows location changes to be scheduled and tracked over time without losing historical data

---

## Core Business Concepts

### Location Identity

Each location is uniquely identified by:
- **Location ID (MeterNo/MtrNo)**: The primary identifier for the meter/location point
- **TSP Number (TspNo)**: The Transporting Service Provider that owns/operates the location
- **Effective Date (EffDateFrom/EffDateTo)**: The period during which this location configuration is active

The combination of Location ID + TSP No + Effective Date From forms the composite key.

### Location Status

Locations have a **StatusCode** that indicates whether they are active or inactive. Changing a location's status triggers events that propagate to other modules (nominations, scheduling, etc.).

### Location Purpose Code (LocPurpCode)

Defines the operational purpose of the location on the pipeline, controlling how the location participates in various business processes.

---

## Location Types and Classifications

### Location Type Code (LocTypeCode)

The location type code classifies the physical or logical nature of the location point. Common location types include:

| Classification | Description |
|---|---|
| Physical Location | A real, physical meter or measurement point on the pipeline |
| Logical Location | A virtual or calculated point that does not correspond to a physical meter (e.g., pool points, aggregate points) |

The `BalanceMeterTypeCode` on the MeterHeader record further refines whether a location is physical or logical (`IsLogicalMtr` flag).

### Location Source (SrcModuleCode)

Indicates which system module or integration source created the location:
- Locations created via the Location Maintenance screen
- Locations created via EDI/external integration (MPS - Measurement Information Process System)
- When a location is sourced from MPS, certain fields become read-only in the UI

---

## Point of View (POV)

The **Point of View (PovCode)** is a critical classification that determines the flow direction at a location:

| POV Code | Name | Description |
|---|---|---|
| `R` | Receipt | Gas is received (enters) the pipeline at this location |
| `D` | Delivery | Gas is delivered (exits) the pipeline at this location |
| `B` | Bidirectional | Gas can flow in either direction at this location |

**Business Rules:**
- POV determines how the location participates in nominations and scheduling
- Bidirectional locations require a paired location (BiDirectLocId) configured in the opposite direction
- The `BidirectionalPOV` global configuration controls whether bidirectional location validation is enforced
- When a bidirectional pair is configured, the system automatically creates/manages `CAScheduleObjectCustom` records

---

## Location Attributes

Location attributes are boolean flags (stored in `PACTRL_LOC_ATTR` table, code table `QCODE_LOC_ATTR`) that control a location's behavior and capabilities. Attributes are maintained on the **Details** tab of the Location Maintenance screen.

### Key Location Attributes

| Code | Name | Description |
|---|---|---|
| `NOM` | Nominatable | Location participates in the nomination process |
| `ALL` | Allocable | Location participates in the allocation process |
| `AGR` | Aggregate | Location is an aggregate parent with child locations |
| `PL` | Pool | Location is a pool point |
| `IC` | Interconnect | Location is an interconnect with another pipeline |
| `STR` | Storage | Location is a storage facility |
| `IN` | Injection | Location supports gas injection (storage) |
| `WD` | Withdrawal | Location supports gas withdrawal (storage) |
| `END` | End User Transportation | Location supports EUT broker tracking (shows Brokers tab) |
| `MP` | Master Pins | Location has supplier pin associations (shows Supplier Location tab) |
| `ACM` | Allocate Using Child Meas | Location allocates using child measurement data (shows Child Location For Allocation tab) |
| `AAF` | Allocate Actual Fuel | Location allocates actual fuel (shows Child Location For Allocation tab) |
| `MST` | Master Meter | Location is a master meter |
| `VTL` | Virtual | Location is virtual/not physically measured |
| `PHY` | Physical | Location is a physical measurement point |
| `OTH` | Other UOM | Location supports an alternate unit of measure (enables OthVolUomCode field) |
| `DPI` | Discount POI | Location is a discount Point of Interconnection |
| `NPI` | Non-Discount POI | Location is a non-discount Point of Interconnection |
| `ATT` | Allow Title Transfer | Location allows title transfer nominations |
| `MTB` | Meter Bounce | Location participates in meter bounce processing |
| `PAY` | Payback | Location participates in payback processing |
| `MAK` | Makeup | Location participates in makeup processing |
| `HOU` | Hourly Measurement | Location has hourly measurement data |
| `PFD` | Prevent Fuel Gross Up On Delivery | Prevents fuel gross-up calculation on delivery side |
| `PFR` | Prevent Fuel Gross Up On Receipt | Prevents fuel gross-up calculation on receipt side |
| `GTH` | Gathering | Location is a gathering system point |
| `WGT` | Wellhead Gathering | Location is a wellhead gathering point |
| `IMB` | Imbalance | Location participates in imbalance processing |
| `OFS` | Off System | Location is off-system |
| `MEP` | Month End Processing | Location participates in month-end processing |

### Attribute-Driven Tab Visibility

Several tabs on the Location Maintenance screen are shown or hidden based on attribute settings:
- **Brokers tab**: Visible when `END` (End User Transportation) attribute is true
- **Child Locations tab**: Visible when `AGR` (Aggregate) attribute is true
- **Supplier Location tab**: Visible when `MP` (Master Pins) attribute is true
- **Child Location For Allocation tab**: Visible when `ACM` or `AAF` attribute is true

### Flat Attribute Table

Location attributes are also stored in a denormalized flat table (`PACTRL_LOC_ATTR_FLAT`) for performance. Columns are named `ATTRIND{CODE}` (e.g., `ATTRINDNOM`, `ATTRINDALL`). The flat table is updated automatically via reflection when attributes are saved.

---

## Operator IDs, Confirm Parties, and Contacts

### Contacts Overview

Locations have multiple associated contacts stored in `PACTRL_LOC_CONTACT`. Each contact has a **Contact Type Code** that defines their role:

| Contact Type | Code | Description | Cardinality |
|---|---|---|---|
| Operator | `OPR` | The operator responsible for the physical location | Single per location |
| Confirming Party | `CNF` | The party that confirms nominations at this location | Single per location |
| Location Analyst | `LOC` | Pipeline analyst assigned to this location | Single per location |
| Account Manager | `ACM` | Account manager for the location | Single per location |
| Operator Agent | `OPA` | Agent representing the operator | Single per location |
| Scheduler | `SCH` | Person responsible for scheduling at this location | Multiple allowed |
| Invoices | `INV` | Contact for invoice-related communications | Multiple allowed |
| Imbalance Trading | `IMB` | Contact for imbalance trading | Multiple allowed |
| Lease Shipper | `LSH` | Lease shipper contact | Multiple allowed |
| Point Analyst | `PAN` | Point analyst for the location | Multiple allowed |
| RFS Approver | `APR` | Approver for Request for Service | Multiple allowed |

### Operator ID and Confirm Party Display

The **Operator ID** and **Confirm Party** are prominently displayed on the main location header and are derived from the contacts grid:
- `OperatorID` = The BpNo|BpNm of the contact with type `OPR`
- `ConfirmParty` = The BpNo|BpNm of the contact with type `CNF`

### Contact Validation Rules

- Only one contact of type `OPR`, `CNF`, `LOC`, `ACM`, or `OPA` is allowed per location per effective date
- Contact type changes are validated (see validation rules 018-024)
- Contacts sourced from MPS (Measurement Information Process System) are read-only
- Deleting a contact that is the sole Operator or Confirm Party triggers validation warnings

---

## Location Groups and Capacity/Rate Areas

### Location Groups

Locations are organized into **Location Groups** (stored in `PACTRL_SYS_LOC_GRP_LOC` and `PACTRL_LOC_GRP`). Each group has:
- **Location Group ID (IdLocGrp)**: The identifier for the group
- **Location Group Type Code (LocGrpTypeCode)**: The type of group (from `QCODE_LOC_GRP_TYPE`)
- **Location Group Name (LocGrpNm)**: Descriptive name

Location groups are used for:
- **Capacity/Rate Areas**: Grouping locations for rate schedule and capacity calculation purposes
- **Scheduling**: Grouping locations for operational scheduling
- **Reporting**: Logical grouping for analysis and reporting

### Capacity/Rate Area Tab

The Capacity/Rate Area tab on the Location Maintenance screen displays the location's group memberships. Changes to capacity/rate area assignments trigger location resolution status updates (`PatranLocResRangeStatus`), which may trigger downstream batch processes.

### Location Group Type Configuration

Location group types can be configured with:
- `IsLocScreen` flag: Whether the group type appears on the Location Maintenance screen
- `IsLocScreenDefault` flag: Whether the group type is shown by default
- `AppLayerCode`: Links to metadata module definitions for profile-based configuration
- `Rank`: Display ordering

---

## Location Paths

**Location Path Maintenance** (managed by `LocationPathMaintenanceController`) defines the transportation paths that connect locations on the pipeline. A path represents a route that gas can take from one point to another.

Key concepts:
- Path Header (`PALocationPathHdr`): The parent record defining the path
- Path Details (`PALocationPath`): Individual segments or legs of the path
- Paths have effective dates and are associated with TSP preferences for energy/volume units of measure
- Paths support Excel import/export and bulk edit operations

---

## Child Locations and Aggregates

### Aggregate Locations

When a location has the `AGR` (Aggregate) attribute set to true, it can have **child locations** associated with it. The parent-child relationship is stored in `PACTRL_LOC_AGGREGATE`.

Key fields:
- **IdLoc**: The parent (aggregate) location ID
- **IdChildLoc**: The child location ID
- **EffDateFrom/EffDateTo**: The effective date range for the relationship
- **EnrollSubmitDate/DeenrollSubmitDate**: LDC enrollment/de-enrollment dates

### Child Locations for Allocation

A separate relationship (`PACTRL_LOC_CTR_CHILD`) tracks child locations specifically for allocation purposes. This is visible when the `ACM` or `AAF` attribute is enabled, and supports allocation processes that use child measurement data.

### Parent Location History

The system tracks the history of parent location assignments. When viewing a location, users can see which aggregate parent the location belongs to, including historical assignments.

---

## Interconnects

The **Interconnect** tab manages relationships between the pipeline's locations and connecting (interconnecting) pipelines. Data is stored in `PALocationInterconnect` records.

Key fields:
- **InterconnectBaNo**: The Business Associate number of the interconnecting pipeline
- **InterconnectBaNm**: The name of the interconnecting pipeline
- **InterconnectID**: The DUNS number of the interconnecting party
- **InterconnectFERCCID**: The FERC Company ID of the interconnecting party (from `BATaxId` with type `CID`)
- **InterconnectLoc**: The associated location from the Associated Names tab (type: Interconnect Location)
- **InterconnectDRN**: The associated DRN from the Associated Names tab (type: Interconnect DRN)

Interconnect information is critical for:
- EDI transactions with connecting pipelines
- FERC reporting requirements
- Nomination/confirmation matching across pipeline boundaries

---

## Ownership and Producers

### Ownership Tab

The Ownership tab tracks which contracts (`CtrNo`) have ownership rights at a location. Each `PALocationOwner` record links a location to a contract, with:
- **CtrNo**: Contract number
- **ActiveBpNo**: The active business party on the contract (derived from `ContractHeaderVald`)
- Ownership percentage and other details

### Producers Tab

The Producers tab (`PALocationProducer`) tracks producers associated with a location:
- **BpNo**: The Business Associate number of the producer
- **BpNm**: The name of the producer
- Producers are ordered by BpNo and effective date

---

## Brokers and End-User Transportation

When the `END` (End User Transportation) attribute is enabled, the **Brokers tab** becomes visible. Broker data is stored in `PACTRL_EUT_BROKER` (`PAEutBrokerDO`).

Key fields:
- **BpNo**: Business Associate number of the broker
- **BpNm**: Name of the broker
- **EffDateFrom/EffDateTo**: Effective date range
- **LocId/TspNo**: Location and TSP association

Brokers are ordered by effective date (descending) and name.

---

## Affidavits

The **Affidavit tab** manages affidavit records (`PACTRL_LOC_AFFIDAVIT`) for locations. Affidavits are regulatory declarations associated with specific business parties.

Key fields:
- **AffidavitBpNo**: Business Associate number filing the affidavit
- **AffidavitBpNm**: Name of the business associate
- **EffDateFrom/EffDateTo**: Effective date range

### Curtailment Period Validation

Affidavit effective dates are validated against configurable **curtailment periods** (`CurtailPeriodFrom`/`CurtailPeriodTo`). If the affidavit dates fall outside the normal update period, the user receives a warning message.

---

## Supplier Pins

When the `MP` (Master Pins) attribute is enabled, the **Supplier Location tab** becomes visible. Supplier pin data is stored in `PACTRL_LOC_SUPPLIER_PINS` (`PALocSupplierPinsDO`).

Key fields:
- **SupplierLocId**: The supplier's location ID
- **BpNo/BpNm**: Business Associate details
- **LocNm**: Location name from the supplier's perspective
- **EffDateFrom/EffDateTo**: Effective date range

Supplier pins link a master location to its individual supplier metering points.

---

## Bidirectional Locations

Bidirectional locations support gas flow in either direction (receipt or delivery). Configuration involves:

1. **BiDirectLocId**: The paired location ID for the opposite flow direction
2. **BiDirectionalLocationNm**: Display name for the paired location
3. **PovCode = "B"**: The bidirectional point of view code

### Bidirectional Business Rules

- When a bidirectional pair is configured, the system creates `CAScheduleObjectCustom` records for scheduling
- The scheduling object ID follows the pattern: `{ReceiptLoc}^^{DeliveryLoc}`
- The scheduling object name follows the pattern: `{ReceiptLoc}_B{DeliveryLoc}`
- The `BidirectionalPOV` global configuration flag must be enabled
- Validation rules 031/032 ensure bidirectional configuration consistency

---

## Mass Change Operations

### Location Contact Mass Change

The **Location Contact Mass Change** screen (`LocationContactMassChangeController`) enables bulk updates to location contacts across multiple locations simultaneously.

Key features:
- Query contacts across multiple locations
- Add, update, or delete contact assignments in bulk
- Filter and sort operations
- Select/deselect rows for targeted changes
- Excel export for review (import is currently disabled)
- Bulk edit via JSON data exchange

Parameters:
- **IdContact**: Contact identifier
- **IdLoc**: Location identifier
- **LocSrc**: Location source filter
- **LocContactType**: Contact type filter

---

## Effective Dating

All location data in QPTM is **effective-dated**, meaning records have `EffDateFrom` and `EffDateTo` fields that define when a configuration is active.

**Key effective dating rules:**
- Multiple time slices can exist for the same location
- When saving changes, the system creates new effective-dated slices as needed
- Validation rule 001 validates effective date consistency
- Validation rule 034 validates date changes
- Child location effective dates must fall within the parent's effective date range (validation rules 010, 017)
- The "As Of Date" filters on various tabs allow users to view data for a specific point in time

---

## Key Business Rules

### Location Resolution

When location data changes (attributes, group memberships, or header fields), the system:
1. Evaluates whether a location resolution is needed (`IsDetailsLocResolve`)
2. If resolution is needed, updates the `PALocationGroup` records with a new `SetId`
3. Updates the `PatranLocResRangeStatus` table to signal downstream batch processes
4. Batch processes then re-resolve location assignments

### Integration Mode

When the system is in **integration mode** (`IsIntegrationMode`), certain fields on the screen become read-only based on the source module (`SrcModuleCode`). Integration-sourced fields are defined in `IntegrationScreenFields` configuration.

### Capacity Effective Date Configuration

The `AllowCapacityEffDate` global configuration controls whether capacity records can have effective dates different from the parent location.

### LDC (Local Distribution Company) Tab

The LDC tab appears only when the system is configured for LDC operations (checked via `IQPTMService_Utility.IsLDC()`). LDC-specific fields include:
- LDC Location Type Code
- Bill Cycle ID
- Division Code
- Customer name and address information

---

## Glossary

| Term | Definition |
|---|---|
| **Location/Meter** | A point on the pipeline system where gas is measured, received, delivered, or tracked. "Location" and "Meter" are used interchangeably in the codebase |
| **TSP** | Transporting Service Provider -- the pipeline company operating the transportation system |
| **POV** | Point of View -- indicates whether a location is a receipt (R), delivery (D), or bidirectional (B) point |
| **MeterNo/MtrNo** | The unique identifier for a location/meter point |
| **Effective Date** | The date range during which a location configuration is valid |
| **Aggregate Location** | A parent location that groups multiple child locations for operational purposes |
| **Interconnect** | A connection point between two different pipeline systems |
| **Operator (OPR)** | The business entity responsible for operating a physical location |
| **Confirm Party (CNF)** | The business entity that confirms nominations at a location |
| **Location Attribute** | A boolean flag that controls a location's behavior and capabilities (e.g., Nominatable, Allocable, Aggregate) |
| **Location Group** | A named grouping of locations for capacity, rate, scheduling, or reporting purposes |
| **Capacity/Rate Area** | A location group used specifically for capacity allocation and rate schedule assignment |
| **Bidirectional** | A location where gas can flow in either direction (receipt or delivery) |
| **Supplier Pin** | A sub-metering point associated with a master meter location |
| **Affidavit** | A regulatory declaration filed by a business associate for a specific location |
| **LDC** | Local Distribution Company -- a utility that distributes natural gas to end consumers |
| **MPS** | Measurement Information Process System -- an external integration source for location data |
| **FERC CID** | Federal Energy Regulatory Commission Company Identifier |
| **DRN** | Delivery Receipt Number -- a unique identifier used in interconnect transactions |
| **EUT** | End User Transportation -- a transportation arrangement for end-use customers |
| **NAESB** | North American Energy Standards Board -- industry standards organization |
| **SetId** | A sequence number used to track batches of location group changes for resolution processing |
| **Location Resolution** | The process of re-evaluating and updating location group memberships after data changes |
| **PPA Reallocation** | Post-save process that may trigger reallocation based on location changes |
| **Curtailment Period** | A configurable time period during which affidavit updates are normally expected |

---

*Cross-references:*
- [Architecture Documentation](./architecture.md) -- Technical implementation details
- [Troubleshooting Guide](./troubleshooting.md) -- Known issues and resolutions

*Last updated: 2026-03-03*

*Document version: 1.0*
