# SKILL — QPEC Batch-Engine / Scheduler Operations Runbook (SHARED)

> **Scope:** CROSS-PRODUCT. QPEC is the batch process-execution engine behind every Quorum product Auto-Bot covers — QPTM, TIPS, QCFS, QCA, QRA, QDO (plus eSuite platform). Index this skill into **every** product KB.
> **Provenance:** Mined 2026-09-02 from 175 closed SF cases (all history, 4 upstream product literals: `My Quorum Financial Accounting`, `My Quorum Cost Accounting`, `My Quorum Revenue Accounting`, `My Quorum Division Order`; Subject `%QPEC%` / `%stuck%`), ADO work-item search (`QPEC crash`, org QuorumSoftware), and consolidation of QPEC content already documented in: `products/QCA/skills/SKILL_QCA_Joint_Interest_Billing.md` §4, `products/QCA/skills/SKILL_QCA_LOS_Reporting.md` §4, `products/QCA/skills/SKILL_QCA_Platform_Workflow_Integration.md` §10, `products/QCFS/skills/SKILL_QCFS_General_Ledger.md` §4, `products/QCFS/skills/SKILL_QCFS_Import_Export_Integration.md` §9, `products/QCFS/skills/SKILL_ADO_QCFS_AR_GL_BankRecon.md`, `products/QRA/skills/SKILL_QRA_Platform_Integration_Security.md` §4/§11/§12, `products/QRA/skills/SKILL_QRA_Prior_Period_Adjustments.md` §13, `products/QRA/skills/SKILL_ADO_QRA_Tax_1099_Regulatory.md` §4, `products/QDO/skills/SKILL_ADO_SHARED_eSuite_V2UI_Workflow_Performance.md` §3, `products/QPTM/skills/SKILL_ADO_QPTM_Nominations_EDI.md`, `products/QPTM/skills/SKILL_ADO_QPTM_Allocations_PPA_Imbalance.md`, `products/TIPS/skills/SKILL_ADO_TIPS_Batch_Processing_SystemConfig_Env.md`, `products/TIPS/skills/SKILL_ADO_TIPS_Measurement_VolumeImport_FlowCal.md`, `.claude/agents/batch-debugger.md`, and the `products/*/PRODUCT.md` vocabulary tables.
> Closes the **PARTIAL GAP: QPEC engine/scheduler ops runbook** flagged in `products/QCFS/knowledge/QCFS_Coverage_Plan.md` (group 8).
> PII redacted (individual names removed; clients referenced by env/short code only).
> *Built by Auto-Bot — the L4 issue solver by Aditya Bhagat.*

---

## 0. Quick Triage

| Symptom (verbatim-ish) | Most likely cause | Go to |
|---|---|---|
| "Batch stuck in Post Pending" / "X never posts" | POSTWKFL drainer not running, stale lock, or a *valid* wait (future Date-to-Post, period not open) | §3 + §9 FAQ |
| "Processes stuck in Queued for Processing" / "jobs not picked up" | QPEC service down/STPER, scheduler off, or scheduler pointed at a dead app server (`APP_SERVER_GRP_CD`) | §3 steps 2–3 |
| "Initialize Function Failed. Duplicate process found" | Prior PQID of the same process still holds the lock | §3 step 5 (26-01107081) |
| Process stuck in **PRC** after a cancel/crash/outage | Status row orphaned — needs cancel/clean or reset script (SXL/SPE) | §3 step 6 |
| "Restart QPECs ASAP" / engines down / "QPEC SYSTEM ERROR" | Service crash, OOM crash-loop, or cloud outage | §4 |
| "Timeout exceeded…" / "Query timeout expired" / step dies at exactly 1 hr — **right after a patch** | `CommandTimeout` in `QPEC.ini`/`QPEC.exe.config` reset by the patch | §5 |
| "Unable to establish a connection with any endpoint" | Endpoint broker / MT plumbing, not business logic | §4 signature table |
| Scheduler-run job fails but the SAME job succeeds manually | Scheduler identity config (SM093 draft/approve/post exclusivity) or DEBUG/impersonation | §3 step 8 |
| Segregated process "completes" but downstream data never appears | Seg child never spawned (packaging/csproj) or drainer silently stopped | §6 + §7 (#1442338, #1839889) |

**Golden rule (all products):** get the **PQID + the first ERROR line + the environment name** before doing anything else. First error is the cause; later errors are cascade (`products/*/PRODUCT.md`: "Batch triage: PQID → first ERROR → SQLID/ORA code").

---

## 1. What QPEC is

- **QPEC** = Quorum's batch **process-execution engine**. Every product ships its own binary: `Quorum.<Product>.Application.QPEC` (TIPS, QPTM, PGAS, QLNG, QDOD, ESuite, QCM variants enumerated in ADO #1567548; client-custom e.g. `NRM.TIPS.Application.QPEC` in #1442338). "QPECS" = the fleet of QPEC service instances on the QPEC/MT servers.
- **System Manager** supervises the QPEC services: shows engine state (`STPER` = stopped-with-error; `KILL` state rows), performs **graceful restarts**, and periodically rescues crashed processes (§4). Known supervisor quirks: restarts a QPEC twice (#1545342), and can falsely flag healthy QPECs as "Stopped Unexpectedly" after a memory-limit restart (#1774745, platform dependency #1780230).
- **QPEC_SCHEDULER** = the scheduler identity that launches scheduled jobs. Scheduled entries carry an `APP_SERVER_GRP_CD` (which server group runs the job) — a wrong/stale value strands jobs in Queued (26-01117615).
- **Two batch families** (per `.claude/agents/batch-debugger.md`):
  - **NORMAL** — scheduled or user-launched runs (PANIGHTLY, ALALLOCATE, JIB cycles, CW*, imports/exports, QRPTLAUNCH/QEMAIL). Failure mode: the run errors → PQID triage.
  - **SEGREGATED** — continuous drainers on short cycles: `POSTWKFL` (Post Pending → Posted, ~5-min cycle, `QSegregatedPostWkflBalanceUpdate.cs`), `PSTWKSPLT` (splitter variant), `BKRVNU` (QRA revenue distribution behind VL100), `GMASLDVOLS` (TIPS volume load). Failure mode: records **stuck in an intermediate status** because the drainer stopped/crashed/timed out — users report "X never posts", not "job failed". Logs: `qtrace.<product>.QPEC.*.segregated.log`.
- **Sizing levers** (Cloud Ops-owned): instances-per-QPEC (maintenance reset it to a default of 4 at EQC; raised back to 20 to match PRD — 25-01042000; raised to 8 for a UAT — 26-01096543; SAP MT QPEC showing a permanent `KILL` row = instance count didn't match the number of MTs — 24-00986198), per-instance **memory limit** (example fleet limit 750 MB, exceeded at 787–822 MB in ADO #1765732), server CPU/RAM (24-00950679, 25-01026684).

---

## 2. Triage decision tree

```
Batch/process problem mentioning QPEC / stuck / not processing
│
├─ Is ANYTHING processing on the environment?
│   ├─ NO — whole env dead, logins failing, "services down"        → §4 crash/outage (Cloud Ops incident)
│   └─ YES — only some jobs affected                                → continue
│
├─ Job runs but DIES WITH AN ERROR
│   ├─ "Timeout expired" / dies ~1 hr / right after a patch         → §5 timeout family
│   ├─ Business-rule error text (period, lock, duplicate, JIB month)→ §3 steps 4–8 + §9 FAQ
│   └─ "QPEC SYSTEM ERROR" / no log captured at all                 → §4 (instance crash mid-run)
│
├─ Job NEVER STARTS (Queued forever)
│   └─ §3 steps 2–3 (service state, scheduler on?, APP_SERVER_GRP_CD, locks)
│
├─ Job shows PROCESSING (PRC) forever
│   ├─ Actually still working (huge volume)?                        → §9 FAQ — verify before killing
│   └─ Orphaned after crash/cancel/outage                           → §3 step 6 (cancel/clean/reset)
│
└─ Segregated drainer symptom ("X stuck in Post Pending", "never posted")
    └─ §3 stuck-queue runbook end-to-end
```

---

## 3. Stuck-queue runbook (Queued forever / Post Pending / PRC)

Work the steps in order — each is cheaper than the next. Evidence anchors are verbatim SF case numbers.

**1. Prove it is actually stuck (do NOT restart yet).**
Long ≠ stuck: a POSTWKFL validating batches of 48,890 / 73,695 / 72,724 GL records finished the same day (25-01035751); an upgrade-week run at ~4 min/batch across 376 batches was healthy (25-01034243). Check rows-processed movement / recent status-change before touching anything. Also rule out *designed* waits: future **Date-to-Post** (25-01022292 — DATETOPOST May 31; 25-01027244; 26-01065520; 25-01017149), accounting period not open in SM006 (25-01051259), "JIB has already been processed for this month" (25-01019990).

**2. Service health.**
- Is the product's QPEC service actually up? A scheduler service in **`stper` state** silently stops all scheduled processing — starting the service fixed it (26-01086774, env `EQCU_HD_UBT17`, "UPS SCH … was in stper state").
- Is the **scheduler turned on**? All scheduled QPEC jobs failing to kick off = scheduler down; Cloud Ops turns it back on (24-00984242).
- QPEC group "in a failed state" → request Cloud Ops **graceful restart**, then verify processes are being picked up again (25-01043752; sister ticket 25-01043896).
- CAUTION: services can show "up and registered" in System Manager and still not process (post-maintenance condition, ADO #1850176 — not caught by STPER alerts).

**3. Scheduler configuration.**
- `APP_SERVER_GRP_CD` on the scheduled entry pointing at a server that no longer exists post-upgrade → POSTWKFL and friends sit in Queued forever (26-01117615, QRA/Jonah).
- POSTWKFL simply **not scheduled** → batches accumulate in Post Pending; kick it manually in QP073 and (re-)enable the schedule (26-01094886; 25-01006218 per QCFS GL skill).
- After upgrades/refreshes, re-check scheduled-job **active indicators** — jobs silently stop (QCFS Import/Export skill §9).
- Scheduled entries missing required parameters (business segment) or a broken Upstream↔Land DB connection also error every cycle (25-01021054).

**4. Locks (the #1 self-service fix).**
- A prior failed run leaves its lock → every subsequent cycle fails. Release in **QP110** (or QP073's lock view): POSTWKFL lock (26-01091172 — "Earlier POSTWKFL Process held the lock causing subsequent POSTWKFL processes to fail"), `QCFS_IMP` lock blocking QCFSIMPCYC so Land payments sat in staging (26-01090446), generic "Locks not releasing for scheduled jobs when failing" (22-00645827, 24-00989273).
- Known defect: system does not release locks when a job fails to obtain *other* locks — fixed in Upstream 2020.09 Hotfix Patch 3, July 2021 (25-01041504). Clients below that build will hit this repeatedly.
- If QP110 itself **times out** releasing the lock, a blocking process is still alive: cancel the blocker (a DOINTXFER in 25-01026541), then restart services; locks then release.
- "Max retries hit for lock type X" → Lock Setup override for attempts/interval (24-00944930, QCA Platform skill §10).

**5. One stuck PQID blocking the drain.**
QP045 recipe (QCFS GL skill §4): filter Process ID = `POSTWKFL`, Process Status = Processing → double-click the stuck PQID → **Cancel, then Release the Lock** (26-01107081 — "Initialize Function Failed. Duplicate process found."). Other blockers seen: REPOSCRUB + WINT stuck and holding up POSTWKFL — cancel them (25-01025036); a runaway `JBOACHILD` force-killed, then graceful QPEC restart (26-01118654, CEN PRDA1).

**6. Orphaned PRC/CI rows after a crash, user cancel, or outage.**
- User cancelled mid-run but the cancel flag didn't stop the work → status stuck in `PRC`, never `CS`: verify the business result actually posted, then run a status-correction script (26-01095776 — JEPOSTONLY RRID stuck PRC, update script to fix JE100 RRID + JE205 batch status; 26-01064142 / follow-up 26-01066103 — client recreated the batches instead).
- After an outage: confirm the PQIDs are NOT running on any QPEC, then script status → `SXL` and release locks (25-01048884, AST). A failed PCW needed status → `SPE` plus **re-inserting the `QARCH_LOCK` / `QARCH_LOCK_PARAM` rows** the failed run had deleted (25-01033024, MAC).
- If the batch itself is wedged in Post Pending for data/defect reasons, the standard exit is a script to move it back to **Draft** (26-01110851 AP055; 26-01079262 — script updated IDBATCHMASTER + workflow status to Draft; 25-00999195 — same, routed through Professional Services; 25-01037856 — invalid batches scripted to `CNP`).
- QDO maintenance groups / transfers stuck in Processing: retry first (25-01036705), then QPEC/System-Manager restart (23-00928287; 25-01050629 — RDCALCNEW hung, **restart the System Manager service** cleared it).

**7. Concurrency collisions.**
Two live instances of the same job = both can die or corrupt state: a cancelled-but-still-running JBLDWCVOL collided with its rerun at the JBDEPPRG cleanup step — ADO cursor conflict failed both (26-01105762, MAC); simultaneous BKRVNU runs caused spurious VL reversals (#1659398, QRA Platform skill §4); Escheat kicked off at the same time as JEPOSTONLY on the same checkwrite dataset caused DB blocking (25-01027279, CEN). **Rule: never run two instances of the same heavy process over overlapping data; after any cancel, verify the old PID is truly gone before rerunning.**

**8. Scheduler-identity config (works manually, fails scheduled).**
The QPEC Scheduler creates+approves+posts some batches itself; if SM093 forbids one entity doing all three, scheduled POSTWKFL errors while manual runs work. Fix: SM093 (GLOBAL COMPANY layer) → WF ID `QCFSIMPORT`: check Allow Draft/Approve, Allow Draft/Post, Allow Draft/Approve/Post (26-01113887, Mitsui). Related: SM093 exclusivity bug fixed in 2023.04 Hotfix 11 (26-01107018); QRA Import batch arriving "COULD NOT POST" → MT100 setup changed so the batch goes directly to Approved Final (26-01113287). Broader pattern (shared eSuite skill §3): scheduler-only failures = DEBUG/impersonation/identity config, not business logic.

---

## 4. Crash / restart runbook

### 4a. Signature table — what the error text tells you

| Log/error signature (verbatim) | Meaning | Action | Anchor |
|---|---|---|---|
| `Exiting QPEC gracefully in response to too much memory being used` repeatedly (>3× in 2 h on one server) | **Memory-exhaustion crash-restart loop**; MT eventually degrades from connection-pool churn; POSTWKFL was the most persistent offender | Treat as incident, not a one-off: identify the offending process, run it in subsets, escalate with the §10 evidence pack | ADO #1806848 (SND; RB0007 runbook addition) |
| `System.OutOfMemoryException` + QPECs found stopped in the morning | Instances exceeding the per-instance memory limit (e.g. 787/822 MB vs 750 MB limit) | Cloud Ops memory review / raise limit / subset the jobs | ADO #1765732 (XCL PRDA1 master ticket) |
| Many instances crash simultaneously, auto-restart in seconds, **no stack trace in any log** | Server-level event (the engines were victims) | RCA via Cloud Ops; rerun the dead PQIDs | 26-01110792 (SGYU_HD_PRD17 — 9 engines, ~5 s) |
| `Realtime message logging has been turned off because QPEC Failed to create/open file to log messages` | Disk/file-system/server outage on the QPEC box | Cloud Ops server restore; processes complete after | 25-01050789 (large-scale outage) |
| `pQueuedProcess = NULL` then `This QPEC instance will be shut down immediately!` | Engine self-shutdown on archive-queue null read; pool silently depletes while monitoring stays green | Restart engines; monitoring alert exists (log wildcard `*.Application.QPEC`) | ADO #1839889 (ENGS/EQC) |
| `Unable to establish a connection with any endpoint.` | Endpoint broker / MT / process-launcher plumbing — NOT business logic | One bizarre confirmed cause: the QPEC service account had >900 AD group memberships; trimming below 900 let services start (25-01011218). Otherwise broker/MT restart | 25-01011218 (SGY); shared eSuite skill §3 |
| `Failed to connect to QPEC Process Launcher Service: Object reference not set…` (one user only) | Stale user session | Log out / back in | 24-00953641 |
| `QPEC SYSTEM ERROR` on a process (e.g. COPY_DVD_W) | Instance died mid-run | Check crash-rescue behavior below; rerun | 26-01086802 (QDO/CNX) |
| Cancelled/failed process simply vanishes from System Manager while job row stays stuck | Engine lost the step | Restart QPECs; reset the row per §3.6 | ADO #874381 (TIPS Settle) |

### 4b. Crash-rescue mechanics (what QPEC does on its own)

- QPECs periodically scan for **crashed processes on the same machine** and reset them to `SE` or `PFL` ("database connection lost") — since #1385288 this reset is logged (`QARCH_QPEC_MSG_LOG` or the machine's QPEC log file). A `PRC` row whose engine died and that *never* moves to SE/PFL means the rescue failed.
- Known rescue-defeat: in AKS/Linux containers, PID reuse makes the recorded `LOCAL_MACHINE_PROCESS_ID` look alive, so abandoned `PRC`/`PIK` rows are stranded until a manual fix-up (ADO #1864454, New — affects `ups-qpec-linux` cells).
- At crash time the engine writes `_Copy_<timestamp>_QPECRealTimeMsgLog_<PID>.log` copies — those are the crash artifacts to pull (ADO #1806848).

### 4c. Restart protocol

1. Prefer **graceful restart** via System Manager / Cloud Ops request (the standard SF ask: "Gracefully restart the <ENV> QPECs" — 26-01119095, 26-01122593, 25-01053175 and ~20 more in the sample). Force-kill only a specific runaway child first if needed (26-01118654).
2. A restart is **mandatory after config changes** that engines cache: metadata/global-key changes (`WRITE_TO_DB_ONLY_AT_END` — 25-01043414), validation toggles (`QESUITEValidationBAEntity0024_DuplicateBAName` — 25-01031115), any FTP/host change (QCFS Import/Export skill §9), and timeout changes (§5).
3. **Verify after restart:** processes actually being picked up (25-01043752), and web/MT endpoints answering — a post-deployment restart once left WCF listeners unbound for ~34 h with processes alive but deaf (`EndpointNotFoundException`/TCP 10061 on ports 9201/9210/9212/9214/9218; ADO RCA #1839026, RRC). If engines crash repeatedly on restart, reboot **both** the QRMMT middle-tier and QPEC servers (22-00669869, QCFS Import/Export skill §9).
4. If L1 cannot restart (access/tooling), raise the Cloud Ops **Incident** — that is the documented path (26-01092959, 26-01086774).
5. Memory-driven instability: restart resets starting memory (QRA 1099 skill §4 workaround); long-term = run large jobs in subsets, and check for known leaky processes (QPTM `NNCALCFUEL` suspected in the ONK QPEC EXE crash/memory-leak RCA — ADO #1734201; QDO MEG screen search spiking MT memory until QPECs crash — ADO #1645457).
6. Monthly **preventive** PRD QPEC restarts are an accepted standing practice for some clients (25-01013765, CNX) — a restart request alone is Expected Behavior, not a defect.

---

## 5. Timeout family (the post-patch reset trap)

**The single most repeated QPEC config incident across QCA/QRA/QCFS:** a patch/hotfix deployment **rewrites `QPEC.ini` (and `QPEC.exe.config`), resetting `CommandTimeout` to the default** → the first heavy month-end process after the patch dies with a timeout. Verbatim: "the patch wipes out the QPEC.ini configuration for the command timeout" (26-01068706, SGY).

| Lever | Where | Default seen | Raised to (cases) |
|---|---|---|---|
| `CommandTimeout` | `QPEC.ini` **and** `QPEC.exe.config`, on **ALL** QPEC servers | 3600 s (1 h); some builds 900 s | 18000 (QCA JIB standard — 26-01104563, 26-01064034, 25-01057580); **28800** for JBOWNALLOC (26-01118602, CEN); 10800 for JBREBILL (26-01079810); 7200 for JBROLLDATE (25-01041819) |
| `COMMAND_TIMEOUT_SECONDS` | global config key, **client metadata layer** | 900–18000 | 14400 (25-01006930); QRA `QSTG1099OV` stop-gap (#1638333, QRA Tax skill §4) |
| `DATABASE_COMMAND_TIMEOUT` | global config key | 900 | 1900 (25-01031905) |
| PPA/QRA batch timeout | `QPEC.ini` | 3600 | 7200; 14400 only as temporary unblock (25-01005326, 25-01037076) |

Rules:
1. **Any "worked before the patch, times out now"** → check these values FIRST, before code/data investigation (QCA JIB skill §4 — highest-frequency cluster).
2. Change on **all** QPEC servers, then **graceful restart** — engines read the ini at start.
3. **Client-layer check-in trap:** a value raised at core but never checked into the client layer resets to 900 on the next deployment (25-01024015 — "resolved in V16, updated at core UPS, never checked into CEN client layer, reset to 900").
4. **Revert temporary raises** after the close: CEN raised 5 h → 8 h for JBOWNERALLOC then reverted to 18000 (24-00984129); EQC reverted 4 h → 1 h via the next hotfix — note hotfixes are also how ini changes DEPLOY, confirming the reset mechanism (26-01086203).
5. Timeout error shapes to recognize: `Timeout exceeded while waiting for execution of this Batch`; `[COM Error] File: …QADOCommand.cpp, Line: 1287 … Query timeout expired` (26-01079810); a process dying at **exactly 1 hour** (TIPS PANIGHTLY — ADO #234047). The 26-01079810 fix stack is the model for "raise timeout is not enough": update stats, add the two indexes, shrink the data set, THEN raise `QPEC.ini` to 10800 — final run 167 min.
6. Timeout ≠ always config: if the same SQL times out at sane settings, hand the SQLID to the product code/perf skill (e.g. `m_INS_PopulateJEStaging` ADO #1671837, QCA JIB skill).

---

## 6. Monitoring screens & logs (per product)

**Screens (classic upstream/eSuite):**
| Screen | Role in this runbook |
|---|---|
| **QP045** | Process-queue monitor ("Post Workflow Manual Request"): filter by Process ID/Status, double-click PQID → Cancel + Release Lock (26-01107081); POSTWKFL scheduling check (QCFS GL skill §4) |
| **QP073** | Process launcher: manual POSTWKFL kick (26-01094886), QCFSIMPCYC, QSTAGXLSIM, 1099 runs; also shows PQIDs/locks |
| **QP074** | Report-process launcher (report jobs like ARR014 run here — QCFS AR skill §7) |
| **QP110** | Lock release (26-01091172, 26-01090446); if it times out, cancel the blocking process first (25-01026541) |
| **QP043** | Export launchers/summary (QRA→QCFS) |
| **SM093** | Workflow draft/approve/post exclusivity — scheduler-identity failures (§3.8) |
| **System Manager** | Engine states (STPER/KILL), graceful restart, hung-process rescue (25-01050629, 24-00986198) |
| Web | eSuite **Batch Processes** page = QP073/QP045 equivalent (QCFS ADO skill) |

**Logs:**
- Server file layout: `E:\Quorum\<ENV>\QPEC\<Product>.Application.QPEC\Logs\qpec_*.log` + `QPECRealTimeMsgLog_*.log`; crash-moment copies `_Copy_<timestamp>_QPECRealTimeMsgLog_<PID>.log` (ADO #1839889, #1806848).
- Segregated drainers: `qtrace.<product>.QPEC.*.segregated.log` via **GatherLogs** from the Managed Steps folder — QPTM EDI runtime errors live HERE, not in EDIServ logs (QPTM Nominations skill, #1737489).
- DB-side: `QARCH_QPEC_MSG_LOG` (engine message log incl. crash-rescue entries, ADO #1385288); process status-change history rarely carries messages, so a crash-reset is easy to miss without it.
- Perf traces: qtrace grep for one SQL repeated thousands of times = cacheable defect (shared eSuite skill, #1721402).

**Per product — the QPEC things that page L4:**
| Product | Segregated / hot processes | First screens |
|---|---|---|
| QCFS | POSTWKFL, PSTWKSPLT, QCFSIMPCYC, ADPUPLOAD | QP045/QP073/QP110, GL025/AP0xx batch status |
| QRA | BKRVNU (+RDCALC/RDCALCNEW children), OFR/CW chain, JEPOSTONLY, POSTWKFL | VL100, JE100 (Clean button — 25-01026200), QP045 |
| QCA | JIB chain (JBLDWCVOL→…→JBOWNERALLOC/JBREBILL), LOSLOAD | JB005, QP073, QP110 |
| QDO | COPY_DVD_W, DOINTXFER, MG create/revert, funds release | DO129/DO020/MEG, QP110 |
| QPTM | PANIGHTLY, ALALLOCATE, EDI seg steps | QPEC segregated log first (QPTM PRODUCT.md) |
| TIPS | GMASLDVOLS, SETTLE chain, MEASUREMENT | System Manager + seg log; packaging check #1442338 |

---

## 7. Known ADO items (QPEC engine/scheduler stability)

| ADO | Type/State | What | Relevance |
|---|---|---|---|
| **#1806848** | SaaS Delivery GCO / Closed | QPEC crash-restart monitoring alert + **RB0007 runbook** review (SND) — memory-exhaustion loop definition, evidence list | §4a/§10 |
| **#1864454** | Bug / New | AKS container PID reuse defeats crash rescue — PRC/PIK rows stranded | §4b — cloud-cell clients |
| **#1385288** | Requirement / Closed | Log when a QPEC resets a crashed process (SE/PFL) to `QARCH_QPEC_MSG_LOG` | §4b |
| **#1734201** | Requirement / Closed | RCA ONK 25-01022891 — QPTM QPEC EXE crashes + memory leak (NNCALCFUEL suspected) | §4c.5 |
| **#1774745** | Bug / Closed | System Manager falsely flags QPECs "Stopped Unexpectedly" after memory-limit restart (EQC); family: 1762900 (MER TIPS stuck queue), 1770245 (EQC), 1773085 (NRM), 1775768 (QPECS down PROD); platform dep #1780230 | §1/§3.2 |
| **#1545342** | Bug / Closed | System Manager restarts QPEC twice | §1 |
| **#1850176** | Incident GCO / Closed | EQT QPTM UAT QPECs "down" post-maintenance while registered-up — alert gap | §3.2 |
| **#1839889** | SaaS Delivery GCO / Closed | ENGS engine self-shutdown on `pQueuedProcess = NULL`; log-path wildcards for alerting | §4a/§6 |
| **#1839026** | RCA Request / New | WCF listener fails to re-bind after pipeline QPEC restart (34 h silent outage, RRC) | §4c.3 |
| **#1765732** | Incident GCO / open | XCL OOM + QPECs stopped (master ticket); 750 MB instance limit evidence | §4a |
| **#1645457** | Bug / Closed | QDO MEG search → MT memory spike → QPECs crash, can't restart (GEC/MAC/GPOR) | §4c.5 |
| **#1442338** | Bug / Verified | NRM.TIPS.Application.QPEC csproj missing Crude packages → GMASLDVOLS never spawned post-upgrade | §6 TIPS row |
| **#1732358** | Bug / Closed (2025.10) | Deployed `QPEC.OnPremDirect.ini` shipped a plaintext DB password in `[Database]` section (section unneeded) — removed across products | patch/refresh audits |
| **#874381** | Bug / Closed | TIPS Settle stall — step disappears from QPEC in System Manager | §4a |
| **#234047** | Rejected | PANIGHTLY dies at exactly 1 h = QPEC.ini query timeout (not code) | §5.5 |
| **#1659398** | Bug / Closed (CNX 2022.04) | Simultaneous BKRVNU collision; clean/undo now releases run locks | §3.7 |
| **#153810** | QFC | Graceful-recovery fix in newer QFC — NOT back-patched to old builds | QPTM Alloc skill §restart |
| **#1865638** / **#1752185** | myQuorum Cloud WIs | Cloud RCAs for stuck OFR queue (26-01123485) / QDO COPYDVD stuck-processing (25-01039524) | §3 QDO/QRA |

---

## 8. Diagnostic SQL

Real, evidence-derived queries only. The generic process-queue table name is intentionally NOT stated here — it has not been verified against a live schema in this mining pass; resolve it per client via the metadata server (`table-analyst`), then adapt A/B. Queries below use only table/column names verbatim from case evidence.

```sql
-- A. Orphaned-workflow check for AFEs/batches stuck in Pending after full approval (26-01105060 pattern)
--    A WF_INSTANCE_ID on the header with no matching engine instance = orphaned workflow.
SELECT h.AFE_NO, h.WF_INSTANCE_ID, h.WF_STATUS_CD
FROM   QCTRL_AFE_HDR h
WHERE  h.WF_INSTANCE_ID IS NOT NULL
  AND  NOT EXISTS (SELECT 1 FROM QARCH_WF_ENG_INSTANCE e
                   WHERE  e.WF_INSTANCE_ID = h.WF_INSTANCE_ID);
-- Cleanup (engineering-approved script only): reset status, clear WF_INSTANCE_ID / WF_STATUS_CD /
-- WF_ROUTE_NM_OVERRIDE / WF_ROUTE_NM_SELECTED, delete stale rows from
-- QARCH_WF_TRAN_INBOX_BASE and QWF_TRAN_INBOX_AFE.            [status: template from 26-01105060]

-- B. Crash-rescue audit: did an engine reset a crashed process? (ADO #1385288)
SELECT *                                   -- filter on the PQID's window
FROM   QARCH_QPEC_MSG_LOG                  -- engine message log
WHERE  MSG LIKE '%reset%'                  -- crash-reset entries logged since #1385288
-- [NOT YET RUN — column list varies by build; confirm via metadata server before use]

-- C. Lock forensics after a failed run deleted its own locks (25-01033024 pattern):
--    compare QARCH_LOCK / QARCH_LOCK_PARAM rows for the failed PQID vs a healthy prior run
--    before re-inserting.                 [NOT YET RUN — client-specific]
```

Status codes seen in evidence (for queue queries once the table is bound): `QUE` queued · `PIK` picked · `PRC` processing · `CS` complete · `SE` stopped w/ error · `SPE` stopped-processing-on-error · `PFL` process failed / DB connection lost · `SXL` scripted cancel (25-01048884) · `CI` cancel issued · `CNP` could-not-post (26-01113287, 25-01037856) · service-level `STPER` (26-01086774).

---

## 9. Expected-Behavior FAQ (close these without investigation)

| "Issue" | Reality | Anchor |
|---|---|---|
| "POSTWKFL stuck — no movement" during a huge post | Validating tens of thousands of GL records per batch takes hours; it finished same-day | 25-01035751 |
| "Job stuck, restart QPECs" during upgrade catch-up | 376 batches × ~4 min each was on pace; restart was cancelled | 25-01034243 |
| "Batch stuck in Post Pending" with future Date-to-Post | System waits for DATETOPOST by design | 25-01022292, 25-01027244, 26-01065520 |
| Batch won't post — next period not open | Open the next accounting period in SM006 (accrual logic needs it) | 25-01051259 |
| Invoices fail post: "JIB has already been processed for this month" | Change accounting date to an open month | 25-01019990 |
| "POSTWKFL completed with errors" panic | The batches often actually posted; only the run reported failure — verify batch status first | ADO #1720373 (QCFS ADO skill) |
| Standing monthly QPEC restart requests | Accepted preventive practice, not a defect | 25-01013765 |
| First JIB step "stuck" for an hour but backend shows it completed | UI didn't refresh; user was watching a finished step | 26-01113058 |
| Process slow after a user mass-launched historical work (e.g. COPY_DVD_W on 300+ properties from 2021) | Let it drain; don't kill | 26-01090998 |

---

## 10. Escalation

| Situation | Route | Bring |
|---|---|---|
| Restart request, engines down, server sizing, crash-loop, scheduler service | **Global Cloud Ops** (Incident GCO work item; L1 "QCloud" first, Incident if they can't — 26-01092959) | Env name (`<CLIENT>_HD_<TIER>` string), which engines/servers, timeline |
| Crash-restart loop specifically | Cloud Ops + App Owner per RB0007 | Per ADO #1806848: process name(s) crashing repeatedly, memory value at crash, crash-cycle duration, whether MT is degrading; the `_Copy_*_QPECRealTimeMsgLog_*.log` files |
| Stuck-status reset scripts (PRC/SXL/Draft moves) | L4 with an **engineering-approved script** (model: 26-01105060 — script reviewed, UAT-validated, DB-verified) | PQID, exact first error, proof the process is not live on any QPEC |
| Post-patch timeout re-application | Deployment/Cloud Ops checklist item — must be re-done after **every** patch for affected clients | The client's known-good CommandTimeout values + server list |
| Suspected engine defect (rescue failure, listener re-bind, System Manager flags) | Platform engineering — cite the §7 ADO item; do not open duplicates | Repro evidence + log signatures from §4a |
| Segregated child never spawns post-upgrade | Product engineering (packaging/csproj audit) | #1442338 pattern: compare QPEC csproj package list pre/post upgrade |

**Handoff minimum (all routes):** PQID + first ERROR line + environment + client build/patch level + which §4a signature matched. DEV-tier metadata findings are CONFIRMED anchors; client-PRD data-state claims stay INFERRED until verified.

---

*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
