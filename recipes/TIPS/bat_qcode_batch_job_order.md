# Fix: QCODE_BATCH_JOB sequence config ("last completed process ID doesn't match" / screen errors)

## Steps
1. Query the batch-job code table for the company/plant:
```sql
SELECT * FROM QCODE_BATCH_JOB ORDER BY ROW_ID;
```
2. Delete any **fully duplicated rows** (this was the fix for the Company Batch Job screen erroring on open/retrieve — 24-00942212, 24-00941908).
3. Correct the hidden **ROW_ID** ordering. Verbatim from 25-00996637: "Reordered the ROW_ID in the db for QCODE_BATCH_JOB, for Settle process. It has to be first SETTLEAGH (Monthly) and then SETTLEDAY (Daily) — it's a hidden column that identifies and orders that row."
4. If a batch job exists in Classic but is missing in Web, configure its **Process Type** on the process definition (25-01014535).
5. Re-run Post Results / re-open the batch screen.

## Verification
- Post Results completes without "the last completed process ID doesn't match what is required to post".
- The Company Batch Job screen opens and retrieves without error; the job appears in Web.

## Workaround
Run the affected job from the UI that still sequences correctly (usually Classic) until the config is corrected.

## Source
SKILL_TIPS_Batch_Processing.md §6, §18-E. Cases 25-00996637, 24-00942212, 24-00941908, 25-01014535.
