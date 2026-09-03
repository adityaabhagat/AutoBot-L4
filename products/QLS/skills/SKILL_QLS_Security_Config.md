# SKILL: QLS Security & Access + Configuration & Code/Decode Maintenance

> **Product:** QLS (Quorum Land System) · `Product_list__c = 'My Quorum Land'` · Oracle, `lis` + `ESUITE_QFC` schemas
> **Coverage-plan groups:** #12 Security & Access (913 cases / 94 actionable) + #14 Configuration & Code/Decode Maintenance (254 / 70)
> **Sources:** all-history SF mining 2026-09-03 (5 validated category pages + 1 keyword sweep, ~150 cases surveyed, 30 deep-sampled via Resolution__c + CaseFeed), ADO org QuorumSoftware (20+ work items, verbatim fix scripts from bug bodies).
> **Note:** QLS case fix detail lives in **CaseFeed `Type='TextPost'`**, NOT CaseComment/EmailMessage (both empty for QLS — confirmed on 26-01087666, 24-00949749, 24-00976767).
> *Auto-Bot skill — built by Aditya Bhagat.*

---

## 1. QUICK TRIAGE

| Symptom heard | Jump to | Likely gate |
|---|---|---|
| "Can't log in" / infinite **Loading** spinner / 400 Login Failed / sees another client's apps | §3.1 Okta identity | G2 config (identity/data) |
| Logged in but a screen, node, widget, or module is missing/greyed | §3.2 Security objects | G2 config |
| A **batch process or report disappeared** or throws SecurityException (AFISCRTAE, CALDELEXP, RPT_*) | §3.3 BTYP security | G2 config / G3 version (Bug 1711330 family) |
| User can approve own record / Approve button behavior wrong | §3.4 Approval security | G2 config or G5 (BR package) |
| Security broke **after upgrade/refresh/QCloud move** (missing roles, sysgen, ORA-02291) | §3.5 Upgrade collateral | G2/G3 |
| User sees agreements they shouldn't (land division / subject / map polygons) | §3.6 Data security | G2 config |
| Code table **not visible** in Code/Decode Value Maintenance | §4.1 Hidden tables | G2 config |
| **"Save Failed"** / can't add-modify-delete a code value | §4.2 Save failures | G4 data or G5 (see fixed-in list) |
| Dropdown blank / wrong column order / decode shows raw code | §4.3 CDTBL_DEFINE_COL | G2 config |
| Config key questions (CheckRoleForApproval, MAX_AUDIT_RECORDS...) | §4.4 Config Settings | G2 |
| Audit History empty/stale | §4.5 Audit | G2/G3 (Bug 1662922) |
| "Please add values to table X" (agreement types, legal entity, client tables) | §4.6 Business adds | Expected behavior / script service |

**Environment naming seen in these cases:** `QINT_<CLIENT3>_DEV17QLS`, `QINT_<CLIENT3>_DEVA1QLS`, `QCLD_<CLIENT3>_QLSA1_PRD`, URLs `<CLIENT>L_HD_DEV17_QLS`. Clients in evidence: HEC (Hilcorp), PHL (Phillips 66), TEP (Tallgrass), EQC/ENB (Enbridge), EQN (Equinor), HES (Hess), XTO, RRC, XOM, SPR, DMB, MAC, COP, SRC (Sandridge), UBT, INV (Invenergy — support suspended 2026-06), BHE.

---

## 2. DECISION TREE

```
Access complaint?
├─ Cannot even open QLS (login/Loading) ──────────► §3.1  Check Okta↔QARCH_SEC_USER identity first
├─ In QLS, but something missing/greyed
│   ├─ Screen/node/widget/module ────────────────► §3.2  Missing QARCH_SEC_OBJECT privilege or module
│   ├─ Batch process / report ───────────────────► §3.3  BTYP/RPT security row missing (post-2024 standardization)
│   └─ Approve button / approval flow ───────────► §3.4  CheckRoleForApproval + CANAPPROVEAGREEMENT + BR packages
├─ Broke after upgrade / env move / refresh ─────► §3.5  sysgen, sequence reseed, security push scripts, core groups
└─ Sees TOO MUCH (data security) ────────────────► §3.6  LAND/SUBJ privileges, GRP vs USER mode

Code/decode complaint?
├─ Table not listed on screen ───────────────────► §4.1  QARCH_CDTBL_DEFINE.HIDDEN_TBL_IND + CODE security object
├─ Save Failed / can't delete ───────────────────► §4.2  Match against known-defect list before investigating
├─ Column/dropdown wrong ────────────────────────► §4.3  QARCH_CDTBL_DEFINE_COL (layer-aware)
├─ Behavior of a config key ─────────────────────► §4.4
├─ Audit history ────────────────────────────────► §4.5
└─ "Add rows/table for us" request ──────────────► §4.6  Script service, not a defect
```

**The QLS security model (verified from bug bodies + case feeds):**
- `QARCH_SEC_USER` — user record incl. **email** (the Okta join key). `QARCH_SEC_GRP` / `QARCH_SEC_GRP_MEMBER` — groups + membership. `QARCH_SEC_USER_MOD` — module assignments. (Anchor: case 26-01106173 feed.)
- `QARCH_SEC_OBJECT` — securable objects. `OBJECT_TYPE_CD` values seen: `BTYP` (batch type), `CODE` (code table), `OTH` (action, e.g. FINANCIALDETAIL.CHANGESTATUS), `LAND` (land division), `SUBJ` (subject type), plus Form-tab screen objects. (Anchors: 26-01116490 feed, Bugs 1782450, 1732044, 1716392.)
- `QARCH_SEC_GRP_PRIVILEGE` / `QARCH_SEC_USER_PRIVILEGE` — grants with `ALLOW_QRY_IND / ALLOW_ADD_IND / ALLOW_DELETE_IND / ALLOW_UPDATE_IND / ALLOW_EXECUTE_IND`. A config decides whether land-div/subject security is evaluated at GRP or USER level (Bug 1716392).
- Known group IDs: **37005** Land Administrator, **37009** View Only, **50030** Financial Processing, **67000** Land Advisor (DMB-specific). (Bugs 1782450, 1732044; case 24-00986832.)
- After ANY security change: **Cache Maintenance → refresh eSuite + Land caches**, user closes screens and re-logs; service/app-pool restart if cache refresh isn't enough (24-00986832 feed).

---

## 3. SECURITY & ACCESS CLUSTERS

### 3.1 Login failures & infinite "Loading" — Okta ↔ QLS identity mismatch
**Signature:** user gets stuck on "Loading" and the QLS window never opens; or 400 Login Failed; or logs in and sees the WRONG client's dashboard apps; or new user absent from Okta.
**Root causes (all CONFIRMED from resolutions):**
- **Duplicate Okta/app accounts** for one person: correct account plus stray auto-created ones → app security maps to the wrong record. Fix = script to inactivate duplicates in QLS + clean duplicate emails, keep privileges on the correct account. (26-01087666 Enbridge — "duplicate users present in the application security tables… updated security ID's and email addresses to properly map to Okta"; 25-01053546 PHL — duplicated users, Script Review ADO **1787526** "Inactivate and clean duplicated users", Cloud Ops WIs 1765587/1766676/1778321/1782978.)
- **Two accounts sharing one email address** → mapping conflict → endless Loading (24-00976108 PHL: an app-support account and a user account shared the same email — "This is the root cause… change the email address for one of the accounts").
- **Contractor vs employee email drift**: profile created against old email; reset/recreate the profile or script-correct it in PRD+UAT (26-01106173 TEP; Cloud WI 1821389).
- **Duplicate user id shows ANOTHER CLIENT'S apps** in myQuorum dashboard — cross-tenant symptom, Okta team renames the user id (24-00985922: id suffixed `_2`).
- **Expired federation certificate** → 400 Login Failed: client's Azure/ADFS federated SSO cert expired; renew, then Quorum syncs Okta (25-01014488). SAML cert renewals are routine (25-01009624).
- **Bad Okta config change** → whole client can't log in; roll back Okta config (26-01086709 BHE). Plain password reset also occurs (26-01088873).
**Triage order:** 1) is it one user or all users? (all → Okta config/cert; one → identity row). 2) Compare `QARCH_SEC_USER` email vs Okta profile email. 3) Look for duplicate rows (SQL below). 4) Route account create/disable to Cloud Ops (myQuorum Cloud WI), scripts through Script Review.

### 3.2 Logged in, but screens / nodes / widgets / modules missing
**Signature:** specific node or button absent or greyed for some users; "Missing access within QLS"; read-only users can't use a feature.
**Confirmed object-to-symptom map:**
| Missing thing | Security object / fix | Anchor |
|---|---|---|
| Prospect node | `QVIEWRELATEDASSET` object missing from user privileges | 25-01052616 |
| eCal widgets — read-only users can't save searches | Add `QLSWIDGETACCESS` (Form tab, Security Group Setup) to group 37009 with Allow Query + Allow Execute; refresh eSuite+Land cache; restart services if needed | 24-00986832 |
| Agreements not viewable at all | User lacks the **Land Division module** (Security Workspace subject) | 26-01102514 |
| Everything missing | User in NO security groups/modules at all (fresh user, incomplete provisioning) | 26-01067720 |
| QLS Maintenance app won't open | Okta group grant (Cloud side), or NTFS/local-group permission on the app server (V17) | 25-01046587, 25-01031493 |
| All users have TOO much (super-user) | Group privileges over-granted; rebuild per role matrix | 25-01019783 |
**Known defect:** users assigned to a new group did not inherit its privileges (24-00949749, Software Defect, Hess-era 2024; no public resolution text — treat recurrence as possible product defect, check current build before scripting).
**Fix recipe (generic):** Security Group Setup → find object on the correct tab (Form/Code/Batch/Report) → grant ALLOW_* flags to group → Cache Maintenance refresh (eSuite + Land) → user relog. Prefer group-level grants; user-level only for exceptions.

### 3.3 Batch processes / reports missing or SecurityException — the BTYP cluster
**Signature:** a batch process vanished from the Batch Processes screen ("AFIS Create Accounting Entries no longer appears — we cannot process payments"), or a role can't see/execute one; report viewing blocked by SecurityException.
**Root cause (CONFIRMED):** 2024+ configuration-standardization enabled **batch- and report-level security** (previously only Batch-Type level). Rows missing from `QARCH_SEC_OBJECT` (`OBJECT_TYPE_CD='BTYP'`) / `QARCH_SEC_GRP_PRIVILEGE` hide the process. Bug **1711330** "QLS - Batch Processes - Missing/Additional batch processes after configuration standardization changes are deployed" (Closed; resolution added batch-process security sync + metadata to add/remove batch processes from `QLS_QFCONL` and `ESUITE_QFC`).
**Verbatim fix pattern** (case 26-01116490 feed, UPG env — adapt object/group):
```sql
insert into QARCH_SEC_OBJECT (OBJECT_ID, OBJECT_TYPE_CD, MODULE_CD, OBJECT_NM, USER_ID, UPDT_DT, APP_LAYER_CD, OWNER_ID, ISSUE_ID, AUDIT_COMMENTS, HIST_IDX)
values ('INTERFACES', 'BTYP', 'QLS', 'INTERFACE PROCESSES', '<OPER>', sysdate, 'QLS', null, '1711330', null, '');
insert into QARCH_SEC_GRP_PRIVILEGE (GRP_ID, OBJECT_ID, OBJECT_TYPE_CD, MODULE_CD, ALLOW_QRY_IND, ALLOW_ADD_IND, ALLOW_DELETE_IND, ALLOW_UPDATE_IND, ALLOW_EXECUTE_IND, USER_ID, UPDT_DT, APP_LAYER_CD, ISSUE_ID, AUDIT_COMMENTS, HIST_IDX)
values (50030, 'INTERFACES', 'BTYP', 'QLS', 0, 0, 0, 0, 1, '<OPER>', sysdate, 'QLS', '1711330', null, '');
```
**Related cases/bugs:** 26-01116116 (AFIS process disappeared after an HF + script; service restart did NOT fix — security rows did), 26-01116490 (enable AFISCRTAE for Financial Processor role 50030), Bug **1713292** CALDELEXP export batch missing security mappings (hotfixed 2022.04→2024.10, script `1713292.001.QLS.CALDELEXP_SecurityMappings.SQL`), 26-01103127 RPT_1029 SecurityException blocks View Invoice, 26-01106286 Document Export security error after upgrade (Software Defect).
**Rule:** if a batch/report disappeared right after a hotfix or standardization deploy, do NOT chase services/QPEC — check the BTYP security rows first.

### 3.4 Approval security & segregation of duties
- **Stop a role from approving:** removing the `CANAPPROVEAGREEMENT` object from the group is NOT enough. Also duplicate the `CheckRoleForApproval` key row on **Land: Configuration Settings** with `Metadata Layer = QDMB` (use the client layer), `Key Value = 1`, save, then Cache Maintenance "refresh all". Approve button then greys out. (24-00976767 verbatim recipe.)
- **User can approve their own record** when the app service (PRD) user touches it between submit and approve: business-rule proc **`ESUITE_QCNX.BR_APPROVAL_AGMTDET`** updated to exclude service users and to block anyone who modified since last Approved state (24-00939606, script → metadata check-in for future hotfix; CNX client layer).
- **"Row 88" error approving an existing agreement:** script update to **`ESUITE_QDMB.BR_APPROVAL_URL_LINK_QDMB`** to not pull two config values; long-term in patch (24-00949049).
- **Approval rule check skipped when saving at sub level** — Software Defect, **fixed in the 2025.04 release** (23-00924844).
- **Approval rules not mapped to all subject types** after adding obligations: corrective scripts (25-01050003 — payments to fed/state payees "will not Approve").

### 3.5 Upgrade / environment-move security collateral
- **Group Security screen crashes / Security Setup by User unviewable after QCloud migration:** environment configuration missing → **full sysgen run** fixes (24-00978250).
- **Missing metadata layers after upgrade:** client metadata profile in the web `.ini` misspelled (`GE` vs `GEC`) and NI flag unchecked (26-01099460).
- **Roles differ between environments** (Dev 59 vs Test 40): run security push scripts Dev→Test (24-00946879 Hess).
- **Unable to add/copy users in one env** ("copy" and "new" both error, Message Center shows details): Oracle **sequences out of sync — reseed** (25-01040350). Same family as `arrg_key` sequence reseed for CREATE AGREEMENT errors (24-00961597).
- **DB patch/upgrade dies with `ORA-02291 (ESUITE_QFC.FK_QARCH_SEC_OBJECT1) parent key not found`** running CORE script `QLS_17.0.00.0027.0000_019_CORE_QFCENGS_019_1752685.sql`: mixed-case object id (`FinancialDetail.ChangeStatus`) vs upper-case merge key. Pre-run script merges the UPPER row into `QARCH_SEC_OBJECT`, repoints `QARCH_SEC_GRP_PRIVILEGE`/`QARCH_SEC_USER_PRIVILEGE`, deletes the mixed-case row. Bug **1782450** (Closed, hotfixed 2023.04→2025.04; RRC & XOM).
- **Client missing Core security groups** makes build scripts fail on `QARCH_SEC_GRP_PRIVILEGE` merges: Bugs **1720064** (QGIS objects/configs, UPDATE GROUPS — hotfixed 2023.04/2024.04/2024.10), **1719989** (SPR pre-upgrade), **1731579** (DB upgrade error on CORE_QLS_044). Product scripts now guard with `SELECT COUNT(1) FROM QARCH_SEC_GRP WHERE GRP_ID = :g` before inserting.
- **V17 Maintenance app access errors:** add client group to server local group + NTFS permissions + system entry (25-01031493 UBT).

### 3.6 Data security (land division / subject / map)
- Agreement search enforces data security by joining `QARCH_SEC_GRP_PRIVILEGE` with `OBJECT_TYPE_CD='LAND'` (land division = `ARRG_ORG_KEY`) and `'SUBJ'` (subject code), via the user's `QARCH_SEC_GRP_MEMBER` rows. **A config switches GRP-level vs USER-level (`QARCH_SEC_USER_PRIVILEGE`) evaluation** — PHL overrides to GRP level. New land divisions need matching LAND privilege rows or nobody can query them. (Bug 1716392, script review QCLD_PHL_QLSA1_UAT, verbatim search SQL in the bug.)
- **Map Status security object `UPDTLEGALSEGMENTMAPSTATUS`** (ESUITE_QFC.QARCH_SEC_GRP_PRIVILEGE) is NOT honored on the Agreement Header screen — open Bug **1524215** (XTO, Proposed; related 1384554). Workaround: make the column read-only via `LIS.QCNFG_SCREEN_CONTROL_DISP` insert copying `MAP_STATUS` display row from `SUB_HDR_DTL` to `AGMT_HDR_DTL` with `READONLY_IND='1'`. There is NO security object for Subdivision Map Status (software gap).
- QGIS map security can show polygons for areas users can't access (22-00824591, config).
- Legacy: OpenID Connect SSO hid Context Filter + Persona menus (Bug 152733, fixed 2020 era — only relevant on ancient builds).

---

## 4. CONFIGURATION & CODE/DECODE MAINTENANCE CLUSTERS

Screens: **Code/Decode Value Maintenance** (myQuorum) and legacy **Code Table Navigator** (Desktop/Classic). Metadata: `LIS.QARCH_CDTBL_DEFINE` (one row per code table; `HIDDEN_TBL_IND` controls visibility) + `LIS.QARCH_CDTBL_DEFINE_COL` (per-column: edit-screen sequence, hidden, dependent table `DEP_CDTBL_ID`, dropdown sort, layer `APP_LAYER_CD`). Code tables are ALSO security objects (`OBJECT_TYPE_CD='CODE'` keyed by the numeric CDTBL_ID).

### 4.1 Code table hidden / missing from the screen
**Signature:** "Missing Code Tables", "table 48980 not accessible or doesn't exist", "make tables visible in UATA1/PRDA1".
**Root cause:** `HIDDEN_TBL_IND='1'` in `QARCH_CDTBL_DEFINE`, and/or no `CODE` security object + group privilege for it.
**Verbatim fixes:**
```sql
-- hide (case 24-00979337/24-00979402: retire legacy 47006 after 58650 replaced it)
UPDATE QARCH_CDTBL_DEFINE SET hidden_tbl_ind = '1' WHERE cdtbl_id IN (47006);
-- expose + secure (Bug 1732044, RA_TYPES 47235, group 37005):
UPDATE LIS.QARCH_CDTBL_DEFINE SET HIDDEN_TBL_IND = '0' WHERE CDTBL_ID IN ('47235');
INSERT INTO ESUITE_QFC.QARCH_SEC_OBJECT (OBJECT_ID, OBJECT_TYPE_CD, MODULE_CD, OBJECT_NM, USER_ID, UPDT_DT, APP_LAYER_CD, OWNER_ID, ISSUE_ID, AUDIT_COMMENTS, HIST_IDX)
VALUES ('47235', 'CODE', 'QLS', 'RA_TYPES', '<OPER>', SYSDATE, 'QLS', NULL, NULL, NULL, NULL);
INSERT INTO ESUITE_QFC.QARCH_SEC_GRP_PRIVILEGE (GRP_ID, OBJECT_ID, OBJECT_TYPE_CD, MODULE_CD, ALLOW_QRY_IND, ALLOW_ADD_IND, ALLOW_DELETE_IND, ALLOW_UPDATE_IND, ALLOW_EXECUTE_IND, USER_ID, UPDT_DT, APP_LAYER_CD, ISSUE_ID, AUDIT_COMMENTS, HIST_IDX)
VALUES (37005, '47235', 'CODE', 'QLS', 1, 1, 0, 1, 1, '<OPER>', SYSDATE, 'QINT', NULL, NULL, NULL);
```
**The 48955/48957 saga (HEC):** provision code tables **48955 `STIP_TYPE_RESP_UNIT_RULES`** and **48957 `STIP_TYPE_UNIT_RULES`** hidden/absent in UATA1+PRDA1; unhide script existed but QA found more table issues → Bug **1771054**; interim `ADD_PROVISIONS_CODE_TABLE` script deployed via Cloud Ops WIs 1785658/1786244 (UAT) + 1787137 (PRD); permanent fix in **Patch 1786484 = "HEC - Patch 13 on 2023.04 - Land"** (QuorumServices\Technology\Upgrades\Patches). Cases: 25-01051505, 24-00946175, 25-01009856. Prior art: 24-00966831 (AFIS GL Cross Ref became its own screen; 58650 Land Divisions added to the maintenance screen); 26-01108256 (48980 AFIS_GL_CROSS_REF "not accessible" = Training — it moved to its own screen).

### 4.2 "Save Failed" / cannot add-modify-delete code values
Match the symptom against known defects FIRST (most are already fixed — G3 exit):
| Symptom | Root cause / fix | Anchor |
|---|---|---|
| Save Failed on ALL code tables after Desktop→MyQuorum upgrade | 3 stacked causes: code-table security rows; identities in `ESUITE_QFC` schema needed **reseed**; then tracelog `The service provider does not contain a service implementation for …` → product defect, delivered in client hotfix | 22-00574327 (Equinor, multi-year) |
| Save fails on specific tables in new build (e.g. 47271) | Per-table script deployed to fix | 22-00638083 |
| Cannot DELETE from 48911 Acreage-to-Subject Relation | escalated via Cloud WI 1622190 | 23-00917954 |
| Cannot DELETE from 48924 `PIP_ARRG_TYPE_RULES` (PIP interest types / Participation Area) | Permanent fix **Patch 1786484** (HEC Patch 13 on 2023.04) | 25-01009856 |
| 'Save failed' toast with NO message on Provision/Stipulation child tables 58626, 48958, 49219 | Open product Bug **1774821** (Proposed); sibling **1775086** = dropdowns not loading on same tables | ADO |
| Provision Types uneditable | BY DESIGN: 48956 stays read-only; edit **49115** and it flows through | 24-00942061 |
| New Provision Type with Is Enabled = 'N' still enables the code | Legacy Code Table Navigator defect | 22-00519599 |
| Multiple selections of same Provision Value Unit error on save | Legacy CTN defect | 22-00519601 |
| Currency required-flag (0 Not Required) not honored | `QCNFG_REQUIRED_COLUMNS` code table honored wrong — Bug **1641331**, hotfixed 2022.04→2024.04 | ADO |
| New county added but absent from QLS Route Mappings | Open Bug **1755205** (Proposed) | ADO |
| Can't add new Provision Group (no table to map group→subject types) | Bug **1373368** (Closed) from case 21-00201118 | ADO |
| Stewardship Group add fails | legacy CTN defect family | 22-00659411 |

### 4.3 Column / dropdown misconfiguration — `QARCH_CDTBL_DEFINE_COL`
- **Columns in wrong order** on a code table's edit screen: update `QARCH_CDTBL_DEFINE_COL` (metadata change) to switch column order for that CDTBL (26-01099487, INV — Resolution verbatim: "Updated QARCH_CDTBL_DEFINE_COL to switch the column order for the specific Codetable").
- **Units dropdown blank** on 48957: dependent code table **48974 `STIPULATION_UNITS`** columns had to be configured in `QARCH_CDTBL_DEFINE_COL` **under the client layer (QHEC)** — layer-awareness matters; core rows don't apply if the client layer overrides (Bug 1771054 resolution).
- **Decode shows raw code** ("PRV" instead of "Provisions") on Provision/Stipulation child tables: core metadata update Bug **1766675** (hotfixed 2023.04+); provision-type table updates Bug **1730601**.
- Column-def insert template is in Bug 1732044 (fields incl. `CDTBL_EDIT_SCRN_SEQ_NO`, `CDTBL_COL_TYPE_CD`, `DEP_CDTBL_ID`, `DROP_LIST_SORT_*`, `APP_LAYER_CD`).

### 4.4 Configuration Settings screen & config keys
- Config keys are layered (core → QDMB/QHEC/QCNX… client layers). Change = duplicate the row at the client layer with new value, save, **refresh caches** (pattern: 24-00976767). Get config changes CHECKED IN to the client metadata repo afterward, or the next deploy reverts them.
- Confirmed keys: `CheckRoleForApproval` (=1 enforces role check on Approve; §3.4); `MAX_AUDIT_RECORDS` (max Audit History rows shown, seen set to 500; 26-01070040).
- **Emails not sending from QLS:** run `ACL_SCRIPT` in SYS (Oracle ACL for SMTP), update QPEC EMAIL NOTIFICATION configs and email **event detectors** in `ESUITE_QFC` and `QLS_QFCONL` (25-01053850). WMN failed-document-upload alert = config (26-01067220). SMTP relay setup itself is Cloud Ops (25-01051842).
- **Metadata layer rename** (e.g. QHEC layer name in PRD/UAT) is a script task (26-01082371). Missing metadata layer after upgrade → check web `.ini` profile spelling (26-01099460).
- **Filters "not working" after migration/upgrade** is usually cutover scripts missed + retraining: type into the blank next to the filter icon; picklists populate only after filters + retrieve arrow (24-00988533 Permian — two missed UAT scripts re-run, rest was training).
- Data capitalization changes across all nodes = client-driven script effort, not product config (25-01034996).

### 4.5 Audit history
- "Audit History not turned on / stale": first verify against the `_log` tables (SQL below) — the SCREEN may cap at `MAX_AUDIT_RECORDS` while the log has rows (26-01070040).
- Header-level (state/county) changes historically NOT audited: Bug **1662922** (HES) — "Modified product object definitions and added audit metadata" to audit state/county; delivered to COP via Land **2024.10 Hotfix** train (User Story 1786599, June 2026). If a client on ≤2024.10 without that HF reports missing header audit → G3 version issue.
- Audit-history error popups on records: check environment refresh state; internal envs are refreshed from PRD with post-refresh scripts including QFC tables (26-01070040 feed).

### 4.6 Business adds — scripts, not defects (route as service request)
- **New agreement/arrangement type:** add to code table **48496 `ARRANGEMENT_TYPES`** — but a script must also populate the child tables (26-01098661); front-end add possible for agreement SUBJECT types (25-01034506); new type "Contract - Term Assignment" (25-01044704).
- **Client-specific code/decode tables:** e.g. `GOPL_JEFF_SECTIONS` inserts (26-01116137 — note Resolution's "GPOL_" spelling is a typo; table is GOPL_JEFF_SECTIONS).
- **New legal entity** for leases: deployment script (26-01091679).
- **Validation severity tuning:** change message types from error to warning per subject type, e.g. ROW payment-date validations (23-00920969).
- PII/user-maintenance (create portal/SF accounts, unlock, Okta admin) → user-admin runbook, not investigation (26-01091560, 23-00933304, 26-01066489).

---

## 5. KNOWN ADO ITEMS (cite when matching)

| ADO | Type/State | Title (short) | Fixed-in |
|---|---|---|---|
| 1711330 | Bug/Closed | Batch processes missing/additional after config standardization | security sync + QLS_QFCONL/ESUITE_QFC metadata (CONFIRMED) |
| 1713292 | Bug/Closed | CALDELEXP calendar export batch missing security mappings | 2022.04→2024.10 hotfix tags (CONFIRMED via tags) |
| 1782450 | Bug/Closed | Patch upgrade blocked: ORA-02291 FK_QARCH_SEC_OBJECT1 (mixed-case object id) | 2023.04→2025.04 hotfixes (CONFIRMED via tags) |
| 1720064 | Bug/Closed | QGIS missing security objects/configs — guard group-exists | 2023.04/2024.04/2024.10 hotfixes |
| 1719989 / 1731579 | Bug/Closed | Pre-upgrade failures when core security groups missing | script-review era 2025.03 |
| 1732044 | Bug/Closed | RA_TYPES 47235 core metadata check-in | 2023.04→2025.04 hotfixes |
| 1771054 | Bug/Closed | HEC 48957 Units dropdown blank (48974 dep-table cols, QHEC layer) | client env + core |
| 1786484 | Patch/Packaged | HEC - Patch 13 on 2023.04 - Land (48955/48957 + 48924 deletes) | permanent fix carrier |
| 1662922 | Bug/Closed | Audit History not updating at header level (county/state) | audit metadata; COP via 2024.10 HF train (US 1786599) |
| 1641331 | Bug/Closed | QCNFG_REQUIRED_COLUMNS Not-Required not honored (Currency) | 2022.04→2024.04 hotfixes |
| 1766675 | Bug/Closed | Provision/Stipulation child code tables show code not decode | 2023.04+ hotfixes |
| 1774821 / 1775086 | Bug/Proposed | 'Save failed' no message / dropdowns not loading on 58626, 48958, 49219 | OPEN — no fixed-in |
| 1755205 | Bug/Proposed | New county not visible in Route Mappings | OPEN |
| 1524215 | Bug/Proposed | Map Status security object UPDTLEGALSEGMENTMAPSTATUS not honored (AGMT_HDR_DTL) | OPEN; workaround QCNFG_SCREEN_CONTROL_DISP |
| 1373368 | Bug/Closed | Unable to add new Provision Group | legacy |
| 1787526 | ScriptReview/— | PHL inactivate + clean duplicated users | script |
| 152733 | Bug/Closed | SSO (OIDC) hid Context Filter + Persona menus | 2020.01/2020.03 era |
| 1716392 | Bug(SR)/Closed | PHL land-division security — GRP vs USER privilege mode | config |

Hotfix trains: tags `YYYY.MM Hotfix (Completed)`; anything labeled only by tag = **INFERRED** fixed-in unless release notes confirm.

## 6. DIAGNOSTIC SQL (Oracle — all from real cases/bugs)

```sql
-- Identity triage (26-01106173): does the user's row match Okta?
SELECT * FROM qarch_sec_user WHERE UPPER(sec_user_id) LIKE '%<USER>%';    -- has the email = Okta join key
SELECT * FROM qarch_sec_grp_member WHERE sec_user_id = '<USER>';          -- assigned groups
SELECT * FROM qarch_sec_user_mod   WHERE sec_user_id = '<USER>';          -- assigned modules

-- Duplicate-account sweep (26-01087666 / 24-00976108 pattern):
SELECT email_address, COUNT(*) FROM qarch_sec_user GROUP BY email_address HAVING COUNT(*) > 1;  -- verify col name in env

-- Is the batch/report/code object secured for the group? (Bug 1782450 / 26-01116490)
SELECT * FROM QARCH_SEC_OBJECT WHERE OBJECT_ID = '<ID>' AND MODULE_CD = 'QLS';
SELECT * FROM QARCH_SEC_GRP_PRIVILEGE WHERE OBJECT_ID = '<ID>' AND GRP_ID IN
  (SELECT GRP_ID FROM QARCH_SEC_GRP_MEMBER WHERE SEC_USER_ID = '<USER>');
SELECT COUNT(1) FROM QARCH_SEC_GRP WHERE GRP_ID = 50030;   -- guard: does the core group even exist?

-- Data-security search join the app builds (Bug 1716392, GRP mode):
SELECT /*+ RESULT_CACHE */ A.ARRG_KEY FROM QCTRL_AGMT_LEGACY_NUMBER A
JOIN QARCH_SEC_GRP_PRIVILEGE GPL ON GPL.OBJECT_TYPE_CD='LAND' AND GPL.ALLOW_QRY_IND=1 AND GPL.OBJECT_ID=A.ARRG_ORG_KEY
 AND GPL.GRP_ID IN (SELECT GRP_ID FROM QARCH_SEC_GRP_MEMBER WHERE SEC_USER_ID='<USER>')
JOIN QARCH_SEC_GRP_PRIVILEGE GPS ON GPS.OBJECT_TYPE_CD='SUBJ' AND GPS.ALLOW_QRY_IND=1 AND GPS.OBJECT_ID=A.SUBJ_CODE
 AND GPS.GRP_ID IN (SELECT GRP_ID FROM QARCH_SEC_GRP_MEMBER WHERE SEC_USER_ID='<USER>');

-- Code table visibility (24-00979337 / Bug 1732044):
SELECT cdtbl_id, hidden_tbl_ind FROM LIS.QARCH_CDTBL_DEFINE WHERE cdtbl_id IN (47006,47235,48955,48956,48957,58650);
SELECT * FROM LIS.QARCH_CDTBL_DEFINE_COL WHERE cdtbl_id = '<ID>' ORDER BY cdtbl_edit_scrn_seq_no;

-- Audit history verification (26-01070040 verbatim):
SELECT * FROM all_agreements_log ORDER BY updt_date DESC;
SELECT * FROM stipulation_obligation_log ORDER BY updt_date DESC;
SELECT * FROM AFIS_LOG ORDER BY updt_date DESC;
SELECT * FROM STIPULATION_DATE_AUDIT_VW_CORE ORDER BY updt_dt DESC;

-- URL/DOC not saving (26-01095454): orphan cleanup target
SELECT * FROM DOC_STIP_DATE_RLTN WHERE <orphan-condition>;  -- orphans removed per resolution
```
DEV-tier caveat: schema/config findings are CONFIRMED anchors; client-PRD data-state claims stay INFERRED until run on the client env.

## 7. EXPECTED-BEHAVIOR FAQ

- **"Table 48956 won't let us edit Provision Types."** By design — edit 49115; 48956 mirrors it (24-00942061).
- **"Code table 48980 AFIS_GL_CROSS_REF doesn't exist."** It moved to its own **AFIS GL Cross Reference screen** (24-00966831; 26-01108256 was closed as Training).
- **"Filter icon opens nothing in new QLS."** Type directly in the blank beside the icon; picklists populate after filters + the retrieve arrow (24-00988533).
- **"We need rows added to GOPL_JEFF_SECTIONS / AFIS_GL_CROSS_REF / new agreement type."** Business change → script service with child-table population, not a defect (26-01116137, 26-01098661).
- **"Can Quorum change all data to upper case?"** Client-side script effort (25-01034996).
- **Cert/IP/SMTP/SFTP/Citrix requests** (SAML renewal 25-01009624, IP whitelisting 24-00947700/24-00993297, TNS timeout whitelist 25-01028900, SMTP 25-01051842, Citrix provisioning 25-01019805) → Cloud Ops runbook items, not product investigation.

## 8. ESCALATION

1. **Security screen crashes or model corrupt** (post-migration): Cloud Ops for sysgen/environment config (24-00978250 pattern).
2. **Okta account create/rename/disable, group grants:** myQuorum Cloud WI (project "myQuorum Cloud"), like 1821389/1766676. Scripts touching QARCH_SEC_* need a **Script Review** work item (e.g. 1787526).
3. **Product defect** (Save Failed with tracelog `service provider does not contain a service implementation`, approval-rule skips, audit gaps): ADO Bug in `Quorum\North America\Upstream\Land RnD` (current) with client prefix in title; maintenance history in `QuorumSoftware\Engineering\Maintenance\Upstream\Customer Service\Land`.
4. **Patch delivery:** QuorumServices\Technology\Upgrades\Patches ("<CLIENT> - Patch N on YYYY.MM - Land", e.g. 1786484).
5. Always: after security/config scripts — cache refresh, relog, then service/app-pool restart as third resort; and get client-layer config changes checked into `<CLIENT3>.QLS.Metadata`.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
