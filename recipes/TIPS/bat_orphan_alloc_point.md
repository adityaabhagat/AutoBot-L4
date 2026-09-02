# Fix: ALLOCATE fails — orphan QTRAN_ALLOC_POINT rows tied to nonexistent TRNX_IDs

## Steps
1. Run the verbatim orphan check (from case 22-00527472):
```sql
SELECT * FROM QTRAN_ALLOC_POINT P
LEFT JOIN QTRAN_TRNX_ID T ON P.TRNX_ID = T.TRNX_ID
WHERE T.TRNX_ID IS NULL;
```
2. If orphans are confirmed, **delete the orphan QTRAN_ALLOC_POINT rows** via a Cloud Ops script (Script Review / Script Deployment; transaction + verify-SELECT first).
3. Re-run ALLOCATE for the scheduling month.

## Verification
- The orphan query returns 0 rows; ALLOCATE completes for the plant/scheduling month.

## Workaround
None — the orphan rows must be deleted before ALLOCATE will pass.

## Source
SKILL_TIPS_Allocations_PPA_Imbalance.md §4a, §16-A. Cases 22-00527472, 22-00527476 (Equitrans).
