# Fix: Reseed the SCTRL_INT_FULLSYNC 'MeterVolume' row lost in a DB refresh

## Steps
1. Confirm the seed row is missing:
```sql
SELECT * FROM SCTRL_INT_FULLSYNC WHERE INT_OBJECT_ID = 'MeterVolume';
```
2. If no row returns, reseed it (verbatim fix from case 23-00907706):
```sql
INSERT INTO SCTRL_INT_FULLSYNC (INT_OBJECT_ID, FULL_SYNC_DT, USER_ID, UPDT_DT)
VALUES ('MeterVolume', GETDATE(), 'FLOWCAL', GETDATE());
```
3. Re-run the core volume/analysis interface step (or wait for the scheduled import).
4. Add the reseed to the environment's post-refresh script so the next refresh does not wipe it again.

## Verification
```sql
SELECT * FROM SCTRL_INT_FULLSYNC WHERE INT_OBJECT_ID = 'MeterVolume';
```
Row present, and the next volume interface run actually writes meter-volume records (check the process log for the run and the Daily Positions data).

## Workaround
None needed once the row is reseeded. Until then, meter volumes will not flow in from FlowCal; the interface step completes without doing anything.

## Source
SKILL_TIPS_Integration_DataSync.md §3 / §16-A; SF case 23-00907706.
