# Fix: Override Revenue Flag screen error / ORA-01013 / hang — restart + timeout + stats

## Steps
1. **While it is failing**, capture **TIPS ClassicGUI / QTRACE logs** — the screen is C++ (ClassicGUI) and does not touch the Middle Tier, so MT logs are useless and Engineering could not root-cause from standard logs (24-00952270 RCA).
2. **Restart the app services** — this cleared the error with no code change (24-00951708, 22-00627530).
3. Bump the **ClassicGUI query timeout from 30s to 60s** in the client's ClassicGUI ini (the screen query took ~36s against stale stats, over the 30s default — ADO #1665332).
4. Recalculate optimizer statistics on the emptied transaction tables (`QTRAN_PAYSTATION`, `QTRAN_ALLOC_VOL`) — the root cause is nightly stats gathered while the tables sit empty after posting.
5. Long-term: add a **stats-recalc step after ALLOCATE** (mirroring the CALC_STATS step added to JOURNALIMB, ADO #1598509).

## Verification
- The Override Revenue Flag screen queries return within the timeout without ORA-01013/disconnects across a full posting cycle.

## Workaround
Retry after a while — the issue often self-heals once statistics refresh against real data; the restart accelerates that.

## Source
SKILL_TIPS_Settlement_Revenue_Journal.md §11; SKILL_ADO_TIPS_Settlement_Revenue_Statements_Reporting.md §7. Cases 24-00951708, 24-00952270, 22-00627530; ADO #1658025, #1665332.
