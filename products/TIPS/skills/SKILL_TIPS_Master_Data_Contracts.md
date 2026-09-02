# SKILL: TIPS Master Data & Contracts Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-11 | **Product:** My Quorum TIPS (oil/gas transaction & accounting)
**Use When:** Any TIPS case involving master-data or contract setup — Contract Maintenance / CCT (Common Contract Terms), Contract Meter List (CML), Meter Definition / Meter Split, Company / Organization Maintenance, BA setup, Rate Schedules / Escalation — **including downstream symptoms**: allocation zeroes, settlement/paystation failures, imbalance duplicates, PPA un-approve errors, facility-batch-job (Measure→Settle / plant close) errors. In TIPS, master-data defects almost always *surface* as allocation/imbalance/settlement failures, so start here whenever the trail leads back to a contract, meter, or facility setup object.
**Companion:** SKILL_Allocations.md (QPTM allocation engine — different product, shared Evolution clients), SKILL_Salesforce_Queries.md.

> Evidence base: 397 closed TIPS cases in the Master Data/Contracts category group; 70 actionable cases retrieved with Root Cause = Software Defect / Application Configuration / ChangeConfig, plus a 30-case Training/Customer Error sample. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining (June 2026).

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Decision Tree](#2-decision-tree)
3. [Contract Time-Slice / Effective-Date Overlaps (SEXTN_CTR_HEADER, QCM sync)](#3-contract-time-slice--effective-date-overlaps)
4. [Meter Split / Contract-Meter Linkage (WIO%, Split Decimal, PDA ties)](#4-meter-split--contract-meter-linkage)
5. [QTRAN_IMBAL_ACCT_BAL Duplicates & Imbalance Sequence Overflow](#5-qtran_imbal_acct_bal-duplicates--sequence-overflow)
6. [Gas Lift Duplication (ASSCGLM Process Step)](#6-gas-lift-duplication-asscglm)
7. [QTRAN_PAYSTATION Build Failures & Duplicates](#7-qtran_paystation-build-failures--duplicates)
8. [Facility Definition / Allocation Group Configuration](#8-facility-definition--allocation-group-configuration)
9. [PPA Framework Failures (Un-Approve, PSWHALLOC, Reinstated PTR)](#9-ppa-framework-failures)
10. [Imbalance Posting / Customer Account Balance Config](#10-imbalance-posting--customer-account-balance-config)
11. [Facility Batch Job / Plant Close-Settle Errors](#11-facility-batch-job--plant-close-settle-errors)
12. [TIPS ↔ QPTM Evolution Sync Issues](#12-tips--qptm-evolution-sync-issues)
13. [Web-vs-Classic Screen Defects](#13-web-vs-classic-screen-defects)
14. [Report / View Calculation Errors](#14-report--view-calculation-errors)
15. [Known ADO Items](#15-known-ado-items)
16. [Diagnostic SQL](#16-diagnostic-sql)
17. [Expected-Behavior / User-Education FAQ](#17-expected-behavior--user-education-faq)
18. [Escalation Guidance](#18-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom | Likely cause | First check |
|---|---|---|
| Contract suddenly not allocating for a month; new contract also not picking up | Contract end-date / time-slice gap tied to MTR SFX CD (QCM-managed contract) | `SEXTN_CTR_HEADER` time slices for the CTR_NO; QCM contract end date (26-01100512) |
| PPA / facility batch job fails "duplicates inserting into pay station" | Overlapping effective-date time slice on the contract header | `SELECT * FROM QRMTIPS.SEXTN_CTR_HEADER_QRMTIPS WHERE CTR_NO='<X>' ORDER BY EFF_DT_FROM DESC` (25-01002372) |
| One owner's volume shows zero on query screen; WIO% has many decimals | Missing CAST → NUMERIC(14,10) rounding defect in query (fixed) | Meter split WIO% decimal places (25-01002874) |
| Noms/volumes go to 0 at allocation for a contract | Meter split % for that contract = 0 | Meter Split screen for the meter/contract (25-01056537) |
| Split decimal not calculated when allocated WHAV slightly > physical WHDV | Progressive-rounding bound check rejects pcr_contr > 1.00000 | Global config: allocation rounding check / `PROGRESSIVE_ROUNDER_NO_BOUND_CHECK` (26-01068082, 24-00985175) |
| Can't end-date a meter — "PDA has not been end dated" though it has | Orphan/second PDA submission record on the meter | PDA submission records for the meter; delete the orphan (24-00984071) |
| Imbalance/customer-account-balance figures doubled | Duplicate rows in `QTRAN_IMBAL_ACCT_BAL` (recurring Hilcorp defect) | Dup-check SQL §16-B; code fix in 2025.04 patch (≥2025.04.1.4) (25-01061774, 26-01068169) |
| "sequence too large for column" on imbalance activity | `QTRAN_IMBAL_ACCT_ACTIVITY_D_SQ` exceeded NUMBER(10) column | Widen `ACCT_ACTIVITY_DTL_ID` precision (25-01014345) |
| Gas lift volumes doubled after plant re-run | ASSCGLM step re-inserts without purging when plant in reallocation mode | `QTRAN_ALLOC_VOL` rows with `PROCESS_ID='ASSCGLM'`; ADO #1731166 (25-01023169) |
| Batch fails "ERROR SETTING VALUE FOR COLUMN EFF_PCT_CONTR" | S_Decimal column too small when meas vol tiny vs nom huge | `QTRAN_PAYSTATION` S_DECIMAL precision NUMBER(14,10)→(16,10) (24-00994961) |
| Allocated NGL product volumes wrong (e.g. Natural Gasoline) | Facility Definition component list / allocation-group recalc basis | Facility Definition components (IC5/NC5 vs C5+); allocation group basis (25-01011404, 25-01027694) |
| Can't un-approve PPAs — concatenate error, holding up close | COMMENTS column varchar2(4000) overflow on un-approve SQL | Script to clear comments; long-term SQL fix (24-00990256, 24-00991302) |
| Evolution prod-month PPA re-run fails unique constraint QPTMSTAGPERMWHALLOC | Staging table re-insert defect on plant re-run (MEASUREGTT→ARAP_IFGTT) | ADO/engineering — code defect (24-00976492) |
| Imbalances vanished from customer account balance after close | POSTRESULT ran prematurely — missing process dependency | Process dependency config; reprocess PA as PPA (25-01021133) |
| Settle process fails, "meter split issue" in log | Missing price index (e.g. GDP) on the contract/rate setup | Index setup; add the index, re-run settle (24-00970370) |
| Production-month volume entry errors in Web only; Classic fine | Web-only screen defect, fix version not yet on PRD | Compare env build vs fix version; workaround in Classic (26-01091817) |
| Daily Imbalances report missing days of receipt data | Facilities left in reallocation mode → batch zeroes/skips those days | Reallocation checkbox on facility lock screen (24-00968763) |

---

## 2. Decision Tree

```
TIPS Master-Data/Contracts case reported
│
├─ Does the failure trace to a CONTRACT object (CTR header, CCT, CML)?
│   ├─ Allocation/settlement skips a contract month → §3 contract end-date / time-slice gap (26-01100512)
│   ├─ Paystation "duplicate insert" / eff-date overlap error → §3 SEXTN_CTR_HEADER overlap → data script
│   ├─ Can't add/edit CCT, picklist blank, seq_no error → §17 FAQ (usually user/caching) or §13 Web defect
│   └─ CML eff-date validation wrong after changing contract dates → ADO #1788087 / #1801070 (§15)
│
├─ Does it trace to a METER object (Meter Definition, Meter Split, PDA tie)?
│   ├─ Volumes zero for one owner/contract → §4 (split %=0, WIO% rounding, missing CCT on split)
│   ├─ Can't end-date/delete meter → §4 orphan PDA / contract-meter records (24-00984071, 26-01087430)
│   └─ Split decimal not updating after batch → ADO #1795476 (Proposed) (§15)
│
├─ Imbalance numbers doubled or sequence errors? → §5 (QTRAN_IMBAL_ACCT_BAL dups → dedupe script + patch)
├─ Gas lift doubled? → §6 ASSCGLM (#1731166)
├─ Batch/settle column-value or paystation errors? → §7 (EFF_PCT_CONTR precision, m_INS_STMT dups)
├─ Product/NGL allocation wrong? → §8 Facility Definition / Allocation Group config
├─ PPA un-approve / Evolution PPA re-run fails? → §9
├─ Imbalances missing/not posting after close? → §10 (POSTRESULT dependency, CICO, realloc mode)
├─ Plant close / facility batch job errors? → §11 (missing index, run-every-facility rule)
├─ TIPS↔QPTM data not flowing (Evolution client)? → §12
├─ Web behaves ≠ Classic? → §13 (check build vs fix version FIRST)
└─ Report wrong but underlying data right? → §14
```

---

## 3. Contract Time-Slice / Effective-Date Overlaps

**Symptom:** A contract stops allocating for a month (and a replacement contract doesn't pick up either); or a facility batch job / PPA fails with a *duplicates inserting into pay station* error citing an effective-date overlap.

**Root cause:** Contract header time slices in `SEXTN_CTR_HEADER` (client schemas: `QRMTIPS.SEXTN_CTR_HEADER_QRMTIPS`) either **gap** (contract end date wrong, so no slice covers the month) or **overlap** (two slices cover the same date range). For QCM-managed clients the contract end date is maintained in **QCM** tied to the **MTR SFX CD**, and TIPS reads the synced slices.

**Resolution recipe:**
1. Pull the slices: `SELECT * FROM QRMTIPS.SEXTN_CTR_HEADER_QRMTIPS WHERE CTR_NO = '<CTR>' ORDER BY EFF_DT_FROM DESC;` — look for overlap or gap around the failing accounting/production month (this exact query resolved 25-01002372, CTR PAM043600A, overlapping 10/1/2024–10/31/2024 slice; fixed with a script).
2. **Gap case (26-01100512):** fix the contract end date in **QCM** (end date tied to MTR SFX CD, e.g. 4/1/2021–3/31/2026), then in TIPS create the delivery nom to the meter for the new slice (4/1/2026–12/31/9000), re-run to month-end.
3. **Overlap case:** Cloud Ops data script to correct/merge the overlapping slice, then re-run the facility batch job / PPA.
4. QCM Contract Meter List screen can throw a **false "invalid effective date"** after changing the contract effective date even when meters are correctly time-sliced — that is ADO **#1788087** (Closed, UPC 26-01084783), a code defect, not bad data.
5. Contract Extension Agent deleting things it shouldn't = code defect, fixed (25-01003394, "code change was made").

**Representative cases:** 26-01100512 (Inter Pipeline), 25-01002372 (IACX), 25-01003394 (ONEOK), 25-01011855 (Howard — UAT time slices corrected in PRD move).

**Code refs:** `SEM.TIPS.Database /CLIENT/Oracle/Procs/QPSEM_MTR_SPLIT_CTR_SYNCH.sql` (+ matching view) is a real client meter-split↔contract sync object touching `SEXTN_CTR_HEADER` — check for client overrides before scripting.

---

## 4. Meter Split / Contract-Meter Linkage

**Symptom:** One owner/contract shows zero volume on the query screen or in imbalance; settlement statement zeros for one meter; can't end-date or delete a meter.

**Root causes & recipes (all real):**
| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Owner volume zero when WIO% has 7 decimals (0.9421875 / 0.0578125) | Query missing data-type cast → rounding dropped a row | Code fix: `CAST(... AS NUMERIC(14,10))` to match S_DECIMAL column | 25-01002874 (Pembina) |
| Noms for a contract not coming over in imbalance | **Meter split % for the contract = 0** → volumes zero out at allocation | Fix the split %, or use Imbalance Volumes for the requirement | 25-01056537 (Howard) |
| Gathering allocation skips s_decimal when allocated WHAV slightly > physical WHDV | Progressive-rounding bound check fails pcr_contr just over 1.00000 | Update allocation rounding check in **global config**; cf. `PROGRESSIVE_ROUNDER_NO_BOUND_CHECK = 1` | 26-01068082 (M6), 24-00985175 (ETP) |
| Can't end-date meter — "PDA has not been end dated" (it was) | Second/orphan PDA submission record on the meter | Delete the orphan PDA record | 24-00984071 (Merit) |
| Can't add child meters on Contract Meter List | Stale contract-meter records → duplicate-key conflict | Identify & remove the existing conflicting CML records | 26-01087430 (Customer Error but same recipe) |
| L&U allocates but fuel/report zeros a meter | Report only accepts FLOW_DIR='D' (delivery) meters; meter not tied to contract in PDA submission + Meter Split | Tie the delivery meter to the contract on both screens | 24-00970501 (Merit) |
| RMS meter with 3 contracts allocating incorrectly | Config (resolved directly with customer; pattern unclear from mined case) | — | 25-00997798 |

**Key insight:** a **Split Decimal of zero at the Meter Split level flows into Paystation data** and zeroes downstream settlement (26-01091612) — always check the split before suspecting the settlement engine.

---

## 5. QTRAN_IMBAL_ACCT_BAL Duplicates & Sequence Overflow

**Symptom:** Imbalance volumes / customer account balances doubled; recurring monthly at Hilcorp (HEC). Or: error *"number's precision too large"* on imbalance activity.

**Root cause (duplicates):** A code defect creates duplicate rows in `QTRAN_IMBAL_ACCT_BAL`. Confirmed recurring — Cloud Ops ran dedupe scripts repeatedly for Hilcorp: ADO **#1772687** (PRD 12/2025, SF 25-01060242), **#1776627/#1776858/#1776936** (UAT+PRD 1/2026, SF 26-01065143), **#1778736/#1778789** (UAT+PRD 1/2026, SF 26-01068169). The **code fix ships in the 2025.04 stream** — "Hilcorp's next upcoming patch #3 2025.04 will contain the code fix" (25-01061774).

**Resolution recipe:**
1. Confirm dups with §16-B.
2. Short-term: Cloud Ops dedupe script (pattern of #1772687/#1778789 — delete duplicates from `QTRAN_IMBAL_ACCT_BAL`, scoped to the affected accounting month).
3. Long-term: confirm client build ≥ the 2025.04 patch containing the fix; if PRD is behind (e.g. 2025.04.1.3 vs fix in 2025.04.1.4 — 26-01091817 pattern) schedule the patch.

**Root cause (sequence overflow, 25-01014345 ETP):** sequence `QTRAN_IMBAL_ACCT_ACTIVITY_D_SQ` passed 10,000,000,000 — too large for `ACCT_ACTIVITY_DTL_ID NUMBER(10)`. Product fix widened precision 10→19. Customer workaround (verbatim from case):
```sql
ALTER TABLE QRMTIPS_CAW.QTRAN_IMBAL_ACCT_ACTIVITY_DTL MODIFY ACCT_ACTIVITY_DTL_ID NUMBER(11);
ALTER TABLE QRMTIPS.QPOST_IMBAL_ACCT_ACTIVITY_DTL    MODIFY ACCT_ACTIVITY_DTL_ID NUMBER(11);
ALTER TABLE QRMTIPS.QTRAN_IMBAL_ACCT_ACTIVITY_DTL    MODIFY ACCT_ACTIVITY_DTL_ID NUMBER(11);
```
(Product standard is NUMBER(19); cover **all three** tables — QTRAN + QPOST + the CAW-schema copy.)

**Code refs:** imbalance balance logic lives in `Quorum.TIPS.ClassicBatch /Common-QI/QPDllTipsImbalance/QPSCustAcctBal.cpp`, `Quorum.TIPS.Crude.Batch .../QPDllTipsCrudeImbalance/CustAcctBal/QCustAcctBal.cs`, web DO/DAL `ImbalAcctBalDO.cs` / `ImbalAcctBalDAL.cs` (Quorum.TIPS.Web).

---

## 6. Gas Lift Duplication (ASSCGLM)

**Symptom:** Gas lift volumes doubled after a plant re-run; "TIPS is double counting gas lift"; netted gas-lift MMBTU wrong.

**Root cause:** The **ASSOCIATED GAS LIFT METER VOL (ASSCGLM)** process step creates duplicate rows in `QTRAN_ALLOC_VOL` when the plant runs dailies **in reallocation mode** — old ASSCGLM records are not purged before re-insert. In TIPSLOCK, TIPS sets `PROCESS_IND` in `QTRAN_TRNX_ID` from reallocations logged in `QTRAN_PLANT_STATUS_REALLOC`, so a realloc-mode run only reprocesses changed meters — and re-generates ASSCGLM rows on top of the old ones. (Repro documented verbatim in 25-01023169.)

**Resolution:** Fixed in ADO **#1731166** (Bug, Closed): engineering added a **DELETE of existing `QTRAN_ALLOC_VOL` rows with `PROCESS_ID = 'ASSCGLM'` before new entries are inserted**. Until the fix is on the client build: take the plant **out of reallocation mode** on the facility lock screen before re-running, or have Cloud Ops purge the duplicate ASSCGLM rows and re-run.

**Representative cases:** 25-01023169 (ETP — closed dup of #1731166), 25-01041541 (Hess, Gas Lift Volumes duplicating — resolution not recorded in SF), 24-00994584 (Merit upgrade double-count — resolution not recorded), 25-01025397 (ONEOK netted gas-lift MMBTU — resolution not recorded). For the three null-resolution cases the recipe above is the best-evidence match; resolution pattern otherwise unclear from mined cases.

**Config note:** ASSCGLM is registered per client in `<CLIENT>.TIPS.Metadata /STANDARD 16.0/QARCH_CTRL_PROCESS_STEP*.json` (seen in DCP/IAC/VMH metadata repos) — verify the step exists/ordering for the client before chasing a code defect. Follow-on requirement ADO **#1792826** "Handle ASSCGLM" is Proposed.

---

## 7. QTRAN_PAYSTATION Build Failures & Duplicates

**Symptom:** Daily Gathering / Monthly batch fails `ERROR SETTING VALUE FOR COLUMN EFF_PCT_CONTR`; or duplicate rows found in `QTRAN_PAYSTATION`.

| Issue | Root cause | Fix | Evidence |
|---|---|---|---|
| `EFF_PCT_CONTR` set-value error when meas volume is tiny and nom is huge | Computed effective % overflowed `S_DECIMAL NUMBER(14,10)` | DB change: widen to `NUMBER(16,10)` in `QTRAN_PAYSTATION` | 24-00994961 (ETP, BTP Co & PAN plant) |
| Registered SQL `m_INS_STMT` inserting 116 duplicates into QTRAN_PAYSTATION | Registered-SQL defect | Code fix | ADO #1783341 (Closed, PEP 26-01083551) |
| Duplicate QTRAN_PAYSTATION records "after bad use of the application" | User-induced dup rows | Cloud Ops delete script | ADO #1782988 (Closed, PEP 26-01080672) |
| Paystation insert dup from contract eff-date overlap | See §3 — fix the SEXTN_CTR_HEADER slice first | Data script | 25-01002372 |

**Triage rule:** a paystation "duplicate" error is **contract-slice data** (§3) until proven otherwise; only after the slices check clean should you suspect the registered SQL (#1783341) or ask Cloud Ops for a dedupe (#1782988 pattern).

---

## 8. Facility Definition / Allocation Group Configuration

**Symptom:** A product's allocated volumes don't match (esp. NGL components), fuel allocated on the wrong basis, negative liquid volumes failing checks (CHKNEGVOL).

**All Application Configuration — fixes are screen edits, no code:**
| Issue | Fix (exact screen/config) | Case |
|---|---|---|
| Natural Gasoline allocated volumes don't match | **Facility Definition**: include **IC5 and NC5** as components instead of **C5+** | 25-01011404 (Howard STX) |
| Physical constants for Natural Gasoline need monthly update by inlet meter | Update the **allocation group** handling Nat Gasoline to **recalc Heat Value based off Gallons (Liquid Volume)** | 25-01027694 (Howard) |
| Fuel allocation basis wrong (MCF vs MMBTU) | **Facility > Allocation Group** (in the allocation step) → change basis of fuel allocation MCF→MMBTU | 25-01002531 (Midstream Energy Services) |
| New meter + contract not allocating | Configure the **allocation groups** for the new meter and contract | 24-00977227 (Merit) |
| CHKNEGVOL errors running Bantry — negative liquid volumes (Propane Produced C1) | **Allocation group to zero out negative liquid volumes** + override inventories for the report | 26-01086773 (Pivotal) |
| Meter "NOT ALLOCATING BACK" | Meter wasn't included in **net delivered** | 24-00980900 (Utah Gas) |
| Allocation group From-Point attribute not editable | User access grant | 25-01049847 (Howard) |

---

## 9. PPA Framework Failures

**Symptom:** Can't un-approve PPAs (concatenate error, holding up close); Evolution prod-month PPA plant re-runs fail; reinstated PTR populates 0.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **Un-approve PPA fails — concatenate error** | Un-approve SQL appends to `COMMENTS varchar2(4000)`; long comments overflow | Short-term: **script to clear the comments** (KB drafted: Knowledge article ka0UG0000002dDNYAY); long-term: SQL updated to restrict comment to 4000 chars | 24-00990256 + 24-00991302 (DCP) |
| Evolution PPA plant re-run (MEASUREGTT→ARAP_IFGTT) fails **unique constraint QPTMSTAGPERMWHALLOC** | Staging-table re-insert defect on re-run | Code defect — resolution not recorded in SF; escalate with PQID (e.g. 15358636 pattern) | 24-00976492 (Enterprise) |
| MID PPA errors at **PSWHALLOC** step | Resolution not recorded in SF — pattern unclear from mined cases | — | 25-01004848 (Enterprise) |
| Permian PPA populating **0 for reinstated PTR** (UAT) | Resolution not recorded in SF | — | 24-00984585 (Enterprise) |
| PPA created on wrong month causing duplicate; re-run blocked | Re-running with the earlier month added as re-run month clears the dup records | Add the earlier prod month as re-run month, re-run | 25-01040113 (training case, same recipe) |
| Regression settlement issue on Permian/MID PPA months | Setup research via provided code-change description | Config research doc | 25-00999257 |

> Enterprise (ETP/MEN/Permian/MID) dominates Evolution-PPA defects; several closed without an SF-recorded resolution — check ADO and the client's patch notes before re-investigating from scratch.

---

## 10. Imbalance Posting / Customer Account Balance Config

**Symptom:** Imbalances missing from Customer Account Balance after close; cashout/CICO wrong; imbalance statement dates wrong.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Imbalances vanished after PA close | **POSTRESULT ran prematurely — missing process dependency** | Update the dependency for POSTRESULT; reprocess PA as a PPA to restore + post | 25-01021133 (Howard) |
| Cashout (CICO) terms not applying for a contract | Imbalance type missing **CICO indicator** | Turn on CICO indicator on the Imbalance type (e.g. EFGDC) | 25-01006116 (Howard STX) |
| Missing imbalance volumes entirely | Rounding bound check | Global config `PROGRESSIVE_ROUNDER_NO_BOUND_CHECK = 1` (verify expected results; behavior-wide change) | 24-00985175 (ETP) |
| Daily Imbalances report missing days 8–13 | Facilities flagged for **reallocation** → batch zeroes those days | Uncheck the reallocation checkbox for the facilities/dates | 24-00968763 (Merit) |
| Imbalance Statement wrong accounting date | Report logic picked first day of *week* instead of first of month | Report logic fix | 25-00999876 (Howard) |
| Interconnect imbalance split across two systems | Split interconnect meters into 4 manual meters customer maintains | Config/master-data redesign | 25-01006432 (Howard) |
| Customer account balance systematically off | **Imbalance module mis-configured at implementation** — beyond support scope | Services engagement (quote) | 25-01048219 (Hilcorp) |
| Prelim cashout restated dth ≠ QPTM (PPA revision) | Resolution not recorded in SF | — | 25-01016551 (Enterprise) |

---

## 11. Facility Batch Job / Plant Close-Settle Errors

**Symptom:** Measure→Settle facility batch job or plant/accounting close fails.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Settle fails; log hints "meter split issue" with no detail | **Missing price index (GDP)** | Add the index (GDP); settle completes | 24-00970370 (Utah Gas) |
| Facility Batch Jobs errors after patch | Defect already fixed for another client in 2024 | Patch back-port to client's version | 24-00985139 (Opportune) |
| Error closing plant after Gathering Module implementation | Resolution not recorded in SF — implementation config suspected | — | 25-01029278 (Hess) |
| Error before allocation process starts | Resolution recorded only as "Resolved" — pattern unclear from mined cases | — | 24-00975846 (Hess) |
| Settle POP formula error on low measured volumes | Formula variable (MDQFAC) out of range on near-zero/false-flow volumes | Zero the bad measured volume; check meter sensors/measurement feed | 25-01009718 (customer-error case, same recipe) |
| Can't close accounting period — unposted facility | EVERY facility for the month must run (even inactive/errored ones) before posting | Run the missing facility, then post | 26-01084761 (training) |
| Can't close prod month | Contract present in **2 invoice groups** | Remove contract from one invoice group | 26-01090740 (customer error) |

---

## 12. TIPS ↔ QPTM Evolution Sync Issues

**Symptom (Evolution/integrated clients — EQT, Enterprise):** TIPS doesn't receive data from QPTM; PTR process warnings; allocation registered-SQL errors after conversion.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| ALALLOCATE "Error in Registered SQL" (TSP 24 + 8925) | **TSP configs in `PACTRL_TSP_CNFG_CTRL` all set to '2' by a conversion error** | Delete and reconvert the config values for the affected TSPs | 25-00996952 (EQT) |
| "DLL Could not be loaded" for TSP 24 + 8925 | Wrong artifact — `EQC.QPTM.Application.QPEC` needed the **client artifact** | Deploy client artifact | 25-00998540 (EQT) |
| Warning: TIPS doesn't receive data from QPTM | Resolution not recorded in SF | — | 24-00972258 (Enterprise) |
| Re-config all PTR process warning messages | Resolution not recorded in SF (enhancement-flavored defect) | — | 24-00969555 (Enterprise) |

> Cross-reference **SKILL_Allocations.md §7/§12** for the QPTM side (ALPTRSYNC, PTR overlay) of the same Evolution clients.

---

## 13. Web-vs-Classic Screen Defects

**Pattern:** Web (MyQuorum) screens lag Classic or carry web-only defects; the resolution is almost always **"the fix exists — check the build"**.

| Issue | Fix | Case |
|---|---|---|
| Production-month volume entry error (web-only) | Fix in **2025.04.1.4+**; client PRD was 2025.04.1.3 → patch, workaround in Classic | 26-01091817 (Hilcorp) |
| Global Attribute Formulas not working in Web | Bug fix with patch | 25-01035964 (Steel Reef) |
| Post Settle Indicator bug | Bug fix with patch | 25-01035013 (Steel Reef) |
| PDA-without-noms errors in UAT (SWK facility) | **Patches were never deployed to UAT during the project** — redeploy patches, restart services | 26-01091115 (Scout) |
| Meter Split web issue (EIG 2025.04); split decimal not updated after batch (2026.04 beta); CML validation gaps | Open/Proposed bugs — see §15 | ADO #1803147, #1795476, #1801070, #1809771 |

**Triage rule:** before any code investigation, get **PRD build number vs the fix version**; for UAT-only anomalies, confirm patch parity between UAT and PRD (26-01091115).

---

## 14. Report / View Calculation Errors

| Report/view | Issue | Fix | Case |
|---|---|---|---|
| Operations Summary NGL Report | Results inconsistent — **conversion factors in the view were incorrectly patched** in the last software update | Corrected view; included in next software update | 26-01084648 (Inter Pipeline) |
| PARKLAND Gas Gathered Volumes | Net delivered ≠ Gathered − fuel | Resolution not recorded in SF | 24-00979895 (Pivotal) |
| Daily Imbalances (TIPS) report | Days missing (realloc-mode zeroing) | §10 — uncheck reallocation | 24-00968763 |
| Imbalance Statement | Accounting date = first day of week, not month | Report logic fix | 25-00999876 |
| Bantry volume upload | Import file **column naming didn't match the import definitions** | Fix file headers per import definition | 24-00989688 (Pivotal) |
| Stored proc pulling volumes at facility level | Client wanted company level | Proc update request (config) | 24-00981970 (Hess) |

> As with QPTM: verify the **underlying table data is right** before touching the report — most "report bugs" here were view/report-layer only.

---

## 15. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1731166** | Bug / **Closed** | ASSOCIATED GAS LIFT METER VOL (ASSCGLM) creates duplicates when run for dailies in reallocation mode | §6 | 25-01023169 |
| **#1772687** | Script Deployment / **Closed** | HEC — Delete duplicates from QTRAN_IMBAL_ACCT_BAL PRD (12/2025) | §5 | 25-01060242 |
| **#1776627 / #1776858 / #1776936** | Script Deployments / **Closed** | HEC — Delete duplicates from QTRAN_IMBAL_ACCT_BAL UAT+PRD (1/2026) | §5 | 26-01065143 |
| **#1778736 / #1778789** | Script Review + Deployment / **Closed** | HEC — Delete duplicates from QTRAN_IMBAL_ACCT_BAL UAT/PRD (1/2026) | §5 | 26-01068169 |
| **#1783341** | Bug / **Closed** | PEP — Registered SQL m_INS_STMT creating 116 duplicates into QTRAN_PAYSTATION | §7 | 26-01083551 |
| **#1782988** | Request Global Cloud Ops / **Closed** | PEP — Script to delete duplicate QTRAN_PAYSTATION records | §7 | 26-01080672 |
| **#1788087** | Bug / **Closed** | UPC — QCM invalid-effective-date error in Contract Meter List after changing contract effective date | §3 | 26-01084783 |
| **#1780377** | Bug / **Active** | ETP — QCM Contract Meter List Copy/Paste not autopopulating required field | §3 | — |
| **#1801070** | Bug / Proposed | 2026.04 QCM Beta — CML validation for incorrect meter dates not triggered | §3 | — |
| **#1809771** | Bug / Proposed | HVK — Validation for CML and Meter Split | §3/§4 | — |
| **#1795476** | Bug / Proposed | 2026.04 TIPS Beta — Meter Split: Split Decimal not updated after batch job | §4 | — |
| **#1803147** | Bug / Proposed | EIG 2025.04 — Meter Split Web issue | §4/§13 | — |
| **#1792826** | Requirement / Proposed | Handle ASSCGLM | §6 | — |
| **#1770292** | Database Change / Rejected | Update custom where clause of QTRAN_PAYSTATION & QTRAN_ALLOC_VOL purge (QCODE_REC_PURGE) | §7 | — |

---

## 16. Diagnostic SQL

### A. Contract header time slices — overlap/gap check (the §3 workhorse)
```sql
SELECT CTR_NO, EFF_DT_FROM, EFF_DT_TO, MTR_SFX_CD, UPDT_DT, USER_ID
FROM   QRMTIPS.SEXTN_CTR_HEADER_QRMTIPS          -- schema/suffix varies by client
WHERE  CTR_NO = '<CTR_NO>'
ORDER BY EFF_DT_FROM DESC;
-- Red flags: two rows covering the same month (overlap → paystation dup error, 25-01002372);
--            no row covering the failing month (gap → contract not allocating, 26-01100512).
```

### B. Duplicate imbalance account balances (§5)
```sql
SELECT BA_NO, CTR_NO, ACCT_DT, PROD_DT, COUNT(*) AS DUP_CT
FROM   QTRAN_IMBAL_ACCT_BAL
WHERE  ACCT_DT = '<ACCTG_MTH>'
GROUP BY BA_NO, CTR_NO, ACCT_DT, PROD_DT
HAVING COUNT(*) > 1;
-- Column names beyond the table name are inferred from the duplicate-key pattern; verify against
-- the client schema before scripting (the HEC dedupe scripts live in ADO #1772687/#1778789 attachments).
```

### C. ASSCGLM duplicate gas-lift rows (§6)
```sql
SELECT *
FROM   QTRAN_ALLOC_VOL
WHERE  PROCESS_ID = 'ASSCGLM'
  AND  PROD_DT = '<PROD_DT>'          -- scope to plant/prod month
ORDER BY UPDT_DT DESC;
-- Duplicates here after a realloc-mode re-run = the #1731166 defect. Also check reallocation state:
SELECT * FROM QTRAN_PLANT_STATUS_REALLOC WHERE PROD_DT = '<PROD_DT>';
SELECT PROCESS_IND, COUNT(*) FROM QTRAN_TRNX_ID GROUP BY PROCESS_IND;   -- TIPSLOCK realloc routing
```

### D. Imbalance activity sequence vs column precision (§5)
```sql
SELECT QTRAN_IMBAL_ACCT_ACTIVITY_D_SQ.NEXTVAL FROM DUAL;   -- compare digits vs column precision
SELECT TABLE_NAME, COLUMN_NAME, DATA_PRECISION
FROM   ALL_TAB_COLUMNS
WHERE  COLUMN_NAME = 'ACCT_ACTIVITY_DTL_ID'
  AND  TABLE_NAME IN ('QTRAN_IMBAL_ACCT_ACTIVITY_DTL','QPOST_IMBAL_ACCT_ACTIVITY_DTL');
-- Product fix = NUMBER(19) (25-01014345). Remember the QRMTIPS_CAW schema copy.
```

### E. Paystation duplicates (§7)
```sql
SELECT CTR_NO, MTR_NO, PROD_DT, ACCT_DT, COUNT(*) AS DUP_CT
FROM   QTRAN_PAYSTATION
WHERE  ACCT_DT = '<ACCTG_MTH>'
GROUP BY CTR_NO, MTR_NO, PROD_DT, ACCT_DT
HAVING COUNT(*) > 1;
-- If dups trace to one contract → run A first (contract-slice overlap). Key columns inferred; verify.
```

### F. Meter split sanity (§4)
```sql
-- Splits for a meter: do the WIO%/split decimals sum to 1.0, and is any contract at 0?
-- (Use the Meter Split query screen first; table-level check via client schema's meter split table.)
-- Zero split for an active contract = the 25-01056537 zero-volume pattern.
```

---

## 17. Expected-Behavior / User-Education FAQ

From the Training / Customer Error sample (51 Training + 42 Customer Error of the 397):

1. **"Meter is not settling / not on the allocated volume query."** → No **CCT set up on the meter split for the current production month** (26-01100577); or **Split Decimal = 0 at Meter Split**, which flows zeros into Paystation and settlement (26-01091612). Master-data completeness, not a defect.
2. **"Can't add a CCT" / CCT save errors.** → Users open an *existing* CCT and change the CCT# instead of creating new (26-01099946). CCTs duplicated from another CCT can hit a cached `seq_no` on `QCTRL_CCT_FEE` — open a fresh window and copy the data in (25-01018951). Newly created formulas not appearing on Rate Schedules = **caching**; requery/new session (26-01098611).
3. **"Can't close the accounting period — unposted error."** → Every facility active in the month must be run (even an inactive facility that ran batches earlier in the month) before posting (26-01084761). A contract sitting in **two invoice groups** also blocks close (26-01090740). For accounting-month misalignment, set **ACCOUNTING PERIOD MODE to facility level**, create the matching accounting month, then post (25-01055239).
4. **"CCT data disappeared / overlapping timeslices appeared."** → Caused by running the **Escalation process** incorrectly; fix the CCTs and follow the escalation runbook (26-01094306).
5. **"Settlement invoice missing a counterparty."** → Contract not updated with the correct **BA suffix** (26-01088067). Similarly, "BA numbers list not populating" = user not configured as internal (25-01048500).
6. **Known-bug FYI:** Contract Unscoped picklist blank in 2025.10 — existing bug with a published RightAnswers workaround (solution 260429123014117) (26-01088401).
7. **How-to favorites:** end-dating/expiring a meter (25-01046352), deleting meter splits via the application (25-01029908), deleting duplicate meters via Meter Definition (26-01101667), Contract Listing report under Miscellaneous report types for CCT/fee/POP listings (25-01016055).

---

## 18. Escalation Guidance

**It's a DEFECT → Engineering (file/attach to ADO bug):**
- Duplicate-row generators: `QTRAN_IMBAL_ACCT_BAL` dups (§5 — cite #1772687 lineage + the 2025.04 fix), ASSCGLM gas-lift dups (§6 — #1731166), `m_INS_STMT` paystation dups (§7 — #1783341), QPTMSTAGPERMWHALLOC unique constraint on Evolution PPA re-runs (§9).
- Precision/overflow errors: EFF_PCT_CONTR (§7), ACCT_ACTIVITY_DTL_ID sequence (§5), WIO% CAST rounding (§4).
- Validation defects on QCM screens: CML invalid-eff-date (#1788087), CML copy/paste (#1780377), CML/Meter-Split validation gaps (#1801070/#1809771).
- Web-only behavior where Classic works (§13) — but **only after confirming the fix isn't already shipped** in a later patch than the client's PRD build.

**It's CONFIG/DATA → Cloud Ops (script or screen change):**
- Contract time-slice overlap/gap scripts (§3), QCM contract end-date corrections.
- Dedupe scripts (imbal acct bal, paystation, ASSCGLM rows) — always scoped to client/env/month, with a verify-SELECT, via Script Review → Script Deployment WIs.
- Facility Definition / Allocation Group edits (§8), CICO indicator, POSTRESULT dependency, global rounding configs (`PROGRESSIVE_ROUNDER_NO_BOUND_CHECK`), index (GDP) additions.
- Patch (re)deployment / UAT-PRD parity (26-01091115, 26-01091817).

**It's the CUSTOMER/Services:**
- Imbalance module mis-implemented at project time → Services quote (25-01048219).
- Missing CCT/split/BA-suffix master data, invoice-group misuse, escalation-process misuse → user education (§17).

**Always capture before escalating:** client + env (PRD/UAT/DEV), build/patch version, plant/facility + accounting month + production month, the Process Queue ID for batch failures, and the exact constraint/column name in the error — the table name alone (IMBAL_ACCT_BAL vs PAYSTATION vs ALLOC_VOL) routes you to the right cluster.

---

*Skill created: 2026-06-11. Evidence: 397 closed TIPS Master Data/Contracts-group cases; 70 actionable (Software Defect / Application Configuration) mined in detail; 30-case Training/Customer Error sample; ADO items #1731166, #1772687, #1776627/858/936, #1778736/89, #1783341, #1782988, #1788087, #1780377, #1801070, #1809771, #1795476, #1803147, #1792826, #1770292; code refs from ADO code search (Quorum.TIPS.ClassicBatch, Quorum.TIPS.Crude.Batch, Quorum.TIPS.Web, SEM/DCP/IAC/VMH.TIPS client repos).*
*Data-quality caveats: aggregate root-cause counts implied 91 actionable (43 SD + 38 AC + 10 ChangeConfig) but the detail query returned 70 (no ChangeConfig rows retrievable); Case_Category__c on returned rows displays functional areas (Allocation Maintenance/Imbalances/PPA Framework) rather than the master-data category labels used in the filter; ~10 actionable cases have no recorded Resolution__c — those clusters are flagged "resolution pattern unclear" rather than invented.*
