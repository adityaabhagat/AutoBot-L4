# SKILL: QDO Platform & Integration Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QDO (My Quorum Division Order — upstream oil-&-gas ownership / division-order accounting, part of the myQuorum / Upstream On-Demand suite)
**Scope:** The **platform & integration** surface of QDO — everything *around* the core division-order math: **Business Associate (BA) master-data web screens** (zip/state/1099/SSN/Tax-ID/notes/attachments/approvals), **eSuite Web vs Classic** screen/config behavior, **SAP ⇄ QDO integration** (PUBBA, QRA Revenue/Royalty webservice, vendor→BA sync, MG/JIB netting interfaces), **QLS ⇄ QDO lease interface** (UPSLSINTFC), **security groups / security objects / Citrix / OKTA / session**, **QQM reporting access**, and **DOI Maintenance / Transfer / Maintenance-Group (Design Studio) screen defects** that surface as platform errors.
**Companion skills (separate):** the DOI math itself — decimal-interest calc, suspense/suspend-release, owner funds release, conveyance, ownership-transfer *funds* — lives in the QDO core/DOI skill; this skill *consumes* BA master data and *moves* DOI data across SAP/QLS, so when a number is wrong fix the DOI/owner setup first; when **a screen won't save, an interface won't run, or a user can't get in**, you are in the right place.

> **Evidence base:** 421 closed QDO "Platform/Integration"-bucket cases (Case_Category IN eSuite / Integration / Design Studio / Security / QQM / Other / All). Root-cause split: **(blank) 122, Customer Cancelled 56, Software Defect 51, Customer Error 48, Application Configuration 48, Training 31**, User-Admin 25, HW/SW Change 24, Business Change 20, Platform 15, Other 15, rest small. This skill mines the **99 actionable** cases (Software Defect 51 + Application Configuration 48; "ChangeConfig" is not used on this product = 0) for fix recipes, plus ~79 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case and/or ADO work item observed during mining.

> **Platform note (READ FIRST):** QDO On-Demand runs on **SQL Server**, schema **`ESUITE_QFC`** (core/shared) and **`ESUITE_Q<CLIENT>`** (per-client, e.g. `ESUITE_QFC` + the client's own). This is different from the Oracle `ESUITE_Q*` schemas in TIPS/QPTM. The recurring fix on this product is **"add the missing security object / security group / config record via a SQL script to `ESUITE_QFC`"** — not a code change. Treat that as the default hypothesis for "screen errors / can't save / button missing / process won't launch."

---

## TABLE OF CONTENTS
1. [Quick Triage Table](#1-quick-triage-table)
2. [Architecture & Concepts](#2-architecture--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — BA web screen: Zip/State/Country masking & validation (HIGH FREQUENCY)](#4-cluster-a--ba-web-screen-zipstatecountry)
5. [Cluster B — BA 1099 / SSN / Tax-ID indicator & security](#5-cluster-b--ba-1099--ssn--tax-id)
6. [Cluster C — BA conversion gaps: notes, attachments, contact-type, names (Classic→Web upgrade)](#6-cluster-c--ba-conversion-gaps)
7. [Cluster D — Security objects / groups / Citrix / OKTA / session (the "add-the-object" cluster)](#7-cluster-d--security-objects--groups--citrix--okta--session)
8. [Cluster E — SAP ⇄ QDO integration (PUBBA, QRA webservice, vendor→BA, MG/JIB)](#8-cluster-e--sap--qdo-integration)
9. [Cluster F — QLS ⇄ QDO lease interface (UPSLSINTFC)](#9-cluster-f--qls--qdo-lease-interface-upslsintfc)
10. [Cluster G — DOI Maintenance / Transfer / Maintenance-Group screen defects (Design Studio)](#10-cluster-g--doi-maintenance--transfer--maintenance-group)
11. [Cluster H — Owner Lease Xref import / bulk-edit](#11-cluster-h--owner-lease-xref-import--bulk-edit)
12. [Cluster I — QQM reporting access / report visibility](#12-cluster-i--qqm-reporting-access)
13. [Known ADO Items](#13-known-ado-items)
14. [Diagnostic SQL](#14-diagnostic-sql)
15. [Expected-Behavior / User-Education FAQ](#15-expected-behavior--user-education-faq)
16. [Key Code, Processes & Repos](#16-key-code-processes--repos)
17. [Escalation Guidance](#17-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| "Zip code error when saving a BA" / "BA won't save, zip code format" / "4-digit zip suffix doesn't show in address" | **Zip-code masking** config + bad converted zip data (4-digit `+4` suffix mis-stored); validation fires even when not mandatory | §4 — run the **zip-code cleanup script**; add/adjust the **zip-code mask**; confirm masking global-config |
| "No States listed on BA Address tab" / "States blank" | Code Table 30000 (country) config — wrong country not hidden so state list won't populate | §4 — set **Hidden Ind = checked on the "USA" country** record in Code Table 30000 (25-01043401) |
| "Adding SSN/Tax-ID won't let me save a new BA" / "no TIN field" | **BA Tax-ID security objects** missing from the BA Data Entry security group | §5 — add BA Tax-ID update privs to the group (script) (25-01042111) |
| "Adding SSN removes the 1099 indicator" / "BA update auto-unchecks 1099" / "1099 indicator changing in BA005" | **Software defect** in BA web 1099 handling **and/or** the 1099 flag in the **QRA address table is out of sync with `SCTRL_BA_ENTITY`** | §5 — defect (patch) + sync script (25-01041826/25-01042098; ADO #1711218, #1775732/#1771382) |
| "Existing BA notes / attachments / contact-type didn't convert to Web (UAT)" | **Classic→Web conversion gap** — data still in classic table, or note categories/contact-type not seeded | §6 — run the **migration / seed scripts** (BA docs, note categories, contact type) |
| "Can't create Property after creating a Cost Center" / "Property screen didn't auto-open" | Missing access to the **`ORGCOSTGEN`** process for that group | §7 — run security update script to grant `ORGCOSTGEN` (25-01042097) |
| "No Approval button on BA" / "Security error creating a Cost Center" | Missing BA-Approval config / missing `ORG/BTYP/QRA` security object | §7 — deploy BA-Approval config scripts / add the security object to the group (25-01042184, 25-01048054) |
| "`SecurityId 'X' is not registered with QApplicationController`" / web access error / "can't access Citrix" | Missing **security object / global-config record**, or user not in **OKTA** | §7 — add the missing record to `QARCH_CNFG_CTRL`; or Cloud adds user to OKTA (25-01000519, 25-01010780) |
| "Session logs me out after 10–15 min even when active" | `WEB SECURITY` timeout configs (`SESSION_TIMEOUT`, `SESSION_UNLOAD_TIMEOUT`, `UIC_UNLOAD_TIMESPAN_MIN`) too low; UPS/ENGS layer caps at 10 vs QFC 60 (bug) | §7 — raise the three configs at ENV layer (23-00928292) |
| "SAP vendors not creating BAs / SYNCHRONIZE_WITH_API HTTP 500 after a patch" | QRA API web-config drift (e.g. `OPENID` parameter), or SAP MT instance count mismatch | §8 — check **QRA API web config** (`OPENID=False`), MT instance count (25-01019743, 24-00986198) |
| "BA update no longer kicks off PUBBA" / "PUBBA stuck / locked / errors" / "MGs stopped interfacing to SAP" | PUBBA process config/visibility, stuck queue records, or interface engine down | §8 — verify PUBBA is configured & visible in Web; clear stuck QUE/WTL records; restart MT (24-00970711, 23-00932125; ADO #1779057, #1781706) |
| "QLS Lease Interface (UPSLSINTFC) failing / out-of-memory / unique constraint" in PRD | Integration-engine defect or bad lease data; recurring on EQT/EQC | §9 — known recurring bug family (ADO #1709805, #1710611, #1745693) |
| "DOI maintenance/transfer record auto-deletes" / "MG won't process" / "combine logic not working" | **DOI Maintenance/Transfer (Design Studio) defect** — many are real bugs sent to engineering | §10 — get MG#/PQID; most resolve via patch or data script |
| "Owner Lease Xref bulk-edit / import to replace doesn't work" | Owner Lease Xref screen import defect | §11 — known bug family (ADO #1329511, #1604605) |
| "Reports not visible in QDO Web" / "QQM report timeout" / "SSO not working for QQM" | Report not migrated to the env / CMC export config / QQM SSO config | §12 — migrate reports PRD→target; QQM team config in CMC portal |

---

## 2. Architecture & Concepts

```
[Business Associates (BA master)]  ──PUBBA──►  [QLS leases]  ──UPSLSINTFC──►  [QDO: DONL_AGMT lease xref]
        │  (SCTRL_BA_ENTITY + QRA BA address tables)                                   │
        │                                                                              ▼
        └──────────────►  [QDO  DOI / Owner / Cost Center / Property / Maintenance Groups]
                                   │
                                   ├──►  SAP integration  (QRA SAP WebService / QPEC SAP MT / SYNCHRONIZE_WITH_API)
                                   │        vendor⇄BA sync, DOI→SAP, MG/JIB netting
                                   └──►  QQM reporting (Business Objects / CMC), DOR/DO reports
```

### Key terms (Quorum / QDO / upstream-accounting vocabulary)
- **BA = Business Associate** — the owner/vendor/payee master record. Edited on the **BA web screen** (a.k.a. **BA005** in Classic). Stored in **`SCTRL_BA_ENTITY`** (entity-level: name, `BA_1099_IND`, Tax-ID) plus **QRA BA *address* tables** (zip, state, address-level 1099). The split between entity and QRA address tables is the source of several "indicator out of sync" defects.
- **DOI = Division Order Interest** — the owner ownership record on a property; **decimal interest** is the owner's fractional share. **DOI Maintenance / Transfer** screens (Design Studio) move/convey ownership; a **Maintenance Group (MG)** batches a set of DOI changes and is what **interfaces to SAP**.
- **Cost Center → Property → DOI** — creation chain. Creating a **Cost Center** triggers the **`ORGCOSTGEN`** process and should auto-open the Property screen; missing `ORGCOSTGEN` access breaks "create new property."
- **PUBBA** — the process that **publishes/syncs BAs from eSuite to QLS** (and is expected to fire after a BA update). Lives in **`Quorum.ESuite`**; common failure modes: not configured/visible in Web, stuck QUE/WTL queue records, duplicate routing numbers on bulk-converted BAs.
- **QRA = Quorum Revenue/Royalty Accounting** — the integration/webservice layer between QDO and SAP (repos `Quorum.Upstream.QRA.*`, incl. `.SAP.Application.WebService`, `.Application.MiddleTier`). The **QRA API web config** (`OPENID`, endpoints) drives the **SYNCHRONIZE_WITH_API** vendor→BA flow.
- **QPEC** — the eSuite **process-engine container**; the **SAP MT (middle tier) QPEC** runs the SAP integration. Instance count must match the number of SAP MTs (a stray instance shows "KILL state").
- **UPSLSINTFC** — **QLS Lease Interface** batch (QP043, process type "QRA Integration") that pulls QLS leases into QDO (`DONL_AGMT`); a prerequisite for Owner-Associated-Lease DOI setup.
- **Security object / Security group** — eSuite authorization. A "SecurityId 'X' is not registered" error or a missing button/tab is almost always a **missing security object** in a group, fixed by a SQL script into `ESUITE_QFC` (groups identified by number, e.g. 48505, 70000, 90671012).
- **`QARCH_CNFG_CTRL`** — the **Global Configurations** table (key/group/value, with layers: ENV / UPS / ENGS / QFC). Missing or low-valued records here cause "not registered" errors and session timeouts.
- **Code Table 30000** — country code table; the **Hidden Ind** flag controls which countries (and their state lists) appear on the BA Address tab.
- **Zip-code mask** — formatting/validation applied to the BA address zip; bad converted `+4` suffix data and a too-aggressive mask cause the dominant "can't save BA / zip error" cluster.
- **QQM** — Quorum Query Manager / Business Objects reporting (CMC portal, "DO Universe"); access issues = report not migrated to the env or SSO/CMC config.
- **DOR003 / DOR005 / DO004 / QP087** — DO reports / report-launcher / query screens that show up in report-formatting cases.

---

## 3. Decision Tree

```
QDO Platform/Integration case
│
├─ Can't SAVE / use a BA web screen?
│   ├─ "zip code error" / state list blank / country / 4-digit suffix       → §4  (zip-mask + cleanup script; Code Table 30000 Hidden Ind)
│   ├─ SSN/Tax-ID won't save / no TIN field                                 → §5  (add BA Tax-ID security objects to the group)
│   ├─ adding SSN removes 1099 / 1099 auto-unchecks / 1099 out of sync      → §5  (defect→patch + QRA-table sync script)
│   └─ notes/attachments/contact-type/name missing after upgrade (UAT)     → §6  (Classic→Web conversion / seed scripts)
│
├─ "Button/tab missing" / "security error" / "can't get in" / "session times out"?
│   ├─ SecurityId not registered / missing button / can't create property  → §7  (add security object/group via script; ORGCOSTGEN; QARCH_CNFG_CTRL record)
│   ├─ Citrix / web access / login                                          → §7  (OKTA add user; deactivate dup DB user; Cloud)
│   └─ logs out after 10–15 min                                             → §7  (raise WEB SECURITY timeout configs at ENV layer)
│
├─ Integration not flowing?
│   ├─ SAP vendor→BA / SYNCHRONIZE_WITH_API HTTP 500 / QPEC SAP MT          → §8  (QRA API web config OPENID; MT instance count; restart)
│   ├─ PUBBA not firing / stuck / locked / MGs stopped interfacing to SAP   → §8  (PUBBA config & Web visibility; clear QUE/WTL; restart MT)
│   └─ QLS leases not coming into QDO / UPSLSINTFC failing / OOM            → §9  (known UPSLSINTFC bug family; data + memory)
│
├─ DOI Maintenance / Transfer / MG screen erroring or behaving wrong?       → §10 (mostly Design-Studio defects; get MG#/PQID; patch or data script)
├─ Owner Lease Xref import / bulk-edit broken?                              → §11 (Owner Lease Xref import bug family)
├─ Report not visible / QQM timeout / QQM SSO?                              → §12 (migrate reports to env; CMC config)
│
└─ "How do I…" / audit / works-as-designed / customer cancelled            → §15 Expected-Behavior FAQ
```

---

## 4. Cluster A — BA web screen: Zip / State / Country masking & validation
**(largest actionable cluster — BA address validation on the eSuite Web BA screen)**

The single most recurring QDO platform signature: **a BA will not save because of a zip-code error**, especially right after a Classic→Web upgrade/UAT, when converted zip data containing a 4-digit `+4` suffix collides with the **zip-code masking** validation.

**Symptoms (verbatim):**
- "when I open any BA and try to save it, I'm getting an error on the zip code format … happened on 100% of the BAs" (25-01044168)
- "All BA records with 4-digit suffix on zip code did not convert properly causing an error when editing" (25-01042115)
- "4 digit zip code … shows in the desktop version and in the Suffix high-level data, but it does not show in the actual address details" (26-01092829)
- "No States listed in BA Address tab" (25-01043401)

**Root causes & fixes seen:**
| Issue | Root cause | Fix | Case |
|---|---|---|---|
| BA won't save — zip format error on existing BAs | Converted zip data has a bad/`+4` suffix that the new mask rejects | **Run the zip-code cleanup script** (cleans data so masking works) | 25-01044168, 25-01042115 |
| 4-digit / foreign zip not displaying in address details | Missing/incorrect **zip-code mask** for that format | **Add the zip-code mask** | 26-01092829 |
| "Zip Code requires 5 digits" rejecting valid foreign zips | Mask too strict | Config the mask to allow the format | 26-01092829 |
| Zip masking driven by a **global configuration** that errored on upgrade | Masking global-config | Confirm/repair the masking global config | 24-00987114 (MEW 2024.04), ADO #1549818 |
| **No States listed** on BA Address tab | Country record not hidden, so the dependent state list won't load | **Code Table 30000 → set Hidden Ind = checked on the "USA" country** record | 25-01043401 |

**Fix recipe:**
1. Reproduce on one BA; capture the exact zip string and whether it has a `+4` suffix or is foreign.
2. For mass failures after an upgrade/conversion → **run the zip-code cleanup script** (attached to 25-01044168 / 25-01042115) to normalize the stored zip, then re-test save.
3. For a specific format not displaying → **add/adjust the zip-code mask** for that country (26-01092829).
4. For blank state lists → **Code Table 30000**, set **Hidden Ind** appropriately on the country record (25-01043401).
5. Note the **field is not marked mandatory yet still triggers validation** — this is a recognized product gap (ADO **#1731741**, Proposed); the operational fix is still the cleanup script + mask.

---

## 5. Cluster B — BA 1099 / SSN / Tax-ID indicator & security

Two distinct problems that present together on the BA web screen.

**(a) Tax-ID / SSN won't save → security, not a bug.**
- 25-01042111: "system allows me to select a tax type but won't let me add a TIN/SSN … can't save a new BA." **Fix:** *"Added the correct BA TAX ID security objects to the BA Data Entry security groups"* (script `19-ESUITE_QFC-Add BA Tax ID Update Privs V2.sql`). → **§7-style security fix.**

**(b) The 1099 indicator changes/unchecks itself → software defect + a data-sync gap.**
| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| "Adding SSN to BA removes the 1099 Indicator" | BA-web defect in 1099 handling | **Defect — fixed, shipped in the Sept hotfix** | 25-01041826 |
| "BA updates auto-uncheck 1099 flag" | Same family | **Bug, requires a patch** | 25-01042098 |
| "Unable to update `BA_1099_IND` in `SCTRL_BA_ENTITY` via the BA web screen" (MEW 2024.04) | BA-web cannot persist the entity-level 1099 flag | Code fix | ADO **#1711218** (Closed) |
| "1099 indicator changing in BA005" (GLE) | Entity-level 1099 (`SCTRL_BA_ENTITY`) **out of sync with the QRA BA *address* table** | **Sync script** to align the 1099 indicator between the QRA BA address table and BA Entity | 25-…, ADO **#1775732** (Closed) + **#1771382** (Script Deployment, Closed) |
| 1099 / QPEC version batch errors (QLS 1099 submission) | QPEC 1099-submission batch defect | Code fix | ADO **#1656731 / #1646888** (Closed) |

> **Key insight:** the 1099 flag lives in **two places** — `SCTRL_BA_ENTITY.BA_1099_IND` (entity) and a **QRA BA address-level** table. The web screen historically failed to keep them in sync (defect → patches #1711218; and a remediation **sync script** #1771382). When a client says "1099 keeps changing/unchecking," check **both** locations and whether the patch + sync script have been applied. AP-Withholding 1099 config is being revisited again in **2026.04** (ADO #1801739/#1802162/#1802892).

**Fix recipe:** (1) Tax-ID/SSN can't save → add **BA Tax-ID security objects** to the BA Data Entry group (script). (2) 1099 flips → confirm the BA-web 1099 patch is deployed (#1711218; 25-01041826 Sept hotfix), then run the **1099 sync script** to reconcile `SCTRL_BA_ENTITY` vs the QRA address table (#1771382).

---

## 6. Cluster C — BA conversion gaps: notes, attachments, contact-type, names
**(Classic→Web upgrade artifacts — data is "missing in UAT/Web" because it stayed in the classic table or was never seeded)**

These spike during 2024.x / 2025 upgrade UAT (Spur, Camino, Riley, Petro-Hunt) and are **Application Configuration**, fixed with a one-time **migration or seed script**, not code.

| Reported as | Root cause | Fix | Case |
|---|---|---|---|
| "Existing attachments on BA records did not convert / don't appear in UAT" | BA doc info still in the **classic table**, not the **web table** | **Script to migrate BA doc info from classic table to web table** | 25-01042121, 23-00917762 |
| "Categories for notes on BA are missing" | Note categories not seeded in Web | **Script to insert BA Note categories** into the correct `ESUITE_QFC` table | 25-01042122 |
| "Contacts are missing a Contact Type on the General tab" | Contact-type not populated on conversion | **Script run to populate contact type; added to post-conversion scripts** | 26-01084649 |
| "BA contact names default messed up" / "BA setups with name error" / "Sub-zero (0) in BA Associate" | Name/format conversion defects | Defect → patch (e.g. **Patch 9** for 25-01006774) | 25-01047255, 25-01006774, 23-00933670 |
| "BA missing categories for adding notes" | Same as note-categories seed | Seed script | 25-01042122 |

**Fix recipe:** treat "X is missing on the BA in Web/UAT after upgrade" as a **conversion/seed gap first**. The repeatable fixes are: migrate BA **documents** classic→web table; **insert** note categories / contact types into the `ESUITE_QFC` table; for name-format corruption, confirm the relevant **post-conversion patch** is on. Ask whether the script was added to **post-conversion scripts** so it survives the next refresh (26-01084649).

---

## 7. Cluster D — Security objects / groups / Citrix / OKTA / session
**(the "add-the-missing-object" cluster — the highest-leverage pattern on this product)**

A large share of "screen errors / button missing / can't get in / can't launch a process" cases resolve by **adding a missing security object or security group via a SQL script into `ESUITE_QFC`**, or by a Cloud-Ops identity fix.

| Reported as | Root cause | Fix | Case / ADO |
|---|---|---|---|
| "Can't create a Property after creating a Cost Center" / property screen didn't auto-open | Group lacks access to the **`ORGCOSTGEN`** process | **Security update script to grant `ORGCOSTGEN`** | 25-01042097 |
| "No Approval button on BA record" | BA-Approval config not enabled for the client | **BA-Approval config scripts** run in `QFC` and `ESUITE_QFC` (attached to case) | 25-01042184 |
| "Security error setting up a cost center (but it says it saved)" | Missing **`ORG/BTYP/QRA`** security object | **Add `ORG/BTYP/QRA` security object** to the groups (e.g. 70000, 90671012) | 25-01048054 |
| "`SecurityId 'QUCPersonaEditor' is not registered with the QApplicationController`" | Missing **Global Configuration** record | **SQL script adds the record to `ESUITE_QFC.QARCH_CNFG_CTRL`** (Global Configurations) | 25-01000519 |
| "Need new security group for `qFrmDOICopy`" / DOI-Copy access | Group missing the **`QFrmDOICopy`** security object | **Add `QFrmDOICopy` security object** to the groups to mirror PRD | 26-01095895 |
| "Security permissions in QDO UAT env" (groups missing) | UAT missing QDO groups vs PRD | **Script to add the missing groups** (e.g. 48505, 48509, 48510) | 25-01022455 |
| "Event drop-down blank on BA Contact screen" | New feature with no Upstream use | Replied — **N/A in Upstream Accounting** (not a defect) | 25-01043405 |
| "Web Access Error — user X" | Duplicate / stale DB user | **Deactivate the duplicate DB user** so they're redirected to the correct (VTL_) account | 25-01028333 |
| "User can't access Citrix environment" | User not provisioned in **OKTA** | **Cloud team adds the user to OKTA** | 25-01010780 |
| "Session logs out after 10–15 min even when active" | `WEB SECURITY` group timeout configs too low; **UPS/ENGS layer caps at 10 vs QFC's 60 (bug)** | **Set `SESSION_TIMEOUT`, `SESSION_UNLOAD_TIMEOUT`, `UIC_UNLOAD_TIMESPAN_MIN` to 60 at the ENV layer** | 23-00928292 |
| "RC4 authentication inquiry" / SSO for QQM | Auth/SSO config | Config (QQM SSO — see §12) | 25-01059347, 25-01043410 |

**Fix recipe:**
1. For a "SecurityId … not registered" or missing-button/tab/process error, identify the **security object name** from the error (e.g. `QUCPersonaEditor`, `QFrmDOICopy`, `ORGCOSTGEN`, `ORG/BTYP/QRA`).
2. Add it to the affected **security group(s)** via the standard script into `ESUITE_QFC` (group numbers come from the client's setup; mirror PRD when fixing UAT). Many such scripts are already attached to the cited cases — reuse them.
3. For "not registered with QApplicationController," the missing item is usually a **Global Configurations (`QARCH_CNFG_CTRL`)** record, not just a group entry (25-01000519).
4. For login/Citrix, route to **Cloud Ops** (OKTA add / dup-user deactivate). For session timeout, raise the **three WEB SECURITY configs at the ENV layer** (and note the UPS/ENGS 10-min cap is a known bug — 23-00928292).

---

## 8. Cluster E — SAP ⇄ QDO integration (PUBBA, QRA webservice, vendor→BA, MG/JIB)

The integration layer between QDO and SAP. Split into the **QRA webservice / vendor→BA** path and the **PUBBA / MG / JIB** path.

| Reported as | Root cause | Fix | Case / ADO |
|---|---|---|---|
| "After Patch 10, SAP vendors → UPS BAs failing; `SYNCHRONIZE_WITH_API` HTTP 500; queue `/QBSOL/QPIQUEUE` backing up" | **QRA API web-config drift** after patch | **Updated the `OPENID` parameter to `False`** in the QRA API web config | 25-01019743 |
| "Two processes in SAP MT QPEC, one always in KILL state" | **QPEC SAP-MT instance count** doesn't match the number of SAP MTs | **Set the number of instances to 2** to match the client's two SAP MTs | 24-00986198 |
| "BA update no longer kicks off PUBBA in the Web interface" | PUBBA not wired to fire from BA-Web update | Configure PUBBA to trigger; verify it's enabled in Web | 24-00970711; ADO **#1779057** ("PUBBA not visible in Web") |
| "PUBBA stuck / process lock / records in 'WTL' & 'QUE' status" | Stuck queue records / process lock | **Clear/cancel the stuck QUE records** (scripts), restart the process | ADO **#1781706, #1777960/#1777968** (Closed) |
| "PUBBA fails when an internal BA record is updated / invalid parameter setup" | PUBBA defect / parameter setup | Code/config fix | ADO **#1769479, #1765992** (Closed) |
| "PUBBA BA sync to QLS fails — multiple converted BAs with the same routing number" | Duplicate routing numbers from bulk conversion | Code fix | ADO **#1777307 / #1777518** (Closed) |
| "Maintenance Groups stopped interfacing to SAP (all stuck)" | Interface engine / MT down or blocked | Restart services/MT; clear stuck MGs (defect investigation) | 23-00932125 (Repsol) |
| "SAP→Quorum BA interface (ZY BA / custom T-Code) — customer not created" | Client SAP-transport / config | **Provided steps to customer; resolved** (client SAP-side config) | 23-00914201 (Apache) |
| "BA changed on DOI setup — SAP has a different BA than the XML sent" | BA mapping mismatch DOI↔SAP | Investigated (no single product WI) | 22-00830681 |
| "Lease Interface (UPSLSINTFC) failing in PRD" — see §9 | — | — | 24-00982285 |
| Legacy MRO/COP DOI↔SAP defects: APRV_USER set to SAP service account, JIB netting, recoup transfer, slow Copy-to-Live | Older integration defects | **Shipped in Spring/Fall 2021 GA releases** | 22-00676549, 22-00676527, 22-00676551, 22-00676532 |
| "Enable integration with eSuite" (Owner Search action/link missing) | Integration module not enabled | **Enable via `SARCH_CNFG_INT_MODULE`** | 24-00985325 |

**Fix recipe:**
1. **Vendor→BA / HTTP 500 after a patch** → first suspect **QRA API web-config drift**; the known fix is the **`OPENID` parameter** value (25-01019743). Check the SAP-side queue (`/QBSOL/QPIQUEUE`, SLG1) to confirm where it's blocked.
2. **QPEC SAP MT "KILL state"** → reconcile the **instance count** with the number of SAP MTs (24-00986198).
3. **PUBBA** → confirm it's **configured and visible in Web** (#1779057), that BA-update triggers it (24-00970711), and clear any **stuck QUE/WTL** records (#1781706). Watch for **duplicate routing numbers** on bulk-converted BAs (#1777307).
4. **MGs stopped interfacing** → restart MT/services first; if all MGs are stuck it's usually the engine, not one MG (23-00932125).
5. Many SAP-side issues (custom T-Codes, transports) are **client SAP configuration** — provide steps, don't assume a Quorum code bug (23-00914201).

---

## 9. Cluster F — QLS ⇄ QDO lease interface (UPSLSINTFC)

**UPSLSINTFC** (QLS Lease Interface, QP043, process type "QRA Integration") pulls QLS leases into QDO's **`DONL_AGMT`** so DOI Owner-Associated-Leases can reference them. A recurring failure cluster, heaviest on **EQT/EQC**.

**Symptom (24-00982285):** "UPSLSINTFC failing in PRD … newest record in `DONL_AGMT` from 2/22/2024 … `Specified cast is not valid` … `Continue Process On Failed Execute Is TRUE for CDTBLSYNC` … process will continue" (PQIDs 8626878 / 8623022) — so the process *appears* to run but the code-table-sync step silently fails and no leases land.

| Signature | Root cause | Fix | ADO |
|---|---|---|---|
| Timeout | Volume / query | Tune / data | #1571811 (MAC, Closed) |
| **Out of Memory** (EQT/EQC, recurring) | Large lease dataset | Memory/batch + code fixes | #1709805, #1709809, #1760007 (Closed) |
| `ORA-00001 unique constraint (LIS.PK_QCODE_QRA_PROP)` | Duplicate QRA property code | Data cleanup + fix | #1710611 (RSC, 25-01000047, Closed) |
| "Specified cast is not valid" / CDTBLSYNC step | Data type / code-table sync defect | Code fix checked into CORE + EQT metadata | #1745693 (CORE), #1745723 (EQT), Closed |

**Fix recipe:** get the **PQID** and the **exact step + error**. "Specified cast is not valid" at **CDTBLSYNC** and **OOM** are known recurring defects with fixes checked into **CORE** metadata (#1745693) plus client metadata; many incidents were unblocked by **data scripts** (duplicate QRA property, code-table rows) deployed to UBT/PRD (#1730536, #1744368, #1761605). Confirm the client has the CORE UPSLSINTFC fixes; if it's OOM, batch/raise memory.

---

## 10. Cluster G — DOI Maintenance / Transfer / Maintenance-Group (Design Studio)

"Design Studio"-category cases here are the **DOI Maintenance, DOI Transfer, and Maintenance-Group screens** — the ownership-conveyance UI. Most actionable ones are **real software defects** (Resolution often blank in SF = routed to Engineering / shipped in a release), so confirm the fix build rather than reconfiguring.

| Reported as | Disposition | Case / ADO |
|---|---|---|
| "Record automatically getting deleted from the **To Owner** section on the DOI maintenance screen" (Edit from MG — both ownership & funds transfer) | Defect — fixed | ADO **#1766463 (DAY), #1766476 (QDO)** Closed |
| "Maintenance transfer one→many RI owners — Preview throws an error" | Defect — fixed | ADO **#1753192 (CNX)** Closed; SF 25-01039798 |
| "Transfers on WI owners on DOIs involved in Makeup not logging PPNs" | Defect — fixed | ADO **#1755241 (MAC)** Closed; SF 25-01044658 |
| "DO Transfer — Combine logic not working" | Defect (engineering) | 22-00704994 |
| "Receiving error when Combine Interest & Owner Lease Data flags both checked on Transfer" | Defect | 22-00672539 |
| "Bearer Group errors when previous Bearer Group maintenance was processed" / "Bearer Group change not interfacing when only % updated" | Defects | 22-00676467, 22-00676494 |
| "ISQs sequencing in DOI Maintenance" / "MG 792 / MG 3551 errors" / "Funds on heirs don't reflect allocation %" | Defects / config | 22-00821074, 22-00564790, 22-00823201 |
| "Unable to delete a Pay Code change in DO127" / "DO081 error" / "DO136 Agmt No. update error" / "PPI required on DO015" | Screen defects | 22-00566283, 22-00653774, 22-00579595, 22-00512840 |
| "Maintenance Group #4331 not fully loading to make changes" | **Bug — fixed by the May 2025 OOC Hotfix for 2024.10 (Patch 2)** | 25-01024893 |
| "DO copy doesn't copy the market group" | **Working as designed** — copy *does* copy a market group **only if it has details**; a header with no details copies neither | 22-00512572 (see §15) |
| "Save failed due to error — well/DOI xref" | Misleading error text; required-field message ("Value must be specified") was the real cause | 22-00818885 |

**Fix recipe:** capture the **MG number / property / PQID** and the exact screen + error. For "record auto-deletes on the To-Owner section" and "preview/transfer errors," these are **known, fixed defects** (#1766463/#1766476, #1753192, #1755241) — confirm the client's build includes the fix or schedule the hotfix; don't reconfigure. Where SF Resolution is blank, the item was handled in a GA release/patch — verify in `Quorum.Upstream.QDO.ReleaseNotes`.

---

## 11. Cluster H — Owner Lease Xref import / bulk-edit

The **Owner Lease Xref** screen links owners to QLS leases on a DOI. Its **import / bulk-edit "replace existing content"** path has a recurring defect history.

| Reported as | Disposition | Case / ADO |
|---|---|---|
| "Importing Owner Lease Xref to **Replace Existing Content** not working" | Defect — fixed | 22-00672538; ADO **#1329511 (MRO)** Closed |
| "Owner Lease Xref **Bulk Edit load does not work**" | Defect — fixed | 22-00823022; ADO **#1604605** Closed |
| "Owner Lease Xref error when replacing agreement on multiple lines/owners" | Defect — fixed | ADO **#1372585 (MRO)** Closed |
| "Owner Lease Xref being deleted when user performs a Modify on the owner" | Defect — fixed | ADO **#249405 (MRO)** Closed |
| "Missing Owner picklist on Owner Lease Xref screen" / "Invalid effective date" | Defect | ADO **#1607907, #1446497** |

**Fix recipe:** Owner Lease Xref import/bulk-edit problems are an established **defect family** (largely MRO-originated, now CORE). Confirm the client build post-dates the relevant fix (#1329511 replace, #1604605 bulk-edit). For "xref deleted on owner modify," that's #249405 — a fixed defect, not user error.

---

## 12. Cluster I — QQM reporting access / report visibility

QQM = Business Objects reporting via the **CMC portal** and the **DO Universe**. Issues are almost always **environment/config**, not data.

| Reported as | Root cause | Fix | Case |
|---|---|---|---|
| "Reports not visible in QDO Web" | Reports not migrated to that environment | **Migrate reports** from PRD to the target env | 23-00931652, 25-01043410 |
| "QQM report time-out" / "can't export results" | CMC export/config | **QQM team changes the config in the CMC portal**; then export works | 24-00941236 |
| "Single Sign-On not working for QQM" | QQM SSO / report deployment | Migrate reports + SSO config | 25-01043410 |
| "QQM objects needed" / "Missing object in DO Universe" | Universe object request / training | Add object / explain (often Training) | 23-00898929, 24-00969542 |
| "QQM export limitation" / "Business Objects upgrade guidance" | Product limitation / guidance | Training (see §15) | 23-00885675, 26-01079869 |

**Fix recipe:** "report not visible" → **migrate the report to that env** (PRD→UAT/UBT). "Timeout / can't export" → route to the **QQM team** to adjust the **CMC** config (24-00941236). SSO/access → QQM SSO config. Universe-object and export-limit questions are usually **Training**, not defects.

---

## 13. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF / note |
|---|---|---|---|---|
| **#1531903** (+#1534156) | Bug / **Closed** | Cannot Save BA with Address due to Zip Code Error (+ analysis) | §4 | zip cleanup |
| **#1549818** | Bug / Ready for QA | RSC — myQDO BA Screen errors with Zip Code Masking Global Config | §4 | |
| **#1731741** | Bug / **Proposed** | 2025.04 ESUITE BA Entity — Zip not mandatory but triggers validation on save | §4 | product gap |
| **#1729155** | (analysis doc) | Zip Code Masking Review (`Quorum.Upstream.Tools/work_item_analysis/`) | §4 | |
| **#1711218** | Bug / **Closed** | MEW 2024.04 — Unable to update `BA_1099_IND` in `SCTRL_BA_ENTITY` via BA web | §5 | |
| **#1775732** (+#1771382) | Bug / **Closed** (+ Script Deployment) | GLE — 1099 indicator changing in BA005 (+ sync 1099 QRA table ↔ BA Entity) | §5 | |
| **#1656731 / #1646888** | Bug / **Closed** | QLS/QPEC — 1099 submission batch process errors | §5 | |
| **#1801739 / #1802162 / #1802892** | Bug/Task | 2026.04 Range — AP Withholding — check BA 1099 setting | §5 | future |
| **#1779057** | Requirement / **Closed** | PUBBA (from ESUITE) process not visible in Web | §8 | |
| **#1781706** | Bug / **Closed** | HEC QLS — PUBBA process lock, stuck 'WTL' & 'QUE' | §8 | + #1777960/#1777968 cancel-QUE scripts |
| **#1769479 / #1765992** | Bug / **Closed** | SEP — PUBBA fails on internal BA update / invalid parameter setup | §8 | |
| **#1777307 / #1777518** | Bug / **Closed** | UPS/ESUITE — PUBBA→QLS fails: converted BAs with same routing number | §8 | |
| **#1709805 / #1709809 / #1760007** | Bug / Incident / **Closed** | EQT/EQC — UPSLSINTFC Out of Memory | §9 | |
| **#1710611** | Bug / **Closed** | RSC — UPSLSINTFC `ORA-00001 PK_QCODE_QRA_PROP` | §9 | 25-01000047 |
| **#1745693 (CORE) / #1745723 (EQT)** | Bug / **Closed** | UPSLSINTFC fixes checked into CORE & EQT metadata | §9 | |
| **#1571811** | Bug / **Closed** | MAC — UPSLSINTFC timeout | §9 | 22-00825868 |
| **#1766463 (DAY) / #1766476 (QDO)** | Bug / **Closed** | DOI maintenance — To-Owner record auto-deletes on MG Edit (ownership & funds) | §10 | |
| **#1753192 (CNX)** | Bug / **Closed** | Maintenance transfer one→many RI owners — Preview error | §10 | 25-01039798 |
| **#1755241 (MAC)** | Bug / **Closed** | Transfers on WI owners in Makeup not logging PPNs | §10 | 25-01044658 |
| **#1329511 (MRO) / #1604605** | Bug / **Closed** | Owner Lease Xref — replace-existing / bulk-edit load not working | §11 | 22-00672538, 22-00823022 |
| **#1372585 / #249405 / #1446497 / #1607907** | Bug / Closed-Proposed | Owner Lease Xref — replace-agreement / deleted-on-modify / invalid date / missing picklist | §11 | |

> Many actionable cases were dispositioned **operationally** (security/config/seed/data scripts into `ESUITE_QFC`, or shipped in a GA release/patch) with **no single product WI** and a blank SF Resolution. For "Software Defect" cases with blank Resolution, the fix was a release/patch — confirm in **`Quorum.Upstream.QDO.ReleaseNotes`** and the client's build/patch level.

---

## 14. Diagnostic SQL

> **Caveat:** QDO On-Demand is **SQL Server**, schemas **`ESUITE_QFC`** (core/shared) and per-client. Column/table names below come from case repro text + code search; **verify against the client schema before scripting**, and always run a verify-SELECT before any UPDATE/DELETE, wrapped in a transaction.

```sql
-- A. BA entity row incl. the 1099 flag and Tax-ID (§5) — the entity side of the 1099 split
SELECT BA_NO, BA_NAME, BA_1099_IND, BA_TAX_ID_NO
FROM   ESUITE_QFC.SCTRL_BA_ENTITY
WHERE  BA_NO = '<BA_NO>';
-- Compare BA_1099_IND here vs the QRA BA *address* table; a mismatch = the #1775732/#1771382 sync gap.

-- B. BA addresses / zip data for the zip-mask cluster (§4) — look for 4-digit (+4) suffix anomalies
SELECT BA_NO, ADDR_SEQ, COUNTRY_CD, STATE_CD, ZIP_CD
FROM   ESUITE_QFC.<BA address table>     -- QRA BA address table; verify exact name in client schema
WHERE  BA_NO = '<BA_NO>';

-- C. Country / state code table (the "no states listed" fix, §4)
SELECT CODE, DESCRIPTION, HIDDEN_IND
FROM   ESUITE_QFC.<Code Table 30000 table>
WHERE  CODE_TABLE = 30000;               -- set HIDDEN_IND for the USA country record (25-01043401)

-- D. Global Configurations — "SecurityId not registered" / session timeout (§7)
SELECT CNFG_GRP, CNFG_KEY, CNFG_VALUE, CNFG_LAYER
FROM   ESUITE_QFC.QARCH_CNFG_CTRL
WHERE  CNFG_GRP = 'WEB SECURITY'
   AND CNFG_KEY IN ('SESSION_TIMEOUT','SESSION_UNLOAD_TIMEOUT','UIC_UNLOAD_TIMESPAN_MIN');
-- UPS/ENGS layers cap at 10 (bug); raise to 60 at ENV layer (23-00928292).

-- E. Which security objects does a group have? ("button/tab/process missing", §7)
--    Find the group number, then confirm the object (e.g. ORGCOSTGEN, QFrmDOICopy, QUCPersonaEditor, ORG/BTYP/QRA) is present.
SELECT SEC_GRP_NO, SEC_OBJ_ID
FROM   ESUITE_QFC.<security group/object xref table>
WHERE  SEC_GRP_NO IN (<group nos, e.g. 70000, 48505>) 
ORDER BY SEC_OBJ_ID;

-- F. Leases pulled by UPSLSINTFC (§9) — is the interface actually landing rows?
SELECT MAX(CREATE_DTTM) newest, COUNT(*) cnt
FROM   <client schema>.DONL_AGMT;        -- a stale MAX(CREATE_DTTM) = UPSLSINTFC silently failing (24-00982285)

-- G. PUBBA / integration queue stuck records (§8)
--    Look for records stuck in 'QUE' / 'WTL' status for the PUBBA process; on SAP side check /QBSOL/QPIQUEUE + SLG1.

-- H. Find the failing process step + error by Process Queue ID (PQID), QP043/QP083 batch
--    Get PQID from the user, then read the process-queue / batch-message rows for that PQID + step
--    (e.g. CDTBLSYNC for UPSLSINTFC, ORGCOSTGEN for cost-center, the PUBBA step).
```

---

## 15. Expected-Behavior / User-Education FAQ

~31 Training + ~48 Customer-Error cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| "DO Copy doesn't copy the market group" | **Working as designed** — copy *does* carry a market group **only if it has details**. A market-group **header with no details** copies neither header nor details. | 22-00512572 |
| "Event drop-down blank on BA Contact screen" | **New feature with no applicable use in Upstream Accounting** — not a defect. | 25-01043405 |
| "New Lease not creating a new property number" / "Cost Center Code" question | Customer Error / setup expectation — walk through the **Cost Center → Property → DOI** creation chain. | 26-01093707, 26-01092858 |
| "BA Pick List shows incorrect entity type" / "BA suffix-2 setup errors" / "BA setup Primary Usage Type" | Training — BA setup field meanings / entity-type vs usage-type. | 25-01043402, 25-01028947, 24-00965739 |
| "MG stopped interfacing" / "MG 5988 errored then re-ran in a new PQID, neither blocked" | Often **Customer Error** — re-submitting creates a new PQID; the original isn't "stuck," it errored. Check the PQID's step error before assuming the engine is down. | 24-00961360, 26-01097853 |
| "Revenue Ownership Interface not active in SAP" / "QDO SAP integration broken after refresh" | Customer/SAP-side — interface toggled off or env refresh dropped config; re-enable / re-point. | 24-00960440, 24-00937766 |
| "PUBBA is deleting BAs in DO / unflagging internal-entity BAs in QLS" | **Customer Error** — understand internal-entity BA flag behavior in the QDO↔QLS sync before treating as a bug. | 24-00956331 |
| "Citrix Adobe / PDFs not opening / asking users to log in" | Customer/Citrix-side Adobe config — not a QDO defect. | 24-00983952, 24-00967195, 24-00967611 |
| "How do I print DOs / JIB statements for mailing" / "DOR003/DOR005 report issues" / "foreign addresses don't print" | Training / report-formatting — DO/JIB mail-out setup, foreign-address handling (verify the integrated SAP address is complete). | 24-00952420, 23-00921504, 22-00569459, 24-00981556 |
| "Batch processes in MyQuorum?" / "UPSLSINTFC full sync" / "certificates across environments" | Training — how scheduled/QRA-integration processes run; full-sync mechanics. | 23-00932130, 22-00689544, 24-00944085 |
| "Country code for Mount Lebanon" / "International country/region codes" | Training / Code-Table guidance — add/verify the country code (then §4 if state list is blank). | 24-00977720, 24-00942810 |
| "QQM export limitation" / "missing object in DO Universe" / "Business Objects upgrade guidance" | Training — QQM/BO product behavior & object requests, not a QDO defect. | 23-00885675, 24-00969542, 26-01079869 |
| "Locked account" / "user list for audit" / "install QDO on a laptop" | User-admin / Cloud — unlock, provide list, deploy client. | 23-00891889, 22-00587864, 22-00607324 |

**Tell-tale it's user/expected:** a BA setup field misunderstood (entity-type vs usage-type, 1099 vs SSN behavior); a "stuck" MG that actually **errored** (read the PQID step); a SAP/Citrix-side toggle or env-refresh drop; a copy/transfer that **correctly** follows the "header needs details" rule; or a reporting/Universe/export limit question. Verify the **security/config and the PQID error** before treating it as a defect.

---

## 16. Key Code, Processes & Repos

### Processes / interfaces
| Process / object | Purpose | Notes |
|---|---|---|
| **`ORGCOSTGEN`** | Cost-center → org-reporting generation (fires the Property screen) | Group needs access; `QBusinessRuleRefreshCostCenterOrgReportingTables.cs` (§7) |
| **PUBBA** | Publish/sync BAs eSuite → QLS (and post-BA-update) | In `Quorum.ESuite.*`; visibility/queue issues (§8) |
| **`SYNCHRONIZE_WITH_API`** | QRA webservice vendor→BA SAP sync | QRA API web config (`OPENID`) governs it (§8) |
| **QPEC SAP MT** | SAP integration process container | Instance count must match # of SAP MTs (§8) |
| **UPSLSINTFC** (QP043) | QLS Lease Interface → QDO `DONL_AGMT` | step `CDTBLSYNC`; OOM / cast / unique-PK defects (§9) |
| **DOI Maintenance / Transfer / MG** | Ownership conveyance UI; MG interfaces to SAP | Design-Studio screen defects (§10) |
| **Owner Lease Xref** import / bulk-edit | Link owners↔QLS leases on a DOI | Import "replace" / bulk-edit defect family (§11) |

### Code & data locations (confirmed via ADO code search)
| Symbol / object | Repo / path | Cluster |
|---|---|---|
| BA web screen / BA Entity unit tests / zip-mask constants | `Quorum.ESuite.Web` (`/Quorum.ESuite.UnitTests/BAEntity/BAEntityUnitTest.cs`, `/Quorum.ESuite.Constants/Constants.cs`) | §4/§5/§6 |
| Cost-center & org maintenance controllers / `ORGCOSTGEN` rule | `Quorum.ESuite.Web.Controllers/UIControllers/QUIControllerCostCenterMaintenance.cs`, `QUIControllerOrgMaintenance.cs`; `Quorum.Upstream.Shared.QUpsShared/BusinessRules/QBusinessRuleRefreshCostCenterOrgReportingTables.cs` | §7 |
| `SCTRL_BA_ENTITY` (entity + `BA_1099_IND`, Tax-ID) | `<CLIENT>.Upstream.*.Database` / generated `SctrlBaEntityDO.cs` in `<CLIENT>.QDO/.QRA.DataObject` | §5 |
| Zip Code Masking Review (analysis) | `Quorum.Upstream.Tools/work_item_analysis/1729155_Zip_Code_Masking_Review.md` | §4 |
| `QARCH_CNFG_CTRL` (Global Configurations) | `ESUITE_QFC` (DB) | §7 |

### Repos (product = `Quorum.Upstream.*`; client overrides = `<CLIENT>.Upstream.*`)
- **`Quorum.Upstream.QDO.*`** — core Division Order: `.DivisionOrder`, `.Application.Web` / `.MiddleTier` / `.APIHost`, `.Database`, `.ClassicBatch`, `.ClassicGUI`, `.Batch`, `.ReleaseNotes`. DOI/Transfer/MG screens (§10), Owner Lease Xref (§11).
- **`Quorum.Upstream.QRA.*`** — Revenue/Royalty Accounting **integration & SAP**: `.SAP.Application.WebService`, `.Application.MiddleTier`, `.ClassicBatch`, `.Database`, `.Tax`. SAP vendor→BA, `SYNCHRONIZE_WITH_API`, UPSLSINTFC plumbing (§8/§9).
- **`Quorum.ESuite.*`** — shared platform: BA web screen, `Application.Web` / `.MiddleTier` / `.QPEC` / `.ClassicGUI`, `.Database`, `.Constants`, security/config. PUBBA, BA, zip/1099, security objects (§4–§8).
- **`Quorum.Upstream.QCA.*` / `Quorum.Upstream.QCFS.*`** — sibling upstream modules (cash/CA, financial services) — relevant when an integration spans modules.
- **`<CLIENT>.Upstream.QDO.*` / `<CLIENT>.Upstream.QRA.SAP.Application.WebService` / `<CLIENT>.Upstream.*.Database / .Metadata / .ESuite.Database`** — client overrides (APA, CNX, EQT/EQC, GLE, MEW, RSC, DAY, MAC, SEP, HEC…). **Check the client repo/schema first** — many fixes are client-specific (SAP transport, UPSLSINTFC metadata, security groups, 1099 sync).

---

## 17. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A **screen behaves wrong on correct input/config**: 1099 unchecks itself / `BA_1099_IND` won't persist (#1711218, 25-01041826/098), DOI-maintenance To-Owner record auto-deletes (#1766463/#1766476), transfer Preview error (#1753192), PPNs not logged on Makeup transfers (#1755241), Owner Lease Xref replace/bulk-edit (#1329511/#1604605), Combine-logic (22-00704994).
- A **batch step crashes from a code/data defect**: UPSLSINTFC "Specified cast"/`CDTBLSYNC`/OOM/unique-PK (#1745693, #1709805, #1710611), PUBBA on internal-BA update / dup routing number (#1769479, #1777307).
- Provide: **PQID + failing step + exact error**, client + BA#/property/MG#, the screen, and a repro. Confirm fix availability in **`Quorum.Upstream.QDO.ReleaseNotes`** (or `Quorum.ESuite.ReleaseNotes`) and the client's build/patch level.

**Handle as Configuration / Cloud Ops (the default for "screen errors / can't get in") when:**
- **Security object/group missing** → add via script to `ESUITE_QFC` (`ORGCOSTGEN`, `QFrmDOICopy`, `QUCPersonaEditor`, `ORG/BTYP/QRA`, BA Tax-ID privs, BA Approval) — mirror PRD when fixing UAT (25-01042097, 26-01095895, 25-01022455, 25-01042111, 25-01042184, 25-01048054).
- **Global config record / timeout** → `QARCH_CNFG_CTRL` (25-01000519; session timeout 23-00928292).
- **Zip-mask / country / conversion** → zip cleanup script + mask, Code Table 30000 Hidden Ind, BA doc/notes/contact-type seed-migration scripts (§4/§6); add scripts to **post-conversion** so they survive refreshes.
- **SAP integration config** → QRA API web config (`OPENID`), QPEC MT instance count, PUBBA visibility/queue, `SARCH_CNFG_INT_MODULE` (§8).
- **Reporting** → migrate reports PRD→env; QQM/CMC config (§12).
- **Identity** → OKTA add / duplicate-DB-user deactivate → Cloud Ops (25-01010780, 25-01028333).

**Handle as Training / Expected behavior (no fix):** see §15 — DO-copy "header needs details," BA field-meaning questions, a "stuck" MG that actually errored (read the PQID), SAP/Citrix-side toggles, env-refresh config drops, QQM/Universe/export limits, report mail-out setup.

---

*Skill created: 2026-06-14.*
*Based on: 421 closed QDO Platform/Integration SF cases — 99 actionable (Software Defect 51 + Application Configuration 48; ChangeConfig not used on this product = 0) mined for fix recipes, plus ~79 Training/Customer-Error cases for the FAQ. ADO work items #1531903/#1534156, #1549818, #1731741, #1711218, #1775732/#1771382, #1656731/#1646888, #1779057, #1781706, #1769479/#1765992, #1777307/#1777518, #1709805/#1709809/#1760007, #1710611, #1745693/#1745723, #1571811, #1766463/#1766476, #1753192, #1755241, #1329511/#1604605, #1372585/#249405/#1446497/#1607907.*
*Companion: the QDO core/DOI (decimal-interest, suspense, owner-funds-release, conveyance) skill; REPO_REFERENCE.md.*
