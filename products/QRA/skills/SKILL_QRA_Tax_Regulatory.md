# SKILL: QRA Tax & Regulatory Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QRA (My Quorum Revenue Accounting — myQuorum/On Demand upstream oil-&-gas accounting)
**Scope:** The tax & regulatory reporting layer of QRA — **Severance / Production Tax** (state sev-tax preliminary, final, e-file/EDI, amendments, tax-combination rollup, tax JE posting), **1099 Reporting** (CW1099EXPT/CW675REXPS/CW675REXPT export, MISC vs NEC, backup withholding, file path/SFTP), and **Federal Royalty Regulatory reporting** (ONRR/MMS-2014, NAUPA/escheat). Covers the tax master screens (TR010, TS005/TS006, TS010, TS015, TS075, TS320, TX006, VL031), the QP043 severance batch process, and the `Quorum.Upstream.QRA.ClassicBatch` tax-combo/sev-tax engine.
**Companion skills:** revenue distribution / DOI / suspense / check-write → revenue-distribution skill; JIB → JIB skill. This skill *consumes* booked revenue + owner/DOI + master tax setup and *produces* tax filings, 1099 files, and ONRR/escheat output — when the *number itself* is wrong, fix the upstream revenue booking or the VL031 input first (tax is usually the messenger).

> **Evidence base:** 425 closed QRA Tax-&-Regulatory cases (Case_Category__c in Tax and Regulatory 401, Severance Tax Reporting 16, 1099 Reporting 8). Root-cause split: **(blank) 135, Software Defect 52, Customer Error 39, Customer Cancelled 37, Training 31, Business Change 22, Application Configuration 19**, Other 17, Not-in-Product-Plan 16, Hardware/Software Change 14, then long tail. This skill mines the **71 actionable** cases (Software Defect 52 + Application Configuration 19; no ChangeConfig rows exist in this dataset) for fix recipes, plus ~70 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining.

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — Texas Severance Tax calc / report / amendment defects (HIGHEST FREQUENCY)](#4-cluster-a--texas-severance-tax)
5. [Cluster B — Severance-tax process SPEs (TRSEVTX*, QP043, TAXJEPOST / TONL_TAX_INPUT)](#5-cluster-b--severance-tax-process-spes)
6. [Cluster C — Severance-tax e-file / EDI duplicates, footing & negative values](#6-cluster-c--severance-tax-e-file--edi)
7. [Cluster D — 1099 reporting (export accuracy, MISC vs NEC, backup withholding)](#7-cluster-d--1099-reporting)
8. [Cluster E — Export / SFTP file-path & folder configuration](#8-cluster-e--export--file-path-config)
9. [Cluster F — ONRR / MMS-2014 federal royalty reporting](#9-cluster-f--onrr--mms-2014)
10. [Cluster G — Escheat / NAUPA / unclaimed property](#10-cluster-g--escheat--naupa)
11. [Cluster H — Tax master screens (TR010 / TS010 / TS015 / grid & registered-SQL)](#11-cluster-h--tax-master-screens)
12. [Cluster I — Lease Use / tax-free volume calculation](#12-cluster-i--lease-use--tax-free-volume)
13. [Known ADO Items](#13-known-ado-items)
14. [Diagnostic SQL](#14-diagnostic-sql)
15. [Expected-Behavior / User-Education FAQ](#15-expected-behavior--user-education-faq)
16. [Key Code, Processes & Repos](#16-key-code-processes--repos)
17. [Escalation Guidance](#17-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| TX Severance Tax **amendments don't reverse** prior bookings | Amendment/reversal defect (esp. originals booked in **v16**) | §4 — fixed bug **#1725228**; confirm build |
| TX Oil Sev Tax report (**TSR096**) incorrectly flags leases as **Drilling Permit** | Drilling-Permit flag logic on the report | §4 — bug **#1732390**; lease's Drilling-Permit checkbox drives Yes/No |
| Sev-tax **EDI/PDF tie-out don't match**; reg fees missing from filing | Tax-amount sum logic / config gap | §4/§6 (25-01009292 sum logic; 25-01007859 config) |
| **TAXJEPOST / TRTAXCOMBO** fails — "Failed to insert into `TONL_TAX_INPUT`" / **PK error** / duplicate property rows | Tax-combination rollup defect creating **duplicate `TONL_TAX_INPUT`** rows; step `QPSTAXCOMBO` / `RATXCMBO37` | §5 — data clean-up script to delete dups; bug **#1589115** |
| Sev-tax prelim/efi **SPE** (TRSEVTXRPT, TRSEVTXRPF, TRSEVTXEPR, TRSEVOKRPT, TRSEVLARPT, QP043 SQLID error) | Process step error — bad data / column-bind / missing parm / env-specific | §5 — get exact step + SQLID + ORA error |
| Sev-tax **e-file has duplicate lines / footing errors / negative taxes** | Override-rate report-group duplication; TS075 auto-2-line; e-file build | §6 — bug **#1587320** (overstates/duplicates) |
| **1099 export not accurate** — Box15/Box17 (State WH / State Income) showing 0, or wrong amounts | 1099 export pulling wrong columns | §7 — bug **#1771560** |
| 1099 backup-withholding on **NEC instead of MISC**; foreign-owner false warning | 1099 form-box mapping / foreign-owner check | §7 — Hotfix 27; foreign-owner warning bug **#1430314** |
| Export/process errors "file not found", efile/NM/sev/1099 **not generated** | **Export file path / folder / SFTP definition not set up** | §8 — set File Path on the imp/exp definition (very common config fix) |
| **ONRR Preliminary failing** / ONRR-2014 dropping or doubling mmbtu / file-structure | ONRR process defect or PPA mmbtu data gap; periodic ONRR format hotfixes | §9 — bug **#1733150**; ONRR hotfix |
| **Escheat / NAUPA** report not created, dates wrong, final doubles amount | Escheat date/setup data; NAUPA metadata; doubling = known | §10 — date-update script; reddog metadata |
| Can't filter / wrong rows on **TS010 / TS015 / TR010** grid | **Registered SQL + Grid Definition** metadata bug | §11 — correct grid def / registered SQL |
| **Lease Use** deduction wrong — Volume carried to TS006 instead of Gross Value | Lease-Use calc defect (Volume×Price not applied) | §12 — Adjustment Override workaround; verify VL031 Marketing Adjustment |

---

## 2. Pipeline & Concepts

```
[Revenue booking: VL031 (volumes, price, marketing adj) + Owner/DOI + Suspense]
      │
      ▼  TAX MASTER SETUP: TR010 (tax reporting reg) · TS005/TS006 (sev-tax common maint) · TX006 (adjustment categories) · TS075 (override rates)
      │
      ▼  SEVERANCE/PRODUCTION TAX  (QP043 process: TRSEVTX* prelim → tax-combination rollup QPSTAXCOMBO → TONL_TAX_INPUT → TAXJEPOST tax JE → TRSEVTX*RPF FINAL)
[TONL_TAX_INPUT (tax input rows), tax JE, TS010/TS015/TS320 review screens]
      │
      ├──► STATE TAX FILINGS  (preliminary/final reports, e-file/EDI: TX CPA, OK, KS, NM, ND, LA, UT; TR_TX_CPA / TR_TX_CPA_CSV)
      ├──► FEDERAL ROYALTY   (ONRR/MMS-2014 e-file, royalty final report)
      ├──► 1099 REPORTING    (CW1099EXPT / CW675REXPS / CW675REXPT → 1099 MISC/NEC file + SFTP)
      └──► ESCHEAT / NAUPA   (unclaimed-property file, EC005/EC006)
```

### Key terms (QRA / upstream-accounting vocabulary)
- **Severance / production tax** — state tax on produced oil/gas/NGL. Each state has its own preliminary & final reports and e-file/EDI format (TX, OK, KS, NM, ND, LA, UT). **TX is by far the highest case volume.**
- **QP043** — the severance-tax batch process type that runs the state TRSEV* steps. A failing run is keyed by the **process + step name (e.g. TRSEVTXRPT) + the SQLID + ORA error**.
- **TRSEVTX*** steps — `TRSEVTXRPT` (TX prelim report), `TRSEVTXRPF` (TX **FINAL** — and the "undo FINAL" path), `TRSEVTXEPR`/`TRSEVTXEFI` (TX e-file), `TRSEVOKRPT` (OK prelim), `TRSEVLARPT` (LA), etc.
- **Tax-combination rollup** — `TRTAXCOMBO` process step, C++ class **`QPSTAXCOMBO`** (step variant `RATXCMBO37`), proc `TAX_COMBO_INS_TAX_INPUT_2ND_ROLLUP`. Inserts combined tax rows into **`TONL_TAX_INPUT`**. Duplicate property rows here = the classic TAXJEPOST/PK-error failure (§5).
- **`TONL_TAX_INPUT`** — staging table that feeds the **tax JE post (TAXJEPOST)**. PK/unique-constraint collisions here stop posting.
- **TS005 / TS006** — Severance Tax Common Maintenance (tax setup + Marketing Adjustment / Lease Use). **TX006** — adjustment categories. **TS075** — override (special-rate) tabs. **TS010 / TS015 / TS320** — sev-tax review/inspect grids. **TR010** — tax reporting registration (tract allocation, RRN trigger).
- **TX CPA** — Texas Comptroller of Public Accounts; import/export defs `TR_TX_CPA` / `TR_TX_CPA_CSV`; oil prelim history table `TTRN_TX_CPA_OIL_PRELIM_HIST`.
- **1099 processes** — `CW1099EXPT` (1099 export), `CW675REXPS`/`CW675REXPT` (revenue 1099 export under process type 1099), `CW1099EXPG` (global), `CW099` screen/table. MISC vs **NEC** box mapping and **federal backup withholding** are recurring defect areas.
- **ONRR / MMS-2014** — federal royalty regulatory reporting (Office of Natural Resources Revenue, formerly MMS). Process `TRRYLMMSEF`, "2014" report/e-file. **NAUPA** = unclaimed-property/escheat file standard.
- **Lease Use** — gas used on-lease (not sold), a deduction. Entered as **Lease Use Volume** in VL031 Marketing Adjustment; QRA should compute **Lease Use Gross Value = Volume × Price** and carry it to TS006.
- **Drilling Permit flag** — a lease attribute that TX oil reports (TSR096) print Yes/No from.

---

## 3. Decision Tree

```
QRA Tax / Regulatory case
│
├─ A batch process/step FAILED (SPE / "Stopped Processing on Error")?  →  GET PROCESS + STEP NAME + SQLID + EXACT ORA ERROR + client/env
│   ├─ TAXJEPOST / TRTAXCOMBO → "insert into TONL_TAX_INPUT" / PK error / dup property rows  → §5 (dup tax-input rows; clean-up script; #1589115)
│   ├─ TRSEVTX*RPT / RPF / EPR / EFI / TRSEVOKRPT / TRSEVLARPT / QP043 SQLID_*  → §5 (step-specific; bad data / column bind / missing parm / env)
│   ├─ ONRR Preliminary failing                                                  → §9 (#1733150)
│   └─ 1099 export process erroring (CW1099EXPT/CW675REXP*)                       → §7 / §8 (often file-path config, §8)
│
├─ Output WRONG (process ran but numbers/file are off)?
│   ├─ TX sev tax amendment not reversing (orig in v16)                          → §4 (#1725228)
│   ├─ TX oil report flags lease as Drilling Permit incorrectly (TSR096)         → §4 (#1732390)
│   ├─ Sev-tax EDI/PDF tie-out mismatch / reg fees missing                       → §4/§6 (sum logic 25-01009292; config 25-01007859)
│   ├─ E-file duplicate lines / footing / negative taxes                         → §6 (#1587320; override-rate report groups; TS075 2-line)
│   ├─ 1099 file: Box15/17 zero / inaccurate / MISC-vs-NEC / backup-wh           → §7 (#1771560; Hotfix 27; foreign-owner #1430314)
│   ├─ ONRR-2014 dropping/doubling mmbtu                                         → §9 (PPA mmbtu data gap)
│   └─ Lease Use deduction = Volume not Gross Value                              → §12 (override workaround; verify VL031)
│
├─ "File not found" / efile / NM / sev / 1099 NOT generated?                     → §8 (Export file path / folder / SFTP definition not set up — VERY common)
│
├─ Can't filter / wrong rows on a tax grid (TS010/TS015/TR010)?                  → §11 (Registered SQL + Grid Definition metadata)
│
├─ Escheat / NAUPA report not created / wrong dates / doubling?                  → §10
│
└─ "How do I…" / setup / rate / amend / undo-FINAL / audit question             → §15 Expected-Behavior FAQ (Training / Customer Error)
```

---

## 4. Cluster A — Texas Severance Tax

**The single largest actionable cluster.** TX sev tax dominates QRA tax cases; the recurring defect families are **amendment/reversal handling, report flags, tie-out (EDI vs PDF), and the schema/column types behind TX tax tables**. Much of the legacy pre-2020 TX defect volume was rolled up into the **"Texas Tax rewrite" (2020.03 → 2020.09 GA → Spring 2022 QUBE work, ADO #1397814)** and **v17** — so for old TX symptoms, the first question is "what build are you on?"

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| TX Sev Tax **amendments don't reverse** original bookings | Amendment-reversal defect, esp. when originals were booked in **v16** | Code fix | 25-01010533 / **#1725228** (CEN, Bug, Closed) |
| Also: TX Sev Tax **reversal incorrect** (MEW upgrade) | Same reversal family | Defect | 22-00659959 |
| TX Oil Sev Tax report **TSR096 mislabels leases as Drilling Permit** | Report's Drilling-Permit flag logic | When lease marked Drilling Permit → Yes checked; else No (corrected) | 25-01019756 / **#1732390** (CEN, Bug, Closed) |
| Sev-tax **EDI and PDF don't match** (tie-out) | Tax amount selected/summed incorrectly | "Changing the way the tax amount is selected and summed allowed the value to be set properly" | 25-01009292 |
| **Reg fees not included** in TX filing | Configuration gap | Configuration change + user documentation | 25-01007859 |
| TX tax calc **inconsistent DEV vs PROD** (blocking go-live) | Metadata-layer value not quoted | Added quotes as `'5525'` in the Metadata layer → fixed | 23-00901426 |
| TX tax DB tables wrong **column data type** (`char` vs `varchar`) | Schema drift on TX tax tables | Changed columns from `char` → `varchar` | 25-01010533 |
| "50% of Value" edit | TX value-edit config | Configuration | 22-00823298 |
| Legacy: negative taxable values, tax-free volume, Type-5 exemption, lease use | Pre-rewrite TX engine defects | **Texas Tax rewrite — 2020.03 / 2020.09 GA / Spring 2022** | 22-00688381, 22-00688361, 22-00597852, 22-00655421, 22-00591901, 22-00591941, 22-00688374, 22-00659992 (v17) |

**Permian Resources upgrade sub-cluster (2024–2025)** — a large block of actionable TX sev-tax cases came out of the Permian (CEN) upgrade E2E. Several were config/metadata, not core engine:
- **25-01003197** — TX Oil Sev Tax "Errors in registered SQL": removed an unneeded requirement from `TTRN_TX_CPA_OIL_PRELIM_HIST`; also Revenue had to fix wells where **Tax Pay Code = 2 (Purchaser)** (the process can't handle those) before PPNs would post.
- **25-01007857** — TSR095 TX Oil Prelim "failed to export": ran a script to insert the **Report Generate Date** parameter; BOM included on the **2023.04 HF (March)**.
- **25-01019829** — "Off Lease" flag: **TS015 grid (grid definition 16000) had bad logic**; metadata corrected and checked in (June Hotfix).
- **24-00973138 / 24-00972614 / 25-01045147** — export **file path/folder not set up** (see §8).

**Fix recipe:**
1. **Get the build/version first.** Most pre-2020 TX symptoms (negative values, exemptions, lease use, tie-out) are resolved by the **TX Tax rewrite (2020.09)** / **v17**. Confirm in release notes before treating as a new defect.
2. **Amendment not reversing** → known bug **#1725228**; confirm the client's build contains it; pay attention to bookings originally done in **v16**.
3. **Tie-out (EDI vs PDF) / reg fees / Off-Lease flag** → usually **config or metadata** (grid def / registered SQL / metadata quoting), not engine. Check the TS015 grid def, the TR_TX_CPA export def, and the metadata layer (23-00901426 quoting; 25-01019829 grid def 16000).
4. **DEV-vs-PROD inconsistency** → compare metadata between environments; a single un-quoted/typed value can diverge calc (23-00901426; 25-01010533 char vs varchar).

---

## 5. Cluster B — Severance-tax process SPEs

Process-step failures ("Stopped Processing on Error" / SPE) in the **QP043** severance run. The actionable defects center on the **tax-combination rollup → `TONL_TAX_INPUT` → tax JE post (TAXJEPOST)** path.

### B1 — TAXJEPOST / TRTAXCOMBO insert into TONL_TAX_INPUT (the marquee signature)

**Symptom (verbatim, 24-00939420):**
```
Failed to execute SQL : TAX_COMBO_INS_TAX_INPUT_2ND_ROLLUP
Failed to insert records into the TONL_TAX_INPUT table.
Call to C++ Batch Process Step Class Name QPSTAXCOMBO failed Execute
Continue Process On Failed Execute Is FALSE for TRTAXCOMBO: Perform tax combination rollup. Process will STOP.
```
Posting a PPN succeeds in revenue but **fails to post in QRA** at the tax-combination rollup.

**Root cause:** the tax-combination rollup creates **duplicate rows in `TONL_TAX_INPUT`** for the same property (e.g. two properties `206052711` / `206045111` with otherwise-identical key tuples, FE vs PR tax type) — a software defect — which then violates the table's PK/unique key when the tax JE post runs (the `RATXCMBO37` PK error).

**Fixes seen:**
- **24-00946826 (related to 24-00939420):** "Provided **data clean-up script to delete erroneous data created by software defect**" — i.e. delete the duplicate `TONL_TAX_INPUT` rows for the affected wells/property, then re-post.
- **26-01095867:** same family — duplicate `TONL_TAX_INPUT` rows for properties `206052711` / `206045111`; clean up before checkwrite.
- **ADO #1589115** (TGNR, Bug, Closed): "PPN unable to post — **RATXCMBO37 PK Error TONL_TAX_INPUT**" — the engineering bug for this signature.
- Also **24-00938123** (Customer Error / data cleanup): "Unreported Texas Tax Records after the JE Tax Post process fails" — same operational cleanup pattern.

**Fix recipe:** (1) confirm the failing step is **TRTAXCOMBO / QPSTAXCOMBO** and the error references `TONL_TAX_INPUT` + a PK/unique violation. (2) Identify duplicate `TONL_TAX_INPUT` rows for the PPN's properties (Diagnostic SQL §14-A). (3) Apply the **clean-up script to delete the duplicates** (verify-SELECT first, wrap in a transaction). (4) Re-run the tax post. (5) If duplicates keep regenerating, it's the engine defect (#1589115) — escalate with the property IDs + prod month.

### B2 — Other sev-tax step SPEs (state prelim/efile)

| Step / signature | Pattern | Disposition | Case |
|---|---|---|---|
| `TRSEVOKRPT` — "`T.CTRY_CD` could not be bound" (OK prelim SPE) | Column-bind defect in OK prelim | Build fix (Newfield integration) | 22-00512615 |
| `TRSEVTXEPR` fails (UAT BUILD_QP043) | TX e-file prelim step | Build fix | 22-00684098 |
| `TRSEVTXEFI` — "Missing Parm" | Missing process parameter | Add the missing parm / latest release | 22-00688731 |
| `TRSEVTX` — "Tax Error PK: \|-119" | PK/data error | Defect | 24-00956279 |
| UTE Sev prelim SPE (FSTR5582 / FSTR4587) | Newfield/UTE prelim build issues | Build | 22-00513006, 22-00512833 |
| `TR010` copy/paste doesn't populate API No → error on add | Screen defect (copy/paste) | Defect | 22-00647333 |

> Several B2 cases have **no Resolution__c text** (legacy Newfield/UTE build tickets) — resolution pattern is "build/integration fix delivered," exact text unclear from mined cases. For a live SPE, always capture **process + step + SQLID + ORA error + client/env** — many "SPE" cases turn out to be **env/config or missing-data**, not engine (see §15 FAQ: TRSEVTXRPT/RPF, Kansas blank prelim, QP043 SQLID errors).

---

## 6. Cluster C — Severance-tax e-file / EDI

E-file/EDI output defects — duplicates, footing, negative taxes.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| TX Sev Tax Prelim **Overstates / Duplicates Values** | Report duplication logic | Code fix | 23-00891150 / **#1587320** (CEN, Bug, Closed) |
| Sev-tax **e-file duplicate lines** for override-rate wells | Wells with special first-sales rates (4%/5%/6%) using **Override tabs** create duplicate e-file lines although no tax is due; **TS075 auto-creates 2 lines from 1 entry** | TS075 correction needed | 22-00640019 |
| **Negative taxes & footing errors** on TX EDI file | EDI build/footing defect | Defect | 22-00704956 |
| Severance Tax **e-file duplicates** (general) | E-file dedup logic | Defect | 22-00640019, 22-00687017 |
| TX Natural Gas Producer Tax Report (crude / service-provider-number / engineering #175124) | Report-format defects | Defects (legacy) | 22-00704986, 22-00704978, 22-00704977 |

**Fix recipe:** when the e-file/EDI **doubles lines or overstates**, check (a) whether the affected wells use **TS075 override (special-rate) tabs** — a single override entry can auto-generate 2 lines (22-00640019); (b) whether it's the prelim-overstates defect **#1587320**. Footing/negative-tax issues on the TX EDI are build defects (22-00704956). Reconcile the **EDI vs PDF** the same way as §4 tie-out (sum logic, 25-01009292).

---

## 7. Cluster D — 1099 Reporting

1099 export accuracy, form-box mapping (MISC vs NEC), and backup withholding.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **QRA 1099 Export not providing accurate data** | Export pulling wrong/zero columns | Code fix | 25-01056145, 25-01056145 / **#1771560** (CNX, Bug, Closed) |
| 1099 MISC file has **0 in Box17 (State Income) & Box15 (State WH)** though source table has values | Export not pulling the state columns | Same family as #1771560 | 25-01056145 |
| **1099 Invalid Error Message** — false warning that 1099 is needed for **foreign owners** | Foreign-owner check in 1099 Load | Code fix | 24-00940346 / **#1430314** (Bug, Closed — "1099 Load - incorrect warning saying 1099 needed for foreign owners") |
| Federal backup withholding shows on **1099-NEC instead of MISC** | Form-box mapping | Defect | 23-00934524, 22-00818726 |
| **1099 MISC data file missing federal w/h amounts** | Export defect | **Software update in Hotfix 27** | 22-00651660 |
| New 1099 processes `CW675REXPS` / `CW675REXPT` (process type 1099) | New build / packaging | **Included in Spring 2022 upgrade** | 22-00512933, 22-00512951, 22-00808366 |
| **QRA 1099 records not exporting** | Export defect | Defect | 22-00672592 |
| Updates to the 1099 export file (AST) | Enhancement to export format | Feature | (1099 cluster) / **#1455630** (AST, Feature, Closed) |

**Fix recipe:** "1099 numbers wrong / file blank in a box" → check which **columns the export pulls** vs the source table (25-01056145/#1771560 — State WH/Income); confirm the build has Hotfix 27 (federal w/h, 22-00651660) and #1430314 (foreign-owner false warning). **MISC vs NEC** mis-boxing (backup withholding) is a form-mapping defect (23-00934524). Many 1099 *errors* are actually **file-path/SFTP config (§8)** or training (§15) — rule those out first.

---

## 8. Cluster E — Export / File-Path Config

**The dominant Application-Configuration cluster.** Tax/1099/escheat exports fail or "don't generate" simply because the **File Path / export folder / SFTP transfer definition is not set up** for that process in the environment. This is config, not a defect.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| TX Severance Tax efile export — file not landing | Target folder **didn't exist** in QCloud network | Created the folder (e.g. `…\AppFiles\Upstream\Exports\Texas Severance Tax efile`); process then worked | 24-00973138 |
| "Can't find sev tax extract for QP043" | File path **not set in the export definition** | Provided a script to add the path | 25-01045147 |
| NM Severance Excel Extract won't run | File path on the **NM Export process** not added | Script + instructions to add via the **Maintenance app** | 24-00972614 |
| Severance Tax **E-file Error** | **File Path** field blank on `TR_TX_CPA` / `TR_TX_CPA_CSV` imp/exp definition screens | Set the Exports path on the FS server | 23-00933898 |
| QRA `CW1099EXPT` **file path** | 1099 export path not configured | Set path | 25-00996195 |
| Create **1099 Export folder + SFTP Transfer definition** (QRA & QLS) | New env needs 1099 FTP defs | Created 1099 FTP definitions, mapped path for Upstream & QLS; added to client post-refresh repo | 25-01047728 / **#1761149** (CNX, Requirement, Closed) |

**Fix recipe:** for any "export errored / file not found / process didn't generate output," **check the imp/exp definition's File Path field** and that the **target folder exists in QCloud** and the **SFTP transfer definition** is present. Fix via the export definition screen or the **Maintenance app** (a script can set it). Add the path to the client's **post-refresh repo** so it survives DB refreshes (a refresh wipes env-specific paths — see the related DB-refresh tickets #1768499/#1769049).

---

## 9. Cluster F — ONRR / MMS-2014

Federal royalty regulatory reporting (Office of Natural Resources Revenue / legacy MMS), "2014" report & e-file.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **ONRR Preliminary failing** (critical) | Process defect | Code fix | 25-01022349 / **#1733150** (BP PRD, Bug, Closed) |
| **ONRR-2014 file-structure change** | Federal format change | **ONRR hotfix** | 22-00814371 |
| MMS `TRRYLMMSEF` Agreement-Number file-format change | Federal format change | **ONRR hotfix** | 22-00685965 |
| ONRR **dropping or doubling mmbtu** → invalid 2014 reporting lines | PPAs for gas missing **mmbtu** on the 2014 records (btu factor falls outside ONRR edit range) | Override in system / ECommerce; underlying data gap | 22-00830233 |
| API needed for lease-level ONRR reporting | Build/enhancement | Build | 22-00544824 |
| MMS process not working / 2014 process review | Process/config | (legacy, resolution unclear from mined cases) | 22-00651658, 22-00657244 |
| Auto-gen MMS Royalty Final Report inconsistent with JE | Report/process consistency | (resolution unclear from mined cases) | 22-00657272 |

**Fix recipe:** ONRR is a **moving federal target** — file-structure/format changes are handled by periodic **ONRR hotfixes** (22-00814371, 22-00685965); check whether a current hotfix covers the format the client is failing on. For **dropping/doubling mmbtu**, it's a **PPA data gap** (missing mmbtu on gas 2014 records → btu factor out of ONRR's valid range) — verify the PPA records have mmbtu before assuming an engine bug. "ONRR Preliminary failing" is bug **#1733150**.

---

## 10. Cluster G — Escheat / NAUPA

Unclaimed-property reporting. Mostly **data/date fixes and metadata**, plus a known doubling behavior.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Escheat dates wrong (high-importance) | Dates on the escheat records | **Script to update the dates on the escheat** | 25-01027368 |
| **Escheat Mismatch — Delaware** | State escheat data/setup | Defect (legacy, resolution unclear from mined cases) | 22-00668108, 22-00668087 |
| **REDDOG / NAUPA file** test | NAUPA metadata | **Updated reddog metadata provided** | 22-00668091, 22-00678345 |
| Escheat **final process doubles amount due** | Escheat-final doubling | Known behavior (see §15) | 22-00659976 |

**Fix recipe:** escheat issues are usually **data fixes** (update escheat dates via script — 25-01027368) or **NAUPA/reddog metadata** updates (22-00668091). If the escheat **final doubles the amount**, treat as the known doubling pattern (verify against §15 before scripting). For "delete EC005/EC006 records for escheat," that's a data-cleanup request (see §15).

---

## 11. Cluster H — Tax Master Screens

Grid/filter/save issues on the tax master screens (**TS010, TS015, TR010**) resolve as **metadata fixes — Registered SQL + Grid Definition**, not engine defects.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **TS010 Well Class filter not working** (round-2 testing) | Grid filter metadata | **Updated Registered SQL and Grid Definition** for TS010 → filter works | 25-01053790, 25-01044137 |
| **TS015 "Off Lease" flag** grid wrong | **Grid definition 16000** had bad logic | Metadata corrected and checked in (June HF) | 25-01019829 |
| **TR010 behaving differently since upgrade** (allocation factors) | Missing business-rule setup | Added a **business rule setup** → user can add different allocation factors per product | 23-00920984 |
| **TR010 Tract Allocation** | RRN trigger | **Updated RRN trigger on TR010** | 22-00826280 |
| TR010 copy/paste doesn't populate API No → error on add | Screen copy/paste defect | Defect (build) | 22-00647333 |
| Reverse/Rebook **TS015** screen | Screen code fix | **Code fix delivered Sept 2020** (incl. 20-00076412, 20-00081693) | 22-00560550 |

**Fix recipe:** for "can't filter / wrong rows / column behaves wrong" on a tax grid (TS010/TS015/TR010), the fix is almost always a **metadata correction — update the screen's Registered SQL and/or Grid Definition** (25-01053790, 25-01044137, 25-01019829 grid def 16000). For TR010 allocation behavior, check for a **missing business-rule setup** (23-00920984) or the **RRN trigger** (22-00826280). These are Cloud-Ops / metadata changes, not Engineering escalations, unless a screen save itself is broken (22-00647333).

---

## 12. Cluster I — Lease Use / Tax-Free Volume

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **Lease Use Gross Value wrong** for one property — the **Lease Use Volume** (not Volume×Price) is carried to TS006 | Lease-Use calc defect: QRA should compute Lease Use **Gross Value = Lease Use Volume × Price** (both from VL031 Marketing Adjustment tab) and carry that to TS006; instead it carried the raw volume | Workaround: enter correct amount in the **Adjustment Override** column; underlying calc is the defect | 25-01043072 |
| **Lease Use Calculation** (legacy) | Pre-rewrite lease-use calc | **TX Tax rewrite** (resolved in 2020.x / v17) | 22-00688374, 22-00688361 (tax-free volume) |
| Severance tax **exempt value greater than gross value** | Exemption calc defect | Resolved in **v17** | 22-00659992 |

**Fix recipe:** Lease Use flows from **VL031 → Marketing Adjustment tab** (enter Lease Use **Volume**); QRA multiplies by **Price** to get **Gross Value**, which lands on **TS006 Marketing Adjustment**. If the **volume itself** is carrying over instead of the gross value (25-01043072), it's a calc defect — quick unblock is the **Adjustment Override** column on TS006; confirm the build (much of legacy lease-use/tax-free-volume was fixed in the **TX Tax rewrite / v17**).

---

## 13. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1725228** | Bug / **Closed** | CEN — TX Severance Tax Amendments not reversing original bookings when done in v16 | §4 | 25-01010533 |
| **#1732390** | Bug / **Closed** | CEN — TX Oil Severance Tax Report (TSR096) incorrectly labels leases as Drilling Permit | §4 | 25-01019756 |
| **#1397814** | Feature / **Closed** | Texas Severance Tax Final QUBE work, Issue Res, Documentation & Transition to Maint (Spring 2022) | §4 (TX rewrite) | 22-00591901/941, 22-00597852 |
| **#1587320** | Bug / **Closed** | CEN — TX Severance Tax Prelim Report Overstates/Duplicates Values (23-00891150) | §6 | 23-00891150 |
| **#1607780 / #1608581** | Bug / **Closed** | New processing of Texas Severance Tax failed (QMEM-5467; ET/EMP 2020.03) | §5 | — |
| **#1589115** | Bug / **Closed** | TGNR — PPN unable to post — RATXCMBO37 PK Error TONL_TAX_INPUT (23-00892611) | §5 | 24-00939420 family |
| **#1393874** | Task / **Closed** | NDTAX GAS — Amended run "No tax data to output" in TS320 despite TONL_TAX_INPUT data | §5 | — |
| **#1771560** | Bug / **Closed** | CNX — QRA 1099 Export is not providing accurate data | §7 | 25-01056145 |
| **#1430314** | Bug / **Closed** | 1099 Load — incorrect warning saying 1099 needed for foreign owners | §7 | 24-00940346 |
| **#1455630** | Feature / **Closed** | AST — Updates to the 1099 Export File | §7 | — |
| **#1761149** | Requirement / **Closed** | CNX — QLS — Create 1099 Export folder & SFTP transfer definition | §8 | 25-01047728 |
| **#1733150** | Bug / **Closed** | BP PRD — Critical — ONRR Preliminary Failing (25-01022349) | §9 | 25-01022349 |
| **#1538825 / #1538829** | Feature / **Discarded** | DAY — TX Sev Tax Reporting — Lease Use price calc & FE tax on Lease Use volume | §12 (not shipped) | — |

> Many actionable cases were dispositioned **operationally** (data clean-up script / config / metadata) with no single product WI: TONL_TAX_INPUT dup clean-up (24-00946826, 26-01095867, 24-00938123); escheat date script (25-01027368); export file-path config (24-00973138, 25-01045147, 24-00972614, 23-00933898, 25-00996195); TS010/TS015 grid-def + registered-SQL (25-01053790, 25-01044137, 25-01019829); metadata quoting DEV/PROD (23-00901426). Periodic **ONRR hotfixes** (22-00814371, 22-00685965) and the **TX Tax rewrite (2020.03 / 2020.09 GA)** + **1099 Hotfix 27** (22-00651660) cover large legacy blocks. Confirm exact build/patch in the QRA release notes when stating fix availability.

---

## 14. Diagnostic SQL

> **Caveat:** QRA runs on Oracle, per-client schemas. Table/column names below come from case repro text and code search; **verify against the client schema before scripting**, and always run a verify-SELECT before any DELETE/UPDATE, wrapped in a transaction.

```sql
-- A. Duplicate TONL_TAX_INPUT rows (the TAXJEPOST / RATXCMBO37 PK collision, §5)
--    Group on the natural key tuple for the prod month; a count > 1 is the defect's footprint.
SELECT PROPERTY_NO, TAX_TYPE_CD, PROD_DATE, ACCTG_DATE, TAX_CATEGORY, COUNT(*) dup_ct
FROM   TONL_TAX_INPUT
WHERE  PROD_DATE = DATE '<PROD_DATE>'          -- e.g. 2025-06-01
GROUP BY PROPERTY_NO, TAX_TYPE_CD, PROD_DATE, ACCTG_DATE, TAX_CATEGORY
HAVING COUNT(*) > 1
ORDER BY dup_ct DESC;
-- Properties like 206052711 / 206045111 with FE & PR rows are the 26-01095867 pattern.

-- B. Tax-input rows for a single PPN/property pending the tax JE post (§5)
SELECT * FROM TONL_TAX_INPUT
WHERE  PROPERTY_NO IN ('<prop1>','<prop2>') AND PROD_DATE = DATE '<PROD_DATE>'
ORDER BY PROPERTY_NO, TAX_TYPE_CD;

-- C. Wells with Tax Pay Code = 2 (Purchaser) — these block the TX prelim post (25-01003197)
SELECT WELL_ID, PROPERTY_NO, TAX_PAY_CD FROM <tax-setup table>
WHERE  TAX_PAY_CD = 2;

-- D. TX CPA oil prelim history (the 25-01003197 'unneeded requirement' / registered-SQL area)
SELECT * FROM TTRN_TX_CPA_OIL_PRELIM_HIST WHERE PROD_DATE = DATE '<PROD_DATE>';

-- E. Lease Use check: VL031 marketing-adjustment volume vs TS006 carried gross value (§12)
--    Expect TS006 gross value = lease-use volume * price; if it equals the volume, that's the 25-01043072 defect.
SELECT PROPERTY_NO, LEASE_USE_VOL, PRICE, (LEASE_USE_VOL * PRICE) expected_gross_value
FROM   <VL031 marketing-adjustment table>
WHERE  PROPERTY_NO = '<prop>' AND PROD_DATE = DATE '<PROD_DATE>';

-- F. Column data type drift on a TX tax table (the 25-01010533 char-vs-varchar pattern)
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, DATA_LENGTH
FROM   ALL_TAB_COLUMNS
WHERE  TABLE_NAME LIKE 'T%TX%'      -- TX tax tables
AND    DATA_TYPE = 'CHAR';          -- CHAR found where VARCHAR2 expected = drift

-- G. ONRR-2014 gas lines missing mmbtu (the 22-00830233 dropping/doubling pattern)
SELECT * FROM <ONRR 2014 staging table>
WHERE  PROD_CD = 'GAS' AND (MMBTU IS NULL OR MMBTU = 0) AND SALES_QTY > 0;

-- H. Escheat dates to update (25-01027368) — verify-SELECT before the date-update script
SELECT * FROM <escheat table> WHERE OWNER_NO = '<owner>' AND ESCHEAT_DT IS NULL;

-- I. Find the failing tax step + error by process run (QP043)
--    Get the process run / PQID + step name (TRSEVTXRPT, TRTAXCOMBO, etc.) from the user,
--    then read the batch message/log for that run + step + SQLID + ORA error.
```

---

## 15. Expected-Behavior / User-Education FAQ

~31 Training + ~39 Customer-Error cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| Sev-tax prelim/efi **SPE** (TRSEVTXRPT, TRSEVTXRPF, TRSEVTXEPR, TRSEVLARPT, "Gas Tax Prelim failed", "Prelim error", batch-type-37 sev-tax clear erroring) | Usually **bad data / env / missing parm**, not engine — capture step + SQLID + ORA error; many cleared once data or a parm was fixed | 22-00572150, 22-00566227, 22-00628264, 22-00628282, 22-00655388, 22-00577382, 22-00612514, 22-00661334, 24-00948013 |
| **Kansas Sev Tax Prelim Report blank** (Sandridge) | No qualifying data / config for that state-month — not a defect | 24-00978701, 24-00948114 |
| QP043 `SQLID_RPT_TX_INS_ORIGINAL_AND_PPA_RECORDS_INTO_STAGING` erroring | Staging/data condition — Customer Error; check the underlying records | 24-00964522 |
| "How do I **undo / clean a FINAL** Texas Severance run?" (TRSEVTXRPF / can't clean on JE100) | Training — the **FINAL** has a specific undo path (TRSEVTXRPF); cleaning on JE100 isn't always offered for prod-date-override FINAL runs | 22-00704985, 25-01023061 |
| "TX sev tax **amended** reporting — how?" / refund processing | Training — amended-reporting workflow | 25-01009559, 23-00933282 |
| 1099: voided checks included / "1099 Issue" / "Upstream 1099 Process" / processing for 2024 / errors+questions | Training — 1099 process walkthrough; voided-check handling is by design | 26-01068888, 25-00998867, 25-00998386, 25-01008520, 22-00644890, 25-01046334, 22-00638156, 22-00612454 |
| "Report owners with payment but **no Tax ID**" | Training / data request — run an owner report; not a defect | 25-00999440 |
| **Escheat** process / reset question / NAUPA not created / delete EC005-EC006 / final doubles | Training + known: escheat **final can double** in some flows; deletes are data-cleanup requests | 25-01005520, 22-00668124, 22-00622163, 25-01002388, 22-00659976 |
| Tax **calc** questions / NGL tax / "Utax uses wrong volume" / DEV-vs-PROD calc | Often **config / setup** (rate, basis, volume source) — verify TS005/TS006 + rate setup before calling it a bug | 24-00979812, 24-00972684, 22-00822917, 24-00989525, 22-00582850, 22-00512499 |
| Documentation requests — State Tax Rate Basis equations, TX Plant Inlet configs, MDR, MMS royalty questions | Documentation/education, not defects | 23-00928609, 22-00571441, 22-00571584, 22-00640017 |
| "Opt out of State Taxes" / "Tribal interest in OK" / "Updating gas tax rate for estimates/accruals" | Config/training — tax setup, not a defect | 25-01041289, 25-01032430, 22-00653919 |
| "Tax Clearing amount clarification" / "Extraction Tax not in JE100" / "Sev tax payable not clearing" | Training — tax-clearing & JE flow questions | 25-01003208, 24-00970687, 23-00917820, 22-00683997 |
| Permian upgrade: "TX sev tax PDF doesn't populate" / "TX Tax Config Assistance" | Config/setup during upgrade (often the export-path or grid-def, §8/§11) | 25-01003202, 25-01003200 |

**Tell-tale it's user/expected/config:** a sev-tax **SPE that clears once data/parm is fixed**; a **blank state prelim** with no qualifying data; a 1099 "issue" that's really a **process/voided-check question or a file-path** (§8); an escheat **reset/delete request**; a tax-calc "wrong number" that traces to **TS005/TS006 rate/basis setup or the VL031 input**. Verify the **tax master setup and the export definition** before treating it as a defect.

---

## 16. Key Code, Processes & Repos

### Processes / batch steps
| Process / step | Purpose | Notes |
|---|---|---|
| **QP043** | Severance-tax batch process | Hosts the state TRSEV* steps + tax-combo rollup + tax JE post |
| **TRSEVTXRPT / TRSEVTXRPF** | TX sev-tax prelim / **FINAL** (and undo-FINAL) | RPF = FINAL; "undo FINAL" is the TRSEVTXRPF path (§15) |
| **TRSEVTXEPR / TRSEVTXEFI** | TX sev-tax e-file (prelim / file) | EFI "Missing Parm" = add the process parameter (22-00688731) |
| **TRSEVOKRPT / TRSEVLARPT** | OK / LA sev-tax prelim | Column-bind/build defects (22-00512615) |
| **TRTAXCOMBO** (`QPSTAXCOMBO` / `RATXCMBO37`) | Tax-combination rollup → inserts into `TONL_TAX_INPUT` | Dup rows → PK error → TAXJEPOST stops (§5) |
| **TAXJEPOST** | Post the tax JE | Fails when `TONL_TAX_INPUT` has dup/PK collisions |
| **CW1099EXPT / CW675REXPS / CW675REXPT / CW1099EXPG** | 1099 export (incl. process type 1099, global) | Box15/17 accuracy (#1771560); Spring-2022 / Hotfix-27 |
| **TRRYLMMSEF** | MMS/ONRR royalty e-file | ONRR format-change hotfixes (22-00685965) |
| ONRR / MMS **2014** report & e-file | Federal royalty regulatory reporting | "ONRR Preliminary failing" #1733150; mmbtu data gap (22-00830233) |

### Code locations (confirmed via ADO code search)
| Symbol | Repo / path | Cluster |
|---|---|---|
| `QPSTaxCombo.cpp` / `QPSTaxCombo.h` (step class `QPSTAXCOMBO`) | `Quorum.Upstream.QRA.ClassicBatch /QPDllRevenueAcctgBR/` | §5 tax-combo rollup |
| `QSQL_TaxCombo.cpp` (proc `TAX_COMBO_INS_TAX_INPUT_2ND_ROLLUP`) | `Quorum.Upstream.QRA.ClassicBatch /QPDllRevenueAcctgBR/` | §5 TONL_TAX_INPUT insert |
| Process-step metadata (`QARCH_CTRL_PROCESS_STEP`) | `SUM.Upstream.Metadata /STANDARD 16.0/` | §5/§16 step config |
| BKRVNU (revenue/tax batch) technical docs | `Quorum.Upstream.Tools /documentation/Analysis/BatchProcesses/BKRVNU/` | §5 |
| TS010/TS015/TR010 grid defs + registered SQL | client `*.Upstream.Metadata` (grid definitions, e.g. **16000**) | §11 |
| `TR_TX_CPA` / `TR_TX_CPA_CSV` imp/exp definitions | export-definition metadata / Maintenance app | §8 |

### Repos
- **`Quorum.Upstream.QRA.ClassicBatch`** — C++ revenue/tax batch (`QPDllRevenueAcctgBR`: `QPSTaxCombo`, `QSQL_TaxCombo`). The tax-combo / sev-tax / 1099 / ONRR engine lives here.
- **`SUM.Upstream.Metadata`** — standard metadata (process steps, grid definitions, screens). Client-specific metadata repos hold grid-def overrides (TS010/TS015 registered SQL, grid def 16000).
- **`Quorum.Upstream.Tools`** — batch-process technical documentation (BKRVNU, etc.).
- Client overrides follow `<CLIENT>.Upstream.*` (CEN/Permian, CNX, TGNR, AST, BP PRD, DAY…). **Check the client repo/schema first** — many fixes are client-specific (grid def, export path, column type, amendment behavior by source version).

---

## 17. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- A **calculation/report** is provably wrong on correct inputs: TX amendment not reversing (#1725228), TSR096 drilling-permit flag (#1732390), prelim overstates/duplicates (#1587320), EDI/PDF tie-out sum logic (25-01009292), 1099 export accuracy/Box15-17 (#1771560), foreign-owner false warning (#1430314), Lease Use volume-not-gross-value (25-01043072), federal w/h missing on 1099 (Hotfix 27, 22-00651660).
- A **step crashes from a code/proc bug**, not data: TRTAXCOMBO/QPSTAXCOMBO PK on `TONL_TAX_INPUT` that **regenerates** after clean-up (#1589115), TRSEVOKRPT column-bind (22-00512615), TS015 reverse/rebook (22-00560550).
- Provide: **process + failing step + SQLID + exact ORA error**, client + property/well + prod/acctg month, and a repro. **Confirm the build first** — much legacy TX volume is fixed by the **TX Tax rewrite (2020.03/2020.09)** or **v17**, and ONRR formats by periodic **ONRR hotfixes**.

**Route to Cloud Ops / handle as Configuration when:**
- **Export file path / folder / SFTP definition** not set up (24-00973138, 25-01045147, 24-00972614, 23-00933898, 25-00996195, 25-01047728/#1761149) — set via the imp/exp definition or **Maintenance app**, ensure the QCloud folder exists, and **add to the client post-refresh repo** so a DB refresh doesn't wipe it.
- **Grid / registered-SQL / metadata** issues on TS010/TS015/TR010 (25-01053790, 25-01044137, 25-01019829 grid def 16000), TR010 business-rule / RRN trigger (23-00920984, 22-00826280), metadata quoting DEV-vs-PROD (23-00901426), reg-fee config (25-01007859).
- **Schema drift** on TX tax tables (`char` vs `varchar2`, 25-01010533) and **NAUPA/reddog metadata** (22-00668091) — DDL/metadata fix in the client repo.

**Handle as a data fix (script, with verify-SELECT in a transaction):**
- Duplicate **`TONL_TAX_INPUT`** rows blocking TAXJEPOST (24-00946826, 26-01095867, 24-00938123).
- **Escheat date** corrections (25-01027368); EC005/EC006 cleanup requests.
- Wells with **Tax Pay Code = 2 (Purchaser)** blocking TX prelim post (25-01003197); inserting a missing **Report Generate Date** parm (25-01007857).

**Handle as Training / Expected behavior (no fix):** see §15 — sev-tax SPEs that clear once data/parm/env is fixed, blank state prelims with no qualifying data, 1099 process/voided-check/file-path questions, escheat reset/delete requests, and tax-calc "wrong number" cases that trace to **TS005/TS006 rate/basis setup or the VL031 input**. Verify the **tax master setup and the export definition** before treating it as a defect.

---

*Skill created: 2026-06-14.*
*Based on: 425 closed QRA Tax-&-Regulatory SF cases — 71 actionable (Software Defect 52 + Application Configuration 19; no ChangeConfig rows in this dataset) mined for fix recipes, plus ~70 Training/Customer-Error cases for the FAQ. ADO work items #1725228, #1732390, #1397814, #1587320, #1607780/#1608581, #1589115, #1393874, #1771560, #1430314, #1455630, #1761149, #1733150, #1538825/#1538829.*
*Companion: revenue-distribution / DOI / suspense / check-write skill, JIB skill, REPO_REFERENCE.*
