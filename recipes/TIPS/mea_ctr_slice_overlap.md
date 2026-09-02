# Fix: Contract header time-slice overlap / gap (SEXTN_CTR_HEADER)

## Steps
1. Pull the slice history for the contract (schema/suffix varies by client):
```sql
SELECT CTR_NO, EFF_DT_FROM, EFF_DT_TO, MTR_SFX_CD, UPDT_DT, USER_ID
FROM   QRMTIPS.SEXTN_CTR_HEADER_QRMTIPS
WHERE  CTR_NO = '{contract}'
ORDER BY EFF_DT_FROM DESC;
```
2. **Gap case** (no slice covers the failing month — 26-01100512 pattern): fix the contract end date in **QCM** (the end date is maintained in QCM tied to the **MTR SFX CD**), then in TIPS create the delivery nom to the meter for the new slice (open-ended to 12/31/9000) and re-run to month-end.
3. **Overlap case** (two slices cover the same date range — 25-01002372 pattern, "duplicates inserting into pay station"): raise a Cloud Ops data script to correct/merge the overlapping slice, scoped to the contract and the affected months, with a verify-SELECT before and after.
4. Re-run the failing facility batch job / PPA after the slices are clean.

## Verification
- Re-run the slice query in Step 1: exactly one slice must cover every affected production/accounting month, with no intersecting `EFF_DT_FROM`/`EFF_DT_TO` ranges.
- The facility batch job / PPA that previously failed on the paystation duplicate completes, and the contract allocates for the month.

## Workaround
Until the slice data is corrected there is no processing workaround — the contract will keep skipping the month (gap) or the batch will keep failing on duplicates (overlap). Do not re-run the job repeatedly; correct the contract dates first.

## Source
SKILL_TIPS_Master_Data_Contracts.md §3 and §16-A. SF cases 25-01002372 (IACX, overlap fixed by script), 26-01100512 (Inter Pipeline, QCM end-date gap). Related code defect (false invalid-eff-date on QCM CML, not bad data): ADO #1788087.
