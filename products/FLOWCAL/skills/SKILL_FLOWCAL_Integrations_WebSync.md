# SKILL — FLOWCAL Family: Integrations & WebSync (TESTit↔FLOWCAL, WebSync, eSuite/IP/QPTM chain)

> **Products:** FLOWCAL + TESTit + PROVEit (`Product_list__c IN ('FLOWCAL','TESTit','PROVEit')`).
> **Coverage plan group:** #11 (Integrations & WebSync) — ~730 family cases, ~150 actionable floor.
> **Sources:** Salesforce all-history mining (closed cases through 2026-09) + ADO org `QuorumSoftware`
> (`Quorum\North America\Measurement*`, `QuorumSoftware\Engineering\Measurement\Field Applications`, `\Maintenance`, `\SF Queue`, `myQuorum Cloud\Global Cloud Operations`). Mined 2026-09-02.
> **Auto-Bot skill — built by Aditya Bhagat.** Every root-cause claim cites SF case and/or ADO ids verbatim.

Three distinct pipes are conflated as "sync" by customers — identify the pipe FIRST:

| Pipe | Moves what | Moving parts |
|---|---|---|
| **A. WebSync** | Tech laptop ⇄ TESTit/PROVEit server | WebSync WebAPI + WebIDP (IIS/NetScaler), OKTA identity, `fa_user_identity` |
| **B. TESTit⇄FLOWCAL desktop integration** | Completed tasks/test reports/cal adjustments ⇄ FLOWCAL; lists & flow averages → TESTit | MSMQ message queues, DTC, databus share, subscription table, `FlowCal.FieldApplications.Integration.Service`, `FlowCal.Enterprise.Integration.Service`, List Polling Service, `FcSrvTESTitCalAdjApply.exe` |
| **C. FLOWCAL ⇄ eSuite / Integration Platform / QPTM (Xchange)** | Meters, volumes, samples/analyses downstream | IP/HEP events, eSuite queue, eSuite API service, MFC.* metadata |

## 1. Quick Triage

| Symptom / error text | Pipe | Likely cause | § |
|---|---|---|---|
| "WebSync Error - Unable to cast object of type 'System.String' to type 'System.Int64'" | A | Defect, fixed TESTit 3.18.0 (INFERRED) | §3.1 |
| WebSync completes but PK error on a DList (post-3.17 upgrade) | A | Open defect ADO 1769174 | §3.1 |
| WebSync crash tied to duplicate Schedule Entry | A | ADO 1743456 (Closed) | §3.1 |
| "WebSync ... stalls at Meter Source Analysis ... connection was forcibly closed by the remote host" | A | Timeout on oversized first sync | §3.1 |
| Failed syncs taking 4-6 hours | A | Schedule Entry form-name mismatch vs Task Explorer | §3.1 |
| WebSync "succeeds", zero new data, no errors | A | `fa_user_identity` ≠ OKTA `external_id` (e.g. stray space) | §3.2 |
| WebSync auth window never opens / OKTA group invisible | A | OKTA app/group config, NetScaler LBVS | §3.2 |
| Websynced tasks land as "Failed" integration status; manual File > Integration > Sync works | B | ADO 1807545 (Active defect) | §3.3 |
| "unhandled exception...failed to send message to address" in Task Explorer sync | B | MSMQ queue permissions / databus share ACL | §3.3 |
| Tasks not syncing to FLOWCAL at all after upgrade/migration | B | MSMQ not installed everywhere, DTC perms, endpoints, subscription table bloat, config flag | §3.3 |
| Task Explorer shows Failed but data IS in FLOWCAL | B | Status-only mismatch → SQL flip to Synced | §3.3 |
| Individual task Failed with characteristic/UOM detail | B | Bad characteristic data (e.g. DP Cut off UOM, pressure base units) — by design | §3.3 |
| TEST report revision not updating in FLOWCAL after sync | B | ADO 1822918 workaround script; fixed by upgrade | §3.3 |
| Calibration adjustments not applied in FLOWCAL | B | `FcSrvTESTitCalAdjApply.exe` service down/broken (ADO 1653223/1812249) | §3.3 |
| Dynamic List / new meter not appearing in TESTit | B | List Polling Service schedule/restart-job conflict; orphan republish events | §3.4 |
| Flow averages not reaching TESTit / integration service crashing | B | ADO 1789020, 1687515/1775815 (fixed R1060/R1080 line, INFERRED) | §3.4 |
| Meters/volumes/analyses missing in eSuite or QPTM | C | IP event stuck, eSuite queue stuck, meter subscription gap | §3.5 |
| "Arithmetic overflow error converting real to data type numeric" on PGAS/FLOWCAL→eSuite | C | Out-of-range GQ component (Ethane 1000) rejected by eSuite | §3.5 |
| FLOWCAL→eSuite sample/analysis failing on Int16 | C | Data type overflow; script fix | §3.5 |

## 2. Decision Tree

```
"Sync isn't working"
├─ Who initiates? Tech laptop → server?  = Pipe A (WebSync)
│   ├─ Error text present → §3.1 (match signature; String→Int64 = version gate 3.18)
│   └─ Silent no-op → §3.2 (identity mismatch: fa_user_identity vs OKTA whoami)
├─ TESTit server ⇄ FLOWCAL?              = Pipe B
│   ├─ EVERYTHING failing → §3.3 infra checklist (MSMQ→DTC→databus→endpoints→subscription→config flag)
│   ├─ SOME tasks failing → §3.3 data-level (characteristics/UOM; master meters & Cone Change never sync — by design)
│   ├─ Status wrong but data present → §3.3 SQL status flip
│   └─ Lists / flow averages inbound to TESTit → §3.4
└─ FLOWCAL → eSuite/IP/QPTM downstream?   = Pipe C → §3.5
     (order: service up? → event/queue stuck? → record-level data rejection?)
```

---

## 3. Symptom Clusters

### 3.1 WebSync failures with an error signature (Pipe A)

**Signatures & root causes (each anchored):**
1. `Unable to cast object of type 'System.String' to type 'System.Int64'` — product defect; resolution verbatim: "This fix will be in the upcoming TESTit 3.18.0 release." (SF 25-00996198, Software Defect). Fixed-in 3.18.0 = INFERRED.
2. **DList primary-key error** — after upgrade 3.16.2→3.17.1, tech syncs complete "except for a primary key error on a dlist. we deleted and purges, removed, created anew, but still the same error" (SF 25-01057677 description, no packaged fix). ADO **1769174** "25-01057677--TESTit 3.17 websync - DList PK Error" (Proposed/open). Treat as known open defect; workaround attempts (recreate DList) historically failed — escalate to Field Applications.
3. **Duplicate Schedule Entry crashes WebSync** — ADO **1743456** "25-01022751--Duplicate Schedule Entry Causing Web-Sync to Crash" (Closed). Check for duplicate schedule entries before retry.
4. `Exception Error occurred in WebSync: Unable to read data from the transport connection: An existing connection was forcibly closed by the remote host` stalling at **Meter Source Analysis** — timeout on a new install syncing a large source-analysis backlog. Resolution verbatim (SF 25-01012771): "The best workaround ... is to export a TIDX file that includes the same meter listed in the access list. Then, import that file into the TESTit desktop and attempt to sync again. This will significantly reduce the load on websync." Increasing the timeout only helps if the network is clean.
5. **Failed syncs taking 4-6 hours** — root cause: form-name mismatch. "We provided SQL scripts to update the Schedule Entry anywhere the form name was mismatched from the form name used in the Task Explorer." (SF 25-01032526).
6. **Parallel tasks not syncing (3.16.1.0)** — a broken page inside the task (Transmitter 1) blocked the task, and the Schedule Entry couldn't sync without its task (SF 24-00990592): fix the offending task page or update the Schedule Def.
7. `Error mapping types` (SF 25-01007816) and HTTP 500 from the WebSync API (SF 24-00940854, Software Defect) — server-side WebSync API fault: check WebAPI app-pool/.NET version, then escalate.

**Environment note:** TESTit 3.19+ WebSync needs a .NET upgrade on the app server (ADO 1855125 "[MOM] [UAT] [.NET Upgraded needed to restore WebSync for TESTit 3.19+ Functionality]"); MSMQ/queues are separate from WebSync — don't conflate pipes.

**Anchors:** SF 25-00996198, 25-01057677, 25-01012771, 25-01032526, 24-00990592, 25-01007816, 24-00940854, 26-01115147, 26-01112615; ADO 1769174, 1743456, 1855125, 1853889.

---

### 3.2 WebSync auth & silent no-op (OKTA / identity) (Pipe A)

**Signature.** Sync runs clean, "process ends without any errors", but nothing new arrives; or the OKTA auth window/groups misbehave.

**Root cause (CONFIRMED, SF 26-01083861 resolution verbatim):** "The username ... in the `fa_user_identity` table contained a space, which caused it to not match the `external_id` configured in the OKTA profile and the result from the whoami command. To resolve the issue, an update statement was executed in the `fa_user_identity` table. Additionally, the user was required to fully log out of TESTit in order to clear any session cookies before attempting to sync again."

**Fix recipe:**
1. Compare `fa_user_identity` username ⇄ OKTA profile `external_id` ⇄ `whoami` output; fix with an UPDATE (exact-match, no whitespace).
2. Full logout of TESTit (clears session cookies), then re-sync.
3. Access/RO-RW problems: verify OKTA group membership (`<Client>-PROVEit-RW-UAT`-style naming) and that WebSync user access lists include the meters (SF 25-01062469, 25-01062558).
4. Infra layer: NetScaler LBVS for TESTit WebSync WebAPI/WebIDP, firewall rules (ADO 1862339/1862340 pattern), auth window not opening (ADO 1853889).

**Anchors:** SF 26-01083861, 25-01062469, 25-01062558, 26-01105101; ADO 1867122, 1853889, 1777234.

---

### 3.3 TESTit ⇄ FLOWCAL desktop integration (MSMQ / DTC / databus / services) (Pipe B)

**Signature.** Completed tasks/test reports don't appear in FLOWCAL; Task Explorer statuses Failed; "Enable for TESTit" not working; whole integration dead after an upgrade or server move.

**Infra checklist (root causes CONFIRMED in case resolutions — run in this order):**
1. **MSMQ everywhere.** "We installed the message queues on the citrix server. These need to be installed anywhere TESTit is pointing to even if TESTit is not installed on the server." (SF 25-01054463). After 3.19 upgrade: "resolved the issue by installing the Message Queues on every single server. They also had to make some component exclusions on the SQL Server Database [antivirus]." (SF 26-01110812).
2. **Queue permissions.** "unhandled exception...failed to send message to address" → grant the AD groups pick/send/receive on the TESTit AND FLOWCAL queues, and add them to the databus shared folder (SF 26-01088590).
3. **DTC permissions** on both servers (SF 25-01054463 step 4).
4. **Endpoints + databus path** correct on both sides (SF 25-01054463 step 2).
5. **Subscription table hygiene** — "Cleaning the subscription table because it had 76 records instead of 38. This fixed the FLOWCAL side sync." (SF 25-01054463 step 1).
6. **Config flag** — integration must be enabled in `TESTit.exe.config` (SF 25-01054463 step 5).
7. **Queue drain** — clean audit + error queues, purge dead-letter queues, restart integration services / app server (SF 26-01092801; ADO 1797619 incident, ADO 1796019 "restart FlowCal.Enterprise.Integration.Service for FC_SUPP").

**Data-level failures (by design, not defects):**
- A task shows **Failed** when a characteristic fails processing — e.g. "the DP Cut off UOM ... the system is designed to display the task as Failed in the Task Explorer. This is the intended behavior" (SF 26-01101692). Another: "Pressure base units was missing." (SF 26-01109077).
- **Master Meter tasks never sync** — "the master meters do not exist in Flowcal. They only exist in TESTit." And Cone Change Reports don't sync — "Only the Meter Inspection Report will sync to Flowcal." (SF 25-01041439).

**Status-only mismatches:** tasks already integrated but stuck "Failed" → support "provided SQL to the customer to set the 'Failed' statuses for the four tasks to 'Synced'." (SF 25-01015747). WebSync-origin tasks landing Failed then integrating fine manually (File > Integration > Sync) = ADO **1807545** "25-01017245 - Websync tasks fail to integrate with FC" (Active). Older tasks never synced = ADO **1715141** (Proposed).

**Known service/report defects:**
- **TEST report revision not updated in FLOWCAL on sync** — workaround script deployed in TESTit DB (SF 26-01086745); same workaround reapplied for SF 26-01121144 ("customer needs to upgrade to TESTit to have this issue fixed"); ADO **1822918** tracked the ops-side fix; sibling sync case SF 26-01113240 fixed via "the workaround under the ADO 1822918 - Case 26-01106622".
- **Calibration adjustments not applied** — `FcSrvTESTitCalAdjApply.exe service does not work`: ADO **1653223** (New, Maintenance) / **1812249** (Closed, Measurement). Matches SF 26-01106284 "Calibration adjustment not applied due to unknown issues - Integration Issues".
- **Exceptions not generated for characteristic mismatches** — ADO **1635433** (New) / **1812248** (Closed) "Test Reports not generating exceptions for mismatches on characteristics and test report"; ADO **1865837** "TESTit Exceptions Not Generating" (New).
- **Meter Editor hangs after save ×2 when TI integration service unreachable** — ADO **1813839** (Proposed).
- **Sync-status enum loss in new SaaS UI** — ADO **1805160** (Closed).

**Anchors:** SF 25-01054463, 26-01110812, 26-01088590, 26-01092801, 26-01101692, 26-01109077, 25-01041439, 25-01015747, 25-01017245, 26-01086745, 26-01121144, 26-01113240, 26-01106284, 25-01029467; ADO 1796019, 1797619, 1822918, 1807545, 1715141, 1653223, 1812249, 1635433, 1812248, 1865837, 1813839, 1805160, 1735859.

---

### 3.4 Dynamic lists & flow averages into TESTit (Pipe B inbound)

**Signature.** New meter added in FLOWCAL doesn't show in TESTit lists; list members appear then vanish; flow averages stale on laptops.

**Root causes (anchored):**
1. **List Polling Service scheduling conflicts.** Resolution verbatim (SF 26-01105446): "We worked on the TESTit Integration Services and message queues ... We disabled the Windows Task Job that was set up to restart the service every two hours. We configured the service to run every 12 hours in the Service Config file." An external restart job fighting the service config = missed polls.
2. **Orphan republish events removing meters.** Deep log analysis (SF 26-01095077): publish events in `FlowCal.Enterprise.Integration.List.PollingService-*.jsonl` matched receives in `FlowCal.FieldApplications.Integration.Service-*.jsonl` within ms — infra healthy — but extra update events on a ~6-hour cadence rewrote `FC_WATTENBERG_ALL_ACTIVE` without the meters, pointing at "another process, service, environment, or synchronization mechanism ... refreshing or republishing the list independently." Hunt for second environments/services subscribed to the same list.
3. **"Enable for TESTit" flag not propagating** — queue backlog; fixed by draining audit/error/dead-letter queues + service restart (SF 26-01092801, ADO 1796019).
4. **Flow averages crash/sync defects** — ADO **1789020** "FlowCal.FieldApplications.Integration.Service crashing due to Flow Averages (R1060 Logging)" (Closed); ADO **1687515/1775815** "Flow Averages to TESTit (R1080* PORT)/(DEV)" (Closed; INFERRED fixed in the R10.60/R10.80 maintenance line); ADO **1736018/1812254** "Syncing FlowAverages happens with open data even though Closed option specified". Laptop-staleness cases: SF 25-01048563, 26-01065667, 25-01043001, 25-01049315.

**Anchors:** SF 26-01105446, 26-01095077, 26-01092801, 25-01048563, 26-01065667, 25-01043001, 25-01049315, 25-01009870 (new meter missing in Scheduler Editor — Software Defect); ADO 1789020, 1687515, 1775815, 1736018, 1812254, 1796019.

---

### 3.5 FLOWCAL → eSuite / Integration Platform / QPTM (Xchange) (Pipe C)

**Signature.** Meters or volume/analysis records missing downstream (eSuite, TIPS, QPTM); IP events stuck; comparison reports mismatch.

**Root causes & fixes (anchored):**
1. **Record-level data rejection** — eSuite enforces ranges/types FLOWCAL doesn't:
   - "Arithmetic overflow error converting real to data type numeric" — "caused by a station/meter that had an Ethane value on the GQ source of 1000. ESUITE will not allow this value. Once the client found the station and removed this GQ everything starting working again." (SF 25-01034944).
   - Sample/analysis failing on **Int16** — fixed by a support script (SF 25-01046743).
   - Invalid flowtime on volume records (SF 25-01020045).
   Recipe: read the IP error payload, isolate the offending meter/record, correct the source data in FLOWCAL, let the event replay.
2. **Stuck queues/events** — eSuite queue id stuck >1 day → ops kill/restart (SF 25-01024512); "Events Stuck or not processed in HEP Integration Platform" (SF 25-01018946); "Integration Platform StoreEntity Errors" (SF 25-00995902).
3. **Service down** — "Esuite API service is down ... Services are back online. Events are now successfully processed" (SF 25-01016267); whole IP link down (SF 25-01000924 "IP FlowCal to ESuite/TIPS is down").
4. **Meter-level publish gaps** — single meter not migrating while others flow: SF 26-01121644 (ADO raised; "started working" after fix — republish), 26-01117242 (meter not moving to eSuite AND QPTM — Deployment Issue), 23-00924504 (missing meter), 25-01053419 (re-publish Meterheader after eSuite DB changes). Recipe: verify meter subscription/publish state, then republish the meter header.
5. **Spurious events** — FLOWCAL sent events to Enterprise Integration even when meter close FAILED — ADO **1774093** (Closed, Engineering\Measurement\Maintenance): explains downstream volumes that "arrived" for failed closes.

**Cross-reference:** `FcTextFileExchange.dll` export failures ("Unable to access the export dll export\FCTextFileExchange.dll", SF 26-01103514, 26-01101971, 26-01119134) are the file-export path, not IP — route to the Imports/Reports skills.

**Anchors:** SF 25-01034944, 25-01046743, 25-01020045, 25-01024512, 25-01018946, 25-00995902, 25-01016267, 25-01000924, 26-01121644, 26-01117242, 23-00924504, 25-01053419, 26-01100159, 24-00962088; ADO 1774093.

---

## 4. Known ADO items (Integrations & WebSync)

| ADO id | Title (verbatim) | State | Area path |
|---|---|---|---|
| 1807545 | 25-01017245 - Websync tasks fail to integrate with FC | Active | QuorumSoftware\Engineering\Measurement\Field Applications |
| 1769174 | 25-01057677--TESTit 3.17 websync - DList PK Error | Proposed | ...\Field Applications |
| 1743456 | 25-01022751--Duplicate Schedule Entry Causing Web-Sync to Crash | Closed | ...\Field Applications |
| 1715141 | TESTit Older Tasks Not Synced to FLOWCAL - PENDING PRODUCTS (3/13/26) | Proposed | ...\SF Queue |
| 1735859 | 25-01023210--Western Midstream - FlowCal/TestIt Integration Services Issues | Active | ...\Field Applications |
| 1774705 | TESTit Integration issue - Test report not loading | Proposed | ...\Field Applications |
| 1789020 | FlowCal.FieldApplications.Integration.Service crashing due to Flow Averages (R1060 Logging) | Closed | ...\Maintenance |
| 1774093 | FLOWCAL sending events to Enterprise Integration when meter close fails (DEV) | Closed | ...\Maintenance |
| 1813839 | Meter Editor hangs after attempting to save twice when unable to communicate with TI integration service | Proposed | ...\Enhancements\Team 4 |
| 1653223 / 1812249 | FcSrvTESTitCalAdjApply.exe service does not work | New / Closed | Quorum\NA\Measurement\Maintenance / Measurement |
| 1635433 / 1812248 | Test Reports not generating exceptions for mismatches on characteristics and test report | New / Closed | Maintenance / Measurement |
| 1812255 | 25-01025859--FourPoint TEST task sync to FLOWCAL fails and add manual labor | New | Measurement |
| 1865837 | TESTit Exceptions Not Generating - PENDING SUPPORT (8/28/2026) | New | Measurement |
| 1822918 | FC FRL PRD - Four point Resources - Customer needs helps to update some TEST report revisions in FLOWCAL | Closed | myQuorum Cloud\Global Cloud Operations\Incidents |
| 1796019 | restart FlowCal.Enterprise.Integration.Service for FC_SUPP | Closed | myQuorum Cloud\...\Incidents\AppOwners |
| 1797619 | 26-01092801 - SUP - PRD - Integration is not working. | Closed | myQuorum Cloud\...\Incidents |

All fixed-in builds INFERRED unless release-notes-confirmed. Bugs cite the source SF case in the title/description (`2x-01xxxxxx`) — use as join key.

## 5. Diagnostic SQL (templates; FLOWCAL/TESTit DB objects; label every execution — NOT YET RUN unless stated)

```sql
-- A. WebSync silent no-op: identity mismatch (pattern CONFIRMED in SF 26-01083861)
SELECT * FROM fa_user_identity WHERE username LIKE '% %' OR username <> LTRIM(RTRIM(username));
-- Fix pattern: UPDATE fa_user_identity SET username = '<okta external_id>' WHERE user_id = :id; then full TESTit logout.

-- B. Task Explorer status stuck 'Failed' though integrated (pattern CONFIRMED in SF 25-01015747)
--    Locate the task sync-status column in the FA task tables and flip Failed→Synced for verified task ids only.

-- C. 4-6h WebSync: Schedule Entry form-name mismatch (pattern CONFIRMED in SF 25-01032526)
--    Compare Schedule Entry form name vs the form name used in Task Explorer; update mismatches.

-- D. TIDX task-attachment import failures
SELECT * FROM FA_ATTACHMENT_TASK_REL WHERE task_id = :task_id;   -- null file refs (SF 26-01097299)
```
Env assumptions: TESTit field-apps schema (SQL Server or Oracle), `fa_*`/`FA_*` object naming. Exact column names must be verified against the client build before running — client-PRD data-state claims stay INFERRED.

## 6. Expected-Behavior FAQ

- **"Master meter tasks never reach FLOWCAL."** Correct — master meters exist only in TESTit (SF 25-01041439).
- **"Cone Change Report didn't sync."** Only the Meter Inspection Report syncs to FLOWCAL (SF 25-01041439).
- **"A task failed to integrate and shows Failed."** When a characteristic fails processing (bad/missing UOM), Failed status is intended behavior; fix the data, resync (SF 26-01101692, 26-01109077).
- **"Do queues need to be on servers without TESTit installed?"** Yes — MSMQ must exist anywhere TESTit points, including Citrix servers (SF 25-01054463).
- **"After 3.19, sync broke."** Expect: MSMQ on every server, antivirus exclusions for SQL components, .NET upgrade for WebSync 3.19+ (SF 26-01110812; ADO 1855125).

## 7. Escalation guidance

- Pipe A signature matching ADO 1769174 (DList PK) or 1807545 (Failed-status websync tasks): link the case to the existing bug — do not file duplicates; both were open as of 2026-09-02.
- Pipe B total outage in QCloud-hosted envs: raise Global Cloud Ops incident (pattern: ADO 1796019/1797619) for service restarts and queue purges; support does not restart hosted services directly.
- Pipe C stuck events/queues: ops kill/replay (SF 25-01024512) — capture queue id and event ids first for the RCA.
- New defect filing: Bug in `Quorum\North America\Measurement` (support triage) with SF case number in title (`2x-01xxxxxx--<summary>` convention, e.g. ADO 1812255); Engineering copies land in `QuorumSoftware\Engineering\Measurement\*` with `(DEV)`/`(R#### PORT)` suffix pairs.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
