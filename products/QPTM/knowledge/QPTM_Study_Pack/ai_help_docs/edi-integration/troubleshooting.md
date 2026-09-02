---
title: QPTM EDI Integration (EDI) - Troubleshooting Guide
category: troubleshooting
feature: QPTM EDI Integration (EDI)
related_repos: Web, Batch
keywords: EDI, troubleshooting, EDI transaction viewer, file not found, trading partner, TPA, outbound, inbound, monitor file, hold file, ParseEDIFile, status code, error code, EDTRAN_TRANSACTION, dataset family, EDINCOMING, file locking, encryption
last_updated: 2026-03-03
---

# QPTM EDI Integration (EDI) - Troubleshooting Guide

## Overview

This document provides troubleshooting guidance for EDI-related issues encountered in the Quorum.QPTM.Web application. Since the Web repo focuses on **viewing and monitoring** EDI activity (not primary processing), most issues here relate to the EDI Transaction Viewer screen, file display problems, and trading partner configuration.

For business concepts, see [Domain Documentation](./domain.md).
For technical architecture, see [Architecture Documentation](./architecture.md).

> **Note**: Issues related to EDI file parsing, translation, encryption/decryption, and batch processing should be investigated in the **Quorum.QPTM.Batch** repository.

---

## Table of Contents

1. [EDI Transaction Viewer Issues](#edi-transaction-viewer-issues)
2. [EDI File Content Display Issues](#edi-file-content-display-issues)
3. [Outbound File Management Issues](#outbound-file-management-issues)
4. [Trading Partner (TPA) Configuration Issues](#trading-partner-tpa-configuration-issues)
5. [Inbound File Queuing Issues](#inbound-file-queuing-issues)
6. [Diagnostic SQL Queries](#diagnostic-sql-queries)
7. [Key Files for Investigation](#key-files-for-investigation)
8. [Common Error Patterns](#common-error-patterns)
9. [Escalation Guidelines](#escalation-guidelines)

---

## EDI Transaction Viewer Issues

### No Transactions Displayed

**Symptoms**: The EDI Transaction History grid is empty after clicking Retrieve.

**Investigation Steps**:
1. **Check TSP selection**: TSP is required. Verify the correct TSP is selected.
2. **Check date range**: The default range is last 7 days. Expand the date range to verify data exists.
3. **Check filters**: Clear the Dataset Family and Status Code filters to rule out overly restrictive filtering.
4. **Verify data exists in the database**:

```sql
SELECT TOP 100 *
FROM EDTRAN_TRANSACTION
WHERE TSP_NO = @TspNo
ORDER BY TRANSACTION_DATE DESC;
```

5. **Check user permissions**: The user must have access to the `QVPEDITRANSACTIONS` security object.

**Root Cause Possibilities**:
- No EDI transactions exist for the selected TSP and date range
- The batch process (EDINCOMING / QPEC) is not running or not creating transaction records
- User lacks security access to the EDI Transaction Viewer screen

### Transactions Load Slowly

**Symptoms**: The grid takes a long time to load results.

**Investigation Steps**:
1. **Check date range**: A very wide date range returns many records. Narrow the date range.
2. **Check record count**: The controller uses `limitedRecordCount` logic. If `numRecordsToReturn` is set and exceeded, an extra record is fetched and trimmed.
3. **Check index usage**:

```sql
-- Verify indexes exist on EDTRAN_TRANSACTION
SELECT name, type_desc
FROM sys.indexes
WHERE object_id = OBJECT_ID('EDTRAN_TRANSACTION');

-- Check query plan for slow filter combinations
SET STATISTICS IO ON;
SELECT *
FROM EDTRAN_TRANSACTION
WHERE TSP_NO = @TspNo
  AND TRANSACTION_DATE BETWEEN @DateFrom AND @DateTo
ORDER BY TRANSACTION_DATE DESC;
SET STATISTICS IO OFF;
```

### Trading Partner Name or Dataset Name Shows as Blank

**Symptoms**: The TradingPartnerName or DatasetName columns in the grid display empty values.

**Investigation Steps**:
1. The service enriches these fields via `AddAdditionalPropertiesEDTransaction()` in `QPTMServiceCore_EDTransaction.cs`.
2. **Check TPA header data**:

```sql
-- Verify TPA header exists for the TpaId
SELECT h.*, ba.BP_NM
FROM ED_TPA_HEADER h
LEFT JOIN BUSINESS_ASSOCIATE ba ON h.BP_NO = ba.BP_NO
WHERE h.ID_TPA = @TpaId AND h.TSP_NO = @TspNo;
```

3. **Check dataset family data**:

```sql
-- Verify dataset family description exists
SELECT * FROM ED_DATASET_FAMILY
WHERE CODE = @EdDatasetFamilyCode;
```

**Root Cause Possibilities**:
- The `TpaId` on the transaction record does not match any active TPA header
- The `EdDatasetFamilyCode` does not exist in the `ED_DATASET_FAMILY` table
- The TPA header's `BpNo` does not match any record in `BUSINESS_ASSOCIATE`

---

## EDI File Content Display Issues

### "No EDI file found." Message

**Symptoms**: Selecting a transaction row displays "No EDI file found." instead of file content.

**Investigation Steps**:
1. **Check file path and name on the transaction**:

```sql
SELECT TRANS_ID, FILE_PATH, FILE_NM, STATUS_CD
FROM EDTRAN_TRANSACTION
WHERE TSP_NO = @TspNo AND TRANS_ID = @TransId;
```

2. **Verify the file exists on disk**: Check that `FILE_PATH + "\" + FILE_NM` exists on the server's file system.
3. **Check file permissions**: The IIS application pool identity must have read access to the file path.

**Root Cause Possibilities**:
- The EDI file has been archived, deleted, or moved from its original location
- The `FilePath` or `FileNm` columns contain null or incorrect values
- File system permissions prevent the web application from reading the file

**Code Reference** (`QUIControllerEDTransaction.cs`):
```csharp
fileContents = this.ServiceProvider.GetService<IQPTMService_EDTransaction>()
    .GetEDIFile(filePath + "\\" + fileNm);
if (fileContents.IsNullOrEmpty())
{
    fileContents = "No EDI file found.";
}
```

### File Content Displays as Single Line / Garbled

**Symptoms**: The EDI file content appears as one long line without segment separation.

**Investigation Steps**:
1. The `ParseEDIFile()` method attempts to detect the segment delimiter from the ISA segment.
2. If the file is shorter than 4 characters or the ISA segment is malformed, parsing may fail silently.
3. Check the raw file content to identify the actual segment delimiter character.

**Root Cause Possibilities**:
- The EDI file does not follow standard X12 ISA segment format
- The segment delimiter is in an unexpected position
- The file is encrypted or corrupted

**Code Reference** (`QUIControllerEDTransaction.cs`):
```csharp
// Element delimiter is at position 3 (character after "ISA")
elementDelimiter = fileContents.Substring(3, 1)[0];
// Segment delimiter is found after the 16th element in the ISA segment
```

### File Content Not Updating When Selecting Different Rows

**Symptoms**: The EDI Viewer shows the same content regardless of which row is selected.

**Investigation Steps**:
1. Check the file content cache in `QUIControllerEDTransaction`. Files are cached by `FileNm` in a `Dictionary<string, string>`.
2. If two transactions reference the same file name but different paths, the cached version is returned.
3. Check browser console for AJAX errors on the `EDTransactionRowChange` POST.

**Root Cause**: The in-memory `cacheFileContents` dictionary keys by file name only (not full path). If multiple transactions have the same file name but different paths, the first-loaded file persists in cache for the session.

---

## Outbound File Management Issues

### Outbound Monitor File List is Empty

**Symptoms**: `EDIService.GetOutboundMonitorFileList()` returns no files.

**Investigation Steps**:
1. **Check monitor directory exists**: Verify `GlobalConfigsAccess.ProcessOutMonitorPath` returns a valid path.
2. **Check directory contents**: Verify files exist in the monitor directory on the server.
3. **Check QPEC batch process**: The Batch repo's QPEC process creates monitor files. If QPEC is not running, no monitor files will be created.

### Outbound File Content Returns Null

**Symptoms**: `EDIService.GetOutboundFileContents()` returns null.

**Investigation Steps**:
1. **Monitor file already deleted**: Another process or thread may have already consumed the monitor file. The method uses `DeleteMonitorFileWithLock()` which returns false if the file does not exist.
2. **Encrypted file missing**: After deleting the monitor file, the method checks for the encrypted file. If missing, it returns empty string (not null -- null indicates monitor file was already gone).

**Root Cause Possibilities**:
- Race condition: multiple threads/processes tried to retrieve the same outbound file simultaneously
- Manual file manipulation on the server
- QPEC created monitor file but failed to create encrypted file
- Wrong `ProcessOutEncryptedPath` configuration

### File Move Fails After Send

**Symptoms**: `EDIService.MoveSentFile()` does not move files as expected.

**Investigation Steps**:
1. **Hold file does not exist**: If the hold file is missing, the method returns silently.
2. **Target directory does not exist**: Check `ProcessOutSentfilesPath` (success) or `ProcessOutErrorholdPath` (failure).
3. **Duplicate file name**: If a file with the same name exists at the target, a timestamp suffix (`_yyyyMMdd_HHmmssfff`) is appended.
4. **File permissions**: The application pool identity must have write access to target directories.

---

## Trading Partner (TPA) Configuration Issues

### TPA Records Not Appearing in EDIServ

**Symptoms**: EDIServ does not see expected trading partners from `GetAllTpaHeaderRecords()`.

**Investigation Steps**:
1. **Check effective dates**: The method filters by `EffDateFrom <= Now` and `EffDateTo >= Now`. Expired or future TPA records are excluded.

```sql
SELECT *
FROM ED_TPA_HEADER
WHERE EFF_DATE_FROM <= GETDATE()
  AND EFF_DATE_TO >= GETDATE();
```

2. **Check TPA Maintenance screen**: Verify the TPA record exists and has correct effective dates.
3. **Verify DUNS numbers**: EDIServ identifies partners by `BpDunsNo` and `TspDunsNo`.

### TPA Connection Parameters Incorrect

**Symptoms**: EDI send/receive fails due to connection issues.

**Investigation Steps**:
1. Open TPA Maintenance and navigate to the EDI Serv tab.
2. Verify Primary Connection settings: IP, Port, CGI Exec path, User/Password, SSL flag.
3. If primary fails, verify Secondary Connection as failover.
4. Check the NAESB Version field -- must match what the trading partner expects.

---

## Inbound File Queuing Issues

### QueueEdiFile Returns False

**Symptoms**: `EDIService.QueueEdiFile()` returns false, indicating the EDINCOMING batch process could not be launched.

**Investigation Steps**:
1. Verify `IQPTMBatchProcessService` is properly registered in the service container.
2. Check batch process service availability and configuration.
3. Review application logs for errors from `LaunchEDINCOMING_EDIncomingFileHandler()`.

### SaveEdiFile Fails

**Symptoms**: `EDIService.SaveEdiFile()` throws an exception.

**Investigation Steps**:
1. Check `GlobalConfigsAccess.ProcessInEncryptedPath` configuration.
2. Verify the target directory exists and is writable.
3. Check for disk space issues on the server.

---

## Diagnostic SQL Queries

### View Recent EDI Transactions

```sql
-- Recent transactions for a TSP
SELECT TOP 100
    t.TSP_NO,
    t.TRANS_ID,
    t.ED_DATASET_FAMILY_CD,
    t.TRANSACTION_DATE,
    t.DIR_CD,
    t.STATUS_CD,
    t.ERROR_CD,
    t.REF_NO,
    t.FILE_PATH,
    t.FILE_NM,
    t.TPA_ID,
    t.PARENT_TRANS_ID,
    t.PARENT_REF_NO
FROM EDTRAN_TRANSACTION t
WHERE t.TSP_NO = @TspNo
ORDER BY t.TRANSACTION_DATE DESC;
```

### View Transactions by Status

```sql
-- Find failed transactions
SELECT *
FROM EDTRAN_TRANSACTION
WHERE TSP_NO = @TspNo
  AND STATUS_CD = 'ERR'
  AND TRANSACTION_DATE >= DATEADD(DAY, -7, GETDATE())
ORDER BY TRANSACTION_DATE DESC;
```

### View Transactions by Dataset Family

```sql
-- Transactions for a specific dataset family
SELECT *
FROM EDTRAN_TRANSACTION
WHERE TSP_NO = @TspNo
  AND ED_DATASET_FAMILY_CD = @DatasetFamilyCode
  AND TRANSACTION_DATE BETWEEN @DateFrom AND @DateTo
ORDER BY TRANSACTION_DATE DESC;
```

### Check Trading Partner Configuration

```sql
-- Active TPA headers with business associate info
SELECT
    h.ID_TPA,
    h.TSP_NO,
    h.BP_NO,
    ba.BP_NM,
    h.BP_DUNS_NO,
    h.TSP_DUNS_NO,
    h.EFF_DATE_FROM,
    h.EFF_DATE_TO,
    h.NAESB_VERSION,
    h.PRIM_IP,
    h.PRIM_PORT,
    h.PRIM_USESSL
FROM ED_TPA_HEADER h
LEFT JOIN BUSINESS_ASSOCIATE ba ON h.BP_NO = ba.BP_NO
WHERE h.EFF_DATE_FROM <= GETDATE()
  AND h.EFF_DATE_TO >= GETDATE()
ORDER BY h.TSP_NO, ba.BP_NM;
```

### Check Dataset Family Definitions

```sql
-- All dataset families
SELECT CODE, DESCRIPTION
FROM ED_DATASET_FAMILY
ORDER BY CODE;
```

### Find Parent-Child Transaction Relationships

```sql
-- Find 997/FA responses and their parent transactions
SELECT
    child.TRANS_ID AS ChildTransId,
    child.ED_DATASET_FAMILY_CD AS ChildDataset,
    child.STATUS_CD AS ChildStatus,
    parent.TRANS_ID AS ParentTransId,
    parent.ED_DATASET_FAMILY_CD AS ParentDataset,
    parent.STATUS_CD AS ParentStatus
FROM EDTRAN_TRANSACTION child
INNER JOIN EDTRAN_TRANSACTION parent
    ON child.PARENT_TRANS_ID = parent.TRANS_ID
    AND child.TSP_NO = parent.TSP_NO
WHERE child.TSP_NO = @TspNo
  AND child.TRANSACTION_DATE >= DATEADD(DAY, -7, GETDATE())
ORDER BY child.TRANSACTION_DATE DESC;
```

### Transaction Volume by Day

```sql
-- Transaction counts per day
SELECT
    CAST(TRANSACTION_DATE AS DATE) AS TransDate,
    DIR_CD,
    ED_DATASET_FAMILY_CD,
    STATUS_CD,
    COUNT(*) AS TransCount
FROM EDTRAN_TRANSACTION
WHERE TSP_NO = @TspNo
  AND TRANSACTION_DATE >= DATEADD(DAY, -30, GETDATE())
GROUP BY CAST(TRANSACTION_DATE AS DATE), DIR_CD, ED_DATASET_FAMILY_CD, STATUS_CD
ORDER BY TransDate DESC, DIR_CD, ED_DATASET_FAMILY_CD;
```

---

## Key Files for Investigation

| File | Path | Purpose |
|---|---|---|
| EDIService.cs | `Quorum.QPTM.ServiceCore.EDI/EDIService.cs` | File management, TPA retrieval, queue inbound |
| EDTransactionController.cs | `Quorum.QPTM.Web.Core/Controllers/EDTransactionController.cs` | MVC controller for EDI Transaction Viewer |
| QUIControllerEDTransaction.cs | `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerEDTransaction.cs` | UI controller with query, file parsing, caching |
| QPTMServiceCore_EDTransaction.cs | `Quorum.QPTM.ServiceCore/QPTMServiceCore_EDTransaction.cs` | Service layer with additional property enrichment |
| EDTransactionDOExt.cs | `Quorum.QPTM.DataObject/EDTransactionDOExt.cs` | Extension properties (TradingPartnerName, DatasetName) |
| EDTransaction.cshtml | `Quorum.QPTM.Web/Views/EDTransaction/EDTransaction.cshtml` | View template |
| EDTransaction.js | `Quorum.QPTM.Web/Scripts/EDTransaction/EDTransaction.js` | Client-side row change and clipboard |
| _TPAMaintenance_EDIServTab.cshtml | `Quorum.QPTM.Web/Views/TPAMaintenance/_TPAMaintenance_EDIServTab.cshtml` | TPA EDI configuration tab |
| EDIServiceTests.cs | `Quorum.QPTM.UnitTests/ServiceCore/EDIServiceTests.cs` | Unit tests for EDIService |

---

## Common Error Patterns

### Pattern 1: Stale File References

**Symptom**: Transaction records reference files that no longer exist on disk.
**Cause**: Files were archived, purged, or moved by a separate maintenance process.
**Resolution**: Check file retention policies and ensure `FILE_PATH` values are still valid. Consider updating database records or restoring files from backup.

### Pattern 2: Monitor File / Encrypted File Mismatch

**Symptom**: Outbound monitor files exist but corresponding encrypted files do not (or vice versa).
**Cause**: QPEC batch process partially completed, or files were manually manipulated.
**Resolution**: Check the QPEC batch process logs in the Batch repo. Orphaned monitor files can be manually deleted. Orphaned encrypted files will remain until manually cleaned.

### Pattern 3: Duplicate Outbound Files

**Symptom**: Multiple copies of the same file appear in sentfiles with timestamp suffixes.
**Cause**: `MoveSentFile()` appends `_yyyyMMdd_HHmmssfff` when a file with the same name exists. This can happen when the same file is reprocessed.
**Resolution**: This is expected behavior. Review the duplicate files to determine if reprocessing was intentional or indicates an issue in the batch pipeline.

### Pattern 4: Thread Contention on Monitor Files

**Symptom**: Intermittent null returns from `GetOutboundFileContents()`.
**Cause**: Multiple threads calling `GetOutboundFileContents()` simultaneously. The file lock prevents double-processing but the losing thread gets a null return.
**Resolution**: This is expected behavior. The calling code should handle null returns gracefully (the file was already picked up by another thread).

---

## Escalation Guidelines

| Issue Type | Investigate In | Escalate To |
|---|---|---|
| Transaction Viewer display issues | Web repo (this doc) | Web team |
| TPA configuration issues | Web repo (TPA Maintenance) | Web team / Pipeline admin |
| Inbound file parsing failures | Batch repo (EDINCOMING) | Batch team |
| Outbound file generation failures | Batch repo (QPEC) | Batch team |
| Encryption/decryption failures | Batch repo (GPG/Privacy) | Batch team / Security team |
| File system permission issues | Server infrastructure | Infrastructure team |
| EDI protocol/NAESB compliance | Batch repo + business rules | EDI team / Business analysts |
| Database performance | DBA | Database team |

---

*See also: [Domain Documentation](./domain.md) | [Architecture Documentation](./architecture.md)*

*Last updated: 2026-03-03*

*Document version: 1.0*
