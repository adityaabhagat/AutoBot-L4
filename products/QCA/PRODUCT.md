# PRODUCT — QCA (Quorum Cost Accounting)

| | |
|---|---|
| **Code** | QCA |
| **Salesforce `Product_list__c`** | `My Quorum Cost Accounting` (4,235 cases, confirmed via aggregate SOQL 2026-09-02) |
| **Domain** | Upstream cost accounting: AFE lifecycle → joint interest billing (JIB) → fixed assets/inventory → lease operating statements (LOS) → platform/workflow integration |
| **Platform** | eSuite / V2UI (shared upstream platform); QPEC segregated processes |
| **Knowledge status** | GOOD — 8 harvested skills (5 SF-mined + 2 ADO defect + shared eSuite/V2UI) + shared QPEC ops runbook; gap survey complete 2026-09-02 (`knowledge/QCA_Coverage_Plan.md`), router built (`knowledge/QCA_Issue_Knowledge_Base.md`) |

## Vocabulary table (grow via survey + cases)

Seeded from `knowledge/QCA_Coverage_Plan.md` §5 + per-group keywords (§3), survey 2026-09-02.

| Kind | Terms |
|---|---|
| Concepts | AFE (authorization for expenditure), JIB (joint interest billing — JIB allocation defects live in QCA repos even when reported on other products), LOS, fixed assets, DOI-on-cost side; owner allocation, property allocation, cash call / prepay, billing deck, cost center, material transfer, DD&A, AFE supplement, JIB netting, rebill, CTF, WIP-to-NET, overhead rates, approval route / desk / approval limit |
| JIB batch & screens | `JB005` `JB010` `JB020` `JB084` `JB200` `JB300` `JB330` `JB340` `JB350` `JB390` `JB500` `JB520` · `JBREBILL` `JBJOURNAL` `JBLDJE2CAS` `JBPREPROOF` `JBOACHILD` `JBOWNERALLOC` `JBROLLDATE` `PAREBILL` · `JBXRF_KEYWORD_DERIVATION` `JBTRN_CTF` `JBCDE_PREPAY_ACCOUNT` |
| AFE batch & tables | `AFEEXTIMP` `AFE_IMPORT` `AFE_HDRUPL` `AFE_SYNCDOI` `AFERECLASS` `QP053` · `QCTRL_AFE_HDR` `QWF_TRAN_INBOX_AFE` `QXREF_AFE_VALID_POST_STATUS` `XREF_COSTCNTR_ACCTATTRIB` |
| FA / LOS / JEA | `FAGLEXPORT` `FAMTPOST` `FAMTEDIT` `FA010` `FA100` `FA110` `FA150` `FAR012` `BV000` UOP/UOPLWE · `LOSDD_IMP` `LOSLOAD` `LOSEXTCHLD` `LOS002`/`LOS003` `QTRAN_LOS_CUSTOM_SL` `QFACT_LOS` `Sel_PRDN_VOL` · `JEGLEXPORT` `COREIMPJE` `JEA003` `SEXTN_CORE_INTFC_JE` |
| Cross-module / GL-AP-AR (QCFS-owned, see router §3.1) | `GL013` `GL025` `GL095` `GL105` `AP055` `AP061` `AR173` `SM275` `SM093` `QP073` `QP086` `QP110` `MT100` `MF035` · check write, void check, AP voucher, deposit batch, GL batch activity date, GL025 greyed out |
| Interfaces & platform | `STRAN_CORE_INTFC` `JBTRN_OWNER_ALLOC` `QARCH_QUEU_PROCESS` `POSTWKFL` `PSTWKSPLT` `QSTG1099EX` · EnergyLink, JIBLink, OpenInvoice, AFEX, eFast, ADP, SFTP, positive pay, PPDM views · QQM universe, Okta/SSO, persona, security group, Citrix, QCloud |
| Batch | QPEC seg-processes; JIB timeout family: `QPEC.ini`/`QPEC.exe.config` CommandTimeout + COMMAND_TIMEOUT_SECONDS reset after every patch (shared runbook §5) |
| Repos | `Quorum.QCA.{Database, Metadata, Reports, Application.MiddleTier, Application.Web, Application.APIHost, Batch, ClassicBatch}`; shared `Quorum.Upstream.*` / `Quorum.ESuite.*` (watch `Esuite` casing); client-prefixed override repos. ADO Area Paths `QuorumSoftware\Engineering\Financials` and `...\Maintenance\Upstream\{Customer Service\Financials, Professional Services}`; projects `QuorumSoftware` + `Quorum` |
| Client prefixes in ADO titles | EQC/EQT, JNE, SGY, GLE, MEW, APHU, SRC, PNR |

## Routing rules

- **Router: `knowledge/QCA_Issue_Knowledge_Base.md`** (symptom → skill §, coverage map, cross-product routing). Legacy upstream-wide rows: `knowledge/UPSTREAM_Issue_Knowledge_Base.md` + `knowledge/UPSTREAM_ADO_Defect_Index.md`.
- Cross-product: GL/AP/AR core transactions filed under QCA (check write, void check, AP voucher, deposit batch, AR173, GL025) are **QCFS-owned** — router §3.1. QPEC engine/scheduler symptoms → `products/_shared/skills/SKILL_QPEC_Ops_Runbook.md` — router §3.2.
- Repos: `knowledge/code_logic/REPO_REFERENCE_UPSTREAM.md`; client overrides first.
- Caveats: fixed-in builds INFERRED (ADO build field empty); no product field on ADO bugs — cluster by title keywords; port-back trap; client-layer (CEN/QFC) metadata drift is the #1 upgrade cause.
- Batch triage: PQID → first ERROR → SQLID/ORA code.
