# QDO Coverage Plan — Skill-Gap Survey

**Product:** QDO — `Product_list__c = 'My Quorum Division Order'`
**Survey date:** 2026-09-02 · All-history aggregates (no date filter) · Sampled 100 newest actionable subjects (4 × LIMIT 25 pages)
**Purpose:** map the actionable case volume to skill groups, mark which groups the 4 existing skills already cover, and flag GAP groups for mining.

---

## 1. Aggregates

### 1.1 Total volume & Status (closed volume)

Total QDO cases (all history): **2,702**

| Status | Count |
|---|---|
| Closed | 2,230 |
| Closed - No Response | 256 |
| Closed - Deferred | 61 |
| Complete - Pending Customer Review | 31 |
| Complete - Pending Delivery | 26 |
| Pending Quorum | 22 |
| In Development Queue | 19 |
| In Review | 18 |
| New | 17 |
| Pending Customer | 9 |
| In Progress | 8 |
| Development In Progress | 5 |

≈ 94% closed — mature history, good mining base.

### 1.2 Root_Cause__c (top 20 of 41 values)

| Root_Cause__c | Count |
|---|---|
| (blank) | 525 |
| **Software Defect** | **407** |
| Customer Error | 301 |
| Customer Cancelled | 282 |
| **Application Configuration** | **213** |
| Training | 188 |
| Hardware/Software Change | 103 |
| Other | 83 |
| Business Change | 82 |
| No Action Taken | 62 |
| Platform | 56 |
| Performance | 47 |
| Project Debt | 46 |
| Hardware/Software Env Change | 40 |
| User Administration Request | 35 |
| Not in Product Plan | 33 |
| Upgrade Request | 24 |
| Client Managed Infrastructure | 20 |
| Release Collateral Damage | 19 |
| ... (ChangeConfig = 7) | ... |

**Actionable** (Software Defect 407 + Application Configuration 213 + ChangeConfig 7) = **627** (23% of all cases).

### 1.3 Case_Category__c (all cases → actionable)

| Case_Category__c | All cases | Actionable (SD+AC+CC) | Actionable share |
|---|---|---|---|
| Division Orders | 1,456 | 379 | 60.4% |
| Transfers | 334 | 77 | 12.3% |
| eSuite | 132 | 54 | 8.6% |
| Integration | 112 | 25 | 4.0% |
| (blank) | 184 | 20 | 3.2% |
| Design Studio | 124 | 16 | 2.6% |
| Suspend/Release | 110 | 16 | 2.6% |
| Query Screens | 44 | 15 | 2.4% |
| Security | 63 | 14 | 2.2% |
| QQM | 40 | 6 | 1.0% |
| Other | 56 | 3 | 0.5% |
| All | 47 | 2 | 0.3% |
| **Total** | **2,702** | **627** | 100% |

Category field is well-populated (only 6.8% null) — but "Division Orders" is a mega-category (54% of everything), so groups below split it by symptom-family vocabulary from subject sampling.

### 1.4 Keyword-family sizing (actionable only, Subject LIKE counts — overlapping)

| Family probe | Actionable hits |
|---|---|
| transfer / carve / combine / convey | 101 |
| DOI / worksheet / decimal / NRI / tier | 123 |
| maintenance group / pending / queued / stuck | 69 |
| suspen / release / OFR / NAUPA / escheat / funds | 66 |
| upgrade / patch / MEW / deploy | **66** |
| BA family (zip / 1099 / tax id / business associate / vendor / SSN) | 68 |
| report / DOR0 / QP08 / mailing / NOMS | 38 |
| search / sort / query / filter / GRPREF | 35 |
| SAP / interface / integration / middle tier | 32 |
| security / login / access | 24 |
| PPN / prior period | 19 |
| JIB / cost center / AFE / voucher | 18 |
| import / excel / datayank / bulk | 17 |

---

## 2. Existing skills (scope from §1/headers)

| # | Skill file | Scope (short) |
|---|---|---|
| S1 | `SKILL_QDO_Division_Orders.md` | Division Orders category: DOI Setup/Worksheet/precision, Maintenance Groups, transfers+Combine, OFR/suspense, PPN, DO mailing reports (DOR003/008/009/015, QP088), Owner Search, MEG/bearer groups, SAP-PRA/QCFS/QRA-MT integration, web-upgrade screen/security cluster. 333 actionable mined. |
| S2 | `SKILL_QDO_Transfers_SuspendRelease.md` | Transfers (DO129, carve-out, recoupment, bearer/MEG movement), Suspend/Release (OFR/EFR, pay-code, escheat/NAUPA), Query Screens (owner/DOI search, saved searches, DOR/CI reports), performance. 99 actionable mined. |
| S3 | `SKILL_QDO_Platform_Integration.md` | BA master-data web screens (zip/state/1099/SSN/Tax-ID/notes/attachments), eSuite Web vs Classic, SAP⇄QDO (PUBBA, vendor→BA, MG/JIB netting), QLS⇄QDO (UPSLSINTFC), security groups/objects/OKTA/Citrix, QQM access, Design Studio screen defects, Owner Lease Xref import. 99 actionable mined. |
| S4 | `SKILL_ADO_QDO_DivisionOrder_Transfers.md` | ADO defect reference: DOI validation on AP vouchers/GL (AP055/GL025), AFE/JIB DOI validation (JB020, AFEEXTIMP), DO006 calc/approve/delete, DOINTXWRK preview, converted-AFE DOI decimals. |

---

## 3. Proposed skill groups (14 groups ≈ 98% of actionable)

Estimates are normalized from the overlapping keyword counts in §1.4 against the 627 actionable total.

| # | Group | Categories | Est. actionable | Covered by |
|---|---|---|---|---|
| G1 | Interest Transfers / carve-out / Combine / pay-code change | Division Orders, Transfers | ~95 | S1 + S2 |
| G2 | DOI Setup / Worksheet / Copy / Tier / decimal precision | Division Orders | ~85 | S1 + S4 |
| G3 | Maintenance Group lifecycle (create/preview/approve/delete/stuck) | Division Orders | ~65 | S1 + S2 |
| G4 | **Upgrade / patch / hotfix regressions & environment availability** | Division Orders, eSuite, All | ~62 | **GAP** (partial: S1 Cluster H, S3 Cluster C — no release-regression skill) |
| G5 | BA master-data web screens | eSuite | ~58 | S3 |
| G6 | Suspend/Release: OFR / EFR / NAUPA / escheat / stuck releases | Suspend/Release, Division Orders | ~45 | S2 |
| G7 | DO mailing reports & report launcher | Division Orders | ~38 | S1 |
| G8 | Security objects / groups / roles / login | Security, Division Orders | ~38 | S3 |
| G9 | Integration: SAP-PRA / QRA MT / QLS / equity-group interfaces | Integration, Division Orders | ~32 | S3 + S1 |
| G10 | Owner / DOI Search & query screens | Query Screens, Division Orders | ~30 | S2 + S1 |
| G11 | PPN generation & staging | Division Orders | ~20 | S1 |
| G12 | **JIB / Cost Center / AFE crossover (SF-side)** | eSuite, Division Orders | ~18 | **GAP** (S4 covers only the ADO defect-reference side of DOI-on-AP/GL/AFE; the SF case family — JIB deck backdate, cost-center errors, JIB transfer fatal error, JIB offset flag, CC renumbering — is unmined) |
| G13 | **Imports & bulk data loads** | Division Orders, eSuite | ~16 | **GAP** (S3 Cluster H covers only Owner-Lease-Xref import; Excel-import decimals, Mineral Answers, Datayank, bulk edits unmined) |
| G14 | QQM reporting & authentication | QQM | ~10 | S3 |

**GAP groups to mine: G4, G12, G13** (~96 actionable cases, ~15% of actionable volume). Everything else is already covered by the 4 existing skills.

### Per-group mining keywords (SOQL LIKE-ready, distinctive strings)

| Group | Keywords for `Subject LIKE` / body mining |
|---|---|
| G1 | `transfer`, `carve-out`, `combine`, `DOINTXWRK`, `pay code`, `paycode`, `Preserve Interest Type`, `recoup`, `SOD` |
| G2 | `DOI Setup`, `DO006`, `DOI Worksheet`, `DOI Copy`, `qFrmDOICopy`, `NRI`, `GWI/PPI`, `decimal`, `DO Tier`, `DOI History` |
| G3 | `Maintenance Group`, `Preview`, `stuck`, `Pending status`, `Queued`, `COPY_DVD`, `Workspace Creation`, `QRA Middle Tier` |
| G4 | `Upgrade`, `Patch`, `Hotfix`, `MEW`, `2023.04`, `2025.04`, `UAT`, `PRD A1`, `widget`, `404`, `deployment`, `regression` |
| G5 | `Business Associate`, `zip code`, `1099`, `Tax ID`, `SSN`, `contact type`, `BA notes`, `vendor`, `producer type`, `Code Table 30000` |
| G6 | `Owner Funds Release`, `OFR`, `EFR`, `Suspense Release`, `NAUPA`, `escheat`, `RSTG_OWNR_FUND_RLS`, `DO129`, `3-Approved`, `Triple Release` |
| G7 | `DOR003`, `DOR008`, `DOR009`, `DOR015`, `QP087`, `QP088`, `Report Launcher`, `NOMS Title Memo`, `mailing`, `exhibit` |
| G8 | `security object`, `security group`, `DO Approver`, `U_DO_MAINT`, `OKTA`, `login`, `missing security`, `privilege` |
| G9 | `SAP-PRA`, `PUBBA`, `UPSLSINTFC`, `INT_QLSWL`, `Equity Group Interface`, `Middle Tier`, `webservice`, `DSTG_`, `RISE` |
| G10 | `Owner Search`, `saved search`, `GRPREFWEB`, `sorting`, `filter`, `fund total`, `suspense report` |
| G11 | `PPN`, `Prior Period`, `LD65`, `PD41`, `LD43`, `PN025`, `impairment`, `PPN staging` |
| G12 | `JIB DOI`, `JIB Deck`, `Cost Center`, `JIB OFF SET`, `JIB offset`, `AFE`, `AP055`, `GL025`, `voucher`, `JB020`, `renumbering` |
| G13 | `Import From Excel`, `Mineral Answers`, `Owner Lease Xref`, `Datayank`, `bulk edit`, `data load`, `import` |
| G14 | `QQM`, `RC4`, `sign in`, `report visibility`, `report access` |

Caveat on `LIKE '%INT_%'`: the underscore is a single-char wildcard in SOQL LIKE — it matches "ma**int**enance". Escape it (`INT\_`) or use the full process name `INT_QLSWL` spelled out.

---

## 4. ADO notes

- **Org:** `QuorumSoftware`. QDO bugs live overwhelmingly in project **`QuorumSoftware`** (92 of 102 hits for "QDO division order transfer" Bug search); a few strays in `Quorum` and `QuorumServices` projects.
- **Area Paths observed on real QDO bugs** (read from 7 bugs):
  - `QuorumSoftware\Engineering\Revenue\Committed Backlog` — product-engineering backlog (QDO sits under the Revenue/Upstream engineering org). Bugs #264870, #1599810, #1723387.
  - `QuorumSoftware\Engineering\Maintenance\Upstream\Professional Services\Revenue` — maintenance/escalation stream. Bugs #1651746, #1758284, #1760759.
  - `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Revenue` — customer-service escalations (SF case number often in title, e.g. #1780297 ↔ 26-01069100).
  - `QuorumSoftware\Engineering\Financials` — DOI-validation crossover bugs on AP/GL/AFE (per existing S4 skill).
- **Repo/name patterns** (from stack traces + S4): `Quorum.Upstream.QDO.*` (e.g. `Quorum.Upstream.QDO.Application.MiddleTier`, `Quorum.Upstream.QDO.ReleaseNotes`), namespaces `Quorum.QDO.ServiceCore`, shared platform `Quorum.QFC.*`.
- **Title conventions:** client prefix + SF case number is common (`APA UPS QDO: ... - 26-01069100`, `24-00949807--Transferring...`, `MEW 2023.04 - ...`, `MAC - ...`, `WEB QDO: ...`). WIQL mining should filter `[System.Title] CONTAINS 'QDO'` OR contains the SF case number.

---

## 5. Vocabulary seeds (spotted in subjects/repro text — for KB queries & mining)

- **Batch/process codes:** `DOINTXWRK` (Preview DOI interest transfer), `COPY_DVD` (workspace approval), `INT_QLSWL` (QLS well interface), `UPSLSINTFC` (QLS⇄QDO lease), `AFEEXTIMP` (AFE XML import), `PUBBA` (SAP BA publish)
- **Screens:** `DO006` DOI Setup, `DO129` funds transfer status, `AP055` AP voucher, `GL025` GL batch, `JB020` JIB, `qFrmDOICopy`, Maintenance Group Creation, DOI Maintenance, Owner Search, `GRPREFWEB`
- **Reports:** `DOR003/008/009/015` (DO mailing), `QP087/QP088` (report launcher), NOMS Title Memo, NAUPA report
- **Tables:** `DONL_*` (live), `DONL_DVD_*` (workspace staging), `RSTG_OWNR_FUND_RLS(+_ERR)` (release staging), `DSTG_*` (SAP staging), `DONL_INT_FUNDS_XFER_HDR`, `DONL_DO_HIST` (TRANS_GRP_SEQ sequence), `QARCH_SEC_USERACTION_AUDIT`
- **Error/domain phrases:** "GWI/PPI is not equal to 1", "pending Suspense Release Transactions that have not been processed", "3-Approved" stuck status, "Invalid DOI Key Combination", "not an effective JIB DOI", PPN reason codes `LD43/LD65/PD41`, "Preserve Interest Type", Unit-to-tract (UTT), MEG/TEG/SOD groups, pay codes 1/2/8, `FOOTING_TOLERANCE` config
- **Release vocabulary:** MEW/MAC/APA/CNR client prefixes, "2023.04"/"2025.04" versions, "October '25 2023.04 Hotfix", Upstream Patch N, PRD A1 / UAT2 / DEVA1 environments

---

*Survey method: aggregate SOQL only + 100-subject sample; no case bodies read. Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat.*
