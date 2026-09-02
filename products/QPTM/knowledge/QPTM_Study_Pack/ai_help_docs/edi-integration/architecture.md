---
title: QPTM EDI Integration (EDI) - Architecture
category: architecture
feature: QPTM EDI Integration (EDI)
related_repos: Web, Batch
keywords: EDI, EDIService, EDTransactionController, QEDIDataAccess, QUIControllerEDTransaction, EDTransactionDO, EDTRAN_TRANSACTION, EDTpaHeader, EDDatasetFamily, IEDIService, QPTMServiceCore_EDTransaction, trading partner, outbound monitor, file management, ParseEDIFile
last_updated: 2026-03-03
---

# QPTM EDI Integration (EDI) - Architecture

## Overview

This document describes the **technical architecture** of EDI-related code in the Quorum.QPTM.Web repository. The Web repo provides EDI transaction viewing, trading partner configuration, and file management services that support the external EDIServ communication layer. The heavy-lifting EDI processing (parsing, translation, encryption) resides in the Batch repo.

For business concepts and terminology, see [Domain Documentation](./domain.md).
For troubleshooting issues, see [Troubleshooting Guide](./troubleshooting.md).

---

## Table of Contents

1. [Layer Architecture](#layer-architecture)
2. [EDIService (ServiceCore.EDI)](#ediservice-servicecoreedi)
3. [EDTransactionController (Web.Core)](#edtransactioncontroller-webcore)
4. [QUIControllerEDTransaction (UI Controller)](#quicontrolleredtransaction-ui-controller)
5. [Service Layer (QPTMServiceCore_EDTransaction)](#service-layer-qptmservicecore_edtransaction)
6. [Data Access Layer](#data-access-layer)
7. [Data Objects](#data-objects)
8. [Database Tables](#database-tables)
9. [View Models](#view-models)
10. [Views and Client-Side Code](#views-and-client-side-code)
11. [External NuGet Dependencies](#external-nuget-dependencies)
12. [Web-Side vs. Batch-Side Responsibilities](#web-side-vs-batch-side-responsibilities)
13. [Key File Paths and Configuration](#key-file-paths-and-configuration)
14. [Unit Tests](#unit-tests)

---

## Layer Architecture

```
+------------------------------------------------------------+
|  Web Layer                                                  |
|  EDTransactionController.cs (MVC Controller)                |
|  EDTransaction.cshtml / EDTransaction.js (View)             |
|  _TPAMaintenance_EDIServTab.cshtml (TPA Config)             |
+------------------------------------------------------------+
|  UI Controller Layer                                        |
|  QUIControllerEDTransaction.cs                              |
|    - Query filters, file content retrieval, EDI parsing     |
+------------------------------------------------------------+
|  Service Layer                                              |
|  QPTMServiceCore_EDTransaction.cs (query/update logic)      |
|  QPTMService_EDTransaction.cs (service proxy)               |
|  EDIService.cs (file management + EDIServ integration)      |
+------------------------------------------------------------+
|  Data Access Layer                                          |
|  QPTMDataAccess_EDTransaction (CodeGen - DB/Cache)          |
|  QEDIDataAccess.cs (EDI-specific - currently empty shell)   |
+------------------------------------------------------------+
|  DAL / Data Objects                                         |
|  EDTransactionDAL.cs (CodeGen - EDTRAN_TRANSACTION table)   |
|  EDTransactionDO.cs / EDTransactionDOExt.cs                 |
+------------------------------------------------------------+
|  Database                                                   |
|  EDTRAN_TRANSACTION table                                   |
|  ED_TPA_HEADER table                                        |
|  ED_DATASET_FAMILY table                                    |
+------------------------------------------------------------+
```

---

## EDIService (ServiceCore.EDI)

**File**: `Quorum.QPTM.ServiceCore.EDI/EDIService.cs` (187 lines)
**Namespace**: `Quorum.QPTM`
**Implements**: `EDIServiceCoreBase`, `IEDIService`

The `EDIService` class is the Web repo's primary integration point with the external EDIServ communication layer. It is registered as a WCF service via `EDIServiceServerContainer`.

### Methods

| Method | Purpose | Details |
|---|---|---|
| `QueueEdiFile(filename, fromDuns, toDuns)` | Queue an inbound EDI file for processing | Calls `IQPTMBatchProcessService.LaunchEDINCOMING_EDIncomingFileHandler()` with TspNo=-1 |
| `SaveEdiFile(fileName, fileContent)` | Save inbound EDI file to disk | Writes to `GlobalConfigsAccess.ProcessInEncryptedPath` |
| `GetOutboundMonitorFileList()` | List files ready for outbound send | Reads file names from `ProcessOutMonitorPath` directory |
| `GetOutboundFileContents(fileName)` | Retrieve outbound file content | Atomically deletes monitor file (with lock), reads encrypted file, moves to holdfiles |
| `MoveSentFile(encryptedFileName, bSuccess)` | Move file after send attempt | Moves from holdfiles to sentfiles (success) or errorhold (failure). Appends timestamp if file exists. |
| `GetAllTpaHeaderRecords()` | Retrieve active TPA records for EDIServ | Filters by effective dates, maps to `TradingPartner_Impl` objects |
| `GetEdiTransactionId()` | Generate next EDI transaction ID | Uses `QPTMServiceUtility.GetNextQFCSeqNo("EDI_TRANSACTION_ID", 1)` |

### Thread Safety

`GetOutboundFileContents` uses a static `fileLock` object to synchronize monitor file deletion across threads:

```csharp
private static readonly object fileLock = new object();

private static bool DeleteMonitorFileWithLock(string monitorFilePath)
{
    lock (fileLock)
    {
        if (!File.Exists(monitorFilePath)) return false;
        File.Delete(monitorFilePath);
        return true;
    }
}
```

### WCF Registration

```csharp
// EDIServiceServerContainer.cs
class EDIServiceServerContainer : QServiceContainerBase
{
    protected override void InitializeServices()
    {
        this.AddService<IEDIService>(() => new EDIService());
    }
}

// EDIServiceWA - WCF-decorated version
[QFCSecurityCheckServiceBehavior]
public class EDIServiceWA : EDIService { }
```

### Dependencies

- `IServiceProvider` -- For resolving `IQPTMBatchProcessService` and `IQPTMService_TPAMaintenance`
- `IQPTMGlobalConfigsAccess` -- For file path configuration (ProcessInEncryptedPath, ProcessOutMonitorPath, ProcessOutEncryptedPath, ProcessOutHoldfilesPath, ProcessOutSentfilesPath, ProcessOutErrorholdPath)

---

## EDTransactionController (Web.Core)

**File**: `Quorum.QPTM.Web.Core/Controllers/EDTransactionController.cs` (246 lines)
**Namespace**: `Quorum.QPTM.Web.Controllers`
**Security**: `[QScreenSecurityObject(Constants.SecurityObjectIDs.EDITransactionViewer)]` = `"QVPEDITRANSACTIONS"`
**Base**: `QMvcQPTMBaseScreenController<QUIControllerEDTransaction, EDTransactionRootVM>`

### Actions and Endpoints

| Endpoint | HTTP Method | Purpose |
|---|---|---|
| `GetActions` | -- | Returns action bar items (Retrieve only; Save/Validate/All/More removed) |
| `DoAction` | -- | Routes More and All actions to UI controller |
| `EDTransactionFieldUpdate` | POST | Handles non-grid field updates |
| `EDTransactionGetData` | POST | Returns grid data as `DataSourceResult` (Kendo grid) |
| `EDTransactionUpdate` | POST | Handles grid row updates |
| `EDTransactionHeaderSelectedObjectsChanged` | POST | Handles grid row selection changes |
| `EDTransactionExcelExport` | GET | Exports grid to Excel file (`EDITransactionHistory.xlsx`) |
| `EDTransactionRowChange` | POST | Retrieves EDI file content for the selected transaction row |

### Key Behavior: Read-Only Screen

The controller explicitly removes Save, Validate, All, and More buttons from the action bar in `GetActions()`, making this a **read-only** viewer:

```csharp
// remove buttons except retrieve
var validateButton = items.FirstOrDefault(x => x.Action == QStandardActions.Validate);
if (validateButton != null) items.Remove(validateButton);
var saveButton = items.FirstOrDefault(x => x.Action == QStandardActions.Save);
if (saveButton != null) items.Remove(saveButton);
```

### Parameter Transfer

The controller transfers these filter parameters between the view model and UI controller:
- `TspNo` -- Pipeline TSP number
- `EdDatasetFamilyCode` -- Dataset family filter
- `StatusCode` -- Transaction status filter
- `AsOfDateFrom` / `AsOfDateTo` -- Date range filter

---

## QUIControllerEDTransaction (UI Controller)

**File**: `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerEDTransaction.cs` (254 lines)
**Namespace**: `Quorum.QPTM.Controllers`
**Security**: `[QSecurityObject(Constants.SecurityObjectIDs.EDITransactionViewer)]`
**Base**: `QPTMBulkInterfaceControllerBase<EDTransactionDO>`

### Key Methods

#### `GetFileContents(filePath, fileNm)`
Retrieves and caches EDI file contents:
1. Checks in-memory cache (`cacheFileContents` dictionary)
2. If not cached, calls `IQPTMService_EDTransaction.GetEDIFile(filePath + "\\" + fileNm)`
3. If file found, calls `ParseEDIFile()` to format content
4. Caches result for subsequent requests

#### `ParseEDIFile(fileContents)`
Parses raw EDI content for display:
1. Reads element delimiter from position 3 of the file (ISA segment, character after "ISA")
2. Finds the 16th element to locate the segment delimiter
3. If the segment delimiter is not a line feed or carriage return, replaces all segment delimiters with `\r\n` for readable display

#### `DoQuery()`
Builds filter list and queries transactions:
1. Starts with TSP filter (`GetFiltersWithTsp`)
2. Adds optional filters: `EdDatasetFamilyCode`, `StatusCode`, `AsOfDateFrom`, `AsOfDateTo`
3. Date range: `AsOfDateFrom` set to 00:00:00.000, `AsOfDateTo` set to 23:59:59.999
4. Calls `Service.GetMultipleEDTransaction()`
5. Orders results by `TransactionDate` descending (newest first)

#### `DoNew()`
On new controller initialization:
1. Sets `TspNo` to the current TSP if not already set
2. Sets default parameters (date range = last 7 days)
3. Triggers a query

### Controller Parameters

The `QControllerParamsEDTransactionViewer` inner class registers these auto-push parameters:
- `EdDatasetFamilyCode` (string)
- `StatusCode` (string)
- `AsOfDateFrom` (DateTime?, default = Now - 7 days)
- `AsOfDateTo` (DateTime?, default = Now)

---

## Service Layer (QPTMServiceCore_EDTransaction)

**File**: `Quorum.QPTM.ServiceCore/QPTMServiceCore_EDTransaction.cs` (381 lines)
**Interface**: `IQPTMService_EDTransaction` (defined in `Quorum.QPTM.ServiceInterface`)

### Key Methods

| Method | Purpose |
|---|---|
| `GetSingleEDTransaction(TspNo, TransId)` | Query single transaction by PK |
| `GetMultipleEDTransaction(filters, ...)` | Query multiple transactions with filtering |
| `GetEDIFile(fileFullPath)` | Read EDI file content from disk |
| `UpdateSingleEDTransaction(updateItem)` | Save changes to a single transaction |
| `UpdateMultipleEDTransaction(updateList)` | Save changes to multiple transactions |

### Additional Properties Enrichment

`AddAdditionalPropertiesEDTransaction()` enriches `EDTransactionDO` objects with:
1. **Dataset Name**: Looks up `EDDatasetFamily.Description` from `EdDatasetFamilyCode`
2. **Trading Partner Name**: Resolves `TpaId` to `EDTpaHeader` to `BusinessAssociate.BpNm`

This performs efficient batch lookups:
- Retrieves distinct `EdDatasetFamilyCode` values, queries `EDDatasetFamily` once
- Retrieves distinct `TpaId` values, queries `EDTpaHeader` once
- Retrieves distinct `BpNo` values from TPA headers, queries `BusinessAssociate` once
- Builds dictionaries for O(1) lookups per record

### Data Access Dependencies

```csharp
private IQPTMDataAccess_EDDatasetFamily EDDatasetFamilyDataAccess { get; }
private IQPTMDataAccess_EDTpaHeader EDTpaHeaderDataAccess { get; }
private IQPTMDataAccess_EDTransaction EDTranDataAccess { get; }
```

---

## Data Access Layer

### QEDIDataAccess

**File**: `Quorum.QPTM.DataAccess/QEDIDataAccess.cs`
**Interface**: `IQEDIDataAccess`

Currently an **empty shell** class. The functional area documentation notes: "EDI = Trading Partners, EDI Datasets". Actual EDI transaction data access is handled through the CodeGen-generated `QPTMDataAccess_EDTransaction` class.

### QPTMDataAccess_EDTransaction (CodeGen)

**File**: `Quorum.QPTM.DataAccess/CodeGen/QPTMDataAccess_EDTransaction.cs`

Three implementations following the standard pattern:
1. **`QPTMDataAccess_EDTransaction_Db`** -- Direct database access via `EDTransactionDAL`
2. **`QPTMDataAccess_EDTransaction_Cache`** -- In-memory cache access
3. **`QPTMDataAccess_EDTransaction`** -- Config-based router that delegates to Cache or Db

Standard CRUD operations:
- `GetSingleEDTransaction(TspNo, TransId)`
- `GetMultipleEDTransaction(filters)` / `GetMultipleEDTransaction(FilterCollection)`
- `CheckExistsEDTransaction(filters)`
- `GetCountEDTransaction(filters)`
- `UpdateSingleEDTransaction(updateItem)`
- `UpdateMultipleEDTransaction(updateList)`
- `DeleteEDTransactionByFilter(filters)`

---

## Data Objects

### EDTransactionDO

**CodeGen File**: `Quorum.QPTM.DataObject/CodeGen/EDTransactionDO.cs`
**Extension File**: `Quorum.QPTM.DataObject/EDTransactionDOExt.cs`
**Table**: `EDTRAN_TRANSACTION`
**Primary Key**: `TspNo` + `TransId`

#### Properties (from CodeGen)

| Property | Type | Column | Description |
|---|---|---|---|
| `TspNo` | short | TSP_NO | TSP number (PK) |
| `TransId` | int | TRANS_ID | Transaction ID (PK) |
| `ParentTransId` | int? | PARENT_TRANS_ID | Parent transaction link |
| `TpaId` | int | TPA_ID | Trading partner agreement ID |
| `EdDatasetFamilyCode` | string | ED_DATASET_FAMILY_CD | Dataset family code |
| `TransactionDate` | DateTime? | TRANSACTION_DATE | When the transaction occurred |
| `DirCode` | string | DIR_CD | Direction code (inbound/outbound) |
| `IsTest` | bool? | IS_TEST | Test transaction flag |
| `StatusCode` | string | STATUS_CD | Transaction status |
| `ErrorCode` | string | ERROR_CD | Error code if failed |
| `RefNo` | string | REF_NO | Reference number |
| `FilePath` | string | FILE_PATH | File directory path |
| `FileNm` | string | FILE_NM | File name |
| `ParentRefNo` | string | PARENT_REF_NO | Parent reference number |
| `ProcessQueueId` | int? | PROCESS_QUEUE_ID | Batch process queue ID |

#### Extension Properties (from DOExt)

| Property | Type | Description |
|---|---|---|
| `TradingPartnerName` | string | Business partner name (resolved from TpaId) |
| `DatasetName` | string | Dataset family description (resolved from EdDatasetFamilyCode) |

#### Extension Constants (from DOExt)

```csharp
public static partial class QEDTransactionConstants
{
    public static partial class PropertyNames
    {
        public const string AsOfDateFrom = "AsOfDateFrom";
        public const string AsOfDateTo = "AsOfDateTo";
    }
}
```

---

## Database Tables

### EDTRAN_TRANSACTION

Primary table for EDI transaction history. Maps to `EDTransactionDO`.

| Column | Type | Key | Description |
|---|---|---|---|
| TSP_NO | smallint | PK | TSP number |
| TRANS_ID | int | PK | Transaction ID |
| PARENT_TRANS_ID | int | | Parent transaction |
| TPA_ID | int | | Trading partner ID |
| ED_DATASET_FAMILY_CD | varchar(8) | | Dataset family code |
| TRANSACTION_DATE | datetime | | Transaction timestamp |
| DIR_CD | varchar | | Direction (I/O) |
| IS_TEST | bit | | Test flag |
| STATUS_CD | varchar(3) | | Status code |
| ERROR_CD | varchar | | Error code |
| REF_NO | varchar | | Reference number |
| FILE_PATH | varchar | | File path |
| FILE_NM | varchar | | File name |
| PARENT_REF_NO | varchar | | Parent reference |
| PROCESS_QUEUE_ID | int | | Process queue ID |

### Related Tables

- **ED_TPA_HEADER** -- Trading partner agreement configuration (maps to `EDTpaHeaderDO`)
- **ED_DATASET_FAMILY** -- Dataset family code table (maps to `EDDatasetFamilyDO`)
- **BUSINESS_ASSOCIATE** -- Business associate information for resolving partner names

---

## View Models

### EDTransactionRootVM

**File**: `Quorum.QPTM.Web.Core/ViewModels/EDTransactionRootVM.cs`

Screen-level view model for filter parameters:

| Property | Type | Description |
|---|---|---|
| `TspNo` | short | TSP filter |
| `EdDatasetFamilyCode` | string | Dataset family filter |
| `StatusCode` | string | Status filter |
| `AsOfDateFrom` | DateTime? | Date range start |
| `AsOfDateTo` | DateTime? | Date range end |
| `FileContent` | string | EDI file content for viewer |

### EDTransactionVM / EDTransactionVMExt

**CodeGen File**: `Quorum.QPTM.Web.Core/ViewModels/CodeGen/EDTransactionVM.cs`
**Extension File**: `Quorum.QPTM.Web.Core/ViewModels/EDTransactionVMExt.cs`

Grid-level view model. Extension adds:
- `TradingPartnerName` (string)
- `DatasetName` (string)

---

## Views and Client-Side Code

### EDTransaction.cshtml

**File**: `Quorum.QPTM.Web/Views/EDTransaction/EDTransaction.cshtml`

Layout: `layout--content-double-major-minor-filter` with side-by-side content panels

**Filter Section:**
- TSP dropdown (required)
- Dataset Family code table dropdown
- Status Code dropdown
- As Of Date From / To date pickers

**Grid Section:**
- Grid ID: `EDITransactionHistoryGrid` (Constants.GridIDs = 30125)
- Grid toolbar title: "EDI Transaction History"
- Read-only grid (no bulk edit, no copy/paste, no import, no delete, no duplicate)
- Excel export enabled
- Row change event triggers file content load

**EDI Viewer Section:**
- Text area displaying selected transaction's file content
- Copy button to copy content to clipboard

### EDTransaction.js

**File**: `Quorum.QPTM.Web/Scripts/EDTransaction/EDTransaction.js`

Two functions:
- `EDTransactionRowChange()` -- AJAX POST to `EDTransactionRowChange` endpoint; displays file content in textarea
- `CopyFileContentToClipboard()` -- Copies textarea content to clipboard with toast notification

### TPA Maintenance EDI Serv Tab

**File**: `Quorum.QPTM.Web/Views/TPAMaintenance/_TPAMaintenance_EDIServTab.cshtml`

Configures trading partner EDI settings across four sections:
- General (PartUser, PartPwd, NaesbVersion)
- Primary Connection (PrimDuns, PrimIp, PrimCgiExec, PrimPort, PrimUser, PrimPwd, PrimUsessl)
- Secondary Connection (SecDuns, SecIp, SecCgiExec, SecPort, SecUser, SecPwd, SecUsessl)
- HTTP Response (HttpResponseExtraLines, HttpResponseContentLength, HttpResponseSignature)

---

## External NuGet Dependencies

The Web repo consumes these EDI-related NuGet packages:

| Package | Version | Purpose |
|---|---|---|
| `Quorum.EDI.GPGInterface` | 17.6.0 - 17.8.0 | GPG encryption/decryption interface |
| `Quorum.EDI.PrivacyService` | 17.6.0 - 17.8.0 | Privacy/encryption service |
| `Quorum.EDI.ServiceInterface` | 17.6.0 - 17.8.0 | `IEDIService` interface, `TradingPartner_Impl` |
| `Quorum.EDI.ServiceCore` | 17.6.0 - 17.8.0 | `EDIServiceCoreBase` base class |

---

## Web-Side vs. Batch-Side Responsibilities

### Web Repo Handles

1. **EDI Transaction Viewer** -- Read-only screen to view transaction history and file content
2. **TPA Maintenance** -- Configure trading partner connection parameters
3. **EDIService WCF Endpoint** -- File save, queue, outbound file management, TPA retrieval
4. **EDI Transaction ID Generation** -- Sequence-based ID generation

### Batch Repo Handles (Reference Only)

1. **EDINCOMING** -- Inbound EDI file processing (decrypt, parse, translate, load to QPTM data)
2. **QPEC** -- Outbound EDI file generation (extract QPTM data, translate, encrypt)
3. **GPG Encryption/Decryption** -- Actual crypto operations
4. **EDI Dataset Translation** -- Mapping between EDI X12 segments and QPTM data objects
5. **Batch Job Scheduling** -- Automated EDI processing cycles

---

## Key File Paths and Configuration

Managed through `IQPTMGlobalConfigsAccess`:

| Config Property | Purpose |
|---|---|
| `ProcessInEncryptedPath` | Directory for saving inbound encrypted files |
| `ProcessOutMonitorPath` | Directory containing outbound monitor files (ready to send) |
| `ProcessOutEncryptedPath` | Directory containing outbound encrypted files |
| `ProcessOutHoldfilesPath` | Directory for files retrieved but not yet confirmed sent |
| `ProcessOutSentfilesPath` | Directory for successfully sent files |
| `ProcessOutErrorholdPath` | Directory for files that failed to send |

**File Flow Directories (Outbound):**
```
QPEC generates: Decrypted -> Encrypted -> Monitor
EDIService reads: Monitor (delete) + Encrypted (read) -> Holdfiles
After send:   Holdfiles -> Sentfiles (success) or Errorhold (failure)
```

---

## Unit Tests

**File**: `Quorum.QPTM.UnitTests/ServiceCore/EDIServiceTests.cs`
**Test Categories**: `SuperDomain_Data Exchange`, `Domain_Electronic Data Interchange (EDI)`

| Test | Verifies |
|---|---|
| `EDIServiceTests_GetAllTpaHeaderRecords_1` | Basic TPA header retrieval with DUNS mapping |
| `EDIServiceTests_GetAllTpaHeaderRecords_2` | TPA retrieval with BusinessAssociate DUNS resolution |
| `EDIServiceTests_GetAllTpaHeaderRecords_CodeCoverage` | Non-nullable TradingPartner_Impl field coverage |
| `EDIServiceTests_SaveEdiFile` | File save to ProcessInEncryptedPath |
| `EDIServiceTests_GetAllEDIFiles` | Outbound monitor file list retrieval |
| `EDIServiceTests_GetSingleEDIFile` | Outbound file content retrieval + monitor deletion + holdfile move |
| `EDIServiceTests_MoveSentFile_successful_1` | File move from holdfiles to sentfiles |
| `EDIServiceTests_MoveSentFile_successful_2` | File move when file already exists (timestamp append) |
| `EDIServiceTests_MoveSentFile_unsuccessful_2` | File move to errorhold on failure |
| `EDIServiceTest_QueueEdiFile` | Queue inbound file via EDINCOMING launch |

**Test EDI Files**: `Quorum.QPTM.UnitTests/EDTransaction/TestEDIFile_01.dec`, `TestEDIFile_02.dec`, `TestEDIFile_03.dec`

---

*See also: [Domain Documentation](./domain.md) | [Troubleshooting Guide](./troubleshooting.md)*

*Last updated: 2026-03-03*

*Document version: 1.0*
