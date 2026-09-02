# SKILL: QCFS Platform / Security Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** My Quorum Financial Accounting (QCFS) — upstream oil-&-gas accounting suite (myQuorum / On Demand "Upstream")
**Scope:** The platform & security surface of QCFS — **Business Associate (BA) / Vendor master-data maintenance** (BA005 web + classic, QCFS/Core-Financials tab, Tax ID, contacts, addresses, attachments, Global-BU sync), **PUBBA → QLS integration**, **user access / login / Okta / Citrix / QCloud**, **security roles / personas / SOD (Segregation of Duties)**, **QQM reporting** (universe, timeout, folders, report logic), platform **process/batch & patch/hotfix deployment**, and incidental **GL/JE/AP/check-register/bank-recon** config that surfaces as "screen error / can't save / can't post."
**Companion skills:** GL/AP/AR transaction-accounting logic, period close, financial statements → the QCFS accounting skills; this skill is the *platform & master-data + access* layer. When a BA "won't save / won't pay," that is almost always **this** skill (Global-BU unsync or a validation override), not an accounting bug.

> **Evidence base:** 1,302 closed QCFS cases in Case_Category in (eSuite, Security, QQM, All). Root-cause split (top): (blank) 395, Customer Error 260, Customer Cancelled 160, **Software Defect 157**, Training 111, **Application Configuration 101**, Business Change 60, Performance 57, others. This skill mines the **209 actionable** cases (**Software Defect 100 + Application Configuration 100 + ChangeConfig 9**) for fix recipes, plus ~40 Training/Customer-Error cases for the Expected-Behavior FAQ. Category mix of the 209: eSuite 129, Security 52, QQM 27, All 1. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Platform & Concepts](#2-platform--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — BA "Saved Successfully" but not saved / can't pay vendor (Global-BU unsync) (HIGHEST FREQUENCY)](#4-cluster-a--ba-saved-successfully-but-not-saved-global-bu-unsync)
5. [Cluster B — BA Tax-ID effective-date validation error](#5-cluster-b--ba-tax-id-effective-date-validation-error)
6. [Cluster C — Other BA / Vendor maintenance (contacts, addresses, state picklist, attachments, zip)](#6-cluster-c--other-ba--vendor-maintenance)
7. [Cluster D — PUBBA → QLS integration](#7-cluster-d--pubba--qls-integration)
8. [Cluster E — User access / login / password / Okta / Citrix / QCloud](#8-cluster-e--user-access--login--password--okta--citrix--qcloud)
9. [Cluster F — Security roles / personas / SOD / posting access](#9-cluster-f--security-roles--personas--sod--posting-access)
10. [Cluster G — QQM reporting (universe, timeout, folders, report logic)](#10-cluster-g--qqm-reporting)
11. [Cluster H — GL/JE/AP/check-register/bank-recon screen & process errors](#11-cluster-h--gljeapcheck-registerbank-recon-screen--process-errors)
12. [Cluster I — Platform processes & patch/hotfix/upgrade deployment](#12-cluster-i--platform-processes--patchhotfixupgrade-deployment)
13. [Known ADO Items](#13-known-ado-items)
14. [Diagnostic SQL](#14-diagnostic-sql)
15. [Expected-Behavior / User-Education FAQ](#15-expected-behavior--user-education-faq)
16. [Key Code, Screens & Repos](#16-key-code-screens--repos)
17. [Escalation Guidance](#17-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| BA "**Saved Successfully**" message but change disappears on refresh / DB never updates; can't pay the vendor; "Use as Vendor" flag won't stay checked | **Global BU unsynced from BA** — orphaned by using the **NEW / COPY** button to create BAs back-to-back; VENDOR table missing the Global-BU (IDGLOBAL/IDBOWNER) record | §4 — check VENDOR vs Global-BU link; script to backfill+resync; confirm DoNew hotfix deployed |
| "**The Tax Type (FED) and Tax ID (…) must have an Effective Date To value**" when updating a BA address (and you never touched Tax ID) | Tax-ID effective-date overlap validation firing on converted/bad Tax-ID data; override sometimes wiped by a later patch | §5 — fix the 8-ish bad Tax-ID rows, or (re)apply the `QESUITEValidationBAEntity0086` object-usage override; confirm Patch #3 / CORE 2024.04 build |
| BA state/province dropdown "**No Data Found**"; must press F5 to populate state | Zip-code mask removal broke the state picklist load | §6 — refresh (F5) workaround; permanent fix in **Patch #14** |
| Vendor "**Use as Vendor**" re-check throws `Violation of UNIQUE KEY constraint 'IX_Vendor_Key'` | BA-save duplicate-key defect (uncheck→save→recheck→save) | §6 / §13 — fixed in GA; #1549989 |
| **PUBBA** process fails / won't run / BA not sent to **QLS** | Lock-parameter (30022) bad setup, `PUBBA_LK` lock row, missing `Quorum.ESuite.Integration.QLS` assembly, missing country/state codes (ZZ), or PUBBA not configured/visible in Web | §7 — clear lock, fix process-param setup, run PUBBA in Web |
| User "**Password Expired**" repeatedly / every Monday / new user can't reset | Okta/AD account state; new-user password-reset script cadence | §8 — reset Okta account / remove Quorum AD from profile; QCloud RCA = reset script now runs every 15 min |
| New user sees **no apps in Citrix Storefront** / can't launch Citrix / stuck at loading | Citrix/QCloud provisioning, security group, or local client | §8 — verify SEC group + Storefront entitlement; Citrix reset; escalate to QCloud |
| User has wrong access — too much or too little (persona, posting, JE-type edit, AP reverse, run reports) | **Security group / Upstream template role** mismatch vs the client's security matrix | §9 — align SEC group membership to the matrix; persona = web security group |
| **SOD violation**: same user could Draft + Approve + Post one voucher despite **SM093** set to block it | SM093 sole-approver defect | §9 — fixed in **Hotfix 11 / 2023.04** (#1771241, tracked by 26-01064968) |
| QQM session **times out** too fast / loses work | Server-side QQM session timeout setting | §10 — QQM team adjusts timeout (e.g. to 30 min) |
| QQM report errors on refresh / missing rows / "Web Intelligence Applet cannot be loaded" | Universe connection, report filter logic, or client set to Applet not HTML | §10 — update universe connection / fix filter; set Preferences → Web Intelligence → **HTML** |
| Error creating GL account / running QCFS Import Cycle / check-register update | Missing **SEC group** or `SARCH_CNFG_INT_MODULE` module entitlement | §11 — grant SEC group / fix module config |
| JEs stuck in "post pending" for days after upgrade | Process scheduler: **server name removed** + scheduled task disabled | §11 — re-point & enable the scheduled task |

---

## 2. Platform & Concepts

```
[BA / Vendor master (BA005 web + classic)] ──PUBBA──► [QLS (Land system)]
        │  (VENDOR, Global BU / IDGLOBAL, Contacts, Bank, Tax ID, QCFS/Core-Financials tab)
        ▼
[QCFS accounting: GL / AP / AR / Check Register / Bank Recon / JE / Vouchers]
        │
        ├──► [QQM reporting universe]  (Web Intelligence reports, AP/AR/GL/Cash universes)
        └──► [Security layer]  Okta (login) → Citrix/QCloud (app delivery) → SEC groups / personas / SM093 SOD
```

### Key terms (Quorum / QCFS vocabulary)
- **BA (Business Associate)** = the master record for a vendor/customer/owner. Screen **BA005** in both classic and the newer **BA Web** module. Tabs: General, Address, Contacts, Bank, **QCFS / Core Financials** (vendor pay terms, 1099, tax), Usage. A BA can be flagged **Use as Vendor / Use as Customer**.
- **Global BU** (a.k.a. Global Business Unit; row in the **VENDOR** table keyed by **IDGLOBAL / IDBOWNER**) = the cross-BU master that each per-BU BA record must stay **synced** to. If a BA loses its Global-BU link it becomes **orphaned** and silently un-saveable (§4).
- **PUBBA** = the batch process (run from **QP063** / Process Queue Explorer, or auto after a BA update) that **publishes/transfers BA data to QLS** (Quorum Land System). Uses assembly `Quorum.ESuite.Integration.QLS`; can be locked by a `PUBBA_LK` / process lock-parameter.
- **QLS** = Quorum Land System — the downstream land/lease app that consumes BA data via PUBBA. Heavily used during **acquisition conversions** (sending many new BAs at once).
- **QCFS** = the upstream Financial Accounting product code (My Quorum Financial Accounting). The **QCFS tab** on BA005 holds the vendor/financial attributes.
- **Okta** = the cloud IdP for login. **Citrix Storefront / QCloud** = how the classic Quorum apps are delivered to users. "Password expired," "no apps in Storefront," "stuck at loading" are access-layer issues, not QCFS bugs.
- **SEC group / persona / Upstream template role** = the security model. **Personas** (e.g. *AP Accountant*, *DO Analyst*, *Land Analyst*) in BA Web map to **security groups**. Most "wrong access" cases are SEC-group membership vs the client's **security matrix**.
- **SM093** = the Segregation-of-Duties (SOD) config screen controlling whether one user may **Draft / Approve / Post** the same voucher. **WF005** = workflow inbox; **AP055** = AP approval-level config.
- **QQM (Quorum Query Manager)** = SAP BusinessObjects Web-Intelligence reporting on accounting **universes** (AP/AR/GL/Cash). Common asks: session **timeout**, save to public folders, universe field exposure, report filter logic.
- **Object usage / `QARCH_CTRL_OBJECT_USE`** = metadata that enables/disables a validation rule per client layer. The Tax-ID fix (§5) is a *disabled* object-usage override of `QESUITEValidationBAEntity0086`.
- **Patch / Hotfix / build** = e.g. `2022.04`, `2023.03`, `2023.04`, `2024.04`, `2024.10`. Many cases are simply scheduled deployments; a patch can **wipe a client-layer override** (the recurring §5 trap).

---

## 3. Decision Tree

```
QCFS Platform / Security case
│
├─ A BA / Vendor won't save or won't pay?
│   ├─ "Saved Successfully" but DB unchanged / "Use as Vendor" won't stick / can't pay vendor   → §4  (Global-BU UNSYNC — orphaned by NEW/COPY button; backfill VENDOR + resync; confirm DoNew hotfix)
│   ├─ "Tax Type & Tax ID must have an Effective Date To value" (didn't touch Tax ID)            → §5  (Tax-ID eff-date validation; fix bad data OR re-apply object-usage override; patch can wipe it)
│   ├─ State/Province dropdown "No Data Found" / need F5                                          → §6  (zip-mask side-effect; F5 workaround; Patch #14)
│   ├─ UNIQUE KEY 'IX_Vendor_Key' on re-checking Use as Vendor                                    → §6 / #1549989
│   └─ Can't inactivate / can't add contact / attachments missing                                → §6
│
├─ BA not reaching QLS / PUBBA failing?                                                            → §7  (lock-param 30022, PUBBA_LK, missing QLS assembly, ZZ codes, PUBBA not in Web)
│
├─ User can't log in / no apps / password expired / Citrix?                                        → §8  (Okta reset, AD-on-profile, SEC group + Storefront, Citrix reset → QCloud)
│
├─ User has wrong access (too much / too little; persona/posting/JE-type/AP-reverse)?              → §9  (align SEC group to matrix); SM093 SOD bug → Hotfix 11 / 2023.04
│
├─ QQM?  timeout → §10 (server setting);  refresh error / missing rows → §10 (universe conn / filter);  applet → set HTML
│
├─ GL/JE/account/check-register/import-cycle screen or process error?                              → §11 (SEC group / module entitlement; scheduler server-name+enable)
│
└─ "Deploy a patch / hotfix / upgrade", scheduled, or post-patch regression?                       → §12 (deployment; watch for wiped client overrides → §5)
```

---

## 4. Cluster A — BA "Saved Successfully" but not saved (Global-BU unsync)

**The single largest and most business-critical actionable signature in QCFS.** A user edits a BA (most often the **QCFS / Core Financials tab** — vendor pay terms, "Use as Vendor"), gets **"Saved Successfully,"** but on refresh the change is gone and the **database was never updated**, so they **cannot pay the vendor**.

**Root cause (consistent across cases):** the **Global BU became unsynced / orphaned from the BA**, because the user created BAs **back-to-back using the NEW or COPY button** (creating one BA as a vendor directly after another). The `DoNew` path failed to reset the QCFS-side Vendor/Customer/Bank objects to NULL, so the new BA carried stale links and the **VENDOR table ended up missing the Global-BU record** (IDGLOBAL / IDBOWNER) — leaving the BA orphaned and silently un-saveable.

**Cases (all the same family):**
| Case | Client | Note |
|---|---|---|
| 25-01010166 | — | "Use as Vendor" prompts Saved Successfully then unchecks; VENDOR missing BA↔Global-BU setup. Workaround = insert missing record; long-term = DoNew logic merged to 2022.04/2023.04/2024.04/2024.10/2025.04 |
| 25-01013311 | ARS | Global BUs unsynced after creating new BA in web; scripts to create new Global BU + reassociate orphans |
| 25-01008651 | GEC | Vendor Pay Terms "Saved Successfully" but not kept (PRD only); **COPY** button orphaned BAs; script to create+resync Global BUs |
| 25-01016041 | — | BA 133325 pay terms not saving → can't cut check; script created missing IDBOWNER 11 (Global BU) row and linked it |
| 25-01032725 | — | VENDOR table missing Global-BU records for several BAs; script to repair |
| 25-01009536 | MST/TXO | Two new vendors' **IDGLOBAL pointed to the same record** after using NEW; esuite code fix delivered in Patch #02 |
| 24-00989785 | APH | Root long-term-fix case: BA Web NEW button **deletes the Global-BU record, orphaning BAs**; hotfix changed `DoNew` to NULL the Vendor/Customer/Bank objects |
| 24-00988309 | APH | "User can no longer edit BAs" — same family (triggered 24-00989785) |
| 25-01061877 | — | "Patch 3 FAILED: BUSINESS ASSOCIATE - UPDATES" — deployment of the fix |

**Fix recipe:**
1. Reproduce: edit the BA's **QCFS/Core-Financials** tab (or toggle **Use as Vendor**), Save → "Saved Successfully" → refresh → change gone, DB unchanged.
2. Confirm orphan: check the **VENDOR** table for the BA — is the **Global-BU / IDGLOBAL (IDBOWNER) row missing** or pointing to the wrong vendor? (see §14 query A).
3. **Immediate unblock (data script, Cloud Ops):** create the missing Global-BU (IDBOWNER) record in VENDOR and **re-link** the orphaned per-BU BA rows to it. Always verify-SELECT first, wrap in a transaction.
4. **Permanent fix:** confirm the client's build includes the **`DoNew` logic change** (resets Vendor/Customer/Bank DOs to NULL to match the new `BusinessAssociateDO`). Merged to **2022.04, 2023.04, 2024.04, 2024.10, develop/2025.04**. Until the client takes the hotfix, the script is the workaround.
5. **Tell the user the trigger:** avoid the **NEW/COPY button to create vendors back-to-back**; create, save, fully exit, then start the next.

> **Tell-tale:** "Saved Successfully" + no DB change + "Use as Vendor"/pay-terms involved + they were bulk-creating vendors = Global-BU unsync, every time. ADO: #1719506 / #1719963 (APH — "Not able to save BA when adding Use as Vendors Flag," both **Closed**).

---

## 5. Cluster B — BA Tax-ID effective-date validation error

A distinct, recurring blocker: updating **any** field on a BA (often the **address**) throws

```
The Tax Type (FED) and Tax ID (9999999999) must have an Effective Date To value.
```

even though the user **never edited the Tax ID**, and the effective-date field isn't even editable on the screen.

**Root cause:** the BA Tax-ID **effective-date overlap validation** (`QESUITEValidationBAEntity0086_BAValidateTaxIdEffDateNoOverlaps`) fires on **converted / bad Tax-ID data** (Tax-ID rows with a null "Effective Date To"). Two resolution paths appear:
- **Fix the data** when only a handful of BAs are affected (25-01017924: "8 BAs had incorrect Tax ID data; once corrected the error is gone").
- **Disable the validation via an object-usage override** when it's systemic (25-01014124: *"disabled object usage QESUITEValidationBAEntity0086_ValidateBATaxIdEffDateNoOverlaps"* in the client layer).

**The recurring trap:** the object-usage override lives in the **client metadata layer**, and a **later patch wipes it**, so the error **comes back** (25-01018302 BTY: "Chase fixed it temporarily but it returned" → override was removed when PRD A1 was patched; not yet in CORE 2024.04). The long-term fix (25-01027299) put the override into **CORE 2024.04** and shipped it as **Patch #3** so future patches don't remove it.

**Cases:** 25-01014124 (override applied), 25-01017924 (data fix, 8 BAs), 25-01018302 / 25-01027299 (BTY — override wiped by patch → permanent CORE fix), 25-01008651-adjacent upgrades. ADO: **#1693784** ("MEW 2024.04 Upgrade — BA Update fails on Tax ID NULL Effective To", Bug/Closed), **#1736723** ("BTY — 25-01018302 — Error updating BA address — prompting for effective date", Bug/Closed).

**Fix recipe:**
1. Confirm the user did **not** edit Tax ID. Query the BA's Tax-ID rows for a **null Effective-Date-To** (see §14 query B).
2. **Few BAs** → correct the Tax-ID data (set/clear the effective dates) — preferred.
3. **Systemic** → (re)apply the **disabled object-usage** of `QESUITEValidationBAEntity0086` in the client layer.
4. **Confirm the override is in the client's build (CORE 2024.04 / Patch #3)** so the next patch doesn't wipe it — this is the #1 cause of the issue "coming back." If you only apply a loose script, **open a tracking case for the metadata/patch fix**.

---

## 6. Cluster C — Other BA / Vendor maintenance

Smaller BA-screen issues; mostly **config / data / known web-screen defects**.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| State/Province dropdown **"No Data Found"**; must press **F5** to populate | Removal of the **Web Zip-code mask** broke the state-picklist load | Workaround: refresh (F5). Permanent code fix in **Patch #14** | 25-01014547, 25-01015257 |
| Re-checking **"Use as Vendor"** → `Violation of UNIQUE KEY constraint 'IX_Vendor_Key'` (uncheck→save→recheck→save) | BA-save duplicate-key web defect | Fixed in latest GA | 23-00895233 / **#1549989** |
| Bank tab "**Account Number/Name required**" unless you open Bank tab & Update *first* | BA-load order web defect | Bug fixed in **2021.10 October Hotfix** | 23-00888536 |
| BA address update very slow → **Execution Timeout Expired** / POSTWKFL failing | Idle blocking session + server memory | Drop the idle blocker; QCloud +20% memory on the Citrix server | 24-00989239 |
| **Zip code shows dashes** / doesn't match configured format | Dashes stored on backend from conversion upload | Remove dashes from zip; the screen logic inserts formatting (standard eSuite practice) | 26-01082054 |
| Can't update Contact Type / add Email; "Additional BAs" record won't add; contacts not converted | Contact-tab data / web screen | Data/config per case | 25-01029190, 22-00830412, 25-01008226 |
| Attachments not visible between new module and BA005 / older attachments missing / can't attach in web | Document-store / fileshare config | Config; see also §11 "Endpoints Cache Denied" | 25-01049324, 26-01065278, 25-01050281 |
| Inactive checkbox grayed out / can't inactivate BA | Open items (e.g. JIB) or duplicate Contact-Id block inactivation | Close open item / remove duplicate non-primary Contact-Id (see §15) | 25-01049517, 25-01007605 |

**Fix recipe:** for "No Data Found" state list, F5 unblocks immediately; confirm the build has the **Patch #14** state-picklist fix. For the UNIQUE_KEY / Bank-tab-first / load-order quirks, they are **known web defects fixed in specific hotfixes** — check the client's build before scripting. For attachment visibility, treat as fileshare/document-store config (§11).

---

## 7. Cluster D — PUBBA → QLS integration

PUBBA publishes BA data to **QLS**; spikes during **acquisition conversions** (sending hundreds of BAs at once). Failures cluster on **process locks, bad process-parameter setup, a missing integration assembly, and reference-data gaps.**

| Symptom | Root cause | Fix | Case / ADO |
|---|---|---|---|
| PUBBA fails: *"parameter 30022 has been defined as a lock parameter… invalid setup… Failed to lock. [Process ID = PUBBA]"* | **Process-parameter setup** wrongly flags 30022 as a lock parameter | Correct the PUBBA process-parameter setup; reruns clean | 25-01054657 |
| PUBBA won't run / `PUBBA_LK` blocks Full Synch; processes stuck in **WTL / QUE** | Stale **PUBBA lock** row | Clear the lock / cancel the stuck QUE record | #1655202, #1781706, #1777968 |
| `Could not load file or assembly 'Quorum.ESuite.Integration.QLS'` when running PUBBA in QP063 | Missing/undeployed **QLS integration assembly** in that environment | Deploy/configure the QLS integration component | 26-01071350 |
| "Batch process to transfer BA to QLS has failed" on every BA save | Missing **country/state codes** (e.g. **ZZ**) in country/state tables | Add the missing codes; **run PUBBA in Web** (succeeded) | 23-00908533 |
| PUBBA BA sync fails with **multiple new converted BAs sharing the same routing number** | Duplicate routing # among converted BAs | Defect fixed | #1777307 / #1777518 |
| PUBBA "Process Not Running" / "not scheduled" / "not running in UAT" | Process not scheduled or not configured for the environment | Schedule / configure PUBBA per environment | 25-01053420, 25-01017678, 25-01044117, #1781736, #1779057 (PUBBA not visible in Web) |
| PUBBA fails when an **internal BA** record is updated | Internal-BA handling defect | Fixed | #1769479 |

**Fix recipe:**
1. Get the **ProcessQueueID** and the exact PUBBA error from the batch message log.
2. **Lock / param errors** (30022, `PUBBA_LK`, stuck WTL/QUE) → clear the lock / cancel the QUE record, correct the process-parameter setup, rerun.
3. **Assembly-load error** → the `Quorum.ESuite.Integration.QLS` component isn't deployed in that env → Cloud Ops deploy/config.
4. **"transfer to QLS failed" on save** → check **country/state code tables** for missing codes (ZZ) and **run PUBBA from Web**.
5. For conversion pushes, watch for **duplicate routing numbers** across the new BAs (#1777307).

---

## 8. Cluster E — User access / login / password / Okta / Citrix / QCloud

The access layer (Okta login → Citrix/QCloud app delivery → SEC entitlement). **Almost never a QCFS code issue** — these route to identity/QCloud config.

| Symptom | Root cause | Fix | Case |
|---|---|---|---|
| "**Password Expired**" repeatedly / can't authenticate | Okta/AD account state | **Reset the Okta account**; or **remove Quorum AD from the user profile** | 24-00990456, 23-00925559 |
| New user has to **reset password every Monday/week** (recurring) — RCA | The QCloud new-user password-prevention **script wasn't running often enough** | QCloud set the reset-prevention script to run **every 15 minutes**; full RCA on ticket | 24-00942222 |
| Resetting password in Okta **created a duplicate user id** (e.g. NAME2) | Username collision in the directory | QCloud must modify/clean the duplicate username to preserve security integrity (explain to client) | 25-01008503 |
| New user sees **no applications in Citrix Storefront** (PROD/UAT) | Missing Storefront entitlement / SEC group provisioning | Verify SEC group + Storefront entitlement; reprovision via QCloud | 24-00983942, 25-01043865 |
| Can't launch Citrix / unresponsive / blue screen / stuck loading | Local Citrix client or session config | Update Citrix client + Citrix reset; if local, reimage the machine | 25-01045548, 25-01010392, 25-01033084 |
| User "won't stay on OPEN ID" / Authentication Mode won't save Open ID type | Auth-mode save defect | Hotfix (2020.03 July 2022) | 24-00971644, 22-00516739 |
| Insecure RDP / Windows service perms on Quorum servers | Server hardening request | Cloud Ops remediation | 25-01006378, 23-00897579 |
| Enable MFA / Secure Gateway / Data Gateway for QCloud | Access provisioning | QCloud config | 24-00946515, 24-00950450, 25-01009956 |

**Fix recipe:** triage **which layer** — Okta (login/password), Citrix/QCloud (app delivery), or QCFS SEC group (entitlement). Password loops → reset Okta / remove AD-from-profile; recurring new-user loops are the **15-min script** RCA. "No apps in Storefront" = entitlement/provisioning, route to QCloud. Unresponsive Citrix is usually **local** (reset client / reimage). These are **operational**, not Software Defects.

---

## 9. Cluster F — Security roles / personas / SOD / posting access

"User has the wrong access" (too much or too little). The fix is almost always **align SEC-group / Upstream-template-role membership to the client's security matrix** — *config*, not code. One genuine SOD defect.

| Symptom | Root cause | Fix | Case |
|---|---|---|---|
| User missing a **persona** in BA Web (only "DO Analyst" shows, no "AP Accountant") | Missing web **security group** behind that persona | Add the required SEC group → persona appears | 25-01049522 |
| Users need access to **FA005 / FA010 / FA020 / AP055 / Land Maintenance / run reports** | SEC-group membership gap | Grant the matching SEC groups | 26-01082690, 26-01082693, 26-01096508, 25-01032714, 25-01011752 |
| Drafts only visible in **WF005** (can't see other statuses) | Not all workflow groups added to the user | Add **all groups in the workflow** to the user | 23-00893694 |
| User can run reports / create GL account / run import cycle only after SEC change | Missing SEC group / module entitlement | Grant SEC group | 25-01005932, 25-01030918 |
| Wrong people **got** (or didn't get) a role vs the matrix (Bank Recon Draft) | Template roles out of sync with the matrix | **Update the Upstream template security roles** to match the matrix | 25-01006314, 25-01006673 |
| User shouldn't be able to **change JE Code Type** | Over-broad role | Tighten the Upstream template security roles | 25-01006673 |
| **SM093 SOD VIOLATION** — same user could **Draft + Approve + Post** one voucher despite SM093 blocking it (audit risk) | SM093 logic applied the block **only to the sole approver** when the checkbox was unchecked | **Bug fixed in Hotfix 11 / 2023.04**; code change so Draft/Approve/Post isn't exclusive to the sole approver | 25-01060035 / **#1771241** (tracked by 26-01064968); related #203203, #1749902 |
| "Metadata Error When Updating Security" | Security-metadata save | Config/metadata | 25-01028350 |

**Fix recipe:** get the **client's security matrix** and the user(s). Map the requested capability to a **SEC group / Upstream template role**, then add/remove membership and have the user re-test. Personas in BA Web are just security groups. The **only Software Defect** here is **SM093 SOD** (one user could draft+approve+post) — confirm **Hotfix 11 on 2023.04** (or later) is deployed; otherwise it's a config alignment.

---

## 10. Cluster G — QQM reporting

QQM = SAP BusinessObjects Web-Intelligence reporting on accounting universes. Mostly **config / report-logic / session settings.**

| Symptom | Root cause | Fix | Case |
|---|---|---|---|
| Session **times out** too fast (10–15 min) / loses work | Server-side QQM session-timeout setting | QQM team **extends the timeout** (e.g. to 30 min); a hard max applies | 24-00981563, 24-00947325, 25-01059662, 23-00908098 |
| **"Web Intelligence Applet cannot be loaded… install a Java virtual machine"** | Client set to **Applet** mode (needs JVM) | Preferences → Web Intelligence → set **HTML** (View & Modify) | 25-01052689 |
| Report **errors on refresh** / "Refreshing Data" error (e.g. REV 28C) | **Universe connection** stale for some objects (e.g. Revenue) | Update the universe connection | 24-00985666 |
| Report **missing rows** depending on date range (Cash Sheet omits a month) | Report **filter logic** bug | Modify the report filtering logic | 24-00979149 |
| **Extreme latency** / report returns too many rows | Bad **joins** in the report query | Correct the joins / filters in the report | 25-01017150 |
| Need a **field/folder/universe** change (expose Account attributes, add GL095/GL096 fields, default row limit, code-block comment) | Universe enhancement request | Universe change by QQM team | 24-00951120, 25-01017483, 24-00971308, 25-01017116 |
| Can't **save to public folder** / move favorites / save logo / promote UAT→PRD | QQM folder permissions / promotion is back-end only | Grant folder rights; promotion done by QQM team via internal request (not front-end) | 23-00918369, 23-00924803, 23-00898013, 26-01103387 |
| QQM **not responding / down / not on dashboard / login prompt / missing folders** | Environment/access (often UAT or post-refresh) | Restart/repoint QQM; verify entitlement | 23-00924230, 26-01097187, 24-00984160 |

**Fix recipe:** classify as **session** (timeout/applet — client-side or a server setting), **report content** (filter/join/universe-connection — fix the report), or **access/folder** (permissions / back-end promotion). Timeout extensions and HTML-vs-Applet are the two highest-frequency, instantly-resolvable ones. "Report wrong/missing rows" is usually the **report's own filter/join**, not a QCFS data bug — verify the SQL behind the report first.

---

## 11. Cluster H — GL/JE/AP/check-register/bank-recon screen & process errors

Incidental QCFS-accounting touches that surface as platform "screen error / can't run / stuck" — overwhelmingly **security/module entitlement or scheduler config**, not accounting-engine bugs.

| Symptom | Root cause | Fix | Case |
|---|---|---|---|
| Error creating a **GL account** (`ValidateAccount.Validate` exception) | Missing SEC entitlement to set up accounts (GL013) | Apply security; user can then create in **GL013** | 25-01005932 |
| Error running **QCFS Import Cycle** (create accounting entries) | SEC group membership gap | Update the user's SEC group membership | 25-01030918 |
| Error on **Check Register Update / Bank Recon** (QP0063) | Wrong/missing modules in `SARCH_CNFG_INT_MODULE` | Update modules to match the client's expected set | 25-01014820 |
| **JEs stuck "post pending"** for a week after upgrade | Process scheduler had the **server name removed** and the **scheduled task disabled** | Re-point the server name and **enable** the scheduled task | 25-01003758 |
| Users **cannot create JEs** | SEC group | Grant SEC group | 25-01006313 |
| **Escheat (QP043)** errors "no records inserted" for one state | State-specific data/variable setup | Per-state config (resolution unclear from mined case 24-00990180) | 24-00990180 |
| **FA→GL imbalance** / GL096 error | Affected batches / one-off | Data script to fix the affected batches | 22-00639552, 22-00646341 |
| Intermittent **"Endpoints Cache Denied"** opening screens (fileshare/attachments) | Fileshare/endpoint cache | Short-term fix applied; long-term via hotfix at mock cutover | 25-01044175 |
| Wrong/missing **attachments** on accrual-reversal / deposit batches | Attachment-association defect | Hotfix | 22-00669770, 22-00512646 |

**Fix recipe:** for "can't create/run X" the first check is **SEC group / module entitlement** (GL013 rights, `SARCH_CNFG_INT_MODULE`), then **process scheduler** (server name present + task enabled) for "stuck/not processing." Reserve "accounting bug" for provable miscalculation — most of these are platform config.

---

## 12. Cluster I — Platform processes & patch/hotfix/upgrade deployment

| Item | Nature | Notes | Case |
|---|---|---|---|
| Scheduled patch/hotfix deployments | Deployment (ChangeConfig / Software) | e.g. 2023.03 Patch 10/11, 2023.04 Patch 8, Permian Patches 8&9, APH 2022.04 hotfixes, ARS Patch #8 | 26-01064968, 25-01063166, 25-01051873, 25-01017770, 25-01002912, 25-01032812 |
| **Post-patch regression: a client-layer override is wiped** | The §5 trap | After any patch to a client env, re-verify the Tax-ID object-usage override (and any client metadata override) is still present | 25-01018302, 25-01027299 |
| QARCHIVE / QRPTLAUNCH / SFTP / "UAT processes not running" | Platform process errors | Often environment/scheduler/refresh-related; check scheduler & after-refresh config | 25-01020484, 23-00902746, 23-00920803, 26-01101040 |
| UAT flashback / restore-point / "UAT down" / temp DB out of disk | Environment ops | Cloud Ops | 23-00930766, 25-01046989, 24-00974779 |
| .NET Framework / IE11 / Adobe RdrCEF on Citrix | Client-runtime | Update runtime on the Citrix image | 24-00963790, 23-00902962, 24-00956714 |

**Fix recipe:** treat deployments as scheduled Cloud Ops work. **The recurring risk** is regression: a patch to a client environment can **remove a client-layer metadata override** (Tax-ID validation, §5) and re-open a "fixed" case — always re-verify overrides post-patch and prefer pushing the override into the CORE build.

---

## 13. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1719506** | Bug / **Closed** | APH — Not able to save BA when adding Use-as-Vendor flag (script review) | §4 | 24-00988309/89785 family |
| **#1719963** | Bug / **Closed** | APH — Not able to save BA (Use-as-Vendor) when bad data present | §4 | — |
| **#1549989** | Bug / **Closed** | eSuite Web — BA screen SQL error while saving (UNIQUE KEY) | §6 | 23-00895233 |
| **#1693784** | Bug / **Closed** | MEW 2024.04 Upgrade — BA Update fails on **Tax ID NULL Effective To** | §5 | 24-00984139 |
| **#1736723** | Bug / **Closed** | BTY — 25-01018302 — BA address update prompting for Tax-ID effective date | §5 | 25-01018302 |
| **#1771241** | Bug / **Closed** | CEN — 25-01060035 — **SM093 Draft/Approve/Post** long-term solution | §9 | 25-01060035 |
| **#1749902** | Requirement / **Proposed** | UPS CORE_REL — Update Roles to Draft on SM093 | §9 | — |
| **#203203** | Bug / **Closed** | EXTIMPBAT requires SM093 Voucher Workflow Sec Grp (QCFS-Voucher Draft) | §9 | — |
| **#1655202** | Bug / **Closed** | UPS — **PUBBA_LK blocks PUBBA** from running Full Synch | §7 | — |
| **#1765992** | Bug / **Closed** | SEP — PUBBA batch errors on **invalid parameter setup** | §7 | 25-01054657 family |
| **#1769479** | Bug / **Closed** | SEP — PUBBA fails when **internal BA** record is updated | §7 | — |
| **#1777307 / #1777518** | Bug / **Closed** | PUBBA BA sync to QLS fails — **multiple new BAs share routing number** | §7 | — |
| **#1781706** | Bug / **Closed** | HEC — QLS — **PUBBA process lock**, stuck in WTL/QUE | §7 | — |
| **#1777968** | Script Deployment / **Closed** | HEC_QLS_UAT — script to cancel QUE record from PUBBA | §7 | — |
| **#1779057** | Requirement / **Closed** | PUBBA (from ESUITE) **not visible in Web** | §7 | — |
| **#1781736** | Bug / **Closed** | 26-01079742 — Configure PUBBA integration in DEVA1/UATA1/PRDA1 | §7 | 26-01079742 |
| **#1744596** | Requirement / **Resolved** | PRM — Sysgen for Positive Pay + Metadata for PUBBA | §7/§11 | — |

> Several actionable cases were dispositioned **operationally** with no single product WI: Global-BU resync scripts (25-01010166, 25-01013311, 25-01016041, 25-01032725); Tax-ID object-usage override + CORE Patch #3 (25-01014124, 25-01027299); state-picklist Patch #14 (25-01015257); MST/TXO IDGLOBAL Patch #02 (25-01009536); SM093 Hotfix 11 on 2023.04 (26-01064968). Confirm exact build/patch in the Upstream release notes when stating fix availability.

---

## 14. Diagnostic SQL

> **Caveat:** QCFS runs on SQL Server (`Quorum.QCFS.*` namespaces) with eSuite metadata in `QARCH_*` tables; table/column names below are from case repro text and code search — **verify against the client DB before scripting**, and always run a verify-SELECT before any INSERT/UPDATE/DELETE, wrapped in a transaction.

```sql
-- A. BA orphaned from its Global BU (the §4 "Saved Successfully but not saved" signature)
--    Look for a per-BU BA whose Global-BU (IDGLOBAL / IDBOWNER) row is missing in VENDOR.
SELECT v.IDVENDOR, v.IDBOWNER, v.IDGLOBAL, v.BANO, v.BASUF, v.NMVENDOR, v.YNVENDOR /* Use-as-Vendor */
FROM   VENDOR v
WHERE  v.BANO = '<BA_NO>'
ORDER BY v.IDBOWNER;
-- Red flags: no IDBOWNER row for the Global BU; two BAs sharing one IDGLOBAL (25-01009536); YNVENDOR set but no Global row.

-- B. BA Tax-ID rows with a null Effective-Date-To (the §5 validation trigger)
SELECT BA_NO, BA_SUF, TAX_TYPE, TAX_ID, EFF_DATE_FROM, EFF_DATE_TO
FROM   <BA Tax-ID table>     -- per-BA tax id / effective-date table
WHERE  BA_NO = '<BA_NO>' AND EFF_DATE_TO IS NULL;

-- C. Is the Tax-ID validation object-usage override present? (was it wiped by a patch?)
SELECT * FROM QARCH_CTRL_OBJECT_USE
WHERE  OBJECT_NAME LIKE '%QESUITEValidationBAEntity0086%';   -- expect a DISABLED usage in the client layer

-- D. Duplicate Contact-Id blocking BA inactivation (§6 / §15: 26-01066538)
SELECT BANO, BASUF, CONTACTID, CONTACTTYPECODE, COUNT(*) ct
FROM   BACONTACTADDRESS
WHERE  BANO = '<BA_NO>'
GROUP BY BANO, BASUF, CONTACTID, CONTACTTYPECODE
HAVING COUNT(*) > 1;

-- E. PUBBA stuck/locked queue records (§7 — WTL/QUE, PUBBA_LK)
SELECT PROCESS_QUEUE_ID, PROCESS_ID, STATUS, CREATE_DT
FROM   <process queue table>
WHERE  PROCESS_ID = 'PUBBA' AND STATUS IN ('WTL','QUE','ERR')
ORDER BY CREATE_DT DESC;

-- F. User has multiple SEC_USER_IDs (voucher inbox / access oddities — 25-01029951)
SELECT SEC_USER_ID, SEC_USER_NM, ACTIVE_FLG
FROM   QARCH_SEC_USER
WHERE  SEC_USER_NM LIKE '%<LASTNAME>%';
-- Deactivate/rename the stale duplicate so transactions tie to the live SEC_USER_ID.

-- G. Country/state code missing or hidden (§7 PUBBA ZZ; §15 hidden countries)
SELECT * FROM SCODE_COUNTRY WHERE CODE = '<ISO2>';   -- check HIDDEN flag (code table 30092)
```

---

## 15. Expected-Behavior / User-Education FAQ

~111 Training + ~260 Customer-Error cases sit behind this group. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| **"No State/Province in the dropdown when setting up a BA"** | User picked the **wrong country code** (`USA` instead of **`US`** / wrong ISO). Pick the correct country code; the state list populates. (If genuinely empty after a zip-mask change, that's §6 — F5 / Patch #14.) | 25-01040651 |
| **"Country X isn't available in BR005 / BA"** (e.g. South Africa, Netherlands) | The country is **set Hidden by default** in code table **30092 (SCODE_COUNTRY)**. Maintenance → Code Table Value Editor → uncheck **Hidden** → Update → **Clear Cache** (Metadata Management → Select All → Clear Cache) | 26-01065977, 26-01081474 |
| **"Can't inactivate / deactivate a BA"** | Usually a **duplicate non-primary Contact-Id** on the Contact tab (unique-constraint error) or an **open JIB item** — remove the duplicate contact / close the open item, then inactivate | 26-01066538, 26-01089263 |
| **"BA info won't save / saved twice"** (and it *can't* be reproduced) | Often a genuine double-save or a single bad field — if the DB shows two saves and it won't reproduce, **working as designed** (distinguish from §4, where the DB **never** updates) | 26-01098539 |
| **"How do I add a Payment-Terms value to the BA QCFS tab dropdown?"** | Define it in **AP047**; it then appears in Core Financials | 26-01099235 |
| **"BA approval doesn't re-trigger after editing an approved BA / ACH"** | **Working as designed** — edits move the BA to **Needs Attention (ATN)** but ATN BAs stay usable in Checkwrite/AR/AP by design; blocking that is an **enhancement**, not a defect. A custom SQL audit query can monitor post-approval changes | 25-01037205 |
| **"Duplicate Tax ID comment not required" / behaves differently than Enterprise** | The web version raises a **warning** instead of Enterprise's hard requirement — expected difference | 25-01053371 |
| **"Can I change a Cost Center *type* after creation?"** | **No** — create a new cost center (or delete+recreate if never used); changing a used CC type needs an out-of-scope script | 25-01031087 |
| **"Can't migrate/promote QQM reports UAT↔PRD from the front end"** | Promotion is **back-end only** — raise an internal request to the QQM team | 26-01103387 |
| **"QQM report missing AP Invoice No"** | For AP, the populating field is **REFNUMDOC**, not `INVOICE_NO` (which is for AR) — expected universe structure | 25-01034068 |
| **"Can't edit Tax ID / need to unmask"** | BA maintenance should be done in **web, not the desktop app**; add the **UNMASKTAXID** privilege to the security group | 25-01017536 |
| **"Voucher inbox empty / vouchers missing"** | User has **multiple SEC_USER_IDs**; vouchers tied to a different one. Deactivate/rename the stale duplicate (§14 F) | 25-01029951 |
| **"Can't add/edit values in a code table"** | The list lives in a module screen (e.g. FA Location Codes 32026 / AP047) — edit it there, not via raw table | 25-01043553, 26-01099235 |
| **"Hierarchy save error: open DataReader / VALIDATE_HIERARCHY"** (OH040) | **Save each hierarchy level before adding the next** (Company → Department …) — expected sequencing | 25-01019747 |

**Tell-tale it's user/expected:** wrong **country code** chosen; a country **Hidden** in code table 30092; a **duplicate Contact-Id** blocking inactivation; an **ATN/approval** "limitation" that is by design; a QQM **promotion/universe-field** question; or "wrong access" that is just a **SEC-group** alignment. Verify country-code/SEC-group/code-table config before treating any of these as a defect. **Critically distinguish** the §4 defect (DB **never** updates, "Saved Successfully" + Global-BU unsync) from a benign double-save (26-01098539) — the former always needs the resync script + DoNew hotfix.

---

## 16. Key Code, Screens & Repos

### Screens / processes
| Screen / process | Purpose | Notes |
|---|---|---|
| **BA005** (classic + **BA Web** module) | Business Associate / Vendor master maintenance | Tabs: General, Address, Contacts, Bank, **QCFS/Core Financials**, Usage; **NEW/COPY** button is the §4 orphan trigger |
| **PUBBA** (run from **QP063** / Process Queue Explorer) | Publish/transfer BA data to **QLS** | Assembly `Quorum.ESuite.Integration.QLS`; `PUBBA_LK` lock; param 30022 |
| **SM093** | Segregation-of-Duties (Draft/Approve/Post) config | Sole-approver SOD bug fixed Hotfix 11 / 2023.04 |
| **WF005 / AP055 / AP047** | Workflow inbox / AP approval level / AP payment-terms definitions | §9, §15 |
| **GL013 / GL025 / OH040 / QP043 (Escheat) / QP0063 (Check Register)** | GL account setup / JE post / hierarchy / escheat / check register | §11 |
| **Code Table Value Editor (30092 SCODE_COUNTRY) + Metadata Management → Clear Cache** | Reference-data maintenance | Hidden-country fix (§15) |
| **QQM** (SAP BO Web Intelligence) | Reporting universes (AP/AR/GL/Cash) | Timeout, HTML-vs-Applet, universe connection, filter/joins (§10) |

### Code locations (confirmed via ADO code search)
| Symbol / file | Repo / path | Cluster |
|---|---|---|
| `QUIControllerBusinessAssociate.cs` (the **DoNew** Vendor/Customer/Bank NULL-reset fix) | `Quorum.ESuite.Web` → `Quorum.ESuite.Web.Controllers/UIControllers/` | §4 Global-BU unsync |
| `QESUITEValidationBAEntity0086_BAValidateTaxIdEffDateNoOverlaps.cs` | `Quorum.ESuite.Web` → `Quorum.ESuite.Validation/BAEntity/Validation Rules/` | §5 Tax-ID eff-date |
| `QARCH_CTRL_OBJECT_USE.json` (object-usage override metadata) | `Quorum.ESuite.Metadata` / `Quorum.ESuite.Shared.Metadata` / `<CLIENT>.Upstream.ESuite.Metadata` → `STANDARD 16.0/` | §5 override (wiped by patch) |
| `ValidateAccount.Validate()` (`Quorum.QCFS.Upstream.ValidateBL`) | QCFS Upstream validate BL (GL013 account save) | §11 GL account |
| `Quorum.ESuite.Integration.QLS` | eSuite QLS integration assembly | §7 PUBBA |

### Repos
- **`Quorum.ESuite.Web`** — BA Web controllers, BA validation rules (the §4/§5 fixes live here).
- **`Quorum.ESuite.Metadata` / `Quorum.ESuite.Shared.Metadata` / `<CLIENT>.Upstream.ESuite.Metadata`** — `QARCH_*` metadata incl. object-usage overrides. **Client metadata layer is where overrides get wiped by patches — always re-verify post-patch.**
- **`Quorum.QCFS.*`** (Upstream GUI/BL/ValidateBL) — classic QCFS accounting screens (GL/AP/AR/JE).
- QLS integration + PUBBA components for the BA→Land transfer.
- **Always check the client layer/build first** — many fixes are client-specific (APH, ARS, BTY, GEC, MST/TXO, MEW, Permian, SEP, HEC, CEN) and gated on which hotfix/patch the client has taken up.

---

## 17. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A BA **can't be saved despite "Saved Successfully"** and you've confirmed **Global-BU orphaning** — the **DoNew** code fix (§4) must be in the build; provide the BA #, client, env, and a repro of the NEW/COPY sequence. (#1719506/#1719963.)
- A **provable validation/logic bug**: Tax-ID NULL Effective-To blocking all BA updates (§5, #1693784/#1736723); UNIQUE_KEY on Use-as-Vendor re-check (#1549989); **SM093 SOD** draft+approve+post (#1771241, Hotfix 11/2023.04); state-picklist after zip-mask removal (Patch #14); PUBBA internal-BA / duplicate-routing-number (#1769479, #1777307).
- Provide: the **exact error text**, BA #/user, client + environment + **build/patch level**, and a repro. Confirm fix availability + target build in the Upstream release notes.

**Route to Cloud Ops / handle as Configuration when:**
- **Global-BU resync** scripts to repair the VENDOR table (§4) — backfill the missing IDBOWNER/IDGLOBAL row and re-link orphans; verify-SELECT in a transaction.
- **Tax-ID object-usage override** (re)application **and** confirming it's baked into the CORE build so a patch won't wipe it (§5).
- **PUBBA**: clear `PUBBA_LK` / stuck WTL-QUE, fix the process-parameter (30022) setup, deploy the QLS integration assembly, add missing country/state codes, schedule/configure PUBBA per environment (§7).
- **Security**: align **SEC-group / Upstream-template-role** membership to the client matrix; add the persona's web security group; add all workflow groups for WF005 (§9). Module entitlement (`SARCH_CNFG_INT_MODULE`), GL013 rights, import-cycle SEC group (§11).
- **QQM**: timeout extension, universe-connection refresh, report filter/join correction, folder permissions, back-end UAT↔PRD promotion (§10).
- **Process scheduler**: re-point server name + **enable** the scheduled task for stuck JE post (§11).

**Route to Identity / QCloud (no QCFS code):** Okta password resets, AD-on-profile removal, duplicate-username cleanup, the recurring-reset 15-min script (§8), Citrix Storefront entitlement / client reset / reimage, MFA / secure-gateway provisioning, server hardening.

**Handle as Training / Expected behavior (no fix):** see §15 — wrong **country code** chosen, **Hidden** country code-table entries, duplicate Contact-Id blocking inactivation, ATN/approval "limitations" by design, QQM promotion/universe-field questions, cost-center-type immutability, hierarchy save sequencing, and "wrong access" that is just a SEC-group alignment.

**Post-patch regression watch:** after any client-environment patch, **re-verify client-layer metadata overrides** (especially the Tax-ID validation override, §5) — a wiped override is the top cause of a "fixed" case re-opening.

---

*Skill created: 2026-06-14.*
*Based on: 1,302 closed QCFS cases in Case_Category (eSuite, Security, QQM, All) — 209 actionable (Software Defect 100 + Application Configuration 100 + ChangeConfig 9) mined for fix recipes, plus ~40 Training/Customer-Error cases for the FAQ. ADO work items #1719506/#1719963, #1549989, #1693784/#1736723, #1771241/#1749902/#203203, #1655202/#1765992/#1769479/#1777307/#1777518/#1781706/#1777968/#1779057/#1781736/#1744596.*
*Companion: QCFS accounting skills (GL/AP/AR/close/statements), REPO_REFERENCE.md.*
