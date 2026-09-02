# Fix: LD17/LD18 PPN fails with 302/311 impairment — verify Market Group setup, RUN_RDCALCNEW workaround

## Steps
1. Capture the exact impairment lines: `302 Impairment - remaining amount is not zero` / `311 Impairment - remaining Total Tax Decimal not zero`, plus the DOI key (`PROP/DO_TYPE/MAJ_PROD/TIER/INT_TYPE/SEQ`), production dates, and MG #.
2. **Verify the Market Group and Bearer Group setup first** — this is frequently customer setup, not a defect:
   - A **Tract-level Market Group needs a corresponding Unit-level Market Group** (Unit-to-Tract).
   - Submit **products 204 and 400 together from VL100** when reprocessing (25-01059135 pattern).
3. If the setup is correct and the impairment persists, apply the workaround: **set the `RUN_RDCALCNEW` global config to disabled** (turns off the new RD calc engine).
4. Escalate for RCA with a DB copy if the impairment recurs with correct setup (open a case per 25-01014688).

## Verification
- Rerun the LD17/LD18 PPN process: it completes without 302/311 impairment lines.
- The remaining distribution decimal and remaining tax decimal for the affected DOI/production month net to zero.

## Workaround
For month-close pressure: disable `RUN_RDCALCNEW` (global config) to bypass the new remaining-decimal check while the Market Group setup is corrected, then re-enable after RCA.

## Source
SKILL_QDO_Division_Orders.md §5 B2. Cases: 25-01014688 (RUN_RDCALCNEW WA, related 25-01019939), 25-01059135 (Market Group setup, Customer Error), 25-01045698 (Unit-level market group).
