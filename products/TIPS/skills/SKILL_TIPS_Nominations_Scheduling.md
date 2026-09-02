# SKILL: TIPS Nominations / Confirmations / Scheduling Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-11 | **Product:** My Quorum TIPS (oil/gas transaction & accounting)
**Scope:** Nomination Transaction entry/submission, the NOMPOST/CFCREATE/NOMDEL submission chain, nomination validation rules (NNG028 future-nom, gas-date validations), invalid date-range (BEG_GAS_DAY > END_GAS_DAY) corruption, Nom Import (NomUploadTemplate), 31-day copy/paste grid, the Nomination→Confirmation sub-process (UTILCALDT → QCTRL_CONF), Confirmation Response screen (confirmed-qty vs nominated-qty, auto/manual confirm), scheduling/balancing (rank-based cuts), NOMCYCLNTF cycle-notify, and the forecasting batch chain (NGLPROD / TMTRSPLIT → ARAP_IFGTT).
**Companion:** For allocation after scheduling see **SKILL_TIPS_Allocations_PPA_Imbalance.md**; for the batch-engine framework (QPEC, process queue, PQID logs) see **SKILL_TIPS_Batch_Processing.md**; for the CAW front-end screen see **SKILL_TIPS_CAW.md**; for gas/settlement statements see **SKILL_TIPS_Reporting_Statements.md**. Nominations *feeds* confirmations → scheduling → allocation; cross-references noted, not duplicated.

> Evidence base: ~344 closed TIPS Nominations/Confirmations/Scheduling/Availability/Forecasting cases. Actionable root causes mined: Application Configuration (35), Software Defect (29), ChangeConfig (7) = 71. Plus ~70 Customer Error / Training cases for the Expected-Behavior section. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining. Where the mined data did not yield a clear fix, the section says so rather than inventing one.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Concepts & Pipeline](#2-concepts--pipeline)
3. [Decision Tree](#3-decision-tree)
4. [Invalid Nom Date Range — BEG_GAS_DAY > END_GAS_DAY (HIGH FREQUENCY)](#4-invalid-nom-date-range)
5. [NOMPOST / CFCREATE / NOMDEL Submission Chain Failures](#5-nompost--cfcreate--nomdel-submission-chain)
6. [Nomination Validation Rules (NNG028 Future-Nom, Contract-Term)](#6-nomination-validation-rules)
7. [Nom Import / Upload (NomUploadTemplate) & Copy/Paste Grid](#7-nom-import--copypaste-grid)
8. [Nomination → Confirmation Sub-Process (UTILCALDT / QCTRL_CONF)](#8-nomination--confirmation-sub-process)
9. [Confirmation Response Screen — Qty Overwrite / Auto-vs-Manual / Web-vs-Classic](#9-confirmation-response-screen)
10. [NOMCYCLNTF Cycle-Notify & Scheduling / Balancing](#10-nomcyclntf--scheduling--balancing)
11. [Forecasting Batch Chain (NGLPROD / TMTRSPLIT → ARAP_IFGTT)](#11-forecasting-batch-chain)
12. [Expected Behavior / User Education](#12-expected-behavior--user-education)
13. [Known ADO Items](#13-known-ado-items)
14. [Database Tables Reference](#14-database-tables-reference)
15. [Diagnostic SQL](#15-diagnostic-sql)
16. [Escalation Guidance](#16-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (message / behavior) | Likely cause | First check |
|------------------------------|--------------|-------------|
| "Impossible dates" / nom can't be deleted; Beg = 1st-of-month, End = last-day-of-prior-month | Invalid date range in `QCTRL_NOM_DTL` (Copy-Noms-Forward bug) | §4 — diagnostic SQL B; needs data script + `QGValidationNomGasDates` fix |
| Nom submit/update silently doesn't post; scheduled qty not updating | NOMPOST/CFCREATE job not firing or failing | §5 — PQID log; `QARCH_PROCESS_MSG_LOG` |
| "Nominations may not be submitted that far in the future"; thousands of noms in error after an upgrade | Validation rule **NNG028** added + global config `Number_Of_Days_In_Future_Allow_Noms` | §6 — Validation Rule Assignment screen |
| "GAS DAY NOT BETWEEN SR K EFF. AND TERM. DATES" | Contract-term validation (QCM-integration removal changes which date it checks) | §6 |
| Nom upload throws errors on a row | NomUploadTemplate End Gas Day < Beg Gas Day | §7 |
| Confirmation Response screen blank / noms not populating after a date | Nom→Conf sub-process broke; **UTILCALDT** not scheduled → `QCTRL_CONF` not built | §8 |
| Confirmed quantity overwritten by shipper's nominated quantity | Confirm-vs-nom precedence defect | §9 |
| Meter set to AutoConfirm but not auto-confirming | Confirmation method = **Manual** on contract header (config, not a bug) | §9 / §12 |
| Alt Conf Qty updates in Classic but not Web | Web-vs-Classic confirmation screen defect | §9 |
| NOMCYCLNTF process fails (object-reference null) | A meter has no confirmation for a gas day | §10 — `QTIP_RPTS_NOM_CYCLE_SUMMARY` |
| Daily/forecast process fails at NGLPROD (ACCESS_VIOLATION C0000005) | Forecasting batch chain defect on new env setup | §11 |
| Duplicate / overlapping noms; can't update or delete | Data dup — usually Customer Error, fixed by script | §12 / §4 |
| Gathering statement shows 0 nominated/scheduled | Usually expected (no confirmed/scheduled qty) or statement suppression logic | §12 |

---

## 2. Concepts & Pipeline

TIPS processes the gathering/midstream gas day in stages. Nominations are entered, posted, confirmed, scheduled, then allocated.

```
[Nomination Transaction entry / Nom Import / CAW]
      │  submit/update
      ▼  NOMPOST  (posts nom; sub-steps incl. CFCREATE = create confirmations, NOMDEL = delete)
[QCTRL_NOM_DTL / QTRAN_* nom detail]
      │  Nom→Confirmation sub-process (depends on UTILCALDT building QCTRL_CONF from QTRAN_CAL_DATE)
      ▼
[Confirmation Response screen / QCTRL_CONF]  ── auto-confirm or manual confirm; confirmed qty ≤ nominated qty
      │  scheduling / balancing (rank-based cuts within a contract)
      ▼
[Scheduled Qty] ──► Allocation (see SKILL_TIPS_Allocations_PPA_Imbalance.md) ──► Statements/Billing
      │
      └── NOMCYCLNTF: per-cycle confirmation/notification job (emails, cycle summary)
```

### Key building blocks
- **NOMPOST** — the process that posts a nomination on submit/update. Internal sub-steps observed: **CFCREATE** (create confirmation records), **NOMDEL** (delete). Failures here block the whole downstream chain. (22-00534097, 22-00592784, 24-00953499)
- **UTILCALDT** — calendar/utility batch that builds the `QCTRL_CONF` confirmation table from the `QTRAN_CAL_DATE` staging table. If UTILCALDT is **not scheduled**, the Confirmation Response screen never populates (25-01001893).
- **Validation Rule Assignment** screen — assigns nomination validation rules (e.g. **NNG028 FUTURE NOM VALIDATION**) per Company/Module (e.g. Gathering). Rules can be silently added by an upgrade/hotfix (26-01064773).
- **Confirmation method** — set on the **contract (K) header**: Auto vs Manual. Manual = nothing auto-confirms (26-01069130).
- **Copy Noms Forward** — copies a nom period to the next month; a page-reload race here is the source of the invalid-date-range corruption (§4).
- **Cycle / NAESB cuts** — scheduling cuts the lowest-ranked nomination within a contract to balance receipt↔delivery (24-00955629).

---

## 3. Decision Tree

```
TIPS Nomination/Confirmation/Scheduling case reported
│
├─ Nom has impossible dates / can't be deleted (Beg > End)?  (§4)
│   ├─ Confirm in QCTRL_NOM_DTL (diag B); it was usually created via Copy Noms Forward
│   ├─ FIX: data script to delete/correct the bad rows (Cloud Ops) +
│   └─ confirm the QGValidationNomGasDates fix is deployed (ADO #1672104 / #1769494) so it can't recur
│
├─ Nom submit/update doesn't take effect; sched qty stale?  (§5)
│   ├─ Get PQID; read QARCH_PROCESS_MSG_LOG for the failing step (NOMPOST/CFCREATE/NOMDEL)
│   ├─ Job didn't run at all → scheduling/trigger gap (ADO #1716164) — Cloud Ops
│   └─ Job ran and errored → match signature to §13 (CFCREATE double-update #1447164; NOMPOST #1660388)
│
├─ "…that far in the future" / mass nom errors after an upgrade?  (§6)
│   └─ CONFIG: check Validation Rule Assignment for NNG028 + global config Number_Of_Days_In_Future_Allow_Noms
│
├─ Confirmation Response screen blank / noms not populating?  (§8)
│   └─ Check UTILCALDT is scheduled & ran; it builds QCTRL_CONF from QTRAN_CAL_DATE → schedule + restart services (25-01001893)
│
├─ Confirmed qty wrong (overwritten by nom / > nom / Web≠Classic)?  (§9)
│   ├─ Confirmed overwritten by shipper nom → DEFECT (24-00966802)
│   ├─ Confirm allows qty > nominated → config/validation (24-00962745)
│   ├─ AutoConfirm not firing → contract header method = Manual (CONFIG, 26-01069130)
│   └─ Alt Conf Qty Classic≠Web → Web screen DEFECT (22-00676427)
│
├─ NOMCYCLNTF fails (null object reference)?  (§10)
│   └─ Find the meter with no confirmation for the gas day (QTIP_RPTS_NOM_CYCLE_SUMMARY); clear orphan confs (22-00875002)
│
├─ Forecast/daily fails at NGLPROD (ACCESS_VIOLATION)?  (§11)  → forecasting batch chain defect, Engineering (24-00945026)
│
└─ Duplicate/overlapping noms, gathering statement zeros, "how do I…"?  (§12)  → usually Customer Error / Training
```

---

## 4. Invalid Nom Date Range — BEG_GAS_DAY > END_GAS_DAY (HIGH FREQUENCY)

The single most recurring actionable + Customer-Error TIPS nomination problem. A nomination ends up with **Beginning Gas Day later than End Gas Day** (classic signature: **Beg = 1st of a month, End = last day of the prior month**, e.g. Beg 11/1/2025, End 10/31/2025). Because the dates are impossible, **TIPS will not let the user delete or update the nom**, so it has to be removed/corrected by a **data script**.

### Root cause
The bad rows are written via **Copy Noms Forward** (copying a nom period from the current month into the next month). A page-reload race in the copy path overrode the user's actual dates with "current" dates, producing the inverted range. The bad data lands in **`QCTRL_NOM_DTL`** (a.k.a. the Nomination Transaction Detail / `qctrl_nom_dtl` table). It can occur more often if the user touches the Date Range field just before clicking Copy Noms. (25-01051919, with a Dynatrace capture of the user session.)

### Fix recipe
1. **Data script (Cloud Ops):** delete or correct the bad-dated nomination rows in `QCTRL_NOM_DTL`. Multiple cases were resolved exactly this way — "We were able to successfully script the deletion of this nomination data" (25-01052068); "Scripted to remove…" (25-01027984, 24-00946292). Scope tightly to the SR/contract/gas-day; verify-SELECT first.
2. **Confirm the validation fix is deployed** so it cannot recur. Engineering added a **mandatory validation `QGValidationNomGasDates`** in the **QG metadata layer** that rejects a nom when BEG_GAS_DAY/END_GAS_DAY are empty/min-value or BEG > END (24-00962813 / ADO #1672104). The follow-up fix (25-01051919 / ADO **#1769494**) corrected it further: it now (a) fires for **all object states except Deleted** (was Added-only) and (b) reads the **correct dates during a Copy Noms** instead of the page-reload "current" dates.
3. Implementing class: **`Quorum.TIPS.Web /Quorum.TIPS.Validation/Nomination Transaction/ValidationRules/Mandatory Validations/QGValidationNomGasDates.cs`**, registered in **`Quorum.TIPS.Metadata / STANDARD 16.0`** (`QARCH_CTRL_OBJECT_*` json). If a client still hits this, verify they are on a build that contains #1769494.

> Many of these come in as **Customer Error** ("Nomination Errors due to bad date range", "Impossible Dates") — the *data* is the customer's, but the *ability to create it* was a defect. Disposition = data script now, confirm the validation build for the long term.

---

## 5. NOMPOST / CFCREATE / NOMDEL Submission Chain Failures

When a user submits/updates a nomination, **NOMPOST** runs to post it; sub-steps create confirmations (**CFCREATE**) and handle deletes (**NOMDEL**). When this chain fails or doesn't fire, the nom appears entered but **scheduled quantities don't update** and confirmations don't get created.

| Signature | Cause | Disposition | Evidence |
|-----------|-------|-------------|----------|
| NOMPOST job **does not run** when user submits/updates a nom | Submit trigger gap | Code fix | ADO **#1716164** (2025.04 Beta) |
| NomPost **CFCREATE fails on double-update** to Nom screen | Race when the Nom screen is updated twice quickly | Code fix | ADO **#1447164 / #1456678** (ONM); SF 22-00592784 |
| 2023.04 **TIPS NOMPOST error** | Post-step defect | Code fix | ADO **#1660388** (HPE); SF 24-00953499 |
| NomPost fails sporadically (~1/day) in **NOMDEL** | Intermittent delete-step failure (logs on QPEC servers) | Investigate via PQID log | SF 22-00534097, 22-00534090 |

### Diagnostic — start here
1. Get the **PROCESS_QUEUE_ID (PQID)** of the failing run (clients usually supply it).
2. Read the error rows from the process message log:
```sql
SELECT * FROM QARCH_PROCESS_MSG_LOG
WHERE  PROCESS_QUEUE_ID = '<PQID>'
  AND  LOG_MSG_TYPE_CD NOT IN ('DEBUG','INFO','WARN');
```
(query shape verbatim from 22-00875002). Look for the failing step name (NOMPOST / CFCREATE / NOMDEL) and the message.
3. If the job **never ran**, it's a trigger/scheduling gap (Cloud Ops + possibly #1716164). If it **ran and threw**, match the signature above and confirm the fix build.

---

## 6. Nomination Validation Rules (NNG028 Future-Nom, Contract-Term)

TIPS fires nomination validation rules assigned per **Company / Module** on the **Validation Rule Assignment** screen. The recurring actionable issue is a rule **appearing or behaving differently after an upgrade/hotfix**, throwing mass errors on previously-valid noms.

### NNG028 — Future-Nom Validation (the 6,000-error case)
- Rule **NNG028 FUTURE NOM VALIDATION (# OF CALENDAR DAYS)** was **added to companies 061/057 during the 2024.04 post-go-live performance hotfix** at ONEOK and immediately put **6,000+ noms in error** ("Nominations may not be submitted that far in the future"). It was *not* added to the client's other companies (101/255/998), which is why the behavior was inconsistent. (26-01064773)
- The gate is the **global config `Number_Of_Days_In_Future_Allow_Noms`** (set to 60 days there), but the client imports noms years into the future.
- **Fix options:** either remove/unassign NNG028 from the affected company on the Validation Rule Assignment screen, or raise `Number_Of_Days_In_Future_Allow_Noms` to match the client's nom horizon. Then re-run the **Nightly Nomination Validation** to clear the existing errors. *(Resolution pattern partly unclear from the mined data — the case documents the diagnosis and options; confirm with Cloud Ops which lever the client chose.)*

### Contract-term date validation
- "GAS DAY NOT BETWEEN SR K EFF. AND TERM. DATES" began firing after the client **lost QCM integration**: without QCM the validation looks at the **contract's primary term expiration date** instead of the **QCM contract-header effective date**, so it fires when it previously wouldn't. (22-00867486; resolution pattern unclear from mined data — treat as a config/validation review, verify which date the rule should key on for a non-QCM client.)
- Other contract-term validation cases: "Nomination Error for Contract Term Dates" (22-00675872), "GAS DAY NOT BETWEEN SR K EFF. AND TERM. DATES" — generally driven by contract header eff/term dates vs gas day.

> When a client reports "noms that used to be fine are now in error," **check the Validation Rule Assignment screen and recent release/hotfix notes first** — a rule was very likely added or its date-source changed.

---

## 7. Nom Import / Upload (NomUploadTemplate) & Copy/Paste Grid

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| External user hits errors on **Nom Upload** | Template allowed End Gas Day < Beg Gas Day | Validate **NomUploadTemplate** so Ending Gas Day ≥ Beginning Gas Day, else error | 24-00962825 |
| Cannot copy/paste noms into the screen / 30-day pop-up from a spreadsheet (Web) | Web grid paste defect | Code change | 22-00598013 |
| 31-day Nom Copy/Paste highlight cells — scrolling issue | Web grid scroll/highlight defect | Code fix | 23-00912355 |
| Nom Copy retains old Total Fuel % from GCR (not the current %) | Copy used stale GCR fuel % | Code fix | 22-00821098 |

> The Nom-Import date-validation (24-00962825) is the same date-integrity theme as §4 — the upload path and the Copy-Noms path both needed Beg/End gas-day guards.

---

## 8. Nomination → Confirmation Sub-Process (UTILCALDT / QCTRL_CONF)

When noms are entered, a **sub-process automatically populates the Confirmation Response screen**. If it stops, noms exist but **nothing can be confirmed** (auto or manual) because the Confirmation screen is empty.

### Root cause & fix (verbatim pattern, 25-01001893)
- The **`UTILCALDT` batch process was not scheduled** for the client. UTILCALDT is required to **populate `QCTRL_CONF`** — the records from **`QTRAN_CAL_DATE`** act as a **staging table** for `QCTRL_CONF`.
- **Fix:** schedule/run **UTILCALDT**, then **restart the services** so the application picks up the rebuilt tables. After that, nomination changes flowed to the Confirmation Response screen.
- **Watch-out (carried into a follow-up case 25-01002219):** existing noms entered while the sub-process was broken **may still not show up** after the fix — they need a **separate data restore** of the missing nom→conf records, and another service restart. Track that as its own item.

### Related screen-availability defect
- "Users cannot open the Confirmation Response screen in TIPS Web" — HVM 25-01033973, handled as a **Global Cloud Ops Problem / RCA** (ADO **#1746576 / #1746577 / #1754745**, In Engineering at mining time). Distinct from the populate issue: here the screen won't open at all.

---

## 9. Confirmation Response Screen — Qty Overwrite / Auto-vs-Manual / Web-vs-Classic

The Confirmation Response screen is where operators/internal schedulers confirm nominated quantities. Recurring defects cluster around **quantity precedence**, **auto-vs-manual confirm**, and **Web-vs-Classic** parity.

| Issue | Root cause | Disposition | Case / ADO |
|-------|-----------|-------------|------------|
| Operator/Scheduler confirms a qty, then the **Shipper's nomination overwrites the confirmed qty** (breaks interconnects) | Confirm-vs-nom precedence defect (same as QPTM 24-00962122) | Code fix | 24-00966802 |
| Confirmation screen **permits confirmed qty > nominated qty** (should be ≤ nom) | Validation/config gap | Config/validation | 24-00962745 |
| Changing Confirmed Qty **does not update Scheduled Qty** (intermittent) | Conf→sched propagation defect | Code fix | 22-00526756 |
| **Alt Conf Qty** updates in Classic but **not in Web** | Web confirmation-screen defect | Code fix | 22-00676427 |
| Confirmation Response screen issues when using **Project filter** (Web) | Web filter defect | Code fix | 22-00598088 |
| Updated **Confirmation Method for a meter not used** when nom submitted | Meter confirm-method not honored on submit | Code fix | ADO **#1556874** |
| Confirmation screen **doesn't agree with Nomination screen** / Activity Report doesn't tie | Screen/report consistency defects | Code fix | 23-00890286, 23-00885357, 22-00679889 |
| Confirmation changes in **CAW prohibited during Facility/Company Lock** | Lock-state handling | Code/config | 22-00679844 |

### Config look-alikes (NOT defects)
- **Meter set to AutoConfirm but not auto-confirming** → the **contract (K) header Confirmation Method is set to Manual**; that overrides the meter. Change the contract header method to Auto. (26-01069130) — config, not a bug.
- **EB-8477** (ADO **#1490446**, Feature/Closed): "Order nominated movements — only use 'confirmed' allocD rows from parent nomination" — relevant when confirmed vs nominated ordering looks off downstream.

> **Web-vs-Classic is a recurring theme** (as in QPTM). If a client says "Classic works, Web doesn't" (Alt Conf Qty, Project filter), reproduce in both — the Web screen is usually the one missing the behavior. Confirm the patch level.

---

## 10. NOMCYCLNTF Cycle-Notify & Scheduling / Balancing

### NOMCYCLNTF (cycle confirmation/notification job)
- **Symptom:** NOMCYCLNTF fails with `Unable to resolve message. Object reference not set to an instance of an object`.
- **Root cause:** a **meter has no confirmation for the gas day** in question. In 22-00875002 (Enable, company 3700), meter #224136 had no confirmation for the 12/15 gas day; once the user **removed the stale/orphan confirmations** for that meter, the scheduled job completed for both plants and the notification emails went out.
- **Diagnostic:** inspect the NOM cycle summary for the failing company/gas day, then the process log by PQID:
```sql
SELECT * FROM QTIP_RPTS_NOM_CYCLE_SUMMARY
WHERE  /* company / gas day filter */;     -- find the meter missing a confirmation
SELECT * FROM QARCH_PROCESS_MSG_LOG
WHERE  PROCESS_QUEUE_ID = '<PQID>' AND LOG_MSG_TYPE_CD NOT IN ('DEBUG','INFO','WARN');
```
- Provisioning note: NOMCYCLNTF must be in the right security group to run (ADO **#1726591** — "Insert NOMCYCLNTF into Security Group 1016").

### Scheduling / Balancing (rank-based cuts)
- **Request pattern (ChangeConfig):** configure scheduling/balancing so that when a **cut occurs on a downstream (delivery) location via confirmations**, the process uses **ranks within the same contract** to cut the **lowest-ranked Receipt nomination**, and vice-versa (cut on receipt → balance to lowest-ranked delivery). (24-00955629) — this is a configuration/enhancement of the balancing rule, route to the product/config owner. *(No single self-service fix recipe in the mined data — it is a balancing-rule setup.)*

---

## 11. Forecasting Batch Chain (NGLPROD / TMTRSPLIT → ARAP_IFGTT)

- **Symptom:** the Daily / forecasting process **fails at the NGLPROD step** with `Operating System Exception — Exception code: C0000005 ACCESS_VIOLATION`, when running the chain **TMTRSPLIT → … → ARAP_IFGTT** (NGL production forecasting). Seen on a **new client/env setup** (Armstrong in ENT PSTA; reproduced in Q). (24-00945026)
- **Disposition:** native-code access violation in the NGLPROD batch step = **Software Defect → Engineering**. *(Resolution detail not captured in the mined data; provide the PQID, env, and the TMTRSPLIT→ARAP_IFGTT step list when escalating.)*

---

## 12. Expected Behavior / User Education

~70 of the closed cases are **Customer Error / Training**. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality | Case |
|-------------|---------|------|
| "Nomination Error — Impossible Dates" / "bad date range" / "incorrect End Gas Day" | Customer created an inverted Beg/End range (often via Copy Noms) — clear with a **data script** (§4) | 26-01104217, 26-01096346, 24-00946292, 23-00936375, 24-00936713 |
| "Duplicate / overlapping nominations causing errors; can't update or delete" | Duplicate nom rows — resolved by **scripting out the duplicates** | 25-01027984 ("Scripted to remove duplicate noms"), 25-01002756, 24-00951556, 23-00928840, 22-00813693 |
| "Meter set to AutoConfirm but not auto-confirming" | **Contract header Confirmation Method = Manual** — change to Auto | 26-01069130 |
| "Nom Transaction Default End Date field gone / not working" | The grid date field was **removed in the 2021.10 release** (it didn't work as expected); newer envs don't have it | 24-00964770 |
| "Deal not appearing in Nomination Creation screen" (QGM) | The deal has **"Confirm Only" checked** — uncheck it so it's available to nominate | SF KB 000004076 |
| "Nominated & Scheduled qty showing as zero on the Gathering statement" | Usually nothing scheduled/confirmed yet, or statement suppression — verify confirmed/scheduled qty exists | 25-01010885, 23-00916045 |
| "Confirmation Validation Configuration / Confirmation Elements Usage" (post-go-live pain points) | Training on how TIPS confirmation validations/elements are meant to be configured | 24-00962759, 24-00962758, 24-00955626, 24-00955618 |
| "Late / Retroactive Nom Error" | Working as designed — late/retro noms are gated by cycle deadlines | 22-00514738, 22-00598081 |
| "Can't create next-month noms / errors on March activity while submitting April" | Month-roll / cycle timing education | 23-00888033, 22-00683476 |
| "Receipt point meter not on contract in Nominations-by-Meter report" | Setup/contract association, not a defect | 24-00940916 |

**Tell-tale it's Customer Error / Training:** inverted or impossible gas-day ranges; duplicate/overlapping noms; AutoConfirm "not working" when the contract is Manual; zeros on a statement before anything is scheduled; "how do I" questions about cycle deadlines, retro noms, or confirmation elements.

---

## 13. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|-------|--------------|-----------------|---------|---------|
| **#1672104** | Bug / **Closed** | MOM — Nomination Transaction submission bug: BEG_GAS_DATE > END_GAS_DATE (orig `QGValidationNomGasDates`) | §4 | 24-00962813 |
| **#1769494** | Bug / **Closed** | ONM — Nomination Detail invalid dates (BEG_GAS_DAY > END_GAS_DAY) after fix from #1672104; fire for all states except Deleted + correct dates on Copy | §4 | 25-01051919 |
| **#1716164** | Bug / **Closed** | 2025.04 — Nomination Transaction: NOMPOST job does not run when user submits/updates nomination | §5 | — |
| **#1660388** | Bug / **Closed** | HPE — 2023.04 TIPS NOMPOST error | §5 | 24-00953499 |
| **#1447164 / #1456678** | Task / **Closed** | ONM — NomPost CFCREATE fails on double update to Nom screen (Dev + QA) | §5 | 22-00592784 |
| **#1556874** | Bug / Proposed | 2022.10 — Confirmation Response: updated Confirmation Method for meter not used when nom submitted | §9 | — |
| **#1490446** | Feature / **Closed** | EB-8477 — Order nominated movements; only use 'confirmed' allocD rows from parent nomination | §9 | — |
| **#1746576** | Problem (Global Cloud Ops) / **Closed** | HVM — 25-01033973 Users cannot open Confirmation Response screen in TIPS Web | §8 | 25-01033973 |
| **#1746577 / #1754745** | AppOwner Task (Global Cloud Ops) / **In Engineering** | HVM — 25-01033973 RCA — Confirmation Response screen won't open | §8 | 25-01033973 |
| **#1726591** | Requirement / **Closed** | QMCW-2970 — Insert NOMCYCLNTF into Security Group 1016 | §10 | — |

> **Takeaway:** TIPS nomination defects split into (a) **data-integrity** cases — inverted date ranges and duplicate noms — dispositioned operationally with a **data clean-up script**, with a validation (`QGValidationNomGasDates`) added so they can't recur; and (b) **batch-chain / screen** bugs — NOMPOST not firing, CFCREATE double-update, UTILCALDT not scheduled, Confirmation Response qty/precedence and Web-vs-Classic parity. The biggest "looks like a bug but is config" trap is **AutoConfirm with a Manual contract header** (26-01069130) and **NNG028 added by an upgrade** (26-01064773).

---

## 14. Database Tables Reference

| Table | Purpose |
|-------|---------|
| **`QCTRL_NOM_DTL`** (`qctrl_nom_dtl`) | **Nomination Transaction Detail — the inverted BEG_GAS_DAY/END_GAS_DAY rows land here (§4); target of the data clean-up scripts.** |
| **`QCTRL_CONF`** | Confirmation table behind the **Confirmation Response screen**; built by **UTILCALDT** from `QTRAN_CAL_DATE` (§8). |
| **`QTRAN_CAL_DATE`** | Staging table for `QCTRL_CONF` (UTILCALDT source). If UTILCALDT doesn't run, QCTRL_CONF is empty → blank confirmation screen. |
| `QTRAN_*` (nom transaction) | Nomination transaction headers/details written by NOMPOST. |
| **`QTIP_RPTS_NOM_CYCLE_SUMMARY`** | NOM cycle summary — used to find the meter with no confirmation for a gas day (NOMCYCLNTF null-ref, §10). |
| **`QARCH_PROCESS_MSG_LOG`** | **Process message log by `PROCESS_QUEUE_ID` (PQID)** — read this for the failing NOMPOST/CFCREATE/NOMDEL/NOMCYCLNTF step (filter out DEBUG/INFO/WARN). |
| **`PACTRL_CYCLE`** | Cycle config (e.g. `GAS_FLOW_START_TIME_OFFSET`) — cycle-timing tuning (26-01088719 set offsets for cycles 3/4). |
| Validation Rule Assignment (metadata) | Where **NNG028** and other nom rules are assigned per Company/Module (§6). Global config `Number_Of_Days_In_Future_Allow_Noms`. |
| `Quorum.TIPS.Metadata / STANDARD 16.0` `QARCH_CTRL_OBJECT_*` | Metadata registration of validations incl. `QGValidationNomGasDates`. |

> Column-name caveat: `QCTRL_NOM_DTL` and the `BEG_GAS_DAY/END_GAS_DAY` fields are confirmed from case text (25-01051919, 24-00962813). `QCTRL_CONF`/`QTRAN_CAL_DATE`/`QARCH_PROCESS_MSG_LOG`/`QTIP_RPTS_NOM_CYCLE_SUMMARY` are confirmed from case resolutions (25-01001893, 22-00875002). Verify exact column names against the schema before scripting.

---

## 15. Diagnostic SQL

### A. Failing-process message log (NOMPOST / CFCREATE / NOMDEL / NOMCYCLNTF) by PQID
```sql
SELECT * FROM QARCH_PROCESS_MSG_LOG
WHERE  PROCESS_QUEUE_ID = '<PQID>'
  AND  LOG_MSG_TYPE_CD NOT IN ('DEBUG','INFO','WARN')
ORDER BY <seq/log time>;
```

### B. Find inverted-date nominations (the §4 corruption)
```sql
SELECT *                                   -- key cols: SR/contract, REC/DEL meter, BEG_GAS_DAY, END_GAS_DAY
FROM   QCTRL_NOM_DTL
WHERE  BEG_GAS_DAY > END_GAS_DAY           -- impossible range (e.g. 11/01 > 10/31)
   /* AND scope to TSP/company/SR/contract/gas-month before any script */;
```

### C. NOMCYCLNTF — meter missing a confirmation for a gas day
```sql
SELECT * FROM QTIP_RPTS_NOM_CYCLE_SUMMARY
WHERE  /* company + gas-day filter */;     -- look for the meter with no confirmation row
```

### D. Confirmation screen empty — is QCTRL_CONF built for the gas day?
```sql
SELECT COUNT(*) FROM QCTRL_CONF  WHERE /* company + gas-day filter */;   -- 0 rows ⇒ UTILCALDT likely didn't run (§8)
SELECT COUNT(*) FROM QTRAN_CAL_DATE WHERE /* same filter */;             -- staging present but QCTRL_CONF empty ⇒ run UTILCALDT + restart services
```

### E. Cycle timing offsets (PACTRL_CYCLE)
```sql
SELECT CYCLE_ID, GAS_FLOW_START_TIME_OFFSET FROM PACTRL_CYCLE WHERE CYCLE_ID IN ('3','4');
-- e.g. 26-01088719 set offsets 28800 / 43200 to correct cycle gas-flow start times.
```

> All scripts that **modify/delete** nom data must be run by Cloud Ops with a verify-SELECT first and wrapped in a transaction, scoped to the specific SR/contract/gas-day. Salesforce/ADO are read-only for investigation.

---

## 16. Escalation Guidance

**Cloud Ops / Config (you can usually resolve or hand off without Engineering):**
- Inverted-date / duplicate nom **data clean-up scripts** in `QCTRL_NOM_DTL` (§4) — most common.
- **UTILCALDT not scheduled** → schedule it + restart services (§8); NOMCYCLNTF security-group provisioning (§10).
- **NNG028 / future-nom** — unassign the rule on Validation Rule Assignment or adjust `Number_Of_Days_In_Future_Allow_Noms`, then run Nightly Nomination Validation (§6).
- **AutoConfirm** = set contract-header Confirmation Method to Auto (§9).
- Cycle-timing offsets in `PACTRL_CYCLE` (§15-E).

**Engineering (Software Defect — route with PQID, env, exact error, build/version):**
- NOMPOST not firing / CFCREATE double-update / NOMPOST post-step errors (§5; #1716164, #1447164, #1660388).
- Confirmed-qty overwritten by nom / conf→sched not propagating / Alt-Conf-Qty Web≠Classic / Confirmation Response won't open (§9; 24-00966802, 22-00526756, 22-00676427, #1746576).
- NGLPROD ACCESS_VIOLATION forecasting chain (§11; 24-00945026).
- If a client is **not on the build containing #1769494**, the inverted-date corruption will recur — push the upgrade alongside the data script.

**Always confirm before escalating:** Web vs Classic? Auto vs Manual confirm? Did the batch job *run* (trigger gap) or *run and error* (defect)? Is it really a bug, or a customer-created impossible/duplicate nom (data script) — check §12 first.

---

*Skill created: 2026-06-11*
*Based on: ~344 closed TIPS Nominations/Confirmations/Scheduling/Availability/Forecasting SF cases (71 actionable: 35 Application Configuration + 29 Software Defect + 7 ChangeConfig) + ~70 Customer Error/Training cases + ADO work items #1672104, #1769494, #1716164, #1660388, #1447164/#1456678, #1556874, #1490446, #1746576/#1746577/#1754745, #1726591. Implementing class confirmed: Quorum.TIPS.Web/Quorum.TIPS.Validation/.../QGValidationNomGasDates.cs.*
*Companion: SKILL_TIPS_Allocations_PPA_Imbalance.md, SKILL_TIPS_Batch_Processing.md, SKILL_TIPS_CAW.md, SKILL_TIPS_Reporting_Statements.md.*
