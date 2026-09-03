# SKILL: QDO Upgrade / Patch / Hotfix Regressions & Environment Availability

**Version:** 1.0 | **Created:** 2026-09-02 | **Product:** My Quorum Division Order (QDO)
**Built by Auto-Bot — the L4 issue solver by Aditya Bhagat.**
**Scope:** Everything that breaks *because a build moved* — upgrade-UAT waves (Build 2023.04 / MEW 2024.04 / 2025 Upgrade / 2025.04), monthly Upstream patches and hotfixes (Patch 11/12, Patch 71, "October '25 2023.04 Hotfix"), post-refresh/mock-cutover environment drift (PRD A1 / UAT / DEVA1), classic-vs-web parity regressions, and the patch/hotfix request-and-deploy workflow itself. Companion skills: S1 `SKILL_QDO_Division_Orders.md` (feature mechanics), S2 `SKILL_QDO_Transfers_SuspendRelease.md` (transfer internals), S3 `SKILL_QDO_Platform_Integration.md` (BA web screens, security), S4 `SKILL_ADO_QDO_DivisionOrder_Transfers.md` (ADO defect reference).

> **Evidence base:** all-history mining 2026-09-02, coverage-plan group G4 (~62 actionable). SOQL sample: 70 closed `upgrade/patch/hotfix/deploy` cases + 25 `MEW/2023.04/2025.04/404/widget/environment` cases, Root_Cause__c IN (Software Defect, Application Configuration, ChangeConfig), newest-first; 16 deep-read (Description + Resolution__c); ADO confirmations via `search_workitem`/`wit_work_item` (org QuorumSoftware). Every claim cites a verbatim SF case number or ADO work item ID. Fixed-in builds are **INFERRED** from ADO history unless the WI states the merge explicitly.
> **Client-prefix vocabulary seen in this cluster:** MEW (Mewbourne), GEC/Gulfport, TEP, PNR, APA, MRO, CNR, SPR — subjects routinely carry `<CLIENT> <version> Upgrade - ...`.

---

## 1. Quick Triage Table

| Symptom | Likely cause | Go to |
|---|---|---|
| QDO **web widgets fail with HTTP 404** after a refresh / mock cutover (PRD A1) | QDO URL in `QARCH_EXTERN_APP_SETUP` set wrong by Post-Refresh Scripts | §4-A1 (26-01068541) |
| "The **patch dropped our configuration**" | Almost always an *isolated* metadata regression, not a bulk drop — find the one screen/report affected | §4-A2 (24-00980918 / 24-00981048) |
| Report parameter **LOV missing** after applying a patch (e.g. Template Type on a Consolidated Exhibit-A) | Patch overwrote report-parameter metadata (Text vs LOV) | §4-A2 (24-00981048 — SQL metadata script) |
| Button does nothing + middle-tier log `Exception has been thrown by the target of invocation` after a hotfix | **Bad/partial hotfix deployment** — redeploy the hotfix before debugging | §4-A3 (25-01053966) |
| Client PRD metadata missing from next patch | PRD metadata never merged to the metadata repo — request a metadata compare/merge | §4-A4 (26-01084575) |
| Field editable in **classic but read-only in web** (e.g. Historical DOI #) | Classic/web parity gap: web still checks a retired security object | §5-B1 (25-01031226, ADO #1743552/#1713922) |
| **Cannot save a BA in web** after upgrade (zip/state/precision) | Web BA screen forces US zip/state format; separate decimal-precision save defect | §5-B2 (24-00987114; ADO #1614286) |
| **Cannot delete a pending Maintenance Group** that has no data (post-2024.04) | Web defect — delete blocked for empty MGs | §6-C1 (25-01002719, ADO #1715622) |
| MG Creation screen **retains data / reuses the previous MG number** | Regression: new group requires re-Retrieve; screen doesn't clear | §6-C2 (26-01067775, 25-01057971; ADO #1775211) |
| Upgrade-UAT transfer w/ funds release: `Column 'OrigBusUnitCode' does not allow DBNull.Value` | Copy/paste defect in a Sept-2022 enhancement (wrong column mapped) | §7-D1 (23-00927336) |
| Preview fails `DELETE ... conflicted with ... FK_DONL_DVD_MKT_EXMPT__DONL_DVD_DO_DETAIL` | Obsolete tables left behind by the upgrade — truncate them | §7-D2 (23-00933603) |
| Mass transfer across multiple effective-date ranges errors on Preview (`Old owner not in DO`) | Chunking-logic defect on large (1,000+ DOI) transfers | §7-D3 (ADO #1651746) |
| Excel **export of DOI Search ≠ DOI Setup** | Export not filtered by inquiry date on `DonlDoDetail` | §7-D4 (25-01000684, ADO #1711287) |
| Bearer-group Bulk Edit fails w/ `PK_DONL_DVD_BEARER_GRP_DETAIL` violation when date breaks exist | Bulk edit tries add/delete instead of update | §7-D5 (24-00965362, ADO #1687869) |
| `Not Authorized to access security object` on many screens right after upgrade | New-version security objects not granted; validation review needed | §7-D6 (23-00933550/23-00933549; U_DO_MAINT ADO #264870) |
| "Please deliver hotfix X for version Y" (no defect) | **Hotfix-logistics case** — track request → build → deploy; not an investigation | §8-E |

---

## 2. Upgrade landscape & concepts

- **Release trains:** on-prem/hosted QDO clients sit on year-versions (`2021.04`, `2022.04`, `2023.04`, `2024.04`, `2024.10`, `2025.04`, `2026.04`). Fixes land in `develop` + the *hotfix branches* of supported versions (pattern confirmed in ADO #1713922: "merged to develop and hotfix branches of release versions 2023.04, 2024.04 and 2024.10").
- **Patches vs hotfixes:** monthly **Upstream Patch N** bundles (e.g. "Upstream Patch 11 & 12", "Patch 71") and named **hotfixes** ("October '25 2023.04 Hotfix", "March 2025 Hotfix for 2023.04" — 25-01000688). A patch can fail Quorum testing and be superseded (Patch 11 failed → go straight to Patch 12, 26-01068283).
- **Environments:** `PRD A1` (production), `UAT` / `UAT2`, `DEVA1` (e.g. `MEWU_HD_DEVA1`), plus Citrix and QCloud fronts. Mock cutovers run **Post Refresh Scripts** that rewrite environment-specific config — a classic source of post-refresh breakage (§4-A1).
- **Upgrade-UAT waves:** each client upgrade generates a burst of `"<CLIENT> <version> Upgrade - ..."` / `"Build 2023.04 - UAT - ..."` cases. Most are (a) web-vs-classic parity gaps, (b) config/security not carried forward, (c) genuine new-version defects. Classify each individually — do not blanket-blame the upgrade.
- **Classic vs Web:** the recurring root-cause *shape* in this cluster is "behavior changed in classic, matching change never made in web" (25-01031226) or "web screen enforces stricter formats than classic" (24-00987114).

## 3. Decision Tree

```
Case mentions upgrade/patch/hotfix/refresh?
├─ Environment-wide outage or 404s right after refresh/cutover?
│    └─ YES → §4-A1 post-refresh config drift (QARCH_EXTERN_APP_SETUP first)
├─ Worked before patch, broken after, ONE screen/report?
│    ├─ Metadata/LOV/parameter → §4-A2 patch metadata regression (script fix)
│    └─ Button dead + MT "target of invocation" → §4-A3 redeploy the hotfix
├─ Web behaves differently from classic on same build?
│    └─ §5 parity regression (check config vs security-object pairs)
├─ Maintenance-Group lifecycle broken post-upgrade?
│    └─ §6 (delete-empty-MG, retained data / reused MG number)
├─ Upgrade-UAT functional error with a hard DB message?
│    └─ §7 known Build-2023.04/2024.04 defect family — match the error string
└─ No defect at all — client asking for a patch/hotfix delivery?
     └─ §8 logistics workflow (Root_Cause__c = Application Configuration)
```

---

## 4. Cluster A — Post-refresh / post-deploy environment drift (G2 config)

**A1 — Web widgets 404 after mock cutover.** `26-01068541` "QDO Web Widgets in PRDA1 are failing on HTTP 404 error" (App Config, Closed 2026-03-06). Case description (verbatim): *"It looks like the QDO URL in QARCH_EXTERN_APP_SETUP may have been incorrectly set by the Post Refresh Scripts from mock cutover."*
**Recipe:** verify the QDO web-app URL row in **`QARCH_EXTERN_APP_SETUP`** against a working environment; correct the URL; recycle/refresh cache. Whenever an environment was just refreshed, audit *all* Post-Refresh-Script outputs (URLs, endpoints, interface configs) before debugging application code.

**A2 — "Patch dropped configuration".** `24-00981048` (App Config): after Patch 71 on PNR PRD, the Template Type parameter LOV was missing on the PNR Consolidated Exhibit-A report. Resolution (verbatim): *"SQL script provided to modify the metadata in order to change the Template type parameter from a Text field to a drop-down (LOV) field."* Companion case `24-00980918` "Did Patch 71 Drop Configuration Changes" concluded (verbatim): *"…an isolated issue… There should not be any other dropped/missed/changed configurations in bulk because of the Patch 71."*
**Recipe:** scope the complaint to the specific screen/report; diff its metadata vs pre-patch backup; script the single correction. Reassure the client bulk config is intact unless evidence says otherwise.

**A3 — Dead button after hotfix ⇒ redeploy first.** `25-01053966` "Possible October hotfix issue - funds only MG query does not work" (App Config): Retrieve button in a funds-only MG did nothing; middle-tier log showed `Exception has been thrown by the target of invocation`. Resolution (verbatim): *"The customer redeployed the hotfix, and everything worked as expected."*
**Recipe:** when a *just-hotfixed* environment throws reflection/invocation errors, suspect a partial deployment; redeploy the hotfix before any code investigation.

**A4 — PRD metadata not merged into the patch stream.** `26-01084575` "Merge PRD metadata into next patch" (App Config): TEP PRD metadata was never merged to the metadata repo; Services performed a metadata compare of PRD vs repo and merged what had to be preserved for Patch 12.
**Recipe:** if a client hand-configured PRD, schedule a **metadata compare + merge** before each patch so the patch doesn't roll their config back.

## 5. Cluster B — Classic-vs-Web parity regressions

**B1 — Historical DOI # not editable in web.** `25-01003450` → follow-up `25-01031226` (both Software Defect; ADO **#1713922** and **#1743552**, both Closed). Root cause per SF resolution (verbatim, condensed): classic was changed to drive editability *only* from config **`EDIT_APPROVED_MASTER_DATA`**, dropping the security object **`DOI_EDIT_APPROVED_MASTER_DATA`** — *"While this change was made in classic application, the matching change was not made in the web application."* Fix: web now keys `Historical DOI #` and `Tier Description` read-only/editable purely off `EDIT_APPROVED_MASTER_DATA`. ADO #1713922 history: *"All the commits are merged to develop and hotfix branches of release versions 2023.04, 2024.04 and 2024.10"* (fixed-in those hotfix streams — CONFIRMED from WI history; specific build numbers INFERRED).
**Diagnostic pattern:** any "certain users can edit in classic but not web" → list the config + security-object *pair* controlling the field; check whether one side of the pair was retired.

**B2 — BA save failures in web after upgrade.** `24-00987114` "MEW 2024.04 Upgrade - Zip code and state code issue when trying to save BA in the web" (App Config): web BA screen (1) forces US zip format for non-US/CA countries, (2) rejects alpha zips, (3) forces a State code even where the country has none. Related earlier defect ADO **#1614286** "MEW - 2023.04 - Cannot Update a BA in the Web screen" (Closed): fixed by *"PR 88123: Correct Precision issue during BA save"*, shipped as **Quorum.ESUITE.Web → 17.30.3** on the 2023.04 hotfix branch. Deep zip/state/1099 mechanics live in S3 (BA master-data web screens) — use this cluster only for the *upgrade-regression* framing.

**B3 — Web grid cosmetics/usability regressions.** ADO **#1693900** "24-00985406 - MEW 2024.04 Upgrade - Picklists that contain a checkbox with is true/is false filter are causing unnecessarily tall filter bars" (Closed) — a Kendo-grid regression touching a documented list of QDO web picklists (Property, DOI Setup, Bearer Group, DOI Copy, UTT, DOI Search, Maintenance Group, BA Contact). Merge-back to 2024.04/2024.10/2025.04 was discussed in the WI (**INFERRED**, not confirmed). Cosmetic — classify Software Defect, low priority, cite the WI.

## 6. Cluster C — Maintenance-Group lifecycle regressions after upgrade

**C1 — Cannot delete an empty pending MG.** `25-01002719` (Software Defect; ADO **#1715622** "Unable to delete a Pending Maintenance Group that does not have any data", Closed, tag `not 2026.04 Ups`). SF resolution: *"Update the code to enable the deleting of Maintenance Groups that do not have any data."*
**C2 — MG Creation screen retains data / reuses MG number.** Cases `26-01067775` "UPGRADE- Maintenance Group Creation Error" (screen retains top+bottom data, Check-All can't be unchecked, users must exit to reset) and `25-01057971` "2025 Upgrade - Maintenance Group Creation Test vs Live" (both Software Defect). ADO **#1775211** "MEW UPS QDO - Maintenance Group Creation Retrieve Required for New Group Number - 26-01063731" (Closed, iteration 26.04, Found-In set to 2024.04; also reported by Gulfport in 2025.04 upgrade testing): reusing the tab without re-Retrieve keeps the **previous approved MG number** instead of generating a new one — wrong group gets modified. Fixed-in 2026.04 (Robot RN 2026.04 tag — **INFERRED**).
**Recipe:** interim workaround — always exit/reopen MG Creation (or re-Retrieve) between consecutive groups; verify the MG number changed before adding transactions.
**C3 — Funds-only MG Retrieve dead** → that is §4-A3 (redeploy hotfix) — check deployment before logging a defect.

## 7. Cluster D — Upgrade-UAT defect wave (Build 2023.04 / 2024.04 families)

**D1 — `OrigBusUnitCode` DBNull on Transfer/Modify with Funds Release.** `23-00927336` (Software Defect). Error (verbatim from subject): *"Table DtrnOwnrFundRls Errors: Row(-1): Column 'OrigBusUnitCode' does not allow DBNull.Value."* Resolution (verbatim): *"Found a copy/paste error that caused the wrong column of data to be used when creating the rows to save to the database. This was part of an enhancement done in Sept 2022."* Code fix — escalate with the error string; no data workaround documented.

**D2 — FK_DONL_DVD_MKT_EXMPT delete-constraint on Preview DOI.** `23-00933603` (App Config). Resolution (verbatim): *"Provided script to truncate 2 tables that are no longer used by this version of QDO."* The MEG-remediation lineage (see S2 §7) obsoleted individual market-exemption tables; leftover rows block workspace deletes. Fix recipe: truncate the obsolete `DONL_DVD_MKT_EXMPT`-family tables per Quorum script (verify table names on the client build first).

**D3 — Mass transfer across multiple effective-date ranges errors on Preview.** SF `24-00949299` (Software Defect, Closed); ADO **#1651746** "MEW 2023.04 - Mass transfer on multiple effective date ranges errors on Preview" (Closed, tag `2024.10 DO`): 1,049-DOI mass JIB transfer failed with `Old owner not in DO` / *"Could not complete transfer for this transaction"*; desktop workspace succeeded. Fix involved transaction **chunking logic**; a walkthrough doc is attached to the WI. Fixed-in 2024.10 stream (tag — **INFERRED**). Workaround: run very large mass transfers via classic/desktop workspace, or split by effective-date range.

**D4 — DOI Search export ≠ DOI Setup export.** `25-01000684` (Software Defect; ADO **#1711287**, Closed, tag SDP2504). Resolution (verbatim): *"Code change implemented to filter the DonlDoDetail based on inquiry date for excel export."* Merged to 2024.04 and 2024.10 hotfix branches (WI history — CONFIRMED statement, builds INFERRED).

**D5 — Bearer-group Bulk Edit with date breaks → PK violation.** `24-00965362` (Software Defect; ADO **#1687869**, Closed). Error (verbatim from WI): *"Violation of PRIMARY KEY constraint 'PK_DONL_DVD_BEARER_GRP_DETAIL'"* — bulk replace of bearer decimals attempts add/delete instead of update when the bearer group has date breaks. Fix scheduled under the **QDO Web Adoption** feature for 2025.10 (WI history — **INFERRED**). Workaround: maintain date-broken bearer groups row-by-row, not via Bulk Edit.

**D6 — Security objects missing after upgrade.** `23-00933550` "Users receiving Not Authorized to access security object errors when navigating screens" + companion `23-00933549` "Review validations QARCH_CTRL_OBJECT_USE" (both App Config): new-version screens reference security objects the client's groups never got. ADO **#264870** "Add the U_DO_MAINT Security Object to CORE_REL" (Closed) documents the same shape: creating INF DOI types looks for `U_DO_MAINT`. Fix recipe: capture the object name from the error, grant it to the affected security groups (S3 owns the deep security cluster), and review `QARCH_CTRL_OBJECT_USE` for the build.

**D7 — Other one-offs seen in the wave (anchors only):** `24-00952414` incorrect PD41 PPNs in 2023.04 UAT (Software Defect — PPN family, S1); `23-00915246` 100% recoup transfer wrong distribution (S2 owns recoupment); `23-00925267` changing BA sub on DOI Maintenance also changed owner number; `23-00928518` Production/Accounting-month filters returning nothing; `23-00933883` External Funds Transfer missing from dashboard; `23-00933599` QRA funds-release errors when releasing the Revenue Interface Lock with pending MGs; `24-00947442` owner-level vs DOI-header note category codes indistinguishable; `24-00943740` UTT participation stuck "In Interest Transfer"; `24-00937054` Preserve Interest Type not disabling owner interest type; `24-00937044` BA search requires full 10 digits; `25-01047600` DOI Worksheet template; `25-01041826` adding SSN removes 1099 indicator (S3). Route these to the owning skill; cite the case number.

## 8. Cluster E — Patch / hotfix logistics workflow (no defect)

Recognize the shape: the case *is the delivery vehicle*, Root_Cause__c is usually Application Configuration, and the "resolution" is a deploy note.
- `25-01000688` "QDO: March 2025 Hotfix Request for 2023.04 Version" → resolution: *"deployed to PRD May 2025"*.
- `25-01045796` "QDO: October 2025 Hotfix Request for 2023.04 Version" → resolution: "October 2023.04 HF".
- `26-01068283` "Upstream Patch 11 & 12 - Perform targetted testing & provide Testing Support" → Patches 9 & 10 promoted to PRD; *"Patch 11 failed Quorum testing so we will proceed with a Patch 12"*; resolution "Patch 12 deployed".
- `24-00940420` "January 2024 hotfix deployment"; historical run: 22-00516787/89, 22-00641213, 22-00672534/47, 22-00676456/64/78 (2021-22 monthly patch/hotfix tickets).
**Recipe:** confirm target version + environment order (UAT → PRD), attach the release-note review, track deploy confirmation, close. No investigation gates needed — classify early and don't burn tokens.

---

## 9. Known ADO Items

| ADO WI | Title (condensed) | State | SF anchor | Fixed-in |
|---|---|---|---|---|
| #1713922 | MEW 2024.04 — Unable to update Historical DOI field | Closed | 25-01003450 | 2023.04/2024.04/2024.10 hotfix branches (WI history) |
| #1743552 | MEW 2024.04 — classic/web Historical DOI # discrepancy | Closed | 25-01031226 | "MEW's next hotfix" (INFERRED) |
| #1715622 | Unable to delete Pending MG with no data | Closed | 25-01002719 | tag `not 2026.04 Ups` (INFERRED) |
| #1711287 | Export diff DOI Search vs DOI Setup | Closed | 25-01000684 | 2024.04 + 2024.10 hotfix branches (WI history) |
| #1687869 | Bearer-group Bulk Edit date breaks → PK violation | Closed | 24-00965362 | QDO Web Adoption 2025.10 (INFERRED) |
| #1775211 | MG Creation — Retrieve required for new group number | Closed | 26-01063731 (family: 26-01067775, 25-01057971) | 2026.04 (Robot RN tag, INFERRED) |
| #1614286 | MEW 2023.04 — cannot update BA in web (precision on save) | Closed | (MEW upgrade wave) | PR 88123, Quorum.ESUITE.Web 17.30.3 → 2023.04 HF branch |
| #1693900 | Tall picklist filter bars (Kendo) after 2024.04 | Closed | 24-00985406 | merge-back discussed (INFERRED) |
| #1651746 | Mass transfer, multiple effective-date ranges errors on Preview | Closed | 24-00949299 | 2024.10 (tag, INFERRED) |
| #264870 | Add U_DO_MAINT security object to CORE_REL | Closed | — | script-review resolution |
| #1732619 | DOINTXWRK batch fails (endpoint) — referenced by #1723387 | (see WI) | — | see JIB skill §E |

## 10. Diagnostic SQL (verification queries — label `NOT YET RUN` if no metadata connection)

```sql
-- A1: post-refresh URL drift — QDO web-app endpoints
SELECT * FROM QARCH_EXTERN_APP_SETUP;            -- compare URL columns vs a known-good env

-- B1: parity pair for Historical DOI # editability
SELECT * FROM <global_config_table> WHERE CONFIG_NM = 'EDIT_APPROVED_MASTER_DATA';  -- verify config table name on client build
-- and check whether security object DOI_EDIT_APPROVED_MASTER_DATA is still granted/referenced

-- C1/C2: pending MGs with no detail rows (delete-blocked candidates)
SELECT h.GRP_NO, h.TRANS_DESCR
FROM DONL_DVD_DO_HDR h                            -- verify exact workspace header table on build
LEFT JOIN DONL_DVD_DO_DETAIL d ON d.GRP_NO = h.GRP_NO
WHERE d.GRP_NO IS NULL;

-- D5: pre-check for bearer bulk edit PK collisions (date-broken groups)
SELECT BEARER_GRP_NO, COUNT(*) 
FROM DONL_DVD_BEARER_GRP_DETAIL
GROUP BY BEARER_GRP_NO HAVING COUNT(*) > 1;       -- inspect for duplicate natural keys before bulk ops
```
*(Table names are from case/ADO text — verify against the client DB before scripting; run SELECTs first.)*

## 11. Expected-Behavior / FAQ

- **"The upgrade broke everything."** Each upgrade-UAT case is triaged individually; the historical split of this cluster is roughly half config-not-carried-forward (App Config) and half genuine defects — see §7-D7 for how varied the wave is.
- **"Did the patch wipe our config?"** Precedent says no — Patch 71 analysis found exactly one isolated metadata regression (24-00980918). Ask for the *specific* broken screen.
- **Warnings/slowness right after go-live** (`25-01054147` "Affiliated Flag Warning & System running very slow", App Config; `25-01001965` QCloud rollout performance, App Config) are usually environment sizing/config tuning, not code — route to environment/config review before G5.
- **Hotfix-request cases** (§8) are not defects: classify fast, don't investigate.
- **After any environment refresh**, treat Post-Refresh Scripts as a suspect for every "X stopped working in <env>" report (26-01068541 precedent).

## 12. Escalation

- Code-change candidates (G5): parity gaps (§5), MG lifecycle regressions (§6), D1/D3/D4/D5 — area paths seen on real QDO bugs: `QuorumSoftware\Engineering\Revenue\Committed Backlog`, `...\Engineering\Maintenance\Upstream\Professional Services\Revenue`, `...\Customer Service\Revenue`. Title convention: `<CLIENT> <version> Upgrade - <symptom> - <SF case #>`.
- Include in the handoff: build/version (found-in), environment (UAT/PRD A1/DEVA1), classic-vs-web behavior matrix, exact error string, and whether a redeploy (§4-A3) was already tried.
- Metadata merge/compare work (§4-A4) routes to Services (Managed Services), not Engineering.

*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
