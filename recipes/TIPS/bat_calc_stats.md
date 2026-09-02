# Fix: Batch job suddenly slow on the first run after posting — stale optimizer stats / CALC_STATS

## Steps
1. Confirm the pattern: the slowness appears on the **first run after a posting cycle or refresh** (verbatim root cause from 23-00892948: "problem was only occurring the first time they ran journal a day after having posted all their plants (which meant the QTRAN tables were empty when stats ran during the night)"). If slowness is constant and data-volume-proportional, this recipe does not apply — capture the long-running SQL and escalate as a perf defect.
2. Have the DBA **gather statistics manually** on the hot QTRAN tables (this alone cleared hung jobs — 24-00975612).
3. Permanently: **add the CALC_STATS process step** to the affected job — Journal (23-00892948), ALLOCATE (23-00932008), JOURNALIMB at position 2 (ADO #1598509; note this is a client-managed layer, so the client must add the step manually — it cannot ship in a core patch).
4. Add the job's hot tables (e.g. `QTRAN_PAYSTATION`) to **`QCODE_TABLE_CALC_STATS`** via a DB-change script (ADO #1633473 / #1644834 / #1706988 pattern):
```sql
SELECT * FROM QCODE_TABLE_CALC_STATS;
```

## Verification
- The next first-run-after-posting completes in normal time (e.g. JOURNALIMB back from 1.5h to ~10min per 23-00892948).

## Workaround
DBA manual stats gather immediately before the first heavy run of each cycle, until the CALC_STATS step and table list are in place.

## Source
SKILL_TIPS_Batch_Processing.md §9a, §18-F; SKILL_ADO_TIPS_Settlement_Revenue_Statements_Reporting.md §11. Cases 23-00892948, 23-00932008, 24-00975612; ADO #1598509, #1633473, #1644834, #1706988.
