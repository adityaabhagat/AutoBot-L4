# Fix: Hard-delete a mis-entered / duplicate QPTM contract (standard cascade)

## Steps
1. Get identifiers: `TSP_NO` and the exact bad `CTR_NO` ({contract}). Confirm with the client which K is the bad one.
2. **Verify the contract is EMPTY** — zero nominations (see Verification). A contract WITH nominations must NOT be hard-deleted; if such a delete succeeded via the UI, that is delete-guard defect 24-00982700.
3. Provide the standard cascade-delete script to Cloud Ops (verbatim template from ADO **#1601380** `TEP_PRD_QPTM_1_Delete_Contract.sql` and **#1586886** `TEP_UAT_QPTM_1_Delete_Contract.sql`; concrete K# redacted to `<CTR_NO>`). Delete strictly **child → parent**:
```sql
BEGIN TRAN;  -- verify counts before COMMIT

-- 0. VERIFY: confirm this is the bad, empty contract
SELECT CTR_NO, TSP_NO, BA_NO, TOS_CD, EFF_DT_FROM, EFF_DT_TO
FROM   SCTRL_CTR_HEADER WHERE CTR_NO = '<CTR_NO>';

-- 1. Child / dependent rows FIRST
DELETE FROM KCTRL_CTR_LOC         WHERE CTR_NO = '<CTR_NO>';   -- contract locations / paths
DELETE FROM KVALD_CTR_AMEND       WHERE CTR_NO = '<CTR_NO>';   -- amendments
DELETE FROM KCTRL_CTR_USER_DEF    WHERE CTR_NO = '<CTR_NO>';   -- user-defined fields
DELETE FROM KCTRL_CTR_ATTR_FLAT   WHERE CTR_NO = '<CTR_NO>';   -- denormalized attr cache (Web binds here)
DELETE FROM KCTRL_CTR_ATTR        WHERE CTR_NO = '<CTR_NO>';   -- contract attributes
DELETE FROM SEXTN_CTR_HEADER_QPTM WHERE CTR_NO = '<CTR_NO>';   -- QPTM extension header
DELETE FROM KXREF_CTR_XREF_NOTE   WHERE CTR_NO = '<CTR_NO>';   -- contract notes (only if notes exist)

-- 2. Parent header LAST
DELETE FROM SCTRL_CTR_HEADER      WHERE CTR_NO = '<CTR_NO>';

-- COMMIT;  -- only after the counts match expectations; else ROLLBACK;
```
4. For a **duplicate slice** (same K#, same amend seq/date created by the save-instead-of-update defect, ADO #1383354/#1723832) remove only the duplicate slice scoped by `HIST_IDX`/`AMEND_SEQ_NO` — not the whole contract.
5. Always scope by `CTR_NO` (plus `TSP_NO` where the schema is multi-TSP). Older/on-prem clients receive this as a PDM instead of a self-service script.

## Verification
```sql
-- Contract must carry NO nominations before deletion:
SELECT COUNT(*) AS NOM_ROWS FROM NNCTRL_NOM_DTL
WHERE  TSP_NO = {tsp} AND SR_CTR_NO = '{contract}';
-- After deletion, the header must be gone:
SELECT COUNT(*) FROM SCTRL_CTR_HEADER WHERE CTR_NO = '{contract}';
```

## Workaround
Until the delete is deployed, the bad contract can simply be left untouched — do not transact against it; it does not affect other contracts or billing as long as no nominations/charges are entered on it.

## Source
SKILL_Contracts.md §11 (verbatim cascade from ADO #1601380 and #1586886 attachments) — SF cases 23-00902451, 23-00890782; duplicate-slice defect ADO #1383354 / #1723832.
