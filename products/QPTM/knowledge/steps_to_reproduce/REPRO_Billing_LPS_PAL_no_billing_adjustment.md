# REPRO — Billing: LPS/PAL PPA generates no billing adjustment (SQL 208 `BLSTAG_PAL_EXT`)

**Source case:** 26-01106039 (EQC/EQT, TSP 24) · predecessor 25-01058356 · ADO Bug #1836277 / WI #1836679
**Skill section:** SKILL_Billing.md §4.4 · **Confidence:** REPRODUCIBLE (L2/L3 reproduced in EQC DEV 2026-07-01; error captured verbatim on Bug #1836277; steps 1–6, 8 EXPLICIT from case/screenshot/bug, step 7 ordering DERIVED from code walkthrough)

## Data-state required (all three, simultaneously)

1. `BLSTAG_PAL_EXT` **absent** from the target DB schema (the defect condition — check `SELECT OBJECT_ID('dbo.BLSTAG_PAL_EXT')` = NULL).
2. Config gates active: `BILLING/USE_DTE_BLRPTS_10_INVOICE_DOC_PAL` = true (⚠️ also true by default when the key is **missing**) **and** TSP config key `INV_DOC_PAL_STMT` = DAY.
3. An LPS-F (park-and-loan) contract with a PPA pending billing in an open/rerunnable invoice cycle (reference data: contract 1269.2278, TSP 24, gas day 5/31/2026, 114 dth, invoice 260675).

No timing dependency — the condition is structural (missing object) and persists until the object is deployed.

## Steps

1. Precondition: instance in the data-state above.
2. Enter a retro nomination change for the gas day (e.g., 114 dth on 5/31/2026) → retro nom error triggers.
3. Reallocation records generate (Reallocation Maintenance).
4. PPA event records trigger (PPA Event Maintenance → `BLTRAN_PPA_EVENT`).
5. Run PANIGHTLY/PAN → PPA status = "processed".
6. Verify Customer Account Main shows the revised balance — lifecycle complete, invoice Adj still 0.
7. Run `CalcPALExtension` (where present), then Invoice Generation **BLINVGEN "Run All PPAs"** for the production month. *(DERIVED ordering)*
8. **Observe:** batch crashes in registered SQL `QSQLID_INS_SEL_INVOICE_DOC_PAL_DAY` — SQL 208 / SQLState 42S02 `Invalid object name 'BLSTAG_PAL_EXT'` → "PAL statement records were not successfully inserted." / "CreateNewData function failed." → no `CHARGE_BASIS_CD='PEX'` row in `BLTRAN_INVOICE_GEN_QTY`, no billing adjustment on the invoice.

## Non-repro control

Insert/create `BLSTAG_PAL_EXT` (even **empty** — join is LEFT OUTER, only `EXT_DAY_COUNT` read) and rerun step 7–8: batch completes, PEX rows appear. This is the WI #1836679 differential proof (EQC DEV flipped repro → non-repro 2026-07-06 with zero code/data change).

*Filed by knowledge-curator, 2026-08-14. Auto-Bot by Aditya Bhagat.*
