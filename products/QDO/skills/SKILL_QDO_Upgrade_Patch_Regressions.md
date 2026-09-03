# SKILL: QDO Upgrade / Patch / Hotfix Regressions & Environment Availability

**Version:** 1.0 | **Created:** 2026-09-03 | **Product:** My Quorum Division Order (QDO) — `Product_list__c = 'My Quorum Division Order'`
**Scope:** Everything that breaks *because a build changed* — version upgrades (classic desktop → myQDO Web, 2021.04 → 2025.04 trains), monthly hotfixes, numbered patches, post-refresh/cutover config drift, web-widget outages (404 / "Something went wrong"), UAT/build-test regressions, and hotfix delivery/deployment mechanics. Covers coverage-plan group **G4** (~62 actionable cases).
**Companion skills:** `SKILL_QDO_Division_Orders.md` (DOI/MG functional detail), `SKILL_QDO_Transfers_SuspendRelease.md` (transfer/OFR pipeline), `SKILL_QDO_Platform_Integration.md` (BA web screens, security groups, eSuite), `SKILL_ADO_QDO_DivisionOrder_Transfers.md` (ADO defect reference for DOI-validation crossovers).

> **Evidence base:** 75 closed actionable cases sampled newest-first (3 × LIMIT 25 pages, `Root_Cause__c IN ('Software Defect','Application Configuration','ChangeConfig')`, subject keywords upgrade/patch/hotfix/MEW/2023.04/2025.04/deploy/widget/404), plus full Description/Resolution and case-feed deep-dives on 12 of the richest. Every claim cites a verbatim SF case number and/or ADO work item ID. Fixed-in builds are **INFERRED** from case-feed/tag text unless marked CONFIRMED.
> **PII:** individual names redacted; 3-letter client prefixes (MEW, APA, REP, PNR, GEC, GLE, CNR) retained as they identify orgs, not persons.

---

## 1. Quick Triage Table

| Symptom | Likely cause | Go to |
|---|---|---|
| QDO web widgets fail with **HTTP 404** or "Something went wrong" after a refresh / mock cutover / patch | `QARCH_EXTERN_APP_SETUP.TARGET_EXE` URL wrong (post-refresh scripts set it to the wrong env), needs QPEC restart | §4 Cluster A |
| One user's widget still errors after the URL fix | User missing the widget's security-group assignment (e.g. group **95000** = New Business widget) | §4 Cluster A |
| After upgrade, Maintenance Group Creation screen keeps old data; re-clicking "Create Maintenance Group" flips an **approved MG to 5-Error** and reuses the old group number | UI controller caches `DonlDvdGrp`; WRKSPC re-runs on the existing approved group (ADO Bug **1775211**) | §5 Cluster B |
| MG creation flow "different in Live vs Test" — goes straight to the maintenance wizard | **Expected behavior**: intentional 2024.04 workflow change (release notes) | §9 FAQ |
| MG stuck "Submitted for approval" with no transactions; can't delete or revert | Code defect — deleting empty MGs was blocked; code fix delivered | §5 Cluster B |
| Post-upgrade MG/DOI maintenance takes 15+ minutes on large owner counts | Known perf defects on 2024.10 web (ADO **1756914**, **1668275**, **1673532**) | §5 Cluster B |
| Field editable in classic DO006 but **read-only in web DOI Setup** (e.g. Historical DOI #) | Web parity gap; fix gated by security action `DOI_EDIT_APPROVED_MASTER_DATA` | §6 Cluster C |
| Custom report / report parameter LOV missing after patch (e.g. QP088, Exhibit-A "Template Type") | Missing metadata for the parameter picklist in global metadata tables — isolated config, script fix | §7 Cluster D |
| "Did the patch drop our configs?" | Patch 71 case: isolated single-parameter issue, **not** bulk config loss | §7 Cluster D |
| OFR jobs not moving monies right after cutover to web | Web-QDO flip configs overwritten: `RUN_WINFORM_CALC_FOR_RSTG`, `DISABLE_CLASSIC_SCREEN` must be 1 | §7 Cluster D |
| Funds-only MG "Retrieve" button dead + middle-tier log "Exception has been thrown by the target of invocation" after hotfix | Bad/partial hotfix deployment — redeploy the hotfix | §7 Cluster D |
| Funds didn't auto-populate in MGs after go-live | Missing **ODBC driver** on new server → JE100 OFR records not flowing; install driver + script stuck records to error + rerun in JE100 | §8 Cluster F |
| 2023.04 UAT: Modify-with-funds errors `Column 'OrigBusUnitCode' does not allow DBNull.Value` | Build defect (copy/paste column bug from a Sept-2022 enhancement) — code fix | §8 Cluster E |
| 2023.04 UAT: MG preview fails `DELETE ... conflicted with FK_DONL_DVD_MKT_EXMPT__DONL_DVD_DO_DETAIL` | Obsolete tables left populated — script to truncate 2 unused tables | §8 Cluster E |
| 2023.04 UAT: mass transfer across multiple effective-date ranges errors on Preview ("Old owner not in DO") | Chunking defect in DOINTXFRWB mass transfer — code fix (chunk remainder now saved in subsequent transaction) | §8 Cluster E |

---

## 2. Concepts — how QDO upgrades & patches work

- **Version trains:** 2020.09 → 2021.04 → 2022.04 → 2023.04 → 2024.04 → 2024.10 → 2025.04 → 2025.10/2026.04. Clients upgrade infrequently; each train gets **monthly hotfixes** ("October 2025 Hotfix for 2023.04 Version", 25-01045796) and cumulative **numbered patches** ("Patch 5", "Patch 8", "Patch 71", "Upstream Patch 11 & 12").
- **Classic vs Web:** upgrades from desktop ("classic") QDO to **myQDO Web** produce a distinct regression family — field-permission parity, screen workflow changes, widget/URL config. Env naming: `<CLIENT>U_HD_DEV17` = classic-version env, `<CLIENT>U_HD_DEVA1` = web env (observed: MEWU_HD_DEV17 vs MEWU_HD_DEVA1 in 25-01003450 feed). Client tiers: DEV / UAT / UAT2 / UBT / **PRD A1**.
- **Delivery mechanics:** hotfixes are packaged per client-version and uploaded to the client **FTP** site (25-01045796). If the client never promoted the previous patch to PRD, the new hotfix must be **repackaged and redeployed** (25-01045796 internal note). A fix "delivered in the March hotfix" for one train may be *deliberately not backported* if the client has an active upgrade (25-01027179 feed: fix rides the 2025.04 upgrade instead).
- **Fix-in-version answers:** support quotes "included in Patch N" / "in the <month> hotfix" / "in the 2025.10 GA release" — treat all as **INFERRED** fixed-in until verified against release notes (`community.quorumsoftware.com/s/release-notes`) or ADO tags (`Robot RN 2026.04`, `2021.04 hotfix 1`, `UpsPerfHotfixed`).

---

## 3. Decision Tree

```
Symptom appeared right after an upgrade / patch / refresh?
├─ Widgets or whole web app erroring (404, "Something went wrong")
│   ├─ All users affected → QARCH_EXTERN_APP_SETUP URL wrong → Cluster A
│   └─ One user only → widget security-group assignment → Cluster A (secondary)
├─ Screen behaves differently than the old version
│   ├─ Check release notes first (2024.04 MG-wizard change is INTENTIONAL) → FAQ §9
│   ├─ Field read-only in web but editable in classic → Cluster C
│   └─ Data retained / status corrupted on re-use → Cluster B (ADO 1775211)
├─ Report / LOV / config missing after patch → Cluster D (metadata script, not bulk loss)
├─ Batch/funds pipeline dead after cutover → configs (Cluster D) or infra/ODBC (Cluster F)
└─ Errors only in the upgrade-UAT build (2023.04-style) → Cluster E (log to engineering;
    most have existing closed ADO bugs — search before filing)
```

---

## 4. Cluster A — Web widgets fail after refresh / cutover (404, "Something went wrong")

**Signature:** After an environment refresh, mock cutover, or patch, QDO web dashboard widgets (Owner/DOI Search, Pending DOI, New Business) return HTTP 404 or the generic "Something went wrong" banner.

**Root cause 1 — extern-app URL drift (CONFIRMED):** the QDO URL in `QARCH_EXTERN_APP_SETUP` is set wrong by post-refresh scripts. Case **26-01068541** ("QDO Web Widgets in PRDA1 are failing on HTTP 404 error", Application Configuration): customer's own description flags `QARCH_EXTERN_APP_SETUP` set incorrectly by Post Refresh Scripts from mock cutover. Fix applied (case feed, verbatim):

```sql
-- run in the QFC/global metadata DB for the env (case ran it in REP_PRDA1UPS_QFC)
UPDATE QARCH_EXTERN_APP_SETUP
SET TARGET_EXE = 'quorum://https://web-prd.myquorumcloud.com/REPUA1QDO/'
WHERE TARGET_MODULE_CD = 'DO'
-- then request a QPEC restart
```

Same signature in **26-01125253** ("PRDA1 - Web DO - Widgets - Something went wrong"): `Resolution__c` = "Updated the DO TARGET_EXE within the extern app setup."

**Root cause 2 — per-user widget security (CONFIRMED):** after the URL fix in 26-01068541, two users still failed on the **New Business widget** only; one was "missing assignment to group **95000** that corresponds to the New Business Widget" (case feed). Fix: add the user to the widget's security group.

**Related:** **23-00912353** "QDO Dashboard Pending DOI widget" (Application Configuration) — same widget-config family, older. **25-01020086** (Owner/DOI Search widget "NO DATA FOUND", Software Defect, Closed-No Response) — widget data defect family, unresolved on case.

**Recipe:**
1. `SELECT TARGET_MODULE_CD, TARGET_EXE FROM QARCH_EXTERN_APP_SETUP WHERE TARGET_MODULE_CD='DO'` — compare URL host/path to the working env.
2. If wrong, UPDATE as above (adjust URL per client/env), QPEC restart.
3. If a single user still fails: check the failing widget's security-group assignment for that user (New Business → group 95000 at REP; group numbers are client-specific — verify).

---

## 5. Cluster B — Post-upgrade Maintenance Group Creation regressions

**B1 — Screen caches old group; WRKSPC corrupts the approved MG (CONFIRMED, code defect).**
Cases **26-01067775** ("UPGRADE - Maintenance Group Creation Error": screen retains all data top+bottom after group creation, "Check All" can't be unchecked, regression vs old behavior where the bottom cleared) and **26-01063731** (per ADO). ADO Bug **1775211** "MEW UPS QDO - Maintenance Group Creation Retrieve Required for New Group Number - 26-01063731" (QuorumSoftware project, Closed, tag `Robot RN 2026.04`):
- Root cause (WI history): "The Maintenance Group Creation screen caches the `DonlDvdGrp` object in the UI controller state… Since the cached value is 1888 (not 0), it skips group creation and tries to run WRKSPC on the existing approved group, which fails" — and **puts the previously-approved MG into status 5-Error**.
- Repro: create MG → do maintenance → preview+approve → return to the same MG Creation tab → do NOT re-retrieve → add new owner/tier → Create Maintenance Group → WRKSPC SPEs, old MG number reused, approved MG flips to ERROR.
- Fixed: Closed, release-noted for **2026.04 (INFERRED from tag `Robot RN 2026.04`)**. Workaround until then: always re-retrieve (or click New) before creating the next group; if an approved MG got flipped to 5-Error, escalate for status correction before re-approving anything.

**B2 — Empty MG undeletable, stuck "Submitted for approval" (CONFIRMED).**
Case **25-01002719** "MEW 2024.04 Upgrade - Unable to delete Maintenance Group": MG with no transactions stuck; delete and revert-status did nothing. `Resolution__c`: "Update the code to enable the deleting of Maintenance Groups that do not have any data." (code fix, fixed-in build INFERRED = a 2024.04 patch).

**B3 — Post-upgrade MG performance (CONFIRMED defects).**
- ADO Bug **1756914** (Quorum project, Closed): "GLE - 2024.10 Upgrade - Slow performance when up to 1.5 million owner records are involved in a maintenance group" — WRKSPC itself ~1.5 min but front-end load +3 min; grid checkbox rendering 6–7 min tracked separately as **#1673532**; total 15–16 min workflow.
- ADO Bug **1668275** (QuorumSoftware, Closed, tags `2024.10 DO; UpsPerfHotfixed`): "GEC - Performance issues after previewing Maintenance Group … takes long time to load while transferring large number of funds (Defect 303)" — post-fix 27 min → ~5 s.
- If a client reports post-upgrade MG slowness on 2024.10-era web builds, check whether these perf hotfixes are consumed before investigating further.

**B4 — Warning noise on approval after upgrade (open/partially fixed).**
Case **26-01067773** "UPGRADE - Warning Messages" (Software Defect): during upgrade testing, MEG/TEG/tax-exempt maintenance approvals emit `No Suspense Release data or no related Subledgers found for OPER_BUS_SEG_CD <X> {DO-CWOWFNDRLS-…}` + `No data posted to GL. {DO-JEPOSTPROC-…}` and the MG completes "with Warnings" (COPY_DVD_W). Multiple MGs listed in the feed (MEG 1→4, TEG 1→2, tax-exempt N→Y — all created PPNs). No resolution recorded on the case — treat as known warning-noise family; verify the MG actually approved and PPNs created, then judge whether funds/GL were genuinely expected to move. Related warning-cleanup lineage: ADO **1622910** (see companion JIB skill §RADOITRW cluster).

---

## 6. Cluster C — Classic→Web parity / field-permission regressions

**Signature:** "We could do X in desktop; the web screen won't let us." Typical after MEW-style 2024.04 web upgrades — logged as Software Defect, fixed per-field in hotfixes.

| Case | Field/behavior | Outcome |
|---|---|---|
| **25-01003450** + follow-up **25-01031226** | `Historical DOI #` editable in classic DO006 on an *approved* DOI; read-only in web DOI Setup (repro'd: MEWU_HD_DEV17 vs MEWU_HD_DEVA1) | Engineering made the field editable for approved DOIs **for users with execute permission on security action `DOI_EDIT_APPROVED_MASTER_DATA`**; delivered March hotfix / "Patch 5"; residual per-user issue fixed in "Patch 8" (both INFERRED builds, case feed) |
| **24-00947442** | Cannot differentiate Owner-level vs DOI-Header note category codes in web | Software Defect (upgrade-project wave; detail on case) |
| **24-00937054** | "Preserve Interest Type does not disable owner interest type" in web | Software Defect, same wave |
| **24-00937044** | Web BA search requires full 10 digits | Software Defect, same wave |
| **24-00943740** | Unit-To-Tract Participation screen shows status "In Interest Transfer" incorrectly | Software Defect, same wave |
| **25-01000684** | Export differs between DOI Search and DOI Setup (MEW 2024.04) | Software Defect |
| **25-01047600** | 2025 upgrade: DOI Worksheet Template broken | Support reproduced, "it's a bug… corrected and included in your next hotfix" (case feed; build INFERRED) |

**Recipe:** reproduce side-by-side in the client's classic (`*_HD_DEV17`) vs web (`*_HD_DEVA1`) envs; if web-only, search ADO for an existing closed bug (this wave is heavily pre-logged) and answer with the fixed-in hotfix; check whether a **security action** gates the behavior (pattern: `DOI_EDIT_APPROVED_MASTER_DATA`) before calling it a defect.

---

## 7. Cluster D — Patch deployment, config drift & missing metadata

**D1 — "Did the patch drop our configuration?" (CONFIRMED isolated, not bulk).**
Case **24-00980918** "Did Patch 71 Drop Configuration Changes" (PNR): after Patch 71, report "PNR Consolidated Exhibit-A" lost its "Template Type" LOV — on the Parameter Definition screen `CodeTableId` was not populated and "Display Control Type" differed vs the un-patched clone. `Resolution__c` (verbatim): the change "was an isolated issue which has been addressed in the salesforce case **24-00981048** where an SQL script has been provided to correct the configurations. There should not be any other dropped/missed/changed configurations in bulk because of the Patch 71." → Answer template for "compare configs pre/post patch" asks: check the specific broken parameter first; bulk config loss from patching is not the observed pattern.

**D2 — Custom report missing after upgrade (CONFIRMED).**
Case **25-01027364** "Upgrade Project - QP088 - Missing Report": custom DO report absent in UBT. `Resolution__c`: "Missing metadata for parameter picklist returns in global metadata tables." Fix = metadata script re-registering the report's parameter picklist metadata.

**D3 — Web-QDO flip configs overwritten by patching (CONFIRMED).**
Case **23-00907112** "Issue Log 139: Patching Activity May Have Overwrote MyQDO Settings": OFR jobs stopped moving monies in testing after a patch. `Resolution__c` (verbatim): "`RUN_WINFORM_CALC_FOR_RSTG` and `DISABLE_CLASSIC_SCREEN`. These two configs are for flipping the system to web QDO. one of them locks down the screens in classic; one of them tells the maintenance group approval process to run OFR based on web configuration. The key value needs to be set to 1 when using myQDO." Also note: the reporter's own metadata authorization was overwritten in the same event — check security alongside configs after patching.

**D4 — Hotfix mis-deployment (CONFIRMED).**
Case **25-01053966** "Possible October hotfix issue - funds only MG query does not work": Retrieve button in funds-only MG transaction did nothing; middle-tier log `Exception has been thrown by the target of invocation`. `Resolution__c`: "The customer redeployed the hotfix, and everything worked as expected." → For dead-button + reflection-exception symptoms right after a hotfix, suspect a partial deployment before debugging product code.

**D5 — Hotfix request/delivery cases (process, Application Configuration).**
**25-01045796** "QDO: October 2025 Hotfix Request for 2023.04 Version" (APA): patch had to be **repackaged and redeployed because the client did not promote the previous patch to PRD**; delivered to FTP. Sibling **25-01000688** (March 2025 hotfix request, 2023.04). **24-00940420** "January 2024 hotfix deployment". These close as Application Configuration; deliverable = scheduling/packaging, not investigation.

---

## 8. Cluster E — Build-UAT regressions (2023.04-style upgrade waves)

Upgrade-project UAT surfaces build defects titled `Build 2023.04 - UAT - …` / `Upgrade Project: QDO - …`. Highest-value resolved examples:

| Case | Error signature (verbatim where quoted) | Root cause / fix |
|---|---|---|
| **23-00927336** | `Message Code: TEMP.DOIMaintIntTransferController.DoAction.345 … Table DtrnOwnrFundRls Errors: Row(-1): Column 'OrigBusUnitCode' does not allow DBNull.Value.` on Modify/Modify-with-funds | `Resolution__c`: "Found a copy/paste error that caused the wrong column of data to be used when creating the rows to save to the database. This was part of an enhancement done in Sept 2022" — code fix |
| **23-00933603** | MG preview (100% backdated transfer with funds) fails: `The DELETE statement conflicted with the REFERENCE constraint "FK_DONL_DVD_MKT_EXMPT__DONL_DVD_DO_DETAIL"` (SQLState 23000, NativeError 547) | `Resolution__c`: "Provided script to truncate 2 tables that are no longer used by this version of QDO." (Application Configuration) |
| **24-00949299** | Mass transfer of one owner across 1,049 JIB DOIs / multiple effective-date ranges errors on Preview: `Old owner not in DO …` + `The QIntTransfer process has failed for group {0}` + `Call to C++ Batch Process Step Class Name QPSINTTRANSFER failed Execute` + `Continue Process On Failed Execute Is FALSE for DOINTXFRWB` (desktop workspace path worked) | `Resolution__c`: "Modified the chunking logic for mass transfer. After Chunking, remaining records will get saved immediately in subsequent transaction." — code fix, go-live blocker for MEW 2023.04 |
| **23-00933599** | QRA Funds Release errors when releasing Revenue Interface Lock with pending MGs | Application Configuration (upgrade wave; sequence releases vs pending MGs) |
| **23-00933550** | "Not Authorized to access security object" errors while navigating post-upgrade | Application Configuration — security-object gaps after upgrade (see S3 security cluster) |
| **24-00952414** | Build 2023.04 UAT: incorrect PD41 PPNs generated | Software Defect (PPN family, see S1) |

**Recipe:** for any `Build <ver> - UAT` regression, first `search_workitem` for the error string / case number — these waves are almost always already logged and often already Closed with a fix in a later patch of the same train.

---

## 9. Cluster F — Environment / infra availability after go-live

**F1 — Missing ODBC driver breaks JE100/OFR feed (CONFIRMED).**
Case **25-01053856** "2025 Upgrade Live - funds did not automatically populate" (MGs 7954 transfer / 7955 pay-code change): `Resolution__c` (verbatim): "The ODBC driver was installed on 11/10/2025. This was preventing JE100 records from coming in correctly. Then, a script was run to update the JE100 OFR records to an 'error' status for a CNR user to then Rerun in JE100." → New-infrastructure go-lives: verify DB drivers on app/middle-tier servers when an interface silently produces nothing; recover stuck rows by scripting them to error status and rerunning in JE100.

**F2 — Merge PRD metadata into next patch** (**26-01084575**, Application Configuration) and **Datayank PRD→UAT data to avoid wiping a patch under test** (**26-01068062**, see companion Imports skill) — environment-management requests that ride the patch pipeline; deliverable is scripts/packaging via Managed Services (ADO **1778563** pattern).

---

## 10. Known ADO Items

| WI | Type/State | Title (verbatim) | Notes |
|---|---|---|---|
| **1775211** | Bug, Closed | MEW UPS QDO - Maintenance Group Creation Retrieve Required for New Group Number - 26-01063731 | `DonlDvdGrp` UI cache → WRKSPC on approved MG → 5-Error; RN tag 2026.04 (fixed-in INFERRED) |
| **1756914** | Bug, Closed (Quorum project) | GLE - 2024.10 Upgrade - Slow performance when up to 1.5 million owner records are involved in a maintenance group | front-end load + checkbox grid (#1673532) |
| **1668275** | Bug, Closed | GEC - Performance issues after previewing Maintenance Group… (Defect 303) | tag `UpsPerfHotfixed`, 2024.10 DO |
| **1622910** | Bug, Closed | 23-00918228--No default market rep found warning message on converted dummy DOIs for Revenue Suspense | warning-noise cleanup; RN 2026.04 tag; market rep = code table 29100 |
| **1659136** | Requirement, Proposed | QDO Web - Review REQUIRE_INQUIRY_DATE logic | config: 0 = blank inquiry date (core default), 1 = defaults to first of month; drives DOI Maintenance retrieve behavior |
| **1778563** | Bug, Resolved (QuorumServices\Managed Services) | 26-01068062--Datayank new PRD Business Associates for insert into UAT | scripts for PRD→UAT data insert without refresh |

---

## 11. Diagnostic SQL

All queries are verification templates — **verify table/column names against the client DB first**; run SELECT before any UPDATE, inside a transaction.

```sql
-- A. Widget/extern-app URL check (CONFIRMED table, from 26-01068541)
SELECT TARGET_MODULE_CD, TARGET_EXE
FROM QARCH_EXTERN_APP_SETUP
WHERE TARGET_MODULE_CD = 'DO';

-- B. Verbatim fix applied in 26-01068541 (adjust URL per client/env; QPEC restart after)
UPDATE QARCH_EXTERN_APP_SETUP
SET TARGET_EXE = 'quorum://https://web-prd.myquorumcloud.com/REPUA1QDO/'
WHERE TARGET_MODULE_CD = 'DO';

-- C. Web-QDO flip configs after patching (keys CONFIRMED in 23-00907112; table = client
--    global config store, name varies — locate via metadata server)  [NOT YET RUN]
--    Expect KEY_VALUE = 1 for both when running myQDO Web:
--    RUN_WINFORM_CALC_FOR_RSTG, DISABLE_CLASSIC_SCREEN
```

---

## 12. Expected-Behavior FAQ

- **"Maintenance Group Creation works differently after the upgrade — it jumps straight into the wizard."** Intentional. In 2024.04 the workflow was changed to remove the MG-screen → Transactions tab → New Transaction clicks and take the user straight to the maintenance wizard, based on usage metrics and customer feedback. Documented in the 2024.04 release notes / executive summary at `community.quorumsoftware.com/s/release-notes`. (Case **25-01057971** feed, closed as confirmed.)
- **"Will you compare every config before/after the patch?"** The observed failure mode is *isolated* parameter metadata (one report LOV), not bulk config loss; fix is a targeted script (24-00980918 → 24-00981048). Offer the targeted check first.
- **"The fix you delivered for our current version — where is it after we upgraded?"** Fixes are delivered per version train; a fix may ship in your *upgrade target* release instead of a backport when an upgrade is active (25-01027179: remaining fix rode 2025.04; 24-00949849 "March Hotfix & Release Notes" family). Always confirm which train the client runs before promising a hotfix.

---

## 13. Escalation

- **Widget/URL & security-group fixes** (Cluster A) — Managed Services / CloudOps can apply; needs QPEC restart window.
- **Code defects** (Clusters B, C, E) — log/route to ADO. QDO engineering areas observed: `QuorumSoftware\Engineering\Revenue\Committed Backlog`, `QuorumSoftware\Engineering\Maintenance\Upstream\Professional Services\Revenue`, `…\Customer Service\Revenue`; some newer bugs in project `Quorum` (`Quorum\North America\Upstream\myQ Accounting RnD`). Title convention: client prefix + SF case number.
- **Hotfix packaging/deployment** (Cluster D5) — coordinate with the delivery owner; confirm previous patch was promoted to PRD or expect repackage (25-01045796).
- Approved MG flipped to 5-Error by B1: **stop the client from re-approving**; escalate for status correction script before further maintenance on that group.

---

*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
