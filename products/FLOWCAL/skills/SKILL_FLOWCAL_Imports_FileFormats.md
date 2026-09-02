# SKILL: FLOWCAL Family — Imports & File Formats (CFX / GQ / Ticket / Text / TIDX / PIDX / Import Drivers)

**Version:** 1.0 | **Created:** 2026-09-02 | **Products:** FLOWCAL (10.x), TESTit (3.x), PROVEit (9.x) — `Product_list__c IN ('FLOWCAL','TESTit','PROVEit')`
**Scope:** Group #1 of the FLOWCAL Coverage Plan — everything that enters the system through a file: `.cfx` (Common File eXchange, gas + liquids per-meter data), GQ source text files, gas/liquid meter text files, liquid ticket files (tank gauge / LACT / LQTICKET), custom import drivers (`.dll`), the **File Import Service** family (`FcSrvFileImport.exe` … `FcSrvFileImport4.exe`), control files (`.ctl_F_*`), and the field-app exchange formats **TIDX** (TESTit) / **PIDX** (PROVEit).
**Evidence base:** ~140 closed family cases reviewed across 8 SOQL sweeps (Subject LIKE on `CFX`, `file import`, `FcSrvFileImport`, `GQ … import`, `ticket import`/`Message 321`, `TIDX`/`PIDX`, `Scout`/`import driver`, + `Case_Category__c IN ('Meter Imports','Ticket Imports','Import Drivers')` actionable sweep), prioritized on `Root_Cause__c IN ('Software Defect','Application Configuration')`; ~45 cases cited below. ADO org `QuorumSoftware`, projects `Quorum` + `QuorumSoftware`, ~30 work items cited (note the `(DEV)` / `(R1080* PORT)` / `(R1090 PORT)` port-bug title convention).
**Caveats:** All "fixed in <version>" claims are **INFERRED** from support-stated case resolutions or ADO tags unless marked release-notes-confirmed. The SF MCP connector intermittently returned crossed result-sets during mining; every cited case number below came from a result row whose Subject/Resolution matched the import domain.

> **Use when:** files stop importing or fail to failed-files folders; the File Import Service is down/stuck/crashing/looping; a CFX imports but the data doesn't land (or lands on the wrong meter); GQ source text files error; liquid tickets won't import or won't recalculate; TIDX/PIDX imports fail on a TESTit/PROVEit laptop or server; a custom import driver misbehaves; SFTP/FTP file delivery into the import folder breaks.

---

## 1. Quick Triage Table

| Symptom (message / behavior) | Likely cause | Class | § |
|---|---|---|---|
| ALL imports stopped; service shows stopped/hung; restarting fixes it | File Import Service crash/hang (memory leak in ≤10.3.x; corrupt file; stuck lock) | Config/Version | §4 |
| Valid CFX files land in `zFailedFilesArchive` even though data would import; orphaned control files; DB locking | **Multiple File Import Service instances watching the same folder** — race condition (10.5.0.6) | Version | §4.2 |
| `Faulting module CC32C250MT.DLL, exception 0xc0000092` on `FcSrvFileImport2.exe`; `Failed to Rename File …cfx` in Event Viewer | Known service crash signature (10.5.0.14) | Version | §4.3 |
| CFX with split-time record fails: "string buffer overflow" / `OverlappingStringBuffering` / `Destination buffer too small! Will truncate` (10.8.0.3–10.8.0.6) | 10.8 StringCopy hardening defect; bad datatype byte in CFX event record | Version | §5 |
| CFX import → PK violation (`Error (201) (1): Unable to save data`), only for data spanning early March / DST | DST duplicate-hour PK collision | Version | §6.1 |
| CFX with hundreds of events → "duplicate events" error, `_fc_db_error` log, PK collision | Duplicate events in CFX not deduped on import | Version | §6.2 |
| **Liquids** meter CFX starts failing ~21st of each month; "excessive number of data records encountered (65000+)" | `FC_EDIT_REASON` explosion (Source Analysis Apply reasons per record) + Liquid Rounding interplay | Version/Data | §6.3 |
| CFX "processed, not failing" but meter data never updates | Duplicate `DEFAULT_IMPORT_FILE` on two meters in `FC_METER` (routing conflict), or service-only defect | Data/Version | §7.1 |
| CFX fails only for specific meters; junk in Volume Editor / Meter Characteristics user-defined fields | Bad data written to user-defined fields by an earlier import — NULL them | Data | §7.2 |
| CFX imports but meter configuration/characteristics don't update | Service Configuration **Ignore Configuration Snapshots = Yes** | Config | §7.3 |
| Warning: meter locked already when service tried to lock it (10.6.0.15+) | Benign inter-service lock message — ignore | Expected | §7.4 |
| Meters permanently locked, "abnormal program termination" on import | Locked-meter defect ≤10.6.0.13 — restart services; fixed 10.6.0.14 / 10.8 (INFERRED) | Version | §7.5 |
| `.ctl_F_*` control files piling up / not moving / "Control Exceeds Retry Count" | Control-file handling defect in 10.5.x — fixed 10.5.0.13 / 10.6.0.2 (INFERRED) | Version | §8 |
| GQ source text files sit unprocessed while CFX imports fine | Import path / per-service folder targeting in `FcDebugOptions.cfg` | Config | §9.1 |
| GQ import "inconsistency" on auto-created sources; missing from-date in file | Deferred defect ADO 1598743 — purge+reimport or add full from/to timestamps | Version (deferred) | §9.2 |
| GQ import fails w/ extended-analysis DB error; hundreds of Duration Fix errors | Extended-analysis duration corruption — Duration Fix utility | Data | §9.3 |
| `ORA-02291 (FCOWNER.FC_METANL_F_LAB_ANALYSIS_ID)` importing CFX/GQ | Same source sent multiple times in month — purge sources, reload one | Data | §9.4 |
| Import service crashes on GQ files after validation edits | GQ Frozen-Value/Expert-Systems validation Window count set outside 1–24 limit | Config | §9.5 |
| `FLOWCAL Message 321: Ticket import failure` email | Ticket import failure notification (check file + email contact list) | Data/Config | §10.1 |
| Tank-gauge ticket **revision** imports don't recalculate | Defect — fixed 10.2.0.8 / 10.3.0.0 (INFERRED) | Version | §10.2 |
| Manual liquid text/ticket import from Dashboard hangs indefinitely | Defect — fixed 10.2.0.16 (INFERRED) | Version | §10.2 |
| Meter TXT import w/ create-revisions → `ORA-00001 (FCOWNER.FC_METPER_PK)` | Open defect ADO 1766053 (10.3.0.24, 10.6.0.7) | Code | §10.3 |
| Text files fail; log shows `FcSrvGasMeterTextFileImport` exception in `FcSrvFileImport4.exe` (10.8.0.5) | Defect — fixed 10.8.0.7 (INFERRED) | Version | §10.3 |
| TIDX import unprotects/unlocks meters on TESTit server | Defect — fixed TESTit 3.16.2 / 3.17.1 (INFERRED) | Version | §11.1 |
| TIDX import fails "while importing notes" or app hangs on import | `fa_user_activity_log` bloat — truncate + disable activity logging | Data | §11.2 |
| TIDX "Error occurred in Import: Sequence contains more than one matching element" / merge-two-unique-meters error | Duplicate meter/device unique-ID conflict — ADO 1741593 | Code/Data | §11.3 |
| TIDX won't import across versions (3.16 → 3.17) | TIDX files are not backward/forward compatible across minor versions | Expected | §11.4 |
| TESTit 3.19 server: TIDX from 3.16 laptops fails / partial | ADO 1862622 (open investigation) | Code | §11.4 |
| PIDX import log: meter/prover skipped | PROVEit x.19 **Create New Devices on Import = No** (foreign devices ignored) — informational | Expected/Config | §11.5 |
| TIDX/PIDX import OutOfMemoryException or fails only on one laptop | Local DB bloat/corruption — truncate activity log or recreate DB (strongDB / DBSetup / Password Utility) | Data | §11.6 |
| Custom driver (KRAOU.dll etc.) imports but never renames/archives files; re-imports in a loop | Custom-driver archive defect — fixed 8.11.37.22+ / 10.4.0.0 (INFERRED) | Version | §12.1 |
| Import drivers dead after upgrade (Fisher/NiMerc/Mercury) | Driver DLL not rebuilt for new FLOWCAL version — request updated driver | Config/Version | §12.2 |
| Files never arrive in import folder (SFTP/FTP/WinSCP errors) | Transport plumbing: credentials, folder permissions, service account | Config | §13 |
| Service won't start / "unable to save to the registry" / no processed-folders created | Service account privileges; run FLOWCAL as admin to edit config; full UNC paths | Config | §13 |

---

## 2. Import Pipeline & Concepts

```
[SCADA / CFX exporters / labs / field apps]
      │  SFTP/FTP/WinSCP/robocopy → import folder (e.g. F:\FTProot\Imports\...)
      ▼
File Import Service (FcSrvFileImport.exe, FcSrvFileImport2/3/4.exe — one Windows service each)
      │  Service Configuration: Settings Manager > Services > Service Configuration
      │  Per-service folder targeting + debug switches: FcDebugOptions.cfg
      │  Subfolder conventions: CFX / GQSourceTextFiles / MeterTextFiles / MeterTextFilesByImportId
      ▼
Parse via format driver (built-in CFX/GQ/text/ticket, or custom .dll import driver)
      │  success → archive/rename; failure → zFailedFilesArchive + _fc_db_error / _FC_FILE_IMPORT.LOG
      │  control files: <file>.ctl_F_<timestamp>; unmapped files → .cf_U_* / .cf_F_* (System Msg 122/123)
      ▼
FLOWCAL DB (FC_METER routing via IMPORT_PATH / DEFAULT_IMPORT_FILE; data → periodic tables,
            FC_METER_ANALYSIS / FC_METER_ANALYSIS_ALT, FC_EDIT_REASON audit rows)
      ▼
Downstream: rollups (FcSrvMtrRollup), GQ apply (FcSrvGQTrans), TESTit/PROVEit sync (TIDX/PIDX, WebSync)
```

Key facts (all anchored):
- **Multiple service instances** are created by copying `FcSrvFileImport.exe` → `FcSrvFileImport2.exe`, … and installing each (SF 22-00588724; ADO 1864320 repro steps). Service Configuration has a "Number of Installations" field (ADO 1435804 repro).
- **`FcDebugOptions.cfg`** (install dir) drives per-service behavior: per-service import folders (SF 26-01123435), `[ALL_USERS] disable_string_copy_checks = Y` (SF 26-01117182), `[FCSRVFILEIMPORT] unmapped_file_action = U|F` → renames unmapped files `.cf_U_*`/`.cf_F_*` and System Messages 122/123 (ADO 1658113).
- **Logs:** `_FC_FILE_IMPORT.LOG`, `_FC_FILE_LIST_FcSrvFileImport.exe.LOG` (grows forever unless "Log Processed Files" unchecked — SF 22-00594877), `_fc_db_error*` files, Windows Event Viewer (service crashes).
- **Meter→file routing** lives in `FC_METER.IMPORT_PATH` / `FC_METER.DEFAULT_IMPORT_FILE` joined to `FC_SYSTEM` (SF 26-01099018 — SQL in §15).
- One CFX can carry data for multiple meters, but the duplicate-DEFAULT_IMPORT_FILE path is broken (SF 26-01099018: "capability… currently not working as expected").

---

## 3. Decision Tree

```
File import problem reported
│
├─ Are files reaching the import folder at all?
│   NO → §13 transport plumbing (SFTP creds SF 26-01064375; FTP folder perms SF 25-01046902;
│         WinSCP missing SF 26-01110322; service account SF 26-01122122/24-00986595)
│
├─ Is the File Import Service running?
│   NO/HUNG → restart first (§4.1). Recurring? → version check:
│       ≤10.3.x memory-leak (SF 25-01037086) · 10.5.0.6 multi-service race (SF 26-01116119)
│       10.5.0.14 CC32C250MT.DLL 0xc0000092 crash (ADO 1710336) · corrupt CFX in folder (SF 26-01121466)
│
├─ Files FAIL (failed-files folder / error log)?
│   ├─ Error mentions string buffer / Destination buffer too small (10.8.0.3–10.8.0.6) → §5
│   ├─ PK violation → DST window? §6.1 (ADO 1805452) · duplicate events? §6.2 (ADO 1565807)
│   │                 TXT-with-revisions FC_METPER_PK? §10.3 (ADO 1766053)
│   ├─ Liquids meter, fails from ~21st of month → §6.3 (ADO 1839777 family)
│   ├─ GQ text file → §9 · Ticket file → §10 · TIDX/PIDX → §11 · custom driver → §12
│   └─ Only specific meters → bad user-defined-field data §7.2, product-code alias §6.3, meter locked §7.5
│
└─ Files SUCCEED but data wrong/missing?
    ├─ No data on target meter → duplicate DEFAULT_IMPORT_FILE §7.1 (run §15 SQL)
    ├─ Config/characteristics not updating → Ignore Configuration Snapshots §7.3
    └─ TESTit task/test-report data not flowing on → known sync defects §11.1/§11.7
```

Gate mapping: restart-and-runs-clean → **Config (G2)**; version-signature match → **Version (G3)**; meter-specific bad rows → **Bad Data (G4)**; reproducible in current build with no fix → **Code (G5)** with ADO reference.

---

## 4. Cluster — File Import Service down / stuck / crashing

### 4.1 Restart-first playbook (highest-frequency ticket in this group)
**Signature:** no files processing in any format; service stopped, or running but idle/"in limbo"; sometimes only after server patching/reboot weekend.
**Fix recipe:** restart the File Import Service(s) (QCloud clients: cloud team does it — buttons exist in some Citrix environments). If a specific file crashed the service, move/rename it out of the import folder first, then restart; hand the corrupt file back to the SCADA team.
**Anchors:** SF 26-01122093, 26-01121466 (crashed on `562751116.cfx` — corrupt archive; renamed file, service stable), 26-01092889 ("stuck in limbo… failing files even though there was no file issue"), 26-01091169, 26-01119473, 25-01023324, 25-01028197 (slowness fixed by restart), 25-01025373 (services not started after Sunday server restart), 26-01118892, 26-01117773, 22-00637683, 22-00542425. TESTit variant: 25-01029776 (TIDX import service crashed — restart). Ops ADO: 1734447 / 1735969 / 1736212 (SF 25-01024220 FC_MNAP), 1606978 (restart button request, SF 23-00905239).
**Recurring-crash workaround:** scheduled nightly service restart (Windows task + PowerShell) — deployed for Salt Creek on 10.3.0.17 pending upgrade; "major fixes to the file import services including memory-leak fixes" in later versions (SF 25-01037086; memory-leak history back to SF 22-00550993 "will resolve with R-01714"). Version-track fixes are **INFERRED**: 10.4.1.0 added retry/control-file handling; 10.5.x/10.6.x improved memory, file locking, DB interaction (support statement on SF 26-01109002).

### 4.2 Multiple service instances on one folder — race condition (10.5.0.6)
**Signature:** valid files intermittently "fail" and land in `zFailedFilesArchive`; orphaned control files; DB locking; a second service moved/renamed the file mid-process.
**Root cause (CONFIRMED via support RCA):** ≥2 File Import Service instances monitoring the same import directory in 10.5.0.6 race each other. **Fix:** upgrade to 10.5.0.14+ (10.5.0.27 / 10.9.0.1 recommended); interim: one service per directory (per-service folders via `FcDebugOptions.cfg`, §9.1 pattern).
**Anchors:** SF 26-01116119 (full RCA in resolution). Active engineering follow-up: ADO 1864320 "Import services consistently throwing errors and appear to be causing missing data" (Escalated, New, Aug 2026 — repro = 3 copied `fcsrvfileimport*.exe` on one folder).

### 4.3 Service crash signature: `CC32C250MT.DLL`, exception `0xc0000092`
**Signature:** Event Viewer: `Faulting application FcSrvFileImport2.exe … Faulting module CC32C250MT.DLL … Exception code 0xc0000092`; import log ends with `Failed to Rename File <path>.cfx`; monthly-boundary correlation reported. FLOWCAL 10.5.0.14 (MarkWest).
**Status:** ADO 1710336 (Quorum project, Bug, state New — investigation). App data itself stayed correct; treat as service-level crash, restart + monitor, escalate with Event Viewer entries + `_FC_FILE_LIST` logs attached.
**Anchors:** ADO 1710336 (SF 24-00992056 referenced inside). Related loop bugs: ADO 1865409 (MBS files — continuous processing loop referencing a meter not in the files, New), SF 26-01106006 (meter 8703 import infinite loop, FC_CFLP).

---

## 5. Cluster — 10.8 StringCopy defects: "string buffer overflow" / "Destination buffer too small"

**Signature:** after upgrading to 10.8.0.3–10.8.0.6, CFX files fail (manual + service) with string-buffer-overflow errors; classic trigger is a split-time record or a bad datatype byte in a CFX event record. `FC_CFLU 10.8.0.3: "No files are being imported; all import files are sent to the failed files folder"` (same meters fine on 10.3.0.16).
**Root cause:** string-copy bounds checking introduced in the 10.8 stream rejects records older builds tolerated. Engineering fixed the overflow itself; fixed-in: **10.8.0.7** (ADO 1789257 tag `"10.8.0.7`; SF 26-01105507) and **10.8.0.8** (SF 26-01110644, 26-01111659 event-import variant), ported to **10.9.0.1** (ADO 1805980 tag). All INFERRED from tags/case text.
**Workaround (support-applied, CONFIRMED):** `FcDebugOptions.cfg` → `[ALL_USERS]` `disable_string_copy_checks = Y`, restart services (SF 26-01117182). Use only as a bridge to the patch.
**Anchors:** ADO 1790015 (DEV, Closed, tag `10.8 StringCopy`; SF 26-01087353 Coastal Flow, repro: orifice meter 3008 + provided cfx), 1789257 (R1080* PORT, Closed), 1805980 (R1090 PORT, Closed). SF 26-01105507 ("split time record — String buffer overflow… resolved in 10.8.0.7"), 26-01110644 ("OverlappingStringBuffering… upgrade to 10.8.0.8"), 26-01117182 (workaround), 26-01118955 (Foundation Energy — env needs 10.8.0.9).

---

## 6. Cluster — CFX fails with PK violations / duplicate data

### 6.1 DST duplicate-hour PK violation
**Signature:** meters stop importing after the March DST switch date; manual import → `Error (201) (1): Unable to save data` + meter PK violation; setting import start date past the DST hour lets data in.
**Root cause:** DST hour duplication on save. Fixed (Closed): ADO 1805452 (DEV) → port ADO 1814628 (R1080 PORT, tag `"10.8.0.9`) — the same PR also resolves ADO 1800154 ("A list of meters have stopped importing as of 4/14/2026"). Fixed-in 10.8.0.9 INFERRED from tag.
**Anchors:** ADO 1805452 / 1814628 / 1800154 (SF 25-01008137, Venture, meter GXP_TCT0190 in repro).

### 6.2 Duplicate events in CFX → PK collision on save
**Signature:** CFX with hundreds of events fails via service and manually; "duplicate events" error; `_fc_db_error` log generated; expected behavior is dedupe-and-ignore.
**Status:** ADO 1565807 "Fail to import CFX files (R1060* PORT)" — **Closed** (fix in the 10.6.0.x stream, INFERRED from R1060 port branch). SF origin 22-00867833 (Delek) referenced in the bug.
**Related expected-behavior:** repeating alarm records in hourly CFX caused failures until the customer's SCADA team fixed the exporter (SF 26-01100523, 25-01025593 — file-side fix, not FLOWCAL).

### 6.3 Liquids meter CFX fails from ~21st of month — FC_EDIT_REASON explosion
**Signature:** multiple **liquid** meters; File Import Service fails the meter's CFX starting ~day 20–24 and recovers at new contract month; manual import works only as backfill; error "Unable to save meter <m> due to excessive number of data records encountered (65000+)"; on 10.8 the import fails even after cleanup.
**Root cause (engineering analysis in ADO):** each import re-applies source analysis and writes `FC_EDIT_REASON` rows (`'Source Mapping: Analysis Edit'`, `'Meter Data Edit: Source Analysis Apply'`, `'Source Import/Edit: Analysis Apply'`) per record until the record cap is hit; `Settings Manager > System > System Factors > Liquid Rounding = No` masks it (import succeeds). Interim relief: delete the excessive edit reasons (SQL in §15) and/or check product-code alias — if the CFX Product Code (e.g. `NGL`) doesn't match the Product Editor code, add an alias and restart import services.
**Status:** ADO 1839777 (DEV, Ready for Test) / 1839778 (R1090 PORT, Acceptance) / 1802447 (R1080* PORT, Ready for Test, Escalated) — **not yet closed** as of 2026-09-02; treat as open defect, offer cleanup workaround.
**Anchors:** ADO 1839777/1839778/1802447 (SF 26-01082401, EQT, meter 42500XL in repro).

---

## 7. Cluster — CFX "succeeds" but data missing, misrouted, or meters locked

### 7.1 Duplicate `DEFAULT_IMPORT_FILE` routing conflict
**Signature:** CFX imported + archived, no failure — but the intended meter never updates.
**Root cause (CONFIRMED, SQL-verified):** two meters configured with the same import file name in `FC_METER` (`3019003API` and `3019044XCM` both mapped to `3019001API.CFX` in system NG3) — `fcsrvfileimport` consumes the file for one meter and archives it. Remove the duplicate assignment (find via §15 SQL). Note: multi-meter-per-CFX capability "currently not working as expected" (support statement).
**Anchors:** SF 26-01099018 (query verbatim in §15).

### 7.2 Bad data in user-defined fields breaks specific meters
**Signature:** import failures / postponed records limited to specific meters; junk visible in Meter Characteristics or Volume Editor user-defined fields.
**Fix recipe:** SQL-NULL the affected user-defined columns, requeue Postponed records (select record → Queue). One meter needed the 10.8.0.8 patch on top of cleanup.
**Anchors:** SF 26-01107790 (Chevron FC_CUSU, 10.8.0.6 — "ran SQL to fix bad data in the User-Defined field in the Meter Characteristics table"), 26-01113739 (TGNR — invalid Volume Editor user-defined data from a previous import; NULLed + requeue). Related empty-row variant: SF 26-01101326 (Harvest — SQL cleared "empty" records in `FC_METER_ANALYSIS_ALT` that blocked all CFX+text imports; recurring due to cross-version DataBoss loads 10.8.0.x → 10.5.0.14).

### 7.3 Ignore Configuration Snapshots = Yes
**Signature:** CFX imports fine but meter configurations/characteristics in the file never apply.
**Fix:** Service Configuration → set **Ignore Configuration Snapshots = N**, purge the latest records, re-import the CFX.
**Anchor:** SF 25-01052536.

### 7.4 Benign lock-contention warning (10.6.0.15+)
"Meter locked already for processing" warnings between import services are an intentional 10.6.0.15 improvement — informational unless data stops. **Anchor:** SF 26-01112718 (support statement; Expected Behavior).

### 7.5 Locked meters + "abnormal program termination" (≤10.6.0.13)
**Signature:** meters stuck locked; imports for them error "abnormal program termination"; QCloud PRD.
**Fix:** restart FC services to release locks (workaround); fixed in **10.6.0.14** and 10.8 (INFERRED).
**Anchor:** SF 25-01016994 (8 locked meters, QCloud PRD).

---

## 8. Cluster — Control files (`.ctl_F_*`) orphaned / retry exhaustion

**Signature:** `.ctl_F_<timestamp>` files pile up in the import folder; `FcSrvFileImport Error - Control Exceeds Retry Count`; sometimes paired with the §4.2 race.
**Root cause:** control-file handling defect in the 10.5 stream. Fixed in **10.5.0.13** and **10.6.0.2** (INFERRED, stated on two separate cases).
**Anchors:** SF 25-01050256 (COP — "known issue with control files in 10.5… resolved in 10.6.0.2"), 25-01010682 ("CTL_F files are control files… resolved in 10.6.0.2"), 23-00921045 ("resolved in 10.5.0.13 and 10.6.0.2"), 24-00953001 (Control Exceeds Retry Count). Related: ADO 1627121 "Temp CFX Files Generated by FlowCal App" (`_~FC_*_FCSRVFILEIMPORT_*.Cfx` temp files, New).

---

## 9. Cluster — GQ source text file imports

### 9.1 GQ text files not processing (folder targeting)
**Signature:** CFX flows, GQ source text files sit untouched.
**Fix recipe (CONFIRMED):** point Service Configuration import path at the parent (`T:\FLOWCAL\Import`), then in `FcDebugOptions.cfg` give each File Import Service its own subfolder — #1 `\CFX`, #2 `\GQSourceTextFiles`, #3 `\MeterTextFiles` — restart services. Standard folder name for GQ drops: `GQSourceTextFiles` (also SF 24-00954835: `F:\FTProot\Imports\GQSourceTextFiles`).
**Anchors:** SF 26-01123435 (TAG), 24-00954835, 24-00982727 (network-drive setup; also documents `SC_*` source-code columns: E=edited, C=calculated, null/I=imported in `fc_meter_analysis`).

### 9.2 GQ import inconsistency on auto-created sources — deferred defect ADO 1598743
**Signature:** intermittent wrong/missing GQ application, typically sources that were auto-created; import file rows missing the "from" date.
**Status:** known 10.3-era bug, **deferred** (workaround exists) — ADO 1598743 (verbatim URL cited in case resolution). **Workarounds:** purge the source and re-import; always populate full timestamps in BOTH from and to date columns of the GQ text file.
**Anchor:** SF 25-01052041.

### 9.3 Extended-analysis DB error + Duration Fix utility
**Signature:** dozens of GQ source text imports fail on a `gest/GQ source extended analysis` DB error; running the **Duration Fix** utility reports hundreds of duration errors.
**Status:** SF 24-00987652 closed "deprioritized" (Software Defect) — no fix version; recipe is: run Duration Fix, correct source naming, re-import (SF 23-00924825: "fix back to the original GQ source name, run duration fix tool, re-import the text gq source"). Older validation-exception variant fixed in 10.0.3.15 (SF 22-00603897, INFERRED).

### 9.4 `ORA-02291` parent key not found (`FC_METANL_F_LAB_ANALYSIS_ID`)
**Signature:** CFX/GQ import throws integrity-constraint error referencing `FCOWNER.FC_METANL_F_LAB_ANALYSIS_ID`.
**Root cause:** the same source was transmitted multiple times within the month, corrupting the lab-analysis linkage. **Fix:** purge that month's sources for the meter and reload a single source (client alternative that also worked: create a new GQ source for the meter).
**Anchor:** SF 25-01060909.

### 9.5 GQ validation limits crash the import service
**Signature:** import service dies processing GQ files for specific sources; GQ Frozen Value / Expert Systems validation "Window count" set far above the coded max (e.g. 339; max is 24).
**Fix:** set Window count within 1–24 on the affected sources.
**Anchor:** SF 22-00608815 (Blackhills/Tallgrass, 7.4.15.2-era but the config trap is version-independent).

---

## 10. Cluster — Ticket & meter text file imports (liquids)

### 10.1 `FLOWCAL Message 321: Ticket import failure`
Message 321 is the ticket-import failure notification (arrives by email to the configured contact list). Triage the failed ticket file itself; also check the notification contact list — one case was purely a stale internal address on the UAT contact list (redacted; employee email removed per PII policy).
**Anchor:** SF 26-01120450.

### 10.2 Ticket import defects (fixed, version-check first)
- Tank Gauge ticket **revision** imports fail to recalculate — fixed **10.2.0.8 / 10.3.0.0** (SF 22-00709957; recurrence 22-00831033 resolved with a delivered update). INFERRED.
- Manual liquid text-file import from **Dashboard** hangs indefinitely — fixed **10.2.0.16** (SF 22-00821011). INFERRED.
- Liquid Source Analysis text import issues — SF 24-00973255 (App Config; format/setup class).
- Custom LQTICKET condensate drivers are custom-services work, not core product (SF 22-00609531, 22-00567013 — "Not in Product Plan"; upgrade collision case 22-00609475 `raimport.lqt`, legacy defect id FC-1945461).

### 10.3 Meter text file import failures (gas/liquid TXT)
- TXT with create-revisions → `ORA-00001: unique constraint (FCOWNER.FC_METPER_PK) violated`, `** Text File Import - Failed to process meter: <id>` in `_FC_FILE_IMPORT.LOG`. Reproduced on **10.3.0.24 and 10.6.0.7**; ADO 1766053 (Bug, **New**) — open; workaround is avoiding duplicate-period revisions in the file. 
- 10.8.0.5 text import exception `rc = FcSrvGasMeterTextFileImport(...)` crash in `FcSrvFileImport4.exe` — fixed **10.8.0.7** (SF 26-01081133 — full stack trace in case; INFERRED).
- "Program encountered a problem while processing a Meter Text File" (10.6.0.11 / 10.8.0.5, `MeterTextFilesByImportId`) — ADO 1815151 (Bug, New).
- Text File Import setting: with per-import-ID files use Service Configuration **Text File Import = "Neither"** instead of "Use Field as Import ID" → files route via `MeterTextFilesByImportId` folder (SF 22-00599854, Noble).
- Header/format plumbing: tab-delimited conversions can be scripted (PowerShell recipe on SF 26-01118262); Liquid Meter Text File Format doc available under NDA (SF 26-01120653, 26-01114458, 26-01117697).

---

## 11. Cluster — TIDX / PIDX (TESTit & PROVEit data exchange)

### 11.1 TIDX import unprotects meters on the server (defect)
**Signature:** meters on the TESTit **server** lose lock protection after a laptop TIDX is imported; third-party data-exchange variant also unlocks meters.
**Fix:** TESTit **3.16.2 / 3.17.1** (INFERRED from case resolution). Third-party exchange variant acknowledged by DEV with no workaround, needs release (SF 24-00989468, TESTit 3.14).
**Anchors:** SF 25-00998992, 24-00989468. Recovery pattern for already-unprotected meters: export a server TIDX listing affected meters → import on desktop → verify lock icons → export desktop TIDX → import back on server (SF 26-01107901 workaround narrative).

### 11.2 `fa_user_activity_log` bloat blocks TIDX import
**Signature:** TIDX import fails "while importing notes", or the desktop app hangs/crawls on import.
**Fix (CONFIRMED, applied on 2 cases):** `truncate table fcowner.fa_user_activity_log;` then disable user-activity logging to prevent recurrence. (One user additionally needed reset-all-settings/reset-layout.)
**Anchors:** SF 25-01046321, 25-01011867.

### 11.3 Duplicate/unmergeable devices in TIDX
**Signature:** `Error occurred in Import: Sequence contains more than one matching element`, or "The import process failed in attempting to merge two unique meters together in the existing database"; app fails to name the conflicting device.
**Status:** ADO 1741593 (Bug, **Active**; TESTit 3.11, CFL) — SF 25-01028855. Field-observed fix: find and remove the duplicate meter (each meter needs a unique ID) then re-import (SF 25-01019617). Nuclear option when the local DB is wedged: recreate the desktop DB — stop services, delete MDF/LDF, run `create strongDB` from `C:\Quorum Software\Field Apps\Resources\Database`, re-import (SF 25-00999348); or Password Utility DB recreate (SF 25-01016236); PROVEit equivalent `DBSetup.bat` in `<install dir>\Resources\Database` after a PIDX full export (SF 24-00993192).

### 11.4 Version compatibility & 3.19 import failures
- TIDX is **not** portable across minor versions: 3.16 exports would not import into 3.17; support uninstalled 3.17 and installed 3.16 to migrate (SF 25-01045322).
- TESTit Server **3.19.0.0**: TIDX from 3.16 domain fails manually and via import service; "because of the failures during import, nothing in the file gets imported" (dev comment) — ADO 1862622 (Bug, **New**, ETE, SF 26-01112292 in title). PII note: submitter contact details in the ADO description redacted here.
- TIDX content is selection-driven: Application Options must include Report Options / Task Options at export time or logos and Transmitter Setup won't transfer (SF 26-01103421 — Expected Behavior).

### 11.5 PIDX foreign-device skip (PROVEit x.19)
"import meter data in pidx failed" log lines that name a skipped meter/prover are **informational**: x.19 added Data Exchange option **Create New Devices on Import**; when set to `No`, devices foreign to the server are ignored on import. Set to Yes if the devices should be created.
**Anchor:** SF 26-01109412.

### 11.6 Local DB capacity / memory
- TESTit desktop DB hit max capacity (SQL Express-class limit) → provision fresh DB and import the TIDX backup (SF 26-01119979).
- `System.OutOfMemoryException` on TIDX import — not reproduced with same DB+files; retry after reboot before deep-diving (SF 24-00994375).
- ORA-12571 during server TIDX import = network drop; requeue the errored files (SF 25-01028215).

### 11.7 TIDX-adjacent sync defects (route to Integrations skill, cite from here)
Test report revisions entered in TESTit not importing into FLOWCAL — 10.8.0.9 + TESTit 3.18.1.0, ADO 1862781 (DEV, Analyze) / 1848873 (R1080* PORT) / 1862782 (R1090 PORT), SF 26-01113308 (MarkWest). TESTit reports causing duplicate PPAs in FLOWCAL (`FcSrvTESTitCalAdjApply.exe`) — ADO 1849247 (New) + logging build 1854030 (Closed; `[MONITORING] log_performance=Y`), 10.6.0.13 + 3.16.1. TESTit exceptions not generating — ADO 1865837 (New, SF 26-01117784, Salt Creek).

---

## 12. Cluster — Import drivers (custom DLLs)

### 12.1 Custom driver doesn't rename/archive → import loop
**Signature:** files import once, then the service loops "NO NEW HISTORY FOUND" forever; files never renamed/archived; ignores FcDebugOptions archive parameters. Trigger includes Service Configuration "Number of Installations" > 1.
**Status:** ADO 1435804 (PORT Dev, Closed; tags `10.4.0.0`, `Target Version 8.11.37.22`) / 1435805 (PORT R1030, Closed) — Kern River `KRAOU.dll`. SF 22-00606399: "resolved in 8.11.37.32" (INFERRED; ADO tags say 8.11.37.22 target — treat exact dot-patch as INFERRED, verify in release notes).

### 12.2 Drivers after upgrades
Custom import drivers are compiled against a FLOWCAL version; after upgrade they must be re-delivered: NiMerc rebuilt for 10.6.0.6 (SF 25-01022404, NiSource), new `Fisher.dll` restored AGA-file imports (SF 22-00605474). Requests for brand-new format drivers (PGAS XLM, DCPLIQ01, LQTICKET condensate) are custom-services scope — "Not in Product Plan" (SF 22-00635353, 22-00567013, 22-00609531). Wrong-driver selection is a common user error (SF 22-00568999).

---

## 13. Cluster — Transport & permissions plumbing (files never arrive / service can't work the folders)

| Failure | Fix | Anchor |
|---|---|---|
| `Error getting name of current remote directory` — CFX not arriving | Refresh SFTP credentials | SF 26-01064375 (+ cloud ADO 1774900) |
| SFTP site unreachable from server | Cloud tickets + RCA | SF 25-01047250 (ADO 1758976, 1766949) |
| FTP import folder access lost | Password reset re-applied folder permissions | SF 25-01046902 |
| Local automated CFX pull broken on new laptop | `.bat` referenced WinSCP — install WinSCP | SF 26-01110322 |
| UAT text imports failing wholesale | Services running under wrong service account; fix account + FTProot Import folder ACLs + FCSRV app account privileges | SF 26-01122122 |
| "processed" folders never created | `FCSRVFILEIMPORT`/`FCSRVFILEIMPORT2` service account lacks privileges — fix in AD | SF 24-00986595 |
| Service silently does nothing, no errors | FCSRV account had a temporary password — set permanent, restart | SF 23-00916789 |
| "Unable to save to the registry" editing Service Configuration; service won't start | Run FLOWCAL as administrator to edit; use full UNC path (`\\server\share\...`) not mapped shortcut | SF 22-00685271 |
| FcDebugOptions misconfig (stray `.exe`, missing `\` in path) | Correct cfg entries | SF 24-00986955 |
| Huge `_FC_FILE_LIST_*.LOG` | Uncheck "Log Processed Files"; stop service to delete log | SF 22-00594877 |

---

## 14. Known ADO items (org `QuorumSoftware`)

| ADO | Title (abbrev.) | State (2026-09-02) | Fixed-in | SF origin |
|---|---|---|---|---|
| 1790015 / 1789257 / 1805980 | Meter import fails due to string buffer overflow (DEV / R1080* / R1090) | Closed | 10.8.0.7, 10.9.0.1 (INFERRED, tags) | 26-01087353 |
| 1805452 / 1814628 / 1800154 | Files are not importing — DST PK violation | Closed | 10.8.0.9 (INFERRED, tag) | 25-01008137 |
| 1839777 / 1802447 / 1839778 | Liquids Meter CFX File Import Service Issue (edit-reason explosion) | Ready for Test / Acceptance | open | 26-01082401 |
| 1565807 | Fail to import CFX files — duplicate events (R1060* PORT) | Closed | 10.6.x (INFERRED) | 22-00867833 |
| 1710336 | FLOWCAL Import Service Failure — 0xc0000092 CC32C250MT.DLL | New | — | 24-00992056 |
| 1864320 | Import services throwing errors / missing data (multi-instance) | New (Escalated) | — | 2026-08 |
| 1865409 | MBS files not processed correctly (import loop) | New | — | — |
| 1815151 | File Import Issue processing a Meter Text File | New | — | — |
| 1766053 | ORA-00001 FC_METPER_PK — TXT import w/ revisions | New | — | — |
| 1658113 | System Messages 122/123 not generated (unmapped_file_action) | New | — | — |
| 1627121 | Temp CFX files generated by FlowCal app | New | — | — |
| 1813756 | [PERF] File import service slow to stop in 10.9.0 | Closed | 10.9.x | — |
| 1435804 / 1435805 | KRAOU.dll custom driver not renaming/archiving | Closed | 8.11.37.22 target / 10.4.0.0 (INFERRED) | 22-00606399 |
| 1598743 | GQ import inconsistency (auto-created sources, missing from-date) | Deferred | workaround only | 25-01052041 |
| 1809471 | Meter stopped updating; CFX processed not failing (service-only) | New | — | 26-01090833 |
| 1862622 | TESTit 3.19 server — TIDX imports not working | New | — | 26-01112292 |
| 1741593 | TESTit failed to import two unique meters (TIDX merge) | Active | — | 25-01028855 |
| 1862781 / 1848873 / 1862782 | Test report revisions not importing into FLOWCAL | Analyze / New | — | 26-01113308 |
| 1849247 / 1854030 | TESTit reports causing duplicate PPAs | New / Closed (logging) | — | — |
| 1865837 | TESTit exceptions not generating | New | — | 26-01117784 |
| 1774900, 1758976, 1766949, 1734447, 1735969, 1736212, 1606978 | Cloud/ops tickets (SFTP, service restarts, restart button) | ops | n/a | see §4.1/§13 |

---

## 15. Diagnostic SQL

Environment assumption: FLOWCAL Oracle schema `FCOWNER` (SQL Server syntax differs only in date handling). Run read-only first; label results INFERRED until re-checked against the client's build.

**Duplicate DEFAULT_IMPORT_FILE routing conflict (verbatim from SF 26-01099018):**
```sql
SELECT s.SYSTEM_NAME, m.meter_number, m.import_path, m.default_import_file
FROM fc_meter m
JOIN fc_system s ON s.SYSTEM_INDEX = m.SYSTEM_INDEX
WHERE m.DEFAULT_IMPORT_FILE = '<file>.CFX';
-- generalized dup-finder:
SELECT default_import_file, COUNT(*) FROM fc_meter
WHERE default_import_file IS NOT NULL
GROUP BY default_import_file HAVING COUNT(*) > 1;
```

**Edit-reason explosion check for a failing liquids meter (from ADO 1839777 repro, Oracle):**
```sql
ALTER SESSION SET nls_date_format = 'mm/dd/yyyy hh24:mi:ss';
SELECT * FROM fc_edit_reason
WHERE meter_number_index = (SELECT meter_number_index FROM fc_meter WHERE meter_number = '<METER>')
  AND gms_date > SYSDATE - 0.1;
```
Cleanup pattern used by engineering (adapt dates/meter; take a backup; from ADO 1839777):
```sql
DELETE FROM fc_edit_reason
WHERE meter_number_index = (SELECT meter_number_index FROM fc_meter WHERE meter_number = '<METER>')
  AND effective_date >= '<contract month start>' AND sequence_number > 20
  AND reason IN ('Source Mapping: Analysis Edit',
                 'Meter Data Edit: Source Analysis Apply',
                 'Source Import/Edit: Analysis Apply');
COMMIT;
```

**TESTit/PROVEit desktop import hang / notes failure (verbatim from SF 25-01046321 / 25-01011867):**
```sql
TRUNCATE TABLE fcowner.fa_user_activity_log;
-- then disable user-activity logging in the app to prevent recurrence
```

**Source-of-value audit on imported analyses (from SF 24-00982727):** most `fc_meter_analysis` value columns have a paired `SC_*` column — `E` = edited, `C` = calculated, `NULL`/`I` = imported. Use to prove whether a wrong value came from the file or a later edit.

---

## 16. Expected-Behavior FAQ

- **"Meter locked already for processing" warnings (10.6.0.15+)** — intentional inter-service coordination message; ignore unless imports actually stop (SF 26-01112718).
- **PIDX log says a meter/prover was skipped (PROVEit x.19)** — informational when Data Exchange "Create New Devices on Import" = No (SF 26-01109412).
- **TIDX didn't carry report logo / Transmitter Setup** — exporter must tick Report Options / Task Options under Application Options at export time (SF 26-01103421).
- **TIDX export "missing meters"** — export scope is selection/list-driven; verified working as designed (SF 26-01080122). No query-list-by-tech exists; use a static list (SF 25-01003921).
- **`_FC_FILE_LIST_*.LOG` grows huge** — by design when "Log Processed Files" is on (SF 22-00594877).
- **CFX file format** — spec document is provided under NDA on request (SF 26-01123847, 26-01122584 ACM/Autosol); same for Liquid Meter Text (SF 26-01120653) and Source Analysis Text formats (SF 26-01114458). API 11.4.1 (2018) product type Water = pure water only; no industry standard for produced water (SF 26-01106494).
- **15-minute data resolution "wrong"** — meters were bulk-changed to a 15-min import resolution; configuration, not defect (SF 26-01115048).
- **FcSrvFileImport File Rename tool** — removed from the product long ago; use a Windows batch job (SF 22-00554869).

---

## 17. Escalation guidance

1. **Restart + collect first.** Before any escalation attach: `_FC_FILE_IMPORT.LOG`, `_FC_FILE_LIST_FcSrvFileImport*.LOG`, `_fc_db_error*`, Windows Event Viewer application entries, the failing file itself (from `zFailedFilesArchive`), and exact build (`Release x.y.z.w` line from the log).
2. **Match a version signature (§5, §6, §8) before writing a new bug** — most import failures 2025-2026 map to the 10.8 StringCopy family, the DST PK fix (10.8.0.9), the 10.5 control-file/race defects, or the ≤10.3 memory leak. "Fixed in" claims here are INFERRED — verify against release notes before promising a patch level.
3. **Open defects to link, not duplicate:** liquids edit-reason explosion (ADO 1839777/1802447/1839778), multi-instance race follow-up (1864320), CC32C250MT crash (1710336), FC_METPER_PK TXT revisions (1766053), MBS loop (1865409), meter text file (1815151), TESTit 3.19 TIDX (1862622), TIDX device merge (1741593).
4. **New engineering bug:** file to area path `Quorum\North America\Measurement` (FLOWCAL) or `…\Field Apps and API` (TESTit/PROVEit); include SF case number in the description (`Case Owner - {name}` + `2x-00xxxxxx` convention), repro FcDataBoss + import file on `\\qddfcfs01.qdev.net\DATA\CustomerData\<client>\<case>`, and expected-vs-actual per the repro-steps style in ADO 1790015.
5. **Custom drivers** (KRAOU/NiMerc/Fisher/LQTICKET class) route to the custom-services team, not core Measurement engineering (§12).
6. **QCloud clients:** service restarts and SFTP/FTP fixes go through cloud ops tickets (see §4.1/§13 ADO ids for precedent).

---
*Sources: Salesforce closed-case history (FLOWCAL/TESTit/PROVEit, mined 2026-09-02) and ADO org QuorumSoftware work items; every root-cause claim above cites its SF case and/or ADO id. PII (names/emails/phones) redacted; client codes retained.*
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
