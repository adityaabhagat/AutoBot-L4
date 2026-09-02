# Fix: BLINVGEN PK_BLSTAG_INVOICE_CTR_DT violation — remove the redundant single-day contract time-slice

## Steps
Field-proven in HPE PRD (ADO #1773883 / SF 25-01062471); no code change needed.
1. Identify the contract time-slices around the failure date: look for a **one-day slice** (e.g. 12/17–12/17) added *after* a longer slice (e.g. 12/18–12/31) with identical terms — this is what BILINVPRE chokes on.
2. **Delete the one-day slice in Classic** (the Web screen will not allow the delete on affected builds; the web delete bug is fixed in 2024.04+).
3. **Extend the adjacent longer slice** back to cover the deleted day (e.g. 12/17–12/31).
4. Re-run in order: **allocations → inventory → billing (BLINVGEN)** for the affected accounting month.
5. Do **not** just delete the `BLSTAG_INVOICE_CTR_DT` staging rows — that does not fix it; the bad slice re-creates them.

## Verification
BLINVGEN completes past the BILINVPRE step without `violation of PRIMARY KEY 'PK_BLSTAG_INVOICE_CTR_DT'`; the contract's time-slices show one contiguous slice covering the affected days.

## Workaround
None short of the slice correction — invoice generation is blocked for the invoice group until the redundant slice is removed. If the client cannot access Classic, Cloud Ops performs the slice delete/extend.

## Source
SKILL_ADO_QPTM_Billing_Invoice_Rates.md §4 Cluster A (A2); ADO #1773883; SF 25-01062471 (HPE).
