# Fix: ALALLOCATE duplicate-key (AK_ALCTRL_ALLOC2) / bad-nom-data clean-up

## Steps
1. Run the duplicate check and the SQL trace to identify the colliding key and the exact failing insert:
```sql
-- duplicate allocation rows on the unique key
SELECT TSP_NO, LOC_ID, ALLOC_GAS_DAY, ACCTG_MTH, TRANS_TYPE_ID, SR_CTR_NO, COUNT(*) AS dup_ct
FROM   ALCTRL_ALLOC
WHERE  TSP_NO = {tsp} AND ACCTG_MTH = '{prod_mth}'
GROUP BY TSP_NO, LOC_ID, ALLOC_GAS_DAY, ACCTG_MTH, TRANS_TYPE_ID, SR_CTR_NO
HAVING COUNT(*) > 1;

-- the exact insert that errored (look for m_Output_Ins* statements)
SELECT SEQ_NO, SQL_TEXT, ERROR_MSG
FROM   QARCH_QFCBATCH_SQL_TRACE
WHERE  PROCESS_QUEUE_ID = {pqid}
ORDER BY SEQ_NO;
```
2. If the duplicate is a **stale alloc row** from a prior run: delete the duplicate `ALCTRL_ALLOC` row for that TSP / LOC / gas-day / acctg-mth / TT / contract, then re-run ALALLOCATE scoped to that month.
3. If the root is **bad nom data** (nom header/detail mismatch, or duplicate Account Managers on a BP per case 23-00903346): clean the nom side first, then re-allocate.
4. Always scope the delete to the **specific location/gas-day** (not the whole month) and wrap in `BEGIN TRAN ... COMMIT` with a verify-SELECT before committing.

## Verification
The duplicate-check SELECT returns 0 rows for the colliding key; the scoped ALALLOCATE re-run completes without `unique constraint (...AK_ALCTRL_ALLOC2) violated`.

## Workaround
None — allocation is blocked for the accounting month until the duplicate/bad rows are cleaned. Do not re-run the whole month blindly; scope the re-run to the affected locations/gas days.

## Source
SKILL_Allocations.md §17 (Recovery recipe) and §4; SF 25-00998023 ("Data clean-up script to clean bad nom data"), 22-00524917 (PANIGHTLY AK_ALCTRL_ALLOC2, TSP 499), 23-00903346 (duplicate Account Managers).
