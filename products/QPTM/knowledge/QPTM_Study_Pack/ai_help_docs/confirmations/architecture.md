---
title: Confirmations (CONF) - Architecture
category: architecture
feature: Confirmations (CONF)
related_repos: Web, Batch
keywords: CONF, architecture, code structure, services, controllers, API, validation, data objects, database, batch, CFCTRL_CONF, ConfirmationResponseController, ConfirmationSummaryController, ConfirmationsController, ValidationEngineConfirmation, QPTMConfirmationResponseServiceExt, QPTMConfirmationWidgetService
last_updated: 2026-03-03
---

# Confirmations (CONF) - Architecture

## Overview

This document explains the **technical architecture** of the Confirmations (CONF) system in QPTM. It covers code structure, service layer design, controller implementation, API endpoints, validation engine, database schema, and integration patterns.

For business concepts and terminology, see [Domain Documentation](./domain.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Web Application Layer](#web-application-layer)
3. [Service Layer](#service-layer)
4. [API Layer](#api-layer)
5. [Validation Engine](#validation-engine)
6. [Data Model](#data-model)
7. [Database Schema](#database-schema)
8. [Batch Processing](#batch-processing)
9. [Configuration Settings](#configuration-settings)
10. [Processing Flow](#processing-flow)
11. [Integration Points](#integration-points)

---

## System Architecture

### Architectural Layers

```
+-------------------------------------------------------------+
|                    WEB APPLICATION LAYER                      |
|  +--------------------+  +---------------------+            |
|  | Confirmation       |  | Confirmation        |            |
|  | Response           |  | Summary             |            |
|  | Controller         |  | Controller          |            |
|  | (MVC)              |  | (MVC)               |            |
|  +--------------------+  +---------------------+            |
+-------------------------------------------------------------+
|                    API LAYER                                  |
|  +----------------------------------------------------------+|
|  | ConfirmationsController (/api/v1/Confirmations)          ||
|  | GET collection | GET summary | GET view | GET by ID      ||
|  | GET enumerated values                                     ||
|  +----------------------------------------------------------+|
+-------------------------------------------------------------+
|                    SERVICE LAYER                              |
|  +-----------------------------+  +-------------------------+|
|  | QPTMConfirmation            |  | QPTMConfirmation        ||
|  | ResponseServiceExt          |  | WidgetService           ||
|  | (Location contacts,         |  | (GetSummary, GetFiltered||
|  |  confirmation entry)        |  |  ApplyCycleFilters)     ||
|  +-----------------------------+  +-------------------------+|
+-------------------------------------------------------------+
|                    VALIDATION LAYER                           |
|  +----------------------------------------------------------+|
|  | ValidationEngineConfirmation                              ||
|  | Level 1: Security | Level 2: FK | Level 3: Line          ||
|  | Level 4: Business                                         ||
|  +----------------------------------------------------------+|
+-------------------------------------------------------------+
|                    DATA ACCESS LAYER                          |
|  +----------------------------------------------------------+|
|  | ConfirmationDO/DOExt (CFCTRL_CONF)                       ||
|  | ConfirmationSummaryDO | ConfirmationHourlyDO             ||
|  | ConfirmationLevelDO/DetailDO | ConfirmationPlanDO        ||
|  | ConfirmationRoleDO                                        ||
|  +----------------------------------------------------------+|
+-------------------------------------------------------------+
|                    DATABASE LAYER                             |
|  +----------------------------------------------------------+|
|  | CFCTRL_CONF | CFCTRL_CONF_HOURLY | CFCTRL_CONF_LVL      ||
|  | CFCTRL_CONF_LVL_DTL | CFCTRL_CONF_PLAN                  ||
|  | CFCTRL_CONF_ROLE                                          ||
|  +----------------------------------------------------------+|
+-------------------------------------------------------------+
```

### Key Design Patterns

- **MVC Pattern**: Confirmation Response and Summary use separate MVC controllers
- **Service Layer Pattern**: Business logic encapsulated in service classes
- **Repository Pattern**: Data access through DOExt classes following the QPTM convention
- **Validation Engine**: 4-level validation pipeline (Security, FK, Line, Business)
- **Widget Service Pattern**: Summary and filtered data retrieval through widget services
- **Kendo DataSource**: Grid data binding via Kendo UI DataSource on summary screens

---

## Web Application Layer

### ConfirmationResponseController

**Location**: `Quorum.QPTM.Web.Core/Controllers/`

**Security Object**: `QVpSOAConfirmationResponse`

**Purpose**: Handles the confirmation entry and editing workflow. This is the primary controller for TSP operators entering confirmation quantities.

**Key Actions:**

| Action | HTTP Method | Description |
|--------|-------------|-------------|
| `ConfOtherChanges` | POST | Processes confirmation quantity changes and related field updates |
| `UpdateHourlyProfileTotal` | POST | Recalculates hourly profile when daily total changes |
| `SetSelectedConfirmation` | POST | Sets the currently selected confirmation record in the session |
| `GetActions` | GET | Returns available actions including "Edit Closed Cycle" based on security and cycle status |

**Action Details:**

**ConfOtherChanges**:
- Receives updated confirmation data from the UI
- Validates changes through ValidationEngineConfirmation
- Persists confirmed quantities, reduction reasons, and confirmation methods
- Triggers path balancing recalculation if enabled

**UpdateHourlyProfileTotal**:
- Called when the daily confirmed quantity changes
- Redistributes hourly values to match the new daily total
- Validates hourly profile consistency (sum of hours = daily total)

**SetSelectedConfirmation**:
- Stores the selected confirmation record identifier in session state
- Used for navigation between confirmation grid and detail views

**GetActions (Edit Closed Cycle)**:
- Returns the list of available actions for the current confirmation
- Includes "Edit Closed Cycle" action when:
  - The current cycle is closed
  - The user has appropriate security permissions
  - The `UseSecObjAllowUserMakeCutOnATTLocation` configuration is enabled

### ConfirmationSummaryController

**Location**: `Quorum.QPTM.Web.Core/Controllers/`

**Security Object**: `ConfirmationSummary`

**Purpose**: Provides the summary view of confirmation data with grid display, filtering, and export capabilities.

**Key Features:**

| Feature | Description |
|---------|-------------|
| **Kendo Grid** | Data displayed using Kendo DataSource with server-side paging and sorting |
| **Excel Export** | Export confirmation summary data to Excel format |
| **Navigation Links** | Links to related screens: Lifecycle, NomSubmission, ConfResponse |
| **Summary Views** | By Location, By Shipper, By Path aggregation views |

**Grid Configuration:**
- Uses Kendo DataSource for server-side data retrieval
- Supports paging, sorting, and filtering
- Column definitions include NomQty, SchdQty, ConfQty, Variance, Status
- Custom column templates for variance highlighting (red for cuts, green for full confirmation)

**Navigation Links:**
- **Lifecycle**: Links to the nomination lifecycle view for the selected record
- **NomSubmission**: Links to the nomination submission screen
- **ConfResponse**: Links to the confirmation response entry screen

---

## Service Layer

### QPTMConfirmationResponseServiceExt

**Location**: `Quorum.QPTM.ServiceCore/`

**Purpose**: Extended service for confirmation response operations, including location contact management and confirmation data preparation.

**Key Responsibilities:**
- Location contact data retrieval for confirmation locations
- Confirmation data preparation for the response entry screen
- Coordination between nomination data and confirmation records
- Support for confirmation submission workflow

**Key Methods:**
- Location contact retrieval for associated confirmation locations
- Confirmation data loading and preparation
- Submission processing coordination

### QPTMConfirmationWidgetService

**Location**: `Quorum.QPTM.ServiceCore/`

**Purpose**: Provides summary and filtered confirmation data for the widget/summary views. This is the primary service for data retrieval in the confirmation summary screens.

**Key Methods:**

| Method | Description |
|--------|-------------|
| `GetSummaryConfirmations` | Retrieves aggregated confirmation data for the summary view |
| `GetFilteredConfirmations` | Retrieves filtered confirmation data based on ConfirmationsFilterEnum |
| `ApplyCycleFilters` | Applies cycle-based filters (NextOpenCycle, PreviousDayCycle) |
| `ApplyNomLatestCycleFilter` | Filters to the latest cycle for each nomination |

**GetSummaryConfirmations:**
- Returns aggregated data by location, shipper, or path
- Calculates totals for NomQty, SchdQty, ConfQty, and Variance
- Supports multiple summary views (ByLocation, ByShipper, ByPath)

**GetFilteredConfirmations with ConfirmationsFilterEnum:**
- Accepts a `ConfirmationsFilterEnum` parameter to specify filter type
- Filter enum values correspond to the business filter types:
  - `NextOpenCycle` - Filter to the next open confirmation cycle
  - `PreviousDayCycle` - Filter to previous day's cycle data
  - `Unconfirmed` - Filter to nominations without confirmations
  - `Unbalanced` - Filter to paths with receipt/delivery imbalance
  - `ExcludeZero` - Exclude zero-quantity records

**ApplyCycleFilters:**
- Applies cycle-specific filtering logic
- Handles the `DefaultToOpenConfirmationCycle` configuration
- Manages cycle status (open vs closed) determination

**ApplyNomLatestCycleFilter:**
- Ensures only the latest cycle version of each nomination is shown
- Prevents duplicate display of nominations across cycles
- Critical for accurate confirmation summary data

---

## API Layer

### ConfirmationsController

**Location**: `Quorum.QPTM.Web.Controllers/APIControllers/`

**Base URL**: `/api/v1/Confirmations`

**Purpose**: RESTful API for confirmation data access. Provides programmatic access to confirmation data for integrations and external consumers.

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/Confirmations` | Get confirmation collection with query parameters |
| `GET` | `/api/v1/Confirmations/Summary/ByLocation` | Get confirmation summary aggregated by location |
| `GET` | `/api/v1/Confirmations/Summary/ByShipper` | Get confirmation summary aggregated by shipper |
| `GET` | `/api/v1/Confirmations/Summary/ByPath` | Get confirmation summary aggregated by path |
| `GET` | `/api/v1/Confirmations/View` | Get confirmation view data |
| `GET` | `/api/v1/Confirmations/{id}` | Get a specific confirmation by ID |
| `GET` | `/api/v1/Confirmations/EnumeratedValues` | Get enumerated values for confirmation dropdowns |

### API Details

**GET Collection** (`/api/v1/Confirmations`):
- Query Parameters: TSP_NO, GAS_DAY, ID_CYCLE, and optional filters
- Returns paginated list of confirmation records
- Supports OData-style filtering and sorting

**GET Summary** (`/api/v1/Confirmations/Summary/{aggregation}`):
- Aggregation types: ByLocation, ByShipper, ByPath
- Returns aggregated totals with variance calculations
- Used by external reporting and dashboard systems

**GET View** (`/api/v1/Confirmations/View`):
- Returns formatted confirmation view data
- Includes related nomination and scheduling data
- Used by the confirmation detail view

**GET by ID** (`/api/v1/Confirmations/{id}`):
- Returns a single confirmation record by its unique identifier
- Includes all detail fields and related data

**GET Enumerated Values** (`/api/v1/Confirmations/EnumeratedValues`):
- Returns lookup values for confirmation-related dropdowns
- Includes ConfMethCode, ReductRsnCode, and other coded values

---

## Validation Engine

### ValidationEngineConfirmation

**Location**: `Quorum.QPTM.Validations.Rules/`

**Purpose**: Four-level validation engine for confirmation data. All confirmation changes pass through this validation pipeline before persistence.

### Validation Levels

| Level | Name | Purpose | Examples |
|-------|------|---------|----------|
| **Level 1** | Security | Verify user has permission to modify confirmation | QVpSOAConfirmationResponse security check, cycle open/closed status |
| **Level 2** | FK (Foreign Key) | Validate referential integrity | TSP exists, Location exists, Contract exists, Cycle is valid |
| **Level 3** | Line | Validate individual field values | ConfQty >= 0, ReductRsnCode provided when ConfQty < NomQty, Hourly profile total = daily total |
| **Level 4** | Business | Validate business rules and cross-record constraints | EPSQ validation, Path balancing, Cycle deadline enforcement |

### Validation Flow

```
Confirmation Change Request
        |
        v
+---Level 1: Security---+
| - User has permission? |
| - Cycle is accessible? |
| - Edit closed cycle?   |
+------------------------+
        | PASS
        v
+---Level 2: FK----------+
| - TSP_NO valid?         |
| - Location exists?      |
| - Contract active?      |
| - Cycle ID valid?       |
+--------------------------+
        | PASS
        v
+---Level 3: Line--------+
| - ConfQty >= 0?         |
| - ReductRsn provided?   |
| - Hourly profile valid? |
| - ConfMethCode set?     |
+--------------------------+
        | PASS
        v
+---Level 4: Business----+
| - EPSQ check passed?    |
| - Path balanced?        |
| - Cycle not expired?    |
| - Cross-record valid?   |
+--------------------------+
        | PASS
        v
  Persist Changes
```

### Validation Error Handling

- Each level returns a collection of validation errors
- Processing stops at the first level with errors (fail-fast)
- Error messages include field name, error code, and user-friendly description
- Validation results are displayed in the UI as error notifications

---

## Data Model

### Data Objects

| Data Object | Table | Description |
|-------------|-------|-------------|
| `ConfirmationDO` / `ConfirmationDOExt` | `CFCTRL_CONF` | Primary confirmation record; DOExt extends CodeGen |
| `ConfirmationSummaryDO` | (Calculated) | Aggregated confirmation summary data |
| `ConfirmationHourlyDO` | `CFCTRL_CONF_HOURLY` | Hourly profile data (24 hourly values per confirmation) |
| `ConfirmationLevelDO` | `CFCTRL_CONF_LVL` | Confirmation level hierarchy records |
| `ConfirmationLevelDetailDO` | `CFCTRL_CONF_LVL_DTL` | Confirmation level detail records |
| `ConfirmationPlanDO` | `CFCTRL_CONF_PLAN` | Planned confirmation quantities |
| `ConfirmationRoleDO` | `CFCTRL_CONF_ROLE` | Confirmation data by business party role |

### ConfirmationDO / ConfirmationDOExt

**Purpose**: Primary data object representing a confirmation record. The DOExt class extends the auto-generated ConfirmationDO with custom properties and methods.

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| TSP_NO | int | TSP number |
| GAS_DAY | DateTime | Gas day for the confirmation |
| ID_CYCLE | int | Cycle identifier (1=Timely, 2=Evening, 3=ID1, 4=ID2, 6=ID3) |
| ID_NOM | int | Associated nomination ID |
| CONF_QTY | decimal | Confirmed quantity |
| NOM_QTY | decimal | Nominated quantity (reference) |
| SCHD_QTY | decimal | Scheduled quantity (reference from CAS) |
| CONF_METH_CD | string | Confirmation method code |
| REDUCT_RSN_CD | string | Reduction reason code |
| IS_HR_PROF | bool | Whether hourly profile is enabled |
| ID_REC_LOC | int | Receipt location ID |
| ID_DEL_LOC | int | Delivery location ID |
| SR_CTR_NO | int | Service requester contract number |
| SR_BP_NO | int | Service requester business party number |

**Important**: Never modify the CodeGen-generated `ConfirmationDO.cs` file. All customizations must be in `ConfirmationDOExt.cs`.

### ConfirmationHourlyDO

**Purpose**: Stores hourly profile data for a confirmation.

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| TSP_NO | int | TSP number |
| GAS_DAY | DateTime | Gas day |
| ID_CYCLE | int | Cycle identifier |
| CONF_ID | int | Parent confirmation ID |
| HR_01 through HR_24 | decimal | Hourly quantity values |

---

## Database Schema

### Core Tables

#### CFCTRL_CONF (Primary Confirmation Table)

**Purpose**: Stores all confirmation records. One record per nomination per cycle.

**Key Columns:**
```
CFCTRL_CONF
  TSP_NO           INT          -- TSP identifier
  GAS_DAY          DATETIME     -- Gas day
  ID_CYCLE         INT          -- Cycle (1,2,3,4,6)
  CONF_ID          INT          -- Unique confirmation identifier
  ID_NOM           INT          -- Associated nomination
  CONF_QTY         DECIMAL      -- Confirmed quantity
  NOM_QTY          DECIMAL      -- Nominated quantity
  SCHD_QTY         DECIMAL      -- Scheduled quantity
  CONF_METH_CD     VARCHAR      -- Confirmation method
  REDUCT_RSN_CD    VARCHAR      -- Reduction reason
  IS_HR_PROF       BIT          -- Hourly profile flag
  ID_REC_LOC       INT          -- Receipt location
  ID_DEL_LOC       INT          -- Delivery location
  SR_CTR_NO        INT          -- Contract number
  SR_BP_NO         INT          -- Business party number
  CONF_STAT_CD     VARCHAR      -- Confirmation status
  CRTE_DT          DATETIME     -- Created date
  UPDT_DT          DATETIME     -- Updated date
  UPDT_USER_ID     VARCHAR      -- Updated by user
```

#### CFCTRL_CONF_HOURLY (Hourly Profile Table)

**Purpose**: Stores hour-by-hour confirmation quantities.

**Key Columns:**
```
CFCTRL_CONF_HOURLY
  TSP_NO           INT          -- TSP identifier
  GAS_DAY          DATETIME     -- Gas day
  ID_CYCLE         INT          -- Cycle
  CONF_ID          INT          -- Parent confirmation ID (FK to CFCTRL_CONF)
  HR_01 - HR_24    DECIMAL      -- Hourly quantities (24 columns)
  CRTE_DT          DATETIME     -- Created date
  UPDT_DT          DATETIME     -- Updated date
```

#### CFCTRL_CONF_LVL (Confirmation Level Table)

**Purpose**: Stores confirmation level hierarchy data for aggregation and reporting.

**Key Columns:**
```
CFCTRL_CONF_LVL
  TSP_NO           INT          -- TSP identifier
  GAS_DAY          DATETIME     -- Gas day
  ID_CYCLE         INT          -- Cycle
  CONF_LVL_ID      INT          -- Level identifier
  CONF_LVL_TYPE    VARCHAR      -- Level type
  PARENT_LVL_ID    INT          -- Parent level (for hierarchy)
  AGG_CONF_QTY     DECIMAL      -- Aggregated confirmed quantity
  AGG_NOM_QTY      DECIMAL      -- Aggregated nominated quantity
```

#### CFCTRL_CONF_LVL_DTL (Confirmation Level Detail Table)

**Purpose**: Stores detail-level data within each confirmation level.

**Key Columns:**
```
CFCTRL_CONF_LVL_DTL
  TSP_NO           INT          -- TSP identifier
  CONF_LVL_ID      INT          -- Parent level ID (FK to CFCTRL_CONF_LVL)
  CONF_ID          INT          -- Confirmation ID (FK to CFCTRL_CONF)
  DTL_SEQ_NO       INT          -- Detail sequence number
  CONF_QTY         DECIMAL      -- Detail confirmed quantity
```

#### CFCTRL_CONF_PLAN (Confirmation Plan Table)

**Purpose**: Stores planned confirmation quantities (pre-submission).

**Key Columns:**
```
CFCTRL_CONF_PLAN
  TSP_NO           INT          -- TSP identifier
  GAS_DAY          DATETIME     -- Gas day
  ID_CYCLE         INT          -- Cycle
  PLAN_ID          INT          -- Plan identifier
  PLANNED_QTY      DECIMAL      -- Planned confirmation quantity
  PLAN_STAT_CD     VARCHAR      -- Plan status
```

#### CFCTRL_CONF_ROLE (Confirmation Role Table)

**Purpose**: Stores confirmation data organized by business party role.

**Key Columns:**
```
CFCTRL_CONF_ROLE
  TSP_NO           INT          -- TSP identifier
  GAS_DAY          DATETIME     -- Gas day
  ID_CYCLE         INT          -- Cycle
  CONF_ID          INT          -- Confirmation ID (FK to CFCTRL_CONF)
  ROLE_CD          VARCHAR      -- Business party role code
  BP_NO            INT          -- Business party number
  ROLE_QTY         DECIMAL      -- Quantity for this role
```

### Table Relationships

```
CFCTRL_CONF (1) ---> (N) CFCTRL_CONF_HOURLY
    |                       (Hourly profile for each confirmation)
    |
    +---> (N) CFCTRL_CONF_LVL_DTL
    |           (Detail records linking to levels)
    |
    +---> (N) CFCTRL_CONF_ROLE
                (Role-based breakdown)

CFCTRL_CONF_LVL (1) ---> (N) CFCTRL_CONF_LVL_DTL
    |                          (Details within a level)
    |
    +---> (N) CFCTRL_CONF_LVL  (Self-referencing hierarchy via PARENT_LVL_ID)

CFCTRL_CONF_PLAN (standalone)
    (Planned quantities before submission)
```

### Foreign Key References

| From Table | To Table | Join Columns | Description |
|------------|----------|--------------|-------------|
| CFCTRL_CONF | NNCTRL_NOM_HDR | TSP_NO, ID_NOM | Links to nomination |
| CFCTRL_CONF | PACTRL_LOC | ID_REC_LOC / ID_DEL_LOC | Links to locations |
| CFCTRL_CONF | KCTRL_CTR | SR_CTR_NO | Links to contract |
| CFCTRL_CONF_HOURLY | CFCTRL_CONF | TSP_NO, CONF_ID | Links hourly to confirmation |
| CFCTRL_CONF_LVL_DTL | CFCTRL_CONF | TSP_NO, CONF_ID | Links level detail to confirmation |
| CFCTRL_CONF_LVL_DTL | CFCTRL_CONF_LVL | TSP_NO, CONF_LVL_ID | Links detail to level |
| CFCTRL_CONF_ROLE | CFCTRL_CONF | TSP_NO, CONF_ID | Links role to confirmation |

---

## Batch Processing

### CFPROCESS Batch Process

**Process Code**: `CFPROCESS`

**Trigger**: Executed after confirmation submission

**Purpose**: Processes submitted confirmations and updates downstream systems.

**Processing Steps:**
1. Read submitted confirmation records
2. Update confirmation status codes
3. Calculate variance data (NomQty - ConfQty)
4. Update path balancing records
5. Generate EDI confirmation transactions (if configured)
6. Notify downstream systems (allocations, billing)
7. Update process queue status

**Batch Parameters:**
- TSP_NO: TSP number to process
- GAS_DAY: Gas day to process
- ID_CYCLE: Cycle to process

**Error Handling:**
- Errors logged to `tMessage` table with process code `CFPROCESS`
- Failed records do not block other confirmations
- Process can be re-run after error resolution

---

## Configuration Settings

### Key Configuration Parameters

| Setting | Description | Impact |
|---------|-------------|--------|
| `UseSecObjAllowUserMakeCutOnATTLocation` | Controls security for editing confirmations at ATT locations | When enabled, additional security check for making cuts at specific locations |
| `DefaultToOpenConfirmationCycle` | Default cycle selection in UI | When true, automatically selects the next open cycle when opening confirmation screen |
| `ShowPrevCycleDataEnabled` | Show previous cycle data | When true, displays previous cycle confirmation data for reference during current cycle entry |
| `ConfRunPathBalForPnt` | Enable path balancing for points | When true, runs path balancing validation during confirmation submission |
| `ConfUpdCallBalancingAfter` | Trigger balancing recalculation | Controls when balancing is recalculated after confirmation updates |

### Configuration Location

Configuration settings are stored in the system configuration tables and accessed through the QPTM configuration framework. Settings can be TSP-specific or system-wide.

---

## Processing Flow

### Confirmation Entry Flow

```
User Opens Confirmation Response Screen
        |
        v
Load Confirmation Data
  |-- QPTMConfirmationWidgetService.GetFilteredConfirmations()
  |-- Apply ConfirmationsFilterEnum (NextOpenCycle, etc.)
  |-- ApplyNomLatestCycleFilter()
  |-- Load grid with nomination/confirmation data
        |
        v
User Enters Confirmation Quantities
  |-- ConfirmationResponseController.ConfOtherChanges()
  |-- Validate via ValidationEngineConfirmation (4 levels)
  |-- If hourly profile: UpdateHourlyProfileTotal()
  |-- Persist changes to CFCTRL_CONF
        |
        v
User Submits Confirmations
  |-- Final validation pass
  |-- Update CFCTRL_CONF status
  |-- Trigger CFPROCESS batch
  |-- Update confirmation summary
        |
        v
Post-Submission Processing
  |-- CFPROCESS updates downstream
  |-- Variance data calculated
  |-- Path balancing updated
  |-- EDI transactions generated (if applicable)
```

### Summary View Flow

```
User Opens Confirmation Summary Screen
        |
        v
Load Summary Data
  |-- QPTMConfirmationWidgetService.GetSummaryConfirmations()
  |-- Select aggregation view (ByLocation/ByShipper/ByPath)
  |-- Apply cycle and status filters
  |-- Bind to Kendo DataSource grid
        |
        v
User Interacts with Summary
  |-- Sort, filter, page through data
  |-- Export to Excel
  |-- Click navigation links (Lifecycle/NomSubmission/ConfResponse)
  |-- Drill down from summary to detail
```

---

## Integration Points

### Upstream Dependencies

| System | Integration | Description |
|--------|-------------|-------------|
| **Nominations (NOM)** | NNCTRL_NOM_HDR | Confirmation records reference nomination data |
| **CAS** | CACTRL_SUMMARY | Scheduled quantities feed into confirmation as reference values |
| **Contracts (CTR)** | KCTRL_CTR | Contract data for validation and capacity checks |
| **Locations (LOC)** | PACTRL_LOC | Location data for EPSQ values and location contacts |

### Downstream Dependencies

| System | Integration | Description |
|--------|-------------|-------------|
| **Allocations (ALLOC)** | Confirmed quantities | Allocation process uses confirmed quantities as input |
| **Billing (INV)** | Variance data | Billing uses confirmation variance for imbalance charges |
| **EDI** | Confirmation transactions | EDI system sends confirmation data to external parties |
| **Reporting** | Summary data | Reports consume confirmation summary and variance data |

### Cross-Reference to Related Features

- **Nominations**: [../nominations/architecture.md](../nominations/architecture.md) - Upstream nomination processing
- **CAS**: [../capacity-scheduling-allocations/architecture.md](../capacity-scheduling-allocations/architecture.md) - Scheduling that produces SchdQty
- **Domain Concepts**: [domain.md](./domain.md) - Business rules and terminology
- **Troubleshooting**: [troubleshooting.md](./troubleshooting.md) - Common issues and solutions

---

*Last updated: 2026-03-03*
*Document version: 1.0*
