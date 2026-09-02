---
title: Penalties (PEN) - Technical Architecture
category: architecture
feature: Penalties (PEN)
related_repos: Web, Batch
keywords: PEN, penalties, PenaltySubmissionController, PenaltyResultsController, QPTMServiceCore_PenaltySubmission, QPTMAllocationServiceExt_PenaltySchedule, PenaltyIdDO, PenaltyResultsHdrDO, HourlyPenaltyScheduleHeaderDO, BLCTRL_PENALTY, BLTRAN_INVOICE_PENALTY_HDR
last_updated: 2026-03-03
---

# Penalties (PEN) - Technical Architecture

## Overview

This document describes the **technical implementation** of the Penalties (PEN) feature in the QPTM system. It covers service layer methods, controllers, data objects, database tables, validation rules, and integration points.

For business concepts, see [Domain Documentation](./domain.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Service Layer](#service-layer)
3. [Controllers - MVC (Web.Core)](#controllers---mvc-webcore)
4. [UI Controllers](#ui-controllers)
5. [Service Interfaces](#service-interfaces)
6. [Data Objects](#data-objects)
7. [Database Tables](#database-tables)
8. [View Models](#view-models)
9. [Views (Razor)](#views-razor)
10. [Constants and Configuration](#constants-and-configuration)
11. [Data Access Interfaces](#data-access-interfaces)
12. [Validation Rules](#validation-rules)
13. [Integration Points](#integration-points)
14. [Security](#security)
15. [Key Method Reference](#key-method-reference)

---

## Architecture Overview

The Penalties feature follows the standard QPTM layered architecture:

```
Views (.cshtml)
  |
MVC Controllers (Quorum.QPTM.Web.Core/Controllers/)
  |
UI Controllers (Quorum.QPTM.Web.Controllers/UIControllers/)
  |
Service Interfaces (Quorum.QPTM.ServiceInterface/)
  |
Service Core (Quorum.QPTM.ServiceCore/ and Quorum.QPTM.ServiceCore.Allocation/)
  |
Data Access (Quorum.QPTM.DataAccessInterface/ -> Quorum.QPTM.DataAccess/)
  |
Database (SQL Server)
```

### Three Sub-Features

The Penalties feature encompasses three related sub-features:
1. **Penalty Submission** - Define penalties and associate accounts
2. **Penalty Results** - Review and manage calculated penalty records
3. **Hourly Penalty Schedule** - Configure hourly tolerance/penalty parameters

---

## Service Layer

### QPTMServiceCore_PenaltySubmission.cs

**File**: `Quorum.QPTM.ServiceCore/QPTMServiceCore_PenaltySubmission.cs`
**Class**: `QPTMServiceCore` (partial class implementing `IQPTMService_PenaltySubmission`)
**Namespace**: `Quorum.QPTM.ServiceCore`

This is the primary service for penalty submission operations. Key method groups:

#### Account-Penalty Association Filtering

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `FilterAccountsByPenaltyRelation` | `DateTime effDateFrom, short nTspNo, List<InventoryAccountHeaderDO> accountList, string penaltyTypeCode` | `List<InventoryAccountHeaderDO>` | Filters accounts by checking TOC rules, TOS-TOC cross-references, and excluding NCTS TOS. Core filtering logic for determining penalty-eligible accounts. |
| `FilterAccountsByPenaltyRelationStreaming` | `QStreamedMessage` | `QStreamedMessage` | Streaming wrapper for the above method. |

**Filtering algorithm** (in `FilterAccountsByPenaltyRelation`):
1. Gets all TOC codes for the TSP via `IQPTMDataAccess_RTTypeOfCharge`
2. For each TOC, checks `RTTypeOfChargeRule` for matching `PenaltyTypeCode` with `IncludeTypeCode = "I"`
3. For each account, gets its contract to determine the TOS code
4. Excludes accounts with TOS = `NCTS` (hard-coded TEC/LDC exclusion)
5. Checks `RateTosTocRuleXRef` for valid TOS-TOC mappings as of the effective date
6. Returns only accounts with matching TOS-TOC cross-reference entries

#### Penalty Basis Retrieval

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `CheckPenaltyBasis` | `short nTspNo, string penaltyTypeCode` | `string` | Returns the `PenaltyBasisCode` for a given penalty type. Returns `"Error"` if not found. |

#### Delete Penalty Details

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `DeletePenaltyDetails` | `List<PenaltyIdDtlDO> deletedPenaltyDetails` | `bool` | Marks detail records as deleted and persists via data access. |

#### Attach Enrichment Data

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `AttachDivisions` | `short nTspNo, List<InventoryAccountHeaderDO> AccountList` | `List<InventoryAccountHeaderDO>` | Enriches accounts with Division from `ContractUserDefined.UserDef1`. |
| `AttachServiceRequesters` | `short nTspNo, List<InventoryAccountHeaderDO> AccountList` | `List<InventoryAccountHeaderDO>` | Enriches accounts with Business Associate name (`BpNm`) from contract data. |

#### CRUD Operations

| Method | Target DO | Description |
|--------|-----------|-------------|
| `GetMultipleInventoryAccounts` | `InventoryAccountHeaderDO` | Query inventory accounts with filters, sorting, paging |
| `UpdateMultipleInventoryAccounts` | `InventoryAccountHeaderDO` | Persist inventory account changes |
| `GetSinglePenaltySubmission` | `PenaltyIdDO` | Get a single penalty by ID and TSP |
| `GetMultiplePenaltySubmission` | `PenaltyIdDO` | Query penalties with filters |
| `UpdateSinglePenaltySubmission` | `PenaltyIdDO` | Save a single penalty (header + details) |
| `UpdateMultiplePenaltySubmission` | `PenaltyIdDO` | Save multiple penalty records |
| `GetMultiplePenaltyDetails` | `PenaltyIdDtlDO` | Query penalty detail records |
| `UpdateMultiplePenaltyDetails` | `PenaltyIdDtlDO` | Save penalty detail record changes |

**Note**: Validation methods exist in the file but are currently **commented out**. The `ValidateSinglePenaltySubmission` and `ValidateMultiplePenaltySubmission` methods are disabled.

### QPTMAllocationServiceExt_PenaltySchedule.cs

**File**: `Quorum.QPTM.ServiceCore.Allocation/QPTMAllocationServiceExt_PenaltySchedule.cs`
**Class**: `QPTMAllocationService` (partial class)
**Namespace**: `Quorum.QPTM`

Handles hourly penalty schedule CRUD operations through the allocation service.

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `GetHrlyPenaltySchdHeaders` | `short tspNo, int schdID, DateTime effDtFrom, DateTime effDtTo` | `List<HourlyPenaltyScheduleHeaderDO>` | Retrieves hourly penalty schedule headers with detail records. Validates TSP > 0 and SchdId > 0. Sets extra info (gas hour, hour order) from hour profile cache. Sorts by `EffDateFrom`. |
| `UpdateHrlyPenaltySchdHeaders` | `short tspNo, int schdID, DateTime effDtFrom, DateTime effDtTo, List<HourlyPenaltyScheduleHeaderDO> updateHeaderList` | `List<HourlyPenaltyScheduleHeaderDO>` | Saves schedule headers within a `ReadCommitted` transaction. Generates new `SCHD_ID` via `USPG_GETNEXTSEQ` if needed. Re-queries after save to return fresh data. |

**Key implementation details**:
- `SetExtraInfo`: Populates `GasHour` and `HourOrder` on detail records from `CycleCache.GetHourlyProfile`
- `SetProfileInfoFromID`: Maps `HourId` to hour profile data
- New schedule IDs are generated using `QPTMServiceUtility.GetNextSeqHelper` with sequence name `"SCHD_ID"`
- Save operations use `QTransactionScope.CreateTransactionScope` with `TransactionScopeOption.RequiresNew`

---

## Controllers - MVC (Web.Core)

### PenaltySubmissionController

**File**: `Quorum.QPTM.Web.Core/Controllers/PenaltySubmissionController.cs`
**Class**: `PenaltySubmissionController`
**Namespace**: `Quorum.QPTM.Web.Controllers`
**Base Class**: `QMvcQPTMBaseScreenController<QUIControllerPenaltySubmission, PenaltySubmissionRootVM>`
**Security**: `[QScreenSecurityObject("QUCPenaltySubmission")]`

#### Actions

| Action | Description |
|--------|-------------|
| `GetActions` | Returns standard actions (Query, Save, Close, New, Clone) with custom query button text. **Removes the Validate button**. |
| `DoAction("GetAvailableAccounts")` | Maps to "Retrieve" action |
| `DoAction("Retrieve")` | Resets `HasAccounts = false` before retrieval to force refresh |

#### Field Updates

| Endpoint | Method | Description |
|----------|--------|-------------|
| `PenaltySubmissionFieldUpdate` | POST | Handles field changes. Resets `HasAccounts = false` when Penalty ID changes. |

#### Grid Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `AvailableAccountsGetData` | POST | Returns accounts in the Available grid |
| `SelectedAccountsGetData` | POST | Returns accounts in the Selected grid |
| `SelectedAccountAddNewRow` | POST | Moves selected rows from Available to Selected |
| `SelectedAccountDeleteRow` | POST | Moves selected rows from Selected to Available |
| `AvailableAccountsUpdate` | POST | Grid cell update for Available accounts |
| `SelectedAccountsUpdate` | POST | Grid cell update for Selected accounts |
| `AvailableAccountsHeaderSelectedObjectsChanged` | POST | Selection state tracking for Available grid |
| `SelectedAccountsHeaderSelectedObjectsChanged` | POST | Selection state tracking for Selected grid |

### PenaltyResultsController

**File**: `Quorum.QPTM.Web.Core/Controllers/PenaltyResultsController.cs`
**Class**: `PenaltyResultsController`
**Namespace**: `Quorum.QPTM.Web.Controllers`
**Base Class**: `QMvcQPTMBaseScreenController<QUIControllerPenaltyResults, PenaltyResultsRootVM>`
**Security**: `[QScreenSecurityObject(Constants.SecurityObjectIDs.PenaltyResults)]` => `"QVPPENALTYRESULTS"`

#### Actions

| Action | Description |
|--------|-------------|
| `GetActions` | Returns Query, Close, and Save buttons (no New, Clone, or Delete) |
| `DoAction(QStandardActions.More)` | Loads more records |
| `DoAction(QStandardActions.All)` | Loads all records |

#### Grid Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `PenaltyResultsGetData` | POST | Returns penalty result header records |
| `PenaltyResultsUpdate` | POST | Grid cell update |
| `PenaltyResultsAddNewRow` | POST | Add/clone row |
| `PenaltyResultsAddSelectedRow` | POST | Clone selected rows |
| `PenaltyResultsDeleteRow` | POST | Delete a row |
| `PenaltyResultsDeleteSelectedRow` | POST | Delete selected rows |
| `PenaltyResultsHeaderSelectedObjectsChanged` | POST | Selection state tracking |
| `PenaltyResultsExcelExport` | GET | Export to Excel |

#### Popup Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `FormPenaltyDetails` | GET | Opens Penalty Details popup. Sets `SelectedRow` on UIC. Checks for pool details to conditionally show Pool tab. Returns `_PenaltyDetails` partial view. |
| `TierDetails` | GET | Returns `_PenaltyDetails_Tier` partial view |
| `GetPenaltyDetailsTier` | POST | Returns tier detail grid data (child `PenaltyResultsDtlDO` records) |
| `PoolingDetails` | GET | Returns `_PenaltyDetails_Pool` partial view |
| `GetPenaltyDetailsPool` | POST | Returns pool detail grid data (child `PenaltyResultsPoolDtlDO` records) |

#### Energy Context Data

The controller initializes energy context data from `TspPreference.EngUomCode` for unit-of-measure display.

---

## UI Controllers

### QUIControllerPenaltySubmission

**File**: `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerPenaltySubmission.cs`
**Class**: `QUIControllerPenaltySubmission`
**Base Class**: `QPTMInterfaceControllerBase`
**Security**: `[QSecurityObject("QUCPenaltySubmission")]`

#### Do Overrides

| Override | Description |
|----------|-------------|
| `DoQuery` | If `HasAccounts` is true, returns immediately. Validates required params. For Allocations basis, returns after basis check. For Inventory basis: retrieves accounts, attaches service requesters and divisions, filters by penalty relation, splits into Available/Selected lists based on existing `PenaltyIdDtl` records. |
| `DoSave` | Validates required params. For Allocations basis: saves header with LocGrpId. For Inventory basis: deletes detail records for accounts in Available list, adds detail records for accounts in Selected list that don't already exist. Calls `UpdateSinglePenaltySubmission`. |
| `DoValidate` | Currently no-op (validation commented out) |
| `DoNew` | Creates new `PenaltyIdDO`, initializes empty account lists, sets default TSP and current date |
| `DoClone` | Clones the current `PenaltyIdDO` using `CloneAsNew` |

#### Params Class: QControllerParamsPenaltySubmission

| Parameter | Type | Description |
|-----------|------|-------------|
| `PenaltyId` | `string` | Penalty ID (defaults to `Constants.NewIdString` for new) |
| `PenaltyDescr` | `string` | Penalty description |
| `EffDateFrom` | `DateTime?` | Effective date from |
| `EffDateTo` | `DateTime?` | Effective date to |
| `PenaltyTypeCode` | `string` | Penalty type code |
| `LocGrpId` | `string` | Location Group ID (Allocations basis) |
| `LocGrpNm` | `string` | Location Group Name (Allocations basis) |
| `PenaltyBasisCode` | `string` | Cached penalty basis code |
| `HasAccounts` | `bool` | Whether accounts have been loaded |
| `AvailableAccountsList` | `List<InventoryAccountHeaderDO>` | Accounts available for selection |
| `SelectedAccountsList` | `List<InventoryAccountHeaderDO>` | Accounts currently associated |

### QUIControllerPenaltyResults

**File**: `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerPenaltyResults.cs`
**Class**: `QUIControllerPenaltyResults`
**Base Class**: `QPTMBulkInterfaceControllerBase<PenaltyResultsHdrDO>`
**Security**: `[QSecurityObject(Constants.SecurityObjectIDs.PenaltyResults)]`

#### Do Overrides

| Override | Description |
|----------|-------------|
| `DoQuery` | Validates TSP > 0. Builds filter list from params (TSP, AcctgMth, ProdMth, CtrNo, Unapproved, Unprocessed). Calls `Service.GetMultiplePenaltyResults`. Uses `BulkContainer.Items`. |
| `DoNew` | Sets default TSP, defaults AcctgMth and ProdMth to current date |
| `DoSave` | Calls `Service.UpdateMultiplePenaltyResults` with `BulkContainer.Items` |

#### Params Class: QControllerParamsPenaltyResults

| Parameter | Type | Description |
|-----------|------|-------------|
| `AcctgMth` | `DateTime?` | Accounting month filter |
| `ProdMth` | `DateTime?` | Production month filter |
| `CtrNo` | `string` | Contract number filter |
| `UnapprovedRecordsOption` | `bool` | Filter for unapproved records |
| `UnprocessedRecordsOption` | `bool` | Filter for unprocessed records |

#### Additional Properties

- `SelectedRow`: Stores the ObjectID of the currently selected row for popup detail retrieval

### QUIControllerHourlyPenaltySchedule

**File**: `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerHourlyPenaltySchedule.cs`
**Class**: `QUIControllerHourlyPenaltySchedule`
**Base Class**: `QPTMEffectiveDatedInterfaceControllerBase`
**Security**: `[QScreenSecurityObject(Constants.SecurityObjectIDs.HourlyPenaltySchedule)]` => `"QVPSOAHOURLYPENALTYSCHEDULE"`
**Implements**: `IQVersionableObject<QUIControllerHourlyPenaltySchedule>`

#### Key Behaviors

- Supports effective dating with `IQEffectiveDated` pattern
- `DoQuery`: Retrieves schedule via `AllocationService.GetHrlyPenaltySchdHeaders`, sets `HourlyPenaltyScheduleHeader` to the matching effective date version
- `DoSave`: Validates via `Service.ValidateSingleHourlyPenaltyScheduleComplete`, then updates via `AllocationService.UpdateHrlyPenaltySchdHeaders`. Notifies QIC service of changes.
- `PreSave`: Calls `ClearToleranceFields` to clear irrelevant tolerance mode fields
- `DoNew`: Builds default 24-hour schedule from `ConfirmationService.GetHourlyProfile`
- `DoClone`: Clones the complete DO, removes all headers except the current effective-dated item
- `ValidateBeforeSave`: Checks if effective date was changed for an existing record

---

## Service Interfaces

### IQPTMService_PenaltySubmission

**File**: `Quorum.QPTM.ServiceInterface/IQPTMServiceInterface_PenaltySubmission.cs`

WCF service contract for penalty submission operations. All methods have both direct and streaming variants.

Key operations:
- `FilterAccountsByPenaltyRelation`, `CheckPenaltyBasis`, `DeletePenaltyDetails`
- `AttachDivisions`, `AttachServiceRequesters`
- CRUD: `GetSingle/GetMultiple/UpdateSingle/UpdateMultiple` for `PenaltyIdDO`, `PenaltyIdDtlDO`, `InventoryAccountHeaderDO`
- Validation methods are **commented out**

### IQPTMService_PenaltyResults

**File**: `Quorum.QPTM.ServiceInterface/IQPTMServiceInterface_PenaltyResults.cs`

WCF service contract for penalty results operations:
- `GetSinglePenaltyResults` / `GetMultiplePenaltyResults`
- `UpdateSinglePenaltyResults` / `UpdateMultiplePenaltyResults`
- `ValidateSinglePenaltyResults` / `ValidateMultiplePenaltyResults`

### IQPTMService_HourlyPenaltySchedule

**File**: `Quorum.QPTM.ServiceInterface/IQPTMServiceInterface_HourlyPenaltySchedule.cs`

WCF service contract for hourly penalty schedule operations:
- CRUD for `HourlyPenaltyScheduleHeaderDO`
- CRUD for `HourlyPenaltyScheduleCompleteDO` (composite with headers)
- Validation for both header and complete objects
- Complete object supports effective dating with `AsOfDate` parameter

All three interfaces are composed into the main `IQPTMService` via partial interface declarations.

---

## Data Objects

### Penalty Submission Data Objects

| Data Object | Table | Primary Key | Description |
|-------------|-------|-------------|-------------|
| `PenaltyIdDO` | `BLCTRL_PENALTY` | `PenaltyId, TspNo` | Penalty definition header. Implements `IQEffectiveDated`. Parent of `PenaltyIdDtlDO` child list. |
| `PenaltyIdDtlDO` | `BLCTRL_PENALTY_DTL` | `PenaltyDtlId` | Penalty detail - links penalty to an inventory account via `InvAcctId`. |

### Penalty Results Data Objects

| Data Object | Table | Primary Key | Description |
|-------------|-------|-------------|-------------|
| `PenaltyResultsHdrDO` | `BLTRAN_INVOICE_PENALTY_HDR` | `InvoicePenaltyId, TspNo` | Calculated penalty result header. Parent of two child lists: `PenaltyResultsDtl` and `PenaltyResultsPoolDtl`. |
| `PenaltyResultsDtlDO` | `BLTRAN_INVOICE_PENALTY_DTL` | `InvoicePenaltyId, TspNo, InvoicePenaltyDtlId` | Tier detail for penalty results. Extended with `TierDtlDescr` property. |
| `PenaltyResultsPoolDtlDO` | `BLTRAN_INVOICE_PENALTY_POOLDTL` | `InvoicePenaltyId, TspNo, PoolSeqNo` | Pool detail for penalty results. |

### Hourly Penalty Schedule Data Objects

| Data Object | Table | Primary Key | Description |
|-------------|-------|-------------|-------------|
| `HourlyPenaltyScheduleCompleteDO` | (composite) | `SchdId, TspNo` | Complete schedule container. Parent of `HourlyPenaltyScheduleHeader` list. |
| `HourlyPenaltyScheduleHeaderDO` | `KCTRL_HRLY_PENALTY_SCHD_HDR` | `TspNo, SchdId, EffDateFrom` | Schedule header with effective dating. Parent of `HourlyPenaltyScheduleDetail` list. |
| `HourlyPenaltyScheduleDetailDO` | `KCTRL_HRLY_PENALTY_SCHD_DTL` | `TspNo, SchdId, EffDateFrom, HourId` | Hour-level tolerance configuration. |

### DOExt Extensions

| File | Extension Properties |
|------|---------------------|
| `PenaltyResultsHdrDOExt.cs` | Adds `BpNm` (Business Partner Name) property |
| `PenaltyResultsDtlDOExt.cs` | Adds `TierDtlDescr` (Tier Detail Description) property |
| `HourlyPenaltyScheduleDetailDOExt.cs` | Extended properties for schedule detail display |
| `HourlyPenaltyScheduleHeaderDOExt.cs` | Extended properties for schedule header |

### Supporting Data Objects

| Data Object | Table | Usage |
|-------------|-------|-------|
| `PenaltyTypeDO` | `QCODE_PENALTY_TYPE` | Code table for penalty types (PK: `PenaltyTypeCode, TspNo`) |
| `InventoryAccountHeaderDO` | (Inventory Account) | Account records used in penalty submission |
| `ContractDO` | (Contract table) | Used for TOS lookup during account filtering |
| `RTTypeOfChargeDO` | (TOC table) | Type of Charge records |
| `RTTypeOfChargeRuleDO` | (TOC Rule table) | Rules linking TOC to penalty types |
| `RateTosTocRuleXRefDO` | (TOS-TOC XRef table) | Cross-reference for TOS-TOC rule matching |
| `ContractUserDefinedDO` | (Contract UDF table) | Provides Division via `UserDef1` |
| `BusinessAssociateDO` | (BA table) | Business Associate/Service Requester names |
| `HourProfileDO` | (Hour Profile table) | Hour profile for gas day schedule |
| `HourlyPenaltyTypeDO` | (Hourly Penalty Type code table) | Code table for hourly penalty type codes |

---

## Database Tables

### Core Tables

| Table Name | Type | Description |
|------------|------|-------------|
| `BLCTRL_PENALTY` | Control | Penalty header definitions (PenaltyId, TspNo, PenaltyTypeCode, EffDateFrom, EffDateTo, PenaltyDescr, LocGrpId) |
| `BLCTRL_PENALTY_DTL` | Control | Penalty detail linking to inventory accounts (PenaltyDtlId, PenaltyId, InvAcctId, TspNo) |
| `BLTRAN_INVOICE_PENALTY_HDR` | Transaction | Calculated penalty results header with all quantities, rates, and amounts |
| `BLTRAN_INVOICE_PENALTY_DTL` | Transaction | Penalty results tier detail breakdown |
| `BLTRAN_INVOICE_PENALTY_POOLDTL` | Transaction | Penalty results pool detail breakdown |
| `KCTRL_HRLY_PENALTY_SCHD_HDR` | Control | Hourly penalty schedule header with effective dating |
| `KCTRL_HRLY_PENALTY_SCHD_DTL` | Control | Hourly penalty schedule detail (one row per hour per schedule version) |

### Code Tables

| Table Name | Description |
|------------|-------------|
| `QCODE_PENALTY_TYPE` | Penalty type code table (PenaltyTypeCode, TspNo, PenaltyBasisCode) |

### Referenced Tables

| Table Name | Usage in Penalties |
|------------|-------------------|
| Contract table | TOS code lookup for account filtering |
| `ContractUserDefined` table | Division assignment (UserDef1) |
| `BusinessAssociate` table | Service requester name lookup |
| `RTTypeOfCharge` table | TOC codes for TSP |
| `RTTypeOfChargeRule` table | TOC-Penalty Type rule matching |
| `RateTosTocRuleXRef` table | TOS-TOC rule cross-reference for effective date filtering |
| `InventoryAccountHeader` table | Inventory accounts for penalty association |

---

## View Models

### Root View Models

| View Model | File | Description |
|------------|------|-------------|
| `PenaltySubmissionRootVM` | `Web.Core/ViewModels/PenaltySubmissionRootVM.cs` | Header fields for Penalty Submission screen. Includes `AvailableAccountsList`, `SelectedAccountsList`, `PenaltyBasisCode`, `HasAccounts`. |
| `PenaltyResultsRootVM` | `Web.Core/ViewModels/PenaltyResultsRootVM.cs` | Header/filter fields for Penalty Results screen. Includes all `BLTRAN_INVOICE_PENALTY_HDR` columns plus `UnapprovedRecordsOption` and `UnprocessedRecordsOption`. |
| `HourlyPenaltyScheduleRootVM` | `Web.Core/ViewModels/HourlyPenaltyScheduleRootVM.cs` | Header fields for Hourly Penalty Schedule screen. |

### Grid/Detail View Models (CodeGen)

| View Model | File | Description |
|------------|------|-------------|
| `PenaltyIdVM` | `Web.Core/ViewModels/CodeGen/PenaltyIdVM.cs` | ViewModel for PenaltyIdDO |
| `PenaltyIdDtlVM` | `Web.Core/ViewModels/CodeGen/PenaltyIdDtlVM.cs` | ViewModel for PenaltyIdDtlDO |
| `PenaltyResultsHdrVM` | `Web.Core/ViewModels/CodeGen/PenaltyResultsHdrVM.cs` | ViewModel for PenaltyResultsHdrDO |
| `PenaltyResultsDtlVM` | `Web.Core/ViewModels/CodeGen/PenaltyResultsDtlVM.cs` | ViewModel for PenaltyResultsDtlDO |
| `PenaltyResultsPoolDtlVM` | `Web.Core/ViewModels/CodeGen/PenaltyResultsPoolDtlVM.cs` | ViewModel for PenaltyResultsPoolDtlDO |
| `PenaltyTypeVM` | `Web.Core/ViewModels/CodeGen/PenaltyTypeVM.cs` | ViewModel for PenaltyTypeDO |
| `HourlyPenaltyScheduleHeaderVM` | `Web.Core/ViewModels/CodeGen/HourlyPenaltyScheduleHeaderVM.cs` | ViewModel for schedule header |
| `HourlyPenaltyScheduleDetailVM` | `Web.Core/ViewModels/CodeGen/HourlyPenaltyScheduleDetailVM.cs` | ViewModel for schedule detail |
| `HourlyPenaltyScheduleCompleteVM` | `Web.Core/ViewModels/CodeGen/HourlyPenaltyScheduleCompleteVM.cs` | ViewModel for complete schedule |
| `HourlyPenaltyTypeVM` | `Web.Core/ViewModels/CodeGen/HourlyPenaltyTypeVM.cs` | ViewModel for hourly penalty type |

### Ext View Models

| View Model | File | Description |
|------------|------|-------------|
| `PenaltyResultsHdrVMExt.cs` | `Web.Core/ViewModels/PenaltyResultsHdrVMExt.cs` | Extensions for penalty results header VM |
| `PenaltyResultsDtlVMExt.cs` | `Web.Core/ViewModels/PenaltyResultsDtlVMExt.cs` | Extensions for penalty results detail VM |
| `HourlyPenaltyScheduleDetailVMExt.cs` | `Web.Core/ViewModels/HourlyPenaltyScheduleDetailVMExt.cs` | Extensions for schedule detail VM |
| `InventoryAccountHeaderVM` | (CodeGen) | Used for Available/Selected account grids on submission screen |

---

## Views (Razor)

| View File | URL Path | Description |
|-----------|----------|-------------|
| `Views/PenaltySubmission/PenaltySubmission.cshtml` | `/PenaltySubmission` | Main Penalty Submission screen |
| `Views/PenaltyResults/PenaltyResults.cshtml` | `/PenaltyResults` | Main Penalty Results screen |
| `Views/PenaltyResults/_PenaltyDetails.cshtml` | (popup) | Penalty Details popup container |
| `Views/PenaltyResults/_PenaltyDetails_Tier.cshtml` | (tab) | Tier Details tab in popup |
| `Views/PenaltyResults/_PenaltyDetails_Pool.cshtml` | (tab) | Pool Details tab in popup |
| `Views/HourlyPenaltySchedule/HourlyPenaltySchedule.cshtml` | `/HourlyPenaltySchedule` | Hourly Penalty Schedule screen |

---

## Constants and Configuration

### Security Object IDs

| Constant | Value | Screen |
|----------|-------|--------|
| `Constants.SecurityObjectIDs.PenaltyResults` | `"QVPPENALTYRESULTS"` | Penalty Results |
| `Constants.SecurityObjectIDs.HourlyPenaltySchedule` | `"QVPSOAHOURLYPENALTYSCHEDULE"` | Hourly Penalty Schedule |
| `"QUCPenaltySubmission"` | (literal) | Penalty Submission |

### Grid IDs

| Constant | Value | Grid |
|----------|-------|------|
| `Constants.GridIDs.PenaltyResults` | `"PenaltyResults"` | Penalty Results main grid |
| `Constants.GridIDs.PenaltyResultsTierDetails` | `"PentaltyDetailsTierGrid"` | Tier details grid |
| `Constants.GridIDs.PenaltyResultsPoolDetails` | `"PentaltyDetailsPoolGrid"` | Pool details grid |
| `Constants.GridIDs.PenaltySubmissionAvailableAccounts` | `"AvailableAccounts"` | Available accounts grid |
| `Constants.GridIDs.PenaltySubmissionSelectedAccounts` | `"SelectedAccounts"` | Selected accounts grid |

### Penalty Basis Codes

| Constant | Value | Description |
|----------|-------|-------------|
| `Constants.PenaltyBasisCode.Allocations` | `"AL"` | Allocation-based penalties |
| `Constants.PenaltyBasisCode.Inventory` | `"IN"` | Inventory-based penalties |

### Penalty Type Codes

| Constant | Value | Description |
|----------|-------|-------------|
| `Constants.PenaltyTypeCode.ImbalancePooling` | `"IMP"` | Imbalance Pooling |
| `Constants.PenaltyTypeCode.CriticalPeriodDelivery` | `"CPD"` | Critical Period Delivery |
| `Constants.PenaltyTypeCode.CriticalPeriodReceipt` | `"CPR"` | Critical Period Receipt |

### Hourly Penalty Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `Constants.HourlyPenaltyTypeCode.Discrete` | `"D"` | Discrete tolerance mode |
| `Constants.HourlyPenaltyTypeCode.Percent` | `"P"` | Percent tolerance mode |
| `Constants.HourlyPenaltyConstant.Hours` | `24` | Expected number of hours in a schedule |

### Pick List IDs

| Constant | Value | Usage |
|----------|-------|-------|
| `Constants.PickListIds.PenaltyResultsContractPick` | `27844` | Contract pick list for Penalty Results |
| `Constants.PickListIds.PenaltySubmissionPenaltyPick` | `27845` | Penalty ID pick list |
| `Constants.PickListIds.PenaltySubmissionLocGrpPick` | `27846` | Location Group pick list |
| `Constants.PickListIds.HourlyPenaltyScheduleIdPick` | `27842` | Schedule ID pick list |

### Metadata Grid IDs

| Constant | Value | Usage |
|----------|-------|-------|
| `Constants.MetadataGridIds.PenaltyResults` | `27852` | Penalty Results metadata |
| `Constants.MetadataGridIds.PenaltyResultsTierDetails` | `27853` | Tier Details metadata |
| `Constants.MetadataGridIds.PenaltyResultsPoolDetails` | `27854` | Pool Details metadata |
| `Constants.MetadataGridIds.PenaltySubmission` | `27855` | Penalty Submission metadata |
| `Constants.MetadataGridIds.HourlyPenaltyScheduleDetailGridId` | `27844` | Hourly Schedule Detail metadata |

---

## Data Access Interfaces

| Interface | DO | Description |
|-----------|-----|-------------|
| `IQPTMDataAccess_PenaltyId` | `PenaltyIdDO` | CRUD for penalty headers |
| `IQPTMDataAccess_PenaltyIdDtl` | `PenaltyIdDtlDO` | CRUD for penalty details |
| `IQPTMDataAccess_PenaltyType` | `PenaltyTypeDO` | Query penalty type codes |
| `IQPTMDataAccess_InventoryAccountHeader` | `InventoryAccountHeaderDO` | Query/update inventory accounts |
| `IQPTMDataAccess_RTTypeOfCharge` | `RTTypeOfChargeDO` | Query TOC codes |
| `IQPTMDataAccess_RTTypeOfChargeRule` | `RTTypeOfChargeRuleDO` | Query TOC rules |
| `IQPTMDataAccess_RateTosTocRuleXRef` | `RateTosTocRuleXRefDO` | Query TOS-TOC cross-references |
| `IQPTMDataAccess_ContractUserDefined` | `ContractUserDefinedDO` | Query contract user-defined fields |
| `IQPTMDataAccess_BusinessAssociate` | `BusinessAssociateDO` | Query business associate records |
| `IQContractDataAccess` | `ContractDO` | Query contract records |

---

## Validation Rules

### Penalty Submission Validation

Validation for Penalty Submission is currently **commented out** in the codebase. The validation infrastructure exists (`QPenaltySubmissionValidationContext` reference, `ValidateSinglePenaltySubmissionInternal`, `ValidateMultiplePenaltySubmissionInternal`) but all methods are disabled.

The `PenaltySubmissionController.GetActions` method explicitly **removes the Validate button** from the UI.

### Penalty Results Validation

Active validation exists for Penalty Results via:
- `IQPTMService_PenaltyResults.ValidateSinglePenaltyResults`
- `IQPTMService_PenaltyResults.ValidateMultiplePenaltyResults`

### Hourly Penalty Schedule Validation

Active validation exists via:
- `IQPTMService_HourlyPenaltySchedule.ValidateSingleHourlyPenaltyScheduleComplete`
- Called explicitly in `QUIControllerHourlyPenaltySchedule.DoSave` before persistence
- Also called in `DoValidate`

### Controller-Level Validation

The `QUIControllerPenaltySubmission` performs inline validation:
- Required params check in `DoQuery`: `EffDateFrom`, `TspNo`, `PenaltyTypeCode`
- Required params check in `DoSave`: `EffDateFrom`, `TspNo`, `PenaltyDescr`, `PenaltyTypeCode`
- `AddAlertOnSave`: For Allocations basis, validates `LocGrpId` and `LocGrpNm` are present
- Error messages added via `QMsgLog.GlobalInstance.AddErrorMsg` or `QUserException`

---

## Integration Points

### Allocation Service

The Hourly Penalty Schedule controller uses `IQPTMAllocationService` for:
- `GetHrlyPenaltySchdHeaders` - retrieve schedules
- `UpdateHrlyPenaltySchdHeaders` - persist schedules

### Confirmation Service

The Hourly Penalty Schedule controller uses `IQPTMConfirmationService` for:
- `GetHourlyProfile` - retrieve the TSP's 24-hour gas day profile

### QIC Service (Integration Change Notifications)

The Hourly Penalty Schedule controller uses `IQICService` for:
- `NotifyOfChange` - sends screen change notifications after save

### Batch Processing

Penalty results (`BLTRAN_INVOICE_PENALTY_HDR`) are generated by batch processes in the `Quorum.QPTM.Batch` repository. The web application provides the review/approval/management interface.

### Invoice Processing

Penalty results link to invoice processing via:
- `ProcessQueueId` / `ProcessStepQueueId` fields
- `IsProc` flag indicates processing status
- `RateResInputId` references rate resolution

### Previously Posted Allocations (PPA)

- `PpaSrcCode` on penalty results tracks PPA source
- `Constants.PpaSourceCode.PenaltyPoolingAllocatedReceipts` = `"PPAR"`

---

## Security

| Screen | Security Object | Controller Attribute |
|--------|-----------------|---------------------|
| Penalty Submission | `QUCPenaltySubmission` | `[QScreenSecurityObject("QUCPenaltySubmission")]` on MVC controller, `[QSecurityObject("QUCPenaltySubmission")]` on UI controller |
| Penalty Results | `QVPPENALTYRESULTS` | `[QScreenSecurityObject(Constants.SecurityObjectIDs.PenaltyResults)]` |
| Hourly Penalty Schedule | `QVPSOAHOURLYPENALTYSCHEDULE` | `[QScreenSecurityObject(Constants.SecurityObjectIDs.HourlyPenaltySchedule)]` |

---

## Key Method Reference

### Quick Lookup: Where to Find Code for Common Operations

| Operation | File | Method |
|-----------|------|--------|
| Filter accounts by penalty eligibility | `QPTMServiceCore_PenaltySubmission.cs` | `FilterAccountsByPenaltyRelation` |
| Check if penalty is AL or IN basis | `QPTMServiceCore_PenaltySubmission.cs` | `CheckPenaltyBasis` |
| Save penalty submission with accounts | `QUIControllerPenaltySubmission.cs` | `DoSave` |
| Query penalty results with filters | `QUIControllerPenaltyResults.cs` | `DoQuery` |
| Save penalty results (approve/process) | `QUIControllerPenaltyResults.cs` | `DoSave` |
| Open penalty details popup | `PenaltyResultsController.cs` | `FormPenaltyDetails` |
| Get tier detail data | `PenaltyResultsController.cs` | `GetPenaltyDetailsTier` |
| Get pool detail data | `PenaltyResultsController.cs` | `GetPenaltyDetailsPool` |
| Export penalty results to Excel | `PenaltyResultsController.cs` | `PenaltyResultsExcelExport` |
| Retrieve hourly penalty schedules | `QPTMAllocationServiceExt_PenaltySchedule.cs` | `GetHrlyPenaltySchdHeaders` |
| Save hourly penalty schedules | `QPTMAllocationServiceExt_PenaltySchedule.cs` | `UpdateHrlyPenaltySchdHeaders` |
| Build default 24-hour schedule | `QUIControllerHourlyPenaltySchedule.cs` | `BuildDefaultSchedule` |
| Clear tolerance fields by type | `QUIControllerHourlyPenaltySchedule.cs` | `ClearToleranceFields` |
| Attach division to accounts | `QPTMServiceCore_PenaltySubmission.cs` | `AttachDivisions` |
| Attach service requester names | `QPTMServiceCore_PenaltySubmission.cs` | `AttachServiceRequesters` |

---

*Last updated: 2026-03-03*

*Document version: 1.0*
