# QCFS Coverage Plan — Gap Survey (ALL history)

**Product:** QCFS — `Product_list__c = 'My Quorum Financial Accounting'`
**Survey date:** 2026-09-02 | **Method:** SOQL aggregates + subject sampling (LIMIT 25 pages) + skill-scope diff + ADO spot checks. No case bodies read beyond subjects.
**Total cases (all history):** 7,120 (sum of category aggregate; CLAUDE.md previously recorded 7,118 — two singleton categories added since).
**Actionable pool (Software Defect + Application Configuration):** 1,162 (SD 509 + AC 653). Add ChangeConfig 46 → ~1,208 if using the skills' wider definition.

**Verdict: QCFS is a WELL-COVERED product.** The 9 existing skills (6 SF-mined + 3 ADO-mined) blanket every category ≥ 21 actionable cases. No full-GAP group found. Two **partial gaps** flagged: (a) state/federal AP **tax-withholding calculation** recipes, (b) **QPEC engine/scheduler ops** (restarts, stuck engines) — both are sub-clusters, not new skills-sized holes; fold into existing skills on next revision.

---

## 1. Aggregate: cases by Case_Category__c

| Case_Category__c | Cases | % |
|---|---|---|
| Accounts Payable (AP) | 2,676 | 37.6% |
| General Ledger (GL) | 925 | 13.0% |
| Security | 459 | 6.4% |
| eSuite | 457 | 6.4% |
| Accounts Receivable (AR) | 355 | 5.0% |
| Integration | 347 | 4.9% |
| Import/Export | 289 | 4.1% |
| All | 285 | 4.0% |
| Master Data | 223 | 3.1% |
| QQM | 190 | 2.7% |
| Workflow | 183 | 2.6% |
| (null) | 168 | 2.4% |
| Ad Hoc Reporting | 139 | 2.0% |
| Other | 138 | 1.9% |
| Bank Recon (BR) | 121 | 1.7% |
| Import / Export (legacy spelling) | 105 | 1.5% |
| Data Hub | 58 | 0.8% |
| AFE / Check Write | 2 | 0.0% |

## 2. Aggregate: cases by Root_Cause__c (top)

| Root_Cause__c | Cases |
|---|---|
| (null) | 1,537 |
| Training | 702 |
| **Application Configuration** | **653** |
| **Software Defect** | **509** |
| Customer Error | 475 |
| Customer Cancelled | 382 |
| Business Change | 353 |
| User Administration Request | 319 |
| Performance | 254 |
| Other | 248 |
| Hardware/Software Env Change | 238 |
| Hardware/Software Change | 232 |
| No Action Taken | 188 |
| Platform | 177 |
| Cloud Outage | 164 |
| Not in Product Plan | 118 |
| ChangeConfig | 46 |
| (29 more values, ≤ 80 each) | — |

## 3. Actionable (SD + AC) by category

| Case_Category__c | SD+AC | Share of 1,162 |
|---|---|---|
| Accounts Payable (AP) | 475 | 40.9% |
| eSuite | 141 | 12.1% |
| General Ledger (GL) | 131 | 11.3% |
| Import/Export (both spellings) | 78 | 6.7% |
| Integration | 60 | 5.2% |
| Accounts Receivable (AR) | 58 | 5.0% |
| Security | 54 | 4.6% |
| Master Data | 46 | 4.0% |
| QQM | 27 | 2.3% |
| Workflow | 26 | 2.2% |
| Bank Recon (BR) | 22 | 1.9% |
| Ad Hoc Reporting | 21 | 1.8% |
| (null) | 15 | 1.3% |
| Data Hub | 7 | 0.6% |
| All | 1 | 0.1% |

AP-specific root-cause split (largest category): null 528, Training 268, SD 266, Customer Error 221, AC 209, Customer Cancelled 171, Business Change 168, HW/SW Change 119, Performance 98.

---

## 4. Proposed groups (10 groups ≈ 98% of actionable)

Estimates from subject-page clustering (4 AP pages, 2 GL pages, 1 page each: eSuite, Security, Integration, Import/Export, AR, BR, MasterData+Workflow, QQM+AdHoc, null-category).

| # | Group | Categories drawn | Est. cases | Actionable | Covered by |
|---|---|---|---|---|---|
| 1 | AP voucher entry / approval workflow / posting | AP, Workflow | ~1,300 | ~240 | SKILL_QCFS_Accounts_Payable.md + SKILL_ADO_QCFS_Accounts_Payable.md (clusters A–D, J) |
| 2 | AP payments: check run / ACH / positive pay | AP | ~600 | ~105 | SKILL_QCFS_Accounts_Payable.md + SKILL_ADO_QCFS_Accounts_Payable.md (clusters E, F) |
| 3 | Vendor/BA master + 1099 + withholding | AP, Master Data, eSuite | ~500 | ~90 | SKILL_QCFS_Platform_Security.md (BA005/PUBBA) + SKILL_QCFS_Accounts_Payable.md (clusters G, H). **PARTIAL GAP: state/federal withholding calc recipes** |
| 4 | GL journal entries / balances / fiscal close | GL, (null) | ~800 | ~140 | SKILL_QCFS_General_Ledger.md + SKILL_ADO_QCFS_AR_GL_BankRecon.md |
| 5 | AR deposits / netting + Bank Recon | AR, BR | ~476 | ~80 | SKILL_QCFS_AR_BankRecon.md + SKILL_ADO_QCFS_AR_GL_BankRecon.md |
| 6 | Import/Export & cross-product interfaces | Integration, Import/Export, Data Hub, AP | ~800 | ~175 | SKILL_QCFS_Import_Export_Integration.md |
| 7 | Platform access & security (login/roles) | Security, eSuite | ~700 | ~110 | SKILL_QCFS_Platform_Security.md |
| 8 | eSuite/V2UI web framework, environment & QPEC infra | eSuite, All, (null) | ~500 | ~90 | SKILL_ADO_SHARED_eSuite_V2UI_Workflow_Performance.md + SKILL_QCFS_Platform_Security.md. **PARTIAL GAP: QPEC engine/scheduler ops runbook** |
| 9 | QQM & Ad Hoc / SSRS reporting | QQM, Ad Hoc Reporting | ~329 | ~48 | SKILL_QCFS_Platform_Security.md (QQM) + SKILL_QCFS_MasterData_Workflow_Reporting.md (SSRS/canned) |
| 10 | Master data & workflow config setup | Master Data, Workflow | ~406 | ~65 | SKILL_QCFS_MasterData_Workflow_Reporting.md |

Groups 1–10 actionable sum ≈ 1,143 of 1,162 (98%). Residual: Other/misc one-offs.

### Per-group distinctive keywords (KB router seeds)

1. **AP voucher/workflow/posting:** AP055, AP056, voucher, batch voucher, Post Pending, Could Not Post, POSTWKFL, approval inbox, reject, resubmit, reversal, reclass, WFID, multiple WFIDs, Approved Final, stuck in WIP, duplicate voucher, route
2. **AP payments:** AP061, check run, check print, ACH, NACHA, remit advice, remittance email, AP150, positive pay, void, reissue, wire payment, single pay, off-system ACH, EFT, cleared date
3. **Vendor/BA/1099/withholding:** BA005, BA030, vendor setup, Business Associate, Tax ID, vendor suffix, zip code, state code, 1099, NEC, INT1099EXP, AP170, withholding, PA withholding, federal WH, inactive vendor, pay term
4. **GL/JE/close:** GL025, BJE, MJE, journal entry, JE definition, GL013, GL014, GL095, GL096, GL092, GL232, SM006, fiscal year, balance refresh, out of balance, trial balance, income statement, retained earnings, accrual reversal, intercompany, LSEALLOC, JBPREPROOF
5. **AR/BankRecon:** AR308, deposit, deposit with match, AR173, AR076, AR086, AR090, JIB netting, pre-check write, PCW, cash call, BR005, BR036, bank recon, reconciled, outstanding checks, CW005
6. **Import/Export/Integration:** QCFSIMPCYC, ADPUPLOAD, ADP import, OpenInvoice, QSTAGXLSIM, QSAGXLSIMP, MT100, QRANET, QRAREV, QRA export, QLS import, QCA import, EnergyLink, JIBLINK, Corcentric, CONCUR, SFTP, FTP, drop folder, HFMACCTBAL, APDYNEXP, stage, import cycle
7. **Access/security:** password expired, QCloud, Citrix, storefront, Okta, OpenID, login, integrated security, security role, persona, SOD, user group, MFA, secure gateway, maintenance app access
8. **eSuite/V2UI/environment/QPEC:** frowny, exception, unhandled, Kendo, timeout, attachment, image, cannot save, patch, hotfix, build, graceful restart, QPEC, middle tier, engine, scheduler, lock not releasing, QEMAIL, QRPTLAUNCH, high resource
9. **QQM/reporting:** QQM, universe, public folder, favorites, row limit, RPT_, ARR003, ARR005, APR004, SSRS, BRPTEMAIL, financial statement report, cash sheet, report timeout
10. **Master data/workflow config:** SM006, business unit, company, fiscal period, cost center, AFE, code table, autonumber, schedule definition, WF005, QP045, workflow lock, AFE_Import lock, PUBORGCC, consolidated BU

---

## 5. ADO notes (verified 2026-09-02)

**Org:** QuorumSoftware. **Projects:** `QuorumSoftware` (bulk of QCFS bugs) and `Quorum` (some 2026+ bugs, e.g. 1831243).

Real QCFS bugs located via `search_workitem`:

| WI | Title (abbrev) | AreaPath |
|---|---|---|
| 1709012 | APH 25-00998985 Batch stuck in POST PENDING | `QuorumSoftware\Engineering\Financials\Committed Backlog\Performance` |
| 1708039 | POSTWKFL failing to post check run (ID bulk insert) | `QuorumSoftware\Engineering\Financials\Committed Backlog\Performance` |
| 1720446 | AP055 Copy Voucher alpha-BU SQL error | `QuorumSoftware\Engineering\Financials\Committed Backlog\Performance` |
| 1739552 | POSTWKFL Account Balance deadlock prevention | `QuorumSoftware\Engineering\Financials\Committed Backlog` |
| 1752121 | Rev batch stuck post pending via QCFSIMPCYC (inactive BU) | `QuorumSoftware\Engineering\Financials\Committed Backlog` |
| 1766274 | CNR POSTWKFL fails setting ID = -1 | `QuorumSoftware\Engineering\Maintenance\Upstream\Professional Services\Financials` |
| 1831243 | RRC state tax WH lines deleted on Validate/Approve (project **Quorum**) | (project Quorum — withholding gap evidence) |

**AreaPath patterns:** `QuorumSoftware\Engineering\Financials\Committed Backlog[\Performance]` (product dev) and `QuorumSoftware\Engineering\Maintenance\Upstream\Professional Services\Financials` (client-maintenance escalations).
**Repo patterns:** `Quorum.Upstream.QCFS.Web` (web/PRs, e.g. PR 105429), `Quorum.QCFS.BL` (`CustomCodeBlockData.cs`, `VoucherBatchBuilder.cs`), classic namespace `Quorum.QCFS.AP` (`QFrmBatchVoucherMaster.cs`), framework `Quorum.QFC.*` (Data/DataProvider), release notes repo `Quorum.Upstream.QCFS.ReleaseNotes`.
**Key tables in repro text:** BATCHVOUCHERMASTER, BATCHVOUCHERDETAIL, BATCHVOUCHERGLDISTRIBUTION, BUSINESSENTITYPERIOD, QXREF_AP_DOC, QARCH_LOCK_MASTER_PROCESS; columns DATEACCT, IDBATCHMASTER, IDWFINSTANCE, IDLINETYPE.

---

## 6. Actions

1. **No new skill needed.** All 10 groups map to existing skills.
2. Next `SKILL_QCFS_Accounts_Payable.md` revision: add a **state/federal tax withholding** cluster (PA withholding, Federal WH, auto-created WH lines deleted on Validate/Approve — Bug 1831243, project Quorum).
3. Next `SKILL_ADO_SHARED_eSuite_V2UI_Workflow_Performance.md` or `SKILL_QCFS_Import_Export_Integration.md` revision: add a short **QPEC engine/scheduler ops** runbook (engines down/crash-loop, "need QPECs restarted", graceful restart, locks not releasing on failed scheduled jobs).
4. Note for intake: category values have legacy duplicates (`Import/Export` vs `Import / Export`); ~168 null-category + 285 "All" cases route by vocabulary, mostly to groups 1, 4, 6.

*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
