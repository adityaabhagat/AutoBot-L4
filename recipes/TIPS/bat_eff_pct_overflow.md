# Fix: ALLOCATE MONVOL fails on EFF_PCT_CONTR ("negative EFF_PCT_CTR" / "ERROR SETTING VALUE FOR COLUMN EFF_PCT_CONTR")

## Steps
1. Identify the day(s) and meter with a **tiny measured volume against a large scheduled volume** — a displacement PDA absorbs (scheduled − measured), and with measured = 1 vs scheduled = 10,000 the displacement contract's percent-contributed explodes past the `NUMBER(14,10)` column max (verbatim mechanics from 24-00952247).
2. Check the client version against **2023.04**: ADO #1580084 widened `EFF_PCT_CONTR` from `NUMBER(14,10)` to `NUMBER(16,10)` — available 2023.04+, judged **too risky to patch back**. On 2023.04+ this error should not occur from this mechanism.
3. If the client is below 2023.04, apply the data workaround: **raise the measured volume or lower the scheduled volumes** so the displacement quantity shrinks, then rerun ALLOCATE.
4. For a one-off run, setting the batch step to **continue processing on error** unblocks the job but leaves the bad day unallocated (26-01100384) — flag that day for correction.

## Verification
- ALLOCATE (MONVOL step) completes for the plant/production month; the displacement contract's percent-contributed is within column precision.

## Workaround
Adjust the measured/scheduled volumes for the offending day(s) (step 3), or run the step with continue-on-error accepting an unallocated day, until the client is on 2023.04+.

## Source
SKILL_TIPS_Allocations_PPA_Imbalance.md §5. Cases 23-00923463, 23-00923877, 24-00952247, 24-00994961, 26-01100384; ADO #1580084.
