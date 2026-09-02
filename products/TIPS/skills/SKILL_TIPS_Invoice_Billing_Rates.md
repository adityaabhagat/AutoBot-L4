# SKILL: TIPS Invoice / Billing / Rates Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-11 | **Product:** My Quorum TIPS (oil & gas transaction & accounting)
**Scope:** Invoice generation & approval (Facility/Company Batch Job Submittal → SETTLE → INVOICE → JOURNAL/JRNROLUP → POST), Invoice Document reports (BL01/BL01A), Settlement Invoice (RPT 200) & Settle Invoice PEM (RPT 108), gas/settlement statements, Statement Group Maintenance & Invoice Group Maintenance, PPA/rerun reversals, rate schedules, Escalation Schedules (ESCALATE/ESCALP), price/index import (OPIS), fee setup via CCT (Common Contract Terms).
**Use when:** a TIPS case is categorized Invoice / Invoices / Billing / Rates — invoice totals wrong/doubled, lines missing or duplicated, PPA reversal wrong, statement won't print, tax/GST missing, escalation or price index not resolving, fee not populating.
**Companion:** QPTM-side allocation issues → `SKILL_Allocations.md` (PTR/Evolution overlap); QPTM billing → `SKILL_Billing.md`.

> Evidence base: 280 closed TIPS Invoice/Billing/Rates cases — 78 actionable (45 Software Defect, 31 Application Configuration, 2 ChangeConfig) + 70 Training/Customer Error cases for the Expected-Behavior section. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining. 60 of the 280 closed cases have no Root_Cause__c set (see data-quality notes at end).

---

## TABLE OF CONTENTS

1. [Quick Triage Checklist](#1-quick-triage-checklist)
2. [Symptom → Root-Cause Matrix](#2-symptom--root-cause-matrix)
3. [Invoice Doubling / Duplicate Detail Lines (HIGH FREQUENCY)](#3-invoice-doubling--duplicate-detail-lines)
4. [PPA / Rerun — Wrong Reversals & Approval Errors](#4-ppa--rerun--wrong-reversals--approval-errors)
5. [Posted Invoice Missing Data (Tax/GST, Comments)](#5-posted-invoice-missing-data)
6. [Imbalance Statement Section on the Invoice](#6-imbalance-statement-section-on-the-invoice)
7. [Statement Group / Invoice Group / Contact Config](#7-statement-group--invoice-group--contact-config)
8. [Gas & Settlement Statement Content (Custom Formats)](#8-gas--settlement-statement-content)
9. [Rates — Rounding, Decimals, Rate vs Applied Rate](#9-rates--rounding-decimals-rate-vs-applied-rate)
10. [Escalation Schedules & Price/Index Import](#10-escalation-schedules--priceindex-import)
11. [Fees Not Populating — CCT / UOM / Fee Setup](#11-fees-not-populating--cct--uom--fee-setup)
12. [Invoice Generation / Delivery Hard Errors](#12-invoice-generation--delivery-hard-errors)
13. [Expected Behavior / User Education](#13-expected-behavior--user-education)
14. [Known Historical ADO Bugs](#14-known-historical-ado-bugs)
15. [Key Code Objects, Reports & Repos](#15-key-code-objects-reports--repos)
16. [Diagnostic SQL Queries](#16-diagnostic-sql-queries)
17. [Escalation Decision Tree](#17-escalation-decision-tree)

---

## 1. Quick Triage Checklist

```
[ ] 1. Which artifact is wrong — the INVOICE DATA (settle/invoice tables) or just a REPORT rendering of it
       (BL01/BL01A Invoice Documents, RPT 200 Settlement Invoice, RPT 108 Settle Invoice PEM, gas statement)?
       Compare against the Settle Fees / Settle Prod / Settle Summary QUERY screens first — if the query is
       right and the report is wrong, it's the report/view layer, not processing.
[ ] 2. Company/Plant_No + Accounting Date + Production Date + Unit of Timing (D/M)? TIPS is acctg-date-centric;
       PPAs/reruns carry prior production months under a later accounting date.
[ ] 3. Posted or non-posted? Posted invoices read from QPOST_* views; non-posted from QRPTS_* views.
       Several defects exist in only one of the two (22-00824672, 22-00642205).
[ ] 4. PPA/rerun involved? Reversal/corrected-line math has its own defect family (§4).
[ ] 5. Internal or EXTERNAL user running the report? BL01A duplicated all sub-reports per security user
       on the contract party for external users (ADO #1538357).
[ ] 6. Meter under MULTIPLE facilities / meter splits? Missing plant filter multiplies volumes x2/x3/x4
       on RPT 200 CAN (ADO #1761173).
[ ] 7. Web or Classic screen? Statement Group Maintenance contact-validation error is Web-only
       (24-00966603, recurred 25-01062445).
[ ] 8. Was anything changed on the BA / contact / address / contract recently? BA time-slice and
       invoice-group-contact changes silently drop invoice sections/contracts (26-01079729, 24-00980998).
[ ] 9. Custom client report format (HEP/Opportune-era gathering invoice, client gas statements)?
       Most formatting fixes are client-report changes, not core defects (§8).
[ ] 10. Rate issue: is the fee rate itself wrong in Rate Resolution / Settle Fees query (processing problem),
        or only displayed wrong on the document (report decimal/format problem)? (§9 vs §10)
```

### Where does the issue live?
| Entry point / symptom | Likely cluster | First place to look |
|------------------------|----------------|---------------------|
| Invoice totals doubled / duplicate detail lines | §3 | SOA population by acctg date; report view joins; external-user run |
| PPA/rerun reversal or corrected volume wrong | §4 | `QRPTS_INVOICE_DTL_VW`; JRNROLUP; OR/R records |
| Tax/GST/comments on screen but missing from POSTED invoice | §5 | `QPOST_RPTS_*` views; Tax Master/Combo + meter splits |
| Imbalance section missing/wrong on invoice | §6 | BA time-slice on contract; imbalance VW |
| Can't save Statement Group / contract missing from picklist / duplicate-record msg | §7 | Statement Group Maintenance (Web), Copies tab, contract eff dates |
| Gas statement %, gain/loss, residue, component names wrong | §8 | client report enhancement; facility definition reporting category; CCT fixed fuels |
| Rates show wrong decimals / Rate vs Applied Rate | §9 | report format; Core Invoice View columns |
| Escalation resolves wrong/nothing; price import wrong | §10 | Escalation Schedule + index values; ESCALP vs SETTLEMAIN rounding; OPIS-only import |
| Fee not on invoice at all | §11 | CCT effective dates/term flags; Flat UOM config; Invoice Group Copy tab |
| Invoice errors out / won't email / wrong version prints | §12 | dictionary-key defect; SMTP bare-LF; FTP report version |

---

## 2. Symptom → Root-Cause Matrix

| Symptom (message / behavior) | Most common root cause | Fix type | Evidence |
|------------------------------|------------------------|----------|----------|
| Gathering invoice totals **doubling** for a month | Invoice process populated SOA table without considering Accounting Date — two acctg dates (Billing + Scheduling) for same company collide | Code fix (shipped) | 22-00624664 |
| Duplicate detail lines after converting systems from **monthly → daily** allocations | Invoice detail granularity defect post-conversion | Code/report fix | 24-00977223 |
| JIBLink / non-posted totals multiplied (x150/x114) | View joined fees on `fee_grp_cd` only, missing `fee_type_cd` | Code fix (view) | 22-00642205 |
| All sub-reports duplicated when **external user** runs Invoice Documents (BL01A) | Report duplicates per security user on contract party | Code fix 2022.04 (PR 73404) | ADO #1538357 |
| RPT 200 CAN volumes x2/x3/x4 for meters under multiple facilities/splits | `QRPTS_INVOICE_DTL_CAN` missing plant filter | Code fix (hotfix 11/7) | ADO #1761173, SF 25-01049592 |
| Imbalance/billed volumes doubled on BL01 (invoice amount correct) | Crystal summing `WHDV_HV` column in subreport | Code fix | ADO #1733867 |
| PPA/rerun shows **doubled reversal & corrected volume** (amount correct) | `QRPTS_INVOICE_DTL_VW` defect on OR/R records | Code fix (TIPS 2022.04 queue) | 25-01004724, ADO #1724455 |
| Reversal amount wrong when invoice had **Waived** fees / cross-credit | JRNROLUP re-sum didn't respect Collection Method (collateral of #260819) | Code fix | 22-00830869, ADO #1566523 |
| INVOICE APPROVAL errors after PPA advance (contract settle OK) | Approval query not filtering by Unit Time Code for the Run ID | Code fix | 22-00691445 (workaround: manual line, 22-00691444) |
| RPT 108 PPA invoice ignores Plant Product Purchases in prior totals | Report only summed Fee amounts from original invoice | Code fix | 23-00895341 |
| Pooling Detail prior-months section multiplied x4, meter no./name blank | Report format defect (multi-facility) | Code fix | 22-00653984 |
| GST/tax on products calculated in Settle Tax but missing from invoice/RPT 200 | Posted-invoice tax pull defect; patches per build | Code fix/patch | 22-00561532, 22-00570830, 22-00561562 |
| Report comment missing from POSTED invoice only | Posted view lacked comment — new `QPOST_RPTS_INVOICE_RPT_STMT_VW/XVW` created | DB change | 22-00824672 → ADO #1564067 |
| Invoice imbalance section vanished after **updating BA on contract** | Imbalance VW reads only the most recent BA time slice regardless of prod month | Code fix (ticket opened) | 26-01079729 |
| Web Statement Group Maintenance: "You must have at least one contact..." on ANY edit (Classic OK) | Web screen validation defect — recurred across builds | Code fix | 24-00966603 (#1674016), 25-01062445 (#1776617) |
| Statement Group "duplicate record for key" with no visible duplicate | Overlapping statement-group eff-date row (data) | Data fix | 22-00666828 |
| New contract not selectable when adding Statement Group | Contract/statement-group eff-date & setup mismatch | Config | 24-00966818 |
| Contract Extension screen Statement tab shows wrong/unrelated BA# | Screen reads Copies-tab table; empty table → bogus rows (ContactId=0) | Code fix | 24-00966260, ADO #1682312 |
| Gas analysis doesn't add to 100% on statement | Extra components added via statement enhancement (by design for that client) | Explain/config | 25-01028950, 25-01023033 |
| Statement missing entirely for one contract | Facility Definition didn't tie the alloc product (RES/SALE) to a reporting category | Config | 25-01016779 |
| Gain/loss volume missing on statement | Suppression logic suppressed negatives instead of only zeroes | Report fix | 25-01012556 |
| Rates show wrong number of decimals on statements/invoice | Report format (TSP/client-specific decimal masks) | Report fix | 25-01023026, 25-01015135, 23-00912556 |
| Invoice shows Rate instead of contract **Applied Rate** | Core Invoice View / Invoice Document pulled wrong column | Code fix | 22-00663653 |
| Escalation Preview empty / escalated rate slightly off | Misconfigured schedule + missing index values; ESCALP vs SETTLEMAIN rounding mismatch | Config / code | 25-01013611, ADO #1590338 |
| ESCALATE process completes but inserts no records / corrupts CCT-rate time slices | Escalation process defect; needs rollback script + patch | Code + script | ADO #1643313 |
| Imported price off by factor of 100 | TIPS price import supports OPIS format only — Platts files parse wrong | Config/limitation | 26-01070189 |
| Flat fee doesn't populate on invoice | 'Flat' UOM needs Quantity UOM + Flow Direction configured | Config | 24-00985674 |
| Whole fee families missing from settlement invoice | CCT not enabled / expired (e.g. BAN4762F off, BAN4762W expired) | Config | 24-00980129 |
| Core invoice won't generate at all for a group | Invoice Group **Copy tab** not populated | Config | 22-00875660 |
| "The given key was not present in the dictionary" on multiple windows | Build defect | Software update | 25-01022916 |
| All emailed invoices rejected after move to Office 365 | SMTP bare line-feed in generated email | Code fix | 22-00617633 |

---

## 3. Invoice Doubling / Duplicate Detail Lines

The highest-stakes cluster — wrong amounts reach customers. **Always determine first whether the DATA doubled or only the REPORT doubled** (compare Settle Fees / Settle Prod query screens or `QTRAN_SETTLE_SUMMARY` sums vs the document).

### Data-level doubling
- **22-00624664 (Meritage):** Gathering invoice totals doubled for Feb production. Root cause: the Invoice process populated the **SOA table without considering Accounting Date**, so running two accounting dates for the same company simultaneously (Billing + Scheduling) inserted duplicates. Fixed in code; interim prevention = don't run two acctg dates for the same company at once.
- **24-00977223 (EQT):** duplicate detail lines (not aggregated into fee total) appeared on exactly the gathering systems converted from **monthly to daily volume/allocations** that month. Daily-conversion edge in invoice detail generation; resolved via report/subreport filter (follow-up 24-00991180 added a subreport filter for third-party services and hid a redundant subtotal section).

### Report/view-level doubling (data correct)
- **ADO #1538357 (DTM, Closed):** BL01A by Account Manager duplicates Invoice Summary, Remittance Advice, Invoice Detail, and Imbalance Statement **once per security user** tied to the contract party when run by an **external** user. Fix cherry-picked to 2022.04 (PR 73404).
- **ADO #1761173 (SRI 25-01049592, Closed, hotfix):** `QRPTS_INVOICE_DTL_CAN` — product volumes x2/x3/x4 on RPT 200 (CAN) when a meter is assigned to **multiple facilities with meter splits**; the view/report lacked a plant filter. Verify with Settle Prod query (values were 74.8 vs expected 18.7).
- **ADO #1733867 (HEP, Closed):** BL01 Imbalance-statement **billed volumes doubling/tripling** (invoice amount correct) — Crystal displayed `SUM(WHDV_HV)`; core subreport patch.
- **22-00642205 (PGI):** JIBLink attachment totals wrong after V17 upgrade — non-posted invoice-total view joined fees on `fee_grp_cd` only (missing `fee_type_cd`), multiplying totals by the number of fee types in the group (150 Processing / 114 Gathering). Display-only; journal entries were correct.
- **23-00888467 (Opportune):** CICO section showed duplicate lines/false totals — gathering-invoice report updated to dedupe CICO lines.

### Fix recipe
1. Compare document vs Settle queries (§16-A/B). Data right + doc wrong → report/view defect, match the ADO items above and check the client build/patch level.
2. Data actually doubled → check whether two accounting dates ran simultaneously for the company (22-00624664 pattern) and whether the month was a daily-allocation conversion month (24-00977223).
3. Also rule out the **user-created duplicate CTR UOM** pattern (Customer Error, §13) before escalating — duplicated DELVOL UOM produces doubled delivery volumes that look identical to this cluster (23-00925718).

---

## 4. PPA / Rerun — Wrong Reversals & Approval Errors

PPAs/reruns reverse the original invoice lines (OR) and write corrected lines (R). Two distinct failure layers:

### Report layer (most common)
- **25-01004724 / ADO #1724455 (Closed, queued TIPS 2022.04):** upon PPA/rerun the invoice shows **doubled volume on both the reversal and corrected line** (e.g. -58,194 shown where amount math used -29,097 * 3.201). Amounts correct, volumes doubled. Defect in `QRPTS_INVOICE_DTL_VW`.
- **23-00895341 (Pembina):** Settle Invoice PEM (RPT 108) PPA invoices used only **Fee amounts** from the original invoice and ignored **Plant Product Purchases** in prior-invoice total and net totals. Report fixed.
- **22-00653984 (Diversified):** Pooling Detail "previous months" section multiplied correct PPA values x4 and dropped meter no/name.
- **23-00916681 / 23-00898353 (Opportune):** net-0 PPA lines clutter Invoice Detail & Imbalance Statement — suppression logic added (suppress only true net-zero, careful not to repeat the 25-01012556 mistake of suppressing negatives).

### Process layer
- **22-00830869 / ADO #1566523 (NorthRiver):** PPA reversal wrong when original invoice had **Waived** (cross-credit/Acid Gas Adjustment) fees. Collateral damage from **#260819**, which changed NRM's **JRNROLUP** step to re-sum the prior invoice total; the re-sum ignored **Collection Method** and included Waived fees in total/tax. Diagnose with a Settle Fees query filtered to the waived line items — discrepancy equals their sum.
- **22-00691445 / 22-00691444 (NorthRiver):** **INVOICE APPROVAL** errors after a PPA advance (CONTRACT SETTLEMENT step fine). Fix: approval query modified to filter results by the **Unit Time Code** retrieved via the Run ID. Workaround used in production: manually add the line to the invoice.

### Fix recipe
1. Reproduce the math: corrected amount ÷ rate = expected volume; if displayed volume is exactly 2x, it's the #1724455 view defect — check build (fixed in 2022.04 stream).
2. Waived/cross-credit fees on the original? → JRNROLUP/Collection-Method pattern; sum the waived lines and compare to the delta.
3. Approval-step error with clean settlement → Unit-Time-Code/Run-ID query defect (22-00691445); confirm fix version before re-running.
4. Before any of this, verify no duplicate CTR UOM / multiple values per fee type were introduced by the client (25-01055374 — Training, §13).

---

## 5. Posted Invoice Missing Data

Posted invoices read **`QPOST_*`** objects; non-posted read **`QRPTS_*`**. Data visible pre-posting but missing post-posting almost always means the posted view lags the non-posted one.

| Issue | Root cause | Fix | Evidence |
|-------|-----------|-----|----------|
| Report Comment missing from POSTED invoice only | Posted view had no comment column | New views `QPOST_RPTS_INVOICE_RPT_STMT_VW` & `_XVW` | 22-00824672 → ADO #1564067 (dup of 23-00877027) |
| GST in fees missing in posted invoice | Build defect | Patch on 2020.01 | 22-00561532 (Pembina) |
| GST missing for Product Purchases (Hythe) | Earlier fix **not consumed** into client's 2021.04 build | Re-include in build | 22-00570830 |
| Tax on Products absent from Invoice process & RPT 200 though Settle Tax/Journal show it (Tax Master, Tax Combo, Meter Splits all set) | Invoice-side tax pull defect | Code fix | 22-00561562 |
| Invoices not printing all pages / contacts out of sequence | Posting bug | "Package 12 DGO Database Upgrade" patch + posting scripts for prior months | 22-00654006 |

**Triage:** confirm the tax actually computed (Settle Tax query / journal) — if yes, it's invoice/report-side; check the client's build consumed the relevant fix (the 22-00570830 lesson: a known fix can silently miss a client build).

---

## 6. Imbalance Statement Section on the Invoice

- **26-01079729 (EQT, CRITICAL pattern):** imbalance section disappeared from the invoice **after updating the BA on the contract**. Root cause: the imbalance VW **populates only from the most recent BA time slice regardless of the production month being run** — older prod months lose their section. A new defect ticket was opened from this case. Workaround pressure point: month-end sends — check BA time-slice history first when a section vanishes after a contract/BA edit.
- **23-00898808 (Opportune):** Net Receipt quantity differed between Invoice Summary and Imbalance Statement sections — tie-out fix in report.
- **23-00913815 / 23-00916620 (Opportune):** receipt fuel / delivery fuel / net delivery imbalance buckets added to Invoice Summary & Imbalance Statement; "Due Shipper Imbalance" relabeled "Due Shipper/(Due Gatherer) Imbalance". (Client-format evolution, not defects.)

---

## 7. Statement Group / Invoice Group / Contact Config

Statement Group Maintenance assigns which contracts get which statements/invoices and to which contacts; Invoice Group Maintenance (incl. the **Copy tab**) gates core invoice generation. This cluster is mostly **config + one recurring Web defect**.

### The recurring Web defect
- **24-00966603 / ADO #1674016 (ONEOK, Closed)** and **recurrence 25-01062445 / ADO #1776617 (2024.04, Closed):** any add/update on **Statement Group Maintenance in Web** throws *"You must have at least one contact and if there is only one it must be the original contact"* — even valid edits. Classic works. If a client reports this, check patch level for their build line first; it has regressed at least once.

### Config/data patterns
| Issue | Resolution | Evidence |
|-------|-----------|----------|
| "Duplicate record for key 540-GLO-340" with no visible dup | Overlapping statement-group effective-date row — fix the eff dates/remove the orphan row in data | 22-00666828 |
| New contract not selectable adding a Statement Group ID | Contract setup/eff-date vs statement group — verify contract exists for the company & period | 24-00966818 |
| Contract Extension screen Statement tab shows unrelated BA# / dups (Web) | Screen joins through the **Copies tab** table of Statement Group Maintenance; empty Copies tab → garbage rows (ContactId=0). Fixed | 24-00966260, ADO #1682312 |
| Payment Terms value differs Oracle vs MSSQL | Code table 28077 row order differs per platform (metadata) | ADO #1572417 |
| Remit-To / Billing Inquiry contact & address change | Pure setup: BA Company Address + contact on the group | 22-00868181 |
| Contracts vanished from invoice after BA **address** change | Client created new address suffix but didn't update the Contact on the **Invoice Group contact tab** — create new contact with new address, attach, rerun invoice (KB ka0UG0000003F0vYAE) | 24-00980998 (Training) |
| Contract won't print | Create/assign default contact on Statement Group; or statement group missing entirely | 24-00956716, 26-01093064 (Training) |
| Core invoice not generating at all | **Invoice Group Copy tab empty** — populate it | 22-00875660 |

---

## 8. Gas & Settlement Statement Content

Dominated by one Evolution-era client (Howard Midstream/HEP) with heavily customized gas statements — treat these as **client-report changes**, but the patterns generalize:

| Symptom | Root cause / fix | Evidence |
|---------|------------------|----------|
| Gas analysis doesn't total 100% | Extra components were deliberately added to the statement via enhancement — explain, or adjust statement | 25-01028950, 25-01023033 |
| Theoretical Residue "doesn't match" | Setup uses **WHDV_HV allocation rule** (WHDV populates the field); final Allocated Residue ties — education | 25-01027783 |
| Gain/loss volume missing | Statement suppression logic suppressed **negatives**; must suppress only zeroes | 25-01012556 |
| Plant gain/loss doesn't match legacy (Waterfield) | Two-place gain/loss not reproducible via TIPS allocations (circular dependency); recompute using **fixed fuels on the CCT** + settlement Shrink — reporting-only fix | 25-01013000, 25-01027791 (RES/SALE basis changed) |
| Statement missing for one contract | **Facility Definition** didn't tie the allocated product (RES/SALE) to a **reporting category** (was right in UAT, wrong in PRD) | 25-01016779 |
| Cover pages missing from gas statements | Custom-enhancement build issue; patched | 25-01030000 |
| "Natural Gasoline" shown as "Natural Gas"; NGL component names blank | Hardcoded label / missing report condition | 25-01011405, 25-01011652 |
| Wellhead buyback line placement / Res Buyback | Statement layout changes | 25-01015357, 25-01019697 |
| Settlement invoice missing G&PC/G&PV fee sections | **Common Contract Terms** not enabled (BAN4762F) / expired (BAN4762W); also BA "N/A" company missing in QCM | 24-00980129 |

> Cross-check **UAT vs PRD config** (facility definition, reporting categories, CCT flags) before raising a defect — two of the biggest cases here were PRD-only config drift.

---

## 9. Rates — Rounding, Decimals, Rate vs Applied Rate

Mostly **report-format** changes (decimal masks), plus one substantive column bug:

- **22-00663653 (Brazos):** Core Invoice View & Invoice Document pulled the **Rate** column instead of the **Applied Rate** — fixed to use Applied Rate. If a client says "invoice rate ≠ contract rate," check which column the doc displays before suspecting rate resolution.
- Decimal-mask family: SLC statement rates to 4 decimals (25-01023026), Wellhead Purchase price more decimals (25-01015135, 25-01023036 — rounding), fees to 7 decimals to match plant statements (23-00912556), remove decimals from Current Mth Net Activity (23-00913823). All resolved as statement-format updates.
- **ADO #1732345 (Closed):** Escalation Schedules **Fixed Amount/Period** displays a rounded integer in Web while `QCTRL_INFL_SCH` holds the decimal — Web display defect; verify the DB value before believing the screen.
- **23-00916618 (Opportune):** fees with multiple rates within a month displayed wrong — invoice now shows the first production date each rate change applies.

---

## 10. Escalation Schedules & Price/Index Import

Escalation (ESCALATE batch / ESCALP preview) resolves CCT fee rates from index-based or fixed schedules; prices/indices import monthly.

### Config first (most cases)
- **25-01013611 (Howard):** FERC index "not working — Escalation Preview empty" → the **escalation schedule was misconfigured AND the index had no data loaded**. Always check both: schedule setup (Global → Escalation Schedules) and index values for the target dates.
- **26-01064409 (Training):** Facility Batch Job settle error "INDEX CPI not Found" → missing CPI index value; add it and rerun.
- **26-01090489 (Training):** Prompt Sequence missing a value because the **rate schedules under it were end-dated in the latest time slice** — keep the most recent time slice open-ended during testing.
- **26-01091878 (Customer Error):** invoice discrepancy because CCTs weren't set up correctly after the Escalate Rate process errored.

### Known code defects
- **ADO #1590338 (ETP 23-00885983, Closed):** **rounding mismatch between ESCALP (Escalation Preview – BR report, ESCAL_BR) and SETTLEMAIN processing** — preview compounded factor 1.0609 vs processing 1.06 → wrong fee rates. Code path: `QInflationSchedule::InflateRate → DetermineBaseRate → DetermineBaseRateIndex → YearOverYearWithBaseRate` (`dRateApp = dRateStart * dAppInfl`), repo `Quorum.TIPS.ClassicBatch`. Interim client workaround was manual fixed rates on the CCT.
- **ADO #1643313 (AltaGas, Closed):** ESCALATE runs "successfully" but **inserts no records**, and a failed escalate/rollback left CCT/rate time slices in a bad state — required a **one-off rollback script + patch**. Diagnose via `QARCH_QFCBATCH_SQL_TRACE` for the process step queue ID.
- **ADO #1736767 (PEM 25-01024319, Closed):** Facility Ownership Terms **Revenue Rate Schedule** resolves to 0 because the schedule ID had no row in `QCODE_PREDEF_FORMULA`.

### Price import
- **26-01070189 (Opportune/UAT Global):** imported price **factored by 100** — the TIPS price import is built for **OPIS** file format only; **Platts is not supported** (different formatting, different code). Don't chase a rounding bug; it's a source-format limitation.
- **26-01069823 (Howard):** "who changed this fixed rate?" → answer from the **rate audit tables** (provide audit history, not a fix).
- **26-01082569 (Training):** input price field allows only 7 digits before the decimal — worked around inside the **user-defined formula**: store A/100 and compute `(A*100)/B`.

---

## 11. Fees Not Populating — CCT / UOM / Fee Setup

| Issue | Root cause / fix | Evidence |
|-------|------------------|----------|
| Flat (cap/limit) fee doesn't populate on invoice | 'Flat' UOM must be configured **with a Quantity UOM and Flow Direction** | 24-00985674 |
| Whole fee families missing (G&PC/G&PV) | CCT term not turned on / expired — fix CCT effective dates | 24-00980129 |
| RMS Credit Fee user-defined fields unreliable | User-defined **Boolean** fields had wrong logic; ADO #1551024 workaround = convert to Yes/No droplists (stored 1/0); long-term fix 2022.10 | 22-00830749 |
| Superfund tax per-producer share | Configure a **new UOM** that calculates each producer's share (setup guide attached to case) | 25-01007097 |
| Fee with mid-month rate changes displays oddly | Show first prod date per rate slice (report logic) | 23-00916618 |
| Core invoice absent for a group | Invoice Group **Copy tab** unpopulated | 22-00875660 |

> CCT detail gotcha (Customer Error 26-01094586): a CCT **Details text field > 100 characters** blocked the entire invoice run for the facility — trim the text. Worth checking when "can't run invoicing" for one plant.

---

## 12. Invoice Generation / Delivery Hard Errors

- **25-01022916 (Howard):** "The given key was not present in the dictionary" across multiple windows — build defect, fixed by software update; capture build number and escalate, no config answer.
- **22-00617633 (MarkWest):** after client moved SMTP to **Office 365**, all external invoice emails rejected with **bare line feed** error — invoice e-mail generation emitted bare LFs; code fix. If "customers stopped receiving invoices" right after a mail-platform change, check this before anything else.
- **23-00930616 (M6):** wrong invoice **report version** in an environment — workaround: configure the **FTP process** (local file name → Qcloud route), upload the desired report, run FTP pickup. Permanent fix = patch the report into the environment.
- **22-00654006 (Diversified):** invoices not printing all pages / contacts out of sequence — posting bug; DB-upgrade patch + posting scripts for previous months.

---

## 13. Expected Behavior / User Education

70 closed cases (44 Training, 26 Customer Error). The repeat offenders:

| Reported as | Reality | Evidence |
|-------------|---------|----------|
| "Delivery volumes doubled on invoice" / "wrong PPAs on rerun" | Client created a **duplicate CTR UOM (e.g. DELVOL)** via user-defined formula — end-date/delete the dup UOM, reload code table, rerun plant | 23-00925718, 23-00934620 |
| "Rerun fee data not flowing to invoice properly" | **Multiple values for the same fee type** confused Settle→Invoice conversion; change the 0-value fee type and rerun | 25-01055374, 25-01054942 |
| "Contracts disappeared from invoice" after address change | New BA address suffix created but **Invoice Group contact** never updated — create contact with new address, attach to invoice group, rerun (KB ka0UG0000003F0vYAE) | 24-00980998 |
| "Can't roll/close accounting month" / "opened wrong acctg date" | Accounting Date Maintenance steps — the date usually exists; open it and the billing month; purge process is the sanctioned cleanup for reruns/wrong acctg-date-type runs | 25-01054509, 25-01032580, 26-01093889, 26-01095199 |
| "Invoice not printing" for a contract | No settle records (add a **0 nomination** so records exist), or missing statement group / default contact | 26-01081326, 26-01093064, 24-00956716 |
| "Escalation/index not working" | Missing index values (CPI), or rate-schedule time slice end-dated; keep latest slice open-ended | 26-01064409, 26-01090489, 25-01048513 |
| "Can't run invoicing for facility X" | CCT Details text exceeded 100-char limit | 26-01094586 |
| "Meter split / allocation error" | Meter time slice not active for the contract period, or missing **Gathering Relation Split** for a G1 split source | 25-01041675, 25-01040686 |
| "Statements/queries don't match" | Use the **Settle Summary query** for wellhead purchases, not an interactive report | 25-01040893 |
| Accrual vs Actuals process | **Not supported by TIPS** (closed as such) | 25-01035032 |

**Tell-tale it's user/config:** the anomaly started right after a client-made change (new UOM, new address, end-dated time slice, wrong acctg date type), and the Settle-level queries are internally consistent.

---

## 14. Known Historical ADO Bugs

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|-------|--------------|-----------------|---------|---------|
| **#1538357** | Bug / Closed | DTM — TIPS Core Invoice — Duplicating Data in External View (BL01A, per security user; PR 73404 → 2022.04) | §3 | — |
| **#1761173** | Bug / Closed (hotfix 11/7) | SRI — QRPTS_INVOICE_DTL_CAN bug — RPT 200 volumes x2–x4, multi-facility meters, missing plant filter | §3 | 25-01049592 |
| **#1733867** | Bug / Closed | HEP — STX Imbalance volumes doubling on BL01 (Crystal SUM of WHDV_HV) | §3/§6 | — |
| **#1724455** | Bug / Closed | MOM — Invoice displays incorrect reversal & corrected volumes on PPA/rerun (QRPTS_INVOICE_DTL_VW) | §4 | 25-01004724 |
| **#1566523** | Bug / Closed | NRM — Service Invoice Report incorrect reversals (JRNROLUP vs Collection Method/Waived fees) | §4 | 22-00830869 |
| **#260819** | Bug / Ready for QA | NRM — PPA Invoice Amended Amount Not Cross Credited (the change #1566523 was collateral of) | §4 | — |
| **#1640286** | Bug / Closed | F/V PEM — Reversal records missing from Functional Unit Journal Entry (`SP_QTIP_JOURNAL_ENTRY_PEM`) | §4/§5 | — |
| **#1564067** | DB Change / Closed | QRMTIPS — new views `QPOST_RPTS_INVOICE_RPT_STMT_VW` & `_XVW` (posted-invoice comments) | §5 | 22-00824672 / 23-00877027 |
| **#1532732** | Bug / Closed | PEM — Journal Rollup table character limit (2022.10) | §5 | 22-00264156 |
| **#1674016** | Bug / Closed | ONM — Statement Group Maintenance Web "must have at least one contact" error | §7 | 24-00966603 |
| **#1776617** | Bug / Closed | ONM — same Web contact error recurrence on 2024.04 | §7 | 25-01062445 |
| **#1682312** | Bug / Closed | ONM — Contract Extension screen wrong BA# on Statement tab (Copies-tab join) | §7 | — |
| **#1572417** | Bug / Closed | Statement Group Maintenance — Payment Terms differs Oracle vs MSSQL (code table 28077 order) | §7 | — |
| **#1590338** | Bug / Closed | ETP — Escalation Schedules rounding (ESCALP vs SETTLEMAIN, `QInflationSchedule`) | §10 | 23-00885983 |
| **#1643313** | Bug / Closed | ALT — ESCALATE inserts no records; CCT/rate time-slice rollback script + patch | §10 | — |
| **#1732345** | Bug / Closed | Escalation Schedules — Fixed Amount/Period decimal shown rounded in Web (`QCTRL_INFL_SCH`) | §9/§10 | — |
| **#1736767** | Bug / Closed | PEM — Facility Ownership Terms Revenue Rate Schedule resolves to 0 (`QCODE_PREDEF_FORMULA` missing row) | §10 | 25-01024319 |
| **#1551024** | Bug / Closed | DTM — Meter Definition user-defined Boolean wrong logic (droplist workaround; 2022.10) | §11 | 22-00830749 |
| **#1669317** | Bug / Closed | ENT — WAH residue volumes doubled in `QTRAN_SETTLE_SUMMARY` (default GATH CCT / POP term, `QContractTermSettlement.cpp`) | §3/§8 | 24-00961961 |
| **#1681547** | Bug / Closed | TIPS CAN — report export failures MSSQL (`QRPTS_INV_ANEQUAL_ADJ_HDR_VW` record selection) | §12 | — |

---

## 15. Key Code Objects, Reports & Repos

### Reports
| Report | What it is |
|--------|------------|
| **BL01 / BL01A** | Invoice Documents report (BL01A = by Account Manager; external-user duplication defect) |
| **RPT 200** | Settlement Invoice (core; CAN variant uses `QRPTS_INVOICE_DTL_CAN`) |
| **RPT 108** | Settle Invoice PEM (Pembina settlement invoice; PPA prior-total defect) |
| **ESCAL_BR** | Escalation Preview – BR report (job ESCALP) |

### Views / tables / procs (confirmed in cases & ADO)
| Object | Purpose |
|--------|---------|
| `QRPTS_INVOICE_DTL_VW` / `QRPTS_INVOICE_DTL_CAN` | Non-posted invoice detail views (PPA-doubling & CAN multi-facility defects) |
| `QPOST_RPTS_INVOICE_RPT_STMT_VW` / `_XVW` | Posted-invoice statement views (added by #1564067) |
| `QTRAN_SETTLE_SUMMARY` | Settle summary by plant/meter/prod (compare D vs M unit-time rows; doubling checks) |
| `SP_QTIP_JOURNAL_ENTRY_PEM` | Journal-entry proc used by JRNROLUP (PEM) |
| `QCTRL_INFL_SCH` | Escalation/inflation schedule definitions (Fixed Amount/Period) |
| `QCODE_PREDEF_FORMULA` | Predefined formulas — rate schedules must have a row to resolve |
| `QARCH_QFCBATCH_SQL_TRACE` | Batch SQL trace by process step queue ID (ESCALATE/SETTLE debugging) |
| Code tables **28077** (Payment Terms), CTR UOM code table | Statement-group picklists; duplicate-CTR-UOM customer-error pattern |

### Batch processes / jobs
`SETTLEMAIN` (settlement), `INVOICE` (invoice gen; SOA population), `JRNROLUP`/`JRNPRORATE` (journal rollup), `JRNSAPINT` (journal transfer), `ESCALATE`/`ESCALP` (rate escalation / preview), `PLANTOWN` (plant ownership), Facility/Company **Batch Job Submittal (FBJS/CBJS)** screens, Accounting Date Maintenance, purge process (rerun cleanup).

### Repos
`Quorum.TIPS.ClassicBatch` (ESCALP/SETTLEMAIN, `QInflationSchedule`, `QContractTermSettlement.cpp`), `Quorum.TIPS.Metadata` (code tables/screens), `<CLIENT>.TIPS.Reports` (invoice/statement Crystal defs under `/Report Definition/MSSQL_CR2011/Client/QRPTS_INVOICE_*.txt`, e.g. `XMG.TIPS.Reports`), `<CLIENT>.TIPS.Metadata`, `<CLIENT>.TIPS.ClassicBatch` / `.App.Qpec` overrides (e.g. ETP). **Always check the client override repo before assuming core behavior** — most invoice formats here are client Crystal reports.

---

## 16. Diagnostic SQL Queries

> Column names below are confirmed from ADO repro steps where cited; verify against the client schema before scripting.

### A. Settle summary vs invoice — doubling check (from ADO #1669317 repro)
```sql
SELECT A.PLANT_NO, A.UNIT_TM_CD, A.MTR_NO, A.MTR_SFX,
       SUM(A.TOT_VALUE_PR)  AS TOT_VALUE_PR,
       SUM(A.TOT_RES_HV)    AS TOT_RES_HV,
       SUM(A.TOT_FEES_INVOICED) AS TOT_FEES_INVOICED
FROM   QRMTIPS.QTRAN_SETTLE_SUMMARY A
WHERE  A.PLANT_NO = '<PLANT>' AND A.ACCT_DT = '<ACCT_DT>'
  AND  A.PROD_DT BETWEEN '<PROD_FROM>' AND '<PROD_TO>'
  AND  A.UNIT_TM_CD IN ('D','M')
GROUP BY A.PLANT_NO, A.MTR_NO, A.MTR_SFX, A.UNIT_TM_CD
ORDER BY A.MTR_NO, A.UNIT_TM_CD DESC;
-- Doubled M rows vs sum of D rows = the #1669317 / doubling family. If this is RIGHT and the
-- document is wrong, the defect is in the report/view layer (§3).
```

### B. Batch SQL trace for a failing/empty process run (ESCALATE/SETTLE/INVOICE)
```sql
SELECT * FROM QARCH_QFCBATCH_SQL_TRACE
WHERE  PROCESS_STEP_QUEUE_ID = <STEP_QUEUE_ID>
ORDER BY 1;   -- per ADO #1643313 repro: shows whether ESCALATE actually inserted anything
```

### C. Escalation schedule + index sanity (the 25-01013611 pattern)
```sql
SELECT * FROM QCTRL_INFL_SCH WHERE SCH_NO = '<SCHEDULE#>';
-- then confirm index values exist for every period the schedule needs (CPI/FERC etc.);
-- empty Escalation Preview almost always = missing index rows or schedule date-basis misconfig.
```

### D. Rate schedule resolves to 0 (ADO #1736767)
```sql
SELECT * FROM QCODE_PREDEF_FORMULA WHERE <SCHEDULE_ID_COL> = '<RATE_SCHEDULE_ID>';
-- No row → the schedule cannot resolve; that's why Rate/Excess Charge blank out on PLANTOWN.
```

### E. Duplicate CTR UOM (customer-error doubling pattern, 23-00925718)
```sql
-- Look for two rows for the same UOM code (e.g. DELVOL) in the CTR UOM code table /
-- user-defined formulas; the newer client-created one causes doubled volumes.
-- Fix: end-date the duplicate, reload the code table, rerun the plant.
```

### F. Posted vs non-posted discrepancy
```sql
-- Compare the same invoice in QRPTS_INVOICE_DTL_VW (non-posted) vs the QPOST_RPTS_* views;
-- a field present pre-post and absent post-post = posted-view gap (§5, #1564067 pattern).
```

---

## 17. Escalation Decision Tree

```
TIPS Invoice/Billing/Rates case reported
│
├─ Amount/volume DOUBLED or duplicate lines?  (§3)
│   ├─ Settle queries also doubled → DATA: two acctg dates same company (22-00624664)?
│   │     duplicate CTR UOM created by client (23-00925718 — Customer Error)? daily-conversion month?
│   └─ Settle queries correct → REPORT/VIEW: external user (BL01A #1538357)? multi-facility meter
│         (RPT 200 CAN #1761173)? JIBLink/non-posted view join (22-00642205)? → Engineering, cite ADO #
│
├─ PPA/rerun reversal or corrected line wrong?  (§4)
│   ├─ Volume exactly 2x, amount right → QRPTS_INVOICE_DTL_VW defect (#1724455) — check build
│   ├─ Original had Waived/cross-credit fees → JRNROLUP Collection-Method (#1566523)
│   └─ INVOICE APPROVAL step errors → Unit-Time-Code/Run-ID query defect (22-00691445)
│
├─ Data on screen but missing from POSTED invoice (tax/GST/comments)?  (§5)
│   └─ Posted-view gap or fix not consumed in client build → Engineering/patch verify
│
├─ Invoice section vanished after a contract/BA edit?  (§6)
│   └─ BA time-slice vs imbalance VW (26-01079729) → check BA history; known defect ticket
│
├─ Statement Group / contact / picklist problem?  (§7)
│   ├─ Web-only "must have at least one contact" → known recurring bug (#1674016/#1776617) — patch level
│   ├─ "Duplicate record" w/ no visible dup → overlapping eff-date row → data fix (Cloud Ops)
│   └─ Contracts/contacts missing after address change → Invoice Group contact tab (Training, KB)
│
├─ Gas/settlement statement content wrong?  (§8)
│   └─ Client custom report → compare UAT vs PRD config (facility def reporting category, CCT flags)
│       before defect; most are report tweaks via the client .TIPS.Reports repo
│
├─ Rate/decimal display wrong?  (§9) → report format; check Rate vs APPLIED Rate column (22-00663653)
│
├─ Escalation / index / price import?  (§10)
│   ├─ Preview empty → schedule misconfig + missing index values (CONFIG)
│   ├─ Preview ≠ processed rate → ESCALP/SETTLEMAIN rounding (#1590338) → Engineering
│   ├─ ESCALATE inserts nothing / corrupted time slices → #1643313 rollback script — Engineering + Cloud Ops
│   └─ Imported price off x100 → OPIS-only import; Platts unsupported (limitation, not bug)
│
├─ Fee missing from invoice entirely?  (§11)
│   └─ CCT enabled & in date? Flat UOM has Qty UOM + Flow Direction? Invoice Group Copy tab populated?
│       CCT Details field ≤100 chars? → CONFIG (Cloud Ops / client) before Engineering
│
└─ Hard error / delivery failure?  (§12)
    ├─ "Key not present in dictionary" → build defect → Engineering with build #
    ├─ Emails rejected post-O365 → bare-LF SMTP defect (22-00617633)
    └─ Wrong report version in env → FTP workaround, then patch
```

**Routing rule of thumb:** report/view math defects and process-step errors with clean config → **Engineering** (cite the §14 ADO item and the client's build); eff-date/contact/CCT/UOM/index-value problems and data cleanups (duplicate rows, overlapping slices) → **Cloud Ops / config** with the exact screen and key named.

---

## Data-quality notes (from mining)

- 60 of 280 closed cases (21%) have **no Root_Cause__c**; several actionable resolutions are one-liners ("defect", "Reporting issue") — cluster sizes are floors, not exact counts.
- Recent actionable volume is dominated by **Howard Midstream (HEP)** custom gas-statement work (2025) and **Opportune-managed gathering-invoice format** work (2023) — §8's recipes are client-specific even when the diagnostic pattern generalizes.
- Case_Category is inconsistent: both 'Invoice' and 'Invoices' exist alongside 'Billing' and 'Rates' — always query all four.
- Pre-2022 cases were renumbered into the 22-005xxxxx/22-006xxxxx ranges; their CreatedDate (2019–2021) is the true age.
- Resolution__c cannot be filtered in SOQL WHERE clauses; clusters were built from Subject+Resolution text post-hoc.

---

*Skill created: 2026-06-11*
*Based on: 78 actionable TIPS Invoice/Billing/Rates SF cases (Software Defect + Application Configuration + ChangeConfig) of 280 closed, plus 70 Training/Customer Error cases; ADO work items #1538357, #1761173, #1733867, #1724455, #1566523, #260819, #1640286, #1564067, #1532732, #1674016, #1776617, #1682312, #1572417, #1590338, #1643313, #1732345, #1736767, #1551024, #1669317, #1681547.*
*Companion: SKILL_Allocations.md (QPTM), SKILL_Billing.md (QPTM). Applies to TIPS CORE and TIPS CAN unless noted.*
