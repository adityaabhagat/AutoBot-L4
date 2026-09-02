# Fix: TRNX_ID exhaustion/collision on MeasAnalysis (reset + long-term patch)

## Steps
1. Confirm the collision for the failing month:
```sql
SELECT TRNX_ID, COUNT(*) AS DUP_CT
FROM   QTRAN_STD_ANALYSIS_BASE
WHERE  PROD_DT = '{prod_mth}'
GROUP BY TRNX_ID
HAVING COUNT(*) > 1;
```
2. **Short-term (field-proven, 23-00916043):** have Cloud Ops reset the TRNX_ID sequence/counter to 0, then re-run the MeasAnalysis / Facility Batch Job.
3. **Long-term:** confirm the client's patch contains the TRNX_ID integer-limit fix — ADO **#1617830** (Bug, Closed) + **#1631131** (Task); settlement-side split scripts in ADO **#1773003** (Core TIPS 17.0 — SETTLEMGR TRNX_ID Split Scripts). If not, schedule the patch.
4. Distinguish from the recycle-by-design complaint: stale Paystation `User_ID`/`Updt_Dt` after the purge-recycle change is **expected behavior** — revert with Facility Config `IGNORE_PURGE_IND = 1` (24-00972261), not a reset.

## Verification
- Step 1 query returns zero rows after the reset/rerun.
- The MeasAnalysis step completes for all facilities in the Facility Batch Job without a unique-constraint error on `QTRAN_STD_ANALYSIS_BASE.TRNX_ID`.

## Workaround
The reset to 0 IS the interim workaround; it will recur until the ADO #1617830 integer-limit fix is on the client build. Warn the client the failure can return at month-end volume peaks until patched.

## Source
SKILL_TIPS_Measurement_Ticketing.md §8a and §18-C. SF cases 23-00916043 (reset to 0), 23-00916530 (long-term fix); ADO #1617830, #1631131, #1656405, #1773003.
