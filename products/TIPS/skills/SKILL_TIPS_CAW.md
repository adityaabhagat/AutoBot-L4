# SKILL: TIPS CAW Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-11 | **Product:** My Quorum TIPS (CAW — Customer Activity Web / external-shipper web portal)
**Scope:** The **CAW** (myQuorum "Customer Activity Web") external-facing portal and reporting layer for TIPS/QPTM pipelines: CAW DB connection (`TIPSCAWDataHelper`) & post-refresh setup, CAW environment/UAT build issues, CAW reports & external gas/settlement statements (RPT_GSTMT-QTIP / RPTGASSTWB-QTIP / RPT_INX51 / IN02MTR / RPT_ALRX04 / IN01), external-user login/security (Okta/AD ↔ ESuite, Agent BA, default BA), TIPS Web data-entry screens reached through CAW (CCT, Nomination Upload, PDA Import, Cuts), and the recent SOC/2025.10 environment-refresh batch failures (BLINVGEN/BLJRNALL/CWNIGHTLY/PALOCEXP) that surface under the CAW category.

> **Use When:** a TIPS case is tagged Case_Category__c = **CAW**, or the symptom involves an **external/producer user** logging into **myQuorum / "the CAW"**, running **gas/settlement/inventory statements** from the web, a **CAW DB connection / post-refresh** problem after a UAT/DEV refresh, or a **CAW security/report-viewer** access error. For pipeline allocation engine internals see the QPTM allocations skill; CAW *consumes* TIPS billing/allocation output and exposes it to external users — keep the boundary in mind.

> **Evidence base:** all **311** closed TIPS-CAW cases were profiled by Root_Cause__c. Actionable subset = **28** cases — Software Defect (22), Application Configuration (5), ChangeConfig (1). Plus a ~20-case Customer Error/Training sample for the Expected-Behavior section. Every root-cause claim below cites a real SF case number and/or ADO work item observed during mining. Many actionable cases have a **null Resolution__c** (resolved silently via ADO hotfix or Cloud Ops) — those are flagged honestly rather than invented.

---

## TABLE OF CONTENTS
1. [Quick Triage Table](#1-quick-triage-table)
2. [What CAW Is — Concepts](#2-what-caw-is--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — CAW DB Connection / Post-Refresh / Environment Setup](#4-cluster-a--caw-db-connection--post-refresh--environment-setup)
5. [Cluster B — External Gas / Settlement Statement Reports (Crystal memory/size)](#5-cluster-b--external-gas--settlement-statement-reports)
6. [Cluster C — CAW Report Access / Security / Report-Viewer Defects](#6-cluster-c--caw-report-access--security--report-viewer-defects)
7. [Cluster D — External-User Login, Password & Identity (Okta/AD ↔ ESuite)](#7-cluster-d--external-user-login-password--identity)
8. [Cluster E — TIPS Web Data-Entry Screens via CAW (CCT / Nom Upload / PDA Import / Cuts)](#8-cluster-e--tips-web-data-entry-screens-via-caw)
9. [Cluster F — SOC / 2025.10 Environment-Refresh Batch Failures (BLINVGEN/BLJRNALL/CWNIGHTLY/PALOCEXP)](#9-cluster-f--soc--202510-environment-refresh-batch-failures)
10. [Cluster G — myQuorum Web Portal Errors / Performance / Widgets](#10-cluster-g--myquorum-web-portal-errors--performance--widgets)
11. [Known ADO Items](#11-known-ado-items)
12. [Diagnostic SQL](#12-diagnostic-sql)
13. [Expected-Behavior / User-Education FAQ](#13-expected-behavior--user-education-faq)
14. [Escalation Guidance](#14-escalation-guidance)
15. [Key Code / Config Artifacts](#15-key-code--config-artifacts)

---

## 1. Quick Triage Table

| Symptom (what the user says) | Likely cause | First check |
|------------------------------|--------------|-------------|
| "CAW Error in UAT" / "CAW steps giving DB reference errors" right after a refresh | **`TIPSCAWDataHelper` (CAW) connection missing** from the post-refresh script | Connection Management for the CAW/TIPSCAW connection; the env's `*_TIPS_QFC_PostRefresh.sql` (§4) |
| External user runs **gas/settlement statement** → "Not Enough Memory" / report won't render | Crystal report image color depth + web file-size streaming limit | RPT_GSTMT-QTIP / RPTGASSTWB-QTIP report; logo color depth; web download MB cap (§5) |
| External user: **report shows NO data** / can't see their locations | No **default BA** on Integrated Security User; or user not on the **Agent BA** | Integrated Security User Setup → Default BA; BA tab (§6/§7) |
| "Report Viewer fails for users with CAW security" | Report-viewer defect for CAW-security users (code fix shipped) | Patch level / ADO #1790197 (§6) |
| CAW report missing / on wrong layer / wrong report type | Report-to-layer mapping (`QARCH_CODE_RPT_TYPE`) / report not enabled in CAW menu | §6, ADO #1802082, #2562/IN01 add-back |
| External user **can't log in / no password email** | Username mismatch **AD/Okta ↔ ESuite**, or account in suspended state | ESuite user setup vs IdP username (§7) |
| Web nom/CCT/PDA screen behaves wrong **only in Web/CAW** (Classic OK) | TIPS-Web-only screen defect | reproduce in Classic vs Web; check trigger/import job (§8) |
| SOC / 2025.10 batch (BLINVGEN/BLJRNALL/CWNIGHTLY/PALOCEXP) erroring in a new env | **Environment setup**: server file paths or BA/COA config not migrated on refresh | process log by PQID; file paths; BA affiliate/COA mapping (§9) |
| myQuorum **slow / widgets not loading / portal errors** | Server/web-tier configuration | server config, web services startup, firewall to MT/QPEC (§10) |
| CAW flat-file upload stores decimals though screen shows whole number | Flat-file upload rounding defect | reproduce via upload (not screen entry) (§8) |

---

## 2. What CAW Is — Concepts

**CAW** is the external-facing **myQuorum web portal** layer over a TIPS/QPTM pipeline ("the CAW"). External users — **producers, shippers, operators, and their agents** — log into myQuorum to: submit/upload **nominations**, run **gas statements / settlement statements / inventory & imbalance reports**, and view notices. Internally CAW is wired up as:

```
External user (Okta/B2C/AD)  ──login──►  myQuorum Web (CAW web servers)
        │                                      │
        │  identity must match ESuite user      │  uses the CAW DB connection
        ▼                                      ▼   (TIPSCAWDataHelper) + CAW views
  Integrated Security User Setup            TIPS/QPTM DB (QRMTIPS / ESUITE_QENT)
  (Default BA, Agent BA, BA tab security)   billing/allocation/inventory output
        │                                      │
        └──────────────► Reports (Crystal): gas stmt, settlement, INX/IN inventory ◄──┘
```

Key facts that drive most cases:
- **A dedicated CAW DB connection** (`TIPSCAWDataHelper`, a.k.a. the "CAW"/"TIPSCAW" connection in Connection Management) must exist in every environment. **Refreshes drop it** unless the env's post-refresh script re-adds it — the #1 setup failure (§4).
- **External-user visibility is BA-driven.** What a user sees is controlled by **security + the BA tab**, a **Default BA** on Integrated Security User Setup, and (for agents) membership on the **Agent BA**. Most "no data / can't see my locations" cases are this, not a bug (§6, §7, §13).
- **CAW reports are heavy Crystal reports** streamed through the web; large logos/color depth + a web file-size cap cause "Not Enough Memory" failures (§5).
- **Identity is 1 User ID per email** under Okta/SSO (Cloud 1.5+); old multi-User-ID-per-email setups break (§7).
- **CAW = the external surface of TIPS billing/allocation.** When a *batch* (BLINVGEN/BLJRNALL/CWNIGHTLY) fails in a CAW-tagged case it is almost always **environment setup** (paths/BA/COA not migrated on refresh), not a CAW-portal bug (§9).

---

## 3. Decision Tree

```
TIPS case tagged CAW
│
├─ Just after a DB refresh / new UAT/DEV env? ("CAW Error in UAT", DB reference error)   → §4
│     └─ CAW (TIPSCAWDataHelper) connection missing → add it in Connection Management;
│        permanent fix = put it in the env post-refresh script (ADO #1655053 pattern)
│
├─ A REPORT problem?                                                                       → §5/§6
│   ├─ "Not Enough Memory" / won't render (gas/settlement stmt) → Crystal color depth + web MB cap  (§5)
│   ├─ "No data" / can't see locations → Default BA / Agent BA / BA security  (§6, usually config/expected)
│   ├─ "Report Viewer fails for CAW-security users" → code defect, patch  (ADO #1790197) (§6)
│   ├─ Report wrong/missing/empty in CAW → report-to-layer & report-type mapping  (§6, ADO #1802082/#1812654/#1809769)
│   └─ Specific report logic wrong (RPT_INX51 ignores BP param) → code defect  (ADO #1798177) (§6)
│
├─ LOGIN / password / "can't access myQuorum"?                                            → §7
│     └─ AD/Okta username ≠ ESuite username, suspended pre-existing account, 1-email-1-UserID → identity config
│
├─ A TIPS WEB data-entry screen wrong (CCT add, nom upload, PDA import, cuts) — Classic OK? → §8
│     └─ TIPS-Web-only defect → reproduce Classic vs Web; check DB trigger / import job  (code)
│
├─ A BATCH failing (BLINVGEN/BLJRNALL/CWNIGHTLY/PALOCEXP) in a new/refreshed env?          → §9
│     └─ ENVIRONMENT SETUP: server file paths not migrated; BA affiliate / COA mapping; rate tiers → config
│
└─ Portal slow / widgets blank / generic "getting errors"?                                 → §10
      └─ Server/web-tier config, web-services startup, firewall to MT/QPEC servers → Cloud Ops / config
```

---

## 4. Cluster A — CAW DB Connection / Post-Refresh / Environment Setup

**Cases:** 24-00947753, 24-00950735, 22-00513042 (also relates to Cluster F refresh issues) | **ADO:** #1655053
**Cases in cluster:** ~3 actionable (the highest-confidence, best-documented CAW-specific cluster).

### Symptom
Right after a UAT/DEV refresh (or a new environment), CAW screens/steps throw **"DB reference errors"** or generic **"CAW Error in UAT"**; external CAW functionality simply doesn't work.

### Root cause
The dedicated **CAW DB connection** (`TIPSCAWDataHelper`, shown as the **CAW / TIPSCAW** connection in Connection Management) is **not recreated by the post-refresh script**. The QFC post-refresh script for many environments omits the CAW connection details, so after every refresh the connection is missing/invalid.

### Resolution recipe
1. Open **Connection Management** and check for the **CAW / TIPSCAW** connection. If missing or invalid, **add it manually** with the environment's CAW DB connection details. (Verbatim from 24-00947753: *"added the CAW connection manually to the connection management."*)
2. Re-run the environment's **post-refresh script**; if it lacks the CAW connection block, that is the defect.
3. For 24-00950735 the disposition was simply **"Updated caw setup"** — i.e. correct the CAW connection/setup in the refreshed env.
4. **Permanent fix:** add the `TIPSCAWDataHelper` connection to the env's post-refresh script. This is exactly **ADO #1655053** (*"HVM – Add TIPSCAWDataHelper connection to the post-refresh scripts to HVM_UAT17_MID and HVM_DEV17MID"*, Bug, **Proposed** as of mining — still open). The connection block lives in the per-client `*.TIPS.Database/PostRefreshScripts/*_TIPS_QFC_PostRefresh.sql` (§15).
5. If a client moved the CAW server / data center and it can't connect at all, suspect **firewall rules** blocking the web server from the **MT and QPEC** servers (22-00513042) — Cloud Ops.

> Rule of thumb: **every "CAW broke after a refresh" case = the CAW connection / post-refresh script.** Check Connection Management first, before any code suspicion.

---

## 5. Cluster B — External Gas / Settlement Statement Reports (Crystal memory/size)

**Cases:** 22-00875574 (RPT_GSTMT-QTIP), 23-00886361 (RPTGASSTWB-QTIP), related 23-00883409 | **Training cross-ref:** 22-00854209, 22-00513087
**Cases in cluster:** ~3 actionable + report training cases.

### Symptom
Producer/external user runs the **external PDF gas statement** (RPT_GSTMT-QTIP) or **web gas statement** (RPTGASSTWB-QTIP) from myQuorum and gets **"Not Enough Memory"**, *"Exception retrieving report files: the formatter threw an exception while trying to deserialize the message,"* or the report **never renders in the browser** (works only when written to a network drive).

### Root cause
Heavy **Crystal report** streamed through the web tier. Two compounding factors: (a) the report **logo's image color depth** bloats the rendered file, and (b) the **web download size limit** is too small for the resulting file.

### Resolution recipe (verbatim from the cases)
1. In Crystal, on the gas-statement report (`GAS_STMT_WEB`), **turn off "Retain Original Image Color Depth"** / **reduce the logo's color depth**. *"This cut the file size in half and allowed the report to be generated and accessible almost immediately"* (23-00886361). 22-00875574 also disabled it to clear the *"Not Enough Memory"* error.
2. **Raise the web file-streaming size limit** for downloads. 22-00875574: limit was **100 MB → raised to 350 MB**.
3. Both fixes together: smaller file + larger cap = statement renders in the browser for external users.

> When an external user "can't open their gas statement," check **report size** (logo color depth) and the **web download cap** before anything else. For RPT documentation requests (formulas/views), see 22-00854209 — that's a documentation deliverable, not a defect.

---

## 6. Cluster C — CAW Report Access / Security / Report-Viewer Defects

**Cases:** 26-01089048 (RPT_ALRX04), 23-00894552 (IN02MTR), 22-00679900, 22-00598070 | **ADO:** #1790197, #1798177, #1802082, #1812654, #1809769, #1787105, #1436992
**Cases in cluster:** several actionable + many config/expected.

This cluster splits into **(a) access/visibility config** (mostly "working as designed", §13 overlaps) and **(b) genuine CAW report defects** (code, ADO-tracked).

### 6a. Access / visibility (config)
| Issue | Root cause | Fix | Evidence |
|-------|-----------|-----|----------|
| Operator can only see a location **not** assigned to them when running **RPT_ALRX04**; can't see managed locations | Report security/config not aligned to app design | **Change configuration to align with application design** (resolved) | 26-01089048 |
| Users **can't run IN02MTR in CAW** ("missing in CAW views") | Users not on the **Agent BA** | **Add the users to the Agent BA** | 23-00894552 (ADO ChangeConfig) |
| External user report shows **NO data** | Missing **Default BA** on Integrated Security User Setup | Select a Default BA for the user | 22-00693490 (see §13) |
| Add a report back into CAW (e.g. **IN01 Monthly Imbalance**) | Report not enabled in CAW menu | Provide Enable instructions / add report to CAW | 22-00562653 |
| Add external security objects to a CAW security group | Security-object/group config | Config (Feature) | ADO #1787105 (NCG, LDC group 3003) |
| NRM external **Service Invoice** report for agents | Agent-scenario code change (Cloud 1.5 / SSO) | Feature delivered | ADO #1436992 |

### 6b. CAW report defects (code, ADO-tracked)
| Issue | Root cause | State | Evidence |
|-------|-----------|-------|----------|
| **"QPTM Web Report Viewer Fails for Users with CAW Security"** | Report-viewer defect specific to CAW-security users | **Closed** (fixed) | ADO #1790197 (ONG 2025.10) + DEV/QA tasks #1799621-23, #1801952 |
| **RPT_INX51** (CAW Inventory / Agreement Balancing Statement) **does not use the BP parameter when selected** | Report ignores BP filter param | **Closed** (fixed) | ADO #1798177 (ETC, SF 26-01087100) |
| **CAW External Reports empty** in TIPS UAT | CAW external report data/layer defect | **Proposed** (open) | ADO #1812654 (AZR) |
| **CAW tables for external users** not populated / CAW Process | CAW external-table population defect | **Proposed** (open) | ADO #1809769, #1809773 (HVK) |
| CAW reports on the **wrong report layer / report type** | `QARCH_CODE_RPT_TYPE` report-type mapping wrong | **Resolved** | ADO #1802082 (GNP — set CAW reports to QGNP layer) |
| Report Viewer in myQuorum **not working for Excel files** | Web report-viewer file-type handling | (older defect) | 22-00598070 |
| Report Parameters showing for the **wrong report** | Report-param binding | (older defect) | 22-00679900 |

> Disposition heuristic: **"can't see my data / wrong locations" is usually BA security config (6a)**; **"report viewer fails / report empty / report ignores a parameter" is usually a code defect (6b)** — match to the ADO item and confirm the patch/version.

---

## 7. Cluster D — External-User Login, Password & Identity (Okta/AD ↔ ESuite)

**Cases:** 26-01089784 (Okta auto-provisioning), 22-00671080, 22-00562651, 22-00642378, 24-00954037, 22-00666852 | **CronGlobalConfig:** SEC_AUTH_EXTRAINFO_MSG (24-00985105)
**Cases in cluster:** mostly Training/Customer Error + a few Okta defects; very high volume of "New CAW User Setup" Cloud-Ops requests (ADO #1781498, #1781691, #1785248, #1787380, #1788355, #1789807, #1793040, #1800014, #1801335, #1808214, #1811890 — all *Request Global Cloud Ops, Closed*).

### Symptom & root causes
| Symptom | Root cause | Fix | Evidence |
|---------|-----------|-----|----------|
| External user **can't log in to myQuorum** | **AD/Okta username ≠ ESuite username** | Align the username in ESuite to the IdP | 22-00671080 ("setup the username different in their AD compared to ESUITE") |
| **Okta auto-provisioning** via Azure AD groups not creating the account | A **pre-existing account** matched and was put in a **suspended** state | Remove the old suspended account so it re-provisions cleanly | 26-01089784 |
| External user **gets no password / reset email** | ESuite CAW user-reset-link config | Provide ESuite walkthrough / send reset email | 22-00562651, 24-00954037, 22-00642378 |
| Want to change **forgot-password verbiage / phone number** on myQuorum | Config key, not a code change | Set **Global Config `SEC_AUTH_EXTRAINFO_MSG`** | 24-00985105 |
| "New CAW User Setup" / "add new QCloud CAW user" | Standard provisioning request | Cloud Ops provisioning | many (ADO Request Global Cloud Ops items above) |
| Add a whole module (e.g. **Gathering**) to all TIPS users | Bulk user/module config | Config | 24-00972857 |

> **Identity rule (Cloud 1.5+ / SSO):** under Okta you get **one User ID per email address**. Old setups with multiple User IDs on one email break after SSO migration (called out in 22-00693490). For agent/multi-BA users this interacts with the Default-BA requirement (§6a/§13).

---

## 8. Cluster E — TIPS Web Data-Entry Screens via CAW (CCT / Nom Upload / PDA Import / Cuts)

**Cases:** 22-00597984 (CCT add), 22-00617660 (nom upload bad record), 23-00929063 (PDA Import eff-dating), 22-00819381 (flat-file decimals), 22-00592849/50/60/61 (Web CCT/meter/lock/required-fields), 22-00676418 (cuts security), 22-00598027 (SR picklist)
**Cases in cluster:** ~9 actionable; recurring theme is **TIPS-Web-only defects** (Classic works, Web doesn't).

| Issue | Root cause | Fix type | Evidence |
|-------|-----------|----------|----------|
| Query existing **CCT**, change number, add new → fails with Oracle trigger `QRMTIPS.GTBIUD_CCT`; only in **TIPS Web** (Classic OK, MSSQL core OK) | Web-only CCT add-after-query path hits the BIUD trigger | Code fix | 22-00597984 (Oneok 2020.03) |
| **Nomination Upload** for a receipt meter also creates an unwanted **delivery** nom (and vice-versa) | Web nom-upload duplicate-record defect | Code fix | 22-00617660 (MKW 2019.05) |
| **PDA Import (PDAIMP)** ignores **Contract Header Agent-tab effective dating** | PDA import doesn't honor agent eff-dates | Code fix | 23-00929063 |
| **CAW flat-file upload** stores **decimals** though the screen shows whole numbers (screen entry is fine) | Flat-file upload rounding/format defect | Code fix | 22-00819381 (*resolution pattern unclear from mined case — confirm fixed build*) |
| Web **Cuts** screen — external **security agency** issue | Web cuts external-security defect | Code/config | 22-00676418 |
| Web **Service Requestor pick list** for external users | Web picklist defect | Code fix | 22-00598027 |
| Web Company/Facility **Lock Screens**, **Required-Fields indicator**, **CCT changes**, **Meter-Type overrides** | Early TIPS-Web screen polish defects (Descriptions empty in SF) | Code | 22-00592860/61/49/50 (*resolution pattern unclear from mined cases*) |
| **CAWT DCP Setup — build errors** | Client (DCP) CAW build/setup | Build/config | 22-00671032 |

> **Web ≠ Classic is the recurring tell.** When an external user reports a data-entry screen behaving wrong, **reproduce in Classic vs Web** — the defect is almost always the Web/CAW path being more permissive (flat-file decimals) or hitting a DB trigger / creating bad records (CCT, nom upload). Many of these older cases have **null Resolution__c** in SF (fixed via build hotfix); confirm the target build before promising a fix.

---

## 9. Cluster F — SOC / 2025.10 Environment-Refresh Batch Failures (BLINVGEN / BLJRNALL / CWNIGHTLY / PALOCEXP)

**Cases:** 26-01090579 (BLINVGEN), 26-01090580 (BLJRNALL), 26-01089624 (CWNIGHTLY), 26-01089498 (PALOCEXP), 26-01089631 (IPWS SFTP), 26-01088304 (security), 26-01088719 (EPSQ cycle offset), 26-01088716 (CAS IT rates), 26-01088173 (RFS auto-award), 26-01089011 (Dynegy EDI XML)
**Cases in cluster:** ~10 recent (2026 / "2025.10" / "SOC") cases tagged CAW. These are **not CAW-portal bugs** — they cluster as **environment/config issues surfacing during SOC (Standard of Conditions) onboarding and post-refresh**.

| Process / symptom | Root cause | Fix | Evidence |
|-------------------|-----------|-----|----------|
| **BLINVGEN** (Invoice Generation) rate-resolution errors / cashout-rate interaction | Rate setup incomplete | **Default accounting, clean up tiers, add additional rates** | 26-01090579 |
| **BLJRNALL** — "Default Bill record not set" for the TSP | **BA affiliate misconfigured** — interconnect AND affiliate both true, no sub-account | **Remove the interconnect indicator; fix COA mapping logic** | 26-01090580 |
| **CWNIGHTLY** erroring (PQID 33995199, TSP 9 HPE) | **Server file paths not updated** to the correspondent server | Update file paths to the correct server | 26-01089624 |
| **PALOCEXP** job failing | Same — file paths wrong for the env | **Update file paths based on the correspondent server** | 26-01089498 |
| **IPWS SFTP** transfer def error (SOC_3) | Wrong `HOST_FILE_PATH` (folder didn't exist on the FTP site) | Correct the SFTP host file path (e.g. `…/StandardOfCond/AFFLNMADDR`) | 26-01089631 |
| **CAS** not scheduling on IT rates | TOC object maintenance missing for res/com on CANOM | TOC object maintenance for res & com on CANOM batch | 26-01088716 |
| **EPSQ → 0** when an error was expected | Cycle gas-flow start-time offset wrong | `UPDATE PACTRL_CYCLE SET GAS_FLOW_START_TIME_OFFSET …` per CYCLE_ID | 26-01088719 |
| Contract Maintenance **security** | Group privileges | Changed privileges for grp 40008 | 26-01088304 |
| EDI Dynegy **XML** error | App XML mapping | App XML change | 26-01089011 |
| Auto-award RFS on last approval | Config request | Global Config `AUTO_AWARD_RFS_ON_APPROVAL = 1` | 26-01088173 |

> **Pattern:** the 2026/"2025.10"/SOC wave under CAW is dominated by **"file paths not updated to the correspondent server"** (CWNIGHTLY, PALOCEXP, IPWS) and **BA/COA/rate config gaps** during SOC onboarding — i.e. **environment & config**, dispositioned by Cloud Ops / config, not Engineering. Always get the **PQID** and check the process log + server file paths first.

---

## 10. Cluster G — myQuorum Web Portal Errors / Performance / Widgets

**Cases:** 22-00636586 ("Web portal getting errors"), 22-00676423 (slow), 22-00708438 (web services startup), 22-00528116 (WEBCAW widgets), 22-00821548 (CAWDATA locking peer processes), 22-00513041 (check data pull)
**Cases in cluster:** ~6 actionable; mostly **server/web-tier configuration**.

| Symptom | Likely cause | Fix | Evidence |
|---------|-------------|-----|----------|
| **WEBCAW widgets not loading** data for external users | Server configuration | Server config | 22-00528116 (resolved "Server Configuration") |
| myQuorum web **very slow** | Web-tier/server load/config | Cloud Ops investigation | 22-00676423 (*resolution pattern unclear from mined case*) |
| **Web Services startup** issue | Web service config | Config | 22-00708438 (*resolution unclear*) |
| **CAWDATA errors locking peer processes** | CAW batch/data contention | (no SF resolution captured) | 22-00821548 (*resolution unclear — see `QPSPurgeCAWRun` §15*) |
| Generic "WEB PORTAL — getting errors" | Triage env/config first | varies | 22-00636586 (*unclear*) |
| Can't pull check data through myQuorum | Data/report availability | varies | 22-00513041 (*unclear*) |

> Several Cluster-G cases have **no captured resolution** — treat as **Cloud Ops / server-config** triage (web-services restart, server config, firewall to MT/QPEC per §4). Do not assume a product code bug.

---

## 11. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF link |
|-------|--------------|-----------------|---------|---------|
| **#1655053** | Bug / **Proposed** | HVM — Add **TIPSCAWDataHelper** connection to post-refresh scripts (HVM_UAT17_MID / DEV17MID) | §4 | 24-00947753 |
| **#1790197** | Bug / **Closed** (2026-06-02) | ONG 2025.10 — **QPTM Web Report Viewer Fails for Users with CAW Security** | §6b | — |
| #1799621/#1799622/#1799623/#1801952 | Task / Closed | DEV/LEAD/QA tasks for #1790197 | §6b | — |
| **#1798177** | Bug / **Closed** (2026-05-13) | ETC — **CAW Inventory Report RPT_INX51** Agreement Balancing Statement **does not use BP parameter** | §6b | 26-01087100 |
| #1800407/#1800408 | Task / Closed | DEV/QA tasks for #1798177 | §6b | — |
| **#1812654** | Bug / **Proposed** | AZR — **CAW External Reports Empty** Bug (TIPS UAT) | §6b | — |
| **#1809769 / #1809773** | Bug / **Proposed** | HVK — **CAW Tables for external users** / CAW Process | §6b | — |
| **#1802082** | Bug / **Resolved** | GNP — `QARCH_CODE_RPT_TYPE` set **CAW Reports to QGNP layer** | §6b | — |
| **#1787105** | Feature / Proposed | NCG — Add External Security Objects to **CAW LDC Security Group (3003)** | §6a | — |
| **#1436992** | Feature / Closed | NRM — **Service Invoice External Users (Agent Scenario)** | §6a | 22-00693490 |
| #1790342/#1790685/#1790785 | Task / Closed | UNSC file should not display **non-CAW-nominatable** locations (PATH level) | §8 | — |
| #1782643 | Internal Issue / Closed | Internal midstream webpage for **CAW environments** is down | §10 | — |
| #1810686 | Internal Issue / Closed | ENT — NI missing **TIPS ClassicGUI CAW** | §4/§8 | — |
| **New CAW User Setup** batch | Request Global Cloud Ops / Closed | #1781498, #1781691, #1785248, #1787380, #1788355, #1789807, #1793040, #1800014, #1801335, #1808214, #1811890 (MOM / Opportune / Harvest) | §7 | various 26-010xxxxx |

> **Takeaway:** open (Proposed) CAW defects all concern **external-report population in UAT** (#1812654, #1809769) and the **post-refresh connection** (#1655053) — these are the live engineering items. The report-viewer-with-CAW-security defect (#1790197) and RPT_INX51-BP-parameter defect (#1798177) are **already fixed (Closed)** — confirm the client's patch level. "New CAW User Setup" is steady-state **Cloud Ops** volume, not engineering.

---

## 12. Diagnostic SQL

> Column/table names below are drawn from the case resolutions themselves (e.g. `PACTRL_CYCLE`, `QARCH_CODE_RPT_TYPE`) and from QPTM/TIPS conventions. Verify exact names against the schema before scripting in PRD; wrap any UPDATE/DELETE in `BEGIN TRAN … COMMIT` with a verify-SELECT.

```sql
-- A. CAW report-to-layer / report-type mapping (the #1802082 "wrong layer" + missing-report pattern)
SELECT * FROM QARCH_CODE_RPT_TYPE
WHERE  RPT_ID IN ('RPT_GSTMT-QTIP','RPTGASSTWB-QTIP','RPT_INX51','RPT_ALRX04','IN02MTR','IN01');
-- Wrong APP_LAYER / report type here = report missing or empty in CAW.

-- B. Cycle gas-flow start-time offset (26-01088719 EPSQ-to-0 fix shape, VERBATIM from the case)
SELECT CYCLE_ID, GAS_FLOW_START_TIME_OFFSET FROM PACTRL_CYCLE WHERE TSP_NO = <TSP_NO>;
-- Resolution example:
--   UPDATE PACTRL_CYCLE SET GAS_FLOW_START_TIME_OFFSET = '43200' WHERE CYCLE_ID = '4';
--   UPDATE PACTRL_CYCLE SET GAS_FLOW_START_TIME_OFFSET = '28800' WHERE CYCLE_ID = '3';

-- C. Batch process failure — pull the log/trace for the failing PQID (CWNIGHTLY/PALOCEXP/BLINVGEN/BLJRNALL)
SELECT * FROM QARCH_QFCBATCH_SQL_TRACE WHERE PROCESS_QUEUE_ID = <PQID> ORDER BY SEQ_NO;
-- For CWNIGHTLY/PALOCEXP look for missing/old SERVER FILE PATHS (the 26-01089624 / 26-01089498 root cause).

-- D. External-user visibility: Default BA + Agent BA (the "no data / can't see my locations" pattern, §6a/§7)
--    Inspect Integrated Security User Setup for the external user's Default BA and BA-tab security.
--    (Exact ESuite security tables vary by env; review via the Integrated Security User Setup screen.)
```

For the **CAW DB connection** (§4) there is no SQL — verify it in **Connection Management** (UI) and in the env's `*_TIPS_QFC_PostRefresh.sql`.

---

## 13. Expected-Behavior / User-Education FAQ

~20 Customer-Error/Training CAW cases were sampled. The top "this is working as designed" answers:

| Reported as | Reality / answer | Evidence |
|-------------|------------------|----------|
| "External user's **report shows NO data**" | They have **no Default BA** on Integrated Security User Setup — select one and the report generates. **Working as designed.** | 22-00693490 (RPT_23920 Service Invoice) |
| "Can't see settings / who can see what in CAW" | Visibility is controlled by **security and the BA tab** on the security setup — educate, not a bug | 22-00513124 |
| "External user **can't log in**" | **AD/Okta username ≠ ESuite username**, or pre-existing **suspended** account; 1 User ID per email under SSO | 22-00671080, 26-01089784 |
| "No password / reset email" | ESuite CAW reset-link config — provide the ESuite walkthrough; send reset | 22-00562651, 22-00642378, 24-00954037 |
| "Revised gas statements not showing" | User must **run the statements as posted**; they then show on the web | 22-00636618 |
| "Taxes missing on **PDF** statement but on CSV" | Report **hides taxes when set to report-only**; the **CSV export lacks that hide-logic** (so CSV shows them) — expected for PDF | 22-00513087 |
| "**Impersonation** doesn't work on internal users" | By design business users impersonate **external** users, not internal | 22-00530904 |
| "MMA error / oops in CAWT" | Could **not be reproduced** outside a defunct test env — non-issue | 22-00671133, 22-00671080 |
| "Retroactive confirmation question (UAT)" | Non-issue — provided confirmation-validation & external-deadline documentation | 22-00530858 |
| "External nomination **upload fails**" | File/date issue — re-create the nom template and **use a different file name**; then upload succeeds | 25-01004088 |
| "ORA-01187 cannot read from file … failed verification" | **Corrupt DB file** — replaced (infra), not a CAW bug | 22-00598654 |

> **Tell-tale it's user/expected:** "no data / can't see my locations" (→ Default BA / Agent BA), login/password (→ ESuite-vs-IdP username), PDF-vs-CSV tax difference (report-only hide-logic), impersonation of internal users, or an "oops/MMA" error only in a stale test env.

---

## 14. Escalation Guidance

**Resolve in support / Cloud Ops (config, no code):**
- CAW connection missing after refresh → add in Connection Management; fix the post-refresh script (§4).
- New CAW user setup / add module → Cloud Ops provisioning request (§7).
- External user "no data / can't see locations" → set **Default BA** / add to **Agent BA** (§6a, §13).
- Gas-statement "Not Enough Memory" → reduce Crystal logo color depth + raise web file-size cap (§5).
- SOC/2025.10 batch failures → fix **server file paths** / **BA-COA-rate** config (§9).
- Portal slow / widgets blank / web-services startup → server config, firewall to MT/QPEC (§10).
- Forgot-password verbiage → Global Config `SEC_AUTH_EXTRAINFO_MSG` (§7).

**Escalate to Engineering (code defect) — confirm patch/version against the ADO item:**
- **Report Viewer fails for CAW-security users** → ADO #1790197 (**Closed** — verify patch).
- **RPT_INX51 ignores BP parameter** → ADO #1798177 (**Closed** — verify patch).
- **CAW external reports empty / CAW tables not populated in UAT** → ADO #1812654, #1809769 (**Proposed — open; link the case**).
- Post-refresh CAW connection automation → ADO #1655053 (**Proposed — open**).
- TIPS-Web-only screen defects (CCT add-after-query trigger, nom-upload bad record, PDA-import eff-dating, flat-file decimals) → reproduce **Classic vs Web**, then Engineering (§8).

**Cloud Ops vs Engineering decision:** if it reproduces only in a **refreshed/new environment** (paths, connection, BA/COA) → **Cloud Ops/config**. If it reproduces in a **clean, correctly-configured env** (especially Web-only behavior or a report ignoring a parameter) → **Engineering**.

---

## 15. Key Code / Config Artifacts

| Artifact | Purpose / relevance |
|----------|---------------------|
| **`TIPSCAWDataHelper`** connection | The CAW DB connection added in Connection Management; must be in the env's post-refresh script (§4, ADO #1655053). |
| `*.TIPS.Database/PostRefreshScripts/*_TIPS_QFC_PostRefresh.sql` (per client: DCP, ENT, MER, EQT, ACP, AHS, …) | Per-environment QFC post-refresh script — where the CAW connection block belongs; omission causes "CAW Error in UAT". |
| `Quorum.TIPS.ClassicBatch/Common/QPDllTipsUtility/QPSPurgeCAWRun.cpp` | CAW run/purge batch utility (relevant to "CAWDATA locking peer processes", 22-00821548). |
| **`QARCH_CODE_RPT_TYPE`** | Report-to-layer / report-type mapping for CAW reports (ADO #1802082 — set CAW reports to client layer e.g. QGNP). |
| `QARCH_CNFG_MENU.json` / `QARCH_CNFG_CTRL.json` (`*.TIPS.Metadata`) | CAW menu & control metadata — which reports/screens are enabled in CAW (e.g. add IN01 back, 22-00562653). |
| **Integrated Security User Setup** screen (ESuite) | Default BA, Agent BA, BA-tab security — drives external-user report visibility (§6a/§7/§13). |
| `Quorum.QPTM.CoreInterface/Constants.cs` | Constants incl. CAW/report-viewer security strings. |
| Reports: **RPT_GSTMT-QTIP / GAS_STMT_WEB**, **RPTGASSTWB-QTIP**, **RPT_INX51**, **RPT_ALRX04**, **IN02MTR**, **IN01** | The CAW external statement/inventory/imbalance reports referenced across §5/§6. |
| Batch: **BLINVGEN, BLJRNALL, CWNIGHTLY, PALOCEXP, CANOM, PDAIMP, IPWS** | TIPS/QPTM batch processes that surface under CAW during SOC/refresh (§8/§9). |
| Global Config keys | `SEC_AUTH_EXTRAINFO_MSG` (forgot-password text), `AUTO_AWARD_RFS_ON_APPROVAL` (RFS auto-award). |

---

*Skill created: 2026-06-11*
*Based on: 311 closed TIPS-CAW SF cases (Software Defect 22, Application Configuration 5, ChangeConfig 1 actionable; ~20 Customer Error/Training sampled) + ADO items #1655053, #1790197, #1798177, #1802082, #1812654, #1809769/#1809773, #1787105, #1436992, #1790342, #1782643, #1810686, and the Cloud-Ops "New CAW User Setup" series.*
*Data-quality caveats: many older Software-Defect cases (TIPS-Web screens, portal errors) have null Resolution__c in SF — fixes shipped via build hotfixes; confirm target build. The "CAW" category also collects non-portal TIPS/QPTM environment-refresh batch cases (§9). Aggregate GROUP BY and multi-value IN() SOQL timed out repeatedly on this connector; counts were obtained via per-value COUNT() queries.*
