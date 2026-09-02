# Fix: SETTLEDAY step fails with ORA-00001 on UNIQUE_ETRAN_GAS_PRICE_DAILY (Measurement to GEN PTR)

## Steps
1. Get the **PQID + failing step name + exact ORA/COM error** — double-click the error row in Batch Messages to read the log.
2. Confirm daily logic is on (`ENT_DAILY_VOL_LOGIC_CHANGE_DT` in the client config/parameter table) and that you are **not re-running a month before the cutoff** — a defect let daily settlement values be generated for pre-cutoff months, colliding on the daily-price unique key; the code fix (24-00940258) prevents daily values for months prior to the cutoff date. Confirm that patch is deployed.
3. Dedupe `ETRAN_GAS_PRICE_DAILY` for the production month:
```sql
SELECT GAS_DAY, MTR_NO, PRICE_TYPE, COUNT(*) dup_ct
FROM   ESUITE_QENT.ETRAN_GAS_PRICE_DAILY
WHERE  PROD_MTH = '{prod_mth}'
GROUP BY GAS_DAY, MTR_NO, PRICE_TYPE
HAVING COUNT(*) > 1;
```
Engineering held the data script for the historical occurrences (SRA, ORL, MEN) — request it via Script Deployment; wrap any clean-up in a transaction with a verify-SELECT.
4. Ensure **`ETRAN_GAS_PRICE_DAILY` is in the rec-purge table list for the Settle Day process** so the prior run's daily prices are purged before re-insert — the repeatable operational fix (24-00942763).
5. If rate schedules using **RPCTR / RPMTR** formulas are involved, apply the config change to use the values as **index adjustments** (24-00940256, ORL).
6. Re-run scoped to the specific **plant + production month + accounting date**.

## Verification
- The dedupe query returns 0 rows for the production month; the SETTLEDAY step of Measurement-to-GEN-PTR completes and PTR is generated for the plant.

## Workaround
None beyond the dedupe + purge-list addition — that combination is the operational fix.

## Source
SKILL_TIPS_Settlement_Revenue_Journal.md §4, §15-A/B. Cases 24-00942763, 24-00940256, 24-00940258.
