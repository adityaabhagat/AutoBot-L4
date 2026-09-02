---
title: "Invoice Management (INVC) - Troubleshooting Guide"
category: "troubleshooting"
feature: "INVC"
related_repos:
  - "Quorum.QPTM.Web"
  - "Quorum.QPTM.Batch"
keywords:
  - invoice
  - billing
  - invoice maintenance
  - troubleshooting
  - invoice status
  - posting
  - external user
  - missing data
  - invoice group
  - BLROLLPER
  - validation error
  - FillSubDetails
  - performance
last_updated: 2026-03-03
---

# Invoice Management (INVC) - Troubleshooting Guide

## Table of Contents

- [Common Issues](#common-issues)
  - [INVC-001: Invoice Maintenance Screen Shows No Data After Query](#invc-001-invoice-maintenance-screen-shows-no-data-after-query)
  - [INVC-002: External User Cannot See Expected Invoices](#invc-002-external-user-cannot-see-expected-invoices)
  - [INVC-003: Cannot Change Invoice Status - Final Status Error](#invc-003-cannot-change-invoice-status---final-status-error)
  - [INVC-004: Cannot Post Invoice - Status Validation Error](#invc-004-cannot-post-invoice---status-validation-error)
  - [INVC-005: Invoice Amounts Incorrect or Missing on Header by Contract Tab](#invc-005-invoice-amounts-incorrect-or-missing-on-header-by-contract-tab)
  - [INVC-006: Sub-Detail Records Missing Rate Type, TOC Description, or Tier Description](#invc-006-sub-detail-records-missing-rate-type-toc-description-or-tier-description)
  - [INVC-007: Save Fails with InvoiceStatCode Required Error](#invc-007-save-fails-with-invoicestatcode-required-error)
  - [INVC-008: BLROLLPER Batch Process Fails During Posting](#invc-008-blrollper-batch-process-fails-during-posting)
  - [INVC-009: Detail Status Not Updated After Header Status Change](#invc-009-detail-status-not-updated-after-header-status-change)
  - [INVC-010: Sub-Detail by TOC Tab Shows Incorrect Aggregated Values](#invc-010-sub-detail-by-toc-tab-shows-incorrect-aggregated-values)
  - [INVC-011: Invoice Report Does Not Generate](#invc-011-invoice-report-does-not-generate)
  - [INVC-012: Cannot Close Future Accounting Month Invoices](#invc-012-cannot-close-future-accounting-month-invoices)
  - [INVC-013: Performance Issues on Invoice Maintenance Query](#invc-013-performance-issues-on-invoice-maintenance-query)
  - [INVC-014: External User Permission Error on Save](#invc-014-external-user-permission-error-on-save)
  - [INVC-015: Header by Contract Tab Not Loading Details](#invc-015-header-by-contract-tab-not-loading-details)
- [Diagnostic SQL Queries](#diagnostic-sql-queries)
- [Code Locations Reference](#code-locations-reference)
- [Related Documentation](#related-documentation)

---

## Common Issues

### INVC-001: Invoice Maintenance Screen Shows No Data After Query

**Symptoms**: User enters query parameters and clicks Query, but all grids remain empty.

**Common Causes**:
1. No invoices exist for the specified AcctgMth/BpNo combination
2. Missing `BLXREF_LAST_INVOICE_GRP_RUN` cross-reference records (headers are filtered out during join)
3. For external users: no contract agent relationships link the user's BP to any invoices

**Diagnostic Steps**:
1. Verify invoice data exists in the database:
```sql
-- Check if headers exist for the given filters
SELECT * FROM BLTRAN_INVOICE_HDR
WHERE TSP_NO = @TspNo
  AND ACCTG_MTH = @AcctgMth
  AND BP_NO = @BpNo;
```

2. Verify billing run cross-reference exists:
```sql
-- Check if xref records exist for matching headers
SELECT x.*
FROM BLXREF_LAST_INVOICE_GRP_RUN x
INNER JOIN BLTRAN_INVOICE_HDR h
  ON x.TSP_NO = h.TSP_NO
  AND x.INVOICE_GRP_ID = h.INVOICE_GRP_ID
  AND x.ACCTG_MTH = h.ACCTG_MTH
  AND x.PROCESS_QUEUE_ID = h.PROCESS_QUEUE_ID
  AND x.BILL_PERIOD_ID = h.BILL_PERIOD_ID
WHERE h.TSP_NO = @TspNo
  AND h.ACCTG_MTH = @AcctgMth;
```

3. For external users, verify the contract agent chain (see INVC-002).

**Code Location**: `QPTMServiceCore_InvoiceMaintenance.cs` -> `AddAdditionalPropertiesInvoiceMaintenanceHeader()` (line ~320)

**Resolution**: Ensure billing runs have completed and xref records are populated. If xref records are missing, a billing rerun may be needed.

---

### INVC-002: External User Cannot See Expected Invoices

**Symptoms**: An external user (shipper/agent) queries invoices but sees fewer records than expected, or no records at all.

**Common Causes**:
1. User's Business Partner (BP) is not linked to the appropriate contracts via the ContractAgent table
2. Contract agent effective dates do not cover the invoice accounting month
3. Contract or contract amendment effective dates are expired
4. Invoice group has only internal delivery method (INT) copies, excluding it from external views
5. User does not have a default BP assigned

**Diagnostic Steps**:
1. Check the user's BP assignment:
```sql
-- Find the user's BP list
SELECT * FROM USER_BP
WHERE USER_ID = @UserId;
```

2. Verify contract agent relationships:
```sql
-- Check contract agents for the user's BP
SELECT ca.*
FROM CTR_AGENT ca
WHERE ca.TSP_NO = @TspNo
  AND ca.AGENT_BP_NO IN (@UserBpNo)
  AND ca.FUNC_INVOICE_CD <> 'NONE'
  AND @AcctgMth BETWEEN ca.AGENT_EFF_DT_FROM AND ca.AGENT_EFF_DT_TO;
```

3. Verify contract effective dates:
```sql
-- Check contract header effective dates
SELECT c.CTR_NO, c.AMEND_NO, c.EFF_DT_FROM, c.EFF_DT_TO
FROM CTR_HDR c
WHERE c.TSP_NO = @TspNo
  AND c.CTR_NO IN (SELECT CTR_NO FROM CTR_AGENT WHERE AGENT_BP_NO = @UserBpNo)
  AND @AcctgMth BETWEEN c.EFF_DT_FROM AND c.EFF_DT_TO;
```

4. Check invoice group delivery methods:
```sql
-- Find groups that are internal-only (excluded from external view)
SELECT gc.INVOICE_GRP_ID, gc.FINAL_INVOICE_DEL_METH_CD
FROM BLCTRL_INVOICE_GRP_COPY gc
WHERE gc.TSP_NO = @TspNo
GROUP BY gc.INVOICE_GRP_ID, gc.FINAL_INVOICE_DEL_METH_CD
HAVING COUNT(*) = 1 AND gc.FINAL_INVOICE_DEL_METH_CD = 'INT';
```

**Code Locations**:
- External user header filtering: `QPTMServiceCore_InvoiceMaintenance.cs` -> `BillingInvoiceHeaderForExternalUser()` (line ~813)
- External user detail filtering: `QPTMServiceCore_InvoiceMaintenance.cs` -> `BillingInvoiceDetailForExternalUser()` (line ~779)
- External user sub-detail filtering: `InvoiceMaintenance_FillSubDetails.cs` -> `BillingInvoiceSubDetailForExternalUser()` (line ~257)
- Contract chain loading: `QPTMServiceCore_InvoiceMaintenance.cs` -> `CheckContractForUser()` (line ~651)
- Invoice group copy filtering: `QPTMServiceCore_InvoiceMaintenance.cs` -> `GetInvoiceGrpCopy()` (line ~688)

**Resolution**: Verify and correct the contract agent, contract header, and contract amendment effective dates. Ensure the user has a BP assigned and that the invoice group has external delivery methods configured.

---

### INVC-003: Cannot Change Invoice Status - Final Status Error

**Symptoms**: Error message "The status cannot be modified on a record that is in final status."

**Root Cause**: Validation rule 001 prevents modifying the status of any header record whose original (pre-edit) status was `FIN` (Final).

**Diagnostic**:
```sql
-- Check original status of the invoice header
SELECT INVOICE_HDR_ID, INVOICE_STAT_CD
FROM BLTRAN_INVOICE_HDR
WHERE INVOICE_HDR_ID = @InvoiceHdrId
  AND TSP_NO = @TspNo;
```

**Code Location**: `QPTMValidationInvoiceHeaderMaintenance001_ValidateHeaderStatusCode.cs`

**Resolution**: Final status is immutable by design. If the invoice needs correction, the standard process is to supersede it with a new invoice through the billing process.

---

### INVC-004: Cannot Post Invoice - Status Validation Error

**Symptoms**: One of these error messages when trying to post (close) an invoice:
- "Invoice must be in FINAL status before it can be closed."
- "Only invoices in the current accounting month can be closed."
- "The accounting month for this invoice has already been closed."

**Diagnostic Steps**:
1. Verify invoice status and accounting month:
```sql
SELECT h.INVOICE_HDR_ID, h.INVOICE_STAT_CD, h.ACCTG_MTH,
       x.OPEN_IND
FROM BLTRAN_INVOICE_HDR h
JOIN BLXREF_LAST_INVOICE_GRP_RUN x
  ON h.TSP_NO = x.TSP_NO
  AND h.INVOICE_GRP_ID = x.INVOICE_GRP_ID
  AND h.ACCTG_MTH = x.ACCTG_MTH
  AND h.PROCESS_QUEUE_ID = x.PROCESS_QUEUE_ID
  AND h.BILL_PERIOD_ID = x.BILL_PERIOD_ID
WHERE h.INVOICE_HDR_ID = @InvoiceHdrId;
```

2. Check current open accounting month:
```sql
SELECT *
FROM ACCOUNTING_MONTH
WHERE TSP_NO = @TspNo
  AND ROLL_TYPE_CD = 'BL';  -- Billing roll type
```

3. Check the `AllowCloseFutureAcctgOnHdr` TSP configuration if trying to close future-month invoices.

**Code Location**: `QPTMValidationInvoiceHeaderMaintenance004_ValidateInvoice.cs`

**Resolution**:
- Ensure the invoice is set to Final (FIN) status before posting
- Only post invoices in the current (or future, if configured) open accounting month
- If the accounting month is already closed, it cannot be posted retroactively

---

### INVC-005: Invoice Amounts Incorrect or Missing on Header by Contract Tab

**Symptoms**: The Header by Contract tab (Tab 2) shows missing or incorrect amount values (CurrentAmt, PpaAmt, fuel quantities).

**Common Causes**:
1. Missing or incorrect records in `BLRPTS_10_INVOICE_DOC_SUM`
2. ProcessQueueId mismatch between the summary table and invoice headers
3. The summary table was not updated after a billing re-run

**Diagnostic**:
```sql
-- Check document summary records for the invoice
SELECT ds.*
FROM BLRPTS_10_INVOICE_DOC_SUM ds
WHERE ds.TSP_NO = @TspNo
  AND ds.INVOICE_HDR_ID = @InvoiceHdrId
  AND ds.PROCESS_QUEUE_ID IS NOT NULL;
```

**Code Location**: `QPTMServiceCore_InvoiceMaintenance.cs` -> `FillHeaderByContract()` (line ~372) and `GetMultipleBlrpts10InvoiceDocSum()` (line ~518)

**Resolution**: Verify that the `BLRPTS_10_INVOICE_DOC_SUM` table is populated correctly. A billing report re-generation may be required if data is missing.

---

### INVC-006: Sub-Detail Records Missing Rate Type, TOC Description, or Tier Description

**Symptoms**: Sub-detail grid rows display blank values for Rate Type Code, TOC Description, or Tier Description columns.

**Common Causes**:
1. **Missing Rate Type Code**: No rate record found for the `RateHdrId` with an effective date range covering the `ActivityDate`
2. **Missing TOC Description**: The `TocCode` value does not exist in the `RT_TYPE_OF_CHARGE` table for the TSP
3. **Missing Tier Description**: The `RateTierId`/`TierDtlId` combination does not exist in the rate tier detail cache

**Diagnostic**:
```sql
-- Check rate record for effective date coverage
SELECT r.RATE_HDR_ID, r.RATE_TYPE_CD, r.EFF_DT_FROM, r.EFF_DT_TO
FROM RT_RATE_HDR r
WHERE r.TSP_NO = @TspNo
  AND r.RATE_HDR_ID = @RateHdrId;

-- Verify sub-detail activity date falls in rate effective range
SELECT sd.INVOICE_SUB_DTL_ID, sd.RATE_HDR_ID, sd.ACTIVITY_DT
FROM BLTRAN_INVOICE_SUB_DTL sd
WHERE sd.INVOICE_SUB_DTL_ID = @InvoiceSubDtlId;

-- Check TOC code exists
SELECT * FROM RT_TYPE_OF_CHARGE
WHERE TSP_NO = @TspNo
  AND TOC_CD = @TocCode;

-- Check tier detail exists
SELECT * FROM RT_TIER_DTL
WHERE RATE_TIER_ID = @RateTierId
  AND TIER_DTL_ID = @TierDtlId;
```

**Code Location**: `InvoiceMaintenance_FillSubDetails.cs` -> `FillSubDetails()` method, lines ~59-88

**Resolution**: Verify that the rate, TOC, and tier reference data exists and has correct effective dates. If rate schedules were updated after invoice generation, the enrichment may not find matching records.

---

### INVC-007: Save Fails with InvoiceStatCode Required Error

**Symptoms**: Error message "Value must be specified for InvoiceStatCode" when saving.

**Root Cause**: The `PreSave` validation in the UI controller checks that all header and detail records have a non-null, non-empty `InvoiceStatCode`. This can happen if a record was loaded with a null status or if a user cleared the status field.

**Code Location**: `QUIControllerInvoiceMaintenance.cs` -> `PreSave()` (line ~283)

**Resolution**: Ensure all header and detail records have a valid InvoiceStatCode value before saving. Valid values: PRE, MOD, APP, FIN.

---

### INVC-008: BLROLLPER Batch Process Fails During Posting

**Symptoms**: Save completes but the batch process fails. The process monitor shows an error status.

**Common Causes**:
1. Batch process infrastructure issues
2. Data inconsistencies in the invoices being posted
3. Conflicting locks on the accounting month records

**Diagnostic Steps**:
1. Check the batch process status:
```sql
-- Check process queue for the specific run
SELECT * FROM PROCESS_QUEUE
WHERE PROCESS_QUEUE_ID = @ProcessQueueId;
```

2. Verify the parameters passed to the batch:
   - `PARAM_TSP_NO`: TSP number
   - `PARAMID_INVOICE_HDR_ID`: Comma-separated list of header IDs being posted
   - `PARAM_ACCTG_MONTH`: Current open accounting month

**Code Location**: `QPTMServiceCore_InvoiceMaintenance.cs` -> `LaunchBatchProcess()` (line ~465)

**Resolution**: Check the batch process logs for specific error details. Ensure no other processes are locking the accounting month. Retry the operation if it was a transient failure.

---

### INVC-009: Detail Status Not Updated After Header Status Change

**Symptoms**: After changing a header to Approved or Preliminary status and saving, the detail records still show the old status.

**Common Causes**:
1. The `PostUpdateAction` method only runs if both `approvedHdrList` and `preliminaryHdrList` are non-empty (there is an AND condition that should be OR)
2. The detail records were filtered by additional criteria not matching the headers

**Diagnostic**:
```sql
-- Check header and detail status mismatch
SELECT h.INVOICE_HDR_ID, h.INVOICE_STAT_CD AS HeaderStatus,
       d.INVOICE_DTL_ID, d.INVOICE_STAT_CD AS DetailStatus
FROM BLTRAN_INVOICE_HDR h
JOIN BLTRAN_INVOICE_DTL d ON h.INVOICE_HDR_ID = d.INVOICE_HDR_ID AND h.TSP_NO = d.TSP_NO
WHERE h.INVOICE_HDR_ID = @InvoiceHdrId
  AND h.INVOICE_STAT_CD <> d.INVOICE_STAT_CD;
```

**Code Location**: `QPTMServiceCore_InvoiceMaintenance.cs` -> `PostUpdateAction()` (line ~253)

**Important Note**: The `PostUpdateAction` method has a condition `if (approvedHdrList.IsInValid() || preliminaryHdrList.IsInValid()) return;` which uses OR logic. This means it only proceeds if BOTH lists are valid (non-empty). If only Approved headers were changed but no Preliminary ones exist (or vice versa), the post-update cascade will be skipped. This is a known behavior pattern to be aware of.

**Resolution**: If the cascade did not occur, a manual status update may be needed, or both header statuses need to be present in the save batch.

---

### INVC-010: Sub-Detail by TOC Tab Shows Incorrect Aggregated Values

**Symptoms**: The Sub-Detail by TOC tab (Tab 4) shows incorrect sums for energy quantities, amounts, or fuel percentages.

**Root Cause**: The grouping algorithm in `GetGroupedBillingInvoiceSubDetailList` uses a complex composite key with many fields. If two records that should be grouped separately share identical values across all grouping key fields, they will be incorrectly merged.

**Key aggregation logic**:
- `ActivityDate`: MIN (start) and MAX (end as UpdtDate)
- `SchdEngQty`, `AllocFuelEngQty`, `EngQty`, `TransAmt`, `VolQty`, `AllocPtrEngQty`: SUM
- `SchdFuelPct`, `SchedPtrPct`: AVERAGE

**Code Location**: `QPTMServiceCore_InvoiceMaintenance.cs` -> `GetGroupedBillingInvoiceSubDetailList()` (line ~547)

**Resolution**: Compare the Sub-Detail by Contract tab (full granular data) with the Sub-Detail by TOC tab to identify the discrepancy. If the grouping key is too broad or too narrow, a code change to the grouping logic may be needed.

---

### INVC-011: Invoice Report Does Not Generate

**Symptoms**: Clicking the invoice report button does not produce a document or process.

**Diagnostic Steps**:
1. Verify a header row is selected in the grid
2. Check that `SelectedBillingInvoiceHeader` is not null
3. Verify the `BLRX00` batch process is configured correctly

**Code Location**: `QUIControllerInvoiceMaintenance.cs` -> `RunInvoiceReport()` (line ~577)

**Resolution**: Ensure a header row is selected. The `RunInvoiceReport` method calls `LaunchBLRX00` with TspNo, AcctgMth, and InvoiceGrpId from the selected header. Verify the batch process service is available and the process returned a valid process ID (non-zero).

---

### INVC-012: Cannot Close Future Accounting Month Invoices

**Symptoms**: Error "Only invoices in the current accounting month can be closed" when trying to post invoices for a future month.

**Root Cause**: The TSP configuration `AllowCloseFutureAcctgOnHdr` is set to 0 (disabled).

**Diagnostic**:
```sql
-- Check the TSP configuration
-- (Check QPTMTspConfigs or the TSP configuration table for AllowCloseFutureAcctgOnHdr setting)
```

**Code Location**:
- Validation: `QPTMValidationInvoiceHeaderMaintenance004_ValidateInvoice.cs` (line ~26)
- Config: `Quorum.QPTM.Common/ConfigSettings/QPTMTspConfigs.cs` -> `AllowCloseFutureAcctgOnHdr()` (line ~382)

**Resolution**: If closing future accounting months is a valid business requirement, the TSP configuration `AllowCloseFutureAcctgOnHdr` needs to be set to 1. This is a TSP-level configuration change.

---

### INVC-013: Performance Issues on Invoice Maintenance Query

**Symptoms**: The Invoice Maintenance query takes a very long time to return, especially for large TSPs or broad date ranges.

**Common Causes**:
1. Large number of sub-detail records being loaded and enriched
2. The FillSubDetails algorithm performing multiple batch lookups
3. External user contract chain joins being expensive
4. Missing database indexes on key join columns

**Key Performance Bottleneck Areas**:

1. **Sub-detail enrichment** (`FillSubDetails`): Loads all sub-details + revisions, joins with xref, then batch-loads rates and TOC data
2. **External user filtering**: Multiple complex LINQ joins across contract/amendment/agent chains
3. **TOC grouping** (`GetGroupedBillingInvoiceSubDetailList`): GroupBy operation on large datasets with many grouping keys

**Diagnostic**:
```sql
-- Count sub-detail records to estimate data volume
SELECT COUNT(*)
FROM BLTRAN_INVOICE_SUB_DTL
WHERE TSP_NO = @TspNo
  AND ACCTG_MTH = @AcctgMth;

-- Check for missing indexes on commonly joined columns
-- Key tables: BLTRAN_INVOICE_HDR, BLTRAN_INVOICE_DTL, BLTRAN_INVOICE_SUB_DTL,
-- BLXREF_LAST_INVOICE_GRP_RUN, BLRPTS_10_INVOICE_DOC_SUM
```

**Code Locations**:
- Sub-detail loading: `QPTMServiceCore_InvoiceMaintenance.cs` -> `GetInvoiceMaintenanceDetails()` (line ~46)
- FillSubDetails: `InvoiceMaintenance_FillSubDetails.cs` (entire file)
- Grouping: `QPTMServiceCore_InvoiceMaintenance.cs` -> `GetGroupedBillingInvoiceSubDetailList()` (line ~547)

**Resolution**:
- Narrow the query by specifying both AcctgMth AND BpNo
- Ensure proper database indexes exist on TSP_NO, ACCTG_MTH, INVOICE_GRP_ID, PROCESS_QUEUE_ID, BILL_PERIOD_ID columns
- Consider the lazy-loading pattern: the `GetDetailsByHeaderId` method loads detail data incrementally per header selection instead of all at once

---

### INVC-014: External User Permission Error on Save

**Symptoms**: Error messages "You do not have permission to update records on this screen" or "You do not have permission to delete records on this screen."

**Root Cause**: Validation rules 002 and 003 block all write operations for non-internal users.

**Code Locations**:
- Delete validation: `QPTMValidationInvoiceHeaderMaintenance002_ValidateDeletePermission.cs`
- Update validation: `QPTMValidationInvoiceHeaderMaintenance003_ValidateUpdatePermission.cs`

**Resolution**: This is by design. External users have read-only access to invoice data. The Save button should be hidden for external users (controlled by `uic.IsUserInternal` in the controller's `GetActions` method). If the Save button is unexpectedly visible, check the `IsUserInternal` property.

---

### INVC-015: Header by Contract Tab Not Loading Details

**Symptoms**: Selecting a row in the Header by Contract tab (Tab 2) does not populate the Detail and Sub-Detail tabs.

**Root Cause**: The `GetDetailsByHeaderId` method lazily loads detail data. It checks if the detail data for the selected header already exists before making a service call. If the condition check fails or the selected header reference is null, no data is loaded.

**Code Location**: `QUIControllerInvoiceMaintenance.cs` -> `GetDetailsByHeaderId()` (line ~256)

**Key Condition**: The method checks `!this.InvoiceDetailList.Items.Any(a => a.TspNo == SelectedBillingInvoiceHeaderByTOC.TspNo && a.InvoiceHdrId == SelectedBillingInvoiceHeaderByTOC.InvoiceHdrId)` - if matching details already exist, it skips the load.

**Resolution**: Verify that the `SelectedBillingInvoiceHeaderByTOC` property is correctly set when a row is selected (via `HeaderByContractGridRowChanged`). Check browser developer tools for the POST request to `GetDetailsByHeaderId`.

---

## Diagnostic SQL Queries

### List All Invoices for a TSP and Month

```sql
SELECT h.INVOICE_HDR_ID, h.INVOICE_ID, h.INVOICE_GRP_ID,
       h.ACCTG_MTH, h.BP_NO, h.BP_NM, h.AGENT_BP_NO,
       h.INVOICE_AMT, h.INVOICE_STAT_CD, h.INVOICE_DT,
       h.NET_DUE_DT, h.PROCESS_QUEUE_ID, h.BILL_PERIOD_ID,
       h.POSTED_DT, h.USER_ID, h.UPDT_DT
FROM BLTRAN_INVOICE_HDR h
WHERE h.TSP_NO = @TspNo
  AND h.ACCTG_MTH = @AcctgMth
ORDER BY h.ACCTG_MTH DESC, h.BP_NO, h.INVOICE_ID;
```

### Check Invoice Open/Closed Status

```sql
SELECT h.INVOICE_HDR_ID, h.INVOICE_ID, h.INVOICE_STAT_CD,
       x.OPEN_IND AS IsOpen
FROM BLTRAN_INVOICE_HDR h
JOIN BLXREF_LAST_INVOICE_GRP_RUN x
  ON h.TSP_NO = x.TSP_NO
  AND h.INVOICE_GRP_ID = x.INVOICE_GRP_ID
  AND h.ACCTG_MTH = x.ACCTG_MTH
  AND h.PROCESS_QUEUE_ID = x.PROCESS_QUEUE_ID
  AND h.BILL_PERIOD_ID = x.BILL_PERIOD_ID
WHERE h.TSP_NO = @TspNo
  AND h.ACCTG_MTH = @AcctgMth;
```

### Find Invoice Details with Status Mismatch

```sql
SELECT h.INVOICE_HDR_ID, h.INVOICE_STAT_CD AS HdrStatus,
       d.INVOICE_DTL_ID, d.LINE_NUM, d.INVOICE_STAT_CD AS DtlStatus
FROM BLTRAN_INVOICE_HDR h
JOIN BLTRAN_INVOICE_DTL d
  ON h.INVOICE_HDR_ID = d.INVOICE_HDR_ID
  AND h.TSP_NO = d.TSP_NO
WHERE h.TSP_NO = @TspNo
  AND h.INVOICE_STAT_CD <> d.INVOICE_STAT_CD
ORDER BY h.INVOICE_HDR_ID, d.LINE_NUM;
```

### List Sub-Details for an Invoice

```sql
SELECT sd.INVOICE_SUB_DTL_ID, sd.INVOICE_DTL_ID,
       sd.ACTIVITY_DT, sd.CTR_NO, sd.TOS_CD, sd.TOC_CD,
       sd.RATE_HDR_ID, sd.RATE, sd.TRANS_AMT,
       sd.VOL_QTY, sd.ENG_QTY, sd.CHARGE_BASIS_CD,
       sd.LOC_ID_1, sd.LOC_ID_2, sd.FLOW_DIRECTION
FROM BLTRAN_INVOICE_SUB_DTL sd
WHERE sd.TSP_NO = @TspNo
  AND sd.INVOICE_HDR_ID = @InvoiceHdrId
ORDER BY sd.ACTIVITY_DT, sd.TOC_CD;
```

### Check Sub-Detail Revision Records

```sql
SELECT sr.INVOICE_SUB_DTL_ID, sr.ACTIVITY_DT,
       sr.CTR_NO, sr.TOC_CD, sr.TRANS_AMT,
       sr.PPA_SRC_CD, sr.PREV_INVOICE_ID
FROM BLTRAN_INVOICE_SUB_DTL_REV sr
WHERE sr.TSP_NO = @TspNo
  AND sr.ACCTG_MTH = @AcctgMth
  AND sr.BP_NO = @BpNo;
```

### Verify External User Contract Agent Chain

```sql
-- Step 1: User's BPs
SELECT BP_NO FROM USER_BP WHERE USER_ID = @UserId;

-- Step 2: Contract agents for user's BPs
SELECT ca.CTR_NO, ca.AGENT_BP_NO, ca.FUNC_INVOICE_CD,
       ca.AGENT_EFF_DT_FROM, ca.AGENT_EFF_DT_TO
FROM CTR_AGENT ca
WHERE ca.TSP_NO = @TspNo
  AND ca.AGENT_BP_NO IN (SELECT BP_NO FROM USER_BP WHERE USER_ID = @UserId)
  AND ca.FUNC_INVOICE_CD <> 'NONE';

-- Step 3: Contracts and amendments
SELECT c.CTR_NO, c.AMEND_NO, c.EFF_DT_FROM, c.EFF_DT_TO
FROM CTR_HDR c
WHERE c.TSP_NO = @TspNo
  AND c.CTR_NO IN (
    SELECT ca.CTR_NO FROM CTR_AGENT ca
    WHERE ca.TSP_NO = @TspNo
      AND ca.AGENT_BP_NO IN (SELECT BP_NO FROM USER_BP WHERE USER_ID = @UserId)
      AND ca.FUNC_INVOICE_CD <> 'NONE'
  );
```

### Check Invoice Group Delivery Methods

```sql
SELECT gc.INVOICE_GRP_ID,
       gc.FINAL_INVOICE_DEL_METH_CD,
       COUNT(*) AS CopyCount
FROM BLCTRL_INVOICE_GRP_COPY gc
WHERE gc.TSP_NO = @TspNo
GROUP BY gc.INVOICE_GRP_ID, gc.FINAL_INVOICE_DEL_METH_CD;
```

### Current Open Accounting Month

```sql
SELECT *
FROM ACCOUNTING_MONTH
WHERE TSP_NO = @TspNo
  AND ROLL_TYPE_CD = 'BL'
ORDER BY MONTH DESC;
```

### Check Rate Coverage for Sub-Detail

```sql
SELECT r.RATE_HDR_ID, r.RATE_TYPE_CD, r.EFF_DT_FROM, r.EFF_DT_TO,
       sd.INVOICE_SUB_DTL_ID, sd.ACTIVITY_DT,
       CASE WHEN sd.ACTIVITY_DT BETWEEN r.EFF_DT_FROM AND r.EFF_DT_TO
            THEN 'COVERED' ELSE 'NOT COVERED' END AS Coverage
FROM BLTRAN_INVOICE_SUB_DTL sd
LEFT JOIN RT_RATE_HDR r
  ON sd.RATE_HDR_ID = r.RATE_HDR_ID
  AND sd.TSP_NO = r.TSP_NO
WHERE sd.TSP_NO = @TspNo
  AND sd.INVOICE_HDR_ID = @InvoiceHdrId;
```

---

## Code Locations Reference

| Area | File | Key Method/Line |
|------|------|----------------|
| Main service query | `QPTMServiceCore_InvoiceMaintenance.cs` | `GetSingleInvoiceMaintenance` (line ~138) |
| Detail/sub-detail loading | `QPTMServiceCore_InvoiceMaintenance.cs` | `GetInvoiceMaintenanceDetails` (line ~46) |
| Header extended properties | `QPTMServiceCore_InvoiceMaintenance.cs` | `AddAdditionalPropertiesInvoiceMaintenanceHeader` (line ~320) |
| Header filtering (external) | `QPTMServiceCore_InvoiceMaintenance.cs` | `FillHeader` (line ~353) |
| Header by Contract fill | `QPTMServiceCore_InvoiceMaintenance.cs` | `FillHeaderByContract` (line ~372) |
| Detail filtering (external) | `QPTMServiceCore_InvoiceMaintenance.cs` | `FillDetails` (line ~407) |
| TOC grouping | `QPTMServiceCore_InvoiceMaintenance.cs` | `GetGroupedBillingInvoiceSubDetailList` (line ~547) |
| Save/update logic | `QPTMServiceCore_InvoiceMaintenance.cs` | `UpdateSingleInvoiceMaintenance` (line ~199) |
| Post-save cascade | `QPTMServiceCore_InvoiceMaintenance.cs` | `PostUpdateAction` (line ~253) |
| Batch process launch | `QPTMServiceCore_InvoiceMaintenance.cs` | `LaunchBatchProcess` (line ~465) |
| External user chain | `QPTMServiceCore_InvoiceMaintenance.cs` | `CheckContractForUser` (line ~651) |
| Sub-detail enrichment | `InvoiceMaintenance_FillSubDetails.cs` | `FillSubDetails` (line ~28) |
| Rate lookup | `InvoiceMaintenance_FillSubDetails.cs` | `GetRateHdrByRateHdrId` (line ~93) |
| TOC lookup | `InvoiceMaintenance_FillSubDetails.cs` | `GetTocByTocCode` (line ~112) |
| Revision copy | `InvoiceMaintenance_FillSubDetails.cs` | `CopyBillingInvoiceSubDetailRevList` (line ~126) |
| UI Controller query | `QUIControllerInvoiceMaintenance.cs` | `DoQuery` (line ~240) |
| UI Controller save | `QUIControllerInvoiceMaintenance.cs` | `DoSave` (line ~319) |
| Pre-save validation | `QUIControllerInvoiceMaintenance.cs` | `PreSave` (line ~283) |
| Lazy detail load | `QUIControllerInvoiceMaintenance.cs` | `GetDetailsByHeaderId` (line ~256) |
| Invoice report | `QUIControllerInvoiceMaintenance.cs` | `RunInvoiceReport` (line ~577) |
| MVC grid data | `InvoiceMaintenanceController.cs` | `HeaderGridGetData` (line ~233) |
| MVC grid selection | `InvoiceMaintenanceController.cs` | `HeaderGridRowChanged` (line ~473) |
| Status code constants | `Constants.cs` | `InvoiceStatCode` class (line ~3993) |
| AllowCloseFuture config | `QPTMTspConfigs.cs` | `AllowCloseFutureAcctgOnHdr` (line ~382) |
| Validation rule 001 | `QPTMValidationInvoiceHeaderMaintenance001_ValidateHeaderStatusCode.cs` | `Validate` |
| Validation rule 004 | `QPTMValidationInvoiceHeaderMaintenance004_ValidateInvoice.cs` | `Validate` |
| Validation rule 005 | `QPTMValidationInvoiceHeaderMaintenance005_ValidateDetailStatusCode.cs` | `Validate` |

---

## Related Documentation

- [Domain Knowledge](./domain.md) - Business concepts, invoice lifecycle, status codes, and business rules
- [Architecture Documentation](./architecture.md) - Technical details of service methods, controllers, database tables, and the FillSubDetails algorithm

---

*Last updated: 2026-03-03*

*Document version: 1.0*
