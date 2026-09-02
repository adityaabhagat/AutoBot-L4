# PRODUCT — QCA (Quorum Cost Accounting)

| | |
|---|---|
| **Code** | QCA |
| **Salesforce `Product_list__c`** | `My Quorum Cost Accounting` (4,235 cases, confirmed via aggregate SOQL 2026-09-02) |
| **Domain** | Upstream cost accounting: AFE lifecycle → joint interest billing (JIB) → fixed assets/inventory → lease operating statements (LOS) → platform/workflow integration |
| **Platform** | eSuite / V2UI (shared upstream platform); QPEC segregated processes |
| **Knowledge status** | GOOD — 8 harvested skills (5 SF-mined + 2 ADO defect + shared eSuite/V2UI); gap survey pending |

## Vocabulary table (grow via survey + cases)

| Kind | Terms |
|---|---|
| Concepts | AFE (authorization for expenditure), JIB (joint interest billing — JIB allocation defects live in QCA repos even when reported on other products), LOS, fixed assets, DOI-on-cost side |
| Batch | QPEC seg-processes; JIB timeout family: `QPEC.ini`/`QPEC.exe.config` CommandTimeout + COMMAND_TIMEOUT_SECONDS reset after every patch |
| Repos | Quorum.Upstream.QCA.ClassicBatch / .Database; ADO Area Path `QuorumSoftware\Engineering\Financials` |

## Routing rules

- Router: `knowledge/UPSTREAM_Issue_Knowledge_Base.md` (QCA rows) + `knowledge/UPSTREAM_ADO_Defect_Index.md` until a QCA-specific router is generated.
- Repos: `knowledge/code_logic/REPO_REFERENCE_UPSTREAM.md`; client overrides first.
- Caveats: fixed-in builds INFERRED (ADO build field empty); no product field on ADO bugs — cluster by title keywords; port-back trap.
- Batch triage: PQID → first ERROR → SQLID/ORA code.
