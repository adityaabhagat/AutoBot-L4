# Fix: Standardized ghost/duplicate nomination delete (QPTM NNCTRL cascade — Template A)

Removes an orphaned/overlapping ("ghost") nomination that blocks submission with "dates that overlap another nomination" / "duplicate key", or that cannot be deleted/zeroed from the UI. Deployed to PRD by Cloud Ops via a "Request Global Cloud Ops" work item; time-boxed to the cycle deadline.

## Steps
1. Get the exact identifiers from the client: `TSP_NO`, `NOM_ID`, shipper (`SR_BP_NO`), `SR_CTR_NO`, gas-day range, cycle, and the deadline. Clients almost always supply the NOM_ID.
2. Run the verify-SELECT (step 0 in the script) and the overlap/ghost diagnostics (SKILL_Nominations.md §4 SQL #1–#3). Confirm you are deleting the BAD record, not the live one. Red flag for the #1761678 pattern: `NNCTRL_ACTV_DTL` NOM_IDs jumping to 10000000+ while the table's real max NOM_ID is much lower.
3. Provide the cascade delete script below to Cloud Ops for PRD deployment (one block PER blocked gas-day range; repeat per `NOM_SEQ_NO`/range — do not widen the range). Delete order is child → parent or FK/constraint errors block the delete.

```sql
-- Standardized nom-delete script template (redacted) — QPTM NNCTRL cascade
-- Params: <TSP_NO>, <NOM_ID>, <NOM_SEQ_NO>, <BEG_DAY>, <END_DAY> (e.g. 'May  8 2026 12:00AM')
BEGIN TRAN;  -- (or BEGIN/COMMIT per DB engine; verify counts before COMMIT)

-- 0. VERIFY FIRST — confirm you are targeting the bad row(s), note the count
SELECT NOM_SEQ_NO, NOM_ID, BEG_GAS_DAY, END_GAS_DAY, CYCLE_ID, NOM_STAT_CD, ACTV_NO
FROM   NNCTRL_NOM_DTL
WHERE  TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID>
  AND  BEG_GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>';

-- 1. Confirmation (hourly then base)
DELETE FROM CFCTRL_CONF_HR WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID> AND GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>';
DELETE FROM CFCTRL_CONF    WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID> AND GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>';

-- 2. Cycle roll-up tables
DELETE FROM NNCTRL_ALLOC_MAX_CYCLE     WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID> AND GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>';
DELETE FROM NNCTRL_NOM_LATEST_CYCLE    WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID> AND GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>';
DELETE FROM NNCTRL_NOM_OVERALL_CYCLE   WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID> AND GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>';

-- 3. Activity (hourly, error, base) — resolve ACTV_NO via subquery on the activity table
DELETE FROM NNCTRL_ACTV_DTL_HRLY WHERE TSP_NO = <TSP_NO> AND ACTV_NO IN (
  SELECT DISTINCT ACTV_NO FROM NNCTRL_ACTV_DTL
  WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID>
    AND (BEG_GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>' OR END_GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>'));
DELETE FROM NNCTRL_ACTV_DTL_ERR  WHERE TSP_NO = <TSP_NO> AND ACTV_NO IN (
  SELECT DISTINCT ACTV_NO FROM NNCTRL_ACTV_DTL
  WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID>
    AND (BEG_GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>' OR END_GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>'));
DELETE FROM NNCTRL_ACTV_DTL      WHERE TSP_NO = <TSP_NO> AND NOM_ID = <NOM_ID>
    AND (BEG_GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>' OR END_GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>');

-- 4. Nom detail (hourly, error, base) — keyed by NOM_SEQ_NO (NOT NOM_ID); delete the parent LAST
DELETE FROM NNCTRL_NOM_DTL_HRLY WHERE TSP_NO = <TSP_NO> AND NOM_SEQ_NO = <NOM_SEQ_NO>;
DELETE FROM NNCTRL_NOM_DTL_ERR  WHERE TSP_NO = <TSP_NO> AND NOM_SEQ_NO = <NOM_SEQ_NO>;
DELETE FROM NNCTRL_NOM_DTL      WHERE TSP_NO = <TSP_NO> AND NOM_SEQ_NO = <NOM_SEQ_NO>;

-- COMMIT;  -- only after row counts above match expectations; else ROLLBACK;
```

4. Transaction safety (from the real scripts): run the verify-SELECT and eyeball the count BEFORE deleting; delete strictly child → parent (confirmation → cycle → activity → nom-detail); the parent `NNCTRL_NOM_DTL` row is keyed by `NOM_SEQ_NO` while child rows key on `NOM_ID` + gas-day range — do not mix them up; wrap in `BEGIN TRAN ... COMMIT` so you can `ROLLBACK` if a count is off.
5. Confirm deletion scope with the client first: delete "for GD `<n>` forward" as specified, not the whole month. If only one cycle is blocked and the client can nominate under a later cycle (ID2), some clients prefer to leave it rather than run a "noisy" script mid-day (26-01096143).
6. TIPS/QLNG noms use Template B instead (`QCTRL_*` tables keyed by `NOM_HASH_ID`, QRMTIPS schema) — see SKILL_Nominations.md §4.

## Verification
- Re-run the step-0 verify-SELECT: 0 rows for the deleted `NOM_ID`/`NOM_SEQ_NO`/gas-day range.
- Have the client re-query the Nom Submission screen and resubmit the nomination before the cycle deadline — the overlap/duplicate error must no longer fire.
- For the #1761678 pattern, re-check `NNCTRL_ACTV_DTL` for the ACTV_NO: no NOM_IDs in the 10000000+ range should remain.

## Workaround
Until the script is deployed: if only one cycle is blocked, the shipper can keep nominating under the next open cycle (for example ID2 instead of ID1). Some "can't delete" cases resolve with no script at all — the client fixes the ghost themselves on a call or the blocking cycle simply closes; try the cheap path first.

## Source
SKILL_Nominations.md §4 (Template A, verbatim from ADO #1806364 `NomDeletionScriptTEP_MAY2026.sql` and ADO #1747369), §10 Deletion Runbook, §18. ADO: #1806364, #1747369, #1761678, #1699360, #1739654. SF cases: 26-01099232, 25-01049356, 25-01060757, 25-01059423, 26-01097145, 24-00995062, 25-00996203.
