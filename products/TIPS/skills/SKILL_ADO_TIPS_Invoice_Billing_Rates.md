# SKILL (ADO): TIPS Invoice / Billing / Rates — Defect & Fix Reference

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** My Quorum TIPS (midstream — measurement, allocation, settlement, statements)
**Source:** Azure DevOps Bugs (QuorumSoftware org) under `Engineering\Midstream` and `Engineering\Maintenance\Midstream and Transportation`, functional terms invoice / billing / rate / fee / CICO / settlement invoice / rate schedule / escalation. Closed/Resolved only. Root cause, fix decision and fixed-in-build inferred from work-item **description + ReproSteps + the full dev comment thread + linked PRs** (read 2026-06-14).
**Use When:** triaging a TIPS Invoice / Billing / Rates ADO bug or an SF case that smells like one — settlement invoice (RPT 200 / RPT 108) wrong, rate displayed ≠ applied rate, PPA reversal not netting, rate-schedule won't save / resolves to 0 / averages wrong, escalate-rates process fails, CCT fee not populating, fee ordering / margin wrong, Web rate/input-price screen errors, invoice doubling on meter splits.
**Companion:** SF-side recipes in `TIPS Assitant\SKILL_TIPS_Invoice_Billing_Rates.md` (cite SF case numbers there). QPTM transport-billing overlap noted throughout (see Overlap caveat).

> **Build-version caveat:** `Microsoft.VSTS.Build.IntegrationBuild` was **EMPTY on every bug analyzed.** Fixed-in-build below is **inferred** from iteration path (YY.NN → release), release tags ("Merged to 2023.04 Release", "PEM Hotfix 5", "queued for next TIPS 2021.04"), and PR target branches (`support/17.26.x`, `hotfix/17.27.1`, `[2024.04]`, `[develop]`). **All marked "(inferred — confirm in release notes)".** Maintenance-branch client bugs are usually delivered as a **client patch/hotfix**, not a core GA; the same fix is then merged forward to develop + last 2 GAs.

---

## 1. Quick Triage

```
[ ] Is the wrong artifact the INVOICE DATA (QTRAN_*/settle tables) or only a REPORT rendering
    (RPT 200 SETTLEMENT INVOICE, RPT 108 SETTLE INVOICE PEM, BL01/BL01A, gas statement)?
    Half the defects here are report/view (Crystal + QRPTS_*/QPOST_* views), not processing.
[ ] Posted vs non-posted? Posted reads QPOST_RPTS_* views; non-posted QRPTS_*. CAN variant uses
    *_CAN views/schema QRMTIPS_CAN (a recurring "table could not be found" cause — #236409).
[ ] Web or Classic? A whole defect family is "works in Classic, fails/missing in Web" — V2UI parity,
    rate-schedule save errors, missing picklist/bulk-edit, ORA-01002 fetch-out-of-sequence on Web.
[ ] PPA / rerun involved? Reversal/corrected-line math is its own family (§4). Confirm acct date ≠
    prod date is EXPECTED for a PPA (standard TIPS — see #1609124).
[ ] Meter split (same contract, MTR_SFX A & B) or meter under multiple facilities? → duplicate/x2
    invoice values from a missing MTR_SFX/plant filter in the view (§3, #1767237).
[ ] Rate complaint: is the RATE wrong (processing — rate resolution / CCT / schedule) or only the
    rate DISPLAYED wrong while the $ amount is right (report pulling RATE not APPLIED_RATE — §5)?
[ ] Escalate-rates / rate-schedule process: hard error (ORA char-limit, missing reg-SQL) vs wrong/
    zero rate (schedule type Fee-vs-Price, schedule not in formula table) — §6.
[ ] Is this actually a QPTM transport-billing item that the title-search swept in? (TSP / Service
    Request / Invoice Detail Maintenance / TOC / BLINVGEN voucher / IN51A / Location Maintenance
    fuel rate / INCUVCALC) → route to the QPTM ADO skill, NOT here. See Overlap caveat.
```

---

## 2. Decision Tree

```
TIPS Invoice/Billing/Rates ADO bug
│
├─ Settlement invoice / RPT 200 / RPT 108 / BL01 amounts or layout wrong?
│   ├─ Duplicate values on meter splits (same contract, A & B suffix) → QRPTS_SETTLE_INV_DTL_VW
│   │     QTRAN_PAYSTATION join missing MTR_SFX (§3, #1767237)
│   ├─ Rate shown ≠ contract Applied Rate, $ total correct → view/report pulled RATE not
│   │     APPLIED_RATE across the QRPTS/QPOST_INVOICE_DTL_* view family (§5, #1352683/#1596465)
│   ├─ PPA "Less original invoice" wrong (excludes product purchases / includes GST or gas-stmt)
│   │     → client SETTLE_INVOICE_PEM view+formula (§4, #1609124/#1619956/#1627661)
│   ├─ "table could not be found" / blank pages / logo overlap / misspelled header / ATTN null
│   │     → report-definition / view / Crystal cosmetic (§7)
│   └─ PPA prior-month not reversing (net not 0) → settle ordering / OR-vs-R generation
│         (§4, #1573301 m_Sel_Paystation order)
│
├─ Rate / rate-schedule / CCT?
│   ├─ Rate resolves to 0 or wrong basis → schedule type Fee vs Price; CCT margin re-stamping
│   │     rate-res-id; missing QCODE/formula row (§6, #1736767, #264857/#280352)
│   ├─ Simple average ignores a 0 price → avg code dropped 0 (§6, #1674818)
│   ├─ Web won't save / "Object reference" / required-column config / global-vs-plant timeslice
│   │     → Web/metadata defect (§8, #1745110, #1647805, #1799931)
│   ├─ ORA-01002 fetch out of sequence on Input Prices / Rate Schedules (Web, multi-row)
│   │     → Web batch update + perf indexes (§8, #1715559)
│   └─ Missing picklist / bulk-edit / hide-show / default not carried Classic→Web → V2UI parity (§8)
│
├─ Escalate-rates batch fails? → client table char limit (CTR_NO 11<12) (§6, #1648566)
│
├─ Fee not populating / wrong order / margin fee?
│   ├─ Missing quantity UOM in code table → fee not calculated (§9, #1697539, #264928)
│   ├─ Margin/min-charge reads wrong fee set / no fee-order control → new MARG_FEE_IND + fee
│   │     ordering query (§9, #1768945)
│   └─ CICO charge basis: truncated to integer / not usable as formula variable (§9, #103794/#109121)
│
└─ Looks QPTM (TSP/Service Request/TOC/voucher/IN51A/INCUVCALC)? → QPTM ADO skill (Overlap caveat)
```

---

## 3. Settlement-Invoice Duplication / Doubling (meter splits & multi-facility)

**Symptom:** Settlement Invoice (RPT 200 / CAN) shows duplicate fee/volume lines or x2 values; settle query screens are correct.

**Root cause:** invoice-detail view joins lose granularity. For meter splits where the **same contract** is on both splits (MTR_SFX A & B), `QRPTS_SETTLE_INV_DTL_VW`'s join to `QTRAN_PAYSTATION` lacks an **MTR_SFX** predicate, so each split row matches both and the value populates twice. The dev isolated it by select-*-ing the view and walking each join until the row duplicated (#1767237). The multi-facility variant (meter under several facilities/splits, CAN report) is the missing **plant filter** family on `QRPTS_INVOICE_DTL_CAN` (cross-referenced from the SF-side skill, ADO #1761173 — not deep-read here, confirm).

**Fix:** add the MTR_SFX filter to the QTRAN_PAYSTATION join in the CAN settlement-invoice detail view; PRs 121922/121992/122000/122002 (`*.TIPS.Database` / client CAN repo).
**Fixed-in-build:** SRI client patch, late-2025 cycle (iter `QuorumSoftware`, tags "Approved by QA; QA Approved Client") **(inferred — confirm in release notes)**; forward-merge to develop + last 2 GAs typical.
**Workaround:** none clean at report level; verify with the Settle Prod / Settle Fees query (correct) vs the report (doubled) to prove it is the view, then patch.
**Bug IDs:** #1767237 (SRI). Related multi-facility/plant-filter: ADO #1761173 (SRI 25-01049592, per SF skill).
**Linked SF:** 25-01055412 (#1767237); 25-01049592 (#1761173).
**Clients:** SRI (Steel Reef), CAN/TIPS-CAN environments.

---

## 4. PPA / Rerun — Wrong Reversals & "Less Original Invoice" Math

**Symptom A (report totals):** On a PPA, RPT 108 SETTLE INVOICE PEM "Less original invoice" line is wrong — it excludes Plant Product Purchases (shows only fee total), or wrongly includes GST / the Gas-Statement subtotal.
**Root cause A:** the client view `QRPTS_SETTLE_INV_TOTALS_VW`/`ESUITE_QPEM` only summed `AMEND_INV_ALL_FEE_TOTAL`; needed `AMEND_INV_ALL_PROD_TOTAL` (pulls "RES" residue values from `QPOST_RPTS_INVOICE_DTL_CAN`), and the Crystal "Less Invoice #" nested formula had to stop adding GST / gas-statement (RES) values. John Weems' triage: the calculation should be in the view, not a nested Crystal formula.
**Fix A:** view change to add the product-purchase column + Crystal formula change in `SETTLE_INVOICE_PEM.rpt`. Delivered as **3 chained bugs**: #1609124 (add product purchases) → #1619956 (remove GST) → #1627661 (Part 2: exclude gas-statement subtotal). PRs 88066-88069 / 89926 / 90698-90751; core columns merged 2022.10+.
**Fixed-in-build:** PEM client patch, 2023; core new columns "merged to 2022.10 and up" **(inferred — confirm in release notes)**.
**Bug IDs:** #1609124, #1619956, #1627661 (all PEM/Pembina). **Linked SF:** 23-00895341.

**Symptom B (data — prior month not netting to 0):** PPA does not reverse the originally-billed value; prior-month line re-bills the same amount instead of OR (reversal) + R (corrected) netting to 0.
**Root cause B (#1573301, DTM):** the core query **`m_Sel_Paystation`** (`Quorum.TIPS.ClassicBatch/Common/QTipsSettleLib/QSQL_SettleMain.cpp`) returned meters in a different order, so a client settle rule (`QRateScheduleRuleFormulaCondDTM_PERK`, picks the *first* entry per contract) processed the wrong meter and the prior-month record was written as **OR instead of R** in `QRPTS_INVOICE_DTL`. Fix: add `TRNX_ID` to the ORDER clause (done as core + client metadata override + FVF custom-formula fix, to avoid risking the core query for other clients).
**Fix B:** PRs 82485/82527/82596 (add ORDER `TRNX_ID`) + 85766 (FVF missing-fee). Merged 2021.10, 2022.10, 2023.04, develop. **(inferred — confirm in release notes)**.
**Workaround B:** none documented; FVF (client-specific settle rule) makes it untestable in core SUP.
**Bug IDs:** #1573301 (DTM). **Linked SF:** in title as `[FVF]` (no 25-/24- number on the WI).

---

## 5. Rate Displayed ≠ Applied Rate (invoice $ correct, RATE column wrong)

**Symptom:** Invoice/Settlement documents show the **base Rate**, not the **Applied Rate** (base ± inflation/escalation/adjustments). The invoice **amount is correct** (it used Applied Rate internally), so customers can't tie volume × shown-rate to the total. (TIPS: Rate = base; Applied Rate = base after adjustments; the value is always volume × Applied Rate.)

**Root cause:** the invoice-detail views and the Crystal sub-reports pulled `QRPTS_INVOICE_DTL_VW.RATE` instead of `APPLIED_RATE`. The fix had to replace RATE→APPLIED_RATE across a **large view family** (Jon Shuck's list): `QRPTS_INVOICE_DTL_VW`, `_VW_CORE`, `_IMB_VW`, the `QPOST_RPTS_*` posted equivalents, the `*_XVW` extended views, plus reports `QRPTS_INVOICE_ACCT_MGR.rpt`, `Invoice Details Acct Mgr.rpt`, `Invoice Details - Imbalance Acct Mgr.rpt`. The DB upgrade was risk-laden (sysgen-view ordering: views referencing the new column failed because sysgens build after non-sysgens — required a forced-sysgen `<QDBMGR action="CREATE" … QRPTS_INVOICE_DTL_VW>` block in the package).

**Fix:** view + report change (BL01/BL01A). #1352683 first (BMH/Brazos), then #1596465 (UTG) for BL01A `QRPTS_INVOICE_ACCT_MGR.RPT`.
**Fixed-in-build:** **intentionally NOT back-patched to all GAs** — dev (Jessica Bradham) explicitly left it in 2019.10 (BMH) + develop only and warned against patching to other builds due to DB risk. UTG (#1596465) delivered via 2023.04 hotfix family. **(inferred / explicitly limited — confirm in release notes before telling any other client it's fixed in their build.)**
**Workaround:** customer computed escalations outside the system (BMH) until patched.
**Bug IDs:** #1352683 (BMH/Brazos, "Patch Immediately"), #1596465 (UTG, FVF). **Linked SF:** 21-00187526, 23-00897523.
**Clients:** BMH/Brazos, UTG. (SF-side companion lists 22-00663653 for the same Rate-vs-Applied family.)

---

## 6. Rate Schedules, CCT Rate Resolution & Escalate-Rates

**6a. Revenue Rate Schedule resolves to 0 / PLANTOWN errors (#1736767, PEM):**
- **Symptom:** Facility Ownership Terms "Revenue Rate Schedule" picklist resolves Rate→0 and ExcessCharge→0 even with excess volume; entering a manual rate works.
- **Root cause:** two issues. (1) A registered SQL **`Sel_H2SCO2_PCT`** existed for Oracle but was **missing for MSSQL**, so PLANTOWN threw "Operating system error". (2) Functionally, the schedule must be **Type = Price**, not Type = Fee — a Fee-type rate schedule does not resolve on the CO&O / Plant Ownership report.
- **Fix:** add a cross-platform `Sel_H2SCO2_PCT` SQL. PRs 116800 (2021.04)/116931 (DEV)/116932 (2025.04)/116954 (REL).
- **Fixed-in-build:** "queued for next TIPS 2021.04" tag + cherry-picks to 2025.04 & REL **(inferred — confirm in release notes)**; PEM client patch.
- **Workaround:** set the rate schedule up as **Type = Price** (Cristina Keeton's verified workaround).
- **Linked SF:** 25-01024319.

**6b. CCT Margin re-stamps / fails to stamp Rate Resolution ID (#264857, #280352, #264928):**
- **#264857 (Contract-basis Margin):** the same rate-res-id was assigned to every record and duplicates logged — Margin at Contract level recalculates the term per paystation and **overwrites the rate-res tied to the originally-calculated term**. Fixed; cherry-picked to 2021.04. (iter 21.05)
- **#280352 (Meter-basis Margin):** Margin rate-res-id was **null in `QTRAN_SETTLE_SUMMARY`** when a **Rate Schedule** was used for Producer % Share. Fixed (feature/280352). Note: CAN does not use margin setup. (iter 21.11)
- **#264928 ("Value" CCT fee):** when the Value tab calculates a line defined as a **Fee** (`QCODE_BSA_VAL_TYPE`), the C++ did not populate **Quantity UOM CD** — fix `QContractTermValueBSA::OutputToDatabaseFEE()`. Fixed, cherry-picked 2021.04. (iter 21.05)
- **Fixed-in-build:** TIPS **2021.04** family **(inferred from iteration 21.04/21.05/21.11 + cherry-pick comments)**.

**6c. Rate Schedule simple average ignores a 0 price (#1674818, DCP):**
- **Symptom:** Rate Schedule "Simple" average drops the 0-priced schedule, giving a wrong average that flows into reports.
- **Root cause:** an `if` block excluded 0 before averaging. **Fix:** remove the if-block so 0 is counted (PR 100103); but a not-effective-for-the-range schedule must still be **ignored entirely, not treated as 0**. Diagnostic tip from dev: query **`QTRAN_PAYSTATION`** to confirm which CCT the meter actually uses (meter-split CCT override often differs from what you set up).
- **Fixed-in-build:** 2024.04 / develop family, Aug-2024 review **(inferred — confirm in release notes)**. **Linked SF:** 24-00962942.

**6d. Escalate-Rates batch fails — client table char limit (#1648566, NRM):**
- **Symptom:** Escalate Rates (Globally) fails `ORA-12899: value too large for column "QTRAN_ESCALATE_RESULTS"."CTR_NO" (actual 12, max 11)`.
- **Root cause:** client-specific `ESUITE_QNRM.QTRAN_ESCALATE_RESULTS.CTR_NO` was **VARCHAR(11)** while core (and CTR_HDR) allow **12**. **Fix:** widen client column to 12 (PR 98467, `NRM.TIPS.Database`; DB ticket #1672494). Also needed connection id "QNRM ESuite Connection" on process step ESCRATES to reproduce.
- **Fixed-in-build:** NRM client patch, July-2024 **(inferred)**. **Linked SF:** 24-00941962.

> SF-side companion adds the deeper escalation defects not in this ADO slice: ESCALP-vs-SETTLEMAIN rounding (ADO #1590338, `QInflationSchedule`), ESCALATE inserts-no-records rollback (#1643313), Fixed-Amount decimal display (#1732345), rate schedule missing `QCODE_PREDEF_FORMULA` row. Cross-check there.

---

## 7. Settlement-Invoice Report Cosmetic / Definition Defects (CAN-heavy)

| Symptom | Root cause / fix | Bug | Fixed-in-build (inferred) | Clients |
|---|---|---|---|---|
| QRPTLAUNCH "table could not be found" running Settlement Invoice BACC Level (108) | Report tied to a view not in `QRMTIPS_CAN` schema — created missing **`QRPTS_SETTLE_INV_TOTALS_CC_VW`**; plus a `Section_Visibility` Crystal "boolean required" formula error | #236409 | 2020.11 (iter 20.24) | TIPS-CAN |
| "ATTN" field null on Settlement Invoice (200) | Core process **INVOICEHDR** SQL `SQLID_UpdtCtrPartyContactSeqNo` selected `CONTACT_ID` while code expected `CONTACT_SEQ_NO` (column absent → null). Fix: alias CONTACT_ID→CONTACT_SEQ_NO. CAN-only call. Workaround: attached SQL to update `QRPTS_INVOICE_HDR_CAN` | #1633673 | merged 2022.10 + develop pre-release-cut | ALTDEVA1 (Canada) |
| Blank pages in middle of Settlement Invoice PEM | Report cosmetic; new `SETTLE_INVOICE_PEM.rpt` | #190083 | PEM Hotfix 5 | PEM |
| Settlement-invoice report formula error (template) | Replaced report template | #177330 | PEM Hotfix 2 | PEM |
| Logo overlaps header (Veresen) | Crystal logo positioning; ENV-layer report def pointing logo path local | #238830 | PEM 2021.03 (iter 21.01) | PEM/Veresen |
| Misspelled "Iinvoice" header on Settlement Detail RPT_42560 | Crystal label fix | #1445777 | 2022.04 (iter 22.08) | TIPS-CAN |
| Logo too small / oversize overlaps header | **REJECTED** — could not reproduce; closed without fix | #1768304 | n/a (Rejected) | SRI |
| BLR_00 Billing Report Oracle unique-constraint error | Pre-report SQL didn't filter eff dates within the acct month for **`SCTRL_BA_TAX_ID`**; BAs with multiple GL-customer-number tax-id timeslices collide | #1585257 | merged 2022.10 + develop/2023.04 | BLH (Black Hills) |
| Invoices grouped by **fee type** instead of by **meter** (BL01) | Crystal grouping; also fix `PPA_COUNT` DistinctCount that was grouped by FEE_BUCKET_CD (changed to meter no) | #1593263 | 2022.10 (hotfix 17.16.16) + 2023.04 + develop | MOM/Momentum (FVF) |

> CAN reports live in client `*.TIPS.Reports` repos under `/Report Definition/MSSQL_CR2011/...`. When a report errors "table could not be found", open Set Database Location in Crystal and confirm every view exists in the right schema (`QRMTIPS` vs `QRMTIPS_CAN`).

---

## 8. Rate / Input-Price Screen — Web (V2UI) Defects

| Symptom | Root cause / fix | Bug | Fixed-in-build (inferred) | Clients |
|---|---|---|---|---|
| ORA-01002 "fetch out of sequence" saving 2+ prices (Input Prices) or a Fixed Rate (Rate Schedules) in **Web** | Web multi-row update + perf problem; fixed `LogPriceSchedulePPA` DB calls and added indexes on `QPOST_PAYSTATION_GATH_FUEL/_FEE` and `QTRAN_RATE_RES_DETAIL`. Classic unaffected | #1715559 | 2024.04 / 2024.10 / 2025.04 + develop | ETP |
| Rate Schedule save → "Object reference not set" | Missing **null check** in a validator (triggered when product changed on a Price-type schedule). Fix: add null check (PR 117990) | #1745110 | 2024.10 hotfix (support/17.26.x, hotfix/17.26.9) + develop | NEM |
| Can't save new Rate Schedule in Web (Classic OK) | Client **required-column config** set true; changed to false (`ALT.TIPS.Metadata` PR 94885) | #1647805 | ALT client patch, Mar-2024 | ALT |
| Can't end-date/edit a **plant-specific UDEF linked to a GLOBAL schedule** after upgrade | Data-conversion left mixed global/plant timeslices; fixed by **data conversion script** (`IPF_User_Defined_Formula_Timeslice_Fix.sql`) making schedules+formulas global from a common start date. Not a code fix | #1799931 | data fix (upgrade-time); flagged High — multiple clients on upgrade | IPF |
| Daily-Rates grid missing Import/Export & Bulk-Edit | Grid def lacked `AllowExcelImport/Export`; BulkEdit was intentionally removed earlier (PR 72973) and re-added | #1544446 | 2022.10 (iter 23.09), V2UI | core/HD |
| Location Fees "Fee Condition" has no picklist (Web) | V2UI grid missing picklist binding | #1543615 | 2024.x (iter 24.25), V2UI | core |
| Rate Schedules SCALE missing "PEN1" Factor option (Web) | Dropdown option missing | #1571959 | 2023.04 (iter 23.07) | core/HD |
| Contract Rates FEE EX hide/show + export not working | V2UI grid behavior | #1583754 | 2023.04 (iter 23.09) | core/HD |
| Rate-source Average + type Simple shows Greatest/Least-of-N fields (Web) | Fields not hidden for Simple/Weighted; value not cleared on toggle → could save stray value. Fixed to match Classic | #1702168 | 2024.04 family | ETP |
| Rate Schedule / Input Price **default Time Interval** not carried Classic→Web | Web didn't set default on New; added SetDefault. Same pattern as QPTM fix #1538707 | #1640160 | 2024.10/2024.04 hotfix + 2022.10 (MKW) | MKW |
| PPA Approval screen Rate-Id filter returns no rows (Web) | Filter broke when config `PPACTRPENDING` = 'cache'; fixed (PR 95083) | #1650590 | 2024.04 + develop | core |
| Contract Sales Rate (Classic ONM override) missing "Bucket" column vs Web | Add hidden Bucket column / parity, ONM client metadata | #1607431 | ONM hotfix, 2022.10 | ONM/ONEOK |

> Pattern: most §8 items are **Web/metadata parity** ("works in Classic"). Confirm the client's TIPS Web build line and whether the fix is a core PR (`Quorum.TIPS.Web`) or a client metadata override (`<CLIENT>.TIPS.Metadata`).

---

## 9. Fees / CCT — Not Populating, Wrong Order, CICO Basis

| Symptom | Root cause / fix | Bug | Fixed-in-build (inferred) | Clients |
|---|---|---|---|---|
| DEHY/H2O fee not calculated → fee not charged | Missing **Quantity UOMs** (LBMC, H2O) in `QCODE_QTY_UOM`; Physical Constants screen had values in DB but code table not configured to use them. Fix: insert UOM codes (PR 104841) | #1697539 | SCT client patch | SCT |
| Margin / Minimum-Charge fee reads only the first calculated fee; **no way to control CCT fee calc order** | Added **`MARG_FEE_IND`** column to `QCODE_FEE_TYPE` (code table 24041) + corrected fee-order calculation queries so margin fees can be based on other fees. Note: MSSQL initially created col as tinyint not QBool → checkbox broke (F/V) | #1768945 | 2024.04, 2025.10, 2026.04 hotfix + 2026.04 forward (per dev John Weems) | ETP (F/V) |
| IN_IMBALCI truncates all CICO quantities to integer | `QPSImbalCico.GetValueFromFormula` saved a double into a **long integer** then returned it; define `nFormulaResult` as double, drop the cast | #103794 | ~2019.x (Sprint 60) | TECO et al. |
| Formula Aggregate Charge Basis can't use CICO as a variable | Aggregate charge-basis formula didn't accept CICO charge basis | #109121 | ~2019.x (Sprint 60); not in 2019.05 | TECO |
| Imbalance Contract Fee step errors — null join | `Sel_Paystation_AllCtr` registered SQL generated a join on NULL → contract-fee process step fails | #84246 | V17 (Sprint 51, "Merge to V17 Pending") | core |
| Lump-Sum Rate Object name misspelled (`QVPSOA REQEST FORSERVICE_INJ_WD_LUMPSUM`) | Misspell in metadata + DB scripts (RFS Inj/Wd lump-sum enhancement) — **note this is QPTM-RFS adjacent**, ONK | #131196 | ONK Hotfix 1 | ONK/ONEOK |
| Imbalance Manual CICO screen fields not clearing on cashout-type change | Screen set read-only but didn't clear Cashout %/Vol/Value | #1754567 | 2025.20 (iter 25.20) | core |

---

## 10. Fix-Version Matrix

> IntegrationBuild empty on all; "Build" column inferred from iteration / tags / PR branches — confirm in release notes.

| Bug | Cluster | Symptom (short) | State | Build (inferred) | SF Case | Client |
|---|---|---|---|---|---|---|
| #1767237 | §3 | Settlement Invoice duplicate on meter splits (MTR_SFX) | Closed | SRI patch, late-2025 | 25-01055412 | SRI |
| #1768304 | §7 | Settlement Invoice logo size | **Rejected** | — | 25-01056486 | SRI |
| #1609124 | §4 | RPT 108 PPA "Less original invoice" excludes products | Verified | PEM 2023 / core 2022.10+ | 23-00895341 | PEM |
| #1619956 | §4 | RPT 108 PPA includes GST | Closed | PEM patch 2023 | (23-00895341 fam) | PEM |
| #1627661 | §4 | RPT 108 PPA includes gas-statement subtotal | Verified | PEM patch / core 2022.10+ | (23-00895341 fam) | PEM |
| #1573301 | §4 | PPA prior month not netting (OR vs R, m_Sel_Paystation order) | Closed | 2021.10/2022.10/2023.04/dev | [FVF] | DTM |
| #1352683 | §5 | Invoice shows RATE not APPLIED_RATE (BL01) | Closed | 2019.10 + dev ONLY (not back-patched) | 21-00187526 | BMH/Brazos |
| #1596465 | §5 | BL01A shows RATE not APPLIED_RATE | Closed (Acceptance) | 2023.04 hotfix family | 23-00897523 | UTG |
| #1736767 | §6a | Revenue Rate Schedule resolves to 0 / PLANTOWN err | Closed | queued TIPS 2021.04 + 2025.04/REL | 25-01024319 | PEM |
| #264857 | §6b | Contract-basis Margin overwrites rate-res-id | Closed | 2021.04 (iter 21.05) | — | core |
| #280352 | §6b | Meter-basis Margin null rate-res-id in Settle Summary | Verified | 2021.x (iter 21.11) | — | core |
| #264928 | §6b | "Value" CCT fee not populating Quantity UOM | Closed | 2021.04 (iter 21.05) | — | core |
| #1674818 | §6c | Rate Schedule simple avg ignores 0 price | Closed (Acceptance) | 2024.04/dev, Aug-2024 | 24-00962942 | DCP |
| #1648566 | §6d | Escalate Rates fails ORA-12899 CTR_NO 11<12 | Verified | NRM patch, Jul-2024 | 24-00941962 | NRM |
| #236409 | §7 | QRPTLAUNCH Settlement Invoice BACC "table not found" | Closed | 2020.11 (iter 20.24) | — | TIPS-CAN |
| #1633673 | §7 | Settlement Invoice ATTN null (INVOICEHDR SQL alias) | Closed (Acceptance) | 2022.10 + develop | — | ALT (CAN) |
| #190083 | §7 | Settlement Invoice PEM blank pages | Closed | PEM Hotfix 5 | — | PEM |
| #177330 | §7 | Settlement Invoice PEM formula error | Closed | PEM Hotfix 2 | — | PEM |
| #238830 | §7 | Settlement Invoice (Veresen) logo overlap | Closed | PEM 2021.03 (iter 21.01) | — | PEM |
| #1445777 | §7 | "Iinvoice" misspelled header RPT_42560 | Closed | 2022.04 (iter 22.08) | — | TIPS-CAN |
| #1585257 | §7 | BLR_00 Oracle unique-constraint (SCTRL_BA_TAX_ID) | Closed (Acceptance) | 2022.10 + 2023.04 + dev | 23-00889568 | BLH |
| #1593263 | §7 | BL01 grouped by fee type not meter | Closed (Acceptance) | 2022.10/2023.04/dev | — | MOM |
| #1715559 | §8 | ORA-01002 fetch-out-of-sequence Web price update | Closed (Acceptance) | 2024.04/2024.10/2025.04/dev | — | ETP |
| #1745110 | §8 | Rate Schedule save "Object reference" (Web) | Closed (Acceptance) | 2024.10 hotfix + dev | 25-01032651 | NEM |
| #1647805 | §8 | Can't save new Rate Schedule (Web) — required col config | Verified | ALT patch, Mar-2024 | — | ALT |
| #1799931 | §8 | Global-vs-plant UDEF/schedule won't edit after upgrade | Verified | data-conversion fix | 26-01094138 | IPF |
| #1544446 | §8 | Daily-Rates grid missing Import/Export/Bulk-Edit (Web) | Closed | 2022.10 (iter 23.09) | — | core |
| #1543615 | §8 | Location Fees "Fee Condition" picklist missing (Web) | Closed (Acceptance) | iter 24.25, V2UI | — | core |
| #1571959 | §8 | Rate Schedules SCALE missing PEN1 option (Web) | Closed | 2023.04 (iter 23.07) | — | core |
| #1583754 | §8 | Contract Rates FEE EX hide/show+export (Web) | Closed | 2023.04 (iter 23.09) | — | core |
| #1702168 | §8 | Rate-source Average+Simple shows Greatest/Least N (Web) | Closed (Acceptance) | 2024.04 family | — | ETP |
| #1640160 | §8 | Rate Schedule/Input Price default Time Interval (Web) | Closed | 2024.10/2024.04 hotfix + 2022.10 | — | MKW |
| #1650590 | §8 | PPA Approval Rate-Id filter no rows (Web) | Closed | 2024.04 + dev | — | core |
| #1607431 | §8 | Contract Sales Rate missing Bucket column (ONM) | Verified | ONM hotfix 2022.10 | 23-00906889 | ONM |
| #1697539 | §9 | DEHY/H2O fee not calculated — missing Qty UOMs | Verified | SCT patch | 24-00987748 | SCT |
| #1768945 | §9 | CCT fee order / margin min-charge wrong (MARG_FEE_IND) | Closed (Acceptance) | 2024.04/2025.10/2026.04 + fwd | — | ETP (F/V) |
| #103794 | §9 | IN_IMBALCI truncates CICO to integer | Verified | ~2019.x (Sprint 60) | — | TECO+ |
| #109121 | §9 | Aggregate charge basis can't use CICO variable | Verified | ~2019.x (Sprint 60) | — | TECO |
| #84246 | §9 | Imbalance contract-fee step null join | Closed | V17 (Sprint 51) | — | core |
| #131196 | §9 | Lump-Sum Rate Object misspelled (RFS) | Closed | ONK Hotfix 1 | — | ONK |
| #1754567 | §9 | Imbalance Manual CICO fields not clearing (Web) | Acceptance | 2025.20 (iter 25.20) | — | core |
| #1553885 | (API) | ONEOK Sales Rate API FeeDetail insert failures (overlapping records, large batch) | Verified | 2022.x hotfix family | 22-00823651 / 22-00285346 | ONM |

### QPTM overlap — swept in by title search, route to QPTM ADO skill (NOT TIPS)
| Bug | Why it's QPTM | SF Case |
|---|---|---|
| #1603117 | IN51A/INX51A CICO double count — TSP/Service Request, `INRPTS_51_AGMT_BAL_STMT_VW` (pipeline balancing) | 23-00902494 (ENT) |
| #1632428 | "Rate Tripled K241 Flex Charges" — Invoice Detail Maintenance / TSP / TOC, BLINVGEN | 23-00929118 (QTR) |
| #1674944 | Invoice Header/Detail/Billing **Voucher** $0.01 — `BLTRAN_*`/`BLRPTS_10_*`, BLINVGEN2 rounding (QPTM billing) | 24-00965437 (TGL) |
| #1675211 | Cash-Out Imbalance / **INCUVCALC** / ALLOC_CUV pipeline (QPTM+TIPS reimpl, but the bug is pipeline cash-out) | 24-00967726 (GNP) |
| #1741015 | Location Maintenance Fuel Rate won't clear (Web) — QPTM Location Maintenance | 25-01024671 (Great Basin) |
| #1730219 | OTC Reconciliation **regulatory** report lease fee — Oklahoma Meter Master / `QRPTS_REG_OTC_*` (upstream-regulatory, not core invoice) | 25-01019922 (ETP) |
| #1755703 | Rate tiers can't resolve with DELK basis — QPTM billing (BLINVGEN, Invoice Maintenance, TOS/charge-basis); closed as **config**, not a defect | — (DSU) |

---

## 11. Diagnostic Pointers

- **Prove report-vs-data:** run the Settle Fees / Settle Prod query for the same plant/acct-dt/prod-dt/meter and compare to the document. Right query + wrong doc = view/Crystal defect (§3/§5/§7).
- **Which CCT is the meter actually using?** Query **`QTRAN_PAYSTATION`** — meter-split CCT overrides routinely differ from what you configured (the trap in #1674818).
- **Rate vs Applied Rate:** open the report's view; if the column maps to `QRPTS_INVOICE_DTL_VW.RATE` (not `APPLIED_RATE`) you have the §5 family. volume × Applied Rate must equal the $ amount.
- **CAN "table could not be found":** Crystal → Set Database Location; the report is pointing at a view absent in `QRMTIPS_CAN` (vs `QRMTIPS`). See #236409 (`QRPTS_SETTLE_INV_TOTALS_CC_VW`).
- **Escalate / settle batch hard error:** read the process error verbatim — ORA-12899 = client column too short (#1648566); "Operating system error" after PLANTOWN = missing registered SQL for that DB platform (#1736767, `Sel_H2SCO2_PCT`).
- **PPA not netting:** look for the prior-month row written as **OR** where it should be **R** in `QRPTS_INVOICE_DTL` (#1573301); compare two meters on the same invoice — one nets, one doesn't = settle row-ordering.
- **Posted vs non-posted gap:** posted reads `QPOST_RPTS_*`, non-posted `QRPTS_*`; a field present pre-post and gone post-post = posted view lagging.
- **Confirm the fix is in the client's build:** IntegrationBuild is blank, so read the PR target branches + release tags on the WI, and verify in release notes before promising a client their build has it (esp. #1352683, which was deliberately NOT back-patched).

---

## 12. Escalation — is the client's build fixed?

```
Reproduced the defect and matched it to a bug above?
│
├─ Bug Closed/Verified AND PRs target the client's GA / a client patch they consumed?
│     → Confirm in release notes (IntegrationBuild blank). If consumed → re-test in their env; if not
│       → request hotfix/patch (Maintenance) citing the bug # and PR list.
│
├─ Bug Closed but fix DELIBERATELY limited (e.g. #1352683 Rate→Applied: only 2019.10 + develop) ?
│     → Do NOT tell the client it's in their build. Engineering must re-package the DB change for
│       their build line (sysgen-view ordering risk — see §5). Escalate with that caveat.
│
├─ Client-specific report/metadata bug (most Maintenance-branch items) ?
│     → No core hotfix needed; fix lives in <CLIENT>.TIPS.Reports / .Metadata / .Database. Route to
│       Maintenance + Upgrades team to re-package the client patch. Forward-merge to develop + last
│       2 GAs is standard so future GAs carry it.
│
├─ Data / config (not a code defect) ?  e.g. #1799931 (timeslice data conversion), #1647805
│     (required-column config), #1755703 (TOS-charge-basis config), #1697539 (missing UOM code) ?
│     → Cloud Ops / PS COE script or config; name the exact table/column/screen.
│
└─ Looks like one of the QPTM-overlap rows in §10 ?  → it's QPTM, not TIPS. Hand to the QPTM ADO
      skill / QPTM Maintenance pod; don't fix it here.
```

**Routing rule of thumb:** view/Crystal math + core process-step defects with clean config → **Engineering/Maintenance** (cite bug # + PR list + the inferred build). Eff-date / timeslice / required-column / CCT type / missing UOM-code / TOS-charge-basis problems → **Cloud Ops / PS COE** with the exact screen and key named.

---

## Mining notes, classification caveats & dead ends

- **WIQL count (Step 1):** the two specified area branches with the 8 functional terms returned **763** Closed/Resolved bugs (`rate`/`fee` over-match verbs like "operate/generate" and sweep in QPTM transport billing). I scoped the deep read to the **most-recent-250 by ChangedDate** (per the ~250 cap), batch-got fields, and hand-filtered to **93 functionally-relevant** items (12 dropped as clearly QPTM, 145 dropped as non-functional noise). **bugsMatched = 763; functional-relevant ≈ 93; deep-read = 50.**
- **Build numbers are inferred** — `Microsoft.VSTS.Build.IntegrationBuild` was **empty on 100% of the 50 deep-read bugs**. Every "Build" value here comes from iteration path (YY.NN), `Planning:NN`/release tags, or PR target branches, and is marked inferred. Confirm in release notes before client-facing use.
- **Maintenance branch is mixed QPTM+TIPS** (the task warned). I kept TIPS settlement-invoice / rate-schedule / CCT / escalation items and dropped QPTM nomination/offer/RFS-style and transport-billing items. **7 swept-in QPTM bugs are listed explicitly in §10** so the next miner doesn't re-pull them as TIPS: #1603117, #1632428, #1674944, #1675211, #1741015, #1730219, #1755703. Borderline: #131196 (ONK lump-sum is RFS/QPTM-adjacent but delivered in a TIPS-CAN metadata context — kept with a note); #1730219 OTC Reconciliation is a **regulatory** report (Oklahoma Meter Master) more than core invoicing.
- **Dead ends:** #1768304 (SRI logo size) was **Rejected** (could not reproduce). #1755703 (DSU rate tiers) closed as **config**, not a defect. #1553885 (ONEOK Sales Rate API) is real but is an **API/integration** defect (FeeDetail insert failures on large/overlapping batches) rather than an invoice/report defect — parked in §10 with no cluster.
- **Many WIs are 3-part chains** (original → FVF/fail-verify → "Part 2"): #1609124→#1619956→#1627661 (PEM PPA); #1573301 spawned #1661513/FVF. Treat the chain as one fix when checking a client build.
- The richest **dev root-cause comments** were on: #1352683 (RATE→APPLIED_RATE view family + sysgen ordering), #1573301 (m_Sel_Paystation ORDER), #1736767 (Sel_H2SCO2_PCT + Fee-vs-Price), #1767237 (MTR_SFX join), #1585257 (SCTRL_BA_TAX_ID timeslice), #1674818 (0-price avg), #103794 (long-int truncation), #1768945 (MARG_FEE_IND).

---
*Skill created 2026-06-14 from ADO TIPS bugs. ADO accessed READ-ONLY. Companion: `TIPS Assitant\SKILL_TIPS_Invoice_Billing_Rates.md` (SF cases). Deep-read bugs: 84246, 103794, 109121, 131196, 177330, 190083, 236409, 238830, 264857, 264928, 280352, 1352683, 1445777, 1543615, 1544446, 1553885, 1571959, 1573301, 1583754, 1585257, 1593263, 1596465, 1603117, 1607431, 1609124, 1612911, 1619956, 1627661, 1632428, 1633673, 1640160, 1647805, 1648566, 1650590, 1674818, 1674944, 1675211, 1697539, 1702168, 1715559, 1730219, 1736767, 1741015, 1745110, 1754567, 1755703, 1767237, 1768304, 1768945, 1799931.*
