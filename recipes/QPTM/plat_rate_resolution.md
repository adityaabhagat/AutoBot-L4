# Fix: Resolve the Max Tariff rate onto a Capacity Release offer (Rate Resolution batch)

## Steps
1. Confirm the failing offer's detail rows carry a NULL `MAX_TARIFF_RATE` (see Verification query) — that is why the Offer Wizard throws "Value cannot be null" on save/submit.
2. Run the **Rate Resolution batch** separately for TSP {tsp} so it ties the Max Tariff Rate onto the offer (field-proven fix from case 24-00953290: *"Run the Rate Resolution batch separately to tie in Max Tariff Rate, then resubmit"*).
3. Have the user resubmit the offer in the Offer Wizard.

## Verification
```sql
SELECT OFFER_ID, OFFER_DTL_SEQ_NO, MAX_TARIFF_RATE, REL_RATE
FROM   CRCTRL_OFFER_DTL
WHERE  TSP_NO = {tsp}
  AND  MAX_TARIFF_RATE IS NULL;
```
Zero rows for the client's offer after the batch means the rate is resolved; the offer submit should no longer error.

## Workaround
No data is lost while the offer is blocked. The pipeline representative runs the rate-update job on request, after which the offer can simply be submitted again — nothing on the offer needs re-entry.

## Source
SKILL_Capacity_Release.md §4 and §9 — SF cases 24-00953290, 22-00609196, 24-00994097.
