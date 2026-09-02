# SKILL: QPTM Allocations Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-01 | **Product:** QPTM (My Quorum Gas Pipeline)
**Scope:** Allocation processing (ALALLOCATE / PANIGHTLY / PADAILY / ALSCHDOVRD), PDA (Predetermined Allocation) submission & methods (ranked / pro-rata / swing / tiered), wellhead/shared allocation (GSWHALLOC/GSWHALLAPP), PTR overlay & PPA (prior-period adjustments), OBA / imbalance & Authorization to Post Imbalance, Customer Account / Inventory accumulation, allocation overrides (Daily Allocated Quantity Maintenance), fuel/L&U in allocation, and allocation reports (ALR/INX/IN41).
**Companion:** For nomination submission/overlap/ghost-nom issues see **SKILL_Nominations.md**; for EDI/cycle-deadline see **SKILL_EDI_Troubleshooting.md**. Allocations *consumes* noms + measurement and produces allocated quantities, inventory, and imbalance — do not duplicate those skills; cross-references noted.

> Evidence base: ~286 QPTM Allocations cases with Root Cause = Software Defect (222) or Application Configuration (64), plus ~285 Customer Error/Training cases for the Expected-Behavior section. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining.

---

## TABLE OF CONTENTS

1. [Quick Triage Checklist](#1-quick-triage-checklist)
2. [Allocations Concepts & Pipeline](#2-allocations-concepts--pipeline)
3. [Symptom → Root-Cause Matrix](#3-symptom--root-cause-matrix)
4. [ALALLOCATE / Allocation-Process Failures (HIGH FREQUENCY)](#4-alallocate--allocation-process-failures-high-frequency)
5. [PDA Submission & Allocation Methods (Rank / Pro-Rata / Swing / Tiered)](#5-pda-submission--allocation-methods)
6. [Wellhead / Shared Allocation (GSWHALLOC / GSWHALLAPP / WGT)](#6-wellhead--shared-allocation)
7. [PTR Overlay & PPA (Prior-Period Adjustments)](#7-ptr-overlay--ppa)
8. [OBA / Imbalance & Authorization to Post Imbalance](#8-oba--imbalance--authorization-to-post-imbalance)
9. [Customer Account / Inventory Accumulation](#9-customer-account--inventory-accumulation)
10. [Allocation Override / Daily Allocated Quantity Maintenance](#10-allocation-override--daily-allocated-quantity-maintenance)
11. [Fuel / L&U / Vaporization in Allocation](#11-fuel--lu--vaporization-in-allocation)
12. [Allocation Reports (ALR / INX / IN41)](#12-allocation-reports)
13. [Expected Behavior / User Education](#13-expected-behavior--user-education)
14. [Key Code Files, Processes & Repos](#14-key-code-files-processes--repos)
15. [Database Tables Reference](#15-database-tables-reference)
16. [Diagnostic SQL Queries](#16-diagnostic-sql-queries)
17. [Standardized Fix-Scripts (VERBATIM, redacted)](#17-standardized-fix-scripts-verbatim-redacted)
18. [Known Historical ADO Bugs](#18-known-historical-ado-bugs)
19. [Escalation Decision Tree](#19-escalation-decision-tree)

---

## 1. Quick Triage Checklist

```
[ ] 1. What EXACTLY failed — a batch process (ALALLOCATE/PANIGHTLY/PADAILY/ALSCHDOVRD/GSWHALLOC), a screen
       (PDA Submission / Daily Allocated Quantity Maintenance / Authorization to Post Imbalance), or a report (ALR/INX)?
[ ] 2. TSP_NO + Accounting Month (acctg_mth) + Production Month (prod_dt) + Gas Day(s)? Allocations is acctg-month-centric.
[ ] 3. The PROCESS_QUEUE_ID (PQID) of the failed run? (clients usually supply it — it keys the log + trace)
[ ] 4. EXACT error text? Common: "unique constraint (...AK_ALCTRL_ALLOC2)", "Child quantity exceeds parent quantity",
       "Error in Registered SQL", "Dll Not Found QPDLLPIPELINEMGRAL_EQC", "Could not find the masterlinks for the grid",
       "location is not tied to an allocation plan", "FlipNegativeNodes() failed".
[ ] 5. Web or Classic? Many PDA / Allocated-Qty-Maintenance / Authorization-to-Post-Imbalance bugs are Web-only.
[ ] 6. Internal or External (shipper) user? PDA TT defaults, imbalance-post access, and override rights differ.
[ ] 7. Is measurement loaded & correct? Allocation failures are very often bad upstream measurement (decimals,
       child>parent, missing parent volume) — check before suspecting a code bug.
[ ] 8. WGT (wellhead) meter involved, and has Wellhead Allocation been APPROVED for the prod month? Approval LOCKS reallocation.
[ ] 9. Is this a retro / PPA (prior-period adjustment) month, or a TIPS→QPTM (Evolution) integrated client (PTR overlay)?
[ ] 10. One-off or recurring? Recurring ALALLOCATE failure for a TSP usually = bad nom/measurement data (data-script cluster).
```

### Where does the issue live?
| Entry point / symptom | Likely cluster | First place to look |
|------------------------|----------------|---------------------|
| ALALLOCATE / PANIGHTLY fails with an error | §4 Process failures | Process log by PQID; `ALCTRL_ALLOC`, nom/measurement data |
| "unique constraint AK_ALCTRL_ALLOC2 violated" | §4 (duplicate alloc rows) | duplicate insert into `ALCTRL_ALLOC`; data script |
| PDA submitted in Web but allocation ignores it | §5 PDA | Nom_ID / Nom_HashID assignment on PDA; `ALALLOCATE` |
| Allocation not using ranks / wrong method (pro-rata) | §5 PDA methods | PDA TT, allocation-plan level, rank config |
| WGT meter completes "with warning" / won't reallocate | §6 Wellhead | `TIPS_PROCESS_CONTROLS_PRM`, WH approval status |
| PTR/PPA not overriding prior month | §7 PTR/PPA | `ALPTRSYNC`, `QTIP_TRAN_PLANT_PTR`, `ALCTRL_ALLOC_OVRD` |
| Imbalance duplicated on report / can't post imbalance | §8 OBA/Imbalance | INX02/IN41 view; Imbal Trade access; web picklists |
| Inventory / Customer Account not updating | §9 Inventory | CUSTACCTACCUM job; TOS code-table setup; loc end-dates |
| Can't override allocated qty on a level | §10 Override | Daily Allocated Quantity Maintenance (level 2/5/101) |
| Fuel/vaporization wrong | §11 Fuel | fuel rate time-slices; LNG child-loc formula |
| Report shows 0 / duplicate / "No Data" | §12 Reports | registered SQL view; rounding; null PTR |

---

## 2. Allocations Concepts & Pipeline

### What allocation does
Allocation distributes **measured/scheduled volume at a location** across the **contracts/shippers/operators** entitled to it, for an **accounting month**. Inputs: nominations/scheduled quantities, measurement, PDAs, fuel rates. Outputs: allocated quantities (`ALCTRL_ALLOC`), which then feed **Inventory / Customer Account** and **Imbalance**, which feed **Billing**.

```
[Noms/Sched Qty] + [Measurement] + [PDA instructions] + [Fuel rates]
      │
      ▼  ALALLOCATE (a.k.a. Allocation Process; nightly = PANIGHTLY/PADAILY)
[ALCTRL_ALLOC  (allocated quantities, by level/trans-type)]
      │
      ├──► Inventory / Customer Account Accumulation (CUSTACCTACCUM)
      ├──► Imbalance / OBA (Authorization to Post Imbalance → INX/IN41 reports)
      └──► Billing
```

### Allocation methods (the "how volume is split")
| Method | Behavior | Notes |
|--------|----------|-------|
| **Ranked** | Fill nominations in rank order 1→999 until volume exhausted | NAESB shipper-provided ranks; if system ignores ranks and pro-rates → defect/config (24-00951976) |
| **Pro-Rata** | Split proportionally across paths/operators | Default when ranks aren't applied; LNG multi-operator must pro-rate (24-00962061) |
| **Swing** | One contract/OBA absorbs the residual ("swing to OBA") | Set up on PDA Submission; needs loc tied to an allocation plan (26-01083452) |
| **Percentage PDA** | Allocate by percent; **ranks within a level must sum to ≤100** | Over-100 now correctly errors (24-00954877) |
| **Tiered (single vs multi)** | Allocation resolves through levels (2, 5, 6, 101...) | Some clients are single-tier only (24-00949194) |

### PDA = Predetermined Allocation
Standing instructions for how to allocate at a location/contract **before** measurement arrives, entered on the **PDA Submission** screen. Keyed by TSP / location / service-requester contract / effective-date-range / allocation level (Level 2/5/6...) and a **PDA Transaction Type (TT)** (e.g. TT 55, TT 6). PDAs can be submitted by external shippers (Web) or internal schedulers (Classic). A PDA that doesn't get a proper Nom_ID/Nom_HashID is silently ignored by ALALLOCATE (23-00899058).

### Levels & Transaction Types
Allocation records exist at multiple **levels** (2 = path/operator, 5, 6, 101 = contract roll-up). Override quantities (Alloc, PTR, Schedule) must be editable at the applicable level (25-01050075). **Allocation TT** and **Prop TT** are the trans-type codes that tag allocated rows; NAESB clients want exactly one default per location, not operator-selectable (24-00949200).

### Key acctg concepts
- **Accounting Month (acctg_mth) vs Production Month (prod_dt):** allocation runs for an acctg month but can carry retro production months (PPAs). Offset resolution is a known failure point (24-00960557, 22-00598104).
- **WGT (Wellhead) meter & approval:** once **Wellhead Allocation is approved** for a prod month, WGT receipt meters are **locked** from reallocation — by design when `TIPS_PROCESS_CONTROLS_PRM=1` (24-00969830, 24-00982115).
- **PTR (Plant Thermal Reduction / TIPS overlay):** for Evolution (TIPS↔QPTM) clients, PTR values sync from TIPS via `ALPTRSYNC` and overlay onto allocation (§7).

---

## 3. Symptom → Root-Cause Matrix

| Symptom (message / behavior) | Most common root cause | Fix type | Evidence |
|------------------------------|------------------------|----------|----------|
| ALALLOCATE/PANIGHTLY fails: `ORA-00001 unique constraint (...AK_ALCTRL_ALLOC2)` | Duplicate allocation rows / re-insert on restatement day; or bad nom data | **Data script** (then code patch) | 22-00524917, 25-00998023, 23-00903346 |
| ALALLOCATE fails: "Could not find the masterlinks for the grid" | Often user/setup or transient; verify params before escalating | Answer/educate or config | 26-01100678 |
| ALALLOCATE: `FlipNegativeNodes() failed` / "Error setting value for column ... NNCTRL_NOM_HDR" | Bad/mismatched nom header–detail data | Data fix + bug | 23-00903346, ADO #1652157 |
| ALALLOCATE: "Error in Registered SQL" | Defect in a registered allocation SQL view | Code fix | 25-00996952, ADO #1706632 |
| ALALLOCATE: "Dll Not Found QPDLLPIPELINEMGRAL_EQC" + Continue-on-fail=False | Missing/unregistered C++ batch DLL in env | Deploy/infra fix | 24-00994160, ADO #1705988 |
| Index/PPA effective-date mid-month → header/detail mismatch → ALALLOCATE fails | Index time-slice creates header/detail mismatch | Code fix | ADO #1796121 |
| Reallocate-Ind run errors out | Reallocation-indicator path defect | Code fix | ADO #1734843 (XCL) |
| **Running ALALLOCATE with "Recalc Fuel" + no location specified DELETED a month of allocations** | Process doesn't validate params before deleting; wipes allocate-as-scheduled/percent-PDA data | Code fix (param guard) | 25-01010799 |
| PDA submitted via Web ignored by allocation; Classic re-entry works | PDA Submission didn't assign Nom_ID/Nom_HashID when "Load Effective Noms" checked | Code fix | 23-00899058 |
| PDA Submission allows To-Date < From-Date / overlapping ranges | Web PDA effective-date validation/date-split gap (Classic was stricter) | Code fix | 24-00828349, 24-00949374, 22-00828349 |
| PDA "Alloc Methd" column blank in Web | Web grid render/preserve defect (data is in DB) | Config/code | 24-00941596 |
| PDA TT 6 won't accept Up Party (proprietary code not filling) | PDA level-detail Up-party field defect | Code fix | 24-00972517 |
| Allocation uses pro-rata instead of shipper ranks | Ranks not applied at/below contract level | Code fix (NAESB) | 24-00951976 |
| LNG multi-operator not pro-rating; LNG override ≠ schedule qty | LNG/ALSCHDOVRD allocation defect | Code (hotfix #1670362) | 24-00962061, 24-00962851 |
| ALSCHDOVRD "Allocate Entire Month End" not covering whole month | ALSCHDOVRD month-range defect | Code fix | 24-00947154 |
| WGT meter allocates "with warning" instead of stopping after WH approval | Should hard-error post-approval | Code fix | 24-00982115, 24-00969830 |
| GSWHALLOC: "Invalid filter for an IN type query / AllocationLatestHistory.ProdMth" when loc WGT in prior but not current month | WGT-changed-mid-period query defect | Code fix | 24-00981516 |
| KW (Keep-Whole) locations not allocated for PPA | Keep-Whole PPA allocation defect | Code fix | 24-00994255 |
| PTR overlay in partial/scheduling month adds extra last/calendar day | PTR overlay partial-month defect | Code fix | 24-00975390 |
| Measurement decimals saved via Bulk Edit → allocation fails "Child qty exceeds parent" | TSP decimal formatting not applied to Bulk Edit grid | Code fix | 24-00939019 |
| Imbalance duplicated on INX02 / IN41 | Report/registered-SQL dedup defect | Config/code | 24-00964240, 22-00609015 |
| Auth-to-Post-Imbalance: missing picklists (Web), can't run | Web picklist/code-table render + access (Imbal Trade) | Config | 24-00964617, 24-00964634, 25-01013422 |
| Customer Account / Inventory not updating after allocation | Missing TOS code-table setup, or loc end-dated while noms exist; job timeout | Config | 24-00966286, 24-00964259 |
| Can't override alloc qty (level 2/5/101): "Override quantity is mandatory" though qty shown (Web) | Web override-validation defect (Classic OK) | Code (patches 70/71) | 25-01050075 |
| Unallocated Volumes report (ALR_26) full of 0-qty rows | Rounding not held to TSP UOM; report filter | Code fix | 22-00570045, 22-00693361 |
| Slow allocation / inventory close-time blowups | Query performance (QNomHashMgr, inventory sub-process) | Perf code fix | ADO #1621519, 24-00988881, 23-00882839 |

---

## 4. ALALLOCATE / Allocation-Process Failures (HIGH FREQUENCY)

The single largest actionable cluster. ALALLOCATE (Web "Allocation Process"; nightly variants **PANIGHTLY** / **PADAILY**) recomputes allocated quantities for a TSP + accounting month. These arrive frequently flagged **CRITICAL** because allocation gates inventory balances and month-end close.

### The dominant failure: `unique constraint (...AK_ALCTRL_ALLOC2) violated`
The process tries to **re-insert allocation rows that already exist** in `ALCTRL_ALLOC` (e.g. `QSQLID_AllocateOutput::m_Output_InsTranForRestatementDay`). Root causes seen:
- A prior run already wrote the rows (restatement/re-run race) — **22-00524917** (TSP 499, `ORA-00001 AK_ALCTRL_ALLOC2`), worked around with a data script + long-term patch.
- **Bad nomination data** feeding allocation — **25-00998023** (CRITICAL, REX gas days 12–13): resolved with "Data clean-up script to clean bad nom data."
- **Duplicate Account Managers** on a BP causing duplicate-key — **23-00903346** (BP 4528 had two Account Managers): resolved by adding a **new validation rule** to prevent the dup.

### Other ALALLOCATE error signatures (all real)
| Error | Cause | Disposition | Evidence |
|-------|-------|-------------|----------|
| `QPSAlloc::FlipNegativeNodes() failed` + "Error setting value for column for primary table NNCTRL_NOM_HDR" | Bad/mismatched nom header data | Fix nom data; code bug | ADO #1652157 |
| "Error in Registered SQL" (tsp 24/8925, 9/30 gas day) | Registered allocation SQL view defect | Code fix | ADO #1706632 (25-00996952) |
| "Dll Not Found QPDLLPIPELINEMGRAL_EQC — Continue Process on Failed Execute Is False" | C++ allocation DLL not deployed/registered in env | Infra/deploy | ADO #1705988 (24-00994160) |
| "Index time-slice creates header/detail mismatch" → ALALLOCATE failure | Mid-month index eff-date + PPA generate mismatch | Code fix | ADO #1796121 |
| ALALLOCATE erroring when **Reallocate Ind** checked | Reallocation-indicator path | Code fix | ADO #1734843 |
| "Child quantity exceeds parent quantity" | Measurement decimals / child>parent volume | Fix measurement (see §6/§11) | 24-00939019 |

### CRITICAL data-loss trap — Recalc Fuel with no location
Running the Allocation Process with **"Recalc Fuel" checked but NO location specified** (just acctg month + entire-month) **deleted all allocated data for the month** for locations that get allocated via *allocate-as-scheduled* or *percent PDA* (they have no measurement to re-derive from). Case **25-01010799** (ETP, March 2025). Until the param-guard fix ships, **warn users never to check Recalc Fuel without scoping a location**, and recovery = re-run allocation for the affected locations.

### PANIGHTLY / accounting-offset failures
- **22-00598104:** PANIGHTLY failing since 12/31 because the **accounting offset = 0** path failed — data script.
- **24-00960557 (MGD):** PA Nightly "Not Resolving Accounting Month Offset" — open-acctg-month param not resolving; code fix.
- **22-00524917 (TSP 499):** PANIGHTLY duplicate-key (above).

### Diagnostic — start here
```sql
-- A. Is there a duplicate allocation row (the AK_ALCTRL_ALLOC2 collision)?
SELECT TSP_NO, LOC_ID, ALLOC_GAS_DAY, ACCTG_MTH, TRANS_TYPE_ID, SR_CTR_NO,
       COUNT(*) AS DUP_CT
FROM   ALCTRL_ALLOC
WHERE  TSP_NO = <TSP_NO> AND ACCTG_MTH = '<ACCTG_MTH>'
GROUP BY TSP_NO, LOC_ID, ALLOC_GAS_DAY, ACCTG_MTH, TRANS_TYPE_ID, SR_CTR_NO
HAVING COUNT(*) > 1;

-- B. Pull the batch SQL trace for the failing PQID (the exact insert that errored)
SELECT * FROM QARCH_QFCBATCH_SQL_TRACE
WHERE  PROCESS_QUEUE_ID = <PQID> ORDER BY SEQ_NO;   -- look for m_Output_Ins* statements

-- C. Two Account Managers on a BP (the 23-00903346 duplicate-key root cause)
SELECT BA_NO, COUNT(*) FROM <ACCOUNT_MANAGER_XREF>
WHERE  TSP_NO = <TSP_NO> AND BA_NO = <BP_NO> GROUP BY BA_NO HAVING COUNT(*) > 1;
```

### Fix recipe
1. Get **PQID, TSP, acctg month, gas day(s)** and the exact error. Open the process log (double-click the error row to see log messages — per ADO #1681051).
2. If `AK_ALCTRL_ALLOC2` / duplicate-key → run diagnostic A/B → provide a **data clean-up script** (clean duplicate alloc rows / bad nom data) to Cloud Ops, then re-run ALALLOCATE for the scoped month. (25-00998023, 22-00524917.)
3. If "Registered SQL" / "Dll Not Found" / FlipNegativeNodes → it's a **code/deploy bug** — match to the ADO items in §18 and confirm the fix version.
4. **Never** advise a blind Recalc-Fuel-no-location re-run (25-01010799).

---

## 5. PDA Submission & Allocation Methods

PDAs are the standing allocation instructions. This cluster (~28 PDA + many "allocation method" cases) splits into (a) **Web-vs-Classic PDA Submission defects**, (b) **allocation-method/NAESB config** (ranks vs pro-rata, TT defaults, tiering), and (c) **swing/allocation-plan setup**.

### 5a. Web PDA Submission defects
| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| PDA submitted in **Web** is **ignored by ALALLOCATE**; same change in Classic works | Web PDA didn't assign **Nom_ID / Nom_HashID** when "Load Effective Noms" checked | Code fix | 23-00899058 |
| To-Date < From-Date submits with no error (Core/Classic rejects) | Web effective-date validation gap | Code fix | 24-00949374 |
| Updating eff-from creates **overlapping date ranges** instead of date-splitting | Web date-split logic differs from Classic | Code fix | 22-00828349 |
| "Alloc Methd" column appears **blank** in Web (value is in DB) | Grid render/preserve defect | Config/code | 24-00941596 |
| Percentage PDA > 100 used to submit; now errors | Validation added (correct) | Data script to clean legacy | 24-00954877 |
| Duplicate overlap errors fire **in multiples of 7** per TSP | Overlap-validation defect | Code fix | 23-00912990 |
| **PDA TT 6** won't accept Up Party (proprietary code won't fill, then "required") | Level-detail Up-party field defect | Code fix | 24-00972517 |
| PDA Submission poor performance in Web | Calc-Schd-Qty record-limiting | Code fix | ADO #1742027 (24-00983745) |
| New TSP name not displaying on PDA Submission / Auth-to-Post-Imbalance | Newly-created-TSP name binding | Code fix | ADO #1719402 |

> **Web ≠ Classic is the recurring theme.** When a client reports "PDA behaves differently in Web," reproduce in BOTH; the defect is almost always the Web screen being more permissive (skips validation) or failing to persist IDs the allocation engine needs.

### 5b. Allocation method / NAESB config (mostly Application Configuration)
| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Allocation applies **pro-rata** when shipper-provided **ranks** should fill noms 1→999 | Ranks not applied at/below contract level | Code (NAESB) | 24-00951976 |
| Allocation TT / Prop TT operator-selectable; want one default (TT 55) per location | Config: lock default, hide from external operator | Config | 24-00949200 |
| Client wants **single-tier only** — remove PDA security & SR value | Config: strip PDA from shipper security + allocation plan | Config | 24-00949194 |
| "Location is not tied to an allocation plan" when setting up **swing to OBA** | Missing allocation-plan/loc-group ref data | **Data script** (see §17) | 26-01083452 |

### Diagnostic
```sql
-- PDA rows for a location/contract (look for overlapping eff ranges, blank method, missing Nom_HashID)
SELECT TSP_NO, LOC_ID, SR_CTR_NO, PDA_LEVEL, PDA_TT, ALLOC_METHD_CD,
       PCT, RANK, EFF_DT_FROM, EFF_DT_TO, NOM_ID, NOM_HASH_ID, USER_ID, UPDT_DT
FROM   <PDA table e.g. ALCTRL_PDA>
WHERE  TSP_NO = <TSP_NO> AND LOC_ID = '<LOC>'
ORDER BY EFF_DT_FROM, PDA_LEVEL, RANK;
-- Red flags: EFF_DT_TO < EFF_DT_FROM; overlapping ranges; ALLOC_METHD_CD blank; NOM_HASH_ID null (the 23-00899058 pattern).
```

---

## 6. Wellhead / Shared Allocation (GSWHALLOC / GSWHALLAPP / WGT)

For producers/gathering (Permian, South Texas, ETP), **WGT (Wellhead) meters** are allocated via **GSWHALLOC** and approved via **GSWHALLAPP**. Approval is a hard gate.

### Key behavior — approval LOCKS WGT reallocation
- When **`TIPS_PROCESS_CONTROLS_PRM = 1`** and shared Wellhead Allocation is **approved** for a prod month, **WGT receipt meters cannot be reallocated**. With `=0` the system (wrongly, for these clients) still allows it. Case **24-00969830** (ETP 30051) — the downstream delivery-meter allocation stopped on error because WH was approved for all STX plants.
- Allocating a WGT meter after WH approval **should hard-stop on error**, but currently **completes with a warning and doesn't allocate** — case **24-00982115** (code fix to convert warning→error).

### GSWHALLOC failure on WGT-changed-mid-period
Case **24-00981516** (UATB Permian): location 52308 is WGT in a prior prod month but became a child of an aggregate meter (no WGT attribute) in the current acctg month. A PPA for the prior period + GSWHALLOC throws:
```
Split Interface Error: Error querying allocation records for the ACCT_MTH and TSP_NO
GSWHALLOC: DoExecute() failed ... Filter Name 'AllocationLatestHistory.ProdMth': Invalid filter for an IN type query
WGT attribute is missing for location: 52308
```
Production completes with warning; UAT errors → code defect in the WGT-history filter.

### Related
- **GSWHALLAPP** generated an approval record for **ETP as plant_no** incorrectly (24-00969554); and **does not approve PPAs originated in TIPS** (24-00985592).
- **Non-WGT meters can't run** allocation after WH approval on error (24-00969830 above).

### Diagnostic
```sql
-- Is the location WGT for the prod month, and is Wellhead Alloc approved?
SELECT LOC_ID, PROD_MTH, IS_WGT, AGG_PARENT_LOC_ID
FROM   <wellhead loc attr / AllocationLatestHistory source>
WHERE  TSP_NO = <TSP_NO> AND LOC_ID = '<LOC>' AND PROD_MTH = '<PROD_MTH>';

-- TSP config that gates WGT reallocation after approval
SELECT TSP_NO, CONFIG_KEY, CONFIG_VALUE FROM QARCH_TSP_CONFIG
WHERE  TSP_NO = <TSP_NO> AND CONFIG_KEY = 'TIPS_PROCESS_CONTROLS_PRM';
```

---

## 7. PTR Overlay & PPA (Prior-Period Adjustments)

For **Evolution** clients (TIPS ↔ QPTM integrated), **PTR** (plant values) sync from TIPS via **ALPTRSYNC** and overlay onto allocation; **PPAs** (prior-period adjustments) restate closed/prior production months.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| **Keep-Whole (KW)** locations not allocated for PPA | KW PPA allocation defect | Code fix | 24-00994255 |
| PTR overlay in partial (scheduling) month adds an extra last/calendar day | Partial-month PTR overlay defect | Code fix | 24-00975390 |
| TIPS PTR PPA did not override previous actualized PTR prior month | Overlay-precedence defect | Code fix | 24-00974145 |
| Blank-out PTR Override Reason in QPTM when PTR Qty is null in TIPS | Sync nulling defect | Code fix | 23-00935177 |
| PPA initiated in TIPS shouldn't need a pipeline approval for pre-Evolution prod months | Approval-gating defect | Code fix | 24-00973513 |
| Stage imbalance overlay unique-constraint on `ESUITE_QENT.BLTRAN_STAG_IMB_OVRLY` | Duplicate insert on overlay staging | Code fix | 24-00984737 |

### Diagnostic
```sql
-- PTR sync source (TIPS) vs QPTM override + allocation for a KW/PTR meter
SELECT * FROM ESUITE_QENT.QTIP_TRAN_PLANT_PTR
WHERE  MTR_NO = '<KW/PTR meter>' AND PROD_DT = '<PROD_DT>' AND GAS_DAY = '<GAS_DAY>';

SELECT * FROM QPTM.ALCTRL_ALLOC_OVRD
WHERE  TSP_NO = <TSP_NO> AND LOC_ID = '<LOC>' AND ALLOC_GAS_DAY = '<GAS_DAY>';

SELECT * FROM QPTM.ALCTRL_ALLOC
WHERE  TSP_NO = <TSP_NO> AND LOC_ID = '<LOC>' AND ALLOC_GAS_DAY = '<GAS_DAY>'
   AND ACCTG_MTH = '<ACCTG_MTH>' AND TRANS_TYPE_ID = <TT>;
```
(Query shape lifted from case 24-00994255's own repro steps — these are real QPTM/ESUITE_QENT tables.)

---

## 8. OBA / Imbalance & Authorization to Post Imbalance

Allocation produces imbalance (scheduled/allocated vs entitlement) against **OBA** (Operational Balancing Agreement) contracts; users post/authorize it on the **Authorization to Post Imbalance** screen; it surfaces on **INX02 / IN41 / IN40 / IN41** reports and imbalance widgets.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Allocation **does not allocate to the OBA contract** on some locs/dates (worked in v4.1, not v17) | Allocation engine OBA-target defect | Code fix | 22-00643981 (TPC) |
| INX02 **duplicating imbalance** for an OBA (system value correct) | Report/registered-SQL dedup | Config/code | 24-00964240 |
| IN41 Monthly Imbalance w/ Location Details — duplicates | Report dedup | Code/config | 22-00609015 |
| Auth-to-Post-Imbalance (Web): **Contracts grid missing picklists / tolerance-basis dropdown** (Classic OK) | Web picklist/code-table binding | Config (patch) | 24-00964617, 24-00964634 |
| User can't run Auth-to-Post-Imbalance (access error) | Missing **"View" Imbal Trade** access | Config (grant access) | 25-01013422 |
| Auth-to-Post-Imbalance report **hangs** for external users (ALRX24) | External-user report perf | Code fix | 25-01027093 |
| Access issue posting imbalances for external users | Security config | Config | 22-00691338 |

> **Web-vs-Classic again:** the Auth-to-Post-Imbalance screen has repeated Web-only picklist/render defects (24-00964617). If a client says "Classic works, Web doesn't," it's a known Web-screen class of bug — check the patch level first.

---

## 9. Customer Account / Inventory Accumulation

After allocation, **CUSTACCTACCUM** (Customer Account Accumulation) rolls allocated/inventory activity into shipper customer accounts. Failures here are mostly **config/data**, not code.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| Allocations run but **Customer Account not updating / inventory activity not displayed** | **Missing TOS setup on code table 27205** | Config | 24-00966286 |
| **CUSTACCTACCUM job runs forever / never completes** | Location **end-dated while noms still exist** (through June); plus job **timeout** in `qpec.ini` | Config (fix loc end-date + raise timeout) | 24-00964259 |
| Unable to delete K# from inventory account (Web): "Primary Contract ... already associated to a customer account" | Web validation blocks delete (Classic allows) | Config (disable/adjust Web validation) | 26-01080109 |
| Inventory processing time blowing up close (load-following) | Inventory sub-process query perf | Code fix (perf) | 24-00988881, 24-00987946 |
| Chart of Accounts — new TOS & TOC setup | Setup request | Config | 25-01058721 |

### Diagnostic
```sql
-- TOS code-table coverage (the 24-00966286 root cause — missing TOS on code table 27205)
SELECT * FROM <code-table 27205 / QCODE_*> WHERE TSP_NO = <TSP_NO>;

-- Locations end-dated while noms still exist (stalls CUSTACCTACCUM — 24-00964259)
SELECT l.ID_LOC, l.EFF_DT_TO, MAX(n.END_GAS_DAY) AS LAST_NOM_DAY
FROM   NNCTRL_LOC l JOIN NNCTRL_NOM_DTL n ON n.TSP_NO=l.TSP_NO AND n.REC_LOC_ID=l.ID_LOC
WHERE  l.TSP_NO=<TSP_NO> AND l.EFF_DT_TO < n.END_GAS_DAY
GROUP BY l.ID_LOC, l.EFF_DT_TO;
```

---

## 10. Allocation Override / Daily Allocated Quantity Maintenance

The **Daily Allocated Quantity Maintenance** screen lets users manually override allocated quantities at levels 2, 5, 101 (Alloc, PTR, Schedule override qtys).

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| "Override quantity is mandatory with an update reason" though qty is on screen (Web, level 2/5/101); Classic OK | Web override-validation defect | Code (patches 70 & 71) | 25-01050075 |
| Daily allocation override on TSP 400 not producing expected result | Override config | Config | 25-01047065 |
| Decimal places wrong on Daily Allocated Maintenance (APL 2023.04) | Decimal formatting | Config/code | 24-00960552 |
| Unable to access Daily Allocated Quantity results in Classic | Classic screen defect | Code | 24-00987849 |
| Order of columns / variance Web-vs-Classic / returns no data after build | Screen render defects | Code/config | 24-00948173, 22-00712615, 22-00603643 |

> When fixing override on this screen, verify **all three override qtys (Alloc / PTR / Schedule) at all applicable levels (2, 5, 101)** — the client explicitly called this out (25-01050075).

---

## 11. Fuel / L&U / Vaporization in Allocation

Fuel/loss is applied during allocation; LNG locations derive measurement from child locations via a fuel-based formula.

| Issue | Root cause | Fix | Case |
|-------|-----------|-----|------|
| **LNG measurement allocating too high** (14079) | A fuel-rate time-slice was wrong; the calc uses fuel qty: `14079 = LNGINLET − (LNGBOILOFF + LNGFUEL + LNGVAPOR)` | **Remove the bad fuel-rate time-slice, re-enter child-loc quantities, re-run allocation** | 25-01052886 |
| Recalc-Fuel-no-location wiped a month of allocations | Param guard missing (see §4) | Code fix | 25-01010799 |
| Vaporization fuel not calculating properly | Fuel/vapor config | Config | 24-00947410 |
| Heat factor error (Bantry ND08) | Heat-factor ref data | Config/data | 24-00967433 |
| Fuel rounding inconsistent TSP401→801 AutoGen (cross-link to Nominations §7) | TSP fuel-rounding config | Config | 25-01044076 |

> **Resolution pattern for LNG/fuel allocation drift (25-01052886, verbatim):** *"Removing fuel rate for [the bad day] time slice, re-entering all child loc quantities and re-running allocations resolved this issue. For future ref, this process calculates based on fuel qty so that needs to be checked."* Always check the fuel-rate time-slices first when LNG/derived measurement looks off.

---

## 12. Allocation Reports (ALR / INX / IN41)

Report-layer issues (registered SQL / Crystal / rounding / null handling). Lower urgency but high volume.

| Report | Issue | Root cause | Fix | Case |
|--------|-------|-----------|-----|------|
| **ALR_26** Unallocated Volumes | Full of 0-qty rows → useless | Rounding not held to TSP UOM; filter | Code fix | 22-00570045, 22-00693361 |
| **ALR_24 / ALR24M** (Daily/Monthly PPA) | "No Data Found" on summary line when allocated PTR is null (pre-Evolution days) | Crystal can't resolve imbalance qty when PTR null | Code fix (patch) | 24-00974206 |
| **ALR_69** Volume Adjustment | PPA volumes missing on retro pool switch | Mid-to-pool relationship change defect | Release upgrade | 22-00826683 |
| **INX02 / IN41** | Imbalance duplicated | Registered-SQL dedup | Config/code | 24-00964240, 22-00609015 |
| **RPT_OBA_VW** | DB object issues | View defect | Code | (DB object case) |
| Service Requester Statement of Gas Allocation | Adjustment report not tying to revision total | Allocation not re-run / report | Workaround | 22-00597398 |

> Most report cases are **config or registered-SQL** — confirm whether the underlying allocation DATA is correct first (often it is; the report just mis-renders/duplicates). 24-00964240 explicitly: "imbalance looks correct in the system" but INX02 duplicated it.

---

## 13. Expected Behavior / User Education

~285 Allocations cases are **Customer Error / Training** — recognize these to avoid needless scripts/escalations.

| Reported as | Reality | Case |
|-------------|---------|------|
| "ALALLOCATE failing — masterlinks error" | Often user params / setup; verify before escalating | 26-01100678 |
| "Allocation Process is RED / getting errors" | Triage params & data first; frequently config/data | 25-01009195, 25-01004158 (data script) |
| "PPA measurement not allocating in UAT" — ran ALALLOCATE many ways | **Customer Error** — usually wrong acctg/prod-month combo or measurement not at the right meter level | 25-01000102 |
| "Child meter not rolling up to parent" / "$2M PPA on invoice" | Measurement entered at wrong child / measurement-entry error | 25-01003722, 25-01033249 |
| "ALR24M shows PPA fuel qty when no fuel-rate/alloc change" | Working as designed (fuel revision flagged as PPA) | 25-01033013 |
| "Nom/Sched volume allocating with zero physical flow" | Nominated qty flows to inventory by design when no measurement | 25-01019127 |
| "Need to load data into a closed month" | Process/training — reopen or PPA path | 25-01001809, 26-01080168 |
| "Allocation Error on upstream pool — validation still triggers after fixing overlap" | Customer-induced: loc **name changed during an overlapping eff-date** in Classic; advise **always use Web** | 24-00985346 |
| "Could not run IN40 / want SQL for audit" | Provide documentation, not a fix | 25-01049399, 25-01057184 |
| Auditor / SOC1 / UBL / training / reassignment requests | Not technical defects | 25-01057184, 24-00991974, 25-01019196 |

**Tell-tale it's user/expected:** measurement entered at the wrong meter/level; wrong acctg-vs-prod month; a closed month; a location whose **name/eff-date was edited in Classic** (Classic doesn't resolve loc-name-on-overlap — use Web); or the "error" is allocation correctly following nominated qty with no physical flow.

> **EQT note:** cases 24-00995627/628/629 ("PDA Error Review with Quorum") were **Declined by Quorum** — they were meeting invites with no actionable content. Don't mistake calendar-invite cases for defects.

---

## 14. Key Code Files, Processes & Repos

### Batch processes (Quorum.QPTM.Batch / ENGS C++ batch — e024d80b-5c45-411c-93e1-78e2798ed885)
| Process | Purpose |
|---------|---------|
| **ALALLOCATE** | Core allocation process (Web "Allocation Process"). C++ batch (`QPDLLPIPELINEMGRAL_EQC` DLL). Steps incl. `ALALLOC_N`, `FlipNegativeNodes`. |
| **PANIGHTLY / PADAILY** | Nightly/daily allocation runs (PA = Pipeline Allocation). Accounting-offset resolution lives here. |
| **ALSCHDOVRD** | Allocate-by-schedule-override (LNG, "Allocate Entire Month End"). |
| **GSWHALLOC / GSWHALLAPP** | Shared Wellhead allocation / approval (WGT meters). |
| **ALPTRSYNC** | Sync PTR plant values from TIPS (Evolution) into QPTM allocation overlay. |
| **CUSTACCTACCUM** | Customer Account Accumulation (inventory roll-up). |
| **ALESVOLIMP** | Volume import feeding allocation (parent-meter volume warnings). |
| **ALLDEFNOM** | Allocate default nom (Classic). |
| **NNCALCFUEL** | Fuel recalc (can create overlapping noms — see Nominations §7). |

> Allocation output writer: `QSQLID_AllocateOutput::m_Output_InsTranForRestatementDay` (the insert that throws `AK_ALCTRL_ALLOC2` on duplicates). Engine class `QPSAlloc` (`FlipNegativeNodes`, `QNomHashMgr` for the nom-hash join — perf bottleneck per ADO #1621519).

### Web screens (Quorum.QPTM.Web — 41e317c0-844c-4728-98da-529092957738)
| Screen / controller | Purpose |
|---------------------|---------|
| **PDA Submission** | Predetermined allocation entry; Web Nom_ID/Nom_HashID assignment defects (23-00899058), eff-date/overlap defects. |
| **Daily Allocated Quantity Maintenance** | Manual override of alloc/PTR/schedule qty at levels 2/5/101 (25-01050075). |
| **Authorization to Post Imbalance** | Post/authorize imbalance; Web picklist/code-table & access defects (24-00964617, 25-01013422). |
| **Measurement Entry (Bulk Edit)** | Decimal-formatting must follow TSP config (24-00939019). |

### Override repos
`<CLIENT>.QPTM.Web` / `.Database` / `.Metadata` (e.g. **ENT** Permian/STX PTR & fuel-split, **MGD/MID** LNG, **APL**, **XCL**, **TGNR**, **EQC/Evolution**). **Always check for a client override** before assuming base allocation behavior.

---

## 15. Database Tables Reference

| Table | Purpose |
|-------|---------|
| **`ALCTRL_ALLOC`** | **Allocated quantities (primary output). Unique key `AK_ALCTRL_ALLOC2` — the duplicate-key collision target.** Keyed by TSP_NO, LOC_ID, ALLOC_GAS_DAY, ACCTG_MTH, TRANS_TYPE_ID, SR_CTR_NO. |
| **`ALCTRL_ALLOC_OVRD`** | Allocation override quantities (Daily Allocated Quantity Maintenance writes here). |
| `ESUITE_QENT.QTIP_TRAN_PLANT_PTR` | TIPS PTR plant values synced into QPTM (Evolution) — source for PTR overlay. |
| `ESUITE_QENT.BLTRAN_STAG_IMB_OVRLY` | Staging imbalance overlay (unique-constraint defect 24-00984737). |
| `PATRAN_LOC_GRP_LOC_GRP_RANGE`, `PACTRL_LOC_GRP_OTHER`, `PAHIST_SYS_LOC_GRP_LOC` | **Allocation-plan / location-group ref data — required for swing/allocation-plan setup (26-01083452).** |
| `ALCTRL_PDA` (PDA submission backing) | Predetermined allocation rows (method, %, rank, TT, eff dates, Nom_HashID). |
| `JBONL_ALLOC_GRP_DETAIL` | Allocation-group detail (AG_CODE/TO_PROP_NO) — dedupe + allocation-basis fix target (ADO #1748514). |
| `QXREF_PROCESS_SYNCGRP` | Process sync-group xref (ALLOCATE app-layer routing — EQC FULLSYNC, ADO #1762619). |
| `QARCH_QFCBATCH_SQL_TRACE` | **Batch SQL trace by PROCESS_QUEUE_ID — read this to find the exact failing insert.** |
| `QARCH_TSP_CONFIG` | TSP config incl. `TIPS_PROCESS_CONTROLS_PRM` (WGT-reallocation gate). |
| `NNCTRL_NOM_DTL` / `NNCTRL_NOM_HDR` | Noms feeding allocation (bad header data → FlipNegativeNodes). |
| `NNCTRL_LOC` | Locations — check `EFF_DT_TO` vs gas day (stalls CUSTACCTACCUM, breaks allocation). |
| Code table **27205** (TOS) | TOS setup required for Customer Account update (24-00966286). |
| `RPT_OBA_VW`, ALR/INX/IN41 registered-SQL views | Report backing objects. |

> Column-name caveat: `ALCTRL_ALLOC` field names (`ALLOC_GAS_DAY`, `ACCTG_MTH`, `TRANS_TYPE_ID`, `LOC_ID`, `SR_CTR_NO`) are confirmed from case repro SQL (24-00994255, 22-00524917). Some allocation-plan/PDA exact column names are inferred — verify against the schema before scripting.

---

## 16. Diagnostic SQL Queries

### A. Allocation results for a location / gas day / acctg month
```sql
SELECT TSP_NO, LOC_ID, ALLOC_GAS_DAY, ACCTG_MTH, TRANS_TYPE_ID, SR_CTR_NO,
       ALLOC_QTY, FUEL_QTY, SCHD_QTY, USER_ID, UPDT_DT
FROM   ALCTRL_ALLOC
WHERE  TSP_NO = <TSP_NO> AND LOC_ID = '<LOC>'
  AND  ALLOC_GAS_DAY = '<GAS_DAY>' AND ACCTG_MTH = '<ACCTG_MTH>'
ORDER BY TRANS_TYPE_ID, SR_CTR_NO;
```

### B. Duplicate allocation rows (AK_ALCTRL_ALLOC2 collision)
```sql
SELECT TSP_NO, LOC_ID, ALLOC_GAS_DAY, ACCTG_MTH, TRANS_TYPE_ID, SR_CTR_NO, COUNT(*) dup_ct
FROM   ALCTRL_ALLOC
WHERE  TSP_NO = <TSP_NO> AND ACCTG_MTH = '<ACCTG_MTH>'
GROUP BY TSP_NO, LOC_ID, ALLOC_GAS_DAY, ACCTG_MTH, TRANS_TYPE_ID, SR_CTR_NO
HAVING COUNT(*) > 1;
```

### C. Failing-run SQL trace (find the exact insert that errored)
```sql
SELECT SEQ_NO, SQL_TEXT, ERROR_MSG
FROM   QARCH_QFCBATCH_SQL_TRACE
WHERE  PROCESS_QUEUE_ID = <PQID>
ORDER BY SEQ_NO;
```

### D. Override rows for the Daily Allocated Quantity Maintenance issue
```sql
SELECT TSP_NO, LOC_ID, ALLOC_GAS_DAY, ALLOC_LEVEL, TRANS_TYPE_ID,
       OVRD_ALLOC_QTY, OVRD_PTR_QTY, OVRD_SCHD_QTY, OVRD_REASON_CD, USER_ID, UPDT_DT
FROM   ALCTRL_ALLOC_OVRD
WHERE  TSP_NO = <TSP_NO> AND LOC_ID = '<LOC>' AND ALLOC_GAS_DAY = '<GAS_DAY>'
ORDER BY ALLOC_LEVEL, TRANS_TYPE_ID;
```

### E. Location active for the gas day (allocation/CUSTACCTACCUM stall)
```sql
SELECT ID_LOC, LOC_NM, IS_ACTIVE, EFF_DT_FROM, EFF_DT_TO
FROM   NNCTRL_LOC WHERE TSP_NO = <TSP_NO> AND ID_LOC = '<LOC>';
-- Watch for EFF_DT_TO earlier than the latest nom/gas day (24-00964259).
```

### F. WGT / Wellhead approval + gating config
```sql
SELECT TSP_NO, CONFIG_KEY, CONFIG_VALUE FROM QARCH_TSP_CONFIG
WHERE  TSP_NO = <TSP_NO> AND CONFIG_KEY = 'TIPS_PROCESS_CONTROLS_PRM';
```

### G. Allocation-plan ref data (swing setup — "loc not tied to an allocation plan")
```sql
SELECT * FROM PATRAN_LOC_GRP_LOC_GRP_RANGE WHERE TSP_NO = <TSP_NO> AND LOC_ID = '<LOC>';
SELECT * FROM PACTRL_LOC_GRP_OTHER         WHERE TSP_NO = <TSP_NO>;
SELECT * FROM PAHIST_SYS_LOC_GRP_LOC       WHERE TSP_NO = <TSP_NO> AND LOC_ID = '<LOC>';
-- Missing rows here = the 26-01083452 "not tied to an allocation plan" warning.
```

---

## 17. Standardized Fix-Scripts (VERBATIM, redacted)

The actual fix SQL lives in **ADO Script Review / Script Deployment work-item attachments**, not in SF. Below are real attachment texts, redacted to `<PLACEHOLDER>` for concrete IDs/dates/server but with **real table/column names and logic intact**. Always run a **verify-SELECT** and eyeball the row count before deleting/updating; wrap destructive steps in a transaction.

#### Template A — Remove duplicate allocation rows + reset allocation basis
> Source (verbatim): ADO **#1748514** *"TGNR PRD-Upstream Script to Remove Duplicate Allocations & Update Allocation Basis"* (attachment `Step 1 Remove duplicates Step 2 Update Alloc Basis.txt`). Targets the allocation-group detail table; dedupe keeps one row per `AG_CODE` + `TO_PROP_NO`, then forces allocation basis. **Add a WHERE scope (TSP/acctg-month/group) before running in PRD — the verbatim script is unscoped.**

```sql
-- Step 1: Remove duplicates (keep one row per AG_CODE + TO_PROP_NO)
WITH CTE AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY AG_CODE, TO_PROP_NO ORDER BY (SELECT NULL)) AS rn
    FROM JBONL_ALLOC_GRP_DETAIL
    -- AND <scope: AG_CODE IN (...) / TSP / acctg month>   <-- ADD before PRD run
)
DELETE FROM CTE WHERE rn > 1;

-- Step 2: Update allocation basis
UPDATE JBONL_ALLOC_GRP_DETAIL
SET    ALLOCATION_BASIS = 1
-- WHERE <same scope as above>                            <-- ADD before PRD run
;
```

#### Template B — Register / sync the ALLOCATE process sync-group (Evolution/EQC)
> Source (verbatim): ADO **#1762619** *"EQC - Script review FULLSYNC ALLOCATE"* (attachment `01_ALLOC_SYNC_DEF.sql`). Idempotent insert/update of `QXREF_PROCESS_SYNCGRP` so the ALLOCATE family of processes routes to the right app layer (`QEQC`) in an Evolution/TIPS-integrated env. Repeat the block per `PROCESS_ID` (`ALLOCATE1`, `ALLOCATE_2`, `ALLOCTEWH1`, `ALLOCWH_2`, ...).

```sql
-- Idempotent upsert of a process→sync-group route (one block per PROCESS_ID)
IF NOT EXISTS (SELECT 1 FROM dbo.QXREF_PROCESS_SYNCGRP
               WHERE PROCESS_ID = '<PROCESS_ID>' AND SYNCGRP_CD = 'ALLOCATE_TIPS')
    INSERT INTO dbo.QXREF_PROCESS_SYNCGRP (PROCESS_ID, SYNCGRP_CD, APP_LAYER_CD, USER_ID, UPDT_DT)
    VALUES ('<PROCESS_ID>', 'ALLOCATE_TIPS', 'QEQC', '<USER_ID>', GETDATE());
ELSE
    UPDATE dbo.QXREF_PROCESS_SYNCGRP
    SET    APP_LAYER_CD = 'QEQC', USER_ID = '<USER_ID>', UPDT_DT = GETDATE()
    WHERE  PROCESS_ID = '<PROCESS_ID>' AND SYNCGRP_CD = 'ALLOCATE_TIPS';
```

#### Recovery recipe — ALALLOCATE duplicate-key / bad-nom-data clean-up
> Pattern (from SF resolutions 25-00998023 "Data clean-up script to clean bad nom data", 22-00524917 PANIGHTLY `AK_ALCTRL_ALLOC2`). No single verbatim attachment was binary-free; the repeatable steps are:
1. Run diagnostic **B** (dup alloc rows) and **C** (SQL trace by PQID) to identify the colliding key + the failing insert.
2. If the duplicate is a **stale alloc row** from a prior run → delete the duplicate `ALCTRL_ALLOC` row for that TSP/LOC/gas-day/acctg-mth/TT/contract, then re-run ALALLOCATE scoped to that month.
3. If the root is **bad nom data** (header/detail mismatch, dup Account Managers per 23-00903346) → clean the nom side first (see Nominations skill §4), then re-allocate.
4. Always scope to the **specific location/gas-day**, not the whole month, and wrap in `BEGIN TRAN ... COMMIT` with a verify-SELECT.

> **Provenance:** verbatim text from ADO attachments **#1748514** and **#1762619**. Other allocation script-deployment WIs confirmed (titles/binary zip only): #1737300/#1733854 (TGNR push volumes to QCA, `INSERT INTO PONL_WELL_COMPL_THEO_RU`), #1748395 (CCI dup-alloc). On-prem/older clients receive these as **PDMs** rather than self-service scripts.

---

## 18. Known Historical ADO Bugs

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|-------|--------------|-----------------|---------|---------|
| **#1670362** | Requirement / **Closed** | GBG 2024.04 Critical Out-of-Cycle — LNG ALSCHDOVRD pro-rate & override fixes | §5/§11 | 24-00962061, 24-00962851 |
| **#1652157** | Bug / **Closed** | ALALLOCATE — `FlipNegativeNodes()` error ("Error setting value for column ... NNCTRL_NOM_HDR") | §4 | — |
| **#1706632** | Bug / **Closed** | ALALLOCATE — "Error in Registered SQL" (tsp 24/8925, 9/30) | §4/§12 | 25-00996952 |
| **#1705988** | Internal Activity / **Closed** | ALALLOCATE — "Dll Not Found QPDLLPIPELINEMGRAL_EQC" | §4 | 24-00994160 |
| **#1796121** | Bug / **Closed** | ENT — Index time-slice creates header/detail mismatch → ALALLOCATE failure | §4/§7 | — |
| **#1734843** | Bug / **Closed** | XCL — ALALLOCATE erroring when Reallocation Indicator selected | §4 | — |
| **#1681051** | Bug / **Closed** | ENT — ALALLOCATE erroring when executed (TSP 30051, Apr 2024) | §4/§6 | — |
| **#1621519** | Bug / **Closed** | ALALLOCATE — performance due to `QNomHashMgr` query | §4 (perf) | — |
| **#1654964** | Bug / **Closed** | CMX — ALALLOCATE takes >20 min | §4 (perf) | — |
| **#1613593 / #1617125** | Requirement / **Closed** | ENT Permian & STX PTR Enhancements — Fuel Split / PTR Overlay (ALALLOCATE C++ batch) | §7 | — |
| **#1770221 / #1778656** | Requirement+Task / **Closed** | ENT — PDA by Processing Contract (ALALLOCATE dev) | §5 | 25-01018678 |
| **#1777938** | Database Change / **Closed** | Insert PTR column in `BLXREF_REALLOC_PPA` codetable for ALALLOCATE | §7 | — |
| **#1742027** | Bug / **Closed** | ETC — PDA Submission poor performance in Web (limiting Calc Schd Qty records) | §5 | 24-00983745 |
| **#1719402** | Bug / **Closed** | 2025.04 — Auth-to-Post-Imbalance / PDA Submission new-TSP name not displaying | §5/§8 | — |
| **#1748514** | Script Deployment / **Closed** | TGNR — Remove Duplicate Allocations & Update Allocation Basis (script attached) | §4/§17 | — |
| **#1762619** | Script Review / **Closed** | EQC — FULLSYNC ALLOCATE process sync-group (script attached) | §17 | — |

> **Takeaway:** ALALLOCATE failures split into (a) **bad-data/duplicate-key** cases → dispositioned operationally with a data clean-up script (no single product fix), and (b) genuine **code bugs** (FlipNegativeNodes, Registered SQL, reallocation-indicator, index time-slice mismatch, perf). PDA/allocation-method cases are predominantly **Application Configuration** (NAESB rank/TT/tiering) or **Web-vs-Classic** screen defects. The biggest data-loss risk is **Recalc-Fuel-with-no-location** (25-01010799) — flag it proactively.

---

## 19. Escalation Decision Tree

```
Allocations case reported
│
├─ A batch process failed (ALALLOCATE / PANIGHTLY / PADAILY / GSWHALLOC)?  (§4, §6)
│   ├─ Get PQID + TSP + acctg month + exact error
│   ├─ "AK_ALCTRL_ALLOC2 / unique constraint" → §16-B dup check + §16-C trace
│   │     ├─ Stale dup alloc row → data clean-up script, re-run scoped  (25-00998023, 22-00524917)
│   │     └─ Bad nom data (dup Acct Mgr, header mismatch) → fix nom side first  (23-00903346, #1652157)
│   ├─ "Registered SQL" / "Dll Not Found" / Reallocate-Ind / index-mismatch → CODE bug, match §18
│   ├─ "Child qty exceeds parent" → measurement decimals/child>parent → fix measurement  (24-00939019)
│   └─ WGT meter + "completes with warning"/won't reallocate → check WH approval + TIPS_PROCESS_CONTROLS_PRM  (§6)
│
├─ PDA Submission issue?  (§5)
│   ├─ Web behaves ≠ Classic (ignored by alloc / overlap / blank method / TT6 up-party) → CODE bug (reproduce both)
│   └─ Wrong method (pro-rata vs rank), TT defaults, tiering → CONFIG / NAESB  (24-00951976, 24-00949200)
│   └─ "Not tied to an allocation plan" (swing) → DATA script (alloc-plan loc-group tables §17/§16-G)
│
├─ PTR overlay / PPA not applying (Evolution/TIPS client)?  (§7)
│   └─ Check ALPTRSYNC + QTIP_TRAN_PLANT_PTR vs ALCTRL_ALLOC_OVRD; KW/partial-month/precedence = code bugs
│
├─ OBA / Imbalance?  (§8)
│   ├─ Won't allocate to OBA contract → code bug  (22-00643981)
│   ├─ Imbalance duplicated on INX02/IN41 → report/registered-SQL  (24-00964240)
│   └─ Can't run/Web picklists missing → access (Imbal Trade) / Web patch  (25-01013422, 24-00964617)
│
├─ Customer Account / Inventory not updating?  (§9)
│   └─ Missing TOS code-table (27205) / loc end-dated while noms exist / job timeout  → CONFIG  (24-00966286, 24-00964259)
│
├─ Can't override allocated qty (level 2/5/101, Web)?  (§10)  → patches 70/71 (25-01050075)
│
├─ Fuel / LNG / vaporization wrong?  (§11)
│   └─ Remove bad fuel-rate time-slice, re-enter child loc qty, re-run alloc  (25-01052886)
│   └─ NEVER Recalc-Fuel with no location (data-loss)  (25-01010799)
│
├─ Report (ALR/INX/IN41) shows 0 / dup / "No Data"?  (§12)
│   └─ Confirm underlying alloc DATA is correct first; usually registered-SQL/rounding/null-PTR
│
└─ "Allocation is RED / errors" with vague detail, audit/UBL/training request?  (§13)
    └─ Likely Customer Error / Training — verify params, acctg-vs-prod month, measurement level before escalating
```

---

*Skill created: 2026-06-01*
*Based on: ~286 actionable QPTM Allocations SF cases (Software Defect + Application Configuration) + ~285 Customer Error/Training cases + ADO work items #1670362, #1652157, #1706632, #1705988, #1796121, #1734843, #1681051, #1621519, #1654964, #1613593, #1617125, #1770221, #1778656, #1777938, #1742027, #1719402, #1748514 (script), #1762619 (script).*
*Companion: SKILL_Nominations.md, SKILL_EDI_Troubleshooting.md. Applicable to all QPTM TSPs/clients (incl. Evolution/TIPS-integrated allocation).*
