# Fix: Imbalance-trade contract missing from picklist — temporarily extend the contract effective date

## Steps
Field-proven workaround (verified on Trade ID 5553, SF 25-01044171) for the Imbalance Trading picklist defect: the screen only lists **currently active** contracts, but should include any contract active when the imbalance was created (e.g. a storage contract end-dated 8/31 is not selectable for an 08/2025 imbalance traded in 09/2025).
1. Confirm the contract's dates vs the imbalance production month:
```sql
SELECT CTR_NO, TOS_CD, EFF_DT_FROM, EFF_DT_TO, IS_ACTIVE
FROM   NNCTRL_CTR
WHERE  TSP_NO = {tsp} AND CTR_NO = '{contract}';
-- If EFF_DT_TO < the imbalance production month, the contract will not appear in the trade picklist.
```
2. **Temporarily extend the contract's `EFF_DT_TO`** (via Contract Maintenance) past the trade date.
3. **Submit the imbalance trade** — the contract now appears in the picklist.
4. **Revert `EFF_DT_TO`** to the original end date immediately after the trade confirms.

## Verification
The trade shows as submitted/confirmed for the correct contract and production-month imbalance; the contract's `EFF_DT_TO` is back at its original value after the revert.

## Workaround
This recipe IS the customer-usable workaround; the underlying picklist defect (contracts active at imbalance creation should remain selectable) needs a code fix — link the case to engineering if the client wants the permanent behavior.

## Source
SKILL_Customer_Accounts_Inventory.md §6 and §15-D; SF 25-01044171 (proven on Trade ID 5553).
