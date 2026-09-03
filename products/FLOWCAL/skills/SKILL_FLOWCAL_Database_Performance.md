# SKILL — FLOWCAL Family: Database & Performance

> **Product family:** FLOWCAL · TESTit · PROVEit (`Product_list__c IN ('FLOWCAL','TESTit','PROVEit')`)
> **Scope:** Oracle/SQL Server errors surfaced through the app (`CDbio` / `_FC_DB_ERROR.log`), tablespace & index maintenance, DB connectivity, purge/archive failures, partitioning stance, database refreshes, and the recurring performance-degradation families (data bloat, lock contention, stale stats, service memory pressure).
> **Sources:** Salesforce closed-case mining (all-history, 2026-09-02) — clusters: tablespace (21 cases), partitioning (16), purge (25+), db-error (25+), performance (25+), Oracle upgrade/compat (25+), deadlock (12); deep-sampled ~30 resolved cases + ADO org `QuorumSoftware` defect chains.
> **Auto-Bot** — the L4 issue solver built by **Aditya Bhagat**.

---

## 1. Quick Triage

| Symptom / error string | Likely cause | § |
|---|---|---|
| `ORA-01653: unable to extend table FCOWNER.<T> ... in tablespace FC_*_TS` | Tablespace datafile(s) full — routine growth OR runaway rollup queue | 3.1 |
| `ORA-25153: Temporary Tablespace is Empty` (Location Edit query) | `FC_TEMP_TS` has no tempfile | 3.1 |
| `Could not allocate a new page for database 'FIELDAPPS' ... filegroup 'PRIMARY'` (TESTit/SQL Server) | SQL Server data file / disk full | 3.1 |
| `ORA-01502: index ... or partition of such index is in unusable state` (imports stop) | Unusable index after maintenance/move — rebuild | 3.2 |
| `ORA-00942 ... select SERIAL# from v$session` flooding `_FC_DB_ERROR.log` | Missing `GRANT SELECT ON v_$session/...` to FC roles | 3.3 |
| `ORA-01031: insufficient privileges` — `Unable Set Role - OnUserSignOn()` or TESTit "Error updating policy file date" | Role passwords / dat-file out of sync — run password utility | 3.3 |
| `ORA-02395: exceeded call limit on IO usage` (read-only user) | Oracle profile `LOGICAL_READS_PER_CALL` limit | 3.3 |
| `ORA-12154` / `ORA-12514` / `ORA-12170` TNS errors | tnsnames/listener/network — not app defect | 3.4 |
| `ORA-03113` / `ORA-03114` end-of-file / not connected | Network path killed mid-session — antivirus interference confirmed once | 3.4 |
| `ORA-01034` + `ORA-27101` shared memory realm | Oracle instance down — client DBA | 3.4 |
| `ORA-00020: maximum number of processes (N) exceeded` (TESTit) | Connection leak — service reinstall; fix expected in TESTit 3.17 (INFERRED) | 3.4 |
| FLOWCAL won't connect after Oracle 19c upgrade | Missing Oracle **32-bit** client for the Delphi/C++ desktop app | 3.4 |
| Point-to-point / span edit takes minutes on GPA 2172 meters; CFX imports process slowly | Duplicate/excessive `FC_EDIT_REASON` rows (defect) | 3.5 |
| Volume Editor freeze up to 30 s opening month with many notes | `FC_USER_NOTE` load defect — fixed 10.6.0.12 | 3.5 |
| Meter delete takes minutes; SQL log shows hang on `FC_REPORT_SCHEDULE(_PARAM)` | Report-schedule cleanup on delete (ADO 1723674, Proposed) | 3.5 |
| Group/list close hangs 20+ min after 10.6.0.7 upgrade | Close regression introduced 10.6.0.7, fixed 10.6.0.11 | 3.5 |
| Calc-meter/location rollups painfully slow or rolled back (v10) | Rollup service defect chain (fixed ~10.2.0.11 / 10.3.0.12 / 10.4.0.7 / 10.5.0.0) OR rollup queue poisoned by future-dated records | 3.5 |
| Whole app slow, everything sluggish, one env only | Stale optimizer stats / service memory pressure (`LcnRollup4.exe`) — infra, not code | 3.5 |
| `ORA-00060 deadlock detected` (Recycle Bin, MPV update, file import) | Concurrency collision — schedule around, or known old fixes | 3.6 |
| `Lock request time out period exceeded` (TESTit `CDbio`, TIDX import) | Large TIDX w/ attachments holding locks | 3.6 |
| "Warning: Purge NOT allowed because there are PPAs" but no PPAs visible; then "No PPA to purge" | End-of-time (`01/18/2038`) rows in `FC_PPA_ACCOUNTING_INFO`/`FC_METER_EDIT` | 3.7 |
| Purged PPA still listed on PPA Approvals screen | `edit_type='E'` instead of `'P'` written by test-report apply — fixed 10.6.0.14 | 3.7 |
| `ORA-00001 (FCOWNER.LCNROLLQ_PK)` when purging | Purge re-queues location rollup that is already queued | 3.7 |
| `ORA-00001` on `FC_AMETANL_PK` / `FC_METPER_PK` / `FC_BATCHRPT_PK` / `FC_GQANLEXT_PK` during import/save | Import/TQ PK-collision defect family — KB workaround + fixed versions | 3.7 |
| "Should we partition the FLOWCAL DB?" | FLOWCAL does not target partitions; limited benefit — Expected Behavior | 3.8 |
| UAT refresh from PRD — things broken afterwards | Version/dat-file/policy-file/import-path drift — checklist | 3.8 |

---

## 2. Decision Tree

```
DB or performance symptom on FLOWCAL/TESTit/PROVEit
│
├─ Is there an ORA-xxxxx / SQL Server error string?
│   ├─ Space family (01653, 25153, filegroup PRIMARY) ............ §3.1  [G2 config/ops]
│   ├─ ORA-01502 unusable index .................................. §3.2  [G4 bad data → rebuild]
│   ├─ Privilege/profile (00942 v$session, 01031, 02395) ......... §3.3  [G2 config]
│   ├─ Connectivity/instance (12154/12514/12170, 3113/3114,
│   │   01034/27101, 00020) ...................................... §3.4  [G2/infra; rarely G5]
│   ├─ ORA-00060 deadlock or lock timeout ........................ §3.6  [G1/G3; old fixes exist]
│   └─ ORA-00001 / ORA-02291 constraint during import/purge ...... §3.7  [G3 version or G4 data]
│
├─ No error, just SLOW?
│   ├─ Slow only on specific meters/months → data bloat:
│   │   count FC_EDIT_REASON + revisions + FC_USER_NOTE .......... §3.5  [G3: fixes in 10.6.x;
│   │                                                                    G4: cleanup SQL]
│   ├─ Slow on one operation app-wide (delete meter, close list)
│   │   → known regressions table ................................ §3.5  [G3 version]
│   ├─ Rollups lagging → check queue for future-dated records,
│   │   then rollup-service defect chain ......................... §3.5  [G4 then G3]
│   └─ Whole environment slow → stats, VM/memory, QCloud restart .. §3.5  [infra/ops]
│
├─ Purge won't run / purge left artifacts? ....................... §3.7
│
└─ Architecture / maintenance question (partitioning, archive,
    refresh, Oracle version support)? ............................ §3.8  [G1 Expected Behavior
                                                                          or ops request]
```

Gate discipline: most of this skill's traffic exits at **G2 (config/DBA action)** or **G3 (fixed in version)**. Only the data-bloat cleanups and end-of-time PPA rows are **G4 (bad data)**; true G5 code changes are rare and already have ADO items — cite them, do not re-investigate.

---

## 3. Symptom Clusters

### 3.1 Tablespace / space exhaustion — `ORA-01653`, `ORA-25153`, SQL Server filegroup full

**Signature.** Services (rollups, `FCSRVTRANS`, file import) stop; `_FC_DB_ERROR.log` or import errors show `ORA-01653: unable to extend table FCOWNER.<TABLE> by 8192 in tablespace <TS>`. Frequent offenders: `FC_FFMTR_HOURLY` in `FC_ROLLUPS_FFMTRHLY_TS`, `FC_METER_PERIODIC_VALUES` in `FC_MAIN_MPER_TS`, `FC_METER_ANALYSIS` in `FC_MAIN_TS` (SF 26-01079753, 22-00528696, 22-00633005, 22-00625918, 23-00902929). TESTit/SQL Server flavor: `Could not allocate a new page for database 'FIELDAPPS' because of insufficient disk space in filegroup 'PRIMARY'` (SF 25-01003163).

**Root cause.** Routine DB growth (each Oracle datafile caps at 32 GB with smallfile tablespaces — SF 22-00655078); occasionally a runaway consumer: customer queued ALL meters for "All Data" rollups, plus two meters with future rollup dates 1/1/2037→EOT kept the meter-rollup service looping (SF 24-00973539 — put future-dated queue rows on Hold, restart `FcSrvMtrRollup`).

**Fix recipe (Oracle, run as SYSTEM — SF 22-00528696 / 22-00534478 / 22-00653527, verbatim from resolutions).**
1. Identify: see Diagnostic SQL D1/D2.
2. Add a datafile:
   `ALTER TABLESPACE <TS> ADD DATAFILE '<path>\<TS>_NN.FCF' SIZE 100M REUSE AUTOEXTEND ON NEXT 100M MAXSIZE UNLIMITED;`
   Datafiles may live on any drive, not only the DB folder (SF 25-01023601).
3. Restart the affected FC services (SF 22-00818904).
4. `ORA-25153`: add a **tempfile** to `FC_TEMP_TS` instead (SF 22-00661064).
5. If space burn is abnormal, check the rollup queues for future-dated/EOT records before adding more space (SF 24-00973539).
6. SQL Server (TESTit `FIELDAPPS` DB): grow/add data file or free disk — client DBA action.

**Class:** Application Configuration / routine maintenance (G2). *Not* a software defect; there is no permanent "fix" — growth is expected (SF 22-00584682).
**Anchors:** SF 26-01079753, 25-01023601, 25-01023361, 24-00973539, 23-00902929, 23-00889118, 22-00818904, 22-00528696, 22-00625918, 22-00679013, 22-00633005, 22-00537182, 22-00653527, 22-00534478, 22-00655078, 22-00661064, 25-01003163.

### 3.2 Unusable indexes — `ORA-01502`

**Signature.** Scheduled TESTit-file import into FLOWCAL suddenly fails; error log shows `ORA-01502: index 'FCOWNER.<INDEX>' or partition of such index is in unusable state`. Seen on `FC_TRATTACH_OBJ_DATA_PK`, `FC_TRATTACH_TEST_DATA_PK`, `FC_MTRROLLQ_PK` (SF 22-00631496, 22-00648854, 22-00671360).

**Root cause.** Index left UNUSABLE after a DBA operation (table move/partition maintenance/direct-path load). Data is intact; DML on the indexed table errors until rebuild.

**Fix recipe (verbatim from SF 22-00631496 resolution).**
1. `select table_name, index_name, tablespace_name, status from all_indexes where table_name like 'FC%' and status <> 'VALID';`
2. Generate rebuilds: `select 'alter index '||index_name||' rebuild tablespace '||tablespace_name||';' from all_indexes where table_name like 'FC%' and status <> 'VALID';`
3. Execute the generated `ALTER INDEX ... REBUILD` statements.
4. Re-run step 1 — must return no rows. Re-run the failed import.

**Class:** Bad data / environment (G4-ops). **Anchors:** SF 22-00631496 (full recipe), 22-00648854, 22-00671360.

### 3.3 Privilege & profile errors — `ORA-00942` on `v$session`, `ORA-01031`, `ORA-02395`

**A. `_FC_DB_ERROR.log` flooded with `ORA-00942: table or view does not exist` on `select SERIAL# from v$session where audsid = userenv('sessionid')` (module `FCDBSECURITY.DLL`).**
Missing grants after DB rebuild/refresh/hardening. Fix (run as SYSTEM, then start FC services — SF 26-01116701 verbatim):
```
GRANT SELECT ON v_$thread  TO fcuser, fcadministrator, fcowner;
GRANT SELECT ON v_$version TO fcuser, fcadministrator, fcowner;
GRANT SELECT ON v_$session TO fcuser, fcadministrator, fcowner;
```

**B. `ORA-01031: insufficient privileges`.**
- FLOWCAL login: `Error: Unable Set Role - OnUserSignOn()` — application role passwords mismatch (SF 24-00987181).
- TESTit after upgrade/refresh: "Error updating policy file date" + CDbio ORA-01031 — encrypted passwords in `fa_application_information` and the app-role passwords (`fcuser`/`fcviewer`/`fcadministrator`) no longer match the `.dat` file. Fix: run the **TESTit Oracle Password Utility** to regenerate the dat file (SF 25-01014088); the same password/dat/policy alignment applies after clones (SF 22-00579900, see §3.8).

**C. `ORA-02395: exceeded call limit on IO usage`** on READ_ONLY accounts. DBA must raise the user's profile (SF 26-01095486 verbatim):
```
SELECT profile FROM dba_users WHERE username = 'USERNAME';
ALTER PROFILE <profile> LIMIT LOGICAL_READS_PER_CALL UNLIMITED;
ALTER PROFILE <profile> LIMIT LOGICAL_READS_PER_SESSION UNLIMITED;
```

**Class:** Application Configuration (G2). **Anchors:** SF 26-01116701, 24-00987181, 25-01014088, 26-01095486, 22-00579900.

### 3.4 Connectivity, instance & client-stack errors

| Error | Meaning | Action | Anchor |
|---|---|---|---|
| `ORA-12154` TNS could not resolve | tnsnames.ora / alias wrong on that workstation | Fix client tnsnames; not app | SF 26-01094099 |
| `ORA-12514` listener does not know of service | Listener/service down | Start listener/DB (client or QCloud) | SF 26-01081002 |
| `ORA-12170` TNS connect timeout | Network/firewall/host down | Infra path check; was a QCloud outage | SF 26-01103315, 26-01103305 |
| `ORA-03113`/`ORA-03114` | Session killed mid-flight | One confirmed cause: AVG/Avast antivirus updates blocking FLOWCAL↔Oracle — whitelist both program trees | SF 26-01087778 |
| `ORA-01034` + `ORA-27101` | Instance not started | Client DBA / Azure team starts DB | SF 26-01094071 |
| `ORA-00020 max processes (320) exceeded` (TESTit 3.x) | Connection leak from TESTit services | Uninstall/reinstall 3.17 services; leak fix expected in TESTit 3.17 (INFERRED — not release-note-confirmed) | SF 25-00996077 |

**Oracle upgrades & compatibility (recurring intake, mostly G1/G2):**
- **19c upgrade → FLOWCAL won't connect:** install the **Oracle 32-bit client** on app/Citrix servers; the desktop app is 32-bit even though `FlowCal.exe` web.config also lists ODP.NET Managed Driver (SF 25-01012276 — confirmed fix).
- `DBColCheck` utility connection issues against 19c are a known follow-on of the client-stack setup (SF 23-00884783, 23-00902744, 23-00906137).
- "provider is not compatible with the version of Oracle client" launching TESTit from FLOWCAL on a new server = wrong/missing client install (SF 23-00906194).
- Version-support matrix questions (10.4/10.5 vs Oracle releases, 19c certification, EE→SE migration, Azure-hosted Oracle) route to product management docs — treat as Expected Behavior/Training (SF 23-00900478, 25-00998717, 26-01101003, 26-01109043, 26-01079850). TESTit integrations breaking right after a client Oracle upgrade was a deployment issue, not a defect (SF 26-01109179).

### 3.5 Performance degradation families

**A. Data bloat: duplicate/excessive Edit Reasons (GPA 2172) — the #1 confirmed perf defect.**
- *Signature:* point-to-point or span edits on GPA 2172-enabled meters take 5+ min per save (SF 26-01118526, Chevron); CFX imports process slowly; app crashes/slowness plus stuck CFX imports (SF 25-01012021); each import adds another whole-month `GPA 2172` edit reason row (294+ rows on one record seen in ADO repro).
- *Root cause:* every import/recalc writes a new GPA 2172 edit reason spanning the month instead of only the changed window — table `FC_EDIT_REASON` explodes. **ADO Bug 1721407** (R1060*), **1770699** (DEV), **1770701** (R1080 PORT) — all Closed; source case 25-01012338.
- *Fix:* short-term — SQL cleanup removing duplicate edit-reason rows while keeping the legitimate ones (support-run; SF 26-01118526, 25-01012021 "excess revision and duplicate edit reason clean up"). Long-term — upgrade: fixed in **FLOWCAL 10.6.0.18 / 10.8.0.9 / 10.9.0.1** (SF 26-01118526 resolution). A liquids-flavor sequel (import fails outright even after cleanup in 10.8) is **ADO 1839778** "Liquids Meter CFX File Import Service Issue (R1090 PORT)" — Acceptance as of 2026-08.
- *Diagnostic:* SQL D4.

**B. Volume Editor slow to open with user notes.** Months with one note per periodic record froze the VE up to 30 s. Fixed in **10.6.0.12** ("Performance Improvement: Volume Editor Load Times for Periodic Data With Notes", ref 25-01011858; customer case SF 26-01086803 ETE, meters 81514-01/81560-01). **ADO Bug 1762468** (DEV, Closed), table `FC_USER_NOTE`.

**C. Meter delete slow — `FC_REPORT_SCHEDULE` / `FC_REPORT_SCHEDULE_PARAM`.** Deleting a meter hangs ~53 s (empty meter) to 19-20 min (meter with data) in one environment but not its twin; SQL performance logging pins the wait on the report-schedule tables (delete must remove the meter from scheduled-report jobs). **ADO Bug 1723674** — still *Proposed/Investigation*; customer-side stats refresh did NOT fix it. SF 25-01013744 resolution states resolved in **10.6.0.11**, which also fixed a bug in the SQL-performance-logging tool itself that had muddied diagnostics for months (label both INFERRED until release notes checked). Diagnostic: SQL D5.

**D. Close/unclose regression.** Group/list close running 20+ min: new functionality introduced in **10.6.0.7** degraded closing; addressed in **10.6.0.11**; advise 10.6.0.18 (SF 26-01105689, Continental).

**E. Rollup performance.**
- v10 calc-meter/location rollup slowness & rollback storm: defect chain **ADO 1119871 (Dev) / 1119864+1119889 (R1010) / 1119870 (R1020, tag "In Patch - FC-10.2.0.11")**; the related SF escalation 23-00876717 was resolved in **10.5.0.0 GA, 10.4.0.7, 10.3.0.12**.
- Rollup service stalls with clean code: look for future-dated rollup-queue records (1/1/2037→EOT) and put them on Hold (SF 24-00973539); or an env-level memory leak — QCloud restart of `LcnRollup4.exe` cleared UAT-wide slowness (SF 26-01112402).
- Debug logging: `_FC_SRV_CALC_MTR_ROLLUP_LOG.LOG`; enable FcDebugOption `[LOCATION_ROLLUP_DEBUG] log_performance_message_to_file = Y` → produces `_lcn_performance_fcsrvcalcmtrrollup.log` (ADO 1119870 history).

**F. Environment-wide slowness (no specific operation).** First moves, in order: (1) gather Oracle stats on all FC tables — resolved "WTG FLOWCAL is very slow" outright (SF 24-00944724); FLOWCAL ships a STATS script incl. a partitioned-table variant (SF 25-01044852); (2) VM/memory/QCloud health & service restart (SF 24-00954222, 24-00982994, 26-01112402); (3) only then look for the §3.5A-D defects. TESTit TIDX import slowness with attachments is expected behavior scaling with attachment size — enhancement request, not defect (SF 25-01028463/25-01018663).

**Class:** A-E are G3 (fixed-in-version) with G4 cleanup steps; F is infra/ops.

### 3.6 Locking — `ORA-00060` deadlocks & SQL Server lock timeouts

- **TESTit Recycle Bin ORA-00060** (3.16.1, Oracle): clearing the recycle bin while field users edit meters/tasks/schedules deadlocks. Workaround: clear the bin off-hours (SF 24-00978682 — customer accepted workaround; no fix shipped from that case).
- **Historic FLOWCAL deadlock fixes:** "Oracle Deadlock - Update to MPV" fixed in 8.11.34.13 / 8.11.35.10 / 8.11.36.4 / 8.11.37.2 / 8.11.38 (SF 22-00531182); `FCSRVFileimport` deadlock storms tracked as FC-1725141 duplicate (SF 22-00538533); one client mitigated via table `INITRANS` increase, never productized (SF 22-00561220). Location delete deadlock (SF 22-00806174) aged out after upgrades.
- **SQL Server (`CDbio`) lock timeouts:** `Database Error occurred in CDbio: Lock request time out period exceeded` during TESTit file-import — big TIDX files with attachments hold long transactions (SF 25-01028463, 26-01087764); `Execution timeout expired` flavor SF 24-00990540. Mitigate: import TIDX without attachments where possible, off-peak imports; enhancement filed for attachment handling.

**Triage rule:** a single deadlock is a retry, not a defect (Oracle auto-resolves the victim). A *pattern* on one operation → check the fixed-version list above (G3) before proposing code work.

### 3.7 Purge & archive failures

**A. "Warning: Purge NOT allowed because there are PPAs" (but no PPAs visible), then "No PPA to purge".**
Cause: rows in `FC_PPA_ACCOUNTING_INFO` and `FC_METER_EDIT` with `effective_end_date = '01/18/2038 21:14:06'` (end-of-time). Fix pattern (**ADO Bug 1592594**, source SF 23-00894675; verbatim SQL in the ADO history): update the offending rows' `effective_end_date`/`end_time_stamp` to the true period end, commit, purge again. Same signature in SF 24-00938300 ("SQL to fix the PPAs that went to the end of time", ~24 meters). Class: G4 bad data.

**B. Purged PPA still showing on PPA Approvals screen** (FC 10.2.0.22; also lingering P-flag in Volume Editor).
Root cause: TESTit test-report apply wrote `FC_METER_EDIT.edit_type = 'E'` instead of `'P'`, so Purge PPAs skipped the approval record. **ADO Bug 1687000** (R1060* PORT) + **1772806** (DEV) "Test reports applied with edit_type = E instead of PPA for PPAs"; fixed in **10.6.0.14**, ported to **10.8.0.4** (SF 26-01063618 resolution; sibling case 24-00977476, Williams). Related items: **1725795** (Purge PPA doesn't purge calibration-adjustment PPAs' approval records), **1684986** (TESTit 3.16 Meter Inspections creating duplicate PPAs in FC 10.2.0.22), **1780149** (unable to approve TESTit CalAdj PPA, R1080* PORT), **1691084** (Access Violation `0C24929B` in `FCENTERPRISEFORMS.DLL` opening a pending PPA, SF 24-00982720).

**C. `ORA-00001 unique constraint (FCOWNER.LCNROLLQ_PK) violated` when purging** — purge tries to enqueue a location-rollup entry that already exists; support has a standard data-fix (clear/dedupe the pending `LCNROLLQ` row for that location, re-run) (SF 26-01084565, resolution "provided instructions"). Sibling: `FC_MTRROLLQ_PK` unusable-index flavor is §3.2.

**D. Purge PPA Batch Split error (liquids).** Purge PPA/purge-to-original errors after a PPA created via ticket batch split; required support SQL + batch recalc; deferred to DEV at the time (SF 24-00954505, 24-00952332 — FC 10.2.0.16). Check current release notes before re-diagnosing.

**E. Import-side `ORA-00001`/`ORA-02291` constraint family** (surfaces in DB error log; overlaps Imports skill):
- `FC_AMETANL_PK` on CFX/analysis import: KB article "Troubleshooting Error ORA-00001: unique constraint (FCOWNER.FC_AMETANL_PK) violated for FLOWCAL" + fixed in **10.6.0.13** (SF 26-01114165; also 26-01074177, 26-01090557, 25-01005621, 26-01112798, 26-01101356).
- `FC_BATCHRPT_PK` importing a batch-report revision via Transaction Queue: fixed in **10.9.0.1** (SF 26-01080237).
- `FC_GQANLEXT_PK` (GQ extended analysis): Software Defect (SF 26-01086651, 24-00987652).
- `FC_METPER_PK` text-file import by IMPORTID (SF 25-01050945); check constraint `FC_METPER_N_MEASUREMENT_MONTH` (SF 26-01102120).
- FK `FC_METANL_F_LAB_ANALYSIS_ID` parent-key-not-found on CFX (SF 26-01098284 defect / 25-01060909 config); FK `FCL_COMO_F_LOCATION_INDEX_ROLL` (SF 25-01040838).

**F. Misc purge:** FcDataboss 3.5.4 purge-retry button mislabeled "Retry Import" — cosmetic bug, ET (SF 24-00950336). Recovering wrongly purged data = restore from backup/archive exercise, no in-app undo (SF 25-01008705, 25-01004080). Extended characteristics are NOT purged with source analyses (SF 25-01012569 — behavior gap, enhancement).

### 3.8 Partitioning, DB maintenance & database refreshes

**Partitioning stance (Expected Behavior — quote this):** FLOWCAL is **not designed to leverage database partitioning directly and cannot target specific partitions in its queries**. Partitioning may help external reporting/storage maintenance, but in-app gains are typically limited; optimization goes through a Services-team database health assessment (SF 26-01120809 resolution, 2026). History: partitioning white papers existed and clients ran partitioned FC DBs (SF 22-00700497, 22-00608888, 22-00529439), Williams abandoned theirs because FK constraints blocked dropping old slices (SF 24-00983643); a Partitioning/Archiving-Purging module is sold with training/implementation (SF 26-01086489, 25-01045342); Technical Health Check engagements cover Partitioning\Purge (SF 25-01022289, ONEOK). Quorum supplies an **Oracle STATS script with a partitioned-tables variant** on request (SF 25-01044852).

**Database refresh (PRD→UAT/TEST) — request type `Root_Cause__c='Database Refresh Request'`, executed by QCloud for hosted clients** (SF 26-01070861, 25-01043852, 25-01016407, 25-01002789, 24-00947579...). Post-refresh gotcha checklist (SF 23-00889577, 22-00579900 — TESTit 3.14 post-refresh breakage):
1. Target env lands on the **source's app version** — redo any test-env upgrade after copying PROD→TEST.
2. All TEST-side config is overwritten (file-import paths, service configs) — re-apply.
3. Passwords: DB roles + app roles must match the `.dat` file — run the password utility; verify `fa_application_information` version row; don't leave the policy file renamed/missing in the install dir (it must copy to ProgramData).
4. Policy file should be copied from the cloned source so users/permissions match; verify Citrix mklink launch shows no "Policy File out of sync" error.
5. On-prem Oracle refreshes of PRD are client-DBA-led with Quorum assistance scheduled (SF 22-00570352 series).

---

## 4. Known ADO items (org `QuorumSoftware`; port convention `(DEV)` / `(R10xx PORT)`)

| ADO | Title (abridged) | State (mined 2026-09-02) | Fixed-in |
|---|---|---|---|
| 1721407 | Excessive edit reasons on meter causing imports to process slowly (R1060*) | Closed | 10.6.0.18 (INFERRED from SF 26-01118526) |
| 1770699 / 1770701 | Excessive edit reasons ... (DEV / R1080 PORT) | Closed | 10.8.0.9, 10.9.0.1 (INFERRED) |
| 1839778 | Liquids Meter CFX File Import Service Issue (R1090 PORT) | Acceptance | open |
| 1762468 | Volume Editor Slow with User Notes (DEV) | Closed | 10.6.0.12 (SF-resolution-confirmed) |
| 1723674 | performance issue [meter delete → FC_REPORT_SCHEDULE] | Proposed / Investigation | 10.6.0.11 claimed by SF 25-01013744 (INFERRED) |
| 1687000 / 1772806 | Test reports applied with edit_type = E instead of PPA (R1060* / DEV) | Closed | 10.6.0.14, ported 10.8.0.4 (SF 26-01063618) |
| 1725795 | Purge PPA does not purge calibration-adjustment PPAs correctly | Closed | see item |
| 1592594 | Error Purging Meter and Loading Text File (end-of-time PPA rows) | Closed (data issue) | n/a — SQL fix |
| 1684986 | TESTit 3.16 Meter Inspections causing duplicate PPAs in FC 10.2.0.22 | referenced | — |
| 1780149 | Unable to Approve PPA created by TESTit Calibration Adjustment (R1080* PORT) | referenced | — |
| 1691084 | PPA Failure — AV in FCENTERPRISEFORMS.DLL on approval open | Closed | — |
| 1119871 / 1119864 / 1119889 / 1119870 | Calculated Meter Rollup Service Issue (Dev/R1010/R1010/R1020) | Closed | tag "In Patch - FC-10.2.0.11"; SF chain adds 10.3.0.12/10.4.0.7/10.5.0.0 |

All fixed-in builds are **INFERRED** unless marked release-notes/SF-resolution-confirmed. Re-verify against release notes before telling a customer.

---

## 5. Diagnostic SQL

Environment assumptions: Oracle, schema owner `FCOWNER`, run via SQL*Plus/SQL Developer as SYSTEM unless noted. On DEV-tier metadata connections these are CONFIRMED-schema queries; client-PRD data states stay INFERRED until run there.

**D1 — Tablespace fill & headroom (SF 22-00653527 verbatim):**
```sql
with tbl as (
  select tablespace_name, count(*) num_df,
         round(sum(bytes)/1024/1024/1024,1) curr_gb,
         (count(*) * 32) max_gb
  from dba_data_files group by tablespace_name)
select t.*, (t.max_gb - t.curr_gb) grow_gb,
  (select count(*) from all_tables  where tablespace_name = t.tablespace_name and owner='FCOWNER') num_tables,
  (select count(*) from all_indexes where tablespace_name = t.tablespace_name and owner='FCOWNER') num_indexes
from tbl t order by 5;
```

**D2 — Datafiles per FC tablespace (SF 22-00528696):**
```sql
select tablespace_name, file_id, round(bytes/1024/1024/1024) file_gb,
       substr(file_name,1,90) file_name
from dba_data_files where tablespace_name like 'FC%' order by 1,2;
-- then: ALTER TABLESPACE <TS> ADD DATAFILE '<path>\<TS>_NN.FCF' SIZE 100M REUSE
--       AUTOEXTEND ON NEXT 100M MAXSIZE UNLIMITED;
```

**D3 — Unusable indexes (SF 22-00631496):**
```sql
select table_name, index_name, tablespace_name, status
from all_indexes where table_name like 'FC%' and status <> 'VALID';
select 'alter index '||index_name||' rebuild tablespace '||tablespace_name||';'
from all_indexes where table_name like 'FC%' and status <> 'VALID';
```

**D4 — Edit-reason bloat on a suspect meter (ADO 1770699 repro, verbatim):**
```sql
alter session set nls_date_format = 'mm/dd/yyyy hh24:mi:ss';
select count(*) from fc_edit_reason
where meter_number_index = (select meter_number_index from fc_meter
                            where meter_number = '<METER>')
  and effective_date = '<RECORD_EFFECTIVE_DATE>';
-- healthy: single digits per record. Bloated example: 294 rows and +1 per import.
```

**D5 — Report-schedule table size (meter-delete slowness, ADO 1723674):**
```sql
select count(*) from fc_report_schedule;
select count(*) from fc_report_schedule_param;
```

**D6 — v$ grants for FC roles (SF 26-01116701; as SYSTEM):**
```sql
GRANT SELECT ON v_$thread  TO fcuser, fcadministrator, fcowner;
GRANT SELECT ON v_$version TO fcuser, fcadministrator, fcowner;
GRANT SELECT ON v_$session TO fcuser, fcadministrator, fcowner;
```

**D7 — End-of-time PPA rows blocking purge (pattern from ADO 1592594; VERIFY meter + dates before running, take backup, then adapt):**
```sql
alter session set nls_date_format = 'mm/dd/yyyy hh24:mi:ss';
select * from fc_ppa_accounting_info
where meter_number_index = (select meter_number_index from fc_meter where meter_number = '<METER>')
  and effective_end_date = '01/18/2038 21:14:06';
select * from fc_meter_edit
where meter_number_index = (select meter_number_index from fc_meter where meter_number = '<METER>')
  and effective_end_date = '01/18/2038 21:14:06';
-- Fix (per ADO 1592594): update both tables' effective_end_date/end_time_stamp
-- to the true period end for the affected effective_date rows, then commit and purge.
```

**D8 — Purged-PPA-still-showing signature (ADO 1725795/1687000):**
```sql
select edit_type, count(*) from fc_meter_edit
where meter_number_index = (select meter_number_index from fc_meter where meter_number = '<METER>')
group by edit_type;  -- PPA edits must be 'P'; stranded 'E' rows from test-report apply are the bug.
```

---

## 6. Expected-Behavior FAQ

| Question | Answer (customer-safe) | Anchor |
|---|---|---|
| Should we partition our FLOWCAL database? | FLOWCAL doesn't target partitions in its queries, so in-app performance gains are limited. Partitioning can help storage management and external reporting. Ask for a database health assessment instead. | SF 26-01120809 |
| Tablespace keeps filling — is that a bug? | No. Database growth is routine maintenance; add datafiles as needed (each smallfile datafile caps at 32 GB). | SF 22-00584682, 22-00655078 |
| After a PRD→UAT refresh our UAT lost its upgrade/settings | Expected: the copy carries the source's version and config; redo upgrades and env-specific settings per the §3.8 checklist. | SF 23-00889577 |
| TESTit TIDX imports with attachments are slow | Expected: import time scales with attachment size; workaround is syncing/importing without heavy attachments. An enhancement request exists. | SF 25-01028463 |
| One deadlock error appeared — is data corrupted? | No; Oracle rolls back one victim statement, data stays consistent. Only a repeating pattern needs investigation. | SF 24-00978682 |
| Purging source analyses left extended characteristics behind | Known behavior gap — extended characteristics aren't included in the source-analysis purge. | SF 25-01012569 |
| Can purged data be restored in-app? | No undo; recovery is from backups/archive DB with support assistance. | SF 25-01008705, 25-01004080 |
| Which Oracle versions are supported for FC 10.x / 19c? | Route to current compatibility matrix; 19c works with the proper 32-bit client stack. | SF 23-00900478, 25-01012276 |

---

## 7. Escalation guidance

- **QCloud/hosted (FLOWCloud) environments:** tablespace adds, refreshes, service restarts, VM memory issues → QCloud ops ticket (support raises internal work item, e.g. refresh items 1711645, 1710922, 1693677 pattern). Client-managed DBs → client DBA executes the §5 SQL; support supplies scripts only.
- **Escalate to Engineering (area paths `Quorum\North America\Measurement[\Maintenance]`, `QuorumSoftware\Engineering\Measurement\Maintenance`)** only with: exact error string + `_FC_DB_ERROR.log` excerpt, app version, FcDataBoss export of the affected meter, and the §5 diagnostic outputs. Check the §4 table first — most of this skill's defects are already fixed; the correct exit is "upgrade to <version>" + interim SQL cleanup.
- **Do NOT hand-write data-fix SQL for PPA/edit-reason cleanups from memory** — reuse the ADO-anchored patterns (1592594, 1721407) and validate against the client's build, since fc_meter_edit semantics changed across 10.6.x.
- Segregated/batch-flag issues (rollup queue stuck, TQ backlog) → `batch-debugger` agent; service up/down and Transaction Queue drainage belong to the *Windows services & rollups* skill (group #3).

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
