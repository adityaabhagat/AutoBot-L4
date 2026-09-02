# Fix: Phantom inventory record delete (orphaned INTRAN_ACCT_ACTIVITY row re-summed by INTRAN_ACCT_BAL)

## Steps
Verbatim pattern from ADO #1632413 attachments (`delete_row_INTRAN_ACCT_BAL.sql`, `delete_row_INTRAN_ACCT_BAL_dates_starting_dec19.sql`, `INTRAN_ACCT_ACTIVITY_record.sql`), redacted. Use when a stuck balance survives because of an orphaned activity row (e.g. after an OBA-to-allocatable point switch). Only operate in an OPEN accounting month (re-open first if needed); wrap in a transaction.
```sql
-- Params: <INV_ACCT_ID>, <TSP_NO>, <ACCT_ACTIVITY_ID>, <STUCK_QTY> (e.g. 44),
--         <START_MTH>, <END_MTH>
-- 0. VERIFY FIRST — confirm the bad activity row (note the count)
SELECT * FROM INTRAN_ACCT_ACTIVITY
WHERE  INV_ACCT_ID = <INV_ACCT_ID> AND TSP_NO = <TSP_NO>
  AND  ACCTG_MTH BETWEEN '<START_MTH>' AND '<END_MTH>'
  AND  ACCT_ACTIVITY_ID = <ACCT_ACTIVITY_ID>;

-- 1. Delete the offending balance rows (single month, or month-forward)
DELETE FROM INTRAN_ACCT_BAL
WHERE INV_ACCT_ID = <INV_ACCT_ID> AND ACCTG_MTH = '<START_MTH>' AND floor(ALLOC_DEL_QTY) = <STUCK_QTY>;
-- ...or, to clear from a month forward (the "_dates_starting" variant):
DELETE FROM INTRAN_ACCT_BAL
WHERE INV_ACCT_ID = <INV_ACCT_ID> AND ACCTG_MTH >= '<START_MTH>' AND floor(ALLOC_DEL_QTY) = <STUCK_QTY>;

-- 2. Delete the orphaned activity row that the balance kept re-summing
DELETE FROM INTRAN_ACCT_ACTIVITY WHERE ACCT_ACTIVITY_ID = <ACCT_ACTIVITY_ID>;
```
Then **re-run INACCTACCM** to rebuild clean balances for the affected months.

## Verification
Re-query `INTRAN_ACCT_BAL` / `INTRAN_ACCT_ACTIVITY` for the `INV_ACCT_ID` + month range — the stuck delta is gone; Customer Account Maintenance / Authorization-to-Post Imbalances show the corrected balance after INACCTACCM re-runs.

## Workaround
None that clears the number — the balance keeps re-summing the orphan row every accumulation. Customers can note/annotate the known phantom quantity on the account until Cloud Ops deploys the delete script.

## Source
SKILL_Customer_Accounts_Inventory.md §12 Template A and §4a; ADO #1632413 (verbatim SQL attachments); SF 23-00928558 (APL, 44 GJ phantom record).
