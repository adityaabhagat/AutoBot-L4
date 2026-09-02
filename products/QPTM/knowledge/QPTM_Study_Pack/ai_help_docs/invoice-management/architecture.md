---
title: "Invoice Management (INVC) - Architecture"
category: "architecture"
feature: "INVC"
related_repos:
  - "Quorum.QPTM.Web"
  - "Quorum.QPTM.Batch"
keywords:
  - invoice
  - billing
  - invoice maintenance
  - service core
  - controller
  - API
  - data access
  - data object
  - validation
  - FillSubDetails
  - invoice group
  - batch process
  - BLROLLPER
  - BLRX00
last_updated: 2026-03-03
---

# Invoice Management (INVC) - Architecture

## Table of Contents

- [Overview](#overview)
- [Layer Architecture](#layer-architecture)
- [Service Layer](#service-layer)
  - [Service Interface](#service-interface)
  - [QPTMServiceCore_InvoiceMaintenance](#qptmservicecore_invoicemaintenance)
  - [InvoiceMaintenance_FillSubDetails](#invoicemaintenance_fillsubdetails)
  - [InvoicesAPIService](#invoicesapiservice)
- [Controller Layer](#controller-layer)
  - [QUIControllerInvoiceMaintenance (UI Controller)](#quicontrollerinvoicemaintenance-ui-controller)
  - [InvoiceMaintenanceController (MVC Controller)](#invoicemaintenancecontroller-mvc-controller)
  - [InvoicesController (API Controller)](#invoicescontroller-api-controller)
- [Data Objects](#data-objects)
- [Database Tables](#database-tables)
- [Validation Rules](#validation-rules)
- [FillSubDetails Algorithm](#fillsubdetails-algorithm)
- [Query Flow](#query-flow)
- [Save Flow](#save-flow)
- [API Endpoints](#api-endpoints)
- [Configuration Settings](#configuration-settings)
- [View Models and UI Tabs](#view-models-and-ui-tabs)
- [Key File Locations](#key-file-locations)
- [Related Documentation](#related-documentation)

---

## Overview

The Invoice Management feature follows QPTM's standard layered architecture pattern: MVC/API Controllers delegate to a UI Controller, which calls Service Layer methods, which interact with the Data Access layer using the repository pattern. The feature includes a separate REST API for external integrations alongside the standard web MVC interface.

---

## Layer Architecture

```
+-------------------------------------------------------------------+
|  Web Layer                                                         |
|  +-------------------------------------------------------------+  |
|  | InvoiceMaintenanceController.cs (MVC - Quorum.QPTM.Web.Core)|  |
|  | InvoicesController.cs (API - Quorum.QPTM.Web.Controllers)   |  |
|  +-------------------------------------------------------------+  |
+-------------------------------------------------------------------+
           |                                    |
           v                                    v
+----------------------------+    +---------------------------+
| UI Controller              |    | API Service               |
| QUIControllerInvoice-      |    | InvoicesAPIService.cs     |
| Maintenance.cs             |    | (Web.Controllers/         |
| (Web.Controllers/          |    |  APIService/)             |
|  UIControllers/)           |    +---------------------------+
+----------------------------+               |
           |                                 v
           v                    +---------------------------+
+----------------------------+  | IQPTMInvoiceSummaryWidget |
| Service Layer              |  | IQPTMAllocationService   |
| QPTMServiceCore_Invoice-   |  +---------------------------+
| Maintenance.cs             |
| (Quorum.QPTM.ServiceCore) |
+----------------------------+
           |
           v
+----------------------------+    +---------------------------+
| InvoiceMaintenance_        |    | Validation Layer          |
| FillSubDetails.cs          |    | QPTMValidation*           |
| (ServiceCore/              |    | (Quorum.QPTM.Validations)|
|  QPTMServiceCore_Invoice-  |    +---------------------------+
|  Maintenance/)             |
+----------------------------+
           |
           v
+----------------------------+
| Data Access Layer          |
| IQPTMDataAccess_*          |
| (Quorum.QPTM.DataAccess)  |
+----------------------------+
           |
           v
+----------------------------+
| Data Objects               |
| BillingInvoice*DO(Ext).cs  |
| InvoiceMaintenanceData     |
| (Quorum.QPTM.DataObject)  |
+----------------------------+
```

---

## Service Layer

### Service Interface

The service interface `IQPTMService_InvoiceMaintenance` defines the contract for invoice maintenance operations. It is implemented by the partial class `QPTMServiceCore`.

### QPTMServiceCore_InvoiceMaintenance

**File**: `Quorum.QPTM.ServiceCore/QPTMServiceCore_InvoiceMaintenance.cs` (~846 lines)

This is the primary service file implementing all invoice maintenance business logic as a partial class of `QPTMServiceCore`.

#### Key Methods

| Method | Purpose |
|--------|---------|
| `GetSingleInvoiceMaintenanceStreaming` | Streaming wrapper for `GetSingleInvoiceMaintenance` |
| `GetInvoiceMaintenanceDetailsStreaming` | Streaming wrapper for `GetInvoiceMaintenanceDetails` |
| `GetSingleInvoiceMaintenance` | Main query method - retrieves headers, fills all tabs, handles external user filtering |
| `GetInvoiceMaintenanceDetails` | Retrieves and fills detail, sub-detail by TOC, and sub-detail data for given headers |
| `UpdateSingleInvoiceMaintenanceStreaming` | Streaming wrapper for `UpdateSingleInvoiceMaintenance` |
| `UpdateSingleInvoiceMaintenance` | Main save method - validates, launches batch, saves headers/details, post-update cascades |
| `ValidateSingleInvoiceMaintenance` | Entry point for validation |
| `AddAdditionalPropertiesInvoiceMaintenanceHeader` | Fills headers with extended props (IsOpen flag, contract data for external users) |
| `FillHeader` | Filters headers for external users based on contract agent chain |
| `FillHeaderByContract` | Joins headers with `BLRPTS_10_INVOICE_DOC_SUM` for Header by Contract tab |
| `FillDetails` | Filters detail records for external users |
| `FillSubDetailsByTos` | Aggregates sub-details by TOC grouping key |
| `GetGroupedBillingInvoiceSubDetailList` | Core grouping/aggregation logic for TOC summary |
| `LaunchBatchProcess` | Launches BLROLLPER batch process for posting Final invoices |
| `PostUpdateAction` | Cascades header status to detail records after save |
| `CheckContractForUser` | Loads contract chain data for external user filtering |

#### Private Helper Methods for External Users

| Method | Purpose |
|--------|---------|
| `BillingInvoiceHeaderForExternalUser` | Complex join chain: InvoiceGroupContract -> InvoiceGroup -> AccountingMonth -> Contract -> ContractAmend -> ContractAgent, filtered by user BPs |
| `BillingInvoiceHeaderSummaryForExternalUser` | Similar chain for Header by Contract view |
| `BillingInvoiceDetailForExternalUser` | Contract chain filtering for detail records |
| `GetContractAgentsByBpNo` | Retrieves contract agents matching user's BP list |
| `GetContractAmendByCtrNoList` | Retrieves contract amendments by contract numbers |
| `GetContractByCtrAmendNoList` | Retrieves contracts by contract and amendment numbers |
| `GetBillingInvoiceGroupContractByCtrNoList` | Retrieves billing group-to-contract mappings |
| `GetBillingInvoiceGroupByInvoiceGrpIdList` | Retrieves billing group definitions |
| `GetAccountingMonth` | Retrieves accounting month records for the billing roll type |
| `GetInvoiceGrpCopy` | Retrieves invoice group copy configuration (delivery methods) |

### InvoiceMaintenance_FillSubDetails

**File**: `Quorum.QPTM.ServiceCore/QPTMServiceCore_InvoiceMaintenance/InvoiceMaintenance_FillSubDetails.cs` (~272 lines)

Dedicated class for enriching sub-detail records with rate, TOC, and tier information.

#### Dependencies

| Dependency | Purpose |
|------------|---------|
| `IQPTMDataAccess_Rate` | Retrieve rate header records |
| `IQPTMDataAccess_RTTypeOfCharge` | Retrieve Type of Charge descriptions |
| `IRateCacheAccess` | Cached access to rate tier details |
| `IQPTMService_Utility` | Utility service for user type checks |

#### Key Methods

| Method | Purpose |
|--------|---------|
| `FillSubDetails` | Main enrichment method - combines sub-details + revisions, joins with billing run xref, filters for external users, enriches with rate/TOC/tier data |
| `GetRateHdrByRateHdrId` | Batch-loads rate records for all referenced RateHdrIds, returns as lookup |
| `GetTocByTocCode` | Batch-loads TOC descriptions for all referenced TocCodes, returns as dictionary |
| `CopyBillingInvoiceSubDetailRevList` | Converts `BillingInvoiceSubDetailRevDO` records to `BillingInvoiceSubDetailDO` (property-by-property copy) |
| `BillingInvoiceSubDetailForExternalUser` | Contract chain filtering for sub-detail records |

### InvoicesAPIService

**File**: `Quorum.QPTM.Web.Controllers/APIService/InvoicesAPIService.cs` (~244 lines)

REST API service layer for external API access to invoice data.

#### Dependencies

| Dependency | Purpose |
|------------|---------|
| `IQPTMInvoiceSummaryWidget` | Provides invoice summary data |
| `IQPTMAllocationService` | Provides open accounting month information |

#### Key Methods

| Method | Purpose |
|--------|---------|
| `GetInvoicesHeaderViews` | Returns flattened invoice header view objects |
| `GetInvoicesHeaderViewsSummary` | Returns grouped summary objects (by AcctgMonth or ServiceRequester) |
| `GetEnumeratedParameterValues` | Returns valid filter and summary enum values |
| `GetInvoiceInformation` | Core data retrieval applying filter enums (CurrentOpenMonth, LastClosedMonth) |

---

## Controller Layer

### QUIControllerInvoiceMaintenance (UI Controller)

**File**: `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerInvoiceMaintenance.cs` (~622 lines)

The UI Controller manages session state and orchestrates the interaction between the web layer and the service layer.

#### Key Properties (Controller Data)

| Property | Type | Description |
|----------|------|-------------|
| `BillingInvoiceHeader` | `QDOListContainer<BillingInvoiceHeaderDO>` | Invoice header grid data (root bind) |
| `InvoiceMaintenanceData` | `InvoiceMaintenanceData` | Composite data transfer object |
| `InvoiceHeaderByContractTOSList` | `QDOListContainer<BillingInvoiceHeaderDO>` | Header by Contract tab data |
| `InvoiceSubTOCDetailSummaryList` | `QDOListContainer<BillingInvoiceSubDetailDO>` | Sub-detail by TOC tab data |
| `InvoiceSubDetailList` | `QDOListContainer<BillingInvoiceSubDetailDO>` | Sub-detail by Contract tab data |
| `InvoiceDetailList` | `QDOListContainer<BillingInvoiceDetailDO>` | Detail tab data |
| `CurrentOpenAccountingMonth` | `DateTime` | Cached current open accounting month |
| `UserDefaultBp` | `string` | External user's default Business Partner |

#### Selected Items (Grid Selection State)

| Property | Type |
|----------|------|
| `SelectedBillingInvoiceHeader` | `BillingInvoiceHeaderDO` |
| `SelectedBillingInvoiceHeaderByTOC` | `BillingInvoiceHeaderDO` |
| `SelectedInvoiceDetail` | `BillingInvoiceDetailDO` |
| `SelectedInvoiceSubDetailByTOC` | `BillingInvoiceSubDetailDO` |
| `SelectedInvoiceSubDetail` | `BillingInvoiceSubDetailDO` |

#### Key Method Overrides

| Method | Behavior |
|--------|----------|
| `Initialize` | Sets `BpNo` for external users from `UserDefaultBp` |
| `IsNew` | Always returns `false` (invoice maintenance is query-based, no new creation) |
| `ReadyForQuery` | Validates that at least AcctgMth or BpNo is provided |
| `DoQuery` | Sets filter, calls `GetSingleInvoiceMaintenance`, populates all grid containers |
| `DoSave` | Transfers grid data to `InvoiceMaintenanceData`, calls `UpdateSingleInvoiceMaintenance`, monitors batch process |
| `PreSave` | Validates `InvoiceStatCode` is not null on all header and detail records |
| `DoNew` | Initializes empty containers (no new invoice creation - this resets state) |
| `DoClone` | Throws `NotImplementedException` (cloning not supported) |
| `GetDetailsByHeaderId` | Lazy-loads detail/sub-detail data for a specific header (used when expanding Header by Contract rows) |
| `RunInvoiceReport` | Launches the `BLRX00` batch process for the selected header |

#### Controller Parameters

The `QControllerParamsInvoiceMaintenance` class defines the query parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `InvoiceHdrId` | `int` | Filter by specific invoice header ID |
| `ProcessQueueId` | `int` | Filter by process queue ID |
| `BpNo` | `string` | Filter by Business Partner number |
| `BpNm` | `string` | Business Partner name (display) |
| `AcctgMth` | `DateTime?` | Filter by accounting month |

### InvoiceMaintenanceController (MVC Controller)

**File**: `Quorum.QPTM.Web.Core/Controllers/InvoiceMaintenanceController.cs` (~632 lines)

The MVC controller handles HTTP requests for the Invoice Maintenance screen.

#### Security

- Decorated with `[QScreenSecurityObject(Constants.SecurityObjectIDs.InvoiceMaintenance)]`

#### Actions and Links

| Action/Link | Description |
|-------------|-------------|
| Query | Executes the invoice query with `ResetScreenState` JavaScript |
| Save | Visible only to internal users, uses `ExecuteBeforeSave` JavaScript |
| Close | Closes the screen |
| Rate Maintenance Link | Navigates to Rate Maintenance for the selected sub-detail's rate, hidden by default |
| Invoice Group Maintenance Link | Navigates to Invoice Group Maintenance for the selected header's group |

#### Tab Endpoints (GET)

| Endpoint | Tab | Partial View |
|----------|-----|-------------|
| `InvoiceHeaderTab` | Tab 1 - Invoice Header | `InvoiceMaintInvoiceHeaderTab` |
| `HeaderByContractTab` | Tab 2 - Header by Contract | `InvoiceMaintHeaderByContractTab` |
| `DetailTab` | Tab 3 - Detail | `InvoiceMaintDetailTab` |
| `SubDetailByTOCTab` | Tab 4 - Sub-Detail by TOC | `InvoiceMaintSubDetailByTOCTab` |
| `SubDetailByContractTab` | Tab 5 - Sub-Detail by Contract | `InvoiceMaintSubDetailByContractTab` |

#### Grid Data Endpoints (POST)

| Endpoint | Grid | Notes |
|----------|------|-------|
| `HeaderGridGetData` | Invoice Header grid | Ordered by AcctgMth DESC, BpNo, AgentBpNo, InvoiceId. Sets `IsPost = !IsOpen`. |
| `HeaderGridUpdate` | Invoice Header grid | Updates header field values |
| `HeaderByContractGridGetData` | Header by Contract grid | Ordered by AcctgMth DESC |
| `DetailsGridGetData` | Detail grid | Ordered by AcctgMth DESC, LineNum |
| `DetailsGridUpdate` | Detail grid | Updates detail field values |
| `SubDetailByTOCGridGetData` | Sub-Detail by TOC grid | Grouped/aggregated sub-details |
| `SubDetailGridGetData` | Sub-Detail by Contract grid | Full granular sub-details |

#### Grid Selection Endpoints (POST)

| Endpoint | Purpose |
|----------|---------|
| `HeaderGridRowChanged` | Sets `SelectedBillingInvoiceHeader` and first `SelectedBillingInvoiceHeaderByTOC` |
| `HeaderByContractGridRowChanged` | Sets `SelectedBillingInvoiceHeaderByTOC` |
| `DetailsGridRowChanged` | Sets `SelectedInvoiceDetail` |
| `SubDetailByTOCGridRowChanged` | Sets `SelectedInvoiceSubDetailByTOC` |
| `SubDetailGridRowChanged` | Sets `SelectedInvoiceSubDetail` |

#### Helper Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `RunInvoiceReport` | POST | Triggers invoice report generation for selected header |
| `GetDetailsByHeaderId` | POST | Lazy-loads detail data for a header in the Header by Contract tab |
| `UpdateFilter` | POST | Stores DataSourceRequest filters on the UI controller for subsequent grid data calls |
| `InvoiceMaintenanceFieldUpdate` | POST | Handles field-level updates on the root view model |

#### Excel Export Endpoints

| Endpoint | Export Name |
|----------|------------|
| `HeaderGridExcelExport` | InvoiceMaintHeader |
| `HeaderByContractGridExcelExport` | InvoiceMaintHeaderByContract |
| `DetailsGridExcelExport` | InvoiceDetail |
| `SubDetailByTOCGridExcelExport` | InvoiceSubDetailByToc |
| `SubDetailGridExcelExport` | InvoiceSubDetail |

### InvoicesController (API Controller)

**File**: `Quorum.QPTM.Web.Controllers/APIControllers/InvoicesController.cs` (~370 lines)

REST API controller for external invoice data access.

#### Route Prefix: `api/v1/Invoices`

#### API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Get list of invoices with embedded details |
| GET | `/EnumeratedParameterValues` | Fetch valid enumeration values for API parameters |
| GET | `/HeaderView` | Get flattened invoice header view collection (supports impersonation) |
| GET | `/HeaderViewSummary` | Get invoice header view summary groupings |
| GET | `/Summary` | Get invoice summary groupings with embedded detail |
| GET | `/SummaryView` | Get flattened invoice summary with embedded detail |
| GET | `/View` | Get flattened invoice detail view collection |
| GET | `/{tsp}/{acctgMonth}` | Get all invoice objects for a specific TSP and month |

#### Common API Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `tsp` | `int` | Transportation Service Provider ID (required) |
| `acctgMonth` | `DateTime?` | Accounting month filter |
| `filter` | `string` | Comma-separated filter enums (see `InvoiceFilterEnum`) |
| `summary` | `string` | Summary grouping enum (see `InvoiceSummaryEnum`) |
| `embed` | `string` | Embedded sub-resources specification |
| `include` | `string` | Properties to include in response |
| `exclude` | `string` | Properties to exclude from response |

#### Filter Enums (`InvoiceFilterEnum`)

- `CurrentOpenMonth` - Filter to current open accounting month
- `LastClosedMonth` - Filter to last closed accounting month

#### Summary Enums (`InvoiceSummaryEnum`)

- `AccountingMonth` - Group by accounting month
- `ServiceRequester` - Group by business partner (shipper)

---

## Data Objects

### Primary Data Objects

| Data Object | Table | DOExt File | Description |
|-------------|-------|-----------|-------------|
| `BillingInvoiceHeaderDO` | `BLTRAN_INVOICE_HDR` | `BillingInvoiceHeaderDOExt.cs` | Invoice header with extended props: IsPost, IsOpen, CtrNo, TosCode, CurrentAmt, PpaAmt, quantity fields |
| `BillingInvoiceDetailDO` | `BLTRAN_INVOICE_DTL` | `BillingInvoiceDetailDOExt.cs` | Invoice detail with extended props: TocDescr, HdrBpNo, HdrBpNm, HdrInvoiceGrpId, HdrInvoiceId |
| `BillingInvoiceSubDetailDO` | `BLTRAN_INVOICE_SUB_DTL` | `BillingInvoiceSubDetailDOExt.cs` | Invoice sub-detail with extended props: TocDescr, HdrBpNo, HdrBpNm, HdrInvoiceGrpId, HdrInvoiceId, UpdtDate, TierDescr |
| `BillingInvoiceSubDetailRevDO` | `BLTRAN_INVOICE_SUB_DTL_REV` | `BillingInvoiceSubDetailRevDOExt.cs` | Sub-detail revision records with extended InvoiceId |
| `BillingInvoiceGroupDO` | `BLCTRL_INVOICE_GRP` | `BillingInvoiceGroupDOExt.cs` | Invoice group definition with extended BpNm |
| `BillingInvoiceGroupContractDO` | `BLCTRL_INVOICE_GRP_CTR` | `BillingInvoiceGroupContractDOExt.cs` | Group-to-contract mapping |

### Supporting Data Objects

| Data Object | Table/Source | Description |
|-------------|-------------|-------------|
| `BillingLastInvoiceGrpRunXrefDO` | `BLXREF_LAST_INVOICE_GRP_RUN` | Billing run cross-reference with IsOpen flag |
| `Blrpts10InvoiceDocSumDO` | `BLRPTS_10_INVOICE_DOC_SUM` | Invoice document summary (contract-level amounts) |
| `BlctrlInvoiceGrpCopyDO` | `BLCTRL_INVOICE_GRP_COPY` | Invoice group delivery method configuration |
| `AccountingMonthDO` | Accounting month table | Accounting periods with roll type |
| `ContractDO` | Contract header | Contract with effective date ranges |
| `ContractAmendDO` | Contract amendment | Amendment with effective date ranges |
| `ContractAgentQPTMDO` | Contract agent | Agent-to-contract relationships with effective dates |
| `RateDO` | Rate header | Rate schedule with effective date ranges |
| `TierDetailDO` | Rate tier detail | Rate tier descriptions (cached) |
| `UserBPDO` | User-BP mapping | Maps security users to business partners |
| `InvoiceMaintenanceData` | Composite DTO | Aggregates all invoice data for service-layer transport |

### Composite Data Transfer Object: InvoiceMaintenanceData

This is the primary DTO passed between the UI controller and service layer. Key properties:

| Property | Type | Description |
|----------|------|-------------|
| `TspNo` | `short` | TSP number |
| `BpNo` | `string` | Business Partner filter |
| `AcctgMth` | `DateTime?` | Accounting month filter |
| `CtrNo` | `string` | Contract number filter |
| `InvoiceHeaderList` | `List<BillingInvoiceHeaderDO>` | Header records |
| `InvoiceDetailList` | `List<BillingInvoiceDetailDO>` | Detail records |
| `InvoiceSubDetailList` | `List<BillingInvoiceSubDetailDO>` | Sub-detail records |
| `InvoiceSubTOCDetailSummaryList` | `List<BillingInvoiceSubDetailDO>` | Aggregated sub-detail records |
| `InvoiceHeaderByContractTOSList` | `List<BillingInvoiceHeaderDO>` | Header by contract records |
| `BillingLastInvoiceGrpRunXrefList` | `List<BillingLastInvoiceGrpRunXrefDO>` | Billing run cross-references |
| `UserBPList` | `List<UserBPDO>` | External user's BP list |
| `ContractList` | `List<ContractDO>` | Contract data for external filtering |
| `ContractAmendList` | `List<ContractAmendDO>` | Amendment data for external filtering |
| `ContractAgentList` | `List<ContractAgentQPTMDO>` | Agent data for external filtering |
| `BillingInvoiceGroupContractList` | `List<BillingInvoiceGroupContractDO>` | Group-contract mappings |
| `BillingInvoiceGroupList` | `List<BillingInvoiceGroupDO>` | Group definitions |
| `AccountingMonthList` | `List<AccountingMonthDO>` | Accounting month records |
| `InvoiceGrpCopy` | `List<BlctrlInvoiceGrpCopyDO>` | Invoice group copy/delivery config |
| `CurrentOpenAccountingMonth` | `DateTime` | Current open accounting month |
| `BatchProcessStatus` | `int` | Batch process ID (after posting) |

---

## Database Tables

### Primary Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `BLTRAN_INVOICE_HDR` | Invoice headers | InvoiceHdrId (PK), TspNo, InvoiceId, InvoiceGrpId, AcctgMth, BpNo, InvoiceAmt, InvoiceStatCode, ProcessQueueId, BillPeriodId |
| `BLTRAN_INVOICE_DTL` | Invoice detail lines | InvoiceDtlId (PK), InvoiceHdrId, TspNo, LineNum, CtrNo, TocCode, TransAmt |
| `BLTRAN_INVOICE_SUB_DTL` | Invoice sub-detail | InvoiceSubDtlId (PK), InvoiceDtlId, InvoiceHdrId, TspNo, ActivityDate, Rate, TransAmt |
| `BLTRAN_INVOICE_SUB_DTL_REV` | Sub-detail revisions | Same structure as sub-detail, stores historical revisions |

### Configuration/Reference Tables

| Table | Purpose |
|-------|---------|
| `BLXREF_LAST_INVOICE_GRP_RUN` | Links invoices to latest billing run; provides IsOpen flag |
| `BLRPTS_10_INVOICE_DOC_SUM` | Invoice document summary by contract (for Header by Contract tab) |
| `BLCTRL_INVOICE_GRP` | Invoice group definitions (billing group configuration) |
| `BLCTRL_INVOICE_GRP_CTR` | Invoice group-to-contract mappings |
| `BLCTRL_INVOICE_GRP_COPY` | Invoice group delivery method configuration |
| `RT_TYPE_OF_CHARGE` | Type of Charge reference data |
| `RT_RATE_HDR` / Rate tables | Rate schedule definitions |
| `RT_TIER_DTL` | Rate tier detail descriptions |

---

## Validation Rules

All validation rules are in `Quorum.QPTM.Validations/Screens/InvoiceMaintenance/`.

### Validation Context

**File**: `Context/QPTMValidationContext_InvoiceMaintenance.cs`

- Class: `QInvoiceMaintenanceValidationContext`
- Validation Group: `QPTMInvoiceMaintenance`
- Provides: `DataToValidate` (InvoiceMaintenanceData), `IsInternalUser`, `AllowCloseFutureAcctgOnHdr`, `CurrentOpenAccountingMonth`

### Rules

| # | Class | Purpose | Key Logic |
|---|-------|---------|-----------|
| 001 | `QPTMValidationInvoiceHeaderMaintenance001_ValidateHeaderStatusCode` | Prevent modifying Final invoices | If header is modified AND original status is Final (FIN), add error |
| 002 | `QPTMValidationInvoiceHeaderMaintenance002_ValidateDeletePermission` | Block external user deletes | If not internal user AND any header/detail is Deleted state, add error |
| 003 | `QPTMValidationInvoiceHeaderMaintenance003_ValidateUpdatePermission` | Block external user updates | If not internal user AND any header/detail is Modified state, add error |
| 004 | `QPTMValidationInvoiceHeaderMaintenance004_ValidateInvoice` | Validate posting requirements | For Open+Post flagged headers: must be Final, must be in current (or future if config allows) accounting month, cannot post closed months |
| 005 | `QPTMValidationInvoiceHeaderMaintenance005_ValidateDetailStatusCode` | Prevent invalid detail status changes | Detail original status Final cannot be changed; detail status cannot be set to Final directly |

### Pre-Save Validation (UI Controller)

The `PreSave` method in the UI controller performs additional validation before calling the service:
- Checks for null/empty `InvoiceStatCode` on all header records
- Checks for null/empty `InvoiceStatCode` on all detail records
- Throws `QUserException` with field-level error highlighting if violations found

---

## FillSubDetails Algorithm

The `InvoiceMaintenance_FillSubDetails.FillSubDetails()` method is the core algorithm for enriching sub-detail records. Here is the step-by-step flow:

### Step 1: Combine Sub-Details and Revisions

```
tmpList = billingInvoiceSubDetailList.ToList()
tmpList.AddRange(CopyBillingInvoiceSubDetailRevList(billingInvoiceSubDetailRevList))
```

Revision records (`BillingInvoiceSubDetailRevDO`) are converted to `BillingInvoiceSubDetailDO` via property-by-property copy (all ~80 properties).

### Step 2: Join with Billing Run Cross-Reference

```
tmpList = tmpList.Join(billingLastInvoiceGrpRunXrefList,
    on: {TspNo, InvoiceGrpId, AcctgMth, ProcessQueueId, BillPeriodId})
```

This filters sub-details to only those matching the latest billing run.

### Step 3: Filter for External Users

If user is external:
1. Get user's BP list
2. Call `BillingInvoiceSubDetailForExternalUser` which joins Contract -> ContractAmend -> ContractAgent
3. Filter sub-details where either BpNo matches user's BPs OR the contract/AcctgMth/TspNo combination is in the agent chain result

### Step 4: Batch-Load Reference Data

```
rateHdrIdList = tmpList.Select(RateHdrId).ToSafeList()
tocCodeList = tmpList.Select(TocCode).ToSafeList()
lookupRates = GetRateHdrByRateHdrId(tspNo, rateHdrIdList)  // ILookup<int, RateDO>
dictTocDescr = GetTocByTocCode(tspNo, tocCodeList)          // Dictionary<string, string>
```

### Step 5: Enrich Each Sub-Detail

For each sub-detail record:

1. **Rate Type Code**: If `RateHdrId` has value, find rate record where `ActivityDate` falls within effective date range. Set `RateTypeCode` from matching rate.

2. **TOC Description**: If `TocCode` is valid, look up description from `dictTocDescr`. Set `TocDescr`.

3. **Tier Description**: If both `TierDtlId` and `RateTierId` have values, retrieve tier detail from cache (`RateCacheAccess.GetRateTierDetail`). Set `TierDescr`.

4. **Accept Changes**: Call `AcceptChanges()` to reset the dirty flag.

### Performance Notes

- Rate and TOC data are batch-loaded upfront (two queries) rather than per-record
- Tier data uses the `RateCacheAccess` cache layer
- The `ToSafeList()` extension deduplicates the ID lists before querying

---

## Query Flow

```
1. User enters AcctgMth and/or BpNo, clicks Query
2. InvoiceMaintenanceController -> MVC framework -> DoQuery()
3. QUIControllerInvoiceMaintenance.DoQuery()
   a. SetFilterToQuery() - copies params to InvoiceMaintenanceData
   b. Service.GetSingleInvoiceMaintenance(data)
      i.   Query BLTRAN_INVOICE_HDR with filters
      ii.  Query BLTRAN_INVOICE_DTL to find matching header IDs
      iii. AddAdditionalPropertiesInvoiceMaintenanceHeader()
           - Query BLXREF_LAST_INVOICE_GRP_RUN for IsOpen flag
           - Join headers with xref to fill IsOpen
           - If external: CheckContractForUser() loads contract chain
           - FillHeader() filters headers (external user filtering)
           - FillHeaderByContract() joins with BLRPTS_10_INVOICE_DOC_SUM
      iv.  GetInvoiceMaintenanceDetails()
           - Query BLTRAN_INVOICE_DTL, BLTRAN_INVOICE_SUB_DTL, BLTRAN_INVOICE_SUB_DTL_REV
           - FillDetails() - external user filtering on details
           - FillSubDetails() - enrichment algorithm (see above)
           - Fill sub-detail header info (BpNo, BpNm, InvoiceId from header lookup)
           - FillSubDetailsByTos() - aggregation/grouping for TOC tab
           - Fill detail header info
   c. SetBillingObjectData() - populates all grid containers from returned data
```

---

## Save Flow

```
1. User modifies status codes or checks IsPost, clicks Save
2. InvoiceMaintenanceController -> MVC framework -> PreSave() then DoSave()
3. PreSave()
   a. Clear previous errors on all header and detail records
   b. Validate InvoiceStatCode is not null on all headers
   c. Validate InvoiceStatCode is not null on all details
   d. Throw QUserException if violations found (with field highlighting)
4. DoSave()
   a. Transfer grid data to InvoiceMaintenanceData
   b. Service.UpdateSingleInvoiceMaintenance(data)
      i.   ValidateSingleInvoiceMaintenance() - runs all 5 validation rules
      ii.  If any errors, return immediately
      iii. LaunchBatchProcess() - if Final+Open+IsPost headers exist
           - Collect InvoiceHdrIds for posting
           - Launch BLROLLPER synchronously
           - If batch fails, return with error
      iv.  Collect Approved and Preliminary header IDs
      v.   dataAccess.UpdateMultipleBillingInvoiceHeader()
      vi.  dataAccess.UpdateMultipleBillingInvoiceDetail()
      vii. PostUpdateAction() - cascade status to details for Approved/Preliminary headers
      viii.Re-query (GetSingleInvoiceMaintenance) to refresh data
   c. SetBillingObjectData() - refresh all grids
   d. If batch process launched, add to UI process monitor
```

---

## Configuration Settings

| Setting | Location | Description |
|---------|----------|-------------|
| `AllowCloseFutureAcctgOnHdr` | `QPTMTspConfigs` | TSP-level setting. When = 1, allows closing invoices for future accounting months. Default behavior (0) only allows closing current month. |
| `AccountRollTypes.Billing` | `Constants` | Roll type code used to retrieve the current open billing accounting month |
| `InvoiceDeliveryMethodCode.Internal` | `Constants` | Value `INT` - used to filter invoice groups that are internal-only from external user views |
| `SecurityObjectIDs.InvoiceMaintenance` | `Constants` | Security object for screen access control |
| `ProcessIDs.BATCHID_BLROLLPER` | `Constants` | Value `BLROLLPER` - batch process ID for invoice posting |
| `AgentFunction.None` | `Constants` | Used to exclude agents with no invoice function when filtering for external users |

---

## View Models and UI Tabs

### Root View Model

**File**: `Quorum.QPTM.Web.Core/ViewModels/InvoiceMaintenanceRootVM.cs`

Maps to `BLTRAN_INVOICE_HDR` table columns with additional UI properties:

| Property | Description |
|----------|-------------|
| `InvoiceHdrId` | Primary key (from BLTRAN_INVOICE_HDR) |
| `ProcessQueueId` | Primary key (from BLTRAN_INVOICE_HDR) |
| `InvoiceId`, `InvoiceGrpId`, `InvoiceDate`, `AcctgMth`, `NetDueDate` | Header fields |
| `InvoiceAmt`, `InvoiceStatCode` | Amount and status |
| `BpNo`, `BpNm`, `AgentBpNo`, `AgentBpNm` | Business partner info |
| `PostedDate`, `PostDate`, `BillPeriodId` | Posting and period info |
| `CtrNo`, `TosCode`, `TocCode` | Contract and service info |
| `TotalInvHeaderAmt` | Total header amount display |
| `TotalInvHeaderContractAmt` | Total contract amount display |
| `TotalInvHeaderContractFuelQty` | Total fuel quantity display |
| `TotalInvDetailAmt` | Total detail amount display |
| `TotalInvSubDetailTOCAmt` | Total sub-detail TOC amount display |
| `TotalInvSubDetailAmt` | Total sub-detail amount display |
| `IsUserInternal` | Determines UI permissions |

### Grid View Models

- `BillingInvoiceHeaderVM` - Header and Header by Contract grids
- `BillingInvoiceDetailVM` - Detail grid
- `BillingInvoiceSubDetailVM` - Sub-Detail by TOC and Sub-Detail by Contract grids

### Grid IDs

| Grid ID Constant | Grid |
|-------------------|------|
| `InvoiceMaintenanceHeaderGrid` | Invoice Header tab grid |
| `InvoiceMaintenanceHeaderByContractGrid` | Header by Contract tab grid |
| `InvoiceMaintenanceDetailGrid` | Detail tab grid |
| `InvoiceMaintenanceSubDetailByTOCGrid` | Sub-Detail by TOC tab grid |
| `InvoiceMaintenanceSubDetailByContractGrid` | Sub-Detail by Contract tab grid |

---

## Key File Locations

| File | Path |
|------|------|
| Service Core | `Quorum.QPTM.ServiceCore/QPTMServiceCore_InvoiceMaintenance.cs` |
| FillSubDetails | `Quorum.QPTM.ServiceCore/QPTMServiceCore_InvoiceMaintenance/InvoiceMaintenance_FillSubDetails.cs` |
| UI Controller | `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerInvoiceMaintenance.cs` |
| MVC Controller | `Quorum.QPTM.Web.Core/Controllers/InvoiceMaintenanceController.cs` |
| API Controller | `Quorum.QPTM.Web.Controllers/APIControllers/InvoicesController.cs` |
| API Service | `Quorum.QPTM.Web.Controllers/APIService/InvoicesAPIService.cs` |
| Root View Model | `Quorum.QPTM.Web.Core/ViewModels/InvoiceMaintenanceRootVM.cs` |
| Header DO Ext | `Quorum.QPTM.DataObject/BillingInvoiceHeaderDOExt.cs` |
| Detail DO Ext | `Quorum.QPTM.DataObject/BillingInvoiceDetailDOExt.cs` |
| SubDetail DO Ext | `Quorum.QPTM.DataObject/BillingInvoiceSubDetailDOExt.cs` |
| SubDetail Rev DO Ext | `Quorum.QPTM.DataObject/BillingInvoiceSubDetailRevDOExt.cs` |
| Group DO Ext | `Quorum.QPTM.DataObject/BillingInvoiceGroupDOExt.cs` |
| Group Contract DO Ext | `Quorum.QPTM.DataObject/BillingInvoiceGroupContractDOExt.cs` |
| Validation Context | `Quorum.QPTM.Validations/Screens/InvoiceMaintenance/Context/QPTMValidationContext_InvoiceMaintenance.cs` |
| Validation Rule 001 | `Quorum.QPTM.Validations/Screens/InvoiceMaintenance/Validation Rules/QPTMValidationInvoiceHeaderMaintenance001_ValidateHeaderStatusCode.cs` |
| Validation Rule 002 | `Quorum.QPTM.Validations/Screens/InvoiceMaintenance/Validation Rules/QPTMValidationInvoiceHeaderMaintenance002_ValidateDeletePermission.cs` |
| Validation Rule 003 | `Quorum.QPTM.Validations/Screens/InvoiceMaintenance/Validation Rules/QPTMValidationInvoiceHeaderMaintenance003_ValidateUpdatePermission.cs` |
| Validation Rule 004 | `Quorum.QPTM.Validations/Screens/InvoiceMaintenance/Validation Rules/QPTMValidationInvoiceHeaderMaintenance004_ValidateInvoice.cs` |
| Validation Rule 005 | `Quorum.QPTM.Validations/Screens/InvoiceMaintenance/Validation Rules/QPTMValidationInvoiceHeaderMaintenance005_ValidateDetailStatusCode.cs` |
| Unit Tests | `Quorum.QPTM.UnitTests/InvoiceMaintenance/InvoiceMaintenanceTests.cs` |
| Unit Tests (No Context) | `Quorum.QPTM.UnitTests/InvoiceMaintenance/InvoiceMaintenanceTests_NoContext.cs` |
| API Unit Tests | `Quorum.QPTM.UnitTests/API/InvoicesControllerTests.cs` |
| Service Core Unit Tests | `Quorum.QPTM.UnitTests/ServiceCore/QPTMServiceCore_InvoiceMaintenance.cs` |
| Constants (InvoiceStatCode) | `Quorum.QPTM.CoreInterface/Constants.cs` (line ~3993) |
| TSP Config | `Quorum.QPTM.Common/ConfigSettings/QPTMTspConfigs.cs` (AllowCloseFutureAcctgOnHdr) |

---

## Related Documentation

- [Domain Knowledge](./domain.md) - Business concepts, invoice lifecycle, status codes, and business rules
- [Troubleshooting Guide](./troubleshooting.md) - Common issues, diagnostic SQL queries, and resolution patterns

---

*Last updated: 2026-03-03*

*Document version: 1.0*
