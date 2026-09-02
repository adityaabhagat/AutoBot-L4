# Fix: Journal not generating / wrong for a contract, CCT, or meter (Journal Entry Control config)

## Steps
1. Open **Journal Entry Control** for the affected CCT/meter.
2. Check that a **condition exists** for the meter/CCT at all — a missing condition means no journal is generated (26-01086172, 25-01011403).
3. Check for an **unintended second condition** — a double condition on the journal entry for a meter blocked generation; removing the extra condition fixed it (25-01013216). Duplicate journal entries usually mean duplicate conditions or a cycle run twice.
4. For data split across cost centers/accounts, use **Journal Conditions** to filter, rather than separate setups (25-01011403).
5. If Journal IDs/entries are missing from the **QQM query** screen, check the query field list for an invalid field — removing the bad "Interconnect" field from the selected fields fixed the query (25-01028136).
6. Regenerate the journal for the production month.

## Verification
- The JOURNAL process generates entries for the meter/CCT, once each; the journal query returns the expected IDs.

## Workaround
None needed — this is the fix (configuration). If the client cannot wait for a regeneration window, cost-center/account corrections can be made downstream in the GL per the client's own process.

## Source
SKILL_TIPS_Settlement_Revenue_Journal.md §6. Cases 25-01013216, 25-01011403, 26-01086172, 25-01028136.
