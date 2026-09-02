# Fix: Location attribute not selectable / meter missing from nom picklist — insert the missing PACTRL_LOC_ATTR row

## Steps
1. Audit the location's attribute rows:
```sql
SELECT a.LOC_ID, a.LOC_ATTR_CD, a.ATTR_VAL, l.LOC_NM, l.LOC_STATUS_CD
FROM   PACTRL_LOC_ATTR a
JOIN   PACTRL_LOC l ON l.TSP_NO = a.TSP_NO AND l.LOC_ID = a.LOC_ID
WHERE  a.TSP_NO = {tsp} AND a.LOC_ID = '<LOC_ID>';
-- Missing NOMINATABLE row  -> location absent from the nom picklist (26-01097568)
-- Missing INTERRUPTIBLE row -> attribute not selectable on converted locations (26-01096011)
```
2. Insert the missing attribute row with value `0` (unchecked) so it becomes selectable/toggleable in the UI (pattern from the script attached to case 26-01096011 — Template M):
```sql
INSERT INTO PACTRL_LOC_ATTR (TSP_NO, LOC_ID, LOC_ATTR_CD, ATTR_VAL)
SELECT {tsp}, l.LOC_ID, '<ATTR_CD>', 0      -- e.g. '<ATTR_CD>' = INTERRUPTIBLE
FROM   PACTRL_LOC l
WHERE  l.TSP_NO = {tsp}
  AND  l.LOC_ID IN (<CONVERTED_LOC_LIST>)
  AND  NOT EXISTS (SELECT 1 FROM PACTRL_LOC_ATTR a
                   WHERE a.TSP_NO = l.TSP_NO AND a.LOC_ID = l.LOC_ID
                     AND a.LOC_ATTR_CD = '<ATTR_CD>');
```
3. Verify the exact column names (`LOC_ATTR_CD` / `ATTR_VAL`) against the target schema before running — the binary value column may differ by version.
4. For the nom-picklist symptom, the business user then checks the **Nominatable** attribute on the Location Maintenance screen (adding the meter to a location group alone is NOT enough).

## Verification
Re-run the step-1 audit — the attribute row must exist for each target location. The attribute must now be toggleable on the Location Maintenance screen, and (for Nominatable) the meter must appear on the nomination-screen picklist.

## Workaround
None needed once identified — the data insert is the fix; until then the user cannot enable the attribute through the UI because the row simply does not exist.

## Source
SKILL_Pipeline_Admin_Config.md §4, §14-A and §15 Template M — SF cases 26-01096011 (script attached), 26-01097568.
