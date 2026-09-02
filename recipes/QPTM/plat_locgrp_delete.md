# Fix: Delete a Location Group the UI refuses to delete (Cloud-Ops two-table script)

## Steps
1. Collect `TSP_NO` and the exact `LOC_GRP_ID`, and confirm **no transactional data** references the group:
```sql
SELECT g.LOC_GRP_ID, g.LOC_GRP_NM, g.ACTV_IND,
       (SELECT COUNT(*) FROM PACTRL_LOC_GRP_ASSOC_QTY q
        WHERE q.TSP_NO = g.TSP_NO AND q.LOC_GRP_ID = g.LOC_GRP_ID) AS ASSOC_QTY_ROWS
FROM   PACTRL_LOC_GRP g
WHERE  g.TSP_NO = {tsp} AND g.LOC_GRP_ID = '<LOC_GRP_ID>';
```
2. Provide the delete script to Cloud Ops via a **Request Global Cloud Ops** work item (ADO #1780227 deployed `WWM_Loc_Grp_ID_Delete_Script.sql` this way). Verbatim template (Template L, source ADO #1778532/#1780227 — real values were TSP 505 / group 'PLA'); **child `_ASSOC_QTY` rows first, then the group**:
```sql
IF EXISTS (SELECT 1 FROM PACTRL_LOC_GRP_ASSOC_QTY
           WHERE TSP_NO = <TSP_NO> AND LOC_GRP_ID = '<LOC_GRP_ID>')
    DELETE FROM PACTRL_LOC_GRP_ASSOC_QTY
    WHERE LOC_GRP_ID = '<LOC_GRP_ID>' AND TSP_NO = <TSP_NO>;

IF EXISTS (SELECT 1 FROM PACTRL_LOC_GRP
           WHERE TSP_NO = <TSP_NO> AND LOC_GRP_ID = '<LOC_GRP_ID>')
    DELETE FROM PACTRL_LOC_GRP
    WHERE LOC_GRP_ID = '<LOC_GRP_ID>' AND TSP_NO = <TSP_NO>;
```
3. For **bulk inactive-group cleanup** (case 25-01047587): run the same two-table delete looped over the inactive `LOC_GRP_ID` list pulled from `PACTRL_LOC_GRP` for the TSP, verifying each is unreferenced first.

## Verification
```sql
SELECT COUNT(*) FROM PACTRL_LOC_GRP
WHERE  TSP_NO = {tsp} AND LOC_GRP_ID = '<LOC_GRP_ID>';   -- must return 0
```
The group must also no longer appear in any location-group picklist.

## Workaround
Until the script runs, mark the group **Inactive** — note however that picklists do not filter inactive groups (the 25-01047587 confusion), so warn users to ignore it.

## Source
SKILL_Pipeline_Admin_Config.md §5 and §15 Template L (verbatim from ADO #1778532/#1780227 `WWM_Loc_Grp_ID_Delete_Script.sql`) — SF cases 26-01064296, 25-01047587.
