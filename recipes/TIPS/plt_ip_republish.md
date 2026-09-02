# Fix: Re-publish transient failed events in Integration Platform

## Steps
1. In Integration Platform, filter the failed events for the affected date range and group them by error text.
2. Re-publish the transient classes - they self-heal:
   - "StoreEntity: Insert/Updates were cancelled" (optimistic concurrency)
   - "Concurrency violation: the UpdateCommand affected 0 of the expected 1 records."
   - "Transaction (Process ID n) was deadlocked ... chosen as the deadlock victim."
   - HTTP send errors / TimeoutRejectedException (IP retry usually clears these on the 2nd/3rd attempt).
3. For events that STILL fail after republish, read the payload: a missing xref/contact/meter (e.g. "GetEntity: Resource not found" naming a Contact ID that no longer exists, 25-01056786) is a client data fix, not a republish; "Factory XRefDataHelper does not exist" is the Connection Management config lost in a refresh.
4. Recurring daily deadlocks at scale: escalate as perf/code with event ids and timestamps.

## Verification
The re-published events process successfully in IP (no repeat failure for the same payload) and the downstream TIPS data (meter/volume/BA) lands.

## Workaround
None needed - re-publishing IS the standing routine for these error classes (PML/AZR pattern). Only open a defect if the identical payload keeps failing after republish.

## Source
SKILL_TIPS_Integration_DataSync.md §6 / §14 item 1; SF cases 25-01013486, 26-01100423, 26-01104196, 24-00984118, 25-01056786.
