# SKILL: QPTM Billing, Invoicing & Rates Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-01 | **Product:** QPTM (My Quorum Gas Pipeline)
**Scope:** Invoice generation (BLINVGEN/BLINVGEN1), billing batch failures (PANIGHTLY/closeout/month roll), invoice amount/charge correctness (rounding, mismatch, over/under-bill, charge not applied), PPA / cashout / true-up, rate application & Rate Maintenance (TOC/TOS/Index/orphan rates), Statement of Account (BLSOAIMP) & payment import, Chart of Accounts & billing exports (CIS/PeopleSoft/XML), invoice presentation & reports (BLR_00, penalty reports), invoice group / invoice ID numbering, accounting month close, tax/GST/surcharge.
**Companion skills:** Nomination/MDQ/imbalance volumes → **SKILL_Nominations.md**; cycle deadlines → **SKILL_EDI_Troubleshooting.md**; capacity-release billing crossover → **SKILL_Capacity_Release.md** (TT/PPA on releases noted below).

> Evidence base: ~191 actionable QPTM Billing + Invoice Generation + Rates SF cases (Root Cause = Software Defect / Application Configuration / Performance / Packaging) plus Customer Error / Training cases for the Expected-Behavior section. Every root-cause claim cites a real SF case number and/or ADO work item. **Categories folded in:** `Billing` (116 actionable), `Rates` (48), `Invoice Generation` (27) — clusters overlapped heavily (Rate config drives invoice amounts; Invoice Generation = BLINVGEN/BLSOAIMP, same engine as Billing), so folding was worthwhile. Each row notes its source: `[Bill]` / `[Rate]` / `[InvG]`.

---

## TABLE OF CONTENTS

1. [Quick Triage Checklist](#1-quick-triage-checklist)
2. [Billing Concepts & Pipeline](#2-billing-concepts--pipeline)
3. [Symptom → Root-Cause Matrix](#3-symptom--root-cause-matrix)
4. [Invoice/Billing Batch Failure (BLINVGEN/PANIGHTLY) — HIGH FREQUENCY](#4-invoicebilling-batch-failure-blinvgenpanightly--high-frequency)
5. [Rate Application / Rate Maintenance / Orphan Rates](#5-rate-application--rate-maintenance--orphan-rates)
6. [Invoice Presentation & Reports](#6-invoice-presentation--reports)
7. [Charge / Amount Wrong (rounding, mismatch, over/under-bill)](#7-charge--amount-wrong-rounding-mismatch-overunder-bill)
8. [PPA / Cashout / True-Up](#8-ppa--cashout--true-up)
9. [Statement of Account / BLSOAIMP / Payment Import](#9-statement-of-account--blsoaimp--payment-import)
10. [Chart of Accounts & Billing Exports (CIS / PeopleSoft / XML)](#10-chart-of-accounts--billing-exports-cis--peoplesoft--xml)
11. [Accounting Month Close / Bill Roll](#11-accounting-month-close--bill-roll)
12. [Invoice Group / Invoice ID / Numbering](#12-invoice-group--invoice-id--numbering)
13. [Tax / GST / Regulatory Surcharge](#13-tax--gst--regulatory-surcharge)
14. [Verbatim Fix Scripts (redacted)](#14-verbatim-fix-scripts-redacted)
15. [Key Code Files, Batch Processes & Repos](#15-key-code-files-batch-processes--repos)
16. [Database Tables Reference](#16-database-tables-reference)
17. [Diagnostic SQL Queries](#17-diagnostic-sql-queries)
18. [Known Historical ADO Bugs](#18-known-historical-ado-bugs)
19. [Expected Behavior / User Education](#19-expected-behavior--user-education)
20. [Escalation Decision Tree](#20-escalation-decision-tree)

---

## 1. Quick Triage Checklist

```
[ ] 1. What EXACTLY failed — a batch process (BLINVGEN/BLINVGEN1/PANIGHTLY/month-roll), an amount that is wrong,
       a rate, an invoice that won't render, or a payment import (BLSOAIMP)?
[ ] 2. Which TSP_NO and which Contract (K#) / Invoice Group / Business Associate (BP_NO)?
[ ] 3. Which Accounting Month / Production Month? Is the month OPEN or already rolled/closed?
[ ] 4. The PQID(s) of the failing batch run (clients usually supply these for BLINVGEN failures)?
[ ] 5. Is there a hard deadline (FERC pipe-close, invoice-send date)? Many billing cases are CRITICAL/time-boxed.
[ ] 6. Web (MyQuorum/CommPass) or Classic (Citrix)? Several invoice/rate-screen bugs are Web-only or Classic-only.
[ ] 7. Internal or External (shipper/CommPass) user? Report access & invoice visibility differ.
[ ] 8. Is the exact error text a "System Error" / "ERROR SETTING VALUE FOR COLUMN ... FOR PRIMARY TABLE
       BLTRAN_INVOICE_INPUT"? → almost always a maxed-out SEQUENCE (see §4).
[ ] 9. Rate-driven? Did anyone recently time-slice / edit / delete a Rate ID, or run a TSP copy? (→ orphan rates §5, false PPAs §8)
[ ] 10. QPTM version (2019.05, 2021.10, 2022.10, 2024.04, 2024.10) — many fixes are version-gated / delivered as hotfixes.
```

### Where does the issue live?
| Symptom | Cluster | First place to look |
|---------|---------|---------------------|
| BLINVGEN/BLINVGEN1/PANIGHTLY/closeout fails or stalls | §4 | PQID error text; `BLTRAN_INVOICE_INPUT`; sequence values |
| "out by one cent" / header≠detail / SOA≠Summary | §7 | rounded-vs-unrounded tax summing (BLR_00) |
| Charge missing / over-billed / tripled / not applied | §7, §5 | TOC/TOS setup, rate detail, child-contract release |
| Rate wrong / Rate Maint won't save / orphan rate errors | §5 | `RTCTRL_RATE_HDR` / `RTCTRL_RATE_DTL` join |
| Invoice blank / cut off / report no data | §6 | report params, external-user access, v17 cutover |
| Payment not applied / SOA import | §9 | BLSOAIMP csv format, multi-row, multi-BA |
| Export (CIS/PeopleSoft/XML) warning/fail | §10 | `BLTRAN_*` export tables, Chart of Accounts |
| Month won't close / closed wrong months | §11 | bill-roll params, bit/closing table |
| PPA created / reversed / $0 cashout | §8 | PPA generation, rate cashout setup, cache |

---

## 2. Billing Concepts & Pipeline

### The billing/invoicing pipeline (typical monthly close)
```
[Volumes scheduled/allocated]  (Nominations/Allocations — other skills)
   ↓
PANIGHTLY  → nightly aggregation incl. a Billing/Invoice step (charge-basis volumes, Cap-Rels, tax)
   ↓
BLINVGEN / BLINVGEN1  → Invoice Generation batch: resolves Rate → TOC/TOS → charge amounts,
   writes BLTRAN_INVOICE_INPUT, builds the invoice & Statement of Account
   ↓
BLR_00 (Invoice Document) / BLSOAIMP (Statement of Account import & payments)
   ↓
Bill Roll / Accounting Month Close  → locks the production/accounting month
```
- **BLINVGEN vs BLINVGEN1:** clients run both; `BLINVGEN1` is a second/variant invoice-generation pass (`BLINVGEN1S` seen for HEP/Midship). Failures in either block month closeout ([Bill] 23-00931079, 24-00944247).
- **Rate → TOC → TOS chain:** a *Rate ID* (`RTCTRL_RATE_HDR/_DTL`) carries the price; it is associated to a **Type of Charge (TOC)** and resolved per **Type of Service (TOS)**. A broken link anywhere = "TOS not Billing" / "AOR not billing" / "Reservation Charge Not Displaying" ([Rate] 25-01007586, [Bill] 23-00932753, [InvG] 24-00969310).
- **PPA = Prior Period Adjustment** (true-up/restatement). Generated when something in a *closed* month changes (rate time-slice, amendment, measurement, cashout). Approved PPAs bill; unapproved ones drop on month close ([Bill] 22-00693332).
- **Cashout** = monetizing an imbalance using a cashout rate; a $0 / wrong cashout rate is a config/rate problem ([Bill] 23-00930770, ADO #1644043).

### Key terms
| Term | Meaning |
|------|---------|
| TOC | Type of Charge (Reservation, Usage, Overrun, Penalty, Lump Sum, Fuel, Cashout, Flex, Interest…) |
| TOS | Type of Service (FTS, ITS, FSS, PAL/ISS, etc.) |
| AOR / UOR | Authorized / Unauthorized Overrun (penalty quantities & charges) |
| OBA | Operational Balancing Agreement (imbalance) — surfaces on invoices/OBA reports |
| Invoice Group | Grouping of contracts billed together under one invoice ID |
| Bill Roll | Accounting-month close/advance process |

---

## 3. Symptom → Root-Cause Matrix

| Symptom (message / behavior) | Most common root cause | Fix type | Evidence |
|------------------------------|------------------------|----------|----------|
| BLINVGEN fails: "ERROR SETTING VALUE FOR COLUMN INVOICE_INPUT_ID / ALLOC_PTR_VOL_QTY FOR PRIMARY TABLE BLTRAN_INVOICE_INPUT" | **Sequence maxed out**; needs reseed + purge report table | Data script (reseed/purge) + monitoring | [Bill] 23-00908498/24-00942047, [InvG] 24-00957495, ADO #1665295/#1607556 |
| BLINVGEN "fails without errors" / stalls / hangs / runs for hours | Maxed sequence, registered-SQL defect, or perf (long header insert) | Data script / code fix / infra | [Bill] 24-00945534, 22-00692658, 22-00620272; [InvG] 24-00974766; ADO #1733048,#1747979,#1773883 |
| CANOMCLTG / billing erroring "for all pipes"; "weird"/random CAS errors; QPTM slow | **Orphan rate detail rows** (`RTCTRL_RATE_DTL` with no matching `_HDR`) | Data script (end-date/delete orphans) | [Rate] 25-01044370/25-01044614/25-01044914, ADO #1756911 |
| Invoice header total ≠ invoice detail total ("out by one cent"); SOA page ≠ Invoice Summary page | **Rounded vs unrounded tax summed inconsistently** in BLR_00 | Code fix | [Bill] 22-00823331, 22-00830838 |
| Charge tripled / over- / under-billed; AOR/UOR wrong; reservation not billing | Rate detail or TOC/TOS association wrong; child-contract release setup | Config (mostly) / code | [Rate] 23-00929118; [Bill] 24-00943252, 23-00932753; [InvG] 24-00969310 |
| Rate Maintenance (Web) won't save / shows pencil/edit; missing TOS validation; decimals | Web rate-grid defects | Code fix | [Rate] 22-00818463, 22-00712293, 22-00534204, 23-00884941 |
| Rate ID not incrementing / can't create Rate ID | Identity/sequence defect on rate header | Data script / code | [Rate] 22-00536964, 25-01017593 |
| PPAs generated that shouldn't exist (after rate time-slice / amendment) | PPA-trigger fires on immaterial end-date change | Code fix; workaround = leave unapproved | [Bill] 22-00693332, [InvG] 24-00973258 |
| PPA cashout returns $0 / wrong rate | Cashout rate setup / TOC config | Config / code | [Bill] 23-00930770, ADO #1644043 |
| Invoice / customer invoice report returns blank (esp. after v17 cutover, or assigned-away contracts) | Report data/access config post-upgrade | Config | [Bill] 23-00907163, 23-00901000, 23-00922003 |
| BLSOAIMP not importing/applying payment; only first BA/first row | CSV multi-row / multi-BA handling defect | Code fix | [InvG] 24-00987963, [Customer] 24-00982684, ADO #1696922 |
| Account # / Billing Party cut off on invoice; field won't take leading-0 / 6 decimals | Invoice template field width / validation | Code/config | [Bill] 22-00609180, 22-00615068, 23-00931973 |
| Month won't close / closes months not requested / reruns need month reopened | Bill-roll parameter or closing-bit table defect | Code/config + data | [Bill] 22-00692668, 22-00563733; [InvG] 25-01061995, 25-01020141 |
| GST off by cents after backdated exemption; GST on cap-rel+PPA | Tax recalc on amendment/exemption | Code/config | [InvG] 24-00961168, [Bill] 22-00601168 |
| LPS/PAL PPA fully processed (PAN "processed", balance updated) but **no billing adjustment** (invoice Adj = 0); batch throws SQL 208 `Invalid object name 'BLSTAG_PAL_EXT'` | **CORE schema/code mismatch** — build 3.1.00.0069 dropped `BLSTAG_PAL_EXT` while the CORE reader still joins it (config gate defaults TRUE) | Ops DDL deploy (script object from DEV/DTE) + rerun PPAs + reverse manual LGAs — §4.4 | [InvG] 26-01106039, ADO #1836277 / WI #1836679 |

---

## 4. Invoice/Billing Batch Failure (BLINVGEN/PANIGHTLY) — HIGH FREQUENCY

This is the **single largest actionable cluster (37 cases; 30 Billing, 5 InvGen, 2 Rates)** and the most operationally urgent — these arrive **CRITICAL with a FERC / pipe-close deadline** ("we have a FERC deadline to close a pipe today" — [InvG] 24-00957495).

### 4.1 The canonical failure: maxed-out sequence
**Symptom:** BLINVGEN aborts with a generic **"System Error"** and:
> `ERROR SETTING VALUE FOR COLUMN INVOICE_INPUT_ID FOR PRIMARY TABLE BLTRAN_INVOICE_INPUT`
> (variant: `... COLUMN ALLOC_PTR_VOL_QTY FOR PRIMARY TABLE BLTRAN_INVOICE_INPUT`)

**Root cause:** the identity/sequence feeding `BLTRAN_INVOICE_INPUT` (e.g., `INVOICE_INPUT_ID`) **maxed out**, with **no prior notification**. Confirmed across TIGT (TSP 302) and others.
**Fix (what L4/Cloud Ops actually does):** *"Update archive definition and script required to reseed sequence / purge report table"* ([InvG] 24-00957495 resolution). The RCA cases asked specifically *"why the sequence values maxed without receiving a notification prior"* ([Bill] 23-00908498). Pair the reseed with **archiving/purging the bloated report/input table** and **add monitoring** so it does not recur ([Bill] 22-00519725 "Tracking max sequence values in QPTM").
**ADO:** #1665295 (TEP/TIGT, Closed), #1607556 (23-00907641 RCA, Closed). See §14 for the sequence-reseed pattern.

### 4.2 Other BLINVGEN failure modes
| Variant | Cause | Fix | Evidence |
|---------|-------|-----|----------|
| "BLINVGEN stopping on error for invoice document" (HEP/Midship 610, HPE 17) | Data/registered-SQL specific to a contract/invoice | Code fix / hotfix | ADO #1733048, #1773883 |
| "Registered SQL Error" (DSU) | Defective registered SQL in invoice gen | Code fix | ADO #1747979 / #1748166 |
| "BLINVGEN process errors out with Invalid Parameter Exception" / "during formula price calculation" (ENT) | Formula-price calc / parameter defect | Code fix (Active/Proposed) | ADO #1806153, #1806551, #1807698 |
| "Rate Resolution Errors" in BLINVGEN | Rate→TOC link missing for a contract (often after TSP copy / segmentation) | Config (fix rate/TOC) | [InvG] 26-01090579, [Bill] 24-00940484 |
| "rate error query taking 2 hours" | Perf on the rate-error validation query | Perf code fix | [InvG] 24-00974766 |
| PANIGHTLY fails at billing step / stalls / "Identify Error PANIGHTLY" | Billing sub-step error (often the same sequence/rate issue) | Per root cause | [Bill] 22-00530972, 22-00686159, 23-00914791 |
| CR Seasonal Date Issue for BLINVGEN (REX 501) | Capacity-release seasonal-date defect | Code fix | ADO #1700620 |
| "Billing Process Fails on Tax Presentation step with dll Error" | Packaging/DB-script (missing object) | Services/packaging | [Bill] 22-00821018 |
| SQL 208 `Invalid object name 'BLSTAG_PAL_EXT'` in `QSQLID_INS_SEL_INVOICE_DOC_PAL_DAY` → "PAL statement records were not successfully inserted." | CORE reader joins a table dropped by build 3.1.00.0069 | Ops DDL deploy → **§4.4** | [InvG] 26-01106039, ADO #1836277 |

### 4.3 Investigation steps
1. Get the **PQID(s)** and the exact error string from the process queue.
2. If the string is the `BLTRAN_INVOICE_INPUT` "ERROR SETTING VALUE FOR COLUMN…" → go straight to the **sequence check** (§17-D). Reseed + purge (§14).
3. If "Rate Resolution" / formula price → check the contract's Rate→TOC→TOS chain (§5, §17-B/C).
4. If a slow/hung run → check for the long header-insert / oversized input table (archive/purge), not necessarily a code bug.
5. Confirm whether the **accounting month is still open** — closeout can't proceed until the run succeeds.
6. If the error is SQL 208 `Invalid object name 'BLSTAG_PAL_EXT'` (LPS/PAL statements) → **§4.4** — schema/code mismatch, not data or config.

### 4.4 PAL/LPS daily statement crash: SQL 208 `Invalid object name 'BLSTAG_PAL_EXT'` (CORE schema/code mismatch)
**Symptom:** an LPS (Park-and-Loan, TOS **LPS-F**) PPA completes the *entire* lifecycle — retro nom error → reallocation → PPA event (`BLTRAN_PPA_EVENT`) → PAN/PANIGHTLY "processed" → Customer Account Main shows the revised balance — but **no billing adjustment is generated** (invoice Adj = 0). BLINVGEN "Run All PPAs" (Generate Documents step; the PANIGHTLY chain is equally exposed at its BLINVGEN step) crashes in registered SQL **`QSQLID_INS_SEL_INVOICE_DOC_PAL_DAY`**:
> `Invalid object name 'BLSTAG_PAL_EXT'` (SQL 208 / SQLState 42S02)
> → "PAL statement records were not successfully inserted." → "CreateNewData function failed." *(cascade — the SQL 208 is the cause)*

**Root cause** [CONFIRMED — [InvG] 26-01106039 L4, live source reads 2026-08-14]: CORE `QPSGenerateDocuments.cpp` (`Quorum.QPTM.ClassicBatch /QPDllPipelineMgrBL/`, L616–636) string-injects `LEFT OUTER JOIN BLSTAG_PAL_EXT` into the PAL daily invoice-doc insert whenever config `BILLING/USE_DTE_BLRPTS_10_INVOICE_DOC_PAL` is true — and the **missing-key default is TRUE** (L200–201) — while QPTM build **3.1.00.0069** drop scripts (ST# 50950/50552, issue 62349, `Quorum.QDBManager`) removed `BLSTAG_PAL_EXT` from the CORE schema. **No CREATE DDL survives in any repo.** The writer (`CalcPALExtension`) exists only in DTE/QLNG repos → **every non-DTE instance on 0069+ with PAL statements configured is exposed** (EQC hit it: ADO Bug #1836277). Second gate: TSP config key `INV_DOC_PAL_STMT` = DAY.

**Fix recipe (ops DDL deploy — no code build; WI #1836679 DEV precedent):**
1. **Script `BLSTAG_PAL_EXT` from an instance that has it** (e.g., a DEV fixed earlier, or any DTE instance) — ⚠️ do **not** hand-build the DDL from column lists — and create it in each affected environment.
2. Rerun BLINVGEN **"Run All PPAs"** for all affected production months; expect `CHARGE_BASIS_CD='PEX'` (PAL Extension) rows to appear in `BLTRAN_INVOICE_GEN_QTY`.
3. **Reverse any manual LGA workaround entries** for the same periods (avoid double-billing).
4. An **empty** table is a complete fix for non-DTE clients: the join is LEFT OUTER and only reads `EXT_DAY_COUNT` → NULL, byte-identical to the config-false branch output.

**Verify:** `SELECT OBJECT_ID('dbo.BLSTAG_PAL_EXT')` NULL → non-NULL; rerun completes without SQL 208; PEX rows appear (§17-G).
⚠️ **Drift risk:** the 0069 drop script is guarded/idempotent — any future QDBManager 3.1.00 baseline re-run **silently re-drops** the restored table. The permanent fix must land in CORE (Bug #1836277: restore the CREATE DDL to the DB baseline, or flip the missing-key default to false — the code guard alone does NOT fix clients whose key is explicitly true).
**Do NOT:** flip `USE_DTE_BLRPTS_10_INVOICE_DOC_PAL=false` as a "fix" (silently changes the billing code path and leaves the CORE trap latent), or delete the CORE join (breaks DTE/QLNG PAL day-count — Issue 197521 / Bug #1638997 territory).
**Evidence:** [InvG] 26-01106039 (EQC/EQT, TSP 24/241, contract LPS 1269.2278, invoice 260675 Adj=0; predecessor 25-01058356); ADO Bug **#1836277** (open, **no fixed-in version** as of 2026-08-14), WI **#1836679** (DEV object insert = differential proof: repro → non-repro with zero code/data change), WI #1836447 (PRD-source missing), WI #1451380 (CORE base table + PK), Bug #1638997 (same path works at DTE with the object present).

---

## 5. Rate Application / Rate Maintenance / Orphan Rates

Largest *Rates*-sourced cluster (36 cases, mostly `[Rate]`). Two recurring failure modes: (a) **orphan rate data** that breaks billing/CAS for the whole pipe; (b) **Rate Maintenance Web screen** defects.

### 5.1 Orphan rate detail rows (HIGH IMPACT — breaks ALL pipes)
**Symptom:** sudden system-wide slowness, **random "weird" CAS errors**, `CANOMCLTG` (or BLINVGEN) erroring **for all pipes** ([Rate] 25-01044370). Root cause confirmed as **orphaned `RTCTRL_RATE_DTL` rows** — detail rows whose `RATE_HDR_ID` + effective dates have **no matching `RTCTRL_RATE_HDR`** parent (left behind by a rate time-slice/delete/edit, often during a TSP copy).
**Detect:** LEFT JOIN `RTCTRL_RATE_DTL` → `RTCTRL_RATE_HDR` on `TSP_NO + RATE_HDR_ID + EFF_DT_FROM + EFF_DT_TO`, keep rows where the header is `NULL` (§17-E / §14 verbatim).
**Fix:** either **end-date** the orphan detail (`SET EFF_DT_TO = <month-end>`) or **DELETE** the orphan `RATE_DTL_ID`s, inside a `BEGIN TRANSACTION` with before/after verify SELECTs (verbatim script in §14, from ADO **#1756911**). Recurs enough that clients open **"Monitor Orphan Rate Issues in PRD"** ([Rate] 25-01044914).

### 5.2 Rate Maintenance (Web/Classic) defects
| Issue | Root cause | Fix | Evidence |
|-------|-----------|-----|----------|
| Web Rate Matrix doesn't save, rows stuck in edit (pencil) | Web rate-grid save defect | Code fix | [Rate] 22-00818463 |
| Missing TOS / TOC validation on rate save | Web validation gap | Code fix | [Rate] 22-00712293, 22-00534204 |
| Can't modify TOC to accept 6 decimals; decimal formatting missing | Decimal precision defect | Code fix / config | [Rate] 23-00884941, 23-00908131 |
| Effective-Date-Gap validation blocks *intentional* discontiguous rates | Over-strict validation | Code fix | [Rate] 22-00693350 |
| Rate ID not incrementing / can't create Rate ID | Rate-header identity defect | Data script / code | [Rate] 22-00536964, 25-01017593 |
| Update Rate from Discount→Negotiated errors; Rate ID/TOS error | Rate-type/TOS config | Config | [Rate] 25-01040363, 25-01022452 |
| Rate "tripled" on child-contract Flex charges | Rate detail / release setup | Code fix | [Rate] 23-00929118 |
| Index Maintenance: missing Actions, sort order ≠ Classic | Web index-screen defects | Code/config | [Rate] 23-00903754, 22-00818474 |
| Index-price feeds (Platts/DATAPUB) not updating | Batch feed failure | Code fix / infra | [Rate] 22-00543162, 22-00586318 |
| Rate Maint Lock (can't edit) | Stuck lock / concurrency | Doc/clear lock | [Rate] 25-01025106 |

### 5.3 Charge config not billing
"FSS Contract not billing Reservation Rate", "TOS not Billing", "AOR not billing on TPC lease", "Reservation Charge not displaying", "charge a fuel rate by Transaction Type", "Path Overrun TOC via RFS" — almost all **Application Configuration**: a missing/incorrect TOC↔TOS↔Rate association or charge-basis. Fix in Rate Maintenance + TOC/TOS setup ([Rate] 26-01102601, 25-01007586; [Bill] 23-00932753; [InvG] 24-00969310; [Rate] 24-00952068, 22-00832274).

---

## 6. Invoice Presentation & Reports

Second-largest cluster (29 cases). Mostly invoice **document/report** rendering, not amount math.

| Issue | Root cause | Fix | Evidence |
|-------|-----------|-----|----------|
| Customer Invoice report / Invoice Documents return **blank** (esp. after v17 cutover) | Report data/template/access config post-upgrade | Config / workaround | [Bill] 23-00901000, 23-00907163, 22-00638259 |
| Contracts that are **assigned away** produce blank invoices | Assignment/contract-link config | Config | [Bill] 23-00922003 |
| Account # / Billing Party / Whistler Account ID **cut off** on invoice | Template field width | Code fix | [Bill] 22-00609180, 22-00615068, 22-00559327 |
| ABA / Wire number won't keep **leading 0** | Field type defect | Code fix | [Bill] 23-00931973 |
| Penalty reports (5.1/5.2/5.3, OFO) no data / external-user can't run / wrong aggregation | Report params, external access, aggregation defect | Code/config | [Bill] 24-00938066, 24-00939267, 24-00938356, 24-00940437 |
| BLR_00 / Billing Voucher report errors or must run twice | Report defect | Code fix | [Bill] 23-00889568, 22-00638284, 22-00603591 |
| OBA Imbalance Letter (RPT_IN53) stops with error | Report perf/defect | Code fix | [Bill] 22-00586322 |
| PDF report not executing; report runtime longer in v17 | Report engine/perf | Code fix | [Bill] 22-00808432, 22-00638259 |
| Missing column (Cap Rels Charge Type) on Invoice Sub-detail | Report column config | Code fix | [Bill] 22-00638283 |
| Invoice cover-page logos distorted | Template image config | Config | [InvG] 25-01021500 |

**Investigation:** confirm Web vs Classic, internal vs external user, and whether the client just upgraded (v17/2024.x) — a large share are post-cutover report-config regressions. Reproduce with the client's exact report parameters.

---

## 7. Charge / Amount Wrong (rounding, mismatch, over/under-bill)

### 7.1 The "out by one cent" / SOA-vs-Summary mismatch (recurring defect)
**Symptom:** invoice **header total ≠ detail total** by a cent ([Bill] 22-00823331, recurred Jul/Oct 2021), or the **Statement of Account page total ≠ Invoice Summary page total** on BLR_00 ([Bill] 22-00830838, every HPL/191 invoice).
**Root cause:** **tax amounts summed inconsistently** — one page sums **unrounded** taxes, the other sums **rounded** taxes; the delta = total-unrounded minus total-rounded tax. Rerunning invoice generation does **not** fix it.
**Fix:** code change so both pages sum the **same** (rounded) tax basis. Related rounding features: ADO **#1472782 / #1490712 / #1472846** ("Invoice Rounding", "PF Invoice Rounding"). Also [Rate] 25-01009658 (invoice billing rounding), [Rate] 24-00950483 (lump-sum fixed-price rounding), [Bill] 22-00630588 (charge-basis not rounding to whole number).

### 7.2 Over/under-bill & charge-not-applied
| Issue | Root cause | Fix | Evidence |
|-------|-----------|-----|----------|
| AOR/UOR bill quantity wrong; AOR not billing on lease | Penalty-qty calc / TOC setup (often TPC/Evolution conversion) | Config / code | [Bill] 24-00943252, 23-00932753; [Rate] 24-00951915 |
| Overrun not billed on a new contract | Overrun TOC/rate not on new K | Config / code | [Bill] 22-00607033, [InvG] 23-00927111 |
| Usage History / Supply Scheduling charge wrong | Charge picks up other inventory accounts' cashout activity | Code fix | [Bill] 22-00563700, 22-00563656 |
| Tiered billing wrong when different rates/tiers same day | Tier-resolution defect | Code/non-software | [Bill] 22-00661789 |
| Reservation calc with date-splits; incremental reservation | Date-split reservation calc | Config / workaround | [Rate] 23-00933403, 24-00994714 |
| DTE IBS PAL extension-fee count error | Fee-counter defect | Perf/code fix | [Bill] 23-00935776, [InvG] 24-00949319 |
| Inventory adjustments not netting to zero | Adjustment calc | Code fix | [Bill] 22-00693306 |

**Approach:** isolate the single charge line; trace **Rate ID → TOC → TOS → charge basis → quantity source**. For TPC/Evolution/TREX conversion projects, most "wrong amount" cases are **config** (segmentation, lease/AOR setup) not code.

---

## 8. PPA / Cashout / True-Up

PPA = Prior Period Adjustment (restatement of a closed month).

| Issue | Root cause | Fix | Evidence |
|-------|-----------|-----|----------|
| **PPAs created that shouldn't exist** after a rate time-slice (882 spurious events when end-dating a closed rate with no material change) | PPA-trigger fires on immaterial end-date change | Code fix; **workaround = leave the PPAs unapproved → they drop on month close** | [Bill] 22-00693332 |
| Contract's PPAs **reverse all charges without restating** (recurs monthly, started after Azure migration); fixed by resetting middle-tier cache + reprocessing | Suspected **cache** defect | Workaround (cache reset) confirmed by engineering | [InvG] 24-00973258 |
| **PPA Cashout returns $0 / wrong rate** | Cashout rate / TOC setup | Config / code | [Bill] 23-00930770 |
| "PPA Cashouts sometimes don't work" | Cashout calc defect | Code fix (Closed) | ADO #1644043 (23-00936358) |
| PPA not showing on invoice / not processing for UoM change | PPA→invoice link / unit-of-measure | Code/workaround | [Bill] 22-00530921, 22-00591476 |
| Measurement PPAs not triggering reallocation records | Measurement-PPA→realloc defect | Code fix | [Bill] 22-00603614 |
| Lump-Sum report doubling on PPA | Report dedup defect | Code fix | [Bill] 23-00936257 |
| TPC tiered cashouts failing | Cashout config | Config | [Rate] 24-00942058 |
| **LPS-F PPA processed but no billing adjustment** (lifecycle completes, PAN "processed", invoice Adj = 0) | Not a PPA defect — the PAL daily invoice-doc insert crashes downstream (missing `BLSTAG_PAL_EXT`, **§4.4**) | Ops DDL deploy + rerun "Run All PPAs" + reverse manual LGAs | [InvG] 26-01106039, ADO #1836277 |

**Rule of thumb:** if a PPA appears after a *closed-month rate/amendment edit* and the change was immaterial, it is usually the **spurious-PPA defect** — tell the client to **leave it unapproved** and it will not bill. If charges *reverse and don't restate*, suspect **middle-tier cache** (reset cache + reprocess).

---

## 9. Statement of Account / BLSOAIMP / Payment Import

**BLSOAIMP** imports a Statement of Account / payment CSV and applies payments to invoices.

| Issue | Root cause | Fix | Evidence |
|-------|-----------|-----|----------|
| Payment file with **multiple rows** only applies some payments (e.g., two Aug payments skipped) | CSV **multi-row import** not supported | Code change to allow multiple rows per file | [InvG] 24-00987963, ADO #1696922 |
| Payment import only applies to the **first Business Associate** | Multi-BA handling defect | Code fix | 24-00982684 |
| BLSOAIMP not importing / "resulting in warning" / not applying | CSV format / mapping / table-clear | Config / code | [InvG] 24-00950442, 24-00957583 |
| Request to **clear the SOA table on import** (stale rows accumulate) | No truncate-on-import | Code change | [InvG] 24-00988410 |
| SOA page formatting changes | Report/template | Code fix | [Bill] 23-00920922 |

**Investigation:** get the client's exact CSV; check row count, BA count, date columns, and whether prior import rows were cleared. Many BLSOAIMP cases are **data-shape-specific** — reproduce with their file.

---

## 10. Chart of Accounts & Billing Exports (CIS / PeopleSoft / XML)

Outbound integration of billed amounts to the client's GL/AR.

| Issue | Root cause | Fix | Evidence |
|-------|-----------|-----|----------|
| Chart of Accounts **PK error** (Web & Classic) | Duplicate/identity on COA | Config | [Bill] 23-00906508 |
| COA detail rows don't update end-date when header is time-sliced | Time-slice cascade defect | Code fix | [Bill] 22-00823332 |
| Intercompany/Affiliates show in Classic COA but not Web | Web COA rendering | Code fix | [Bill] 24-00939817 |
| CIS / CIS+ / PeopleSoft billing export warning or wrong PPA invoice id | Export mapping / PPA-id resolution defect | Code fix | [Bill] 23-00888639, 22-00570072/22-00570193, 22-00563725, 22-00825211 |
| XML load fails / file error (e.g., TSP 20072) | Export XML format/data | Code fix | [Bill] 22-00825285, 22-00694694 |
| CMX invoice export — edited text in XML | Export config | Config | [Bill] 23-00906571 |

**Note:** these depend on each client's GL system; confirm whether the failure is in QPTM's export build (`BLTRAN_*` → file) or the downstream system's import.

---

## 11. Accounting Month Close / Bill Roll

| Issue | Root cause | Fix | Evidence |
|-------|-----------|-----|----------|
| **Multiple runs of accounting-month-close close months not requested** | Bill-roll parameter scoping defect | Code fix + data correction | [Bill] 22-00692668, 22-00563733 |
| `BLROLLDATE` Accounting Month parameter "not working" | Parameter handling defect | Software update available | [Bill] 22-00815288 |
| End-of-Month Roll process not completing | Sub-step error (often billing) | Per root cause | [Bill] 23-00912258 |
| Invoice reruns require **reopening** the billing month | Rerun forces reopen by design/limitation | Config | [InvG] 25-01061995 |
| "Bit table incorrect for closing" / bit file incorrect | Closing-bit table out of sync | Code fix / data | [InvG] 25-01020141, 24-00945390 |

**Caution:** month-close is destructive/locking. Before any data correction, confirm exactly which production & accounting months are affected and whether downstream invoices already went out.

---

## 12. Invoice Group / Invoice ID / Numbering

| Issue | Root cause | Fix | Evidence |
|-------|-----------|-----|----------|
| New Invoice Group ID in Web doesn't auto-populate next # nor error | Web ID-generation defect | Code fix | [Bill] 22-00821101 |
| Can't create new Invoice Group (Open Season / CommPass) | Invoice-group creation defect | Data script / code | [Bill] 22-00586605, 22-00586601 |
| Reconfigure Invoice ID numbering (Ruby) | Config | Config | [Bill] 23-00922664 |
| Tracking max sequence values (proactive) | Sequence monitoring gap (see §4) | Non-standard / monitoring | [Bill] 22-00519725, 22-00586602 |

These overlap with the **§4 sequence** problem — invoice-id generation and the `BLTRAN_INVOICE_INPUT` identity both depend on healthy sequences.

---

## 13. Tax / GST / Regulatory Surcharge

| Issue | Root cause | Fix | Evidence |
|-------|-----------|-----|----------|
| GST off by cents on PPAs after a **backdated exemption** | Tax recalc on backdated exemption | Config / code | [InvG] 24-00961168 |
| GST billed on a contract with **capacity release + PPA** after amendment | Tax on cap-rel/PPA interaction (resolved on v17 upgrade) | Upgrade / non-standard | [Bill] 22-00601168 |
| Tax presentation step fails (dll) in billing | Packaging/DB object missing | Services/packaging | [Bill] 22-00821018 |

Tax issues are usually a **few cents** and tie to **amendments/exemptions/cap-rel** changing a closed month → recalc. Confirm the exemption effective date and whether the affected month was reprocessed.

---

## 14. Verbatim Fix Scripts (redacted)

> **KEY LESSON applied:** the verbatim fix SQL lives in **ADO .sql attachments**, not in SF. Concrete TSP/Rate/date/ID values are replaced with `<PLACEHOLDER>` tokens; **real table names, columns, join logic, and ordering are kept intact.** Always run the verify-SELECT and eyeball the before/after counts BEFORE `COMMIT`. Every script is wrapped in a transaction so you can `ROLLBACK`.

### Template A — Orphan Rate Detail cleanup (verbatim, redacted)
> Source: ADO **#1756911** attachments `1756911_ORPHAN_RATES.sql` / `_UPDATED.sql` / `TEP_PRD_UPDATE_RATE_*.SQL` (TEP, case 25-01044370 — CANOMCLTG erroring for all pipes). The orphan detail rows are found by a LEFT JOIN where the parent header is NULL; fixed by **end-dating** (UPDATE EFF_DT_TO) or **deleting** the orphan `RATE_DTL_ID`s. Real engine pattern below.

```sql
BEGIN TRANSACTION;

-- 0. VERIFY FIRST — list orphan rate-header IDs (detail with NO matching header on TSP+HDR+eff dates)
PRINT 'BEFORE UPDATES';
SELECT DISTINCT H.RATE_HDR_ID
FROM   RTCTRL_RATE_DTL H
LEFT JOIN RTCTRL_RATE_HDR D
       ON  H.TSP_NO      = D.TSP_NO
       AND H.RATE_HDR_ID = D.RATE_HDR_ID
       AND H.EFF_DT_FROM = D.EFF_DT_FROM
       AND H.EFF_DT_TO   = D.EFF_DT_TO
WHERE  D.TSP_NO IS NULL
  AND  H.EFF_DT_TO >= '<CUTOFF_DATE>';   -- e.g. '1/1/2025'

-- 1a. FIX OPTION 1 — end-date the orphan detail to a closed month-end (one block per orphan RATE_HDR_ID)
PRINT 'RATE <RATE_HDR_ID>';
SELECT * FROM RTCTRL_RATE_HDR WHERE TSP_NO = <TSP_NO> AND RATE_HDR_ID = <RATE_HDR_ID>;
SELECT * FROM RTCTRL_RATE_DTL WHERE TSP_NO = <TSP_NO> AND RATE_HDR_ID = <RATE_HDR_ID>;

UPDATE RTCTRL_RATE_DTL
SET    EFF_DT_TO = '<MONTH_END>'          -- e.g. '2025-01-31 00:00:00.000'
WHERE  TSP_NO = <TSP_NO>
  AND  RATE_DTL_ID IN (<DTL_ID_1>, <DTL_ID_2>, ...);

-- 1b. FIX OPTION 2 — when the detail must not exist at all, DELETE the orphan detail rows
PRINT 'RATE <RATE_HDR_ID>';
SELECT * FROM RTCTRL_RATE_HDR WHERE TSP_NO = <TSP_NO> AND RATE_HDR_ID = <RATE_HDR_ID>;
SELECT * FROM RTCTRL_RATE_DTL WHERE TSP_NO = <TSP_NO> AND RATE_HDR_ID = <RATE_HDR_ID>;

DELETE FROM RTCTRL_RATE_DTL
WHERE  TSP_NO = <TSP_NO>
  AND  RATE_DTL_ID IN (<DTL_ID_1>, <DTL_ID_2>, ...);

-- 2. RE-VERIFY — the orphan list should now be empty (or only expected rows)
PRINT 'AFTER UPDATES';
SELECT DISTINCT H.RATE_HDR_ID
FROM   RTCTRL_RATE_DTL H
LEFT JOIN RTCTRL_RATE_HDR D
       ON  H.TSP_NO = D.TSP_NO AND H.RATE_HDR_ID = D.RATE_HDR_ID
       AND H.EFF_DT_FROM = D.EFF_DT_FROM AND H.EFF_DT_TO = D.EFF_DT_TO
WHERE  D.TSP_NO IS NULL AND H.EFF_DT_TO >= '<CUTOFF_DATE>';

COMMIT;        -- only after the AFTER list is clean; else ROLLBACK;
-- ROLLBACK;
```

### Template B — BLINVGEN sequence reseed + report-table purge (pattern)
> Source: resolution text + ADO **#1665295 / #1607556** (TEP/TIGT, "ERROR SETTING VALUE FOR COLUMN INVOICE_INPUT_ID FOR PRIMARY TABLE BLTRAN_INVOICE_INPUT"). Resolution: *"Update archive definition and script required to reseed sequence / purge report table."* The verbatim values are environment-specific; the **pattern** is: (1) confirm the maxed identity/sequence on `BLTRAN_INVOICE_INPUT`, (2) archive/purge the bloated input/report rows, (3) reseed the identity, (4) add monitoring. Do NOT widen scope — reseed only the affected sequence.

```sql
-- 0. CONFIRM the maxed sequence/identity feeding the failing column
SELECT MAX(INVOICE_INPUT_ID) AS MAX_ID FROM BLTRAN_INVOICE_INPUT;   -- compare to the column's max datatype value
-- (also inspect the identity/sequence object's current value via the env's reseed utility)

-- 1. ARCHIVE / PURGE the bloated report/input rows per the client's archive definition (do this FIRST)
--    -> follow the "archive definition" update; remove processed/stale BLTRAN_INVOICE_INPUT (and report) rows.

-- 2. RESEED the identity/sequence for BLTRAN_INVOICE_INPUT back to a safe low value
--    (use the supported reseed utility/script for the platform; e.g. DBCC CHECKIDENT on SQL Server,
--     or the QPTM sequence-reseed script — NOT a manual UPDATE of the id).

-- 3. RE-RUN BLINVGEN for the affected accounting month; confirm it completes.
-- 4. ADD monitoring on the sequence so it alerts BEFORE maxing (gap that caused 23-00908498 RCA).
```

> **Provenance:** Template A is verbatim from ADO #1756911 attachments (redacted). Template B is reconstructed from the #1665295 / #1607556 resolution text + the SF "ERROR SETTING VALUE…" error string ([Bill] 23-00908498/24-00942047, [InvG] 24-00957495); the exact reseed values are env-specific, so capture the real numbers per incident.

---

## 15. Key Code Files, Batch Processes & Repos

### Batch processes (Quorum.QPTM.Batch — repo e024d80b-5c45-411c-93e1-78e2798ed885)
| Process | Purpose | Cluster |
|---------|---------|---------|
| `BLINVGEN` / `BLINVGEN1` (`BLINVGEN1S`) | Invoice Generation — Rate→TOC→charge, writes `BLTRAN_INVOICE_INPUT` | §4, §7 |
| `PANIGHTLY` | Nightly aggregation incl. billing step | §4 |
| `BLSOAIMP` | Statement of Account / payment import | §9 |
| `BLROLLDATE` / Accounting Month Close (Bill Roll) | Advance/close accounting month | §11 |
| `BLCCSVOL` | Charge-basis volume build (perf-heavy) | §4 |
| `CANOMCLTG` | (CAS) — first victim of orphan-rate corruption | §5 |
| `DATAPUB` / Platts feed | Index-price publication | §5 |

### Repos to search
| Repo | Purpose |
|------|---------|
| Quorum.QPTM.Batch (e024d80b-…) | BLINVGEN/PANIGHTLY/BLSOAIMP/bill-roll batch code |
| Quorum.QPTM.Web (41e317c0-844c-4728-98da-529092957738) | Rate Maintenance / Invoice Maintenance / COA Web screens & reports |
| APL.QPTM.Database (2e1fb9e5-…) | QPTM billing/rate schema + migrations |
| `<CLIENT>.QPTM.*` (TEP, QTR, HEP/HPE, DSU, ENT, GBG) | Client overrides — **always check** for client-specific invoice/rate code before assuming base behavior |

Code search examples:
```
{"searchText":"BLTRAN_INVOICE_INPUT"}
{"searchText":"RTCTRL_RATE_DTL repo:Quorum.QPTM.Batch"}
{"searchText":"unrounded tax repo:Quorum.QPTM"}
```

---

## 16. Database Tables Reference

| Table | Purpose |
|-------|---------|
| `BLTRAN_INVOICE_INPUT` | **Invoice generation input rows; identity `INVOICE_INPUT_ID` maxes out → §4 failure.** Also `ALLOC_PTR_VOL_QTY` column. |
| `RTCTRL_RATE_HDR` | **Rate header** (Rate ID, TSP, eff dates). |
| `RTCTRL_RATE_DTL` | **Rate detail** (RATE_DTL_ID, price); **orphans here (no matching HDR) break billing — §5/§14.** |
| `BLTRAN_*` (invoice/charge/export) | Billing transaction & export tables (CIS/PeopleSoft/XML build) |
| Chart of Accounts tables | GL account mapping; PK errors & time-slice cascade (§10) |
| Statement-of-Account / payment tables | BLSOAIMP target (§9) |
| Accounting-month / closing-bit tables | Month-close state (§11) |
| TOC / TOS config tables | Type-of-Charge / Type-of-Service associations (charge resolution) |
| PPA / cashout tables | Prior-period-adjustment events (§8) |
| `BLTRAN_PPA_EVENT` | PPA event records (lifecycle upstream of billing) — rows here with **no** matching billing line = billing half failed (§4.4/§8). |
| `BLTRAN_INVOICE_GEN_QTY` | Generated billing quantity lines; `CHARGE_BASIS_CD='PEX'` = PAL-extension charge — **0 PEX rows** for the month = §4.4 impact signature. |
| `BLSTAG_PAL_EXT` | CORE STAG base table (PAL extension day counts). **Dropped by build 3.1.00.0069 while the CORE reader kept joining it → §4.4 crash.** Writer (`CalcPALExtension`) exists only at DTE/QLNG; an empty table is a complete fix elsewhere. |
| `BLRPTS_10_INVOICE_DOC_PAL` | PAL daily/monthly statement report-staging target of `QSQLID_INS_SEL_INVOICE_DOC_PAL_DAY/_MTH` (§4.4). |

> Concrete child-table names for BLTRAN/SOA/closing were not all exposed in the mined cases — confirm exact names against the schema (APL.QPTM.Database) before scripting beyond `RTCTRL_RATE_*` and `BLTRAN_INVOICE_INPUT`, which ARE confirmed from the verbatim script + error strings.

---

## 17. Diagnostic SQL Queries

### A. Identify the failing BLINVGEN run
```sql
-- Pull the process-queue error for the client-supplied PQID(s); look for
-- "ERROR SETTING VALUE FOR COLUMN INVOICE_INPUT_ID / ALLOC_PTR_VOL_QTY FOR PRIMARY TABLE BLTRAN_INVOICE_INPUT"
-- (process-queue table per environment).
```

### B. Rate → header sanity for a contract / Rate ID
```sql
SELECT TSP_NO, RATE_HDR_ID, EFF_DT_FROM, EFF_DT_TO  -- + TOC/TOS columns
FROM   RTCTRL_RATE_HDR
WHERE  TSP_NO = <TSP_NO> AND RATE_HDR_ID = <RATE_HDR_ID>;

SELECT *
FROM   RTCTRL_RATE_DTL
WHERE  TSP_NO = <TSP_NO> AND RATE_HDR_ID = <RATE_HDR_ID>
ORDER BY EFF_DT_FROM;
```

### C. Charge resolution (Rate→TOC→TOS) — confirm the charge is actually associated
```sql
-- Verify the contract's TOC/TOS carries the expected Rate ID for the production month.
-- (TOC/TOS association tables — confirm names in schema; pattern: contract -> TOS -> TOC -> RATE_HDR_ID.)
```

### D. Sequence / identity health (the §4 root cause)
```sql
SELECT MAX(INVOICE_INPUT_ID) AS MAX_ID FROM BLTRAN_INVOICE_INPUT;
-- Compare MAX_ID to the column's datatype ceiling; near the ceiling => reseed + purge (§14 Template B).
```

### E. Orphan rate detail (the §5 root cause) — VERBATIM detector
```sql
SELECT DISTINCT H.RATE_HDR_ID
FROM   RTCTRL_RATE_DTL H
LEFT JOIN RTCTRL_RATE_HDR D
       ON  H.TSP_NO = D.TSP_NO AND H.RATE_HDR_ID = D.RATE_HDR_ID
       AND H.EFF_DT_FROM = D.EFF_DT_FROM AND H.EFF_DT_TO = D.EFF_DT_TO
WHERE  D.TSP_NO IS NULL
  AND  H.EFF_DT_TO >= '<CUTOFF_DATE>';
```

### F. PPA events for a contract/month (the §8 spurious-PPA check)
```sql
-- List PPA events for the contract & production month; if they appeared after an immaterial
-- closed-month rate end-date change, they are likely spurious -> leave UNAPPROVED, they drop on close.
SELECT * FROM BLTRAN_PPA_EVENT WHERE TSP_NO = <TSP_NO> /* + contract / prod month filters */;
```

### G. PAL/LPS billing adjustment missing (the §4.4 check)
```sql
-- Proves the defect condition: NULL = BLSTAG_PAL_EXT missing (§4.4 crash will occur).
SELECT OBJECT_ID('dbo.BLSTAG_PAL_EXT');

-- Proves billing impact: 0 rows = no PAL-extension (PEX) billing lines written for the prod month.
SELECT * FROM BLTRAN_INVOICE_GEN_QTY
WHERE  CHARGE_BASIS_CD = 'PEX' AND TSP_NO = <TSP_NO> AND PROD_MTH = '<YYYY-MM-01>';

-- Proves the PPA lifecycle completed (event exists, processed) while the billing half is missing.
SELECT * FROM BLTRAN_PPA_EVENT WHERE TSP_NO = <TSP_NO> /* contract & prod month */;
```

---

## 18. Known Historical ADO Bugs

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|-------|--------------|-----------------|---------|---------|
| **#1756911** | Bug / **Closed** | TEP — CANOMCLTG erroring for all pipes; **orphan `RTCTRL_RATE_DTL` cleanup** (verbatim SQL attached) | §5 Orphan rates | 25-01044370 |
| **#1665295** | Bug / **Closed** | TEP/TIGT — CRITICAL BLINVGEN fails without errors; **reseed sequence + purge report table** | §4 Sequence | 24-00957495 |
| **#1607556** | Bug / **Closed** | TIGT — BLINVGEN batch failure RCA (sequence maxed, no prior notification) | §4 Sequence | 23-00907641 / 23-00908498 |
| #1733048 | Bug / Closed | HEP/Midship 610 — BLINVGEN stopping on error (BLINVGEN1S invoice) | §4 | — |
| #1773883 | Bug / Closed | HPE TSP 17 — BLINVGEN stopping on errors (Jan 2025 close) | §4 | 25-01062471 |
| #1747979 / #1748166 | Bug+Task / Closed | DSU — BLINVGEN Registered SQL Error | §4 | — |
| #1700620 | Bug / Closed | TEP/REX 501 — CR Seasonal Date issue for BLINVGEN | §4 | 24-00991058 |
| #1705283 / #1727654 | Bug / Closed | QTR — BLINVGEN causing invoice document to generate differently | §4/§6 | 24-00984145 |
| #1806153 / #1806551 / #1807698 | Bug+Task / **Active/Proposed** | ENT/QPTM — BLINVGEN Invalid Parameter Exception / formula-price calc | §4 | — |
| #1696922 | Bug / Closed | GBG — BLSOAIMP not applying payment; **multi-row CSV import** | §9 | 24-00987963 |
| #1644043 | Bug / Closed | PPA Cashouts sometimes don't work | §8 | 23-00936358 |
| #1472782 / #1490712 / #1472846 | Feature / Closed | Invoice Rounding / PF Invoice Rounding | §7 | — |
| **#1836277** | Bug / **Proposed (open — NO fixed-in version as of 2026-08-14)** | EQC — `BLSTAG_PAL_EXT` invalid object name (CORE 3.1.00.0069 schema drop vs CORE reader in QPSGenerateDocuments.cpp) | §4.4 PAL/LPS | 26-01106039 |
| WI #1836679 | Request / Closed | EQC DEV — `BLSTAG_PAL_EXT` inserted from another instance; **the ops-deploy precedent + differential proof** (zero code/data change cleared the error) | §4.4 | 26-01106039 |
| #1638997 | Bug / Closed (Client-Specific) | DTE — PAL Extension Fee Count Error (proves the PAL path works where the object exists) | §4.4 | — |

> **Takeaway:** the two highest-value, repeatable operational fixes are (1) **orphan-rate cleanup** (verbatim script, #1756911) and (2) **BLINVGEN sequence reseed + purge** (#1665295/#1607556). Both are Cloud-Ops data deployments, usually deadline-boxed. Many "BLINVGEN failing" SF cases are **not** linked to a unique product bug — they recur as the same sequence/orphan condition.

---

## 19. Expected Behavior / User Education

Root Cause = **Customer Error / Training** (~90+ across the three categories). Recognize these before scripting/escalating.

| Reported as | Reality | Case |
|-------------|---------|------|
| "PPAs appeared after I time-sliced/edited a closed-month rate" | Expected if material; if **immaterial end-date** change, leave them **unapproved** → they drop on close | 22-00693332, 22-00832258 |
| "Rate Maintenance triggered a PPA in the current month" | Working as designed when the rate change is in an open month | 22-00832258 |
| "BillGen / billing issue" (generic) | Often a config/data question, not a defect — get the specific contract & error | 25-01030802, 24-00994408, 25-01017306 |
| "No PPAs using the workaround" / "Cannot get Quorum to process PPAs" | Workaround/training, not a code fix | 23-00933371, 23-00906663, 23-00905066 |
| "Accounting month roll mistake / month still closed" | User ran the roll with wrong params / wrong month | 23-00928929, 23-00929855, 23-00910775 |
| "CICO imbalance differs from Invoice Sub-Detail Summary" | Expected presentation difference, needs explanation | 26-01082063 |
| "Rate warning / MULTIPLE RATE IDS on Rate Errors report" | Informational/setup, not a defect | 24-00951892, 23-00927199, 23-00911457 |
| Documentation requests (charge-basis lists, TOC association, retro how-to) | Provide docs, not a fix | 25-01040169, 26-01085123 |
| Invoice template format change (date format, logos, drop timestamp) | Config/template request | 23-00921077 |

**Tell-tale that it's user/expected:** a generic "billing issue" with no error string; a PPA after an open-month or immaterial change; a month-roll run with the wrong parameter; or a presentation difference between two screens that sum differently by design.

---

## 20. Escalation Decision Tree

```
Billing / Invoicing / Rate case reported
│
├─ Batch FAILED (BLINVGEN/BLINVGEN1/PANIGHTLY/month-roll)?  (§4, §11)
│   ├─ Error mentions "...COLUMN INVOICE_INPUT_ID/ALLOC_PTR_VOL_QTY ... BLTRAN_INVOICE_INPUT"?
│   │     → SEQUENCE MAXED → reseed + purge report table (§14-B); add monitoring → ADO #1665295/#1607556
│   ├─ "Erroring for ALL pipes" / CANOMCLTG / random CAS errors / system slow?
│   │     → ORPHAN RATE DETAIL → run §17-E detector → orphan-rate cleanup script (§14-A) → ADO #1756911
│   ├─ "Rate Resolution" / formula-price / Invalid Parameter?
│   │     → fix Rate→TOC→TOS chain (§5) or escalate code (ADO #1806153 family)
│   ├─ SQL 208 "Invalid object name 'BLSTAG_PAL_EXT'" (LPS/PAL — PPA processed, no billing adjustment)?
│   │     → MISSING CORE OBJECT (3.1.00.0069 drop) → script object from DEV/DTE + rerun PPAs
│   │       + reverse manual LGAs (§4.4) → ADO #1836277 / WI #1836679
│   └─ Slow/hung but not erroring? → archive/purge bloated input table; perf
│
├─ Amount WRONG?  (§7, §5, §8)
│   ├─ Header≠detail / SOA≠Summary "out by one cent"? → rounded-vs-unrounded tax defect (code) → #1472782 family
│   ├─ Charge missing / over / tripled? → Rate→TOC→TOS config (mostly), or child-contract release setup
│   ├─ PPA created/reversed/$0 cashout? → §8 (spurious-PPA: leave unapproved; reversing: cache reset; $0: cashout config)
│   └─ Tax/GST off by cents? → amendment/exemption recalc (§13)
│
├─ Invoice/report won't RENDER (blank/cutoff/no-data)?  (§6)
│   └─ Check Web vs Classic, internal vs external user, post-upgrade (v17/2024.x) report config
│
├─ Payment / Statement of Account import?  (§9)
│   └─ BLSOAIMP CSV multi-row/multi-BA, table-clear → reproduce with client's file → ADO #1696922
│
├─ Rate Maintenance / Index screen?  (§5)
│   └─ Web save/validation/decimal defect, or Rate-ID identity → check <CLIENT>.QPTM override first
│
├─ Export (CIS/PeopleSoft/XML) / Chart of Accounts?  (§10)
│   └─ Export build vs downstream import; COA PK / time-slice cascade
│
├─ Month won't close / closed wrong months?  (§11)
│   └─ Bill-roll parameter scoping; closing-bit table → confirm affected months BEFORE any data fix
│
└─ Generic "billing issue", PPA how-to, month-roll mistake, presentation difference?
    → likely Customer Error / Training (§19) — get specifics; educate, don't script
```

---

*Skill created: 2026-06-01 · Updated: 2026-08-14 (§4.4 PAL/LPS `BLSTAG_PAL_EXT` cluster from case 26-01106039 / ADO #1836277)*
*Based on: ~191 actionable QPTM Billing + Invoice Generation + Rates SF cases + ADO #1756911, #1665295, #1607556, #1733048, #1773883, #1747979, #1700620, #1705283, #1696922, #1644043, #1472782/#1490712/#1472846, #1836277/WI #1836679. Verbatim fix SQL from ADO #1756911 attachments.*
*Companions: SKILL_Nominations.md, SKILL_EDI_Troubleshooting.md, SKILL_Capacity_Release.md. Applicable to all QPTM TSPs/clients.*
