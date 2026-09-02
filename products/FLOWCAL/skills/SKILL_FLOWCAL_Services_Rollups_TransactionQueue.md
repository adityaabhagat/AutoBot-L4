# SKILL — FLOWCAL Windows Services, Rollups & Transaction Queue

> **Product:** FLOWCAL (Product_list__c `FLOWCAL`; TESTit server-side services covered where the same `FcSrv*` machinery is involved)
> **Coverage plan group:** #3 — Windows services, rollups & transaction queue (~3,125 family cases, ~345 actionable)
> **Sources:** Salesforce closed-case mining (all history, 2013–2026-09), ADO org `QuorumSoftware` (projects `Quorum`, `QuorumSoftware`; area paths `Quorum\North America\Measurement*`, `QuorumSoftware\Engineering\Measurement\Maintenance`). Mined 2026-09-02.
> **Auto-Bot** — the L4 issue solver built by **Aditya Bhagat**.
> Confidence labels: `CONFIRMED` = anchored to SF Resolution/ADO repro; `INFERRED` = build/fix claim from case text, not release-notes-verified.

FLOWCAL background processing runs as a fleet of Windows services (`FcSrv*.exe`) installed on the app server and administered from **Settings Manager > Services > Service Configuration** (queues visible under **Settings Manager > Services > Service Queues**). The big four data movers:
- **FcSrvTrans.exe** — Transaction Queue (TQ): drains `fc_transaction_queue` (SCADA/FMS periodic + event + meter-characteristic transactions) into meter data.
- **FcSrvMtrRollup.exe / FcSrvLcnRollup.exe / FcSrvCalcMtrRollup.exe** — meter/location rollups: aggregate periodic data into daily/monthly final-form tables; queues in `fc_meter_rollup_queue` (+ location equivalent); status visible in **Rollup Viewer**.
- **FcSrvGQTrans.exe** (a.k.a. FcGqTrans.exe) — Source/analysis apply: drains `fc_gq_apply_queue` ("Unprocessed Analysis Apply" queue) applying GQ source analyses to meter data.
- **FcSrvAutoEstimate.exe** — creates estimated volume records for non-reporting meters.
Others seen in this cluster: `FcSrvFileImport(.2).exe`, `FcSrvReports.exe`, `FcSrvCloseData.exe`, `FcSrvLcnCloseData.exe`, `FcSrvHCDPQueueProcessor` (HCDP calc queue), `FcSrvGQAnlRollup` (GQ analysis rollup), and TESTit-side `FcSrvFaExport`, `FcSrvDataManagement`, `FcSrvTESTitCalAdjApply.exe`, `FcSrvTESTitAnalysisSync`, `FcSrvListMembersAPI`.

---

## 1. Quick Triage

| Symptom | Likely cause | § |
|---|---|---|
| ALL services red in Services Monitor / "fails to log in" | FCSRV service-account password expired or locked | §3.1 |
| One service crash-loops after hours of running; restart helps temporarily | Known memory leak (<10.5) or version-specific defect | §4.1 |
| Service won't START under a service account after upgrade to 10.8.0.0 (runs fine as local user) | 10.8.0.0 launch defect, fixed 10.8.0.2 | §4.2 |
| DB reports "max processes are reached" (TESTit FcSrvFaExport/FcSrvDataManagement) | Connection-leak defect, fixed TI X.17.0 | §4.3 |
| FcSrvReports dies immediately on start; log blames an export dll or a specific .rpt | Report/dll defect (FcTextFileExchange.dll), fixed 10.8.0.10 | §4.4 |
| TQ backlog growing; service crashes repeatedly ("abnormal termination") | Poison record in `fc_transaction_queue` (several known data-shape crash bugs) | §5 |
| TQ records marked status 10, not written to DB, FK error on Lab Analysis ID; only with 3+ TQ services | Multi-instance race condition | §5.5 |
| TQ processes but Volume Editor still shows only auto-estimated data | TQ transactions not matching periodic data (defect class) | §5.6 |
| Meter/location stuck **Postponed** in Rollup Queue; requeue → postpones again | Data condition: duration/flow_time garbage, data gap, or 10.8 StringCopy bug | §6 |
| Rollup log: `Destination buffer too small! Will truncate` + garbage in FC_METER_CHARACTERISTIC user fields | 10.8 StringCopy defect family, fixed 10.8.0.9 | §6.1 |
| Rollup Viewer "Incomplete" days but hourly complete; wrong `rollup_report_id` | Duration Fix Utility + VCF recalc workaround | §6.2 |
| ORA-01653 unable to extend FC_FFMTR_HOURLY / FC_ROLLUPS_*_TS | Tablespace full — DBA extend, not a product bug | §6.4 |
| "Unprocessed Analysis Apply" queue not draining (hundreds–10k+ entries) | FcSrvGQTrans not running/undersized, or version defect (10.8.0.5) | §7 |
| GQ Rollup queue pending 500K records, service hangs | Defect fixed 10.5.0.13 | §7.3 |
| Auto Estimate service not creating estimates | Licensing (site key), config, or version defect | §8 |
| System "made edits on its own" / meter closed by FCSRV | Expected behavior of services (analysis apply, scheduled close) or a known 10.5.0.17 defect | §9 (FAQ) + §8.2 |

## 2. Decision Tree

```
Service issue reported
├─ ALL services down/red?
│   ├─ Services Monitor: "fails to log in" → FCSRV account expired/locked → reset pwd + restart (§3.1)
│   └─ After environment change (server move, upgrade)? → check service install + licensing/site key (§3.2)
├─ ONE service down or crash-looping?
│   ├─ Version < 10.5 and dies after hours → memory leak; schedule restarts, upgrade (§4.1)
│   ├─ Just upgraded to 10.8.0.0 and won't start under svc account → fixed 10.8.0.2 (§4.2)
│   ├─ TESTit FcSrvFaExport/FcSrvDataManagement + "max processes" → TI X.17.0 (§4.3)
│   ├─ FcSrvReports dies on start → isolate report/dll; 10.8.0.10 fix (§4.4)
│   └─ Otherwise → check _FC_DB_ERROR.LOG + service log for the killing record (§5/§6 pattern)
├─ TQ backlog / crash?
│   ├─ Crash repeats at the same record → poison-record family: find & park it (unavailable=999),
│   │   requeue rest, match to known bug (§5.1–§5.6)
│   └─ No crash, just slow → add FcSrvTrans instances (watch §5.5 multi-instance race)
├─ Rollups postponed / incomplete?
│   ├─ Log says "Destination buffer too small!" → 10.8 StringCopy family (§6.1)
│   ├─ Log says "Unable to rollup Meter <x> ... Postponing queue entry" → data condition:
│   │   Duration Fix Utility, flow_duration/flow_time cleanup, purge/reload (§6.2, §6.3)
│   └─ ORA-01653 in log → extend tablespace (§6.4)
├─ Analysis/GQ apply queue stuck? → service running? sized right? version defect? (§7)
└─ Auto Estimate not estimating? → license, then config, then version (§8)
```

Gate mapping: §3, §6.4, §7.1–7.2, §8.1 are usually **G2 Config**; §4, §5 poison-record families, §6.1, §7.3 are **G3 Version** or **G5 Code**; §6.2–6.3 are **G4 Bad Data** with utility-driven correction.

---

## 3. Cluster A — All services stopped (account / environment / provisioning)

### 3.1 FCSRV service-account password expired or locked
- **Signature:** Services Monitor shows file import "fails to log in", other services red; everything stopped at once. Often reported as "system down" at month-close.
- **Root cause:** The shared `FCSRV` Windows service account's password expired (`CONFIRMED` SF 25-01023295: "The FCSRV password expired. The Cloud team reset the FCSRV password and restarted the services.") or the account got locked (SF 25-01031729).
- **Fix recipe:** (QCloud: route to Cloud team) Reset/unlock the FCSRV account password → update the logon credential on each FLOWCAL Windows service (or re-type PW on the Services window) → restart services → confirm queues drain. Prevention: set the service account to non-expiring per client security policy, or calendar the rotation.
- **Anchors:** SF 25-01023295 (Application Configuration), SF 25-01031729, SF 25-01053261 / 26-01064956 / 26-01065803 (UAT services down, repeat offender — user-administration).

### 3.2 Service not installed / needs install or extra instances
- **Signature:** A queue never drains because the corresponding service simply isn't installed in that environment (common after new env / refresh / selective provisioning).
- **Fix recipe:** Install + start the missing `FcSrv*` service. Examples: FcGqTrans.exe installed by QCloud cleared the Unprocessed Analysis Apply queue (`CONFIRMED` SF 25-01040936); FCSrvGQAnlRollup install request (SF 25-00999483); Auto Estimate service install in UAT (SF 24-00995466); report service enablement in UAT (SF 26-01115940).
- **Note:** Licensing can gate services — an Auto Estimate outage was resolved via CrypKey site code/site key exchange (`CONFIRMED` SF 25-01011146; license transfer needed after one of two servers died). If a service silently does nothing after a server move, check license before debugging code.

### 3.3 December-style multi-service disruptions (QCloud)
- Recurring QCloud incidents show as multiple services stopping; resolution is restart + environment fix, classified Application Configuration (SF 25-01062510, SF 25-01039728 `FcSrvMtrRollup` failure marked Cloud Outage). Treat as environment first, defect second — ask Cloud ops for server event logs before code-level investigation.

## 4. Cluster B — Single service crashing / resource exhaustion

### 4.1 Memory leak in import (and sibling) services, versions < 10.5
- **Signature:** FcSrvFileImport (and other services) run for several hours then die with memory-related errors; reboot doesn't cure; recurs daily.
- **Root cause:** `CONFIRMED` known memory leak, resolved in 10.5+ (SF 25-01062691 Resolution: "known memory leak issue in your version ... resolved in 10.5 and later"; also SF 25-01055291 `FCSRVTESTitAnalysisSync` memory leak report on FC 10.2.0.30).
- **Fix recipe:** Interim — Windows Scheduled Task to restart the affected services on a cadence. Real fix — upgrade to ≥10.5 (`INFERRED` exact patch level; verify in release notes).

### 4.2 10.8.0.0: Import & Report services won't start under a service account
- **Signature:** Right after upgrade to 10.8.0.0, FcSrvFileImport/FcSrvReports start fine as local user but fail to start under any domain service account; registry timeout increase does NOT help; users can't export reports to network shares.
- **Root cause / fix:** `CONFIRMED` product defect, resolved in **10.8.0.2** (SF 25-01051113, Software Defect).
- **Anchors:** SF 25-01051113.

### 4.3 TESTit FcSrvFaExport / FcSrvDataManagement exhaust DB "max processes"
- **Signature:** After installing these two TESTit services on the app server, Oracle hits "max processes are reached"; reinstall/re-type password doesn't help; reproduces in DEV and QA.
- **Root cause / fix:** `CONFIRMED` connection-leak defect; SF Resolution: "Will be addressed in TI X.17.0 released 5/24/24" (`INFERRED` = TESTit 3.17.0). Interim workaround: Scheduled Task stop/start of both services every hour.
- **Anchors:** SF 23-00930961 (Software Defect).

### 4.4 FcSrvReports killed by a specific report / export dll
- **Signature:** Report service crashes the moment it starts in PRD; log points to `FcTextFileExchange.dll` ("Unable to access the export dll export\FCTextFileExchange.dll") or a specific .rpt (e.g. Liquid Volume Statement / volume summary by total fluid).
- **Root cause / fix:** `CONFIRMED` defect resolved in **10.8.0.10** (SF 26-01119134); same-signature earlier case SF 26-01103514. Triage recipe: pull the report schedule queue, identify the report being picked up at crash time, disable/deschedule it to restore service, then match version.
- **Anchors:** SF 26-01119134, SF 26-01103514 (both Software Defect).

### 4.5 FCSRVTESTITCALADJAPPLY "Failed to run process"
- Calibration-adjustment apply service fails to run (Software Defect, SF 25-01046750; related integration confusion SF 26-01088530 was Training). Check the DB log for the service's error rows (SF 25-00996566) before assuming defect.

## 5. Cluster C — Transaction Queue (FcSrvTrans) not processing / crashing

**Mental model:** TQ crashes are almost always *data-driven*: one poison transaction kills the service, service restarts (or is restarted), hits the same record, dies again — so the queue "is not processing". The generic recipe: find the record the log dies on → park it (`update fc_transaction_queue set unavailable = 999 where ...`) → restart service to drain the rest → root-cause the poison record against the known families below. Requeue parked rows later with `unavailable = 0`. (Parking convention `unavailable=999` and requeue `unavailable=0` appear verbatim in ADO repro steps — Bug 1745472, Bug 1797611.)

Known poison-record families (all reproduced by engineering with FcDataBoss + SQL + `run fcsrvtrans`):

### 5.1 Orphan transaction_type 4 (meter characteristic edit) without Transaction Snapshot
- **Signature:** TQ stops with ~100K+ unprocessed; monitoring shows crashes when SCADA/FMS sends **transaction_type 4** (meter characteristic edits) records without the corresponding edit/snapshot record; other transaction types importing simultaneously for the same meter hit inconsistencies and the service fails.
- **Fix recipe:** Correct at the source system (FMS) so type-4 edits always ship with their snapshot; use diagnostic SQL to detect orphans (script attached to the SF case). Reset/park the orphans to unblock.
- **Anchors:** `CONFIRMED` SF 26-01086935 (Continental Resources); related snapshot-crash bug ADO **1773284** "TQ is crashing on snapshot record" (CLR 25-01062128); newest open ADO **1868173** "TQ crashes" (CLR 26-01124783).

### 5.2 AGA-2013 / SI Units meter-characteristic change crashes TQ
- **Signature:** Service crashes processing a meter whose characteristics were changed to AGA-2013 (e.g. "SI Units 2016 at 15C"); crash confirmed in 10.5.0.16.
- **Anchors:** ADO **1685148** "TQ service crashing on AGA-2013 data" (New), ADO **1802507** (2026 duplicate/port). No fixed-in build confirmed — treat as open; workaround is parking the record and correcting the characteristic.

### 5.3 NULL temperature/pressure on gas turbine meters
- **Signature:** TQ (and CFX import) crash on turbine meter records where T and P are not provided. Behavior regressed in **10.4.0.0+** — older versions performed the invalid calc silently; 10.4+ crash hard.
- **Anchors:** ADO **1549450** (Dev, tag z10.5.0, Closed) + port **1563276** (R1040 PORT, Closed) — `INFERRED` fixed ~10.5.0/10.4 port. Workaround from bug history: ensure P/T present (or zero pulses/volume records).

### 5.4 Out-of-range GQ percentages (1992 Gross 2) crash TQ during GQ apply
- **Signature:** TQ crashes minutes after start "when doing GQ apply"; cause: component percentages out of range for the 1992 Gross 2 calculation, aggravated by records with volume=1 / raw volume=0.
- **Anchors:** ADO **1615044** (SF 23-00912180, FLOWCAL 10.5.0.0, Closed). Customer-side fix: correct the bad records; product hardened to not crash.

### 5.5 Multi-instance race: 3+ TQ services → status 10, FK violation on Lab Analysis ID
- **Signature:** With 3 or more FcSrvTrans instances running, records get marked **status 10** and are not written; `_FC_DB_ERROR.LOG` shows an FK constraint on Lab Analysis ID; requeueing the same data processes cleanly.
- **Fix recipe:** Drop concurrency to 2 instances (or requeue affected batches) until on a build where this is fixed; treat as scaling ceiling when sizing TQ throughput.
- **Anchors:** `CONFIRMED` SF 23-00930144 (Application Configuration).

### 5.6 TQ "processes" but periodic data never lands (auto-estimates persist)
- **Signature:** No crash; TQ drains, but Volume Editor still shows only auto-estimated data for specific meters unless a manual .CFX import is done. Seen on 10.6.0.10 (SF 26-01064118, gas meters, downstream partner impact).
- **Triage:** Compare `fc_transaction_queue` rows for the meter (processed flags) vs `fc_meter_periodic_values` revisions; get FcDataBoss + CFX from client for repro. Related defect: ADO **1797611** "TQ does not process certain records" — ~40 meters / 4000 records stuck; suspected transaction_type 10 (UFM diagnostic) involvement; service eventually crashes with repeating db-error messages. No confirmed fix build — escalate with databoss repro.
- Also: 10.6.0.11 TQ "abnormal termination" bug (`CONFIRMED` still-an-issue-in-10.6 statement, SF 25-01056281; client moved to 10.8). QCloud crash-restart loop case SF 25-01032779 → ADO **1745472** (negative atmospheric pressure −14.1 sent while atm pressure config is 14.1 → hang/crash; state Proposed). TQ event-processing crash ADO **1624504** (CLR 23-00923429, closed Duplicate).

## 6. Cluster D — Meter / Location rollups postponed, incomplete, or wrong

### 6.1 10.8 "StringCopy" family: `Destination buffer too small!` → postponed queues + corrupted user fields
- **Signature:** After upgrading to 10.8.x (trigger case: 10.5.0.11 → 10.8.0.4), location/meter rollups postpone en masse. `_FC_SRV_LCN_ROLLUP_LOG.LOG` / `_FC_DB_ERROR.LOG` full of: `FcAssert Failure in 'void __cdecl FCSystem::CheckTruncation(size_t, const char *, size_t)' : expression: 'source_len <= destSize' is false : message: 'Destination buffer too small! Will truncate'` (source `Dlls/CBuilderGUIs/SetFlowCalString.h(42,46)`). Side effect: garbage characters written into `FC_METER_CHARACTERISTIC.USER_FIELD_*` (VARCHAR2(20 BYTE)) — the bad data then re-triggers the assert everywhere it's read (volume editor, meter close, imports).
- **Root cause:** 10.8 string-copy hardening asserting on legacy over-length data; CFX import was also writing bad data into user fields (fix ADO **1796147** "CFX files importing incorrect Meter Characteristics User Fields (R1080* PORT)").
- **Fix recipe (verbatim from SF 26-01112398 resolution):**
  1. Execute the cleanup script from WI **1837701** (clears bad-data user fields in `fc_meter_characteristic`).
  2. Add to `FcDebugOptions.cfg`:
     ```
     [ALL_USERS]
     disable_string_copy_checks = Y
     ```
  3. Restart the affected services.
  Permanent fix: **10.8.0.9** (`CONFIRMED` via bug tag "10.8.0.9" on ADO 1811928 and regression Requirement ADO 1839078; SF 26-01115461 also cites 10.8.0.9 for the GQ-apply flavor).
- **Anchors:** SF 26-01112398 (Coastal Flow UAT); ADO **1811928** (R1080* PORT, Closed, tags `10.8.0.9; 10.8 StringCopy; Escalated`), **1819169** (R1090 PORT, Closed), **1819170** (DEV, Closed), **1819152** (Volume Editor buffer overflow, 10.8.0.5), **1808959**/**1820422** (meter close / volumetric view "Unable to establish openDate"), **1849624** (RCA, CFX import crash 10.10.0.0, `Set_user_field_s15` truncation), **1792011** (10.8.0.4 upgrade error, GPMCalculationCorrection.exe), Cloud script WI **1837701**.

### 6.2 Postponed / incomplete from bad flow durations & rollup IDs — Duration Fix Utility
- **Signature:** Meters postpone repeatedly ("Unable to rollup Meter <x> ... Unknown exception type ... Error: Postponing queue entry" in the meter rollup log), or Rollup Viewer shows daily Incomplete while hourly is Complete; root data condition = wrong `flow_duration`/`flow_time` on latest revisions, data gaps, or wrong `rollup_report_id`/`measurement_day` on `fc_meter_periodic_values`.
- **Fix recipes (all CONFIRMED from case resolutions):**
  - Run the **Duration Fix Utility** for the affected meters, then requeue (SF 26-01098300 — utility found and corrected a data gap).
  - Duration Fix Utility + **force VCF recalculation** — regenerates a new revision in `fc_meter_periodic_values`, and FLOWCAL reassigns `rollup_report_id` and `measurement_day` correctly; may generate new exceptions, validate in UAT first (SF 26-01090240, verbatim workaround).
  - If the utility finds nothing: **purge + reload + requeue** the meter data (SF 26-01096658).
  - Engineering-side variants: clean `flow_duration`/`flow_time` on latest revisions, "recalc rollup IDs" from the Toolbox (ADO **1613415**, Harvest 23-00900241, Closed).
- **Related defect bugs:** ADO **1665527** (SilverBow 24-00957591 — mass postpones after importing ~1000 gas meters; span-edit + auto-edit contract-hour-9/TL interaction; rolled fine on Dev branch), **1651048** (Western Midstream 24-00946817 — TQ+CFX dual-fed meters postponing), **1640891** (always-postponing meters w/ text-file-fed data gaps), **1572896** (Tallgrass 22-00875962). Rollup Queue **Ignore** button only hides Postponed records (UI defect ADO **1653003**; `fc_meter_rollup_queue.rolled_up = 'I'`; actual removal = DELETE on FC_METER_ROLLUP_QUEUE).
- SF 24-00979515: client-side first step is the **Rollup queue cleanup script** — ask for it when postpones persist (also SF 26-01094275 "Meter Rollup service queue cleanup (QCLOUD)").

### 6.3 Rollup logic defects (fixed builds)
- **Analysis not rolled when last record of day is 0 flow:** daily analysis left 0 even though 23 records have data; manual requeue corrects. `CONFIRMED` fixed in 10.8.0 DEV (PR-14188), 10.7.0.0 (PR-14417), 10.6.0.7 (PR-14191), 10.5.0.20 (PR-14190) — PR-#### are FLOWCAL problem-report numbers from the SF resolution, `INFERRED` vs release notes. (SF 24-00949117.)
- **1st day of month Incomplete for Time Trails daily meters:** known product-backlog item, workaround exists (SF 25-01059906 — still open in backlog as of case close).
- **Location rollup direction data:** location failing/postponing month rollup was fixed by re-assigning directions to location entries (SF 26-01119203, FC 10.6.0.13). Composition not showing on location rollups → config (SF 25-01004825).
- **Rollup service crash RCA:** rollup services crashing, restart recovered; RCA tracked in the ADO attached to SF 25-01047514 (Software Defect); crash+restart also SF 25-01043643 (Golden Pass).

### 6.4 Tablespace exhaustion stops rollups/TQ (Oracle)
- **Signature:** Rollups or TQ halt; logs/db show `ORA-01653: unable to extend table FCOWNER.FC_FFMTR_HOURLY ... in tablespace FC_ROLLUPS_FFMTRHLY_TS` (or FC_METER_ANALYSIS in FC_MAIN_TS, fc_meter_periodic_values in FC_MAIN_MPER_TS).
- **Fix:** DBA extends the tablespace / adds datafile; restart services. Not a product defect; recurring fast growth → review partitioning/purge strategy.
- **Anchors:** SF 26-01079753 (Application Configuration), 22-00633005 (FCSRVTRANS/FC_METER_ANALYSIS), 23-00889118 (Location rollups stopped), 23-00902929 / 22-00625918 (FC_FFMTR_HOURLY imports).

## 7. Cluster E — GQ / Analysis apply queue (FcSrvGQTrans) & GQ rollups

### 7.1 "Unprocessed Analysis Apply" backlog — throughput/config
- **Signature:** Hundreds to 10K+ meters sitting in the Unprocessed Analysis Apply Service Queue; analyses visible in GQ Source but not applied to Volume Editor data; month-end blocked.
- **Fix recipe:** Confirm FcSrvGQTrans/FcGqTrans is installed and running (SF 25-01040936); **scale horizontally — adding 7 more FcSrvGQTrans instances cleared a 10,028-meter backlog quickly** (`CONFIRMED` SF 26-01103970, post-upgrade); also SF 25-01055681 (PRD backlog, Application Configuration).
- **Note:** after a version upgrade a slower apply rate has been reported with no confirmed defect — treat as capacity/config first.

### 7.2 Analysis apply defect on 10.8.0.5
- **Signature:** On import of current gas sources, entries stack in Unprocessed Analysis Apply with "buffering logs"; analyses show in GQ Source, don't apply.
- **Fix:** `CONFIRMED` FC defect on 10.8.0.5, fixed **10.8.0.9** (SF 26-01115461) — same 10.8 StringCopy release train as §6.1.

### 7.3 GQ Rollup service hang with big pending queue
- **Signature:** GQ (source analysis) rollup service hangs, ~500K records pending.
- **Fix:** `CONFIRMED` "fixed in 10.5.0.13 and ported to dev and 10.6" (SF 24-00971722, Software Defect). On-hold records in the GQ Analysis Rollup queue can be removed with SQL by support (SF 25-01055810).

### 7.4 GQ-apply calculation defects (data written wrong by the service)
- FcSrvGQTrans applying analyses has produced wrong PPA arithmetic historically — delta PPA missing from Adjusted Total Volume/Energy (ADO **1430767** PORT 10.2.0.18*, **1443673** PORT Dev z10.4.1, **1443674** PORT 10.4.0.1 — all Closed = `INFERRED` fixed in those trains), Total Adj Volume doubled on 2nd PPA (ADO Task **1696294**, Closed investigation), Std Volume incorrect on 2nd PPA (ADO **1702381**, EnLink 24-00993074, New), energy recalculated despite "don't recalc energy" GQ assignment (ADO **1699895**, New). If a client disputes post-apply volumes/energy, check these before blaming client edits.

## 8. Cluster F — Auto Estimate service

### 8.1 Service running but no estimates / not working
- Check in order: (1) **License** — CrypKey site key transfer resolved an "urgent, not creating estimated volume records" outage after a server loss (SF 25-01011146); (2) **Install** — service present in this env? (SF 24-00995466); (3) **Meter config** — Auto Estimate tab/settings on the meter (SF 26-01089191, 25-01028845, 25-00998052; Line Pack Fill meters have no Auto Estimate tab by design, SF 24-00961754); (4) **Version defect** — Liquids auto estimates broken in 10.5.0.1 DEV env (SF 23-00914558, Software Defect).

### 8.2 Auto Estimate data fighting real data
- **Pulses removed/revised on current data when Auto Estimate enabled:** `CONFIRMED` bug "originated from enabling the autoestimate setting", fixed **FC 10.6.0.7** (SF 25-01024811).
- **Import doesn't replace auto-estimated data (liquids text import):** behavior/priority question — Training (SF 24-00982859); "No Original Record when importing over AutoEstimate" (SF 24-00976894).
- **FCSRV making unsolicited daily meter data edits** (large volumes of system edits ~every 24h, even on inactive meters importing zeroes): `CONFIRMED` defect introduced in 10.5.0.17, fixed **10.5.0.20** (released 6/25/2025) (SF 25-01027967).

---

## Known ADO items (org `QuorumSoftware`)

Title convention: `(DEV)` / `(R1080* PORT)` / `(R1090 PORT)` suffixes = same defect ported per release branch. Fixed-in builds are `INFERRED` from tags/case text unless noted.

| ADO ID | Type/State | Title (abridged) | Cluster |
|---|---|---|---|
| 1811928 | Bug/Closed | Postponed Queues due to Destination buffer too small! (R1080* PORT) — tags 10.8.0.9, 10.8 StringCopy | §6.1 |
| 1819169 / 1819170 | Bug/Closed | Same, R1090 PORT / DEV | §6.1 |
| 1819152 | Bug/Closed | Buffer overflow error in volume editor (10.8.0.5) | §6.1 |
| 1808959 / 1820422 | Bug/Closed | Error closing meter data / viewing volumetric data 10.8.0.5 (PORT/DEV) | §6.1 |
| 1796147 | Bug | CFX files importing incorrect Meter Characteristics User Fields (R1080* PORT) | §6.1 |
| 1849624 | RCA/New | Import CFX crash, Set_user_field_s15 truncation garbage (10.10.0.0) | §6.1 |
| 1792011 | Bug/Closed | FLOWCAL 10.8.0.4 upgrade error (GPMCalculationCorrection.exe truncation) | §6.1 |
| 1837701 | Cloud Req/Closed | 26-01112398 CFL — clear bad user fields in fc_meter_characteristic (script) | §6.1 |
| 1839078 | Req/Closed | 10.8.0.9 manual regression & AT run (verifies 1819152/1808959/1811928) | §6.1 |
| 1868173 | Bug/New | TQ crashes (CLR 26-01124783) | §5.1 |
| 1773284 | Bug/New | TQ is crashing on snapshot record (CLR 25-01062128) | §5.1 |
| 1685148 / 1802507 | Bug/New | TQ service crashing on AGA-2013 data (crashes in 10.5.0.16) | §5.2 |
| 1549450 / 1563276 | Bug/Closed | Gas turbine meter crashes when T and P not provided (Dev* / R1040 PORT) | §5.3 |
| 1615044 | Bug/Closed | 23-00912180 TQ service keeps crashing (1992 Gross 2 out-of-range) | §5.4 |
| 1745472 | Bug/Proposed | Transaction Queue Service keeps stopping after restarting (neg. atm pressure) | §5 |
| 1797611 | Bug/New | TQ does not process certain records (susp. transaction_type 10 UFM) | §5.6 |
| 1624504 | Bug/Closed-Dup | TQ crashes trying to process events (CLR 23-00923429) | §5 |
| 1665527 | Bug/New | 24-00957591 SBW Gas meter rollups failing (mass postpone) | §6.2 |
| 1651048 | Bug/Closed | Meter Rollups postponing (WES 24-00946817) | §6.2 |
| 1613415 | Bug/Closed | Meters "Postponed" in Meter Rollup Queue (flow_duration garbage) | §6.2 |
| 1640891 / 1572896 | Bug/Closed | Meters postponed (data gaps / Tallgrass 22-00875962) | §6.2 |
| 1653003 | Bug/New | Rollup Queue — Ignore button (fc_meter_rollup_queue.rolled_up='I') | §6.2 |
| 1430767 / 1443673 / 1443674 | Bug/Closed | Delta PPA missing in adjusted totals on GQ apply (ports 10.2.0.18*/Dev/10.4.0.1) | §7.4 |
| 1696294 | Task/Closed | Total Adj Volume doubled on 2nd PPA from fcsrvgqtrans | §7.4 |
| 1702381 | Bug/New | Standard volume incorrect on PPA (EnLink 24-00993074) | §7.4 |
| 1699895 | Bug/New | Energy recalculated despite no-recalc-energy option (fc_gq_apply_queue repro) | §7.4 |

## Diagnostic SQL (from ADO repro steps / case resolutions — Oracle FLOWCAL schema `FCOWNER`; run read-only first; UPDATE/DELETE only with client approval. Env assumption: these were written against engineering DEV copies of client DBs.)

```sql
-- TQ: what's stuck and why (backlog snapshot)
SELECT transaction_type, unavailable, COUNT(*)
FROM fc_transaction_queue
GROUP BY transaction_type, unavailable
ORDER BY 1, 2;

-- TQ: park a poison record set (verbatim convention from ADO 1745472)
UPDATE fc_transaction_queue SET unavailable = 999
 WHERE source_id = '<METER_ID>' AND unavailable = 0
   AND write_date > TO_DATE('<MM/DD/YYYY HH24:MI:SS>','MM/DD/YYYY HH24:MI:SS');
COMMIT;

-- TQ: requeue records for reprocessing (verbatim from ADO 1797611)
UPDATE fc_transaction_queue SET unavailable = 0
 WHERE source_id = '<METER_ID>'
   AND effective_date >= TO_DATE('<start>','MM/DD/YYYY HH24:MI:SS')
   AND effective_date <  TO_DATE('<end>','MM/DD/YYYY HH24:MI:SS');
COMMIT;

-- §5.1 orphan check: type-4 (meter characteristic edit) rows lacking snapshot counterpart
-- (a full script is attached to SF 26-01086935 — request it from the case before hand-rolling)
SELECT source_id, effective_date, COUNT(*)
FROM fc_transaction_queue
WHERE transaction_type = 4
GROUP BY source_id, effective_date;

-- Rollup queue: see ignored/postponed state (ADO 1653003)
SELECT rolled_up, COUNT(*) FROM fc_meter_rollup_queue GROUP BY rolled_up;

-- GQ apply: manually queue a source re-apply (verbatim from ADO 1699895 repro)
INSERT INTO fc_gq_apply_queue
  (gqsource_index, start_time_stamp, end_time_stamp, start_date, end_date,
   gms_date, status, username, source)
VALUES ((SELECT gqsource_index FROM fc_gq_source WHERE gqsource_number = '<SRC>'),
        fc_timestamp('<start>'), fc_timestamp('<end>'), '<start>', '<end>',
        SYSDATE, 'N', '<USER>', 'I');
COMMIT;

-- §6.1 corrupted user fields scan (cleanup script itself lives on WI 1837701)
SELECT meter_id, user_field_s15
FROM fc_meter_characteristic
WHERE LENGTHB(user_field_s15) > 20;  -- USER_FIELD_* are VARCHAR2(20 BYTE)
```

## Expected-Behavior FAQ

- **"Why was my list/meter closed by FCSRV?"** — The close services (FcSrvCloseData/FcSrvLcnCloseData) act under the FCSRV account per the **Schedule Close Dates Editor**; system-initiated closes show FCSRV as the user. Not a defect (SF 26-01107895, 25-01007145 — both Training/No Action).
- **"FCSRV made edits to meter data"** — analysis apply / auto estimate / PPA services legitimately write revisions attributed to FCSRV. Only the 10.5.0.17-specific unsolicited daily-edit storm was a bug (fixed 10.5.0.20, SF 25-01027967) — check version before conceding a defect.
- **"Records sit in the rollup queue as Postponed after we Ignore them"** — Ignore only suppresses Postponed rows and the grid still shows them (ADO 1653003); permanent removal requires queue cleanup (support script).
- **TQ vs File Import** — moving from text-file FileImport to TransactionQueue feed is a supported config change, not a bug workaround (SF 25-01035440). TQ internals documentation may require an NDA (SF 26-01120941).
- **HCDP not calculating** — often just a stalled `FcSrvHCDPQueueProcessor`; restart first (SF 25-01016254).

## Escalation guidance

1. **Always collect first:** FLOWCAL version (exact 10.x.0.y), the service's own log (`_FC_SRV_*_LOG.LOG`), `_FC_DB_ERROR.LOG`, Windows Event Viewer entries, and queue screenshots (Service Queues / Rollup Viewer). Engineering repros require an **FcDataBoss** export of the affected meter(s) + queue SQL — request early (pattern in every ADO repro above; support FTP/`qddfcfs01` drop).
2. **Restart ladder:** single service restart → FCSRV account check → all-service restart (QCloud ticket if hosted). If a restart "fixes" it but it recurs, it's a poison record or leak — do not close, root-cause.
3. **Version match before code-level work:** check §Known-ADO table and release notes for the client's build; a large share of this cluster is already fixed in 10.5.0.20 / 10.6.0.7 / 10.8.0.2 / 10.8.0.9 / 10.8.0.10 / TI 3.17. Label any fixed-in claim `INFERRED` until verified in release notes.
4. **Escalate to Engineering (Measurement Maintenance)** with: databoss + SQL repro, log excerpts with the FcAssert/ORA text verbatim, and the matching ADO ID if it exists (open a new bug referencing the SF case number in the description, per the `Case Owner - {name}` + case-number convention).
5. **Data-correction scripts** (user-field cleanup, queue cleanup, on-hold removal) go through Cloud ops "Request Global Cloud Ops" items for hosted clients (pattern: WI 1837701) — never run destructive SQL directly on PRD.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
