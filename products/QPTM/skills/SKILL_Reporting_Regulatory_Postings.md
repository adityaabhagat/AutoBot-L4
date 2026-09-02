# SKILL: QPTM Reporting, Informational Postings & Regulatory Reporting Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-01 | **Product:** QPTM (My Quorum Gas Pipeline)
**Scope:** Canned/registered reports (run/launch/access/email/scheduling), invoice & imbalance & penalty report data (IN##, BLR##, ALR##), FERC regulatory reporting (RR30/549D, Index of Customers, NAESB postings), Informational Postings / EBB publication (IPWS — OAC, Unsubscribed Capacity, Transactional Reporting, IOC, Tariff, Notices), audit logging / access, and system notifications / event-detector email.
**Companion skills:** report *data* that is really an allocation/billing/contract calculation problem lives in **SKILL_Allocations.md / SKILL_Billing.md / SKILL_Contracts.md**; nom-error reports (NN12) in **SKILL_Nominations.md §12**; EDI in **SKILL_EDI_Troubleshooting.md**. Cross-references noted inline — do not duplicate.

> **Evidence base:** ~1,470 closed cases across categories Reporting, Informational Postings, Regulatory Reporting, Logging, Compliance, Notifications (`Product_list__c = 'My Quorum Gas Pipeline'`). Actionable root causes mined: **Application Configuration (~138), Software Defect (~127), Customer Error (~43), Training (~74)**. Each cluster below cites the **source Case_Category** and a real SF case # and/or ADO work item. Where a claim is config vs defect, that is from the case's `Root_Cause__c`.

---

## TABLE OF CONTENTS

1. [Quick Triage Checklist](#1-quick-triage-checklist)
2. [Concepts: Reports vs Postings vs Notices](#2-concepts-reports-vs-postings-vs-notices)
3. [Symptom → Root-Cause Matrix](#3-symptom--root-cause-matrix)
4. [Cluster A — Report Run / Launch / Access / Favorites](#4-cluster-a--report-run--launch--access--favorites)
5. [Cluster B — Report Email & Scheduling Delivery (QRPTLAUNCH / QEMAIL / Event Detectors)](#5-cluster-b--report-email--scheduling-delivery)
6. [Cluster C — Invoice / Imbalance / Penalty / Overrun Report Data (IN##, BLR##, ALR##)](#6-cluster-c--invoice--imbalance--penalty--overrun-report-data)
7. [Cluster D — FERC Regulatory Reporting (RR30 / 549D, Index of Customers)](#7-cluster-d--ferc-regulatory-reporting)
8. [Cluster E — Informational Postings / IPWS / EBB (OAC, Unsubscribed, Transactional Reporting, Tariff, LDD)](#8-cluster-e--informational-postings--ipws--ebb)
9. [Cluster F — Notices & System Notifications](#9-cluster-f--notices--system-notifications)
10. [Cluster G — Logging / Access / Audit](#10-cluster-g--logging--access--audit)
11. [Key Batch Processes](#11-key-batch-processes)
12. [Key Code Files & Repos](#12-key-code-files--repos)
13. [Database Tables Reference](#13-database-tables-reference)
14. [Diagnostic SQL Queries](#14-diagnostic-sql-queries)
15. [Known Historical ADO Bugs](#15-known-historical-ado-bugs)
16. [Expected Behavior / User Education](#16-expected-behavior--user-education)
17. [Escalation Decision Tree](#17-escalation-decision-tree)

---

## 1. Quick Triage Checklist

```
[ ] 1. What EXACTLY broke — a report (run/launch/data), an IPWS/EBB posting, a notice/email, or access/logging?
[ ] 2. Report ID / acronym? (e.g. RR30, CAX15, IN51, IN20, IN40, BLR_62, ALR_24, ALRX18, K15, NN49, IOC, OAC, IPWS-Transactional)
[ ] 3. Which TSP_NO / pipeline? (postings & FERC reports are per-TSP)
[ ] 4. Where did it fail — Report Viewer screen, scheduled email (QRPTLAUNCH/QEMAIL), an EBB batch (CWINDXCUST/CWUNSUBCAP/CWFIRMTRAN), or IPWS site?
[ ] 5. Internal or External (shipper) user? (many report-access bugs are External-only)
[ ] 6. Web (myQuorum) or Classic (Citrix)? Several defects are Web-only or Classic-only.
[ ] 7. "Won't run / errors" vs "runs but data wrong" vs "runs but not delivered"? — drives the cluster.
[ ] 8. One-off or recurring (every cycle / nightly batch)? Recurring batch = process/config, not data.
[ ] 9. QPTM version / recent hotfix? (many reporting regressions are version- or patch-gated: 2022.04, 2023.04, 2024.04, 2025.04, 2025.10)
[ ] 10. Is there a regulatory/filing deadline (FERC 549D quarter, IOC monthly)? → prioritize.
```

### Where does the issue live?
| Entry point / phrase | Cluster | First place to look |
|---|---|---|
| "report fails / errors / won't launch / can't access" | §4 Run/Launch/Access | Report Viewer; `QARCH_CTRL_PROCESS_PARAM`; user security group |
| "report not emailed / not received / scheduled job failed" | §5 Email/Schedule | QRPTLAUNCH / QEMAIL process log; event detector recipients |
| "IN##/BLR##/ALR## numbers are wrong" | §6 Invoice/Imbalance | report-backing table + underlying alloc/billing data |
| "RR30 / 549D / FERC / Index of Customers wrong" | §7 FERC | `RRRPTS_30_FERC_FORM_549D`; IOC XML export |
| "IPWS / EBB / OAC / Unsubscribed / Transactional not posting" | §8 Postings | CW* posting batch + IPWS import log |
| "notice / email / event detector" | §9 Notices | Notice Posting screen; event detector config |
| "can't log in / app tile missing / audit" | §10 Logging | access/store-front config (often platform) |

---

## 2. Concepts: Reports vs Postings vs Notices

QPTM produces three distinct things people loosely call "reports." Correctly classifying the request is half the triage:

- **Registered/canned Reports** — run on demand or on a schedule from the Report Viewer. Identified by a **Report ID** (e.g. `RPT_IN51`, `RPT_RR30`, `RPT_CAX15`, `RPT_ALRX18`, `RPT_K15`). Each has registered parameters and a backing SQL/table. Delivered to screen, file (SFTP), or email. Config lives in report metadata + `QARCH_CTRL_PROCESS_PARAM`. (Reporting category.)
- **Informational Postings / EBB (IPWS)** — NAESB-mandated public website data (the "Informational Postings Website"). Populated by **CW\* batch processes** that calculate and **export XML/flat files** which IPWS then **imports**. Examples: Operationally Available Capacity (OAC), Unsubscribed Capacity, Transactional Reporting (Firm/Interruptible), Index of Customers (IOC), Location Data Download (LDD), Gas Quality, Tariff. (Informational Postings / Compliance categories.)
- **Notices / Notifications** — operational/critical/non-critical notices posted to IPWS and/or emailed to shippers; plus **event-detector** driven system emails (cut reports, BA entity, etc.). (Notifications category.)

**Posting data flow (memorize this — it localizes 80% of IPWS cases):**
```
[QPTM data] --CW* batch (calc + write XML to file path)--> [XML/flat file on SFTP/share]
    --> [IPWS import job reads the file] --> [IPWS website / download link]
```
A posting can break at THREE points: (1) the **calc/export batch** (wrong/zero data, missing column → import rejects it), (2) the **file path / SFTP** (file never lands), or (3) the **IPWS import / site** (file lands but site stale/down). Always ask "did the XML generate, and does it contain the data?" before blaming IPWS.

---

## 3. Symptom → Root-Cause Matrix

| Symptom (message / behavior) | Most common root cause | Fix type | Cluster | Source category · Evidence |
|---|---|---|---|---|
| Report Viewer throws error / "weird error" / won't open | Corrupt/changed registered params or post-hotfix regression | Config / hotfix | §4 | Reporting · 26-01087720, 26-01086581, 25-01056242 |
| Report missing from the reports list / report-type dropdown | Report type not registered for the build/security group | Config (register report type) | §4 | Reporting · 25-01034708 (IN_57), 25-01029305, 25-00999136, 25-01021868 |
| External shipper can't run / can't favorite reports | Security group / report-type x-ref missing for External | Config | §4 | Reporting · 25-00996569 (ALRX18), 24-00965634, 25-01034224, 22-00821104 |
| Report runs but is **not emailed / not received** | QRPTLAUNCH/QEMAIL step failing, or event-detector recipient list | Config (process step / recipients) | §5 | Reg.Reporting · 23-00913987, 23-00914714, 23-00921160; Reporting 25-01044367, 26-01064286 |
| IN##/imbalance/penalty **numbers wrong** | Report SQL / calc defect OR upstream alloc/billing data | Code fix or data | §6 | Reporting · 22-00814542 (IN63), 24-00966790 (IN40), 24-00966785 (IN41) |
| **RR30 / FERC 549D** wrong totals / unique-constraint / location lookup | Report SQL defect (column summing, location join) | Code fix | §7 | Reg.Reporting · ADO #1699870, #1670534, 22-00536972, 23-00926590 |
| **Index of Customers** XML wrong / multiple files / not posting / AMA-or-BA# shown | IOC export (CWINDXCUST) config/defect | Config or code | §7/§8 | Compliance · 24-00936650, 24-00974923, 22-00671633, 22-00588124; ADO #1772304 |
| **Unsubscribed Capacity** wrong/zero / IPWS import "Unable to enforce constants" | CWUNSUBCAP export calc or missing column (TSP_NM) | Code fix | §8 | Compliance · ADO #1668756, #1680441, 24-00971312 |
| **OAC / Transactional Reporting** not posting / doubling / suppressed loc showing | CW* posting batch config/defect | Config or code | §8 | Inf.Postings · 24-00941209, 22-00818877, 24-00954335, 22-00703130 |
| IPWS site **down / slow / stale** | IPWS middle-tier / connection-link / perf | Platform/restart | §8 | Inf.Postings · 22-00603367, 22-00609188, 23-00889303, 22-00832920 |
| **Notice** email shows HTML tags / wrong sender / not sent / "?" chars | Notice template / encoding / "do not send email" defect | Code or config | §9 | Notifications · 23-00898064, 22-00808446, 23-00909914, 24-00937878 |
| Notice **type/subtype missing** from select list after upgrade | Notice-type metadata not migrated | Config | §9 | Notifications · 25-01030338 (NON), 24-00946449, 24-00958185 |
| Event-detector contact added but **not receiving** | Recipient resolution / event-detector config | Config | §9 | Notifications · 26-01067561, 26-01080390 |
| App tile / Classic app missing, can't log in | Store-front / platform access (often not a product defect) | Platform | §10 | Logging · 26-01067561, 24-00961585, 25-01042377 |

---

## 4. Cluster A — Report Run / Launch / Access / Favorites
*Source category: Reporting (AppConfig 69, Software Defect 32 — the largest actionable bucket).*

The single highest-volume reporting cluster. Three recurring failure modes:

**A1. Report errors / won't launch.** Often a post-hotfix/upgrade regression or a corrupt registered parameter. Representative: 26-01087720 / 26-01086581 ("Report Viewer Screen errors", SOC), 25-01056242 (UTILSCHNOT & CAX15 *failing in prod after latest hotfix* — config), 25-01039733 (reports not launching after a refresh), 25-01032943 (Citrix launch fails for one user), 23-00892544 ("Issues running a report in Web"). For older builds the "report launch popup download not showing up" is a known Web defect (22-00598048, 22-00599362).

**A2. Report missing from the list / report-type dropdown.** The report type isn't registered for that build or that user's security context. Representative: 25-01034708 (IN_57 missing), 25-01029305 ([2025.04] canned reports missing in new build — Software Defect), 25-00999136 ([2024.04] unable to see some report types), 25-01021868 (NMGC report type missing from QCM), 25-01016472 (Process Type missing in Classic only). Fix = register the report/process type and verify the security-group x-ref.

**A3. External-shipper access & favorites.** External users frequently can't run or can't *save favorites*. Representative: 25-00996569 (external can't run ALRX18), 24-00965634 (external operator can't access 5.1/5.2/5.3 penalty reports), 24-00980816 (report error on RALRX04_EX / RPT_ALRX18 for some external users), 25-01034224 (external shippers can't save favorites — AppConfig), 22-00821104 (can't favorite reports), 24-00948674 (external reports not executing). Almost always a **security group / report-type cross-reference** config gap for the External user class.

### Triage steps
1. Get the exact **Report ID** and whether it's Web or Classic, Internal or External.
2. Reproduce: run the report from the Report Viewer with the client's exact parameters.
3. If "missing": confirm the **report/process type is registered** for the build and mapped to the user's security group.
4. If "errors": check whether it followed a **hotfix/upgrade** (A1 pattern) — compare working env vs broken env params (`QARCH_CTRL_PROCESS_PARAM`).
5. Check the process-execution log for the failing step.

---

## 5. Cluster B — Report Email & Scheduling Delivery
*Source category: Regulatory Reporting + Reporting (Application Configuration).*

Reports run fine but never reach the recipient. The delivery chain is **scheduled job → QRPTLAUNCH (render/launch) → QEMAIL (send) → SFTP/email**. Failures cluster on the QRPTLAUNCH/QEMAIL steps and on **event-detector recipient lists**.

| Issue | Root cause | Fix | Case (category) |
|---|---|---|---|
| Emailing reports fails on **QRPTLAUNCH** step, email never sends | Process-step / template config | Config | 23-00913987, 23-00914714 (Reg.Reporting, VGP) |
| "Reports not being emailed" generally | Schedule/recipient config | Config | 23-00913653 (Reg.Reporting) |
| Shippers (GID) **stopped receiving cut reports** (event detector 11014) | Event-detector recipient list / contact resolution | Config | 23-00921160 (Reg.Reporting, SWN) |
| Users not receiving QQM Complex Meter reports since a date | Schedule/recipient or QQM delivery config | Config | 26-01064286 (Reporting) |
| Email reports from Reports screen results in error | Web email-from-screen defect | Config/code | 24-00968254 (MGD, Reporting) |
| UAT email notifications not generated as expected | Environment email config | Config | 24-00991084 (Reporting) |
| QPEC_Scheduler processes not working as expected | Scheduler config | Config | 25-01050380 (Reporting) |
| `QEMAIL` process receiving errors | QEMAIL config / SMTP | Config | 22-00592334 (Inf.Postings, OH) |

### Triage steps
1. Did the report **render**? Check the QRPTLAUNCH step in the process-execution log. If it failed there, the email never had an attachment (see also 24-00962570 "blank attachments", 24-00951456 BLRX_00 runs but can't open).
2. Did **QEMAIL** run and what recipients did it resolve? For "specific users stopped receiving," check the **event detector** recipient list and whether the contact is still active/linked (cf. 22-00712253 CWSHIPEXP including inactive contacts).
3. Confirm **SFTP** credentials/path if delivery is file-based (26-01084228 SFTP password, 25-01022361 SFTP connection errors, 24-00982987 IOC TXT not generating in SFTP).

---

## 6. Cluster C — Invoice / Imbalance / Penalty / Overrun Report Data
*Source category: Reporting + Regulatory Reporting (Software Defect-heavy).*

These are the "report runs but the numbers are wrong" cases. The report **family** localizes the area: **IN##** = imbalance/statement reports, **BLR##/RPTBLRX_##** = billing/penalty, **ALR##** = allocation reports, **5.1/5.2/5.3** = penalty statements. Decide first whether the defect is in the **report SQL/presentation** or in the **upstream allocation/billing data** (if upstream, route to SKILL_Allocations / SKILL_Billing).

| Report | Issue | Root cause | Case |
|---|---|---|---|
| IN63 | Imbalance percent not calculated correctly; headings cut off | Report calc/format defect | 22-00814542, 22-00814365 |
| IN40 | Gross Receipt row shows Net Receipt data; daily-tier execution | Report SQL defect | 24-00966790, 24-00954599 |
| IN41 | PTR not included in imbalance calc | Report calc defect | 24-00966785 |
| IN51 | Agreement Balancing — Alloc PTR Qty not carried to Net Alloc Qty (recurring, 3 cases for same K) | Report calc defect | 25-01003643, 25-01003750, 24-00985629, 24-00972265 |
| IN20 / INX20 | Cumulative Imbalance — Beg Imbal column wrong; BP name truncation | Report SQL/format defect | 24-00972263, 24-00969923, 24-00945449 |
| Overrun / Unauth. Overrun | Missing Scheduled/Delivered Alloc/MDQ for PPA; AOR/AORP/UORP presentation | Report presentation defect | 24-00984399, 24-00989485, 24-00978852 |
| BLR_62 / RPTBLRX_62 | Scheduling Imbalance Penalties — PPA reversal/restate presentation; external picklist/loc hide | Code/config | 24-00968417, 24-00968786 |
| 5.1 Penalty | Billing determinant too high (SPPC); external access | Code/config | 24-00938056, 24-00965634 |
| ALR_24 | Proc K's not broken out correctly (reopened); field spacing | Code fix | 24-00973759, 25-01014338 |
| Pool Balance | Not showing buy/sell mismatches; registered-SQL error (`m_Ins_SQLID_NN03_POOL`) | Code fix | 24-00944521, 22-00530955 |
| Daily imbalance | BTU factor not updating on daily imbalance report | Code fix | 24-00977243 |

### Triage steps
1. Pull the **report's backing SQL/table** (registered SQL ID is in the error for "Error in registered SQL" cases).
2. Reproduce with the client's parameters; compare the report figure against the **source allocation/billing table** for the same K/loc/gas-day. If the source data is wrong → it's an Allocations/Billing case, not a reporting bug.
3. If source data is right but the report is wrong → **report SQL or presentation defect** → ADO bug.

---

## 7. Cluster D — FERC Regulatory Reporting
*Source category: Regulatory Reporting + Compliance.*

### D1. RR30 — FERC Form 549D
Quarterly FERC filing. Recurring defects in **column summing** and **location-name lookup**, plus a unique-constraint failure that halts the run.

- **#1699870 (Bug, Closed)** — case **24-00985687 (DTE)**: RR30 *"not picking up all rates when summing up column 62 `CTR_USAGE_WD_QTY`"* — field 62 was off by the **TOC SWOVW** rate value; validated against IN58 Summary Storage Contract. The report reads table **`RRRPTS_30_FERC_FORM_549D`**.
- **#1670534 (Task, Closed)** — DTE RR30 "Report Fixes" umbrella covering cases 22-00823581, 23-00928605, 22-00831312, **23-00926590** (location-name lookup fix). Also **#1697284** (Column Y begin-date / grid type).
- **22-00536972** — "RR30 FERC 549D stopping with Unique Constraint Error" (run aborts).
- **24-00985687 / RR30 Park Contract Withdrawal Volume** issue (also surfaced as a Reporting AppConfig case).

**Triage:** run RR30 for the filing quarter; for a wrong field, find the contributing **rate/TOC** (e.g. SWOVW) and confirm whether the report SQL is summing all applicable rate components into the column. For unique-constraint, check for duplicate source rows feeding `RRRPTS_30_FERC_FORM_549D`.

### D2. Index of Customers (IOC)
NAESB monthly posting. Two failure shapes: **XML generation defects** and **identity/footnote/content errors**.

| Issue | Root cause | Case / ADO |
|---|---|---|
| IOC export generates **all previous XML files** + new file (multiple files to FTP) | CWINDXCUST file-cleanup defect | 24-00977062, 22-00675973, 22-00615030 |
| IOC XML **not updating** to new report date / shows prior month | CWINDXCUST run/date config | 23-00876744, 25-01046198, 25-01045971 (after CWINDXCUST + GBGIOCIMP) |
| **Missing Agent / TSP info** in IOC XML; staging failed | CWINDXCUST not generating agent/TSP — fixed | **ADO #1772304/#1774246** (Lead): *update CWINDXCUST to generate agent and TSP info in the XML*; 24-00936650, 22-00676026 |
| IOC shows **AMA ID / BA #** that it should not | Identity-field defect | 22-00671633, 22-00588124 |
| Negotiated Rate indicator on IOC wrong (NO vs YES) | Contract/IOC config | 26-01090698, 22-00675961 |
| IOC footnotes missing / multiple-footnote XML not updating | IOC footnote config/defect | 25-01017307, 24-00974923 |
| IOC download link errors / wrong file | IPWS download / staging | 23-00909214, 25-01062791, 25-01027710 (IOC_1000_DOWN) |

**Triage:** confirm **CWINDXCUST** ran and produced the XML; open the XML and verify agent/TSP/footnote content and the report date; then confirm the IPWS import (e.g. GBGIOCIMP) picked it up. The multiple-files-to-FTP issue is a known cleanup defect — verify the export file path isn't accumulating stale files.

---

## 8. Cluster E — Informational Postings / IPWS / EBB
*Source category: Informational Postings (Software Defect 50, AppConfig 21) + Compliance.*

Apply the **§2 three-point posting flow**. The CW\* batch calculates and writes a file; IPWS imports it. Most "IPWS is wrong" cases are actually **export-batch** problems.

### E1. Unsubscribed Capacity (CWUNSUBCAP / CWALLUNCAP / CAALLUNCAP)
- **#1668756 (Bug, Closed)** — *"Unsubscribed Capacity export missing `TSP_NM`, causing IPWS import to fail with 'Unable to enforce constants ... Column TspNm does not allow DBNull'."* The QPTM export wasn't writing TSP_NM, so the IPWS import rejected the whole dataset. Repro: run CAS/CWALLUNCAP then CAW/CWUNSUBCAP, inspect XML for missing TSP_NM.
- **#1680441 (Bug, Closed)** — case **24-00971317 (GBG/MGD)**: *Unsubscribed Capacity incorrectly calculating* — the process exported the **Location Maintenance capacity** instead of **calculating unsubscribed = location capacity − contract-location capacity in use** (firm MDQ subtracted from available capacity). Expected all delivery locations = 0 unsubscribed.
- Related: 24-00956256 (NAESB Unsubscribed test), 24-00971312 (CAALLUNCAP & CWUNSUBCAP ran but didn't post), 23-00913725 (wrong volumes on TCPL IPWS).

### E2. Operationally Available Capacity (OAC) & Transactional Reporting (CWFIRMTRAN / Firm & Interruptible)
| Issue | Root cause | Case |
|---|---|---|
| OAC locations showing that should be **suppressed**; loc not showing | OAC location-suppression config/defect | 24-00941209 |
| OAC populating **ZERO for TSQ** post-cutover; OAC blank in IPWS | OAC export defect/config | 22-00818877, 23-00913886 |
| Total Scheduled Qty **doubling** for rolled-up location groups when process run twice | Re-run accumulation defect | 24-00954335 |
| CWOPAVAIL / Segment Unsubscribed running excessively long / erroring | Posting batch perf/defect | 22-00808360, 22-00630734 |
| Transactional Reporting (Firm/Interruptible) **not posting** / missing data | CW*TRAN export config/defect | 22-00675980, 22-00703130, 22-00819857, 24-00966867 |
| Transactional Reporting **won't post ACA** / no rate or qty | Posting content defect/config | 24-00982506, 24-00986338 |
| Capacity Release **duplicating** data in Transactional Reporting | Dedup defect — fixed | **ADO #1795060** (HPE, 25-01018583); 25-00995840 (PCC/RCC multiple lines) |
| Bidirectional / segment-level views on IPWS transactional exports | View/segment config | 25-01052863, 25-01052954, 25-01051010 (OkTex) |

> **`CWRPTS_FT_POSTING`** is the backing table for Firm Transactional Reporting posting (confirmed in QPTM schema; clients keep a correction proc e.g. `APL_SP_CWRPTS_FT_POSTING_CORRECTION`). History availability of this table was asked in 26-01064681 (Training).

### E3. IPWS site down / performance / middle-tier
A large 2022-era cluster of **IPWS outage / restart / connection-link** cases — these are usually **platform/infra**, resolved by a middle-tier restart, not a product code change: 22-00603367, 22-00603368, 22-00609188, 22-00609190, 22-00615051/54/55/56, 23-00889303 (BBT PRD down), 23-00924135 (Gator Express down), 22-00832920 (RCA: IPWS MT did not restart gracefully), 22-00679613 (HPE IPWS down). **Performance:** 23-00908933 (records introduced between CWGASQUAL runs), 22-00808360. Treat "IPWS down" as infra first; escalate to Cloud Ops/Platform.

### E4. Tariff / Location Data Download (LDD) / Gas Quality
- LDD posted to wrong TSP / missing location: 22-00676018, 23-00914712, 23-00901907.
- Tariff sheet/section/index issues: 24-00937681, 22-00580689, 22-00559228, 24-00986230 (double links).
- Gas Quality not updating: 23-00919415, 24-00995623, 22-00675997.
- Special characters become "upside-down ?" in postings/notices — **encoding** defect: 24-00937878, 25-01014755.

---

## 9. Cluster F — Notices & System Notifications
*Source category: Notifications (AppConfig 21, Software Defect 2) + some Inf.Postings.*

Two sub-areas: **Notice Posting** (operational/critical/non-critical notices to IPWS + email) and **event-detector** system emails.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Notice email shows **HTML tags** in a field (e.g. Notice Ending Date/Time) | Notice template encoding defect | Code | 23-00898064 (OH) |
| Notice **"do not send email" option not working** | Notice-posting flag defect | Code | 22-00808446 (OH, TDD1118) |
| **Recall notices not sent** | Notice trigger defect | Code | 23-00909914 |
| Notice subject line driven by **default TSP** on dashboard (wrong) | Subject-resolution defect | Code | 22-00598181 |
| Notice **type/subtype missing** from select list (esp. after 2023.04/2025.04 upgrade) | Notice-type metadata not migrated | Config | 25-01030338 (NON), 24-00946449, 24-00958185, 25-01042526, 25-01048304 |
| Posted notice **stuck** / appears after end date | Notice status/expiry defect | Config/code | 24-00968085, 24-00980360 |
| Notice email **wrong sender / header reverted** | Email header config | Config | 24-00984083, 24-00946062, 23-00912769 |
| **Duplicated** notifications | Trigger/dedup config | Config | 24-00948120 |
| Event-detector **contact added but not receiving**; permissions for event-detector access | Recipient resolution / event-detector security config | Config | 26-01067561, 26-01080390, 26-01084250, 26-01067520 |
| Email notifications **not generated** (SOC) | Event-detector / email config | Config | 26-01091459, 26-01089517 |
| Customer notification **not created** | Notification trigger defect | Code | 22-00515563 |

**Triage:** for "not sent/received," confirm (1) the **notice/event was posted** (Notice Posting screen / event log), (2) the **recipient list** resolves to active contacts with email, (3) the **QEMAIL** step ran. For "type/subtype missing," it's almost always upgrade-migrated metadata — re-add the notice (sub)type config. For HTML/encoding artifacts, it's a template defect → ADO bug.

---

## 10. Cluster G — Logging / Access / Audit
*Source category: Logging — dominated by **User Administration Request (272)**; actionable Software Defect 6, AppConfig 5.*

The Logging category is overwhelmingly **access provisioning / user-admin** (route those to SKILL_Security_UserAdmin.md), plus a thin layer of genuine defects/infra:
- App tiles / Classic apps **missing** at login: 26-01067561 (DTE Classic apps missing), 24-00961585 (tiles not in login.myquorumcloud.com), 25-01042377 (users can't access Classic) — store-front / entitlement, usually **platform**.
- QPTM Web server **connection errors / outage**: 25-01051789, 25-01051694, 25-01051713 (Critical) — infra, escalate to Platform/Cloud Ops.
- FTP/SQL-user/auth provisioning: 24-00980688 (FTP auth), 24-00964089 (new SQL user), 25-01062389 (AD Manager license expiring) — Cloud Ops requests.
- Email Notification **Logs** "show unsent items only": 22-00598102 (UI filter defect) — this is the closest thing to true audit-log tooling in scope.

**Takeaway:** if a "Logging" case is really "give me/this user access," it's User Admin, not a defect. Genuine product work here is rare.

---

## 11. Key Batch Processes
(Process IDs attested across the mined cases — these are the workhorses of postings/reports.)

| Process | Purpose | Common failure (case) |
|---|---|---|
| `QRPTLAUNCH` | Render/launch a registered report for delivery | Email step fails, report not sent (23-00913987) |
| `QEMAIL` | Send rendered report/notice emails | Errors in env, no send (22-00592334) |
| `CWINDXCUST` | Generate **Index of Customers** XML | Missing agent/TSP info (#1772304); multiple files (24-00977062); stale date (23-00876744) |
| `GBGIOCIMP` | IPWS-side IOC import | IOC not updating after import (25-01045971) |
| `CWUNSUBCAP` / `CWUNSUBCAP2` | Export **Unsubscribed Capacity** to IPWS | Missing TSP_NM → import fails (#1668756) |
| `CAALLUNCAP` / `CWALLUNCAP` | Calculate unsubscribed capacity (source for CWUNSUBCAP) | Wrong calc (#1680441); didn't post (24-00971312) |
| `CWOPAVAIL` | Export **Operationally Available Capacity** | Runs excessively long (22-00808360); zero TSQ (22-00818877) |
| `CWFIRMTRAN` / `CWCAPTRAN` | Firm / Capacity-Release **Transactional Reporting** export | Can't resolve contract eff date (23-00912391); no data (25-01017542) |
| `CWGASQUAL` | Gas Quality posting | Records introduced between runs / perf (23-00908933) |
| `CWNTLYFIRM` / `CWNIGHTLY` | Nightly firm/posting roll-up | QPEC system errors (23-00878341) |
| `PALOCEXP` | Posting/allocation location export | Fails on REX (23-00936341); error (25-01017329) |
| `UTILSCHNOT` | Scheduled-notice utility | Failing in prod after hotfix (25-01056242) |
| `CWSHIPEXP` | Shipper List Extract | Includes inactive contacts (22-00712253) |

> When a posting/report batch "ran but didn't post," check the **process-execution log** for the step, then check the **export file path** and the **IPWS import log**.

---

## 12. Key Code Files & Repos
(Confirmed via ADO code search; report/posting logic is split between batch repos, the report metadata, and per-client DB.)

| Area | Repo / file | Notes |
|---|---|---|
| IOC Maintenance screen + ops | `Quorum.QPTM.AT` → `IndexOfCustomersMaintenanceScreenTests.cs`, `IndexOfCustomersMaintenancePageOperations.cs` | IOC screen behavior (also ADO #1801596 dirty-indicator) |
| Process/report parameters | `*.QPTM.Metadata` / `*.ESuite.Metadata` → `QARCH_CTRL_PROCESS_PARAM.json`, `QARCH_CTRL_GLOBAL_PROCESS_TYPE.json` | Registered report/process params & global process types (the "report type missing" fix) |
| Firm Transactional posting table + correction | `*.QPTM.Database` → `...QPTMSCR.sql` (defines `CWRPTS_FT_POSTING`); `APL.ESuite.Database/.../APL_SP_CWRPTS_FT_POSTING_CORRECTION.sql` | Backing table + a client correction proc pattern |
| FERC RR30 backing table | `RRRPTS_30_FERC_FORM_549D` (QPTM schema) | Read by RPT_RR30 (#1699870) |
| Event detector / queue constants | `Quorum.PGAS.Web` → `Utility/Util_Queue/QConstants.vb`; per-client `*.QPTM.Database` migrations referencing `EVENT_DETECTOR` | Event-detector wiring |
| Client report/notice overrides | `<CLIENT>.QPTM.Database` / `<CLIENT>.QPTM.Metadata` (e.g. APL, DTE, GBG, OkTex, VGP, HPE) | **Always check for a client override** of a report SQL or notice template before assuming base behavior |

> Reporting/posting fixes are predominantly **report-SQL / metadata / batch-calc** changes — **not** the cascade hard-delete .sql scripts seen in the Nominations skill. No verbatim deletion-style script attachments were found on the report/posting bugs reviewed (#1699870, #1670534, #1668756, #1680441, #1772304 carry design docs/walkthroughs, not data scripts). The one script *pattern* in scope is a **client posting-correction proc** (`*_SP_CWRPTS_FT_POSTING_CORRECTION`) used to repair Firm Transactional posting rows.

---

## 13. Database Tables Reference

| Table / object | Purpose |
|---|---|
| `RRRPTS_30_FERC_FORM_549D` | **RR30 FERC Form 549D** report backing table (column 62 `CTR_USAGE_WD_QTY`, 64 `CTR_USAGE_PAL_QTY`) |
| `CWRPTS_FT_POSTING` | **Firm Transactional Reporting** posting data (IPWS export source) |
| `QARCH_CTRL_PROCESS_PARAM` | Registered **report/process parameters** (drives "report type/parameter" issues) |
| `QARCH_CTRL_GLOBAL_PROCESS_TYPE` | Global **process/report type** registry (report missing from list) |
| `*` unsubscribed/OAC export staging | Populated by CWUNSUBCAP/CWOPAVAIL; consumed by IPWS import (`UnsubCapLocHdr` is the IPWS-side table that rejected DBNull TspNm in #1668756) |
| Allocation/billing source tables | Upstream of IN##/BLR##/ALR## — see SKILL_Allocations / SKILL_Billing |

> Table names beyond these were **not** assumed — for event-detector/notice backing tables, inspect the client's `*.QPTM.Database` migrations (code-searched `EVENT_DETECTOR` returns per-client migration scripts) rather than guessing a global name.

---

## 14. Diagnostic SQL Queries

> Reporting/posting cases turn on three questions: **(1) is the report/process registered & parameterized? (2) did the batch produce data/file? (3) is the source data correct?** These queries target those. Replace `<...>` placeholders.

### A. Is the report/process type registered & what are its params?
```sql
-- Registered process/report parameters (drives "report missing" / "wrong parameter" cases)
SELECT pp.PROCESS_ID, pp.PARAM_NM, pp.PARAM_VALUE, pp.PARAM_TYPE_CD, pp.SEQ_NO
FROM   QARCH_CTRL_PROCESS_PARAM pp
WHERE  pp.PROCESS_ID = '<REPORT_OR_PROCESS_ID>'   -- e.g. 'CWINDXCUST', 'RPT_RR30', 'CWUNSUBCAP'
ORDER  BY pp.SEQ_NO;

-- Global process/report type registry (is the report type even available for this build?)
SELECT gt.PROCESS_TYPE_CD, gt.PROCESS_TYPE_DESCR, gt.IS_ACTIVE
FROM   QARCH_CTRL_GLOBAL_PROCESS_TYPE gt
WHERE  gt.PROCESS_TYPE_CD LIKE '%<KEYWORD>%';
```

### B. RR30 / FERC 549D field validation (the #1699870 pattern)
```sql
-- Inspect the FERC 549D backing rows for a filing quarter / contract;
-- compare field 62 (withdrawal) vs 64 (PAL) and trace the rate components feeding col 62.
SELECT CTR_NO, RATE_SCHEDULE_CD, CTR_USAGE_WD_QTY /*field 62*/, CTR_USAGE_PAL_QTY /*field 64*/,
       BEG_DT, END_DT
FROM   RRRPTS_30_FERC_FORM_549D
WHERE  TSP_NO = <TSP_NO>
  AND  BEG_DT >= '<QTR_START>' AND END_DT <= '<QTR_END>'
  AND  CTR_NO IN ('<K1>','<K2>')          -- e.g. 04226-10
ORDER  BY CTR_NO, RATE_SCHEDULE_CD;
-- Red flag (#1699870): col 62 short by a specific rate (e.g. SWOVW) → report SQL not summing all WD rate components.
```

### C. Firm Transactional Reporting posting check (IPWS export source)
```sql
-- Did the posting batch write rows for the gas day(s) the client says are missing on IPWS?
SELECT TSP_NO, CTR_NO, RATE_SCHEDULE_CD, LOC_ID, GAS_DAY, POST_QTY, POST_RATE, POST_DT
FROM   CWRPTS_FT_POSTING
WHERE  TSP_NO = <TSP_NO>
  AND  GAS_DAY BETWEEN '<BEG_DAY>' AND '<END_DAY>'
ORDER  BY GAS_DAY, CTR_NO;
-- If rows are missing/zero here, the export batch (CWFIRMTRAN) is the problem, not IPWS.
-- Duplicate (CTR_NO, LOC_ID, GAS_DAY) rows → the CapRel-duplication defect (ADO #1795060).
```

### D. Process-execution log (did the batch run & which step failed?)
```sql
-- Generic process-run history. Exact log table varies by build; start from the Batch Process
-- Execution screen, or query the client's process-history table for the PROCESS_ID + run date.
-- Confirm: did CWINDXCUST / CWUNSUBCAP / CWOPAVAIL / QRPTLAUNCH complete, with errors, or not start?
SELECT PROCESS_ID, RUN_DT, STATUS_CD, ERROR_MSG, ROWS_PROCESSED
FROM   <PROCESS_HISTORY_TABLE>            -- confirm name in the client DB
WHERE  PROCESS_ID = '<PROCESS_ID>'
  AND  RUN_DT >= DATEADD(day,-3,GETDATE())
ORDER  BY RUN_DT DESC;
```

### E. Report email / event-detector recipient resolution
```sql
-- Why did a shipper stop receiving a scheduled report / cut report (23-00921160 pattern)?
-- Find the event detector and its recipient contacts; verify contacts are active with email.
-- Inspect the client's event-detector tables (code search 'EVENT_DETECTOR' in <CLIENT>.QPTM.Database
-- to find the exact table/columns for this build) and confirm:
--   * the event detector (e.g. 11014) is active
--   * the GID/contact is still linked and active (cf. CWSHIPEXP inactive-contact defect 22-00712253)
--   * the contact has a valid email address
```

---

## 15. Known Historical ADO Bugs

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case (category) |
|---|---|---|---|---|
| **#1699870** | Bug / **Closed** | DTE — RR30 FERC 549D not picking up all rates summing col 62 `CTR_USAGE_WD_QTY` (off by SWOVW) | §7 RR30 | 24-00985687 (Reg.Reporting) |
| **#1670534** | Task / **Closed** | DTE — RR30 549D Report Fixes (umbrella: 22-00823581, 23-00928605, 22-00831312, 23-00926590) | §7 RR30 | 22-00823581 / 23-00926590 (Reg.Reporting) |
| #1697284 | Task / Closed | DTE — RR30 Column Y begin-date / grid type | §7 RR30 | — |
| **#1668756** | Bug / **Closed** | Unsubscribed Capacity export missing `TSP_NM` → IPWS import "Unable to enforce constants" | §8 Unsub | (HPE) Inf.Postings |
| **#1680441** | Bug / **Closed** | GBG/MGD — Unsubscribed Capacity incorrectly calculating (exported Loc-Maint capacity instead of computing unsub) | §8 Unsub | 24-00971317 (Compliance) |
| **#1772304 / #1774246** | Task / **Closed** | Lead — update CWINDXCUST to generate **agent & TSP info** in IOC XML | §7 IOC | 24-00936650 (Compliance) |
| #1779000 | Task / Closed | Automation test for CWINDXCUST batch | §7 IOC | — |
| **#1795060** | Task / **Closed** | HPE — Transactional Reporting Capacity Release **duplicating** data | §8 Transactional | 25-01018583 (Compliance) |
| #1711191 | Feature / **Proposed** | Report OAC & unsubscribed capacity at **segment level** | §8 (enhancement) | (OkTex 25-01052954) |
| #1802081 | Feature / **Proposed** | Automated **incremental** IPWS Transactional Reporting for non-Quorum | §8 (enhancement) | 26-01095768 |

> Takeaway: FERC/posting defects are fixed via **report-SQL / batch-calc** code changes (RR30 column summing, Unsubscribed calc, IOC XML content, CapRel dedup). Segment-level OAC and incremental transactional reporting are **enhancement Features (Proposed)** — classify those as Enhancement Requests, not bugs.

---

## 16. Expected Behavior / User Education
*Source category: Training (~74) + Customer Error (~43) across the categories. Recognize these to avoid unnecessary code/config work.*

| Reported as | Reality | Case (category) |
|---|---|---|
| "Where's the SQL behind IN02 / report X?" | Documentation request — provide the registered SQL/spec | 25-01055578, 24-00964820 (Reporting) |
| "Is history available for `CWRPTS_FT_POSTING`?" | Education — table is current-state; no built-in history generation | 26-01064681 (Reporting) |
| "How do I schedule a report to email a user?" | Training — walk through Report scheduling | 25-01003171 (Reporting) |
| "Make a report available to a user who can't access it" | User-admin / security-group config, not a defect | 24-00979173 (Reporting), 24-00938119 (Inf.Postings) |
| "Refile historical Index of Customers" | Operational re-run request, not a bug | 26-01095434 (Compliance) |
| "IOC shows prior month right after posting" | Posting cadence / download cache — verify CWINDXCUST date, then re-download | 25-01046198 (Compliance) |
| "Report numbers differ from my other report" | Often two reports use different definitions (e.g. IN58 vs RR30) — explain the difference before assuming a defect | 24-00976025 (IN03/IN05 usage), 24-00985687 cross-check |
| "Remove a Transactional Reporting record from IPWS" | Operational data correction (posting-correction proc), not a code bug | 24-00957196 (Reporting) |
| "Add PDF download links to IPWS front page" | Configuration/setup request | 24-00957209 (Reporting) |
| "IPWS overview / how-to" | Documentation | 23-00894737 (Inf.Postings), 22-00592348 (OH) |

**Tell-tale it's education/expected:** the client is comparing two differently-defined reports, asking for the report's SQL/spec, asking to schedule/route a report, or requesting an operational re-run/correction — none of which is a product defect.

---

## 17. Escalation Decision Tree

```
Reporting / Postings / Notification case
│
├─ A report (has a Report ID like IN51, RR30, ALRX18, K15)?
│   ├─ Won't run / errors / missing from list?  (§4)
│   │   ├─ After a hotfix/upgrade? → config regression; compare params (QARCH_CTRL_PROCESS_PARAM) good vs bad env
│   │   ├─ Missing from list / external can't access? → register report type + fix security-group x-ref (CONFIG)
│   │   └─ Generic Web launch/popup defect? → known code defect, check version
│   ├─ Runs but NOT emailed/received?  (§5)
│   │   └─ Check QRPTLAUNCH render → QEMAIL send → recipient list / event detector / SFTP
│   └─ Runs but DATA wrong?  (§6/§7)
│       ├─ Compare report figure vs source alloc/billing table
│       │   ├─ Source data wrong → it's an Allocations/Billing case (other skill)
│       │   └─ Source right, report wrong → report-SQL/presentation DEFECT → ADO bug
│       └─ FERC RR30/549D or IOC? → §7 (RRRPTS_30_FERC_FORM_549D / CWINDXCUST XML)
│
├─ An IPWS / EBB posting (OAC, Unsubscribed, Transactional, Tariff, LDD, Gas Quality)?  (§8)
│   ├─ Apply the 3-point flow: did the CW* batch produce data? did the file land? is IPWS importing it?
│   ├─ Import error "Unable to enforce constants / DBNull"? → export missing a column (e.g. TSP_NM, #1668756)
│   ├─ Wrong/zero/doubled values? → export-calc defect (#1680441 unsub; #1795060 CapRel dup) → ADO bug
│   ├─ Segment-level / incremental request? → ENHANCEMENT (#1711191, #1802081), not a bug
│   └─ IPWS site down/slow? → PLATFORM/infra (restart, Cloud Ops) — not product code
│
├─ A notice / system notification / event-detector email?  (§9)
│   ├─ Type/subtype missing after upgrade? → re-add notice-type metadata (CONFIG)
│   ├─ Not sent/received? → posted? recipients active+email? QEMAIL ran?
│   └─ HTML tags / wrong sender / "?" chars / stuck notice? → template/encoding/expiry DEFECT → ADO bug
│
├─ Access / app tile / login / audit?  (§10)
│   ├─ "Give user access" → USER ADMIN (SKILL_Security_UserAdmin.md), not a defect
│   └─ Web/IPWS server down → PLATFORM/Cloud Ops
│
└─ Asking how-to / SQL spec / re-run / report comparison?  →  §16 Education (no fix needed)
```

---

*Skill created: 2026-06-01*
*Based on: ~1,470 closed QPTM Reporting / Informational Postings / Regulatory Reporting / Logging / Compliance / Notifications SF cases + ADO work items #1699870, #1670534, #1697284, #1668756, #1680441, #1772304/#1774246, #1779000, #1795060, #1711191, #1802081. Source category noted per cluster.*
*Companion skills: SKILL_Allocations.md, SKILL_Billing.md, SKILL_Contracts.md, SKILL_Nominations.md, SKILL_EDI_Troubleshooting.md, SKILL_Security_UserAdmin.md. Applicable to all QPTM TSPs/clients.*
