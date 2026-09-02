# PRODUCT — QLS (Quorum Land System)

| | |
|---|---|
| **Code** | QLS |
| **Salesforce `Product_list__c`** | `My Quorum Land` (confirmed via aggregate SOQL 2026-08-14; 14,471 cases carry it) |
| **Domain** | Land management: leases, land payments, obligations, BA/ownership data |
| **Knowledge status** | SCAFFOLD — no dedicated skills yet. Run the onboarding phases. |

## Known integration touchpoints (starting leads, from upstream skills)

- **PUBBA BA-publish** to QLS via assembly `Quorum.ESuite.Integration.QLS` — see Upstream Assistant `SKILL_QCFS_Platform_Security.md` §7.
- **QLS → AP land-payment invoice imports** — `SKILL_QCFS_Accounts_Payable.md` Cluster C.
- **GL013 DATAPUBLISH** needs Connection Mgmt entries `QLS` / `QLandDataHelper` — `SKILL_QCFS_General_Ledger.md`.
- Client repos: `<CLIENT>.QLS.ESuite.Database` (see `knowledge/code_logic/REPO_REFERENCE_UPSTREAM.md`, copied from the QDO/upstream set).

## Vocabulary table

| Kind | Terms |
|---|---|
| (fill during onboarding) | PUBBA, QLandDataHelper, DATAPUBLISH, … |

## Next step

`/onboard-product QLS` → then Phases 1–6 in `docs/ONBOARD_NEW_PRODUCT.md`.
