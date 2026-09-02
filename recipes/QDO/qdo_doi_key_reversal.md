# Fix: Reverse/reclass fails "Invalid DOI Key Combination" — complete the historical DOI key or reclass via GL025

## Steps
1. Confirm the by-design pattern: the **original voucher posted fine** (historically, with a NULL TIER / incomplete DOI key), and only the **reversal/copy** now fails — the client has since tightened account code-block / JIB-group setup so a complete DOI key (TIER included) is required for anything moving to JIB.
2. Choose one of the field-proven paths:
   - **Script the old posted batches to complete the DOI key** so the key is fully populated on reclasses (verify-SELECT in a transaction first).
   - **Use GL025 to reclass** instead of reversing the AP voucher.
   - **Manually build the reclass**: copy the original batch, double the lines reversing the sign on the originals, fix the Tier coding, reclass on the new lines.
   - As a last resort, temporarily revert the code-block rules, repost as-was, then restore the rules.

## Verification
- The reversal/reclass posts without the "Invalid DOI Key Combination" / "Must approve DOI before booking" messages.
- The historical batch rows now carry a complete DOI key (PROP_NO + DO_TYPE_CD + DO_MAJ_PROD_CD + TIER + OPER_BUS_SEG_CD).

## Workaround
Reclass via GL025 requires no data script and unblocks the accounting immediately; the DOI-key completion script is the durable cleanup for all remaining historical vouchers.

## Source
SKILL_ADO_QDO_DivisionOrder_Transfers.md §4 A1. ADO: 1609157 (Closed/Rejected — By-Design; dev comments by Ben Weis, workaround per Zeb / Nitin Shingi). SF case: 22-00854618.
