# Fix: OFR "Plugged TRANS_AMT exceeds tolerance" — set FOOTING_TOLERANCE

## Steps
1. Confirm the rejection reason in `RSTG_OWNR_FUND_RLS_ERR` reads *"Plugged TRANS_AMT exceeds tolerance"*.
2. **Create an environment-specific `FOOTING_TOLERANCE` record in Global Config** for {client} and set it to **1**.
3. **Reprocess `CWOWFNDRLS` (OFR) with the "Process Rejected Records Flag" = Y** so the previously-rejected staging rows are picked up.

## Verification
- The rerun completes without the tolerance rejection; no new rows land in `RSTG_OWNR_FUND_RLS_ERR` for the affected TRANS_SEQ_NO.
- `SELECT COUNT(*) FROM RSTG_OWNR_FUND_RLS WHERE PROC_FL = 'N'` returns 0 for the affected release.

## Workaround
None needed beyond the config — the funds are simply held in staging until the tolerance record exists and the process is rerun with Process Rejected Records checked.

## Source
SKILL_QDO_Transfers_SuspendRelease.md §5. Case: 22-00560533.
