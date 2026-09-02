# Fix: OFR/EFR blocked by unprocessed RSTG_OWNR_FUND_RLS rows — skip the bad TRANS_SEQ_NO

## Steps
1. Query the staging and error tables for the owner/transfer:
```sql
SELECT TRANS_SEQ_NO, PROC_FL, FROM_OWNER_BA, TO_OWNER_BA, SL_NO, SL_DETAIL_NO
FROM   RSTG_OWNR_FUND_RLS
WHERE  PROC_FL = 'N';   -- red flag: trailing space in FROM_OWNER_BA / TO_OWNER_BA

SELECT * FROM RSTG_OWNR_FUND_RLS_ERR WHERE TRANS_SEQ_NO IN ('<seq>');
```
2. If the rows are recoverable, **rerun OFR (CWOWFNDRLS via QP043) with "Process Rejected Records" = Y** for those seq numbers.
3. If the data is genuinely bad (trailing space in the Owner/BA number, FROM/TO BA mismatch) and cannot be cleaned in the app, mark the bad transfer's records processed (verify-SELECT in a transaction first):
```sql
UPDATE RSTG_OWNR_FUND_RLS SET PROC_FL = 'Y' WHERE TRANS_SEQ_NO IN ('<seq>');
```
4. Reprocess CWOWFNDRLS with Process Rejected Records = Y.

## Verification
- Rerun the OFR: the "DIVISION ORDER/OWNER HAS PENDING SUSPENSE RELEASE TRANSACTIONS THAT HAVE NOT BEEN PROCESSED" (`FUNDS_RLS`) message no longer appears.
- `SELECT COUNT(*) FROM RSTG_OWNR_FUND_RLS WHERE PROC_FL = 'N'` returns 0 for the affected owner/transfer.

## Workaround
Until the legacy rows are cleaned, rerun the OFR with the "Process Rejected Records" flag checked so previously-rejected rows are picked up. Newer builds no longer create the trailing-space rows; this cleanup is for legacy data only.

## Source
SKILL_QDO_Transfers_SuspendRelease.md §5. Cases: 25-01005386, 23-00918864, 23-00914643, 25-01036728, 25-01027352.
