# Fix: Orphaned location stopping ALL batch jobs in a TSP (cross-table cleanup)

## Steps
1. Confirm the orphan: the location/meter code appears in attribute/group/contract/meter tables but is no longer a valid location (verify-SELECTs below). In case 24-00951885 the orphan (`KATYPOOL`/`ATPKTYMXP`) made every batch job in every TSP stop with a warning.
2. Run the verify-SELECTs first:
```sql
SELECT 'PACTRL_LOC_ATTR' tbl, COUNT(*) n FROM PACTRL_LOC_ATTR WHERE LOC_ID='<LOC_ID>'
UNION ALL SELECT 'KCTRL_CTR_LOC', COUNT(*) FROM KCTRL_CTR_LOC WHERE LOC_ID_2='<LOC_ID>'
UNION ALL SELECT 'SEXTN_MTR_HEADER_QPTM', COUNT(*) FROM SEXTN_MTR_HEADER_QPTM WHERE MTR_NO='<LOC_ID>';
```
3. Delete the orphaned location's rows in this order (verbatim from ADO **#1660692** attachment `WWM Script.sql`):
```sql
DELETE FROM PACTRL_LOC_ATTR             WHERE LOC_ID = '<LOC_ID>';
DELETE FROM PACTRL_LOC_ATTR_FLAT        WHERE LOC_ID = '<LOC_ID>';
DELETE FROM PACTRL_SYS_LOC_GRP_LOC      WHERE LOC_ID = '<LOC_ID>';
DELETE FROM PACTRL_LOC_USER_DEF         WHERE LOC_ID = '<LOC_ID>';
DELETE FROM PACTRL_LOC_CAP              WHERE LOC_ID = '<LOC_ID>';
DELETE FROM PACTRL_SYS_LOC_GRP_LOC_FLAT WHERE LOC_ID = '<LOC_ID>';
DELETE FROM KCTRL_CTR_LOC               WHERE LOC_ID_2 = '<LOC_ID>';
DELETE FROM PAVALD_LOC                  WHERE LOC_ID = '<LOC_ID>';
DELETE FROM SEXTN_MTR_HEADER_QPTM       WHERE MTR_NO = '<LOC_ID>';
```

## Verification
Re-run the step-2 verify-SELECTs — all counts must be zero. Then re-run any previously-failing batch job (e.g. the nightly) and confirm it completes without the orphaned-record warning.

## Workaround
None practical — while the orphan rows exist, batch jobs in the TSP keep stopping with the warning; prioritize the cleanup script.

## Source
SKILL_Integration_Processing.md §15-D and §16 Script B (verbatim from ADO #1660692 `WWM Script.sql`) — SF case 24-00951885.
