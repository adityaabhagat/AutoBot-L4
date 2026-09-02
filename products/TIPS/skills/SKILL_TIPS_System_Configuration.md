# SKILL: TIPS System Configuration, Installation & Environment Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-11 | **Product:** TIPS (My Quorum TIPS — oil/gas transaction & accounting)
**Scope:** System Configuration / Installation / Environment Issue category. Covers: environment access & login (Citrix / Okta / AD / Oracle / QCloud), FTP/SFTP & Import-Export definition paths, QPEC services & scheduled batch jobs (STDPDA / ALLOCATEWH / SETTLE / MEAS / TRANSFER / GMASMAST / UPLOPTANLS), post-refresh scripts, QEMAIL / SMTP, metadata-layer config (QAZR / CAN / QFC / QTIP / QPEM), code-table / picklist / grid (HIDDEN_IND) config, security groups & module setup, Gas/Settlement/Plant statements, Invoice & Imbalance reports, Shared Meter / Meter Setup / Meter Split screens, Allocation Group config, and the large patch/hotfix-tracking case stream.

**Companion:** For allocation-engine logic (ALLOCATE failing on data, PPA reallocation, OBA/imbalance math) see the QPTM **SKILL_Allocations.md** model — TIPS shares the ESUITE/QPEC batch substrate. This skill is the *config / environment / screen / report* layer; it does not re-derive allocation math.

> **Evidence base:** ~1,051 closed TIPS cases in categories System Configuration (1,044) / Installation (6) / Environment Issue (1). **255 are actionable** (Root Cause = Software Defect 141, Application Configuration 110, ChangeConfig 4). The remaining ~796 are non-actionable for a fix recipe (User Administration 135, Training 93, Project Debt 92, DB Refresh 62, Platform 56, Business Change 55, Customer Cancelled 43, Customer Error 27, null 54, etc.). Every root-cause claim below cites a real SF case number and/or ADO work item observed during mining.
>
> **Data-quality caveat:** ~54 actionable cases have a blank `Resolution__c`; a large share of the "Software Defect" bucket (~50+ cases) are **patch/hotfix delivery-tracking** cases whose "subject" is just "Patch N on <version>" — those carry no symptom and are summarized as a stream, not clustered by symptom.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Decision Tree](#2-decision-tree)
3. [Cluster: Environment Access & Login (Citrix / Okta / AD / Oracle / Registry)](#3-cluster-environment-access--login)
4. [Cluster: FTP/SFTP & Import-Export Definition Paths](#4-cluster-ftpsftp--import-export-definition-paths)
5. [Cluster: QPEC Services & Scheduled Batch Jobs](#5-cluster-qpec-services--scheduled-batch-jobs)
6. [Cluster: Post-Refresh Scripts (UAT/DEV)](#6-cluster-post-refresh-scripts)
7. [Cluster: QEMAIL / SMTP / Notifications](#7-cluster-qemail--smtp--notifications)
8. [Cluster: Picklist / Grid / Code-Table Config (HIDDEN_IND, module = Internal)](#8-cluster-picklist--grid--code-table-config)
9. [Cluster: Security Groups & Module Setup](#9-cluster-security-groups--module-setup)
10. [Cluster: Gas / Settlement / Plant Statements (suppression, decimals, doubling)](#10-cluster-gas--settlement--plant-statements)
11. [Cluster: Invoice & Imbalance Reports](#11-cluster-invoice--imbalance-reports)
12. [Cluster: Shared Meter / Meter Setup / Meter Split screens](#12-cluster-shared-meter--meter-setup--meter-split-screens)
13. [Cluster: Reports "Fail to Load" / DLL / Report Definition](#13-cluster-reports-fail-to-load--dll--report-definition)
14. [Cluster: Metadata-Layer & Process/Code-Table Definition gaps](#14-cluster-metadata-layer--processcode-table-definition-gaps)
15. [Cluster: Patch / Hotfix delivery stream](#15-cluster-patch--hotfix-delivery-stream)
16. [Known ADO Items](#16-known-ado-items)
17. [Diagnostic SQL](#17-diagnostic-sql)
18. [Expected-Behavior / User-Education FAQ](#18-expected-behavior--user-education-faq)
19. [Escalation Guidance](#19-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom | Likely cause | First check |
|---------|--------------|-------------|
| "Can't log in / NT SECURITY IS BEING USED / DB error in Citrix" | Connection-info table points at old domain after a refresh/clone, or user missing from the env security group | `QARCH_CTRL_CONNECT_INFO` connection name; AD/Okta group membership (§3) |
| "Web/Classic won't open from QCloud Citrix" / opens as PDF | Citrix cert expired, or `.ica` not associated; registry `Userinit` | Citrix certificate update; KUsrInit registry value (§3) |
| Import/Export batch errors "no local file path" / file not on FTP | Import/Export (Transfer) Definition path still points at PROD or is blank after refresh | Transfer/ImpExp Definition file paths; SFTP availability (§4) |
| "Scheduled jobs stuck in QUEUE / not running since <date>" | QPEC service down/needs restart, OR incomplete metadata on a layer (QAZR), OR post-refresh script left a job enabled | QPEC status; metadata layer; post-refresh script (§5, §6) |
| Job dies at **STDPDA / ALLOCATEWH** intermittently | QPEC memory-leak / seg-process startup CPU (bootstrap logging) | Server log for "too much memory being used"; patch level (§5) |
| **QEMAIL** stops on error after refresh | `EMAIL_USERNAME/PASSWORD/HOSTNAME` global config not updated for env | Configuration Setting (Global) email keys (§7) |
| Picklist returns nothing / "Picklist not working" | TIPS module not set as **Internal**, or picklist Direct Query syntax error | Module setup = Internal; picklist `Direct Query` (§8) |
| Grid column missing in Web (present in Classic) | Grid definition `HIDDEN_IND = 1` for that column in `ESUITE_QFC` | Grid definition for the grid ID (§8) |
| Statement missing gain/loss or PPA lines; wrong decimals | Custom report suppression logic suppresses negatives not just zeroes; decimal format too short | Gas Statement custom report logic / format (§10) |
| **Single statement run returns thousands** of statements | Statement-by-BA driving query / sub-plant key defect | Plant Statement report (§10) |
| Imbalance report duplicates / spacing / errors after patch | Report registered-SQL / view defect; patch regression | Monthly Imbalance report view (§11) |
| Daily Imbalance report blank until facility unlocked daily | `m_Sel_IMBALANCE` zeros `REC_QTY` when `PPA_IND=1`; CLREALLOC not run | Reallocation flag / CLREALLOC step (§11) |
| Shared Meter screen MER auto-fills "W"; multi-facility update bug | Classic validation forcing Location fields; multi-facility defect | `DISALLOW_MODULES_FOR_METER_UPDATE` config (§12) |
| Report "Fail to Load" / "DLL Error" in V.17 | Report code/registered-SQL not migrated, or export pathway wrong in Process Definition | Process Definition export path; code stream (§13) |
| Process Type / Batch Process Type dropdown blank or missing process | Code-table not mapped to metadata module/profile | `QARCH_XREF_CDTBL_VALU_META_MOD` (§14) |
| "Patch N on <version>" | Hotfix delivery-tracking case | Confirm patch package delivered / PRD date (§15) |

---

## 2. Decision Tree

```
TIPS System-Config / Installation / Environment case
│
├─ User can't get IN (login / app launch / DB connect)?  → §3
│   ├─ After a refresh/clone or domain change → QARCH_CTRL_CONNECT_INFO points at old domain (24-00981688)
│   ├─ Citrix: cert expired / .ica opens as PDF / command prompt flashes → Citrix cert + registry (25-01039543, 24-00973811, 24-00985686)
│   ├─ Okta/AD: user not in the env's security group → add to group (24-00987731, 24-00956658)
│   └─ Oracle locked / disk full / ORA-03114 → DBA/QCloud (25-00996114, 25-00995736 family)
│
├─ A batch IMPORT/EXPORT failed?  → §4
│   ├─ "no local file path" / SFTP not available → fix Import/Export (Transfer) Definition path (24-00964237, 25-01053157)
│   └─ Paths point at PROD in UAT/DEV → repoint per env (25-01044364, 22-00693502)
│
├─ SCHEDULED JOBS not running / QPEC?  → §5 / §6
│   ├─ QPEC service down → restart (QCloud) (24-00955874, 24-00953811)
│   ├─ Job dies at STDPDA/ALLOCATEWH on memory → patch (23-00913707)
│   ├─ Stopped since a date / metadata-driven failure → metadata layer (23-00925632)
│   └─ After UAT refresh jobs enabled/QUEUE → post-refresh script (23-00935139, 23-00935513)
│
├─ EMAIL / notifications?  → §7  (global EMAIL_* config; event detector setup)
│
├─ Screen shows wrong/blank picklist or grid?  → §8
│   ├─ Picklist empty → module not Internal / picklist Direct Query (25-01050877, 24-00965214)
│   └─ Column missing in Web → grid HIDDEN_IND=1 (25-01049294)
│
├─ Security / access to a screen, report, process?  → §9  (security group / module privileges; Imbal Trade etc.)
│
├─ A STATEMENT or REPORT is wrong?  → §10–§13
│   ├─ Gas/Settlement/Plant statement (suppression, decimals, doubling) → §10
│   ├─ Invoice / Imbalance report (dup, spacing, daily-imbalance blank) → §11
│   └─ Report "Fail to Load" / DLL → §13
│
├─ Shared Meter / Meter Setup / Meter Split screen?  → §12
│
├─ Process/Batch Type or code-table dropdown empty?  → §14  (metadata module mapping)
│
└─ "Patch N on <version>" with no symptom?  → §15  (delivery tracking, confirm package + PRD date)
```

---

## 3. Cluster: Environment Access & Login

**Cases:** ~30+ actionable (mostly Application Configuration). The single largest config cluster.

**Symptom:** Users cannot log in, app won't launch from Citrix, "NT SECURITY IS BEING USED", DB connection error, account locked.

**Root cause & resolution recipe:**
- **Connection-info points at old domain after a refresh/clone.** QCloud changes the domain with a script; entries in **`QARCH_CTRL_CONNECT_INFO`** (ESuite Connection Management) must be corrected to the new connection name (e.g. point to `QCLD_IAC_ENGS17_UAT` instead of `QINT_IAC_DEV17ENGS`) so MT services start. (**24-00981688**)
- **User not in the environment's AD/Okta security group.** Add the user to the correct group (e.g. "NorthRiver Midstream Energy Limited Users") and they can access. (**24-00987731, 24-00956658, 24-00954397, 23-00930255**)
- **Citrix certificate expired / apps won't open / open as PDF / command-prompt flash.** Download & install the updated Citrix certificate; for `.ica` opening as PDF, install Citrix Workspace and set Citrix Connection Manager as default for `.ica`; for the command-prompt-on-launch, QCloud updates registry on Citrix servers. (**25-01039543, 25-01043603, 24-00978849, 24-00973811**)
- **Registry `Userinit` wrong.** Set `HKLM\...\Winlogon\Userinit` to `C:\Windows\system32\KUsrInit.exe,` (CLOUD ticket). Extra/incorrect registry entries also block login — delete the stray entry and fix the path. (**24-00985686, 23-00912305**)
- **Oracle locked / disk full / archive-log.** QCloud unlocks the Oracle account; for a halted DB, free disk and (on-prem) disable archive-log mode. (**24-00954946, 25-00996114**)
- **SSO collision.** Enabling SSO for another product (Quorum Land) interfered with TIPS SSO; resolved by a new Okta group. (**24-00961825**)

> Most of these are **Cloud Ops / QCloud** actions, not product defects. Confirm env (UAT/DEV/PRD) and whether a refresh/clone or domain change just happened — that is the usual trigger.

---

## 4. Cluster: FTP/SFTP & Import-Export Definition Paths

**Cases:** ~15+ (Application Configuration). Extremely common, especially right after a UAT refresh.

**Symptom:** Import/export batch job errors; "no local file path"; file never lands on FTP; "SFTP Connection Not Available"; Nom/Vol/Analysis/JE import fails.

**Root cause:** The **Import/Export Definition** (a.k.a. Transfer Definition / ImpExp Definition) file path is **blank or still pointed at PROD** in a non-PROD env, or the SFTP endpoint isn't reachable.

**Resolution recipe:**
1. Open the **Import/Export (Transfer) Definition** for the failing process and set the correct **local file path** and remote path for that environment. (**24-00964237** JE Export SAB, **24-00964462, 24-00978367, 25-01025055**)
2. If "SFTP not available" — QCloud/Engineering fixes the SFTP connection first, then re-point the path and re-test with the client. (**25-01053157, 25-01053159, 24-00980686, 25-01049286**)
3. After **every UAT refresh**, import paths revert to PROD — clients must re-set them (e.g. GMAS path). Treat as expected post-refresh housekeeping. (**22-00693502, 25-01044364**)

> Tell-tale: the error is on the **first/transfer step** of an import/export job and the case mentions FileZilla/WinSCP/SFTP or "after the refresh."

---

## 5. Cluster: QPEC Services & Scheduled Batch Jobs

**Cases:** ~20+ (mix of Software Defect + Application Configuration).

**Symptoms & recipes:**
- **QPEC service needs restart** — jobs queued, not progressing. QCloud restarts PRD/UAT QPEC services. (**24-00955874, 24-00953811, 24-00953361** QPEC config)
- **Scheduled jobs stopped running since a date** — "have not run since 10/14." Root cause was **incomplete metadata on the QAZR layer** causing the batch process to fail silently; fix the metadata. (**23-00925632**)
- **Job dies intermittently at STDPDA / ALLOCATEWH on memory** — server log shows "Exiting QPEC gracefully in response to too much memory being used. QPEC is using 689MB, limit 750MB… memory leak in [ALLOCATEWH]." Root cause = bootstrap-logging CPU + seg-process startup; fixed by Engineering (only write bootstrap log on error; move pipe connection earlier in seg startup). Client consumes via patch. (**23-00913707**, ADO #630489 / #1098174 / #1588505)
- **TRNX_ID integer-limit / re-run growth** — re-processing a facility for the same Prod/Acct Dt created new `QTRAN_TRNX_ID` rows each run; medium-term fix recycles TRNX_IDs and adjusts RecPurge so the "CREATE TRANSACTIONAL METERS" step IDs aren't purged. (**23-00923599**)
- **Cancel a stuck PQID** — created doc on building a code table to set batch-job/step status to **UX** to clear a stuck job (e.g. cancel PQID-1949756). (**24-00944791**)
- **UAT QPEC parameters differ from PRD** — running UAT with PRD parameters errors; align params. (**24-00944147**)

**Key batch processes seen:** MEAS → STDPDA → ALLOCATE/ALLOCATEWH → SETTLE → TRANSFER; GMASMAST/GMASMASTER (analysis import); UPLOPTANLS (Protrend analysis upload); JE Export; CLREALLOC / TIPSUNLOCK (see §11); MTHLYTODLY (journal); POST.

---

## 6. Cluster: Post-Refresh Scripts (UAT/DEV)

**Cases:** ~10 (Application Configuration / ChangeConfig).

**Symptom:** After a UAT/DEV DB refresh from PROD: scheduled jobs run when they shouldn't, security reverts, purge jobs left enabled, paths wrong.

**Root cause:** The **post-refresh script** is incomplete — it should **disable all scheduled jobs**, reset paths, and reapply non-PROD security, but misses items.

**Resolution recipe:** Update/repair the post-refresh script bundle so that on refresh: all scheduled jobs are disabled, SQL-trace-purge handled per client agreement, and security/connection config repointed. Examples: one **Purge Archive** job found enabled and disabled manually + internal ticket to fix the script (**23-00935139**); Engineering recommended leaving SQL Trace Purge active, agreed with client (**23-00935513**); ONEOK/ETP post-clone refresh script recommendations provided (**25-01000771, 25-01006808, 23-00904154**).

> This is recurring environment hygiene, not a product defect. Pair with §4 (paths) and §3 (connection info) — they all break together on a refresh.

---

## 7. Cluster: QEMAIL / SMTP / Notifications

**Cases:** ~6.

**Symptom:** QEMAIL process stops on error after a refresh; outgoing email address wrong; notification on cancel/large attachment.

**Resolution recipe:**
- Set **`EMAIL_USERNAME`, `EMAIL_PASSWORD`, `EMAIL_HOSTNAME`** in **Configuration Setting (Global)** for the environment, then restart QPEC. (**24-00944285, 22-00693503**) SMTP config reference: QuorumSoftware wiki "SMTP Configurations for sending emails" (**23-00922562**).
- Change outgoing email address in config then restart services so the app picks it up. (**23-00916973**)
- For notification control: events are configured on the **Event Detector Setup** screen (Maintenance → Notifications). `SEND_EMAIL_ON_CANCEL=0` stops cancel-notice emails; `ATTSIZERR` event configures large-attachment notifications. (**22-00854887, 25-00995736**)

---

## 8. Cluster: Picklist / Grid / Code-Table Config

**Cases:** ~15 (Software Defect + Application Configuration).

**Symptoms & recipes:**
- **Picklist returns nothing.** The **TIPS module was not set up as Internal** — set the module to Internal and the picklist populates. (**25-01050877**)
- **Picklist Direct Query syntax error** freezes/blocks the popup (e.g. Delivery Point Terms popup freeze on Meter Split). Fix the **`Direct Query`** of the picklist (e.g. Picklist **24525**). (**24-00965214**)
- **Grid column missing in Web** but present in Classic — the grid definition had **`HIDDEN_IND = 1`** for that column. E.g. grid **30031 (METER LIST)** in **`ESUITE_QFC`** had `HIDDEN_IND=1` for `MtrRedeliveryPointCode` (Meter Group); unhide it. (**25-01049294**)
- **Picklist scoping** — Run-ID picklist not scoped to facility on JOBUNAPPRV; filtering logic corrected. (**22-00561482**) Meter picklists not filtering by Facility; corrected to filter by selected Facility. (**22-00561503**)
- **Override grid pointed at wrong picklist in a client layer** — core was fine but PEM override grid 53055 pointed wrong; repoint to picklist 53068. (**22-00561508**)
- **Code-table cleanup** — remove comma separator on code table 41005 (**24-00968740**); prevent duplicates / allow null contract on code table 40666 (**23-00922401**).

> Pattern: blank/wrong picklists & grids are almost always **config in a metadata layer** (`ESUITE_QFC` grid def, picklist Direct Query, module Internal flag, code-table values), not engine bugs. Reproduce in both Web and Classic to localize the layer.

---

## 9. Cluster: Security Groups & Module Setup

**Cases:** ~15+ (note: pure user-add requests live under *User Administration*, 135 cases, and are out of scope here).

**Symptom:** Security-clearance errors; external user can't see a report link / process explorer; "Esuite not loading in web for certain security groups"; scheduler can't run company jobs.

**Resolution recipe:**
- Grant the right **security-group / module privileges**. External Process Explorer needs **query + execute** privileges on Process Explorer objects in **both ESuite and TIPS**. (**25-01003964**)
- Add **External Operator Role** to the Customer Portal for external operators. (**25-01049300**)
- Upgrade-related: security groups/scripts must be reapplied for the new version (scheduler persona menu, company jobs, query-only). (**23-00905997, 23-00905471, 23-00908175, 24-00941793**)
- External user view-report-link / posting access = **security setup** in the external group. (**24-00950867, 22-00691338-style**)
- Misassigned role (Developer instead of SYSADMIN; roles set incorrectly) → correct the role. (**23-00918332, 23-00918377**)

---

## 10. Cluster: Gas / Settlement / Plant Statements

**Cases:** ~10 (Software Defect, several ChangeConfig). High-value functional defects.

**Symptoms & recipes:**
- **Statement not showing gain/loss (or PPA) lines.** Custom report **suppression logic suppresses negatives**, but it should only **suppress zeroes**. Update the suppression to zero-only. (**25-01012556**, STX gain/loss; **23-00916681** suppress net-0 PPA lines)
- **Wrong decimals on a statement** (e.g. Wellhead Purchase price needs 4 decimals). Update the **statement/format decimal places** on the custom Gas Statement format. (**25-01015135**)
- **Single-meter statement run returns thousands of statements.** "Pull one statement by BA returned 7,779." Driving-query / key defect; resolved as a bug (tested 3/6). (**26-01080890**) Related core dev: ADO #1804667 (EIG Gas Settlement Report system-name field), #1777979 (Core Gas Statement report distribution/execution fails).
- **Theoretical gallons / shrink wrong on gas statements.** Resolved with a **new User Defined Formula** (weighted-average price) tied to a rate schedule and attached to the **CCT** per producer — avoided code change. (**25-01007229**)
- **Rate-change first-production-date on invoice/fee.** Add logic to show the first production date a rate change is calculated for a fee through the month. (**23-00916618**)

> Statements are heavily **custom per client** (CAN/QPEM layers, UDEFs, custom report formats). Most fixes are **report-logic or UDEF/format config**, occasionally a core report bug (doubling, distribution).

---

## 11. Cluster: Invoice & Imbalance Reports

**Cases:** ~8 (Software Defect + Application Configuration).

**Symptoms & recipes:**
- **Daily Imbalance report blank until facility unlocked every day.** Root cause: when a **PPA is run** modifying `REC_QTY`, stored proc **`m_Sel_IMBALANCE`** zeros the SUM `REC_QTY`; that proc feeds the writer that updates **`QRPTS_IMBAL_ACCT`**, so with `PPA_IND=1` it zeros the Daily Imbalances report view. **Workaround:** uncheck the reallocation flag via an automatic batch step **`CLREALLOC`**, configured (like Harvest) to run every time **`TIPSUNLOCK`** runs, so TIPS recalculates all allocated volume without skipping unadjusted meters. (**24-00974581** — "Facility Lock")
- **Monthly Imbalance report duplicates / spacing / errors after patch.** Core report registered-SQL/view defects. (ADO #1805277 core report spacing on Monthly Imbalance; #1805171 HEC imbalance process errors after patch #3)
- **Invoice doubling / compounded steps.** Invoice-step compounding defect investigated under V.17 (**23-00927559**). Core Settlement Invoice report (Report ID 200) dev: ADO #1802097.
- **Suppress net-0 PPA lines on Invoice Imbalance Statement.** Add logic to suppress net-zero PPA lines. (**23-00916681**)

---

## 12. Cluster: Shared Meter / Meter Setup / Meter Split screens

**Cases:** ~12 (Software Defect, several from the 2021 myQuorum-web rollout 22-00561xxx series).

**Symptoms & recipes:**
- **Shared Meter Location MER auto-fills "W"; meter update blocked.** Classic auto-populates Location fields (LSD/SEC/TWP/RGE/MER) and validation rejects. **Final config fix:** remove **PGAS** from **`DISALLOW_MODULES_FOR_METER_UPDATE`** so PGAS-sourced updates aren't validated; **code fix:** add an exception for Location fields when `SRC_MODULE_CD != ENGS`. (**24-00941208**) Web also defaults MER to 'W' to match Classic. (**22-00561488**)
- **Multi-facility shared-meter update bug / effective-date issues.** Defect on multi-facility shared meter; PPA/reallocation pop-up not triggering on the Shared Meter screen. (**24-00940800**, ADO #1791641 SRI multi-facility, #1780354 ENT pop-up not triggered, #1739299 add Operator Name to Shared Meter scope)
- **Meter Setup picklists not filtering by Facility / Mass Change screen** — filter picklists by selected Facility; Mass Change Meter screen launch corrected in Web. (**22-00561503, 22-00617665, 22-00570811**)
- **Grid order / context** — wrong column order on Shared Meter Mass Change for one user; clear that user's context via **Maintenance → User Setting Maintenance**. (**23-00879719**)

---

## 13. Cluster: Reports "Fail to Load" / DLL / Report Definition

**Cases:** ~12, heavily from the **V.17 upgrade UAT** smoke tests (AltaGas et al.).

**Symptoms & recipes:**
- **"Report Fail to Load" / "DLL Error"** on a specific report in V.17 (102B Allocation Groups, Customer Profiles by Facility, 118 Meter MOL, 132 Plant Hierarchy, Contract Audit). Root causes: report code/registered-SQL **not migrated into the code stream** (fix = add code back, **23-00934000**), or the **export pathway** in the Process Definition / Process Step Definition is wrong (fix = update export pathways, e.g. reports 109/112, **23-00922895**), or parameter exposure (AL02 hides param 153 blocking scheduling, **22-00562654**).
- **Param data-type mismatch** on a report (TOW Recon) — correct the **Parameter Definition** (script + manual steps). (**23-00917226**)

> Many V.17 "Fail to Load" UAT cases have **blank `Resolution__c`** (closed via the upgrade project). Where a recipe exists it is: re-migrate report code, fix Process-Definition export path, or fix Parameter Definition. **Resolution pattern is partly unclear from the blank-resolution UAT cases** — treat the populated ones above as the template.

---

## 14. Cluster: Metadata-Layer & Process/Code-Table Definition gaps

**Cases:** ~8 (Software Defect + Application Configuration).

**Symptom:** A Process Type / Batch Process Type dropdown is blank or a process that existed in an old version is missing in V.17; "missing metadata"; data-truncated.

**Resolution recipe:**
- **Code table not mapped to the metadata module/profile.** Add the code table to **`QARCH_XREF_CDTBL_VALU_META_MOD`** at the right module/profile/layer — e.g. add **CDTBL 80** at the QTIP module / NRM Metadata Profile (**22-00693561**); add the Process Type code table to the profile module setup via cutover script (**22-00530862**). Missing **MASTERPROC** process type in V17 (**23-00922848**).
- **Hard-coded metadata layer vs global config.** UPLOPTANLS code is hard-coded to read the **CAN** metadata layer; the **global config** must be set to match that layer. (**25-01016727**)
- **Stored-proc / layer reference stale after migration** — remove old `AZR_PRD16MID_ESUITE_QAZR` reference in `SP_SETSCHEDDATES`; redeploy proc. (**23-00884243**)
- **Wrong DB driver at install** caused "Data Truncated" — must use the **SQL Server** driver, not **SQL Server Native Client 11.0**. (**23-00921993**)

---

## 15. Cluster: Patch / Hotfix delivery stream

**Cases:** ~50+ of the 141 "Software Defect" cases are **patch/hotfix delivery-tracking** records: subject is "Patch N on <version>", "Hotfix #N", "Support Hotfix for 20xx.xx", "myQuorum Security Vulnerability Patch (XSS)". `Resolution__c` is typically just "Patch N on <version>" with an occasional PRD date.

**How to handle:** These are **not symptom-bearing**. When one surfaces:
1. It is a container for delivering one or more fixes to a specific client/version (e.g. 2019.10, 2021.04, 2022.04, 2023.04, 2024.04, 2024.10, 2025.04). Identify the underlying functional item(s) from linked cases/ADO, not from this case's subject.
2. Confirm the **patch package** was delivered (FTP) and the **PRD deploy date** is recorded.
3. Recurring clients in the stream: Energy Transfer, Markwest/MKW, NorthRiver/NRM, Oneok/ONM, Third Coast, Chord, Hilcorp, QUBE, DTE, Merit.

> The XSS/myQuorum security patches (e.g. 23-00905805, 23-00896497, 23-00903856) are platform vulnerability patches — route to the standard myQuorum patch process, not a product investigation.

---

## 16. Known ADO Items

> Titles/states verified live during mining (2026-06-11). SF-case linkage shown where the ADO title or case resolution states it; otherwise the ADO item is a same-area reference, not a proven 1:1 link (noted as "area").

| ADO # | Type / State | Title (abbrev.) | Cluster | SF / link |
|-------|--------------|-----------------|---------|-----------|
| #1804667 | Bug / Closed | EIG — TIPS Gas Settlement Report System Name field adjustment | §10 | area |
| #1777979 | Task / Closed | 2026.04 TIPS — Core Gas Statement Report Distribution & Execution Fails | §10 | area |
| #1787034 | Bug / Closed | HEP — TIPS Reports screen filters not producing results for Gas Statements | §10/§13 | 26-01081145 |
| #1785206 | Bug / Closed | SCT — Gas Statement filtering issue (TIPS) | §10 | area |
| #1802097 | Task / Active | TIPS CAN core Settlement Invoice Report (Report ID 200) | §11 | 26-01091162 |
| #1805277 | Bug / Closed | TIPS Core report spacing issue on Monthly Imbalance report | §11 | 24-00943148 |
| #1805171 | Bug / Closed | HEC — TIPS imbalance process errors after deployment of patch #3 | §11 | 26-01097671 / 1772117 |
| #1786191 | Feature / Discarded | P66 — TIPS Imbalance WAP Report | §11 | area |
| #1791641 | Bug / Closed | SRI — Shared Meter with Multi-Facility Update bug | §12 | 26-01089871 |
| #1780354 | Bug / Closed | ENT — 2024.04 PPA/Reallocation pop-up not triggered for Shared Meter screen | §12 | area |
| #1739299 | Bug / Resolved | Contracts — Shared Meter scope: add Operator Name for query | §12 | 25-01020940 |
| #630489 / #1098174 / #1588505 | (Closed) | QPEC seg-process startup CPU / bootstrap-logging perf (STDPDA/ALLOCATEWH memory) | §5 | 23-00913707 |
| #1458388 | (Closed) | Meter List date-range / cache fix (DAYS_TO_CACHE_QCTRL_VALID_PLANT_MTR_LIST_VW) | §12 | 23-00915188 |
| #1620209 | (QuorumServices) | Code table 40666 — prevent duplicates / allow null contract | §8 | 23-00922401 |
| #1616268 / #1616287 / #1616307 | Script Review/Deploy / Closed | Remove orphaned users from `SCTRL_USER_ADDITIONAL_INFO` (login error) | §3/§9 | 23-00915196 |

> Active/Proposed dev seen for the Gas-Statement area (e.g. #1803588/#1803589 IACX incorrect fixed recovery — Proposed; #1821958/#1815136 Flowcal import) indicates these clusters are **still receiving fixes** — always confirm the client's version/patch carries the fix before promising resolution.

---

## 17. Diagnostic SQL

> Table/column names below are taken from case resolutions verified during mining (`QARCH_CTRL_CONNECT_INFO`, `ESUITE_QFC`, `QARCH_XREF_CDTBL_VALU_META_MOD`, `QRPTS_IMBAL_ACCT`, `QTRAN_TRNX_ID`, `SCTRL_USER_ADDITIONAL_INFO`, `QARCH_SEC_USER`). Verify against the live schema before scripting; **SF is read-only and these are for the DB side via Cloud Ops.**

```sql
-- A. Connection-info still pointing at the old domain after a refresh (§3, 24-00981688)
SELECT * FROM QARCH_CTRL_CONNECT_INFO;          -- look for stale connection names (e.g. QINT_*_DEV vs QCLD_*_UAT)

-- B. Grid column hidden in Web but expected (§8, 25-01049294)
SELECT GRID_ID, COLUMN_NAME, HIDDEN_IND
FROM   ESUITE_QFC.<grid-def table>
WHERE  GRID_ID = 30031 AND HIDDEN_IND = 1;       -- e.g. MtrRedeliveryPointCode (Meter Group)

-- C. Code table not mapped to a metadata module/profile (§14, 22-00693561 / 22-00530862)
SELECT * FROM QARCH_XREF_CDTBL_VALU_META_MOD
WHERE  CDTBL_NO = <code table, e.g. 80> ;        -- missing row at the client's module/profile/layer

-- D. Users in additional-info security table but missing from QARCH_SEC_USER (login error, §3/§9, 23-00915196)
SELECT a.USER_ID
FROM   ESUITE.SCTRL_USER_ADDITIONAL_INFO a
LEFT-style check via NOT EXISTS (SOQL has no LEFT JOIN; this is DB-side):
SELECT a.USER_ID FROM ESUITE.SCTRL_USER_ADDITIONAL_INFO a
WHERE  NOT EXISTS (SELECT 1 FROM ESUITE.QARCH_SEC_USER u WHERE u.USER_ID = a.USER_ID);

-- E. Daily Imbalance zeroed by PPA reallocation (§11, 24-00974581)
SELECT * FROM QRPTS_IMBAL_ACCT WHERE FACILITY = '<FAC>' AND ACCT_DT = '<MTH>';
-- if REC_QTY = 0 where activity exists and PPA_IND=1 was run, schedule CLREALLOC with TIPSUNLOCK.

-- F. TRNX_ID sequence growth (§5, 23-00923599)
SELECT COUNT(*) , MIN(TRNX_ID), MAX(TRNX_ID) FROM QTRAN_TRNX_ID;   -- watch approach to integer limit
```

**Useful SF SOQL (read-only) to re-pull this population:**
```sql
SELECT Root_Cause__c, COUNT(Id) cnt FROM Case
WHERE Product_list__c='My Quorum TIPS' AND IsClosed=true
  AND Case_Category__c IN ('System Configuration','Installation','Environment Issue')
GROUP BY Root_Cause__c ORDER BY COUNT(Id) DESC
-- Note: Resolution__c cannot be used in WHERE; SOQL has no LEFT(); LIKE is case-insensitive.
```

---

## 18. Expected-Behavior / User-Education FAQ

Sampled from ~93 Training + 27 Customer Error cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|-------------|------------------|------|
| "Meter Def changed in PRD by QBS_PRD17_QPEC_USER — who did it?" | **FlowCal integration** carried changes through the platform, creating granular time slices; the QPEC user is the integration, not a person. | 26-01102547 |
| "TIPS/FlowCal opening as PDF" | Install Citrix Workspace; set Citrix Connection Manager as default for `.ica`. | 24-00978849 |
| "Where do I enter / find an analysis?" | Only two places: **Gas Analysis** screen or **Ticket Analysis** screen; check whether the meter is configured to get analysis as **derived**. | 24-00944564 |
| "FlowCal Integration widget error / widget on dashboard" | Remove the FlowCal widget for plant accountants, or correct the API-key **OPENID AUTHORITY** URL (was DEV, point to PROD). | 26-01100536, 23-00898251, 24-00947412 |
| "Only see data up to 2018 after upgrade" | **Accounting Date Maintenance** global config — adjust the open accounting date range. | 23-00898248 |
| "Value too large for table column on import" | Outside-volume columns expect fixed decimals (e.g. liquid = 2); extra trailing zeroes are rounded — no data loss. | 24-00984926 |
| "How do I end-date a facility / meter?" | Procedure provided (end-date steps); DataSync mismatch resolved by end-dating the meter. | 26-01085450, 25-01047226 |
| "Need a widget for Rate Schedule / how to add widgets" | Dashboard → Persona → Customize → Add Widget; rates tie to contracts in CCT/Contract Rates, not the Rate Schedule widget. | 23-00893129 |
| "Can't inactivate / should I delete a user?" | Set users **Inactive**, do not delete, in ESuite System Manager. | 23-00925628 |
| Auditor / license / SOC / Java-licensing questions | Provide info; QQM bundles its own JVM (no separate Oracle Java license). | 25-01003223, 25-01003273, 26-01083325, 25-01032359 |
| "QQM copy public→personal folder not working" / urgent QQM | QQM (Quorum Query Module) usage/config guidance, not a TIPS defect. | 26-01092975, 26-01066846 |
| ORA-03114 / Oracle connection (on-prem) | Server-communication issue; route on-prem clients to Database/Professional Services. | 25-01004010, 25-01014646 |

---

## 19. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A statement/report produces **wrong or doubled output** that reproduces on clean data (Gas/Settlement/Plant statement doubling 26-01080890; Monthly Imbalance spacing/dup; invoice compounding; suppression suppressing negatives).
- A screen behaves differently in **Web vs Classic** due to validation/render (Shared Meter MER auto-W; multi-facility update bug; picklist Direct Query freeze).
- A **batch process** fails on a code/perf bug, not data (QPEC memory at STDPDA/ALLOCATEWH; TRNX_ID growth; metadata-driven silent failure).
- A **stored proc / registered SQL / report DLL** is defective or missing from the code stream after upgrade.
- Match to an existing ADO bug in §16 and confirm the **fix version/patch**; if none exists, file a new bug with: client, version/patch, env, screen/process, exact error, repro steps, PQID where applicable.

**Route to Cloud Ops / QCloud (Application Configuration) when:**
- Login/access, Citrix certificate, AD/Okta group, Oracle unlock, disk/archive-log, registry, connection-info repointing (§3).
- FTP/SFTP and Import/Export Definition paths, especially **after a refresh** (§4).
- QPEC service restart, scheduled-job enablement, **post-refresh script** repair (§5, §6).
- QEMAIL/SMTP global config, Event Detector setup (§7).
- Picklist module=Internal, grid `HIDDEN_IND`, code-table → metadata-module mapping, security-group/module privileges (§8, §9, §14).

**Handle as Training / Expected Behavior (no fix) when:** the answer is a screen-navigation, a config the client owns, an audit/license question, a FlowCal-integration artifact, or a rounding/format that is working as designed (§18).

**On-prem clients:** environment, Oracle, and infrastructure issues generally route to **Professional Services**, and fixes arrive as version patches rather than self-service config.

---

*Skill created: 2026-06-11*
*Based on: 255 actionable TIPS System-Configuration/Installation/Environment cases (Software Defect 141 + Application Configuration 110 + ChangeConfig 4) out of ~1,051 closed, plus ~120 Training/Customer-Error samples and ADO work items #1804667, #1777979, #1787034, #1785206, #1802097, #1805277, #1805171, #1791641, #1780354, #1739299, #630489/#1098174/#1588505, #1458388, #1620209, #1616268. Companion: SKILL_Allocations.md (QPTM).*
