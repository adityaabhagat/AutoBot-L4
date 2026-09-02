# Fix: Doubled/tripled CAS & EBB volumes — delete duplicate Location Path Maintenance rows and re-run CANOMCLTG

Duplicate rows in Location Path Maintenance (`NNCTRL_LOC_PATH` backing table) make the same path count twice, doubling/tripling flow quantities for the affected segments and locations on CAS Maintenance and the EBB. Field-proven fix from cases 24-00966311 (customer created duplicate rows; script deleted the dupes) and 25-01017371 ("Removed the row in location path maintenance for the pool meter 080038 and north inventory meter 080036").

## Steps
1. Identify the duplicate rows:
```sql
SELECT TSP_NO, LOC_ID, SEG_NO, PATH_ID, FLOW_IND, EFF_DT_FROM, EFF_DT_TO, COUNT(*)
FROM NNCTRL_LOC_PATH
WHERE TSP_NO = {tsp}
GROUP BY TSP_NO, LOC_ID, SEG_NO, PATH_ID, FLOW_IND, EFF_DT_FROM, EFF_DT_TO
HAVING COUNT(*) > 1;   -- >1 = duplicate path rows
```
2. Verify with the client which row is the extra/duplicate (often user-created via the Location Path Maintenance screen) — run a verify-SELECT of the exact rows to be removed and confirm the count.
3. Remove the duplicate row(s): via the Location Path Maintenance screen where possible; otherwise provide a targeted delete script to Cloud Ops (wrap in a transaction, delete only the duplicate keys found in step 1).
4. Re-run **CANOMCLTG** (nom classification) for the affected TSP/gas day so CAS re-reads the corrected paths.
5. Retrieve CAS Maintenance and confirm the values corrected.

## Verification
- Re-run the step-1 duplicate query: 0 rows.
- CAS Maintenance Flow Qty and EBB volumes for the affected segments/locations return to the nominated/confirmed amounts (no longer doubled).

## Workaround
None safe — the doubled numbers persist until the duplicate rows are removed and CANOMCLTG re-runs. If two users retrieving CAS Maintenance simultaneously is suspected instead (no duplicate rows found), that is the separate concurrent-retrieve code defect (24-00973852) — have one user retrieve at a time until patched.

## Source
SKILL_Confirmations_Scheduling.md §4 (verbatim config fixes, cases 24-00966311, 25-01017371, 25-01055876) and §10 (doubled-flow-qty triage). Companion defect: concurrent retrieve 24-00973852 / 23-00927006.
