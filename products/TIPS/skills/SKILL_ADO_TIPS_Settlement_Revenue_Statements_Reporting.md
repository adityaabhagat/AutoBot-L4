# SKILL: TIPS Settlement / Revenue / Statements / Reporting — ADO Defect & Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** TIPS (My Quorum TIPS — gas & crude transaction processing / settlement accounting) | **Source:** Azure DevOps closed/resolved Bugs (QuorumSoftware org)
**Scope:** The **settlement → revenue → journal → statement/report** back-end and its reporting surface — the **Settlement** engine & batch (Settle / Contractual Settlement / GAS_STMT proc, rate schedules, fixed fuels, plant ownership), **Revenue** (Override Revenue Flag screen, revenue export/transfer to QDOD/BOLO, double-volume tie-out, revenue reversal), **Journal** (Journal Entry Control, JOURNAL/JOURNALIMB/JEOGSYSEXP/journal-split/journal-transfer batch, GL/SAP/OGSYS export), and the **Statements & Reports** layer (Gas Statement, Settlement Invoice, Plant Performance, Liquid Allocation, Tier1, CO&O, Report Distribution, Crystal/QQM query screens).

> **Use When:** an ADO bug or L4/L2 case is about a TIPS settlement number, a revenue/journal/statement value that is wrong or missing, a Settle/JOURNAL/REVTRAN/PLANTOWN batch step crashing, a Gas Statement / Settlement Invoice / Plant Performance / CO&O **Crystal report** producing wrong/blank/duplicate data, the **Override Revenue Flag** screen erroring or not matching Classic, **Journal Entry Control** columns/conditions, or **Report Distribution / QEMAIL** not sending. Companion (out of scope here): allocation/PPA/imbalance *volume* generation, measurement, contract/CCT master-data maintenance, QPTM nomination/scheduling/RFS/offer/capacity-release and IPWS/EBB/FERC posting (see the QPTM ADO skills).

> **Evidence base:** WIQL over BOTH bug branches — `…\Engineering\Midstream` (TIPS product teams: *Guardians of TIPS, TIPS Samurai, TIPS'n Tricks*) and `…\Engineering\Maintenance\Midstream and Transportation` (Customer/Professional Service — **this branch is MIXED QPTM + TIPS**). Bug, State in (Closed, Resolved), title containing settlement / settle-fees / SETTLEMGR / revenue / statement / gas-statement / query-screen / report / QRPTS / QPOST / journal. Those broad terms matched **1,413** bugs (dominated by generic "report"/"revenue" noise spanning all of midstream). After fetching fields and filtering to genuine TIPS settlement/revenue/journal/statement/report function (dropping QPTM nomination/offer/RFS/capacity-release/IPWS and QPTM-billing items), **~482 in-area bugs** remain. **64 were deep-read** (description + repro + full comment thread + linked PRs + linked SF case). Every root-cause/fix below cites a real ADO #, and an SF case (`YY-xxxxxxxx`) where one was linked.
>
> **Fixed-in-build caveat:** `Microsoft.VSTS.Build.IntegrationBuild` is **empty on every one of these bugs.** Fixed-in-build is therefore **inferred** from iteration path (YY.NN), tags ("PEM 2022", "queued for next TIPS 2020.03", "Reviewed - <Month Year>"), and the **PR target branches named in the comment thread** (e.g. "merged to 2020.03 / 2023.04 / 2024.04 / develop"). All build values below are marked *(inferred — confirm in `Quorum.TIPS.ReleaseNotes`)*. Many fixes are **client-specific** and ship as a **client hotfix/patch** (e.g. `IAC.TIPS.ClassicBatch`, `PEM.*`, `SCX.*`, `ALT.TIPS.Database`), NOT a core GA.

---

## TABLE OF CONTENTS
1. [Quick Triage Table](#1-quick-triage-table)
2. [The Settlement→Revenue→Journal→Statement Pipeline & Vocabulary](#2-the-pipeline--vocabulary)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — Gas Statement Crystal/view defects (posted-vs-nonposted & client-vs-core drift)](#4-cluster-a--gas-statement-crystalview-defects)
5. [Cluster B — Settlement batch failures (GAS_STMT proc / row-width / formula crash)](#5-cluster-b--settlement-batch-failures)
6. [Cluster C — Settlement Invoice & CO&O / Plant-Performance reports](#6-cluster-c--settlement-invoice--coo--plant-performance-reports)
7. [Cluster D — Override Revenue Flag screen (error / parity / double-volume)](#7-cluster-d--override-revenue-flag-screen)
8. [Cluster E — Revenue export / transfer / reversal (QDOD, BOLO)](#8-cluster-e--revenue-export--transfer--reversal)
9. [Cluster F — Journal output wrong (config: conditions, columns, char-limit)](#9-cluster-f--journal-output-wrong-config)
10. [Cluster G — Journal reversal / sign / split / netting defects (code)](#10-cluster-g--journal-reversal--sign--split--netting-defects)
11. [Cluster H — Journal batch failures (JOURNALIMB perf, transfer, OGSYS)](#11-cluster-h--journal-batch-failures)
12. [Cluster I — Rate schedule / fixed fuels / settle-fees calculation](#12-cluster-i--rate-schedule--fixed-fuels--settle-fees-calculation)
13. [Cluster J — Reporting infrastructure (Crystal upgrade, Report Distribution, external views, query screens)](#13-cluster-j--reporting-infrastructure)
14. [Fix-Version Matrix](#14-fix-version-matrix)
15. [Diagnostic pointers (SQL / views / files)](#15-diagnostic-pointers)
16. [Escalation Guidance](#16-escalation-guidance)
17. [Product-overlap caveats & dead ends](#17-product-overlap-caveats--dead-ends)

---

## 1. Quick Triage Table

| Symptom (what the case/bug reports) | Likely cause | First check / cluster |
|---|---|---|
| Gas Statement value wrong only on the **POSTED** report (non-posted is correct) | A view fix was applied to `QRPTS_…_VW` (non-posted) but **not** the mirror `QPOST_RPTS_…_VW` (posted) | §4 — the recurring posted-vs-nonposted drift (#1434950, #1665714, #1770839) |
| Gas Statement value wrong only for **one client**, core looks fine | Client has a **client-specific .RPT crystal + client `QRMTIPS` view**; the core fix was never copied to the client report | §4 — client-vs-core drift (#1354249, #1611648, #1324962) |
| Gas Statement: shrink=0 on TIK, theo gallons missing on POP, gas-lift double-counts wellhead, C6+/Hexane+ rolled into "Other", liquid line hidden when 0 | Crystal formula / `QRPTS_SETTLE_GAS_STMT_*_VW` logic defect | §4 |
| **Settlement batch ERRORS at GAS_STMT step** ("can't access `SP_QTIP_RPT_SETTLE_STMT`", MSSQL Msg 611) | `QTIP_RPTS_SETTLE_STMT` has 538 mostly-VARCHAR cols → row width over limit + MSSQL clustered-index bug (KB4045814) | §5 (#1672304/#1672793 SRB) |
| Settle Fees not generating for random days; fee=0 | A 0-volume disposition (MESD) crashes the rate formula; or split-decimal `EFF_PCT_CONTR`=0 | §12 (#1708209 EQT — config `PROGRESSIVE_ROUNDER_NO_BOUND_CHECK`) |
| Settlement Invoice report shows **duplicate fee values** | Meter split with **same contract on both suffixes**; `QRPTS_SETTLE_INV_DTL_VW` QTRAN_PAYSTATION join missing `MTR_SFX` filter | §6 (#1767237 SRI) |
| CO&O / Plant Ownership **Rate & Excess charge = 0** when using a Revenue **Rate Schedule** (manual rate works) | Rate schedule is type **Fee**; CO&O needs type **Price**. (Also missing `Sel_H2SCO2_PCT` SQL on MSSQL → PLANTOWN "Operating system error") | §6 (#1736767 PEM) |
| Plant Performance NGL/residue wrong with PPAs | `QRPTS_PLANT_PERF_CTGRY` logged under the **PPA month** not current month | §6 (#1430998 DCP) |
| **Override Revenue Flag** screen errors / `ORA-01013` / disconnect, fixes itself | Query timeout vs **stale optimizer stats on empty QTRAN_PAYSTATION/ALLOC_VOL** after posting | §7 (#1658025/#1665332 IAC — bump ClassicGUI timeout; recalc stats) |
| Override Revenue Web **doesn't match Classic** / missing grid columns | Web grid/SOA grid-definition out of sync with Classic | §7 (#1726832, #1783101) |
| Revenue volume **doubled** vs settle | Revenue sums **all** iteration volumes incl. CALC_ONLY rows; or **duplicate open-ended meter timeslice** → dup QTRAN/QPOST_REVENUE rows | §7 (#1709416 ETP — `CALC_ONLY_IND`; #1355919 IAC — dedupe timeslice) |
| Revenue export/transfer: tax=0 to BOLO, NULL into QDOD, "@" in formula | Client SP driven by `USR_DEF_2`; missing COALESCE; Crystal-2016 upgrade rejects "@" | §8 |
| Journal **not generating** for a meter / wrong account | Missing / **double** condition on **Journal Entry Control**; or missing Web column | §9 |
| Journal **reversal/GST/tax not reversed**, split tripling/excluding, OGSYS offset not netting to 0 | Reversal-handling or split-rounding **code/view** defect | §10 |
| `JOURNALIMB` / journal-split takes hours (1st re-run only) | Stale stats on empty TRAN tables; add `CALC_STATS` step | §11 (#1598509 IAC) |
| Journal Transfer file: wrong create-user, BA datatype, won't init | Client `QPPJRNTRN_FM` / `QPSJournalTransFM` proc defect | §11, §8 |
| Various reports **fail to export** ("A boolean is required here", won't build) | **Crystal Reports 2016/2025 upgrade**; client report missing from path; external `_XVW` missing a column | §13 |
| **Report Distribution** sends the 2nd report twice / first never / wrong BAs | Bad `QCODE_RPT_DISTR_DTL` setup + inactive event detector; or view only filters NP statement-format-code | §13 (#1613498 ALT), §4 (#1773030 MOM) |

---

## 2. The Pipeline & Vocabulary

```
[Allocation + Measurement + Contract CCTs + Rate Schedules + Fixed Fuels]
      │  Facility Batch Job Submittal (FBJS):  MEASUREMENT → ALLOCATE → SETTLE (CONTRACTUAL SETTLEMENT) → JOURNAL
      ▼
[QTRAN_SETTLE_SUMMARY / QTRAN_SETTLE_PROD / QTRAN_SETTLE_TAX / QTRAN_PAYSTATION]   (non-posted = QTRAN_*, posted = QPOST_*)
      │
      ├─► STATEMENTS/REPORTS:  GAS_STMT proc → QTIP_RPTS_SETTLE_STMT → QRPTS_/QPOST_RPTS_*_VW → Crystal .RPT (Gas Statement, Settlement Invoice, Plant Perf, CO&O…)
      ├─► REVENUE:  Override Revenue Flag screen (sets REVENUE_IND), Revenue batch → QTRAN_/QPOST_REVENUE → export/transfer (QDOD, BOLO)
      └─► JOURNAL:  Journal Entry Control (conditions/value-types) → JOURNAL / JOURNALIMB / JESPLIT / JEOGSYSEXP → QTRAN_JOURNAL_ENTRY → Journal Transfer (QPPJRNTRN_FM / QPSJournalTransFM) → GL / SAP / OGSYS
```

### Key terms (Quorum/TIPS vocabulary)
- **Posted vs Non-Posted** = every settlement/journal/revenue table and report view exists twice: non-posted `QTRAN_*` / `QRPTS_*_VW`, and posted `QPOST_*` / `QPOST_RPTS_*_VW`. **The #1 statement defect pattern is a fix landing on one side only** — verify the mirror view/report. "Report Table Map Cd" parameter (NON-POSTED / POSTED RESULTS) selects which side a report reads.
- **Client-vs-Core report** = a client (SCX, PEM, IAC, DCP, ONM, CHD…) usually has a **client-specific `.RPT` Crystal file + client `ESUITE_Q<CLIENT>`/`QRMTIPS` view** copied from core at go-live. A core fix does **not** propagate to the client report unless explicitly re-applied — and vice versa. Half the FVFs here are "fixed core but not client" (or "client but not core").
- **CCT** = Contract Charge Type — the contract row driving a fee/charge; has a **unit time code** (daily vs monthly). Mismatch causes wrong roll-ups.
- **PPA** = Prior Period Adjustment (re-open a closed month). Reruns/PPAs surface many of these defects (perf, doubling, plant-perf month mislogging, journal reversal).
- **Override Revenue Flag screen** = `QVPOVERRIDEREVENUEFLAG` (Web) / Facility>Revenue>Override Revenue Flag (Classic). Sets the **Revenue Indicator** (which meters get revenue-processed) by comparing prior vs corrected gas-statement net value against **plant tolerances** (% AND $). Backed by `QCTRL_REV_OVERRIDE_VW` and (for IAC/DCP) a client-specific prior-amount query in `*.TIPS.ClassicBatch\QPDllTipsSettle`.
- **Journal Entry Control** = screen mapping fees/products → GL account/cost center via **conditions** and **value types**. Tables `QCTRL_JOURNAL_DTL` (config), `QTRAN_JOURNAL_ENTRY` / `_CAN` (output). CAN (Canada) has parallel `_CAN` tables that **drift** in column width.
- **GAS_STMT proc** = `SP_QTIP_RPT_SETTLE_STMT` populates the very wide `QTIP_RPTS_SETTLE_STMT` table that the gas statement reads. Runs as part of the SETTLE batch.
- **`QRPTS_SETTLE_GAS_STMT_*_VW`** family = the gas-statement source views (PLNT / PROD / base). Most gas-statement value bugs trace here or to the matching crystal formula.
- **Report Distribution** = System>Exports>Report Distribution → logs notification events → `QEMAIL` job sends them. Config in `QCODE_RPT_DISTR_DTL` + event-detector active flag.
- **QQM / Query Screens / Interactive Reports** = the Web report-replacement layer (Exago/Interactive Reports). Many "Query Screens" bugs are internal beta/parity items, not customer defects.
- **CR2016 / CR2025** = Crystal Reports runtime upgrades; both caused waves of report-execution failures (boolean-formula, "@" in param name, build failures).

---

## 3. Decision Tree

```
TIPS settlement / revenue / journal / statement / report bug
│
├─ A BATCH process/step crashed?  → get FBJS Process-Queue-ID + step name + exact ORA/COM/SQL error
│   ├─ SETTLE errors at GAS_STMT / "can't access SP_QTIP_RPT_SETTLE_STMT" / MSSQL Msg 611  → §5 (row-width; truncate TAX_TYPE_DESCR / drop PK clustered index; long-term split table)
│   ├─ JOURNALIMB / JESPLIT takes hours, 1st re-run only                                    → §11 (stale stats on empty TRAN tables; add CALC_STATS step)
│   ├─ JOURNAL transfer fails (create-user, BA datatype, m_pTipsMsgLog null)                → §11/§8 (client QPPJRNTRN_FM / QPSJournalTransFM)
│   ├─ PLANTOWN "Operating system error" (MSSQL)                                            → §6 (#1736767 missing Sel_H2SCO2_PCT SQL)
│   └─ REVTRAN revenue-reversal inserts NULL                                                → §8 (#127302 client SP missing COALESCE)
│
├─ A REPORT ran but VALUE is wrong / blank / duplicate?
│   ├─ Wrong only on POSTED report (non-posted OK)               → §4 (apply the QRPTS_ fix to the QPOST_RPTS_ mirror view)
│   ├─ Wrong only for one client (core OK)                       → §4 (copy core fix into the client .RPT + client QRMTIPS view)
│   ├─ Gas Statement shrink/theo/gas-lift/C6+/0-liquid           → §4 (crystal formula / QRPTS_SETTLE_GAS_STMT_*_VW)
│   ├─ Settlement Invoice duplicate fees (meter split same ctr)  → §6 (#1767237 add MTR_SFX filter on QRPTS_SETTLE_INV_DTL_VW)
│   ├─ Plant Performance wrong NGL/residue w/ PPA                → §6 (#1430998 QRPTS_PLANT_PERF_CTGRY logged under PPA month)
│   ├─ CO&O rate/excess = 0 with rate schedule                   → §6 (#1736767 rate schedule must be type Price not Fee)
│   ├─ Report fails to export ("boolean required", won't build)  → §13 (Crystal 2016/2025 upgrade; external _XVW missing column; client report missing from path)
│   ├─ Report ignores a parameter (e.g. Prod_Cd)                 → §13 (#1611648 Web has no "Ignore Param"; default the param)
│   └─ Report Distribution sends wrong/dup/no email              → §13 (#1613498 QCODE_RPT_DISTR_DTL + event detector) / §4 (#1773030 BA filter)
│
├─ REVENUE?
│   ├─ Override Revenue Flag errors / ORA-01013 / disconnects    → §7 (timeout + stale stats; restart, bump ClassicGUI timeout, recalc stats)
│   ├─ Override Revenue Web ≠ Classic / missing columns          → §7 (grid/SOA def parity)
│   ├─ Revenue volume doubled                                    → §7 (#1709416 CALC_ONLY_IND; #1355919 dup meter timeslice)
│   └─ Revenue export/transfer wrong (BOLO tax 0, QDOD NULL, "@")→ §8
│
├─ JOURNAL output wrong (not a crash)?
│   ├─ Not generating for a meter / wrong account / missing Web column  → §9 (config: Journal Entry Control condition / QCTRL_JOURNAL_DTL columns)
│   ├─ CAN journal won't run "String/binary truncated"          → §9 (#1776599 CAN column char-limit drift; widen JE_COND_CD_VALUE)
│   ├─ Reversal/GST/tax not reversed, split tripling/excluding   → §10 (code/view defect)
│   └─ OGSYS offset not netting to 0                             → §10 (#1355571 JEOGSYSEXP QJournalEntry.cs)
│
└─ Vague "error", "how do I", audit, parity-only beta/Query-Screen item → likely Training/internal-QA; verify config & upstream allocation first (§17).
```

---

## 4. Cluster A — Gas Statement Crystal/view defects

**The single largest and most repetitive statement signature.** Two structural traps drive almost every gas-statement value bug:

1. **Posted-vs-Non-posted view drift.** A fix is applied to the non-posted view `QRPTS_SETTLE_GAS_STMT_*_VW` but **not** to the posted mirror `QPOST_SETTLE_GAS_STMT_*_VW` (or vice versa). Symptom: report correct for current/non-posted month, wrong for a posted month.
2. **Client-vs-Core report drift.** The client (SCX, IAC, CHD, PEM, Fundare…) runs a **client-specific `.RPT` + client `ESUITE_Q<CLIENT>` view**; a core fix never reaches it. Symptom: correct in core, wrong for the client (or only the client report exists and core was never fixed).

| Bug | Client | Symptom | Root cause | Fix |
|---|---|---|---|---|
| **#1354249** | SCX | Shrink shows 0 for **TIK ALL** pay code; POP statement missing **Theoretical Gallons**; gas-lift volume wrongly added to **Gross Wellhead** | Crystal formula + `QRMTIPS` gas-stmt view logic; gross wellhead should be `QTRAN_FIXED_FUELS` wellhead-delivered only | Fixed shrink regardless of pay code; added theo-gallons to POP section; gross wellhead = wellhead-delivered. **Applied to SCX AND core** after a follow-up (changes 1 & 3 had to be ported to core) |
| **#1434950** | SCX | FR gas statement **Allocated Gallons wrong on POSTED month**; TIK contracts show 0 allocated gallons | A prior core fix (#277677) changed **`QRPTS_SETTLE_GAS_STMT_PROD_VW`** (non-posted) but **not** `QPOST_SETTLE_GAS_STMT_PROD_VW` (posted); crystal alloc-gallons formula didn't look at TIK volume like shrink does | Apply same change to the **POSTED** view + crystal; alloc gallons = theo × fixed recovery, include TIK |
| **#1665714** | CHD | Core gas statement: condensate **theoretical = allocated** (identical) under Plant Volume Info | Crystal formula wrong for allocated condensate (DB view returned correct values) | Corrected crystal formula in `Quorum.TIPS.Reports` (PR 97132) |
| **#1411812** | Fundare | Liquid line (e.g. Condensate) **suppressed when allocated/settled gallons = 0** even though theoretical > 0 | Crystal suppressed all-3-zero AND zero-settled rows | Show liquid rows where theo > 0 even if alloc+settle = 0, **only for liquids on the CCT** (don't show every liquid); keep hiding all-three-zero |
| **#1783561** | IAC (Cimarron) | **C6+ / Hexanes+** Mol%/GPM rolled into "Other" after 2024.10 upgrade | Measurement "massaged" for the gas statement dropped Hexanes+; client GAS_STMT.RPT (copied from DCP) | Client-specific crystal fix; *(note: caused by config change, not the build per dev)* |
| **#1773030** | MOM | **Report Distribution** Gas Statement includes BAs that should NOT get a statement; all get Petroquest's PDF | Distribution view only filters out the **NP** statement-format-code → BAs whose statement format is IV (invoice) still pass | View filter corrected to exclude non-gas-statement BAs |
| **#1774952** | MOM | Gas Statement report **25+ min** only when **"View Contract Summary"** checkbox ON, only on client side | Report/query perf on the contract-summary path; MT timeout | Perf tuning; deploy `QTIP_17.0.00.0026.0000_00_CORE_QTIP_21_1622682.sql` |
| **#1614317 / #1622136** | MOM | Invoice/Imbalance statement: add fuel buckets so imbalance ties; **net-0 PPAs** still showing on Invoice Detail | BL01 report + `QRPTS_/QPOST_RPTS_INVOICE_IMBAL_VW` missing columns / not suppressing 0 PPAs | Add GROSS_REC/FUEL_REC/FUEL_DEL/NET_DEL columns; suppress net-0 PPAs on Invoice Detail |

**Fix recipe:** (1) Determine **posted vs non-posted** — reproduce on both; if only posted is wrong, the `QPOST_RPTS_*` view/crystal didn't get the fix. (2) Determine **client vs core** — find the `.RPT` file name (core `SETTLE_GAS_STMT.rpt` / `GAS_STMT.RPT` vs client copy) and the source view schema (`QRMTIPS` core vs `ESUITE_Q<CLIENT>`); the fix must land in **both** the crystal and the source view, on **both** posted and non-posted, for **both** core and the client. Reports live in `Quorum.TIPS.Reports` (+ `<CLIENT>.TIPS.Metadata` / `.Database`).

---

## 5. Cluster B — Settlement batch failures (GAS_STMT proc / row-width)

**Signature:** the **SETTLE / Contractual Settlement** batch errors at the **GAS_STMT** step with a generic "can't access stored procedure `SP_QTIP_RPT_SETTLE_STMT`".

- **#1672304 / #1672793 (SRB, 24-00965359 / 24-00966118):** The statement table **`QTIP_RPTS_SETTLE_STMT` has 538 columns, mostly variable-length VARCHARs.** The proc's chained `UPDATE … SET TAX_TYPE_DESCR_1/2/3 = …` statements push the **total row data width past the SQL Server limit**, triggering **MSSQL Msg 611** (a known SQL Server bug with **clustered/columnstore index** present — Microsoft KB4045814). 
  - **Workaround (immediate):** truncate the `TAX_TYPE_DESCR_[1/2/3]` update values to ~20 chars (gets through the month); SRB uses all-state tax breakout so the descr fields are long.
  - **Alternate:** **drop the PK clustered index** on `QTIP_RPTS_SETTLE_STMT` and replace with a non-clustered unique constraint on (`TRNX_ID`, `MTR_SFX`) — removes the clustered index that triggers Msg 611.
  - **Long-term (Travis/Cristina):** **split the wide table into ≥2 tables joined by a view** named `QTIP_RPTS_SETTLE_STMT` so the reports/proc don't change. Closed when SRB moved to the new QCloud 1.5 / TIPS-upgrade environment. *Fixed-in-build: client environment upgrade, not a core GA — confirm in release notes.*

- **#131305 (ENT — Rejected):** "TIPS Settlement Failing / Oracle Version" on a v17 2019.03 build after the client upgraded Oracle client/DB 12.1→12.2. **Not a product defect** — resolved via the Oracle client/DB version guidance (see WI 146456). Dead end as a code fix.

**Fix recipe:** for a SETTLE-at-GAS_STMT crash, get the exact SQL error. If **MSSQL Msg 611**, it's the wide-table row-width issue (#1672304) — apply the truncation or drop-clustered-index workaround, escalate the table-split as the permanent fix. Rule out an environment/Oracle-version mismatch (#131305) before assuming a code defect.

---

## 6. Cluster C — Settlement Invoice & CO&O / Plant-Performance reports

| Bug | Client | Symptom | Root cause | Fix |
|---|---|---|---|---|
| **#1767237** | SRI (CAN) | **Settlement Invoice report shows duplicate fee values** | Meter split with the **same contract on both suffixes (A & B)**; `QRPTS_SETTLE_INV_DTL_VW` **QTRAN_PAYSTATION join lacks an `MTR_SFX` filter** → each split joins to both → duplicate rows | Add `MTR_SFX` to the QTRAN_PAYSTATION join in the view |
| **#1736767** | PEM | **Facility Ownership Terms → CO&O / Plant Ownership report Rate & Excess charge = 0** when a **Revenue Rate Schedule** is used (manual Revenue Rate works) | (a) Rate schedule is type **Fee**; CO&O resolution needs type **Price**. (b) On MSSQL, a **missing registered SQL `Sel_H2SCO2_PCT`** caused `PLANTOWN` "Operating system errors" | **Workaround:** set the rate schedule to type **Price**. **Code:** added `Sel_H2SCO2_PCT` SQL compatible with ORA + MSSQL so PLANTOWN runs |
| **#1430998** | DCP | **Plant Performance reports wrong NGL/residue with PPAs** | `QRPTS_PLANT_PERF_CTGRY` logs the perf data under the **PPA production month instead of the current accounting month** | Code fix to log under current month (client patch) — workaround was reruns per PPA month (infeasible at scale) |
| **#1578332** | UTG | **Plant Performance Liquids Report (74B)** missing prior-month/12-mo-avg/YTD data; daily client | Report/views weren't handling **daily** runs; null-handling gaps; YTD avg formula confusion | Better null handling + views look at **monthly** records only (UTG ultimately reverted to the core monthly report) |
| **#177330** | PEM | Settlement Invoice Report **formula error** | Bad report template | Replaced with the working report template (hotfix, report-only) |
| **#1609124** | PEM | Settlement Invoice **(108)** "Less original invoice" line wrong on **PPA** — excludes Plant Product Purchase | Client view `ESUITE_QPEM` + `SETTLE_INVOICE_PEM` report only pulled `AMEND_INV_ALL_FEE_TOTAL`, not `AMEND_INV_ALL_PROD_TOTAL` | View + report change to include the product total in the "Less invoice" line |
| **#1678622** | HVM | Gas Statement **"Cust Settlement Liquid Val" total blank** when one liquid (Normal Butane) is empty | Crystal total formula fails on an empty liquid | Crystal fix (client patch) |

**Fix recipe:** Settlement Invoice duplicates → check meter-split same-contract + the `MTR_SFX` filter in `QRPTS_SETTLE_INV_DTL_VW` (#1767237). CO&O rate=0 → verify rate-schedule **type = Price** (#1736767). Plant-perf PPA mislogging → `QRPTS_PLANT_PERF_CTGRY` month (#1430998). All are client-report-heavy — confirm core vs client.

---

## 7. Cluster D — Override Revenue Flag screen

The Override Revenue Flag screen is a recurring trouble spot, in three flavors:

**(a) Screen errors / `ORA-01013` / disconnect / "needs services restarted" — intermittent, self-healing.**
- **#1658025 (IAC, 24-00951708)** and **#1665332 (IAC, 24-00957493, RCA)** and **#1623239 (IACX, 23-00921964 — Rejected):** querying the screen throws `ORA-01013` (user-cancel/timeout); fixes itself after a while; service restart often clears it. **Root cause (#1665332):** IAC posts their plants leaving `QTRAN_PAYSTATION` / `QTRAN_ALLOC_VOL` **empty for days**, so nightly stats are gathered on **0 rows**; when the next month's data lands, the optimizer stats are **stale** and the screen query takes ~36s, over the **30s ClassicGUI timeout**. **This is the same stats-on-empty-tables root cause as the JOURNALIMB perf bug #1598509.**
  - **Immediate fix:** bump the **ClassicGUI query timeout 30 → 60s** in `IAC.TIPS.Application.ClassicGUI` ini (was done manually first; needs a PR to persist).
  - **Long-term:** add a **stats-recalc step** after ALLOCATE (mirroring the `CALC_STATS` step added to JOURNALIMB).
  - **Logs:** the screen is **C++ (ClassicGUI)** and does NOT touch the Middle Tier, so MT logs are useless — capture **TIPS ClassicGUI / QTRACE** logs while failing.

**(b) Web Override Revenue ≠ Classic / missing grid columns.**
- **#1726832 (DCP, 25-01015459):** Web shows fewer records than Classic — root-caused & fixed (grid/query), 2024.10/2025.04/develop.
- **#1783101 (ONM, 25-01045663):** Web grid missing `SYSTEM_CD` & `MTR_CTGRY_CD` (a prior feature #1584617 accidentally added CtrPartyBaNo/Suf instead) — fix SOA grid def 53077. CAN Web still showed no data (logged separately).

**(c) Revenue doubling / wrong Revenue Indicator.**
- **#1709416 (ETP, 25-00998597 — "Double volume found from revenue data"):** Revenue **summed ALL volumes in the iteration including CALC_ONLY rows**. **Fix:** only sum volumes where **`CALC_ONLY_IND = 0`**. Config `IGNORE_CALC_ONLY_IND` toggles behavior (TRUE = don't double). PRs to **2020.03** + develop. *(inferred fixed-in-build: 2020.03 line — confirm in release notes.)*
- **#1355919 (IAC, 20-00094218 — "Revenue Override not calculating correctly"):** Two intertwined problems: (1) a **duplicate open-ended meter timeslice** on the Revenue Control screen inserted **duplicate rows into QTRAN/QPOST_REVENUE**, doubling the "Prior Amount"; (2) the **Revenue Indicator** was wrongly set for **0-difference PPAs and waived-fee meters**. **Fix:** delete the duplicate timeslice + dedupe `QPOST_REVENUE` (script `delete_identicals_QPOST_REVENUE.sql`), correct the **PPA revenue-ind SQL** (PPAs are in a different prod month so the run's PROD_DT filter missed them) and exclude **waived fees** from the prior-amount calc. Logic lives in **`IAC.TIPS.ClassicBatch\QPDllTipsSettle\QSQL_TipsSettleIAC.cpp`** (SQL vars `m_Updt_Paystation_Rev_Ind_*`), executed in `QPSSettleReversals.cpp`. Note: this prior-amount query is **custom DCP code copied to IAC** — verify which client. Roadmap note from dev: `QTRAN_REVENUE` has **no primary key**, which let the duplicates in silently.

**Fix recipe:** screen errors → restart services + bump ClassicGUI timeout + plan a stats recalc; grab ClassicGUI/QTRACE logs (NOT MT). Web≠Classic → grid/SOA definition. Doubling → first rule out a **duplicate meter timeslice** (data) and the **CALC_ONLY_IND** summation (code), before assuming an allocation bug.

---

## 8. Cluster E — Revenue export / transfer / reversal

| Bug | Client | Symptom | Root cause | Fix |
|---|---|---|---|---|
| **#1682234** | CHD | **Revenue Export to BOLO**: Gas & Prod Tax = 0 for 5 new meters (condensate tax OK) | Client revenue SP driven by **`USR_DEF_2` (POP / NONPOP)** in `QCTRL_MTR_SPLIT_DTL`; the 5 meters' field was not set to POP | Data fix (set USR_DEF_2 = POP, rerun) + **expose the column** on the Meter Split screen renamed **"POP"** (client metadata, classic + web) |
| **#127302** | ONM (SWK) | **REVTRAN → Revenue Reversal step fails** inserting NULL into QDOD | Client SP `ESUITE_ONK.SP_QTIP_REVENUE_REVERSAL` (last touched 2014) missing **COALESCE around `S_decimal`** on some INSERT statements; new no-split meter-split rows produced NULL S_decimal | Add COALESCE around all S_decimal inserts (client SP, low risk) |
| **#1724527** | DCP | **Revenue Transfer to QDOD IFACE report fails** — "Formula name cannot have @" | **Crystal Reports 2016 upgrade** rejects "@" in a formula/parameter name | Rename the param (TAX_AMT), update `DCP.QDOD.Metadata` `QARCH_RPTS_PARAM`; known CR2016 upgrade issue (see CR Upgrade Tool wiki) |

**Fix recipe:** BOLO tax-0 → check the client meter-split `USR_DEF_2`/POP flag (#1682234). QDOD NULL insert → client revenue/reversal SP missing COALESCE (#127302). "@"-in-formula failures → CR2016 upgrade (§13).

---

## 9. Cluster F — Journal output wrong (config)

Most "journal missing / wrong column" cases are **configuration on Journal Entry Control** or **CAN column-width drift**, not engine bugs.

| Bug | Client | Symptom | Root cause | Fix |
|---|---|---|---|---|
| **#1776599** | SRI (CAN) | **JOURNAL fails** "String or binary data would be truncated … `JE_COND_CD_VALUE`" | **CAN journal table char-limit drift**: `QTRAN_JOURNAL_ENTRY_CAN.JE_COND_CD_VALUE` was 12 chars while the QRMTIPS (non-CAN) version was wider; multi-value conditions (`1064,1055,10…`) overflow | **Widen `JE_COND_CD_VALUE` 12 → 200** chars in the CAN table; PRs to release + 2025.10 |
| **#1725846** | DCP | Web **Journal Entry Control missing core columns** (ACCOUNT_NO_2, COST_CENTER_2, CO_CD, AFFILIATE_BUSN_UNIT, PRODUCT_TYPE_CD, BUSN_UNIT, PROCESS_CD) needed for Rev-Rec | Rev-Rec (ASC606) columns existed in Classic/core DB but were **never added to the Web grid** | Add columns to Web `QCTRL_JOURNAL_DTL` grid + DCP override grid def; 2024.10 hotfix |
| **#1414541 / #1430003** | PEM | Web Journal Entry Control missing **"Exclude 0 Value/Volume"** and **"QTY UOM Code"** columns (present in Classic) | Web grid def incomplete vs Classic | Add the missing columns to the Web grid (client metadata, PEM 2021.04 hotfix) |
| **#1787043** | SRI | Journal Entry Control **user-def field** not brought from Classic to Web | Web grid def | Bring the UDEF column to Web |
| **#1806658** | HEC | **POSTPLANT** job blocked by a **JOURNAL dependency check** (Hilcorp doesn't run JOURNAL) | Hard-coded dependency-check that shouldn't apply | **Remove the JOURNAL dependency from POSTPLANT** (HEC.TIPS.Metadata) |

**Fix recipe:** journal "missing for a meter" → check the **Journal Entry Control condition** (missing/doubled). CAN journal truncation → widen the `_CAN` table column to match QRMTIPS (#1776599 — a recurring CAN-vs-core drift). Missing Web column → add to the `QCTRL_JOURNAL_DTL` grid def (core + client override).

---

## 10. Cluster G — Journal reversal / sign / split / netting defects (code)

A distinct **code/view** cluster around reversals, sign handling, split logic, and offset netting.

| Bug | Client | Symptom | Root cause | Fix |
|---|---|---|---|---|
| **#1640286** | PEM | **Reversal records missing from Functional-Unit (FNC) Journal** on a PPA; PPA journal doesn't balance | Meter (`MTR`) journals use `QTRAN_PAYSTATION_JRN_VW` (joins posted tables, handles reversals); **FNC journals use the plain `QTRAN_PAYOWNER` table** with no reversal logic — a miss when SemCAMS was merged into Pembina | Add a Pembina `QTRAN_PAYOWNER_JRN_VW` (mirroring `SEM_QTRAN_PAYOWNER_JRN_VW`) with reversal logic + sysgen; merged 2022.10/2023.04/develop |
| **#1445610** | PEM (CAN) | **GST not reversing on Journal Entry Report** for PPAs | Reversal entries in `QTRAN_JOURNAL_ENTRY_CAN` had **0 journal values**; report views (`QRPTS_JOURNAL_ENTRIES_ROLLUP` / `QPOST_RPTS_JRN_ENTRIES_ROLLUP`) need the tax-reversal source | **Sysgen addition for `QTRAN_SETTLE_TAX_JRN_VW`**; 2021.04 + 2022.04 + develop |
| **#260736** | ONM/IAC (QDOD) | **QDOD Journal Split excludes records** — JE Summary ACH total ≠ Recon Report | Split where-clause `OA_RANK > n*(total/splits)` relied on Oracle truncating `(2+1)*(4564/3)=4563.999…`, so a boundary record was dropped | Rewrote split to assign **sequentially** instead of by chunk; cast to float / CEILING for MSSQL integer-division (collateral #1404419) |
| **#1404419** | ONM (QDOD) | Collateral from #260736: 3-way split **triples** volumes/values | MSSQL integer division rounds the split size down before CEILING | Cast one operand to float before division in the MSSQL split SQL |
| **#1355571** | core (OGSYS) | **JEOGSYSEXP** offset doesn't net to zero → OGSQL balance errors | One **offset record maps to multiple JE records** for the same meter/well; the offset = negative sum of all, doesn't net each line | Fix in **`Quorum.TIPS.Batch / QPDllTipsIntegrationQGSys / QJournalEntry.cs`** (~lines 235-266) so offsets net per line; 2021.04 |
| **#200855** | ONM | **Plant Journal Summary (RPT_57B)** shows negative debit/credit when a credit fee (SERVCR/LOCAL_CR) offsets a regular fee | Report sign convention | Functional change: show a negative debit as a positive credit and vice versa |
| **#171787** | ONM | Journal Summary Report lumps **PPA totals into current-month** subtotals | Report doesn't separate current vs PPA month | Report change to separate current-month and PPA totals |
| **#1590537** | core (QGM) | Journal process logs **too many "missing spec" errors** (incl. 0-vol/0-val rows) | Logs every record incl. zero-volume/value | Only log records with a volume and/or value |
| **#1659042** | HPE | Journal Entry **export incorrect formatting** | Export formatting (QGM/TIPS journal) | Export fix *(TIPS-adjacent financial; see §17 overlap)* |

**Fix recipe:** reversal/GST/tax-not-reversed → check the journal **rollup views** (`QRPTS_/QPOST_RPTS_JRN_ENTRIES_ROLLUP`) and whether the reversal source view/sysgen exists (#1445610, #1640286). Split tripling/excluding → the **integer-division rounding** in the QDOD split SQL (#260736/#1404419 — Oracle vs MSSQL behave differently, test both). OGSYS offset → `QJournalEntry.cs` per-line netting (#1355571).

---

## 11. Cluster H — Journal batch failures (performance & transfer)

| Bug | Client | Symptom | Root cause | Fix |
|---|---|---|---|---|
| **#1598509** | IAC | **JOURNALIMB takes hours** on the **1st re-run** of a month (subsequent reruns fine); slow on `SQLID_SEL_SETTLE_FEE`/`_SETTLE_SUMMARY`/`_ALLOC_VOL` | IAC has only 2 plants; after posting, `QTRAN_*` tables sit **empty for days**, so **nightly stats are gathered on 0 rows**; when the rerun loads data the explain-plan is wildly off (`QTRAN_SETTLE_SUMMARY_JRN_VW`). Same family as Override-Revenue #1665332 and earlier #1096923 | Add a **`CALC_STATS` step** at position 2 of the JOURNALIMB process so stats are regathered before the heavy selects. **Client-managed layer** — IAC must add the step manually after the patch (can't deliver client-layer metadata in a patch) |
| **#264997** | KEY (CAN) | **Journal Transfer** file has the wrong `CREATE_USER` (the runner, not `QRMTIPS`) | Client proc `ESUITE_QKEY.QPPJRNTRN_FM` line 119 / `QPIBS_JOURNAL_FM` line 179 passed `jrn.user_id` | Set create-user / user id to **`QRMTIPS`** in the client proc; 2021.04 |
| **#1672304/#1672793** | SRB | SETTLE/GAS_STMT step crash (Msg 611) | (see §5) | (see §5) |

**Fix recipe:** "journal/journalimb slow only on 1st rerun" → it's the **stale-stats-on-empty-TRAN-tables** pattern (#1598509). Quick fix: gather stats on `QTRAN_PAYSTATION`/`QTRAN_ALLOC_VOL`/settle tables before the run; permanent: a `CALC_STATS` process step (mind client-managed layers). Journal-transfer create-user/datatype crashes → the client `QPPJRNTRN_FM` / `QPSJournalTransFM` proc.

---

## 12. Cluster I — Rate schedule / fixed fuels / settle-fees calculation

| Bug | Client | Symptom | Root cause | Fix |
|---|---|---|---|---|
| **#1708209** | EQT | **Settle Fees not generating for select days** (21, 23, 27, 29) | Those days have **0 volume on the MESD (Measured Delivery) disposition** → the rate formula crashes/zeros; split-decimal `EFF_PCT_CONTR` = 0 for a meter suffix (basis-qty mismatch) | **Config:** set **`PROGRESSIVE_ROUNDER_NO_BOUND_CHECK` = 1** on EQT's Quorum-managed layer |
| **#1722183** | core | **Settlement Calculation (Web)** Fixed-Fuels rows missing the fuel **description** ("/ /" blank) that Classic shows | Web didn't include `P_PRODUCTDESCRIPTION` / `D_DISPOSITIONDESCRIPTION` in the data object → null bindings | Add the two properties + joins in `QpostFixedFuel` via **`TIPS.cg`** codegen; **non-posted** only; 2025.10 |
| **#1770839** | ETP | Same Fixed-Fuels description blank **only for POSTED** transactions | #1722183 fixed non-posted; **`QpostFixedFuelsDO.cs`** still didn't map the two description props for posted | CodeGen change in `QpostFixedFuel` (TIPS.cg) adding the props + joins for posted; 2024.04 |
| **#1551800** | core (V2UI) | Settlement Calc **Processing-Rights tooltip** doesn't show the formula calc | **Bootstrap 3.3.7** (bundled with V2UI) doesn't render the `<table>` in the tooltip `data-content` | UI fix to render tables in popovers (related #1688475); release |
| **#1575813** | core | Report generated, fee not displayed for a meter (AT test case) — **not reproducible**, closed | — | Dead end (no AT impact) |

**Fix recipe:** "settle fees missing for some days" → check the **disposition volume = 0 crashing the formula** and the split-decimal/`EFF_PCT_CONTR` (#1708209; config `PROGRESSIVE_ROUNDER_NO_BOUND_CHECK`). Fixed-fuels description blank on Web → `TIPS.cg` / `QpostFixedFuelsDO.cs` (non-posted #1722183, posted #1770839 — verify both).

---

## 13. Cluster J — Reporting infrastructure

Cross-cutting report-execution defects (not value logic).

**(a) Crystal Reports runtime upgrades (CR2016 / CR2025) — a recurring wave.**
- **#1681547 (TIPS CAN, various reports):** report export fails **"A boolean is required here … errorKind {QTIP-RPT_…}"** on Equalization/Allocation/Tier reports; reproducible in **CR2025 upgrade testing**. Fix: correct the crystal **Record Selection** formula; fix MSSQL view column names (`QRPTS_MARKETING_VOL`); a stray client report (`ALLOC_ANAL_COMP.RPT` Meter Analysis by Month) was **missing from the report path** → remove its dangling CORE metadata def. 2026.08.
- **#1672951 (DTM, 24-00963876 — BL01 Invoice Documents fails for EXTERNAL users):** collateral from #1352683 which added `APPLIED_RATE` to the report but **not to the external `_XVW` views** (`CRPTS_INVOICE_DTL_XVW`, `QPOST_RPTS_INVOICE_DTL_XVW` + source views). Fix: add `APPLIED_RATE` to all external views (DB script must add to **source view before** the `_XVW`); merged 2019.10–develop.
- **#1679586 (NM Final Severance Report):** report execution failing on Web; crystal change; 2024.21/release.
- **#1662005 (QRegReportsLib won't build in VS2022):** `mscorlib.dll` assembly-path compiler change (CMake issue 22583); build fix. 2024.09.
- **#1724527 (DCP):** "@" in a formula/param name rejected by CR2016 (see §8).

**(b) Report ignores a parameter.**
- **#1611648 (ONM, 23-00908788 — Liquid Allocation by Product 10B ignores Prod_Cd):** Classic had an **"Ignore Param" checkbox** that set the Component-Code param to `IGNORE`; **Web has no such checkbox**, so leaving Component blank returned **all** products. Fix: default the Component-Code param to `IGNORE` via a crystal formula (`IF {?IN_COMP_CD}='' THEN 'Ignore' …`) + `QCRReport.cs` null-param handling; applied to **core AND ONM client report** (initial FVF was core-only). 2022.10.
- **#1612921 (ONM, OC532/37B Contractual Gross Value Residue):** Web "Settle Rpt Qty UOM" dropdown returns **NO DATA** (required param) → can't run. Cause: SOA .NET **code table 53006 has no Connection**; related #1585680. Fix: re-sync the report def to the process def (client-managed reports need manual re-sync). 2022.10.
- **#1324962 (KEY, CAN Tier1 Allocation Report):** H2O details missing on report though data is in `QTRAN_/QPOST_ALLOC_VOL` — the services change was made to the **client report only, not deployed to CORE CAN**; posted views (`QPOST_RPTS_TIER1_ALLOC_VOL_VW` etc.) had no data. Fix: apply the H2O/decimal change to the core CAN report. 2021.04.

**(c) Report Distribution / QEMAIL.**
- **#1613498 (ALT, 23-00904297):** running reports 121 & 200 via Report Distribution → recipient gets **only the 2nd report, twice**, never the 1st. **Root cause:** bad setup in **`QCODE_RPT_DISTR_DTL`** + the **event detector was not active**. **No code change** — activate the event detector + fix the distribution-detail setup (one-time script in `ALT.TIPS.Database`).
- **#1773030 (MOM):** Report Distribution includes BAs that shouldn't get a Gas Statement (§4).

**Fix recipe:** report **won't export / boolean error / build failure** → suspect the **Crystal upgrade** (CR2016/CR2025) and check the **Record Selection formula** + whether the report is even in the path. External-user report failure → check the **`_XVW` external views** for a missing column added to the base report (#1672951). Param ignored in Web → the missing **Ignore-Param** default (#1611648) or an empty **code-table connection** (#1612921). Report Distribution dup/no-email → **`QCODE_RPT_DISTR_DTL` + event-detector active flag** (#1613498), no code.

---

## 14. Fix-Version Matrix

> IntegrationBuild is empty on all; "Fixed-in-build" below is **inferred** from iteration/tags/PR-target-branches and **must be confirmed in `Quorum.TIPS.ReleaseNotes`**. "client patch" = shipped as a client-specific hotfix, not a core GA.

| ADO # | Cluster | Symptom (short) | State | Client | SF Case | Fixed-in-build (inferred) |
|---|---|---|---|---|---|---|
| #1354249 | A | SCX gas stmt shrink/theo/gas-lift | Closed | SCX/core | — | 2020.11–2021.10 + develop (client+core) |
| #1434950 | A | FR gas stmt alloc gallons POSTED+TIK | Closed | SCX/core | 22-00824910 / 22-00219951 | 2021.10 + 2022.04 (POSTED view fix) |
| #1665714 | A | CHD condensate theo=alloc | Closed | CHD | — | 2023.04 (Quorum.TIPS.Reports) |
| #1411812 | A | Fundare 0-gallon liquid suppressed | Closed | Fundare/core | — | 2021.04 + 2021.10 + develop |
| #1783561 | A | IAC C6+/Hexane+ → "Other" | Closed | IAC | 26-01069756 | client patch (2024.10 line) |
| #1773030 | A | MOM report-dist wrong BAs (gas stmt) | Closed | MOM | — | 2025.04 + develop |
| #1774952 | A | MOM gas stmt 25-min perf | Closed | MOM | — | 2025.04 (CORE_QTIP_21 script) |
| #1614317 | A | MOM invoice fuel buckets | Closed | MOM | 23-00913815 | 2022.10–2023.04 + develop |
| #1622136 | A | MOM net-0 PPAs on invoice detail | Closed | MOM | 23-00916681 | 2022.10 + up |
| #1672304/#1672793 | B | SRB SETTLE GAS_STMT Msg 611 row-width | Closed | SRB | 24-00965359 / 24-00966118 | client env upgrade (QCloud 1.5) |
| #131305 | B | ENT settle fail (Oracle 12.2) | Rejected | ENT | — | n/a (env, not code) |
| #1767237 | C | SRI settlement invoice duplicate fees | Closed | SRI (CAN) | 25-01055412 | 2025.x (QRPTS_SETTLE_INV_DTL_VW) |
| #1736767 | C | PEM CO&O rate/excess = 0 (rate sched) | Closed | PEM | 25-01024319 | 2021.04 + 2025.04 + release |
| #1430998 | C | DCP plant-perf PPA month mislog | Closed | DCP | 22-00218917 | 2021.10 + 2022.04 + develop (client patch) |
| #1578332 | C | UTG 74B Plant-Perf Liquids daily | Closed | UTG | 22-00821014 | 2022.10 + up |
| #1609124 | C | PEM Settlement Invoice 108 PPA line | Closed | PEM | 23-00895341 | 2023.04 era (client) |
| #1678622 | C | HVM gas-stmt liquid-val total blank | Closed | HVM | 24-00952565 | client patch (2024) |
| #1658025 | D | IAC Override Revenue ORA-01013 | Closed | IAC | 24-00951708 | config (ClassicGUI timeout) |
| #1665332 | D | IAC Override Revenue perf RCA | Closed | IAC | 24-00957493 | config (timeout) + stats step |
| #1726832 | D | DCP Override Revenue Web≠Classic | Closed | DCP | 25-01015459 | 2024.10 + 2025.04 + develop |
| #1783101 | D | ONM Override Revenue Web missing cols | Closed | ONM | 25-01045663 | 2026.04 + back-branches |
| #1709416 | D | ETP double revenue volume (CALC_ONLY) | Closed | ETP | 25-00998597 | 2020.03 + develop |
| #1355919 | D | IAC Revenue Override wrong (dup slice) | Closed | IAC | 20-00094218 | client (IAC.TIPS.ClassicBatch) + data |
| #1682234 | E | CHD Revenue Export BOLO tax=0 | Closed | CHD | 24-00970476 | client metadata patch |
| #127302 | E | ONM SWK revenue-reversal NULL | Closed | ONM | — | client SP (ESUITE_ONK) |
| #1724527 | E | DCP Revenue→QDOD report "@" (CR2016) | Closed | DCP | — | 2024.10 (DCP.QDOD.Metadata) |
| #1776599 | F | SRI CAN journal char-limit truncation | Closed | SRI (CAN) | 26-01066044 | release + 2025.10 |
| #1725846 | F | DCP journal-entry-control Web columns | Closed | DCP | 25-01016226 | 2024.10 hotfix |
| #1414541/#1430003 | F | PEM JEC Web missing columns | Closed | PEM | 21-00215055 / 22-00218093 | PEM 2021.04 hotfix (client) |
| #1806658 | F | HEC POSTPLANT JOURNAL dependency | Closed | HEC | 26-01099529 | client (HEC.TIPS.Metadata) |
| #1640286 | G | PEM FNC journal missing reversals | Closed | PEM | — | 2022.10 + 2023.04 + develop |
| #1445610 | G | PEM CAN GST not reversing | Closed | PEM (CAN) | 22-00253116 | 2021.04 + 2022.04 + develop |
| #260736 | G | ONM/IAC QDOD journal split excludes | Closed | ONM/IAC | 21-00101580 | 2019.10 + 2020.11 + 2021.04 + develop |
| #1404419 | G | ONM QDOD split triples (MSSQL int div) | Closed | ONM | 21-00211190 | 2021.10 + develop |
| #1355571 | G | JEOGSYSEXP offset not netting | Closed | core | — | 2021.04 (Quorum.TIPS.Batch) |
| #200855 | G | ONM Plant Journal Summary 57B signs | Closed | ONM | — | (older GA) |
| #1590537 | G | QGM journal too many missing-spec errs | Closed | core (QGM) | — | 2023.06 era |
| #1598509 | H | IAC JOURNALIMB perf (stale stats) | Closed | IAC | 23-00892948 | client (CALC_STATS step) |
| #264997 | H | KEY CAN journal-transfer create-user | Closed | KEY (CAN) | 21-00101710 | 2021.04 (client proc) |
| #1708209 | I | EQT settle fees missing select days | Closed | EQT | 25-00996960 | config (PROGRESSIVE_ROUNDER…) |
| #1722183 | I | Fixed-fuels desc blank (non-posted) | Closed | core | — | 2025.10 |
| #1770839 | I | ETP fixed-fuels desc blank (posted) | Closed | ETP | — | 2024.04 |
| #1681547 | J | TIPS CAN reports boolean (CR2025) | Closed | CAN core | — | 2026.08 |
| #1672951 | J | DTM BL01 external _XVW missing col | Closed | DTM | 24-00963876 | 2019.10–develop |
| #1611648 | J | ONM 10B ignores Prod_Cd | Closed | ONM/core | 23-00908788 | 2022.10 + up |
| #1612921 | J | ONM OC532/37B Web UOM dropdown empty | Closed | ONM | (TP159394) | 2022.10 + 2023.04 |
| #1324962 | J | KEY CAN Tier1 H2O missing (not in core)| Closed | KEY (CAN) | — | 2021.04 |
| #1613498 | J | ALT report-distribution dup/no email | Closed | ALT | 23-00904297 | config/data (no code) |
| #1679586 | J | NM Final Severance report fails | Closed | core | — | 2024.21/release |
| #1662005 | J | QRegReportsLib won't build VS2022 | Closed | core | — | 2024.09 |

---

## 15. Diagnostic pointers (SQL / views / files)

> **Caveat:** TIPS lives in per-client Oracle/MSSQL schemas (`ESUITE_Q<CLIENT>`, `<CLIENT>_…_QRMTIPS`, `…_QRMTIPS_CAN`). Names below come from the bug repro text — **verify against the client schema**, and always run a verify-SELECT before any UPDATE/DELETE, wrapped in a transaction.

```sql
-- A. POSTED vs NON-POSTED gas-statement view drift (§4): compare the two mirrors
--    If only the posted report is wrong, the QPOST_ view didn't get the fix.
SELECT * FROM QRPTS_SETTLE_GAS_STMT_PROD_VW  WHERE PLANT_NO='<P>' AND PROD_DT='<D>';   -- non-posted
SELECT * FROM QPOST_SETTLE_GAS_STMT_PROD_VW  WHERE PLANT_NO='<P>' AND PROD_DT='<D>';   -- posted

-- B. Settlement-invoice duplicate fees (§6, #1767237): same contract on two meter suffixes
SELECT MTR_NO, MTR_SFX, CTR_NO, COUNT(*) FROM QTRAN_PAYSTATION
WHERE PLANT_NO='<P>' AND PROD_DT='<D>' GROUP BY MTR_NO, MTR_SFX, CTR_NO HAVING COUNT(*)>1;

-- C. Duplicate open-ended revenue timeslice → doubled Override-Revenue prior amount (§7, #1355919)
SELECT MTR_NO, MTR_SFX, TRAN_DTL_TYPE_CD, COUNT(*) dup
FROM QPOST_REVENUE WHERE PLANT_NO='<P>' AND PROD_DT='<D>'
GROUP BY MTR_NO, MTR_SFX, TRAN_DTL_TYPE_CD HAVING COUNT(*)>1;   -- also check QTRAN_REVENUE (no PK!)

-- D. CALC_ONLY rows doubling revenue (§7, #1709416): config + flag
--    IGNORE_CALC_ONLY_IND should be TRUE; sum only CALC_ONLY_IND=0 volumes.
SELECT CALC_ONLY_IND, COUNT(*) FROM QTRAN_REVENUE WHERE MTR_NO='<M>' AND PROD_DT='<D>' GROUP BY CALC_ONLY_IND;

-- E. CAN journal column-width drift (§9, #1776599): JE_COND_CD_VALUE should be wide (200), not 12
SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME='QTRAN_JOURNAL_ENTRY_CAN' AND COLUMN_NAME='JE_COND_CD_VALUE';
-- compare to the non-CAN QTRAN_JOURNAL_ENTRY.

-- F. Plant-performance logged under PPA month instead of current (§6, #1430998)
SELECT PLANT_NO, ACCT_DT, PROD_DT, PERF_CTGRY, NGL_VOL, RES_VOL FROM QRPTS_PLANT_PERF_CTGRY
WHERE PLANT_NO='<P>' ORDER BY ACCT_DT, PROD_DT;   -- red flag: rows under the PPA prod month

-- G. Wide statement table row-width crash (§5, #1672304): count columns / see VARCHAR bloat
SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='QTIP_RPTS_SETTLE_STMT';  -- ~538

-- H. Journal-transfer create-user wrong (§11, #264997)
SELECT DISTINCT CREATE_USER FROM QSTAG_JOURNAL_FM WHERE PLANT_NO='<P>' AND ACCT_DT='<A>' AND PROD_DT='<D>';
-- should be 'QRMTIPS', not the runner's id.

-- I. Report-distribution dup/no-email (§13, #1613498): bad QCODE_RPT_DISTR_DTL + inactive event detector
SELECT * FROM QCODE_RPT_DISTR_DTL WHERE RPT_ID IN ('121','200','242');
-- also verify the report-distribution event detector is ACTIVE.

-- J. External-user report missing column (§13, #1672951): APPLIED_RATE on _XVW
SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME IN ('CRPTS_INVOICE_DTL_XVW','QPOST_RPTS_INVOICE_DTL_XVW') AND COLUMN_NAME='APPLIED_RATE';
```

### Code / repo locations (from PR target branches in the threads)
| Symbol / report | Repo / path | Cluster |
|---|---|---|
| Gas-statement & settlement-invoice crystal reports | `Quorum.TIPS.Reports` (+ `<CLIENT>.TIPS.Metadata` / `.Database` client copies) | §4, §6 |
| `SP_QTIP_RPT_SETTLE_STMT` / `QTIP_RPTS_SETTLE_STMT` (538-col table) | `<CLIENT>.ESUITE.Database` procedures | §5 |
| Override-Revenue prior-amount SQL `m_Updt_Paystation_Rev_Ind_*` | `IAC.TIPS.ClassicBatch\QPDllTipsSettle\QSQL_TipsSettleIAC.cpp`; exec in `QPSSettleReversals.cpp` | §7 |
| Revenue-reversal SP (COALESCE) | client `ESUITE_Q<CLIENT>.SP_QTIP_REVENUE_REVERSAL` | §8 |
| `QJournalEntry.cs` (OGSYS offset netting) | `Quorum.TIPS.Batch\QPDllTipsIntegrationQGSys\` | §10 |
| Journal-transfer proc | client `ESUITE_Q<CLIENT>.QPPJRNTRN_FM` / `QPIBS_JOURNAL_FM`; `QPSJournalTransFM` (client `.ClassicBatch`) | §11, §8 |
| Fixed-fuels description codegen | `QpostFixedFuelsDO.cs` / `TIPS.cg` (codegen) | §12 |
| `QCRReport.cs` (null-param record-selection) | TIPS QFC reporting layer | §13 |
| `QRegReportsLib` (C++ regulatory report build) | `Quorum.TIPS.ClassicBatch\Common\QRegReportsLib\` | §13 |

---

## 16. Escalation Guidance

**Route to Engineering (code/view defect) when:**
- A report value is wrong on **correct data** and traces to a **crystal formula or `QRPTS_/QPOST_RPTS_*_VW` view** — but **first** identify posted-vs-nonposted and client-vs-core so the fix lands in all four places (§4).
- A **batch step crashes** from code/proc, not data: SETTLE/GAS_STMT Msg 611 row-width (#1672304), JEOGSYSEXP offset netting (#1355571), QDOD split rounding (#260736/#1404419), FNC/CAN reversal views (#1640286/#1445610).
- A **calculation** is provably wrong: revenue double-volume CALC_ONLY (#1709416), settle-fees-missing-days (#1708209), fixed-fuels-desc (#1722183/#1770839).
- Provide: **FBJS Process-Queue-ID + failing step + exact ORA/COM/SQL error**, client + plant + acct/prod month, the report name + .RPT file + Report-Table-Map (posted/non-posted), and a repro. Confirm fix availability in `Quorum.TIPS.ReleaseNotes` (IntegrationBuild is blank on the WI).

**Handle as Configuration / data (Cloud Ops or Services), no code:**
- **Journal Entry Control** missing/double condition or missing Web column (§9); **CAN column-width drift** (widen the `_CAN` column, #1776599).
- **CO&O rate-schedule type = Price** not Fee (#1736767); **Override-Revenue** duplicate meter timeslice cleanup (#1355919); **BOLO** `USR_DEF_2`/POP flag (#1682234).
- **Report Distribution**: fix `QCODE_RPT_DISTR_DTL` + **activate the event detector** (#1613498).
- **EQT** settle-fees config `PROGRESSIVE_ROUNDER_NO_BOUND_CHECK` (#1708209).
- Note: many client fixes ship on a **client-managed metadata/code layer** and **cannot be delivered in a core patch** — the client must apply the step/override manually (e.g. JOURNALIMB `CALC_STATS` #1598509, OC532 report re-sync #1612921).

**Service-restart first (no code):** Override Revenue Flag "error / can't query / ORA-01013 / hang" — restart app services; **bump the ClassicGUI query timeout** and capture **TIPS ClassicGUI / QTRACE** logs while failing (the screen is C++, MT logs are useless) (#1658025, #1665332, #1623239).

**Crystal-upgrade triage:** a wave of "report fails to export / A boolean is required here / won't build / @-in-formula" right after a **CR2016 or CR2025** upgrade is the runtime upgrade, not the data — check the Crystal Reports Upgrade Tool wiki and the report's Record Selection formula (§13).

---

## 17. Product-overlap caveats & dead ends

- **Mixed Maintenance branch.** `…\Maintenance\Midstream and Transportation\{Customer Service, Professional Service}` holds **both QPTM and TIPS** bugs. The functional title terms here (settlement/journal/revenue/gas-statement/escalation/fixed-fuel) are TIPS-specific, but generic "report"/"revenue" matched a lot of QPTM. The filtering dropped clear QPTM items (nomination/offer/RFS/capacity-release/IPWS/EBB/FERC and QPTM-billing `BLTRAN`/nomination journal). **Pure TIPS product teams** are `\Engineering\Midstream\…\Guardians of TIPS`, `TIPS Samurai`, `TIPS'n Tricks`.
- **Dropped as QPTM (the OTHER product):** **#1554226** ("QPTM — ENTIRE IMBALANCE … Settlement Method calc") is a QPTM imbalance-trading settlement method, not TIPS settlement accounting. **#112435** ("AR — Journal Entry process combines results") is **QPTM Billing** (`CHN.QPTM.ClassicBatch`, `BLTRAN_GL_JRNL`/`BLTRAN_ORA_JRNL_AR`, nomination-driven) — excluded despite "Journal" in the title.
- **TIPS-adjacent financial (QCM/QGM/QDOD), kept with caveat:** **#1714728** (SRC trade-settlement rounding $86,000→$85,999.99) and **#1783800** (DSU QGM journal-vs-payables variance, Rejected — never reproduced) and **#1659042** (HPE journal-entry export formatting) live in the QCM/QGM **financial deal** stack and the **QDOD** journal stack that sit downstream of TIPS settlement. The **QDOD journal-split** bugs (#260736/#1404419) and the **Revenue→QDOD transfer** (#1724527, #127302) are TIPS data flowing into QDOD — included because the defect is on the TIPS side, but the fix repo may be `*.QDOD.*`.
- **Internal QA / parity / "Query Screens (Interactive Reports Replacement)" items** ("2022.10 TIPS Beta Testing", "Exago … Release Testing", "Test Fest", "V2UI", "AT script") are **not customer defects** — they are release-regression/parity findings. They legitimately match the area but should be treated as test-coverage, not field issues. Several deep-read confirmed non-reproducible and were closed (#1575813, #1551800 was a real V2UI Bootstrap fix though).
- **Dead ends:** #131305 (ENT settle fail = Oracle version, not code), #1783800 (QGM variance, closed un-reproduced after >2 months blocked), #1575813 (fee-not-displayed, not reproducible). Don't chase these as code defects.
- **IntegrationBuild is empty on 100% of these bugs** — never quote a build number as fact; cross-check the iteration (YY.NN), the PR target branches in the comment thread, and `Quorum.TIPS.ReleaseNotes`.

---

*Skill created: 2026-06-14. Source: Azure DevOps closed/resolved TIPS Bugs (QuorumSoftware org), both `\Engineering\Midstream` and `\Engineering\Maintenance\Midstream and Transportation` branches. WIQL matched 1,413; ~482 in-area after QPTM-noise filtering; 64 deep-read (description + repro + full comment thread + linked PRs/SF cases). Fixed-in-build values inferred from iteration/tags/PR-branches — confirm in Quorum.TIPS.ReleaseNotes.*
*Companion: SKILL_ADO_QPTM_Reporting_Postings_Regulatory.md, SKILL_ADO_QPTM_Billing_Invoice_Rates.md, and the TIPS Assistant SF-based skills (SKILL_TIPS_Settlement_Revenue_Journal.md, SKILL_TIPS_Reporting_Statements.md).*
