# Fix: Daily Imbalance report blank until facility unlocked - schedule CLREALLOC with TIPSUNLOCK

## Steps
1. Confirm the signature: when a PPA has run (PPA_IND=1), stored proc `m_Sel_IMBALANCE` zeros the summed REC_QTY; that proc feeds the writer updating `QRPTS_IMBAL_ACCT`, so the Daily Imbalances report view reads zero/blank until the facility is unlocked each day.
```sql
SELECT * FROM QRPTS_IMBAL_ACCT WHERE FACILITY = '<FAC>' AND ACCT_DT = '<MTH>';
-- REC_QTY = 0 where activity exists and a PPA was run = the signature.
```
2. Apply the field-proven workaround (Harvest pattern, 24-00974581): configure the automatic batch step `CLREALLOC` (unchecks the reallocation flag) to run every time `TIPSUNLOCK` runs, so TIPS recalculates all allocated volume without skipping unadjusted meters.
3. Escalate the underlying proc behavior (`m_Sel_IMBALANCE` zeroing REC_QTY on PPA_IND=1) to Engineering as the root defect if the client wants a product fix.

## Verification
Next accounting day, the Daily Imbalance report populates without anyone manually unlocking the facility; QRPTS_IMBAL_ACCT shows non-zero REC_QTY where activity exists.

## Workaround
Until CLREALLOC is scheduled: manually unlock the facility each day, which forces the recalculation and populates the report.

## Source
SKILL_TIPS_System_Configuration.md §11 / §17-E; SF case 24-00974581 ("Facility Lock").
