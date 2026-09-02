# SKILL (ADO): TIPS Batch Processing, System Config & Environment — Defect/Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** My Quorum TIPS (Midstream)
**Source:** Azure DevOps Bugs (QuorumSoftware), area paths `Engineering\Midstream\*` + `Engineering\Maintenance\Midstream and Transportation\*`, State Closed/Resolved.
**Scope (this functional area):** TIPS *batch framework & environment* — QPEC stability (crashes / STPER / System-Manager false-stops / stuck-in-queue), Facility & Company Batch Job Submittal Web-vs-Classic sync defects, TIPSLOCK / Master-TIPS-lock timeouts, batch-step performance regressions (SQL tuning), TRNX_ID exhaustion/collision & duplicate-row PK failures created by batch steps, posting / imbalance / accounting-period roll PK errors, archive & purge (QARCHIVE / TIPARCHIVE / PPAPNDPURG / RECPURGE), environment provisioning & post-refresh (TIPS API Host not starting, reseed identity/sequence procs, QPEC.ini password, connection-type), and batch-related config/warning-flood items.

**Use When:** You have a TIPS batch/QPEC/environment symptom and want to know *is there already an ADO fix, in which build, and what was the root cause* — before re-debugging. Pairs with the SF-mined `SKILL_TIPS_Batch_Processing.md` (operational recipes); this file is the ADO defect ledger behind those recipes.

> **Evidence base:** WIQL matched **1,176** Closed/Resolved bugs across the two Midstream area branches under the functional title filter (capped at the 250 most-recently-changed for field skim). **~40** representative TIPS bugs were deep-read in full (Description + ReproSteps + the full dev **comment thread** + linked PRs/branches). The Midstream + Maintenance branches are **mixed QPTM + TIPS**; QPTM-only items (Nomination/NNNOMLOAD, Capacity Release, RFS, EDI/NMST, QGM/QCM/QDOD/IPWS, TSP/Interconnect) were dropped — see *Classification & Overlap* at the end. IntegrationBuild is **empty on every bug**; fixed-in-build is inferred from **iteration path (YY.NN)** and **PR target branches** (`release/17.NN.0`, `hotfix/17.NN.x`) and is marked *(inferred — confirm in release notes)*.

---

## TABLE OF CONTENTS
1. [Quick Triage](#1-quick-triage)
2. [Decision Tree](#2-decision-tree)
3. [Cluster A — QPEC Stability: crashes, STPER, false "Stopped", stuck-in-queue](#a)
4. [Cluster B — TIPSLOCK / Master-TIPS-Lock SQL timeouts](#b)
5. [Cluster C — Batch-step Performance Regressions (SQL tuning)](#c)
6. [Cluster D — Facility/Company Batch Job Submittal: Web↔Classic sync](#d)
7. [Cluster E — TRNX_ID exhaustion, collision & duplicate-row PK failures](#e)
8. [Cluster F — Posting / Imbalance / Accounting-period roll PK errors](#f)
9. [Cluster G — Archive & Purge (QARCHIVE / TIPARCHIVE / PPAPNDPURG / RECPURGE)](#g)
10. [Cluster H — Environment Provisioning & Post-Refresh (API Host, Reseed, QPEC.ini, Connection-Type)](#h)
11. [Cluster I — Batch Config & Warning-Flood / Security-Metadata items](#i)
12. [FIX-VERSION MATRIX](#matrix)
13. [Diagnostic Pointers](#diag)
14. [Escalation: is the client build fixed?](#esc)
15. [Classification & Overlap, Dead Ends, Caveats](#caveats)

---

<a name="1-quick-triage"></a>
## 1. Quick Triage

```
[ ] 1. SYMPTOM CLASS — QPEC down/crash/stuck (A) | a SPECIFIC step times out (B/C) |
       Web shows different status than Classic (D) | PK / duplicate-key error (E/F) |
       archive/purge fails (G) | broke right after refresh / new env (H) | warning flood / config (I)?
[ ] 2. Capture EXACT error + the registered-SQL name in the QPEC log
       (QARCH_QFCBATCH_SQL_TRACE.PROCESS_STEP_QUEUE_ID names the failing SQL — e.g. Sel_MonthlyRunID,
       Select_ReallocDependTrnxIdProcessInd_Monthly, SQLID_INS_GATH_REC_PAYSTATION, INS_CTRL_REG_OTC_DTL_RECORDS).
[ ] 3. Client VERSION (2022.10=17.22 line / 2024.04=17.21? see note / 2025.04=17.27 / 2025.10=17.28 / 2026.04=17.29).
       Most fixes are version-gated; an unpatched client needs a hotfix even though the bug is "Closed".
[ ] 4. DB vendor — MANY of these are MSSQL-ONLY regressions (OPTION FORCE ORDER, missing column in the MSSQL
       branch of a split query). Oracle-only too (reseed semicolons). Always note vendor.
[ ] 5. CORE bug or CLIENT-SPECIFIC (stored proc / metadata)? Client-specific fixes live in <CLIENT>.TIPS.Metadata
       and do NOT ship in a core build — they need a per-client patch.
[ ] 6. Did it start after a DB REFRESH / Q-end refresh / new env provision? → Cluster H + Cluster A (refresh storms).
```

---

<a name="2-decision-tree"></a>
## 2. Decision Tree

```
TIPS batch/QPEC/env symptom
│
├─ QPECs crashing/restarting, "Stopped unexpectedly", STPER, all processes stuck in queue?      → A
│    └─ Started at a DB-refresh window or at CPU>97%? infra mitigation first, then QFC fix #1774745
│
├─ ONE step hangs ~hour that normally takes seconds, message points at a registered SQL?
│    ├─ TIPSLOCK / Master lock (Select_ReallocDependTrnxIdProcessInd_Monthly)                   → B
│    └─ Any other step (MEASANALYS, CTRMTR, GATHFUEL, INACCTACCM, REGRVRSMAN, TOLERANCE)         → C
│
├─ Web FBJS/CBJS status ≠ Classic, or Web lets you run a job Classic blocks, or "No batch job
│    sequence defined…", or rerun jobs greyed out in Web?                                       → D
│
├─ PK / duplicate-key violation?
│    ├─ PK_QTRAN_PAYSTATION / TRNX_ID dup on an ALLOCATE step                                    → E
│    ├─ PK_QTRAN_IMBAL_ACCT_BAL (CUSTACCTBAL / posting roll)                                     → F
│    └─ "PDA/Measurement fails on LARGE TRNX_ID value" (int overflow)                            → E (long-term fix)
│
├─ QARCHIVE/TIPARCHIVE PK error, or scheduled archive/purge won't kick off, PPA purge missing?  → G
│
├─ Broke right after a refresh / new env: API host won't start, reseed warnings, missing
│    connection IDs, .NET-vs-SQL connection type?                                               → H
│
└─ Warning flood ("No records found in Facility Configuration…"), or config-screen edit
     bypassing security, or a step erroring on a missing/changed config?                        → I
```

---

<a name="a"></a>
## 3. Cluster A — QPEC Stability: crashes, STPER, false "Stopped", stuck-in-queue

**Symptom:** QPEC instances crash/restart; all batch processes stuck in QUEUE; System Manager flags QPECs as "Stopped with Error" / STPER even though they came back up; "stopped unexpectedly" logged immediately after a successful restart.

**Root causes (from dev comments):**
- **System-Manager false-stop (the core defect):** when a running QPEC exceeds its memory limit it auto-restarts; the QPEC comes back up but **System Manager doesn't see it as up and sets it to "Stopped with Error."** Reproduced in `EQC_UPG17MID_QRMTIPS`. Dependent on platform item **#1780230**. — **#1774745** (EQC; also drives MER #1762900, NRM #1773085, TEP, and QPTM ONEOK cases — same signature). QFC/platform fix.
- **Infra-driven restart storms (NOT a code bug):** DB refresh on the PRD server caused mass QPEC restarts at the exact refresh start/end; CPU exhaustion (MaxOCPU pinned >97%). Customer self-mitigated by moving the refresh DB off PRD and raising MaxOCPU 24→32, dropping crashes to a 1–3/month baseline; Oracle RAC connection behavior still under investigation. — **#1788585** (ETP; ties to RCA **#1749170**).
- **Stuck in STPER, restart clears it:** QCloud restarts the services + uploads logs; if it doesn't recur it's closed as infra (rejected as a code bug). — **#1821239** (EQC, *Rejected*; check via #1820170).

**Fix / fixed-in-build:** #1774745 QFC fix deployed to **EQC dev then patched** to affected clients (no clean core build number — platform-dependent on #1780230); *(inferred 2025.10/2026.04 line — confirm in release notes)*. #1788585 / #1821239 = **operational/infra**, no code fix.

**Workaround:** QCloud restart of QPEC services clears the immediate stuck state (consistent with the SF-side UX-script recipe). For refresh storms, move the refresh DB off the PRD host and ensure CPU headroom. Don't expect a code fix for the infra-driven variants.

**Bug IDs:** #1774745, #1788585, #1821239 (+ related #1762900, #1770245, #1773085, #1775768, #1782402, RCA #1749170, platform #1780230).
**Linked SF:** 25-01058663 (#1770245), 26-01065396 (#1775768).
**Clients:** EQC, MER, NRM, TEP, ETP (and QPTM ONEOK shares the System-Manager defect).

---

<a name="b"></a>
## 4. Cluster B — TIPSLOCK / Master-TIPS-Lock SQL timeouts

**Symptom:** Master TIPS process / **TIPSLOCK** step hangs (SQL timeout); a step that normally runs 5–15 s takes 13–20 min or "forever," locking the facility. Plant-size-dependent (big plants like WEST3 hang, small ones fine).

**Root cause:** the registered SQL **`Select_ReallocDependTrnxIdProcessInd_Monthly`** (reallocation-dependency check). Two distinct dev findings:
- A **`UNION`** forces a DISTINCT over both legs *before* the join to the TRNX CTE, which would otherwise exclude almost all rows. Changing **`UNION` → `UNION ALL`** dropped runtime from >1 h to seconds. — **#1679048** (UTG).
- Even after the rewrite, performance was inconsistent on high-volume plants; further tuning brought the SQL Server plan cost from ~12 to ~1.5. — **#1683233** (core follow-up), then **#1725292** (ETP) when ETP on 2024.04 still saw 13-min runs on WEST3.

**Fix / fixed-in-build:** repo `Quorum.TIPS.ClassicBatch` (registered SQL). #1679048 ≈ **2024.04** (iter 24.x). #1683233 merged to **2024.04** (PR target). #1725292 PR **1725292 → 2024.04** hotfix line, deep-tuned; *(inferred 2024.04 + hotfix — confirm in release notes)*.

**Workaround:** none clean — it's a query fix; an unpatched client just suffers the timeout. Raising the QPEC timeout only defers the failure.

**Bug IDs:** #1679048, #1683233, #1725292.  **Clients:** UTG, ETP, ONM (referenced).

---

<a name="c"></a>
## 5. Cluster C — Batch-step Performance Regressions (SQL tuning)

The recurring pattern: a registered SQL regresses (often a release-to-release plan change or a query someone split per-vendor), and the fix is **MSSQL `OPTION (FORCE ORDER)`**, **`JOIN` instead of `LEFT JOIN`**, or undoing an "Enterprise" change. Most are caught by the **TIPS Performance (PRF) regression suite** (tag `Performance`), not by clients.

| Bug | Step / SQL | Root cause | Fix | Build (inferred) |
|-----|-----------|-----------|-----|------------------|
| **#1636859** (MOM) | Company Imbalance **INACCTACCM** → `SQLID_SSEL_QTRAN_FIXED_FUEL`; "Query timeout expired" | Splitting logic adds huge overhead when **no splits are set up**; optimizer picked a small-data plan against large rerun volume | **Bypass split logic when no splits configured.** Workaround: raise **`SPLIT_COUNT_INACCTACCM`** (e.g. 6 on 8-QPEC PRD) to parallelize | 2022.10 + up (merged 2022.10/2023.04/develop) |
| **#1726948** (SCT) | **MEASANALYS** → `SQLID_ANL_STD_METERS` (hangs at 0 rows vs ~80k) | MSSQL plan instability | **`OPTION (FORCE ORDER)`** added | 2024.10 / 2025.04 / develop (PR 111432-34); `ClassicBatch hotfix/17.27.5, 17.28.1` |
| **#1745358** (SCT) | **CTRMTR** → `SQLID_INS_GATH_DEL_PAYSTATION` stuck/timeout | MSSQL query plan | MSSQL query corrected (force-order pattern) | 2024.10 / develop (PR 115120-21); `ClassicBatch hotfix/17.21.33, 17.27.6, 17.27.7, 17.28.3` |
| **#1746523** (SCT) | **CTRMTR** part 2 → `SQLID_INS_GATH_REC_PAYSTATION` | same plan issue, second SQL | applied same **FORCE ORDER** fix as #1745358 | 2021.04→2025.04→2024.10 (PR 115145/115216/115217/115218); `hotfix/17.21.34, 17.27.6/7, 17.28.3` |
| **#1651744** (DCP) | **REGRVRSMAN** (in REVENUEIMB) → `INS_CTRL_REG_OTC_DTL_RECORDS` (`QSQL_TipsRevRevRegRvrslManAdj.cpp`); 7 min → 30–35 min | Oracle plan change with **`LEFT JOIN`** | change **`LEFT JOIN` → `JOIN`** (client-specific step) | 2024.04 |
| **#1687619** (ONM) | **FIXEDFUELS** → `m_Ins_Fixed_Fuels_Rev`; Facility batch +62 min in 2024.10 | Enterprise changes + slow insert query | rewrote query (5 min → 27 s, PR 101244); also backed out an Enterprise change | 2024.04 hotfix + 2024.10 |
| **#1651730** (ONM) | GATHRATES / CONFVOLS +19 min in 2024.04 | no code change found; query tuning + env parity | query tuning only | 2024.04 |
| **#1095594** (SEM, TIPS CAN) | SETTLE **TOLERANCE** → `SQLID_Upd_Paystation_Zero_Dollar_No_Reversal`; rerun 2 h vs few s | nasty rerun-comparison SQL (facility-CCT handling) | tuned (1 h → 40–70 s; "moderate" due to CCT handling) | 2021.04 |
| **#1783999** (ONM) | GATHFUEL / ONKSHIPALL +44 min in 2026.04 | **DB-speed fluctuation, NOT product**; ONKSHIPALL is a client-specific proc | none — **Rejected** | n/a |

**Resolution recipe:** capture the long-running registered SQL from `QARCH_QFCBATCH_SQL_TRACE`. If it regressed at a version bump and is MSSQL-only → suspect a per-vendor split or a plan flip; the standard fixes are **FORCE ORDER** / **JOIN-not-LEFT-JOIN** / **UNION ALL** (see B). "Every step slower across the board" = infra/DB speed, not a code defect (#1783999).

**Linked SF:** 23-00934008 / 23-00934500 (#1636859).  **Clients:** MOM, SCT, DCP, ONM, SEM.

---

<a name="d"></a>
## 6. Cluster D — Facility/Company Batch Job Submittal: Web↔Classic sync

**The largest TIPS-batch defect family.** The Web FBJS/CBJS screens front the same job tables (`QCODE_BATCH_JOB` orders jobs; `QTRAN_JOB_CONTROL` / `QARCH_QUEU_PROCESS` carry status) but get out of sync with Classic or skip a guard Classic enforces. Heavily the **2022.10 / ONEOK (ONM) & MPLX (MKW)** upgrade wave.

| Bug | Symptom | Root cause / fix | Build |
|-----|---------|------------------|-------|
| **#1607605** (ONM) | Rerun month selectable but process jobs **greyed/locked** in Web; Classic works | Bad **Rerun-Exclude** logic for FBJS on Web (jobs marked Rerun Exclude / approval jobs). PR 87265/87266 | 2023.04 / develop (already in 2022.10) |
| **#1608023** (MKW) | "**No batch job sequence defined for ('ALL') or plant**…" + status not reflecting Classic | FBJS didn't pick up jobs run via the **scheduler** (`TPSCHEDPRC`) and threw a bogus "no sequence" error; start-job list wrong after scheduler run. PR 92006/92007. MKW's INT_RERUN handled client-specifically | 2022.10 / 2023.04 / develop |
| **#1608737** (ONM) | Company status out of sync Web vs Classic; **Post fails from Web**, must use Classic | CBJS stability fix when posting | 2022.10 / 2023.04 / develop (PR 87109) |
| **#1681736** (ONM) | FBJS status indicator **stays grey after Settle completes** | Status check fails if user reloaded/navigated away between launch & completion (MPLX/Pembina, client-specific override suspected) | 2022.10 + (R2 SUP verified) |
| **#1687157** (ONM) | "**Run Next Job**" populates the wrong next process (esp. with an approval job mid-sequence) | logic fix | 2022.10 / 2024.04 / 2024.10 / develop |
| **#1649924** (core) | "No batch job sequence defined…" generated **after posting** a facility/company | post-state handling → now shows an info message instead | 24.09 (2024.10) |
| **#1429598** (PEM, TIPS CAN) | Daily facility jobs **not stopping on failure** (should cancel subsequent days) | regression of enh #218035; CANSPAWN/sequence | 2021.04 (TIPS.Batch 17.17.3 hotfix) |
| **#1395314** (TIPS CAN) | **TIPSSPAWN/CANSPAWN stuck** on "Run All Jobs for a Date Range," facility locks | stuck spawn process | 2021.04 (TIPS.Batch 17.17.2) + 2021.10 |
| **#1757579** (core beta) | 2025.10 QAC plant FBJS fails: **`'NVL' is not a recognized built-in function`**, "Incorrect syntax near 'MSE'" | Oracle SQL (NVL) leaked into the MSSQL path | 2025.10 (iter 25.20) |
| **#1804647** (IPF) | Web FBJS gives no UX pop-up / no refresh; only reproduces for **one user** in IPF DEV | not reproducible by anyone else — **Rejected** | n/a |

**Resolution recipe:** reproduce in **both** UIs. If Classic is right and Web wrong (or vice-versa) it's a code defect — match to this family and the client's patch level. The 2022.10 wave fixes are all merged to 2022.10+; later recurrences (#1687157, #1649924) reach 2024.04/2024.10. Workaround: perform the action in the correct UI and never trust the Web status icon without a Retrieve.

**Linked SF:** 23-00906527 (#1607605), 23-00893815 (#1608023), 23-00905993 (#1681736), 24-00942089 (#1687157).
**Clients:** ONM/ONEOK, MKW/MPLX, PEM, IPF, core CAN.

---

<a name="e"></a>
## 7. Cluster E — TRNX_ID exhaustion, collision & duplicate-row PK failures

**Symptom:** `Violation of PRIMARY KEY constraint 'PK_QTRAN_PAYSTATION'` / duplicate `TRNX_ID`; or a step **fails on a large TRNX_ID value**; or rerun POST fails on duplicate TRNX_IDs between QTRAN and QPOST tables.

**Root causes & fixes (chronological ONEOK-driven program + collateral):**
- **C++ int overflow on TRNX_ID (long-term fix):** code stored the DB sequence number as `int` (max 2,147,483,647); ONEOK's sequence passed that. Fix = widen to `long long`/`unsigned long long`. — **#1617830** (ONM long-term; short-term was #1617437). **#1652993** = the **PDA Allocation** step failing on large TRNX_ID — same int-overflow family, separate step. Builds: 2024.07 (iter 24.07) + back-merges.
- **TRNX_ID waste → collision (medium-term fix):** each reprocess of a facility for the same Prod/Acct Dt created **new** TRNX_IDs. RECPURGE changed to **recycle** existing TRNX_IDs (add new only for added splits, remove for removed splits). — **#1619944** (ONM; merged **2020.03, 2022.10, develop**; delivered ONM Patch 17).
- **Collateral over-purge:** the RECPURGE/PPA delete SQL **`m_DEL_MTR_TRNX_PPA`** joined on `PROD_DT` without normalizing to first-of-month → **daily CO TRNX_IDs on non-1st days got purged**. Fix = join on first-of-month. — **#1656405** (collateral of #1639010; 24.07). And **#1639010** (ONM): unapprove-one-PPA-month left **orphan rows in `QTRAN_TRNX_ID`** because `m_DEL_MTR_TRNX_PPA` was missing the Prod-Dt filter — added a delete for the re-run-flipped PPA records (2022.10 hotfix + 2024.x).
- **Step *creates* duplicates:** **`ASSOCIATED GAS LIFT METER VOL` (ASCGLM/ASSCGLM)** duplicated `QTRAN_ALLOC_VOL` rows when run for dailies while the plant is in **reallocation mode** — fix: only consider `PROCESS_IND = 1` + a new delete on `QTRAN_ALLOC_VOL`. — **#1731166** (2025.04 + back-merge; `ClassicBatch hotfix/17.26.20, 17.27.6, 17.28.3`).
- **Client-specific TRNX_ID collision on POST:** SRB's custom SUM-meter enhancement (**#1579772**) set TRNX_ID = numeric PROD_DT, so reruns of any month first processed after Aug-2023 collided in `QTIP_POST_RPTS_SETTLE_STMT`. — **#1640044** (short-term scripts via #1638984/#1643221; long-term = generate a unique-per-monthly-run TRNX_ID). Client-specific.

**Workaround:** for *pre-existing* dups, the SF-side delete-duplicates script + rerun. For *step-created* dups, you need the version with the fix (recycle / PROCESS_IND filter / first-of-month join / int-widening) — an unpatched client keeps regenerating them.

**Linked SF:** 23-00916530 (#1617830), 23-00923599 (#1619944), 23-00935744 (#1639010), 23-00936172 / 24-00951618 (#1640044).
**Clients:** ONM/ONEOK (program owner), SRB (client-specific), core.

---

<a name="f"></a>
## 8. Cluster F — Posting / Imbalance / Accounting-period roll PK errors

**Symptom:** `Violation of PRIMARY KEY constraint 'PK_QTRAN_IMBAL_ACCT_BAL'. Cannot insert duplicate key …` during the **CUSTACCTBAL** step of plant IMBALANCE, or when rolling the accounting period at POST; duplicate rows visible on **Customer Account Maintenance** for an OBA contract.

**Root cause:** duplicate records in `QTRAN_IMBAL_ACCT_BAL` (and `QPOST_IMBAL_ACCT_BAL`). Root-cause investigation lives in **#1772117**; delete-duplicate scripts were deployed and a code change shipped in **2025.04 Patch #3** — but Hilcorp (HEC) **still hit it after Patch #3** (the patch didn't fully prevent re-creation of the dups for their single OBA imbalance contract). — **#1805171** (HEC, *F/V*; SF **26-01097671**, references **26-01065143**). This is the same `QTRAN_IMBAL_ACCT_BAL` family the SF skill tracks (ADO #1772117 / scripts #1776936 / #1778789).

**Related posting defect:** **#1806658** (HEC) — POSTPLANT threw a **dependency error requiring JOURNAL** even though HEC doesn't run JOURNAL; fix = **remove the JOURNAL dependency check from the POSTPLANT batch job** in `HEC.TIPS.Metadata` (client-specific metadata; PR 128791). And **#1767897** (IPF) — **DAILY SETTLE** (`SETTLEMKD`) failed on `Sel_MonthlyRunID` because the registered SQL filters `UNIT_TM_CD='M'` but dailies have no monthly run id; fix = **add/update the monthly-run-id entry for daily runs** (`Quorum.TIPS.Web` + `ClassicGUI`, 2025.04/2025.10; `hotfix/17.28.x, 17.29.1`).

**Workaround:** delete-duplicates script against `QTRAN_IMBAL_ACCT_BAL` / `QPOST_IMBAL_ACCT_BAL` (verify-SELECT first), then re-run the IMBALANCE/POST step; for the JOURNAL-dependency case, remove the dependency in the client metadata layer (already done in PRD for HEC — the WI just checks it in so a future patch won't revert it).

**Linked SF:** 26-01097671 / 26-01065143 (#1805171), 26-01099529 (#1806658), 25-01056036 (#1767897).
**Clients:** HEC/Hilcorp, IPF.

---

<a name="g"></a>
## 9. Cluster G — Archive & Purge (QARCHIVE / TIPARCHIVE / PPAPNDPURG / RECPURGE)

| Bug | Symptom | Root cause / fix | Build |
|-----|---------|------------------|-------|
| **#1689869** (HPE/BBT) | Scheduled QArchive job won't kick off from Schedule Definition; once queued, **completes with PK errors** | Two issues: (1) scheduler/schedule-definition setup (delete stale Profile, set current start date — largely a **QCloud/setup** matter), (2) the **`ARC_90_DAY` archive definition was missing the `TSP_PROP` / TSP joins** in the Parent-Table-Join clause → PK error. Core fix per requirement **#1454430**. Delivered via patch **#1709778** | release branch (2025.04 era); SF 24-00974423 |
| **#1535066** (ENT) | **TIPARCHIVE** fails in step **QARCHIVE** (`INT_DIVIDE_BY_ZERO`); recurs after DB refresh | data-dependent divide-by-zero in archive; QFC C++ fix | 2022.10 hotfixable; Reviewed Oct-2022; SF 22-00263789 |
| **#1458936** (core) | **PPAPNDPURG** job (purge PPAs marked "Do Not Process") **missing in Web** | migration miss — job not linked under Process Type screen in myQ; added (Core only, CAN n/a) | 2024.10 (iter 24.20) |

**Resolution recipe:** archive PK errors → check the archive definition's parent-table join (TSP joins for TSP-scoped archive groups, per #1454430) and the connection details (post-refresh). "Scheduled job won't start" is usually **QCloud/schedule-definition setup**, not code. Missing purge job in Web = Process-Type config (#1458936 added PPAPNDPURG to core). See the SF skill for the broader QARCHIVE family (#1650552 invalid column, #1460618 daily failure).

**Clients:** HPE/BBT, ENT, core.

---

<a name="h"></a>
## 10. Cluster H — Environment Provisioning & Post-Refresh

**The "broke after a refresh / on a new env" family — config/deployment, not allocation logic.**

- **TIPS API Host won't start (MSSQL):** after the SQL driver upgrade (SQLNCLI11 → MSOLEDBSQL), the API throws `KeyNotFoundException … GetDatabaseVendor` and the host stays down. The conflict: a **CAW data-sync process requires `DB_CON_STR_TYPE` to be NULL** on the **TIPSDSDataHelper** connection, but with it NULL the **TIPS APIs won't start**. — **#1617552** (orig fix), then **#1762912** (2025): the fix didn't populate `APIHost.config` correctly for OnPrem NI→CI; needed the **data-providers section added to `App.OnPremNI.Config`** (PRs 119xxx/120xxx, iter 25.23). *(Note: the cited "correct" fix would have been to make the CAW process not require NULL — see SF §10 Connection-Management .NET-vs-SQL family, 25-01016313/26-01065785.)* Found in Q testing → **no release note**. Builds: orig 2023.04+; resurfaced fix 2025.10 line. Clients: internal DEV (AHS), HPE Crude collateral.
- **Reseed identities/sequences (QDBMgr post-upgrade):** the QDBMgr "Reset Sequences" menu calls a synonym **`UTIL_RESEED_IDENTITIES_SYN`** that wasn't set up per-schema for any product, so reseed always failed (warnings "procedure … does not exist for CLIENTMNGD/ENGS/ARCVQTIP…"). — **#1589995** (AZR/Clearfork; built the proc/synonym across products; note the MSSQL script used `ALTER PROC` and failed where the proc didn't yet exist → use CREATE-OR-ALTER). **#1716447**: the new procs **don't work for Oracle** — `EXECUTE IMMEDIATE` strings carried trailing semicolons (double-semicolon syntax error) and **dropping/recreating sequences de-compiled triggers** that used them; fixed to update sequence values without drop/recreate. Hotfixed back to **2023.04 / 2024.04 (/2024.10)**; #1716447 merged **2023.04 and up** (iter 25.10). Wiki: "How-to-Resynch-Sequences" (QuorumSoftware.wiki/7100).
- **QPEC.ini ships unencrypted DB password:** deployed `QPEC.OnPremDirect.ini` `[Database]` section contained a plaintext DB password (present since the v17/ADO deployment transition); the section isn't even needed (QPEC manager passes connection info on the command line). Fix = remove the `[Database]` section from deployed QPEC.ini across products (eSuite, TIPS, QPTM, IPWS, QCM, QDOD, QGM). — **#1732358** (M&T, iter 25.17; mirrors upstream #1731941/#1731941).
- See also the SF skill's post-refresh items (connections pointing at PRD, missing facility configs, FTP paths) — those are SF-tracked operational cases; the ADO defects above are the *code/deployment* roots.

**Resolution recipe:** anything that broke right after a refresh/new-env → run the post-refresh checklist (connection strings/.NET-vs-SQL types, facility configs, paths), restart services, and for API-host/reseed/QPEC.ini check the client's build against the fixes above. These are **Cloud Ops / DevOps** owned, not allocation Engineering.

**Clients:** AZR/Clearfork, internal DEV/AHS/HPE Crude, M&T (all products).

---

<a name="i"></a>
## 11. Cluster I — Batch Config & Warning-Flood / Security-Metadata items

| Bug | Symptom | Root cause / fix | Build |
|-----|---------|------------------|-------|
| **#1757638** (core) | Running FIXEDFUELS floods warnings: "**No records found in Facility Configuration Settings table. Key Name = USE_FIXEDFUEL_SPLITS / SPLIT_ON_CTR. Key Group = FIXEDFUEL.**" on every run | the two plant configs are optional one-time setup; code shouldn't warn when absent. Fix = no warning regardless of config on/off | 2025.04 / 2025.10 (iter 25.22; `ClassicBatch hotfix/17.28.4, release/17.29.0`) |
| **#1736468** (DCP) | Facility batch **fails on FIXEDFUELS** → `Sel_MonthlyRunID` "Either BOF or EOF is True" | bad data when a new accounting month starts with a rerun month; **script** fix (no code) + a client stored-proc change to stop reintroducing it | client script; ties to #1690958 |
| **#1610587** (MKW) | **`sel_paystation`** reg SQL fails on FIXEDFUELS after #1573301 | new `@0ORDER_BY_TRNX_ID` param not set when the optional config `TRNX_ID_ORDER_BY_CLAUSE_IN_SEL_PAYSTATION` is absent → literal `NULL` appended to the SQL; set it to empty string | 2022.10 (Reviewed Oct-2023) |
| **#1749123** (EQC) | FBJS **STDPDA** step errors | core MSSQL regression: a #1737759 perf change split the query per-vendor and the **MSSQL branch dropped `MTR_NO`** (`QPDAWithoutNominations.QueryMeasVolSQL`); Oracle (ETP) unaffected. Add MTR_NO back | 2024.10 / 2025.04 (PR 116140/116141) |
| **#1408815** (SCT) | Web Import/Export Process: **IMPEXP ID param disappears** when tabbing off | QFC.Metadata reg-SQL layer change (per #256455) not committed | 2021.04 / 2021.10 TIPS metadata |
| **#1798373** (ENT) | TIPS/QPTM/eSuite **config screens let users edit metadata without security** | Web screens don't check code table **296 (QARCH_SEC_EDIT_METADATA)** / honor `ALLOW_EDIT_METADATA` / `ALLOW_EDIT_LOWER_LEVEL_METADATA` | 2026.04 (iter 26.09) |
| **#1769949** (ENT) | **GSWHALLOC** (MID Wellhead Allocation → TIPS) fails "transaction … completed but not yet disposed"; staging rows deleted, none inserted | client-specific ENT process timing/transaction issue when run without Production Month (too much data → timeout); workaround = run with TSP + Acct + **Prod Month** | client-specific hotfix 12/26/2025 (SF; L4-Investigated) |

**Clients:** DCP, MKW, EQC, SCT, ENT, core.

---

<a name="matrix"></a>
## 12. FIX-VERSION MATRIX

> IntegrationBuild was empty on all bugs. "Fixed-in" below is from iteration path (YY.NN) and PR target branches (`release/17.NN.0`, `hotfix/17.NN.x`). Treat as **inferred — confirm in release notes**. Rough line map: 2022.10≈17.22 · 2024.04≈17.21/17.26 lines (Maintenance hotfixes vary) · 2025.04≈17.27 · 2025.10≈17.28 · 2026.04≈17.29.

| Bug | Cluster | Symptom (1-line) | State | Fixed-in (inferred) | SF case |
|-----|---------|------------------|-------|--------------------|---------|
| #1774745 | A | System Manager false-flags restarted QPEC as Stopped/STPER | Closed/Verified | 2025.10/2026.04 line (platform #1780230 dep) | 25-01058663, 26-01065396 (related) |
| #1788585 | A | QPEC crashes from refresh storms / CPU exhaustion (infra) | Closed/Verified | infra mitigation, no code | — (RCA #1749170) |
| #1821239 | A | QPECs stuck in STPER; restart clears | Closed/Rejected | n/a | — |
| #1679048 | B | Master TIPS lock SQL: UNION→UNION ALL | Closed/Verified | 2024.04 | — |
| #1683233 | B | TIPSLOCK reallocation SQL further tuned | Closed/Verified | 2024.04 | — |
| #1725292 | B | TIPSLOCK 13–20 min on big plants (ETP) | Closed/Accept. | 2024.04 + hotfix | — |
| #1636859 | C | INACCTACCM query timeout; bypass split logic | Closed/Accept. | 2022.10+ | 23-00934008 |
| #1726948 | C | MEASANALYS hang; OPTION FORCE ORDER | Closed/Accept. | 2024.10/2025.04 | — |
| #1745358 | C | CTRMTR SQLID_INS_GATH_DEL_PAYSTATION timeout | Closed/Accept. | 2024.10 + hotfix 17.21.33/17.27.x | — |
| #1746523 | C | CTRMTR INS_GATH_REC_PAYSTATION timeout (pt2) | Closed/Accept. | 2021.04→2025.04 hotfixes | — |
| #1651744 | C | REGRVRSMAN LEFT JOIN→JOIN (DCP) | Closed/RFQ | 2024.04 | — |
| #1687619 | C | FIXEDFUELS m_Ins_Fixed_Fuels_Rev +62 min | Closed/Verified | 2024.04 hotfix + 2024.10 | — |
| #1095594 | C | SETTLE TOLERANCE rerun 2h (SEM CAN) | Closed/Verified | 2021.04 | — |
| #1783999 | C | Facility batch +44 min 2026.04 = DB speed | Closed/Rejected | n/a | — |
| #1607605 | D | Rerun jobs greyed in Web (Rerun Exclude) | Closed/Accept. | 2022.10/2023.04 | 23-00906527 |
| #1608023 | D | "No batch job sequence defined"; scheduler sync | Closed/Accept. | 2022.10/2023.04 | 23-00893815 |
| #1608737 | D | Company status Web≠Classic; Post fails from Web | Closed/Accept. | 2022.10/2023.04 | — |
| #1681736 | D | FBJS status grey after Settle | Closed/Accept. | 2022.10+ | 23-00905993 |
| #1687157 | D | "Run Next Job" wrong next process | Closed/Accept. | 2022.10/2024.04/2024.10 | 24-00942089 |
| #1649924 | D | "No sequence" error after posting | Closed | 2024.10 | — |
| #1429598 | D | CAN daily jobs not stopping on failure | Closed/RFQ | 2021.04 (17.17.3) | — |
| #1395314 | D | CANSPAWN stuck "Run All for Date Range" | Closed/RFQ | 2021.04 (17.17.2)/2021.10 | — |
| #1757579 | D | 2025.10 QAC FBJS: NVL in MSSQL path | Closed/RFQ | 2025.10 | — |
| #1617830 | E | TRNX_ID int→long long overflow (long-term) | Closed/RFQ | 2024.04+ (back-merge) | 23-00916530 |
| #1652993 | E | PDA step fails on large TRNX_ID | Closed/RFQ | 2024.07 | — |
| #1619944 | E | RECPURGE recycles TRNX_IDs (medium-term) | Closed/Accept. | 2020.03/2022.10/develop | 23-00923599 |
| #1639010 | E | PPA unapprove leaves orphan QTRAN_TRNX_ID | Closed/Accept. | 2022.10 hotfix + 2024.x | 23-00935744 |
| #1656405 | E | Daily CO TRNX_ID over-purged (m_DEL_MTR_TRNX_PPA) | Closed/Verified | 2024.07 | — |
| #1731166 | E | ASSOCIATED GAS LIFT METER VOL dup rows | Closed/Accept. | 2025.04 + hotfix 17.26.20/17.27.6/17.28.3 | — |
| #1640044 | E/F | SRB SUM-meter TRNX_ID collision on POST | Closed/Verified | client-specific (2024) | 23-00936172/24-00951618 |
| #1805171 | F | PK_QTRAN_IMBAL_ACCT_BAL on CUSTACCTBAL (post Patch#3) | Closed/Verified | 2025.04 Patch#3+ (still recurring) | 26-01097671 (26-01065143) |
| #1806658 | F | POSTPLANT JOURNAL dependency removed | Closed/Verified | client metadata (HEC) | 26-01099529 |
| #1767897 | F | DAILY SETTLE Sel_MonthlyRunID UNIT_TM_CD='M' | Closed/Accept. | 2025.04/2025.10 (hotfix 17.28.x/17.29.1) | 25-01056036 |
| #1689869 | G | QArchive PK error (missing TSP joins ARC_90_DAY) | Closed/Accept. | 2025.04 era (patch #1709778) | 24-00974423 |
| #1535066 | G | TIPARCHIVE INT_DIVIDE_BY_ZERO | Closed/Verified | 2022.10 | 22-00263789 |
| #1458936 | G | PPAPNDPURG job missing in Web | Closed/Accept. | 2024.10 | — |
| #1617552 | H | TIPS API host won't start (MSSQL, DB_CON_STR_TYPE NULL) | Closed | 2023.04+ | — |
| #1762912 | H | TIPS API host STILL won't start (APIHost.config) | Closed/Verified | 2025.10 (no release note) | — |
| #1589995 | H | Reseed identities fail (UTIL_RESEED_IDENTITIES_SYN) | Closed | 2023.04/2024.04 hotfix | — |
| #1716447 | H | Reseed procs broken on Oracle (semicolons/triggers) | Closed | 2023.04 and up (iter 25.10) | — |
| #1732358 | H | QPEC.ini ships plaintext DB password | Closed/Accept. | 2025.10 (iter 25.17) | — |
| #1757638 | I | FIXEDFUELS warning flood (USE_FIXEDFUEL_SPLITS/SPLIT_ON_CTR) | Closed/Accept. | 2025.04/2025.10 (hotfix 17.28.4/release 17.29.0) | — |
| #1736468 | I | DCP FIXEDFUELS Sel_MonthlyRunID BOF/EOF (data) | Closed/Verified | client script | — |
| #1610587 | I | MKW sel_paystation NULL appended | Closed/Accept. | 2022.10 | — |
| #1749123 | I | STDPDA MSSQL branch dropped MTR_NO | Closed/Accept. | 2024.10/2025.04 | — |
| #1408815 | I | Web IMPEXP ID param disappears | Closed/Accept. | 2021.04/2021.10 | — |
| #1798373 | I | Config screens bypass security (codetable 296) | Closed/RFQ | 2026.04 | — |
| #1769949 | I | GSWHALLOC transaction-disposed error (ENT) | Closed/Accept. | client hotfix 12/2025 | — |

---

<a name="diag"></a>
## 13. Diagnostic Pointers

- **Find the failing registered SQL:** `SELECT * FROM QARCH_QFCBATCH_SQL_TRACE WHERE PROCESS_QUEUE_ID = '<MasterPQID>' AND PROCESS_STEP_QUEUE_ID = '<stepQ>' ORDER BY SEQ_NO;` (compare a failed run's row count vs a good run — e.g. MEASANALYS good ≈ 80k rows, failed = 0, #1726948).
- **SQL-name → step → fix shortcut:**
  - `Select_ReallocDependTrnxIdProcessInd_Monthly` → TIPSLOCK/Master lock → UNION ALL / tuning (B).
  - `SQLID_INS_GATH_DEL_PAYSTATION` / `SQLID_INS_GATH_REC_PAYSTATION` → CTRMTR → FORCE ORDER (C, #1745358/#1746523).
  - `SQLID_ANL_STD_METERS` → MEASANALYS → FORCE ORDER (C, #1726948).
  - `INS_CTRL_REG_OTC_DTL_RECORDS` (`QSQL_TipsRevRegRvrslManAdj.cpp`) → REGRVRSMAN → JOIN not LEFT JOIN (C).
  - `Sel_MonthlyRunID` → daily SETTLE/FIXEDFUELS → monthly-run-id handling / bad data (F #1767897, I #1736468).
  - `SQLID_SSEL_QTRAN_FIXED_FUEL` → INACCTACCM → split-logic bypass / SPLIT_COUNT_INACCTACCM (C #1636859).
  - `m_DEL_MTR_TRNX_PPA` → RECPURGE/PPA → first-of-month join + Prod-Dt filter (E #1656405/#1639010).
- **QPEC false-stop check (System Manager):** `SELECT * FROM QCTRL_QPEC_MGR_MSG_LOG ORDER BY UPDT_DT DESC;` look for a "stopped unexpectedly" immediately after a restart (#1774745).
- **TRNX_ID exhaustion:** `SELECT sequence_name, last_number FROM dba_sequences WHERE sequence_name IN ('QTRAN_TRNX_ID_SQ','QTRAN_PAYSTATION_TRNX_ID_SQ');` — values approaching 2,147,483,647 imply the int-overflow defect (#1617830) if the client is unpatched.
- **Imbalance dup check:** `SELECT <PK cols>, COUNT(*) FROM QTRAN_IMBAL_ACCT_BAL GROUP BY <PK cols> HAVING COUNT(*)>1;` (also `QPOST_IMBAL_ACCT_BAL`) — #1805171/#1772117.
- **Repos:** `Quorum.TIPS.ClassicBatch` (registered SQL / C++ batch), `Quorum.TIPS.ClassicGUI` & `Quorum.TIPS.Web` (FBJS/CBJS UI + daily SETTLE), `<CLIENT>.TIPS.Metadata` (process/dependency config, e.g. `HEC.TIPS.Metadata`), QFC for platform pieces. Reseed wiki: QuorumSoftware.wiki page **7100** ("How to Resynch Sequences").

---

<a name="esc"></a>
## 14. Escalation: is the client build fixed?

1. **Identify cluster + SQL/constraint name** from the QPEC log (use §13).
2. **Find the bug** in the matrix; note the inferred fixed-in version.
3. **Compare to the client's running version.** Because every bug here is already *Closed*, the question is almost always *did the fix reach this client's build?* — confirm in release notes / the PR target branches noted per bug.
   - If the client is **on/after** the fixed-in version → it's a different issue (or a client-specific regression — check the `<CLIENT>.TIPS.Metadata` layer; e.g. #1749123 STDPDA, #1640044 SRB, #1769949/#1806658 ENT/HEC client procs).
   - If the client is **before** it → request a **hotfix** to their release line (these fixes were broadly back-ported: 2022.10 / 2023.04 / 2024.04 / 2024.10 / 2025.04, see PR branch lists).
4. **Route:**
   - **Engineering (Maintenance / Midstream):** registered-SQL/C++ defects (B, C, E, parts of F/G/I), Web↔Classic sync (D). Many carry tag `Maintenance: Escalated`.
   - **Cloud Ops / DevOps:** QPEC restarts & refresh storms (A), post-refresh & provisioning (H — API host, reseed, QPEC.ini, connections), archive scheduler setup (G #1689869).
   - **Client-specific (per-client patch, not a core build):** anything fixed in `<CLIENT>.TIPS.Metadata` or a client stored proc (#1640044 SRB, #1806658/#1769949 HEC/ENT, #1736468 DCP).

---

<a name="caveats"></a>
## 15. Classification & Overlap, Dead Ends, Caveats

**Overlap / mixed area paths.** Both queried branches (`Engineering\Midstream\*` and `Engineering\Maintenance\Midstream and Transportation\*`) hold **QPTM and TIPS** bugs (and some QGM/QCM/QDOD/IPWS, which are QPTM-family/transport products). The functional title filter (batch/process/QPEC/purge/archive/config/refresh/TRNX_ID/SFTP…) is broad, so it pulled many QPTM items. **Dropped as QPTM-only** (representative, by title): NNNOMLOAD / Nomination upload (#1664436, #1692624, #1754241, #1532428, #1779484, #1756194), Capacity Release / Unsubscribed Capacity (#1411874, #1638745, #1669924), RFS / Interconnect / CICO (#1673554, #1691561, #1547604, #1810055), EDI/NMST/Post-Noms (#123903, #177229, #1610415, #1611244), CRBIDEVAL/PALOCEXP/PBBALCHAIN/CAS (#1639052, #1639481, #1813346, #1816122, #1672548), and QGM/QCM/QDOD/IPWS-prefixed items. A handful are genuinely **shared platform** (e.g. #1732358 QPEC.ini password and #1798373 security-metadata touch QPTM+TIPS+eSuite together — kept, flagged as shared).

**QPEC ambiguity.** "QPEC" appears in both products' batch frameworks. I kept QPEC items only where the body/area was TIPS (TIPS lock, TIPS env, QRMTIPS DBs) and dropped QPEC items that were clearly QPTM/QGM (e.g. IPWS QPEC crashes #207997, myQ batch QPEC #172781 marked "not product-specific").

**Caveats / honesty notes.**
- **No IntegrationBuild anywhere** → every "Fixed-in" is *inferred* from iteration path + PR target branch and must be confirmed in release notes. The `hotfix/17.NN.x` branch numbers are reliable as *evidence a fix shipped to that line* but don't map 1:1 to a customer-facing "2024.04.x" label without the release-notes lookup.
- **Some "Bugs" are infra/ops, not code:** #1788585, #1821239 (QPEC crashes — DB refresh placement / CPU), #1689869 (scheduler setup), #1736468/#1640044 (data scripts). Treat the *cluster behavior*, not the work-item type, as the signal.
- **Rejected items** (#1783999 DB-speed; #1804647 single-user-only; #1821239) are kept in the matrix marked Rejected so you don't re-chase them as code defects.
- **Client-specific fixes** in `<CLIENT>.TIPS.Metadata` / client stored procs will never appear in a core build — confirm the per-client patch.
- One work item (**#1769948**, a typo neighbor of #1769949) returned empty — not a real bug; the real one is #1769949 (GSWHALLOC).
- Deep-read sample = ~40 of 1,176 matched; clusters cover the recurring TIPS-batch/QPEC/env families but are **not exhaustive** of all 1,176 (the long tail is mostly one-off client SQL/data scripts and the dropped QPTM items).

---

*Skill created 2026-06-14 from Azure DevOps Bugs (QuorumSoftware). WIQL matched 1,176 Closed/Resolved bugs; ~40 deep-read with full comment threads + linked PRs. Bug IDs cited: A #1774745/#1788585/#1821239; B #1679048/#1683233/#1725292; C #1636859/#1726948/#1745358/#1746523/#1651744/#1687619/#1651730/#1095594/#1783999; D #1607605/#1608023/#1608737/#1681736/#1687157/#1649924/#1429598/#1395314/#1757579/#1804647; E #1617830/#1652993/#1619944/#1639010/#1656405/#1731166/#1640044; F #1805171/#1806658/#1767897; G #1689869/#1535066/#1458936; H #1617552/#1762912/#1589995/#1716447/#1732358; I #1757638/#1736468/#1610587/#1749123/#1408815/#1798373/#1769949. Cross-product platform deps: #1780230, #1454430, #1709778. Companion: SKILL_TIPS_Batch_Processing.md (SF-mined operational recipes).*
