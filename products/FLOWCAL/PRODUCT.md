# PRODUCT — FLOWCAL (measurement family: FLOWCAL + TESTit + PROVEit)

| | |
|---|---|
| **Code** | FLOWCAL |
| **Salesforce `Product_list__c`** | `FLOWCAL` (44,912 cases) + family: `TESTit` (16,126), `PROVEit` (6,518) — all three confirmed via aggregate SOQL 2026-09-02. Case queries use `Product_list__c IN ('FLOWCAL','TESTit','PROVEit')`. |
| **Domain** | Gas & liquids measurement data management: EFM data collection/validation/editing (FLOWCAL), meter testing (TESTit), meter proving (PROVEit). Upstream feed into TIPS/QPTM measurement imports (WHMEASIMP/FlowCal interfaces). |
| **Knowledge status** | SCAFFOLD → survey + all-history mining in progress (started 2026-09-02) |

## Vocabulary table (filled by the coverage survey + mining)

| Kind | Terms |
|---|---|
| Batch/process codes | (survey) |
| Table prefixes | (survey) |
| Error-code patterns | (survey) |
| Screens/concepts | EFM, CFX files, gas analysis, meter proving, (survey) |

## Routing rules

- Router: `knowledge/FLOWCAL_Issue_Knowledge_Base.md` (created by mining).
- ADO: area path/repos discovered during survey — record here.
- Cross-product note: "FlowCal" symptoms inside QPTM/TIPS cases (import failures) stay with QPTM/TIPS (SKILL_Integration_Processing / SKILL_TIPS_Integration_DataSync); this product covers the FLOWCAL application itself.
