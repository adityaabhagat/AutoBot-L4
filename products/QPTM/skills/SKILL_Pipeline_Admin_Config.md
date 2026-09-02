# SKILL: QPTM Pipeline Admin & System Configuration Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-01 | **Product:** QPTM (My Quorum Gas Pipeline)
**Scope:** System preferences / global & TSP config keys, code tables (Code/Decode & Code Table Definition Maintenance), TSP / pipeline setup & TSP-copy, calendar / accounting-month / cycle setup, **Location Administration** (add/edit/deactivate locations & meters, location attributes, location groups, points, zones), and **Install / upgrade / hotfix / deployment / metadata packaging / file-path & service config**.
**Companions:** Nomination/cycle behavior → **SKILL_Nominations.md** & **SKILL_EDI_Troubleshooting.md**. User/security setup → **SKILL_Security_UserAdmin.md**. Reporting/postings → **SKILL_Reporting_Regulatory_Postings.md**. This guide does **not** duplicate those.

> Evidence base: 1,141 closed QPTM cases in categories Pipeline Admin (683), System Configuration (362), Location Administration (57), Installation (39). Actionable subset mined here: **323 cases** with Root Cause = **Application Configuration (182)** or **Software Defect (141)**, plus the Customer Error / Training tail for the Expected-Behavior section. Resolution mix of those 323: Configuration Changed **135**, Software Updated **82**, Data Script Provided **27**, Software Update Available **23**, Workaround **13**, Infrastructure **11**. Every claim below cites a real SF case # and/or ADO work item.

---

## TABLE OF CONTENTS

1. [Quick Triage Checklist](#1-quick-triage-checklist)
2. [Concepts: Where Config Lives in QPTM](#2-concepts-where-config-lives-in-qptm)
3. [Symptom → Root-Cause Matrix](#3-symptom--root-cause-matrix)
4. [Location & Meter Administration (HIGH FREQUENCY)](#4-location--meter-administration-high-frequency)
5. [Location Groups & Zones](#5-location-groups--zones)
6. [Code Tables / Picklists / Dropdowns](#6-code-tables--picklists--dropdowns)
7. [Global & TSP Configuration Keys / System Preferences](#7-global--tsp-configuration-keys--system-preferences)
8. [TSP / Pipeline Setup & TSP-Copy](#8-tsp--pipeline-setup--tsp-copy)
9. [Calendar / Accounting Month / Cycle Setup](#9-calendar--accounting-month--cycle-setup)
10. [Install / Upgrade / Hotfix / Deployment / Metadata Packaging](#10-install--upgrade--hotfix--deployment--metadata-packaging)
11. [File Paths, Batch-Job Config, Services & Connectivity](#11-file-paths-batch-job-config-services--connectivity)
12. [Key Code Files & Repos](#12-key-code-files--repos)
13. [Database Tables Reference](#13-database-tables-reference)
14. [Diagnostic SQL Queries](#14-diagnostic-sql-queries)
15. [Verbatim Cloud-Ops Scripts (redacted)](#15-verbatim-cloud-ops-scripts-redacted)
16. [Known Historical ADO Bugs](#16-known-historical-ado-bugs)
17. [Expected Behavior / User Education](#17-expected-behavior--user-education)
18. [Escalation Decision Tree](#18-escalation-decision-tree)

---

## 1. Quick Triage Checklist

```
[ ] 1. WHAT is being configured — a Location/Meter, Location Group/Zone, Code Table,
       Global/TSP config key, Calendar/Accounting Month, TSP, or batch/file path?
[ ] 2. Which TSP_NO (and abbreviation)? Many setup bugs are TSP-copy artifacts.
[ ] 3. Which ENVIRONMENT — UAT / UBT / UATA1 / PRD / PRDA1 / a refresh/conversion env?
       A huge share of these cases are non-PRD setup/go-live work, NOT production defects.
[ ] 4. Web or Classic? Several config screens behave differently (esp. Location Maintenance).
[ ] 5. Is it tied to a build/hotfix/upgrade (e.g., "2025.10", "2024.04", "1.0→1.5")?
       If yes → §10 (packaging/metadata/file-path), not a product defect.
[ ] 6. EXACT screen + error text? (e.g., "unscoped picklist missing", "cannot be deleted",
       "dropdown not populating/retaining", "config cannot be modified").
[ ] 7. Is the request a DELETE of a config object (loc group, child meter, zone)? QPTM
       blocks most config deletes by design → likely a Cloud-Ops delete script (§15).
[ ] 8. Is it actually Expected Behavior? (filtered picklists, MDQ-only display) → §17.
[ ] 9. Data-conversion / TSP-copy origin? Attributes/labels frequently mis-seed (§4, §8).
[ ] 10. Deadline / go-live pressure? Go-live config cases are frequently CRITICAL.
```

### Where does it live?
| Reported as | Cluster | First place to look |
|-------------|---------|---------------------|
| Location/meter won't save, attribute missing, picklist filtered | §4 | Location Maintenance; `PACTRL_LOC*`, `PACTRL_LOC_ATTR` |
| "Can't delete location group / zone / child meter" | §5 | `PACTRL_LOC_GRP*` → Cloud-Ops delete script (§15) |
| Dropdown blank / value won't retain | §6 | Code Table Definition Maintenance / Code-Decode Value Maintenance |
| Middletier logging "missing config key"; can't edit global config | §7 | `qarch_cnfg_ctrl` (a.k.a. QARCH_GLOBAL_CONFIG / QARCH_TSP_CONFIG) |
| Wrong TSP label/abbrev after a copy | §8 | TSP setup metadata; TSP abbreviation |
| "month should be expired but is active" blocking saves | §9 | Code/Decode Value Maintenance — Accounting Month |
| "2025.10/2024.04 …" job failing, screen missing post-hotfix | §10/§11 | Packaging/metadata check-ins; environment file paths |

---

## 2. Concepts: Where Config Lives in QPTM

QPTM configuration is spread across several distinct subsystems. Knowing which one a request touches is 80% of the triage.

- **Global / TSP config keys** — key/value settings read by the middletier from the config-control table (`qarch_cnfg_ctrl`; documented elsewhere as `QARCH_GLOBAL_CONFIG` / `QARCH_TSP_CONFIG`). Keys are grouped (e.g., `NOMINATIONS`, `NAESB`, `TSP`). If a key is **missing**, the middletier logs `QConfigMgrBase.GetConfigKey.Missing` and falls back to a hard-coded default (case 25-01031118).
- **Code tables** — two screens: **Code Table Definition Maintenance** (defines a numbered code table, its columns, and **Displayed Column Order**) and **Code / Decode Value Maintenance** (the actual values). A dropdown that has options but **won't retain the selection** is almost always a missing **Displayed Column Order** on the code table definition (case 24-00984137, table **26204** Penalty Type).
- **Location / point setup** — **Location Maintenance** screen, backed by `PACTRL_LOC*` tables; location attributes (e.g., **Interruptible**, **Nominatable**, **OBA**) live in `PACTRL_LOC_ATTR`. **Location Groups** live in `PACTRL_LOC_GRP` (+ `PACTRL_LOC_GRP_ASSOC_QTY`).
- **TSP / pipeline setup** — per-TSP metadata incl. screen/tab labels and abbreviation; frequently seeded via a **TSP-copy** which can carry the source TSP's labels (case 25-01039826).
- **Calendar / accounting month** — Accounting Months are values in **Code/Decode Value Maintenance**; an un-closed expired month blocks Location saves (case 25-01035258).
- **Metadata layers** — base + client metadata. Screens, tabs, menu trees, process/report types, and import/export defs are metadata that must be **checked in / packaged (sysgen)** and travel through upgrade/hotfix scripts (cases 26-01102793, 25-01033214, 24-00972277).

**Key rule of thumb:** *QPTM does not allow most configuration objects to be deleted via the UI once created* (location groups, zones, child meters). The standard L4 disposition for "I need to delete X" is a **targeted Cloud-Ops delete script** — see §5 and §15.

---

## 3. Symptom → Root-Cause Matrix

| Symptom (message / behavior) | Most common root cause | Fix type | Evidence |
|------------------------------|------------------------|----------|----------|
| "Cannot delete this Location Group" (created by mistake, no txn data) | UI blocks loc-grp deletes by design | **Data script** (Template L, §15) | 26-01064296 / ADO #1778532,#1780227; 25-01047587 |
| Loc-group picklists show **Inactive** groups → confusion | Picklists don't filter Inactive groups | Data script to delete inactive groups | 25-01047587 |
| Locations **missing from location-group picklist** on nom screen | Meter missing the **Nominatable** attribute | Config (check attribute) | 26-01097568 |
| Picklist "opens with filters" / some locations missing | Working as designed — default/date filters | Education | 26-01099866 |
| **Interruptible** (or other) attribute not selectable on converted locs | Data-conversion didn't seed the attr row | Data script — insert `0` into `PACTRL_LOC_ATTR` | 26-01096011 |
| Location won't save: "Accounting month active when it should be expired" | Expired Accounting Month left **open** in Code/Decode | Config (close month) + cache refresh | 25-01035258 |
| Loc Maintenance: can't set two locations to the **same name** (Web) | Web same-name bug (worked in Classic) | Software updated (2022.10) | 24-00958301 / ADO #1670884 |
| Loc Maintenance: **States don't populate** after 1.0→1.5 upgrade | Sysgen view not regenerated for `QCODE_STATE`/`SCODE_STATE` | Re-sysgen + post-upgrade script | 24-00972277 |
| **Unscoped picklist** missing on Location Maintenance | Config / metadata not enabled in new version | Config | 24-00950009, 25-01045900 |
| Segment change in **Web** doesn't update location group (Classic does) | Web loc-group/segment sync defect | Software updated | 24-00939083 / ADO #1651001 |
| Dropdown has options but **selection won't retain** | Code table missing **Displayed Column Order** | Config (Code Table Definition Mtnce) | 24-00984137 / ADO #1692629 |
| Dropdown **empty** (Penalty Type, etc.) in UAT | Code table definition row missing entirely | Config (add code-table def, e.g. 26204) | 24-00967113 |
| TT (Trans Type) dropdown blank on Nom Submission | Pooling TOS x-ref missing; `QCODE_ACTN`/`KCTRL_TOS` name+descr mismatch | Config (Nom Config Sys Pref) | 26-01095071 |
| Middletier log floods "configuration setting … was missing" | Config keys never created; default-only | Config (create keys w/ defaults) | 25-01031118 / ADO #1744270 |
| "**UAT Global Config cannot be modified**" (error on save) | Env permission / config-control lock | Config | 26-01089759 |
| IPWS rates not displaying / code-table add errors | Wrong global config (`SEPARATE_TRANS_REPORT_TOCS`) | Config (set key = true) | 25-01015916 |
| Screen/tab labels show **wrong TSP** after TSP copy | TSP abbreviation not corrected in copy | Config (fix abbreviation) | 25-01039826 |
| Storage Transfer form: contract picklist empty | Missing **AST "ALLOW STORAGE TRANSFER"** attribute | Config (enable attribute) | 24-00985064 |
| Tab/screen/menu missing **post-hotfix** | Metadata not checked in to client layer | Config (metadata check-in / sysgen) | 26-01102793, 25-01033214 |
| "2025.10 …" batch job (PALOCEXP/CWNIGHTLY) erroring | Env **file paths** not updated for the server | Config (update file paths) | 26-01089498, 26-01089624, 24-00956879 |
| Import/Export def "columns not found in `<table>`" | File-definition vs table mismatch / def metadata | Config | 24-00955232 |

---

## 4. Location & Meter Administration (HIGH FREQUENCY)

The largest in-scope defect/config cluster (**~45 cases**). Almost everything happens on the **Location Maintenance** screen (Web or Classic). Recurring themes: (a) an **attribute is missing/unselectable**, (b) a **picklist is filtered or unscoped**, (c) a **save is blocked** by a stale dependency, (d) Web vs Classic inconsistency.

### Attribute issues
- **Nominatable not checked → location absent from nom picklist.** Parent meters added to a location group still won't appear on the nomination screen picklist unless the **Nominatable** attribute is enabled (26-01097568, root cause confirmed in resolution).
- **Interruptible attribute not selectable on data-converted locations.** Conversion seeds firm customers without the attribute row; when they switch to interruptible the business user can't check it. Fix = insert the attribute row (value `0`) into `PACTRL_LOC_ATTR` via script (26-01096011, script attached to case).
- **AST "ALLOW STORAGE TRANSFER"** must be enabled or the Storage Transfer Maintenance contract picklist returns nothing (24-00985064).
- **OBA / wheeling point setup** (flip a receipt point to OBA, populate PDAs on level 5 & 101) is a configuration walkthrough, not a defect (25-01017985 — bi-directional/OBA on TSP1000).
- **Location Purpose** values (e.g., "Mainline", "Both Receipt and Delivery") are config — add/adjust on the screen (24-00953203, 25-01051467).

### Save-blocked
- **Expired-but-open Accounting Month** blocks saving any location tied to it (Web *and* Classic). Close the month in Code/Decode Value Maintenance and refresh cache (25-01035258 — see §9).

### Web vs Classic
- **Same-name locations** couldn't be saved in **Web** (common for LDC parent/child) — fixed in **2022.10** (24-00958301 / ADO #1670884). Workaround was renaming in Classic.
- **Segment change** made in **Web** updated the *new* location group but not the *old* one and broke contract subscribed-segments; doing it in **Classic** updated all tables correctly (24-00939083 / ADO #1651001, Bug Closed).

### Upgrade-driven
- **States don't populate** in Location Maintenance after a **1.0→1.5** upgrade — the non-sysgen view referencing `QCODE_STATE`/`SCODE_STATE` was not regenerated. Fix = manually recreate the non-sysgen view, drop the auto-reg sysgen, run a **full sysgen**, then fold steps into a post-upgrade DB script in the cutover playbook (24-00972277).
- **Unscoped picklist** that existed in v16 missing in the new version — config/metadata re-enable (24-00950009, 25-01045900).

### Deletions (→ §5 / §15)
Removing meters/locations is generally a **Cloud-Ops script** because the UI blocks it (child meters 26-01096669, meter removal 25-01036047, location cleanup 26-01097582).

### Diagnostic
```sql
-- Is the location active for the gas day, and what attributes does it carry?
SELECT TSP_NO, LOC_ID, LOC_NM, LOC_STATUS_CD, EFF_DT_FROM, EFF_DT_TO
FROM   PACTRL_LOC WHERE TSP_NO = <TSP_NO> AND LOC_ID = '<LOC_ID>';

SELECT TSP_NO, LOC_ID, LOC_ATTR_CD, ATTR_VAL
FROM   PACTRL_LOC_ATTR
WHERE  TSP_NO = <TSP_NO> AND LOC_ID = '<LOC_ID>'
ORDER  BY LOC_ATTR_CD;   -- look for missing NOMINATABLE / INTERRUPTIBLE / OBA rows
```
> Table/column names follow the QPTM `PACTRL_LOC*` convention confirmed by the verbatim scripts in §15 (`PACTRL_LOC_GRP`, `PACTRL_LOC_GRP_ASSOC_QTY`, `PACTRL_LOC_ATTR`). Verify exact column names against the target schema before scripting.

---

## 5. Location Groups & Zones

### "I need to delete a Location Group" — the canonical pattern
QPTM **does not allow location groups to be deleted in the UI** once created (even seconds after, even with zero transactional data) — the user gets a generic "cannot be deleted" error (26-01064296). Inactive groups also **are not filtered out of picklists**, causing confusion (25-01047587). The standard disposition is a **targeted Cloud-Ops delete script** against `PACTRL_LOC_GRP` (+ its `_ASSOC_QTY` child). The verbatim script is in **§15, Template L**.

Procedure:
1. Confirm `TSP_NO`, the exact `LOC_GRP_ID`, and that **no transactional data** references the group (client usually asserts this; verify with diagnostic SQL below).
2. Provide the delete script to Cloud Ops (raise a **Request Global Cloud Ops** WI — e.g., ADO **#1780227** deployed `WWM_Loc_Grp_ID_Delete_Script.sql` to `WWM_PRDA1MID_QPTM`, bypassing UAT, for case 26-01064296).
3. For **bulk** inactive-group cleanup (OkTex, 25-01047587), the same two-table delete is parameterized over a list pulled from `PACTRL_LOC_GRP` for the TSP.

### Other location-group / zone issues
- **Locations missing from a loc-group picklist** on the nom screen → the meter lacks the **Nominatable** attribute, *not* a group problem (26-01097568).
- **Web segment change not propagating to the old location group** — defect, do it in Classic (24-00939083 / ADO #1651001).
- **Inactive zones for IPWS** — the system blocks setting up a zone that is *intended* to be inactive; workaround is set up active then backdate, or script the inactive zone/meter rows (25-01052893, OkTex OK-8). "Remove requirement for zones" is a **code-table** config change (26-01081758).

### Diagnostic
```sql
-- The location group and whether it carries associated-quantity rows (must clear those first)
SELECT TSP_NO, LOC_GRP_ID, LOC_GRP_NM, ACTV_IND
FROM   PACTRL_LOC_GRP WHERE TSP_NO = <TSP_NO> AND LOC_GRP_ID = '<LOC_GRP_ID>';

SELECT COUNT(*) AS ASSOC_QTY_ROWS
FROM   PACTRL_LOC_GRP_ASSOC_QTY
WHERE  TSP_NO = <TSP_NO> AND LOC_GRP_ID = '<LOC_GRP_ID>';
-- List all Inactive groups for a TSP (bulk-cleanup candidates)
SELECT TSP_NO, LOC_GRP_ID, LOC_GRP_NM FROM PACTRL_LOC_GRP
WHERE  TSP_NO = <TSP_NO> AND ACTV_IND = 0 ORDER BY LOC_GRP_ID;
```

---

## 6. Code Tables / Picklists / Dropdowns

Two screens drive almost every dropdown/picklist case:
- **Code Table Definition Maintenance** (SOA .NET) — defines the numbered code table, its columns, and the **Displayed Column Order**.
- **Code / Decode Value Maintenance** — the actual values (e.g., Penalty Types, Accounting Months).

### Diagnostic patterns
| Symptom | Root cause | Fix | Case |
|---------|-----------|-----|------|
| Dropdown has options but the selection **won't stick / display** | Code table **Displayed Column Order** not assigned | Assign Displayed Column Order on the Penalty Type code table (**26204**) | 24-00984137 / ADO #1692629 |
| Dropdown **completely empty** in UAT (Penalty Type Underrun/Overrun) | Code-table **definition row missing** | Add a code-table definition for table **26204** | 24-00967113 |
| TT/Trans-Type field blank on Nom Submission | Pooling TOS x-ref missing; `QCODE_ACTN` vs `KCTRL_TOS` **name + descr must match** | Nom Config System Pref + align the two tables | 26-01095071 |
| Can't add code-table values; IPWS rates show only some | Wrong global config gating the report TOCs | Set `SEPARATE_TRANS_REPORT_TOCS = true` | 25-01015916 |
| "Remove requirement for zones" | Zone requirement enforced via code table | Code-table change | 26-01081758 |
| Accounting Month wrongly **open** (blocks loc save) | Code/Decode value left open past expiry | Close the month (see §9) | 25-01035258 |

> **Heuristic:** dropdown shows values but won't **retain** → Displayed Column Order. Dropdown is **empty** → missing code-table *definition* or *value* row. Field expects a pre-populated value but is blank → a missing **cross-reference** (e.g., pooling TOS x-ref, `QCODE_ACTN`/`KCTRL_TOS` mismatch).

---

## 7. Global & TSP Configuration Keys / System Preferences

Config keys are key/value pairs read by the middletier from the config-control table (`qarch_cnfg_ctrl`) and grouped by key-group. A **missing** key is non-fatal — the middletier logs `QConfigMgrBase.GetConfigKey.Missing` and uses a hard-coded default.

### Recurring cases
- **Missing-key log flood** (25-01031118 / ADO #1744270, ETC). Real keys observed missing: `NOMINATIONS / NUM_STREAMING_OBJECTS`, `NAESB / NAESB30` (Boolean default `1`), `TSP / SHOW_UP_DN_CONTRACT_PICKLIST_IN_GRID`, `NOMINATIONS / DISABLE_NOMINATION_SUBMISSION_BY_CONTRACT`. Disposition: create the keys in `qarch_cnfg_ctrl` with their default values so the middletier stops logging; engineering confirms the code default for each.
- **Config can't be modified in UAT** — error on save of a global config setting (26-01089759); environment permission / config-control state.
- **Behavior-gating keys** referenced by other clusters: `SEPARATE_TRANS_REPORT_TOCS` (IPWS rate display, 25-01015916). For EDI/nom keys (`SEND_NMST_QUICK_RESPONSE`, `BLOCK_BI_NOM_SUBMISSION`, etc.) see the EDI/Nominations skills — don't duplicate here.

### Diagnostic
```sql
-- Does a config key exist, and what is its value? (config-control table)
SELECT KEY_GRP_NM, KEY_NM, KEY_VAL, TSP_NO
FROM   qarch_cnfg_ctrl
WHERE  (KEY_GRP_NM = '<GROUP>'  -- e.g. 'NOMINATIONS','NAESB','TSP'
   AND  KEY_NM    = '<KEY>')
ORDER  BY KEY_GRP_NM, KEY_NM;

-- All keys for a group, to spot what's defined vs defaulting
SELECT KEY_GRP_NM, KEY_NM, KEY_VAL FROM qarch_cnfg_ctrl
WHERE  KEY_GRP_NM = '<GROUP>' ORDER BY KEY_NM;
```
> Some references in this knowledge base call the same store `QARCH_GLOBAL_CONFIG` / `QARCH_TSP_CONFIG`; the middletier log names the physical table `qarch_cnfg_ctrl`. Confirm the physical name in the target DB.

---

## 8. TSP / Pipeline Setup & TSP-Copy

New TSPs are frequently seeded by **copying an existing TSP**, which can carry the source TSP's labels and abbreviation.
- **Screen/tab labels show the wrong (source) TSP** after a copy — e.g., Pinyon (#327) showing **TPC** instead of **PPC**. Fix = correct the **TSP #327 abbreviation** (25-01039826).
- **TSP number formatting in batch params** — TSP No rendered comma-separated in the BLGENARAP parameters screen (24-00947575, config).
- New-pipeline / expansion setup (JISH 26-01080461, data conversion of BAs/Locations/Contract Templates) is **project/conversion work**, often staged in UAT/conversion envs.

### Diagnostic
- Verify the TSP abbreviation and label metadata against the intended values after any TSP copy.
- Search ADO TSP-copy WIs (cluster around #1739167–#1739172, #1605559, #1597732, #1391716/#1391717) for the copy procedure used.

---

## 9. Calendar / Accounting Month / Cycle Setup

Lowest-volume in-scope cluster, but one high-impact pattern:
- **Expired Accounting Month left open blocks Location saves.** Saving a Location linked to an Accounting Month that has already closed fails in **both Web and Classic**. Root cause: the month is still marked **open/active** in **Code / Decode Value Maintenance**. Fix: close the expired months, refresh the cache, then the Location saves (25-01035258 — Software Defect dispositioned as Configuration Changed).
- Cycle/deadline setup itself (PACTRL_CYCLE_DEADLINE, late-nom) is owned by **SKILL_EDI_Troubleshooting.md §4/§6** and **SKILL_Nominations.md §11** — cross-link, do not duplicate.

### Diagnostic
```sql
-- Accounting Months and their open/closed state (Code/Decode-backed)
SELECT ACCTG_MONTH, ACCTG_YEAR, OPEN_CLOSE_IND, EFF_DT_FROM, EFF_DT_TO
FROM   <accounting-month code/decode table>   -- via Code/Decode Value Maintenance
ORDER  BY ACCTG_YEAR, ACCTG_MONTH;
-- Red flag: an expired month with OPEN_CLOSE_IND still = open.
```

---

## 10. Install / Upgrade / Hotfix / Deployment / Metadata Packaging

**The single largest subject cluster (~62 of 323 by keyword)**, but mostly **routine packaging / deployment** rather than product defects. Most are titled by build (e.g., "QPTM: July 2025 Support Hotfix to 2024.04", "2025.10 - …"). They are dispositioned as Configuration Changed / Software Update Available. Triage them as **deployment work**, not code bugs.

### Recurring patterns
- **Missing screens / tabs / menu trees after an upgrade or hotfix** — client metadata wasn't checked in / packaged. E.g., **Credit Rating tab missing post UAT Hotfix #1** → added metadata check-ins into the client layer (QNJR) (26-01102793). **Process Type / Report Type screens & ESUITE menu tree** absent in 2025 version → must be set up in the client metadata layer / Menu Editor (25-01033214).
- **Upgrade-broke-a-view** — 1.0→1.5 sysgen view not regenerated → run a **full sysgen** + post-upgrade script (24-00972277, see §4).
- **Conversion cleanup** — master metadata check-in tickets, data conversion of BAs/locations/contract templates (24-00953365, 26-01080461).
- **Packaging-issue root causes** exist as their own SF root-cause values (Packaging Issue – Code/Metadata/Database Scripts/Sysgen) — small counts but always a deployment fix, never a config the client can self-serve.

### Disposition guidance
1. Identify the **build/hotfix** and **environment**.
2. If a screen/tab/process/report is "missing," it's almost always a **metadata check-in / sysgen** gap in the **client layer** — package it; don't look for a code bug.
3. Fold any manual DB step into the **cutover playbook / post-upgrade scripts** so it survives the next hotfix (explicit lesson from 24-00972277).

---

## 11. File Paths, Batch-Job Config, Services & Connectivity

These ride alongside install/upgrade and are overwhelmingly **environment configuration**, not code.

| Symptom | Root cause | Fix | Case |
|---------|-----------|-----|------|
| `PALOCEXP` / `CWNIGHTLY` / `PALOC` job erroring after a build | Env **file paths** not pointed at the correct server | Update file paths | 26-01089498, 26-01089624, 24-00956879 |
| IPWS SFTP / FTP transfer failing, SFTP creds | Env credentials / transfer-def config | Cloud Ops config | 26-01089631, 26-01084956, 26-01082639 |
| Import/Export def: "columns not found in `<table>`" (e.g., `ALCTRL_ANALYSIS`) | File-definition vs table mismatch in def metadata | Config (fix import def) | 24-00955232 |
| Service account password change broke a service / login | Pwd not synced to DB schema / service config | Config + doc (TSA annual pwd change) | 24-00993802, 26-01098713, 25-01029206 |
| "Unable to access OData Service" opening Web screens | Service/endpoint config | Config | 25-01031839 |
| Max sequences hitting limit | Sequence config/maintenance | Documentation provided | 24-00936702 |

> These are typically routed to **Managed Services / Cloud Ops**. L4's job is to confirm it's an env/file-path/credential issue and hand off — not to chase a product bug.

---

## 12. Key Code Files & Repos

| Repo / area | Relevance |
|-------------|-----------|
| `Quorum.QPTM.Web` (41e317c0-844c-4728-98da-529092957738) | Location Maintenance, Code Table Definition Maintenance, Storage Transfer, Penalty Submission Web screens; same-name & segment-sync defects |
| `Quorum.QPTM.ClassicGUI` | Classic Location/Code-Decode screens (the Web/Classic divergence cases) |
| `<CLIENT>.QPTM.Metadata` | **Client metadata layer** — screens/tabs/menu trees/import-export defs/process & report types; source of "missing after hotfix" cases (always check before assuming a code bug) |
| `<CLIENT>.QPTM.Database` | Client DB scripts incl. post-upgrade / cutover scripts (24-00972277) |
| Middletier config: `QConfigMgrBase` | Emits `GetConfigKey.Missing` for absent keys (25-01031118) |
| `APL.QPTM.Database` (2e1fb9e5-…), `Quorum.QGM.Database` (8bfba59c-…) | Schema, code-table & migration scripts |

> Code search: `{"searchText":"PACTRL_LOC_GRP repo:<CLIENT>.QPTM"}`, `{"searchText":"GetConfigKey.Missing"}`, `{"searchText":"DisplayedColumnOrder code table"}`.

---

## 13. Database Tables Reference

| Table | Purpose |
|-------|---------|
| `PACTRL_LOC` | **Location/meter master** (status, eff dates, purpose) |
| `PACTRL_LOC_ATTR` | **Location attributes** (Nominatable, Interruptible, OBA, AST) — missing rows cause "attribute not selectable" (26-01096011, 26-01097568) |
| `PACTRL_LOC_GRP` | **Location group master** (delete blocked in UI → §15 Template L) |
| `PACTRL_LOC_GRP_ASSOC_QTY` | Location-group associated-quantity child — **delete before parent** |
| `qarch_cnfg_ctrl` | **Config-control table** (global & TSP keys; a.k.a. QARCH_GLOBAL_CONFIG/QARCH_TSP_CONFIG) |
| Code Table Definition (table id e.g. **26204** Penalty Type) | Defines columns + **Displayed Column Order** (24-00984137, 24-00967113) |
| Code / Decode Value Maintenance store | Code values incl. **Accounting Months** (25-01035258) |
| `QCODE_ACTN` / `KCTRL_TOS` | Action codes / Type-of-Service — **name + descr must match** (26-01095071) |
| `QCODE_STATE` / `SCODE_STATE` | State code views — sysgen regen needed after 1.0→1.5 (24-00972277) |
| `ALCTRL_ANALYSIS` | Gas-quality analysis table referenced by IPWS import/export defs (24-00955232) |

> Table/column names verified against the verbatim Cloud-Ops scripts in §15 and the middletier missing-key log. Always confirm exact column names against the target schema before running anything.

---

## 14. Diagnostic SQL Queries

### A. Location attribute audit (most-used)
```sql
SELECT a.LOC_ID, a.LOC_ATTR_CD, a.ATTR_VAL, l.LOC_NM, l.LOC_STATUS_CD
FROM   PACTRL_LOC_ATTR a
JOIN   PACTRL_LOC l ON l.TSP_NO = a.TSP_NO AND l.LOC_ID = a.LOC_ID
WHERE  a.TSP_NO = <TSP_NO> AND a.LOC_ID = '<LOC_ID>';
-- Missing NOMINATABLE row → not on nom picklist (26-01097568)
-- Missing INTERRUPTIBLE row → attribute not selectable (26-01096011)
```

### B. Location group + dependency check (pre-delete)
```sql
SELECT g.LOC_GRP_ID, g.LOC_GRP_NM, g.ACTV_IND,
       (SELECT COUNT(*) FROM PACTRL_LOC_GRP_ASSOC_QTY q
        WHERE q.TSP_NO = g.TSP_NO AND q.LOC_GRP_ID = g.LOC_GRP_ID) AS ASSOC_QTY_ROWS
FROM   PACTRL_LOC_GRP g
WHERE  g.TSP_NO = <TSP_NO> AND g.LOC_GRP_ID = '<LOC_GRP_ID>';
```

### C. Config key lookup
```sql
SELECT KEY_GRP_NM, KEY_NM, KEY_VAL, TSP_NO FROM qarch_cnfg_ctrl
WHERE  KEY_NM IN ('NUM_STREAMING_OBJECTS','NAESB30',
                  'SHOW_UP_DN_CONTRACT_PICKLIST_IN_GRID',
                  'DISABLE_NOMINATION_SUBMISSION_BY_CONTRACT',
                  'SEPARATE_TRANS_REPORT_TOCS')
ORDER  BY KEY_GRP_NM, KEY_NM;   -- absent row = middletier is defaulting it
```

### D. QCODE_ACTN vs KCTRL_TOS alignment (blank TT dropdown — 26-01095071)
```sql
SELECT a.ACTN_CD, a.ACTN_NM, a.ACTN_DESCR FROM QCODE_ACTN a ORDER BY a.ACTN_CD;
SELECT t.TOS_CD, t.TOS_NM, t.TOS_DESCR  FROM KCTRL_TOS  t ORDER BY t.TOS_CD;
-- The pooling TOS NM + DESCR must match between the two; mismatch blanks the field.
```

---

## 15. Verbatim Cloud-Ops Scripts (redacted)

> Concrete TSP/loc-group/value tokens replaced with `<PLACEHOLDER>`; **real table names, columns, and delete ordering are kept intact.** Always run the existence/verify check and confirm the row count before deleting. **Delete child (`_ASSOC_QTY`) before parent.**

### Template L — Location Group hard-delete (`PACTRL_LOC_GRP`)
> Source (verbatim): ADO **#1778532** / **#1780227** `WWM_Loc_Grp_ID_Delete_Script.sql` (case 26-01064296, deployed to `WWM_PRDA1MID_QPTM`). The exact reconstructed text (real values were `TSP_NO = 505`, `LOC_GRP_ID = 'PLA'`):

```sql
-- Location Group delete (redacted) — child quantity rows FIRST, then the group
IF EXISTS (SELECT 1 FROM PACTRL_LOC_GRP_ASSOC_QTY
           WHERE TSP_NO = <TSP_NO> AND LOC_GRP_ID = '<LOC_GRP_ID>')
    DELETE FROM PACTRL_LOC_GRP_ASSOC_QTY
    WHERE LOC_GRP_ID = '<LOC_GRP_ID>' AND TSP_NO = <TSP_NO>;

IF EXISTS (SELECT 1 FROM PACTRL_LOC_GRP
           WHERE TSP_NO = <TSP_NO> AND LOC_GRP_ID = '<LOC_GRP_ID>')
    DELETE FROM PACTRL_LOC_GRP
    WHERE LOC_GRP_ID = '<LOC_GRP_ID>' AND TSP_NO = <TSP_NO>;
```
> **Bulk inactive-group cleanup (25-01047587):** same two-table delete, looped over the list of inactive `LOC_GRP_ID`s pulled from `PACTRL_LOC_GRP` for the TSP (verify each is unreferenced first).

### Template M — Add a missing Location attribute row (`PACTRL_LOC_ATTR`)
> Source: case 26-01096011 (script attached to SF; reconstructed pattern). Data-conversion missed the attribute row, so the UI can't toggle it. Insert the attribute with value `0` (unchecked) so it becomes selectable:

```sql
-- Make the <ATTR> attribute selectable on converted locations (default unchecked = 0)
INSERT INTO PACTRL_LOC_ATTR (TSP_NO, LOC_ID, LOC_ATTR_CD, ATTR_VAL)
SELECT <TSP_NO>, l.LOC_ID, '<ATTR_CD>', 0      -- e.g. '<ATTR_CD>' = INTERRUPTIBLE
FROM   PACTRL_LOC l
WHERE  l.TSP_NO = <TSP_NO>
  AND  l.LOC_ID IN (<CONVERTED_LOC_LIST>)
  AND  NOT EXISTS (SELECT 1 FROM PACTRL_LOC_ATTR a
                   WHERE a.TSP_NO = l.TSP_NO AND a.LOC_ID = l.LOC_ID
                     AND a.LOC_ATTR_CD = '<ATTR_CD>');
```
> Verify the exact column names (`LOC_ATTR_CD` / `ATTR_VAL`) against the target schema; the binary value column may differ by version.

---

## 16. Known Historical ADO Bugs

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|-------|--------------|-----------------|---------|---------|
| **#1651001** | Bug / **Closed** | TEP — In Web, Location Groups not updated with a segment change (Classic works) | §4/§5 | 24-00939083 |
| **#1670884** | Bug / **Closed** | ONG — Location Maintenance same-name bug in Web (fixed 2022.10) | §4 | 24-00958301 |
| **#1692629** | Bug / **Closed** | GBG — Penalty Type dropdown not retaining selection (Displayed Column Order) | §6 | 24-00984137 |
| **#1744270** | Bug / **Closed** | ETC — Add missing Global/TSP config keys with defaults | §7 | 25-01031118 |
| **#1778532** | Requirement / **Closed** | WWM — Need to delete a Location Group (UI blocks delete) | §5 | 26-01064296 |
| **#1780227** | Request Global Cloud Ops / **Closed** | WWM — Deploy Location Group delete script to PRD (bypass UAT) | §5/§15 | 26-01064296 |

> Takeaway: the **delete-config-object** cases are dispositioned operationally (Cloud-Ops delete script), not via a product fix. The genuine **code** fixes in scope are the **Web/Classic Location Maintenance divergences** (#1651001 segment sync, #1670884 same-name) and **code-table display** (#1692629). Many config cases have **no ADO bug** — they're self-serviceable config changes.

---

## 17. Expected Behavior / User Education

Root Cause = Customer Error / Training (~120 cases in scope). Recognize these before scripting/escalating.

| Reported as | Reality | Case |
|-------------|---------|------|
| "Locations missing — picklist opens with filters" | Working as designed — picklist applies default & date filters | 26-01099866 |
| "Location won't save" | An **expired Accounting Month is still open** — close it, then save | 25-01035258 |
| "Can't delete a location group / zone / child meter" | UI **blocks deletes by design** — needs a Cloud-Ops script (§5/§15) | 26-01064296, 26-01096669 |
| "Config key missing" warnings flooding logs | **Non-fatal** — middletier uses defaults; create keys only to quiet logs | 25-01031118 |
| "How do I set up an OBA / wheeling point?" | Configuration walkthrough (flip to OBA, populate PDAs L5 & 101) | 25-01017985 |
| "Tabs/screens missing after upgrade" | **Metadata not checked in** to the client layer — package it | 26-01102793, 25-01033214 |
| "Wrong TSP label after copy" | TSP-copy carried source abbreviation — correct it | 25-01039826 |
| "Salesforce product dropdown changed" | Not a QPTM issue at all — SF picklist config | 25-01005035 |

**Tell-tale that it's config/expected:** the object can't be *deleted* (by design), an attribute/key/code-table row simply needs to be *added/enabled*, or a screen is *missing after a build* (packaging, not a defect).

---

## 18. Escalation Decision Tree

```
Pipeline-Admin / Config case reported
│
├─ Tied to a build/hotfix/upgrade ("2025.10", "2024.04", "1.0→1.5")?  (§10/§11)
│   ├─ Screen/tab/process/menu missing? → metadata check-in / sysgen in CLIENT layer (not a bug)
│   ├─ Batch job (PALOCEXP/CWNIGHTLY) erroring? → env FILE PATHS (Cloud Ops)
│   └─ View/sequence broke on upgrade? → re-sysgen + post-upgrade script in cutover playbook
│
├─ "Delete this location group / zone / child meter / location"?  (§5/§15)
│   ├─ Confirm TSP + ID + no transactional refs (diagnostic §14B)
│   └─ Provide Cloud-Ops DELETE script (Template L) → Request Global Cloud Ops WI
│
├─ Location/meter won't save or attribute missing?  (§4)
│   ├─ "Accounting month active when expired"? → close the month (§9), refresh cache
│   ├─ Attribute not selectable (Interruptible/Nominatable/AST)? → add PACTRL_LOC_ATTR row (Template M) / enable
│   └─ Web vs Classic mismatch (same-name, segment sync)? → known code defect (#1670884/#1651001) — workaround in Classic
│
├─ Dropdown / picklist problem?  (§6)
│   ├─ Has values but won't retain? → Code Table Definition: assign Displayed Column Order (#1692629)
│   ├─ Empty? → add code-table definition/value row (e.g. 26204)
│   └─ Pre-populated field blank (TT)? → fix cross-reference (pooling TOS / QCODE_ACTN↔KCTRL_TOS)
│
├─ Config key missing / can't modify global config?  (§7)
│   ├─ Log flood only? → create keys w/ defaults in qarch_cnfg_ctrl (non-urgent)
│   └─ Can't save in UAT? → env permission / config-control state (Cloud Ops)
│
├─ TSP setup / wrong labels after copy?  (§8) → correct TSP abbreviation/metadata
│
└─ File path / FTP/SFTP / service / password / OData?  (§11) → Managed Services / Cloud Ops (env config)
```

---

*Skill created: 2026-06-01*
*Based on: 323 actionable QPTM Pipeline-Admin/System-Config/Location-Admin/Installation SF cases + ADO work items #1651001, #1670884, #1692629, #1744270, #1778532, #1780227. Verbatim script captured from ADO #1778532/#1780227 (`WWM_Loc_Grp_ID_Delete_Script.sql`).*
*Companions: SKILL_Nominations.md, SKILL_EDI_Troubleshooting.md, SKILL_Security_UserAdmin.md, SKILL_Reporting_Regulatory_Postings.md. Applicable to all QPTM TSPs/clients.*
