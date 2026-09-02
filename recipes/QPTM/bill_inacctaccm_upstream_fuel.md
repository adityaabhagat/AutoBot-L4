# Fix: Remove the Upstream Fuel step from the INACCTACCM job definition (Auth-to-Post totals inflated)

## Steps
Application Configuration fix (ADO #1729655 "Metadata Changes for INACCTACCM Upstream Fuel Step", Closed).
1. Confirm the symptom: Authorization-to-Post Imbalances **Activity-tab totals miscalculate** (and billing runs slow) after a fuel-related hotfix; the account should accumulate **TSP fuel or nomination fuel, not upstream fuel**.
2. Open the **INACCTACCM (Customer Account Accumulation) job definition** metadata and locate the **Upstream Fuel calculation step** (code `QPSUpstreamFuelCalc.cpp`; client variants `QPDllPipelineMgrIN_CNP`, `_SUI`).
3. **Remove the Upstream Fuel process step** from the job definition (metadata change — no code build).
4. **Re-run INACCTACCM** for the affected accounting months so the account balances rebuild.

## Verification
Re-open Authorization to Post Imbalances and re-check the Activity-tab totals for the affected contracts/months — they must tie to TSP/nomination fuel only; billing runtime returns to normal.

## Workaround
Until the metadata change deploys, tell the customer the Activity-tab total is inflated by an extra fuel component and to rely on the underlying account balance verified by support; do not manually adjust the account to compensate (the re-run will restate it).

## Source
SKILL_Customer_Accounts_Inventory.md §4b; ADO #1729655; SF 24-00966031, 25-01008982, 25-01012810 (Summit).
