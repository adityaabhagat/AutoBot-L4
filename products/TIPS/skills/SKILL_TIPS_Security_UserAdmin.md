# SKILL: TIPS Security & User Administration Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-11 | **Product:** My Quorum TIPS
**Scope:** Everything in the **Security** and **Business Associates** case categories: external/internal **OKTA & QCloud** user provisioning (create / activate / unlock / reset / deactivate / email-update / add-to-group / mirror-access), **CAW / myQuorum web** login & activation, **ESUITE security groups & report-type privileges** (Read-Only, Super User, persona/role setup), **read-only Oracle DB accounts** (Databricks/Snowflake/reporting IDs, ORA resource-limit errors), **SSO / SAML certificate renewal** to Okta, **Secure Gateway** DB repointing after a TIPS upgrade, and **BA (Business Associate) Entity screen** setup/validation.
**Use when:** the case mentions OKTA, QCloud, CAW, myQuorum login, "external user", "provision/activate/unlock/reset", "add to Okta group", "security group", "Read Only", "Super User", persona, "RO database account", `*_READ_ONLY`, ORA-0239x, "SSO cert", "Secure Gateway", or the **BA Entity / Business Associate** screen.
**Companion:** The external **portal data layer** (CAWDATA replication, web-screen rendering of statements) lives in **SKILL_TIPS_CAW.md** — that skill and this one overlap on "external user can't log in"; this skill owns the **identity/security/account** side (OKTA, groups, DB accounts, certs), CAW owns the **data-sync/rendering** side. Internal app config beyond security lives in **SKILL_TIPS_System_Configuration.md**.

> **Evidence base:** ~519 closed TIPS cases in `Case_Category__c IN ('Security','Business Associates')` (Security 508, Business Associates 12). Root-cause split: **User Administration Request 421**, Business Change 42, **Application Configuration 15**, Training 11, Customer Cancelled 7, No Action Taken 6, Cloud Outage 5, Customer Error 5, null 5, Platform 2, Database Refresh 1. **Only 15 cases are "actionable"** (Root Cause = Application Configuration; there were **zero** Software Defect or ChangeConfig in this group) — this category is overwhelmingly **routine user-admin fulfillment**, not product defects. Every claim below cites a real SF case number and/or ADO work item observed during mining.
>
> **Data-quality caveat:** This category is the noisiest of all TIPS groups for triage purposes — ~80% of volume is one-off "create/unlock/reset a named user" tickets with terse or null resolutions ("External Okta user request", "OKTA External User", "created", "Sent password reset email"). The technical signal is concentrated in the 15 Application-Config cases plus a handful of Training/Customer-Error education answers. Treat the user-admin clusters as **runbook routing**, not RCA.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [How TIPS Identity & Security Works](#2-how-tips-identity--security-works)
3. [Decision Tree](#3-decision-tree)
4. [OKTA / QCloud External User Lifecycle (DOMINANT — ~400 cases)](#4-okta--qcloud-external-user-lifecycle)
5. [Login / Activation / Lockout / "doesn't exist in tenant"](#5-login--activation--lockout)
6. [ESUITE Security Groups & Report-Type Privileges (Read-Only / Super User / Persona)](#6-esuite-security-groups--report-type-privileges)
7. [Read-Only Oracle DB Accounts (Databricks / Snowflake / Reporting)](#7-read-only-oracle-db-accounts)
8. [SSO / SAML Certificate Renewal to Okta](#8-sso--saml-certificate-renewal)
9. [Secure Gateway / DB Repointing After Upgrade](#9-secure-gateway--db-repointing-after-upgrade)
10. [Business Associate (BA) Entity Screen](#10-business-associate-ba-entity-screen)
11. [Known ADO Items](#11-known-ado-items)
12. [Diagnostic SQL](#12-diagnostic-sql)
13. [Expected-Behavior FAQ](#13-expected-behavior-faq)
14. [Escalation Guidance](#14-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom | Likely cause | First check / first action |
|---------|-------------|----------------------------|
| "Provision OKTA account" / "New CAW User Setup" / "Add user to our Okta group" | Routine user-admin request | Route to **QCloud / Cloud Ops** OKTA runbook (§4). Confirm client + correct **OKTA group name** (`<Client> External TIPS User PRD` pattern) and whether to **mirror** an existing user's access |
| External user never got / lost credentials, "needs activation" | Account **pending activation**, not broken | Resend OKTA **activation email**; tell user to check spam (sender is a noreply address) (25-01055400) |
| "Unlock OKTA account" / "Reset Password" / account locked | Standard OKTA lockout | Send **password-reset / unlock** from OKTA admin (25-01059728, 25-01062867) |
| Login fails / "User Unauthorized" after new setup | **Security setup not completed in the application** (OKTA exists but ESUITE user/group not done) | Verify the in-app ESUITE user + group, not just OKTA (26-01070522, 26-01102044) |
| `"doesn't exist in tenant"` error on login | User was **not actually launching a Quorum app** / wrong tenant | Confirm what URL/app they clicked — frequently NOT a Quorum issue (26-01101388) |
| Two logins / "delete second username" / save fails on security group | **Duplicate user record** with same email/similar UserID | Inactivate the duplicate user not tied to OKTA; then security-group save succeeds (26-01065590, 26-01094597) |
| Read-Only user can still **input/edit data** | Wrong **security group / report-type** privileges | Fix ESUITE security group so group can run reports but not update (§6) (25-01012923) |
| `*_READ_ONLY` Oracle ID gets **ORA-02394 / ORA-02395** (IO/session limit) | DB **resource profile limits** too low on the RO account | DBA sets profile limiters to UNLIMITED on the RO account (§7) (25-01024639) |
| RO/Databricks/Snowflake DB account needed after **upgrade** | New DB has no RO account / old one not migrated | Cloud Ops creates/validates RO account on new DB, send credentials (§7) (26-01090123) |
| Microsoft email: "renew SSO certificate to Okta in N days" | SAML signing cert expiring | Coordinate **Entra ID → Okta cert roll** (§8); confirm login after (25-01034697) |
| Users point to **old DB** after a TIPS upgrade | **Secure Gateway** still pointed at pre-upgrade DB | Cloud Ops repoints Secure Gateway to new/current DB (§9) (26-01089055) |
| BA Entity screen: CAN **postal code** format error | Postal-code validation/config defect | Config/script fix by DEV (§10) (25-01039037 / ADO #1751980) |
| Security Group / User screen **slow to load (>10s)** | Known perf bug on the security screen | Confirm patch level (§11, ADO #1703281) |

---

## 2. How TIPS Identity & Security Works

TIPS access is a **three-layer stack** — a login failure can be broken at any one layer, and the #1 triage mistake is fixing the wrong layer:

```
[ LAYER 1 — Identity: OKTA / Microsoft Entra (SSO) ]
   • External users (shippers, producers, agents) authenticate via OKTA.
   • Each client has OKTA groups named like  "<Client> External TIPS User PRD"
     and per-environment "tiles/apps" (e.g. "EQT Midstream Esuite PRD tile").
   • SSO from a client's own Entra/Azure AD federates IN via a SAML signing
     CERTIFICATE that must be renewed before expiry (§8).
   • Cloud Ops/QCloud owns OKTA: create/activate/unlock/reset/deactivate,
     add-to-group, email update, "mirror <existing user>" access.
        │  (authenticated)
        ▼
[ LAYER 2 — Connectivity: Secure Gateway / Citrix / network ]
   • Secure Gateway points the user's session at a specific TIPS DATABASE.
   • After an upgrade the gateway must be repointed to the NEW db (§9).
   • Citrix Storefront / IP allow-listing / ISP issues also live here.
        │  (connected to the right DB)
        ▼
[ LAYER 3 — Application authorization: ESUITE security ]
   • The in-app ESUITE USER record + SECURITY GROUP grant module/screen/report
     privileges (Read-Only group, Super User group, personas/roles, report types,
     plant/company/region-scoped security).
   • "OKTA is fine but they can't do X" almost always means Layer 3 is incomplete.
   • Read-only REPORTING access is ALSO granted as a separate Oracle DB account
     (e.g. MER_READ_ONLY) for Databricks/Snowflake/ad-hoc SQL (§7) — a different
     thing from the in-app Read-Only security group.
```

**Golden rule for "external user can't log in / can't do X":** identify **which layer** before acting.
- Can't authenticate at all → Layer 1 (OKTA: activation/lockout/group/cert).
- Authenticates but lands on wrong/old data, or after an upgrade → Layer 2 (Secure Gateway/DB).
- Logs in fine but missing a screen/report or can edit when they shouldn't → Layer 3 (ESUITE security group / report type).

---

## 3. Decision Tree

```
Security / Business-Associates case
│
├─ Pure provisioning verb in the subject (provision / create / add to group /
│  activate / resend / unlock / reset / deactivate / inactivate / update email / mirror)?
│   └─► ROUTINE USER-ADMIN (§4). Route to QCloud/Cloud Ops OKTA runbook.
│       Confirm: client, exact OKTA group, mirror-target user. Not a defect.
│
├─ "Can't log in" / "User Unauthorized" / locked out?  (§5)
│   ├─ Account pending activation → resend activation (check spam)
│   ├─ Locked / forgot pw → OKTA unlock + password reset
│   ├─ Logs in but "Unauthorized"/missing app → ESUITE security not completed (Layer 3)
│   ├─ "doesn't exist in tenant" → user wasn't launching a Quorum app (verify URL)
│   └─ Duplicate username/email → inactivate the non-OKTA duplicate user
│
├─ Authorization wrong INSIDE the app?  (§6)
│   ├─ Read-Only user can still edit → fix security group (reports-only, no update)
│   ├─ Missing a report / screen / persona → add report type / persona / module to group
│   ├─ Need to limit to a company/facility → plant-company-region scoped security (doc)
│   └─ Security-group SAVE errors → look for DUPLICATE user record first
│
├─ Read-only DATABASE account (Databricks/Snowflake/SQL ID)?  (§7)
│   ├─ ORA-02394/02395 (IO/session limit) → DBA raises profile limiters to UNLIMITED
│   └─ Post-upgrade RO account missing/validate → Cloud Ops create/validate on new DB
│
├─ SSO / SAML CERTIFICATE renewal email?  (§8)  → coordinate Entra→Okta cert roll; verify login
│
├─ After an UPGRADE, users on the OLD database?  (§9)  → repoint Secure Gateway to new DB
│
├─ BA Entity / Business Associate screen?  (§10)
│   ├─ CAN postal-code format error → config/script fix (ADO #1751980)
│   ├─ "How to expire a BA" / validation question → Training (provide steps)
│   └─ BA status list / code-table missing → add/activate code-table records
│
└─ Vague / audit / "review our security groups" / IP warning, no concrete break?  (§13)
    └─ Likely Training / No-Action / Customer-Error / project work — confirm scope before doing anything.
```

---

## 4. OKTA / QCloud External User Lifecycle

**This is the category.** ~421 of ~519 cases are `User Administration Request`, and the large majority are external-user OKTA fulfillment. These are **not defects and not config bugs** — they are runbook tasks owned by **QCloud / Global Cloud Ops**. The L4 job is to **classify, route, and confirm the request is unambiguous**, not to RCA.

### The recurring request sub-types (with representative cases)
| Request type | Subject patterns | Typical resolution text | Examples |
|--------------|------------------|--------------------------|----------|
| **Provision / create** new OKTA account | "Provision OKTA account for Midstream user X", "New CAW User Setup", "Need assistance creating a new user X" | "OKTA account created and added to the corresponding OKTA group" | 25-01056934, 25-01058880, 25-01059535, 26-01105541 |
| **Add to existing OKTA group / tile** | "Add user to our Okta group", "Please add X to our Okta group" | "User added to group `<Client> External TIPS User PRD`" | 25-01057026, 25-01056773, 26-01103702 |
| **Mirror** another user's access | "...Mirroring <existing user>", "Mirroring AMANDA_MEDLAND access" | "created and added... mirroring <user> access" | 25-01060448, 25-01060399, 25-01056890 |
| **Resend activation** | "Resend OKTA activation for X", "TIPS: activation email" | "Account has been activated" / "Activation email sent" | 25-01055400, 25-01040320, 26-01106154 |
| **Unlock / reset password** | "Unlock OKTA user account for X", "Reset Password", "Account Unlock", "Send reset to user X" | "Sent password reset email" / "reset the password" | 25-01059728, 25-01062867, 26-01105753 |
| **Email / domain update** | "Update external user email address", "Revise user email for asset access", "Please update the email for X" | "email successfully updated... user able to access" | 26-01100211, 26-01083650, 25-01059690 |
| **Deactivate / remove** | "Remove OKTA account for X", "Inactivate OKTA account", "Deactivate X's OKTA Account", "Remove ... tile from OKTA user" | "user removed from group/tile" | 25-01053387, 25-01059028, 25-01059339, 26-01105544 |
| **Internal QCloud user** | "New Internal QCloud User - X", "Provision OKTA account for Midstream user" (staff) | "Modified user in app" | 25-01039742, 25-01040407 |

### Fulfillment recipe (what Cloud Ops does — for confirming/routing)
1. Confirm the **client** and the **exact OKTA group/tile** (naming convention: `<Client> External TIPS User PRD`, plus env-specific tiles like `EQT Midstream Esuite PRD`).
2. If "mirror X" — copy the group/tile/role membership of the named existing user.
3. Create the OKTA user (or add existing user to the group) → send **activation email** → user sets password/MFA.
4. For unlock/reset → trigger OKTA password-reset/unlock email.
5. **Two-step gotcha:** OKTA membership alone is **not** enough — the in-app **ESUITE security setup** must also be completed or the user logs in and gets "Unauthorized" (see §5 / 26-01070522).

> **Why so many of these resolutions are blank/terse:** the action happens in OKTA admin / a Cloud Ops Request work item, not in SF. Resolution text like "External Okta user request", "OKTA External User", "created", "completed" is normal for this cluster. Corresponding **Global Cloud Ops Request** work items exist in ADO (§11) — e.g. #1779299 (HVM create external user), #1786775 (Hilcorp new external user, ref 26-01085246), #1782847 (SRI assign OKTA admin), #1821638 (Clearfork app-not-loading, ref 26-01106743).

---

## 5. Login / Activation / Lockout

When a user genuinely **cannot log in**, walk the three layers from §2. The frequent failure modes:

| Symptom | Real root cause | Fix | Case |
|---------|-----------------|-----|------|
| New user set up but **cannot log in** ("see prior case") | **Security setup was not completed in the application** (OKTA done, ESUITE not) | Complete the in-app ESUITE user/group (Layer 3) | 26-01070522 |
| New user gets **"User Unauthorized"** prompt like past new users | ESUITE **security user** record not updated | "Security user updated" | 26-01102044 |
| Login + dashboard access broken | Users in **wrong OKTA group** + SSO not enabled on client side | QCloud assigned users to correct group; client IT enabled SSO per provided doc | 26-01079960 |
| `"<user> doesn't exist in tenant"` on login | User was **NOT launching a Quorum application** (wrong tenant/app) | Educate — not a Quorum break | 26-01101388 |
| Needs **authentication code / MFA** for MyQuorum (new phone) | MFA re-enroll | User reset MFA internally via OKTA on new phone | 26-01080576 |
| **Duplicate username** blocks login / "delete second username" | A 2nd user created with the **same email** conflicts at login | **Inactivate** the user not linked to the OKTA account | 26-01065590 |
| Apps unavailable / EBB / Citrix Storefront issues | Citrix-side or network, not identity | Citrix reset on user machine; QCloud fixed Citrix pwd expiration | 26-01081349, 26-01101947 |
| MyQuorum connection issues | Client **IP blacklisted by their ISP** | Client verifies with ISP (not Quorum) | 25-01007230 |

> **Activation-email note:** external users routinely report "never received credentials" when the account is simply **pending activation**. The activation/reset email lands in spam often — always have them check spam before re-issuing.

---

## 6. ESUITE Security Groups & Report-Type Privileges

In-app authorization (Layer 3). The recurring real-work cluster among the actionable cases.

| Issue | Root cause | Resolution recipe | Case |
|-------|-----------|-------------------|------|
| **Read-Only user can still input data** | Security group not actually restricted | Update the user **group** so it can **run reports but not update** anything | 25-01012923 |
| **Error updating the Read-Only group** (mimic Plant Accountant report types) | **Duplicate user record** with similar UserIDs blocked the save | Remove the duplicate user record → security-group settings save successfully | 26-01094597 |
| Update **security role privilege** (e.g. `PA- ADMIN`) | Group-security setup question | Provide how-to for setting up group security/privileges | 25-01050154 |
| User in **read-only** group needs **add** privileges | Wrong group membership | Move user from `esuite read only group` to `esuite super user group` | 25-01044349 |
| **NN02 / Monthly Confirmations report blank** for a meter/svc-req that has data on screen | **User security modules** missing the report's data scope | Update user **security modules** (interim fix) | 26-01083009 |
| Limit a user to **certain company/facility** | Scoped-security setup | Apply **plant-company-region scoped security** (documentation provided) | 25-01047809 |
| Persona/role missing (e.g. "Pipeline Scheduler" persona) for external user | Persona not assigned | Assign the persona/role to the user | 26-01095187, 26-01097786 |
| Pembina role `PA- Kaybob #3 South` access question | Group-security privileges education | Guided user on group security privileges | 26-01068067 |
| "Review Security Groups for Quorum Support" | Larger security-model cleanup | **Deferred to a bigger project** (not a quick config) | 26-01086102 |

> **Pattern:** almost all of these are **config/education**, fixed by adjusting the **ESUITE security group / report-type / persona / scoped-security**, not code. When a security-group **save errors**, suspect a **duplicate user record** first (26-01094597). For "can run but not edit", the lever is making the group **reports-only**.

> **Base-security provisioning for NEW TIPS customers** is being productized via ADO #1624308 / #1656054 / #1658977 / #1787840 ("Add Base TIPS Security Groups to REL") and client-specific **Script Deployment** WIs like #1607885 (EQC TIPS PRD Security Group Script) — i.e. new clients get a standard set of base groups loaded by script.

---

## 7. Read-Only Oracle DB Accounts (Databricks / Snowflake / Reporting)

Separate from the in-app Read-Only group: clients get a **dedicated read-only Oracle account** (naming pattern `<CLIENT>_READ_ONLY`, e.g. `MER_READ_ONLY`) to run ad-hoc SQL / feed **Databricks / Snowflake / reporting**. Two recurring cases:

| Issue | Root cause | Resolution recipe | Case |
|-------|-----------|-------------------|------|
| `ORA-02395: exceeded call limit on IO usage` and `ORA-02394: exceeded session limit on IO usage` on the RO ID | The Oracle **resource profile** on the RO account caps IO per call/session | **DBA sets the profile limiters to UNLIMITED** on the `<CLIENT>_READ_ONLY` account | 25-01024639 (`MER_READ_ONLY`) |
| Post-upgrade: **validate / create RO DB account** (e.g. for Databricks) on the **new** PRD database | New DB created by the upgrade has no RO account yet | Cloud Ops **creates/validates the RO account** on the new DB and **sends credentials** | 26-01090123 (HVM, Databricks) |
| Export TIPS data to Snowflake / access UTG database | How-to | Provide export-process guidance + UTG DB access | 26-01068154 |

> **UTG** is the reporting/extract database clients query for these exports (26-01068154). The RO account + UTG access is the standard "let us pull our own data" pattern.

---

## 8. SSO / SAML Certificate Renewal

Clients that federate via their own Microsoft Entra ID receive automated **"renew your application certificate" / "certificate ... going to expire in N days"** emails for the **Okta - Quorum Software** SAML app. If not renewed, SSO breaks for everyone at that client.

**Resolution recipe (from 25-01034697, Merit Energy):**
1. In the client's **Azure portal → Single sign-on** page for "Okta - Quorum Software", under **SAML Signing Certificate**, **Create new certificate** (duration up to 3 years).
2. **Make new certificate active** and Save (rolls over the existing cert).
3. **Download** the new cert and **upload it to Okta - Quorum Software** (the Quorum/Cloud Ops side adds the new SSO authentication).
4. **Confirm the customer can log in** before closing — there may be brief SSO downtime during the roll, so schedule it.

> Coordinate the **client side (Entra)** and the **Quorum side (Okta)** — both must hold the new cert. The resolution explicitly: "Added the new SSO authentication on the customer's side and ours and confirmed the customer could login."

---

## 9. Secure Gateway / DB Repointing After Upgrade

After a TIPS database **upgrade**, the **Secure Gateway** (the access layer that connects external users to a specific DB) can still be pointed at the **pre-upgrade** database, so users see stale/old data or can't reach the current environment.

**Resolution recipe (26-01089055, Harvest Midstream):** Cloud Ops **repoints Secure Gateway access to the new/current database**. Pair this with §7 (validate the RO DB account on the new DB) as part of the standard **post-upgrade access checklist**:
1. Repoint **Secure Gateway** to the new DB (26-01089055).
2. **Validate/create the RO DB account** on the new DB; send credentials (26-01090123).
3. Confirm external users land on the new environment.

> Related post-upgrade access work also shows up as Citrix password-expiration fixes (26-01101947) and IP allow-listing (26-01095351 "Whitelist IP Addresses - BHE Eastern Gas" → "Qcloud infra change"). All are **Cloud Ops infra**, not product.

---

## 10. Business Associate (BA) Entity Screen

The small **Business Associates** category (12 cases). Mostly setup/training; one real config defect.

| Issue | Root cause | Resolution recipe | Case / ADO |
|-------|-----------|-------------------|------------|
| BA Screen — **CAN (Canadian) postal-code format erroring** | Postal-code **validation/config** defect for Canadian addresses | **DEV corrected via scripts**; tracked as ADO **#1751980** (SRI Steel Reef, 2024.10, DEV+PRD) | 25-01039037 / #1751980 |
| **"How to expire a BA"** | Training | Provide steps to expire **Meters, Contracts and BAs** | 26-01106806 |
| **Validation for BA Setup** (wants stricter validation) | Enhancement, declined | Confirmed current process; customer **declined an enhancement** | 26-01067183 |
| BA **"Current BA Status" list** missing values | Code-table records inactive/missing | **Activated existing + added new code-table records** | 26-01101067 |
| **Company Address window** — states don't appear | Expected behavior | **Country must be filled first**, then states populate | 25-01020950 |
| BA Entity Screen **Security Objects** | Investigated, nothing to change | **No Action Taken** | 26-01096770 |

> **Address picklists are dependent:** Country → State/Province → Postal. "States missing" is almost always "Country not selected yet" (25-01020950), and CAN postal-code formatting is the one genuine config bug (#1751980).

---

## 11. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF / ref |
|-------|--------------|-----------------|---------|----------|
| **#1751980** | Bug / **Closed** | SRI Steel Reef — 2024.10 TIPS **CAN Postal Code Configuration Error** (DEV & PRD) | §10 BA screen | 25-01039037 |
| **#1675800** | Bug / **Resolved** | ARS — AP Dynamic Export **Postal Code** | §10 (postal-code family) | — |
| **#1703281** | Bug / **Closed** | 2024.10 — TIPS **Security Group/User screen load > 10 seconds** | §6 (perf) | — |
| **#1540593 / #1588800 / #1656804** | Bug+Task / **Closed** | TIPS — **Interactive Reports screen enabled when "allow query" is OFF** (RO/security gap) | §6 | — |
| **#1624308** | Bug / **Active** | TIPS REL Security — **Add Base TIPS Security Groups to REL** for new TIPS customers | §6 (base provisioning) | — |
| **#1656054 / #1658977 / #1787840** | Task / Closed+Proposed | Refinement/Execution/backlog of the **Base TIPS Security Groups** work | §6 | — |
| **#1607885** | Script Deployment / **Closed** | **EQC TIPS PRD Security Group Script** (base groups loaded by script) | §6 | — |
| **#1574819 / #1680649** | Change / **Closed** | PNR / HEP TIPS repos **missing branch security group on Develop** (DevOps repo perms, not app) | infra | — |
| **#1756454** | Request / **Closed** | IPF Interpipeline — **Set up TIPS SSO via OKTA** | §4/§8 | — |
| **#1760974** | Incident Global Cloud Ops / **Closed** | IPF Interpipeline 2025.04 TIPS — **OKTA admins log-in issue** | §5 | — |
| **#1779299** | Request Global Cloud Ops / **Closed** | HVM Harvest — **Create OKTA External User** to TIPS PRD | §4 | — |
| **#1786775** | Request Global Cloud Ops / **Closed** | Hilcorp — **new external OKTA user** (Carlos Huertas) | §4 | 26-01085246 |
| **#1782847** | Request Global Cloud Ops / **Closed** | SRI Steel Reef — **assign SRI OKTA admin** (UAT & PRD) | §4 | — |
| **#1821638** | Request Global Cloud Ops / **Closed** | Clearfork Midstream — **OKTA / TIPS app not loading** | §4/§5 | 26-01106743 |

> **Takeaway:** in this category, ADO items split into (a) **Global Cloud Ops Request/Incident** items mirroring routine OKTA fulfillment (the bulk), and (b) a few genuine product items — the **CAN postal-code** config bug (#1751980), the **security-screen perf** bug (#1703281), the **Interactive-Reports/allow-query** RO gap (#1540593), and the **Base TIPS Security Groups** productization (#1624308 family). There are **no Software-Defect-rooted security cases** in the mined SF set.

---

## 12. Diagnostic SQL

> Column/table names below follow the ESUITE/TIPS security model. Several are **inferred** (no case in this group attached verbatim security-table SQL); **verify against the schema before scripting**, and keep everything read-only — SF/this skill never writes to security tables directly.

### A. Find a user and their group membership (duplicate-user check — 26-01094597 / 26-01065590)
```sql
-- Look for >1 active user record sharing the same email / similar UserID (blocks security-group save & login)
SELECT USER_ID, USER_NM, EMAIL_ADDR, IS_ACTIVE, OKTA_LINKED, UPDT_DT
FROM   <ESUITE_USER table>
WHERE  UPPER(EMAIL_ADDR) = UPPER('<user email>')
ORDER BY IS_ACTIVE DESC, UPDT_DT DESC;
-- Two+ rows for one email = inactivate the one NOT linked to OKTA.
```

### B. Security group → report-type / privilege coverage (Read-Only can still edit — 25-01012923)
```sql
SELECT g.GROUP_ID, g.GROUP_NM, p.PRIVILEGE_CD, p.ALLOW_UPDATE_FL, p.REPORT_TYPE_CD
FROM   <SECURITY_GROUP> g
JOIN   <SECURITY_GROUP_PRIV> p ON p.GROUP_ID = g.GROUP_ID
WHERE  g.GROUP_NM LIKE '%READ%ONLY%';
-- Red flag: ALLOW_UPDATE_FL = 'Y' on a group that should be reports-only.
```

### C. Read-only Oracle account resource profile (ORA-02394/02395 — 25-01024639)
```sql
-- What profile is the RO account on, and what are its IO limits?
SELECT USERNAME, PROFILE FROM DBA_USERS WHERE USERNAME = '<CLIENT>_READ_ONLY';
SELECT RESOURCE_NAME, LIMIT
FROM   DBA_PROFILES
WHERE  PROFILE = (SELECT PROFILE FROM DBA_USERS WHERE USERNAME = '<CLIENT>_READ_ONLY')
  AND  RESOURCE_NAME IN ('LOGICAL_READS_PER_CALL','LOGICAL_READS_PER_SESSION');
-- Fix is a DBA action: set these limiters to UNLIMITED on the RO profile.
```

### D. BA status code-table coverage (BA status list missing values — 26-01101067)
```sql
SELECT CODE_TABLE_ID, CODE_VALUE, CODE_DESC, IS_ACTIVE
FROM   <QCODE_* BA-status code table>
WHERE  CODE_TABLE_ID = '<BA status code table>'
ORDER BY IS_ACTIVE, CODE_VALUE;
-- Missing/inactive rows = add/activate the needed status records.
```

---

## 13. Expected-Behavior FAQ

The Training / Customer-Error / No-Action answers worth recognizing before doing any work:

| Reported as | Reality / answer | Case |
|-------------|------------------|------|
| `"<user> doesn't exist in tenant"` at login | The user **was not launching a Quorum app** — wrong tenant/URL on their side | 26-01101388 |
| "Read-Only user can still input data" | Their security **group** isn't actually restricted — make it reports-only (config, not a bug) | 25-01012923 |
| "Company Address window — no states show" | **Select Country first**; State/Province is dependent and then populates | 25-01020950 |
| "How do I expire a BA?" | Provide steps to expire **Meters → Contracts → BAs** (order matters) | 26-01106806 |
| "We want stricter BA-setup validation" | That's an **enhancement** (often declined); current validation is by design | 26-01067183 |
| "Limit users to a company/facility" | Use **plant-company-region scoped security** (documented setup, not a defect) | 25-01047809 |
| "MyQuorum connection issues" | Could be **client ISP blacklisting** — have them verify with their ISP | 25-01007230 |
| "EQC_ prefix not on user profile" | Self-service: upload the user via the **QCloud template** (doc provided) | 25-01002208 |
| "IP Address Warning — just in case" | Informational; **No action** | 26-01090213 |
| "Review our security groups" | Usually a **project**, not a quick ticket — scope before acting | 26-01086102 |

> **Tell-tale it's user/expected/Cloud-Ops, not a defect:** the verb is provision/unlock/reset/add-to-group; the "error" is a dependent picklist (Country→State) or a wrong-tenant login; the ask is "how do I…"; or it's an ISP/Citrix/IP/network issue on the client side.

---

## 14. Escalation Guidance

```
Security / User-Admin case
│
├─ Routine OKTA/QCloud fulfillment (provision/activate/unlock/reset/remove/email/group/mirror)?
│     → Route to QCLOUD / GLOBAL CLOUD OPS (user-admin runbook). NOT engineering.
│       Confirm client + exact OKTA group + mirror target. (§4)
│
├─ Read-only DB account (ORA limits, post-upgrade RO account, Databricks/Snowflake)?
│     → CLOUD OPS / DBA. Profile limiters, account creation, credentials. (§7)
│
├─ SSO/SAML cert renewal, Secure Gateway repointing, Citrix, IP allow-list?
│     → CLOUD OPS / INFRA. Coordinate client Entra side for certs. (§8, §9)
│
├─ In-app authorization wrong (Read-Only edits, missing report/persona, scoped security)?
│     → CONFIG, handled by L4/Support: adjust ESUITE security group / report type / persona.
│       Check for a DUPLICATE user record if the group SAVE errors. (§6)
│       New-customer base groups → Base TIPS Security Groups work (#1624308 family) / script (#1607885).
│
├─ BA Entity screen — CAN postal-code error or similar validation bug?
│     → ENGINEERING (config/script). Reference ADO #1751980 (Closed). (§10)
│
└─ Security/User screen performance, or a reproducible product bug?
      → ENGINEERING. Security-screen >10s perf is ADO #1703281 (Closed) — confirm patch level first. (§11)
```

**When it's a defect → Engineering:** only the **BA CAN postal-code** config bug (#1751980), the **security-screen perf** bug (#1703281), and the **Interactive-Reports / allow-query** RO gap (#1540593) are true product items in this group. Everything else is Cloud Ops or config.

**When it's config → L4/Cloud Ops:** the 15 actionable cases were **all Application Configuration** resolved by adjusting OKTA groups, ESUITE security groups/report types/personas, DB account profiles, SSO certs, or Secure Gateway pointing — **no code change required**.

---

*Skill created: 2026-06-11*
*Based on: ~519 closed TIPS Security/Business-Associates SF cases (421 User Administration Request, 15 Application Configuration actionable, 0 Software Defect) + Training/Customer-Error sample + ADO work items #1751980, #1703281, #1540593/#1588800/#1656804, #1624308/#1656054/#1658977/#1787840, #1607885, #1756454, #1760974, #1779299, #1786775, #1782847, #1821638, #1675800.*
*Companion: SKILL_TIPS_CAW.md (portal data layer & external login data-sync), SKILL_TIPS_System_Configuration.md (non-security app config). Applicable to all TIPS clients.*
