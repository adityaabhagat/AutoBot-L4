# QRA Coverage Plan — Skill-Group Survey (GAP analysis)

**Product:** QRA · `Product_list__c = 'My Quorum Revenue Accounting'`
**Survey date:** 2026-09-02 · **Method:** SOQL aggregates over ALL history (no date filter) + subject sampling (3 pages x 25, newest first) + ADO area-path spot-check. No case bodies read.
**Totals:** 8,908 cases · **1,412 actionable** (Root_Cause__c = Software Defect 836 + Application Configuration 576) · 8,541 closed (95.9%: Closed 7,728 + Closed-No Response 699 + Closed-Deferred 114).

**Headline finding:** QRA already has 12 skills (9 SF-mined + 3 ADO-mined) and at the *category* level they cover ~98% of actionable volume. This is a **depth/refresh survey**, not a greenfield plan — the only true routing GAP is the 387 uncategorized cases (22 actionable). The thinnest depth spots are **eSuite/owner-portal (60 actionable)** and **Security (40 actionable)**, both bundled inside the Platform catch-all skill.

---

## 1. Aggregates

### 1.1 COUNT by Case_Category__c (all history, 44 values)

| Case_Category__c | Cases | | Case_Category__c | Cases |
|---|---:|---|---|---:|
| Check Write | 1,596 | | System Configuration | 86 |
| Revenue Distribution | 888 | | Wind Royalty | 71 |
| Prior Period Adjustments | 607 | | Business Associates | 71 |
| Journal | 478 | | Volumetric Reporting | 53 |
| All | 461 | | Archive | 42 |
| Master Data | 410 | | Contracts | 42 |
| Tax and Regulatory | 405 | | Volume Allocation | 30 |
| Integration | 391 | | Gas Balancing | 28 |
| *(null)* | 387 | | Estimate | 27 |
| Other | 302 | | Escheat | 27 |
| Ownership | 295 | | Severance Tax Reporting | 27 |
| Acquisitions and Dispositions | 294 | | Production Master Data | 17 |
| Direct Revenue Input | 265 | | Check Interfaces | 17 |
| Security | 262 | | Royalties | 15 |
| eSuite | 255 | | Installation | 14 |
| Check Input | 249 | | 1099 Reporting | 12 |
| Production Allocation | 133 | | System Valued | 6 |
| QQM | 128 | | Coal Royalty | 5 |
| Payouts | 112 | | Design Studio | 4 |
| Platform / UX | 105 | | Estimates / Accruals | 2 |
| Contractual Allocation | 100 | | Division Orders | 2 |
| Journal Entries | 95 | | | |
| Revenue Master Data | 92 | | **Total** | **8,908** |

Category field is well populated (null = 387, 4.3%) — no subject-cluster fallback needed.

### 1.2 COUNT by Root_Cause__c (top rows of 41)

| Root_Cause__c | Cases | | Root_Cause__c | Cases |
|---|---:|---|---|---:|
| *(null)* | 2,318 | | No Action Taken | 216 |
| Customer Error | 1,036 | | Hardware/Software Env Change | 190 |
| **Software Defect** | **836** | | Project Debt | 165 |
| Customer Cancelled | 701 | | Database Refresh Request | 156 |
| **Application Configuration** | **576** | | User Administration Request | 138 |
| Training | 565 | | Cloud Outage | 89 |
| Business Change | 299 | | Upgrade Request | 79 |
| Other | 295 | | Client Managed Infrastructure | 77 |
| Performance | 249 | | Not in Product Plan | 74 |
| Hardware/Software Change | 237 | | Unknown | 70 |
| Platform | 227 | | ChangeConfig | 35 |

Long tail: Release Collateral 41, Data Loader/Update 31, User Error 27, Declined by Customer 24, Release Collateral Damage 21, Deployment Issue 20, Packaging Issue - Metadata 18, Collateral Damage 15, Packaging - DB Scripts 13, others < 12 each. (Note: `ChangeConfig` 35 is arguably actionable too; the existing skills counted it in their evidence bases.)

### 1.3 ACTIONABLE by Case_Category__c (Root_Cause__c IN 'Software Defect','Application Configuration') — 1,412 cases

| Case_Category__c | Actionable | | Case_Category__c | Actionable |
|---|---:|---|---|---:|
| Check Write | 252 | | Payouts | 20 |
| Prior Period Adjustments | 163 | | System Configuration | 19 |
| Revenue Distribution | 154 | | Contractual Allocation | 16 |
| Master Data | 92 | | Production Allocation | 16 |
| Ownership | 79 | | QQM | 12 |
| Tax and Regulatory | 64 | | All | 11 |
| eSuite | 60 | | Other | 11 |
| Journal | 57 | | Severance Tax Reporting | 11 |
| Direct Revenue Input | 46 | | Volumetric Reporting | 9 |
| Integration | 43 | | Escheat / Contracts / Check Interfaces | 6 each |
| Acquisitions and Dispositions | 41 | | Royalties / Volume Allocation | 5 each |
| Security | 40 | | Archive / Gas Balancing | 4 each |
| Check Input | 30 | | 1099 Reporting / Production Master Data | 3 each |
| Revenue Master Data | 27 | | Installation | 2 |
| Business Associates | 24 | | Sys Valued / Wind Royalty / Estimate | 1 each |
| Journal Entries | 24 | | *(null)* | 22 |
| Platform / UX | 22 | | **Total** | **1,412** |

### 1.4 COUNT by Status

| Status | Cases | | Status | Cases |
|---|---:|---|---|---:|
| Closed | 7,728 | | In Review | 46 |
| Closed - No Response | 699 | | In Development Queue | 39 |
| Closed - Deferred | 114 | | Complete - Pending Delivery | 34 |
| Pending Quorum | 65 | | Pending Customer | 30 |
| Complete - Pending Customer Review | 58 | | In Progress | 27 |
| New | 55 | | Development In Progress | 13 |

---

## 2. Skill groups vs. existing coverage (GAP map)

13 groups = 100% of the 1,412 actionable cases. Existing skill files live in `products/QRA/skills/`.

| # | Group | SF categories folded in | Est. cases | Actionable | Covered by |
|---|---|---|---:|---:|---|
| 1 | Check Write / Disbursement / Bank files / Escheat output | Check Write, Check Input, Check Interfaces, Escheat | 1,889 | 294 | `SKILL_QRA_Check_Processing.md` (+ `SKILL_ADO_QRA_CheckWrite_OFR_Escheat.md`) |
| 2 | Prior Period Adjustments / PPN / impairments | Prior Period Adjustments | 607 | 163 | `SKILL_QRA_Prior_Period_Adjustments.md` (+ `SKILL_ADO_QRA_Revenue_Distribution_PPA.md`) |
| 3 | Revenue Distribution / Valuation / DRI / CA | Revenue Distribution, Direct Revenue Input, Contractual Allocation | 1,253 | 216 | `SKILL_QRA_Revenue_Distribution.md` (+ ADO PPA skill) |
| 4 | Ownership / DOI / Master Data / BA | Master Data, Ownership, Revenue Master Data, Business Associates | 868 | 222 | `SKILL_QRA_Ownership_MasterData.md` |
| 5 | Journal / JE / QCFS export | Journal, Journal Entries | 573 | 81 | `SKILL_QRA_Journal.md` |
| 6 | Tax & Regulatory / Severance / 1099 / ONRR | Tax and Regulatory, Severance Tax Reporting, 1099 Reporting | 444 | 78 | `SKILL_QRA_Tax_Regulatory.md` (+ `SKILL_ADO_QRA_Tax_1099_Regulatory.md`) |
| 7 | A&D / Payouts | Acquisitions and Dispositions, Payouts | 406 | 61 | `SKILL_QRA_AcqDisp_Payouts.md` |
| 8 | Volume / Production Allocation / Gas Balancing / Royalty reporting | Production Allocation, Volumetric Reporting, Volume Allocation, Gas Balancing, Production Master Data, Royalties, Wind Royalty, Coal Royalty | 352 | 43 | `SKILL_QRA_Volume_Allocation.md` |
| 9 | eSuite / owner web portal | eSuite | 255 | 60 | `SKILL_QRA_Platform_Integration_Security.md` — **THIN**: 4th-largest actionable bucket bundled in a catch-all; candidate for a dedicated skill |
| 10 | Integration / interfaces / env sync | Integration | 391 | 43 | `SKILL_QRA_Platform_Integration_Security.md` |
| 11 | Security / access / permissions | Security | 262 | 40 | `SKILL_QRA_Platform_Integration_Security.md` — thin (bundled) |
| 12 | Platform / batch infra / QQM / system config / misc | Platform / UX, System Configuration, QQM, Other, All, Installation, Archive, Contracts, Estimate(s), System Valued, Design Studio, Division Orders | 1,221 | 89 | `SKILL_QRA_Platform_Integration_Security.md` |
| 13 | Uncategorized (null Case_Category__c) | *(null)* | 387 | 22 | **GAP** — no skill can claim them by category; route by vocabulary match (subjects sampled show they are mostly PPA/impairment and check-write symptoms mis-filed without a category) |

Cumulative: groups 1–8 alone = 1,158 actionable (82%); adding 9–12 = 1,390 (98.4%); group 13 closes it out.

**Recommended actions (priority order):**
1. **Split group 9 (eSuite)** out of the Platform catch-all into a dedicated `SKILL_QRA_eSuite_OwnerPortal.md` — 60 actionable cases, distinctive vocabulary (V17 upgrade, owner login, check-detail web view, BA Contacts tab) that the catch-all's Quick Triage under-serves.
2. **Security mini-refresh** inside the Platform skill (40 actionable): screen-level button/attachment disablement (GL025), env connection denials, SEC_USER_ID.
3. **Null-category router note** in the KB router: treat no-category cases as vocabulary-first (they sampled as PPA/impairment + check-write symptoms).
4. No new skills needed for groups 1–8 — refresh evidence bases on next mining pass (skills were built 2026-06-14; ~2.5 months of new cases since).

---

## 3. Per-group mining keywords (SOQL `Subject LIKE '%kw%'` — distinctive strings, not plain English)

| Group | Keywords |
|---|---|
| 1 Check Write | `CW_MAIN`, `PCW`, `CWBANKACH`, `CWACHEMAIL`, `NACHA`, `negative check`, `OFR`, `CWOWFNDRLS`, `NAUPA`, `CW005`, `footing`, `WELLSFARGO`, `check legend`, `RylPmtTypeCode`, `state withholding` |
| 2 PPA / PPN | `PPN`, `PPA`, `impair`, `Impaired Reason 301`, `540 error`, `302 impairment`, `612`, `recoup`, `rebook`, `DRI reversal`, `RRV`, `LD45`, `LD65` |
| 3 Revenue Distribution | `VL100`, `VL031`, `VL040`, `BKRVNU`, `RDCALCNEW`, `RDPROCNEW`, `CA020`, `DRI`, `VLCALC`, `SOD`, `remitter`, `flow grid` |
| 4 Ownership / Master Data / BA | `DOI`, `DOINTXFER`, `maintenance group`, `MEG`, `market group`, `bearer group`, `NRI`, `DO130`, `DO005`, `masterlink`, `BA005`, `zip code validation`, `Tax ID`, `TIN`, `Customer Category`, `transfer` |
| 5 Journal | `JE100`, `JE101`, `JE102`, `JEPOST`, `QCFSEXPORT`, `Export to QCFS`, `MJE`, `RRID`, `JESUMMARY`, `roll date`, `DATAPUBLISH`, `posting` |
| 6 Tax & Regulatory | `TS006`, `TS005`, `TX006`, `severance`, `CW1099EXPT`, `1099`, `MISC`, `NEC`, `ONRR`, `MMS-2014`, `withholding`, `tax combo`, `NM Tax`, `Product Code 400` |
| 7 A&D / Payouts | `QP043`, `ASTG_ORG_V2`, `Acquisition Stage`, `payout`, `PO005`, `POR005`, `PO010`, `divestiture`, `EC010`, `CWMNLESCHT`, `CWUCESCHT`, `dormancy` |
| 8 Volume Allocation | `VA005`, `VA030`, `VA035`, `INT_ALLOC`, `Staging Volume`, `GB010`, `GB015`, `OGP`, `SP025`, `well completion`, `PD051`, `wind royalty`, `CACTRALLOC` |
| 9 eSuite | `eSuite`, `ESUITE_Q`, `owner portal`, `check detail`, `V17`, `web down`, `Contacts tab`, `owner relations`, `login` |
| 10 Integration | `UPSLSINTFC`, `ODP`, `UBT`, `interface`, `FTP`, `File Zilla`, `refresh`, `Enverus`, `EnergyLink`, `Land Connections`, `Approved for Accounting` |
| 11 Security | `security group`, `edit rights`, `GL025`, `disabled`, `unable to connect`, `SEC_USER_ID`, `access`, `permission`, `grant` |
| 12 Platform / infra | `QQM`, `QPEC`, `PostWkFL`, `Qued for Processing`, `stuck`, `Citrix`, `Storefront`, `restart`, `hotfix`, `Patch`, `lock`, `Failed to clean`, `App Launch Error` |
| 13 Uncategorized | route by any of the above; sampled subjects hit `Impaired Reason`, PPN, and check-write vocab |

---

## 4. ADO notes (org `QuorumSoftware`)

Area paths verified by reading `[System.AreaPath]` off real QRA bugs (2026-09-02):

| Area Path | Project | Evidence | Use for |
|---|---|---|---|
| `QuorumSoftware\Engineering\Maintenance\Upstream\Professional Services` (+ `\Revenue` sub-area) | QuorumSoftware | Bugs 1624386 (DRI reversal), 1636588 (negative checks), 1737525 (owners not receiving checks — `\Revenue`) | **Primary** — client-escalated QRA maintenance bugs, tags `Maintenance: Escalated`, fix-version via `Robot RN`/Hotfix tags |
| `QuorumSoftware\Engineering\Financials` (+ `\Committed Backlog`, `\Customer Service`, `\Maintenance and Overhead`) | QuorumSoftware | Documented evidence base of the 3 SKILL_ADO_QRA_* files | QCFS/JIB/1099/check-write product-team bugs |
| `QuorumServices\Managed Services` | QuorumServices | Bug 1855204 (REP 302 impairment BKRVNU/VL100) | Managed-services-raised triage bugs (often `Proposed` state) |
| `Quorum\North America\Upstream\myQ Accounting RnD` | Quorum | Bug 1867627 (RD impairment 612 on PPAs) | R&D-side accounting bugs |

Bug titles routinely embed the SF case number (`25-01008963 - ...`) and client code prefix (`CNX`, `EQT`, `REP`, `RRC`, `SGY`, `MEW`) — search ADO by SF case number first.
Repos (per existing SKILL_ADO_QRA_* mining): `Quorum.Upstream.QRA.ClassicBatch`, `Quorum.Upstream.QCFS.*`, `Quorum.Upstream.QCA.ClassicBatch` / `.Database`, `Quorum.Upstream.Shared.ClassicBatch`; C++ batch internals cited as `QPSRDInterestTrackPostCalc.cpp`-style files.

---

## 5. Vocabulary seeds (spotted in 75 sampled actionable subjects, newest-first)

- **Process/batch codes:** `UPSLSINTFC`, `CWBANKACH`, `PCW`, `CW_MAIN`, `BKRVNU`, `PostWkFL`, `QPEC`, `QP043`, `INT_ALLOC`, `CACTRALLOC`, `CWMNLESCHT`
- **Screens:** `VL100`, `VL031`, `TS006`, `JE100`, `GL025`, `DO130`, `BA005`, `CW005`, `EC010`, `SP025`, `VA030`
- **Tables/views:** `RSTG_PCW_MIN_AMT_OWNR`, `QARCH_PROCESS_MSG_LOG`, `ASTG_ORG_V2`, `ESUITE_Q*` views, `DSTG_DO_TRACK_HDR`, `BHE_CONVERT_SSTAG_BANKDTL`
- **Error/reason codes:** impairment reasons `301`, `302`, `305`, `310`, `311`, `314`, `540`, `612`; `Group 23 Error`; "does not foot"; "Progressive rounding error"; "Failed to clean"
- **Domain acronyms:** `PPN`, `PPA`, `DRI`, `DOI`, `MEG`, `MJE`, `RRID`, `RRV`, `OFR`, `NRI`, `SOD`, `BG`, `MG`, `NAUPA`, `NACHA`, `TIK deck`
- **Config keys:** `USE_NETTING_FOR_CHK_MIN_RELEASE`, `CHECK_NETTED_MINIMUM_PAY`, `BOOKREV_TRACK_ERR_TWO`, `QARCH_EXP_DEF_DATA_FILTER` / `EXP_TO_PDS_FL`
- **Client codes seen:** BHE, CNX, EQT/EQC, MEW (Mewbourne), MAC (Mach), REP, RRC, SGY (Surge), DAY, UBT, Sandridge, Jonah, Eiger; env naming `<CLIENT3>U_HD_DEV17` / `_DEVA1` / `PRD A1` / `UATA1`

---

*Survey by Auto-Bot coverage-survey agent. Aggregates: SOQL 2026-09-02, all history. Subject sampling limited to 3 x 25 (no case bodies read). Actionable = Root_Cause__c IN ('Software Defect','Application Configuration'); add `ChangeConfig` (35) if the mining pass wants the wider net.*
