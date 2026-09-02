# Fix: CANOMCLTG "Found Orphaned Location attribute ..." — orphan rows in PACTRL_LOC_ATTR(_FLAT)

## Steps
1. Run the verbatim orphan checks (from the 24-00994166 resolution):
```sql
SELECT * FROM PACTRL_LOC_ATTR_FLAT WHERE LOC_ID NOT IN (SELECT LOC_ID FROM PACTRL_LOC);
SELECT * FROM PACTRL_LOC_ATTR      WHERE LOC_ID NOT IN (SELECT LOC_ID FROM PACTRL_LOC);
```
2. If orphans are confirmed, **delete this data** (per the case resolution) — via the Script Review / Script Deployment workflow, wrapped in a transaction with the verify-SELECT above.
3. Re-run the failing job (CANOMCLTG).

## Verification
- Both orphan queries return 0 rows; CANOMCLTG completes without the "Found Orphaned Location attribute" error.

## Workaround
None — the orphan rows must be removed for the job to pass.

## Source
SKILL_TIPS_Batch_Processing.md §14, §18-C. Case 24-00994166 (EQT).
