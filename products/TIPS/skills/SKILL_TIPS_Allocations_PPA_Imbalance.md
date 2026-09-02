# SKILL: TIPS Allocations / PPA / Imbalance Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-11 | **Product:** My Quorum TIPS (oil/gas transaction & accounting)
**Use When:** Any TIPS case in categories Allocations, Allocation Maintenance, PPA Framework, PPA (CAN), Imbalance(s) — failed Facility Batch Jobs (MEASUREMENT → ALLOCATE → SETTLE → POSTRESULT), allocation group / Volume Assembly Rule problems, PDA Submission / Meter Split issues, PPA approve/un-approve/advance failures, imbalance not calculating or duplicating, customer-account-balance issues, allocation/imbalance reports.
**Companion:** For QPTM-side allocation (ALALLOCATE, PTR overlay to QPTM) see **SKILL_Allocations.md**. Evolution clients (TIPS↔QPTM) appear in both; TIPS is the plant/settlement side.

> Evidence base: 962 closed TIPS cases in this category group. 207 actionable (Software Defect 119, Application Configuration 78, ChangeConfig 10) were mined in full (subjects + resolutions), plus a 30-case sample of Training/Customer Error cases for the Expected-Behavior section. Every root-cause claim cites a real SF case and/or ADO work item observed during mining. 185 closed cases carry no Root_Cause__c and were not mined.

---

## TABLE OF CONTENTS

1. [Quick Triage](#1-quick-triage)
2. [TIPS Allocation Pipeline Concepts](#2-tips-allocation-pipeline-concepts)
3. [Decision Tree](#3-decision-tree)
4. [Duplicate / Orphan Rows → Constraint Failures in Batch (HIGH FREQUENCY)](#4-duplicate--orphan-rows--constraint-failures)
5. [EFF_PCT_CONTR / Numeric-Precision Overflow on ALLOCATE](#5-eff_pct_contr--numeric-precision-overflow)
6. [Allocation Group / Volume Assembly Rule / Facility Definition Config](#6-allocation-group--volume-assembly-rule--facility-definition-config)
7. [PDA Submission / PDA Import / Meter Split](#7-pda-submission--pda-import--meter-split)
8. [PPA Framework (Approve / Un-approve / Advance / Rebook)](#8-ppa-framework)
9. [Imbalance Calculation & Posting](#9-imbalance-calculation--posting)
10. [Web (myQuorum) Screen & Picklist Defects](#10-web-myquorum-screen--picklist-defects)
11. [Batch Performance / Hangs / Services](#11-batch-performance--hangs--services)
12. [Time-Slices & Integration Sync (QCM ↔ TIPS)](#12-time-slices--integration-sync)
13. [Reports & Statement Views](#13-reports--statement-views)
14. [Expected Behavior / User Education FAQ](#14-expected-behavior--user-education-faq)
15. [Database Tables & Process Steps Reference](#15-database-tables--process-steps-reference)
16. [Diagnostic SQL](#16-diagnostic-sql)
17. [Known ADO Items](#17-known-ado-items)
18. [Escalation Guidance](#18-escalation-guidance)

---

## 1. Quick Triage

| Symptom | Likely cause | First check |
|---------|--------------|-------------|
| Facility Batch Job fails: "Violation of PRIMARY KEY constraint" / "unique constraint" (TRNX_ID, PAYSTATION, QPTMSTAGPERMWHALLOC) | Duplicate/orphan transactional rows, usually from **overlapping effective-date time slices** on meter or contract header | §4; `SEXTN_MTR_HEADER_QRMTIPS` / `SEXTN_CTR_HEADER_QRMTIPS` overlap query (§16-B) |
| Imbalance doubled / dup rows in `QTRAN_IMBAL_ACCT_BAL` | Known defect, fixed in **2025.04 patch #3**; dups created pre-patch need a delete script | §4b; dup-check SQL (§16-C); ADO #1772117 |
| ALLOCATE fails at MONVOL: "negative EFF_PCT_CTR" / "ERROR SETTING VALUE FOR COLUMN EFF_PCT_CONTR" | Column `NUMBER(14,10)` overflow — huge contract split % from a **displacement PDA** when measured ≪ scheduled | §5; ADO #1580084 (fixed 2023.04+) |
| Recoveries / theoretical NGL / fuel wrong for some days only | Allocation-group **Volume Assembly Rule basis resolves to 0** (e.g. WHDV=0 with gas lift), wrong disposition, or Unit of Timing mismatch | §6; review the alloc group rules + basis for the bad days |
| PDA won't save / validates wrongly in Web (works in Classic) | Web PDA validation defect (agent timeslices, 100% leak, meter-split gaps) | §7; reproduce in Classic; check patch level |
| Can't approve / un-approve a PPA | COMMENTS > 4000 chars (un-approve), Seq-No-null insert (approve), or overlapping contract time slice | §8 |
| PPA ran but volumes/components missing | PPA Advance copying from wiped `QTRAN_ALLOC_POINT` CPWD rows, or meter-split change didn't trigger PPA | §8 |
| Imbalances missing from Customer Account Balance after close | **POSTRESULT ran prematurely** (missing batch dependency) — reprocess as PPA | §9 (25-01021133) |
| Imbalance widget / screen empty | Integration Synchronizer module not checked; picklist target-table wrong | §9 / §10 |
| Sporadic gas days flip to 0 imbalance, fixed on next nightly run | Rounding bound check — global config `PROGRESSIVE_ROUNDER_NO_BOUND_CHECK` | §9 (24-00985175) |
| Web screen blank / picklist empty / decimals truncated (Classic OK) | myQuorum Web metadata/picklist defect | §10 |
| Batch jobs hang, "Bootstrap" / SendMessageAndWaitForResponse errors | Process timeout config or stuck QPECS/middle-tier services | §11 |
| Allocations stop after a contract/meter change | Time-slice gap/overlap, QCM↔TIPS contract end-date mismatch, meter not end-dated | §12 |
| Report total wrong but transactional data correct | Registered view defect (reversals, conversion factors, date logic) | §13 |

---

## 2. TIPS Allocation Pipeline Concepts

- TIPS allocates **plant/facility volumes** (wellhead → plant products: residue, NGLs, condensate) per **accounting month (Acct Dt)** and **production month (Prd Dt)** via **Facility Batch Jobs** (screen: Facility Batch Job Submittal). Canonical step order: **MEASUREMENT → ALLOCATE (MONVOL/DAYVOLS/ASSCGLM/PSWHALLOC/PLNTPERF...) → SETTLE → POSTRESULT** (then imbalance/statements/invoices). Step order and dependencies are config (`QCODE_BATCH_JOB`, process-step metadata) — wrong order is a recurring root cause (25-01021133, 24-00943813).
- **Allocation Groups** define how a facility's volume is split: allocation type (e.g. DERMTRATTR), **Volume Assembly Rules** (user-defined formulas), an **Allocation Rule/basis** that must resolve to a **positive number** or nothing calculates, **disposition codes** (WHDV, NDD, MESR, GLFT...), **Unit of Timing** (Daily vs Monthly), and **subsequence** (run order between groups).
- **PDA (Predetermined Allocation)** + **Meter Split** + **Contract Meter List (CML)** drive contractual allocation. A **displacement PDA** absorbs the nom-vs-measured difference — source of the EFF_PCT_CONTR overflow (§5).
- **PPA (Prior Period Adjustment)**: rerun of a closed production month in a current accounting month. PPA Approval / un-approval gates rebooking. **PPA Advance** copies prior-run results forward. Closing an accounting month is **irreversible** — corrections go through PPA (26-01064442).
- **Imbalance**: nominated/confirmed vs allocated per contract → `QTRAN_IMBAL_ACCT_BAL` / activity detail → Customer Account Maintenance/Balance, cashout. Imbalance types & **CICO** (carry-in/carry-out) indicator are code-table config.
- **Reallocation Mode**: per-facility flag that forces re-allocation of posted days; leaving it on interacts badly with nightly jobs and ASSCGLM (24-00968763, ADO #1731166). Core step **CLREALLOC** (2021.04+) clears it (22-00679870).
- **Evolution clients** (ETP/Enterprise, EQT): TIPS plant results feed QPTM (PTR). Reruns of Evolution PPA months can hit staging constraint errors (24-00976492) — see SKILL_Allocations.md §7 for the QPTM side.

---

## 3. Decision Tree

```
TIPS Allocations/PPA/Imbalance case
│
├─ A Facility Batch Job step FAILED with an error?
│   ├─ "PRIMARY KEY / unique constraint" → §4 (dup/orphan rows, overlapping time slices)
│   ├─ "EFF_PCT_CONTR / negative percent contributed" → §5 (precision overflow / displacement PDA)
│   ├─ "From point volumes missing" → §14 (meter time-slice missing — usually setup)
│   ├─ "Bootstrap"/"SendMessageAndWaitForResponse"/no error text, job hangs → §11 (timeouts/services)
│   └─ Step ran out of order / missing dependency (POSTRESULT early) → §9 / §12 (job config)
│
├─ Volumes ALLOCATED but WRONG (recoveries, theo NGL, fuel, gas lift, splits)?
│   ├─ Only some days wrong → §6 (alloc rule basis = 0 those days; timing mismatch)
│   ├─ Doubled volumes → §4 (ASSCGLM/realloc dups) or §6 (two alloc groups active for same period)
│   └─ Wrong contract gets volume → §7 (PDA/meter split/CML) or §12 (contract time slice)
│
├─ PPA problem? → §8 (approve/un-approve/advance/rebook defects)
│
├─ Imbalance problem?
│   ├─ Missing after close → §9 (POSTRESULT dependency → reprocess as PPA)
│   ├─ Duplicated → §4b (QTRAN_IMBAL_ACCT_BAL defect)
│   └─ Calculating wrong / not at all → §9 (imbalance type / CICO / code tables / realloc ind)
│
├─ Web screen behaves differently from Classic? → §10 (Web defect; workaround = Classic)
│
├─ Report wrong but data right? → §13 (view/report defect)
│
└─ "How do I…" / setup confusion → §14 (expected behavior / training)
```

---

## 4. Duplicate / Orphan Rows → Constraint Failures

The single most damaging cluster (~12 actionable cases). Facility Batch Jobs die on PK/unique-constraint violations because transactional tables contain duplicates or orphans — almost always traceable to **overlapping effective-date time slices** on meter/contract master data, or a process re-inserting on rerun/reallocation.

### 4a. Patterns and verbatim fixes
| Error / symptom | Root cause | Fix | Case / ADO |
|-----------------|-----------|-----|------------|
| "Violation of PRIMARY KEY constraint" on TRNX_IDs (meter 1449959B) | **Overlapping time slices** in `SEXTN_MTR_HEADER_QRMTIPS` + `QCTRL_MTR_ATTR_FLAT` | Data script to correct the overlapping slices; SQL-log analysis to find mismatching eff dates | 23-00935563 |
| ALLOCATE fails for a scheduling month; orphan rows | `QTRAN_ALLOC_POINT` rows tied to **nonexistent TRNX_ID** | Delete orphans (verbatim SQL in §16-A) | 22-00527472/22-00527476 (Equitrans) |
| PPA errors "duplicates when inserting into pay station" (PAYSTATION_QDOD) | **Overlapping contract-header time slice** in `SEXTN_CTR_HEADER_QRMTIPS` (CTR PAM043600A, 10/2024) | Script to correct the overlapping slice | 25-01002372 (IACX) |
| Gas-lift volumes duplicated; records not purged | **ASSCGLM** (Associated Gas Lift Meter Vol) step creates duplicates in `QTRAN_ALLOC_VOL` when run for dailies with plant in **reallocation mode** | Code fix: DELETE existing `process_id='ASSCGLM'` rows before insert | 25-01023169; ADO **#1731166** (Closed) |
| Evolution PPA month rerun: "Unique constraint error QPTMSTAGPERMWHALLOC" | Staging table re-insert on plant rerun (TIPS→QPTM staging) | Code defect (Evolution staging) | 24-00976492 (ETP) |

### 4b. The `QTRAN_IMBAL_ACCT_BAL` duplicate epidemic (Hilcorp/HEC)
Recurring 2025-2026 incident chain: duplicated rows in `QTRAN_IMBAL_ACCT_BAL` / `QPOST_IMBAL_ACCT_BAL` break the imbalance process and Customer Account Balance.
- Root cause bug: ADO **#1772117** (Closed) — code fix shipped in **2025.04 patch #3** (25-01061774).
- Dups created **before** the patch still had to be deleted by script — repeated Script Deployments: **#1772095/#1772687** (Dec 2025), **#1776936** (Jan 2026), **#1778789** (Jan 2026) — cases 25-01060242, 26-01065143, 26-01068169, 26-01097671.
- Related sync bugs: **#1699412** (GNM CAW `QTRAN_IMBAL_ACCT_BAL` not syncing, Closed), **#1701884** (Proposed), **#1768683** (HVK table not populated, Ready for Review).

**Fix recipe:** (1) run dup-check SQL §16-C; (2) confirm client patch level vs 2025.04 patch #3; (3) if dups predate the patch → request delete script via Script Review/Deployment (Cloud Ops); (4) re-run the imbalance process.

---

## 5. EFF_PCT_CONTR / Numeric-Precision Overflow

ALLOCATE fails on the **MONVOL** step with "negative EFF_PCT_CTR" or "ERROR SETTING VALUE FOR COLUMN EFF_PCT_CONTR". The contract-split percent column is `NUMBER(14,10)` and overflows when the split percent is enormous.

**Mechanics (verbatim from 24-00952247, Momentum):** a **displacement PDA** absorbs (scheduled − measured). With measured volume = 1 and scheduled = 10,000 on a day, the displacement contract's percent-contributed explodes past the column max → batch error.

| Case | Detail |
|------|--------|
| 23-00923463 / 23-00923877 (Equitrans) | MONVOL fail, value −11999. Long-term fix = widen `EFF_PCT_CONTR` `NUMBER(14,10)` → `NUMBER(16,10)` per ADO **#1580084** — **available 2023.04+, too risky to patch back**. Workaround: raise the measured volume or lower scheduled volumes so the displacement qty shrinks. |
| 24-00994961 (Enterprise) | Same family: widened `S_DECIMAL` `NUMBER(14,10)` → `NUMBER(16,10)` in `QTRAN_PAYSTATION`. |
| 24-00952247 (MOM) | `PCT_CONTR numeric(14,10)` — patch required; data workaround as above. |
| 25-01002874 (Pembina) | WIO% on meter split rounding wrong — missing data-type cast; fix `CAST(... AS NUMERIC(14,10))` to match `S_DECIMAL` precision. |
| 26-01100384 | Negative percent contributed from negative propane volumes — worked around by setting the batch step to **continue processing on error** (root product issue separate). |

**Fix recipe:** identify the day(s) and meter with tiny measured vs large scheduled qty; either correct the volumes (data workaround) or confirm version ≥ 2023.04 for the column fix. For one-off runs, "continue on error" unblocks the job but leaves the bad day unallocated.

---

## 6. Allocation Group / Volume Assembly Rule / Facility Definition Config

Biggest **Application Configuration** cluster (~16 cases). Volumes allocate, but wrongly — and only under specific data conditions.

| Symptom | Root cause | Resolution recipe | Case |
|---------|-----------|-------------------|------|
| C2-C4 recoveries/producer payment too high on one meter, fine elsewhere | Liquid alloc groups (LIQCHAPSPC, CALCTH*) used **WHDV MCF as Allocation Rule basis**; days with gas lift where WHDV=0 → basis 0 → Volume Assembly Rules silently skip those days → partial month allocates | Create derived product/disposition **WH/WHGL = WH/WHDV + WH/GLFT** for all settlement meters; new Allocation Rule on WH/WHGL; repoint the liquid groups | 24-00964001 (ETP Carlsbad) |
| Volumes duplicated by ND allocations | Alloc groups referenced wrong/old disposition | Update groups + formulas to new disposition **NDD** (net delivered daily) | 23-00921745, 23-00934453 (Crestwood) |
| Custom daily imbalance report won't tie out | Two alloc groups (50013FUEL vs 50013F) had **different Unit of Timing** (Monthly vs Daily) → slightly different dailies | Set both groups to Monthly timing + add Gathering Category for FFCU | 22-00829463 (EQT XL) |
| Total volume wrong | Alloc-group **subsequence** wrong: group BMG-991 ran before DERNETGL though it computes the total the other consumes | Reorder subsequence | 23-00920299 (Brazos) |
| Theoretical ethane/NGL wrong | Wrong Allocation Rule type | Change rule to "THEORETICAL GALLONS ON GROSS VOLUME"; rerun measurement→settle | 23-00923045 |
| Natural Gasoline wrong | Facility Definition product mapping used C5+ instead of IC5+NC5; or heat value not recalculated | Fix Facility Definition components (25-01011404); set alloc group to recalc Heat Value from Gallons (25-01027694) | HMEP STX |
| Residue mismatch between two plants on TO/TI meters | Facility Definition **Residue Theoretical** tab deductions inconsistent | Align deductions (Res/FPP vs Condensate) across both plants | 22-00867460 (DCP) |
| CHKNEGVOL errors (negative liquid volumes) | Negative components reaching settle | Allocation group to zero out negative liquid volumes + override inventories | 26-01086773 (Pivotal/Bantry) |
| Duplicate allocation in PPA | **Two monthly SPLIT alloc groups active for the same period** | Correct the allocation-group timeline (end-date one) | 26-01089308 |
| Alloc groups missing From Point attribute | Ref data | Update `QCTRL_ALLOC_GRP_FROM_PT_ATTR` | 23-00935285 |
| Fuel allocated on wrong basis | Basis on the group | Facility > Allocation Group > change fuel basis MCF → MMBTU | 25-01002531 |

> **Rule of thumb:** "right total, wrong split / some days zero" is almost always the **Allocation Rule basis or disposition** on the group — check what the basis resolves to on the bad days before suspecting code.

---

## 7. PDA Submission / PDA Import / Meter Split

~14 cases; heavily **Web-vs-Classic** (same theme as QPTM). The Web PDA/meter-split screens either over- or under-validate.

| Issue | Root cause | Fix | Case / ADO |
|-------|-----------|-----|------------|
| PDA Submission fails validation when there's an **agent** change between timeslices (Classic OK) | `QTIPSValidationPDASubmission0021_MtrCtrBaRelatedAndEffectiveRange` compared against agents from prior PDA timeslices → false effective-date gaps | Code fix: validate against update agents for the same SR contract + BA | 24-00952959 (ONEOK); related #1611693 |
| **PDA Import** fails when Contract Header's open-ended timeslice isn't the active one | Validation `return false` aborted instead of `continue` | Code fix | 22-00818967 (Harvest) |
| PDA validation triggers on **normal gaps in Meter Split** | Web validation defect | Code fix | 22-00679913 (Harvest) |
| PDA "must equal 100%" **validation leak** in Web | Web-only gap (Classic enforces) | Code fix | 22-00676428 (Harvest) |
| Can't add meter split row in Web: validation error | **Orphaned record in `QCTRL_MTR_SPLIT_HDR`** — Web validates differently | Update/clean the record via Classic (different validation path) or script | 22-00529683 (Utah Gas) |
| Meter Split errors when meter-suffix blank on new setup | Web defect | Code fix | 23-00915506 (ONEOK) |
| Volumes go to 0 on allocation of noms | **Meter split for the contract = 0** | Fix the split (or use Imbalance Volumes for the requirement) | 25-01056537 (HMEP) |
| Nom/Conf overrides an "Apply w/o Nom" PDA | Monthly-splits precedence defect | Code | 22-00831859 (Merit) |
| Allocation stopped after end-dating a PDA | A required PDA row was missing/deleted | Re-add/delete the bad PDA for the meter | 24-00984071 |
| External user gets "Update access rights" error updating PDA | External-user security config | Config | 24-00966145 (Genesis) |

**Triage:** always reproduce in **both** Web and Classic. If Classic works, it's a known class of Web defect — check patch level first (e.g. 26-01091817: fix existed in 2025.04.1.4+, client PRD was on .3; workaround = do it in Classic).

---

## 8. PPA Framework

~16 cases. Three sub-patterns: approval/un-approval blockers, PPA Advance data loss, and PPA-not-triggered.

| Issue | Root cause | Fix | Case / ADO |
|-------|-----------|-----|------------|
| **Cannot un-approve PPAs** — concatenate error | `COMMENTS varchar2(4000)` overflow when appending un-approval comments | Script to **clear/trim the comments**, then un-approve; long-term SQL fix restricts to 4000 chars. KB: ka0UG0000002dDNYAY | 24-00990256 → 24-00991302 (DCP) |
| **Cannot approve contractual PPA** | `ValidateAndInsertPPARecords()` inserted NULL into non-nullable auto-increment Seq No on `QCTRL_PPA_MTR_DTL` | Code fix: `AddRows` → `AddRowsIgnoreNulls` | 22-00823678 (Utah Gas) |
| **PPA Advance: sales volumes/components not allocated** | Another process wiped **CPWD entries in `QTRAN_ALLOC_POINT`** before posting; PPA Advance couldn't copy them | Code fixes: nonop-split ignores reversal transactions (prevents doubling); PPA-Advance RECPURGE filtered on `unit_tm_cd` | 22-00570825 / 22-00570847 (Pembina) |
| PPA doesn't insert into Measured Volumes | Web `PPAMeasVolPending` grid not synced with Measured Volume screen grid | Ported Classic sync logic to Web | 22-00815433 (Utah Gas) |
| Meter-split update **did not trigger a PPA** | Trigger gap — a trivial re-save creates it | Make a small update to the split to force the PPA | 22-00529632 (Utah Gas) |
| PPA errors at PAYSTATION/QDOD step | Overlapping contract-header time slice | Script (§4a) | 25-01002372 |
| Permian PPA populates 0 for reinstated PTR (Evolution) | PTR reinstatement defect | Code (Evolution) | 24-00984585 (ETP) |
| Can't run plants for PPA months prior to Evolution date | **Batch-job job-code sequence** wrong for ARM | Resequence job codes within the batch job | 24-00943813 (ETP) |
| PPAs won't rebook | Version defect | Patch via premium support | 22-00655436 (Pioneer) |
| PPA Framework config error adding new contract | Fixed by version upgrade | Upgrade | 24-00964879 (Genesis) |
| PPA Approval screen returns no results / search takes ~52s (2025.10) | Screen defect / perf regression | ADO **#1760521** (Closed), **#1762417** (Proposed) | ONEOK 24-00941958 (older) |

---

## 9. Imbalance Calculation & Posting

~12 cases, mostly **Application Configuration**.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| **Imbalances missing from Customer Account Balance after close** | **POSTRESULT ran prematurely — missing batch dependency** | Fix the process dependency; **reprocess PA as a PPA** for the prod month to restore/post imbalances | 25-01021133 (HMEP) |
| Random past gas days flip to imbalance 0, self-heal next nightly (`QRPTS_ALLOC_VOL_GATH_CTGRY`) | Allocation rounding bound check | Set global config **`PROGRESSIVE_ROUNDER_NO_BOUND_CHECK` = 1** (verify expected results; this changes system-wide rounding behavior) | 24-00985175 (ETP); same key used for EQT 25-00996960 |
| Gathering allocation skips s_decimal when allocated slightly > physical (>1.00000) | Rounding-check tolerance | Update the **allocation rounding check in global config** so pcr contr is caught when slightly over 1.00000 | 26-01068082 (M6) |
| Daily imbalance report not picking up data after a date | **Reallocation checkbox left on** for facilities → nightly job zeroes records | Uncheck reallocation for those facility/dates | 24-00968763 (Merit) |
| CICO rate / carry-in-carry-out not applied | Imbalance type missing **CICO indicator** | Turn on CICO ind for the imbalance type (code table) | 25-01006116 (HMEP) |
| Contracts point to **non-existing imbalance type** | Stale code-table reference | Update imbalance-type code tables to a valid option | 23-00906022 (Crestwood) |
| Imbalance widget error | "Quorum Imbalance" group not checked in **Integration Synchronizer Module Setup** | Check it | 24-00942692 (Genesis) |
| Imbalances not calculating correctly (one-off) | **NOMPOST job ran simultaneously** with the imbalance run → updates failed | Re-update noms, rerun processes | 22-00516114 (Merit) |
| Estimated fuel not available in Sched/Pre-Sched month (AL01R) | Code-table config for estimated fuels | Code-table change, test in UAT, promote | 23-00935467 (Third Coast) |
| Whole imbalance module producing wrong balances | **Module set up incorrectly at implementation** | Beyond support — Services engagement (quote) | 25-01048219 (Hilcorp) |
| Imbalance duplicates | See §4b | — | 25-01061774 etc. |

---

## 10. Web (myQuorum) Screen & Picklist Defects

Largest defect cluster by raw count (~20 cases incl. an 8-case MarkWest picklist batch from one upgrade project). Pattern: data is correct in DB; the Web screen/picklist/metadata mis-renders. **Workaround is almost always Classic; fix is a patch.**

| Issue | Fix | Case |
|-------|-----|------|
| Tract Part Percentage rounds to 2dp in Web (Classic 8dp) | Removed hardcoded decimal formatting; metadata 2→8 dp for "Tract Part Percentage" & "Participation Basis" (Unit Definition > Tract tab) | 23-00914042 (ONEOK) |
| Allocated Quantity Query (AQQ) screen returns nothing in Web | Screen defect — patch | 24-00953417, 24-00952546 |
| Attribute formulas broken in Web (NULL not accepted / not working) | Missing space in formula-construction logic; later regression patched | 22-00815478 (Utah Gas), 25-01035964 (Steel Reef) |
| Customer Account Maintenance filter popup errors | Picklists **28007/28008** target-table repointed `QTRAN_INV_ACCT_ACTIVITY_DTL_VW` → **`QTRAN_INV_ACCT_ACT_DTL_VW_2`** | 22-00530944 (ETP) |
| Alloc Group Preferential-Detail meter picklist shows non-physical meters | Use picklist **53068** (physical meters only) on the Web grid | 22-00570815 (Pembina) |
| Alloc Group Maintenance "Alert" error on retrieve | Added missing **custom sysgen object** | 23-00893822 (MarkWest) |
| Upgrade-project picklist batch: Contract Header/Ticket Maintenance/Shared Meter View/Contract Rates/Contract Meter List/Gathering Attributes | Per-picklist metadata fixes during 2022.10/2023.04 upgrades | 23-00893832…-840 (MarkWest) |
| Imbalance Volume bulk copy loses dependent column values | Web grid defect | 22-00818967-era (22-00818778 Crestwood) |
| Imbalance web-only bug, PRD behind UAT patch | Fix in **2025.04.1.4+**; workaround = Classic until patched | 26-01091817 (Hilcorp) |
| Post Settle Indicator bug; "Bucket" column missing on Contract Rates (Web) | Patches | 25-01035013, 23-00906889 |

---

## 11. Batch Performance / Hangs / Services

~10 cases. Before deep-diving: **was anything actually wrong with the data, or did the job just hang/timeout?**

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Company Batch Jobs timeout | **Splitting logic adds huge overhead when no splitting configured** | Workaround: raise **split count** (e.g. 6) so splits run in parallel; long-term code bypass when splitting absent | 23-00934008 (MOM) |
| "Internal Program (Bootstrap) Error" in Allocate | Segregated-process timeout too low | Allow timeout increases via app.config | 22-00598140 (ONEOK) |
| STDPDA `SendMessageAndWaitForResponse` error | Messaging timeout | Raise **ShortWaitForMessageDelay**; longer-term QFC fix | 22-00603621 (ONEOK) |
| Facility jobs error at random / Revenue Override errors | Stuck services | Restart **QPECS** / TIPS Middle Tier | 22-00516203, 22-00516176, 24-00941960 |
| Allocate fails on PLNTPERF step | Bad RUN ID | Delete the bad Run ID via the application | 22-00526779 (EQT XL) |
| General production slowness | Infra/DBA review; server resources increased | Cloud Ops ticket | 25-01050441 (M6) |
| Patches missing after project; long processing | Redeploy patches; restart services | 26-01091115 (Scout) |

---

## 12. Time-Slices & Integration Sync (QCM ↔ TIPS)

~10 cases. TIPS master data is time-sliced everywhere; QCM (contracts) and Flowcal/measurement integrate in.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Contract not allocating for new months | **QCM contract end-date tied to MTR SFX CD** out of sync with TIPS noms | Set contract end date in QCM (e.g. 4/1/2021–3/31/2026), then create the deliver nom for the new slice in TIPS | 26-01100512 (Inter Pipeline) |
| Total fuel calc wrong for months | Meters went inactive but were **never end-dated in TIPS** | End-date the meters | 23-00885707 (DT Midstream) |
| MPO upload won't create new time slice | Import skips when slice falls **within an existing slice** (by design) | End-date the existing timeslice first, then import | 22-00854448 (NorthRiver) |
| Classic Meter Definition time-slicing stopped | Integration Synchronizer Setup: TIPS_METERS group's **Integrate Group** checkbox unchecked | Re-check it | 22-00830758 (Crestwood) |
| Factor-ID script created bad slice | Prior slice's `Eff_Dt_To` not closed before daily-config switch | Corrective script (QBS13) | 24-00964978 (ETP) |
| Measured volumes skipped for a day | `QCODE_BATCH_JOB` Measurement/Allocate **indicator settings** drifted from standard | Reset `QCODE_BATCH_JOB` config | 23-00892066, 22-00874359 (MOM) |
| TIPS not receiving data from QPTM (warning) | Evolution sync defect | Code | 24-00972258 (ETP) |
| Meters missing from imbalance after conversion | TRANSPOOL meter missing from **conversion scripts** | Add meter + fix cutover scripting | 23-00877993 (MOM) |

---

## 13. Reports & Statement Views

~8 cases. Confirm the **underlying transactional data is correct first** — it usually is; the registered view or report logic is wrong.

| Report / view | Issue | Fix | Case |
|---------------|-------|-----|------|
| Settlement statements | Same production date on all statements despite PPAs | Modify `QPOST/RPTS_SETTLE_GAS_STMT_VW` to **exclude reversals**; Crystal shows `PROD_DT` not `STATUS_PROD_DT` | 24-00958086 (Opportune) |
| Imbalance Statement | Wrong accounting date | Report logic picked **first day of week** instead of first of month | 25-00999876 (HMEP) |
| Operations Summary NGL | Inconsistent results | **Conversion factors in the view** were patched incorrectly; corrected in next update | 26-01084648 (Inter Pipeline) |
| External daily report (RPT_23922) | External users see wrong days | `TIPSUPDATE` (in TIPSUNLOCK) didn't set last-completed-job when TIPSMASTER uses **CANSPAWN** | 22-00691546 (NorthRiver) |
| Allocate L&U report | Zeros for some meters | Report only accepts `FLOW_DIR='D'` (delivery) meters — tie delivery meter to contract in PDA + Meter Split | 24-00970501 (Merit) |
| 102B Allocation Group in Order of Allocation | Group name duplicated in headers | Report fix | 22-00642284 (Keyera) |

---

## 14. Expected Behavior / User Education FAQ

From the Training/Customer Error sample (~238 such closed cases in this group). Recognize these before scripting/escalating.

| Reported as | Reality | Case |
|-------------|---------|------|
| "Fuel deductions still appear after end-dating the Meter Split" | Meter Split only defines contractual splits/split sources. To remove a meter from allocation you must **also remove it from the Contract Meter List** | 26-01088373 |
| "Master meter allocation used stale data" | MEASUREMENT for month N uses month N-1 production **only if POSTRESULT for N-1 ran first** — job ordering, not a bug | 26-01085981 |
| "Accidentally closed the accounting month" | Irreversible. Path forward = **PPA** for the desired production month | 26-01064442 |
| "ALLOCATE error: From point volumes missing" | Meter has no active time slice for the period — add a new timeslice and rerun | 26-01093548 |
| "Contract missing from Customer Account Maintenance picklist" | Must add the contract via the **unscoped** picklist + correct account type, then run imbalance; that ties it to the account | 26-01096131 |
| "Can't cancel/run a daily batch job for the whole month in Web" | Web runs daily jobs **day-by-day** by design | 26-01084583 |
| "Need two cash-out methods on one contract" | Not supported — one cash-out method per contract; set up separate contracts | 26-01065991 |
| "Plant won't balance / flare or NGL off" | Almost always a **measured-volume entry anomaly** — find the outlier day/meter and correct it | 26-01093092, 26-01087345 |
| "New DERMTRATTR allocation group not working" | Setup error — verify allocation type + disposition (MESR) + rules | 26-01087046 |
| "Meter ownership change not taking" | Meter lives on **Shared Meter screen**, not Meter Split | 26-01091751 |

---

## 15. Database Tables & Process Steps Reference

### Tables (all observed verbatim in case resolutions)
| Table | Purpose / failure mode |
|-------|------------------------|
| `QTRAN_ALLOC_POINT` | Allocation point transactions; **orphans vs `QTRAN_TRNX_ID`** kill ALLOCATE; CPWD rows feed PPA Advance |
| `QTRAN_ALLOC_VOL` | Allocated volumes; **ASSCGLM duplicates** (gas lift + realloc mode) |
| `QTRAN_TRNX_ID` | Transaction master — orphan-check anchor |
| `QTRAN_PAYSTATION` | Settlement pay station; `S_DECIMAL`/`EFF_PCT_CONTR` precision failures; PAYSTATION_QDOD dup inserts |
| `QTRAN_IMBAL_ACCT_BAL` / `QPOST_IMBAL_ACCT_BAL` | Imbalance account balances — **duplicate-row defect** (fix 2025.04 patch #3) |
| `QTRAN_IMBAL_ACCT_ACTIVITY_DTL` (+`QPOST_`) | Imbalance activity; `ACCT_ACTIVITY_DTL_ID` widened to 19 digits (ADO #1724474) |
| `SEXTN_MTR_HEADER_QRMTIPS` / `SEXTN_CTR_HEADER_QRMTIPS` | Meter/contract header time slices — **overlap = constraint violations downstream** |
| `QCTRL_MTR_ATTR_FLAT` | Meter attribute flat — pairs with meter-header overlap fixes |
| `QCTRL_MTR_SPLIT_HDR` | Meter split header — orphans block Web saves |
| `QCTRL_PPA_MTR_DTL` | PPA meter detail — Seq-No-null insert bug on approval |
| `QCTRL_ALLOC_GRP_FROM_PT_ATTR` | Allocation group from-point attributes |
| `QCODE_BATCH_JOB` | Batch job step/indicator config — drift breaks measurement/allocate pickup |
| `QARCH_CTRL_PROCESS_STEP` / `QARCH_CTRL_PROC_PROCSTEP` (metadata repos) | Process-step definitions (ASSCGLM etc.) — live in `<CLIENT>.TIPS.Metadata` repos |
| `QRPTS_ALLOC_VOL_GATH_CTGRY` | Gathering-category reporting layer (rounding flips to 0) |
| `QTRAN_INV_ACCT_ACT_DTL_VW_2` | Correct picklist target for Customer Account Maintenance filters |
| `QPOST/RPTS_SETTLE_GAS_STMT_VW` | Settlement statement view (reversal exclusion fix) |

### Process steps / jobs (Facility Batch Job family)
`MEASUREMENT` → `ALLOCATE` (sub-steps `MONVOL`, `DAYVOLS`, `ASSCGLM`, `PSWHALLOC`, `PLNTPERF`) → `SETTLE` → `POSTRESULT`; plus `NOMPOST`, `RECPURGE`, `STDPDA`, `CLREALLOC` (clears realloc mode, 2021.04+), `TIPSMASTER`/`TIPSUNLOCK`/`TIPSUPDATE` (job-state bookkeeping; CANSPAWN interaction), `CHKNEGVOL` (negative-volume check). Global config keys seen: `PROGRESSIVE_ROUNDER_NO_BOUND_CHECK`, `ShortWaitForMessageDelay`, allocation rounding check.

### Repos
Client overrides/metadata: `<CLIENT>.TIPS.Metadata` (e.g. DCP, IAC, VMH — confirmed via code search), `IPF.TIPS.*`, plus client web/app artifacts (e.g. `EQC.QPTM.Application.QPEC` for Evolution DLL routing, 25-00998540).

---

## 16. Diagnostic SQL

### A. Orphan allocation points (verbatim from 22-00527472)
```sql
SELECT * FROM QTRAN_ALLOC_POINT P
LEFT JOIN QTRAN_TRNX_ID T ON p.trnx_id = t.trnx_id
WHERE t.trnx_id IS NULL;
-- Fix = delete the orphan QTRAN_ALLOC_POINT rows (script via Cloud Ops), rerun ALLOCATE.
```

### B. Overlapping contract/meter header time slices (shape verbatim from 25-01002372)
```sql
SELECT * FROM QRMTIPS.SEXTN_CTR_HEADER_QRMTIPS
WHERE CTR_NO = '<CTR_NO>' ORDER BY eff_dt_from DESC;
-- Look for a slice whose eff_dt_from falls before the prior slice's eff_dt_to.
-- Same check on SEXTN_MTR_HEADER_QRMTIPS (+ QCTRL_MTR_ATTR_FLAT) for meter-driven PK errors (23-00935563).
```

### C. Duplicate imbalance balance rows (the §4b epidemic)
```sql
SELECT <natural key cols: ctr/meter/acct dt/prod dt/imbal type>, COUNT(*) dup_ct
FROM   QTRAN_IMBAL_ACCT_BAL
GROUP BY <same cols>
HAVING COUNT(*) > 1;
-- Verify exact key against the client schema. If dups exist and patch level < 2025.04 #3 → delete script + patch.
```

### D. Duplicate gas-lift allocation rows (ASSCGLM, 25-01023169 / ADO #1731166)
```sql
SELECT <meter/prod day/product cols>, COUNT(*)
FROM   QTRAN_ALLOC_VOL
WHERE  PROCESS_ID = 'ASSCGLM'
GROUP BY <same cols> HAVING COUNT(*) > 1;
```

### E. Batch-job step/indicator config drift (23-00892066)
```sql
SELECT * FROM QCODE_BATCH_JOB WHERE <client/facility scope>;
-- Compare Measurement/Allocate indicator settings against a known-good environment.
```

> Column-name caveat: table names above are verbatim from case resolutions; some key-column lists are inferred — confirm against the client schema before scripting. All destructive fixes go through ADO Script Review/Script Deployment, wrapped in a transaction with a verify-SELECT.

---

## 17. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|-------|--------------|-----------------|---------|---------|
| **#1580084** | Bug / **Closed** | EFF_PCT_CONTR column needs increase (Facility Allocate errors) — fix in **2023.04+**, not back-patchable | §5 | 23-00923877, 22-00875229 |
| **#1731166** | Bug / **Closed** | ASSCGLM creates duplicates for dailies when plant in reallocation mode (DELETE-before-insert fix) | §4 | 25-01023169 |
| **#1772117** | Bug / **Closed** | HEC root cause: duplicated records in QPOST/QTRAN_IMBAL_ACCT_BAL — fix in **2025.04 patch #3** | §4b | 25-01060242, 25-01061774 |
| **#1772095 / #1772687 / #1776936 / #1778789** | Script Deployments / **Closed** | Delete duplicates from QTRAN_IMBAL_ACCT_BAL (UAT/PRD, Dec 2025–Jan 2026) | §4b | 26-01065143, 26-01068169 |
| **#1723573** | Bug / **Closed** | Imbalance sequence QTRAN_IMBAL_ACCT_ACTIVITY_D_SQ too large for column | §4b | 25-01014345 |
| **#1724474** | DB Change / **Closed** | ACCT_ACTIVITY_DTL_ID widened to 19 (QTRAN+QPOST activity dtl) | §4b | 25-01014345 |
| **#1699412** | Bug / **Closed** | GNM — CAW QTRAN_IMBAL_ACCT_BAL not syncing | §4b/§9 | — |
| **#1701884** | Bug / **Proposed** | CTRAN_IMBAL_ACCT_BAL not syncing from QTRAN_IMBAL_ACCT_BAL | §4b/§9 | — |
| **#1768683** | Bug / **Ready for Review** | HVK — QTRAN_IMBAL_ACCT_BAL not being populated | §4b/§9 | — |
| **#1556909** | Bug / **Closed** | AZR Formula Schedule Rule not working — **"caused collateral, do NOT patch"**; resolved via hotfix #1570632 + patch #1569733 + package #1571551 | §9 | 22-00824610, 22-00874369 |
| **#1611693** | Bug / **Closed** | MKW — Unable to save on PDA Submission screen | §7 | 23-00911394 |
| **#1760521** | Bug / **Closed** | PPA Approval search perf (~52s) in 2025.10 | §8 | — |
| **#1762417** | Bug / **Proposed** | PPA Approval search still slow | §8 | — |
| **#1757579** | Bug / **Closed** | 2025.10 beta — Facility Batch Jobs failing (QAC plant) | §11 | — |
| **#1777919** | Bug / **Closed** | IPF — CAN Facility Batch Job screen honor setup & display status | §10 | 26-01067772 |
| **#1751116** | Bug / **Proposed** | EQC — meters WITHOUT a PPA showing on invoice | §8 | — |

---

## 18. Escalation Guidance

```
Is it a DEFECT → Engineering (bug WI), CONFIG → Cloud Ops / consultant, or SERVICES-scope?

→ Engineering (raise/attach to a Bug WI):
   - Constraint-violation patterns matching §4 where master data is clean (e.g. ASSCGLM dups, IMBAL_ACCT_BAL dups
     at patch < 2025.04 #3, Evolution staging QPTMSTAGPERMWHALLOC)
   - EFF_PCT_CONTR overflow on version < 2023.04 (#1580084) — patch/upgrade conversation, NOT a data bug
   - Web ≠ Classic behavior (screens, picklists, validations) — cite the screen + both behaviors; check patch level first
   - PPA approve/un-approve code paths (Seq-No null, comments concat) — script workaround exists, fix is code

→ Cloud Ops (Script Review → Script Deployment):
   - Orphan/duplicate-row clean-ups (§16-A/C/D) — always with a verify-SELECT and scoped WHERE
   - Overlapping time-slice corrections (SEXTN_*_HEADER_QRMTIPS, QCTRL_MTR_ATTR_FLAT)
   - Services restarts (QPECS / Middle Tier), timeout raises, patch redeployments, env refreshes

→ Config (you / client admin can fix):
   - Allocation group rules/basis/disposition/timing/subsequence (§6)
   - Imbalance type + CICO indicators, Integration Synchronizer checkboxes, QCODE_BATCH_JOB indicators
   - Global config keys (PROGRESSIVE_ROUNDER_NO_BOUND_CHECK — warn: system-wide rounding impact)

→ Services engagement (quote), not support:
   - Module fundamentally misconfigured at implementation (e.g. whole imbalance setup — 25-01048219)
   - Reconfiguration projects (producer-split migrations, new plant gas-lift config)

→ User education (§14): job ordering (POSTRESULT before MEASUREMENT), CML vs Meter Split,
   closed-month = PPA, day-by-day Web jobs, measured-volume entry errors.
```

---

*Skill created: 2026-06-11 from 962 closed SF cases (207 actionable mined in full + 30-case Training/Customer Error sample) and ADO items #1580084, #1731166, #1772117, #1772095/#1772687/#1776936/#1778789, #1723573, #1724474, #1699412, #1701884, #1768683, #1556909/#1570632/#1569733/#1571551, #1611693, #1760521, #1762417, #1757579, #1777919, #1751116.*
*Caveats: 185 closed cases have no Root_Cause__c (unmined); ~30 actionable cases have terse/null resolutions ("Defect", "Resolved" — e.g. 24-00976492 has a Software-Defect classification but a null Resolution__c); where a cluster's fix was not explicit in the data it is marked rather than invented. Category field uses both 'Imbalance' and 'Imbalances' spellings — query both. A handful of cases cited above for narrative continuity are NOT in the 207-actionable set because SF classifies them under Training / Business Change / Customer Error rather than Software Defect/App Config/ChangeConfig (25-01060242 = Business Change; 26-01065143 = Business Change AND category 'Processing', not an allocation category; 26-01097671 & 26-01089308 = Customer Error; 26-01100384 & 25-00996960 = Training) — the underlying defects they describe are nonetheless backed by genuine Software-Defect cases (e.g. the IMBAL_ACCT_BAL dup epidemic via 25-01061774 + ADO #1772117; the EFF_PCT_CONTR overflow via 24-00952247 + ADO #1580084). Counts re-verified 2026-06-13: 207 actionable (Software Defect 119 / Application Configuration 78 / ChangeConfig 10) of 962 closed in-group; Training 152, Customer Error 86, null 185.*
