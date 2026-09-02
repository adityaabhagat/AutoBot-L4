# SKILL: TIPS Reporting & Statements Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-11 | **Product:** My Quorum TIPS (oil/gas transaction & accounting)
**Scope:** Gas/settlement statements (Report ID 45 family), statement generation/printing/distribution, settlement invoice reports, regulatory & severance-tax reports (TX RRC, OK OTC, ND EDI, NM, KS, CO), imbalance reports (IN01/IN02V/IN02MTR), allocation/volume reports (AL01R, ALR_24/55, Daily Position), owner/WI/CO&O/pipeline statements, Interactive Reports (Exago/CAW), Excel/export issues, external-shipper report access, Post Results posting.
**Use When:** Any TIPS case in categories Reporting, Ad Hoc Reporting, Regulatory Reports, Regulatory, Gas Statements, Statement Generation / Distribution, Post Results — a report/statement is blank, doubled, mis-totaled, won't print/distribute, fails to run, or a regulatory file is rejected by the state.
**Companion:** SKILL_Allocations.md (QPTM allocation engine; TIPS PTR/Evolution overlay), SKILL_Salesforce_Queries.md.

> Evidence base: 1,945 closed TIPS cases across the 7 reporting/statement categories; 354 actionable (Software Defect 204, Application Configuration 131, ChangeConfig 19) mined in full, plus 30 Training/Customer Error cases for the Expected-Behavior section. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Decision Tree](#2-decision-tree)
3. [Gas / Settlement Statement Content Wrong or Missing (HIGH FREQUENCY)](#3-gas--settlement-statement-content)
4. [Statements Not Generating / Not Populating / Won't Print](#4-statements-not-generating)
5. [Report Distribution & Statement Emailing](#5-report-distribution--statement-emailing)
6. [Regulatory / Severance Tax Reports (TX, OK OTC, ND EDI, NM, KS, CO)](#6-regulatory--severance-tax-reports)
7. [Interactive Reports / Exago / CAW Infrastructure](#7-interactive-reports--exago--caw)
8. [External (Shipper) Users — Blank Reports & Access Errors](#8-external-users--blank-reports--access)
9. [Imbalance Reports (IN01 / IN02V / IN02MTR)](#9-imbalance-reports)
10. [Allocation / Volume Reports — Doubling & Duplicates](#10-allocation--volume-reports--doubling)
11. [Settlement Invoice / Invoice Reports](#11-settlement-invoice--invoice-reports)
12. [Owner / WI / CO&O / Pipeline Statements](#12-owner--wi--coo--pipeline-statements)
13. [Daily vs Monthly (PSTA) Tie-Out Issues](#13-daily-vs-monthly-psta-tie-out)
14. [Excel / Export Failures](#14-excel--export-failures)
15. [Post Results / Posting Failures](#15-post-results--posting-failures)
16. [Expected Behavior / User Education](#16-expected-behavior--user-education)
17. [Known ADO Items](#17-known-ado-items)
18. [Diagnostic SQL](#18-diagnostic-sql)
19. [Escalation Guidance](#19-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom | Likely cause | First check |
|---|---|---|
| Gas statement value missing/wrong for one product or fee | Crystal formula pulling wrong DB column, or fee-type→fee-bucket config | Compare report view vs `QTRAN_PAYSTATION`; check fee bucket config (§3) |
| Duplicate statement pages for same meter | `ASSIGN_NO` missing from settle-gas-stmt views; meter-split w/o MTR_SFX filter | `QRPTS/QPOST_SETTLE_GAS_STMT_*_VW` definition (§3) |
| Posted statement wrong but non-posted OK (or vice versa) | Report wired to the wrong table family (`QRPTS_*` = non-posted vs `QPOST_RPTS_*` = posted) | Which view the report definition uses (§3, 24-00954713) |
| Gas statements not populating at all, no error | `SP_QTIP_SETTLE_GAS_STMT` silent error swallow (INVOICE_NO truncation) | Run the proc manually / check column lengths (§4, 23-00919231) |
| Statements won't print / memory error | Oversized logo image in Crystal template | Logo file size (§4, 24-00960226) |
| Report Distribution not sending | Email service "Active" unchecked, `QRMTIPS_CAN` code-table setup, missing JS include (client web) | Email reporting service config (§5) |
| State rejects file: "volume cannot be zero with a reported value" | TX Reg zero-value/zero-volume handling | Config `CHECK_FOR_ZERO_VAL_ZERO_VOL`; code fix for gross-vol>0/value=0 (§6) |
| Regulatory report duplicate lines | Bad data in reg staging tables | Data script cleanup (§6, 21-00664048) |
| ND EDI tax summed across facilities | T-12 header query not filtered by TaxPayerNo | `m_nSel_ND_Tot_Ext_Tax` fix / run REGRPTSEV by Taxpayer No (§6) |
| Interactive Reports "Oops something went wrong" | Exago config keys / API key / network-logon password / cache | Global config Key Group EXAGO (§7) |
| External user gets blank report, internal OK | External view missing columns, CAW replication lag, deleted security object | External `*_VW` definition; CAW sync (§8) |
| IN01/IN02V blank or doubled | Report table map hidden+required; external prior-month dup defect | Report table mapping; build level (§9) |
| Allocation report columns doubled after facility change | Views not handling facility time slices when joining `QCTRL_PLANT_VALID_PROD` | New time slice on Facility Definition? (§10, ADO #1637427) |
| Invoice subtotal doubled (CICO) / dup fees on meter splits | `SP_QTIP_POP_INVOICE_DTL` staging proc; missing MTR_SFX filter | (§11) |
| WI/owner statement columns shifted or 2x pages | Posted report view defect (`QPOST_RPTS_WI_STMT_*_VW`); zero-production column shift | (§12) |
| Daily and monthly runs don't tie (POP%, fixed fuels, residue) | PSTA daily-vs-monthly defects (ETP Daily project family) | (§13) |
| Excel export "Unlicensed Product" error | Citrix profile corruption | Reset Citrix profile (§14, 24-00981110) |
| Batch processes fail with no message log | `PROCESS_LOG_ID` sequence overflowed int max | Reset sequence (§15, 22-00711934) |
| Report blank right after month start | Batch jobs (Measure→Alloc→Settle) not run yet | Expected behavior (§16) |

---

## 2. Decision Tree

```
TIPS reporting/statement case
│
├─ Is it a STATEMENT (gas/settlement/owner/pipeline)?
│   ├─ Wrong/missing VALUES on the statement ......................... §3 (views/formulas/fee config)
│   ├─ Statement DOESN'T GENERATE or print ........................... §4 (SP_QTIP_SETTLE_GAS_STMT, logo, region security)
│   ├─ Not EMAILED/DISTRIBUTED ....................................... §5 (Report Distribution config, QEMAIL)
│   └─ Owner/WI/CO&O/pipeline statement format/columns ............... §12
│
├─ Is it a REGULATORY/TAX report or state file (TX/OK/ND/NM/KS/CO)? .. §6
│   ├─ State rejection error → config key or known code fix
│   ├─ Duplicate lines → data script
│   └─ Report ≠ GL/CSV → client tax config (deductions, tax basis)
│
├─ Is it INTERACTIVE REPORTS / query screens / CAW? .................. §7 (Exago config, CAW sync, report-type mapping)
│
├─ EXTERNAL user only (internal works)? .............................. §8 (external views, CAW replication, security objects)
│
├─ IMBALANCE report (IN01/IN02V)? .................................... §9
│
├─ Allocation/volume report DOUBLED or duplicate rows? ............... §10 (time-sliced facility joins)
│
├─ INVOICE report? ................................................... §11
│
├─ Daily vs monthly numbers don't tie (PSTA)? ........................ §13
│
├─ Excel/export file problem? ........................................ §14
│
├─ POSTING / Post Results process failure? ........................... §15
│
└─ Report just "blank" or user question? ............................. §16 first (batch jobs run? right plant/filters? posted vs non-posted?)
```

---

## 3. Gas / Settlement Statement Content

The largest actionable cluster (~45 cases). The gas statement (core Report ID 45 + client variants) renders from `QRPTS_*` (non-posted) and `QPOST_RPTS_*` (posted) views over `QTRAN_PAYSTATION` settlement data, with Crystal Reports formulas on top. Three recurring root-cause families:

### 3a. Report view / table-family defects
| Issue | Root cause / fix | Case |
|---|---|---|
| Duplicate gas statements for the same meter | `ASSIGN_NO` column from `QTRAN_PAYSTATION` was missing in both non-posted views (`QRPTS_SETTLE_GAS_STMT_CTR_VW`, `QRPTS_SETTLE_GAS_STMT_GEN_VW`) and the matching `QPOST_*` views — added | 23-00892449, follow-up collateral 24-00991508 |
| Posted statements missing Product & Inlet Volumes (non-posted OK) | Report read non-posted pen table `qrpts_alloc_vol_stmt_pen` instead of `qpost_rpts_alloc_vol_stmt_pen` | 24-00954713 |
| Incorrect Net Value Settlement total per contract | New views created for Report ID 45 to total across the entire contract regardless of Assignment Number (posted + non-posted) | 24-00949450, 24-00991866 |
| Liquid Settlement section blank on PDF | Column suppression fired if ANY product had zero VALUE_PR; engineering removed suppression, blanks individual zero products instead | 24-00952565 |
| WI statement / pipeline statement missing one meter/contract | Stored proc joined on accounting date instead of production date; or proc items dropped after a rename | 24-00973200, 24-00948273 |

### 3b. Crystal formula / template defects
| Issue | Root cause / fix | Case |
|---|---|---|
| Missing JCEEP C2+ Sale Price (meter level) | Crystal formula pointed at wrong DB column; edited to pull the price column (delivered Patch 3 / 2024.10) | 24-00949550 |
| Wrong JCEEP C2+ to-Sale M3 total (contract level) | Total formula summed the wrong component formulas (`sum_of@liq_sum_jceep_liq` chain) — corrected | 23-00892448 |
| GST# missing (Report ID 45) | Formula referenced `ctrpty.usr_custom2`; value actually lives on `CTR_PARTY_BA_NO` — re-mapped | 23-00877623 |
| Analysis GPM total doesn't foot | Removed methane, nitrogen and CO2 physical constants from the GPM total | 23-00888471 |
| Wellhead BTU shown wrong | Always show the contractually adjusted BTU Factor in the Wellhead Information section | 23-00888461 |
| Production date format inconsistent | New field needed format matching the existing fields | 24-00983765 |

### 3c. Fee / CCT configuration (Cloud Ops or client config — NOT code)
| Issue | Root cause / fix | Case |
|---|---|---|
| Blending Services Fee not showing | Statement pulled Fee Buckets; updated to pull Fee Types | 23-00888456 |
| CO2/H2S Treating Fee on one line, doubled volume, no rate | Fee-type → fee-bucket configuration | 23-00888735 |
| NM GRT not in fee detail section | Advised to use the fee bucket available for the core gas statement | 26-01067726 |
| Theoretical gallons / shrink wrong | New user-defined formula (weighted-avg price) tied to a rate schedule and attached to the CCT per producer — avoided a code change | 25-01006146 |
| Gas Daily pricing makes statement unreadable | CCT changed to monthly settlement; daily pricing aligned to WAVG formula schedule | 23-00888882 |
| Fixed fuels not showing on statements | Asset config needed for field fuels / fixed fuels/deducts / 1% FL&U scenarios | 25-01003960 |
| Values appear only after Settle re-run | Run the Settle job again — values for NGL Sale/TIK volumes appeared after second run | 24-00954711 |

> **Fix recipe:** (1) confirm whether the underlying `QTRAN_PAYSTATION` / allocation data is correct — if yes, it's the report layer; (2) determine posted vs non-posted and check the view family used by the report definition; (3) if a single field is wrong, suspect a Crystal formula column mapping; (4) if a fee is missing/merged, check Fee Type vs Fee Bucket config before escalating to Engineering.

---

## 4. Statements Not Generating

| Issue | Root cause / fix | Case |
|---|---|---|
| Gas statements not populating, NO error raised (recurring) | `SP_QTIP_SETTLE_GAS_STMT` had `''` instead of `NULL` in its error handler, swallowing "string or binary data would be truncated". Real error: proc builds `INVOICE_NO` as `MMDD-{CTR_NO}` and `QTIP_RPTS_SETTLE_GAS_STMT.INVOICE_NO` was VARCHAR(10) — too short. **Fix: widen INVOICE_NO to 17.** | 23-00919231 |
| Statements won't print — "not enough memory" | Crystal logo image too large; replaced with 50%-smaller logo | 24-00960226 |
| Crystal logo issues on Invoice + Gas Statement after upgrade | Logo/template packaging — verify client logo vs Quorum logo after upgrades | 25-00998491, 26-01083363 |
| Blank pages between statements | Reduced white space between pages in the report template | 22-00571453 |
| Printing "Posted & Non posted" together errors | Added combined view `QALL_RPTS_SETTLE_GAS_STMT_VW` (client CCI) to serve both at once | 22-00824313 |
| Plant statements not printing for a user | User missing the **regions** in the Region tab of Security User Setup | 23-00874874 |
| Keepwhole statements not generating | CCT used statement type DC which internally maps to NP; code/report view skips keepwhole when statement type cd = NP — fix the CCT statement type | 23-00875720 |
| Gas statement w/ "view contract summary" extremely slow | Engineering added a DB index | 25-01063079 |
| Gas statement flat-file generation broken | Defect in the flat-file stored proc | 22-00679799 |
| Statements bad after patch/upgrade | Patch recompiled in wrong order (25-01033650); always re-check statement output after every TIPS patch | 25-01033650, 24-00954713 |

---

## 5. Report Distribution & Statement Emailing

| Issue | Root cause / fix | Case |
|---|---|---|
| Report Distribution not working in PROD | "Active" checkbox unchecked in the email reporting service config; duplicated export files traced to bad `QRMTIPS_CAN` code-table setup | 23-00904297 |
| Report Distribution screen broken in client web | `ReportDistributionHdr.js` not added as content include in `<CLIENT>.TIPS.Application.Web` solution (MKW) | 24-00973800 |
| Distribution doesn't exclude Inactive BAs / add a report to distribution | Adding a report (e.g. Gas Statement LINSTMT) to the Report Distribution screen is a **Feature** (ADO #1769540) — per-report enablement, not config | 25-01048912 / 25-01048919 |
| Two notices combined into one email | `QEMAIL` runs every 5 minutes and merges submissions inside one interval — leave >5 min between posting submissions | 24-00993505 |
| Settlement export logged but no email sent | `QEMAIL` releases the statements after the event is logged — run/wait for QEMAIL | 26-01084450 |
| Bringing 2023.04 Report Distribution into 2022.10 | Backport request — handled per-client | 23-00907206 |

---

## 6. Regulatory / Severance Tax Reports

~32 actionable cases across Texas RRC/Comptroller, Oklahoma OTC, North Dakota EDI (T-12/NDOE), New Mexico, Kansas, Colorado. Engine = **Regulatory Interface Master / Generate Regulatory Reports (REGRPTSEV)** writing reg staging tables, then state-format report/CSV/EDI/XML generation; status tracked in `QTRAN_REG_STATUS`.

### Texas
| Issue | Root cause / fix | Case |
|---|---|---|
| Comptroller rejection "Volume cannot be zero" (value reported, volume 0) | Config `CHECK_FOR_ZERO_VAL_ZERO_VOL` added to the Batch key group (default 1); options discussed with client | 24-00951593 |
| Critical error when Gross Volume > 0 with Gross Value = 0 (gas lift / marketing / tax liability) | Code fix to zero the Gross Volume in reporting tables for those scenarios | 23-00917114, 23-00826022 |
| Reversals on previously suppressed records wrong | TX Reg logic updated to use suppressed records as the source for the reversal record/value | 24-00968268 |
| TX exemption type / API change; $87/day exemption | Reg logic updates (enhancement-flavored defects) | 23-00885480, 25-01003810 |
| ET scenarios long-term fix; slow `QHIST_CONTRACT` view | Contract Change report view optimized + fixes | 23-00818462 |

### Oklahoma (OTC)
| Issue | Root cause / fix | Case |
|---|---|---|
| OTC report ≠ GL ≠ CSV sent to state | Client tax config — e.g. marketing deductions not used in the severance accrual calc; "client configuration changes needed" | 24-00954627, 25-01009296 |
| Want to omit net-zero lease records | Config key `OMIT_LEASE_WITH_NO_NET_CHANGES` = TRUE | 24-00974439 |
| Gross Volume column shows Gross Value | Tax Basis config under Global > Tax Master changed from VALPRGE to OKVOL (OKRF & OKMP) | 24-00969521 |
| OTC Recon subtotal/grand-total columns overlap; duplicate rows | Views updated to return DISTINCT records; column widths/fonts adjusted | 25-01019922, 25-01041592 |
| Tax Calculation Report 82B field cutoff | Field size defect | 24-00978619 |
| OTC Recon / Reg Interface Master fails on unique constraint (MSSQL) | Open bug ADO **#1796532** (Proposed) | — |

### North Dakota / Kansas / Colorado / New Mexico
| Issue | Root cause / fix | Case |
|---|---|---|
| ND EDI: NDOE tax summed across two facilities (line 8118) | Query `m_nSel_ND_Tot_Ext_Tax` now filters by TaxPayerNo + TranTypeCd (T-12 header group-by had them, column overrides didn't) | 23-00923092 |
| ND EDI must generate per taxpayer | REGRPTSEV got an optional **Taxpayer No** parameter | 23-00905216 |
| ND EDI wrong sequence numbers; runtime growth | Code fixes (older builds) | 20-00598154, 20-00598107 |
| KS manual adjustments reversed by plant rerun | Process-handling guidance provided (operational, not code) | 20-00598116 |
| CO "Post Regulator Results" failed | Reset `posted_ind = 0` for the month in `QTRAN_REG_STATUS`, re-run | 21-00670983 |
| NM_SEV_XML process fails for agency 30001NM | Resolution not recorded in case (mined data unclear) | 25-01022219 |
| NM GRT missing in fee detail | Use core gas-statement fee bucket (config) | 26-01067726 |

### Cross-state
| Issue | Root cause / fix | Case |
|---|---|---|
| Registry Volumetric & SAFOAF reports duplicate lines | **Data script** to clean bad staging data (root cause chased separately) | 21-00664045, 21-00664048 |
| Regulatory dataset not set up — processes can't run | Load Reg Form Configuration data (implementation config) | 23-00888875 |
| Registry Reporting picklist missing facility types | Added the other facility types to the REG REPORTING picklist | 26-01083995 |
| Tax report error from BA in wrong county | Erasing the Override Party BA # resolved it; BA in Reg Reporting module had wrong county | 25-01042076 |
| Reg Interface Master "facility not valid for PPA prod date" | Validation defect fixed in later upgrade; workaround available | 21-00666382 |

---

## 7. Interactive Reports / Exago / CAW

Biggest infrastructure cluster (~51 cases incl. overlaps). TIPS Interactive Reports run on **Exago** against the **CAW** (Common Analytics Warehouse) replica, fed by DataSync (`TIPSDSDataHelper` / `QTIPExagoDataHelper` connections) and the `CAWDATAFS` job. Failures are almost always **environment/config**, owned by Cloud Ops:

| Symptom | Root cause / fix | Case |
|---|---|---|
| "Oops, something went wrong" before any report loads | Config changes + recreate the Exago **API key** + clear both TIPS and ESuite cache | 24-00984396 |
| Interactive reports error in PROD | Exago **network-logon password** in app config differed from the actual password — update it | 24-00947847 |
| Interactive reports fail in one env (UAT2) | Wrong connection ID — set to `QTIPExagoDataHelper` | 24-00917031 |
| Error running interactive reports in UAT | Missing AD groups on the file share (`...\AppFiles\TIPS`) + stale EXAGO key-group config entries deleted | 23-00917478 |
| Can't run interactive queries — config absent | Exago configuration values missing in global config (Key Group: EXAGO) — provide/load them | 23-00883065 |
| Performance bad after Exago upgrade | Settings missed when upgrading Exago v19→v20; interactive report settings restored | 20-00561514, 20-00561498 |
| `CAWDATAFS` job failing | DataSync Connection's .NET Connection Type was set equal to SQL CONNECTION — deleting that record fixed it | 25-01015982 |
| Report shows stale/partial data (e.g. AL01R only through gas day 15) | Plant out of sync in TIPSCAW after a `TIPSDSDataHelper` connection-management change — reverted, CAW resynced | 23-00893159 |
| ESuite report types not in dropdown / reports missing | **Process & Report Type mapping** must be (re)done as part of upgrade (myQuorum) | 25-01017988, 23-00909356, 23-00906496 |
| JE Query returns duplicates in Web (20 vs 8 in Classic) | Web query-screen defect (Interactive Reports Replacement family) | 24-00939816, 23-00820881 |
| Report runs but table-map conflict | Report table map was required **and** hidden → conflict; unhide/fix mapping | 25-01046205 |
| "Previous Run Parameters" → "Value is required" though filled | Hotfix-introduced defect (repro: env with hotfix errors, env without doesn't) | 24-00943563, 24-00994198 |
| Recents/favorites not preserved | Defect tied to developer-rights flag | 23-00830669, 23-00830670 |
| PROD-wide Interactive Reports outages (MOM/PML/MER/UTG/BMH) | Cloud Ops incidents with RCA tasks | ADO #1790561, #1790338, #1726379 |
| CAW context error when running reports | Run the **REPOSCRUB** batch process to clear context data | 26-01066902 |

> **Recipe:** for any "interactive reports broken" case, collect environment + exact error, then check in order: (1) EXAGO key-group config values present and correct, (2) Exago network-logon password/API key, (3) DataSync connection IDs and CAW sync freshness, (4) process & report-type mapping if it's post-upgrade, (5) cache clear. Escalate to Cloud Ops, not Engineering, unless a query-screen defect reproduces in a healthy env.

---

## 8. External Users — Blank Reports & Access

External (shipper/producer) report runs go through dedicated **external views** and CAW; internal-vs-external differences are the diagnostic gold:

| Symptom | Root cause / fix | Case |
|---|---|---|
| AL01R blank for external users only | External client view definition missing columns the Crystal report references (`TOTAL_FUEL_REC_HV`, `TOTAL_DEL_FUEL_HV`) — report errored to blank | 24-00976410 |
| BL01 internal vs external XLS data differs | `APPLIED_RATE` column absent from some core/system external generated views | 24-00963876 |
| External users: Internal Server Error running reports | Security object `QVpGloablBatchReportExecution` had been deleted — restored deleted security objects | 24-00970141 |
| AL01R external blanks after go-live | Environment connection (CAW replication) issue | 24-00960457 |
| IN02V blank for externals, current month only | Defect (internal fine, prior month fine) — code-level | 24-00969454 |
| Shipper report "Auth Check Failed" | User security/auth config | 24-00926151 |
| RPTGEN_INV generates ALL customers' invoices for one user | BA scoping on the user profile not applied by the report — verify BA setup, then defect | 24-00969641 |
| User can't print plant statements | Add user to both regions in Security User Setup Region tab | 23-00874874 |
| Report access complaints | Security privileges for reports (report-level security groups) | 23-00885512, 22-00867456 |
| SSO stopped after enabling AES 128/256 on QQM account | Keytab/SPN must be regenerated — validate SPN + Keytab per install guide | 26-01091774 |

---

## 9. Imbalance Reports

| Issue | Root cause / fix | Case |
|---|---|---|
| IN02V vertical display not summarizing by day (externals see many pages) | Core report behaves differently per mapping code — bug fixed in 2024.04; confirm client build ≥ fix | 26-01096894 |
| IN01 monthly imbalance returns blank | ESuite module flagged INT (wrong module assignment) — under engineering review; also verify Customer Account Adjustments + facility batch jobs ran | 26-01084536 |
| Imbalance reports won't run in env | `REPORTPATH` variable pointed at wrong file path — fixed and redeployed reports | 24-00955776 |
| Daily Imbalance report errors | Deprecated meter-type report still selectable — removed from availability | 24-00940776 |
| External prior-month run doubles lines and totals (2 lines/day Rec+Del) | Code defect, external path only | 24-00980710 |
| Wrong level of detail on vertical view | Report defect | 24-00964918 (ADO #1696982+, #1702054) |
| Monthly Imbalance report spacing | Core report spacing bug — fixed | 24-00943148 (ADO #1805277 Closed) |
| Report table map conflict (PRD imbalance reports) | Table map required+hidden | 25-01046205 |

---

## 10. Allocation / Volume Reports — Doubling

The signature defect family: **report views that don't handle facility time slices**.

| Issue | Root cause / fix | Case |
|---|---|---|
| Monthly Allocation Summary & Marketing Shrinkage reports double after adding a Facility Definition time slice (e.g. new Valid Products) | All views for both reports updated to account for time-sliced facilities when joining `QCTRL_PLANT_VALID_PROD` | 23-00911334 → ADO **#1637427** (Closed) |
| Liquid Marketing Report volumes doubled | Backend proc that seeds the report tables corrected | 21-00643238 |
| Invoice/TIK/NGL reports duplicate rows | Contractual gross TIK dup records (20-00521905); NGL Offload duplicating settlement meters (22-00814053); XCL invoice dup contract rows (20-00526792) | — |
| Liquid Allocation by Product ignores Prod_cd parameter | Report parameter defect | 23-00908788 |
| ALR_24 shows whole-plant volume instead of per-Proc-K | Resolution pattern unclear from mined cases (no recorded fix) | 24-00966517 |
| ALR_55 Daily Meter Split errors (Evolution) | Client-specific report defect | 24-00953265 |
| AL07M doesn't group by details | Report grouping defect | 23-00820310 |
| Older "Statements" dup/bad data | Scripts deployed to clear bad data from `QTRAN_ALLOC_VOL` and `QTRAN_TRNX_ID` | 22-00668434 |

> **Rule of thumb:** doubling that starts the month a facility/contract/product time slice was added = view join missing eff-date qualification. Reproduce by comparing report output before/after the slice date; fix is a view change (Engineering), with a possible data script if staging tables already double-seeded.

---

## 11. Settlement Invoice / Invoice Reports

| Issue | Root cause / fix | Case |
|---|---|---|
| Duplicate fees when meter splits share one contract (A/B) | Added **MTR_SFX filter** to the Settlement Invoice Report | 25-01055412 |
| CICO doubling in invoice subtotal; wrong totals for non-CICO fee types | Updated `SP_QTIP_POP_INVOICE_DTL` (invoice staging table population proc) | 22-00556365 |
| Pricing decimals truncated | Increased invoice display to 4 decimal places | 25-01032032 |
| Invoice settings/format wrong after upgrade | Report re-imported by services team; packaged in patch (ADO #1669485 / patch #1667626) | 25-01022605 |
| Invoice Documents Report empty before a date | Conversion issue — some `QPOST_*` tables missing from migration | 24-00940777 |
| Invoice Backup Details duplicating detail lines | Report defect (v17) | 23-00934106 |
| 13th-month invoice posting broken | Posting-process bug fix + tables added to the Post code table | 20-00588992, 20-00583589 |
| Sales invoice doubles amount after UOM change on contracts | Defect on UOM change handling | 22-00711968 |
| QRPTS_INVOICE_DTL_CAN bug | CAN-layer invoice detail view defect | 25-01049592 |

---

## 12. Owner / WI / CO&O / Pipeline Statements

| Issue | Root cause / fix | Case |
|---|---|---|
| WI Operator Statement posted version doubles page count / misformatted | Corrected posted-results DB view `QPOST_RPTS_WI_STMT_PEM_VW` | 24-00981587 |
| WIOS columns shift when meter has Opening Inventory but zero Production | Report ignored zero production and shifted sale/closing-inv volumes left — adjusted to keep sales in correct columns | 23-00934076 |
| Pipeline statement missing MMBTU for one meter | Stored proc items dropped after a name change — proc fixed | 24-00948273 |
| Pipeline statement missing a contract | Proc joined accounting date instead of production date | 24-00973200 |
| Allocated WI Owner Statement totals wrong ("Product Others") | Changed the Crystal group for the producer-total section | 23-00908572, 24-00970732, 23-00889038 |
| Operator/measurement statements not populating | Meter Definition settings + WH/OVOL product line changes so meters land in the report source tables | 23-00938635 |
| CO&O report rounding/total capacity/mailout | Throughput-by-owner rounding matched to total; mailout changes | 23-00908581, 23-00889912, 24-00955352, 23-00888715 |
| POP statements don't tie / Keepwhole statements | CCT statement-type config (see §4 keepwhole) | 23-00925881, 23-00875720 |

---

## 13. Daily vs Monthly (PSTA) Tie-Out

ETP/Enterprise "Daily" project family (~14 cases, tracked as numbered "Daily Issues"). Daily runs and monthly runs of settlement (PSTA env) disagreed:

| Issue | Status / fix | Case |
|---|---|---|
| WAH residue volumes doubled in monthly (wrong on T27D BOBJ report) | Resolution not recorded in SF (handled in project channel) | 24-00961961, 24-00961962 |
| Applied POP% not populating for monthly records (Residue only, 0 monthly) | Resolution not recorded in SF | 24-00952968, 24-00961965, 24-00948146 |
| Fixed fuels data daily vs monthly don't tie (VOL_UOM) | Resolution not recorded in SF | 24-00948144 |
| Fixed Fuels process 35+ min for one plant | **CCT data cleanup** then re-run — no delays after | 24-00950082 |
| `s_decimal` not calculated for SRA meter in PSTA | Data/config investigation | 24-00963868 |
| Settle Summary monthly values doubled | Code fix expected; recorded resolution sparse | 24-00943326 |
| GENPTRPRM2 step in GENSHPTR failing for STX plants in scheduling month | Config | 24-00982436 |

> **Caveat:** most "Daily Issue NN" cases carry no Resolution__c — they were worked via the ETP project spreadsheet. Treat this section as symptom recognition (route to the Daily/PSTA owner), not a fix cookbook.

---

## 14. Excel / Export Failures

| Issue | Root cause / fix | Case |
|---|---|---|
| "Unlicensed Product" error exporting to Excel | **Citrix profile reset** fixed it (ADO incident #1688413) | 24-00981110 |
| Excel exports format numbers as TEXT after upgrade | Engineering fix, deployed in patch | 25-01046851 |
| Excel reports won't open / no file created | Client-side: IP connection blocking; or Citrix/infra | 24-00944393 |
| Can't edit/save exported Excel files | Windows patching + Internet Explorer expiry (legacy) | 23-00885999 |
| Excel errors out of Classic | Fixed during environment monthly maintenance | 24-00983885, 24-00985336 |
| Reports won't download automatically (CAW) | CAW download handling defect | 22-00679843 |
| Batch Process Message Log export, meter split export issues | Export feature defects | 24-00963538, 24-00962927 |

> Most Excel/export cases are **environment (Citrix/Office)**, not product. Try Citrix profile reset + another user/machine before escalating.

---

## 15. Post Results / Posting Failures

| Issue | Root cause / fix | Case |
|---|---|---|
| All batch processes failing, Message Log empty, `PROCESS_LOG_ID` went negative | Log-ID **sequence overflowed 2147483647** and wrapped negative — QBS script reset the sequence to 1 | 22-00711934 |
| GMAS batch: "Could not find any entity definition for parent tag: ROW" | Batch/entity definition config in env | 24-00983456 |
| JOURNAL posting process erroring on a step | Removed obsolete step `LDOGSYS` from the JOURNAL process-step ID list (Batch Process Definition; user needs edit permission) | 24-00985228 |
| Post Regulator Results failed (CO) | Reset `posted_ind=0` in `QTRAN_REG_STATUS` for the month, re-run | 21-00670983 |
| Error closing accounting month | Client-specific posting config (Black Hills) | 24-00944542 |
| 13th-month post process | Bug fix + Post code table additions | 20-00588992, 20-00583589 |
| Posted reports missing data after conversion | `QPOST_*` tables missing from conversion | 24-00940777 |

---

## 16. Expected Behavior / User Education

From 30 sampled Training/Customer Error cases — recognize these before scripting or escalating:

| Reported as | Reality | Case |
|---|---|---|
| "Daily Position / Shipper Summary report blank for new month" | **Facility batch jobs (Measurement → Allocation → Settle) haven't run yet** — report populates after the sequence completes. The #1 false alarm. | 26-01100183, 26-01098877, 25-01035727 |
| "Contract shows No Data" | Contract not **posted** after meter-list changes — run the report with non-posted parameters (posted vs non-posted is a report parameter, not a bug) | 25-01042626 |
| "Gas statements missing/wrong" | User filtered the wrong plant; or used wrong meter suffix for delivery breakdown | 25-01032365, 26-01079511 |
| "Settlement export logged but no email" | QEMAIL releases statements on its next cycle — run/wait for QEMAIL | 26-01084450 |
| "Gas statement generated on rerun though Revenue Override unchecked" | Statement generates because the revenue indicator WAS checked — working as designed | 26-01080308 |
| "Error running reports in CAW" | Run REPOSCRUB batch process to clear context data | 26-01066902 |
| "Restore my deleted QQM favorites" | Deleted QQM user favorites cannot be restored, even after access reinstatement | 26-01063999 |
| "How to amend a TX severance filing" | Use current accounting date + original production date, then run the full tax process — record flags as amended | 25-01049178 |
| "Operator parameter ignores agent agreements" | Working as designed — Operator parameter explained | 25-01056975 |
| "JE/JV reports not picking up new BA/contract" | Facility missing from the new contract (master-data, not report) | 25-01056340 |

---

## 17. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1637427** | Feature / **Closed** | PEM — Marketing Shrinkage Allocation Report doubling (time-sliced facility view fix) | §10 | 23-00911334 |
| **#1586547** | Feature / **Closed** | Gas Statement changes for new Oxygen Fee | §3 | 23-00879715 |
| **#1688413** | Incident / **Closed** | CLF — Unlicensed Product error exporting TIPS reports to Excel (Citrix profile reset) | §14 | 24-00981110 |
| **#1769540** | Feature / **PM Acceptance** | SCT — Add "Gas Statement-LINSTMT" to Report Distribution screen | §5 | 25-01048919 |
| **#1669485** | Bug / **Ready for QA** | PEP — Settlement Invoice format issue (delivered via Patch #1667626 Completed) | §11 | 25-01022605 |
| **#1796532** | Bug / **Proposed** | TIPS MSSQL — OTC Recon Report / Regulatory Interface Master fails on unique constraint | §6 | — |
| **#1577710** | DB Change / **Closed** | Update TIPS view `QSTAG_REG_OTC_RPT_CSV_VW` | §6 | — |
| **#1624453** | DB Change / **Closed** | Update OTC views `QRPTS_REG_OTC_PRE_POST_VW`, `QRPTS/QPOST_REG_OTC_GR_PROD_VW` | §6 | — |
| **#1805277** | Bug / **Closed** | Core report spacing issue on Monthly Imbalance Report | §9 | 24-00943148 |
| **#1696982-85, #1702054** | Reqs+Task / mixed | GNM — Daily Operator Imbalance Report (vertical-view detail) | §9 | 24-00964918 |
| **#1711018 / #1711172** | Bugs / **Closed** | Interactive Reports Replacement — TIPS Query Screens (favorites confirmation, filter errors) | §7 | — |
| **#1726379, #1790338, #1790561** | Cloud Ops incidents+RCA / **Closed** | TIPS PROD Interactive Reports not working (MOM/PML/MER/UTG/BMH) | §7 | 25-01015962 |
| **#1803582-89** | Requirements / **Proposed** | IACX — Incorrect Fixed Recovery on Gas Statement | §3 | 26-01087770 |
| **#1540338** | Task / **Closed** | OTC — Settle Tax incorrectly ignoring Contract Rates Fixed Fuels (ETP) | §6 | — |

---

## 18. Diagnostic SQL

Real table/column names from mined case resolutions; verify against the client schema before scripting. TIPS DBs use per-client schemas (e.g. `QRMTIPS`, `ESUITE_QENT` style naming).

### A. Statement source rows for a meter/contract (is the DATA right before blaming the report?)
```sql
SELECT * FROM QTRAN_PAYSTATION
WHERE  CTR_NO = '<CTR_NO>' AND PROD_DT = '<PROD_DT>'   -- add meter/acct-dt filters as applicable
ORDER BY ASSIGN_NO;
-- Duplicate statement pages usually = multiple ASSIGN_NO rows the report view doesn't carry/group (23-00892449).
```

### B. Gas-statement generation silently failing (23-00919231 pattern)
```sql
-- Check the report staging table and the column that overflowed
SELECT MAX(LEN(INVOICE_NO)) FROM QTIP_RPTS_SETTLE_GAS_STMT;
-- Proc: SP_QTIP_SETTLE_GAS_STMT builds INVOICE_NO = 'MMDD-' + CTR_NO  → needs VARCHAR(17), not (10).
-- Also inspect the proc's error handler for '' vs NULL (swallowed THROW).
```

### C. Posted vs non-posted view families (wrong-family wiring, 24-00954713)
```sql
-- Non-posted:  QRPTS_SETTLE_GAS_STMT_CTR_VW / QRPTS_SETTLE_GAS_STMT_GEN_VW / qrpts_alloc_vol_stmt_pen
-- Posted:      QPOST_SETTLE_GAS_STMT_*_VW   / qpost_rpts_alloc_vol_stmt_pen / QPOST_RPTS_WI_STMT_<CLIENT>_VW
-- Combined:    QALL_RPTS_SETTLE_GAS_STMT_VW (client CCI custom, 22-00824313)
SELECT OBJECT_DEFINITION(OBJECT_ID('QRPTS_SETTLE_GAS_STMT_CTR_VW'));  -- confirm ASSIGN_NO present
```

### D. Regulatory posting status (CO/posting failures, 21-00670983)
```sql
SELECT * FROM QTRAN_REG_STATUS WHERE ACCT_DT = '<MTH>';   -- stuck run: posted_ind=1 blocking re-run
-- Recovery used in 21-00670983: UPDATE QTRAN_REG_STATUS SET POSTED_IND = 0 WHERE <month scope>;  (verify-SELECT first)
```

### E. Batch message-log sequence overflow (22-00711934)
```sql
SELECT MAX(PROCESS_LOG_ID), MIN(PROCESS_LOG_ID) FROM QARCH_PROCESS_MSG_LOG;
-- MIN negative / MAX = 2147483647 ⇒ sequence wrapped; QBS reset script required (Cloud Ops).
```

### F. Facility time-slice doubling check (23-00911334 / #1637427)
```sql
SELECT PLANT_NO, EFF_DT_FROM, EFF_DT_TO, COUNT(*)
FROM   QCTRL_PLANT_VALID_PROD
WHERE  PLANT_NO = '<PLANT>'
GROUP BY PLANT_NO, EFF_DT_FROM, EFF_DT_TO ORDER BY EFF_DT_FROM;
-- A report that doubles starting at a new EFF_DT_FROM = view join not time-slice-qualified.
```

### G. Bad statement data cleanup targets (22-00668434)
```sql
-- Tables cleaned by deployed scripts when statements showed dup/bad rows:
SELECT COUNT(*) FROM QTRAN_ALLOC_VOL  WHERE <scope: plant + prod/acct month>;
SELECT COUNT(*) FROM QTRAN_TRNX_ID    WHERE <scope>;
```

---

## 19. Escalation Guidance

**It's a DEFECT → Engineering** when:
- A report view / Crystal formula provably maps the wrong column or drops rows (§3a/3b, §10 time-slice doubling, §12 view fixes) — attach before/after data and the view name.
- Internal vs external (or Classic vs Web, posted vs non-posted) give different results on identical parameters with healthy config (§8, §9, 24-00939816).
- The defect reproduces in a clean/core environment, or matches a known ADO item (§17) — then it's a **fix-version check**, not a new bug.
- State-format logic is wrong (TX reversal handling, ND taxpayer summing) — these have always landed as code fixes.

**It's CONFIG → Cloud Ops (or client admin)** when:
- Interactive Reports/Exago/CAW anything: EXAGO key group, API key, network logon, DataSync connection IDs, CAW sync, REPOSCRUB, file-share AD groups (§7).
- Report Distribution / QEMAIL setup, region security, report security objects/privileges (§5, §8).
- Fee Type vs Fee Bucket, CCT statement type / rate schedule, Tax Master tax basis, reg config keys (`CHECK_FOR_ZERO_VAL_ZERO_VOL`, `OMIT_LEASE_WITH_NO_NET_CHANGES`) (§3c, §6).
- Excel/Citrix/Office problems — Citrix profile reset first (§14).

**It's a DATA SCRIPT → L4 + Cloud Ops deploy** when:
- Regulatory duplicate lines (§6), bad statement rows in `QTRAN_ALLOC_VOL`/`QTRAN_TRNX_ID` (§18-G), `posted_ind` resets (§18-D), message-log sequence reset (§18-E). Always verify-SELECT + transaction + narrow scope.

**Before any escalation:** confirm batch jobs ran for the month, correct plant/filters/posted-flag, and that the underlying transaction data (`QTRAN_PAYSTATION`, allocation queries) is itself correct — roughly half of "report is wrong" cases are upstream data/config or user parameters (§16).

---

*Skill created: 2026-06-11.*
*Based on: 354 actionable TIPS Reporting/Statements SF cases (204 Software Defect, 131 Application Configuration, 19 ChangeConfig out of 1,945 closed) + 30 Training/Customer Error cases + ADO items #1637427, #1586547, #1688413, #1769540, #1669485/#1667626, #1796532, #1577710, #1624453, #1805277, #1696982-85/#1702054, #1711018/#1711172, #1726379/#1790338/#1790561, #1803582-89, #1540338.*
*Data-quality caveats: ~41 actionable cases are titled "Hotfix/Patch N" (delivery vehicles, symptom unrecoverable from SF); the ETP Daily/PSTA cluster (§13) mostly lacks recorded resolutions; cluster counts overlap because cases match multiple symptom keywords.*
