# SKILL — FLOWCAL Family: Reports & Report Scheduling

> **Product family:** FLOWCAL (desktop 7.x–10.9), TESTit 2.x/3.x, PROVEit 9.x · Coverage-plan group #2
> **Sources:** Salesforce all-history mining 2026-09-02 (`Product_list__c IN ('FLOWCAL','TESTit','PROVEit')`, ~110 cases surveyed, 32 sampled at resolution depth) + ADO org `QuorumSoftware` (projects `Quorum`, `QuorumSoftware`, `myQuorum Cloud`).
> **Auto-Bot** — the L4 issue solver built by **Aditya Bhagat**.
> Fixed-in builds are **INFERRED** from SF resolutions unless marked release-notes-CONFIRMED.

---

## 1. Quick Triage

| Symptom (verbatim signatures) | Likely cause | § |
|---|---|---|
| Scheduled reports stopped going out; Service Monitor Reports tab red; "I think the service is just not on" | FcSrvReports down/stuck — stuck schedule, duplicate queue entry, expired Oracle password, memory bloat | §3 |
| `Unknown error (-1). - 2086` in FCSRVREPORTS log, service fails ~monthly | Report service memory spike when exception count > ~500k records — fixed 10.5.0.18 | §3.4 |
| `FcSrvReports is not working - Unable to access the export dll export\FCTextFileExchange.dll` after 10.6→10.7/10.8 upgrade | Upgrade script missed case-variant rows renaming FcTextFileExchange→GasTextFileExchange | §4 |
| Report Service crash, `_FC_SRV_REPORTS.LOG: "Terminated while running"` on Balance Detail (Calc) / Location Balance Detail Partial 2020.rpt | Known defect emailing that report via scheduler — fixed 10.8.0.10 | §3.2 |
| FcSrvReports.exe crash `0xc0000374` (ntdll.dll) on 10.8 when report uses an export DLL; pure Crystal report OK | 10.8 DLL-report defect (ADO 1746775); also SAP Crystal runtime 39 investigation | §3.3 |
| `Error 1209-999: Unable to send email`; schedules go to Holding after retries; `-1027` on email | SMTP config/credentials (QCloud: O365 → mailgun swap; SMTP password rotation) | §5 |
| `Unknown error (-1). - 4290` / `- 4299` + `Invalid report location: ...\Crystal\<name>.rpt` | Bad/stale .rpt files in `Crystal\<SCHEMA>` folder, or orphaned schedule rows — archive .rpt / recreate schedule | §6 |
| `See exception file for errors.` + FCREPORTS.DLL `CReportGroupScheduler FailAReport/RunAnExport` stack | Scheduled report file path invalid for the service account (mapped drive letter / missing share permission) | §6.2 |
| `Unable to open the Report Schedule Parameters table` in _FC_SRV_REPORTS.LOG | Missing/incomplete schedule parameter configuration rows — re-save each schedule | §6.3 |
| Report shows wrong/missing data (meter missing, meters duplicated, Original Revision returns Current, blank rows) | Data-side: rollups pending, characteristics gap, revision-option defect, report-version defect | §7 |
| `CrystalDecisions.CrystalReports.Engine.LogOnException: Log on failed.` on TESTit print preview | Missing ODBC connection on the workstation | §8.1 |
| `External exception EEFFACE` opening reports screen | Date/Time UI component defect ≤10.4.x — fixed 10.5.0.0 | §8.2 |
| `Page header or footer longer than a page.` at `<PEStartPrintJob>` | Legacy/corrupt .rpt layout (seen on FLOWCAL 7.x) — upgrade path | §8.3 |
| Rollup Viewer blank records after close; `Unable to find column -32000 <PPA ...>` log spam; Volume Editor ≠ Rollup Viewer totals | Rollup data defects / rollup_report_id corruption — Recalc Rollup IDs recipe | §9 |
| TESTit monthly schedule skips the current month (3/2 create for 3/15 → runs 4/15) | TESTit ≤3.16 scheduler defect — fixed 3.17 | §10.1 |
| TESTit Plate Change report fails only via Report Scheduler | TESTit 3.x defect — fixed in later 3.x | §10.2 |

## 2. Decision Tree

```
Report problem reported
├─ NOTHING generating (all schedules dead)?
│   ├─ Service Monitor > Reports tab red / service stopped → §3.1 restart drill
│   │    ├─ dies again immediately after restart → look for stuck/poison schedule (§3.1 step 4)
│   │    ├─ log shows "Unable to access the export dll ...FCTextFileExchange.dll"
│   │    │    and client recently upgraded 10.6→10.7/10.8 → §4 rename-fix SQL
│   │    ├─ log shows "Terminated while running" + Balance Detail (Calc) → §3.2 (fixed 10.8.0.10)
│   │    ├─ Windows event: FcSrvReports.exe 0xc0000374, report uses a DLL → §3.3
│   │    ├─ log shows "Unknown error (-1). - 2086", recurring ~monthly → §3.4 (fixed 10.5.0.18)
│   │    └─ Oracle "password will soon expire" around the same time → §3.5
│   └─ service RUNNING but queue stuck "Running"/"Holding" → clear Failed/Crystal tabs,
│        delete + recreate the stuck schedule (§3.1 step 4-6)
├─ ONLY EMAIL delivery failing (file output works)?
│   → §5: 1209-999 / -1027 → SMTP settings & credentials (QCloud: escalate, mailgun swap);
│     TIPS/DLL export writes file but never emails → known defect family ADO 1319619/1412392
├─ SPECIFIC schedule failing (-4290 / -4299 / "Invalid report location") → §6
├─ Report RUNS but data wrong/missing → §7 (check rollups current FIRST, then §7 recipes)
├─ Preview/print error on client PC (LogOnException / EEFFACE / page header) → §8
├─ Rollup Viewer display/mismatch problem → §9
└─ TESTit/PROVEit scheduler or report-specific → §10
```

Gate mapping: §3.1/§3.5/§5/§6 are usually **G2 Config**; §3.2/§3.3/§3.4/§4/§8.2/§9.1/§10 are **G3 Version (already fixed)**; §7/§9.3 are **G4 Bad Data**; unfixed crashes route **G5 Code**.

---

## 3. Cluster: FcSrvReports service down / crashing / stuck

The report scheduler is the Windows service **FcSrvReports.exe** (UI: Reports → Scheduling; queue tabs: Scheduled Reports / Failed Reports / Crystal Reports under Reports → Status; statuses Ready / Running / Holding). Log: **`_FC_SRV_REPORTS.LOG`**. Debug technique used by engineering: run `FcSrvReports.exe /run_as_app` (ADO 1776732).

### 3.1 Standard restart drill (service dead or queue jammed)
Signature: schedules silently stop; Service Monitor shows red on Reports tab; customers say "reports didn't go out last night".
Recipe (assembled verbatim from SF 26-01112597, 26-01104369, 26-01101336, 22-00605475):
1. Restart the FcSrvReports service (QCloud-hosted: cloud team restarts — SF 26-01101336, ADO Incident 1687067, 1772149 pattern).
2. If it dies again, open Reports → Status: clear the **Failed Reports** and **Crystal Reports** tabs (SF 26-01112597).
3. Look for **duplicate** scheduled-report rows in the queue — delete duplicates (SF 26-01112597).
4. Identify the schedule the service dies on (last entry in `_FC_SRV_REPORTS.LOG` before crash). **Delete that schedule and have the user recreate it** — poison-schedule pattern confirmed in SF 26-01104369 ('APCI Liberal Daily Report'), 22-00605475.
5. Verify runs resume for 24–72 h (SF 26-01104369 confirmed after 72 h).
Prevention: a stuck **export** (e.g. TIPS Noon export in queue for days) can wedge the whole report service — put the export on hold / recreate its schedule (SF 24-00979697; the ops incident was ADO 1687067 `24-00979697 SCT FC PRD - Report service failure`).

### 3.2 "Terminated while running" — Balance Detail (Calc) email crash
Signature: FcSrvReports crashes each time a schedule using Crystal report **Location Balance Detail Partial 2020.rpt** (UI name *Balance Detail (Calc)*) is emailed; writes to file OK; 1st–3rd runs crash with queue flapping Running→Failed→Running, 4th lands in Holding; `_FC_SRV_REPORTS.LOG: Terminated while running` (ADO 1814424 repro table).
Root cause/fix: defect in scheduler email path — **ADO 1814424** (R1080* PORT, Closed), **1845098** (DEV, Closed), **1845099** (R1090 PORT, New at survey). SF 26-01104125 resolution: **fixed in FC 10.8.0.10** (INFERRED) — customer must upgrade.
Workaround while unpatched: schedule the report to file and mail it outside FLOWCAL, or run/email manually (manual email works — ADO 1814424).

### 3.3 10.8 DLL-report crashes / Crystal runtime 39
Signature: on 10.8, any scheduled report that goes through an **export DLL** kills the service; Windows event `Faulting application name: FcSrvReports.exe ... Exception code: 0xc0000374` (ntdll.dll heap corruption); report left in Running; a pure-Crystal report processes fine — **ADO 1746775** `[AHT 10.8] Report Service failing reports with DLLs` (Closed, tag 10.8 MF).
Related: **ADO 1776732** `Investigate Report service crash with new runtime` — SAP Crystal **runtime 39** suspected on 10.8/10.9, but engineering reproduced the crash on both runtime 37 and 39 (build 10.8-130), so not runtime-specific. Same family: EOG TOW / ALNG exports hang FLOWCAL — **ADO 1745450** (R1080* PORT, Closed).
Liquid volume statement variant: SMM LVS Daily Total Fluid 2016.rpt crashing the service — SF 26-01119134, **fixed in FLOWCAL 10.8.0.10** (INFERRED).

### 3.4 Recurring monthly failure — `Unknown error (-1). - 2086`
Signature: FCSRVREPORTS fails roughly every ~28–35 days; log `Unknown error (-1). - 2086` (SF 26-01108372, client on 10.5.0.6 — the case description includes an 11-event timeline).
Root cause: known Reports Service issue — **memory spike when the exception count exceeds ~500,000 records**. Fix documented in **FLOWCAL 10.5.0.18** (INFERRED; SF 26-01108372 resolution). Interim: keep the exception backlog worked down (Exception Resolver) and restart the service when the error appears. Note: the same -2086 subcode also appears on schedule-output failures (SF 26-01064683) — read the surrounding log lines before assuming this cluster.

### 3.5 Oracle password expiry takes down all report runs
Signature: reports stop + `Oracle password will soon expire` warnings (SF 22-00667398).
Recipe (verbatim from SF 22-00667398): stop **all** FC services → update the DB password → update the **service config** with the new password → start ONE service and verify → start the rest.

## 4. Cluster: Post-upgrade `FCTextFileExchange.dll` breakage (10.6 → 10.7/10.8)

Signature: after upgrading from FLOWCAL ≤10.6 to 10.7/10.8 with **scheduled exports** configured, FcSrvReports stops with `Unable to access the export dll export\FCTextFileExchange.dll` (SF 26-01103514); Service Monitor Reports tab red.
Root cause (CONFIRMED via ADO 1814982 `10.7 Upgrade script change`, Closed): the 10.6.0.17→10.7 upgrade script renames FcTextFileExchange → **GasTextFileExchange** in `fc_report_group`, `fc_report_schedule`, `fc_report_list`, but the original UPDATEs lacked `UPPER()` on the match, so case-variant rows were left pointing at the removed DLL. Corrected statements (verbatim from ADO 1814982, `fc-migration\FLOWCAL Incremental\FLOWCAL 10\10.7\__updateDB_10.6.0.17_to_10.7.0.0.sql`):

```sql
UPDATE fc_report_group    SET group_name = 'GasTextFileExchange'            WHERE UPPER(group_name) = 'FCTEXTFILEEXCHANGE';
UPDATE fc_report_schedule SET group_name = 'GasTextFileExchange'            WHERE UPPER(group_name) = 'FCTEXTFILEEXCHANGE';
UPDATE fc_report_list     SET report_name = 'GasTextFileExchange'           WHERE UPPER(report_name) = 'FCTEXTFILEEXCHANGE';
UPDATE fc_report_list     SET report_location = 'Export\GasTextFileExchange.dll' WHERE UPPER(report_location) = 'EXPORT\FCTEXTFILEEXCHANGE.DLL';
COMMIT;
ALTER TABLE fc_report_schedule ENABLE CONSTRAINT fc_rptsch_f_group_name;
```

Diagnostic first (used by engineering on ADO 1814424): `select * from fc_report_list where UPPER(report_location) like '%EXCHANGE%';`
Anchors: SF 26-01103514 (Software Defect; "related to the FLOWCAL upgrade scripts for customers who upgraded from 10.6 or earlier to 10.8 with scheduled exports"), ADO 1814982. Related export-content defect (not service crash): ADO 1801851 `26-01092643- FcTextFileExchange Export Issue`.

## 5. Cluster: Scheduled report EMAIL delivery failures

SMTP is configured under **Reports → Report Scheduler → Configuration** (ADO 1814424 / 1412392 repro steps).

### 5.1 `Error 1209-999: Unable to send email` / schedules parked in Holding
Signature: email schedules fail repeatedly then go to **Holding**; Scheduled Reports screen shows `Error 1209-999: Unable to send email` (SF 26-01092264).
Fix (QCloud): cloud team changed the SMTP relay **from Office 365 to mailgun**; delivery resumed (SF 26-01092264 — an ADO incident was raised). Self-hosted equivalent: validate SMTP host/port/auth from the report server.

### 5.2 SMTP credentials rotated / expired
Signature: "Report Scheduling service not running *urgent*" — customers not receiving automated reports; recurs after ~a month (SF 25-01061248, duplicate 25-01061037).
Fix: **SMTP credentials updated** — ADO Incident 1772149 `25-01061248 - SEM FC PRD - Reports not sending` (Global Cloud Ops, Closed).

### 5.3 Writes file but never emails (export DLL schedules)
Signature: schedule with file+email output: file lands on disk, email never sent, schedule vanishes from failed AND successful lists; `-1027` on email attempts (SF 26-01064683 companion symptom).
Known defect family: **ADO 1319619** (R1010* PORT) / **1412392** (Dev, tag 10.4.0.0) / **1412396** (R1020 PORT) / **1412397** (R1030 PORT) `Running Scheduled Tips Export Causing Report Service to Fail` — all Closed. Repro used `StndTIPS.dll` export with email recipient; service crashed after writing output.
Workaround seen in the field: point the schedule at a different report/export variant — SF 26-01064683 resolved errors `-1027` (email) / `-2086` (file) by switching the schedule to the **GVS 2008** report.

## 6. Cluster: Schedule/config errors (-4290, -4299, paths, parameters)

### 6.1 `Unknown error (-1). - 4290` — stale .rpt files in the schema Crystal folder
Signature: all distributions stop; failure reason `unknown error (-1) - 4290` (SF 26-01105526).
Fix recipe (verbatim from SF 26-01105526): 1) stop FCSRVREPORT service; 2) archive (move out) the .rpt files in `C:\FCAPPS\FLOWCAL-RW\Crystal\<SCHEMA>\` that the failing schedules use (case list: Meter Daily Cross tab 2016.rpt, Analysis Summary (C6)/(Mole) Meter Daily 2016.rpt, Daily Meter Summary 2016.rpt, GVS Daily 2016.rpt, Liq Volume Summary Total Fluid - Meter Daily 2016.rpt); 3) start the service (it re-resolves clean copies).

### 6.2 `See exception file for errors.` — file path not reachable by the service account
Signature: `_FC_SRV_REPORTS.LOG` entry with stack `FCREPORTS.DLL CReportGroupScheduler FailAReport / RunAnExport / RunAFailedReport` + FCDBSECURITY.DLL LogMessageToFile (SF 26-01115272, 10.4.0.6).
Root cause: scheduled report File Configuration pointed at a path the **service account** cannot resolve. Two rules from the resolution: (1) the FcSrvReports service account must have permissions on the output path; (2) use **full UNC paths** (`\\Server\Share\Folder`) — mapped drive letters are not visible in service context.

### 6.3 `- 4299` / `Invalid report location` and `Unable to open the Report Schedule Parameters table`
- `Invalid report location: <path>\Crystal\GVS Daily.rpt` + `Unknown error (-1). - 4299` → schedule rows reference a missing .rpt; support ran SQL to find the bad schedules, then **deleted and recreated the report schedules** (SF 22-00605475).
- `Unable to open the Report Schedule Parameters table` in `_FC_SRV_REPORTS.LOG` → schedule parameter rows missing/corrupt; customer fixed it by **re-opening and re-saving each scheduled report** after a config-audit query from support (SF 26-01104467).

## 7. Cluster: Report data wrong or missing (report runs fine)

Order of checks — cheapest first:
1. **Are rollups current?** Reports read rollup tables. "Data not coming in the reports / only 18 rows" → FcSrvMtrRollup was bloated at >2 GB RAM; restart all FC services, confirm no pending rollups (SF 26-01115419). Location GVS missing meter runs → rollup/Service-Monitor crash window; treat recurrence as critical, engage cloud team for service + server resources (SF 25-01028604).
2. **Meter absent from Meter Monthly Summary although active with volume** → gap in the meter **characteristics**; run the **duration fix tool** (SF 25-01042348).
3. **Meters duplicated on Balance reports** (totals still correct) → version-specific report defect; workaround: use **Balance Detailed Calc** report; fix: upgrade (SF 25-01016365; data verified clean — contract hours aligned).
4. **BLM Gas Volume Statement ignores "Original Revision"** and returns Current revision → defect **fixed in 10.7** (INFERRED; SF 24-00953444).
5. **BLM Meter Sample/Analysis report missing GQ fields** → known bug fixed in **10.5.0.2+ / 10.5.0.5 / 10.6.0.0** (INFERRED; SF 24-00974092). Workaround: disable the GQ source assignment and re-enable; last resort purge the meter's volume and re-load.
6. **BLM Analysis flow rate blank** → configuration-side (SF 26-01120078, Application Configuration; no published recipe — check meter flow-rate source config before escalating).
7. Location Balance report vs rollups imbalance → ADO 1805244 `22-00514861--Location Balance Report/Rollups Balance` (Closed).

## 8. Cluster: Crystal preview/print failures (client side)

### 8.1 `CrystalDecisions.CrystalReports.Engine.LogOnException: Log on failed.`
TESTit Desktop print-preview of TEST reports fails with LogOnException (SF 25-01034183 on 2.14.5; recurrences 25-01034650, 25-01040309 on 2.13.5).
Fix: **create the ODBC connection(s)** the report expects on the affected workstation (SF 25-01034183 resolution). Check DSN name/bitness (32-bit driver for 32-bit runtime).

### 8.2 `External exception EEFFACE` in the reports screen
Known Date/Time UI component defect on FLOWCAL 10.4.x (seen 10.4.0.13); **fixed in FC 10.5.0.0** (INFERRED; SF 26-01105022). Upgrade; harmless to dismiss otherwise.

### 8.3 `Page header or footer longer than a page.`
Error at `Execute <PEStartPrintJob>` with the .rpt under `Crystal\<USER>\` — seen on FLOWCAL **7.4.15.1** (SF 26-01112366, Missing Data Summary.rpt). Layout defect in legacy report/runtime; answer is upgrade to v10 (account team engaged for quote). If a single custom .rpt: shrink the page header/footer sections in Crystal Designer.

### 8.4 Custom report opens-then-closes on preview
TESTit custom Meter History report: preview window flashes and closes — corrupt custom .rpt; support **rebuilt the report** and validated against the client DB (SF 26-01068398). Citrix note: Crystal running under Citrix published apps has its own quirk set (SF 26-01100869 routed as Training; 26-01105046 was client network, Root_Cause 'Client Managed Infrastructure').

## 9. Cluster: Rollup Viewer (Open > Rollup Viewers > Meter/Location Rollups)

### 9.1 Error-log spam `Unable to find column -32000 <PPA Mass|PPA GSV|CPA|PPA NSV|PPA SWV> in for Location`
Trigger: Inventory checkbox on the Liquid Adjustment tab for a location with inventory; four+ entries per member written to `_FC_FC_ERROR.LOG` (SF 22-00567021).
Fix (release-notes-CONFIRMED, quoted in the SF resolution): **10.0.3.7** — PPA columns no longer display for inventory location data (internal defect **FC-1934825**). Display data was always correct; log spam only.

### 9.2 Blank records in Daily/Monthly Location Rollup Viewer after close
Blank rows appear mid-month post-close; a re-rollup clears them each time (SF 22-00709526). **Fixed in 8.10.44** (INFERRED). On modern builds treat recurrence as new — check rollup queue first.

### 9.3 Volume Editor ≠ Rollup Viewer totals after PPA (time leads/trails change)
Root cause: switching a meter between time leads and time trails left some `rollup_report_id` values wrong → rollup calc wrong (SF 24-00989831, 10.5.0.16).
Fix recipe (verbatim sequence from SF 24-00989831):
1. Purge the PPAs for the affected month.
2. Setup > Meter > Close Dates — re-open the month.
3. Close and re-open FLOWCAL.
4. Tools > Toolbox → **Recalc Rollup IDs** for the month.
5. Setup > Meter > Close Dates — close the month again.
6. Volume Editor: span edit for the month on the meter to re-trigger source apply.
Caveat: **ADO 1814934** `Toolbox Recalc Rollup IDs does not work (DEV)` (Closed) — on ~10.5.0.10 the toolbox fix itself misset `rollup_report_id` (first hour of the month wrong); verify with the SQL in §11 after running it.
Related open rollup-content items: ADO 1868033 (LinePack location Inventory Volume/Energy absent from Rollup Viewer — New), ADO 1773286 (location rollups miss summed components until re-queued via Settings Manager > Services > Service Queues — New), ADO 1863438/1860292 (FcSrvLcnRollup spamming event-viewer errors via FcSrvMtrRollup — Analyze/New).

## 10. Cluster: TESTit / PROVEit report scheduling & report defects

### 10.1 TESTit monthly schedule skips the current month
Creating/editing a monthly schedule dated later in the current month bumps the first run to next month (3/2 edit of a 3/15 job → 4/15). Weekly/daily unaffected (SF 23-00900346, TESTit 3.12; **ADO 1623648** `23-00900346--TESTit Monthly Report Schedule Issue`, Closed). **Fixed in TESTit 3.17** (INFERRED). Workaround pre-3.17: manually run/one-off-schedule current-month occurrences.

### 10.2 TESTit Plate Change report fails only through Report Scheduler
Runs fine from Reports, errors via scheduler with nothing in log viewer (SF 23-00893903). Resolved in a later TESTit 3.x version (INFERRED — support verified fixed in "latest version"; upgrade).

### 10.3 Crystal/print issues on TESTit/PROVEit clients
LogOnException → ODBC (§8.1). PROVEit Crystal Report runtime not installing → client infrastructure (SF 26-01070209). TESTit 3.17.1 printing reports/attachments defect logged as Software Defect (SF 25-01021817). TESTit server Crystal failing → config (SF 26-01102365).

---

## Known ADO items (org `QuorumSoftware`)

| ADO | Type / Area | Title (verbatim) | State | Notes |
|---|---|---|---|---|
| 1814424 | Bug, Quorum\NA\Measurement | Report Service crash with error message "Terminated while running" when emailing the Balance Detail (Calc) report (R1080* PORT) | Closed | SF 26-01104125; fix shipped 10.8.0.10 (INFERRED) |
| 1845098 / 1845099 | Bug | same title (DEV) / (R1090 PORT) | Closed / New | R#### PORT convention |
| 1746775 | Bug | [AHT 10.8] Report Service failing reports with DLLs | Closed | 0xc0000374 ntdll; DLL reports only |
| 1776732 | Requirement, Engineering | Investigate Report service crash with new runtime (Dev*) | Closed | SAP Crystal runtime 37 vs 39; repro on both |
| 1745450 | Bug | [AHT 10.8] EOG TOW and ALNG exports cause FLOWCAL to become unresponsive (R1080* PORT) | Closed | export-DLL family |
| 1319619 / 1412392 / 1412396 / 1412397 | Bug | Running Scheduled Tips Export Causing Report Service to Fail (R1010* PORT / Dev / R1020 / R1030 PORT) | Closed | writes file, no email; tag 10.4.0.0 |
| 1814982 | Bug | 10.7 Upgrade script change | Closed | UPPER() fix for FcTextFileExchange→GasTextFileExchange rename (§4) |
| 1801851 | Bug | 26-01092643- FcTextFileExchange Export Issue | Closed | export content (lat/long 0/NULL) |
| 1687067 | Incident, myQuorum Cloud\QCloud Ops | 24-00979697 SCT FC PRD - Report service failure | Closed | stuck TIPS export wedged service |
| 1772149 | Incident Global Cloud Ops | 25-01061248 - SEM FC PRD - Reports not sending | Closed | SMTP credentials updated |
| 1623648 | Bug, Engineering | 23-00900346--TESTit Monthly Report Schedule Issue | Closed | fixed TESTit 3.17 (INFERRED) |
| 1814934 | Bug | Toolbox Recalc Rollup IDs does not work (DEV) | Closed | verify SQL below after any Recalc Rollup IDs run |
| 1868033 | Bug | LinePack location is not showing Inv. Volume and Inv. energy in rollup viewer. | New | open at survey date |
| 1773286 | Bug | Location rollups does not rollup components correctly initially | New | re-queue workaround via Service Queues |
| 1863438 / 1860292 | Bug | FcSrvLcnRollup service is causing errors to be reported to the event viewer by the FCSrvMtrRollup Service (DEV / R1090* PORT) | Analyze / New | rollup-service noise |
| 1805244 | Bug | 22-00514861--Location Balance Report/Rollups Balance | Closed | balance vs rollups mismatch |
| FC-1934825 | legacy internal id | Rollup Viewer PPA columns for inventory locations | shipped 10.0.3.7 | release-notes-CONFIRMED (quoted in SF 22-00567021) |

## Diagnostic SQL (FLOWCAL DB — Oracle syntax; run against the client schema; DEV-tier results stay INFERRED for PRD state)

```sql
-- 1. Schedules pointing at a missing/renamed export DLL (§4; from ADO 1814424 engineering thread)
select * from fc_report_list where UPPER(report_location) like '%EXCHANGE%';

-- 2. Post-10.7-upgrade rename audit (§4; expect zero FCTEXTFILEEXCHANGE rows on a healthy 10.7+)
select 'group'    src, group_name  val from fc_report_group    where UPPER(group_name)  = 'FCTEXTFILEEXCHANGE'
union all
select 'schedule', group_name       from fc_report_schedule    where UPPER(group_name)  = 'FCTEXTFILEEXCHANGE'
union all
select 'list',     report_location  from fc_report_list        where UPPER(report_location) = 'EXPORT\FCTEXTFILEEXCHANGE.DLL';

-- 3. Reset schedule delivery tracking in a TEST environment (engineering technique, ADO 1776732 — do NOT run in PRD without approval)
-- delete from fc_report_distribution;
-- delete from fc_report_failed;
-- commit;

-- 4. Verify rollup_report_id after Recalc Rollup IDs (§9.3; verbatim from ADO 1814934)
alter session set nls_Date_format = 'mm/dd/yyyy hh24:mi:ss';
select effective_Date, effective_end_Date, rollup_report_id, rollup_calendar_id, measurement_hour
from fc_meter_periodic_values p
where meter_number_index = (select meter_number_index from fc_meter where meter_number = '<METER>')
  and effective_Date >= '<MM/01/YYYY> 00:00:00' and effective_Date <= '<MM/19/YYYY> 00:00:00'
  and sequence_number = (select min(sequence_number) from fc_meter_periodic_values
                         where meter_number_index = p.meter_number_index and effective_Date = p.effective_Date)
order by 1;
-- Expect: first row's rollup_report_id corresponds to hour 1 of the contract month.
```

## Expected-Behavior FAQ

- **"How often should FCSRVREPORTS be restarted?"** — No scheduled restart is required on healthy versions; recurring restarts signal one of §3's defects (SF 22-00655065 asked exactly this). Pre-10.5.0.18 sites with heavy exception volumes benefit from a monthly proactive restart (§3.4).
- **Can I run a second FcSrvReports instance?** — Multi-instance requests appear in history (SF 24-00993939 cancelled; 22-00605387) — treat as architecture/services question, not this skill; route to services group.
- **Monthly schedule shows next run in the following month** — On FLOWCAL this is normal when the run date/time already passed; on TESTit ≤3.16 it's the §10.1 defect even for future dates.
- **Rollup Viewer log spam but data looks right** — §9.1 was cosmetic; data was never wrong. Say so explicitly in customer comms.
- **Report totals ≠ Volume Editor totals** — Not automatically a defect: rollups may simply be pending. Only after rollups are confirmed current does §9.3 apply.
- **Customer wants a new/updated custom Crystal report deployed** — Operational request (User Administration/M&S), not a defect: QCloud drops the .rpt into the environment's Crystal folder (SF 26-01086191, 26-01084591, 25-01025697 pattern).

## Escalation guidance

- **QCloud-hosted clients:** service restarts, SMTP relay changes (O365↔mailgun), and .rpt deployments are cloud-team actions — raise the incident in `myQuorum Cloud` (pattern: ADO 1687067, 1772149). Recurring "reports empty/incomplete" with Service Monitor crashes → treat as critical, cloud team checks service status + server resources (SF 25-01028604).
- **Engineering handoff (G5):** unexplained FcSrvReports crashes after §3.1–§3.4 are ruled out → area path `Quorum\North America\Measurement` (bugs get DEV + R#### PORT copies under `QuorumSoftware\Engineering\Measurement\Maintenance`). Include: `_FC_SRV_REPORTS.LOG` excerpt, Windows event (exception code), the .rpt/DLL the dying schedule uses, and whether manual run/email works — that manual-vs-scheduler split is the single most diagnostic fact (ADO 1776732: scheduler-only crash ⇒ service-context difference).
- **Version answers:** always re-verify "fixed in" against release notes before telling a customer to upgrade; most fixed-in claims above are INFERRED from SF resolutions.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
