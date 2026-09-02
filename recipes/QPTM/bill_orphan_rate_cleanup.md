# Fix: Orphan RTCTRL_RATE_DTL cleanup (end-date or delete detail rows with no header parent)

## Steps
Verbatim engine pattern from ADO #1756911 attachments (`1756911_ORPHAN_RATES.sql` / `_UPDATED.sql`), redacted to placeholders. Run the verify-SELECT and eyeball before/after counts BEFORE `COMMIT`.
```sql
BEGIN TRANSACTION;

-- 0. VERIFY FIRST — list orphan rate-header IDs (detail with NO matching header on TSP+HDR+eff dates)
PRINT 'BEFORE UPDATES';
SELECT DISTINCT H.RATE_HDR_ID
FROM   RTCTRL_RATE_DTL H
LEFT JOIN RTCTRL_RATE_HDR D
       ON  H.TSP_NO      = D.TSP_NO
       AND H.RATE_HDR_ID = D.RATE_HDR_ID
       AND H.EFF_DT_FROM = D.EFF_DT_FROM
       AND H.EFF_DT_TO   = D.EFF_DT_TO
WHERE  D.TSP_NO IS NULL
  AND  H.EFF_DT_TO >= '<CUTOFF_DATE>';

-- 1a. FIX OPTION 1 — end-date the orphan detail to a closed month-end (one block per orphan RATE_HDR_ID)
UPDATE RTCTRL_RATE_DTL
SET    EFF_DT_TO = '<MONTH_END>'
WHERE  TSP_NO = <TSP_NO>
  AND  RATE_DTL_ID IN (<DTL_ID_1>, <DTL_ID_2>, ...);

-- 1b. FIX OPTION 2 — when the detail must not exist at all, DELETE the orphan detail rows
DELETE FROM RTCTRL_RATE_DTL
WHERE  TSP_NO = <TSP_NO>
  AND  RATE_DTL_ID IN (<DTL_ID_1>, <DTL_ID_2>, ...);

-- 2. RE-VERIFY — the orphan list should now be empty (or only expected rows)
PRINT 'AFTER UPDATES';
SELECT DISTINCT H.RATE_HDR_ID
FROM   RTCTRL_RATE_DTL H
LEFT JOIN RTCTRL_RATE_HDR D
       ON  H.TSP_NO = D.TSP_NO AND H.RATE_HDR_ID = D.RATE_HDR_ID
       AND H.EFF_DT_FROM = D.EFF_DT_FROM AND H.EFF_DT_TO = D.EFF_DT_TO
WHERE  D.TSP_NO IS NULL AND H.EFF_DT_TO >= '<CUTOFF_DATE>';

COMMIT;   -- only after the AFTER list is clean; else ROLLBACK;
```
Then re-run the failing process (CANOMCLTG / BLINVGEN) for the affected TSP(s).

## Verification
The BEFORE/AFTER orphan-detector SELECT above returns 0 rows after the fix; CANOMCLTG/BLINVGEN complete without the random CAS/"all pipes" errors and system slowness clears.

## Workaround
None practical — the orphan detail rows corrupt rate resolution for every pipe until they are end-dated or deleted. Clients that hit this repeatedly should stand up orphan-rate monitoring in PRD (run the detector SELECT on a schedule).

## Source
SKILL_Billing.md §14 Template A and §5.1; ADO #1756911 (verbatim SQL attachments); SF 25-01044370, 25-01044614, 25-01044914 (TEP).
