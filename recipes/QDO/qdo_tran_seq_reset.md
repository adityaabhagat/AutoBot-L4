# Fix: Post-refresh primary-key errors on transfers/MEG — reset QARCH_TRAN_SEQ.LAST_NO

## Steps
1. Confirm the environment was recently **refreshed** and transfers / MEG maintenance now fail on a primary-key error (the post-refresh script did not reset the sequence).
2. Run the sequence-reset script — resets `QARCH_TRAN_SEQ.LAST_NO` for `TRANS_GRP_SEQ_NO` to the max across all transfer/maintenance/history tables (live + DVD). Wrap in `BEGIN TRAN` / verify / `COMMIT`:
```sql
UPDATE QARCH_TRAN_SEQ
SET LAST_NO = (SELECT MAX(TRANS_GRP_SEQ_NO) FROM (
        SELECT MAX(TRANS_GRP_SEQ_NO) TRANS_GRP_SEQ_NO FROM DONL_INT_FUNDS_XFER_HDR
  UNION ALL SELECT MAX(TRANS_GRP_SEQ_NO) FROM DONL_DVD_INT_FUNDS_XFER_HDR
  UNION ALL SELECT MAX(TRANS_GRP_SEQ_NO) FROM DONL_OWNR_EXCPT_MAINT_HDR
  UNION ALL SELECT MAX(TRANS_GRP_SEQ_NO) FROM DONL_DVD_OWNR_EXCPT_MAINT_HDR
  UNION ALL SELECT MAX(TRANS_GRP_SEQ_NO) FROM DONL_PAY_CD_MAINT_HDR
  UNION ALL SELECT MAX(TRANS_GRP_SEQ_NO) FROM DONL_DVD_PAY_CD_MAINT_HDR
  UNION ALL SELECT MAX(TRANS_GRP_SEQ_NO) FROM DONL_DVD_DO_HIST
  UNION ALL SELECT MAX(TRANS_GRP_SEQ_NO) FROM DONL_DO_HIST) A)
WHERE SEQ_NM = 'TRANS_GRP_SEQ_NO';
```

## Verification
- `SELECT LAST_NO FROM QARCH_TRAN_SEQ WHERE SEQ_NM = 'TRANS_GRP_SEQ_NO'` returns a value >= the max TRANS_GRP_SEQ_NO across the tables above.
- A new MEG change / transfer saves without the primary-key error.

## Workaround
None — new transactions will keep colliding until the sequence is reset. Add this script to the standard **post-refresh** script set so it survives the next environment refresh.

## Source
SKILL_QDO_Transfers_SuspendRelease.md §6 and §15-F. Case: 25-00997687.
