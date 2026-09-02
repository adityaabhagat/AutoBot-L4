# SKILL: QPTM Security & User Administration Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-01 | **Product:** QPTM (My Quorum Gas Pipeline)
**Scope:** Login / SSO (Okta) / password / MFA, account provisioning & deactivation, Security User Setup, security groups / personas / permissions ("access denied", missing screens/tiles), external (TPA / shipper) user access, Business Associate (BA) screens & name-change, service-account password rotation, certificates.
**Companion:** For the TPA→security-user join and EDI-side SR/TSP identity errors see **SKILL_EDI_Troubleshooting.md §10, §15F**. For nom-screen permission symptoms see **SKILL_Nominations.md**.

> **Evidence base:** ~3,308 closed `Case_Category__c IN ('Security','Business Associates')` cases on `Product_list__c = 'My Quorum Gas Pipeline'` (Security is the single biggest QPTM category). **The dominant reality: this category is overwhelmingly an OPS RUNBOOK, not a defect queue** — see the split below. Every root-cause / defect claim cites a real SF case # and/or ADO work item.

---

## 0. The Split — Runbook vs. Defect (READ THIS FIRST)

`GROUP BY Root_Cause__c` over the 3,308 closed cases:

| Root Cause | Count | Disposition |
|------------|------:|-------------|
| **User Administration Request** | **2,556** | **§1 OPS RUNBOOK** — provision / reset / deactivate / MFA. Routine. |
| Business Change | 117 | Mostly account/access change requests → runbook or Services |
| *(null)* | 97 | Triage individually |
| **Application Configuration** | **79** | **§7–§9 deep-dive** (permissions, personas, security groups, screen access) |
| Training | 66 | §11 Expected behavior / educate |
| No Action Taken / Customer Cancelled | 105 | Closed without work |
| **Software Defect** | **44** | **§6, §8 deep-dive** (real bugs w/ ADO items) |
| Platform / HW-SW Env Change / Cloud Outage | 74 | Infrastructure / QCloud — not a code or config fix |
| User Setup Request | 17 | §1 runbook |
| Customer Error | 16 | §11 |
| Licenses / Performance / other | ~80 | Misc |

By **Resolution_Type__c**: `User Administration Complete` = **2,154**, `Configuration Changed` = 333, `Answered Questions` = 282, `Infrastructure Resolved` = 94, `Software Updated` = 34, `Data Script Provided` = 18.

**Bottom line:** ~78% of this queue (2,556 + 17 + much of "Business Change") is **routine user-admin handled with the §1 runbook** (no script, no ADO bug). Reserve deep diagnosis (§6–§10) for the **~123 `Software Defect` + `Application Configuration`** cases.

---

## TABLE OF CONTENTS

1. [USER ADMIN RUNBOOK (the 78%)](#1-user-admin-runbook-the-78)
2. [Concepts: Identity Stack & Security Model](#2-concepts-identity-stack--security-model)
3. [Quick Triage Checklist](#3-quick-triage-checklist)
4. [Symptom → Root-Cause Matrix](#4-symptom--root-cause-matrix)
5. [Login / SSO / MFA Cluster](#5-login--sso--mfa-cluster)
6. [Security User Setup Defects](#6-security-user-setup-defects)
7. [Permissions / Personas / Security Groups (Config)](#7-permissions--personas--security-groups-config)
8. [Business Associate (BA) Screens & Name Change](#8-business-associate-ba-screens--name-change)
9. [Service Accounts & Certificates](#9-service-accounts--certificates)
10. [Diagnostic SQL Queries](#10-diagnostic-sql-queries)
11. [Expected Behavior / User Education](#11-expected-behavior--user-education)
12. [Key Code Files & Repos](#12-key-code-files--repos)
13. [Database Tables Reference](#13-database-tables-reference)
14. [Known Historical ADO Bugs](#14-known-historical-ado-bugs)
15. [Escalation Decision Tree](#15-escalation-decision-tree)

---

## 1. USER ADMIN RUNBOOK (the 78%)

> These are `Root_Cause__c = 'User Administration Request'` / `Resolution_Type__c = 'User Administration Complete'`. **No code, no ADO bug, usually no SQL.** Most are executed by **QCloud / Cloud Ops** in Okta + the QPTM Security User Setup screen. L4's job: collect the exact identifiers, verify the right environment/client, route to QCloud or perform in-app, confirm with the client.

### Subject-line clusters (counts from the 2,556 runbook cases)

| Cluster | Typical subject patterns | Vol. signal |
|---------|--------------------------|-------------|
| **New Okta / external account** | "New Okta Account(s) - NAME", "Create New External User - NAME", "OKTA – New Security User – Quick Turnaround – NAME", "Pembina \| Add User \| NAME", "New user ID Commpass \| DATE" | Largest single cluster (hundreds) |
| **Password reset / activation link** | "Okta - Password Reset / Activation Link - EMAIL", "Okta Password Reset - NAME", "Resend Activation Link", "Send Reset Link to External User", "User ID reset \| DATE" | Very high |
| **Account disable / removal** | "Disable Okta Account(s) - NAME / MULTIPLE", "Remove DTE app from NAME", "Remove NAME Access" | High |
| **MFA** | "Reset MFA - NAME", "Okta One-time Password - NAME", "MFA Phone number update", "Customer not Receiving MFA Verifications Text", "Okta MFA Security Questions & Password Reset" | Medium |
| **Account update** | "Update Existing Okta Account", "Email Update", name/email change ("…changed her name and email…fix OKTA account") | Medium |
| **Lockout / can't login** | "User Locked Out", "User Unable to Login", "QCloud Login Error - NAME", "myQuorum Login Error - NAME" | Medium |
| **Group / persona assignment** | "Okta User Incorrect Group", "PNGTS Okta Groups", "Okta Admin Setup", "Okta Permission Error" | Medium (→ if app-side, see §7) |
| **Bulk / recurring jobs** | "Monthly Okta Internal User Extract Request" (16×), "TransGas Network Access Review" (5×), "Network Access Review" | Recurring scheduled |

### Runbook procedures

**A. Provision a new user (external shipper / TPA or internal)**
1. Collect: full name, **login email**, client/TSP, environment (PRD/UAT/DEV), the **persona / security group** they should get, and the **BA / shipper company** (for external). Many clients submit via a standard intake (DTE, Pembina, Summit, Commpass templates).
2. New external users need **both** (a) an Okta account and (b) a QPTM **Security User** record mapped to the right **security group(s)/persona** and **BA**. Okta alone is not enough — without the QPTM persona they log in but see **no tile / no menu** (cases 26-01094136, 26-01095187).
3. QCloud creates the Okta account + group membership; the QPTM Security User Setup maps groups/personas/TSPs/BAs.
4. Send the activation link; confirm the user can log in and see the correct tile.
> **Gotcha (26-01089784):** Azure-AD-group → Okta auto-provisioning fails if the person had a **prior Okta account left in *suspended* state** — the new login matches the old suspended account. Fix: delete/clear the old suspended account, then retry.
> **Gotcha (26-01013059 / 25-01013059):** assigning a BA to a user in Integrated User Setup can throw a **"unique constraint" error** — the user↔BA link already exists; remove the dup mapping rather than re-adding.

**B. Password reset / resend activation**
- Initiate the Okta password reset / send activation (one-time-password) link to the user's email. If "the verification-email link just loops back to Login and never lets them set a password" → **Okta/AD sync issue**, escalate to QCloud (case 25-01041322, WEMBLEY_PLANTSTATION).
- "Verification email never comes" → check the email is correct & not blocked; QCloud can re-trigger (25-01027285).

**C. Unlock an account**
- Web/Okta lockouts after failed attempts: unlock in Okta. If unlock link loops without letting them reset → AD sync (escalate QCloud). Citrix-vs-Web lockouts can differ — confirm which client they use (22-00688202, 22-00686175).

**D. MFA**
- Reset MFA enrollment, send one-time password, or update the registered phone. If MFA prompts aren't appearing at all for a whole environment, that's a **QCloud Okta-policy config**, not per-user (23-00903667 → QCloud ticket; see §5).

**E. Deactivate / remove access**
- Confirm scope (single user vs. "MULTIPLE"); disable the Okta account and/or remove the QPTM security-group/app assignment. "Remove DTE app from NAME" = remove that chiclet/app, not delete the whole account.
> **Gotcha (26-01092423):** the **security-user deletion script** historically also removed the **TSP** from the user's security record, requiring manual re-add. The corrected script **excludes the TSP table** (added a `WHERE … NOT IN` clause). If you deploy a bulk user-removal script, **confirm it does not strip TSP assignments** from users who remain.

**F. Recurring / scheduled runbook items**
- "Monthly Okta Internal User Extract Request" (16×): standard monthly Okta user export — fulfill and close.
- "Network Access Review" / "TransGas Network Access Review": periodic access-recertification; provide the user/group listing.

### What to verify before closing any runbook case
```
[ ] Correct environment (PRD vs UAT vs DEV) and correct client/TSP
[ ] External user has BOTH Okta account AND QPTM persona/group + BA mapping
[ ] User can actually log in and see the expected tile/menu (not just "account created")
[ ] Deactivations: scope confirmed; remaining users' TSP assignments intact (26-01092423)
[ ] No prior suspended Okta account blocking auto-provisioning (26-01089784)
```

---

## 2. Concepts: Identity Stack & Security Model

### The identity stack (cloud QPTM)
```
[User] → Okta (auth, MFA, groups)  ──SSO/OpenID──>  myQuorum portal (tile/chiclet)
                                                      → QPTM Web / Classic (eSuite)
                                                         → Security User record + Security Group(s) + Persona
                                                            → screen/object permissions, TSP scope, BA scope
```
- **Okta** owns authentication, MFA, password, and the Azure-AD-group→Okta-group mapping (managed by **QCloud**). Most "can't log in / reset / MFA" cases stop here.
- **myQuorum portal** shows **tiles/chiclets** per app+environment. "No tile" usually = missing **persona/group** mapping on the QPTM side, even though Okta login succeeded (26-01094136).
- **QPTM Security** (in-app): a **Security User** belongs to one or more **Security Groups**; **Personas** (e.g., *Pipeline Scheduler*, *Pipeline Internal*, *Shipper*) bundle screen/object access; access is scoped by **TSP** and, for external users, by **BA**. Edited in **Security User Setup** (Web) / **Integrated Security Setup** (Classic).

### Personas seen in cases
`Pipeline Scheduler`, `Pipeline Internal`, `Shipper` — switching a user's persona requires the app to pick up the change; a **stale security cache** can prevent it (26-01095187, see §7).

### Security objects
Screens are gated by a **security object** code (e.g., `QVPTYPEOFCHARGEMAINTENANCE` for Type-of-Charge setup — 24-00949766). If a screen is read-only/missing for a group, the group may lack the right security object even if it "looks" assigned.

---

## 3. Quick Triage Checklist

```
[ ] 1. Is this just provisioning/reset/deactivate/MFA?  → §1 RUNBOOK, stop here.
[ ] 2. Exact symptom: can't log in? logged in but no tile? logged in but screen/menu missing/read-only? save error?
[ ] 3. Okta layer or QPTM layer? (login/MFA/password = Okta/QCloud; tile/persona/screen = QPTM)
[ ] 4. Internal or External (shipper/TPA) user? External adds BA-scope + tile concerns.
[ ] 5. Which environment (PRD/UAT/DEV) and which client/TSP?
[ ] 6. Web or Classic (Citrix/eSuite)? Several bugs are Web-only (notice types, BA save, TOC setup).
[ ] 7. User ID / login email / BA / security group / persona involved?
[ ] 8. QPTM version (e.g., 2022.10, 2023.04, 2024.04, 2025.04, 2025.10)? Many fixes are version-gated.
[ ] 9. One-off or affecting many users / whole environment? (env-wide MFA/login = QCloud config/outage)
[ ] 10. Did a recent change happen? (upgrade, BA name change/acquisition, deletion-script run)
```

---

## 4. Symptom → Root-Cause Matrix

| Symptom | Most common root cause | Layer / Fix type | Evidence |
|---------|------------------------|------------------|----------|
| New external user logs in but **sees no tile / no persona** | Missing QPTM persona/group mapping (Okta-only provisioned) | QPTM config | 26-01094136, 26-01095187 |
| Persona switched (e.g., to Pipeline Scheduler) but **app not honoring it** | **Stale security cache** — clear security cache / run cache maintenance | QPTM config | 26-01095187 |
| External user "set up" but **can't log in** | Okta/AD sync or account state; verify Okta side | Okta/QCloud | 25-01044701, 25-01065383→26-01065383, 25-01041322 |
| New **internal** user not in Okta Admin, can't add to groups | Provisioning not completed in Okta; QCloud adds to QPTM groups | QCloud | 25-01052456 |
| Azure-AD-group auto-provisioning **doesn't create Okta user** | **Pre-existing suspended Okta account** matched | Okta/QCloud | 26-01089784 |
| Whole environment **not prompting MFA** | Okta MFA-policy config | QCloud config | 23-00903667 |
| Unlock link **loops back to Login**, can't set password | Okta/AD sync | QCloud | 25-01041322 |
| **"unique constraint"** error assigning BA to user | Duplicate user↔BA mapping in user setup | QPTM config | 25-01013059 |
| Bulk user-**deletion script also removed TSP** from remaining users | Script over-scoped (included TSP table) | Data script fix | 26-01092423 |
| Security User Setup **won't save Notice Types** (Web) | Web-only save defect (Classic worked) | Code defect | 22-00804903, 24-00986453 |
| Notice Type sub-types **not cleared** when type changes | Notice-posting defect | Code defect | ADO #1556308, #1721675 |
| Screen addable in Classic but **read-only/missing in Web** (TOC setup) | Web security-object / eSuite setup mismatch | Data script / config | 24-00949766 |
| **"Factory QCFSDataHelper does not exist"** on BA save (2024.04) | BA-screen data-helper defect | Code defect | 25-00999022, ADO #1709045, #1718362 |
| BA Contact / Company-Additional-BAs **save fails** (Web only) | BA-save trigger/data defect | Code defect | 24-00946543, 24-00955015 |
| **BA name-change** shows wrong previous name / wrong history / downstream errors | BA name-change history defect cluster | Code/release/data script | 24-00957884, ADO #1670424, #1575870, #1774649, #1550323 |
| New/changed **TSP name not reflected** for existing BA contacts | Existing-BA-contact window not refreshing TSP name | Code fix (minor) | 24-00965037 |
| Previous pool manager **can still see** switched customer's pool | Security scoping missing on a tab | Code fix | 22-00693292 |
| "Security User cannot be updated" in Security User Setup | Setup-screen update defect | Code/config | 22-00530978, ADO #1448962 |
| Service account password rotation (SRV_QPTM_QPEC_*) | Routine credential rotation | Config | 25-01028881, 24-00957348 |
| Certificate (…seiweb.net / EDI SSL) expiring | Cert renewal | Config | 25-00998617, 24-00992298, 23-00913817 |

---

## 5. Login / SSO / MFA Cluster

Most volume here is **§1 runbook**. The non-routine subset:

- **Env-wide no-MFA-prompt (23-00903667):** users not prompted for MFA at all → **QCloud Okta-policy config**, fixed on myQuorum-Cloud work item **#1603171**. Not a per-user reset, not a QPTM code change.
- **Global login outage (25-01051684):** "Unable to get into QPTM this morning, co-workers too" → check for a **QCloud global outage** before treating as user-specific. Resolution_Type = *Infrastructure Resolved*.
- **Okta/AD sync (25-01041322):** unlock/verification link loops back to Login → AD sync repair by QCloud.
- **Auto-provisioning blocked by suspended account (26-01089784):** see §1-A gotcha.
- **Login page broken / 400 on Sign Out / "browser not supported" (23-00912181, 23-00916813, 25-01034888):** portal/infra or browser-support config, not in-app security.

> **Rule of thumb:** if it's authentication, MFA, password, the portal login page, or "whole company can't log in," it's **Okta / QCloud / infrastructure** — route there, don't hunt QPTM code.

---

## 6. Security User Setup Defects

In-app **Security User Setup** (Web) / **Integrated Security Setup** (Classic). Recurring theme: **Web-only** save/persist defects where Classic worked.

| Issue | Root cause | Fix | Evidence |
|-------|-----------|-----|----------|
| Notice Types **not saving** in Web Security User Setup (Critical notices missing from Resolve-User tab) | Web save defect; Classic saved fine (workaround = set in Classic) | Software Updated | 22-00804903 |
| After 2024.04 upgrade, **Information Disclosures / Invoice notice types unchecked** for all users | Upgrade regression on notice-type persistence | Software Updated | 24-00986453 |
| Notice **sub-types not cleared** when the notice type changes | Notice-posting defect | Closed/Fixed | ADO #1556308 (2022.10), #1721675 (2025.04) |
| "Security User **cannot be updated**" in Setup screen (Web & Classic) | Setup update defect | Config change | 22-00530978, ADO #1448962 (ETC) |
| Client-specific notice types need adding to Security User Setup | Requirement/PR | Closed | ADO #1593113 (CMX) |

**Diagnostic:** reproduce in **both Web and Classic** — if Classic persists and Web doesn't, it's the Web setup-screen defect; Classic is the interim workaround. Check the user's notice-type rows after save (see §10 query D).

---

## 7. Permissions / Personas / Security Groups (Config)

The bulk of `Application Configuration` cases. The user **can log in** but can't see/do something.

### Common patterns & fixes
| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| External user logs in, **no tile / no persona** | Persona/group not mapped on QPTM side | Assign persona/group; confirm tile | 26-01094136 |
| Persona switched but **app still uses old access** | **Stale security cache** | Clear security cache + run **Cache maintenance**; if still stale, escalate | 26-01095187 |
| Screen addable in Classic but **read-only/missing in Web** | Wrong/missing **security object** on the group; eSuite setup not moved | Verify security object (e.g. `QVPTYPEOFCHARGEMAINTENANCE`); move eSuite setup / data script | 24-00949766 |
| User can't run **batch processes** (PADAILY) | Missing batch-process permission/role | Config (grant) | 25-01009441 (reopen of 24-00992429) |
| Missing **Citrix/Commpass app** (sees myQuorum but not PROD Citrix) | App-assignment gap | Config (assign app) | 25-01016460, 24-00958158 |
| Group still shows old company name after acquisition | Security-group naming carries old client name | Services-managed rename | 25-01021569 (EGWEST), 23-00933484 |
| Remove a TSP from Security User Setup for a client | TSP-scope cleanup | Config | 24-00970850 (MGD SWGN), 23-00933484 |
| Remove a tab/screen from a persona's tree view | Persona tree config | Config | 23-00906959 (Shipper "Contracts" tab) |
| Web security group missing screens it has in Classic | Web/Classic security-object parity gap | Config | 23-00906597 (CMX Medición) |
| Previous pool manager **sees switched customer's pool** | Security scoping not applied to a tab | Code fix (scope the tab) | 22-00693292 |

### How to investigate a permission case
1. Confirm the user **can log in** (else it's §5/Okta).
2. Identify the **persona / security group(s)** and **security object** behind the screen they need. Developer/admin rights bypass the issue — reproduce as the affected group.
3. If a persona change "won't take" → **clear security cache + Cache maintenance** (26-01095187) before assuming a deeper defect.
4. Verify **TSP scope** (user must have the TSP) and, for external, **BA scope**.
5. For Web-vs-Classic gaps, check the security-object parity (24-00949766, 23-00906597).

---

## 8. Business Associate (BA) Screens & Name Change

The `Business Associates` category (40 cases) plus BA-screen defects in Security. Two clusters: **BA save/data defects** and the **BA name-change history** cluster.

### BA save / data defects
| Issue | Root cause | Fix | Evidence |
|-------|-----------|-----|----------|
| **"Factory QCFSDataHelper does not exist"** on creating/saving a BA (2024.04) | BA-screen data-helper factory defect (also hits Royalty Payment Type) | Software Updated | 25-00999022; ADO **#1709045**, **#1718362** |
| **Company Additional BAs** tab save fails (Web only; Classic OK) | BA-save trigger/data defect | Software Updated | 24-00946543 |
| BA Contact **address / zip** save fails ("zip doesn't match configured formatting") — not reproducible in core | Client-data/config | Data Script Provided | 24-00955015 |
| BA Contact screen **missing "add contact type"** / missing fields in Web | Web BA-contact parity gap | Config | 23-00913226, 25-01034395 |
| BA address update fails on upgrade UAT | BA-screen config | Config | 26-01068855 |

### BA name-change cluster
When a client renames a BA (often after an **acquisition**, e.g., Dominion→Enbridge), several defects surface:

| Issue | Root cause | Fix | Evidence |
|-------|-----------|-----|----------|
| Name-change **effective date shows wrong previous business name** | BA name-change history defect (APL 2023.04) | Release Upgrade Required + **script to clean up BA Name Change History** | 24-00957884; ADO **#1670424** (Script Review) |
| BA Name Change **History tab is editable** (shouldn't be) | History-tab defect | Bug (Proposed) | ADO **#1550323** |
| **New TSP name not reflected** for existing BA contacts after a TSP rename | Existing-BA-contact window not refreshing | Minor code fix / hotfix | 24-00965037 |
| EDI process completing with downstream-BP error **after BA name change** | Name change not propagated downstream | Bug Closed | ADO **#1575870** (DTE) |
| Owner Search (Checks tab) pulls **incorrect data after BA name change** | Name-change data linkage | Bug Closed | ADO **#1774649** (APH) |
| BA name changes don't auto-carry to `REC_BA_NM`/`DEL_BA_NM` on noms | Feature gap (not a bug) | Feature (Proposed) | ADO **#1356810** |
| BA showing name-change history in UAT (Symmetry Energy) | History display defect | Data Script Provided | 26-01085407 |

> **L4 takeaway on BA name change:** treat acquisition-driven renames as a **known multi-symptom cluster**. The fix is frequently a **BA-name-change-history cleanup script** (ADO #1670424) plus a hotfix/upgrade — *not* a config toggle. Check downstream (noms `REC_BA_NM`/`DEL_BA_NM`, EDI BP errors, Owner Search) before closing.

---

## 9. Service Accounts & Certificates

Routine but recurring in this category:
- **Service-account password rotation** `SRV_QPTM_QPEC_{DEV|UAT|PRD}` (25-01028881, 24-00957348, plus DEV variant) — coordinated credential change; *Configuration Changed*. Rotate in all dependent layers (middle tier / batch / EDI) to avoid login failures.
- **Certificate renewals** — `*.seiweb.net` (TransGas: 25-00998617, 24-00992298), partner **EDI SSL** certs (Tenaska 23-00913817). Track expiry; renew before the date or logins/EDI break. *Configuration Changed* / Infrastructure.
- `housftp.qbsol.net not working` (26-01103060) — SFTP host access, handled as user-admin/infra.

---

## 10. Diagnostic SQL Queries

> Security tables follow the `QARCH_*` convention used elsewhere in QPTM (see EDI skill §15F for the TPA→security-user join, which uses `QARCH_SECURITY_USER`). Replace `<PLACEHOLDER>` tokens. Confirm exact column names against the live schema (code: `SecurityUserDAL.cs` / `SecurityGroupDAL.cs`).

### A. Look up a security user
```sql
SELECT su.SECURITY_USER_ID, su.USER_NM, su.USER_TYPE_CD, su.EMAIL,
       su.IS_ACTIVE, su.IS_LOCKED, su.LAST_LOGIN_DT
FROM QARCH_SECURITY_USER su
WHERE su.USER_NM = '<USER_ID>' OR su.EMAIL = '<LOGIN_EMAIL>';
```

### B. A user's security groups / personas
```sql
SELECT su.SECURITY_USER_ID, su.USER_NM,
       sg.SECURITY_GROUP_ID, sg.SECURITY_GROUP_NM, sg.PERSONA_CD
FROM QARCH_SECURITY_USER su
JOIN QARCH_USER_SECURITY_GROUP usg ON usg.SECURITY_USER_ID = su.SECURITY_USER_ID
JOIN QARCH_SECURITY_GROUP       sg  ON sg.SECURITY_GROUP_ID = usg.SECURITY_GROUP_ID
WHERE su.USER_NM = '<USER_ID>';
```

### C. TSP scope for a user (the row a bad deletion script can strip — 26-01092423)
```sql
SELECT sut.SECURITY_USER_ID, sut.TSP_NO
FROM QARCH_SECURITY_USER_TSP sut
WHERE sut.SECURITY_USER_ID = <SECURITY_USER_ID>
ORDER BY sut.TSP_NO;
-- After a bulk user-removal script, confirm remaining users STILL have their TSP rows here.
```

### D. Notice-type preferences for a user (Web save defect — §6)
```sql
SELECT nt.SECURITY_USER_ID, nt.NOTICE_TYPE_CD, nt.SUB_TYPE_CD, nt.IS_SELECTED
FROM QARCH_SECURITY_USER_NOTICE nt
WHERE nt.SECURITY_USER_ID = <SECURITY_USER_ID>
ORDER BY nt.NOTICE_TYPE_CD;
-- After saving in Web, confirm Critical / Information Disclosure / Invoice rows persisted (22-00804903, 24-00986453).
```

### E. External user → BA scope (and the TPA/security-user link)
```sql
-- See EDI skill §15F for the canonical TPA join. External-user BA scope:
SELECT su.USER_NM, ub.BA_NO, ba.BA_NM, ub.IS_ACTIVE
FROM QARCH_SECURITY_USER su
JOIN QARCH_USER_BA ub ON ub.SECURITY_USER_ID = su.SECURITY_USER_ID
JOIN NNCTRL_BP     ba ON ba.BA_NO = ub.BA_NO
WHERE su.USER_NM = '<USER_ID>';
-- Missing/duplicate rows here drive "no tile" and the "unique constraint" error (26-01094136, 25-01013059).
```

### F. Security object behind a screen (Web-vs-Classic parity — 24-00949766)
```sql
SELECT sg.SECURITY_GROUP_NM, so.SECURITY_OBJECT_CD, sgo.CAN_ADD, sgo.CAN_EDIT, sgo.CAN_VIEW
FROM QARCH_SECURITY_GROUP        sg
JOIN QARCH_SECURITY_GROUP_OBJECT sgo ON sgo.SECURITY_GROUP_ID = sg.SECURITY_GROUP_ID
JOIN QARCH_SECURITY_OBJECT       so  ON so.SECURITY_OBJECT_ID = sgo.SECURITY_OBJECT_ID
WHERE so.SECURITY_OBJECT_CD = '<OBJECT_CD>';  -- e.g. 'QVPTYPEOFCHARGEMAINTENANCE'
```

---

## 11. Expected Behavior / User Education

`Root_Cause__c = 'Training'` (66) and `Customer Error` (16). Recognize these to avoid unnecessary scripts/escalations.

| Reported as | Reality | Disposition |
|-------------|---------|-------------|
| "User can't see screen X" | Their persona/group legitimately excludes it — explain or request the right group | Educate / config request |
| "Notice types keep unchecking" (post-2024.04) | Was a real defect (§6) — but verify version; on fixed versions it's user re-save | Educate / verify version |
| "External shipper can't see Informational Postings menu" | Menu visibility by persona/config — document the setup | Documentation Provided (24-00968667) |
| "How do I set up a new user / group?" | Provide the Security User Setup how-to | Documentation |
| "Browser not supported" | Use a supported browser/version | Documentation (25-01034888) |
| Acquisition rename "old company name still shows" | Some of this is **Services-managed** group renaming, not support config | Route to Services (25-01021569) |

---

## 12. Key Code Files & Repos

### Quorum.QPTM.Web (41e317c0-844c-4728-98da-529092957738)
| File | Purpose |
|------|---------|
| `Quorum.QPTM.DAL/CodeGen/SecurityUserDAL.cs` | Security User data access (CRUD on the security-user record) |
| `Quorum.QPTM.DAL/CodeGen/SecurityGroupDAL.cs` | Security Group data access |
| `Quorum.QPTM.DataObject/CodeGen/SecurityGroupDO.cs` | Security Group data object |
| `Quorum.QPTM.DataCache/CacheObjects/SecurityUserCache.cs` | **Security-user cache** — stale cache causes persona-change-not-honored (26-01095187) |
| `Quorum.QPTM.DataCache/Resolvers/ResolverSecurity/ResolverSecurityAccess.cs` | Resolves a user's effective access/scope |
| `Quorum.QPTM.CoreInterface/Constants.cs` | Persona / security constants |

### Quorum.QFC.Web (shared framework — myQuorum/eSuite)
| File | Purpose |
|------|---------|
| `Quorum.QFC.Web.Core/Utilities/QWebUtilities_Persona.cs` | **Persona utilities** (tile/persona resolution — "no tile" cases) |

### Quorum.SystemManager
| File | Purpose |
|------|---------|
| `Quorum.SystemManager.CmdLibrary/QSysMgrCmdMetaDataService.cs` | `ClearSecurityCache` / Cache maintenance (the §7 fix for stale persona) |

### Override repos
`<CLIENT>.QPTM.Web` (e.g., **ETC**, **APL**, **APH**, **DTE**, **CMX**, **TGL**) carry client-specific security tests/overrides (e.g., `TGL.QPTM.UnitTests/QFCSecurityTest.cs`). **Check for a client override before assuming base behavior.** Code search: `{"searchText":"SecurityUser repo:<CLIENT>.QPTM"}`.

---

## 13. Database Tables Reference

| Table | Purpose |
|-------|---------|
| `QARCH_SECURITY_USER` | **Security user record** (login, type INT/EXT, active/locked) — confirmed via EDI skill TPA join |
| `QARCH_SECURITY_GROUP` | Security group / persona definitions |
| `QARCH_USER_SECURITY_GROUP` | User↔group membership *(verify exact name in schema)* |
| `QARCH_SECURITY_USER_TSP` | **User TSP scope** — the table a bad deletion script stripped (26-01092423) *(verify name)* |
| `QARCH_USER_BA` | External-user→BA scope *(verify name)* |
| `QARCH_SECURITY_USER_NOTICE` | User notice-type preferences (§6 Web save defect) *(verify name)* |
| `QARCH_SECURITY_OBJECT` / `QARCH_SECURITY_GROUP_OBJECT` | Screen security objects + per-group rights (e.g. `QVPTYPEOFCHARGEMAINTENANCE`) *(verify names)* |
| `NNCTRL_BP` | Business Partner / BA definitions (name, active) — BA name-change cluster |
| `NNCTRL_TPA` | Trading Partner Agreements (links external shipper to security user — see EDI skill §15F) |

> **Data-quality note:** `QARCH_SECURITY_USER` is corroborated by the EDI skill's working TPA join and by `SecurityUserDAL.cs`. The membership/scope/notice/object table names marked *(verify)* are inferred from the `QARCH_*` convention + code-search class names; confirm exact spelling against the live schema or `SecurityUserDAL.cs`/`SecurityGroupDAL.cs` before scripting. The almsearch index returned 0 hits for the literal `QARCH_SECURITY_*` strings (likely an indexing/casing limitation), so names were not verbatim-confirmed from raw DDL.

---

## 14. Known Historical ADO Bugs

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|-------|--------------|-----------------|---------|---------|
| **#1709045** | Bug / **Closed** | 25-00999022 — BA Create New Entity "Factory QCFSDataHelper does not exist" on save | §8 BA save | 25-00999022 |
| **#1718362** | Bug / **Closed** | 25-01002942 / 24-00979256 — CNX 2022.04 Royalty Payment Type "Factory QCFSDataHelper does not exist" (BA Web screens) | §8 BA save | 25-01002942 |
| **#1670424** | Requirement / **Closed** | APL — Script Review 24-00957884 — Clean Up BA Name Change History | §8 BA name change | 24-00957884 |
| **#1575870** | Bug / **Closed** | DTE 23-00881799 — EDI Process completing w/ downstream BP error after BA Name Change | §8 BA name change | 23-00881799 |
| **#1774649** | Bug / **Closed** | APH 25-01061823 — Owner Search (Checks tab) pulls incorrect data after BA name change | §8 BA name change | 25-01061823 |
| **#1550323** | Bug / **Proposed** | 2022.10 — BA Name Change History tab is editable | §8 BA name change | — |
| **#1356810** | Feature / **Proposed** | Make BA Name changes auto-carry to REC_BA_NM/DEL_BA_NM on noms | §8 (enhancement) | — |
| **#1448962** | Bug / **Closed** | ETC 22-00255521 — Security User cannot be updated in Security User Setup (Web & Classic) | §6 | 22-00530978 |
| **#1556308** | Bug / **Closed** | 2022.10 — Notice Posting sub-types not cleared on Notice Type change | §6 notice types | — |
| **#1721675** | Bug / **Closed** | 2025.04 — Notice Posting old subtype persists after type change | §6 notice types | — |
| **#1593113** | Requirement / **Closed** | CMX — add client-specific Notice Types to Security User Setup | §6 notice types | — |
| **#1603171** | myQuorum Cloud config / Closed | Okta MFA-prompt configuration | §5 MFA | 23-00903667 |

> **Takeaway:** the genuine **code defects** here cluster in two places — **BA screens** (QCFSDataHelper factory + name-change history) and **Security User Setup notice-type persistence (Web)**. Everything else is **runbook (§1)**, **QCloud/Okta infra (§5)**, or **in-app config (§7)**. There is **no high-volume single product bug** — unlike Nominations' duplicate-nom cluster, Security is dominated by routine user administration.

### Verbatim fix scripts captured
**None applicable / none safely reconstructable.** Unlike the Nominations nom-delete scripts, the Security defect/config subset does **not** rely on standardized verbatim SQL:
- The only script-flavored items are (a) the **BA-Name-Change-History cleanup** (ADO #1670424 — a *Script Review*, client-specific to APL, not a reusable template) and (b) the **bulk user-deletion script** behind 26-01092423. For (b), the only durable, transferable lesson is the **fix logic** (not a full reusable script): the corrected version **removed the TSP table from the delete and added a `WHERE ... NOT IN (...)` guard** so it stops stripping `QARCH_SECURITY_USER_TSP` rows from users who remain. Treat any bulk security-user delete with the same caution as the §4 nom-delete scripts in SKILL_Nominations.md: **verify-SELECT first, scope tightly, and never let it touch the TSP-scope table for users you are keeping.**

---

## 15. Escalation Decision Tree

```
Security / User-Admin case reported
│
├─ Provision / reset / unlock / deactivate / MFA / activation link?  (§1)
│   └─ RUNBOOK → collect identifiers, route to QCloud or do in-app, verify login+tile, close.
│      ├─ External user? → must have BOTH Okta acct AND QPTM persona/group + BA.
│      └─ Bulk deactivation script? → confirm it does NOT strip TSP scope (26-01092423).
│
├─ Can't log in / no MFA prompt / login page broken / "whole company down"?  (§5)
│   ├─ Env-wide / many users → QCloud Okta config or global OUTAGE (23-00903667, 25-01051684)
│   ├─ Unlock link loops / verification never works → Okta/AD sync → QCloud (25-01041322)
│   └─ Auto-provision didn't create user → check for prior SUSPENDED Okta acct (26-01089784)
│
├─ Logged in but NO TILE / wrong persona not taking?  (§7)
│   ├─ No tile → missing QPTM persona/group mapping → assign (26-01094136)
│   └─ Persona change ignored → CLEAR SECURITY CACHE + Cache maintenance (26-01095187)
│
├─ Logged in but a SCREEN/MENU missing, read-only, or batch denied?  (§7)
│   ├─ Web vs Classic parity gap → check security object (24-00949766, 23-00906597)
│   ├─ Can't run batch (PADAILY) → grant batch permission (25-01009441)
│   └─ Missing Citrix/Commpass app → assign app (25-01016460)
│
├─ Security User Setup won't SAVE (notice types, user update)?  (§6)
│   ├─ Web fails, Classic works → Web setup defect; Classic = interim workaround (22-00804903)
│   └─ Post-upgrade regression → check version, link ADO (24-00986453)
│
├─ Business Associate screen?  (§8)
│   ├─ Save error "Factory QCFSDataHelper..." → BA-screen defect (ADO #1709045/#1718362)
│   ├─ Company-Additional-BAs / contact / address save fails (Web) → BA-save defect (24-00946543)
│   └─ BA NAME CHANGE wrong/history/downstream → known cluster; cleanup script + hotfix
│        (24-00957884, ADO #1670424/#1575870/#1774649) — check noms/EDI/Owner Search too
│
├─ Service account / certificate?  (§9)
│   └─ Rotate creds in all layers / renew cert before expiry (25-01028881, 25-00998617)
│
└─ "How do I…" / persona legitimately excludes the screen?  →  §11 Educate / Documentation
```

---

*Skill created: 2026-06-01*
*Evidence base: ~3,308 closed QPTM Security/Business Associates SF cases. Split: ~2,573 User Administration runbook vs. ~123 Software Defect + Application Configuration deep-dive.*
*ADO work items: #1709045, #1718362, #1670424, #1575870, #1774649, #1550323, #1356810, #1448962, #1556308, #1721675, #1593113, myQuorum Cloud #1603171.*
*Companion: SKILL_EDI_Troubleshooting.md (§10/§15F TPA→security-user), SKILL_Nominations.md. Applicable to all QPTM TSPs/clients.*
