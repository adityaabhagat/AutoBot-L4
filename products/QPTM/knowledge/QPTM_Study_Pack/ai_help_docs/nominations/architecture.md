---
title: Nominations (NOM) - Architecture & Implementation
category: architecture
feature: Nominations (NOM)
related_repos: Web, Batch
keywords: QPTMNominationService, NominationMaintenanceController, NominationSubmissionController, validation engine, ActivityDetailDO, NominationDetailDO, NNCTRL_NOM, API
last_updated: 2026-03-03
---

# Nominations (NOM) - Architecture & Implementation

## Overview

This document describes the **technical architecture** of the Nominations feature in QPTM Web. It covers code structure, key classes, database schema, algorithms, and service dependencies.

For business concepts, see [Domain Documentation](./domain.md).
For troubleshooting, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [Layer Architecture](#layer-architecture)
2. [Service Layer](#service-layer)
3. [Controller Layer](#controller-layer)
4. [API Layer](#api-layer)
5. [Validation Engine](#validation-engine)
6. [Data Objects](#data-objects)
7. [Database Schema](#database-schema)
8. [Data Access Layer](#data-access-layer)
9. [Caching Strategy](#caching-strategy)
10. [Event System](#event-system)
11. [Widget Services](#widget-services)
12. [Key Algorithms](#key-algorithms)
13. [Configuration](#configuration)

---

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ WEB LAYER                                                       │
│  Quorum.QPTM.Web.Core/Controllers/                             │
│    NominationMaintenanceController.cs                           │
│    NominationSubmissionController.cs                            │
│    LCNominationSubmissionController.cs                          │
│    NominationErrorOverridesController.cs                        │
│    NominationAutogenController.cs                               │
│  Quorum.QPTM.Web.Controllers/APIControllers/                   │
│    NominationsController.cs                                     │
├─────────────────────────────────────────────────────────────────┤
│ SERVICE LAYER                                                   │
│  Quorum.QPTM.ServiceCore.Nomination/                           │
│    QPTMNominationService.cs           (907KB - primary)         │
│    QPTMAPINominationProcessor.cs      (API batch processing)    │
│    QPTMNominationWidgetService.cs     (widget operations)       │
│    QPTMNomAPIValidationUtility.cs     (API validation helpers)  │
│    QPTMNominationService_ErrorOverrideHelper.cs                 │
├─────────────────────────────────────────────────────────────────┤
│ VALIDATION LAYER                                                │
│  Quorum.QPTM.Validations/                                      │
│    ValidationEngineNomination.cs      (orchestrator)            │
│  Quorum.QPTM.Validations.Rules.Nomination/                     │
│    BusinessRules/    (61 rules)                                 │
│    LineRules/        (80 rules)                                 │
│    ForeignKey/       (25 rules)                                 │
│    SecurityRules/    (1 rule)                                   │
│    Helpers/          (PathValidator, ValidationRuleHelper)       │
├─────────────────────────────────────────────────────────────────┤
│ DATA ACCESS LAYER                                               │
│  Quorum.QPTM.DataAccess/                                       │
│    QNominationDataAccess.cs           (main DA implementation)  │
│    IQNominationDataAccess.cs          (interface)               │
│  Quorum.QPTM.DAL/                                              │
│    NominationHeaderDAL.cs                                       │
│    NominationDetailDAL.cs                                       │
│    NominationDetailErrorDAL.cs                                  │
│    NominationDetailHourlyDAL.cs                                 │
│    NominationLatestCycleDAL.cs                                  │
│    NominationLeaseDal.cs                                        │
│    NominationLifecycleDAL.cs                                    │
├─────────────────────────────────────────────────────────────────┤
│ DATA OBJECTS                                                    │
│  Quorum.QPTM.DataObject/                                       │
│    NominationDetailDOExt.cs                                     │
│    NominationHeaderDOExt.cs (CodeGen)                           │
│    NominationLeaseDOExt.cs                                      │
│    NominationLatestCycleDOExt.cs                                │
│    NominationLifecycleDOExt.cs                                  │
│    NominationErrorOverridesDOExt.cs                             │
│    NominationDetailHourlyDOExt.cs                               │
│    NominationDetailErrorDOExt.cs                                │
│    NominationPendingTitleXferDOExt.cs                           │
├─────────────────────────────────────────────────────────────────┤
│ EVENTS                                                          │
│  Quorum.QPTM.Events.Nomination/                                │
│    QPTMNomMaintEventDetector.cs                                 │
│    QPTMNomSubEventDetector.cs                                   │
│    QPTMNomMaintEventEmailNotificationHandler.cs                 │
│    QPTMNomSubEventEmailNotificationHandler.cs                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Service Layer

### QPTMNominationService.cs

**Location**: `Quorum.QPTM.ServiceCore.Nomination/QPTMNominationService.cs`
**Size**: ~907KB (largest service file in the codebase)

**Interfaces Implemented:**
- `IQPTMNominationService` - Core nomination operations
- `IQPTMConfirmationService` - Confirmation processing
- `IQPTMCycleService` - Cycle management
- `IQPTMContractService` - Contract lookups
- `IQPTMMaintenanceService` - Maintenance operations
- `IQPTMSecurityService` - Authorization
- `IQPTMNominationAutoGenService` - Autogeneration

### Key Service Methods

#### Retrieval

| Method | Description |
|--------|-------------|
| `GetNominations(tspNo, gasDay, shipper, activityNo)` | Retrieves a month of nominations for TSP, gas day, shipper |
| `GetNominations(tspNo, gasDay, shipper, activities)` | Same with pre-loaded activity collection |
| `GetNomFromDateToEOM(tspNo, gasDay)` | Nominations from gas day to end of month (batch use) |
| `GetNominationsWithErrors(tspNo, gasDay, serviceRequestor, ruleCodes)` | Only nominations with specific validation errors |

#### Validation

| Method | Description |
|--------|-------------|
| `ValidateNominations(tspNo, gasDay, nominations, out errorLevel, subsetValidation, concurrencyGasDay)` | Full validation with error level reporting |
| `ValidateNominationsForeignKey(tspNo, gasDay, nominations, out errorLevel, concurrencyGasDay)` | Foreign key validation only |

#### Submission

| Method | Description |
|--------|-------------|
| `SubmitNominations(actvNo, tspNo, gasDay, activities, out errorLevel, out idSetAdd, out idSetModify)` | Core submission; returns set IDs |
| `SubmitNominationsWithSetIDs(...)` | Submission with explicit set ID handling |
| `SubmitNominationsAndUpdatePendingTitleXfers(...)` | Submit + update title transfers |

#### Activity Management

| Method | Description |
|--------|-------------|
| `SaveActivity(ref actvNo, actvDescr, tspNo, srBpNo, idCycle, gasDay, defEndGasDay, overrideThroughEndDate, activities)` | Save draft; creates activity code if none |
| `RejectActivity(tspNo, actvNo, gasDayOffset)` | Mark activities as inactive |

#### Calculations

| Method | Description |
|--------|-------------|
| `CalculateKMDQ(nominations, gasDay)` | K-contract MDQ, MSQ, MDWQ, MDIQ, MinMSQ |
| `CalculateEPSQ(nominations, gasDay, idCycle)` | Evening Peak Scheduled Quantity |
| `CalculateLocationMDQ(nominations, gasDay)` | Location-level PPP MDQ |
| `CalculateRecHeatingFactors(nominations)` | BTU heating factors |

#### Cycle & Gas Day

| Method | Description |
|--------|-------------|
| `GetFirstNomOpenCycle(tspNo, gasDay)` | First open nomination cycle (defaults to ONT) |
| `GetFirstOpenCycle(tspNo, gasDay, deadlineCategory, deadlineType)` | First open cycle by category/type |
| `GetCurrentGasDay(tspNo, gasOffset)` | Current gas day adjusted by offset |
| `GetCycleStatus(tspNo, gasDay, deadlineCategory, deadlineType)` | Dict of cycle ID -> open status |
| `GetOpenCycleByDay(tspNo, gasDay, deadlineCategory, deadlineType, bENSCycles)` | Open cycles per day of month |
| `GetENSCycleInd()` | Dict of cycle ID -> ENS indicator |

### QPTMAPINominationProcessor.cs

**Location**: `Quorum.QPTM.ServiceCore.Nomination/QPTMAPINominationProcessor.cs`

Handles batch processing of nominations from the REST API:
- Groups nominations by TSP and gas day month
- Manages three result lists: `ErrorNominations`, `SubmittedNominations`, `SubmittedNominationsWithErrors`
- Tracks API messages for auditing via `APIMessages`
- Handles error override persistence

### QPTMNominationService_ErrorOverrideHelper.cs

**Location**: `Quorum.QPTM.ServiceCore.Nomination/QPTMNominationService_ErrorOverrideHelper.cs`

Manages error override logic:
- `CheckErrorOverrideChanges()` - Detects override flag changes
- Splits nominations when override end date < nomination end date
- Creates two records: one overridden, one not
- Copies error records with appropriate override status

---

## Controller Layer

### MVC Controllers

#### NominationMaintenanceController

**Location**: `Quorum.QPTM.Web.Core/Controllers/NominationMaintenanceController.cs`
**Security**: `Constants.SecurityObjectIDs.NominationMaintenance`
**Screen**: Contract-based nomination grid view

| Action | HTTP | Purpose |
|--------|------|---------|
| `GetActions()` | GET | Action buttons: Query, Submit, Close, Classification, Push, ENS Cycle |
| `Filter()` | POST | Apply grid filters |
| `ShowAll()` | POST | Clear all filters |
| `Push()` | POST | Toggle Up/Down data |
| `ENSCycle()` | POST | Toggle ENS Cycle visibility |
| `NominationMaintenanceParamsFieldUpdate()` | POST | Parameter field changes |
| `GetLinks()` | GET | Life Cycle link with parameters |

#### NominationSubmissionController

**Location**: `Quorum.QPTM.Web.Core/Controllers/NominationSubmissionController.cs`
**Security**: `"QVpSOANominationSubmission"`
**Screen**: NAESB nomination submission (PNT path/up/down tabs)

| Action | HTTP | Purpose |
|--------|------|---------|
| `GetActions()` | GET | Retrieve, Validate, Submit, Save Activity, Copy, Recalc, Import |
| `PNTPathGridAddNewRow()` | POST | Add row to Path grid |
| `PNTPathGridUpdate()` | POST | Update path grid |
| `PNTPathGridDeleteRow()` | POST | Delete path grid row |
| `PNTRecGridAddNewRow()` | POST | Add upstream receipt nomination |
| `PNTRecGridUpdate()` | POST | Update receipt grid |
| `SetLastSelectedRecNom()` | POST | Set selected receipt nomination |
| `PntSplitter()` | GET | PNT splitter partial view |
| `LocationSummaryGrid()` | GET | Location summary partial view |
| `PathForm()` | GET | Path form partial view |
| `PNTGridTab()` | GET | Path grid partial view |
| `CreateNewActivity()` | POST | Create new activity |
| `DoUICLink()` | GET | Process inbound link with TSP, gas day, cycle, SR params |

#### LCNominationSubmissionController

**Location**: `Quorum.QPTM.Web.Core/Controllers/LCNominationSubmissionController.cs`
**Security**: `"QVpSOALCNominationSubmission"`
**Screen**: Location-centric nominations

Inherits from `NominationSubmissionControllerBase` with additions:
- `SwitchLocationId()` - Switch current location context
- `GetPickIdBpForDropDown()` - Filtered business partner picklist
- `GetRecDelPickID()` - Rec/Del location picklist
- Suppresses "Show All Ups/Downs" option

#### NominationErrorOverridesController

**Location**: `Quorum.QPTM.Web.Core/Controllers/NominationErrorOverridesController.cs`
**Security**: `Constants.SecurityObjectIDs.NominationErrorOverrides`

| Action | HTTP | Purpose |
|--------|------|---------|
| `GetActions()` | GET | Query, Close buttons |
| `NominationErrorOverridesFieldUpdate()` | POST | Field change handler |
| `NominationErrorOverridesGridGetData()` | POST | Grid data with row numbers |
| `NominationErrorOverridesGridExcelExport()` | GET | Excel export |

#### NominationAutogenController

**Location**: `Quorum.QPTM.Web.Core/Controllers/NominationAutogenController.cs`
**Security**: `Constants.SecurityObjectIDs.NominationAutogen`

| Action | HTTP | Purpose |
|--------|------|---------|
| `GetActions()` | GET | New, Delete, Query, Save buttons |
| `NominationAutogenFieldUpdate()` | POST | Field change handler |
| `NominationAutogenContractFiltersGridGetData()` | POST | Contract filter grid |

### UIController Classes

Each MVC controller delegates to a UIController class for business logic:

| UIController | Purpose |
|-------------|---------|
| `QUIControllerNominationMaintenance` | Maintenance screen logic |
| `QUIControllerNominationSubmission` | Submission screen logic |
| `QUIControllerLCNominationSubmission` | Location-centric logic |
| `QUIControllerNominationErrorOverrides` | Error overrides logic |
| `QUIControllerNominationAutogen` | Autogen configuration logic |

### View Models

| ViewModel | Screen |
|-----------|--------|
| `NominationMaintenanceVM` | Maintenance grid (quantities, filters, totals) |
| `NominationSubmissionVM` | Submission screen (PNT totals, NAESB flags, tabs) |
| `LCNominationSubmissionVM` | Location-centric (location context, filters) |
| `NominationErrorOverridesRootVM` | Error overrides (gas day, SR filter) |
| `NominationAutogenRootVM` | Autogen config (target TSP, cycle, locations, thresholds) |

---

## API Layer

### NominationsController

**Location**: `Quorum.QPTM.Web.Controllers/APIControllers/NominationsController.cs`
**Route**: `api/v1/Nominations`
**Auth**: `[Authorize]`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Get nominations collection |
| `/{tsp}/{NominationId}` | GET | Get single nomination by ID |
| `/Summary` | GET | Nominations summary (grouping options) |
| `/ValidationMessages` | GET | Validation messages for a nomination |
| `/Discrepancies` | GET | Nomination discrepancies |
| `/Discrepancies/Summary` | GET | Discrepancies summary |
| `/Discrepancies/View` | GET | Discrepancies view |
| `/View` | GET | Nomination views |
| `/EnumeratedParameterValues` | GET | Enumerated parameter values |

**Common Parameters**: `tsp`, `beginGasDay`, `endGasDay`, `cycleId`, `serviceRequester`, `filter`, `embed`, `include`, `exclude`

**Data Shaping**:
- `embed` - Include sub-resources (None, All, or comma-separated)
- `include` / `exclude` - Property-level filtering
- Uses `PropertiesContractResolver` for JSON serialization

**Filter Enums**:
- `NominationFilterEnum` - Filter by status
- `NominationDiscrepanciesFilterEnum` - Filter by discrepancy type
- `NominationValidationMessageFilterEnum` - Filter by message type
- `NominationSummaryEnum` - Summary grouping

---

## Validation Engine

### ValidationEngineNomination.cs

**Location**: `Quorum.QPTM.Validations/ValidationEngineNomination.cs`

Orchestrates all nomination validation in strict order:

```
1. SECURITY (ValidationLevel = 1)
   └─ RuleNNSEC00010: User authorization check
   └─ If fails → Stop (security violation)

2. FOREIGN KEY (ValidationLevel = 2)
   └─ 25 rules (RuleNNFK*, RuleNNMAN*, RuleNNAK*)
   └─ Per-record validation
   └─ Can stop or continue based on bStopValidatingOnError

3. LINE (ValidationLevel = 3)
   └─ 80 rules (RuleNN000*-009*)
   └─ Per-record within date range
   └─ Uses NomLatestCycleData cache

4. BUSINESS (ValidationLevel = 5)
   └─ 61 rules (RuleNN000*-009*)
   └─ Collection-level validation
   └─ MDQ, imbalance, cross-record checks
```

### Rule Firing Logic

Each rule has conditional firing via `ShouldRuleFireForNom()`:

1. **TOS Check** (`ShouldRuleFireForTOS()`) - Rule applies to this Type of Service?
2. **Transaction Type Check** (`ShouldRuleFireForTransType()`) - Rule applies to this transaction type?
3. **Zero Nomination Check** (`ShouldRuleFireForZeroNom()`) - Skip for zero-quantity nominations?

Results cached in `TransTypeFireCache` and `ContractFireCache` dictionaries.

### Rule Data Objects

| Class | Level | Key Properties |
|-------|-------|---------------|
| `QRuleDataNominationSecurity` | Security | ValidatingUserID |
| `QRuleDataNominationForeign` | FK | ContractCache, LocationCache |
| `QRuleDataNominationLine` | Line | ContractCache, LocationCache, NominationSubset |
| `QRuleDataNominationBusiness` | Business | ValidatingUserID, LatestCycleData, InventoryData, NominationSubset |

### Validation Subsets

| Subset | Behavior |
|--------|----------|
| `ValidationNominationSubsetAll` | Includes all nominations |
| `ValidationNominationSubsetAGN` | Only AGN (autogen) system source nominations |

### Key Validation Rules Reference

#### Business Rules (selected)

| Rule | Purpose |
|------|---------|
| RuleNN00003060 | MDQ validation - total delivery < contract MDQ |
| RuleNN00003061-003073 | Delivery/Receipt quantity validation suite |
| RuleNN00003100-003115 | Transportation/path validation |
| RuleNN00003240-003245 | Imbalance and constraint validations |
| RuleNN00009550-009933 | Credit, lease, fuel preference validations |

#### Line Rules (selected)

| Rule | Purpose |
|------|---------|
| RuleNN00003010 | Contract validity across gas days |
| RuleNN00003013-003055 | Location, contract, path record validations |
| RuleNN00004010-004060 | Nomination attribute validations |
| RuleNN00004170-004227 | Contract attribute for different nom types |
| RuleNN00005000-005060 | Location and brokerage validations |

#### Foreign Key Rules (selected)

| Rule | Purpose |
|------|---------|
| RuleNNFK000010 | Contract existence validation |
| RuleNNFK000020-000060 | Location and partner existence |
| RuleNNMAN00010-000110 | Manual nomination FK validations |

### Error Attachment

```csharp
// Add error to nomination
string errorMsg = ValidationRuleHelper.AddErrorToNomination(
    rule,                                       // IValidationRuleBase
    activityDetailDO,                           // target nomination
    customErrorMsg,                             // optional message
    Constants.ValidationStateBusinessInvalid,   // error state
    begGasDay                                   // validation date
);

// Property-specific error
nomination.AddErrorMsg("SrCtrNo", errorMsg);
```

### Error States

| State | Code | Description |
|-------|------|-------------|
| ValidationStateLineInvalid | "VALD" | FK or line rule failure |
| ValidationStateBusinessInvalid | "INVL" | Business rule failure |
| ValidationStateLineValid | "LINE" | Passed line validations |
| ValidationStateBusinessValid | (varies) | All validations passed |

---

## Data Objects

### Primary Data Objects

#### ActivityDetailDO

Main nomination wrapper bridging database to UI:
- Contains `NominationDetailDO` data
- Holds errors, quantities, calculated factors
- Tracks state: Added, Modified, Deleted, Unchanged
- Can be "FromActivityTable" (saved draft) or direct nomination

Key properties:
- `TspNo`, `IdNom`, `IdNomHash`
- `BegGasDay`, `EndGasDay`, `IdCycle`
- `SrBpNo`, `SrCtrNo`
- `IdRecLoc`, `IdDelLoc`
- `RecQty`, `DelQty`, `FuelQty`, `FuelPct`
- `NomStatCode` - Validation state
- `ErrorAllowOverride` - Error can be overridden
- `IsPathRecord`, `IsRecLocNPP`, `IsDelLocNPP`
- `LastQueryDate` - For concurrency checking
- Child: `NominationDetailError` (error collection)
- Child: `NominationDetailHourly` (hourly data)

#### NominationDetailDO / NominationDetailDOExt

Core nomination database record (maps to NNCTRL_NOM_DTL):
- Implements `INomCommon` interface
- Manages conversion to/from `ActivityDetailDO`
- Extended properties in DOExt for UI presentation

#### NominationHeaderDO

Nomination batch header (maps to NNCTRL_NOM_HDR):
- Links detail records to header
- Contains header-level metadata: IdNom, TspNo, routing info
- Contains NominationDetailBindingList (child collection)

### Supporting Data Objects

| DO Class | Table | Purpose |
|----------|-------|---------|
| `NominationDetailErrorDO/Ext` | NNCTRL_NOM_DTL_ERR | Validation errors per detail |
| `NominationDetailHourlyDO/Ext` | NNCTRL_NOM_DTL_HRLY | Hourly quantity breakdown |
| `NominationLatestCycleDO/Ext` | NNCTRL_NOM_LATEST_CYCLE | Current cycle snapshot |
| `NominationLifecycleDO/Ext` | NNCTRL_LIFECYCLE | Lifecycle history |
| `NominationLeaseDO/Ext` | NNTRAN_NOM_LEASE | Lease nomination data |
| `NominationLimitDO` | NNCTRL_NOM_LIMIT | Nomination limits |
| `NominationOverallCycleDO` | NNCTRL_NOM_OVERALL_CYCLE | Cycle-level aggregation |
| `NominationTemplateDO` | NNCTRL_NOM_TEMPLATE | Templates for auto-population |
| `NominationCalDateDO` | NNTRAN_CAL_DATE | Calendar date references |
| `NominationContractPreferenceDO` | NNCTRL_CTR_PREF | Contract preferences |
| `NominationErrorOverridesDO/Ext` | NNTRAN_ERROR_OVERRIDES | Error override records |
| `NominationPendingTitleXferDO/Ext` | (non-DB) | Pending title transfers |

---

## Database Schema

### Table Inventory

| Table | Prefix | Description |
|-------|--------|-------------|
| **NNCTRL_NOM_HDR** | NNCTRL | Nomination header (main control) |
| **NNCTRL_NOM_DTL** | NNCTRL | Nomination detail (line items) |
| **NNCTRL_NOM_DTL_ERR** | NNCTRL | Detail validation errors |
| **NNCTRL_NOM_DTL_HRLY** | NNCTRL | Detail hourly breakdown |
| **NNCTRL_NOM_LATEST_CYCLE** | NNCTRL | Latest cycle snapshot |
| **NNCTRL_NOM_LIMIT** | NNCTRL | Nomination limits |
| **NNCTRL_NOM_OVERALL_CYCLE** | NNCTRL | Cycle-level aggregation |
| **NNCTRL_NOM_TEMPLATE** | NNCTRL | Nomination templates |
| **NNCTRL_CTR_PREF** | NNCTRL | Contract preferences |
| **NNCTRL_LIFECYCLE** | NNCTRL | Nomination lifecycle |
| **NNCTRL_AUTOGEN_HDR** | NNCTRL | Autogen rule headers |
| **NNTRAN_NOM_LEASE** | NNTRAN | Lease nominations |
| **NNTRAN_CAL_DATE** | NNTRAN | Calendar dates |
| **NNTRAN_ERROR_OVERRIDES** | NNTRAN | Error overrides |

**Naming Convention**: `NNCTRL_*` = Control tables, `NNTRAN_*` = Transaction tables

### Key Columns (NNCTRL_NOM_HDR)

| Column | Type | Description |
|--------|------|-------------|
| IdNom | int | Nomination ID (PK) |
| TspNo | short | TSP identifier |
| SrBpNo | string | Service requester BP number |
| SrCtrNo | string | Service requester contract |
| IdRecLoc | string | Receipt location ID |
| IdDelLoc | string | Delivery location ID |
| RecBpNo | string | Receipt business partner |
| DelBpNo | string | Delivery business partner |
| TransTypeCode | string | Transaction type |
| NomCapTypeCode | string | Capacity type |
| IsUpRecord | bool | Upstream flag |
| IsDnRecord | bool | Downstream flag |
| IsPathRecord | bool | Path record flag |
| NaesbModelCode | string | NAESB model (PNT/PT) |
| IdNomHash | string | Hash for uniqueness |

### Key Columns (NNCTRL_NOM_DTL)

| Column | Type | Description |
|--------|------|-------------|
| NomSeqNo | int | Detail sequence (PK) |
| TspNo | short | TSP identifier |
| IdNom | int | FK to header |
| BegGasDay | DateTime | Start gas day |
| EndGasDay | DateTime | End gas day |
| IdCycle | short | Cycle ID |
| RecQty | decimal | Receipt quantity |
| DelQty | decimal | Delivery quantity |
| FuelQty | decimal | Fuel quantity |
| FuelPct | decimal | Fuel percentage |
| NomStatCode | string | Validation status |
| ActnCode | string | Action code |
| RecRank | int | Receipt ranking |
| DelRank | int | Delivery ranking |
| IsDelete | bool | Soft delete flag |
| IsFuelOvrd | bool | Fuel override flag |
| IdNomHash | string | Hash for uniqueness |

### Key Relationships

```
NNCTRL_NOM_HDR (IdNom, TspNo)
  │
  ├── NNCTRL_NOM_DTL (NomSeqNo, TspNo, IdNom)
  │     ├── NNCTRL_NOM_DTL_ERR (NomSeqNo)
  │     └── NNCTRL_NOM_DTL_HRLY (NomHrlyNo, NomSeqNo)
  │
  ├── NNCTRL_NOM_LATEST_CYCLE (IdNom, TspNo, GasDay, IdCycle)
  │
  └── NNCTRL_LIFECYCLE (IdNom, TspNo, GasDay, IdCycle)

Cross-References:
  SrBpNo, RecBpNo, DelBpNo  →  BusinessAssociate
  SrCtrNo, RecCtrNo, DelCtrNo  →  Contract (KCTRL_CTR_*)
  IdRecLoc, IdDelLoc  →  Location (PACTRL_LOC*)
  IdCycle  →  Cycle
```

---

## Data Access Layer

### QNominationDataAccess.cs

**Location**: `Quorum.QPTM.DataAccess/QNominationDataAccess.cs`
**Interface**: `IQNominationDataAccess`

#### Header Operations

```csharp
GetNominationHeader(short tspNo, List<Filter> additionalFilters)
GetNominationHeader(short tspNo, int nomId)
GetNominationHeaderByHashID(short tspNo, string idNomHash)
```

#### Detail Operations

```csharp
GetNominationDetails(short tspNo, List<Filter> additionalFilters)
GetLatestNomDetailWithFilter(short tspNo, List<Filter> additionalFilters)
GetCountNominationDetails(short tspNo, FilterCollection additionalFilters)
```

#### Cycle Operations

```csharp
GetNomLatestCycle(short tspNo, DateTime gasDay, short idCycle, int nomId)
GetNomLatestCycle(short tspNo, DateTime gasDay, short idCycle, List<Filter> additionalFilters)
```

#### Activity Operations

```csharp
GetActivityInfo(short tspNo, int activityNo)
GetActivityDetail(short tspNo, int activityNo)
```

### DAL Pattern

Uses `SelectByFilterAsList<T>()` with `FilterCollection`:
- `ControlTableBaseRepositoryDAL` - Base for NNCTRL tables
- `TransactionBaseDO` - Base for NNTRAN tables
- Supports child object retrieval (`RetrieveChildren` flag)
- Supports pagination (`startRecord`, `maxRecords`)

---

## Caching Strategy

### Multi-Level Caching

| Cache | Type | Purpose |
|-------|------|---------|
| `NominationHeaderCache` | SingletonCache | Nomination headers by ID and hash |
| `NomControlCache` | SingletonCache | Control nomination data |
| `ContractCache` | SingletonCache | Contract existence/date range checks |
| `LocationCache` | SingletonCache | Location lookups and attributes |
| `CycleCache` | SingletonCache | Cycle definitions and status |
| `TspCache` | SingletonCache | TSP preferences and config |
| `RuleCache` | SingletonCache | Compiled validation rule metadata |
| `AutoGenCache` | SingletonCache | Autogen type definitions |

### Validation Caching

- `TransTypeFireCache` - Dict caching transaction type rule firing decisions
- `ContractFireCache` - Dict caching TOS/contract rule firing decisions
- `NomLatestCycleData` - Shared between Line and Business validation levels
- Cache invalidation via `RuleCacheChanged` event clears compiled rule sets

### Cache Refresh

```csharp
// Header cache with refresh
GetNomHeaderFromNomIDWithRefresh()

// Rule cache invalidation
void Instance_RuleCacheChanged(object sender, EventArgs e) {
    _lock_NomRulesByModel.WriteLock(writeNomRules => {
        writeNomRules.Clear();  // Force recompilation
    });
}
```

---

## Event System

### Event Detectors

**Location**: `Quorum.QPTM.Events.Nomination/`

| Class | Trigger |
|-------|---------|
| `QPTMNomMaintEventDetector` | Nomination maintenance changes |
| `QPTMNomSubEventDetector` | Nomination submissions |

### Event Handlers

| Class | Action |
|-------|--------|
| `QPTMNomMaintEventEmailNotificationHandler` | Email on maintenance changes |
| `QPTMNomSubEventEmailNotificationHandler` | Email on submissions |

### Event Data

| Class | Payload |
|-------|---------|
| `QNomMaintNotificationEventData` | Maintenance event details |
| `QNomSubNotificationEventData` | Submission event details |

---

## Widget Services

### QPTMNominationWidgetService

**Location**: `Quorum.QPTM.ServiceCore.Nomination/QPTMNominationWidgetService.cs`

| Method | Purpose |
|--------|---------|
| `GetNominationErrors(tspNo, gasDay)` | Nominations with validation errors |
| `GetNominationsPendingTitleXfer(tspNo, gasDay, cycle, shipper, titleXferAttr)` | Pending title transfers |
| `GetConfirmationsCuts(tspNo, fromDate, toDate)` | Confirmation totals/cuts |
| `GetNominationChanges(tspNo, gasDay, cycle)` | Nomination changes/modifications |

**Dependencies**: IQPTMNominationServiceSide, IQPTMCycleServiceSide, IQPTMConfirmationServiceSide, IQPTMSecurityServiceSide, IQContractDataAccess, IQNominationDataAccess, IQPipelineAdminDataAccess

---

## Key Algorithms

### Validation Flow Algorithm

```
Input: List<ActivityDetailDO> nominations, DateTime gasDay
Output: string validationErrorLevel

1. FindGasDaysWithChanges() → identify impacted dates
2. For each impacted date range:
   a. Run Security rules (level 1)
   b. Run Foreign Key rules (level 2)
      - Backup FK errors
      - If FK errors AND not "submit by contract" → stop
   c. Run Line rules (level 3)
      - Loop until no new line errors
      - Merge backed-up FK errors
   d. Run Business rules (level 5)
      - Skip if FK errors present (unless "submit by contract")
3. Return highest error level encountered
```

### Submission Flow Algorithm

```
Input: Activity nominations, tspNo, gasDay
Output: idSetAdd (new), idSetModify (updated)

1. Validate all nominations
2. If "submit by contract" mode:
   a. FilterOutErrorNominationsByContract()
   b. Separate error/non-error nominations
3. Create submission records
4. Assign set IDs:
   - idSetAdd for Added nominations
   - idSetModify for Modified nominations
5. Persist to NNCTRL_NOM_HDR / NNCTRL_NOM_DTL
6. Create lifecycle records
7. Update title transfers if applicable
```

### Error Override Split Algorithm

```
Input: Nomination with override change, override end date
Output: Two nominations (overridden + non-overridden)

1. Scan errors: IsOvrd != IsOvrdOriginal
2. If override end date < nomination EndGasDay:
   a. Clone nomination
   b. Original: EndGasDay = override end date
   c. Clone: BegGasDay = override end date + 1
   d. Copy errors to each with appropriate override status
3. If override end date >= nomination EndGasDay:
   a. Simply update override status on existing nomination
```

---

## Configuration

### Global Settings

| Setting | Purpose |
|---------|---------|
| `ALLOW_USER_OVRD_FUEL` | Allow fuel override by users |
| `SHOW_K_QUANTITIES_IN_PATHGRID` | Display MSQ, MDIQ, MDWQ, MinMSQ |
| `BLOCK_BI_NOM_SUBMISSION` | Block submissions with business errors |
| `DisableNomSubmissionByContract` | Disable contract-level submission filtering |
| `UseZeroNomTemplate` | Enable zero nomination templates |
| `NnnomloadMaxRecsPerSave` | Batch size for NNOMLOAD submissions |
| `UseSRK99999` | Enable default contract "99999" (pathless) |
| `AllowNomDeletes` | Enable deletion capability in grid |
| `IsEnabledLCNOMSTrackingMsgs` | Enable LC nomination diagnostic tracing |

### Security Objects

| Security ID | Screen |
|-------------|--------|
| `NominationMaintenance` | Nomination Maintenance |
| `NominationErrorOverrides` | Error Overrides |
| `NominationAutogen` | Autogeneration Config |
| `QVpSOANominationSubmission` | Nomination Submission |
| `QVpSOALCNominationSubmission` | Location-Centric Nominations |

### Permission Flags

| Flag | Controls |
|------|----------|
| `IsUserInternal` | Internal-only features (Reject, Classification) |
| `AllowFuelReCalcForExternalUser` | External fuel recalculation |
| `AllowHeatingFactorsReCalcForExternalUser` | External heating factor recalc |
| `ShowClassification` | Classification button visibility |
| `ShowENSCycle` | ENS Cycle visibility |
| `EnableTitleXfer` | Title transfer button |
| `EnalbleBulkCopy` | Bulk copy functionality |

### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `UomType_Energy` | "ENG" | Energy-based units |
| `UomType_Volume` | "VOL" | Volume-based units |
| `DeadlineCategory.Nomination` | "NOM" | Nomination deadline category |
| `DeadlineType.OnTime` | "ONT" | Standard deadline type |
| `DeadlineType.EndofFlowday` | "INT" | Intraday deadline type |
| `DeadlineType.LatestNomAccept` | "LAT" | Latest nomination time |
| `LocationAttribute.NPPool` | "NPPool" | National Pricing Pool |
| `msc_sSvcReqKDef` | "99999" | Default contract number |

---

## Related Documentation

- [Domain Documentation](./domain.md) - Business concepts and workflows
- [Troubleshooting Guide](./troubleshooting.md) - Known issues and solutions
- [CAS Architecture](../capacity-scheduling-allocations/architecture.md) - Scheduling that processes nominations
- [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) - Feature/keyword mapping

---

*Last updated: 2026-03-03*
*Document version: 1.0*
