# Fix: Re-add the CAW (TIPSCAWDataHelper) DB connection dropped by an environment refresh

## Steps
1. Open Connection Management and check for the CAW / TIPSCAW connection (TIPSCAWDataHelper). If missing or invalid, add it manually with the environment's CAW DB connection details (verbatim disposition from 24-00947753: "added the CAW connection manually to the connection management").
2. Review the environment's post-refresh script (`*.TIPS.Database/PostRefreshScripts/*_TIPS_QFC_PostRefresh.sql` for the client): if it lacks the CAW connection block, that omission is the defect - add the TIPSCAWDataHelper connection block so refreshes stop wiping it (the ADO #1655053 pattern).
3. If the CAW server moved / data-center change and it still cannot connect, suspect firewall rules blocking the web server from the MT and QPEC servers (22-00513042) - route to Cloud Ops.

## Verification
CAW screens/steps no longer throw "DB reference" / "CAW Error in UAT" errors; external CAW functionality works. After the next refresh, the connection survives (post-refresh script carries the block).

## Workaround
Manually re-adding the connection in Connection Management after every refresh works until the post-refresh script is fixed.

## Source
SKILL_TIPS_CAW.md §4 / §15; SF cases 24-00947753, 24-00950735, 22-00513042; ADO #1655053.
