# Fix: PPA / Reallocation pop-up not firing on Contract Maintenance save (BLXREF_REALLOC_PPA mapping)

## Steps
1. Verify the code-table mapping the pop-up code expects (code table **27310**):
```sql
SELECT OBJECT_ID, DBTBL_NM FROM BLXREF_REALLOC_PPA WHERE OBJECT_ID LIKE 'QVPCONTRACT%';
```
   The code expects `OBJECT_ID = 'QVPCONTRACTMAINTENANCE'` with `DBTBL_NM = 'CONTRACTHEADER'`.
2. If the client instead carries `QVPCONTRACTHEADER` / `SCTRL_CTR_HEADER`, apply the verbatim client-data fix from ADO #1784462:
```sql
UPDATE BLXREF_REALLOC_PPA
SET    OBJECT_ID = 'QVPCONTRACTMAINTENANCE', DBTBL_NM = 'CONTRACTHEADER'
WHERE  OBJECT_ID = 'QVPCONTRACTHEADER' AND DBTBL_NM = 'SCTRL_CTR_HEADER';
```
3. If the mapping is already correct and the change was to the **Related-K (Shared MDQ)** effective date, the client build needs the ADO #1773033 code fix (the `HandleGenericScreenChangeEvent` handler was missing table `SCTRL_RELATED_CTR`) — cherry-picked to 2025.04 / 2025.10; confirm the build.

## Verification
Reproduce: change a contract **date** that impacts a **closed** accounting month and save — the PPA/Reallocation pop-up must appear and a `BLTRAN_PPA_EVENT` row must be written. Note the pop-up correctly does NOT fire when an unprocessed PPA event already exists for that contract + production month.

## Workaround
None needed for the pop-up itself; if a required PPA was missed, raise the PPA event manually for the impacted production month. Remember: a contract **status-only** change is NOT expected to trigger the pop-up — only date changes impacting a closed month do.

## Source
SKILL_ADO_QPTM_Contracts_RFS_Offer_CapacityRelease.md §10 G2 — ADO #1784462 (verbatim UPDATE), #1773033 (ENT Panaya Defect 90).
