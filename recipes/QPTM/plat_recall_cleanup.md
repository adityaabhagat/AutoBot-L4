# Fix: Delete a stuck / orphaned Capacity Release Recall record (CRCTRL_RECALL_REPUT PDM)

## Steps
1. Identify the replacement contract number, the recall status code (e.g. `RC` = recalled) and the exact `UPDT_DT` of the bad row with the client.
2. **Verify the exact row first** (verbatim PDM pattern from case 22-00661770; concrete values redacted):
```sql
SELECT *
FROM   CRCTRL_RECALL_REPUT
WHERE  REPL_SR_CTR_NO = <REPLACEMENT_CTR_NO>
  AND  CR_STATUS_CD   = '<STATUS>'      -- e.g. 'RC' (recalled)
  AND  UPDT_DT        = '<UPDT_DT>';    -- pin the exact row by its update timestamp
```
3. Deploy the delete as a PDM / Cloud Ops script only after the count is confirmed (expect exactly 1 row), wrapped in a transaction:
```sql
DELETE FROM CRCTRL_RECALL_REPUT
WHERE  REPL_SR_CTR_NO = <REPLACEMENT_CTR_NO>
  AND  CR_STATUS_CD   = '<STATUS>'
  AND  UPDT_DT        = '<UPDT_DT>';
```
4. For a **cancelled recall that left bad `AWARD_AMEND_ID`s** (case 22-00661775), the PDM instead clears the corresponding bad rows in `CRCTRL_AWARD_AMEND` — same verify-then-delete pattern, pinned by ID/`UPDT_DT`.

## Verification
Re-run the step-2 SELECT — zero rows. The releaser must then be able to recall/reput normally on the replacement contract, and IPWS unsubscribed/recall quantities should reconcile.

## Workaround
Until the orphan row is removed, no further recall or reput action is possible on that replacement contract; no other contracts are affected.

## Source
SKILL_Capacity_Release.md §6 (verbatim WHERE predicate from the case 22-00661770 PDM) — SF cases 22-00661770, 22-00661775, 22-00875593.
