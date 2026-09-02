# Fix: Duplicate QTRAN_IMBAL_ACCT_BAL rows (doubled imbalance balances)

## Steps
1. Confirm the duplicates, scoped to the affected month:
```sql
SELECT BA_NO, CTR_NO, ACCT_DT, PROD_DT, COUNT(*) AS DUP_CT
FROM   QTRAN_IMBAL_ACCT_BAL
WHERE  PROD_DT = '{prod_mth}'
GROUP BY BA_NO, CTR_NO, ACCT_DT, PROD_DT
HAVING COUNT(*) > 1;
```
   (Key columns beyond the table name are inferred — verify against the client schema; the proven HEC dedupe scripts are attached to ADO #1772687 / #1778789.)
2. **Short-term:** raise a Cloud Ops dedupe script following the #1772687/#1778789 lineage — delete duplicates from `QTRAN_IMBAL_ACCT_BAL`, scoped to client/env/accounting month, via Script Review → Script Deployment work items, with a verify-SELECT.
3. **Long-term:** confirm the client build is at or above the **2025.04 patch containing the code fix** (Hilcorp pattern: PRD 2025.04.1.3 lacked it, fix in 2025.04.1.4; core PRs 124423 [2025.04] / 124426 [2025.10] on `QCODE_POST_TABLES`). Schedule the patch if behind.
4. Ensure config **`RUN_IMBALANCE_BY_FACILITY`** is **checked into the Quorum-managed client repo** — if it lives only in the DB, the next patch reverts it and the duplicates return (root-cause note on ADO #1772117).

## Verification
- Step 1 query returns zero rows for the affected month after the dedupe.
- Customer Account Maintenance balances match pre-doubling expectations; the next monthly PLANTIMBAL/IMBALANCE run does not recreate duplicates (the real proof the patch + repo config took).

## Workaround
The scoped dedupe script is the workaround; without the 2025.04 patch and the repo-checked config, the duplicates recur monthly (as they did at Hilcorp for 3 consecutive months).

## Source
SKILL_TIPS_Master_Data_Contracts.md §5 and §16-B (SF 25-01060242, 25-01061774, 26-01065143, 26-01068169); SKILL_ADO_TIPS_MasterData_Contracts_CCT_Meter.md §4-A (ADO #1772117, #1772687, #1776627/858/936, #1778736/89).
