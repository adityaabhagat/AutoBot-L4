# QCA Coverage Plan — Gap Survey (all Salesforce history)

**Product:** My Quorum Cost Accounting (`Product_list__c = 'My Quorum Cost Accounting'`)
**Survey date:** 2026-09-02 · **Method:** SOQL aggregates + subject sampling (LIMIT 25 pages) + skill-scope cross-check + ADO spot-verification. No case bodies read beyond subjects.

---

## 1. Aggregates

**Total cases (all history): 4,235**

### 1.1 COUNT by Case_Category__c (all root causes)

| Case_Category__c | Cases |
|---|---|
| Joint Interest Billing (JIB) | 1,349 |
| Authorization for Expenditure (AFE) | 1,152 |
| Ad Hoc Reporting | 235 |
| Workflow | 196 |
| eSuite | 194 |
| Security | 190 |
| All | 154 |
| *(null)* | 136 |
| Lease Operating Statement (LOS) | 136 |
| Integration | 114 |
| DD&A (FA) | 112 |
| Inventory (FA) | 79 |
| QQM | 63 |
| Other | 55 |
| Journal Entry Allocations (JEA) | 27 |
| Data Hub | 24 |
| Capital Tracking (CT) | 10 |
| Payout Tracking (POT) | 6 |
| Design Studio | 3 |

### 1.2 COUNT by Root_Cause__c (top rows)

| Root_Cause__c | Cases |
|---|---|
| *(null)* | 1,086 |
| Training | 446 |
| **Application Configuration** | **354** |
| Customer Error | 317 |
| **Software Defect** | **279** |
| Customer Cancelled | 262 |
| Business Change | 200 |
| Other | 177 |
| Hardware/Software Change | 166 |
| User Administration Request | 127 |
| Performance | 120 |
| Hardware/Software Env Change | 102 |
| No Action Taken | 90 |
| Platform | 72 |
| Not in Product Plan | 67 |
| Cloud Outage | 61 |
| Database Refresh Request | 45 |
| Project Debt | 37 |
| Release Collateral (+ Damage) | 65 |
| ChangeConfig | 19 |
| *(29 more small buckets)* | — |

**Actionable pool (Software Defect + Application Configuration) = 633 cases (~15% of all history).**

### 1.3 Actionable COUNT by Case_Category__c (Root_Cause__c IN SD, AC)

| Case_Category__c | Actionable |
|---|---|
| Joint Interest Billing (JIB) | 231 |
| Authorization for Expenditure (AFE) | 163 |
| eSuite | 46 |
| Workflow | 43 |
| Integration | 35 |
| Inventory (FA) | 19 |
| Ad Hoc Reporting | 18 |
| Lease Operating Statement (LOS) | 17 |
| DD&A (FA) | 16 |
| Security | 15 |
| *(null)* | 10 |
| QQM | 9 |
| Journal Entry Allocations (JEA) | 5 |
| Data Hub / Other / Design Studio / CT | 6 |
| **Total** | **633** |

---

## 2. Null-heavy category clustering (subject sampling)

Sampled: `null` (2 pages), `All` (2 pages), `Other` (1 page) — plus actionable-only pages for JIB, AFE, eSuite+Workflow, Integration+QQM+AdHoc, FA+LOS.

- **`null` category (136):** mixes (a) integration plumbing — OpenInvoice/AFEX mapping, stuck invoices, SFTP file checks; (b) **GL/AP/AR core-financial transactions — Void Check, Check Write, AP voucher creation/import, deposit batches, AR173 balances, QP073 loads, GL025 greyed-out commands**; (c) admin/service requests (password resets, purge & archive Q&A, report field asks).
- **`All` (154):** dominated by environment/deployment ops — QPECS restarts, UAT/DEV refreshes, hotfix deployments, "Mewbourne Software Update 16.0.00.053.xx" series, TeamViewer/QCloud/Citrix access, webapps down after v17 upgrade. Low actionable density; mostly service requests.
- **`Other` (55):** same env-ops vocabulary (TeamViewer, QCloud Excel upload, system down) + a thin layer of real module issues (cutback errors, property allocation error, producer revenue not on JIB) that belong to the module groups.

**Distinct new cluster surfaced:** GL/AP/AR core transactions filed under QCA (check write/void, vouchers, deposits, AR balances). Every existing QCA skill defers this to "SKILL_QCA_GL_AP.md (planned)" — this is the one true GAP.

---

## 3. Proposed groups (10 groups cover ~98% of actionable)

| # | Group | SF categories | Est. cases | Actionable | Covered by |
|---|---|---|---|---|---|
| 1 | JIB billing cycle & allocations | Joint Interest Billing (JIB) | 1,349 | 231 | SKILL_QCA_Joint_Interest_Billing.md + SKILL_ADO_QCA_JIB_FixedAssets_LOS.md |
| 2 | AFE lifecycle, import & approval | Authorization for Expenditure (AFE) | 1,152 | 163 | SKILL_QCA_AFE.md + SKILL_ADO_QCA_AFE.md |
| 3 | eSuite / Web UI & screens | eSuite | 194 | 46 | SKILL_QCA_Platform_Workflow_Integration.md + SKILL_ADO_SHARED_eSuite_V2UI_Workflow_Performance.md |
| 4 | Workflow engine (AP/AFE routing, locks, batch post) | Workflow | 196 | 43 | SKILL_QCA_Platform_Workflow_Integration.md + SKILL_ADO_SHARED_eSuite_V2UI_Workflow_Performance.md |
| 5 | Integration & file exchange | Integration, Data Hub | 138 | 37 | SKILL_QCA_Platform_Workflow_Integration.md |
| 6 | Fixed Assets / Inventory / DD&A / MT | Inventory (FA), DD&A (FA), Capital Tracking (CT) | 201 | 36 | SKILL_QCA_FixedAssets_Inventory.md + SKILL_ADO_QCA_JIB_FixedAssets_LOS.md |
| 7 | LOS, Ad-Hoc Reporting & JEA | LOS, Ad Hoc Reporting, JEA | 398 | 40 | SKILL_QCA_LOS_Reporting.md |
| 8 | Security / access / SSO | Security | 190 | 15 | SKILL_QCA_Platform_Workflow_Integration.md (Cluster A) |
| 9 | QQM report plumbing | QQM | 63 | 9 | SKILL_QCA_Platform_Workflow_Integration.md (Cluster H) |
| 10 | **GL/AP/AR core transactions in QCA** (check write, void check, vouchers, deposits, AR balances) | subset of null/All/Other/Workflow | ~60 | ~12 | **GAP** — every skill defers to "SKILL_QCA_GL_AP.md (planned)"; QCFS-side knowledge exists only upstream |
| 11 | Environment & deployment ops (refreshes, QPEC restarts, hotfixes, Citrix/QCloud) | All, null, Other (remainder) | ~290 | ~10 | SKILL_QCA_Platform_Workflow_Integration.md (Clusters F/G) — partial; mostly service requests, low investigation value |

Groups 1–9 alone account for **620 / 633 actionable (98%)**. Group 10 is the only knowledge GAP worth building; group 11 is service-request noise, not worth a skill.

### Per-group distinctive keywords

1. **JIB:** JB005, JB200, JB330, JB340, JB520, JBREBILL, JBJOURNAL, JBLDJE2CAS, JBPREPROOF, PAREBILL, owner allocation, property allocation, prepay/cash call, netting, rebill, CTF, STRAN_CORE_INTFC, JBTRN_OWNER_ALLOC, EnergyLink, JIBLink, "stopped processing on error", GL imbalance/tie-out, overhead rates, INS_PopulateJEStaging
2. **AFE:** AFE stuck in pending, AFEEXTIMP, AFE_IMPORT, AFE_HDRUPL, AFERECLASS, WIP-to-NET, AFE_SYNCDOI, supplement, route/desk, approval limit, QCTRL_AFE_HDR, QWF_TRAN_INBOX_AFE, cost center, JIB tiers unselectable, AFE notification, Execute integration
3. **eSuite/Web:** BA screen save error, zip code error, code tables, Kendo, V2UI, frowny face, web app down, masking, vendor disappearing, special characters, icon naming
4. **Workflow:** POSTWKFL, PSTWKSPLT, WFIP, workflow lock, inbox, batch post, AP055 post pending, QEMAIL, draft/approve/post violation, cancel workflow, voucher back to draft
5. **Integration:** OpenInvoice, ADP, eFast, AFEX, MT100, SFTP, file upload failing, positive pay, QP073 process launcher, staged files, whitelist IP, PPDM views
6. **Fixed Assets:** FAGLEXPORT, FAMTPOST, MT post to subledger, material transfer, DD&A template, UOP/UOPLWE, asset master, FA010, FA100, FA150, stock item, average cost, BV000xxxxx inventory errors
7. **LOS/Reporting/JEA:** LOSDD_IMP, LOSLOAD, LOS002/LOS003, QP086, LOS $0/wrong volumes, JEGLEXPORT, COREIMPJE, GL025, GL095, ODBC error, scheduled job not running
8. **Security:** Okta, SSO, security group, persona, account locked, password reset, screen access, user log on
9. **QQM:** QQM universe, report permissions, cannot create/modify report, QQM daily report
10. **GL/AP/AR core (GAP):** check write, void check, AP voucher creation/approval, voucher import, deposit batch, AR173, GL batch activity date, SM275, QP073 upload, GL025 commands greyed out
11. **Env ops:** UAT refresh, DB refresh, QPEC/QPECS restart, hotfix/patch deployment, software update, TeamViewer, Citrix, QCloud access, environment down

---

## 4. ADO notes (verified on live work items 2026-09-02)

Real QCA bugs located via `search_workitem` with `[System.AreaPath]` pulled via `wit_work_item get_batch`:

| Bug ID | Title (abridged) | System.AreaPath |
|---|---|---|
| 1459297 | EQC - JIB property allocation rebill not processing | `QuorumSoftware\Engineering\Maintenance\Upstream\Professional Services` |
| 1397799 | APHU - myQDO Web - AFE Sync DO failure on JIB DOI XFER | `QuorumSoftware\Engineering\Maintenance\Upstream\Professional Services` |
| 1662007 | JNE - AFE stuck in PEN after final approval | `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Financials` |
| 1718398 | GLE - 25-01008466 - Cancel workflow not sending voucher to draft | `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Financials` |
| 1744335 | SGY - System not creating JE for rebill | `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Financials` |

- Primary bug area paths: `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Financials` (client-escalated, often carries the SF case number in the title) and `...\Upstream\Professional Services`; the ADO-mined skills were built from the broader `QuorumSoftware\Engineering\Financials` tree — keep both in WIQL scope.
- A second ADO project **"Quorum"** now holds `Robot Analysis`-tagged bugs (e.g. 1868261 PAREBILL double-billing, 1813093 AFE desk special characters) — include `project IN (QuorumSoftware, Quorum)` in searches.
- Client prefix convention in bug titles: EQC/EQT, JNE, SGY, GLE, MEW, APHU, SRC, PNR.
- **Repos** (per `knowledge/code_logic/REPO_REFERENCE_UPSTREAM.md`): module tier pattern `Quorum.QCA.{Database, Metadata, Reports, Application.MiddleTier, Application.Web, Application.APIHost, Batch, ClassicBatch}`; shared platform `Quorum.Upstream.*` (Metadata ~4 GB, Reports, Shared.*) and `Quorum.ESuite.*` (watch inconsistent `Esuite` casing); client-prefixed repos hold per-tenant Database/Metadata/Reports overrides. No standalone `Quorum.QCA.API` repo — API surface hosted from `.Application.APIHost`.
- `Microsoft.VSTS.Build.IntegrationBuild` is empty on Financials bugs — infer fixed-in version from IterationPath (e.g. `Product Development\25.19`) + release tags, confirm against PR target branch.

---

## 5. Vocabulary seeds (product detection & KB queries)

`JB005 JB200 JB330 JB340 JB520 JBREBILL JBJOURNAL JBLDJE2CAS JBPREPROOF JBOACHILD PAREBILL POSTWKFL PSTWKSPLT AFEEXTIMP AFE_IMPORT AFE_SYNCDOI AFERECLASS QCTRL_AFE_HDR QWF_TRAN_INBOX_AFE STRAN_CORE_INTFC JBTRN_OWNER_ALLOC QARCH_QUEU_PROCESS FAGLEXPORT FAMTPOST FA010 FA100 FA150 LOSDD_IMP LOSLOAD JEGLEXPORT COREIMPJE GL013 GL025 GL095 GL105 AP055 QP073 QP086 SM093 SM275 AR173 QQM QPEC QPECS QCloud Citrix Okta EnergyLink JIBLink OpenInvoice AFEX eFast MT100 BV000 "owner allocation" "property allocation" "cash call" "billing deck" "cost center" "material transfer" "DD&A" "AFE supplement" "JIB netting"`

---

## 6. Verdict

QCA knowledge coverage is **effectively complete for investigation purposes**: 5 SF-mined skills + 3 ADO-mined skills cover 98% of the historical actionable pool. The only true gap is a small **GL/AP/AR core-transactions** skill (check write / vouchers / deposits / AR balances as filed under QCA) — every existing skill points at it as "planned". Env-ops noise (group 11) should be routed as service requests, not investigated.

*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
