---
title: Inventory (INV) - Architecture
category: architecture
feature: Inventory (INV)
related_repos: Web, Batch
keywords: INV, architecture, QPTMInventoryService, inventory accounts, imbalance trading, storage transfer, controllers, API, validation, data objects, database tables, cache, configuration, INACCTACCM, INTRDPEND, INCONFTRADE
last_updated: 2026-03-03
---

# Inventory (INV) - Architecture

## Overview

This document explains the **technical architecture** of the Inventory (INV) system in QPTM. It covers the service layer design, controller structure, API endpoints, validation framework, data objects, database schema, batch processes, caching, and configuration.

For business concepts and terminology, see [Domain Documentation](./domain.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Service Layer](#service-layer)
3. [Controllers](#controllers)
4. [API Layer](#api-layer)
5. [Validation Framework](#validation-framework)
6. [Data Objects](#data-objects)
7. [Database Tables](#database-tables)
8. [Batch Processes](#batch-processes)
9. [Caching](#caching)
10. [Configuration](#configuration)
11. [Integration Points](#integration-points)

---

## System Architecture

### Architectural Layers

```
+---------------------------------------------------------------------+
|                      WEB APPLICATION LAYER                           |
|  +---------------------------+  +--------------------------------+  |
|  | InventoryAccountsController|  | InventoryAdjustmentsController |  |
|  | (MVC - Monthly/Daily tabs) |  | (MVC - Bulk Edit Grid)         |  |
|  +-------------+-------------+  +---------------+----------------+  |
+----------------|-------------------------------|--------------------+
                 |                               |
                 v                               v
+---------------------------------------------------------------------+
|                         API LAYER                                    |
|  +---------------------------------------------------------------+  |
|  | InventoryController (route: /api/v1/Inventory)                |  |
|  |   Accounts | Activity | ActivityPath | BalanceDaily |          |  |
|  |   BalanceMonthly | EnumeratedParameterValues                  |  |
|  +---------------------------------------------------------------+  |
+---------------------------------------------------------------------+
                 |
                 v
+---------------------------------------------------------------------+
|                        SERVICE LAYER                                 |
|  +---------------------------------------------------------------+  |
|  | QPTMInventoryService.cs (1133 lines - Main Orchestrator)      |  |
|  |   - Imbalance Trading (Submit/Confirm/Reject/Accept/Process)  |  |
|  |   - Storage Transfers (Submit/Confirm/Reject/Accept/Process)  |  |
|  |   - Account Management (Get/Save/Validate Headers)            |  |
|  |   - Manual Posting (Get/Save/Validate)                        |  |
|  |   - Account Balance & Activity queries                        |  |
|  |   - Code Tables (Trade Status, Actions, Account Types)        |  |
|  |   - TSP Configuration management                              |  |
|  +---------------------------------------------------------------+  |
|  | QPTMInventoryWidgetService.cs (Dashboard Widget)              |  |
|  |   - GetInventoryImbalances (IMB accounts)                     |  |
|  |   - GetOperatorImbalances (OBA accounts)                      |  |
|  |   - GetStorageBalances (STO accounts)                         |  |
|  |   - Tolerance calculations                                    |  |
|  +---------------------------------------------------------------+  |
|  | QPTMServiceCore_InventoryAccounts.cs (Accounts Screen)        |  |
|  |   - Monthly/Daily Activity and Balance view queries           |  |
|  |   - Component type filtering (Group/SubGroup/Quantity)        |  |
|  +---------------------------------------------------------------+  |
+---------------------------------------------------------------------+
                 |
                 v
+---------------------------------------------------------------------+
|                      VALIDATION LAYER                                |
|  +---------------------------------------------------------------+  |
|  | ImbalanceTrading: RuleINTR000010 - RuleINTR000310 (31 rules)  |  |
|  | InventoryAccount: RuleINCA000010 - RuleINCA000160 (16 rules)  |  |
|  | ManualPosting:    RuleINMP000010 - RuleINMP000020 (2 rules)   |  |
|  | StorageTransfer:  RuleINST000010 - RuleINST000220 (22 rules)  |  |
|  +---------------------------------------------------------------+  |
+---------------------------------------------------------------------+
                 |
                 v
+---------------------------------------------------------------------+
|                    DATA ACCESS LAYER                                 |
|  +---------------------------------------------------------------+  |
|  | IQInventoryDataAccess (Main inventory DA interface)           |  |
|  | IQPTMDataAccess_InventoryAccountHeader                        |  |
|  | IQPTMDataAccess_InventoryAccountContract                      |  |
|  | IQPTMDataAccess_InventoryAccountBalance                       |  |
|  | IQPTMDataAccess_InventoryAccountActivity                      |  |
|  | IQPTMDataAccess_InventoryActivityVw                           |  |
|  | IQPTMDataAccess_InventoryBalanceVw                            |  |
|  | IQPTMDataAccess_InventoryActivityDayVw                        |  |
|  | IQPTMDataAccess_InventoryBalanceDayVw                         |  |
|  | IQPTMDataAccess_InventoryAdjust                               |  |
|  +---------------------------------------------------------------+  |
+---------------------------------------------------------------------+
                 |
                 v
+---------------------------------------------------------------------+
|                       DATABASE LAYER                                 |
|  INCTRL_ACCT_HDR | INTRAN_ACCT_BAL | INTRAN_ACCT_BAL_DAILY         |
|  INTRAN_ACCT_ACTIVITY | INCTRL_ACCT_TRADE | INCTRL_INV_ADJ          |
|  INCTRL_ACCT_CTR | INCTRL_ACCT_DTL | INCTRL_ACCT_POST              |
|  INCTRL_TSP_CONFIG | INCTRL_ACCT_FUEL_ADJ | INCTRL_ACCT_TRADE_CHARGE|
+---------------------------------------------------------------------+
```

---

## Service Layer

### QPTMInventoryService.cs

**Location**: `Quorum.QPTM.ServiceCore.Inventory/QPTMInventoryService.cs`
**Lines**: ~1133
**Implements**: `IQPTMInventoryService`, `IQPTMInventoryServiceSide`

This is the **primary service class** for inventory operations. It is organized into the following regions:

#### Imbalance Trading Methods

| Method | Description |
|--------|-------------|
| `GetImbalanceTrade(tspNo, tradeId, validate)` | Retrieves a single trade by ID with optional validation |
| `GetImbalanceTrade(tspNo, filters, fillOtherData)` | Retrieves trades by filter criteria |
| `ValidateTrade(tspNo, trade, actionType)` | Runs imbalance trade validation rules |
| `SaveInventoryAccountTrade(trade, actionType)` | Routes to Submit/Confirm/Reject/Accept/Process/Withdraw |
| `SaveTradeTransfer(trade)` | Low-level save of a single trade record |
| `SaveTradeTransfer(trades)` | Low-level save of multiple trade records |
| `GetQuantityAvailableForTrade(trade, openAcctMth, isInitTrader)` | Calculates available quantity for trading |
| `SubmitTrade(trade)` | Sets status, validates, saves, fires events |
| `ConfirmTrade(trade)` | Validates, saves, launches `INTRDPEND` batch |
| `RejectTrade(trade)` | Validates, sets rejected status, saves |
| `AcceptTrade(trade)` | Validates, saves, launches `INCONFTRADE` batch |
| `ProcessTrade(trade)` | Validates, saves, launches `INCONFTRADE` batch |
| `WithdrawTrade(trade)` | Validates, saves, launches `INTRDWITH` batch |

#### Storage Transfer Methods

| Method | Description |
|--------|-------------|
| `GetStorageTransfer(tspNo, transferId, validate)` | Retrieves a storage transfer by ID |
| `ValidateTransfer(tspNo, transfer, actionType)` | Runs storage transfer validation rules |
| `SaveInventoryAccountTransfer(transfer, actionType)` | Routes to Submit/Confirm/Reject/Accept/Process/Withdraw |
| `SubmitTransfer(transfer)` | Sets `XFER` type, `STO` trade type, validates, saves |
| `ConfirmTransfer(transfer)` | Validates, saves, launches `INTRDPEND` batch |
| `RejectTransfer(transfer)` | Validates, resets status on failure, saves |
| `AcceptTransfer(transfer)` | Validates, saves, launches `INCONFTRADE` batch |
| `ProcessTransfer(transfer)` | Same as AcceptTransfer flow |
| `WithdrawTransfer(transfer)` | Validates, saves, launches `INTRDWITH` batch |

#### Inventory Account Methods

| Method | Description |
|--------|-------------|
| `GetInventoryAccountHeader(tspNo, invAcctId, asOfDate, validate, isRetrieveChildren, childFilter)` | Retrieves account header with optional children and validation |
| `GetInventoryAccountHeaderByPrimaryContract(tspNo, primaryCtrNo)` | Retrieves accounts by primary contract |
| `GetInventoryAccountHeaderByPrimaryCtrNoAndOIA(tspNo, ctrNo, oia)` | Retrieves by contract and OIA |
| `SaveInventoryAccountHeader(invAcctHdr)` | Validates and saves account header plus balance list |
| `ValidateAccount(tspNo, account, actionType)` | Runs inventory account validation rules |
| `GetMultipleInventoryAccountHeader(filters, includeChildren)` | Bulk query of account headers |
| `GetMultipleInventoryAccountContract(filters, includeChildren)` | Bulk query of account contracts |
| `GetInventoryAccountContracts(tspNo, filters)` | Query account-contract associations |

#### Manual Posting Methods

| Method | Description |
|--------|-------------|
| `GetInventoryAccountManualPost(tspNo, idInvAcct, prodMth)` | Retrieves manual post record |
| `ValidateManualPost(tspNo, invAcctPost, actionType)` | Runs manual posting validation rules |
| `SaveInventoryAccountManualPost(invAcctPost)` | Validates and saves manual post |

#### Balance and Activity Methods

| Method | Description |
|--------|-------------|
| `GetInventoryAccountBalance(tspNo, filters)` | Queries monthly balances |
| `GetInventoryAccountBalanceDaily(tspNo, filters)` | Queries daily balances |
| `GetAccountActivity(tspNo, filters)` | Queries account activity records |

#### Code Table Methods

| Method | Description |
|--------|-------------|
| `GetAccountTypeCtgyCode()` | Returns all account type category codes |
| `GetAccountTypeCtgyCode(acctType)` | Returns a single account type category |
| `GetTradeStatusTradeActionXref(tspNo)` | Returns status-action cross reference |
| `GetTradeDirCode(tradeDirCd)` | Returns trade direction code |
| `GetTradeCodes(out statusCodes, out actionCodes)` | Returns all status and action codes |
| `GetTradeActionCodes()` | Returns all trade action codes |

#### TSP Configuration Methods

| Method | Description |
|--------|-------------|
| `GetInventoryTspConfig(tspNo, effDtFrom, effDtTo)` | Retrieves TSP config for date range |
| `GetInventoryTspConfigs(tspNo)` | Retrieves all TSP configs |
| `SubmitInventoryTspConfigList(tspNo, list)` | Validates date overlaps, saves config list |

#### Helper Methods

| Method | Description |
|--------|-------------|
| `EvaluateFormula(formulaId, formulaVariables)` | Evaluates a user-defined formula |

#### Data Access Properties

| Property | Interface | Description |
|----------|-----------|-------------|
| `INDataAcess` | `IQInventoryDataAccess` | Primary inventory data access |
| `InventoryHeaderDataAccess` | `IQPTMDataAccess_InventoryAccountHeader` | Account header DA |
| `InventoryAccountContractDataAccess` | `IQPTMDataAccess_InventoryAccountContract` | Account-contract DA |
| `ContractDataAccess` | `IQContractDataAccess` | Contract DA (shared) |
| `BalanceDataAccess` | `IQPTMDataAccess_InventoryAccountBalance` | Balance DA |
| `ActivityDataAccess` | `IQPTMDataAccess_InventoryAccountActivity` | Activity DA |

### QPTMInventoryWidgetService.cs

**Location**: `Quorum.QPTM.ServiceCore.Inventory/QPTMInventoryWidgetService.cs`
**Implements**: `IQPTMInventoryWidget`

Provides data for dashboard widgets:

| Method | Description |
|--------|-------------|
| `GetInventoryImbalances(tspNo, asOfDate)` | Returns imbalance data for IMB accounts |
| `GetOperatorImbalances(tspNo, asOfDate)` | Returns imbalance data for OBA accounts |
| `GetStorageBalances(tspNo, asOfDate)` | Returns storage balance data for STO accounts |

**Key Logic:**
- Filters contracts by `OperationalBalance` attribute (OBA vs IMB/STO)
- Uses `InventoryCache` for account header lookups
- Retrieves balances from `INTRAN_ACCT_BAL` (minimum accounting month if multiple)
- Calculates daily imbalance from activity on previous gas day
- Calculates tolerance using TSP-configured percentage and basis

### QPTMServiceCore_InventoryAccounts.cs

**Location**: `Quorum.QPTM.ServiceCore/QPTMServiceCore_InventoryAccounts.cs`
**Implements**: `IQPTMService_InventoryAccounts`

Provides data for the Inventory Accounts screen:

| Method | Description |
|--------|-------------|
| `GetSingleInventoryAccountsData(data)` | Queries monthly/daily activity and balance views |
| `ValidateSingleInventoryAccountsData(data, context)` | Validates account data |
| `AddAdditionalPropertiesInventoryAccounts(data)` | Calculates running BegBal/ClosingBal on daily balances |

**Key Logic:**
- Filters by `InvGrpCode`, `InvSubGrpCode`, `InvQtyCode`, `FacilityId`, `AcctgMth`, `ProdMth`
- Component type progresses: `GRP` -> `SUB_GRP` -> `QTY` as more specific codes are provided
- Aggregates duplicate records using `ToLookup` by key fields, summing quantity columns
- Daily balance running total: `beginBalance = (row == 1) ? BegBalQty : previousEndingBalance`

---

## Controllers

### InventoryAccountsController

**Location**: `Quorum.QPTM.Web.Core/Controllers/InventoryAccountsController.cs`
**Security**: `[QScreenSecurityObject(Constants.SecurityObjectIDs.InventoryAccounts)]`
**Base**: `InventoryControllerBase<QUIControllerInventoryAccounts, InventoryAccountsRootVM>`

**Actions:**
- Query and Close buttons

**Tabs:**
| Tab | Action | Grid Data Method |
|-----|--------|-----------------|
| Monthly Activity | `MonthlyActivityTab` | `MonthlyActivityGridGetData` |
| Monthly Balance | `MonthlyBalanceTab` | `MonthlyBalanceGridGetData` |
| Daily Activity | `DailyActivityTab` | `DailyActivityGridGetData` |
| Daily Balance | `DailyBalanceTab` | `DailyBalanceGridGetData` |

**Grid ViewModels:**
- `InventoryActivityVwVM` (monthly activity)
- `InventoryBalanceVwVM` (monthly balance)
- `InventoryActivityDayVwVM` (daily activity)
- `InventoryBalanceDayVwVM` (daily balance)

**Special Features:**
- UOM (Unit of Measure) column toggling: `ShowHideMonthlyActivityAndBalanceGridColumns` switches between Energy (`Dth`) and Volume (`Mcf`) columns
- Excel export for all four grids
- Links to Authorization to Post Imbalances and Customer Account Summary screens
- Total calculations for injection, withdrawal, net, beginning balance, and closing balance

**Field Updates:**
- `InventoryAccountsFieldUpdate` - handles parameter changes

**Parameters:**
- `TspNo`, `InvGrpCode`, `InvSubGrpCode`, `InvQtyCode`, `FacilityId`, `AcctgMth`, `ProdMth`, `UomTypeCd`

### InventoryAdjustmentsController

**Location**: `Quorum.QPTM.Web.Core/Controllers/InventoryAdjustmentsController.cs`
**Security**: `[QScreenSecurityObject(Constants.SecurityObjectIDs.InventoryAdjustments)]`
**Base**: `InventoryControllerBase<QUIControllerInventoryAdjustments, InventoryAdjustmentsRootVM>`

**Actions:**
- Query, Close, and Save buttons

**Grid Operations:**
| Method | Description |
|--------|-------------|
| `InventoryAdjustmentsGridGetData` | Reads grid data with pagination fix |
| `InventoryAdjustmentsGridUpdate` | Updates grid row; triggers `IsModified` for SubmitInd/DeleteInd changes |
| `InventoryAdjustmentsGridAddNewRow` | Adds new row; supports cloning from existing |
| `InventoryAdjustmentsGridDeleteRow` | Removes row from bulk container |
| `InventoryAdjustmentsGridExcelExport` | Excel export |
| `InventoryAdjustmentsGridBulkEdit` (GET) | Exports for bulk edit |
| `InventoryAdjustmentsGridBulkEdit` (PUT) | Imports bulk edit data |

**Control State Logic** (`UpdateControlStates`):
- When `IsProc = true`: All fields become read-only
- Delete indicator: Read-only for new records; conditionally writable for processed records based on accounting month validity
- Required fields: `ActivityDate`, `ProdMth`, `AcctgMth`, `InvAdjTypeCode`

---

## API Layer

### InventoryController

**Location**: `Quorum.QPTM.Web.Controllers/APIControllers/InventoryController.cs`
**Route Prefix**: `api/v1/Inventory`
**Service**: `IInventoryAPIService` (via `InventoryAPIService`)

| Endpoint | Method | Route | Description |
|----------|--------|-------|-------------|
| Get Account | GET | `Accounts/{tsp}/{InventoryAccountId}` | Get single account with filters |
| Get Activity Collection | GET | `Activity` | Get activity for date range, account types |
| Get Activity by Account | GET | `Activity/{tsp}/{InventoryAccountId}` | Get activity for specific account |
| Get Activity Path Collection | GET | `ActivityPath` | Get activity path data |
| Get Activity Path by Account | GET | `ActivityPath/{tsp}/{InventoryAccountId}` | Get activity path for specific account |
| Get Balance Daily Collection | GET | `BalanceDaily` | Get daily balances for date range |
| Get Balance Daily by Account | GET | `BalanceDaily/{tsp}/{InventoryAccountId}` | Get daily balance for specific account |
| Get Balance Monthly Collection | GET | `BalanceMonthly` | Get monthly balances |
| Get Balance Monthly by Account | GET | `BalanceMonthly/{tsp}/{InventoryAccountId}` | Get monthly balance for specific account |
| Get Enum Values | GET | `EnumeratedParameterValues` | Get enumerated parameter values |

**Common Parameters:**
- `tsp` (int) - TSP number
- `inventoryAccountId` (int) - Inventory account ID
- `beginActivityDate` / `endActivityDate` (DateTime) - Date range
- `acctgMonth` (DateTime?) - Accounting month (defaults to open)
- `accountTypes` (string) - Comma-separated account type codes (e.g., `IMB,INK,PAL,STO`)
- `filter` (string) - Comma-separated filter enums
- `include` / `exclude` (string) - Data shaping (field inclusion/exclusion)

**Filter Enums:**
- `ActivityFilterEnum` - For activity endpoints
- `ActivityPathFilterEnum` - For activity path endpoints
- `BalanceDailyFilterEnum` - For daily balance endpoints
- `BalanceMonthlyFilterEnum` - For monthly balance endpoints

---

## Validation Framework

### Validation Contexts and Containers

| Domain | Context Class | Container Class | Base Class |
|--------|--------------|-----------------|------------|
| Imbalance Trading | `QINImbalanceTradeValidationContext` | `QINImbalanceValidationContainer` | `QImbalaceTradingValidationBase` |
| Inventory Account | `QINInventoryAccountValidationContext` | `QINInventoryAccountValidationContainer` | `QInventoryAccountValidationBase` |
| Manual Posting | `QINManualPostingValidationContext` | `QINManualPostingValidationContainer` | `QManualPostingValidationBase` |
| Storage Transfer | `QINStorageTransferValidationContext` | `QINStorageTransferValidationContainer` | `QStorageTransferValidationBase` |

### Validation Action Types

```csharp
enum enTradeValidationActionType { Query, Submit, Confirm, Reject, Accept, Process, Withdraw }
enum enAccountValidationActionType { Query, Submit }
enum enManualPostValidationActionType { Submit }
enum enTransferValidationActionType { Query, Submit, Confirm, Reject, Accept, Process, Withdraw }
```

### Imbalance Trading Rules (RuleINTR)

| Rule | Action | Description |
|------|--------|-------------|
| `RuleINTR000010` | Submit | Monthly trades require `MonthlyTradeLagTime` on contract |
| `RuleINTR000020` | Submit | Only new (Added) records can be submitted |
| `RuleINTR000030` | Submit | Validates initiating account and trade fields |
| `RuleINTR000040` | Submit | Validates confirming side fields |
| `RuleINTR000050` | Submit | Trade qty cannot exceed available for IMB category (external users) |
| `RuleINTR000060` | Submit | Additional initiating side validation |
| `RuleINTR000070` | Submit | Additional confirming side validation |
| `RuleINTR000080` | Confirm | Validates confirm action prerequisites |
| `RuleINTR000090` | Confirm | Validates trade status for confirm |
| `RuleINTR000100` | Accept | Validates accept action prerequisites |
| `RuleINTR000110` | Accept | Validates trade status for accept |
| `RuleINTR000120` | Reject | Validates reject action prerequisites |
| `RuleINTR000130` | Reject | Validates trade status for reject |
| `RuleINTR000140` | Withdraw | Validates withdraw action prerequisites |
| `RuleINTR000150-310` | Various | Additional business rule validations |

### Inventory Account Rules (RuleINCA)

| Rule | Action | Description |
|------|--------|-------------|
| `RuleINCA000010` | Submit | External users cannot add new accounts |
| `RuleINCA000020-160` | Various | Account header validation rules |

### Manual Posting Rules (RuleINMP)

| Rule | Action | Description |
|------|--------|-------------|
| `RuleINMP000010` | Submit | Account balance must exist for the account/prodMth/acctgMth |
| `RuleINMP000020` | Submit | Additional manual posting validations |

### Storage Transfer Rules (RuleINST)

| Rule | Action | Description |
|------|--------|-------------|
| `RuleINST000010` | Accept/Confirm | Confirming contact, phone, and contract required |
| `RuleINST000020-220` | Various | Storage transfer-specific validations |

**Rule Location**: `Quorum.QPTM.Validations.Rules.Inventory/`

---

## Data Objects

### Core Data Objects

| Data Object | Table | Description |
|-------------|-------|-------------|
| `InventoryAccountHeaderDO` | `INCTRL_ACCT_HDR` | Account header (type, primary contract, OIA, status) |
| `InventoryAccountBalanceDO` | `INTRAN_ACCT_BAL` | Monthly balance record |
| `InventoryAccountBalanceDailyDO` | `INTRAN_ACCT_BAL_DAILY` | Daily balance record |
| `InventoryAccountActivityDO` | `INTRAN_ACCT_ACTIVITY` | Account activity (alloc rec/del, rec/del diff) |
| `InventoryAccountTradeDO` | `INCTRL_ACCT_TRADE` | Trade/transfer record |
| `InventoryAdjustDO` | `INCTRL_INV_ADJ` | Inventory adjustment record |
| `InventoryAccountContractDO` | `INCTRL_ACCT_CTR` | Account-to-contract association |
| `InventoryAccountDetailDO` | `INCTRL_ACCT_DTL` | Account detail records |
| `InventoryAccountPostDO` | `INCTRL_ACCT_POST` | Manual posting record |
| `InventoryAccountFuelAdjustDO` | `INCTRL_ACCT_FUEL_ADJ` | Fuel adjustment record |
| `InventoryTspConfigDO` | `INCTRL_TSP_CONFIG` | TSP-level inventory configuration |

### View Data Objects

| Data Object | View/Table | Description |
|-------------|------------|-------------|
| `InventoryActivityVwDO` | `INTRAN_INV_ACTIVITY_VW` | Monthly activity view (Group/SubGroup/Qty) |
| `InventoryActivityDayVwDO` | `INTRAN_INV_ACTIVITY_DAY_VW` | Daily activity view |
| `InventoryBalanceVwDO` | `INTRAN_INV_BALANCE_VW` | Monthly balance view |
| `InventoryBalanceDayVwDO` | `INTRAN_INV_BALANCE_DAY_VW` | Daily balance view |

### Widget Data Objects

| Data Object | Description |
|-------------|-------------|
| `InventoryImbalancesDO` | Dashboard imbalance widget data (virtual table `INVENTORYIMBALANCES`) |
| `InventoryStorageBalanceDO` | Dashboard storage widget data (virtual table `INVENTORYSTORAGEBALANCE`) |

### Trade-Related Data Objects

| Data Object | Table | Description |
|-------------|-------|-------------|
| `InventoryAccountTradeRuleHeaderDO` | `INCTRL_ACCT_TRADE_RULE_HDR` | Trade rule header |
| `InventoryAccountTradeChargeDO` | `INCTRL_ACCT_TRADE_CHARGE` | Trade charge record |
| `TradeStatDO` | Code table | Trade status code |
| `TradeActnDO` | Code table | Trade action code |
| `TradeStatTradeActnDO` | Code table | Status-action cross reference |
| `TradeDirDO` | Code table | Trade direction code |
| `AccountTypeDO` | Code table | Account type with category, screen format, rolling flag |

### Supplementary Data Objects

| Data Object | Table | Description |
|-------------|-------|-------------|
| `InventoryAccountOiaDetailDO` | `INTRAN_ACCT_ACCUM_OIA_DTL` | OIA detail accumulation |
| `InventoryAccountEffContractXRefVwDO` | `INCTRL_XFER_EFF_CTR_VW` | Transfer effective contract view |
| `InventoryAccountEffContractXRefWithBalVwDO` | `INCTRL_XFER_WITH_BAL_VW` | Transfer with balance view |
| `InxrefAcctTradeRuleCheckDO` | `INXREF_ACCT_TRADE_RULE_CHECK` | Trade rule check cross reference |
| `InventoryAccountTypeTosDtlXRefDO` | `INXREF_ACCT_TYPE_TOS_DTL` | Account type to TOS detail cross reference |

### Composite Data Objects

| Data Object | Description |
|-------------|-------------|
| `InventoryAccountsData` | Composite: contains `MonthlyActivityList`, `MonthlyBalanceList`, `DailyActivityList`, `DailyBalanceList` |

---

## Database Tables

### Control Tables (INCTRL_*)

| Table | Primary Key | Description |
|-------|-------------|-------------|
| `INCTRL_ACCT_HDR` | `TSP_NO`, `INV_ACCT_ID` | Account header - type, primary contract, OIA, status |
| `INCTRL_ACCT_CTR` | `TSP_NO`, `INV_ACCT_ID`, `CTR_NO` | Account-to-contract mapping |
| `INCTRL_ACCT_DTL` | `TSP_NO`, `INV_ACCT_ID`, (detail keys) | Account detail records |
| `INCTRL_ACCT_TRADE` | `TSP_NO`, `ACCT_TRADE_ID` | Imbalance trade/transfer records |
| `INCTRL_ACCT_TRADE_CHARGE` | `TSP_NO`, `ACCT_TRADE_ID`, (charge keys) | Trade charges |
| `INCTRL_ACCT_TRADE_RULE_HDR` | `TSP_NO`, (rule keys) | Trade rules |
| `INCTRL_ACCT_POST` | `TSP_NO`, `INV_ACCT_ID`, `PROD_MTH` | Manual posting records |
| `INCTRL_ACCT_FUEL_ADJ` | `TSP_NO`, `INV_ACCT_ID`, (fuel keys) | Fuel adjustments |
| `INCTRL_INV_ADJ` | `TSP_NO`, `ID_ACCT_ADJ` | Inventory adjustments |
| `INCTRL_TSP_CONFIG` | `TSP_NO`, `EFF_DT_FROM` | TSP inventory configuration |

### Transaction Tables (INTRAN_*)

| Table | Primary Key | Description |
|-------|-------------|-------------|
| `INTRAN_ACCT_BAL` | `TSP_NO`, `INV_ACCT_ID`, `PROD_MTH`, `ACCTG_MTH` | Monthly account balance |
| `INTRAN_ACCT_BAL_DAILY` | `TSP_NO`, `INV_ACCT_ID`, `ACTIVITY_DATE` | Daily account balance |
| `INTRAN_ACCT_ACTIVITY` | `TSP_NO`, `INV_ACCT_ID`, `ACTIVITY_DATE`, `CTR_NO` | Account activity records |
| `INTRAN_ACCT_ACCUM_OIA_DTL` | `TSP_NO`, `INV_ACCT_ID`, (OIA keys) | OIA accumulation detail |

### View Tables (INTRAN_INV_*_VW)

| View | Source | Description |
|------|--------|-------------|
| `INTRAN_INV_ACTIVITY_VW` | Activity rollup | Monthly activity by Group/SubGroup/Qty |
| `INTRAN_INV_ACTIVITY_DAY_VW` | Activity rollup | Daily activity by Group/SubGroup/Qty |
| `INTRAN_INV_BALANCE_VW` | Balance rollup | Monthly balance summary |
| `INTRAN_INV_BALANCE_DAY_VW` | Balance rollup | Daily balance summary |

### Cross-Reference Tables (INXREF_*)

| Table | Description |
|-------|-------------|
| `INXREF_ACCT_TYPE_TOS_DTL` | Account type to Type of Service detail |
| `INXREF_ACCT_TRADE_RULE_CHECK` | Trade rule check cross reference |

### Report Tables (INRPTS_*)

| Table | Description |
|-------|-------------|
| `INRPTS_64_MTH_CUMU_IMB` | Monthly cumulative imbalance report |
| `INRPTS_65_DLY_CTR_OVER` | Daily contract overrun report |
| `INRPTS_66_UNA_DLY_CTR_OV_UN` | Unauthorized daily contract over/under report |

---

## Batch Processes

### INACCTACCM - Inventory Account Accumulation

**Process ID**: Referenced in QUICK_REFERENCE
**Purpose**: Accumulates allocation results into inventory account balances. This is the primary batch process that populates `INTRAN_ACCT_BAL` and `INTRAN_ACCT_ACTIVITY` from allocation data.

**Trigger**: Run after allocation processing completes

### INTRDPEND - Trade Pending

**Process ID**: `INTRDPEND`
**Launch Method**: `QPTMBatchProcessService.LaunchINTRDPEND_TradePending(tspNo, idAcctTrade, successStatCode, failStatCode)`
**Purpose**: Processes a trade from Pending to Confirmed status. Validates the trade and updates the status.

**Parameters**:
- `tspNo` - TSP number
- `idAcctTrade` - Trade ID
- `successTradeStatCode` - Status to set on success
- `failTradeStatCode` - Status to set on failure

**Triggered by**: Confirm action (both trades and storage transfers)

### INTRDTRANS (INCONFTRADE) - Trade Confirmation

**Process ID**: `INTRDTRANS`
**Launch Method**: `QPTMBatchProcessService.LaunchINCONFTRADE_TradeConfirmation(tspNo, idAcctTrade, successStatCode, failStatCode, acctMonth)`
**Purpose**: Processes a confirmed trade by updating account balances. Moves the trade to Processed status.

**Parameters**:
- `tspNo` - TSP number
- `idAcctTrade` - Trade ID
- `successTradeStatCode` - Status to set on success
- `failTradeStatCode` - Status to set on failure
- `dtAcctMonth` - Accounting month

**Triggered by**: Accept/Process action (both trades and storage transfers)

### INTRDWITH - Trade Withdrawal

**Process ID**: `INTRDWITH`
**Launch Method**: `QPTMBatchProcessService.LaunchINTRADEWITH_TradeWithdrawal(tspNo, idAcctTrade)`
**Purpose**: Reverses a pending trade and sets status to Withdrawn.

**Parameters**:
- `tspNo` - TSP number
- `idAcctTrade` - Trade ID

**Triggered by**: Withdraw action (both trades and storage transfers)

### INKASSIGN - IN Contract Assignment

**Launch Method**: `QPTMBatchProcessService.LaunchINKASSIGN_INContractAssignment(tspNo, contracts, assignCtrInvoiceGrp)`
**Purpose**: Assigns contracts to inventory accounts. Used during capacity release and RFS (Request for Service) approval.

---

## Caching

### InventoryCache

**Class**: `SingletonCache<InventoryCache>`

Cached operations:
- `GetInventoryAccountHdrsForContracts(tspNo, ctrNos, asOfDate)` - Account headers for contracts
- `GetInventoryTspConfig(tspNo, effDtFrom, effDtTo)` - TSP configuration
- `GetInventoryTspConfigs(tspNo)` - All TSP configurations
- `RefreshCacheForTable("INCTRL_TSP_CONFIG", ...)` - Cache invalidation after TSP config save

### QPTMTspOrGlobalConfigs

TSP-level or global configuration values:
- `GetImbalanceToleranceBasis(tspNo)` - Tolerance basis source (`REC` or delivery)
- `GetImbalanceTolerancePercent(tspNo)` - Tolerance percentage
- `FormulaIdInvRecDelDiffQty(tspNo)` - Monthly trade availability formula ID
- `FormulaIdInvRecDelDiffQtyDaily(tspNo)` - Daily trade availability formula ID

### QPTMTspConfigs

TSP-specific configuration:
- `AccountingMonthLagTime(tspNo)` - Lag between accounting and production months

---

## Configuration

### TSP-Level Configuration (`INCTRL_TSP_CONFIG`)

| Field | Description |
|-------|-------------|
| `TSP_NO` | TSP number |
| `EFF_DT_FROM` | Effective date from |
| `EFF_DT_TO` | Effective date to |
| `Y_DAY_CUTOFF_TIME` | Yesterday cutoff time for gas day |

### Global/TSP Configuration (`PACTRL_TSP_CNFG_CTRL`)

| Key Group | Key Name | Description |
|-----------|----------|-------------|
| TSP | `ACCTG_MTH_LAG_TIME` | Months between accounting and production |
| TSP | Imbalance tolerance % | Tolerance percentage |
| TSP | Imbalance tolerance basis | `REC` or delivery based |
| TSP | Formula ID (monthly) | User-defined formula for monthly trade availability |
| TSP | Formula ID (daily) | User-defined formula for daily trade availability |

### Contract-Level Configuration

| Field | Description |
|-------|-------------|
| `MonthlyTradeLagTime` | Number of months for trade lag calculation |
| `OperationalBalance` | Contract attribute indicating OBA vs standard account |
| `CtrMsq` / `CtrMsqMin` | Storage quantity limits |
| `FixedMDIQQty` / `FixedMDWQQty` | Fixed injection/withdrawal limits |

---

## Integration Points

### Upstream Dependencies

| System | Integration | Description |
|--------|-------------|-------------|
| **Allocations** | `INTRAN_ACCT_ACTIVITY` | Allocation results feed into inventory activity |
| **Contracts** | `IQContractDataAccess` | Contract headers provide lag time, MSQ, attributes |
| **Pipeline Admin** | `IQPipelineAdminDataAccess` | Open accounting month, roll types |
| **Nominations** | `IQPTMNominationWidget` | Widget service consumes nomination data |

### Downstream Consumers

| System | Integration | Description |
|--------|-------------|-------------|
| **Invoicing** | Balance data | Inventory balances feed invoicing/billing |
| **EDI** | Trade confirmations | EDI transactions for confirmed trades |
| **Reports** | `INRPTS_*` tables | Inventory reports consume balance/activity data |
| **Capacity Release** | `INKASSIGN` | Contract assignment during CR awards |
| **Dashboard** | Widget service | Real-time imbalance and storage balance display |

### Event System

**Event Context**: `QPTMINTradeTransferDetectorContext`
- Fired during `SubmitTrade` and `SubmitTransfer` operations
- `InvAcntTradeTransfer` - The trade/transfer being processed
- `UpdateSuccessful` - Set to true after successful save
- Handled via `ExecuteAndHandleEvents` pattern

**Event Project**: `Quorum.QPTM.Events.Inventory`

---

*Cross-references:*
- [Domain Documentation](./domain.md) - Business concepts and terminology
- [Troubleshooting Guide](./troubleshooting.md) - Known issues and diagnostic queries

*Last updated: 2026-03-03*

*Document version: 1.0*
