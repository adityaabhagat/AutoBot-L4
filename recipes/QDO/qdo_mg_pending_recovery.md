# Fix: MG partially interfaced to SAP and stopped in Pending — COPY_DVDS2, revert, re-approve

## Steps
1. Confirm the signature: the MG stopped in **Pending** with only some tiers processed (field example: MG 4513, 11 of 87 tiers), i.e. a partial SAP-side integration, not a QDO engine failure.
2. Check the MG header status first:
```sql
SELECT GRP_NO, GRP_ST_CD, MAINT_REASON_CD, MAINT_STATUS, CREATE_USER, CREATE_DT, UPDT_DT
FROM   DONL_DVD_GRP
WHERE  GRP_NO = '<MG#>';   -- GRP_ST_CD 3 = committed back into QDO
```
3. **Run `COPY_DVDS2` for the partially-completed groups** so the already-processed tiers are committed.
4. **Revert the MG to Submitted.**
5. **Re-approve the MG** so the remaining tiers process.

## Verification
- All tiers of the MG show processed and the MG advances from Pending to Completed.
- The DOI Sync events for the remaining tiers reach SAP-PRA without PK/duplicate-transaction errors.

## Workaround
None at the user level — do not delete/recreate the MG (the partially-committed tiers would be orphaned); use the COPY_DVDS2 + revert + re-approve recovery.

## Source
SKILL_QDO_Division_Orders.md §7/§10 and §15-A. Case: 25-01051115.
