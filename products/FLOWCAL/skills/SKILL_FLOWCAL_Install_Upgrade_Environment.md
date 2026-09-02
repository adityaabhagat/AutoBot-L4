# SKILL: FLOWCAL Family — Installation, Upgrade, Environment & Deployment Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-09-02 | **Products:** `FLOWCAL`, `TESTit`, `PROVEit` (Product_list__c literals)
**Scope:** Everything between "we want to move to version X / new hardware" and "the upgraded environment works": **FLOWCAL 10.x database upgrade scripts** (fc-migration `__updateDB_*.sql` failures, DBColCheck), **post-upgrade app breakage** (DLL mismatch, rollup buffer errors, UDF bad data, splash-screen hangs), **the FLOWCAL upgrade runbook**, **TESTit/PROVEit desktop & server installers** (bundled SQL Server Express failures, VC++ prerequisites), **field-app launch errors after install/upgrade/Windows update** (Layouts corruption, `fieldapplications.dat`, SQL service logon), **FLOWCAL↔TESTit integration redeployment** (NServiceBusSetup, MSMQ, Contracts DLLs, `NSBOWNER.SUBSCRIPTION`), **server/infrastructure migrations** (new app server, AIX→Linux, Oracle 19c cutover, multi-server Citrix `mklink`), and **downgrades**.
**Use when:** case mentions "upgrade", "installer", "installation failed", "upgrade script", `DBColCheck`, "SQL Express", "new server", "migration", "new environment", "UAT refresh" (upgrade context), `FlowcalCompatibilityUpdate`, `NServiceBusSetup`, "version mismatch", "after the upgrade", "downgrade", or FLOWCAL 10.x / TESTit 3.x / PROVEit 9.x version pairs.
**Companion skills:** site keys & license transfer mechanics → Licensing/CrypKey skill (group #5). OKTA/Citrix/Instant-Login access after refresh → SKILL_FLOWCAL_Security_Access (group #9). Service stuck/queue drain problems not tied to an upgrade → Services/Rollups/TQ skill (group #3). QCloud-hosted outages/FTP → FLOWCloud skill (group #10).

> **Evidence base (mined 2026-09-02):** ~115 closed family cases surveyed across 6 SOQL clusters (Installation/Upgrade + Environment categories filtered to Software Defect/Application Configuration, upgrade+error subjects, SQL-install subjects, migration/new-server subjects, refresh/environment subjects); 40 cases pulled in full (Description + Resolution). 23 ADO work items verified live across `Quorum`, `QuorumSoftware`, `QuorumServices`, and `myQuorum Cloud` projects. Coverage plan sizes this group at ~7,005 family cases, ~420 actionable (FLOWCAL 92 + TESTit 108 + PROVEit 57 in the two core categories alone — the TESTit/PROVEit installer clusters are the single biggest actionable block for those literals). Every root-cause claim cites an SF case number and/or ADO id. Fixed-in versions are **INFERRED** from SF/ADO text unless marked release-notes-confirmed.
>
> **Data-quality caveat:** a large share of this category's raw volume is routine fulfillment — "upload installer X to our FTP folder", scheduled upgrade assistance, site-key-with-install requests (e.g. 25-01019921, 25-01043668, 25-01048461, 26-01068663, 25-01008047). The defect signal concentrates in §3 (upgrade-script bugs — real, recurring, ADO-confirmed), §6 (installer/SQL Express — the dominant TESTit/PROVEit actionable family), and §8 (integration redeploy misses). Auto-Bot by Aditya Bhagat.

---

## 1. Quick Triage Table

| Symptom | Likely cause | § | First action |
|---|---|---|---|
| After 10.7 upgrade: "Unable to access the export dll export\FCTextFileExchange.dll", upgrade UPDATEs hit **0 rows** | 10.6.0.17→10.7 script missed rows on case-sensitive Oracle (FCTextFileExchange→GasTextFileExchange rename) | §3 | Run the UPPER()-matched fix SQL on `fc_report_group/schedule/list` (26-01101971, ADO 1814982/1819174) |
| 10.8→10.9 upgrade script fails mid-run / partial commit state | Known script defect: stray COMMITs + misplaced ALTERs | §3 | ADO 1779716; get corrected script before re-running |
| Upgrade script runs 14+ hours, never completes | Giant `FC_FFLCN_HOURLY` (hourly location data) — 2TB+ table being altered | §3 | DBA windowing/purge before upgrade; 23-00923294 |
| DBColCheck flags `fc_exception_description` count on a clean 10.9 DB | DbColCheck tool bug (tableinfo.h expected 3253 vs actual 3259) | §5 | False positive; ADO 1805447 |
| Post-upgrade: FLOWCAL.DLL errors, meter edits fail, crashes on import | Stale FLOWCAL.DLL on app server and/or CR/LF garbage in `fc_meter_characteristic` user fields | §4 | Swap FLOWCAL.DLL; run UDF-cleanup SQL (26-01103168, ADO 1854903) |
| Post-upgrade (10.8.0.4–.7): location rollups postpone queues, log "Destination buffer too small! Will truncate" | 10.8 StringCopy/charset defect triggered by upgrade | §4 | Upgrade to 10.8.0.9+ (INFERRED) + fix script (ADO 1811928/1819169/1819170) |
| FLOWCAL stuck on splash screen after 10.8 upgrade (never reaches login) | Client's custom `ThirdPartyTicketID.dll` incompatible with new build | §4 | Deploy rebuilt DLL for the new version (25-01045709) |
| FLOWCAL installer: "MS Visual C++ Runtime for Visual Studio 2022 v.17 (x86) could not be installed" | Prereq install blocked (needs admin / already-newer runtime) | §5 | Install VC++ runtime manually, rerun installer (26-01084386) |
| TESTit/PROVEit desktop install: "SQL Server could not be installed" / bundled SQL Express fails | Installer provisions logged-in Windows account as SQL sysadmin — fails for domain-only accounts, no-admin users | §6 | Manual SQL Server install + `PasswordUtilityUI.exe` DB create (25-01012469, 25-01024261, ADO 1612199) |
| SQL 2022 install on Win11 fails: "Wait on the Database Engine recovery handle failed" / Error 1067 / "Unable to create stack dump file due to stack shortage" | NVMe 4K-native sector size vs SQL Server | §6 | `ForcedPhysicalSectorSizeInBytes` registry workaround (26-01100072) |
| Installer says "existing database detected" on a machine with a fresh empty FCFIELDAPPS instance | Installer equates running MSSQL instance with existing DB | §6 | Answer per actual state; ADO 1591870 |
| TESTit/PROVEit crashes at launch: "Root Element is missing" or XtraSerializer "elements are not closed" | Corrupted layout XML in the user's AppData Layouts folder | §7 | Delete `%LOCALAPPDATA%\Flow-Cal, Inc\<TESTIT|TESTit3>\Layouts` (25-01002929, 25-01060576) |
| TESTit "unknown error" at launch after a Windows update; reinstall does NOT fix | Corrupt `fieldapplications.dat` in ProgramData | §7 | Delete `C:\ProgramData\Flow-Cal, Inc\Field Apps\fieldapplications.dat` (25-01052975) |
| Can't log in; SQL service won't start, "Error 1069: logon failure" | SQL service Log On credentials stale (AD password change) | §7 | Re-enter service Log On account/password (25-01003408) |
| TESTit Server upgrade done, site key entered, then "An application error occurred" | `NSBOWNER` Oracle account locked | §8 | Unlock NSBOWNER, retry; reinstall if a second error follows (25-01004236) |
| After FLOWCAL/TESTit upgrade, sync dead; `nsbowner.subscription` shows OLD versions | Contracts DLL not upgraded on one side | §8 | Verify both Contracts DLL versions, re-run integration upgrade, truncate NSBOWNER subscription tables, restart services (25-01001859, 26-01109179) |
| TESTit 3.19 server upgrade: sync stops entirely | MSMQ (Message Queuing) not installed on every server | §8 | Install MSMQ on all servers + SQL Server AV/component exclusions (26-01110812) |
| `FlowcalCompatibilityUpdate.ps1` errors during TI integration setup on 10.9.0.1 | Known script issue — safe to skip when nothing changed | §8 | Use matching `NServiceBusSetup-1.19.1.0`; skip the step (26-01117483) |
| New/second FLOWCAL app or Citrix server: TESTit throws "type initializer for ...CAuthorization threw an exception" | Each server has its own `Field Apps` ProgramData folder; auth file not shared | §9 | `mklink /d "C:\ProgramData\Flow-Cal, Inc\Field Apps" \\<share>\Field Apps` on every server (23-00905031) |
| DB platform migration (e.g. AIX→Linux): missing data, dead sequences, slow queries | Sequences/statistics/rollup state not migrated cleanly | §9 | Recopy sequences, gather stats, clear rollup tables (25-01060388) |
| Post-Oracle-19c-cutover: flow averages hit the OLD database, queues stuck | Automated job auto-restarting against old DB + config path garbage + DLL mismatch | §9 | 26-01109179 recipe (see §8/§9) |
| Customer wants to downgrade PROVEit/TESTit | Not officially supported; data must round-trip via PIDX/TIDX export | §10 | Follow the downgrade recipe (25-01008909, 25-01032948) |

---

## 2. Decision Tree

```
"Install / upgrade / environment problem"
│
├─ Is it a REQUEST (installer download, scripts, schedule an upgrade, refresh UAT)?
│   └─ Yes → fulfillment, not investigation. FLOWCAL: installers + upgrade scripts land in the
│       client FTP folder (RW & RO exes, FcIntegratedServices-<ver>.exe, per-patch scripts —
│       25-01019921). QCloud-hosted: route as "FlowCal Upgrade Assistance Request"
│       (QuorumServices) / "Upgrade Environment" (myQuorum Cloud). → §5 runbook.
│
├─ Failure DURING the upgrade itself?
│   ├─ DB upgrade script errors / 0-rows / hangs ......................... §3
│   ├─ DBColCheck discrepancies after scripts ............................ §5
│   └─ App installer prereq errors (VC++, disk, admin rights) ............ §5 / §6
│
├─ Worked BEFORE the upgrade, broken AFTER?
│   ├─ FLOWCAL app/DLL errors, rollups postponed, imports crash .......... §4
│   ├─ Login/launch broken (site key OK) — TESTit/PROVEit ................ §7 / §8
│   ├─ FLOWCAL↔TESTit sync dead .......................................... §8
│   └─ Login broken after DB refresh+upgrade (QCloud) → refresh+rerun
│       upgrade (26-01122205); Instant-Login/vault side → Security skill.
│
├─ Fresh INSTALL failing (field tech laptop/desktop)?
│   ├─ Bundled SQL Express fails ......................................... §6
│   ├─ Launch crash right after install .................................. §7
│   └─ License/site-key transfer to new computer → Licensing skill
│       (install half of it: 25-01024261, 25-01052208, 25-01016459).
│
├─ NEW SERVER / migration / platform change?
│   ├─ Multi-server TESTit (Citrix, second app server) ................... §9
│   ├─ DB host/platform migration, environment copy/refresh .............. §9
│   └─ Oracle/SQL Server version upgrade under FLOWCAL ................... §9
│
└─ Wants an OLDER version back .......................................... §10
```

---

## 3. FLOWCAL 10.x database upgrade-script failures

**Signature:** errors or silent no-ops while running the incremental `__updateDB_<from>_to_<to>.sql` scripts; app errors afterward that trace to schema/config rows the script should have changed. Scripts live in the `fc-migration` repo: `fc-migration\FLOWCAL Incremental\FLOWCAL 10\<release>\__updateDB_x_to_y.sql` (ADO 1814982; detail files like `FLOWCAL Incremental/FLOWCAL 10/10.9/details/__updateDB_10.9.0.0.1_to_10.9.0.0.2.sql` per ADO 1819169).

### 3.1 10.7 rename misses rows on case-sensitive Oracle → export DLL errors — CONFIRMED defect
- **Root cause:** the 10.6.0.17→10.7.0.0 script renames the `FCTextFileExchange` export to `GasTextFileExchange` with literal-case WHERE clauses; on Oracle (case-sensitive) clients whose rows differ in case, the UPDATEs hit **0 rows**. App then throws "Unable to access the export dll export\FCTextFileExchange.dll" (SF 26-01101971, Application Configuration).
- **Fix recipe (from 26-01101971 resolution — adjust literals to the client's actual case; the SET value must match their data exactly or you get 0 rows again):**
```sql
ALTER TABLE fc_report_schedule DISABLE CONSTRAINT fc_rptsch_f_group_name;
UPDATE fc_report_group    SET group_name      = 'GasTextFileExchange'        WHERE UPPER(group_name)      = 'FCTEXTFILEEXCHANGE';
UPDATE fc_report_schedule SET group_name      = 'GasTextFileExchange'        WHERE UPPER(group_name)      = 'FCTEXTFILEEXCHANGE';
UPDATE fc_report_list     SET report_name     = 'GasTextFileExchange'        WHERE UPPER(report_name)     = 'FCTEXTFILEEXCHANGE';
UPDATE fc_report_list     SET report_location = 'Export\GasTextFileExchange.dll' WHERE UPPER(report_location) = 'EXPORT\FCTEXTFILEEXCHANGE.DLL';
COMMIT;
ALTER TABLE fc_report_schedule ENABLE CONSTRAINT fc_rptsch_f_group_name;
```
  Check all four table/column pairs; a client may already have some fixed (26-01101971 excluded `fc_report_schedule`).
- **Product fix:** ADO 1814982 "10.7 Upgrade script change" adds `UPPER()` to those statements in the script itself; ADO 1819174 "Correct 10.6.0.17 to 10.7.0.0 upgrade script" is the companion engineering-side item. Both Closed — script corrected in later 10.7 packages (INFERRED).

### 3.2 10.8→10.9 script structure defect — CONFIRMED
- ADO 1779716 "Fix 10.8.0 to 10.9 upgrade script" (Closed): stray `COMMIT;` statements at ~10 line positions had to be removed and a block of ALTER TABLE statements moved to the end of the "ALTERS TO DATABASE OBJECTS" section. Symptom pattern: partial-commit state / ALTERs failing on objects not yet ready when clients run the original script. If a client reports 10.8→10.9 script errors, confirm they have the corrected script revision before letting them re-run.

### 3.3 Script hangs on very large tables — environment constraint, not a bug
- SF 23-00923294: upgrade statements against `FC_FFLCN_HOURLY` (hourly location flow data) at 2TB+ ran 14+ hours vs <30 min the prior year. No product fix; this is DBA territory — purge/archive or partition strategy before the upgrade window, and size the window from the largest `FC_FF*_HOURLY` table. Flag any client whose hourly tables are near-TB as an upgrade-planning risk.

### 3.4 Generic "upgrade script error" cases
- 25-01041519 (FlowCal 10.6.0.9 upgrade script error — resolved working the script with support; no reusable detail) and 25-01048763 (10.6.0.6 upgrade — login + DBColCheck fixed on a call) show the routine pattern: script error screenshots + log file attachment → support fixes interactively. Always request the script log and the DBColCheck output first.

---

## 4. Post-upgrade FLOWCAL application breakage

**Signature:** upgrade "succeeded", then the app misbehaves: DLL errors, rollup queues postponed, imports crash, splash screen hangs.

### 4.1 FLOWCAL.DLL errors + edits/imports failing — CONFIRMED (bad data + stale DLL)
- SF 26-01103168 (FC_MRCP upgraded DB): three symptoms at once — stuck import file crashing services, save-edit errors on meters, Settings Manager/Dashboard access errors. Resolution: (a) **swap out FLOWCAL.DLL on the server** ("client was getting FLOWCAL.DLL errors after the upgrade which can happen"), (b) stop File Import Services and delete stuck control files, (c) run the **UDF cleanup SQL** — hidden CR/LF characters in `fc_meter_characteristic.user_field_s01..s30` break meter/location rollups, import, and meter-data viewing. The cleanup nulls any user field containing chr(13)/chr(10) (full 30-column CASE/instr UPDATE in the case resolution; pattern below in §12).
- ADO 1854903 (Meter Import Error, July 2026): same fix — "run the attached script to clear the UDF fields in meter characteristics"; engineering guidance in-thread: "They have to upgrade to 10.8.0.9" / "latest 10.8 or 10.9" (fixed-in **INFERRED**).

### 4.2 "Destination buffer too small! Will truncate" → postponed rollup queues — CONFIRMED defect, 10.8.0.4–10.8.0.7
- Trigger: "Customer upgraded from FLOWCAL 10.5.0.11 to 10.8.0.4 and the issue began occurring immediately during location rollups" (ADO 1811928 description; affected 10.8.0.4/10.8.0.5, duplicated in 10.8.0.7). Repro: Settings Manager > Services > Services Queue → queue All Data for a location → start `FcSrvLcnRollup` service.
- Cause: 10.8 StringCopy/character-set handling ("FLOWCAL does not explicitly set any character set" — ADO 1811928 history). Fix = code change + support SQL script; tags indicate **10.8.0.9** (INFERRED). Ports: ADO 1819169 (R1090 PORT — script change went into `__updateDB_10.9.0.0.1_to_10.9.0.0.2.sql`), ADO 1819170 (DEV — "script isn't needed in 10.10 DEV; will only port to 10.8 and 10.9").
- Note the R#### PORT convention: same defect tracked per release branch as `(DEV)` / `(R1080* PORT)` / `(R1090 PORT)`.

### 4.3 Splash-screen hang after upgrade (client-custom DLL) — CONFIRMED
- SF 25-01045709: FLOWCAL 10.8.0.0 (DEV & MO) stuck on splash screen, never reaches login. Cause: the client-specific **`ThirdPartyTicketID.dll`** needed a rebuild for 10.8; new DLL delivered via the client FTP folder fixed it. Triage rule: any client with custom ticket-ID/exchange DLLs must get rebuilt DLLs as part of the upgrade package. (Splash hangs on QCloud with Instant Login are a different animal → Security skill.)
- Related fulfillment defect: 25-01049340 "GPM Calculation Correction Utility Issue" (Software Defect, Installation/Upgrade) — the liquids correction utility that the upgrade runbook (§5) requires before restarting services on liquid-meter databases.

### 4.4 Post-upgrade login failures (QCloud)
- SF 26-01122205: after a TESTit UAT upgrade no user could log in; resolution: **database refresh + performing the upgrade again**. When an upgrade lands on a stale/partial refresh, redo refresh→scripts→app in order. See also 26-01081662 (Instant Login broken after refresh+upgrade → Security skill for the vault/`ALTER USER` recipe).

---

## 5. The FLOWCAL upgrade runbook (what "done right" looks like)

Verbatim step pattern from QCloud upgrade work items (ADO 1813878 MOM 10.4.0.4→10.6.0.5, ADO 1805213 [CCI]/TG Natural Resources 10.4.0.6→10.8.0.3, ADO 1806899 SCG 10.6.0.6→10.6.0.16):

1. Check the database version before upgrade.
2. Stop services on the app server.
3. **Uninstall** services (screenshot the current service list first so you can reinstall the same set).
4. Upgrade the database — run **every** incremental script in order ("do not miss any scripts").
5. Review script logs, resolve errors, and **run DBCOLCHECK**.
6. Install the application — RW always, RO too if the client uses it (installers named like `FLOWCAL-10.8.0.4.exe`; integrated services `FcIntegratedServices-<ver>.exe` — 25-01019921).
7. Reinstall the services.
8. Start services — but leave the **Report Service stopped/manual** during validation.
   - 10.8+ liquids clients: run the liquid-meter correction utility BEFORE starting services ("this step is very important for liquid meters ONLY" — ADO 1805213; utility defect: 25-01049340).
9. Smoke test: Volume Editor, Meter Editor, Location Editor, GQ Source, List Editor, Volume Statement report preview, Rollup Viewer, Exception Resolver, Quality Assignment, logs in the FC folder (C:), and Settings Manager > Service Configuration import path.

**DBColCheck** (`DbColCheck.exe`, double-click on the app server — ADO 1837326): compares the upgraded schema against the expected column/index inventory; output reviewed by support, who returns corrective SQL (25-01060058 — "I reviewed your DBColCheck results... run this against your database and then your test database will be completely upgraded"; 25-01048763). Gotchas:
- Empty DBColCheck log = rerun it, don't sign off (ADO 1866926).
- **False positive on 10.9:** `fc_exception_description` expected-count 3253 vs actual 3259 in the `__Index_columns` output — DbColCheck tool bug, fixed in `tools/dbcolcheck/tableinfo.h` line 4718 (ADO 1805447). Don't chase this one against a clean 10.9 DB.

**Installer prereq failure:** 26-01084386 — upgrading test 10.6.0.11→10.8.0.4 with `FLOWCAL-10.8.0.4.exe` (run as admin), dialog "MS Visual C++ Runtime for Visual Studio 2022 v.17 (x86) could not be installed", OK continues the wizard. Treat as a prereq install failure: install the VC++ 2022 x86 runtime manually (or verify a newer one exists), then proceed; support shared the 10.6→10.8 upgrade steps as the resolution.

---

## 6. TESTit/PROVEit desktop & server installers — SQL Server Express failures

**Signature:** during a TESTit 3.x / PROVEit 9.x desktop full-install ("Full" installers bundle SQL Server Express — x.14+ ship MSSQL 2019 per ADO 1160652; newer ship 2022), a popup says SQL Server could not be installed; or the app installs "half way". This is the **highest-volume actionable cluster for the TESTit/PROVEit literals**.

### 6.1 Domain accounts / restricted rights break the bundled SQL install — CONFIRMED defect
- Mechanism (ADO 1612199, from SF 23-00909260): the installer passes the logged-in `COMPUTERNAME\username` to MSSQL `setup.exe` as the account to provision as SQL sysadmin (`/QS /ACTION=Install /FEATURES=SQL,Conn,SDK /SECURITYMODE=SQL /SAPWD=...`). Exit message: "The Windows account <X> does not exist and cannot be provisioned as a SQL Server system administrator." Fails when the user is a domain account not in local users, or on locked-down corporate laptops.
- SF 25-01012469 (PROVEit 9.16/9.17, recurring): "The PROVEit installer expects the user running the install to be a user on the machine (local user)... SQL installation always has to be installed manually as well as creating fcfieldapps database, and ProveIt installer only installed half way."
- **Fix recipe (support-standard, 25-01024261 / 24-00971976 / 25-01004196):**
  1. Manually install SQL Server Express (matching version), instance name **FCFIELDAPPS**, mixed mode.
  2. Re-run the product installer (it now uses the existing instance), or if the app is already half-installed:
  3. Stop the TESTit/PROVEit services; run **`PasswordUtilityUI.exe`** (Password Utility) to create the `fcfieldapps` database and set passwords; update the **FCADMIN** password in the app; restart services.
  4. Finish with the site key (license transfer if it's a new computer → Licensing skill).
- The Password Utility is also the fallback when the installer's DB **upgrade** step fails (TESTit 3.14→3.17 DB upgrade failures — 25-01006345).

### 6.2 SQL Server 2022 + Windows 11 NVMe 4K sector size — CONFIRMED, full workaround on file
- SF 26-01100072 (PROVEit): SQL 2022 setup fails "Wait on the Database Engine recovery handle failed"; FCFIELDAPPS instance won't start (Error 1067); SQL errorlog shows "Unable to create stack dump file due to stack shortage". Root cause: NVMe drive reporting 4K-native sectors.
- Workaround (verbatim from the case, all steps as admin): uninstall SQL 2022 components + delete leftover `C:\Program Files\Microsoft SQL Server\MSSQL16.MSSQLSERVER\`; verify `Get-PhysicalDisk` BusType = NVMe; `REG DELETE` then `REG ADD "HKLM\SYSTEM\CurrentControlSet\Services\stornvme\Parameters\Device" /v ForcedPhysicalSectorSizeInBytes /t REG_MULTI_SZ /d "* 4095" /f`; reboot; confirm `fsutil fsinfo sectorinfo C:` shows PhysicalBytesPerSectorForAtomicity 4096; reinstall SQL 2022 fresh.

### 6.3 Installer's DB detection is instance-based, not database-based — known behavior
- ADO 1591870: after manually creating an empty FCFIELDAPPS instance, the installer reports "an existing database has been detected" — it assumes instance ⇒ database. Answer the prompt per the true state ("If this is an initial install... answer Yes" guidance in-thread). Affects Win11/Server 2022 with SQL 2019/2022, TESTit Desktop & Server.

### 6.4 Missing VC++ runtime prerequisites in field-app installers — CONFIRMED gap, closed
- ADO 1713160: Microsoft Visual C++ 2013 Runtime was not included in PROVEit installers (added to Full + Web installers for TESTit and PROVEit). ADO 1745793: x.18-generation installer prereq testing across TESTit Desktop / Server MSSQL / Server MSSQL-RO / Server Oracle and PROVEit Desktop / Server MSSQL / Server Oracle. If a 9.1x PROVEit crashes immediately on a clean machine, check installed VC++ runtimes before deeper triage.
- Related: ADO 1742791 (area `QuorumSoftware\Engineering\Measurement\Field Applications`) — Field Apps .NET services "failing to respond to the start or control request in a timely fashion" on a clean VM.
- Big picture: ADO 1779660 (Feature, Proposed) describes the whole MSI deployment system for FieldApplications products (TESTit, PROVEit, **PYCit**): Desktop = standalone + local SQL Express; Server = centralized SQL Server.

### 6.5 Windows 11 / OS-currency install questions
- 25-01006441 (TESTit 2.15 on Windows 11) and 26-01070115 (TESTit 2 + SQL 2019 + password utility) — old TESTit 2.x on new OSes generally routes to "upgrade to 3.x current"; support supplies the manual-SQL + password-utility path when clients must stay put.

---

## 7. Field-app launch/login failures right after install, upgrade, or a Windows update

All local-profile corruption patterns. Try these BEFORE reinstalling — reinstalling does not touch these files (proven by 25-01052975 where reinstall + DB re-create + relicense all failed).

| Error | File to delete | Anchor |
|---|---|---|
| "Root Element is missing" at TESTit login (app closes after 2nd error) | `C:\Users\<user>\AppData\Local\Flow-Cal, Inc\TESTIT\Layouts` (whole folder) | 25-01002929 (+ KB article "Troubleshooting Error Root Element Is Missing FA") |
| PROVEit "Exception Error occurred in Program.cs: Unexpected end of file... elements are not closed: property, property, XtraSerializer" — opens ~0.5s then crashes | Layouts folder under `C:\Users\<user>\AppData\Local\Flow-Cal, Inc\TESTit3` | 25-01060576 |
| TESTit "unknown error" at launch (after a Windows update); reinstall/relicense useless | `C:\ProgramData\Flow-Cal, Inc\Field Apps\fieldapplications.dat` | 25-01052975 |
| Login fails because SQL service down; service start = "Error 1069: logon failure" | none — SQL service Properties > Log On > re-browse account + re-enter Windows password (AD-password-change fallout, not a product bug) | 25-01003408 |
| "TESTit has encountered an unknown error" on launch, 3.11-era, single machine | try Layouts then `fieldapplications.dat` in that order | 25-01052975 pattern |

Post-upgrade launch errors with a **server** flavor (site key accepted then "application error") → §8 (NSBOWNER). Desktop login/password loops with the DB healthy → Password Utility recipe in §6.1 / Security skill.

---

## 8. FLOWCAL↔TESTit/PROVEit integration redeployment (the upgrade step everyone misses)

Integrated environments run NServiceBus-over-MSMQ services on both sides. **Every FLOWCAL or TESTit version move requires redeploying the integration with the matching `NServiceBusSetup-<ver>` package** — this is the #1 source of "upgrade done, sync dead" cases.

**Toolkit (ADO 1123422/1156271, live usage in ADO 1674731 [DLP UAT 10.3.0.18→10.6.0.1]):**
- `NServiceBusSetup-<ver>.zip` (e.g. 1.17.0.0 for 10.6-era, **1.19.1.0 for FLOWCAL 10.9.0.1 + TESTit 3.17** — 26-01117483). Internal source: `Q:\InstallBuilds\InstallSets\TESTit Integrated\TESTit 3\Installer\NServiceBusSetup`. Ships the NServiceBus license XML.
- `_Uninstall_Integration_Services.bat` — run as Administrator from `<FLOWCAL dir>\Integration` (e.g. `C:\FCAPPS\FLOWCAL-RW\Integration`).
- `FlowcalQueueConfiguration.ps1 -Cleanup|-Create -Version '<major.minor>' -Account <svc acct>` — MSMQ queue teardown/setup (ADO 1674731 used `-Account svcintservices@QCLOUD.com`).
- `FlowcalCompatibilityUpdate.ps1 <configFile path>` — **known issue**: it can error spuriously; per 26-01117483 resolution, "There is a known issue with the script, but since nothing has changed in this case, this step can be skipped."
- Integration services need Log On configured in service properties; Oracle sides need TNS_ADMIN/tnsnames.ora reachable (ADO 1123422).

### 8.1 Version mismatch detection: `NSBOWNER.SUBSCRIPTION` — CONFIRMED mechanism
- The subscription table's version column reflects each subscriber's **Contracts DLL**: FLOWCAL service (endpoint `FlowCal.Enterprise.Integration.Service`) reads `FlowCal.FieldApplications.Integration.Contracts.dll` in the FLOWCAL integration install dir; TESTit service (endpoint `FlowCal.FieldApplications.Integration.Service`) reads `FlowCal.Enterprise.Integration.Contracts.dll` under the TESTit install `Integration` folder (25-01001859, quoting product expert).
- **Standard fix when versions are stale:** stop services → re-run integration upgrade on BOTH sides (verify DLL file version/size actually changed) → **truncate the NSBOWNER subscription tables** → start services; the table repopulates from the live subscribers (25-01001859; same recipe re-proven in 26-01109179 where the TESTit side had silently stayed on 3.15.1.0).

### 8.2 The Oracle-19c cutover case — a complete post-mortem worth reading (26-01109179)
One client cutover produced five stacked integration failures, all resolved in-case:
1. FLOWAVERAGES landing in the OLD database — an automated job kept auto-restarting; kill it and run the job manually against the new DB.
2. Databus path in integration config files had an **invisible linefeed** character (found via Notepad++ in the logs).
3. Folder permissions removed on the integration service's folder — re-add.
4. Contracts DLL mismatch (TESTit side never upgraded in May) → §8.1 recipe including truncating `NSBOWNER.SUBSCRIPTION`.
5. TESTit couldn't send to the FLOWCAL **audit queue** — MSMQ queue-size limit hit; mitigation: nightly scheduled PowerShell purge of the audit queue (script template provided to client).

### 8.3 MSMQ is a per-server prerequisite — CONFIRMED
- 26-01110812: TESTit Server 3.16.0.0→3.19.0.0, sync dead after upgrade; fixed by **installing Message Queuing on every single server** + adding SQL Server component (AV) exclusions. On any multi-server topology change, verify the MSMQ Windows feature everywhere.

### 8.4 NSBOWNER account health
- 25-01004236: TESTit Server 3.14→3.17, post-site-key "An application error occurred" → the **NSBOWNER database account was locked**; unlock, then a follow-on error needed a reinstall. Post-upgrade checklist: NSBOWNER unlocked + password unexpired on Oracle before blaming the app. Related fulfillment: integration-service packages are requested alongside patches (25-01033843 — "FLOWCAL 10.6.0.8 Patch, Upgrade Scripts, and TESTit Integration Services"); TESTit Integration Service failures post-install also filed as 25-01051364.

---

## 9. Server / platform migrations, new environments, refreshes

### 9.1 Multi-server TESTit (new Citrix/app server): CAuthorization crash — CONFIRMED config pattern
- SF 23-00905031: new virtual Windows Server 2022 FLOWCAL server; launching TESTit from it throws `Exception Error occurred in Program.cs: The type initializer for 'FlowCal.FieldApplications.Classes.Utility.CAuthorization' threw an exception` (TESTit 3.14 log).
- Root cause: every server has its own `C:\ProgramData\Flow-Cal, Inc\Field Apps` — the licensing/auth state (`fieldapplications.pf`) must be **shared from one master server**. Fix, run as admin on each additional server:
```
mklink /d "C:\ProgramData\Flow-Cal, Inc\Field Apps" "\\<master-or-share>\Field Apps"
```
  Grant the share/NTFS access to the appropriate AD group. Same mklink pattern underlies TESTit-on-Citrix license issues (24-00940790; CrypKey MK-link variants → Licensing skill).
- Related: 24-00940399 "new server for flowcal - Testit not connecting to the db" (Application Configuration) — same family: on a new server, check Field Apps link + DB config file before anything else.

### 9.2 Database platform migration (AIX→Linux et al.) — CONFIRMED failure inventory
- SF 25-01060388: FLOWCAL DB migration AIX→Linux hit, in one weekend: **sequence issues** (client had to recopy sequences from the old DB), **missing optimizer statistics** (had to create statistics that were not there), general DB errors, and **rollup tables needing to be cleared**. Post-migration validation SQL in §12. Budget a support-on-call window for any cross-platform move.
- Oracle version upgrades under FLOWCAL/TESTit (19c cutover) → the 26-01109179 post-mortem in §8.2. TESTit Server on Oracle also needs its DB account privileges intact — `Database Error occurred in CDbio: ORA-01031: insufficient privileges` (25-01014088) is a grants problem, not a product defect.

### 9.3 Environment copies / UAT refreshes
- Routine: 26-01065453 (UAT Refresh), 25-01059092 (UAT Database Refresh), 25-01049182 (copy PRD→TST), 25-01053123 (copy of PRD+QA env), 26-01069142 (Test env refresh) — fulfillment, but the aftermath generates real cases: post-refresh logins/Instant Login break because vault/DB passwords diverge (26-01081662 → Security skill) and post-refresh+upgrade login failures need refresh-then-upgrade redo (26-01122205, §4.4).
- New self-hosted environments: 25-01051172 (config details for a new Linux-server test env) — hand the client the environment config doc; multi-server rules from §9.1 apply.
- Citrix estate changes during env moves: 25-01057567 (UAT apps open twice per ICA click), 25-01051107 (decommissioning old Citrix servers) — coordinate with Cloud; not product defects.
- TESTit 2→3 major-version data migration is a **Professional Services** engagement, not support: 23-00926727 / 24-00936647 (lists/locations migrated; period data gaps escalated to PS). Post-migration data-quality complaints like default pressure base wrong after migration (24-00947983) are config/data fixes.

---

## 10. Downgrades & version management

Downgrades are **not officially supported** ("We ideally don't allow customers to downgrade; however..." — 25-01032948) but support has a working recipe. Driver in both mined cases: newer PROVEit removed the ability to delete proving runs.

**PROVEit downgrade recipe (9.16.1→9.8.2, SF 25-01008909; variant 9.17.1→9.11, SF 25-01032948):**
1. Export everything from the current database (PIDX).
2. Stop the SQL Server service (FCFIELDAPPS instance).
3. Move the PROVEit database files (MDF & LDF) to a Backup folder.
4. Start the SQL service again.
5. Reset the `sa` password to the target version's default (cmd).
6. Run the older installer — create a NEW database during install.
7. Turn off PROVEit Import/Export services if unused.
8. Run the PROVEit **Password Utility** (match its version to the app, e.g. "1.4") to update passwords; reset the FCADMIN password.
9. Launch and re-import the PIDX from step 1.

**Upgrade-in-place for desktop PROVEit** (9.10→9.16.1, SF 25-01046353): backup data → uninstall old version → run the new installer and select the version you're coming from → installer updates passwords and launches. TESTit desktop upgrade issues follow the same shape (25-01009490).

**Version/package delivery facts:** FLOWCAL patches ship as RW & RO installers + `FcIntegratedServices-<ver>.exe` + per-patch upgrade scripts to the client FTP folder (25-01019921); TESTit has separate Desktop vs Server-MSSQL vs Server-Oracle installers (25-01008047, ADO 1745793); "x.18 Installers" is a tracked installer generation (ADO 1748335). Patch requests (25-01055644, 25-01004856) are fulfillment.

---

## 11. Known ADO items (verified live 2026-09-02)

| ADO id | Project | Type/Title (abbrev) | Relevance |
|---|---|---|---|
| 1814982 | Quorum | Bug: 10.7 Upgrade script change | UPPER() fix for FCTextFileExchange rename; script path `fc-migration\FLOWCAL Incremental\FLOWCAL 10\10.7\__updateDB_10.6.0.17_to_10.7.0.0.sql` (§3.1) |
| 1819174 | QuorumSoftware | Bug: Correct 10.6.0.17 to 10.7.0.0 upgrade script | Engineering-side of §3.1 |
| 1779716 | QuorumSoftware | Bug: Fix 10.8.0 to 10.9 upgrade script | COMMIT removals + ALTER reorder (§3.2) |
| 1811928 | Quorum | Bug: Postponed Queues due to Destination buffer too small! Will truncate (R1080* PORT) | 10.8.0.4–.7 post-upgrade rollup defect; tags "10.8.0.9; 10.8 StringCopy" (§4.2) |
| 1819169 / 1819170 | Quorum / QuorumSoftware | Same bug (R1090 PORT) / (DEV) | Port trio; 10.9 script `__updateDB_10.9.0.0.1_to_10.9.0.0.2.sql` (§4.2) |
| 1854903 | Quorum | Bug: Meter Import Error - July 2026 | UDF-cleanup script + "upgrade to 10.8.0.9" guidance (§4.1) |
| 1805447 | QuorumSoftware | Bug: Update exception description count for fc_exception_description in tableinfo.h | DBColCheck 10.9 false positive (§5) |
| 1612199 | QuorumSoftware | Bug: 23-00909260 User couldn't install MS-SQL during PROVEit 9.16 install | Installer provisions logged-in user as SQL sysadmin (§6.1) |
| 1591870 | QuorumSoftware | Feature: FieldApps Installers - Enhance detection of previously installed database | Instance-vs-database detection (§6.3) |
| 1713160 | QuorumSoftware | Feature: MS VC++ 2013 Runtime should be included in PROVEit installers | §6.4 |
| 1745793 | QuorumSoftware | Req: installer test TESTit/PROVEit VC++ prereqs | x.18 installer matrix (§6.4) |
| 1160652 | QuorumSoftware | Req: Update installers to ship MSSQL 2019 | x.14+ bundle history (§6) |
| 1742791 | QuorumSoftware | Bug: Field Apps .NET services failing to respond to start... on clean VM | Area `Engineering\Measurement\Field Applications` (§6.4) |
| 1779660 | QuorumSoftware | Feature: TMP - FieldApps: Deployment | MSI deployment system; PYCit product (§6.4) |
| 1123422 / 1156271 | QuorumSoftware | Feature/Req: Integration installers | NServiceBusSetup/FlowcalQueueConfiguration/CompatibilityUpdate docs (§8) |
| 1674731 | myQuorum Cloud | DLP UAT FLOWCAL Upgrade 10.3.0.18→10.6.0.1 | Live integration-redeploy command log (§8) |
| 1813878 / 1805213 / 1806899 | QuorumServices | FlowCal Upgrade Assistance Request (MOM / CCI / SCG) | Canonical runbook + smoke test (§5) |
| 1866926 | myQuorum Cloud | Upgrade Environment: [FC_MRCU] 10.8.0.9→10.8.0.10 | "Upgrade Environment" work-item type, tag "Measurement Upgrades"; empty-DBColCheck-log rule (§5) |
| 1837326 | myQuorum Cloud | Request Global Cloud Ops: [CFLP] Run DB ColCheck | DbColCheck.exe ops procedure (§5) |

---

## 12. Diagnostic SQL (FLOWCAL DB; Oracle syntax where shown — adapt for SQL Server)

```sql
-- §3.1 Detect the 10.7 export-rename miss (any rows returned = fix needed)
SELECT 'fc_report_group' t, group_name v FROM fc_report_group    WHERE UPPER(group_name) = 'FCTEXTFILEEXCHANGE'
UNION ALL
SELECT 'fc_report_schedule', group_name  FROM fc_report_schedule WHERE UPPER(group_name) = 'FCTEXTFILEEXCHANGE'
UNION ALL
SELECT 'fc_report_list(name)', report_name FROM fc_report_list   WHERE UPPER(report_name) = 'FCTEXTFILEEXCHANGE'
UNION ALL
SELECT 'fc_report_list(loc)', report_location FROM fc_report_list WHERE UPPER(report_location) = 'EXPORT\FCTEXTFILEEXCHANGE.DLL';

-- §4.1 Detect CR/LF-poisoned meter UDFs (repeat the predicate for user_field_s01..s30;
-- full 30-column cleanup UPDATE is in SF 26-01103168's resolution)
SELECT meter_number FROM fc_meter_characteristic
 WHERE INSTR(user_field_s01, CHR(13)) > 0 OR INSTR(user_field_s01, CHR(10)) > 0
    OR INSTR(user_field_s02, CHR(13)) > 0 OR INSTR(user_field_s02, CHR(10)) > 0;

-- §3.3 Upgrade-window sizing: find the monster tables first (Oracle)
SELECT segment_name, ROUND(SUM(bytes)/1024/1024/1024,1) gb
  FROM dba_segments WHERE segment_name LIKE 'FC_FF%_HOURLY'
 GROUP BY segment_name ORDER BY 2 DESC;

-- §8.1 Integration version check (integrated environments; NSBOWNER schema)
SELECT * FROM nsbowner.subscription;
-- Compare version values against the Contracts DLL file versions on each side (§8.1).

-- §9.2 Post-migration sequence sanity (Oracle): sequences behind MAX(pk) = the 25-01060388 signature
SELECT sequence_name, last_number FROM dba_sequences WHERE sequence_owner = 'FCOWNER';
```
Environment assumptions: FLOWCAL schema owner commonly `FCOWNER`, integration schema `NSBOWNER`; on client PRD these are **INFERRED** until confirmed against the live environment (metadata MCP binds DEV-tier only).

---

## 13. Expected-Behavior FAQ

- **"Do we need new integration scripts for FLOWCAL 10.9.0.1 + TESTit 3.17?"** Use `NServiceBusSetup-1.19.1.0`; the `FlowcalCompatibilityUpdate.ps1` error is a known issue and the step can be skipped when nothing changed (26-01117483).
- **"Does the TESTit Desktop x64 Full installer include SQL Server Express?"** Yes — Full desktop installers bundle SQL Express (MSSQL 2019 from x.14, 2022 later — 25-00998197, ADO 1160652); Server installers expect your own SQL Server/Oracle.
- **"Installer says a database was detected but this is a fresh machine."** It detected the FCFIELDAPPS *instance*, not a database (ADO 1591870). If you pre-installed SQL yourself, answer as an existing-DB install.
- **"Can we downgrade?"** Not supported, but a support-guided path exists (§10). Expect a full export/re-import; proving-run history behavior differs across versions.
- **"Upgrade scripts ran but DBColCheck flags fc_exception_description on 10.9."** Known tool false positive (ADO 1805447).
- **"Who does TESTit 2→3 data migration?"** Professional Services, not support (23-00926727).
- **"Why is the report service left stopped after our QCloud upgrade?"** Runbook step — it stays manual until smoke tests pass (ADO 1805213/1813878).

---

## 14. Escalation guidance

- **Upgrade-script defects (§3):** escalate to Measurement engineering with the script name (`__updateDB_<from>_to_<to>.sql`), the failing statement, DB platform (Oracle vs SQL Server) and the script log. Area paths: `Quorum\North America\Measurement[\Maintenance]`; engineering copies/ports in `QuorumSoftware\Engineering\Measurement\Maintenance` (R#### PORT titles).
- **Installer defects (§6):** area `QuorumSoftware\Engineering\Measurement\Field Applications`; include OS, SQL version, whether the account is domain-only, and the MSSQL setup exit message. FieldApplications source lives on GitHub (`flowcal/FieldApplications` — PR refs in ADO 1745793), so code-level fixes route through the Field Apps team, not ADO repos.
- **QCloud-hosted upgrades/refreshes:** file "FlowCal Upgrade Assistance Request" (QuorumServices) or "Upgrade Environment"/"Request Global Cloud Ops" (myQuorum Cloud, tag `Measurement Upgrades`). Always attach DB scripts log + DBColCheck output.
- **Integration sync death after upgrade (§8):** before escalating, capture: `nsbowner.subscription` contents, both Contracts DLL file versions, MSMQ feature state on every server, and the integration service log (look for invisible-character path errors). If subscription repopulation stalls with configs verified clean, pull in the products team (26-01109179 precedent).
- **Cross-platform DB migrations (§9.2):** pre-book support standby for cutover weekend; validate sequences/statistics/rollups with §12 SQL before go-live sign-off.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
