# Fix: FlowCal REVISION_NUMBER inflation (>1000) breaking the Integration Platform

## Steps
1. Confirm the inflation on the client's measurement/analysis rows (table is client-specific — verify the exact table in the client schema first):
```sql
SELECT MTR_NO, PROD_DT, REVISION_NUMBER
FROM   <measurement/analysis table>
WHERE  REVISION_NUMBER > 1000;
```
2. **Interim (field-proven, recurring operational pattern):** route to **Cloud Ops** to run the reset script that sets `REVISION_NUMBER` values above 1000 back to **1 or 2**, scoped to the affected meters/months, with a verify-SELECT.
3. Re-run the FlowCal→TIPS Integration Platform sync; the error clears once revisions are back in range.
4. **Durable fix:** the inflation comes from FlowCal sending multiple events per change — flag the client's **FlowCal upgrade** as the real fix; until then the reset script needs to be re-run periodically.

## Verification
- The Step 1 query returns zero rows after the reset.
- The Integration Platform FlowCal→TIPS import completes without the revision-number error, and subsequent syncs keep REVISION_NUMBER in normal range (single digits) until FlowCal re-inflates it.

## Workaround
The periodic reset script IS the workaround (standing pattern across 25-01047138, 25-01050084 BMD, 25-01050137 UTG, 25-01014139 — the recurring "Script Deployment for Integration Platform Error" family). Schedule it as a recurring Cloud Ops task until the FlowCal upgrade lands.

## Source
SKILL_TIPS_Measurement_Ticketing.md §12 and §18-E (SF 25-01047138 + the Script Deployment family 25-01050084, 25-01050137, 25-01014139).
