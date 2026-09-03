# SKILL — FLOWCAL Windows Services, Rollups & Transaction Queue

> **Product:** FLOWCAL (family: FLOWCAL / TESTit / PROVEit) · **Coverage plan group #3** (~3,125 family cases, ~345 actionable)
> **Sources:** Salesforce all-history mining 2026-09-02 (~208 case subjects reviewed, ~48 resolutions read in full, `Product_list__c IN ('FLOWCAL','TESTit','PROVEit')`) + ADO org `QuorumSoftware` work-item mining (35 items). Every root-cause claim below cites SF case numbers and/or ADO ids VERBATIM.
> **Fixed-in versions:** labeled **INFERRED** when stated in SF resolutions or ADO tags — re-verify against release notes before telling a client to upgrade.
> **Auto-Bot** — built by Aditya Bhagat, Quorum Business Solutions.

Service executables covered (from FC.BoolTox `ServicesRepository.cs` + case evidence): `FcSrvTrans.exe`/`FcSrvTrans2.exe`/`FcSrvTransPD.exe` (Transaction Queue gas/PD-liquids), `FcSrvMtrRollup.exe` (Meter Rollup), `FcSrvLcnRollup.exe` (Location Rollup), `FcSrvCalcMtrRollup.exe` (Calc Meter Rollup), `FcSrvGQTrans.exe` (Source/Analysis Apply), `FCSrvGQAnlRollup` (GQ Analysis Rollup), `FcSrvAutoEstimate.exe`, `FcSrvFileImport.exe`/`FcSrvFileImport2.exe`, `FcSrvReports.exe`, `FcSrvCloseData.exe`, `FcSrvLcnCloseData.exe`, `FcSrvHCDPQueueProcessor`, `FcSrvListMembersAPI`, plus TESTit-side `FcSrvTESTitCalAdjApply.exe`, `FCSRVTESTitAnalysisSync`, `FcSrvFaImport`, `FcSrvFaExport`, `FcSrvDataManagement`, `FlowCal.FieldApplications.Integration.Service`.

---

## 1. Quick Triage

| Symptom (verbatim-ish) | Likely cause | § |
|---|---|---|
| ALL FLOWCAL services stopped at once; won't start | `FCSRV` service-account password expired or account locked | §3.1 |
| One service crash-loops daily / grows memory until it dies (pre-10.5) | Known service memory leak, fixed 10.5+ (INFERRED) | §3.2 |
| 10.8.0.0: Import + Report services won't launch under a service account | Defect, fixed 10.8.0.2 (INFERRED) | §3.3 |
| TESTit `FcSrvFaExport`/`FcSrvDataManagement`/`FcSrvFaImport` → Oracle "max processes reached" | Connection-leak defect, fixed TESTit/FieldApps X.17 (INFERRED) | §3.4 |
| TQ service stops within minutes of restart; DB error log grows | One or few poison records in `FC_TRANSACTION_QUEUE` (bad field data, e.g. battery failure, negative atmospheric pressure) | §4.1 |
| TQ crashes only when it reaches a specific meter | Poison record OR inactive meter holding a duplicate Import ID with "Check Meter Import ID first" enabled | §4.1 / §4.2 |
| TQ running but a meter never receives data; `fc_transaction_queue` query for meter is empty | Import-ID misroute to inactive meter | §4.2 |
| `FcSrvTrans2.exe` faulting module `CC32C250MT.DLL`, exception `0xc0000092` | Known TQ crash family (ADO 1868173, 1685148…) | §4.1 |
| TQ processes but Periodic data not updated / expected CV exception missing on PD meters | 10.6 TQ defects (fixed 10.6.0.15 for CV-idx case, INFERRED) | §4.3 |
| Liquids TQ batches failing with status 98 | Job-timing collision (Shakeout vs batch load into FCOWNER) or unsupported liquids TQ generation tooling | §4.4 |
| Meter/location rollup entries flip to **Postponed** | Data gap / duration errors → Duration Fix Utility; or 10.8 "Destination buffer too small!" defect | §5.1 / §5.2 |
| `_FC_SRV_LCN_ROLLUP_LOG.LOG` shows `FcAssert Failure … 'Destination buffer too small! Will truncate'` after 10.8 upgrade | 10.8 StringCopy defect family (charset conversions), garbage in `FC_METER_CHARACTERISTICS` user fields | §5.2 |
| "Unable to establish openDate in STATION:: Open …" | Invalid data in Volume Editor user-defined fields (same StringCopy family) | §5.2 |
| Locations won't roll; meters fine | DB health: unusable `FC_FFLC*_PK` indexes, invalid triggers, parallel indexes; or location direction assignments | §5.3 |
| Rollups skip analysis data when last record of day = 0 | Defect, fixed 10.5.0.20 / 10.6.0.7 / 10.7.0.0 (INFERRED) | §5.4 |
| Meter rolls but data lands on wrong hour/day; `rollup_report_id` wrong | Data-span/contract-hour edits; Duration Fix + VCF recalc regenerates ids | §5.5 |
| GQ / Source Analysis rollups postponed or "Unprocessed Analysis Apply" backlog | GQ rollup defects (fixed 10.5.0.13 INFERRED) or stalled `FcSrvGQTrans` needing restart; on-hold records need SQL cleanup | §6 |
| Auto Estimate not estimating at all | Service not installed/started, or AE settings missing on the meter | §7.1 |
| AE estimates wrong volume (raw vol posted as volume) / AE overwrites real data | Old AE defects (fixed 10.2.0.7 / 10.5 era, INFERRED) | §7.2 |
| ORA-01653 unable to extend `FC_FFMTR_HOURLY` / `FC_FFLNC…` tablespace | Tablespace exhaustion — DBA add space (KB article exists) | §5.3 |

**Cheapest-exit reminder:** most "service down" cases close as restart + account/password fix (G2 config), not code. Only route to G5 when a *specific record or version* reproducibly kills the service.

---

## 2. Decision Tree

```
Service problem reported
├─ ALL services down simultaneously?
│   └─ YES → check FCSRV service account (locked/expired?) → §3.1 (G2 config)
├─ ONE service down/crash-looping?
│   ├─ Crashes at a consistent point in the queue? → poison record hunt → §4.1 (G4 bad data)
│   ├─ Crashes on schedule (daily/after hours of uptime)? → memory leak pre-10.5 → §3.2 (G3 version)
│   ├─ Won't launch at all under service account on 10.8.0.0/0.1? → §3.3 (G3 version)
│   └─ Oracle "max processes" from TESTit Fa* services? → §3.4 (G3 version)
├─ Service RUNNING but queue not draining?
│   ├─ Transaction Queue → §4 (check UNAVAILABLE codes, Import-ID routing, poison records)
│   ├─ Meter/Location Rollup queue → Postponed? → §5.1/§5.2; silently stuck? → DB health §5.3
│   ├─ GQ/Analysis apply queue → §6
│   └─ Auto Estimate not posting → §7
└─ Data rolled/processed but WRONG →
    ├─ wrong hour/day placement → §5.5
    ├─ analysis missing when last record 0 → §5.4
    └─ AE values wrong → §7.2
```

Batch flag: these are Windows services (continuous queue processors), NOT segregated QPEC batch — do not route to the QPEC batch-debugger playbook.

---

## 3. Cluster A — Windows services down / won't start / crash

### 3.1 FCSRV account locked or password expired (ALL services stop)
- **Signature:** every FLOWCAL service down at once; services fail to log on; environment-wide import/rollup stall.
- **Root cause:** the shared `FCSRV` Windows service account is locked out or its password expired. Anchors: **25-01023295** ("Urban [PRD] - ALL FLOWCAL Services Have Stopped Working - FCSRV password has expired" — Cloud reset password + restarted services), **25-01031729** ("FCSRV account is locked and services stop working").
- **Fix recipe (from 25-01031729 resolution):** 1) stop ALL FLOWCAL services; 2) unlock the account / set new password (AD); 3) update service log-on credentials if changed; 4) start all services. On QCloud, route the reset to Cloud Ops.
- **Prevention:** non-expiring policy or gMSA for the service account; monitor for first lockout event.
- **Class:** G2 Application Configuration.

### 3.2 Service memory leak (pre-10.5) — periodic crash/restart needed
- **Signature:** long-running services (File Import, TQ, rollups) consume memory until crash; restarting "fixes" it for a while.
- **Root cause:** known memory leak in service builds before 10.5. Anchor: **25-01062691** ("FlowCal Services Running into Memory Issues" — "known memory leak issue in your version … resolved in 10.5 and later"; workaround: scheduled service restarts). Related older report: **25-01055291** (FCSRVTESTitAnalysisSync memory leak on FLOWCAL 10.2.0.30, closed No Action).
- **Fix:** upgrade to 10.5+ (INFERRED). Interim: nightly/weekly scheduled restart of affected services.
- **Class:** G3 Version.

### 3.3 10.8.0.0 — Import & Report services fail to launch under a service account
- **Anchor:** **25-01051113** ("10.8.0.0: Import service and Report service failing to launch under a service account" — Software Defect; "resolved in the 10.8.0.2 release", INFERRED).
- **Fix:** patch to 10.8.0.2+. Interim: run interactively/as app (not recommended for PRD).
- **Class:** G3 Version.

### 3.4 TESTit field-app services exhaust Oracle processes
- **Signature:** DB error "max processes are reached"; TESTit server services (`FcSrvFaExport`, `FcSrvDataManagement`, `FcSrvFaImport`) generating hundreds of sessions.
- **Anchors:** **23-00930961** (FcSrvFaExport + FcSrvDataManagement max-processes — "Will be addressed in TI X.17.0 released 5/24/24", INFERRED), **24-00969467** ("TESTit Server 3.16.1.0 - FcSrvFaImport creating too many processes in Oracle *BUG*" — "fixed in FieldApps x.17", INFERRED).
- **Fix:** upgrade TESTit/FieldApps to X.17+. Interim: DBA raise `PROCESSES` + scheduled service restarts.
- **Class:** G3 Version.

### 3.5 Miscellaneous service-down one-offs (know these exist)
- `FcSrvReports` crashed by export DLL: **26-01119134**, **26-01103514** ("Unable to access the export dll export\FCTextFileExchange.dll" — Software Defect). Reports service crash history is deep (22-00538930, 22-00712565, 22-00542156 …) — see the Reports skill for §details; triage here only to identify WHICH service is dying.
- `FcSrvHCDPQueueProcessor` stall → HCDP not calculating: **25-01016254** (restart cleared).
- `FcSrvTESTitCalAdjApply` "Failed to run process": **25-01046750** (TESTit, Software Defect), DB-log errors **25-00996566**.
- TESTit `FlowCal.FieldApplications.Integration.Service` won't start / crashes on Flow Averages: **26-01070066**, **26-01082856**; Flow Averages utility defect ADO **1687515** ("Flow Averages to TESTit (R1080* PORT)", `FlowCal.Integration.FlowAverages.exe`, `external_process_flag_7` in `fc_ffmtr_monthly`; bad/negative pulses+pressure in source data block the run).
- QCloud service-down alerts arrive as qhealth incidents (e.g. ADO **1855251** `[qcloud]-[RB0025]-[PRD-Flowcal-FCSRVFILEIMPORT ... Down]`); a "service down" SF case often has a twin myQuorum Cloud incident — search ADO for the case number.

---

## 4. Cluster B — Transaction Queue (FcSrvTrans*) stuck, crashing, misrouting

**Core table:** `FC_TRANSACTION_QUEUE` (key columns seen in fixes: `SOURCE_ID` = meter import id, `EFFECTIVE_DATE`, `TRANSACTION_TYPE` (3 = periodic record; 10 = UFM diagnostic), `UNAVAILABLE` (0 = queued/available; non-zero = parked; values used by support: 76, 107, 600, 999), `WRITE_DATE`).
**Config UI:** Settings Manager > Services > Service Configuration (DB binding) and Settings Manager > Services > Transaction Queue (queueing by meter/timeframe).

### 4.1 TQ service crashes on poison records (bad field data)
- **Signature:** `FcSrvTrans`/`FcSrvTrans2` stops within a minute or two of starting; restarting doesn't help; crash recurs when processing reaches a specific meter/date. Windows event: `Faulting application name: FcSrvTrans2.exe … Faulting module name: CC32C250MT.DLL … Exception code: 0xc0000092` (ADO **1868173**, FC 10.6.0.7, client FC_CRIP, SF 26-01124783).
- **Root causes seen:**
  - Field-hardware garbage (battery failure) in queued records — **25-00999090** ("TQ NOT PROCESSING DATA", Software Defect; ~50 meters crashing the service).
  - Specific bad meters — **25-01037835**, **26-01080984** (both "TQ NOT PROCESSING!", meters GC21583001 / 1464688604 parked via SQL).
  - Atmospheric pressure sign flip (customer sends −14.1 vs atm 14.1) — ADO **1745472** ("Transaction Queue Service keeps stopping after restarting", SF **25-01032779**).
  - Gas turbine meter records with NULL T & P — ADO **1549450** (Dev*, tag z10.5.0, Closed) + port **1563276** (R1040): crash appears 10.4.0.0+ (earlier versions failed silently); Exception 1036 = pulses not provided.
  - AGA-2013 data — ADO **1685148** (crashes in 10.5.0.16, still New) + **1802507** (port, New).
  - Snapshot records — ADO **1773284** ("TQ is crashing on snapshot record", SF 25-01062128, New).
  - Event records — ADO **1624504** ("TQ crashes trying to process events", SF 23-00923429; closed as duplicate — SF case closed because QCloud parked the data, NOT because the defect was fixed).
  - UFM diagnostic records (`transaction_type = 10`) combined with auto-estimated data — ADO **1797611** ("TQ does not process certain records", ~40 meters / ~4,000 records stuck, New).
- **Fix recipe (support-standard, from 25-00999090 / 26-01080984):**
  1. Identify the meter(s) the service dies on (last `SOURCE_ID` in `_FC_DB_ERROR` log before crash timestamps).
  2. Park the poison records so the queue drains:
     `UPDATE FC_TRANSACTION_QUEUE SET UNAVAILABLE = 600 WHERE SOURCE_ID = '<meter>' AND UNAVAILABLE = 0;` (26-01080984 used 600; 25-00999090 used 107 — any agreed non-zero park code works, keep it consistent per site) then `COMMIT`.
  3. Restart the TQ service; confirm queue drains.
  4. Harvest the parked records (FcDataBoss export) and attach to an ADO bug — this family is largely NOT fixed; several bugs still New/Proposed.
  5. Once field data corrected, requeue: `UPDATE … SET UNAVAILABLE = 0 WHERE SOURCE_ID = '<meter>' AND UNAVAILABLE = <park code>;`
- **Version notes (INFERRED from SF resolutions):** "new TQ fixes" landed in **10.5.0.9** (23-00918412); a specific-data crash fixed in **10.5.0.16**, ported 10.6.0 + DEV (24-00974152); a further 10.6 TQ bug remained open with workaround, client moved to 10.8 (25-01056281).
- **Class:** G4 Bad Data (park+requeue) with G5 secondary (crash itself is a defect — service should exception, not die).

### 4.2 TQ misroutes meter data: inactive meter owns the Import ID
- **Signature:** active meter stops receiving TQ data; `SELECT … FROM fc_transaction_queue WHERE source_id = '<inactive meter id>'` returns nothing (records sit under the ACTIVE import id); TQ service run as app crashes processing the inactive meter.
- **Root cause (fully documented in 26-01095058):** an inactive meter configured with an Import ID belonging to an active meter + service option **"Check Meter Import ID first"** enabled ⇒ all TQ records with that `sourceID` routed to the inactive meter.
- **Fix:** remove the Import ID from the inactive meter; queues route correctly immediately. Checklist (verbatim conditions from the case): (1) meter transactions missing from `fc_transaction_queue` for the expected meter, (2) meter imports by Import ID, (3) "Check Meter Import ID first" enabled, (4) an inactive meter shares the Import ID.
- **Class:** G2 Application Configuration.

### 4.3 TQ processes but output wrong / validations missing
- **PD meters, index-only imports:** TQ fails to auto-fill `measured_volume_idx_start` from prior day when only `measured_volume_idx_end` supplied ⇒ exception "CV - Measured Volume Does Not Equal Index Difference" never generated. Anchor: **25-01048300**, fixed **FC 10.6.0.15** (INFERRED).
- **TQ not updating periodic data:** **26-01064118** (App Config, resolution not recorded) — check meter TQ queueing window (Settings Manager > Services > Transaction Queue meter/timeframe) and Import-ID routing (§4.2) before assuming defect.
- **Off-hour records failing / analysis-informational clutter:** **25-01040167** — deleted informational rows from `FC_METER_ANALYSIS_ALT`, then tuned **Snap Before/After** settings to absorb off-hour records.
- **Concurrency ceiling:** running 3+ TQ services against one DB caused data-save failures — **23-00930144** ("Data Failing to Save with 3 or More TQ Services Running", App Config). Keep TQ service count within the site's validated config; scale by meter partitioning, not blind instance count.

### 4.4 Liquids TQ specifics
- **Status 98 batch failures (random batches, one meter):** **26-01115381** — timing collision between customer's Shakeout job and batch load into the `FCOWNER` schema; fixed by rescheduling (Customer process, not product).
- **Scale tickets:** liquids TQ scale tickets are processed by `FcSrvTransPD.exe` (NOT FcSrvTrans) — **22-00630173**; defect "FCSRVTRANS does not appear to work in 10.1.0.4 for scale tickets" **22-00601542** (Software Defect, ancient).
- **Third-party TQ record generators:** Autosol automated TQ record generation does **not** support liquid meters; it also flipped meter time spans (liquids must be Trails) so meters couldn't purge — **26-01118597** ("TQ GCTRANS.EXE Service Review"): stop tool for liquids, correct time span, purge + reload via CFX, reroll.
- **Oracle-side blowups:** TQ insert can fail on tablespace (`FC_METER_ANALYSIS` in `FC_MAIN_TS` — 22-00633005) or ORA-14400 partition-key on service start (22-00542183).

---

## 5. Cluster C — Meter & Location Rollups (postponed / not rolling / wrong)

**Queue tables:** `FC_METER_ROLLUP_QUEUE` (`ROLLED_UP` flag: 'I' = ignored; postponed entries visible in Settings Manager > Services > Services Queue, "Unrolled Meters" tab) and the location equivalent. Rollup destination (flow-file) tables seen in fixes: `FC_FFMTR_HOURLY`, `FC_FFLNC*` (location hourly/daily/monthly with PKs `FC_FFLCHLY_PK`, `FC_FFLCDLY_PK`, `FC_FFLCMLY_PK`), `FC_FFGQ_HOURLY`/`FC_FFGQ_DAILY` (GQ). Logs: `_FC_SRV_LCN_ROLLUP_LOG.LOG`, `_FC_DB_ERROR.LOG` — postpone reason is ALWAYS in the rollup log ("Unable to rollup Meter <X> … Postponing queue entry").

### 5.1 Postponed rollups — data-gap / duration corruption (the common case)
- **Signature:** specific meters repeatedly flip to Postponed; log shows "Unable to rollup Meter <n>"; often follows big imports, span edits, or purge/reload.
- **Root causes + anchors:**
  - Data gaps / bad durations in periodic data → **Duration Fix Utility** resolves: **26-01098300** ("Meter is postponed in Meter Rollup Queue" — Duration Fix identified and corrected a data gap), **26-01096658** (Duration Fix + purge/reload + requeue cleared postponed status).
  - Huge `flow_duration`/`flow_time` values in revision 0 → ADO **1613415** ("Meters 'Postponed' in Meter Rollup Queue (DEV)", SF 23-00900241; editing meters so flow_duration/flow_time clean up on latest revisions rolled other months).
  - VCF span edits + auto-edits (contract hour / data span TL) → ADO **1665527** (SilverBow **24-00957591**, ~1000 imported gas meters mostly postponed; newer versions respect auto-edit options older versions ignored).
  - Mixed TQ+CFX collection meters → ADO **1651048** ("Meter Rollups postponing", Western Midstream 24-00946817).
  - Historical: ADO **1572896** (Tallgrass 22-00875962), **1640891** (meters 17143/5100113 "Unable to rollup").
- **Fix recipe:** 1) read the rollup log for the named meter; 2) run **Duration Fix Utility** for the meter/date span; 3) if still postponed: Toolbox > **Recalc Rollup IDs**, then requeue (select record > Queue); 4) stubborn meters: purge + reload data, requeue (26-01096658); 5) validate in Rollup Viewer.
- **Class:** G4 Bad Data (defect-adjacent; capture FcDataBoss if reproducible).

### 5.2 Postponed rollups — 10.8 "Destination buffer too small!" (StringCopy defect family)
- **Signature:** after upgrading to 10.8.x (reported trigger 10.5.0.11 → 10.8.0.4), location/meter rollups mass-postpone; `_FC_SRV_LCN_ROLLUP_LOG.LOG` / `_FC_DB_ERROR.LOG` flooded with: `FcAssert Failure in 'void __cdecl FCSystem::CheckTruncation(size_t, const char *, size_t)' : expression: 'source_len <= destSize' is false : message: 'Destination buffer too small! Will truncate'` (SetFlowCalString.h). Side effect: garbage/unreadable characters written into `FC_METER_CHARACTERISTICS` user-defined fields; also surfaces as Volume Editor "Unable to establish openDate in STATION:: Open" errors and buffer overflow in Volume Editor.
- **Root cause (ADO 1811928 analysis):** multiple implicit charset conversions across OCI + DOA + FLOWCAL layers; FLOWCAL does not explicitly control charset. Affected: 10.8.0.4, 10.8.0.5, duplicated 10.8.0.7.
- **Anchors:** SF **26-01112398** ("Location rollups are not running properly" — full workaround), **26-01101449** ("Postponed Queues due to Destination buffer too small! Will truncate" — engineering-confirmed root cause; permanent fix planned 10.8.0.10+, INFERRED), **26-01116904** ("Unable to establish openDate in STATION:: Open" — NULLed invalid Volume Editor UDF data, requeued postponed records). ADO: bugs **1811928** (R1080* PORT; tags `10.8.0.9; 10.8 StringCopy`), **1819169** (R1090 PORT, Closed), **1819170** (DEV, Closed), **1819152** (Buffer overflow in Volume Editor), **1808959**/**1820422** (openDate/meter-close variant), RCA **1849624** (CFX import variant, `Set_user_field_s15` truncation, 10.10.0.0 dev build), cloud script ticket **1837701** ("Clear the user fields with bad data for the fc_meter_characteristic table"), qcloud incident **1810860** (FCSRVFILEIMPORT down on 10.8.0.6 with same assert). Regression sign-off for 10.8.0.9: requirement **1839078** (INFERRED fix vehicle: **10.8.0.9**, also 10.9 via `__updateDB_10.9.0.0.1_to_10.9.0.0.2.sql`).
- **Workaround recipe (from 26-01112398, verbatim):**
  1. Execute the cleanup script from WI **1837701** (clears bad user-field data in `fc_meter_characteristic`).
  2. Add to `FcDebugOptions.cfg`:
     ```
     [ALL_USERS]
     disable_string_copy_checks = Y
     ```
  3. Restart affected services.
- **Permanent fix:** upgrade to 10.8.0.9+/10.9 (INFERRED — confirm release notes).
- **Class:** G3 Version (workaround is config+data cleanup).

### 5.3 Rollups stuck/slow — database health (Oracle)
- **Unusable PK indexes + invalid triggers:** locations would not roll at all → validated constraints, fixed `FC_SECTION_TRIGGER` and `FC_SRV_REGISTRATION_TRIGGER`, rebuilt unusable indexes `FC_FFLCHLY_PK`, `FC_FFLCDLY_PK`, `FC_FFLCMLY_PK` — **25-01047578** ("Location Rollups not being Rolled up by the Service"; general DB-health script used).
- **Parallel indexes degrade rollup:** location rollup "getting stuck" fixed by setting ALL indexes NOPARALLEL (stop services → run NoParallel statements → start services) — **26-01115068** (Flywheel PRD).
- **Tablespace exhaustion:** `ORA-01653: unable to extend table FCOWNER.FC_FFMTR_HOURLY … tablespace FC_ROLLUPS_FFMTRHLY_TS` — **26-01079753**; same for `FC_FFLNC…` — **25-01048708**. Fix: DBA adds datafiles/autoextend (KB article exists per 26-01079753).
- **Rollup service performance defect (V10 Calc Meter Rollup):** **23-00876717** — resolved in **10.5.0.0 GA, 10.4.0.7, 10.3.0.12** (INFERRED).
- **Location direction assignments:** location failing to rollup resolved by re-assigning directions to location entries — **26-01119203**.
- **Class:** G4 Bad Data / environment (DBA work), except the perf defect (G3).

### 5.4 Rollups silently skip analysis data when last record of day is 0
- **Anchor:** **24-00949117** ("ROLLUPS NOT ROLLING ANALYSIS DATA WHEN LAST RECORD OF DAY IS 0" — Software Defect). Resolution lists fix vehicles (INFERRED): **10.5.0.20** (PR-14190), **10.6.0.7** (PR-14191), **10.7.0.0** (PR-14417), **10.8.0 DEV** (PR-14188).
- **Class:** G3 Version.

### 5.5 Rolled-up data on wrong hour/day; `rollup_report_id`/`measurement_day` wrong
- **Signature:** volume exists in Volume Editor at hour X but appears at X+1 (or missing) in Rollup Viewer; meters "not rolling up the changes".
- **Anchors:** **26-01090240** ("Meters are not rolling up the changes due to incorrect rollup_report_id" — workaround: run **Duration Fix Utility** then **force VCF recalculation**; reapplies density, writes a new revision in `fc_meter_periodic_values`, and FLOWCAL reassigns `rollup_report_id` + `measurement_day`. May generate new exceptions — validate in UAT first). ADO **1785473** ("Flow Times and Volumes are wrong due to data span changes (R1060* PORT)", SF 26-01082533, Closed — contract hour 0/time-leads misalignment; Toolbox 'Recalc Rollup IDs' + 'Run Duration Fix' insufficient pre-fix).
- **Related defects:** DST spring-forward day leaves location completion status incomplete — **26-01091855** (repro 10.5.0.16; not reproducible 10.9/latest 10.5 patch — INFERRED fixed); 1st day of month incomplete for Time-Trails daily meters — **25-01059906** (product backlog, workaround exists); rollups not condensing characteristic slices (perf) — ADO **1388733** (10.4.0.0, Closed; data condenser tool is the manual equivalent); Rollup Queue Ignore button doesn't hide ignored postponed rows — ADO **1653003** (DEV*, New; ignore = `ROLLED_UP='I'` in `FC_METER_ROLLUP_QUEUE`).
- **Class:** G4 with G5 secondary.

### 5.6 Rollup service crashed / "just restart it" pattern
Plain restarts closed: **25-01043643** (Meter Rollup Service Disconnected), **26-01106915** (FcSrvLcnRollup restarted, queue drained), **26-01112248**, **26-01093995**, **26-01120775**. RCA-grade repeat failures: **25-01047514** (RCA for 25-01047433 — Software Defect; "See ADO attached to this case"), **26-01067345** (Performance RCA). If the same env restarts >2×/month, stop closing as restart — pull the rollup log around each death and open/locate the ADO bug.

---

## 6. Cluster D — GQ / Source Analysis apply & GQ rollups (FcSrvGQTrans, GQ Anl Rollup)

- **Unprocessed Analysis Apply backlog (month-end blocker):** **25-01055681** ("PRD not processing analysis data. Unprocessed analysis apply has items from 10 this morning" — multiple service restarts got it draining; App Config), **26-01103970** ("Unprocessed Analysis Apply Service Queue / FcSrvGQTrans services" — queue tuning session, App Config).
- **GQ Rollups Not Processing:** **24-00971722** — Software Defect, "fixed in **10.5.0.13** and ported to dev and 10.6" (INFERRED).
- **GQ Rollups postponed (insert-vs-update defect):** ADO **1374706** ("GQ Rollups Postponed (R1020 PORT)", Closed) — service tried INSERT instead of UPDATE into `FC_FFGQ_HOURLY`/`FC_FFGQ_DAILY`; support cleanup pattern: delete the FF rows for the `gqsource_index` then requeue the postponed source (Settings Manager > Services > Service Queues > select Source > All Data > Save > run GQ Anl Rollup service).
- **Chromatograph hourly gap-fill regression:** ADO **1388284** ("Monthly heating value discrepancy … (R1020 PORT)", Closed) — 10.1.0.11 stopped creating `fc_ffgq_hourly` gap records between multi-hour samples vs 8.10.50; shows in GQ Rollup Viewer monthly totals.
- **On-hold analysis records blocking the GQ Analysis Rollup:** removed with SQL by support — **25-01055810** ("Removing on hold records in the GQ Analysis Rollup", App Config).
- **Install/scale:** second/parallel GQ services get installed by Cloud on request — **25-00999483** (FCSrvGQAnlRollup service install).
- **Class:** mostly G2/G4; the two ADO defects are G3 when client is on affected versions.

---

## 7. Cluster E — Auto Estimate service (FcSrvAutoEstimate)

**Tracking table:** `fc_autoestimate_tracking` (per-meter watermark; delete a meter's row to force AE re-run — see ADO 1119293 repro). AE config lives on the meter: Meter Editor > Services tab > Auto Estimate tab (Estimate Techniques, reference location, multiplier).

### 7.1 AE "not working" at all
- **Most common:** service not installed/started, or AE settings absent on the meter. Anchors: **23-00925895** ("Why is Auto Estimate not working?" — Cloud installed+started the service, then configured AE settings on the meters), **24-00995466** (install AE service in UAT), **23-00933322** / **23-00934306** (install + configure AE service run times), **23-00917751** ("Auto Estimate not available in Production anymore" — App Config).
- **Liquids AE dead in 10.5.0.1:** **23-00914558** — "fixed in **10.5.0.8**" (INFERRED).
- **Bulk Change can't set AE settings on liquid meters:** **24-00995522** (App Config/limitation).
- **Class:** G2 first; G3 only for the 10.5.0.x liquids window.

### 7.2 AE producing wrong data / colliding with real data
- **Pulses not calculated with AE enabled:** **25-01024811** — known bug, fixed **FC 10.6.0.7** (INFERRED).
- **AE overriding original (real) data:** **22-00823255** ("AE overriding original data" — Software Defect; "no longer an issue in FLOWCAL 10.5", INFERRED). Interplay detail (ADO 1549450 description): when real data later arrives via TQ and replaces AE records, energy recalcs on the AE records only.
- **AE via reference location posts RAW volume as volume:** ADO **1119293** (Dev) / **1119292** (R1020 — fix tag Release 10.2.0.7) / **1119294** (R1003 — fix tag 10.0.3.16). All Closed.
- **Exception floods from AE:** 'MD - Data has been auto estimated' exception volume reduction has a known solution pattern; 10.9 no longer generates 'Pulses Not given' exception — ADO **1863605** (FC_XCLP, 10.5.0.21, Closed).
- **Class:** G3 Version for all three defects; G2 for exception-flood tuning.

---

## 8. Known ADO items (org QuorumSoftware) — cite VERBATIM ids

| ADO id | Type | Title (abridged) | State (mining date) | Notes |
|---|---|---|---|---|
| 1868173 | Bug | TQ crashes (FcSrvTrans2.exe / CC32C250MT.DLL 0xc0000092) | New | FC 10.6.0.7, FC_CRIP, SF 26-01124783 |
| 1834281 | Bug | Transaction Queue Service crashes | Closed | repro parks/unparks UNAVAILABLE 76↔0 |
| 1685148 / 1802507 | Bug | TQ service crashing on AGA-2013 data (+port) | New | crashes 10.5.0.16 |
| 1797611 | Bug | TQ does not process certain records | New | transaction_type=10 (UFM) + autoestimate combo |
| 1773284 | Bug | TQ is crashing on snapshot record | New | SF 25-01062128 |
| 1624504 | Bug | TQ crashes trying to process events | Closed (Duplicate) | SF closed via SQL parking, defect NOT fixed |
| 1745472 | Bug | TQ Service keeps stopping after restarting | Proposed | SF 25-01032779; −14.1 atm pressure |
| 1549450 / 1563276 | Bug | Gas turbine meter crashes when T and P not provided (Dev*/R1040) | Closed | z10.5.0; Exception 1036 |
| 1811928 / 1819169 / 1819170 | Bug | Postponed Queues due to Destination buffer too small! (R1080*/R1090/DEV) | Closed | 10.8 StringCopy; fix tag 10.8.0.9 (INFERRED) |
| 1819152 | Bug | Buffer overflow error in volume editor | Closed | same family |
| 1808959 / 1820422 | Bug | Error when closing meter data / viewing volumetric data 10.8.0.5 (+DEV) | Closed | "Unable to establish openDate"; SF 26-01100778 harvest |
| 1849624 | RCA Request | Import CFX crash, Set_user_field_s15 truncation | New | family recurrence on 10.10 dev |
| 1837701 | Request Global Cloud Ops | Clear bad user fields in fc_meter_characteristic (26-01112398) | Closed | the cleanup-script vehicle |
| 1810860 / 1855251 | Cloud ops items | FCSRVFILEIMPORT down w/ same assert / qhealth RB0025 | Closed/New | 10.8.0.6 / 10.8.0.9 |
| 1839078 | Requirement | 10.8.0.9 Manual regression and AT run | Closed | regression proof for StringCopy fixes |
| 1665527 | Bug | SilverBow — gas meter rollups failing (postponed) | New | SF 24-00957591; VCF span edit + auto edit |
| 1651048 | Bug | Meter Rollups postponing (TQ+CFX meters) | Closed | SF 24-00946817 |
| 1613415 | Bug | Meters "Postponed" in Meter Rollup Queue (DEV) | Closed | huge flow_duration/flow_time rev 0; SF 23-00900241 |
| 1640891 | Bug | Meters Postponed in the Meter Rollup Queue | Closed | "Unable to rollup Meter <17143>" |
| 1572896 | Bug | 22-00875962 Meter Rollup postponement | Closed | Tallgrass |
| 1653003 | Bug | Rollup Queue - Ignore Button (DEV*) | New | FC_METER_ROLLUP_QUEUE.ROLLED_UP='I' |
| 1785473 | Bug | Flow Times and Volumes wrong due to data span changes (R1060*) | Closed | SF 26-01082533; rollup_report_id fix |
| 1388733 | Bug | Meter rollups do not condense characteristics (Dev*) | Closed | 10.4.0.0 |
| 1374706 | Bug | GQ Rollups Postponed (R1020 PORT) | Closed | insert-vs-update into FC_FFGQ_* |
| 1388284 | Bug | Monthly heating value discrepancy (R1020 PORT) | Closed | chromatograph fc_ffgq_hourly gap fill |
| 1119292 / 1119293 / 1119294 | Bug | AE using reference location posts raw volume as volume | Closed | fixes 10.2.0.7 / 10.0.3.16 (tags) |
| 1863605 | Bug | Reduce or Eliminate Exceptions (AE 'MD' flood) | Closed | FC_XCLP, 10.5.0.21 |
| 1687515 | Bug | Flow Averages to TESTit (R1080* PORT) | Closed | FlowCal.Integration.FlowAverages.exe |

Area paths: `Quorum\North America\Measurement(\Maintenance)`, `QuorumSoftware\Engineering\Measurement\Maintenance` (DEV/PORT copies — title suffix `(R1080* PORT)`, `(R1090 PORT)`, `(DEV)`), `myQuorum Cloud\QCloud Ops\*` for QCloud restart/script tickets. Bugs usually embed the SF case number + "Case Owner - {name}".

## 9. Diagnostic SQL (Oracle, FCOWNER schema — real queries from case fixes; verify env before running)

```sql
-- TQ backlog by meter and park code (from 25-00999090 / 26-01080984 fix pattern)
SELECT source_id, unavailable, COUNT(*), MIN(effective_date), MAX(effective_date)
FROM fc_transaction_queue
GROUP BY source_id, unavailable
ORDER BY COUNT(*) DESC FETCH FIRST 25 ROWS ONLY;

-- Is a specific meter's data queued? (26-01095058; empty result + import-by-ID meter => check Import-ID misroute)
SELECT * FROM fc_transaction_queue
WHERE source_id = '<import_id>' AND unavailable = 0 AND transaction_type = 3
FETCH FIRST 25 ROWS ONLY;

-- Park poison records so the TQ drains (support-standard; pick a consistent park code)
UPDATE fc_transaction_queue SET unavailable = 600
WHERE source_id = '<meter>' AND unavailable = 0;
COMMIT;
-- Requeue after correction:
UPDATE fc_transaction_queue SET unavailable = 0
WHERE source_id = '<meter>' AND unavailable = 600;
COMMIT;

-- Force Auto Estimate to re-evaluate a meter (ADO 1119293 repro)
DELETE FROM fc_autoestimate_tracking
WHERE meter_number_index = (SELECT meter_number_index FROM fc_meter WHERE meter_number = '<meter>');
COMMIT;

-- GQ rollup FF-row cleanup before requeue (ADO 1374706 pattern)
DELETE FROM fc_ffgq_hourly WHERE gqsource_index =
  (SELECT gqsource_index FROM fc_gq_source WHERE gqsource_number = '<source>');
DELETE FROM fc_ffgq_daily  WHERE gqsource_index =
  (SELECT gqsource_index FROM fc_gq_source WHERE gqsource_number = '<source>');
COMMIT;
```
Data-parking and DELETE statements are PRD-invasive: snapshot rows first, run in UAT where possible, and on QCloud route execution through Cloud Ops (pattern: WI 1837701).

## 10. Expected-Behavior FAQ

- **"A list/meter was closed by FCSRV — who did that?"** `FCSRV` is the service account; scheduled close services (`FcSrvCloseData`, Schedule Close Dates Editor config) act under it. Not a rogue user. (26-01107895, 25-01007145 — both Training/No Action.)
- **"How often should FcSrvReports (or any service) be restarted?"** Healthy modern versions: not on a schedule. Scheduled restarts are only a sanctioned workaround for the pre-10.5 memory leak (25-01062691) — see 22-00655065 (ancient FAQ case).
- **"TQ service is 'locking data'."** The TQ takes row locks while processing; sustained locks usually mean it is grinding a big queue, not hung (23-00885962 — Training).
- **"Records show Postponed — is my data lost?"** No. Postponed = rollup deferred; the periodic data is intact. Fix the cause, requeue (select > Queue). Ignored postponed rows remain visible in the grid by design-gap (ADO 1653003).
- **"Auto Estimated volumes changed when accepted / were replaced by import."** By design: real data arriving via TQ or file import replaces AE data; AE records recalc energy on replacement (22-00824522; ADO 1549450 description). Liquid meter text imports NOT replacing AE data was Training (24-00982859).
- **"Multiple FcSrv requests — can we run N instances of a service?"** Only per validated config; 3+ TQ services caused save failures at one site (23-00930144). Second instances of GQ/Reports services are a Cloud install request, not a toggle (25-00999483).

## 11. Escalation guidance

1. **Restart-loop rule:** >2 restarts/month for the same service+env → stop treating as ops noise. Pull `_FC_DB_ERROR.LOG` + the service's own log around each death, identify last `Source id:` processed, and search ADO for an existing bug (this cluster has many New/Proposed bugs; attach, don't duplicate).
2. **Harvest before you park:** before parking TQ rows or purging rollup data, export the meter via FcDataBoss and note exact SQL run — engineering repro depends on it (every TQ bug above carries a `\\qddfcfs01.qdev.net\DATA\CustomerData\<client>\<case>` harvest).
3. **10.8.x clients with postponed queues:** check for the StringCopy assert FIRST (§5.2) — it mimics generic data-gap postponement but needs the script + cfg workaround, and upgrade to ≥10.8.0.9 (verify release notes).
4. **QCloud:** service restarts, script execution, and account unlocks go through Global Cloud Ops work items (`myQuorum Cloud` project); reference the SF case number in the WI title per convention.
5. **Handoff packet for G5:** service name+exe, product version (exact 4-part), Windows event (faulting module/exception code), last Source id, park SQL used, FcDataBoss file location, and matching ADO id(s) from §8.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
