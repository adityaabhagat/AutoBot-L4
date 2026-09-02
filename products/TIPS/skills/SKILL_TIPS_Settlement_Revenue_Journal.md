# SKILL: TIPS Settlement / Revenue / Journal Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-11 | **Product:** TIPS (My Quorum TIPS — gas & crude transaction processing / settlement accounting)
**Scope:** The back-end accounting pipeline — **Settlement** (Settle Day / Settle Process / CAR / WAH processors, GEN PTR, Fixed Fuels, rate schedules, UDEFs, fees, escalations), **Revenue** (Revenue Override, revenue export/CICO, margin/volume tie-out), and **Journal** (Journal Entry Control setup, Journal Process / Journal Transfer to SAP/GL, journal reports). Also Annual Equalizations (rare).
**Companion skills:** Allocation/PPA/imbalance → **SKILL_TIPS_Allocations_PPA_Imbalance.md**; statements & report formatting → **SKILL_TIPS_Reporting_Statements.md**; rate/fee/contract master setup → **SKILL_TIPS_Invoice_Billing_Rates.md** and **SKILL_TIPS_Master_Data_Contracts.md**; batch job mechanics (process queue, steps, restart) → **SKILL_TIPS_Batch_Processing.md**. This skill *consumes* allocated volumes + measurement + contract rates and *produces* settled products/values, revenue, and journal entries — fix upstream allocation/measurement first when the settled number itself is wrong (it is usually the messenger).

> **Evidence base:** 577 closed TIPS Settlement/Revenue/Journal cases. Root-cause split: Training 96, (blank) 95, **Software Defect 76**, Business Change 66, Customer Error 55, Customer Cancelled 40, **Application Configuration 32**, **ChangeConfig 14**, others. This skill mines the **122 actionable** cases (Defect + App-Config + ChangeConfig) for fix recipes, plus ~60 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining. Category mix of the 577: Settlement 344, Revenue 143, Journal 89, Annual Equalizations 1.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — Settle Day / GEN PTR batch-step failures (HIGH FREQUENCY)](#4-cluster-a--settle-day--gen-ptr-batch-step-failures)
5. [Cluster B — CAR / WAH processor & daily-CCT settlement (Evolution)](#5-cluster-b--car--wah-processor--daily-cct-settlement)
6. [Cluster C — Journal not generating / wrong journal config](#6-cluster-c--journal-not-generating--wrong-journal-config)
7. [Cluster D — Journal sign / reversal / tax handling](#7-cluster-d--journal-sign--reversal--tax-handling)
8. [Cluster E — Journal batch-process failures (JRNTRSPEN1 / JrnVchrRpt / transfer)](#8-cluster-e--journal-batch-process-failures)
9. [Cluster F — Rate schedule / UDEF / fee & escalation calculation](#9-cluster-f--rate-schedule--udef--fee--escalation-calculation)
10. [Cluster G — Fixed Fuels & UOM mapping](#10-cluster-g--fixed-fuels--uom-mapping)
11. [Cluster H — Revenue Override, revenue export & volume tie-out](#11-cluster-h--revenue-override-revenue-export--volume-tie-out)
12. [Cluster I — Contract / CCT / meter timeslice & overlap data fixes](#12-cluster-i--contract--cct--meter-timeslice--overlap-data-fixes)
13. [Cluster J — Performance (PRICETOSCH / PPA volume / out-of-memory)](#13-cluster-j--performance)
14. [Known ADO Items](#14-known-ado-items)
15. [Diagnostic SQL](#15-diagnostic-sql)
16. [Expected-Behavior / User-Education FAQ](#16-expected-behavior--user-education-faq)
17. [Key Code, Processes & Repos](#17-key-code-processes--repos)
18. [Escalation Guidance](#18-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| Settle Day / GEN PTR / `Measurement to GEN PTR` errors at **Settle Daily step** with `ORA-00001 unique constraint (ESUITE_QENT.UNIQUE_ETRAN_GAS_PRICE_DAILY)` | Duplicate daily gas-price rows when daily logic is on (`ENT_DAILY_VOL_LOGIC_CHANGE_DT`); also re-run/PPA months | Process Queue ID + step; check `ETRAN_GAS_PRICE_DAILY` dups; **§4** (data-script + the patch that blocks daily values pre-cutoff) |
| Settle job "Stopped Processing on Error" at a named step (CFTOOUTVOL, GEN PTR, PRICETOSCH, JRNTRSPEN1) | Step-specific defect or bad data; sp returning >1 row into a `SELECT INTO` | PQID + the **exact step name + ORA error**; §4/§8/§13 |
| Journal not generating for a contract/meter | Journal Entry Control **condition** missing or **double condition**; Journal Conditions filter | §6 — check Journal Entry Control setup for that CCT/meter |
| Journal report/transfer/query shows **0 for a net-negative** account, or doesn't reverse taxes | Sign/reversal handling (IT_VALUE UDEF, FEE<0→0 default, tax reversal) | §7 — Journal Entry Control value type & UDEF; tax reversal is a known gap |
| Cost center / journal column truncated, char-limit mismatch CAN vs core | Column length / metadata config | §6 — cost-center char limit, CAN vs core column widths |
| Revenue Override screen errors / "need services restarted" / query hangs | App-tier/service issue, often transient | §11 — restart services; capture ClassicGUI logs before; usually NOT a code fix |
| Double / 6x volume on revenue or settlement vs allocation | Allocation/dedication-agreement setup, or daily-vs-monthly CCT level | §5/§11 — verify upstream allocation first; check CCT unit-time-code |
| Rate schedule simple average wrong when a price is 0; UDEF If/Then/Else rounding wrong; escalation off | Calculation defect in rate-schedule/UDEF engine | §9 |
| Fee/fuel not populating on statement/invoice; residue/field-fuel missing | **Fixed Fuels UOM mapping** to invalid UOM class; UDEF→UOM remap | §10 |
| Settle product NGLs/residue not tying out | Upstream fuel/UOM or NDD/gas-analysis config; allocation | §10/§16 — verify gas analysis & UOM first |
| PRICETOSCH / PPA / statement gen taking hours / out-of-memory | Performance — query not filtered, PPA volume over recommended limit (~2000/month) | §13 |
| Can't save CCT / new BA / formula end-date / meter timeslice | Data: overlapping timeslices, null key columns, security | §12 |

---

## 2. Pipeline & Concepts

```
[Measurement / Gas Analysis] + [Allocation] + [Contract CCTs + Rate Schedules + UDEFs + Fixed Fuels]
      │
      ▼  SETTLE DAY / SETTLE PROCESS   (daily: GEN PTR; processors: CAR, WAH; steps: CFTOOUTVOL, SETTLEDAY, PRICETOSCH …)
[QTRAN_SETTLE_PROD  (settled products/values, PTR), QTRAN_ESCALATE_RESULTS]
      │
      ├──► REVENUE  (Revenue Override, Revenue Export / Billing CICO, margin/volume tie-out)
      └──► JOURNAL  (Journal Entry Control → JOURNAL Process → Journal Transfer file → SAP/GL; journal reports/queries)
```

### Key terms (Quorum/TIPS vocabulary)
- **CCT** = Contract Charge Type (a.k.a. Contract Calc Type) — the row on a contract that drives a settled charge/fee. Has a **unit time code** (daily vs monthly) — a mismatch (CCT at monthly level when measurement is daily) causes wrong roll-ups (24-00964004).
- **PTR** = Plant Thermal Reduction / plant-value figure generated by **GEN PTR** in the daily Settle path; stored in PTR tables. Negative/incorrect PTR is a recurring CAR-processor symptom (24-00963334).
- **CAR / WAH** = settlement processors run on **Settle Day** (CAR = Contract Accounting Routine-type processor; WAH = Wellhead/Well allocation-to-settlement). Heavily used by ENT (Enterprise) Evolution/daily clients.
- **Settle Day steps** (each can fail independently): `SETTLEDAY`, `CFTOOUTVOL` (CFTO out-volume), `GEN PTR`, `PRICETOSCH` (price-to-schedule / import esuite indexes to TIPS). Get the **Process Queue ID (PQID)** + the failing step name — they key the log.
- **Rate schedule / UDEF** = pricing formulas. **UDEF** = User Defined Formula (incl. journal `IT_VALUE`, settlement If/Then/Else, simple-average rate schedules). Rounding and 0-price handling are known defect areas.
- **Fixed Fuels** = a tab on the CCT defining field/plant fuel; UOM there must map to a valid **UOM Class Code** or fuel silently won't calculate (23-00876904).
- **Journal Entry Control** = the screen/config that maps settled fees/products → GL accounts/cost centers via **conditions** and **value types** (DTLFEE core type, or `IT_VALUE`/`IT_VALUE ADJUSTMENT` UDEF). The JOURNAL process reads it to build the **Journal Transfer file** to SAP/GL.
- **`ENT_DAILY_VOL_LOGIC_CHANGE_DT`** = ENT client config date (e.g. 6/1/23) that switches Settle from monthly to daily logic. Months before it must NOT get daily values — a defect generated them and collided on the daily-price unique key (24-00940258).
- **QQM** = Quorum Query Manager report layer (journal/revenue query screens). A bad field in the QQM select can break the whole query (25-01028136).
- **NDD** = client config (gas-analysis "no data"/default config) referenced in CAR tie-out resolutions (23-00925877/879).

---

## 3. Decision Tree

```
Settlement / Revenue / Journal case
│
├─ A batch process/step failed? (Settle Day / GEN PTR / Journal Process / PRICETOSCH)   →  GET PQID + STEP NAME + EXACT ORA/COM ERROR
│   ├─ "unique constraint UNIQUE_ETRAN_GAS_PRICE_DAILY" at SETTLEDAY step  → §4  (daily-logic dup; data script + ENT_DAILY_VOL_LOGIC_CHANGE_DT patch)
│   ├─ CFTOOUTVOL / sp pulled >1 row into SELECT INTO (re-run months)      → §4  (sp defect on rerun)
│   ├─ Journal step (JRNTRSPEN1 / JrnVchrRpt / serialization / BA datatype)→ §8
│   ├─ Add a purge table / step-config gap (ETRAN_GAS_PRICE_DAILY purge)   → §4  (24-00942763)
│   └─ PRICETOSCH slow/hangs                                                → §13 (perf)
│
├─ Journal output wrong (not the process crashing)?
│   ├─ Journal not generating for a contract/meter                          → §6  (missing/double condition in Journal Entry Control)
│   ├─ Net-negative account shows 0 / reversal not reversed / tax not reversed → §7
│   └─ Cost-center/column truncated, CAN vs core char limit                  → §6
│
├─ Revenue?
│   ├─ Override screen error / "restart services" / hang                     → §11 (service restart; capture logs; usually not code)
│   ├─ Double / 6x volume vs allocation                                      → §5/§11 (fix upstream allocation / CCT level first)
│   └─ Export / CICO price not populating on PMA/re-run                       → §11 (defect — patch)
│
├─ Settled number wrong (fee/fuel/rate/escalation)?
│   ├─ Fee/fuel/residue missing on statement                                 → §10 (Fixed Fuels UOM → UOM Class Code mapping)
│   ├─ Rate schedule simple-avg with 0 / UDEF rounding / escalation          → §9
│   └─ Number ties to bad allocation/measurement/gas-analysis                → upstream (Allocations / Measurement skill); see §16
│
├─ Can't save CCT / BA / meter timeslice / end-date a formula?              → §12 (data: overlap, null key cols, security)
│
└─ Vague "error", audit question, "how do I…", PPA reprocess request        → §16 Expected-Behavior FAQ (Training / Customer Error)
```

---

## 4. Cluster A — Settle Day / GEN PTR batch-step failures

**The single largest actionable settlement-batch signature.** ENT (Enterprise) Evolution/daily clients run **Measurement → GEN PTR → SETTLEDAY** and the **SETTLEDAY step throws `ORA-00001` on `UNIQUE_ETRAN_GAS_PRICE_DAILY`**, so no PTR is generated.

**Symptom (verbatim, 24-00942763 / 24-00940256):**
```
[COM Error] ... QADOCommand.cpp ... ORA-00001: unique constraint (ESUITE_QENT.UNIQUE_ETRAN_GAS_PRICE_DAILY) violated  ORA-06512: at line 1
```
seen at the **Settle Daily step** of `Measurement to GEN PTR` for plants ORL, MEN, SRA (PQIDs e.g. 14326679, 14333473).

**Root causes & fixes seen:**
- **Daily logic generating values for months before the cutoff.** `ENT_DAILY_VOL_LOGIC_CHANGE_DT` (e.g. 6/1/23) switches Settle to daily; a defect let daily settlement values be created for *prior* months, colliding on the daily gas-price unique key. **Fix (24-00940258):** code fix deployed that *prevents daily settlement values from being generated for months prior to the `ENT_DAILY_VOL_LOGIC_CHANGE_DT` date.*
- **Rate-schedule / config gap (ORL, 24-00940256):** "Configuration changes missing in ORL for rate schedules that were using the **RPCTR / RPMTR** formulas. Applied changes to use values as **index adjustments** and the batch job ran successfully." → **Application Configuration** fix on the rate schedules.
- **Purge-table gap (24-00942763):** the duplicate-price collision was cleared by adding **`ETRAN_GAS_PRICE_DAILY` to the rec-purge table list for the Settle Day process** (so the prior run's daily prices are purged before re-insert). This is the repeatable operational fix; Will/engineering held the data script for the historical occurrences (SRA, ORL, MEN).

**Other Settle-step failures:**
- **CFTOOUTVOL step fails on rerun months (22-00649145, Pioneer MKBN5):** root cause "**sp pulled in more than 1 line for a `SELECT INTO`** resulting in an error for rerun months" → stored-proc defect; fix the sp to constrain to one row.
- **Residue from Fixed Fuels not transferring to `QTRAN_SETTLE_PROD` (24-00964004):** dedicated-agreement CCT was applied at monthly level though unit time code was daily → CCT now populated only at the correct unit time code so the rolled-up monthly value evaluates correctly (code fix to ENT).

**Fix recipe:**
1. Get **PQID + failing step name + exact ORA/COM error**. Double-click the error row in Batch Messages to read the log.
2. `UNIQUE_ETRAN_GAS_PRICE_DAILY` at SETTLEDAY → confirm daily logic is on (`ENT_DAILY_VOL_LOGIC_CHANGE_DT`), confirm you are not re-running a pre-cutoff month, dedupe `ETRAN_GAS_PRICE_DAILY` for the prod month, ensure the table is in the Settle-Day purge list, re-run scoped to the plant/month. Confirm the ENT patch (24-00940258) is deployed.
3. `SELECT INTO` >1-row / CFTOOUTVOL on rerun → stored-proc defect (22-00649145), escalate to Engineering with the PQID.
4. Always scope re-runs to the specific **plant + prod month + acctg date**; wrap any data clean-up in a transaction with a verify-SELECT.

---

## 5. Cluster B — CAR / WAH processor & daily-CCT settlement (Evolution)

ENT/Evolution clients settle through **CAR** and **WAH** processors on Settle Day. Most cases here are **Application Configuration** around **dedication-agreement / daily-vs-monthly CCT** setup, surfacing during STX/Midland E2E (DEVF/UATA) testing.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| CAR T27D **incorrect negative PTR** | Dedication-agreement setup for **daily CCTs** | Resolved by dev for Panaya issue 145; validated in DEVA1 | 24-00963334 |
| Residue from Fixed Fuels not transferring to `QTRAN_SETTLE_PROD` | Dedicated-Agreement CCT applied at monthly level vs daily unit-time-code | CCT populated only at correct unit-time-code; code fix to ENT | 24-00964004 |
| CAR adding **extra tax not on the CCT** | CCT/tax config | Config | 24-00964151 |
| CAR & WAH batch failed on Settle Day running Nov-2023 PPA (E2E) | Process/config during PPA E2E | Config | 24-00968655 |
| STX E2E DEVF **ALR22 Wellhead Purchases** | Report/config | Config | 24-00966931 |
| CAR Processor NGL Settlement; T27D meter differences | CCT/dedication config | Config | 24-00963998, 24-00963343 |
| Daily SettleDay GEN PTR error for MEN/ORL | See §4 | Config + purge | 24-00942763, 24-00940256, 24-00940258 |

**Pattern:** when an ENT/Evolution daily client reports wrong PTR / wrong tax / residue-not-transferring during E2E, the cause is almost always **CCT setup at the wrong unit-time-code (monthly vs daily) or a dedication-agreement config**, not a core-engine bug. Verify the CCT unit-time-code and dedication agreement before escalating. Several of these were dispositioned via **scripts/config delivered to the client for testing** (24-00961958 "Scripts provided to Enterprise via FTP"; 24-00951434/435 Midland Reconfiguration — Min Margin Fees / Birch Offload).

---

## 6. Cluster C — Journal not generating / wrong journal config

Most "journal missing/wrong" cases are **Application Configuration on the Journal Entry Control** screen, not defects.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Journal for a contract/meter **not generating** | A **double condition** existed on the Journal entry for that meter; only one was required | Remove the extra condition | 25-01013216 |
| Journals missing for a CCT# | Journal setup / meter setup detail | Provide correct journal/meter setup | 26-01086172, 25-01011403 |
| **Journal IDs / Journal entries missing** (QQM) | A bad field (**Interconnect**) in the QQM select was breaking the QQM query | Removed Interconnect from the selected fields | 25-01028136 |
| Want data split across cost centers/accounts | Use **Journal Conditions** to filter/refine the data going to each cost center/account | Configuration guidance | 25-01011403 |
| **Cost-center character limit** too short | Column/metadata length | Cost-center character limit increased | 25-01037545 |
| Char-limit discrepancy **CAN vs core** journal tables | CAN columns narrower than US | US & CAN columns set to same char limit | 26-01066044 |
| Custom Journal Entry columns need to move to Web | 2024.10 enhancement (move custom columns to Web) | Config/enhancement | 25-01016226 |
| Journal Entry Control needs GROSS and NET columns | Screen/metadata | Add columns | 23-00898410 |
| Functional-unit journal setup (Pembina) | Journal Entry setup in DEV | ChangeConfig | 23-00883695 |

**Fix recipe:** open **Journal Entry Control** for the affected CCT/meter. Check (a) is there a **condition** at all, (b) is there an **unintended second condition** (25-01013216), (c) for splits use **Journal Conditions** rather than separate setups (25-01011403). For "journal query/IDs missing," check the **QQM query field list** for an invalid field (25-01028136). Cost-center/column truncation → metadata column-length config (25-01037545, 26-01066044).

---

## 7. Cluster D — Journal sign / reversal / tax handling

A distinct **Software Defect** cluster around how the journal treats **negative amounts, reversals, and tax reversals**.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| Journal Transfer file / Journal Entry Report / Journal Query **do not show a net-negative total at account level — defaults to 0** | For the IT line in Journal Entry Control the value type is `IT_VALUE \|\| JOURNAL IT VALUE ADJUSTMENT`; per the IT_VALUE UDEF, **if FEE value < 0 it defaults to 0** | Advised client to change either the value-type or the UDEF so negatives aren't floored to 0 | 23-00903733 |
| `IT_VALUE` journal UDEF also **re-calculates the reversal values**; an IF condition wrongly applies to reversals too (not present with core `DTLFEE` value type) | UDEF reversal-handling defect | Code fix | 22-00693541 / **ADO #1364795** (NRM, Closed) |
| Reversing **taxes not picked up** in the Journal (only product/fee reversals); Journal Entry Log treats tax reversal (-169.92) as an offset | Tax-reversal handling in journal generation | Code fix planned in **Patch 7** (2024.04); duplicate raised as 25-01060004 | 25-01002393, 25-01060004 |
| Missing reversal of original entries for CO&O report fees on WFC PPA Journal | Reversal-generation defect | Addressed in patch | 23-00935001 |
| Journal Formula `IT_VALUE` reversals should not be calculated (older instance) | Same family as #1364795 | Code | 22-00693541 |

> **Key insight:** the recurring journal defect family is **sign/reversal**: (1) negatives floored to 0 because the `IT_VALUE` UDEF has a `FEE<0 → 0` default (23-00903733 — *config* fix on the UDEF/value type), and (2) the `IT_VALUE` UDEF incorrectly recomputing reversal lines (22-00693541/#1364795 — *code* fix); the core `DTLFEE` value type does not have the reversal bug. **Tax reversals** are a separate, later defect (25-01002393, Patch 7). When a client says "the journal/SAP transfer doesn't match the invoice," check whether a **negative or reversal line** is involved first.

---

## 8. Cluster E — Journal batch-process failures

The JOURNAL process itself crashing at a step (distinct from §6/§7 where output is just wrong).

| Step / signature | Root cause | Fix | Case |
|---|---|---|---|
| `JRNTRSPEN1` "Stopped Processing on Error" | Process step error (resourcing/data) | Engineering assist to resolve the step | 25-01005434 |
| Insert into `qstag_journal_fm` fails — **BA is alphanumeric but inserted as `client_id` (NUMBER)** | Proc line ~232: `CASE WHEN ... invoice_transaction_code_ind=1 THEN nvl(ba.usr_custom1, jrn.CTR_PARTY_BA_NO)` — alphanumeric vendor (`10122A`) into a numeric column | Corrected vendor to all-numeric → process completed (data fix; underlying proc assumes numeric BA) | 25-01005434 |
| Journal Entry batch fails at **`JrnVchrRpt`** step | Code that prevents null values had an IF condition that ignored a null-generating case | Code change to **exit the step when the query returns nothing** | 22-00691505 |
| TIPS Journal **Serialization error** | Concurrent writes to the segregated-process pipe for the first two messages | Updated `QInterProcessMessaging` to prevent concurrent writes for the first two pipe messages (logic already existed for subsequent ones) | 22-00561438 |
| Unable to transfer Harmattan PPAs (AltaGas) | Client-specific `QPSJournalTransFM` not initializing `m_pTipsMsgLog` | Software update — initialize `m_pTipsMsgLog` in client-specific `QPSJournalTransFM` | 22-00643237 |
| Plant Journal Summary Report issue | Report change required | Report fix | 22-00598114 |
| Manually-posted plant journals didn't hit the GL | See §16 (process/training) | — | 22-00811087, 22-00811622 |

**Fix recipe:** get the **exact failing step** (JRNTRSPEN1 / JrnVchrRpt / transfer). For `qstag_journal_fm` insert failures, check whether the **BA / vendor is alphanumeric** while being mapped to a numeric `client_id` (25-01005434) — quickest unblock is to make the vendor numeric; the proc assumption is the real defect. Serialization/transfer crashes are code (22-00561438, 22-00643237) — escalate with PQID.

---

## 9. Cluster F — Rate schedule / UDEF / fee & escalation calculation

Pricing/formula calculation defects feeding settlement.

| Issue | Root cause | Fix | Case / code |
|---|---|---|---|
| Rate schedule **simple average wrong when one price is 0** (avg of EP11=0 & TW11=.22 gave .22 not .11) | Simple-average calc ignored the 0 | Modified **`QRateScheduleFormulaCalcsAveSimp`** to include 0's in the simple average | 24-00962942 (`Quorum.TIPS.ClassicBatch/Common/QTipsSettleLib/QRateScheduleFormulaCalcsAveSimp.cpp`; TurboTips: `RateScheduleFormulaCalcsAveSimp.cs`) |
| UDEF **If/Then/Else** with a non-null **IF Round-To-Places** computes the ELSE branch even when THEN is valid | Rounding-field handling in the UDEF engine | Code change | 22-00617662 (related RNs 131487, 132954) |
| **Max Escalation schedule rounding** issue (V17 Web & Classic) | Escalation rounding defect | Defect/code | 24-00970078 |
| **Rate Escalation Process** completed with errors (NRM) | Client `ESUITE_QNRM.QTRAN_ESCALATE_RESULTS.CTR_NO` was wrong type | Set `CTR_NO` to `VARCHAR2(12)` to match core `CTR_NO` columns; process then completes | 24-00941962 |
| Escalations not calcing correctly on 2nd year forward (Meritage) | Escalation calc defect | Defect | 22-00629393 |
| Unable to update **formula-based rate schedules** (2021.04) | Screen/save defect | Defect | 22-00671724 |
| Daily Rate Schedule missing types; Input Prices screen errors | Config/defect | Config / build | 22-00561480, 22-00561476, 22-00468... (Input Prices: 24-00968470 — *client to unlock locked facilities*) |
| Global/Local **User Defined Formula** screen save errors (Web, 2020.03 / 2022.10) | Web screen save defects | Web fixes | 22-00598151, 22-00598150, 24-00970589 |
| Residue settlement / producer's-share value ≠ liq-vol × price | Calc/build | Build required | 22-00603680, 23-00876962 |

**Fix recipe:** reproduce the calc with the client's exact inputs. Simple-average-with-0 and If/Then/Else-rounding are confirmed engine defects with known fixes (24-00962942, 22-00617662). For escalation "completed with errors," check the **client-specific `QTRAN_ESCALATE_RESULTS` table** for a `CTR_NO` type/length mismatch vs the core 12-char standard (24-00941962) — a frequent client-clone schema drift.

---

## 10. Cluster G — Fixed Fuels & UOM mapping

"Fee/fuel/residue not showing on the statement/invoice" is most often a **UOM mapping** problem on the **Fixed Fuels** tab — config, not code.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Field fuel not showing on statements → Wellhead Net Delivered too high → theoretical & settled NGLs too high; residue settlement wrong | **`CTRSHK` UOM on the Fixed Fuels tab mapped to an invalid UOM Class Code** | Re-map CTRSHK to a valid UOM Class Code | 23-00876904, 23-00876962 |
| Demand/metering/DEHY/COMP/BSF fees not populating; rate not pulling through (Opportune) | UOM / rate-schedule mapping; **`MONMDQ` UDEF needed remap to `CTRMDQ` UOM**; gas-analysis consistency between envs | Remap UOM/UDEF; verify gas analysis | 23-00878026, 23-00881064, 23-00884937/938/940, 23-00881121 |
| UOM UDEF creating **duplicates on invoice** (2023.04) | UOM UDEF defect | Defect | 24-00948288 |
| CTRSHK / contractual-UOM mismatch | UOM class mapping | Config | (Fixed-Fuels cluster) |

**Fix recipe:** when a fee/fuel is missing or a settled volume is too high, open the **CCT → Fixed Fuels tab** and verify every UOM there maps to a **valid UOM Class Code**; check the corresponding **UDEF→UOM mapping** (e.g. `MONMDQ`→`CTRMDQ`). Confirm **gas analysis is consistent between environments** (a fee can appear missing in TEST simply because gas analysis differs — 23-00881064). This is the dominant Opportune-cluster fix.

---

## 11. Cluster H — Revenue Override, revenue export & volume tie-out

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| Revenue Override **error / "need services restarted"** (IACX) | App-tier/service issue; **engineering could not determine a direct root cause from logs** | **Restart services** (worked); recommendation = upgrade; capture **TIPS ClassicGUI logs** next time | 24-00951708, 24-00952270 (RCA) |
| Revenue Override `ORA-01013` (timeout) | Query timeout | Service restart | 22-00627530 |
| Override Revenue screen **not showing all results** in Web (2024.10) | Web grid/result defect | Defect | 25-01015459 |
| Copy from Revenue Override takes 30+ min (hourglass) | Performance | See §13 | 23-00922184 (Customer Error/perf) |
| **Double volume** found between settlement vs revenue (ETP, margin calc) | Volume defect | **Software update patched to 2024.04** | 25-00998597 / **ADO #1709416** (ETP, Bug, Closed) |
| **Price not populating on Billing CICO export** for PMA/re-run months (DCP) | Export defect | **Patched, pending QA** | 24-00976340 |
| Fees not populating on Revenue Export for BOLO | Export config/defect | Defect | 22-00700676, 23-00917846 |
| SW Kansas Revenue Transfer to QDOD errored in WEB TEST1 but ok elsewhere | Custom metadata / env | `custom meta` | 23-00906279 |

**Fix recipe:** Revenue Override "error / hang / can't query" is the classic **service-restart** case (24-00951708, 22-00627530) — restart the app services first; it usually clears with no code change, and Engineering often can't root-cause it from logs (so **grab ClassicGUI logs while it's failing**). True data defects (double volume 25-00998597/#1709416; CICO price 24-00976340) get patched — confirm the target build. For "double/6x volume," **rule out upstream allocation** before assuming a revenue bug (see §5 and the Allocations skill).

---

## 12. Cluster I — Contract / CCT / meter timeslice & overlap data fixes

A steady stream of "can't save / can't end-date / wrong record" issues that resolve as **targeted data fixes** for overlapping or orphaned timeslices (often between the **core `SCTRL_*` tables and the client `QRMTIPS`/SEXTN extension tables**).

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Can't create a timeslice for a meter | Timeslice existed in `QRMTIPS` extension table but **not in `SCTRL`**; record had to be deleted from the DB | Delete orphaned extension row | 22-00671090 |
| Allocation/settlement error on a plant; can't update contract meter list | Eff dates on **contract header vs SEXTN/`sextn` TIPS table misaligned** | Correct/align the effective dates | 22-00671049, 22-00513109 |
| Unable to **end-date a User-ID formula** | Formula detail table had **null `mtr_plant_no`** → SQL queried meter with null plant → returned null → couldn't end-date | Script added the data back in | 22-00513095 |
| ETRAN Facility jobs failed (Opportune) | Meter effective-date **overlaps** | Changed meter effective dates to avoid overlaps | 23-00884245 |
| Able to delete a meter from Contract Meter List despite an effective meter split | Validation gap | Defect | 23-00925437 |
| Unable to save new BA / update CCT (notifications) / `ORA-12899` saving new CCT | Notification-event & column-length defects | Multiple fixes | 23-00913426, 23-00908598, 23-00910859, 22-00598150 |
| Contract meter company code not valid for eff dates | Eff-date validation | Defect | 23-00908082 |

**Fix recipe:** for "can't save / can't end-date / wrong record on a meter or CCT," check for **overlapping or orphaned timeslices** between core (`SCTRL_*`) and the client extension tables (`QRMTIPS`, `SEXTN`), and for **null key columns** (e.g. `mtr_plant_no`). The fix is a scoped data script (delete the orphan, align eff dates, or backfill the null key). Always verify-SELECT first.

---

## 13. Cluster J — Performance

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **PRICETOSCH** manual runs take 5+ hours (was ~2h) | Process had no logic to narrow incoming daily rate schedules to those affected by incoming esuite prices → **all** daily rate schedules processed | **Two fixes:** (1) exit early when no esuite prices found (no work to do); (2) **filter daily rate schedules by the distinct production dates from the esuite data** | 23-00923516 / **ADO #1624635, #1625566** (HPE, Closed); earlier #1531452, #1319767 |
| PPA taking 2.5+ hours; PPA volume blowups | PPA volume over recommended limit | **TIPS recommended PPA limit is ~2000 per month**; work around by processing in batches (50 months of PPAs) | 22-00636596, 22-00630797 |
| TIPS **Out of Memory** errors | Large dataset / volume | Batch the work; raise limits | 22-00630797 |
| Settle/copy operations slow (Revenue Override copy 30+ min) | Query/volume | Perf | 23-00922184 |

**Fix recipe:** PRICETOSCH slowness is a known, fixed defect — confirm the build includes #1625566 (filter daily rate schedules by distinct esuite production dates + early exit). For PPA/out-of-memory, keep PPA batches under the **~2000/month** recommended limit.

---

## 14. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1364795** | Bug / **Closed** | NRM — TIPS Journal Formula (IT_VALUE) reversals should not be calculated | §7 | 22-00693541 |
| **#1709416** | Bug / **Closed** | ETP — Double volume found from revenue data | §11 | 25-00998597 |
| **#1625566 / #1624635** | Bug / Incident / **Closed** | HPE — PRICETOSCH job takes 5+ hours | §13 | 23-00923516 |
| **#1531452** | Bug / **Closed** | HPE — PRICETOSCH "Import Esuite Indexes to TIPS" taking 6+ hours | §13 | 22-00263967 |
| **#1319767** | Bug / **Closed** | SCX — PRICETOSCH step erroring on update of `SCTRL_INDEX_PRICE` | §13 | — |
| **#1740190 / #1762200** | Requirement / Task / **Closed** | TIPS CORE & CAN — Query the Journal Entry Control screen (#1725846) | §6 | — |
| **#1735463** | Task / **Closed** | Test Coverage — TIPS Settlement Accounting → Journal → Journal Entry Control | §6 | — |
| **#1669261** | Feature / **Proposed** | TIPS CAN Journal Entry Control | §6 | — |
| **#1413222** | Requirement / **Closed** | IACX — New TIPS QQM Report: Revenue Override Flag Screen & Contract Party | §11 | 21-00209847 |
| **#1355919** | Bug / **Closed** | IAC — TIPS Revenue Override not calculating correctly | §11 | 20-00094218 |
| **#1484412 / #1523362** | Feature / **Closed** | DB fix tax-reversal references / Workflow Event on Invoice Tax Reversal | §7 | — |
| **#1813294** | Bug / **Closed** | WIT — Reallocation of OBA PDA incorrectly showing double volume | §11 (cross-ref allocation) | 26-01103426 |

> Several actionable cases were dispositioned **operationally** (data script / config / FTP'd scripts) with no single product WI: ENT daily-price purge (24-00942763), ENT daily-logic cutoff patch (24-00940258, "Matthew deployed a fix"), Tax-reversal Patch 7 (25-01002393), CICO price patch (24-00976340), simple-avg-with-0 (`QRateScheduleFormulaCalcsAveSimp`, 24-00962942). Confirm exact build/patch in `Quorum.TIPS.ReleaseNotes` when stating fix availability.

---

## 15. Diagnostic SQL

> **Caveat:** TIPS lives in Oracle schemas `ESUITE_QENT` / `ESUITE_Q<CLIENT>` (per-client). Table/column names below are taken from case repro text and code search; **verify against the client schema before scripting**, and always run a verify-SELECT before any DELETE/UPDATE, wrapped in a transaction.

```sql
-- A. Duplicate daily gas-price rows (the UNIQUE_ETRAN_GAS_PRICE_DAILY collision, §4)
SELECT GAS_DAY, MTR_NO, PRICE_TYPE, COUNT(*) dup_ct
FROM   ESUITE_QENT.ETRAN_GAS_PRICE_DAILY
WHERE  PROD_MTH = '<PROD_MTH>'   -- e.g. 6/1/23
GROUP BY GAS_DAY, MTR_NO, PRICE_TYPE
HAVING COUNT(*) > 1;

-- B. Is the daily-logic cutoff set, and are you running a pre-cutoff month? (§4)
--    ENT_DAILY_VOL_LOGIC_CHANGE_DT lives in the client config/parameter table.
SELECT PARM_NM, PARM_VALUE FROM <client config/parameter table>
WHERE  PARM_NM = 'ENT_DAILY_VOL_LOGIC_CHANGE_DT';

-- C. Settle results for a contract / plant / prod month (did residue/fuel transfer?) (§4/§10)
SELECT CTR_NO, PLANT_NO, PROD_MTH, PROD_CD, SETTLE_VOL, SETTLE_VALUE, PTR_QTY
FROM   QTRAN_SETTLE_PROD
WHERE  PLANT_NO = '<PLANT>' AND PROD_MTH = '<PROD_MTH>'
ORDER BY CTR_NO, PROD_CD;

-- D. Escalation-results table column type (the 24-00941962 CTR_NO type drift)
--    CTR_NO should be VARCHAR2(12) to match core; check the client clone.
SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH
FROM   ALL_TAB_COLUMNS
WHERE  TABLE_NAME = 'QTRAN_ESCALATE_RESULTS' AND COLUMN_NAME = 'CTR_NO';

-- E. Orphaned / overlapping meter timeslice: extension vs core (§12)
--    Row in QRMTIPS/SEXTN extension but not in SCTRL = the 22-00671090 pattern.
SELECT * FROM <ESUITE_Q*.SEXTN_*contract/meter table>  WHERE MTR_NO = '<MTR>';
SELECT * FROM SCTRL_<corresponding core table>          WHERE MTR_NO = '<MTR>';

-- F. Null key column blocking a formula end-date (22-00513095)
SELECT * FROM <formula detail table>
WHERE  FORMULA_ID = '<id>' AND MTR_PLANT_NO IS NULL;

-- G. Journal staging rows for a prod month (BA datatype / journal-not-generating, §6/§8)
SELECT CTR_NO, CTR_PARTY_BA_NO, GL_ACCT, COST_CTR, GROSS_AMT, NET_AMT
FROM   QSTAG_JOURNAL_FM
WHERE  PROD_MTH = '<PROD_MTH>'
ORDER BY CTR_NO;
-- Red flag: alphanumeric CTR_PARTY_BA_NO when invoice_transaction_code_ind=1 (client_id is NUMBER) → 25-01005434.

-- H. Find the failing Settle/Journal step + error by Process Queue ID (use SKILL_TIPS_Batch_Processing.md for the exact table)
--    Get PQID from the user (e.g. 14333473), then read the batch message/log for that PQID + step.
```

---

## 16. Expected-Behavior / User-Education FAQ

~96 Training + ~55 Customer-Error cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| "Journal entries not created for one meter" / "Duplicate Journal Entry records" / "Error completing JOURNAL (Cycle 1)" | Customer setup error — check the **Journal Entry Control condition** for that meter (double/missing condition); duplicates usually = duplicate conditions or running a cycle twice | 26-01098245, 26-01083543, 25-01052421, 25-01037705, 25-01015672 |
| "How do I add to / set up Journal Entry Control?" | Training — walk through conditions, value types, cost-center mapping | 25-01039139, 26-01084922, 22-00668435, 26-01069900 |
| "Plant is locked…" when rolling Cycle 1 but picked Cycle 2 as end date | User error rolling cycles — re-roll with correct cycle boundaries | 25-01021705 |
| "Manually posted plant journals didn't hit the GL" / "Post errored / can restart Post Results step?" | Process/training — manual posts still require the **transfer/post** step; POSTRESIMB Post-Results step can be restarted | 22-00811087, 22-00811622, 23-00926456 |
| "Incorrect rate used in Escalation Process" | Customer Error — usually the wrong rate schedule / base year configured, not an engine bug | 26-01087586, 23-00932733 |
| "Gas statement shows negative price/residue for a meter with 0 residue" | Working as designed given the alloc rule / inputs; verify allocation & gas analysis (not a settlement bug) | 25-01028241, 24-00940355 |
| "CHRG fee shows in Settle but not Revenue" / "fee deducted when calc severance tax — where does TIPS look?" | Training — fee-type config & tax-base setup; explain where the deduction is configured | 23-00913809, 22-00824336 |
| "Settlement Calculations / Btu factor / Plant statement" questions, audits, DLL audit, "validation for auditors" | Documentation/education, not defects | 22-00823540, 22-00540316, 25-01017605, 25-01031038 |
| "Need PPA to reprocess due to rate change" / "adjust closed month" | Process/training — PPA path (mind the ~2000/month limit, §13) | 22-00868800, 24-00971241, 22-00866831 |
| "Revenue copy / query screens slow / not responding" | Often volume/perf or transient; restart services / batch the work (§11/§13) | 24-00948854, 23-00922184 |

**Tell-tale it's user/expected:** a journal "missing" because of a missing/double **Journal Entry Control condition**; a "negative/odd" settled value that correctly follows allocation + gas analysis; an escalation using a rate the client themselves configured; a cycle rolled with the wrong boundaries; or an audit/"how does it work" question. Verify the **CCT/Journal-Entry-Control config and upstream allocation/measurement** before treating it as a defect.

---

## 17. Key Code, Processes & Repos

### Processes / batch steps
| Process / step | Purpose | Notes |
|---|---|---|
| **Settle Day / Settle Process** | Core settlement (daily & monthly) | Steps: `SETTLEDAY`, `CFTOOUTVOL`, `GEN PTR`, `PRICETOSCH` |
| **GEN PTR** (`Measurement to GEN PTR`) | Generate plant-thermal-reduction / PTR (daily path) | Fails at SETTLEDAY on `UNIQUE_ETRAN_GAS_PRICE_DAILY` (§4) |
| **CAR / WAH** | Settlement processors (ENT/Evolution) | CCT unit-time-code & dedication-agreement config (§5) |
| **PRICETOSCH** | Import esuite indexes → TIPS / price-to-schedule | Perf fix: filter daily rate schedules by distinct esuite prod dates (§13) |
| **JOURNAL Process** | Build journal entries from settled data | Steps: `JRNTRSPEN1`, `JrnVchrRpt`; staging `QSTAG_JOURNAL_FM` |
| **Journal Transfer** | Build Journal Transfer file → SAP/GL | `QPSJournalTransFM` (client-specific in `<CLIENT>.TIPS.ClassicBatch`) |
| **Rate Escalation Process** | Apply rate escalations | Writes client `QTRAN_ESCALATE_RESULTS` |

### Code locations (confirmed via ADO code search)
| Symbol | Repo / path | Cluster |
|---|---|---|
| `QRateScheduleFormulaCalcsAveSimp` (.cpp/.h) | `Quorum.TIPS.ClassicBatch /Common/QTipsSettleLib/` | §9 simple-avg-with-0 |
| `RateScheduleFormulaCalcsAveSimp.cs` | `Quorum.Tips.TurboTips /…SettleEngine/RateSchedules/` | §9 (TurboTips port) |
| `QPSJournalTransFM` (.cpp/.h) | `ALT.TIPS.ClassicBatch /QPDllTipsJournal/`, `CMP.TIPS.ClassicBatch /QPDllTipsJournalQCMP/` | §8 journal transfer (client-specific) |
| `QPIBS_JOURNAL_FM_ACCT.sql` / `qstag_journal_fm` proc | `<CLIENT>.ESUITE.Database /…/Procedures/` | §6/§8 journal staging |
| `QInterProcessMessaging` | `Quorum.TIPS.*` segregated-process messaging | §8 serialization |
| Journal Entry Control screen | `Quorum.TIPS.Web.Controllers` + `Quorum.TIPS.Metadata` (+ CAN layer) | §6 |

### Repos (see REPO_REFERENCE.md)
- **`Quorum.TIPS.ClassicBatch`** — C++ settle/journal/rate batch (`QTipsSettleLib`, `QPDllTipsJournal`).
- **`Quorum.TIPS.Batch`** — managed batch (statements, transfers).
- **`Quorum.Tips.TurboTips`** — newer C# settle engine (`SettleEngine`).
- **`Quorum.TIPS.Web` / `.Web.Controllers` / `.Metadata`** — Journal Entry Control, Revenue Override, UDEF/rate-schedule screens.
- **`<CLIENT>.TIPS.ClassicBatch / .Database / .Metadata`** and **`<CLIENT>.ESUITE.Database`** — client overrides (ENT, ALT, CMP, NRM, HPE, IAC, ETP…). **Always check the client repo/schema first** — many fixes are client-specific (journal transfer, escalation-results column type, daily-logic cutoff).

---

## 18. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A batch **step** crashes from a code/proc bug, not data: `SELECT INTO` returns >1 row (CFTOOUTVOL, 22-00649145); serialization/pipe concurrency (22-00561438); `m_pTipsMsgLog` not initialized (22-00643237); `JrnVchrRpt` null-handling (22-00691505).
- A **calculation** is provably wrong on correct inputs: simple-average-with-0 (24-00962942), If/Then/Else rounding (22-00617662), max-escalation rounding (24-00970078), `IT_VALUE` reversal recompute (22-00693541/#1364795), tax reversal not picked up (25-01002393 → Patch 7), double volume (25-00998597/#1709416), CICO price (24-00976340).
- Provide: **PQID + failing step + exact ORA/COM error**, client + plant + prod/acctg month, the contract/CCT, and a repro. Confirm fix availability in `Quorum.TIPS.ReleaseNotes` and the linked WI's target build.

**Route to Cloud Ops / handle as Configuration when:**
- **Journal Entry Control** condition missing/doubled, journal split via Journal Conditions, cost-center/column char-limit (25-01013216, 25-01011403, 25-01037545, 26-01066044).
- **CCT setup**: unit-time-code daily-vs-monthly, dedication agreement, Fixed-Fuels **UOM → UOM Class Code** mapping, UDEF→UOM remap (24-00964004, 23-00876904, 23-00878026).
- **ENT daily Settle** dedupe/purge of `ETRAN_GAS_PRICE_DAILY` + confirm the daily-logic cutoff patch; scripts delivered to client for E2E testing (24-00942763, 24-00940256, 24-00961958).
- **Client-clone schema drift** (e.g. `QTRAN_ESCALATE_RESULTS.CTR_NO` should be `VARCHAR2(12)`, 24-00941962) — data/DDL fix in `<CLIENT>.ESUITE.Database`.
- **Data fixes**: orphaned/overlapping meter timeslices (core `SCTRL_*` vs `QRMTIPS`/`SEXTN`), null key columns, eff-date overlaps (22-00671090, 22-00671049, 22-00513095, 23-00884245). Always verify-SELECT in a transaction.

**Handle as Training / Expected behavior (no fix):** see §16 — missing/double Journal Entry Control conditions, cycle-roll mistakes, manual-post→transfer steps, audit/"how does it work" questions, and "wrong number" cases that correctly follow allocation/gas-analysis (verify upstream first).

**Service-restart first (no code):** Revenue Override "error / can't query / ORA-01013 / hang" — restart app services; capture **TIPS ClassicGUI logs** while failing (Engineering often can't root-cause from existing logs) (24-00951708, 22-00627530).

---

*Skill created: 2026-06-11.*
*Based on: 577 closed TIPS Settlement/Revenue/Journal SF cases — 122 actionable (Software Defect 76 + Application Configuration 32 + ChangeConfig 14) mined for fix recipes, plus ~60 Training/Customer-Error cases for the FAQ. ADO work items #1364795, #1709416, #1625566/#1624635, #1531452, #1319767, #1740190/#1762200, #1735463, #1669261, #1413222, #1355919, #1484412/#1523362, #1813294.*
*Companion: SKILL_TIPS_Allocations_PPA_Imbalance.md, SKILL_TIPS_Invoice_Billing_Rates.md, SKILL_TIPS_Batch_Processing.md, SKILL_TIPS_Reporting_Statements.md, SKILL_TIPS_Master_Data_Contracts.md, REPO_REFERENCE.md.*
