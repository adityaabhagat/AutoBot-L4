# Fix: Deploy missing CORE table BLSTAG_PAL_EXT (LPS/PAL SQL 208 crash, no PEX billing lines)

## Steps
1. **Script `BLSTAG_PAL_EXT` from an instance that has it** (a DEV fixed earlier per WI #1836679, or any DTE instance). Do **not** hand-build the DDL from column lists — no CREATE DDL survives in any repo.
2. Create the object in each affected environment. An **empty** table is a complete fix for non-DTE clients: the CORE join is LEFT OUTER and only reads `EXT_DAY_COUNT` → NULL, byte-identical to the config-false branch output.
3. Rerun BLINVGEN **"Run All PPAs"** for all affected production months.
4. Confirm `CHARGE_BASIS_CD='PEX'` (PAL Extension) rows appear in `BLTRAN_INVOICE_GEN_QTY` for each rerun month.
5. **Reverse any manual LGA workaround entries** for the same periods to avoid double-billing.
6. Do **NOT** flip `BILLING/USE_DTE_BLRPTS_10_INVOICE_DOC_PAL=false` as a "fix" (silently changes the billing code path and leaves the CORE trap latent), and do **NOT** delete the CORE join (breaks DTE/QLNG PAL day-count).

## Verification
```sql
-- Object now exists (was NULL before the deploy):
SELECT OBJECT_ID('dbo.BLSTAG_PAL_EXT') AS obj_id;

-- PEX billing lines now written for the production month:
SELECT * FROM BLTRAN_INVOICE_GEN_QTY
WHERE  CHARGE_BASIS_CD = 'PEX' AND TSP_NO = {tsp} AND PROD_MTH = '{prod_mth}';
```
The BLINVGEN "Run All PPAs" rerun must complete without SQL 208 / "PAL statement records were not successfully inserted."

## Workaround
Until the table is deployed, the customer can enter manual LGA (adjustment) entries so the affected periods still bill — track every manual entry so it can be reversed after the rerun. Note the drift risk: the guarded 3.1.00.0069 drop script silently re-drops the restored table on any QDBManager 3.1.00 baseline re-run; the permanent CORE DDL restore rides ADO Bug #1836277 (open, no fixed-in version as of 2026-08-14).

## Source
SKILL_Billing.md §4.4; SF case 26-01106039 (EQC/EQT, predecessor 25-01058356); ADO Bug #1836277, WI #1836679 (DEV ops-deploy precedent / differential proof), WI #1836447, WI #1451380.
