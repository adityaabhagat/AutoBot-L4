---
title: Inventory (INV) - Troubleshooting Guide
category: troubleshooting
feature: Inventory (INV)
related_repos: Web, Batch
keywords: INV, troubleshooting, imbalance, balance, trade, transfer, adjustment, storage, accumulation, INACCTACCM, INTRDPEND, INCONFTRADE, diagnostic queries, error messages
last_updated: 2026-03-03
---

# Inventory (INV) - Troubleshooting Guide

## Overview

This document provides troubleshooting guidance for Inventory (INV) issues in QPTM. It includes common problems, diagnostic SQL queries, error messages, investigation workflows, and historical issue patterns.

For business concepts, see [Domain Documentation](./domain.md).
For technical details, see [Architecture Documentation](./architecture.md).

---

## Table of Contents

1. [Common Issues](#common-issues)
2. [Diagnostic Queries](#diagnostic-queries)
3. [Key Code Locations](#key-code-locations)
4. [Investigation Workflow](#investigation-workflow)
5. [Performance Issues](#performance-issues)
6. [Historical Issues Template](#historical-issues-template)

---

## Common Issues

### Issue 1: Trade Cannot Be Submitted - "Monthly Trading Lag Time did not have value"

**Symptoms:**
- Error message: "Monthly Trading Lag Time did not have value for Contract Number: {CtrNo}."
- Trade submission fails for monthly-period trades
- The trade remains in NEW status

**Root Causes:**
1. The contract header does not have a `MonthlyTradeLagTime` value set
2. The contract was recently created or modified and the lag time was not configured
3. Wrong contract number on the trade

**Diagnostic Query:**
```sql
-- Check MonthlyTradeLagTime for the contract
SELECT CTR_NO, MONTHLY_TRADE_LAG_TIME, EFF_DT_FROM, EFF_DT_TO
FROM QCTRL_CTR_HDR
WHERE TSP_NO = @TspNo
  AND CTR_NO = @CtrNo
  AND EFF_DT_FROM <= @AsOfDate
  AND EFF_DT_TO >= @AsOfDate;
```

**Resolution:**
- Set the `MonthlyTradeLagTime` on the contract header for the relevant effective date range
- Verify the correct contract number is specified on the trade

**Code Location**: `Quorum.QPTM.Validations.Rules.Inventory/ImbalanceTrading/RuleINTR000010.cs`

---

### Issue 2: Trade Cannot Be Submitted - "Record cannot be submitted"

**Symptoms:**
- Error message: "Record cannot be submitted. Please press the NEW button to create a new record or copy the current record, then press the SUBMIT REQUEST button."
- Attempting to resubmit an existing trade

**Root Causes:**
1. The user is trying to submit an existing (already saved) trade record
2. The `DataObjectState` is not `Added` (it is `Modified` or `Unchanged`)

**Resolution:**
- Create a new trade record using the NEW button or copy the current record
- Do not attempt to resubmit a previously submitted or processed trade

**Code Location**: `Quorum.QPTM.Validations.Rules.Inventory/ImbalanceTrading/RuleINTR000020.cs`

---

### Issue 3: Trade Quantity Exceeds Available - "Trade Quantity Requested is not available for trade"

**Symptoms:**
- Error message: "Record cannot be submitted. Trade Quantity Requested is not available for trade."
- Trade submission fails because requested quantity exceeds the available imbalance

**Root Causes:**
1. The `ReqTradeQty` exceeds `|RecDelDiffQty|` (absolute value of available quantity)
2. Prior trades or adjustments have already consumed the available quantity
3. The balance data for the account is stale or incorrect
4. The trade availability formula is returning an unexpected value

**Diagnostic Query:**
```sql
-- Check available quantity for the account
SELECT INV_ACCT_ID, PROD_MTH, ACCTG_MTH,
       REC_DEL_DIFF_QTY, TRADE_QTY, TRANSFER_QTY, ADJ_QTY, CICO_QTY, END_BAL_QTY
FROM INTRAN_ACCT_BAL
WHERE TSP_NO = @TspNo
  AND INV_ACCT_ID = @InvAcctId
  AND PROD_MTH = @ProdMth
ORDER BY ACCTG_MTH;

-- Check existing trades for this account/period
SELECT ACCT_TRADE_ID, TRADE_STAT_CD, REQ_TRADE_QTY, APPR_TRADE_QTY,
       INIT_INV_ACCT_ID, CONF_INV_ACCT_ID, PROD_MTH
FROM INCTRL_ACCT_TRADE
WHERE TSP_NO = @TspNo
  AND (INIT_INV_ACCT_ID = @InvAcctId OR CONF_INV_ACCT_ID = @InvAcctId)
  AND TRADE_STAT_CD NOT IN ('REJ', 'WTH')
ORDER BY ACCT_TRADE_ID DESC;
```

**Resolution:**
- Reduce the requested trade quantity to within the available balance
- Verify no pending trades are consuming the available quantity
- Check if the trade availability formula is configured correctly for the TSP
- Internal users can override this validation

**Code Location**: `Quorum.QPTM.Validations.Rules.Inventory/ImbalanceTrading/RuleINTR000050.cs`

---

### Issue 4: Manual Posting Fails - "Imbalance Quantity could not be located"

**Symptoms:**
- Error message: "Imbalance Quantity could not be located for the current primary contract number, accounting and production months."
- Manual posting cannot proceed

**Root Causes:**
1. No `INTRAN_ACCT_BAL` record exists for the account/production month/accounting month combination
2. The INACCTACCM batch process has not been run for the relevant period
3. The accounting month lag time configuration is incorrect

**Diagnostic Query:**
```sql
-- Check for account balance record
SELECT INV_ACCT_ID, PROD_MTH, ACCTG_MTH, END_BAL_QTY, NNS_IMB_QTY
FROM INTRAN_ACCT_BAL
WHERE TSP_NO = @TspNo
  AND INV_ACCT_ID = @InvAcctId;

-- Check open accounting month
SELECT MIN(ACCTG_MTH) AS OPEN_ACCTG_MTH
FROM QCTRL_ACCTG_MTH
WHERE TSP_NO = @TspNo
  AND OPEN_IND = 1
  AND ACCTG_ROLL_TYPE_CD = 'BIL';

-- Check accounting month lag time
SELECT KEY_VALUE
FROM PACTRL_TSP_CNFG_CTRL
WHERE TSP_NO = @TspNo
  AND KEY_GRP_NM = 'TSP'
  AND KEY_NM = 'ACCTG_MTH_LAG_TIME';
```

**Resolution:**
- Run the INACCTACCM batch process to create the balance records
- Verify the accounting month lag time is correctly configured
- Ensure the billing accounting month is open

**Code Location**: `Quorum.QPTM.Validations.Rules.Inventory/ManualPosting/RuleINMP000010.cs`

---

### Issue 5: Storage Transfer Missing Confirming Details

**Symptoms:**
- Error messages: "Please enter a confirming contact.", "Please enter confirming phone number.", or "Please enter a confirming contract."
- Storage transfer cannot be confirmed or accepted

**Root Causes:**
1. The confirming party's contact name (`ConfContactNm`) is null
2. The confirming party's phone number (`ConfContactPhoneNo`) is null
3. The confirming contract number (`ConfPrimaryCtrNo`) is null

**Resolution:**
- Populate all three confirming fields before attempting confirm/accept
- Contact the confirming party to obtain the required information

**Code Location**: `Quorum.QPTM.Validations.Rules.Inventory/Storage Transfer/RuleINST000010.cs`

---

### Issue 6: External User Cannot Add Inventory Account

**Symptoms:**
- External user receives an error when trying to add a new inventory account header
- The error references authorization to post imbalances

**Root Causes:**
1. Business rule prevents external users from creating new inventory accounts
2. Only internal (pipeline) users have permission to add accounts

**Resolution:**
- Contact the pipeline's internal administrator to create the account
- Verify the user's internal/external status in the security configuration

**Code Location**: `Quorum.QPTM.Validations.Rules.Inventory/InventoryAccount/RuleINCA000010.cs`

---

### Issue 7: Inventory Account Balance Discrepancy

**Symptoms:**
- The ending balance does not match the expected formula: `END_BAL = BEG_BAL + REC_DEL_DIFF + TRADE + TRANSFER + ADJ + CICO`
- Monthly totals do not reconcile with daily totals
- Dashboard widgets show different values than the Inventory Accounts screen

**Root Causes:**
1. INACCTACCM batch process did not complete successfully
2. A trade was processed but the balance was not updated
3. An adjustment was submitted but not yet processed
4. Multiple accounting month records exist and the wrong one is being displayed
5. The widget uses the minimum accounting month while the screen may show a different one

**Diagnostic Query:**
```sql
-- Full balance breakdown for an account
SELECT INV_ACCT_ID, PROD_MTH, ACCTG_MTH,
       BEG_BAL_QTY, ALLOC_REC_QTY, ALLOC_DEL_QTY, REC_DEL_DIFF_QTY,
       TRADE_QTY, TRANSFER_QTY, ADJ_QTY, CICO_QTY, END_BAL_QTY,
       GROSS_REC_QTY, GROSS_DEL_QTY, REC_FUEL_QTY, DEL_FUEL_QTY,
       PPA_QTY, PPA_REC_QTY, PPA_DEL_QTY, RETAINED_QTY, PAYBACK_QTY
FROM INTRAN_ACCT_BAL
WHERE TSP_NO = @TspNo
  AND INV_ACCT_ID = @InvAcctId
  AND PROD_MTH = @ProdMth
ORDER BY ACCTG_MTH;

-- Verify balance formula
SELECT INV_ACCT_ID, PROD_MTH, ACCTG_MTH,
       BEG_BAL_QTY + REC_DEL_DIFF_QTY + TRADE_QTY + TRANSFER_QTY + ADJ_QTY + CICO_QTY AS CALCULATED_END_BAL,
       END_BAL_QTY AS STORED_END_BAL,
       (BEG_BAL_QTY + REC_DEL_DIFF_QTY + TRADE_QTY + TRANSFER_QTY + ADJ_QTY + CICO_QTY) - END_BAL_QTY AS DIFFERENCE
FROM INTRAN_ACCT_BAL
WHERE TSP_NO = @TspNo
  AND INV_ACCT_ID = @InvAcctId;
```

**Resolution:**
- Re-run the INACCTACCM batch process for the affected period
- Check for pending trades/adjustments that need processing
- Verify the correct accounting month is being viewed

**Code Location**: `Quorum.QPTM.ServiceCore.Inventory/QPTMInventoryService.cs` (balance methods), `Quorum.QPTM.ServiceCore.Inventory/QPTMInventoryWidgetService.cs` (widget)

---

### Issue 8: Trade Stuck in Pending Status

**Symptoms:**
- Trade shows status `PEN` (Pending) but the confirm action fails or does not update the status
- The `INTRDPEND` batch process may have failed

**Root Causes:**
1. The `INTRDPEND` batch process failed to complete
2. Validation errors on the confirming side
3. The trade action code xref (`TradeStatTradeActn`) does not have the correct next status

**Diagnostic Query:**
```sql
-- Check trade status and details
SELECT ACCT_TRADE_ID, TRADE_STAT_CD, TRADE_TRANS_TYPE_CD,
       INIT_INV_ACCT_ID, CONF_INV_ACCT_ID,
       REQ_TRADE_QTY, APPR_TRADE_QTY, STMT_DT, UPDT_DT
FROM INCTRL_ACCT_TRADE
WHERE TSP_NO = @TspNo
  AND ACCT_TRADE_ID = @TradeId;

-- Check batch process execution log
SELECT TOP 10 *
FROM PACTRL_PROC_QUEUE
WHERE TSP_NO = @TspNo
  AND BATCH_ID = 'INTRDPEND'
ORDER BY PROC_QUEUE_ID DESC;
```

**Resolution:**
- Check the batch process log for errors
- Re-run the `INTRDPEND` process manually if needed
- Verify the trade status action xref is configured correctly

**Code Location**: `Quorum.QPTM.ServiceCore.Inventory/QPTMInventoryService.cs` lines 404-431 (`ConfirmTrade`)

---

### Issue 9: TSP Configuration Date Overlap Error

**Symptoms:**
- Error message: "Unable to save to the specified date due to an overlap with another date range.."
- Saving inventory TSP configuration fails

**Root Causes:**
1. The new configuration record's date range overlaps with an existing record
2. When adding a single new record without first querying existing records

**Diagnostic Query:**
```sql
-- Check existing TSP config date ranges
SELECT TSP_NO, EFF_DT_FROM, EFF_DT_TO, Y_DAY_CUTOFF_TIME
FROM INCTRL_TSP_CONFIG
WHERE TSP_NO = @TspNo
ORDER BY EFF_DT_FROM;
```

**Resolution:**
- Adjust the effective date range to not overlap with existing records
- Query existing records first before adding a new one
- End-date an existing record before creating a new one for the same TSP

**Code Location**: `Quorum.QPTM.ServiceCore.Inventory/QPTMInventoryService.cs` lines 1059-1096 (`SubmitInventoryTspConfigList`)

---

### Issue 10: Daily Imbalance Shows Zero on First of Month

**Symptoms:**
- The daily imbalance widget shows 0 on the 1st day of a production month
- Expected to see a non-zero daily imbalance

**Root Causes:**
1. This is **expected behavior** for non-rolling accounts. On the first of the month, `DailyImbalQty` is deliberately set to 0
2. For rolling accounts, this should not happen -- if it does, the account type's `IsRollProdMth` flag may be incorrect

**Diagnostic Query:**
```sql
-- Check if the account type is rolling
SELECT AT.ACCT_TYPE_CD, AT.IS_ROLL_PROD_MTH, AT.INV_SCR_FMT_CD, AT.ACCT_TYPE_CTGRY_CD
FROM INCTRL_ACCT_HDR AH
JOIN QCODE_ACCT_TYPE AT ON AH.ACCT_TYPE_CD = AT.ACCT_TYPE_CD
WHERE AH.TSP_NO = @TspNo
  AND AH.INV_ACCT_ID = @InvAcctId;
```

**Resolution:**
- For non-rolling accounts: This is expected behavior, no action needed
- For rolling accounts: Verify the `IS_ROLL_PROD_MTH` flag on the account type code table

**Code Location**: `Quorum.QPTM.ServiceCore.Inventory/QPTMInventoryWidgetService.cs` lines 114-147 (`_GetInventoryImbalances`)

---

### Issue 11: Inventory Adjustments Grid Not Showing Updated Data

**Symptoms:**
- After saving an adjustment, the grid does not reflect the changes
- Page navigation issues after deletions

**Root Causes:**
1. Pagination fix in the controller: if the current page exceeds the total page count after deletions, the page is reset
2. The `IsModified` state may not be triggered for `SubmitInd` or `DeleteInd` changes (they are DOExt properties)

**Diagnostic Query:**
```sql
-- Check adjustment records for the account
SELECT ID_ACCT_ADJ, ACTIVITY_DATE, PROD_MTH, ACCTG_MTH,
       FROM_CTR_NO, TO_CTR_NO, INV_ADJ_TYPE_CD, ADJ_QTY, ADJ_QTY_VOL,
       SUBMIT_IND, IS_PROC, DELETE_IND
FROM INCTRL_INV_ADJ
WHERE TSP_NO = @TspNo
ORDER BY UPDT_DT DESC;
```

**Resolution:**
- The controller manually triggers `IsModified` by adding an `UpdateDate` to the field update when `SubmitInd` or `DeleteInd` changes
- Refresh the grid after save operations
- Check that pagination resets properly when items are deleted

**Code Location**: `Quorum.QPTM.Web.Core/Controllers/InventoryAdjustmentsController.cs` lines 179-192 (`InventoryAdjustmentsGridUpdate`)

---

### Issue 12: Inventory Accounts Screen Shows Wrong UOM Columns

**Symptoms:**
- Energy (Dth) columns are visible when Volume (Mcf) should be shown, or vice versa
- Totals do not match the displayed columns

**Root Causes:**
1. The UOM type code parameter is not being passed correctly
2. The `ShowHideMonthlyActivityAndBalanceGridColumns` method is not toggling columns

**Resolution:**
- Verify the `UomTypeCd` parameter is set correctly on the view model
- Check that the TSP preference `EngUomCode` and `VolUomCode` are configured
- The controller hides all energy/volume columns, then shows only the selected set

**Code Location**: `Quorum.QPTM.Web.Core/Controllers/InventoryAccountsController.cs` lines 408-461 (`ShowHideMonthlyActivityAndBalanceGridColumns`)

---

## Diagnostic Queries

### Query 1: Account Header and Balance Summary

```sql
-- Get account header with current balance
SELECT
    AH.INV_ACCT_ID,
    AH.ACCT_TYPE_CD,
    AH.PRIMARY_CTR_NO,
    AH.OPER_IMP_AREA_CD,
    AB.PROD_MTH,
    AB.ACCTG_MTH,
    AB.BEG_BAL_QTY,
    AB.REC_DEL_DIFF_QTY,
    AB.TRADE_QTY,
    AB.TRANSFER_QTY,
    AB.ADJ_QTY,
    AB.CICO_QTY,
    AB.END_BAL_QTY
FROM INCTRL_ACCT_HDR AH
LEFT JOIN INTRAN_ACCT_BAL AB
    ON AH.TSP_NO = AB.TSP_NO AND AH.INV_ACCT_ID = AB.INV_ACCT_ID
WHERE AH.TSP_NO = @TspNo
  AND AH.INV_ACCT_ID = @InvAcctId
ORDER BY AB.PROD_MTH, AB.ACCTG_MTH;
```

### Query 2: Daily Balance for a Gas Day

```sql
-- Daily balance for a specific gas day
SELECT
    INV_ACCT_ID,
    ACTIVITY_DATE,
    REC_DEL_DIFF_QTY,
    TRADE_QTY,
    TRANSFER_QTY,
    ADJ_QTY,
    CICO_QTY,
    END_BAL_QTY
FROM INTRAN_ACCT_BAL_DAILY
WHERE TSP_NO = @TspNo
  AND INV_ACCT_ID = @InvAcctId
  AND ACTIVITY_DATE = @GasDay;
```

### Query 3: Account Activity for a Period

```sql
-- Activity for an account in a date range
SELECT
    INV_ACCT_ID,
    CTR_NO,
    ACTIVITY_DATE,
    ALLOC_REC_QTY,
    ALLOC_DEL_QTY,
    REC_DEL_DIFF_QTY
FROM INTRAN_ACCT_ACTIVITY
WHERE TSP_NO = @TspNo
  AND INV_ACCT_ID = @InvAcctId
  AND ACTIVITY_DATE BETWEEN @BeginDate AND @EndDate
ORDER BY ACTIVITY_DATE;
```

### Query 4: All Trades for an Account

```sql
-- Trade history for an account
SELECT
    T.ACCT_TRADE_ID,
    T.TRADE_STAT_CD,
    T.TRADE_TRANS_TYPE_CD,
    T.IMBAL_PERIOD_CD,
    T.INIT_INV_ACCT_ID,
    T.INIT_PRIMARY_CTR_NO,
    T.CONF_INV_ACCT_ID,
    T.CONF_PRIMARY_CTR_NO,
    T.REQ_TRADE_QTY,
    T.APPR_TRADE_QTY,
    T.PROD_MTH,
    T.ACCTG_MTH,
    T.GAS_DAY,
    T.STMT_DT,
    T.UPDT_DT
FROM INCTRL_ACCT_TRADE T
WHERE T.TSP_NO = @TspNo
  AND (T.INIT_INV_ACCT_ID = @InvAcctId OR T.CONF_INV_ACCT_ID = @InvAcctId)
ORDER BY T.ACCT_TRADE_ID DESC;
```

### Query 5: Inventory Adjustments for a Period

```sql
-- Adjustments for a contract/period
SELECT
    ID_ACCT_ADJ,
    ACTIVITY_DATE,
    PROD_MTH,
    ACCTG_MTH,
    FROM_CTR_NO,
    TO_CTR_NO,
    INV_ADJ_TYPE_CD,
    ADJ_QTY,
    ADJ_QTY_VOL,
    SUBMIT_IND,
    IS_PROC,
    DELETE_IND,
    COMMENTS,
    USER_ID,
    UPDT_DT
FROM INCTRL_INV_ADJ
WHERE TSP_NO = @TspNo
  AND PROD_MTH = @ProdMth
  AND ACCTG_MTH = @AcctgMth
ORDER BY ACTIVITY_DATE, ID_ACCT_ADJ;
```

### Query 6: Account Type Configuration

```sql
-- Account type details including rolling and screen format
SELECT
    ACCT_TYPE_CD,
    ACCT_TYPE_CTGRY_CD,
    INV_SCR_FMT_CD,
    IS_ROLL_PROD_MTH,
    ACCT_TYPE_DESC
FROM QCODE_ACCT_TYPE
ORDER BY ACCT_TYPE_CD;
```

### Query 7: Contracts with Inventory Accounts

```sql
-- Contracts linked to inventory accounts
SELECT
    AH.INV_ACCT_ID,
    AH.ACCT_TYPE_CD,
    AH.PRIMARY_CTR_NO,
    AC.CTR_NO,
    CH.TOS_CD,
    CH.MONTHLY_TRADE_LAG_TIME
FROM INCTRL_ACCT_HDR AH
JOIN INCTRL_ACCT_CTR AC ON AH.TSP_NO = AC.TSP_NO AND AH.INV_ACCT_ID = AC.INV_ACCT_ID
LEFT JOIN QCTRL_CTR_HDR CH ON AH.TSP_NO = CH.TSP_NO AND AC.CTR_NO = CH.CTR_NO
WHERE AH.TSP_NO = @TspNo
ORDER BY AH.INV_ACCT_ID;
```

---

## Key Code Locations

### Service Layer

| File | Location | Description |
|------|----------|-------------|
| `QPTMInventoryService.cs` | `Quorum.QPTM.ServiceCore.Inventory/` | Main inventory service (~1133 lines) |
| `QPTMInventoryWidgetService.cs` | `Quorum.QPTM.ServiceCore.Inventory/` | Dashboard widget service |
| `QPTMServiceCore_InventoryAccounts.cs` | `Quorum.QPTM.ServiceCore/` | Inventory accounts screen service |

### Controllers

| File | Location | Description |
|------|----------|-------------|
| `InventoryAccountsController.cs` | `Quorum.QPTM.Web.Core/Controllers/` | MVC controller for inventory accounts |
| `InventoryAdjustmentsController.cs` | `Quorum.QPTM.Web.Core/Controllers/` | MVC controller for adjustments |
| `InventoryController.cs` | `Quorum.QPTM.Web.Controllers/APIControllers/` | REST API controller |

### Validation Rules

| Directory | Location | Rule Count |
|-----------|----------|------------|
| `ImbalanceTrading/` | `Quorum.QPTM.Validations.Rules.Inventory/` | 31 rules (RuleINTR000010-310) |
| `InventoryAccount/` | `Quorum.QPTM.Validations.Rules.Inventory/` | 16 rules (RuleINCA000010-160) |
| `ManualPosting/` | `Quorum.QPTM.Validations.Rules.Inventory/` | 2 rules (RuleINMP000010-020) |
| `Storage Transfer/` | `Quorum.QPTM.Validations.Rules.Inventory/` | 22 rules (RuleINST000010-220) |

### Data Access

| File | Location | Description |
|------|----------|-------------|
| `InventoryAccountHeaderDAL.cs` | `Quorum.QPTM.DAL/CodeGen/` | Account header data access |
| `InventoryAccountBalanceDAL.cs` | `Quorum.QPTM.DAL/CodeGen/` | Monthly balance data access |
| `InventoryAccountBalanceDailyDAL.cs` | `Quorum.QPTM.DAL/CodeGen/` | Daily balance data access |
| `InventoryAccountActivityDAL.cs` | `Quorum.QPTM.DAL/CodeGen/` | Activity data access |
| `InventoryAccountTradeDAL.cs` | `Quorum.QPTM.DAL/CodeGen/` | Trade data access |

### Batch Processes

| File | Location | Description |
|------|----------|-------------|
| `QPTMBatchProcessService.cs` | `Quorum.QPTM.Common/` | Batch process launcher (lines 182-250) |

### Constants

| File | Location | Sections |
|------|----------|----------|
| `Constants.cs` | `Quorum.QPTM.CoreInterface/` | `ImbalanceTradeStatus` (line ~1122), `ImbalanceTradeActions` (~1172), `ImbalancePeriod` (~1185), `ImbalanceTradeType` (~1193), `ImbalanceTradeTransType` (~1203), `InventoryAccountType` (~1211) |

---

## Investigation Workflow

### Step 1: Identify the Area

Inventory issues generally fall into these categories:

| Category | Keywords | Starting Point |
|----------|----------|----------------|
| **Balance Issues** | balance, discrepancy, wrong quantity | `INTRAN_ACCT_BAL`, Query 1, Query 7 |
| **Trade Issues** | trade, submit, confirm, reject, pending | `INCTRL_ACCT_TRADE`, Query 4, Issue 1-3 |
| **Transfer Issues** | storage transfer, XFER | `INCTRL_ACCT_TRADE` (XFER type), Issue 5 |
| **Adjustment Issues** | adjustment, correction, ADJ | `INCTRL_INV_ADJ`, Query 5, Issue 11 |
| **Dashboard Issues** | widget, dashboard, imbalance display | Widget service, Issue 10, 12 |
| **Configuration Issues** | TSP config, lag time, tolerance | `INCTRL_TSP_CONFIG`, `PACTRL_TSP_CNFG_CTRL`, Issue 9 |
| **Batch Process Issues** | INACCTACCM, INTRDPEND, stuck | Process queue, Issue 4, 8 |

### Step 2: Gather Information

1. **TSP Number**: Which pipeline?
2. **Inventory Account ID**: Which account? (check `INCTRL_ACCT_HDR`)
3. **Time Period**: Which production month and accounting month?
4. **Account Type**: IMB, STO, PAL, OBA? (determines screen format and rules)
5. **User Type**: Internal or external? (affects validation behavior)
6. **Error Message**: Exact error text (map to validation rule)

### Step 3: Check Data

Run the relevant diagnostic queries from the [Diagnostic Queries](#diagnostic-queries) section to understand the current data state.

### Step 4: Trace the Code

1. Start at the controller action being called
2. Follow through to the service method
3. If validation fails, check the specific `Rule*` class
4. If a batch process is involved, check the process queue and logs

### Step 5: Verify Configuration

For configuration-related issues:
- Check `INCTRL_TSP_CONFIG` for date range and cutoff time
- Check `PACTRL_TSP_CNFG_CTRL` for lag time and tolerance settings
- Check `QCTRL_ACCTG_MTH` for open accounting months
- Check contract header for `MonthlyTradeLagTime` and `OperationalBalance` attribute

---

## Performance Issues

### Slow Inventory Accounts Screen

**Possible Causes:**
- Large number of account headers for the TSP
- Multiple accounting months creating duplicate activity/balance records
- View queries (`INTRAN_INV_ACTIVITY_VW`, `INTRAN_INV_BALANCE_VW`) not indexed properly

**Investigation:**
- Check the number of rows returned by the activity and balance view queries
- Look at the `ToLookup` aggregation in `QPTMServiceCore_InventoryAccounts.cs` -- it deduplicates records by key
- Verify database indexes on the `_VW` views

### Slow Widget Loading

**Possible Causes:**
- The widget service queries all contracts for the user, then all accounts, then all activities
- The `Break(500)` batch processing of account IDs may create many database round-trips

**Investigation:**
- Check how many contracts the user has access to
- Monitor the number of `GetInventoryAcctBalances` and `GetInventoryAcctActivity` calls
- The `InventoryCache.GetInventoryAccountHdrsForContracts` may be returning too many results

### Slow Trade Submission

**Possible Causes:**
- The `GetQuantityAvailableForTrade` method makes multiple balance queries (up to 3 for monthly)
- The formula evaluation adds processing time
- Event handling (`ExecuteAndHandleEvents`) may trigger slow downstream processes

---

## Historical Issues Template

Use this template when documenting resolved inventory issues for future reference:

```markdown
### [Issue Title]

**Work Item**: [WI/Bug Number]
**Date Resolved**: [Date]
**Customer/Environment**: [Customer name / Environment]

**Symptoms:**
- [What the user reported]

**Root Cause:**
- [Technical root cause]

**Resolution:**
- [What was done to fix it]

**Code Changes:**
- [Files modified with brief description]

**Diagnostic Query Used:**
```sql
-- [Query that helped diagnose]
```

**Prevention:**
- [How to prevent recurrence]
```

---

*Cross-references:*
- [Domain Documentation](./domain.md) - Business concepts and terminology
- [Architecture Documentation](./architecture.md) - Technical implementation details

*Last updated: 2026-03-03*

*Document version: 1.0*
