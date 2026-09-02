# SKILL: QCFS Master Data / Workflow / Ad Hoc Reporting Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QCFS — **My Quorum Financial Accounting** (upstream oil-and-gas accounting; part of the myQuorum / Upstream On Demand suite alongside QRA revenue, QCA cost-allocation/JIB, QDO division-order)
**Scope:** The cross-cutting "plumbing" of QCFS financials — **Master Data** (business units / companies, fiscal periods, banks, business associates/vendors, AFE & cost-center setup, code tables, autonumbering), **Workflow** (AP voucher / JE / batch approval & posting via POSTWKFL, workflow locks, scheduled processes), and **Ad Hoc Reporting** (SSRS/canned reports, financial statements, report paths/endpoints, Excel export, report-query data issues). This skill covers the **setup, posting-pipeline, and reporting** layer — not the revenue/owner-pay engine (QRA) or JIB/cost-allocation math (QCA), which have their own skills.
**Companion skills (sibling QCFS/Upstream groups):** revenue & owner disbursements → QRA skills; JIB / joint-interest billing & cost allocation → QCA skills; division order → QDO skills. When a "report is wrong" because the *underlying number* is wrong, fix it in the source module first — this skill handles the report/config/posting layer, which is usually the messenger.

> **Evidence base:** 479 closed QCFS cases in categories **Master Data (182) + Workflow (167) + Ad Hoc Reporting (130)**. Root-cause split: (blank) 70, Training 47, **Application Configuration 34**, Hardware/Software Change 34, Customer Error 31, **Software Defect 30**, Performance 29, Customer Cancelled 25, Business Change 25, … **ChangeConfig 2**. This skill mines the **66 actionable** cases (Software Defect 30 + Application Configuration 34 + ChangeConfig 2) for fix recipes, plus ~45 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Concepts, Screens & Pipeline](#2-concepts-screens--pipeline)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — POSTWKFL / workflow locks & posting failures (HIGHEST FREQUENCY)](#4-cluster-a--postwkfl--workflow-locks--posting-failures)
5. [Cluster B — Fiscal period & Business Unit setup (SM006)](#5-cluster-b--fiscal-period--business-unit-setup-sm006)
6. [Cluster C — Reports not found / wrong path / SSRS & Excel export](#6-cluster-c--reports-not-found--wrong-path--ssrs--excel-export)
7. [Cluster D — Report data wrong (joins, duplicate lines, segments)](#7-cluster-d--report-data-wrong-joins-duplicate-lines-segments)
8. [Cluster E — Business Associate (BA) creation, autonumbering & contacts](#8-cluster-e--business-associate-ba-creation-autonumbering--contacts)
9. [Cluster F — Bank account & ACH/check setup](#9-cluster-f--bank-account--achcheck-setup)
10. [Cluster G — AFE / cost center / JIB property master data](#10-cluster-g--afe--cost-center--jib-property-master-data)
11. [Cluster H — Code tables, grid definitions & masks](#11-cluster-h--code-tables-grid-definitions--masks)
12. [Cluster I — 1099 processes](#12-cluster-i--1099-processes)
13. [Cluster J — Environment / path / instance config (UAT/UBT refresh aftermath)](#13-cluster-j--environment--path--instance-config)
14. [Known ADO Items](#14-known-ado-items)
15. [Diagnostic SQL](#15-diagnostic-sql)
16. [Expected-Behavior / User-Education FAQ](#16-expected-behavior--user-education-faq)
17. [Key Screens, Processes & Repos](#17-key-screens-processes--repos)
18. [Escalation Guidance](#18-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| "Can't approve invoices / vouchers" — error **"Workflow instance is no longer available or does not exist"** / "Voucher was not submitted to workflow" | Stale/orphaned **workflow locks** blocking approval | §4 — release the workflow locks (script/KB); then re-submit |
| **POSTWKFL** process "stuck", "completes with errors", "Could not Post", failing after a maintenance window | Stale locks from a prior process (often **QCFSIMPCYC** killed mid-run during maintenance) blocking POSTWKFL | §4 — let running processes finish, **release active locks**, rerun |
| POSTWKFL **"Specified cast is not valid"** / **"Nullable object must have a value"** / Invalid Syntax | Posting-step data/code defect | §4 — script to fix the offending field; or hotfix WI |
| "SM006 not set up for 2026" / can't run an ACH dated next year | Fiscal periods not created for the new year | §5 — SM006 → **Global** company → Auto Create → **update screen to save** |
| **DELETE … REFERENCE constraint / duplicate key** error on SM006 opening/closing periods | SM006 leaves a transaction open on exception → blocking; code defect | §5 — 2022.04 hotfix; interim Global **resync** script |
| Business Unit created in MF035/SM006 but **missing from picklist** | BU not fully linked (BA link) / replication | §5 — link BA, deploy add-BU script |
| "Failed to load the report … filename was empty" / report not found after refresh | **Report path** points at wrong environment (post-refresh repoint) | §6/§13 — rerun post-refresh path scripts; fix SSRS endpoint config |
| Report calls **DEV server** from UBT/UAT; can't select banks (AP061) | `SRRS_ENDPOINT_URL` / `REPORT_SERVICE_URL` global config wrong | §6 — set REPORTS key group endpoint to the env's SSRS URL |
| Open report in **Excel → sign-in fails** | Outdated Citrix VDA / Office license | §6/§13 — upgrade VDA on Citrix server; fix M365 license |
| Report shows **duplicate / pseudo-duplicate rows**, wrong segment, "strange State values" | **Report SQL join** missing a predicate (e.g. property↔state) | §7 — add the missing AND to the join |
| New BA auto-numbers starting at an **existing number** / "new number could not be created" | Autonumber seed wrong in **QARCH_TRAN_SEQ / AUTONUMBERINGMASTER**; PUBBA adapter not updated | §8 — reseed last-used number; update PUBBA adapter |
| "Cannot insert NULL into BANKACCOUNT" in MF035; new bank won't save | Bank set up via the wrong screen | §9 — follow SM002→SM021→BR037→BR036→AP048 sequence (not MF035) |
| AFE imported without cost center / **AFE_IMPORT locks every month** | Concurrent-upload delete-then-reinsert defect; or stale import lock | §10/§4 — code fix scopes delete by file; release lock & re-import |
| "Not an active JIB property" on AP invoice; GL with no JIB group code shows in JIB | Property/Tier **JIB-Based flag** or **JIB group code** config | §10 — set JIB-Based flag on the DOI; fix GL group-code mapping |
| "Cannot add job code" / column in UAT ≠ PRD / hidden mandatory column | **Code-table grid definition** points at wrong table id | §11 — fix the grid definition's Code Table id for that column |
| Zip codes / masked field won't save | **Field mask** (e.g. `ZIPCODE_MASK_WEB`) too restrictive | §11 — remove/relax the mask in Metadata |
| 1099 export option missing / warnings (QSTG1099EX vs QSTG1099OVR) | Old 1099 process disabled since 2020.09 | §12 — use **QSTG1099OVR**; 1099 at address vs entity level |

---

## 2. Concepts, Screens & Pipeline

```
MASTER DATA (setup)                WORKFLOW (post pipeline)              REPORTING
  SM006  Business Unit / fiscal      AP voucher / JE / batch              SSRS canned reports (RPT_*, APR*, ARR*)
         periods (Global company)      → submit to Workflow (WF005)        GL016/GL232 financial statements
  MF035  Company / BU master          → approve / reject                   QP043/QP073/QP074 process+report launchers
  BR037/BR036  bank accounts          → POSTWKFL (post to GL)              Excel / M365 export via Citrix
  AP048  vendor check-run def           ↑ uses LOCKS (SXL)                 report PATH + SSRS ENDPOINT config
  SM002/SM021  autonumber / jrnl def   QCFSIMPCYC  import-cycle (revenue→QCFS, JIB) ── shares the same lock pool
  BA005/BA030  business associate/contacts
  Code tables (32xxx) + grid defs
```

### Key terms (QCFS / Upstream vocabulary)
- **QCFS** = My Quorum Financial Accounting (the GL/AP/AR/bank/financial-statement core). **QRA** = revenue/owner-pay, **QCA** = cost allocation / JIB, **QDO** = division order. They share one DB and one **process-lock** pool.
- **POSTWKFL** = the batch process that posts workflow-approved AP vouchers / JEs / batches to the GL. Most workflow tickets here are **POSTWKFL "stuck / errored"** and resolve by **releasing stale locks**.
- **QCFSIMPCYC** = the import-cycle process (pulls revenue/JIB into QCFS). Frequently the *cause* of POSTWKFL blockage: if QCFSIMPCYC is killed mid-run (often during a QCloud maintenance window) it leaves **stale locks** that later processes can't acquire (24-00948904, 26-01082993).
- **Workflow lock / SXL error** = QCFS serializes posting via DB locks; an aborted process leaves a lock that blocks the next one. The standard fix is **release the active locks** (there is a KB article + queries) and rerun — *not* a code change.
- **SM006** = Business Unit Maintenance, incl. **fiscal period** open/close. Periods must be created/managed **from the Global company** for soft/hard close to work, then the **screen must be updated to save**.
- **MF035** = Company/BU master maintenance (where a company/BU is first created and linked to a BA). A BU created here must be **linked to a BA** before it appears in SM006 picklists (24-00968561).
- **BA** = Business Associate (vendor/owner/operator master). **BA005** = BA maintenance, **BA030** = contacts. Auto-numbering is driven by **QARCH_TRAN_SEQ** (last-used number) and **AUTONUMBERINGMASTER**; **PUBBA** is the public-BA adapter that the Web app must be pointed at after a V17 cutover.
- **BR037 / BR036** = physical bank account + bank-account-type setup; **AP048** = vendor check-run definition; **SM002** = autonumber definitions; **SM021** = journal definitions. New bank accounts must be built through this sequence, **not** MF035.
- **JIB-Based flag** = a flag on the Property/Tier **DOI** that makes a property eligible for joint-interest billing. Missing flag → "not an active JIB property" on AP (26-01066978). GL accounts with **no JIB group code** wrongly appearing in JIB is the inverse mapping issue (25-01008678).
- **AFE** = Authorization for Expenditure; cost centers live in **QCTRL_AFE_COST_CNTR**. AFE import is multi-child/concurrent and has a known delete-scope defect (24-00983364).
- **Code tables (32xxx) + grid definitions** = the metadata that drives lookup grids (e.g. 32026 FA Location Codes). A grid column can point at the wrong **Code Table id**, hiding a mandatory column (24-00992353).
- **SSRS endpoint config** = global config keys **`SRRS_ENDPOINT_URL`** / **`REPORT_SERVICE_URL`** (Key Group `REPORTS`, Metadata Layer "Environment Specific") that tell each environment which report server to call. Post-refresh, these (and report file paths) frequently point at the wrong env (25-01049564, 26-01101171).
- **QPEC** = the QCFS application/compute server tier; **instances per QPEC** is a throughput setting that must match across PRD/UAT/UBT (25-01042000). The `QVariant.cpp | 692` "Attempt to convert From Type 8 To Type 11" QPEC event-log message is **informational** (24-00974584).

---

## 3. Decision Tree

```
QCFS Master-Data / Workflow / Reporting case
│
├─ Posting / approval blocked? (AP voucher, JE, batch, POSTWKFL)
│   ├─ "Workflow instance no longer available" / can approve-reject but not approve   → §4 (release workflow locks)
│   ├─ POSTWKFL stuck/errored AFTER a maintenance window / QCFSIMPCYC killed          → §4 (stale-lock release, then rerun)
│   ├─ POSTWKFL "Specified cast"/"Nullable object"/Invalid Syntax/"Could not Post"   → §4 (data-field script or hotfix WI)
│   └─ "Could not Post" but really bad DOI GL distribution / wrong autonumber setup   → §16 (customer data error)
│
├─ Period / BU setup?
│   ├─ "SM006 not set up for <year>"                                                  → §5 (Global → Auto Create → save)
│   ├─ DELETE FK / duplicate-key error opening-closing periods                        → §5 (2022.04 hotfix; Global resync script)
│   └─ New BU/company missing from picklist                                           → §5 (link BA; add-BU script)
│
├─ Report won't run / not found / can't export?
│   ├─ "report filename was empty" / report not found (esp. after refresh)            → §6 / §13 (repoint paths; SSRS endpoint config)
│   ├─ Report calls DEV from UBT/UAT (AP061 bank selection)                           → §6 (SRRS_ENDPOINT_URL / REPORT_SERVICE_URL)
│   └─ Excel/M365 export sign-in fails                                                → §6 / §13 (VDA upgrade; M365 license)
│
├─ Report runs but DATA is wrong?
│   ├─ Duplicate/pseudo-duplicate rows, strange segment/State                         → §7 (missing AND in report join)
│   └─ Income statement / financial-statement errors                                 → §7 (GL016/GL232 header config)
│
├─ Master-data create/save failing?
│   ├─ BA autonumber wrong / "new number could not be created"                        → §8 (QARCH_TRAN_SEQ / AUTONUMBERINGMASTER; PUBBA adapter)
│   ├─ Bank account won't save / NULL BANKACCOUNT                                      → §9 (SM002→SM021→BR037→BR036→AP048)
│   ├─ AFE without cost center / AFE_IMPORT locking                                    → §10 (delete-scope fix; lock release)
│   ├─ "Not an active JIB property" / GL w/o group code in JIB                         → §10 (JIB-Based flag; group-code map)
│   ├─ "Cannot add job code" / hidden mandatory column / UAT≠PRD columns               → §11 (grid-definition Code-Table id)
│   └─ Masked field (zip) won't save                                                   → §11 (relax mask in Metadata)
│
├─ 1099?                                                                               → §12 (QSTG1099OVR; address-level flag)
│
└─ Vague "error", audit/"how does it work", process-question, slow                     → §16 Expected-Behavior FAQ
```

---

## 4. Cluster A — POSTWKFL / workflow locks & posting failures

**The single largest signature across Workflow cases.** Symptoms cluster into three families, the first two of which are **operational (release locks)**, the third a **defect/hotfix**.

### A1. Workflow locks block AP-voucher approval (config/operational — NOT a code fix)
**Symptom (25-01021798, GLE):** "Several users can't approve invoices but can reject them." Error **"Workflow instance is no longer available or does not exist"** + **"Voucher was not submitted to workflow."**
**Root cause:** orphaned workflow locks left behind on the voucher/workflow tables.
**Fix:** deploy/run the **script to remove the workflow locks**; users can then approve. This recurs — there is a KB article for releasing process locks (26-01082993).

### A2. POSTWKFL / QCFSIMPCYC stale locks after a maintenance window (operational)
**Symptom:** POSTWKFL is "stuck," "locked since <date>," or each subsequent scheduled process fails with **SXL** lock errors; often right after a QCloud maintenance window.
**Root cause:** **QCFSIMPCYC** (or another process) was scheduled during/near maintenance, got killed mid-run, and **never released its locks** (24-00948904, 24-00960174, 23-00890511, 22-00653839, 26-01082993).
**Fix recipe:**
1. Identify the running/stuck processes; **let any genuinely-running process finish** (do not kill blindly).
2. **Release the stale/active locks** (KB article + the lock queries — see §15) so POSTWKFL/QCFSIMPCYC can acquire its lock.
3. Rerun POSTWKFL (or let the schedule pick it up). Client can self-serve via the KB once trained.
> Tell-tale that it is *this* and not a defect: the failure starts immediately after maintenance and "stale locks from <prior date>" appear in the lock query.

### A3. POSTWKFL posting-step defects (Software Defect — script or hotfix)
| Signature | Root cause | Fix | Case / ADO |
|---|---|---|---|
| POSTWKFL completes with **"Specified cast is not valid"** | Bad `IDBATCHMASTER` field value | Script to update `IDBATCHMASTER` | 23-00910972 |
| POSTWKFL error when posting JE / **QP045 Post Workflow Manual Request** odd behavior | Posting-step data defect | Script sent; hotfix back-ported to 2020.09 where needed | 22-00523349, 22-00652068, 22-00651968 |
| **AP workflow** users blocked | Service hung | **Restart of service** corrected it | 22-00654835 |
| Web POSTWKFL doesn't post (works from Classic) | Web-vs-Classic posting parity bug | Bug, Closed | **ADO #1755621** (SOC2) |
| AP Reversal stuck in Post Pending; POSTWKFL in CE "Nullable object must have a value" | Null-handling in posting step | Bug, Closed | **ADO #1769179** (SGY, SF 25-01052627) |
| 2022.04 **Invalid Syntax** running POSTWKFL | SQL-syntax defect in 2022.04 line | Bug, Closed | **ADO #1760237** |
| POSTWKFL **automatic process not running** in Schedule Definition | Scheduler defect | Bug, Closed | **ADO #1728471** |
| POSTWKFL Account Balance **deadlock** | Deadlock under concurrency | Prevention task | **ADO #1742965** (25.14) |
| MyQuorum **AP widgets** not working | Web report-parameter autocomplete bug | Bug, Closed | **ADO #1618264** (SF 24-00940955) |
| Schedule POSTWKFL to run every 5 min | Scheduler config | Script to set POSTWKFL interval | 25-01081423 |

**AFE-in-workflow can't approve (22-00711024):** reproducible by submitting an AFE **supplement without an amount** into workflow → aborted records. Interim fix = **script to clear the aborted records**; long-term WI created.

---

## 5. Cluster B — Fiscal period & Business Unit setup (SM006)

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| "SM006 not set up for <year>" (e.g. can't date a 1/2/2026 ACH) | Fiscal periods for the new year not created | SM006 → select **Global Company** → enter # of fiscal years → **Auto Create** → **update the screen to save**. All periods must be added from Global for soft/hard close | 25-01063039 |
| **DELETE statement conflicted with REFERENCE constraint** + duplicate-key on `BUSINESSENTITYPERIOD` when opening/closing periods | On an exception during SM006 update, a **transaction was left open**, creating blocking until the app closed; periods got created at individual-BU level too | Code change to **skip the delete in the exception path**; delivered in **Upstream 2022.04 Hotfix – May 2025** (TGNR). Interim: **SM006 Global resync** script | 25-01014730 / **ADO script-deploys #1734039, #1773563** |
| New **Business Unit missing from SM006 picklist** after creation in MF035 | BU created in MF035 but not surfacing (BA link / replication) | Deploy script to add the BU once it is created in MF035 **and the respective BA is linked** | 24-00968561 (also 24-00980352) |
| Pacific Partners company had a bad company number `1/1/1900` | Wrong company code value | Update company code to `145` in SM006 | 24-00951936 |
| New consolidated / functional-unit BUs | Setup guidance | Provided configuration details | 23-00900417 |

**Fix recipe:** for period work, **always operate from the Global company in SM006**, Auto Create the years, and **save by updating the screen**. For the FK/duplicate-key error, confirm the **2022.04 May-2025 hotfix** is deployed; until then a **Global resync** script realigns BU periods. For "BU missing," verify it exists in MF035 **and** is linked to a BA before scripting it into the picklist.
> Active enhancement direction (Proposed): **"SM006 Add in new months"** (#1778306) and **"Hide APWF Closed Date from SM006"** (#1749934, #1790222) — mention if a client asks about period-screen changes.

---

## 6. Cluster C — Reports not found / wrong path / SSRS & Excel export

Most "report won't run / not found" tickets are **environment path / SSRS-endpoint config**, very often the aftermath of a database/environment refresh (see also §13).

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| "Failed to load the report … The report filename was empty" (DOINTXFER pointing at wrong UATA1 path) | Post-refresh scripts left **UATA1 pointing at UBTA1 paths** | **Re-run the post-refresh scripts** (from the correct prior dates) to reset report paths + process config | 26-01101171 |
| AR Cash Call Invoice "not found" in UBT | Report **path** wrong | Changed the path to find the reports | 25-01055348 |
| Reports broken (SSRS) | SSRS link stale | **SSRS link updated** | 23-00906762 |
| **AP061 Bank Selection report calls the DEV server** from UBT | Wrong SSRS endpoint config for the env | Maintenance → Configuration Control Settings → **Global**; Key Group **REPORTS**, Metadata Layer **Environment Specific**, set **`SRRS_ENDPOINT_URL`** + **`REPORT_SERVICE_URL`** to the env's ReportServer URL (`…/ReportServer/ReportExecution2005.asmx`) | 25-01049564 |
| Opening reports in **Excel → Microsoft sign-in fails** | Outdated **Citrix VDA** on the (UBT) Citrix server | Upgraded VDA so users authenticate with their M365 account | 25-01045791 |
| Missing reports | Config / catalog | resolution pattern unclear from mined cases (Resolution blank) | 26-01094233 |
| Rename HFM Account Balance report | Cosmetic rename request | (Resolution blank) | 25-01030028 |

**Fix recipe:** when a report "can't be found" right after a refresh/maintenance, suspect **paths/endpoints pointing at the wrong environment**. (1) Re-run the **post-refresh path scripts** (26-01101171). (2) Verify the **`REPORTS` global config keys** `SRRS_ENDPOINT_URL` / `REPORT_SERVICE_URL` point at *this* env's SSRS (25-01049564). (3) For export/sign-in failures, it's usually the **Citrix VDA / M365 license**, not QCFS (25-01045791, 23-00906350).

---

## 7. Cluster D — Report data wrong (joins, duplicate lines, segments)

When the report *runs* but the numbers/rows are wrong, it is usually a **report SQL** or **header config** issue, not the source data.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| JE History / JE Entry Detail report show **pseudo-duplicate rows** with strange "State" values | The **report join** between property and state was missing a predicate | **Add the additional AND** to the property↔state join | 25-01012020 |
| **Income Statement** errors / won't run | Header configuration on the financial-statement screens | Corrected **header configurations in GL016 and GL232** | 23-00912953 |
| Duplicate lines on **ARR005** not matching AR090 batch | Report defect | Patch required | 22-00669761 |
| Financial Statement Report issue | Defect | Resolved in upgrade | 22-00565014 |
| LOS report — **no revenue pulling in on Gross** | Report/data defect | Defect resolved in **March 2024 hotfix** | 24-00938781 |
| Level-3 Org Code **3220 doubling up** | Org-setup glitch surfaced in report | Had client **correct the org configuration** | 23-00886737 |
| Incorrect business segment displaying for reports | Segment config | "correct" (config corrected) | 25-01007454 |
| Bank Reconciliation Outstanding Checks (EQT-specific) failing for single BU+bank | Missing index on the EQT-specific report | **Added an index** to the report; tracked for **Patch 17** | 24-00965148 (→ 24-00969913) |

**Fix recipe:** reproduce with the client's exact parameters. "Duplicate / strange extra rows" almost always = a **report join missing a predicate** (25-01012020). Financial-statement (income statement / trial balance) errors are usually **GL016/GL232 header configuration** (23-00912953). EQT-specific / single-BU performance failures may need an **index on the custom report** (24-00965148).

---

## 8. Cluster E — Business Associate (BA) creation, autonumbering & contacts

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **V17 upgrade** — BA autogeneration **starting at an existing number**; PUBBA not working | (a) `QARCH_TRAN_SEQ` last-used BA number not seeded to the true last value; (b) **PUBBA** not updated at cutover to the new **Web PUBBA adapter** | Updated **Last User Number for BAs in `QARCH_TRAN_SEQ`** to the true last value (44350); **updated the PUBBA adapter via script** | 25-01023079 |
| Batch "Could not post" — **"new number could not be created from the AutoNumberMaster table"** | A user **cleared a number out of `AUTONUMBERINGMASTER`** (ACH), so autonumbering failed | Restore the autonumber config in AUTONUMBERINGMASTER | 24-00963774 |
| BA auto-numbering (general) | Autonumber config | (Resolution blank) — see reseed pattern above | 24-00989661 |
| BA screen **Core Financials tab not working** (MEW 2024.04) | Web BA screen defect | Software Defect (Resolution blank; treat as upgrade/hotfix) | 24-00989199 |
| Mass-add **5,890 contacts (BA030)** | Bulk data load | Added the records to Contacts (data load) | 24-00947205 |
| "Invalid BA Notes API Configuration" (Permian upgrade) | Note-controller creation broken by a Platform change; bad global config blocked the QDO→ESuite call | Corrected note-controller creation; enhanced code so a **global config can override the ESuite API URL** (Key Group `API-ENGS`, Key `URL`; default = ESuite base URL + `_API`) | 24-00969356 |

**Fix recipe:** BA autonumber problems after an upgrade/cutover are the recurring pattern — check (1) the **last-used number seed in `QARCH_TRAN_SEQ`**, (2) whether **`AUTONUMBERINGMASTER`** was edited (a cleared row breaks it), and (3) whether the **PUBBA Web adapter** was pointed correctly at cutover (25-01023079). For BA↔ESuite API errors after a Permian-style upgrade, the override is the `API-ENGS / URL` global config (24-00969356).

---

## 9. Cluster F — Bank account & ACH/check setup

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **"Cannot insert the value NULL into column 'BANKACCOUNT'"** in MF035 when setting a bank account | Bank account being created via the **wrong screen (MF035)** | Build the physical bank account through the correct sequence (below) — **do not add via MF035** | 25-01009852 |
| New bank account set up but not usable | `Deposit Journal Def` column on **BR036** was blank | Set the bank-account type's **Deposit Journal Def** value in BR036 | 22-00853542 |
| document tool not working in classic | Wrong port in config files | Corrected the port in config | 22-00874999 |
| ACH Email Remittance process failed | Config | resolution pattern unclear (Resolution blank) | 25-01012940 |

**Physical bank-account setup sequence (25-01009852) — the canonical recipe:**
1. **SM002** — create the autonumber ID (check format `########`).
2. **SM021** — add the journal definition.
3. **BR037** — create the **physical bank account**.
4. **BR036** — set the bank-account type; tick **"Allow payments"**; set the **Deposit Journal Def** (22-00853542).
5. **AP048** — set the **Vendor Check Run Definitions**.
> Building a bank account directly in **MF035** is the recurring mistake that throws the NULL `BANKACCOUNT` error.

---

## 10. Cluster G — AFE / cost center / JIB property master data

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| AFE copied from Execute → Quorum **without Cost Center** (concurrent multi-file upload) | On concurrent uploads the import **deletes all `QCTRL_AFE_COST_CNTR` rows for every AFE in the process**, then re-inserts only the current child's — wiping the others | **Code change to scope the delete by file path/name** so each child job only deletes its own data; delivered in next release | 24-00983364 |
| **AFE_IMPORT locks every month** | Stale import lock | **Script to fully import the AFE** / release the lock (operational; see §4) | 24-00947529 |
| **"This property is not an active JIB property"** on all invoices booked to a property | The Property/Tier combo's **DOI was not marked JIB-Based** | Mark the **JIB-Based flag** on the DOI; approvals then proceed | 26-01066978 |
| Transactions booked to **GL accounts with no JIB group code** showing up in JIB | JIB group-code mapping on the GL accounts | Correct the GL/JIB group-code config | 25-01008678 |
| Payout **POMERGEJIB** completes with errors — "No JIB data selected to load" for 8/1/2021 | Missing/incomplete QCA data for the period | **Script to reload the QCA tables** so the JIB process completes | 23-00929347 |
| APH **block** — wrong cost centers/AFEs | Bad cost-center/AFE values | **Update script** for the cost centers and AFEs | 26-01079962 |
| Script to assign **security to new Business Units** | BU security | Advised the script is **no longer required** with the update; provided **Enable Business Unit Security** doc | 24-00939219 |

**Fix recipe:** for AFE-import cost-center loss, confirm the **delete-scope-by-file** fix is in the build (24-00983364); interim, re-import. For JIB eligibility errors, the answer is almost always the **JIB-Based flag on the DOI** (26-01066978) or the **GL→JIB group-code mapping** (25-01008678) — both config. POMERGEJIB "no data" is upstream QCA data — reload it (23-00929347).

---

## 11. Cluster H — Code tables, grid definitions & masks

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **"Cannot add job code"** to Code Table 32026; UAT≠PRD columns; mandatory `ST_CD` hidden / "cannot be null" | The **grid definition's Code Table id** for the `ST_CD` row pointed at the wrong table, so **32026 FA Location Codes** didn't show the available states | Fix the **grid definition** so the column points at the correct Code Table id (table 2026 FA Location Codes); data then populates | 24-00992353 |
| **Zip codes not saving** (INC0050534) | **`ZIPCODE_MASK_WEB`** field mask too restrictive | **Remove the mask** for `ZIPCODE_MASK_WEB`; check in the Metadata change | 24-00975935 |
| Code Table 34039 **Tangible Flag column missing** | Grid/metadata column config | (Customer Error; resolution blank) — same grid-definition family | 24-00972662 |
| Database exception saving attribute data | Attribute Group/Type names didn't **exactly match** the PK rows in `SCODE_ATTR_TYPE` | Make names match exactly (spaces, underscores, case, dashes) vs the source tables | 23-00878286 |

**Fix recipe:** "can't add a value / mandatory column hidden / UAT≠PRD columns" = the **grid definition Code-Table id is wrong** (24-00992353) — fix the column's table pointer in the grid definition. A field that **silently won't save** is usually a **metadata mask** (24-00975935). "Database exception" on attribute setup = **exact-name mismatch** vs the PK in `SCODE_ATTR_TYPE` (23-00878286).

---

## 12. Cluster I — 1099 processes

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| 1099 preliminary review — **QSTG1099EX export option missing** (QP073), QP043 Export Summary throws warnings | **`QSTG1099EX` was disabled since version 2020.09** | Use **`QSTG1099OVR`** going forward — it captures the same data plus override options (`QSTG1099EX` staged data for later QRA consolidation; `QSTG1099OVR` supersedes it) | 25-01062066 |
| V17 upgrade — **1099 flag error** | 1099 was set at the **entity** level; client wants it at the **address** level | Set global config **`BA_ADDRESS_1099 = 1`** on the CEN layer (handle 1099 at the address, not the entity) | 25-01041723 |
| 1099 Updates (general) | 1099 process defect | (Resolution blank) — confirm target patch | 22-00674521 |

**Fix recipe:** the modern 1099 path is **`QSTG1099OVR`** (not the disabled `QSTG1099EX`). 1099 at **address vs entity** level is a **`BA_ADDRESS_1099`** global-config toggle.

---

## 13. Cluster J — Environment / path / instance config (UAT/UBT refresh aftermath)

A recurring **Application Configuration** family: after a DB refresh or maintenance, environments point at the wrong paths/servers or are under-provisioned.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| UATA1 report/process paths pointing at **UBTA1** after refresh | Post-refresh scripts set the wrong paths | **Re-run the post-refresh scripts** from the correct dates to reset paths + processes | 26-01101171 |
| AP061 calling **DEV** SSRS from UBT | Endpoint config | Set `SRRS_ENDPOINT_URL` / `REPORT_SERVICE_URL` (Key Group REPORTS) — §6 | 25-01049564 |
| **Instances per QPEC** = 4 after maintenance (too few for load) | Default reset on maintenance | **Raise UAT/UBT instances per QPEC to 20** to match PRD | 25-01042000 |
| EQT **OOC Patch 20** to reduce QCFS/QCA cache load on the server | Cache/server load | Deploy OOC Patch #20 code changes | 26-01094254 |
| Unable to access UAT **Maintenance App** | Outdated **SQL driver** for the Maintenance App install | Update the SQL driver | 24-00983516 |
| DB connection drops on large tables (**TCP Provider** error) | Firewall/firmware | **Firmware update** on the firewall | 23-00931186 |
| User accounts not set up / multiple users can't access | User/security config | Configured the users (with services) | 25-01033234 |
| TST processes not running | Env/process config | resolution pattern unclear (Resolution blank) | 23-00921108 |

**Fix recipe:** treat "broke right after a refresh/maintenance" as **environment config drift** — re-run **post-refresh path scripts** (26-01101171), verify **SSRS endpoint keys** (25-01049564), and check **instances per QPEC** matches PRD (25-01042000). Maintenance-app and DB-connection failures are usually **driver/firmware**, not QCFS code.

---

## 14. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1769179** | Bug / **Closed** | SGY — AP Reversal in Post Pending; POSTWKFL CE "Nullable object must have a value" | §4 | 25-01052627 |
| **#1760237** | Bug / **Closed** | 2022.04 Invalid Syntax whenever running POSTWKFL | §4 | — |
| **#1755621** | Bug / **Closed** | SOC2 — Voucher not posted when POSTWKFL run from Web (OK from Classic) | §4 | — |
| **#1728471** | Bug / **Closed** | POSTWKFL automatic process not running in Schedule Definition | §4 | — |
| **#1742965** | Task / **Closed** | Dev — POSTWKFL Account Balance deadlock prevention (25.14) | §4 | — |
| **#1716612 / #1715938** | Task/Requirement / **Closed** | POSTWKFL — setting POSTED date in child tables | §4 | — |
| **#1618264** | Bug / **Closed** | Autocomplete not working for Report Parameters (myQ AP widgets) | §4/§6 | 24-00940955 |
| **#1734039** | Script Deployment / **Closed** | FMO Upstream PRD16 — SM006 message delete script | §5 | (25-01014730 family) |
| **#1773563** | Script Deployment / **Closed** | TGNR — SM006 Global Resync script PRD deployment | §5 | — |
| **#1778306** | Requirement / **Proposed** | UPS CORE_REL — SM006 add in new months | §5 | — |
| **#1749934 / #1790222** | Requirement / **Proposed** | UPS CORE_REL — Hide APWF Closed Date from SM006 | §5 | — |

> Many actionable QCFS cases were dispositioned **operationally** (lock-release KB, post-refresh path scripts, config edits, reseed scripts) with **no single product WI** — e.g. workflow-lock release (25-01021798, 24-00948904), SSRS endpoint config (25-01049564), BA autonumber reseed (25-01023079), bank-setup sequence (25-01009852). Several **defects** name a **hotfix/patch rather than a WI**: SM006 FK fix → **Upstream 2022.04 Hotfix May-2025** (25-01014730); LOS Gross → **March 2024 hotfix** (24-00938781); EQT bank-rec index → **Patch 17** (24-00965148); AFE delete-scope fix → "next release" (24-00983364); pay-terms fix → **2024.10 Hotfix June-2026** (26-01096761). Confirm exact build/patch in the relevant `Quorum.*.ReleaseNotes` / `<CLIENT>.Upstream.*` repo before stating fix availability.

---

## 15. Diagnostic SQL

> **Caveat:** QCFS runs on **SQL Server** (note `dbo.` tables, `IX_*` indexes, `SqlException` — distinct from TIPS/Oracle). Table names below are taken from case repro text; **verify against the client DB before scripting**, and always run a verify-SELECT before any DELETE/UPDATE, wrapped in a transaction.

```sql
-- A. Stale process / workflow locks blocking POSTWKFL / QCFSIMPCYC (§4)
--    Identify locks held by a prior/aborted process so they can be released per the KB.
--    (Lock table names vary by version; common patterns: process-lock / SXL lock tables.)
SELECT *            -- look for locks from a prior date / a killed QCFSIMPCYC run
FROM   <process lock table>          -- e.g. the SXL / process-lock table
WHERE  LOCK_DATE < CONVERT(date, GETDATE())   -- stale (yesterday or older)
ORDER BY LOCK_DATE;

-- B. Fiscal periods that exist for a BU / year (the SM006 "not set up for <year>" check, §5)
SELECT FISCAL_YEAR, FISCAL_PERIOD, BUSINESS_ENTITY_ID
FROM   dbo.BUSINESSENTITYPERIOD
WHERE  FISCAL_YEAR = <YEAR>
ORDER BY BUSINESS_ENTITY_ID, FISCAL_PERIOD;
-- The 25-01014730 error is a duplicate-key on IX_BusinessEntityPeriod_FiscalYearPeriod
-- (periods created at individual-BU level as well as Global) → confirm 2022.04 May-2025 hotfix.

-- C. BA autonumber seed vs actual last-used (the V17 "starting at existing number", §8)
SELECT *  FROM dbo.AUTONUMBERINGMASTER WHERE <key for BA / ACH>;   -- a cleared row breaks autonumber (24-00963774)
SELECT MAX(<BA number col>) AS last_used FROM <BA master table>;    -- compare to QARCH_TRAN_SEQ last-user-number (25-01023079)

-- D. Bank account setup completeness (§9) — BR036 Deposit Journal Def must be set
SELECT BANK_ACCOUNT, ALLOW_PAYMENTS, DEPOSIT_JOURNAL_DEF
FROM   <BR036 bank-account-type table>
WHERE  BANK_ACCOUNT = '<acct>';     -- blank DEPOSIT_JOURNAL_DEF = the 22-00853542 issue

-- E. AFE cost centers (the concurrent-import wipe, §10)
SELECT AFE_NO, COST_CNTR, FILE_NAME
FROM   QCTRL_AFE_COST_CNTR
WHERE  AFE_NO = '<afe>';            -- missing rows after a multi-file import = 24-00983364

-- F. JIB eligibility / group code (§10)
SELECT PROPERTY_NO, TIER, JIB_BASED_FLAG       -- JIB_BASED_FLAG must be set on the DOI (26-01066978)
FROM   <property/DOI table> WHERE PROPERTY_NO = '<prop>';
--   GL accounts with NULL JIB group code that still hit JIB = 25-01008678.

-- G. SSRS endpoint config for THIS environment (§6/§13)
--    Maintenance > Configuration Control Settings > Global; Key Group = REPORTS, Layer = Environment Specific.
--    Keys: SRRS_ENDPOINT_URL, REPORT_SERVICE_URL  → must point at this env's ReportServer (…/ReportExecution2005.asmx)

-- H. Code-table grid definition pointing at the wrong table (§11)
--    For the failing column (e.g. ST_CD on table 32026), confirm the grid definition's Code Table id
--    matches the intended lookup table (2026 FA Location Codes) — fixed via the grid definition screen (24-00992353).
```

---

## 16. Expected-Behavior / User-Education FAQ

~47 Training + ~31 Customer-Error cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| "Can't approve / batch in Could-Not-Post / POSTWKFL glitch" | Usually **stale workflow locks** (release per KB, §4) **or** bad data the user entered — e.g. **DOI GL distributions not populated** (23-00878588, 22-00854576), a removed **Post Date** leaving batches in status 90 / post-pending (22-00668101), wrong process parameters (22-00668651), or a cleared autonumber row (24-00963774). Check data + locks before calling it a defect. | 23-00882822, 23-00878588, 22-00854576, 22-00668101, 22-00668651 |
| "How do I add 2026 months / a new fiscal year in SM006?" | Training — **Global company → enter # years → Auto Create → update screen to save** (§5) | 25-01063039 |
| "Database is read-only" running Schedule Definition in v16 | The **v16 QPECs were turned off** (sunset); change must be made in the supported version | 26-01084183 |
| "Forgot to select the Global indicator when creating company 930" / "new company setup issue" | Customer setup error — recreate/correct with the **Global indicator** set | 24-00983027, 24-00977842 |
| "Upstream won't launch / is there an outage?" | Usually **Citrix server down** (QCloud restarts it) — not a QCFS defect; RCA via the linked outage case | 25-01013843 |
| QPEC event-log **"Attempt to convert From Type 8 To Type 11 … QVariant.cpp\|692"** | **Informational only** — the named processes (e.g. ADP Invoice Upload / QCFS Import) are running as expected | 24-00974584, 24-00963256 |
| "QCFSIMPCYC / JIB Scheduler didn't pick up / locked" | Process working as expected, or **stale locks from a maintenance-window kill** — release locks and let it run (§4) | 24-00942364, 24-00948904, 26-01082993 |
| "JE Code Type question / formula screen / prior-period reporting / user guides" | Documentation/training — provide guidance, no fix | 23-00930776, 23-00920746, 23-00894442, 22-00612542 |
| "Inactivate a desk / object" fails | A **reference must be deleted** first | 25-01036563 |
| "Draft batches locked / can't unlock" after go-live | **Security group** for the workflow wasn't assigned at go-live — fix security, not a lock bug | 25-01023551 |
| Excel/M365 export or sign-in fails | **Citrix VDA / M365 license** (client-side), not QCFS (§6) | 23-00906350, 23-00907231 |

**Tell-tale it's user/expected:** a posting "failure" that's really **stale locks** or **un-entered DOI GL distributions / removed post date**; a "missing year" that just needs **SM006 Auto Create from Global**; a "company setup" miss because the **Global indicator** wasn't ticked; an "outage" that's **Citrix/QCloud**; or a QPEC **`QVariant.cpp|692`** message that is **informational**. Verify **locks + the user's data entry + the screen sequence** before treating it as a defect.

---

## 17. Key Screens, Processes & Repos

### Screens / processes
| Screen / process | Purpose | Notes |
|---|---|---|
| **SM006** | Business Unit Maintenance + fiscal periods | Operate from **Global company**; Auto Create years; update to save (§5) |
| **MF035** | Company / BU master | Create+link BA here; do **not** build bank accounts here (§5/§9) |
| **SM002 / SM021** | Autonumber defs / journal defs | Step 1–2 of bank-account setup (§9) |
| **BR037 / BR036 / AP048** | Physical bank acct / acct type / vendor check-run def | Step 3–5 of bank-account setup; BR036 needs Deposit Journal Def (§9) |
| **BA005 / BA030** | Business Associate / contacts | Autonumber via QARCH_TRAN_SEQ + AUTONUMBERINGMASTER; PUBBA Web adapter (§8) |
| **POSTWKFL** | Post workflow-approved AP/JE/batches to GL | Stale-lock prone; shares lock pool with QCFSIMPCYC (§4) |
| **QCFSIMPCYC** | Import cycle (revenue/JIB → QCFS) | If killed during maintenance, leaves stale locks blocking POSTWKFL (§4) |
| **QP043 / QP073 / QP074 / QP045** | Process & report launchers (incl. 1099, AP aging, manual post-workflow) | 1099 path = QSTG1099OVR (§12) |
| **GL016 / GL232** | Financial-statement header config (income statement) | Header misconfig → statement errors (§7) |
| **WF005** | Workflow query | Workflow visibility (§4) |
| Code tables (32xxx) + **grid definitions** | Lookup metadata | Wrong Code-Table id hides mandatory columns (§11) |

### Repos (confirmed via ADO repo list)
Core (product) repos:
- **`Quorum.Upstream.QCFS.Database`**, **`Quorum.Upstream.QCFS.ClassicGUI`**, **`Quorum.Upstream.QCFS.Application.MiddleTier`**, **`Quorum.Upstream.QCFS.Application.Web`**, **`Quorum.Upstream.QCFS.Batch`**, **`Quorum.Upstream.QCFS.ReleaseNotes`** — the QCFS financial core (SM006/MF035/POSTWKFL/bank/BA logic, screens, posting batch).
- **`Quorum.QFC.*`** — the **shared QFC framework** (Maintenance App, Workflow engine `Quorum.QFC.Workflow`, QPEC, Reporting `Quorum.QFC.Reporting`/`Quorum.QFC.Reports`, Metadata, codegen DAL/BL — the `Quorum.QCFS.DAL`/`Quorum.QCFS.BL` namespaces in stack traces live on top of `Quorum.QFC.Data.CodeGenImpl`).
- **`Quorum.Upstream.QCA.*`** (JIB/cost allocation — POMERGEJIB, JIB group codes), **`Quorum.Upstream.QRA.*`** (revenue), **`Quorum.Upstream.QDO.*`** (division order), **`Quorum.Upstream.Shared.*`**, **`Quorum.Upstream.Reports`**.
- Per-client overrides: **`<CLIENT>.Upstream.QCFS.Database`**, **`<CLIENT>.Upstream.QCA.Database`**, **`<CLIENT>.Upstream.Metadata`**, **`<CLIENT>.Upstream.Reports`**, **`<CLIENT>.Upstream.ESuite.*`** (e.g. APH, AES, AEL, APA, ARS). **Check the client repo/metadata first** — many fixes are client-specific (report paths, custom reports like the EQT bank-rec, autonumber seeds, period scripts).

---

## 18. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A **posting step** fails from code, not data/locks: Web-vs-Classic POSTWKFL parity (#1755621), "Nullable object" / CE (#1769179), 2022.04 Invalid Syntax (#1760237), Account-Balance deadlock (#1742965), scheduler not firing POSTWKFL (#1728471).
- A **calculation/import** is provably wrong on correct input: AFE concurrent-import **delete-scope** wipe of cost centers (24-00983364), SM006 **open-transaction-on-exception** FK/blocking (25-01014730 → 2022.04 May-2025 hotfix), LOS Gross revenue (24-00938781 → Mar-2024 hotfix), ARR005 duplicate lines (22-00669761).
- A **report** is structurally broken: missing join predicate (25-01012020), missing index on a custom/EQT report (24-00965148 → Patch 17), BA Core Financials tab (24-00989199).
- Provide: the **process name + Process Queue / batch id + exact SQL Server error**, client + BU + period, the screen/report, and a repro. Confirm fix availability in `Quorum.Upstream.QCFS.ReleaseNotes` (or `Quorum.QFC.ReleaseNotes`) and the linked hotfix/patch.

**Handle as Configuration / Cloud Ops when:**
- **SM006 period** creation (Global → Auto Create → save), BU-missing-from-picklist (link BA + add-BU script), company-code fixes (24-00951936, 24-00968561, 25-01063039).
- **Report paths / SSRS endpoints / instances-per-QPEC** after a refresh — re-run post-refresh path scripts, set `REPORTS` global keys, match QPEC instances to PRD (26-01101171, 25-01049564, 25-01042000).
- **Bank-account setup** via SM002→SM021→BR037→BR036→AP048 (not MF035); BR036 Deposit Journal Def (25-01009852, 22-00853542).
- **BA autonumber** reseed (QARCH_TRAN_SEQ / AUTONUMBERINGMASTER) + PUBBA adapter; BA↔ESuite API URL override (25-01023079, 24-00963774, 24-00969356).
- **JIB** JIB-Based flag / GL group-code mapping; **code-table grid-definition** id; **metadata masks** (26-01066978, 25-01008678, 24-00992353, 24-00975935).
- **1099** path (QSTG1099OVR; BA_ADDRESS_1099) (25-01062066, 25-01041723).

**Operational (release locks) first — no code:** POSTWKFL / QCFSIMPCYC / AFE_IMPORT "stuck / locked / Could-Not-Post" after a maintenance window — **release the stale locks** per the KB and rerun; only escalate if it recurs with no stale lock present (25-01021798, 24-00948904, 24-00960174, 23-00890511, 24-00947529).

**Handle as Training / Expected behavior (no fix):** see §16 — SM006 Auto-Create, Global-indicator misses, un-entered DOI GL distributions, Citrix/QCloud "outages," and the informational `QVariant.cpp|692` QPEC message. Verify **locks + user data entry + screen sequence** before treating as a defect.

---

*Skill created: 2026-06-14.*
*Based on: 479 closed QCFS Master Data / Workflow / Ad Hoc Reporting SF cases — 66 actionable (Software Defect 30 + Application Configuration 34 + ChangeConfig 2) mined for fix recipes, plus ~45 Training/Customer-Error cases for the FAQ. ADO work items #1769179, #1760237, #1755621, #1728471, #1742965, #1716612/#1715938, #1618264, #1734039, #1773563, #1778306, #1749934/#1790222.*
*Companion: QRA (revenue), QCA (JIB/cost allocation), QDO (division order) QCFS/Upstream skills; REPO inventory under Quorum.Upstream.QCFS.* / Quorum.QFC.* / <CLIENT>.Upstream.*.*
