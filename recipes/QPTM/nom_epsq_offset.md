# Fix: EPSQ only firing in ID3 / EPSQ=0 — set PACTRL_CYCLE.GAS_FLOW_START_TIME_OFFSET

EPSQ (scheduled quantity for operator) is gated by the cycle's gas-flow-start timing. When `GAS_FLOW_START_TIME_OFFSET` on `PACTRL_CYCLE` is NULL for the earlier cycles, the engine has no flow-start anchor for ID1/ID2, so EPSQ only applies in ID3 or returns 0.

## Steps
1. Verify the current offsets first and confirm a NULL/zero offset is actually the cause:
```sql
SELECT CYCLE_ID, GAS_FLOW_START_TIME_OFFSET
FROM PACTRL_CYCLE
WHERE TSP_NO = {tsp}
ORDER BY CYCLE_ID;
```
2. Confirm the correct CYCLE_ID → cycle mapping for the TSP before applying (cycle IDs are TSP-specific).
3. Apply the fix script (verbatim from case 26-01088719; the example values are that client's seconds-offsets — 43200 = 12h for ID2/cycle 4; 28800 = 8h for ID1/cycle 3):
```sql
-- Source (verbatim, case 26-01088719): set the cycle gas-flow-start offset so EPSQ evaluates.
UPDATE PACTRL_CYCLE
SET GAS_FLOW_START_TIME_OFFSET = '<OFFSET_SECONDS>'   -- e.g. 43200
WHERE CYCLE_ID = '<CYCLE_ID>';                         -- e.g. 4

UPDATE PACTRL_CYCLE
SET GAS_FLOW_START_TIME_OFFSET = '<OFFSET_SECONDS_2>'  -- e.g. 28800
WHERE CYCLE_ID = '<CYCLE_ID_2>';                        -- e.g. 3
```
4. Scope the UPDATE to the client's TSP_NO if the DB hosts multiple TSPs.

## Verification
```sql
SELECT CYCLE_ID, GAS_FLOW_START_TIME_OFFSET
FROM PACTRL_CYCLE
WHERE TSP_NO = {tsp}
ORDER BY CYCLE_ID;
-- Non-NULL offsets on ID1/ID2 rows.
```
Then have the operator retrieve EPSQ/Confirmation Response for an ID1/ID2 cycle gas day — EPSQ now evaluates (non-zero where flow has elapsed) instead of only in ID3.

## Workaround
Until the offsets are set, the operator can work EPSQ in ID3 only (the one cycle where it evaluates), or apply manual EPSQ overrides on the affected locations for earlier cycles.

## Source
SKILL_Confirmations_Scheduling.md §8 (verbatim fix script from case 26-01088719; same pattern resolved 24-00982666 "Updated Gas Flow Start time (PACTRL_CYCLES) for ID1 and ID2").
