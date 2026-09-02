# Fix: Remove inverted-date nominations (BEG_GAS_DAY > END_GAS_DAY) from QCTRL_NOM_DTL

## Steps
1. Verify-SELECT the bad rows, then scope tightly to the SR/contract/gas-month before any script:
```sql
SELECT *                                   -- key cols: SR/contract, REC/DEL meter, BEG_GAS_DAY, END_GAS_DAY
FROM   QCTRL_NOM_DTL
WHERE  BEG_GAS_DAY > END_GAS_DAY
  /* AND scope to TSP/company/SR/contract/gas-month */;
```
2. Cloud Ops scripts the deletion (or correction) of the bad-dated nomination rows, wrapped in a transaction with the verify-SELECT counts recorded. Multiple cases closed exactly this way - "We were able to successfully script the deletion of this nomination data" (25-01052068); "Scripted to remove..." (25-01027984, 24-00946292).
3. Confirm the client's build carries ADO #1769494 (follow-up to #1672104): the mandatory validation `QGValidationNomGasDates` (Quorum.TIPS.Validation, QG metadata layer) now fires for all object states except Deleted and reads the correct dates during Copy Noms Forward - without it the corruption recurs.
4. If the build predates #1769494, push the upgrade alongside the data script.

## Verification
The step-1 SELECT returns zero rows in scope; the user can update/delete nominations for the affected SR/contract again; no new inverted-date rows appear after month-roll Copy Noms Forward.

## Workaround
None for the user - TIPS refuses to update or delete a nom whose dates are impossible, so the rows must be scripted out.

## Source
SKILL_TIPS_Nominations_Scheduling.md §4 / §15-B; SF cases 25-01051919, 25-01052068, 25-01027984, 24-00946292, 24-00962813; ADO #1672104, #1769494.
