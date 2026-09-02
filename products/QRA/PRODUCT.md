# PRODUCT — QRA (Quorum Revenue Accounting)

| | |
|---|---|
| **Code** | QRA (requested as "QRD" — confirmed to mean QRA 2026-09-02) |
| **Salesforce `Product_list__c`** | `My Quorum Revenue Accounting` (8,908 cases, confirmed via aggregate SOQL 2026-09-02) |
| **Domain** | Upstream revenue accounting: ownership/master data → volume allocation → revenue distribution → checks/payouts → journals/GL → tax & regulatory (1099, escheat) |
| **Platform** | eSuite / V2UI (shared upstream platform); QPEC segregated processes |
| **Knowledge status** | GOOD — 12 harvested skills (9 SF-mined + 3 ADO defect, from Upstream Assistant projects); gap survey pending |

## Vocabulary table (grow via survey + cases)

| Kind | Terms |
|---|---|
| Batch/process codes | BKRVNU (segregated engine behind VL100 revenue distribution), POSTWKFL (segregated post-after-workflow, QP045), QPEC seg-processes |
| Screens/concepts | VL100 (revenue distribution), check write, OFR, escheat, prior-period adjustments (PPA = rebill here, ≠ QPTM/TIPS PPA), ownership decks, 1099 |
| Repos | Quorum.Upstream.* ; ADO Area Path `QuorumSoftware\Engineering\Financials` (no product field on bugs — cluster by title keywords) |

## Routing rules

- Router: `knowledge/UPSTREAM_Issue_Knowledge_Base.md` (QRA rows) + `knowledge/UPSTREAM_ADO_Defect_Index.md`.
- Repos: `knowledge/code_logic/REPO_REFERENCE_UPSTREAM.md`; client overrides first.
- Caveats (from ADO mining): fixed-in builds are INFERRED (build field empty); port-back trap (develop ≠ client service branch); JIB allocation defects live in QCA repos.
- Batch triage: PQID → first ERROR → SQLID/ORA code.
