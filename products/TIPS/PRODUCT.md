# PRODUCT — TIPS (Transaction Information Processing System)

| | |
|---|---|
| **Code** | TIPS |
| **Salesforce `Product_list__c`** | `My Quorum TIPS` (confirmed via aggregate SOQL 2026-08-14; 9,975 cases carry it) |
| **Domain** | Gas & crude measurement → allocation → contracts/rates → inventory/imbalance → statements/settlements → EDI/reporting |
| **Two code lines** | Gas: `Quorum.TIPS.*` · Crude: `Quorum.TIPS.Crude.*` (truck/marine/batch tickets, terminals, crude, water → crude line) |
| **Knowledge status** | FULL — 24 skills (14 SF-mined + 8 ADO defect + modules map + TIPS-tuned SF queries) |

## Vocabulary table

| Kind | Terms |
|---|---|
| Batch/process codes | FBJ chain: MEASUREMENT→ALLOCATE→SETTLE→POSTRESULT, SETTLEMAIN, NOMPOST, CFCREATE, WHMEASIMP, QIMPVOLD, INACCUM, GMASLDVOLS (segregated), GEN PTR, SETTLEMGR, ASSCGLM |
| Table prefixes | QTRAN_* (PAYSTATION, IMBAL_ACCT_BAL, SETTLE_*), CTRMTR, TRNX_ID families |
| Concepts | Settle Day, CCT/CML fees, time-slice effective dating (contract/meter overlaps!), CAW external portal (OKTA, CAWDATA), Exago reports, QCM, IN01/IN02 statements, severance tax, SAP GL journals, Evolution QPTM↔TIPS PTR sync |
| Engine | QPEC batch engine (stuck jobs, TRNX_ID PK violations, purge/archive) |

## Routing rules

- Router: `knowledge/TIPS_Issue_Knowledge_Base.md`; module map: `skills/SKILL_TIPS_Modules.md` (12 modules with repos/tables/common root causes).
- Repos: `knowledge/code_logic/REPO_REFERENCE_TIPS.md` — gas vs crude split; ~80 client 3-letter prefixes (`<CLIENT>.TIPS.*` override FIRST); fix availability via `Quorum.TIPS.ReleaseNotes`.
- Config: `knowledge/config_logic/CONFIG_REFERENCE_TIPS.md` (QPTM & TIPS master key reference — TIPS sections incl. TurboTips ALLOCATE/SETTLEMAIN); three scopes global/company/plant; authoritative in `ps<PROCESS>_ConfigSettingsUsed.cs` (Quorum.Tips.TurboTips) — trust the C# initializer over XML doc-comments.
- Cross-cutting defect families: TRNX_ID exhaustion/duplication, contract/meter time-slice overlaps, Web-vs-Classic parity, post-refresh drift, Evolution sync, patch-delivery noise.
- "PPA" here = allocation restatement (≠ QPTM billing PPA ≠ upstream JIB rebill); statement value bugs typically need fixes in 4 places.
