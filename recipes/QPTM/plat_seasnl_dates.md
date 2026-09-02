# Fix: Capacity Release seasonal dates wrong on offer / replacement contract (USE_SEASNL_DATES)

## Steps
1. Confirm the TSP config **`USE_SEASNL_DATES` = 0** (and check `USE_AUTO_POPULATE_SEASNL_DATES`). When it is 0 the seasonal-date columns are hidden on the Offer and Bid screens, so stale values copied by Copy Offer are invisible to the user.
2. Pull the affected offer detail and compare seasonal vs release dates:
```sql
SELECT OFFER_DTL_SEQ_NO, SEASNL_START_DT, SEASNL_END_DT, REL_BEG_DT, REL_END_DT
FROM   CRCTRL_OFFER_DTL
WHERE  TSP_NO = {tsp} AND OFFER_ID = <OFFER_ID>;
```
3. Correct the `CRCTRL_OFFER_DTL` seasonal dates via script for the affected offers so **Seasonal Start/End = Release Start/End**, BEFORE billing runs (field-proven interim from ADO #1702160 RCA: *"confirm USE_SEASNL_DATES=0 ... then correct CRCTRL_OFFER_DTL seasonal dates via script for the affected offers before billing"*).
4. If `RuleCROF000250` is blocking a stuck offer, the rule can be **temporarily deactivated** as an interim unblock (done in case 26-01080121) — but fix the underlying dates/config, then re-activate.
5. Long-term: confirm the client build contains the code failsafe (when `!UseSeasonalDates`, `QUIControllerCROfferV2.cs` forces seasonal = release dates; ADO #1702160/#1773394 — the fix was wiped once by a hotfix, so verify it is present).

## Verification
Re-run the step-2 SELECT: every detail row must show `SEASNL_START_DT = REL_BEG_DT` and `SEASNL_END_DT = REL_END_DT`. The replacement contract generated on award must carry the release date range, and BLINVGEN must complete without date errors.

## Workaround
Until the dates are corrected, do not evaluate/award the affected offer — awarding from stale seasonal dates creates a replacement contract with the wrong term and downstream invoice failures.

## Source
SKILL_Capacity_Release.md §8 (cases 24-00990888, 24-00991839 RCA, 25-01050402, 26-01080121); SKILL_ADO_QPTM_Contracts_RFS_Offer_CapacityRelease.md §5 B1 — ADO #1604135, #1702160, #1773394.
