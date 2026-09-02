# SKILL: QPTM Confirmations & Scheduling (CAS) Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-01 | **Product:** QPTM (My Quorum Gas Pipeline)
**Scope:** The two downstream legs of the nomination lifecycle —
- **Confirmations** — a downstream/upstream party confirming the nominated quantity: Confirmation Response & Confirmation Summary screens, AutoConfirm (CFAUTOCONF), confirmation deadlines, EPSQ (scheduled-qty-for-operator), confirmation cut/bump logic.
- **Scheduling / Capacity Allocation Scheduling (CAS)** — turning confirmed noms into **scheduled quantities**: nomination classification (CANOMCLTG), CAS Maintenance screen, cut/reduction when capacity-constrained, path balancing (PBBALCHAIN), cut notices & sched-qty reports (CAX/CARPTS), allocation of capacity by priority of service.

**Companion skills (do not duplicate):**
- **SKILL_EDI_Troubleshooting.md** — cycle deadlines / `PACTRL_CYCLE_DEADLINE`, inbound NMST, outbound NMQR/OACY EDI, ENMQR error codes. For *confirmation deadline* and *EDI confirmation files* config, cross-reference there.
- **SKILL_Nominations.md** — nom submission/validation, duplicate/overlap "ghost noms", nom-delete scripts (Templates A/B), AutoGen, MDQ/fuel. Confirmation & CAS both consume nom rows produced there; "nom not showing in Conf Response" is often a §Nominations ghost-nom.

> **Evidence base:** ~585 closed combined SF cases (Confirmations + Scheduling (CAS) + Capacity Allocation Scheduling (CAS)) under `Product_list__c = 'My Quorum Gas Pipeline'`. The actionable subset mined here = **181 cases** (Root Cause = Software Defect 64, Application Configuration 59, Customer Error 26, Training 32). Every root-cause claim cites a real SF case # and/or ADO work item. Category each pattern came from is tagged **[CONF]**, **[SCHED]**, or **[CAS]**.

---

## TABLE OF CONTENTS

1. [Quick Triage Checklist](#1-quick-triage-checklist)
2. [Concepts: Confirmation & Scheduling Pipeline](#2-concepts-confirmation--scheduling-pipeline)
3. [Symptom → Root-Cause Matrix](#3-symptom--root-cause-matrix)
4. [Capacity / Segment / Path / Rate Config — CAS won't run/classify (HIGHEST VOLUME)](#4-capacity--segment--path--rate-config--cas-wontrunclassify-highest-volume)
5. [Confirmation Response Screen (bump / confirm-qty / display)](#5-confirmation-response-screen-bump--confirm-qty--display)
6. [Confirmation Summary / Cycles Mismatch](#6-confirmation-summary--cycles-mismatch)
7. [AutoConfirm (CFAUTOCONF)](#7-autoconfirm-cfautoconf)
8. [EPSQ — Scheduled Quantity for Operator](#8-epsq--scheduled-quantity-for-operator)
9. [Path Balancing (PBBALCHAIN)](#9-path-balancing-pbbalchain)
10. [CAS Maintenance Display / Flow-Qty (doubled / graphical)](#10-cas-maintenance-display--flow-qty-doubled--graphical)
11. [Cut Logic — not cutting / override / ratchet / rounding](#11-cut-logic--not-cutting--override--ratchet--rounding)
12. [Nomination Classification (CANOMCLTG)](#12-nomination-classification-canomcltg)
13. [CAS Run / Batch Failure (rate mismatch, timeout, loading)](#13-cas-run--batch-failure-rate-mismatch-timeout-loading)
14. [Cut Notices & Sched-Qty Reports (CAX / CARPTS / CF67 / SQOP)](#14-cut-notices--sched-qty-reports-cax--carpts--cf67--sqop)
15. [Key Code Files & Repos](#15-key-code-files--repos)
16. [Database Tables Reference](#16-database-tables-reference)
17. [Diagnostic SQL Queries](#17-diagnostic-sql-queries)
18. [Known Historical ADO Bugs](#18-known-historical-ado-bugs)
19. [Expected Behavior / User Education](#19-expected-behavior--user-education)
20. [Escalation Decision Tree](#20-escalation-decision-tree)

---

## 1. Quick Triage Checklist

```
[ ] 1. Which leg — CONFIRMATION (confirming a nom qty) or SCHEDULING/CAS (cutting/scheduling)?
[ ] 2. Which TSP_NO, pipeline/zone, and segment/location involved?
[ ] 3. Which gas day(s) and cycle (Timely / Evening / ID1-3)?
[ ] 4. Which screen/process — Confirmation Response, Confirmation Summary, CAS Maintenance,
       or a batch (CANOMCLTG, CFAUTOCONF, CFPSTRESP, PBBALCHAIN, CARPTS, CAALLUNCAP)?
[ ] 5. Does CAS RUN at all, or does it run but produce WRONG numbers? (different clusters — §13 vs §10/§11)
[ ] 6. Is this an implementation/UAT/conversion client (REX/Ruby/TREX, ECGS, SOC) or steady-state PRD?
       (~half of Scheduling cases are TREX/REX buildout config — §4)
[ ] 7. Web or Classic? Several Confirmation defects are web-vs-classic display mismatches.
[ ] 8. Internal or External (shipper/operator) user? External query/confirm rights differ.
[ ] 9. Did a nom or rate change just before the issue? (CAS reads classified noms + rates)
[ ] 10. QPTM version (2022.10, 2023.04, 2024.04, 2025.04)? Many fixes are version-gated/back-patched.
```

### Where does it live?
| Symptom | Cluster | First place to look |
|---------|---------|---------------------|
| CAS won't run / classify; noms/TOS not showing in CAS | §4, §13 | Location Path Maint, segment/path config, `RTCTRL_RATE_HDR/DTL` mismatch |
| Confirm qty wrong, bump not saving, can't query | §5 | `QUIControllerConfirmationResponse.cs`; web-vs-classic |
| Conf Summary cycles ≠ Conf Response | §6 | Confirmation Summary screen config / cache |
| AutoConfirm over-cutting / not running | §7 | `CFAUTOCONF` config + service health |
| EPSQ only in ID3 / EPSQ=0 unexpectedly | §8 | `PACTRL_CYCLE.GAS_FLOW_START_TIME_OFFSET` |
| Cuts unbalanced / CBLs on paths | §9 | `PBBALCHAIN`, `ALL_PATH_IND` on CFPSTRESP |
| CAS flow qty doubled / graphical wrong | §10 | concurrent-retrieve defect; dup Location Path Maint rows |
| CAS cutting incorrectly / override / rounding | §11 | `QSchedulingReductionSeg`, capacity, POV, ratchet |
| Cut notice/report not generating/attaching | §14 | `CARPTS`, `RPT_CAX*`, report scheduling |

---

## 2. Concepts: Confirmation & Scheduling Pipeline

### The lifecycle (where this skill sits)
```
Nominate (SKILL_Nominations) ─▶ CONFIRM ─▶ CLASSIFY ─▶ SCHEDULE/CUT ─▶ ALLOCATE/REPORT
                                 (CONF)     (CANOMCLTG)   (CAS / PBBALCHAIN)   (CAX/CARPTS)
```
1. **Confirmation** — the confirming party (downstream operator/upstream party) accepts or reduces the nominated qty. Output = a **confirmed quantity**. Drives the Confirmation Response & Summary screens and outbound confirmation EDI.
2. **Nomination Classification (CANOMCLTG)** — classifies each nom by contract/TOS/path into firm-primary, firm-secondary, IT, etc. **CAS cannot see/cut a nom until it is classified.** Most "nom not in CAS" cases are a classification or path/segment-config gap.
3. **CAS (Capacity Allocation Scheduling)** — compares classified, confirmed volumes against available **capacity** per segment/location; when over capacity it **cuts/reduces** by priority of service (POV/rank). Output = **scheduled quantity**.
4. **Path Balancing (PBBALCHAIN / CFPSTRESP)** — rebalances both ends of a path after a cut so receipts = deliveries.
5. **Reports / Notices (CARPTS, CAX*, CF67, SQOP)** — cut notices and scheduled-quantity reports to shippers/operators; outbound OACY/scheduled-qty EDI (see EDI skill).

### Key batch processes (memorize)
| Process | Role | Cluster |
|---------|------|---------|
| `CANOMCLTG` | Nom Classification & Trans Grouping (feeds CAS) | §12 |
| `CFAUTOCONF` | Auto-confirm nominations | §7 |
| `CFPSTRESP` | Post confirmation response / balancing | §5, §9 |
| `PBBALCHAIN` | Path balancing chain | §9 |
| `CARPTS` | CAS reports / cut-notice generation | §14 |
| `CAALLUNCAP` | Allocate uncapacitated / CAS allocation | §4 |
| `CANOM` | CAS nom job (rate/res-com classification) | §4, §12 |

---

## 3. Symptom → Root-Cause Matrix

| Symptom | Most common root cause | Fix type | Evidence |
|---------|------------------------|----------|----------|
| CAS won't run / errors out when running on a new pipeline (REX/Ruby) | Segment/path/default-path or **rate header↔detail mismatch** | Config / data script | 23-00930041, 23-00930211, 23-00936155, 23-00897056 |
| Noms / a TOS (LTPC, FSS) not displayed in CAS | TOS/segment/path classification config gap | Config | 24-00936577, 23-00925715, 23-00936167, 24-00937202 |
| CAS Flow Qty **doubled** | Two users retrieving CAS Maint simultaneously, OR duplicate Location Path Maint rows | Code fix / delete-dupes script | 24-00973852, 23-00927006, 24-00966311, 25-01055876, 25-01017371 |
| CAS not cutting correctly / cuts unbalanced | Capacity/POV/ratchet config or scheduling-reduction defect | Config / code | 25-01022326, 23-00881417, 24-00940500, 22-00536889 |
| Confirm Response lets you confirm **above** the nom | Validation gap on confirmed qty | Code fix #1695520 | 24-00985949 |
| Confirmed subsequent cuts don't hold after nom change | Confirmation persistence defect | Code fix #1744837 | 25-01032374 |
| EPSQ only applies in ID3 / EPSQ=0 unexpectedly | `PACTRL_CYCLE.GAS_FLOW_START_TIME_OFFSET` NULL for ID1/ID2 | Config (set offset) | 24-00982666, 26-01088719 |
| Conf qty differs web vs classic | Web/classic display defect | Code fix | 23-00910509 |
| Conf Summary cycles ≠ Conf Response; summary timeouts | Summary screen defect/perf | Code fix | 22-00620259, 22-00630594, 22-00609359 |
| CFAUTOCONF cutting extra volumes every cycle | AutoConfirm cut defect | Code fix (hotfix) | 22-00874403, 22-00875195 |
| AutoConfirm batch not running | Service/infra (needs restart) | Infra | 26-01087210, 25-01010281 |
| AUTOCONF fails after TSP Copy | TSP Copy script missing column | Script fix | 23-00905756 |
| PBBALCHAIN cuts across contract holders when Agent noms | Agent-nom service-requester rights config | Config | 24-00972503, 24-00972508 |
| Cut notice / CAS report not generating/attaching PDF | Report config / CARPTS defect | Config / code | 24-00957577, 23-00918900, 22-00828342, 23-00891527 |
| Path Balancing zeroing LNG plant qty | Balancing defect | Critical hotfix #1670362 | 24-00963500 |

---

## 4. Capacity / Segment / Path / Rate Config — CAS won't run/classify (HIGHEST VOLUME)

**This is the single largest cluster (36 actionable cases, ~24 Application Configuration).** It is overwhelmingly an **implementation / UAT / conversion** problem on pipelines being stood up or re-modeled — **REX/Ruby (TREX), TPC, ECGS, SOC**. The recurring theme: CAS can only schedule what it can *see and classify*, so any gap in segment definition, location path, default path, virtual segment, TOS labeling, or **rate data** makes noms invisible to CAS or makes the run fail outright.

### Sub-patterns & fixes
| Sub-pattern | Root cause | Fix | Case |
|-------------|-----------|-----|------|
| Can't path noms through a (virtual) segment / add a segment to default path | Default-path / virtual-segment config incomplete | Config in segment/default-path maint | 24-00954182, 24-00944523, 24-00944164, 24-00937202 |
| A TOS not showing in CAS (LTPC, FSS, Cap-Release) | TOS not classified / not labeled with flow type | Config (TOS flow-type, classification) | 23-00925715, 23-00936167, 24-00955391, 24-00951166 |
| Noms not displaying / not all noms in CAS | Location path / classification gap | Config (Location Path Maint) | 24-00936577, 25-01017371, 23-00933598 |
| CAS not cutting/scheduling correct capacity | Capacity values or capacity-type (primary/secondary) config | Config | 25-01022326, 25-01022469, 25-01022467, 26-01088716 |
| CAS won't **run** at all for the pipeline | Segment/path setup incomplete OR **rate mismatch** (see §13) | Config / data script | 23-00936155, 23-00905163, 24-00953159 |
| Doubling/tripling volumes for segments & locations | Duplicate Location Path Maint rows | **Delete-dupes data script**, re-run CANOMCLTG | 25-01055876, 24-00966311, 25-01017371 |
| Missing initial setup after conversion | Conversion setup gaps (ECGS, SOC) | Config / data script | 24-00950168, 26-01085907, 26-01089630 |

### Verbatim config fixes captured
- **25-01017371 [CAS]** "noms not coming correctly through PITTSEG": *"Removed the row in location path maintenance for the pool meter 080038 and north inventory meter 080036."* → extra Location Path Maint rows duplicated the path.
- **24-00966311 [CAS]** doubling CAS & EBB volumes: a customer (Joe Williams) created **duplicate Location Path Maintenance rows**; a script deleted the dupes, then **CANOMCLTG** was re-run and CAS values corrected. (Root cause = Customer Error, fix = data script.)
- **26-01088716 [CAS]** "CAS not scheduling based on IT rates": *"toc object maintenance for res and com to CANOM batch job"* — TOC object maintenance (res & com) had to be wired into the CANOM job.
- **23-00902424 [SCHED]** Ruby CAS classifications inaccurate: resolved by **Ruby Zone** changes.

### Diagnostic
```sql
-- Is the nom classified at all? (CAS only sees classified noms)
SELECT TSP_NO, NOM_ID, GAS_DAY, CYCLE_ID, CLASS_CD, TOS_CD, SEG_NO, CTR_NO, SCHED_QTY
FROM CACTRL_CLASS_NOM            -- classified-nom table (verify name in client schema)
WHERE TSP_NO = <TSP_NO> AND GAS_DAY = '<GAS_DAY>' AND CYCLE_ID = <CYCLE>;

-- Is the location/segment on a valid path? (duplicate rows = doubled volumes)
SELECT TSP_NO, LOC_ID, SEG_NO, PATH_ID, FLOW_IND, BACK_FLOW_IND, EFF_DT_FROM, EFF_DT_TO, COUNT(*)
FROM NNCTRL_LOC_PATH             -- Location Path Maintenance backing table
WHERE TSP_NO = <TSP_NO> AND LOC_ID IN ('<LOC1>','<LOC2>')
GROUP BY TSP_NO, LOC_ID, SEG_NO, PATH_ID, FLOW_IND, BACK_FLOW_IND, EFF_DT_FROM, EFF_DT_TO
HAVING COUNT(*) > 1;             -- >1 = duplicate path rows (25-01017371, 24-00966311 pattern)
```
> **Always:** confirm CANOMCLTG (classification) ran cleanly **before** blaming CAS. An unclassified nom is the #1 reason a nom "isn't in CAS."

---

## 5. Confirmation Response Screen (bump / confirm-qty / display)

Largest Confirmations cluster (30 actionable; SD 5, AC 9, CE 9, TR 7 — i.e. **half are user/training/config**, not defects). The Confirmation Response screen is where the operator enters confirmed/cut quantities and bumps.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Screen lets you confirm a qty **above** the nomination | Missing upper-bound validation | **Code fix — Bug #1695520 (Closed)** | 24-00985949 |
| Confirmed subsequent cuts don't hold after a nom change | Persistence defect on subsequent-cycle cuts | **Code fix — Bug #1744837 (Closed)** | 25-01032374 |
| Confirm qty displays differently web vs classic | Web/classic render defect | Code fix | 23-00910509 |
| Max Qty became less than Confirmed Qty | Max-qty recompute defect | Code fix | 22-00603767 |
| Bumping qty not updating after save | Save/refresh behavior — usually expected/training | Education / config | 26-01069228, 24-00957957 |
| Both sides of nom balanced after a cut (unexpected) | Balancing config on confirm | Config | 23-00889729 |
| External user can't query Conf Response | External-user data-scope config | Config | 23-00933936, 23-00930383 |
| Exclude-Confirmed-Loc checkbox not working (Classic) | Classic screen defect | Code fix | 22-00603662 |
| Sort / contact-popup / PPA-popup not working | Minor UI / customer-side | Education / config | 24-00963195, 22-00598000, 22-00591433 |
| Infinite loading / page-not-responding on Conf Response | Perf/render defect (large data) | Code fix | 25-01014361, 22-00697906 |

### Diagnostic
```sql
-- Confirmed quantities for a gas day / cycle (compare to nominated)
SELECT TSP_NO, NOM_ID, GAS_DAY, CYCLE_ID, LOC_ID, NOM_QTY, CONF_QTY, DIFF_QTY,
       REDUCTION_REASON_CD, CONF_LEVEL_CD, UPDT_DT, USER_ID
FROM CFCTRL_CONF
WHERE TSP_NO = <TSP_NO> AND GAS_DAY = '<GAS_DAY>' AND CYCLE_ID = <CYCLE>
ORDER BY LOC_ID, NOM_ID;
-- CONF_QTY > NOM_QTY without authorization = the #1695520 scenario.
```

---

## 6. Confirmation Summary / Cycles Mismatch

Lower-volume, almost entirely **defects** (4 SD) — the Confirmation Summary screen is a roll-up that historically drifted out of sync with the per-line Confirmation Response.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Cycles on Conf Summary ≠ Conf Response | Summary aggregation defect | Code fix | 22-00620259 |
| Confirmation Summary timeouts | Summary query performance | Code fix | 22-00630594 |
| Data not in Web Confirmation Summary | Web summary population defect | Code fix | 22-00609359 |
| Summary screen not in menu | Menu/metadata config | Config | 22-00609342 |

> Several of these were dispositioned together via a **2021.04 urgent support hotfix** (22-00875195). When a client reports a Summary-vs-Response mismatch, check their version against the hotfix.

---

## 7. AutoConfirm (CFAUTOCONF)

AutoConfirm auto-applies confirmed quantities so operators don't hand-confirm every nom.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| CFAUTOCONF **cutting additional volumes** unexpectedly every cycle | AutoConfirm cut defect | **Code fix (hotfix)** | 22-00874403, 22-00875195 |
| AutoConfirmation batch not working | Service/infra hang | **Full service restart** (QPECs, Servers, Web, MT) | 26-01087210 |
| AUTOCONF fails after annual **TSP Copy** | TSP Copy script missing a column reference | Fix the TSP Copy script | 23-00905756 |
| New AutoConf setup / config | Standard config | Config | 24-00940832 |

> **Triage tip:** "AutoConfirm stopped" with no config change → suspect **service health first** (26-01087210 was fixed purely by restarting QPECs/MT/Web). "AutoConfirm cutting too much" → defect (22-00874403).

---

## 8. EPSQ — Scheduled Quantity for Operator

EPSQ (the operator's scheduled/confirmed quantity) is gated by the cycle's gas-flow-start timing. **The recurring defect/config:** EPSQ only fires in ID3 (or returns 0) because the **`GAS_FLOW_START_TIME_OFFSET` on `PACTRL_CYCLE` is NULL for earlier cycles**, so the engine has no flow-start anchor for ID1/ID2.

- **24-00982666 [CONF]** "EPSQ needs to apply in all cycles (currently only ID3)": *"Updated Gas Flow Start time (PACTRL_CYCLES) for ID1 and ID2 to trigger a non-NULL value in database."*
- **26-01088719 [CAS]** "EPSQ to 0 when expecting an error" — **verbatim fix script:**

```sql
-- Source (verbatim, case 26-01088719): set the cycle gas-flow-start offset so EPSQ evaluates.
-- Values are this client's seconds-offsets (43200 = 12h for ID2/cycle 4; 28800 = 8h for ID1/cycle 3).
-- Confirm the correct CYCLE_ID→cycle mapping for the TSP before applying.
UPDATE PACTRL_CYCLE
SET GAS_FLOW_START_TIME_OFFSET = '<OFFSET_SECONDS>'   -- e.g. 43200
WHERE CYCLE_ID = '<CYCLE_ID>';                         -- e.g. 4

UPDATE PACTRL_CYCLE
SET GAS_FLOW_START_TIME_OFFSET = '<OFFSET_SECONDS_2>'  -- e.g. 28800
WHERE CYCLE_ID = '<CYCLE_ID_2>';                        -- e.g. 3
```
> Always verify the existing offsets first (`SELECT CYCLE_ID, GAS_FLOW_START_TIME_OFFSET FROM PACTRL_CYCLE WHERE TSP_NO=<TSP_NO>`) and that a NULL/zero offset is actually the cause before updating.

---

## 9. Path Balancing (PBBALCHAIN)

After a cut, path balancing rebalances both ends so the path nets out. 8 actionable cases; a mix of config and a critical defect.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Path Balancing **cutting LNG plant qty to zero** | Balancing defect | **Critical out-of-cycle hotfix — Requirement #1670362 (Closed, HOTFIX, 2024.04)** | 24-00963500 |
| PBBALCHAIN cuts across multiple contract holders when an **Agent** nominates | Agent-nom service-requester rights | Config: assign Agent **full service-requester rights** / use the **service requester DUNS** | 24-00972508, 24-00972503 |
| CAS cuts leaving unbalanced paths | `ALL_PATH_IND` not set, OR balancing-timing expectation | Config + education | 22-00536889 |
| PBBALCHAIN produces CBLs on PT-model paths in testing | Test used **ATT** locations (not real scenario) | No action (not reproducible in prod) | 24-00976439 |

### Verbatim config note (22-00536889 [SCHED], Customer Error)
> *"The `ALL_PATH_IND` should be set to 1 for `CFPSTRESP` if [the client] expects CAS to balance the entire path. However, it is **not recommended** to make this change. Instead, [they] should run balancing at the end of each cycle to balance all nominations."*

So: `ALL_PATH_IND = 1` on CFPSTRESP forces whole-path balancing, but the supported approach is end-of-cycle balancing. Document this rather than flipping the flag.

---

## 10. CAS Maintenance Display / Flow-Qty (doubled / graphical)

CAS Maintenance is the operator's working screen (Tabular + Graphical tabs). Heavily **defect-driven** (13 SD of 18). The standout recurring bug is **doubled flow quantities**.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Flow Qty **doubled** when **two users retrieve CAS Maint at the same time** | Concurrent-retrieve defect | Code fix / config doc | 24-00973852, 23-00927006 |
| Flow Qty doubled/tripled (segments & locations) | Duplicate Location Path Maint rows (see §4) | Delete-dupes script | 25-01055876, 24-00966311 |
| Gas missing from Flow Qty on Timely/ID1 | Cycle/display defect | Config | 25-01021834 |
| Graphical tab unusable / not showing cuts / wrong pipeline | Graphical-render defects | Code fix | 25-01033451, 23-00906423, 24-00969046 |
| Backhaul qty inaccurate / not in Back Flow column | Backhaul calc defect | Code fix (version-gated) | 24-00951165, 22-00544499 |
| AOR not displayed consistently through segments | Display defect | Config/code | 24-00938907 |
| Variance: CAS Maint Flow Qty ≠ Conf Response total at receipt loc | Roll-up/config mismatch | Config | 24-00973228 |
| Exported files / whole numbers / MFC columns / Segment POV | Display & export config/defects | Config / code | 22-00831012, 24-00950393, 24-00948544 |

> **Doubled-flow-qty triage:** first ask "were two users on CAS Maint at once?" (concurrency defect — 24-00973852) vs "are there duplicate Location Path Maint rows?" (data — §4). They look identical on screen but have different fixes.
> **Version note (24-00951165):** the Backhaul fix existed since Jan 2023 for ONK but wasn't in their 2022.10 patch line — always check whether a known fix shipped in the client's specific patch.

---

## 11. Cut Logic — not cutting / override / ratchet / rounding

How CAS reduces over-capacity volumes. 13 actionable (9 SD). Cut math lives in the classic scheduling-reduction batch.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| CAS not cutting correctly | Scheduling-reduction defect | Code fix | 23-00881417 |
| IT Bump ID3 cutting incorrectly | Bump/IT cut config | Config | 24-00940500 |
| CAS Override issue / override won't accept zero qty | Override defects | Code fix | 22-00826396, 22-00822166 |
| Ratcheting when submitting cuts via CAS | Ratchet config/behavior | Config (then software updated) | 23-00901305, 23-00883026 |
| CAS rounding error on flowing cuts | Rounding defect | Code fix | 22-00588114 |
| Incorrect flow-day redirect / single-loc prelim cuts | Redirect/prelim defects | Code fix | 22-00661867, 22-00598105 |
| Pooling service flowing redirect | Redirect defect | Code fix | 22-00868420 |

### Diagnostic
```sql
-- Capacity vs scheduled for a segment/location/cycle (is it actually constrained?)
SELECT TSP_NO, SEG_NO, LOC_ID, GAS_DAY, CYCLE_ID,
       AVAIL_CAP_QTY, SCHED_QTY, CUT_QTY, POV_CD, PRIORITY_RANK
FROM CACTRL_SEG_CAP              -- segment capacity/scheduled table (verify name)
WHERE TSP_NO = <TSP_NO> AND SEG_NO = '<SEG>' AND GAS_DAY = '<GAS_DAY>' AND CYCLE_ID = <CYCLE>;
-- If SCHED_QTY <= AVAIL_CAP_QTY there should be NO cut; a cut here = defect or stale capacity.
```

---

## 12. Nomination Classification (CANOMCLTG)

Classification is the bridge: it must run and succeed before CAS can schedule. 11 actionable. Failures here surface downstream as "nom not in CAS."

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| `NomClassifyAndTransGroup` error when retrieving CAS Maint | Classification defect on retrieve | Code/config | 23-00933590 |
| Secondary nom gas not classified correctly (shows on nom screen, not CAS) | Secondary-classification defect | Code fix | 24-00949400 |
| Contract not classifying as Firm Primary (F59 at Owyhee) | Classification rule/config | Code fix | 24-00948473 |
| NOM CLASS ERROR for a gas day/cycle | **Rate data issue** (see §13) | Data script on `RTCTRL_RATE_*` | 22-00581584 |
| Classification CAS failure (v17) | Classification defect | Code fix | 22-00561424 |
| Nom not classifying in Tabular tab after batch | Classification/config gap | Config | 23-00933598 |

> "NOM CLASS ERROR" is frequently a **rate** problem, not a classification-logic problem — jump to §13.

---

## 13. CAS Run / Batch Failure (rate mismatch, timeout, loading)

CAS won't *run* (vs runs-but-wrong). 17 actionable (11 SD). The **single most important verbatim root cause** in this cluster:

### Rate Header ↔ Detail mismatch (recurring on REX/Ruby)
- **23-00930041 [SCHED]** "Error when Running CAS on REX": root cause *"Rate Header and Detail table mismatch on rates 14157 & 14218."*
- **23-00930211 [SCHED]** (follow-up) "Bad rates cleanup via script."
- **22-00581584 [SCHED]** NOM CLASS ERROR: *"Data issue resolved by update/delete scripts on `RTCTRL_RATE_HDR` and `RTCTRL_RATE_DTL` tables."*

When a rate exists in `RTCTRL_RATE_HDR` without matching `RTCTRL_RATE_DTL` rows (or vice versa), classification/CAS throws on that rate and the whole run fails. **Fix = clean up the orphaned/mismatched rate rows via script, then re-run CANOMCLTG/CAS.**

```sql
-- Find rate header rows with no matching detail (orphaned headers) — the CAS-run-fail cause
SELECT h.TSP_NO, h.RATE_ID, h.RATE_NM, h.EFF_DT_FROM, h.EFF_DT_TO
FROM RTCTRL_RATE_HDR h
LEFT JOIN RTCTRL_RATE_DTL d
       ON h.TSP_NO = d.TSP_NO AND h.RATE_ID = d.RATE_ID
WHERE h.TSP_NO = <TSP_NO>
  AND d.RATE_ID IS NULL;       -- header without detail = mismatch (rates 14157/14218 pattern)

-- And the reverse: detail rows pointing at a missing/expired header
SELECT d.TSP_NO, d.RATE_ID, COUNT(*) AS DTL_ROWS
FROM RTCTRL_RATE_DTL d
LEFT JOIN RTCTRL_RATE_HDR h
       ON d.TSP_NO = h.TSP_NO AND d.RATE_ID = h.RATE_ID
WHERE d.TSP_NO = <TSP_NO> AND h.RATE_ID IS NULL
GROUP BY d.TSP_NO, d.RATE_ID;
```

### Other run-failure modes
| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| CAS throws error when running the process | Various run defects | Code fix | 24-00964902, 24-00993136 |
| CANOMCLTG fails for TIGT with full month of data | Volume/perf defect | Code fix | 22-00638254 |
| Unable to run CAS for a pipeline (TIGT/REX/Trailblazer) | Setup/rate/segment gap | Config / script | 23-00905163, 23-00936155, 23-00897056 |
| Balancing job fails 2nd day running | Batch state defect | Workaround | 22-00662434 |
| CAS submit times / batch timing | Perf | Code fix | 22-00536918, 22-00638322 |
| AutoConfirm/CAS batch hung — needs restart | Service health | **Middle-tier / full restart** | 26-01087210, 25-01010281 |

---

## 14. Cut Notices & Sched-Qty Reports (CAX / CARPTS / CF67 / SQOP)

Outbound communication of cuts/scheduled quantities. 10 actionable.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Cut notice does not **attach** report `RPT_CAX15Z` | Report-attachment config | Config | 24-00957577 |
| `CAX_14` SQOP cut report sends even with no data | Report-trigger config (send only on CPR reduction) | Software updated | 23-00899755 |
| CAS Cut Report not generating PDF after CARPTS | Report-gen defect | Code fix | 23-00918900 |
| CAS report not generating/executing in myQuorumWeb | Web report-launch defects | Code fix | 22-00828342, 23-00891527 |
| CF67 report does not display dates | Report defect | Code fix | 22-00868468 |
| Cut reports sent with no attachments / failures running | Infra/report failure | Infra | 23-00892825 |
| SQOP / Sched Qty Detail report wrong qty | Usually customer/rate-data | Education / data | 22-00569540, 22-00569560 |
| Customers not receiving scheduled CF03O reports | Report scheduling config | Education | 22-00679607 |

> For the **outbound EDI** side of scheduled quantities (OACY / G874), see **SKILL_EDI_Troubleshooting.md**. This section is the report/notice (PDF/email) side.

---

## 15. Key Code Files & Repos

### Quorum.QPTM.Web (41e317c0-844c-4728-98da-529092957738)
| File | Purpose |
|------|---------|
| `Quorum.QPTM.Web.Controllers/UIControllers/QUIControllerConfirmationResponse.cs` | **Confirmation Response web controller** (confirm qty, bump, EPSQ) |
| `Quorum.QPTM.Web/Views/CASummaryMaintenance/CASummaryMaintenance.cshtml` + `Scripts/.../CASummaryMaintenance.js` | **CAS Maintenance screen** (Tabular/Graphical) |
| `Quorum.QPTM.ServiceCore.Nomination/QPTMNominationService.cs` | Shared nom/confirm service (overlap + confirm logic) |
| `Quorum.QPTM.CoreInterface/Constants.cs` | Process names (CANOMCLTG, CFAUTOCONF, CFPSTRESP, CAALLUNCAP) |
| `Quorum.QPTM.UnitTests/ConfirmationResponse/ConfirmationResponseTests.cs` | Conf Response tests |

### Quorum.QPTM.Batch (e024d80b-5c45-411c-93e1-78e2798ed885)
| File / process | Purpose |
|----------------|---------|
| `Quorum.QPTM.QPDllScheduling/QSchedulingReductionSeg.cs` + `QPSSchedulingReductionSeg.cs` | **CAS cut/reduction logic by segment** (§11) |
| `CANOMCLTG` | Nom classification & trans grouping (§12) |
| `CFAUTOCONF` | AutoConfirm (§7) |
| `CARPTS` | CAS cut-notice/report generation (§14) |

### Quorum.QPTM.ClassicBatch (classic C++ pipeline manager)
| File | Purpose |
|------|---------|
| `QPDllPipelineMgrPB/QPSBalanceSumDtl.cpp` | **Path-balancing summary detail** (PBBALCHAIN, §9) |
| `QPDllPipelineMgrPB/QTranBalRec.cpp` | Transaction balance records (path balancing) |
| `QPipelineMgrSharedLib/QResolverContractHeader.cpp`, `QResolverMDQ.cpp` | Contract/MDQ resolution for CAALLUNCAP (§4) |

### Quorum.QPTM.ClassicGUI
| File | Purpose |
|------|---------|
| `Managed/Quorum.QPTM.UserControls/QCntlConfirmationScreen.cs` | Classic Confirmation Response (web-vs-classic mismatches, §5) |

### Override repos
`<CLIENT>.QPTM.*` (DTE, APL, ONK, ONG, REX/Ruby clients) carry custom CAS/confirm config, classic batch overrides (e.g. `DTE.QPTM.ClassicBatch/QPDLLPipelineMgrPB_DTE/QPSBalanceSumDtl.cpp`), and metadata. **Always check the client override before assuming base behavior** — code search `{"searchText":"<term> repo:<CLIENT>.QPTM"}`.

---

## 16. Database Tables Reference

| Table | Purpose | Cluster |
|-------|---------|---------|
| `CFCTRL_CONF` / `CFCTRL_CONF_HR` | **Confirmation detail (confirmed qty, diff, reduction reason) + hourly** | §5, §7 |
| `PACTRL_CYCLE` | **Cycle config inc. `GAS_FLOW_START_TIME_OFFSET` (drives EPSQ)** | §8 |
| `RTCTRL_RATE_HDR` / `RTCTRL_RATE_DTL` | **Rate header & detail — mismatch breaks CAS runs / NOM CLASS** | §13, §12 |
| `NNCTRL_LOC_PATH` | Location Path Maintenance backing rows (dupes = doubled volumes) | §4, §10 |
| `CACTRL_CLASS_NOM` | Classified-nom table CAS reads (verify exact name per client) | §4, §12 |
| `CACTRL_SEG_CAP` | Segment capacity vs scheduled/cut (verify name) | §11 |
| `NNCTRL_NOM_DTL` | Nomination detail (source for confirm/classify) — see Nominations skill | all |
| `PACTRL_CYCLE_DEADLINE` | Confirmation/scheduling deadlines — see EDI skill | §1 |
| `QARCH_GLOBAL_CONFIG` / `QARCH_TSP_CONFIG` | Global/TSP config (`ALL_PATH_IND`, report toggles) | §9, §14 |

> Table names in `CACTRL_*` and some path tables vary by client schema/version — **confirm the exact name against the client's DB** (case 26-01098601 / 25-01024941: clients regularly ask "what SQL/tables are behind the Confirmation Response & CAS grids"; the answer is the tables above).

---

## 17. Diagnostic SQL Queries

### A. Confirmed quantities for a gas day/cycle (§5)
```sql
SELECT TSP_NO, NOM_ID, GAS_DAY, CYCLE_ID, LOC_ID, NOM_QTY, CONF_QTY, DIFF_QTY,
       REDUCTION_REASON_CD, CONF_LEVEL_CD, UPDT_DT, USER_ID
FROM CFCTRL_CONF
WHERE TSP_NO = <TSP_NO> AND GAS_DAY = '<GAS_DAY>' AND CYCLE_ID = <CYCLE>
ORDER BY LOC_ID, NOM_ID;
```

### B. EPSQ cycle-offset check (§8)
```sql
SELECT CYCLE_ID, GAS_FLOW_START_TIME_OFFSET
FROM PACTRL_CYCLE
WHERE TSP_NO = <TSP_NO>
ORDER BY CYCLE_ID;
-- NULL/0 offset on ID1/ID2 → EPSQ only fires ID3 (24-00982666 / 26-01088719).
```

### C. Rate header/detail mismatch (§13 — CAS run failures)
```sql
SELECT h.RATE_ID, h.RATE_NM, h.EFF_DT_FROM, h.EFF_DT_TO
FROM RTCTRL_RATE_HDR h
LEFT JOIN RTCTRL_RATE_DTL d ON h.TSP_NO = d.TSP_NO AND h.RATE_ID = d.RATE_ID
WHERE h.TSP_NO = <TSP_NO> AND d.RATE_ID IS NULL;
```

### D. Duplicate Location Path Maint rows (§4/§10 — doubled volumes)
```sql
SELECT TSP_NO, LOC_ID, SEG_NO, PATH_ID, FLOW_IND, EFF_DT_FROM, EFF_DT_TO, COUNT(*)
FROM NNCTRL_LOC_PATH
WHERE TSP_NO = <TSP_NO>
GROUP BY TSP_NO, LOC_ID, SEG_NO, PATH_ID, FLOW_IND, EFF_DT_FROM, EFF_DT_TO
HAVING COUNT(*) > 1;
```

### E. Capacity vs scheduled for a segment (§11 — should it have cut?)
```sql
SELECT SEG_NO, LOC_ID, GAS_DAY, CYCLE_ID, AVAIL_CAP_QTY, SCHED_QTY, CUT_QTY, POV_CD, PRIORITY_RANK
FROM CACTRL_SEG_CAP
WHERE TSP_NO = <TSP_NO> AND SEG_NO = '<SEG>' AND GAS_DAY = '<GAS_DAY>' AND CYCLE_ID = <CYCLE>;
```

### F. Is the nom classified yet? (§4/§12 — "not in CAS")
```sql
SELECT NOM_ID, GAS_DAY, CYCLE_ID, CLASS_CD, TOS_CD, SEG_NO, CTR_NO, SCHED_QTY
FROM CACTRL_CLASS_NOM
WHERE TSP_NO = <TSP_NO> AND GAS_DAY = '<GAS_DAY>' AND CYCLE_ID = <CYCLE> AND NOM_ID = <NOM_ID>;
-- No row = CANOMCLTG hasn't classified it → CAS can't see it.
```

---

## 18. Known Historical ADO Bugs

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|-------|--------------|-----------------|---------|---------|
| **#1695520** | Bug / **Closed** | Confirmation Response screen allows confirming quantity above nomination | §5 | 24-00985949 |
| **#1744837** | Bug / **Closed** | Confirmed subsequent cuts not holding after nom change (reopen) | §5 | 25-01032374 |
| **#1670362** | Requirement / **Closed** (Tags: **HOTFIX**) | GBG 2024.04 Critical Out-of-Cycle — incl. Path Balancing zeroing LNG plant qty | §9 | 24-00963500 |

> **Data-quality note on ADO linkage:** the vast majority of these SF cases are **not** linked to a discrete ADO Bug. Confirmations/CAS cases are dispositioned operationally — **Configuration Changed** (50+), **Data Script Provided**, **Software Updated** (often rolled into a version/hotfix without a per-case bug). The "Software Updated" resolution usually points at a release/patch (e.g. 2021.04, 2022.10, 2023.04, 2024.04 hotfix #1670362) rather than a standalone work item. When you need the code root cause, search the **process/table name** (CANOMCLTG, CFAUTOCONF, PBBALCHAIN, RTCTRL_RATE_*) in code search rather than expecting a linked bug.

---

## 19. Expected Behavior / User Education

~58 of the 181 actionable cases are **Customer Error / Training** — recognize these to avoid needless scripts/escalations.

| Reported as | Reality | Case |
|-------------|---------|------|
| "CAS leaving unbalanced paths" | Working as designed — run balancing at end of cycle; don't flip `ALL_PATH_IND` | 22-00536889 |
| "PBBALCHAIN CBLs on PT paths" | Test used ATT locations, not a real scenario | 24-00976439 |
| "Bumping qty not updating after save" | Save/refresh behaves as designed | 26-01069228 |
| "Where does CAS pull RATE from?" / "SQL behind the grids" | Education — point to CAS User Guide + tables in §16 | 23-00909480, 22-00644002, 26-01098601, 25-01024941 |
| "CAS report not populating" | User didn't check **Prelim** / wrong run mode | 22-00874949 |
| "Nom cut, then confirm higher than cut but below original" | Supported workflow — train the operator | 22-00618839 |
| "CAS nom class didn't bring updated rate" | Documented behavior — CAS User Guide v1.1 | 24-00992706 |
| "Different GD/cycles in same EDI conf-response file" | Expected EDI batching | 22-00555586 |
| "Cut notices not going out on reductions" | Config/training, not a defect | 22-00679655 |
| SQOP report "wrong qty" | Customer/rate data, not a system fault | 22-00569540, 22-00569560 |

**Tell-tales it's user/expected:** the client wants CAS to balance mid-cycle (it balances end-of-cycle), is testing with ATT/non-prod locations, hasn't run/checked the right batch or run-mode (Prelim), or is asking how a number is derived.

---

## 20. Escalation Decision Tree

```
Confirmation / Scheduling (CAS) case reported
│
├─ CONFIRMATION leg?
│   ├─ Confirm qty wrong / above nom / cuts not holding?
│   │    → §5; check CFCTRL_CONF; known bugs #1695520, #1744837
│   ├─ Conf Summary ≠ Conf Response / timeouts?  → §6 (defect; check version vs hotfix)
│   ├─ AutoConfirm not running?  → §7: SERVICE RESTART first (26-01087210)
│   ├─ AutoConfirm cutting extra volumes?  → §7 defect (22-00874403)
│   └─ EPSQ only in ID3 / EPSQ=0?  → §8: PACTRL_CYCLE.GAS_FLOW_START_TIME_OFFSET
│
├─ SCHEDULING / CAS leg?
│   ├─ Does CAS even RUN?
│   │    ├─ NO (errors out):  → §13
│   │    │     → check RTCTRL_RATE_HDR/DTL mismatch FIRST (23-00930041, 22-00581584)
│   │    │     → segment/path/default-path setup (REX/Ruby buildout) §4
│   │    │     → batch hung? → restart MT/services (25-01010281, 26-01087210)
│   │    └─ YES but WRONG numbers:
│   │          ├─ Nom/TOS not appearing in CAS?  → §12 classification + §4 path config
│   │          │      (confirm CANOMCLTG ran before blaming CAS)
│   │          ├─ Flow qty DOUBLED?  → §10: concurrent retrieve (defect) vs dup path rows (§4 script)
│   │          ├─ Cutting incorrectly / override / ratchet / rounding?  → §11
│   │          └─ Cuts unbalanced / CBLs?  → §9 PBBALCHAIN (Agent rights, ALL_PATH_IND)
│   └─ Cut notice / CAS report not generating/attaching?  → §14 (CARPTS / RPT_CAX*)
│
├─ Implementation/UAT/conversion client (TREX/REX/Ruby, ECGS, SOC)?
│   → expect CONFIG, not defect — §4 (segment/path/TOS/rate setup) is the default hypothesis
│
└─ "How does X work / what SQL is behind the grid?"  → §19 Education (CAS User Guide + §16 tables)
```

---

*Skill created: 2026-06-01*
*Based on: 181 actionable QPTM Confirmations + Scheduling (CAS) + Capacity Allocation Scheduling (CAS) SF cases; verbatim resolutions from 26-01088719, 24-00982666, 23-00930041/30211, 22-00581584, 24-00966311, 25-01017371, 24-00972503/508, 22-00536889, 23-00905756, 26-01088716, 26-01087210; ADO work items #1695520, #1744837, #1670362; QPTM code search.*
*Companions: SKILL_EDI_Troubleshooting.md (cycle deadlines / OACY EDI), SKILL_Nominations.md (nom rows / ghost-nom delete scripts). Applicable to all QPTM TSPs/clients.*
