# Fix: ASSCGLM gas-lift duplication after reallocation-mode rerun

## Steps
1. Confirm the pattern for the affected production month:
```sql
SELECT * FROM QTRAN_ALLOC_VOL
WHERE  PROCESS_ID = 'ASSCGLM' AND PROD_DT = '{prod_mth}'
ORDER BY UPDT_DT DESC;
SELECT * FROM QTRAN_PLANT_STATUS_REALLOC WHERE PROD_DT = '{prod_mth}';
```
   Stacked ASSCGLM rows after a realloc-mode rerun = the ADO #1731166 defect (the step re-inserts without purging prior ASSCGLM rows when the plant runs dailies in reallocation mode).
2. **If the fix is NOT on the client build:** either take the plant **out of reallocation mode** on the facility lock screen before re-running, **or** have Cloud Ops purge the duplicate `PROCESS_ID='ASSCGLM'` rows from `QTRAN_ALLOC_VOL` (scoped to plant/prod month, verify-SELECT first), then re-run.
3. **Durable fix:** get the client to build **2025.04.1.3** or later — the shipped change deletes existing `QTRAN_ALLOC_VOL` rows with `PROCESS_ID='ASSCGLM'` before new entries are inserted and only considers meters with `process_ind=1` (ADO #1731166; PRs 114597/114879-114881, `Quorum.TIPS.ClassicBatch`).
4. Verify the ASSCGLM step is registered/ordered for the client in `<CLIENT>.TIPS.Metadata QARCH_CTRL_PROCESS_STEP*.json` before chasing anything further.

## Verification
- Re-run the plant: the Step 1 query shows a single set of ASSCGLM rows per meter for {prod_mth} (no stacking), and gas-lift / netted gas-lift MMBTU volumes match pre-duplication values downstream (allocation groups, statements).

## Workaround
Take the plant out of reallocation mode before any rerun until the 2025.04.1.3 hotfix is consumed; a realloc-mode rerun will re-stack the rows every time.

## Source
SKILL_TIPS_Master_Data_Contracts.md §6 and §16-C (SF 25-01023169 ETP; 25-01041541 AHS = dup of the same defect); SKILL_ADO_TIPS_MasterData_Contracts_CCT_Meter.md §5 (ADO #1731166 fixed 2025.04/2025.04.1.3; dups #1734347, #1761294).
