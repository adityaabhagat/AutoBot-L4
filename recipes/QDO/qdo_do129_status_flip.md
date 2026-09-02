# Fix: DO129 funds release stuck at 3-Approved — flip status to 6-Completed

## Steps
1. Get the **TRANS_SEQ_NO** (and PQID) of the stuck transfer from DO129 for {client}.
2. Verify-SELECT inside a transaction, then run the status-flip script:
```sql
BEGIN TRAN;
SELECT TRANS_SEQ_NO, XFER_STAT_CD, OPER_BUS_SEG_CD, UPDT_DT
FROM   DONL_INT_FUNDS_XFER_HDR
WHERE  XFER_STAT_CD = '3' AND TRANS_SEQ_NO IN ('<seq>');

UPDATE DONL_INT_FUNDS_XFER_HDR
SET    XFER_STAT_CD = '6'
WHERE  XFER_STAT_CD = '3' AND TRANS_SEQ_NO IN ('<seq>');
COMMIT;
```
3. Optionally confirm the duplicate kickoff in the process queue (two PQIDs seconds apart):
```sql
SELECT PQID, STATUS_CD, START_DT FROM QARCH_QUEU_PROCESS WHERE PQID IN (<pqid1>, <pqid2>);
```

## Verification
- Re-query DO129: the release shows **6 - Completed** and the tied owners can be acted on again.
- Confirm the funds moved only **once** (first approval completed; the duplicate was cancelled) — no double payment.

## Workaround
The record being stuck does not affect the money — the funds already moved correctly on the first approval. The durable fix is the upgrade to Web DO ("does not happen in web/future versions"); until then, run the status-flip script whenever a release sticks at 3-Approved.

## Source
SKILL_QDO_Transfers_SuspendRelease.md §4. Cases: 24-00950107, 25-01041288 (seq 115303), 25-01006556 (seq 76470/100960), 25-01049272. ADO: 1668846 (double approve), 1655987/1661187, 1715947 (script review).
