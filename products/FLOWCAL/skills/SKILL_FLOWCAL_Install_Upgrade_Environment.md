# SKILL — FLOWCAL Family: Installation / Upgrade / Environment / Deployment

> **Products:** FLOWCAL (10.x) · TESTit (3.x) · PROVEit (9.x) — `Product_list__c IN ('FLOWCAL','TESTit','PROVEit')`
> **Sources:** Salesforce all-history mining (closed cases through 2026-09-02, categories `Installation / Upgrade`, `Installation`, `Upgrades`, `Environment`, `Database` where upgrade-related) + ADO org `QuorumSoftware` (projects `Quorum`, `QuorumSoftware`, Measurement area paths).
> **Coverage plan group:** #4 Installation / upgrade / environment / deployment (~7,005 family cases, ~420 actionable floor).
> **Auto-Bot skill** — built by Aditya Bhagat. Every root-cause claim below is anchored to SF case numbers / ADO work item IDs, verbatim. Fixed-in builds are **INFERRED** from ADO/case comments unless marked release-notes-confirmed.

---

## 1. Quick Triage

| Symptom | Likely cause | § |
|---|---|---|
| `_updateDB_x_to_y.sql` throws ORA- errors (identifier length / invalid table name) during 10.9 upgrade | Oracle `COMPATIBLE` parameter still at 11.2 → 30-char identifier limit | §3.1 |
| DBColCheck shows missing/extra columns after upgrade | Skipped or partially-run incremental script; support supplies correction script | §3.1 |
| DBColCheck flags a count mismatch that is NOT real | DBColCheck tool defect (wrong expected counts) | §3.1 |
| FLOWCAL won't launch after upgrade — CrypKey / "Semaphore" error | CrypKey broken by upgrade → uninstall/reinstall CrypKey | §3.2 |
| "Error Initializing Crypkey" after PROVEit desktop upgrade | License lost by upgrade → re-license | §3.2 |
| FLOWCAL stuck on loading/splash screen (all users) | CrypKey service hung on app server → log out all, restart service | §3.2 |
| TESTit Server login fails right after environment upgrade | `NSBOWNER` DB account locked; secondary errors → reinstall TESTit | §3.2 |
| TESTit login fails after UAT upgrade (env-wide) | Bad upgrade against stale DB → refresh DB + re-run upgrade | §3.2 |
| "The provider is not compatible with the version of Oracle client" (TESTit/PROVEit launch, new server) | ODP.NET / Oracle client vs DB version mismatch; wrong bitness | §3.2 |
| Functional regression appears immediately after patch (calc, close, import, sync) | Version defect — check fixed-in chain before investigating | §3.3 |
| TESTit Server sync fails after upgrading to 3.19 | MSMQ (Message Queuing) not installed on every server | §3.3 |
| PROVEit crashes on open after Windows 10→11 upgrade | Known defect, fixed 9.16.2 / 9.17.1 (INFERRED) | §3.3 |
| SQL Server 2019/2022 install fails on Windows 11 laptop (TESTit/PROVEit desktop) | NVMe 4K-sector issue → `ForcedPhysicalSectorSizeInBytes` registry key | §3.4 |
| Installer hangs/fails at embedded MSSQL step | Pre-install SQL Server externally, then run product installer | §3.4 |
| "Error 1904. Module …dll failed to register" (crystal runtime) during TESTit/PROVEit install | .NET Framework 3.5/4 Windows features not enabled | §3.4 |
| "Exception Error occurred in CAppDATUtils: …" on TESTit/PROVEit launch | Corrupt local .DAT / profile data | §3.4 |
| "PROVEit has encountered an unknown error. Check the log file" on launch | Corrupt local profile → delete Flow-Cal, Inc. folders | §3.4 |
| App dead after server migration — license errors | CrypKey site key is machine-bound → new site key required | §3.5 |
| TESTit/FLOWCAL can't reach DB on newly built server | Missing `tnsnames.ora` entries / Oracle system variables | §3.5 |
| Users can't log in after UAT refresh from PRD (Instant Login / FCSRV) | RMAN copy carried PRD passwords → reset + unlock Oracle accounts | §3.5 |
| SSL error hitting hosted FLOWCAL | QCloud certificate renewal window / expired cert | §3.5 |
| TESTit-created meters fail to create in FLOWCAL (servers in time zone behind CST) | Known integration defect (timestamp offset) | §3.5 |

---

## 2. Decision Tree

```
Case mentions install / upgrade / migration / refresh / new server?
├─ DURING the upgrade (DB scripts, DBColCheck, installer wizard)
│   ├─ ORA- errors from _updateDB_*.sql          → §3.1 Oracle COMPATIBLE check first
│   ├─ DBColCheck discrepancies                  → §3.1 (real gap vs tool defect)
│   └─ Installer error (1904, MSSQL step, dirs)  → §3.4
├─ AFTER the upgrade
│   ├─ App won't launch / login fails            → §3.2 (CrypKey → DB accounts → Oracle client)
│   ├─ Feature worked before, broken now          → §3.3 (VERSION issue — check fixed-in list,
│   │                                                route via version-investigator / G3)
│   └─ Slow after upgrade                        → §3.3 (CFLA slowness ADO 1862906) else DB health
├─ FRESH desktop install (TESTit/PROVEit field laptop)
│   └─ §3.4 — SQL Server first, then app, then PasswordUtility, then license
├─ SERVER MIGRATION / NEW ENVIRONMENT
│   └─ §3.5 — checklist: site keys, tnsnames, Oracle client 32-bit, services, MSMQ
└─ ENVIRONMENT REFRESH (UAT←PRD)
    └─ §3.5 — routine op (Root_Cause__c 'Database Refresh Request'); post-refresh
              login failures = Oracle account passwords/locks
Gate note: most "upgrade assistance" volume is ROUTINE (Upgrade Request / Database
Refresh Request root causes) → G1/G2 cheap exits. Only regressions (§3.3) are G3,
and only script/tool errors (§3.1) or installer bugs are G5 candidates.
```

---

## 3. Symptom Clusters

### 3.1 FLOWCAL DB upgrade script & DBColCheck failures

**Signature.** Client DBA runs the incremental upgrade scripts and hits ORA- errors, or the post-upgrade DBColCheck output shows column/count discrepancies.

**Mechanics (CONFIRMED via ADO):**
- Upgrade scripts are shipped per-patch as `__updateDB_<from>_to_<to>.sql` under `SQL Scripts\SQLScripts\FLOWCAL Incremental\FLOWCAL 10\<major.minor>\` with `FcArchive\...-archival.sql` variants for the archive DB (ADO 1860577, 1863747, 1839314, 1836927, 1855349 — "Prepare upgrade script for X" stories; repo `fc-migration`).
- **DBColCheck** is the schema validation tool run before/after upgrades; it is "cloud internal only" tooling per ADO 1814917, but customers self-hosting run it and send results to support for review (dozens of routine "DBColCheck review" cases, e.g. 26-01119763, 24-00990177).
- Other utilities run during FC upgrades (ADO 1814917 inventory): `GPMCalculationCorrection`, `TicketRollupReportID`, `UpgradeCapacityTables`, `CRCompatibilityTool`, `FcRolePassword`, `FcInit` (licensing), `DurationFix`, `fctxt2binary`.

**Root causes & fixes (each anchored):**
1. **Oracle `COMPATIBLE` parameter too old.** Targa hit identifier-length and invalid-table-name ORA- errors running `_updateDB_10.6.0.17_to_10.7.0.0.sql` and `_updateDB_10.7.0.0_to_10.8.0.0.sql` for the 10.9.0.1 upgrade: their Oracle 19c DB had `COMPATIBLE=11.2.0.1.0`, still enforcing the 30-character identifier limit. Fix: `ALTER SYSTEM SET COMPATIBLE='19.0.0' SCOPE=SPFILE;` → restart DB → re-run scripts. (SF **26-01113819**, resolution verbatim.)
2. **Upgrade script content defect.** The 10.6.0.17→10.7 script's `UPDATE fc_report_group/fc_report_schedule/fc_report_list ... WHERE group_name='FCTEXTFILEEXCHANGE'` rename to `GasTextFileExchange` misses rows when stored case differs — fix added `UPPER()` to the WHERE clauses; failure mode is the subsequent `ALTER TABLE fc_report_schedule ENABLE CONSTRAINT fc_rptsch_f_group_name` erroring. (ADO **1814982** "10.7 Upgrade script change".)
3. **DBColCheck itself wrong.** 10.9 DBColCheck expected 3253 rows for `fc_exception_description` when actual is 3259 (`tools/dbcolcheck/tableinfo.h` line 4718) — false positive in `__Index_columns` output (ADO **1805447**). Historically DBColCheck also failed to flag missing columns in 5 tables (ADO **1415490**). So: a DBColCheck discrepancy is *evidence, not verdict* — confirm against the live schema before scripting corrections.
4. **Genuine column gaps.** When real, support reviews the DBColCheck output and supplies a correction script to run against the client DB (SF **25-01060058** "DBColCheck - Update Issue", Software Defect — attached fix script completed the test-DB upgrade).
5. **GPM Calculation Correction Utility issue** during upgrade window: SF **25-01049340** (Software Defect, Installation/Upgrade category) — utility is cloud-internal, run during FC upgrades (ADO 1814917).

**Recipe.**
1. Get exact script name + full ORA- error text.
2. Check `COMPATIBLE`: `SELECT name, value FROM v$parameter WHERE name = 'compatible';` (needs DBA; on client DB — label result CONFIRMED only if run).
3. If DBColCheck output attached: separate real gaps from known tool false-positives (ADO 1805447/1415490), then have support generate the correction script (pattern of 25-01060058).
6. Escalate to Measurement Maintenance only when the script content itself is wrong (pattern of ADO 1814982).

### 3.2 Post-upgrade launch & login failures (app won't start / can't log in)

**Signature.** Upgrade completed, now FLOWCAL/TESTit/PROVEit won't launch or users can't authenticate. Order of investigation: **CrypKey → DB accounts → Oracle client → reinstall**.

1. **CrypKey broken by upgrade (FLOWCAL).** "Unable to launch FLOWCAL application after upgrade" with a **Semaphore error** → uninstall/reinstall CrypKey resolved (SF **24-00939661**, Software Defect, CrypKey category). Same family: CrypKey `ERR3 - Semaphore wait on` (SF **22-00628893**).
2. **CrypKey service hang (env-wide stuck loading screen).** All users stuck on FLOWCAL loading screen → log everyone off the app server, restart the CrypKey service (SF **26-01069931**).
3. **PROVEit "Error Intializing Crypkey" after desktop upgrade** → re-license PROVEit (SF **23-00922988**, Licenses).
4. **TESTit Server: `NSBOWNER` account locked after PRD upgrade.** First error cleared by unlocking the NSBOWNER DB account; a follow-on error required reinstalling TESTit (SF **25-01004236**, App Config).
5. **TESTit login broken env-wide after UAT upgrade** → refresh the TESTit database and re-run the upgrade (SF **26-01122205**, App Config).
6. **Oracle client / ODP.NET mismatch on new or upgraded server.** `Oracle.DataAccess.Client.OracleException: The provider is not compatible with the version of Oracle client`:
   - Proper fix: install the **Oracle client version matching the DB** (19c), **32-bit** (SF **23-00906194** — TESTit launched from FLOWCAL on new server; SF **22-00676331** — PROVEit).
   - Emergency workaround (22-00676331 verbatim): copy `OraProvCfg.exe` into `...\ODP.NET\bin\2.x` and `...\PublisherPolicy\2.x`, then as admin GAC-register `Oracle.DataAccess.dll` and each `Policy.2.1xx.Oracle.DataAccess.dll` via `oraprovcfg.exe /action:gac /providerpath:...`.
   - Standing rule: **FLOWCAL/TESTit require the 32-bit Oracle client**; 19c 32-bit is supported (SF **24-00938067**, **22-00628905**).
7. **TESTit won't launch after server upgrade (transient).** Re-running the app updated meters/tasks, then re-login worked (SF **23-00921272**, Customer Error).
8. **.NET 3.5 dependency on servers.** TESTit 3.17.1 Report Jobs "An application error occurred" crash — engineering suspected missing .NET 3.5 on the customer's Windows Server 2019 (ADO **1781449**, SF 26-01067039). Check enabled Windows features on any new/rebuilt server.

### 3.3 Post-upgrade functional regressions (route as VERSION issues, G3)

When a feature breaks *immediately after* a version change, check the known-regression list before deep investigation. Confirmed pairs (fixed-in labels **INFERRED** from case/ADO comments unless noted):

| Broke in | Symptom | Fixed in / fix | Anchor |
|---|---|---|---|
| 10.8.0.3 | "Unable to establish openDate in STATION::Open for <mtr> at <month>" on specific meters | Bad-record SQL cleanup + fixed in **10.8.0.8** | SF **26-01101983** |
| 10.5.0.13 | GQ heating values wrong after upgrade | **10.5.0.16** delivered via FTP | SF **24-00987592** |
| 10.5.0.9 | Closing tickets extremely slow | version defect (Closing/PPA's) | SF **24-00967376** |
| 10.5.0.9 | Auto Edit not applying on import | version defect (Meter) | SF **24-00961560** |
| 10.5.0.3 | GQ Source Apply issue (critical) | version defect | SF **23-00923394** |
| 10.6.0.0 | Import issue | **10.6.0.6** (UAT+PRD upgraded) | SF **25-01025445** |
| TESTit 3.19.0.0 (UAT) | Server sync fails post-upgrade | Install **MSMQ (Message Queuing) on every server** + SQL Server component exclusions | SF **26-01110812** |
| TESTit server ≠ desktop version | Task synchronization status "failed" | Upgrade server and desktop to same version (3.17) | SF **25-01029467** |
| Win10→11 OS upgrade | PROVEit crashes on open (fleet-wide) | Fixed, delivered **PROVEit 9.17.1** (port ADO 1710375) + x.16.2 port (ADO 1710369) | ADO **1709028**, SF 24-00991076 |
| 10.x upgrade (CFLA archive envs) | FLOWCAL slow on startup after upgrade | Under investigation (DEV + R1090 PORT pair) | SF **26-01082541**, ADO **1862906/1862908** |
| 10.1.0.17 | FLOWCAL→TESTit integration exporting oversized files | version defect | SF **23-00893980** |

Also environment-shaped: TESTit-integrated meters **cannot be created in FLOWCAL when app servers run in a time zone behind CST** (timestamp offset ±3600s/hour causes constraint violation) — ADO **1773513** / **1812259**. Ask for server time zone on any new TESTit/FC integration environment.

ADO port convention: bug pairs carry `(DEV)` / `(R1090 PORT)` suffixes for the 10.90 branch (e.g. 1862906/1862908); support-origin bugs embed the SF case number in the title (`26-01067039 - …`).

### 3.4 Fresh install failures — TESTit/PROVEit desktop & field laptops

TESTit/PROVEit Desktop bundle a local SQL Server instance **`MSSQL15.FCFIELDAPPS`** (Windows service "SQL Server (fcfieldapps)"); most install failures are really SQL Server failures.

1. **Windows 11 + NVMe 4K sector — SQL Server install fails.** Full recipe (SF **26-01100072**, PROVEit + SQL 2022, verbatim; same fix on TESTit SF **25-01047256**, **25-01046239**):
   1. Uninstall all SQL Server components; delete leftover `C:\Program Files\Microsoft SQL Server\MSSQL16.MSSQLSERVER\`; reboot.
   2. Verify drive: `Get-PhysicalDisk | Select FriendlyName, MediaType, BusType` → applies when BusType = NVMe.
   3. `REG DELETE "HKLM\SYSTEM\CurrentControlSet\Services\stornvme\Parameters\Device" /v "ForcedPhysicalSectorSizeInBytes" /f`
   4. `REG ADD "HKLM\SYSTEM\CurrentControlSet\Services\stornvme\Parameters\Device" /v "ForcedPhysicalSectorSizeInBytes" /t REG_MULTI_SZ /d "* 4095" /f` → reboot.
   5. Verify: `fsutil fsinfo sectorinfo C:` → `PhysicalBytesPerSectorForAtomicity` must read 4096 before proceeding.
   6. Reinstall SQL Server fresh, then the product.
   - In stubborn cases the working combination was SQL Server **2022** instead of 2019, then create a new TESTit DB, swap in the customer's MDF/LDF backup, and run the Password Utility (25-01046239).
2. **Embedded MSSQL step fails in product installer.** Install MSSQL externally FIRST; the product installer then detects the toolset and skips its PowerShell MSSQL load (SF **26-01090422**, TESTit 3.13 on Win11).
3. **SQL system-admin provisioning error.** PROVEit 9.16 desktop installer failed at the MSSQL step: "The Windows account <machine>\<user> does not exist and cannot be provisioned as a SQL Server system administrator" (ADO **1612199**, SF 23-00909260) — local-account/profile problem, not a product defect.
4. **Old/broken SQL instance blocks install.** Delete the old SQL instance and install fresh (SF **25-01019100**); SQL service not starting post-install (SF **24-00987457**).
5. **"Error 1904. Module …dll failed to register" (crystal runtime).** Recurring TESTit/PROVEit installer failure (SF **22-00605150**, **22-00574854**, **22-00710217**, **22-00559920**). Fix that worked: Programs and Features → "Turn Windows features on or off" → enable **all** .NET Framework 3.5 and 4.x boxes (including children) → reboot → reinstall (22-00605150 verbatim).
6. **Launch exceptions from corrupt local data:**
   - `Exception Error occurred in CAppDATUtils: An item with the same key has already been added.` → delete the user's local **.DAT** file (single-user impact, permissions unaffected) (SF **26-01102884**, PROVEit, Software Defect).
   - `CAppDATUtils: '.', hexadecimal value 0x00, is an invalid character.` (SF **22-00633117**, **22-00619839**, TESTit).
   - `PROVEit has encountered an unknown error. Check the log file` → delete `C:\ProgramData\Flow-Cal, Inc.` and `%LocalAppData%\Flow-Cal, Inc.` folders, relaunch (SF **25-01017762**, Software Defect).
7. **TESTit desktop upgrade recipe (3.13→3.16.1 pattern, SF 24-00986150 verbatim; also 24-00987443):** stop "SQL Server (fcfieldapps)"; back up MDF/LDF from `C:\Program Files\Microsoft SQL Server\MSSQL15.FCFIELDAPPS\MSSQL\DATA`; run new installer as admin; run **PasswordUtilityUI** from the install directory ("change passwords only") using the standard FieldApps password set introduced in 3.16+ (`SA`, `FC_ADMIN`, `FC_USER_ROLE`, `FC_ADMINISTRATOR_ROLE`, `FC_VIEWER_ROLE`, `FC_OWNER` — retrieve values from case 24-00986150 or the install guide; do not guess); log in as `FCADMIN`, re-enter the service password under File > Services > Edit; switch back to Windows authentication. PROVEit desktop upgrades follow the simpler backup → uninstall old → run new installer (select prior version) → installer updates passwords (SF **25-01046353**, 9.10→9.16.1).
8. **FCIntegratedServices installer defect (FLOWCAL side of TESTit integration).** The 10.3.1 FcIntegratedServices installer dropped files into the FLOWCAL root install dir instead of `Integration\`, overwriting app files (ADO **1396059**; installers live under `\\fcfileserver\...\InstallBuilds\InstallSets\TESTit Integrated\TESTit 3\Installer\FcIntegratedServices`). If integration breaks right after installing integration services, verify file locations.

### 3.5 Server migration, new environment builds & refreshes

1. **Site keys after ANY server change (the #1 migration gotcha).** CrypKey licenses are machine-bound: moving FLOWCAL/TESTit/PROVEit to new hardware, Azure/Citrix migration, or even a Windows 11 OS reimage of a field laptop requires new site keys (SF **26-01092384** "Site Keys After More Server Migrations", **24-00981800/24-00981778/24-00981703/24-00981643** Azure migration batches, **25-01028670/25-01024863/25-01024592** laptop rekeys after Win11 upgrade, **26-01063775**, **24-00944376** 60-day trial key for migration testing). Counter-rule: an **in-place version upgrade does NOT need relicensing** — "You should not need to relicense Flowcal if you upgraded it without moving it to a new location" (SF **25-01015589** verbatim).
2. **New-server DB connectivity.** TESTit on a freshly built FLOWCAL server couldn't reach the DB — missing Windows system variables and `tnsnames.ora` entries; diagnosed by installing Oracle SQL Developer and diffing against a working server (SF **24-00940399** verbatim). Pair with the 32-bit Oracle client rule (§3.2.6).
3. **Post-refresh login/lock storm (hosted + self-hosted).** After a UAT refresh via RMAN restore from PRD, the UAT Oracle accounts carry PRD passwords → Instant Login and services fail. Fix (SF **26-01081662** verbatim, passwords redacted):
   ```sql
   ALTER USER FCSRV        IDENTIFIED BY <UAT pw> ACCOUNT UNLOCK;
   ALTER USER SVCFCINSTANT IDENTIFIED BY <UAT pw> ACCOUNT UNLOCK;
   ALTER USER FCOWNER      IDENTIFIED BY <UAT pw> ACCOUNT UNLOCK;
   ```
   Related: "Unable to Start FLOWCAL - RW - UAT Environment After Refresh" — post-refresh access restore steps requested as standing procedure (SF **26-01116210**).
4. **Refresh requests are routine ops**, not defects: Salesforce even has `Root_Cause__c = 'Database Refresh Request'` (≥10 closed 2026 cases, e.g. 26-01109551, 26-01102415, 26-01095808). Route to cloud/DBA runbook; only post-refresh breakage (item 3) needs investigation.
5. **Hosted (QCloud) environment errors.** SSL error reaching FLOWCAL = certificate renewal window; QCloud rotates certs (SF **26-01083623**; SSO cert renewal SF **25-01056493**). Citrix outages surface as env-down (26-01081662 first phase). Citrix server decommissions are coordinated infra changes (SF **25-01051107**).
6. **Field Apps API deployment.** The FA API deployment utility looked for CAPI (SChannel CSP) private keys in the wrong folder and failed to grant app-pool access to the TLS cert — deployment fails with cert/permission errors (ADO **1833845**, fixed/Closed 2026-07).
7. **Migration assistance scope.** Full platform moves (Test+Prod to new site/servers) are Services engagements, not support tickets (SF **25-01050601**, **25-00999178**, **24-00954165** — closed as guidance/Not in Product Plan).

---

## 4. Known ADO items (cite these, don't rediscover)

| ADO | Type/State | Title (verbatim) | Relevance |
|---|---|---|---|
| 1814982 | Bug, Closed | 10.7 Upgrade script change | UPPER() fix to FCTEXTFILEEXCHANGE renames in `__updateDB_10.6.0.17_to_10.7.0.0.sql` |
| 1805447 | Bug, Closed | Update exception description count for fc_exception_description in tableinfo.h | DBColCheck false positive on 10.9 |
| 1415490 | Bug, Closed | DbColCheck does not recognize missing columns in 5 tables | DBColCheck false negative |
| 1814917 | Story, Closed | SPIKE: Hookup other Tools into Azure | Inventory of upgrade-time utilities (GPMCalculationCorrection, UpgradeCapacityTables, CRCompatibilityTool, FcInit, FcRolePassword, DbColCheck…) |
| 1860577 / 1863747 / 1839314 / 1836927 / 1855349 / 1841021 / 1864169 | Stories, Closed | Prepare upgrade script for 10.x.y.z | Upgrade-script naming/location convention (`fc-migration`, FcArchive variants) |
| 1709028 | Bug, Closed | 24-00991076--PROVEit Crashing | PROVEit crash after Win10→11; ports 1710369 (x.16.2), 1710375 (x.17.1 — "delivered in PROVEit 9.17.1") |
| 1612199 | Bug, Closed | 23-00909260--User couldn't install MS-SQL server during the PROVEit 9.16 installation | Windows-account SQL sysadmin provisioning error |
| 1586782 | Bug, Closed (Duplicate) | 23-00890640--PROVEit running slow | 9.14 slowness, Win11 angle |
| 1396059 | Bug, Closed | [AHT] FCIntegratedServices installer installs files to the wrong location | 10.3.1 integration installer defect |
| 1781449 | Bug, Proposed | 26-01067039 - Devon - TESTit Report Job Error | Missing .NET 3.5 on Windows Server 2019 suspected |
| 1833845 | Bug, Closed | FA API Deployment - Deployment utility looks for CAPI (SChannel CSP) private keys in the wrong folder… | Field Apps API deployment cert failure |
| 1773513 / 1812259 | Bugs | TI cannot create meter in FC via integration when time zone is behind CST | Environment time-zone defect |
| 1862906 / 1862908 | Bugs, Analyze/New | CFLA Slowness on start up of FLOWCAL Investigation (DEV) / (R1090 PORT) | Post-upgrade startup slowness, open |

Area paths: `Quorum\North America\Measurement(\Maintenance | \Field Apps and API)`; engineering copies in `QuorumSoftware\Engineering\Measurement\Maintenance`. Port suffix convention: `(DEV)` / `(R1090 PORT)`.

---

## 5. Diagnostic SQL (FLOWCAL Oracle DB unless noted — label results NOT YET RUN until executed on the client env)

```sql
-- 1. Oracle COMPATIBLE parameter (upgrade-script ORA- errors; case 26-01113819)
SELECT name, value FROM v$parameter WHERE name = 'compatible';

-- 2. FLOWCAL DB version stamp before/after running updateDB scripts
--    (verify the from-version matches the script chain being run)
--    Table name INFERRED from support practice — confirm via DBColCheck output header.

-- 3. Post-refresh / post-upgrade account state (case 26-01081662, 26-01116210)
SELECT username, account_status, lock_date
FROM   dba_users
WHERE  username IN ('FCOWNER','FCSRV','SVCFCINSTANT','NSBOWNER');

-- 4. Invalid FC indexes after upgrade/reorg (ORA-01502 family; cases 22-00631496, 22-00671360)
SELECT table_name, index_name, tablespace_name, status
FROM   all_indexes
WHERE  table_name LIKE 'FC%' AND status <> 'VALID';
-- rebuild generator:
SELECT 'alter index '||index_name||' rebuild tablespace '||tablespace_name||';'
FROM   all_indexes WHERE table_name LIKE 'FC%' AND status <> 'VALID';

-- 5. Who is still connected before an upgrade window (case 22-00671360)
SELECT username, osuser, machine, program FROM v$session ORDER BY 1;
```

TESTit/PROVEit desktop (SQL Server): instance `MSSQL15.FCFIELDAPPS` (or MSSQL16 for SQL 2022); data files under `...\MSSQL\DATA`; sector check `fsutil fsinfo sectorinfo C:`.

---

## 6. Expected-Behavior FAQ (cheap G1 exits)

- **"Please review our DBColCheck results"** — routine service, not a defect. Support reviews and either blesses the upgrade or returns a correction script (26-01119763, 24-00990177, 25-01015589).
- **"Upgrade our UAT/PRD to version X" / "send installers"** — routine Upgrade Request; hosted clients go to the cloud team (24-00983744), self-hosted get FTP-delivered packages + release notes (25-01004856). Note: many such routine tickets are miscoded `Root_Cause__c='Software Defect'` — do not treat the code as evidence.
- **"Refresh UAT from PRD"** — routine `Database Refresh Request` (26-01109551 et al.). Expect §3.5.3 password/lock follow-up.
- **Windows 11 compatibility:** PROVEit 9 works on Windows 11 including 25H2 (26-01116501); TESTit behavior unchanged by Win11 itself (23-00886019) — the pain is SQL Server install (§3.4.1) and rekeys (§3.5.1). FLOWCAL 10/TESTit 3.14+ compat questions answered via system-requirements doc (24-00956525, 26-01088763).
- **Oracle client choice:** 32-bit required; 19c 32-bit supported for FLOWCAL/TESTit (24-00938067, 22-00628905).
- **Re-license after upgrade?** No — only after a machine/location change (25-01015589 vs §3.5.1).
- **SSO:** FLOWCAL has no traditional SSO; Instant Login uses Windows group membership (26-01103830). Hosted auth is OKTA-fronted (QCloud).
- **DB partitioning for performance:** FLOWCAL does not target partitions in queries; partitioning helps maintenance, not app speed — DB health assessments are a Services engagement (26-01120809).

---

## 7. Escalation guidance

- **L4 → Engineering (Measurement Maintenance):** upgrade-script content errors (attach exact script name + ORA- text; pattern ADO 1814982), DBColCheck tool false positives/negatives (ADO 1805447/1415490), reproducible post-patch regressions (§3.3 — file with SF case number in the ADO title, expect DEV + PORT pair).
- **L4 → Cloud/QCloud:** hosted env down, cert/SSL renewals, refreshes, OKTA/Citrix access, upgrade execution for hosted clients.
- **L4 → Services:** whole-platform migrations, new environment builds, DB health/partitioning projects (25-01050601, 26-01120809).
- **Stay in support (recipes here):** CrypKey reinstalls/rekeys, Oracle client installs, SQL Server on Win11, PasswordUtility runs, tnsnames fixes, post-refresh account unlocks.
- Always capture: product + exact build (e.g. 10.6.0.15 / 3.17.1.0 / 9.17.1), hosted vs self-hosted, Oracle vs SQL Server, and what changed last (patch? OS? server? refresh?). "What changed" resolves ~80% of this group.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
