# PRODUCT — QCFS (Quorum Financial Accounting)

| | |
|---|---|
| **Code** | QCFS |
| **Salesforce `Product_list__c`** | `My Quorum Financial Accounting` (7,118 cases, confirmed via aggregate SOQL 2026-09-02) |
| **Domain** | Upstream financial accounting: accounts payable → AR/bank reconciliation → general ledger → master data/workflow/reporting → imports/exports & integration → platform security |
| **Platform** | eSuite / V2UI; QPEC segregated processes — incl. **POSTWKFL** (segregated post-after-workflow drainer, ~5-min cycle, `QSegregatedPostWkflBalanceUpdate.cs` in Quorum.Upstream.QCFS.Batch, monitored in QP045) |
| **Knowledge status** | GOOD — 9 harvested skills (6 SF-mined + 2 ADO defect + shared eSuite/V2UI); gap survey pending |

## Vocabulary table (grow via survey + cases)

| Kind | Terms |
|---|---|
| Batch/process codes | POSTWKFL (Post Pending → Posted), GL013 DATAPUBLISH, AP157, QCFSEXPORT (inbound from QRA) |
| Concepts | AP invoice imports (incl. QLS land payments — Cluster C), bank recon, GL post, PUBBA BA-publish (`Quorum.ESuite.Integration.QLS`), Connection Mgmt entries (QLS/QLandDataHelper) |
| Repos | Quorum.Upstream.QCFS.*; ADO Area Path `QuorumSoftware\Engineering\Financials` |

## Routing rules

- Router: `knowledge/UPSTREAM_Issue_Knowledge_Base.md` (QCFS rows) + `knowledge/UPSTREAM_ADO_Defect_Index.md` until a QCFS-specific router is generated.
- Repos: `knowledge/code_logic/REPO_REFERENCE_UPSTREAM.md`; client overrides first.
- Cross-product touchpoints: QLS→AP invoice imports, QRA→QCFS journal export (JE100/JEPOST side lives in QRA skills).
- "Records stuck in Post Pending" = POSTWKFL segregated drainer symptom → batch-debugger SEGREGATED family.
