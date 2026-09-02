# SKILL: TIPS Uncategorized Case Sweep — Triage & Resolution Patterns

**Version:** 1.0 | **Created:** 2026-06-11 | **Product:** My Quorum TIPS (oil/gas transaction & accounting)
**Scope:** The ~1,336 closed TIPS cases with Case Category = All / Other / blank ("uncategorized sweep"). This is a **triage-and-routing skill**: most of these cases were never properly categorized, so the primary value is (a) recognizing which of ~14 recurring symptom families a new uncategorized TIPS case belongs to, (b) the first check for each, and (c) the documented fix recipes where the data preserved them.
**Use When:** A TIPS case arrives with no category, a vague subject ("TIPS error", "process error", "TIPS isn't working"), or it touches QPEC engines, environment refreshes, batch job failures (ALLOCATE / TIPSMASTER / SETTLEMAIN), volume/analysis imports, Meter Split / Contract Meter List, statements/invoices, or user access.

> Evidence base: 1,336 closed cases (Product = 'My Quorum TIPS', Category in All/Other/null). Root-cause field coverage is poor: **890 (67%) have NO root cause recorded**; only 43 are tagged Software Defect / Application Configuration / ChangeConfig. Clustering below is from bulk subject mining (~1,066 subjects reviewed) plus full Description/Resolution pulls on ~30 representative cases and 40 Training/Customer Error cases, cross-referenced to ADO.
>
> **DATA-QUALITY CAVEAT (important):** cases created 2017–mid-2022 (the bulk of the "22-00xxxxxx" series) were migrated from a legacy ticket system and have **null Description and null Resolution** in Salesforce — only the subject line survives. Resolution recipes below are therefore anchored on 2022-12-onward cases; for older clusters where no resolution text exists, this skill says so explicitly rather than inventing one.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Decision Tree](#2-decision-tree)
3. [QPEC Engines / Stuck Process Queue (HIGH FREQUENCY)](#3-qpec-engines--stuck-process-queue)
4. [Environment Refresh & Post-Refresh Breakage](#4-environment-refresh--post-refresh-breakage)
5. [Facility Batch Job Failures — ALLOCATE / TIPSMASTER / TIPSLOCK / SETTLEMAIN](#5-facility-batch-job-failures)
6. [Volume & Analysis Import/Export Interfaces](#6-volume--analysis-importexport-interfaces)
7. [Meter Split / Meter Definition / Shared Meter / Contract Meter List](#7-meter-split--meter-definition--shared-meter--contract-meter-list)
8. [Statements, Invoices & Journals](#8-statements-invoices--journals)
9. [Reports & Report Viewer](#9-reports--report-viewer)
10. [PPA / PMA / Reruns / Rerun Purge](#10-ppa--pma--reruns--rerun-purge)
11. [Accounting Date / Month Close / Facility Lock / Reallocation Mode](#11-accounting-date--month-close--facility-lock--reallocation-mode)
12. [PDA (TIPS-side) Issues](#12-pda-tips-side-issues)
13. [Fees, Taxes, Escalations & Rate Schedules](#13-fees-taxes-escalations--rate-schedules)
14. [QEMAIL / Notifications / Event Detectors](#14-qemail--notifications--event-detectors)
15. [Archive / Purge](#15-archive--purge)
16. [User Access / Login / Okta / Citrix / QCloud (ROUTE TO CLOUD OPS)](#16-user-access--login--okta--citrix--qcloud)
17. [Recurring Scripted Data Loads (Condensate GPM etc.)](#17-recurring-scripted-data-loads)
18. [Expected Behavior / User Education FAQ](#18-expected-behavior--user-education-faq)
19. [Known ADO Items](#19-known-ado-items)
20. [Key Tables, Processes & Repos](#20-key-tables-processes--repos)
21. [Diagnostic SQL](#21-diagnostic-sql)
22. [Escalation Guidance](#22-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (subject pattern) | Likely cause | First check | § |
|---|---|---|---|
| "Jobs stuck in queue" / "process says Queued" / "UAT jobs will not complete" / "QPEC restart" | QPEC engines down, hung, or rogue; memory leak on app server | Are QPECs running? Request restart / rogue-QPEC kill from Cloud Ops | §3 |
| "Refresh UAT/DEV from PRD" | Routine environment request | Confirm env + restore point; hand to Cloud Ops/Data Services | §4 |
| Screen/report broken right after a refresh | Post-refresh scripts overrode config (Exago, paths, security objects) | Compare config vs PRD (Exago URL, FILE_SHARE_ROOT_PATH, Imp/Exp paths) | §4 |
| ALLOCATE / TIPSMASTER / Facility Batch Job errored or ran hours long | Data/config feeding the run; TIPSLOCK realloc-check; known engine bugs | Get MPQID + plant + prod month + exact step (CTRMTR, STDPDA, UPDTALLOCV, SETTLEMAIN) | §5 |
| "Volumes not uploading" / "import file not found" / FlowCal/PI/spreadsheet load fails | Wrong import/export path or file-format/parameter error | Import/Export Definition path; QIMPEXP step default-value override | §6 |
| Can't update/delete on Contract Meter List; "invalid effective date" on correctly timesliced meter | Meter Definition time slice end-dated (known IP bug); CML validation defects | Meter Definition time slices for the meter; ADO #1788087 | §7 |
| Meter Split Mass Change skips meters / split decimal not updating | Known Meter Split defects (ADO #1795476, #1790136) | Which meters skipped; daily vs monthly split; Acctg Date Maint setup | §7 |
| Statement/invoice wrong (missing rows, duplicate invoice no., wrong BA name, doubled volume) | Report/statement config or statement-format defect; allocation upstream | Is the underlying allocated data right? Then statement format/BA suffix filters | §8 |
| Report empty / won't open / stuck in queue / doubled values | Report layer (Crystal/Exago) or upstream data | Underlying data first; then report queue/QPEC; then report definition | §9 |
| PPA/PMA/rerun behaving oddly; rerun data not purged | Rerun purge / realloc-mode processing defects | Was plant taken out of realloc mode? PROCESS_IND population | §10–11 |
| Batch won't run for a month / "process error" with no detail | Accounting period closed, or facility locked | Accounting Date Maintenance status; Facility Lock screen | §11 |
| PDA submission errors ("column added by qfc is required") | PDA screen defect/config | Reproduce; check greyed required fields; escalate as defect | §12 |
| Fee not applied / escalation wrong / tax calc wrong | Setup (CCT/rate schedule/escalation/tax master) | Rate Resolution Query; effective dates on the rate/escalation | §13 |
| QEMAIL/event-detector emails not sent (or doubled) | QEMAIL config (Global Redirect Email), inactive Event Detector | QEMAIL config + Event Detector active flag | §14 |
| Login/password/Okta/Citrix/access | User admin / platform | Route to Cloud Ops; internal-vs-external Okta account type | §16 |
| "Load attached Condensate GPM script" | Recurring monthly scripted data load | Standard script-deployment request to Cloud Ops | §17 |

---

## 2. Decision Tree

```
Uncategorized TIPS case arrives
│
├─ Is it about ACCESS (login, password, Okta, Citrix, new user, MFA, QCloud)?
│   └─ YES → §16. User-admin/platform. Route to Cloud Ops. (~65+ cases — biggest single bucket)
│
├─ Is it an ENVIRONMENT REQUEST (refresh, restore point, restart services, create env)?
│   └─ YES → §4 / §3. Routine Cloud Ops ticket. If something BROKE after a refresh → §4 post-refresh config.
│
├─ Is a BATCH PROCESS stuck or failed?
│   ├─ Stuck at "Queued"/"Processing", nothing moving → §3 QPEC engines (restart / rogue QPEC kill).
│   ├─ Failed with an error → §5. Get MPQID, plant, prod month, failing STEP name
│   │     (CTRMTR / STDPDA / UPDTALLOCV / SETTLEMAIN / TIPSLOCK / NBPCALC / RESALLOCGP…).
│   │     ├─ Won't even submit for the month → §11 closed accounting date / facility lock.
│   │     └─ Slow rather than failed → TIPSLOCK realloc-check & registered-SQL perf bugs (§5).
│   └─ Import/export step failed → §6 paths & file format.
│
├─ Is it a SCREEN doing the wrong thing?
│   ├─ Meter Split / Meter Def / Shared Meter / Contract Meter List → §7 (time-slice bug family).
│   ├─ PDA screens → §12.
│   ├─ Accounting Date Maintenance → §11 (also see FAQ — Add vs Update button).
│   └─ Other screen, Web vs Classic difference → reproduce in both; likely Web defect (same pattern as QPTM).
│
├─ Is it an OUTPUT problem (statement / invoice / journal / report)?
│   ├─ Verify the underlying allocated/settled DATA first (often correct; rendering/config wrong).
│   ├─ Statement/invoice → §8.  Report → §9.
│   └─ Values genuinely wrong in data → upstream §5/§6/§10.
│
├─ Is it PPA / rerun / prior-period related? → §10 (and §11 if realloc-mode involved).
│
├─ Is it fees/tax/escalation? → §13 (almost always setup, not code).
│
└─ Vague subject, audit/doc/license/quote request? → §18 expected-behavior/no-action family.
```

---

## 3. QPEC Engines / Stuck Process Queue

**~60 cases — the highest-frequency operational cluster.** QPECs are the TIPS batch-execution engines. Symptoms: jobs sit in "Queued"/"Processing" forever, reports stuck in queue, "TIPS UAT Jobs will not complete" (repeat offender), "PROD QPECs down", "QPEC SYSTEM ERROR" on TIPSMASTER, engines won't start, app-server memory leak.

- **Resolution pattern (documented):** restart the QPEC services. Case **23-00877213** (FlowCal manual import stuck at "Queued") — *"Restarted QPEC services for them and that resolved their execution process issue."* Case **23-00899661** (NRM UAT all jobs queuing since Apr 21) — *"NRM UAT services restarted successfully."*
- **Memory:** **23-00889554** (QQM hourglass) — root cause recorded as *"HIGH MEMORY ON QQM SERVER"*; **22-00666434** "TIPS Prod QPEC stopped due to memory leak" (legacy, no resolution text).
- **"Rogue QPECs"** is the current operational term — ADO Internal Issues are raised continuously to *kill rogue QPECs* per environment (e.g. #1822903 EIG, #1822888 NJR, #1821246 TGL, all June 2026). This is Cloud Ops work, not Engineering.
- A recurring sub-pattern: a *hung job* blocks the queue → client asks to "stop a hung process in processing status" → stop request sent to job queue (22-00663949 resolution: *"sent stop request to job queue for client's account"*).
- If TIPSMASTER reports a QPEC System Error rather than queue stall → see §5 (ADO #1732760 / #1741563).

**Fix recipe:** confirm environment + affected MPQID(s); check whether ANY job moves (engine-wide vs single hung job); request QPEC restart / rogue-QPEC kill / stop-request from Cloud Ops; only escalate to Engineering if the same process errors reproducibly after a clean restart.

---

## 4. Environment Refresh & Post-Refresh Breakage

**~45 cases.** Two distinct sub-types:

**4a. Routine refresh requests** ("Refresh UAT from PRD", "restore point", "Refresh DEV") — pure Cloud Ops/Data Services tickets. Confirm source→target, restore point if testing something risky (22-00663964 pattern), and any tables to purge (22-00637169).

**4b. Things break after the refresh — the actionable part:**
| Broken after refresh | Root cause | Fix | Case |
|---|---|---|---|
| Interactive (Exago) reports dead | Post-refresh scripts overrode Exago config with wrong values | Correct the Exago config setting | **23-00909196** |
| Spreadsheet volume load (LDSSVOLS) "import file not found" | QIMPEXP process step default-value override for Imp/Exp path pointed at old QCloud 1.0 path | Correct the path override on the QIMPEXP step | **23-00909948** |
| Web attachments error | FILE_SHARE_ROOT_PATH still pointing at PRD path in non-prod | Reset FILE_SHARE_ROOT_PATH to a non-prod path | **23-00899989** |
| Global Filters missing / invalid query objects | Security-objects refresh pushed invalid Query objects | Delete the invalid Query objects (UAT + PRD) | **22-00676424** |
| TEST screens erroring post-refresh | (legacy, no resolution text preserved) | — | 22-00556393 |

**Triage tip:** for ANY "X stopped working" case, ask first: *was the environment refreshed recently?* The post-refresh config-override family explains a disproportionate share of "sudden" breakage in this group.

---

## 5. Facility Batch Job Failures

**~45 cases** across ALLOCATE/CTRMTR, TIPSMASTER, TIPSLOCK, Meas→Settle/SETTLEMAIN, UPDTALLOCV, NBPCALC, RESALLOCGP, company jobs. The plant-level nightly/close chain is: measurement → Allocate → Settle → TIPSMASTER (+ TIPSLOCK/TIPSUNLOCK around it).

| Failure signature | Root cause | Fix | Evidence |
|---|---|---|---|
| Various ORA errors during ALLOCATE (CTRMTR step) | Meter Effective Dating integration scripts erroneously enabled | Disable the integration scripts | **23-00903715** (Pioneer) |
| TIPSMASTER intermittent failure on **STDPDA** step | Code defect | Fixed — ADO **#1617894** (Closed; SF 23-00913707) | EQT |
| TIPSMASTER processes not updating status correctly / QPEC System Error on TIPSMASTER | Code defects | ADO **#1741563** (Closed), **#1732760** (Pending Engineering) — SF 25-01022325 | ONEOK |
| TIPSLOCK step times out / wildly inconsistent runtimes | Reallocation-logic check; registered SQL `Select_ReallocDependTrnxIdProcessInd…` | Code/perf fix — ADO **#1683233**, **#1725292**, **#1734459** (all Closed) | ETP/EQC 2024.04 |
| TIPSLOCK errors on incorrect parameter | Step parameter config | ADO **#1533819** (Closed) | ETP 2020.03 |
| TIPSMASTER takes hours longer in UAT than PRD | UAT sizing/perf, not necessarily a defect | Compare env resources before escalating | **25-01057808** (Hess, MPQID 87325595: Allocate 3h, TIPSMASTER +3h) |
| Facility batch job hangs during execution | See §3 first (QPEC), then step-level investigation | **25-01057459 / 25-01057094** (Hess) | App-config |
| PRIMARY KEY / duplicate-key errors in ALLOCATE; "Company Job Fails in Revenue for PK Violation — Reruns ONLY"; SETTLEMAIN fails first run for a plant; Settle Tax inserting NULLs; PMA runs failing | Legacy cases (2017–2020) — **resolution pattern unclear from mined cases** (descriptions not migrated). Treat as data-script candidates; pull the failing step's SQL trace | 22-00517694, 22-00711603, 22-00608993, 22-00528197, 22-00671095 |
| Scheduled daily Measurement+Allocations job failing | (resolution not captured) — verify schedule param + acctg date first | **23-00907397** (Crestwood, app-config) |

**Fix recipe:** always collect **MPQID, plant/facility, production month, exact failing STEP name and error text**. Match against the ADO table (§19). If the step is TIPSLOCK/realloc-related, check whether the plant is in reallocation mode (§11). If duplicate-key on rerun, suspect stale rerun data (§10).

---

## 6. Volume & Analysis Import/Export Interfaces

**~40 cases.** TIPS ingests measured volumes and gas analyses from FlowCal, PI, spreadsheets (LDSSVOLS), EDF, Coastal Flow, CIS+, Avatar/Allegro/Vertex feeds; and exports statements/data outbound.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| PI data not loading into TIPS | Wrong path in the **Import/Export Definition tab** | Update the path; re-run; volumes appear in Measured Volumes | **23-00912393** (NorthRiver) |
| LDSSVOLS "import file not found" | QIMPEXP step path override pointing to old QCloud 1.0 path | Correct the default-value override | **23-00909948** |
| FlowCal vols/analysis wrong for one meter | Upstream measurement re-export needed; re-import via batch | Re-import after measurement group updates source | **25-01004490** (BSG-033) |
| FlowCal manual import stuck "Queued" | QPEC engines (not the interface) | QPEC restart | **23-00877213** |
| Analysis loaded to wrong month / not visible | **User ran load-analysis import with wrong prod-month parameter** | Re-run with correct parameter | **23-00885077** |
| Monthly analysis import failing (FTP) | sFTP folders missing / FTP Transfer setup wrong in UAT | Create folders + fix FTP Transfer setup to match PRD | **22-00636694** (IACX) |
| "Numeric value too large for column definition" on volume import; Excel/XLS import "MICROSOFT JET DATABASE ENGINE" error; duplicated volumes on upload; EDF volume not processed; gas-analysis import failures (Ringwood, Kalk) | Legacy cases — **resolution pattern unclear from mined cases**. First checks: file format/column widths, duplicate detection in staging, source-file encoding, JET/ACE driver bitness on the import server | 22-00641322, 22-00517693, 22-00617639, 22-00648568, 22-00549881, 22-00516037 |

**Fix recipe:** (1) Identify the interface + process step (QIMPEXP-based?); (2) check the Import/Export Definition path and any step default-value overrides — the #1 documented cause; (3) check the file itself (format, columns, prod month); (4) if stuck rather than failing → §3.

---

## 7. Meter Split / Meter Definition / Shared Meter / Contract Meter List

**~35 cases.** The master-data screen family with the richest defect history in this group.

### The time-slice bug family (top recipe)
- **23-00894029** (Clearfork/M6): can't remove meters from Contract Meter List — *"known bug with IP causing the meter definition time slice to end-date every month; time slices need to be updated by the user in the Meter Definition screen for the meters presenting this error."* → **Fix: repair the Meter Definition time slice, then retry the CML operation.**
- ADO **#1788087** (Closed): QCM "invalid effective date error with meters that are correctly timesliced" — same family, fixed in code (SF 26-01084783).
- Legacy echoes (no resolution text): "Contract Meter List Eff Date Error" (22-00521890), "Create new time slice while deleting row causes error" (22-00609024), "Unable to Timeslice record for K2005260" (22-00711911), "TIPS will allow two open-dated Contract Meter List records — should auto end-date" (22-00617598).

### Meter Split defects
- **Mass Change skips meters:** **25-00999486** — Mass Change applied to 223 meters, 66 came back unchanged (resolution not captured in SF; matches ADO **#1795476** "Split Decimal Not Getting Updated After Running Batch Job", Proposed for 2026.04). Also legacy 22-00555532 "Meter Split Can't Update Split Decimal".
- **Daily splits ignore Accounting Date Maintenance setup** — ADO **#1790136/#1790251** (Closed tasks, May 2026): current-month issues for daily meter splits.
- **CML/Meter Split validation gaps** — ADO **#1809771** (HVK, Proposed); **#1769433/#1780377** CML copy/paste not autopopulating required field (ETP QCM).
- **Shared Meter sync:** meters must be created via the **Shared Meter screen first**, then maintained in Meter Definition (22-00663946 resolution). Sync processes: STF FACILITYFULLSYNCALL + Meter Split Sync (22-00609036/22-00609022 — legacy, resolution unclear).
- **Non-op splits not picked up:** certain columns on the Meter Split screen must NOT be populated or the meter is excluded from non-op split processing (**22-00663950**).

**Fix recipe:** for any "can't update/delete meter X on CML/Meter Split": (1) check Meter Definition time slices for that meter (end-dated slice?), (2) check Shared Meter record completeness/sync, (3) reproduce in Web vs Classic/QCM, (4) match to the ADO items above before logging a new bug.

---

## 8. Statements, Invoices & Journals

**~40 cases**: gas statements, settlement statements, invoices, journal/SAP/Qbyte exports.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Journal Summary Report includes PPAs in current-month total | Report defect | Report change delivered in (April) hotfix | **22-00598128** (ONEOK) |
| 300 gas statements missing for a party | **BA suffix filter excluded a contract** | Exclude/fix the suffix filter; statements generate by contract party | **22-00636704** |
| Gathering Statement shows no records | No measured volume loaded → no allocation → no rows | Load volume, allocate, rerun statement | **23-00904644** |
| Statement won't open in Web but shows generated in Classic Report File Viewer | Quorum-managed report defect | Fixed via metadata delivery | **23-00893819** (MarkWest) |
| PMA value-only adjustment missing from Cash Out Detail/Summary (shows on Imbalance Summary) | Imbalance/cash-out report gap | **Resolution pattern unclear from mined cases** — verify whether value-only PMAs are expected on cash-out reports for the client config | 22-00875693 (Weld) |
| Duplicate invoice numbers / mismatching offset entries; invoice with no detail; PPA invoice errors; old BA name on invoice; wrong residue value on statements; doubled volume on IMBSTM | Legacy (2017–2020) — **resolution patterns unclear from mined cases**. First checks: invoice-number sequence config, statement format assignment, BA name effective dates, allocation data correctness before blaming the statement | 22-00517692, 22-00617694, 22-00654059, 22-00694634, 22-00536143, 22-00683326, 22-00679848 |

**Triage rule (same as QPTM reports):** verify the underlying allocated/settled data FIRST. In the documented cases the data was usually right and the statement config (filters, formats, BA setup) or the report layer was wrong.

---

## 9. Reports & Report Viewer

**~35 cases** (Crystal/Exago/CAW reports, report queue, formatting/doubling).

- **Stuck in queue / won't run at all** → §3 QPEC first (22-00679893 "Reports remain stuck in queue after QPEC restart").
- **Broken after refresh** → §4 Exago config (**23-00909196**).
- **CAW report behavior:** "Running Reports in CAW not saving to Recents" — fixed by *removing the check that filtered out reports not visible to users* (**22-00556218**). CAW Report Favorites cleared on logout (22-00562611, legacy).
- **Value doubling / wrong totals:** "KFS Reports Doubling up" (22-00642270), "Plant Summary Alloc Rep Heat Value Doubling" (22-00642241), Tier-1 component-vs-volume issues (22-00642265/67), IN01/IN02 imbalance reports not generating correct output (22-00592901/11) — all legacy, **resolution patterns unclear from mined cases**; treat as report-definition defects and check whether a newer build fixed them before re-logging.
- **myQuorum TIPS Help broken:** fix made in ProProfs (help platform), not TIPS (**23-00888628**).

---

## 10. PPA / PMA / Reruns / Rerun Purge

**~20 cases.** TIPS prior-period corrections run as **PPAs** (targeted) or **PMAs** (full plant reruns).

- **Well-level PPAs vs PMA:** some clients' gas-statement configuration forces corrections to be processed as **PMAs (full plant reruns) rather than PPAs** (**22-00636750**, IACX). Walkthrough of multi-month rerun sequence in UAT then PRD: **22-00636751**.
- **Rerun purge defects (recurring theme):** "RUN ID'S NOT PURGED PROPERLY" (22-00642311), "MISSED DATA from RERUN purge" (22-00556276), "Customer Account Adjustments & Rerun Purge" enhancement (22-00617602) — legacy, no resolution text. The MODERN, fully documented instance is the **gas-lift purge bug**, §11 below.
- **Core factor with reruns:** MCFAVG3MO not returning correct volumes when reruns involved (22-00530906 — legacy, unresolved text).
- "Delete a PPA Run" / "PPA Advance not working" / "Meter Double Reversed for PPA month" (22-00520116, 22-00588417, 22-00607736) — **resolution patterns unclear from mined cases**.

---

## 11. Accounting Date / Month Close / Facility Lock / Reallocation Mode

**~12 cases but disproportionately important** — this is where the best-documented defect in the whole group lives.

### The reallocation-mode mechanism (from case 25-01016940, verbatim-grade detail)
> During TIPSLOCK, TIPS sets **`PROCESS_IND` in `QTRAN_TRNX_ID`** based on reallocations logged in **`QTRAN_PLANT_STATUS_REALLOC`**, which determines which meters get processed when running in reallocation mode.

### Gas Lift doubling bug — ADO #1734347 (Closed)
**25-01016940** (ETP, Eagleford): Automated Gas Lift (**ASCGLM**) records were **not purged when rerunning the plant in reallocation mode** (plant not taken out of realloc mode on the Facility Lock screen first) → the same ASCGLM records regenerate → **gas lift volumes doubled**. Repro: run Meas→Allocate out of realloc mode, change a volume, rerun WITHOUT taking the plant out of realloc mode. Fixed under ADO **#1734347** (also SF 25-01023169). Code home: `Quorum.TIPS.ClassicBatch /Common/QPDllTipsMeasurement/QSQL_AsscGLMVolumes.cpp`; TurboTips `psMEASGLVOL.cs` (MEASGLVOL process).

### Other recipes
- **Batch won't run for a month at all:** the accounting period is **closed** — *"April Accounting period is closed and that's why they are not able to run any batch process for April"* (**22-00876327**). Check Accounting Date Maintenance before debugging anything else.
- **Accounting date didn't roll to Billing:** Facility Type on Facility Definition must be **Processing** (not G&P) for POSTRESULT to roll the date to Billing instead of Scheduling (**22-00642365**, Roswell).
- **"Cannot schedule processes without taking plant out of realloc mode"** (22-00679895), **"Please Unlock Plant"** (22-00520118), facility lock after errored plants (22-00603751) — operational realloc/lock handling; the Facility Lock screen is the control point.
- **Mistakenly closed period** (22-00869169) — resolution not captured; treat as reopen-request via standard close-reversal procedure (confirm with Engineering before any manual date flip).

---

## 12. PDA (TIPS-side) Issues

**~10 cases.** (TIPS PDAs split volumes at meters — distinct from QPTM PDA Submission; see SKILL_Allocations.md §5 for the QPTM side.)

- **25-01013604:** new PDA submission fails with **"column added by qfc is required"** and required-looking fields are greyed out — screen/metadata defect pattern; resolution not captured in SF. Reproduce, capture screenshot, check whether client metadata layer added a required column (the error text says a **QFC-added column** is required) — that points at grid/metadata configuration in the client's `<CLIENT>.TIPS.Metadata` overlay rather than core code.
- **26-01089637:** trouble adding a contract to a downstream PDA — resolution not captured.
- **22-00679864 (Harvest):** *"PDA validation not looking at correct time periods in CAW"* — **code change made** (tagged Software Defect).
- Legacy: "Rounding PDA Splits" (x3, 22-00516106/153/154), "Delivery Meter not allocating based on PDA percentages" (22-00603710), sysgen `QCTRL_ALLOC_PDA` row deletes during package deploys (22-00519692) — **resolution patterns unclear from mined cases**.

---

## 13. Fees, Taxes, Escalations & Rate Schedules

**~25 cases.** Almost always **setup**, not code:

- **H2S Treating Fee not applied** (4 linked legacy cases 22-00519663/65/66/689) — resolution text not migrated; first check the fee's CCT/rate-schedule effective dates and meter applicability.
- "Fees not charging on all meters under a GCR" (22-00679880), "Minimum Monthly Fee Calculation" (22-00588458), "Minimum Volume Fee Issue on CCT" (22-00516039), Escalation setup issues (22-00530811, 22-00528163, 22-00541581), "Rate Schedule Wrong Formula Displayed" (22-00609027), Kansas Severance / Oklahoma tax / North Dakota tax screen errors, "Ticket Level Tax Needs to factor in Exempt Decimal" (22-00685998) — legacy, **resolution patterns unclear from mined cases**.
- **OTC manual adjustments (modern):** reversals entered on the **OTC Manual Adjustments screen** are picked up by the OTC recon report after running regulatory jobs (**25-01029444**, P66 — KB attached to that case).
- **Attribute formulas:** allocation "wrong" because the **wrong column was selected in the attribute formula** setup (**23-00881611**) — config, user-fixable.

---

## 14. QEMAIL / Notifications / Event Detectors

**~12 cases.**

- **23-00903543** (M6) — QEMAIL not sending: (1) **Global Redirect Email** in QEMAIL configuration was set to a dummy address (NotReal@Qbsol.com) — correct it; (2) the **Event Detector setup for BRPTEMAIL was not active** — activate it. The canonical two-point check for any "emails not going out".
- "System Sending out Double Emails" (22-00694636), "QPEC Notifications Emailed Every 10 mins" (22-00671087), "Post-go-live: QEMAIL job failing" (22-00607716), batch-failure notifications not triggering (22-00686098), external users not receiving emailed reports (22-00683320) — legacy, **resolution patterns unclear**; start with the same QEMAIL config + event-detector-active check, then SMTP relay.

---

## 15. Archive / Purge

**~12 cases.** Recurring asks: review/verify archive definitions (24-00946454), archive posted data to fix **close-period performance** (**26-01104023**, AltaGas — client has a historical Quorum-provided archiving script they want re-validated), archive validation triggering errors incorrectly (22-00530857), purge runs broken in v16 (22-00642227), non-latest archiving setup (22-00592952, 22-00586281), restore-from-archive errors (22-00586355). Modern resolution path: validate the client's archive script against current schema, then deploy via the script-deployment process (§17). **Resolution patterns for the legacy purge defects unclear from mined cases.**

---

## 16. User Access / Login / Okta / Citrix / QCloud

**~65+ cases — the single biggest bucket, and almost entirely Cloud Ops routing.** Password resets, account unlocks, new-user setup, MFA, Citrix login errors, "Unable to initialize the QFC.Net UI Environment", AD Manager, activation emails.

Worth keeping (actual technical recipes):
- **External user sees internal apps (or vice versa):** the QCloud **Okta account type** was wrong — flip internal↔external on the Okta account (**23-00887811**: account was created as INTERNAL Clearfork; changed to external → only the client PRD web app visible).
- **External users don't appear in Okta admin views** — expected (23-00905981 explanation).
- **Users locked in BOTH QCloud AD and the TIPS application** — unlock both (22-00636657); password complexity requirements often the real blocker (22-00636650).
- **Security to limit users to specific Co/Region/Plant** (22-00711963/45) — TIPS security-group configuration request, not a defect.
- Screen privilege errors ("unable to add to Contract Meter List — security") → grant the screen priv to the user's TIPS group (**23-00893813**: added privs to group "TIPS Regular User").

---

## 17. Recurring Scripted Data Loads

**~10 cases.** Some clients run monthly **data-load scripts via the support queue** — the canonical one: **"Monthly Condensate GPM script"** (23-00897614, 23-00891709, 23-00902703, 23-00911261, 23-00912794, 23-00881805 — Platform/Data-Loader root cause). Resolution is always: *"Script deployment request, script deployed successfully in production environment."* Treat as routine: validate the attached script (read-only review), pass to Cloud Ops script deployment, confirm row counts. Same machinery for one-off data-cleanup scripts (22-00665254 SVALD/QVALD cleanup, 22-00688816 truck-ticket analysis update).

---

## 18. Expected Behavior / User Education FAQ

From the 40-case Training/Customer Error sample (~74 such cases in the group):

| Reported as | Reality | Case |
|---|---|---|
| "Update button missing on Accounting Date Maintenance" | The Update button only appears when records EXIST for that accounting date; you must **Add** records first — Add and Update are different buttons | **23-00876631** |
| "TIPS process error / can't run batch for month X" | The accounting period for month X is **closed** | **22-00876327** |
| "Gathering Statement shows no records" | No measured volume loaded → nothing allocated → nothing to report | **23-00904644** |
| "Analysis didn't load / comp query empty" | Import was run with the **wrong production-month parameter** | **23-00885077** |
| "Allocation is wrong" | Wrong **column picked in the attribute formula** setup | **23-00881611** |
| "Accounting date didn't roll to Billing" | Facility Type must be **Processing** (not G&P) for POSTRESULT to roll to Billing | **22-00642365** |
| "Non-op splits not working" | Certain Meter Split columns must be left blank or the meter is excluded from non-op split processing | **22-00663950** |
| "Can I close production months out of order?" | Possible but risky — unexpected results; test in UAT with a restore point | **22-00663964** |
| "Copying query data takes 5–10 minutes" | Narrow the query — less data copies faster | **22-00642377** |
| "Can't find meter in Meter Definition" | Meters must be created through the **Shared Meter screen** first; extra tabs are enabled via the available-tabs dropdown | **22-00663946** |

---

## 19. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1734347** | Bug / **Closed** | ETP — Automated Gas Lift Records Not Purged (realloc-mode rerun doubling) | §11 | 25-01016940, 25-01023169 |
| **#1617894** | Bug / **Closed** | EQT — TIPSMASTER STDPDA step fails intermittently | §5 | 23-00913707 |
| **#1741563** | Bug / **Closed** | ONM — TIPSMASTER processes not updating status correctly | §5 | 25-01022325 |
| **#1732760** | Bug / **Pending Engineering** | ONK — QPEC System Error on TIPSMASTER process | §5 | 25-01022325 |
| **#1683233** | Bug / **Closed** | TIPSLOCK step timing out on reallocation logic check | §5/§11 | — |
| **#1725292 / #1734459** | Bug / **Closed** | ETP/EQC 2024.04 — Inconsistent TIPSLOCK runtimes (Registered SQL `Select_ReallocDependTrnxIdProcessInd…`) | §5 | — |
| **#1533819** | Bug / **Closed** | ETP 2020.03 — TIPSLOCK error from incorrect parameter | §5 | — |
| **#1683217** | Bug / **Resolved** (pending hotfix) | GLC — CLREALLOC step added to TIPSMASTER | §5/§11 | — |
| **#1788087** | Bug / **Closed** | UPC — QCM invalid-effective-date error on correctly timesliced meters | §7 | 26-01084783 |
| **#1795476** | Bug / Proposed | 2026.04 beta — Meter Split decimal not updated after batch job | §7 | (25-00999486 same symptom) |
| **#1790136 / #1790251** | Task / **Closed** | Daily Meter Splits don't respect Accounting Date Maintenance setup | §7 | — |
| **#1769433** (Closed) / **#1780377** (Active) | Bug | ETP QCM — Contract Meter List copy/paste not autopopulating required field | §7 | — |
| **#1809771** | Bug / Proposed | HVK — Validation for CML and Meter Split | §7 | — |
| **#143559 / #143560** | Req+Task / **Closed** | Pembina — LDSSVOLS spreadsheet volume import converted to MSSQL | §6 | — |
| **#1822903, #1822888, #1821246, …** | Internal Issues (ongoing) | "Kill rogue QPECs" per environment — standing Cloud Ops pattern | §3 | — |
| **#1316471** | Requirement / Proposed | Document TIPSMASTER / TIPSLOCK / TIPSUNLOCK in KB | §5 | — |

---

## 20. Key Tables, Processes & Repos

### Processes / steps seen in this group
| Process / step | Purpose |
|---|---|
| **TIPSMASTER** (steps incl. STDPDA, CLREALLOC) | Master plant batch chain; **TIPSLOCK / TIPSUNLOCK** bracket it (lock + realloc determination) |
| **ALLOCATE** (CTRMTR step), UPDTALLOCV, RESALLOCGP, RESGRMTRS, RESMTRLIST | Allocation chain & supporting resolves |
| **SETTLEMAIN / Meas→Settle**, NBPCALC, GATHRATES, PRICETOSCH | Settlement / pricing |
| **MEASGLVOL** (gas lift), Daily Measurement Standardization, Truck Ticket Standardization | Measurement derivations |
| **LDSSVOLS** (spreadsheet vols), **LDGANLES** (gas analysis), QIMPEXP-based interfaces, FlowCal / PI / EDF / CIS+ imports | Volume & analysis I/O |
| **QEMAIL** + Event Detectors (e.g. BRPTEMAIL, NOMCHGEXT) | Notifications |
| STF **FACILITYFULLSYNCALL**, Meter Split Sync | Shared-meter/facility sync (eSuite↔TIPS) |

### Tables (confirmed from case text / code search)
| Table | Purpose |
|---|---|
| **`QTRAN_TRNX_ID`** (`PROCESS_IND`) | Which meters get processed in reallocation mode — set during TIPSLOCK |
| **`QTRAN_PLANT_STATUS_REALLOC`** | Logged reallocations driving the PROCESS_IND determination |
| `QTRAN_ALLOC_VOL` | Allocated volumes (seen in TurboTips test data) |
| `QARCH_CTRL_PROC_PROCSTEP`, `QARCH_CTRL_PROCESS_STEP_PARAM` | Batch process/step definitions + parameters (where step path/param overrides live; per-client values in `<CLIENT>.TIPS.Metadata` repos) |
| `QCTRL_* / QHIST_*` → `SCTRL_* / SHIST_*` (+ `QARCH_TRAN_SEQ`) | QCM→eSuite migrations (Well tab data, 25-01002905) — watch sequence collisions |
| `QCTRL_ALLOC_PDA` | TIPS PDA rows (sysgen deletes during deploys, 22-00519692) |
| `QPOST_PAYSTATION_EXEMPT` | Pay-station exempt data (duplication case 22-00556297) |
| Code table 4011 `PTIP_CODE_STMT_IFACE` | Statement interface codes (22-00649115) |

### Repos
- **Quorum.Tips.TurboTips** (modern batch engine — e.g. `Quorum.Tips.TurboTips.Measurement/MEASUREMENT/MEASGLVOL/psMEASGLVOL.cs`)
- **Quorum.TIPS.ClassicBatch** (C++ legacy batch — `QPDllTipsUtility/QPSDllTipsLockPlant.cpp` = TIPSLOCK; `QPDllTipsMeasurement/QSQL_AsscGLMVolumes.cpp` = gas-lift ASCGLM)
- **`<CLIENT>.TIPS.Metadata`** (IPF, PEP, CMP, XMG, SRB, …) — per-client process-step config (`QARCH_CTRL_PROC_PROCSTEP` JSON); check the client overlay before assuming core behavior.

---

## 21. Diagnostic SQL

> Column names below are confirmed only where stated in §20; verify against the client schema before scripting. Salesforce note for queue mining: `Resolution__c` cannot appear in a SOQL WHERE clause; LIKE is case-insensitive.

### A. Is the plant in reallocation mode / what will reprocess? (gas-lift doubling check, 25-01016940)
```sql
SELECT * FROM QTRAN_PLANT_STATUS_REALLOC
WHERE  PLANT_NO = <PLANT> AND PROD_DT = '<PROD_MTH>';

SELECT TRNX_ID, PROCESS_IND          -- PROCESS_IND set during TIPSLOCK
FROM   QTRAN_TRNX_ID
WHERE  PLANT_NO = <PLANT> AND PROD_DT = '<PROD_MTH>';
-- If rerunning after a volume change, the plant must be taken OUT of realloc mode
-- on the Facility Lock screen, or only changed meters reprocess (and pre-fix builds
-- double ASCGLM gas-lift records — ADO #1734347).
```

### B. Find the failing step + parameters for a batch run
```sql
SELECT ps.PROCESS_ID, ps.STEP_NO, ps.STEP_ID
FROM   QARCH_CTRL_PROC_PROCSTEP ps
WHERE  ps.PROCESS_ID = '<PROCESS e.g. TIPSMASTER>'
ORDER BY ps.STEP_NO;

SELECT * FROM QARCH_CTRL_PROCESS_STEP_PARAM
WHERE  PROCESS_ID = '<PROCESS>'              -- look for default-value overrides:
;                                            -- wrong Imp/Exp paths live here (23-00909948)
```

### C. Duplicate gas-lift (ASCGLM) records after a realloc-mode rerun
```sql
-- Shape: count gas-lift source records per meter/day for the prod month; >1 of the
-- same record = the doubling signature (exact table name from client schema; the
-- ASCGLM write path is QSQL_AsscGLMVolumes.cpp / psMEASGLVOL.cs).
```

### D. Salesforce — find prior art for an uncategorized TIPS case (run in SF, not the client DB)
```sql
SELECT CaseNumber, Subject, Status, CreatedDate
FROM Case
WHERE Product_list__c = 'My Quorum TIPS' AND IsClosed = true
  AND Subject LIKE '%<process/screen keyword>%'
ORDER BY CreatedDate DESC LIMIT 20
-- Remember: cases created before ~mid-2022 have empty Description/Resolution.
```

---

## 22. Escalation Guidance

```
WHO FIXES WHAT (this group's dispositions):

CLOUD OPS (no Engineering needed):
  - QPEC restarts, rogue-QPEC kills, stop-requests for hung jobs        (§3)
  - Environment refreshes, restore points, env creation                 (§4)
  - Script deployments (Condensate GPM, data cleanups, archive scripts) (§15, §17)
  - All access/login/Okta/Citrix/AD/password work                       (§16)
  - Post-refresh config repairs (Exago, FILE_SHARE_ROOT_PATH, Imp/Exp paths) — L4 diagnoses, Cloud Ops applies

L4 CONFIG / CLIENT-FIXABLE (diagnose, then guide or apply config):
  - Import/Export Definition paths & QIMPEXP step overrides             (§6)
  - Meter Definition time-slice repair to unblock CML                   (§7)
  - QEMAIL Global Redirect Email + Event Detector active flags          (§14)
  - Facility Type / POSTRESULT accounting-date roll; facility lock /
    realloc-mode handling; closed-period explanations                   (§11)
  - Fees / escalations / tax setup; attribute formula columns           (§13)
  - Statement filters (BA suffix), statement format assignment          (§8)

ENGINEERING (log/attach to an ADO bug — confirm it's not already fixed):
  - TIPSMASTER/TIPSLOCK step failures & perf (match §19 first)          (§5)
  - Meter Split / CML defect family (#1795476, #1788087, #1769433...)   (§7)
  - Realloc-mode purge defects (gas-lift #1734347 pattern)              (§10/§11)
  - PDA screen "column added by qfc is required" class errors           (§12)
  - Reproducible report-engine defects after data verified correct      (§8/§9)

RED FLAGS that it is NOT a defect:
  - Environment was just refreshed (config override, §4)
  - Accounting period closed / plant locked / realloc mode (§11)
  - Wrong run parameter (prod month) on an import (§6, FAQ)
  - It's one of the ~65 access cases or ~45 refresh cases → routine ops
```

---

*Skill created: 2026-06-11 from the Uncategorized_Sweep mining pass (1,336 closed TIPS cases; 43 tagged actionable + 890 untagged subjects clustered + 40 Training/Customer-Error samples).*
*ADO cross-refs: #1734347, #1617894, #1741563, #1732760, #1683233, #1683217, #1725292, #1734459, #1533819, #1788087, #1795476, #1790136, #1790251, #1769433, #1780377, #1809771, #143559, #143560, #1316471.*
*Known gaps: legacy (pre-mid-2022) cases carry no Description/Resolution in SF, so several legacy clusters are flagged "resolution pattern unclear from mined cases" — enrich them as fresh instances arrive.*
*Companions: SKILL_Allocations.md (QPTM allocation/PTR overlay), SKILL_EDI_Troubleshooting.md.*
