# Fix: Delete orphan open-ended SCTRL_MTR_FACILITY rows blocking Meter Definition / Shared Meter saves

## Steps
1. Verify-SELECT the orphan rows for the affected meter (orphan = an open-ended link to a facility/plant the meter should not be on; WTG pattern is a bogus link to plant 999):
```sql
SELECT * FROM ESUITE.SCTRL_MTR_FACILITY
WHERE  MTR_NO = '<MTR_NO>' AND EFF_DT_TO IS NULL;
```
2. Cross-check the header side and overlapping timeslices (MER pattern, ADO #1722628):
```sql
SELECT * FROM SCTRL_MTR_HEADER          WHERE MTR_NO = '<MTR_NO>' ORDER BY EFF_DT_FROM;
SELECT * FROM SEXTN_MTR_HEADER_QRMTIPS  WHERE MTR_NO = '<MTR_NO>' ORDER BY EFF_DT_FROM;
```
3. Script the deletion of the orphan open-ended row(s) only (scoped to the named meter and bogus facility), wrapped in a transaction with the verify-SELECT row counts recorded. Route via a Script Review / Script Deployment WI (pattern: ADO #1689827 WTG, #1758912/#1758697 MER, #1734858, #1722628).
4. Long-term: check whether the client's build carries ADO #1561405 ("Remove SCTRL_MTR_FACILITY from Integration Synch tables") - if these recur monthly, the build lacks it.

## Verification
Re-run the step-1 SELECT: zero orphan open-ended rows remain for the meter. The user can now save the Meter Definition / Shared Meter screen.

## Workaround
None for the user - the screens stay blocked for that meter until the orphan rows are scripted out.

## Source
SKILL_TIPS_Integration_DataSync.md §7 / §16-B; SF cases 25-00997682, 24-00972581, 24-00984237; ADO #1689827, #1758912, #1758697, #1734858, #1722628, #1561405.
