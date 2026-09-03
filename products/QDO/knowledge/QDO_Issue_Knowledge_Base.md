# QDO Issue Knowledge Base (Master Index)

**Product:** QDO — Salesforce `Product_list__c = 'My Quorum Division Order'` (2,702 cases all-history; actionable pool = Software Defect 407 + Application Configuration 213 + ChangeConfig 7 = **627**).
**Purpose:** Route a new QDO case to the right skill § fast — including the three gap groups closed 2026-09-02/03 (upgrade/patch regressions, JIB/cost-center/AFE crossover, imports & bulk loads) and the cases that belong to QRA, QCFS/QCA or the shared QPEC runbook.

> **How to use:** Match the case symptom/keyword in §1 → open the linked skill at the cited § → follow its Quick Triage + Decision Tree. Or search everything at once: `python engine/kb.py search "<symptom>" --product QDO -k 8`. All § anchors below were verified against the live skill headings on 2026-09-03.

---

## 1. Symptom → Skill Lookup

### 1.1 Core QDO skills

| If the case mentions… | Go to |
|---|---|
| **Combine** checked but lines didn't combine / split into 2 sequenced lines · combine erased **MEG / lease xref / market group** · **PPN created when none expected** (PD41/LD43 on a plain transfer) · **LD17/LD18 PPN fails** `302 Impairment remaining amount is not zero` / `311 remaining Total Tax Decimal not zero` · **OFR did not move the money** / partial move / funds left under old owner · **trapped suspense** / "held by another release" with no MG · MG **won't delete** / "partially deleted" · MG **locked** (approved twice) / can't release via DO025 · MG stuck **"Creating Group"/"Pending"** / **QRA Middle Tier error** on save · removing errored DOIs deletes ALL DOIs · **DOI Worksheet ignores PRECISION** / NRI past 8 decimals → GWI/BG approval fails · DO/Transfer Order form **duplicates the owner's interest** (DOR003/QP088) · mailing report NRI rounds to 8 / address missing / DOR015 Exhibit A mismatch · QP043 export **didn't reach QCFS GL** (MT100 cleared, COA JE Code Type) · **SAP integration error** (BA filter, SMICM timeout, DOI Sync stuck "Approved") · "Not Authorized to access security object" after upgrade · **DOI Copy** missing/erroring in Web · **Owner Search** no results / wrong fund total / >1000-line export | [SKILL_QDO_Division_Orders.md](../skills/SKILL_QDO_Division_Orders.md) §4 A transfer/Combine · §5 B PPN · §6 C OFR/suspense · §7 D MG lifecycle · §8 E DOI Setup/Worksheet/precision · §9 F mailing reports · §10 G integration · §11 H web upgrade screen/security · §12 I bearer/MEG setup · §13 J Owner Search (§14 ADO · §15 SQL · §16 FAQ) |
| Wells/transfers **stuck in DO129 at "3-Approved"** (double-approval) · OFR/EFR *"pending Suspense Release Transactions that have not been processed"* (`RSTG_OWNR_FUND_RLS(+_ERR)`, `FOOTING_TOLERANCE`) · workspace/MG approval **COPY_DVD / COPY_DVD_W fails** on FK or interest-seq (`FK_DONL_DVD_MKT_EXMPT`) · MEG assigned but **DO007 shows no exemptions** (backfill `DONL_MKT_EXMPT`) · funds don't move / wrong amount after transfer or **pay-code change** (`SL_DETAIL_NO` int32 overflow → 0) · bearer-group change / **carve-out doesn't generate PPN** / "bearer percent sum ≠ 1" · mass **MG status Pending→Complete / DOI change flag Y→N scripts** · transfer red-bars on bad data (Lawsuit Flag, trailing space, decimals) · owner/DOI search "NO DATA FOUND" / saved searches (`QARCH_FILTER_SAVE_NET`) · **Preview DOI / DOINTXWRK taking hours** | [SKILL_QDO_Transfers_SuspendRelease.md](../skills/SKILL_QDO_Transfers_SuspendRelease.md) §4 A DO129 3-Approved · §5 B OFR/EFR staging · §6 C COPY_DVD FK · §7 D MEG missing · §8 E funds wrong · §9 F carve-out/PPN · §10 G mass cleanup scripts · §11 H bad-data blocks · §12 I query screens · §13 J performance (§14 ADO · §15 SQL · §16 FAQ) |
| **Zip code error saving a BA** / 4-digit zip suffix / zip mask · "No States listed on BA Address tab" (Code Table 30000) · SSN/Tax-ID blocks BA save (**BA Tax-ID security objects**) · adding SSN **removes the 1099 indicator** (sync with `SCTRL_BA_ENTITY`) · BA **notes/attachments/contact-type didn't convert to Web** · can't create Property after Cost Center (**ORGCOSTGEN** access) · no Approval button on BA / Cost Center security error (**ORG/BTYP/QRA**) · `SecurityId not registered with QApplicationController` / **OKTA/Citrix** access · session logs out after 10–15 min (`SESSION_TIMEOUT`) · **SAP vendors not creating BAs** / SYNCHRONIZE_WITH_API HTTP 500 (`OPENID` web config) · **PUBBA stuck/locked** / MGs stopped interfacing to SAP · **UPSLSINTFC** (QLS lease interface) failing / out-of-memory · DOI maintenance/transfer record auto-deletes (Design Studio) · **Owner Lease Xref bulk-edit/import** doesn't work · reports not visible in QDO Web / **QQM timeout / SSO** | [SKILL_QDO_Platform_Integration.md](../skills/SKILL_QDO_Platform_Integration.md) §4 A zip/state/country masking · §5 B 1099/SSN/Tax-ID security · §6 C conversion gaps · §7 D security objects/Citrix/OKTA · §8 E SAP⇄QDO (PUBBA) · §9 F QLS⇄QDO (UPSLSINTFC) · §10 G Design Studio DOI maint · §11 H Owner Lease Xref import · §12 I QQM (§13 ADO · §14 SQL · §15 FAQ) |
| Web **widgets fail HTTP 404 / "Something went wrong"** after refresh/cutover/patch (`QARCH_EXTERN_APP_SETUP.TARGET_EXE` quorum:// URL + QPEC restart) · one user's widget still errors (widget security group, e.g. **95000** New Business) · post-upgrade **MG Creation keeps old data / flips approved MG to 5-Error** (`DonlDvdGrp` cache, **WRKSPC** re-run, ADO 1775211) · MG stuck "Submitted for approval" with no transactions · post-upgrade MG/DOI maintenance 15+ min · field editable in classic DO006 but **read-only in web DOI Setup** (`DOI_EDIT_APPROVED_MASTER_DATA`) · report parameter LOV missing after patch (QP088 "Template Type") · **Patch 71 config drift** ("did the patch drop our configs?") · OFR not moving monies after web cutover (`RUN_WINFORM_CALC_FOR_RSTG` + `DISABLE_CLASSIC_SCREEN` = 1) · funds-only MG "Retrieve" dead after hotfix (redeploy) · funds didn't auto-populate in MGs after go-live (**ODBC driver → JE100** OFR feed) · 2023.04 UAT: `Column 'OrigBusUnitCode' does not allow DBNull.Value` · 2023.04 UAT: `FK_DONL_DVD_MKT_EXMPT__DONL_DVD_DO_DETAIL` delete conflict · mass transfer Preview "Old owner not in DO" (DOINTXFRWB chunking) · **PRD A1 / UAT** environment down after go-live | [SKILL_QDO_Upgrade_Patch_Regressions.md](../skills/SKILL_QDO_Upgrade_Patch_Regressions.md) §4 A widgets 404 · §5 B MG-creation regressions · §6 C classic→web parity · §7 D patch/config drift · §8 E build-UAT regressions (2023.04 wave) · §9 F environment/infra + ODBC/JE100 (§10 ADO · §11 SQL · §12 FAQ) |
| Can't save a 2nd JIB tier ("must have **JIB Base Flag** checked") · JIB tier number 100 saves as Tier 1 (`CAN_CHANGE_TIER_VALUE`/`CAN_CHANGE_TIER_JIB_VALUE`) · JIB deck missing from **backdate screen BD006** (`SELECT_DONL_DO_PROP_BACKDATE_PICK`) · JIB transfer warnings **RADOITRW58/RADOITRW59** (default market rep, code table **29100**) · JIB deck template imports MI but shows DI · **JIB OFF SET** owner forces Pay Reason 5 · new cost center "number already in use" (code table **29111** / `QARCH_TRAN_SEQ` Last No, ADO 1837136) · cost center saves but property screen never opens (**ORGCOSTGEN**) · CC security error but CC still created (**ORG/BTYP/QRA**) · AFE sync/crossover · **Import From Excel loads NRIs as 0.00000000** (scientific notation `1E-08`, ADO 1322617/1813832) · DOI Worksheet import skips owners' NRI (`NRIDecMasked`) · **Owner Lease Xref "Replace Content" reverts on Save** · Bulk View/Edit on Bearer Group adds/deletes rows or rounds pasted decimals · "Load BA data from **Mineral Answers**" / **Datayank** | [SKILL_QDO_JIB_Crossover_Imports.md](../skills/SKILL_QDO_JIB_Crossover_Imports.md) §4 A base flag · §4 B tier numbering/backdate · §4 C RADOITRW58/59 · §4 D deck template · §4 E cost center numbering & security · §4 F AFE crossover · §5 G Excel-import decimals · §6 H/I Xref import & bulk edits · §7 J external loads (§8 FAQ · §9 ADO · §10 SQL · §11 Escalation) |

### 1.2 ADO defect-and-fix references (use when the question is "is this already fixed, and in what build?")

| If the case mentions… | Go to |
|---|---|
| AP voucher / GL batch "**Invalid DOI Key Combination**" / "Must approve DOI before booking…" on reverse/reclass (By-Design, NULL tier) · "Activity date is not within the DOI's effective date range" wrong/missing on **AP055** · duplicate unapproved-DOI messages on **GL025/AP055** post · **AFEEXTIMP** "The property must have a DOI" · **JB020 "not an effective JIB DOI"** on a valid save (date-format) · DO006 "NRI decimal sum of 1.75" / Delete greyed on header-only DOI / documents won't attach · **DOINTXWRK preview batch fails** after a MG transfer (`IQMetadataService.DO`) · converted AFEs **NULL `AFE_DOI_DEC`** · DOI picklist duplicates (AFE committed costs, web) · `Sel_DoiDecimals` slow | [SKILL_ADO_QDO_DivisionOrder_Transfers.md](../skills/SKILL_ADO_QDO_DivisionOrder_Transfers.md) §4 A AP055/GL025 DOI validation · §5 B AFE/JIB validation · §6 C DO006 · §7 D DOINTXWRK preview · §8 E converted-AFE decimals · §9 F picklist/perf (§10 not-QDO overlap · §11 fix-version matrix · §12 diagnostics) |
| POSTWKFL/PSTWKSPLT fails **only on the scheduler** · "Workflow Instance … no longer available/does not exist" on Approve · status stuck after approve · **frowny face** / console 500 / **Kendo** regressions after 2024.10 · XSS pop-ups · password reset blank email · attachment handling · process-launch/impersonation plumbing | [SKILL_ADO_SHARED_eSuite_V2UI_Workflow_Performance.md](../skills/SKILL_ADO_SHARED_eSuite_V2UI_Workflow_Performance.md) §3 A POSTWKFL · §4 B workflow engine · §5 C performance · §6 D V2UI/Kendo · §7 E XSS/login · §8 F attachments · §9 G process launch (§10 fix-version matrix) |

---

## 2. CROSS-PRODUCT ROUTING

### 2.1 QPEC engine / scheduler (shared runbook)

Any QPEC symptom routes to **[../../_shared/skills/SKILL_QPEC_Ops_Runbook.md](../../_shared/skills/SKILL_QPEC_Ops_Runbook.md)** (indexed into the QDO vector KB).

| Symptom | Go to |
|---|---|
| `COPY_DVD_W` "QPEC SYSTEM ERROR" / maintenance group or transfer stuck in Processing / MEG-search QPEC crashes | runbook §3 (stuck-queue, step 6) + §4 (crash/restart) |
| "Gracefully restart the QPECs" / engines down / "Unable to establish a connection with any endpoint" | runbook §4c |
| Post-patch mass timeouts (QPEC.ini / `COMMAND_TIMEOUT_SECONDS` reset by deployment) | runbook §5 |
| Scheduled run fails but manual run works | runbook §3 step 8 |

### 2.2 Other products

| If the case (filed under QDO) is really about… | Go to |
|---|---|
| Revenue distribution (VL100/BKRVNU), check write (CW_MAIN/PCW), QRA-side PPA/impairment, QRA MG middle tier internals | **QRA** — [QRA_Issue_Knowledge_Base.md](../../QRA/knowledge/QRA_Issue_Knowledge_Base.md); note QDO MG saves ride the **QRA Middle Tier** (RabbitMQ) — restart guidance stays in SKILL_QDO_Division_Orders.md §7/§10 |
| AP vouchers / GL batches themselves (not the DOI validation on them), POSTWKFL post-pending drains | **QCFS** — [../../QCFS/knowledge/QCFS_Issue_Knowledge_Base.md](../../QCFS/knowledge/QCFS_Issue_Knowledge_Base.md); the DOI-validation crossover stays in SKILL_ADO_QDO_DivisionOrder_Transfers.md §4–§5 |
| JIB billing cycle / rebill / owner allocation (JB0xx processing, not JIB DOI setup) | **QCA** — `../../QCA/skills/SKILL_QCA_Joint_Interest_Billing.md` |
| QLS lease master defects behind UPSLSINTFC records | **QLS** — QDO side stays in SKILL_QDO_Platform_Integration.md §9 |

---

## 3. Coverage Map (from [QDO_Coverage_Plan.md](QDO_Coverage_Plan.md) §3, survey 2026-09-02; covered_by updated 2026-09-03)

| # | Group | Est. actionable | Covered by |
|---|---|---:|---|
| G1 | Interest Transfers / carve-out / Combine / pay-code change | ~95 | ✅ SKILL_QDO_Division_Orders.md §4 + SKILL_QDO_Transfers_SuspendRelease.md §4–§9 |
| G2 | DOI Setup / Worksheet / Copy / Tier / decimal precision | ~85 | ✅ SKILL_QDO_Division_Orders.md §8 + SKILL_ADO_QDO_DivisionOrder_Transfers.md §6/§8 |
| G3 | Maintenance Group lifecycle (create/preview/approve/delete/stuck) | ~65 | ✅ SKILL_QDO_Division_Orders.md §7 + SKILL_QDO_Transfers_SuspendRelease.md §6/§10 |
| G4 | Upgrade / patch / hotfix regressions & environment availability | ~62 | ✅ **GAP CLOSED 2026-09-03** → SKILL_QDO_Upgrade_Patch_Regressions.md |
| G5 | BA master-data web screens | ~58 | ✅ SKILL_QDO_Platform_Integration.md §4–§6 |
| G6 | Suspend/Release: OFR / EFR / NAUPA / escheat / stuck releases | ~45 | ✅ SKILL_QDO_Transfers_SuspendRelease.md §4–§5 + SKILL_QDO_Division_Orders.md §6 |
| G7 | DO mailing reports & report launcher | ~38 | ✅ SKILL_QDO_Division_Orders.md §9 |
| G8 | Security objects / groups / roles / login | ~38 | ✅ SKILL_QDO_Platform_Integration.md §7 (+ widget groups: SKILL_QDO_Upgrade_Patch_Regressions.md §4) |
| G9 | Integration: SAP-PRA / QRA MT / QLS / equity-group interfaces | ~32 | ✅ SKILL_QDO_Platform_Integration.md §8–§9 + SKILL_QDO_Division_Orders.md §10 |
| G10 | Owner / DOI Search & query screens | ~30 | ✅ SKILL_QDO_Transfers_SuspendRelease.md §12 + SKILL_QDO_Division_Orders.md §13 |
| G11 | PPN generation & staging | ~20 | ✅ SKILL_QDO_Division_Orders.md §5 |
| G12 | JIB / Cost Center / AFE crossover (SF-side) | ~18 | ✅ **GAP CLOSED 2026-09-03** → SKILL_QDO_JIB_Crossover_Imports.md §4 (ADO defect side stays in SKILL_ADO_QDO_DivisionOrder_Transfers.md §4–§5) |
| G13 | Imports & bulk data loads | ~16 | ✅ **GAP CLOSED 2026-09-03** → SKILL_QDO_JIB_Crossover_Imports.md §5–§7 (+ SKILL_QDO_Platform_Integration.md §11) |
| G14 | QQM reporting & authentication | ~10 | ✅ SKILL_QDO_Platform_Integration.md §12 |

Groups 1–14 = ~98% of the 627 actionable. All three survey GAPs (G4, G12, G13) are closed by the 2026-09 mining wave.

---

## 4. Cross-cutting QDO patterns (check on every case)

1. **The gate ladder loves QDO config.** Web-cutover misbehavior is usually `QARCH_EXTERN_APP_SETUP`, `RUN_WINFORM_CALC_FOR_RSTG`/`DISABLE_CLASSIC_SCREEN`, a missing security object/group, or a metadata layer overwritten by a patch — check config (G2) before code (G5).
2. **Double-click defects are a family.** DO129 3-Approved, MG approved twice, WRKSPC re-run flipping approved MGs to 5-Error — anything "stuck after user clicked twice" starts with the status-repair script, then the ADO fix check.
3. **QDO MG/transfer saves ride the QRA Middle Tier** (RabbitMQ). "Stuck Creating Group"/"Pending" under PRD load = restart RabbitMQ + QRA MT QPEC before investigating data.
4. **Refresh/cutover drift.** After any environment refresh: widget URLs, ODBC driver on new servers, report parameter metadata, import/export paths, session-timeout layers. "Worked before the refresh" starts here.
5. **SOQL LIKE gotcha:** underscore is a single-char wildcard — `LIKE '%INT_%'` matches "maintenance". Escape it or spell out `INT_QLSWL`.
6. **SF conversation source:** CaseComment and EmailMessage are **empty for QDO** — the conversation lives in CaseFeed TextPost/LinkPost. Query via the Feeds relationship subquery (`SELECT Subject, (SELECT Body FROM Feeds WHERE Type IN ('TextPost','LinkPost')) FROM Case …`); direct SOQL on CaseFeed with a ParentId filter has returned corrupted/mismatched results.

---

## 5. Standard data sources

- **Salesforce:** connector `soqlQuery`; filter `Product_list__c = 'My Quorum Division Order'`. `LIMIT ≤ 25`. Conversation = CaseFeed Feeds subquery (see §4.6).
- **Azure DevOps:** org `QuorumSoftware`. Area paths: `QuorumSoftware\Engineering\Revenue\Committed Backlog`, `QuorumSoftware\Engineering\Maintenance\Upstream\{Professional Services|Customer Service}\Revenue`, `QuorumSoftware\Engineering\Financials` (DOI-validation crossover), and newer bugs under `Quorum\North America\Upstream\myQ Accounting RnD`. Titles embed client prefix + SF case number. Repos: `Quorum.Upstream.QDO.*`, `Quorum.QDO.ServiceCore`, shared `Quorum.QFC.*` — detail: [code_logic/REPO_REFERENCE_UPSTREAM.md](code_logic/REPO_REFERENCE_UPSTREAM.md).
- **Environments:** `<CLIENT>U_HD_DEV17` (classic tier) vs `<CLIENT>U_HD_DEVA1` (web tier); PRD A1 / UAT2 naming in case text.
- **Vector KB:** `python engine/kb.py search "<symptom>" --product QDO -k 8` (includes `_shared` skills).
- **Coverage survey:** [QDO_Coverage_Plan.md](QDO_Coverage_Plan.md) — volumes, per-group keywords, ADO notes.
- **Legacy routers (still valid for upstream-wide rows):** [UPSTREAM_Issue_Knowledge_Base.md](UPSTREAM_Issue_Knowledge_Base.md), [UPSTREAM_ADO_Defect_Index.md](UPSTREAM_ADO_Defect_Index.md).

---

*Index created 2026-09-03 from `QDO_Coverage_Plan.md` (survey 2026-09-02) + the 6 live QDO skills (incl. the two new gap skills) + the shared QPEC runbook and eSuite/V2UI defect reference. § anchors verified against live skill headings.*

*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
