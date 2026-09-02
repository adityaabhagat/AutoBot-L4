# Fix: Fee/fuel/residue missing on statement or invoice — Fixed Fuels UOM mapping

## Steps
1. Open the **CCT → Fixed Fuels tab** for the affected contract.
2. Verify every UOM there maps to a **valid UOM Class Code**. The proven case: the `CTRSHK` UOM was mapped to an invalid UOM Class Code, so field fuel silently did not calculate — Wellhead Net Delivered came out too high and theoretical/settled NGLs too high (23-00876904, 23-00876962). Re-map to a valid class.
3. Check the corresponding **UDEF → UOM mapping** — e.g. the `MONMDQ` UDEF needed a remap to the `CTRMDQ` UOM (23-00878026).
4. Confirm **gas analysis is consistent between environments** — a fee can appear missing in TEST simply because the gas analysis differs from PRD (23-00881064).
5. Rerun Settle (and downstream statement generation) for the plant/production month.

## Verification
- The fee/fuel/residue appears on the statement/invoice; Wellhead Net Delivered and theoretical/settled NGL values return to expected ranges.

## Workaround
None needed — this is configuration; the remap plus rerun is the fix.

## Source
SKILL_TIPS_Settlement_Revenue_Journal.md §10. Cases 23-00876904, 23-00876962, 23-00878026, 23-00881064, 23-00884937.
