# PRODUCT — QDO (Division Order)

| | |
|---|---|
| **Code** | QDO |
| **Salesforce `Product_list__c`** | `My Quorum Division Order` |
| **Domain** | Upstream division orders: ownership decks, transfers, suspend/release, platform integration (eSuite) |
| **Knowledge status** | PARTIAL — 4 skills (3 SF-mined: Division_Orders ~333 cases, Transfers_SuspendRelease ~99, Platform_Integration ~77; 1 ADO defect skill). Grow via `docs/ONBOARD_NEW_PRODUCT.md` Phase 2–5. |

## Vocabulary table (grow as cases arrive)

| Kind | Terms |
|---|---|
| Batch/process codes | POSTWKFL (segregated post-after-workflow, ~5-min drain, monitored in QP045), upstream QPEC seg-processes |
| Concepts | division orders, ownership decks, transfers, suspend/release, DOI |
| Platform | eSuite/V2UI (shared upstream platform — see SKILL_ADO_SHARED_eSuite_V2UI in Upstream ADO Assistant), Quorum.QDOD.Application.QPEC |

## Routing rules

- Router: upstream router copied at `knowledge/UPSTREAM_Issue_Knowledge_Base.md` (covers QRA/QCA/QDO/QCFS — use the QDO rows); defects: `knowledge/UPSTREAM_ADO_Defect_Index.md`.
- Repos: `knowledge/code_logic/REPO_REFERENCE_UPSTREAM.md`; ADO Area Path: `QuorumSoftware\Engineering\Financials`; no product field on ADO bugs — cluster by title keywords.
- Caveats from the ADO mining: fixed-in-build numbers are INFERRED (build field empty); JIB allocation defects live in QCA repos; port-back trap (fix in develop ≠ client's service branch).
- Batch triage: PQID → first ERROR → SQLID/ORA code.
