# Fix: DO006 "NRI decimal sum of X.XX" blocks DOI Calculate/Approve — delete the stray future-dated owner line

## Steps
1. Confirm the DOGWICALC failure text (e.g. *"12/31/9999 has an NRI decimal sum of 1.75"*) while the on-screen NRI total shows 1.00 — the tell-tale of a hidden owner line.
2. **Clear the inquiry date on DO006** so ALL interest lines are revealed, including any line with a typo far-future effective date (field example: 7/1/2027 entered instead of 7/1/2017 — visible only with a far-future inquiry date).
3. **Delete the bad future-dated owner line.**
4. **Recalculate** the DOI (DOGWICALC), then approve.
5. To spot the overlapping window in SQL, sum NRI per effective window:
```sql
SELECT EFF_DT_FROM, EFF_DT_TO, SUM(NRI_DEC) NRI_SUM
FROM   DONL_DO_DETAIL
WHERE  PROP_NO = '<PROP>' AND DO_TYPE_CD = '<TYPE>' AND TIER = <TIER>
GROUP  BY EFF_DT_FROM, EFF_DT_TO ORDER BY EFF_DT_FROM;
```

## Verification
- DOGWICALC completes and the NRI sum per effective window equals the expected total (1.00).
- The DOI can be approved on DO006.

## Workaround
None needed — this is a setup/data correction the user can perform on-screen; it is not an engine bug, so do not escalate to engineering.

## Source
SKILL_ADO_QDO_DivisionOrder_Transfers.md §6 C1. ADO: 364709 (Closed, iteration 21.04 — setup, not a code fix).
