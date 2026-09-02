# Fix: Duplicate QTRAN_IMBAL_ACCT_BAL / QPOST_IMBAL_ACCT_BAL rows (CUSTACCTBAL / posting-roll PK errors)

## Steps
1. Run the duplicate check on both tables (verify-SELECT first):
```sql
SELECT CTR_NO, CO_CD, ACCT_DT, PROD_DT, COUNT(*) AS dup_ct
FROM   QTRAN_IMBAL_ACCT_BAL
GROUP BY CTR_NO, CO_CD, ACCT_DT, PROD_DT HAVING COUNT(*) > 1;
-- repeat for QPOST_IMBAL_ACCT_BAL (ADO #1772117 covers both)
```
2. Confirm the client patch level against **2025.04 patch #3** (the code fix for dup creation, ADO #1772117). If below, dups will be recreated until the patch lands.
3. If duplicates exist, request the **delete-duplicates script via Script Review / Script Deployment** (Cloud Ops) — the repeated field pattern is ADO #1772095 / #1772687 / #1776936 / #1778789 (HEC UAT/PRD, Dec 2025 – Jan 2026). Wrap in a transaction with a verify-SELECT; scope tightly.
4. Re-run the IMBALANCE / POST step (CUSTACCTBAL or the accounting-period roll).
5. If it recurs **after** patch #3 (seen for a single-OBA-contract client, ADO #1805171), escalate to Engineering with the dup rows as evidence — the patch did not fully prevent re-creation for that shape.

## Verification
- The duplicate-check query returns 0 rows on both tables; CUSTACCTBAL / the posting roll completes; no dup rows visible on Customer Account Maintenance.

## Workaround
None — the duplicates must be deleted before the step can pass; unpatched clients will keep regenerating them until 2025.04 patch #3 is applied.

## Source
SKILL_TIPS_Allocations_PPA_Imbalance.md §4b, §16-C; SKILL_ADO_TIPS_Batch_Processing_SystemConfig_Env.md Cluster F. Cases 25-01060242, 25-01061774, 26-01065143, 26-01068169, 26-01097671, 26-01087709; ADO #1772117, #1772095, #1772687, #1776936, #1778789, #1805171.
