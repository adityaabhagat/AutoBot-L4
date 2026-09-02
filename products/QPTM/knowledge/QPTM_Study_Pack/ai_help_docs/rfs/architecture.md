---
title: Request For Service (RFS) - Technical Architecture
category: architecture
feature: Request For Service (RFS)
related_repos: Web, Batch
keywords: QPTMRFSService, QPTMContractsWidgetService, RFSWizardV2Controller, RFSApprovalController, NewRFSActivityController, RFSHeaderDO, validation rules, RFS_HEADER, RFS_LOCATION, RFS_APPROVAL, rate resolution, award, KRFSTOCTR
last_updated: 2026-03-03
---

# Request For Service (RFS) - Technical Architecture

## Overview

This document describes the **technical implementation** of the RFS feature in the QPTM system. It covers service classes, controllers, data objects, validation rules, database tables, and API endpoints.

For business concepts, see [Domain Documentation](./domain.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [QPTMRFSService - Primary Service](#qptmrfsservice---primary-service)
3. [QPTMContractsWidgetService](#qptmcontractswidgetservice)
4. [Web Controllers](#web-controllers)
5. [Data Objects](#data-objects)
6. [Validation Rules](#validation-rules)
7. [Database Tables](#database-tables)
8. [Caching Architecture](#caching-architecture)
9. [Event and Notification System](#event-and-notification-system)
10. [Configuration System](#configuration-system)
11. [Key Interfaces](#key-interfaces)
12. [Related Documentation](#related-documentation)

---

## Architecture Overview

### Layer Diagram

```
+-----------------------------------------------------------------+
|  Web Layer (MVC Controllers)                                    |
|  +-----------------------------------------------------------+  |
|  | RFSWizardV2Controller   | RFSApprovalController          |  |
|  | NewRFSActivityController | (Widget & Wizard controllers)  |  |
|  +-----------------------------------------------------------+  |
+-----------------------------------------------------------------+
         |                          |
         v                          v
+-----------------------------------------------------------------+
|  UI Controller Layer                                            |
|  +-----------------------------------------------------------+  |
|  | QUIControllerRFSWizardV2 | QUIControllerRFSApproval       |  |
|  | QUIControllerRFSActivity | Workflow States (QState*)       |  |
|  +-----------------------------------------------------------+  |
+-----------------------------------------------------------------+
         |
         v
+-----------------------------------------------------------------+
|  Service Layer                                                  |
|  +-----------------------------------------------------------+  |
|  | QPTMRFSService (5101 lines - primary)                     |  |
|  | QPTMContractsWidgetService                                |  |
|  | QPTMContractService | QPTMRateService | QPTMConfirmation  |  |
|  +-----------------------------------------------------------+  |
+-----------------------------------------------------------------+
         |
         v
+-----------------------------------------------------------------+
|  Data Access Layer                                              |
|  +-----------------------------------------------------------+  |
|  | IQContractDataAccess  | IQPTMDataAccess_RFSHeader         |  |
|  | IQPTMDataAccess_RFSApproval | IQPTMDataAccess_RFSAuction  |  |
|  | IQPTMDataAccess_RFSHeaderRates | IQPTMDataAccess_RFSStatus|  |
|  +-----------------------------------------------------------+  |
+-----------------------------------------------------------------+
         |
         v
+-----------------------------------------------------------------+
|  Validation Layer                                               |
|  +-----------------------------------------------------------+  |
|  | Quorum.QPTM.Validations.Rules.RFS                        |  |
|  | ForeignKeyRules/ | LineRules/ | MandatoryLineRules/       |  |
|  | RFSGeneralRules/ | RFSLocationRules/ | RFSApprovalRules/  |  |
|  +-----------------------------------------------------------+  |
+-----------------------------------------------------------------+
         |
         v
+-----------------------------------------------------------------+
|  Database (SQL Server)                                          |
|  RFS_HEADER | RFS_LOCATION | RFS_APPROVAL | RFS_HEADER_RATES   |
|  RFS_TEXT | RFS_DISCOUNT_RATE | RFS_PAL_* | RFS_CONTACT         |
+-----------------------------------------------------------------+
```

### Project Structure

| Project | Purpose |
|---------|---------|
| `Quorum.QPTM.ServiceCore.RFS` | Business logic service layer |
| `Quorum.QPTM.Web.Core/Controllers` | MVC controllers for web UI |
| `Quorum.QPTM.DataObject` | Data objects (RFSHeaderDO, etc.) |
| `Quorum.QPTM.Validations.Rules.RFS` | Business validation rules |
| `Quorum.QPTM.CoreInterface` | Constants, interfaces, shared types |
| `Quorum.QPTM.DataAccess` | Repository pattern data access |
| `Quorum.QPTM.Events.Contract` | Event detection for notifications |

---

## QPTMRFSService - Primary Service

**File**: `Quorum.QPTM.ServiceCore.RFS/QPTMRFSService.cs` (5101 lines)
**Class**: `QPTMRFSService : QPTMServiceBase, IQPTMRFSService, IQPTMRFSServiceSide`

This is the central service class for all RFS business logic. It handles CRUD operations, validation orchestration, rate resolution, approval management, award processing, and security filtering.

### Constructor and Dependencies

```csharp
public QPTMRFSService(QIMsgLog msgLog, ValidationEngineControl ValidationEngine,
    IRFSApprovalsCacheAccess rfsApprovalsCacheAccess,
    IBACacheAccess baCacheAccess,
    ISecurityUserCacheAccess securityUserCacheAccess,
    IServiceProvider serviceProvider,
    IResolverSecurity resolverSecurity,
    IQPTMGlobalConfigsAccess globalConfigsAccess)
```

Key dependencies:
- `ValidationEngineControl`: Orchestrates validation rule execution
- `IRFSApprovalsCacheAccess`: Cache access for approval department configurations
- `IBACacheAccess`: Business Associate cache
- `ISecurityUserCacheAccess`: Security user cache
- `IResolverSecurity`: Security resolution (BP association, agent authorization)
- `IQPTMGlobalConfigsAccess`: Global configuration settings

### Key Methods - Retrieval

| Method | Lines (approx) | Description |
|--------|:-:|-------------|
| `GetRFSContract(tspNo, rfsNo)` | 432-466 | Retrieves complete RFS with all child data and resolved rates |
| `GetRFSContractData(tspNo, rfsNo)` | (internal) | Core data retrieval without rate resolution |
| `GetRFSContractDataForRange(dtFrom, dtTo)` | 489-520 | Retrieves RFS headers for a date range with security filtering |
| `GetRFSContractForRange(dtFrom, dtTo)` | 930-973 | Full retrieval with extra info and rate resolution |
| `GetRFSListForWeb(dtFrom, dtTo, userID)` | 794-850 | Retrieval for web queue display with status/request type filtering |
| `GetRFSHeaderList(tspNo, dtFrom, dtTo)` | 863-875 | Simple header list retrieval with optional children |
| `GetRFSHeaderQueryData(tspNo, filters)` | 877-893 | Lightweight query data with security check |
| `GetRFSHeaderComplete(tspNo, rfsNo)` | 1607-1626 | Returns RFSHeaderCompleteDO wrapper with full data |
| `GetRFSApprovalQueue(dtFrom, dtTo, userID)` | 679-792 | Retrieves approval queue with BP info, status, and approvals |
| `GetAllLongTermBids(tspNo, effDtFrom)` | 1833-1872 | Long-term bid viewer data with competing bids |

### Key Methods - Modification

| Method | Lines (approx) | Description |
|--------|:-:|-------------|
| `UpdateRFSContract(tspNo, rfsNo, beginDate, endDate, headers)` | 1119-1271 | Saves RFS header, approvals, and auction data in transaction |
| `ValidateRFSContract(header, mandatoryOnly)` | 389-424 | Executes validation rules on RFS data |
| `ExecuteRFSAction(headerComplete, beginDate, endDate, actionCode)` | 1628-1734 | Orchestrates action execution (submit, award, withdraw, etc.) |
| `SubmitRFSApproval(headerDO, apprDeptCode)` | 975-1061 | Submits an approval decision for a department |
| `UpdateRFSApproval(approvalList)` | 1089-1108 | Persists approval record changes |
| `ValidateBeforeAward(headerDO)` | 1063-1087 | Pre-award validation with CTR action code |
| `UpdateCompetingBids(bidsList, effStartDate)` | 1985-2197 | Updates long-term competing bids with rate changes |

### Key Methods - Rate Resolution

| Method | Lines (approx) | Description |
|--------|:-:|-------------|
| `ResolveRate(header, tariffOnly, ovrdDate)` | 2438-2971 | Core rate resolution for header, location, discount, and PAL rates |
| `GetRFSContractFromCtr(header)` | 1330-1404 | Copies contract data to RFS and resolves rates |
| `AddDicountAndNegotiatedRates(header, date, svc, tocList)` | 2973-2995 | Adds discount and negotiated rate records |

### Key Methods - Configuration and Lookup

| Method | Description |
|--------|-------------|
| `GetRFSWorkflowData(tspNo)` | Returns RFS configuration: actions, status/action xrefs, screen config, tab settings |
| `GetRFSConfigData(tspNo)` | Returns RFS config data with actions and status xrefs |
| `GetAllRequestTypes()` | Returns all configured request types from cache |
| `GetTypeOfService(tspNo, tosCodes)` | Returns TOS details for given codes |
| `GetFirstOpenCycle(tspNo, gasDay, requestType)` | Returns the first open nomination cycle |
| `GetApprovalRecords(tspNo, reqType, tos, isNonPreapproved, isCapChange, ref seqNo)` | Builds approval records based on TSP configuration |

### Key Methods - Security

| Method | Description |
|--------|-------------|
| `FilterRfsListForSecurity(unfilteredList)` | Filters RFS list by user TSP and BP authorization |
| `IsUserAuthorizedForRfs(userID, header)` | Checks if user can access specific RFS based on request type |
| `RFSHeaderQueryDataSecurityCheck(tspNo, fullList)` | Performant security check for query data |
| `IsActionAllowed(actionType)` | Checks security object permission for the action |
| `GetBPViewUpdateAgent(tspNo, effDate, out view, out update)` | Gets BP agent lists for view/update authorization |

### Internal Helper Methods

| Method | Description |
|--------|-------------|
| `ValidateData(header, ref setStatusOnFail, validateNonMandatory)` | Two-phase validation: mandatory then non-mandatory |
| `AddApprovalRecords(complete, header)` | Generates approval records at submit time |
| `AddExtraInfo(ref headerList)` | Attaches child data: approvals, PAL data, unsold capacity |
| `SetExtraInfo(headerList)` | Sets request type, TOS, status, BP, and approval info |
| `RemovePathsWithInactiveLocations(header)` | Removes paths with inactive locations (configurable) |
| `UpdateOrigRFSToCPY(header)` | Updates original RFS status on copy forward |
| `CheckUpdateCompeteRoundEndTime(header)` | Updates auction compete round end time |
| `SetAuctionID(header)` | Assigns auction ID for competitive bidding |
| `MarkApprovalsWithProxyInd(approvals)` | Marks proxy approvals |

### Exception Handling Pattern

```csharp
// All public methods follow this pattern:
public ReturnType MethodName(params)
{
    return this.ServiceHelper.Execute(() =>
    {
        try
        {
            // Business logic
        }
        catch (FaultException<QPTMRFSServiceFault> ex)
        {
            throw ex; // Re-throw known faults
        }
        catch (Exception ex)
        {
            throw this.ConvertException<QPTMRFSServiceFault>(ex);
        }
    });
}
```

The `ConvertException<T>` method handles `ValidateFailedException` specially by extracting individual `Issue` objects with severity, table, column, and message details.

---

## QPTMContractsWidgetService

**File**: `Quorum.QPTM.ServiceCore.RFS/QPTMContractsWidgetService.cs` (422 lines)
**Class**: `QPTMContractsWidgetService : QPTMServiceBase, IQPTMContractsWidget`

Provides data for the dashboard widgets showing active contracts and RFS activity.

### Key Methods

| Method | Description |
|--------|-------------|
| `GetActiveContracts(tspNo, asOfDate, filterByBP)` | Returns active contracts for the widget with MDQ, UOM, and facility info |
| `GetRFSActivity(tspNo, asOfDate, filterByBP)` | Returns recent RFS activity for the widget (cached) |
| `GetContractForUser(tspNo, ctrNo, asOfDate)` | Returns a specific contract for the current user |

### RFS Activity Cache

The widget uses `MemoryCache` with configurable expiration:
- Cache key: `TspNo:{tsp},AsOfDate:{date},User:{user},FilterByBPForInternalUser:{flag}`
- Expiration: Configured by `GlobalConfigsAccess.WidgetCacheRfsActivity` (milliseconds)
- Double-checked locking pattern for thread safety

### RFS Activity Filtering Logic

RFS headers are included in the activity widget if:
1. Updated since the cutoff time (`WidgetRecentActivityDays` from TSP config), OR
2. Status is active AND the RFS is effective as of the current date or in the future

---

## Web Controllers

### RFSWizardV2Controller

**File**: `Quorum.QPTM.Web.Core/Controllers/RFSWizardV2Controller.cs`
**Class**: `RFSWizardV2Controller : QPTMWizardV2ControllerBase<QUIControllerRFSWizardV2, RFSWizardMainV2VM>`
**Security**: `[QScreenSecurityObject("QUCRFSWizardScreenV2")]`

The main wizard controller for creating, amending, and querying RFS requests.

**Key Features:**
- Implements the Wizard V2 pattern with start page, step navigation, and end page
- Tab order determined by TSP + TOS configuration
- Dynamic SUBMIT button on last tab when submit action is available
- Pre-transition and post-submission JavaScript hooks

**Wizard Options:**
| Option | Title | Description |
|--------|-------|-------------|
| NEW | Create New Contract | New service request |
| AMEND | Amend an Existing Contract | Amendment request |
| QUERY | Query for an Existing Request | View existing RFS |
| COPYFORWARD | Copy Forward | (Conditional) Copy from denied RFS |

### RFSApprovalController

**File**: `Quorum.QPTM.Web.Core/Controllers/RFSApprovalController.cs`
**Class**: `RFSApprovalController : RFSApprovalControllerBase<QUIControllerRFSApproval, RFSApprovalMainVM>`
**Security**: `[QScreenSecurityObject("QUCRFSApproval")]`

Manages the RFS approval queue workflow with multiple states.

**Workflow States:**
| State Class | View | Description |
|-------------|------|-------------|
| `QStateRFSApprovalQueue` | `_ApprovalQueue` | List of pending RFS requests |
| `QStateRFSApprovalSummary` | `_ApprovalSummary` | RFS detail summary with all tabs |
| `QStateRFSApprovalApprove` | `_ApprovalApprove` | Approve action form |
| `QStateRFSApprovalReject` | `_ApprovalApprove` | Reject action form (shares view) |
| `QStateRFSApprovalAward` | `_ApprovalAward` | Award confirmation |

**Key Actions:**
| Action | Method | Description |
|--------|--------|-------------|
| Refresh | `DoAction("Restart")` | Re-queries the approval queue |
| Award | `DoAwardRFS` | Triggers RFS-to-contract conversion, returns pqid |
| Post Award | `DoPostAwardRFS(pqid)` | Completes award after async processing |
| Auto Approval | `DoAutoApproval(apprDeptCode)` | Approves and optionally awards in one step |
| Approve/Reject | Standard Save | Commits approval decision |

**Grid Endpoints:**
| Endpoint | Data |
|----------|------|
| `GetRFSApprovalQueue` | Approval queue list |
| `GetRFSHeaderRates` | Header-level rates for summary |
| `GetRFSLocations` | Location paths for summary |
| `GetRFSDiscountRates` | Discount/negotiated rates |
| `GetRFSTextRequested/Removed/PreApproved` | Contract text by category |
| `GetRFSContacts` | Contact information |
| `GetRFSPalAction/PalRate` | PAL action dates and rates |
| `GetLocationUnsoldCapacity` | Location unsold capacity |
| `GetZoneUnsoldCapacity` | Zone/group unsold capacity |
| `GetFacilityUnsoldSummary` | Facility unsold capacity |
| `GetInjWthPeriodsSummary` | Injection/withdrawal periods |
| `GetMyRFSApprovals/OtherRFSApprovals` | Approval records split by my/other |

### NewRFSActivityController

**File**: `Quorum.QPTM.Web.Core/Controllers/Personas/Scheduler/NewRFSActivityController.cs`
**Class**: `NewRFSActivityController : QMvcQPTMBaseScreenController<QUIControllerRFSActivity, NewRFSActivityVM>`
**Security**: `[QScreenSecurityObject("QVpNewRFSActivity")]`

Dashboard widget controller for RFS activity display.

**Key Endpoints:**
| Endpoint | Description |
|----------|-------------|
| `GetNewRFSActivity` | Returns RFS activity grid data with navigation URLs |
| `GetNewRFSActivityCounts` | Returns counts: Denied, Awarded, Pending (for widget badges) |

The `ViewRFSURL` is constructed to link to the RFS Wizard V2 with Query action.

---

## Data Objects

### Primary Data Objects

| Class | File | Description |
|-------|------|-------------|
| `RFSHeaderDO` | `DataObject/CodeGen/RFSHeaderDO.cs` | Auto-generated header with all RFS columns |
| `RFSHeaderDO` (partial) | `DataObject/RFSHeaderDOExt.cs` | Extension with business methods |
| `RFSHeaderCompleteDO` | DataObject | Wrapper containing RFSHeader list |
| `RFSLocationDO` | DataObject | Path/location details (receipt/delivery points) |
| `RFSApprovalDO` | DataObject | Approval department records |
| `RFSHeaderRatesDO` | DataObject | Header-level rate records by TOC |
| `RFSDiscountRateDO` | DataObject | Discount/negotiated rate records |
| `RFSTextDO` | DataObject | Contract text records |
| `RFSContactDO` | DataObject | Contact information |
| `RFSPalActionDateQtyDO` | DataObject | PAL action date and quantity records |
| `RFSPalRatesDO` | DataObject | PAL rate records by TOC |
| `RFSPalDealDO` | DataObject | PAL deal information |
| `RFSInjectionWithdrawalDO` | DataObject | Storage injection/withdrawal periods |
| `RFSErrorDO` | DataObject | Validation error records |
| `RFSAuctionDO` | DataObject | Auction information for competitive bidding |
| `RFSLocationUnsoldCapDO` | DataObject | Location unsold capacity |
| `RFSLocationGrpUnsoldCapDO` | DataObject | Location group/zone unsold capacity |
| `RFSFacilityUnsoldCapDO` | DataObject | Facility unsold capacity |

### RFSHeaderDOExt Key Methods

| Method | Description |
|--------|-------------|
| `CopyCtrData(contracts, dtFrom, dtTo, calcMethod)` | Copies contract data into RFS fields |
| `CopyCtrDataTRM(contract, dtFrom, dtTo, calcMethod)` | Special copy for Termination requests |
| `IsCapacityChangeRequested()` | Detects capacity changes between current and requested quantities |
| `UpdateChildListRFSNO(rfsNo, header)` | Propagates RFS number to all child records |
| `UpdateApprovalChildListRFSNO(rfsNo, header)` | Propagates RFS number to approval records |
| `AddRFSRHeaderRate(toc, rate, rateType, max, min, isNew, period)` | Adds header rate record |
| `AddRFSRPALRate(tocDO)` | Adds PAL rate record |
| `GetRFSPresentValues(from, to, annualRate, calcType)` | Calculates present values |
| `AddCurrentText(contractText)` | Adds existing contract text as current text |
| `DeleteRFSHeaderRates()` / `DeleteRFSPalRates()` / `DeleteRFSDiscRates()` | Clears rate collections |

### Supporting Data Objects

| Class | Description |
|-------|-------------|
| `RFSConfigData` | Configuration wrapper: actions, status xrefs, screen config, tabs, rates |
| `RFSActionDO` | Action definition with success/fail status codes, event type, button label |
| `RFSStatusRFSActionXRefDO` | Maps status + request type to available actions |
| `RFSScreenConfigDO` | Screen configuration per TSP |
| `RFSStatusDO` | Status code definitions with IsActive flag |
| `CDRequestTypeDO` | Request type definitions with behavioral flags |
| `RFSApprovalConfigXRefDO` | Approval department configuration with sequence |
| `PAApprovalDeptUserXRefDO` | Maps users to approval departments |
| `RFSLongTermBidVwDO` | Long-term bid view data |
| `RFSLongTermBidVwWrapperDO` | Wrapper for bids + competing bids |
| `KTranRfsCompeteBidsDO` | Competing bid linking records |
| `RFSActivityDO` | Widget display data |
| `RFSHeaderQueryDataDO` | Lightweight query result data |
| `TypeOfServiceRFSTabDO` | Tab visibility configuration per TOS |
| `RFSTabDO` | Tab definition with mandatory flag |

### Enumerations

**File**: `Quorum.QPTM.DataObject/Enumerations.cs`

```csharp
public enum RFSActionType
{
    DNY = 0,   // DENY
    UPD = 1,   // ADD / UPDATE
    VLD = 2,   // VALIDATE
    SUB = 3,   // SUBMIT
    CPY = 4,   // COPY FORWARD
    CTR = 6,   // AWARD
    WTH = 7,   // WITHDRAW
    RES = 8,   // RESUBMIT
    SVO = 9,   // SERVICE ORDER PREVIEW
    CNT = 10   // CONTINUE (Web Wizard)
}

public enum RFSRequestStatus
{
    NEW = 0,   // New request
    UPD = 1    // Amendment
}
```

### RFSWorkflow Static Class

**File**: `Quorum.QPTM.DataObject/RFSWorkflow.cs`

Static workflow helper that manages:
- `ConfigData`: Current RFS configuration data
- `CurrentRequestType`: Active request type
- `CurrentTypeOfService`: Active TOS
- `GetActiveActions(reqType, isInternal, status, copyFwd)`: Returns available actions for the current state
- `GetRFSActionDO(actionType)`: Looks up action definition
- `GetActionSuccessStatus/FailureStatus/EventTypeCD/Name/Object`: Action attribute lookups

---

## Validation Rules

### Project Structure

**Project**: `Quorum.QPTM.Validations.Rules.RFS`

```
Quorum.QPTM.Validations.Rules.RFS/
+-- ForeignKeyRules/        (RuleKFK001 - RuleKFK020)
+-- LineRules/              (RuleK00040 - RuleK09010)
+-- MandatoryLineRules/     (RuleK01000, RuleK01510, RuleK01520, etc.)
+-- RFSGeneralRules/        (RuleK0001)
+-- RFSLocationRules/       (RuleK0003)
+-- RFSApprovalRules/       (RuleK0002)
+-- RSFContactRules/        (RuleK0004)
```

### Validation Rule Base Classes

| Base Class | Purpose |
|------------|---------|
| `ValidationRuleBaseRFS` | General RFS header validation |
| `ValidationRuleBaseRFSLine` | Line-level (child record) validation |
| `ValidationRuleBaseRFSForeignKey` | Foreign key / mandatory field validation |

### Validation Execution

The `ValidationEngineControl` executes rules in two phases:

1. **Mandatory Validation** (`ValidationLevel.ForeignKey`): Always executed on save
   - Foreign key rules (RuleKFK series)
   - Mandatory line rules (RuleK01000, RuleK01510, etc.)
   - Required field checks

2. **Full Validation** (`ValidationLevel.All`): Executed on Submit, Resubmit, and Award
   - All mandatory rules plus line-level business rules
   - Rate validation, date range checks, quantity validations
   - Status-specific rules based on action code

### Key Validation Rule Categories

| Rule Range | Category | Examples |
|------------|----------|---------|
| KFK001-KFK020 | Foreign Key | Valid BP, valid TOS, valid location, valid route |
| K00040-K00415 | General Line | Date range validation, rate bounds, quantity limits |
| K01000-K01050 | Line Mandatory | Required fields per tab/section |
| K01510-K01520 | Mandatory FK | Advanced foreign key with business logic |
| K02000-K02030 | Rate Rules | Rate type validation, tariff bounds |
| K03000-K03030 | Quantity Rules | MDQ consistency, storage quantity rules |
| K04010 | Contract Rules | Contract-specific validation |
| K05000-K05040 | PAL Rules | Park and Lend specific validation |
| K06000-K06080 | Location Rules | Path validation, location group rules |
| K07000-K07010 | Discount Rate | Discount rate validation |
| K08010-K08090 | Text Rules | Contract text validation |
| K09000-K09010 | Approval Rules | Approval completeness validation |

### Validation Error Handling

Validation errors are captured in `RFSErrorDO` objects on the header:
- `ErrorMsg`: Human-readable error message
- `IsOvrd`: Whether the error can be overridden
- `RfsNo`: Associated RFS number

The `ValidateData` helper method implements backup/merge pattern:
```
1. ClearPropertyErrors()
2. BackUpErrorMsgs()
3. Execute mandatory validation
4. If invalid, return false
5. ClearPropertyErrors() + DeleteErrorMsgs()
6. Execute full validation
7. MergeBackUpErrorMsgs() -- re-adds mandatory errors
```

---

## Database Tables

### Core RFS Tables

| Table | Primary Key | Description |
|-------|-------------|-------------|
| `RFS_HEADER` | TspNo, RfsNo, EffDateFrom | Main RFS header record |
| `RFS_LOCATION` | TspNo, RfsNo, EffDateFrom, IdRfsLoc | Path/location records |
| `RFS_APPROVAL` | TspNo, RfsNo, ApprDeptCode | Approval department records |
| `RFS_HEADER_RATES` | TspNo, RfsNo, EffDateFrom, TocCode | Header-level rate records |
| `RFS_DISCOUNT_RATE` | TspNo, RfsNo, EffDateFrom, [composite] | Discount/negotiated rates |
| `RFS_TEXT` | TspNo, RfsNo, [composite] | Contract text records |
| `RFS_CONTACT` | TspNo, RfsNo, [composite] | Contact information |
| `RFS_PAL_ACTION_DATE_QTY` | TspNo, RfsNo, [composite] | PAL action dates/quantities |
| `RFS_PAL_RATES` | TspNo, RfsNo, [composite] | PAL rate records |
| `RFS_PAL_DEAL` | TspNo, RfsNo, [composite] | PAL deal information |
| `RFS_INJECTION_WITHDRAWAL` | TspNo, RfsNo, [composite] | Injection/withdrawal periods |
| `RFS_ERROR` | TspNo, RfsNo, [composite] | Validation errors |
| `RFS_AUCTION` | TspNo, IdAuction | Auction records for competitive bidding |

### Configuration Tables

| Table | Description |
|-------|-------------|
| `RFS_ACTION` | Action definitions (DNY, UPD, VLD, SUB, etc.) |
| `RFS_STATUS` | Status definitions with IsActive flag |
| `RFS_STATUS_RFS_ACTION_XREF` | Maps status + request type to available actions |
| `RFS_SCREEN_CONFIG` | Screen configuration per TSP |
| `RFS_TAB` | Tab definitions with mandatory flag |
| `TYPE_OF_SERVICE_RFS_TAB` | Tab visibility per TOS with order |
| `RFS_APPROVAL_CONFIG_XREF` | Approval department config with sequence |
| `PA_APPROVAL_DEPT_USER_XREF` | User-to-department mapping |
| `CD_REQ_TYPE` | Request type definitions |

### Related Tables

| Table | Description |
|-------|-------------|
| `K_TRAN_RFS_COMPETE_BIDS` | Links competing bids by CompeteId |
| `RFS_LONG_TERM_BID_VW` | View for long-term bid display |
| `TSP_CONFIGURATION_CONTROL` | TSP-level config (INTEREST_RATE, etc.) |
| `GLOBAL_CONFIGURATION_CONTROL` | Global config (RFS_COPY_INACTIVE_LOCATIONS, etc.) |

### Key Filter Constants

The codebase uses `QRFSHeaderConstants.FilterNames` for query filtering:
- `TspNo`, `RfsNo`, `EffDateFrom`, `EffDateTo`
- `RfsStatusCode`, `ReqTypeCode`, `IsCopyFwd`
- `UpdateDate`, `BpNo`, `CtrNo`

---

## Caching Architecture

### Singleton Caches Used by RFS

| Cache Class | Content | Usage |
|-------------|---------|-------|
| `RFSActionCache` | RFS actions, status/action xrefs | Workflow configuration |
| `RFSScreenConfigCache` | Screen configuration per TSP | Tab/field visibility |
| `RFSApprovalsCache` | Approval dept config, dept users | Approval record generation |
| `RequestTypeCache` | Request type definitions | Request type lookups |
| `ContractCache` | TOS, TOC, contract data | Rate resolution, TOS lookups |
| `MetadataCache` | Hidden tab config, mandatory tabs, global config | Tab settings |
| `RateCache` | Rate TOC/process xrefs | Rate resolution |
| `LocationCache` | Location definitions | Inactive location filtering |
| `TspCache` | TSP config settings | Interest rate, TSP preferences |
| `BACache` | Business associate data | BP name lookups |
| `QCodeCache` | Charge basis codes | Rate resolution |
| `AwardAmendmentCache` | Rate form type codes | Location rate resolution |

### Widget Cache

`QPTMContractsWidgetService` implements its own `MemoryCache`:
- **Cache Name**: `RFSActivityWidget`
- **Key Format**: `TspNo:{tsp},AsOfDate:{date},User:{user},FilterByBPForInternalUser:{flag}`
- **Expiration**: Configurable via `GlobalConfigsAccess.WidgetCacheRfsActivity`
- **Thread Safety**: Double-checked locking with `_RFSActivityCacheLock`

---

## Event and Notification System

### Event Contexts

| Context Class | Event Type | Trigger |
|---------------|------------|---------|
| `QPTMRFSActionEventDetectorContext` | Configurable per action | RFS action execution (submit, award, etc.) |
| `QPTMRFSApprovalEventDetectorContext` | `K_RFS_APPR` | Approval submission |

### Notification Methods

```csharp
// Action notification (submit, award, etc.)
SendActionNotification(rfsHeader, eventTypeCd, reqTypeDesc, tosDescr)

// Approval notification (next department in sequence)
SendApprovalNotification(rfsHeader, reqTypeDesc, tosDescr, actnCode, orderNo)
```

### Notification Logic

On approval submission:
1. Check if all approvals at current and prior levels are complete (no PEN records)
2. If any rejection at current/prior levels, send rejection notification to `IsRejectEmail` recipients
3. If all approved, send sequential notification to next `IsSeqEmail` recipients at next order number

---

## Configuration System

### TSP-Level Configuration

| Config Key | Category | Description |
|------------|----------|-------------|
| `INTEREST_RATE` | TSP | Annual interest rate for present value calculations |
| `WidgetRecentActivityDays` | TSP/Global | Number of days for widget activity display |
| `WidgetCacheRfsActivity` | Global | Cache duration in ms for RFS activity widget |

### Global Configuration

| Config Key | Category | Description |
|------------|----------|-------------|
| `RFS_COPY_INACTIVE_LOCATIONS_TO_NEW_REQUEST` | CONTRACTS | Whether to copy inactive locations (0=no, 1=yes) |
| `RFS_AUTO_APPROVE_SEC_USER` | Global | Auto-approve for internal users in approval departments |
| `RFSGetKInfoMethod` | Global | MDQ calculation method: `UseFirstDateMDQ` or `UseMinMDQ` |
| `RfsPresentValueCalcType` | TSP/Global | Calculation type for present value |

---

## Key Interfaces

### Service Interfaces

| Interface | Implementation | Description |
|-----------|----------------|-------------|
| `IQPTMRFSService` | `QPTMRFSService` | Primary RFS service contract |
| `IQPTMRFSServiceSide` | `QPTMRFSService` | Server-side RFS operations |
| `IQPTMContractsWidget` | `QPTMContractsWidgetService` | Widget service contract |

### Data Access Interfaces

| Interface | Description |
|-----------|-------------|
| `IQContractDataAccess` | Contract and RFS data access (GetRFSHeaderList, GetRFSStatuses, etc.) |
| `IQPTMDataAccess_RFSHeader` | RFS header CRUD operations |
| `IQPTMDataAccess_RFSApproval` | RFS approval CRUD operations |
| `IQPTMDataAccess_RFSAuction` | RFS auction CRUD operations |
| `IQPTMDataAccess_RFSHeaderRates` | RFS header rates operations |
| `IQPTMDataAccess_RFSStatus` | RFS status lookup |
| `IQPTMDataAccess_QarchLock` | Record locking for concurrent access |

### Cache Access Interfaces

| Interface | Description |
|-----------|-------------|
| `IRFSApprovalsCacheAccess` | Approval department config and users |
| `IBACacheAccess` | Business associate agent data |
| `ISecurityUserCacheAccess` | Security user BP list |
| `IQPTMGlobalConfigsAccess` | Global configuration settings |
| `IQPTMTspOrGlobalConfigsAccess` | TSP or global configuration |
| `IResolverSecurity` | Security resolution methods |

---

## Related Documentation

- [Domain Documentation](./domain.md) - Business concepts and workflows
- [Troubleshooting Guide](./troubleshooting.md) - Known issues and resolution steps

---

*Last updated: 2026-03-03*

*Document version: 1.0*
