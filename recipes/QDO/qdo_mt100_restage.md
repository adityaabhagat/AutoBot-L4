# Fix: QP043 export not reaching QCFS GL — reload MT100 and restage via QCFSIMPCYC

## Steps
1. Check the **MT100** screen (QCFS Journal/Trans definitions) for {client}: the V16-and-older bug **silently clears the settings when the screen is queried** — treat any blank Journal/Trans definitions as the cleared-config signature.
2. **Reload the MT100 configuration from DEV** (or the last known-good copy) into the affected environment.
3. Find records **orphaned in SEXTN staging** without a Journal/Trans definition, then restage: **delete the orphaned rows from staging and rerun `QCFSIMPCYC`** (re-interface the staging records) after MT100 is fixed.
4. Verify the **COA carries the appropriate JE Code Type** — a missing JE Code Type also stops the export from landing in QCFS GL (23-00915272).
5. Going forward, keep MT100 **Q-managed** so clients do not touch the V16 screen.

## Verification
- Rerun QP043: the export lands in QCFS GL and the QRA-vs-QCFS balances tie out.
- No new orphaned rows in SEXTN staging after the rerun.

## Workaround
None practical at the user level — the export silently succeeds on the QRA side; the fix is the MT100 reload + restage. Keep the period open until the restage completes.

## Source
SKILL_QDO_Division_Orders.md §10. Cases: 24-00950935 / 24-00948961 (MT100 cleared + QCFSIMPCYC restage), 23-00915272 (COA JE Code Type).
