# Fix: BLINVGEN sequence exhaustion — archive/purge staging table + reseed the counter

## Steps
1. Identify the maxed counter:
```sql
SELECT * FROM QTRAN_SEQ      WHERE LAST_NO >= 2000000000 ORDER BY LAST_NO DESC;
SELECT * FROM QARCH_TRAN_SEQ WHERE LAST_NO >= 2000000000 ORDER BY LAST_NO DESC;
```
2. Ensure the staging table (e.g. `BLTRAN_INVOICE_INPUT`, `BLTRAN_INVOICE_RATE`, `BLRPTS_10_INVOICE_DOC_IMB_DTL`) is in the short-cycle **Archive Definition** (`ARCH_7_DAY`; report staging → `RPTS_CORE`), then run the purge (`QPTM_PRG`) so live rows are gone.
3. Reset the counter (safe because the table purges, so old/new numbers cannot collide) — wrap in a transaction with a verify-SELECT:
```sql
UPDATE QTRAN_SEQ SET LAST_NO = 1
WHERE  SEQ_NM = '<table>.<col>' AND TSP_NO = '{tsp}';
-- MSSQL identity column instead of QTRAN_SEQ:
-- DBCC CHECKIDENT('<table>', RESEED, 1);
-- (SQL Server: dev-suggested alternative is the UTIL_RESEED_IDENTITIES stored proc.)
```
4. Re-run BLINVGEN for the affected accounting month and confirm it completes.
5. Confirm the client build carries the long-term prevention fixes **#1384511 / #1572396 / #1600044** — older builds recur (XCL hit it repeatedly; ~6 months of runway per reset). Add monitoring so the sequence alerts BEFORE maxing.

## Verification
```sql
SELECT SEQ_NM, TSP_NO, LAST_NO FROM QTRAN_SEQ WHERE LAST_NO >= 2000000000;  -- expect 0 rows
```
BLINVGEN/PANIGHTLY reruns without "ERROR SETTING VALUE FOR COLUMN ... BLTRAN_INVOICE_INPUT" / "too large or too small for an Int32".

## Workaround
None avoids the reseed — invoicing is hard-stopped until the counter is reset. If the client build lacks the prevention fixes, schedule proactive resets and plan the upgrade as the permanent fix.

## Source
SKILL_Billing.md §14 Template B and §4.1; SKILL_ADO_QPTM_Billing_Invoice_Rates.md §5; ADO #1665295, #1607556, #1639324, #1728741; SF 24-00957495, 23-00908498, 23-00907641.
