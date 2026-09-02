# Fix: CAWDATA / SPAWNCAW / CAWDATAFS replication errors - realign the env-specific DataSync config

## Steps
1. Open the Connection Information screen and confirm the `TIPSDSDataHelper` (Data Sync) connection's .NET connection type is NULL - it must be NULL for CAWDATA to run on SQL Server (dev-confirmed on ADO #1534309: "this .NET connection type needs to be set to NULL for the TIPSDSDataHelper, and then the CAWDATA process completes successfully").
2. Align the `QARCH_DS_SRC_SYSTEM_SCHEMA` code table to the Connection Information screen values - it is environment-specific and goes stale (dev-confirmed root cause on ADO #1427530).
```sql
SELECT * FROM QARCH_DS_SRC_SYSTEM_SCHEMA;   -- must match the Connection Information screen for this env
```
3. Re-run CAWDATA; for the full-sync job re-run CAWFULLSYNC after correcting the connection.
4. Persist both settings in the environment's post-refresh scripts, or the next refresh wipes them (per ADO thread guidance).
5. API Host interaction warning: the TIPS API Host needs `DB_CON_STR_TYPE` POPULATED to start while CAWDATA needs it NULL - if the API Host then fails to start, the permanent fix is the APIHost.config change in ADO #1617552 / #1762912 (~2025.10 build).

## Verification
The CAWDATA/SPAWNCAW step in the facility/company batch completes; transactional data lands in QRMTIPS_CAW and external users see current gas days (no stale cut-off).

## Workaround
Until the config is corrected, external/CAW reports show no or stale data; there is no user-side workaround.

## Source
SKILL_ADO_TIPS_CAW_ExternalUsers_Integration_DataSync.md §3, §4, §13-A/B; ADO #1427530, #1534309, #1725660, #1617552, #1762912; SF cases 25-01015982, 22-00272601.
