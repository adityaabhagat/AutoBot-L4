# SKILL: QRA Acquisitions & Dispositions / Payouts / Escheat Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** My Quorum Revenue Accounting (QRA — upstream oil-&-gas owner/revenue accounting, part of the myQuorum / On Demand suite)
**Scope:** Three adjacent QRA back-office areas that move owner money and ownership:
- **Acquisitions & Dispositions (A&D)** — loading/converting acquired or divested property, well, BA (business associate / owner) and DOI (Division-of-Interest) data through the A&D module / staging tables into live tables (QP043 import path, `ASTG_ORG_V2` staging, BA usage types, ownership/decimal-interest updates).
- **Payouts** — the Payout module (QP043 process steps + QP085/PO0xx reports): JIB-to-revenue rollup, payout balance calc, payout statements (POR005/PO005/PO010), pricing.
- **Escheat / Unclaimed Property** — the escheat process family (CWMNLESCHT / CWUCESCHT / Escheat Manual-Selection & Current-State), EC006/EC010 screens, NAUPA/state reporting, dormancy & cutoff-date logic.

**Companion skills (other QRA category groups):** Revenue distribution / valuation / RD-MEG-SOD mechanics, check-write / ACH / NACHA / 1099, suspense & owner relations, and JIB live in their own SKILL_QRA_* files. This guide *consumes* live ownership + revenue-distribution + suspense balances and *produces* loaded ownership, payout balances/statements, and escheat bookings — when the underlying revenue/decimal is wrong, fix that upstream first (this module is usually the messenger).

> **Evidence base:** 409 closed QRA cases in categories Acquisitions and Dispositions (290), Payouts (99), Escheat (20). Root-cause split: (blank) 53, Customer Error 48, Training 47, **Software Defect 47**, Customer Cancelled 44, Business Change 36, Platform 27, Hardware/Software Change 26, **Application Configuration 11**, **ChangeConfig 1**, others. This skill mines the **59 actionable** cases (Software Defect 47 + Application Configuration 11 + ChangeConfig 1) for fix recipes, plus ~60 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining. Where a cluster had no clear documented fix, it is marked "resolution pattern unclear from mined cases."

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — A&D load: BA / owner-usage-type & decimal-interest errors](#4-cluster-a--ad-load-ba--owner-usage-type--decimal-interest-errors)
5. [Cluster B — A&D staging stuck / bulk ownership & property fixes (scripts)](#5-cluster-b--ad-staging-stuck--bulk-ownership--property-fixes)
6. [Cluster C — Payout process failures (NULL columns, archived data, PK)](#6-cluster-c--payout-process-failures)
7. [Cluster D — Payout reports & values (POR005/PO010 format, perf, discrepancy)](#7-cluster-d--payout-reports--values)
8. [Cluster E — Escheat process defects (doubling, parameters, dates)](#8-cluster-e--escheat-process-defects)
9. [Cluster F — Revenue-distribution / SOD / PPN / prior-period reversal feeding A&D](#9-cluster-f--revenue-distribution--sod--ppn--prior-period-reversal)
10. [Cluster G — Production / severance / ad-valorem tax on distribution](#10-cluster-g--production--severance--ad-valorem-tax)
11. [Cluster H — Batch out-of-memory / timeout / large-dataset (ONRR, BKRVNU)](#11-cluster-h--batch-out-of-memory--timeout--large-dataset)
12. [Cluster I — Check-write / ACH / NACHA / owner-funds-release feeding payout](#12-cluster-i--check-write--ach--nacha--owner-funds-release)
13. [Known ADO Items](#13-known-ado-items)
14. [Diagnostic SQL](#14-diagnostic-sql)
15. [Expected-Behavior / User-Education FAQ](#15-expected-behavior--user-education-faq)
16. [Key Code, Processes & Repos](#16-key-code-processes--repos)
17. [Escalation Guidance](#17-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| Pushing acquired decks to live and `For JIB DOIs, the only valid owner BA usage type is 'BI'…the owner is not valid because it does not have this usage type` | BA on a JIB DOI lacks the **BI (Billing Interest) usage type** | §4 — add BI usage type to that BA; verify staging vs live BA setup (26-01070023) |
| "BA Error Message Won't Clear in Acquisition Module" | Stale/duplicate BA reference in staging; or BA setup detail | §4 — re-check BA usage/setup; may need a staging cleanup script |
| Acquired BA **comments showing on the wrong BA** after A&D convert | `NOTE_GROUP_ID` reused — note group already exists on another BA | §4 — de-dupe `SXREF_BA_ENTITY_XREF_NOTES.NOTE_GROUP_ID` (25-01051005) |
| Properties **stuck** in `*ASTG_ORG_V2`; can't import or fully delete | Orphaned staging rows after you deleted prop/well from live | §5 — script to delete the stuck rows from `ASTG_ORG_V2` (26-01082244) |
| "Need a script ASAP — wrong BA# / bulk-update ownership on props & wells" | Bad BA# on import templates (e.g. 400000_1→300000_1) | §5 — scripted ownership/BA update in PRD from corrected templates (25-01059532, 23-00923958) |
| PAYOUT process: `Cannot insert the value NULL into column 'RYLTY_RATE'` | Payout deck has JIB-only data / no royalty-interest owner → null royalty rate hits a NOT-NULL insert | §6 — defect, fixed via WI **#1720425** (25-01010666) |
| Payout process errors "no data to pull" / POMERGEJIB fails | Detail records needed by payout were **archived/purged** (pre-cutoff prod periods) | §6 — sysgen view override to read from `ARCV_*` archive tables (24-00992249 / #1702254) |
| Payout balances **change month-to-month** unexpectedly | Archive-join **view** returning partial data | §6/§7 — corrected the archive-join view, WI **#1713439** (24-00994733) |
| `POR005` / Payout Stmt by Owner **runs for hours** or **format changed** | Report SQL perf / report-version drift | §7 — POR005 perf & format fixes (22-00868477/#1573809, 22-00571490/#1548204) |
| Tax value on **PO010 ~2-3x too high** for ~5% of records | Duplicate insert into PO010 staging | §7 — code added a condition in the insert query to stop dups (24-00953186) |
| Escheat: **duplicate records in EC006** after running Final mode | Bug in `CWUCESCHT` final mode (also user-error twin: CU then MA without posting) | §8 — defect (26-01090132); verify processing order first (see §15) |
| Escheat **Current-State** pulling **wrong cutoff dates** for previously-escheated owners | Current-State process doesn't take a cutoff-date parameter; uses last escheat year | §8 — date-correction script (25-01045406, 25-01042481) |
| 2024.04 upgrade: Escheat **process parameter (Country Code) ignored** | Parameter introduced by WI 1321337 not wired into the batch | §8 — fixed WI **#1695760** (24-00986934) |
| Production/severance tax **calculating on State-Royalty (SR) owners** that should be exempt | RD not exempting SOD/SR owners; patch-introduced regression | §10 — patched 01/2023 (22-00827442, 22-00512935) |
| `LD45` ad-valorem net change ≠ 0 / `LD65` PPNs reversing & rebooking to **current** instead of historical NRI | Prior-period-adjustment reversal using current rather than original NRI/MEG | §9 — data-script / reversal logic (22-00680662, 22-00704955) |
| Batch fails **Out of Memory** on a large state/subledger (ONRR `TRRYLMMSER`, `BKRVNU`) | Recordset too large for the batch step's cursor | §11 — code change to stream/batch (22-00830416 = code change; BKRVNU 22-00660027) |
| ACH stub emails not sending (`CWACHEMAIL`/QP043) | Regression from an OOC hotfix | §12 — software update (22-00831194) |
| NACHA files sent to bank for the **wrong month** | Old file left on SFTP, re-sent | §12 — Control-M step to purge SFTP after transfer (25-01016336) |

---

## 2. Pipeline & Concepts

```
A&D LOAD                                          PAYOUTS                                 ESCHEAT
templates → QP043 import → ASTG_ORG_V2            JIB cost + Revenue subledger            Suspense / unpaid owner balances
 (BA / owner / prop / well / DOI staging)          │                                       │
        │ validate (BA usage type, eff dates)       ▼ POMERGEJIB → POEXTRPEXP → POGNRTRPT    ▼ Escheat Manual-Selection (MA / CWMNLESCHT)
        ▼ post to LIVE                              [Payout detail/balance]                  then Escheat Current-State (CU / CWUCESCHT)
[DONL_DO_DETAIL/HDR live DOI,                       │                                        │ uses dormancy (EC010) + cutoff date
 SXREF_BA_* owner master]                           ▼ QP085 reports (POR005/PO005/PO010)      ▼ DONL_ESCHT_OWNR_DETAIL (EC006), NAUPA/state files
```

### Key terms (Quorum / QRA vocabulary)
- **BA** = Business Associate (the owner/vendor entity). Owners carry **usage types** per DOI type — e.g. **BI = Billing Interest** (required for JIB DOIs), revenue-owner usages for REV DOIs. "Owner not valid because it does not have this usage type" = the BA is missing the usage the DOI type requires (26-01070023).
- **DOI** = Division of Interest; **DO_TYPE_CD** REV (revenue) vs JIB (billing). Held in `DONL_DO_DETAIL` / `DONL_DO_HDR`. **Decimal interest** (NRI/WI) per owner per property/tier.
- **A&D module / QP043** = the import/convert pipeline for acquired or divested assets. Templates (prop/well/BA/DOI) load into **staging** (`*ASTG_ORG_V2`, prefixed per client/business-segment, e.g. `AK_ASTG_ORG_V2`) then **post** to live. Errors here are usually validation (BA usage, eff-date) or orphaned staging rows.
- **MEG** = Marketing/Entitlement Group (group of owners marketed together). Reversal/rebook must preserve the **same MEG structure**; SOD = Suspense-On-Demand / special-owner-distribution handling.
- **PPN** = Prior-Period Notification / prior-period-adjustment booking (the reverse-and-rebook pair that corrects a closed period). `LD45` (ad-valorem), `LD65` (PPN) are revenue-distribution batch/booking codes. A correct PPA must reverse off the **original (historical) NRI** and rebook to **current** — reversing off *current* is the recurring defect (22-00704955).
- **Payout** = recoupment account: operator recovers costs (JIB) before the non-op/royalty owner is paid out. Payout process: **POMERGEJIB** (merge monthly JIB expense) → **POEXTRPEXP** (extract property expense detail) → **POGNRTRPT** (generate payout report detail), then reports in **QP085** (POR005 = Payout/Payment Stmt by Owner No, PO005, PO010). **Sales/payout price = Σ(txn amount) ÷ Σ(txn quantity)** from the JE101 subledger for a property/major-product/acct-date (this is *by design* — §15).
- **UMI** = (payout) interest flag on the payout setup; mismatch vs template is a config item (25-01039811).
- **Escheat** = unclaimed-property to the state. Two passes: **Manual-Selection (MA)** and **Current-State (CU)** = `CWMNLESCHT` / `CWUCESCHT`. **Dormancy** per state in **EC010**; **Escheat Cutoff Date** drives which production months are pulled. Owner detail lands in **EC006** (`DONL_ESCHT_OWNR_DETAIL`); **NAUPA** = the state-reporting file format. The **Negative Reporting Flag (EC010)** controls whether negative balances are reported/netted (state-specific).
- **ARCV_* tables** = archive copies (e.g. `ARCV_JBTRN_COST_SUBLEDGER_HIST`). When a client archives/purges old prod periods, payout/escheat that reach back further must read these via a **sysgen view override** (24-00992249).
- **QP043 / QP085** = batch-process / report launcher screens; **QPEC** = the batch process engine (errors surface as `[COM Error] QADOCommand.cpp / QADORecordset.cpp`).
- **RD** = Revenue Distribution run; **RRID** = Revenue Run ID; **Run ID** = process run identifier on the booking.

---

## 3. Decision Tree

```
QRA A&D / Payout / Escheat case
│
├─ A&D LOAD / convert (templates, QP043, staging → live)?
│   ├─ "owner not valid…must have usage type 'BI'"                         → §4 (add BI usage to the BA; JIB DOI rule)
│   ├─ BA error won't clear / BA comments on wrong BA / zip not loading     → §4 (BA setup; NOTE_GROUP_ID dup; BA-info script)
│   ├─ Properties stuck in *ASTG_ORG_V2 / can't import or delete            → §5 (script to clear orphaned staging rows)
│   └─ "wrong BA# on template / bulk update ownership on props & wells"     → §5 (scripted ownership/BA update from corrected templates)
│
├─ PAYOUTS?
│   ├─ Process ERRORS (NULL RYLTY_RATE / no data / PK / archived data)      → §6
│   │     • NULL RYLTY_RATE (JIB-only deck)            → defect #1720425
│   │     • "no data"/POMERGEJIB fail (records archived)→ sysgen archive-view override (#1702254/#1713439)
│   ├─ Reports/values (POR005/PO005/PO010 format, slow, balance discrepancy)→ §7
│   └─ "exports not working" / "report blank"                              → usually §15 (must run POMERGEJIB→POEXTRPEXP→POGNRTRPT first)
│
├─ ESCHEAT?
│   ├─ Duplicate EC006 / amounts doubling after Final                      → §8 defect (CWUCESCHT) — but first rule out CU-then-MA-without-posting (§15)
│   ├─ Current-State pulling wrong cutoff dates                            → §8 (date script; Current-State has no cutoff param)
│   ├─ Upgrade: escheat parameter (Country Code) ignored                   → §8 fixed #1695760
│   └─ "how do I set up / NAUPA / negative-reporting flag"                 → §15 (training/expected)
│
├─ Numbers wrong because of REVENUE feeding the above?
│   ├─ SR/SOD owners getting tax they should be exempt from                → §10 (patched 01/2023)
│   ├─ LD45 ad-valorem net≠0 / LD65 PPN reversing to current NRI           → §9 (PPA reversal logic / data script)
│   └─ MEG/SOD/PPN reversal not preserving MEG owners                       → §9
│
├─ Batch CRASH (not wrong output)?
│   ├─ Out of Memory / timeout on big dataset (ONRR TRRYLMMSER, BKRVNU)    → §11
│   └─ Owner Funds Release / CW proc param missing                         → §12 (proc-signature defect)
│
└─ Vague "error", "how do I…", audit, "report not pulling data"           → §15 Expected-Behavior FAQ
```

---

## 4. Cluster A — A&D load: BA / owner-usage-type & decimal-interest errors

**The dominant A&D-load failure mode.** When pushing acquired DOI decks from staging to live, the load validates each owner's **BA usage type against the DOI type**. The recurring blocker:

**Symptom (verbatim, 26-01070023):**
```
[DONL_DO_DETAIL:…DO_TYPE_CD='JIB';…BA_NO='700000';BA_SUB='3';INT_TYPE_CD='WI'…]:
For JIB DOIs, the only valid owner BA usage type is 'BI' (Billing Interest Owner).
The owner is not valid because it does not have this usage type.
```
Even when "the BA is set up correctly in staging and live," the BA is missing the **BI usage type** that a JIB DOI requires.

**Root causes & fixes seen:**
- **Missing BI usage on the BA for a JIB DOI** (26-01070023) → add the **BI (Billing Interest) usage type** to that BA, then re-post the deck. (Mirror for REV DOIs: the BA needs the revenue-owner usage.)
- **BA comments landing on the wrong BA after convert** (25-01051005): A&D convert assigned a **`NOTE_GROUP_ID` that already exists** on another BA, so `SXREF_BA_ENTITY_XREF_NOTES` shows one note-group shared across multiple `BA_NO`s. Detection query is in §14; fix is to de-dupe/re-key the note group before loading more commented BAs. (Software Defect, 25-01051005 — resolution text not captured; treat the dup-NOTE_GROUP_ID detection as the actionable step.)
- **BA reference detail wrong / "BA error won't clear"** (26-01070023 family, 23-00923958): zip+4 not populating, BA attributes off → **script to update BA information from corrected templates** (23-00923958).

**Fix recipe:**
1. Read the exact validation line — it names `DONL_DO_DETAIL` key columns (`DO_TYPE_CD`, `BA_NO`, `BA_SUB`, `INT_TYPE_CD`, eff dates). The DO_TYPE_CD tells you the required usage.
2. For **JIB** DOIs → BA needs **BI** usage. For **REV** → revenue usage. Add the missing usage to the BA and re-post.
3. For "comments on wrong BA," run the `NOTE_GROUP_ID` dup query (§14-B) before loading more BAs.
4. Bad BA attributes across many owners → request a **scripted BA-info update** from the corrected import templates (don't hand-edit each BA).

---

## 5. Cluster B — A&D staging stuck / bulk ownership & property fixes

A steady stream of **Application Configuration** cases resolved by **a targeted script** against staging or ownership tables — the A&D import path frequently leaves orphaned/partly-loaded rows that the UI can neither import nor delete.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Properties **stuck in `*ASTG_ORG_V2`**; error on import, can't fully delete | User deleted prop/well from live (decks were tied to wells in the template) → staging rows orphaned | **Script to delete those properties from `ASTG_ORG_V2`** | 26-01082244 |
| "Need script ASAP — bulk update ownership on props & wells," wrong BA# on templates (`400000_1`→`300000_1`) | Bad BA# carried by import templates | **Script run in PRD to update ownership on properties/wells** from corrected templates (e.g. `MAC_ALL_QRA_UPDATE_NONOP_PROP_CNTY_*`) | 25-01059532 |
| Tetris Acq BA problems — zip+4 not populating for owners | BA attributes wrong post-load | **Script to update BA information provided in templates** | 23-00923958 |
| "A&D Upload" generic load failure | Load/staging defect | resolution pattern unclear from mined cases (null Resolution) | 24-00938096 |

**Fix recipe:** for "stuck in staging / can't import or delete," the staging table is **`<segment>ASTG_ORG_V2`** (the prefix is the operating business-segment / client, e.g. `AK_`, `MAC_`). The repeatable unblock is a **scoped DELETE of the orphaned staging rows** for the affected prop/well numbers, then re-create the package and re-import. For bad BA/ownership across many props, drive the correction **from the corrected import template via a script** rather than the UI. Always verify-SELECT the staging rows first and wrap the DELETE in a transaction. These are dispositioned operationally (script) — no product code fix.

---

## 6. Cluster C — Payout process failures

The Payout process (`POMERGEJIB` → `POEXTRPEXP` → `POGNRTRPT`) crashing during a step. Two confirmed defect signatures + the archive-data pattern:

| Signature | Root cause | Fix | Case / ADO |
|---|---|---|---|
| `Cannot insert the value NULL into column 'RYLTY_RATE', table '…RONL_PO_DETAIL_RVNU'` from `CCI_SP_PAYOUT_STAGING / Insert_RONL_PO_DETAIL_RVNU` | A payout deck had **JIB-only data and no royalty-interest owner**, so royalty rate was null going into a NOT-NULL column. Allowing nulls in UAT "worked" but not the real fix | **Software Defect — WI #1720425** (CCI/TGNR, Closed) | 25-01010666 |
| Payout process **errors with no data to pull / `POMERGEJIB` fails** | Detail the payout needs (back to 2013-2014) was **archived & purged** (client archives pre-2019); process can't read pre-cutoff periods from live | **Sysgen override to the view** so the Payout process reads from `ARCV_JBTRN_COST_SUBLEDGER_HIST` as needed; delivered via OOC patch (restoring 30M rows was infeasible) | 24-00992249 / #1702254 |
| After the archive-view fix, **payout balances differ month-to-month** (e.g. 21.6M vs 13.7M for same Payout ID) | The **archive-join view** was returning partial data | **View corrected — WI #1713439**, packaged on patch 10 | 24-00994733 / #1713439 |
| **PK error during payout process** | Duplicate key in payout staging | **WI #1600613** (TGNR/CCI, Closed) | (TGNR) |
| `PAYOUT error … RYLTY_RATE` recurrence on CNR | Payout export/config | "solved during the latest Hotfix for CNR" | 25-01040409 |

**Fix recipe:**
1. Capture the exact `[COM Error]` + the staging proc name (`*_SP_PAYOUT_STAGING`, `Insert_RONL_PO_DETAIL_RVNU`) + the column.
2. **NULL RYLTY_RATE** → check whether the failing deck is **JIB-only / has no royalty-interest owner** (25-01010666). Confirm the build includes #1720425. Do **not** "fix" it by allowing nulls on the grid — that masks it and won't hold in PRD.
3. **"No data" / POMERGEJIB fail** → check whether the needed prod periods were **archived/purged** (24-00992249). The fix is a **sysgen archive-join view override** (a DB/config change), delivered via OOC patch — not a live-table restore. After applying, re-validate **payout balances** (the archive-join view itself had a follow-on bug, #1713439).
4. Scope re-runs to one **Payout ID** at a time when volume/perf is a factor (see §15, Permian/MEW pattern).

---

## 7. Cluster D — Payout reports & values

Mostly **report** issues on the QP085 / PO0xx reports — format drift, performance, or a value discrepancy traced to the data the report pulls.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| `POR005` Payout/Payment Stmt by Owner **runs 3+ hours** | Report SQL not narrowed; slow query | Report SQL sped up — **#1573809** (Upstream 2022.04 Hotfix Jan-2023, APH); later perf **#1609740** | 22-00868477 |
| `POR005` **report format changed** unexpectedly | Report-version / template drift across environments | Format corrected — **#1548204** (TGNR, Closed); cleanup/standardize which POR005 to use **#1391240** | 22-00571490 |
| `POR005` **payment-by-owner discrepancy** (balances don't tie) | A **view that joins archived data** returned wrong data — report was working, the *data feeding it* was off | **View corrected — #1713439**, patch 10 | 24-00994733 |
| **PO010 Tax Value ~2-3x too high** for ~5% of records | **Duplicate inserts** into the PO010 staging | **Code change** — added a condition in the insert query so PO010 has no duplicates | 24-00953186 |
| `RPT_PO005 - Payout Stmt By Owner No` **fails to launch** after 2024.04 upgrade | Report-launch regression on upgrade | **#1680349** (MEW, Closed) | (MEW upgrade) |
| Payout module **pricing calculation** questioned | (see §15 — by design) | Sales price = Σ(amt)/Σ(qty) from JE101 subledger | 25-01030213 / #1752719 |
| Older POR005 calc/perf items | Pre-cloud feature requests | **#1369887, #1372250** (PNR, Discarded — superseded) | — |

**Fix recipe:** first decide **report vs data**. If the *format* changed or it's slow → report version/SQL (POR005: #1573809 perf, #1548204 format; confirm the environment is on the standardized report per #1391240). If *values* are wrong → trace what the report pulls: a **PO010 2-3x** value is a duplicate-insert defect (24-00953186), and a **POR005 owner discrepancy** is the archive-join **view** bug (#1713439). For "report blank / not pulling data," it's almost always the **missing prerequisite steps** — see §15.

---

## 8. Cluster E — Escheat process defects

Small but high-criticality cluster (state deadlines). Distinguish **true defect** from the very common **user-error twin** (wrong MA/CU order — §15).

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **Duplicate records in EC006** (`DONL_ESCHT_OWNR_DETAIL`) after running `CWUCESCHT` in **Final mode** | **Bug in CWUCESCHT in final mode** — duplication occurs after reg-SQL `m_CW_INS_ESCHT_OWNR_DETAILS` (JSTG_JE_INPUT was clean, so dup is in the detail insert) | Confirmed defect; new WI opened to check latest version. Related historical defect **#1321337** "Escheat amounts doubling upon run of Final Process" | 26-01090132 |
| **Current-State** escheat using the **wrong cutoff dates** for previously-escheated owners | **Escheat – Current State has no Escheat-Cutoff-Date parameter**; for owners escheated in prior years it reuses the last-escheat-year cutoff instead of the current run's calculated date | **Script to update the dates on the escheat** | 25-01045406, 25-01042481 |
| 2024.04 upgrade — **escheat "Country Code Process" parameter not actually used** in the batch | Parameter (introduced by WI 1321337) wasn't wired into the batch process | **Fixed — WI #1695760** | 24-00986934 |
| `CWMNLESCHT` error (PROC_FL) needing script approval | Process-flag data | **Script — WI #1647080** (CCI/TGNR) | (CCI) |
| Current escheat blocked by previous run with "Prevent Posting" checked | Prior run state | **#1693827** (CEN) | — |
| NAUPA reports not created for "Unknown" state | State mapping | **#1715033** (GEC) | 25-01005520 |
| Check-Write for Delaware escheat **Out of Memory** | Large dataset (see §11) | **#1718501** (PNR) | — |

**Fix recipe:**
1. **Before** treating an escheat-doubling case as a defect, confirm the user ran **Manual-Selection (MA) and Current-State (CU) with a POST in between** — running CU then MA (or either without posting) lets the same SL records land in both passes and *duplicate* (this is the #1 user-error twin, 26-01098217, §15).
2. If the order was correct and EC006 still duplicates after **Final** `CWUCESCHT`, it's the defect (26-01090132 / lineage of #1321337) — capture the **Process Queue ID**, the EC006 detail dup query, and the SQL-trace (`QARCH_QFCBATCH_SQL_TRACE`) around `m_CW_INS_ESCHT_OWNR_DETAILS`; escalate.
3. **Current-State wrong cutoff** is a known limitation — Current-State doesn't accept a cutoff date; for previously-escheated owners the dates come from their last escheat year. The operational fix is a **date-update script** (25-01045406); for a one-off, run **Manual-Selection with the specific cutoff date** instead (25-01045717, §15).
4. Upgrade-broke-a-parameter → check the WI that introduced it (e.g. Country Code, #1695760).

---

## 9. Cluster F — Revenue-distribution / SOD / PPN / prior-period reversal

Cases categorized A&D/Payout whose *real* cause is in the **revenue-distribution / prior-period-adjustment** machinery feeding ownership changes. The recurring defect family is **reversals using current instead of original NRI/MEG**.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| DOI recoup transfers generated **PPNs that reversed off *current* NRI and rebooked to current**, and **dropped the original MEG owner** from the reversal | Transfer/PPA reversal logic used current ownership instead of historical; MEG structure not preserved | Immediate: reverse the bad PPNs & rebook on correct historical NRI; RCA on reverse-off-current behavior | 22-00704955 |
| `LD45` ad-valorem PPA **net change ≠ 0** (prepaid ad-valorem account off by the reversal amount) | Reverse/rebook of previously-processed prepaid ad-valorem created a residual | **Data issue stemming from a prior (2019) script** — corrected via data fix | 22-00680662 |
| Batch-type **33 reversal left 2 records on RSF** (reversal source file) not cleared, causing double reversal | Reversal-source not fully cleared on the original correction | **Resolution delivered with latest upgrade** | 22-00577293 |
| `LD65 PPN` reversing & rebooking on current | Same PPA-on-current family as 22-00704955 | resolution pattern unclear from mined cases (null Resolution) | 22-00704955, 22-00825935 |
| Impairment Reason Code 302 ("calculating remaining amount is not zero") on a new flow grid | **Override GMI Decimal field on MG006 populated** — SOD distribution is handled differently when that field is set | **Script to remove the Override GMI Decimal on MG006** | 22-00565013 |
| Revenue PPN issue (SOD) | SOD config | resolution pattern unclear from mined cases (null Resolution) | 23-00934917 |
| CA Allocation Failed / can't close CA after MG/ownership shift | Allocation/master-link control view stale after SP025 change | Data script (see CA020 below) | 22-00661303 |
| Error closing CA — `Failed to insert new records into PTRN_CA_VOL … parent control` | Parent-control blocks the CA close | **Data script to resolve CA020 error** | 22-00661378 |

**Fix recipe:** when an A&D/payout number is wrong because of a **transfer / recoup / PPA**, verify the reversal used the **original historical NRI and preserved the MEG owners** (22-00704955). For ad-valorem/LD45 net-≠-0, reconcile the prepaid vs payable accounts for the Run ID — often a residual from an **older script** (22-00680662). For impairment-302 with SOD, check the **Override GMI Decimal on MG006** (22-00565013). For CA-close errors (`PTRN_CA_VOL` parent control), a **CA020 data script** clears it (22-00661378). Most of these are **revenue-distribution** mechanics — see the companion RD/valuation skill, and fix the distribution before re-running payout/escheat.

---

## 10. Cluster G — Production / severance / ad-valorem tax

A focused **Software Defect** cluster: production/severance taxes calculating on owners that should be exempt (introduced by a patch).

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **Production taxes calculating on State-Royalty (SR) interest types** that should be exempt — only on DRIs on product 200; started after patches 31 & 32 | Patch regression in tax calc for SR owners | resolution pattern unclear from mined cases (null Resolution); cluster-twin 22-00827442 was **patched 01/2023** | 22-00512935 |
| **RD not exempting SOD owners on MEGs** — non-working-interest SOD owners got adjustment amounts even though the adjustment was on a MEG | RD exemption logic missed SOD-on-MEG | **Patched 01/2023** | 22-00827442 |
| Ad-valorem LD45 net change ≠ 0 | see §9 | data script | 22-00680662 |

**Fix recipe:** "taxes calculating on owners that shouldn't have them" is the signature. Capture the **interest type (SR / SOD / non-WI), product code, RRID/property/BA**, and whether it started **after a patch** (22-00512935 named patches 31 & 32). Compare a patched env (TQA) vs an unpatched env (DEV) to confirm regression. The SOD-on-MEG exemption was **patched 01/2023** (22-00827442) — confirm the client's build is at/after that.

---

## 11. Cluster H — Batch out-of-memory / timeout / large-dataset

Batch steps that **crash on volume** rather than producing wrong output — recurring on ONRR/MMS royalty reporting and revenue valuation.

| Step / signature | Root cause | Fix | Case |
|---|---|---|---|
| **ONRR Reporting `TRRYLMMSER`** (`QPSROYALTYREPORTINGERRORCHECKMMS`) — `Out of memory` / "Can't insert row in recordset" filtered on a large state (Utah ~1M rows vs Wyoming ~31k) | Step loads the whole recordset into memory; can't be split by state (Final runs once/month) | **Code change** to handle the full dataset in one batch | 22-00830416 |
| `BKRVNU` (VL100) **timing out** on large revenue batches; stuck in `RDCALC` with "Unable to execute the query to build the tax-free allowable deduct add-back information for Valuation" | Process didn't scale; ~2h before it even times out | Workaround = break into ~250-line batches (Stephen Emerson script); root perf not fully resolved in mined text | 22-00660027 |
| Check-Write for **Delaware escheat Out of Memory** | Large escheat dataset | **#1718501** (PNR) | — |
| `ONRR Value Difference` (BP GOM) | Reporting value diff | resolution pattern unclear from mined cases (null Resolution) | 22-00657255 |

**Fix recipe:** for OOM, the durable fix is a **code change to stream/batch the recordset** (22-00830416, code change). As an immediate unblock, **narrow the run** (by state / smaller line counts), but note where the client *can't* split (ONRR Final runs once/month) — that's why it needed the code fix. Capture the **Process Step ID + Process Queue ID** (e.g. `TRRYLMMSER` / PQID 7659029) and the `QADORecordset.cpp Out of memory` signature.

---

## 12. Cluster I — Check-write / ACH / NACHA / owner-funds-release

Money-out plumbing that gates A&D/payout cutovers. Mostly defects/config in the check-write (CW) family.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **ACH stub emails not sending** (`CWACHEMAIL`, QP043 "CW Bank ACH Email Stubs") | **Regression introduced in an October OOC hotfix** | **Software update** | 22-00831194 |
| **NACHA files sent to the bank for the wrong month** (March files instead of April) | Old NACHA file left on the SFTP server, re-sent | **Add a Control-M step to remove files from SFTP after successful transfer** | 25-01016336 |
| **Owner Funds Release (`CWOWFNDRLS`)** — `Procedure USPR_CW_OWNR_FUND_RLS_SPLIT expects parameter '@REJ_FL', which was not supplied` | Stored-proc **signature mismatch** (app calling without the `@REJ_FL` param) — proc in `Quorum.Upstream.QRA.Database` | resolution pattern unclear from mined cases (null Resolution); proc identified — escalate as version/param mismatch | 22-00612413 |
| **Checkwrite "already processed for the month"** | Stale CW process state | **Script deployed to BRM; CW completed/posted** | 22-00713800 |

**Fix recipe:** ACH-email not sending = a **CW hotfix regression** → software update (22-00831194). NACHA wrong-month = **stale file on SFTP** → operational fix is purging the SFTP after a successful bank transfer (25-01016336), not a code change. `CWOWFNDRLS` param error = a **proc-signature / version mismatch** on `USPR_CW_OWNR_FUND_RLS_SPLIT` (`@REJ_FL` not supplied) — confirm app build vs DB proc version. "Already processed this month" → a **state-reset script** in BRM unblocks the re-run (22-00713800).

---

## 13. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1720425** | Bug / **Closed** | CCI/TGNR — PAYOUT `Cannot insert NULL into RYLTY_RATE` | §6 | 25-01010666 |
| **#1702254** | Bug / **Closed** | TGNR(CCI) — POMERGEJIB failing due to older payout records archived | §6 | 24-00992249 (orig 24-00980736) |
| **#1713439** | Bug / **Closed** | TGNR(CCI) — RPT_POR005 Payment Stmt by Owner discrepancy (archive-join view) | §6/§7 | 24-00994733 |
| **#1600613** | Bug / **Closed** | TGNR(CCI) — PK error during payout process | §6 | — |
| **#1680349** | Bug / **Closed** | MEW 2024.04 — RPT_PO005 Payout Stmt by Owner fails to launch | §7 | — |
| **#1573809** | Requirement / **Closed** | Upstream 2022.04 Hotfix Jan-2023 (APH) — POR005 SQL speed-up | §7 | 22-00868477 |
| **#1548204** | Bug / **Closed** | TGNR — 22-00289258 POR005 report format has changed | §7 | 22-00571490 |
| **#1609740** | Bug / **Closed** | TGNR(CCI) — POR005 performance issue | §7 | — |
| **#1391240** | Requirement / **Proposed** | Confirm which POR005 to use & clean up client envs | §7 | — |
| **#1752719** | Bug / **Closed** | DAY — Payout Module pricing calculation | §7/§15 | 25-01030213 |
| **#1765730** | Bug / **Closed** | MEWU 2024.04 — Payout performance improvement investigation | §7 | 25-01050043 |
| **#1369887 / #1372250** | Feature / **Discarded** | PNR — POR005 perf & calc (superseded, pre-cloud) | §7 | — |
| **#1695760** | Bug / **Closed** | MEW 2024.04 — Escheat "Country Code Process" parameter not used in batch | §8 | 24-00986934 |
| **#1321337** | Bug / **Closed** | Escheat amounts doubling upon run of Final Process | §8 | (lineage of 26-01090132) |
| **#1647080** | Bug / **Closed** | CCI/TGNR — Escheat CWMNLESCHT error (PROC_FL) script approval | §8 | — |
| **#1693827** | Bug / **Closed** | CEN — Escheat "Current" blocked by prior run with Prevent-Posting | §8 | — |
| **#1700164** | Bug / **Closed** | PRM — 24-00990180 Error running Escheat process | §8 | 24-00990180 |
| **#1702062** | Bug / **Closed** | APH — Escheatable By Susp Rsn report CWR024 not working | §8 | 24-00992646 |
| **#1715033** | Bug / **Closed** | GEC — Escheat NAUPA reports not created for "Unknown" state | §8 | 25-01005520 |
| **#1718501** | Bug / **Closed** | PNR — Check Write (CW_MAIN) for Delaware escheat OOM | §8/§11 | — |
| **#1709194** | Bug / **Closed** | MIT/CORE — Make BA escheat info available in WEB | §8 | — |

> Several actionable cases were dispositioned **operationally** (data/config script, sysgen view override, Control-M step) with no standalone product WI captured: A&D staging clear (26-01082244), bulk ownership/BA updates (25-01059532, 23-00923958), escheat date scripts (25-01045406/25-01042481), archive-view override (24-00992249, delivered OOC patch), NACHA SFTP purge step (25-01016336), CW BRM reset (22-00713800), SOD/tax patches (22-00827442 patched 01/2023). Confirm exact build/patch in the Upstream release notes before stating fix availability.

---

## 14. Diagnostic SQL

> **Caveat:** QRA runs on **SQL Server** (T-SQL), one DB per client/env with names like `<DBPREFIX>_PRDA1UPS_QRA`, `..._ESUITE`, `..._ESUITE_QFC` (archive/note schemas). Table/column names below are from case repro text + code search — **verify against the client DB** and always run a verify-SELECT before any DELETE/UPDATE, wrapped in a transaction.

```sql
-- A. A&D staging rows stuck for given props (the ASTG_ORG_V2 orphan pattern, §5)
--    Prefix is the operating segment/client (e.g. AK_, MAC_). Find the right table first:
SELECT name FROM sys.tables WHERE name LIKE '%ASTG_ORG_V2';
SELECT * FROM <seg>ASTG_ORG_V2 WHERE PROP_NO IN ('<prop>','<prop>');   -- verify before delete

-- B. BA comments landing on the wrong BA — duplicate NOTE_GROUP_ID across BAs (§4, 25-01051005)
SELECT NOTE_GROUP_ID, COUNT(DISTINCT BA_NO) AS ba_ct
FROM   <db>.[..._ESUITE].dbo.SXREF_BA_ENTITY_XREF_NOTES
GROUP BY NOTE_GROUP_ID HAVING COUNT(DISTINCT BA_NO) > 1 ORDER BY 1;
SELECT * FROM <db>.[..._ESUITE_QFC].dbo.QARCH_NOTE_GROUP WHERE NOTE_GROUP_ID = <id>;

-- C. JIB DOI owner missing BI usage type (§4, 26-01070023) — inspect the failing DOI line
SELECT OPER_BUS_SEG_CD, PROP_NO, DO_TYPE_CD, BA_NO, BA_SUB, INT_TYPE_CD, EFF_DT_FROM
FROM   DONL_DO_DETAIL
WHERE  DO_TYPE_CD = 'JIB' AND PROP_NO = '<prop>' AND BA_NO = '<ba>';
-- then verify the BA carries a 'BI' usage type in the BA usage/master tables before re-posting.

-- D. Payout NULL RYLTY_RATE — find decks with no royalty-interest owner (§6, 25-01010666)
SELECT PAYOUT_ID, PROP_NO, COUNT(*) AS det
FROM   RONL_PO_DETAIL_RVNU      -- target of Insert_RONL_PO_DETAIL_RVNU
WHERE  RYLTY_RATE IS NULL GROUP BY PAYOUT_ID, PROP_NO;

-- E. Payout needs archived periods (§6, 24-00992249) — does live data exist back far enough?
SELECT MIN(PROC_PRD), MAX(PROC_PRD) FROM JBTRN_COST_SUBLEDGER_HISTORY WHERE PROP_NO = '<prop>';
SELECT MIN(PROC_PRD), MAX(PROC_PRD) FROM ARCV_JBTRN_COST_SUBLEDGER_HIST WHERE PROP_NO = '<prop>';
-- if the payout reaches before live MIN(PROC_PRD), the archive-join view override is needed.

-- F. Escheat EC006 duplicate detail (§8, 26-01090132)
SELECT BA_NO, PRDN_DT, PROP_NO, COUNT(*) AS dup
FROM   DONL_ESCHT_OWNR_DETAIL
WHERE  BA_NO = '<ba>' AND PROP_NO = '<prop>'
GROUP BY BA_NO, PRDN_DT, PROP_NO HAVING COUNT(*) > 1;
-- trace the run: which reg-SQL duplicated?
SELECT REGISTERED_SQL_NAME, SQL_STATEMENT_PART1, SQL_SUCCESS_IND
FROM   QARCH_QFCBATCH_SQL_TRACE WHERE PROCESS_QUEUE_ID = <pqid> ORDER BY SQL_SUCCESS_IND;
-- red flag: duplication appearing after reg-SQL m_CW_INS_ESCHT_OWNR_DETAILS.

-- G. PO010 tax value doubled (§7, 24-00953186) — duplicate staging rows
SELECT PROP_NO, OWNR_BA_NO, ACCT_PRD, COUNT(*) AS dup
FROM   <PO010 staging table> GROUP BY PROP_NO, OWNR_BA_NO, ACCT_PRD HAVING COUNT(*) > 1;

-- H. Production tax on SR/SOD owners that should be exempt (§10, 22-00512935/22-00827442)
--    Confirm the interest type and product on the booking that got tax.
SELECT RVNU_RUN_ID, PROP_NO, BA_NO, INT_TYPE_CD, DO_TYPE_CD, PROD_CD, TAX_AMT
FROM   <revenue distribution detail> WHERE PROP_NO = '<prop>' AND INT_TYPE_CD IN ('SR') AND TAX_AMT <> 0;
```

---

## 15. Expected-Behavior / User-Education FAQ

~47 Training + ~48 Customer-Error cases. Recognize these to avoid needless scripts/escalations — several are the **user-error twin** of a defect above.

| Reported as | Reality / answer | Case |
|---|---|---|
| "Escheat owner releases are **randomly doubling**" | **User error** — ran **CU (Current-State) then MA (Manual-Selection) without posting in between**, so the same SL records were included in both passes. **Correct order: run MA, POST, then CU** (or per your config — but post between). This is the twin of the §8 defect — rule it out first. | 26-01098217 |
| "**Payout exports not working / report blank**" | **Prerequisite steps not run.** Must run, in order, in QP043 Process Type = Payouts: **POMERGEJIB → POEXTRPEXP → POGNRTRPT**; then the QP085 PO0xx reports are runnable. | 25-01062263, 25-01040409, 22-00520419 |
| "Payout **pricing/sales price looks wrong**" | **By design.** Sales Price = **Σ(Transaction Amount) ÷ Σ(Transaction Quantity)** from the subledger (JE101) for a given property / major product / acct-prd. (e.g. 76.773 = sum amt / sum qty). | 25-01030213 (#1752719), 24-00956570, 25-01045817, 25-01024828 |
| "**Current** escheat cutoff date is wrong / I want a specific cutoff" | Current-State has **no cutoff-date parameter**; to use a specific cutoff, run **Escheat – Manual Selection** instead. | 25-01045717, 25-01035348 ("not an error, expected behavior") |
| "Negative Reporting Flag on EC010 — what does it do?" | **State-specific** — controls whether negative balances may be reported or netted against prior escheat; differs by state's unclaimed-property rules. | 26-01065509 |
| "How do I **upload well/DOI data / clear staging** in the A&D module?" / "QP43 stage failed" | **Training + correct steps.** Walk the QP043 upload steps; "stage failed" is usually a **missing owner / missing table row** to add, not a defect. Removing wells from allocation groups happens **in the allocation screens, not the A&D batch**. | 22-00823541, 22-00591800, 22-00682495, 22-00532944, 25-01012058, 25-01004859 |
| "`CWMNLESCHT` errors / FK `DONL_DO_HDR`" | Often **missing DOI data** for a property — DO team adds the data and the process runs. | 25-01050551 |
| "EC Final **hung**" | Client **missing the global config for state of incorporation**. | 22-00672684 |
| "Disposition process errors / well-status update" | Process/training — confirm the right module; dispositions don't remove wells from allocation groups. | 25-01012058, 22-00831011 |
| "Need **escheat / DOI-payout setup training or documentation**" | Documentation / training (no fix). | 25-01021010, 22-00582941, 23-00884455, 22-00591800 |
| "MJEUPLD / journal upload fails" | Often an **MS Access driver** missing on the workstation — reinstall. | 22-00661377 |
| "Batch job not running / locks / restart QPEC" | Use the **Upstream Maintenance Application** to clear locks / restart QPEC; confirm processes are at END/complete. | 22-00661289, 23-00928970, 22-00678350 |

**Tell-tale it's user/expected:** escheat "doubling" from wrong MA/CU order without posting; payout reports "blank" because the three generate steps weren't run; payout price questioned (it's Σamt/Σqty); Current-State cutoff "wrong" (no such parameter — use Manual Selection); A&D "stage failed" from a missing owner/row; or an audit/"how do I / what does this flag do" question. Verify the **process order, prerequisite steps, and upstream DOI/revenue data** before treating it as a defect.

---

## 16. Key Code, Processes & Repos

### Processes / batch steps (QP043 launcher; QP085 reports)
| Process / step | Code | Purpose | Cluster |
|---|---|---|---|
| A&D import / convert | (QP043 import path → `*ASTG_ORG_V2` staging → live `DONL_DO_*`, `SXREF_BA_*`) | Load acquired/divested prop/well/BA/DOI | §4/§5 |
| **POMERGEJIB → POEXTRPEXP → POGNRTRPT** | Payout process steps | JIB-expense merge → property-expense extract → generate payout report detail | §6/§7/§15 |
| Payout staging | `*_SP_PAYOUT_STAGING` / `Insert_RONL_PO_DETAIL_RVNU` → `RONL_PO_DETAIL_RVNU` | Build payout revenue detail | §6 (NULL RYLTY_RATE) |
| **CWMNLESCHT / CWUCESCHT** | Escheat Manual-Selection / Current-State (`m_CW_INS_ESCHT_OWNR_DETAILS`) | Escheat owner detail → `DONL_ESCHT_OWNR_DETAIL` (EC006) | §8 |
| **TRRYLMMSER** | `QPSRoyaltyReportingErrorCheckMMS` (`QPDllRevenueAcctgTRR`) | ONRR/MMS royalty reporting | §11 (OOM) |
| **BKRVNU / VL100 / RDCALC** | Revenue valuation/booking | Revenue distribution & valuation | §11 (timeout) |
| **CWACHEMAIL / CW_MAIN / CWOWFNDRLS** | Check-write family; `USPR_CW_OWNR_FUND_RLS_SPLIT` | ACH email stubs / check write / owner funds release | §12 |

### Code locations (confirmed via ADO code search)
| Symbol | Repo / path | Cluster |
|---|---|---|
| `USPR_CW_OWNR_FUND_RLS_SPLIT.sql` | **`Quorum.Upstream.QRA.Database`** /Stored Procedures/ (also in `Quorum.Upstream.Database/…QRA.Database`) | §12 owner funds release |
| `QPSRoyaltyReportingErrorCheckMMS.cpp/.h`, `QPSRoyaltyReportingCalculationsMMS.cpp`, `QPSRoyaltyReportingOutputMMS.cpp` | **`Quorum.Upstream.QRA.ClassicBatch`** /`QPDllRevenueAcctgTRR`/ | §11 ONRR/MMS |
| Core QRA stored procs & DB migrations | `Quorum.Upstream.QRA.Database` / `Quorum.Upstream.Database` (FluentMigrator EmbeddedScripts/MSSQL/QRA) | §6/§8/§12 |
| Client metadata (process-step defs, code tables) | `<CLIENT>.Upstream.Metadata` (e.g. `SUM.Upstream.Metadata`, `ATR.Upstream.Metadata`) — `QARCH_CTRL_PROCESS_STEP.json`, `QARCH_CDTBL_DEFINE.json` | metadata/config |

### Repos
- **`Quorum.Upstream.QRA.Database`** — core QRA stored procs (payout staging, escheat insert, CW owner-funds-release, payout/escheat views). **Most data/config fixes (sysgen view overrides, proc changes) live here.**
- **`Quorum.Upstream.QRA.ClassicBatch`** — C++ batch DLLs (`QPDllRevenueAcctgTRR` = ONRR/MMS royalty reporting; revenue/valuation steps). OOM/timeout code fixes here.
- **`Quorum.Upstream.Database`** — broader Upstream DB (FluentMigrator migration scripts; bundles the QRA DB project).
- **`<CLIENT>.Upstream.Metadata`** — per-client process-step, screen, and code-table metadata (e.g. code table 18012 for MP types). Client-specific config; **check the client metadata/schema first** — many fixes are env/client-specific (archive-join view override, escheat parameters, report versions).

---

## 17. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A **calculation/insert is provably wrong** on correct inputs: PAYOUT NULL RYLTY_RATE on a JIB-only deck (25-01010666/#1720425), PO010 tax doubled by duplicate insert (24-00953186), POR005 owner discrepancy from the archive-join view (24-00994733/#1713439), escheat EC006 duplication after Final `CWUCESCHT` (26-01090132 / lineage #1321337), production tax on exempt SR/SOD owners (22-00512935; SOD-on-MEG patched 01/2023, 22-00827442), PPA reversing off current instead of historical NRI (22-00704955).
- A **batch step crashes from a code limit**: ONRR `TRRYLMMSER` Out of Memory (22-00830416, code change), CW OOM (#1718501), `CWOWFNDRLS` proc param mismatch (`@REJ_FL`, 22-00612413).
- An **upgrade broke a parameter/report**: escheat Country-Code param (24-00986934/#1695760), RPT_PO005 fails to launch (#1680349).
- Provide: **Process Queue ID + failing step + exact `[COM Error]`/SQL error**, client + DB/env, the prop/BA/Payout-ID/RRID, and a repro. Confirm fix availability in the Upstream release notes and the WI's target patch.

**Handle as Configuration / Cloud-Ops (script or sysgen) when:**
- **A&D staging orphans / bulk ownership-BA corrections**: clear `*ASTG_ORG_V2` orphaned rows (26-01082244), scripted ownership/BA updates from corrected templates (25-01059532, 23-00923958). Verify-SELECT, transaction.
- **Payout reaching archived periods**: **sysgen archive-join view override** so the process reads `ARCV_*` (24-00992249) — delivered via OOC patch; re-validate balances after (the view itself can be buggy, #1713439).
- **Escheat date corrections** for previously-escheated owners (25-01045406/25-01042481) and **CWMNLESCHT PROC_FL** scripts (#1647080).
- **NACHA wrong-month** → Control-M step to purge SFTP after bank transfer (25-01016336); **CW "already processed"** → BRM state-reset script (22-00713800).
- **Client-specific metadata/code-table** gaps (e.g. code table 18012 root-node FL for MP type 20, 26-01069253) in `<CLIENT>.Upstream.Metadata`.

**Handle as Training / Expected behavior (no fix):** see §15 — escheat doubling from wrong **MA/CU order without posting** (run MA→POST→CU), payout reports blank because **POMERGEJIB→POEXTRPEXP→POGNRTRPT** weren't run, payout **price = Σamt/Σqty** by design, **Current-State has no cutoff parameter** (use Manual Selection), A&D "stage failed" from missing owner/row, MJEUPLD MS-Access driver, lock/QPEC restart via the Upstream Maintenance Application. Verify **process order, prerequisite steps, and upstream DOI/revenue data** before escalating.

---

*Skill created: 2026-06-14.*
*Based on: 409 closed QRA cases in Acquisitions and Dispositions (290) / Payouts (99) / Escheat (20) — 59 actionable (Software Defect 47 + Application Configuration 11 + ChangeConfig 1) mined for fix recipes, plus ~60 Training/Customer-Error cases for the FAQ. ADO work items #1720425, #1702254, #1713439, #1600613, #1680349, #1573809, #1548204, #1609740, #1391240, #1752719, #1765730, #1369887/#1372250, #1695760, #1321337, #1647080, #1693827, #1700164, #1702062, #1715033, #1718501, #1709194. Code: Quorum.Upstream.QRA.Database (USPR_CW_OWNR_FUND_RLS_SPLIT), Quorum.Upstream.QRA.ClassicBatch (QPDllRevenueAcctgTRR / QPSRoyaltyReportingErrorCheckMMS).*
*Companion: SKILL_QRA_* (Revenue Distribution / Valuation, Check-Write/ACH/1099, Suspense/Owner Relations, JIB), REPO_INVENTORY, CONFIG_REFERENCE.*
