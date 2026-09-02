# Fix: Doubled quantity line on invoice from REC + RECF — set SHOW_QTY_INVOICE_IND = 0

## Steps
Config fix proven in WIT (ADO #1813295, Acceptance). The allocation output in `ALCTRL_ALLOC` is correct; only the invoice presentation doubles.
1. Verify the current config:
```sql
SELECT TSP_NO, TOS_CD, CHARGE_BASIS_CD, SHOW_QTY_INVOICE_IND
FROM   BLXREF_TOS_CHARGE_BASIS
WHERE  TSP_NO = {tsp} AND TOS_CD = 'ITS' AND CHARGE_BASIS_CD IN ('REC','RECF');
```
2. Set the indicator to 0 (wrap in a transaction; verify-SELECT before COMMIT):
```sql
UPDATE BLXREF_TOS_CHARGE_BASIS
SET    SHOW_QTY_INVOICE_IND = 0
WHERE  TSP_NO = {tsp} AND TOS_CD = 'ITS' AND CHARGE_BASIS_CD IN ('REC','RECF');
```
3. **Re-run BLINVGEN** for the affected invoice group / accounting month.

## Verification
The invoice no longer shows the merged doubled quantity line (e.g. 8,600 + 8,600 = 17,200 at $0); re-run the step-1 SELECT and confirm `SHOW_QTY_INVOICE_IND = 0` for both charge bases.

## Workaround
None needed once identified — the amounts were never wrong (the doubled line is quantity presentation at $0); tell the customer the underlying allocation (receipt and delivery of equal quantity) is correct while the config change is scheduled.

## Source
SKILL_ADO_QPTM_Allocations_PPA_Imbalance.md §10 and §16-G; ADO #1813295 (dup #1813294); SF 26-01103426 (WIT).
