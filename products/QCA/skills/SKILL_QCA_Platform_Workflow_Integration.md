# SKILL: QCA Platform / Workflow / Integration Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QCA (My Quorum Cost Accounting — myQuorum/On Demand upstream oil-and-gas accounting suite)
**Scope:** The *platform & plumbing* layer of QCA, NOT the accounting math. Covers **eSuite / Web app behavior** (Business Associate screen, code tables, masking, AP/voucher web), **Workflow** (AP invoice & AFE approval routing, workflow locks, batch post), **Integration** (QCFS/JIB/AFE subledger interface via MT100, ADP/Open-Invoice import, QLS sync, EnergyLink/JIBLink, SFTP/FTP exports, positive-pay/check files), **Security** (user login, Okta/SSO, security groups & personas, screen access), **QQM** report-launch plumbing, and **Data Hub / environment / Citrix / QCloud** infrastructure.
**Companion skills (other QCA category groups — fix the *number* there, fix the *plumbing* here):** JIB → SKILL_QCA_JIB.md; AFE → SKILL_QCA_AFE.md; Fixed Assets (DD&A / Inventory / Capital Tracking) → SKILL_QCA_FixedAssets.md; LOS / Ad-Hoc Reporting / JEA → respective skills. This skill *consumes* master data (BAs, properties, cost centers, security) and *moves* finished accounting data between modules and external systems — when a **number** is wrong, fix it in the module skill first; come here when **the screen won't save, the user can't log in, the process won't run, or the data won't move between systems**.

> **Evidence base:** 656 closed QCA cases in the Platform/Workflow/Integration category group (Case_Category__c IN eSuite 174, Workflow 178, Security 168, Integration 100, QQM 56, Other 55 — minus Data Hub which is tiny). Root-cause split across the group: **Application Configuration 90**, (blank) 89, User Administration Request 66, Training 61, Customer Cancelled 57, Business Change 44, Cloud Outage 44, Customer Error 41, **Software Defect 39**, Performance 37, Platform 30, others. This skill mines the **132 actionable** cases (App-Config 90 + Software-Defect 39 + ChangeConfig 3) for fix recipes, plus ~35 Training/Customer-Error cases for the Expected-Behavior FAQ and the large User-Administration-Request pool for the security cluster. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining. Actionable mix by category: eSuite 43, Workflow 39, Integration 28, Security 12, QQM 6, Other 2, Data Hub 2.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Platform Concepts & Vocabulary](#2-platform-concepts--vocabulary)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — Security: login, Okta/SSO, groups & personas (HIGH FREQUENCY)](#4-cluster-a--security-login-oktasso-groups--personas)
5. [Cluster B — Business Associate (BA) screen: save / sync / duplicate-name](#5-cluster-b--business-associate-ba-screen-save--sync--duplicate-name)
6. [Cluster C — AP / AFE Workflow stuck, locks & batch post](#6-cluster-c--ap--afe-workflow-stuck-locks--batch-post)
7. [Cluster D — Document attachments & image/file export](#7-cluster-d--document-attachments--imagefile-export)
8. [Cluster E — Integration: QCFS/JIB/AFE subledger interface (MT100) & imports](#8-cluster-e--integration-qcfsjibafe-subledger-interface-mt100--imports)
9. [Cluster F — Upgrade / env config drift (metadata layers, sysgen, missing configs)](#9-cluster-f--upgrade--env-config-drift)
10. [Cluster G — Process timeouts, service restarts & locking config](#10-cluster-g--process-timeouts-service-restarts--locking-config)
11. [Cluster H — QQM report-launch plumbing](#11-cluster-h--qqm-report-launch-plumbing)
12. [Cluster I — Check / payment file (positive pay, check detail, clear date)](#12-cluster-i--check--payment-file)
13. [Known ADO Items](#13-known-ado-items)
14. [Diagnostic SQL](#14-diagnostic-sql)
15. [Expected-Behavior / User-Education FAQ](#15-expected-behavior--user-education-faq)
16. [Key Screens, Processes & Repos](#16-key-screens-processes--repos)
17. [Escalation Guidance](#17-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| "Can't log in" / "I see no apps/widgets/personas in Web" / "no desks associated" | Security email or SEC_USER_ID mismatch; Okta/SSO out of sync; client-prefixed username (`GLE_`/`CEN_`/`REP_`) not the one carrying the groups | §4 — confirm the **email** is populated on the *correct* SEC_USER_ID and that the Okta group maps to it |
| User can't see/open a specific screen (AP055, GL025, JB200, CI022, Manual JE) | Missing security group / All-Access level for that screen | §4 — add the screen's security group/credential; user logs out & back in |
| BA won't save / "can't have two BAs with same name" / BA Entity ID auto-fills wrong / BA fields clear out | BA duplicate-name validation defect (fixed) + autofill behavior | §5 — disable `QESUITEValidationBAEntity0024_DuplicateBAName` on ESuite layer or take the fix (ADO #1711589/91) |
| Vendor name disappears from voucher / invoice "entered but not in workflow" | **Trailing space on BA** | §5 — script to trim trailing space; long-term fix in current build |
| Invoice "fully approved but still in workflow" / "Workflow instance no longer available" / stuck Post-Pending | **Workflow lock not released** (defect #1711015) | §6 — deploy remove-workflow-locks script; confirm build has the unlock fix |
| AFE_IMPORT (or any cyclic process) fails repeatedly after one bad run | **Stuck process lock** (PQID held the lock) | §6/§10 — clear the lock; raise lock retry attempts in Lock Setup |
| Can't attach / open / delete a document; image export not landing on FTP | DocManagement stage config; **FTP Transfer Definition missing**; file-name special char or >100 chars | §7 |
| AFE actuals vs GL/subledger out of alignment; ADP/Open-Invoice import errors; QCFS import cycle errors after patch | **MT100 Core Interface Cross Reference** missing/extra config; identity-sequence exhaustion | §8 |
| After upgrade/cutover: missing configs, security objects, "Collision with nonsysgen object trigger", Web≠Classic | **Application-layer / metadata config drift**; sysgen collision | §9 |
| Process times out (QSTG1099EX, JBOWNERALLOC, LOSDD_IMP); "Max retries hit for lock type" | Command-timeout too low; lock-retry config; QPEC memory | §10 — raise `COMMAND_TIMEOUT_SECONDS` / QPEC.ini timeout; Lock Setup overrides |
| QQM report won't launch / "Statement(s) could not be prepared" / restriction error / attributes missing | ODBC driver mismatch in the universe; OU/server path; attribute staging not run | §11 |
| Positive-pay file won't generate; check detail wrong; payment clear date wrong | Dynamic-export config; data script; GUI redeploy | §12 |
| App slow / crashing / "error when desktop app left open" | Citrix server memory / Citrix LTSR bug / desktop session expiry | §10 / §15 |

---

## 2. Platform Concepts & Vocabulary

**QCA** = My Quorum Cost Accounting (upstream accounting). Sits in the **myQuorum / On Demand** suite alongside **QCFS** (Core Financials / GL), **QLS** (Land System), **QRA** (Revenue Accounting / API). Most platform cases involve the seams *between* these.

- **Classic GUI vs Web / eSuite** — QCA has a legacy **Classic** desktop client (run via Citrix) and a newer **Web** (eSuite) UI. They share the DB but the Web layer does **extra filtering/validation** and reads different config; many "works in Classic, broken in Web" cases are Web-layer metadata/config gaps (25-01033015, 24-00990542).
- **Application layers** — config is stacked: **core → ESUITE → QFMO → client layer (e.g. QGEC, QVTL, QMEW, ENV)**. A value set on the wrong layer, or missing on the client layer after an upgrade, is the single most common "config drift" cause (§9). The **ENV layer should hold only file paths/URLs**; logic belongs on QFMO/client layers (25-01030069).
- **MT100 — Core Interface Cross Reference** — the screen that maps which records flow between modules (MT → QCFS → JIB → GL; AFE → subledger). Missing or extra rows here = data doesn't move, or moves twice (25-01031530, 24-00950081, 25-01020792). Backed by `SXREF_CORE_INTFC_*` / `STRAN_CORE_INTFC` / `SEXTN_CORE_INTFC_JIB` tables.
- **QCFS Import Cycle / ADPUPLOAD / AFEEXTIMP / QCFSIMPCYC** — batch import processes that pull external/Open-Invoice/AFE data into QCA. They run through **QPEC** (the process engine) and acquire **process locks**.
- **Workflow** — AP invoice and AFE approval routing. A workflow **instance** is locked while being worked; if a session dies the lock can stick → "Workflow instance no longer available" / stuck "In Progress" or "Post Pending" (§6). **POSTWKFL** posts approved batches.
- **Security model** — a **SEC_USER_ID** (often client-prefixed, e.g. `GLE_JBRADLEY`, `CEN_JORDAN_NEWTON`) carries **GRP_IDs** (security groups, numeric, e.g. `5010`, `2510`, `2705`) which map to **CDTBL_IDs** via `QXRF_SECGRPID_CDTBL_ID`. The user's **email** must be populated and must match the Okta/SSO identity. **Personas / Web widgets** are driven by these groups. The two most common failure modes: (1) email missing or on the wrong duplicate SEC_USER_ID, (2) the username has a **space instead of `_`** so it doesn't match the desk/group records.
- **Desk / Originating Desk** — AFE routing entity (Cost Accounting: Desk Maintenance). AFEs route to approvers via desks; a missing desk or a desk not tied to the username breaks AFE approval routing.
- **QCloud / Citrix / Okta** — the hosting layer. Login, file-path, NTFS-permission, OU, VPN, and Citrix-version issues are handled by **QCloud Ops** (often "Cloud Outage" / "Platform" root cause), not Engineering.
- **QPEC / QPEC.ini / QPECS** — the process execution engine and its services. `COMMAND_TIMEOUT_SECONDS` (default 18000 = 5h) and the QPEC.ini Command Timeout cap long-running processes. **QPECS restart** clears many transient "process not running" issues.
- **DOCMGMT / DocManagement.MiddleTier** — document attachment subsystem; config key `DOCMGMT / ENABLED`. Attachments also flow to an FTP via **FTP Transfer Definitions** (Maintenance app).
- **QQM** = Quorum Query Manager (BusinessObjects-based reporting). Reports run against a **universe** with **ODBC connections** per DB (QCA/QCFS/QRA). Driver mismatches and OU/server-path restrictions are the usual launch failures.

---

## 3. Decision Tree

```
Platform / Workflow / Integration case
│
├─ Can't log in / can't see apps / personas / desks / a screen?           → §4 SECURITY
│   ├─ No widgets/personas in Web, or "no desks associated"               → email missing on correct SEC_USER_ID; username prefix/space mismatch; Okta group
│   ├─ Can't open one screen (AP055/GL025/JB200/CI022/JE)                  → add the screen's security group / All-Access level; log out & in
│   └─ Okta lockout / SSO out of sync / Citrix profile                     → QCloud Ops (Okta group, reload Citrix)
│
├─ Business Associate screen misbehaving (save/sync/name)?                 → §5 BA
│   ├─ "can't have two BAs same name" / Entity ID auto-fills / fields clear→ duplicate-name validation defect (ADO #1711589/91); disable QESUITEValidationBAEntity0024_DuplicateBAName
│   ├─ Vendor disappears from voucher / "entered but not in workflow"      → trailing space on BA (trim script)
│   ├─ Contact/role/type error (PAY, primary)                             → SCTRL_BA_CONTACT_ROLE / _ADDRESS config
│   └─ BA doesn't sync to QLS                                              → add the BA's missing dependency in QLS (§8)
│
├─ Invoice/AFE stuck in workflow, or batch won't post?                     → §6 WORKFLOW
│   ├─ "fully approved but still in workflow" / "instance no longer avail" → workflow lock not released (ADO #1711015) → remove-locks script
│   ├─ Stuck Post-Pending / POSTWKFL error                                 → check AP043 zero-bank-acct type; contact-role dup; deploy script
│   └─ AFE not routing to expected approver                                → desk/route not updated for the new desk (config/training)
│
├─ Can't attach/open/delete a doc; image/file export missing?             → §7 ATTACHMENTS/EXPORT
│   ├─ Attach fails                                                        → DocManagement stage config / DOCMGMT ENABLED; special char or >100-char filename
│   └─ Images/files not on FTP                                            → add FTP Transfer Definition (Maintenance → FTP)
│
├─ Data not moving between modules / external systems?                     → §8 INTEGRATION
│   ├─ AFE actuals ≠ GL/subledger; MT didn't post; data doubled           → MT100 Core Interface Cross Reference missing/extra row
│   ├─ ADP / Open-Invoice import error / wrong acct date                   → QCFS config tab / ADP_UPLOAD_AUTO_SET_ACCT_DATE / JBCDE_BUSINESS_SEGMENT
│   ├─ QCFS import cycle errors after a patch                              → bad SXREF_CORE_INTFC row (delete it)
│   └─ "exceed Maximum Sequence Number" / Finalize-and-Post identity error → reseed STRAN/SEXTN_CORE_INTFC identity (DBCC CHECKIDENT)
│
├─ After upgrade/cutover: missing config / security / Web≠Classic?         → §9 CONFIG DRIFT
│   ├─ "Collision with nonsysgen object trigger"                          → rerun sysgen in target env; correct app-layer usage
│   └─ Missing configs / security objects / metadata                       → sync from DEV; check-in metadata; put on correct client layer
│
├─ Process times out / "Max retries hit for lock type"?                    → §10 TIMEOUT/LOCK
│   ├─ Timeout (QSTG1099EX, JBOWNERALLOC, LOSDD_IMP)                       → raise COMMAND_TIMEOUT_SECONDS / QPEC.ini timeout; QPEC memory subsets
│   └─ "Max Number of retries hit for this lock type: <X>"                 → Lock Setup → override max attempts/time-between
│
├─ QQM report won't launch / wrong?                                        → §11 QQM
│
└─ Vague "error", "how do I…", "is this expected", access question         → §15 Expected-Behavior FAQ (Training / Customer Error)
```

---

## 4. Cluster A — Security: login, Okta/SSO, groups & personas

**The single largest platform signature** (the group also carries ~66 "User Administration Request" cases on top of the actionable 12 Security-category + many eSuite/Workflow login cases). Almost all are **Application Configuration**, resolved by QCloud/Support, not code.

**Two dominant root patterns:**

1. **Email missing or on the wrong (duplicate) SEC_USER_ID.** When a user has two SEC_USER_IDs (e.g. a client-prefixed `CEN_JORDAN_NEWTON` and a bare `Jordan_Newton`), only one carries the security groups and only one has the **email** populated. Login / persona visibility breaks when Okta authenticates against the record *without* the groups/email.
   - 26-01093862 — two `Jordan Newton` records; `CEN_Jordan_Newton` had no email; remove the stray `Jordan_Newton` from security so auth uses the correct account.
   - 26-01098577 — email had two SEC_USER_IDs; the **wrong** SEC_USER_ID held the SEC_GRPs; once the correct SEC_USER_ID got the GRP_IDs the user could log in.
   - 25-01063103 — new username created without populating the **email** section → no Web apps until email added.
   - 25-01043142 — "default personas" fixed by **updating the user's email** in each environment.

2. **Username doesn't match the desk/group records** — usually a **space instead of `_`** or the wrong prefix.
   - 24-00971869 — user was `JARED CHRISTOPHER` (space) but desks were under `JARED_CHRISTOPHER`; rename the security username to use `_`.
   - 25-01027218 — set security to `GLE_EVAN_LOFLIN` instead of `EVAN_LOFLIN` to see personas.
   - 26-01098577 above is the same family.

**Other security fixes seen:**
- **Screen/credential access** — add the specific security group: AP055 → group `5010` (23-00908567); GL025 → "10: All Access User" (23-00918354); "Post To Inventory Subledger" credential lives in group `2510` (24-00980550); Web personas QCA-WEB-PERSONA-AFE COORDINATOR `2705` / APPROVER `2708` (25-01030514). User must **log out and back in** after group changes.
- **Okta / SSO out of sync** — add the user to the correct Okta group (25-01025966 Greylock Users OKTA group); Okta lockout threshold is **10 attempts** (25-01056137); periodic Okta lockout fixed by **reloading Citrix** (25-01032607).
- **Security-group metadata cross-ref missing after upgrade** — `QXRF_SECGRPID_CDTBL_ID` rows tying custom GRP_IDs to CDTBL_IDs were missing in PRDA1; **synced from DEVA1** (25-01022895).
- **Web security objects missing on a custom group** — add Web security objects to the client custom security groups (25-01025886, scripts attached).
- **AD-group based access** — add users to correct AD groups (23-00917112).

**Fix recipe:**
1. Get the exact **SEC_USER_ID** the user logs in with. Check for **duplicate** user records and confirm the **email** is populated on the one Okta authenticates against.
2. If no apps/personas/desks: confirm the username (prefix + `_` vs space) matches the **group** and **desk** records.
3. If one screen is blocked: identify the screen's **security group** and add it (or the All-Access level); have the user re-login.
4. Okta/SSO/Citrix-profile issues → **QCloud Ops** (Okta group membership, Citrix reload). These are typically *not* code and not Engineering.

---

## 5. Cluster B — Business Associate (BA) screen: save / sync / duplicate-name

A distinct, recurring **eSuite/Web** cluster around the **Business Associate (BA005 / BA screen)**. BAs are the vendor/owner master records that feed AP, JIB, revenue, and check-writing — a BA that won't save or silently corrupts blocks everything downstream.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| "Cannot have two BAs with the same name" / unable to re-activate or save a BA with a duplicate name (2024.04 upgrade) | Web validation `QESUITEValidationBAEntity0024_DuplicateBAName` blocked legitimate duplicate names; the "similar name" prompt fired wrongly and checked the *name-change-history* table instead of current names | **Disabled** the validation on the ESuite layer; fixed the prompt to fire on add and to check `SCTRL_BA_ENTITY`; BA Name field now only autofills the Entity ID when you *select* from the dropdown (not on tab-off) | 25-01004452, 25-01002233, 24-00984431 / **ADO #1711589, #1711591** (Bug, Closed) |
| BA **Entity ID / BA Name fields clear out** when retrieving values | Web screen field-handling defect | Code fix | **ADO #1528690** (Bug, Closed) |
| Cannot edit BA name — **auto-fills BA Entity ID if name matches another BA** | Same autofill family as above | Code fix | **ADO #1595163/#1595164/#1595170** (Closed) |
| **Vendor name disappears** from a saved voucher; invoice "entered into workflow" but not visible | **Trailing space on the BA** name | Script to trim the trailing space; **long-term fix in current build** | 26-01088113 |
| BA Vendor/Customer data **not saving** | Defect | **November Hotfix** resolved it | 24-00980819 (ref 24-00976962) |
| BA "Effective date error code" when updating | Missing EFF DATE on Tax ID | Script to add EFF DATE to Tax ID | 25-01030212 |
| BA005 JIB-tab "Special Handling" error + PUBBA completes with errors | Missing metadata values; QLS integration missing values in 'Connection Information Control' | Add metadata + QLS connection values (post-upgrade scripts) | 23-00919413 |
| BA "Use as Vendor" object-reference error | Defect | Resolved in later build | 23-00910748 |
| BA Sub being set to 0 (2023.04 UAT) | Defect | Code fix | 23-00931208 |
| Editing/saving BA → **Zip Code error** | Zip masking config | Removed masking set in config `ZIPCODE_MASK_WEB` and code table 29037 | 25-01041976 |
| Contact-type / "Contact Type error" on ACH remittance; can't create contact in BA005 | Missing **PAYMENT** contact type on the "Additional BA" tab; contact ID not on code table | Add Additional BA with Contact type = Payment Party (25-00999621); update contact id on code table 9131 (24-00961934) | 25-00999621, 24-00961934 |
| BA note categories missing in Web (present in Classic) | Web does extra filtering — category not tied to the BA notes xref + cache not refreshed | Add/associate the record in **Code Table 224** (ESuite), refresh **ESuite Cache Maintenance** | 25-01033015 (expected behavior + config) |

**Fix recipe:** For "duplicate BA name" / "can't save BA" on a 2024.04+ upgrade, the fix is **ADO #1711589/#1711591** (disable `QESUITEValidationBAEntity0024_DuplicateBAName` on the ESuite layer as the immediate unblock, then take the build with the corrected prompt/autofill). For **vendor-disappears-from-voucher**, the cause is a **trailing space on the BA** — run the trim script (long-term fix shipped). For contact/ACH errors, verify the BA has the **PAYMENT contact type / primary contact** configured (`SCTRL_BA_CONTACT_ROLE` + `_ADDRESS`). For Web≠Classic dropdown gaps, add to the right **code table** and **refresh ESuite cache**.

---

## 6. Cluster C — AP / AFE Workflow stuck, locks & batch post

Invoices/AFEs that approve but won't advance, or batches stuck in **Post Pending** — mostly a **workflow-lock defect** plus a few config items.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| Invoice **fully approved but still "In Progress"** in workflow; "Workflow instance is no longer available or does not exist"; "Voucher was not submitted to workflow" | **Workflow instance lock not released** when a session dies | **Script to remove the workflow locks** (immediate); **long-term fix** | 24-00992878, 23-00902566 / **ADO #1711015** (Bug, Closed — "Workflow instance not always being unlocked"); related script-deploy WIs #1661160/#1661268 |
| **AFE_IMPORT locked again** — subsequent imports fail because a prior PQID held the process lock | Stuck process lock from a failed/abandoned run (PQID held it) | Clear the held lock; monitor; raise lock-retry attempts (§10) | 26-01064522 (ref 25-01061459) |
| Batch stuck **Post Pending** in AP061; POSTWKFL error "bank account type does not correspond to the zero bank account type" | **AP043 Zero bank account** misconfigured (was ODEN, should be OPERATING) | Set AP043 Zero bank account to OPERATING | 23-00905765 |
| Batches stuck Post Pending — POSTWKFL "Column ... is constrained to be unique ... BA_NO,CONTACTTYPECODE 'PAY'" | **Duplicate primary** rows in `SCTRL_BA_CONTACT_ADDRESS` / `SCTRL_BA_CONTACT_ROLE` | Delete the duplicate primary contact row | 25-01035193 (Customer Error) |
| Invoice **stuck in workflow** (single) | Lock / state | Data script to move voucher to Draft | 25-01025832 |
| **Missing AFE Workflow** after v17→v18 | Workflow version mismatch on existing items | Script to update workflow from v17 to v18 for existing WF items | 25-01061112 |
| **Batch Post process not running** | Schedule definition disabled | Enable the schedule definition for the Post Workflow process | 23-00907240 |
| On-Submit notification / "On Submit" button removed (Q3 Sept) | Web config; cosmetic | Confirmed notifications still received; button removal fixed in later hotfix | 22-00823287 |
| AFE/Supplement needs status change but is closed | Closed-status block | Script to open AFE/supplement | 22-00632367 |
| "Critical AFEs/Supplements that need Status changes" | Same | Script | 22-00632367 |
| Workflow error approving invoice — `FK_BATCHVOUCHERDETAIL_IDVENDOR` | User credential / approval-limit value wrong | Modify the user's credential & approval limit | 24-00976561 |
| **Idle AP invoice count wrong** on dashboard | Display defect | Script to display correct invoice count | 24-00954896 |
| Unable to **delete uploaded invoices** | File name **>100 characters** | Fixed in a later build (not hotfixable to TPW's version — must upgrade) | 25-01030421 (dup 25-01031369) |
| **Phantom attachments** appearing on new vouchers | Orphaned metadata adding 2017-era attachments to new vouchers | Script to delete the orphan metadata | 25-01000836 |

**Fix recipe:** For "approved but stuck" / "instance no longer available," deploy the **remove-workflow-locks script** and confirm the build carries **#1711015** (the unlock fix). For **stuck Post Pending**, check (a) **AP043 zero-bank-account type** = OPERATING (23-00905765), (b) **duplicate primary BA contact** rows (25-01035193). For a stuck single voucher, a data script to reset it to **Draft** is the standard unblock (25-01025832). For AFE_IMPORT/cyclic-process locks, clear the lock and raise **Lock Setup** retry attempts (§10).

---

## 7. Cluster D — Document attachments & image/file export

"Can't attach / open / delete a document" or "exported images aren't on the FTP." Mostly **config** (DocManagement stage, FTP transfer definitions) and **filename hygiene** (special chars, length).

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Document attachment error after upgrade | Upgraded environment **stages not created** in DocManagement | Create the stages in **DocManagement.MiddleTier**, redeploy Classic GUI code | 26-01095607 |
| Material-Transfer doc-attachment config missing | Global config `DOCMGMT / ENABLED` not set on the client layer | Set `DOCMGMT/ENABLED = 1` on the **QVTL** layer; metadata check-in | 25-01035711 |
| Unable to view/add documents on the BA screen after upgrade | ESUITE config mismatch vs UPS QFC + document-path mapping | Update ESUITE config to match UPS QFC; bulk-update path mapping on the documents table | 26-01071376 |
| Can't attach a file (Web voucher/AP) | **Special character** in the file name (e.g. `'`) | Rename the file (or "print to Microsoft PDF" to re-save clean) | 24-00991782, 25-01058092 |
| Invoice **images not exporting to FTP** | **FTP Transfer Definition missing** | Add the `WEBPORTALIMAGEEXPORT` FTP Transfer Definition (Maintenance → FTP → FTP Transfer Definition) so the system knows source/target paths | 23-00928933 |
| Adobe acts like first-time use every time a doc opens | Wrong/old Adobe Reader in the environment | QCloud reconfigured & reinstalled the correct Adobe Reader | 24-00995643 |

**Fix recipe:** Attach failures → check **DocManagement stages / `DOCMGMT ENABLED`** config and the **filename** (special chars, >100 chars). Export-not-landing → add the **FTP Transfer Definition** in the Maintenance app (host id, host/local file paths, transfer type Upload). Path/permission issues are QCloud.

---

## 8. Cluster E — Integration: QCFS/JIB/AFE subledger interface (MT100) & imports

QCA's value as an accounting hub is moving data **MT → QCFS → JIB → GL** and **AFE → subledger**, plus pulling external invoices (ADP/Open-Invoice) and syncing BAs to QLS. The dominant fix is **MT100 — Core Interface Cross Reference** config.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **AFE actuals ≠ GL/subledger** (AFE_SUBLEDGER vs GENERAL_LEDGER misaligned) | **MT100 Core Interface Cross Reference** config missing — some AFE records never moved to the subledger | Add the missing MT100 config, rerun the realign process | 25-01031530 |
| MT (Material Transfer) data **duplicated** in the GL | Same data came in twice: once via MT→QCFS→JIB→GL and once directly MT→JIB→GL | Remove the duplicate; the *how-it-got-through-twice* root cause tracked separately | 25-01020792 (ref 25-01025562) |
| Import "An Item with the Same Key has already been added" (ADPUPLOAD) | System didn't recognize the **ARCONV Journal ID** | Remove the MT100 ARCONV Journal ID from the QCFS config tab | 24-00950081 |
| **QCFS Import Cycle errors after a patch** | Bad row in `SXREF_CORE_INTFC_QCFS_EXT` | `DELETE FROM SXREF_CORE_INTFC_QCFS_EXT WHERE JOURNAL_ID='QCFS' AND TRX_TYPE='GL'` | 25-01042240 |
| "Entries may soon exceed the **Maximum Sequence Number**" (STRAN_CORE_INTFC) | Identity column near max | Reseed `SSTAG_CORE_INTFC`/`STRAN_CORE_INTFC` identities to 0; rebuild archive tables | 24-00953398 |
| **Finalize-and-Post failed** (Pioneer) | Identity exhaustion on `SEXTN_CORE_INTFC_JIB` | `DBCC CHECKIDENT (SEXTN_CORE_INTFC_JIB, RESEED, 0)` (in a TRAN) | 23-00887308 |
| ADP / Open-Invoice import **wrong accounting date** | Depends on global config `ADP_UPLOAD_AUTO_SET_ACCT_DATE` + `JBCDE_BUSINESS_SEGMENT.BILLING_IN_PROGRESS`/`PROCESS_PERIOD` | Set config & business-segment state per the matrix; put config on the client (QGEC) layer | 24-00974384 |
| Recurring payment-group error on ADP Invoice Import | Config | (config) | 25-01008689 |
| ADPUPLOAD validation regression (V17) — couldn't fail an invoice in a batch | V17 broke the "fail one invoice in a batch" path; fixed again in 2024.04 | Engineering **ported WIs back to 2023.04** (May release) | 25-01006935 |
| **BA not syncing to QLS** | Missing dependency in QLS | Add the missing record (e.g. the country "Kenya") to QLS | 24-00980832 |
| QP063 Cost-Center interface to QLS errors; QP053 export to JIBLink failed; EnergyLink cash-call statements missing | DB-to-DB connectivity / tnsnames / config between Upstream and QLS/external | Fix `tnsnames`, resolve DB connections (23-00905279); config (24-00974228, 23-00923270) | 23-00905279, 24-00974228, 23-00923270 |
| QP073 JPM card file — wrong end date across year boundary | Dynamic export calc | Update dynamic-export settings to calc end date across new year | 25-01058295 |
| LOSDD_IMP UCALC errors (high volume) | QPEC memory overloaded | Config change to handle smaller data subsets (§10) | 24-00957656 |

**Fix recipe:** When **data doesn't move or moves twice between modules**, the first stop is **MT100 (Core Interface Cross Reference)** — confirm the right rows exist (and no extra/stale ones like ARCONV). "After a patch, import cycle errors" → look for a bad `SXREF_CORE_INTFC_*` row to delete (25-01042240). "Finalize-and-Post / sequence number" errors → **reseed the `*_CORE_INTFC*` identity** in a transaction (23-00887308, 24-00953398). ADP/Open-Invoice acct-date issues → the `ADP_UPLOAD_AUTO_SET_ACCT_DATE` + `JBCDE_BUSINESS_SEGMENT` matrix (24-00974384). QLS/JIBLink/EnergyLink failures are usually **DB connectivity/config**, often handled with QCloud.

---

## 9. Cluster F — Upgrade / env config drift

Upgrades (v17 → 2023.04/2024.04/2024.10) and DEV→PRD cutovers surface **application-layer / metadata config that exists in one env/layer but not another**. These spike during UAT and mock cutovers.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| "**Collision with nonsysgen object trigger** TR_RI_SCODE_CURRENCEY_D" — refresh DEVA1→PRDA1 left items pointing at DEV | sysgen collision during refresh | **Rerun sysgen** in the target env (identifies the errors so they can be corrected) | 25-01002439, 25-01000811 |
| Missing **Web security objects** on custom groups after upgrade | Objects not carried into client custom groups | Add Web security objects to the custom groups (scripts) | 25-01025886 |
| Missing **QMEW config for JIB Offset** / missing **Primary Usage config** after a hotfix | Config dropped during patch | Re-add the configs | 25-01020021, 25-01018842 |
| Property/Well changes **not syncing Web↔Desktop** | Software gap | Fixed in a 2023.04 hotfix | 24-00990542 |
| ENV-layer cleanup on v17 | Logic wrongly on the ENV layer | ENV layer should hold **only file paths/URLs**; delete or migrate the rest to **QFMO** | 25-01030069 |
| Code-table content differs Classic vs Web (`QARCH_CODE_NOTE_CATEGORY`) | **Web does extra filtering** (expected) | Add the record on the ESuite Code Table Value screen + associate to the xref + refresh cache | 25-01033015 |
| Confirm config records "missing" in on-prem vs QCloud | Not actually required on-prem | Researched & confirmed not required | 23-00906103 |
| "Cannot launch Maintenance App" after upgrade | Wrong launch path | Provided correct steps to launch the client installer | 23-00912685 |
| Esuite AFE error during cutover | Same sysgen-collision family | Rerun sysgen (see above) | 25-01002439 |
| 1099 AP export path wrong after upgrade | File-path metadata | Update the file-path metadata | 25-01008773 |
| Reports default to "Excel 1997" | Default export type config | Change default report export type to **XLSDATA** | 25-01008217 |

**Fix recipe:** For upgrade/cutover gaps, identify **which application layer** the value belongs on (core / ESUITE / QFMO / client e.g. QGEC/QMEW/QVTL/ENV) and **sync from DEV / re-add the config, then check in metadata**. "Collision with nonsysgen object trigger" = **rerun sysgen** in the target env. Remember the **ENV layer is paths/URLs only**. Many "Web shows different data than Classic" reports are **expected** (Web filters more) — fix via the right code table + **ESuite Cache refresh**, not a defect.

---

## 10. Cluster G — Process timeouts, service restarts & locking config

Long-running JIB/AP/import processes that **time out** or **deadlock on a lock**, plus the QPEC service-restart reflex.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **QSTG1099EX timing out** | `COMMAND_TIMEOUT_SECONDS` too low | Raise to 5h (18000s) and rerun | 25-00998658 |
| **JBOWNERALLOC failing with timeout** during JIB close | QPEC.ini Command Timeout too low | Raise QPEC.ini Command Timeout (5h→8h) for the close; **revert to 18000s afterward** to avoid downstream issues | 24-00984129 |
| **LOSDD_IMP UCALC errors** (high volume) | QPEC memory overloaded by one big dataset | Config to process **smaller subsets** so QPEC memory isn't overloaded | 24-00957656 |
| "**Max Number of retries hit for this lock type: CFS_IMP – QCFS IMPORT LOCK**" | Default lock attempts too few for the volume | **Lock Setup** (Maintenance → Locking → Lock Setup): for `CFS_IMP`/`QCFSIMPCYC` set Override Max Attempts=60, Time Between=30 | 24-00944930 |
| QPECS not running / process not executing | Service stopped | **Restart QPECS** | 25-01027220, 23-00927995 |
| QQM queries with Excel data source not processing | **Adaptive Processing Server** stopped | Restart the APS | 23-00914164 |
| App performing slow | Citrix server **memory spikes** | QCloud increased RAM on the Citrix server | 24-00938430 |
| App crashing without warning | **Citrix LTSR 2405 bug** | Use **LTSR 2402** instead of 2405 | 24-00970238 |
| FAMTPOST/FAMTEDIT run simultaneously → both error & roll back inconsistently | No lock preventing concurrent execution | **New lock added** to block simultaneous FAMTPOST/FAMTEDIT (hotfix) | 23-00889383 / **ADO #1585578** (Bug, Closed); perf follow-up #1644523/#1735154 |

**Fix recipe:** Timeouts → raise **`COMMAND_TIMEOUT_SECONDS`** / **QPEC.ini Command Timeout** for the run, then **revert** (24-00984129). "Max retries hit for lock type X" → **Lock Setup** override attempts/time-between for that lock+process (24-00944930). Transient "process not running / not processing" → **restart QPECS** (or the Adaptive Processing Server for QQM). High-volume QPEC memory errors → process in **subsets**. Citrix slowness/crashes → **QCloud** (RAM, LTSR version).

---

## 11. Cluster H — QQM report-launch plumbing

(The *reporting math* lives in the Ad-Hoc Reporting skill; here it's about QQM **launching at all**.)

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| QQM report fails "**Statement(s) could not be prepared**" in one env only | **Outdated ODBC driver** in that env's universe | Change the connection to **MS SQL Server 2019** driver for QCA/QCFS/QRA DBs and re-import into the universe | 24-00994264 |
| QQM "restriction in effect on this computer" when exporting/downloading | Citrix server in the wrong **OU** for saving files | QCloud moved the server to the correct OU / path | 24-00985684 |
| QQM reports won't run | **Adaptive Processing Server** stopped | Restart APS (see §10) | 23-00914164 |
| **AFE attributes not available** in QQM | Attribute data not staged | Set AFE type/attribute settings + global config `ENABLE_ATTRIBUTE_REPORTING`, run **Stage AFE Attributes** (populates `QSTAG_AFE_ATTR_FLAT`) | 24-00938127 |
| QQM 1099 report (AP001) change | Maintenance/metadata | Resolved by Maintenance Engineering | 23-00909851 |
| Can't launch Web Intelligence in QQM | Java plugin blocked in Citrix profile | Reset Citrix profile to clear the "don't load" Java setting | 22-00632352 |

**Fix recipe:** "Works in DEV/PRD, fails in UAT" QQM launch errors are almost always an **ODBC-driver/connection mismatch in the universe** (24-00994264) or an **OU/server-path restriction** (24-00985684, QCloud). "Attribute/field missing" → run the relevant **staging process** and set its global config (24-00938127).

---

## 12. Cluster I — Check / payment file

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Unable to generate **positive pay** file | GUI/positive-pay build | Redeployed the GUI with the positive-pay dev | 24-00970244 |
| Positive Pay path not working | **Space in the folder name** ("Positive Pay") broke QCloud File Explorer | Correct the path (no space, or escape it) | 25-01026849 |
| **Check detail** wrong (state/country code) | Bad codes in JE & check-write tables | Script to fix state/country codes in the journal-entry and check-write tables | 23-00922630 |
| **Payment clear date** wrong in AP157/AP155 | Reconciliation vs staging mismatch | Script to set dates where recon-table records equal staging-table dates | 24-00936541 |
| Check File **return address** wrong | Dynamic EXP config | Requested Dynamic-EXP changes (also bundled to a hotfix) | 24-00986629 |
| BK040 Global Payment File Staging Inquiry errors on Query | Bad registered SQL + grid def | Corrected registered SQL & grid definition in BK040 | 23-00907694 |
| POSPAY file from QLS ran "successfully" but not in eSuite BK010 | ESB connection pointed at the wrong DB | Repoint ESB connection to Upstream ESUITE in Connection Management; restart services | 23-00905508 |

**Fix recipe:** Positive-pay/check-file issues split into **GUI/build redeploys** (24-00970244), **dynamic-export config** (return address, JPM card file 25-01058295), **path/space hygiene** (25-01026849), and **data scripts** for clear-date/state-country corrections. BK-screen query errors are typically **registered-SQL + grid-definition** fixes.

---

## 13. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1711589 / #1711591** | Bug / **Closed** | MEW 2024.04 — Unable to save Business Associate with the same name (core & web) | §5 | 25-01002233, 25-01004452 |
| **#1595163 / #1595164 / #1595170** | Task / **Closed** | myQuorum: Cannot edit BA name — autofills BA Entity ID if name matches another BA | §5 | (BA-name family) |
| **#1528690** | Bug / **Closed** | BA Entity ID and BA Name fields clear out when retrieving values | §5 | (BA-name family) |
| **#1444019 / #1452583 / #1541343** | Bug+Task / **Closed** | ONK — BA Name Change History tab not being populated (22-00251004) | §5 | 22-00251004 |
| **#1711015** | Bug / **Closed** | Workflow instance not always being unlocked | §6 | 24-00992878, 23-00902566 |
| **#1661160 / #1661268** | Bug + Script Deployment / **Closed** | PHL QLS — Remove Workflow Locks (UAT & PRD script deploys) | §6 | (workflow-lock family) |
| **#1481660** | Feature / **Closed** | [EB-5287] Put workspace into Read-only mode for locked workflows | §6 | — |
| **#1585578** | Bug / **Closed** | SRC — FAMTPOST/FAMTEDIT executed simultaneously, processes improperly rolled back | §10 | 23-00889383 |
| **#1644523 / #1735154 / #1741527** | Bug+Requirement+Task / **Closed** | SRC — FAMTEDIT/FAMTPOST performance review | §10 | (MT-post perf) |

> Many actionable cases here were dispositioned **operationally** (config change, data script, service restart, QCloud action) with **no single product WI** — e.g. MT100 Core-Interface-Cross-Reference config (25-01031530, 24-00950081), `SXREF_CORE_INTFC` row delete (25-01042240), `*_CORE_INTFC` identity reseed (23-00887308, 24-00953398), `COMMAND_TIMEOUT_SECONDS`/QPEC.ini timeout (25-00998658, 24-00984129), Lock-Setup retry overrides (24-00944930), QQM ODBC-driver swap (24-00994264), `DOCMGMT/ENABLED` + FTP Transfer Definition (25-01035711, 23-00928933), BA trailing-space trim (26-01088113), security email/SEC_USER_ID/Okta fixes (§4). The hotfix references in eSuite "patch" cases (24-00984433 Patch 12, 25-01058609 Patch 11&12, 25-01014250 Patch 15, 26-01085614 Patch 8 abandoned) point to the **Upstream Hotfix/Patch** stream — confirm the exact build in the Upstream release notes / patch manifest when stating fix availability.

---

## 14. Diagnostic SQL

> **Caveat:** QCA runs on **SQL Server** per-client (e.g. `<CLIENT>_PRDA1UPS_QFC`), with `SCTRL_*` (core master), `SXREF_*`/`STRAN_*`/`SEXTN_*` (interface/staging), `QSTAG_*` (staging/flat), `QXRF_*` (security xref) tables. **Table/column names below are from case repro text — verify against the client DB before scripting.** Always run a verify-SELECT first and wrap any DELETE/UPDATE/reseed in a transaction.

```sql
-- A. Duplicate/short security user records & missing email (§4)
SELECT SEC_USER_ID, USER_NM, EMAIL_ADDR, STATUS
FROM   SCTRL_SEC_USER           -- verify exact table name in client DB
WHERE  USER_NM LIKE '%NEWTON%';  -- look for prefix vs bare, space vs underscore, NULL email

-- B. Security groups tied to a user, and the group→codetable xref (§4)
SELECT u.SEC_USER_ID, g.GRP_ID
FROM   <SEC_USER_GRP table> g JOIN <SEC_USER table> u ON ...
WHERE  u.SEC_USER_ID = '<CLIENT_PREFIX_USER>';
-- Missing rows here after an upgrade = the QXRF_SECGRPID_CDTBL_ID gap (25-01022895):
SELECT * FROM QXRF_SECGRPID_CDTBL_ID WHERE GRP_ID = '<grp>';

-- C. BA trailing-space / duplicate-name (§5)
SELECT BA_NO, BA_SUF, BA_NM, LEN(BA_NM) AS namelen, LEN(RTRIM(BA_NM)) AS trimlen
FROM   SCTRL_BA_ENTITY
WHERE  RTRIM(BA_NM) = '<vendor>'         -- trimlen<namelen => trailing space (26-01088113)
ORDER BY BA_NM;

-- D. Duplicate PRIMARY BA contact blocking POSTWKFL (§6, 25-01035193)
SELECT BA_NO, BA_SUF, CONTACT_ID, CONTACTTYPECODE, PRIMARY_IND
FROM   SCTRL_BA_CONTACT_ROLE
WHERE  CONTACTTYPECODE = 'PAY' AND PRIMARY_IND = 1
GROUP BY BA_NO, BA_SUF, CONTACT_ID, CONTACTTYPECODE, PRIMARY_IND
HAVING COUNT(*) > 1;

-- E. Stuck workflow instances / locks (§6)
SELECT * FROM <workflow instance table> WHERE STATUS IN ('In Progress','Post Pending')
  AND <fully-approved flag> = 1;        -- candidates for the remove-locks script (#1711015)

-- F. Core-interface cross-reference rows (MT100) — did the data have a path to move? (§8)
SELECT JOURNAL_ID, TRX_TYPE, * FROM SXREF_CORE_INTFC_QCFS_EXT
WHERE  JOURNAL_ID IN ('QCFS','ARCONV');  -- stale ARCONV/QCFS-GL rows are the usual culprits

-- G. Identity-sequence near max on the interface tables (§8)
SELECT IDENT_CURRENT('STRAN_CORE_INTFC')  AS stran_cur,
       IDENT_CURRENT('SEXTN_CORE_INTFC_JIB') AS sextn_cur;
-- Reseed (in a TRAN, after archiving):  DBCC CHECKIDENT (SEXTN_CORE_INTFC_JIB, RESEED, 0);

-- H. AFE actuals vs GL/subledger tie-out (§8, 25-01031530)
-- Compare AFE_SUBLEDGER totals to GENERAL_LEDGER for the AFE; a gap = missing MT100 config.

-- I. ADP import accounting-date inputs (§8, 24-00974384)
SELECT BILLING_IN_PROGRESS, PROCESS_PERIOD FROM JBCDE_BUSINESS_SEGMENT;  -- + global ADP_UPLOAD_AUTO_SET_ACCT_DATE

-- J. AFE-attribute staging for QQM (§11, 24-00938127)
SELECT COUNT(*) FROM QSTAG_AFE_ATTR_FLAT;  -- empty => run "Stage AFE Attributes"; check ENABLE_ATTRIBUTE_REPORTING
```

---

## 15. Expected-Behavior / User-Education FAQ

~61 Training + ~41 Customer-Error cases in this group. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| "User can't log in / see anything in Web" | **Email not populated** on the (correct) SEC_USER_ID, or the **username has a space instead of `_`**, or wrong client prefix — match it to the group/desk records | 26-01098577, 25-01063103, 24-00971869, 25-01007128 |
| "AFE not routing to the right approver" / "user not in Originating Desk list" | The user needs a **desk** (Cost Accounting: Desk Maintenance) and the **workflow route** must be updated to include the new desk | 26-01086524, 26-01084452 |
| "Can't open this screen" (Manual JE, AP055, etc.) | Missing **security group**; sometimes just **wrong order of operations** on the screen | 25-01008119, 25-01030514, 24-00976036 |
| "Can't attach a file" | The **file name has a special character (`'`) or is too long** — rename / print-to-PDF and re-attach | 24-00991782, 25-01058092, 25-01030421 |
| "Why does Web show different code-table values than Classic?" | **Expected** — Web does extra filtering; add the record on the ESuite code table, associate it to the xref, refresh ESuite cache | 25-01033015 |
| "Voided checks didn't void" / "batches stuck post pending" | User **ran the process without clicking Update/Save** first (CW020); or a **duplicate primary BA contact** | 25-01062132, 25-01035193 |
| "How do I edit/add a column to a QQM report?" | Training — open in Design Mode → Edit Data Provider → add object → Run Queries → Save | 25-01059274, 25-01051851 |
| "Okta lockout / how many attempts / IP flagged as malicious" | Lockout after **10 attempts**; "flagged as malicious" is usually the client's **VPN split-tunnel**, not Quorum | 25-01056137, 25-01027110 |
| "Change a Cost Center code / property on an existing record" | If no costs booked, **create a new CC and inactivate the old** (codes aren't editable in place) | 25-01018875 |
| "Prepayments didn't apply to AR" / "allocation property can't save" / setup how-tos | Walk-through / documentation; often a security or order-of-operations nuance, not a defect | 24-00977337, 24-00969000, 25-01027990 |
| "App crashes when left open / error on close" | Desktop session expiry or a known **Citrix LTSR 2405 bug** — use LTSR 2402 | 22-00866123, 22-00660010, 24-00970238 |

**Tell-tale it's user/expected:** a login/visibility problem that resolves by fixing the **email or username casing/prefix** on the security record; an AFE not routing because a **desk/route** wasn't set up; a screen "blocked" that just needs the **right security group**; an attach failure caused by the **file name**; a Web-vs-Classic data difference (Web filters more); or a "didn't save" caused by **not clicking Update**. Verify the **security record, desk/route, and the filename/order-of-operations** before treating it as a defect.

---

## 16. Key Screens, Processes & Repos

### Screens (Classic codes carry over to Web)
| Screen | Purpose | Cluster |
|---|---|---|
| **BA005 / Business Associate** | Vendor/owner master; contacts, JIB tab, special handling | §5 |
| **AP043 / AP055 / AP061 / AP150 / AP155 / AP157** | AP bank/zero-account setup, validation, batch post, ACH/check, payment recon | §6, §12 |
| **MT100 — Core Interface Cross Reference** | Maps which records flow between modules (MT/QCFS/JIB/GL, AFE→SL) | §8 |
| **GL013 / GL105** | Account JE Code Type; Custom Code Type Maintenance (Optional/Required/Not-Allowed code-block columns) | §8 (cross-ref FA skill) |
| **BK010 / BK040** | Bank/global payment-file staging & inquiry; positive pay | §12 |
| **CW020 / CI021 / CI022** | Check void / check import & edit | §12, FAQ |
| **Cost Accounting: Desk Maintenance** | AFE approval desks | §6, FAQ |
| **Maintenance app** → Locking → Lock Setup; FTP → FTP Transfer Definition; Connection Management; ESuite Cache Maintenance; ESuite Code Table Value | locks, FTP defs, ESB connections, cache, code tables | §7, §8, §9, §10 |

### Processes (run via QPEC)
| Process | Purpose | Notes |
|---|---|---|
| **POSTWKFL** | Post approved AP workflow batches | §6 — zero-bank-acct / contact-role errors |
| **AFE_IMPORT / AFEEXTIMP** | Import AFEs | §6 — process-lock stuck (26-01064522) |
| **QCFSIMPCYC / ADPUPLOAD / QCFS Import Cycle** | Import external/Open-Invoice/QCFS data | §8/§10 — MT100 config, lock retries (CFS_IMP) |
| **FAMTPOST / FAMTEDIT** | Material-transfer post/edit | §10 — concurrency lock (#1585578) |
| **PUBBA** | Publish/sync BA to integrated systems (QLS) | §5/§8 |
| **Stage AFE Attributes** | Populate `QSTAG_AFE_ATTR_FLAT` for QQM | §11 |
| **QSTG1099EX / JBOWNERALLOC / LOSDD_IMP / QP053 / QP063 / QP073** | 1099 staging, JIB owner alloc, LOS DD import, JIBLink/QLS/JPM exports | §8/§10 — timeouts, dynamic export |

### Config keys & tables seen in resolutions
`DOCMGMT/ENABLED`, `ZIPCODE_MASK_WEB`, `ADP_UPLOAD_AUTO_SET_ACCT_DATE`, `ENABLE_ATTRIBUTE_REPORTING`, `COMMAND_TIMEOUT_SECONDS` (18000s default), QPEC.ini Command Timeout; tables `SCTRL_BA_ENTITY`, `SCTRL_BA_CONTACT_ROLE`/`_ADDRESS`, `SXREF_CORE_INTFC_QCFS_EXT`, `STRAN_CORE_INTFC`, `SSTAG_CORE_INTFC`, `SEXTN_CORE_INTFC_JIB`, `QXRF_SECGRPID_CDTBL_ID`, `QSTAG_AFE_ATTR_FLAT`, `JBCDE_BUSINESS_SEGMENT`; code tables 224 (note category), 9131 (contact id), 29037 (zip mask), 34075 (business segment).

### Repos (upstream — discover via repo list if a code dive is needed)
Upstream/QCA code lives under the **On Demand / myQuorum** family in the **QuorumSoftware** ADO project. The BA-name, workflow-unlock, and FAMTPOST defects above are tracked as **QuorumSoftware** work items (#1711589/91, #1711015, #1585578). The application is largely **metadata/config-driven** (application layers, registered SQL, dynamic exports, picklist/grid definitions) — so most "fixes" are **config or data scripts**, not source changes. When a code dive is genuinely needed, search ADO code for the screen code (e.g. `BK040`, `MT100`), the process name (`FAMTPOST`, `POSTWKFL`), or the validation class (`QESUITEValidationBAEntity0024_DuplicateBAName`).

---

## 17. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A **Web screen** misbehaves on correct input: BA duplicate-name/save/autofill/field-clear (ADO #1711589/91, #1595163-70, #1528690); workflow instance not unlocking (#1711015); FAMTPOST/FAMTEDIT concurrency (#1585578); positive-pay GUI (24-00970244); idle-invoice dashboard count (24-00954896); file-name >100-char delete block (25-01030421).
- A behavior **regressed in an upgrade** and needs a port-back: ADPUPLOAD "fail one invoice in batch" (25-01006935); property/well Web↔Desktop sync (24-00990542).
- Provide: exact **screen code + error text**, the **SEC_USER_ID / BA / voucher / AFE**, client + environment + build, the **PQID** for a failed process, and a repro. Confirm fix availability in the **Upstream release notes / patch manifest** (Patch 11/12/15 stream).

**Handle as Configuration / data script when:**
- **MT100 Core Interface Cross Reference** missing/extra rows (25-01031530, 24-00950081); `SXREF_CORE_INTFC` stale row (25-01042240); `*_CORE_INTFC` identity reseed (23-00887308, 24-00953398).
- **Timeouts** → `COMMAND_TIMEOUT_SECONDS` / QPEC.ini Command Timeout (25-00998658, 24-00984129; remember to revert); **lock retries** → Lock Setup overrides (24-00944930).
- **Attachments/exports** → DocManagement stages / `DOCMGMT ENABLED` (25-01035711, 26-01095607), **FTP Transfer Definition** (23-00928933).
- **BA** trailing-space trim (26-01088113), EFF-DATE / contact-role / zip-mask config (25-01030212, 25-00999621, 25-01041976).
- **Upgrade config drift** → sync from DEV, correct application layer, rerun sysgen for nonsysgen-trigger collisions (25-01002439, 25-01000811, 25-01022895).

**Route to QCloud Ops (Cloud Outage / Platform — not Engineering) when:**
- **Okta/SSO** group membership & sync (25-01025966, 25-01032607), Citrix profile/OU/path (24-00985684, 25-01030148), NTFS permissions (25-01055839), VPN/Netscaler/Citrix-version (25-01051718, 24-00970238, 24-00938430), VPN tunnel / IP whitelist (26-01087585, 26-01081203), service restarts (QPECS, APS — 25-01027220, 23-00914164).

**Handle as Training / Expected behavior (no fix):** see §15 — login/visibility from email-or-username mismatch; AFE routing needing a desk/route; screen "access" needing the right security group; attach failures from the file name; Web-vs-Classic data differences (Web filters more); "didn't save" from not clicking Update. **Always verify the security record, desk/route, filename, and order-of-operations before treating it as a defect.**

---

*Skill created: 2026-06-14.*
*Based on: 656 closed QCA Platform/Workflow/Integration SF cases (Case_Category__c IN eSuite/Workflow/Security/Integration/QQM/Data Hub/Other) — 132 actionable (Application Configuration 90 + Software Defect 39 + ChangeConfig 3) mined for fix recipes, plus ~35 Training/Customer-Error cases for the FAQ and the User-Administration-Request pool for the security cluster. ADO work items #1711589/#1711591, #1595163/#1595164/#1595170, #1528690, #1444019/#1452583/#1541343, #1711015, #1661160/#1661268, #1481660, #1585578, #1644523/#1735154/#1741527.*
*Companion: SKILL_QCA_JIB.md, SKILL_QCA_AFE.md, SKILL_QCA_FixedAssets.md (and the LOS / Ad-Hoc Reporting / JEA skills).*
